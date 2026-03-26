# ACTIVE: maintained shared visualization helpers exercised by Research Factory tests.
from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from scipy.cluster.hierarchy import dendrogram


def _pick_font() -> str:
    candidates = (
        "Noto Naskh Arabic",
        "Noto Sans Arabic",
        "Amiri",
        "Arial",
        "DejaVu Sans",
    )
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return "sans-serif"


plt.rcParams["font.family"] = _pick_font()
plt.rcParams["axes.unicode_minus"] = False


def _prepare_output(out_path: str | Path) -> Path:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def plot_heatmap(matrix, labels, title, out_path):
    arr = np.asarray(matrix, dtype=float)
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(arr, cmap="viridis", aspect="auto")
    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=90)
    ax.set_yticklabels(labels)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(_prepare_output(out_path), dpi=300, bbox_inches="tight")
    return fig


def plot_dendrogram(linkage_matrix, labels, title, out_path):
    fig, ax = plt.subplots(figsize=(10, 8))
    dendrogram(np.asarray(linkage_matrix, dtype=float), labels=list(labels), leaf_rotation=90, ax=ax)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(_prepare_output(out_path), dpi=300, bbox_inches="tight")
    return fig


def plot_violin(groups: dict[str, list], title, out_path):
    labels = list(groups.keys())
    values = [np.asarray(groups[label], dtype=float) for label in labels]
    fig, ax = plt.subplots(figsize=(10, 6))
    parts = ax.violinplot(values, showmeans=True, showextrema=True)
    for body in parts["bodies"]:
        body.set_alpha(0.6)
    ax.set_xticks(np.arange(1, len(labels) + 1))
    ax.set_xticklabels(labels, rotation=20)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(_prepare_output(out_path), dpi=300, bbox_inches="tight")
    return fig


def plot_scatter_with_labels(x, y, labels, title, out_path):
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.scatter(x_arr, y_arr, s=45, alpha=0.8)
    for xi, yi, label in zip(x_arr, y_arr, labels):
        ax.annotate(str(label), (xi, yi), fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(_prepare_output(out_path), dpi=300, bbox_inches="tight")
    return fig


def plot_distribution(values, title, out_path, bins=50):
    arr = np.asarray(values, dtype=float)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(arr, bins=bins, color="#3A6EA5", alpha=0.8, edgecolor="white")
    mean = float(np.mean(arr))
    median = float(np.median(arr))
    ax.axvline(mean, color="#D1495B", linestyle="--", linewidth=1.8, label=f"mean={mean:.3f}")
    ax.axvline(median, color="#2E8B57", linestyle=":", linewidth=1.8, label=f"median={median:.3f}")
    ax.legend()
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(_prepare_output(out_path), dpi=300, bbox_inches="tight")
    return fig
