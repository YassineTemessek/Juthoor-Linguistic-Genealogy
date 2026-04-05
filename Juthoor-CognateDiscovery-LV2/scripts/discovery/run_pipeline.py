"""
Juthoor LV2 — Unified Discovery Pipeline

Chains Eye 1 → Eye 2 → Cognate Graph in a single command.

Usage:
    python scripts/discovery/run_pipeline.py --source ara --target grc
    python scripts/discovery/run_pipeline.py --source ara --target grc --stage eye1
    python scripts/discovery/run_pipeline.py --source ara --target grc --stage eye2
    python scripts/discovery/run_pipeline.py --stage graph
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

LV2_ROOT = Path(__file__).resolve().parents[2]

EYE1_SCRIPT = LV2_ROOT / "scripts" / "discovery" / "run_eye1_full_scale.py"
EYE2_MODULE = "juthoor_cognatediscovery_lv2.discovery.eye2_batch_scorer"
GRAPH_SCRIPT = LV2_ROOT / "scripts" / "discovery" / "build_cognate_graph.py"
OUTPUTS_DIR = LV2_ROOT / "outputs"

# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def _load_config() -> dict:
    """Load discovery.yaml; return hardcoded defaults if pyyaml is unavailable."""
    config_path = LV2_ROOT / "config" / "discovery.yaml"
    try:
        import yaml  # type: ignore
        with open(config_path, encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except ImportError:
        print("[pipeline] pyyaml not available — using hardcoded defaults", file=sys.stderr)
    except FileNotFoundError:
        print(f"[pipeline] Config not found: {config_path} — using hardcoded defaults", file=sys.stderr)
    return {
        "eye1": {"threshold": 0.3, "min_overlap": 2, "top_k": 200},
        "eye2": {"batch_size": 10, "first_pass_model": "sonnet", "min_discovery_score": 0.6, "top_n_per_root": 50},
    }

# ---------------------------------------------------------------------------
# Stage helpers
# ---------------------------------------------------------------------------

def _header(msg: str) -> None:
    bar = "=" * 60
    print(f"\n{bar}", file=sys.stderr)
    print(f"  {msg}", file=sys.stderr)
    print(f"{bar}", file=sys.stderr)


def _run(cmd: list[str], label: str) -> int:
    """Run a subprocess, stream output live, return exit code."""
    print(f"[pipeline] Running: {' '.join(str(c) for c in cmd)}", file=sys.stderr)
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"[pipeline] ERROR: {label} exited with code {result.returncode}", file=sys.stderr)
    return result.returncode


def run_eye1(args: argparse.Namespace, cfg: dict) -> int:
    eye1_cfg = cfg.get("eye1", {})
    threshold = args.threshold if args.threshold is not None else eye1_cfg.get("threshold", 0.3)
    top_k = args.top_k if args.top_k is not None else eye1_cfg.get("top_k", 200)
    min_overlap = eye1_cfg.get("min_overlap", 2)

    cmd = [
        sys.executable, str(EYE1_SCRIPT),
        "--target", args.target,
        "--threshold", str(threshold),
        "--top-k", str(top_k),
        "--min-overlap", str(min_overlap),
    ]
    return _run(cmd, "Eye 1")


def run_eye2(args: argparse.Namespace, cfg: dict) -> int:
    eye1_output = OUTPUTS_DIR / f"eye1_full_scale_{args.target}.jsonl"
    if not eye1_output.exists():
        print(
            f"[pipeline] ERROR: Eye 1 output not found: {eye1_output}\n"
            "  Run Eye 1 first: --stage eye1",
            file=sys.stderr,
        )
        return 1

    eye2_cfg = cfg.get("eye2", {})
    model = args.model if args.model else eye2_cfg.get("first_pass_model", "sonnet")
    batch_size = eye2_cfg.get("batch_size", 10)
    min_score = eye2_cfg.get("min_discovery_score", 0.6)
    top_n = eye2_cfg.get("top_n_per_root", 50)

    eye2_output = OUTPUTS_DIR / "leads" / f"eye2_{args.source}_{args.target}.jsonl"
    eye2_output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", EYE2_MODULE,
        "--input", str(eye1_output),
        "--output", str(eye2_output),
        "--lang", args.target,
        "--model", model,
        "--batch-size", str(batch_size),
        "--min-discovery-score", str(min_score),
        "--top-n-per-root", str(top_n),
    ]
    if args.dry_run:
        cmd.append("--dry-run")
    if args.resume:
        cmd.append("--resume")

    return _run(cmd, "Eye 2")


def run_graph(cfg: dict) -> int:
    leads_dir = OUTPUTS_DIR / "leads"
    if not leads_dir.exists() or not any(leads_dir.glob("eye2_*.jsonl")):
        print(
            f"[pipeline] ERROR: No Eye 2 leads found in: {leads_dir}\n"
            "  Run Eye 2 first: --stage eye2",
            file=sys.stderr,
        )
        return 1

    cmd = [sys.executable, str(GRAPH_SCRIPT)]
    return _run(cmd, "Cognate Graph")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Juthoor LV2 unified discovery pipeline: Eye 1 → Eye 2 → Graph"
    )
    p.add_argument("--source", default="ara", help="Source language code (default: ara)")
    p.add_argument("--target", default=None, help="Target language code (required for eye1/eye2)")
    p.add_argument(
        "--stage",
        default="all",
        choices=["all", "eye1", "eye2", "graph"],
        help="Pipeline stage to run (default: all)",
    )
    p.add_argument("--top-k", type=int, default=None, help="Override Eye 1 top-K")
    p.add_argument("--threshold", type=float, default=None, help="Override Eye 1 threshold")
    p.add_argument("--model", default=None, help="Override Eye 2 model (sonnet/opus)")
    p.add_argument("--dry-run", action="store_true", help="Pass --dry-run to Eye 2")
    p.add_argument("--resume", action="store_true", help="Pass --resume to Eye 2")
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    # Validate --target requirement
    if args.stage in ("eye1", "eye2", "all") and not args.target:
        print("[pipeline] ERROR: --target is required for stages: eye1, eye2, all", file=sys.stderr)
        sys.exit(1)

    cfg = _load_config()
    t_start = time.time()
    failed = False

    stages = ["eye1", "eye2", "graph"] if args.stage == "all" else [args.stage]

    for stage in stages:
        _header(f"Stage: {stage.upper()}")
        t0 = time.time()

        if stage == "eye1":
            rc = run_eye1(args, cfg)
        elif stage == "eye2":
            rc = run_eye2(args, cfg)
        else:
            rc = run_graph(cfg)

        elapsed = time.time() - t0
        status = "OK" if rc == 0 else "FAILED"
        print(f"[pipeline] {stage.upper()} {status} ({elapsed:.1f}s)", file=sys.stderr)

        if rc != 0:
            failed = True
            break

    total = time.time() - t_start
    _header(f"Pipeline {'DONE' if not failed else 'FAILED'} ({total:.1f}s total)")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
