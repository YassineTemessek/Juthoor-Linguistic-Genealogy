# Phase 3 Root Prediction — Method A Calibration v2
**Date:** 2026-03-23
**Reviewer:** Claude Opus 4.6
**Baseline:** v1 report at `root_method_a_calibration.md` (Method A ~32%, Method B 13.5%)
**Fixes applied:** S3.9 (phonetic_gestural: all features, no sifaat), S3.10 (5 synonym groups), S3.11 (68 empty-actual recovered)
**Model routing:** Intersection (1085, was 518), Phonetic-Gestural (781, was 1193), Sequence (71, was 218), Empty (1)
**Sample:** 60 roots — 12 exact, 12 partial_hi (J≥0.5), 12 partial_lo (0<J<0.5), 12 zero, 12 empty_actual

---

## Delta Summary (v1 → v2)

| Metric | v1 | v2 | Delta |
|--------|----|----|-------|
| Nonzero predictions | 692 (35.7%) | 899 (46.4%) | +207 (+30%) |
| Mean Jaccard | 0.1345 | 0.1496 | +0.015 (+11%) |
| Mean weighted Jaccard | 0.1316 | 0.1424 | +0.011 (+8%) |
| Exact matches (J=1.0) | 39 | 42 | +3 |
| Partial (0<J<1) | 651 | 856 | +205 (+31%) |
| Zero (J=0, has actuals) | 1,041 | 901 | -140 |
| Empty actual | 207 | 139 | -68 |
| Intersection model share | 26.7% | 56.0% | +29pp |
| Phonetic-gestural share | 61.6% | 40.3% | -21pp |

**Key structural change:** Intersection is now the dominant model (56% of roots). This is because the fixes expanded feature overlap, letting more roots qualify for intersection instead of falling back to phonetic_gestural. This is the right direction — intersection was always the better model.

---

## EXACT MATCH STRATUM (12 entries, J=1.0)

| # | Root | Model | Pred | Actual | A Score | Notes |
|---|------|-------|------|--------|---------|-------|
| 1 | غسق | intersection | باطن | عمق | 90 | غسق = darkness. باطن≈عمق via synonym group. Dark = deep/inner. Correct |
| 2 | غرق | intersection | باطن | عمق | 92 | غرق = drowning/sinking deep. Same synonym match. Correct |
| 3 | دون | intersection | باطن | باطن | 95 | دون = below/beneath. Inner/hidden. Exact |
| 4 | مقت | intersection | غلظ | غلظ | 88 | مقت = loathing/abhorrence. Coarseness of feeling. Good but metaphorical |
| 5 | أدد | intersection | امتداد+ضغط | ضغط+امتداد | 98 | إدّ = monstrous thing. Extension+pressure = overwhelming force. Perfect |
| 6 | روض-ريض | intersection | رخاوة | رخاوة | 95 | روضة = garden. Softness/ease. Exact |
| 7 | زمر | intersection | تجمع+اكتناز | تجمع | 90 | زمر = groups. Gathering. اكتناز is legitimate synonym (compaction). Correct |
| 8 | خضض | intersection | رخاوة | رخاوة | 92 | Softness/yielding. Exact |
| 9 | جنن | intersection | كثافة | كثافة | 88 | جنة = paradise/concealment. Density (of vegetation/covering). Good |
| 10 | سرمد | intersection | امتداد | امتداد | 95 | سرمد = eternal. Extension (of time). Exact |
| 11 | هضض | intersection | غلظ | غلظ | 90 | Grinding/crushing implies thickness/coarseness. Exact |
| 12 | كبب | intersection | تجمع | تجمع | 95 | كبكبوا = tumbled/heaped together. Gathering. Exact |

**Exact stratum Method A mean: 92.3** (v1: 89.1, +3.2)

All 12 are through intersection. Quality is high — synonym groups are working (باطن≈عمق for غسق, غرق). No trivial empty-empty matches in this sample.

---

## PARTIAL HIGH STRATUM (12 entries, J≥0.5)

