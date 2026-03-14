from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier

REPO_ROOT = Path(__file__).resolve().parents[4]
LV1_SRC = REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "src"
if str(LV1_SRC) not in sys.path:
    sys.path.append(str(LV1_SRC))

from juthoor_arabicgenome_lv1.core.loaders import load_binary_roots, load_triliteral_roots  # noqa: E402
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


def generate_candidate(binary_root: str, added_letter: str, position: int) -> str:
    if position == 1:
        return added_letter + binary_root
    if position == 2:
        return binary_root[0] + added_letter + binary_root[1]
    return binary_root + added_letter


def position_one_hot(position: int) -> np.ndarray:
    vec = np.zeros(3, dtype=np.float32)
    vec[position - 1] = 1.0
    return vec


def build_dataset() -> tuple[np.ndarray, np.ndarray, list[dict]]:
    binary_embeddings, binary_meta = load_feature("binary_meaning_embeddings")
    letter_embeddings, letter_meta = load_feature("letter_embeddings")
    binary_index = {root.translate(NORMALIZE_MAP): i for i, root in enumerate(binary_meta["entity_ids"])}
    letter_index = {letter.translate(NORMALIZE_MAP): i for i, letter in enumerate(letter_meta["entity_ids"])}

    observed_tri = {canonical_tri_root(record.tri_root) for record in load_triliteral_roots()}
    observed_tri.discard(None)

    letters = sorted(letter_index)
    binaries = sorted({record.binary_root.translate(NORMALIZE_MAP) for record in load_binary_roots() if len(record.binary_root) == 2})
    x = []
    y = []
    rows = []
    for binary in binaries:
        if binary not in binary_index:
            continue
        binary_vec = binary_embeddings[binary_index[binary]]
        for added_letter in letters:
            letter_vec = letter_embeddings[letter_index[added_letter]]
            for position in (1, 2, 3):
                candidate = generate_candidate(binary, added_letter, position)
                features = np.concatenate([binary_vec, letter_vec, position_one_hot(position)], axis=0)
                x.append(features)
                exists = 1 if candidate in observed_tri else 0
                y.append(exists)
                rows.append(
                    {
                        "binary_root": binary,
                        "added_letter": added_letter,
                        "position": position,
                        "candidate_root": candidate,
                        "exists": exists,
                    }
                )
    return np.asarray(x, dtype=np.float32), np.asarray(y, dtype=np.int32), rows


def run_phantom_roots() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    x, y, rows = build_dataset()
    train_idx, test_idx = train_test_split(np.arange(x.shape[0]), test_size=0.2, random_state=42, stratify=y)
    clf = MLPClassifier(
        hidden_layer_sizes=(256, 128),
        activation="relu",
        solver="adam",
        max_iter=300,
        early_stopping=True,
        random_state=42,
    )
    clf.fit(x[train_idx], y[train_idx])
    test_probs = clf.predict_proba(x[test_idx])[:, 1]
    auc = roc_auc_score(y[test_idx], test_probs)

    all_probs = clf.predict_proba(x)[:, 1]
    absent_rows = []
    for row, prob in zip(rows, all_probs.tolist()):
        if row["exists"]:
            continue
        payload = dict(row)
        payload["predicted_existence_probability"] = round(float(prob), 6)
        absent_rows.append(payload)
    absent_rows.sort(key=lambda item: item["predicted_existence_probability"], reverse=True)

    with (OUTPUT_DIR / "phantom_roots.jsonl").open("w", encoding="utf-8") as handle:
        for row in absent_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "n_candidates": int(x.shape[0]),
        "n_absent_candidates": int(sum(1 for row in rows if not row["exists"])),
        "test_auc": round(float(auc), 6),
        "supports_h12_generative": bool(float(auc) > 0.7),
        "top_20_phantom_roots": absent_rows[:20],
        "bottom_20_phantom_roots": list(reversed(absent_rows[-20:])),
    }
    (OUTPUT_DIR / "phantom_roots_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    config = ExperimentConfig(
        id="6.4",
        name="phantom_roots",
        hypotheses=["H12"],
        required_features=["binary_meaning_embeddings", "letter_embeddings"],
        run_fn=run_phantom_roots,
    )
    result = run_experiment(config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
