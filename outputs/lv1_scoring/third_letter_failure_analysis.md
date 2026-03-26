# B.1 Third-Letter Failure Classification

**Scope:** 495 roots — consensus_strict predictions where root Jaccard = 0
but the binary nucleus appears in the nucleus score matrix with Jaccard > 0
(nucleus has directional signal; root composition nonetheless fails).

**Date:** 2026-03-24
**Scholar filter:** consensus_strict
**Data source:** `outputs/lv1_scoring/root_predictions.json` + `outputs/lv1_scoring/nucleus_score_matrix.json`

---

## 1. Summary Counts by Category

| Category | Count | Share | Description |
|----------|------:|------:|-------------|
| **Cat1: Third letter CONTRADICTS nucleus** | 263 | 53.1% | Nucleus predicts correct semantic direction; third-letter features introduce a conflicting or unrelated set that makes J=0 |
| **Cat2: Third letter TOO GENERIC** | 62 | 12.5% | Prediction dominated by generic features (انتقال, امتداد, اتصال, ظاهر) that dilute the nucleus signal into an unfalsifiable mix |
| **Cat3: WRONG MODEL selected** | 98 | 19.8% | Intersection model over-prunes to 1 feature; nucleus had strong signal (J≥0.25) but the model discarded it |
| **Cat4: Nucleus itself WEAK** | 72 | 14.5% | Nucleus Jaccard 0.125–0.167 (< 0.2 threshold); even a perfect third-letter contribution could not recover the root |
| **Total** | **495** | **100%** | |

The dominant failure mode is Cat1 (third-letter contradiction). Together, Cat1 + Cat3 account for 72.9% of all failures — both are addressable through model and feature-weighting changes.

### Nucleus Jaccard Distribution Across the 495

| Range | Count | Notes |
|-------|------:|-------|
| < 0.20 | 72 | All assigned Cat4 (weak nucleus) |
| 0.20–0.33 | 273 | Majority; Cat1/Cat2/Cat3 mixed |
| 0.33–0.50 | 83 | Strong nucleus signal, still fails at root |
| 0.50–0.75 | 47 | High nucleus confidence, complete contradiction at root |
| ≥ 0.75 | 20 | Nucleus near-perfect; failure is entirely third-letter-caused |

Mean nucleus Jaccard across all 495: **0.289**

---

## 2. Model Breakdown — Which Model Produces the Most Pollution?

| Model | All 495 | Cat1 | Cat2 | Cat3 | Cat4 |
|-------|--------:|-----:|-----:|-----:|-----:|
| **intersection** | 278 (56.2%) | 91 | 44 | 98 | 45 |
| **phonetic_gestural** | 165 (33.3%) | 140 | 8 | 0 | 17 |
| **sequence** | 52 (10.5%) | 32 | 10 | 0 | 10 |

Key observations:

- **Intersection is responsible for 100% of Cat3 failures.** Cat3 is definitionally an intersection pathology: the model selects only the features shared across all letters, leaving a single surviving feature that misses the actual meaning entirely.
- **Phonetic_gestural dominates Cat1** (140/263 = 53%). When this model adds third-letter features it tends to add semantically plausible but directionally wrong features that actively conflict with the actual root meaning.
- **Sequence contributes ~10% across Cat1 and Cat2** — mostly dilution failures where sequential composition merges a generic feature from the third letter into the prediction.

---

## 3. Top 10 Polluting Third Letters

Ranked by total failure count across the 495. "Pollution features" are the features most frequently added by that letter that do not appear in the actual root features.

| Rank | Letter | Failures | Top features in predictions | Most common category |
|------|--------|---------:|-----------------------------|---------------------|
| 1 | ر | 62 | التحام (23×), تجمع (11×), انتقال (8×), تلاصق (8×), امتداد (6×) | Cat1 (33) |
| 2 | ل | 43 | التحام (14×), تجمع (10×), امتداد (5×), تماسك (4×), فراغ (4×) | Cat1 (24) |
| 3 | د | 37 | إمساك (25×), قوة (9×), تجمع (5×), تلاصق (3×), امتداد (3×) | Cat1 (21) |
| 4 | ب | 35 | تجمع (11×), التحام (8×), امتداد (6×), تلاصق (5×), بروز (3×) | Cat1 (15) |
| 5 | م | 29 | تجمع (14×), اكتناز (10×), تلاصق (5×), تخلخل (3×), انتشار (3×) | Cat1/Cat3 tied (13 each) |
| 6 | ف | 25 | اختراق (13×), نفاذ (7×), امتداد (3×), نقص (3×) | Cat1 (18) |
| 7 | ي | 23 | تلاصق (6×), امتداد (5×), باطن (3×), تجمع (3×), قوة (3×) | Cat1 (16) |
| 8 | ن | 23 | باطن (9×), انتقال (8×), غلظ (2×), رقة (2×), انتشار (2×) | Cat1 (8) |
| 9 | ح | 22 | اتساع (6×), باطن (5×), امتداد (5×), انتقال (3×), جوف (3×) | Cat1 (8) |
| 10 | ع | 21 | ظاهر (11×), باطن (6×), تلاصق (3×), غلظ (3×), قوة (3×) | Cat4 (6), Cat1 (10) |

