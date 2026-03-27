# Juthoor Data Flow Architecture

## Overview

```
LV0 (DataCore)          LV1 (ArabicGenome)         LV2 (CognateDiscovery)      LV3 (Origins)
┌──────────────┐       ┌──────────────────┐       ┌─────────────────────┐     ┌──────────────┐
│ Raw Kaikki   │──────>│ Root Genome      │──────>│ Scoring Pipeline    │────>│ Corridor     │
│ JSONL dumps  │       │ Research Factory │       │ Discovery Engine   │     │ Cards        │
│ 9 languages  │       │ 4 Hypotheses    │       │ 12 Methods         │     │ Anchor Gates │
│ ~2.64M rows  │       │ QCA             │       │ Cognate Graph      │     │ Theory       │
└──────────────┘       └──────────────────┘       └─────────────────────┘     └──────────────┘
```

## LV0 → LV1: Raw Data to Genome

| Source | File | Rows | Consumer |
|--------|------|------|----------|
| Quranic Arabic | `LV0/data/processed/quranic_arabic/sources/quran_lemmas_enriched.jsonl` | 4,903 | LV1 genome, LV2 discovery source |
| Classical Arabic | `LV0/data/processed/arabic/classical/lexemes.jsonl` | 32,687 | LV2 discovery source (gold supplement) |
| Arabic HF roots | `LV0/data/processed/arabic/classical/sources/hf_roots.jsonl` | 56,606 | LV1 genome |
| Modern English | `LV0/data/processed/english_modern/sources/kaikki.jsonl` | 1,442,008 | LV2 target corpus |
| Old English | `LV0/data/processed/english_old/sources/kaikki.jsonl` | 7,948 | LV2 historical variants |
| Middle English | `LV0/data/processed/english_middle/sources/kaikki.jsonl` | 49,779 | LV2 historical variants |
| Hebrew | `LV0/data/processed/hebrew/sources/kaikki.jsonl` | 17,034 | LV2 target (IPA extraction) |
| Latin | `LV0/data/processed/latin/classical/sources/kaikki.jsonl` | 883,915 | LV2 target (stride-sampled) |
| Ancient Greek | `LV0/data/processed/ancient_greek/sources/kaikki.jsonl` | 56,058 | LV2 target (IPA extraction) |
| Persian | `LV0/data/processed/persian/modern/sources/kaikki.jsonl` | 19,361 | LV2 target |
| Aramaic | `LV0/data/processed/aramaic/classical/sources/kaikki.jsonl` | 2,176 | LV2 target (IPA extraction) |
| Turkish | `LV0/data/processed/turkish/sources/kaikki.jsonl` | 100 | LV2 target (test) |
| Akkadian | `LV0/data/processed/akkadian/sources/kaikki.jsonl` | 50 | LV2 target (test) |

## LV1 → LV2: Promoted Features

| LV1 Output | File | Data | LV2 Consumer |
|------------|------|------|-------------|
| H2 Field Coherence | `promoted_features/field_coherence_scores.jsonl` | 396 binary root families with coherence scores | `GenomeScorer.root_coherence_score()` |
| H5 Metathesis | `promoted_features/metathesis_pairs.jsonl` | 166 metathesis pair families | `GenomeScorer.is_metathesis_pair()` |
| H8 Positional | `promoted_features/positional_profiles.jsonl` | 28 letters × 3 positions with coherence | `PhoneticLawScorer._POSITION_WEIGHTS` (loaded dynamically) |
| H12 Meaning | `promoted_features/meaning_predictor_predictions.jsonl` | 1,721 roots with predicted meanings | `RootQualityScorer.root_quality()` |
| Cross-lingual | `promoted_features/cross_lingual_support.jsonl` | Replication evidence across languages | `GenomeScorer.cross_lingual_support()` |
| Sound Laws | `factory/sound_laws.py` | `project_root_sound_laws()`, `project_root_by_target()` | `PhoneticLawScorer`, `MultiMethodScorer` |

## LV2 Internal: Scoring Pipeline

