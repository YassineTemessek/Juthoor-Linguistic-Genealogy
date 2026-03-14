from __future__ import annotations

import json
import sys
import importlib.util
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
LV1_SRC = REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "src"
if str(LV1_SRC) not in sys.path:
    sys.path.append(str(LV1_SRC))

from juthoor_arabicgenome_lv1.core.loaders import load_triliteral_roots  # noqa: E402
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


_visualization = _load_common_module("visualization")
plot_distribution = _visualization.plot_distribution


OUTPUT_DIR = REPO_ROOT / "outputs" / "research_factory" / "axis2"


def mean_pairwise_cosine(vectors: np.ndarray) -> float | None:
    if vectors.shape[0] < 2:
        return None
    sim = np.asarray(vectors, dtype=np.float32) @ np.asarray(vectors, dtype=np.float32).T
    idx = np.triu_indices(sim.shape[0], k=1)
    return float(np.mean(sim[idx]))


def compute_random_baseline(
    embeddings: np.ndarray,
    family_sizes: list[int],
    *,
    n_iter: int = 1000,
    random_state: int = 42,
) -> list[float]:
    rng = np.random.default_rng(random_state)
    n = embeddings.shape[0]
    all_idx = np.arange(n)
    results: list[float] = []
    valid_sizes = [size for size in family_sizes if size >= 2]
    for _ in range(n_iter):
        perm = rng.permutation(all_idx)
        pos = 0
        scores = []
        for size in valid_sizes:
            group_idx = perm[pos : pos + size]
            pos += size
            score = mean_pairwise_cosine(embeddings[group_idx])
            if score is not None:
                scores.append(score)
        if scores:
            results.append(float(np.mean(scores)))
    return results


def run_field_coherence() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    axial_embeddings, axial_meta = load_feature("axial_meaning_embeddings")
    tri_roots = load_triliteral_roots()
    tri_to_index = {tri_root: i for i, tri_root in enumerate(axial_meta["entity_ids"])}

    families: dict[str, list[str]] = {}
    for record in tri_roots:
        families.setdefault(record.binary_root, []).append(record.tri_root)

    rows: list[dict] = []
    family_sizes: list[int] = []
    for binary_root, members in families.items():
        member_idx = [tri_to_index[root] for root in members if root in tri_to_index]
        family_sizes.append(len(member_idx))
        if len(member_idx) < 2:
            continue
        coherence = mean_pairwise_cosine(axial_embeddings[np.asarray(member_idx)])
        rows.append(
            {
                "binary_root": binary_root,
                "n_members": len(member_idx),
                "coherence": round(float(coherence), 6) if coherence is not None else None,
                "members": members,
            }
        )

    rows.sort(key=lambda item: float(item["coherence"]), reverse=True)
    with (OUTPUT_DIR / "field_coherence.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    real_scores = np.array([float(row["coherence"]) for row in rows], dtype=np.float32)
    baseline_scores = np.array(compute_random_baseline(axial_embeddings, family_sizes), dtype=np.float32)
    summary = {
        "real_mean": round(float(np.mean(real_scores)), 6),
        "real_std": round(float(np.std(real_scores)), 6),
        "baseline_mean": round(float(np.mean(baseline_scores)), 6),
        "baseline_std": round(float(np.std(baseline_scores)), 6),
        "families_scored": len(rows),
        "baseline_iterations": int(baseline_scores.size),
        "passes_two_sigma": bool(float(np.mean(real_scores)) > float(np.mean(baseline_scores) + 2 * np.std(baseline_scores))),
    }
    (OUTPUT_DIR / "coherence_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    top_bottom = {"top_20": rows[:20], "bottom_20": list(reversed(rows[-20:]))}
    (OUTPUT_DIR / "top_bottom_20.json").write_text(json.dumps(top_bottom, ensure_ascii=False, indent=2), encoding="utf-8")
    plot_distribution(real_scores, "Binary Root Field Coherence", OUTPUT_DIR / "coherence_distribution.png", bins=40)
    return summary


def main() -> int:
    config = ExperimentConfig(
        id="2.3",
        name="field_coherence",
        hypotheses=["H2"],
        required_features=["axial_meaning_embeddings"],
        run_fn=run_field_coherence,
    )
    result = run_experiment(config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
