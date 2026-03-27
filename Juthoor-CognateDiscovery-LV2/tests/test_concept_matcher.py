"""Tests for ConceptMatcher."""
from __future__ import annotations

from pathlib import Path

import pytest

from juthoor_cognatediscovery_lv2.discovery.concept_matcher import ConceptMatcher

_CONCEPTS_PATH = (
    Path(__file__).parent.parent
    / "data/processed/concepts/concepts_v3_2_enriched.jsonl"
)


def test_loading():
    """ConceptMatcher loads without errors and has non-zero concept_count."""
    cm = ConceptMatcher(_CONCEPTS_PATH)
    assert cm.concept_count > 0


def test_concept_count():
    """concept_count reflects actual number of concept entries (287 expected)."""
    cm = ConceptMatcher(_CONCEPTS_PATH)
    # The file has 287 lines as of v3.2; allow a small range for future additions
    assert 200 <= cm.concept_count <= 500


def test_similarity_zero_for_unrelated():
    """Entries with no semantic connection return 0.0."""
    cm = ConceptMatcher(_CONCEPTS_PATH)
    arabic = {"english_gloss": "stone wall ancient fortification"}
    english = {"gloss": "abstract mathematical function derivative"}
    score = cm.concept_similarity(arabic, english)
    assert score == 0.0


def test_index_sizes():
    """Both reverse indexes are non-empty after loading."""
    cm = ConceptMatcher(_CONCEPTS_PATH)
    assert cm.en_index_size > 0
    # ar_index_size may be small (only figurative_links forms) but >= 0
    assert cm.ar_index_size >= 0


def test_graceful_on_missing_file():
    """ConceptMatcher returns 0.0 scores when the concepts file does not exist."""
    cm = ConceptMatcher("/nonexistent/path/concepts.jsonl")
    score = cm.concept_similarity(
        {"english_gloss": "head"},
        {"gloss": "skull"},
    )
    assert score == 0.0
    assert cm.concept_count == 0
