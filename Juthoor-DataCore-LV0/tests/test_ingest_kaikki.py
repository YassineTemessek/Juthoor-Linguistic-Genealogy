"""
Tests for scripts/ingest/ingest_kaikki.py

Uses inline fixture data only — no real JSONL files are read.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from io import StringIO

import pytest

# Ensure scripts/ingest/ is on sys.path so we can import the script directly.
_SCRIPTS_INGEST = Path(__file__).resolve().parents[1] / "scripts" / "ingest"
if str(_SCRIPTS_INGEST) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_INGEST))

import ingest_kaikki  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

GREEK_RECORD = json.dumps({
    "word": "σκύλος", "lang_code": "grc", "pos": "noun",
    "senses": [{"glosses": ["skin, hide"]}],
    "sounds": [{"ipa": "/ský.los/"}],
})

LATIN_RECORD = json.dumps({
    "word": "thesaurus", "lang_code": "la", "pos": "noun",
    "senses": [{"glosses": ["treasure, hoard"]}],
    "sounds": [{"tags": ["Classical-Latin"], "ipa": "[tʰeːˈsau̯.rʊs]"}],
})

OE_RECORD = json.dumps({
    "word": "word", "lang_code": "ang", "pos": "noun",
    "senses": [{"glosses": ["word"]}],
    "sounds": [{"ipa": "/word/"}],
})

ME_RECORD = json.dumps({
    "word": "cat", "lang_code": "enm", "pos": "noun",
    "senses": [{"glosses": ["cat (feline)"]}],
    "sounds": [{"ipa": "/kat/"}],
})

EN_RECORD = json.dumps({
    "word": "house", "lang_code": "en", "pos": "noun",
    "senses": [{"glosses": ["a dwelling"]}],
    "sounds": [{"ipa": "/haʊs/"}],
})


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _parse(raw_json: str) -> dict | None:
    return ingest_kaikki.parse_record(json.loads(raw_json))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_lang_map_covers_all_targets():
    assert set(ingest_kaikki.LANG_MAP.keys()) == {"grc", "la", "ang", "enm", "en"}


def test_parse_greek_record():
    rec = _parse(GREEK_RECORD)
    assert rec is not None
    assert rec["language"] == "grc"
    assert rec["stage"] == "ancient"
    assert rec["script"] == "Grek"
    assert rec["gloss_plain"] == "skin, hide"
    assert rec["id"]


def test_parse_latin_record():
    rec = _parse(LATIN_RECORD)
    assert rec is not None
    assert rec["language"] == "lat"
    assert rec["gloss_plain"] == "treasure, hoard"


def test_parse_old_english():
    rec = _parse(OE_RECORD)
    assert rec is not None
    assert rec["language"] == "ang"
    assert rec["stage"] == "old"


def test_parse_middle_english():
    rec = _parse(ME_RECORD)
    assert rec is not None
    assert rec["language"] == "enm"
    assert rec["stage"] == "middle"


def test_parse_modern_english():
    rec = _parse(EN_RECORD)
    assert rec is not None
    assert rec["language"] == "eng"
    assert rec["stage"] == "modern"


def test_ingest_lines_deduplicates_ids(tmp_path):
    out_file = tmp_path / "out.jsonl"
    # Feed the same raw line twice — should produce 2 records with distinct IDs.
    lines = [LATIN_RECORD, LATIN_RECORD]
    count = ingest_kaikki.ingest_lines(iter(lines), out_file)
    assert count == 2
    records = [json.loads(l) for l in out_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(records) == 2
    assert records[0]["id"] != records[1]["id"]


def test_form_text_populated():
    rec = _parse(LATIN_RECORD)
    assert rec is not None
    assert "thesaurus" in rec.get("form_text", "")


def test_meaning_text_populated():
    rec = _parse(LATIN_RECORD)
    assert rec is not None
    assert rec.get("meaning_text") == "treasure, hoard"


def test_skips_empty_word():
    raw = json.dumps({"word": "", "lang_code": "la", "pos": "noun",
                      "senses": [{"glosses": ["something"]}], "sounds": []})
    assert ingest_kaikki.parse_record(json.loads(raw)) is None


def test_skips_unknown_lang_code():
    rec = ingest_kaikki.parse_record({"word": "hello", "lang_code": "xyz", "pos": "noun", "senses": [{"glosses": ["x"]}]})
    assert rec is None


def test_no_ipa_in_sounds():
    """Records where sounds list exists but has no 'ipa' key."""
    raw = {"word": "testword", "lang_code": "la", "pos": "noun",
           "senses": [{"glosses": ["a test"]}],
           "sounds": [{"tags": ["audio"], "mp3": "test.mp3"}]}
    rec = ingest_kaikki.parse_record(raw)
    assert rec is not None
    assert rec.get("ipa_raw", "") == ""
    # form_text should be just the lemma, no IPA
    assert rec["form_text"] == "testword"


def test_empty_glosses_skipped():
    """Sense with empty glosses list is skipped; next sense's gloss is used."""
    raw = {"word": "testword", "lang_code": "la", "pos": "noun",
           "senses": [
               {"glosses": []},           # empty, should be skipped
               {"glosses": ["fallback"]}  # this should be used
           ],
           "sounds": []}
    rec = ingest_kaikki.parse_record(raw)
    assert rec is not None
    assert rec.get("gloss_plain") == "fallback"
    assert rec.get("meaning_text") == "fallback"


def test_old_english_fields():
    """Old English records have form_text and lemma as translit."""
    rec = ingest_kaikki.parse_record(json.loads(OE_RECORD))
    assert rec["form_text"]  # must be populated
    assert "word" in rec["form_text"]  # lemma appears in form_text
    assert rec.get("translit") == "word"  # translit set to lemma
