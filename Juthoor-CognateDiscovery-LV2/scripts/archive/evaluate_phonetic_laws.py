"""Evaluate PhoneticLawScorer against expanded benchmark pairs.

Computes:
- Mean phonetic law score for gold Arabic<->English pairs
- Mean score for silver pairs
- Mean score for random negative pairs
- Score distributions and thresholds
- Per-confidence-tier breakdown
- Top-scoring and bottom-scoring pairs for analysis
"""
from __future__ import annotations

import io
import json
import random
import statistics
import sys
from pathlib import Path

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Ensure we can import from src/
SCRIPT_DIR = Path(__file__).resolve().parent
LV2_ROOT = SCRIPT_DIR.parent
SRC_ROOT = LV2_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import PhoneticLawScorer
from juthoor_cognatediscovery_lv2.discovery.correspondence import cross_lingual_skeleton_score

BENCHMARK_DIR = LV2_ROOT / "resources" / "benchmarks"
GOLD_PATH = BENCHMARK_DIR / "cognate_gold.jsonl"
SILVER_PATH = BENCHMARK_DIR / "cognate_silver.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def pct(values: list[float], threshold: float) -> tuple[float, int]:
    n = sum(1 for v in values if v > threshold)
    return (n / len(values) * 100) if values else 0.0, n


def score_pairs(
    pairs: list[dict], scorer: PhoneticLawScorer
) -> list[dict]:
    results = []
    for p in pairs:
        src = p.get("source", {})
        tgt = p.get("target", {})
        result = scorer.score_pair(src, tgt)
        results.append(
            {
                "ara": src.get("lemma", ""),
                "eng": tgt.get("lemma", ""),
                "confidence": p.get("confidence"),
                "phonetic_law_score": result["phonetic_law_score"],
                "best_projection": result.get("best_projection", ""),
                "details": result.get("projection_details", {}),
                "phonetic_law_bonus": scorer.phonetic_law_bonus(src, tgt),
                "skeleton_score": cross_lingual_skeleton_score(
                    src.get("lemma", ""), tgt.get("lemma", "")
                ),
            }
        )
    return results


def print_group_stats(label: str, scores: list[float], bonuses: list[float]) -> None:
    if not scores:
        print(f"  {label}: no pairs")
        return
    mean = statistics.mean(scores)
    median = statistics.median(scores)
    std = statistics.stdev(scores) if len(scores) > 1 else 0.0
    p40, n40 = pct(scores, 0.4)
    p60, n60 = pct(scores, 0.6)
    p80, n80 = pct(scores, 0.8)
    bonus_mean = statistics.mean(bonuses)
    bonus_nonzero = sum(1 for b in bonuses if b > 0)
    print(f"  Mean score:               {mean:.4f}")
    print(f"  Median score:             {median:.4f}")
    print(f"  Std dev:                  {std:.4f}")
    print(f"  Score > 0.4 (bonus):      {p40:.1f}% (N={n40})")
    print(f"  Score > 0.6 (strong):     {p60:.1f}% (N={n60})")
    print(f"  Score > 0.8 (excellent):  {p80:.1f}% (N={n80})")
    print(f"  Mean bonus applied:       {bonus_mean:.4f}")
    print(f"  Pairs receiving bonus:    {bonus_nonzero}/{len(bonuses)}")


