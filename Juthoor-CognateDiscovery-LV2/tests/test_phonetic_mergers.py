from __future__ import annotations

from juthoor_cognatediscovery_lv2.discovery.phonetic_mergers import (
    build_target_to_arabic_map,
    has_merger_ambiguity,
    load_phonetic_mergers,
    merger_overlap,
)


def test_load_phonetic_mergers_is_nonempty() -> None:
    rules = load_phonetic_mergers()
    assert rules
    assert any(rule.target_lang == "heb" for rule in rules)


def test_hebrew_target_mapping_covers_ayin_merger() -> None:
    mapping = build_target_to_arabic_map("heb")
    assert {"ع", "غ"} <= mapping["ע"]


def test_merger_overlap_flags_arab_vs_erev_case() -> None:
    overlap = merger_overlap("ara", "عرب", "heb", "ערב")
    assert "ع" in overlap or "غ" in overlap
    assert has_merger_ambiguity("ara", "عرب", "heb", "ערב") is True


def test_zero_overlap_negative_stays_safe() -> None:
    overlap = merger_overlap("ara", "كلب", "fas", "سگ")
    assert overlap == set()
