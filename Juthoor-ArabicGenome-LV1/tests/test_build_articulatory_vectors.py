"""Tests for build_articulatory_vectors.py."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

# Make the script importable
sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "research_factory"
        / "phase0_setup"
    ),
)

from build_articulatory_vectors import SIFAAT_NAMES, build_articulatory_matrix


@pytest.fixture(scope="module")
def articulatory_result():
    """Build the matrix once for all tests."""
    return build_articulatory_matrix()


class TestArticulatoryMatrix:
    def test_shape_is_28_by_25(self, articulatory_result):
        matrix, letters, features = articulatory_result
        assert matrix.shape[0] == 28, f"Expected 28 rows, got {matrix.shape[0]}"
        assert matrix.shape == (28, 25), f"Expected (28, 25), got {matrix.shape}"

    def test_all_28_letters_present(self, articulatory_result):
        _, letters, _ = articulatory_result
        assert len(letters) == 28
        assert len(set(letters)) == 28  # no duplicates

    def test_one_hot_makhraj_rows_sum_to_one(self, articulatory_result):
        matrix, _, features = articulatory_result
        num_makhraj = sum(1 for f in features if f.startswith("makhraj_"))
        makhraj_block = matrix[:, :num_makhraj]
        row_sums = makhraj_block.sum(axis=1)
        np.testing.assert_array_almost_equal(
            row_sums, np.ones(28), decimal=5,
            err_msg="Each letter must have exactly one makhraj (one-hot)",
        )

    def test_sifaat_values_are_binary(self, articulatory_result):
        matrix, _, features = articulatory_result
        num_makhraj = sum(1 for f in features if f.startswith("makhraj_"))
        sifaat_block = matrix[:, num_makhraj:]
        unique_vals = set(sifaat_block.flatten().tolist())
        assert unique_vals <= {0.0, 1.0}, f"Non-binary sifaat values: {unique_vals}"

    def test_feature_names_count_matches_columns(self, articulatory_result):
        matrix, _, features = articulatory_result
        assert len(features) == matrix.shape[1]

    def test_sifaat_names_are_expected(self, articulatory_result):
        _, _, features = articulatory_result
        num_makhraj = sum(1 for f in features if f.startswith("makhraj_"))
        sifaat_features = features[num_makhraj:]
        assert sifaat_features == SIFAAT_NAMES

    def test_emphatic_letters_have_itbaq(self, articulatory_result):
        """Emphatic letters (ص ض ط ظ) should have itbaq=True."""
        matrix, letters, features = articulatory_result
        itbaq_idx = features.index("itbaq")
        emphatics = {"ص", "ض", "ط", "ظ"}
        for i, letter in enumerate(letters):
            if letter in emphatics:
                assert matrix[i, itbaq_idx] == 1.0, f"{letter} should have itbaq=True"
            else:
                assert matrix[i, itbaq_idx] == 0.0, f"{letter} should have itbaq=False"

    def test_letters_sharing_makhraj_have_same_one_hot(self, articulatory_result):
        """Letters ط د ت share makhraj_id=11 -- their makhraj one-hot should match."""
        matrix, letters, features = articulatory_result
        num_makhraj = sum(1 for f in features if f.startswith("makhraj_"))
        makhraj_block = matrix[:, :num_makhraj]

        taa_idx = letters.index("ت")
        dal_idx = letters.index("د")
        taa_emph_idx = letters.index("ط")

        np.testing.assert_array_equal(makhraj_block[taa_idx], makhraj_block[dal_idx])
        np.testing.assert_array_equal(makhraj_block[taa_idx], makhraj_block[taa_emph_idx])
