# Project Progress Log

## 2026-03-18
- **LV2 Benchmark Corrections (Phonetic Merger Principle) Started**:
  - Added merger-aware phonetic utilities in `src/juthoor_cognatediscovery_lv2/discovery/phonetic_mergers.py`.
  - Added benchmark audit tooling in `src/juthoor_cognatediscovery_lv2/discovery/benchmark_audit.py` and `scripts/discovery/audit_benchmark_mergers.py`.
  - Added test coverage for merger mapping and benchmark audit behavior.
- **Benchmark Audit Findings Persisted**:
  - Audited `cognate_gold.jsonl` and `non_cognate_negatives.jsonl` against merger-aware rules.
  - Current audit summary:
    - `41` total findings
    - `33` merger-sensitive cognates recorded as informational
    - `8` risky negatives / false-friend controls marked for review
  - Audit outputs written under `outputs/reports/benchmark_merger_audit.json` and `outputs/reports/benchmark_merger_review_findings.json`.
- **Benchmark Asset Corrections Applied Conservatively**:
  - Annotated risky rows in `resources/benchmarks/non_cognate_negatives.jsonl` with:
    - lower confidence
    - `audit_status: "review_required"`
    - explicit `audit_reason`
  - Kept the risky rows in the benchmark for now, but stopped treating them as settled high-confidence controls.
- **Operational Conclusion**:
  - LV2 benchmarking is now merger-aware at the audit layer.
  - The next benchmark-cleanup pass should either replace the `8` review-bound negatives with safer zero-overlap controls or split them into a separate review-only benchmark asset.

## 2026-03-11
- **Phase 1a (LV0 Arabic Enrichment) Completed**:
  - Enriched Quranic Arabic and Classical Arabic `lexemes.jsonl` files in LV0.
  - Added `form_text` and `meaning_text` fields to over 37,000 entries.
- **Phase 1b (Benchmark) Started**:
  - Created initial `resources/benchmarks/cognate_gold.jsonl` with 10 high-confidence Semitic pairs (Arabic-Hebrew).
- **Phase 2 (LV2 Refactor) Started**:
  - Created `src/juthoor_cognatediscovery_lv2/discovery/corpora.py` and `retrieval.py` for modular corpus discovery and embedding/retrieval.
  - Implemented field-aware embedding logic in `retrieval.py` (meaning_text for semantic, form_text for form).

