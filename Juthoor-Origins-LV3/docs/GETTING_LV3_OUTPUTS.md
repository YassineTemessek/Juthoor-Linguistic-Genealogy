# Getting LV3 outputs (inputs to LV4)

LV4 does not generate data itself. It **consumes LV3 artifacts**:

- Canonical processed lexeme tables (`data/processed/...`)
- Ranked leads (matching outputs)
- KPI/QA reports and run manifests

You have two ways to obtain them.

## Option A: Build locally (most reproducible)

1) Build/fetch canonical processed data via LV0 (data core):

- LV0 repo: `https://github.com/YassineTemessek/Juthoor-DataCore-LV0`
- LV0 project ReadMe: `https://github.com/YassineTemessek/Juthoor-DataCore-LV0/blob/main/ReadMe.txt`
- LV3 repo: `https://github.com/YassineTemessek/Juthoor-CognateDiscovery-LV2`
- `python scripts/discovery/run_discovery_retrieval.py --source ... --target ...` (SONAR/CANINE retrieval + hybrid scoring)
- Optional legacy matcher: `python scripts/discovery/run_full_matching_pipeline.py`

LV3 writes run manifests, caches, and outputs under `outputs/`.

Note: SONAR/CANINE runs require the optional LV3 dependencies (`requirements.embeddings.txt`) and will download model weights on first use.

## Option B: Download maintainer-published processed bundles (fastest)

If maintainers publish LV0 per-language bundles (recommended for big files):

- Install LV0 package (editable) and fetch: `ldc fetch --release latest --dest <your LV3 repo root>`

This extracts into the destination, creating `data/processed/...`.

See LV3: `docs/RELEASE_ASSETS.md`.
