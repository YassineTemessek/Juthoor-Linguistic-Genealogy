from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any


_ARABIC_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")
_SPACE_RE = re.compile(r"\s+")
_WEAK_RADICALS = set("اويى")
_WEAK_LATIN = {"a", "i", "u", "w", "y"}
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


def correspondence_string(text: str) -> str:
    text = normalize_hamza(text)
    out: list[str] = []
    for ch in text:
        if not ch.isalpha():
            continue
        out.append(_CLASS_MAP.get(ch, ch))
    return "".join(out)


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
