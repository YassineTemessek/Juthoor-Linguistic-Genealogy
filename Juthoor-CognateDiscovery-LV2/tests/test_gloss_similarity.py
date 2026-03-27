"""Tests for gloss_similarity module."""
from __future__ import annotations

import pytest

from juthoor_cognatediscovery_lv2.discovery.gloss_similarity import (
    _extract_content_words,
    gloss_similarity,
    has_semantic_overlap,
)


# ---------------------------------------------------------------------------
# _extract_content_words
# ---------------------------------------------------------------------------

class TestExtractContentWords:
    def test_stopwords_filtered(self):
        result = _extract_content_words("the cat is in the house")
        assert "the" not in result
        assert "is" not in result
        assert "in" not in result
        assert "cat" in result
        assert "house" in result

    def test_short_words_excluded(self):
        # words under 3 chars are excluded by regex
        result = _extract_content_words("go do it up on")
        assert result == set()

    def test_empty_string(self):
        assert _extract_content_words("") == set()

    def test_case_insensitive(self):
        result = _extract_content_words("RIVER River river")
        assert result == {"river"}


# ---------------------------------------------------------------------------
# gloss_similarity
# ---------------------------------------------------------------------------

class TestGlossSimilarity:
    def test_known_cognate_pair_has_positive_similarity(self):
        # Arabic 'malik' (king) and English 'king' share no words, but
        # Arabic 'kalb' (dog) and English 'dog' share no words either.
        # Use a pair that actually shares gloss words.
        source = {"meaning_text": "heart organ blood pump"}
        target = {"gloss": "heart blood organ"}
        score = gloss_similarity(source, target)
        assert score > 0.0
        # heart, organ, blood are shared; union = {heart, organ, blood, pump}
        # intersection = {heart, organ, blood} -> 3/4 = 0.75
        assert score == pytest.approx(3 / 4)

    def test_unrelated_pair_returns_zero(self):
        source = {"meaning_text": "mountain peak summit"}
        target = {"gloss": "fish water ocean"}
        score = gloss_similarity(source, target)
        assert score == 0.0

    def test_empty_source_returns_zero(self):
        source = {}
        target = {"gloss": "light illuminate"}
        assert gloss_similarity(source, target) == 0.0

    def test_empty_target_returns_zero(self):
        source = {"meaning_text": "water river flow"}
        target = {}
        assert gloss_similarity(source, target) == 0.0

    def test_both_empty_returns_zero(self):
        assert gloss_similarity({}, {}) == 0.0

    def test_none_values_handled(self):
        source = {"meaning_text": None, "gloss": None, "short_gloss": "tree plant"}
        target = {"meaning_text": None, "gloss": "plant grow"}
        score = gloss_similarity(source, target)
        assert score > 0.0
        assert "plant" in _extract_content_words("tree plant")

    def test_stopword_only_glosses_return_zero(self):
        source = {"gloss": "a the in of to"}
        target = {"gloss": "is was be and or"}
        assert gloss_similarity(source, target) == 0.0

    def test_uses_multiple_gloss_fields(self):
        source = {"meaning_text": "sun", "gloss": "light", "short_gloss": "star", "gloss_plain": "bright"}
        target = {"meaning_text": "moon", "gloss": "light", "short_gloss": "night"}
        score = gloss_similarity(source, target)
        # shared: light; src_words = {sun, light, star, bright}; tgt_words = {moon, light, night}
        # intersection = {light}, union = {sun, light, star, bright, moon, night} = 6
        assert score == pytest.approx(1 / 6)

    def test_identical_glosses_return_one(self):
        source = {"gloss": "large big enormous"}
        target = {"gloss": "large big enormous"}
        assert gloss_similarity(source, target) == pytest.approx(1.0)

    def test_partial_overlap(self):
        source = {"gloss": "river water flow stream"}
        target = {"gloss": "water ocean sea flow"}
        score = gloss_similarity(source, target)
        # src = {river, water, flow, stream}; tgt = {water, ocean, sea, flow}
        # intersection = {water, flow} = 2; union = 6
        assert score == pytest.approx(2 / 6)


# ---------------------------------------------------------------------------
# has_semantic_overlap
# ---------------------------------------------------------------------------

class TestHasSemanticOverlap:
    def test_overlap_above_threshold(self):
        source = {"gloss": "heart blood vessel pump"}
        target = {"gloss": "heart muscle organ"}
        # heart is shared: 1/6 ~0.167 > 0.05
        assert has_semantic_overlap(source, target, min_overlap=0.05) is True

    def test_no_overlap_below_threshold(self):
        source = {"gloss": "mountain rock peak"}
        target = {"gloss": "fish ocean water"}
        assert has_semantic_overlap(source, target, min_overlap=0.05) is False

    def test_default_threshold_is_005(self):
        source = {"gloss": "mountain rock peak"}
        target = {"gloss": "fish ocean water"}
        assert has_semantic_overlap(source, target) is False

    def test_zero_threshold_true_when_any_overlap(self):
        source = {"gloss": "tree leaf branch"}
        target = {"gloss": "tree wood lumber"}
        assert has_semantic_overlap(source, target, min_overlap=0.0) is True

    def test_empty_glosses_false(self):
        assert has_semantic_overlap({}, {}) is False
