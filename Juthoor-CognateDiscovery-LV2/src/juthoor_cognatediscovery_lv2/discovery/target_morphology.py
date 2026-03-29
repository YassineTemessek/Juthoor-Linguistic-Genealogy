"""Target-language morpheme decomposition and phonetic shift variants.

Handles two critical preprocessing steps for the reverse discovery pipeline:
1. Morpheme decomposition — extract root/stem from inflected/compound words
   (Latin, Ancient Greek, Old English)
2. Western phonetic shift variants — generate consonant skeleton alternatives
   based on known IE sound laws (Grimm's Law, Latin digraph shifts, etc.)

Purpose: Before extracting consonant skeletons and looking up Arabic matches,
every IE word must be decomposed to its meaningful root. Without this step,
inflectional affixes and epenthetic consonants pollute the skeleton comparison.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Iterator


# ---------------------------------------------------------------------------
# Vowel / consonant helpers
# ---------------------------------------------------------------------------

_VOWELS = frozenset("aeiouāēīōūæœ")
_ENG_CONSONANTS_RE = re.compile(r"[bcdfghjklmnpqrstvwxyz]")

# IPA vowel characters (for IPA-based skeleton extraction)
_IPA_VOWELS = frozenset(
    "aeiouæœøɑɐɒɔɛɜɞɪɨɵɯʊʏᵻ"
    "ɐɑɒɔɕɖɘɚɛɜɝɞɟɠɡɢɣɤɥɦɧɨɩɪɫɬɭɮɯɰɱɲɳɴɵɶɷɸɹɺɻɼɽɾɿ"
    "\u00e0\u00e1\u00e2\u00e3\u00e4\u00e5\u00e6"  # à á â ã ä å æ
    "\u00e8\u00e9\u00ea\u00eb"  # è é ê ë
    "\u00ec\u00ed\u00ee\u00ef"  # ì í î ï
    "\u00f2\u00f3\u00f4\u00f5\u00f6"  # ò ó ô õ ö
    "\u00f9\u00fa\u00fb\u00fc"  # ù ú û ü
)


def _to_latin(word: str) -> str:
    """Best-effort Greek-script to Latin transliteration (for decomposition)."""
    _GRC_MAP = {
        "α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e",
        "ζ": "z", "η": "e", "θ": "th", "ι": "i", "κ": "k",
        "λ": "l", "μ": "m", "ν": "n", "ξ": "x", "ο": "o",
        "π": "p", "ρ": "r", "σ": "s", "ς": "s", "τ": "t",
        "υ": "u", "φ": "ph", "χ": "kh", "ψ": "ps", "ω": "o",
    }
    result = []
    for ch in unicodedata.normalize("NFC", word.lower()):
        mapped = _GRC_MAP.get(ch)
        if mapped is not None:
            result.append(mapped)
        elif ch.isascii():
            result.append(ch)
        # drop other non-ASCII / accents
    return "".join(result)


# ---------------------------------------------------------------------------
# Latin morphology tables
# ---------------------------------------------------------------------------

# Ordered longest-first to ensure greedy matching
LATIN_SUFFIXES: tuple[str, ...] = (
    "ificare", "ificatio",
    "entia", "antia", "atura", "itura",
    "ositas", "ivitas",
    "abilis", "ibilis",
    "mentum", "ensis",
    "ember",  # month suffix: septem-ber
    "aster",
    "arius", "arium",
    "alis", "aris", "ilis", "anus", "inus", "icus", "osus", "ivus",
    "trix", "tion", "sion",
    "tura", "tudo",
    "tas", "tor", "sor", "tio",
    "ber",   # month suffix: septem-ber, octo-ber, novem-ber, decem-ber
    "men", "ium", "eus",
    "us", "um", "is", "es", "or", "io", "ia", "ae",
    "er", "ar", "ur",
    "a", "e", "i", "o",
)

LATIN_PREFIXES: tuple[str, ...] = (
    "trans", "super", "inter", "circum", "contra",
    "prae", "pref", "pros",
    "con", "com", "col", "cor",
    "sub", "sup", "suf", "suc",
    "per", "pro", "pre", "dis", "dif",
    "abs", "obs",
    "ad", "ab", "ob", "ex", "in", "im", "de", "re",
)

# Month-name number prefixes that precede "-ber" suffix
_LATIN_NUMBER_STEMS: dict[str, str] = {
    "septem": "sept",
    "octo": "oct",
    "novem": "nov",
    "decem": "dec",
    "quinque": "quinqu",
    "sex": "sex",
    "septem": "septem",
}


# ---------------------------------------------------------------------------
# Ancient Greek morphology tables
# ---------------------------------------------------------------------------

# Compound elements that are themselves meaningful — split into TWO stems
GREEK_COMPOUND_SUFFIXES: tuple[str, ...] = (
    "logia", "philia", "phobia", "graphia", "morphos", "phoros",
    "sophia", "kratia", "nomia", "patheia", "geneia",
)

GREEK_SUFFIXES: tuple[str, ...] = (
    "omai", "etai", "ontai",
    "eia", "oia", "sia",
    "tes", "ter", "tor", "eus",
    "sis", "xis", "psis",
    "mos", "sma", "tis",
    "ēs", "ōn", "ōr",
    "os", "on", "es", "is", "ma", "ē",
    "ai", "oi", "as",
    "a", "e", "i", "o",
)

GREEK_PREFIXES: tuple[str, ...] = (
    "amphi", "hyper", "hypo", "anti", "kata", "meta", "para", "peri",
    "pros", "apo", "dia", "epi", "syn", "ana",
    "ek", "ex", "en", "em",
    "an",  # alpha privative with n
    "a",   # alpha privative bare (last — shortest)
)


# ---------------------------------------------------------------------------
# Old English morphology tables
# ---------------------------------------------------------------------------

OE_SUFFIXES: tuple[str, ...] = (
    "ness", "ung", "dom", "scipe", "had", "lac",
    "wist", "estre",
    "lic",
    "end",
    "ere", "est",
    "ian", "ode", "ede",
    "um",   # dative plural (e.g., "wordum" → "word")
    "an", "on", "en",
    "ig", "isc",
    "e", "a", "u",
)

OE_PREFIXES: tuple[str, ...] = (
    "ge",
    "for", "mis", "un", "be", "of",
    "on", "to",
)

_MIN_STEM = 2  # minimum stem length after stripping


# ---------------------------------------------------------------------------
# Helper: strip one suffix from a word (returns None if no valid strip)
# ---------------------------------------------------------------------------

def _strip_suffix(word: str, suffixes: tuple[str, ...]) -> str | None:
    """Strip the first (longest) matching suffix. Returns None if none match."""
    for suf in suffixes:
        if word.endswith(suf):
            stem = word[: -len(suf)]
            if len(stem) >= _MIN_STEM:
                return stem
    return None


def _strip_all_suffixes(word: str, suffixes: tuple[str, ...]) -> list[str]:
    """Return stems for ALL matching suffixes (greedy: each suffix tried once).

    This allows "dominus" to yield both "dom" (strip "inus") and "domin" (strip "us").
    Results are sorted longest-first.
    """
    stems: list[str] = []
    seen: set[str] = set()
    for suf in suffixes:
        if word.endswith(suf):
            stem = word[: -len(suf)]
            if len(stem) >= _MIN_STEM and stem not in seen:
                seen.add(stem)
                stems.append(stem)
    stems.sort(key=len, reverse=True)
    return stems


def _strip_prefix(word: str, prefixes: tuple[str, ...]) -> str | None:
    for pre in prefixes:
        if word.startswith(pre):
            stem = word[len(pre):]
            if len(stem) >= _MIN_STEM:
                return stem
    return None


# ---------------------------------------------------------------------------
# Latin epenthetic consonant removal
# ---------------------------------------------------------------------------

def _remove_latin_epenthetic(stem: str) -> str | None:
    """Remove epenthetic consonants typical in Latin number words.

    - "m" before "b": "septem" → "sept" (but keep "mb" in true stems)
    - Final nasal before a following consonant cluster boundary
    """
    changed = stem
    # Remove trailing nasal before final consonant if it looks epenthetic
    # Pattern: word ends in vowel + m|n + consonant (e.g., "septem" → "sept")
    m = re.match(r"^(.+?[aeiou])(m|n)([bcdfghjklmnpqrstvwxyz]+)$", changed)
    if m:
        candidate = m.group(1) + m.group(3)
        if len(candidate) >= _MIN_STEM:
            return candidate
    # Simple: trailing "m" after vowel (e.g., "septem" → "septe")
    if len(changed) > 3 and changed[-1] == "m" and changed[-2] in "aeiou":
        candidate = changed[:-1]
        if len(candidate) >= _MIN_STEM:
            return candidate
    return None


# ---------------------------------------------------------------------------
# Function 1: decompose_target
# ---------------------------------------------------------------------------

def decompose_target(word: str, lang: str) -> list[str]:
    """Return candidate stems for *word* in language *lang*.

    Always includes the original word. Longest stems come first after the
    original, followed by shorter stripped variants. Duplicates are removed.

    Parameters
    ----------
    word:
        The word form as it appears in the corpus (may be inflected).
    lang:
        Language code: "lat", "grc", or "ang".  Other codes receive the
        original word only (no-op decomposition).

    Returns
    -------
    list[str]
        Unique candidate stems, original first.
    """
    word_lower = word.lower().strip()

    seen: dict[str, None] = {word_lower: None}  # insertion-ordered set
    candidates: list[str] = []  # additional stems (not the original)

    if lang == "lat":
        candidates = _decompose_latin(word_lower)
    elif lang == "grc":
        # Transliterate Greek script if necessary
        if any(ord(ch) > 127 for ch in word_lower):
            word_lower_latin = _to_latin(word_lower)
        else:
            word_lower_latin = word_lower
        candidates = _decompose_greek(word_lower_latin)
    elif lang == "ang":
        candidates = _decompose_old_english(word_lower)
    # else: no-op

    result: list[str] = [word_lower]
    for stem in candidates:
        if stem and stem not in seen and len(stem) >= _MIN_STEM:
            seen[stem] = None
            result.append(stem)
    return result


def _decompose_latin(word: str) -> list[str]:
    stems: list[str] = []

    # 1. Try stripping month suffix "-ber" specially: look for number prefix
    for num_stem, stripped in _LATIN_NUMBER_STEMS.items():
        if word.startswith(num_stem) and word.endswith("ber"):
            stems.append(num_stem)       # e.g., "septem"
            stems.append(stripped)       # e.g., "sept"
            # also try with epenthetic removal on the full word sans "-ber"
            body = word[:-3]  # strip "ber"
            ep = _remove_latin_epenthetic(body)
            if ep and len(ep) >= _MIN_STEM:
                stems.append(ep)
            break

    # 2. Strip ALL matching suffixes (allows "dominus" → both "dom" and "domin")
    for suffix_stem in _strip_all_suffixes(word, LATIN_SUFFIXES):
        stems.append(suffix_stem)
        # Remove epenthetic from suffix-stripped stem
        ep = _remove_latin_epenthetic(suffix_stem)
        if ep and len(ep) >= _MIN_STEM:
            stems.append(ep)
        # Also try stripping prefix from the suffix-stripped stem
        pre_of_suf = _strip_prefix(suffix_stem, LATIN_PREFIXES)
        if pre_of_suf:
            stems.append(pre_of_suf)
            ep2 = _remove_latin_epenthetic(pre_of_suf)
            if ep2 and len(ep2) >= _MIN_STEM:
                stems.append(ep2)

    # 3. Strip prefix from original
    prefix_stem = _strip_prefix(word, LATIN_PREFIXES)
    if prefix_stem:
        stems.append(prefix_stem)
        # Then suffix from that
        suf_of_pre = _strip_suffix(prefix_stem, LATIN_SUFFIXES)
        if suf_of_pre:
            stems.append(suf_of_pre)
            ep3 = _remove_latin_epenthetic(suf_of_pre)
            if ep3 and len(ep3) >= _MIN_STEM:
                stems.append(ep3)

    # Sort longest first (after original)
    stems.sort(key=len, reverse=True)
    return stems


def _decompose_greek(word: str) -> list[str]:
    """Decompose a Greek word (in Latin transliteration)."""
    stems: list[str] = []

    # 1. Check compound elements — split into two meaningful stems
    for compound_suf in GREEK_COMPOUND_SUFFIXES:
        if word.endswith(compound_suf) and len(word) > len(compound_suf) + 1:
            first_part = word[: -len(compound_suf)]
            if len(first_part) >= _MIN_STEM:
                stems.append(first_part)   # e.g., "philo" from "philosophia"
                stems.append(compound_suf) # e.g., "sophia"
            break

    # 2. Strip inflectional suffix
    suffix_stem = _strip_suffix(word, GREEK_SUFFIXES)
    if suffix_stem:
        stems.append(suffix_stem)
        # Strip prefix from that
        pre_of_suf = _strip_prefix(suffix_stem, GREEK_PREFIXES)
        if pre_of_suf:
            stems.append(pre_of_suf)

    # 3. Strip prefix from original
    prefix_stem = _strip_prefix(word, GREEK_PREFIXES)
    if prefix_stem:
        stems.append(prefix_stem)
        suf_of_pre = _strip_suffix(prefix_stem, GREEK_SUFFIXES)
        if suf_of_pre:
            stems.append(suf_of_pre)

    stems.sort(key=len, reverse=True)
    return stems


def _decompose_old_english(word: str) -> list[str]:
    stems: list[str] = []

    # 1. Try compound splitting at consonant cluster boundaries
    compound_parts = _oe_compound_split(word)
    stems.extend(compound_parts)

    # 2. Strip suffix
    suffix_stem = _strip_suffix(word, OE_SUFFIXES)
    if suffix_stem:
        stems.append(suffix_stem)
        pre_of_suf = _strip_prefix(suffix_stem, OE_PREFIXES)
        if pre_of_suf:
            stems.append(pre_of_suf)

    # 3. Strip prefix
    prefix_stem = _strip_prefix(word, OE_PREFIXES)
    if prefix_stem:
        stems.append(prefix_stem)
        suf_of_pre = _strip_suffix(prefix_stem, OE_SUFFIXES)
        if suf_of_pre:
            stems.append(suf_of_pre)

    stems.sort(key=len, reverse=True)
    return stems


def _oe_compound_split(word: str) -> list[str]:
    """Try splitting an OE compound word at consonant cluster boundaries.

    If both halves are >= 3 chars, return both. E.g. "hlafweard" → ["hlaf", "weard"].
    """
    results: list[str] = []
    # Find positions where a vowel-to-consonant boundary occurs (natural split point)
    for i in range(3, len(word) - 2):
        left = word[:i]
        right = word[i:]
        if len(left) >= 3 and len(right) >= 3:
            # Prefer splits where left ends in consonant and right starts with consonant
            # (typical compound boundary in OE)
            if left[-1] not in _VOWELS and right[0] not in _VOWELS:
                results.append(left)
                results.append(right)
                break  # take first plausible split only to avoid explosion
            # Also try vowel-consonant boundary
            elif left[-1] in _VOWELS and right[0] not in _VOWELS and i >= 4:
                results.append(left)
                results.append(right)
                break
    return results


# ---------------------------------------------------------------------------
# Function 2: phonetic_variants
# ---------------------------------------------------------------------------

# Grimm's Law: OE/Germanic consonant → possible pre-shift (Arabic-side) equivalents
GRIMM_MAP: dict[str, list[str]] = {
    "f":  ["b", "f", "p"],
    "th": ["t", "d", "th"],
    "h":  ["k", "kh", "g"],
    "p":  ["b", "p"],
    "t":  ["d", "t"],
    "k":  ["g", "k"],
    "b":  ["bh", "b", "p"],
    "d":  ["dh", "d", "t"],
    "g":  ["gh", "g", "k"],
}

# Latin digraphs and phonetic shifts
LATIN_PHONETIC: dict[str, list[str]] = {
    "qu": ["k", "kw"],
    "x":  ["ks", "k", "s"],
    "ph": ["f", "p"],
    "th": ["t"],
    "ch": ["k", "kh"],
    "c":  ["k", "s"],
    "v":  ["w", "b"],
}

# Greek transliteration shifts
GREEK_PHONETIC: dict[str, list[str]] = {
    "ph": ["f", "p", "b"],
    "th": ["t", "d"],
    "kh": ["k", "g", "kh"],
    "ps": ["s", "ps"],
    "ks": ["k", "ks"],
}

# Epenthetic patterns applied to ALL languages
_EPENTHETIC_PATTERNS: list[tuple[str, str]] = [
    ("mb", "b"),
    ("nd", "d"),
    ("nd", "n"),
    ("ng", "g"),
    ("ng", "n"),
]

# Double-consonant normalization (all languages)
_DOUBLES: list[tuple[str, str]] = [
    ("ll", "l"), ("ss", "s"), ("tt", "t"), ("nn", "n"),
    ("rr", "r"), ("mm", "m"), ("ff", "f"), ("pp", "p"),
    ("bb", "b"), ("dd", "d"), ("gg", "g"), ("cc", "k"),
]

# Universal consonant correspondence — core Juthoor phonetic corridors
# These apply to ALL target languages (the hypothesis is that these shifts
# occurred when Arabic consonants entered IE languages)
UNIVERSAL_CORRESPONDENCES: dict[str, list[str]] = {
    # Bilabial interchange: b ↔ p ↔ f ↔ v
    "b": ["p", "f", "v"],
    "p": ["b", "f", "v"],
    "f": ["b", "p", "v"],
    "v": ["b", "p", "f", "w"],
    # Dental/alveolar interchange: t ↔ d ↔ th
    "t": ["d"],
    "d": ["t"],
    # Velar interchange: k ↔ g ↔ q
    "k": ["g", "q"],
    "g": ["k", "q"],
    "q": ["k", "g"],
    # Sibilant interchange: s ↔ sh ↔ z
    "s": ["z", "sh"],
    "z": ["s"],
    # Guttural deletion: h could be Arabic ح/خ/ع/غ → sometimes deleted
    "h": ["kh", ""],
    # w ↔ v (common in Germanic/Latin)
    "w": ["v", "b"],
}

_MAX_VARIANTS = 25


def phonetic_variants(skeleton: str, lang: str) -> list[str]:
    """Generate consonant skeleton variants based on IE phonetic shift laws.

    Always includes the original skeleton. Limits output to _MAX_VARIANTS
    entries. Substitutions are applied one at a time (not combinatorially).

    Applies three layers:
    1. Universal corridors (bilabial, dental, velar, sibilant interchange)
    2. Epenthetic removal + double-consonant normalization
    3. Language-specific shifts (Grimm for OE, digraphs for Latin/Greek)

    Parameters
    ----------
    skeleton:
        Consonant skeleton string (ASCII, lowercase).
    lang:
        Language code: "lat", "grc", "ang", or other.

    Returns
    -------
    list[str]
        Unique skeleton strings, original first.
    """
    skel = skeleton.lower().strip()
    seen: dict[str, None] = {skel: None}
    result: list[str] = [skel]

    def _add(s: str) -> None:
        if s and s not in seen and len(result) < _MAX_VARIANTS:
            seen[s] = None
            result.append(s)

    # 1. Epenthetic removals (all languages)
    for pattern, replacement in _EPENTHETIC_PATTERNS:
        if pattern in skel:
            _add(skel.replace(pattern, replacement, 1))

    # 2. Double-consonant normalization (all languages)
    for double, single in _DOUBLES:
        if double in skel:
            _add(skel.replace(double, single, 1))

    # 3. Universal consonant correspondences (all languages)
    _apply_map_variants(skel, UNIVERSAL_CORRESPONDENCES, _add)

    # 4. Language-specific shifts (on top of universal)
    if lang == "ang":
        _apply_map_variants(skel, GRIMM_MAP, _add)
    elif lang == "lat":
        _apply_digraph_variants(skel, LATIN_PHONETIC, _add)
    elif lang == "grc":
        _apply_digraph_variants(skel, GREEK_PHONETIC, _add)

    return result


def _apply_map_variants(
    skeleton: str,
    shift_map: dict[str, list[str]],
    add_fn: "callable[[str], None]",
) -> None:
    """Apply single-character substitutions from shift_map."""
    for i, ch in enumerate(skeleton):
        if ch in shift_map:
            for replacement in shift_map[ch]:
                if replacement != ch:
                    variant = skeleton[:i] + replacement + skeleton[i + 1:]
                    add_fn(variant)


def _apply_digraph_variants(
    skeleton: str,
    shift_map: dict[str, list[str]],
    add_fn: "callable[[str], None]",
) -> None:
    """Apply both digraph (2-char) and monograph substitutions from shift_map."""
    # Try digraphs first
    i = 0
    while i < len(skeleton):
        # Try 2-char match
        if i + 1 < len(skeleton):
            digraph = skeleton[i:i + 2]
            if digraph in shift_map:
                for replacement in shift_map[digraph]:
                    if replacement != digraph:
                        variant = skeleton[:i] + replacement + skeleton[i + 2:]
                        add_fn(variant)
        # Try 1-char match
        ch = skeleton[i]
        if ch in shift_map:
            for replacement in shift_map[ch]:
                if replacement != ch:
                    variant = skeleton[:i] + replacement + skeleton[i + 1:]
                    add_fn(variant)
        i += 1


# ---------------------------------------------------------------------------
# Function 3: extract_all_skeletons
# ---------------------------------------------------------------------------

def _extract_skeleton_from_text(text: str, is_ipa: bool = False) -> str:
    """Extract consonant skeleton from a Latin-script word or IPA string."""
    if is_ipa:
        # For IPA: remove vowels, diacritics, suprasegmentals, keep consonant letters
        out = []
        for ch in text.lower():
            if ch in _IPA_VOWELS:
                continue
            if ch in ("\u02c8", "\u02cc", "\u02d0", "\u02d1",  # stress / length
                      "\u0306", "\u032f",  # breve / inverted breve
                      " ", ".", ",", "-", "ː", "ˈ", "ˌ"):
                continue
            if ch.isalpha():
                out.append(ch)
        return "".join(out)
    else:
        # Latin-script: strip vowels, keep consonants
        return "".join(_ENG_CONSONANTS_RE.findall(text.lower()))


def extract_all_skeletons(word: str, ipa: str | None, lang: str) -> list[str]:
    """Main entry point: decompose word, extract skeletons, generate variants.

    Chains:
    1. ``decompose_target(word, lang)`` → list of candidate stems
    2. For each stem, extract consonant skeleton (from Latin script or IPA)
    3. For each skeleton, generate ``phonetic_variants(skeleton, lang)``
    4. Deduplicate and return

    Parameters
    ----------
    word:
        Surface form (lemma) of the target-language word.
    ipa:
        IPA pronunciation string, or None.  When provided the IPA skeleton
        is added as an extra source alongside the orthographic skeleton.
    lang:
        Language code: "lat", "grc", "ang", etc.

    Returns
    -------
    list[str]
        All unique consonant skeletons, most informative first.
    """
    seen: dict[str, None] = {}
    result: list[str] = []

    def _add_skel(s: str) -> None:
        if s and s not in seen:
            seen[s] = None
            result.append(s)

    # Step 1: decompose
    stems = decompose_target(word, lang)

    # Step 2 + 3: extract skeleton + variants for each stem
    for stem in stems:
        # Orthographic skeleton
        orth_skel = _extract_skeleton_from_text(stem, is_ipa=False)
        if orth_skel:
            for var in phonetic_variants(orth_skel, lang):
                _add_skel(var)

    # Also extract from IPA if available (applied to the original word's IPA)
    if ipa:
        ipa_skel = _extract_skeleton_from_text(ipa, is_ipa=True)
        if ipa_skel:
            for var in phonetic_variants(ipa_skel, lang):
                _add_skel(var)

    return result
