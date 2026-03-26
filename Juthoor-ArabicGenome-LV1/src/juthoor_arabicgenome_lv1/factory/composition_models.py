from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from juthoor_arabicgenome_lv1.core.feature_decomposition import (
    FEATURE_TO_CATEGORY,
    decompose_semantic_text,
    invert_features,
)


@dataclass(frozen=True)
class CompositionResult:
    model_name: str
    predicted_features: tuple[str, ...]
    supporting_categories: tuple[str, ...]


def _ordered_unique(items: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item for item in items if item))


def _categories(features: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(FEATURE_TO_CATEGORY.get(feature, "unknown") for feature in features))


def _as_features(value: str | tuple[str, ...] | list[str]) -> tuple[str, ...]:
    if isinstance(value, str):
        return decompose_semantic_text(value)
    return tuple(value)


def model_intersection(letter1: str | tuple[str, ...], letter2: str | tuple[str, ...]) -> CompositionResult:
    f1 = _as_features(letter1)
    f2 = _as_features(letter2)
    overlap = [feature for feature in f1 if feature in set(f2)]
    if not overlap:
        cats2 = {FEATURE_TO_CATEGORY.get(feature) for feature in f2}
        overlap = [feature for feature in f1 if FEATURE_TO_CATEGORY.get(feature) in cats2]
    features = _ordered_unique(overlap or list(f1[:1] + f2[:1]))
    return CompositionResult("intersection", features, _categories(features))


def model_sequence(letter1: str | tuple[str, ...], letter2: str | tuple[str, ...]) -> CompositionResult:
    f1 = _as_features(letter1)
    f2 = _as_features(letter2)
    features = _ordered_unique(list(f1[:2]) + list(f2[:2]))
    return CompositionResult("sequence", features, _categories(features))


def model_dialectical(letter1: str | tuple[str, ...], letter2: str | tuple[str, ...]) -> CompositionResult:
    f1 = _as_features(letter1)
    f2 = _as_features(letter2)
    inverse2 = set(invert_features(f2))
    synthesis = [feature for feature in f1 if feature not in inverse2]
    synthesis.extend(feature for feature in f2 if feature not in set(invert_features(f1)))
    if not synthesis:
        synthesis = list(f1[:1] + invert_features(f2[:1]))
    features = _ordered_unique(synthesis)
    return CompositionResult("dialectical", features, _categories(features))


def model_phonetic_gestural(
    letter1: str | tuple[str, ...],
    letter2: str | tuple[str, ...],
    *,
    articulatory1: dict[str, Any] | None = None,
    articulatory2: dict[str, Any] | None = None,
) -> CompositionResult:
    del articulatory1, articulatory2
    # S3.14 — Precision-capped semantic fallback.
    # Take up to 2 features from the nucleus (letter1, dominant) and up to 1
    # from the modifier (letter2). This avoids the over-prediction problem
    # where concatenating all features from both sides (4-7 total) floods the
    # output with noise and tanks Jaccard precision.
    f1 = _as_features(letter1)
    f2 = _as_features(letter2)
    combined = list(f1[:2]) + list(f2[:1])
    ordered = _ordered_unique(combined)
    return CompositionResult("phonetic_gestural", ordered, _categories(ordered))


from juthoor_arabicgenome_lv1.factory.position_aware_composer import model_position_aware  # noqa: E402

COMPOSITION_MODELS = {
    "intersection": model_intersection,
    "sequence": model_sequence,
    "dialectical": model_dialectical,
    "phonetic_gestural": model_phonetic_gestural,
    "position_aware": model_position_aware,
}