| # | Root | Model | Pred | Actual | J(B) | A Score | Notes |
|---|------|-------|------|--------|------|---------|-------|
| 1 | محص | intersection | خلوص | خلوص+فراغ+غلظ | 0.50 | 70 | تمحيص = purification. Purity (خلوص) is the core. Missed void+thickness aspects |
| 2 | حبب | intersection | تجمع | تجمع+دقة+لطف | 0.50 | 65 | حب = love/grain. Gathering core correct. Missed fineness (grain-like quality) |
| 3 | كشش | phon_gest | خروج+قوة+التحام+تفشي+انتشار+دقة | خروج+لطف+انتشار | 0.60 | 60 | Over-predicts massively (6 features vs 3 actual). Hits 3/3 actual features but adds 3 noise features |
| 4 | رين | intersection | باطن | ظاهر+باطن | 0.50 | 75 | ران = to cover/rust over hearts. Inner dimension correct. Missed ظاهر (the covering is visible) |
| 5 | غشش | intersection | كثافة | رقة+كثافة | 0.50 | 65 | غش = deception/covering. Density captured. Missed fineness (subtle deception) |
| 6 | وهج | intersection | حدة | احتواء+حدة | 0.50 | 80 | وهّاج = blazing. Sharpness/intensity correct. Missed containment |
| 7 | نعج | phon_gest | رخاوة+رقة+تجمع+حدة | رخاوة+رقة | 0.50 | 65 | نعجة = ewe. Softness+fineness captured. Over-predicts تجمع+حدة |
| 8 | زرع | intersection | دقة | دقة+امتداد | 0.50 | 70 | زرع = sowing/planting. Fineness (seed) correct. Missed extension (growth) |
| 9 | عجج | intersection | تجمع | تجمع+غلظ | 0.50 | 70 | عج = dust clouds. Gathering correct. Thickness missed |
| 10 | عشش | phon_gest | اتصال+اشتمال+تفشي+انتشار+دقة | اتصال+اشتمال+حيز+لطف | 0.60 | 65 | Nest-building. Connection+containment correct. Over-predicts spreading+fineness. Misses حيز (space) |
| 11 | زرر | phon_gest | نفاذ+دقة+إمساك+استرسال+تماسك | نفاذ+دقة+تجمع+إمساك | 0.50 | 60 | Button/fastener. 3/4 actual features hit. Over-predicts استرسال+تماسك, misses تجمع |
| 12 | دثث | intersection | كثافة | إبعاد+كثافة | 0.50 | 65 | Covering/wrapping. Density correct. Missed distancing |

**Partial-high stratum Method A mean: 67.5** (v1 partial was 58.7, +8.8)

**New pattern:** Phonetic-gestural now produces 4-6 features per prediction (was 2 in v1). This increases recall (more hits) but also increases false positives. The model has swung from under-prediction to over-prediction for phonetic_gestural roots.

---

## PARTIAL LOW STRATUM (12 entries, 0 < J < 0.5)

| # | Root | Model | Pred | Actual | J(B) | A Score | Notes |
|---|------|-------|------|--------|------|---------|-------|
| 1 | فصص | intersection | قوة | ظاهر+ظهور+تميز+قوة | 0.33 | 55 | فصّ = gem setting. Force is there but minor. Main meaning is manifestation+distinction |
| 2 | نهـر | phon_gest | فراغ+استرسال+تماسك | رقة+اتساع+استرسال+اختراق | 0.17 | 40 | نهر = river. Flow (استرسال) caught. But void+cohesion wrong; should be fineness+width+penetration |
| 3 | دنو | phon_gest | باطن+امتساك+اشتمال+احتواء | وصول+جوف | 0.25 | 35 | دنا = to approach. Inner (باطن≈جوف via synonyms) should score but doesn't catch وصول (arrival) as the core |
| 4 | لفف | phon_gest | ظاهر+كثافة+طرد+إبعاد+نفاذ+قوة | ظاهر | 0.17 | 25 | التفّ = to wrap. Outer/visible correct but 5 noise features. Massive over-prediction |
| 5 | شهد | phon_gest | فراغ+احتباس+ضغط+امتداد+طول | حيز+امتساك | 0.20 | 20 | شهد = to witness. Space+firmness is what Jabal has. Void+pressure+extension misses badly |
| 6 | جذذ | intersection | غلظ | قطع+قوة+غلظ | 0.33 | 55 | جذاذ = fragments. Coarseness is one aspect. Cutting+force are primary meaning |
| 7 | كثث | intersection | كثافة | كثافة+دقة+ظاهر | 0.33 | 60 | Thickness/density core correct. Missed fineness+manifestation |
| 8 | هيل | phon_gest | فراغ+تعلق+امتداد+استقلال+تميز | فراغ+تخلخل+تجمع+تماسك+تعلق | 0.25 | 40 | مهيل = crumbling sand. Void+attachment hit. But 3 wrong + 3 missed |
| 9 | جزأ | phon_gest | تميز+استقلال+تأكيد+ضغط+تقوية | إمساك | 0.20 | 25 | جزء = part/portion. Distinction is conceptually close to إمساك (holding a piece). Weak |
| 10 | فقق | intersection | عمق | اختراق+عمق+كثافة | 0.33 | 60 | فقّ = to hatch/crack. Depth correct. Penetration+density missed |
| 11 | سنهـ | sequence | تلاصق+امتداد | امتداد+فراغ | 0.33 | 50 | سنة = year/dozing. Extension correct. Adhesion wrong, should be void |
| 12 | عزز | intersection | تماسك | تماسك+رخاوة+تخلخل+قوة+غلظ | 0.20 | 40 | عزّة = might/honor. Cohesion is one aspect. Missing force+coarseness as primary |

