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
    REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "scripts" / "research_factory" / "axis6" / "exp_6_2_unsupervised_discovery.py",
    "phase3_axis6_unsupervised",
)


def test_canonical_tri_root_normalizes_hamza() -> None:
    assert axis6.canonical_tri_root("أوب/أيب") == "ءوب"
    assert axis6.canonical_tri_root("قرن") == "قرن"


def test_summarize_clusters_counts_noise_and_dominance() -> None:
    labels = np.array([0, 0, 1, -1], dtype=int)
    families = ["بر", "بر", "تب", "تب"]
    roots = ["بور", "بير", "توب", "ثوب"]
    rows, summary = axis6.summarize_clusters(labels, families, roots)
    assert summary["n_clusters"] == 2
    assert summary["n_noise"] == 1
    assert rows[0]["dominant_binary_root"] == "بر"
