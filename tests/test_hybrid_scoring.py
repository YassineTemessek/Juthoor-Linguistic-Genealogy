"""
Tests for the hybrid scoring module.

These tests verify the core similarity scoring logic used in cognate discovery.
"""

import pytest


class TestTextNormalization:
    """Test text normalization utilities."""

    def test_norm_text_basic(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import _norm_text

        assert _norm_text("Hello World") == "helloworld"
        assert _norm_text("UPPERCASE") == "uppercase"
        assert _norm_text("  spaces  ") == "spaces"

    def test_norm_text_punctuation(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import _norm_text

        assert _norm_text("hello-world") == "helloworld"
        assert _norm_text("test.case") == "testcase"
        assert _norm_text("(brackets)") == "brackets"

    def test_norm_text_unicode(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import _norm_text

        # NFKC normalization
        result = _norm_text("café")
        assert "cafe" in result or "café" in result.lower()

    def test_norm_text_empty(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import _norm_text

        assert _norm_text("") == ""
        assert _norm_text(None) == ""


class TestCharNgrams:
    """Test character n-gram generation."""

    def test_ngrams_basic(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import _char_ngrams

        result = _char_ngrams("hello", 2)
        assert "he" in result
        assert "el" in result
        assert "ll" in result
        assert "lo" in result

    def test_ngrams_short_text(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import _char_ngrams

        # Text shorter than n should return empty set
        assert _char_ngrams("a", 2) == set()
        assert _char_ngrams("ab", 3) == set()

    def test_ngrams_exact_length(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import _char_ngrams

        result = _char_ngrams("ab", 2)
        assert result == {"ab"}


class TestJaccard:
    """Test Jaccard similarity."""

    def test_jaccard_identical(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import _jaccard

        a = {"a", "b", "c"}
        assert _jaccard(a, a) == 1.0

    def test_jaccard_disjoint(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import _jaccard

        a = {"a", "b"}
        b = {"c", "d"}
        assert _jaccard(a, b) == 0.0

    def test_jaccard_partial(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import _jaccard

        a = {"a", "b", "c"}
        b = {"b", "c", "d"}
        # Intersection: {b, c} = 2, Union: {a, b, c, d} = 4
        assert _jaccard(a, b) == 0.5

    def test_jaccard_empty(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import _jaccard

        assert _jaccard(set(), {"a"}) == 0.0
        assert _jaccard({"a"}, set()) == 0.0
        assert _jaccard(set(), set()) == 0.0


class TestSkeleton:
    """Test consonant skeleton extraction."""

    def test_skeleton_basic(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import _skeleton

        # Should remove vowels
        result = _skeleton("hello")
        assert "e" not in result
        assert "o" not in result
        assert "h" in result
        assert "l" in result

    def test_skeleton_consonants_only(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import _skeleton

        result = _skeleton("bcdfg")
        assert result == "bcdfg"

    def test_skeleton_vowels_only(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import _skeleton

        result = _skeleton("aeiou")
        assert result == ""


class TestOrthographyScore:
    """Test orthographic similarity scoring."""

    def test_orthography_identical(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import orthography_score

        source = {"lemma": "test"}
        target = {"lemma": "test"}
        score = orthography_score(source, target)
        assert score == 1.0

    def test_orthography_different(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import orthography_score

        source = {"lemma": "abc"}
        target = {"lemma": "xyz"}
        score = orthography_score(source, target)
        assert score < 0.5  # Should be low for completely different strings

    def test_orthography_similar(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import orthography_score

        source = {"lemma": "testing"}
        target = {"lemma": "tester"}
        score = orthography_score(source, target)
        assert 0.3 < score < 1.0  # Should be moderate

    def test_orthography_empty(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import orthography_score

        assert orthography_score({}, {}) == 0.0
        assert orthography_score({"lemma": ""}, {"lemma": "test"}) == 0.0


class TestSoundScore:
    """Test phonetic/IPA similarity scoring."""

    def test_sound_with_ipa(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import sound_score

        source = {"ipa": "tɛst"}
        target = {"ipa": "tɛst"}
        score = sound_score(source, target)
        assert score == 1.0

    def test_sound_no_ipa(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import sound_score

        source = {"lemma": "test"}  # No IPA
        target = {"lemma": "test"}
        score = sound_score(source, target)
        assert score is None  # None when IPA absent, so combined_score skips this component


class TestHybridWeights:
    """Test the HybridWeights dataclass."""

    def test_default_weights(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import HybridWeights

        w = HybridWeights()
        assert w.semantic == 0.40
        assert w.form == 0.20
        assert w.orthography == 0.15
        assert w.sound == 0.15
        assert w.skeleton == 0.10
        # Weights should sum to 1.0
        assert abs(w.semantic + w.form + w.orthography + w.sound + w.skeleton - 1.0) < 0.001

    def test_custom_weights(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import HybridWeights

        w = HybridWeights(semantic=0.5, form=0.5, orthography=0, sound=0, skeleton=0)
        assert w.semantic == 0.5
        assert w.form == 0.5


class TestCombinedScore:
    """Test the combined scoring function."""

    def test_combined_all_components(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import (
            HybridWeights,
            combined_score,
        )

        weights = HybridWeights()
        score, used = combined_score(
            semantic_score=0.8,
            form_score=0.6,
            orthography=0.7,
            sound=0.5,
            skeleton=0.4,
            weights=weights,
        )
        assert 0 < score < 1
        assert "semantic" in used
        assert "form" in used

    def test_combined_partial_components(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import (
            HybridWeights,
            combined_score,
        )

        weights = HybridWeights()
        score, used = combined_score(
            semantic_score=0.8,
            form_score=None,  # Missing
            orthography=0.7,
            sound=None,  # Missing
            skeleton=0.4,
            weights=weights,
        )
        assert 0 < score < 1
        assert "semantic" in used
        assert "form" not in used
        assert "sound" not in used

    def test_combined_no_components(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import (
            HybridWeights,
            combined_score,
        )

        weights = HybridWeights()
        score, used = combined_score(
            semantic_score=None,
            form_score=None,
            orthography=None,
            sound=None,
            skeleton=None,
            weights=weights,
        )
        assert score == 0.0
        assert used == {}


class TestComputeHybrid:
    """Test the main compute_hybrid function."""

    def test_compute_hybrid_full(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import (
            HybridWeights,
            compute_hybrid,
        )

        source = {"lemma": "kitab", "translit": "kitab", "ipa": "kitaːb"}
        target = {"lemma": "book", "translit": "book", "ipa": "bʊk"}

        result = compute_hybrid(
            source=source,
            target=target,
            semantic=0.7,
            form=0.3,
            weights=HybridWeights(),
        )

        assert "components" in result
        assert "combined_score" in result
        assert "weights_used" in result
        assert "orthography" in result["components"]
        assert "sound" in result["components"]
        assert "skeleton" in result["components"]


class TestL2Normalize:
    """Test L2 normalization for embeddings."""

    def test_l2_normalize(self):
        import numpy as np
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import l2_normalize

        vectors = np.array([[3.0, 4.0], [1.0, 0.0]], dtype="float32")
        normalized = l2_normalize(vectors)

        # Check that norms are 1
        norms = np.linalg.norm(normalized, axis=1)
        np.testing.assert_array_almost_equal(norms, [1.0, 1.0])

    def test_l2_normalize_zero_vector(self):
        import numpy as np
        from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import l2_normalize

        vectors = np.array([[0.0, 0.0]], dtype="float32")
        normalized = l2_normalize(vectors)

        # Zero vectors should remain zero (avoid division by zero)
        np.testing.assert_array_almost_equal(normalized, [[0.0, 0.0]])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
