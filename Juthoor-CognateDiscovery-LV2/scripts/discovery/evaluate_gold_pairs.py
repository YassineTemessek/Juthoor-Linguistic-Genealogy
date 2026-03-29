"""Direct evaluation of Arabic-English gold benchmark pairs.

Evaluates all 837 ara<->eng gold pairs from cognate_gold.jsonl using:
  - MultiMethodScorer (phonetic / structural methods)
  - ConceptMatcher  (concept-level semantic similarity)
  - gloss_similarity (Jaccard gloss word overlap)

No N×M candidate generation — every gold pair is scored directly.
"""
from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

# Windows-safe Unicode output
sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

LV2_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LV2_ROOT / "src"))

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
# Data loading
# ---------------------------------------------------------------------------

def load_gold_pairs(path: Path) -> list[dict]:
    """Load Arabic-English pairs from cognate_gold.jsonl."""
    pairs = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            src = rec.get("source", {})
            tgt = rec.get("target", {})
            if src.get("lang") == "ara" and tgt.get("lang") == "eng":
                pairs.append(rec)
    return pairs


def load_arabic_corpus(path: Path) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    """Return two lookup dicts keyed by normalised lemma and normalised root."""
    by_lemma: dict[str, list[dict]] = {}
    by_root:  dict[str, list[dict]] = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            lemma_key = _norm_arabic(entry.get("lemma", ""))
            root_key  = _norm_arabic(entry.get("root", ""))
            if lemma_key:
                by_lemma.setdefault(lemma_key, []).append(entry)
            if root_key:
                by_root.setdefault(root_key, []).append(entry)
    return by_lemma, by_root


def load_english_corpus(path: Path) -> dict[str, list[dict]]:
    """Return lookup dict keyed by lowercase lemma."""
    by_lemma: dict[str, list[dict]] = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            key = (entry.get("lemma") or "").strip().lower()
            if key:
                by_lemma.setdefault(key, []).append(entry)
    return by_lemma


def load_glosses(path: Path) -> dict[str, list[str]]:
    """Load arabic_english_glosses.json → {arabic_form: [gloss1, ...]}."""
    with path.open(encoding="utf-8") as fh:
        raw = json.load(fh)
    # Key normalisation
    return {_norm_arabic(k): v.get("english_glosses", []) for k, v in raw.items()}


# ---------------------------------------------------------------------------
# Entry lookup helpers
# ---------------------------------------------------------------------------

def find_arabic_entry(
    lemma: str,
    gloss: str,
    by_lemma: dict[str, list[dict]],
    by_root: dict[str, list[dict]],
    gloss_lookup: dict[str, list[str]],
) -> dict:
    """Return the best Arabic corpus entry for a gold lemma, or a synthetic stub."""
    norm = _norm_arabic(lemma)

    # 1. Exact normalised lemma match
    candidates = by_lemma.get(norm, [])
    if candidates:
        return candidates[0]

    # 2. Root match (use lemma as root key)
    candidates = by_root.get(norm, [])
    if candidates:
        return candidates[0]

    # 3. Partial match — any lemma that starts with the normalised form
    for key, entries in by_lemma.items():
        if key.startswith(norm) or norm.startswith(key):
            return entries[0]

    # 4. Synthetic fallback — use gold gloss for semantic scoring
    glosses_from_lookup = gloss_lookup.get(norm, [])
    english_gloss = gloss or (glosses_from_lookup[0] if glosses_from_lookup else "")
    return {
        "lemma": lemma,
        "root": lemma,
        "translit": "",
        "ipa": "",
        "english_gloss": english_gloss,
        "_synthetic": True,
    }


