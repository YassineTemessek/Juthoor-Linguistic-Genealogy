# QCA — Progress Log

Last updated: 2026-03-14

## Current State

QCA (Quranic Corpus Analysis) is a subpackage of LV1 at `juthoor_arabicgenome_lv1.qca`.

## Location

| Artifact | Path |
|----------|------|
| Python subpackage | `juthoor_arabicgenome_lv1/qca/` |
| Scripts | `Juthoor-ArabicGenome-LV1/scripts/qca/` |
| Docs | `Juthoor-ArabicGenome-LV1/docs/qca/` |
| Data | `Juthoor-ArabicGenome-LV1/data/qca/` |
| Outputs | `Juthoor-ArabicGenome-LV1/outputs/qca/` |

## Scripts

- `build_word_root_map.py` — maps Quranic words to their roots
- `01_rj_cooc.py` — root-join co-occurrence analysis
- `make_examples_from_roots.py` — generates root usage examples
- `make_subset.py` — extracts corpus subsets

## Data Source

- 4,903 Quranic Arabic lexemes ingested via LV0 adapter (`ingest_quran_morphology.py`)
- Morphology data available in `Juthoor-DataCore-LV0/data/processed/quranic_arabic/`