**Partial-low stratum Method A mean: 42.1**

---

## ZERO MATCH STRATUM (12 entries, J=0)

| # | Root | Model | Pred | Actual | A Score | Notes |
|---|------|-------|------|--------|---------|-------|
| 1 | بلد | intersection | امتداد | ظاهر+نفاذ | 10 | بلد = town. Extension ≠ manifestation+penetration. Wrong |
| 2 | رتق | intersection | امتساك | التحام+جوف | 30 | رتق = to mend/seal. Holding firm is conceptually close to fusion. Synonym gap: امتساك should overlap with التحام |
| 3 | عيش | intersection | اتصال | امتداد+انتقال | 15 | عيش = living. Connection ≠ extension+movement. Wrong |
| 4 | أبد | phon_gest | ظهور+تأكيد+ضغط+تقوية | امتداد | 15 | أبد = eternity. Extension (of time) is the core. Appearance+force is wrong |
| 5 | شيد | intersection | امتساك | قوة | 30 | مشيد = built high/fortified. Firmness is conceptually close to force. Synonym gap |
| 6 | خطف | intersection | إمساك | رخاوة+لطف | 5 | خطف = to snatch. Holding ≠ softness/delicacy. Completely wrong |
| 7 | سبت | intersection | دقة | سطح+ظاهر+امتداد+حدة+باطن | 0 | سبت = sabbath/rest. Fineness has no connection to surface+manifest+extension. Wrong |
| 8 | عيب | intersection | رخاوة+تخلخل | فراغ+التحام+ظاهر | 20 | عيب = flaw. Looseness is conceptually close to فراغ (void/gap). Partial concept overlap |
| 9 | جحم | intersection | باطن | حدة+غلظ | 15 | جحيم = hellfire. Inner ≠ intensity+coarseness. Misses the defining features |
| 10 | صور | phon_gest | قوة+إمساك+ضغط+انتشار+اشتمال+احتواء | تعقد+تجمع | 10 | صورة = form/shape. Complexity+gathering. Force chain is wrong |
| 11 | طفأ | phon_gest | وصول+امتداد+اشتمال+تأكيد+ضغط+تقوية | نقص | 5 | أطفأ = to extinguish. Diminishing/reduction. 6-feature over-prediction completely wrong |
| 12 | خصف | phon_gest | دقة+طرد+إبعاد+نفاذ+قوة | تجمع | 5 | يخصفان = to patch/layer. Gathering (layering). Fineness+expulsion is wrong |

**Zero stratum Method A mean: 13.3** (v1: 16.3, -3.0)

Slightly worse than v1 — the phonetic_gestural over-prediction makes wrong predictions even more wrong (more noise features, same 0 correct ones).

---

## EMPTY ACTUAL STRATUM (12 entries, no Jabal features)

| # | Root | Pred | Verse | Assessment |
|---|------|------|-------|------------|
| 1 | أمد | تلاصق+امتداد+تأكيد+ضغط+تقوية | أمد بعيد | Partial: امتداد (extension) is clearly right for "distant span". But 4 noise features |
| 2 | جزى | تميز+استقلال | الجزية | Good: recompense = distinguishing/separating debts |
| 3 | يقت | دقة | الياقوت | Weak: ruby → fineness? Hardness/density better |
| 4 | رعى | رقة | أماناتهم وعهدهم راعون | Weak: رعاية = tending/care. Fineness ≠ care |
| 5 | صفح | رقة+غلظ | تصفحوا | Interesting: صفحة = page (thin) + forgiveness (thick-skinned). Both textures present |
| 6 | سبغ | دقة | أسبغ عليكم نعمه | Weak: إسباغ = to shower/complete. Fineness wrong |
| 7 | لقب | إمساك+صدم+حيز+قوة+تجمع+رخاوة+تلاصق | الألقاب | Wrong: Over-predicts 7 features. Labels ≠ force chain |
| 8 | وسن | تلاصق | لا تأخذه سنة | Weak: سنة = drowsiness. Adhesion doesn't fit |
| 9 | ينع | رقة | ينعه | Partial: ينع = ripening fruit. Fineness/softness is plausible |
| 10 | ثرى | تجمع+انتشار | تحت الثرى | Good: ثرى = moist earth. Gathering+spreading (of moisture in soil) |
| 11 | دفف | ضغط | (دف) | Plausible: دف = to push/drive. Pressure fits |
| 12 | تجر | استرسال+تماسك | التجارة | Partial: trade = flowing exchange + binding agreements. Plausible but speculative |

**Empty actual assessment:** 2 good (17%), 4 partial (33%), 6 weak/wrong (50%)
**Estimated Method A: ~35** (same as v1 — these roots need extracted features, not better predictions)

