"""
Tests for scripts/ingest/ingest_arabic_ten_dicts.py

Uses inline fixture data only — no real CSV files are read.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

import pytest

# Ensure scripts/ingest/ is on sys.path so we can import the script directly.
_SCRIPTS_INGEST = Path(__file__).resolve().parents[1] / "scripts" / "ingest"
if str(_SCRIPTS_INGEST) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_INGEST))

import ingest_arabic_ten_dicts  # noqa: E402
from ingest_arabic_ten_dicts import (  # noqa: E402
    DICT_NAMES,
    _normalize_header,
    parse_csv_row,
    ingest_csv_file,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_HEADER = "Root;No of derevatives found;derevatives found;Root Length;Has Vowel;Full Text"
SAMPLE_ROW = 'أبن;4; الْإِبَّانُ إبَّانِهَا;3;vowel;"*أبن*\t تهيؤ الشيء واستعداده"'
EMPTY_ROOT_ROW = ';0;;0;no vowel;""'
BOM_HEADER = '\ufeffRoot;No of derevatives found;derevatives found;Root Length;Has Vowel;Full Text'


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _reader(rows):
    return csv.reader(io.StringIO("\n".join(rows)), delimiter=";")


def _parse_row(raw_row: str, raw_header: str = SAMPLE_HEADER, source_name: str = "AlMaghreb") -> dict | None:
    header_row = next(_reader([raw_header]))
    header = _normalize_header(header_row)
    data_row = next(_reader([raw_row]))
    return parse_csv_row(data_row, header=header, source_name=source_name, row_num=1)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_dict_names_not_empty():
    assert len(DICT_NAMES) >= 12


def test_parse_valid_row():
    rec = _parse_row(SAMPLE_ROW)
    assert rec is not None
    assert rec["lemma"] == "أبن"
    assert rec["language"] == "ara"
    assert "AlMaghreb" in rec["source"]
    assert rec["id"]


def test_parse_empty_root_returns_none():
    result = _parse_row(EMPTY_ROOT_ROW)
    assert result is None


def test_bom_header_handled():
    rec = _parse_row(SAMPLE_ROW, raw_header=BOM_HEADER)
    assert rec is not None
    assert rec["lemma"] == "أبن"


def test_form_text_populated():
    rec = _parse_row(SAMPLE_ROW)
    assert rec is not None
    assert rec["form_text"] == "AR: أبن"


def test_meaning_text_from_derivatives():
    rec = _parse_row(SAMPLE_ROW)
    assert rec is not None
    assert rec.get("meaning_text") and len(rec["meaning_text"]) > 0


def test_ingest_csv_file_writes_jsonl(tmp_path):
    csv_content = "\n".join([SAMPLE_HEADER, SAMPLE_ROW])
    csv_file = tmp_path / "AlMaghreb.csv"
    csv_file.write_text(csv_content, encoding="utf-8-sig")
    out_file = tmp_path / "out.jsonl"
    count = ingest_csv_file(csv_file, out_file, source_name="AlMaghreb")
    assert count == 1
    lines = [l for l in out_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["lemma"] == "أبن"


def test_skips_empty_root_in_file(tmp_path):
    csv_content = "\n".join([SAMPLE_HEADER, SAMPLE_ROW, EMPTY_ROOT_ROW])
    csv_file = tmp_path / "AlMaghreb.csv"
    csv_file.write_text(csv_content, encoding="utf-8-sig")
    out_file = tmp_path / "out.jsonl"
    count = ingest_csv_file(csv_file, out_file, source_name="AlMaghreb")
    assert count == 1
    lines = [l for l in out_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 1


def test_ingest_csv_file_deduplicates_ids(tmp_path):
    """Two rows with the same root get distinct IDs."""
    csv_content = SAMPLE_HEADER + "\n" + SAMPLE_ROW + "\n" + SAMPLE_ROW + "\n"
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(csv_content, encoding="utf-8")
    out_file = tmp_path / "out.jsonl"
    count = ingest_csv_file(csv_file, out_file, source_name="AlMaghreb")
    assert count == 2
    lines = [json.loads(l) for l in out_file.read_text(encoding="utf-8").splitlines()]
    assert lines[0]["id"] != lines[1]["id"], "Duplicate rows must get distinct IDs"
