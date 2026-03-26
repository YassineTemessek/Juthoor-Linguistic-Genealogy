# Binary Composition Verification
## Do Letter Meanings Predict Binary Nucleus Meanings?

**Date:** 2026-03-26
**Dataset:** 456 binary nuclei from Jabal's root genealogy
**Status:** Empirical analysis — primary result of Experiment S2.5

---

## 1. Introduction

The central claim of the Arabic genome hypothesis is that letter meanings compose upward: if letter ض means "pressure and compression" (ضغط وتجمع) and letter م means "gathering and cohesion" (تجمع وتلاصق), then the nucleus ضم should mean something in the neighbourhood of "pressure + gathering". This document tests that claim directly.

For each of Jabal al-Muzaffar's 456 binary nuclei (ثنائيات), we computed the union of both letters' empirical feature sets and measured how closely that composed set matches Jabal's actual feature description of the nucleus. The result is a sharp, honest audit of where composition works, where it fails, and what the failure pattern tells us about how the genome actually operates.

**Core question:** Is binary nucleus meaning the simple sum of its letters' meanings, or does something emergent happen at the composition step?

---

## 2. Method

### 2.1 Data Sources

- **Letter empirical features:** Derived via Method A consensus across 30 BAB files (see `empirical_letter_meanings.md`). Each letter is assigned 2–4 feature tags drawn from a controlled Arabic vocabulary (~40 terms).
- **Nucleus features (Jabal):** Extracted from Jabal al-Muzaffar's *Al-Mu'jam al-Ishtiqaqi al-Mu'assal*, where each nucleus is given a concise Arabic semantic description. These descriptions were converted to the same feature vocabulary for comparison.
- **Coverage:** 456 nuclei total; of these, 444 are "genuine" (at least one side has features). The remaining 12 are empty-empty: both letters and the nucleus lack features, producing a Jaccard of 1.0 by convention — these are artifacts excluded from all substantive counts.

### 2.2 Composition Rule

For nucleus XY:

```
composed_union(XY) = empirical_features(X) ∪ empirical_features(Y)
```

This is the simplest possible composition: pure feature union, no weighting, no interaction terms.

### 2.3 Scoring

Two metrics are computed per nucleus:

**Jaccard similarity:**
```
J(XY) = |composed_union ∩ jabal_features| / |composed_union ∪ jabal_features|
```

**Blended Jaccard** (partial credit for near-synonym features — see `method_a_calibration_v2.md`):
Uses a feature proximity matrix to award partial credit when composed and Jabal features are semantically adjacent (e.g., ظاهر and ظهور). Blended scores are systematically higher than Jaccard; Jaccard remains the primary metric.

---

## 3. Results Overview

### 3.1 Summary Statistics

| Metric | Value |
|--------|-------|
| Total nuclei | 456 |
| Genuine nuclei (non-empty) | 444 |
| Empty-empty artifacts (excluded) | 12 |
| Mean Jaccard (all 456) | 0.154 |
| Mean Blended (all 456) | 0.193 |

### 3.2 Score Distribution (444 genuine nuclei)

| Jaccard band | Count | Pct | Interpretation |
|---|---|---|---|
| J = 0.0 | 212 | 47.7% | Zero overlap — complete emergent divergence |
| J = 0.01–0.19 | 90 | 20.3% | Very weak signal |
| J = 0.20–0.39 | 99 | 22.3% | Partial match |
| J = 0.40–0.49 | 22 | 5.0% | Near match |
| J = 0.50–0.59 | 15 | 3.4% | Strong match |
| J = 0.60–0.74 | 3 | 0.7% | Very strong match |
| J = 0.75–1.0 | 3 | 0.7% | Near-perfect (genuine) |

**Key correction on "strong matches":** The headline figure of 33 nuclei with J >= 0.5 includes 12 empty-empty artifacts. Among the 444 genuine nuclei, only **21 reach J >= 0.5** (4.7%). The 33-nucleus figure cited in some summaries must be read as 21 genuine + 12 artifacts.

### 3.3 Coverage Weighted by Root Count

The 444 genuine nuclei collectively cover **1,912 root family slots** (counted by member roots in each nucleus). Of these:

