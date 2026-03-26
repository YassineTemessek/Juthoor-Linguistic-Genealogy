# Root Prediction: How Well Does the Genome Predict Root Meanings?

**Source:** LV1_EXECUTIVE_SUMMARY.md, method_a_v5_consensus_weighted.md, Juthoor LV1 experiments
**Calibration method:** Method A (human-judged accuracy on stratified 100-root sample)
**Date:** 2026-03-26

---

## The Root Prediction Problem

Given an Arabic triliteral root (e.g., ك-ت-ب), can we predict its meaning from the letter charges alone?

The genome hypothesis says: yes, to a meaningful extent. The composition chain is:
1. Each letter carries empirical features (e.g., ك = تجمع + إمساك + ضغط)
2. The first two letters form a binary nucleus with a predicted meaning (e.g., كت = gripping + pressure → cutting/reduction)
3. The third letter modifies the nucleus meaning (e.g., ب adds emergence/visibility)
4. The result should approximate the root's actual meaning

The LV1 research tested this prediction system across multiple composition models and calibrated it using Method A — expert-judged assessment of how closely predictions match attested root meanings.

---

## Method A Overview

Method A is a human-calibrated accuracy track rather than a strict automated metric. It was designed to address a key problem with pure Jaccard scoring: the feature vocabulary used in the model is not the same as the full semantic richness of Arabic roots.

**Process:**
1. A stratified sample of 100 Arabic roots is drawn (Quranic and non-Quranic, across confidence bands)
2. For each root, the best prediction from the composition pipeline is retrieved
3. An expert judge rates the prediction on a 4-level scale: exact, partial-high, partial-low, zero
4. The score is weighted by how confidently the system predicts each root

**Scale:**
- **Exact**: the prediction captures the dominant semantic theme of the root
- **Partial-high**: prediction is in the right semantic neighborhood with most features right
- **Partial-low**: prediction shares one or two features with the actual meaning but misses the main theme
- **Zero**: no meaningful overlap

---

## Overall Results

| Metric | Value |
|--------|-------|
| Roots in sample | 100 (99 assessable) |
| Overall weighted Method A score | **49.5 / 100** |
| Baseline before LV1 work (v3) | 36.7 |
| Improvement | +12.8 percentage points |
| Exact-band predictions | 90.9 (those scoring in exact band) |
| Partial-high band score | 65.0 |
| Partial-low band score | 44.2 |
| Zero-band score | 9.8 |
| Empty-actual score | 37.1 |

**Interpretation:** 49.5/100 is the first LV1 score clearly above the midpoint. The genome predicts root meanings meaningfully for about half the Arabic root system. It is not a complete decoder, but it is a significant prior — better than chance, better than any prior scholarly model tested.

The improvement from v3 to v5 (+12.8 points) comes mainly from moving more roots into the *exact* and *partial-high* strata, not from inflating weak cases.

---

## Composition Models Used

The prediction system uses multiple composition models and selects the best prediction via adaptive routing:

### Model 1: Intersection (nucleus_intersection)

Takes features common to both letters in the nucleus. More conservative than union; avoids over-predicting.

Best for: nuclei where both letters share features (e.g., سن: س and ن both carry نفاذ and امتداد).

Weakness: If the letters have few shared features, the intersection is empty.

### Model 2: Nucleus-Only (nucleus_only)

