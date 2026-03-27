"""Tune PhoneticLawScorer threshold to minimize false positives while preserving recall.

Generates 300 random negatives from gold ara<->eng pairs, scores all pairs,
then computes precision/recall/F1 across a range of thresholds.
"""
from __future__ import annotations

import io
import json
import random
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent
LV2_ROOT = SCRIPT_DIR.parent
SRC_ROOT = LV2_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import PhoneticLawScorer

GOLD_PATH = LV2_ROOT / "resources" / "benchmarks" / "cognate_gold.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    # 1. Load gold ara<->eng pairs
    gold_all = load_jsonl(GOLD_PATH)
    gold = [
        p for p in gold_all
        if p.get("source", {}).get("lang") == "ara"
        and p.get("target", {}).get("lang") == "eng"
    ]
    print(f"Gold ara<->eng pairs: {len(gold)}")

    # 2. Generate 300 random negatives
    rng = random.Random(42)
    arabic_lemmas = [p["source"]["lemma"] for p in gold]
    english_lemmas = [p["target"]["lemma"] for p in gold]
    gold_pairs_set = {(p["source"]["lemma"], p["target"]["lemma"]) for p in gold}

    negatives: list[dict] = []
    attempts = 0
    shuffled_eng = english_lemmas[:]
    while len(negatives) < 300 and attempts < 10000:
        rng.shuffle(shuffled_eng)
        for i, ara in enumerate(arabic_lemmas):
            eng = shuffled_eng[i % len(shuffled_eng)]
            if (ara, eng) not in gold_pairs_set:
                negatives.append({
                    "source": {"lang": "ara", "lemma": ara},
                    "target": {"lang": "eng", "lemma": eng},
                })
            if len(negatives) >= 300:
                break
        attempts += 1

    print(f"Negatives generated: {len(negatives)}")

    # 3. Score all pairs
    scorer = PhoneticLawScorer()
    print("Scoring gold pairs...")
    gold_scores: list[float] = []
    for p in gold:
        res = scorer.score_pair(p["source"], p["target"])
        gold_scores.append(res["phonetic_law_score"])

    print("Scoring negative pairs...")
    neg_scores: list[float] = []
    for p in negatives:
        res = scorer.score_pair(p["source"], p["target"])
        neg_scores.append(res["phonetic_law_score"])

    # 4. Threshold sweep
    thresholds = [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]

    print("\n" + "=" * 72)
    print(f"{'Threshold':>10} {'Recall%':>10} {'FP_Rate%':>10} {'Precision%':>12} {'F1':>8}")
    print("=" * 72)

    best_f1 = -1.0
    best_thresh = thresholds[0]

    for t in thresholds:
        gold_above = sum(1 for s in gold_scores if s > t)
        neg_above = sum(1 for s in neg_scores if s > t)
        recall = gold_above / len(gold_scores) if gold_scores else 0.0
        fpr = neg_above / len(neg_scores) if neg_scores else 0.0
        precision = gold_above / (gold_above + neg_above) if (gold_above + neg_above) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        marker = " <-- best" if f1 > best_f1 else ""
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = t

        print(
            f"{t:>10.2f} {recall*100:>10.1f} {fpr*100:>10.1f} {precision*100:>12.1f} {f1:>8.4f}{marker}"
        )

    print("=" * 72)
    print(f"\nOPTIMAL THRESHOLD: {best_thresh:.2f}  (F1={best_f1:.4f})")

    # Show current false positive rate at 0.40 for context
    neg_above_040 = sum(1 for s in neg_scores if s > 0.40)
    print(f"\nCurrent state (threshold=0.40): {neg_above_040/len(neg_scores)*100:.1f}% of negatives above threshold")
    print(f"Target: <40% of negatives above optimal threshold")


if __name__ == "__main__":
    main()
