from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LV2_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = LV2_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.append(str(SRC_ROOT))

from juthoor_cognatediscovery_lv2.discovery.evaluation import load_benchmark
from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScorer


def _round(value: float) -> float:
    return round(float(value), 6)


def _pair_payload(record: Any) -> dict[str, Any]:
    return {
        "lang": record.source_lang,
        "lemma": record.source_lemma,
        "gloss": record.source_gloss,
    }


def _target_payload(record: Any) -> dict[str, Any]:
    return {
        "lang": record.target_lang,
        "lemma": record.target_lemma,
        "gloss": record.target_gloss,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze which MultiMethodScorer methods find gold benchmark pairs.")
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=LV2_ROOT / "resources" / "benchmarks" / "cognate_gold.jsonl",
        help="Path to cognate_gold.jsonl",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=100,
        help="Number of random gold pairs to score.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible sampling.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=LV2_ROOT / "outputs" / "benchmark_method_analysis.json",
        help="Where to save the analysis JSON.",
    )
    args = parser.parse_args()

    benchmark_rows = load_benchmark(args.benchmark, relations={"cognate"})
    if not benchmark_rows:
        raise ValueError(f"No cognate benchmark rows found in {args.benchmark}")
    if args.sample_size <= 0:
        raise ValueError("--sample-size must be positive")
    if args.sample_size > len(benchmark_rows):
        raise ValueError(
            f"--sample-size ({args.sample_size}) exceeds benchmark size ({len(benchmark_rows)})"
        )

    scorer = MultiMethodScorer()
    sampled_rows = random.Random(args.seed).sample(benchmark_rows, args.sample_size)

    method_pair_scores: dict[str, list[float]] = defaultdict(list)
    method_best_counts: Counter[str] = Counter()
    language_pair_counts: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "pairs": 0,
            "pairs_with_any_method": 0,
            "best_scores": [],
            "fired_method_counts": [],
            "best_methods": Counter(),
        }
    )
    pair_records: list[dict[str, Any]] = []

    for pair in sampled_rows:
        score = scorer.score_pair(
            {
                "lang": pair.source_lang,
                "lemma": pair.source_lemma,
                "gloss": pair.source_gloss,
                "root_norm": pair.source_lemma,
            },
            {
                "lang": pair.target_lang,
                "lemma": pair.target_lemma,
                "gloss": pair.target_gloss,
            },
        )

        per_method_best: dict[str, float] = {}
        for result in score.all_results:
            current = per_method_best.get(result.method_name, 0.0)
            if result.score > current:
                per_method_best[result.method_name] = result.score

        for method_name, method_score in per_method_best.items():
            method_pair_scores[method_name].append(method_score)

        if score.best_method:
            method_best_counts[score.best_method] += 1

        language_pair_key = f"{pair.source_lang}-{pair.target_lang}"
        lang_bucket = language_pair_counts[language_pair_key]
        lang_bucket["pairs"] += 1
        lang_bucket["best_scores"].append(score.best_score)
        lang_bucket["fired_method_counts"].append(len(score.methods_that_fired))
        if score.methods_that_fired:
            lang_bucket["pairs_with_any_method"] += 1
        if score.best_method:
            lang_bucket["best_methods"][score.best_method] += 1

        pair_records.append(
            {
                "source": _pair_payload(pair),
                "target": _target_payload(pair),
                "relation": pair.relation,
                "confidence": pair.confidence,
                "notes": pair.notes,
                "best_score": score.best_score,
                "best_method": score.best_method,
                "methods_that_fired": score.methods_that_fired,
                "method_scores": {
                    method_name: _round(method_score)
                    for method_name, method_score in sorted(per_method_best.items())
                },
                "raw_result_count": len(score.all_results),
            }
        )

    method_stats = {
        method_name: {
            "gold_pairs_found": len(scores),
            "average_score": _round(sum(scores) / len(scores)) if scores else 0.0,
            "best_method_count": method_best_counts.get(method_name, 0),
        }
        for method_name, scores in sorted(method_pair_scores.items())
    }

    language_pair_stats = {}
    for pair_name, bucket in sorted(language_pair_counts.items()):
        total_pairs = int(bucket["pairs"])
        best_scores = bucket["best_scores"]
        fired_counts = bucket["fired_method_counts"]
        language_pair_stats[pair_name] = {
            "sampled_pairs": total_pairs,
            "pairs_with_any_method": int(bucket["pairs_with_any_method"]),
            "coverage": _round(bucket["pairs_with_any_method"] / total_pairs) if total_pairs else 0.0,
            "average_best_score": _round(sum(best_scores) / len(best_scores)) if best_scores else 0.0,
            "average_methods_that_fired": _round(sum(fired_counts) / len(fired_counts)) if fired_counts else 0.0,
            "best_method_distribution": dict(sorted(bucket["best_methods"].items())),
        }

    payload = {
        "benchmark_path": str(args.benchmark),
        "output_path": str(args.output),
        "total_gold_pairs_loaded": len(benchmark_rows),
        "sample_size": args.sample_size,
        "seed": args.seed,
        "method_stats": method_stats,
        "language_pair_stats": language_pair_stats,
        "pairs": pair_records,
    }

    print(f"Loaded gold benchmark: {len(benchmark_rows)} pairs")
    print(f"Scored sample: {args.sample_size} gold pairs (seed={args.seed})")
    print("")
    print("Per-method stats")
    for method_name, stats in method_stats.items():
        print(
            f"  {method_name}: "
            f"found={stats['gold_pairs_found']}, "
            f"avg_score={stats['average_score']:.3f}, "
            f"best_method={stats['best_method_count']}"
        )

    print("")
    print("Per-language-pair stats")
    for pair_name, stats in language_pair_stats.items():
        print(
            f"  {pair_name}: "
            f"sampled={stats['sampled_pairs']}, "
            f"covered={stats['pairs_with_any_method']}, "
            f"coverage={stats['coverage']:.3f}, "
            f"avg_best_score={stats['average_best_score']:.3f}"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("")
    print(f"Saved analysis to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
