# Ingest (LV0)

LV2 does not own ingest anymore.

Raw → processed canonical datasets live in LV0 (data core):

- `Juthoor-DataCore-LV0/`
- LV0 project ReadMe: `Juthoor-DataCore-LV0/ReadMe.txt`

LV2 consumes processed datasets (for example, a binary-root lexicon JSONL) and focuses on clustering/regrouping + graph exports.

In LV0, the canonical Arabic binary-root lexicon is:

- Canonical merged lexemes (recommended): `data/processed/arabic/classical/lexemes.jsonl`
- Source-specific (optional): `data/processed/arabic/classical/arabic_words_binary_roots.jsonl`

## Graph exports (LV2)

Given an Arabic binary-root lexicon JSONL, export a graph-friendly view:

- Nodes + edges CSVs: `python "scripts/graph/export_binary_root_graph.py" --input <binary_root_lexicon.jsonl>`
