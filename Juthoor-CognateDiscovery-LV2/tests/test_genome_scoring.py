# Tests for genome_scoring.py — GenomeScorer and helpers.
# No __init__.py in this directory.
from __future__ import annotations

from pathlib import Path

import pytest

from juthoor_cognatediscovery_lv2.discovery.genome_scoring import (
    GenomeScorer,
    _extract_binary_root,
    _DEFAULT_PROMOTED_DIR,
)

# Known values sampled from promoted_features at test-write time:
#   field_coherence_scores.jsonl[0]: binary_root="\u063a\u0638", coherence=0.766433
#   metathesis_pairs.jsonl[0]:  binary_root_a="\u0621\u0628", binary_root_b="\u0628\u0621"
_KNOWN_BR_COHERENCE = "\u063a\u0638"  # غظ  — first entry, score 0.766433
_KNOWN_META_A = "\u0621\u0628"        # ءب  — first metathesis pair root A
_KNOWN_META_B = "\u0628\u0621"        # بء  — first metathesis pair root B


# ---------------------------------------------------------------------------
# 1. Module loads from real promoted outputs without error
# ---------------------------------------------------------------------------

def test_scorer_loads_without_error():
    scorer = GenomeScorer()
    scorer._ensure_loaded()  # explicit load to trigger any I/O errors


# ---------------------------------------------------------------------------
# 2. root_coherence_score returns float for a known binary root
# ---------------------------------------------------------------------------

def test_root_coherence_score_known_root():
    scorer = GenomeScorer()
    # Pass the known binary root directly as the "root" argument.
    # _extract_binary_root will pull the first two consonants from it.
    result = scorer.root_coherence_score(_KNOWN_BR_COHERENCE)
    assert result is not None, "expected a float for known binary root"
    assert isinstance(result, float)
    assert 0.0 <= result <= 1.0


# ---------------------------------------------------------------------------
# 3. root_coherence_score returns None for unknown root
# ---------------------------------------------------------------------------

def test_root_coherence_score_unknown_root():
    scorer = GenomeScorer()
    # A pair of Latin characters — will never match an Arabic binary root.
    result = scorer.root_coherence_score("zz")
    assert result is None


# ---------------------------------------------------------------------------
# 4. is_metathesis_pair returns True for a known pair
# ---------------------------------------------------------------------------

def test_is_metathesis_pair_known():
    scorer = GenomeScorer()
    # Pass binary roots directly; _extract_binary_root will grab both letters.
    assert scorer.is_metathesis_pair(_KNOWN_META_A, _KNOWN_META_B) is True


# ---------------------------------------------------------------------------
# 5. is_metathesis_pair returns False for non-pair
# ---------------------------------------------------------------------------

def test_is_metathesis_pair_false():
    scorer = GenomeScorer()
    # Two identical roots — metathesis set contains reversed pairs, not identity.
    assert scorer.is_metathesis_pair("zz", "qq") is False


# ---------------------------------------------------------------------------
# 6. genome_bonus returns float in [0.0, 0.15]
# ---------------------------------------------------------------------------

def test_genome_bonus_range():
    scorer = GenomeScorer()
    # High-coherence source root should give +0.05 bonus at minimum.
    source = {"root": _KNOWN_BR_COHERENCE}
    target = {"root": "abc"}
    bonus = scorer.genome_bonus(source, target)
    assert isinstance(bonus, float)
    assert 0.0 <= bonus <= 0.15


# ---------------------------------------------------------------------------
# 7. genome_bonus with empty entries returns 0.0
# ---------------------------------------------------------------------------

def test_genome_bonus_empty_entries():
    scorer = GenomeScorer()
    assert scorer.genome_bonus({}, {}) == 0.0


# ---------------------------------------------------------------------------
# 8. _extract_binary_root extracts first two consonants correctly
# ---------------------------------------------------------------------------

def test_extract_binary_root_basic():
    # Three-letter Arabic root: should extract first two.
    root = "\u0643\u062a\u0628"  # كتب
    result = _extract_binary_root(root)
    assert result == "\u0643\u062a"  # كت


def test_extract_binary_root_too_short():
    # Single Arabic consonant — cannot form a binary root.
    result = _extract_binary_root("\u0643")  # ك
    assert result is None


def test_extract_binary_root_normalization():
    # أ (hamza on alef) should normalize to ا before extraction.
    root = "\u0623\u0628"  # أب — normalizes to اب
    result = _extract_binary_root(root)
    assert result == "\u0627\u0628"  # اب


# ---------------------------------------------------------------------------
# 9. Lazy loading: scorer does not load files until first method call
# ---------------------------------------------------------------------------

def test_lazy_loading():
    scorer = GenomeScorer()
    # Immediately after construction, _loaded must be False.
    assert scorer._loaded is False
    # Trigger a method call.
    scorer.root_coherence_score("xx")
    # After the first call, files should be loaded.
    assert scorer._loaded is True


# ---------------------------------------------------------------------------
# Sanity: verify default promoted dir points to a real directory
# ---------------------------------------------------------------------------

def test_default_promoted_dir_exists():
    assert _DEFAULT_PROMOTED_DIR.exists(), (
        f"Promoted dir not found: {_DEFAULT_PROMOTED_DIR}\n"
        "Run the LV1 research factory promotion script to generate promoted outputs."
    )


# ---------------------------------------------------------------------------
# Bonus: count entries loaded from real data
# ---------------------------------------------------------------------------

def test_data_counts():
    scorer = GenomeScorer()
    scorer._ensure_loaded()
    # We know from generation that there are 396 coherence entries and 166 metathesis pairs
    # (each pair stored twice — both directions — so 332 tuples in the set).
    assert len(scorer._coherence) > 0, "no coherence entries loaded"
    assert len(scorer._metathesis_set) > 0, "no metathesis pairs loaded"
