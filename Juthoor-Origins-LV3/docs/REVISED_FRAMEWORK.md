# Revised Theoretical Framework

**After Null Model Validation — 2026-03-27**

## The Core Question Restated

The null model results force a sharper statement of what the Juthoor project can and cannot claim.

### What We CAN Claim (Statistically Validated)

1. **Arabic root structure is non-arbitrary (LV1):**
   - Binary nuclei define coherent semantic fields (>11σ)
   - Consonant order is meaningful (p=0.014)
   - Position 1 carries most semantic weight (86% of letters)
   - Meaning is 71.6% predictable from structure
   - **These are properties of Arabic, not cross-linguistic claims.**

2. **Expert-curated cognate pairs show systematic consonant correspondences:**
   - 3,461 consonant alignments from 861 verified pairs
   - ع deletion at 88% (Khashim's Law)
   - Bilabial cluster {b,p,f,v} interchangeability
   - ق→c as primary correspondence (39%)
   - **These describe KNOWN cognate pairs, not discovered ones.**

3. **Semitic-Semitic cognate detection works (with embeddings):**
   - GenomeScorer achieves MRR 0.837 for Arabic↔Hebrew
   - This uses embedding-based semantic similarity, not just consonants
   - **Within Semitic, the genome metaphor is validated computationally.**

### What We CANNOT Claim (Not Yet Validated)

1. **Cross-family cognate DISCOVERY exceeds random chance:**
   - Null model: z=0.0, all 12 methods = random
   - Even gloss filtering doesn't help
   - **Consonant-based matching alone cannot discover cross-family cognates**

2. **The "linguistic genome" extends beyond Semitic:**
   - Arabic root structure properties (H2, H5, H8, H12) are real within Arabic
   - Whether other language families share this structure is UNKNOWN
   - The discovery pipeline cannot yet validate this

## Why the Null Model Shows No Signal

The fundamental issue: **consonant matching is frequency-driven, not meaning-driven.**

Arabic has ~28 consonants with specific frequency distributions. English has ~21 consonants with different frequencies. When Arabic consonant projections (via LATIN_EQUIVALENTS, sound laws) generate Latin-alphabet strings, these strings match English consonant skeletons at rates determined by the joint frequency distribution — NOT by etymological relationships.

Shuffling Arabic roots preserves the consonant frequency distribution. Therefore, shuffled roots produce the same match rates.

**This is not a bug — it's a fundamental limitation of consonant-only comparison.**

## The Path Forward

### Option A: Embedding-Based Discovery (Most Promising)
- Use BGE-M3 semantic embeddings to compute meaning similarity
- Only consider pairs with BOTH high semantic AND high phonetic scores
- The semantic dimension provides the discriminative power that consonants cannot
- **Requires GPU or API access to embedding models**

### Option B: Conditional Testing (Alternative)
- Instead of "does the pipeline find cognates?", ask "given a KNOWN cognate pair, does the pipeline rank it higher than non-cognates?"
- This is the MRR-based null model approach
- If MRR_real > MRR_null, the pipeline has SOME discriminative power
- **Being tested now**

### Option C: Frequency-Corrected Scoring (Research)
- Weight consonant matches by their RARITY, not their presence
- A match on rare consonants (ق, ظ, ع) should count MORE than a match on common consonants (ر, ل, ن)
- This could de-bias the frequency effect
- **Not yet implemented**

### Option D: Historical Evidence Integration (Expert)
- Instead of purely computational discovery, integrate:
  - Attestation dates from etymological dictionaries
  - Historical contact evidence (trade routes, conquest, scholarship)
  - Phonological regularity tests (do the correspondences follow known sound laws?)
- **Requires expert linguist collaboration**

## Revised Project Scope

| Scope | Status | Confidence |
|-------|--------|------------|
| Arabic root structure is non-arbitrary | **Validated** | Very high (>11σ) |
| Arabic root meaning is predictable | **Validated** | High (cosine 0.716) |
| Semitic-Semitic cognate detection | **Validated** | High (MRR 0.837) |
| Expert-curated correspondences | **Described** | High (3,461 alignments) |
| Cross-family cognate discovery | **Not validated** | Requires embedding-based scoring |
| "Linguistic genome" extends to IE | **Hypothesis only** | Requires validation |
| 10 corridor cards | **Provisional** | Need re-validation with semantic data |
| Convergent evidence (153 roots) | **Computational observation** | Not yet statistically validated |
