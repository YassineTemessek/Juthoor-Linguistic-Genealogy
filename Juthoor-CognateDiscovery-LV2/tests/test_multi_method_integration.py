"""Tests for multi-method scorer integration with scoring pipeline."""
from __future__ import annotations
import pytest
from juthoor_cognatediscovery_lv2.discovery.scoring import (
    _apply_multi_method_bonus,
    apply_hybrid_scoring,
    DiscoveryScorer,
)
from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScorer
from juthoor_cognatediscovery_lv2.discovery.rerank import FEATURE_NAMES, _feature_vector


def _make_hybrid(combined_score=0.5):
    return {"combined_score": combined_score, "components": {}}


def test_multi_method_bonus_fields_present():
    scorer = MultiMethodScorer()
    hybrid = _make_hybrid()
    source = {"lemma": "كتب", "root": "كتب", "root_translit": "ktb"}
    target = {"lemma": "script", "ipa": "skɹɪpt"}
    result = _apply_multi_method_bonus(
        hybrid, source_fields=source, target_fields=target,
        multi_method_scorer=scorer,
    )
    assert "multi_method_best_score" in result["components"]
    assert "multi_method_best_method" in result["components"]
    assert "multi_method_fired_count" in result["components"]
    assert "multi_method_bonus" in result["components"]


def test_multi_method_bonus_capped_at_012():
    scorer = MultiMethodScorer()
    hybrid = _make_hybrid(0.9)
    source = {"lemma": "كتب", "root": "كتب", "root_translit": "ktb"}
    target = {"lemma": "script", "ipa": "skɹɪpt"}
    result = _apply_multi_method_bonus(
        hybrid, source_fields=source, target_fields=target,
        multi_method_scorer=scorer,
    )
    assert result["components"]["multi_method_bonus"] <= 0.12


def test_multi_method_bonus_semantic_guard():
    scorer = MultiMethodScorer()
    hybrid = _make_hybrid(0.5)
    source = {"lemma": "كتب", "root": "كتب", "root_translit": "ktb"}
    target = {"lemma": "script", "ipa": "skɹɪpt"}
    result_no_guard = _apply_multi_method_bonus(
        hybrid, source_fields=source, target_fields=target,
        multi_method_scorer=scorer,
    )
    result_guarded = _apply_multi_method_bonus(
        _make_hybrid(0.5), source_fields=source, target_fields=target,
        multi_method_scorer=scorer, semantic_score=0.1,
    )
    # With low semantic, bonus should be halved
    assert result_guarded["components"]["multi_method_bonus"] <= result_no_guard["components"]["multi_method_bonus"]


def test_scorer_without_multi_method_backwards_compat():
    """DiscoveryScorer without multi_method_scorer should still work."""
    scorer = DiscoveryScorer()
    assert scorer.multi_method_scorer is None
    # Should not crash when scoring
    candidates = {
        "test": {
            "scores": {"semantic": 0.5, "form": 0.3},
            "_source_fields": {"lemma": "test", "lang": "eng"},
            "_target_fields": {"lemma": "test2", "lang": "eng"},
        }
    }
    result = scorer.score(candidates)
    assert len(result) == 1
    assert "multi_method_best_score" in result[0]["hybrid"]["components"]
    assert result[0]["hybrid"]["components"]["multi_method_best_score"] == 0.0


def test_reranker_has_11_features():
    assert len(FEATURE_NAMES) == 11
    assert "multi_method_score" in FEATURE_NAMES
    assert "root_quality" in FEATURE_NAMES
    assert "methods_fired_count" in FEATURE_NAMES


def test_feature_vector_extracts_multi_method():
    entry = {
        "scores": {"semantic": 0.5, "form": 0.3},
        "hybrid": {
            "components": {
                "sound": 0.1,
                "correspondence": 0.1,
                "genome_bonus": 0.0,
                "phonetic_law_bonus": 0.05,
                "source_coherence": 0.2,
                "multi_method_best_score": 0.65,
                "cross_pair_evidence": 0.3,
                "root_quality_bonus": 0.08,
                "multi_method_fired_count": 2,
            }
        },
    }
    vec = _feature_vector(entry)
    assert len(vec) == 11
    assert vec[7] == 0.65
    assert vec[8] == pytest.approx(0.3)
    assert vec[9] == pytest.approx(0.08)
    assert vec[10] == pytest.approx(2.0)
