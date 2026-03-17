from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
LV1_SRC = REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "src"
if str(LV1_SRC) not in sys.path:
    sys.path.append(str(LV1_SRC))

from juthoor_arabicgenome_lv1.core.loaders import load_triliteral_roots  # noqa: E402
from juthoor_arabicgenome_lv1.factory.experiment_runner import ExperimentConfig, run_experiment  # noqa: E402
from juthoor_arabicgenome_lv1.factory.feature_store import load_feature  # noqa: E402


OUTPUT_DIR = REPO_ROOT / "outputs" / "research_factory" / "axis3"
ARABIC_RE = re.compile(r"[ءابتثجحخدذرزسشصضطظعغفقكلمنهويى]")
SPLIT_RE = re.compile(r"(?:/|-|←|\s)+")
NORMALIZE_MAP = str.maketrans({"أ": "ء", "إ": "ء", "آ": "ء", "ى": "ي"})


def canonical_tri_root(value: str) -> str | None:
    candidate = SPLIT_RE.split(value.strip())[0].translate(NORMALIZE_MAP)
    letters = ARABIC_RE.findall(candidate)
    if len(letters) != 3:
        return None
    return "".join(letters)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    a_norm = np.linalg.norm(a, axis=1, keepdims=True)
    b_norm = np.linalg.norm(b, axis=1, keepdims=True)
    a_norm[a_norm == 0] = 1.0
    b_norm[b_norm == 0] = 1.0
    return np.sum((a / a_norm) * (b / b_norm), axis=1)


def build_compositional_dataset() -> tuple[np.ndarray, np.ndarray, np.ndarray, list[dict]]:
    letter_embeddings, letter_meta = load_feature("letter_embeddings")
    binary_embeddings, binary_meta = load_feature("binary_meaning_embeddings")
    axial_embeddings, axial_meta = load_feature("axial_meaning_embeddings")
    letter_index = {letter.translate(NORMALIZE_MAP): i for i, letter in enumerate(letter_meta["entity_ids"])}
    binary_index = {root: i for i, root in enumerate(binary_meta["entity_ids"])}
    axial_index = {root: i for i, root in enumerate(axial_meta["entity_ids"])}

    additive_rows = []
    binary_rows = []
    target_rows = []
    meta_rows: list[dict] = []
    for record in load_triliteral_roots():
        tri_root = canonical_tri_root(record.tri_root)
        if tri_root is None:
            continue
        if record.tri_root not in axial_index or record.binary_root not in binary_index:
            continue
        if any(letter not in letter_index for letter in tri_root):
            continue
        letter_vecs = np.stack([letter_embeddings[letter_index[letter]] for letter in tri_root], axis=0)
        additive_rows.append(np.sum(letter_vecs, axis=0))
        binary_rows.append(binary_embeddings[binary_index[record.binary_root]])
        target_rows.append(axial_embeddings[axial_index[record.tri_root]])
        meta_rows.append(
            {
                "tri_root": record.tri_root,
                "binary_root": record.binary_root,
                "letters": list(tri_root),
            }
        )

    return (
        np.asarray(additive_rows, dtype=np.float32),
        np.asarray(binary_rows, dtype=np.float32),
        np.asarray(target_rows, dtype=np.float32),
        meta_rows,
    )


def shuffled_baseline(additive: np.ndarray, targets: np.ndarray, *, n_perm: int = 1000, random_state: int = 0) -> np.ndarray:
    rng = np.random.default_rng(random_state)
    scores = np.empty(n_perm, dtype=np.float32)
    indices = np.arange(targets.shape[0])
    for i in range(n_perm):
        scores[i] = float(np.mean(cosine_similarity(additive, targets[rng.permutation(indices)])))
    return scores


def run_compositionality() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    additive, binary_only, targets, meta_rows = build_compositional_dataset()
    additive_cos = cosine_similarity(additive, targets)
    binary_cos = cosine_similarity(binary_only, targets)
    shuffled = shuffled_baseline(additive, targets)

    detailed_rows = []
    for meta, add_sim, bin_sim in zip(meta_rows, additive_cos.tolist(), binary_cos.tolist()):
        row = dict(meta)
        row["additive_cosine"] = round(float(add_sim), 6)
        row["binary_only_cosine"] = round(float(bin_sim), 6)
        row["improvement_over_binary"] = round(float(add_sim - bin_sim), 6)
        detailed_rows.append(row)
    detailed_rows.sort(key=lambda item: item["additive_cosine"], reverse=True)

    with (OUTPUT_DIR / "compositionality_rows.jsonl").open("w", encoding="utf-8") as handle:
        for row in detailed_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    observed = float(np.mean(additive_cos))
    shuffle_mean = float(np.mean(shuffled))
    p_value = float((np.sum(shuffled >= observed) + 1) / (shuffled.size + 1))
    summary = {
        "n_examples": int(targets.shape[0]),
        "additive_mean_cosine": round(observed, 6),
        "binary_only_mean_cosine": round(float(np.mean(binary_cos)), 6),
        "mean_improvement_over_binary": round(float(np.mean(additive_cos - binary_cos)), 6),
        "shuffle_mean_cosine": round(shuffle_mean, 6),
        "shuffle_std": round(float(np.std(shuffled)), 6),
        "permutation_p_value": round(p_value, 6),
        "supports_compositional_signal": bool(observed > shuffle_mean and p_value < 0.05),
        "supports_full_compositionality": bool(observed >= 0.65 and observed > float(np.mean(binary_cos)) + 0.05 and p_value < 0.05),
    }
    (OUTPUT_DIR / "compositionality_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    config = ExperimentConfig(
        id="3.2",
        name="compositionality",
        hypotheses=["H10"],
        required_features=["letter_embeddings", "binary_meaning_embeddings", "axial_meaning_embeddings"],
        run_fn=run_compositionality,
    )
    result = run_experiment(config)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
