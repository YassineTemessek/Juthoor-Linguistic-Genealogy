# Juthoor Linguistic Genealogy - Project Overview

## The Vision
**Juthoor** (Arabic: *Roots*) is a unified linguistic engine designed to trace the genealogy of human language, with a primary focus on the Arabo-Semitic root system as a potential "linguistic DNA."

This monorepo consolidates five distinct research layers into a single, cohesive system where higher levels build upon the foundational data and logic of the lower levels.

## Architecture & Layers

The project is organized into a **layered architecture** (LV0 to LV4):

| Level | Folder Name | Role & Responsibility | Dependencies |
| :--- | :--- | :--- | :--- |
| **LV0** | `Juthoor-DataCore-LV0` | **The Foundation.** Data ingestion, normalization, and canonization. It serves as the "single source of truth" for raw linguistic data. | *(None)* |
| **LV1** | `Juthoor-ArabicGenome-LV1` | **Arabic Genome.** Decoding the biconsonantal (2-letter) root system and establishing the core "atomic" meanings of Arabic sounds. | LV0 |
| **LV2** | `Juthoor-CognateDiscovery-LV2` | **Discovery Engine.** Cross-lingual similarity scoring (e.g., comparing Arabic roots to English, Latin, Greek). Generates ranked candidates for cognates. | LV0 |
| **LV3** | `Juthoor-Origins-LV3` | **Theory & Genealogy.** The synthesis layer. Hypothesis testing, genealogical mapping, and reconstructing the "Origin" language model. | LV0, LV1, LV2 |
| **App** | `Quran-Corpus-Analysis` | **Quran Application.** Semantic analysis of Quranic text using the engines above. | LV0, LV1 |

## Workspace Structure (Python)

This project is configured as a **Python Workspace**. The root `pyproject.toml` defines the entire repository as a workspace, meaning all 5 levels are member packages.

### Benefits
*   **Unified Imports:** Scripts in LV4 can import directly from LV0 (e.g., `from juthoor_datacore_lv0 import ...`) without messy path hacks (`sys.path.append`).
*   **Explicit Dependencies:** Each level has its own `pyproject.toml` declaring exactly which other levels it needs.
*   **Single Install:** You can install the entire project in one go using `uv`, `pip`, or `pdm`.

### Package Names
| Folder | Python Package Name (Importable) |
| :--- | :--- |
| LV0 | `juthoor-datacore-lv0` |
| LV1 | `juthoor-arabicgenome-lv1` |
| LV2 | `juthoor-cognatediscovery-lv2` |
| LV3 | `juthoor-origins-lv3` |
| App | `quran-corpus-analysis` |

## Directory Layout

```text
Juthoor-Linguistic-Genealogy/
├── pyproject.toml              # Root workspace definition
├── README.md                   # Main entry point
├── docs/                       # Shared project-wide documentation
├── Resources/                  # Shared external resources (PDFs, reference materials)
│
├── Juthoor-DataCore-LV0/       # [CODE] Data Engine
├── Juthoor-ArabicGenome-LV1/   # [CODE] Arabic Root Graph
├── Juthoor-CognateDiscovery-LV2/ # [CODE] Cross-Lingual Scorer
├── Juthoor-Origins-LV3/        # [CODE] Theoretical Models
└── Quran-Corpus-Analysis/      # [CODE] Quran Analysis Application
```

## Development Guidelines

1.  **Code Placement:**
    *   **Reusable Logic:** Put it in `src/` within the appropriate level's folder. This makes it importable by other levels.
    *   **Experiments/Runners:** Put it in `scripts/` within the appropriate level.

2.  **Data Flow:**
    *   Data should ideally flow **UP** the levels (LV0 -> LV4).
    *   LV0 is the only place that should handle raw data ingestion.
    *   Higher levels should consume the *canonical* data produced by LV0.

3.  **New Dependencies:**
    *   If you add a new library (e.g., `numpy`), add it to the `pyproject.toml` of the specific level that needs it.

## Deep Dive: Juthoor-CognateDiscovery-LV2 (The Discovery Engine)

This layer is the **Laboratory** where cross-lingual connections are hypothesized and ranked.

### Core Functionality
1.  **AI Retrieval (The Heavy Lifting):**
    *   **SONAR (Meta):** Finds words with similar *meanings* across languages (semantic search), even if they sound different.
    *   **CANINE (Google):** Finds words with similar *spelling/form* at a character level (raw Unicode).

2.  **Hybrid Scoring (The Refinement):**
    *   Calculates precise scores for candidate pairs based on:
        *   **Orthography:** Visual letter similarity.
        *   **Phonetics (IPA):** Sound similarity.
        *   **Skeleton:** Consonant root structure comparison.

3.  **Output:**
    *   Generates **"Ranked Leads"**: Lists of candidate cognates with match scores (e.g., "85% match").
    *   Does *not* make final truth claims; it filters the noise so researchers can focus on high-probability connections.

---
*Generated: February 3, 2026*
