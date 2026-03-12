from __future__ import annotations

import json
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.rerank import (
    DiscoveryReranker,
    build_training_examples,
    train_reranker,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def test_build_training_examples_matches_benchmark_rows(tmp_path: Path):
    benchmark = tmp_path / "benchmark.jsonl"
    leads = tmp_path / "leads.jsonl"
    _write_jsonl(
        benchmark,
        [
            {"source": {"lang": "ara", "lemma": "عين"}, "target": {"lang": "heb", "lemma": "עין"}, "relation": "cognate"},
            {"source": {"lang": "ara", "lemma": "سكر"}, "target": {"lang": "eng", "lemma": "sugar"}, "relation": "borrowing"},
        ],
    )
    _write_jsonl(
        leads,
        [
            {
                "source": {"lang": "ara", "lemma": "عين"},
                "target": {"lang": "heb", "lemma": "עין"},
                "scores": {"semantic": 0.8, "form": 0.7},
                "hybrid": {"components": {"orthography": 0.6, "sound": 0.5, "skeleton": 0.6, "root_match": 1.0, "correspondence": 0.8, "weak_radical_match": 0.0, "hamza_match": 0.0}, "family_boost_applied": True},
            },
            {
                "source": {"lang": "ara", "lemma": "سكر"},
                "target": {"lang": "eng", "lemma": "sugar"},
                "scores": {"semantic": 0.9, "form": 0.8},
                "hybrid": {"components": {"orthography": 0.9, "sound": 0.7, "skeleton": 0.2, "root_match": 0.0, "correspondence": 0.1, "weak_radical_match": 0.0, "hamza_match": 0.0}, "family_boost_applied": False},
            },
        ],
    )

    rows = build_training_examples([benchmark], leads)
    assert len(rows) == 2
    assert rows[0].label == 1.0
    assert rows[1].label == 0.0


def test_train_reranker_writes_model_and_predicts_probability(tmp_path: Path):
    benchmark = tmp_path / "benchmark.jsonl"
    leads = tmp_path / "leads.jsonl"
    model_path = tmp_path / "reranker.json"
    _write_jsonl(
        benchmark,
        [
            {"source": {"lang": "ara", "lemma": "عين"}, "target": {"lang": "heb", "lemma": "עין"}, "relation": "cognate"},
            {"source": {"lang": "ara", "lemma": "سكر"}, "target": {"lang": "eng", "lemma": "sugar"}, "relation": "borrowing"},
        ],
    )
    _write_jsonl(
        leads,
        [
            {
                "source": {"lang": "ara", "lemma": "عين"},
                "target": {"lang": "heb", "lemma": "עין"},
                "scores": {"semantic": 0.7, "form": 0.8},
                "hybrid": {"components": {"orthography": 0.6, "sound": 0.7, "skeleton": 0.8, "root_match": 1.0, "correspondence": 0.9, "weak_radical_match": 0.0, "hamza_match": 0.0}, "family_boost_applied": True},
            },
            {
                "source": {"lang": "ara", "lemma": "سكر"},
                "target": {"lang": "eng", "lemma": "sugar"},
                "scores": {"semantic": 0.95, "form": 0.8},
                "hybrid": {"components": {"orthography": 0.9, "sound": 0.8, "skeleton": 0.1, "root_match": 0.0, "correspondence": 0.1, "weak_radical_match": 0.0, "hamza_match": 0.0}, "family_boost_applied": False},
            },
        ],
    )

    model = train_reranker([benchmark], leads, model_path, epochs=50)
    assert model_path.exists()
    assert model.model_type == "logistic_regression"

    loaded = DiscoveryReranker(model_path)
    score = loaded.predict_one(
        {
            "scores": {"semantic": 0.7, "form": 0.8},
            "hybrid": {"components": {"orthography": 0.6, "sound": 0.7, "skeleton": 0.8, "root_match": 1.0, "correspondence": 0.9, "weak_radical_match": 0.0, "hamza_match": 0.0}, "family_boost_applied": True},
        }
    )
    assert 0.0 <= score <= 1.0


def test_train_reranker_can_mine_implicit_negatives_from_positive_only_benchmark(tmp_path: Path):
    benchmark = tmp_path / "benchmark.jsonl"
    leads = tmp_path / "leads.jsonl"
    model_path = tmp_path / "reranker.json"
    _write_jsonl(
        benchmark,
        [
            {"source": {"lang": "lat", "lemma": "mater"}, "target": {"lang": "grc", "lemma": "μήτηρ"}, "relation": "cognate"},
        ],
    )
    _write_jsonl(
        leads,
        [
            {
                "source": {"lang": "lat", "lemma": "mater"},
                "target": {"lang": "grc", "lemma": "μήτηρ"},
                "scores": {"semantic": 0.9, "form": 0.9},
                "hybrid": {"components": {"orthography": 0.8, "sound": 0.7, "skeleton": 0.9, "root_match": 0.0, "correspondence": 0.9, "weak_radical_match": 0.0, "hamza_match": 0.0}, "family_boost_applied": True},
            },
            {
                "source": {"lang": "lat", "lemma": "mater"},
                "target": {"lang": "grc", "lemma": "πατήρ"},
                "scores": {"semantic": 0.5, "form": 0.4},
                "hybrid": {"components": {"orthography": 0.2, "sound": 0.2, "skeleton": 0.1, "root_match": 0.0, "correspondence": 0.2, "weak_radical_match": 0.0, "hamza_match": 0.0}, "family_boost_applied": True},
            },
        ],
    )

    model = train_reranker([benchmark], leads, model_path, epochs=50, negatives_per_positive=1)
    assert model_path.exists()
    assert model.model_type == "logistic_regression"
