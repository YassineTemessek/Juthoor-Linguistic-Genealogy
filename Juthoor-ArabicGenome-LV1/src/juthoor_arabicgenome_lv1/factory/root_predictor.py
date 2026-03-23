from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from juthoor_arabicgenome_lv1.factory.composition_models import (
    model_intersection,
    model_phonetic_gestural,
    model_sequence,
)
from juthoor_arabicgenome_lv1.factory.scoring import (
    jaccard_similarity,
    weighted_jaccard_similarity,
)
from juthoor_arabicgenome_lv1.core.feature_decomposition import FEATURE_TO_CATEGORY


@dataclass(frozen=True)
class RootPrediction:
    root: str
    binary_nucleus: str
    third_letter: str
    model_used: str
    scholar: str
    predicted_features: tuple[str, ...]
    actual_features: tuple[str, ...]
    jaccard: float
    weighted_jaccard: float
    predicted_meaning: str | None


def _as_tuple(value: Any) -> tuple[str, ...]:
    if not value:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(str(item) for item in value if item)
    return (str(value),)


def _features_to_gloss(features: tuple[str, ...]) -> str | None:
    if not features:
        return None
    return " + ".join(features)


LETTER_ALIASES = {
    "أ": "ء",
    "إ": "ء",
    "آ": "ء",
    "ى": "ي",
    "ه": "هـ",
}


def _normalize_letter_token(letter: str) -> str:
    return LETTER_ALIASES.get(letter, letter)


def choose_root_prediction_model(
    binary_features: tuple[str, ...],
    third_letter_features: tuple[str, ...],
) -> str:
    """Choose the Phase 3 model.

    Use Intersection only when the nucleus field and third-letter modifier
    already share a semantic signal. Otherwise follow Claude's recommendation
    and fall back to Phonetic-Gestural rather than forcing a fake overlap.
    """
    if binary_features and third_letter_features:
        if jaccard_similarity(binary_features, third_letter_features) > 0.0:
            return "intersection"
        binary_categories = {FEATURE_TO_CATEGORY.get(feature) for feature in binary_features}
        third_categories = {FEATURE_TO_CATEGORY.get(feature) for feature in third_letter_features}
        if binary_categories & third_categories:
            return "intersection"
        return "phonetic_gestural"
    if binary_features or third_letter_features:
        return "sequence"
    return "empty"


def predict_root_from_parts(
    *,
    root: str,
    binary_nucleus: str,
    third_letter: str,
    binary_features: tuple[str, ...],
    third_letter_features: tuple[str, ...],
    actual_features: tuple[str, ...] = (),
    scholar: str = "jabal",
    third_letter_articulatory: dict[str, Any] | None = None,
) -> RootPrediction:
    model_name = choose_root_prediction_model(binary_features, third_letter_features)
    predicted_features: tuple[str, ...]

    if model_name == "intersection":
        result = model_intersection(binary_features, third_letter_features)
        predicted_features = result.predicted_features
    elif model_name == "phonetic_gestural":
        result = model_phonetic_gestural(
            binary_features,
            third_letter_features,
            articulatory2=third_letter_articulatory,
        )
        predicted_features = result.predicted_features
    elif model_name == "sequence":
        result = model_sequence(binary_features, third_letter_features)
        predicted_features = result.predicted_features
    else:
        predicted_features = ()

    return RootPrediction(
        root=root,
        binary_nucleus=binary_nucleus,
        third_letter=third_letter,
        model_used=model_name,
        scholar=scholar,
        predicted_features=predicted_features,
        actual_features=actual_features,
        jaccard=jaccard_similarity(predicted_features, actual_features),
        weighted_jaccard=weighted_jaccard_similarity(predicted_features, actual_features),
        predicted_meaning=_features_to_gloss(predicted_features),
    )


def build_root_prediction_rows(
    root_rows: list[dict[str, Any]],
    nucleus_rows: list[dict[str, Any]],
    scholar_letters: dict[str, dict[str, dict[str, Any]]],
    *,
    scholar: str = "jabal",
) -> list[dict[str, Any]]:
    nucleus_map = {row["binary_root"]: row for row in nucleus_rows}
    letters = scholar_letters.get(scholar, {})
    out: list[dict[str, Any]] = []

    for row in root_rows:
        nucleus = nucleus_map.get(row["binary_nucleus"], {})
        third_letter = _normalize_letter_token(row["third_letter"])
        third_letter_entry = letters.get(third_letter, {})

        prediction = predict_root_from_parts(
            root=row["root"],
            binary_nucleus=row["binary_nucleus"],
            third_letter=third_letter,
            binary_features=_as_tuple(nucleus.get("jabal_features")),
            third_letter_features=_as_tuple(third_letter_entry.get("atomic_features")),
            actual_features=_as_tuple(row.get("jabal_features")),
            scholar=scholar,
            third_letter_articulatory=third_letter_entry.get("articulatory_features"),
        )

        out.append(
            {
                "root": prediction.root,
                "binary_nucleus": prediction.binary_nucleus,
                "third_letter": prediction.third_letter,
                "scholar": prediction.scholar,
                "model": prediction.model_used,
                "predicted_meaning": prediction.predicted_meaning,
                "predicted_features": list(prediction.predicted_features),
                "actual_features": list(prediction.actual_features),
                "jaccard": round(prediction.jaccard, 6),
                "weighted_jaccard": round(prediction.weighted_jaccard, 6),
                "bab": row.get("bab"),
                "quranic_verse": row.get("quranic_verse"),
            }
        )
    return out


def summarize_root_predictions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    nonzero = [row for row in rows if row["jaccard"] > 0.0]
    by_model: dict[str, list[dict[str, Any]]] = {}
    by_bab: dict[str, list[dict[str, Any]]] = {}

    for row in rows:
        by_model.setdefault(row["model"], []).append(row)
        by_bab.setdefault(row.get("bab") or "", []).append(row)

    def _mean(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    return {
        "overall": {
            "roots": total,
            "nonzero_predictions": len(nonzero),
            "nonzero_rate": round(len(nonzero) / total, 6) if total else 0.0,
            "mean_jaccard": round(_mean([row["jaccard"] for row in rows]), 6),
            "mean_weighted_jaccard": round(_mean([row["weighted_jaccard"] for row in rows]), 6),
        },
        "by_model": {
            model: {
                "count": len(model_rows),
                "mean_jaccard": round(_mean([row["jaccard"] for row in model_rows]), 6),
                "mean_weighted_jaccard": round(_mean([row["weighted_jaccard"] for row in model_rows]), 6),
            }
            for model, model_rows in sorted(by_model.items())
        },
        "by_bab": {
            bab: {
                "count": len(bab_rows),
                "mean_jaccard": round(_mean([row["jaccard"] for row in bab_rows]), 6),
                "mean_weighted_jaccard": round(_mean([row["weighted_jaccard"] for row in bab_rows]), 6),
            }
            for bab, bab_rows in sorted(by_bab.items())
            if bab
        },
        "top_predictions": sorted(rows, key=lambda row: row["weighted_jaccard"], reverse=True)[:50],
        "bottom_predictions": sorted(rows, key=lambda row: row["weighted_jaccard"])[:50],
    }
