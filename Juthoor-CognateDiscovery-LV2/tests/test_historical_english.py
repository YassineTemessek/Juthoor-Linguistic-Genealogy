"""Tests for HistoricalEnglishLookup."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from juthoor_cognatediscovery_lv2.discovery.historical_english import (
    HistoricalEnglishLookup,
)


def _make_jsonl(tmp_path: Path, rows: list[dict]) -> Path:
    p = tmp_path / "historical_variants.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    return p


class TestHistoricalEnglishLookup:
    def test_graceful_when_file_missing(self):
        """No error when the file does not exist."""
        lookup = HistoricalEnglishLookup(path="/nonexistent/path/historical_variants.jsonl")
        assert lookup.size == 0
        assert lookup.get_variants("water") is None
        assert lookup.has_historical_form("water") is False

    def test_loading_from_file(self, tmp_path):
        rows = [
            {"modern_lemma": "water", "old_english_form": "wæter", "middle_english_form": "water", "ipa": "ˈwɑː.tər"},
            {"modern_lemma": "fire", "old_english_form": "fyr", "middle_english_form": "fir", "ipa": "ˈfaɪər"},
        ]
        path = _make_jsonl(tmp_path, rows)
        lookup = HistoricalEnglishLookup(path=path)
        assert lookup.size == 2

    def test_lookup_known_word(self, tmp_path):
        rows = [
            {"modern_lemma": "water", "old_english_form": "wæter", "middle_english_form": "water", "ipa": ""},
        ]
        path = _make_jsonl(tmp_path, rows)
        lookup = HistoricalEnglishLookup(path=path)
        result = lookup.get_variants("water")
        assert result is not None
        assert result["old_english_form"] == "wæter"

    def test_lookup_unknown_word_returns_none(self, tmp_path):
        rows = [{"modern_lemma": "water", "old_english_form": "wæter", "middle_english_form": "", "ipa": ""}]
        path = _make_jsonl(tmp_path, rows)
        lookup = HistoricalEnglishLookup(path=path)
        assert lookup.get_variants("zzznonsense") is None

    def test_lookup_is_case_insensitive(self, tmp_path):
        rows = [{"modern_lemma": "abbey", "old_english_form": "", "middle_english_form": "abbey", "ipa": ""}]
        path = _make_jsonl(tmp_path, rows)
        lookup = HistoricalEnglishLookup(path=path)
        assert lookup.get_variants("ABBEY") is not None
        assert lookup.get_variants("Abbey") is not None

    def test_has_historical_form(self, tmp_path):
        rows = [{"modern_lemma": "fire", "old_english_form": "fyr", "middle_english_form": "", "ipa": ""}]
        path = _make_jsonl(tmp_path, rows)
        lookup = HistoricalEnglishLookup(path=path)
        assert lookup.has_historical_form("fire") is True
        assert lookup.has_historical_form("unknown") is False

    def test_size_property(self, tmp_path):
        rows = [
            {"modern_lemma": "a", "old_english_form": "", "middle_english_form": "", "ipa": ""},
            {"modern_lemma": "b", "old_english_form": "", "middle_english_form": "", "ipa": ""},
            {"modern_lemma": "c", "old_english_form": "", "middle_english_form": "", "ipa": ""},
        ]
        path = _make_jsonl(tmp_path, rows)
        lookup = HistoricalEnglishLookup(path=path)
        assert lookup.size == 3

    def test_lazy_loading(self, tmp_path):
        """File is not read until first access."""
        rows = [{"modern_lemma": "test", "old_english_form": "test", "middle_english_form": "", "ipa": ""}]
        path = _make_jsonl(tmp_path, rows)
        lookup = HistoricalEnglishLookup(path=path)
        assert not lookup._loaded
        _ = lookup.size
        assert lookup._loaded

    def test_empty_lines_skipped(self, tmp_path):
        p = tmp_path / "historical_variants.jsonl"
        with open(p, "w", encoding="utf-8") as f:
            f.write('{"modern_lemma": "word", "old_english_form": "w", "middle_english_form": "", "ipa": ""}\n')
            f.write("\n")
            f.write("   \n")
        lookup = HistoricalEnglishLookup(path=p)
        assert lookup.size == 1
