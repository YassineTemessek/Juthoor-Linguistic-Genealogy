from __future__ import annotations

import json
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.evaluation import (
    BenchmarkPair,
    build_metrics,
    evaluate_pairs,
    find_rank,
    format_summary,
    load_benchmark,
    load_leads,
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
    metrics = build_metrics(
        [
            type("R", (), {"hit": True, "reciprocal_rank": 1.0, "ndcg": 1.0, "weighted_reciprocal_rank": 1.0, "weighted_ndcg": 1.0, "pair": type("P", (), {"relation": "cognate", "confidence": 1.0})()})(),
            type("R", (), {"hit": False, "reciprocal_rank": 0.0, "ndcg": 0.0, "weighted_reciprocal_rank": 0.0, "weighted_ndcg": 0.0, "pair": type("P", (), {"relation": "borrowing", "confidence": 1.0})()})(),
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