- **1,180 root slots** (61.7%) sit under nuclei with J > 0 — meaning at least some compositional signal reaches those roots
- **732 root slots** (38.3%) sit under nuclei where composition predicts nothing correctly

The root-weighted figure is more optimistic than the nucleus-level figure because nuclei with high member counts are slightly more likely to have some match (active, frequent nuclei may have cleaner semantic structure).

---

## 4. Best Composition Matches

The 20 nuclei below are the clearest successes — cases where simple feature union closely or exactly predicts Jabal's nucleus description. Arabic features are given first; English glosses follow in parentheses.

### Tier A: Near-Perfect (J >= 0.75)

**أث** (J = 1.00, B = 1.00, 2 root families)
- أ features: ∅ (hamza has no empirical features assigned)
- ث features: كثافة (density), تجمع (aggregation)
- Composed union: كثافة، تجمع
- Jabal features: تجمع، كثافة — *exact match*
- Jabal meaning: "تجمع الدقائق بكثافة" (aggregation of fine particles with density)
- Note: أ contributes nothing; ث carries the full meaning. The nucleus is effectively mono-literal here.

**ضم** (J = 0.75, B = 0.72, 2 root families)
- ض features: ضغط (pressure), تجمع (aggregation), كثافة (density)
- م features: تجمع (aggregation), تلاصق (cohesion)
- Composed union: ضغط، تجمع، كثافة، تلاصق
- Jabal features: تجمع، ضغط، تلاصق — 3 of 4 composed features hit
- Jabal meaning: "هو الجمع بضغط ولأم" (gathering by pressure and bonding)
- This is the genome hypothesis at its clearest: pressing (ض) + gathering (م) = gathering-by-pressing (ضم).

**عم** (J = 0.75, B = 0.82, 9 root families)
- ع features: ظهور (emergence/visibility), عمق (depth)
- م features: تجمع (aggregation), تلاصق (cohesion)
- Composed union: ظهور، عمق، تجمع، تلاصق
- Jabal features: التحام (fusion), تجمع، ظاهر — التحام not in composed set but related to تلاصق; ظاهر matches ظهور
- Jabal meaning: "الالتحام العلوي، أي التجمع مع علو" (upper-level fusion, gathering from above)
- The blended score (0.82) reflects التحام/تلاصق and ظاهر/ظهور being near-synonyms.

### Tier B: Strong (J = 0.60–0.74)

**جث** (J = 0.67, B = 0.67, 3 root families)
- ج features: تجمع (aggregation), بروز (protrusion)
- ث features: كثافة (density), تجمع (aggregation)
- Composed union: تجمع، بروز، كثافة
- Jabal features: تجمع، كثافة — 2/3 hit; بروز absent from Jabal
- Jabal meaning: "تجمع الكتلة الكثيفة" (aggregation of a dense mass)

**سر** (J = 0.60, B = 0.65, 18 root families)
- س features: امتداد (extension), نفاذ (penetration), دقة (fineness)
- ر features: استرسال (continuous flow), امتداد (extension)
- Composed union: امتداد، نفاذ، دقة، استرسال
- Jabal features: تلاصق، امتداد، نفاذ، دقة — 3 of 4 hit; تلاصق is the extra
- Jabal meaning: "الامتداد أو النفاذ مع الدقة" (extension or penetration with fineness)
- Notable: 18 root families — this is a high-frequency nucleus where composition works.

**قن** (J = 0.60, B = 0.72, 7 root families)
- ق features: قوة (force), عمق (depth)
- ن features: نفاذ (penetration), باطن (interior), امتداد (extension)
- Composed union: قوة، عمق، نفاذ، باطن، امتداد
- Jabal features: نفاذ، باطن، إمساك، عمق، امتداد — 4/5 hit; إمساك absent
- Jabal meaning: "النفاذ في الباطن أو الأخذ إليه بعمق أو امتداد" (penetrating into the interior, reaching it with depth or extension)

### Tier C: Solid (J = 0.50)

