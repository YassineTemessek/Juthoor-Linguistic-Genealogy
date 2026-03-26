# ACTIVE: maintained Axis 4 binary-metathesis experiment with direct test coverage.
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

from juthoor_arabicgenome_lv1.core.loaders import load_binary_roots  # noqa: E402
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


_statistics = _load_common_module("stat_helpers")
_visualization = _load_common_module("visualization")
wilcoxon_rank_sum = _statistics.wilcoxon_rank_sum
cohens_d = _statistics.cohens_d
plot_violin = _visualization.plot_violin


OUTPUT_DIR = REPO_ROOT / "outputs" / "research_factory" / "axis4"


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def build_metathesis_pairs(binary_roots: list[str]) -> list[tuple[str, str]]:
    binary_set = {root for root in binary_roots if len(root) == 2 and root[0] != root[1]}
    return sorted({tuple(sorted((root, root[::-1]))) for root in binary_set if root[::-1] in binary_set})


def sample_control_pairs(binary_roots: list[str], n_pairs: int, *, random_state: int = 42) -> list[tuple[str, str]]:
    rng = np.random.default_rng(random_state)
    candidates = sorted({root for root in binary_roots if len(root) == 2})
    metathesis = {tuple(sorted((root, root[::-1]))) for root in candidates if root[::-1] in candidates}
    pool = [
        (a, b)
        for idx, a in enumerate(candidates)
        for b in candidates[idx + 1 :]
        if tuple(sorted((a, b))) not in metathesis
    ]
    chosen_idx = rng.choice(len(pool), size=n_pairs, replace=False)
    return [pool[i] for i in sorted(chosen_idx)]


def classify_similarity(score: float) -> str:
    if score > 0.7:
        return "similar"
    if score < 0.3:
        return "divergent"
    return "middle"


def run_binary_metathesis() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    binary_embeddings, binary_meta = load_feature("binary_meaning_embeddings")
    binary_map = {record.binary_root: record for record in load_binary_roots()}
    emb_map = {root: binary_embeddings[idx] for idx, root in enumerate(binary_meta["entity_ids"])}

    pairs = build_metathesis_pairs(list(binary_map))
    controls = sample_control_pairs(list(binary_map), len(pairs))

    real_rows = []
    real_scores = []
    for a, b in pairs:
        score = cosine(emb_map[a], emb_map[b])
        real_scores.append(score)
        real_rows.append(
            {
                "pair_type": "metathesis",
                "binary_root_a": a,
                "binary_root_b": b,
                "meaning_a": binary_map[a].meaning,
                "meaning_b": binary_map[b].meaning,
                "cosine_similarity": round(score, 6),
                "classification": classify_similarity(score),
            }
        )

    control_rows = []
    control_scores = []
    for a, b in controls:
        score = cosine(emb_map[a], emb_map[b])
        control_scores.append(score)
        control_rows.append(
            {
                "pair_type": "control",
                "binary_root_a": a,
                "binary_root_b": b,
                "meaning_a": binary_map[a].meaning,
                "meaning_b": binary_map[b].meaning,
                "cosine_similarity": round(score, 6),
                "classification": classify_similarity(score),
            }
        )

    with (OUTPUT_DIR / "metathesis_analysis.jsonl").open("w", encoding="utf-8") as handle:
        for row in real_rows + control_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    plot_violin({"metathesis": real_scores, "control": control_scores}, "Binary Metathesis vs Random Control", OUTPUT_DIR / "violin_plot.png")
    statistic, p_value = wilcoxon_rank_sum(real_scores, control_scores)
    counts = {
        "metathesis": {
            "similar": sum(1 for row in real_rows if row["classification"] == "similar"),
            "middle": sum(1 for row in real_rows if row["classification"] == "middle"),
            "divergent": sum(1 for row in real_rows if row["classification"] == "divergent"),
        },
        "control": {
            "similar": sum(1 for row in control_rows if row["classification"] == "similar"),
            "middle": sum(1 for row in control_rows if row["classification"] == "middle"),
            "divergent": sum(1 for row in control_rows if row["classification"] == "divergent"),
        },
        "n_pairs": len(pairs),
        "mean_metathesis": round(float(np.mean(real_scores)), 6),
        "mean_control": round(float(np.mean(control_scores)), 6),
        "effect_size_d": round(float(cohens_d(real_scores, control_scores)), 6),
        "rank_sum_statistic": round(float(statistic), 6),
        "p_value": round(float(p_value), 6),
    }
    (OUTPUT_DIR / "classification_counts.json").write_text(json.dumps(counts, ensure_ascii=False, indent=2), encoding="utf-8")
    return counts


def main() -> int:
    config = ExperimentConfig(
        id="4.1",
        name="binary_metathesis",
        hypotheses=["H4", "H5"],
        required_features=["binary_meaning_embeddings"],
        run_fn=run_binary_metathesis,
    )
    result = run_experiment(config)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
