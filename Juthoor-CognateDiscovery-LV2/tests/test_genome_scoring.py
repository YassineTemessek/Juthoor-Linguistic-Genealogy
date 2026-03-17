from __future__ import annotations

import json
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.genome_scoring import GenomeScorer
from juthoor_cognatediscovery_lv2.discovery.scoring import apply_hybrid_scoring
from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import HybridWeights


def _write_promoted(tmp_path: Path) -> Path:
    features = tmp_path / "promoted_features"
    features.mkdir(parents=True)
    (features / "field_coherence_scores.jsonl").write_text(
        json.dumps({"binary_root": "ʕy", "coherence": 0.72}) + "\n"
        + json.dumps({"binary_root": "by", "coherence": 0.68}) + "\n",
        encoding="utf-8",
    )
    (features / "metathesis_pairs.jsonl").write_text(
        json.dumps({"binary_root_a": "qb", "binary_root_b": "bq"}) + "\n",
        encoding="utf-8",
    )
    return tmp_path


def test_genome_bonus_uses_cross_script_binary_match(tmp_path: Path):
    scorer = GenomeScorer(_write_promoted(tmp_path))
    bonus = scorer.genome_bonus(
        {"lemma": "عين", "root_norm": "عين"},
        {"lemma": "עין"},
    )
    assert bonus == 0.13


def test_genome_bonus_is_pair_sensitive_not_source_only(tmp_path: Path):
    scorer = GenomeScorer(_write_promoted(tmp_path))
    bonus = scorer.genome_bonus(
        {"lemma": "عين", "root_norm": "عين"},
        {"lemma": "אב"},
    )
    assert bonus == 0.0


def test_genome_bonus_persisted_in_components(tmp_path: Path):
    """After scoring with GenomeScorer, genome_bonus must appear in hybrid.components."""
    scorer = GenomeScorer(_write_promoted(tmp_path))
    candidates = {
        "pair1": {
            "scores": {"semantic": 0.7, "form": 0.5},
            "_source_fields": {"lemma": "عين", "root_norm": "عين"},
            "_target_fields": {"lemma": "עין"},
        }
    }
    apply_hybrid_scoring(candidates, HybridWeights(), genome_scorer=scorer)
    entry = candidates["pair1"]
    components = entry["hybrid"]["components"]
    assert "genome_bonus" in components, "genome_bonus must be stored in hybrid.components"
    assert isinstance(components["genome_bonus"], float)
    assert components["genome_bonus"] == 0.13


def test_genome_bonus_defaults_to_zero_in_components_without_scorer():
    """When no GenomeScorer is used, genome_bonus must default to 0.0 in components."""
    candidates = {
        "pair1": {
            "scores": {"semantic": 0.6, "form": 0.4},
            "_source_fields": {"lemma": "cat"},
            "_target_fields": {"lemma": "chat"},
        }
    }
    apply_hybrid_scoring(candidates, HybridWeights(), genome_scorer=None)
    entry = candidates["pair1"]
    components = entry["hybrid"]["components"]
    assert "genome_bonus" in components
    assert components["genome_bonus"] == 0.0