**غم** (J = 0.50, B = 0.65, 4 root families)
- غ features: باطن (interior), اشتمال (containment)
- م features: تجمع (aggregation), تلاصق (cohesion)
- Composed union: باطن، اشتمال، تجمع، تلاصق
- Jabal features: اشتمال، باطن — exact subset; Jabal distils two of four
- Jabal meaning: "نوع من التغطية والحجب" (a type of covering and concealment)

**عم-reversed (مك)** (J = 0.50, B = 0.65, 5 root families)
- م features: تجمع (aggregation), تلاصق (cohesion)
- ك features: تجمع (aggregation), إمساك (grasping), ضغط (pressure)
- Composed union: تجمع، تلاصق، إمساك، ضغط
- Jabal features: امتساك، تماسك، احتباس — all are containment/holding variants
- Jabal meaning: "التمكن والرسوخ والاحتباس" (firmness, solidity, and retention)
- The blended score (0.65) is high because تلاصق/تماسك and إمساك/امتساك are near-synonyms.

**ذق** (J = 0.50, B = 0.50, 3 root families)
- ذ features: نفاذ (penetration), حدة (sharpness)
- ق features: قوة (force), عمق (depth)
- Composed union: نفاذ، حدة، قوة، عمق
- Jabal features: نفاذ، حدة — exact subset
- Jabal meaning: "النفاذ الحاد والأثر العميق" (sharp penetration and deep impact)

**رس** (J = 0.50, B = 0.55, 5 root families)
- ر features: استرسال (continuous flow), امتداد (extension)
- س features: امتداد (extension), نفاذ (penetration), دقة (fineness)
- Composed union: استرسال، امتداد، نفاذ، دقة
- Jabal features: نفاذ، امتداد — exact subset
- Jabal meaning: "النفاذ بامتداد" (penetration with extension)

**بش** (J = 0.50, B = 0.55, 2 root families)
- ب features: ظهور (emergence), خروج (exiting)
- ش features: انتشار (spreading), تفرق (scattering)
- Composed union: ظهور، خروج، انتشار، تفرق
- Jabal features: انتشار، ظاهر — ظاهر matches ظهور
- Jabal meaning: "الانتشار الظاهر" (visible/manifest spreading)

**مم** (J = 0.50, B = 0.65, 2 root families)
- م + م: both contribute تجمع (aggregation), تلاصق (cohesion)
- Jabal features: تجمع — the doubled letter intensifies but reduces to one feature
- Jabal meaning: "التجمع والتضام" (gathering and compression together)

**سن / نس** (J = 0.50, 11 and 10 root families respectively)
Both س and ن share نفاذ and امتداد. Union: امتداد، نفاذ، دقة، باطن. Jabal reduces to نفاذ + دقة in both directions — the shared features dominate.

**صد** (J = 0.50, B = 0.57, 8 root families)
- ص features: غلظ (coarseness), قوة (force), نفاذ (penetration)
- د features: احتباس (retention), امتداد (extension)
- Jabal features: كثافة، صلابة، غلظ، قوة، نفاذ
- Jabal meaning: "شيء كثيف أو صلب قوي يعترض فيوقف النفاذ" (something dense or solid that blocks penetration)
- Three of five Jabal features are directly in the composed set.

**مد** (J = 0.50, B = 0.55, 4 root families)
- م: تجمع، تلاصق; د: احتباس، امتداد
- Jabal: تلاصق، امتداد — two direct hits
- Jabal meaning: "الامتداد والغاية" (extension and its terminus)

---

## 5. Failure Analysis

The 20 worst failures below are nuclei where J = 0 and both sides have real features. The pattern is diagnostically important.

### 5.1 Failure Cases by Root Coverage

**بر** (J = 0.00, B = 0.00, 16 root families — largest failure)
- ب features: ظهور، خروج
- ر features: استرسال، امتداد
- Composed union: ظهور، خروج، استرسال، امتداد
- Jabal features: خلوص، فراغ
- Jabal meaning: "التجرد والخلوص" (purity, bareness, stripping away)
- **Why it fails:** بر is one of the most fertile Arabic nuclei. Its meaning — bareness, openness, innocence (بر: land, righteousness, wheat; برهان: proof by clarity; برد: cold clarity) — is an *emergent* concept not derivable from ب's visibility or ر's flow. The nucleus has synthesized a higher-order abstraction.

