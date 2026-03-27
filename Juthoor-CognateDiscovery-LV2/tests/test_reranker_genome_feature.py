"""Tests for genome_bonus as reranker feature."""

import numpy as np
import pytest

from juthoor_cognatediscovery_lv2.discovery.rerank import FEATURE_NAMES, _feature_vector


def test_genome_bonus_in_feature_names():
    assert "genome_bonus" in FEATURE_NAMES, "genome_bonus must be a reranker feature"


def test_genome_bonus_feature_index():
    """genome_bonus should stay in the compact v3 feature set."""
    assert FEATURE_NAMES.index("genome_bonus") == 4


def test_feature_vector_length_matches_feature_names():
    entry = {
        "scores": {"semantic": 0.8, "form": 0.5},
        "hybrid": {
            "components": {
                "sound": 0.2,
                "correspondence": 0.0,
                "genome_bonus": 0.08,
            },
        },
    }
    vec = _feature_vector(entry)
    assert len(vec) == len(FEATURE_NAMES)


def test_feature_vector_extracts_genome_bonus():
    entry = {
        "scores": {"semantic": 0.8, "form": 0.5},
        "hybrid": {
            "components": {
                "sound": 0.2,
                "correspondence": 0.0,
                "genome_bonus": 0.08,
            },
        },
    }
    vec = _feature_vector(entry)
    assert vec[4] == pytest.approx(0.08)


def test_feature_vector_defaults_genome_bonus_to_zero():
    entry = {
        "scores": {"semantic": 0.5, "form": 0.3},
        "hybrid": {"components": {}},
    }
    vec = _feature_vector(entry)
    assert len(vec) == len(FEATURE_NAMES)
    assert vec[4] == 0.0
