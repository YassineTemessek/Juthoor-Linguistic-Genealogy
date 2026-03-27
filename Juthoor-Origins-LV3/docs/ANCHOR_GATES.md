# LV3 Anchor Gate Definitions

**Date:** 2026-03-27
**Status:** Active — applied to cognate graph (23,480 edges, 7 languages)

## Anchor Tiers

Each cognate lead from LV2 is classified into one of three anchor tiers based on cumulative evidence strength. Higher tiers provide stronger theoretical support.

### Gold Anchor (Highest Confidence)
**Criteria:** ALL of the following must be met:
1. Multi-method score ≥ 0.85
2. Cross-pair convergent evidence in **3+ target languages** (same Arabic root matches English AND Latin AND Greek independently)
3. At least 4 methods fired (methods_that_fired ≥ 4)
4. Either: known etymology exists (in gold benchmark) OR article_detection fired (near-perfect precision)

**Interpretation:** Near-certain cognate or attested loanword. Can be used as primary evidence in theory construction.

**Expected proportion:** ~2-5% of leads

### Silver Anchor (High Confidence)
**Criteria:** ALL of the following must be met:
1. Multi-method score ≥ 0.70
2. At least 2 methods fired
3. At least ONE of:
   - Phonetic law match (phonetic_law_bonus > 0)
   - Genome bonus > 0 (for Semitic-Semitic pairs)
   - Cross-pair evidence in 2+ languages
   - Root quality score > 0.6 (H12)

**Interpretation:** Probable cognate. Strong enough for corridor validation but needs cross-referencing before publication.

**Expected proportion:** ~10-20% of leads

### Auto-Brut Anchor (Computational Signal)
**Criteria:**
1. Multi-method score ≥ 0.55
2. At least 1 method fired
3. NOT classified as gold or silver

**Interpretation:** Computational match worth investigating but not evidence-quality. May be a true cognate, a loanword, or a false positive. Requires manual review or additional computational evidence before promotion.

**Expected proportion:** ~75-85% of leads

## Anchor Promotion Rules

Anchors can be promoted upward but never demoted:

1. **Auto-Brut → Silver:** When new discovery runs find the same pair with higher score or additional method matches
2. **Silver → Gold:** When cross-pair evidence accumulates (new language pair confirms the match) OR manual expert validation confirms etymology
3. **Any → Rejected:** When identified as false positive (accidental consonant overlap with no semantic relationship). Move to `non_cognate_negatives.jsonl`.

## Statistical Validation

Each anchor tier should exceed these significance thresholds:

| Tier | Minimum Evidence | Null Model Comparison |
|------|-----------------|----------------------|
| Gold | p < 0.001 | Match rate > 10× random chance |
| Silver | p < 0.01 | Match rate > 5× random chance |
| Auto-Brut | p < 0.05 | Match rate > 2× random chance |

**Null model:** Shuffle Arabic roots randomly, re-run discovery, count matches. The real match rate should far exceed the shuffled rate for each tier.

## Application to Current Data

Based on cognate graph (23,480 edges):

| Criterion | Proxy in Current Data |
|-----------|----------------------|
| score ≥ 0.85 | `multi_method_best` or `final_combined` in leads JSONL |
| 3+ target languages | Count distinct `target.lang` per Arabic root in cognate graph |
| 4+ methods fired | `methods_fired_count` in leads JSONL |
| Phonetic law match | `phonetic_law_bonus > 0` in scoring components |
| Genome bonus | `genome_bonus > 0` in scoring components |
| Root quality | `root_quality_score` from H12 scorer |

## Next Steps

1. Apply anchor classification to all 23,480 cognate graph edges
2. Count distribution: how many gold, silver, auto_brut?
3. Manually review top 50 gold anchors for correctness
4. Build corridor-anchor cross-reference: which corridors produce the most gold anchors?
5. Run null model test: shuffle roots, measure false gold rate
