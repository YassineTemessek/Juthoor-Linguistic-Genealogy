from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any


_ARABIC_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")
_SPACE_RE = re.compile(r"\s+")
_WEAK_RADICALS = set("اويى")
_WEAK_LATIN = {"a", "e", "i", "o", "u", "w", "y"}
_HAMZA_MAP = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ؤ": "و",
        "ئ": "ي",
        "ء": "ا",
    }
)
_CLASS_MAP = {
    "ء": "A", "ا": "A", "أ": "A", "إ": "A", "آ": "A", "ٱ": "A", "ʔ": "A",
    "ه": "H", "ح": "H", "خ": "H", "ḥ": "H", "ḫ": "H", "x": "H", "h": "H",
    "ع": "E", "غ": "E", "ʕ": "E", "ġ": "E", "ɣ": "E",
    "ب": "B", "ف": "B", "پ": "B", "b": "B", "f": "B", "v": "B",
    "م": "M", "m": "M",
    "ت": "T", "ط": "T", "ث": "T", "د": "T", "ض": "T", "ذ": "T", "ظ": "T",
    "t": "T", "ṭ": "T", "d": "T", "ḍ": "T", "ð": "T", "θ": "T", "ẓ": "T",
    "س": "S", "ص": "S", "ز": "S", "ش": "S", "ج": "S", "c": "S", "s": "S",
    "ṣ": "S", "z": "S", "š": "S", "ʃ": "S", "j": "S", "ʒ": "S", "g": "S",
    "ر": "R", "ل": "R", "ن": "R", "r": "R", "l": "R", "n": "R",
    "ك": "K", "ق": "K", "گ": "K", "k": "K", "q": "K", "g̣": "K",
    "و": "W", "ي": "W", "ى": "W", "w": "W", "y": "W",
}
_DISPLAY_MAP = {
    "ء": "ʔ", "ا": "a", "أ": "ʔ", "إ": "ʔ", "آ": "ʔa", "ٱ": "a",
    "ه": "h", "ح": "ḥ", "خ": "kh", "ع": "ʿ", "غ": "gh",
    "ب": "b", "ف": "f", "م": "m",
    "ت": "t", "ط": "ṭ", "ث": "th", "د": "d", "ض": "ḍ", "ذ": "dh", "ظ": "ẓ",
    "س": "s", "ص": "ṣ", "ز": "z", "ش": "sh", "ج": "j",
    "ر": "r", "ل": "l", "ن": "n",
    "ك": "k", "ق": "q", "گ": "g",
    "و": "w", "ي": "y", "ى": "y",
}


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).strip().casefold()
    text = _ARABIC_DIACRITICS_RE.sub("", text)
    text = _SPACE_RE.sub("", text)
    return text


def normalize_hamza(text: str) -> str:
    return _norm(text).translate(_HAMZA_MAP)


def collapse_weak_radicals(text: str) -> str:
    text = normalize_hamza(text)
    out: list[str] = []
    for ch in text:
        if ch in _WEAK_RADICALS or ch in _WEAK_LATIN:
            continue
        out.append(ch)
    return "".join(out)


def literal_skeleton(text: str) -> str:
    text = normalize_hamza(text)
    out: list[str] = []
    for ch in text:
        if not ch.isalpha():
            continue
        if ch in _WEAK_RADICALS or ch in _WEAK_LATIN:
            continue
        out.append(ch)
    return "".join(out)


def correspondence_string(text: str) -> str:
    text = normalize_hamza(text)
    out: list[str] = []
    for ch in text:
        if not ch.isalpha():
            continue
        out.append(_CLASS_MAP.get(ch, ch))
    return "".join(out)


def _display_tokens(text: str) -> list[str]:
    text = literal_skeleton(text)
    return [_DISPLAY_MAP.get(ch, ch) for ch in text]


def display_skeleton(text: str) -> str:
    return "-".join(_display_tokens(text))


def _seq_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return float(SequenceMatcher(None, a, b).ratio())


def best_radical_text(row: dict[str, Any]) -> str:
    return str(
        row.get("root_norm")
        or row.get("root")
        or row.get("translit")
        or row.get("ipa")
        or row.get("lemma")
        or ""
    ).strip()


def explain_correspondence_rules(source: dict[str, Any], target: dict[str, Any]) -> list[str]:
    src = best_radical_text(source)
    tgt = best_radical_text(target)
    notes: list[str] = []
    src_skeleton = display_skeleton(src)
    tgt_skeleton = display_skeleton(tgt)
    if normalize_hamza(src) == normalize_hamza(tgt) and src and tgt and src != tgt:
        notes.append("hamza normalization aligns the forms")
    if collapse_weak_radicals(src) == collapse_weak_radicals(tgt) and src and tgt:
        notes.append("weak-radical reduction produces the same consonant trace")
    src_corr = correspondence_string(src)
    tgt_corr = correspondence_string(tgt)
    if src_corr == tgt_corr and src_corr:
        notes.append(f"shared correspondence class trace: {src_corr}")
    elif _seq_ratio(src_corr, tgt_corr) >= 0.7 and src_corr and tgt_corr:
        notes.append(f"close correspondence class traces: {src_corr} vs {tgt_corr}")
    src_tokens = _display_tokens(src)
    tgt_tokens = _display_tokens(tgt)
    if src_tokens and tgt_tokens and len(src_tokens) == len(tgt_tokens):
        mismatches: list[str] = []
        for left, right in zip(src_tokens, tgt_tokens):
            if left == right:
                continue
            pair = f"{left} ~ {right}"
            if pair not in mismatches:
                mismatches.append(pair)
            if len(mismatches) >= 2:
                break
        if mismatches:
            notes.append("observed rule path: " + ", ".join(mismatches))
    return notes


def correspondence_features(source: dict[str, Any], target: dict[str, Any]) -> dict[str, float]:
    src = best_radical_text(source)
    tgt = best_radical_text(target)
    src_corr = correspondence_string(src)
    tgt_corr = correspondence_string(tgt)
    src_hamza = normalize_hamza(src)
    tgt_hamza = normalize_hamza(tgt)
    src_weak = collapse_weak_radicals(src)
    tgt_weak = collapse_weak_radicals(tgt)
    return {
        "correspondence": round(_seq_ratio(src_corr, tgt_corr), 6),
        "hamza_match": 1.0 if src_hamza and src_hamza == tgt_hamza else 0.0,
        "weak_radical_match": 1.0 if src_weak and src_weak == tgt_weak else 0.0,
    }