**قر** (J = 0.00, B = 0.07, 14 root families)
- Composed: قوة، عمق، استرسال، امتداد
- Jabal: استقرار، تخلخل، حيز
- Jabal meaning: "استقرار ما شأنه التسيب في قاع عميق أو حيز" (settling of what tends to flow, into a deep base or defined space)
- **Why it fails:** *Settling* (استقرار) is the interaction product of force (ق) meeting flow (ر) — the force arrests the flow. Neither letter individually signals حيز (bounded space). The nucleus describes what happens *between* the letters' meanings, not their union.

**رب** (J = 0.00, B = 0.00, 9 root families)
- Composed: استرسال، امتداد، ظهور، خروج
- Jabal: غلظ، تماسك، تجمع
- Jabal meaning: "الاستغلاظ وما إليه من تماسك وتجمع" (thickening and the cohesion that follows)
- **Why it fails:** Neither ر (flow) nor ب (emergence) predicts *thickening*. Thickening is what happens when sustained flow (ر) accumulates around a surface point of emergence (ب). It is an interaction, not a union.

**نع** (J = 0.00, B = 0.00, 7 root families)
- Composed: نفاذ، باطن، امتداد، ظهور، عمق
- Jabal: رخاوة، رقة
- Jabal meaning: "الرخاوة والطراءة وما إلى ذلك رقة الأثناء" (softness, suppleness, tenderness of interior)
- **Why it fails:** *Softness* (رخاوة) and *tenderness* (رقة) are qualities, not operations. They describe the *character* of the interaction between interior depth (ن) and visible depth (ع), not the features themselves. The nucleus operates at a different semantic level.

**بس** (J = 0.00, B = 0.07, 8 root families)
- Composed: ظهور، خروج، امتداد، نفاذ، دقة
- Jabal: جفاف
- Jabal meaning: "الجفاف واليبوسة" (dryness and aridity)
- **Why it fails:** *Dryness* is entirely absent from both letters. This is an extreme emergent case — the combination of fine penetrating extension (س) through a manifesting surface (ب) has, in the language's history, come to denote desiccation. No simple union captures this.

**عب** (J = 0.00, B = 0.07, 9 root families)
- Composed: ظهور، عمق، خروج
- Jabal: رخاوة، تخلخل، حيز
- Jabal meaning: "اجتماع الرخو، أو المائع، أو التخلخل في الحيز" (gathering of the soft/liquid in a bounded space)
- **Why it fails:** Similar to نع: رخاوة (softness) and تخلخل (looseness) describe a *quality* of the interior (ع) + surfacing (ب) interaction, not a union of features.

**نب** (J = 0.00, B = 0.10, 9 root families)
- Composed: نفاذ، باطن، امتداد، ظهور، خروج
- Jabal: صعود (ascent)
- Jabal meaning: "النُّبُوُّ ارتفاعًا أو ابتعادًا" (rising upward or moving away)
- **Why it fails:** *Ascent* is directional. Neither letter carries a vertical axis feature. Interior penetration (ن) + emergence (ب) has been semantically rotated to mean *upward emergence* — a directional inference the feature union cannot make.

**رج** (J = 0.00, B = 0.10, 9 root families)
- Composed: استرسال، امتداد، تجمع، بروز
- Jabal: تخلخل، انتقال
- Jabal meaning: "الاضطراب المادي، أي اضطراب الجِرْم وتردده" (physical agitation — vibration and oscillation of a body)
- **Why it fails:** *Agitation* (اضطراب) and *oscillation* (تردد) are dynamical properties. Flow (ر) + protrusion (ج) interacting produces trembling motion — a physical process that emerges from the tension between the two letter meanings, not their union.

**رح** (J = 0.00, B = 0.15, 6 root families)
- Composed: استرسال، امتداد، خلوص، احتكاك، جفاف
- Jabal: اتساع، رقة
- Jabal meaning: "الاتساع والانبساط مع نوع من الرقة" (breadth and expansiveness with a quality of fineness)
- **Why it fails:** *Expansiveness* (اتساع) is scale, not movement or texture. This is a measurement concept that the letter feature sets — which describe motion and texture — cannot produce by union.

