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


axis6 = _load_script(
    REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "scripts" / "research_factory" / "axis6" / "exp_6_1_meaning_predictor.py",
    "phase3_axis6_predictor",
)


def test_infer_added_letter_and_position() -> None:
    assert axis6.infer_added_letter_and_position("بوب", "بب") == ("و", 2)
    assert axis6.infer_added_letter_and_position("أوب/أيب", "ءب") == ("و", 2)
    assert axis6.infer_added_letter_and_position("قرن", "قر") == ("ن", 3)
    assert axis6.infer_added_letter_and_position("حصحص-حصحص", "حص") is None


def test_position_one_hot() -> None:
    assert axis6.position_one_hot(1).tolist() == [1.0, 0.0, 0.0]
    assert axis6.position_one_hot(3).tolist() == [0.0, 0.0, 1.0]


def test_cosine_similarity_vectorized() -> None:
    a = np.array([[1.0, 0.0], [1.0, 1.0]], dtype=np.float32)
    b = np.array([[1.0, 0.0], [1.0, -1.0]], dtype=np.float32)
    sims = axis6.cosine_similarity(a, b)
    assert sims.shape == (2,)
    assert abs(float(sims[0]) - 1.0) < 1e-6
