"""Tests for scripts.ingest.processed_schema — core schema utilities."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts directory to path so we can import processed_schema
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "ingest"))

from processed_schema import (
    coerce_pos_list,
    derive_binary_root,
    ensure_min_schema,
    iter_missing_required,
    normalize_arabic_root,
    normalize_ipa,
    stable_id,
    strip_html,
)


# ── normalize_arabic_root ────────────────────────────────────────

class TestNormalizeArabicRoot:
    def test_strips_diacritics(self):
        assert normalize_arabic_root("كَتَبَ") == "كتب"

    def test_normalizes_hamza_variants(self):
        assert normalize_arabic_root("أكل") == "اكل"
        assert normalize_arabic_root("إسلام") == "اسلام"

    def test_normalizes_alef_maqsura(self):
        assert normalize_arabic_root("مشى") == "مشي"

    def test_normalizes_taa_marbuta(self):
        assert normalize_arabic_root("كتابة") == "كتابه"

    def test_empty_string(self):
        assert normalize_arabic_root("") == ""

    def test_none_input(self):
        assert normalize_arabic_root(None) == ""

    def test_strips_tatweel(self):
        # \u0640 is tatweel (kashida)
        assert normalize_arabic_root("كـتـب") == "كتب"


# ── derive_binary_root ───────────────────────────────────────────

class TestDeriveBinaryRoot:
    def test_normal_root(self):
        binary, method = derive_binary_root("كتب")
        assert binary == "كتب"[:2]
        assert method == "first2"

    def test_short_root(self):
        binary, method = derive_binary_root("ا")
        assert binary == ""
        assert method == "missing"

    def test_empty_root(self):
        binary, method = derive_binary_root("")
        assert binary == ""
        assert method == "missing"


# ── strip_html ───────────────────────────────────────────────────

class TestStripHtml:
    def test_removes_tags(self):
        assert strip_html("<b>bold</b> text") == "bold text"

    def test_collapses_whitespace(self):
        assert strip_html("a   b   c") == "a b c"

    def test_empty_input(self):
        assert strip_html("") == ""

    def test_none_returns_empty(self):
        assert strip_html(None) == ""


# ── normalize_ipa ────────────────────────────────────────────────

class TestNormalizeIpa:
    def test_strips_slashes(self):
        assert normalize_ipa("/kæt/") == "kæt"

    def test_strips_brackets(self):
        assert normalize_ipa("[kæt]") == "kæt"

    def test_removes_stress_marks(self):
        result = normalize_ipa("ˈwɔːtər")
        assert "ˈ" not in result

    def test_empty(self):
        assert normalize_ipa("") == ""

    def test_removes_whitespace(self):
        assert normalize_ipa("/ k æ t /") == "kæt"


# ── coerce_pos_list ──────────────────────────────────────────────

class TestCoercePosList:
    def test_none(self):
        assert coerce_pos_list(None) == []

    def test_string(self):
        assert coerce_pos_list("noun") == ["noun"]

    def test_list(self):
        assert coerce_pos_list(["noun", "verb"]) == ["noun", "verb"]

    def test_empty_string(self):
        assert coerce_pos_list("   ") == []

    def test_list_with_none(self):
        assert coerce_pos_list([None, "verb"]) == ["verb"]

    def test_integer(self):
        assert coerce_pos_list(42) == ["42"]


# ── stable_id ────────────────────────────────────────────────────

class TestStableId:
    def test_deterministic(self):
        id1 = stable_id("a", "b", "c")
        id2 = stable_id("a", "b", "c")
        assert id1 == id2

    def test_prefix(self):
        result = stable_id("a", prefix="test")
        assert result.startswith("test:")

    def test_different_inputs_different_ids(self):
        assert stable_id("a", "b") != stable_id("x", "y")

    def test_none_fields(self):
        result = stable_id(None, "b")
        assert result.startswith("lex:")


# ── ensure_min_schema ────────────────────────────────────────────

class TestEnsureMinSchema:
    def test_minimal_record(self):
        rec = ensure_min_schema({"lemma": "aqua"}, default_language="lat", default_source="test")
        assert rec["lemma"] == "aqua"
        assert rec["language"] == "lat"
        assert rec["source"] == "test"
        assert rec["translit"] == "aqua"  # defaults to lemma
        assert "id" in rec
        assert "ipa" in rec

    def test_arabic_root_processing(self):
        rec = ensure_min_schema(
            {"lemma": "كتاب", "language": "arabic", "root": "كَتَبَ"},
            default_source="test",
        )
        assert rec["root"] == "كَتَبَ"
        assert rec["root_norm"] == "كتب"
        assert rec["binary_root"] == "كت"

    def test_ipa_normalization(self):
        rec = ensure_min_schema({"lemma": "cat", "ipa_raw": "/kæt/"}, default_language="en")
        assert rec["ipa"] == "kæt"
        assert rec["ipa_raw"] == "/kæt/"

    def test_gloss_html_to_plain(self):
        rec = ensure_min_schema(
            {"lemma": "test", "gloss": "<b>hello</b> world"},
            default_language="en",
        )
        assert rec["gloss_html"] == "<b>hello</b> world"
        assert rec["gloss_plain"] == "hello world"

    def test_pos_coerced(self):
        rec = ensure_min_schema({"lemma": "test", "pos": "noun"}, default_language="en")
        assert rec["pos"] == ["noun"]

    def test_existing_id_preserved(self):
        rec = ensure_min_schema({"lemma": "test", "id": "custom:123"}, default_language="en")
        assert rec["id"] == "custom:123"


# ── iter_missing_required ────────────────────────────────────────

class TestIterMissingRequired:
    def test_complete_record(self):
        rec = {
            "id": "x",
            "lemma": "a",
            "language": "en",
            "source": "s",
            "lemma_status": "ok",
            "translit": "a",
            "ipa": "",
        }
        assert list(iter_missing_required(rec)) == []

    def test_missing_fields(self):
        rec = {"lemma": "a"}
        missing = list(iter_missing_required(rec))
        assert "id" in missing
        assert "language" in missing
        assert "source" in missing
