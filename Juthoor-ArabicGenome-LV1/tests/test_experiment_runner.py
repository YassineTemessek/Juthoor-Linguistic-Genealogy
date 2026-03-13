"""Tests for experiment_runner.py."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from juthoor_arabicgenome_lv1.factory.experiment_runner import (
    ExperimentConfig,
    MissingFeatureError,
    run_experiment,
)
from juthoor_arabicgenome_lv1.factory.feature_store import save_feature


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(tmp_path: Path, **overrides) -> ExperimentConfig:
    """Return a minimal ExperimentConfig wired to tmp_path directories."""
    features_dir = tmp_path / "features"
    reports_dir = tmp_path / "reports"
    hyp_path = tmp_path / "hypothesis_status.json"

    defaults = dict(
        id="0.1",
        name="test_exp",
        hypotheses=["H1"],
        required_features=[],
        run_fn=lambda: {"score": 0.9},
        features_dir=features_dir,
        reports_dir=reports_dir,
        hypothesis_status_path=hyp_path,
    )
    defaults.update(overrides)
    return ExperimentConfig(**defaults)


def _seed_feature(tmp_path: Path, name: str) -> None:
    """Write a tiny feature array so feature_exists() returns True."""
    features_dir = tmp_path / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    save_feature(name, np.array([1.0, 2.0]), {"model_used": "test"}, features_dir=features_dir)


# ---------------------------------------------------------------------------
# Test: successful experiment
# ---------------------------------------------------------------------------

def test_successful_experiment_writes_result(tmp_path: Path) -> None:
    config = _make_config(tmp_path, run_fn=lambda: {"accuracy": 0.95, "count": 42})
    result = run_experiment(config)

    # Return value
    assert result["status"] == "completed"
    assert result["experiment_id"] == "0.1"
    assert result["experiment_name"] == "test_exp"
    assert result["metrics"] == {"accuracy": 0.95, "count": 42}
    assert result["error"] is None
    assert result["duration_seconds"] >= 0.0

    # File written
    result_file = tmp_path / "reports" / "0.1_result.json"
    assert result_file.exists()
    on_disk = json.loads(result_file.read_text(encoding="utf-8"))
    assert on_disk["status"] == "completed"
    assert on_disk["metrics"]["accuracy"] == 0.95
    assert on_disk["error"] is None


def test_result_json_has_all_required_keys(tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    run_experiment(config)
    on_disk = json.loads((tmp_path / "reports" / "0.1_result.json").read_text(encoding="utf-8"))
    for key in ("experiment_id", "experiment_name", "status", "start_time",
                "end_time", "duration_seconds", "metrics", "error"):
        assert key in on_disk, f"Missing key in result JSON: {key}"


# ---------------------------------------------------------------------------
# Test: failed experiment
# ---------------------------------------------------------------------------

def test_failed_experiment_records_error(tmp_path: Path) -> None:
    def boom() -> dict:
        raise ValueError("something went wrong")

    config = _make_config(tmp_path, run_fn=boom)
    result = run_experiment(config)

    assert result["status"] == "failed"
    assert "ValueError" in result["error"]
    assert "something went wrong" in result["error"]
    assert result["metrics"] == {}

    # File still written
    result_file = tmp_path / "reports" / "0.1_result.json"
    assert result_file.exists()
    on_disk = json.loads(result_file.read_text(encoding="utf-8"))
    assert on_disk["status"] == "failed"
    assert on_disk["error"] is not None


# ---------------------------------------------------------------------------
# Test: missing feature check
# ---------------------------------------------------------------------------

def test_missing_feature_raises_before_running(tmp_path: Path) -> None:
    called = []

    def run_fn() -> dict:
        called.append(True)
        return {}

    config = _make_config(
        tmp_path,
        required_features=["embeddings_v1", "embeddings_v2"],
        run_fn=run_fn,
    )

    with pytest.raises(MissingFeatureError) as exc_info:
        run_experiment(config)

    assert "embeddings_v1" in str(exc_info.value)
    assert called == [], "run_fn should not be called when features are missing"


def test_present_feature_does_not_raise(tmp_path: Path) -> None:
    _seed_feature(tmp_path, "my_feature")
    config = _make_config(tmp_path, required_features=["my_feature"])
    result = run_experiment(config)
    assert result["status"] == "completed"


def test_partially_missing_feature_raises(tmp_path: Path) -> None:
    _seed_feature(tmp_path, "feat_a")
    config = _make_config(tmp_path, required_features=["feat_a", "feat_b"])
    with pytest.raises(MissingFeatureError) as exc_info:
        run_experiment(config)
    # Only feat_b is missing
    assert "feat_b" in str(exc_info.value)
    assert "feat_a" not in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test: hypothesis status update
# ---------------------------------------------------------------------------

def test_hypothesis_status_created_on_first_run(tmp_path: Path) -> None:
    config = _make_config(tmp_path, hypotheses=["H3"])
    run_experiment(config)

    hyp_file = tmp_path / "hypothesis_status.json"
    assert hyp_file.exists()
    data = json.loads(hyp_file.read_text(encoding="utf-8"))
    assert "H3" in data
    assert data["H3"]["last_experiment_id"] == "0.1"
    assert data["H3"]["last_experiment_name"] == "test_exp"
    assert data["H3"]["last_run_status"] == "completed"


def test_hypothesis_status_multiple_hypotheses(tmp_path: Path) -> None:
    config = _make_config(tmp_path, id="4.1", hypotheses=["H4", "H5"])
    run_experiment(config)

    data = json.loads((tmp_path / "hypothesis_status.json").read_text(encoding="utf-8"))
    assert "H4" in data
    assert "H5" in data
    assert data["H4"]["last_experiment_id"] == "4.1"
    assert data["H5"]["last_experiment_id"] == "4.1"


def test_hypothesis_status_preserves_existing_entries(tmp_path: Path) -> None:
    # First experiment touches H1
    config1 = _make_config(tmp_path, id="1.1", name="first", hypotheses=["H1"])
    run_experiment(config1)

    # Second experiment touches H2 — H1 entry must survive
    config2 = _make_config(tmp_path, id="2.1", name="second", hypotheses=["H2"])
    run_experiment(config2)

    data = json.loads((tmp_path / "hypothesis_status.json").read_text(encoding="utf-8"))
    assert "H1" in data
    assert "H2" in data
    assert data["H1"]["last_experiment_id"] == "1.1"
    assert data["H2"]["last_experiment_id"] == "2.1"


def test_hypothesis_status_updated_on_failed_run(tmp_path: Path) -> None:
    config = _make_config(tmp_path, hypotheses=["H3"], run_fn=lambda: (_ for _ in ()).throw(RuntimeError("oops")))
    run_experiment(config)

    data = json.loads((tmp_path / "hypothesis_status.json").read_text(encoding="utf-8"))
    assert data["H3"]["last_run_status"] == "failed"