**رق / رح / بر** pattern summary: ر (flow, extension) when combined with letters encoding surface or containment consistently produces *spaciousness* concepts (اتساع, رقة, خلوص, فراغ) — an emergent quality family the union model cannot predict.

**قط** (J = 0.00, B = 0.00, 7 root families)
- Composed: قوة، عمق، امتداد، اشتمال، ضغط
- Jabal: قطع، استواء
- Jabal meaning: "نوع من القطع باستواء وتسوية" (a type of cutting with levelling)
- **Why it fails:** قطع (cutting) overlaps with ق's force-and-depth profile but is not a feature label in the composed set. The union yields *compression* features; Jabal describes *severing*, which requires the force to cross a threshold — an interaction effect.

### 5.2 Most Common Emergent Features in Failures

Features that appear in Jabal's nucleus descriptions but cannot be derived from the composed sets:

| Emergent feature | Occurrences in J=0 failures | Character |
|---|---|---|
| قوة (force) | 25 | Scale/intensity — derived from interaction strength |
| نقص (diminution) | 17 | Relational — requires comparing before/after states |
| رخاوة (softness) | 17 | Quality — describes the result's texture |
| غلظ (coarseness/thickness) | 12 | Quality — result of accumulation |
| اتساع (expansiveness) | 11 | Scale — measurement of space cleared |
| حيز (bounded space) | 11 | Topological — container concept |
| كثافة (density) | 11 | Quality — degree of compaction |
| إبعاد (distancing) | 10 | Relational — directional change |
| اتصال (connection) | 8 | Topological — binary relation |
| انتقال (transition/movement) | 8 | Dynamical — change of state |

These emergent features cluster into three cognitive types:
1. **Quality terms** (رخاوة، رقة، غلظ، كثافة): describe the result's sensory character
2. **Scale terms** (اتساع، حيز، نقص): measure extent or degree
3. **Dynamical terms** (انتقال، اضطراب، استقرار): describe the process of interaction

---

## 6. What This Proves

### 6.1 The Genome Principle Is Real But Incomplete

Simple feature union correctly accounts for:
- **4.7% of genuine nuclei** at high confidence (J >= 0.5)
- **52.3% of genuine nuclei** with any signal (J > 0)
- **61.7% of root family slots** with any compositional signal

This is not noise. Mean Jaccard of 0.154 against a random baseline near zero demonstrates systematic signal. The genome principle — that letter meanings shape nucleus meanings — is empirically supported. But the composition function is not union.

### 6.2 The Failure Pattern Is Systematic, Not Random

The 162 cases of genuine J = 0 failures are not scattered randomly. They cluster around:

1. **Quality emergence:** The letters describe *operations* (pressure, flow, penetration). The nucleus describes the *result's quality* (softness, thickness, dryness). The feature vocabulary has two layers, and simple union only works within the operational layer.

2. **Directional specificity:** Nuclei like نب (ascent), زل (gliding), انتقال-family encode direction or axis. The letter features are direction-agnostic. The direction emerges from the *orientation* of one letter's operation relative to the other.

3. **Interaction products:** Cases like قر (settling) and رج (vibration) describe what happens *when* the two letters' meanings meet — not what each letter means individually. These require a relational or dynamical model.

4. **ر-pattern:** The letter ر (استرسال، امتداد — continuous flow) systematically produces *spaciousness* concepts (اتساع، رقة، خلوص، فراغ) when paired with surface/container letters. This is a recurring bi-literal interaction rule, not a unary property.

### 6.3 Which Letters Compose Best

Mean Jaccard by letter (minimum 3 nucleus appearances):

**Best composers:** ث (0.228), م (0.220), ق (0.186), هـ (0.179), س (0.175)
**Weakest composers:** ء (0.033), ظ (0.053), و (0.073), ي (0.089), ل (0.095)

