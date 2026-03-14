"""
Tests for genome bonus integration in the scoring pipeline.

Covers:
- apply_hybrid_scoring without genome_scorer (backward compatibility)
- apply_hybrid_scoring with genome_scorer (bonus applied)
- genome_bonus field is recorded in hybrid dict
- combined_score is capped at 1.0
- DiscoveryScorer accepts and propagates genome_scorer
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from juthoor_cognatediscovery_lv2.discovery.scoring import (
    apply_hybrid_scoring,
    _apply_genome_bonus,
    DiscoveryScorer,
)
from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import HybridWeights


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_candidate(
    semantic: float = 0.5,
    form: float = 0.4,
    source_root: str | None = None,
    target_root: str | None = None,
) -> dict:
    """Build a minimal candidate dict as produced by the runner."""
    src_fields: dict = {}
    tgt_fields: dict = {}
    if source_root:
        src_fields["root_norm"] = source_root
    if target_root:
        tgt_fields["root_norm"] = target_root

    return {
        "scores": {"semantic": semantic, "form": form},
        "_source_fields": src_fields,
        "_target_fields": tgt_fields,
    }


def _make_candidates(**kwargs) -> dict[str, dict]:
    return {"cand1": _make_candidate(**kwargs)}


def _make_mock_genome_scorer(bonus: float = 0.10) -> MagicMock:
    """Return a mock GenomeScorer whose genome_bonus always returns `bonus`."""
    mock = MagicMock()
    mock.genome_bonus.return_value = bonus
    return mock


# ---------------------------------------------------------------------------
# Backward compatibility — no genome_scorer
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    def test_no_genome_scorer_param_works(self):
        """apply_hybrid_scoring with only 2 args still works."""
        candidates = _make_candidates()
        weights = HybridWeights()
        apply_hybrid_scoring(candidates, weights)
        assert "hybrid" in candidates["cand1"]

    def test_genome_scorer_none_skips_bonus(self):
        """Explicit genome_scorer=None produces no genome_bonus field."""
        candidates = _make_candidates()
        weights = HybridWeights()
        apply_hybrid_scoring(candidates, weights, genome_scorer=None)
        hybrid = candidates["cand1"]["hybrid"]
        assert "genome_bonus" not in hybrid

    def test_combined_score_unchanged_without_genome(self):
        """Score with genome_scorer=None equals score without the parameter."""
        cand_a = _make_candidates(semantic=0.6, form=0.5)
        cand_b = _make_candidates(semantic=0.6, form=0.5)
        weights = HybridWeights()
        apply_hybrid_scoring(cand_a, weights)
        apply_hybrid_scoring(cand_b, weights, genome_scorer=None)
        assert cand_a["cand1"]["hybrid"]["combined_score"] == cand_b["cand1"]["hybrid"]["combined_score"]

    def test_discovery_scorer_default_no_genome(self):
        """DiscoveryScorer() constructed without genome_scorer has genome_scorer=None."""
        scorer = DiscoveryScorer()
        assert scorer.genome_scorer is None


# ---------------------------------------------------------------------------
# Genome bonus applied
# ---------------------------------------------------------------------------

class TestGenomeBonusApplied:
    def test_genome_bonus_increases_combined_score(self):
        """With genome_scorer returning 0.10, combined_score is higher than without."""
        candidates_no = _make_candidates(semantic=0.5, form=0.4)
        candidates_yes = _make_candidates(semantic=0.5, form=0.4)
        weights = HybridWeights()
        mock = _make_mock_genome_scorer(bonus=0.10)

        apply_hybrid_scoring(candidates_no, weights, genome_scorer=None)
        apply_hybrid_scoring(candidates_yes, weights, genome_scorer=mock)

        score_no = candidates_no["cand1"]["hybrid"]["combined_score"]
        score_yes = candidates_yes["cand1"]["hybrid"]["combined_score"]
        assert score_yes > score_no

    def test_genome_bonus_recorded_in_hybrid(self):
        """genome_bonus field is present in hybrid dict when scorer is provided."""
        candidates = _make_candidates()
        mock = _make_mock_genome_scorer(bonus=0.10)
        apply_hybrid_scoring(candidates, HybridWeights(), genome_scorer=mock)
        hybrid = candidates["cand1"]["hybrid"]
        assert "genome_bonus" in hybrid
        assert hybrid["genome_bonus"] == pytest.approx(0.10)

    def test_zero_bonus_recorded_when_scorer_returns_zero(self):
        """Even when genome_bonus returns 0.0, the field is present with value 0."""
        candidates = _make_candidates()
        mock = _make_mock_genome_scorer(bonus=0.0)
        apply_hybrid_scoring(candidates, HybridWeights(), genome_scorer=mock)
        hybrid = candidates["cand1"]["hybrid"]
        assert "genome_bonus" in hybrid
        assert hybrid["genome_bonus"] == pytest.approx(0.0)

    def test_genome_scorer_called_with_source_and_target_fields(self):
        """genome_bonus is called with the _source_fields and _target_fields dicts."""
        src = {"root_norm": "كتب", "lemma": "kataba"}
        tgt = {"root_norm": "ktb", "lemma": "scribe"}
        candidates = {
            "c": {
                "scores": {"semantic": 0.5, "form": 0.4},
                "_source_fields": src,
                "_target_fields": tgt,
            }
        }
        mock = _make_mock_genome_scorer(bonus=0.05)
        apply_hybrid_scoring(candidates, HybridWeights(), genome_scorer=mock)
        mock.genome_bonus.assert_called_once_with(src, tgt)


# ---------------------------------------------------------------------------
# Capping at 1.0
# ---------------------------------------------------------------------------

class TestGenomeBonusCap:
    def test_combined_score_capped_at_one(self):
        """combined_score never exceeds 1.0 even with a large genome bonus."""
        # Start near-perfect with high scores
        candidates = _make_candidates(semantic=0.99, form=0.99)
        mock = _make_mock_genome_scorer(bonus=0.15)
        apply_hybrid_scoring(candidates, HybridWeights(), genome_scorer=mock)
        hybrid = candidates["cand1"]["hybrid"]
        assert hybrid["combined_score"] <= 1.0

    def test_apply_genome_bonus_directly_caps_at_one(self):
        """_apply_genome_bonus caps combined_score at 1.0."""
        hybrid_in = {"combined_score": 0.95, "components": {}}
        mock = _make_mock_genome_scorer(bonus=0.15)
        result = _apply_genome_bonus(
            hybrid_in,
            source_fields={},
            target_fields={},
            genome_scorer=mock,
        )
        assert result["combined_score"] == pytest.approx(1.0)
        assert result["genome_bonus"] == pytest.approx(0.15)

    def test_apply_genome_bonus_exact_cap(self):
        """1.0 base + any bonus stays exactly 1.0."""
        hybrid_in = {"combined_score": 1.0, "components": {}}
        mock = _make_mock_genome_scorer(bonus=0.10)
        result = _apply_genome_bonus(
            hybrid_in,
            source_fields={},
            target_fields={},
            genome_scorer=mock,
        )
        assert result["combined_score"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# DiscoveryScorer integration
# ---------------------------------------------------------------------------

class TestDiscoveryScorerGenomeIntegration:
    def test_discovery_scorer_accepts_genome_scorer(self):
        """DiscoveryScorer constructor accepts genome_scorer parameter."""
        mock = _make_mock_genome_scorer()
        scorer = DiscoveryScorer(genome_scorer=mock)
        assert scorer.genome_scorer is mock

    def test_discovery_scorer_score_applies_genome_bonus(self):
        """DiscoveryScorer.score() propagates genome_scorer into scoring."""
        mock = _make_mock_genome_scorer(bonus=0.08)
        scorer_with = DiscoveryScorer(genome_scorer=mock)
        scorer_without = DiscoveryScorer(genome_scorer=None)

        cand_with = _make_candidates(semantic=0.5, form=0.4)
        cand_without = _make_candidates(semantic=0.5, form=0.4)

        results_with = scorer_with.score(cand_with)
        results_without = scorer_without.score(cand_without)

        hybrid_with = results_with[0]["hybrid"]
        hybrid_without = results_without[0]["hybrid"]

        assert hybrid_with["combined_score"] > hybrid_without["combined_score"]
        assert "genome_bonus" in hybrid_with
        assert "genome_bonus" not in hybrid_without

    def test_discovery_scorer_cleans_temp_fields(self):
        """_source_fields and _target_fields are removed after scoring."""
        mock = _make_mock_genome_scorer()
        scorer = DiscoveryScorer(genome_scorer=mock)
        candidates = _make_candidates()
        results = scorer.score(candidates)
        assert "_source_fields" not in results[0]
        assert "_target_fields" not in results[0]

    def test_discovery_scorer_adds_category(self):
        """category field is set by DiscoveryScorer.score()."""
        scorer = DiscoveryScorer()
        candidates = _make_candidates()
        results = scorer.score(candidates)
        assert "category" in results[0]
