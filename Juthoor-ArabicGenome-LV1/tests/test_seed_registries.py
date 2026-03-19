from __future__ import annotations

import json
import sys
from pathlib import Path

from juthoor_arabicgenome_lv1.core.canon_loaders import (
    load_binary_field_registry,
    load_letter_registry,
    load_root_composition_registry,
    load_theory_claims,
)


LV1_ROOT = Path(__file__).resolve().parent.parent
CANON_SCRIPTS = LV1_ROOT / "scripts" / "canon"
if str(CANON_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(CANON_SCRIPTS))

from seed_registries import seed_registries  # noqa: E402


def test_seed_script_runs(tmp_path: Path) -> None:
    summary = seed_registries(tmp_path)
    assert summary["letters"] == 28
    assert summary["binary_fields"] >= 400
    assert summary["root_composition"] > 0
    assert summary["theory_claims"] >= 4


def test_seed_outputs_exist(tmp_path: Path) -> None:
    seed_registries(tmp_path)
    assert (tmp_path / "letters.jsonl").exists()
    assert (tmp_path / "binary_fields.jsonl").exists()
    assert (tmp_path / "root_composition.jsonl").exists()
    assert (tmp_path / "theory_claims.jsonl").exists()
    assert (tmp_path / "quranic_profiles.jsonl").exists()


def test_seeded_letter_registry_loads(tmp_path: Path) -> None:
    seed_registries(tmp_path)
    rows = load_letter_registry(tmp_path)
    assert len(rows) == 28
    assert rows["ب"].status == "draft"
    assert rows["ب"].sources


def test_seeded_binary_registry_loads(tmp_path: Path) -> None:
    seed_registries(tmp_path)
    rows = load_binary_field_registry(tmp_path)
    assert len(rows) >= 400
    assert any(entry.coherence_score is not None for entry in rows.values())


def test_seeded_root_registry_loads(tmp_path: Path) -> None:
    seed_registries(tmp_path)
    rows = load_root_composition_registry(tmp_path)
    assert len(rows) > 1000
    assert any(entry.axial_meaning for entry in rows.values())


def test_seeded_theory_claims_load(tmp_path: Path) -> None:
    seed_registries(tmp_path)
    claims = load_theory_claims(tmp_path)
    assert len(claims) >= 4
    assert {claim.scholar for claim in claims} >= {"jabal", "neili"}


def test_seeded_rows_are_jsonl(tmp_path: Path) -> None:
    seed_registries(tmp_path)
    first = (tmp_path / "letters.jsonl").read_text(encoding="utf-8").splitlines()[0]
    assert json.loads(first)["letter"]
