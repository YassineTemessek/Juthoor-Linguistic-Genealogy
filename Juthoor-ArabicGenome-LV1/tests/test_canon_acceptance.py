from __future__ import annotations

import sys
from pathlib import Path

from juthoor_arabicgenome_lv1.core.canon_loaders import load_binary_field_registry, load_letter_registry
from juthoor_arabicgenome_lv1.core.loaders import load_binary_roots


LV1_ROOT = Path(__file__).resolve().parent.parent
CANON_SCRIPTS = LV1_ROOT / "scripts" / "canon"
if str(CANON_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(CANON_SCRIPTS))

from seed_registries import seed_registries  # noqa: E402


def test_all_28_letters_have_registry_rows(tmp_path: Path) -> None:
    seed_registries(tmp_path)
    assert len(load_letter_registry(tmp_path)) == 28


def test_all_binary_roots_have_registry_rows(tmp_path: Path) -> None:
    seed_registries(tmp_path)
    registry = load_binary_field_registry(tmp_path)
    expected = {row.binary_root for row in load_binary_roots()}
    assert expected.issubset(set(registry))


def test_every_seeded_canonical_gloss_has_provenance(tmp_path: Path) -> None:
    seed_registries(tmp_path)
    for entry in load_letter_registry(tmp_path).values():
        if entry.canonical_semantic_gloss:
            assert entry.sources


def test_contested_entries_preserve_multiple_sources(tmp_path: Path) -> None:
    seed_registries(tmp_path)
    path = tmp_path / "letters.jsonl"
    original = path.read_text(encoding="utf-8").splitlines()
    original.append('{"letter":"ث","letter_name":"الثاء","canonical_semantic_gloss":"x","canonical_kinetic_gloss":null,"canonical_sensory_gloss":null,"articulatory_features":null,"sources":[{"source_id":"s1","scholar":"hassan_abbas","claim_type":"sensory","claim_text":"x","document_ref":"doc","curation_status":"reviewed"},{"source_id":"s2","scholar":"jabal","claim_type":"semantic","claim_text":"y","document_ref":"doc","curation_status":"reviewed"}],"agreement_level":"contested","confidence_tier":"low","status":"draft"}')
    path.write_text("\n".join(original) + "\n", encoding="utf-8")
    # Duplicate key should fail loudly
    import pytest
    with pytest.raises(ValueError):
        load_letter_registry(tmp_path)


def test_h2_outputs_link_to_binary_entries(tmp_path: Path) -> None:
    seed_registries(tmp_path)
    registry = load_binary_field_registry(tmp_path)
    assert any(entry.coherence_score is not None for entry in registry.values())
