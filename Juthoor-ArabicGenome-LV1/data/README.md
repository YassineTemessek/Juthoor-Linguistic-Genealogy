# Data folder (LV1)

This project uses large datasets under `data/`. They are intentionally **not committed** by default (see `.gitignore`).

## `data/raw/` (inputs)

Expected inputs (examples):

- `data/raw/arabic/quran-morphology/quran-morphology.txt`
- `data/raw/arabic/word_root_map.csv`
- `data/raw/arabic/arabic_roots_hf/train-00000-of-00001.parquet`

LV1 does not own ingest anymore; raw datasets and processing live in LV0 (data core).

## `data/processed/` (outputs)

Generated, machine-readable JSONL outputs consumed by downstream tooling.


## Project Status & Progress
- Project-wide progress log: docs/PROGRESS_LOG.md`n- Raw data flow (Resources -> LV0 -> processed): docs/RAW_DATA_FLOW.md`n
