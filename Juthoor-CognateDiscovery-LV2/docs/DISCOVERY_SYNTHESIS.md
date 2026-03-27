# LV2 Discovery Synthesis Report

**Date:** 2026-03-27
**Session:** Multi-method scorer integration, multi-language discovery, scoring calibration

## Executive Summary

This session recovered a frozen pipeline, integrated a 12-method etymology scorer into the main LV2 pipeline, built multi-language discovery support (6 languages), and applied 5 false-positive reduction guards. Discovery runs produced 9,620 leads across 4 language pairs (Arabic to English, Latin, Hebrew, Greek).

## Architecture Changes

### Multi-Method Scorer (12 Methods)
Integrated as the 14th feature in the scoring pipeline alongside the existing 13 features (semantic, form, orthography, sound, skeleton, family_boost, root_match, correspondence, weak_radical, hamza, genome, phonetic_law, coherence).

| Method | Description | Fires Most For |
|--------|------------|----------------|
| direct_skeleton | Arabic consonant skeleton projected to Latin | All languages (41.5%) |
| position_weighted | LV1 H8 positional semantics weighting | Latin, English |
| reverse_root | English consonants mapped back to possible Arabic roots | All languages |
| ipa_scoring | IPA-based consonant matching | English only |
| morpheme_decomposition | Prefix/suffix stripping, stem matching | English, Latin |
| multi_hop_chain | Arabic -> Latin/Greek intermediate -> target | Hebrew, Greek |
| metathesis | Consonant reversal/swap detection | Hebrew (highest) |
| emphatic_collapse | Arabic emphatics (s/t/d/z) -> plain | Latin |
| guttural_projection | Khashim guttural deletion rules | Low fire rate |
| article_detection | Arabic "al-" article absorption | Latin only |
| dialect_variant | Gulf/Egyptian/Moroccan consonant shifts | Low fire rate |
| synonym_expansion | Synonym family from LV1 genome | Requires LV1 data |

### Multi-Language Discovery
New script `run_discovery_multilang.py` supports any source/target pair with:
- IPA-based skeleton extraction for non-Latin scripts (Hebrew, Greek, Aramaic)
- Semitic-mode flag for intra-family discovery (skips Latin projection)
- Stride-based sampling for large corpora (Latin: 884K entries)

## Discovery Results

### Cross-Language Comparison (2026-03-27)

| Pair | Scale | Leads | Prefilter % | Gold Found | MRR | Runtime |
|------|-------|-------|------------|------------|-----|---------|
| ara->eng | 200x5000 | 3,076 | N/A | 1/837 | 0.0 | 624s |
| ara->lat | 200x5000 | 2,963 | 6.5% | N/A | N/A | 388s |
| ara->heb | 200x2000 | 2,155 | 3.0% | 3/55 | 0.0003 | 138s |
| ara->grc | 100x2000 | 1,426 | 8.2% | N/A | N/A | 120s |

### Scoring Fixes Applied
1. **Minimum 5-consonant guard**: Rejects pairs where total consonants < 5
2. **Length ratio guard (3x)**: Rejects very mismatched skeleton lengths
3. **Minimum score 0.55 per method**: Filters out low-confidence noise
4. **Consonant class diversity penalty (0.5x)**: Penalizes single-class matches
5. **Short-root penalty (0.7x)**: Position-weighted method penalized for < 3 consonants

### Impact of Fixes
- Before fixes: 89% of leads scored above 0.85, MRR 0.0 (noise dominated)
- After fixes: More distributed scores, fewer false positives, but MRR still low
- Root cause of low MRR: fast mode has no semantic embeddings, so phonetically similar but semantically unrelated pairs still score high

## Method Effectiveness Analysis

### Across All 4 Language Pairs (9,620 leads total)

| Method | Total Fires | % | Assessment |
|--------|------------|---|------------|
| direct_skeleton | 4,017 | 41.5% | High recall, moderate precision |
| position_weighted | 1,911 | 19.8% | Useful but permissive |
| reverse_root | 1,336 | 13.8% | High false positive rate |
| morpheme_decomposition | 631 | 6.5% | Good for IE languages |
| multi_hop_chain | 569 | 5.9% | Valuable for cross-family |
| ipa_scoring | 531 | 5.5% | English-only, good precision |
| metathesis | 462 | 4.8% | Best for Semitic-Semitic |
| emphatic_collapse | 103 | 1.1% | Specialized, low fire rate |
| guttural_projection | 42 | 0.4% | Very specialized |
| article_detection | 18 | 0.2% | Niche but high precision |

### Language-Specific Insights

**Hebrew (Semitic-Semitic):**
- Metathesis fires at 3x the rate of other languages (9.8% vs ~3%)
- Multi-hop chain fires at 11.8% — unexpected for a Semitic target
- Morpheme decomposition barely fires (0.7%) — Hebrew doesn't have IE affixes

**Latin (IE via direct contact):**
- Article detection fires here (16 leads) — Arabic loanwords (algebra, alchemy, etc.)
- High morpheme decomposition (9.1%) — Latin's rich morphology
- Emphatic collapse highest here (1.7%) — Arabic emphatics map to Latin plain consonants

**Greek (IE via ancient contact):**
- Balanced method distribution
- Multi-hop fires at 7.9% — reasonable for an intermediate language

**English (IE, target language):**
- IPA scoring fires heavily (16.3%) — English has the best IPA coverage
- Morpheme decomposition at 11.0% — English affixes well-covered

## Test Suite Status
- **1,055+ tests** passing across all levels (LV0: 167, LV1: 505, LV2: 383)
- New tests: multi_method_scorer (23), llm_validator (14), multi_method_integration (6)

## Next Steps

### Short-term (improve MRR)
1. Run full-mode discovery with semantic embeddings (BGE-M3 + FAISS) — semantic scores enable the semantic guard
2. Retrain reranker with 14 features on latest leads
3. Expand source to all 4,903 Quranic Arabic + 32,687 classical Arabic lemmas

### Medium-term (expand coverage)
4. Arabic->Persian and Arabic->Aramaic discovery
5. Cross-reference leads across language pairs (if Arabic root X matches both Latin Y and Greek Z, that's stronger evidence)
6. Build false-positive classifier from negative benchmark pairs

### Long-term (theory synthesis)
7. Feed validated leads into LV3 corridor analysis
8. Language genealogy graph visualization
9. Statistical significance testing of cognate clusters
