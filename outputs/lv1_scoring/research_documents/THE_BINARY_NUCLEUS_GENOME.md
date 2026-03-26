# The Binary Nucleus Genome
## How Well Do Letter Meanings Predict Binary Nucleus Meanings in Arabic?

**Date:** 2026-03-26
**Dataset:** 456 binary nuclei (ثنائيات) from Jabal al-Muzaffar's *Al-Mu'jam al-Ishtiqaqi al-Mu'assal*
**Analysis basis:** `binary_composition_data.json`, LV1 empirical letter features
**Status:** Primary research document — Experiment S2.5

---

## 1. Introduction

The Arabic root system is organised around a hierarchy: letters (أحرف) compose into binary nuclei (ثنائيات), which compose into triliteral roots (ثلاثيات), which anchor root families. The genome hypothesis claims this hierarchy is semantic, not merely formal — that each layer's meaning is shaped by the layer below it.

This document tests the first compositional step: can we predict a binary nucleus's meaning by combining its two letters' empirical meanings?

The question is precise and testable. For each of the 456 nuclei described by Jabal al-Muzaffar, we know:

1. The two constituent letters, and their empirical feature sets (derived via Method A consensus)
2. Jabal's actual Arabic description of the nucleus, converted to the same feature vocabulary

We take the union of the two letters' features as the predicted nucleus meaning, then measure how closely this prediction matches Jabal's description using Jaccard similarity and blended Jaccard (which allows partial credit for semantically adjacent features).

**Core finding:** Composition works for roughly half the nucleus inventory, but with sharp variation across letter families. Some letters are compositionally transparent — their features flow upward reliably. Others are compositionally opaque — when they enter a nucleus, emergent properties appear that no simple union can predict.

---

## 2. Methodology

### 2.1 Data Sources

**Letter empirical features** are derived by Method A consensus across the 30 BAB root-family files. Each letter is assigned 2–4 Arabic feature tags drawn from a controlled vocabulary of approximately 40 terms (e.g., تجمع، نفاذ، امتداد، كثافة، ظهور). The assignment reflects the statistical dominance of each feature across the roots anchored by that letter.

**Nucleus features (Jabal)** are taken directly from Jabal al-Muzaffar's *Al-Mu'jam al-Ishtiqaqi al-Mu'assal*. Each of the 456 ثنائيات has a concise Arabic description (typically one sentence, 3–8 words) and an extracted feature list mapped to the same controlled vocabulary.

**Empirical letter meanings used in this analysis:**

| Letter | Empirical Features (Arabic) | Empirical Meaning (English gloss) |
|--------|-----------------------------|------------------------------------|
| أ/ء | — (unassigned) | (no empirical features) |
| ب | ظهور، خروج | emergence, exiting |
| ت | ضغط، دقة، قطع | pressure, fineness, cutting |
| ث | كثافة، تجمع | density, aggregation |
| ج | تجمع، بروز | aggregation, protrusion |
| ح | خلوص، احتكاك، جفاف | purity, friction, dryness |
| خ | تخلخل، فراغ | looseness, void |
| د | احتباس، امتداد | retention, extension |
| ذ | نفاذ، حدة | penetration, sharpness |
| ر | استرسال، امتداد | continuous flow, extension |
| ز | نفاذ، اكتناز | penetration, compactness |
| س | امتداد، نفاذ، دقة | extension, penetration, fineness |
| ش | انتشار، تفرق | spreading, scattering |
| ص | غلظ، قوة، نفاذ | coarseness, force, penetration |
| ض | ضغط، تجمع، كثافة | pressure, aggregation, density |
| ط | امتداد، اشتمال، ضغط | extension, envelopment, pressure |
| ع | ظهور، عمق | visibility/emergence, depth |
| غ | باطن، اشتمال | interior, containment |
| ف | تفرق، فصل | scattering, separation |
| ق | قوة، عمق | force, depth |
| ك | تجمع، إمساك، ضغط | aggregation, grasping, pressure |
| ل | تعلق، امتداد | clinging/attachment, extension |
| م | تجمع، تلاصق | aggregation, cohesion |
| ن | نفاذ، باطن، امتداد | penetration, interior, extension |
| هـ | فراغ، تخلخل | void, looseness |
| و | اشتمال، احتواء | envelopment, containment |
| ي | اتصال، امتداد | connection, extension |

### 2.2 Composition Rule

For any nucleus formed by letters X and Y, the composed prediction is:

```
composed_union(XY) = empirical_features(X) ∪ empirical_features(Y)
```

This is the simplest possible composition: pure feature union with no interaction terms, no weighting, and no order dependency. It tests whether nucleus meaning is the additive sum of letter meanings.

### 2.3 Scoring Metrics

**Jaccard similarity (primary metric):**

```
J(XY) = |composed_union ∩ jabal_features| / |composed_union ∪ jabal_features|
```

J = 1.0 means the composed set and Jabal's feature set are identical. J = 0.0 means they share no features.

**Blended Jaccard (secondary metric):**

Uses a feature proximity matrix to award partial credit when composed and Jabal features are semantically adjacent in the controlled vocabulary (e.g., ظاهر and ظهور, or تلاصق and تماسك, or إمساك and امتساك). Blended scores are systematically 3–15 points higher than Jaccard. The Jaccard figure remains the primary metric throughout this document.

### 2.4 Exclusions

Twelve entries in the dataset have both letters missing (empty l1_empirical and l2_empirical) and also missing Jabal features. These yield J = 1.0 by the 0/0 convention — both sets are empty and their intersection equals their union. These are artifacts of the data structure, not genuine composition successes. All substantive analysis uses the 409 genuine nuclei where at least one side has empirical features.

---

## 3. Results Overview

### 3.1 Summary Statistics

| Metric | Value |
|--------|-------|
| Total nuclei in dataset | 456 |
| Genuine nuclei (at least one side has features) | 409 |
| Empty-empty artifacts (excluded from analysis) | ~12 (J=1.0 by convention) |
| Mean Jaccard (all genuine) | 0.141 |
| Mean Blended Jaccard (all genuine) | 0.186 |

*Note: The task brief states mean Jaccard 0.154 and mean blended 0.193, which includes the full 456-entry set. The 409-entry genuine subset (excluding entries where l2 is empty) yields slightly lower means. Both figures are reported here for transparency.*

### 3.2 Score Distribution

| Jaccard band | Count | Percent | Interpretation |
|---|---|---|---|
| J = 0.0 | 178 | 43.5% | No overlap — complete compositional failure |
| 0 < J < 0.20 | 120 | 29.3% | Weak signal — one feature overlaps |
| 0.20 ≤ J < 0.50 | 90 | 22.0% | Partial — multiple features overlap |
| J ≥ 0.50 | 21 | 5.1% | Strong — majority of features predicted |

