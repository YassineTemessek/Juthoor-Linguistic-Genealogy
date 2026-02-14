# Arabic Word Decoding (LV1) 🧩

![level](https://img.shields.io/badge/level-LV1-6f42c1)
![license](https://img.shields.io/badge/license-MIT-blue)

LV1 is the Arabic-focused level: **binary-root (2-letter nucleus) decoding**, clustering, and graph exports, starting with Quranic Arabic and expanding to broader Arabic.

Core idea:

- Arabic roots are often 3 (or 4) radicals.
- LV1 treats many 3-letter roots as variations around a deeper **binary nucleus** (first 2 "core" radicals), with later letters shaping nuance.
- LV1 builds a wide-coverage Arabic lexeme/root table, then **regroups words into binary-root-centered clusters** using methods that fit the purpose (heuristics, BGE-M3/ByT5 embeddings, and graph methods).


## Role in the stack ??

LV1 regroups Arabic words by binary roots derived in LV0, measures distances between binary roots,
and studies how 3-letter roots connect inside each binary-root cluster.

## Project map 🧭

- LV0 (data core): Juthoor-DataCore-LV0
- LV1 (Arabic genome, this repo): Juthoor-ArabicGenome-LV1
- LV2 (cognate discovery): Juthoor-CognateDiscovery-LV2
- LV3 (theory & validation): Juthoor-Origins-LV3
- QCA (Quranic analysis): Quran-Corpus-Analysis

## Outputs ✅

- Binary-root-ready lexeme tables (consumed from LV0; processed locally as needed)
- Cluster assignments (discovery-stage)
- Graph exports (nodes/edges) for inspection and GraphRAG-style workflows

## Graph view 🕸️

LV1 aims to produce a graph-friendly representation of Arabic word relationships:

- Nodes: `lemma`, `root`, `binary_root`
- Edges: `lemma -> root`, `root -> binary_root`, plus optional derived links (shared pattern, shared cluster, etc.)

## Repo policy (important) 📌

- Large datasets under `data/raw/` and generated tables under `data/processed/` are **not committed by default** (see `.gitignore`).
- Small, versioned reference assets can live under `resources/`.

## Quickstart 🚀

1) Get canonical Arabic processed tables from LV0 (recommended: fetch LV0 release bundles).
2) Run LV1 clustering/graph scripts here.

Binary-root clustering (discovery):

- `python "scripts/cluster/cluster_by_binary_root.py"`

QA report (binary vs tri-root):

- `python "scripts/analysis/compare_binary_vs_triroot.py"`

Graph export (nodes + edges):

- `python "scripts/graph/export_binary_root_graph.py" --input <binary_root_lexicon.jsonl>`

## Docs 📚

- Start here: `docs/START_HERE.md`
- Ingest policy (LV0): `docs/INGEST.md`

## Contact 🤝

For collaboration: `yassine.temessek@hotmail.com`

## Suggested GitHub "About" 📝

Arabic decoding (LV1): binary-root clustering + graph exports, built on LV0 canonical datasets.


## Project Status & Progress
- Project-wide progress log: docs/PROGRESS_LOG.md`n- Raw data flow (Resources -> LV0 -> processed): docs/RAW_DATA_FLOW.md`n
