from __future__ import annotations

import pytest

from juthoor_arabicgenome_lv1.core.neili_constraints import (
    NeiliFlag,
    apply_neili_constraints,
    check_composition_coherence,
    check_conceptual_level,
    check_no_synonymy,
    is_quranic_root,
)


# ---------------------------------------------------------------------------
# NeiliFlag dataclass
# ---------------------------------------------------------------------------

def test_neili_flag_is_frozen() -> None:
    flag = NeiliFlag(constraint="no_synonymy", root="كتب", description="test", severity="hard")
    with pytest.raises(Exception):
        flag.root = "other"  # type: ignore[misc]


def test_neili_flag_str_includes_severity_and_root() -> None:
    flag = NeiliFlag(constraint="no_synonymy", root="كتب", description="desc", severity="hard")
    text = str(flag)
    assert "HARD" in text
    assert "كتب" in text
    assert "no_synonymy" in text


# ---------------------------------------------------------------------------
# check_no_synonymy
# ---------------------------------------------------------------------------

def test_no_synonymy_flags_identical_features_for_quranic_roots() -> None:
    predictions = [
        {"root": "كتب", "predicted_features": ("تجمع", "اتصال"), "is_quranic": True},
        {"root": "جمع", "predicted_features": ("تجمع", "اتصال"), "is_quranic": True},
    ]
    flags = check_no_synonymy(predictions)
    roots_flagged = {f.root for f in flags}
    assert "كتب" in roots_flagged
    assert "جمع" in roots_flagged
    assert all(f.constraint == "no_synonymy" for f in flags)
    assert all(f.severity == "hard" for f in flags)


def test_no_synonymy_skips_non_quranic_roots_when_quranic_only() -> None:
    predictions = [
        {"root": "كتب", "predicted_features": ("تجمع", "اتصال"), "is_quranic": False},
        {"root": "جمع", "predicted_features": ("تجمع", "اتصال"), "is_quranic": False},
    ]
    flags = check_no_synonymy(predictions, quranic_only=True)
    assert flags == []


def test_no_synonymy_includes_non_quranic_when_flag_is_false() -> None:
    predictions = [
        {"root": "كتب", "predicted_features": ("تجمع", "اتصال"), "is_quranic": False},
        {"root": "جمع", "predicted_features": ("تجمع", "اتصال"), "is_quranic": False},
    ]
    flags = check_no_synonymy(predictions, quranic_only=False)
    assert len(flags) == 2


def test_no_synonymy_no_flag_for_distinct_features() -> None:
    predictions = [
        {"root": "كتب", "predicted_features": ("تجمع", "اتصال"), "is_quranic": True},
        {"root": "فتح", "predicted_features": ("نفاذ", "اختراق"), "is_quranic": True},
    ]
    flags = check_no_synonymy(predictions)
    assert flags == []


def test_no_synonymy_empty_features_not_flagged() -> None:
    predictions = [
        {"root": "كتب", "predicted_features": (), "is_quranic": True},
        {"root": "جمع", "predicted_features": (), "is_quranic": True},
    ]
    flags = check_no_synonymy(predictions)
    assert flags == []


def test_no_synonymy_missing_is_quranic_treated_as_non_quranic() -> None:
    # No 'is_quranic' key — treated as False when quranic_only=True
    predictions = [
        {"root": "كتب", "predicted_features": ("تجمع",)},
        {"root": "جمع", "predicted_features": ("تجمع",)},
    ]
    flags = check_no_synonymy(predictions, quranic_only=True)
    assert flags == []


# ---------------------------------------------------------------------------
# check_conceptual_level
# ---------------------------------------------------------------------------

def test_conceptual_level_flags_instance_feature() -> None:
    pred = {"root": "وسع", "predicted_features": ("حيز", "اتساع")}
    flags = check_conceptual_level(pred)
    assert len(flags) == 1
    assert flags[0].constraint == "conceptual_level"
    assert "حيز" in flags[0].description


def test_conceptual_level_hard_when_majority_are_instance() -> None:
    pred = {"root": "سطح", "predicted_features": ("حيز", "سطح")}
    flags = check_conceptual_level(pred)
    assert len(flags) == 1
    assert flags[0].severity == "hard"


def test_conceptual_level_soft_when_minority_are_instance() -> None:
    pred = {"root": "وسع", "predicted_features": ("اتساع", "امتداد", "انتشار", "حيز")}
    flags = check_conceptual_level(pred)
    assert len(flags) == 1
    assert flags[0].severity == "soft"


def test_conceptual_level_no_flag_for_abstract_features() -> None:
    pred = {"root": "ربط", "predicted_features": ("اتصال", "تلاصق", "امتساك")}
    flags = check_conceptual_level(pred)
    assert flags == []


def test_conceptual_level_custom_instance_features() -> None:
    pred = {"root": "خرج", "predicted_features": ("خروج", "اتساع")}
    flags = check_conceptual_level(pred, instance_features=frozenset({"خروج"}))
    assert len(flags) == 1
    assert "خروج" in flags[0].description


