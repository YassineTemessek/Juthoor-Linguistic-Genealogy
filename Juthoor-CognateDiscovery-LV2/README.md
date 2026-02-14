# Juthoor-CognateDiscovery-LV2

![level](https://img.shields.io/badge/level-LV2-6f42c1)
![license](https://img.shields.io/badge/license-MIT-blue)

Reproducible **discovery pipeline** that produces **ranked cross-language candidates** + **QA-friendly outputs**.

LV2 is "discovery-first": results are **not polished/final**, but we still **compare and score** aggressively to see what the outputs look like.
LV2 does not claim historical directionality.

## Role in the stack

LV2 compares Arabic 3-letter roots with Indo-European lexemes using orthographic and
phonetic similarity, then ranks candidate connections for review.

## Tools

- **BGE-M3 (BAAI)**: multilingual semantic retrieval (100+ languages, language-agnostic, cross-platform).
- **ByT5 (Google)**: byte-level character form retrieval (tokenizer-free, raw Unicode).
- **Hybrid scoring**: after retrieval, compute additional rough scores on retrieved pairs (orthography/IPA/skeleton/etc.).
- **FAISS**: vector similarity search for fast nearest-neighbor retrieval.

## What You Get

- Canonical, machine-readable lexeme tables under `data/processed/` (JSONL contract).
- Discovery outputs under `outputs/` (ranked leads, manifests, caches, previews).
- Validation tooling to catch broken rows early.

## Repo Policy

- Large datasets live under `data/raw/` and are **not committed** by default.
- Generated outputs under `data/processed/` and `outputs/` are **not committed** by default.

## Layout

- `scripts/`: runnable pipeline entrypoints (ingest + discovery)
- `outputs/`: local run artifacts (ignored by default)
- `data/`: local datasets (ignored by default) and processed outputs
- `resources/`: tracked reference assets (small, versioned)
- `src/`: reusable code (discovery modules live here)
- `docs/`: project documentation

## Pipeline

1) **Get canonical processed data (LV0)**: fetch release bundles or build locally in LV0.
2) **Discovery retrieval**: BGE-M3 (meaning) and/or ByT5 (form) retrieve top-K candidates.
3) **Hybrid scoring**: compute additional rough signals on the retrieved pairs and re-rank.
4) **Review/QA**: inspect `outputs/leads/` and iterate on data + scoring.

## Quickstart

1) Create a Python environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Linux/macOS
pip install -r requirements.txt
pip install -r requirements.embeddings.txt  # BGE-M3 + ByT5
```

2) Put datasets under `data/raw/` (see `data/README.md`).

3) Get canonical processed data from LV0:
   - Option A: use LV0 release bundles: `ldc fetch --release latest --dest ./`
   - Option B: build locally: `ldc ingest --all`

4) Run discovery retrieval:

```bash
python "scripts/discovery/run_discovery_retrieval.py" \
  --source ara@modern="path/to/arabic.jsonl" \
  --target eng@modern="path/to/english.jsonl" \
  --models bge_m3 byt5 --topk 200 --max-out 200 --limit 200
```

Corpus spec format: `<lang>[@<stage>]=<path>`

Outputs are written to `outputs/leads/` and embeddings/index caches to `outputs/`.

## Legacy (Classic Scoring Pipeline)

The classic scorer (orthography vs IPA sound scoring) remains available:

- `python "scripts/discovery/run_full_matching_pipeline.py"`

## Contributing

See `CONTRIBUTING.md`.

## Contact

For collaboration: `yassine.temessek@hotmail.com`
