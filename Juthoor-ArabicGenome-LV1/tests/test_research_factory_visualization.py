from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import linkage


def _load_module(name: str, rel_path: str):
    path = Path(__file__).resolve().parents[1] / rel_path
    spec = spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


viz = _load_module("rf_visualization", "scripts/research_factory/common/visualization.py")


def test_visualization_functions_write_png(tmp_path: Path):
    heatmap_path = tmp_path / "heatmap.png"
    dendro_path = tmp_path / "dendro.png"
    violin_path = tmp_path / "violin.png"
    scatter_path = tmp_path / "scatter.png"
    dist_path = tmp_path / "dist.png"

    fig1 = viz.plot_heatmap(np.eye(3), ["أ", "ب", "ت"], "heatmap", heatmap_path)
    fig2 = viz.plot_dendrogram(linkage(np.array([[0.0], [1.0], [2.0]]), method="ward"), ["أ", "ب", "ت"], "dendro", dendro_path)
    fig3 = viz.plot_violin({"a": [1, 2, 3], "b": [2, 3, 4]}, "violin", violin_path)
    fig4 = viz.plot_scatter_with_labels([0, 1], [1, 0], ["أ", "ب"], "scatter", scatter_path)
    fig5 = viz.plot_distribution([1, 2, 3, 4, 5], "dist", dist_path)

    for path in (heatmap_path, dendro_path, violin_path, scatter_path, dist_path):
        assert path.exists()
        assert path.stat().st_size > 0

    for fig in (fig1, fig2, fig3, fig4, fig5):
        assert fig is not None
