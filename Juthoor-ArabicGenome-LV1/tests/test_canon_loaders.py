from __future__ import annotations

from pathlib import Path

import pytest

from juthoor_arabicgenome_lv1.core.canon_loaders import (
    load_binary_field_registry,
    load_letter_registry,
    load_quranic_profiles,
    load_root_composition_registry,
    load_theory_claims,
)


def test_load_empty_letter_registry(tmp_path: Path) -> None:
    assert load_letter_registry(tmp_path) == {}


def test_load_valid_letter_registry(tmp_path: Path) -> None:
    path = tmp_path / "letters.jsonl"
    path.write_text(
        '{"letter":"ب","letter_name":"الباء","canonical_semantic_gloss":"x","canonical_kinetic_gloss":null,"canonical_sensory_gloss":null,"articulatory_features":null,"sources":[],"agreement_level":"unknown","confidence_tier":"stub","status":"draft"}\n',
        encoding="utf-8",
    )
    rows = load_letter_registry(path)
    assert rows["ب"].canonical_semantic_gloss == "x"


def test_load_malformed_registry_raises(tmp_path: Path) -> None:
    path = tmp_path / "letters.jsonl"
    path.write_text("{bad json}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_letter_registry(path)


def test_load_binary_registry(tmp_path: Path) -> None:
    path = tmp_path / "binary_fields.jsonl"
    path.write_text(
        '{"binary_root":"حس","field_gloss":null,"field_gloss_source":null,"letter1":"ح","letter2":"س","letter1_gloss":null,"letter2_gloss":null,"member_roots":["حسب"],"member_count":1,"coherence_score":0.5,"cross_lingual_support":null,"status":"draft"}\n',
        encoding="utf-8",
    )
    rows = load_binary_field_registry(path)
    assert rows["حس"].member_count == 1


def test_load_root_registry(tmp_path: Path) -> None:
    path = tmp_path / "root_composition.jsonl"
    path.write_text(
        '{"root":"حسب","binary_root":"حس","third_letter":"ب","conceptual_root_meaning":null,"binary_field_meaning":null,"axial_meaning":"x","letter_trace":null,"position_profile":null,"modifier_profile":null,"compositional_signal":null,"agreement_with_observed_gloss":null,"status":"draft","semantic_score":0.7}\n',
        encoding="utf-8",
    )
    rows = load_root_composition_registry(path)
    assert rows["حسب"].semantic_score == 0.7


def test_load_theory_claims(tmp_path: Path) -> None:
    path = tmp_path / "theory_claims.jsonl"
    path.write_text(
        '{"claim_id":"c1","theme":"intentionality","scholar":"neili","statement":"x","scope":"quranic_only","evidence_type":"doctrinal","source_doc":"doc","source_locator":null,"status":"asserted"}\n',
        encoding="utf-8",
    )
    rows = load_theory_claims(path)
    assert rows[0].claim_id == "c1"


def test_load_quranic_profiles(tmp_path: Path) -> None:
    path = tmp_path / "quranic_profiles.jsonl"
    path.write_text(
        '{"lemma":"قلب","root":"قلب","conceptual_meaning":null,"binary_field_meaning":null,"lexical_realization":null,"letter_trace":null,"contextual_constraints":["وجدان"],"contrast_lemmas":["فؤاد"],"interpretive_notes":null,"confidence":"stub","status":"draft"}\n',
        encoding="utf-8",
    )
    rows = load_quranic_profiles(path)
    assert rows["قلب"].contrast_lemmas == ("فؤاد",)