def find_english_entry(
    lemma: str,
    gloss: str,
    by_lemma: dict[str, list[dict]],
) -> dict:
    """Return the best English corpus entry for a gold lemma, or a synthetic stub."""
    key = lemma.strip().lower()

    candidates = by_lemma.get(key, [])
    if candidates:
        return candidates[0]

    # Partial match
    for k, entries in by_lemma.items():
        if k.startswith(key) or key.startswith(k):
            return entries[0]

    # Synthetic fallback
    return {
        "lemma": lemma,
        "meaning_text": gloss or "",
        "_synthetic": True,
    }


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_pair(
    arabic_entry: dict,
    english_entry: dict,
    scorer,
    concept_matcher,
) -> dict[str, float]:
    """Run all scorers on a single pair; return score components."""
    from juthoor_cognatediscovery_lv2.discovery.gloss_similarity import gloss_similarity

    # Phonetic / structural score from MultiMethodScorer
    mm_result = scorer.score_pair(arabic_entry, english_entry)
    phonetic = mm_result.best_score
    best_method = mm_result.best_method

    # Semantic scores
    gloss_sim   = gloss_similarity(arabic_entry, english_entry)
    concept_sim = concept_matcher.concept_similarity(arabic_entry, english_entry)
    semantic    = max(gloss_sim, concept_sim)

    # Combined score: weight phonetic more, semantic as bonus
    combined = 0.6 * phonetic + 0.4 * semantic

    return {
        "phonetic":    phonetic,
        "gloss_sim":   gloss_sim,
        "concept_sim": concept_sim,
        "semantic":    semantic,
        "combined":    combined,
        "best_method": best_method,
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_distribution(label: str, values: list[float]) -> None:
    if not values:
        print(f"  {label}: no data")
        return
    s = sorted(values)
    n = len(s)
    mean = statistics.mean(s)
    median = statistics.median(s)
    p25 = s[int(0.25 * n)]
    p75 = s[int(0.75 * n)]
    p90 = s[int(0.90 * n)]
    print(
        f"  {label}: mean={mean:.3f}  median={median:.3f}"
        f"  p25={p25:.3f}  p75={p75:.3f}  p90={p90:.3f}"
    )


def threshold_counts(label: str, values: list[float], thresholds: list[float]) -> None:
    n = len(values)
    parts = [f"  {label}:"]
    for t in thresholds:
        cnt = sum(1 for v in values if v > t)
        parts.append(f"  >{t:.1f}: {cnt}/{n} ({100*cnt/n:.1f}%)")
    print("".join(parts))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------
    gold_path   = LV2_ROOT / "resources" / "benchmarks" / "cognate_gold.jsonl"
    arabic_path = LV2_ROOT / "data" / "processed" / "arabic" / "unified_arabic_discovery.jsonl"
    gloss_path  = LV2_ROOT / "data" / "processed" / "arabic" / "arabic_english_glosses.json"
    english_path= LV2_ROOT / "data" / "processed" / "english" / "english_enriched_discovery.jsonl"
    concepts_path = LV2_ROOT / "resources" / "concepts" / "concepts_v3_2_enriched.jsonl"

    for p in [gold_path, arabic_path, gloss_path, english_path]:
        if not p.exists():
            print(f"ERROR: missing file: {p}")
            sys.exit(1)

    # ------------------------------------------------------------------
    # Imports (after sys.path setup)
    # ------------------------------------------------------------------
    from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScorer
    from juthoor_cognatediscovery_lv2.discovery.concept_matcher import ConceptMatcher

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    print("Loading gold benchmark pairs...")
    gold_pairs = load_gold_pairs(gold_path)
    print(f"  {len(gold_pairs)} Arabic-English gold pairs loaded")

    print("Loading Arabic corpus (may take a moment)...")
    ara_by_lemma, ara_by_root = load_arabic_corpus(arabic_path)
    print(f"  {len(ara_by_lemma):,} normalised Arabic lemmas, {len(ara_by_root):,} roots")

    print("Loading Arabic-English glosses...")
    gloss_lookup = load_glosses(gloss_path)
    print(f"  {len(gloss_lookup):,} gloss entries")

    print("Loading English corpus (may take a moment)...")
    eng_by_lemma = load_english_corpus(english_path)
    print(f"  {len(eng_by_lemma):,} English lemmas")

    print("Initialising scorers...")
    scorer = MultiMethodScorer()
    concept_matcher = ConceptMatcher(concepts_path)
    print(f"  ConceptMatcher: {concept_matcher.concept_count} concepts loaded")

    # ------------------------------------------------------------------
    # Score every gold pair
    # ------------------------------------------------------------------
    print(f"\nScoring {len(gold_pairs)} gold pairs...")
    results = []
    synthetic_arabic = 0
    synthetic_english = 0
    missing_arabic = 0
    missing_english = 0

    for i, gp in enumerate(gold_pairs, 1):
        src = gp["source"]
        tgt = gp["target"]

        ara_entry = find_arabic_entry(
            src["lemma"], src.get("gloss", ""),
            ara_by_lemma, ara_by_root, gloss_lookup,
        )
        eng_entry = find_english_entry(
            tgt["lemma"], tgt.get("gloss", ""),
            eng_by_lemma,
        )

        if ara_entry.get("_synthetic"):
            synthetic_arabic += 1
        if eng_entry.get("_synthetic"):
            synthetic_english += 1

        scores = score_pair(ara_entry, eng_entry, scorer, concept_matcher)

        results.append({
            "arabic":      src["lemma"],
            "english":     tgt["lemma"],
            "gold_gloss_ara": src.get("gloss", ""),
            "gold_gloss_eng": tgt.get("gloss", ""),
            "ara_synthetic": ara_entry.get("_synthetic", False),
            "eng_synthetic": eng_entry.get("_synthetic", False),
            "confidence":  gp.get("confidence", 1.0),
            **scores,
        })

        if i % 100 == 0:
            print(f"  Scored {i}/{len(gold_pairs)}...")

    print(f"  Done. Synthetic Arabic entries: {synthetic_arabic}, Synthetic English: {synthetic_english}")

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    phonetics  = [r["phonetic"]    for r in results]
    gloss_sims = [r["gloss_sim"]   for r in results]
    concept_s  = [r["concept_sim"] for r in results]
    semantics  = [r["semantic"]    for r in results]
    combineds  = [r["combined"]    for r in results]

    print("\n" + "=" * 70)
    print("SCORE DISTRIBUTIONS")
    print("=" * 70)
    print_distribution("phonetic ", phonetics)
    print_distribution("gloss_sim", gloss_sims)
    print_distribution("concept  ", concept_s)
    print_distribution("semantic ", semantics)
    print_distribution("combined ", combineds)

    print("\n" + "=" * 70)
    print("THRESHOLD COUNTS")
    print("=" * 70)
    n = len(results)
    for label, vals, thresholds in [
        ("phonetic ", phonetics,  [0.3, 0.5, 0.6, 0.7]),
        ("gloss_sim", gloss_sims, [0.0, 0.1, 0.3, 0.5]),
        ("concept  ", concept_s,  [0.0, 0.3, 0.9]),
        ("semantic ", semantics,  [0.0, 0.1, 0.3]),
        ("combined ", combineds,  [0.3, 0.4, 0.5, 0.6]),
    ]:
        row = f"  {label}:"
        for t in thresholds:
            cnt = sum(1 for v in vals if v > t)
            row += f"  >{t}: {cnt}/{n} ({100*cnt/n:.1f}%)"
        print(row)

    # Coverage: any non-zero signal
    nonzero_phonetic = sum(1 for v in phonetics if v > 0)
    nonzero_semantic = sum(1 for v in semantics if v > 0)
    nonzero_combined = sum(1 for v in combineds if v > 0.3)
    print(f"\n  Pairs with phonetic > 0  : {nonzero_phonetic}/{n} ({100*nonzero_phonetic/n:.1f}%)")
    print(f"  Pairs with semantic > 0  : {nonzero_semantic}/{n} ({100*nonzero_semantic/n:.1f}%)")
    print(f"  Pairs with combined > 0.3: {nonzero_combined}/{n} ({100*nonzero_combined/n:.1f}%)")

    # ------------------------------------------------------------------
    # Top 20 highest-scoring
    # ------------------------------------------------------------------
    sorted_desc = sorted(results, key=lambda r: r["combined"], reverse=True)
    print("\n" + "=" * 70)
    print("TOP 20 HIGHEST-SCORING GOLD PAIRS")
    print("=" * 70)
    print(f"  {'Arabic':<15} {'English':<15} {'phonetic':>8} {'gloss_sim':>9} {'concept':>7} {'combined':>8}  method")
    print("  " + "-" * 68)
    for r in sorted_desc[:20]:
        syn_flag = "*" if r["ara_synthetic"] or r["eng_synthetic"] else " "
        print(
            f"  {syn_flag}{r['arabic']:<14} {r['english']:<15}"
            f" {r['phonetic']:>8.3f} {r['gloss_sim']:>9.3f} {r['concept_sim']:>7.3f}"
            f" {r['combined']:>8.3f}  {r['best_method']}"
        )

    # ------------------------------------------------------------------
    # Bottom 20 lowest-scoring
    # ------------------------------------------------------------------
    sorted_asc = sorted(results, key=lambda r: r["combined"])
    print("\n" + "=" * 70)
    print("BOTTOM 20 LOWEST-SCORING GOLD PAIRS")
    print("=" * 70)
    print(f"  {'Arabic':<15} {'English':<15} {'phonetic':>8} {'gloss_sim':>9} {'concept':>7} {'combined':>8}  gold_gloss")
    print("  " + "-" * 68)
    for r in sorted_asc[:20]:
        syn_flag = "*" if r["ara_synthetic"] or r["eng_synthetic"] else " "
        gl = f"{r['gold_gloss_ara']} / {r['gold_gloss_eng']}"
        print(
            f"  {syn_flag}{r['arabic']:<14} {r['english']:<15}"
            f" {r['phonetic']:>8.3f} {r['gloss_sim']:>9.3f} {r['concept_sim']:>7.3f}"
            f" {r['combined']:>8.3f}  {gl}"
        )

    # ------------------------------------------------------------------
    # Method breakdown
    # ------------------------------------------------------------------
    from collections import Counter
    method_counts = Counter(r["best_method"] for r in results if r["best_method"])
    print("\n" + "=" * 70)
    print("BEST METHOD DISTRIBUTION (non-zero phonetic pairs only)")
    print("=" * 70)
    for method, cnt in method_counts.most_common():
        pct = 100 * cnt / n
        print(f"  {method:<30} {cnt:>4}  ({pct:.1f}%)")

    print("\n" + "=" * 70)
    print(f"TOTAL GOLD PAIRS EVALUATED: {n}")
    print("  * = synthetic entry (corpus match not found, gold gloss used)")
    print("=" * 70)


if __name__ == "__main__":
    main()
