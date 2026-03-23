# Phase 3 Root Prediction — Method A Calibration Report
**Date:** 2026-03-23
**Reviewer:** Claude Opus 4.6
**Sample:** 60 roots, stratified (15 exact J=1.0, 15 partial 0<J<1, 15 zero J=0, 15 empty_actual)
**Model routing:** Intersection (518), Phonetic-Gestural (1193), Sequence (218), Empty (9)
**Input:** root_predictions.json + root_score_matrix.json (first Phase 3 checkpoint)

---

## Scoring Methodology

**Method B (Jaccard):** Exact synonym-aware feature-set overlap. 0 = no matching features, 1.0 = perfect overlap.

**Method A (semantic):** 0–100 scale.
- 90–100: Prediction captures the root's المعنى المحوري and all major semantic dimensions
- 70–89: Core meaning direction correct, minor features missed or over-predicted
- 50–69: Partial — right semantic neighborhood but key dimensions wrong or missing
- 25–49: Weak — some thematic connection but mostly different vocabulary
- 0–24: Wrong — no meaningful semantic overlap with the root's actual usage

---

## EXACT MATCH STRATUM (15 entries, Jaccard = 1.0)

| # | Root | Model | Pred | Actual | J(B) | A Score | Notes |
|---|------|-------|------|--------|------|---------|-------|
| 1 | خصص | phon_gest | دقة+نفاذ | نفاذ+دقة | 1.0 | 95 | خصاصة = narrowness/penetrating specificity. Perfect semantic fit — خصّ someone = singling out with precision |
| 2 | تلو-تلي | intersection | اتصال | اتصال | 1.0 | 90 | تلاوة = following/connection (reciting = connecting word after word). Correct |
| 3 | عود-عيد | intersection | امتداد | امتداد | 1.0 | 75 | عاد = return. "Extension" captures temporal extension but misses the directional reversal. Acceptable but not perfect |
| 4 | ضحو/ضحى | sequence | اتساع+ظهور | ظهور+اتساع | 1.0 | 98 | الضحى = the wide, visible morning. Expansion + appearance = perfect |
| 5 | شطن | intersection | امتداد | امتداد | 1.0 | 85 | شيطان from شطن = distancing/extending away. Extension is the core. Good |
| 6 | خضع | intersection | رخاوة | رخاوة | 1.0 | 92 | خضوع = softening/yielding. Softness is exactly right |
| 7 | خدن | intersection | جوف | باطن | 1.0 | 90 | خدن = intimate companion (one who enters your inner space). جوف≈باطن via synonyms. Correct |
| 8 | خوو/خوى | sequence | فراغ | فراغ | 1.0 | 98 | خاوية = empty/void. Perfect |
| 9 | عصف | intersection | قوة | قوة | 1.0 | 88 | عصف = violent wind/force. Core correct; misses the directionality (sweeping away) |
| 10 | سنبل | intersection | امتداد | امتداد | 1.0 | 82 | سنبلة = ear of grain. Extension captures the upward growth. Misses the gathering/cluster aspect |
| 11 | هضض | intersection | غلظ | غلظ | 1.0 | 85 | هضم = crushing/grinding implies thickness/coarseness. Good |
| 12 | بدأ | sequence | ظهور | ظهور | 1.0 | 95 | بدأ = to begin = first appearance. Perfect |
| 13 | تيهـ/توهـ | sequence | فراغ | فراغ | 1.0 | 90 | تيه = wandering in void/wilderness. Exact |
| 14 | ونى | sequence | نقص+انتقال | نقص+انتقال | 1.0 | 85 | وني = to weaken/slacken (diminish + movement). Good, though the "movement" is metaphorical |
| 15 | هنن | intersection | باطن+لطف | دقة+باطن | 1.0 | 88 | هنّ = delicate/fine inner thing. لطف≈دقة via synonyms. Correct |

**Exact stratum Method A mean: 89.1** (Method B: 1.0)

**Verdict:** The 39 exact matches (2% of all roots) are genuinely high-quality. Most are semantically accurate, not just coincidental vocabulary overlap. Synonym groups are working correctly (جوف≈باطن, لطف≈دقة).

**Red flag:** 5 of the 39 "perfect" matches are trivial — either empty actual + empty predicted (غوى, ويل) or single-feature intersections where only one generic feature was tested. These inflate the "exact" count by ~13%.

---

## PARTIAL MATCH STRATUM (15 entries, 0 < Jaccard < 1)

