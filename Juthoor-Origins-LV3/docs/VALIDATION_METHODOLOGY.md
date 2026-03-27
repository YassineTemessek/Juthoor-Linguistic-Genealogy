# LV3 Validation Methodology

**Date:** 2026-03-27
**Status:** Framework defined, awaiting first validation run

## Purpose
This document defines how each corridor card is validated — moving from "computational observation" to "statistically validated linguistic hypothesis." Without this, the discovery pipeline produces interesting leads but not publishable science.

## Validation Tiers

### Tier 1: Statistical Significance (Automated)
Each corridor must pass a permutation test showing its match rate exceeds random chance.

**Method:**
1. **Real run:** Apply the corridor's discovery method to Arabic↔target corpus, count matches above threshold
2. **Null model (N=100 iterations):** Shuffle Arabic roots randomly (breaking root-meaning association), re-run, count matches
3. **Compare:** z-score = (real_count - null_mean) / null_std
4. **Threshold:** z > 3.29 (p < 0.001) for "confirmed", z > 2.58 (p < 0.01) for "provisional"

**Per-corridor expected results:**
| Corridor | Expected z-score | Rationale |
|----------|-----------------|-----------|
| C01 Guttural Deletion | >10 | 88% ع deletion vs ~5% random = ~17x |
| C02 Emphatic Collapse | 3-5 | Moderate signal, low frequency |
| C03 Article Absorption | >20 | Near-perfect precision, zero random chance |
| C04 Metathesis | 2-3 | Small effect (H5: 52.6% vs 50.2%) |
| C05 Position-1 Anchor | 5-8 | Strong H8 evidence (24/28 significant) |
| C06 Binary Nucleus | 3-5 | H2 evidence (>11σ internally) |
| C07 Morpheme Decomposition | 4-6 | IE-specific, moderate signal |
| C08 Multi-Hop Chain | 3-5 | Historical pathway, moderate precision |
| C09 Bilabial Cluster | 2-4 | High frequency → more chance overlap |
| C10 Meaning Predictability | 5-10 | H12 AUC=0.739, strong internal signal |

### Tier 2: Cross-Language Replication (Automated)
A corridor is stronger if it produces matches in multiple independent target languages.

**Method:**
1. Run corridor on Arabic→English, Arabic→Latin, Arabic→Greek independently
2. Count: how many Arabic roots match via this corridor in 2+ languages?
3. **Threshold:** ≥20% of corridor's matches replicate across 2+ languages for "confirmed"

### Tier 3: Expert Etymological Verification (Manual)
Top gold-anchor leads must be verified against standard etymological dictionaries.

**Method:**
1. Take top 50 gold-anchor leads from each corridor
2. Look up in: Wiktionary etymology, Etymonline, Lisan al-Arab, Lane's Lexicon
3. Classify: confirmed (attested etymology), plausible (no attested but linguistically sound), rejected (false positive)
4. **Threshold:** ≥60% confirmed + plausible for "validated"

### Tier 4: Chronological Consistency (Manual)
Verify that the proposed direction of influence is historically plausible.

**Method:**
1. For each validated lead: identify earliest attestation date in source and target language
2. Check: is the proposed direction consistent with attestation chronology?
3. Check: was there historical contact (trade, conquest, scholarship) at the relevant period?
4. **Threshold:** ≥80% chronologically consistent for "historically validated"

## Corridor Status Template

After validation, each corridor card gets updated with:

```yaml
validation_status:
  tier1_statistical:
    z_score: 12.3
    p_value: "<0.001"
    result: "confirmed"
    date_tested: "2026-03-28"
  tier2_replication:
    languages_tested: ["eng", "lat", "grc"]
    replication_rate: 0.35
    result: "confirmed"
    date_tested: "2026-03-28"
  tier3_expert:
    pairs_reviewed: 50
    confirmed: 32
    plausible: 12
    rejected: 6
    result: "validated (88% confirmed+plausible)"
    date_tested: null  # Awaiting expert review
  tier4_chronological:
    result: "pending"
    date_tested: null
  overall_status: "statistically confirmed, awaiting expert review"
```

## Cross-Corridor Validation

When multiple corridors fire for the same Arabic-target pair, evidence compounds:

| Corridors Firing | Confidence Multiplier | Interpretation |
|-----------------|----------------------|----------------|
| 1 corridor | 1.0× | Standard match |
| 2 corridors | 1.5× | Reinforced match |
| 3+ corridors | 2.0× | Strong convergent evidence |
| C01 + C02 (guttural + emphatic) | 2.5× | Double phonological pathway |
| C03 (article) alone | 3.0× | Near-certain loanword |

## Implementation

The validation pipeline will:
1. Load corridor cards from `Juthoor-Origins-LV3/data/corridors/`
2. Map each corridor to its MultiMethodScorer method
3. Run Tier 1 permutation tests automatically
4. Run Tier 2 replication checks automatically
5. Generate validation report for Tier 3/4 manual review
6. Update corridor cards with validation_status

## Timeline
- **Phase 1 (automated):** Tier 1 + Tier 2 — can be done now with existing data
- **Phase 2 (manual):** Tier 3 — requires researcher time (~2 hours per corridor)
- **Phase 3 (manual):** Tier 4 — requires historical linguistics expertise
