# Juthoor Usage Guide

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      JUTHOOR PIPELINE                               │
└─────────────────────────────────────────────────────────────────────┘

  Resources/                            Raw CSVs, Parquet, StarDict,
  (raw data)                            Kaikki JSONL, Quran morphology
       │
       ▼
  ┌───────────┐     ldc ingest          Canonical JSONL per language
  │    LV0    │ ─────────────────►      data/processed/{lang}/lexemes.jsonl
  │  DataCore │     --all               (Arabic, English, Latin, Greek...)
  └───────────┘
       │
       ├────────────────┬──────────────────────────┐
       ▼                ▼                          ▼
  ┌───────────┐   ┌───────────┐             ┌───────────┐
  │    LV1    │   │    LV2    │             │    QCA    │
  │  Arabic   │   │  Cognate  │             │   Quran   │
  │  Genome   │   │ Discovery │             │  Analysis │
  └───────────┘   └───────────┘             └───────────┘
  Binary root      Ranked leads              Word-root maps
  clusters         discovery_*.jsonl         Co-occurrence
  Root graphs      + hybrid scores           Semantic fields
       │                │
       └───────┬────────┘
               ▼
          ┌───────────┐
          │    LV3    │     Validated corridors
          │  Origins  │     Genealogical mapping
          └───────────┘     (future implementation)
```

### What Each Level Does

| Level | Name | What It Does | Status |
|-------|------|-------------|--------|
| **LV0** | DataCore | Ingests raw data → clean canonical JSONL per language | Done |
| **LV1** | Arabic Genome | Groups Arabic words by 2-letter root nucleus, exports graphs | Done |
| **LV2** | Cognate Discovery | AI-powered cross-language matching using embeddings + hybrid scoring | Done |
| **LV3** | Origins | Tests genealogical hypotheses using LV1+LV2 outputs | Blueprint |
| **QCA** | Quran Analysis | Semantic analysis of Quranic text (word relationships, co-occurrence) | Done |

---

## Quick Start (3 Commands)

```bash
# 1. Install
uv pip install -e . -e Juthoor-DataCore-LV0 -e Juthoor-CognateDiscovery-LV2

# 2. Ingest raw data → canonical JSONL
ldc ingest --all

# 3. Discover cognates (interactive — no flags needed)
cd Juthoor-CognateDiscovery-LV2
python scripts/discovery/run_discovery_retrieval.py
```

The interactive wizard guides you through backend selection, corpus picking, and cost estimation.

---

## What Goes In, What Comes Out

### LV0: Raw Data → Canonical JSONL

**In:** Raw files from `Resources/`

| Source | Format | Language |
|--------|--------|----------|
| Quran morphology | TXT | Arabic (Quranic) |
| Arabic roots (HuggingFace) | Parquet | Arabic |
| IPA Dict + CMUDict | TXT/Dict | English |
| Kaikki (Wiktionary) | JSONL | English, Latin, Greek |
| StarDict dictionaries | Binary | 15+ languages |

**Out:** `data/processed/{lang}/lexemes.jsonl` — one row per lexeme:

```json
{
  "id": "ara-qur:lemma:001",
  "language": "ara",
  "lemma": "ذهب",
  "translit": "dhahaba",
  "ipa": "/ðɑˈhɑbɑ/",
  "root": "ذ-ه-ب",
  "binary_root": "ذ-ه",
  "pos": "VERB"
}
```

### LV1: Canonical Arabic → Root Clusters + Graphs

**In:** `data/processed/arabic/classical/lexemes.jsonl`

**Out:**
- `outputs/clusters/binary_root_clusters.jsonl` — words grouped by 2-letter nucleus
- `outputs/graphs/{nodes.jsonl, edges.jsonl}` — root relationship graph

### LV2: Canonical JSONL (any languages) → Ranked Cognate Leads

**In:** Any LV0 canonical JSONL files (source + target languages)

**Out:** `outputs/leads/discovery_<timestamp>.jsonl` — ranked candidate pairs:

```json
{
  "source": {"lemma": "كتاب", "lang": "ara", "ipa": "/kitaːb/"},
  "target": {"lemma": "book",  "lang": "eng", "ipa": "/bʊk/"},
  "scores": {"semantic": 0.82, "form": 0.31},
  "hybrid": {
    "combined_score": 0.71,
    "orthography": 0.45,
    "sound": 0.52,
    "skeleton": 0.60
  },
  "category": "strong_union"
}
```

### QCA: Quranic JSONL → Semantic Analysis

**In:** `data/processed/quranic_arabic/lexemes.jsonl`

**Out:** Word-root maps, co-occurrence analysis, semantic field clustering

---

## Detailed Steps

### Step 1: Prerequisites

```bash
# Python 3.10+ (3.11 recommended)
uv venv .venv --python 3.11
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # Linux/macOS

