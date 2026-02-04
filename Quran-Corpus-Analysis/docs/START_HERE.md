# Start Here (LV1)

LV1 is the Quran-focused analysis layer. It consumes LV0 canonical data and produces
Quran-specific analysis outputs that measure opposites, semantic distance, and nuance.


Focus areas:

- Identify 100 percent opposites where they exist.
- Measure distance between close words and concepts.
- Document nuance where meanings are similar but not identical.

Workflow:

1) Build or fetch LV0 processed data.
2) Run LV1 analysis scripts against the Quranic tables.
3) Inspect outputs under outputs.

## Core data inputs

In LV0, Quranic Arabic outputs typically include:

- data/processed/quranic_arabic/lexemes.jsonl
- data/processed/quranic_arabic/sources/quran_lemmas_enriched.jsonl

Copy or fetch these into this repo under data/processed.

## Core scripts (LV1)

- scripts/analysis/01_rj_cooc.py
- scripts/analysis/build_word_root_map.py
- scripts/analysis/make_examples_from_roots.py
- scripts/analysis/make_subset.py

Legacy scripts and archived outputs live under scripts/legacy and outputs/legacy.
