"""
Tests for build_dashboard.build_dashboard().
"""

import sys
from pathlib import Path

# Ensure the script directory is importable without installing a package
_COMMON = (
    Path(__file__).resolve().parents[1]
    / "scripts" / "research_factory" / "common"
)
if str(_COMMON) not in sys.path:
    sys.path.insert(0, str(_COMMON))

from build_dashboard import build_dashboard


def test_dashboard_top_level_keys():
    dashboard = build_dashboard()
    assert "hypotheses" in dashboard
    assert "summary" in dashboard
    assert "generated" in dashboard
    assert "total_experiments_run" in dashboard


def test_twelve_hypotheses():
    dashboard = build_dashboard()
    assert len(dashboard["hypotheses"]) == 12


def test_summary_counts_add_to_twelve():
    dashboard = build_dashboard()
    total = sum(dashboard["summary"].values())
    assert total == 12, f"Summary counts sum to {total}, expected 12"


def test_experiments_with_result_files_have_metrics():
    """Any experiment that has a *_result.json on disk must have metrics != None."""
    dashboard = build_dashboard()
    for hyp in dashboard["hypotheses"]:
        for exp in hyp["experiments"]:
            if exp["status"] == "completed":
                assert exp["metrics"] is not None, (
                    f"Experiment {exp['id']} is completed but metrics is None"
                )


def test_hypothesis_ids_are_strings():
    dashboard = build_dashboard()
    for hyp in dashboard["hypotheses"]:
        assert isinstance(hyp["id"], str)
        assert hyp["id"].startswith("H")


def test_pending_experiments_have_no_metrics():
    """Experiments with no result file should be marked pending with metrics=None."""
    dashboard = build_dashboard()
    for hyp in dashboard["hypotheses"]:
        for exp in hyp["experiments"]:
            if exp["status"] == "pending":
                assert exp["metrics"] is None, (
                    f"Pending experiment {exp['id']} unexpectedly has metrics"
                )
