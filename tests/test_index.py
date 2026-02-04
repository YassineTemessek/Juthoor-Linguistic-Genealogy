"""
Tests for FAISS index utilities.

These tests verify index building, saving, loading, and search operations.
"""

import pytest
import numpy as np


class TestBuildFlatIP:
    """Test flat inner product index building."""

    def test_build_basic(self):
        pytest.importorskip("faiss")
        from juthoor_cognatediscovery_lv2.lv3.discovery.index import build_flat_ip

        vectors = np.random.randn(100, 64).astype("float32")
        index, dim = build_flat_ip(vectors)

        assert dim == 64
        assert index.ntotal == 100

    def test_build_empty(self):
        pytest.importorskip("faiss")
        from juthoor_cognatediscovery_lv2.lv3.discovery.index import build_flat_ip

        vectors = np.zeros((0, 32), dtype="float32")
        index, dim = build_flat_ip(vectors)

        assert dim == 32
        assert index.ntotal == 0

    def test_search_returns_correct_shape(self):
        pytest.importorskip("faiss")
        from juthoor_cognatediscovery_lv2.lv3.discovery.index import build_flat_ip

        vectors = np.random.randn(50, 32).astype("float32")
        index, _ = build_flat_ip(vectors)

        query = np.random.randn(5, 32).astype("float32")
        scores, idxs = index.search(query, 10)

        assert scores.shape == (5, 10)
        assert idxs.shape == (5, 10)

    def test_search_finds_exact_match(self):
        pytest.importorskip("faiss")
        from juthoor_cognatediscovery_lv2.lv3.discovery.index import build_flat_ip

        # Create known vectors
        vectors = np.eye(10, dtype="float32")  # 10 orthogonal unit vectors
        index, _ = build_flat_ip(vectors)

        # Query with the 5th vector
        query = np.array([[0, 0, 0, 0, 1, 0, 0, 0, 0, 0]], dtype="float32")
        scores, idxs = index.search(query, 1)

        assert idxs[0, 0] == 4  # Should find index 4 (0-based)
        assert abs(scores[0, 0] - 1.0) < 1e-5  # Perfect match


class TestFaissIndex:
    """Test FaissIndex dataclass."""

    def test_save_and_load(self, tmp_path):
        pytest.importorskip("faiss")
        from juthoor_cognatediscovery_lv2.lv3.discovery.index import FaissIndex, build_flat_ip

        vectors = np.random.randn(20, 16).astype("float32")
        index, dim = build_flat_ip(vectors)

        idx_wrapper = FaissIndex(
            index_path=tmp_path / "test.faiss",
            meta_path=tmp_path / "meta.json",
            dim=dim,
        )
        idx_wrapper.save(index)

        # Verify files exist
        assert (tmp_path / "test.faiss").exists()
        assert (tmp_path / "meta.json").exists()

        # Load and verify
        loaded = idx_wrapper.load()
        assert loaded.ntotal == 20

    def test_metadata_content(self, tmp_path):
        pytest.importorskip("faiss")
        import json
        from juthoor_cognatediscovery_lv2.lv3.discovery.index import FaissIndex, build_flat_ip

        vectors = np.random.randn(10, 32).astype("float32")
        index, dim = build_flat_ip(vectors)

        idx_wrapper = FaissIndex(
            index_path=tmp_path / "test.faiss",
            meta_path=tmp_path / "meta.json",
            dim=dim,
        )
        idx_wrapper.save(index)

        # Read and verify metadata
        meta = json.loads((tmp_path / "meta.json").read_text())
        assert meta["dim"] == 32

    def test_load_nonexistent_raises(self, tmp_path):
        pytest.importorskip("faiss")
        from juthoor_cognatediscovery_lv2.lv3.discovery.index import FaissIndex

        idx_wrapper = FaissIndex(
            index_path=tmp_path / "nonexistent.faiss",
            meta_path=tmp_path / "meta.json",
            dim=32,
        )

        with pytest.raises(Exception):  # FAISS raises various exceptions
            idx_wrapper.load()


class TestIndexSearchIntegration:
    """Integration tests for index search operations."""

    def test_cosine_similarity_with_normalized_vectors(self, tmp_path):
        pytest.importorskip("faiss")
        from juthoor_cognatediscovery_lv2.lv3.discovery.index import build_flat_ip
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import l2_normalize

        # Create vectors and normalize (for cosine similarity)
        rng = np.random.default_rng(42)
        vectors = rng.standard_normal((100, 64)).astype("float32")
        vectors = l2_normalize(vectors)

        index, _ = build_flat_ip(vectors)

        # Query with a normalized vector
        query = l2_normalize(rng.standard_normal((1, 64)).astype("float32"))
        scores, _ = index.search(query, 5)

        # All scores should be in [-1, 1] for normalized vectors
        assert np.all(scores >= -1.0 - 1e-5)
        assert np.all(scores <= 1.0 + 1e-5)

    def test_top_k_ordering(self):
        pytest.importorskip("faiss")
        from juthoor_cognatediscovery_lv2.lv3.discovery.index import build_flat_ip

        vectors = np.random.randn(50, 16).astype("float32")
        index, _ = build_flat_ip(vectors)

        query = np.random.randn(1, 16).astype("float32")
        scores, _ = index.search(query, 10)

        # Scores should be in descending order
        for i in range(len(scores[0]) - 1):
            assert scores[0, i] >= scores[0, i + 1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
