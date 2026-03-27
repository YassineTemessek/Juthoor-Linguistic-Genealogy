from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

LV2_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = LV2_ROOT.parent
SRC_ROOT = LV2_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.append(str(SRC_ROOT))

from juthoor_cognatediscovery_lv2.discovery.precomputed_assets import (  # noqa: E402
    english_curation_score,
    english_ipa_skeleton,
    english_orth_skeleton,
)

CANONICAL_MODERN_ENGLISH = (
    REPO_ROOT / "Juthoor-DataCore-LV0" / "data" / "processed" / "english_modern" / "sources" / "kaikki.jsonl"
)
LV2_ENGLISH_IPA = LV2_ROOT / "data" / "processed" / "english" / "english_ipa_merged_pos.jsonl"
BEYOND_NAME_CSV = LV2_ROOT / "data" / "processed" / "beyond_name_etymology_pairs.csv"
REVERSE_ROOT_INDEX = LV2_ROOT / "data" / "processed" / "reverse_arabic_root_index.json"
OUTPUT_PATH = LV2_ROOT / "data" / "processed" / "english" / "english_arabic_candidates.jsonl"

CONTENT_POS = {"n", "noun", "v", "verb", "adj", "adjective", "adv", "adverb", "name", "proper_noun"}
INTERMEDIATE_BORROW_LANGS = {"latin", "french", "spanish", "italian", "greek"}
SCIENCE_MATH_TOKENS = {
    "admiral",
    "algebra",
    "album",
    "algorithm",
    "alchemy",
    "alkali",
    "alembic",
    "alcove",
    "alhazen",
    "alidade",
    "almanac",
    "arsenal",
    "zenith",
    "nadir",
    "azimuth",
    "cipher",
    "zero",
    "sine",
    "tangent",
    "elixir",
    "magazine",
}
SCIENCE_MATH_GLOSS_TOKENS = {
    "science",
    "scientific",
    "mathematics",
    "mathematical",
    "geometry",
    "astronomy",
    "astrology",
    "chemistry",
    "alchemical",
    "number",
    "numeric",
    "calculation",
    "measure",
    "compass",
    "navigation",
    "medicinal",
    "medicine",
    "instrument",
    "laboratory",
}
FOOD_TRADE_TOKENS = {
    "alfalfa",
    "amber",
    "apricot",
    "candy",
    "carafe",
    "carat",
    "carob",
    "coffee",
    "cotton",
    "giraffe",
    "jar",
    "lemon",
    "lime",
    "magazine",
    "mattress",
    "mohair",
    "muslin",
    "orange",
    "saffron",
    "sherbet",
    "sofa",
    "spinach",
    "sugar",
    "syrup",
    "tariff",
    "coffee",
}
FOOD_TRADE_GLOSS_TOKENS = {
    "food",
    "drink",
    "beverage",
    "fruit",
    "spice",
    "seed",
    "sugar",
    "cloth",
    "fabric",
    "textile",
    "cotton",
    "trade",
    "commerce",
    "merchant",
    "cargo",
    "tariff",
    "warehouse",
    "furniture",
    "container",
}
AL_PREFIX_ALLOW = {
    "alarm",
    "album",
    "alcohol",
    "alchemy",
    "alcove",
    "alembic",
    "alfalfa",
    "alfalfa",
    "algorithm",
    "alidade",
    "alkali",
    "alkaline",
    "alkane",
    "alkene",
    "alkyne",
    "allah",
    "almanac",
    "almond",
    "azimuth",
    "alcazar",
    "algebra",
    "alkahest",
    "almucantar",
    "aludel",
    "alizarin",
    "altair",
    "alcoran",
    "alhidade",
    "alidade",
    "alkermes",
    "alcazar",
    "alcade",
}
AL_PREFIX_BLOCK = {
    "albeit",
    "alarmed",
    "alarmist",
    "albums",
    "alder",
    "algae",
    "alias",
    "alibi",
    "alien",
    "align",
    "alive",
    "all",
    "alley",
    "alloy",
    "allow",
    "alone",
    "along",
    "alphabet",
    "already",
    "also",
    "alter",
    "always",
}
STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "for",
    "by",
    "with",
}
NON_ALPHA_RE = re.compile(r"[^a-z]+")
HEURISTIC_ALLOW = AL_PREFIX_ALLOW | SCIENCE_MATH_TOKENS | FOOD_TRADE_TOKENS


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


