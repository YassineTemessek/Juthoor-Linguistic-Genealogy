from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.append(str(SRC_ROOT))

from juthoor_cognatediscovery_lv2.discovery.benchmarking import (
    apply_gloss_overrides,
    extract_benchmark_subset,
    filter_available_benchmark_pairs,
    load_gloss_overrides,
    load_combined_benchmark,
    read_jsonl,
    write_jsonl,
)
from juthoor_cognatediscovery_lv2.discovery.corpora import CorpusSpec
from juthoor_cognatediscovery_lv2.discovery.retrieval import resolve_corpus_path


def parse_spec(value: str) -> CorpusSpec:
    left, right = value.split("=", 1)
    parts = [part for part in left.split("@") if part]
    return CorpusSpec(lang=parts[0], stage=parts[1] if len(parts) > 1 else "unknown", path=Path(right))


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize source/target benchmark slices and the filtered benchmark JSONL.")
    parser.add_argument("--benchmark", action="append", required=True, help="Benchmark JSONL path (repeatable).")
    parser.add_argument("--source", required=True, help="Source corpus spec: <lang>[@<stage>]=<path>.")
    parser.add_argument("--target", required=True, help="Target corpus spec: <lang>[@<stage>]=<path>.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--gloss-overrides",
        type=Path,
        default=REPO_ROOT / "resources" / "benchmarks" / "arabic_gloss_overrides.json",
        help="Optional JSON file mapping lang:lemma -> preferred short_gloss for benchmark slices.",
    )
    args = parser.parse_args()

    source_spec = parse_spec(args.source)
    target_spec = parse_spec(args.target)
    output_dir = args.output_dir if args.output_dir.is_absolute() else (Path.cwd() / args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    benchmark = load_combined_benchmark([Path(item) for item in args.benchmark])
    gloss_overrides = load_gloss_overrides(args.gloss_overrides)
    source_rows = read_jsonl(resolve_corpus_path(source_spec, REPO_ROOT))
    target_rows = read_jsonl(resolve_corpus_path(target_spec, REPO_ROOT))

    source_subset = extract_benchmark_subset(
        source_rows,
        benchmark,
        lang=source_spec.lang,
        side="source",
        gloss_overrides=gloss_overrides,
    )
    target_subset = extract_benchmark_subset(
        target_rows,
        benchmark,
        lang=target_spec.lang,
        side="target",
        gloss_overrides=gloss_overrides,
    )
    filtered = filter_available_benchmark_pairs(
        benchmark,
        source_rows=source_subset,
        target_rows=target_subset,
    )

    source_out = write_jsonl(output_dir / f"{source_spec.lang}_{source_spec.stage}_benchmark_subset.jsonl", source_subset)
    target_out = write_jsonl(output_dir / f"{target_spec.lang}_{target_spec.stage}_benchmark_subset.jsonl", target_subset)
    benchmark_out = write_jsonl(output_dir / f"benchmark_{source_spec.lang}_{target_spec.lang}_available.jsonl", filtered)
    summary = {
        "source_subset_path": str(source_out),
        "target_subset_path": str(target_out),
        "benchmark_path": str(benchmark_out),
        "source_rows": len(source_subset),
        "target_rows": len(target_subset),
        "available_pairs": len(filtered),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