def main() -> None:
    print("Loading benchmark data...")
    gold_all = load_jsonl(GOLD_PATH)
    silver_all = load_jsonl(SILVER_PATH)

    # Filter gold to ara<->eng only
    gold_ara_eng = [
        p for p in gold_all
        if p.get("source", {}).get("lang") == "ara"
        and p.get("target", {}).get("lang") == "eng"
    ]
    print(f"Gold total: {len(gold_all)}, ara<->eng: {len(gold_ara_eng)}")
    print(f"Silver total: {len(silver_all)}")

    # Generate negative pairs — take arabic lemmas from gold, pair with shuffled english
    rng = random.Random(42)
    arabic_lemmas = [p["source"]["lemma"] for p in gold_ara_eng]
    english_lemmas = [p["target"]["lemma"] for p in gold_ara_eng]
    shuffled_english = english_lemmas[:]
    rng.shuffle(shuffled_english)
    # Ensure no accidental real pair (shift by one position)
    negatives_raw = []
    for i, ara in enumerate(arabic_lemmas[:200]):
        # Pick an english lemma that doesn't match the real pair
        eng = shuffled_english[(i + 100) % len(shuffled_english)]
        negatives_raw.append(
            {
                "source": {"lang": "ara", "lemma": ara},
                "target": {"lang": "eng", "lemma": eng},
            }
        )
    # Drop any that accidentally match a real gold pair
    gold_pairs_set = {(p["source"]["lemma"], p["target"]["lemma"]) for p in gold_ara_eng}
    negatives_raw = [
        p for p in negatives_raw
        if (p["source"]["lemma"], p["target"]["lemma"]) not in gold_pairs_set
    ][:200]
    print(f"Negatives generated: {len(negatives_raw)}")

    print("\nScoring all pairs (this may take a moment)...")
    scorer = PhoneticLawScorer()

    gold_scored = score_pairs(gold_ara_eng, scorer)
    silver_scored = score_pairs(silver_all, scorer)
    neg_scored = score_pairs(negatives_raw, scorer)

    gold_scores = [r["phonetic_law_score"] for r in gold_scored]
    gold_bonuses = [r["phonetic_law_bonus"] for r in gold_scored]
    silver_scores = [r["phonetic_law_score"] for r in silver_scored]
    silver_bonuses = [r["phonetic_law_bonus"] for r in silver_scored]
    neg_scores = [r["phonetic_law_score"] for r in neg_scored]
    neg_bonuses = [r["phonetic_law_bonus"] for r in neg_scored]

    # --- REPORT ---
    print("\n" + "=" * 60)
    print("  PHONETIC LAW SCORER EVALUATION")
    print("=" * 60)

    print(f"\nGold pairs (ara<->eng):  N={len(gold_ara_eng)}")
    print_group_stats("gold", gold_scores, gold_bonuses)

    print(f"\nSilver pairs:            N={len(silver_all)}")
    print_group_stats("silver", silver_scores, silver_bonuses)

    print(f"\nNegative pairs:          N={len(neg_scored)}")
    print_group_stats("negative", neg_scores, neg_bonuses)

    # Separation
    print("\nSeparation:")
    gold_mean = statistics.mean(gold_scores) if gold_scores else 0.0
    neg_mean = statistics.mean(neg_scores) if neg_scores else 0.0
    gold_p40, _ = pct(gold_scores, 0.4)
    neg_p40, _ = pct(neg_scores, 0.4)
    print(f"  Gold mean - Negative mean = {gold_mean - neg_mean:+.4f}")
    print(f"  Gold >0.4 rate - Negative >0.4 rate = {gold_p40 - neg_p40:+.1f}%")

    # Per-confidence breakdown for gold
    from collections import defaultdict
    by_conf: dict[float, list[float]] = defaultdict(list)
    for r in gold_scored:
        conf = r.get("confidence")
        if conf is not None:
            by_conf[float(conf)].append(r["phonetic_law_score"])

    print("\nPer-confidence breakdown (gold ara<->eng):")
    for conf in sorted(by_conf.keys(), reverse=True):
        scores_c = by_conf[conf]
        mean_c = statistics.mean(scores_c)
        print(f"  conf={conf:.2f}: mean={mean_c:.4f} (N={len(scores_c)})")

    # Cross-lingual skeleton score comparison
    gold_skel = [r["skeleton_score"] for r in gold_scored]
    neg_skel = [r["skeleton_score"] for r in neg_scored]
    print("\nCross-lingual skeleton score (correspondence.py):")
    print(f"  Gold ara<->eng:  mean={statistics.mean(gold_skel):.4f}, "
          f"median={statistics.median(gold_skel):.4f}")
    print(f"  Negative pairs:  mean={statistics.mean(neg_skel):.4f}, "
          f"median={statistics.median(neg_skel):.4f}")
    print(f"  Separation:      {statistics.mean(gold_skel) - statistics.mean(neg_skel):+.4f}")

    # Phonetic law bonus distribution
    bonus_vals = [r["phonetic_law_bonus"] for r in gold_scored if r["phonetic_law_bonus"] > 0]
    if bonus_vals:
        print("\nPhonetic law bonus distribution (gold, bonus > 0 only):")
        print(f"  N pairs with bonus:  {len(bonus_vals)}/{len(gold_scored)}")
        print(f"  Mean bonus:          {statistics.mean(bonus_vals):.4f}")
        print(f"  Max bonus:           {max(bonus_vals):.4f}")
        print(f"  Min bonus:           {min(bonus_vals):.4f}")
        tiers = [(0.05, ">0.05"), (0.08, ">0.08"), (0.12, ">0.12"), (0.149, ">0.149")]
        for thresh, label in tiers:
            n = sum(1 for b in bonus_vals if b > thresh)
            print(f"  Bonus {label}:     {n}")

    # Top 10 highest scoring gold pairs
    top10 = sorted(gold_scored, key=lambda r: r["phonetic_law_score"], reverse=True)[:10]
    print("\nTop 10 highest-scoring gold pairs:")
    for i, r in enumerate(top10, 1):
        det = r.get("details", {})
        print(
            f"  {i:2d}. {r['ara']!s:20s} -> {r['eng']!s:20s}  "
            f"score={r['phonetic_law_score']:.4f}  "
            f"proj={det.get('projection_match', 0):.3f}  "
            f"direct={det.get('direct_match', 0):.3f}"
        )

    # Bottom 10 scoring gold pairs (potential misses)
    bottom10 = sorted(gold_scored, key=lambda r: r["phonetic_law_score"])[:10]
    print("\nBottom 10 lowest-scoring gold pairs:")
    for i, r in enumerate(bottom10, 1):
        det = r.get("details", {})
        print(
            f"  {i:2d}. {r['ara']!s:20s} -> {r['eng']!s:20s}  "
            f"score={r['phonetic_law_score']:.4f}  "
            f"ar_skel={det.get('arabic_skeleton', '')!s:10s}  "
            f"eng_skel={det.get('english_skeleton', '')}"
        )

    # Top 5 negative pairs (false positives at risk)
    top5_neg = sorted(neg_scored, key=lambda r: r["phonetic_law_score"], reverse=True)[:5]
    print("\nTop 5 highest-scoring negative pairs (potential false positives):")
    for i, r in enumerate(top5_neg, 1):
        print(
            f"  {i}. {r['ara']!s:20s} -> {r['eng']!s:20s}  "
            f"score={r['phonetic_law_score']:.4f}"
        )

    print("\n" + "=" * 60)
    print("  EVALUATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
