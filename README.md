# Juthoor Linguistic Genealogy

[![CI](https://github.com/YassineTemessek/Juthoor-Linguistic-Genealogy/actions/workflows/ci.yml/badge.svg)](https://github.com/YassineTemessek/Juthoor-Linguistic-Genealogy/actions/workflows/ci.yml)

### Tracing the DNA of Human Language

**Juthoor** (Arabic: *Roots*) is a computational linguistics engine designed to decode the genealogical relationships between world languages, with a primary hypothesis centered on the Arabo-Semitic root system as a fundamental "linguistic genome."

This monorepo consolidates a multi-layered research stack -- from raw data ingestion to theoretical synthesis -- into a unified Python workspace.

---

## Architecture & Layers

| Level | Module | Description |
| :--- | :--- | :--- |
| **LV0** | **[Juthoor-DataCore-LV0](./Juthoor-DataCore-LV0)** | **The Foundation.** A robust data engine that ingests, normalizes, and canonizes lexical data from diverse sources (Wiktionary, Lane, Taj al-Arus, Khorsi). Single source of truth. |
| **LV1** | **[Juthoor-ArabicGenome-LV1](./Juthoor-ArabicGenome-LV1)** | **The Genome.** Decodes the **biconsonantal (2-letter) root system**. Maps the "atomic meanings" of Arabic sounds and generates the binary root graph. |
| **LV2** | **[Juthoor-CognateDiscovery-LV2](./Juthoor-CognateDiscovery-LV2)** | **The Laboratory.** AI-powered discovery engine using **BGE-M3** (semantic search) and **ByT5** (character-level matching) to find and rank cross-lingual cognates (English, Greek, Latin vs. Arabic). |
| **LV3** | **[Juthoor-Origins-LV3](./Juthoor-Origins-LV3)** | **The Theory.** Synthesis layer testing genealogical hypotheses, mapping global language corridors, and reconstructing the "Origin" model. |
| **App** | **[Quran-Corpus-Analysis](./Quran-Corpus-Analysis)** | **The Application.** Semantic analysis suite for the Quranic corpus using root-based associations. |

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
# Run all tests across all levels (356 tests, excluding slow model-loading tests)
pytest Juthoor-DataCore-LV0/tests/ Juthoor-ArabicGenome-LV1/tests/ Juthoor-CognateDiscovery-LV2/tests/ -v -m "not slow"

# Run a single level
pytest Juthoor-DataCore-LV0/tests/ -v
```

### Running the Pipeline

**1. Data Ingestion (LV0)**
```bash
ldc ingest --all
```

**2. Arabic Genome (LV1)**
```bash
python Juthoor-ArabicGenome-LV1/scripts/build_genome_phase1.py
python Juthoor-ArabicGenome-LV1/scripts/build_genome_phase2.py
```

**3. Discovery (LV2)**
```bash
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_retrieval.py
# Interactive wizard guides you through corpus and model selection
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
| **Hybrid Scoring** | Weighted combination of orthographic, phonetic, skeletal, and semantic similarity |
| **Graph Theory** | Modeling language roots as connected graph networks |

---

## Documentation

- **[Project Overview](./docs/PROJECT_OVERVIEW.md)**: Detailed breakdown of the workspace and logic.
- **[Data Flow](./docs/RAW_DATA_FLOW.md)**: How data moves from raw resources to canonical JSONL.
- **[Progress Log](./docs/PROGRESS_LOG.md)**: Tracking the development milestones.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Author:** Yassine Temessek
