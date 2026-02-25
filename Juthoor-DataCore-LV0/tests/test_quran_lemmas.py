"""
Tests for juthoor_datacore_lv0.ingest.adapters.quran_lemmas.QuranLemmasAdapter

Uses inline fixtures only — no real data files are read.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from juthoor_datacore_lv0.ingest.adapters.quran_lemmas import QuranLemmasAdapter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_input(tmp_path: Path, records: list[dict]) -> Path:
    """Write records as JSONL at the path the adapter expects."""
    src = tmp_path / "data" / "processed" / "arabic" / "quran_lemmas_enriched.jsonl"
    src.parent.mkdir(parents=True, exist_ok=True)
    with src.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return src


def _run(tmp_path: Path, records: list[dict]) -> tuple[list[dict], dict]:
    """Run the adapter and return (output_records, manifest_dict)."""
    _write_input(tmp_path, records)
    output_path = tmp_path / "out" / "quran_lemmas.jsonl"
    manifest_path = tmp_path / "out" / "quran_lemmas.manifest.json"

    adapter = QuranLemmasAdapter()
    result = adapter.run(
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
# Basic parsing
# ---------------------------------------------------------------------------

MINIMAL_RECORD = {"lemma": "كَتَبَ", "pos": "verb"}

FULL_RECORD = {
    "lemma": "كَتَبَ",
    "language": "ara-qur",
    "stage": "quranic",
    "script": "Arab",
    "source": "quranic-corpus-morphology",
    "lemma_status": "attested",
    "pos": ["verb"],
    "gloss_plain": "to write",
    "ipa_raw": "kataba",
}


def test_basic_record_written(tmp_path):
    rows, _, result = _run(tmp_path, [MINIMAL_RECORD])
    assert result.rows_written == 1
    assert len(rows) == 1


def test_defaults_applied_when_fields_missing(tmp_path):
    rows, _, _ = _run(tmp_path, [MINIMAL_RECORD])
    rec = rows[0]
    assert rec["language"] == "ara-qur"
    assert rec["stage"] == "quranic"
    assert rec["script"] == "Arab"
    assert rec["source"] == "quranic-corpus-morphology"
    assert rec["lemma_status"] == "attested"


def test_explicit_fields_preserved(tmp_path):
    rows, _, _ = _run(tmp_path, [FULL_RECORD])
    rec = rows[0]
    assert rec["language"] == "ara-qur"
    assert rec["stage"] == "quranic"
    assert rec["gloss_plain"] == "to write"
    assert rec["ipa_raw"] == "kataba"


def test_id_generated_when_absent(tmp_path):
    rows, _, _ = _run(tmp_path, [MINIMAL_RECORD])
    assert rows[0].get("id"), "ID must be non-empty"


def test_id_preserved_when_present(tmp_path):
    rec = {**MINIMAL_RECORD, "id": "custom-id-001"}
    rows, _, _ = _run(tmp_path, [rec])
    assert rows[0]["id"] == "custom-id-001"


def test_pos_string_converted_to_list(tmp_path):
    rec = {"lemma": "كَتَبَ", "pos": "verb"}
    rows, _, _ = _run(tmp_path, [rec])
    assert isinstance(rows[0]["pos"], list)
    assert rows[0]["pos"] == ["verb"]


def test_pos_list_preserved(tmp_path):
    rec = {"lemma": "كَتَبَ", "pos": ["verb", "noun"]}
    rows, _, _ = _run(tmp_path, [rec])
    assert rows[0]["pos"] == ["verb", "noun"]


def test_pos_none_becomes_empty_list(tmp_path):
    rec = {"lemma": "كَتَبَ"}
    rows, _, _ = _run(tmp_path, [rec])
    assert rows[0]["pos"] == []


# ---------------------------------------------------------------------------
# ID disambiguation
# ---------------------------------------------------------------------------

def test_duplicate_lemmas_get_distinct_ids(tmp_path):
    rec = {"lemma": "كَتَبَ", "pos": "verb"}
    rows, _, _ = _run(tmp_path, [rec, rec])
    assert rows[0]["id"] != rows[1]["id"]


def test_three_duplicates_all_distinct(tmp_path):
    rec = {"lemma": "نَظَرَ", "pos": "verb"}
    rows, _, _ = _run(tmp_path, [rec, rec, rec])
    ids = [r["id"] for r in rows]
    assert len(set(ids)) == 3


def test_different_lemmas_get_different_ids(tmp_path):
    records = [
        {"lemma": "كَتَبَ", "pos": "verb"},
        {"lemma": "قَرَأَ", "pos": "verb"},
    ]
    rows, _, _ = _run(tmp_path, records)
    assert rows[0]["id"] != rows[1]["id"]


# ---------------------------------------------------------------------------
# Multi-record and row count
# ---------------------------------------------------------------------------

def test_rows_written_matches_non_empty_lines(tmp_path):
    records = [{"lemma": f"كلمة{i}"} for i in range(5)]
    rows, _, result = _run(tmp_path, records)
    assert result.rows_written == 5
    assert len(rows) == 5


def test_blank_lines_in_source_skipped(tmp_path):
    src = tmp_path / "data" / "processed" / "arabic" / "quran_lemmas_enriched.jsonl"
    src.parent.mkdir(parents=True, exist_ok=True)
    with src.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps({"lemma": "كَتَبَ"}, ensure_ascii=False) + "\n")
        fh.write("\n")
        fh.write("   \n")
        fh.write(json.dumps({"lemma": "قَرَأَ"}, ensure_ascii=False) + "\n")

    output_path = tmp_path / "out" / "quran_lemmas.jsonl"
    manifest_path = tmp_path / "out" / "quran_lemmas.manifest.json"
    result = QuranLemmasAdapter().run(
        input_dir=tmp_path, output_path=output_path, manifest_path=manifest_path
    )
    assert result.rows_written == 2


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def test_manifest_written(tmp_path):
    _, manifest, _ = _run(tmp_path, [MINIMAL_RECORD])
    assert manifest["schema_version"] == "lv0.7"
    assert manifest["generated_by"] == "QuranLemmasAdapter"
    assert "sha256" in manifest
    assert manifest["row_count"] == 1


def test_manifest_row_count_matches_output(tmp_path):
    records = [{"lemma": f"كلمة{i}"} for i in range(7)]
    _, manifest, result = _run(tmp_path, records)
    assert manifest["row_count"] == result.rows_written == 7


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_missing_input_raises(tmp_path):
    adapter = QuranLemmasAdapter()
    with pytest.raises(FileNotFoundError, match="Missing input file"):
        adapter.run(
            input_dir=tmp_path,
            output_path=tmp_path / "out.jsonl",
            manifest_path=tmp_path / "out.manifest.json",
        )


def test_output_dir_created_automatically(tmp_path):
    _write_input(tmp_path, [MINIMAL_RECORD])
    deep_output = tmp_path / "nested" / "deeply" / "out.jsonl"
    manifest_path = tmp_path / "nested" / "deeply" / "out.manifest.json"
    QuranLemmasAdapter().run(
        input_dir=tmp_path,
        output_path=deep_output,
        manifest_path=manifest_path,
    )
    assert deep_output.exists()


# ---------------------------------------------------------------------------
# Unicode / Arabic script
# ---------------------------------------------------------------------------

def test_arabic_lemma_preserved_as_unicode(tmp_path):
    rec = {"lemma": "مَكْتُوبٌ", "pos": "noun"}
    rows, _, _ = _run(tmp_path, [rec])
    assert rows[0]["lemma"] == "مَكْتُوبٌ"


def test_extra_fields_passed_through(tmp_path):
    rec = {**FULL_RECORD, "custom_field": "custom_value"}
    rows, _, _ = _run(tmp_path, [rec])
    assert rows[0].get("custom_field") == "custom_value"
