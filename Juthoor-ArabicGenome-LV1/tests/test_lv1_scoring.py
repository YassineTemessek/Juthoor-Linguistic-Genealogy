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
    apply_neili_filters_to_prediction_rows,
    build_root_prediction_rows_all_scholars,
    build_root_prediction_rows,
    choose_root_prediction_model,
    filter_third_letter_features,
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


def test_filter_third_letter_features_blocks_poison_and_opposites() -> None:
    kept, dropped = filter_third_letter_features(
        ("تجمع", "تفرق"),
        ("التحام", "تجمع", "تجمع", "تفرق", "امتداد"),
    )
    assert "التحام" in dropped
    assert "تفرق" not in dropped
    assert "تجمع" in kept
    assert "تفرق" in kept
    assert "امتداد" in kept


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
    assert summary["by_scholar"]["jabal"]["count"] == 1


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


def test_build_root_prediction_rows_all_scholars() -> None:
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
        },
        "consensus_strict": {
            "ب": {"atomic_features": ("تجمع",), "articulatory_features": None},
        },
    }
    rows = build_root_prediction_rows_all_scholars(
        roots,
        nuclei,
        scholars,
        scholars=("jabal", "consensus_strict"),
    )
    assert {row["scholar"] for row in rows} == {"jabal", "consensus_strict"}
    summary = summarize_root_predictions(rows)
    assert summary["by_scholar"]["jabal"]["count"] == 1
    assert summary["by_scholar"]["consensus_strict"]["count"] == 1


def test_root_predictor_uses_nucleus_only_fallback_when_intersection_over_prunes() -> None:
    prediction = predict_root_from_parts(
        root="وسع",
        binary_nucleus="وس",
        third_letter="ع",
        binary_features=("ظهور", "حدة"),
        third_letter_features=("اتساع",),
        actual_features=("ظهور",),
    )
    assert prediction.model_used == "nucleus_only"
    assert prediction.predicted_features == ("ظهور", "حدة")


def test_apply_neili_filters_to_prediction_rows_adds_serialized_flags() -> None:
    rows = [
        {
            "root": "كتب",
            "scholar": "jabal",
            "model": "intersection",
            "predicted_features": ["تجمع", "اتصال"],
            "actual_features": ["تجمع"],
            "jaccard": 0.5,
            "weighted_jaccard": 0.5,
            "blended_jaccard": 0.5,
            "quranic_verse": "sample",
        },
        {
            "root": "جمع",
            "scholar": "jabal",
            "model": "intersection",
            "predicted_features": ["تجمع", "اتصال"],
            "actual_features": ["اتصال"],
            "jaccard": 0.5,
            "weighted_jaccard": 0.5,
            "blended_jaccard": 0.5,
            "quranic_verse": "sample",
        },
    ]
    enriched = apply_neili_filters_to_prediction_rows(rows)
    assert all("neili_flags" in row for row in enriched)
    assert all(isinstance(row["neili_flags"], list) for row in enriched)
    assert all(row["neili_hard_flag_count"] >= 1 for row in enriched)
    assert all(row["neili_valid"] is False for row in enriched)


def test_summarize_root_predictions_includes_neili_summary() -> None:
    rows = apply_neili_filters_to_prediction_rows(
        [
            {
                "root": "كتب",
                "scholar": "jabal",
                "model": "intersection",
                "predicted_features": ["تجمع", "اتصال"],
                "actual_features": ["تجمع"],
                "jaccard": 0.5,
                "weighted_jaccard": 0.5,
                "blended_jaccard": 0.5,
                "quranic_verse": "sample",
                "bab": "الكاف",
            },
            {
                "root": "جمع",
                "scholar": "jabal",
                "model": "intersection",
                "predicted_features": ["تجمع", "اتصال"],
                "actual_features": ["اتصال"],
                "jaccard": 0.5,
                "weighted_jaccard": 0.5,
                "blended_jaccard": 0.5,
                "quranic_verse": "sample",
                "bab": "الجيم",
            },
        ]
    )
    summary = summarize_root_predictions(rows)
    assert summary["overall"]["neili_hard_rejections"] == 2
    assert summary["neili_summary"]["constraint_counts"]["no_synonymy"] == 2


def test_summarize_root_predictions_includes_quranic_validation_split() -> None:
    rows = apply_neili_filters_to_prediction_rows(
        [
            {
                "root": "كتب",
                "scholar": "jabal",
                "model": "intersection",
                "predicted_features": ["تجمع"],
                "actual_features": ["تجمع"],
                "jaccard": 1.0,
                "weighted_jaccard": 1.0,
                "blended_jaccard": 1.0,
                "quranic_verse": "sample",
                "bab": "الكاف",
            },
            {
                "root": "غرب",
                "scholar": "jabal",
                "model": "sequence",
                "predicted_features": ["تفرق"],
                "actual_features": ["اتصال"],
                "jaccard": 0.0,
                "weighted_jaccard": 0.0,
                "blended_jaccard": 0.0,
                "quranic_verse": None,
                "bab": "الغين",
            },
        ]
    )
    summary = summarize_root_predictions(rows)
    assert summary["quranic_validation"]["quranic"]["count"] == 1
    assert summary["quranic_validation"]["non_quranic"]["count"] == 1
