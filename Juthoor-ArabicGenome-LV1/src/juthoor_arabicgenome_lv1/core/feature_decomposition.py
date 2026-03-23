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

FEATURE_VOCAB = tuple(FEATURE_TO_CATEGORY.keys())

# Keep a bounded synonym layer on top of the direct vocabulary scan.
# The aim is not full Arabic NLP; it is to catch Jabal's repeated paraphrases.
FEATURE_ALIASES: dict[str, tuple[str, ...]] = {
    "تفشي": ("تفش", "تفشٍ", "تفشٍّ"),
    "انتشار": ("نشر", "النشر"),
    "تفرق": ("تفريق", "التفريق"),
    "تخلخل": ("تفكك", "التفكك", "تسيب", "التسيب", "تفتت", "التفتت"),
    "رخاوة": ("رخو", "لين", "اللين", "ليونه", "الليونه", "طراءه", "طراءة", "طراوه"),
    "غلظ": ("غليظ", "غلظة", "استغلاظ", "صلب", "صلابه", "صلابة"),
    "كثافة": ("كثيف", "كثره", "كثرة", "امتلاء", "الامتلاء"),
    "دقة": ("دقيق",),
    "رقة": ("رقيق",),
    "لطف": ("لطيف", "مستطاب", "مستطابه", "مستطابة"),
    "تأكيد": ("تؤكد",),
    "قوة": ("شدة", "الشدة", "شديد", "اشتداد"),
    "ضغط": ("انضغاط", "حبس", "منع", "منعه"),
    "احتباس": ("انحباس", "محبوس", "محبس", "امتناع", "الامتناع"),
    "إمساك": ("منع", "منعه", "صد", "الصد", "قبض", "القبض", "انسداد", "الانسداد"),
    "امتساك": ("تمكن", "التمكن", "رسوخ", "الرسوخ", "ثبات", "الثبات", "وثاقه", "وثاقة", "تركز", "التركز"),
    "خروج": ("انبثاق", "انطلاق", "تفجر", "التفجر", "فوران", "الفوران"),
    "امتداد": ("تزايد", "التزايد"),
    "انتقال": ("تحرك", "التحرك", "رجوع", "الرجوع", "تردد", "التردد", "تحريك", "تحريكه", "معاوده", "معاودة"),
    "وصول": ("بلوغ", "البلوغ"),
    "ظهور": ("اتضاح", "كشف", "انكشاف", "الانكشاف", "بدو", "بدوه", "التكوين الاول"),
    "بروز": ("تبرز",),
    "اتصال": ("وصل", "اتباع", "الاتباع", "تداخل", "التداخل", "مماسه", "مماسة"),
    "تلاصق": ("التصاق", "لصوق", "اللصوق"),
    "تماسك": ("رسوخ", "تراكم", "التراكم"),
    "اشتمال": ("احاطة", "الاحاطة", "تغطية", "التغطية"),
    "احتواء": ("استعمال", "الاستعمال"),
    "اتساع": ("انفتاح", "الحوز", "حوز", "مجال"),
    "نفاذ": ("منفذ", "المنفذ", "ولوج"),
    "خلوص": ("التجرد", "خلاصه", "خلاصته"),
    "اختراق": ("شق", "الشق", "فتح", "الفتح"),
    "نقص": ("قلة", "القلة", "ضعف", "الضعف", "القصر"),
    "إفراغ": ("افراز", "إفراز"),
    "إبعاد": ("نفي", "نفيه", "دفع", "الدفع", "ازالة", "الازالة"),
    "فراغ": ("خلو", "الخلو", "خلوه", "الفراغ", "باطل"),
    "جفاف": ("يبوسة", "اليبوسة", "جاف"),
    "احتكاك": ("دلك", "الدلك", "حكا", "حك"),
    "صدم": ("ارتطام", "الارتطام"),
    "باطن": ("الصميم", "صميم", "اخفاء", "الاخفاء", "استتار", "الاستتار", "غياب", "الغياب", "تغطي", "التغطي", "انغماس", "الانغماس", "دس"),
    "ظاهر": ("خارج", "الخارج"),
    "عمق": ("العمق", "اغوار", "غور", "قعر", "غيور", "غئور"),
    "جوف": ("الجوف", "الحفره", "حفرة", "مقر", "المقر", "مستقر", "المستقر"),
    "حيز": ("حيز", "حوزه"),
    "سطح": ("السطح", "سطحي"),
    "استقلال": ("انفراد", "الانفراد", "انفصال", "الانفصال"),
    "تميز": ("التمايز",),
    "تعلق": ("لزوم", "اللزم", "ملازمه", "ملازمة"),
    "استواء": ("مستو", "مستوٍ"),
    "صعود": ("ارتفاع", "الارتفاع", "رفع", "الرفع"),
    "وحدة": ("واحدا", "واحد"),
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
    "خروج": "احتواء",
    "احتواء": "خروج",
    "وصول": "إبعاد",
    "تعلق": "استقلال",
    "ظهور": "باطن",
}

_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670\u0640]")
_NON_ARABIC = re.compile(r"[^\u0621-\u064A0-9\s/]+")


def normalize_arabic_text(text: str | None) -> str:
    value = (text or "").strip()
    value = _DIACRITICS.sub("", value)
    value = value.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    value = value.replace("ؤ", "و").replace("ئ", "ي").replace("ى", "ي").replace("ة", "ه")
    value = _NON_ARABIC.sub(" ", value)
    return re.sub(r"\s+", " ", value).strip()


def _iter_feature_matches(text: str) -> Iterable[str]:
    normalized = normalize_arabic_text(text)
    if not normalized:
        return ()

    matches: list[tuple[int, str]] = []
    for feature in FEATURE_VOCAB:
        feature_norm = normalize_arabic_text(feature)
        position = normalized.find(feature_norm)
        if position >= 0:
            matches.append((position, feature))
            continue
        for alias in FEATURE_ALIASES.get(feature, ()):
            alias_norm = normalize_arabic_text(alias)
            position = normalized.find(alias_norm)
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
    return tuple(FEATURE_POLARITIES.get(feature, feature) for feature in features)
