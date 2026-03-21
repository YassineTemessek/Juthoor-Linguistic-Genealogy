# Project Progress Log

Last updated: 2026-03-21

## Current State

| Level | Status | Summary |
|-------|--------|---------|
| LV0 DataCore | Complete | 7 adapters, ~2.6M lexemes, 167 tests |
| LV1 ArabicGenome | Complete | Genome Phase 1-3 done, Research Factory Phase 0-3 done, 227 tests |
| LV2 CognateDiscovery | Operational | BGE-M3 + ByT5 hybrid scoring, genome-informed reranker, 215 tests |
| LV3 Origins | Architecture only | Docs defined, awaits promoted results from LV1/LV2 |

---

## 2026-03-21 — Documentation Refresh
- Updated all READMEs and status files to reflect current project state
- 711 tests passing across all levels

## 2026-03-19 — Arabic-English Benchmark Expansion
- Added 17 Arabic-English gold pairs from "Beyond the Word" research (Mazen Hammoude)
- Gold benchmark: 126 pairs across 5 language pair categories
- Added Arabic→English consonant shift rules to phonetic merger tables (ج↔K, ب↔F, د↔T, ق↔C)
- GenomeScorer now family-aware: bonuses only for Semitic-Semitic pairs (S.6 complete)

## 2026-03-18 — Benchmark Corrections (Phonetic Merger Principle)
- Critical correction: negatives must use zero-consonant-overlap only
- Removed 6 wrongly classified false friends (حرب/חרב, نار/נر, etc.) — moved to gold with semantic drift
- Added phonetic merger tables for 6 languages (66 entries)
- Codex started LV1 Core Restructure (structure first, content later)
- Created yassine_input folder for manual benchmark contributions

## 2026-03-17 — Multi-Pair Discovery + Evaluation
- Codex completed Wave 1: Arabic-Hebrew, Arabic-Aramaic, Arabic-Persian discovery runs
- Genome results: MRR +0.029 (Hebrew), +0.109 (Aramaic), 0.0 (Persian)
- Trained 3 rerankers with genome_bonus as 11th feature
- genome_bonus weight: 0.459 (Hebrew), 0.185 (Aramaic), 0.117 (Persian)
- B.7 Opus review: genome works for Semitic cognates, zero effect on Persian loanwords
- Persian normalization fix: fa↔fas language code mapping (S.1+S.2)
- Aramaic + Persian consonant mappings added to GenomeScorer (S.3+S.4, C.1+C.2)

## 2026-03-16 — Benchmark Expansion to 100+ Pairs
- Phase A complete: 104 gold pairs (50 ara-heb, 20 ara-fa, 18 ara-arc, 10 lat-grc, 6 ara-eng)
- 30 negatives with 13 false friends
- genome_bonus added as 11th reranker feature (B.4)
- genome_bonus persisted in lead components for reranker consumption (B.5)
- LV2 Evaluation Expansion plan created

## 2026-03-15 — CI Fixes
- Fixed CI: removed non-existent Quran-Corpus-Analysis from build job
- Fixed CI: prevented setuptools flat-layout discovery in root package
- Fixed CI: skip data-file tests when kaikki.jsonl not present on CI runners
- CI now green on GitHub Actions

---

## 2026-03-14 — Prior State (snapshot)

## LV0 — DataCore

- 7 adapters ingesting ~2.6M lexemes across 6 languages
- Arabic (classical multi-dict, HF roots, merged, Quranic), Modern English, Latin, Ancient Greek, Old English, Middle English
- Canonical JSONL schema with normalized fields across all sources
- 145 tests passing (now 167)

## LV1 — ArabicGenome

- **Genome (Phase 1-3 complete):** 12,333 roots, 22,908 words; Muajam Ishtiqaqi overlay at 68.9% match; semantic validation scored 1,910 triconsonantal roots (mean cosine 0.5578)
- **Research Factory Phase 0:** Infrastructure complete — models, loaders, feature store, experiment runner, embeddings, articulatory vectors
- **Research Factory Phase 1:** 3 experiments run — 1.1 letter similarity, 2.3 field coherence, 3.1 modifier personality
  - H2 (binary root field coherence): supported
  - H1, H3: inconclusive
- 175 tests passing (now 227)
- QCA is a subpackage at `juthoor_arabicgenome_lv1.qca`

## LV2 — CognateDiscovery

- Discovery engine operational with BGE-M3 + ByT5 hybrid scoring
- Benchmark framework with gold/silver/negative evaluation sets
- Supports local (BGE-M3, ByT5) and API (Gemini embedding-001) backends
- 150 tests passing (now 215)

## LV3 — Origins

- Architecture documents: ROADMAP.md, CORRIDORS.md, VALIDATION_TRACK.md, ANCHOR_POLICY.md
- No implementation code — theory synthesis layer awaiting promoted results from LV1 and LV2