```
Source Corpus ──> Pre-filter (fast skeleton match)
    │                    │
    │              Top candidates
    │                    │
    ▼                    ▼
Target Corpus ──> MultiMethodScorer (12 methods)
                        │
                  ┌─────┴──────┐
                  ▼            ▼
            Best Score    Methods Fired
                  │            │
                  ▼            ▼
            Hybrid Scoring (14 features):
            ├── semantic (0.50) ← BGE-M3 embedding
            ├── form (0.18) ← ByT5 embedding
            ├── orthography (0.05) ← n-gram match
            ├── sound (0.22) ← IPA match
            ├── skeleton (0.05) ← consonant skeleton
            ├── root_match (+0.35) ← exact root
            ├── correspondence (+0.12) ← consonant matrix
            ├── genome_bonus (+0.13) ← LV1 H2/H5 (Semitic only)
            ├── phonetic_law (+0.15) ← sound law projection
            ├── multi_method (+0.12) ← 12-method best score
            ├── root_quality (+0.08) ← LV1 H12
            └── cross_pair (+0.10) ← convergent evidence
                  │
                  ▼
            DiscoveryReranker (14-feature logistic model)
                  │
                  ▼
            Anchor Classification (gold/silver/auto_brut)
                  │
                  ▼
            Leads JSONL + Report MD
                  │
                  ▼
            Cognate Graph (8,876 nodes, 23,480 edges)
```

## LV2 → LV3: Evidence Flow

| LV2 Output | File | LV3 Consumer |
|------------|------|-------------|
| Cognate Graph | `outputs/cognate_graph.json` | Cross-pair evidence for corridor validation |
| Convergent Leads | `outputs/cross_pair_convergent_leads.jsonl` | Gold anchor candidates |
| Discovery Leads | `outputs/leads/*.jsonl` | Raw evidence for corridor cards |
| Gold Benchmark | `resources/benchmarks/cognate_gold.jsonl` | Validation ground truth |
| Correspondence Matrix | `data/processed/consonant_correspondence_matrix.json` | Empirical merger rules |

## LV3 Internal: Theory Synthesis

```
Validated Leads ──> Corridor Cards (10 defined)
                        │
                  Anchor Classification
                  ├── Gold: 3+ langs, 4+ methods, score>0.85
                  ├── Silver: 2+ methods, score>0.70
                  └── Auto_brut: score>0.55
                        │
                  Validation Pipeline
                  ├── Tier 1: Permutation test (automated)
                  ├── Tier 2: Cross-language replication (automated)
                  ├── Tier 3: Expert verification (manual)
                  └── Tier 4: Chronological consistency (manual)
                        │
                  Theory Synthesis Document
```

## Key Files Index

### Configuration
- `pyproject.toml` (root + each LV) — Python package configs
- `resources/phonetic_mergers.jsonl` — Semitic merger rules
- `resources/phonetic_mergers_latin.jsonl` — Latin merger rules (pending)
- `resources/phonetic_mergers_greek.jsonl` — Greek merger rules (pending)

### Scripts
- `scripts/discovery/run_full_discovery.py` — Arabic→English pipeline
- `scripts/discovery/run_discovery_multilang.py` — Multi-language pipeline
- `scripts/discovery/build_cognate_graph.py` — Graph builder
- `scripts/discovery/dashboard.py` — Project status dashboard
- `scripts/discovery/null_model_test.py` — Statistical validation
- `scripts/discovery/calibrate_thresholds.py` — Threshold tuning

### Key Modules
- `discovery/scoring.py` — Hybrid scoring + bonus pipeline
- `discovery/multi_method_scorer.py` — 12 etymology methods
- `discovery/phonetic_law_scorer.py` — Sound law projection
- `discovery/genome_scoring.py` — LV1 genome integration
- `discovery/root_quality_scorer.py` — H12 meaning predictor
- `discovery/cross_pair_scorer.py` — Convergent evidence
- `discovery/scoring_profiles.py` — Per-language weight profiles
- `discovery/loanword_detector.py` — Loanword vs cognate classification
- `discovery/rerank.py` — 14-feature logistic reranker
