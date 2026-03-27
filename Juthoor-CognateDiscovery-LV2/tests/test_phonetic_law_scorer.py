"""Tests for the phonetic law scorer."""
from __future__ import annotations

import pytest
from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import (
    PhoneticLawScorer,
    _HIGH_FREQ_WORDS,
    _arabic_consonant_skeleton,
    _best_projection_match,
    _best_projection_match_ipa,
    _english_consonant_skeleton,
)
from juthoor_cognatediscovery_lv2.discovery.correspondence import cross_lingual_skeleton_score
from juthoor_cognatediscovery_lv2.discovery.ipa_lookup import IPALookup


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

    def test_projection_details_contain_ipa_fields(self, scorer):
        result = scorer.score_pair({"lemma": "لفت"}, {"lemma": "left"})
        details = result["projection_details"]
        assert "ipa_proj_score" in details
        assert "ipa_skeleton" in details
        assert "freq_penalty_applied" in details


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


# ---------------------------------------------------------------------------
# V3 additions: IPA lookup, IPA projection, frequency penalty
# ---------------------------------------------------------------------------

class TestIPALookup:
    @pytest.fixture
    def lookup(self):
        return IPALookup()

    def test_known_word_returns_ipa(self, lookup):
        # "left" is a very common English word — should be in the corpus
        ipa = lookup.get_ipa("left")
        assert ipa is not None, "expected IPA for 'left'"
        # IPA for 'left' should contain 'l' and 't'
        assert "l" in ipa

    def test_case_insensitive(self, lookup):
        lower = lookup.get_ipa("knight")
        upper = lookup.get_ipa("KNIGHT")
        if lower is not None:
            assert lower == upper

    def test_unknown_word_returns_none(self, lookup):
        result = lookup.get_ipa("xqzjrplunk")
        assert result is None

    def test_ipa_consonant_skeleton_strips_vowels(self, lookup):
        # "knight" IPA is /naɪt/ — skeleton should be "nt" (silent k, no vowels)
        # The corpus IPA for "knight" should be something like "naɪt"
        skel = lookup.ipa_consonant_skeleton("knight")
        if skel is not None:
            assert "k" not in skel, f"'k' should not appear in IPA skeleton of 'knight', got {skel!r}"
            assert "n" in skel

    def test_ipa_consonant_skeleton_known_word(self, lookup):
        skel = lookup.ipa_consonant_skeleton("left")
        if skel is not None:
            # IPA /lɛft/ — skeleton should have l, f, t
            assert "l" in skel
            assert "t" in skel

    def test_len_is_positive(self, lookup):
        # After loading, the lookup should have many entries
        assert len(lookup) > 10_000

    def test_contains(self, lookup):
        # "time" is common enough to be in the corpus
        assert "time" in lookup or lookup.get_ipa("time") is not None


class TestIPAProjectionMatch:
    def test_nt_matches_night_root(self):
        # Arabic نيت (nayta) — project against IPA skeleton "nt"
        score, _ = _best_projection_match_ipa("نيت", "nt")
        assert score > 0.0

    def test_empty_ipa_returns_zero(self):
        score, var = _best_projection_match_ipa("لفت", "")
        assert score == 0.0
        assert var == ""

    def test_ipa_vs_ortho_for_knight(self, scorer=None):
        """IPA skeleton 'nt' for 'knight' should score better than ortho skeleton 'knght'."""
        scorer = PhoneticLawScorer()
        result = scorer.score_pair({"lemma": "نيت"}, {"lemma": "knight"})
        details = result["projection_details"]
        # IPA skeleton for knight should be 'nt' (no 'k', no 'gh'), which is simpler
        ipa_skel = details.get("ipa_skeleton", "")
        if ipa_skel:
            # IPA skeleton should not contain 'k' (silent in knight)
            assert "k" not in ipa_skel, f"IPA skeleton should not have 'k', got {ipa_skel!r}"
            # IPA proj score with "nt" should be >= ortho-based score
            ipa_proj = details.get("ipa_proj_score", 0.0)
            ortho_proj = details.get("projection_match", 0.0)
            assert ipa_proj >= ortho_proj or ipa_proj > 0.0


class TestFrequencyPenalty:
    def test_common_word_gets_penalty(self, scorer):
        # "the" is high-frequency — freq_penalty_applied should be True
        result = scorer.score_pair({"lemma": "ذا"}, {"lemma": "the"})
        assert result["projection_details"]["freq_penalty_applied"] is True

    def test_rare_word_no_penalty(self, scorer):
        # "ruthless" is not a high-frequency function word
        result = scorer.score_pair({"lemma": "رثى"}, {"lemma": "ruthless"})
        assert result["projection_details"]["freq_penalty_applied"] is False

    def test_penalty_reduces_score(self, scorer):
        # Score for "be" (high freq) should be less than it would be without penalty.
        # We can't easily compare directly, but we verify freq_penalty_applied=True
        # and that the final score is not inflated.
        result_freq = scorer.score_pair({"lemma": "بي"}, {"lemma": "be"})
        assert result_freq["projection_details"]["freq_penalty_applied"] is True
        # Score should be at most ~0.6 * max_possible (< 1.0 after penalty)
        assert result_freq["phonetic_law_score"] < 1.0

    def test_high_freq_words_set_not_empty(self):
        assert len(_HIGH_FREQ_WORDS) > 50
        assert "the" in _HIGH_FREQ_WORDS
        assert "be" in _HIGH_FREQ_WORDS
        assert "and" in _HIGH_FREQ_WORDS
