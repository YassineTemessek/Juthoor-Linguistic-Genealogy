from __future__ import annotations

from juthoor_arabicgenome_lv1.factory.composition_models import (
    model_dialectical,
    model_intersection,
    model_phonetic_gestural,
    model_sequence,
)
from juthoor_arabicgenome_lv1.factory.scoring import (
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
    assert "ضغط" in gestural.predicted_features
    assert "عمق" in gestural.predicted_features


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
