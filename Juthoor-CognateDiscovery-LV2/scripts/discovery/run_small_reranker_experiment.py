from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.append(str(SRC_ROOT))

from juthoor_cognatediscovery_lv2.discovery.benchmarking import (
    compare_metrics,
    evaluate_leads_against_benchmark,
    extract_benchmark_subset,
    filter_available_benchmark_pairs,
    read_jsonl,
    write_jsonl,
)
from juthoor_cognatediscovery_lv2.discovery.evaluation import load_benchmark
from juthoor_cognatediscovery_lv2.discovery.rerank import rerank_leads_file, train_reranker


def parse_spec(value: str) -> tuple[str, str, Path]:
    if "=" not in value:
        raise ValueError(f"Invalid spec {value!r}. Expected <lang>[@<stage>]=<path>.")
    left, right = value.split("=", 1)
    parts = [p for p in left.split("@") if p]
    if not parts:
        raise ValueError(f"Invalid spec {value!r}: missing <lang>.")
    lang = parts[0]
    stage = parts[1] if len(parts) > 1 else "unknown"
    return lang, stage, Path(right)


def _resolve(path: Path) -> Path:
    if path.is_absolute():
        return path
    cwd_candidate = (Path.cwd() / path)
    if cwd_candidate.exists() or cwd_candidate.parent.exists():
        return cwd_candidate.resolve()
    return (REPO_ROOT / path).resolve()


def _run_discovery(args: list[str]) -> Path:
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "discovery" / "run_discovery_retrieval.py"), *args]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8", check=True)
    match = re.search(r"Wrote \d+ leads to:\s*(.+)", proc.stdout)
    if not match:
        raise RuntimeError(f"Could not find output leads path in discovery output.\n{proc.stdout}\n{proc.stderr}")
    return Path(match.group(1).strip())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a small benchmark-aligned LV2 discovery experiment, train a reranker, and compare metrics."
    )
    parser.add_argument("--benchmark", action="append", required=True, help="Benchmark JSONL file (repeatable).")
    parser.add_argument("--source", required=True, help="Source corpus spec: <lang>[@<stage>]=<path>.")
    parser.add_argument("--target", required=True, help="Target corpus spec: <lang>[@<stage>]=<path>.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for subset corpora, models, and reports.")
    parser.add_argument("--models", nargs="+", default=["semantic", "form"], choices=["semantic", "form"])
    parser.add_argument("--topk", type=int, default=25)
    parser.add_argument("--max-out", type=int, default=25)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--backend", choices=["local", "api"], default="local")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--learning-rate", type=float, default=0.5)
    parser.add_argument("--l2", type=float, default=0.01)
    parser.add_argument("--rebuild-cache", action="store_true")
    parser.add_argument("--rebuild-index", action="store_true")
    args = parser.parse_args()

    source_lang, source_stage, source_path = parse_spec(args.source)
    target_lang, target_stage, target_path = parse_spec(args.target)
    output_dir = _resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    benchmark_pairs = []
    for item in args.benchmark:
        benchmark_pairs.extend(load_benchmark(_resolve(Path(item))))

    source_rows = read_jsonl(_resolve(source_path))
    target_rows = read_jsonl(_resolve(target_path))

    source_subset = extract_benchmark_subset(source_rows, benchmark_pairs, lang=source_lang, side="source")
    target_subset = extract_benchmark_subset(target_rows, benchmark_pairs, lang=target_lang, side="target")
    available_pairs = filter_available_benchmark_pairs(
        benchmark_pairs,
        source_rows=source_subset,
        target_rows=target_subset,
    )
    if not available_pairs:
        raise ValueError("No benchmark pairs remain after filtering to the selected source/target corpora.")

    source_subset_path = write_jsonl(output_dir / f"{source_lang}_{source_stage}_benchmark_subset.jsonl", source_subset)
    target_subset_path = write_jsonl(output_dir / f"{target_lang}_{target_stage}_benchmark_subset.jsonl", target_subset)
    filtered_benchmark_path = write_jsonl(
        output_dir / f"benchmark_{source_lang}_{target_lang}_available.jsonl",
        available_pairs,
    )

    pair_id = f"{source_lang}_benchmark_vs_{target_lang}_benchmark"
    discovery_args = [
        "--source",
        f"{source_lang}@{source_stage}={source_subset_path}",
        "--target",
        f"{target_lang}@{target_stage}={target_subset_path}",
        "--models",
        *args.models,
        "--topk",
        str(args.topk),
        "--max-out",
        str(args.max_out),
        "--backend",
        args.backend,
        "--device",
        args.device,
        "--pair-id",
        pair_id,
        "--no-report",
        "--yes",
    ]
    if args.limit:
        discovery_args.extend(["--limit", str(args.limit)])
    if args.rebuild_cache:
        discovery_args.append("--rebuild-cache")
    if args.rebuild_index:
        discovery_args.append("--rebuild-index")

    leads_path = _run_discovery(discovery_args)
    baseline_metrics = evaluate_leads_against_benchmark(leads_path, filtered_benchmark_path, top_k=args.topk)

    reranker_path = output_dir / f"{pair_id}_reranker.json"
    train_reranker(
        [filtered_benchmark_path],
        leads_path,
        reranker_path,
        learning_rate=args.learning_rate,
        epochs=args.epochs,
        l2=args.l2,
    )

    reranked_leads_path = output_dir / f"{leads_path.stem}_reranked.jsonl"
    rerank_leads_file(reranker_path, leads_path, reranked_leads_path)
    reranked_metrics = evaluate_leads_against_benchmark(reranked_leads_path, filtered_benchmark_path, top_k=args.topk)
    comparison = compare_metrics(baseline_metrics, reranked_metrics)

    summary = {
        "source_subset_path": str(source_subset_path),
        "target_subset_path": str(target_subset_path),
        "benchmark_path": str(filtered_benchmark_path),
        "leads_path": str(leads_path),
        "reranker_path": str(reranker_path),
        "reranked_leads_path": str(reranked_leads_path),
        "comparison": comparison,
    }
    summary_path = output_dir / f"{pair_id}_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Summary written to: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