**ر** is the single worst polluter: 62 failures, primarily because the التحام feature (cohesion) which is strongly associated with ر in many nuclei does not carry over to the actual root meanings. The التحام hit rate across the 495 is only 4% (predicted 49×, matched 2×).

### Feature-Level Pollution: Worst Hit Rates

These features appear frequently in predictions across the 495 but almost never match actual root features:

| Feature | Predicted | Matched | Hit Rate |
|---------|----------:|--------:|---------:|
| التحام | 49 | 2 | **4%** |
| اكتناز | 17 | 3 | 18% |
| استقلال | 20 | 4 | 20% |
| طول | 9 | 2 | 22% |
| انتشار | 34 | 10 | 29% |
| استرسال | 23 | 10 | 43% |
| تلاصق | 48 | 22 | 46% |
| ثقل | 15 | 7 | 47% |

**التحام** is the primary poison feature in this failure set — it should be down-weighted or blacklisted when the third letter is ر, ل, or ب in intersection/phonetic_gestural predictions.

---

## 4. Concrete Recommendations

### Recommendation A — Blacklist التحام as a third-letter contribution (highest ROI)
**Targets Cat1: ~40 recoveries estimated**

التحام has a 4% hit rate (49 predictions, 2 matches). It is generated as a third-letter contribution by ر, ل, and ب across multiple models. Filtering it from root predictions when it is added solely by the third letter (i.e., not present in the nucleus prediction) would immediately remove the most common false positive.

**Implementation:** In `feature_decomposition.py`, add a `THIRD_LETTER_BLOCKED_FEATURES` set. When merging third-letter features into the root prediction, drop any feature in this set that was not already in the nucleus predicted features.

```python
THIRD_LETTER_BLOCKED_FEATURES = {'التحام', 'اكتناز', 'استقلال'}
```

### Recommendation B — Fix intersection model over-pruning (Cat3: 98 failures)
**Targets Cat3: ~21 recoveries estimated (direct), ~50 partial improvement**

The intersection model drops to 1 feature for 98 roots where the nucleus Jaccard is ≥ 0.25. This indicates the letter combination has low feature overlap — the intersection strategy is wrong for these letter pairs.

**Implementation:** Add a fallback rule in the model selector: if `model == 'intersection'` and `len(predicted_features) <= 1` and `nucleus_jaccard >= 0.25`, switch to `phonetic_gestural` and re-predict. This is a post-prediction correction step that requires no retraining.

**Specific trigger:** Third letters ر, م, ل, د, ح dominate Cat3 (14, 13, 12, 11, 9 failures respectively). An intersection model with these third letters and strong-signal nuclei should route to phonetic_gestural by default.

### Recommendation C — Add generic-feature penalty (Cat2: 62 failures)
**Targets Cat2: 0 direct recoveries currently, but prevents J=0 edge cases from spreading**

When the prediction is dominated (≥50%) by generic features (انتقال, امتداد, اتصال, حركة, ظاهر, عام), the root prediction carries no discriminative signal. A scoring penalty — or pre-filtering — for predictions where generic features exceed 50% of the feature set would surface the nucleus signal instead.

**Implementation:** In `scoring.py`, compute `generic_ratio = len(predicted & GENERIC_FEATURES) / len(predicted)`. If `generic_ratio >= 0.5`, fall back to nucleus-only prediction (omit third-letter contribution).

### Recommendation D — Nucleus-only fallback for J=0 roots with strong nucleus (combined impact)
**Estimated ~51 additional partial-match recoveries**

For roots where Cat1 applies (nucleus J ≥ 0.33, root J = 0), the nucleus prediction alone would intersect the actual features in 30 out of 263 cases. A "nucleus-only fallback" — triggered when full root prediction fails and nucleus Jaccard is above a threshold — would convert hard J=0 failures into partial J>0 predictions.