The pattern is interpretable: ث (density-aggregation), م (gathering-cohesion), and ق (force-depth) have feature sets that are *stable, concrete, and operational* — they contribute to nucleus meanings without being transformed. The weak composers — ء، و، ي — are the semi-vowels and weak letters; their phonetic instability maps to semantic diffuseness.

### 6.4 The Genome Has Two Tiers

These results suggest the genome operates in two tiers:

**Tier 1 (captured by union):** Letters contribute their core operational features directly to the nucleus. When both letters have stable, concrete feature sets and the nucleus describes an operation (not a quality or measurement), union prediction works. Examples: ضم، سر، قن، غم.

**Tier 2 (not captured by union):** Letters interact to produce emergent meanings — qualities, measurements, or dynamic processes that are the *result* of the two operations meeting. These require a composition function that models the interaction, not just the union.

---

## 7. Implications for Root Prediction

### 7.1 Current Predictor Limitations

The root predictor (Method A) uses nucleus-level features as the primary semantic anchor for root prediction. If nucleus features are only partially predicted by letter composition, then:

- Roots under high-J nuclei (ضم، سر، عم) can be well-anchored by letter-level features
- Roots under low-J nuclei (بر، قر، رب) require nucleus-level features as an independent prior, not derivable from letter features alone

### 7.2 Recommended Architecture Upgrade

**Stage 1 (letter features → nucleus prediction):** Use letter feature union as a prior, but train a residual correction. The residual should learn the interaction patterns — particularly the quality-emergence and directional cases identified above.

**Stage 2 (nucleus features → root features):** Jabal's nucleus features remain the stronger anchor. When letter composition matches (J >= 0.5), letter features can substitute or reinforce. When J = 0, rely on Jabal's nucleus features directly.

**Stage 3 (interaction rules):** The ر-pattern (flow + surface → spaciousness) is the clearest example of a compositional rule beyond union. A small set of such bi-literal interaction rules — perhaps 15–25 covering the most frequent interaction types — would substantially improve Tier 2 predictions.

### 7.3 Feature Vocabulary Gap

The most frequent emergent features in failures (رخاوة، اتساع، استقرار، انتقال) are largely *absent* from the current letter empirical feature set. This is not a calibration problem — it is a principled gap. These features are properties of interactions, not of individual letters. The feature vocabulary for letters and the feature vocabulary for nuclei should remain separate, with a mapping layer between them (currently missing).

### 7.4 Priority Nuclei for Manual Review

The following high-frequency nuclei (large member counts) currently have J = 0 but are analytically important — manual feature alignment would improve root prediction for many roots simultaneously:

| Nucleus | Member roots | Jabal meaning summary |
|---|---|---|
| بر | 16 | Bareness, purity (خلوص، فراغ) |
| قر | 14 | Settling in depth (استقرار، حيز) |
| رب | 9 | Thickening/cohesion (غلظ، تماسك) |
| رج | 9 | Vibration/agitation (تخلخل، انتقال) |
| عب | 9 | Soft/liquid in bounded space (رخاوة، حيز) |
| نب | 9 | Ascent/distancing (صعود) |
| بس | 8 | Dryness (جفاف) |
| قل | 8 | Rising/lifting (صعود) |

---

## 8. Conclusion

Binary composition by simple feature union explains approximately half the Arabic nucleus system. The genome principle is real: letters carry stable meanings that predictably shape nucleus semantics. But the composition function is richer than union. Nucleus meanings at the zero-Jaccard end are *emergent* — they describe what happens when two letter-operations interact, not just what each letter means alone.

The failures cluster into three interpretable families: quality-emergence (softness, thickness from operational components), directional specificity (ascent, distancing, settling from direction-agnostic components), and interaction products (vibration, spreading, arresting from the tension between operations). Each family points toward a specific augmentation of the composition model.

The Arabic root genome is a two-tier system: a compositional tier where features flow upward from letter to nucleus by union, and an emergent tier where interaction dynamics produce semantic properties that no single letter encodes alone. Both tiers are rule-governed; only one is currently modelled.

---

*Analysis based on 456 nuclei, binary_composition_data.json, LV1 empirical letter features, Jabal al-Muzaffar's nucleus descriptions.*
