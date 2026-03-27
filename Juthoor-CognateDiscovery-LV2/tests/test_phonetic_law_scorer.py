"""Tests for the phonetic law scorer."""
from __future__ import annotations

import pytest
from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import (
    PhoneticLawScorer,
    _arabic_consonant_skeleton,
    _best_projection_match,
    _english_consonant_skeleton,
)
from juthoor_cognatediscovery_lv2.discovery.correspondence import cross_lingual_skeleton_score


@pytest.fixture
def scorer():
    return PhoneticLawScorer()


class TestConsonantSkeletons:
    def test_english_skeleton(self):
        assert _english_consonant_skeleton("ruthless") == "rthlss"
        assert _english_consonant_skeleton("left") == "lft"
        assert _english_consonant_skeleton("dam") == "dm"

    def test_arabic_skeleton(self):
        skel = _arabic_consonant_skeleton("رثى")
        assert "ر" in skel
        assert "ث" in skel


class TestProjectionMatch:
    def test_left_lft(self):
        score, _ = _best_projection_match("لفت", "left")
        assert score > 0.5

    def test_dam(self):
        score, _ = _best_projection_match("دأم", "dam")
        assert score > 0.4


class TestScorePair:
    def test_ruth_ratha(self, scorer):
        result = scorer.score_pair({"lemma": "رثى"}, {"lemma": "ruth"})
        assert result["phonetic_law_score"] > 0.5

    def test_left_laft(self, scorer):
        result = scorer.score_pair({"lemma": "لفت"}, {"lemma": "left"})
        assert result["phonetic_law_score"] > 0.6

    def test_dam(self, scorer):
        result = scorer.score_pair({"lemma": "دأم"}, {"lemma": "dam"})
        assert result["phonetic_law_score"] > 0.5

    def test_fog_fayj(self, scorer):
        result = scorer.score_pair({"lemma": "فيج"}, {"lemma": "fog"})
        assert result["phonetic_law_score"] > 0.3

    def test_random_low(self, scorer):
        result = scorer.score_pair({"lemma": "كتب"}, {"lemma": "elephant"})
        assert result["phonetic_law_score"] < 0.5


class TestBonus:
    def test_bonus_good_pair(self, scorer):
        bonus = scorer.phonetic_law_bonus({"lemma": "لفت"}, {"lemma": "left"})
        assert bonus > 0.0

    def test_bonus_bad_pair(self, scorer):
        bonus = scorer.phonetic_law_bonus({"lemma": "كتب"}, {"lemma": "elephant"})
        assert bonus == 0.0


class TestCrossLingualSkeleton:
    def test_basic(self):
        score = cross_lingual_skeleton_score("رثى", "ruth")
        assert score > 0
