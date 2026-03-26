"""Similarity scoring utilities for projected cross-lingual lemmas.

This module normalizes target spellings, expands script-specific variants, and
scores benchmark projection rows against the generated LV1 candidates.
"""

from __future__ import annotations

import itertools
import re
import unicodedata
from collections import OrderedDict
from difflib import SequenceMatcher
from typing import Any


HEBREW_VARIANTS: dict[str, tuple[str, ...]] = {
    "א": ("a", ""),
    "ב": ("b", "v"),
    "ג": ("g",),
    "ד": ("d",),
    "ה": ("h",),
    "ו": ("w", "v", "u", "o"),
    "ז": ("z",),
    "ח": ("ḥ", "h"),
    "ט": ("ṭ", "t"),
    "י": ("y", "i"),
    "כ": ("k", "c", "kh"),
    "ך": ("k", "c", "kh"),
    "ל": ("l",),
    "מ": ("m",),
    "ם": ("m",),
    "נ": ("n",),
    "ן": ("n",),
    "ס": ("s",),
    "ע": ("ʕ", "a", ""),
    "פ": ("p", "f"),
    "ף": ("p", "f"),
    "צ": ("ṣ", "s"),
    "ץ": ("ṣ", "s"),
    "ק": ("q", "k", "c"),
    "ר": ("r",),
    "ש": ("sh", "s"),
    "ת": ("t",),
}

LATIN_FAMILY_TARGETS = {"eng", "lat", "grc"}
LATIN_DIACRITIC_RE = re.compile(r"[^a-z]")
PROJECTION_NORMALIZE_MAP = str.maketrans(
    {
        "ḥ": "h",
        "ṭ": "t",
        "ṣ": "s",
        "ḍ": "d",
        "ẓ": "z",
        "ʕ": "",
    }
)
LATIN_REPLACEMENTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ph", ("ph", "f")),
    ("qu", ("qu", "k", "q", "c")),
    ("ck", ("ck", "k")),
    ("ch", ("ch", "k", "c", "h", "sh")),
    ("gh", ("gh", "g", "h", "")),
    ("th", ("th", "t")),
    ("sh", ("sh", "s")),
    ("j", ("j", "g", "y")),
    ("c", ("c", "k")),
)


def _dedupe_preserve_order(values: list[str]) -> tuple[str, ...]:
    ordered: OrderedDict[str, None] = OrderedDict()
    for value in values:
        if value:
            ordered[value] = None
    return tuple(ordered.keys())


def _collapse_doubles(text: str) -> str:
    if not text:
        return text
    out = [text[0]]
    for ch in text[1:]:
        if ch != out[-1]:
            out.append(ch)
    return "".join(out)


def _strip_vowels(text: str) -> str:
    return "".join(ch for ch in text if ch not in "aeiouy")


