from __future__ import annotations

import json
import sys
import importlib.util
from pathlib import Path

import numpy as np
from sklearn.cross_decomposition import CCA
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[4]
LV1_SRC = REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "src"
if str(LV1_SRC) not in sys.path:
    sys.path.append(str(LV1_SRC))

from juthoor_arabicgenome_lv1.factory.experiment_runner import ExperimentConfig, run_experiment  # noqa: E402
from juthoor_arabicgenome_lv1.factory.feature_store import load_feature  # noqa: E402


OUTPUT_DIR = REPO_ROOT / "outputs" / "research_factory" / "axis5"


def align_articulatory_vectors(letter_ids: list[str], vectors: np.ndarray, articulatory_ids: list[str]) -> np.ndarray:
    order = {letter: i for i, letter in enumerate(articulatory_ids)}
    if set(letter_ids) != set(order):
        raise ValueError("letter_embeddings and articulatory_vectors contain different letter sets")
    return np.asarray([vectors[order[letter]] for letter in letter_ids], dtype=np.float32)


def compute_first_canonical_correlation(
    articulatory_vectors: np.ndarray,
    semantic_embeddings: np.ndarray,
) -> tuple[float, np.ndarray, np.ndarray]:
    x = StandardScaler().fit_transform(np.asarray(articulatory_vectors, dtype=np.float32))
    y = StandardScaler().fit_transform(np.asarray(semantic_embeddings, dtype=np.float32))
    y = PCA(n_components=2, random_state=42).fit_transform(y)
    cca = CCA(n_components=1, max_iter=2000)
    x_c, y_c = cca.fit_transform(x, y)
    correlation = float(np.corrcoef(x_c[:, 0], y_c[:, 0])[0, 1])
    return correlation, x_c[:, 0], y_c[:, 0]


def permutation_baseline(
    articulatory_vectors: np.ndarray,
    semantic_embeddings: np.ndarray,
    *,
    n_perm: int = 999,
    random_state: int = 42,
) -> tuple[float, np.ndarray, float, float]:
    rng = np.random.default_rng(random_state)
    observed, _, _ = compute_first_canonical_correlation(articulatory_vectors, semantic_embeddings)
    permuted = []
    for _ in range(n_perm):
        perm = rng.permutation(semantic_embeddings.shape[0])
        corr, _, _ = compute_first_canonical_correlation(articulatory_vectors, semantic_embeddings[perm])
        permuted.append(corr)
    permuted_arr = np.asarray(permuted, dtype=np.float32)
    p_value = float((np.sum(permuted_arr >= observed) + 1) / (permuted_arr.size + 1))
    return observed, permuted_arr, float(np.mean(permuted_arr)), p_value


def run_sound_meaning_matrix() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    letter_embeddings, letter_meta = load_feature("letter_embeddings")
    articulatory_vectors, articulatory_meta = load_feature("articulatory_vectors")
    labels = list(letter_meta["entity_ids"])
    aligned_articulatory = align_articulatory_vectors(labels, articulatory_vectors, list(articulatory_meta["entity_ids"]))

    correlation, x_scores, y_scores = compute_first_canonical_correlation(aligned_articulatory, letter_embeddings)
    observed, permuted_arr, perm_mean, perm_p = permutation_baseline(aligned_articulatory, letter_embeddings)
    summary = {
        "n_letters": len(labels),
        "articulatory_dims": int(aligned_articulatory.shape[1]),
        "semantic_dims": int(letter_embeddings.shape[1]),
        "semantic_pca_dims": 2,
        "first_canonical_correlation": round(correlation, 6),
        "permutation_mean": round(perm_mean, 6),
        "permutation_p_value": round(perm_p, 6),
        "permutation_ci_low": round(float(np.quantile(permuted_arr, 0.025)), 6),
        "permutation_ci_high": round(float(np.quantile(permuted_arr, 0.975)), 6),
        "success_threshold": 0.4,
        "supports_h1_via_cca": bool(correlation > 0.4 and perm_p < 0.05),
    }
    loadings = [
        {
            "letter": label,
            "articulatory_score": round(float(x_scores[idx]), 6),
            "semantic_score": round(float(y_scores[idx]), 6),
        }
        for idx, label in enumerate(labels)
    ]
    visualization_path = REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "scripts" / "research_factory" / "common" / "visualization.py"
    spec = importlib.util.spec_from_file_location("rf_common_visualization_axis5_1", visualization_path)
    assert spec and spec.loader
    visualization_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(visualization_module)
    visualization_module.plot_scatter_with_labels(
        x_scores,
        y_scores,
        labels,
        "CCA First Component: Sound vs Meaning",
        OUTPUT_DIR / "cca_first_component.png",
    )
    (OUTPUT_DIR / "cca_letter_loadings.json").write_text(
        json.dumps(loadings, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "cca_result.json").write_text(
        json.dumps(
            {
                "n_letters": len(labels),
                "n_components": 1,
                "canonical_correlations": [round(correlation, 6)],
                "first_canonical_correlation": round(correlation, 6),
                "success_threshold": 0.4,
                "passes_threshold": bool(correlation > 0.4),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "cca_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    config = ExperimentConfig(
        id="5.1",
        name="sound_meaning_matrix",
        hypotheses=["H1"],
        required_features=["letter_embeddings", "articulatory_vectors"],
        run_fn=run_sound_meaning_matrix,
    )
    result = run_experiment(config)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
