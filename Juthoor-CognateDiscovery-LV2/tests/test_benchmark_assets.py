from __future__ import annotations

from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.evaluation import load_benchmark


BENCHMARK_DIR = Path(__file__).resolve().parents[1] / "resources" / "benchmarks"


def test_cognate_gold_contains_only_cognates():
    rows = load_benchmark(BENCHMARK_DIR / "cognate_gold.jsonl")
    assert rows
    assert {row.relation for row in rows} == {"cognate"}


def test_benchmark_assets_are_nonempty():
    for name in ["cognate_gold.jsonl", "cognate_silver.jsonl", "non_cognate_negatives.jsonl"]:
        rows = load_benchmark(BENCHMARK_DIR / name)
        assert rows, f"{name} should not be empty"