# ---------------------------------------------------------------------------
# check_composition_coherence
# ---------------------------------------------------------------------------

def test_coherence_flags_semantic_opposites() -> None:
    # تجمع and تفرق are direct opposites in FEATURE_POLARITIES
    pred = {"root": "غرب", "predicted_features": ("تجمع", "تفرق", "اتصال")}
    flags = check_composition_coherence(pred)
    assert len(flags) == 1
    flag = flags[0]
    assert flag.constraint == "composition_coherence"
    assert flag.severity == "soft"
    assert "تجمع" in flag.description or "تفرق" in flag.description


def test_coherence_no_flag_for_coherent_prediction() -> None:
    pred = {"root": "وصل", "predicted_features": ("اتصال", "تلاصق", "امتساك")}
    flags = check_composition_coherence(pred)
    assert flags == []


def test_coherence_no_flag_for_single_feature() -> None:
    pred = {"root": "ضغط", "predicted_features": ("ضغط",)}
    flags = check_composition_coherence(pred)
    assert flags == []


def test_coherence_flags_too_many_categories() -> None:
    # Pick features from 4+ distinct categories with no direct opposite
    # pressure_force: ضغط
    # extension_movement: امتداد
    # texture_quality: رخاوة
    # sharpness_cutting: قطع
    # spatial_orientation: باطن
    pred = {
        "root": "خاص",
        "predicted_features": ("ضغط", "امتداد", "رخاوة", "قطع", "باطن"),
    }
    flags = check_composition_coherence(pred)
    # Should flag due to category spread (5 categories) or opposites
    assert len(flags) >= 1


# ---------------------------------------------------------------------------
# is_quranic_root
# ---------------------------------------------------------------------------

def test_is_quranic_root_returns_true_when_present() -> None:
    quranic = {"كتب", "فتح", "علم"}
    assert is_quranic_root("كتب", quranic) is True


def test_is_quranic_root_returns_false_when_absent() -> None:
    quranic = {"كتب", "فتح"}
    assert is_quranic_root("غرب", quranic) is False


def test_is_quranic_root_empty_set() -> None:
    assert is_quranic_root("كتب", set()) is False


# ---------------------------------------------------------------------------
# apply_neili_constraints — full pipeline
# ---------------------------------------------------------------------------

def _make_pred(root: str, features: tuple[str, ...], is_quranic: bool = True) -> dict:
    return {"root": root, "predicted_features": features, "is_quranic": is_quranic}


def test_apply_adds_neili_flags_field() -> None:
    predictions = [_make_pred("كتب", ("تجمع", "اتصال"))]
    result = apply_neili_constraints(predictions)
    assert "neili_flags" in result[0]


def test_apply_does_not_mutate_input_dicts() -> None:
    pred = _make_pred("كتب", ("تجمع", "اتصال"))
    original_keys = set(pred.keys())
    apply_neili_constraints([pred])
    assert set(pred.keys()) == original_keys


def test_apply_synonymy_detected_across_predictions() -> None:
    preds = [
        _make_pred("كتب", ("تجمع", "اتصال")),
        _make_pred("جمع", ("تجمع", "اتصال")),
    ]
    result = apply_neili_constraints(preds)
    for r in result:
        constraint_names = [f.constraint for f in r["neili_flags"]]
        assert "no_synonymy" in constraint_names


def test_apply_conceptual_flag_present() -> None:
    preds = [_make_pred("وسع", ("حيز", "اتساع", "امتداد"))]
    result = apply_neili_constraints(preds)
    constraint_names = [f.constraint for f in result[0]["neili_flags"]]
    assert "conceptual_level" in constraint_names


def test_apply_coherence_flag_present() -> None:
    preds = [_make_pred("غرب", ("تجمع", "تفرق", "اتصال"))]
    result = apply_neili_constraints(preds)
    constraint_names = [f.constraint for f in result[0]["neili_flags"]]
    assert "composition_coherence" in constraint_names


def test_apply_annotates_is_quranic_from_set() -> None:
    pred = {"root": "كتب", "predicted_features": ("تجمع",)}
    quranic_roots = {"كتب"}
    result = apply_neili_constraints([pred], quranic_roots=quranic_roots)
    assert result[0]["is_quranic"] is True


def test_apply_does_not_overwrite_existing_is_quranic() -> None:
    pred = {"root": "كتب", "predicted_features": ("تجمع",), "is_quranic": False}
    quranic_roots = {"كتب"}
    result = apply_neili_constraints([pred], quranic_roots=quranic_roots)
    # Existing value must not be overwritten
    assert result[0]["is_quranic"] is False


def test_apply_empty_predictions_returns_empty() -> None:
    assert apply_neili_constraints([]) == []


def test_apply_clean_prediction_has_no_flags() -> None:
    preds = [_make_pred("وصل", ("اتصال", "تلاصق", "امتساك"))]
    result = apply_neili_constraints(preds)
    assert result[0]["neili_flags"] == []
