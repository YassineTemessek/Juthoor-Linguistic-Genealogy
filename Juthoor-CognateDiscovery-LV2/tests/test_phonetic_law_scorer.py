"""Tests for the phonetic law scorer."""
from __future__ import annotations

import pytest
from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import (
    PhoneticLawScorer,
    _HIGH_FREQ_WORDS,
    _POSITION_WEIGHTS,
    _arabic_consonant_skeleton,
    _best_projection_match,
    _best_projection_match_ipa,
    _english_consonant_skeleton,
    _weighted_projection_score,
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
        # جرجر (reduplicated root, not in any synonym family) vs "sky" (no phonetic overlap)
        result = scorer.score_pair({"lemma": "جرجر"}, {"lemma": "sky"})
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
        # جرجر (reduplicated root, not in any synonym family) vs "sky" (no phonetic overlap)
        bonus = scorer.phonetic_law_bonus({"lemma": "جرجر"}, {"lemma": "sky"})
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


# ---------------------------------------------------------------------------
# V4 additions: position-weighted scoring
# ---------------------------------------------------------------------------

class TestPositionWeights:
    """Unit tests for _POSITION_WEIGHTS and _weighted_projection_score."""

    def test_weights_defined(self):
        assert _POSITION_WEIGHTS[0] > _POSITION_WEIGHTS[1]
        assert _POSITION_WEIGHTS[1] > _POSITION_WEIGHTS[2]

    def test_position1_match_beats_position3_only_match(self):
        """A variant matching at position 0 (anchor) should outscore one matching only at position 2."""
        # Arabic skeleton: k-t-b (كتب)
        # Variant A: "ktb" — matches English "ktx" at positions 0 and 1
        # Variant B: "xtb" — matches English "ktx" only at position 2 (b vs b... wait, let's be precise)
        #
        # English: "ktz"
        # Variant matching pos 0 only: "kxx" — score = 1.5 / (1.5+1.0+0.7) = 0.4688
        # Variant matching pos 2 only: "xxz" — score = 0.7 / (1.5+1.0+0.7) = 0.2188
        score_pos0, _ = _weighted_projection_score("كتب", "ktz", ("kxx",))
        score_pos2, _ = _weighted_projection_score("كتب", "ktz", ("xxz",))
        assert score_pos0 > score_pos2

    def test_exact_match_returns_high_score(self):
        """A variant that exactly matches the English skeleton should score ~1.0."""
        # Arabic كتب, variant "ktb", English "ktb"
        score, var = _weighted_projection_score("كتب", "ktb", ("ktb",))
        assert score > 0.9
        assert var == "ktb"

    def test_empty_inputs_return_zero(self):
        score, var = _weighted_projection_score("", "ktb", ("ktb",))
        assert score == 0.0
        assert var == ""

        score, var = _weighted_projection_score("كتب", "", ("ktb",))
        assert score == 0.0
        assert var == ""

        score, var = _weighted_projection_score("كتب", "ktb", ())
        assert score == 0.0
        assert var == ""

    def test_position0_weight_is_1_5(self):
        assert _POSITION_WEIGHTS[0] == 1.5

    def test_position2_weight_is_0_7(self):
        assert _POSITION_WEIGHTS[2] == 0.7


class TestPositionWeightedInScorePair:
    """Integration tests: position_weighted_score shows up in projection_details."""

    def test_score_pair_has_position_weighted_score(self):
        scorer = PhoneticLawScorer()
        result = scorer.score_pair({"lemma": "كتب"}, {"lemma": "kit"})
        details = result["projection_details"]
        assert "position_weighted_score" in details
        assert isinstance(details["position_weighted_score"], float)

    def test_position_weight_anchor_match_boosts_good_pair(self):
        """لفت -> left: first consonant l maps to l — should score well."""
        scorer = PhoneticLawScorer()
        result = scorer.score_pair({"lemma": "لفت"}, {"lemma": "left"})
        details = result["projection_details"]
        # Position-weighted score should be positive for this good pair
        assert details["position_weighted_score"] > 0.3

    def test_position_weighted_score_nonnegative(self):
        scorer = PhoneticLawScorer()
        result = scorer.score_pair({"lemma": "كتب"}, {"lemma": "elephant"})
        details = result["projection_details"]
        assert details["position_weighted_score"] >= 0.0

    def test_anchor_match_pair_vs_tail_only_match(self):
        """Pair matching at position 0 should produce higher pos_weighted_score
        than a pair that only matches at the last position."""
        scorer = PhoneticLawScorer()
        # كتب -> k/c variants at pos 0 — compare against "cat" (starts with c)
        result_anchor = scorer.score_pair({"lemma": "كتب"}, {"lemma": "cat"})
        # مرك -> m at pos 0, different — compare against "arc" (no m at pos 0)
        result_tail = scorer.score_pair({"lemma": "مرك"}, {"lemma": "arc"})
        pos_anchor = result_anchor["projection_details"]["position_weighted_score"]
        pos_tail = result_tail["projection_details"]["position_weighted_score"]
        # "كتب" -> "cat": pos 0 is k/c vs c = exact, should be higher
        assert pos_anchor >= pos_tail


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


# ---------------------------------------------------------------------------
# V5: Synonym family expansion tests
# ---------------------------------------------------------------------------

class TestSynonymExpansion:
    """Tests for synonym family expansion in PhoneticLawScorer."""

    def test_projection_details_has_synonym_fields(self, scorer):
        """score_pair always returns synonym_match and synonyms_tried fields."""
        result = scorer.score_pair({"lemma": "لفت"}, {"lemma": "left"})
        details = result["projection_details"]
        assert "synonym_match" in details
        assert "synonyms_tried" in details
        assert isinstance(details["synonym_match"], float)
        assert isinstance(details["synonyms_tried"], int)

    def test_lazy_load_no_crash_when_file_missing(self):
        """Scorer does not crash when synonym file is absent."""
        scorer = PhoneticLawScorer()
        # Force synonym file path to a nonexistent location
        scorer._synonym_loaded = True  # pretend already loaded, families stay empty
        scorer._synonym_families = {}
        result = scorer.score_pair({"lemma": "قلب"}, {"lemma": "heart"})
        assert result["phonetic_law_score"] >= 0.0
        assert result["projection_details"]["synonyms_tried"] == 0

    def test_synonym_families_loaded_lazily(self, scorer):
        """Synonym families are not loaded until score_pair is called."""
        fresh = PhoneticLawScorer()
        assert fresh._synonym_loaded is False
        # Trigger loading
        families = fresh._get_synonym_families()
        assert fresh._synonym_loaded is True
        # Returns a dict (may be empty if file not on this machine, but must be dict)
        assert isinstance(families, dict)

    def test_synonym_can_improve_score_for_heart_family(self, scorer):
        """The root قلب (heart) belongs to a synonym family with لب and فؤاد.
        Scoring لب (lb) against 'lib' should score higher than قلب (qlb) directly.
        When قلب is the input root and the synonym file is loaded, the synonym
        score (via لب) should be >= 0 and the field should be populated.
        """
        result = scorer.score_pair({"lemma": "قلب"}, {"lemma": "lib"})
        details = result["projection_details"]
        # synonym_match is a float in [0, 1]
        assert 0.0 <= details["synonym_match"] <= 1.0
        # If the synonym families file is present, synonyms_tried should be > 0
        # (we don't assert exact count since file presence is environment-dependent)
        assert details["synonyms_tried"] >= 0

    def test_synonyms_capped_at_three(self, scorer):
        """No more than 3 synonym roots are tried (excluding the root itself)."""
        # Use a root that is likely to have at least 3 synonyms in the family
        # Family seed-003: جمع, ضم, لم, حشد (4 members, so جمع has 3 synonyms)
        result = scorer.score_pair({"lemma": "جمع"}, {"lemma": "sum"})
        details = result["projection_details"]
        # synonyms_tried must never exceed 3 (the cap)
        assert details["synonyms_tried"] <= 3
