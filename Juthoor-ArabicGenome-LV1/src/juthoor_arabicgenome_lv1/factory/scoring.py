from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from juthoor_arabicgenome_lv1.core.feature_decomposition import (
    FEATURE_POLARITIES,
    feature_categories,
    weighted_feature_vector,
)
from juthoor_arabicgenome_lv1.factory.composition_models import COMPOSITION_MODELS, CompositionResult


@dataclass(frozen=True)
class ScoredPrediction:
    scholar: str
    model_name: str
    predicted_features: tuple[str, ...]
    actual_features: tuple[str, ...]
    jaccard: float
    weighted_jaccard: float


# ---------------------------------------------------------------------------
# S1.1 — Synonym groups for Jaccard scoring
# Features within the same group are treated as identical during scoring.
# This collapses near-synonymous Arabic terms that appear in Jabal's corpus
# and the prediction vocabulary but differ lexically.
# ---------------------------------------------------------------------------

SYNONYM_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"امتداد", "طول"}),                          # extension / length
    frozenset({"تفشي", "انتشار"}),                         # spreading / diffusion
    frozenset({"دقة", "رقة", "لطف"}),                      # fineness / delicacy
    frozenset({"تعقد", "كثافة"}),                          # density / complexity
    frozenset({"اكتناز", "تجمع"}),                         # compaction / gathering
    frozenset({"خروج", "بروز", "ظهور"}),                   # emergence / protrusion
    frozenset({"احتباس", "ضغط"}),                          # retention / pressure
    frozenset({"نفاذ", "اختراق"}),                         # passage / penetration
    frozenset({"غلظ", "كثافة", "ثخانة"}),                  # thickness / density
    frozenset({"إمساك", "امتساك"}),                        # holding / gripping
    frozenset({"التحام", "تلاصق", "تماسك"}),              # fusion / cohesion / adhesion
    frozenset({"اشتمال", "احتواء"}),                       # containment / enveloping
    frozenset({"تفرق", "تخلخل"}),                          # dispersal / loosening
    frozenset({"فراغ", "تخلخل"}),                          # void / loosening
    frozenset({"باطن", "عمق", "جوف"}),                     # inner / depth / hollow
)

# Build a canonical-form lookup: feature -> canonical (first in frozenset, sorted)
_SYNONYM_CANONICAL: dict[str, str] = {}
for _group in SYNONYM_GROUPS:
    _canon = min(_group)  # deterministic canonical form
    for _feat in _group:
        _SYNONYM_CANONICAL[_feat] = _canon


def _canonicalize(features: tuple[str, ...]) -> frozenset[str]:
    """Map each feature to its synonym-group canonical form, return as a set."""
    return frozenset(_SYNONYM_CANONICAL.get(f, f) for f in features)


# ---------------------------------------------------------------------------
# S1.3 — Semantic opposition mapping for Golden Rule scoring
# Extends FEATURE_POLARITIES with the additional pairs from the task spec.
# ---------------------------------------------------------------------------

SEMANTIC_OPPOSITES: dict[str, str] = {
    **FEATURE_POLARITIES,
    # Additional opposites not already in FEATURE_POLARITIES
    "قوة": "رخاوة",
    "رخاوة": "قوة",
    "غلظ": "رقة",
    "رقة": "غلظ",
    "امتداد": "انحسار",
    "انحسار": "امتداد",
    "نقص": "اتساع",
    "اتساع": "نقص",
}


def invert_features_extended(features: tuple[str, ...]) -> frozenset[str]:
    """Invert features using the extended SEMANTIC_OPPOSITES map."""
    return frozenset(SEMANTIC_OPPOSITES.get(f, f) for f in features)


def jaccard_similarity(predicted: tuple[str, ...], actual: tuple[str, ...]) -> float:
    p = _canonicalize(predicted)
    a = _canonicalize(actual)
    if not p and not a:
        return 1.0
    if not p or not a:
        return 0.0
    return len(p & a) / len(p | a)


def weighted_jaccard_similarity(predicted: tuple[str, ...], actual: tuple[str, ...]) -> float:
    # Canonicalize before weighting so synonym variants collapse
    pred_canon = tuple(_SYNONYM_CANONICAL.get(f, f) for f in predicted)
    actual_canon = tuple(_SYNONYM_CANONICAL.get(f, f) for f in actual)
    pred_weights = weighted_feature_vector(pred_canon)
    actual_weights = weighted_feature_vector(actual_canon)
    keys = set(pred_weights) | set(actual_weights)
    if not keys:
        return 1.0
    numerator = sum(min(pred_weights.get(key, 0.0), actual_weights.get(key, 0.0)) for key in keys)
    denominator = sum(max(pred_weights.get(key, 0.0), actual_weights.get(key, 0.0)) for key in keys)
    return numerator / denominator if denominator else 0.0


def score_prediction(
    scholar: str,
    result: CompositionResult,
    actual_features: tuple[str, ...],
) -> ScoredPrediction:
    return ScoredPrediction(
        scholar=scholar,
        model_name=result.model_name,
        predicted_features=result.predicted_features,
        actual_features=actual_features,
        jaccard=jaccard_similarity(result.predicted_features, actual_features),
        weighted_jaccard=weighted_jaccard_similarity(result.predicted_features, actual_features),
    )


def build_nucleus_score_rows(
    nucleus_rows: list[dict[str, Any]],
    scholar_letters: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    scored_rows: list[dict[str, Any]] = []
    for row in nucleus_rows:
        actual_features = tuple(row.get("jabal_features") or row.get("actual_features", ()))
        for scholar, letters in scholar_letters.items():
            if row["letter1"] not in letters or row["letter2"] not in letters:
                continue
            letter1 = letters[row["letter1"]]
            letter2 = letters[row["letter2"]]
            for model_name, model in COMPOSITION_MODELS.items():
                kwargs: dict[str, Any] = {}
                if model_name == "phonetic_gestural":
                    kwargs = {
                        "articulatory1": letter1.get("articulatory_features"),
                        "articulatory2": letter2.get("articulatory_features"),
                    }
                result = model(letter1.get("atomic_features", ()), letter2.get("atomic_features", ()), **kwargs)
                score = score_prediction(scholar, result, actual_features)
                scored_rows.append(
                    {
                        "binary_root": row["binary_root"],
                        "scholar": scholar,
                        "model": model_name,
                        "predicted_features": list(score.predicted_features),
                        "predicted_categories": list(feature_categories(score.predicted_features)),
                        "actual_features": list(actual_features),
                        "actual_categories": list(feature_categories(actual_features)),
                        "jaccard": round(score.jaccard, 6),
                        "weighted_jaccard": round(score.weighted_jaccard, 6),
                    }
                )
    return scored_rows
