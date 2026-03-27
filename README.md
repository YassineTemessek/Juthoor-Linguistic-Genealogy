# Juthoor Linguistic Genealogy

[![CI](https://github.com/YassineTemessek/Juthoor-Linguistic-Genealogy/actions/workflows/ci.yml/badge.svg)](https://github.com/YassineTemessek/Juthoor-Linguistic-Genealogy/actions/workflows/ci.yml)

### Tracing the DNA of Human Language

**Juthoor** (Arabic: *Roots*) is a computational linguistics engine designed to decode genealogical relationships between languages, with the Arabic root system treated as a measurable structural core rather than only a descriptive lexicographic artifact.

This monorepo consolidates the full stack: LV0 data ingestion, LV1 Arabic genome construction, LV2 cognate discovery, and LV3 theory synthesis.

---

## Project Status

| Level | Module | Current status |
| :--- | :--- | :--- |
| **LV0** | **[Juthoor-DataCore-LV0](./Juthoor-DataCore-LV0)** | ~2.64M lexemes across 11 languages (Arabic, English, Latin, Greek, Hebrew, Persian, Aramaic, Old/Middle English, Turkish, Akkadian). Foundation layer complete. |
| **LV1** | **[Juthoor-ArabicGenome-LV1](./Juthoor-ArabicGenome-LV1)** | Research Factory complete: 4 hypotheses supported (H2 field coherence >11sigma, H5 order matters, H8 positional semantics 86%, H12 meaning predictability cosine=0.716). 498 tests. |
| **LV2** | **[Juthoor-CognateDiscovery-LV2](./Juthoor-CognateDiscovery-LV2)** | Full discovery engine: 12-method scorer, 14-feature reranker, 7 language pairs, **47,071-edge cognate graph** across 7 languages. 1,889 gold benchmark pairs. 32.1% gold coverage. 394 tests. |
| **LV3** | **[Juthoor-Origins-LV3](./Juthoor-Origins-LV3)** | Theory bootstrap active: 10 corridor cards, 3-tier anchor gates, validation methodology, 14,494 validated leads flowing from LV2. Theory synthesis document written. |

## Architecture & Layers

| Level | Module | Description |
| :--- | :--- | :--- |
| **LV0** | **[Juthoor-DataCore-LV0](./Juthoor-DataCore-LV0)** | **The Foundation.** Data engine that ingests, normalizes, validates, and packages canonical lexical datasets for the rest of the stack. |
| **LV1** | **[Juthoor-ArabicGenome-LV1](./Juthoor-ArabicGenome-LV1)** | **The Genome & Research Factory.** Models Arabic binary nuclei and triliteral roots, scores composition models, and exports promoted theory assets. |
| **LV2** | **[Juthoor-CognateDiscovery-LV2](./Juthoor-CognateDiscovery-LV2)** | **The Laboratory.** Cross-lingual cognate discovery engine using semantic retrieval, character-form retrieval, genome-informed scoring, and benchmarked reranking. |
| **LV3** | **[Juthoor-Origins-LV3](./Juthoor-Origins-LV3)** | **The Theory.** Synthesis layer for broader genealogical hypotheses and origin-level interpretation. |

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

uv pip install -e . -e Juthoor-DataCore-LV0 -e Juthoor-ArabicGenome-LV1 -e Juthoor-CognateDiscovery-LV2
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
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_retrieval.py
```

**4. Evaluate / Benchmark (LV2)**
```bash
python Juthoor-CognateDiscovery-LV2/scripts/discovery/evaluate.py \
  Juthoor-CognateDiscovery-LV2/outputs/leads/discovery_YYYYMMDD_HHMMSS.jsonl \
  --benchmark Juthoor-CognateDiscovery-LV2/resources/benchmarks/cognate_gold.jsonl
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
