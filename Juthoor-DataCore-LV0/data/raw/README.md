# LV0 Raw Data (Not Committed)

This folder is where contributors place **raw source datasets** locally before running `ldc ingest`.
Raw data flow reference: `docs/RAW_DATA_FLOW.md`.

Raw data is intentionally **not committed** to Git by default (size/licensing/provenance).

## Recommended layout

Use a consistent dataset folder structure:

- `data/raw/<source>/<language>/<stage>/...`

Examples (Arabic, classical):

- `data/raw/arabic/quran-morphology/quran-morphology.txt`
- `data/raw/arabic/word_root_map.csv`
- `data/raw/arabic/arabic_roots_hf/train-00000-of-00001.parquet`

## Arabic source checklist (optional)

- Quran morphology: `data/raw/arabic/quran-morphology/quran-morphology.txt`
- Word root map: `data/raw/arabic/word_root_map.csv`
- HF roots: `data/raw/arabic/arabic_roots_hf/train-00000-of-00001.parquet`

## Notes

- `stage` is treated as a dataset boundary in LV0 (folder/file level), not a required per-row field.
- After ingest, LV0 writes per-source processed files under `data/processed/<language>/<stage>/sources/` and a merged canonical `lexemes.jsonl`.

## Currently linked raw sources (as of 2026-02)

The `data/raw/` directory is populated via `scripts/setup_raw_links.ps1` which creates junctions from `Resources/` into here.

Currently present:
- `arabic/arabic_roots_hf/` — HuggingFace Arabic roots Parquet
- `arabic/quran-morphology/` — Quran morphology text file
- `arabic/word_root_map.csv` — Arabic word-root mapping CSV
- `arabic/cmudict` — CMU pronouncing dictionary (Arabic-adjacent IPA source)
- `english/` — English IPA data

Not yet linked here (consumed directly from `Resources/` via `kaikki_root` path in runner):
- `ancient_greek/kaikki.org-dictionary-AncientGreek.jsonl`
- `latin/kaikki.org-dictionary-Latin.jsonl`
- `english_old/kaikki.org-dictionary-OldEnglish.jsonl`
- `english_middle/kaikki.org-dictionary-MiddleEnglish.jsonl`
- `english_modern/kaikki.org-dictionary-English.jsonl`
- `Ten dictionaries for Arabic language/` (CSV files)

## Project Status & Progress
- Raw data flow (Resources -> LV0 -> processed): `docs/RAW_DATA_FLOW.md`