Uses the empirically derived nucleus meaning directly (Jabal's description), without composing from letter features. Falls back to this when letter-level composition fails.

Best for: nuclei with low Jaccard scores where the direct nucleus meaning is available and reliable.

This model is the dominant fallback for about 30-40% of roots.

### Model 3: Phonetic-Gestural (phonetic_gestural)

Uses the phonetic properties of the letters (place and manner of articulation) as an additional signal. Emphatic consonants signal force; pharyngeals signal depth; sibilants signal fine extension.

Best for: letters where the articulatory gesture reliably encodes semantic content (ص, ع, غ, هـ).

### Model 4: Position-Aware (position_aware)

Treats letter 1 and letter 2 asymmetrically. Letter 1 sets the direction; letter 2 specifies or qualifies. Letter 3 modifies the binary nucleus.

This model captures cases where position matters — for example, ب as initiator tends toward emergence (بد, بر), while ب as completer tends toward protrusion (جب, نب).

### Adaptive Routing: How the System Selects a Model

The prediction pipeline does not use a single model. It routes each root to the most appropriate model based on several signals:

1. **Nucleus Jaccard score:** If the nucleus has a high Jaccard (≥ 0.3), use direct composition (intersection or union)
2. **Letter confidence level:** If both letters are HIGH-confidence, prefer composition; if one or both is LOW, fall back to nucleus_only
3. **Third-letter modifier score:** If the third letter is a known strong modifier (ج, ظ, ق), include its contribution; if it is a known risky modifier (ر, ل, م in position 3), reduce weight
4. **Root stratum:** Quranic roots receive higher-confidence treatment; rarer roots are flagged as lower-confidence predictions

---

## Quranic vs. Non-Quranic Accuracy

Quranic Arabic (قرآني) represents the most attested, most analyzed, and most semantically stable portion of classical Arabic. Juthoor tested whether Quranic roots predict better than non-Quranic roots.

**Result:** Quranic roots do show systematically higher prediction accuracy. This is consistent with two hypotheses:
1. Quranic roots are more semantically "pure" — closer to the underlying compositional system
2. Quranic roots are more thoroughly documented, allowing better empirical calibration

The gap is meaningful but not dramatic — the system works across both strata, with Quranic showing higher exact-band hit rates.

---

## Third-Letter Modifier Profiles

The third letter of a root acts as a **modifier** of the binary nucleus's meaning. Modifier profiling was conducted using consensus-based root predictions across 456 nuclei.

### Strongest Supportive Modifiers

| Letter | Mean Blended Score | Nonzero Rate | Primary Signature |
|--------|-------------------|--------------|-------------------|
| ج | 0.274 | 0.782 | اكتناز (dense compaction) |
| ظ | 0.293 | 0.750 | ثخانة (thick substance) |
| ق | 0.247 | 0.753 | ثقل (weight/deep force) |

When ج, ظ, or ق appear in third position, they reliably contribute their empirical meaning to the root prediction. These are semantically stable modifiers.

### Risky Modifiers (frequent prediction failures)

| Letter | Issue |
|--------|-------|
| ر | Generates spaciousness/softness as emergent quality — poisons التحام predictions |
| ل | Attachment-and-extension sometimes contaminates gathering predictions |
| م | Gathering in third position often produces interaction products not predictable from features |
| ت | Precise cutting as modifier produces result-states not encoded in its features |

The biggest repeated poison pattern is **التحام** (fusion/merger). It especially contaminates predictions under ر, ل, and م when these appear in third position.

### Notable Third-Letter Signatures

| Letter (L3) | Signature |
|-------------|-----------|
| ء | انتقال + تأكيد (movement + emphasis) |
| ب | بروز + رجوع + ظاهر (protrusion + return + visible) |
| ث | انتشار (spreading/dispersal) |
| غ | باطن (interior/concealed) |
| ض | إمساك + ثخانة (holding + thick substance) |
| ك | إمساك + اكتناز (gripping + compaction) |

---

## What the Score Means in Practice

A Method A score of 49.5/100 means:

- For roots where the nucleus Jaccard is high (the "genome works" cases), the system predicts with 65-91% accuracy
- For roots where the nucleus involves emergent interaction, the system degrades to 9-44%
- The overall system is "meaningfully better than chance" for about half the Arabic root inventory
- It is not a complete decoder — the other half requires interaction rules not yet implemented

**Practical use:** Trust predictions for roots in high-J nuclei families (ضم, سر, قن, غم, مد, مم, مك). Treat predictions for low-J nuclei (بر, قر, رج, هـز) as directional hints requiring external validation.

---

## Why 49.5 Is a Strong Result

For context:
- A random feature-prediction baseline for Arabic roots would score near 0 on Method A
- The best prior scholarly model tested (Jabal-only, unweighted) scored approximately 36 on the same metric
- Human intuition without the genome theory scores approximately 20-30% on strict Jaccard
- The 49.5 result uses 28 empirically derived letter meanings + 456 nucleus descriptions + adaptive routing across 4 models

The gain of +12.8 over baseline reflects the improvements made during LV1: empirical letter corrections (especially م, ع, غ, ب), better modifier profiling, and the adaptive routing system that falls back to nucleus-only when letter composition is likely to fail.

The ceiling for a purely additive genome model is probably around 55-60 on Method A. Reaching above that will require explicit interaction rules — the work of LV2.
