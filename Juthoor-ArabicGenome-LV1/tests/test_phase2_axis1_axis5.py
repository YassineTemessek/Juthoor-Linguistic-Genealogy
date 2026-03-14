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


axis1 = _load_script(
    REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "scripts" / "research_factory" / "axis1" / "exp_1_2_positional_semantics.py",
    "phase2_axis1",
)
axis5 = _load_script(
    REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "scripts" / "research_factory" / "axis5" / "exp_5_1_sound_meaning_matrix.py",
    "phase2_axis5",
)


def test_canonical_tri_root_keeps_only_three_letters() -> None:
    assert axis1.canonical_tri_root("أوب/أيب") == "ءوب"
    assert axis1.canonical_tri_root("حصحص-حصحص") is None
    assert axis1.canonical_tri_root("قرن") == "قرن"


def test_mean_pairwise_cosine_returns_expected_value() -> None:
    vectors = np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    result = axis1.mean_or_none(axis1.pairwise_cosine_values(vectors))
    assert result is not None
    assert abs(result - (1.0 / 3.0)) < 1e-6


def test_align_articulatory_vectors_reorders_rows() -> None:
    aligned = axis5.align_articulatory_vectors(
        ["ب", "ت", "ث"],
        np.array([[3.0], [1.0], [2.0]], dtype=np.float32),
        ["ت", "ث", "ب"],
    )
    assert aligned[:, 0].tolist() == [2.0, 3.0, 1.0]


def test_compute_first_canonical_correlation_is_bounded() -> None:
    x = np.array([[0.0, 1.0], [1.0, 0.0], [1.0, 1.0], [2.0, 1.0]], dtype=np.float32)
    y = np.array([[0.0, 2.0], [2.0, 0.0], [2.0, 2.0], [4.0, 2.0]], dtype=np.float32)
    corr, x_scores, y_scores = axis5.compute_first_canonical_correlation(x, y)
    assert -1.0 <= corr <= 1.0
    assert x_scores.shape == (4,)
    assert y_scores.shape == (4,)
