# Juthoor Linguistic Genealogy 🌳

[![CI](https://github.com/YassineTemessek/Juthoor-Linguistic-Genealogy/actions/workflows/ci.yml/badge.svg)](https://github.com/YassineTemessek/Juthoor-Linguistic-Genealogy/actions/workflows/ci.yml)

### Tracing the DNA of Human Language

**Juthoor** (Arabic: *Roots*) is a computational linguistics engine designed to decode the genealogical relationships between world languages, with a primary hypothesis centered on the Arabo-Semitic root system as a fundamental "linguistic genome."

This monorepo consolidates a multi-layered research stack—from raw data ingestion to theoretical synthesis—into a unified Python workspace.

---

## 🏗️ Architecture & Layers

The project is organized into a hierarchical stack where each level builds upon the intelligence of the previous one.

| Level | Module | Description |
| :--- | :--- | :--- |
| **LV0** | **[Juthoor-DataCore-LV0](./Juthoor-DataCore-LV0)** | **The Foundation.** A robust data engine that ingests, normalizes, and canonizes lexical data from diverse sources (Wiktionary, Lane, Taj al-Arus, Khorsi). It serves as the single source of truth. |
| **LV1** | **[Juthoor-ArabicGenome-LV1](./Juthoor-ArabicGenome-LV1)** | **The Genome.** Decodes the **biconsonantal (2-letter) root system**. It maps the "atomic meanings" of Arabic sounds and generates the binary root graph. |
| **LV2** | **[Juthoor-CognateDiscovery-LV2](./Juthoor-CognateDiscovery-LV2)** | **The Laboratory.** An AI-powered discovery engine using **Meta SONAR** (semantic search) and **Google CANINE** (character-level matching) to find and rank cross-lingual cognates (English, Greek, Latin vs. Arabic). |
| **LV3** | **[Juthoor-Origins-LV3](./Juthoor-Origins-LV3)** | **The Theory.** The synthesis layer. It tests genealogical hypotheses, maps global language corridors, and reconstructs the theoretical "Origin" model. |
| **App** | **[Quran-Corpus-Analysis](./Quran-Corpus-Analysis)** | **The Application.** A specialized semantic analysis suite focused on the Quranic corpus, utilizing the engines above to decode meaning through root-based associations. |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+ (3.11 recommended for full ML support)
- [uv](https://github.com/astral-sh/uv) (Recommended) or standard pip

### Installation

```bash
# Clone the repository
git clone https://github.com/YassineTemessek/Juthoor-Linguistic-Genealogy.git
cd Juthoor-Linguistic-Genealogy

# Create a virtual environment (Python 3.11 recommended)
uv venv .venv --python 3.11
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install core packages (editable mode)
uv pip install -e . -e Juthoor-DataCore-LV0 -e Juthoor-CognateDiscovery-LV2

# Install ML embeddings (platform-specific)
# Windows - CANINE only (SONAR requires Linux/macOS):
uv pip install "juthoor-cognatediscovery-lv2[canine]"

# Linux/macOS - Full embeddings (SONAR + CANINE):
uv pip install "juthoor-cognatediscovery-lv2[embeddings]"
```

### Running Tests

```bash
# Run all tests (excluding slow model-loading tests)
pytest tests/ -v -m "not slow"

# Run with coverage
pytest tests/ -v --cov=Juthoor-DataCore-LV0/src --cov=Juthoor-CognateDiscovery-LV2/src
```

### Running the Pipeline

**1. Data Ingestion (LV0)**
```bash
# Fetch and canonicalize the core datasets
ldc ingest --all
```

**2. Discovery (LV2)**
```bash
# Run a cross-lingual comparison (e.g., Arabic vs. English)
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_retrieval.py \
  --source ara@modern \
  --target eng@modern \
  --models sonar canine
```

---

## 🌍 Supported Languages

The discovery engine supports **60+ language codes** including:

| Category | Languages |
| :--- | :--- |
| **Modern Semitic** | Arabic (`ara`), Hebrew (`heb`), Amharic (`amh`), Maltese (`mlt`) |
| **Ancient Semitic** | Akkadian (`akk`), Phoenician (`phn`), Punic (`xpu`), Ugaritic (`uga`), Ge'ez (`gez`) |
| **Aramaic Variants** | Syriac (`syr`, `syc`), Imperial Aramaic (`arc`), Jewish Palestinian (`jpa`), Talmudic (`tmr`) |
| **Indo-European** | English (`eng`), Latin (`lat`), Greek (`ell`, `grc`), German (`deu`), French (`fra`), Spanish (`spa`) |
| **Quranic** | Quranic Arabic (`ar-qur`, `ara-qur`) |

Ancient languages are mapped to their closest living relative for embedding (e.g., Akkadian → Arabic, Phoenician → Hebrew).

---

## 🛠️ Technologies & Methodology

| Technology | Description |
| :--- | :--- |
| **[Meta SONAR](https://github.com/facebookresearch/SONAR)** | Multilingual semantic embeddings for meaning-based similarity (Linux/macOS only) |
| **[Google CANINE](https://huggingface.co/google/canine-c)** | Character-level transformer for form-based similarity (cross-platform) |
| **[FAISS](https://github.com/facebookresearch/faiss)** | Facebook's vector similarity search for fast nearest-neighbor retrieval |
| **Hybrid Scoring** | Weighted combination of orthographic, phonetic, skeletal, and semantic similarity |
| **Graph Theory** | Modeling language roots as connected graph networks |

---

## 📚 Documentation

- **[Project Overview](./docs/PROJECT_OVERVIEW.md)**: Detailed breakdown of the workspace and logic.
- **[Data Flow](./docs/RAW_DATA_FLOW.md)**: How data moves from raw resources to canonical JSONL.
- **[Progress Log](./docs/PROGRESS_LOG.md)**: Tracking the development milestones.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Author:** Yassine Temessek
