# Documentation

- Start here: `docs/START_HERE.md`
- Ingest & pipeline: `docs/INGEST.md`
- Similarity scoring spec: `docs/SIMILARITY_SCORING_SPEC.md`
- Next data improvements (ordered): `docs/NEXT_DATA_IMPROVEMENTS.md`
- LV0 data core: `docs/LV0_DATA_CORE.md`
- **Pipeline specification**: `docs/pipeline_specification.md` — comprehensive spec for the full discovery pipeline (forward + reverse, scoring, reranker, benchmarks)

LV2 discovery entrypoints:

- `scripts/discovery/run_reverse_discovery.py` — reverse pipeline (target → Arabic), recommended
- `scripts/discovery/run_discovery_multilang.py` — forward multilang pipeline (Arabic → target)
- `scripts/discovery/run_improved_discovery.py` — forward Arabic → English with semantic layer

## Project Status & Progress

- Project-wide progress log: `docs/PROGRESS_LOG.md`
- Raw data flow (Resources → LV0 → processed): `docs/RAW_DATA_FLOW.md`
