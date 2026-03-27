"""Calibrate a MultiMethodScorer threshold against gold and negative benchmarks."""
from __future__ import annotations

import argparse
import io
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent
LV2_ROOT = SCRIPT_DIR.parent.parent
SRC_ROOT = LV2_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScorer

NEGATIVE_PATH = LV2_ROOT / "resources" / "benchmarks" / "non_cognate_negatives.jsonl"
GOLD_PATH = LV2_ROOT / "resources" / "benchmarks" / "cognate_gold.jsonl"


@dataclass(frozen=True)
class ScoredPair:
    label: str
    score: float
    source_lang: str
    source_lemma: str
    target_lang: str
    target_lemma: str
    best_method: str


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sample_gold(rows: list[dict[str, Any]], sample_size: int, seed: int) -> list[dict[str, Any]]:
    if sample_size >= len(rows):
        return rows[:]
    rng = random.Random(seed)
    return rng.sample(rows, sample_size)


def score_rows(
    rows: list[dict[str, Any]],
    label: str,
    scorer: MultiMethodScorer,
) -> list[ScoredPair]:
    scored: list[ScoredPair] = []
    for row in rows:
        source = row.get("source", {})
        target = row.get("target", {})
        result = scorer.score_pair(source, target)
        scored.append(
            ScoredPair(
                label=label,
                score=result.best_score,
                source_lang=str(source.get("lang", "")),
                source_lemma=str(source.get("lemma", "")),
                target_lang=str(target.get("lang", "")),
                target_lemma=str(target.get("lemma", "")),
                best_method=result.best_method,
            )
        )
    return scored


def print_scores(title: str, scored_pairs: list[ScoredPair]) -> None:
    print(title)
    for pair in scored_pairs:
        method = pair.best_method or "-"
        print(
            f"  {pair.score:0.6f}  "
            f"{pair.source_lang}:{pair.source_lemma} -> {pair.target_lang}:{pair.target_lemma}  "
            f"[{method}]"
        )
    print()


def summarize(scores: list[float]) -> str:
    if not scores:
        return "n=0"
    ordered = sorted(scores)
    mid = len(ordered) // 2
    if len(ordered) % 2 == 0:
        median = (ordered[mid - 1] + ordered[mid]) / 2
    else:
        median = ordered[mid]
    mean = sum(ordered) / len(ordered)
    return (
        f"n={len(ordered)} min={ordered[0]:0.6f} max={ordered[-1]:0.6f} "
        f"mean={mean:0.6f} median={median:0.6f}"
    )


def threshold_candidates(gold_scores: list[float], negative_scores: list[float]) -> list[float]:
    values = sorted(set(gold_scores + negative_scores))
    candidates = {0.0, 1.0}
    candidates.update(values)
    for left, right in zip(values, values[1:]):
        candidates.add(round((left + right) / 2.0, 6))
    return sorted(candidates)


def choose_threshold(gold_scores: list[float], negative_scores: list[float]) -> tuple[float, dict[str, float]]:
    best_threshold = 0.0
    best_metrics = {
        "youden_j": float("-inf"),
        "balanced_accuracy": 0.0,
        "f1": 0.0,
        "recall": 0.0,
        "specificity": 0.0,
        "precision": 0.0,
        "false_positive_rate": 0.0,
    }
    for threshold in threshold_candidates(gold_scores, negative_scores):
        tp = sum(score >= threshold for score in gold_scores)
        fn = len(gold_scores) - tp
        fp = sum(score >= threshold for score in negative_scores)
        tn = len(negative_scores) - fp
        recall = tp / len(gold_scores) if gold_scores else 0.0
        specificity = tn / len(negative_scores) if negative_scores else 0.0
        false_positive_rate = fp / len(negative_scores) if negative_scores else 0.0
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        balanced_accuracy = (recall + specificity) / 2.0
        youden_j = recall - false_positive_rate
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        metrics = {
            "youden_j": youden_j,
            "balanced_accuracy": balanced_accuracy,
            "f1": f1,
            "recall": recall,
            "specificity": specificity,
            "precision": precision,
            "false_positive_rate": false_positive_rate,
        }
        current_key = (
            metrics["youden_j"],
            metrics["balanced_accuracy"],
            metrics["f1"],
            -threshold,
        )
        best_key = (
            best_metrics["youden_j"],
            best_metrics["balanced_accuracy"],
            best_metrics["f1"],
            -best_threshold,
        )
        if current_key > best_key:
            best_threshold = threshold
            best_metrics = metrics
    return best_threshold, best_metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-size", type=int, default=100, help="Gold pair sample size")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for gold sampling")
    args = parser.parse_args()

    negatives = load_jsonl(NEGATIVE_PATH)
    gold_all = load_jsonl(GOLD_PATH)
    gold_sample = sample_gold(gold_all, args.sample_size, args.seed)

    print(f"Loaded negatives: {len(negatives)} from {NEGATIVE_PATH}")
    print(f"Loaded gold pairs: {len(gold_all)} from {GOLD_PATH}")
    print(f"Using gold sample: {len(gold_sample)} (seed={args.seed})")
    print()

    scorer = MultiMethodScorer()

    negative_scored = score_rows(negatives, "negative", scorer)
    gold_scored = score_rows(gold_sample, "gold", scorer)

    print_scores("Negative pair scores:", negative_scored)
    print_scores("Gold pair scores:", gold_scored)

    negative_scores = [pair.score for pair in negative_scored]
    gold_scores = [pair.score for pair in gold_scored]

    print(f"Negative summary: {summarize(negative_scores)}")
    print(f"Gold summary: {summarize(gold_scores)}")
    print()

    threshold, metrics = choose_threshold(gold_scores, negative_scores)
    print(
        "Recommended threshold metrics: "
        f"recall={metrics['recall']:.4f} "
        f"specificity={metrics['specificity']:.4f} "
        f"precision={metrics['precision']:.4f} "
        f"fpr={metrics['false_positive_rate']:.4f} "
        f"f1={metrics['f1']:.4f} "
        f"youden_j={metrics['youden_j']:.4f}"
    )
    print(f"RECOMMENDED_THRESHOLD={threshold:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
