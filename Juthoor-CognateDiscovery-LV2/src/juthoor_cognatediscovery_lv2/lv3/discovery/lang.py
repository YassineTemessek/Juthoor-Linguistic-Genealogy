"""
Language code mapping and language family metadata.

NOTE: The SONAR-specific language mappings (DEFAULT_SONAR_LANG_MAP,
resolve_sonar_lang) are DEPRECATED as of the BGE-M3 migration.
BGE-M3 is language-agnostic and does not require language codes.
These mappings are retained only for backward compatibility.

The language family utilities (LANGUAGE_FAMILIES, get_language_family,
are_same_family) remain active and useful for cognate discovery
prioritization and analysis.
"""

from __future__ import annotations

# Best-effort mappings from ISO codes to SONAR language codes.
# Override per corpus with `@<sonar_lang>` in the CLI.
DEFAULT_SONAR_LANG_MAP: dict[str, str] = {
    # ==========================================================================
    # SEMITIC LANGUAGES
    # ==========================================================================

    # Arabic variants
    "ar": "arb_Arab",
    "ara": "arb_Arab",
    "arb": "arb_Arab",
    "ar-qur": "arb_Arab",      # Quranic Arabic
    "ara-qur": "arb_Arab",
    "ar-cla": "arb_Arab",      # Classical Arabic
    "ara-cla": "arb_Arab",
    "ar-mod": "arb_Arab",      # Modern Standard Arabic
    "arz": "arz_Arab",         # Egyptian Arabic (if supported)

    # Hebrew
    "he": "heb_Hebr",
    "heb": "heb_Hebr",
    "hbo": "heb_Hebr",         # Ancient/Biblical Hebrew

    # Aramaic/Syriac (use Classical Syriac as closest SONAR support)
    "syr": "syc_Syrc",         # Syriac
    "syc": "syc_Syrc",         # Classical Syriac
    "arc": "syc_Syrc",         # Official/Imperial Aramaic
    "sam": "syc_Syrc",         # Samaritan Aramaic
    "jpa": "syc_Syrc",         # Jewish Palestinian Aramaic
    "tmr": "syc_Syrc",         # Jewish Babylonian Aramaic (Talmudic)
    "amw": "syc_Syrc",         # Western Neo-Aramaic
    "aii": "syc_Syrc",         # Assyrian Neo-Aramaic

    # Akkadian - No direct SONAR support, use Arabic as Semitic proxy
    # NOTE: Results may be suboptimal; consider form-based matching instead
    "akk": "arb_Arab",
    "akkadian": "arb_Arab",

    # Punic/Phoenician - Use Hebrew as closest Canaanite relative
    "phn": "heb_Hebr",         # Phoenician
    "xpu": "heb_Hebr",         # Punic
    "punic": "heb_Hebr",
    "phoenician": "heb_Hebr",

    # Ugaritic - Use Hebrew as closest Canaanite relative
    "uga": "heb_Hebr",
    "ugaritic": "heb_Hebr",

    # Ge'ez (Ethiopic) - Use Arabic as Semitic proxy
    "gez": "arb_Arab",
    "geez": "arb_Arab",

    # Modern Ethiopian Semitic
    "am": "amh_Ethi",          # Amharic
    "amh": "amh_Ethi",
    "ti": "tir_Ethi",          # Tigrinya (if supported)
    "tir": "tir_Ethi",

    # ==========================================================================
    # INDO-EUROPEAN LANGUAGES
    # ==========================================================================

    # English
    "en": "eng_Latn",
    "eng": "eng_Latn",
    "en-old": "eng_Latn",      # Old English -> Modern English model
    "ang": "eng_Latn",         # Old English (Anglo-Saxon)
    "enm": "eng_Latn",         # Middle English

    # German
    "de": "deu_Latn",
    "deu": "deu_Latn",
    "gmh": "deu_Latn",         # Middle High German
    "goh": "deu_Latn",         # Old High German

    # French
    "fr": "fra_Latn",
    "fra": "fra_Latn",
    "fro": "fra_Latn",         # Old French

    # Spanish
    "es": "spa_Latn",
    "spa": "spa_Latn",

    # Italian
    "it": "ita_Latn",
    "ita": "ita_Latn",

    # Portuguese
    "pt": "por_Latn",
    "por": "por_Latn",

    # Dutch
    "nl": "nld_Latn",
    "nld": "nld_Latn",

    # ==========================================================================
    # CLASSICAL LANGUAGES
    # ==========================================================================

    # Latin
    "la": "lat_Latn",
    "lat": "lat_Latn",

    # Ancient Greek
    "grc": "ell_Grek",         # Ancient Greek -> Modern Greek model

    # Modern Greek
    "el": "ell_Grek",
    "ell": "ell_Grek",

    # Sanskrit (if supported)
    "sa": "san_Deva",
    "san": "san_Deva",

    # ==========================================================================
    # IRANIAN LANGUAGES
    # ==========================================================================

    # Persian/Farsi
    "fa": "pes_Arab",
    "fas": "pes_Arab",
    "pes": "pes_Arab",
    "prs": "prs_Arab",         # Dari

    # ==========================================================================
    # TURKIC LANGUAGES
    # ==========================================================================

    # Turkish
    "tr": "tur_Latn",
    "tur": "tur_Latn",

    # ==========================================================================
    # OTHER LANGUAGES
    # ==========================================================================

    # Russian
    "ru": "rus_Cyrl",
    "rus": "rus_Cyrl",

    # Chinese
    "zh": "zho_Hans",
    "zho": "zho_Hans",

    # Hindi
    "hi": "hin_Deva",
    "hin": "hin_Deva",
}


