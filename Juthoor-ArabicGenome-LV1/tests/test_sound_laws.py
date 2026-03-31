from __future__ import annotations

from juthoor_arabicgenome_lv1.factory.sound_laws import (
    KHASHIM_SOUND_LAWS,
    are_makhraj_neighbors,
    are_in_same_succession_group,
    makhraj_id,
    normalize_arabic_root,
    project_root_by_target,
    project_root_sound_laws,
    semantic_corridor_letters,
    semantic_corridor_roots,
    substitution_options,
    succession_group,
)


def test_khashim_sound_laws_cover_the_nine_primary_shifts() -> None:
    assert set(KHASHIM_SOUND_LAWS) == {"ف", "ق", "ط", "ص", "ش", "ح", "ع", "غ", "خ"}


def test_normalize_arabic_root_strips_variants() -> None:
    assert normalize_arabic_root("أبوة") == "ابوه"
    assert normalize_arabic_root("رأى") == "راي"


def test_substitution_options_include_primary_shift_targets() -> None:
    assert "p" in substitution_options("ف", include_group_expansion=False)
    assert {"q", "c", "k", "g"} <= set(substitution_options("ق", include_group_expansion=False))
    assert "" in substitution_options("ع", include_group_expansion=False)


def test_succession_groups_capture_khashim_families() -> None:
    assert succession_group("ف") == "labials"
    assert succession_group("ش") == "sibilants"
    assert are_in_same_succession_group("ف", "ب")
    assert not are_in_same_succession_group("ف", "ق")


def test_makhraj_neighbors_capture_adjacent_front_of_mouth_letters() -> None:
    assert makhraj_id("ص") == 13
    assert makhraj_id("ذ") == 12
    assert are_makhraj_neighbors("ص", "ذ")
    assert not are_makhraj_neighbors("ص", "ع")


def test_semantic_corridor_letters_include_same_and_adjacent_makhraj_options() -> None:
    corridor = set(semantic_corridor_letters("ص"))
    assert "س" in corridor
    assert "ذ" in corridor
    assert "ص" not in corridor


def test_semantic_corridor_roots_generate_arabic_neighbor_forms() -> None:
    variants = set(semantic_corridor_roots("صقر", max_variants=128))
    assert "سقر" in variants
    assert "ذقر" in variants


def test_project_root_sound_laws_generates_khashim_style_variants() -> None:
    variants = project_root_sound_laws("فطر", include_group_expansion=False, max_variants=32)
    assert "fṭr" in variants
    assert "ptr" in variants


def test_project_root_sound_laws_supports_group_expansion() -> None:
    variants = project_root_sound_laws("شبح", include_group_expansion=True, max_variants=128)
    assert "spk" in variants or "sph" in variants or "sbc" in variants


def test_project_root_by_target_uses_broader_projection_for_cross_lingual_targets() -> None:
    hebrew_like = project_root_by_target("غلف", "hebrew")
    english_like = project_root_by_target("غلف", "english")
    assert "glf" in hebrew_like or "glf" in english_like
    assert len(english_like) >= len(project_root_sound_laws("غلف", include_group_expansion=False))
