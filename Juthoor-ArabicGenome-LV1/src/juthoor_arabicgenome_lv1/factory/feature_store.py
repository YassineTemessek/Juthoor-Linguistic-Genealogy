"""Feature store for saving and loading numpy arrays with metadata.

Provides a simple key-value store backed by .npy + .meta.json file pairs
under outputs/research_factory/features/ relative to the LV1 package root.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# LV1 root: factory/feature_store.py -> factory/ -> juthoor_arabicgenome_lv1/ -> src/ -> LV1 root
_LV1_ROOT = Path(__file__).resolve().parents[4]
FEATURES_DIR = _LV1_ROOT / "outputs" / "research_factory" / "features"


def _ensure_dir(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)


def save_feature(name: str, array: np.ndarray, meta: dict, *, features_dir: Path | None = None) -> None:
    """Save a numpy array and metadata JSON to the feature store.

    Saves:
      - <features_dir>/<name>.npy
      - <features_dir>/<name>.meta.json

    Args:
        name: Feature identifier (no extension).
        array: Numpy array to persist.
        meta: Metadata dict. Should include entity_ids (list), model_used (str).
              timestamp and shape are added automatically if not present.
        features_dir: Override storage directory (used in tests).
    """
    store = features_dir if features_dir is not None else FEATURES_DIR
    _ensure_dir(store)

    # Augment metadata with auto-fields
    if "timestamp" not in meta:
        meta = {**meta, "timestamp": datetime.now(timezone.utc).isoformat()}
    if "shape" not in meta:
        meta = {**meta, "shape": list(array.shape)}

    npy_path = store / f"{name}.npy"
    meta_path = store / f"{name}.meta.json"

    np.save(str(npy_path), array)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def load_feature(name: str, *, features_dir: Path | None = None) -> tuple[np.ndarray, dict]:
    """Load a feature array and its metadata.

    Args:
        name: Feature identifier (no extension).
        features_dir: Override storage directory (used in tests).

    Returns:
        Tuple of (array, meta_dict).

    Raises:
        FileNotFoundError: If the feature does not exist in the store.
    """
    store = features_dir if features_dir is not None else FEATURES_DIR

    npy_path = store / f"{name}.npy"
    meta_path = store / f"{name}.meta.json"

    if not npy_path.exists():
        raise FileNotFoundError(f"Feature '{name}' not found in store: {npy_path}")

    array = np.load(str(npy_path))
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    return array, meta


def feature_exists(name: str, *, features_dir: Path | None = None) -> bool:
    """Check if a feature exists in the store.

    Args:
        name: Feature identifier (no extension).
        features_dir: Override storage directory (used in tests).

    Returns:
        True if the .npy file exists, False otherwise.
    """
    store = features_dir if features_dir is not None else FEATURES_DIR
    return (store / f"{name}.npy").exists()


def list_features(*, features_dir: Path | None = None) -> list[str]:
    """List all feature names in the store (without extensions).

    Args:
        features_dir: Override storage directory (used in tests).

    Returns:
        Sorted list of feature names (stems of .npy files found).
    """
    store = features_dir if features_dir is not None else FEATURES_DIR
    if not store.exists():
        return []
    return sorted(p.stem for p in store.glob("*.npy"))
