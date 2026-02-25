"""
Tests for juthoor_cognatediscovery_lv2.lv3.discovery.jsonl

Covers:
- LexemeRow properties: lemma, lexeme_id
- read_jsonl_rows(): normal read, empty file, limit, missing file, blank lines
- write_jsonl(): creates parent dirs, unicode, round-trips
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from juthoor_cognatediscovery_lv2.lv3.discovery.jsonl import (
    LexemeRow,
    read_jsonl_rows,
    write_jsonl,
)


# ---------------------------------------------------------------------------
# LexemeRow
# ---------------------------------------------------------------------------

class TestLexemeRow:
    def test_lemma_present(self):
        row = LexemeRow(row_idx=0, data={"lemma": "كَتَبَ", "id": "ar:cla:1"})
        assert row.lemma == "كَتَبَ"

    def test_lemma_missing_returns_empty_string(self):
        row = LexemeRow(row_idx=0, data={})
        assert row.lemma == ""

    def test_lemma_none_returns_empty_string(self):
        row = LexemeRow(row_idx=0, data={"lemma": None})
        assert row.lemma == ""

    def test_lemma_strips_whitespace(self):
        row = LexemeRow(row_idx=0, data={"lemma": "  word  "})
        assert row.lemma == "word"

    def test_lexeme_id_from_data(self):
        row = LexemeRow(row_idx=3, data={"id": "ar:cla:test:ktb"})
        assert row.lexeme_id == "ar:cla:test:ktb"

    def test_lexeme_id_fallback_when_missing(self):
        row = LexemeRow(row_idx=7, data={})
        assert row.lexeme_id == "row:7"

    def test_lexeme_id_fallback_when_none(self):
        row = LexemeRow(row_idx=2, data={"id": None})
        assert row.lexeme_id == "row:2"

    def test_lexeme_id_fallback_when_empty_string(self):
        row = LexemeRow(row_idx=5, data={"id": "   "})
        assert row.lexeme_id == "row:5"

    def test_row_is_frozen(self):
        row = LexemeRow(row_idx=0, data={})
        with pytest.raises((AttributeError, TypeError)):
            row.row_idx = 99  # type: ignore[misc]

    def test_data_accessible_directly(self):
        row = LexemeRow(row_idx=0, data={"lemma": "word", "pos": "verb"})
        assert row.data["pos"] == "verb"


# ---------------------------------------------------------------------------
# read_jsonl_rows()
# ---------------------------------------------------------------------------

class TestReadJsonlRows:
    def _write_lines(self, path: Path, records: list[dict]) -> None:
        path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
            encoding="utf-8",
        )

    def test_reads_all_rows(self, tmp_path):
        records = [
            {"id": "a:1", "lemma": "alpha"},
            {"id": "a:2", "lemma": "beta"},
            {"id": "a:3", "lemma": "gamma"},
        ]
        p = tmp_path / "test.jsonl"
        self._write_lines(p, records)

        rows = read_jsonl_rows(p)
        assert len(rows) == 3

    def test_row_data_matches_source(self, tmp_path):
        p = tmp_path / "test.jsonl"
        self._write_lines(p, [{"id": "ar:1", "lemma": "كتب", "pos": "verb"}])

        rows = read_jsonl_rows(p)
        assert rows[0].data["lemma"] == "كتب"
        assert rows[0].data["pos"] == "verb"

    def test_row_idx_reflects_file_line_index(self, tmp_path):
        p = tmp_path / "test.jsonl"
        self._write_lines(p, [{"id": "x"}, {"id": "y"}, {"id": "z"}])

        rows = read_jsonl_rows(p)
        assert rows[0].row_idx == 0
        assert rows[1].row_idx == 1
        assert rows[2].row_idx == 2

    def test_limit_zero_means_no_limit(self, tmp_path):
        p = tmp_path / "test.jsonl"
        self._write_lines(p, [{"id": str(i)} for i in range(10)])

        rows = read_jsonl_rows(p, limit=0)
        assert len(rows) == 10

    def test_limit_restricts_number_of_rows(self, tmp_path):
        p = tmp_path / "test.jsonl"
        self._write_lines(p, [{"id": str(i)} for i in range(20)])

        rows = read_jsonl_rows(p, limit=5)
        assert len(rows) == 5

    def test_limit_larger_than_file_returns_all(self, tmp_path):
        p = tmp_path / "test.jsonl"
        self._write_lines(p, [{"id": "a"}, {"id": "b"}])

        rows = read_jsonl_rows(p, limit=100)
        assert len(rows) == 2

    def test_empty_file_returns_empty_list(self, tmp_path):
        p = tmp_path / "empty.jsonl"
        p.write_text("", encoding="utf-8")

        rows = read_jsonl_rows(p)
        assert rows == []

    def test_blank_lines_are_skipped(self, tmp_path):
        p = tmp_path / "blanks.jsonl"
        p.write_text(
            '{"id": "a"}\n\n\n{"id": "b"}\n\n',
            encoding="utf-8",
        )

        rows = read_jsonl_rows(p)
        assert len(rows) == 2

    def test_missing_file_raises_file_not_found(self, tmp_path):
        missing = tmp_path / "nonexistent.jsonl"
        with pytest.raises(FileNotFoundError):
            read_jsonl_rows(missing)

    def test_unicode_content_preserved(self, tmp_path):
        p = tmp_path / "unicode.jsonl"
        record = {"id": "ar:1", "lemma": "كَتَبَ", "gloss": "to write (كَتَبَ)"}
        p.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

        rows = read_jsonl_rows(p)
        assert rows[0].data["lemma"] == "كَتَبَ"
        assert "كَتَبَ" in rows[0].data["gloss"]

    def test_returns_list_of_lexeme_row(self, tmp_path):
        p = tmp_path / "test.jsonl"
        self._write_lines(p, [{"id": "x"}])

        rows = read_jsonl_rows(p)
        assert all(isinstance(r, LexemeRow) for r in rows)


# ---------------------------------------------------------------------------
# write_jsonl()
# ---------------------------------------------------------------------------

class TestWriteJsonl:
    def test_writes_correct_number_of_lines(self, tmp_path):
        p = tmp_path / "out.jsonl"
        records = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        write_jsonl(p, records)

        lines = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) == 3

    def test_each_line_is_valid_json(self, tmp_path):
        p = tmp_path / "out.jsonl"
        records = [{"id": str(i), "val": i * 2} for i in range(5)]
        write_jsonl(p, records)

        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                obj = json.loads(line)
                assert isinstance(obj, dict)

    def test_round_trip(self, tmp_path):
        p = tmp_path / "round_trip.jsonl"
        originals = [
            {"id": "ar:1", "lemma": "كتب", "pos": "verb"},
            {"id": "en:1", "lemma": "write", "pos": "verb"},
            {"id": "la:1", "lemma": "scribo", "pos": "verb"},
        ]
        write_jsonl(p, originals)
        read_back = read_jsonl_rows(p)

        assert len(read_back) == len(originals)
        for original, row in zip(originals, read_back):
            assert row.data == original

    def test_creates_parent_directories(self, tmp_path):
        nested = tmp_path / "a" / "b" / "c" / "out.jsonl"
        assert not nested.parent.exists()

        write_jsonl(nested, [{"id": "x"}])
        assert nested.exists()

    def test_unicode_preserved_without_escaping(self, tmp_path):
        p = tmp_path / "unicode.jsonl"
        record = {"id": "ar:1", "lemma": "كَتَبَ", "note": "Arabic root \u0643\u062a\u0628"}
        write_jsonl(p, [record])

        raw = p.read_text(encoding="utf-8")
        # ensure_ascii=False: Arabic chars should appear literally, not as \uXXXX
        assert "كَتَبَ" in raw

    def test_overwrites_existing_file(self, tmp_path):
        p = tmp_path / "overwrite.jsonl"
        write_jsonl(p, [{"id": "old"}])
        write_jsonl(p, [{"id": "new1"}, {"id": "new2"}])

        rows = read_jsonl_rows(p)
        assert len(rows) == 2
        assert rows[0].data["id"] == "new1"

    def test_empty_iterable_produces_empty_file(self, tmp_path):
        p = tmp_path / "empty.jsonl"
        write_jsonl(p, [])

        assert p.exists()
        assert p.read_text(encoding="utf-8").strip() == ""

    def test_generator_input_accepted(self, tmp_path):
        p = tmp_path / "gen.jsonl"

        def record_gen():
            for i in range(3):
                yield {"id": str(i)}

        write_jsonl(p, record_gen())
        rows = read_jsonl_rows(p)
        assert len(rows) == 3
