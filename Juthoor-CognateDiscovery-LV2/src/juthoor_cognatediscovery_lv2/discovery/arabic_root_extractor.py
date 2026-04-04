"""Arabic morphological root extractor.

Extracts the triliteral (or biliteral-weak) root from Arabic derived forms
that the simple word_root_map lookup misses: masadirs, verbal nouns,
participles, broken plurals, Form IV-X forms, etc.

Public API
----------
    extract_root(word: str) -> tuple[str | None, str]

Returns (root, status) where:
    root   : 3-letter root string (after hamza normalisation), or None
    status : 'extracted' | 'loanword' | 'failed'

Design principles
-----------------
* Conservative: better to return (None, 'failed') than a wrong root.
* Uses the same hamza normalisation as build_arabic_profiles.normalize_arabic():
  أ إ آ  →  ا   (for prefix/suffix detection)
  ء ئ ؤ  are kept as genuine consonants (they ARE root letters).
* Patterns applied longest/most-specific first.
* After all stripping, exactly 3 Arabic consonants  → root.
  4 consonants where one is a known epenthetic ا   → remove it.
  2 consonants + one weak (و/ي) at edge position   → accept as weak root.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Unicode helpers
# ---------------------------------------------------------------------------

# Diacritics (tashkeel) and tatweel
_DIACRITICS_RE = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED\u0640]"
)

# Hamza variants that normalise to bare alef (same as normalize_arabic())
_HAMZA_RE = re.compile(r"[إأآ]")

# Arabic letters that can be root consonants.
# Excludes bare alef (ا) because after normalisation ا is only epenthetic.
# ء (U+0621), ئ (U+0626), ؤ (U+0624) are genuine consonants.
_ARA_CONSONANT = re.compile(
    r"[بتثجحخدذرزسشصضطظعغفقكلمنهوي"
    r"\u0621"  # ء
    r"\u0624"  # ؤ
    r"\u0626"  # ئ
    r"]"
)

# Weak letters (may be epenthetic or root depending on context)
_WEAK = frozenset("وي")

# ---------------------------------------------------------------------------
# Loanword set (non-Arabic origin — return (None, 'loanword'))
# ---------------------------------------------------------------------------

_LOANWORDS: frozenset[str] = frozenset({
    # after normalisation (hamza → ا, no diacritics)
    "انسولين", "بازوكا", "تلفزيون", "راديو", "تلغراف", "اسفنجي",
    "بروتين", "فيتامين", "اكسجين", "هيدروجين", "بنسلين",
    "كاكاو", "شوكولاتة", "بطاطس", "طماطم", "موزاييك",
    "تلفون", "تليفون", "تلفزيون", "ميكروفون", "انترنت",
    "كمبيوتر", "تابلت", "سينما", "بيانو", "غيتار",
})

# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def _normalise(word: str) -> str:
    """Strip diacritics, tatweel, punctuation; normalise hamza; strip whitespace."""
    word = _DIACRITICS_RE.sub("", word)
    word = word.replace("\u0640", "")          # tatweel
    word = _HAMZA_RE.sub("ا", word)            # أ إ آ → ا
    word = word.strip("،,.؟!؛ \t\n\r")
    return word


def _strip_al(word: str) -> str:
    """Strip leading ال (definite article)."""
    if word.startswith("ال"):
        return word[2:]
    return word


# ---------------------------------------------------------------------------
# Consonant counting
# ---------------------------------------------------------------------------

def _consonants(stem: str) -> list[str]:
    """Return list of root consonants in the stem (excludes bare ا)."""
    return _ARA_CONSONANT.findall(stem)


def _to_root(consonants: list[str]) -> str | None:
    """Convert a consonant list to a root string if valid (3 letters).

    Also handles:
    - 4 consonants where one is ا in an epenthetic position (Form IV/VII/VIII)
    - 2 consonants + 1 weak letter at edge = weak/hollow/defective root
    """
    n = len(consonants)
    if n == 3:
        return "".join(consonants)
    if n == 4:
        # Epenthetic ا from Form IV/VII/VIII often left as bare alef in stem.
        # We don't include ا in _consonants, so n==4 means 4 real consonants.
        # A quadriliteral root is possible but uncommon; skip.
        return None
    if n == 2:
        # Geminate root (same letter repeated) or defective root
        # Too ambiguous without more context — reject
        return None
    return None


# ---------------------------------------------------------------------------
# Pattern-based stripping rules
# ---------------------------------------------------------------------------
# Each rule is a function:  stem -> list[str] | None
# Returns list of candidate consonant strings (not roots — the caller counts).
# Return None if the pattern does not match.
# Rules are tried in order; first success wins.

def _try_form_x_masdar(w: str) -> list[str] | None:
    """Form X masdar: استفعال — strip است prefix + ال suffix."""
    if not w.startswith("است"):
        return None
    stem = w[3:]  # remove است
    if stem.endswith("ال") and len(stem) > 2:
        stem = stem[:-2]
    elif stem.endswith("ة") and len(stem) > 1:
        stem = stem[:-1]
    return _consonants(stem) or None


def _try_form_x_participle(w: str) -> list[str] | None:
    """Form X participle: مستفعل — strip مست prefix."""
    if not w.startswith("مست"):
        return None
    stem = w[3:]
    # strip feminine/plural suffixes
    for suf in ("ين", "ات", "ون", "ة", "ي"):
        if stem.endswith(suf) and len(stem) > len(suf):
            stem = stem[: -len(suf)]
            break
    return _consonants(stem) or None


def _try_form_viii_masdar(w: str) -> list[str] | None:
    """Form VIII masdar: افتعال — strip ا prefix, infix ت, ال suffix.

    Pattern: ا + C1 + ت + C2C3 + ال
    Example: اقتصاد → ق ص د  (اقتصاد without ا,ت,ال)
    """
    if not w.startswith("ا") or len(w) < 5:
        return None
    # must have a ت somewhere in the middle (not at position 1 right after ا)
    body = w[1:]  # strip leading ا
    t_pos = body.find("ت")
    if t_pos < 1:  # ت must be after at least one consonant
        return None
    # strip ت infix
    candidate = body[:t_pos] + body[t_pos + 1:]
    # strip ال suffix
    if candidate.endswith("ال") and len(candidate) > 2:
        candidate = candidate[:-2]
    elif candidate.endswith("ة") and len(candidate) > 1:
        candidate = candidate[:-1]
    cons = _consonants(candidate)
    if len(cons) == 3:
        return cons
    return None


def _try_form_viii_verb(w: str) -> list[str] | None:
    """Form VIII verb: افتعل — strip ا prefix and infix ت.

    Example: اكتسب → ك س ب
    """
    if not w.startswith("ا") or len(w) < 5:
        return None
    body = w[1:]
    t_pos = body.find("ت")
    if t_pos < 1:
        return None
    candidate = body[:t_pos] + body[t_pos + 1:]
    # strip verb suffixes
    for suf in ("وا", "ون", "ين", "ان", "ات", "ة", "ت"):
        if candidate.endswith(suf) and len(candidate) > len(suf):
            candidate = candidate[: -len(suf)]
            break
    cons = _consonants(candidate)
    if len(cons) == 3:
        return cons
    return None


def _try_form_vii_masdar(w: str) -> list[str] | None:
    """Form VII masdar: انفعال — strip ان prefix + ال suffix.

    Example: انكسار → ك س ر
    """
    if not w.startswith("ان") or len(w) < 5:
        return None
    stem = w[2:]
    if stem.endswith("ال") and len(stem) > 2:
        stem = stem[:-2]
    elif stem.endswith("ة") and len(stem) > 1:
        stem = stem[:-1]
    cons = _consonants(stem)
    if len(cons) == 3:
        return cons
    return None


def _try_form_vii_verb(w: str) -> list[str] | None:
    """Form VII verb: انفعل — strip ان prefix.

    Example: انكسر → ك س ر
    """
    if not w.startswith("ان") or len(w) < 5:
        return None
    stem = w[2:]
    for suf in ("وا", "ون", "ين", "ان", "ات", "ة", "ت"):
        if stem.endswith(suf) and len(stem) > len(suf):
            stem = stem[: -len(suf)]
            break
    cons = _consonants(stem)
    if len(cons) == 3:
        return cons
    return None


def _try_form_iv_masdar(w: str) -> list[str] | None:
    """Form IV masdar: إفعال — strip ا prefix + ال suffix.

    Example: إرسال → ر س ل
             إقصاء → ق ص (weak) → accept as defective root
    """
    if not w.startswith("ا") or len(w) < 4:
        return None
    stem = w[1:]
    # strip ال suffix
    if stem.endswith("ال") and len(stem) > 2:
        stem = stem[:-2]
    # strip اء suffix (Form IV masdar of defective verbs: إيماء, إقصاء)
    elif stem.endswith("اء") and len(stem) > 2:
        stem = stem[:-2]
    # strip ة suffix
    elif stem.endswith("ة") and len(stem) > 1:
        stem = stem[:-1]
    cons = _consonants(stem)
    if len(cons) == 3:
        return cons
    # Accept 2 consonants + initial weak letter (defective root e.g. قصو)
    # In this pattern ا prefix was stripped, stem might be just 2 consonants
    # if the root is defective (third root letter = و/ي was part of the suffix)
    if len(cons) == 2 and len(stem) >= 2:
        # The third root letter may have been absorbed into the اء/ال suffix
        # Try appending و (most common defective ending)
        return cons  # return as-is; caller will try weak extension
    return None


def _try_form_iv_verb(w: str) -> list[str] | None:
    """Form IV verb: أفعل — strip ا prefix.

    Example: أرسل → ر س ل   أجير → drop ا, strip ي suffix → ج ر? No.
    Note: أجير is actually Form I with Form IV look — أجير = اجير (hired man).
    Conservative: only accept if exactly 3 consonants remain.
    """
    if not w.startswith("ا") or len(w) < 4:
        return None
    stem = w[1:]
    for suf in ("وا", "ون", "ين", "ان", "ات", "ة", "ت"):
        if stem.endswith(suf) and len(stem) > len(suf):
            stem = stem[: -len(suf)]
            break
    cons = _consonants(stem)
    if len(cons) == 3:
        return cons
    return None


def _try_form_iii_masdar(w: str) -> list[str] | None:
    """Form III masdar: مفاعلة — strip م prefix, ا infix, ة suffix.

    Example: مراسلة → ر س ل
             مفاوضة → ف و ض  (و is root letter here)
    """
    if not w.startswith("م") or len(w) < 5:
        return None
    stem = w[1:]  # strip م
    if stem.endswith("ة") and len(stem) > 1:
        stem = stem[:-1]
    elif stem.endswith("ات") and len(stem) > 2:
        stem = stem[:-2]
    # remove the internal ا (alef after first radical in Form III)
    # It appears at position 1 of the stem (after the first consonant)
    if len(stem) >= 3 and stem[1] == "ا":
        stem = stem[0] + stem[2:]
    cons = _consonants(stem)
    if len(cons) == 3:
        return cons
    return None


def _try_form_iii_noun(w: str) -> list[str] | None:
    """Form III active participle: مفاعل — strip م prefix and ا infix.

    Example: مساعد → س ع د
    """
    if not w.startswith("م") or len(w) < 4:
        return None
    stem = w[1:]
    # strip suffixes
    for suf in ("ين", "ون", "ات", "ة", "ي"):
        if stem.endswith(suf) and len(stem) > len(suf):
            stem = stem[: -len(suf)]
            break
    # remove internal ا
    if len(stem) >= 3 and stem[1] == "ا":
        stem = stem[0] + stem[2:]
    cons = _consonants(stem)
    if len(cons) == 3:
        return cons
    return None


def _try_form_v_masdar(w: str) -> list[str] | None:
    """Form V masdar: تفعّل — strip ت prefix + ة suffix.

    Example: تكريم → (also Form II masdar: تفعيل) → ك ر م
             تكرمة → ك ر م
    """
    if not w.startswith("ت") or len(w) < 4:
        return None
    stem = w[1:]
    for suf in ("يل", "ية", "يات", "ات", "ون", "ين", "ة", "ي"):
        if stem.endswith(suf) and len(stem) > len(suf):
            stem = stem[: -len(suf)]
            break
    # Remove internal ا (Form II masdar: تفعيل → تفعل after يل strip)
    # Remove internal و or ي that is epenthetic
    cons = _consonants(stem)
    if len(cons) == 3:
        return cons
    if len(cons) == 4:
        # Remove one weak letter if present
        non_weak = [c for c in cons if c not in _WEAK]
        if len(non_weak) == 3:
            return non_weak
    return None


def _try_form_vi_masdar(w: str) -> list[str] | None:
    """Form VI masdar: تفاعل — strip ت prefix + ا infix.

    Example: تبادل → ب د ل
    """
    if not w.startswith("ت") or len(w) < 5:
        return None
    stem = w[1:]
    for suf in ("ون", "ين", "ات", "ة", "ي"):
        if stem.endswith(suf) and len(stem) > len(suf):
            stem = stem[: -len(suf)]
            break
    # remove the ا after first consonant (Form VI marker)
    if len(stem) >= 3 and stem[1] == "ا":
        stem = stem[0] + stem[2:]
    cons = _consonants(stem)
    if len(cons) == 3:
        return cons
    return None


def _try_verbal_noun_aa(w: str) -> list[str] | None:
    """Verbal nouns ending in اء (masdar of defective Form IV verbs).

    Example: إقصاء (normalised: اقصاء) → strip leading ا + trailing اء → ق ص
             Then third root letter و/ي assumed defective.
    Also: إيماء → strip ا prefix + اء suffix → يم → then accept ومي or similar.
    This is the most ambiguous pattern — very conservative.
    """
    if not w.endswith("اء") or len(w) < 4:
        return None
    stem = w[:-2]  # strip اء
    if stem.startswith("ا"):
        stem = stem[1:]
    cons = _consonants(stem)
    # Need at least 2 consonants for a weak root
    if len(cons) >= 2:
        return cons
    return None


def _try_form_ii_masdar_taf3il(w: str) -> list[str] | None:
    """Form II masdar: تفعيل — strip ت prefix + يل suffix.

    Example: تكريم → strip nothing (كريم) … handled below.
             This pattern: تفعيل exact, e.g. تعليم → ع ل م
    """
    if not w.startswith("ت") or not w.endswith("يل") or len(w) < 5:
        return None
    stem = w[1:-2]  # strip ت prefix + يل suffix
    cons = _consonants(stem)
    if len(cons) == 3:
        return cons
    return None


def _try_masdar_form_ii(w: str) -> list[str] | None:
    """Form II masdar ending -يم / -ير / -يل / -يف (CaCCīC pattern).

    Example: تكريم → ك ر م   (the ت is a prefix in the word التكريم)
             We handle this after ال is stripped: كريم → try stripping ي infix.
    Heuristic: word is 4+ letters, contains ي as 3rd letter from end.
    """
    if len(w) < 4:
        return None
    # Pattern: C1C2يC3 (e.g., كريم, رحيم, عظيم)
    # The ي is epenthetic (not a root letter in Form II masdar)
    if len(w) >= 4:
        # Check for CيC pattern (ي at second-to-last position)
        yi_pos = None
        for i in range(len(w) - 1):
            if w[i] == "ي":
                yi_pos = i
                break
        if yi_pos is not None and yi_pos >= 1:
            candidate = w[:yi_pos] + w[yi_pos + 1:]
            cons = _consonants(candidate)
            if len(cons) == 3:
                return cons
    return None


def _try_participle_m_prefix(w: str) -> list[str] | None:
    """Active/passive participle: مفعول, مفعِل, مفعَل — strip م prefix.

    Example: مكتوب → ك ت ب   (strip م + و)
             مكرم  → ك ر م   (strip م)
             مدرسة → د ر س   (strip م + ة)
    """
    if not w.startswith("م") or len(w) < 3:
        return None
    stem = w[1:]
    for suf in ("كم", "هم", "هن", "نا", "ها", "وية", "ية", "ون", "ين", "ات", "ة", "ي"):
        if stem.endswith(suf) and len(stem) > len(suf):
            stem = stem[: -len(suf)]
            break
    cons = _consonants(stem)
    if len(cons) == 3:
        return cons
    if len(cons) == 4:
        # maf3uul: مفعول — the و is epenthetic
        non_weak = [c for c in cons if c not in _WEAK]
        if len(non_weak) == 3:
            return non_weak
    return None


def _try_suffix_strip_only(w: str) -> list[str] | None:
    """Last resort: strip common suffixes/possessives, check for 3 consonants.

    Handles: أصلابكم → أصلاب → ص ل ب  (strip possessive كم + leading ا)
    """
    stem = w
    # Possessive suffixes (longest first)
    for suf in ("كم", "هم", "هن", "نا", "ها", "كن", "تم", "تن",
                "وية", "ية", "اء", "ان", "ين", "ون", "ات", "ة", "ت", "ي", "ك", "ه"):
        if stem.endswith(suf) and len(stem) > len(suf) + 1:
            stem = stem[: -len(suf)]
            break
    # Strip leading ا (epenthetic alef in some nominal forms)
    if stem.startswith("ا") and len(stem) > 1:
        stem = stem[1:]
    cons = _consonants(stem)
    if len(cons) == 3:
        return cons
    if len(cons) == 4:
        non_weak = [c for c in cons if c not in _WEAK]
        if len(non_weak) == 3:
            return non_weak
    return None


# ---------------------------------------------------------------------------
# Ordered pattern list
# ---------------------------------------------------------------------------

_PATTERNS = [
    _try_form_x_masdar,       # است + ال  (most specific)
    _try_form_x_participle,    # مست
    _try_form_viii_masdar,     # ا + ت-infix + ال
    _try_form_viii_verb,       # ا + ت-infix
    _try_form_vii_masdar,      # ان + ال
    _try_form_vii_verb,        # ان
    _try_form_iv_masdar,       # ا + ال  (or اء suffix)
    _try_form_iv_verb,         # ا (bare)
    _try_form_iii_masdar,      # م + ا-infix + ة
    _try_form_iii_noun,        # م + ا-infix (no ة)
    _try_form_vi_masdar,       # ت + ا-infix
    _try_form_v_masdar,        # ت + يل/ية/ة
    _try_form_ii_masdar_taf3il,  # ت + يل
    _try_masdar_form_ii,       # C1C2يC3 pattern
    _try_verbal_noun_aa,       # اء suffix
    _try_participle_m_prefix,  # م prefix
    _try_suffix_strip_only,    # fallback: suffix strip only
]


# ---------------------------------------------------------------------------
# Weak root resolution
# ---------------------------------------------------------------------------

def _resolve_weak(cons: list[str], original: str) -> str | None:
    """Attempt to reconstruct a weak root from 2 consonants.

    When a pattern extracts only 2 consonants, the third may be:
    - Initial و (e.g., وصل → وصل): check if original had initial weak
    - Final و or ي (defective root): append و as guess
    - Hollow root (middle weak): less common in masdar forms

    Very conservative — only return when evidence is strong.
    """
    if len(cons) != 2:
        return None
    # If original word (before normalisation) starts with و or ي, add as first
    # This is not available here — use conservative approach only.
    # If 2 consonants and we stripped an اء suffix → defective, 3rd = و
    # If 2 consonants and we stripped an ال after ا prefix → could be hollow
    # Too ambiguous — do not guess
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_root(word: str) -> tuple[str | None, str]:
    """Extract triliteral root from an Arabic derived form.

    Parameters
    ----------
    word:
        Arabic word in any form (with or without diacritics, with or without
        definite article, with possessive suffixes, etc.)

    Returns
    -------
    (root, status):
        root   - 3-letter root string (hamza-normalised) or None
        status - 'extracted' | 'loanword' | 'failed'
    """
    if not word or not word.strip():
        return None, "failed"

    # 1. Normalise
    w = _normalise(word)
    if not w:
        return None, "failed"

    # 2. Strip definite article
    w = _strip_al(w)
    if not w:
        return None, "failed"

    # 3. Loanword check (after normalisation)
    if w in _LOANWORDS:
        return None, "loanword"

    # 4. Fast path: if the word (after stripping ال) is already 3 consonants
    bare_cons = _consonants(w)
    if len(bare_cons) == 3:
        return "".join(bare_cons), "extracted"

    # 5. Try each morphological pattern
    for pattern_fn in _PATTERNS:
        cons = pattern_fn(w)
        if cons is None:
            continue
        if len(cons) == 3:
            return "".join(cons), "extracted"
        # 2 consonants: try weak-root resolution
        if len(cons) == 2:
            resolved = _resolve_weak(cons, w)
            if resolved:
                return resolved, "extracted"
        # For other lengths: continue trying next pattern

    # 6. Loanword heuristic: very long word with no root resolution
    if len(w) > 9:
        return None, "loanword"

    return None, "failed"
