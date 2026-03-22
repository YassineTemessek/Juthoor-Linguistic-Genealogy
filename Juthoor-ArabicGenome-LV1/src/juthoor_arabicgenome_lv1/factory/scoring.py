from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from juthoor_arabicgenome_lv1.core.feature_decomposition import (
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


def jaccard_similarity(predicted: tuple[str, ...], actual: tuple[str, ...]) -> float:
    p = set(predicted)
    a = set(actual)
    if not p and not a:
        return 1.0
    if not p or not a:
        return 0.0
    return len(p & a) / len(p | a)


def weighted_jaccard_similarity(predicted: tuple[str, ...], actual: tuple[str, ...]) -> float:
    pred_weights = weighted_feature_vector(predicted)
    actual_weights = weighted_feature_vector(actual)
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
