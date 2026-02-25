# Start Here (LV2)

This repo is a **discovery engine** for linguistic comparison.

The workflow is always:

1) **Get processed data** from LV0 (canonical tables under `data/processed/`).
2) **Discovery retrieval** consumes the canonical tables to produce **ranked leads** under `outputs/` (not committed).

## What "good" looks like

- `data/processed/*` files exist and pass validation (`id`, `lemma`, etc. are present; IPA is normalized).
- Discovery outputs contain lead rows with `semantic` and/or `form` scores plus provenance fields so results are traceable.
- Each LV0 ingest run produces a manifest JSON under LV0 `outputs/manifests/`.

## Collaboration-friendly samples (tracked)

Full datasets are not committed by default, but small samples are tracked under `resources/samples/processed/`.

- Run a quick discovery smoke test on samples (local backend):
  - `python "scripts/discovery/run_discovery_retrieval.py" --source ara@modern@arb_Arab="resources/samples/processed/Arabic-English_Wiktionary_dictionary_stardict_filtered_sample.jsonl" --target eng@modern@eng_Latn="resources/samples/processed/english_ipa_merged_pos_sample.jsonl" --models semantic form --topk 200 --max-out 200 --limit 200`

- Or use the API backend (no local GPU needed):
  - `pip install -r requirements.api.txt`
  - `python "scripts/discovery/run_discovery_retrieval.py" --backend api --source ara@modern@arb_Arab="resources/samples/processed/Arabic-English_Wiktionary_dictionary_stardict_filtered_sample.jsonl" --target eng@modern@eng_Latn="resources/samples/processed/english_ipa_merged_pos_sample.jsonl" --models semantic form --topk 200 --max-out 200 --limit 200`

## Recommended runs (Arabic → Indo‑European)

Replace paths with your LV0 outputs:

- Arabic (classical) vs English (modern):
  - `python "scripts/discovery/run_discovery_retrieval.py" --pair-id ara_vs_eng_modern --language-group indo_european --source ara@classical="data/processed/arabic/classical/lexemes.jsonl" --target eng@modern="data/processed/english/modern/lexemes.jsonl" --models semantic form --topk 200 --max-out 200`

- Arabic (classical) vs English (old + middle + modern):
  - `python "scripts/discovery/run_discovery_retrieval.py" --pair-id ara_vs_eng_all --language-group indo_european --source ara@classical="data/processed/arabic/classical/lexemes.jsonl" --target eng@old="data/processed/english/old/lexemes.jsonl" --target eng@middle="data/processed/english/middle/lexemes.jsonl" --target eng@modern="data/processed/english/modern/lexemes.jsonl" --models semantic form --topk 200 --max-out 200`

- Arabic (classical) vs Latin:
  - `python "scripts/discovery/run_discovery_retrieval.py" --pair-id ara_vs_lat --language-group indo_european --source ara@classical="data/processed/arabic/classical/lexemes.jsonl" --target lat@old="data/processed/latin/old/lexemes.jsonl" --models semantic form --topk 200 --max-out 200`

- Arabic (classical) vs Ancient Greek:
  - `python "scripts/discovery/run_discovery_retrieval.py" --pair-id ara_vs_grc --language-group indo_european --source ara@classical="data/processed/arabic/classical/lexemes.jsonl" --target grc@old="data/processed/greek/old/lexemes.jsonl" --models semantic form --topk 200 --max-out 200`

## Core commands

- Get/build canonical processed outputs: see `docs/LV0_DATA_CORE.md`
- Discover (BGE-M3/ByT5): `python "scripts/discovery/run_discovery_retrieval.py" ...`

## Discovery mode (BGE-M3 + ByT5)

LV2's recommended mode is embedding-first retrieval:

- **BGE-M3**: multilingual semantic retrieval (100+ languages, language-agnostic)
- **ByT5**: byte-level character/form retrieval (tokenizer-free, raw Unicode)

After retrieval, LV2 applies **hybrid scoring** to the retrieved pairs (rough, iterative):

- orthography signal (n-grams + string ratio; prefers `translit` when available)
- sound signal (IPA when available)
- consonant skeleton signal

Stages are treated as **free text** and can be used to split corpora (e.g., `eng@old`, `eng@middle`, `eng@modern`).

Corpus spec format:

`<lang>[@<stage>][@<bge_lang>]=<path>`

Where:

- `lang` is your project-level label (free text).
- `stage` is free text (defaults to `unknown`).
- `bge_lang` is the BGE-M3 language code (e.g., `eng_Latn`, `arb_Arab`). If omitted, LV2 uses a best-effort map for common languages.

## Getting full processed data (optional)

See `docs/LV0_DATA_CORE.md` for fetching LV0 release bundles.

## Where to read next

- Pipeline details: `docs/INGEST.md`
- LV0 data core: `docs/LV0_DATA_CORE.md`
- Data layout: `data/README.md`
- Processed data contract: `data/processed/README.md`
- Scoring model: `docs/SIMILARITY_SCORING_SPEC.md`
