# Juthoor Linguistic Genealogy 🌳
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
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (Recommended) or standard pip

### Installation

This project is configured as a Python Workspace. You can install all dependencies for all levels in one command.

```bash
# Clone the repository
git clone https://github.com/YassineTemessek/Juthoor-Linguistic-Genealogy.git
cd Juthoor-Linguistic-Genealogy

# Create a virtual environment and install (editable mode)
uv pip install -e .
```

### Running the Pipeline

**1. Data Ingestion (LV0)**
```bash
# Fetch and canonicalize the core datasets
ldc ingest --all
```

**2. Discovery (LV2)**
To run a cross-lingual comparison (e.g., Arabic vs. English):
```bash
python scripts/discovery/run_discovery_retrieval.py \
  --source ara@modern \
  --target eng@modern \
  --models sonar canine
```

---

## 🛠️ Technologies & Methodology

*   **Graph Theory:** Modeling language roots as connected graph networks.
*   **Vector Embeddings:** Using **SONAR** text embeddings for language-agnostic semantic retrieval.
*   **Morphological Analysis:** Custom algorithms for decomposing Semitic roots.
*   **Hybrid Scoring:** A weighted scoring system combining orthographic (spelling), phonetic (sound), and semantic (meaning) similarity.

---

## 📚 Documentation

- **[Project Overview](./docs/PROJECT_OVERVIEW.md)**: Detailed breakdown of the workspace and logic.
- **[Data Flow](./docs/RAW_DATA_FLOW.md)**: How data moves from raw resources to canonical JSONL.
- **[Progress Log](./docs/PROGRESS_LOG.md)**: Tracking the development milestones.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Author:** Yassine Temessek