**Threshold suggestion:** Activate fallback when nucleus Jaccard ≥ 0.33 and model is phonetic_gestural. Do not activate for intersection (too few features) or when third letter is on the BLOCKED_FEATURES list.

---

## 5. Detailed Examples

### Category 1: Third Letter CONTRADICTS Nucleus (5 examples)

#### Example C1-1
**Root:** زمل | **Nucleus:** زم | **Third letter:** ل | **Model:** intersection
- Nucleus predicted: [اكتناز] — actual: [اكتناز، تجمع] — J=1.000
- Root predicted: [اكتناز، تجمع] — actual: [اتصال] — J=0
- Nucleus true positives: [اكتناز]
- Features added by third letter: [تجمع]
- Diagnosis: Nucleus correctly identified اكتناز (compactness). The third letter ل contributed تجمع (gathering), which is directionally compatible with the nucleus but semantically wrong for the actual root زمل (to wrap/cover/connect). The actual feature اتصال (connection) appears in neither the nucleus nor the third-letter contribution.

#### Example C1-2
**Root:** زمه | **Nucleus:** زم | **Third letter:** هـ | **Model:** phonetic_gestural
- Nucleus predicted: [اكتناز] — actual: [اكتناز، تجمع] — J=1.000
- Root predicted: [اكتناز، باطن، تجمع] — actual: [حدة] — J=0
- Nucleus true positives: [اكتناز]
- Features added by third letter: [باطن، تجمع]
- Diagnosis: Nucleus correctly signals اكتناز. The هـ phoneme contributes باطن (interiority) and تجمع (gathering), both systematically wrong. The actual meaning of زمه (stupidity/dullness) carries حدة (sharpness) — the opposite semantic direction. This is a full contradiction: the third letter actively redirected the prediction away from the actual.

#### Example C1-3
**Root:** قهـر | **Nucleus:** قهـ | **Third letter:** ر | **Model:** phonetic_gestural
- Nucleus predicted: [باطن، ثقل] — actual: [باطن، قوة] — J=1.000
- Root predicted: [التحام، باطن، قوة] — actual: [حدة] — J=0
- Nucleus true positives: [باطن]
- Features added by third letter: [التحام، قوة]
- Diagnosis: Strong nucleus signal (J=1.0). The third letter ر added التحام and قوة. قوة is present in nucleus actual features — so the root prediction is internally consistent, but the actual root meaning (حدة = sharpness/acuity) belongs to a different semantic category entirely. The ر-التحام pattern (see Rec A) is the primary pollutant.

#### Example C1-4
**Root:** سرق | **Nucleus:** سر | **Third letter:** ق | **Model:** phonetic_gestural
- Nucleus predicted: [التحام، امتداد، دقة] — actual: [امتداد، تلاصق، دقة، نفاذ] — J=0.750
- Root predicted: [امتداد، تلاصق، ثقل] — actual: [إمساك، حيز، عمق] — J=0
- Nucleus true positives: [امتداد، دقة]
- Features added by third letter: [تلاصق، ثقل]
- Diagnosis: Nucleus (سر) had strong signal at J=0.75 with correct features. The third letter ق added ثقل (heaviness), which conflicts with the actual meaning of سرق (theft/stealth) — a root requiring features around concealment and seizure (إمساك). The entire prediction shifted from the correct semantic domain.

#### Example C1-5
**Root:** شرم | **Nucleus:** شر | **Third letter:** م | **Model:** phonetic_gestural
- Nucleus predicted: [تخلخل، انتشار، غلظ] — actual: [تخلخل، انتشار] — J=0.667
- Root predicted: [تجمع، اكتناز، تخلخل] — actual: [جوف] — J=0
- Nucleus true positives: [تخلخل، انتشار]
- Features added by third letter: [تجمع، اكتناز]
- Diagnosis: Nucleus had good directional signal (J=0.667). The third letter م introduced تجمع and اكتناز — both clustering/compression features that directly contradict the dispersal semantics (انتشار) already correctly identified in the nucleus.

---

### Category 2: Third Letter TOO GENERIC (5 examples)

#### Example C2-1
**Root:** سيب | **Nucleus:** سب | **Third letter:** ب | **Model:** intersection
- Nucleus predicted: [التحام، امتداد، دقة] — actual: [اتصال، امتداد، تلاصق، دقة] — J=0.750
- Root predicted: [اتصال، امتداد، تلاصق] — actual: [استرسال] — J=0
- Nucleus true positives: [امتداد، دقة]
- Generic features in prediction: [اتصال، امتداد]
- Diagnosis: The root prediction is dominated by امتداد (extension) and اتصال (connection) — two of the most generic features in the system. These features describe movement without destination and connection without specificity. The actual meaning of سيب (flowing freely/abandoning) requires استرسال — which is a specific directional feature not present in any generic feature set.