| # | Root | Model | Pred | Actual | J(B) | A Score | Notes |
|---|------|-------|------|--------|------|---------|-------|
| 1 | كدد | phon_gest | قوة+احتباس | قوة+تلاصق+امتساك+احتكاك | 0.20 | 55 | كدّ = toil/grinding. Force captured, but missed the physical contact/friction dimension |
| 2 | نظر | phon_gest | إمساك+استرسال | إمساك | 0.50 | 65 | نظر = to look/hold gaze. Holding (إمساك) correct. استرسال (flow) is wrong for looking |
| 3 | بطأ | sequence | ثقل+ضغط | ثقل+انتقال | 0.33 | 60 | بطّأ = to slow down. Heaviness correct. Pressure wrong — should be movement (slowness = heavy movement) |
| 4 | مرر | intersection | استرسال | استرسال+قوة+ضغط | 0.33 | 55 | مرّ = to pass + bitterness. Flow correct, but force/pressure aspects of bitterness missed |
| 5 | رخو-رخى | sequence | رخاوة | رخاوة+جفاف+اشتداد+قوة | 0.25 | 50 | رخاء = ease/softness. Core feature nailed. But Jabal's actual features include paradoxical opposites (softness+hardness) — composition from the root |
| 6 | لكك | phon_gest | تماسك+ضغط | تماسك+اشتداد+قوة | 0.25 | 60 | لكّ = to press/push hard. Cohesion right, pressure is in the force neighborhood. Close |
| 7 | غوط | phon_gest | باطن+ضغط | عمق+غلظ+طول | 0.25 | 55 | غوط/غائط = low depression. باطن≈عمق via synonyms — should be scoring higher. طول (length) and غلظ (thickness) missed |
| 8 | ركز | intersection | تجمع+تماسك | امتساك+تماسك | 0.33 | 70 | ركز = to fix/plant firmly. Cohesion captured. تجمع is close to امتساك (both about concentration) |
| 9 | فضض | intersection | غلظ | كثافة+غلظ+تفرق | 0.50 | 60 | فضّ = to scatter/break up. Thickness captured but scattering (the key action) missed |
| 10 | نجو | phon_gest | نفاذ+اشتمال | خلوص+فراغ+نفاذ | 0.25 | 55 | نجا = to escape/survive. Penetration (getting out) correct. Containment (اشتمال) is backwards — نجاة is about leaving containment |
| 11 | سغب | phon_gest | نفاذ+تجمع | فراغ+جوف+تجمع | 0.25 | 45 | مسغبة = hunger. Gathering correct (hunger = gathering of emptiness?). But the core is void/emptiness, not penetration |
| 12 | بتر | phon_gest | قطع+استرسال | قطع+دقة | 0.33 | 65 | الأبتر = cut off. Cutting exact. استرسال (flow) wrong — should be fineness (precise cut) |
| 13 | دحو-دحي | phon_gest | ضغط+اتصال | ضغط | 0.50 | 70 | دحا = to spread (the earth). Pressure correct (flattening force). اتصال (connection) is over-prediction |
| 14 | غيظ | phon_gest | قوة+نفاذ | وحدة+حدة+قوة+جوف | 0.20 | 50 | غيظ = intense anger. Force correct. But missed شدة/حدة (sharpness/intensity) and جوف (inner) |
| 15 | صهـر | sequence | استرسال+تماسك | تماسك | 0.50 | 65 | صهر = to melt/fuse. Cohesion (fusion) correct. استرسال (flow) is plausible for melting but not in Jabal's actual |

**Partial stratum Method A mean: 58.7** (Method B mean: 0.33)

**Key patterns:**
- Method A is roughly 1.7× Method B in this band (58.7 vs 33×100 = 33%). Similar to nucleus calibration ratio.
- Phonetic-Gestural model consistently predicts one correct feature + one wrong/generic one
- The "wrong" second feature often comes from articulatory sifaat (ضغط from shidda, استرسال from takrir) that don't match Jabal's semantic vocabulary

---

## ZERO MATCH STRATUM (15 entries, Jaccard = 0)

