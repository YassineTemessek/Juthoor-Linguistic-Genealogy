"""Tests for juthoor_datacore_lv0.features.build_text_fields."""

from __future__ import annotations

import pytest

from juthoor_datacore_lv0.features.build_text_fields import (
    build_form_text,
    build_meaning_text,
    iter_text_fields,
)


# ── build_form_text ──────────────────────────────────────────────

class TestBuildFormText:
    def test_arabic_prefix(self):
        result = build_form_text(language="arabic", lemma="كتب")
        assert result == "AR: كتب"

    def test_arabic_with_translit_and_ipa(self):
        result = build_form_text(language="arabic", lemma="كتب", translit="ktb", ipa="kataba")
        assert result == "AR: كتب | TR: ktb | IPA: kataba"

    def test_non_arabic_plain(self):
        result = build_form_text(language="latin", lemma="aqua")
        assert result == "aqua"

    def test_non_arabic_with_ipa(self):
        result = build_form_text(language="english", lemma="water", ipa="ˈwɔːtər")
        assert result == "water | IPA: ˈwɔːtər"

    def test_empty_lemma(self):
        result = build_form_text(language="latin", lemma="")
        assert result == ""

    def test_none_translit_and_ipa_omitted(self):
        result = build_form_text(language="latin", lemma="rex", translit=None, ipa=None)
        assert result == "rex"

    def test_arabic_language_prefix_match(self):
        """Any language starting with 'ar' gets the AR: prefix."""
        result = build_form_text(language="aramaic", lemma="מלך")
        assert result.startswith("AR: ")


# ── build_meaning_text ───────────────────────────────────────────

class TestBuildMeaningText:
    def test_prefers_gloss_plain(self):
        text, fallback = build_meaning_text(gloss_plain="to write", lemma="كتب")
        assert text == "to write"
        assert fallback is False

    def test_fallback_definition_with_lemma(self):
        text, fallback = build_meaning_text(gloss_plain=None, lemma="aqua", fallback_definition="water")
        assert text == "aqua — water"
        assert fallback is True

    def test_fallback_definition_without_lemma(self):
        text, fallback = build_meaning_text(gloss_plain=None, lemma=None, fallback_definition="water")
        assert text == "water"
        assert fallback is True

    def test_no_gloss_no_fallback(self):
        text, fallback = build_meaning_text(gloss_plain=None, lemma="test")
        assert text is None
        assert fallback is False

    def test_whitespace_only_gloss_treated_as_empty(self):
        text, fallback = build_meaning_text(gloss_plain="   ", lemma="test")
        assert text is None

    def test_whitespace_stripped(self):
        text, _ = build_meaning_text(gloss_plain="  hello world  ")
        assert text == "hello world"


# ── iter_text_fields ─────────────────────────────────────────────

class TestIterTextFields:
    def test_enriches_row(self):
        rows = [{"language": "latin", "lemma": "aqua", "gloss_plain": "water"}]
        result = list(iter_text_fields(rows))
        assert len(result) == 1
        assert result[0]["form_text"] == "aqua"
        assert result[0]["meaning_text"] == "water"

    def test_uses_ipa_raw_fallback(self):
        rows = [{"language": "english", "lemma": "cat", "ipa_raw": "/kæt/"}]
        result = list(iter_text_fields(rows))
        assert "IPA: /kæt/" in result[0]["form_text"]

    def test_no_meaning_when_no_gloss(self):
        rows = [{"language": "latin", "lemma": "rex"}]
        result = list(iter_text_fields(rows))
        assert "meaning_text" not in result[0]

    def test_does_not_mutate_input(self):
        original = {"language": "latin", "lemma": "aqua"}
        list(iter_text_fields([original]))
        assert "form_text" not in original

    def test_arabic_form_text(self):
        rows = [{"language": "arabic", "lemma": "كتب"}]
        result = list(iter_text_fields(rows))
        assert result[0]["form_text"] == "AR: كتب"
