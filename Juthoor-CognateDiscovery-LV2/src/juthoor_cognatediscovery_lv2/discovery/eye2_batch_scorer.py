"""Eye 2 Batch Scorer — Eye 1 ranked candidates -> LLM semantic scoring -> JSONL.

CLI: python -m juthoor_cognatediscovery_lv2.discovery.eye2_batch_scorer \\
         --input eye1.jsonl --output eye2.jsonl --lang grc --resume
"""
from __future__ import annotations

import argparse, json, os, re, sys, time
from collections import defaultdict
from pathlib import Path
from typing import Any

# Arabic normalization (mirrors run_eye1_full_scale._norm_arabic for symmetric
# lookup — ensures profiles/LV0/deep-glossary keys match Eye 1 output keys).
_ARABIC_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")
_HAMZA_TR = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ؤ": "و", "ئ": "ي", "ء": "ا",
})


def _norm_arabic_lookup(text: str) -> str:
    """Normalize an Arabic string for dictionary lookup.

    Mirrors run_eye1_full_scale._norm_arabic: strip diacritics, normalize
    hamza variants, strip leading ال (if at least 2 letters remain).
    """
    if not text:
        return text
    text = _ARABIC_DIACRITICS_RE.sub("", text)
    text = text.translate(_HAMZA_TR).strip()
    if text.startswith("ال") and len(text) >= 4:
        text = text[2:]
    return text


_MODEL_MAP = {"sonnet": "claude-sonnet-4-6", "opus": "claude-opus-4-6"}
_LANG_NAMES = {"lat": "Latin", "grc": "Greek", "eng": "English", "deu": "German", "fra": "French", "spa": "Spanish"}

_IPA_GLOSS_PATHS = {
    "grc": "data/processed/greek_ipa_gloss_lookup.json",
    "lat": "data/processed/latin_ipa_gloss_lookup.json",
}

def _lv2_root() -> Path:
    return Path(__file__).resolve().parents[3]

def _repo_root() -> Path:
    return _lv2_root().parent

def _default_profiles_path() -> Path:
    return _lv2_root() / "data" / "llm_annotations" / "arabic_semantic_profiles.jsonl"

def _default_lv0_lexemes_path() -> Path:
    return _repo_root() / "Juthoor-DataCore-LV0" / "data" / "processed" / "arabic" / "classical" / "lexemes.jsonl"

# -- Target IPA+gloss lookup (lazy, per lang) --------------------------------

_target_glosses_cache: dict[str, dict[str, dict[str, str]]] = {}

def _load_target_glosses(lang: str) -> dict[str, dict[str, str]]:
    """Load IPA+gloss lookup for the target language. Returns {lemma: {ipa, gloss}}."""
    global _target_glosses_cache
    if lang in _target_glosses_cache:
        return _target_glosses_cache[lang]
    _target_glosses_cache[lang] = {}
    rel_path = _IPA_GLOSS_PATHS.get(lang)
    if rel_path is None:
        print(f"[warn] No IPA gloss path configured for lang={lang!r}", file=sys.stderr)
        return _target_glosses_cache[lang]
    full_path = _lv2_root() / rel_path
    if not full_path.exists():
        print(f"[warn] Target gloss file not found: {full_path}", file=sys.stderr)
        return _target_glosses_cache[lang]
    with open(full_path, encoding="utf-8") as fh:
        data = json.load(fh)
    # Normalise: expect either {lemma: {ipa, gloss}} or {lemma: {...}} — keep as-is
    _target_glosses_cache[lang] = {k: {"ipa": v.get("ipa", ""), "gloss": v.get("gloss", "")} for k, v in data.items() if isinstance(v, dict)}
    print(f"[info] Loaded {len(_target_glosses_cache[lang])} target glosses for lang={lang!r}.", file=sys.stderr)
    return _target_glosses_cache[lang]

# -- Deep Arabic glossary (lazy) ---------------------------------------------

_deep_glossary_cache: dict[str, Any] | None = None

