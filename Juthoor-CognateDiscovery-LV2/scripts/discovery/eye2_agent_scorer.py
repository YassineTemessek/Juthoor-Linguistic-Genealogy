"""Eye 2 Agent Scorer — prepare Eye 1 candidates as detective investigation files for Claude Code agents.

No Anthropic API key required. Agents read the prompt files and return findings JSON.

Modes:
  --prepare       Filter Eye 1 output, enrich pairs, write batch investigation .txt files (5-10 pairs each)
  --investigate   Print an investigation prompt for a single batch file to stdout
  --ingest-response  Parse findings JSON response and write JSONL results
  --merge         Merge all findings JSONL files into a final output with verdict summary

Usage:
  python eye2_agent_scorer.py --prepare --lang got --min-ds 0.90 --top-k 3 --batch-size 8
  python eye2_agent_scorer.py --investigate outputs/eye2_agent_batches/got/batch_000.txt
  python eye2_agent_scorer.py --ingest-response --lang got --batch-index 0 --response-file <findings.json>
  python eye2_agent_scorer.py --merge --lang got
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from collections import defaultdict

# Ensure stdout handles UTF-8 (Arabic text) on all platforms including Windows.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path bootstrap — allow running this script directly without package install
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = Path(__file__).resolve().parent           # scripts/discovery/
_LV2_ROOT = _SCRIPTS_DIR.parents[1]                      # Juthoor-CognateDiscovery-LV2/
_REPO_ROOT = _LV2_ROOT.parent                            # Juthoor-Linguistic-Genealogy/
_SRC_DIR = _LV2_ROOT / "src"

if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

# ---------------------------------------------------------------------------
# Import enrichment helpers from eye2_batch_scorer
# ---------------------------------------------------------------------------

from juthoor_cognatediscovery_lv2.discovery.eye2_batch_scorer import (  # noqa: E402
    _norm_arabic_lookup,
    _load_profiles,
    _load_lv0_definitions,
    _load_deep_glossary,
    _load_target_glosses,
    _default_profiles_path,
    _LANG_NAMES,
    load_eye1_candidates,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _outputs_dir() -> Path:
    return _LV2_ROOT / "outputs"

def _batches_dir(lang: str) -> Path:
    return _outputs_dir() / "eye2_agent_batches" / lang

def _results_dir(lang: str) -> Path:
    return _outputs_dir() / "eye2_results" / lang

def _eye1_path(lang: str) -> Path:
    return _outputs_dir() / f"eye1_full_scale_{lang}.jsonl"

def _final_path(lang: str) -> Path:
    return _outputs_dir() / f"eye2_final_{lang}.jsonl"

def _detective_prompt_path() -> Path:
    return _REPO_ROOT / "autoresearch" / "eye2_prompt.md"

# ---------------------------------------------------------------------------
# Load detective prompt
# ---------------------------------------------------------------------------

_detective_prompt_cache: str | None = None


def _load_detective_prompt() -> str:
    global _detective_prompt_cache
    if _detective_prompt_cache is not None:
        return _detective_prompt_cache
    prompt_path = _detective_prompt_path()
    if prompt_path.exists():
        _detective_prompt_cache = prompt_path.read_text(encoding="utf-8")
    else:
        # Minimal fallback if the file is missing
        _detective_prompt_cache = (
            "You are a linguistic detective investigating deep connections between Arabic roots "
            "and words in other ancient languages.\n\n"
            "For each pair, output a finding with: pair_id, finding (path_found/no_path), "
            "semantic_journey, journey_type, confidence (high/medium/low), key_insight.\n"
            "Return a JSON array of finding objects."
        )
        print(
            f"[warn] Detective prompt not found at {prompt_path}, using minimal fallback.",
            file=sys.stderr,
        )
    return _detective_prompt_cache

# ---------------------------------------------------------------------------
# Arabic root letter analysis hints
# ---------------------------------------------------------------------------

# Approximate semantic fields encoded by common Arabic root letter pairs (first two radicals).
# This is a lightweight hint layer — not exhaustive, just aids the detective's initial read.
_ROOT_SEED_HINTS: dict[str, str] = {
    "كت": "binding/enclosing/writing",
    "كل": "wholeness/completeness/eating",
    "كن": "being/existence/dwelling",
    "كر": "returning/rolling/opposing",
    "كب": "falling/toppling/turning over",
    "كس": "breaking/covering/clothing",
    "نظ": "looking/observing",
    "نف": "breath/soul/self/wind",
    "نق": "purity/selection/criticism",
    "نج": "saving/escaping/success",
    "نش": "spreading/rising/growing",
    "نص": "erecting/text/core",
    "نع": "softness/blessing/cattle",
    "نم": "growth/informing/sleeping",
    "بر": "land/righteousness/outside",
    "بن": "building/structure/son",
    "بد": "beginning/body/spreading",
    "بس": "extending/enough/cats",
    "بط": "slowness/belly/ducks",
    "بع": "distance/selling/sending",
    "بق": "remaining/persistence",
    "بل": "moistening/testing/heart",
    "سل": "extracting/drawing out/basket",
    "سم": "name/poison/height",
    "سن": "tooth/age/law/sharpening",
    "سر": "secret/joy/journeying/navel",
    "سف": "lowness/travel/stupidity",
    "سك": "silence/dwelling/pouring",
    "صل": "connecting/prayer/roasting",
    "صن": "making/crafting/protecting",
    "صر": "binding/tying/crying/small",
    "طر": "freshness/path/striking",
    "طب": "medicine/skill/nature",
    "طح": "grinding/spreading",
    "ظه": "back/appearing/support",
    "عب": "crossing/load/worship",
    "عج": "wonder/haste/calf",
    "عد": "counting/crossing/enemy",
    "عر": "knowing/exposing/width",
    "عق": "reason/tying/punishing",
    "عل": "height/above/knowledge",
    "عم": "covering/general/blindness/uncle",
    "غل": "covering/entering deeply/boiling",
    "غر": "deceiving/depth/abundance",
    "فت": "opening/crumbling/young",
    "فر": "fleeing/emptying/distinguishing",
    "فق": "opening/poverty/understanding",
    "قل": "smallness/turning/heart",
    "قط": "cutting/dropping/cat",
    "قر": "coldness/settlement/reading",
    "قن": "permanence/hunting/flute",
    "قص": "cutting/story/going",
    "حب": "love/grain/holding/seed",
    "حر": "heat/freedom/silk",
    "حك": "wisdom/ruling/scratching",
    "حل": "solving/unlocking/milk",
    "حم": "heat/fever/protection/charcoal",
    "خر": "exiting/destruction/flowing",
    "خل": "emptiness/friendship/vinegar",
    "دل": "showing/pointing/softness",
    "دم": "blood/continuity/payment",
    "دن": "nearness/religion/vileness",
    "ذه": "going/gold/mind",
    "ذك": "memory/male/sharpness",
    "رأ": "seeing/head/opinion",
    "رح": "spaciousness/mercy/grinding",
    "رد": "returning/rejecting",
    "رس": "anchoring/sending/drawing",
    "رك": "riding/assembling/weakness",
    "ضر": "harm/necessity/striking",
    "ضع": "placing/weakness/nursing",
    "وج": "face/direction/existence",
    "وز": "weight/balance/chest",
    "وق": "falling/time/protecting",
    "جل": "greatness/skin/coming",
    "جم": "gathering/silence/body",
    "جن": "hidden/garden/madness/jinn",
    "جر": "flowing/pulling/running",
    "جد": "seriousness/grandfather/cutting",
}


def _get_root_seed_hint(arabic_root: str) -> str:
    """Return a seed concept hint for the first two letters of an Arabic root."""
    # Try the first two characters as a key
    if len(arabic_root) >= 2:
        key = arabic_root[:2]
        hint = _ROOT_SEED_HINTS.get(key)
        if hint:
            return hint
    return ""

# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def _build_investigation_prompt(pairs: list[dict[str, Any]], lang: str) -> str:
    """Build a complete detective investigation prompt for a batch of 5-10 pairs."""
    lang_name = _LANG_NAMES.get(lang, lang.upper())
    detective_prompt = _load_detective_prompt()

    pair_lines: list[str] = []
    for i, p in enumerate(pairs):
        pair_id = p.get("pair_id", f"P{i:03d}")

        # Arabic root information
        ara_root = p["arabic_root"]
        seed_hint = _get_root_seed_hint(ara_root)

        # Build meaning layers
        meaning_parts: list[str] = []

        masadiq = p.get("masadiq_gloss", "")
        if masadiq:
            meaning_parts.append(f"masadiq (dictionary): {masadiq}")

        mafahim = p.get("mafahim_gloss", "")
        if mafahim:
            meaning_parts.append(f"mafahim (conceptual core): {mafahim}")

        if seed_hint:
            meaning_parts.append(f"root seed concept: {seed_hint}")

        expanded = p.get("arabic_meanings_expanded", [])
        if expanded:
            senses = [
                m["sense"]
                for m in expanded[:8]
                if isinstance(m, dict) and m.get("sense")
            ]
            if senses:
                meaning_parts.append("all known senses: " + "; ".join(senses))

        if not meaning_parts:
            meaning_parts.append("(no gloss available)")

        arabic_block = "\n    ".join(meaning_parts)

        # Target word information
        tgt_lemma = p["target_lemma"]
        tgt_meaning = p.get("target_meaning", "")
        tgt_block = f'{tgt_lemma}'
        if tgt_meaning:
            tgt_block += f' — "{tgt_meaning}"'

        ds = float(p.get("discovery_score", 0.0))

        pair_lines.append(
            f'### Pair {pair_id}\n'
            f'- **Arabic root**: {ara_root} (Eye 1 score: {ds:.3f})\n'
            f'  - {arabic_block}\n'
            f'- **{lang_name} word**: {tgt_block}\n'
        )

    pairs_block = "\n".join(pair_lines)

    n = len(pairs)
    output_schema = json.dumps(
        [
            {
                "pair_id": "P000",
                "finding": "path_found or no_path",
                "semantic_journey": "Step-by-step meaning path from Arabic to target...",
                "journey_type": "direct_preservation | semantic_drift | metaphorical_extension | specialization | generalization | negation_cognate | material_culture | shared_loanword | no_connection",
                "confidence": "high | medium | low",
                "key_insight": "One sentence core of the finding.",
            }
        ],
        ensure_ascii=False,
        indent=2,
    )

    prompt = (
        f"{detective_prompt}\n\n"
        f"---\n\n"
        f"## Investigation batch — {lang_name} ({n} pairs)\n\n"
        f"Eye 1 has already established the consonant skeleton match for each pair below. "
        f"Your job is purely semantic: investigate whether a meaning path exists.\n\n"
        f"{pairs_block}\n"
        f"---\n\n"
        f"## Your output\n\n"
        f"Return a JSON array of exactly {n} finding objects. "
        f"Do NOT wrap in markdown fences. Schema:\n\n"
        f"{output_schema}\n\n"
        f"Pair IDs to return: "
        + ", ".join(p.get("pair_id", f"P{i:03d}") for i, p in enumerate(pairs))
    )
    return prompt

# ---------------------------------------------------------------------------
# Enrichment
# ---------------------------------------------------------------------------

def _enrich_candidates(candidates: list[dict[str, Any]], lang: str) -> list[dict[str, Any]]:
    """Enrich each candidate dict in-place with Arabic and target glosses."""
    profiles = _load_profiles(_default_profiles_path())
    lv0_defs = _load_lv0_definitions()
    target_glosses = _load_target_glosses(lang)
    deep = _load_deep_glossary()

    enriched_ara = 0
    enriched_tgt = 0
    enriched_deep = 0

    for c in candidates:
        ar_key = _norm_arabic_lookup(c["arabic_root"])
        c["_ar_key"] = ar_key

        prof = profiles.get(ar_key, {})
        c["masadiq_gloss"] = prof.get("masadiq_gloss", "")
        c["mafahim_gloss"] = prof.get("mafahim_gloss", "")

        # LV0 fallback when no profile exists
        if not c["masadiq_gloss"] and not c["mafahim_gloss"]:
            c["masadiq_gloss"] = lv0_defs.get(ar_key, "")

        if c["masadiq_gloss"] or c["mafahim_gloss"]:
            enriched_ara += 1

        tgt_entry = target_glosses.get(c["target_lemma"], {})
        c["target_meaning"] = tgt_entry.get("gloss", "")
        if c["target_meaning"]:
            enriched_tgt += 1

        expanded = deep.get(ar_key, {}).get("meanings", [])
        c["arabic_meanings_expanded"] = expanded
        if expanded:
            enriched_deep += 1

    total = len(candidates)
    print(
        f"[info] Arabic enrichment: {enriched_ara}/{total} "
        f"| Target glosses: {enriched_tgt}/{total} "
        f"| Deep glossary: {enriched_deep}/{total}",
        file=sys.stderr,
    )
    return candidates

# ---------------------------------------------------------------------------
# Mode 1: --prepare
# ---------------------------------------------------------------------------

_DEFAULT_BATCH_SIZE = 8  # deep investigation: 5-10 pairs per batch


def cmd_prepare(args: argparse.Namespace) -> None:
    lang = args.lang
    min_ds: float = args.min_ds
    top_k: int = args.top_k
    batch_size: int = max(5, min(10, args.batch_size))  # clamp to 5-10

    if args.batch_size != batch_size:
        print(
            f"[info] batch_size clamped to {batch_size} (detective mode requires 5-10 pairs per batch).",
            file=sys.stderr,
        )

    eye1_path = _eye1_path(lang)
    if not eye1_path.exists():
        print(f"[error] Eye 1 file not found: {eye1_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[info] Loading Eye 1 candidates from {eye1_path}", file=sys.stderr)
    candidates = load_eye1_candidates(
        input_path=eye1_path,
        min_discovery_score=min_ds,
        top_n_per_root=top_k,
        lang_filter=lang,
    )
    print(
        f"[info] {len(candidates)} candidates after filtering (min_ds={min_ds}, top_k={top_k}).",
        file=sys.stderr,
    )

    if not candidates:
        print("[warn] No candidates to process. Check --min-ds and --top-k.", file=sys.stderr)
        sys.exit(0)

    candidates = _enrich_candidates(candidates, lang)

    # Assign stable pair IDs
    for i, c in enumerate(candidates):
        c["pair_id"] = f"{lang.upper()}_{i:04d}"

    # Split into batches and write prompt files
    out_dir = _batches_dir(lang)
    out_dir.mkdir(parents=True, exist_ok=True)

    batches: list[list[dict[str, Any]]] = []
    for start in range(0, len(candidates), batch_size):
        batches.append(candidates[start: start + batch_size])

    batch_meta_summary: list[dict[str, Any]] = []
    for idx, batch in enumerate(batches):
        prompt = _build_investigation_prompt(batch, lang)
        batch_file = out_dir / f"batch_{idx:03d}.txt"
        batch_file.write_text(prompt, encoding="utf-8")

        # Store pair metadata alongside prompt so --ingest-response can reconstruct results
        meta_file = out_dir / f"batch_{idx:03d}_meta.json"
        meta_pairs = [
            {
                "pair_id": p["pair_id"],
                "pair_index": i,
                "arabic_root": p["arabic_root"],
                "target_lemma": p["target_lemma"],
                "lang": p.get("lang", lang),
                "discovery_score": float(p.get("discovery_score", 0.0)),
                "masadiq_gloss": p.get("masadiq_gloss", ""),
                "mafahim_gloss": p.get("mafahim_gloss", ""),
                "target_meaning": p.get("target_meaning", ""),
            }
            for i, p in enumerate(batch)
        ]
        meta_file.write_text(json.dumps(meta_pairs, ensure_ascii=False, indent=2), encoding="utf-8")

        batch_meta_summary.append(
            {"batch_index": idx, "file": str(batch_file), "n_pairs": len(batch)}
        )
        print(f"[info] Wrote batch_{idx:03d}.txt ({len(batch)} pairs)", file=sys.stderr)

    # Write manifest
    manifest = {
        "lang": lang,
        "total_pairs": len(candidates),
        "batch_count": len(batches),
        "batch_size": batch_size,
        "min_ds": min_ds,
        "top_k": top_k,
        "batches": batch_meta_summary,
        "instructions": (
            "For each batch_{NNN}.txt, send the file contents to a Claude Code agent. "
            "The agent returns a JSON array of FINDINGS (not scores). Save the response and run:\n"
            f"  python eye2_agent_scorer.py --ingest-response --lang {lang} "
            "--batch-index NNN --response-file <findings.json>"
        ),
    }
    manifest_file = out_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[done] {len(batches)} investigation batch files written to {out_dir}", file=sys.stderr)
    print(f"[done] Manifest: {manifest_file}", file=sys.stderr)
    print(
        f"\nNext step: for each batch_NNN.txt, send it to a Claude Code agent and save "
        f"the findings JSON, then run:\n"
        f"  python eye2_agent_scorer.py --ingest-response --lang {lang} "
        f"--batch-index NNN --response-file <path-to-findings.json>",
        file=sys.stderr,
    )

# ---------------------------------------------------------------------------
# Mode 2: --investigate  (print investigation prompt; agents process externally)
# ---------------------------------------------------------------------------

def cmd_investigate(args: argparse.Namespace) -> None:
    """Print the investigation prompt for a batch file to stdout (for piping to an agent)."""
    batch_file = Path(args.investigate)
    if not batch_file.exists():
        print(f"[error] Batch file not found: {batch_file}", file=sys.stderr)
        sys.exit(1)
    # Print the full detective investigation prompt — the agent is the investigator.
    print(batch_file.read_text(encoding="utf-8"))

# ---------------------------------------------------------------------------
# Verdict mapping: finding → verdict category
# ---------------------------------------------------------------------------

_VERDICT_MAP = {
    # finding + journey_type combinations → verdict
    ("path_found", "direct_preservation"): "confirmed_cognate",
    ("path_found", "semantic_drift"): "confirmed_cognate",
    ("path_found", "specialization"): "confirmed_cognate",
    ("path_found", "generalization"): "confirmed_cognate",
    ("path_found", "metaphorical_extension"): "plausible_link",
    ("path_found", "negation_cognate"): "confirmed_cognate",
    ("path_found", "material_culture"): "confirmed_cognate",
    ("path_found", "shared_loanword"): "shared_loanword",
    ("no_path", "shared_loanword"): "shared_loanword",
    ("no_path", "no_connection"): "no_connection",
}

# Confidence thresholds for upgrading/downgrading
_CONFIDENCE_WEIGHT = {"high": 1.0, "medium": 0.6, "low": 0.3}

# Proper name detection keywords
_PROPER_NAME_SIGNALS = {
    "biblical", "quranic", "proper name", "personal name", "place name",
    "toponym", "anthroponym", "adam", "gabriel", "ishmael", "noah", "moses",
}


def _classify_finding(item: dict[str, Any]) -> str:
    """Map a finding dict to a verdict string."""
    finding = str(item.get("finding", "no_path")).lower().strip()
    journey_type = str(item.get("journey_type", "no_connection")).lower().strip()
    confidence = str(item.get("confidence", "medium")).lower().strip()
    semantic_journey = str(item.get("semantic_journey", "")).lower()
    key_insight = str(item.get("key_insight", "")).lower()

    combined_text = semantic_journey + " " + key_insight

    # Proper name check
    if any(sig in combined_text for sig in _PROPER_NAME_SIGNALS):
        return "proper_name"

    verdict = _VERDICT_MAP.get((finding, journey_type))
    if verdict:
        # Downgrade confirmed_cognate to plausible_link if confidence is low
        if verdict == "confirmed_cognate" and confidence == "low":
            return "plausible_link"
        return verdict

    # Fallback logic for unexpected journey_type values
    if finding == "path_found":
        return "plausible_link" if confidence == "low" else "confirmed_cognate"
    return "no_connection"

# ---------------------------------------------------------------------------
# Mode 3: --ingest-response  (parse findings JSON and write JSONL)
# ---------------------------------------------------------------------------

def cmd_ingest_response(args: argparse.Namespace) -> None:
    """Parse agent findings JSON for a batch and write JSONL results."""
    lang = args.lang

    # Resolve meta file: either explicit --batch-meta or derived from --batch-index
    if args.batch_meta:
        meta_file = Path(args.batch_meta)
    elif args.batch_index is not None:
        meta_file = _batches_dir(lang) / f"batch_{args.batch_index:03d}_meta.json"
    else:
        print("[error] Provide --batch-meta <path> or --batch-index <N>.", file=sys.stderr)
        sys.exit(1)

    if not meta_file.exists():
        print(f"[error] Batch meta file not found: {meta_file}", file=sys.stderr)
        sys.exit(1)

    response_file = Path(args.response_file)
    if not response_file.exists():
        print(f"[error] Response file not found: {response_file}", file=sys.stderr)
        sys.exit(1)

    meta_pairs: list[dict[str, Any]] = json.loads(meta_file.read_text(encoding="utf-8"))
    # Build lookup by pair_id
    meta_by_id: dict[str, dict[str, Any]] = {mp["pair_id"]: mp for mp in meta_pairs}

    raw_response = response_file.read_text(encoding="utf-8").strip()

    # Strip markdown fences if present
    if raw_response.startswith("```"):
        parts = raw_response.split("```", 2)
        inner = parts[1]
        if inner.startswith("json"):
            inner = inner[4:]
        raw_response = inner.strip()

    try:
        findings: list[dict[str, Any]] = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        print(f"[error] Failed to parse agent findings JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        out_path = Path(args.output)
    else:
        batch_stem = meta_file.stem.replace("_meta", "")
        out_path = _results_dir(lang) / f"{batch_stem}.jsonl"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped = 0
    verdict_counts: defaultdict[str, int] = defaultdict(int)

    with open(out_path, "w", encoding="utf-8") as fh:
        for item in findings:
            pair_id = str(item.get("pair_id", ""))

            # Try pair_id lookup first, then fall back to pair_index for backwards compat
            if pair_id in meta_by_id:
                c = meta_by_id[pair_id]
            else:
                idx = item.get("pair_index")
                if isinstance(idx, int) and 0 <= idx < len(meta_pairs):
                    c = meta_pairs[idx]
                else:
                    print(
                        f"[warn] Skipping finding with unrecognised pair_id={pair_id!r}",
                        file=sys.stderr,
                    )
                    skipped += 1
                    continue

            verdict = _classify_finding(item)
            verdict_counts[verdict] += 1

            # Derive a semantic_score from confidence for downstream compatibility
            confidence = str(item.get("confidence", "medium")).lower()
            finding = str(item.get("finding", "no_path")).lower()
            if finding == "path_found":
                score = _CONFIDENCE_WEIGHT.get(confidence, 0.5)
            else:
                score = 0.0

            record = {
                "source_lemma": c["arabic_root"],
                "target_lemma": c["target_lemma"],
                "lang_pair": f"ara-{c.get('lang', lang)}",
                "pair_id": c["pair_id"],
                "finding": item.get("finding", "no_path"),
                "semantic_journey": str(item.get("semantic_journey", "")),
                "journey_type": str(item.get("journey_type", "no_connection")),
                "confidence": confidence,
                "key_insight": str(item.get("key_insight", "")),
                "verdict": verdict,
                "semantic_score": score,
                "discovery_score": float(c.get("discovery_score", 0.0)),
                "model": "agent_detective",
                "batch": meta_file.stem.replace("_meta", ""),
            }
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1

    print(f"[done] Wrote {written} findings to {out_path}", file=sys.stderr)
    if skipped:
        print(f"[warn] Skipped {skipped} findings (unrecognised pair IDs).", file=sys.stderr)
    print("[info] Verdict breakdown:", file=sys.stderr)
    for v, count in sorted(verdict_counts.items()):
        print(f"  {v}: {count}", file=sys.stderr)

# ---------------------------------------------------------------------------
# Mode 4: --merge
# ---------------------------------------------------------------------------

def cmd_merge(args: argparse.Namespace) -> None:
    lang = args.lang
    results_dir = _results_dir(lang)

    batch_files = sorted(results_dir.glob("batch_*.jsonl")) if results_dir.exists() else []
    if not batch_files:
        print(f"[error] No batch JSONL files found in {results_dir}", file=sys.stderr)
        sys.exit(1)

    all_records: list[dict[str, Any]] = []
    for bf in batch_files:
        with open(bf, encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    all_records.append(json.loads(raw))
                except json.JSONDecodeError:
                    continue
        print(f"[info] Loaded {bf.name}", file=sys.stderr)

    # Deduplicate: keep best finding per (source, target) pair
    # Priority: confirmed_cognate > plausible_link > shared_loanword > proper_name > no_connection
    _VERDICT_PRIORITY = {
        "confirmed_cognate": 5,
        "plausible_link": 4,
        "shared_loanword": 3,
        "proper_name": 2,
        "no_connection": 1,
    }

    best: dict[tuple[str, str], dict[str, Any]] = {}
    for rec in all_records:
        key = (rec.get("source_lemma", ""), rec.get("target_lemma", ""))
        existing = best.get(key)
        if existing is None:
            best[key] = rec
        else:
            # Compare by verdict priority, then by semantic_score as tie-break
            new_prio = _VERDICT_PRIORITY.get(rec.get("verdict", "no_connection"), 0)
            old_prio = _VERDICT_PRIORITY.get(existing.get("verdict", "no_connection"), 0)
            if new_prio > old_prio or (
                new_prio == old_prio
                and float(rec.get("semantic_score", 0.0)) > float(existing.get("semantic_score", 0.0))
            ):
                best[key] = rec

    # Sort: confirmed first, then plausible, then rest; within group by discovery_score desc
    def _sort_key(r: dict[str, Any]) -> tuple[int, float]:
        prio = _VERDICT_PRIORITY.get(r.get("verdict", "no_connection"), 0)
        ds = float(r.get("discovery_score", 0.0))
        return (-prio, -ds)

    merged = sorted(best.values(), key=_sort_key)

    final_path = _final_path(lang)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    with open(final_path, "w", encoding="utf-8") as fh:
        for rec in merged:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # Summary
    verdict_counts: defaultdict[str, int] = defaultdict(int)
    for rec in merged:
        verdict_counts[rec.get("verdict", "no_connection")] += 1

    confirmed = verdict_counts.get("confirmed_cognate", 0)
    plausible = verdict_counts.get("plausible_link", 0)
    loanwords = verdict_counts.get("shared_loanword", 0)
    proper = verdict_counts.get("proper_name", 0)
    rejected = verdict_counts.get("no_connection", 0)
    discoveries = confirmed + plausible

    print(f"\n[merge] Total findings: {len(merged)}", file=sys.stderr)
    print(f"[merge] Verdict summary:", file=sys.stderr)
    print(f"  confirmed_cognate : {confirmed}", file=sys.stderr)
    print(f"  plausible_link    : {plausible}", file=sys.stderr)
    print(f"  shared_loanword   : {loanwords}", file=sys.stderr)
    print(f"  proper_name       : {proper}", file=sys.stderr)
    print(f"  no_connection     : {rejected}", file=sys.stderr)
    print(f"[merge] Total discoveries (confirmed + plausible): {discoveries}", file=sys.stderr)
    print(f"[done] Merged output: {final_path}", file=sys.stderr)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Eye 2 Agent Scorer: prepare/investigate/merge LLM findings (no API key).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--prepare", action="store_true",
        help="Prepare investigation batch prompt files from Eye 1 output (5-10 pairs each).",
    )
    mode.add_argument(
        "--investigate", metavar="BATCH_FILE",
        help="Print the investigation prompt for a batch file to stdout (agent processes externally).",
    )
    mode.add_argument(
        "--ingest-response", action="store_true",
        help="Parse agent findings JSON response and write JSONL results.",
    )
    mode.add_argument(
        "--merge", action="store_true",
        help="Merge all findings JSONL files into a final output with verdict summary.",
    )

    # --prepare options
    p.add_argument("--lang", help="Target language code (got, grc, lat, ...)")
    p.add_argument(
        "--min-ds", type=float, default=0.90, metavar="SCORE",
        help="Minimum Eye 1 discovery_score to include (default: 0.90).",
    )
    p.add_argument(
        "--top-k", type=int, default=3, metavar="K",
        help="Max candidates per Arabic root (default: 3).",
    )
    p.add_argument(
        "--batch-size", type=int, default=_DEFAULT_BATCH_SIZE, metavar="N",
        help=f"Pairs per batch file (default: {_DEFAULT_BATCH_SIZE}, clamped to 5-10).",
    )

    # --ingest-response options
    p.add_argument(
        "--batch-index", type=int, metavar="N",
        help="Batch index (used to locate batch_NNN_meta.json).",
    )
    p.add_argument(
        "--batch-meta", metavar="FILE",
        help="Explicit path to batch_NNN_meta.json.",
    )
    p.add_argument(
        "--response-file", metavar="FILE",
        help="Path to agent findings JSON response file.",
    )

    # shared
    p.add_argument(
        "--output", metavar="FILE",
        help="Output file path (used by --ingest-response).",
    )

    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    if args.prepare:
        if not args.lang:
            print("[error] --prepare requires --lang.", file=sys.stderr)
            sys.exit(1)
        cmd_prepare(args)

    elif args.investigate:
        cmd_investigate(args)

    elif args.ingest_response:
        if not args.response_file:
            print("[error] --ingest-response requires --response-file.", file=sys.stderr)
            sys.exit(1)
        if not args.lang and not args.batch_meta:
            print("[error] --ingest-response requires --lang (or --batch-meta).", file=sys.stderr)
            sys.exit(1)
        cmd_ingest_response(args)

    elif args.merge:
        if not args.lang:
            print("[error] --merge requires --lang.", file=sys.stderr)
            sys.exit(1)
        cmd_merge(args)


if __name__ == "__main__":
    main()
