# Research Directions: Next Phase

Based on the mega sprint findings, here are the prioritized research directions.

## Priority 1: Semantic-Filtered Discovery (Blocking)

**Problem:** Fast-mode discovery = random chance (null model z=0.0)
**Solution:** Add semantic filtering — either GPU-based (BGE-M3) or lightweight (gloss overlap)
**Expected impact:** If semantic filtering works, real cognates should score HIGH on both phonetic AND semantic axes, while false friends score high on phonetic but LOW on semantic.
**Key test:** Re-run null model with semantic filter. If z > 3.29 (p < 0.001), the filtered pipeline IS discriminative.

## Priority 2: Validate the Consonant Correspondence Matrix

**Status:** 3,461 alignments from 861 EXPERT-CURATED gold pairs are empirically valid.
**Question:** Do these correspondences (ع→deletion at 88%, ب→b/p, ق→c) generalize to NON-curated data?
**Test:** Score 1000 random Arabic-English pairs from LV0 corpora, compute consonant alignment, compare distribution against the gold-pair matrix.
**Expected:** If correspondences are real, gold-pair matrix should differ significantly from random-pair matrix.

## Priority 3: Diachronic Tracking

**Available data:** Old English (7,948 entries), Middle English (49,779 entries), Modern English (1.4M entries)
**Hypothesis:** Arabic cognates should be closer to Old/Middle English forms than Modern English forms (because older forms preserve more consonant structure).
**Test:** For each Arabic-English gold pair, compute consonant skeleton similarity against OE, ME, and ModE forms. If Arabic matches OE better, that suggests deep inheritance rather than recent contact.
**Why this matters:** Diachronic evidence can distinguish inherited cognates from loanwords without chronological expertise.

## Priority 4: Semitic Internal Validation

**Strongest data:** Arabic↔Hebrew pairs with GenomeScorer (MRR 0.837 in embedding mode)
**Question:** Can the H2/H8/H12 findings predict Hebrew cognates?
**Test:** Use H12 meaning predictor scores to predict which Arabic roots have Hebrew cognates. If roots with high H12 scores (well-formed, predictable meaning) have MORE Hebrew cognates, the "genome" metaphor is validated cross-linguistically within Semitic.

## Priority 5: Akkadian Deep Comparison

**Why:** Akkadian is the oldest documented Semitic language (~2500 BCE).
**Available:** 50-entry test corpus (minimal but includes known cognates like sharru/Arabic sariy, kalbu/kalb, shamash/shams)
**Goal:** Demonstrate that Arabic root structure has continuity over 4,500 years.
**Need:** Full Akkadian Kaikki dump (likely 5K-20K entries)

## Priority 6: Turkish Loanword Layer

**Why:** Turkish borrowed massively from Arabic during Ottoman period (~600 years of contact).
**Expected result:** Arabic→Turkish discovery should show TWO distinct layers:
1. Loanwords (high consonant preservation, post-Islamic terminology)
2. Potential deeper connections (if any — controversial)
**Loanword detector:** The loanword_detector.py module should flag high-similarity matches as loans.

## Priority 7: Publication Preparation

Once semantic filtering validates the corridors (Priority 1), prepare:
1. Reproducible methodology document (written)
2. Statistical validation with permutation tests (tool built)
3. Expert review of top 200 gold-anchor leads (needs human)
4. Chronological validation of attested forms (needs expert)
5. Frozen research bundle for peer review (built, 25 files)

## Non-Priorities (Parked)

- **QCA integration:** Quranic semantic vectors exist but adding another feature doesn't help if the base pipeline = random chance
- **More languages:** Turkish, Akkadian, Sanskrit are interesting but won't fix the core statistical issue
- **Reranker tuning:** Reranker v3 is trained but can't improve a pipeline that doesn't distinguish signal from noise
- **UI/visualization:** Important for presentation but doesn't advance the science
