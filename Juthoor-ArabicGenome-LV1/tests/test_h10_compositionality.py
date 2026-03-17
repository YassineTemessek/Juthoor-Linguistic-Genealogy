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


axis3 = _load_script(
    REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "scripts" / "research_factory" / "axis3" / "exp_3_2_compositionality.py",
    "phase4_axis3_compositionality",
)


def test_canonical_tri_root_for_compositionality() -> None:
    assert axis3.canonical_tri_root("أوب/أيب") == "ءوب"
    assert axis3.canonical_tri_root("قرن") == "قرن"
    assert axis3.canonical_tri_root("حصحص-حصحص") is None


def test_cosine_similarity_vectorized_for_compositionality() -> None:
    a = np.array([[1.0, 0.0], [1.0, 1.0]], dtype=np.float32)
    b = np.array([[1.0, 0.0], [1.0, -1.0]], dtype=np.float32)
    sims = axis3.cosine_similarity(a, b)
    assert sims.shape == (2,)
    assert abs(float(sims[0]) - 1.0) < 1e-6


def test_shuffled_baseline_returns_requested_permutations() -> None:
    additive = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    targets = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    baseline = axis3.shuffled_baseline(additive, targets, n_perm=25, random_state=0)
    assert baseline.shape == (25,)
    assert np.all(np.isfinite(baseline))
