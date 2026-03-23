from __future__ import annotations

from juthoor_arabicgenome_lv1.core.feature_decomposition import (
    decompose_semantic_text,
    feature_categories,
    invert_features,
)


def test_decompose_jabal_letter_meaning() -> None:
    features = decompose_semantic_text("تجمع رخو مع تلاصق ما")
    assert features == ("تجمع", "رخاوة", "تلاصق")
    assert feature_categories(features) == (
        "gathering_cohesion",
        "texture_quality",
        "gathering_cohesion",
    )


def test_decompose_handles_synonyms_and_normalization() -> None:
    features = decompose_semantic_text("انبثاق الحركة من مكمنها مع اتضاح")
    assert "خروج" in features
    assert "ظهور" in features


def test_invert_features_maps_polarities() -> None:
    assert invert_features(("تجمع", "باطن", "ضغط")) == ("تفرق", "ظاهر", "فراغ")
    assert invert_features(("خروج", "وصول", "تعلق")) == ("احتواء", "إبعاد", "استقلال")


def test_decompose_compound_jabal_nucleus_meanings() -> None:
    assert decompose_semantic_text("النشر والتفريق") == ("انتشار", "تفرق")
    assert decompose_semantic_text("الانفتاح والمنفذ") == ("اتساع", "نفاذ")
    assert decompose_semantic_text("إفراز شيء مكروه ونفيه") == ("إفراغ", "إبعاد")


def test_decompose_extended_synonym_groups() -> None:
    assert decompose_semantic_text("الثبات والرسوخ") == ("امتساك", "تماسك")
    assert decompose_semantic_text("التغطية والإخفاء") == ("اشتمال", "باطن")
    assert decompose_semantic_text("الارتفاع الشاهق") == ("صعود",)
