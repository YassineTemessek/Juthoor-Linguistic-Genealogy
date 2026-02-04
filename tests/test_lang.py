"""
Tests for language code resolution and family mappings.

These tests verify the SONAR language code mappings and language family utilities.
"""

import pytest


class TestResolveSonarLang:
    """Test SONAR language resolution."""

    def test_arabic_variants(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang

        assert resolve_sonar_lang("ar", None) == "arb_Arab"
        assert resolve_sonar_lang("ara", None) == "arb_Arab"
        assert resolve_sonar_lang("arb", None) == "arb_Arab"

    def test_quranic_arabic(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang

        assert resolve_sonar_lang("ar-qur", None) == "arb_Arab"
        assert resolve_sonar_lang("ara-qur", None) == "arb_Arab"

    def test_override_takes_precedence(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang

        result = resolve_sonar_lang("ar", "custom_Lang")
        assert result == "custom_Lang"

    def test_unknown_raises(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang

        with pytest.raises(ValueError, match="Unknown SONAR"):
            resolve_sonar_lang("xyz_unknown", None)

    def test_empty_raises(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang

        with pytest.raises(ValueError, match="Missing"):
            resolve_sonar_lang("", None)

    def test_case_insensitive(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang

        assert resolve_sonar_lang("AR", None) == "arb_Arab"
        assert resolve_sonar_lang("Eng", None) == "eng_Latn"
        assert resolve_sonar_lang("HEB", None) == "heb_Hebr"

    def test_whitespace_handling(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang

        assert resolve_sonar_lang("  ar  ", None) == "arb_Arab"
        assert resolve_sonar_lang("\teng\n", None) == "eng_Latn"


class TestSemiticLanguages:
    """Test Semitic language mappings."""

    def test_akkadian(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang

        # Akkadian maps to Arabic as fallback
        assert resolve_sonar_lang("akk", None) == "arb_Arab"
        assert resolve_sonar_lang("akkadian", None) == "arb_Arab"

    def test_punic_phoenician(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang

        # Punic/Phoenician map to Hebrew as closest Canaanite
        assert resolve_sonar_lang("xpu", None) == "heb_Hebr"
        assert resolve_sonar_lang("phn", None) == "heb_Hebr"
        assert resolve_sonar_lang("punic", None) == "heb_Hebr"
        assert resolve_sonar_lang("phoenician", None) == "heb_Hebr"

    def test_ugaritic(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang

        assert resolve_sonar_lang("uga", None) == "heb_Hebr"
        assert resolve_sonar_lang("ugaritic", None) == "heb_Hebr"

    def test_geez(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang

        assert resolve_sonar_lang("gez", None) == "arb_Arab"
        assert resolve_sonar_lang("geez", None) == "arb_Arab"

    def test_aramaic_variants(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang

        assert resolve_sonar_lang("syr", None) == "syc_Syrc"
        assert resolve_sonar_lang("syc", None) == "syc_Syrc"
        assert resolve_sonar_lang("arc", None) == "syc_Syrc"
        assert resolve_sonar_lang("jpa", None) == "syc_Syrc"
        assert resolve_sonar_lang("tmr", None) == "syc_Syrc"

    def test_hebrew(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang

        assert resolve_sonar_lang("he", None) == "heb_Hebr"
        assert resolve_sonar_lang("heb", None) == "heb_Hebr"
        assert resolve_sonar_lang("hbo", None) == "heb_Hebr"  # Biblical Hebrew

    def test_amharic(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang

        assert resolve_sonar_lang("am", None) == "amh_Ethi"
        assert resolve_sonar_lang("amh", None) == "amh_Ethi"


class TestIndoEuropeanLanguages:
    """Test Indo-European language mappings."""

    def test_english(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang

        assert resolve_sonar_lang("en", None) == "eng_Latn"
        assert resolve_sonar_lang("eng", None) == "eng_Latn"
        assert resolve_sonar_lang("ang", None) == "eng_Latn"  # Old English

    def test_latin(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang

        assert resolve_sonar_lang("la", None) == "lat_Latn"
        assert resolve_sonar_lang("lat", None) == "lat_Latn"

    def test_greek(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import resolve_sonar_lang

        assert resolve_sonar_lang("grc", None) == "ell_Grek"  # Ancient Greek
        assert resolve_sonar_lang("el", None) == "ell_Grek"   # Modern Greek
        assert resolve_sonar_lang("ell", None) == "ell_Grek"


class TestGetLanguageFamily:
    """Test language family detection."""

    def test_semitic_family(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import get_language_family

        assert get_language_family("ara") == "semitic"
        assert get_language_family("heb") == "semitic"
        assert get_language_family("akk") == "semitic"
        assert get_language_family("phn") == "semitic"

    def test_germanic_family(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import get_language_family

        assert get_language_family("eng") == "indo_european_germanic"
        assert get_language_family("deu") == "indo_european_germanic"

    def test_romance_family(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import get_language_family

        assert get_language_family("lat") == "indo_european_romance"
        assert get_language_family("fra") == "indo_european_romance"
        assert get_language_family("spa") == "indo_european_romance"

    def test_unknown_family(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import get_language_family

        assert get_language_family("xyz_unknown") is None
        assert get_language_family("") is None


class TestAreSameFamily:
    """Test language family comparison."""

    def test_same_family(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import are_same_family

        assert are_same_family("ara", "heb") is True
        assert are_same_family("eng", "deu") is True
        assert are_same_family("lat", "fra") is True

    def test_different_families(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import are_same_family

        assert are_same_family("ara", "eng") is False
        assert are_same_family("heb", "lat") is False

    def test_unknown_language(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.lang import are_same_family

        assert are_same_family("ara", "xyz") is False
        assert are_same_family("xyz", "abc") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