---

## Overall Method A v2 Verdict

| Stratum | Count | % | Method B | Method A | vs v1 A |
|---------|-------|---|----------|----------|---------|
| Exact (J=1.0) | 42 | 2.2% | 1.0 | 92.3 | +3.2 |
| Partial high (J≥0.5) | ~300* | ~15.5% | ~0.55 | 67.5 | +8.8 |
| Partial low (0<J<0.5) | ~556* | ~28.7% | ~0.25 | 42.1 | — |
| Zero (J=0) | 901 | 46.5% | 0.0 | 13.3 | -3.0 |
| Empty actual | 139 | 7.2% | 0.0 | ~35 | 0 |

*Estimated split of the 856 partial roots based on sample distribution

**Weighted Method A estimate:**
(42×92.3 + 300×67.5 + 556×42.1 + 901×13.3 + 139×35) / 1938 = **~33.8**

**vs v1: 32.4 → 33.8 (+1.4 points)**

---

## Analysis: Why Only +1.4 Points Despite Big Structural Improvement?

The fixes delivered real structural gains:
- **+207 roots moved from zero to partial** (the biggest win)
- **Intersection dominance** (56% vs 27%) — better model routing
- **Empty-actual down** by 68 roots

But Method A barely moved because of a **new problem the fixes introduced:**

### New Pattern: Phonetic-Gestural Over-Prediction

The v1 phonetic_gestural predicted 2 features per root (truncated).
The v2 phonetic_gestural predicts **4-7 features per root** (all nucleus features + all third-letter features).

This trades under-prediction for over-prediction:
- v1: 2 predicted features, 0-1 correct → low recall, but wrong features are few
- v2: 5-6 predicted features, 1-2 correct → better recall, but 3-4 noise features **tank Jaccard**

Example: كشش predicts 6 features, hits 3/3 actual, but Jaccard = 0.6 (not 1.0) because of 3 false positives.

### The Intersection Model Is Working Well

Intersection predictions are clean: 1-2 features, high precision. The model is doing exactly what it should — finding shared semantic signals. The problem is entirely in the phonetic_gestural fallback.

### Empty-Actual Remains a Ceiling

139 roots with no extractable features → all scored as 0 regardless of prediction quality. This is 7.2% of roots contributing 0 to the weighted average.

---

## Concrete Recommendations for Next Pass

### R7: Cap phonetic_gestural output to top 2-3 features (HIGH IMPACT)
The model now over-predicts. Apply a precision filter: take only the nucleus features that appear in the same *category* as a third-letter feature (or vice versa). Alternatively, hard-cap at 3 predicted features, prioritizing nucleus features.

### R8: Weighted Jaccard with recall bonus (MEDIUM IMPACT)
Current Jaccard penalizes over-prediction heavily. Consider a scoring variant: `F1 = 2 * (precision * recall) / (precision + recall)` which balances false positives against false negatives. This would better reward phonetic_gestural roots that hit all actual features but also predict extras.

### R9: Targeted empty-actual extraction for top 50 Quranic roots (MEDIUM IMPACT)
Of the 139 empty-actual roots, ~60 have Quranic verses. These are the most valuable. Manual/targeted extraction of their Jabal meanings would directly improve coverage.

### R10: Category-level partial scoring (LOW-MEDIUM)
When predicted and actual features are in the same category but not the same word, count as 0.3 instead of 0. Examples: امتساك↔التحام (both cohesion), قوة↔غلظ (both pressure_force/texture).

### Previous recommendations status:
- R1 (all features): DONE by Codex → swung to over-prediction, needs R7 cap
- R2 (synonym groups): DONE by Codex → working well for intersection model
- R3 (drop sifaat): DONE by Codex → BUT phonetic_gestural now pulls from articulatory features again? Need to verify
- R4 (empty-actual recovery): DONE by Codex → 68 recovered, 139 remain

---

## Sprint 3 Updated Verdict

**Method A v2: ~33.8%** (target >55%). Marginal improvement (+1.4pp) despite significant structural gains.

The fixes correctly shifted model routing toward intersection (the better model) and recovered empty-actual roots. But the phonetic_gestural model swung from under-prediction to over-prediction, neutralizing the gains for the 40% of roots still on that pathway.

**Next high-impact fix:** R7 (cap phonetic_gestural at 2-3 features). This should compress false positives without losing the recall gains, potentially lifting Method B from 0.15 to 0.18-0.20 and Method A to ~38-42%.

**Realistic assessment:** Reaching >55% Method A will likely require *both* R7 (precision cap) and a deeper scoring reform (R8 or R10). The single-number Jaccard metric is fundamentally harsh on roots where the prediction captures the right semantic *direction* but uses slightly different vocabulary.