def normalize_latin_script(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.translate(PROJECTION_NORMALIZE_MAP)
    return LATIN_DIACRITIC_RE.sub("", normalized)


def hebrew_target_variants(lemma: str, *, max_variants: int = 64) -> tuple[str, ...]:
    option_lists = [HEBREW_VARIANTS.get(ch, (ch,)) for ch in lemma]
    variants: OrderedDict[str, None] = OrderedDict()
    for combo in itertools.product(*option_lists):
        value = "".join(combo)
        if value:
            variants[value] = None
        if len(variants) >= max_variants:
            break
    return tuple(variants.keys())


def latin_target_variants(lemma: str, *, max_variants: int = 64) -> tuple[str, ...]:
    base = normalize_latin_script(lemma)
    if not base:
        return ()

    variants: OrderedDict[str, None] = OrderedDict()
    queue: list[str] = [base]
    while queue and len(variants) < max_variants:
        current = queue.pop(0)
        if not current or current in variants:
            continue
        variants[current] = None
        collapsed = _collapse_doubles(current)
        stripped = _strip_vowels(current)
        if collapsed and collapsed not in variants:
            queue.append(collapsed)
        if stripped and stripped not in variants:
            queue.append(stripped)
        for source, replacements in LATIN_REPLACEMENTS:
            if source not in current:
                continue
            for replacement in replacements:
                candidate = current.replace(source, replacement)
                if candidate and candidate not in variants:
                    queue.append(candidate)
    return tuple(variants.keys())


def target_variants(lemma: str, *, target_lang: str = "heb", max_variants: int = 64) -> tuple[str, ...]:
    if target_lang in {"heb", "arc"}:
        return hebrew_target_variants(lemma, max_variants=max_variants)
    if target_lang in LATIN_FAMILY_TARGETS:
        return latin_target_variants(lemma, max_variants=max_variants)
    normalized = normalize_latin_script(lemma)
    return (normalized,) if normalized else ()


def _normalized_projected_variants(projected_variants: list[str], target_lang: str) -> tuple[str, ...]:
    if target_lang in {"heb", "arc"}:
        return _dedupe_preserve_order(projected_variants)

    expanded: list[str] = []
    for variant in projected_variants:
        normalized = normalize_latin_script(variant)
        if not normalized:
            continue
        expanded.append(normalized)
        collapsed = _collapse_doubles(normalized)
        stripped = _strip_vowels(normalized)
        if collapsed:
            expanded.append(collapsed)
        if stripped:
            expanded.append(stripped)
    return _dedupe_preserve_order(expanded)


def best_similarity(
    projected_variants: list[str],
    target_lemma: str,
    *,
    target_lang: str = "heb",
) -> tuple[float, str | None]:
    normalized_projected = _normalized_projected_variants(projected_variants, target_lang)
    targets = target_variants(target_lemma, target_lang=target_lang)
    if not normalized_projected or not targets:
        return 0.0, None

    best_score = 0.0
    best_variant: str | None = None
    for projected in normalized_projected:
        for target in targets:
            score = SequenceMatcher(a=projected, b=target).ratio()
            if score > best_score:
                best_score = score
                best_variant = target
    return best_score, best_variant


def score_projection_row(row: dict[str, Any]) -> dict[str, Any]:
    target_lang = row.get("target_lang", "heb")
    projected = list(row.get("projected_variants", ()))
    normalized_projected = set(_normalized_projected_variants(projected, target_lang))
    targets = set(target_variants(row.get("target_lemma", ""), target_lang=target_lang))
    best_score, best_variant = best_similarity(projected, row.get("target_lemma", ""), target_lang=target_lang)

    exact_hit = any(candidate in targets for candidate in normalized_projected)
    binary_prefix_hit = any(
        target[:2] == candidate[:2]
        for target in targets
        for candidate in normalized_projected
        if len(target) >= 2 and len(candidate) >= 2
    )

    return {
        **row,
        "target_variants": sorted(targets),
        "normalized_projected_variants": sorted(normalized_projected),
        "exact_projection_hit": exact_hit,
        "binary_prefix_hit": binary_prefix_hit,
        "best_target_variant": best_variant,
        "best_projection_similarity": round(best_score, 6),
    }


def summarize_projection_scores(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    exact_hits = sum(1 for row in rows if row.get("exact_projection_hit"))
    binary_hits = sum(1 for row in rows if row.get("binary_prefix_hit"))
    mean_similarity = (
        sum(float(row.get("best_projection_similarity", 0.0)) for row in rows) / total
        if total
        else 0.0
    )

    by_lang: dict[str, dict[str, float | int]] = {}
    for lang in sorted({row.get("target_lang") for row in rows}):
        lang_rows = [row for row in rows if row.get("target_lang") == lang]
        count = len(lang_rows)
        lang_exact = sum(1 for row in lang_rows if row.get("exact_projection_hit"))
        lang_binary = sum(1 for row in lang_rows if row.get("binary_prefix_hit"))
        by_lang[lang] = {
            "count": count,
            "exact_hits": lang_exact,
            "exact_hit_rate": round(lang_exact / count, 6) if count else 0.0,
            "binary_hits": lang_binary,
            "binary_hit_rate": round(lang_binary / count, 6) if count else 0.0,
            "mean_similarity": round(
                sum(float(row.get("best_projection_similarity", 0.0)) for row in lang_rows) / count,
                6,
            ) if count else 0.0,
        }

    return {
        "rows": total,
        "exact_hits": exact_hits,
        "exact_hit_rate": round(exact_hits / total, 6) if total else 0.0,
        "binary_hits": binary_hits,
        "binary_hit_rate": round(binary_hits / total, 6) if total else 0.0,
        "mean_similarity": round(mean_similarity, 6),
        "by_target_lang": by_lang,
    }
