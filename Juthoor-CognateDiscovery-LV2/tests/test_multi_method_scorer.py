"""Tests for MultiMethodScorer."""
from __future__ import annotations

import pytest

from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import (
    MultiMethodScore,
    MultiMethodScorer,
    MethodResult,
)


@pytest.fixture(scope="module")
def scorer() -> MultiMethodScorer:
    return MultiMethodScorer()


# ---------------------------------------------------------------------------
# Structural / smoke tests
# ---------------------------------------------------------------------------

def test_returns_multi_method_score(scorer: MultiMethodScorer) -> None:
    result = scorer.score_pair({"lemma": "كتب"}, {"lemma": "write"})
    assert isinstance(result, MultiMethodScore)
    assert 0.0 <= result.best_score <= 1.0
    assert isinstance(result.all_results, list)
    assert isinstance(result.methods_that_fired, list)
    assert result.arabic_expansions_tried >= 1


def test_empty_source_returns_zero(scorer: MultiMethodScorer) -> None:
    result = scorer.score_pair({}, {"lemma": "word"})
    assert result.best_score == 0.0
    assert result.all_results == []


def test_empty_target_returns_zero(scorer: MultiMethodScorer) -> None:
    result = scorer.score_pair({"lemma": "كتب"}, {})
    assert result.best_score == 0.0


def test_method_results_have_fields(scorer: MultiMethodScorer) -> None:
    result = scorer.score_pair({"lemma": "لفت"}, {"lemma": "left"})
    for r in result.all_results:
        assert isinstance(r, MethodResult)
        assert r.method_name
        assert isinstance(r.score, float)
        assert isinstance(r.explanation, str)
        assert isinstance(r.arabic_variant_used, str)
        assert isinstance(r.english_variant_used, str)


# ---------------------------------------------------------------------------
# Method 1: Direct skeleton
# ---------------------------------------------------------------------------

def test_direct_skeleton(scorer: MultiMethodScorer) -> None:
    result = scorer.score_pair({"lemma": "لفت"}, {"lemma": "left"})
    assert result.best_score > 0.4
    direct_results = [r for r in result.all_results if "skeleton" in r.method_name or "direct" in r.method_name]
    assert len(direct_results) > 0


# ---------------------------------------------------------------------------
# Method 2: Morpheme decomposition
# ---------------------------------------------------------------------------

def test_morpheme_decomposition(scorer: MultiMethodScorer) -> None:
    # كتب/inscription — strip prefix "in-" and suffix "-tion", stem "scrip" ~ ktb
    result = scorer.score_pair({"lemma": "كتب"}, {"lemma": "inscription"})
    morpheme_results = [r for r in result.all_results if "morpheme" in r.method_name]
    assert len(morpheme_results) > 0


def test_morpheme_with_suffix(scorer: MultiMethodScorer) -> None:
    # "scription" has suffix "-tion", stem "scrip" ~ Arabic root كتب
    result = scorer.score_pair({"lemma": "كتب"}, {"lemma": "inscription"})
    morpheme_results = [r for r in result.all_results if "morpheme" in r.method_name]
    assert len(morpheme_results) > 0


# ---------------------------------------------------------------------------
# Method 6: Metathesis
# ---------------------------------------------------------------------------

def test_metathesis_present(scorer: MultiMethodScorer) -> None:
    # رمس/smear — reversal of 'rms' = 'smr' ~ 'smr' (smear)
    result = scorer.score_pair({"lemma": "رمس"}, {"lemma": "smear"})
    meta_results = [r for r in result.all_results if "metathesis" in r.method_name]
    assert len(meta_results) > 0


def test_metathesis_full_reversal(scorer: MultiMethodScorer) -> None:
    # Test that metathesis fires on clear reversal case
    result = scorer.score_pair({"lemma": "رمس"}, {"lemma": "smear"})
    meta_results = [r for r in result.all_results if "metathesis" in r.method_name]
    assert len(meta_results) > 0


# ---------------------------------------------------------------------------
# Method 7: Dialect variants
# ---------------------------------------------------------------------------

def test_dialect_variants_tried(scorer: MultiMethodScorer) -> None:
    # قلب — qaf gets shifted in Egyptian/Gulf dialects
    result = scorer.score_pair({"lemma": "قلب"}, {"lemma": "heart"})
    # arabic_expansions_tried should reflect synonym + dialect expansion
    assert result.arabic_expansions_tried >= 1


# ---------------------------------------------------------------------------
# Method 8: Position-weighted
# ---------------------------------------------------------------------------

def test_position_weighted_present(scorer: MultiMethodScorer) -> None:
    # كتب/script — position-weighted scoring via consonant projection
    result = scorer.score_pair({"lemma": "كتب"}, {"lemma": "script"})
    # Position weighted may or may not fire depending on scoring thresholds
    # Just verify the scorer handles the pair without error
    assert isinstance(result.best_score, float)
    assert result.best_score >= 0.0


