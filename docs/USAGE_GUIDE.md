# Juthoor Usage Guide

A step-by-step guide to using the Juthoor Linguistic Genealogy pipeline, from raw data to discovery results.

---

## Prerequisites

- Python 3.10+ (3.11 recommended)
- [uv](https://github.com/astral-sh/uv) or pip

```bash
# From the monorepo root
uv venv .venv --python 3.11
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # Linux/macOS

# Install core packages
uv pip install -e . -e Juthoor-DataCore-LV0 -e Juthoor-CognateDiscovery-LV2

# Install ML embeddings (BGE-M3 + ByT5, cross-platform)
uv pip install "juthoor-cognatediscovery-lv2[embeddings]"
```

---

## Step 1: Prepare Raw Data

Place your raw language datasets under `Juthoor-DataCore-LV0/data/raw/`:

```
data/raw/
  arabic/
    quran-morphology/quran-morphology.txt
    word_root_map.csv
    arabic_roots_hf/train-00000-of-00001.parquet
  english/
    ipa-dict/data/en_US.txt
    cmudict/cmudict.dict
  wiktionary_extracted/
    ...StarDict dictionaries...
```

A helper script can set up symlinks to a shared `Resources/` folder:

```powershell
# Windows
powershell scripts/setup_raw_links.ps1
```

---

## Step 2: LV0 -- Data Ingestion & Canonicalization

LV0 turns raw sources into clean, canonical JSONL files. It provides the `ldc` CLI.

### Build everything

```bash
ldc ingest --all
```

This runs ~30 ingest steps: parsing, normalizing, enriching (IPA, transliteration, POS), merging, and producing canonical lexeme tables.

### Build specific datasets only

```bash
ldc ingest --only quran_morphology --only arabic_hf_roots
```

### Validate outputs

```bash
ldc validate --all --require-files
```

### Package release bundles

```bash
ldc package --version 2025.12.19
```

### Fetch pre-built releases (skip local build)

```bash
ldc fetch --release latest --dest ./data/processed/
```

### Key outputs

| File | Description |
|------|-------------|
| `data/processed/quranic_arabic/lexemes.jsonl` | Canonical Quranic Arabic lexemes |
| `data/processed/arabic/classical/lexemes.jsonl` | Canonical classical Arabic lexemes |
| `data/processed/english/english_ipa_merged_pos.jsonl` | English with IPA + POS |
| `data/processed/wiktionary_stardict/filtered/*.jsonl` | Latin, Greek bilingual entries |

---

## Step 3: LV1 -- Arabic Genome (Binary Root Analysis)

LV1 studies how Arabic 3-letter roots group around deeper 2-letter (binary) nuclei. It consumes LV0 outputs.

### Cluster words by binary root

```bash
cd Juthoor-ArabicGenome-LV1
python scripts/cluster/cluster_by_binary_root.py
```

### Compare binary vs tri-root groupings

```bash
python scripts/analysis/compare_binary_vs_triroot.py
```

### Export root graph (nodes + edges)

```bash
python scripts/graph/export_binary_root_graph.py --input data/processed/arabic/classical/lexemes.jsonl
```

Outputs go to `outputs/clusters/`, `outputs/qa/`, and `outputs/graphs/`.

---

## Step 4: LV2 -- Cross-Language Cognate Discovery

LV2 is the main discovery engine. It supports two backends:

- **Local** (default): BGE-M3 + ByT5 on your machine (requires GPU or patience)
- **API**: Gemini embedding-001 via Google API (no local GPU, free tier available)

### Choose your backend

| | Local (`--backend local`) | API (`--backend api`) |
|---|---|---|
| **Models** | BGE-M3 + ByT5 | Gemini embedding-001 |
| **Quality** | MTEB 63.0 | MTEB 68.3 (higher) |
| **Requirements** | torch + ~2 GB download | `google-genai` + API key |
| **Cost** | Free (your hardware) | Free tier / $0.15 per 1M tokens |
| **Speed** | Fast with GPU, slow on CPU | Fast (cloud) |

### API backend setup

```bash
pip install -r requirements.api.txt
set GOOGLE_API_KEY=your_key_here   # Get free at https://ai.google.dev/
```

### Estimated API costs

| Corpus | Tokens (~) | Free tier | Paid ($0.15/1M) |
|--------|-----------|-----------|-----------------|
| Arabic + English (2 passes) | 2.2M | **Free** | $0.33 |
| + Latin + Greek (4 targets) | 4.5M | **Free** | $0.68 |
| Full Kaikki English (1.4M words) | 11M | **Free** | $1.65 |

Embeddings are cached to disk — re-runs cost nothing.

### Basic discovery run

```bash
cd Juthoor-CognateDiscovery-LV2

python scripts/discovery/run_discovery_retrieval.py \
  --source ara@modern="data/processed/arabic/classical/lexemes.jsonl" \
  --target eng@modern="data/processed/english/english_ipa_merged_pos.jsonl" \
  --models semantic form
```

The `--models semantic form` flag runs both BGE-M3 (semantic) and ByT5 (form) retrieval models.

### API discovery run (no local GPU)

```bash
python scripts/discovery/run_discovery_retrieval.py \
  --backend api \
  --source ara@modern="data/processed/arabic/classical/lexemes.jsonl" \
  --target eng@modern="data/processed/english/english_ipa_merged_pos.jsonl" \
  --models semantic form
```

Uses Gemini embedding-001 with `SEMANTIC_SIMILARITY` and `RETRIEVAL_DOCUMENT` task types.

### Corpus spec format

```
<lang>[@<stage>]=<path>
```

Examples:
- `ara@modern=path/to/arabic.jsonl`
- `eng@modern=path/to/english.jsonl`
- `lat@old=path/to/latin.jsonl`
- `grc@ancient=path/to/greek.jsonl`

### Common options

| Flag | Default | Description |
|------|---------|-------------|
| `--backend` | `local` | `local` (BGE-M3/ByT5) or `api` (Gemini embedding-001) |
| `--models` | `semantic form` | Which retrieval models (`semantic` = BGE-M3, `form` = ByT5) |
| `--semantic-model` | `BAAI/bge-m3` | HuggingFace model ID for semantic embeddings |
| `--form-model` | `google/byt5-small` | HuggingFace model ID for form embeddings |
| `--rebuild-index` | off | Force rebuild FAISS indexes |
| `--topk` | `200` | Top-K candidates per query |
| `--limit` | `0` | Limit rows loaded (0 = all) |
| `--max-out` | `200` | Max leads per source lexeme |
| `--device` | `cpu` | `cpu` or `cuda` |
| `--rebuild-cache` | off | Force recompute embeddings |
| `--no-hybrid` | off | Skip hybrid scoring after retrieval |

### Tuning hybrid weights

```bash
python scripts/discovery/run_discovery_retrieval.py \
  --source ara@modern=arabic.jsonl \
  --target eng@modern=english.jsonl \
  --w-semantic 0.5 --w-form 0.2 --w-orth 0.1 --w-sound 0.1 --w-skeleton 0.1
```

### Multi-language comparison

Run multiple targets:

```bash
python scripts/discovery/run_discovery_retrieval.py \
  --source ara@modern=arabic.jsonl \
  --target eng@modern=english.jsonl \
  --target lat@old=latin.jsonl \
  --target grc@ancient=greek.jsonl \
  --models semantic form --topk 100
```

### Key outputs

| Path | Description |
|------|-------------|
| `outputs/leads/discovery_*.jsonl` | Ranked candidate pairs with scores |
| `outputs/embeddings/<model>/<lang>/` | Cached embedding vectors |
| `outputs/indexes/<model>/<lang>/` | Cached FAISS indexes |

Each lead entry contains:
- Source and target lexeme data
- Per-model retrieval scores (semantic, form)
- Hybrid component scores (orthography, sound, skeleton)
- Combined weighted score

---

## Step 5: LV3 -- Theory & Validation (Blueprint)

LV3 is the theory layer. It consumes LV2 discovery outputs and defines how to test genealogical hypotheses. Currently documentation-only.

Key documents:
- `Master FoundationV3.2.md` -- Main theoretical framework
- `docs/CORRIDORS.md` -- Language corridor definitions
- `docs/ANCHOR_POLICY.md` -- Anchor pair policy
- `docs/VALIDATION_TRACK.md` -- Validation methodology

---

## Quran Corpus Analysis (Application)

A specialized analysis suite for the Quranic corpus.

```bash
cd Quran-Corpus-Analysis

# Build word-to-root map from Quranic morphology
python scripts/analysis/build_word_root_map.py
```

Additional analysis scripts live under `scripts/analysis/`.

---

## Quick Reference

```
Raw Data  -->  LV0 (ldc ingest)  -->  Canonical JSONL
                                          |
                    +---------------------+---------------------+
                    |                     |                     |
               LV1 (cluster)      LV2 (discovery)      QCA (Quran app)
               Binary roots       BGE-M3 + ByT5
               Graph exports      Ranked leads
                                       |
                                  LV3 (theory)
                                  Hypothesis testing
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| First run is slow | BGE-M3 (~2 GB) and ByT5 (~300 MB) download on first use. Subsequent runs use cache. |
| `torch` not found | Install embeddings extras: `pip install -r requirements.embeddings.txt` |
| CUDA out of memory | Use `--device cpu` or reduce `--limit` |
| Stale embeddings | Pass `--rebuild-cache` to recompute, `--rebuild-index` to rebuild FAISS indexes |

---

## Running Tests

```bash
# From monorepo root -- all fast tests
pytest tests/ -v -m "not slow"

# With coverage
pytest tests/ -v --cov=Juthoor-DataCore-LV0/src --cov=Juthoor-CognateDiscovery-LV2/src
```
