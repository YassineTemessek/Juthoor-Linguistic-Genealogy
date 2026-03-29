"""Direct evaluation of gold benchmark pairs for ANY language pair.

Evaluates gold pairs from cognate_gold.jsonl for a given source↔target language
using MultiMethodScorer + ConceptMatcher + gloss_similarity, without N×M discovery.

Usage:
  python evaluate_gold_pairs_multilang.py --target lat
  python evaluate_gold_pairs_multilang.py --source ara --target grc
  python evaluate_gold_pairs_multilang.py --source ara --target heb --threshold 0.4
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

# Windows-safe Unicode output
sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

LV2_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = LV2_ROOT.parent
LV0_PROCESSED = REPO_ROOT / "Juthoor-DataCore-LV0/data/processed"
GOLD_BENCHMARK = LV2_ROOT / "resources/benchmarks/cognate_gold.jsonl"
CONCEPTS_FILE = LV2_ROOT / "resources/concepts/concepts_v3_2_enriched.jsonl"
ARABIC_GLOSSES_LOOKUP = LV2_ROOT / "data/processed/arabic/arabic_english_glosses.json"
ENGLISH_CORPUS = LV2_ROOT / "data/processed/english/english_ipa_merged_pos.jsonl"

sys.path.insert(0, str(LV2_ROOT / "src"))

# ---------------------------------------------------------------------------
# Corpus map (mirrors run_discovery_multilang.py)
# ---------------------------------------------------------------------------

CORPUS_PATHS: dict[str, str | None] = {
    "ara": "quranic_arabic/sources/quran_lemmas_enriched.jsonl",
    "ara_classical": "arabic/classical/lexemes.jsonl",
    "heb": "hebrew/sources/kaikki.jsonl",
    "lat": "latin/classical/sources/kaikki.jsonl",
    "grc": "ancient_greek/sources/kaikki.jsonl",
    "per": "persian/modern/sources/kaikki.jsonl",
    "arc": "aramaic/classical/sources/kaikki.jsonl",
    "eng": None,  # English uses LV2-specific enriched corpus
    "enm": "english_middle/sources/kaikki.jsonl",
    "ang": "english_old/sources/kaikki.jsonl",
}

ARABIC_SCHEMA_LANGS: set[str] = {"ara", "ara_classical"}
SEMITIC_LANGS: set[str] = {"ara", "heb", "arc", "ara_classical"}

# ---------------------------------------------------------------------------
# Arabic normalisation helpers
# ---------------------------------------------------------------------------

_DIAC = re.compile(r"[\u064B-\u065F\u0670\u0640]")
_HAMZA = str.maketrans({
    "\u0623": "\u0627",  # أ → ا
    "\u0625": "\u0627",  # إ → ا
    "\u0622": "\u0627",  # آ → ا
    "\u0671": "\u0627",  # ٱ → ا
    "\u0624": "\u0648",  # ؤ → و
    "\u0626": "\u064A",  # ئ → ي
    "\u0621": "\u0627",  # ء → ا
})


def _norm_arabic(text: str) -> str:
    return _DIAC.sub("", text).translate(_HAMZA).strip()


# ---------------------------------------------------------------------------
# Corpus loading
# ---------------------------------------------------------------------------

def _corpus_path(lang: str) -> Path | None:
    rel = CORPUS_PATHS.get(lang)
    if rel is None:
        return None
    return LV0_PROCESSED / rel


def load_corpus_as_lookup(lang: str) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    """Load a language corpus and return (by_lemma, by_root) lookup dicts.

    For Arabic-schema languages: by_lemma keyed by normalised Arabic lemma,
    by_root keyed by normalised root.
    For all others: by_lemma keyed by lowercase lemma, by_root is empty.
    """
    is_arabic = lang in ARABIC_SCHEMA_LANGS

    if lang == "eng":
        path = ENGLISH_CORPUS
    else:
        path = _corpus_path(lang)
        if path is None:
            raise ValueError(f"Unknown language code: {lang!r}")

    if not path.exists():
        raise FileNotFoundError(f"Corpus not found: {path}")

    by_lemma: dict[str, list[dict]] = {}
    by_root: dict[str, list[dict]] = {}

    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            lemma_raw = str(entry.get("lemma", "") or "").strip()
            if not lemma_raw:
                continue

            if is_arabic:
                key = _norm_arabic(lemma_raw)
                root_raw = str(entry.get("root", "") or "").strip()
                root_key = _norm_arabic(root_raw) if root_raw else ""
            else:
                key = lemma_raw.lower()
                root_key = ""

            if key:
                by_lemma.setdefault(key, []).append(entry)
            if root_key:
                by_root.setdefault(root_key, []).append(entry)

    return by_lemma, by_root


def load_arabic_glosses(path: Path) -> dict[str, list[str]]:
    """Load arabic_english_glosses.json → {normalised_arabic: [gloss1, ...]}."""
    with path.open(encoding="utf-8") as fh:
        raw = json.load(fh)
    return {_norm_arabic(k): v.get("english_glosses", []) for k, v in raw.items()}


# ---------------------------------------------------------------------------
# Gold pair loading
# ---------------------------------------------------------------------------

def load_gold_pairs(path: Path, source_lang: str, target_lang: str) -> list[dict]:
    """Load gold pairs matching source_lang ↔ target_lang from cognate_gold.jsonl."""
    pairs = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            src = rec.get("source", {})
            tgt = rec.get("target", {})
            src_lang = src.get("lang", "")
            tgt_lang = tgt.get("lang", "")
            if src_lang == source_lang and tgt_lang == target_lang:
                pairs.append(rec)
            elif src_lang == target_lang and tgt_lang == source_lang:
                # Swap so source is always first
                rec = dict(rec)
                rec["source"], rec["target"] = rec["target"], rec["source"]
                pairs.append(rec)
    return pairs


# ---------------------------------------------------------------------------
# Entry lookup helpers
# ---------------------------------------------------------------------------

def find_source_entry(
    lemma: str,
    gloss: str,
    lang: str,
    by_lemma: dict[str, list[dict]],
    by_root: dict[str, list[dict]],
    gloss_lookup: dict[str, list[str]] | None,
) -> dict:
    """Return the best corpus entry for the source lemma, or a synthetic stub."""
    is_arabic = lang in ARABIC_SCHEMA_LANGS

    if is_arabic:
        norm = _norm_arabic(lemma)
    else:
        norm = lemma.strip().lower()

    # 1. Exact match
    candidates = by_lemma.get(norm, [])
    if candidates:
        return candidates[0]

    # 2. Root match (Arabic only)
    if is_arabic:
        candidates = by_root.get(norm, [])
        if candidates:
            return candidates[0]

    # 3. Prefix partial match
    for key, entries in by_lemma.items():
        if key.startswith(norm) or norm.startswith(key):
            return entries[0]

    # 4. Synthetic fallback
    if is_arabic and gloss_lookup is not None:
        glosses_from_lookup = gloss_lookup.get(norm, [])
        english_gloss = gloss or (glosses_from_lookup[0] if glosses_from_lookup else "")
    else:
        english_gloss = gloss or ""

    return {
        "lemma": lemma,
        "root": lemma,
        "translit": "",
        "ipa": "",
        "english_gloss": english_gloss,
        "meaning_text": english_gloss,
        "_synthetic": True,
    }


def find_target_entry(
    lemma: str,
    gloss: str,
    by_lemma: dict[str, list[dict]],
) -> dict:
    """Return the best corpus entry for the target lemma, or a synthetic stub."""
    key = lemma.strip().lower()

    candidates = by_lemma.get(key, [])
    if candidates:
        return candidates[0]

    # Prefix partial match
    for k, entries in by_lemma.items():
        if k.startswith(key) or key.startswith(k):
            return entries[0]

    return {
        "lemma": lemma,
        "meaning_text": gloss or "",
        "_synthetic": True,
    }


# ---------------------------------------------------------------------------
# IPA injection for non-Latin-script targets
# ---------------------------------------------------------------------------

def _prepare_target_for_scoring(tgt: dict) -> dict:
    """For non-Latin-script targets, inject IPA as lemma so scorer can work."""
    tgt_lemma = str(tgt.get("lemma", "") or "").strip()
    if tgt_lemma and not tgt_lemma[0].isascii():
        tgt_ipa = str(tgt.get("ipa", "") or "").strip()
        clean_ipa = tgt_ipa.strip("/[]").split(",")[0].strip()
        if clean_ipa:
            tgt_for_scoring = dict(tgt)
            tgt_for_scoring["lemma"] = clean_ipa
            return tgt_for_scoring
    return tgt


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_pair(
    source_entry: dict,
    target_entry: dict,
    scorer,
    concept_matcher,
) -> dict[str, float]:
    """Run all scorers on a single pair; return score components."""
    from juthoor_cognatediscovery_lv2.discovery.gloss_similarity import gloss_similarity

    tgt_for_scoring = _prepare_target_for_scoring(target_entry)

    mm_result = scorer.score_pair(source_entry, tgt_for_scoring)
    phonetic = mm_result.best_score
    best_method = mm_result.best_method

    gloss_sim   = gloss_similarity(source_entry, target_entry)
    concept_sim = concept_matcher.concept_similarity(source_entry, target_entry)
    semantic    = max(gloss_sim, concept_sim)

    combined = phonetic * 0.7 + semantic * 0.3

    return {
        "phonetic":    phonetic,
        "gloss_sim":   gloss_sim,
        "concept_sim": concept_sim,
        "semantic":    semantic,
        "combined":    combined,
        "best_method": best_method,
    }


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

def print_distribution(label: str, values: list[float]) -> None:
    if not values:
        print(f"  {label}: no data")
        return
    s = sorted(values)
    n = len(s)
    mean   = statistics.mean(s)
    median = statistics.median(s)
    p25    = s[int(0.25 * n)]
    p75    = s[int(0.75 * n)]
    p90    = s[int(0.90 * n)]
    print(
        f"  {label}: mean={mean:.3f}  median={median:.3f}"
        f"  p25={p25:.3f}  p75={p75:.3f}  p90={p90:.3f}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate gold benchmark pairs for any language pair.",
    )
    parser.add_argument("--source", default="ara", help="Source language code (default: ara)")
    parser.add_argument("--target", required=True, help="Target language code (e.g. lat, grc, heb)")
    parser.add_argument("--threshold", type=float, default=0.5, help="Score threshold (default: 0.5)")
    args = parser.parse_args()

    source_lang = args.source
    target_lang = args.target
    threshold   = args.threshold

    # ------------------------------------------------------------------
    # Path validation
    # ------------------------------------------------------------------
    for p, label in [(GOLD_BENCHMARK, "gold benchmark")]:
        if not p.exists():
            print(f"ERROR: missing {label}: {p}")
            sys.exit(1)

    # ------------------------------------------------------------------
    # Imports
    # ------------------------------------------------------------------
    from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScorer
    from juthoor_cognatediscovery_lv2.discovery.concept_matcher import ConceptMatcher

    # ------------------------------------------------------------------
    # Load gold pairs
    # ------------------------------------------------------------------
    print(f"Loading gold pairs for {source_lang} ↔ {target_lang}...")
    gold_pairs = load_gold_pairs(GOLD_BENCHMARK, source_lang, target_lang)
    if not gold_pairs:
        print(f"  No gold pairs found for {source_lang} ↔ {target_lang}.")
        print("  Available language codes: " + ", ".join(sorted(CORPUS_PATHS.keys())))
        sys.exit(0)
    print(f"  {len(gold_pairs)} gold pairs loaded")

    # ------------------------------------------------------------------
    # Load source corpus
    # ------------------------------------------------------------------
    print(f"Loading {source_lang} corpus...")
    src_by_lemma, src_by_root = load_corpus_as_lookup(source_lang)
    print(f"  {len(src_by_lemma):,} lemmas, {len(src_by_root):,} roots")

    # Load Arabic glosses only when source is Arabic-schema
    gloss_lookup: dict[str, list[str]] | None = None
    if source_lang in ARABIC_SCHEMA_LANGS and ARABIC_GLOSSES_LOOKUP.exists():
        print("Loading Arabic-English glosses...")
        gloss_lookup = load_arabic_glosses(ARABIC_GLOSSES_LOOKUP)
        print(f"  {len(gloss_lookup):,} gloss entries")

    # ------------------------------------------------------------------
    # Load target corpus
    # ------------------------------------------------------------------
    print(f"Loading {target_lang} corpus...")
    tgt_by_lemma, _ = load_corpus_as_lookup(target_lang)
    print(f"  {len(tgt_by_lemma):,} lemmas")

    # ------------------------------------------------------------------
    # Initialise scorers
    # ------------------------------------------------------------------
    print("Initialising scorers...")
    scorer = MultiMethodScorer()
    concept_matcher = ConceptMatcher(CONCEPTS_FILE)
    print(f"  ConceptMatcher: {concept_matcher.concept_count} concepts loaded")

    # ------------------------------------------------------------------
    # Score every gold pair
    # ------------------------------------------------------------------
    print(f"\nScoring {len(gold_pairs)} gold pairs...")
    results = []
    synthetic_src = 0
    synthetic_tgt = 0

    for i, gp in enumerate(gold_pairs, 1):
        src_gold = gp["source"]
        tgt_gold = gp["target"]

        src_entry = find_source_entry(
            src_gold["lemma"],
            src_gold.get("gloss", ""),
            source_lang,
            src_by_lemma,
            src_by_root,
            gloss_lookup,
        )
        tgt_entry = find_target_entry(
            tgt_gold["lemma"],
            tgt_gold.get("gloss", ""),
            tgt_by_lemma,
        )

        if src_entry.get("_synthetic"):
            synthetic_src += 1
        if tgt_entry.get("_synthetic"):
            synthetic_tgt += 1

        scores = score_pair(src_entry, tgt_entry, scorer, concept_matcher)

        results.append({
            "source_lemma":     src_gold["lemma"],
            "target_lemma":     tgt_gold["lemma"],
            "gold_gloss_src":   src_gold.get("gloss", ""),
            "gold_gloss_tgt":   tgt_gold.get("gloss", ""),
            "src_synthetic":    src_entry.get("_synthetic", False),
            "tgt_synthetic":    tgt_entry.get("_synthetic", False),
            "confidence":       gp.get("confidence", 1.0),
            **scores,
        })

        if i % 100 == 0:
            print(f"  Scored {i}/{len(gold_pairs)}...")

    print(
        f"  Done. Synthetic source: {synthetic_src}, synthetic target: {synthetic_tgt}"
    )

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    n          = len(results)
    phonetics  = [r["phonetic"]    for r in results]
    gloss_sims = [r["gloss_sim"]   for r in results]
    concept_s  = [r["concept_sim"] for r in results]
    semantics  = [r["semantic"]    for r in results]
    combineds  = [r["combined"]    for r in results]

    print("\n" + "=" * 70)
    print(f"SCORE DISTRIBUTIONS  ({source_lang} → {target_lang}, n={n})")
    print("=" * 70)
    print_distribution("phonetic ", phonetics)
    print_distribution("gloss_sim", gloss_sims)
    print_distribution("concept  ", concept_s)
    print_distribution("semantic ", semantics)
    print_distribution("combined ", combineds)

    print("\n" + "=" * 70)
    print("THRESHOLD COUNTS")
    print("=" * 70)
    for label, vals, thresholds in [
        ("phonetic ", phonetics,  [0.3, 0.5, 0.7]),
        ("semantic ", semantics,  [0.0, 0.1, 0.3]),
        ("combined ", combineds,  [0.3, 0.5]),
    ]:
        row = f"  {label}:"
        for t in thresholds:
            cnt = sum(1 for v in vals if v > t)
            row += f"  >{t}: {cnt}/{n} ({100*cnt/n:.1f}%)"
        print(row)

    nonzero_phonetic = sum(1 for v in phonetics if v > 0)
    nonzero_semantic = sum(1 for v in semantics if v > 0)
    nonzero_combined = sum(1 for v in combineds if v > threshold)
    print(f"\n  Pairs with phonetic > 0      : {nonzero_phonetic}/{n} ({100*nonzero_phonetic/n:.1f}%)")
    print(f"  Pairs with semantic > 0      : {nonzero_semantic}/{n} ({100*nonzero_semantic/n:.1f}%)")
    print(f"  Pairs with combined > {threshold:.1f}  : {nonzero_combined}/{n} ({100*nonzero_combined/n:.1f}%)")

    # ------------------------------------------------------------------
    # Top 20 highest-scoring
    # ------------------------------------------------------------------
    sorted_desc = sorted(results, key=lambda r: r["combined"], reverse=True)
    print("\n" + "=" * 70)
    print("TOP 20 HIGHEST-SCORING GOLD PAIRS")
    print("=" * 70)
    print(
        f"  {'source':<18} {'target':<18} {'phonetic':>8} {'gloss':>6}"
        f" {'concept':>7} {'combined':>8}  method"
    )
    print("  " + "-" * 72)
    for r in sorted_desc[:20]:
        syn_flag = "*" if r["src_synthetic"] or r["tgt_synthetic"] else " "
        print(
            f"  {syn_flag}{r['source_lemma']:<17} {r['target_lemma']:<18}"
            f" {r['phonetic']:>8.3f} {r['gloss_sim']:>6.3f}"
            f" {r['concept_sim']:>7.3f} {r['combined']:>8.3f}  {r['best_method']}"
        )

    # ------------------------------------------------------------------
    # Bottom 20 lowest-scoring
    # ------------------------------------------------------------------
    sorted_asc = sorted(results, key=lambda r: r["combined"])
    print("\n" + "=" * 70)
    print("BOTTOM 20 LOWEST-SCORING GOLD PAIRS")
    print("=" * 70)
    print(
        f"  {'source':<18} {'target':<18} {'phonetic':>8} {'gloss':>6}"
        f" {'concept':>7} {'combined':>8}  gold_gloss"
    )
    print("  " + "-" * 72)
    for r in sorted_asc[:20]:
        syn_flag = "*" if r["src_synthetic"] or r["tgt_synthetic"] else " "
        gl = f"{r['gold_gloss_src']} / {r['gold_gloss_tgt']}"
        print(
            f"  {syn_flag}{r['source_lemma']:<17} {r['target_lemma']:<18}"
            f" {r['phonetic']:>8.3f} {r['gloss_sim']:>6.3f}"
            f" {r['concept_sim']:>7.3f} {r['combined']:>8.3f}  {gl}"
        )

    # ------------------------------------------------------------------
    # Method distribution
    # ------------------------------------------------------------------
    method_counts = Counter(r["best_method"] for r in results if r["best_method"])
    print("\n" + "=" * 70)
    print("BEST METHOD DISTRIBUTION")
    print("=" * 70)
    for method, cnt in method_counts.most_common():
        pct = 100 * cnt / n
        print(f"  {method:<35} {cnt:>4}  ({pct:.1f}%)")

    print("\n" + "=" * 70)
    print(f"TOTAL GOLD PAIRS EVALUATED: {n}  ({source_lang} → {target_lang})")
    print(f"  threshold used: {threshold}")
    print("  * = synthetic entry (corpus match not found, gold gloss used)")
    print("=" * 70)


if __name__ == "__main__":
    main()
