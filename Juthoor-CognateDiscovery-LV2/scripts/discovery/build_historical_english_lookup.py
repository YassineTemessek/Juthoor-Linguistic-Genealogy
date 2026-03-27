from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[3]
LV2_ROOT = REPO_ROOT / "Juthoor-CognateDiscovery-LV2"

_NON_LETTER_RE = re.compile(r"[^a-z ]+")
_WHITESPACE_RE = re.compile(r"\s+")
_WORD_RE = re.compile(r"[a-z]+(?:[ -][a-z]+){0,2}")
_POS_CONTENT = {
    "noun",
    "verb",
    "adjective",
    "adverb",
    "proper_noun",
    "name",
}
_POS_FUNCTION = {
    "pronoun",
    "determiner",
    "article",
    "preposition",
    "conjunction",
    "particle",
    "auxiliary",
    "interjection",
    "prefix",
    "suffix",
    "character",
}
_META_PREFIXES = (
    "abbreviation of",
    "alternative form of",
    "alternative spelling of",
    "aphetic form of",
    "contracted form of",
    "inflection of",
    "plural of",
    "singular of",
    "genitive of",
    "dative of",
    "accusative of",
    "nominative of",
    "vocative of",
    "comparative of",
    "superlative of",
    "past tense of",
    "past participle of",
    "present participle of",
    "obsolete form of",
    "misspelling of",
    "clipping of",
    "short for",
)
_META_CONTAINS = (
    " indicative of ",
    " subjunctive of ",
    " imperative of ",
    " participle of ",
    " form of ",
)
_STOP_LEMMAS = {
    "a",
    "an",
    "the",
    "this",
    "that",
    "these",
    "those",
    "someone",
    "something",
    "one",
    "ones",
}
_HEAD_BREAKERS = {"of", "for", "to", "in", "on", "with", "from", "by", "at", "as"}


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def _normalize_spaces(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def _normalize_pos(values: Any) -> set[str]:
    if values is None:
        return set()
    if isinstance(values, str):
        items = [values]
    else:
        items = [str(value) for value in values]
    normalized: set[str] = set()
    for item in items:
        value = _normalize_spaces(item.lower())
        value = value.replace("-", "_").replace(" ", "_")
        if value:
            normalized.add(value)
    return normalized


def _normalize_modern_lemma(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().replace("-", " ")
    value = _NON_LETTER_RE.sub(" ", value)
    value = _normalize_spaces(value)
    return value


def _clean_gloss(text: str) -> str:
    value = _normalize_spaces(str(text or ""))
    value = re.sub(r"\([^)]*\)", "", value)
    value = value.replace("“", "").replace("”", "").replace('"', "")
    return _normalize_spaces(value)


def _extract_modern_lemma(row: dict[str, Any]) -> str:
    gloss = _clean_gloss(str(row.get("gloss_plain") or row.get("meaning_text") or ""))
    if not gloss:
        return ""

    lowered = f" {gloss.lower()} "
    if lowered.strip().startswith(_META_PREFIXES):
        return ""
    if any(marker in lowered for marker in _META_CONTAINS):
        return ""

    candidate = gloss.lower()
    candidate = re.sub(r"^(to|a|an|the)\s+", "", candidate)
    candidate = re.split(r"[;,/:]", candidate, maxsplit=1)[0]
    candidate = re.split(r"\.\s*", candidate, maxsplit=1)[0]
    candidate = _normalize_modern_lemma(candidate)
    if not candidate or candidate in _STOP_LEMMAS:
        return ""

    words = candidate.split()
    for index, word in enumerate(words[1:], start=1):
        if word in _HEAD_BREAKERS:
            candidate = " ".join(words[:index])
            words = candidate.split()
            break

    match = _WORD_RE.fullmatch(candidate)
    if not match:
        return ""
    if len(words) > 3 or any(len(word) == 1 for word in words):
        return ""
    return candidate


def _historical_score(row: dict[str, Any], modern_lemma: str) -> tuple[int, ...]:
    lemma = str(row.get("lemma") or "").strip()
    lemma_norm = _normalize_modern_lemma(lemma)
    ipa = str(row.get("ipa") or "").strip()
    pos_values = _normalize_pos(row.get("pos"))
    score = 0

    if row.get("lemma_status") == "attested":
        score += 5
    if pos_values & _POS_CONTENT:
        score += 5
    if not (pos_values & _POS_FUNCTION):
        score += 2
    if ipa:
        score += 3
    if modern_lemma == lemma_norm:
        score += 6
    if len(lemma) >= 3:
        score += 1

    return (
        score,
        int(bool(ipa)),
        int(modern_lemma == lemma_norm),
        -len(lemma),
        lemma,
    )


def _best_stage_forms(path: Path) -> tuple[dict[str, dict[str, str]], dict[str, int]]:
    best_by_modern: dict[str, tuple[tuple[int, ...], dict[str, str]]] = {}
    stats = {
        "rows_scanned": 0,
        "rows_with_modern_lemma": 0,
        "unique_modern_lemmas": 0,
    }

    for row in _iter_jsonl(path):
        stats["rows_scanned"] += 1
        modern_lemma = _extract_modern_lemma(row)
        if not modern_lemma:
            continue

        stats["rows_with_modern_lemma"] += 1
        candidate = {
            "modern_lemma": modern_lemma,
            "historical_form": str(row.get("lemma") or "").strip(),
            "ipa": str(row.get("ipa") or "").strip(),
        }
        rank = _historical_score(row, modern_lemma)
        previous = best_by_modern.get(modern_lemma)
        if previous is None or rank > previous[0]:
            best_by_modern[modern_lemma] = (rank, candidate)

    stats["unique_modern_lemmas"] = len(best_by_modern)
    return {lemma: payload for lemma, (_, payload) in best_by_modern.items()}, stats


def build_historical_english_lookup(
    old_english_path: Path,
    middle_english_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    old_best, old_stats = _best_stage_forms(old_english_path)
    middle_best, middle_stats = _best_stage_forms(middle_english_path)

    modern_lemmas = sorted(set(old_best) | set(middle_best))
    rows_out: list[dict[str, str]] = []
    for modern_lemma in modern_lemmas:
        old_row = old_best.get(modern_lemma)
        middle_row = middle_best.get(modern_lemma)
        rows_out.append(
            {
                "modern_lemma": modern_lemma,
                "old_english_form": old_row["historical_form"] if old_row else "",
                "middle_english_form": middle_row["historical_form"] if middle_row else "",
                "ipa": (middle_row or old_row or {}).get("ipa", ""),
            }
        )

    written = _write_jsonl(output_path, rows_out)
    return {
        "old_english_path": str(old_english_path),
        "middle_english_path": str(middle_english_path),
        "output_path": str(output_path),
        "rows_written": written,
        "rows_with_old_english_form": sum(1 for row in rows_out if row["old_english_form"]),
        "rows_with_middle_english_form": sum(1 for row in rows_out if row["middle_english_form"]),
        "old_english_stats": old_stats,
        "middle_english_stats": middle_stats,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a modern English to Old/Middle English lookup from Kaikki corpora.")
    parser.add_argument(
        "--old-english",
        type=Path,
        default=REPO_ROOT / "Juthoor-DataCore-LV0" / "data" / "processed" / "english_old" / "sources" / "kaikki.jsonl",
    )
    parser.add_argument(
        "--middle-english",
        type=Path,
        default=REPO_ROOT / "Juthoor-DataCore-LV0" / "data" / "processed" / "english_middle" / "sources" / "kaikki.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=LV2_ROOT / "data" / "processed" / "english" / "historical_variants.jsonl",
    )
    args = parser.parse_args()

    summary = build_historical_english_lookup(
        args.old_english,
        args.middle_english,
        args.output,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
