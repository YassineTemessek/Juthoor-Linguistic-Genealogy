"""Tests for Phase 3 semantic validation scoring logic."""
import json
import numpy as np
import pytest
from pathlib import Path
import sys

# Ensure we can import from scripts/
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.append(str(SCRIPTS_DIR))

def test_cosine_score_identical_vectors():
    """Identical L2-normalized vectors should score 1.0."""
    from semantic_validation_phase3 import cosine_score

    a = np.array([1.0, 0.0, 0.0], dtype="float32")
    b = np.array([1.0, 0.0, 0.0], dtype="float32")
    assert cosine_score(a, b) == pytest.approx(1.0, abs=1e-6)


def test_cosine_score_orthogonal_vectors():
    """Orthogonal vectors should score 0.0."""
    from semantic_validation_phase3 import cosine_score

    a = np.array([1.0, 0.0, 0.0], dtype="float32")
    b = np.array([0.0, 1.0, 0.0], dtype="float32")
    assert cosine_score(a, b) == pytest.approx(0.0, abs=1e-6)


def test_cosine_score_opposite_vectors():
    """Opposite vectors should score -1.0."""
    from semantic_validation_phase3 import cosine_score

    a = np.array([1.0, 0.0], dtype="float32")
    b = np.array([-1.0, 0.0], dtype="float32")
    assert cosine_score(a, b) == pytest.approx(-1.0, abs=1e-6)


def test_build_text_index_unique_texts():
    """build_text_index should deduplicate texts and return text->index mapping."""
    from semantic_validation_phase3 import build_text_index

    records = [
        {"binary_root_meaning": "meaning A", "axial_meaning": "axial 1"},
        {"binary_root_meaning": "meaning A", "axial_meaning": "axial 2"},
        {"binary_root_meaning": "meaning B", "axial_meaning": "axial 1"},
    ]
    brm_index, ax_index = build_text_index(records)
    # binary_root_meaning has 2 unique texts
    assert len(brm_index) == 2
    assert "meaning A" in brm_index
    assert "meaning B" in brm_index
    # axial_meaning has 2 unique texts
    assert len(ax_index) == 2
    assert "axial 1" in ax_index
    assert "axial 2" in ax_index


def test_build_text_index_skips_empty():
    """build_text_index should skip records with empty meanings."""
    from semantic_validation_phase3 import build_text_index

    records = [
        {"binary_root_meaning": "", "axial_meaning": "axial 1"},
        {"binary_root_meaning": "meaning A", "axial_meaning": ""},
        {"binary_root_meaning": "meaning A", "axial_meaning": "axial 1"},
    ]
    brm_index, ax_index = build_text_index(records)
    assert len(brm_index) == 1  # only "meaning A"
    assert len(ax_index) == 1  # only "axial 1"


def test_compute_scores_with_mock_embeddings():
    """compute_scores should pair each record with its correct vectors and score."""
    from semantic_validation_phase3 import compute_scores

    # Fake embeddings: 3-dim, L2-normalized
    brm_embeddings = {
        "meaning A": np.array([1.0, 0.0, 0.0], dtype="float32"),
        "meaning B": np.array([0.0, 1.0, 0.0], dtype="float32"),
    }
    ax_embeddings = {
        "axial 1": np.array([1.0, 0.0, 0.0], dtype="float32"),  # identical to meaning A
        "axial 2": np.array([0.0, 0.0, 1.0], dtype="float32"),  # orthogonal to both
    }
    records = [
        {"tri_root": "abc", "binary_root_meaning": "meaning A", "axial_meaning": "axial 1"},
        {"tri_root": "def", "binary_root_meaning": "meaning A", "axial_meaning": "axial 2"},
        {"tri_root": "ghi", "binary_root_meaning": "meaning B", "axial_meaning": "axial 1"},
    ]
    scores = compute_scores(records, brm_embeddings, ax_embeddings)
    assert len(scores) == 3
    assert scores[0]["tri_root"] == "abc"
    assert scores[0]["semantic_score"] == pytest.approx(1.0, abs=1e-6)  # identical
    assert scores[1]["semantic_score"] == pytest.approx(0.0, abs=1e-6)  # orthogonal
    assert scores[2]["semantic_score"] == pytest.approx(0.0, abs=1e-6)  # orthogonal


def test_compute_scores_skips_missing_embeddings():
    """Records whose meaning text wasn't embedded should be skipped."""
    from semantic_validation_phase3 import compute_scores

    brm_embeddings = {"meaning A": np.array([1.0, 0.0], dtype="float32")}
    ax_embeddings = {"axial 1": np.array([1.0, 0.0], dtype="float32")}
    records = [
        {"tri_root": "abc", "binary_root_meaning": "meaning A", "axial_meaning": "axial 1"},
        {"tri_root": "def", "binary_root_meaning": "UNKNOWN", "axial_meaning": "axial 1"},
    ]
    scores = compute_scores(records, brm_embeddings, ax_embeddings)
    assert len(scores) == 1
    assert scores[0]["tri_root"] == "abc"


def test_build_report_structure():
    """build_report should produce correct distribution stats."""
    from semantic_validation_phase3 import build_report

    scored = [
        {"tri_root": "abc", "binary_root": "ab", "binary_root_meaning": "m1", "axial_meaning": "a1", "semantic_score": 0.9},
        {"tri_root": "def", "binary_root": "de", "binary_root_meaning": "m2", "axial_meaning": "a2", "semantic_score": 0.5},
        {"tri_root": "ghi", "binary_root": "gh", "binary_root_meaning": "m3", "axial_meaning": "a3", "semantic_score": 0.1},
    ]
    report = build_report(scored)
    assert report["total_scored"] == 3
    assert report["mean"] == pytest.approx(0.5, abs=1e-6)
    assert report["median"] == pytest.approx(0.5, abs=1e-6)
    assert "q25" in report
    assert "q75" in report
    assert "std" in report
    assert len(report["top_10"]) == 3  # only 3 items, so all shown
    assert len(report["bottom_10"]) == 3
    assert report["top_10"][0]["tri_root"] == "abc"  # highest first
    assert report["bottom_10"][0]["tri_root"] == "ghi"  # lowest first
    assert "histogram" in report


def test_load_muajam_records_real_data():
    """Verify we can load the real muajam roots.jsonl and get expected structure."""
    from semantic_validation_phase3 import load_muajam_records

    records = load_muajam_records()
    assert len(records) == 1938
    # Check first record has required fields
    rec = records[0]
    assert "binary_root_meaning" in rec
    assert "axial_meaning" in rec
    assert "tri_root" in rec
    assert "binary_root" in rec


def test_build_text_index_real_data():
    """Verify text index from real data produces reasonable counts."""
    from semantic_validation_phase3 import load_muajam_records, build_text_index

    records = load_muajam_records()
    brm_index, ax_index = build_text_index(records)
    # We expect ~200-300 unique binary_root_meaning texts
    assert 100 < len(brm_index) < 500
    # We expect ~1500-1900 unique axial_meaning texts
    assert 1000 < len(ax_index) < 2000
    # All index values should be sequential
    assert set(brm_index.values()) == set(range(len(brm_index)))
    assert set(ax_index.values()) == set(range(len(ax_index)))