def _normalize_lemma(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _normalize_pos(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        raw = [values]
    else:
        raw = [str(item) for item in values]
    normalized: set[str] = set()
    for item in raw:
        item = NON_ALPHA_RE.sub("_", item.lower()).strip("_")
        if item:
            normalized.add(item)
    return sorted(normalized)


def _clean_gloss(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _content_pos_score(pos_values: list[str]) -> int:
    pos_set = set(pos_values)
    return int(bool(pos_set & CONTENT_POS))


def _pick_better_ipa(existing: str, candidate: str) -> str:
    candidate = str(candidate or "").strip()
    existing = str(existing or "").strip()
    if not candidate:
        return existing
    if not existing:
        return candidate
    return candidate if len(candidate) > len(existing) else existing


def _pick_better_gloss(existing: str, candidate: str) -> str:
    existing = _clean_gloss(existing)
    candidate = _clean_gloss(candidate)
    if len(candidate) > len(existing):
        return candidate
    return existing


def _load_full_english_corpus(modern_path: Path, ipa_path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    by_lemma: dict[str, dict[str, Any]] = {}
    stats = Counter()

    if modern_path.exists():
        for row in _iter_jsonl(modern_path):
            stats["modern_rows_scanned"] += 1
            lemma = _normalize_lemma(row.get("lemma"))
            if not lemma or len(lemma) < 3:
                continue
            if lemma in STOPWORDS:
                continue
            entry = by_lemma.setdefault(
                lemma,
                {
                    "lemma": lemma,
                    "meaning_text": "",
                    "ipa": "",
                    "pos": set(),
                    "sources": set(),
                    "source_priority": 99,
                },
            )
            entry["meaning_text"] = _pick_better_gloss(entry["meaning_text"], row.get("gloss_plain") or row.get("meaning_text") or "")
            entry["ipa"] = _pick_better_ipa(entry["ipa"], row.get("ipa"))
            entry["pos"].update(_normalize_pos(row.get("pos")))
            entry["sources"].add("lv0_kaikki")

    if ipa_path.exists():
        for row in _iter_jsonl(ipa_path):
            stats["ipa_rows_scanned"] += 1
            lemma = _normalize_lemma(row.get("lemma"))
            if not lemma or len(lemma) < 3:
                continue
            if lemma in STOPWORDS:
                continue
            entry = by_lemma.setdefault(
                lemma,
                {
                    "lemma": lemma,
                    "meaning_text": "",
                    "ipa": "",
                    "pos": set(),
                    "sources": set(),
                    "source_priority": 99,
                },
            )
            entry["meaning_text"] = _pick_better_gloss(entry["meaning_text"], row.get("meaning_text") or "")
            entry["ipa"] = _pick_better_ipa(entry["ipa"], row.get("ipa"))
            entry["pos"].update(_normalize_pos(row.get("pos")))
            priority = row.get("source_priority")
            if isinstance(priority, int):
                entry["source_priority"] = min(entry["source_priority"], priority)
            entry["sources"].add("lv2_ipa")

    finalized: dict[str, dict[str, Any]] = {}
    for lemma, row in by_lemma.items():
        merged = {
            "lemma": lemma,
            "meaning_text": row["meaning_text"],
            "ipa": row["ipa"],
            "pos": sorted(row["pos"]),
            "sources": sorted(row["sources"]),
            "source_priority": row["source_priority"],
        }
        merged["orth_skeleton"] = english_orth_skeleton(lemma)
        merged["ipa_skeleton"] = english_ipa_skeleton(merged["ipa"])
        merged["curation_score"] = english_curation_score(merged)
        finalized[lemma] = merged

    stats["unique_lemmas"] = len(finalized)
    return finalized, dict(stats)


def _split_langs(value: Any) -> list[str]:
    parts = []
    for item in str(value or "").split(","):
        item = " ".join(item.split())
        if item:
            parts.append(item)
    return parts


def _load_beyond_name(path: Path) -> tuple[dict[str, dict[str, Any]], Counter]:
    evidence: dict[str, dict[str, Any]] = {}
    stats: Counter = Counter()
    unique_english_words: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            stats["rows_scanned"] += 1
            lemma = _normalize_lemma(row.get("english_word"))
            if not lemma:
                continue
            intermediate_langs = _split_langs(row.get("intermediate_langs"))
            lang_names = [lang.lower() for lang in intermediate_langs]
            has_chain = any(lang in INTERMEDIATE_BORROW_LANGS for lang in lang_names)
            payload = evidence.setdefault(
                lemma,
                {
                    "english_meaning": "",
                    "arabic_roots": set(),
                    "arabic_translit": set(),
                    "arabic_meanings": set(),
                    "intermediate_langs": set(),
                    "source_post_ids": set(),
                    "entry_types": set(),
                    "max_confidence": 0.0,
                    "known_arabic_etymology": False,
                    "borrowed_via_intermediate_lang": False,
                },
            )
            payload["english_meaning"] = _pick_better_gloss(payload["english_meaning"], row.get("english_meaning") or "")
            root = _normalize_lemma(row.get("arabic_root"))
            if root:
                payload["arabic_roots"].add(root)
            translit = _clean_gloss(row.get("arabic_translit"))
            if translit:
                payload["arabic_translit"].add(translit)
            arabic_meaning = _clean_gloss(row.get("arabic_meaning"))
            if arabic_meaning:
                payload["arabic_meanings"].add(arabic_meaning)
            payload["intermediate_langs"].update(intermediate_langs)
            if row.get("source_post_id"):
                payload["source_post_ids"].add(str(row["source_post_id"]))
            if row.get("entry_type"):
                payload["entry_types"].add(str(row["entry_type"]))
            try:
                payload["max_confidence"] = max(payload["max_confidence"], float(row.get("confidence") or 0.0))
            except ValueError:
                pass
            payload["known_arabic_etymology"] = True
            payload["borrowed_via_intermediate_lang"] = payload["borrowed_via_intermediate_lang"] or has_chain
            unique_english_words.add(lemma)
            if has_chain:
                stats["with_intermediate_chain"] += 1

    normalized: dict[str, dict[str, Any]] = {}
    for lemma, row in evidence.items():
        normalized[lemma] = {
            "english_meaning": row["english_meaning"],
            "arabic_roots": sorted(row["arabic_roots"]),
            "arabic_translit": sorted(row["arabic_translit"]),
            "arabic_meanings": sorted(row["arabic_meanings"]),
            "intermediate_langs": sorted(row["intermediate_langs"]),
            "source_post_ids": sorted(row["source_post_ids"]),
            "entry_types": sorted(row["entry_types"]),
            "max_confidence": row["max_confidence"],
            "known_arabic_etymology": row["known_arabic_etymology"],
            "borrowed_via_intermediate_lang": row["borrowed_via_intermediate_lang"],
        }
    stats["unique_english_words"] = len(unique_english_words)
    return normalized, stats


def _load_reverse_root_index(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _has_keyword(text: str, keywords: set[str]) -> bool:
    haystack = f" {text.lower()} "
    return any(f" {keyword} " in haystack for keyword in keywords)


def _is_al_prefix_candidate(lemma: str) -> bool:
    if lemma in AL_PREFIX_ALLOW:
        return True
    if lemma in AL_PREFIX_BLOCK:
        return False
    if not lemma.startswith("al") or len(lemma) < 5:
        return False
    if not lemma.isalpha():
        return False
    if lemma[2] in "aeiou":
        return False
    return True


def _reverse_root_matches(orth_skeleton: str, reverse_index: dict[str, Any]) -> list[dict[str, Any]]:
    if len(orth_skeleton) < 3:
        return []
    payload = reverse_index.get(orth_skeleton)
    if not payload:
        return []
    candidate_count = int(payload.get("candidate_count") or 0)
    if candidate_count <= 0 or candidate_count > 24:
        return []
    candidates = payload.get("candidates") or []
    strong = []
    for candidate in candidates[:5]:
        if int(candidate.get("word_count") or 0) < 3:
            continue
        strong.append(
            {
                "root": candidate.get("root", ""),
                "projection": candidate.get("projection", ""),
                "word_count": int(candidate.get("word_count") or 0),
                "meaning_text": _clean_gloss(candidate.get("meaning_text") or ""),
            }
        )
    return strong


def _candidate_categories(
    row: dict[str, Any],
    seed_evidence: dict[str, Any] | None,
    reverse_index: dict[str, Any],
) -> tuple[list[str], int, dict[str, Any]]:
    categories: list[str] = []
    score = 0
    support: dict[str, Any] = {}
    lemma = row["lemma"]
    gloss = _clean_gloss(row.get("meaning_text") or "")

    if seed_evidence:
        categories.append("known_arabic_etymology")
        score += 12
        support["beyond_name"] = seed_evidence
        if seed_evidence.get("borrowed_via_intermediate_lang"):
            categories.append("borrowed_via_intermediate_lang")
            score += 4

    if _is_al_prefix_candidate(lemma):
        categories.append("al_prefix")
        score += 3

    root_matches = _reverse_root_matches(row.get("orth_skeleton") or "", reverse_index)
    if root_matches and (seed_evidence is not None or lemma in HEURISTIC_ALLOW):
        categories.append("arabic_root_pattern")
        score += 4
        support["reverse_root_matches"] = root_matches

    if lemma in SCIENCE_MATH_TOKENS or (seed_evidence and _has_keyword(gloss, SCIENCE_MATH_GLOSS_TOKENS)):
        categories.append("scientific_mathematical")
        score += 3

    if lemma in FOOD_TRADE_TOKENS or (seed_evidence and _has_keyword(gloss, FOOD_TRADE_GLOSS_TOKENS)):
        categories.append("food_trade")
        score += 3

    if len(set(categories) - {"known_arabic_etymology"}) >= 2:
        score += 2

    return categories, score, support


def _should_keep_candidate(row: dict[str, Any], categories: list[str], score: int) -> bool:
    if not row["lemma"].isalpha():
        return False
    if len(row["lemma"]) < 3:
        return False
    if row["curation_score"] < 4:
        return False
    if not _content_pos_score(row.get("pos", [])):
        return False
    if "known_arabic_etymology" in categories:
        return True
    heuristic_categories = set(categories)
    primary_heuristics = heuristic_categories & {"al_prefix", "scientific_mathematical", "food_trade"}
    if not primary_heuristics:
        return False
    if row["lemma"] not in HEURISTIC_ALLOW:
        return False
    if "arabic_root_pattern" not in heuristic_categories and len(heuristic_categories) < 2:
        return False
    return score >= 7 and len(heuristic_categories) >= 2


def extract_candidates(
    *,
    modern_english_path: Path,
    english_ipa_path: Path,
    beyond_name_path: Path,
    reverse_root_index_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    english_rows, english_stats = _load_full_english_corpus(modern_english_path, english_ipa_path)
    beyond_name, beyond_stats = _load_beyond_name(beyond_name_path)
    reverse_index = _load_reverse_root_index(reverse_root_index_path)

    rows_out: list[dict[str, Any]] = []
    category_counts: Counter = Counter()
    multi_category = 0

    for lemma, row in english_rows.items():
        seed_evidence = beyond_name.get(lemma)
        categories, score, support = _candidate_categories(row, seed_evidence, reverse_index)
        if not categories:
            continue
        if not _should_keep_candidate(row, categories, score):
            continue

        if len(categories) > 1:
            multi_category += 1
        category_counts.update(categories)

        output_row = {
            "lemma": lemma,
            "ipa": row.get("ipa", ""),
            "pos": row.get("pos", []),
            "meaning_text": row.get("meaning_text", ""),
            "orth_skeleton": row.get("orth_skeleton", ""),
            "ipa_skeleton": row.get("ipa_skeleton", ""),
            "curation_score": row.get("curation_score", 0),
            "candidate_score": score,
            "matched_categories": categories,
            "sources": row.get("sources", []),
        }
        output_row.update(support)
        rows_out.append(output_row)

    rows_out.sort(
        key=lambda row: (
            -int("known_arabic_etymology" in row["matched_categories"]),
            -row["candidate_score"],
            -len(row["matched_categories"]),
            row["lemma"],
        )
    )
    written = _write_jsonl(output_path, rows_out)

    return {
        "modern_english_path": str(modern_english_path),
        "english_ipa_path": str(english_ipa_path),
        "beyond_name_path": str(beyond_name_path),
        "reverse_root_index_path": str(reverse_root_index_path),
        "output_path": str(output_path),
        "english_corpus_stats": english_stats,
        "beyond_name_stats": dict(beyond_stats),
        "rows_written": written,
        "multi_category_candidates": multi_category,
        "category_counts": dict(sorted(category_counts.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract a curated list of English words most likely to have Arabic origins."
    )
    parser.add_argument("--modern-english", type=Path, default=CANONICAL_MODERN_ENGLISH)
    parser.add_argument("--english-ipa", type=Path, default=LV2_ENGLISH_IPA)
    parser.add_argument("--beyond-name", type=Path, default=BEYOND_NAME_CSV)
    parser.add_argument("--reverse-root-index", type=Path, default=REVERSE_ROOT_INDEX)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    summary = extract_candidates(
        modern_english_path=args.modern_english,
        english_ipa_path=args.english_ipa,
        beyond_name_path=args.beyond_name,
        reverse_root_index_path=args.reverse_root_index,
        output_path=args.output,
    )

    print("=== ENGLISH ARABIC CANDIDATE EXTRACTION ===")
    print(f"Modern English rows scanned: {summary['english_corpus_stats'].get('modern_rows_scanned', 0)}")
    print(f"LV2 IPA rows scanned      : {summary['english_corpus_stats'].get('ipa_rows_scanned', 0)}")
    print(f"Unique English lemmas     : {summary['english_corpus_stats'].get('unique_lemmas', 0)}")
    print(f"Beyond the Name rows      : {summary['beyond_name_stats'].get('rows_scanned', 0)}")
    print(f"Known Arabic-origin seeds : {summary['beyond_name_stats'].get('unique_english_words', 0)}")
    print(f"Candidates written        : {summary['rows_written']}")
    print(f"Multi-category candidates : {summary['multi_category_candidates']}")
    print()
    print("Per-category counts:")
    for category, count in summary["category_counts"].items():
        print(f"  {category:28s} {count}")
    print()
    print(f"Output: {summary['output_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
