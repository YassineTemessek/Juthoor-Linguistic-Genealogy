# Juthoor-CognateDiscovery-LV2

![level](https://img.shields.io/badge/level-LV2-6f42c1)
![license](https://img.shields.io/badge/license-MIT-blue)
![tests](https://img.shields.io/badge/tests-523%20passing-brightgreen)

Cross-lingual cognate discovery engine. Compares Arabic 3-letter roots against Indo-European lexemes using semantic, phonetic, and form-based evidence, then ranks candidates for review.

LV2 is discovery-first: outputs are ranked leads for human review, not final claims about historical relationships.

## Supported Deployment Model

LV2 is supported inside the **Juthoor monorepo checkout** with editable installs. Shared cross-level artifacts use the repo-root `outputs/` directory. Standalone installation of LV2 without the rest of the monorepo is not a supported target.

## Current Status

- **523 tests passing**
- **Forward discovery** (Arabic → target): 7 language pairs operational
- **Reverse discovery** (target → Arabic): primary pipeline, 54K-key reverse Arabic root index
- **Gold benchmark**: 1,889 pairs across 13 language pairs
- **Cognate graph**: 12,455 nodes, 47,071 edges across 7 languages
- **LLM annotation layers**: Layer 1 (morphology) + Layer 2 (semantic) complete for ara-lat
- **Arabic semantic profiles**: 954 lemmas with mafahim (genome) + masadiq (dictionary)
- **Eye 2 LLM semantic scoring**: in progress — replaces broken gloss-based semantic with LLM reasoning

## Role in the Stack

Consumes canonical lexeme tables from LV0 and promoted evidence cards from LV1. Produces ranked lead rows with evidence cards for LV3 theory synthesis.

## Architecture

### Discovery Modules (`src/juthoor_cognatediscovery_lv2/discovery/`)

| Module | Description |
|--------|-------------|
| `multi_method_scorer.py` | 12 etymology scoring methods (best: multi_hop_chain 3.4% precision) |
| `phonetic_law_scorer.py` | Arabic phonetic projection engine |
| `phonetic_mergers.py` | Consonant correspondence matrices (bilabial cluster b/p/f/v interchangeable) |
| `target_morphology.py` | Latin/Greek/OE decomposition + universal phonetic corridors |
| `gloss_similarity.py` | Jaccard word overlap on English glosses |
| `concept_matcher.py` | 287-concept structured semantic matcher |
| `scoring_profiles.py` | Per-language-pair weight tuning |
| `precomputed_assets.py` | Reverse index builder (54K Arabic root entries) |
| `synonym_expansion.py` | Arabic root family expansion |
| `loanword_detector.py` | al- prefix heuristic detection |
| `discovery_reranker.py` | v3 reranker — 11 features (removed 6 anti-signals from v2) |

### Scripts (`scripts/discovery/`)

| Script | Description |
|--------|-------------|
| `run_reverse_discovery.py` | **Recommended** — target → Arabic reverse pipeline |
| `run_discovery_multilang.py` | Forward multilang discovery (7+ language pairs) |
| `run_improved_discovery.py` | Forward Arabic → English with semantic layer |
| `run_full_discovery.py` | Original 6-stage forward pipeline |
| `evaluate_gold_pairs.py` | Direct gold pair scoring (English) |
| `evaluate_gold_pairs_multilang.py` | Direct gold pair scoring (any language) |
| `build_arabic_english_glosses.py` | Gloss lookup builder (12K entries) |
| `build_unified_arabic_source.py` | Unified Arabic corpus (37K entries) |
| `build_enriched_english_corpus.py` | Enriched English corpus with glosses |
| `null_model_test.py` | Permutation statistical validation |
| `eval_layer1_impact.py` | A/B evaluation of Layer 1 morphology impact |
| `build_arabic_profiles.py` | Combine mafahim + masadiq for Arabic semantic profiles |

## Target Languages

| Language | Lexemes | Code |
|----------|---------|------|
| Latin | 883,915 | `lat` |
| Modern English | 1,442,008 | `eng` |
| Ancient Greek | 56,058 | `grc` |
| Middle English | 49,779 | `enm` |
| Old English | 7,948 | `ang` |
| Persian | 19,361 | `fas` |
| Hebrew | 17,034 | `heb` |

## Key Commands

```bash
# Reverse discovery — recommended (target → Arabic)
python scripts/discovery/run_reverse_discovery.py --target ang --no-semantic
python scripts/discovery/run_reverse_discovery.py --target lat --limit 5000

# Forward multilang discovery
python scripts/discovery/run_discovery_multilang.py --source ara --target lat --fast --limit 500

# Gold pair evaluation
python scripts/discovery/evaluate_gold_pairs_multilang.py --source ara --target lat

# Run tests
python -m pytest tests/ -q
```

## Scoring Pipeline

- **Base hybrid weights**: semantic 0.50, sound 0.22, form 0.18, orthography 0.05, skeleton 0.05
- **Bonuses**: root_match, correspondence, genome, phonetic_law, multi_method, root_quality (H12), cross_pair_evidence
- **Reranker v3**: 11 features — `multi_method_score` (+1.39) is the strongest signal; skeleton and orthography are anti-signals
- **Scoring profiles**: per-language-pair weight adjustments in `scoring_profiles.py`

## Key Findings

- Arabic source coverage was 0.9% before fix — supplementing from classical Arabic was the breakthrough
- Bilabial cluster {b, p, f, v} is interchangeable cross-family
- ع deletion occurs at 88% in cross-family cognates
- Skeleton and orthography features are anti-signals (reranker v2 weights: -0.70, -0.54)
- `multi_method_score` is the strongest positive reranker signal (+1.39)

## Layout

```
src/juthoor_cognatediscovery_lv2/
  discovery/         — scoring + pipeline modules
  data/              — data access utilities
scripts/             — runnable pipeline entrypoints + annotation builders
tests/               — 523 tests
resources/benchmarks/ — 1,889-pair gold benchmark (13 language pairs)
data/llm_annotations/ — Layer 1-2 annotations + Arabic profiles (tracked)
docs/                — pipeline specification and documentation
outputs/             — local run artifacts (gitignored)
data/raw/, data/processed/ — local datasets (gitignored)
```

## LLM-Assisted Annotation Phase

The pipeline uses LLMs as annotators (never judges) to fill knowledge gaps. Results are promoted into deterministic rules once patterns stabilize.

### Completed Layers

| Layer | Purpose | Status | Artifacts |
|-------|---------|--------|-----------|
| 1. Target Morphology | Latin etymological stems, false prefix fixes | **DONE** (244/244) | `data/llm_annotations/layer1_morphology.jsonl` |
| 2. Semantic Normalization | English glosses for Latin gold pairs | **DONE** (244/244) | `data/llm_annotations/layer2_semantic_mapping.jsonl` |
| Arabic Profiles | Mafahim (genome) + masadiq (dictionary) for Arabic sources | **DONE** (954 lemmas) | `data/llm_annotations/arabic_semantic_profiles.jsonl` |

**Layer 1 impact** (A/B validated): 50 pairs improved, 5 degraded (10:1 ratio), skeleton hits at >0.45 threshold: 96 → 112 (+16).

### In Progress

| Layer | Purpose | Status |
|-------|---------|--------|
| Eye 2: LLM Semantic | Smart LLM scores semantic relatedness using mafahim + masadiq | **In progress** |
| 3. Consonant Correspondence | Per-consonant mapping with matched controls | Planned |
| 4. Pre-Ranker Redesign | Engineering analysis on clean data | After Eye 2 |

**Eye 2 architecture**: Eye 1 (phonetic/skeleton) produces candidate matches → Eye 2 (LLM) evaluates semantic plausibility. The LLM checks dictionary meaning (masadiq) first for obvious connections, then uses deep root meaning (mafahim) for hidden links. This replaces the broken gloss-based semantic scorer (4.1% coverage → expected 95%+).

### Key Finding: Pipeline Bottleneck Analysis

The semantic channel (55% of total score weight) was effectively dead:
- 98.8% of ara-lat gold pairs had zero semantic score
- 80% of Arabic sources lacked any gloss
- Gloss-matching cannot capture conceptual depth (e.g., كومة "heap" → cemetery "sleeping place of dead")

Eye 2 solves this by replacing mechanical gloss matching with LLM reasoning.

## Documentation

- `docs/pipeline_specification.md` — comprehensive pipeline spec + LLM annotation methodology

## Repo Policy

- Large datasets under `data/raw/` and `outputs/` are not committed.
- Gold benchmark under `resources/benchmarks/` is tracked.
- Canonical shared artifacts such as `cognate_graph.json` and `cross_pair_convergent_leads.jsonl` live under the repo-root `outputs/` directory.
- LV2-local run artifacts such as discovery lead files stay under `Juthoor-CognateDiscovery-LV2/outputs/`.

## Contact

For collaboration: `yassine.temessek@hotmail.com`
