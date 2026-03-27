"""Phonetic law scoring for cross-family (Arabic<->English/European) cognate candidates.

Uses LV1 sound laws (Khashim, Latin equivalents) to project Arabic roots
into expected English consonant patterns and scores the match.

V2 additions:
- Morpheme-aware scoring: strip known prefixes/suffixes, score the stem
- Improved metathesis: try pairwise adjacent-consonant swaps (partial metathesis)

V3 additions:
- IPA-based consonant skeleton (more accurate than orthographic for English)
- Frequency penalty for high-frequency function words
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

# Try importing LV1 sound laws; fall back to inline copies if unavailable
try:
    from juthoor_arabicgenome_lv1.factory.sound_laws import (
        LATIN_EQUIVALENTS,
        normalize_arabic_root,
        project_root_sound_laws,
    )
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


_DIACRITICAL_MAP = str.maketrans(
    {"ṭ": "t", "ṣ": "s", "ḥ": "h", "ḍ": "d", "ẓ": "z", "ʕ": "", "ġ": "g", "ḫ": "kh"}
)
_ENG_CONSONANTS_RE = re.compile(r"[bcdfghjklmnpqrstvwxyz]")
_ARABIC_WEAK = set("اويى")

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


def _best_projection_match(arabic_root: str, english_word: str) -> tuple[float, str]:
    eng_skel = _english_consonant_skeleton(english_word)
    if not eng_skel:
        return 0.0, ""
    variants = project_root_sound_laws(arabic_root, include_group_expansion=True, max_variants=256)
    if not variants:
        return 0.0, ""
    best_score, best_var = 0.0, ""
    for var in variants:
        clean = _strip_diacriticals(var)
        score = SequenceMatcher(None, clean, eng_skel).ratio()
        if score > best_score:
            best_score, best_var = score, var
    return best_score, best_var


def _best_projection_match_ipa(arabic_root: str, ipa_skeleton: str) -> tuple[float, str]:
    """Like _best_projection_match but matches against an IPA consonant skeleton.

    The IPA skeleton uses IPA consonant symbols rather than orthographic letters.
    We map the Arabic projected variants (which produce Latin-like strings) against
    the IPA using a transliteration layer that maps common IPA consonants to their
    closest Latin equivalents before comparison.
    """
    if not ipa_skeleton:
        return 0.0, ""
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
    ipa_lat = ipa_lat.replace("tʃ", "ch").replace("dʒ", "j")
    ipa_lat = ipa_lat.replace("ʃ", "sh").replace("ʒ", "zh")
    ipa_lat = ipa_lat.replace("ŋ", "ng")
    ipa_lat = ipa_lat.translate(_IPA_TO_LATIN)

    best_score, best_var = 0.0, ""
    for var in variants:
        clean = _strip_diacriticals(var)
        score = SequenceMatcher(None, clean, ipa_lat).ratio()
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

        base_score = max(proj_score, direct_score, stem_score, ipa_proj_score)
        combined = (
            base_score
            + min(metathesis_score * 0.4, 0.12)  # raised from 0.3 to 0.4, cap 0.12
            + mined_bonus
            + morpheme_bonus
        )
        combined = min(combined, 1.0)

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

        # Optimal threshold = 0.50 (tuned to minimise false positives)
        if raw < 0.50:
            return 0.0
        return round(min(0.15, (raw - 0.50) * 0.30), 6)
