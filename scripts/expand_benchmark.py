"""
Expand cognate_gold.jsonl with new Arabic-English pairs from beyond_name_cognate_gold_candidates.jsonl.
Gold tier (confidence >= 0.7): appended to cognate_gold.jsonl
Silver tier (0.5 <= confidence < 0.7): written to new cognate_silver.jsonl
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
GOLD_PATH = REPO_ROOT / "Juthoor-CognateDiscovery-LV2/resources/benchmarks/cognate_gold.jsonl"
SILVER_PATH = REPO_ROOT / "Juthoor-CognateDiscovery-LV2/resources/benchmarks/cognate_silver.jsonl"
CANDIDATES_PATH = REPO_ROOT / "Juthoor-CognateDiscovery-LV2/data/processed/beyond_name_cognate_gold_candidates.jsonl"

REQUIRED_FIELDS = {"source", "target", "relation", "confidence", "notes"}
REQUIRED_SOURCE_FIELDS = {"lang", "lemma", "gloss"}


def load_jsonl(path: Path) -> list[dict]:
    entries = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {lineno} of {path}: {e}") from e
    return entries


def validate_entry(entry: dict, lineno: int) -> None:
    missing = REQUIRED_FIELDS - set(entry.keys())
    if missing:
        raise ValueError(f"Entry at line {lineno} missing fields: {missing}")
    for side in ("source", "target"):
        missing_sub = REQUIRED_SOURCE_FIELDS - set(entry[side].keys())
        if missing_sub:
            raise ValueError(f"Entry at line {lineno} {side} missing fields: {missing_sub}")
    if entry["relation"] != "cognate":
        raise ValueError(f"Entry at line {lineno} has relation={entry['relation']!r}, expected 'cognate'")


def write_jsonl(path: Path, entries: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> None:
    # --- Load existing gold ---
    existing_gold = load_jsonl(GOLD_PATH)
    original_gold_count = len(existing_gold)
    print(f"Original gold count: {original_gold_count}")

    # Build dedup key set (source lemma + target lemma)
    seen_keys: set[tuple[str, str]] = set()
    for entry in existing_gold:
        seen_keys.add((entry["source"]["lemma"], entry["target"]["lemma"]))

    # --- Load candidates ---
    candidates = load_jsonl(CANDIDATES_PATH)
    print(f"Candidate entries loaded: {len(candidates)}")

    # --- Validate all candidates ---
    for i, c in enumerate(candidates, 1):
        validate_entry(c, i)

    # --- Split by confidence tier, dedup ---
    new_gold: list[dict] = []
    new_silver: list[dict] = []
    skipped_dups = 0

    for c in candidates:
        key = (c["source"]["lemma"], c["target"]["lemma"])
        if key in seen_keys:
            skipped_dups += 1
            continue
        seen_keys.add(key)  # prevent intra-batch duplicates

        conf = c["confidence"]
        if conf >= 0.7:
            new_gold.append(c)
        elif conf >= 0.5:
            new_silver.append(c)
        # entries below 0.5 are dropped (none expected per analysis)

    print(f"Duplicates skipped: {skipped_dups}")
    print(f"New gold entries (>=0.7): {len(new_gold)}")
    print(f"New silver entries (0.5-0.69): {len(new_silver)}")

    # --- Append new gold to existing file ---
    all_gold = existing_gold + new_gold
    write_jsonl(GOLD_PATH, all_gold)
    print(f"Final gold total: {len(all_gold)}")

    # --- Write silver file ---
    write_jsonl(SILVER_PATH, new_silver)
    print(f"Final silver total: {len(new_silver)}")

    # --- Verify by reloading ---
    print("\n--- Verification (reload) ---")
    verified_gold = load_jsonl(GOLD_PATH)
    verified_silver = load_jsonl(SILVER_PATH)
    print(f"Verified gold count: {len(verified_gold)}")
    print(f"Verified silver count: {len(verified_silver)}")
    assert len(verified_gold) == original_gold_count + len(new_gold), "Gold count mismatch!"
    assert len(verified_silver) == len(new_silver), "Silver count mismatch!"
    print("All assertions passed.")

    # --- Sample check: first new gold entry ---
    if new_gold:
        print("\nSample new gold entry:")
        print(json.dumps(new_gold[0], ensure_ascii=False, indent=2))

    # --- Sample check: first silver entry ---
    if new_silver:
        print("\nSample silver entry:")
        print(json.dumps(new_silver[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
