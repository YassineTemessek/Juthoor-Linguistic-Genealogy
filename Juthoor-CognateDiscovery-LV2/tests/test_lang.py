"""
Tests for juthoor_cognatediscovery_lv2.lv3.discovery.lang

Covers:
- DEFAULT_SONAR_LANG_MAP lookups
- resolve_sonar_lang()
- get_language_family()
- are_same_family()
- LANGUAGE_FAMILIES structure integrity
"""
from __future__ import annotations

import pytest

from juthoor_cognatediscovery_lv2.lv3.discovery.lang import (
    DEFAULT_SONAR_LANG_MAP,
    LANGUAGE_FAMILIES,
    are_same_family,
    get_language_family,
    resolve_sonar_lang,
)


# ---------------------------------------------------------------------------
# LANGUAGE_FAMILIES integrity
# ---------------------------------------------------------------------------

class TestLanguageFamiliesStructure:
    def test_all_family_values_are_lists(self):
        for family, members in LANGUAGE_FAMILIES.items():
            assert isinstance(members, list), f"{family} should be a list"

    def test_no_duplicate_members_within_family(self):
        for family, members in LANGUAGE_FAMILIES.items():
            assert len(members) == len(set(members)), (
                f"Duplicate codes in family {family!r}: {members}"
            )

    def test_known_families_present(self):
        expected = {
            "semitic",
            "indo_european_germanic",
            "indo_european_romance",
            "indo_european_hellenic",
        }
        assert expected.issubset(set(LANGUAGE_FAMILIES.keys()))

    def test_semitic_contains_arabic_variants(self):
        semitic = LANGUAGE_FAMILIES["semitic"]
        for code in ("ar", "ara", "arb", "he", "heb"):
            assert code in semitic, f"{code!r} missing from semitic family"

    def test_germanic_contains_english_variants(self):
        germanic = LANGUAGE_FAMILIES["indo_european_germanic"]
        for code in ("en", "eng", "ang", "enm"):
            assert code in germanic

    def test_romance_contains_latin(self):
        romance = LANGUAGE_FAMILIES["indo_european_romance"]
        assert "la" in romance or "lat" in romance

    def test_all_member_codes_are_lowercase(self):
        for family, members in LANGUAGE_FAMILIES.items():
            for code in members:
                assert code == code.lower(), (
                    f"Code {code!r} in family {family!r} is not lowercase"
                )


# ---------------------------------------------------------------------------
# get_language_family()
# ---------------------------------------------------------------------------

class TestGetLanguageFamily:
    @pytest.mark.parametrize("code,expected_family", [
        ("ar",  "semitic"),
        ("ara", "semitic"),
        ("arb", "semitic"),
        ("he",  "semitic"),
        ("heb", "semitic"),
        ("hbo", "semitic"),
        ("arc", "semitic"),
        ("akk", "semitic"),
        ("gez", "semitic"),
        ("am",  "semitic"),
        ("en",  "indo_european_germanic"),
        ("eng", "indo_european_germanic"),
        ("ang", "indo_european_germanic"),
        ("enm", "indo_european_germanic"),
        ("de",  "indo_european_germanic"),
        ("deu", "indo_european_germanic"),
        ("la",  "indo_european_romance"),
        ("lat", "indo_european_romance"),
        ("fr",  "indo_european_romance"),
        ("es",  "indo_european_romance"),
        ("it",  "indo_european_romance"),
        ("grc", "indo_european_hellenic"),
        ("el",  "indo_european_hellenic"),
        ("fa",  "indo_european_iranian"),
        ("tr",  "turkic"),
        ("tur", "turkic"),
    ])
    def test_known_codes(self, code, expected_family):
        assert get_language_family(code) == expected_family

    def test_unknown_code_returns_none(self):
        assert get_language_family("xx") is None

    def test_empty_string_returns_none(self):
        assert get_language_family("") is None

    def test_whitespace_only_returns_none(self):
        assert get_language_family("   ") is None

    def test_case_insensitive_lookup(self):
        # ISO codes are lowercase in the map, but function should handle uppercase input
        assert get_language_family("AR") == "semitic"
        assert get_language_family("EN") == "indo_european_germanic"

    def test_leading_trailing_whitespace_stripped(self):
        assert get_language_family("  ar  ") == "semitic"


# ---------------------------------------------------------------------------
# are_same_family()
# ---------------------------------------------------------------------------