| # | Root | Model | Pred | Actual | J(B) | A Score | Notes |
|---|------|-------|------|--------|------|---------|-------|
| 1 | ضوف/ضيف | phon_gest | تجمع+طرد | تعقد+حيز | 0.0 | 20 | ضيف = guest. Both sides are about spatial configuration, but the vocabulary doesn't overlap. Weak conceptual link |
| 2 | رذذ | phon_gest | نقص+نفاذ | رقة | 0.0 | 25 | رذاذ = fine drizzle. "Fineness" (رقة) is what matters. نقص+نفاذ is in a different semantic zone |
| 3 | سفح | intersection | جفاف | قوة+كثافة | 0.0 | 10 | سفح = to spill/shed (blood). Dryness is the opposite of spilling. Wrong |
| 4 | غلو | intersection | اشتمال | طول+حدة | 0.0 | 15 | غلو = excess/extremity. Containment ≠ extension+sharpness. Wrong direction |
| 5 | خبز | intersection | تجمع | غلظ | 0.0 | 30 | خبز = bread. Gathering (kneading?) is conceptually adjacent to thickness (dough density). Weak link |
| 6 | حطب | phon_gest | ضغط+تجمع | جفاف | 0.0 | 15 | حطب = firewood. Dryness is the defining feature. Pressure+gathering miss the point |
| 7 | قضب | phon_gest | استقلال+تجمع | قطع | 0.0 | 10 | قضب = to cut/trim branches. Cutting (قطع) is the core. Independence+gathering is irrelevant |
| 8 | حلف | phon_gest | تخلخل+طرد | حدة+ظاهر | 0.0 | 10 | حلف = to swear an oath. Sharpness+manifestation (of the vow). Loosening+expulsion is wrong |
| 9 | فكر | phon_gest | تخلخل+استرسال | وصول | 0.0 | 15 | فكر = to think. Arrival/reaching (a conclusion) is Jabal's reading. Loosening+flow is wrong |
| 10 | فتن | phon_gest | استقلال+امتداد | باطن | 0.0 | 10 | فتن = trial/temptation. Inner (hidden seduction). Independence+extension is wrong |
| 11 | صغو-صغى | sequence | رخاوة | صعود | 0.0 | 5 | صغا = to incline (the ear). Rising/ascending is Jabal's reading (of attention). Softness is wrong |
| 12 | ثقق | intersection | قوة | خروج+تلاصق+غلظ+ثقل | 0.0 | 25 | ثقّ = heaviness/weight. Force is in the neighborhood but not what Jabal encoded. Missed thickness+heaviness+adhesion |
| 13 | نتت | phon_gest | انتقال+ضغط | دقة+وحدة+حدة+ظاهر | 0.0 | 10 | نتن = stench/protrusion. Fineness+sharpness+manifestation. Movement+pressure is wrong |
| 14 | دحر | phon_gest | ضغط+استرسال | قوة+إبعاد | 0.0 | 30 | دحر = to drive away. Pressure conceptually adjacent to force, and flow→movement. But Method B doesn't see it |
| 15 | قصر | phon_gest | قطع+استرسال | ضغط+انتشار+طول | 0.0 | 15 | قصر = to restrict/confine. Cutting is adjacent (limiting), but pressure+length is what Jabal has |

**Zero stratum Method A mean: 16.3** (Method B: 0.0)

**Key finding:** Most Jaccard=0 predictions are genuinely wrong, not just vocabulary mismatches. Average Method A of 16.3 confirms Method B is accurate in this band — there's no hidden semantic accuracy being missed. Only 3/15 had even weak conceptual connections (دحر, خبز, ثقق).

---

## EMPTY ACTUAL STRATUM (15 entries, no Jabal features for the root)

