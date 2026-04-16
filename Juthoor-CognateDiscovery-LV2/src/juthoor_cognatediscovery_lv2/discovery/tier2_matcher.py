"""Tier 2 extended sound-law matcher for the Juthoor cognate discovery pipeline.

Eye 1 (Tier 1) applies basic consonant skeleton matching via Jaccard similarity
and catches roughly 55% of lemmas. Tier 2 runs on the ~45% that Tier 1 missed,
applying richer cross-family sound correspondence rules and positional conditioning.

No LLM calls — pure rule-based, runs in seconds.

Usage (standalone):
    from juthoor_cognatediscovery_lv2.discovery.tier2_matcher import tier2_match

Usage (from Eye 1 script):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from juthoor_cognatediscovery_lv2.discovery.tier2_matcher import tier2_match
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path bootstrapping — allows direct execution and import from run_eye1_full_scale.py
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve()
_LV2_SRC = _HERE.parents[3]  # .../Juthoor-CognateDiscovery-LV2/src
if str(_LV2_SRC) not in sys.path:
    sys.path.insert(0, str(_LV2_SRC))

# ---------------------------------------------------------------------------
# Consonant helpers (shared with target_morphology)
# ---------------------------------------------------------------------------

_ENG_CONSONANTS_RE = re.compile(r"[bcdfghjklmnpqrstvwxyz]")


def _extract_consonants(text: str) -> str:
    """Strip vowels and non-letter characters, return consonant skeleton."""
    return "".join(_ENG_CONSONANTS_RE.findall(text.lower()))


# ---------------------------------------------------------------------------
# CROSS_FAMILY_SHIFTS
#
# Sound correspondences between Arabic consonants and IE realisations that go
# beyond the basic EQUIVALENTS tables in phonetic_law_scorer.py.  These
# represent historically documented (or plausibly argued) correspondences used
# by Nostratic / Afroasiatic-IE comparative proposals.
#
# Each Arabic character maps to a tuple of possible IE surface realisations.
# The empty string "" means the consonant is deleted entirely in the target.
# ---------------------------------------------------------------------------

CROSS_FAMILY_SHIFTS: dict[str, tuple[str, ...]] = {
    # م (m) ↔ w  — documented in some Nostratic proposals (bilabial weakening)
    "م": ("m", "w"),
    # ع (ʕ) ↔ Ø  — guttural deletion; ʿayn commonly lost in IE loans
    "ع": ("", "h", "g"),
    # ه (h) ↔ Ø  — aspiration loss; also sometimes ↔ k (rough breathing shift)
    "ه": ("h", "", "k"),
    # ن (n) ↔ l  — liquid interchange, widely documented in Semitic
    "ن": ("n", "l"),
    # ح (ḥ) ↔ Ø or h  — pharyngeal simplification
    "ح": ("h", "", "kh"),
    # غ (ġ) ↔ g or Ø  — uvular simplification
    "غ": ("g", "gh", ""),
    # Also carry forward the most productive basic correspondences
    # so that Tier 2 can run standalone without the full EQUIVALENTS table.
    "ب": ("b", "p", "f"),
    "ت": ("t", "d"),
    "ث": ("th", "s", "t"),
    "ج": ("j", "g", "k"),
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
    "ف": ("f", "p", "b"),
    "ق": ("k", "q", "g"),
    "ك": ("k", "c"),
    "ل": ("l", "r"),
    "و": ("w", "v", "b"),
    "ي": ("y", "i"),
    "ا": ("", "a"),
}

# ---------------------------------------------------------------------------
# POSITIONAL_RULES
#
# Each rule is a dict with keys:
#   arabic_char  — the Arabic consonant this rule targets
#   position     — "initial", "medial", or "final"
#   ie_variants  — tuple of IE surface forms at that position
# ---------------------------------------------------------------------------

POSITIONAL_RULES: list[dict[str, Any]] = [
    # Arabic ق word-initial → Latin/Greek k; word-medial → g
    {
        "arabic_char": "ق",
        "position": "initial",
        "ie_variants": ("k", "c", "q"),
    },
    {
        "arabic_char": "ق",
        "position": "medial",
        "ie_variants": ("g", "k"),
    },
    {
        "arabic_char": "ق",
        "position": "final",
        "ie_variants": ("k", "g"),
    },
    # Arabic ع word-initial → Ø (deleted); word-medial → sometimes h or g
    {
        "arabic_char": "ع",
        "position": "initial",
        "ie_variants": ("",),
    },
    {
        "arabic_char": "ع",
        "position": "medial",
        "ie_variants": ("", "h", "g"),
    },
    {
        "arabic_char": "ع",
        "position": "final",
        "ie_variants": ("", "h"),
    },
    # Arabic ح pharyngeal: initial → h; medial/final → Ø
    {
        "arabic_char": "ح",
        "position": "initial",
        "ie_variants": ("h", "kh"),
    },
    {
        "arabic_char": "ح",
        "position": "medial",
        "ie_variants": ("", "h"),
    },
    {
        "arabic_char": "ح",
        "position": "final",
        "ie_variants": ("", "h"),
    },
    # Arabic غ uvular: initial → g; medial → g or Ø
    {
        "arabic_char": "غ",
        "position": "initial",
        "ie_variants": ("g", "gh"),
    },
    {
        "arabic_char": "غ",
        "position": "medial",
        "ie_variants": ("g", ""),
    },
    # Arabic ن liquid interchange: initial always n; medial may be l
    {
        "arabic_char": "ن",
        "position": "initial",
        "ie_variants": ("n",),
    },
    {
        "arabic_char": "ن",
        "position": "medial",
        "ie_variants": ("n", "l"),
    },
    {
        "arabic_char": "ن",
        "position": "final",
        "ie_variants": ("n", "l"),
    },
]

# Build a nested lookup for positional rules: {arabic_char: {position: (variants...)}}
_POSITIONAL_LOOKUP: dict[str, dict[str, tuple[str, ...]]] = {}
for _rule in POSITIONAL_RULES:
    _char = _rule["arabic_char"]
    _pos = _rule["position"]
    if _char not in _POSITIONAL_LOOKUP:
        _POSITIONAL_LOOKUP[_char] = {}
    _POSITIONAL_LOOKUP[_char][_pos] = tuple(_rule["ie_variants"])


# ---------------------------------------------------------------------------
# Arabic consonant extraction
# ---------------------------------------------------------------------------

_ARABIC_WEAK = frozenset("اويى")
_ARABIC_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")
_ARABIC_CONSONANT_RE = re.compile(r"[\u0621-\u064A]")
_HAMZA_TR = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ؤ": "و", "ئ": "ي", "ء": "ا",
})


def _arabic_skeleton(text: str) -> str:
    """Extract the consonant skeleton from an Arabic root string.

    Strips diacritics, normalises hamza variants, removes weak letters
    (alif / waw / ya) that act as vowel holders in trilateral roots.
    """
    text = _ARABIC_DIACRITICS_RE.sub("", text)
    text = text.translate(_HAMZA_TR)
    chars = _ARABIC_CONSONANT_RE.findall(text)
    return "".join(ch for ch in chars if ch not in _ARABIC_WEAK)


def _position_of(index: int, total: int) -> str:
    """Map a character index in a skeleton to a positional label."""
    if total <= 1:
        return "initial"
    if index == 0:
        return "initial"
    if index == total - 1:
        return "final"
    return "medial"


# ---------------------------------------------------------------------------
# expand_with_cross_family_shifts
# ---------------------------------------------------------------------------

_MAX_EXPANDED = 32  # cap to avoid combinatorial explosion


def expand_with_cross_family_shifts(arabic_skeleton: str) -> list[str]:
    """Generate IE consonant skeleton variants from an Arabic skeleton string.

    Applies CROSS_FAMILY_SHIFTS one position at a time (non-combinatorial) to
    keep the variant count manageable.  Always includes the primary projection
    as the first element.

    Parameters
    ----------
    arabic_skeleton:
        Pure consonant string in Arabic script, e.g. "مطر".

    Returns
    -------
    list[str]
        Unique IE skeleton strings, primary first.
    """
    if not arabic_skeleton:
        return []

    # Build per-position option lists using CROSS_FAMILY_SHIFTS
    char_list = list(arabic_skeleton)
    option_lists: list[list[str]] = []
    for ch in char_list:
        opts = list(CROSS_FAMILY_SHIFTS.get(ch, (ch,)))
        # Filter to ASCII, remove duplicates while preserving order
        seen_opts: dict[str, None] = {}
        clean: list[str] = []
        for o in opts:
            if o not in seen_opts and (o == "" or o.isascii()):
                seen_opts[o] = None
                clean.append(o)
        option_lists.append(clean if clean else [""])

    # Primary = first option at each position
    primary = "".join(o[0] for o in option_lists)
    primary = _extract_consonants(primary) if primary else primary

    seen: dict[str, None] = {primary: None}
    variants: list[str] = [primary]

    def _add(s: str) -> None:
        s = _extract_consonants(s) if not s.isascii() else s
        # Retain only consonant characters
        s = "".join(c for c in s.lower() if c.isalpha())
        if s and len(s) >= 1 and s not in seen and len(variants) < _MAX_EXPANDED:
            seen[s] = None
            variants.append(s)

    # One-position substitutions only
    for i, opts in enumerate(option_lists):
        for alt in opts[1:]:  # skip primary (index 0)
            parts = [option_lists[j][0] for j in range(len(option_lists))]
            parts[i] = alt
            candidate = "".join(parts)
            _add(candidate)
            if len(variants) >= _MAX_EXPANDED:
                return variants

    return variants


# ---------------------------------------------------------------------------
# apply_positional_rules
# ---------------------------------------------------------------------------

def apply_positional_rules(arabic_skeleton: str, lang: str) -> list[str]:
    """Generate IE consonant skeleton variants using position-dependent rules.

    For each character in *arabic_skeleton* that has an entry in
    POSITIONAL_RULES, substitute the positionally-appropriate IE variant
    while keeping all other characters at their primary (CROSS_FAMILY_SHIFTS)
    value.

    Parameters
    ----------
    arabic_skeleton:
        Pure Arabic consonant string.
    lang:
        Target language code (e.g. "lat", "grc").  Currently the positional
        rules are language-agnostic but the parameter is kept for future
        per-language conditioning.

    Returns
    -------
    list[str]
        Unique IE skeleton strings.
    """
    if not arabic_skeleton:
        return []

    char_list = list(arabic_skeleton)
    total = len(char_list)

    # Build the primary (non-positional) projection
    primary_parts = [
        CROSS_FAMILY_SHIFTS.get(ch, (ch,))[0] for ch in char_list
    ]
    primary = "".join(primary_parts)
    primary = "".join(c for c in primary.lower() if c.isalpha() and c.isascii())

    seen: dict[str, None] = {primary: None}
    variants: list[str] = [primary]

    def _add(s: str) -> None:
        s = "".join(c for c in s.lower() if c.isalpha() and c.isascii())
        if s and s not in seen and len(variants) < _MAX_EXPANDED:
            seen[s] = None
            variants.append(s)

    for i, ch in enumerate(char_list):
        if ch not in _POSITIONAL_LOOKUP:
            continue
        pos_label = _position_of(i, total)
        pos_variants = _POSITIONAL_LOOKUP[ch].get(pos_label, ())
        for pv in pos_variants:
            # Build a new projection with this positional variant at position i
            parts = list(primary_parts)
            parts[i] = pv
            candidate = "".join(parts)
            _add(candidate)
            if len(variants) >= _MAX_EXPANDED:
                return variants

    return variants


# ---------------------------------------------------------------------------
# split_compound  (delegates to target_morphology.decompose_target)
# ---------------------------------------------------------------------------

def split_compound(target_word: str, lang: str) -> list[str]:
    """Split a compound target-language word into independent matchable parts.

    Delegates to :func:`~juthoor_cognatediscovery_lv2.discovery.target_morphology.decompose_target`
    which handles Latin suffix/prefix stripping, Greek compound splitting, and
    Old English compound boundary detection.

    Parameters
    ----------
    target_word:
        Surface lemma as it appears in the corpus.
    lang:
        Language code: "lat", "grc", "ang", or similar.

    Returns
    -------
    list[str]
        All candidate stems (original first), as returned by ``decompose_target``.
    """
    from juthoor_cognatediscovery_lv2.discovery.target_morphology import decompose_target
    return decompose_target(target_word, lang)


# ---------------------------------------------------------------------------
# Scoring helpers (mirrors Tier 1 scoring functions)
# ---------------------------------------------------------------------------

def _jaccard(a: frozenset, b: frozenset) -> float:
    """Set Jaccard similarity between two character frozensets."""
    inter = len(a & b)
    if inter == 0:
        return 0.0
    return inter / len(a | b)


def _ordered_overlap(skel_a: str, skel_b: str) -> list[str]:
    """Consonants appearing in both skeletons in the same relative order.

    Greedy left-to-right scan — identical logic to run_eye1_full_scale.ordered_overlap.
    """
    j = 0
    matches: list[str] = []
    for ch in skel_a:
        while j < len(skel_b):
            if skel_b[j] == ch:
                matches.append(ch)
                j += 1
                break
            j += 1
    return matches


def _discovery_score(
    jaccard: float,
    ord_ov_len: int,
    ar_len: int,
    tgt_len: int,
) -> float:
    """Composite score identical to run_eye1_full_scale._discovery_score."""
    min_len = min(ar_len, tgt_len)
    max_len = max(ar_len, tgt_len)
    ord_ov_ratio = ord_ov_len / min_len if min_len > 0 else 0.0
    len_ratio = min_len / max_len if max_len > 0 else 0.0
    len_bonus = min(min_len / 4.0, 1.0)
    return (
        jaccard * 0.35
        + ord_ov_ratio * 0.30
        + len_ratio * 0.15
        + len_bonus * 0.20
    )


# ---------------------------------------------------------------------------
# tier2_match — main entry point
# ---------------------------------------------------------------------------

def tier2_match(
    arabic_skeleton: str,
    target_skeletons: list[str],
    lang: str,
) -> tuple[float, dict[str, Any]]:
    """Tier 2 extended-sound-law matcher.

    Takes an Arabic consonant skeleton (Arabic script), generates a rich set
    of IE variant projections via cross-family shifts and positional rules, then
    scores each variant against every target skeleton (including compound parts)
    using the same Jaccard + ordered-overlap composite score as Tier 1.

    Parameters
    ----------
    arabic_skeleton:
        Arabic consonant skeleton string in Arabic script, e.g. "مطر".
        May also be a pre-projected Latin string — detection is automatic.
    target_skeletons:
        List of IE consonant skeleton strings already extracted from the target
        lemma (e.g. by ``target_morphology.extract_all_skeletons``).  May include
        compound parts.
    lang:
        Target language code ("lat", "grc", "ang", etc.).

    Returns
    -------
    (best_score, match_details)
        best_score  — composite discovery score in [0, 1].
        match_details — dict with keys:
            - best_arabic_variant: IE variant of the Arabic skeleton that scored best
            - best_target_skeleton: target skeleton that scored best
            - jaccard: set Jaccard of the best pair
            - ordered_overlap: list of matching consonants in order
            - ordered_overlap_ratio: len(ordered_overlap) / min(ar_len, tgt_len)
            - n_arabic_variants: number of Arabic IE projections generated
            - n_target_skeletons: number of target skeletons evaluated
    """
    if not arabic_skeleton or not target_skeletons:
        return 0.0, {
            "best_arabic_variant": "",
            "best_target_skeleton": "",
            "jaccard": 0.0,
            "ordered_overlap": [],
            "ordered_overlap_ratio": 0.0,
            "n_arabic_variants": 0,
            "n_target_skeletons": len(target_skeletons),
        }

    # Determine whether the input is Arabic script or already a Latin projection
    _is_arabic = any("\u0600" <= ch <= "\u06ff" for ch in arabic_skeleton)

    if _is_arabic:
        # Generate all IE projections
        shift_variants = expand_with_cross_family_shifts(arabic_skeleton)
        pos_variants = apply_positional_rules(arabic_skeleton, lang)
        # Merge, deduplicating while preserving order
        seen_av: dict[str, None] = {}
        arabic_variants: list[str] = []
        for v in shift_variants + pos_variants:
            if v and v not in seen_av:
                seen_av[v] = None
                arabic_variants.append(v)
    else:
        # Already a Latin/Greek projection — use as-is, add simple single-step variants
        arabic_variants = [arabic_skeleton]
        # Still try positional expansion but treat it as opaque
        # (just add what we have)

    if not arabic_variants:
        arabic_variants = [arabic_skeleton]

    # Filter out empty variants for scoring
    arabic_variants_clean = [v for v in arabic_variants if v]
    if not arabic_variants_clean:
        arabic_variants_clean = arabic_variants

    # Filter target skeletons
    target_skeletons_clean = [s for s in target_skeletons if s]

    # Pre-compute frozensets
    ar_sets = [frozenset(v) for v in arabic_variants_clean]
    tgt_sets = [frozenset(s) for s in target_skeletons_clean]

    best_score = 0.0
    best_ar_var = arabic_variants_clean[0] if arabic_variants_clean else ""
    best_tgt_skel = target_skeletons_clean[0] if target_skeletons_clean else ""
    best_jaccard = 0.0
    best_ord_ov: list[str] = []

    for ai, (ar_var, ar_set) in enumerate(zip(arabic_variants_clean, ar_sets)):
        ar_len = len(ar_var)
        for ti, (tgt_skel, tgt_set) in enumerate(zip(target_skeletons_clean, tgt_sets)):
            tgt_len = len(tgt_skel)

            j = _jaccard(ar_set, tgt_set)
            ord_ov = _ordered_overlap(ar_var, tgt_skel)
            score = _discovery_score(j, len(ord_ov), ar_len, tgt_len)

            if score > best_score:
                best_score = score
                best_ar_var = ar_var
                best_tgt_skel = tgt_skel
                best_jaccard = j
                best_ord_ov = ord_ov

    min_len = min(len(best_ar_var), len(best_tgt_skel))
    ord_ov_ratio = len(best_ord_ov) / min_len if min_len > 0 else 0.0

    match_details: dict[str, Any] = {
        "best_arabic_variant": best_ar_var,
        "best_target_skeleton": best_tgt_skel,
        "jaccard": round(best_jaccard, 4),
        "ordered_overlap": best_ord_ov,
        "ordered_overlap_ratio": round(ord_ov_ratio, 3),
        "n_arabic_variants": len(arabic_variants_clean),
        "n_target_skeletons": len(target_skeletons_clean),
    }

    return round(best_score, 4), match_details