class TestAreSameFamily:
    @pytest.mark.parametrize("lang1,lang2", [
        ("ar",  "he"),      # both semitic
        ("ara", "heb"),     # both semitic (3-letter codes)
        ("arc", "akk"),     # Aramaic + Akkadian, both semitic
        ("en",  "de"),      # both germanic
        ("eng", "deu"),     # both germanic (3-letter codes)
        ("la",  "fr"),      # both romance
        ("lat", "es"),      # Latin + Spanish
        ("grc", "el"),      # Ancient + Modern Greek
        ("fa",  "sa"),      # Persian + Sanskrit, both Iranian
    ])
    def test_same_family_returns_true(self, lang1, lang2):
        assert are_same_family(lang1, lang2) is True

    @pytest.mark.parametrize("lang1,lang2", [
        ("ar", "en"),       # semitic vs germanic
        ("he", "la"),       # semitic vs romance
        ("ar", "tr"),       # semitic vs turkic
        ("en", "grc"),      # germanic vs hellenic
        ("fr", "ar"),       # romance vs semitic
        ("de", "fa"),       # germanic vs iranian
    ])
    def test_different_family_returns_false(self, lang1, lang2):
        assert are_same_family(lang1, lang2) is False

    def test_unknown_lang1_returns_false(self):
        assert are_same_family("xx", "ar") is False

    def test_unknown_lang2_returns_false(self):
        assert are_same_family("ar", "xx") is False

    def test_both_unknown_returns_false(self):
        assert are_same_family("xx", "yy") is False

    def test_empty_string_returns_false(self):
        assert are_same_family("", "ar") is False
        assert are_same_family("ar", "") is False
        assert are_same_family("", "") is False

    def test_symmetric(self):
        # are_same_family should be symmetric
        assert are_same_family("ar", "he") == are_same_family("he", "ar")
        assert are_same_family("en", "ar") == are_same_family("ar", "en")

    def test_reflexive_known_lang(self):
        # A language is always in the same family as itself
        assert are_same_family("ar", "ar") is True
        assert are_same_family("en", "en") is True


# ---------------------------------------------------------------------------
# DEFAULT_SONAR_LANG_MAP structure
# ---------------------------------------------------------------------------

class TestSonarLangMap:
    def test_arabic_maps_to_arb_arab(self):
        assert DEFAULT_SONAR_LANG_MAP["ar"] == "arb_Arab"
        assert DEFAULT_SONAR_LANG_MAP["ara"] == "arb_Arab"

    def test_english_maps_to_eng_latn(self):
        assert DEFAULT_SONAR_LANG_MAP["en"] == "eng_Latn"

    def test_hebrew_maps_to_heb_hebr(self):
        assert DEFAULT_SONAR_LANG_MAP["he"] == "heb_Hebr"

    def test_latin_maps_to_lat_latn(self):
        assert DEFAULT_SONAR_LANG_MAP["la"] == "lat_Latn"

    def test_all_values_have_underscore_format(self):
        """SONAR codes should follow the '<lang>_<Script>' convention."""
        for key, value in DEFAULT_SONAR_LANG_MAP.items():
            assert "_" in value, (
                f"SONAR code for {key!r} is {value!r} — expected '<lang>_<Script>' format"
            )


# ---------------------------------------------------------------------------
# resolve_sonar_lang()
# ---------------------------------------------------------------------------

class TestResolveSonarLang:
    def test_known_lang_no_override(self):
        assert resolve_sonar_lang("ar", None) == "arb_Arab"
        assert resolve_sonar_lang("en", None) == "eng_Latn"
        assert resolve_sonar_lang("la", None) == "lat_Latn"

    def test_override_takes_precedence(self):
        result = resolve_sonar_lang("ar", "custom_Arab")
        assert result == "custom_Arab"

    def test_override_ignores_lang_entirely(self):
        # Even an unknown lang code should work when override is provided
        result = resolve_sonar_lang("xx_unknown", "eng_Latn")
        assert result == "eng_Latn"

    def test_unknown_lang_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown SONAR language mapping"):
            resolve_sonar_lang("xx_unknown", None)

    def test_empty_lang_raises_value_error(self):
        with pytest.raises(ValueError):
            resolve_sonar_lang("", None)

    def test_whitespace_lang_raises_value_error(self):
        with pytest.raises(ValueError):
            resolve_sonar_lang("   ", None)