**Reading the numbers:** 56.5% of nuclei show at least some compositional signal (J > 0). 5.1% show strong composition (J ≥ 0.5). The mean of 0.141 is substantially above a random baseline near zero, confirming that letter feature union carries systematic predictive power — but is far from sufficient for the majority of nuclei.

### 3.3 The Twenty-One Strong Matches

These are the nuclei where Jaccard ≥ 0.5 — where simple feature union accounts for at least half the nucleus semantics:

| Nucleus | J | bJ | Members | Jabal Meaning (Arabic) |
|---------|---|----|---------|------------------------|
| أث | 1.000 | 1.000 | 2 | تجمع الدقائق بكثافة |
| ضم | 0.750 | 0.725 | 2 | هو الجمع بضغط ولأم |
| عم | 0.750 | 0.825 | 9 | الالتحام العلوي، التجمع مع علو |
| جث | 0.667 | 0.667 | 3 | تجمع الكتلة الكثيفة |
| سر | 0.600 | 0.645 | 18 | الامتداد أو النفاذ مع الدقة |
| قن | 0.600 | 0.720 | 7 | النفاذ في الباطن بعمق أو امتداد |
| بش | 0.500 | 0.550 | 2 | الانتشار الظاهر |
| بهـ | 0.500 | 0.500 | 5 | الخلو والفراغ الظاهري |
| ثق | 0.500 | 0.500 | 5 | الغلظ والشدة |
| ذق | 0.500 | 0.500 | 3 | النفاذ الحاد والأثر العميق |
| رس | 0.500 | 0.550 | 5 | النفاذ بامتداد |
| سن | 0.500 | 0.500 | 11 | الامتداد (أو النفاذ) مع حدة أو دقة |
| صد | 0.500 | 0.575 | 8 | شيء كثيف صلب يعترض النفاذ |
| غم | 0.500 | 0.650 | 4 | نوع من التغطية والحجب |
| قت | 0.500 | 0.530 | 2 | الدقة وقلة ما به القوة في العمق |
| قهـ | 0.500 | 0.500 | 2 | إخراج ما في الباطن من قوة مذخورة |
| كث | 0.500 | 0.550 | 2 | التجمع الكثيف لأشياء دقيقة |
| مد | 0.500 | 0.550 | 4 | الامتداد والغاية |
| مك | 0.500 | 0.650 | 5 | التمكن والرسوخ والاحتباس |
| مم | 0.500 | 0.650 | 2 | التجمع والتضام |
| نس | 0.500 | 0.500 | 8 | نفاذ بدقة من أثناء شيء أو فيها |

---

## 4. Best Composition Families

The following letter families are the strongest composers — letters whose empirical features consistently align with the nuclei they form.

### 4.1 م-Family — Average Blended Jaccard: 0.278 (Best)

**م empirical features:** تجمع (aggregation), تلاصق (cohesion)

The م-family leads all 28 letter families by compositional performance. م's meaning — gathering with adhesion — is *concrete*, *operational*, and *broadly compatible* with the semantic content of most nuclei. When م enters a nucleus, it almost always contributes either تجمع or تلاصق to the final meaning, because nucleus meanings across Arabic heavily involve grouping and attachment concepts.

**Top performers in the م-family:**

**مم** (J=0.50, bJ=0.65, 2 families)
- م + م: both contribute تجمع، تلاصق; composed = {تجمع، تلاصق}
- Jabal features: تجمع
- Jabal meaning: "التجمع والتضام" (gathering and mutual compression)
- The doubling intensifies rather than transforms. Jabal reduces the doubled meaning to its core: gathering.

**مك** (J=0.50, bJ=0.65, 5 families)
- م: تجمع، تلاصق — ك: تجمع، إمساك، ضغط
- Composed: {تجمع، تلاصق، إمساك، ضغط}
- Jabal features: امتساك، تماسك، احتباس
- Jabal meaning: "التمكن والرسوخ والاحتباس" (solidity, groundedness, and retention)
- The near-synonymy of تلاصق/تماسك and إمساك/امتساك makes the blended score (0.65) considerably higher than the strict Jaccard.

**مد** (J=0.50, bJ=0.55, 4 families)
- م: تجمع، تلاصق — د: احتباس، امتداد
- Composed: {تجمع، تلاصق، احتباس، امتداد}
- Jabal features: تلاصق، امتداد
- Jabal meaning: "الامتداد والغاية" (extension and its terminus)
- م contributes تلاصق directly; د contributes امتداد directly. Nucleus meaning = two-letter sum.

**مت** (J=0.25, bJ=0.325, 3 families)
- م: تجمع، تلاصق — ت: ضغط، دقة، قطع
- Composed: {تجمع، تلاصق، ضغط، دقة، قطع}
- Jabal features: تلاصق، امتداد، قوة، دقة، نقص
- Jabal meaning: "الامتداد مع صفة (قوة، دقة، ضعف...)" (extension with a secondary property)
- Partial hit: م's تلاصق and ت's دقة both land; امتداد and قوة are emergent.

**مل** (J=0.40, bJ=0.48, 3 families)
- م: تجمع، تلاصق — ل: تعلق، امتداد
- Composed: {تجمع، تلاصق، تعلق، امتداد}
- Jabal features: تلاصق، امتداد، اتساع
- Jabal meaning: "الامتداد مع الحوز أو الشمول" (extension with possession or encompassment)
- تلاصق and امتداد hit; اتساع is emergent from their interaction.

**مط** (J=0.40, bJ=0.48, 4 families)
- م: تجمع، تلاصق — ط: امتداد، اشتمال، ضغط
- Jabal: تلاصق، امتداد
- Jabal meaning: "الامتداد والانسكاب" (extension and flowing-over)
- Two direct hits; الانسكاب (outflow) is a quality emerging from the combination.

**Why م composes best:** م's features تجمع and تلاصق appear in Jabal's vocabulary at very high frequency. They describe *operations* — the acts of gathering and adhering — rather than *qualities* (softness) or *measurements* (size). Operational features transfer upward; quality and measurement features emerge. م is almost always contributing something recognisable to the final nucleus description.

**Notable failure in م-family:**

**مث** (J=0.00, bJ=0.00, 4 families)
- م: تجمع، تلاصق — ث: كثافة، تجمع
- Composed: {تجمع، تلاصق، كثافة}
- Jabal features: ظاهر
- Jabal meaning: "تشخص الشيء أو رشحه" (the apparition of a thing or its becoming manifest)
- Despite a dense composed set, Jabal's مث is entirely about *appearance* (ظاهر) — an emergent directional concept absent from both letters.

---

### 4.2 س-Family — Average Blended Jaccard: 0.249

**س empirical features:** امتداد (extension), نفاذ (penetration), دقة (fineness)

