from __future__ import annotations

from juthoor_arabicgenome_lv1.factory.composition_models import (
    model_dialectical,
    model_intersection,
    model_phonetic_gestural,
    model_sequence,
)
from juthoor_arabicgenome_lv1.factory.scoring import (
    build_nucleus_score_rows,
    jaccard_similarity,
    weighted_jaccard_similarity,
)


def test_basic_similarity_functions() -> None:
    predicted = ("تجمع", "رخاوة")
    actual = ("تجمع", "تلاصق")
    assert jaccard_similarity(predicted, actual) == 1 / 3
    assert weighted_jaccard_similarity(predicted, actual) == 1 / 3


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
