from __future__ import annotations

import json
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.evaluation import (
    BenchmarkPair,
    MatchResult,
    build_metrics,
    evaluate_pairs,
    find_rank,
    format_summary,
    load_benchmark,
    load_leads,
    recall_at_k,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def test_load_benchmark_filters_relations(tmp_path: Path):
    path = tmp_path / "benchmark.jsonl"
    _write_jsonl(
        path,
        [
            {"source": {"lang": "ara", "lemma": "عين"}, "target": {"lang": "heb", "lemma": "עין"}, "relation": "cognate"},
            {"source": {"lang": "ara", "lemma": "سكر"}, "target": {"lang": "eng", "lemma": "sugar"}, "relation": "borrowing"},
        ],
    )
    rows = load_benchmark(path, relations={"cognate"})
    assert len(rows) == 1
    assert rows[0].relation == "cognate"


def test_find_rank_matches_lang_and_lemma():
    pair = BenchmarkPair("ara", "عين", "heb", "עין", "cognate")
    leads = {
        ("ara", "عين"): [
            {"target": {"lang": "eng", "lemma": "eye"}},
            {"target": {"lang": "heb", "lemma": "עין"}},
        ]
    }
    assert find_rank(pair, leads, top_k=5) == 2


def test_evaluate_pairs_computes_metrics():
    benchmark = [
        BenchmarkPair("ara", "عين", "heb", "עין", "cognate"),
        BenchmarkPair("ara", "سكر", "eng", "sugar", "borrowing"),
    ]
    leads = {
        ("ara", "عين"): [{"target": {"lang": "heb", "lemma": "עין"}}],
        ("ara", "سكر"): [{"target": {"lang": "eng", "lemma": "sweet"}}],
    }
    results, metrics = evaluate_pairs(benchmark, leads, top_k=10)
    assert len(results) == 2
    assert metrics["hits"] == 1
    assert metrics["recall"] == 0.5
    assert "cognate" in metrics["by_relation"]
    assert metrics["by_relation"]["cognate"]["recall"] == 1.0
    assert metrics["by_relation"]["borrowing"]["recall"] == 0.0
    assert "weighted_mrr" in metrics
    assert "weighted_ndcg" in metrics


def test_format_summary_includes_core_metrics():
    hit_pair = BenchmarkPair("ara", "عين", "heb", "עין", "cognate", confidence=1.0)
    miss_pair = BenchmarkPair("ara", "سكر", "eng", "sugar", "borrowing", confidence=1.0)
    metrics = build_metrics(
        [
            MatchResult(pair=hit_pair, found_rank=1, top_k=20),
            MatchResult(pair=miss_pair, found_rank=None, top_k=20),
        ]
    )
    summary = format_summary(metrics, top_k=20)
    assert "Recall@20" in summary
    assert "MRR" in summary
    assert "nDCG" in summary
    assert "wMRR" in summary
    assert "wnDCG" in summary
    assert "cognate" in summary


def test_load_leads_groups_by_source_key(tmp_path: Path):
    path = tmp_path / "leads.jsonl"
    _write_jsonl(
        path,
        [
            {"source": {"lang": "ara", "lemma": "عين"}, "target": {"lang": "heb", "lemma": "עין"}},
            {"source": {"lang": "ara", "lemma": "عين"}, "target": {"lang": "eng", "lemma": "eye"}},
        ],
    )
    grouped = load_leads(path)
    assert ("ara", "عين") in grouped
    assert len(grouped[("ara", "عين")]) == 2


def test_recall_at_10():
    # Gold pair found at rank 5 — inside @10 but outside @1
    pair = BenchmarkPair("ara", "عين", "heb", "עין", "cognate")
    # found_rank=5, top_k=100 (large enough so .hit is True but we test recall_at_k directly)
    result = MatchResult(pair=pair, found_rank=5, top_k=100)
    assert recall_at_k([result], k=10) == 1.0
    assert recall_at_k([result], k=1) == 0.0


def test_recall_at_100():
    # Gold pair found at rank 75 — inside @100 but outside @50
    pair = BenchmarkPair("ara", "عين", "heb", "עין", "cognate")
    result = MatchResult(pair=pair, found_rank=75, top_k=100)
    assert recall_at_k([result], k=100) == 1.0
    assert recall_at_k([result], k=50) == 0.0


def test_build_metrics_includes_recall_at_k_keys():
    benchmark = [
        BenchmarkPair("ara", "عين", "heb", "עין", "cognate"),
        BenchmarkPair("ara", "سكر", "eng", "sugar", "borrowing"),
    ]
    leads = {
        ("ara", "عين"): [{"target": {"lang": "heb", "lemma": "עין"}}],
        ("ara", "سكر"): [{"target": {"lang": "eng", "lemma": "sweet"}}],
    }
    _, metrics = evaluate_pairs(benchmark, leads, top_k=100)
    assert "recall@10" in metrics
    assert "recall@50" in metrics
    assert "recall@100" in metrics
    # The hit is at rank 1, so all three recall values should be 0.5 (1 of 2 found)
    assert metrics["recall@10"] == 0.5
    assert metrics["recall@50"] == 0.5
    assert metrics["recall@100"] == 0.5


def test_weighted_metrics_follow_confidence():
    benchmark = [
        BenchmarkPair("ara", "عين", "heb", "עין", "cognate", confidence=1.0),
        BenchmarkPair("ara", "سكر", "eng", "sugar", "borrowing", confidence=0.2),
    ]
    leads = {
        ("ara", "عين"): [{"target": {"lang": "heb", "lemma": "עין"}}],
        ("ara", "سكر"): [{"target": {"lang": "eng", "lemma": "sweet"}}],
    }
    _, metrics = evaluate_pairs(benchmark, leads, top_k=10)
    assert metrics["weighted_mrr"] > metrics["mrr"]
