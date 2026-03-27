"""
Merge Beyond the Name language-specific pairs into the unified gold benchmark.

Usage:
    python scripts/discovery/merge_gold_benchmark.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
GOLD_PATH = ROOT / "resources" / "benchmarks" / "cognate_gold.jsonl"
DATA_DIR = ROOT / "data" / "processed"

BEYOND_NAME_FILES = [
    ("beyond_name_latin_pairs.jsonl", "latin"),
    ("beyond_name_greek_pairs.jsonl", "greek"),
    ("beyond_name_french_pairs.jsonl", "french"),
    ("beyond_name_other_pairs.jsonl", "other"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dedup_key(entry: dict) -> tuple:
    src = entry["source"]
    tgt = entry["target"]
    return (src["lang"], src["lemma"], tgt["lang"], tgt["lemma"])


def load_jsonl(path: Path) -> list[dict]:
    entries = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def convert_beyond_name(entry: dict, provenance_suffix: str) -> dict:
    """Convert a beyond_name_*.jsonl entry to gold benchmark schema."""
    src = entry.get("source", {})
    tgt = entry.get("target", {})

    # Use confidence from source; fall back to 0.7
    confidence = float(entry.get("confidence", 0.7))
    # Cap at 0.9 for automatically extracted pairs (not manual)
    confidence = min(confidence, 0.9)

    return {
        "source": {
            "lang": src.get("lang", "ara"),
            "lemma": src.get("lemma", ""),
            "gloss": src.get("gloss", ""),
        },
        "target": {
            "lang": tgt.get("lang", ""),
            "lemma": tgt.get("lemma", ""),
            "gloss": tgt.get("gloss", ""),
        },
        "relation": entry.get("relation", "cognate"),
        "confidence": confidence,
        "provenance": f"beyond_the_name_{provenance_suffix}",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # 1. Load existing gold benchmark
    existing = load_jsonl(GOLD_PATH)
    seen: set[tuple] = {_dedup_key(e) for e in existing}
    print(f"Existing gold pairs: {len(existing)}")

    # Track counts per language pair
    lang_pair_counts: dict[str, int] = defaultdict(int)
    for e in existing:
        lp = f"{e['source']['lang']}-{e['target']['lang']}"
        lang_pair_counts[lp] += 1

    new_entries: list[dict] = []
    skipped = 0

    # 2. Process each beyond_name file
    for filename, suffix in BEYOND_NAME_FILES:
        file_path = DATA_DIR / filename
        if not file_path.exists():
            print(f"  WARNING: {filename} not found, skipping.")
            continue

        raw = load_jsonl(file_path)
        file_new = 0
        file_skip = 0

        for entry in raw:
            converted = convert_beyond_name(entry, suffix)
            key = _dedup_key(converted)

            if key in seen:
                file_skip += 1
                skipped += 1
                continue

            seen.add(key)
            new_entries.append(converted)
            file_new += 1

            lp = f"{converted['source']['lang']}-{converted['target']['lang']}"
            lang_pair_counts[lp] += 1

        print(f"  {filename}: +{file_new} new, {file_skip} duplicates skipped")

    # 3. Write merged file
    all_entries = existing + new_entries
    with GOLD_PATH.open("w", encoding="utf-8") as fh:
        for entry in all_entries:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # 4. Summary
    print(f"\nMerge complete.")
    print(f"  Added:   {len(new_entries)} new pairs")
    print(f"  Skipped: {skipped} duplicates")
    print(f"  Total:   {len(all_entries)} pairs in gold benchmark")
    print()
    print("Pairs per language pair:")
    for lp, count in sorted(lang_pair_counts.items(), key=lambda x: -x[1]):
        print(f"  {lp}: {count}")


if __name__ == "__main__":
    main()