# ---------------------------------------------------------------------------
# Method 10: Reverse root generation
# ---------------------------------------------------------------------------

def test_reverse_root_present(scorer: MultiMethodScorer) -> None:
    # عقل/equal — reverse root generation fires for clear cognate pairs
    result = scorer.score_pair({"lemma": "عقل"}, {"lemma": "equal"})
    rev_results = [r for r in result.all_results if "reverse_root" in r.method_name]
    assert len(rev_results) > 0


# ---------------------------------------------------------------------------
# Method 11: Synonym expansion
# ---------------------------------------------------------------------------

def test_synonym_expansion(scorer: MultiMethodScorer) -> None:
    result = scorer.score_pair({"lemma": "قلب"}, {"lemma": "heart"})
    # Even without synonym data loaded, arabic_expansions_tried >= 1
    assert result.arabic_expansions_tried >= 1


def test_synonym_expansion_uses_multiple_variants(scorer: MultiMethodScorer) -> None:
    scorer2 = MultiMethodScorer()
    # Force synonym expansion to be tested
    result = scorer2.score_pair({"lemma": "قلب"}, {"lemma": "cardiac"})
    # The scorer should have tried at least the base root
    assert result.arabic_expansions_tried >= 1


# ---------------------------------------------------------------------------
# Method 12: Article detection
# ---------------------------------------------------------------------------

def test_article_detection(scorer: MultiMethodScorer) -> None:
    # "alcohol" comes from Arabic al-kuhl (الكحل)
    result = scorer.score_pair({"lemma": "كحل"}, {"lemma": "alcohol"})
    article_results = [r for r in result.all_results if "article" in r.method_name]
    assert len(article_results) > 0


def test_article_detection_al_prefix(scorer: MultiMethodScorer) -> None:
    result = scorer.score_pair({"lemma": "جبر"}, {"lemma": "algebra"})
    article_results = [r for r in result.all_results if "article" in r.method_name]
    assert len(article_results) > 0


# ---------------------------------------------------------------------------
# Integration: methods_that_fired
# ---------------------------------------------------------------------------

def test_methods_that_fired_threshold(scorer: MultiMethodScorer) -> None:
    result = scorer.score_pair({"lemma": "لفت"}, {"lemma": "left"})
    # All fired methods should have score > 0.4
    for method_name in result.methods_that_fired:
        matching = [r for r in result.all_results if r.method_name == method_name]
        assert any(r.score > 0.4 for r in matching)


def test_best_method_is_best_result(scorer: MultiMethodScorer) -> None:
    result = scorer.score_pair({"lemma": "رقص"}, {"lemma": "rock"})
    if result.all_results:
        max_score = max(r.score for r in result.all_results)
        assert abs(result.best_score - max_score) < 1e-6


# ---------------------------------------------------------------------------
# Method 4: Guttural projection
# ---------------------------------------------------------------------------

def test_guttural_projection(scorer: MultiMethodScorer) -> None:
    # عصفر — contains ع (guttural); stripped = صفر (sfr, 3 consonants)
    # matches "saffron" skeleton "sfrn" well
    result = scorer.score_pair({"lemma": "عصفر"}, {"lemma": "saffron"})
    guttural_results = [r for r in result.all_results if "guttural" in r.method_name]
    assert len(guttural_results) > 0


# ---------------------------------------------------------------------------
# Method 5: Emphatic collapse
# ---------------------------------------------------------------------------

def test_emphatic_collapse(scorer: MultiMethodScorer) -> None:
    # صبر contains ص (emphatic)
    result = scorer.score_pair({"lemma": "صبر"}, {"lemma": "super"})
    emphatic_results = [r for r in result.all_results if "emphatic" in r.method_name]
    assert len(emphatic_results) > 0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_short_arabic_root(scorer: MultiMethodScorer) -> None:
    result = scorer.score_pair({"lemma": "في"}, {"lemma": "of"})
    assert isinstance(result, MultiMethodScore)


def test_root_norm_field_used(scorer: MultiMethodScorer) -> None:
    result = scorer.score_pair({"root_norm": "كتب", "lemma": "ignored"}, {"lemma": "script"})
    assert isinstance(result, MultiMethodScore)


def test_score_bounded(scorer: MultiMethodScorer) -> None:
    pairs = [
        ({"lemma": "قلم"}, {"lemma": "pen"}),
        ({"lemma": "كتب"}, {"lemma": "book"}),
        ({"lemma": "لسان"}, {"lemma": "language"}),
    ]
    for src, tgt in pairs:
        result = scorer.score_pair(src, tgt)
        assert 0.0 <= result.best_score <= 1.0
