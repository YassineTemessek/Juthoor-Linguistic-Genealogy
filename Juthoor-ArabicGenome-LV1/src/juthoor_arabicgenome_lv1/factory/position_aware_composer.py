"""Position-aware composition model for trilateral root prediction.

Uses empirically derived modifier profiles: when a letter serves as the
third letter in a root, it may contribute different features than when it
appears in a binary nucleus. This model respects that positional difference.
"""
from __future__ import annotations

from typing import Any

from juthoor_arabicgenome_lv1.factory.composition_models import (
    CompositionResult,
    _as_features,
    _categories,
    _ordered_unique,
)


# Empirical modifier overrides — letters whose modifier behavior differs from nucleus behavior
# Derived from THIRD_LETTER_MODIFIER_PROFILES analysis
MODIFIER_OVERRIDES: dict[str, tuple[str, ...]] = {
    "م": ("ظاهر", "تجمع"),          # surfaces/manifests as modifier, not just gathering
    "ر": ("استرسال", "امتداد"),      # flow/extension as modifier
    "ب": ("ظهور", "تجمع"),          # emergence as modifier
    "ع": ("ظهور", "عمق", "قوة"),   # manifestation+depth+force as modifier
    "ق": ("عمق", "قوة"),            # depth+force as modifier
    "ن": ("نفاذ", "امتداد"),        # penetration+extension as modifier
    "ل": ("تعلق", "امتداد"),        # attachment+extension as modifier
    "د": ("احتباس", "إمساك"),       # retention+holding as modifier
    "ف": ("تفرق", "إبعاد"),         # separation+distancing as modifier
    "ح": ("اتساع", "خلوص"),         # expansion+purity as modifier
}


def model_position_aware(
    nucleus_features: str | tuple[str, ...],
    third_letter_features: str | tuple[str, ...],
    *,
    third_letter: str = "",
    **kwargs: Any,
) -> CompositionResult:
    """Position-aware composition: uses modifier overrides for the third letter.

    If the third letter has an empirical modifier override, use that instead
    of its raw atomic_features. Otherwise fall back to standard intersection logic.
    """
    nuc = _as_features(nucleus_features)

    # Use modifier override if available, otherwise use raw features
    if third_letter and third_letter in MODIFIER_OVERRIDES:
        mod = MODIFIER_OVERRIDES[third_letter]
    else:
        mod = _as_features(third_letter_features)

    # Intersection: find overlap between nucleus and modifier
    overlap = [f for f in nuc if f in set(mod)]
    if overlap:
        features = _ordered_unique(overlap)
    else:
        # No overlap — take top 1 from nucleus + top 1 from modifier
        features = _ordered_unique(list(nuc[:1]) + list(mod[:1]))

    return CompositionResult("position_aware", features, _categories(features))
