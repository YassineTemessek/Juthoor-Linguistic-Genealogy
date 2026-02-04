# Quran's Words decoding (LV1)

![level](https://img.shields.io/badge/level-LV1-6f42c1)
![license](https://img.shields.io/badge/license-MIT-blue)

LV1 focuses on Quranic Arabic word relationships: opposites, semantic distance, and nuance.
It consumes LV0 canonical outputs and tests the idea that Quranic words are not fully identical
in meaning even when they are close.


## Role in the stack

LV1 is the Quran-specific analysis layer. It measures relationships between Quranic words
(opposites, distance, and nuance) on top of LV0-processed tables.

## Project map

- LV0 (data core): https://github.com/YassineTemessek/Juthoor-DataCore-LV0
- LV0 project ReadMe: https://github.com/YassineTemessek/Juthoor-DataCore-LV0/blob/main/ReadMe.txt
- LV1 (this repo): https://github.com/YassineTemessek/Quran-Corpus-Analysis
- LV2 (Arabic decoding and clustering): https://github.com/YassineTemessek/Juthoor-ArabicGenome-LV1
- LV3 (cross-language discovery): https://github.com/YassineTemessek/Juthoor-CognateDiscovery-LV2
- LV4 (validation blueprint): https://github.com/YassineTemessek/Juthoor-Origins-LV3

## Repo policy

- Large datasets under data/raw and data/processed are not committed by default.
- Outputs under outputs are not committed by default.
- Small tracked references can live under resources.

## Quickstart

1) Get canonical Quranic Arabic tables from LV0.
   - Recommended: use LV0 release bundles with ldc fetch.
   - Alternative: build locally in LV0 (ldc ingest --all).
2) Run LV1 analysis scripts in scripts/analysis.
3) Review outputs under outputs.

## Docs

- Start here: docs/START_HERE.md
- Ingest policy (LV0): docs/INGEST.md

## Contact

For collaboration: yassine.temessek@hotmail.com


## Project Status & Progress
- Project-wide progress log: docs/PROGRESS_LOG.md`n- Raw data flow (Resources -> LV0 -> processed): docs/RAW_DATA_FLOW.md`n
