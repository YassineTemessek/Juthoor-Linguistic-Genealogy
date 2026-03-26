# ACTIVE: maintained Axis 3 modifier-personality experiment with direct test coverage.
from __future__ import annotations

import json
import re
import sys
import importlib.util
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
LV1_SRC = REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "src"
if str(LV1_SRC) not in sys.path:
    sys.path.append(str(LV1_SRC))

from juthoor_arabicgenome_lv1.core.loaders import load_letters, load_triliteral_roots  # noqa: E402
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
plot_heatmap = _visualization.plot_heatmap
plot_scatter_with_labels = _visualization.plot_scatter_with_labels


OUTPUT_DIR = REPO_ROOT / "outputs" / "research_factory" / "axis3"
ARABIC_LETTERS = "ءابتثجحخدذرزسشصضطظعغفقكلمنهويى"
ARABIC_RE = re.compile(f"[{ARABIC_LETTERS}]")
SPLIT_RE = re.compile(r"(?:/|-|←|\s)+")
NORMALIZE_MAP = str.maketrans({"أ": "ء", "إ": "ء", "آ": "ء", "ى": "ي"})


def canonical_added_letter(tri_root: str) -> str | None:
    candidate = SPLIT_RE.split(tri_root.strip())[0].translate(NORMALIZE_MAP)
    letters = ARABIC_RE.findall(candidate)
    if not letters:
        return None
    return letters[-1]


def pairwise_consistency(vectors: np.ndarray) -> float | None:
    if vectors.shape[0] < 2:
        return None
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    unit = vectors / norms
    sim = unit @ unit.T
    idx = np.triu_indices(sim.shape[0], k=1)
    return float(np.mean(sim[idx]))


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def shuffled_consistency_baseline(
    grouped_vectors: dict[str, list[np.ndarray]],
    *,
    n_iter: int = 500,
    random_state: int = 42,
) -> tuple[float, float, float]:
    rng = np.random.default_rng(random_state)
    counts = {letter: len(vectors) for letter, vectors in grouped_vectors.items() if vectors}
    all_vectors = [vector for vectors in grouped_vectors.values() for vector in vectors]
    if not all_vectors:
        return 0.0, 0.0, 1.0
    matrix = np.asarray(all_vectors, dtype=np.float32)
    scores = []
    for _ in range(n_iter):
        perm = matrix[rng.permutation(matrix.shape[0])]
        pos = 0
        iter_scores = []
        for count in counts.values():
            group = perm[pos : pos + count]
            pos += count
            consistency = pairwise_consistency(group)
            if consistency is not None:
                iter_scores.append(consistency)
        if iter_scores:
            scores.append(float(np.mean(iter_scores)))
    score_arr = np.asarray(scores, dtype=np.float32)
    observed_placeholder = 0.0
    return float(np.mean(score_arr)), float(np.std(score_arr)), observed_placeholder