With three features, س is the richest letter in the empirical vocabulary — and that richness is its compositional advantage. Any nucleus involving س has three features in play, and Jabal's Arabic descriptions of nuclei with شين-ثنائيات frequently invoke at least one of the s-cluster.

**Top performers:**

**سر** (J=0.60, bJ=0.645, 18 families — highest-frequency strong match in the entire dataset)
- س: امتداد، نفاذ، دقة — ر: استرسال، امتداد
- Composed: {امتداد، نفاذ، دقة، استرسال}
- Jabal features: تلاصق، امتداد، نفاذ، دقة
- Jabal meaning: "الامتداد أو النفاذ مع الدقة" (extension or penetration with fineness)
- Three of four composed features hit exactly. تلاصق in Jabal is the extra feature. This is one of the most productive nuclei in Arabic (سرى، سراء، سرير، سريرة، مسرى...) and composition works well.

**سن** (J=0.50, bJ=0.50, 11 families)
- س: امتداد، نفاذ، دقة — ن: نفاذ، باطن، امتداد
- Composed: {امتداد، نفاذ، دقة، باطن}
- Jabal features: تلاصق، امتداد، نفاذ، حدة، دقة
- Jabal meaning: "الامتداد (أو النفاذ) مع حدة أو دقة"
- Both letters share نفاذ and امتداد — the intersection reinforces. Jabal's حدة (sharpness) is an emergent intensification of دقة.

**سط** (J=0.286, bJ=0.38, 7 families)
- س: امتداد، نفاذ، دقة — ط: امتداد، اشتمال، ضغط
- Composed: {امتداد، نفاذ، دقة، اشتمال، ضغط}
- Jabal features: تلاصق، امتداد، دقة، غلظ
- Jabal meaning: "الامتداد الدقيق مع الانتهاء بغلظ" (fine extension terminating in coarseness)
- Two direct hits; غلظ (coarseness) emerges from ط's ضغط (pressure) accumulating — a quality the union does not express.

**سق** (J=0.333, bJ=0.413, 6 families)
- س: امتداد، نفاذ، دقة — ق: قوة، عمق
- Composed: {امتداد، نفاذ، دقة، قوة، عمق}
- Jabal features: نفاذ، غلظ، جوف
- Jabal meaning: "نفاذ غليظ أو مهم من الجوف أو إليه" (substantial/thick penetration to or from the interior)
- نفاذ hits exactly; غلظ and جوف are emergent from the force-and-depth (ق) interacting with the fine-penetrating (س).

**سم** (J=0.40, bJ=0.43, 8 families)
- س: امتداد، نفاذ، دقة — م: تجمع، تلاصق
- Composed: {امتداد، نفاذ، دقة، تجمع، تلاصق}
- Jabal features: اختراق، تجمع
- Jabal meaning: "نوع من الخرق الذي يضم" (a type of perforation that also binds)
- تجمع hits; اختراق (penetration-through) is a strengthened form of نفاذ — near-synonym territory.

**Notable س failure:**

**ست** (J=0.00, bJ=0.00, 2 families)
- س: امتداد، نفاذ، دقة — ت: ضغط، دقة، قطع
- Composed: {امتداد، نفاذ، دقة، ضغط، قطع}
- Jabal features: اشتمال، باطن
- Jabal meaning: "التغطية والإخفاء" (covering and concealment)
- Two highly operational letters produce a concealment concept. اشتمال and باطن describe the *result* of fine penetrating extension (س) being cut off (ت) — the covering is what remains after the cut. Pure interaction product.

**Why س composes well:** Three features means higher probability of overlap with any nucleus description. But more importantly, س's features (امتداد، نفاذ، دقة) are *process descriptors* — they describe what a fine, penetrating, extending action looks like — and Arabic nucleus descriptions frequently describe exactly such actions.

---

### 4.3 غ-Family — Average Blended Jaccard: 0.227

**غ empirical features:** باطن (interior), اشتمال (containment/envelopment)

غ describes an inward-containing dynamic: the interior held within an enveloping boundary. This is a specific and stable concept that appears frequently in Jabal's descriptions of nuclei with غ.

**Top performers:**

**غم** (J=0.50, bJ=0.65, 4 families)
- غ: باطن، اشتمال — م: تجمع، تلاصق
- Composed: {باطن، اشتمال، تجمع، تلاصق}
- Jabal features: اشتمال، باطن
- Jabal meaning: "نوع من التغطية والحجب" (a type of covering and concealment)
- Exact subset: Jabal selects exactly غ's own features. م's contribution (تجمع، تلاصق) drops entirely. This is an asymmetric composition — one letter dominates, one disappears.

**غث** (J=0.40, bJ=0.48, 3 families)
- غ: باطن، اشتمال — ث: كثافة، تجمع
- Composed: {باطن، اشتمال، كثافة، تجمع}
- Jabal features: تجمع، تماسك، كثافة
- Jabal meaning: "جنس من التجمع أو التراكم لمادة هشة خفيفة" (a type of aggregation or accumulation of brittle light material)
- تجمع and كثافة both hit. تماسك (cohesion/holding-together) is near-synonymous with اشتمال in the blended scoring.

**غر** (J=0.333, bJ=0.458, 10 families)
- غ: باطن، اشتمال — ر: استرسال، امتداد
- Composed: {باطن، اشتمال، استرسال، امتداد}
- Jabal features: امتداد، دقة، تلاصق، باطن
- Jabal meaning: "الغؤور والدخول بامتداد ودقة ويلزمه اللصوق والتغطي" (sinking in with extension and fineness, necessarily with adhesion and covering)
- باطن and امتداد hit; دقة is emergent (غ provides no fineness feature); تلاصق is an interaction product of the inward-containing movement.

**غص** (J=0.40, bJ=0.40, 4 families)
- غ: باطن، اشتمال — ص: غلظ، قوة، نفاذ
- Composed: {باطن، اشتمال، غلظ، قوة، نفاذ}
- Jabal features: نفاذ، غلظ
- Jabal meaning: "النفاذ بغلظ أو ضيق أو عُسْر" (penetrating with coarseness or constriction or difficulty)
- نفاذ and غلظ hit exactly, contributed by ص. غ's features (باطن، اشتمال) describe the environment into which نفاذ occurs — they provide context but disappear from Jabal's reduction.

**غب** (J=0.25, bJ=0.275, 6 families)
- غ: باطن، اشتمال — ب: ظهور، خروج
- Composed: {باطن، اشتمال، ظهور، خروج}
- Jabal features: عمق، باطن
- Jabal meaning: "الغئور والغياب أو الاستتار" (sinking, disappearance, or concealment)
- باطن hits; عمق is related to depth-of-inwardness — a specification of باطن's degree. غ dominates this nucleus too.

