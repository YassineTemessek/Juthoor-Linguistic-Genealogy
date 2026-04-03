"""
build_arabic_profiles.py

Builds a semantic profile for every unique Arabic lemma in the gold benchmark
by combining:
  - Mafahim: deep conceptual root meaning from LV1 genome
  - Masadiq: dictionary meaning from LV0

Run from repo root:
  python Juthoor-CognateDiscovery-LV2/scripts/build_arabic_profiles.py
"""

import sys
import re
import json
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Paths (all relative to repo root where the script is invoked from)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]

GOLD_FILE = REPO_ROOT / "Juthoor-CognateDiscovery-LV2/resources/benchmarks/cognate_gold.jsonl"
WORD_ROOT_MAP = REPO_ROOT / "Juthoor-DataCore-LV0/data/processed/arabic/classical/sources/word_root_map_filtered.jsonl"
BINARY_FIELDS = REPO_ROOT / "Juthoor-ArabicGenome-LV1/data/theory_canon/registries/binary_fields.jsonl"
ROOTS_FILE = REPO_ROOT / "Juthoor-ArabicGenome-LV1/data/muajam/roots.jsonl"
LETTER_MEANINGS_FILE = REPO_ROOT / "Juthoor-ArabicGenome-LV1/data/muajam/letter_meanings.jsonl"
LEXEMES_FILE = REPO_ROOT / "Juthoor-DataCore-LV0/data/processed/arabic/classical/lexemes.jsonl"

OUTPUT_FILE = REPO_ROOT / "Juthoor-CognateDiscovery-LV2/data/llm_annotations/arabic_semantic_profiles.jsonl"


# ---------------------------------------------------------------------------
# Arabic normalization
# ---------------------------------------------------------------------------

def normalize_arabic(text: str) -> str:
    """Strip diacritics, tatweel, normalize hamza variants."""
    # Remove diacritics (tashkeel)
    text = re.sub(
        r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]",
        "",
        text,
    )
    # Remove tatweel
    text = text.replace("\u0640", "")
    # Normalize hamza variants to bare alef
    text = re.sub(r"[إأآ]", "ا", text)
    # Strip trailing/leading punctuation and commas
    text = text.strip("،, \t\n")
    return text


AL_PREFIX = re.compile(r"^ال")


def strip_al(text: str) -> str:
    """Strip leading ال (definite article) for root lookup."""
    return AL_PREFIX.sub("", text)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def build_word_root_map(records: list[dict]) -> tuple[dict, dict]:
    """Return (exact_map, norm_map) keyed by lemma and normalized lemma."""
    exact: dict[str, dict] = {}
    norm: dict[str, dict] = {}
    for rec in records:
        lemma = rec.get("lemma", "")
        if lemma and lemma not in exact:
            exact[lemma] = rec
        normed = normalize_arabic(lemma)
        if normed and normed not in norm:
            norm[normed] = rec
    return exact, norm


def build_binary_fields_map(records: list[dict]) -> dict[str, dict]:
    """Keyed by binary_root."""
    return {rec["binary_root"]: rec for rec in records if "binary_root" in rec}


def build_roots_map(records: list[dict]) -> dict[str, list[dict]]:
    """Keyed by tri_root, each key holds a list (multiple axial meanings possible)."""
    mapping: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        tri = rec.get("tri_root")
        if tri:
            mapping[tri].append(rec)
    return mapping


def build_roots_norm_map(records: list[dict]) -> dict[str, list[dict]]:
    """Same but keyed by normalize_arabic(tri_root)."""
    mapping: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        tri = rec.get("tri_root")
        if tri:
            mapping[normalize_arabic(tri)].append(rec)
    return mapping


def build_letter_map(records: list[dict]) -> dict[str, str]:
    """Keyed by letter -> meaning string."""
    return {rec["letter"]: rec.get("meaning", "") for rec in records if "letter" in rec}


def build_lexemes_map(records: list[dict]) -> tuple[dict, dict]:
    """Return (exact_map, norm_map) keyed by lemma, holding the richest entry."""
    exact: dict[str, dict] = {}
    norm: dict[str, dict] = {}
    for rec in records:
        lemma = rec.get("lemma", "")
        if lemma and lemma not in exact:
            exact[lemma] = rec
        normed = normalize_arabic(lemma)
        if normed and normed not in norm:
            norm[normed] = rec
        # Also index by root so we can fall back to root-level lookup
        root = rec.get("root", "")
        root_normed = normalize_arabic(root) if root else ""
        if root_normed and root_normed not in norm:
            norm[root_normed] = rec
    return exact, norm


# ---------------------------------------------------------------------------
# Profile builder
# ---------------------------------------------------------------------------

