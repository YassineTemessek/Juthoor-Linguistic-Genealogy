"""
Tests for juthoor_datacore_lv0.ingest.adapters.concepts.ConceptsAdapter

Uses inline fixtures only — no real data files are read.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from juthoor_datacore_lv0.ingest.adapters.concepts import ConceptsAdapter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_input(tmp_path: Path, records: list[dict]) -> Path:
    src = tmp_path / "data" / "processed" / "concepts" / "concepts_v3_2_enriched.jsonl"
    src.parent.mkdir(parents=True, exist_ok=True)
    with src.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return src


def _run(tmp_path: Path, records: list[dict]):
    _write_input(tmp_path, records)
    output_path = tmp_path / "out" / "concepts.jsonl"
    manifest_path = tmp_path / "out" / "concepts.manifest.json"

    result = ConceptsAdapter().run(
        input_dir=tmp_path,
        output_path=output_path,
        manifest_path=manifest_path,
    )

    rows = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return rows, manifest, result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_RECORD = {"lemma": "water"}

FULL_RECORD = {
    "lemma": "fire",
    "language": "en",
    "stage": "concept",
    "script": "Latn",
    "source": "concepts_v3_2_enriched",
    "lemma_status": "attested",
    "pos": ["noun"],
    "gloss_plain": "rapid oxidation producing heat and light",
    "meaning_text": "rapid oxidation producing heat and light",
}


# ---------------------------------------------------------------------------
# Basic parsing
# ---------------------------------------------------------------------------

def test_basic_record_written(tmp_path):
    rows, _, result = _run(tmp_path, [MINIMAL_RECORD])
    assert result.rows_written == 1
    assert len(rows) == 1


def test_defaults_applied_when_fields_missing(tmp_path):
    rows, _, _ = _run(tmp_path, [MINIMAL_RECORD])
    rec = rows[0]
    assert rec["language"] == "en"
    assert rec["stage"] == "concept"
    assert rec["script"] == "Latn"
    assert rec["source"] == "concepts_v3_2_enriched"
    assert rec["lemma_status"] == "attested"


def test_explicit_fields_preserved(tmp_path):
    rows, _, _ = _run(tmp_path, [FULL_RECORD])
    rec = rows[0]
    assert rec["language"] == "en"
    assert rec["stage"] == "concept"
    assert rec["gloss_plain"] == "rapid oxidation producing heat and light"
    assert rec["meaning_text"] == "rapid oxidation producing heat and light"


def test_lemma_preserved(tmp_path):
    rows, _, _ = _run(tmp_path, [{"lemma": "earth"}])
    assert rows[0]["lemma"] == "earth"


def test_id_generated_when_absent(tmp_path):
    rows, _, _ = _run(tmp_path, [MINIMAL_RECORD])
    assert rows[0].get("id"), "ID must be non-empty"


def test_id_preserved_when_present(tmp_path):
    rec = {**MINIMAL_RECORD, "id": "swadesh-001"}
    rows, _, _ = _run(tmp_path, [rec])
    assert rows[0]["id"] == "swadesh-001"


def test_id_contains_lemma(tmp_path):
    rows, _, _ = _run(tmp_path, [{"lemma": "stone"}])
    assert "stone" in rows[0]["id"]


# ---------------------------------------------------------------------------
# POS normalisation
# ---------------------------------------------------------------------------

def test_pos_string_to_list(tmp_path):
    rows, _, _ = _run(tmp_path, [{"lemma": "run", "pos": "verb"}])
    assert rows[0]["pos"] == ["verb"]


def test_pos_list_preserved(tmp_path):
    rows, _, _ = _run(tmp_path, [{"lemma": "light", "pos": ["noun", "verb", "adjective"]}])
    assert rows[0]["pos"] == ["noun", "verb", "adjective"]


def test_pos_missing_becomes_empty_list(tmp_path):
    rows, _, _ = _run(tmp_path, [{"lemma": "water"}])
    assert rows[0]["pos"] == []


def test_pos_empty_string_becomes_empty_list(tmp_path):
    rows, _, _ = _run(tmp_path, [{"lemma": "water", "pos": ""}])
    assert rows[0]["pos"] == []


# ---------------------------------------------------------------------------
# ID disambiguation
# ---------------------------------------------------------------------------

def test_duplicate_lemmas_get_distinct_ids(tmp_path):
    rec = {"lemma": "hand", "pos": "noun"}
    rows, _, _ = _run(tmp_path, [rec, rec])
    assert rows[0]["id"] != rows[1]["id"]


def test_four_duplicates_all_distinct(tmp_path):
    rec = {"lemma": "eye", "pos": "noun"}
    rows, _, _ = _run(tmp_path, [rec, rec, rec, rec])
    ids = [r["id"] for r in rows]
    assert len(set(ids)) == 4


def test_same_lemma_different_pos_have_distinct_ids(tmp_path):
    records = [
        {"lemma": "back", "pos": "noun"},
        {"lemma": "back", "pos": "verb"},
        {"lemma": "back", "pos": "adjective"},
    ]
    rows, _, _ = _run(tmp_path, records)
    ids = [r["id"] for r in rows]
    assert len(set(ids)) == 3


def test_different_lemmas_have_different_ids(tmp_path):
    records = [{"lemma": w} for w in ["sun", "moon", "star"]]
    rows, _, _ = _run(tmp_path, records)
    ids = [r["id"] for r in rows]
    assert len(set(ids)) == 3


# ---------------------------------------------------------------------------
# Multi-record and row count
# ---------------------------------------------------------------------------

def test_multiple_records_all_written(tmp_path):
    swadesh = [
        {"lemma": "I"}, {"lemma": "you"}, {"lemma": "we"},
        {"lemma": "this"}, {"lemma": "that"},
    ]
    rows, _, result = _run(tmp_path, swadesh)
    assert result.rows_written == 5
    assert len(rows) == 5


def test_blank_lines_skipped(tmp_path):
    src = tmp_path / "data" / "processed" / "concepts" / "concepts_v3_2_enriched.jsonl"
    src.parent.mkdir(parents=True, exist_ok=True)
    with src.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps({"lemma": "water"}) + "\n")
        fh.write("\n")
        fh.write("   \n")
        fh.write(json.dumps({"lemma": "fire"}) + "\n")

    output_path = tmp_path / "out" / "concepts.jsonl"
    manifest_path = tmp_path / "out" / "concepts.manifest.json"
    result = ConceptsAdapter().run(
        input_dir=tmp_path, output_path=output_path, manifest_path=manifest_path
    )
    assert result.rows_written == 2


def test_single_record_row_count(tmp_path):
    _, _, result = _run(tmp_path, [FULL_RECORD])
    assert result.rows_written == 1


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def test_manifest_written(tmp_path):
    _, manifest, _ = _run(tmp_path, [MINIMAL_RECORD])
    assert manifest["schema_version"] == "lv0.7"
    assert manifest["generated_by"] == "ConceptsAdapter"
    assert "sha256" in manifest
    assert manifest["row_count"] == 1


def test_manifest_id_policy_present(tmp_path):
    _, manifest, _ = _run(tmp_path, [MINIMAL_RECORD])
    assert "id_policy" in manifest


def test_manifest_row_count_matches_result(tmp_path):
    records = [{"lemma": f"concept{i}"} for i in range(10)]
    _, manifest, result = _run(tmp_path, records)
    assert manifest["row_count"] == result.rows_written == 10


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_missing_input_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="Missing input file"):
        ConceptsAdapter().run(
            input_dir=tmp_path,
            output_path=tmp_path / "out.jsonl",
            manifest_path=tmp_path / "out.manifest.json",
        )


def test_output_dir_created_automatically(tmp_path):
    _write_input(tmp_path, [MINIMAL_RECORD])
    deep_output = tmp_path / "x" / "y" / "z" / "concepts.jsonl"
    ConceptsAdapter().run(
        input_dir=tmp_path,
        output_path=deep_output,
        manifest_path=tmp_path / "x" / "y" / "z" / "concepts.manifest.json",
    )
    assert deep_output.exists()


# ---------------------------------------------------------------------------
# Extra fields and unicode
# ---------------------------------------------------------------------------

def test_extra_fields_passed_through(tmp_path):
    rec = {**FULL_RECORD, "concept_id": "swadesh-001", "frequency_rank": 1}
    rows, _, _ = _run(tmp_path, [rec])
    assert rows[0].get("concept_id") == "swadesh-001"
    assert rows[0].get("frequency_rank") == 1


def test_non_ascii_lemma_preserved(tmp_path):
    rec = {"lemma": "naître", "language": "fra", "stage": "concept"}
    rows, _, _ = _run(tmp_path, [rec])
    assert rows[0]["lemma"] == "naître"


def test_result_fields(tmp_path):
    _, _, result = _run(tmp_path, [MINIMAL_RECORD])
    assert result.output_path.exists()
    assert result.manifest_path.exists()
    assert result.rows_written >= 0