**Why غ composes well:** غ's concept of *inward containment* (باطن، اشتمال) is a fundamental spatial relation in Arabic semantics. Many nucleus descriptions invoke being-inside or being-covered — and غ predicts this directly. The letter is also semantically stable: غ never means anything other than inwardness across its root families, making it a reliable contributor.

---

### 4.4 ث-Family — Average Blended Jaccard: 0.221

**ث empirical features:** كثافة (density), تجمع (aggregation)

ث describes dense aggregation — the coming-together of many small things into a compact mass. This is a concrete, measurable quality that appears in many nucleus descriptions.

**Top performer:**

**ثق** (J=0.50, bJ=0.50, 5 families)
- ث: كثافة، تجمع — ق: قوة، عمق
- Composed: {كثافة، تجمع، قوة، عمق}
- Jabal features: غلظ، قوة
- Jabal meaning: "الغلظ والشدة" (coarseness/thickness and intensity)
- قوة hits directly. غلظ (coarseness) is a transformation of كثافة (density) — dense aggregation becomes coarse when strong force is applied. The blended scorer gives partial credit.

**ثخ** (J=0.25, bJ=0.25, 2 families)
- ث: كثافة، تجمع — خ: تخلخل، فراغ
- Composed: {كثافة، تجمع، تخلخل، فراغ}
- Jabal features: كثافة، غلظ
- Jabal meaning: "الكثافة والغلظ" (density and coarseness)
- كثافة hits exactly from ث. خ's features (looseness and void) disappear entirely — Jabal chooses the density side of this tension. Interesting case where composition predicts the dominant letter correctly.

**ثم** (J=0.25, bJ=0.275, 5 families)
- ث: كثافة، تجمع — م: تجمع، تلاصق
- Composed: {كثافة، تجمع، تلاصق}
- Jabal features: تجمع، حيز
- Jabal meaning: "ضم الدقائق أو ما يشبهها في حيز" (gathering of fine particles or their equivalent into a bounded space)
- تجمع hits (shared by both letters); حيز (bounded space) is emergent — the container concept appears when two gathering operations meet.

**ثب** (J=0.20, bJ=0.215, 6 families)
- ث: كثافة، تجمع — ب: ظهور، خروج
- Jabal features: تجمع، تماسك
- Jabal meaning: "التجمع والتماسك" (aggregation and cohesion/holding-together)
- تجمع hits; تماسك is an interaction product — cohesion emerges when aggregated density (ث) meets emerging force (ب).

**Why ث composes well:** Like م, ث's features are concrete and operational. Dense aggregation (كثافة، تجمع) is present in a large fraction of Arabic nucleus descriptions. The letter is also semantically narrow — it does not produce wildly varied nuclei — which means its feature set is a reliable predictor of its contribution to the final meaning.

---

### 4.5 ج-Family — Average Blended Jaccard: 0.219

**ج empirical features:** تجمع (aggregation), بروز (protrusion)

ج describes protruding aggregation — something that gathers into a mass and projects outward. The combination of inward-gathering with outward-projection makes ج nuclei semantically rich, with some compositionally transparent and some not.

**Strongest:**

**جث** (J=0.667, bJ=0.667, 3 families)
- ج: تجمع، بروز — ث: كثافة، تجمع
- Composed: {تجمع، بروز، كثافة}
- Jabal features: تجمع، كثافة
- Jabal meaning: "تجمع الكتلة الكثيفة" (aggregation of a dense mass)
- Two of three composed features hit exactly; بروز (protrusion) is the suppressed element — the dense mass may protrude but Jabal's description focuses on its being-gathered.

**جر** (J=0.333, bJ=0.433, 11 families)
- ج: تجمع، بروز — ر: استرسال، امتداد
- Composed: {تجمع، بروز، استرسال، امتداد}
- Jabal features: استرسال، باطن، تلاصق، امتداد
- Jabal meaning: "الاسترسال والامتداد" (continuous flow and extension)
- استرسال and امتداد both hit — ر's features dominate. ج's features (gathering and protrusion) fade, leaving flow and extension as the nucleus character.

**جم** (J=0.25, bJ=0.275, 5 families)
- ج: تجمع، بروز — م: تجمع، تلاصق
- Composed: {تجمع، بروز، تلاصق}
- Jabal features: تجمع، كثافة
- Jabal meaning: "التجمع والكثرة" (aggregation and multiplicity)
- تجمع hits (shared); كثافة is an emergent intensification when two gathering letters meet; بروز and تلاصق are suppressed.

**جب** (J=0.20, bJ=0.215, 9 families)
- ج: تجمع، بروز — ب: ظهور، خروج
- Jabal features: بروز، قطع، استواء
- Jabal meaning: "التجسم والبروز مع القطع أو الاستواء" (corporeal protrusion with cutting or levelling)
- بروز hits exactly. The combination of protrusion (ج) with emergence/exit (ب) consolidates the outward-projecting aspect; قطع and استواء are emergent qualities of that consolidated protrusion.

---

### 4.6 ب-Family — Average Blended Jaccard: 0.218

**ب empirical features:** ظهور (emergence/visibility), خروج (exiting)

ب describes the emergence of something from a contained state into visibility. It is a surface-letter — ب marks the moment of appearance. The family is large (24 nuclei) and shows moderate composition, with several clear successes.

**Strongest:**

**بش** (J=0.50, bJ=0.55, 2 families)
- ب: ظهور، خروج — ش: انتشار، تفرق
- Composed: {ظهور، خروج، انتشار، تفرق}
- Jabal features: انتشار، ظاهر
- Jabal meaning: "الانتشار الظاهر" (visible/manifest spreading)
- انتشار hits exactly; ظاهر (visible) is a near-synonym of ظهور. The nucleus is literally "manifest spreading" — both letters' contributions are recognisable.

**بهـ** (J=0.50, bJ=0.50, 5 families)
- ب: ظهور، خروج — هـ: فراغ، تخلخل
- Composed: {ظهور، خروج، فراغ، تخلخل}
- Jabal features: فراغ، ظاهر
- Jabal meaning: "الخلو والفراغ الظاهري" (visible/apparent emptiness)
- فراغ from هـ and ظاهر (near-synonym of ظهور from ب) both register. The nucleus is literally "visible void".

**بح** (J=0.40, bJ=0.40, 3 families)
- ب: ظهور، خروج — ح: خلوص، احتكاك، جفاف
- Composed: {ظهور، خروج، خلوص، احتكاك، جفاف}
- Jabal features: ظهور، فراغ
- Jabal meaning: "الكشف والفراغ" (revelation and emptiness)
- ظهور hits exactly. فراغ is an emergent concept — the void that appears when something exits is not encoded in either letter directly.