def build_profile(
    lemma: str,
    word_root_exact: dict,
    word_root_norm: dict,
    binary_fields: dict,
    roots_map: dict,
    roots_norm_map: dict,
    letter_map: dict,
    lex_exact: dict,
    lex_norm: dict,
) -> dict:
    lemma_norm = normalize_arabic(lemma)
    lemma_no_al = strip_al(lemma_norm)

    # --- 1. Root lookup (primary: word_root_map; fallback: lexemes record) ---
    root_rec = (
        word_root_exact.get(lemma)
        or word_root_norm.get(lemma_norm)
        or word_root_norm.get(lemma_no_al)
    )

    root = None
    binary_root = None
    if root_rec:
        root = root_rec.get("root") or root_rec.get("root_norm")
        binary_root = root_rec.get("binary_root")
        if not binary_root and root:
            root_clean = normalize_arabic(root)
            binary_root = root_clean[:2] if len(root_clean) >= 2 else root_clean

    # --- 5 (early). Masadiq from lexemes — also used to supply root if WRM missed ---
    lex_rec = (
        lex_exact.get(lemma)
        or lex_norm.get(lemma_norm)
        or lex_norm.get(lemma_no_al)
    )

    # If WRM missed but lexemes has a root, use it for genome lookups
    if not root and lex_rec:
        lex_root = lex_rec.get("root_norm") or normalize_arabic(lex_rec.get("root", ""))
        if lex_root:
            root = lex_root
            lex_br = lex_rec.get("binary_root")
            if lex_br:
                binary_root = normalize_arabic(lex_br)
            elif len(lex_root) >= 2:
                binary_root = lex_root[:2]

    root_norm = normalize_arabic(root) if root else None

    # --- 2. Binary field (mafahim) ---
    binary_field_gloss = None
    if binary_root:
        bf_norm = normalize_arabic(binary_root)
        bf_rec = binary_fields.get(binary_root) or binary_fields.get(bf_norm)
        if bf_rec:
            binary_field_gloss = bf_rec.get("field_gloss")

    # --- 3. Root meaning + axial meaning from roots.jsonl ---
    axial_meaning = None
    quran_example = None

    if root_norm:
        entries = roots_map.get(root_norm) or roots_norm_map.get(root_norm) or []
        # Prefer entries with non-empty axial_meaning
        chosen = next((e for e in entries if e.get("axial_meaning")), None) or (entries[0] if entries else None)
        if chosen:
            axial_meaning = chosen.get("axial_meaning") or None
            quran_example = chosen.get("quran_example") or None

    # --- 4. Letter meanings ---
    letter_meanings = []
    if root_norm:
        for ch in root_norm:
            meaning = letter_map.get(ch)
            if meaning:
                letter_meanings.append(f"{ch}: {meaning}")

    # lex_rec already resolved above; also try root-level fallback if still None
    if not lex_rec and root_norm:
        lex_rec = lex_norm.get(root_norm)

    short_gloss = None
    definition = None
    meaning_text = None
    if lex_rec:
        short_gloss = lex_rec.get("short_gloss") or None
        definition = lex_rec.get("definition") or None
        meaning_text = lex_rec.get("meaning_text") or None

    # --- 6. Determine lookup_status ---
    if root and (binary_field_gloss or axial_meaning) and (short_gloss or definition):
        status = "full"
    elif root:
        status = "partial"
    else:
        status = "no_root"

    return {
        "lemma": lemma,
        "lemma_normalized": lemma_norm,
        "root": root,
        "binary_root": binary_root,
        "mafahim": {
            "binary_field_gloss": binary_field_gloss,
            "axial_meaning": axial_meaning,
            "letter_meanings": letter_meanings if letter_meanings else None,
            "quran_example": quran_example,
        },
        "masadiq": {
            "short_gloss": short_gloss,
            "definition": definition,
            "meaning_text": meaning_text,
        },
        "lookup_status": status,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading data files...")

    # Gold pairs -> unique Arabic lemmas
    gold_lemmas: set[str] = set()
    with open(GOLD_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            src = rec.get("source", {})
            if src.get("lang") == "ara" and src.get("lemma"):
                gold_lemmas.add(src["lemma"])

    print(f"  Unique Arabic lemmas in gold: {len(gold_lemmas)}")

    # Load reference tables
    print("  Loading word_root_map_filtered...")
    wrm_records = load_jsonl(WORD_ROOT_MAP)
    word_root_exact, word_root_norm = build_word_root_map(wrm_records)

    print("  Loading binary_fields...")
    bf_records = load_jsonl(BINARY_FIELDS)
    binary_fields_map = build_binary_fields_map(bf_records)

    print("  Loading roots...")
    roots_records = load_jsonl(ROOTS_FILE)
    roots_map = build_roots_map(roots_records)
    roots_norm_map = build_roots_norm_map(roots_records)

    print("  Loading letter_meanings...")
    lm_records = load_jsonl(LETTER_MEANINGS_FILE)
    letter_map = build_letter_map(lm_records)

    print("  Loading lexemes (this may take a moment)...")
    lex_records = load_jsonl(LEXEMES_FILE)
    lex_exact, lex_norm = build_lexemes_map(lex_records)

    print("Building profiles...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    counts = {"full": 0, "partial": 0, "no_root": 0}

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for lemma in sorted(gold_lemmas):
            profile = build_profile(
                lemma,
                word_root_exact,
                word_root_norm,
                binary_fields_map,
                roots_map,
                roots_norm_map,
                letter_map,
                lex_exact,
                lex_norm,
            )
            counts[profile["lookup_status"]] += 1
            out.write(json.dumps(profile, ensure_ascii=False) + "\n")

    total = len(gold_lemmas)
    print()
    print("=" * 50)
    print(f"DONE — {total} Arabic lemmas processed")
    print(f"  Full profiles  : {counts['full']:4d} ({100*counts['full']/total:.1f}%)")
    print(f"  Partial        : {counts['partial']:4d} ({100*counts['partial']/total:.1f}%)")
    print(f"  No root found  : {counts['no_root']:4d} ({100*counts['no_root']/total:.1f}%)")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
