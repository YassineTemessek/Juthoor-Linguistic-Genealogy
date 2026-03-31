# Juthoor Linguistic Genealogy

[![CI](https://github.com/YassineTemessek/Juthoor-Linguistic-Genealogy/actions/workflows/ci.yml/badge.svg)](https://github.com/YassineTemessek/Juthoor-Linguistic-Genealogy/actions/workflows/ci.yml)

### Tracing the DNA of Human Language

**Juthoor** (Arabic: جذور *Roots*) is a computational linguistics research engine investigating whether the Arabic triconsonantal root system preserves the structure of an ancestral tongue older than both Classical Arabic and Proto-Indo-European (PIE).

The core thesis: Arabic's 28-consonant phonemic inventory and root-template morphology represent a **high-resolution preservation** of a deep ancestral system. Indo-European languages are lower-resolution projections of this system, where pharyngeal, emphatic, and uvular consonants were deleted or merged. The project builds computational evidence for this hypothesis through cross-lingual cognate discovery, systematic phonetic correspondence mapping, and convergent multi-language analysis.

This monorepo consolidates the full stack: LV0 data ingestion, LV1 Arabic genome construction, LV2 cognate discovery, and LV3 theory synthesis toward an alternative model of language origins.

## Supported Deployment Model

Juthoor is supported as a **monorepo checkout with editable installs**.

- Clone the full repository and install the workspace packages with `uv pip install -e . -e Juthoor-DataCore-LV0 -e Juthoor-ArabicGenome-LV1 -e Juthoor-CognateDiscovery-LV2 -e Juthoor-Origins-LV3`
- Treat the repo-root `outputs/` directory as the canonical location for shared cross-level artifacts such as `cognate_graph.json`
- Do not treat the individual LV packages as standalone PyPI-style distributions; several runtime paths intentionally assume the full monorepo checkout and shared data/outputs layout

Wheel builds in CI are kept for workspace integrity checks, not as a promise of standalone package portability.

---

## Project Status

| Level | Module | Current status |
| :--- | :--- | :--- |
| **LV0** | **[Juthoor-DataCore-LV0](./Juthoor-DataCore-LV0)** | ~2.64M lexemes across 12 languages (Arabic, English, Latin, Ancient Greek, Hebrew, Persian, Aramaic, Old/Middle English, Quranic Arabic). Foundation layer complete. 167 tests. |
| **LV1** | **[Juthoor-ArabicGenome-LV1](./Juthoor-ArabicGenome-LV1)** | Research Factory complete: 12,333 roots, 4 hypotheses supported (H2, H5, H8, H12). Promoted evidence cards feed LV2. 498 tests. |
| **LV2** | **[Juthoor-CognateDiscovery-LV2](./Juthoor-CognateDiscovery-LV2)** | Operational — forward (Arabic→target, 7 languages) + reverse (target→Arabic) discovery pipelines. 54K-key reverse index, 1,889-pair gold benchmark, 47,071-edge cognate graph, 32.1% gold coverage. 498 tests. |
| **LV3** | **[Juthoor-Origins-LV3](./Juthoor-Origins-LV3)** | Theory synthesis active: building toward an alternative to PIE reconstruction based on convergent Arabic-IE evidence from 153 cross-language root families. 10 corridor cards, 14,494 validated leads. |

## Architecture & Layers

| Level | Module | Description |
| :--- | :--- | :--- |
| **LV0** | **[Juthoor-DataCore-LV0](./Juthoor-DataCore-LV0)** | **The Foundation.** Data engine that ingests, normalizes, validates, and packages canonical lexical datasets for the rest of the stack. |
| **LV1** | **[Juthoor-ArabicGenome-LV1](./Juthoor-ArabicGenome-LV1)** | **The Genome & Research Factory.** Models Arabic binary nuclei and triliteral roots, scores composition models, and exports promoted theory assets. |
| **LV2** | **[Juthoor-CognateDiscovery-LV2](./Juthoor-CognateDiscovery-LV2)** | **The Laboratory.** Cross-lingual cognate discovery engine using semantic retrieval, character-form retrieval, genome-informed scoring, and benchmarked reranking. |
| **LV3** | **[Juthoor-Origins-LV3](./Juthoor-Origins-LV3)** | **The Theory.** Synthesis of convergent evidence into an alternative model of language origins — proposing an ancestral tongue older than both Classical Arabic and PIE, preserved best in the Arabic root system. |

---

## Getting Started

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) or standard pip

### Installation

```bash
git clone https://github.com/YassineTemessek/Juthoor-Linguistic-Genealogy.git
cd Juthoor-Linguistic-Genealogy

uv venv .venv --python 3.11
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

uv pip install -e . -e Juthoor-DataCore-LV0 -e Juthoor-ArabicGenome-LV1 -e Juthoor-CognateDiscovery-LV2 -e Juthoor-Origins-LV3
uv pip install "juthoor-cognatediscovery-lv2[embeddings]"
```

### Running Tests

```bash
pytest Juthoor-DataCore-LV0/tests/ Juthoor-ArabicGenome-LV1/tests/ Juthoor-CognateDiscovery-LV2/tests/ -v -m "not slow"
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
python Juthoor-ArabicGenome-LV1/scripts/canon/build_lv1_theory_assets.py
python scripts/generate_lv1_dashboard.py
```

**3. Discovery (LV2)**
```bash
# Reverse discovery — recommended (target → Arabic)
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_reverse_discovery.py --target ang --no-semantic
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_reverse_discovery.py --target lat --limit 5000

# Forward multilang discovery
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_multilang.py --source ara --target lat --fast --limit 500
```

**4. Evaluate / Benchmark (LV2)**
```bash
# Direct gold pair scoring for any language pair
python Juthoor-CognateDiscovery-LV2/scripts/discovery/evaluate_gold_pairs_multilang.py --source ara --target lat
```

---

## Supported Languages

The discovery stack can query any language supported by the embedding backend, but the following languages currently have active LV0 data and benchmark usage:

| Category | Languages |
| :--- | :--- |
| **Modern Semitic** | Arabic (`ara`), Hebrew (`heb`) |
| **Classical/Ancient Semitic** | Quranic Arabic (`ar-qur`), Aramaic (`arc`) |
| **Indo-Iranian** | Persian (`fa`) |
| **Indo-European (Ancient)** | Latin (`lat`), Ancient Greek (`grc`) |
| **Indo-European (Germanic)** | Modern English (`en`), Middle English (`enm`), Old English (`ang`) |

---

## Technologies & Methodology

| Technology | Description |
| :--- | :--- |
| **[BGE-M3](https://huggingface.co/BAAI/bge-m3)** | Multilingual semantic embeddings |
| **[ByT5](https://huggingface.co/google/byt5-small)** | Byte-level form similarity |
| **[FAISS](https://github.com/facebookresearch/faiss)** | Vector similarity search |
| **Hybrid Scoring** | Combined orthographic, phonetic, skeletal, semantic, and correspondence-aware evidence |
| **GenomeScorer** | LV1-informed cross-lingual bonus layer with promoted binary-root evidence |

---

## Repository Structure

```
Juthoor-Linguistic-Genealogy/
├── Juthoor-DataCore-LV0/
├── Juthoor-ArabicGenome-LV1/
├── Juthoor-CognateDiscovery-LV2/
├── Juthoor-Origins-LV3/
├── Resources/
├── outputs/
├── docs/
└── README.md
```

## Documentation

- **[LV1 Complete Overview](./docs/LV1_COMPLETE_OVERVIEW.md)**: Arabic genome and research-factory overview.
- **[Data Flow](./docs/RAW_DATA_FLOW.md)**: Resource-to-processed-data flow.
- **[Progress Log](./docs/PROGRESS_LOG.md)**: Project milestone log.
- **[LV2 Benchmarks](./Juthoor-CognateDiscovery-LV2/resources/benchmarks/README.md)**: Evaluation assets and workflow.
- **[Status Tracker](./docs/plans/STATUS_TRACKER.md)**: Resume point after interruptions.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

**Author:** Yassine Temessek
