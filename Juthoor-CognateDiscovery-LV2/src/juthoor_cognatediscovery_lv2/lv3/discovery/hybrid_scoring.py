from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any


_DEFAULT_VOWELS = set("aeiouyɑæɛɪɔʊʌəɨʉɯ")  # Latin + IPA vowels
_ARABIC_MATRES = frozenset("وياأإآ")             # Arabic long-vowel carriers (matres lectionis)
_ARABIC_DIACRITICS_RE = re.compile(r"[\u064B-\u0652\u0670\u0640]")  # short vowel diacritics
_PUNCT_RE = re.compile(r"[\s\-\u2010-\u2015_.,;:!?\"'`~()\[\]{}<>|/\\]+")


def _norm_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.casefold()
    text = _PUNCT_RE.sub("", text)
    return text


def _seq_ratio(a: str, b: str) -> float:
    a = a or ""
    b = b or ""
    if not a or not b:
        return 0.0
    return float(SequenceMatcher(None, a, b).ratio())


def _char_ngrams(text: str, n: int) -> set[str]:
    if len(text) < n:
        return set()
    return {text[i : i + n] for i in range(0, len(text) - n + 1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return float(len(a & b) / len(union))


def _skeleton(text: str) -> str:
    text = _ARABIC_DIACRITICS_RE.sub("", text)  # strip Arabic short vowel diacritics first
    text = _norm_text(text)
    out: list[str] = []
    for ch in text:
        if not ch.isalpha():
            continue
        if ch in _ARABIC_MATRES:   # Arabic long-vowel carriers act as vowels
            continue
        if ch in _DEFAULT_VOWELS:  # Latin/IPA vowels
            continue
        out.append(ch)
    return "".join(out)


def _first_nonempty(*values: Any) -> str:
    for v in values:
        s = str(v or "").strip()
        if s:
            return s
    return ""


@dataclass(frozen=True)
class HybridWeights:
    semantic: float = 0.40   # semantic model weight (BGE-M3)
    form: float = 0.20       # form model weight (ByT5)
    orthography: float = 0.15
    sound: float = 0.15
    skeleton: float = 0.10
    family_boost: float = 0.05  # multiplicative boost (+5%) for same language family


def orthography_score(source: dict[str, Any], target: dict[str, Any]) -> float:
    a_raw = _first_nonempty(source.get("translit"), source.get("lemma"))
    b_raw = _first_nonempty(target.get("translit"), target.get("lemma"))
    a = _norm_text(a_raw)
    b = _norm_text(b_raw)
    if not a or not b:
        return 0.0

    grams_a = _char_ngrams(a, 2) | _char_ngrams(a, 3) | _char_ngrams(a, 4)
    grams_b = _char_ngrams(b, 2) | _char_ngrams(b, 3) | _char_ngrams(b, 4)
    j = _jaccard(grams_a, grams_b)
    r = _seq_ratio(a, b)
    return float(0.6 * j + 0.4 * r)


def sound_score(source: dict[str, Any], target: dict[str, Any]) -> float | None:
    a_raw = _first_nonempty(source.get("ipa"), source.get("ipa_raw"))
    b_raw = _first_nonempty(target.get("ipa"), target.get("ipa_raw"))
    a = _norm_text(a_raw)
    b = _norm_text(b_raw)
    if not a or not b:
        return None   # IPA absent — skip this component rather than penalise with 0.0
    return _seq_ratio(a, b)


def skeleton_score(source: dict[str, Any], target: dict[str, Any]) -> float:
    a_src = _first_nonempty(source.get("ipa"), source.get("translit"), source.get("lemma"))
    b_src = _first_nonempty(target.get("ipa"), target.get("translit"), target.get("lemma"))
    a = _skeleton(a_src)
    b = _skeleton(b_src)
    if not a or not b:
        return 0.0
    grams_a = _char_ngrams(a, 2) | _char_ngrams(a, 3)
    grams_b = _char_ngrams(b, 2) | _char_ngrams(b, 3)
    j = _jaccard(grams_a, grams_b)
    r = _seq_ratio(a, b)
    return float(0.5 * j + 0.5 * r)


def combined_score(
    *,
    semantic_score: float | None,
    form_score: float | None,
    orthography: float | None,
    sound: float | None,
    skeleton: float | None,
    weights: HybridWeights,
) -> tuple[float, dict[str, float]]:
    parts: list[tuple[str, float, float]] = []
    if semantic_score is not None:
        parts.append(("semantic", float(semantic_score), float(weights.semantic)))
    if form_score is not None:
        parts.append(("form", float(form_score), float(weights.form)))
    if orthography is not None:
        parts.append(("orthography", float(orthography), float(weights.orthography)))
    if sound is not None:
        parts.append(("sound", float(sound), float(weights.sound)))
    if skeleton is not None:
        parts.append(("skeleton", float(skeleton), float(weights.skeleton)))

    if not parts:
        return 0.0, {}

    weight_sum = sum(w for _, _, w in parts)
    if weight_sum <= 0:
        return 0.0, {}

    score = sum(v * w for _, v, w in parts) / weight_sum
    used = {k: w for k, _, w in parts}
    return float(score), used


def compute_hybrid(
    *,
    source: dict[str, Any],
    target: dict[str, Any],
    semantic: float | None,
    form: float | None,
    weights: HybridWeights,
) -> dict[str, Any]:
    from .lang import are_same_family

    ort = orthography_score(source, target)
    snd = sound_score(source, target)   # may be None when IPA is absent
    skel = skeleton_score(source, target)

    combined, used_weights = combined_score(
        semantic_score=semantic,
        form_score=form,
        orthography=ort,
        sound=snd,
        skeleton=skel,
        weights=weights,
    )

    # Apply a small multiplicative boost for same-family language pairs
    src_lang = source.get("lang", "") or source.get("language", "")
    tgt_lang = target.get("lang", "") or target.get("language", "")
    family_match = bool(src_lang and tgt_lang and are_same_family(src_lang, tgt_lang))
    if family_match and weights.family_boost > 0:
        combined = min(1.0, combined * (1.0 + weights.family_boost))

    return {
        "components": {
            "orthography": ort,
            "sound": snd,        # null when IPA absent — intentional
            "skeleton": skel,
        },
        "combined_score": round(combined, 4),
        "weights_used": used_weights,
        "family_boost_applied": family_match,
    }

