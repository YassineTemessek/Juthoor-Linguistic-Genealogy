from __future__ import annotations

import json
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.genome_scoring import GenomeScorer


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

