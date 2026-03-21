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
- **Correspondence-aware reranking**: use root matches, consonant-class correspondence, hamza normalization, and weak-radical-aware features.
- **FAISS**: vector similarity search for fast nearest-neighbor retrieval.

## What You Get

- Canonical, machine-readable lexeme tables under `data/processed/` (JSONL contract).
- Discovery outputs under `outputs/` (ranked leads, manifests, caches, previews).
- Structured `evidence_card` fields in lead rows so candidates can be shown as explainable multi-channel evidence rather than a single score.
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
3) **Hybrid scoring**: compute rough signals on the retrieved pairs and re-rank.
4) **Benchmark evaluation**: score runs against tracked JSONL benchmarks and compare runs directly.
5) **Review/QA**: inspect `outputs/leads/` and iterate on data + scoring.

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
# Local backend (requires torch + model downloads)
python "scripts/discovery/run_discovery_retrieval.py" \
  --source ara@modern="path/to/arabic.jsonl" \
  --target eng@modern="path/to/english.jsonl" \
  --models semantic form --topk 200 --max-out 200 --limit 200

# API backend (no local GPU needed, uses Gemini embedding-001)
pip install -r requirements.api.txt
set GOOGLE_API_KEY=your_key
python "scripts/discovery/run_discovery_retrieval.py" \
  --backend api \
  --source ara@modern="path/to/arabic.jsonl" \
  --target eng@modern="path/to/english.jsonl" \
  --models semantic form --topk 200 --max-out 200 --limit 200
```

Corpus spec format: `<lang>[@<stage>]=<path>`

Outputs are written to `outputs/leads/` and embeddings/index caches to `outputs/`.

## Benchmark Workflow

Evaluate a run against one or more benchmarks:

```bash
python "scripts/discovery/evaluate.py" \
  "outputs/leads/discovery_YYYYMMDD_HHMMSS.jsonl" \
  --benchmark "resources/benchmarks/cognate_gold.jsonl"
```

Compare two runs directly:

```bash
python "scripts/discovery/evaluate.py" \
  "outputs/leads/new_run.jsonl" \
  --benchmark "resources/benchmarks/cognate_gold.jsonl" \
  --compare-to "outputs/leads/baseline_run.jsonl"
```

Check whether a benchmark is runnable against explicit corpora:

```bash
python "scripts/discovery/benchmark_coverage.py" \
  --benchmark "resources/benchmarks/cognate_gold.jsonl" \
  --source lat@classical="../Juthoor-DataCore-LV0/data/processed/latin/classical/sources/kaikki.jsonl" \
  --target grc@ancient="../Juthoor-DataCore-LV0/data/processed/ancient_greek/sources/kaikki.jsonl"
```

Materialize source/target benchmark slices:

```bash
python "scripts/discovery/materialize_benchmark_slice.py" \
  --benchmark "resources/benchmarks/cognate_gold.jsonl" \
  --source lat@classical="../Juthoor-DataCore-LV0/data/processed/latin/classical/sources/kaikki.jsonl" \
  --target grc@ancient="../Juthoor-DataCore-LV0/data/processed/ancient_greek/sources/kaikki.jsonl" \
  --output-dir "outputs/benchmark_slices/lat_grc_gold"
```

Train and apply a reranker:

```bash
python "scripts/discovery/train_reranker.py" \
  "outputs/leads/discovery_YYYYMMDD_HHMMSS.jsonl" \
  --benchmark "resources/benchmarks/cognate_gold.jsonl" \
  --output "outputs/models/reranker.json"

python "scripts/discovery/apply_reranker.py" \
  "outputs/leads/discovery_YYYYMMDD_HHMMSS.jsonl" \
  --model "outputs/models/reranker.json" \
  --output "outputs/leads/discovery_YYYYMMDD_HHMMSS_reranked.jsonl"
```

Build the Arabic root-family corpus used by the new root-family retrieval mode:

```bash
python "scripts/discovery/build_root_family_corpus.py"
```

## Current Benchmark Status

**Gold benchmark: 126 pairs across 5 categories**

| Category | Pairs | Notes |
|----------|-------|-------|
| Arabic-Hebrew | 55 | Semitic cognates |
| Arabic-English | 23 | Cross-family, incl. "Beyond the Word" research |
| Arabic-Persian | 20 | Arabic loanwords into Persian |
| Arabic-Aramaic | 18 | Sister Semitic languages |
| Latin-Greek | 10 | Indo-European control group |

**Negative pairs:** 33 (zero-consonant-overlap only)

**GenomeScorer (family-aware):**
- Cross-lingual consonant mapping for Arabic ↔ Hebrew, Aramaic, and Persian
- Bonuses are applied only for Semitic-Semitic pairs (family-aware gating)
- Phonetic merger tables covering 6 languages (66 entries)
- Arabic→English consonant shifts documented: ج↔K, ب↔F, د↔T, ق↔C
- Benchmark corrections based on phonetic merger principle (see `BENCHMARK_CORRECTIONS.md`)

**Reranker:** logistic model with 11 features; `genome_bonus` is the 11th feature (backward compatible).

**Multi-pair evaluation results (genome impact):**

| Language pair | MRR delta | Notes |
|---------------|-----------|-------|
| Arabic-Hebrew | +0.029 | Recall@10 +0.108 |
| Arabic-Aramaic | +0.109 | Strongest genome effect |
| Arabic-Persian | 0 | Expected — loanwords, no consonant drift |

- Reranking is not universally helpful; it should be treated as language-pair-specific and benchmark-gated.
- Latin-Greek gold slice: `10/10` gold pairs are currently runnable with existing corpora, and the baseline retrieval is already perfect on that slice.

## Evidence Cards

LV2 lead rows now carry an `evidence_card` object. The goal is to show each candidate as explainable historical evidence, not only as a scalar score.

Each card includes:

- surface forms
- transliteration
- IPA
- literal consonantal skeleton
- correspondence-class trace
- gloss fields
- score breakdown by channel
- correspondence note
- generated `why_this_candidate`
- candidate category

## Contributing

See `CONTRIBUTING.md`.

## Contact

For collaboration: `yassine.temessek@hotmail.com`
