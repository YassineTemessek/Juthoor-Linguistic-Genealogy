# ACTIVE: maintained Axis 2 missing-combinations experiment with direct test coverage.
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

from juthoor_arabicgenome_lv1.core.loaders import load_binary_roots, load_letters  # noqa: E402
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
wilcoxon_rank_sum = _statistics.wilcoxon_rank_sum
cohens_d = _statistics.cohens_d


OUTPUT_DIR = REPO_ROOT / "outputs" / "research_factory" / "axis2"
NORMALIZE_MAP = str.maketrans({"أ": "ء", "إ": "ء", "آ": "ء", "ى": "ي"})


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def all_binary_pairs(letters: list[str]) -> list[str]:
    return [a + b for a in letters for b in letters]


def run_missing_combinations() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    letter_embeddings, letter_meta = load_feature("letter_embeddings")
    letter_index = {letter.translate(NORMALIZE_MAP): i for i, letter in enumerate(letter_meta["entity_ids"])}

    letters = [record.letter.translate(NORMALIZE_MAP) for record in load_letters()]
    observed = {record.binary_root.translate(NORMALIZE_MAP) for record in load_binary_roots()}
    all_pairs = all_binary_pairs(letters)
    missing = sorted(set(all_pairs) - observed)

    observed_scores = []
    missing_rows = []
    for root in sorted(observed):
        if root[0] not in letter_index or root[1] not in letter_index:
            continue
        score = cosine(letter_embeddings[letter_index[root[0]]], letter_embeddings[letter_index[root[1]]])
        observed_scores.append(score)

    for root in missing:
        if root[0] not in letter_index or root[1] not in letter_index:
            continue
        score = cosine(letter_embeddings[letter_index[root[0]]], letter_embeddings[letter_index[root[1]]])
        missing_rows.append({"binary_root": root, "compatibility_score": round(score, 6)})

    missing_rows.sort(key=lambda item: item["compatibility_score"])
    with (OUTPUT_DIR / "missing_combinations_analysis.jsonl").open("w", encoding="utf-8") as handle:
        for row in missing_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    missing_scores = [row["compatibility_score"] for row in missing_rows]
    statistic, p_value = wilcoxon_rank_sum(observed_scores, missing_scores)
    summary = {
        "n_letters": len(letters),
        "n_observed": len(observed_scores),
        "n_missing": len(missing_scores),
        "mean_observed_compatibility": round(float(np.mean(observed_scores)), 6),
        "mean_missing_compatibility": round(float(np.mean(missing_scores)), 6),
        "rank_sum_statistic": round(float(statistic), 6),
        "p_value": round(float(p_value), 6),
        "effect_size_d": round(float(cohens_d(observed_scores, missing_scores)), 6),
        "supports_h7": bool(float(np.mean(missing_scores)) < float(np.mean(observed_scores)) and float(p_value) < 0.05),
        "lowest_20_missing": missing_rows[:20],
        "highest_20_missing": list(reversed(missing_rows[-20:])),
    }
    (OUTPUT_DIR / "missing_combinations_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    config = ExperimentConfig(
        id="2.2",
        name="missing_combinations",
        hypotheses=["H7"],
        required_features=["letter_embeddings"],
        run_fn=run_missing_combinations,
    )
    result = run_experiment(config)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
