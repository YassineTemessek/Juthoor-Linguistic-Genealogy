"""Build a compact IPA lookup JSON from the full english_ipa_merged_pos.jsonl corpus.

Reads the 88MB JSONL file, extracts {lemma: ipa} pairs (preferring source_priority=1,
i.e. ipa-dict entries), and writes a compact JSON to data/processed/english_ipa_lookup.json.

Run from repo root:
    python Juthoor-CognateDiscovery-LV2/scripts/build_ipa_lookup.py
"""
from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    here = Path(__file__).resolve()
    # scripts/ -> LV2 root
    lv2_root = here.parent.parent
    src_path = lv2_root / "data" / "processed" / "english" / "english_ipa_merged_pos.jsonl"
    out_path = lv2_root / "data" / "processed" / "english_ipa_lookup.json"

    if not src_path.exists():
        print(f"ERROR: source file not found: {src_path}")
        return

    # Two-pass: collect best IPA per lemma (prefer lower source_priority = better source)
    # source_priority 1 = ipa-dict (canonical), 2 = cmudict, etc.
    lookup: dict[str, tuple[str, int]] = {}  # lemma -> (ipa, priority)

    print(f"Reading {src_path} ...")
    count = 0
    with src_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            lemma = entry.get("lemma", "")
            ipa = entry.get("ipa", "")
            if not lemma or not ipa:
                continue
            priority = int(entry.get("source_priority", 99))
            existing = lookup.get(lemma)
            if existing is None or priority < existing[1]:
                lookup[lemma] = (ipa, priority)
            count += 1
            if count % 200_000 == 0:
                print(f"  processed {count:,} lines, {len(lookup):,} unique lemmas ...")

    # Strip priority from output — just {lemma: ipa}
    final: dict[str, str] = {lemma: ipa for lemma, (ipa, _) in lookup.items()}

    print(f"Writing {len(final):,} entries to {out_path} ...")
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = out_path.stat().st_size / 1024
    print(f"Done. Output size: {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
