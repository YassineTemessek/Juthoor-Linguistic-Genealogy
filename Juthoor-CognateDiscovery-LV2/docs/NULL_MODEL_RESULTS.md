# Null Model Results: Fast-Mode Pipeline Statistical Validation

**Date:** 2026-03-27
**Status:** CRITICAL FINDING — fast mode does NOT exceed random chance

## Test Setup
- Arabic corpus: 15 entries (Quranic)
- English corpus: 190 entries (stride-sampled)
- Total pairs: 2,850
- Threshold: 0.55
- Iterations: 2 null + 1 real
- Scorer: MultiMethodScorer (12 methods, all scoring guards active)

## Results

| Run | Matches Above 0.55 |
|-----|-------------------|
| **Real** | 1,278 |
| Null iteration 1 | 1,279 |
| Null iteration 2 | 1,278 |
| **Null mean** | **1,278.5 ± 0.7** |

**Z-score: -0.7**
**Effect size: 1.0× (no difference from random)**
**p-value: 0.76 (NOT significant)**

## Interpretation

The fast-mode pipeline (MultiMethodScorer without semantic embeddings) produces the **same number of matches regardless of whether Arabic roots are real or randomly shuffled.** This means:

1. **Consonant frequency, not meaning, drives matches.** Arabic consonant patterns (e.g., common consonants like ر, ل, م, ن, س) match English consonant patterns at rates determined by letter frequency distributions, not by linguistic relationships.

2. **The MultiMethodScorer is a consonant pattern detector, not a cognate detector** in fast mode. It finds pairs where Arabic and English consonant skeletons share characters — which happens equally often for real and random Arabic roots.

3. **Semantic embeddings are ESSENTIAL.** The semantic guard (halving phonetic bonus when semantic_score < 0.25) is the only mechanism that can distinguish true cognates (semantically related + phonetically similar) from false friends (phonetically similar but semantically unrelated).

## Why Gold Pairs ARE Found (32.1% Coverage)

Despite the null model showing no overall significance, gold pairs ARE found at 32.1% coverage. This is because:
- Gold pairs have BOTH consonant similarity AND meaning relationship
- Random shuffled pairs have consonant similarity BUT NO meaning relationship
- Both pass the consonant-only threshold equally
- The RANKING (not the detection) is where signal should emerge — gold pairs should rank HIGHER when semantic scores are added

## Implications for the Project

1. **All published claims MUST use full-mode pipeline** (with BGE-M3 semantic embeddings)
2. **Fast-mode results are exploratory only** — they show coverage capability but not statistical significance
3. **The 10 corridor cards need re-validation** using full-mode data with semantic guard
4. **The convergent evidence framework remains valid** — if the same Arabic root matches 3+ languages via different methods, that's still stronger than a single match, even if individual matches aren't above random chance
5. **The reranker's strongest signal (multi_method_score +1.39) may be capturing frequency effects** rather than linguistic relationships

## Recommended Next Steps

1. Run null model test with **full-mode pipeline** (semantic + form embeddings)
2. Re-compute corridor validation statistics using semantic-filtered leads only
3. Add semantic_score as a REQUIRED filter (not optional guard) for any claim
4. The consonant correspondence matrix (3,461 alignments from gold pairs) remains valid because those ARE expert-curated cognates — but the discovery pipeline's ability to FIND them in the wild needs semantic filtering