| # | Root | Model | Pred | Actual | Verse | Assessment |
|---|------|-------|------|--------|-------|------------|
| 1 | جزى | sequence | تميز+استقلال | — | الجزية | Plausible: recompense = distinguishing/separating what's owed |
| 2 | أفك | sequence | تخلخل | — | المؤتفكة | Plausible: overturning = loosening/disintegrating |
| 3 | زلل | phon_gest | انتقال+تعلق | — | زللتم | Partial: slipping = movement, but تعلق (attachment) seems wrong |
| 4 | كعب | phon_gest | استرسال+تجمع | — | الكعبة | Weak: الكعبة is about elevation/gathering, but استرسال doesn't fit |
| 5 | وكد | phon_gest | قوة+اشتمال | — | توكيدها | Good: confirming = force + encompassing (securing firmly) |
| 6 | شطأ | sequence | تلاصق+امتداد | — | شطأه | Good: shoot of a plant = adhesion (to trunk) + extension (growth) |
| 7 | يقت | intersection | دقة | — | الياقوت | Weak: rubies → fineness? Hardness/density would be better |
| 8 | دمى | phon_gest | استواء+اشتمال | — | الدم | Weak: blood → evenness+containment? Blood is about flow/life force |
| 9 | أمو | phon_gest | نقص+اشتمال | — | أمة | Weak: bondmaid/nation → deficiency+containment? Not convincing |
| 10 | جبت | intersection | قطع | — | الجبت | Interesting: الجبت = false deities. Cutting (as in severing from truth)? Speculative |
| 11 | تعس | phon_gest | رخاوة+امتداد | — | تعسًا | Weak: تعس = misfortune/stumbling. Softness+extension doesn't capture it |
| 12 | لحق | phon_gest | التحام+تعقد | — | يلحقوا | Partial: لحق = to catch up with = joining/fusing. التحام is close. تعقد is wrong |
| 13 | رتل | phon_gest | تلاصق+تعلق | — | رتّل | Partial: ترتيل = measured recitation = joining (words in sequence). Adjacency but not exact |
| 14 | نفل | phon_gest | نفاذ+تعلق | — | الأنفال | Weak: أنفال = war spoils. Penetration+attachment doesn't capture "extra/surplus" |
| 15 | زكر | intersection | تلاصق | — | زكريا | Cannot assess: proper noun, no semantic root meaning available |

**Empty actual stratum assessment:** 3 good (20%), 3 partial (20%), 8 weak (53%), 1 unassessable (7%).
**Estimated Method A for assessable predictions: ~35**

This stratum reveals a critical issue: 207 roots (10.7% of all 1,938) have no actual_features from Jabal. These are all scored as J=0 in Method B, dragging down the overall mean. They are feature extraction failures, not prediction failures.

---

## Overall Method A Verdict

| Stratum | Count | % of 1938 | Method B Mean | Method A Mean | Ratio A/B |
|---------|-------|-----------|---------------|---------------|-----------|
| Exact (J=1.0) | 39 | 2.0% | 1.0 | 89.1 | 0.89× |
| Partial (0<J<1) | 651 | 33.6% | ~0.33 | 58.7 | 1.78× |
| Zero (J=0) | 1,041 | 53.7% | 0.0 | 16.3 | — |
| Empty actual | 207 | 10.7% | 0.0 | ~35* | — |

**Weighted Method A estimate across all 1,938 roots:**
- (39 × 89.1 + 651 × 58.7 + 1041 × 16.3 + 207 × 35) / 1938 = **32.4**

**Excluding empty-actual (1,731 assessable roots):**
- (39 × 89.1 + 651 × 58.7 + 1041 × 16.3) / 1731 = **32.0**

This is **below the Sprint 3 target of >55% Method A**.

---

## Failure Pattern Analysis

### Pattern 1: Phonetic-Gestural Model Dominance (61.6% of all predictions)

The model routing sends 1,193/1,938 roots through phonetic_gestural. This happens whenever the binary nucleus features and third letter features have zero Jaccard overlap — which is the common case because letter features are typically from different semantic categories.

**Problem:** The phonetic_gestural model takes `first_feature_of_nucleus + first_feature_of_third_letter`, then appends articulatory sifaat (shidda→ضغط, safeer→دقة, takrir→استرسال, itbaq→كثافة, ghunna→باطن). This produces *generic* phonetic features that rarely match Jabal's *semantic* description of the root.

**Evidence:** phonetic_gestural mean Jaccard = 0.105 vs intersection's 0.185 (1.76× worse).

**Root cause:** The articulatory features (sifaat) describe how the letter is *pronounced*, not what it *means* in the root. Jabal's root meanings are semantic compositions, not phonetic descriptions.

### Pattern 2: First-Feature Truncation

Both phonetic_gestural and sequence models take only `f1[:1]` or `f1[:2]` from each component. Many nuclei have 3-4 features — the later ones are dropped, losing critical semantic dimensions.

**Example:** بر (خلوص, فراغ, ظاهر, جفاف) → only خلوص is used → all بر-family roots predict خلوص as the dominant feature, but many actual roots (برج, برح, برق) emphasize the other features.

### Pattern 3: Third-Letter Features Are Too Generic

The `atomic_features` from scholar letters often don't overlap with nucleus features, forcing the phonetic_gestural fallback. But the real composition is more nuanced — the third letter *modifies* the nucleus meaning directionally, not additively.

