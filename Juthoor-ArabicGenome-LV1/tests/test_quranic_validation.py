from __future__ import annotations

from juthoor_arabicgenome_lv1.factory.quranic_validation import (
    quranic_accuracy_report,
    quranic_by_bab,
    split_by_quranic,
    top_quranic_predictions,
    worst_quranic_predictions,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_prediction(
    *,
    root: str = "كتب",
    is_quranic: bool = False,
    quranic_verse: str | None = None,
    jaccard: float = 0.5,
    blended_jaccard: float = 0.5,
    weighted_jaccard: float = 0.5,
    bab: str | None = None,
) -> dict:
    return {
        "root": root,
        "is_quranic": is_quranic,
        "quranic_verse": quranic_verse,
        "jaccard": jaccard,
        "blended_jaccard": blended_jaccard,
        "weighted_jaccard": weighted_jaccard,
        "bab": bab,
    }


MIXED_PREDICTIONS = [
    _make_prediction(root="كتب", is_quranic=True, jaccard=0.8, blended_jaccard=0.8, weighted_jaccard=0.8, bab="ك"),
    _make_prediction(root="قرأ", quranic_verse="2:1", jaccard=0.6, blended_jaccard=0.6, weighted_jaccard=0.6, bab="ق"),
    _make_prediction(root="علم", is_quranic=True, jaccard=0.4, blended_jaccard=0.4, weighted_jaccard=0.4, bab="ع"),
    _make_prediction(root="درس", jaccard=0.3, blended_jaccard=0.3, weighted_jaccard=0.3, bab="د"),
    _make_prediction(root="خرج", jaccard=0.0, blended_jaccard=0.0, weighted_jaccard=0.0, bab="خ"),
]


# ---------------------------------------------------------------------------
# Tests: split_by_quranic
# ---------------------------------------------------------------------------

def test_split_by_quranic_separates_correctly() -> None:
    quranic, non_quranic = split_by_quranic(MIXED_PREDICTIONS)
    assert len(quranic) == 3
    assert len(non_quranic) == 2


def test_split_by_quranic_is_quranic_flag() -> None:
    rows = [
        _make_prediction(is_quranic=True),
        _make_prediction(is_quranic=False),
    ]
    quranic, non_quranic = split_by_quranic(rows)
    assert len(quranic) == 1
    assert len(non_quranic) == 1


def test_split_by_quranic_verse_field() -> None:
    rows = [
        _make_prediction(quranic_verse="3:10"),
        _make_prediction(quranic_verse=None),
    ]
    quranic, non_quranic = split_by_quranic(rows)
    assert len(quranic) == 1
    assert len(non_quranic) == 1


def test_split_by_quranic_empty_input() -> None:
    quranic, non_quranic = split_by_quranic([])
    assert quranic == []
    assert non_quranic == []


def test_split_by_quranic_all_quranic() -> None:
    rows = [_make_prediction(is_quranic=True) for _ in range(5)]
    quranic, non_quranic = split_by_quranic(rows)
    assert len(quranic) == 5
    assert non_quranic == []


# ---------------------------------------------------------------------------
# Tests: quranic_accuracy_report
# ---------------------------------------------------------------------------

def test_quranic_accuracy_report_structure() -> None:
    report = quranic_accuracy_report(MIXED_PREDICTIONS)
    assert "quranic" in report
    assert "non_quranic" in report
    assert "delta" in report


def test_quranic_accuracy_report_required_keys() -> None:
    report = quranic_accuracy_report(MIXED_PREDICTIONS)
    for section in ("quranic", "non_quranic"):
        metrics = report[section]
        assert "count" in metrics
        assert "mean_jaccard" in metrics
        assert "mean_blended" in metrics
        assert "mean_weighted_jaccard" in metrics
        assert "nonzero_rate" in metrics
        assert "nonzero_blended_rate" in metrics


def test_quranic_accuracy_report_counts() -> None:
    report = quranic_accuracy_report(MIXED_PREDICTIONS)
    assert report["quranic"]["count"] == 3
    assert report["non_quranic"]["count"] == 2


def test_quranic_accuracy_report_delta_keys() -> None:
    report = quranic_accuracy_report(MIXED_PREDICTIONS)
    delta = report["delta"]
    assert "mean_jaccard" in delta
    assert "mean_blended" in delta
    assert "mean_weighted_jaccard" in delta
    assert "nonzero_rate" in delta


def test_quranic_accuracy_report_delta_sign() -> None:
    # Quranic rows have higher jaccard scores in MIXED_PREDICTIONS
    report = quranic_accuracy_report(MIXED_PREDICTIONS)
    assert report["delta"]["mean_jaccard"] > 0


def test_quranic_accuracy_report_empty_predictions() -> None:
    report = quranic_accuracy_report([])
    assert report["quranic"]["count"] == 0
    assert report["non_quranic"]["count"] == 0
    assert report["delta"]["mean_jaccard"] == 0.0


def test_quranic_accuracy_report_all_zero_jaccard() -> None:
    rows = [_make_prediction(is_quranic=True, jaccard=0.0, blended_jaccard=0.0, weighted_jaccard=0.0)]
    report = quranic_accuracy_report(rows)
    assert report["quranic"]["nonzero_rate"] == 0.0


def test_quranic_accuracy_report_mean_values() -> None:
    rows = [
        _make_prediction(is_quranic=True, jaccard=0.8, blended_jaccard=0.8, weighted_jaccard=0.8),
        _make_prediction(is_quranic=True, jaccard=0.4, blended_jaccard=0.4, weighted_jaccard=0.4),
    ]
    report = quranic_accuracy_report(rows)
    assert abs(report["quranic"]["mean_jaccard"] - 0.6) < 1e-5


# ---------------------------------------------------------------------------
# Tests: top_quranic_predictions
# ---------------------------------------------------------------------------

def test_top_quranic_predictions_count() -> None:
    results = top_quranic_predictions(MIXED_PREDICTIONS, n=2)
    assert len(results) == 2


def test_top_quranic_predictions_order() -> None:
    results = top_quranic_predictions(MIXED_PREDICTIONS)
    scores = [r["blended_jaccard"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_top_quranic_predictions_only_quranic() -> None:
    results = top_quranic_predictions(MIXED_PREDICTIONS)
    for row in results:
        assert row.get("is_quranic") or row.get("quranic_verse")


def test_top_quranic_predictions_n_larger_than_pool() -> None:
    results = top_quranic_predictions(MIXED_PREDICTIONS, n=100)
    assert len(results) == 3  # only 3 Quranic rows in fixture


def test_top_quranic_predictions_empty_returns_empty() -> None:
    assert top_quranic_predictions([]) == []


# ---------------------------------------------------------------------------
# Tests: worst_quranic_predictions
# ---------------------------------------------------------------------------

def test_worst_quranic_predictions_count() -> None:
    results = worst_quranic_predictions(MIXED_PREDICTIONS, n=2)
    assert len(results) == 2


def test_worst_quranic_predictions_order() -> None:
    results = worst_quranic_predictions(MIXED_PREDICTIONS)
    scores = [r["blended_jaccard"] for r in results]
    assert scores == sorted(scores)


def test_worst_quranic_predictions_only_quranic() -> None:
    results = worst_quranic_predictions(MIXED_PREDICTIONS)
    for row in results:
        assert row.get("is_quranic") or row.get("quranic_verse")


def test_worst_quranic_predictions_empty_returns_empty() -> None:
    assert worst_quranic_predictions([]) == []


def test_worst_quranic_predictions_lowest_first() -> None:
    rows = [
        _make_prediction(root="أ", is_quranic=True, blended_jaccard=0.9),
        _make_prediction(root="ب", is_quranic=True, blended_jaccard=0.1),
        _make_prediction(root="ج", is_quranic=True, blended_jaccard=0.5),
    ]
    results = worst_quranic_predictions(rows, n=1)
    assert results[0]["root"] == "ب"


# ---------------------------------------------------------------------------
# Tests: quranic_by_bab
# ---------------------------------------------------------------------------

def test_quranic_by_bab_groups_by_bab() -> None:
    result = quranic_by_bab(MIXED_PREDICTIONS)
    # Quranic roots in MIXED_PREDICTIONS have bab: ك, ق, ع
    assert "ك" in result
    assert "ق" in result
    assert "ع" in result


def test_quranic_by_bab_excludes_non_quranic() -> None:
    result = quranic_by_bab(MIXED_PREDICTIONS)
    # Non-Quranic babs are "د" and "خ"
    assert "د" not in result
    assert "خ" not in result


def test_quranic_by_bab_metrics_structure() -> None:
    result = quranic_by_bab(MIXED_PREDICTIONS)
    for bab, metrics in result.items():
        assert "count" in metrics
        assert "mean_jaccard" in metrics
        assert "mean_blended" in metrics
        assert "nonzero_rate" in metrics


def test_quranic_by_bab_count_per_bab() -> None:
    result = quranic_by_bab(MIXED_PREDICTIONS)
    # Each Quranic root has a unique bab in our fixture
    for bab in ("ك", "ق", "ع"):
        assert result[bab]["count"] == 1


def test_quranic_by_bab_empty_returns_empty() -> None:
    assert quranic_by_bab([]) == {}


def test_quranic_by_bab_excludes_rows_with_no_bab() -> None:
    rows = [_make_prediction(is_quranic=True, bab=None)]
    result = quranic_by_bab(rows)
    assert result == {}


def test_quranic_by_bab_aggregates_multiple_roots_per_bab() -> None:
    rows = [
        _make_prediction(root="كتب", is_quranic=True, jaccard=0.8, blended_jaccard=0.8, weighted_jaccard=0.8, bab="ك"),
        _make_prediction(root="كسر", is_quranic=True, jaccard=0.4, blended_jaccard=0.4, weighted_jaccard=0.4, bab="ك"),
    ]
    result = quranic_by_bab(rows)
    assert result["ك"]["count"] == 2
    assert abs(result["ك"]["mean_jaccard"] - 0.6) < 1e-5
