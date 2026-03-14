"""
build_dashboard.py — Aggregate all experiment results and hypothesis statuses
into a single dashboard JSON.

Usage:
    python build_dashboard.py
    → writes outputs/research_factory/reports/hypothesis_dashboard.json
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# Path anchors
_SCRIPT_DIR = Path(__file__).resolve().parent          # .../scripts/research_factory/common
_LV1_ROOT   = _SCRIPT_DIR.parents[2]                  # .../Juthoor-ArabicGenome-LV1
_MONO_ROOT  = _LV1_ROOT.parent                        # monorepo root

HYPOTHESES_YAML    = _LV1_ROOT / "resources" / "hypotheses.yaml"
REPORTS_DIR        = _MONO_ROOT / "outputs" / "research_factory" / "reports"
STATUS_FILE        = _MONO_ROOT / "outputs" / "research_factory" / "hypothesis_status.json"
DASHBOARD_OUT      = REPORTS_DIR / "hypothesis_dashboard.json"


def _load_hypotheses() -> list[dict]:
    with HYPOTHESES_YAML.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data.get("hypotheses", [])


def _load_results() -> dict[str, dict]:
    """Return mapping experiment_id -> result dict for every *_result.json found."""
    results: dict[str, dict] = {}
    for path in REPORTS_DIR.glob("*_result.json"):
        try:
            with path.open(encoding="utf-8") as fh:
                result = json.load(fh)
            exp_id = result.get("experiment_id")
            if exp_id:
                results[exp_id] = result
        except (json.JSONDecodeError, OSError):
            pass
    return results


def _load_status() -> dict[str, dict]:
    if not STATUS_FILE.exists():
        return {}
    with STATUS_FILE.open(encoding="utf-8") as fh:
        return json.load(fh)


def _build_experiment_entry(exp_id: str, result: dict | None) -> dict[str, Any]:
    if result is None:
        return {
            "id": exp_id,
            "name": None,
            "status": "pending",
            "metrics": None,
        }
    return {
        "id": exp_id,
        "name": result.get("experiment_name"),
        "status": result.get("status", "unknown"),
        "metrics": result.get("metrics"),
    }


def build_dashboard() -> dict[str, Any]:
    """Build and return the dashboard dict."""
    hypotheses_raw = _load_hypotheses()
    results        = _load_results()
    statuses       = _load_status()

    summary_counts: dict[str, int] = {}
    hypotheses_out: list[dict] = []

    for hyp in hypotheses_raw:
        hyp_id   = hyp["id"]
        exp_ids  = hyp.get("experiments", [])

        # Determine status: prefer YAML (already verdict-bearing), fall back to runtime status
        status = hyp.get("status", "pending")
        if status == "pending" and hyp_id in statuses:
            status = statuses[hyp_id].get("last_run_status", "pending")

        # Build per-experiment entries
        experiments_out = [
            _build_experiment_entry(eid, results.get(eid))
            for eid in exp_ids
        ]

        summary_counts[status] = summary_counts.get(status, 0) + 1

        hypotheses_out.append({
            "id":          hyp_id,
            "name":        hyp.get("name"),
            "claim":       hyp.get("claim"),
            "source":      hyp.get("source"),
            "status":      status,
            "experiments": experiments_out,
        })

    total_experiments_run = len(results)

    return {
        "generated":              datetime.now(timezone.utc).isoformat(),
        "total_experiments_run":  total_experiments_run,
        "hypotheses":             hypotheses_out,
        "summary":                summary_counts,
    }


def main() -> None:
    dashboard = build_dashboard()

    DASHBOARD_OUT.parent.mkdir(parents=True, exist_ok=True)
    with DASHBOARD_OUT.open("w", encoding="utf-8") as fh:
        json.dump(dashboard, fh, ensure_ascii=False, indent=2)

    print(f"Dashboard written -> {DASHBOARD_OUT}")
    print(f"Total experiments run : {dashboard['total_experiments_run']}")
    print("Summary:")
    for verdict, count in sorted(dashboard["summary"].items()):
        print(f"  {verdict:<20} {count}")
    total = sum(dashboard["summary"].values())
    print(f"  {'TOTAL':<20} {total}")


if __name__ == "__main__":
    main()
