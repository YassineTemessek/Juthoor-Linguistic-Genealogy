from __future__ import annotations

from juthoor_arabicgenome_lv1.factory.composition_models import (
    model_dialectical,
    model_intersection,
    model_phonetic_gestural,
    model_sequence,
)
from juthoor_arabicgenome_lv1.factory.scoring import (
    build_consensus_scholar_letters,
    build_nucleus_score_rows,
    invert_features_extended,
    jaccard_similarity,
    weighted_jaccard_similarity,
)
from juthoor_arabicgenome_lv1.factory.root_predictor import (
    build_root_prediction_rows,
    choose_root_prediction_model,
    predict_root_from_parts,
    summarize_root_predictions,
)


def test_basic_similarity_functions() -> None:
    predicted = ("تجمع", "رخاوة")
    actual = ("تجمع", "تلاصق")
    assert jaccard_similarity(predicted, actual) == 1 / 3
    assert weighted_jaccard_similarity(predicted, actual) == 1 / 3


def test_similarity_functions_collapse_synonym_groups() -> None:
    predicted = ("امتداد", "نفاذ", "رخاوة")
    actual = ("طول", "اختراق", "قوة")
    assert jaccard_similarity(predicted, actual) == 2 / 4
    assert weighted_jaccard_similarity(predicted, actual) == 2 / 4


def test_similarity_functions_use_extended_root_synonym_groups() -> None:
    predicted = ("قوة", "ضغط", "خلوص", "استقلال", "ظاهر")
    actual = ("ثقل", "إمساك", "فراغ", "قطع", "ظهور")
    assert jaccard_similarity(predicted, actual) == 1.0
    assert weighted_jaccard_similarity(predicted, actual) == 1.0


def test_invert_features_extended_uses_sprint1_opposites() -> None:
    assert invert_features_extended(("قوة", "غلظ", "امتداد", "نقص")) == {
        "رخاوة",
        "رقة",
        "انحسار",
        "اتساع",
    }


def test_composition_models_return_features() -> None:
    assert model_intersection(("تجمع", "رخاوة"), ("تجمع", "تلاصق")).predicted_features == ("تجمع",)
    assert model_sequence(("تجمع", "رخاوة"), ("تلاصق", "ضغط")).predicted_features == ("تجمع", "رخاوة", "تلاصق", "ضغط")
    assert model_dialectical(("تجمع", "باطن"), ("تفرق", "ظاهر")).predicted_features
    gestural = model_phonetic_gestural(
        ("تجمع",),
        ("استرسال",),
        articulatory1={"sifaat": {"shidda": True}, "makhraj": {"makhraj_en": "between_lips"}},
        articulatory2={"sifaat": {"takrir": True}, "makhraj": {"makhraj_en": "deepest_throat"}},
    )
    assert gestural.predicted_features == ("تجمع", "استرسال")


def test_build_nucleus_score_rows_filters_missing_scholar_letters() -> None:
    nuclei = [
        {
            "binary_root": "بر",
            "letter1": "ب",
            "letter2": "ر",
            "actual_features": ("تجمع", "استرسال"),
        }
    ]
    scholars = {
        "jabal": {
            "ب": {"atomic_features": ("تجمع",), "articulatory_features": None},
            "ر": {"atomic_features": ("استرسال",), "articulatory_features": None},
        },
        "partial": {
            "ب": {"atomic_features": ("ظهور",), "articulatory_features": None},
        },
    }
    rows = build_nucleus_score_rows(nuclei, scholars)
    assert rows
    assert {row["scholar"] for row in rows} == {"jabal"}


def test_build_consensus_scholar_letters_supports_strict_and_weighted_modes() -> None:
    scholars = {
        "jabal": {
            "ب": {"letter_name": "الباء", "atomic_features": ("تجمع", "رخاوة"), "articulatory_features": None},
        },
        "asim_al_masri": {
            "ب": {"letter_name": "الباء", "atomic_features": ("خروج", "تجمع"), "articulatory_features": None},
        },
        "hassan_abbas": {
            "ب": {"letter_name": "الباء", "atomic_features": ("بروز",), "articulatory_features": None},
        },
    }
    strict = build_consensus_scholar_letters(scholars, mode="strict")
    weighted = build_consensus_scholar_letters(scholars, mode="weighted")
    assert strict["ب"]["atomic_features"] == ("اكتناز", "بروز")
    assert weighted["ب"]["atomic_features"] == ("اكتناز", "بروز", "رخاوة")