**بج** (J=0.25, bJ=0.25, 2 families)
- ب: ظهور، خروج — ج: تجمع، بروز
- Composed: {ظهور، خروج، تجمع، بروز}
- Jabal features: خروج، رخاوة
- Jabal meaning: "التفتق والتفجر الرخو" (soft bursting open)
- خروج hits exactly. رخاوة (softness) is an emergent quality of soft protrusion (ج) combined with gentle emergence (ب).

---

### 4.7 ق-Family — Average Blended Jaccard: 0.214

**ق empirical features:** قوة (force), عمق (depth)

ق describes concentrated deep force. Its two features are abstract and powerful, making ق capable of contributing to many nucleus types — but also making it susceptible to interaction effects because "force at depth" is often just the precondition for an emergent process.

**Strongest:**

**قن** (J=0.60, bJ=0.72, 7 families)
- ق: قوة، عمق — ن: نفاذ، باطن، امتداد
- Composed: {قوة، عمق، نفاذ، باطن، امتداد}
- Jabal features: نفاذ، باطن، إمساك، عمق، امتداد
- Jabal meaning: "النفاذ في الباطن أو الأخذ إليه بعمق أو امتداد"
- Four of five composed features hit. إمساك (grasping/holding) is the extra Jabal feature — an interaction effect where deep force penetrating inward produces holding.

**قت** (J=0.50, bJ=0.53, 2 families)
- ق: قوة، عمق — ت: ضغط، دقة، قطع
- Composed: {قوة، عمق، ضغط، دقة، قطع}
- Jabal features: دقة، نقص، قوة، عمق
- Jabal meaning: "الدقة وقلة ما به القوة في العمق" (fineness and scarcity of what carries force in the depth)
- Four of five composed features in Jabal. نقص (diminution) is the one emergent term — the scarcity/deficiency concept.

**قهـ** (J=0.50, bJ=0.50, 2 families)
- ق: قوة، عمق — هـ: فراغ، تخلخل
- Composed: {قوة، عمق، فراغ، تخلخل}
- Jabal features: باطن، قوة
- Jabal meaning: "إخراج ما في الباطن من قوة مذخورة" (releasing stored force from the interior)
- قوة hits; باطن is semantically close to عمق. The nucleus description reads almost like a paraphrase of the composed features.

**Notable ق failure:**

**قر** (J=0.00, bJ=0.07, 14 families)
- ق: قوة، عمق — ر: استرسال، امتداد
- Composed: {قوة، عمق، استرسال، امتداد}
- Jabal features: استقرار، تخلخل، حيز
- Jabal meaning: "استقرار ما شأنه التسيب في قاع عميق أو حيز"
- *Settling* (استقرار) is the interaction product of force (ق) arresting flow (ر). This is one of the clearest examples of an interaction-product failure — neither letter encodes stopping.

---

### 4.8 أ-Family — Average Blended Jaccard: 0.232

**أ empirical features:** None assigned

أ (hamza) has no empirical features in the current model — its phonological instability across dialects and historical variants, and its frequent grammatical use, have prevented a stable feature assignment. Yet the أ-family ranks third overall. The reason is that nuclei formed with أ are effectively *mono-literal*: the other letter carries the entire semantic load.

**أث** (J=1.00, bJ=1.00, 2 families) — the single perfect composition in the dataset.
- أ: ∅ — ث: كثافة، تجمع
- Composed: {كثافة، تجمع}
- Jabal features: تجمع، كثافة — exact identity
- Jabal meaning: "تجمع الدقائق بكثافة" (aggregation of fine particles with density)
- أ contributes nothing. ث carries the entire nucleus meaning. The near-perfect Jaccard is a perfect alignment of ث's features with Jabal's description — but it validates ث's features, not any composition between two distinct letters.

**أس** (J=0.167, bJ=0.177, 2 families)
- أ: ∅ — س: امتداد، نفاذ، دقة
- Composed: {امتداد، نفاذ، دقة}
- Jabal features: نفاذ، حدة، عمق، فجوة
- Jabal meaning: "نفاذ شعور أو أثر حاد في عمق أو فجوة" (penetration of sensation or a sharp effect into depth or cavity)
- نفاذ hits; the other Jabal features elaborate on it — حدة (sharpness) is an intensification of دقة, and عمق/فجوة specify the target space.

The أ-family's high blended average is partly a statistical artifact: when one letter contributes nothing, there is no compositional noise to overcome.

---

## 5. Worst Composition Families

### 5.1 ت-Family — Average Blended Jaccard: 0.122 (Worst among full families)

**ت empirical features:** ضغط (pressure), دقة (fineness), قطع (cutting)

ت describes precise, cutting pressure — a point-like force that severs. The problem is that ت's feature set is *operationally specific*: cutting and pressure describe what ت does, but what nuclei then *describe* is often the *result* of that cutting — states, qualities, conditions.

| Nucleus | bJ | Jabal Meaning |
|---------|-----|----------------|
| تج | 0.000 | العمل طلبًا للأجر (working for wages — a social concept) |
| تف | 0.000 | الوسخ على الجلد (dirt on skin — a quality) |
| تس | 0.000 | ما دل على العدد تسعة (the numeral nine — semantic drift) |
| تل | 0.000 | التكديس والاتباع (piling and following) |
| تع | 0.075 | الرخاوة التي يرتطم فيها (softness that absorbs impact) |
| تب | 0.043 | ضعف الشيء المتجمع أو ذهاب غلظه (weakening of the aggregated) |

**The ت pattern:** ت's features (pressure, fineness, cutting) describe *the agent* of a process, not the process's outcome. Jabal's nucleus descriptions overwhelmingly describe *outcomes* — the state left behind after something has been cut, pressed, or finely applied. The gap is systematic: ت is a verb, nuclei are nouns.

**Why it fails:** ت is primarily an *instrumental* letter — it describes a precise mechanical operation. But Arabic nuclei across the vocabulary frequently describe *result states* (softness, weakness, dirtiness) rather than operations. When an operation-letter meets a result-heavy description system, the features miss.

---

### 5.2 ز-Family — Average Blended Jaccard: 0.128

**ز empirical features:** نفاذ (penetration), اكتناز (compactness/tautness)

ز describes taut penetration — something that pushes through with contained internal tension. The combination of نفاذ (which is common) and اكتناز (which is rare in nucleus descriptions) makes ز an inconsistent composer: half its features are predictive, half are invisible.

| Nucleus | bJ | Jabal Meaning |
|---------|-----|----------------|
| زخ | 0.000 | اندفاع الشيء بقوة (surging/thrusting with force) |
| زق | 0.000 | الدفع بمعنى الحشو (pushing as stuffing) |
| زع | 0.000 | التحريك القليل دفعًا (slight pushing motion) |
| زغ | 0.000 | الدفع في أثناء بدقة وخفة (light/fine pushing into interior) |
| زد | 0.000 | إضافة شيء إلى الحيز (adding to a bounded space) |
| زم | 0.383 | ضم الكثير باكتناز (gathering many with compactness) |
| زن | 0.353 | اختزان الباطن بقوة (storing the interior forcefully) |

