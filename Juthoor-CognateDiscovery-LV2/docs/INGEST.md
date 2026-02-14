# Data ingest (LV0) and LV2 pipeline

LV2 no longer owns ingest.

Raw → processed canonical datasets live in LV0:

- `https://github.com/YassineTemessek/Juthoor-DataCore-LV0`

See `docs/LV0_DATA_CORE.md` for how to fetch/build processed data.

## LV2 pipeline (discovery)

LV2 consumes canonical processed tables (from LV0) and runs:

- BGE-M3/ByT5 retrieval (high recall)
- Hybrid scoring (rough component scores + combined score)
- Output ranked leads under `outputs/`
