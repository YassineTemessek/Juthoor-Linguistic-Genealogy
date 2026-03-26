"""Quranic validation for LV1 root predictions.

Separates prediction accuracy for Quranic roots (كلام الخالق — purest Arabic)
vs non-Quranic roots. The Quran is the gold standard for Arabic genome validation.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def split_by_quranic(
    predictions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split predictions into Quranic and non-Quranic lists."""
    quranic = [p for p in predictions if p.get("is_quranic") or p.get("quranic_verse")]
    non_quranic = [p for p in predictions if not p.get("is_quranic") and not p.get("quranic_verse")]
    return quranic, non_quranic


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _cohort_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute standard accuracy metrics for a cohort of prediction rows."""
    count = len(rows)
    if count == 0:
        return {
            "count": 0,
            "mean_jaccard": 0.0,
            "mean_blended": 0.0,
            "mean_weighted_jaccard": 0.0,
            "nonzero_rate": 0.0,
            "nonzero_blended_rate": 0.0,
        }

    jaccards = [row.get("jaccard", 0.0) for row in rows]
    blended = [row.get("blended_jaccard", 0.0) for row in rows]
    weighted = [row.get("weighted_jaccard", 0.0) for row in rows]
    nonzero = sum(1 for j in jaccards if j > 0.0)
    nonzero_blended = sum(1 for b in blended if b > 0.0)

    return {
        "count": count,
        "mean_jaccard": round(_mean(jaccards), 6),
        "mean_blended": round(_mean(blended), 6),
        "mean_weighted_jaccard": round(_mean(weighted), 6),
        "nonzero_rate": round(nonzero / count, 6),
        "nonzero_blended_rate": round(nonzero_blended / count, 6),
    }


def quranic_accuracy_report(
    predictions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate accuracy metrics split by Quranic vs non-Quranic.

    Returns dict with:
    - quranic: {count, mean_jaccard, mean_blended, nonzero_rate, ...}
    - non_quranic: {count, mean_jaccard, mean_blended, nonzero_rate, ...}
    - delta: difference between the two (positive = Quranic is better)
    """
    quranic, non_quranic = split_by_quranic(predictions)
    q_metrics = _cohort_metrics(quranic)
    nq_metrics = _cohort_metrics(non_quranic)

    delta: dict[str, float] = {}
    for key in ("mean_jaccard", "mean_blended", "mean_weighted_jaccard", "nonzero_rate", "nonzero_blended_rate"):
        delta[key] = round(q_metrics[key] - nq_metrics[key], 6)

    return {
        "quranic": q_metrics,
        "non_quranic": nq_metrics,
        "delta": delta,
    }


def top_quranic_predictions(
    predictions: list[dict[str, Any]],
    *,
    n: int = 50,
) -> list[dict[str, Any]]:
    """Return the top N best Quranic root predictions by blended_jaccard."""
    quranic, _ = split_by_quranic(predictions)
    return sorted(quranic, key=lambda p: p.get("blended_jaccard", 0.0), reverse=True)[:n]


def worst_quranic_predictions(
    predictions: list[dict[str, Any]],
    *,
    n: int = 50,
) -> list[dict[str, Any]]:
    """Return the N worst Quranic root predictions (J=0 with most roots)."""
    quranic, _ = split_by_quranic(predictions)
    return sorted(quranic, key=lambda p: p.get("blended_jaccard", 0.0))[:n]


def quranic_by_bab(
    predictions: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Break down Quranic accuracy by BAB (letter chapter)."""
    quranic, _ = split_by_quranic(predictions)

    by_bab: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in quranic:
        bab = row.get("bab") or ""
        if bab:
            by_bab[bab].append(row)

    return {
        bab: _cohort_metrics(rows)
        for bab, rows in sorted(by_bab.items())
    }
