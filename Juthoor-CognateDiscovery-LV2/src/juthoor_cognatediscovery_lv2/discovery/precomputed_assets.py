from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable

try:
    from juthoor_arabicgenome_lv1.factory.sound_laws import normalize_arabic_root, project_root_by_target
except ImportError:
    from .phonetic_law_scorer import normalize_arabic_root, project_root_by_target  # type: ignore[attr-defined]


_CONTENT_POS = {
    "n",
    "noun",
    "v",
    "verb",
    "adj",
    "adjective",
    "adv",
    "adverb",
    "name",
    "proper_noun",
}
_FUNCTION_POS = {
    "pron",
    "pronoun",
    "det",
    "determiner",
    "art",
    "article",
    "prep",
    "preposition",
    "conj",
    "conjunction",
    "part",
    "particle",
    "aux",
    "auxiliary",
    "interj",
    "interjection",
    "character",
    "prefix",
    "suffix",
}
_ASCII_LETTER_RE = re.compile(r"[a-z]+")
_PARENS_RE = re.compile(r"\([^)]*\)")
_IPA_VOWEL_RE = re.compile(r"[aeiouɪɛæʌɒɔʊəɑɜɐɵøœɶɯɤɨʉyˈˌː\.ʔ̃]")
_NON_ALPHA_RE = re.compile(r"[^a-z]+")
_HISTORICAL_PATTERNS = (
    re.compile(r"أصل الكلمة كان يعني\s*[\"“”'()]?\s*([^\"”'\n\.]+)"),
    re.compile(r"كانت تشير إلى\s*[\"“”'()]?\s*([^\"”'\n\.]+)"),
    re.compile(r"كان يدل على\s*[\"“”'()]?\s*([^\"”'\n\.]+)"),
    re.compile(r"كانت تدل على\s*[\"“”'()]?\s*([^\"”'\n\.]+)"),
)


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            yield json.loads(line)


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def _normalize_lemma(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _normalize_pos(values: Any) -> set[str]:
    if values is None:
        return set()
    if isinstance(values, str):
        items = [values]
    else:
        items = [str(item) for item in values]
    normalized: set[str] = set()
    for item in items:
        clean = _NON_ALPHA_RE.sub("_", item.strip().lower()).strip("_")
        if clean:
            normalized.add(clean)
    return normalized


def _is_content_pos(pos_values: set[str]) -> bool:
    return bool(pos_values & _CONTENT_POS)


def _is_function_pos(pos_values: set[str]) -> bool:
    return bool(pos_values & _FUNCTION_POS)


def english_ipa_skeleton(ipa: str) -> str:
    collapsed = _PARENS_RE.sub("", str(ipa or "").strip().lower())
    collapsed = collapsed.replace("/", "").replace("[", "").replace("]", "").replace(",", "")
    return _IPA_VOWEL_RE.sub("", collapsed).strip()


def english_orth_skeleton(word: str) -> str:
    return "".join(ch for ch in str(word or "").strip().lower() if ch in "bcdfghjklmnpqrstvwxyz")


def english_curation_score(row: dict[str, Any]) -> int:
    lemma = _normalize_lemma(row.get("lemma"))
    pos_values = _normalize_pos(row.get("pos"))
    ipa = str(row.get("ipa") or "").strip()
    score = 0

    if ipa:
        score += 8
    if _is_content_pos(pos_values):
        score += 8
    if not _is_function_pos(pos_values):
        score += 3
    if lemma.isalpha():
        score += 4
    if 4 <= len(lemma) <= 12:
        score += 3
    if len(english_orth_skeleton(lemma)) >= 3:
        score += 3

    priority = row.get("source_priority")
    if isinstance(priority, int):
        score += max(0, 4 - priority)

    if "'" in lemma or "-" in lemma or "(" in lemma or ")" in lemma:
        score -= 5
    if any(ch.isdigit() for ch in lemma):
        score -= 8
    if len(lemma) <= 2:
        score -= 8
    if _is_function_pos(pos_values):
        score -= 10

    return score


def curate_english_corpus(
    input_path: Path,
    output_path: Path,
    *,
    max_entries: int = 10_000,
) -> dict[str, Any]:
    best_by_lemma: dict[str, tuple[tuple[Any, ...], dict[str, Any]]] = {}
    scanned = 0
    content_candidates = 0

    for row in _iter_jsonl(input_path):
        scanned += 1
        lemma = _normalize_lemma(row.get("lemma"))
        if not lemma:
            continue

        pos_values = _normalize_pos(row.get("pos"))
        score = english_curation_score(row)
        if _is_content_pos(pos_values):
            content_candidates += 1

        enriched = dict(row)
        enriched["lemma"] = lemma
        enriched["pos"] = sorted(pos_values)
        enriched["curation_score"] = score
        enriched["ipa_skeleton"] = english_ipa_skeleton(str(row.get("ipa") or ""))
        enriched["orth_skeleton"] = english_orth_skeleton(lemma)

        rank_key = (
            score,
            int(_is_content_pos(pos_values)),
            int(bool(str(row.get("ipa") or "").strip())),
            -int(row.get("source_priority", 99)) if isinstance(row.get("source_priority"), int) else -99,
            -len(enriched["orth_skeleton"]),
        )
        previous = best_by_lemma.get(lemma)
        if previous is None or rank_key > previous[0]:
            best_by_lemma[lemma] = (rank_key, enriched)

    ranked = sorted(
        (item[1] for item in best_by_lemma.values()),
        key=lambda row: (
            -int(row["curation_score"]),
            -int(_is_content_pos(set(row.get("pos", [])))),
            -int(bool(row.get("ipa_skeleton"))),
            row["lemma"],
        ),
    )

    selected: list[dict[str, Any]] = []
    for row in ranked:
        pos_values = set(row.get("pos", []))
        if row["curation_score"] < 4:
            continue
        if len(row["lemma"]) < 3:
            continue
        if not row["ipa_skeleton"]:
            continue
        if not _is_content_pos(pos_values):
            continue
        selected.append(row)
        if max_entries and len(selected) >= max_entries:
            break

    written = _write_jsonl(output_path, selected)
    return {
        "input_path": str(input_path),
        "output_path": str(output_path),
        "rows_scanned": scanned,
        "unique_lemmas": len(best_by_lemma),
        "content_candidates": content_candidates,
        "rows_written": written,
    }


def build_reverse_root_index(
    input_path: Path,
    output_path: Path,
    *,
    projector: Callable[[str, str], tuple[str, ...]] | None = None,
) -> dict[str, Any]:
    projector = projector or project_root_by_target
    index: dict[str, dict[str, Any]] = defaultdict(lambda: {"candidates": []})
    roots_seen = 0
    projections_total = 0

    for row in _iter_jsonl(input_path):
        root = normalize_arabic_root(str(row.get("root_norm") or row.get("lemma") or row.get("root") or ""))
        if not root:
            continue
        roots_seen += 1
        variants = projector(root, "european")
        for variant in variants:
            skeleton = english_orth_skeleton(variant)
            if not 2 <= len(skeleton) <= 4:
                continue
            projections_total += 1
            entry = {
                "root": root,
                "projection": variant,
                "binary_root": row.get("binary_root"),
                "meaning_text": row.get("meaning_text") or row.get("gloss_plain") or "",
                "word_count": int(row.get("word_count") or 0),
            }
            index[skeleton]["candidates"].append(entry)

    serializable: dict[str, Any] = {}
    for skeleton, payload in sorted(index.items()):
        deduped: dict[tuple[str, str], dict[str, Any]] = {}
        for candidate in payload["candidates"]:
            key = (candidate["root"], candidate["projection"])
            previous = deduped.get(key)
            if previous is None or candidate["word_count"] > previous["word_count"]:
                deduped[key] = candidate
        ordered = sorted(
            deduped.values(),
            key=lambda item: (-item["word_count"], item["root"], item["projection"]),
        )
        serializable[skeleton] = {
            "candidate_count": len(ordered),
            "candidates": ordered[:64],
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "input_path": str(input_path),
        "output_path": str(output_path),
        "roots_seen": roots_seen,
        "indexed_skeletons": len(serializable),
        "projection_rows": projections_total,
    }


def _extract_historical_phrases(text: str) -> list[str]:
    phrases: list[str] = []
    normalized = " ".join(str(text or "").split())
    for pattern in _HISTORICAL_PATTERNS:
        for match in pattern.findall(normalized):
            phrase = match.strip(" :;،.()[]{}\"'“”")
            if phrase and phrase not in phrases:
                phrases.append(phrase)
    return phrases


def _collect_stage_matches(path: Path) -> dict[str, list[dict[str, str]]]:
    matches: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in _iter_jsonl(path):
        lemma = _normalize_lemma(row.get("lemma"))
        meaning = " ".join(str(row.get("meaning_text") or row.get("gloss_plain") or "").split()).strip()
        ipa = str(row.get("ipa") or "").strip()
        if not lemma or not meaning:
            continue
        if len(matches[lemma]) >= 5:
            continue
        matches[lemma].append({"meaning": meaning, "ipa": ipa})
    return matches


def build_historical_english_lookup(
    beyond_csv_path: Path,
    old_english_path: Path,
    middle_english_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    old_matches = _collect_stage_matches(old_english_path)
    middle_matches = _collect_stage_matches(middle_english_path)

    rows_out: list[dict[str, Any]] = []
    seen_words: set[str] = set()
    scanned = 0

    with beyond_csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            scanned += 1
            lemma = _normalize_lemma(row.get("english_word"))
            if not lemma or lemma in seen_words:
                continue
            seen_words.add(lemma)

            explanation = str(row.get("etymology_explanation") or "")
            extracted = _extract_historical_phrases(explanation)
            rows_out.append(
                {
                    "lemma": lemma,
                    "modern_gloss": " ".join(str(row.get("english_meaning") or "").split()).strip(),
                    "historical_phrases": extracted,
                    "intermediate_langs": " ".join(str(row.get("intermediate_langs") or "").split()).strip(),
                    "confidence": row.get("confidence"),
                    "source_post_id": row.get("source_post_id"),
                    "beyond_name_note": explanation.strip(),
                    "old_english_matches": old_matches.get(lemma, []),
                    "middle_english_matches": middle_matches.get(lemma, []),
                }
            )

    rows_out.sort(
        key=lambda row: (
            -len(row["historical_phrases"]),
            -len(row["old_english_matches"]),
            -len(row["middle_english_matches"]),
            row["lemma"],
        )
    )
    written = _write_jsonl(output_path, rows_out)
    return {
        "input_path": str(beyond_csv_path),
        "output_path": str(output_path),
        "rows_scanned": scanned,
        "rows_written": written,
        "rows_with_historical_phrase": sum(1 for row in rows_out if row["historical_phrases"]),
        "rows_with_old_english_match": sum(1 for row in rows_out if row["old_english_matches"]),
        "rows_with_middle_english_match": sum(1 for row in rows_out if row["middle_english_matches"]),
    }
