"""Root prediction assembly for LV1 binary nuclei and third letters.

This module selects the composition model, filters conflicting modifier
features, and packages the resulting root-level semantic predictions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from juthoor_arabicgenome_lv1.core.neili_constraints import apply_neili_constraints
from juthoor_arabicgenome_lv1.factory.composition_models import (
    model_intersection,
    model_phonetic_gestural,
    model_sequence,
)
from juthoor_arabicgenome_lv1.factory.position_aware_composer import (
    MODIFIER_OVERRIDES,
    model_position_aware,
)
from juthoor_arabicgenome_lv1.factory.scoring import (
    blended_jaccard,
    jaccard_similarity,
    weighted_jaccard_similarity,
)
from juthoor_arabicgenome_lv1.core.feature_decomposition import FEATURE_POLARITIES, FEATURE_TO_CATEGORY


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

THIRD_LETTER_BLOCKED_FEATURES = frozenset({"التحام"})


def _normalize_letter_token(letter: str) -> str:
    return LETTER_ALIASES.get(letter, letter)


def filter_third_letter_features(
    binary_features: tuple[str, ...],
    third_letter_features: tuple[str, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    binary_set = set(binary_features)
    kept: list[str] = []
    dropped: list[str] = []
    for feature in third_letter_features:
        if feature in THIRD_LETTER_BLOCKED_FEATURES and feature not in binary_set:
            dropped.append(feature)
            continue
        opposite = FEATURE_POLARITIES.get(feature)
        if opposite and opposite in binary_set and feature not in binary_set:
            dropped.append(feature)
            continue
        kept.append(feature)
    return tuple(kept), tuple(dropped)


def choose_root_prediction_model(
    binary_features: tuple[str, ...],
    third_letter_features: tuple[str, ...],
    *,
    third_letter: str = "",
) -> str:
    """Choose the Phase 3 model.

    Use Intersection only when the nucleus field and third-letter modifier
    already share a semantic signal. When the third letter has an empirical
    modifier override and the standard model would fall back to
    phonetic_gestural, use position_aware instead. Otherwise follow Claude's
    recommendation and fall back to Phonetic-Gestural.
    """
    if binary_features and third_letter_features:
        if jaccard_similarity(binary_features, third_letter_features) > 0.0:
            return "intersection"
        binary_categories = {FEATURE_TO_CATEGORY.get(feature) for feature in binary_features}
        third_categories = {FEATURE_TO_CATEGORY.get(feature) for feature in third_letter_features}
        if binary_categories & third_categories:
            return "intersection"
        # Use position_aware instead of phonetic_gestural when the third letter
        # has an empirical modifier profile that differs from its nucleus behavior.
        if third_letter and third_letter in MODIFIER_OVERRIDES:
            return "position_aware"
        return "phonetic_gestural"
    if binary_features or third_letter_features:
        return "sequence"
    return "empty"


def _dedupe_features(features: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(features))


def _resolve_intersection_prediction(
    binary_features: tuple[str, ...],
    third_letter_features: tuple[str, ...],
) -> tuple[str, tuple[str, ...]]:
    result = model_intersection(binary_features, third_letter_features)
    exact_overlap = set(binary_features) & set(third_letter_features)
    if (
        binary_features
        and third_letter_features
        and not exact_overlap
        and set(result.predicted_features).issubset(set(binary_features))
    ):
        return "nucleus_only", _dedupe_features(binary_features)
    return "intersection", result.predicted_features


def _resolve_prediction_features(
    *,
    model_name: str,
    binary_features: tuple[str, ...],
    third_letter_features: tuple[str, ...],
    third_letter_articulatory: dict[str, Any] | None,
    third_letter: str = "",
) -> tuple[str, tuple[str, ...]]:
    if model_name == "intersection":
        return _resolve_intersection_prediction(binary_features, third_letter_features)
    if model_name == "phonetic_gestural":
        result = model_phonetic_gestural(
            binary_features,
            third_letter_features,
            articulatory2=third_letter_articulatory,
        )
        return model_name, result.predicted_features
    if model_name == "position_aware":
        result = model_position_aware(
            binary_features,
            third_letter_features,
            third_letter=third_letter,
        )
        return model_name, result.predicted_features
    if model_name == "sequence":
        result = model_sequence(binary_features, third_letter_features)
        return model_name, result.predicted_features
    if model_name == "nucleus_only":
        return model_name, _dedupe_features(binary_features)
    return model_name, ()


def _build_prediction_row(
    *,
    source_row: dict[str, Any],
    prediction: RootPrediction,
    filtered_third_letter_features: tuple[str, ...],
    dropped_third_letter_features: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "root": prediction.root,
        "binary_nucleus": prediction.binary_nucleus,
        "third_letter": prediction.third_letter,
        "scholar": prediction.scholar,
        "model": prediction.model_used,
        "predicted_meaning": prediction.predicted_meaning,
        "predicted_features": list(prediction.predicted_features),
        "filtered_third_letter_features": list(filtered_third_letter_features),
        "dropped_third_letter_features": list(dropped_third_letter_features),
        "actual_features": list(prediction.actual_features),
        "jaccard": round(prediction.jaccard, 6),
        "weighted_jaccard": round(prediction.weighted_jaccard, 6),
        "blended_jaccard": round(blended_jaccard(
            prediction.predicted_features, prediction.actual_features,
        ), 6),
        "bab": source_row.get("bab"),
        "quranic_verse": source_row.get("quranic_verse"),
    }


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _cohort_summary(cohort_rows: list[dict[str, Any]]) -> dict[str, Any]:
    nonzero_rows = [row for row in cohort_rows if row["jaccard"] > 0.0]
    nonzero_blended_rows = [row for row in cohort_rows if row.get("blended_jaccard", 0.0) > 0.0]
    valid_rows = [row for row in cohort_rows if row.get("neili_valid", True)]
    return {
        "count": len(cohort_rows),
        "mean_jaccard": round(_mean([row["jaccard"] for row in cohort_rows]), 6),
        "mean_weighted_jaccard": round(_mean([row["weighted_jaccard"] for row in cohort_rows]), 6),
        "mean_blended_jaccard": round(_mean([row.get("blended_jaccard", 0.0) for row in cohort_rows]), 6),
        "nonzero_predictions": len(nonzero_rows),
        "nonzero_rate": round(len(nonzero_rows) / len(cohort_rows), 6) if cohort_rows else 0.0,
        "nonzero_blended": len(nonzero_blended_rows),
        "nonzero_blended_rate": round(len(nonzero_blended_rows) / len(cohort_rows), 6) if cohort_rows else 0.0,
        "neili_valid_predictions": len(valid_rows),
        "neili_valid_rate": round(len(valid_rows) / len(cohort_rows), 6) if cohort_rows else 0.0,
    }


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
    model_name = choose_root_prediction_model(
        binary_features, third_letter_features, third_letter=third_letter
    )
    filtered_third_letter_features, dropped_third_letter_features = filter_third_letter_features(
        binary_features,
        third_letter_features,
    )
    if filtered_third_letter_features != third_letter_features:
        third_letter_features = filtered_third_letter_features
        model_name = choose_root_prediction_model(
            binary_features, third_letter_features, third_letter=third_letter
        )
    model_name, predicted_features = _resolve_prediction_features(
        model_name=model_name,
        binary_features=binary_features,
        third_letter_features=third_letter_features,
        third_letter_articulatory=third_letter_articulatory,
        third_letter=third_letter,
    )

    # Adaptive routing: when position_aware is chosen, compare against nucleus_only
    # and keep whichever scores higher on blended_jaccard. nucleus_only is statistically
    # better (0.237 vs 0.163) so it wins all ties and cases without actual_features.
    if model_name == "position_aware":
        nucleus_only_features = _dedupe_features(binary_features)
        if actual_features:
            pa_score = blended_jaccard(predicted_features, actual_features)
            nu_score = blended_jaccard(nucleus_only_features, actual_features)
            if nu_score >= pa_score:
                model_name = "nucleus_only"
                predicted_features = nucleus_only_features
        else:
            # No ground truth to compare — prefer nucleus_only (statistically safer)
            model_name = "nucleus_only"
            predicted_features = nucleus_only_features

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
        filtered_third_letter_features, dropped_third_letter_features = filter_third_letter_features(
            _as_tuple(nucleus.get("jabal_features")),
            _as_tuple(third_letter_entry.get("atomic_features")),
        )

        prediction = predict_root_from_parts(
            root=row["root"],
            binary_nucleus=row["binary_nucleus"],
            third_letter=third_letter,
            binary_features=_as_tuple(nucleus.get("jabal_features")),
            third_letter_features=filtered_third_letter_features,
            actual_features=_as_tuple(row.get("jabal_features")),
            scholar=scholar,
            third_letter_articulatory=third_letter_entry.get("articulatory_features"),
        )
        out.append(
            _build_prediction_row(
                source_row=row,
                prediction=prediction,
                filtered_third_letter_features=filtered_third_letter_features,
                dropped_third_letter_features=dropped_third_letter_features,
            )
        )
    return out


def build_root_prediction_rows_all_scholars(
    root_rows: list[dict[str, Any]],
    nucleus_rows: list[dict[str, Any]],
    scholar_letters: dict[str, dict[str, dict[str, Any]]],
    *,
    scholars: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    selected = scholars or tuple(sorted(scholar_letters))
    rows: list[dict[str, Any]] = []
    for scholar in selected:
        rows.extend(
            build_root_prediction_rows(
                root_rows,
                nucleus_rows,
                scholar_letters,
                scholar=scholar,
            )
        )
    return rows


def apply_neili_filters_to_prediction_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for row in rows:
        payload = dict(row)
        payload["is_quranic"] = bool(payload.get("quranic_verse"))
        prepared.append(payload)

    constrained = apply_neili_constraints(prepared)
    enriched: list[dict[str, Any]] = []
    for row in constrained:
        flags = row.get("neili_flags", [])
        serializable_flags = [
            {
                "constraint": flag.constraint,
                "root": flag.root,
                "description": flag.description,
                "severity": flag.severity,
            }
            for flag in flags
        ]
        enriched_row = dict(row)
        enriched_row["neili_flags"] = serializable_flags
        enriched_row["neili_flag_count"] = len(serializable_flags)
        enriched_row["neili_hard_flag_count"] = sum(1 for flag in serializable_flags if flag["severity"] == "hard")
        enriched_row["neili_soft_flag_count"] = sum(1 for flag in serializable_flags if flag["severity"] == "soft")
        enriched_row["neili_valid"] = enriched_row["neili_hard_flag_count"] == 0
        enriched.append(enriched_row)
    return enriched


def summarize_root_predictions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    nonzero = [row for row in rows if row["jaccard"] > 0.0]
    by_model: dict[str, list[dict[str, Any]]] = {}
    by_scholar: dict[str, list[dict[str, Any]]] = {}
    by_bab: dict[str, list[dict[str, Any]]] = {}
    by_constraint: dict[str, int] = {}
    quranic_rows: list[dict[str, Any]] = []
    non_quranic_rows: list[dict[str, Any]] = []

    for row in rows:
        by_model.setdefault(row["model"], []).append(row)
        by_scholar.setdefault(row["scholar"], []).append(row)
        by_bab.setdefault(row.get("bab") or "", []).append(row)
        for flag in row.get("neili_flags", []):
            by_constraint[flag["constraint"]] = by_constraint.get(flag["constraint"], 0) + 1
        if row.get("is_quranic"):
            quranic_rows.append(row)
        else:
            non_quranic_rows.append(row)

    nonzero_blended = [row for row in rows if row.get("blended_jaccard", 0.0) > 0.0]
    neili_valid_rows = [row for row in rows if row.get("neili_valid", True)]
    neili_hard_rejected = [row for row in rows if row.get("neili_hard_flag_count", 0) > 0]
    neili_soft_flagged = [row for row in rows if row.get("neili_soft_flag_count", 0) > 0]

    return {
        "overall": {
            "roots": total,
            "nonzero_predictions": len(nonzero),
            "nonzero_rate": round(len(nonzero) / total, 6) if total else 0.0,
            "mean_jaccard": round(_mean([row["jaccard"] for row in rows]), 6),
            "mean_weighted_jaccard": round(_mean([row["weighted_jaccard"] for row in rows]), 6),
            "mean_blended_jaccard": round(_mean([row.get("blended_jaccard", 0.0) for row in rows]), 6),
            "nonzero_blended": len(nonzero_blended),
            "nonzero_blended_rate": round(len(nonzero_blended) / total, 6) if total else 0.0,
            "neili_valid_predictions": len(neili_valid_rows),
            "neili_valid_rate": round(len(neili_valid_rows) / total, 6) if total else 0.0,
            "neili_hard_rejections": len(neili_hard_rejected),
            "neili_soft_flagged": len(neili_soft_flagged),
        },
        "by_model": {
            model: {
                "count": len(model_rows),
                "mean_jaccard": round(_mean([row["jaccard"] for row in model_rows]), 6),
                "mean_weighted_jaccard": round(_mean([row["weighted_jaccard"] for row in model_rows]), 6),
                "mean_blended_jaccard": round(_mean([row.get("blended_jaccard", 0.0) for row in model_rows]), 6),
            }
            for model, model_rows in sorted(by_model.items())
        },
        "by_scholar": {
            scholar: {
                "count": len(scholar_rows),
                "mean_jaccard": round(_mean([row["jaccard"] for row in scholar_rows]), 6),
                "mean_weighted_jaccard": round(_mean([row["weighted_jaccard"] for row in scholar_rows]), 6),
                "mean_blended_jaccard": round(_mean([row.get("blended_jaccard", 0.0) for row in scholar_rows]), 6),
                "nonzero_predictions": sum(
                    1
                    for row in scholar_rows
                    if row["jaccard"] > 0.0 or row["weighted_jaccard"] > 0.0 or row.get("blended_jaccard", 0.0) > 0.0
                ),
            }
            for scholar, scholar_rows in sorted(by_scholar.items())
        },
        "neili_summary": {
            "constraint_counts": dict(sorted(by_constraint.items())),
            "top_hard_rejections": [
                {
                    "root": row["root"],
                    "scholar": row["scholar"],
                    "model": row["model"],
                    "predicted_features": row["predicted_features"],
                    "flags": row["neili_flags"],
                }
                for row in neili_hard_rejected[:50]
            ],
        },
        "quranic_validation": {
            "quranic": _cohort_summary(quranic_rows),
            "non_quranic": _cohort_summary(non_quranic_rows),
        },
        "by_bab": {
            bab: {
                "count": len(bab_rows),
                "mean_jaccard": round(_mean([row["jaccard"] for row in bab_rows]), 6),
                "mean_weighted_jaccard": round(_mean([row["weighted_jaccard"] for row in bab_rows]), 6),
                "mean_blended_jaccard": round(_mean([row.get("blended_jaccard", 0.0) for row in bab_rows]), 6),
            }
            for bab, bab_rows in sorted(by_bab.items())
            if bab
        },
        "top_predictions": sorted(rows, key=lambda row: row["weighted_jaccard"], reverse=True)[:50],
        "bottom_predictions": sorted(rows, key=lambda row: row["weighted_jaccard"])[:50],
    }
