# LV1 ArabicGenome — Progress Log

Last updated: 2026-03-14

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
