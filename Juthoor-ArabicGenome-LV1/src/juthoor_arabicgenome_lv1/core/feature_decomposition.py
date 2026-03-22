from __future__ import annotations

import re
from collections import Counter
from typing import Iterable


ATOMIC_FEATURE_CATEGORIES: dict[str, tuple[str, ...]] = {
    "pressure_force": (
        "ضغط",
        "احتباس",
        "تعقد",
        "اشتداد",
        "إمساك",
        "امتساك",
        "قوة",
        "تقوية",
        "تأكيد",
        "ثقل",
    ),
    "extension_movement": (
        "امتداد",
        "استرسال",
        "طول",
        "اتساع",
        "خروج",
        "انتقال",
        "وصول",
        "بروز",
        "ظهور",
        "صعود",
    ),
    "penetration_passage": (
        "نفاذ",
        "خلوص",
        "اختراق",
        "نقص",
    ),
    "gathering_cohesion": (
        "تجمع",
        "اكتناز",
        "ازدحام",
        "التحام",
        "تلاصق",
        "تماسك",
        "اشتمال",
        "احتواء",
        "اتصال",
    ),
    "spreading_dispersal": (
        "تفشي",
        "انتشار",
        "طرد",
        "إبعاد",
        "فراغ",
        "إفراغ",
        "تفرق",
        "تخلخل",
    ),
    "texture_quality": (
        "رخاوة",
        "غلظ",
        "كثافة",
        "ثخانة",
        "دقة",
        "رقة",
        "لطف",
        "هشاشة",
        "جفاف",
    ),
    "sharpness_cutting": (
        "حدة",
        "قطع",
        "صدم",
        "احتكاك",
    ),
    "spatial_orientation": (
        "باطن",
        "ظاهر",
        "عمق",
        "جوف",
        "حيز",
        "سطح",
    ),
    "independence_distinction": (
        "استقلال",
        "تميز",
        "تعلق",
        "استواء",
        "وحدة",
    ),
}

FEATURE_TO_CATEGORY = {
    feature: category
    for category, features in ATOMIC_FEATURE_CATEGORIES.items()
    for feature in features
}

FEATURE_SYNONYMS: dict[str, tuple[str, ...]] = {
    "تفشي": ("تفش", "تفشٍ", "تفشٍّ"),
    "رخاوة": ("رخو",),
    "غلظ": ("غليظ", "استغلاظ", "استغلظ", "غلظة"),
    "دقة": ("دقيق",),
    "رقة": ("رقيق",),
    "احتواء": ("يحتوي",),
    "تأكيد": ("تؤكد", "تأكيداً"),
    "تقوية": ("يقوي",),
    "اتصال": ("وصل", "الوصل"),
    "تجمع": ("جمع", "تراكمي", "التئام"),
    "إمساك": ("يمسك",),
    "امتساك": ("ممسك",),
    "تخلخل": ("خلخلة",),
    "بروز": ("برز",),
    "ظهور": ("ظهر", "اتضاح"),
    "اتساع": ("انفتاح", "اتسع"),
    "استرسال": ("جريان", "تكرار", "منتظم"),
    "خروج": ("انبثاق", "انطلاق"),
    "احتكاك": ("احتكاكي",),
    "نفاذ": ("نافذ",),
    "حِدة": ("حدة",),
    "لطف": ("لطيف",),
    "تلاصق": ("التصاق",),
    "استواء": ("مستوي",),
}

FEATURE_POLARITIES: dict[str, str] = {
    "تجمع": "تفرق",
    "تفرق": "تجمع",
    "ضغط": "فراغ",
    "فراغ": "ضغط",
    "إفراغ": "احتواء",
    "احتواء": "إفراغ",
    "باطن": "ظاهر",
    "ظاهر": "باطن",
    "اتصال": "استقلال",
    "استقلال": "اتصال",
    "امتساك": "انتشار",
    "انتشار": "امتساك",
    "تلاصق": "إبعاد",
    "إبعاد": "تلاصق",
    "تماسك": "تخلخل",
    "تخلخل": "تماسك",
    "اختراق": "احتباس",
    "احتباس": "اختراق",
}

_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670\u0640]")
_NON_ARABIC_WORD = re.compile(r"[^\u0621-\u064A0-9\s/]+")


def normalize_arabic_text(text: str | None) -> str:
    value = (text or "").strip()
    value = _DIACRITICS.sub("", value)
    value = value.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    value = value.replace("ؤ", "و").replace("ئ", "ي").replace("ى", "ي").replace("ة", "ه")
    value = _NON_ARABIC_WORD.sub(" ", value)
    return re.sub(r"\s+", " ", value).strip()


def _iter_feature_matches(text: str) -> Iterable[str]:
    normalized = normalize_arabic_text(text)
    if not normalized:
        return ()
    matches: list[tuple[int, str]] = []
    for feature in FEATURE_TO_CATEGORY:
        feature_norm = normalize_arabic_text(feature)
        position = normalized.find(feature_norm)
        if position >= 0:
            matches.append((position, feature))
            continue
        for synonym in FEATURE_SYNONYMS.get(feature, ()):
            synonym_norm = normalize_arabic_text(synonym)
            position = normalized.find(synonym_norm)
            if position >= 0:
                matches.append((position, feature))
                break
    matches.sort(key=lambda item: (item[0], item[1]))
    return tuple(dict.fromkeys(feature for _, feature in matches))


def decompose_semantic_text(text: str | None) -> tuple[str, ...]:
    return tuple(_iter_feature_matches(text or ""))


def feature_categories(features: Iterable[str]) -> tuple[str, ...]:
    return tuple(FEATURE_TO_CATEGORY[feature] for feature in features if feature in FEATURE_TO_CATEGORY)


def weighted_feature_vector(features: Iterable[str]) -> dict[str, float]:
    counts = Counter(features)
    return {feature: float(count) for feature, count in counts.items()}


def invert_features(features: Iterable[str]) -> tuple[str, ...]:
    inverted: list[str] = []
    for feature in features:
        inverted.append(FEATURE_POLARITIES.get(feature, feature))
    return tuple(inverted)
