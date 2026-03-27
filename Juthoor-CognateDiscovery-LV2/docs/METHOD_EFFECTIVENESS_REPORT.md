# Method Effectiveness Report

**Date:** 2026-03-27
**Dataset:** Gold-supplemented discovery run (19,005 leads, 269/837 gold pairs found)

## Per-Method Gold Hit Analysis

From the gold-supplemented Arabic→English discovery run, we measured which of the 12 MultiMethodScorer methods actually find real cognate pairs.

| Rank | Method | Gold Hits | Total Leads | Precision | Recommendation |
|------|--------|----------|-------------|-----------|----------------|
| 1 | **multi_hop_chain** | 25 | 736 | **3.40%** | BOOST — best precision, historical pathway validated |
| 2 | **reverse_root** | 57 | 2,560 | 2.23% | KEEP — good recall, moderate precision |
| 3 | **emphatic_collapse** | 10 | 531 | 1.88% | BOOST — specialized but reliable for emphatic pairs |
| 4 | **direct_skeleton** | 120 | 7,052 | 1.70% | TIGHTEN — highest recall but floods with FPs |
| 5 | **position_weighted** | 23 | 1,708 | 1.35% | KEEP — LV1 H8 evidence makes it valuable |
| 6 | **guttural_projection** | 6 | 745 | 0.81% | KEEP — specialized, validates Khashim's Law |
| 7 | **ipa_scoring** | 17 | 2,476 | 0.69% | TIGHTEN — low precision despite IPA data |
| 8 | **morpheme_decomposition** | 10 | 2,210 | 0.45% | TIGHTEN — over-decomposes, too many false stems |
| 9 | **metathesis** | 1 | 944 | **0.11%** | DISABLE for ara-eng — nearly useless cross-family |
| 10 | **article_detection** | 0 | 43 | 0.00% | INVESTIGATE — should be high precision, gold may lack al- words |

## Key Findings

### 1. Multi-Hop Chain is the Best Method (3.40% precision)
The historical Arabic→Latin/Greek→English pathway produces the most reliable cognates. This validates the multi-hop chain corridor (CORRIDOR_08). The method traces actual historical transmission paths rather than relying on surface consonant similarity.

### 2. Metathesis is Nearly Useless for Cross-Family (0.11%)
Consonant reversal between Arabic and English is almost always accidental. However, for Semitic-Semitic pairs (Arabic→Hebrew), metathesis fires at 9.8% of leads — much higher. **Recommendation:** Disable metathesis for cross-family pairs, enable for intra-Semitic.

### 3. Direct Skeleton Finds the Most Gold but Generates the Most Noise
With 120 gold hits but 7,052 total leads, direct_skeleton has high recall but terrible signal-to-noise ratio (1.70%). It should remain enabled but with stricter minimum skeleton length (already enforced: 5-consonant minimum).

### 4. Article Detection Found Zero Gold Pairs
Surprising for the "highest precision method." Investigation needed: the gold benchmark may not include al- loanwords (alcohol, algebra, etc.) as their Arabic origin is so well-known they weren't included as discovery targets.

### 5. Emphatic Collapse is a Hidden Gem (1.88%)
With only 531 total leads, emphatic_collapse is selective and reliable. Arabic emphatic consonants (ص/ض/ط/ظ) collapsing to plain (s/d/t/z) is a systematic phonological law that produces genuine cognates.

## Score Distribution of Gold Hits

| Score Range | Gold Hits | % of All Gold Hits |
|------------|----------|-------------------|
| ≥ 0.90 | 147 | 55% |
| 0.80-0.89 | 77 | 29% |
| 0.70-0.79 | 15 | 6% |
| 0.55-0.69 | 24 | 9% |
| < 0.55 | 6 | 2% |

**89% of gold hits score ≥ 0.70** — the scoring calibration captures real cognates at high scores. The ranking problem is that too many false positives also score high.

## Recommendations for Reranker v3

Based on this analysis, the reranker should:
1. **Remove anti-signal features:** skeleton, orthography, family_boost, root_match, weak_radical_match, hamza_match (all negative coefficients in v2)
2. **Add method-aware features:** `methods_fired_count`, `best_method_precision` (from this table)
3. **Add cross-pair evidence:** convergent matches across 3+ languages
4. **Weight multi_hop_chain matches higher** (3.4% precision vs 1.7% average)
5. **Disable metathesis for cross-family pairs** to reduce noise
