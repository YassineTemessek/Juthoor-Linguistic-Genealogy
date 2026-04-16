"""Phonetic law scoring for cross-family (Arabic<->English/European) cognate candidates.

Uses LV1 sound laws (Khashim, Latin equivalents) to project Arabic roots
into expected English consonant patterns and scores the match.

V2 additions:
- Morpheme-aware scoring: strip known prefixes/suffixes, score the stem
- Improved metathesis: try pairwise adjacent-consonant swaps (partial metathesis)

V3 additions:
- IPA-based consonant skeleton (more accurate than orthographic for English)
- Frequency penalty for high-frequency function words

V4 additions:
- Position-weighted scoring: LV1 H8 proved position 1 is the semantic anchor.
  Matches at position 1 of the Arabic root count 1.5x, position 3 counts 0.7x.

V5 additions:
- Synonym family expansion: if the primary Arabic root does not match well,
  try related roots from LV1 synonym families (lazy-loaded, capped at 3 synonyms).

V6 additions:
- Target-aware projection: switch from project_root_sound_laws(..., max_variants=256)
  to project_root_by_target(root, "european") which uses 128 variants with proper
  phonetic succession group expansion tuned for European target languages.
- _ARABIC_IPA_TO_ENGLISH_IPA mapping: applied in _best_projection_match_ipa to remap
  Arabic IPA consonants (ق ع ح خ غ etc.) to their expected English realisations before
  comparison, improving accuracy when IPA data is available.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import Any

# Try importing LV1 sound laws; fall back to inline copies if unavailable
try:
    from juthoor_arabicgenome_lv1.factory.sound_laws import (
        LATIN_EQUIVALENTS,
        normalize_arabic_root,
        project_root_sound_laws,
        project_root_by_target,
    )
    _HAS_TARGET_PROJECTION = True
except ImportError:
    # Minimal fallback — define inline
    _HAMZA_NORM = str.maketrans(
        {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ؤ": "و", "ئ": "ي", "ى": "ي", "ة": "ه"}
    )
    _AR_CONS_RE = re.compile(r"[\u0621-\u064A]")

    def normalize_arabic_root(root: str) -> str:  # type: ignore[misc]
        return "".join(_AR_CONS_RE.findall(root.translate(_HAMZA_NORM)))

    LATIN_EQUIVALENTS: dict[str, tuple[str, ...]] = {  # type: ignore[misc]
        "ا": ("a", ""),
        "ب": ("b", "p"),
        "ت": ("t",),
        "ث": ("th", "s"),
        "ج": ("j", "g", "c"),
        "ح": ("h",),
        "خ": ("kh", "h", "g"),
        "د": ("d", "t"),
        "ذ": ("dh", "z", "d"),
        "ر": ("r",),
        "ز": ("z", "s"),
        "س": ("s",),
        "ش": ("sh", "s"),
        "ص": ("s",),
        "ض": ("d",),
        "ط": ("t",),
        "ظ": ("z",),
        "ع": ("", "h"),
        "غ": ("gh", "g"),
        "ف": ("f", "p"),
        "ق": ("q", "k", "c", "g"),
        "ك": ("k", "c"),
        "ل": ("l",),
        "م": ("m",),
        "ن": ("n",),
        "ه": ("h",),
        "و": ("w", "v", "u"),
        "ي": ("y", "i"),
    }

    def project_root_sound_laws(  # type: ignore[misc]
        root: str,
        *,
        include_group_expansion: bool = False,
        max_variants: int = 128,
    ) -> tuple[str, ...]:
        import itertools

        normalized = normalize_arabic_root(root)
        if not normalized:
            return ()
        options = [LATIN_EQUIVALENTS.get(ch, (ch,)) for ch in normalized]
        variants: list[str] = []
        for combo in itertools.product(*options):
            v = "".join(combo)
            if v and v not in variants:
                variants.append(v)
            if len(variants) >= max_variants:
                break
        return tuple(variants)

    def project_root_by_target(root: str, target_family: str) -> tuple[str, ...]:  # type: ignore[misc]
        return project_root_sound_laws(root, include_group_expansion=True, max_variants=128)

    _HAS_TARGET_PROJECTION = False


# ---------------------------------------------------------------------------
# Greek equivalents: Arabic consonants → romanized Ancient Greek
# ---------------------------------------------------------------------------
# Greek target morphology transliterates: φ→ph, θ→th, χ→kh, β→b, γ→g, δ→d
# Key differences from LATIN_EQUIVALENTS:
#   ف→ph (aspiration), ث→th (preserved), ع→∅/g (ghayin variant),
#   ح→kh/∅ (no pharyngeal), emphatics→aspirated (ق→kh, ط→th),
#   devoicing (ج→k, ض→t, ب→ph), ζ was /zd/ (ز→d component)
# Sources: phonetic_mergers_greek.jsonl, PHONETIC_MERGERS.md,
#   Brill Semitic Loanwords in Greek, Phoenician alphabet scholarship,
#   Grassmann's law, Semitic devoicing patterns in Greek loans
GREEK_EQUIVALENTS: dict[str, tuple[str, ...]] = {
    "ا": ("", "a"),           # alif → silent or vowel
    "ب": ("b", "p", "ph"),    # ba → β / π / φ (devoicing + aspiration chain)
    "ت": ("t", "d"),          # ta → τ (tau) / δ (delta)
    "ث": ("th",),             # tha → θ (theta) — preserved in Greek
    "ج": ("g", "k"),          # jim → γ (gamma) / κ (devoicing: gamal→kamelos)
    "ح": ("kh", "", "h"),     # ḥa → χ (chi) / deleted / rough breathing
    "خ": ("kh",),             # kha → χ (chi)
    "د": ("d", "t"),          # dal → δ (delta) / τ (tau)
    "ذ": ("d", "th", "z"),    # dhal → δ / θ (theta) / ζ (zeta)
    "ر": ("r",),              # ra → ρ (rho)
    "ز": ("z", "s", "d"),     # zayn → ζ (zeta=/zd/) / σ / δ (zd-cluster)
    "س": ("s",),              # sin → σ (sigma)
    "ش": ("s", "kh"),         # shin → σ (sigma) / χ (chi)
    "ص": ("s", "z"),          # ṣad → σ / ζ (tsade affricate, voiced variant)
    "ض": ("d", "t"),          # ḍad → δ / τ (systematic devoicing)
    "ط": ("t", "th"),         # ṭa → τ (tau) / θ (theta) — emphatic→aspirated
    "ظ": ("z", "d", "th"),    # ẓa → ζ / δ / θ — emphatic interdental
    "ع": ("", "g"),           # ʿayn → DELETED / γ (ghayin: Gaza, Gomorrah)
    "غ": ("g",),              # ghayn → γ (gamma)
    "ف": ("ph", "p", "b"),    # fa → φ (phi=aspirated p) / π / β
    "ق": ("k", "kh"),         # qaf → κ / χ (emphatic→aspirated pattern)
    "ك": ("k", "kh"),         # kaf → κ / χ (kaph without dagesh = chi)
    "ل": ("l",),              # lam → λ (lambda)
    "م": ("m",),              # mim → μ (mu)
    "ن": ("n",),              # nun → ν (nu)
    "ه": ("h", ""),           # ha → rough breathing or deleted
    "و": ("w", "u", ""),      # waw → w / υ / deleted (post-digamma loss)
    "ي": ("y", "i"),          # ya → ι (iota)
}


# ---------------------------------------------------------------------------
# Old English equivalents: Arabic consonants → Old English consonants
# ---------------------------------------------------------------------------
# Key differences from LATIN_EQUIVALENTS:
#   ث → þ/th (thorn, /θ/) — OE preserved the dental fricative
#   ذ → ð/th  (eth, /ð/)  — OE preserved the voiced dental fricative
#   ف → f     (OE had no /v/ phoneme word-initially; /f/ covered both)
#   و → w     (OE retained w- robustly; modern English sometimes lost it)
#   ج → g/c   (OE /g/ covered both stops and fricatives; c = /k/)
#   ق → c/k   (OE used c for /k/ before back vowels)
#   ك → c/k   (same: OE c = /k/)
#   ع → ∅/h   (pharyngeal deleted, sometimes breathy-h in early OE)
#   ح → h     (OE had robust /h/, maps pharyngeal ح cleanly)
#   خ → h/k   (OE h- before consonant was the velar fricative /x/)
#   غ → g/∅   (ghayin → OE g or deleted)
#   ش → sc/s  (OE sc = /ʃ/, so Arabic ش maps to OE sc or s)
#   ص/ض/ط/ظ → emphatic flattening same as Latin (no OE emphatics)
#   hw → Arabic ح+و compound (OE hw- in "hwæt", "hwil" etc.)
# Sources: OE phonology (Campbell 1959), Grimm's Law for stop series,
#   Juthoor phonetic_mergers_eng.jsonl, feedback_phonetic_merger.md
OLD_ENGLISH_EQUIVALENTS: dict[str, tuple[str, ...]] = {
    "ا": ("", "a"),             # alif → silent or vowel carrier
    "ب": ("b", "p"),            # ba → b (Grimm: PIE *bh → OE b)
    "ت": ("t", "d"),            # ta → t / d (Grimm voicing in medial)
    "ث": ("þ", "th", "t", "s"), # tha → þ (thorn /θ/) / th / t / s
    "ج": ("g", "c", "j"),       # jim → g / c (/k/) / j (after Norman influence crept in)
    "ح": ("h",),                # ḥa → h (OE strong /h/)
    "خ": ("h", "k", "c"),       # kha → h (/x/ in OE) / k / c
    "د": ("d", "t"),            # dal → d / t (Grimm)
    "ذ": ("ð", "th", "d", "z"), # dhal → ð (eth /ð/) / th / d / z
    "ر": ("r",),                # ra → r
    "ز": ("z", "s"),            # zayn → z / s
    "س": ("s",),                # sin → s
    "ش": ("sc", "s", "sh"),     # shin → OE sc (/ʃ/) / s / sh
    "ص": ("s",),                # ṣad → s (emphatic flattened)
    "ض": ("d",),                # ḍad → d
    "ط": ("t",),                # ṭa → t
    "ظ": ("z", "d"),            # ẓa → z / d
    "ع": ("", "h"),             # ʿayn → deleted / h (breathy onset)
    "غ": ("g", ""),             # ghayn → g / deleted
    "ف": ("f",),                # fa → f (OE f covers /f/ and /v/ allophonically)
    "ق": ("c", "k", "cw"),      # qaf → c (/k/) / k / cw (OE qu = cw)
    "ك": ("c", "k"),            # kaf → c / k
    "ل": ("l",),                # lam → l
    "م": ("m",),                # mim → m
    "ن": ("n",),                # nun → n
    "ه": ("h", ""),             # ha → h / deleted
    "و": ("w", "v"),            # waw → w (OE retained w strongly) / v
    "ي": ("g", "y", "i"),       # ya → OE g (palatal /j/) / y / i
}


def get_language_equivalents(lang: str) -> dict[str, tuple[str, ...]]:
    """Return the Arabic→target consonant equivalents table for the given language."""
    if lang == "grc":
        return GREEK_EQUIVALENTS
    if lang == "ang":
        return OLD_ENGLISH_EQUIVALENTS
    return LATIN_EQUIVALENTS


_DIACRITICAL_MAP = str.maketrans(
    {"ṭ": "t", "ṣ": "s", "ḥ": "h", "ḍ": "d", "ẓ": "z", "ʕ": "", "ġ": "g", "ḫ": "kh"}
)
_ENG_CONSONANTS_RE = re.compile(r"[bcdfghjklmnpqrstvwxyz]")
_ARABIC_WEAK = set("اويى")

# ---------------------------------------------------------------------------
# Position weights (LV1 H8 — positional semantics)
# Default fallback if LV1 positional profile data is unavailable.
# ---------------------------------------------------------------------------
_POSITION_WEIGHTS: dict[int, float] = {0: 1.5, 1: 1.0, 2: 0.7}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _consonant_correspondence_matrix_path() -> Path:
    return (
        _repo_root()
        / "Juthoor-CognateDiscovery-LV2"
        / "data"
        / "processed"
        / "consonant_correspondence_matrix.json"
    )


def _fallback_correspondence_weights() -> dict[str, dict[str, float]]:
    fallback: dict[str, dict[str, float]] = {}
    for letter, equivalents in LATIN_EQUIVALENTS.items():
        normalized = [eq.translate(_DIACRITICAL_MAP) for eq in equivalents if eq.translate(_DIACRITICAL_MAP)]
        if normalized:
            fallback[letter] = {eq: 1.0 for eq in normalized}
    return fallback


def _load_correspondence_weights() -> dict[str, dict[str, float]]:
    matrix_path = _consonant_correspondence_matrix_path()
    fallback = _fallback_correspondence_weights()
    if not matrix_path.exists():
        return fallback

    with matrix_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    arabic_to_english = payload.get("arabic_to_english", {})
    weights: dict[str, dict[str, float]] = {}
    for letter, counts in arabic_to_english.items():
        total = counts.get("total", 0)
        if not isinstance(total, int) or total <= 0:
            continue
        letter_weights = {
            latin: round(count / total, 2)
            for latin, count in counts.items()
            if latin not in {"total", "primary"} and isinstance(count, int) and count > 0
        }
        if letter_weights:
            weights[str(letter)] = letter_weights

    for letter, letter_weights in fallback.items():
        weights.setdefault(letter, letter_weights)
    return weights


CORRESPONDENCE_WEIGHTS: dict[str, dict[str, float]] = _load_correspondence_weights()


def _positional_profiles_candidates() -> tuple[Path, ...]:
    repo_root = _repo_root()
    return (
        repo_root
        / "Juthoor-ArabicGenome-LV1"
        / "outputs"
        / "research_factory"
        / "promoted"
        / "promoted_features"
        / "positional_profiles.jsonl",
        repo_root
        / "outputs"
        / "research_factory"
        / "promoted"
        / "promoted_features"
        / "positional_profiles.jsonl",
    )


@lru_cache(maxsize=1)
def _load_position_weight_profiles() -> dict[str, dict[int, float]]:
    profile_path = next((path for path in _positional_profiles_candidates() if path.exists()), None)
    if profile_path is None:
        return {}

    rows: list[tuple[str, int, float]] = []
    with profile_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            payload = json.loads(line)
            letter = str(payload.get("letter", ""))
            positions = payload.get("positions", {})
            for pos_key in ("1", "2", "3"):
                coherence = positions.get(pos_key, {}).get("coherence")
                if letter and isinstance(coherence, (int, float)):
                    rows.append((letter, int(pos_key) - 1, float(coherence)))

    if not rows:
        return {}

    mean_coherence = sum(coherence for _, _, coherence in rows) / len(rows)
    if mean_coherence <= 0:
        return {}

    weights: dict[str, dict[int, float]] = {}
    for letter, position, coherence in rows:
        weights.setdefault(letter, {})[position] = coherence / mean_coherence
    return weights


def _position_weight_for(letter: str, position: int) -> float:
    profile_weights = _load_position_weight_profiles()
    if letter:
        letter_weights = profile_weights.get(letter)
        if letter_weights is not None and position in letter_weights:
            return letter_weights[position]
    default_w = _POSITION_WEIGHTS.get(2, 0.7)
    return _POSITION_WEIGHTS.get(position, default_w)

# ---------------------------------------------------------------------------
# Arabic IPA to English IPA consonant mapping (V6)
# Used in _best_projection_match_ipa when IPA data is available for more
# accurate projection comparison.  Keys are Arabic IPA consonants; values are
# their expected English IPA realisations (ordered most-likely first).
# ---------------------------------------------------------------------------
_ARABIC_IPA_TO_ENGLISH_IPA: dict[str, list[str]] = {
    "q": ["k", "g"],          # ق → k/g
    "ʕ": ["", "h"],           # ع → deletion or h
    "ħ": ["h", ""],           # ح → h or deletion
    "χ": ["h", "k", "x"],     # خ → h/k/x
    "ɣ": ["g", ""],           # غ → g or deletion
    "sˤ": ["s"],              # ص → s
    "tˤ": ["t"],              # ط → t
    "dˤ": ["d"],              # ض → d
    "ðˤ": ["z", "d"],         # ظ → z/d
    "θ": ["θ", "t", "s"],     # ث → th/t/s
    "ð": ["ð", "d", "z"],     # ذ → th/d/z
    "dʒ": ["dʒ", "g", "ʒ"],  # ج → j/g/zh
    "ʃ": ["ʃ", "s"],          # ش → sh/s
}

# ---------------------------------------------------------------------------
# High-frequency English words — too common to be meaningful cognate evidence.
# These words match by coincidence and inflate false-positive rates.
# ---------------------------------------------------------------------------
_HIGH_FREQ_WORDS: frozenset[str] = frozenset({
    # Top-200 most frequent English words (function words + very common content words)
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
    "people", "into", "year", "your", "good", "some", "could", "them", "see",
    "other", "than", "then", "now", "look", "only", "come", "its", "over",
    "think", "also", "back", "after", "use", "two", "how", "our", "work",
    "first", "well", "way", "even", "new", "want", "because", "any", "these",
    "give", "day", "most", "us", "great", "between", "need", "large", "often",
    "hand", "high", "place", "hold", "turn", "been", "every", "find", "here",
    "thing", "tell", "much", "before", "own", "had", "very", "were", "more",
    "was", "has", "are", "am", "is", "did", "does", "done", "got", "gets",
    "may", "might", "must", "shall", "should", "let", "set", "put", "go",
    "too", "very", "still", "while", "down", "long", "same", "old", "little",
    "few", "both", "those", "through", "where", "again", "right", "big",
    "different", "next", "hard", "real", "life", "few", "north", "open",
    "seem", "together", "next", "white", "children", "begin", "got", "walk",
    "example", "ease", "paper", "often", "always", "music", "those", "both",
})

# Known English prefixes and suffixes that can hide the Arabic root
_KNOWN_PREFIXES: tuple[str, ...] = (
    "auto", "anti", "semi", "hyper", "super", "inter", "trans", "over",
    "out", "mis", "fore", "sub", "pre", "pro", "dis", "con", "com",
    "geo", "re", "de", "in", "im", "un", "ex", "es",
)
_KNOWN_SUFFIXES: tuple[str, ...] = (
    "ology", "logy", "tion", "sion", "ment", "ness", "ship", "hood",
    "ward", "ance", "ence", "ary", "ory", "ity", "ism", "ist", "ize",
    "ise", "ify", "ous", "ive", "ful", "age", "ure", "dom", "ify",
    "gen", "less", "al", "er", "or",
)


def _strip_diacriticals(text: str) -> str:
    return text.translate(_DIACRITICAL_MAP)


def _english_consonant_skeleton(word: str) -> str:
    return "".join(_ENG_CONSONANTS_RE.findall(word.lower()))


def _arabic_consonant_skeleton(text: str) -> str:
    norm = normalize_arabic_root(text)
    return "".join(ch for ch in norm if ch not in _ARABIC_WEAK)


def _morpheme_decompose(word: str) -> tuple[str, str, str]:
    """Decompose an English word into (prefix, stem, suffix).

    Prefixes are checked before suffixes; longer matches take priority.
    Returns empty strings for absent components.
    """
    w = word.lower().strip()
    prefix = ""
    suffix = ""
    stem = w

    # Check prefix (longest first)
    for p in _KNOWN_PREFIXES:
        if w.startswith(p) and len(w) > len(p) + 2:
            prefix = p
            stem = w[len(p):]
            break

    # Check suffix on remaining stem (longest first)
    for s in _KNOWN_SUFFIXES:
        if stem.endswith(s) and len(stem) > len(s) + 1:
            suffix = s
            stem = stem[: -len(s)]
            break

    return prefix, stem, suffix


def _pairwise_swap_variants(skeleton: str) -> list[str]:
    """Return all variants of skeleton with one pair of adjacent chars swapped."""
    variants = []
    s = list(skeleton)
    for i in range(len(s) - 1):
        swapped = s[:]
        swapped[i], swapped[i + 1] = swapped[i + 1], swapped[i]
        v = "".join(swapped)
        if v != skeleton and v not in variants:
            variants.append(v)
    return variants


def _consonant_class_diversity(arabic_skel: str, english_skel: str) -> int:
    """Count how many distinct consonant classes are shared between the two skeletons.

    Uses the _CLASS_MAP from correspondence.py for a broader cross-lingual class
    grouping (Arabic and English characters both mapped to the same class labels).
    Returns the count of shared class labels -- higher = more diverse match.
    """
    from juthoor_cognatediscovery_lv2.discovery.correspondence import _CLASS_MAP

    ar_classes = {_CLASS_MAP.get(c, "?") for c in arabic_skel if c in _CLASS_MAP}
    en_classes = {_CLASS_MAP.get(c, "?") for c in english_skel if c in _CLASS_MAP}
    shared = ar_classes & en_classes
    shared.discard("?")
    return len(shared)


def _consonant_class(ch: str) -> str:
    """Return a broad consonant class for partial-match credit (0.5 score)."""
    _CLASSES = [
        frozenset("pbfv"),          # labials
        frozenset("tdszθðʃʒ"),      # dentals / sibilants
        frozenset("kg"),            # velars
        frozenset("mn"),            # nasals
        frozenset("lr"),            # liquids
        frozenset("hw"),            # glottals / glides
    ]
    for cls in _CLASSES:
        if ch in cls:
            return str(id(cls))
    return ch  # unique class — no cross-class credit


def _correspondence_ratio(arabic_letter: str, latin_char: str) -> float:
    normalized = _strip_diacriticals(latin_char).lower()
    if not normalized:
        return 0.0
    letter_weights = CORRESPONDENCE_WEIGHTS.get(arabic_letter)
    if not letter_weights:
        return 1.0
    primary_weight = max(letter_weights.values(), default=0.0)
    if primary_weight <= 0.0:
        return 1.0
    return min(1.0, letter_weights.get(normalized, primary_weight) / primary_weight)


def _score_aligned_projection(
    arabic_skeleton: str,
    english_skeleton: str,
    projected_variant: str,
    *,
    use_position_weights: bool,
) -> float:
    if not arabic_skeleton or not english_skeleton or not projected_variant:
        return 0.0

    n = len(arabic_skeleton)
    base_weights = (
        [_position_weight_for(arabic_skeleton[i], i) for i in range(n)]
        if use_position_weights
        else [1.0] * n
    )
    total_weight = sum(base_weights)
    if total_weight <= 0.0:
        return 0.0

    clean = _strip_diacriticals(projected_variant).lower()
    eng_lower = english_skeleton.lower()
    aligned_len = min(len(clean), len(eng_lower), n)
    numerator = 0.0
    for i in range(aligned_len):
        english_char = eng_lower[i]
        projected_char = clean[i]
        correspondence_weight = _correspondence_ratio(arabic_skeleton[i], english_char)
        if projected_char == english_char:
            numerator += base_weights[i] * correspondence_weight
        elif _consonant_class(projected_char) == _consonant_class(english_char):
            numerator += base_weights[i] * 0.5 * correspondence_weight

    return numerator / total_weight


def _weighted_projection_score(
    arabic_skeleton: str,
    english_skeleton: str,
    variants: tuple[str, ...],
) -> tuple[float, str]:
    """Score with position weights: position 0 (first consonant) counts most.

    For each projected variant, align it position-by-position against the
    English consonant skeleton and compute a weighted match score.

    Match value per position:
      1.0 — exact character match
      0.5 — same broad consonant class
      0.0 — no match

    weighted_score = sum(match[i] * w[i]) / sum(w[i])

    Only positions present in both the variant and the English skeleton are
    scored; missing positions contribute 0 to the numerator.
    """
    if not arabic_skeleton or not english_skeleton or not variants:
        return 0.0, ""

    best_score, best_var = 0.0, ""
    for var in variants:
        score = _score_aligned_projection(
            arabic_skeleton, english_skeleton, var, use_position_weights=True
        )
        if score > best_score:
            best_score, best_var = score, var

    return best_score, best_var


def _best_projection_match(arabic_root: str, english_word: str) -> tuple[float, str]:
    eng_skel = _english_consonant_skeleton(english_word)
    ar_skel = _arabic_consonant_skeleton(arabic_root)
    if not eng_skel or not ar_skel:
        return 0.0, ""
    try:
        variants = project_root_by_target(arabic_root, "european")
    except Exception:
        variants = project_root_sound_laws(arabic_root, include_group_expansion=True, max_variants=256)
    if not variants:
        return 0.0, ""
    best_score, best_var = 0.0, ""
    for var in variants:
        score = _score_aligned_projection(ar_skel, eng_skel, var, use_position_weights=False)
        if score > best_score:
            best_score, best_var = score, var
    return best_score, best_var


def _best_projection_match_ipa(arabic_root: str, ipa_skeleton: str) -> tuple[float, str]:
    """Like _best_projection_match but matches against an IPA consonant skeleton.

    The IPA skeleton uses IPA consonant symbols rather than orthographic letters.
    We map the Arabic projected variants (which produce Latin-like strings) against
    the IPA using a transliteration layer that maps common IPA consonants to their
    closest Latin equivalents before comparison.

    Also applies _ARABIC_IPA_TO_ENGLISH_IPA normalisation to the skeleton so that
    Arabic-specific IPA consonants (ق, ع, ح, etc.) are remapped to their expected
    English realisations before comparison.
    """
    if not ipa_skeleton:
        return 0.0, ""
    ar_skel = _arabic_consonant_skeleton(arabic_root)
    if not ar_skel:
        return 0.0, ""
    try:
        variants = project_root_by_target(arabic_root, "european")
    except Exception:
        variants = project_root_sound_laws(arabic_root, include_group_expansion=True, max_variants=256)
    if not variants:
        return 0.0, ""

    # IPA -> simplified Latin consonant map for comparison with projected variants
    _IPA_TO_LATIN = str.maketrans({
        "θ": "s",   # theta -> s (as in think)
        "ð": "d",   # eth -> d
        "ʃ": "sh",  # -- replaced below via .replace()
        "ʒ": "zh",
        "ŋ": "ng",
        "ɹ": "r",
        "ɾ": "r",
        "ʁ": "r",
        "χ": "kh",
        "ħ": "h",
        "ʕ": "",
        "ɣ": "g",
        "β": "b",
        "ɸ": "f",
        "ʔ": "",    # glottal stop
        "ɫ": "l",
        "ʍ": "wh",
    })

    # Multi-char IPA sequences first, then single-char map
    ipa_lat = ipa_skeleton
    # Apply Arabic IPA → English IPA mapping (longest keys first to avoid partial matches)
    for arabic_ipa, english_options in sorted(
        _ARABIC_IPA_TO_ENGLISH_IPA.items(), key=lambda kv: -len(kv[0])
    ):
        if arabic_ipa in ipa_lat:
            ipa_lat = ipa_lat.replace(arabic_ipa, english_options[0] if english_options else "")
    ipa_lat = ipa_lat.replace("tʃ", "ch").replace("dʒ", "j")
    ipa_lat = ipa_lat.replace("ʃ", "sh").replace("ʒ", "zh")
    ipa_lat = ipa_lat.replace("ŋ", "ng")
    ipa_lat = ipa_lat.translate(_IPA_TO_LATIN)

    best_score, best_var = 0.0, ""
    for var in variants:
        score = _score_aligned_projection(ar_skel, ipa_lat, var, use_position_weights=False)
        if score > best_score:
            best_score, best_var = score, var
    return best_score, best_var


@dataclass
class PhoneticLawScorer:
    _mined_weights: dict[str, Any] = field(default_factory=dict)
    _loaded: bool = False

    _morpheme_data: dict[str, Any] = field(default_factory=dict)
    _morpheme_loaded: bool = False

    _ipa_lookup: Any = field(default=None)  # IPALookup — lazy-initialised

    _synonym_families: dict[str, list[str]] = field(default_factory=dict)
    _synonym_loaded: bool = False

    def _get_synonym_families(self) -> dict[str, list[str]]:
        """Lazy-load synonym families from LV1 data. Returns empty dict if file missing."""
        if self._synonym_loaded:
            return self._synonym_families
        self._synonym_loaded = True
        here = Path(__file__).resolve()
        repo_root = here.parents[4]
        families_path = (
            repo_root
            / "Juthoor-ArabicGenome-LV1"
            / "data"
            / "theory_canon"
            / "roots"
            / "synonym_families_full.jsonl"
        )
        if families_path.exists():
            from juthoor_cognatediscovery_lv2.discovery.synonym_expansion import load_synonym_families
            self._synonym_families = load_synonym_families(str(families_path))
        return self._synonym_families

    def _get_ipa_lookup(self) -> Any:
        """Lazy-initialise and return the IPALookup instance."""
        if self._ipa_lookup is None:
            from .ipa_lookup import IPALookup
            self._ipa_lookup = IPALookup()
        return self._ipa_lookup

    def _try_load_mined_data(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        # Walk up from this file to find the repo root
        here = Path(__file__).resolve()
        # src/juthoor_cognatediscovery_lv2/discovery/phonetic_law_scorer.py
        # -> parents[0]=discovery, [1]=juthoor_cognate..., [2]=src, [3]=LV2_ROOT, [4]=REPO_ROOT
        repo_root = here.parents[4]
        weights_path = (
            repo_root
            / "Juthoor-CognateDiscovery-LV2"
            / "data"
            / "processed"
            / "phonetic_law_weights.json"
        )
        if weights_path.exists():
            with weights_path.open("r", encoding="utf-8") as f:
                self._mined_weights = json.load(f)

    def _try_load_morpheme_data(self) -> None:
        if self._morpheme_loaded:
            return
        self._morpheme_loaded = True
        here = Path(__file__).resolve()
        repo_root = here.parents[4]
        morpheme_path = (
            repo_root
            / "Juthoor-CognateDiscovery-LV2"
            / "data"
            / "processed"
            / "morpheme_correspondences.json"
        )
        if morpheme_path.exists():
            with morpheme_path.open("r", encoding="utf-8") as f:
                self._morpheme_data = json.load(f)

    def _get_morpheme_suffixes(self) -> set[str]:
        """Return the set of known English suffixes from morpheme_correspondences.json."""
        self._try_load_morpheme_data()
        return {
            entry["english"].lstrip("-")
            for entry in self._morpheme_data.get("suffixes", [])
            if entry.get("english")
        }

    def _get_morpheme_prefixes(self) -> set[str]:
        """Return the set of known English prefixes from morpheme_correspondences.json."""
        self._try_load_morpheme_data()
        return {
            entry["english"].rstrip("-")
            for entry in self._morpheme_data.get("prefixes", [])
            if entry.get("english")
        }

    def score_pair(
        self,
        source_entry: dict[str, Any],
        target_entry: dict[str, Any],
    ) -> dict[str, Any]:
        self._try_load_mined_data()
        arabic_root = str(
            source_entry.get("root_norm")
            or source_entry.get("root")
            or source_entry.get("translit")
            or source_entry.get("lemma")
            or ""
        ).strip()
        english_lemma = str(
            target_entry.get("lemma")
            or target_entry.get("translit")
            or ""
        ).strip()

        if not arabic_root or not english_lemma:
            return {
                "phonetic_law_score": 0.0,
                "best_projection": "",
                "projection_details": {},
            }

        proj_score, best_var = _best_projection_match(arabic_root, english_lemma)

        ar_skel = _arabic_consonant_skeleton(arabic_root)
        eng_skel = _english_consonant_skeleton(english_lemma)

        # --- V4: position-weighted scoring ---
        try:
            variants_for_pos = project_root_by_target(arabic_root, "european")
        except Exception:
            variants_for_pos = project_root_sound_laws(
                arabic_root, include_group_expansion=True, max_variants=256
            )
        pos_weighted_score, pos_best_var = _weighted_projection_score(
            ar_skel, eng_skel, variants_for_pos
        )
        if pos_best_var and not best_var:
            best_var = pos_best_var
        primary_latin = _strip_diacriticals(
            "".join(LATIN_EQUIVALENTS.get(ch, (ch,))[0] for ch in ar_skel)
        )
        direct_score = (
            SequenceMatcher(None, primary_latin, eng_skel).ratio()
            if primary_latin and eng_skel
            else 0.0
        )

        # --- IPA-based scoring (V3) ---
        # Use IPA consonant skeleton when available — more accurate than orthography
        # for words with silent letters (knight, psalm, write, etc.)
        ipa_proj_score = 0.0
        ipa_skel = None
        ipa_lookup = self._get_ipa_lookup()
        ipa_skel = ipa_lookup.ipa_consonant_skeleton(english_lemma)
        if ipa_skel:
            ipa_proj_score, ipa_var = _best_projection_match_ipa(arabic_root, ipa_skel)
            if ipa_proj_score > proj_score and not best_var:
                best_var = ipa_var

        # --- Task 3: Improved metathesis ---
        # Try full reversal + all pairwise adjacent-consonant swaps
        metathesis_score = 0.0
        if primary_latin and eng_skel:
            # Full reversal
            metathesis_score = SequenceMatcher(None, primary_latin[::-1], eng_skel).ratio()
            # Pairwise swaps of adjacent consonants
            for swap_var in _pairwise_swap_variants(primary_latin):
                s = SequenceMatcher(None, swap_var, eng_skel).ratio()
                if s > metathesis_score:
                    metathesis_score = s

        mined_bonus = 0.0
        if self._mined_weights:
            for law in self._mined_weights.get("individual_laws", []):
                if law.get("arabic", "") in ar_skel and law.get("english", "") in eng_skel:
                    mined_bonus += law.get("weight", 0) * 0.02
            mined_bonus = min(mined_bonus, 0.1)

        # --- Task 2: Morpheme-aware scoring ---
        morpheme_bonus = 0.0
        stem_score = 0.0
        stem_used = ""
        _, stem, suffix = _morpheme_decompose(english_lemma)
        if (suffix or _) and stem and len(stem) >= 2:
            stem_proj, stem_var = _best_projection_match(arabic_root, stem)
            stem_skel = _english_consonant_skeleton(stem)
            stem_direct = (
                SequenceMatcher(None, primary_latin, stem_skel).ratio()
                if primary_latin and stem_skel
                else 0.0
            )
            stem_score = max(stem_proj, stem_direct)
            if stem_score > max(proj_score, direct_score):
                stem_used = stem
                if not best_var and stem_var:
                    best_var = stem_var

        # Check if suffix/prefix matches a known morpheme correspondence → +0.05 bonus
        known_suffixes = self._get_morpheme_suffixes()
        known_prefixes = self._get_morpheme_prefixes()
        prefix_str, _, suffix_str = _morpheme_decompose(english_lemma)
        if suffix_str in known_suffixes or prefix_str in known_prefixes:
            morpheme_bonus = 0.05

        # --- V5: Synonym family expansion ---
        # If the primary root does not match well, try up to 3 synonym roots.
        best_synonym_score = 0.0
        synonyms_tried: list[str] = []
        synonym_families = self._get_synonym_families()
        if synonym_families and arabic_root:
            from juthoor_cognatediscovery_lv2.discovery.synonym_expansion import expand_root
            synonyms = expand_root(arabic_root, synonym_families)
            for syn in synonyms[:3]:  # cap at 3 to avoid combinatorial explosion
                if syn == arabic_root:
                    continue
                synonyms_tried.append(syn)
                syn_score, _ = _best_projection_match(syn, english_lemma)
                if syn_score > best_synonym_score:
                    best_synonym_score = syn_score

        base_score = max(proj_score, direct_score, stem_score, ipa_proj_score, pos_weighted_score, best_synonym_score)
        combined = (
            base_score
            + min(metathesis_score * 0.4, 0.12)  # raised from 0.3 to 0.4, cap 0.12
            + mined_bonus
            + morpheme_bonus
        )
        combined = min(combined, 1.0)

        # --- V6: Consonant class diversity penalty ---
        # A true cognate matches across DIVERSE consonant classes.
        # Matches that share <2 distinct consonant classes are likely coincidental.
        diversity = _consonant_class_diversity(ar_skel, eng_skel)
        diversity_penalty_applied = False
        if diversity < 2:
            combined *= 0.6
            diversity_penalty_applied = True

                # --- Frequency penalty (V3) ---
        # Common function words match by coincidence — reduce their score to cut false positives.
        freq_penalty_applied = False
        if english_lemma.lower() in _HIGH_FREQ_WORDS:
            combined *= 0.6
            freq_penalty_applied = True

        return {
            "phonetic_law_score": round(combined, 6),
            "best_projection": best_var,
            "projection_details": {
                "projection_match": round(proj_score, 4),
                "direct_match": round(direct_score, 4),
                "metathesis_match": round(metathesis_score, 4),
                "mined_bonus": round(mined_bonus, 4),
                "morpheme_bonus": round(morpheme_bonus, 4),
                "stem_score": round(stem_score, 4),
                "stem_used": stem_used,
                "arabic_skeleton": ar_skel,
                "english_skeleton": eng_skel,
                "primary_latin": primary_latin,
                "ipa_proj_score": round(ipa_proj_score, 4),
                "ipa_skeleton": ipa_skel or "",
                "freq_penalty_applied": freq_penalty_applied,
                "position_weighted_score": round(pos_weighted_score, 4),
                "synonym_match": round(best_synonym_score, 4),
                "synonyms_tried": len(synonyms_tried),
                "consonant_diversity": diversity,
                "diversity_penalty_applied": diversity_penalty_applied,
            },
        }

    def phonetic_law_bonus(
        self,
        source_entry: dict[str, Any],
        target_entry: dict[str, Any],
    ) -> float:
        # Minimum skeleton length guard: too short = unreliable match
        arabic_root = str(
            source_entry.get("root_norm")
            or source_entry.get("root")
            or source_entry.get("translit")
            or source_entry.get("lemma")
            or ""
        ).strip()
        english_lemma = str(
            target_entry.get("lemma") or target_entry.get("translit") or ""
        ).strip()
        ar_skel = _arabic_consonant_skeleton(arabic_root)
        eng_skel = _english_consonant_skeleton(english_lemma)
        if len(ar_skel) < 2 or len(eng_skel) < 2:
            return 0.0

        raw = self.score_pair(source_entry, target_entry)["phonetic_law_score"]

        # Length ratio penalty: extreme mismatch = unlikely cognate, halve the score
        ratio = len(eng_skel) / len(ar_skel) if ar_skel else 0.0
        if ratio > 3.0 or ratio < 0.33:
            raw *= 0.5

        # V6: Sigmoid bonus curve -- sharply rewards high-confidence matches.
        # Threshold raised to 0.55 (was 0.50); sigmoid centred at 0.70.
        # Score 0.55-0.65: very small bonus (sigmoid approx 0.05-0.15 of max)
        # Score 0.70: bonus approx 0.075 (half max)
        # Score 0.85+: bonus approx 0.14 (near max)
        if raw < 0.55:
            return 0.0
        x = 10.0 * (raw - 0.70)
        sigmoid = 1.0 / (1.0 + math.exp(-x))
        return round(min(0.15, 0.15 * sigmoid), 6)
