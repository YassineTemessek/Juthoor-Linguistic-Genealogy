# Juthoor Linguistic Genealogy

[![CI](https://github.com/YassineTemessek/Juthoor-Linguistic-Genealogy/actions/workflows/ci.yml/badge.svg)](https://github.com/YassineTemessek/Juthoor-Linguistic-Genealogy/actions/workflows/ci.yml)

### Tracing the DNA of Human Language

**Juthoor** (Arabic: *Roots*) is a computational linguistics engine designed to decode the genealogical relationships between world languages, with a primary hypothesis centered on the Arabo-Semitic root system as a fundamental "linguistic genome."

This monorepo consolidates a multi-layered research stack -- from raw data ingestion to theoretical synthesis -- into a unified Python workspace.

---

## Architecture & Layers

| Level | Module | Description |
| :--- | :--- | :--- |
| **LV0** | **[Juthoor-DataCore-LV0](./Juthoor-DataCore-LV0)** | **The Foundation.** Data engine that ingests, normalizes, and canonizes lexical data from diverse sources (Wiktionary, Lane, Taj al-Arus, Khorsi). Single source of truth for ~2.6M lexemes across 6 languages. |
| **LV1** | **[Juthoor-ArabicGenome-LV1](./Juthoor-ArabicGenome-LV1)** | **The Genome & Research Factory.** Decodes the biconsonantal root system (457 binary roots, 1,938 triliteral roots, 12,333 genome entries). Houses a computational research factory testing 12 formal hypotheses about Arabic sound-meaning structure across 19 experiments. |
| **LV2** | **[Juthoor-CognateDiscovery-LV2](./Juthoor-CognateDiscovery-LV2)** | **The Laboratory.** Cross-lingual cognate discovery engine using **BGE-M3** (semantic search), **ByT5** (character-level matching), correspondence-aware reranking, benchmark evaluation, and root-family retrieval. |
| **LV3** | **[Juthoor-Origins-LV3](./Juthoor-Origins-LV3)** | **The Theory.** Synthesis layer testing genealogical hypotheses, mapping global language corridors, and reconstructing the "Origin" model. |

---

## Getting Started

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or standard pip

### Installation

```bash
# Clone the repository
git clone https://github.com/YassineTemessek/Juthoor-Linguistic-Genealogy.git
cd Juthoor-Linguistic-Genealogy

# Create a virtual environment
uv venv .venv --python 3.11
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install core packages (editable mode)
uv pip install -e . -e Juthoor-DataCore-LV0 -e Juthoor-ArabicGenome-LV1 -e Juthoor-CognateDiscovery-LV2

# Install ML embeddings (cross-platform)
uv pip install "juthoor-cognatediscovery-lv2[embeddings]"
```

### Running Tests

```bash
# Run all tests across all levels (500+ tests, excluding slow model-loading tests)
pytest Juthoor-DataCore-LV0/tests/ Juthoor-ArabicGenome-LV1/tests/ Juthoor-CognateDiscovery-LV2/tests/ -v -m "not slow"

# Run a single level
pytest Juthoor-ArabicGenome-LV1/tests/ -v
```

### Running the Pipeline

**1. Data Ingestion (LV0)**
```bash
ldc ingest --all
```

**2. Arabic Genome (LV1)**
```bash
# Build the genome (Phase 1 brute grouping + Phase 2 Muajam overlay)
python Juthoor-ArabicGenome-LV1/scripts/build_genome_phase1.py
python Juthoor-ArabicGenome-LV1/scripts/build_genome_phase2.py

# Research Factory — compute features and run experiments
python Juthoor-ArabicGenome-LV1/scripts/research_factory/phase0_setup/compute_all_embeddings.py
python Juthoor-ArabicGenome-LV1/scripts/research_factory/phase0_setup/build_articulatory_vectors.py
```

**3. Discovery (LV2)**
```bash
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_retrieval.py
# Interactive wizard guides you through corpus and model selection
```

**4. Evaluate / Benchmark (LV2)**
```bash
python Juthoor-CognateDiscovery-LV2/scripts/discovery/evaluate.py \
  Juthoor-CognateDiscovery-LV2/outputs/leads/discovery_YYYYMMDD_HHMMSS.jsonl \
  --benchmark Juthoor-CognateDiscovery-LV2/resources/benchmarks/cognate_gold.jsonl
```

---

## Supported Languages

The discovery engine supports **60+ language codes** including:

| Category | Languages |
| :--- | :--- |
| **Modern Semitic** | Arabic (`ara`), Hebrew (`heb`), Amharic (`amh`), Maltese (`mlt`) |
| **Ancient Semitic** | Akkadian (`akk`), Phoenician (`phn`), Punic (`xpu`), Ugaritic (`uga`), Ge'ez (`gez`) |
| **Aramaic Variants** | Syriac (`syr`, `syc`), Imperial Aramaic (`arc`), Jewish Palestinian (`jpa`), Talmudic (`tmr`) |
| **Indo-European** | English (`eng`), Latin (`lat`), Greek (`ell`, `grc`), German (`deu`), French (`fra`), Spanish (`spa`) |
| **Quranic** | Quranic Arabic (`ar-qur`, `ara-qur`) |

---

## Technologies & Methodology

| Technology | Description |
| :--- | :--- |
| **[BGE-M3](https://huggingface.co/BAAI/bge-m3)** | Multilingual semantic embeddings (100+ languages, cross-platform, 1024-dim) |
| **[ByT5](https://huggingface.co/google/byt5-small)** | Byte-level tokenizer-free model for character/form-based similarity |
| **[FAISS](https://github.com/facebookresearch/faiss)** | Facebook's vector similarity search for fast nearest-neighbor retrieval |
| **Hybrid Scoring** | Weighted combination of orthographic, phonetic, skeletal, semantic, and correspondence-aware similarity |
| **Graph Theory** | Modeling language roots as connected graph networks |

---

## Showing Connections

The project should not present a candidate as only `score = 0.82`.
It should present each proposed Arabic-to-other-language link as an **evidence card**.

Each evidence card should expose:

- surface forms in script
- transliteration
- IPA / phonetic form
- root or consonantal skeleton
- semantic gloss
- correspondence explanation
- score breakdown

Example of a strong explanation:

- Arabic: `بيت` / `bayt`
- Hebrew: `בית` / `bayit`
- Gloss: `house`
- Skeleton: `byt` vs `byt`
- Shape similarity: high
- Phonetic similarity: high
- Semantic similarity: high
- Root-family support: yes
- Correspondence note: stable Semitic `b-y-t`

Example of a weaker explanation:

- Arabic: `قرن` / `qarn`
- English: `horn`
- Gloss: `horn`
- Skeleton: `qrn` vs `hrn`
- Shape similarity: medium
- Phonetic similarity: medium
- Semantic similarity: high
- Correspondence note: possible `q/h` corridor hypothesis
- Confidence: tentative, needs broader pattern support

The connection should be shown in parallel channels, not as one blended score:

1. surface shape
2. phonetic form
3. consonantal skeleton
4. correspondence classes
5. meaning

A good candidate should show **convergence of evidence**:

- at least moderate semantic proximity
- some form or phonetic support
- some consonantal or correspondence support
- ideally broader family or root support

Success means the system can:

1. retrieve plausible pairs
2. explain why they are plausible
3. separate real historical candidates from false friends and mere translations

---

## Documentation

- **[Project Overview](./docs/PROJECT_OVERVIEW.md)**: Detailed breakdown of the workspace and logic.
- **[Data Flow](./docs/RAW_DATA_FLOW.md)**: How data moves from raw resources to canonical JSONL.
- **[Progress Log](./docs/PROGRESS_LOG.md)**: Tracking the development milestones.
- **[LV2 Benchmarks](./Juthoor-CognateDiscovery-LV2/resources/benchmarks/README.md)**: Evaluation assets, coverage checks, and slice-generation workflow.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Author:** Yassine Temessek
