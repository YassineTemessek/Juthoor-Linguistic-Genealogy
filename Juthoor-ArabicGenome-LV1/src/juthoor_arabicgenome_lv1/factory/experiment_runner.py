"""Lightweight experiment runner for the Juthoor research factory.

Wraps a callable experiment with feature-gate checks, timing, result logging,
and hypothesis status tracking.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .feature_store import feature_exists

# LV1 root: factory/experiment_runner.py -> factory/ -> juthoor_arabicgenome_lv1/ -> src/ -> LV1 root
_LV1_ROOT = Path(__file__).resolve().parents[4]
_REPORTS_DIR = _LV1_ROOT / "outputs" / "research_factory" / "reports"
_HYPOTHESIS_STATUS_PATH = _LV1_ROOT / "outputs" / "research_factory" / "hypothesis_status.json"


@dataclass
class ExperimentConfig:
    """Configuration for a single experiment run.

    Fields:
        id: Experiment identifier (e.g. "3.1").
        name: Human-readable experiment name (e.g. "modifier_personality").
        hypotheses: List of hypothesis IDs this experiment touches (e.g. ["H3"]).
        required_features: Feature names that must exist in the feature store
            before this experiment can run.
        run_fn: Callable that performs the actual work. Must return a dict of
            metrics (any JSON-serialisable values).
        features_dir: Override feature store directory (used in tests).
        reports_dir: Override reports output directory (used in tests).
        hypothesis_status_path: Override hypothesis_status.json path (used in tests).
    """
    id: str
    name: str
    hypotheses: list[str]
    required_features: list[str]
    run_fn: Callable[[], dict[str, Any]]
    features_dir: Path | None = field(default=None, repr=False)
    reports_dir: Path | None = field(default=None, repr=False)
    hypothesis_status_path: Path | None = field(default=None, repr=False)


def run_experiment(config: ExperimentConfig) -> dict[str, Any]:
    """Run an experiment, log results, and update hypothesis status.

    Args:
        config: Experiment configuration including the callable to run.

    Returns:
        The result dict written to disk (includes status, metrics, timing).

    Raises:
        MissingFeatureError: If any required feature is absent from the store.
    """
    # --- resolve output paths ---
    reports_dir = config.reports_dir if config.reports_dir is not None else _REPORTS_DIR
    hypothesis_status_path = (
        config.hypothesis_status_path
        if config.hypothesis_status_path is not None
        else _HYPOTHESIS_STATUS_PATH
    )
    reports_dir.mkdir(parents=True, exist_ok=True)
    hypothesis_status_path.parent.mkdir(parents=True, exist_ok=True)

    # --- feature gate ---
    missing = [
        feat
        for feat in config.required_features
        if not feature_exists(feat, features_dir=config.features_dir)
    ]
    if missing:
        raise MissingFeatureError(
            f"Experiment '{config.id}' ({config.name}) cannot run -- "
            f"missing features in store: {missing}"
        )

    # --- run ---
    start_dt = datetime.now(timezone.utc)
    start_iso = start_dt.isoformat()
    metrics: dict[str, Any] = {}
    error_msg: str | None = None
    status = "completed"

    try:
        metrics = config.run_fn()
        if not isinstance(metrics, dict):
            metrics = {"result": metrics}
    except Exception as exc:  # noqa: BLE001
        status = "failed"
        error_msg = f"{type(exc).__name__}: {exc}"

    end_dt = datetime.now(timezone.utc)
    end_iso = end_dt.isoformat()
    duration = (end_dt - start_dt).total_seconds()

    # --- build result ---
    result: dict[str, Any] = {
        "experiment_id": config.id,
        "experiment_name": config.name,
        "status": status,
        "start_time": start_iso,
        "end_time": end_iso,
        "duration_seconds": duration,
        "metrics": metrics,
        "error": error_msg,
    }

    # --- write result JSON ---
    result_path = reports_dir / f"{config.id}_result.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # --- update hypothesis status ---
    _update_hypothesis_status(
        hypothesis_status_path=hypothesis_status_path,
        hypotheses=config.hypotheses,
        experiment_id=config.id,
        experiment_name=config.name,
        status=status,
        end_time=end_iso,
    )

    return result


def _update_hypothesis_status(
    *,
    hypothesis_status_path: Path,
    hypotheses: list[str],
    experiment_id: str,
    experiment_name: str,
    status: str,
    end_time: str,
) -> None:
    """Load hypothesis_status.json, update entries, and write back."""
    if hypothesis_status_path.exists():
        existing: dict[str, Any] = json.loads(
            hypothesis_status_path.read_text(encoding="utf-8")
        )
    else:
        existing = {}

    for hyp_id in hypotheses:
        existing[hyp_id] = {
            "last_experiment_id": experiment_id,
            "last_experiment_name": experiment_name,
            "last_run_status": status,
            "last_run_time": end_time,
        }

    hypothesis_status_path.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8"
    )


class MissingFeatureError(RuntimeError):
    """Raised when a required feature is absent from the feature store."""
