"""Evaluation CLI for LV2 discovery benchmarks."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from juthoor_cognatediscovery_lv2.discovery.evaluation import (
    evaluate_pairs,
    format_summary,
    load_benchmark,
    load_leads,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def evaluate(benchmark_path: Path, leads_path: Path, *, top_k: int, relations: set[str] | None = None) -> int:
    benchmark = load_benchmark(benchmark_path, relations=relations)
    leads_by_source = load_leads(leads_path)
    results, metrics = evaluate_pairs(benchmark, leads_by_source, top_k=top_k)

    print(f"Evaluating {leads_path.name} against {benchmark_path.name} (Top-{top_k})")
    print("-" * 60)
    for result in results:
        src = f"{result.pair.source_lang}:{result.pair.source_lemma}"
        tgt = f"{result.pair.target_lang}:{result.pair.target_lemma}"
        status = f"HIT (Rank {result.found_rank})" if result.hit else "MISS"
        print(f"{src} -> {tgt}: {status} [{result.pair.relation}]")
    print("-" * 60)
    print(format_summary(metrics, top_k=top_k))
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("leads", type=Path, help="Path to discovery leads JSONL.")
    parser.add_argument("--benchmark", type=Path, default=Path("resources/benchmarks/cognate_gold.jsonl"))
    parser.add_argument("--top-k", type=int, default=100)
    parser.add_argument(
        "--relation",
        action="append",
        default=[],
        help="Limit evaluation to specific relations (repeatable).",
    )
    args = parser.parse_args()

    relations = set(args.relation) if args.relation else None
    raise SystemExit(evaluate(args.benchmark, args.leads, top_k=args.top_k, relations=relations))

if __name__ == "__main__":
    main()
