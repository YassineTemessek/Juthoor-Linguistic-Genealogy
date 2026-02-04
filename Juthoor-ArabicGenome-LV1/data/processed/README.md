# Processed data (LV2)

`data/processed/` contains **machine-readable outputs** produced from `data/raw/` by the ingestion scripts.

Datasets are not committed by default, but this README documents the contract.

## Canonical outputs

- `data/processed/arabic/quran_lemmas_enriched.jsonl` (Quran lemma list + translit + IPA)
- `data/processed/arabic/word_root_map_filtered.jsonl` (word-root mapping; empty-root rows removed; adds `type`)
- `data/processed/arabic/hf_roots.jsonl` (Arabic roots dataset with translit + IPA)
- `data/processed/arabic/arabic_words_binary_roots.jsonl` (merged word list with `binary_root` fields for LV2 grouping)

## Binary roots (LV2)

LV2 introduces `binary_root` as a 2-letter nucleus derived from the standard root string.

This repo keeps both:

- the source `root` (triliteral/quadriliteral as provided), and
- a derived `binary_root` (2-letter key used for grouping).

## Graph-friendly exports (LV2)

Downstream, we also support exporting the processed lexicon as simple **nodes/edges CSVs** for visualization and GraphRAG-style workflows:

- `outputs/graphs/binary_root_nodes.csv`
- `outputs/graphs/binary_root_edges.csv`

## Common JSONL schema (target contract)

For JSONL lexeme files, we aim for a shared minimal schema:

- Always present: `id`, `lemma`, `language`, `stage`, `script`, `source`, `lemma_status`
- Optional but normalized when present:
  - `ipa_raw` + `ipa` (`ipa` is normalized; no surrounding `/.../` or `[...]`)
  - `pos` (always a list)
  - `gloss_html` + `gloss_plain`
  - `source_ref` (optional pointer back to a source row/key for traceability)


## Project Status & Progress
- Project-wide progress log: docs/PROGRESS_LOG.md`n- Raw data flow (Resources -> LV0 -> processed): docs/RAW_DATA_FLOW.md`n
