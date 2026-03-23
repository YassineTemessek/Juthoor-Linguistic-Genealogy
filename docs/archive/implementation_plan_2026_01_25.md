# Audit Report & Improvement Plan (2026-01-25)

## 1. Executive Summary
The project correctly separates concerns between **Juthoor-DataCore-LV0** (Data Ingestion & Canonization) and **Juthoor-CognateDiscovery-LV2** (Discovery & Scoring). The "Pipeline Modernization" documentation in LV0 is robust and aligns with the project vision. However, the modernization code (adapters, embeddings) is currently in a "scaffolding" state and needs implementation.

## 2. Findings

### 2.1. Project Structure
- **LV0 (Data Core)**: Central truth for ingestion/canonization.
- **LV3 (Comparison)**: Consumes LV0 for discovery.

### 2.2. Code Status
- **Modernization**: `src/ingest/adapters` and `src/embeddings` in LV0 are scaffolds as documented.
- **Missing Logic**: **"Snapshot Export" and "Neo4j Pipeline" scripts were NOT FOUND** in standard paths. The only mention is in LV2 `export_binary_root_graph.py` referring to importers.

## 3. Vertical Slice: Acceptance Criteria
We will implement a minimal "vertical slice" to prove the pipeline before expanding:
**LV0 Ingest (Arabic Classical)** → **LV2 Graph Export (Nodes/Edges)**.

| Phase | Success Metric |
| :--- | :--- |
| **Phase 1: LV0 Ingest (Arabic)** | `run_adapters.py` produces `data/processed/canonical/arabic/classical/lexemes.jsonl` with stable IDs. |
| **Phase 2: LV2 Export** | `scripts/graph/export_binary_root_graph.py` runs against the **canonical** file and produces valid CSVs. |
| **Phase 3: Validation** | Visual check of CSVs shows `lemma_status` is respected (unverified edges filtered). |

## 4. Proposed Improvements (Revised)

### Phase 1: Implement LV0 Adapters (Vertical Slice Base)
- **Goal**: Generate proper canonical data for both Quran and Classical Arabic.
- **Files**:
    - [MODIFY] [quran_lemmas.py](file:///c:/AI%20Projects/Juthoor-Linguistic-Genealogy/Juthoor-DataCore-LV0/src/ingest/adapters/quran_lemmas.py): Fix input path to `data/processed/quranic_arabic/sources/quran_lemmas_enriched.jsonl`.
    - [NEW] [arabic_classical.py](file:///c:/AI%20Projects/Juthoor-Linguistic-Genealogy/Juthoor-DataCore-LV0/src/ingest/adapters/arabic_classical.py): New adapter for `data/processed/arabic/classical/lexemes.jsonl`.
    - [MODIFY] [run_adapters.py](file:///c:/AI%20Projects/Juthoor-Linguistic-Genealogy/Juthoor-DataCore-LV0/scripts/ingest/run_adapters.py): existing file, add Arabic Classical step.

### Phase 2: Refine LV2 Graph Export (The "Neo4j" Fix)
- **Goal**: Rescope "Neo4j/Snapshot" fix to LV2's existing graph code and connect to canonical data.
- **Files**:
    - [MODIFY] [export_binary_root_graph.py](file:///c:/AI%20Projects/Juthoor-Linguistic-Genealogy/Juthoor-ArabicGenome-LV1/scripts/graph/export_binary_root_graph.py):
        - Default input changed to `data/processed/canonical/arabic/classical/lexemes.jsonl`.
        - Add filtering to exclude unverified items.

### Phase 3: Text Fields (Preparation for LV3)
- **Goal**: Add `form_text` and `meaning_text` to canonical outputs.
- **Files**:
    - [MODIFY] [build_text_fields.py](file:///c:/AI%20Projects/Juthoor-Linguistic-Genealogy/Juthoor-DataCore-LV0/src/features/build_text_fields.py)

## 5. Verification Plan

### Automated
- **Ingest Test**: Run `ldc ingest --all` to get raw data, then `python scripts/ingest/run_adapters.py`.
- **Validation**: Verify `data/processed/canonical/` contains the expected files.
- **Graph Test**: Run `export_binary_root_graph.py` and inspect `outputs/graphs`.

### Manual
- **Neo4j Import**: Manually import the generated CSVs into Neo4j Desktop and check for errors.
