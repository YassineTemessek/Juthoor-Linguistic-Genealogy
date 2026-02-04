# Raw Data Flow (Resources → LV0 Raw → LV0 Processed)

This project treats `Resources/` as the single source of truth for raw datasets.
LV0 reads those sources via lightweight links under `Juthoor-DataCore-LV0/data/raw/`,
then writes canonical outputs under `Juthoor-DataCore-LV0/data/processed/`.

Flow summary:

1. Drop or update raw datasets in `Resources/`.
2. Run `scripts/setup_raw_links.ps1` to create junctions/hardlinks into LV0 raw.
3. Run `ldc ingest ...` inside `Juthoor-DataCore-LV0` to produce processed outputs.

Notes:
- The LV0 raw folder should stay thin; do not manually copy large datasets into it.
- If a source is missing, LV0 ingest will skip or fail depending on flags.
- Processed outputs are the only inputs that upper levels should consume.
