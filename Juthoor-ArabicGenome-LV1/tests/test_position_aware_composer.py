from __future__ import annotations

import pytest

from juthoor_arabicgenome_lv1.factory.position_aware_composer import (
    MODIFIER_OVERRIDES,
    model_position_aware,
)


def test_override_letter_uses_modifier_profile() -> None:
    """م has an empirical override — should use (ظاهر, تجمع) as modifier features."""
    # Nucleus features that overlap with م's override (تجمع appears in both)
    nucleus = ("تجمع", "قوة")
    raw_third = ("شيء_آخر",)  # raw features that would NOT overlap
    result = model_position_aware(nucleus, raw_third, third_letter="م")
    assert result.model_name == "position_aware"
    # Expected overlap: تجمع (from nucleus ∩ override (ظاهر, تجمع))
    assert "تجمع" in result.predicted_features


def test_no_override_uses_raw_features() -> None:
    """A letter without an override (e.g. ز) uses the passed third_letter_features."""
    nucleus = ("قوة", "عمق")
    raw_third = ("قوة",)  # overlaps with nucleus
    result = model_position_aware(nucleus, raw_third, third_letter="ز")
    assert result.model_name == "position_aware"
    assert "قوة" in result.predicted_features


def test_intersection_when_overlap_exists() -> None:
    """When nucleus and modifier share a feature, intersection is returned."""
    nucleus = ("امتداد", "قوة")
    # ر has override (استرسال, امتداد) — امتداد overlaps with nucleus
    result = model_position_aware(nucleus, ("شيء",), third_letter="ر")
    assert "امتداد" in result.predicted_features
    # Result should not include features absent from both nucleus and override
    for f in result.predicted_features:
        assert f in set(nucleus) or f in set(MODIFIER_OVERRIDES["ر"])


def test_fallback_when_no_overlap() -> None:
    """When there is no feature overlap, takes top-1 from nucleus + top-1 from modifier."""
    nucleus = ("ثقل",)
    raw_third = ("تفرق",)
    # Use a letter with no override so raw_third is used directly
    result = model_position_aware(nucleus, raw_third, third_letter="ز")
    assert result.model_name == "position_aware"
    assert len(result.predicted_features) >= 1
    assert "ثقل" in result.predicted_features
    assert "تفرق" in result.predicted_features


def test_empty_third_letter_uses_raw_features() -> None:
    """When third_letter is empty string, raw third_letter_features are used."""
    nucleus = ("قوة",)
    raw_third = ("قوة",)
    result = model_position_aware(nucleus, raw_third, third_letter="")
    assert result.model_name == "position_aware"
    assert "قوة" in result.predicted_features


def test_supporting_categories_are_returned() -> None:
    """CompositionResult should always have non-empty supporting_categories when features exist."""
    nucleus = ("احتباس",)
    raw_third = ("احتباس",)
    result = model_position_aware(nucleus, raw_third, third_letter="د")
    # د override is (احتباس, إمساك) — احتباس overlaps with nucleus
    assert "احتباس" in result.predicted_features
    assert isinstance(result.supporting_categories, tuple)


def test_all_override_letters_are_covered() -> None:
    """Sanity check: all keys in MODIFIER_OVERRIDES have non-empty override tuples."""
    for letter, feats in MODIFIER_OVERRIDES.items():
        assert isinstance(feats, tuple)
        assert len(feats) > 0, f"Override for {letter} is empty"


def test_choose_model_returns_position_aware_for_override_letter() -> None:
    """choose_root_prediction_model should prefer position_aware over phonetic_gestural
    when the third letter has a modifier override and there is no semantic overlap."""
    from juthoor_arabicgenome_lv1.factory.root_predictor import choose_root_prediction_model

    # Nucleus and third-letter features have no overlap and are in different categories,
    # so without the override the model would be phonetic_gestural.
    binary = ("ثقل",)
    third_feats = ("تفرق",)
    model = choose_root_prediction_model(binary, third_feats, third_letter="م")
    assert model == "position_aware"


def test_choose_model_still_uses_phonetic_gestural_for_non_override() -> None:
    """Letters without an override still fall back to phonetic_gestural."""
    from juthoor_arabicgenome_lv1.factory.root_predictor import choose_root_prediction_model

    binary = ("ثقل",)
    third_feats = ("تفرق",)
    model = choose_root_prediction_model(binary, third_feats, third_letter="ز")
    assert model == "phonetic_gestural"
