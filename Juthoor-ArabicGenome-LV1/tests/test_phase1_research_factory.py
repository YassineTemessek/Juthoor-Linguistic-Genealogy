from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np


def _load_module(name: str, rel_path: str):
    path = Path(__file__).resolve().parents[1] / rel_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


exp11 = _load_module("exp11", "scripts/research_factory/axis1/exp_1_1_letter_similarity.py")
exp23 = _load_module("exp23", "scripts/research_factory/axis2/exp_2_3_field_coherence.py")
exp31 = _load_module("exp31", "scripts/research_factory/axis3/exp_3_1_modifier_personality.py")


def test_letter_similarity_helpers_return_square_matrices():
    vectors = np.eye(3, dtype=np.float32)
    sim = exp11.cosine_similarity_matrix(vectors)
    dist = exp11.euclidean_distance_matrix(vectors)
    assert sim.shape == (3, 3)
    assert dist.shape == (3, 3)
    assert np.allclose(np.diag(sim), 1.0)


def test_field_coherence_mean_pairwise_cosine():
    vectors = np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    value = exp23.mean_pairwise_cosine(vectors)
    assert value is not None
    assert value < 1.0


def test_modifier_personality_canonical_added_letter_prefers_final_letter():
    assert exp31.canonical_added_letter("أبو") == "و"
    assert exp31.canonical_added_letter("أدى/أدو") == "ي"
    assert exp31.canonical_added_letter("قرن") == "ن"


def test_modifier_personality_pairwise_consistency_positive_for_aligned_vectors():
    vectors = np.array([[1.0, 0.0], [0.8, 0.1], [0.9, 0.0]], dtype=np.float32)
    value = exp31.pairwise_consistency(vectors)
    assert value is not None
    assert value > 0.9