**Example:** بعد (بع + د). Nucleus بع = خروج (exit/emergence). Third letter د = احتباس (retention). The root بعد means "distance" — not خروج+احتباس but rather "the exit that keeps going" → بُعد. The intersection model would find no overlap and fall back to phonetic_gestural, which just concatenates first features.

### Pattern 4: Empty Actual Features (10.7% of roots)

207 roots have no extracted features from Jabal's data. These include major Quranic terms (جزى, أفك, زلل, لحق, نفل). This is a feature extraction gap, not a prediction problem.

### Pattern 5: Synonym Groups Don't Reach Deep Enough

Several J=0 predictions had *conceptually* related features that aren't in the synonym table:
- قوة (force) vs ثقل (heaviness) — related but not grouped
- ضغط (pressure) vs إمساك (holding) — both about constraint, not synonymized
- تجمع (gathering) vs كثافة (density) — partially overlapping but treated as separate groups

### Pattern 6: BAB-Level Variance

Best BABs: الهاء (0.187), الغين (0.182), الضاد (0.178), الخاء (0.174)
Worst BABs: الصاد (0.091), الحاء (0.107), الدال (0.109), النون (0.112)

The strong BABs tend to have simpler, more consistent nucleus semantics. The weak BABs (especially الحاء, الصاد) have nuclei with complex, multi-feature meanings that the single-feature truncation can't capture.

---

## Concrete Recommendations

### R1: Fix the Phonetic-Gestural Model (HIGH IMPACT)
**Current:** Takes 1 feature from each component + articulatory sifaat.
**Recommended:** Take *all* features from both components (not just first), but weight nucleus features higher (0.7 nucleus, 0.3 third letter). Drop sifaat entirely from prediction — they describe articulation, not semantics.

### R2: Expand Synonym Groups (MEDIUM IMPACT)
Add these missing groups:
- `frozenset({"قوة", "ثقل"})` — force/heaviness
- `frozenset({"ضغط", "إمساك"})` — pressure/holding (both about constraint)
- `frozenset({"خلوص", "فراغ"})` — already partially covered but needs explicit grouping
- `frozenset({"استقلال", "قطع"})` — independence as severing
- `frozenset({"ظاهر", "ظهور"})` — manifest (adjective) vs appearance (action)

### R3: Use All Nucleus Features, Not Just First (HIGH IMPACT)
The `model_phonetic_gestural` function at line 71 does `_as_features(letter1)[:1]`. Change to use all features. Many nuclei have 2-4 features, and the first one is often not the most distinctive.

### R4: Fix Empty-Actual Extraction (MEDIUM IMPACT)
207 roots with Quranic verses but no extracted features. Run a second pass on these roots using the full FEATURE_ALIASES + FEATURE_VOCAB against Jabal's raw BAB text.

### R5: Category-Level Fallback Scoring (LOW-MEDIUM IMPACT)
When Jaccard is 0 but predicted and actual features share a *category* (e.g., both in "pressure_force"), count that as a partial match (e.g., 0.3 instead of 0). This would lift many J=0 roots that are conceptually close but vocabularily different.

### R6: Improve Model Routing Logic (MEDIUM IMPACT)
**Current:** If intersection Jaccard between inputs > 0 → intersection model, else → phonetic_gestural.
**Recommended:** Use category-level overlap instead of exact feature overlap to decide routing. If nucleus and third-letter features share a *category*, use intersection at category level. This would route more predictions through the better-performing intersection model.

---

## Sprint 3 Verdict

**First root prediction pass: Method A ~32%, Method B ~13.5%.** Below target (>55% A, >30% B).

The predictor *works* for simple, clear-semantic roots (2% exact, 33.6% partial) but fails systematically on the 54% where phonetic-gestural fallback produces generic/wrong features.

**The bottleneck is not the scoring or the data — it's the composition model.**

Specifically:
1. Phonetic-gestural drops too much information (single feature per component)
2. Articulatory sifaat contaminate predictions with phonetic noise
3. Model routing sends too many roots to the weakest model

**Recommendations R1 + R3 together could lift phonetic_gestural from 0.105 to the neighborhood of intersection's 0.185**, which would raise the overall mean Jaccard from 0.135 to approximately 0.19–0.22, and Method A from ~32% to ~45–50%.

A second pass with R1+R2+R3 implemented, followed by R4 to recover the empty-actual roots, is the recommended next step before Sprint 4.
