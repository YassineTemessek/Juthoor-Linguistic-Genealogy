"""
Tests for juthoor_datacore_lv0.ingest.adapters.english_ipa.EnglishIPAAdapter

Uses inline fixtures only — no real data files are read.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from juthoor_datacore_lv0.ingest.adapters.english_ipa import EnglishIPAAdapter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_input(tmp_path: Path, records: list[dict]) -> Path:
    src = tmp_path / "data" / "processed" / "english" / "english_ipa_merged_pos.jsonl"
    src.parent.mkdir(parents=True, exist_ok=True)
    with src.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return src


def _run(tmp_path: Path, records: list[dict]):
    _write_input(tmp_path, records)
    output_path = tmp_path / "out" / "english_ipa.jsonl"
    manifest_path = tmp_path / "out" / "english_ipa.manifest.json"

    result = EnglishIPAAdapter().run(
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

MINIMAL_RECORD = {"lemma": "run", "pos": "verb"}

FULL_RECORD = {
    "lemma": "house",
    "language": "eng",
    "stage": "modern",
    "script": "Latn",
    "source": "english-ipa-merged",
    "lemma_status": "attested",
    "pos": ["noun"],
    "ipa_raw": "/haʊs/",
    "gloss_plain": "a dwelling",
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
    assert rec["language"] == "eng"
    assert rec["stage"] == "modern"
    assert rec["script"] == "Latn"
    assert rec["source"] == "english-ipa-merged"
    assert rec["lemma_status"] == "attested"


def test_explicit_fields_preserved(tmp_path):
    rows, _, _ = _run(tmp_path, [FULL_RECORD])
    rec = rows[0]
    assert rec["language"] == "eng"
    assert rec["stage"] == "modern"
    assert rec["script"] == "Latn"
    assert rec["ipa_raw"] == "/haʊs/"
    assert rec["gloss_plain"] == "a dwelling"


def test_id_generated_when_absent(tmp_path):
    rows, _, _ = _run(tmp_path, [MINIMAL_RECORD])
    assert rows[0].get("id"), "ID must be non-empty"


def test_id_preserved_when_present(tmp_path):
    rec = {**MINIMAL_RECORD, "id": "eng:modern:english-ipa-merged:run:verb:0"}
    rows, _, _ = _run(tmp_path, [rec])
    assert rows[0]["id"] == "eng:modern:english-ipa-merged:run:verb:0"


def test_id_contains_lemma(tmp_path):
    rows, _, _ = _run(tmp_path, [MINIMAL_RECORD])
    assert "run" in rows[0]["id"]


# ---------------------------------------------------------------------------
# POS normalisation
# ---------------------------------------------------------------------------

def test_pos_string_converted_to_list(tmp_path):
    rows, _, _ = _run(tmp_path, [{"lemma": "run", "pos": "verb"}])
    assert isinstance(rows[0]["pos"], list)
    assert rows[0]["pos"] == ["verb"]


def test_pos_list_preserved(tmp_path):
    rows, _, _ = _run(tmp_path, [{"lemma": "run", "pos": ["verb", "noun"]}])
    assert rows[0]["pos"] == ["verb", "noun"]


def test_pos_none_becomes_empty_list(tmp_path):
    rows, _, _ = _run(tmp_path, [{"lemma": "run"}])
    assert rows[0]["pos"] == []


def test_pos_empty_string_becomes_empty_list(tmp_path):
    rows, _, _ = _run(tmp_path, [{"lemma": "run", "pos": ""}])
    assert rows[0]["pos"] == []


# ---------------------------------------------------------------------------
# ID disambiguation
# ---------------------------------------------------------------------------

def test_duplicate_lemmas_get_distinct_ids(tmp_path):
    rec = {"lemma": "run", "pos": "verb"}
    rows, _, _ = _run(tmp_path, [rec, rec])
    assert rows[0]["id"] != rows[1]["id"]


def test_three_duplicates_all_distinct(tmp_path):
    rec = {"lemma": "set", "pos": "verb"}
    rows, _, _ = _run(tmp_path, [rec, rec, rec])
    ids = [r["id"] for r in rows]
    assert len(set(ids)) == 3


def test_different_pos_same_lemma(tmp_path):
    records = [
        {"lemma": "run", "pos": "verb"},
        {"lemma": "run", "pos": "noun"},
    ]
    rows, _, _ = _run(tmp_path, records)
    assert rows[0]["id"] != rows[1]["id"]


# ---------------------------------------------------------------------------
# Multi-record and row count
# ---------------------------------------------------------------------------

def test_multiple_records_all_written(tmp_path):
    records = [{"lemma": w} for w in ["cat", "dog", "bird", "fish", "ant"]]
    rows, _, result = _run(tmp_path, records)
    assert result.rows_written == 5
    assert len(rows) == 5


def test_blank_lines_skipped(tmp_path):
    src = tmp_path / "data" / "processed" / "english" / "english_ipa_merged_pos.jsonl"
    src.parent.mkdir(parents=True, exist_ok=True)
    with src.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps({"lemma": "cat"}) + "\n")
        fh.write("\n")
        fh.write("   \n")
        fh.write(json.dumps({"lemma": "dog"}) + "\n")

    output_path = tmp_path / "out" / "english_ipa.jsonl"
    manifest_path = tmp_path / "out" / "english_ipa.manifest.json"
    result = EnglishIPAAdapter().run(
        input_dir=tmp_path, output_path=output_path, manifest_path=manifest_path
    )
    assert result.rows_written == 2


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def test_manifest_written(tmp_path):
    _, manifest, _ = _run(tmp_path, [MINIMAL_RECORD])
    assert manifest["schema_version"] == "lv0.7"
    assert manifest["generated_by"] == "EnglishIPAAdapter"
    assert "sha256" in manifest
    assert manifest["row_count"] == 1


def test_manifest_row_count_matches_output(tmp_path):
    records = [{"lemma": f"word{i}"} for i in range(6)]
    _, manifest, result = _run(tmp_path, records)
    assert manifest["row_count"] == result.rows_written == 6


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_missing_input_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="Missing input file"):
        EnglishIPAAdapter().run(
            input_dir=tmp_path,
            output_path=tmp_path / "out.jsonl",
            manifest_path=tmp_path / "out.manifest.json",
        )


def test_output_dir_created_automatically(tmp_path):
    _write_input(tmp_path, [MINIMAL_RECORD])
    deep_output = tmp_path / "a" / "b" / "c" / "out.jsonl"
    EnglishIPAAdapter().run(
        input_dir=tmp_path,
        output_path=deep_output,
        manifest_path=tmp_path / "a" / "b" / "c" / "out.manifest.json",
    )
    assert deep_output.exists()


# ---------------------------------------------------------------------------
# IPA / unicode fields
# ---------------------------------------------------------------------------

def test_ipa_field_passed_through(tmp_path):
    rec = {"lemma": "thought", "pos": "noun", "ipa_raw": "/θɔːt/"}
    rows, _, _ = _run(tmp_path, [rec])
    assert rows[0]["ipa_raw"] == "/θɔːt/"


def test_lemma_case_preserved(tmp_path):
    rec = {"lemma": "iPhone"}
    rows, _, _ = _run(tmp_path, [rec])
    assert rows[0]["lemma"] == "iPhone"


def test_extra_fields_passed_through(tmp_path):
    rec = {**FULL_RECORD, "form_text": "house /haʊs/", "meaning_text": "a dwelling"}
    rows, _, _ = _run(tmp_path, [rec])
    assert rows[0]["form_text"] == "house /haʊs/"
    assert rows[0]["meaning_text"] == "a dwelling"
