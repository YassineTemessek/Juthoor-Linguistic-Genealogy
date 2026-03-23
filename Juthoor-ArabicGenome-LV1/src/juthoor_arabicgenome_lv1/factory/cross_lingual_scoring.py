from __future__ import annotations

import itertools
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


def target_variants(lemma: str, *, max_variants: int = 64) -> tuple[str, ...]:
    option_lists = [HEBREW_VARIANTS.get(ch, (ch,)) for ch in lemma]
    variants: OrderedDict[str, None] = OrderedDict()
    for combo in itertools.product(*option_lists):
        value = "".join(combo)
        if value:
            variants[value] = None
        if len(variants) >= max_variants:
            break
    return tuple(variants.keys())


def best_similarity(projected_variants: list[str], target_lemma: str) -> tuple[float, str | None]:
    targets = target_variants(target_lemma)
    if not projected_variants or not targets:
        return 0.0, None

    best_score = 0.0
    best_variant: str | None = None
    for projected in projected_variants:
        for target in targets:
            score = SequenceMatcher(a=projected, b=target).ratio()
            if score > best_score:
                best_score = score
                best_variant = target
    return best_score, best_variant


def score_projection_row(row: dict[str, Any]) -> dict[str, Any]:
    projected = list(row.get("projected_variants", ()))
    targets = set(target_variants(row.get("target_lemma", "")))
    best_score, best_variant = best_similarity(projected, row.get("target_lemma", ""))

    exact_hit = any(candidate in targets for candidate in projected)
    binary_prefix_hit = any(
        target[:2] == candidate[:2]
        for target in targets
        for candidate in projected
        if len(target) >= 2 and len(candidate) >= 2
    )

    return {
        **row,
        "target_variants": sorted(targets),
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
