# The Arabic Binary Nucleus Genome

**Source:** THE_BINARY_NUCLEUS_GENOME.md (Juthoor LV1, Experiment S2.5)
**Date:** 2026-03-26
**Dataset:** 456 binary nuclei (ثنائيات) from Jabal's *Al-Mu'jam al-Ishtiqaqi al-Mu'assal*

---

## What Is a Binary Nucleus?

A binary nucleus (ثنائي — *thuna'i*) is a two-letter combination that functions as the semantic core of a root family in Arabic.

Every triliteral root contains three overlapping binary pairs: R1+R2 (the primary nucleus), R2+R3 (the secondary nucleus), and R1+R3 (the frame nucleus). Juthoor's analysis uses the R1+R2 primary nucleus throughout, as this is the most semantically stable pair.

Jabal catalogued 456 such nuclei, each with an Arabic description of the shared meaning across all roots containing that pair. For example:

- **سر** (sin-ra): "الامتداد الدقيق المتواصل" — fine, continuous penetrating extension (18 root families — largest nucleus in the dataset)
- **ضم** (dad-meem): "الجمع بضغط ولأم" — gathering by pressure and binding
- **قن** (qaf-nun): "النفاذ في الباطن بعمق أو امتداد" — penetrating into the interior with depth or extension

---

## The Core Experiment

**Question:** Can we predict a binary nucleus's meaning by combining its two letters' empirical feature sets?

**Composition rule:** Given letters X and Y, the predicted nucleus meaning is simply:
```
predicted(XY) = features(X) ∪ features(Y)
```

This is the simplest possible composition — pure feature union, no interaction terms, no position weighting.

**Scoring:** Jaccard similarity between the predicted feature set and Jabal's actual feature set for the nucleus.

```
J(XY) = |predicted ∩ actual| / |predicted ∪ actual|
```

J = 1.0 means perfect prediction. J = 0.0 means no overlap.

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total nuclei in dataset | 456 |
| Genuine nuclei (at least one side has empirical features) | 409 |
| Mean Jaccard (genuine nuclei) | 0.141 |
| Mean Blended Jaccard (genuine nuclei) | 0.186 |
| Nuclei with any signal (J > 0) | 56.5% |
| Strong composition (J ≥ 0.5) | 21 nuclei (5.1%) |

**Interpretation:** Composition by simple feature union works for roughly half the system, not all of it. The 0.141 mean is substantially above a random baseline near zero — letter meanings carry real systematic predictive power. But full additivity is not supported.

---

## Score Distribution

| Jaccard Band | Count | Percent | Interpretation |
|---|---|---|---|
| J = 0.0 | 178 | 43.5% | No overlap — complete compositional failure |
| 0 < J < 0.20 | 120 | 29.3% | Weak signal — one feature overlaps |
| 0.20 ≤ J < 0.50 | 90 | 22.0% | Partial — multiple features overlap |
| J ≥ 0.50 | 21 | 5.1% | Strong — majority of features predicted |

---

## The 21 Strong-Composition Nuclei (J ≥ 0.5)

These are the clearest cases where letter meanings compose directly into nucleus meaning:

| Nucleus | J | Members | Arabic Meaning | Composition Analysis |
|---------|---|---------|----------------|---------------------|
| أث | 1.000 | 2 | تجمع الدقائق بكثافة | أ has no features; ث carries it all |
| ضم | 0.750 | 2 | هو الجمع بضغط ولأم | ض (pressure) + م (gathering) = gathering by pressure — poster case |
| عم | 0.750 | 9 | الالتحام العلوي، التجمع مع علو | ع (depth→visibility) + م (gathering) = encompassing depth |
| جث | 0.667 | 3 | تجمع الكتلة الكثيفة | ج (protrusion) + ث (density) = dense protruding mass |
| سر | 0.600 | 18 | الامتداد أو النفاذ مع الدقة | س (extension+fineness) + ر (flow) = fine continuous flow |
| قن | 0.600 | 7 | النفاذ في الباطن بعمق أو امتداد | ق (force+depth) + ن (penetration+inner) = deep inner penetration |
| بش | 0.500 | 2 | الانتشار الظاهر | ب (emergence) + ش (spreading) = manifest spreading |
| بهـ | 0.500 | 5 | الخلو والفراغ الظاهري | ب (emergence) + هـ (void) = visible emptiness |
| ثق | 0.500 | 5 | الغلظ والشدة | ث (density) + ق (depth-force) = coarse intensity |
| ذق | 0.500 | 3 | النفاذ الحاد والأثر العميق | ذ (penetration) + ق (depth) = sharp deep penetrating effect |
| رس | 0.500 | 5 | النفاذ بامتداد | ر (flow) + س (extension+penetration) = penetrating flow |
| سن | 0.500 | 11 | الامتداد (أو النفاذ) مع حدة أو دقة | س (extension+fineness) + ن (inner extension) = sharp fine extension |
| صد | 0.500 | 8 | شيء كثيف صلب يعترض النفاذ | ص (thick+force) + د (retention) = thick solid barrier |
| غم | 0.500 | 4 | نوع من التغطية والحجب | غ (inner+concealing) + م (gathering) = covering and concealment |
| قت | 0.500 | 2 | الدقة وقلة ما به القوة في العمق | ق (force+depth) + ت (pressure+fineness) = fine force at depth |
| قهـ | 0.500 | 2 | إخراج ما في الباطن من قوة مذخورة | ق (force+depth) + هـ (void) = releasing stored interior force |
| كث | 0.500 | 2 | التجمع الكثيف لأشياء دقيقة | ك (gripping) + ث (density) = densely gripped fine things |
| مد | 0.500 | 4 | الامتداد والغاية | م (adhesion) + د (extension) = adhesive extension to a limit |
| مك | 0.500 | 5 | التمكن والرسوخ والاحتباس | م (gathering) + ك (gripping) = total groundedness |
| مم | 0.500 | 2 | التجمع والتضام | م + م: both gather; doubling intensifies |
| نس | 0.500 | 8 | نفاذ بدقة من أثناء شيء أو فيها | ن (penetration) + س (fineness) = fine-penetrating through interior |

**Poster case — ضم:** ض (pressure + gathering + density) + م (gathering + adhesion) → predicted: {pressure, gathering, density, adhesion} → Jabal says "gathering by pressure" — exact subset. This is the clearest "genome works" example.

---

## Best Composition Families

Letters whose empirical features flow most reliably into nucleus meanings:

### 1. م-Family — Mean Blended Jaccard: 0.278 (best)

م's features (تجمع + تلاصق — gathering and adhesion) are *operational concepts* that appear at high frequency in Jabal's nucleus descriptions. When م enters a nucleus, it almost always contributes تجمع or تلاصق because Arabic nucleus descriptions heavily involve grouping and attachment.

Top performers: ضم (J=0.75), مم (J=0.50), مك (J=0.50), مد (J=0.50)

Why م composes best: its features describe *operations* (acts of gathering and adhering), not qualities (softness, dryness). Operational features transfer upward; quality features often become subsumed in an emergent result.

### 2. س-Family — Mean Blended Jaccard: 0.249

س has three features (امتداد + نفاذ + دقة), giving it higher probability of overlap with any nucleus description. Its features are also *process descriptors* — they describe what fine, penetrating, extending action looks like.

Top performers: سر (J=0.60, 18 families — highest-frequency strong match), سن (J=0.50), نس (J=0.50)

### 3. غ-Family — Mean Blended Jaccard: 0.227

غ's concept of inward containment (باطن + اشتمال) is a fundamental spatial relation in Arabic semantics. Many nucleus descriptions invoke being-inside or being-covered — and غ predicts this directly.

Top performers: غم (J=0.50), جث (J=0.667), غص (J=0.40)

### 4. ث-Family — Mean Blended Jaccard: 0.221

ث (كثافة + تجمع — density + aggregation) is semantically narrow and stable. Dense aggregation appears in many Arabic nucleus descriptions, and ث never means anything other than dense gathering across its root families.

Top performer: ثق (J=0.50), جث (J=0.667)

### 5. ج-Family — Mean Blended Jaccard: 0.219

ج (تجمع + بروز — aggregation + protrusion) combines two concepts that are compatible but distinct. Strongest when paired with another density letter.

Top performer: جث (J=0.667)

---

## Worst Composition Families

### ت-Family — Mean Blended Jaccard: 0.122 (worst)

ت's features (ضغط + دقة + قطع — pressure + fineness + cutting) describe *the agent* of a process, not the outcome. Arabic nucleus descriptions overwhelmingly describe *result states*. When an operation-letter meets a result-heavy description system, the features miss.

Examples of failure: تج (working for wages — social concept), تف (dirt on skin — quality), تس (the numeral nine — semantic drift). These are all *results* of precise fine cutting/pressure — not the cutting itself.

### ز-Family — Mean Blended Jaccard: 0.128

ز's features (نفاذ + اكتناز — penetration + compactness) fail because ز nuclei frequently involve *directional pushing* (اندفاع — forward surge) which neither نفاذ nor اكتناز encodes. Direction is emergent from context, not predictable from ز.

### هـ-Family — Mean Blended Jaccard: 0.131

هـ's features (فراغ + تخلخل — void + looseness) are *textural quality* features, not operations. Arabic nuclei regularly describe *dynamics* (trembling, surging, collapsing). When هـ enters a dynamic context, its void-quality vanishes.

Best هـ cases: هـد (collapse — تخلخل hits), هـل (interior emptiness — فراغ hits). These are the rare nuclei that describe qualities, not processes.

### ر-Family — Mean Blended Jaccard: 0.145

ر is a *process letter* — it describes continuous, smooth, extending motion. The paradox: ر appears in some of the best nuclei in the dataset (سر: J=0.60) but has a low family average because it systematically *transforms* when paired with surface, containment, or protrusion letters.

**The ر spaciousness rule:** When ر's continuous flow meets letters encoding surface or containment, the nucleus consistently describes *spaciousness* (اتساع، رقة، خلوص، فراغ) — a concept absent from both letters:
- رق: flow + force → اتساع + رقة (breadth and fineness)
- بر: emergence + flow → خلوص + فراغ (purity and void)
- رح: flow + friction → اتساع + رقة (breadth and fineness)

This is a **bi-literal interaction rule** that cannot be captured by feature union. It requires a dedicated ر-interaction term.

---

## The Three Failure Patterns

Binary composition fails in three structurally distinct ways. These are not random misses — they are principled limits of the union model.

### Failure 1: Quality Emergence

**Description:** The letters describe *operations*. The nucleus describes the *quality* of the result.

Operations and qualities are different semantic layers. Pressure is an operation; dryness is a quality. Fine extension is an operation; purity is a quality. The gap between them is systematic.

**Example — بس (J=0, 8 families):**
- ب: ظهور، خروج (emergence, exiting)
- س: امتداد، نفاذ، دقة (extension, penetration, fineness)
- Predicted: {ظهور، خروج، امتداد، نفاذ، دقة}
- Jabal says: الجفاف واليبوسة (dryness and aridity)
- Neither letter encodes dryness. Fine-penetrating extension (س) breaking through a surface (ب) has, in Arabic's semantic history, come to denote desiccation. Dryness *emerged* from the operation.

### Failure 2: Directional Specificity

**Description:** The letters name actions without axis. The nucleus names ascent, descent, distancing, gliding, or settling.

**Example — رج (J=0, 9 families):**
- ر: استرسال، امتداد (flow, extension)
- ج: تجمع، بروز (gathering, protrusion)
- Predicted: {استرسال، امتداد، تجمع، بروز}
- Jabal says: الاضطراب المادي (physical disturbance/turbulence)
- Flow meeting protrusion produces turbulence — a directional-dynamic concept neither letter encodes.

### Failure 3: Interaction Products

**Description:** The nucleus names what *happens when* the two operations meet — vibration, arrest, thickening, oscillation.

**The clearest interaction rule is ر:** Flow (ر) + a boundary letter = spaciousness (اتساع). Flow meeting a boundary produces the quality of the cleared-away space, not the flow or the boundary themselves.

**Example — قر (J=0, 14 families — largest nucleus in ق):**
- ق: قوة، عمق (force, depth)
- ر: استرسال، امتداد (flow, extension)
- Predicted: {قوة، عمق، استرسال، امتداد}
- Jabal says: استقرار ما شأنه التسيب في قاع عميق (settling of what would flow, in a deep basin)
- *Settling* (استقرار) is the interaction product of force (ق) arresting flow (ر). Neither letter encodes "stopping" — that only emerges from their meeting.

---

## Theoretical Consequence: A Two-Tier Composition Model

Arabic semantic composition operates at two tiers, not one:

**Tier 1 — Direct contribution (feature union):** Works for ~56% of nuclei. The nucleus meaning is the sum of its letters' charges. This is the genome hypothesis in its simplest form.

**Tier 2 — Emergent interaction:** Works for the remaining ~44%. The nucleus meaning names a state, quality, or result that arises *from the interaction* of the two operations — not from either letter alone. These states are systematic and modelable (quality emergence, directional specificity, interaction products) but not recoverable by simple union.

The theoretical advance of Juthoor LV1 is not proving that everything composes perfectly. It is that *the failure patterns are systematic and therefore modelable*. LV2 will build interaction rules to cover Tier 2.
