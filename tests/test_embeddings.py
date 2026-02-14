"""
Tests for the embedding modules.

These tests verify embedder configuration and basic functionality.
Heavy model loading tests are marked slow and skipped by default.

Run all tests: pytest tests/test_embeddings.py -v
Run fast tests only: pytest tests/test_embeddings.py -v -m "not slow"
"""

import pytest
import numpy as np


class TestL2Normalize:
    """Test L2 normalization utility."""

    def test_basic_normalization(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import l2_normalize

        vectors = np.array([[3.0, 4.0], [1.0, 0.0]], dtype="float32")
        normalized = l2_normalize(vectors)

        norms = np.linalg.norm(normalized, axis=1)
        np.testing.assert_array_almost_equal(norms, [1.0, 1.0])

    def test_zero_vector_handling(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import l2_normalize

        vectors = np.array([[0.0, 0.0]], dtype="float32")
        normalized = l2_normalize(vectors)

        # Zero vectors should remain zero (no NaN)
        assert not np.any(np.isnan(normalized))
        np.testing.assert_array_almost_equal(normalized, [[0.0, 0.0]])

    def test_preserves_direction(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import l2_normalize

        vectors = np.array([[1.0, 1.0]], dtype="float32")
        normalized = l2_normalize(vectors)

        # Direction should be preserved (both components equal)
        assert abs(normalized[0, 0] - normalized[0, 1]) < 1e-6

    def test_multiple_vectors(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import l2_normalize

        vectors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 2.0, 0.0],
            [0.0, 0.0, 3.0],
        ], dtype="float32")
        normalized = l2_normalize(vectors)

        norms = np.linalg.norm(normalized, axis=1)
        np.testing.assert_array_almost_equal(norms, [1.0, 1.0, 1.0])

    def test_high_dimensional(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import l2_normalize

        rng = np.random.default_rng(42)
        vectors = rng.standard_normal((100, 1024)).astype("float32")
        normalized = l2_normalize(vectors)

        norms = np.linalg.norm(normalized, axis=1)
        np.testing.assert_array_almost_equal(norms, np.ones(100), decimal=5)


class TestBgeM3Config:
    """Test BgeM3Config dataclass."""

    def test_default_config(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import BgeM3Config

        cfg = BgeM3Config()
        assert cfg.model_id == "BAAI/bge-m3"
        assert cfg.use_fp16 is True
        assert cfg.max_length == 8192

    def test_custom_config(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import BgeM3Config

        cfg = BgeM3Config(model_id="custom/model", use_fp16=False, max_length=512)
        assert cfg.model_id == "custom/model"
        assert cfg.use_fp16 is False
        assert cfg.max_length == 512

    def test_config_immutable(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import BgeM3Config

        cfg = BgeM3Config()
        with pytest.raises(AttributeError):
            cfg.model_id = "modified"


class TestByT5Config:
    """Test ByT5Config dataclass."""

    def test_default_config(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import ByT5Config

        cfg = ByT5Config()
        assert cfg.model_id == "google/byt5-small"
        assert cfg.pooling == "mean"

    def test_cls_pooling(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import ByT5Config

        cfg = ByT5Config(pooling="cls")
        assert cfg.pooling == "cls"

    def test_custom_model(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import ByT5Config

        cfg = ByT5Config(model_id="google/byt5-base")
        assert cfg.model_id == "google/byt5-base"


class TestBgeM3EmbedderInit:
    """Test BgeM3Embedder initialization (no model loading)."""

    def test_init_no_load(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import BgeM3Embedder

        # Should not load model on init (lazy loading)
        embedder = BgeM3Embedder()
        assert embedder._model is None

    def test_init_custom_config(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import (
            BgeM3Config,
            BgeM3Embedder,
        )

        cfg = BgeM3Config(model_id="custom/model")
        embedder = BgeM3Embedder(config=cfg)
        assert embedder.config.model_id == "custom/model"

    def test_init_default_config(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import BgeM3Embedder

        embedder = BgeM3Embedder()
        assert embedder.config is not None
        assert embedder.config.model_id == "BAAI/bge-m3"


class TestByT5EmbedderInit:
    """Test ByT5Embedder initialization (no model loading)."""

    def test_init_no_load(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import ByT5Embedder

        embedder = ByT5Embedder()
        assert embedder._model is None
        assert embedder._tokenizer is None

    def test_device_setting(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import ByT5Embedder

        embedder = ByT5Embedder(device="cuda")
        assert embedder.device == "cuda"

    def test_default_device_cpu(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import ByT5Embedder

        embedder = ByT5Embedder()
        assert embedder.device == "cpu"

    def test_custom_config(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import (
            ByT5Config,
            ByT5Embedder,
        )

        cfg = ByT5Config(model_id="google/byt5-base", pooling="cls")
        embedder = ByT5Embedder(config=cfg)
        assert embedder.config.model_id == "google/byt5-base"
        assert embedder.config.pooling == "cls"


class TestBackwardCompatAliases:
    """Test that deprecated aliases still work."""

    def test_sonar_aliases(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import (
            SonarConfig,
            SonarEmbedder,
            BgeM3Config,
            BgeM3Embedder,
        )

        assert SonarConfig is BgeM3Config
        assert SonarEmbedder is BgeM3Embedder

    def test_canine_aliases(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import (
            CanineConfig,
            CanineEmbedder,
            ByT5Config,
            ByT5Embedder,
        )

        assert CanineConfig is ByT5Config
        assert CanineEmbedder is ByT5Embedder


@pytest.mark.slow
class TestBgeM3EmbedderIntegration:
    """Integration tests for BGE-M3 embedder (requires model download)."""

    def test_embed_arabic(self):
        pytest.importorskip("FlagEmbedding")
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import BgeM3Embedder

        embedder = BgeM3Embedder()
        texts = ["كتاب", "قلم"]
        vecs = embedder.embed(texts)

        assert vecs.shape == (2, 1024)
        norms = np.linalg.norm(vecs, axis=1)
        np.testing.assert_array_almost_equal(norms, [1.0, 1.0], decimal=5)

    def test_embed_english(self):
        pytest.importorskip("FlagEmbedding")
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import BgeM3Embedder

        embedder = BgeM3Embedder()
        texts = ["book", "pen", "house"]
        vecs = embedder.embed(texts)

        assert vecs.shape == (3, 1024)
        norms = np.linalg.norm(vecs, axis=1)
        np.testing.assert_array_almost_equal(norms, np.ones(3), decimal=5)


@pytest.mark.slow
class TestByT5EmbedderIntegration:
    """Integration tests for ByT5 embedder (requires model download)."""

    def test_embed_multilingual(self):
        pytest.importorskip("transformers")
        pytest.importorskip("torch")
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import ByT5Embedder

        embedder = ByT5Embedder(device="cpu")
        texts = ["hello", "مرحبا", "שלום"]
        vecs = embedder.embed(texts)

        assert vecs.shape[0] == 3
        assert vecs.shape[1] == 1472  # ByT5-small hidden size

        norms = np.linalg.norm(vecs, axis=1)
        np.testing.assert_array_almost_equal(norms, np.ones(3), decimal=5)

    def test_embed_cls_pooling(self):
        pytest.importorskip("transformers")
        pytest.importorskip("torch")
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import (
            ByT5Config,
            ByT5Embedder,
        )

        cfg = ByT5Config(pooling="cls")
        embedder = ByT5Embedder(config=cfg, device="cpu")
        texts = ["test"]
        vecs = embedder.embed(texts)

        assert vecs.shape == (1, 1472)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not slow"])
