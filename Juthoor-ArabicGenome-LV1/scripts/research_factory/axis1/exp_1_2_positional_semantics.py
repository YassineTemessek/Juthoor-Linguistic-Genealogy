# ACTIVE: maintained Axis 1 positional semantics experiment with direct test coverage.
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
LV1_SRC = REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "src"
if str(LV1_SRC) not in sys.path:
    sys.path.append(str(LV1_SRC))

from juthoor_arabicgenome_lv1.core.loaders import load_letters, load_triliteral_roots  # noqa: E402
from juthoor_arabicgenome_lv1.factory.experiment_runner import ExperimentConfig, run_experiment  # noqa: E402
from juthoor_arabicgenome_lv1.factory.feature_store import load_feature  # noqa: E402

ARABIC_RE = re.compile(r"[ءابتثجحخدذرزسشصضطظعغفقكلمنهويى]")
SPLIT_RE = re.compile(r"(?:/|-|←|\s)+")
NORMALIZE_MAP = str.maketrans({"أ": "ء", "إ": "ء", "آ": "ء", "ى": "ي"})
OUTPUT_DIR = REPO_ROOT / "outputs" / "research_factory" / "axis1"


def canonical_tri_root(raw: str) -> str | None:
    candidate = SPLIT_RE.split(raw.strip())[0]
    candidate = candidate.translate(NORMALIZE_MAP)
    letters = ARABIC_RE.findall(candidate)
    if len(letters) != 3:
        return None
    return "".join(letters)


def pairwise_cosine_values(vectors: np.ndarray) -> np.ndarray:
    arr = np.asarray(vectors, dtype=np.float32)
    if arr.shape[0] < 2:
        return np.array([], dtype=np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    unit = arr / norms
    sim = unit @ unit.T
    idx = np.triu_indices(sim.shape[0], k=1)
    return np.asarray(sim[idx], dtype=np.float32)


def mean_or_none(values: np.ndarray) -> float | None:
    if values.size == 0:
        return None
    return float(np.mean(values))


def run_positional_semantics() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    axial_embeddings, axial_meta = load_feature("axial_meaning_embeddings")
    tri_to_idx = {tri_root: i for i, tri_root in enumerate(axial_meta["entity_ids"])}
    group_indices: dict[tuple[str, int], list[int]] = defaultdict(list)
    for record in load_triliteral_roots():
        tri_root = canonical_tri_root(record.tri_root)
        if tri_root is None or record.tri_root not in tri_to_idx:
            continue
        for position, letter in enumerate(tri_root, start=1):
            group_indices[(letter, position)].append(tri_to_idx[record.tri_root])

    letter_rows = []
    summary_rows = []
    letters = [record.letter.translate(NORMALIZE_MAP) for record in load_letters()]
    name_map = {record.letter.translate(NORMALIZE_MAP): record.letter_name for record in load_letters()}

    statistics_path = REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "scripts" / "research_factory" / "common" / "stat_helpers.py"
    import importlib.util

    spec = importlib.util.spec_from_file_location("rf_common_stat_helpers_axis1_2", statistics_path)
    assert spec and spec.loader
    statistics_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(statistics_module)
    kruskal_wallis = statistics_module.kruskal_wallis

    for letter in letters:
        position_distributions: list[np.ndarray] = []
        letter_payload = {
            "letter": letter,
            "letter_name": name_map.get(letter, ""),
            "positions": {},
        }
        for position in (1, 2, 3):
            idx = group_indices.get((letter, position), [])
            pairwise = pairwise_cosine_values(axial_embeddings[np.asarray(idx)]) if idx else np.array([], dtype=np.float32)
            position_distributions.append(pairwise)
            letter_payload["positions"][str(position)] = {
                "n_roots": len(idx),
                "n_pairwise": int(pairwise.size),
                "coherence": round(float(np.mean(pairwise)), 6) if pairwise.size else None,
            }

        valid_groups = [group for group in position_distributions if group.size > 0]
        if len(valid_groups) >= 2:
            statistic, p_value = kruskal_wallis(*valid_groups)
            letter_payload["kruskal_statistic"] = round(float(statistic), 6)
            letter_payload["p_value"] = round(float(p_value), 6)
        else:
            letter_payload["kruskal_statistic"] = None
            letter_payload["p_value"] = None

        letter_rows.append(letter_payload)
        for position in (1, 2, 3):
            coherence = letter_payload["positions"][str(position)]["coherence"]
            if coherence is not None:
                summary_rows.append(coherence)

    with (OUTPUT_DIR / "positional_semantics.jsonl").open("w", encoding="utf-8") as handle:
        for row in letter_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    significant_letters = [
        row["letter"]
        for row in letter_rows
        if row["p_value"] is not None and float(row["p_value"]) < 0.05
    ]
    summary = {
        "letters_profiled": len(letter_rows),
        "letters_with_significant_position_effect": len(significant_letters),
        "significant_letters": significant_letters,
        "mean_position_coherence": round(float(np.mean(np.asarray(summary_rows, dtype=np.float32))), 6) if summary_rows else None,
    }
    (OUTPUT_DIR / "positional_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    config = ExperimentConfig(
        id="1.2",
        name="positional_semantics",
        hypotheses=["H8"],
        required_features=["axial_meaning_embeddings"],
        run_fn=run_positional_semantics,
    )
    result = run_experiment(config)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
