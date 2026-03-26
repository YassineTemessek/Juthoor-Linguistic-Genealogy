"""End-to-end integration test for the LV1 pipeline.

Loads real data files and validates that the full prediction pipeline runs
without errors and meets expected shape invariants.
"""
from __future__ import annotations

import json
from pathlib import Path

from juthoor_arabicgenome_lv1.factory.root_predictor import (
    build_root_prediction_rows,
    summarize_root_predictions,
)

# Resolve data directories relative to the LV1 package root
_LV1_ROOT = Path(__file__).resolve().parents[1]
_CANON_ROOT = _LV1_ROOT / "data" / "theory_canon"
_ROOTS_FILE = _CANON_ROOT / "roots" / "jabal_roots_raw.jsonl"
_NUCLEI_FILE = _CANON_ROOT / "binary_fields" / "jabal_nuclei_raw.jsonl"
_LETTERS_DIR = _CANON_ROOT / "letters"

_SCHOLAR_FILES = [
    "jabal_letters.jsonl",
    "neili_letters.jsonl",
    "hassan_abbas_letters.jsonl",
    "asim_al_masri_letters.jsonl",
    "anbar_letters.jsonl",
]


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _load_scholar_letters() -> dict[str, dict[str, dict]]:
    grouped: dict[str, dict[str, dict]] = {}
    for fname in _SCHOLAR_FILES:
        for row in _load_jsonl(_LETTERS_DIR / fname):
            scholar = row["scholar"]
            letter = row["letter"]
            grouped.setdefault(scholar, {})[letter] = row
    return grouped


def test_roots_file_has_expected_count() -> None:
    roots = _load_jsonl(_ROOTS_FILE)
    assert len(roots) == 1924, f"Expected 1924 roots, got {len(roots)}"


def test_nuclei_file_loads_correctly() -> None:
    nuclei = _load_jsonl(_NUCLEI_FILE)
    assert len(nuclei) == 456, f"Expected 456 nuclei, got {len(nuclei)}"
    # Every nucleus should have a binary_root key
    assert all("binary_root" in n for n in nuclei)


def test_scholar_letters_load_all_five_scholars() -> None:
    scholars = _load_scholar_letters()
    expected = {"jabal", "neili", "hassan_abbas", "asim_al_masri", "anbar"}
    assert expected == set(scholars.keys()), f"Unexpected scholars: {set(scholars.keys())}"
    # Jabal should have all 28 letters
    assert len(scholars["jabal"]) == 28, f"Expected 28 Jabal letters, got {len(scholars['jabal'])}"


def test_jabal_pipeline_runs_and_returns_all_roots() -> None:
    roots = _load_jsonl(_ROOTS_FILE)
    nuclei = _load_jsonl(_NUCLEI_FILE)
    scholars = _load_scholar_letters()

    rows = build_root_prediction_rows(roots, nuclei, scholars, scholar="jabal")

    assert len(rows) == len(roots), (
        f"Expected one prediction row per root ({len(roots)}), got {len(rows)}"
    )


def test_no_empty_predictions_for_roots_with_features() -> None:
    roots = _load_jsonl(_ROOTS_FILE)
    nuclei = _load_jsonl(_NUCLEI_FILE)
    scholars = _load_scholar_letters()

    rows = build_root_prediction_rows(roots, nuclei, scholars, scholar="jabal")

    # Roots that have actual jabal_features should produce non-empty predictions
    roots_with_features = {r["root"] for r in roots if r.get("jabal_features")}
    failures = [
        row for row in rows
        if row["root"] in roots_with_features and not row["predicted_features"]
    ]
    # Allow a small tolerance (some roots may be genuinely unpredictable after filtering)
    assert len(failures) < 50, (
        f"Too many roots with features but empty predictions: {len(failures)}"
    )


def test_summary_reflects_correct_root_count() -> None:
    roots = _load_jsonl(_ROOTS_FILE)
    nuclei = _load_jsonl(_NUCLEI_FILE)
    scholars = _load_scholar_letters()

    rows = build_root_prediction_rows(roots, nuclei, scholars, scholar="jabal")
    summary = summarize_root_predictions(rows)

    assert summary["overall"]["roots"] == 1924
    assert "jabal" in summary["by_scholar"]
    assert summary["by_scholar"]["jabal"]["count"] == 1924


def test_summary_contains_expected_model_keys() -> None:
    roots = _load_jsonl(_ROOTS_FILE)
    nuclei = _load_jsonl(_NUCLEI_FILE)
    scholars = _load_scholar_letters()

    rows = build_root_prediction_rows(roots, nuclei, scholars, scholar="jabal")
    summary = summarize_root_predictions(rows)

    # At least intersection and phonetic_gestural models should appear
    by_model = summary["by_model"]
    assert "intersection" in by_model or "phonetic_gestural" in by_model, (
        f"No known model keys found: {list(by_model.keys())}"
    )
    # All rows should be accounted for across models
    total_from_models = sum(v["count"] for v in by_model.values())
    assert total_from_models == 1924