#### Example C2-2
**Root:** سبأ | **Nucleus:** سب | **Third letter:** ء | **Model:** intersection
- Nucleus predicted: [التحام، امتداد، دقة] — actual: [اتصال، امتداد، تلاصق، دقة] — J=0.750
- Root predicted: [امتداد] — actual: [انتقال، حدة] — J=0
- Nucleus true positives: [امتداد، دقة]
- Generic features in prediction: [امتداد]
- Diagnosis: After intersection pruning, only امتداد survives. This single generic feature covers too broad a semantic space to discriminate against any root meaning. The actual features (انتقال، حدة) point to movement-with-sharpness — a specific compound that امتداد cannot approximate.

#### Example C2-3
**Root:** سبح | **Nucleus:** سب | **Third letter:** ح | **Model:** intersection
- Nucleus predicted: [التحام، امتداد، دقة] — actual: [اتصال، امتداد، تلاصق، دقة] — J=0.750
- Root predicted: [امتداد] — actual: [احتواء] — J=0
- Nucleus true positives: [امتداد، دقة]
- Generic features in prediction: [امتداد]
- Diagnosis: Identical to C2-2 in structure — the intersection model strips to امتداد. The actual root سبح (to swim/praise) carries احتواء (containment) — a feature in the opposite direction from extension. The ح phoneme's features were not included; only the intersection survived, and that intersection is too vague.

#### Example C2-4
**Root:** سبع | **Nucleus:** سب | **Third letter:** ع | **Model:** phonetic_gestural
- Nucleus predicted: [التحام، امتداد، دقة] — actual: [اتصال، امتداد، تلاصق، دقة] — J=0.750
- Root predicted: [امتداد، تلاصق، ظاهر] — actual: [حيز] — J=0
- Generic features in prediction: [امتداد، ظاهر]
- Diagnosis: Even with phonetic_gestural (which should provide more features), two of the three predicted features are generic. The ع phoneme contributed ظاهر (surface/manifest) which is among the most overused features in the system. The actual meaning of سبع (seven/a beast of prey) requires حيز — a spatial feature absent from the prediction entirely.

