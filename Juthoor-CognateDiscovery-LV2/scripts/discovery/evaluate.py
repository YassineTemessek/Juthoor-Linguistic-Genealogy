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
from juthoor_cognatediscovery_lv2.discovery.benchmarking import compare_lead_runs

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def evaluate(
    benchmark_paths: list[Path],
    leads_path: Path,
    *,
    top_k: int,
    relations: set[str] | None = None,
) -> tuple[int, dict]:
    benchmark = []
    for benchmark_path in benchmark_paths:
        benchmark.extend(load_benchmark(benchmark_path, relations=relations))
    leads_by_source = load_leads(leads_path)
    results, metrics = evaluate_pairs(benchmark, leads_by_source, top_k=top_k)

    label = ", ".join(path.name for path in benchmark_paths)
    print(f"Evaluating {leads_path.name} against {label} (Top-{top_k})")
    print("-" * 60)
    for result in results:
        src = f"{result.pair.source_lang}:{result.pair.source_lemma}"
        tgt = f"{result.pair.target_lang}:{result.pair.target_lemma}"
        status = f"HIT (Rank {result.found_rank})" if result.hit else "MISS"
        print(f"{src} -> {tgt}: {status} [{result.pair.relation}]")
    print("-" * 60)
    print(format_summary(metrics, top_k=top_k))
    return 0, metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("leads", type=Path, help="Path to discovery leads JSONL.")
    parser.add_argument("--benchmark", action="append", type=Path, default=[])
    parser.add_argument("--top-k", type=int, default=100)
    parser.add_argument("--compare-to", type=Path, default=None, help="Optional baseline leads JSONL to compare against.")
    parser.add_argument("--json-out", type=Path, default=None, help="Optional path to write metrics/comparison JSON.")
    parser.add_argument(
        "--relation",
        action="append",
        default=[],
        help="Limit evaluation to specific relations (repeatable).",
    )
    args = parser.parse_args()

    benchmark_paths = args.benchmark or [Path("resources/benchmarks/cognate_gold.jsonl")]
    relations = set(args.relation) if args.relation else None
    if args.compare_to:
        comparison = compare_lead_runs(args.compare_to, args.leads, benchmark_paths, top_k=args.top_k)
        import json
        print(json.dumps(comparison, ensure_ascii=False, indent=2))
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
        raise SystemExit(0)

    rc, metrics = evaluate(benchmark_paths, args.leads, top_k=args.top_k, relations=relations)
    if args.json_out:
        import json
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(rc)

if __name__ == "__main__":
    main()
