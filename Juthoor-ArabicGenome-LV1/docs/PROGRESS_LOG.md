# LV1 ArabicGenome — Progress Log

Last updated: 2026-03-19

## 2026-03-19

### LV1 Core Restructure — Canon Layer Added

- Added a fully additive canon layer on top of the existing LV1 stack:
  - `core/canon_models.py`
  - `core/canon_loaders.py`
  - `core/canon_import.py`
  - `core/canon_pipeline.py`
  - `qca/canon_bridge.py`
  - `factory/canon_feedback.py`
- Added the theory-canon folder contract under `data/theory_canon/` with:
  - `inbox/`
  - `imported/`
  - `rejected/`
  - `registries/`
  - `import_reports/`
  - `SCHEMA.md`
- Added registry seeding from current repo assets via `scripts/canon/seed_registries.py`.

### Seeded Canon State

- Seeded canon registries now exist under `data/theory_canon/registries/`.
- Current seeded counts:
  - `28` letter entries
  - `457` binary-field entries
  - `12,333` root-composition entries
  - `5` initial theory claims
  - `0` Quranic profiles seeded by default

### Import And Bridge Behavior

- The canon importer now supports:
  - inbox validation
  - status-aware merge rules
  - imported/rejected routing
  - import reports
- Fixed an important isolation bug:
  - custom inbox/registry paths no longer leak imported/rejected/report artifacts into the real LV1 canon root during tests or temporary runs.
- The canon processing pipeline now:
  - degrades gracefully when semantic content is incomplete
  - attaches promoted LV1 evidence (H2/H8/H10/H9 outputs) instead of recomputing it
- The QCA bridge now exposes interpretation-ready evidence objects without collapsing conceptual / lexical / contextual layers.

### Test Status

- Added canon-specific tests for:
  - models
  - loaders
  - seeding
  - acceptance
  - import
  - pipeline
  - QCA bridge
  - promotion rules
- Full LV1 test suite status after the canon restructure:
  - `275 passed`

### Operational Conclusion

- LV1 is now structurally ready to receive curated theory content later without redesign.
- The next real LV1 bottleneck is no longer architecture; it is curated content ingestion:
  - letter semantics
  - binary field meanings
  - source claims
  - Quranic contrast/context assets

## Current State: Complete (Genome + Research Factory Phase 1)

## Genome Pipeline

| Phase | Status | Output |
|-------|--------|--------|
| Phase 1 — Root word lists | Complete | 30 BAB files, 12,333 roots, 22,908 words (`outputs/genome/`) |
| Phase 2 — Muajam overlay | Complete | 68.9% match (1,335/1,938 roots); enriched files in `outputs/genome_v2/` |
| Phase 3 — Semantic validation | Complete | 1,910 roots scored; mean cosine 0.5578; report at `outputs/reports/semantic_validation.json` |

**Phase 3 detail:** `scripts/semantic_validation_phase3.py` embeds Muajam axial meanings vs binary root meanings using BGE-M3 (1024-dim, L2-normalized). 928 genome_v2 entries carry a `semantic_score` field.

## Research Factory

| Phase | Status | Details |
|-------|--------|---------|
| Phase 0 — Infrastructure | Complete | Models, loaders, feature store, experiment runner, embeddings, articulatory vectors |
| Phase 1 — Experiments | Complete | 3 experiments run |

**Phase 1 experiments and verdicts:**

| Experiment | Name | Verdict |
|------------|------|---------|
| 1.1 | Letter similarity | H1 inconclusive |
| 2.3 | Field coherence | H2 supported |
| 3.1 | Modifier personality | H3 inconclusive |

## QCA Subpackage

- Located at `juthoor_arabicgenome_lv1.qca`
- Scripts at `scripts/qca/`, docs at `docs/qca/`
- See `docs/qca/PROGRESS_LOG.md` for details

## Tests

- 175 tests passing