def _load_deep_glossary() -> dict[str, Any]:
    """Load arabic_deep_glossary.jsonl if it exists. Returns {root_norm: {...}}."""
    global _deep_glossary_cache
    if _deep_glossary_cache is not None:
        return _deep_glossary_cache
    _deep_glossary_cache = {}
    path = _lv2_root() / "data" / "enriched" / "arabic_deep_glossary.jsonl"
    if not path.exists():
        return _deep_glossary_cache
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            root = (obj.get("root_norm") or "").strip()
            if root:
                key = _norm_arabic_lookup(root)
                if key and key not in _deep_glossary_cache:
                    _deep_glossary_cache[key] = obj
    print(f"[info] Loaded {len(_deep_glossary_cache)} entries from deep glossary.", file=sys.stderr)
    return _deep_glossary_cache

# -- Arabic semantic profiles (lazy) ----------------------------------------

_profiles_cache: dict[str, dict[str, str]] | None = None


def _extract_masadiq_gloss(masadiq: Any) -> str:
    """Extract a concise masadiq string from the nested profile structure.

    Profile file stores masadiq as {short_gloss, definition, meaning_text}.
    """
    if not isinstance(masadiq, dict):
        return str(masadiq).strip() if masadiq else ""
    sg = (masadiq.get("short_gloss") or "").strip()
    if sg:
        return sg
    defn = (masadiq.get("definition") or "").strip()
    if defn:
        return defn[:200] + ("\u2026" if len(defn) > 200 else "")
    return (masadiq.get("meaning_text") or "").strip()


def _extract_mafahim_gloss(mafahim: Any) -> str:
    """Extract a concise mafahim (genome) string from the nested profile.

    Profile file stores mafahim as {binary_field_gloss, axial_meaning,
    letter_meanings: [...], quran_example}.
    """
    if not isinstance(mafahim, dict):
        return str(mafahim).strip() if mafahim else ""
    parts: list[str] = []
    axial = (mafahim.get("axial_meaning") or "").strip()
    if axial:
        parts.append(f"CORE: {axial}")
    letters = mafahim.get("letter_meanings") or []
    if isinstance(letters, list) and letters:
        parts.append("letters: " + "; ".join(str(l) for l in letters))
    quran = (mafahim.get("quran_example") or "").strip()
    if quran:
        parts.append(f"quran: {quran[:100]}")
    return " | ".join(parts)


