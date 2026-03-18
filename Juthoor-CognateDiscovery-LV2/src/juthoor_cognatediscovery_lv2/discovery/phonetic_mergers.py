from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PhoneticMergerRule:
    target_lang: str
    arabic_pair: tuple[str, ...]
    merged_to: str | None
    notes: str


_HEB_ARC_BASE_MAP: dict[str, set[str]] = {
    "א": {"ا"},
    "ב": {"ب"},
    "ג": {"ج"},
    "ד": {"د", "ذ"},
    "ה": {"ه", "ح"},
    "ו": {"و"},
    "ז": {"ز", "ظ"},
    "ח": {"ح", "خ"},
    "ט": {"ط", "ت", "ظ"},
    "י": {"ي"},
    "כ": {"ك", "خ"},
    "ך": {"ك", "خ"},
    "ל": {"ل"},
    "מ": {"م"},
    "ם": {"م"},
    "נ": {"ن"},
    "ן": {"ن"},
    "ס": {"س"},
    "ע": {"ع", "غ"},
    "פ": {"ف", "ب"},
    "ף": {"ف", "ب"},
    "צ": {"ص", "ض", "ظ"},
    "ץ": {"ص", "ض", "ظ"},
    "ק": {"ق"},
    "ר": {"ر"},
    "ש": {"ش", "س", "ث"},
    "ת": {"ت", "ط", "ث"},
}

_PERSIAN_BASE_MAP: dict[str, set[str]] = {
    "ا": {"ا", "ع"},
    "آ": {"ا"},
    "ب": {"ب"},
    "پ": {"ب"},
    "ت": {"ت", "ط"},
    "ث": {"ث", "س", "ص"},
    "ج": {"ج"},
    "چ": {"ج"},
    "ح": {"ح", "ه"},
    "خ": {"خ"},
    "د": {"د"},
    "ذ": {"ذ", "ز", "ض", "ظ"},
    "ر": {"ر"},
    "ز": {"ز", "ذ", "ض", "ظ"},
    "ژ": {"ز", "ذ", "ض", "ظ"},
    "س": {"س", "ث", "ص"},
    "ش": {"ش"},
    "ص": {"ص", "س", "ث"},
    "ض": {"ض", "ذ", "ز", "ظ"},
    "ط": {"ط", "ت"},
    "ظ": {"ظ", "ذ", "ز", "ض"},
    "ع": {"ع", "غ", "ا"},
    "غ": {"غ", "ع"},
    "ف": {"ف"},
    "ق": {"ق"},
    "ک": {"ك"},
    "ك": {"ك"},
    "گ": {"ج"},
    "ل": {"ل"},
    "م": {"م"},
    "ن": {"ن"},
    "ه": {"ه", "ح"},
    "و": {"و"},
    "ی": {"ي"},
    "ي": {"ي"},
}

_SCRIPT_TOKEN_RE = re.compile(r"[\u0590-\u05FF\u0600-\u06FFA-Za-z]+")
_ARABIC_LETTER_RE = re.compile(r"[\u0621-\u064A\u067E\u0686\u0698\u06A9\u06AF\u06CC]")
_ARABIC_OVERLAP_EXCLUDE = {"ا", "و", "ي", "ى", "ة", "آ"}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _resource_path() -> Path:
    return _repo_root() / "Juthoor-CognateDiscovery-LV2" / "resources" / "phonetic_mergers.jsonl"


def _norm(value: Any) -> str:
    return " ".join(str(value or "").split()).strip().casefold()


def _norm_lang(code: str) -> str:
    aliases = {"fa": "fas", "fas": "fas", "he": "heb", "heb": "heb", "arc": "arc", "ara": "ara", "ar": "ara"}
    return aliases.get(_norm(code), _norm(code))


def load_phonetic_mergers(path: Path | None = None) -> list[PhoneticMergerRule]:
    path = path or _resource_path()
    rules: list[PhoneticMergerRule] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rec = json.loads(line)
            rules.append(
                PhoneticMergerRule(
                    target_lang=_norm_lang(rec["target_lang"]),
                    arabic_pair=tuple(str(item) for item in rec.get("arabic_pair", []) if item),
                    merged_to=rec.get("merged_to"),
                    notes=str(rec.get("notes", "")),
                )
            )
    return rules


def build_target_to_arabic_map(target_lang: str, rules: list[PhoneticMergerRule] | None = None) -> dict[str, set[str]]:
    lang = _norm_lang(target_lang)
    if lang in {"heb", "arc"}:
        mapping = {key: set(value) for key, value in _HEB_ARC_BASE_MAP.items()}
    elif lang == "fas":
        mapping = {key: set(value) for key, value in _PERSIAN_BASE_MAP.items()}
    else:
        mapping = {}
    for rule in rules or load_phonetic_mergers():
        if rule.target_lang != lang or not rule.merged_to:
            continue
        merged_tokens = [token for token in _SCRIPT_TOKEN_RE.findall(rule.merged_to) if token]
        for token in merged_tokens:
            mapping.setdefault(token, set()).update({item for item in rule.arabic_pair if len(item) == 1 and _ARABIC_LETTER_RE.fullmatch(item)})
    return mapping


def ambiguous_target_chars(target_lang: str, rules: list[PhoneticMergerRule] | None = None) -> set[str]:
    lang = _norm_lang(target_lang)
    out: set[str] = set()
    for rule in rules or load_phonetic_mergers():
        if rule.target_lang != lang or not rule.merged_to:
            continue
        arabic_letters = [item for item in rule.arabic_pair if len(item) == 1 and _ARABIC_LETTER_RE.fullmatch(item)]
        if len(arabic_letters) < 2:
            continue
        merged_tokens = [token for token in _SCRIPT_TOKEN_RE.findall(rule.merged_to) if token]
        out.update(merged_tokens)
    return out


def arabic_letter_set(text: str) -> set[str]:
    return {char for char in text if _ARABIC_LETTER_RE.fullmatch(char) and char not in _ARABIC_OVERLAP_EXCLUDE}


def possible_arabic_letters(target_lang: str, lemma: str, rules: list[PhoneticMergerRule] | None = None) -> set[str]:
    lang = _norm_lang(target_lang)
    if lang == "ara":
        return arabic_letter_set(lemma)
    mapping = build_target_to_arabic_map(lang, rules=rules)
    out: set[str] = set()
    for char in lemma:
        if char in mapping:
            out.update(mapping[char])
    return out


def merger_overlap(source_lang: str, source_lemma: str, target_lang: str, target_lemma: str) -> set[str]:
    if _norm_lang(source_lang) != "ara":
        return set()
    source_letters = arabic_letter_set(source_lemma)
    target_letters = possible_arabic_letters(target_lang, target_lemma)
    return source_letters & target_letters


def has_merger_ambiguity(source_lang: str, source_lemma: str, target_lang: str, target_lemma: str) -> bool:
    return bool(merger_overlap(source_lang, source_lemma, target_lang, target_lemma))
