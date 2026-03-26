# ACTIVE: maintained Axis 6 meaning-predictor experiment with direct test coverage.
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor

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


def infer_added_letter_and_position(tri_root: str, binary_root: str) -> tuple[str, int] | None:
    tri = canonical_tri_root(tri_root)
    if tri is None:
        return None
    binary = (binary_root or "").translate(NORMALIZE_MAP)
    if len(binary) != 2:
        return None
    if tri[0] == binary[0] and tri[1] == binary[1]:
        return tri[2], 3
    if tri[0] == binary[0] and tri[2] == binary[1]:
        return tri[1], 2
    if tri[1] == binary[0] and tri[2] == binary[1]:
        return tri[0], 1
    return None


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = np.linalg.norm(a, axis=1, keepdims=True)
    b_norm = np.linalg.norm(b, axis=1, keepdims=True)
    a_norm[a_norm == 0] = 1.0
    b_norm[b_norm == 0] = 1.0
    return np.sum((a / a_norm) * (b / b_norm), axis=1)


def position_one_hot(position: int) -> np.ndarray:
    vec = np.zeros(3, dtype=np.float32)
    if 1 <= position <= 3:
        vec[position - 1] = 1.0
    return vec


def build_dataset() -> tuple[np.ndarray, np.ndarray, np.ndarray, list[dict]]:
    binary_embeddings, binary_meta = load_feature("binary_meaning_embeddings")
    axial_embeddings, axial_meta = load_feature("axial_meaning_embeddings")
    letter_embeddings, letter_meta = load_feature("letter_embeddings")

    binary_index = {root: i for i, root in enumerate(binary_meta["entity_ids"])}
    axial_index = {root: i for i, root in enumerate(axial_meta["entity_ids"])}
    letter_index = {letter.translate(NORMALIZE_MAP): i for i, letter in enumerate(letter_meta["entity_ids"])}

    binary_only = []
    with_letter = []
    with_letter_position = []
    targets = []
    rows = []
    for record in load_triliteral_roots():
        inferred = infer_added_letter_and_position(record.tri_root, record.binary_root)
        if inferred is None:
            continue
        added_letter, position = inferred
        if record.binary_root not in binary_index or record.tri_root not in axial_index or added_letter not in letter_index:
            continue
        binary_vec = binary_embeddings[binary_index[record.binary_root]]
        letter_vec = letter_embeddings[letter_index[added_letter]]
        pos_vec = position_one_hot(position)
        target_vec = axial_embeddings[axial_index[record.tri_root]]
        binary_only.append(binary_vec)
        with_letter.append(np.concatenate([binary_vec, letter_vec], axis=0))
        with_letter_position.append(np.concatenate([binary_vec, letter_vec, pos_vec], axis=0))
        targets.append(target_vec)
        rows.append(
            {
                "tri_root": record.tri_root,
                "binary_root": record.binary_root,
                "added_letter": added_letter,
                "position": position,
            }
        )

    return (
        np.asarray(binary_only, dtype=np.float32),
        np.asarray(with_letter, dtype=np.float32),
        np.asarray(with_letter_position, dtype=np.float32),
        np.asarray(targets, dtype=np.float32),
        rows,
    )


def run_regressor(x: np.ndarray, y: np.ndarray, *, random_state: int = 42) -> tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    train_idx, test_idx = train_test_split(np.arange(x.shape[0]), test_size=0.2, random_state=random_state)
    x_train = x[train_idx]
    x_test = x[test_idx]
    y_train = y[train_idx]
    y_test = y[test_idx]
    regressor = MLPRegressor(
        hidden_layer_sizes=(256, 128),
        activation="relu",
        solver="adam",
        max_iter=400,
        early_stopping=True,
        random_state=random_state,
    )
    regressor.fit(x_train, y_train)
    pred = regressor.predict(x_test).astype(np.float32)
    sims = cosine_similarity(pred, y_test)
    return float(np.mean(sims)), sims, test_idx, pred


def run_meaning_predictor() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    x_binary, x_letter, x_letter_position, y, rows = build_dataset()

    datasets = {
        "binary_only": x_binary,
        "binary_plus_letter": x_letter,
        "binary_plus_letter_plus_position": x_letter_position,
    }
    metrics = {}
    detailed_rows = []
    best_name = None
    best_score = -1.0
    best_test_idx = None
    best_pred = None
    for name, features in datasets.items():
        mean_cosine, sims, test_idx, pred = run_regressor(features, y)
        metrics[name] = round(mean_cosine, 6)
        if mean_cosine > best_score:
            best_score = mean_cosine
            best_name = name
            best_test_idx = test_idx
            best_pred = pred

    assert best_name is not None and best_test_idx is not None and best_pred is not None
    for row_idx, pred_vec, sim in zip(best_test_idx.tolist(), best_pred, cosine_similarity(best_pred, y[best_test_idx])):
        row = dict(rows[row_idx])
        row["cosine_similarity"] = round(float(sim), 6)
        row["model_variant"] = best_name
        detailed_rows.append(row)

    detailed_rows.sort(key=lambda item: item["cosine_similarity"], reverse=True)
    with (OUTPUT_DIR / "meaning_predictor_predictions.jsonl").open("w", encoding="utf-8") as handle:
        for row in detailed_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "n_examples": int(y.shape[0]),
        "test_fraction": 0.2,
        "variants": metrics,
        "best_variant": best_name,
        "best_mean_cosine": round(float(best_score), 6),
        "supports_h12": bool(best_score > 0.6),
    }
    (OUTPUT_DIR / "meaning_predictor_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    config = ExperimentConfig(
        id="6.1",
        name="meaning_predictor",
        hypotheses=["H12"],
        required_features=["binary_meaning_embeddings", "letter_embeddings", "axial_meaning_embeddings"],
        run_fn=run_meaning_predictor,
    )
    result = run_experiment(config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