# Install core packages
uv pip install -e . -e Juthoor-DataCore-LV0 -e Juthoor-CognateDiscovery-LV2
```

### Step 2: LV0 — Data Ingestion

Place raw data under `Juthoor-DataCore-LV0/data/raw/` (or use symlinks):

```bash
powershell scripts/setup_raw_links.ps1   # Windows: create symlinks to Resources/

ldc ingest --all                          # Build all canonical JSONL
ldc validate --all --require-files        # Validate outputs
```

Key outputs in `data/processed/`:
- `arabic/quran_lemmas_enriched.jsonl` — Quranic Arabic
- `english/english_ipa_merged_pos.jsonl` — English with IPA + POS
- `wiktionary_stardict/filtered/*.jsonl` — Latin, Greek, etc.

### Step 3: LV1 — Arabic Genome (Optional)

```bash
cd Juthoor-ArabicGenome-LV1
python scripts/cluster/cluster_by_binary_root.py
python scripts/graph/export_binary_root_graph.py --input data/processed/arabic/classical/lexemes.jsonl
```

### Step 4: LV2 — Cognate Discovery

#### Interactive mode (recommended)

```bash
cd Juthoor-CognateDiscovery-LV2
python scripts/discovery/run_discovery_retrieval.py
```

The wizard walks you through:
1. **Backend**: Local (BGE-M3 + ByT5) or API (Gemini, no GPU)
2. **Source corpus**: Select from discovered JSONL files
3. **Target corpus(es)**: Multi-select
4. **Models**: Semantic + form, or one only
5. **Cost estimate** (API): Shows tokens, cost, and asks for confirmation

#### CLI mode

```bash
# Local backend
python scripts/discovery/run_discovery_retrieval.py \
  --source ara@modern="data/processed/arabic/quran_lemmas_enriched.jsonl" \
  --target eng@modern="data/processed/english/english_ipa_merged_pos.jsonl" \
  --models semantic form

# API backend (no GPU needed)
python scripts/discovery/run_discovery_retrieval.py \
  --backend api \
  --source ara@modern="data/processed/arabic/quran_lemmas_enriched.jsonl" \
  --target eng@modern="data/processed/english/english_ipa_merged_pos.jsonl" \
  --models semantic form

# Multi-language, skip confirmation
python scripts/discovery/run_discovery_retrieval.py \
  --backend api -y \
  --source ara@modern=arabic.jsonl \
  --target eng@modern=english.jsonl \
  --target lat@old=latin.jsonl \
  --target grc@ancient=greek.jsonl
```

#### Backend comparison

| | Local (`--backend local`) | API (`--backend api`) |
|---|---|---|
| **Models** | BGE-M3 + ByT5 | Gemini embedding-001 (pinned) |
| **Quality** | MTEB 63.0 | MTEB 68.3 (higher) |
| **Requires** | torch + ~2 GB download | `google-genai` + API key |
| **Cost** | Free (your hardware) | Free tier / $0.15 per 1M tokens |
| **Speed** | Fast with GPU, slow on CPU | Fast (cloud) |

#### API setup

```bash
pip install -r requirements.api.txt
set GOOGLE_API_KEY=your_key_here   # Get free at https://ai.google.dev/
```

#### Cost estimation

The script shows a cost preview before any API call:

```
+==================================================+
|           Gemini API Cost Estimate                |
+==================================================+
| Corpora        : ara:modern (1,200) + eng:modern (5,000)
| Model passes   : 2 (semantic + form)
| Total texts    : 12,400
| Est. tokens    : ~14,880
| Est. cost      : FREE (within 3.5M free tier)
| Model          : gemini-embedding-001
+==================================================+
Proceed? [Y/n]:
```

Use `-y` to skip in scripts. Model is pinned to `gemini-embedding-001` — a warning appears if overridden.

#### Reference costs

| Corpus | Tokens (~) | Free tier | Paid ($0.15/1M) |
|--------|-----------|-----------|-----------------|
| Arabic + English (2 passes) | 2.2M | **Free** | $0.33 |
| + Latin + Greek (4 targets) | 4.5M | **Free** | $0.68 |
| Full Kaikki English (1.4M words) | 11M | **Free** | $1.65 |

Embeddings cached to disk — re-runs cost nothing.

#### CLI reference

| Flag | Default | Description |
|------|---------|-------------|
| `--backend` | `local` | `local` or `api` |
| `--models` | `semantic form` | Retrieval models |
| `--topk` | `200` | Top-K candidates |
| `--max-out` | `200` | Max leads per source |
| `--limit` | `0` | Row limit (0 = all) |
| `--device` | `cpu` | `cpu` or `cuda` |
| `-y` / `--yes` | off | Skip cost confirmation |
| `--rebuild-cache` | off | Recompute embeddings |
| `--rebuild-index` | off | Rebuild FAISS indexes |
| `--no-hybrid` | off | Skip hybrid scoring |

### Step 5: LV3 — Theory & Validation (Blueprint)

Consumes LV2 leads to validate genealogical hypotheses. Currently documentation-only.

Key docs: `Master FoundationV3.2.md`, `docs/CORRIDORS.md`, `docs/ANCHOR_POLICY.md`, `docs/VALIDATION_TRACK.md`.

### QCA — Quran Corpus Analysis

```bash
cd Quran-Corpus-Analysis
python scripts/analysis/build_word_root_map.py
```

---

## Understanding Your Results

The discovery output (`outputs/leads/discovery_*.jsonl`) contains one JSON object per line:

| Field | Meaning |
|-------|---------|
| `source.lemma` | The source word being searched |
| `target.lemma` | A candidate match in the target language |
| `scores.semantic` | Meaning similarity (0–1, higher = more similar) |
| `scores.form` | Orthographic/form similarity (0–1) |
| `hybrid.combined_score` | Weighted blend of all signals |
| `hybrid.orthography` | Character-level similarity |
| `hybrid.sound` | IPA phonetic similarity |
| `hybrid.skeleton` | Consonant skeleton match |
| `category` | `strong_union` (both models agree), `semantic_only`, or `form_only` |

**Filtering tips:**
- `combined_score > 0.70` → high-confidence leads
- `category == "strong_union"` → both semantic and form agree
- Sort by `combined_score` descending for best matches first

---

## Docker & Containerization

The pipeline is CLI-only (no web server, no ports).

### Volume mounts

```yaml
volumes:
  - ./data/processed:/app/data/processed     # Input corpora
  - ./outputs:/app/outputs                   # Cache + results
  - ./resources:/app/resources               # Reference data
```

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | API backend only | From https://ai.google.dev/ |
| `LV2_DEVICE` | No | `cpu` (default) or `cuda` |

### Example Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app

# API backend (lightweight, no torch)
RUN pip install --no-cache-dir -e . \
    -e Juthoor-DataCore-LV0 \
    -e Juthoor-CognateDiscovery-LV2 \
    && pip install --no-cache-dir -r Juthoor-CognateDiscovery-LV2/requirements.api.txt

# For local backend, add: RUN pip install "juthoor-cognatediscovery-lv2[embeddings]"

ENTRYPOINT ["python", "Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_retrieval.py"]
```

### Example docker-compose.yml

```yaml
services:
  discovery:
    build: .
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    volumes:
      - ./Juthoor-CognateDiscovery-LV2/data/processed:/app/Juthoor-CognateDiscovery-LV2/data/processed
      - ./Juthoor-CognateDiscovery-LV2/outputs:/app/Juthoor-CognateDiscovery-LV2/outputs
    command: >
      --backend api -y
      --source ara@modern=data/processed/arabic/quran_lemmas_enriched.jsonl
      --target eng@modern=data/processed/english/english_ipa_merged_pos.jsonl
      --models semantic form
```

### What to update for Docker

1. **Paths**: Use paths relative to `/app` (same as repo structure)
2. **API key**: Pass via `environment` or `--env-file .env`
3. **Mount `outputs/`**: So results persist after container stops
4. **No port mapping**: CLI tool, not a web server

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| First run is slow | BGE-M3 (~2 GB) + ByT5 (~300 MB) download on first use. Cached after. |
| `torch` not found | `pip install -r requirements.embeddings.txt` |
| CUDA out of memory | `--device cpu` or `--limit 1000` |
| Stale embeddings | `--rebuild-cache` + `--rebuild-index` |
| `google.genai` not found | `pip install -r requirements.api.txt` |
| Model warning | Non-default Gemini model. Use `gemini-embedding-001`. |

---

## Running Tests

```bash
pytest tests/ -v -m "not slow"          # Fast tests (~1s)
pytest tests/ -v                        # All tests (includes model loading)
```
