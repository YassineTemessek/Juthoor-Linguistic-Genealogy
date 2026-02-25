"""
Phase 2 Genome Overlay Script
Merges Muajam Ishtiqaqi meanings into Phase 1 genome word lists.

Input:
  data/muajam/roots.jsonl        — 1,938 triconsonantal root entries
  data/muajam/letter_meanings.jsonl — 28 letter meaning entries
  outputs/genome/*.jsonl         — Phase 1 BAB files

Output:
  outputs/genome_v2/<bab>.jsonl  — Enriched entries, one per triconsonantal root
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent
MUAJAM_ROOTS = BASE / "data" / "muajam" / "roots.jsonl"
LETTER_MEANINGS = BASE / "data" / "muajam" / "letter_meanings.jsonl"
GENOME_V1_DIR = BASE / "outputs" / "genome"
GENOME_V2_DIR = BASE / "outputs" / "genome_v2"

# Arabic diacritic codepoints (harakat + shadda + etc.)
_ARABIC_DIACRITICS = re.compile(
    "[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8"
    "\u06EA-\u06ED]"
)


def normalize_root(root: str) -> str:
    """Strip spaces and Arabic diacritics for comparison."""
    root = root.strip()
    root = _ARABIC_DIACRITICS.sub("", root)
    return root


# ── Load letter meanings ───────────────────────────────────────────────────────
def load_letter_meanings() -> dict:
    letter_map = {}
    with LETTER_MEANINGS.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            letter_map[rec["letter"]] = rec["meaning"]
    print(f"Loaded {len(letter_map)} letter meanings")
    return letter_map


# ── Load Muajam roots ──────────────────────────────────────────────────────────
def load_muajam_roots() -> dict:
    """Return dict: normalized_tri_root -> full muajam record."""
    muajam = {}
    with MUAJAM_ROOTS.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            key = normalize_root(rec["tri_root"])
            muajam[key] = rec
    print(f"Loaded {len(muajam)} Muajam roots")
    return muajam


# ── Process one BAB file ───────────────────────────────────────────────────────
def process_bab_file(
    bab_path: Path,
    muajam: dict,
    letter_map: dict,
    out_dir: Path,
) -> tuple[int, int]:
    """
    Read a Phase 1 genome file, enrich each entry, write to genome_v2.
    Returns (matched_count, unmatched_count).
    """
    entries = []
    with bab_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))

    matched = 0
    unmatched = 0
    out_records = []

    for entry in entries:
        root = entry.get("root", "")
        key = normalize_root(root)
        muajam_rec = muajam.get(key)

        if muajam_rec:
            rec = {
                "bab": entry["bab"],
                "binary_root": entry["binary_root"],
                "root": root,
                "words": entry.get("words", []),
                "muajam_match": True,
                "binary_root_meaning": muajam_rec.get("binary_root_meaning", ""),
                "axial_meaning": muajam_rec.get("axial_meaning", ""),
                "added_letter": muajam_rec.get("added_letter", ""),
                "quran_example": muajam_rec.get("quran_example", ""),
                "letter1": muajam_rec.get("letter1", ""),
                "letter1_meaning": muajam_rec.get("letter1_meaning", ""),
                "letter2": muajam_rec.get("letter2", ""),
                "letter2_meaning": muajam_rec.get("letter2_meaning", ""),
                "bab_meaning": muajam_rec.get("bab_meaning", ""),
            }
            matched += 1
        else:
            rec = {
                "bab": entry["bab"],
                "binary_root": entry["binary_root"],
                "root": root,
                "words": entry.get("words", []),
                "muajam_match": False,
            }
            unmatched += 1

        out_records.append(rec)

    # Sort: by binary_root then root (preserving Phase 1 sort order is
    # already the natural order, but we sort explicitly for correctness)
    out_records.sort(key=lambda r: (r["binary_root"], r["root"]))

    out_path = out_dir / bab_path.name
    with out_path.open("w", encoding="utf-8") as f:
        for rec in out_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return matched, unmatched


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    GENOME_V2_DIR.mkdir(parents=True, exist_ok=True)

    letter_map = load_letter_meanings()
    muajam = load_muajam_roots()

    bab_files = sorted(GENOME_V1_DIR.glob("*.jsonl"))
    print(f"Processing {len(bab_files)} BAB files...\n")

    total_matched = 0
    total_unmatched = 0
    per_bab_stats = []

    for bab_path in bab_files:
        matched, unmatched = process_bab_file(bab_path, muajam, letter_map, GENOME_V2_DIR)
        total_matched += matched
        total_unmatched += unmatched
        per_bab_stats.append((bab_path.stem, matched, unmatched))

    # ── Summary ────────────────────────────────────────────────────────────────
    print("=" * 60)
    print(f"{'BAB':<8} {'Matched':>8} {'Unmatched':>10} {'Total':>8}")
    print("-" * 60)
    for bab, m, u in per_bab_stats:
        print(f"{bab:<8} {m:>8} {u:>10} {m+u:>8}")
    print("=" * 60)
    grand = total_matched + total_unmatched
    pct = (total_matched / grand * 100) if grand else 0
    print(f"{'TOTAL':<8} {total_matched:>8} {total_unmatched:>10} {grand:>8}")
    print(f"\nMatch rate: {pct:.1f}%")
    print(f"Output written to: {GENOME_V2_DIR}")


if __name__ == "__main__":
    main()
