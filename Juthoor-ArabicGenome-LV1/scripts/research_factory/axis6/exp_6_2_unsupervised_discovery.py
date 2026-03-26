# ACTIVE: maintained Axis 6 unsupervised-discovery experiment with direct test coverage.
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
from sklearn.cluster import HDBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score

REPO_ROOT = Path(__file__).resolve().parents[4]
LV1_SRC = REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "src"
if str(LV1_SRC) not in sys.path:
    sys.path.append(str(LV1_SRC))

from juthoor_arabicgenome_lv1.core.loaders import load_triliteral_roots  # noqa: E402
from juthoor_arabicgenome_lv1.factory.experiment_runner import ExperimentConfig, run_experiment  # noqa: E402
from juthoor_arabicgenome_lv1.factory.feature_store import load_feature  # noqa: E402


OUTPUT_DIR = REPO_ROOT / "outputs" / "research_factory" / "axis6"
ARABIC_RE = re.compile(r"[ءابتثجحخدذرزسشصضطظعغفقكلمنهويى]")
SPLIT_RE = re.compile(r"(?:/|-|←|\s)+")
NORMALIZE_MAP = str.maketrans({"أ": "ء", "إ": "ء", "آ": "ء", "ى": "ي"})


def canonical_tri_root(value: str) -> str | None:
    candidate = SPLIT_RE.split(value.strip())[0].translate(NORMALIZE_MAP)
    letters = ARABIC_RE.findall(candidate)
    if len(letters) != 3:
        return None
    return "".join(letters)


def prepare_dataset() -> tuple[np.ndarray, list[str], list[str]]:
    axial_embeddings, axial_meta = load_feature("axial_meaning_embeddings")
    valid_roots = []
    labels = []
    tri_index = {tri_root: i for i, tri_root in enumerate(axial_meta["entity_ids"])}
    for record in load_triliteral_roots():
        if canonical_tri_root(record.tri_root) is None:
            continue
        if record.tri_root not in tri_index:
            continue
        valid_roots.append(record.tri_root)
        labels.append(record.binary_root.translate(NORMALIZE_MAP))
    x = np.asarray([axial_embeddings[tri_index[root]] for root in valid_roots], dtype=np.float32)
    return x, labels, valid_roots


def cluster_embeddings(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    pca_dims = min(50, x.shape[0] - 1, x.shape[1])
    reduced = PCA(n_components=pca_dims, random_state=42).fit_transform(x)
    clusterer = HDBSCAN(min_cluster_size=5, min_samples=3)
    labels = clusterer.fit_predict(reduced)
    return reduced, labels


def summarize_clusters(cluster_labels: np.ndarray, family_labels: list[str], roots: list[str]) -> tuple[list[dict], dict]:
    rows = []
    unique_clusters = sorted({int(label) for label in cluster_labels if int(label) != -1})
    for cluster_id in unique_clusters:
        idx = np.where(cluster_labels == cluster_id)[0]
        family_counts = {}
        for i in idx:
            family_counts[family_labels[i]] = family_counts.get(family_labels[i], 0) + 1
        dominant_family, dominant_count = max(family_counts.items(), key=lambda item: item[1])
        rows.append(
            {
                "cluster_id": cluster_id,
                "size": int(idx.size),
                "dominant_binary_root": dominant_family,
                "dominant_share": round(float(dominant_count / idx.size), 6),
                "n_binary_roots": len(family_counts),
                "sample_roots": [roots[i] for i in idx[:10]],
            }
        )

    noise_count = int(np.sum(cluster_labels == -1))
    summary = {
        "n_clusters": len(unique_clusters),
        "n_noise": noise_count,
        "noise_share": round(float(noise_count / len(cluster_labels)), 6),
    }
    return rows, summary


def run_unsupervised_discovery() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    x, family_labels, roots = prepare_dataset()
    reduced, cluster_labels = cluster_embeddings(x)
    ari = adjusted_rand_score(family_labels, cluster_labels)
    cluster_rows, cluster_summary = summarize_clusters(cluster_labels, family_labels, roots)

    with (OUTPUT_DIR / "unsupervised_clusters.jsonl").open("w", encoding="utf-8") as handle:
        for row in cluster_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    assignments = []
    for root, family, cluster_id, coords in zip(roots, family_labels, cluster_labels.tolist(), reduced.tolist()):
        assignments.append(
            {
                "tri_root": root,
                "binary_root": family,
                "cluster_id": int(cluster_id),
                "pca_1": round(float(coords[0]), 6),
                "pca_2": round(float(coords[1]), 6) if len(coords) > 1 else 0.0,
            }
        )
    with (OUTPUT_DIR / "cluster_assignments.jsonl").open("w", encoding="utf-8") as handle:
        for row in assignments:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "n_examples": int(x.shape[0]),
        "ari": round(float(ari), 6),
        "supports_h11": bool(float(ari) > 0.2),
        **cluster_summary,
    }
    (OUTPUT_DIR / "unsupervised_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    config = ExperimentConfig(
        id="6.2",
        name="unsupervised_discovery",
        hypotheses=["H11"],
        required_features=["axial_meaning_embeddings"],
        run_fn=run_unsupervised_discovery,
    )
    result = run_experiment(config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
