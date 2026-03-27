"""Tests for genome_bonus as reranker feature."""

import numpy as np
import pytest

from juthoor_cognatediscovery_lv2.discovery.rerank import FEATURE_NAMES, _feature_vector


def test_genome_bonus_in_feature_names():
    assert "genome_bonus" in FEATURE_NAMES, "genome_bonus must be a reranker feature"


def test_genome_bonus_is_last_feature():
    """genome_bonus should be the 11th feature (index 10)."""
    assert FEATURE_NAMES.index("genome_bonus") == 10


def test_feature_vector_length_is_13():
    entry = {
        "scores": {"semantic": 0.8, "form": 0.5},
        "hybrid": {
            "components": {
                "orthography": 0.3, "sound": 0.2, "skeleton": 0.1,
                "root_match": 0.0, "correspondence": 0.0,
                "weak_radical_match": 0.0, "hamza_match": 0.0,
                "genome_bonus": 0.08,
            },
            "family_boost_applied": False,
        },
    }
    vec = _feature_vector(entry)
    assert len(vec) == len(FEATURE_NAMES)


def test_feature_vector_extracts_genome_bonus():
    entry = {
        "scores": {"semantic": 0.8, "form": 0.5},
        "hybrid": {
            "components": {
                "orthography": 0.3, "sound": 0.2, "skeleton": 0.1,
                "root_match": 0.0, "correspondence": 0.0,
                "weak_radical_match": 0.0, "hamza_match": 0.0,
                "genome_bonus": 0.08,
            },
            "family_boost_applied": False,
        },
    }
    vec = _feature_vector(entry)
    assert vec[10] == pytest.approx(0.08)


def test_feature_vector_defaults_genome_bonus_to_zero():
    entry = {
        "scores": {"semantic": 0.5, "form": 0.3},
        "hybrid": {"components": {}, "family_boost_applied": False},
    }
    vec = _feature_vector(entry)
    assert len(vec) == len(FEATURE_NAMES)
    assert vec[10] == 0.0
