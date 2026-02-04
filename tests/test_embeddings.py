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


class TestSonarConfig:
    """Test SonarConfig dataclass."""

    def test_default_config(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import SonarConfig

        cfg = SonarConfig()
        assert cfg.encoder == "text_sonar_basic_encoder"
        assert cfg.tokenizer == "text_sonar_basic_encoder"

    def test_custom_config(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import SonarConfig

        cfg = SonarConfig(encoder="custom_encoder", tokenizer="custom_tokenizer")
        assert cfg.encoder == "custom_encoder"
        assert cfg.tokenizer == "custom_tokenizer"

    def test_config_immutable(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import SonarConfig

        cfg = SonarConfig()
        with pytest.raises(AttributeError):
            cfg.encoder = "modified"


class TestCanineConfig:
    """Test CanineConfig dataclass."""

    def test_default_config(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import CanineConfig

        cfg = CanineConfig()
        assert cfg.model_id == "google/canine-c"
        assert cfg.pooling == "mean"

    def test_cls_pooling(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import CanineConfig

        cfg = CanineConfig(pooling="cls")
        assert cfg.pooling == "cls"

    def test_custom_model(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import CanineConfig

        cfg = CanineConfig(model_id="google/canine-s")
        assert cfg.model_id == "google/canine-s"


class TestSonarEmbedderInit:
    """Test SonarEmbedder initialization (no model loading)."""

    def test_init_no_load(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import SonarEmbedder

        # Should not load model on init (lazy loading)
        embedder = SonarEmbedder()
        assert embedder._pipeline is None

    def test_init_custom_config(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import (
            SonarConfig,
            SonarEmbedder,
        )

        cfg = SonarConfig(encoder="custom")
        embedder = SonarEmbedder(config=cfg)
        assert embedder.config.encoder == "custom"

    def test_init_default_config(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import SonarEmbedder

        embedder = SonarEmbedder()
        assert embedder.config is not None
        assert embedder.config.encoder == "text_sonar_basic_encoder"


class TestCanineEmbedderInit:
    """Test CanineEmbedder initialization (no model loading)."""

    def test_init_no_load(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import CanineEmbedder

        embedder = CanineEmbedder()
        assert embedder._model is None
        assert embedder._tokenizer is None

    def test_device_setting(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import CanineEmbedder

        embedder = CanineEmbedder(device="cuda")
        assert embedder.device == "cuda"

    def test_default_device_cpu(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import CanineEmbedder

        embedder = CanineEmbedder()
        assert embedder.device == "cpu"

    def test_custom_config(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import (
            CanineConfig,
            CanineEmbedder,
        )

        cfg = CanineConfig(model_id="google/canine-s", pooling="cls")
        embedder = CanineEmbedder(config=cfg)
        assert embedder.config.model_id == "google/canine-s"
        assert embedder.config.pooling == "cls"


@pytest.mark.slow
class TestSonarEmbedderIntegration:
    """Integration tests for SONAR embedder (requires model download)."""

    def test_embed_arabic(self):
        pytest.importorskip("sonar")
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import SonarEmbedder

        embedder = SonarEmbedder()
        texts = ["كتاب", "قلم"]
        vecs = embedder.embed(texts, sonar_lang="arb_Arab")

        assert vecs.shape == (2, 1024)
        norms = np.linalg.norm(vecs, axis=1)
        np.testing.assert_array_almost_equal(norms, [1.0, 1.0], decimal=5)

    def test_embed_english(self):
        pytest.importorskip("sonar")
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import SonarEmbedder

        embedder = SonarEmbedder()
        texts = ["book", "pen", "house"]
        vecs = embedder.embed(texts, sonar_lang="eng_Latn")

        assert vecs.shape == (3, 1024)
        norms = np.linalg.norm(vecs, axis=1)
        np.testing.assert_array_almost_equal(norms, np.ones(3), decimal=5)


@pytest.mark.slow
class TestCanineEmbedderIntegration:
    """Integration tests for CANINE embedder (requires model download)."""

    def test_embed_multilingual(self):
        pytest.importorskip("transformers")
        pytest.importorskip("torch")
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import CanineEmbedder

        embedder = CanineEmbedder(device="cpu")
        texts = ["hello", "مرحبا", "שלום"]
        vecs = embedder.embed(texts)

        assert vecs.shape[0] == 3
        assert vecs.shape[1] == 768  # CANINE hidden size

        norms = np.linalg.norm(vecs, axis=1)
        np.testing.assert_array_almost_equal(norms, np.ones(3), decimal=5)

    def test_embed_cls_pooling(self):
        pytest.importorskip("transformers")
        pytest.importorskip("torch")
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import (
            CanineConfig,
            CanineEmbedder,
        )

        cfg = CanineConfig(pooling="cls")
        embedder = CanineEmbedder(config=cfg, device="cpu")
        texts = ["test"]
        vecs = embedder.embed(texts)

        assert vecs.shape == (1, 768)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not slow"])
