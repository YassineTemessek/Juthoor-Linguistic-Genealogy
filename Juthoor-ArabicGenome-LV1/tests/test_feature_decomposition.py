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
    assert decompose_semantic_text("الاستقرار والرجوع") == ("استقرار", "رجوع")
    assert decompose_semantic_text("الحسن والنقاء") == ("خلوص",)


def test_decompose_root_meaning_aliases_for_empty_actual_recovery() -> None:
    assert "امتداد" in decompose_semantic_text("البقاء الدائم أو الإقامة الدائمة بلا حد")
    assert "احتواء" in decompose_semantic_text("غلاف للشيء العظيم أو المهم يسعه ويغطيه")
    assert "انتقال" in decompose_semantic_text("تحول عن الاتجاه إلى عكسه")
    assert "استرسال" in decompose_semantic_text("جريان الشيء أو سريانه بلا نهاية")
    assert "تعقد" in decompose_semantic_text("انحناء الشيء أو استدارته حول غيره")


def test_decompose_quranic_empty_root_glosses() -> None:
    thara = decompose_semantic_text("تخلل الندى ونحوه أثناء جرم باستر سال")
    assert "نفاذ" in thara
    assert "استرسال" in thara
    assert decompose_semantic_text("طي الشيء وإدخال أجزاء منه في أحنائه") == ("تعقد",)
    hifz = decompose_semantic_text("حياطة قوية ضابطة للشيء؛ فلا يضيع، ولا يتفلت")
    assert "احتواء" in hifz
    assert "قوة" in hifz
    assert "امتساك" in hifz
    sabgh = decompose_semantic_text("أن يمتد من الشيء ما يصير كالغشاء الساتر لما وراءه")
    assert "امتداد" in sabgh
    assert "اشتمال" in sabgh
    assert "باطن" in sabgh
    assert decompose_semantic_text("استجلاب الشيء من بعيد") == ("وصول", "امتداد")
    assert decompose_semantic_text("توقف ما يجري في الأثناء - أو منها - سكونًا أو انقطاعًا") == ("احتباس",)
    assert decompose_semantic_text("الطعن من بعيد") == ("اختراق", "امتداد")


def test_decompose_modulation_semantics_from_gap_audit() -> None:
    assert "فوران" in decompose_semantic_text("فوران الشيء أو امتلاؤه بما هو غض")
    assert "امتلاء" in decompose_semantic_text("امتلاء باطن الشيء بلطيف يصلحه")
    assert "صلابة" in decompose_semantic_text("اندفاع مع صلابة في الشيء المجتمع")
    assert "فجوة" in decompose_semantic_text("شق عظيم أو فجوة عظيمة في جرم شديد")
    assert "نصاعة" in decompose_semantic_text("ينضح على الظاهر نصاعة أو رقة")
