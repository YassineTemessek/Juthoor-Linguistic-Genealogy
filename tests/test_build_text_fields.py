"""
Tests for text field building utilities.

These tests verify form_text and meaning_text generation for embeddings.
"""

import pytest


class TestBuildFormText:
    """Test form_text generation."""

    def test_arabic_with_translit(self):
        from juthoor_datacore_lv0.features.build_text_fields import build_form_text

        result = build_form_text(language="ara", lemma="كتاب", translit="kitab")
        assert "AR: كتاب" in result
        assert "TR: kitab" in result

    def test_arabic_with_ipa(self):
        from juthoor_datacore_lv0.features.build_text_fields import build_form_text

        result = build_form_text(language="ar", lemma="كتب", translit="ktb", ipa="kataba")
        assert "AR: كتب" in result
        assert "TR: ktb" in result
        assert "IPA: kataba" in result

    def test_english_simple(self):
        from juthoor_datacore_lv0.features.build_text_fields import build_form_text

        result = build_form_text(language="eng", lemma="book")
        assert result == "book"

    def test_english_with_ipa(self):
        from juthoor_datacore_lv0.features.build_text_fields import build_form_text

        result = build_form_text(language="eng", lemma="book", ipa="bʊk")
        assert "book" in result
        assert "IPA: bʊk" in result

    def test_empty_lemma(self):
        from juthoor_datacore_lv0.features.build_text_fields import build_form_text

        result = build_form_text(language="eng", lemma="", translit=None)
        assert result == ""

    def test_none_values(self):
        from juthoor_datacore_lv0.features.build_text_fields import build_form_text

        result = build_form_text(language="eng", lemma="word", translit=None, ipa=None)
        assert result == "word"

    def test_all_fields(self):
        from juthoor_datacore_lv0.features.build_text_fields import build_form_text

        result = build_form_text(
            language="ara",
            lemma="قلم",
            translit="qalam",
            ipa="qalam"
        )
        assert "AR: قلم" in result
        assert "TR: qalam" in result
        assert "IPA: qalam" in result
        # Check delimiter
        assert " | " in result


class TestBuildMeaningText:
    """Test meaning_text generation."""

    def test_with_gloss(self):
        from juthoor_datacore_lv0.features.build_text_fields import build_meaning_text

        meaning, fallback = build_meaning_text(gloss_plain="a written work")
        assert meaning == "a written work"
        assert fallback is False

    def test_gloss_with_whitespace(self):
        from juthoor_datacore_lv0.features.build_text_fields import build_meaning_text

        meaning, fallback = build_meaning_text(gloss_plain="  book  ")
        assert meaning == "book"
        assert fallback is False

    def test_fallback_definition(self):
        from juthoor_datacore_lv0.features.build_text_fields import build_meaning_text

        meaning, fallback = build_meaning_text(
            gloss_plain=None,
            lemma="book",
            fallback_definition="printed pages bound together"
        )
        assert "book" in meaning
        assert "printed pages bound together" in meaning
        assert fallback is True

    def test_fallback_without_lemma(self):
        from juthoor_datacore_lv0.features.build_text_fields import build_meaning_text

        meaning, fallback = build_meaning_text(
            gloss_plain=None,
            lemma=None,
            fallback_definition="a definition"
        )
        assert meaning == "a definition"
        assert fallback is True

    def test_no_meaning_available(self):
        from juthoor_datacore_lv0.features.build_text_fields import build_meaning_text

        meaning, fallback = build_meaning_text(gloss_plain=None, lemma=None)
        assert meaning is None
        assert fallback is False

    def test_empty_gloss(self):
        from juthoor_datacore_lv0.features.build_text_fields import build_meaning_text

        meaning, fallback = build_meaning_text(gloss_plain="")
        assert meaning is None
        assert fallback is False

    def test_whitespace_only_gloss(self):
        from juthoor_datacore_lv0.features.build_text_fields import build_meaning_text

        meaning, fallback = build_meaning_text(gloss_plain="   ")
        assert meaning is None
        assert fallback is False


class TestTextFieldSpec:
    """Test TextFieldSpec dataclass."""

    def test_basic_creation(self):
        from juthoor_datacore_lv0.features.build_text_fields import TextFieldSpec

        spec = TextFieldSpec(form_text="AR: كتاب", meaning_text="book")
        assert spec.form_text == "AR: كتاب"
        assert spec.meaning_text == "book"
        assert spec.meaning_fallback is False

    def test_with_fallback(self):
        from juthoor_datacore_lv0.features.build_text_fields import TextFieldSpec

        spec = TextFieldSpec(
            form_text="word",
            meaning_text="word — definition",
            meaning_fallback=True
        )
        assert spec.meaning_fallback is True

    def test_none_values(self):
        from juthoor_datacore_lv0.features.build_text_fields import TextFieldSpec

        spec = TextFieldSpec(form_text=None, meaning_text=None)
        assert spec.form_text is None
        assert spec.meaning_text is None


class TestIterTextFields:
    """Test iter_text_fields generator."""

    def test_basic_iteration(self):
        from juthoor_datacore_lv0.features.build_text_fields import iter_text_fields

        rows = [
            {"language": "ara", "lemma": "كتاب", "translit": "kitab"},
            {"language": "eng", "lemma": "book"},
        ]

        results = list(iter_text_fields(rows))

        assert len(results) == 2
        assert "form_text" in results[0]
        assert "form_text" in results[1]

    def test_arabic_row(self):
        from juthoor_datacore_lv0.features.build_text_fields import iter_text_fields

        rows = [{"language": "ara", "lemma": "قلم", "translit": "qalam"}]
        result = list(iter_text_fields(rows))[0]

        assert "AR: قلم" in result["form_text"]
        assert "TR: qalam" in result["form_text"]

    def test_with_gloss(self):
        from juthoor_datacore_lv0.features.build_text_fields import iter_text_fields

        rows = [{
            "language": "eng",
            "lemma": "book",
            "gloss_plain": "a written work"
        }]
        result = list(iter_text_fields(rows))[0]

        assert result["meaning_text"] == "a written work"
        assert result["meaning_fallback"] is False

    def test_preserves_original_fields(self):
        from juthoor_datacore_lv0.features.build_text_fields import iter_text_fields

        rows = [{
            "id": "test_id",
            "language": "eng",
            "lemma": "test",
            "extra_field": "value"
        }]
        result = list(iter_text_fields(rows))[0]

        assert result["id"] == "test_id"
        assert result["extra_field"] == "value"

    def test_ipa_fallback(self):
        from juthoor_datacore_lv0.features.build_text_fields import iter_text_fields

        rows = [{
            "language": "eng",
            "lemma": "test",
            "ipa_raw": "tɛst"  # Uses ipa_raw as fallback
        }]
        result = list(iter_text_fields(rows))[0]

        assert "IPA: tɛst" in result["form_text"]

    def test_definition_fallback(self):
        from juthoor_datacore_lv0.features.build_text_fields import iter_text_fields

        rows = [{
            "language": "eng",
            "lemma": "word",
            "definition": "a unit of language"  # Uses definition as fallback
        }]
        result = list(iter_text_fields(rows))[0]

        # definition is used when gloss_plain is not available
        assert "meaning_text" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
