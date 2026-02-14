# Source code (`src/`)

`src/` is reserved for reusable code and modules (planned shared library).

Current status:

- `src/ingest/*_stub.py`: language ingest stubs/plans (not the active pipeline).
- Ingest now lives in LV0 (data core); LV2 consumes processed data.
- LV2 discovery retrieval modules live under `src/juthoor_cognatediscovery_lv2/lv3/` (BGE-M3 + ByT5 + indexing helpers).


## Project Status & Progress
- Project-wide progress log: docs/PROGRESS_LOG.md`n- Raw data flow (Resources -> LV0 -> processed): docs/RAW_DATA_FLOW.md`n
