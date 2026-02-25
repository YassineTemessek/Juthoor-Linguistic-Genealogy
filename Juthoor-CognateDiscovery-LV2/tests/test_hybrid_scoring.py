"""
Tests for juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring

Covers:
- orthography_score()
- sound_score()
- skeleton_score()
- combined_score()
- compute_hybrid()
- HybridWeights dataclass
- Internal helpers (_norm_text, _skeleton, _char_ngrams, _jaccard, _seq_ratio)
  tested indirectly through the public API
"""
from __future__ import annotations

import pytest

from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import (
    HybridWeights,
    combined_score,
    compute_hybrid,
    orthography_score,
    skeleton_score,
    sound_score,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _lex(lemma="", translit="", ipa="", ipa_raw="", lang="") -> dict:
    """Build a minimal lexeme dict for testing."""
    d: dict = {}
    if lemma:
        d["lemma"] = lemma
    if translit:
        d["translit"] = translit
    if ipa:
        d["ipa"] = ipa
    if ipa_raw:
        d["ipa_raw"] = ipa_raw
    if lang:
        d["lang"] = lang
    return d


# ---------------------------------------------------------------------------
# HybridWeights
# ---------------------------------------------------------------------------

class TestHybridWeights:
    def test_default_weights_sum_close_to_one(self):
        w = HybridWeights()
        total = w.semantic + w.form + w.orthography + w.sound + w.skeleton
        assert abs(total - 1.0) < 1e-9

    def test_default_family_boost(self):
        assert HybridWeights().family_boost == pytest.approx(0.05)

    def test_custom_weights(self):
        w = HybridWeights(semantic=0.5, form=0.1, orthography=0.2, sound=0.1, skeleton=0.1)
        assert w.semantic == 0.5
        assert w.orthography == 0.2

    def test_frozen(self):
        w = HybridWeights()
        with pytest.raises((AttributeError, TypeError)):
            w.semantic = 0.9  # type: ignore[misc]


# ---------------------------------------------------------------------------
# orthography_score()
# ---------------------------------------------------------------------------

class TestOrthographyScore:
    def test_identical_strings_score_one(self):
        src = _lex(lemma="write")
        tgt = _lex(lemma="write")
        assert orthography_score(src, tgt) == pytest.approx(1.0)

    def test_completely_different_strings_score_near_zero(self):
        src = _lex(lemma="write")
        tgt = _lex(lemma="خرج")
        score = orthography_score(src, tgt)
        assert 0.0 <= score <= 0.2

    def test_similar_strings_score_higher_than_different(self):
        src = _lex(lemma="script")
        similar = _lex(lemma="scripto")
        different = _lex(lemma="apple")
        assert orthography_score(src, similar) > orthography_score(src, different)

    def test_score_in_unit_interval(self):
        pairs = [
            (_lex(lemma="alpha"), _lex(lemma="alpha")),
            (_lex(lemma="abc"), _lex(lemma="xyz")),
            (_lex(lemma="write"), _lex(lemma="wrote")),
            (_lex(lemma="كتب"), _lex(lemma="ktb")),
        ]
        for src, tgt in pairs:
            s = orthography_score(src, tgt)
            assert 0.0 <= s <= 1.0, f"Score {s} out of [0,1] for {src} vs {tgt}"

    def test_translit_preferred_over_lemma(self):
        # When translit is present, it should be used instead of lemma
        src = _lex(lemma="كَتَبَ", translit="kataba")
        tgt = _lex(lemma="kataba")
        # translit "kataba" vs lemma "kataba" → high score
        assert orthography_score(src, tgt) > 0.8

    def test_missing_lemma_returns_zero(self):
        src = _lex()
        tgt = _lex(lemma="write")
        assert orthography_score(src, tgt) == 0.0

    def test_both_empty_returns_zero(self):
        assert orthography_score(_lex(), _lex()) == 0.0

    def test_case_insensitive(self):
        src = _lex(lemma="Write")
        tgt = _lex(lemma="write")
        assert orthography_score(src, tgt) == pytest.approx(1.0)

    def test_punctuation_stripped(self):
        src = _lex(lemma="write!")
        tgt = _lex(lemma="write")
        assert orthography_score(src, tgt) == pytest.approx(1.0)

    def test_hyphen_stripped(self):
        src = _lex(lemma="well-known")
        tgt = _lex(lemma="wellknown")
        assert orthography_score(src, tgt) == pytest.approx(1.0)

    def test_symmetric(self):
        src = _lex(lemma="script")
        tgt = _lex(lemma="scripto")
        assert orthography_score(src, tgt) == pytest.approx(orthography_score(tgt, src))


# ---------------------------------------------------------------------------
# sound_score()
# ---------------------------------------------------------------------------

class TestSoundScore:
    def test_identical_ipa_returns_one(self):
        src = _lex(ipa="kætəb")
        tgt = _lex(ipa="kætəb")
        assert sound_score(src, tgt) == pytest.approx(1.0)

    def test_missing_ipa_returns_none(self):
        src = _lex(lemma="write")
        tgt = _lex(lemma="write")
        assert sound_score(src, tgt) is None

    def test_one_missing_ipa_returns_none(self):
        src = _lex(ipa="raɪt")
        tgt = _lex(lemma="write")
        assert sound_score(src, tgt) is None

    def test_ipa_raw_used_as_fallback(self):
        src = _lex(ipa_raw="raɪt")
        tgt = _lex(ipa_raw="raɪt")
        result = sound_score(src, tgt)
        assert result == pytest.approx(1.0)

    def test_ipa_preferred_over_ipa_raw(self):
        # ipa takes precedence; ipa_raw ignored when ipa is present
        src = _lex(ipa="raɪt", ipa_raw="something_else")
        tgt = _lex(ipa="raɪt")
        assert sound_score(src, tgt) == pytest.approx(1.0)

    def test_similar_ipa_higher_than_different(self):
        src = _lex(ipa="kætəb")
        similar = _lex(ipa="kɑtəb")
        different = _lex(ipa="zʌmbra")
        s1 = sound_score(src, similar)
        s2 = sound_score(src, different)
        assert s1 is not None and s2 is not None
        assert s1 > s2

    def test_score_in_unit_interval_when_present(self):
        src = _lex(ipa="kætəb")
        tgt = _lex(ipa="mɑːlɪk")
        s = sound_score(src, tgt)
        assert s is not None
        assert 0.0 <= s <= 1.0


# ---------------------------------------------------------------------------
# skeleton_score()
# ---------------------------------------------------------------------------

class TestSkeletonScore:
    def test_identical_consonant_skeleton(self):
        # "write" and "wrote" share root consonants w-r-t
        src = _lex(lemma="write")
        tgt = _lex(lemma="wrote")
        score = skeleton_score(src, tgt)
        assert score > 0.5

    def test_arabic_diacritics_stripped_for_skeleton(self):
        # Arabic short vowel diacritics should be stripped before skeleton extraction
        src = _lex(lemma="كَتَبَ")  # kataba with diacritics
        tgt = _lex(lemma="كتب")    # ktb without diacritics
        score = skeleton_score(src, tgt)
        assert score > 0.0

    def test_completely_different_skeleton_scores_low(self):
        src = _lex(lemma="bbb")
        tgt = _lex(lemma="zzz")
        score = skeleton_score(src, tgt)
        assert score == 0.0  # no shared bigrams/trigrams between 'bbb' and 'zzz'

    def test_score_in_unit_interval(self):
        pairs = [
            (_lex(lemma="write"), _lex(lemma="wrote")),
            (_lex(lemma="script"), _lex(lemma="scribe")),
            (_lex(lemma="abc"), _lex(lemma="xyz")),
        ]
        for src, tgt in pairs:
            s = skeleton_score(src, tgt)
            assert 0.0 <= s <= 1.0

    def test_ipa_preferred_over_lemma_for_skeleton(self):
        # When IPA is present it should be used for skeleton extraction
        src = _lex(ipa="raɪt")
        tgt = _lex(ipa="rɪt")
        score = skeleton_score(src, tgt)
        assert score > 0.0

    def test_empty_lemma_returns_zero(self):
        src = _lex()
        tgt = _lex(lemma="write")
        assert skeleton_score(src, tgt) == 0.0

    def test_symmetric(self):
        src = _lex(lemma="write")
        tgt = _lex(lemma="wrote")
        assert skeleton_score(src, tgt) == pytest.approx(skeleton_score(tgt, src))

    def test_vowels_removed_from_skeleton(self):
        # "aeiou" are all vowels → skeleton should be empty
        src = _lex(lemma="aeiou")
        tgt = _lex(lemma="bcdfg")
        # After removing vowels, src skeleton is empty → score 0
        assert skeleton_score(src, tgt) == 0.0

    def test_identical_consonant_roots_score_high(self):
        # k-t-b root: kataba vs kutiba — same consonantal skeleton
        src = _lex(translit="kataba")
        tgt = _lex(translit="kutiba")
        score = skeleton_score(src, tgt)
        assert score > 0.5


# ---------------------------------------------------------------------------
# combined_score()
# ---------------------------------------------------------------------------

class TestCombinedScore:
    def test_all_components_present(self):
        w = HybridWeights()
        score, used = combined_score(
            semantic_score=0.8,
            form_score=0.6,
            orthography=0.5,
            sound=0.4,
            skeleton=0.3,
            weights=w,
        )
        assert 0.0 <= score <= 1.0
        assert set(used.keys()) == {"semantic", "form", "orthography", "sound", "skeleton"}

    def test_no_components_returns_zero(self):
        w = HybridWeights()
        score, used = combined_score(
            semantic_score=None,
            form_score=None,
            orthography=None,
            sound=None,
            skeleton=None,
            weights=w,
        )
        assert score == 0.0
        assert used == {}

    def test_sound_none_excluded_from_computation(self):
        w = HybridWeights()
        # With and without sound — the remaining components should still produce a valid score
        score_with, _ = combined_score(
            semantic_score=0.8, form_score=0.6, orthography=0.5, sound=0.5, skeleton=0.4,
            weights=w,
        )
        score_without, _ = combined_score(
            semantic_score=0.8, form_score=0.6, orthography=0.5, sound=None, skeleton=0.4,
            weights=w,
        )
        # Both should be valid scores in [0,1]; they will differ
        assert 0.0 <= score_with <= 1.0
        assert 0.0 <= score_without <= 1.0

    def test_perfect_scores_produce_one(self):
        w = HybridWeights()
        score, _ = combined_score(
            semantic_score=1.0, form_score=1.0, orthography=1.0, sound=1.0, skeleton=1.0,
            weights=w,
        )
        assert score == pytest.approx(1.0)

    def test_zero_scores_produce_zero(self):
        w = HybridWeights()
        score, _ = combined_score(
            semantic_score=0.0, form_score=0.0, orthography=0.0, sound=0.0, skeleton=0.0,
            weights=w,
        )
        assert score == pytest.approx(0.0)

    def test_only_semantic_component(self):
        w = HybridWeights()
        score, used = combined_score(
            semantic_score=0.75,
            form_score=None,
            orthography=None,
            sound=None,
            skeleton=None,
            weights=w,
        )
        # Only semantic present → score should equal semantic value
        assert score == pytest.approx(0.75)
        assert "semantic" in used

    def test_weights_used_dict_keys_match_present_components(self):
        w = HybridWeights()
        _, used = combined_score(
            semantic_score=0.5,
            form_score=0.5,
            orthography=None,
            sound=0.5,
            skeleton=None,
            weights=w,
        )
        assert set(used.keys()) == {"semantic", "form", "sound"}

    def test_result_is_normalized_weighted_average(self):
        # With equal weights and equal values, score should equal the value
        w = HybridWeights(semantic=0.5, form=0.5, orthography=0.0, sound=0.0, skeleton=0.0,
                          family_boost=0.0)
        score, _ = combined_score(
            semantic_score=0.6,
            form_score=0.6,
            orthography=None,
            sound=None,
            skeleton=None,
            weights=w,
        )
        assert score == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# compute_hybrid()
# ---------------------------------------------------------------------------

class TestComputeHybrid:
    def test_returns_required_keys(self):
        src = _lex(lemma="write", lang="en")
        tgt = _lex(lemma="scribe", lang="la")
        w = HybridWeights()
        result = compute_hybrid(source=src, target=tgt, semantic=0.7, form=0.5, weights=w)

        assert "components" in result
        assert "combined_score" in result
        assert "weights_used" in result
        assert "family_boost_applied" in result

    def test_components_dict_has_scoring_keys(self):
        src = _lex(lemma="write", lang="en")
        tgt = _lex(lemma="wrote", lang="en")
        result = compute_hybrid(
            source=src, target=tgt, semantic=0.8, form=0.7, weights=HybridWeights()
        )
        comp = result["components"]
        assert "orthography" in comp
        assert "sound" in comp
        assert "skeleton" in comp

    def test_combined_score_in_unit_interval(self):
        src = _lex(lemma="write", lang="en")
        tgt = _lex(lemma="scribe", lang="la")
        result = compute_hybrid(
            source=src, target=tgt, semantic=0.8, form=0.6, weights=HybridWeights()
        )
        assert 0.0 <= result["combined_score"] <= 1.0

    def test_family_boost_applied_same_family(self):
        # Arabic and Hebrew are in the same (semitic) family
        src = _lex(lemma="كتب", lang="ar")
        tgt = _lex(lemma="כתב", lang="he")
        result = compute_hybrid(
            source=src, target=tgt, semantic=0.5, form=0.5, weights=HybridWeights()
        )
        assert result["family_boost_applied"] is True

    def test_family_boost_not_applied_different_family(self):
        # Arabic and English are in different families
        src = _lex(lemma="كتب", lang="ar")
        tgt = _lex(lemma="write", lang="en")
        result = compute_hybrid(
            source=src, target=tgt, semantic=0.5, form=0.5, weights=HybridWeights()
        )
        assert result["family_boost_applied"] is False

    def test_family_boost_increases_score(self):
        src = _lex(lemma="كتب", lang="ar")
        tgt_same = _lex(lemma="כתב", lang="he")    # same family: semitic
        tgt_diff = _lex(lemma="write", lang="en")  # different family: germanic

        w = HybridWeights()
        result_same = compute_hybrid(source=src, target=tgt_same, semantic=0.5, form=0.5, weights=w)
        result_diff = compute_hybrid(source=src, target=tgt_diff, semantic=0.5, form=0.5, weights=w)

        # Same-family pair should have a boost applied, so score should be >= cross-family
        assert result_same["combined_score"] >= result_diff["combined_score"]

    def test_family_boost_zero_disables_boost(self):
        src = _lex(lemma="كتب", lang="ar")
        tgt = _lex(lemma="כתב", lang="he")

        w_with = HybridWeights(family_boost=0.05)
        w_without = HybridWeights(family_boost=0.0)

        result_with = compute_hybrid(source=src, target=tgt, semantic=0.5, form=0.5, weights=w_with)
        result_without = compute_hybrid(source=src, target=tgt, semantic=0.5, form=0.5, weights=w_without)

        # boost=0 means no increase; boost=0.05 means same-family pairs are slightly higher
        assert result_with["combined_score"] >= result_without["combined_score"]

    def test_sound_component_none_when_ipa_absent(self):
        src = _lex(lemma="write", lang="en")
        tgt = _lex(lemma="scribe", lang="la")
        result = compute_hybrid(
            source=src, target=tgt, semantic=0.7, form=0.5, weights=HybridWeights()
        )
        # No IPA in either lexeme → sound should be None
        assert result["components"]["sound"] is None

    def test_sound_component_present_when_ipa_provided(self):
        src = _lex(lemma="write", ipa="raɪt", lang="en")
        tgt = _lex(lemma="rite", ipa="raɪt", lang="en")
        result = compute_hybrid(
            source=src, target=tgt, semantic=0.9, form=0.8, weights=HybridWeights()
        )
        assert result["components"]["sound"] is not None

    def test_combined_score_rounded_to_4_decimals(self):
        src = _lex(lemma="write", lang="en")
        tgt = _lex(lemma="wrote", lang="en")
        result = compute_hybrid(
            source=src, target=tgt, semantic=0.123456789, form=0.987654321,
            weights=HybridWeights()
        )
        score = result["combined_score"]
        # Check 4 decimal places: str representation should have at most 4 decimal digits
        assert score == round(score, 4)

    def test_semantic_none_excluded_from_score(self):
        src = _lex(lemma="write", lang="en")
        tgt = _lex(lemma="wrote", lang="en")
        result = compute_hybrid(
            source=src, target=tgt, semantic=None, form=0.5, weights=HybridWeights()
        )
        assert "combined_score" in result
        assert 0.0 <= result["combined_score"] <= 1.0

    def test_language_field_alias_lang_vs_language(self):
        # compute_hybrid reads 'lang' or 'language' field
        src = {"lemma": "كتب", "language": "ar"}
        tgt = {"lemma": "כתב", "language": "he"}
        result = compute_hybrid(
            source=src, target=tgt, semantic=0.5, form=0.5, weights=HybridWeights()
        )
        assert result["family_boost_applied"] is True
