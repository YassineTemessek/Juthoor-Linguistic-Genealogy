# Juthoor-CognateDiscovery-LV2

![level](https://img.shields.io/badge/level-LV2-6f42c1)
![license](https://img.shields.io/badge/license-MIT-blue)
![tests](https://img.shields.io/badge/tests-498%20passing-brightgreen)

Cross-lingual cognate discovery engine. Compares Arabic 3-letter roots against Indo-European lexemes using semantic, phonetic, and form-based evidence, then ranks candidates for review.

LV2 is discovery-first: outputs are ranked leads for human review, not final claims about historical relationships.

## Supported Deployment Model

LV2 is supported inside the **Juthoor monorepo checkout** with editable installs. Shared cross-level artifacts use the repo-root `outputs/` directory. Standalone installation of LV2 without the rest of the monorepo is not a supported target.

## Current Status

- **498 tests passing**
- **Forward discovery** (Arabic → target): 7 language pairs operational
- **Reverse discovery** (target → Arabic): new primary pipeline, 54K-key reverse Arabic root index
- **Gold benchmark**: 1,889 pairs across 13 language pairs
- **Cognate graph**: 12,455 nodes, 47,071 edges across 7 languages
- **Gold coverage**: 32.1% (269/837 pairs) after Arabic source fix

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
scripts/discovery/   — runnable pipeline entrypoints
tests/               — 498 tests
resources/benchmarks/ — 1,889-pair gold benchmark (13 language pairs)
docs/                — pipeline specification and documentation
outputs/             — local run artifacts (gitignored)
data/                — local datasets (gitignored)
```

## Next Phase: LLM-Assisted Annotation

The pipeline is entering a controlled annotation phase where LLMs fill knowledge gaps that scripts cannot handle. The LLM acts as a temporary annotator — not a judge — returning structural facts that get promoted into deterministic rules once patterns stabilize.

| Layer | Purpose | Status |
|-------|---------|--------|
| 1. Target Morphology | Correct stems, false prefixes, consonant stem nouns | Starting |
| 2. Semantic Normalization | English translations for Latin/Greek/OE glosses | Planned |
| 3. Consonant Correspondence | Per-consonant mapping with matched controls | Planned |
| 4. Pre-Ranker Redesign | Engineering analysis on clean data | After 1-3 |

Small batches (30-50 items), reviewed iteratively. No bulk runs. See `docs/pipeline_specification.md` for full methodology.

## Documentation

- `docs/pipeline_specification.md` — comprehensive pipeline spec + LLM annotation methodology

## Repo Policy

- Large datasets under `data/raw/` and `outputs/` are not committed.
- Gold benchmark under `resources/benchmarks/` is tracked.
- Canonical shared artifacts such as `cognate_graph.json` and `cross_pair_convergent_leads.jsonl` live under the repo-root `outputs/` directory.
- LV2-local run artifacts such as discovery lead files stay under `Juthoor-CognateDiscovery-LV2/outputs/`.

## Contact

For collaboration: `yassine.temessek@hotmail.com`