def run_modifier_personality() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    letter_embeddings, letter_meta = load_feature("letter_embeddings")
    binary_embeddings, binary_meta = load_feature("binary_meaning_embeddings")
    axial_embeddings, axial_meta = load_feature("axial_meaning_embeddings")

    tri_to_idx = {item: i for i, item in enumerate(axial_meta["entity_ids"])}
    binary_to_idx = {item: i for i, item in enumerate(binary_meta["entity_ids"])}
    letter_to_idx = {item.translate(NORMALIZE_MAP): i for i, item in enumerate(letter_meta["entity_ids"])}
    letter_name_map = {record.letter.translate(NORMALIZE_MAP): record.letter_name for record in load_letters()}

    grouped_vectors: dict[str, list[np.ndarray]] = {letter: [] for letter in letter_to_idx}
    grouped_roots: dict[str, list[str]] = {letter: [] for letter in letter_to_idx}
    for record in load_triliteral_roots():
        added = canonical_added_letter(record.tri_root)
        if added is None or added not in letter_to_idx:
            continue
        if record.tri_root not in tri_to_idx or record.binary_root not in binary_to_idx:
            continue
        modifier = axial_embeddings[tri_to_idx[record.tri_root]] - binary_embeddings[binary_to_idx[record.binary_root]]
        grouped_vectors[added].append(modifier)
        grouped_roots[added].append(record.tri_root)

    profile_rows: list[dict] = []
    personality_vectors: list[np.ndarray] = []
    labels: list[str] = []
    consistencies: list[float] = []
    alignments: list[float] = []
    for letter in letter_meta["entity_ids"]:
        norm_letter = str(letter).translate(NORMALIZE_MAP)
        vectors = np.asarray(grouped_vectors.get(norm_letter, []), dtype=np.float32)
        if vectors.size == 0:
            personality = np.zeros(letter_embeddings.shape[1], dtype=np.float32)
            consistency = None
            alignment = 0.0
        else:
            personality = np.mean(vectors, axis=0)
            consistency = pairwise_consistency(vectors)
            alignment = cosine(personality, letter_embeddings[letter_to_idx[norm_letter]])
        personality_vectors.append(personality)
        labels.append(letter)
        consistencies.append(float(consistency) if consistency is not None else 0.0)
        alignments.append(float(alignment))
        profile_rows.append(
            {
                "letter": letter,
                "letter_name": letter_name_map.get(norm_letter, ""),
                "n_roots": len(grouped_roots.get(norm_letter, [])),
                "consistency": round(float(consistency), 6) if consistency is not None else None,
                "alignment_to_letter_meaning": round(float(alignment), 6),
                "sample_roots": grouped_roots.get(norm_letter, [])[:10],
            }
        )

    with (OUTPUT_DIR / "modifier_profiles.jsonl").open("w", encoding="utf-8") as handle:
        for row in profile_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    personality_matrix = np.asarray(personality_vectors, dtype=np.float32)
    norms = np.linalg.norm(personality_matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    personality_unit = personality_matrix / norms
    personality_sim = personality_unit @ personality_unit.T
    plot_heatmap(personality_sim, labels, "Modifier Personality Similarity", OUTPUT_DIR / "modifier_heatmap.png")
    plot_scatter_with_labels(consistencies, alignments, labels, "Modifier Consistency vs Letter Alignment", OUTPUT_DIR / "personality_vs_letter_meaning.png")

    consistencies_non_null = [row["consistency"] for row in profile_rows if row["consistency"] is not None]
    observed_mean = float(np.mean(consistencies_non_null)) if consistencies_non_null else 0.0
    baseline_mean, baseline_std, _ = shuffled_consistency_baseline(grouped_vectors)
    z_score = (observed_mean - baseline_mean) / baseline_std if baseline_std > 0 else 0.0
    summary = {
        "letters_profiled": len(profile_rows),
        "letters_with_data": sum(1 for row in profile_rows if row["n_roots"] > 0),
        "mean_consistency": round(observed_mean, 6) if consistencies_non_null else None,
        "letters_above_0_5": sum(1 for row in profile_rows if row["consistency"] is not None and float(row["consistency"]) > 0.5),
        "share_above_0_5": round(
            float(sum(1 for row in profile_rows if row["consistency"] is not None and float(row["consistency"]) > 0.5) / max(1, len(consistencies_non_null))),
            6,
        ) if consistencies_non_null else 0.0,
        "shuffled_baseline_mean": round(baseline_mean, 6),
        "shuffled_baseline_std": round(baseline_std, 6),
        "z_score_vs_shuffled": round(float(z_score), 6),
    }
    (OUTPUT_DIR / "consistency_scores.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    config = ExperimentConfig(
        id="3.1",
        name="modifier_personality",
        hypotheses=["H3"],
        required_features=["letter_embeddings", "binary_meaning_embeddings", "axial_meaning_embeddings"],
        run_fn=run_modifier_personality,
    )
    result = run_experiment(config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
