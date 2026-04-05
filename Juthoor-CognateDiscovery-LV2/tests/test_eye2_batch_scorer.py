"""Tests for the Eye 2 batch scorer (Eye 1 → Eye 2 pipeline connector)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.eye2_batch_scorer import (
    load_eye1_candidates,
    load_scored_pairs,
)


def _write_eye1(path: Path, records: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def test_load_eye1_candidates_filters_by_score():
    records = [
        {"arabic_root": "فرس", "target_lemma": "a", "discovery_score": 0.9, "lang": "grc"},
        {"arabic_root": "فرس", "target_lemma": "b", "discovery_score": 0.5, "lang": "grc"},
        {"arabic_root": "فرس", "target_lemma": "c", "discovery_score": 0.8, "lang": "grc"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
        path = Path(f.name)

    try:
        result = load_eye1_candidates(path, min_discovery_score=0.7, top_n_per_root=10)
        assert len(result) == 2  # only 0.9 and 0.8 pass
        assert result[0]["target_lemma"] == "a"  # sorted desc by score
        assert result[1]["target_lemma"] == "c"
    finally:
        path.unlink()


def test_load_eye1_candidates_top_n():
    records = [
        {"arabic_root": "كلب", "target_lemma": f"w{i}", "discovery_score": 0.9 - i * 0.01, "lang": "lat"}
        for i in range(10)
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
        path = Path(f.name)

    try:
        result = load_eye1_candidates(path, min_discovery_score=0.5, top_n_per_root=3)
        assert len(result) == 3
        assert result[0]["discovery_score"] >= result[1]["discovery_score"]
    finally:
        path.unlink()


def test_load_eye1_candidates_lang_filter():
    records = [
        {"arabic_root": "حكم", "target_lemma": "x", "discovery_score": 0.9, "lang": "grc"},
        {"arabic_root": "حكم", "target_lemma": "y", "discovery_score": 0.9, "lang": "lat"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
        path = Path(f.name)

    try:
        result = load_eye1_candidates(path, min_discovery_score=0.5, top_n_per_root=10, lang_filter="grc")
        assert len(result) == 1
        assert result[0]["target_lemma"] == "x"
    finally:
        path.unlink()


def test_load_scored_pairs():
    records = [
        {"source_lemma": "فرس", "target_lemma": "equus"},
        {"source_lemma": "كلب", "target_lemma": "canis"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
        path = Path(f.name)

    try:
        pairs = load_scored_pairs(path)
        assert len(pairs) == 2
        assert ("فرس", "equus") in pairs
        assert ("كلب", "canis") in pairs
    finally:
        path.unlink()


def test_load_scored_pairs_missing_file():
    pairs = load_scored_pairs(Path("/nonexistent/file.jsonl"))
    assert pairs == set()
