from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

LV2_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = LV2_ROOT.parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUTPUT_LOOKUP_PATH = LV2_ROOT / "data/processed/arabic/arabic_english_glosses.json"
UNIFIED_ARABIC_PATH = LV2_ROOT / "data/processed/arabic/unified_arabic_discovery.jsonl"
GOLD_PATH = LV2_ROOT / "resources/benchmarks/cognate_gold.jsonl"
BTN_PATH = LV2_ROOT / "data/processed/beyond_name_etymology_pairs.csv"
CONCEPT_CANDIDATE_PATHS = (
    LV2_ROOT / "data/processed/concepts/concepts_v3_2_enriched.jsonl",
    LV2_ROOT / "resources/concepts/concepts_v3_2_enriched.jsonl",
)
WIKTIONARY_SAMPLE_GLOB = "*Arabic-English*_sample.jsonl"

_ARABIC_DIACRITICS = {
    "\u0610",
    "\u0611",
    "\u0612",
    "\u0613",
    "\u0614",
    "\u0615",
    "\u0616",
    "\u0617",
    "\u0618",
    "\u0619",
    "\u061A",
    "\u064B",
    "\u064C",
    "\u064D",
    "\u064E",
    "\u064F",
    "\u0650",
    "\u0651",
    "\u0652",
    "\u0653",
    "\u0654",
    "\u0655",
    "\u0656",
    "\u0657",
    "\u0658",
    "\u0659",
    "\u065A",
    "\u065B",
    "\u065C",
    "\u065D",
    "\u065E",
    "\u065F",
    "\u0670",
    "\u06D6",
    "\u06D7",
    "\u06D8",
    "\u06D9",
    "\u06DA",
    "\u06DB",
    "\u06DC",
    "\u06DF",
    "\u06E0",
    "\u06E1",
    "\u06E2",
    "\u06E3",
    "\u06E4",
    "\u06E7",
    "\u06E8",
    "\u06EA",
    "\u06EB",
    "\u06EC",
    "\u06ED",
}
_WHITESPACE_RE = re.compile(r"\s+")
_NON_GLOSS_CHARS_RE = re.compile(r"[^a-z0-9' -]+")
_LEADING_POS_RE = re.compile(
    r"^(?:noun|verb|adj|adjective|adv|adverb|prep|preposition|pron|pronoun|"
    r"particle|conjunction|interjection|proper noun|name)\s+",
    flags=re.IGNORECASE,
)
_SPLIT_GLOSS_RE = re.compile(r"[;/]|,\s*(?=[A-Za-z])")
_ARABIC_SCRIPT_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def normalize_spaces(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def contains_arabic_script(text: str) -> bool:
    return bool(_ARABIC_SCRIPT_RE.search(text or ""))


def normalize_arabic(text: str) -> str:
    value = unicodedata.normalize("NFKC", str(text or ""))
    value = "".join(ch for ch in value if ch not in _ARABIC_DIACRITICS)
    value = value.replace("ـ", "")
    value = (
        value.replace("ٱ", "ا")
        .replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("ى", "ي")
        .replace("ؤ", "و")
        .replace("ئ", "ي")
    )
    return normalize_spaces(value)


def normalize_english_gloss(text: str) -> str:
    value = unicodedata.normalize("NFKC", str(text or ""))
    value = value.replace("’", "'").replace("`", "'")
    value = value.replace("&", " and ")
    value = re.sub(r"\([^)]*\)", " ", value)
    value = _LEADING_POS_RE.sub("", value)
    value = value.lower()
    value = re.sub(r"\bto\s+", "", value)
    value = _NON_GLOSS_CHARS_RE.sub(" ", value)
    value = normalize_spaces(value)
    return value.strip(" -'")


def extract_glosses(raw_text: str) -> list[str]:
    text = normalize_spaces(str(raw_text or ""))
    if not text:
        return []

    candidates: list[str] = []
    for part in _SPLIT_GLOSS_RE.split(text):
        gloss = normalize_english_gloss(part)
        if not gloss:
            continue
        if len(gloss) <= 1:
            continue
        if gloss in {"and", "or"}:
            continue
        candidates.append(gloss)

    deduped: list[str] = []
    seen: set[str] = set()
    for gloss in candidates:
        if gloss not in seen:
            deduped.append(gloss)
            seen.add(gloss)
    return deduped


class GlossAccumulator:
    def __init__(self) -> None:
        self._glosses_by_term: dict[str, list[str]] = defaultdict(list)
        self._sources_by_term: dict[str, set[str]] = defaultdict(set)
        self._normalized_to_terms: dict[str, set[str]] = defaultdict(set)

    def add(self, term: str, glosses: Iterable[str], source: str) -> bool:
        term = normalize_spaces(str(term or ""))
        if not term or not contains_arabic_script(term):
            return False

        normalized_term = normalize_arabic(term)
        if not normalized_term:
            return False

        added = False
        bucket = self._glosses_by_term[term]
        existing = set(bucket)
        for gloss in glosses:
            normalized_gloss = normalize_english_gloss(gloss)
            if not normalized_gloss or normalized_gloss in existing:
                continue
            bucket.append(normalized_gloss)
            existing.add(normalized_gloss)
            added = True

        if bucket:
            self._sources_by_term[term].add(source)
            self._normalized_to_terms[normalized_term].add(term)
        return added

    def resolve(self, term: str) -> dict[str, Any] | None:
        exact = self._build_entry(term)
        if exact:
            return exact

        normalized_term = normalize_arabic(term)
        if not normalized_term:
            return None

        merged_glosses: list[str] = []
        seen_glosses: set[str] = set()
        merged_sources: set[str] = set()
        for candidate in sorted(self._normalized_to_terms.get(normalized_term, set())):
            for gloss in self._glosses_by_term.get(candidate, []):
                if gloss not in seen_glosses:
                    merged_glosses.append(gloss)
                    seen_glosses.add(gloss)
            merged_sources.update(self._sources_by_term.get(candidate, set()))

        if not merged_glosses:
            return None
        return {
            "english_glosses": merged_glosses,
            "sources": sorted(merged_sources),
        }

    def _build_entry(self, term: str) -> dict[str, Any] | None:
        glosses = self._glosses_by_term.get(term, [])
        if not glosses:
            return None
        return {
            "english_glosses": list(glosses),
            "sources": sorted(self._sources_by_term.get(term, set())),
        }

    def as_output(self) -> dict[str, dict[str, Any]]:
        return {
            term: self._build_entry(term)
            for term in sorted(self._glosses_by_term)
            if self._build_entry(term)
        }


def load_gold_benchmark(accumulator: GlossAccumulator) -> int:
    loaded = 0
    for row in iter_jsonl(GOLD_PATH):
        source = row.get("source", {})
        if not str(source.get("lang") or "").startswith("ara"):
            continue
        lemma = str(source.get("lemma") or "").strip()
        glosses = extract_glosses(source.get("gloss", ""))
        if accumulator.add(lemma, glosses, "gold_benchmark"):
            loaded += 1
    return loaded


def load_beyond_name(accumulator: GlossAccumulator) -> int:
    loaded = 0
    with BTN_PATH.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            root = str(row.get("arabic_root") or "").strip()
            glosses = extract_glosses(row.get("english_word", ""))
            if accumulator.add(root, glosses, "beyond_name"):
                loaded += 1
    return loaded


def find_concepts_path() -> Path | None:
    for path in CONCEPT_CANDIDATE_PATHS:
        if path.exists():
            return path
    return None


def load_concepts(accumulator: GlossAccumulator, concepts_path: Path | None) -> int:
    if not concepts_path:
        return 0

    loaded = 0
    for row in iter_jsonl(concepts_path):
        glosses = extract_glosses(row.get("core_gloss_en", ""))
        for synonym in row.get("synonyms_en", []) or []:
            glosses.extend(extract_glosses(synonym))

        deduped_glosses: list[str] = []
        seen: set[str] = set()
        for gloss in glosses:
            if gloss not in seen:
                deduped_glosses.append(gloss)
                seen.add(gloss)

        for link in row.get("figurative_links", []) or []:
            if link.get("lang") != "ara":
                continue
            form = str(link.get("form") or "").strip()
            if accumulator.add(form, deduped_glosses, "concepts"):
                loaded += 1
    return loaded


def load_wiktionary_samples(accumulator: GlossAccumulator) -> tuple[int, list[str]]:
    sample_dir = LV2_ROOT / "resources/samples/processed"
    sample_files = sorted(sample_dir.glob(WIKTIONARY_SAMPLE_GLOB))
    loaded = 0
    used_files: list[str] = []

    for path in sample_files:
        used_files.append(str(path.relative_to(LV2_ROOT)))
        for row in iter_jsonl(path):
            lemma = str(row.get("lemma") or "").strip()
            glosses = extract_glosses(row.get("gloss_plain") or row.get("gloss_html") or "")
            if accumulator.add(lemma, glosses, "wiktionary"):
                loaded += 1
    return loaded, used_files


def write_lookup(path: Path, payload: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)


def update_unified_arabic(accumulator: GlossAccumulator) -> tuple[int, int]:
    rows = list(iter_jsonl(UNIFIED_ARABIC_PATH))
    updated = 0

    with UNIFIED_ARABIC_PATH.open("w", encoding="utf-8") as handle:
        for row in rows:
            lemma = str(row.get("lemma") or "")
            root = str(row.get("root") or "")
            match = accumulator.resolve(lemma)
            if not match and normalize_arabic(lemma) == normalize_arabic(root):
                match = accumulator.resolve(root)
            if match:
                row["english_gloss"] = match["english_glosses"][0]
                updated += 1
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    return updated, len(rows)


def main() -> None:
    accumulator = GlossAccumulator()

    source_counts = Counter()
    source_counts["gold_benchmark"] = load_gold_benchmark(accumulator)
    source_counts["beyond_name"] = load_beyond_name(accumulator)

    concepts_path = find_concepts_path()
    source_counts["concepts"] = load_concepts(accumulator, concepts_path)

    wiktionary_loaded, wiktionary_files = load_wiktionary_samples(accumulator)
    source_counts["wiktionary"] = wiktionary_loaded

    output_payload = accumulator.as_output()
    write_lookup(OUTPUT_LOOKUP_PATH, output_payload)

    updated_entries, total_entries = update_unified_arabic(accumulator)

    print(f"Gold benchmark additions: {source_counts['gold_benchmark']}")
    print(f"Beyond the Name additions: {source_counts['beyond_name']}")
    print(f"Concept additions: {source_counts['concepts']}")
    print(f"Wiktionary additions: {source_counts['wiktionary']}")
    print(f"Concept file used: {concepts_path.relative_to(LV2_ROOT) if concepts_path else 'missing'}")
    if wiktionary_files:
        print(f"Wiktionary files used: {', '.join(wiktionary_files)}")
    else:
        print("Wiktionary files used: none")
    print(f"Arabic lookup entries: {len(output_payload)}")
    print(f"Arabic entries with English glosses: {updated_entries} / {total_entries}")
    print(f"Lookup written to: {OUTPUT_LOOKUP_PATH}")
    print(f"Unified Arabic updated: {UNIFIED_ARABIC_PATH}")


if __name__ == "__main__":
    main()
