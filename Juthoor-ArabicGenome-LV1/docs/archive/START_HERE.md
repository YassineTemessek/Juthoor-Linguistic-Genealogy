# Start Here (LV1)

Juthoor Arabic Genome (LV1) decodes the Arabo-Semitic root system by analyzing the 2-letter binary root structure underlying Arabic words.

## Current Status

**Phase 1: DONE**
- Grouping Arabic lexemes by BAB → binary root → triconsonantal root → words
- Command: `python scripts/build_genome_phase1.py`
- Output: `outputs/genome/<letter>.jsonl` (one file per Arabic letter)

**Phase 2: IN PROGRESS**
- Overlaying Muajam Ishtiqaqi meanings (letter → binary root → axial meanings)
- Ingest: Processes Muajam Ishtiqaqi data into `data/muajam/`
- This phase links letter-based meaning semantics to binary root clusters

**Phase 3: PLANNED**
- Semantic validation of binary root ↔ word meaning connections

## Existing Clustering Scripts

Clustering and analysis pipelines from earlier work still available:
- Cluster by binary root: `python scripts/cluster/cluster_by_binary_root.py`
- Binary vs tri-root coherence: `python scripts/analysis/compare_binary_vs_triroot.py`
- Export binary root graph: `python scripts/graph/export_binary_root_graph.py --input <binary_root_lexicon.jsonl>`

## Quick Start

1. Ensure LV0 processed data is ready (see `Juthoor-DataCore-LV0/`)
2. Run Phase 1 genome build: `python scripts/build_genome_phase1.py`
3. Results appear in `outputs/genome/`
