# Arabic Genome Phase 1 — Brute Word List Design

**Goal:** Group LV0 Arabic lexemes into a hierarchical structure: BAB (first letter) → binary root → triconsonantal root → word list.

**Input:** `Juthoor-DataCore-LV0/data/processed/arabic/classical/lexemes.jsonl`

**Script:** `scripts/build_genome_phase1.py`

**Output:** `outputs/genome/<bab_letter>.jsonl` — 24 files, one per BAB letter.

**Schema (one line per triconsonantal root):**
```json
{"bab": "ب", "binary_root": "بب", "root": "بوب", "words": ["باب", "بوّاب", "أبواب"]}
```

**Logic:**
1. Read all LV0 lexemes, skip records with no `root_norm`
2. `bab = root_norm[0]` (first character)
3. Group by bab → binary_root → root_norm → collect unique lemma strings (deduplicated, sorted)
4. Write one JSONL file per bab letter to `outputs/genome/`
5. Sort output: by binary_root alphabetically, then root alphabetically within each binary_root

**Phase 2 (later):** Overlay Muajam Ishtiqaqi meanings onto this structure.