# Language family metadata for cognate discovery prioritization
LANGUAGE_FAMILIES: dict[str, list[str]] = {
    "semitic": [
        "ar", "ara", "arb", "ar-qur", "ara-qur", "ar-cla",
        "he", "heb", "hbo",
        "syr", "syc", "arc", "sam", "jpa", "tmr",
        "akk", "akkadian",
        "phn", "xpu", "punic", "phoenician",
        "uga", "ugaritic",
        "gez", "geez",
        "am", "amh", "ti", "tir",
    ],
    "indo_european_germanic": [
        "en", "eng", "ang", "enm",
        "de", "deu", "gmh", "goh",
        "nl", "nld",
    ],
    "indo_european_romance": [
        "la", "lat",
        "fr", "fra", "fro",
        "es", "spa",
        "it", "ita",
        "pt", "por",
    ],
    "indo_european_hellenic": [
        "grc", "el", "ell",
    ],
    "indo_european_iranian": [
        "fa", "fas", "pes", "prs",
        "sa", "san",
    ],
    "turkic": [
        "tr", "tur",
    ],
}


def resolve_sonar_lang(lang: str, sonar_lang_override: str | None) -> str:
    """Resolve a language code to a SONAR-compatible language code.

    .. deprecated::
        BGE-M3 is language-agnostic. This function is retained for backward
        compatibility only and will be removed in a future version.
    """
    if sonar_lang_override:
        return sonar_lang_override
    key = (lang or "").strip().lower()
    if not key:
        raise ValueError("Missing `lang` for SONAR; provide `<lang>` and/or `@<sonar_lang>`.")
    if key in DEFAULT_SONAR_LANG_MAP:
        return DEFAULT_SONAR_LANG_MAP[key]
    raise ValueError(
        f"Unknown SONAR language mapping for lang={lang!r}. "
        "Provide an explicit SONAR code using `@<sonar_lang>` (e.g., `eng_Latn`, `arb_Arab`)."
    )


def get_language_family(lang: str) -> str | None:
    """
    Return the language family for a given language code.

    Args:
        lang: Language code to look up

    Returns:
        Language family name, or None if unknown

    Example:
        >>> get_language_family("ara")
        'semitic'
        >>> get_language_family("eng")
        'indo_european_germanic'
    """
    key = (lang or "").strip().lower()
    for family, members in LANGUAGE_FAMILIES.items():
        if key in members:
            return family
    return None


def are_same_family(lang1: str, lang2: str) -> bool:
    """
    Check if two languages belong to the same language family.

    Args:
        lang1: First language code
        lang2: Second language code

    Returns:
        True if both languages are in the same family, False otherwise
    """
    family1 = get_language_family(lang1)
    family2 = get_language_family(lang2)
    if family1 is None or family2 is None:
        return False
    return family1 == family2