def _load_profiles(profiles_path: Path) -> dict[str, dict[str, str]]:
    global _profiles_cache
    if _profiles_cache is not None:
        return _profiles_cache
    _profiles_cache = {}
    if not profiles_path.exists():
        print(f"[warn] Arabic profiles not found: {profiles_path}", file=sys.stderr)
        return _profiles_cache
    populated = 0
    with open(profiles_path, encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            obj = json.loads(raw)
            lemma = (obj.get("lemma") or "").strip()
            if not lemma:
                continue
            key = _norm_arabic_lookup(lemma)
            if not key:
                continue
            # Read actual nested dict fields (masadiq, mafahim) — NOT the
            # non-existent masadiq_gloss/mafahim_gloss flat fields.
            masadiq_str = _extract_masadiq_gloss(obj.get("masadiq") or {})
            mafahim_str = _extract_mafahim_gloss(obj.get("mafahim") or {})
            if masadiq_str or mafahim_str:
                populated += 1
            _profiles_cache[key] = {
                "masadiq_gloss": masadiq_str,
                "mafahim_gloss": mafahim_str,
            }
    print(
        f"[info] Loaded {len(_profiles_cache)} Arabic semantic profiles "
        f"({populated} with glosses).",
        file=sys.stderr,
    )
    return _profiles_cache

# -- LV0 Arabic definitions (fallback for roots without profiles) -----------

# Strip leading metadata prefixes from dictionary glosses: "(ء ب خَ)", "(K:)", "(و)"
_LV0_PAREN_PREFIX_RE = re.compile(r"^\([^)]{1,20}\)\s*")

_lv0_cache: dict[str, str] | None = None

def _load_lv0_definitions(lv0_path: Path | None = None) -> dict[str, str]:
    """Load Arabic definitions from LV0 lexemes (short_gloss field, Arabic text).

    These cover ~100% of Eye 1 roots. Used as fallback when no masadiq/mafahim
    profile exists. The LLM reads Arabic natively.
    """
    global _lv0_cache
    if _lv0_cache is not None:
        return _lv0_cache
    _lv0_cache = {}
    path = lv0_path or _default_lv0_lexemes_path()
    if not path.exists():
        print(f"[warn] LV0 lexemes not found: {path}", file=sys.stderr)
        return _lv0_cache
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            root = (obj.get("root_norm") or "").strip()
            defn = (obj.get("short_gloss") or obj.get("definition") or "").strip()
            # Strip leading dictionary metadata like "(ء ب خَ)" or "(K:)"
            defn = _LV0_PAREN_PREFIX_RE.sub("", defn)
            if root and defn:
                key = _norm_arabic_lookup(root)
                if key and key not in _lv0_cache:
                    _lv0_cache[key] = defn
    print(f"[info] Loaded {len(_lv0_cache)} LV0 Arabic definitions (fallback).", file=sys.stderr)
    return _lv0_cache

# -- Eye 1 loading -----------------------------------------------------------

def load_eye1_candidates(input_path: Path, min_discovery_score: float, top_n_per_root: int, lang_filter: str | None = None) -> list[dict[str, Any]]:
    """Load Eye 1 JSONL, filter by score and lang, keep top N per root."""
    by_root: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    with open(input_path, encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            obj = json.loads(raw)
            if float(obj.get("discovery_score", 0)) < min_discovery_score:
                continue
            if lang_filter and obj.get("lang") != lang_filter:
                continue
            by_root[obj["arabic_root"]].append(obj)
    out: list[dict[str, Any]] = []
    for items in by_root.values():
        items.sort(key=lambda x: float(x.get("discovery_score", 0)), reverse=True)
        out.extend(items[:top_n_per_root])
    return out

# -- Resume support ----------------------------------------------------------

def load_scored_pairs(output_path: Path) -> set[tuple[str, str]]:
    """Return (source_lemma, target_lemma) pairs already written to output."""
    scored: set[tuple[str, str]] = set()
    if not output_path.exists():
        return scored
    with open(output_path, encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
                scored.add((obj["source_lemma"], obj["target_lemma"]))
            except (json.JSONDecodeError, KeyError):
                continue
    return scored

# -- LLM helpers -------------------------------------------------------------

_prompt_template_cache: str | None = None


def _load_prompt_template() -> str:
    """Load the V2 prompt template from config/eye2_prompt_template.txt."""
    global _prompt_template_cache
    if _prompt_template_cache is not None:
        return _prompt_template_cache
    template_path = _lv2_root() / "config" / "eye2_prompt_template.txt"
    if template_path.exists():
        _prompt_template_cache = template_path.read_text(encoding="utf-8")
    else:
        # Minimal fallback if template file is missing
        _prompt_template_cache = (
            "You are scoring semantic connections between Arabic words and {LANG_NAME} words.\n"
            "Score 0.0-1.0. Method: masadiq_direct, mafahim_deep, combined, weak.\n\n"
            "{TASK_INSTRUCTION}\n"
            "Return ONLY a JSON array, no markdown fences."
        )
    return _prompt_template_cache


def _build_prompt(pairs: list[dict[str, Any]], lang: str) -> str:
    lang_name = _LANG_NAMES.get(lang, lang.upper())
    lines: list[str] = []
    for i, p in enumerate(pairs):
        ara_m = (f"masadiq: {p['masadiq_gloss']}" if p.get("masadiq_gloss") else "(no gloss)")
        if p.get("mafahim_gloss"):
            ara_m += f" | mafahim: {p['mafahim_gloss']}"
        if p.get("arabic_meanings_expanded"):
            ara_m += " | ALL MEANINGS: " + "; ".join(m["sense"] for m in p["arabic_meanings_expanded"][:7] if isinstance(m, dict) and m.get("sense"))
        tgt_p = f' ({p["target_meaning"]})' if p.get("target_meaning") else ""
        lines.append(f'{i}. Arabic "{p["arabic_root"]}" ({ara_m}) <-> {lang_name} "{p["target_lemma"]}"{tgt_p}')
    n = len(pairs)

    task_instruction = (
        "Score these pairs:\n" + "\n".join(lines) +
        f"\n\nReturn a JSON array of exactly {n} objects: "
        '[{"pair_index":0,"score":0.85,"reasoning":"...","method":"masadiq_direct"},...]\n'
    )

    template = _load_prompt_template()
    return template.replace("{LANG_NAME}", lang_name).replace("{TASK_INSTRUCTION}", task_instruction)

def _call_llm(client: Any, model_id: str, prompt: str, retries: int = 3) -> list[dict[str, Any]]:
    """Call Anthropic API; parse JSON array; retry with backoff on failure."""
    delay = 2.0
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            resp = client.messages.create(model=model_id, max_tokens=2048, messages=[{"role": "user", "content": prompt}])
            raw = resp.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                if raw.endswith("```"):
                    raw = raw[:-3]
            return json.loads(raw.strip())
        except Exception as exc:
            last_err = exc
            if attempt < retries - 1:
                print(f"[warn] LLM failed ({attempt+1}/{retries}): {exc}. Retry in {delay:.0f}s...", file=sys.stderr)
                time.sleep(delay); delay *= 2
    raise RuntimeError(f"LLM call failed after {retries} attempts: {last_err}") from last_err

# -- Core scoring loop (public API) ------------------------------------------

def score_candidates(candidates: list[dict[str, Any]], profiles: dict[str, dict[str, str]],
                     output_path: Path, model_alias: str, lang: str, batch_size: int,
                     resume: bool, dry_run: bool, batch_label: str) -> int:
    """Score candidates, appending results to output_path. Returns count scored."""
    already: set[tuple[str, str]] = set()
    if resume:
        already = load_scored_pairs(output_path)
        if already:
            print(f"[resume] Skipping {len(already)} already-scored pairs.", file=sys.stderr)

    to_score = [c for c in candidates if (c["arabic_root"], c["target_lemma"]) not in already]
    if not to_score:
        print("[info] Nothing left to score.", file=sys.stderr); return 0

    # Enrich with Arabic meanings (profiles first, LV0 fallback)
    # Cache a normalized lookup key per candidate — ensures profiles/LV0/deep
    # glossary lookups hit regardless of residual ال or hamza variants.
    for c in to_score:
        c["_ar_key"] = _norm_arabic_lookup(c["arabic_root"])

    lv0_defs = _load_lv0_definitions()
    enriched = 0
    for c in to_score:
        ar_key = c["_ar_key"]
        prof = profiles.get(ar_key, {})
        c["masadiq_gloss"] = prof.get("masadiq_gloss", "")
        c["mafahim_gloss"] = prof.get("mafahim_gloss", "")
        # Fallback: LV0 Arabic definition (Arabic text — LLM reads it natively)
        if not c["masadiq_gloss"] and not c["mafahim_gloss"]:
            c["masadiq_gloss"] = lv0_defs.get(ar_key, "")
        if c["masadiq_gloss"] or c["mafahim_gloss"]:
            enriched += 1

    print(f"[info] {enriched}/{len(to_score)} pairs enriched with Arabic meaning ({enriched/max(1,len(to_score))*100:.1f}%).", file=sys.stderr)

    # Enrich with target-language glosses
    target_glosses = _load_target_glosses(lang)
    deep = _load_deep_glossary()
    tgt_enriched = 0
    deep_enriched = 0
    for c in to_score:
        tgt_entry = target_glosses.get(c["target_lemma"], {})
        c["target_meaning"] = tgt_entry.get("gloss", "")
        if c["target_meaning"]:
            tgt_enriched += 1
        expanded = deep.get(c["_ar_key"], {}).get("meanings", [])
        c["arabic_meanings_expanded"] = expanded
        if expanded:
            deep_enriched += 1
    print(f"[info] {tgt_enriched} pairs with target meaning, {deep_enriched} with deep glossary.", file=sys.stderr)

    print(f"[info] Scoring {len(to_score)} pairs in batches of {batch_size}.", file=sys.stderr)

    if dry_run:
        for c in to_score[:5]:
            gloss = (c.get("masadiq_gloss") or "")[:50]
            print(f"  [dry-run] {c['arabic_root']} ({gloss}) <-> {c['target_lemma']}", file=sys.stderr)
        if len(to_score) > 5:
            print(f"  [dry-run] ... and {len(to_score)-5} more.", file=sys.stderr)
        return 0

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("[error] ANTHROPIC_API_KEY not set.", file=sys.stderr); sys.exit(1)

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    model_id = _MODEL_MAP.get(model_alias, model_alias)

    scored = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    total = (len(to_score) + batch_size - 1) // batch_size

    with open(output_path, "a", encoding="utf-8") as out_fh:
        for i, start in enumerate(range(0, len(to_score), batch_size), 1):
            batch = to_score[start: start + batch_size]
            print(f"[batch {i}/{total}] Scoring {len(batch)} pairs...", file=sys.stderr)
            try:
                results = _call_llm(client, model_id, _build_prompt(batch, lang))
            except RuntimeError as exc:
                print(f"[error] {exc}", file=sys.stderr); continue
            for item in results:
                idx = item.get("pair_index", 0)
                if idx >= len(batch):
                    continue
                c = batch[idx]
                out_fh.write(json.dumps({
                    "source_lemma": c["arabic_root"], "target_lemma": c["target_lemma"],
                    "lang_pair": f"ara-{lang}", "semantic_score": float(item.get("score", 0.0)),
                    "reasoning": str(item.get("reasoning", "")), "method": str(item.get("method", "unknown")),
                    "discovery_score": float(c.get("discovery_score", 0.0)),
                    "model": model_alias, "batch": batch_label,
                }, ensure_ascii=False) + "\n")
                scored += 1
            out_fh.flush()

    print(f"[info] Done. Scored {scored} pairs.", file=sys.stderr)
    return scored

# -- CLI ---------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Eye 2 Batch Scorer: LLM semantic scoring of Eye 1 candidates.")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--lang", required=True, help="Target lang code: lat, grc, eng, ...")
    p.add_argument("--model", default="sonnet", choices=list(_MODEL_MAP))
    p.add_argument("--min-discovery-score", type=float, default=0.6)
    p.add_argument("--top-n-per-root", type=int, default=50)
    p.add_argument("--batch-size", type=int, default=10)
    p.add_argument("--profiles", default=None, help="Path to arabic_semantic_profiles.jsonl.")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--batch-label", default=None)
    return p.parse_args(argv)

def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    input_path = Path(args.input)
    output_path = Path(args.output)
    profiles_path = Path(args.profiles) if args.profiles else _default_profiles_path()
    batch_label = args.batch_label or f"eye2_discovery_{args.lang}"

    print(f"[info] Loading Eye 1 candidates from {input_path}", file=sys.stderr)
    candidates = load_eye1_candidates(input_path, min_discovery_score=args.min_discovery_score,
                                      top_n_per_root=args.top_n_per_root, lang_filter=args.lang)
    print(f"[info] {len(candidates)} candidates after filtering.", file=sys.stderr)
    profiles = _load_profiles(profiles_path)
    score_candidates(candidates=candidates, profiles=profiles, output_path=output_path,
                     model_alias=args.model, lang=args.lang, batch_size=args.batch_size,
                     resume=args.resume, dry_run=args.dry_run, batch_label=batch_label)

if __name__ == "__main__":
    main()
