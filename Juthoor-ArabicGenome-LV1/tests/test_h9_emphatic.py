from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1].parent


def _load_script(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


axis5 = _load_script(
    REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "scripts" / "research_factory" / "axis5" / "exp_5_2_emphasis_hypothesis.py",
    "phase4_axis5_emphasis",
)


def test_infer_added_letter_and_position_for_emphatic_experiment() -> None:
    assert axis5.infer_added_letter_and_position("كتب", "كب") == ("ت", 2)
    assert axis5.infer_added_letter_and_position("قطب", "قب") == ("ط", 2)
    assert axis5.infer_added_letter_and_position("حصحص-حصحص", "حص") is None


def test_modifier_effect_is_distance_from_binary() -> None:
    binary = np.array([1.0, 0.0], dtype=np.float32)
    axial_same = np.array([1.0, 0.0], dtype=np.float32)
    axial_diff = np.array([0.0, 1.0], dtype=np.float32)
    assert abs(axis5.modifier_effect(binary, axial_same) - 0.0) < 1e-6
    assert abs(axis5.modifier_effect(binary, axial_diff) - 1.0) < 1e-6


def test_summarize_emphatic_rows_flags_negative_result() -> None:
    rows = [
        {"pair_id": "ت_ط", "plain_effect": 0.4, "emphatic_effect": 0.3},
        {"pair_id": "ت_ط", "plain_effect": 0.5, "emphatic_effect": 0.4},
        {"pair_id": "د_ض", "plain_effect": 0.6, "emphatic_effect": 0.5},
        {"pair_id": "د_ض", "plain_effect": 0.3, "emphatic_effect": 0.2},
        {"pair_id": "س_ص", "plain_effect": 0.4, "emphatic_effect": 0.35},
    ]
    summary = axis5.summarize_emphatic_rows(rows)
    assert summary["n_pairs"] == 5
    assert summary["mean_diff"] < 0.0
    assert summary["supports_h9"] is False
