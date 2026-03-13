"""Build articulatory feature vectors for 28 Arabic letters.

Loads makhaarij.json (place of articulation) and sifaat.json (binary features),
encodes each letter as [one-hot makhraj | binary sifaat], and saves to the
feature store as 'articulatory_vectors'.

Output shape: (28, 25) = 15 makhraj one-hot + 10 sifaat binary.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from juthoor_arabicgenome_lv1.factory.feature_store import save_feature

_LV1_ROOT = Path(__file__).resolve().parents[3]
_PHONETICS_DIR = _LV1_ROOT / "resources" / "phonetics"

SIFAAT_NAMES = [
    "jahr", "shidda", "itbaq", "isti3la", "qalqala",
    "safeer", "ghunna", "inhiraf", "takrir", "istitala",
]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_articulatory_matrix(
    makhaarij_path: Path | None = None,
    sifaat_path: Path | None = None,
) -> tuple[np.ndarray, list[str], list[str]]:
    """Build the articulatory feature matrix.

    Returns:
        (matrix, letters, feature_names) where:
        - matrix has shape (28, num_makhaarij + num_sifaat)
        - letters is the ordered list of 28 Arabic letters
        - feature_names lists every column name
    """
    makhaarij_path = makhaarij_path or _PHONETICS_DIR / "makhaarij.json"
    sifaat_path = sifaat_path or _PHONETICS_DIR / "sifaat.json"

    makhaarij = _load_json(makhaarij_path)
    sifaat = _load_json(sifaat_path)

    # Use makhaarij key order as canonical letter order
    letters = list(makhaarij.keys())
    assert len(letters) == 28, f"Expected 28 letters, got {len(letters)}"

    # Verify same 28 letters in both files
    sifaat_letters = set(sifaat.keys())
    makhaarij_letters = set(letters)
    missing_in_sifaat = makhaarij_letters - sifaat_letters
    missing_in_makhaarij = sifaat_letters - makhaarij_letters
    if missing_in_sifaat or missing_in_makhaarij:
        raise ValueError(
            f"Letter mismatch: missing in sifaat={missing_in_sifaat}, "
            f"missing in makhaarij={missing_in_makhaarij}"
        )

    # Determine unique makhraj IDs (sorted)
    unique_ids = sorted({v["makhraj_id"] for v in makhaarij.values()})
    id_to_col = {mid: i for i, mid in enumerate(unique_ids)}
    num_makhaarij = len(unique_ids)

    # Build makhraj feature names from English names
    id_to_en = {}
    for v in makhaarij.values():
        id_to_en[v["makhraj_id"]] = v["makhraj_en"]
    makhraj_feature_names = [f"makhraj_{id_to_en[mid]}" for mid in unique_ids]

    # Build matrix
    num_sifaat = len(SIFAAT_NAMES)
    total_features = num_makhaarij + num_sifaat
    matrix = np.zeros((28, total_features), dtype=np.float32)

    for i, letter in enumerate(letters):
        # One-hot makhraj
        mid = makhaarij[letter]["makhraj_id"]
        matrix[i, id_to_col[mid]] = 1.0

        # Binary sifaat
        letter_sifaat = sifaat[letter]
        for j, feat_name in enumerate(SIFAAT_NAMES):
            matrix[i, num_makhaarij + j] = float(letter_sifaat[feat_name])

    feature_names = makhraj_feature_names + SIFAAT_NAMES
    return matrix, letters, feature_names


def main() -> None:
    """Build and save articulatory vectors to the feature store."""
    matrix, letters, feature_names = build_articulatory_matrix()

    meta = {
        "entity_ids": letters,
        "feature_names": feature_names,
        "model_used": "manual_phonetic_encoding",
        "makhraj_count": len([f for f in feature_names if f.startswith("makhraj_")]),
        "sifaat_count": len(SIFAAT_NAMES),
    }

    save_feature("articulatory_vectors", matrix, meta)
    print(f"Saved articulatory_vectors: shape {matrix.shape}")
    print(f"  {meta['makhraj_count']} makhraj features + {meta['sifaat_count']} sifaat features")
    print(f"  Letters: {len(letters)} entries")


if __name__ == "__main__":
    main()
