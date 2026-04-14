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

## Current Status (April 2026)

| Metric | Value |
| :--- | :--- |
| **Discoveries** | 907 Arabic-Greek/Latin cognate pairs (Greek: 854, Latin: 53) |
| **Pairs scored** | 55,694 via Eye 2 LLM semantic scoring |
| **Arabic roots** | 12,333 in genome (binary nuclei validated >11 sigma) |
| **Languages** | 12 in LV0 + Gothic and Old Irish queued for Wave 1 |
| **Tests** | 1,206 across LV0/LV1/LV2 |
| **Null model** | z=3.23 (partial signal, gate at 3.29 -- gloss quality fix pending) |
| **Scoring** | Hybrid: BGE-M3 semantic 50% + sound 22% + ByT5 form 18% + skeleton 5% |

## Project Status

| Level | Module | Current status |
| :--- | :--- | :--- |
| **LV0** | **[Juthoor-DataCore-LV0](./Juthoor-DataCore-LV0)** | ~2.76M lexemes across 12 languages. Gothic and Old Irish data downloaded for Wave 1 expansion. 167 tests. |
| **LV1** | **[Juthoor-ArabicGenome-LV1](./Juthoor-ArabicGenome-LV1)** | Research Factory complete: 12,333 roots, 4 hypotheses supported (H2, H5, H8, H12). Promoted evidence cards feed LV2. 498 tests. |
| **LV2** | **[Juthoor-CognateDiscovery-LV2](./Juthoor-CognateDiscovery-LV2)** | 907 discoveries across Greek and Latin. Eye 1 skeleton matching + Eye 2 LLM scoring operational. Hybrid scoring pipeline with tiered architecture planned (Tier 1 mechanical + Tier 2 sound laws + Tier 3 AI reasoning). 541 tests. |
| **LV3** | **[Juthoor-Origins-LV3](./Juthoor-Origins-LV3)** | Null model validation rewired to hybrid scoring (z=3.23 partial). Theory synthesis: 10 corridor cards, convergent Arabic-IE evidence. |

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
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) or standard pip

### Installation

```bash
git clone https://github.com/YassineTemessek/Juthoor-Linguistic-Genealogy.git
cd Juthoor-Linguistic-Genealogy

uv venv .venv --python 3.12
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

| Category | In Pipeline | Queued (Wave 1-3) |
| :--- | :--- | :--- |
| **Semitic** | Arabic (`ara`), Quranic Arabic (`ar-qur`), Hebrew (`heb`), Aramaic (`arc`) | |
| **Indo-Iranian** | Persian (`fa`) | |
| **Hellenic** | Ancient Greek (`grc`) | |
| **Italic** | Latin (`lat`) | |
| **Germanic (West)** | Modern English (`en`), Middle English (`enm`), Old English (`ang`) | Old High German (`goh`) |
| **Germanic (East)** | | Gothic (`got`) |
| **Germanic (North)** | | Old Norse (`non`) |
| **Celtic (Goidelic)** | | Old Irish (`sga`) |
| **Celtic (Brythonic)** | | Welsh (`cy`) |
| **Tocharian** | | Tocharian B (`txb`) |
| **Anatolian** | | Hittite (special project) |

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
- **[Data Flow Architecture](./docs/DATA_FLOW_ARCHITECTURE.md)**: Pipeline data flow and scoring architecture.
- **[LV2 Benchmarks](./Juthoor-CognateDiscovery-LV2/resources/benchmarks/README.md)**: Evaluation assets and workflow.
- **[Status Tracker](./docs/plans/STATUS_TRACKER.md)**: Resume point after interruptions.

## License

This project is licensed under the MIT License with an attribution clause. Any use in publications, research, or derivative works must credit the author. See [LICENSE](./LICENSE).

**Author:** Yassine Temessek
