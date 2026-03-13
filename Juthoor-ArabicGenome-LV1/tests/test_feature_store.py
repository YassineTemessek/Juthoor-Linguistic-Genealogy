"""Tests for the feature_store module.

Uses tmp_path to keep all file I/O isolated from the real outputs/ directory.
The features_dir keyword argument on each function acts as the injection point.
"""
import numpy as np
import pytest

from juthoor_arabicgenome_lv1.factory.feature_store import (
    feature_exists,
    list_features,
    load_feature,
    save_feature,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _store(tmp_path):
    """Return a per-test features directory inside tmp_path."""
    d = tmp_path / "features"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# Round-trip test
# ---------------------------------------------------------------------------

def test_save_load_roundtrip(tmp_path):
    store = _store(tmp_path)
    original = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    meta_in = {
        "entity_ids": ["root_a", "root_b"],
        "model_used": "test-model",
    }

    save_feature("test_array", original, meta_in, features_dir=store)
    loaded_array, loaded_meta = load_feature("test_array", features_dir=store)

    np.testing.assert_array_equal(original, loaded_array)
    assert loaded_meta["model_used"] == "test-model"
    assert loaded_meta["entity_ids"] == ["root_a", "root_b"]


# ---------------------------------------------------------------------------
# Auto-augmented metadata
# ---------------------------------------------------------------------------

def test_timestamp_added_automatically(tmp_path):
    store = _store(tmp_path)
    arr = np.zeros((3,))
    save_feature("ts_test", arr, {}, features_dir=store)
    _, meta = load_feature("ts_test", features_dir=store)
    assert "timestamp" in meta, "timestamp should be auto-added"


def test_shape_added_automatically(tmp_path):
    store = _store(tmp_path)
    arr = np.ones((5, 10), dtype=np.float64)
    save_feature("shape_test", arr, {}, features_dir=store)
    _, meta = load_feature("shape_test", features_dir=store)
    assert meta["shape"] == [5, 10]


def test_existing_timestamp_not_overwritten(tmp_path):
    store = _store(tmp_path)
    arr = np.zeros((2,))
    custom_ts = "2026-01-01T00:00:00+00:00"
    save_feature("ts_custom", arr, {"timestamp": custom_ts}, features_dir=store)
    _, meta = load_feature("ts_custom", features_dir=store)
    assert meta["timestamp"] == custom_ts


# ---------------------------------------------------------------------------
# feature_exists
# ---------------------------------------------------------------------------

def test_feature_exists_true_after_save(tmp_path):
    store = _store(tmp_path)
    arr = np.arange(6)
    save_feature("exists_test", arr, {}, features_dir=store)
    assert feature_exists("exists_test", features_dir=store) is True


def test_feature_exists_false_for_nonexistent(tmp_path):
    store = _store(tmp_path)
    assert feature_exists("ghost", features_dir=store) is False


# ---------------------------------------------------------------------------
# list_features
# ---------------------------------------------------------------------------

def test_list_features_includes_saved_name(tmp_path):
    store = _store(tmp_path)
    save_feature("alpha", np.zeros((2,)), {}, features_dir=store)
    save_feature("beta", np.ones((3,)), {}, features_dir=store)
    names = list_features(features_dir=store)
    assert "alpha" in names
    assert "beta" in names


def test_list_features_returns_sorted(tmp_path):
    store = _store(tmp_path)
    for name in ["zebra", "apple", "mango"]:
        save_feature(name, np.zeros((1,)), {}, features_dir=store)
    names = list_features(features_dir=store)
    assert names == sorted(names)


def test_list_features_empty_when_no_store(tmp_path):
    # directory doesn't exist yet
    missing_store = tmp_path / "nonexistent"
    assert list_features(features_dir=missing_store) == []


# ---------------------------------------------------------------------------
# load_feature missing file
# ---------------------------------------------------------------------------

def test_load_missing_feature_raises(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(FileNotFoundError):
        load_feature("does_not_exist", features_dir=store)


# ---------------------------------------------------------------------------
# Data type preservation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("dtype", [np.float32, np.float64, np.int32, np.bool_])
def test_dtype_preserved(tmp_path, dtype):
    store = _store(tmp_path)
    arr = np.array([1, 0, 1], dtype=dtype)
    save_feature(f"dtype_{dtype.__name__}", arr, {}, features_dir=store)
    loaded, _ = load_feature(f"dtype_{dtype.__name__}", features_dir=store)
    assert loaded.dtype == dtype
