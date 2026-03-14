from __future__ import annotations

import json
import sys
import importlib.util
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform

REPO_ROOT = Path(__file__).resolve().parents[4]
LV1_SRC = REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "src"
if str(LV1_SRC) not in sys.path:
    sys.path.append(str(LV1_SRC))

from juthoor_arabicgenome_lv1.factory.experiment_runner import ExperimentConfig, run_experiment  # noqa: E402
from juthoor_arabicgenome_lv1.factory.feature_store import load_feature  # noqa: E402


def _load_common_module(name: str):
    common_root = REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "scripts" / "research_factory" / "common"
    path = common_root / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"rf_common_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"rf_common_{name}"] = module
    spec.loader.exec_module(module)
    return module


_statistics = _load_common_module("statistics")
_visualization = _load_common_module("visualization")
mantel_test = _statistics.mantel_test
plot_dendrogram = _visualization.plot_dendrogram
plot_heatmap = _visualization.plot_heatmap


OUTPUT_DIR = REPO_ROOT / "outputs" / "research_factory" / "axis1"


def cosine_similarity_matrix(vectors: np.ndarray) -> np.ndarray:
    return np.asarray(vectors, dtype=np.float32) @ np.asarray(vectors, dtype=np.float32).T


def euclidean_distance_matrix(vectors: np.ndarray) -> np.ndarray:
    arr = np.asarray(vectors, dtype=np.float32)
    diffs = arr[:, None, :] - arr[None, :, :]
    return np.sqrt(np.sum(diffs * diffs, axis=2, dtype=np.float32))


def build_neighbor_rows(labels: list[str], sim_matrix: np.ndarray) -> list[dict]:
    rows: list[dict] = []
    for idx, label in enumerate(labels):
        order = np.argsort(sim_matrix[idx])[::-1]
        neighbors = []
        for j in order:
            if j == idx:
                continue
            neighbors.append({"letter": labels[j], "similarity": round(float(sim_matrix[idx, j]), 6)})
            if len(neighbors) >= 5:
                break
        rows.append(
            {
                "letter": label,
                "top_neighbors": neighbors,
                "mean_similarity_to_others": round(float(np.mean(np.delete(sim_matrix[idx], idx))), 6),
            }
        )
    return rows


def run_letter_similarity() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    letter_embeddings, letter_meta = load_feature("letter_embeddings")
    articulatory_vectors, artic_meta = load_feature("articulatory_vectors")
    labels = list(letter_meta["entity_ids"])
    artic_order = {letter: i for i, letter in enumerate(artic_meta["entity_ids"])}
    if set(labels) != set(artic_order):
        raise ValueError("letter_embeddings and articulatory_vectors contain different letter sets")
    articulatory_vectors = np.asarray([articulatory_vectors[artic_order[label]] for label in labels], dtype=np.float32)

    semantic_sim = cosine_similarity_matrix(letter_embeddings)
    semantic_dist = 1.0 - semantic_sim
    phonetic_dist = euclidean_distance_matrix(articulatory_vectors)
    condensed_semantic = squareform(semantic_dist, checks=False)
    linkage_matrix = linkage(condensed_semantic, method="average")
    mantel_r, mantel_p = mantel_test(semantic_dist, phonetic_dist, permutations=999, random_state=42)

    rows = build_neighbor_rows(labels, semantic_sim)
    with (OUTPUT_DIR / "letter_similarity.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    plot_heatmap(semantic_sim, labels, "Semantic Similarity Between Arabic Letters", OUTPUT_DIR / "semantic_heatmap.png")
    plot_dendrogram(linkage_matrix, labels, "Letter Semantic Clustering", OUTPUT_DIR / "dendrogram.png")
    mantel_payload = {
        "mantel_r": round(float(mantel_r), 6),
        "p_value": round(float(mantel_p), 6),
        "n_letters": len(labels),
    }
    (OUTPUT_DIR / "mantel_result.json").write_text(json.dumps(mantel_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return mantel_payload


def main() -> int:
    config = ExperimentConfig(
        id="1.1",
        name="letter_similarity_matrix",
        hypotheses=["H1"],
        required_features=["letter_embeddings", "articulatory_vectors"],
        run_fn=run_letter_similarity,
    )
    result = run_experiment(config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
