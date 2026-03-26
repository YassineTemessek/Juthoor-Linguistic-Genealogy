# Juthoor ArabicGenome (LV1)

![level](https://img.shields.io/badge/level-LV1-6f42c1)
![license](https://img.shields.io/badge/license-MIT-blue)

**LV1 is the Arabic linguistic genome and computational research factory.** It models the claim that Arabic meaning is structured across three layers: the single letter, the biconsonantal nucleus, and the triliteral root.

## Current Status

- **Method A:** **53.0%**
- **Best scholar model:** `consensus_weighted` at **bJ=0.200**
- **Pipeline:** adaptive routing is active; `position_aware` is used with fallback to `nucleus_only` when it would score worse
- **Empirical corrections:** 4 letter fixes confirmed and applied (`م`, `ع`, `غ`, `ب`)
- **Research corpus:** 25 research documents
- **Test suite status:** 498 LV1 tests

## The Core Idea

Arabic words derive from 3-consonant roots, but LV1 tests whether the first two consonants define a stable semantic field while the third consonant acts as a modifier with measurable behavior.

## Two Layers

### LV1-CORE

| Phase | What | Output | Status |
|-------|------|--------|--------|
| **Phase 1** | Brute grouping of Arabic lexemes by binary root | 30 BAB files, 12,333 genome entries | Complete |
| **Phase 2** | Muajam Ishtiqaqi overlay | 1,924 roots, 456 nuclei in current theory canon | Complete |
| **Phase 3** | Root prediction + scoring | adaptive-routed score matrices and promoted assets | Active |

### LV1-RESEARCH FACTORY

A computational research engine testing 12 formal hypotheses through experiment outputs, score matrices, promoted registries, and downstream exports to LV2/LV3.

## Root Prediction Rebuild

The current rebuild uses five scholar tracks:

- `jabal`
- `asim_al_masri`
- `hassan_abbas`
- `consensus_strict`
- `consensus_weighted`

Current generated metrics from `outputs/lv1_scoring/root_score_matrix.json`:

| Scope | Mean blended Jaccard |
|------|-----------------------:|
| Overall | 0.195517 |
| `jabal` | 0.195024 |
| `consensus_strict` | 0.198397 |
| `consensus_weighted` | **0.200392** |

Current model means:

| Model | Count | Mean blended Jaccard |
|------|------:|----------------------:|
| `nucleus_only` | 3116 | **0.236867** |
| `consensus_weighted` scholar total | 1924 | **0.200392** |
| `phonetic_gestural` | 1594 | 0.193946 |
| `intersection` | 1447 | 0.183413 |
| `position_aware` | 3005 | 0.162999 |

The important behavior change is routing, not unconditional replacement: `position_aware` can still be selected, but the predictor now prefers `nucleus_only` when the position-aware composition would underperform.

## Letter Corrections

Four letter meanings were corrected empirically after repeated scoring failures:

| Letter | Corrected meaning |
|--------|-------------------|
| م | تجمع + تلاصق |
| ع | ظهور + عمق |
| غ | باطن + اشتمال |
| ب | ظهور + خروج |

## Research Factory Snapshot

Current dashboard snapshot:

- 12 hypotheses tracked
- 11 experiments with result files
- 4 supported
- 1 weakly supported
- 1 weak signal
- 3 not supported
- 2 pending

## Project Structure

```
Juthoor-ArabicGenome-LV1/
├── src/juthoor_arabicgenome_lv1/
├── scripts/
├── data/theory_canon/
├── outputs/
├── resources/
└── tests/
```

## Quickstart

```bash
uv pip install -e . -e ../Juthoor-DataCore-LV0 -e ../Juthoor-CognateDiscovery-LV2

python scripts/build_genome_phase1.py
python scripts/build_genome_phase2.py
python scripts/canon/build_lv1_theory_assets.py
python ../scripts/generate_lv1_dashboard.py
```

## Role in the Stack

```
LV0 (data) -> LV1 (genome + research factory) -> LV2/LV3
```

LV1 is the structural layer. It produces scored Arabic theory assets, promoted research outputs, and cross-lingual support features consumed by LV2.

## Documentation

- **[Research Factory Master Plan](./docs/plans/RESEARCH_FACTORY_MASTER_PLAN.md)**
- **[LV1 Future Refinements](./docs/plans/LV1_FUTURE_REFINEMENTS.md)**
- **[QCA Documentation](./docs/qca/START_HERE.md)**

## License

MIT License. See [LICENSE](./LICENSE).

**Author:** Yassine Temessek
