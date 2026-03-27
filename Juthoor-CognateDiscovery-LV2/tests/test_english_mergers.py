from __future__ import annotations

from juthoor_cognatediscovery_lv2.discovery.phonetic_mergers import (
    _ENGLISH_BASE_MAP,
    build_target_to_arabic_map,
    merger_overlap,
    possible_arabic_letters,
)


def test_possible_arabic_letters_english() -> None:
    letters = possible_arabic_letters("eng", "crust")
    assert "ق" in letters or "ك" in letters  # c→ق/ك
    assert "ر" in letters  # r→ر
    assert "س" in letters or "ش" in letters  # s→س/ش
    assert "ت" in letters or "د" in letters  # t→ت/د


def test_possible_arabic_letters_english_alias() -> None:
    # "en" should resolve to "eng"
    letters_en = possible_arabic_letters("en", "book")
    letters_eng = possible_arabic_letters("eng", "book")
    assert letters_en == letters_eng


def test_merger_overlap_english() -> None:
    overlap = merger_overlap("ara", "قرس", "eng", "crust")
    assert len(overlap) > 0


def test_merger_overlap_english_king() -> None:
    # Arabic ملك (m-l-k), English "king" (k→ق/ك)
    overlap = merger_overlap("ara", "ملك", "eng", "king")
    assert "ك" in overlap or "ق" in overlap


def test_english_base_map_coverage() -> None:
    # All common English consonants should be covered
    for c in "bcdfghjklmnpqrstvwz":
        assert c in _ENGLISH_BASE_MAP, f"Missing English consonant: {c}"


def test_build_target_to_arabic_map_english() -> None:
    mapping = build_target_to_arabic_map("eng")
    assert "ب" in mapping["b"]
    assert "ف" in mapping["p"] or "ب" in mapping["p"]
    assert "ر" in mapping["r"]
    assert "ل" in mapping["l"]
    assert "م" in mapping["m"]
    assert "ن" in mapping["n"]


def test_english_map_s_variants() -> None:
    # English 's' maps to س and ش (primary mergers, ≥2 observations)
    assert "س" in _ENGLISH_BASE_MAP["s"]
    assert "ش" in _ENGLISH_BASE_MAP["s"]


def test_english_map_h_pharyngeals() -> None:
    # English 'h' should cover ه and ع (pharyngeal/glottal merger)
    assert "ه" in _ENGLISH_BASE_MAP["h"]
    assert "ع" in _ENGLISH_BASE_MAP["h"]


def test_english_map_g_variants() -> None:
    # English 'g' maps to ج and ق (two dominant Arabic correspondences)
    assert "ج" in _ENGLISH_BASE_MAP["g"]
    assert "ق" in _ENGLISH_BASE_MAP["g"]