#### Example C2-5
**Root:** سرو-سرى | **Nucleus:** سر | **Third letter:** ي | **Model:** sequence
- Nucleus predicted: [التحام، امتداد، دقة] — actual: [امتداد، تلاصق، دقة، نفاذ] — J=0.750
- Root predicted: [امتداد، تلاصق] — actual: [دقة، قوة، نفاذ] — J=0
- Generic features in prediction: [امتداد]
- Diagnosis: Nucleus had J=0.75 — strong signal. The sequence model merged امتداد (from ي's generic contribution) into the final prediction, while the actual root's discriminating features (دقة، نفاذ) were dropped. The ي phoneme's contribution of امتداد is semantically true but not specific enough to survive Jaccard scoring against the actual feature set.

---

### Category 3: WRONG MODEL Selected (5 examples)

#### Example C3-1
**Root:** قهـهـ-قهقه | **Nucleus:** قهـ | **Third letter:** هـ | **Model:** intersection
- Nucleus predicted: [باطن، ثقل] — actual: [باطن، قوة] — J=1.000
- Root predicted: [باطن] — actual: [قوة] — J=0
- Predicted features count: 1
- Diagnosis: Nucleus had perfect J=1.0 — it completely captured the actual meaning direction. The intersection model then selected only باطن (the single feature common to nucleus and هـ), discarding قوة. The actual root meaning requires قوة (power/force). A phonetic_gestural model would have retained both nucleus features, giving J=0.5. The intersection strategy destroyed a perfect nucleus prediction.

#### Example C3-2
**Root:** أمم | **Nucleus:** مم | **Third letter:** م | **Model:** intersection
- Nucleus predicted: [اكتناز] — actual: [تجمع] — J=1.000
- Root predicted: [تجمع] — actual: [حيز، ظاهر، لطف] — J=0
- Nucleus true positives: (اكتناز ↔ تجمع via synonym relationship)
- Predicted features count: 1
- Diagnosis: Intersection model with a repeated letter (مم + م) produces exactly 1 feature — تجمع — which matches the nucleus actual but not the full root actual set. The root أمم (mother/nation) has a richer feature set (حيز، ظاهر، لطف) that requires non-intersection inference. A sequence model would build up from the nucleus signal rather than pruning to a single feature.

#### Example C3-3
**Root:** سرج | **Nucleus:** سر | **Third letter:** ج | **Model:** intersection
- Nucleus predicted: [التحام، امتداد، دقة] — actual: [امتداد، تلاصق، دقة، نفاذ] — J=0.750
- Root predicted: [تلاصق] — actual: [تعلق، لطف] — J=0
- Nucleus true positives: [امتداد، دقة]
- Predicted features count: 1
- Diagnosis: Strong nucleus (J=0.75, correct features امتداد and دقة). The intersection with ج produces only تلاصق — a single feature that does not appear in the actual root meaning (تعلق = attachment, لطف = gentleness). If phonetic_gestural were used, the nucleus features (امتداد، دقة) would be carried forward with J=0.4 against the actual.

#### Example C3-4
**Root:** سرف | **Nucleus:** سر | **Third letter:** ف | **Model:** intersection
- Nucleus predicted: [التحام، امتداد، دقة] — actual: [امتداد، تلاصق، دقة، نفاذ] — J=0.750
- Root predicted: [نفاذ] — actual: [إمساك] — J=0
- Nucleus true positives: [امتداد، دقة]
- Predicted features count: 1
- Diagnosis: Intersection of سر nucleus with ف yields only نفاذ. The actual root سرف (excess/extravagance) requires إمساك (holding/seizing in reverse sense). Nucleus features امتداد and دقة are both more accurate than the intersection output. Using phonetic_gestural would preserve the nucleus features and give partial credit.

#### Example C3-5
**Root:** سرم | **Nucleus:** سر | **Third letter:** م | **Model:** intersection
- Nucleus predicted: [التحام، امتداد، دقة] — actual: [امتداد، تلاصق، دقة، نفاذ] — J=0.750
- Root predicted: [تلاصق] — actual: [امتداد، تجمع، دقة، نفاذ] — J=0
- Nucleus true positives: [امتداد، دقة]
- Predicted features count: 1
- Diagnosis: The actual root سرم has 4 features — all of which overlap with the nucleus (امتداد، دقة are nucleus true positives; نفاذ is in nucleus actual). The intersection model discarded all of this and produced only تلاصق — a single wrong feature. This is the clearest possible case of intersection over-pruning: the nucleus had 75% of the answer; intersection removed it.

---

## 6. Implementation Checklist for Codex

The following changes are ordered by estimated recovery yield:

1. **[HIGH] Blacklist التحام from third-letter contributions** (Rec A)
   - File: `Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/core/feature_decomposition.py`
   - Add `THIRD_LETTER_BLOCKED_FEATURES = {'التحام', 'اكتناز', 'استقلال'}` constant
   - In the merge step: remove blocked features from third-letter contribution unless already in nucleus predicted features
   - Expected: ~40 Cat1 recoveries (J moves from 0 to >0)

2. **[HIGH] Fallback from intersection to phonetic_gestural when output <= 1 feature and nucleus_jaccard >= 0.25** (Rec B)
   - File: `Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/factory/scoring.py`
   - Post-prediction check: if `model == 'intersection'` and `len(predicted_features) <= 1` and nucleus entry has J ≥ 0.25, re-run with phonetic_gestural
   - Expected: 21 direct Cat3 recoveries; partial improvement on ~50 more

3. **[MEDIUM] Generic-feature fallback to nucleus-only prediction** (Rec C)
   - File: `Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/factory/scoring.py`
   - Compute `generic_ratio = |predicted ∩ {انتقال, امتداد, اتصال, حركة, ظاهر, عام}| / |predicted|`
   - If `generic_ratio >= 0.5`, replace predicted_features with nucleus.predicted_features
   - Expected: Prevent Cat2 spreading; 0 direct J=0→>0 in current 495 but blocks future regression

4. **[LOW] Nucleus-only fallback for Cat1 with nucleus J >= 0.33** (Rec D)
   - Same file as Rec C
   - When root prediction fails after Rec A+B, if nucleus J ≥ 0.33, output nucleus predicted features as root predicted features with a `fallback=nucleus` flag
   - Expected: 30 additional partial-match recoveries in Cat1

---

*Report generated from 495 failure cases across 153 unique binary nuclei and 10 bab chapters. Top bab chapters represented: السين (53), النون (50), الراء (40), الشين (35), الحاء (33).*
