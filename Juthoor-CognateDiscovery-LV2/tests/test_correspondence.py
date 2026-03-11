from __future__ import annotations

from juthoor_cognatediscovery_lv2.discovery.correspondence import (
    collapse_weak_radicals,
    correspondence_features,
    correspondence_string,
    normalize_hamza,
)


def test_normalize_hamza_collapses_variants():
    assert normalize_hamza("أخذ") == normalize_hamza("ءخذ")


def test_collapse_weak_radicals_removes_matres():
    assert collapse_weak_radicals("قول") == collapse_weak_radicals("قل")


def test_correspondence_string_groups_related_consonants():
    assert correspondence_string("ثور") == correspondence_string("طور")


def test_correspondence_features_detect_soft_equivalences():
    features = correspondence_features(
        {"root_norm": "أخذ", "lemma": "أخذ"},
        {"root_norm": "ءخذ", "lemma": "ءخذ"},
    )
    assert features["hamza_match"] == 1.0
    assert features["correspondence"] > 0.5
