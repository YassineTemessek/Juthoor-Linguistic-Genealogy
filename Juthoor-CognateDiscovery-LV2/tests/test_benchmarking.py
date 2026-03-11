from __future__ import annotations

import json
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.benchmarking import (
    compare_metrics,
    extract_benchmark_subset,
    filter_available_benchmark_pairs,
    write_jsonl,
)
from juthoor_cognatediscovery_lv2.discovery.evaluation import BenchmarkPair


def test_extract_benchmark_subset_matches_requested_side():
    pairs = [
        BenchmarkPair("ara", "بيت", "eng", "booth", "cognate"),
        BenchmarkPair("ara", "كلب", "eng", "dog", "negative_translation"),
    ]
    corpus_rows = [
        {"lang": "ara", "lemma": "بيت", "lexeme_id": "ara1"},
        {"lang": "ara", "lemma": "كلب", "lexeme_id": "ara2"},
        {"lang": "ara", "lemma": "شمس", "lexeme_id": "ara3"},
    ]

    subset = extract_benchmark_subset(corpus_rows, pairs, lang="ara", side="source")
    assert [row["lemma"] for row in subset] == ["بيت", "كلب"]


def test_filter_available_benchmark_pairs_only_keeps_present_rows():
    pairs = [
        BenchmarkPair("ara", "بيت", "eng", "booth", "cognate"),
        BenchmarkPair("ara", "كلب", "eng", "dog", "negative_translation"),
    ]
    available = filter_available_benchmark_pairs(
        pairs,
        source_rows=[{"lang": "ara", "lemma": "بيت"}],
        target_rows=[{"lang": "eng", "lemma": "booth"}],
    )
    assert len(available) == 1
    assert available[0]["source"]["lemma"] == "بيت"


def test_compare_metrics_reports_deltas():
    comparison = compare_metrics(
        {"recall": 1.0, "mrr": 0.5, "ndcg": 0.6},
        {"recall": 1.0, "mrr": 0.7, "ndcg": 0.65},
    )
    assert comparison["delta"]["mrr"] == 0.2
    assert comparison["delta"]["ndcg"] == 0.05
    assert comparison["improved"] is True


def test_write_jsonl_round_trips(tmp_path: Path):
    path = tmp_path / "rows.jsonl"
    write_jsonl(path, [{"lemma": "بيت"}, {"lemma": "كلب"}])
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows[1]["lemma"] == "كلب"
