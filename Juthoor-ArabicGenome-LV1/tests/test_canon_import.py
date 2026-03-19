from __future__ import annotations

import json
from pathlib import Path

from juthoor_arabicgenome_lv1.core.canon_import import ingest_from_inbox
from juthoor_arabicgenome_lv1.core.canon_loaders import load_letter_registry, load_quranic_profiles


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _seed_letter_registry(registry_root: Path) -> None:
    _write_jsonl(
        registry_root / "letters.jsonl",
        [
            {
                "letter": "ب",
                "letter_name": "الباء",
                "canonical_semantic_gloss": None,
                "canonical_kinetic_gloss": None,
                "canonical_sensory_gloss": None,
                "articulatory_features": None,
                "sources": [],
                "agreement_level": "unknown",
                "confidence_tier": "stub",
                "status": "empty",
            }
        ],
    )
    _write_jsonl(registry_root / "binary_fields.jsonl", [])
    _write_jsonl(registry_root / "root_composition.jsonl", [])
    _write_jsonl(registry_root / "theory_claims.jsonl", [])
    _write_jsonl(registry_root / "quranic_profiles.jsonl", [])


def test_valid_import_updates_registry_and_moves_file(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    registry = tmp_path / "registries"
    _seed_letter_registry(registry)
    _write_jsonl(
        inbox / "letters" / "letters_patch.jsonl",
        [
            {
                "letter": "ب",
                "letter_name": "الباء",
                "canonical_semantic_gloss": "ظهور مع وصل",
                "canonical_kinetic_gloss": None,
                "canonical_sensory_gloss": None,
                "articulatory_features": {"place": "شفوي"},
                "sources": [
                    {
                        "source_id": "manual-b",
                        "scholar": "jabal",
                        "claim_type": "semantic",
                        "claim_text": "ظهور مع وصل",
                        "document_ref": "inbox/letters/letters_patch.jsonl",
                        "curation_status": "accepted",
                    }
                ],
                "agreement_level": "majority",
                "confidence_tier": "medium",
                "status": "curated",
            }
        ],
    )

    report = ingest_from_inbox(inbox_root=inbox, registry_root=registry)
    letters = load_letter_registry(registry)

    assert report["updated"] == 1
    assert letters["ب"].canonical_semantic_gloss == "ظهور مع وصل"
    assert letters["ب"].status == "curated"
    assert letters["ب"].sources[0].source_id == "manual-b"
    assert not (inbox / "letters" / "letters_patch.jsonl").exists()
    assert Path(report["report_path"]).parent == tmp_path / "import_reports"


def test_invalid_import_moves_to_rejected(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    registry = tmp_path / "registries"
    _seed_letter_registry(registry)
    _write_jsonl(inbox / "letters" / "broken.jsonl", [{"letter": "ب"}])

    report = ingest_from_inbox(inbox_root=inbox, registry_root=registry)

    assert report["rejected"] == 1
    assert not (inbox / "letters" / "broken.jsonl").exists()
    assert (tmp_path / "rejected" / "letters" / "broken.jsonl").exists()


def test_dry_run_does_not_move_or_write(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    registry = tmp_path / "registries"
    _seed_letter_registry(registry)
    source_file = inbox / "letters" / "letters_patch.jsonl"
    _write_jsonl(
        source_file,
        [
            {
                "letter": "ب",
                "letter_name": "الباء",
                "agreement_level": "majority",
                "confidence_tier": "medium",
                "status": "curated",
                "sources": [],
            }
        ],
    )

    report = ingest_from_inbox(inbox_root=inbox, registry_root=registry, dry_run=True)
    letters = load_letter_registry(registry)

    assert report["dry_run"] is True
    assert source_file.exists()
    assert letters["ب"].status == "empty"


def test_promoted_row_is_not_overwritten(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    registry = tmp_path / "registries"
    _write_jsonl(
        registry / "letters.jsonl",
        [
            {
                "letter": "ب",
                "letter_name": "الباء",
                "canonical_semantic_gloss": "old",
                "canonical_kinetic_gloss": None,
                "canonical_sensory_gloss": None,
                "articulatory_features": None,
                "sources": [],
                "agreement_level": "majority",
                "confidence_tier": "high",
                "status": "promoted",
            }
        ],
    )
    _write_jsonl(registry / "binary_fields.jsonl", [])
    _write_jsonl(registry / "root_composition.jsonl", [])
    _write_jsonl(registry / "theory_claims.jsonl", [])
    _write_jsonl(registry / "quranic_profiles.jsonl", [])
    _write_jsonl(
        inbox / "letters" / "letters_patch.jsonl",
        [
            {
                "letter": "ب",
                "letter_name": "الباء",
                "canonical_semantic_gloss": "new",
                "agreement_level": "consensus",
                "confidence_tier": "high",
                "status": "curated",
                "sources": [],
            }
        ],
    )

    ingest_from_inbox(inbox_root=inbox, registry_root=registry)
    letters = load_letter_registry(registry)

    assert letters["ب"].canonical_semantic_gloss == "old"
    assert letters["ب"].status == "promoted"


def test_conflicting_sources_are_appended(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    registry = tmp_path / "registries"
    _seed_letter_registry(registry)
    _write_jsonl(
        inbox / "letters" / "letters_patch.jsonl",
        [
            {
                "letter": "ب",
                "letter_name": "الباء",
                "canonical_semantic_gloss": "ظهور مع وصل",
                "agreement_level": "majority",
                "confidence_tier": "medium",
                "status": "curated",
                "sources": [
                    {
                        "source_id": "src-1",
                        "scholar": "jabal",
                        "claim_type": "semantic",
                        "claim_text": "ظهور مع وصل",
                        "document_ref": "doc-1",
                        "curation_status": "accepted",
                    }
                ],
            }
        ],
    )
    ingest_from_inbox(inbox_root=inbox, registry_root=registry)
    _write_jsonl(
        inbox / "letters" / "letters_patch_2.jsonl",
        [
            {
                "letter": "ب",
                "letter_name": "الباء",
                "canonical_semantic_gloss": "بروز واتصال",
                "agreement_level": "contested",
                "confidence_tier": "medium",
                "status": "curated",
                "sources": [
                    {
                        "source_id": "src-2",
                        "scholar": "other",
                        "claim_type": "semantic",
                        "claim_text": "بروز واتصال",
                        "document_ref": "doc-2",
                        "curation_status": "accepted",
                    }
                ],
            }
        ],
    )

    ingest_from_inbox(inbox_root=inbox, registry_root=registry, force=True)
    letters = load_letter_registry(registry)

    assert {item.source_id for item in letters["ب"].sources} == {"src-1", "src-2"}


def test_quranic_import_loads(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    registry = tmp_path / "registries"
    _seed_letter_registry(registry)
    _write_jsonl(
        inbox / "quranic" / "quranic_patch.jsonl",
        [
            {
                "lemma": "الأرض",
                "root": "ارض",
                "conceptual_meaning": "earth",
                "binary_field_meaning": "سطح",
                "lexical_realization": "اليابسة",
                "letter_trace": [],
                "contextual_constraints": ["context:creation"],
                "contrast_lemmas": ["السماء"],
                "interpretive_notes": "demo",
                "confidence": "medium",
                "status": "draft",
            }
        ],
    )

    ingest_from_inbox(inbox_root=inbox, registry_root=registry)
    profiles = load_quranic_profiles(registry)

    assert profiles["الأرض"].root == "ارض"