def test_build_nucleus_score_rows_includes_consensus_scholars_when_provided() -> None:
    nuclei = [
        {
            "binary_root": "بر",
            "letter1": "ب",
            "letter2": "ر",
            "actual_features": ("تجمع", "استرسال"),
        }
    ]
    scholars = {
        "jabal": {
            "ب": {"letter_name": "الباء", "atomic_features": ("تجمع", "رخاوة"), "articulatory_features": None},
            "ر": {"letter_name": "الراء", "atomic_features": ("استرسال",), "articulatory_features": None},
        },
        "asim_al_masri": {
            "ب": {"letter_name": "الباء", "atomic_features": ("تجمع", "خروج"), "articulatory_features": None},
            "ر": {"letter_name": "الراء", "atomic_features": ("انتقال",), "articulatory_features": None},
        },
    }
    scholars["consensus_strict"] = build_consensus_scholar_letters(scholars, mode="strict")
    rows = build_nucleus_score_rows(nuclei, scholars)
    assert "consensus_strict" in {row["scholar"] for row in rows}


def test_root_predictor_prefers_intersection_when_overlap_exists() -> None:
    prediction = predict_root_from_parts(
        root="حسب",
        binary_nucleus="حس",
        third_letter="ب",
        binary_features=("نفاذ", "حدة", "سطح"),
        third_letter_features=("تجمع", "نفاذ"),
        actual_features=("نفاذ", "تجمع"),
    )
    assert prediction.model_used == "intersection"
    assert "نفاذ" in prediction.predicted_features


def test_root_predictor_falls_back_when_no_overlap_exists() -> None:
    assert choose_root_prediction_model(("نفاذ",), ("تجمع",)) == "phonetic_gestural"


def test_root_predictor_uses_intersection_for_category_overlap() -> None:
    assert choose_root_prediction_model(("ظهور",), ("اتساع",)) == "intersection"


def test_build_root_prediction_rows_and_summary() -> None:
    roots = [
        {
            "root": "حسب",
            "binary_nucleus": "حس",
            "third_letter": "ب",
            "jabal_features": ("نفاذ", "تجمع"),
            "bab": "الحاء",
            "quranic_verse": None,
        }
    ]
    nuclei = [
        {
            "binary_root": "حس",
            "jabal_features": ("نفاذ", "حدة"),
        }
    ]
    scholars = {
        "jabal": {
            "ب": {"atomic_features": ("تجمع", "نفاذ"), "articulatory_features": None},
        }
    }
    rows = build_root_prediction_rows(roots, nuclei, scholars, scholar="jabal")
    assert rows[0]["root"] == "حسب"
    assert rows[0]["model"] == "intersection"
    summary = summarize_root_predictions(rows)
    assert summary["overall"]["roots"] == 1
    assert summary["by_model"]["intersection"]["count"] == 1


def test_build_root_prediction_rows_normalizes_letter_aliases() -> None:
    roots = [
        {
            "root": "بدأ",
            "binary_nucleus": "بد",
            "third_letter": "أ",
            "jabal_features": ("ظهور", "ضغط"),
            "bab": "الباء",
            "quranic_verse": None,
        },
        {
            "root": "بكى",
            "binary_nucleus": "بك",
            "third_letter": "ى",
            "jabal_features": ("اتصال",),
            "bab": "الباء",
            "quranic_verse": None,
        },
    ]
    nuclei = [
        {"binary_root": "بد", "jabal_features": ("ظهور",)},
        {"binary_root": "بك", "jabal_features": ("إمساك",)},
    ]
    scholars = {
        "jabal": {
            "ء": {"atomic_features": ("ضغط",), "articulatory_features": None},
            "ي": {"atomic_features": ("اتصال",), "articulatory_features": None},
        }
    }
    rows = build_root_prediction_rows(roots, nuclei, scholars, scholar="jabal")
    assert rows[0]["third_letter"] == "ء"
    assert rows[1]["third_letter"] == "ي"
    assert rows[0]["predicted_features"]
    assert rows[1]["predicted_features"]