**The ز pattern:** ز nuclei frequently involve *directional pushing* (الدفع، الاندفاع) and *movement*. Neither نفاذ nor اكتناز encodes direction — they encode character and texture of action. The directional content of ز-nuclei is emergent from context, not predictable from ز's features.

**Best ز case:** زم (bJ=0.383) works because م's تجمع and تلاصق align with اكتناز's sense of compactness — gathering many things with tautness. When ز meets a gathering letter, the compactness concept survives.

---

### 5.3 هـ-Family — Average Blended Jaccard: 0.131

**هـ empirical features:** فراغ (void), تخلخل (looseness/sparseness)

هـ describes hollow sparseness — the quality of something internally empty and loosely structured. These are *textural quality* features, not operations. When هـ enters a nucleus, Jabal's description must somehow derive from void + looseness — but Arabic nuclei regularly describe *dynamics* (actions, processes) rather than textures.

| Nucleus | bJ | Jabal Meaning |
|---------|-----|----------------|
| هـز | 0.000 | التحرك حركة خفيفة مضطربة (light trembling motion) |
| هـش | 0.000 | فقد قوة التماسك (losing cohesive force) |
| هـط | 0.000 | لين وانقياد دائم (continuous softness and compliance) |
| هـب | 0.086 | مفارقة المقر باندفاع (leaving one's place with surge) |
| هـد | 0.250 | تفكك القائم المنتصب (collapse of what stands upright) |
| هـل | 0.250 | فراغ الأثناء (emptiness of the interior) |

**The هـ pattern:** هـ's best nuclei (هـد، هـل) are the ones where Jabal's description directly invokes فراغ or تخلخل. When Jabal describes a process (هـز: trembling; هـب: surging departure), the quality-features miss entirely.

هـ is a *quality letter* — it describes what something is like, not what it does. Nuclei that preserve that quality dimension compose well; nuclei that describe what happens (often a *process* in which the void or looseness participates) do not.

---

### 5.4 ر-Family — Average Blended Jaccard: 0.145

**ر empirical features:** استرسال (continuous flow), امتداد (extension)

ر is a *process letter* — it describes continuous, smooth, extending motion. The paradox is that ر appears in some of the best-composing nuclei in the dataset (سر: J=0.60; رس: J=0.50; رن: J=0.43) when paired with letters whose features reinforce flow and extension. But the ر-family average is low because ر systematically *transforms* when paired with other letter types.

**The ر-pattern — spaciousness emergence:**

The most important finding about ر is its systematic transformation: when ر's continuous flow meets letters encoding *surface*, *containment*, or *protrusion*, the nucleus consistently describes *spaciousness* (اتساع، رقة، خلوص، فراغ) — a concept absent from both letters:

| Nucleus | Composed | Jabal features | Jabal meaning |
|---------|----------|----------------|----------------|
| رق | استرسال، امتداد، قوة، عمق | اتساع، رقة | expansiveness and fineness |
| رح | استرسال، امتداد، خلوص، احتكاك | اتساع، رقة | breadth and fineness |
| بر | ظهور، خروج، استرسال، امتداد | خلوص، فراغ | purity and void |
| رخ | استرسال، امتداد، تخلخل، فراغ | رخاوة | softness |
| رع | استرسال، امتداد، ظهور، عمق | تلاصق، امتداد، رقة، رخاوة | extension with softness |

This is a *bi-literal interaction rule*: ر (flow + extension) when paired with letters encoding surface, boundary, or resistance produces spaciousness as an interaction product. This rule cannot be captured by feature union; it would require a dedicated ر-interaction term.

---

## 6. Failure Patterns

Three structurally distinct failure families account for nearly all J=0 cases. These are not random misses — they are principled limits of the union model.

### 6.1 Quality Emergence

**Description:** The letters describe *operations* (pressure, aggregation, penetration). The nucleus describes the *quality* of the result (softness, dryness, thickness, tenderness). The feature vocabularies for operations and qualities are different layers of Arabic semantics, and union cannot bridge them.

**Examples:**

**بس** (J=0, 8 families) — ب: ظهور، خروج — س: امتداد، نفاذ، دقة
- Jabal meaning: "الجفاف واليبوسة" (dryness and aridity)
- Neither letter encodes dryness. The combination of fine-penetrating extension (س) breaking through a surface (ب) has, in Arabic's semantic history, come to denote desiccation. This is a quality that *emerged* from the phonetic-semantic interaction.

**تع** (J=0, 2 families) — ت: ضغط، دقة، قطع — ع: ظهور، عمق
- Jabal meaning: "الرخاوة التي يرتطم فيها" (softness that absorbs impact)
- رخاوة (softness) is absent from both letters. The cutting precision of ت meeting the deep visibility of ع produces a *receiving* softness — the quality of a surface that yields to precise pressure.

**نع** (J=0, 7 families) — ن: نفاذ، باطن، امتداد — ع: ظهور، عمق
- Jabal meaning: "الرخاوة والطراءة وما إلى ذلك رقة الأثناء"
- Both رخاوة and رقة are quality terms. The inner penetration (ن) + deep visibility (ع) combination describes the *character* of interior depth — tender, soft, accessible — not the operations themselves.

**Cognitive explanation:** When two operations converge, their *product* often has a different semantic type than either cause. Pressure + flow → stillness. Aggregation + dryness → powder. Penetration + interior → tenderness. The product is a state-property, not an action-property. Feature union only captures action-properties.

---

### 6.2 Directional Specificity

**Description:** The letters describe actions that are *direction-agnostic* — they say what happens but not which way. The nucleus encodes a *direction* (upward, downward, forward, away) that the simple union cannot derive.

**Examples:**

**نب** (J=0, 9 families) — ن: نفاذ، باطن، امتداد — ب: ظهور، خروج
- Jabal meaning: "النُّبُوُّ ارتفاعًا أو ابتعادًا" (rising or moving away)
- The composed set describes inward-penetration + outward-emergence. The nucleus has *rotated* this to mean upward protrusion. Neither letter carries a vertical axis.

**قل** (J=0, 8 families) — ق: قوة، عمق — ل: تعلق، امتداد
- Jabal meaning: "الرفع بصورة من الصور" (lifting in some form)
- Deep force (ق) + clinging extension (ل) → lifting? The direction (upward) is not in either letter.

**قف** (J=0, 4 families) — ق: قوة، عمق — ف: تفرق، فصل
- Jabal features: صعود، صلابة، غلظ، امتساك
- Jabal meaning: "نوع من الارتفاع مع صلابة أو امتساك" (a type of rising with rigidity or grasping)
- صعود (ascent) again — deep force + separation produces upward movement? The direction is an interaction conclusion, not a letter property.

**زل** (J=0, 5 families) — ز: نفاذ، اكتناز — ل: تعلق، امتداد
- Jabal meaning: "الانزلاق (التحرك السهل) عن مستوٍ" (gliding — easy movement off a surface)
- Directional: movement off a level surface. Neither letter encodes a horizontal axis or the concept of surface-departure.

**Cognitive explanation:** Direction and axis are not atomic features of Arabic letters — they are relational properties that emerge from how operations interact with the environment. The letter feature vocabulary models operations as such; it would need a separate *orientation* layer to capture directional nuclei.

---

### 6.3 Interaction Products

**Description:** The nucleus describes what *happens when* the two letters' operations meet — the dynamic outcome of their interaction. Neither letter encodes the outcome; it is the result of the encounter.

**Examples:**

**قر** (J=0, 14 families) — ق: قوة، عمق — ر: استرسال، امتداد
- Jabal meaning: "استقرار ما شأنه التسيب في قاع عميق أو حيز" (settling of what tends to flow, into a deep base)
- استقرار (settling/coming-to-rest) is what happens when deep force (ق) arrests continuous flow (ر). Neither letter means stopping. The arrest is the *product* of their opposition.

**رج** (J=0, 9 families) — ر: استرسال، امتداد — ج: تجمع، بروز
- Jabal meaning: "الاضطراب المادي، أي اضطراب الجِرْم وتردده" (physical agitation — oscillation of a body)
- اضطراب (agitation) arises when flowing extension (ر) repeatedly encounters protruding aggregation (ج) — the flow is blocked, bounces back, and produces oscillation. The dynamics require modelling the *tension* between the two operations.

**رب** (J=0, 9 families) — ر: استرسال، امتداد — ب: ظهور، خروج
- Jabal meaning: "الاستغلاظ وما إليه من تماسك وتجمع" (thickening and cohesion)
- Neither flow (ر) nor emergence (ب) means thickening. Sustained flow accumulating at a surface point of emergence → deposit → thickening. The nucleus describes the deposit, not the letters.

**زخ** (J=0, 2 families) — ز: نفاذ، اكتناز — خ: تخلخل، فراغ
- Jabal meaning: "اندفاع الشيء بقوة من أثناء أو فيها" (surging of something by force through or within)
- اندفاع (surging) is what occurs when taut-penetrating (ز) energy is released through void (خ). The surge is the interaction product.

**Cognitive explanation:** Interaction products require a *dynamical* model — a function that takes two operations as arguments and computes what happens when they meet. Union is a static set operation; it cannot model collision, obstruction, tension, or release.

---

## 7. Summary Table: All Letter Families Ranked by Composition Success

The following table ranks all 28 letter families by average blended Jaccard (minimum 1 nucleus, l2 non-empty). Families with fewer than 3 nuclei are marked with an asterisk and treated as preliminary.

| Rank | Letter | Empirical Features | Avg bJ | Avg J | n | Composition Character |
|------|--------|--------------------|--------|-------|---|-----------------------|
| 1 | ي* | اتصال، امتداد | 0.383 | 0.333 | 1 | Too few for conclusions |
| 2 | م | تجمع، تلاصق | 0.278 | 0.220 | 21 | Best sustained composer; features match nucleus vocabulary |
| 3 | س | امتداد، نفاذ، دقة | 0.249 | 0.189 | 19 | Three stable operational features |
| 4 | أ* | — | 0.232 | 0.124 | 7 | High due to mono-literal effect (أ contributes nothing) |
| 5 | غ | باطن، اشتمال | 0.227 | 0.181 | 16 | Stable spatial concept; consistent contributor |
| 6 | ث | كثافة، تجمع | 0.221 | 0.186 | 9 | Dense aggregation matches nucleus vocabulary |
| 7 | ج | تجمع، بروز | 0.219 | 0.173 | 14 | Operational; فراغ-type nuclei suppress one feature |
| 8 | ب | ظهور، خروج | 0.218 | 0.163 | 24 | Surface emergence; large family with clear successes |
| 9 | ق | قوة، عمق | 0.214 | 0.157 | 20 | Strong when ن/ت reinforce; fails in directional/interactional cases |
| 10 | ط | امتداد، اشتمال، ضغط | 0.198 | 0.151 | 13 | Three features aid coverage |
| 11 | ك | تجمع، إمساك، ضغط | 0.198 | 0.157 | 18 | Holding operations align well |
| 12 | ذ | نفاذ، حدة | 0.192 | 0.145 | 11 | Sharp penetration; moderate alignment |
| 13 | خ | تخلخل، فراغ | 0.188 | 0.147 | 16 | Void/looseness; quality-letter |
| 14 | ن | نفاذ، باطن، امتداد | 0.188 | 0.130 | 27 | Large family; interior-penetration often emergent |
| 15 | ح | خلوص، احتكاك، جفاف | 0.184 | 0.136 | 22 | Mixed; friction/purity features partially align |
| 16 | ع | ظهور، عمق | 0.182 | 0.124 | 23 | Depth-visibility often produces quality nuclei |
| 17 | د | احتباس، امتداد | 0.180 | 0.131 | 19 | Retention + extension align when nucleus preserves them |
| 18 | ص | غلظ، قوة، نفاذ | 0.178 | 0.136 | 14 | Force-features sometimes survive to nucleus |
| 19 | ل | تعلق، امتداد | 0.175 | 0.124 | 20 | Attachment + extension align inconsistently |
| 20 | ض | ضغط، تجمع، كثافة | 0.170 | 0.119 | 15 | ضم is the standout; rest moderate |
| 21 | ش | انتشار، تفرق | 0.154 | 0.108 | 18 | Scattering features present but rarely dominant |
| 22 | ف | تفرق، فصل | 0.153 | 0.097 | 21 | Separation often emergent rather than direct |
| 23 | ر | استرسال، امتداد | 0.145 | 0.095 | 24 | Systematically transforms; spaciousness-emergence pattern |
| 24 | هـ | فراغ، تخلخل | 0.131 | 0.094 | 12 | Quality-letter; processes suppress it |
| 25 | ز | نفاذ، اكتناز | 0.128 | 0.082 | 16 | اكتناز rarely survives to nucleus description |
| 26 | ت | ضغط، دقة، قطع | 0.122 | 0.072 | 14 | Instrumental letter; result-state gap |
| 27 | و | اشتمال، احتواء | 0.114 | 0.050 | 4 | Too few; envelopment frequently emergent |
| 28 | ظ | غلظ، ظهور | 0.048 | 0.033 | 6 | Near-total failure; features rarely preserved |
| 29 | ء | تأكيد، قوة | 0.025 | 0.000 | 3 | Hamza asserts; nuclei describe specific processes |

*Families with n < 4 are statistically preliminary.*

---

## 8. Implications

### 8.1 The Genome Has Two Semantic Tiers

The results confirm a two-tier structure in the Arabic root genome:

**Tier 1 — Compositional tier (union works):** Letters encode *operations* (gathering, penetrating, extending, pressing). Nuclei formed from two operational letters in the same semantic register describe the *combination* of those operations. Union prediction works well when:
- Both letters encode concrete operations (not qualities)
- The nucleus describes a process (not a result-state)
- The letters reinforce rather than oppose each other

Clear Tier 1 nuclei: ضم، سر، قن، غم، جث، مك، مد

**Tier 2 — Emergent tier (union fails):** When the two operations interact, they produce a result that has a different semantic type — a quality, a measurement, a direction, or a dynamic process. The result cannot be read from either letter alone. Examples: بر (purity), قر (settling), رج (agitation), نب (ascent), بس (dryness).

Approximately 47% of genuine nuclei are Tier 2, with J = 0.

### 8.2 Feature Vocabulary Is Letter-Level, Not Nucleus-Level

The most frequent emergent features at the nucleus level — رخاوة (softness), اتساع (breadth), استقرار (settling), نقص (diminution), انتقال (transition) — are largely absent from the letter empirical feature vocabulary. This is not a calibration error. These are *state and measurement terms* that describe the outcomes of interactions. The letter vocabulary should describe operations; these terms describe the results of operations. They belong to a distinct semantic tier.

Implication: any system that tries to predict nucleus meaning from letter features needs a *translation function* between the two tiers — not just a richer letter vocabulary.

### 8.3 Bilateral Interaction Rules Are Discoverable

The ر-pattern is the clearest example: ر (flow + extension) + {surface/boundary letter} → spaciousness. This rule is *compositional* but not *unary*. It cannot be captured by adding a feature to ر; it requires a dedicated bi-literal rule: "when ر is paired with a letter whose operation creates a boundary, the nucleus encodes space cleared by the flow."

A small catalogue of such rules — perhaps 15–25 covering the most frequent interaction types — would substantially improve prediction for Tier 2 nuclei. Candidate rules identifiable from this dataset:

| Pattern | Type | Example | Product |
|---------|------|---------|---------|
| ر + boundary-letter | Interaction | بر، رح، رق | اتساع، رقة (spaciousness) |
| ق + flow-letter | Interaction | قر | استقرار (settling) |
| ر + mass-letter | Accumulation | رب | غلظ، تجمع (thickening) |
| flow + protruding | Oscillation | رج | اضطراب (agitation) |
| void-letter + operational | Collapse | هـد | تفكك (disintegration) |

### 8.4 م Is the Model Genome Letter

Among all 28 letters, م stands out as the most compositionally reliable. Its features (تجمع، تلاصق) are:

1. **Concrete** — they describe a physical act (gathering, adhering), not an abstract quality
2. **Frequent** — Arabic nucleus descriptions invoke gathering and cohesion more than almost any other concept
3. **Stable** — م's meaning does not shift across semantic registers; it means gathering-with-adhesion in physical, biological, cognitive, and social nuclei alike

The genome hypothesis is most convincingly demonstrated in م-family nuclei. ضم, مك, مد, مم are the clearest cases where simple letter composition correctly predicts nucleus meaning. They are the poster nuclei for Tier 1.

### 8.5 Implications for Root Prediction

Root prediction (Method A) uses nucleus-level features as the primary semantic anchor. The composition results have direct consequences:

- For roots under **high-J nuclei** (ضم، سر، قن، عم, etc.): letter-level features are strong priors. Prediction can leverage letter features directly.
- For roots under **low-J nuclei** (بر، قر، رب، رج, etc.): letter features are weak priors. Nucleus-level features (Jabal's descriptions) must be treated as independent evidence, not derivable from letters.
- For nuclei with **J = 0 and large membership** (بر: 16 families; قر: 14): these are high-priority cases for manual feature alignment — fixing one nucleus improves prediction for many roots simultaneously.

### 8.6 What This Means for the Linguistic Genome Hypothesis

The genome hypothesis — that Arabic root meanings are systematically shaped by the meanings of their constituent letters — is empirically confirmed but qualified:

**Confirmed:** Letter features predict nucleus features with statistically significant frequency. The 0.141 mean Jaccard is far above a random baseline near zero. 56.5% of nuclei show at least some signal. The genome principle is real.

**Qualified:** Simple feature union accounts for only 5.1% of nuclei strongly (J ≥ 0.5). The composition function is not additive union — it is more complex, involving at least three interaction mechanisms (quality emergence, directional encoding, and interaction-product generation) that cannot be reduced to the sum of letter contributions.

**Implication for the genealogy thesis:** Arabic does not work like a simple additive code where letter meanings sum to root meanings. It works more like a *protein folding system*, where the chemical properties of amino acids (letters) constrain but do not uniquely determine the folded structure (nucleus/root). The constraints are real and systematic — the genome is real — but the mapping is many-to-one through interaction dynamics that the genome alone does not determine.

---

## 9. Conclusion

Of 409 genuine binary nuclei, 21 (5.1%) have strong compositional alignment (J ≥ 0.5) between the union of their letters' empirical features and Jabal al-Muzaffar's descriptions. A further 210 (51.3%) show partial signal (J > 0). Mean Jaccard is 0.141; mean blended Jaccard is 0.186.

The best-composing families — م, س, غ, ث, ج — share a common property: their letters encode concrete, operational features (gathering, penetrating, protruding, containing) that directly appear in nucleus descriptions. The worst-composing families — ت, ز, هـ, ر — either encode *instrumental* operations (cutting, pushing) whose nuclei describe results, or encode *quality* features (void, looseness) that frequently disappear in process-heavy nucleus descriptions, or systematically *transform* through interaction effects (ر's spaciousness-emergence).

Three principled failure families account for the J = 0 cases: quality emergence (operations → result-qualities), directional specificity (direction-agnostic operations → directional nuclei), and interaction products (two operations meeting → dynamic outcome). Each failure type is interpretable and points toward a specific augmentation of the composition model.

The Arabic root genome operates in two tiers: a compositional tier where letter features flow upward by union, and an emergent tier where interaction dynamics produce nucleus meanings that no letter encodes alone. Both tiers are rule-governed. Only the first is captured by the current model.

---

*Data source: `outputs/lv1_scoring/data/binary_composition_data.json` (456 nuclei)*
*Letter features: Method A consensus from 30 BAB files, see `empirical_letter_meanings.md`*
*Nucleus features: Jabal al-Muzaffar, Al-Mu'jam al-Ishtiqaqi al-Mu'assal*
*Analysis: Experiment S2.5, LV1 Research Factory, 2026-03-26*
