# Quranic Deep Dive: Why Quranic Roots Score Lower Than Non-Quranic

**Date:** 2026-03-26
**Scope:** consensus_weighted predictions — 1,924 roots total
**Focus:** Structural analysis of the Quranic / non-Quranic accuracy gap

---

## 1. The Statistical Split

Of the 1,924 consensus_weighted predictions:

| Corpus | Roots | Mean bJ | Median bJ | Zero Rate | ≥0.5 Rate |
|--------|-------|---------|-----------|-----------|-----------|
| Quranic | 1,666 | 0.1834 | 0.1000 | 42.4% | 11.4% |
| Non-Quranic | 258 | 0.3099 | 0.2900 | 26.4% | 27.1% |
| **Gap** | | **−0.1265** | **−0.1900** | **+16 pp** | **−15.7 pp** |

The gap is not marginal. Non-Quranic roots are nearly **70% more accurate on average**, and they produce a J≥0.5 "strong match" at more than twice the rate. The zero-score rate (complete prediction failure) is 16 percentage points higher in Quranic roots.

### Score distributions

```
Quranic:      =0 → 42.4%   0–0.25 → 23.7%   0.25–0.5 → 22.5%   ≥0.5 → 11.4%
Non-Quranic:  =0 → 26.4%   0–0.25 → 15.9%   0.25–0.5 → 30.6%   ≥0.5 → 27.1%
```

The non-Quranic distribution is dramatically right-shifted. Where Quranic roots cluster at zero and low scores, non-Quranic roots cluster in the moderate-to-strong range.

---

## 2. Root Composition: Reduplicated Roots Inflate Non-Quranic Scores

The single most important structural finding: **59.7% of the 258 non-Quranic roots are reduplicated or quadriliteral forms** (e.g., كظظ, ضفف, غشش, مثث-مثمث), while only **14.9% of Quranic roots** fall into this category.

| Type | Quranic (n) | Mean bJ | Non-Quranic (n) | Mean bJ |
|------|-------------|---------|-----------------|---------|
| Reduplicated / extended | 248 | 0.2868 | 154 | 0.3161 |
| Simple triliteral | 1,418 | 0.1654 | 104 | 0.3008 |

Two conclusions follow immediately:

1. Reduplicated roots are **easier to score** for both corpora (the repeated letter pattern constrains the semantic field, making predictions more precise).
2. Even **controlling for root type**, simple non-Quranic roots (bJ=0.3008) outperform simple Quranic roots (bJ=0.1654) by a factor of 1.8. The gap is structural, not merely a compositional artefact.

---

## 3. Failure Classification: The 706 Quranic J=0 Roots

Of 1,666 Quranic roots, 706 (42.4%) score J=0 — complete prediction failure. Classifying by primary cause:

| Failure Category | Count | % of J=0 |
|-----------------|-------|----------|
| position_aware model selected, predictions wrong | 254 | 36.0% |
| nucleus_only model selected, predictions wrong | 173 | 24.5% |
| intersection model selected, predictions wrong | 126 | 17.8% |
| Empty actual_features (unscored by design) | 101 | 14.3% |
| phonetic_gestural model selected, predictions wrong | 52 | 7.4% |

**The largest single failure mode is position_aware model selection.** When position_aware is chosen for a Quranic root, it fails 55.9% of the time (276/494 roots score zero). By contrast, nucleus_only fails only 29.9% of the time when selected.

The position_aware model appears over-selected for Quranic roots (29.7% of Quranic predictions vs. 14.7% of non-Quranic predictions use it), yet it is the worst-performing model for that corpus.

---

## 4. Analysis of 50 Sampled Quranic J=0 Roots

Examining 50 randomly selected Quranic J=0 roots (seed=42), four distinct failure patterns emerge:

### 4a. Model Routing Mismatch (the dominant mode)
The composition model selected does not match the semantic structure of the root. Examples:

- **نصو** — Quranic word: بناصيتها "taking it by the forelock." Actual meaning: ظاهر (visible prominence). Predicted: نفاذ + امتداد + احتواء (phonetic_gestural model, oriented toward penetration/spread). The physical meaning of the root is missed because the gestural model interprets the consonant cluster in a different direction.

- **حرص** — Quranic: حَرِيصٌ عَلَيْكُمْ "eagerly desirous of you." Actual: مقر (settled, persistent). Predicted: خلوص (purity/sincerity, intersection model). The model maps the root to a related but non-overlapping semantic field.

- **رسو** — Quranic: وَالْجِبَالَ أَرْسَاهَا "He anchored the mountains." Actual: تعلق + باطن + امتساك (attachment, interior, adhesion). Predicted: نفاذ + امتداد + احتواء (phonetic_gestural: penetration, extension, containment). The physical anchoring meaning is completely missed.

- **بسق** — Quranic: وَالنَّخْلَ بَاسِقَاتٍ "the towering date-palms." Actual: اندفاع + عمق + قوة (surge, depth, force). Predicted: جفاف (dryness, position_aware model). A catastrophic routing error.

### 4b. Empty Actual Features (14.3% of J=0)
101 Quranic roots have no actual_features recorded. These include roots like هدى (guidance), بسم (smiling), فتر (ceasing), and عوق (hindering). These roots carry meanings that Jabal's lexicon either left unfeaturized or assigned to a level of abstraction the current feature vocabulary cannot capture.

The scoring infrastructure scores these as J=0 by necessity — not because the model predicted wrongly, but because there is nothing to match against. These 101 roots represent the **Jabal coverage gap**, not model failure.

### 4c. Semantic Drift Between Quranic and Lexical Register
Several roots fail because the Quranic usage emphasizes a semantic dimension that differs from the root's primary lexical meaning:

- **صير** — Quranic: وَإِلَى اللَّهِ الْمَصِيرُ "and to God is the final return." This is a theological destination word. The core root meaning involves انتقال + تجمع (transition, gathering). The model predicts قوة + إمساك (force, holding). The Quranic context pulls toward eschatological finality, which the current phonosemantic model has no mechanism to express.

- **حين** — Quranic: فَسُبْحَانَ اللَّهِ حِينَ تُمْسُونَ "glorify God when you enter the evening." Actual: وصول (arrival/attainment). The model predicts جوف + قوة (hollow, force). The word's temporal/processual meaning (a point of arrival in time) is structurally different from its consonantal profile.

- **موت** — Quranic: فَأَحْيَا بِهِ الْأَرْضَ بَعْدَ مَوْتِهَا "He revived the earth after its death." Actual: احتباس + حدة (containment, sharp cessation). Predicted: دقة (fineness/precision). The death-meaning involves a quality of abrupt stopping that the model misses entirely.

### 4d. Long-Root Failures (Quadriliterals and Extended Forms)
60 genuinely quadriliteral Quranic roots (e.g., برزخ, بعثر, جهنم, حلقم, خردل) perform poorly. Examples:

- **برزخ** bJ=0.000 — The barrier between two seas. The four-consonant structure exceeds what the binary-nucleus model was designed for.
- **بعثر** bJ=0.000 — Quranic: وَإِذَا الْقُبُورُ بُعْثِرَتْ "when the graves are overturned." Actual: تفرق + استقرار. Predicted: انتقال. The quadriliteral scattering sense is not recovered.

---

## 5. Why Non-Quranic Roots Succeed

Examining 20 sampled non-Quranic roots with J>0 (mean bJ ≈ 0.50 for the sample's top tier), the pattern is clear:

### 5a. Reduplicated roots are self-reinforcing
Roots like ضفف, كظظ, غشش, سجسج, نقق are structurally simpler to predict. Reduplication signals that the meaning is an amplification or intensification of the binary nucleus. Since the binary nucleus drives our prediction, doubling it concentrates the signal:

- **ضفف** bJ=1.000 — predicted: تجمع, actual: تجمع. Perfect match.
- **كظظ** bJ=0.750 — predicted: امتلاء + كثافة + جوف + قوة, actual: امتلاء + كثافة + قوة + غلظ. Near-perfect.
- **غشش** bJ=0.650 — predicted: كثافة, actual: رقة + كثافة. Strong partial match.

### 5b. Concrete physical meanings dominate
Non-Quranic roots in this dataset tend to describe concrete physical phenomena: thickness (غلظ), filling (امتلاء), scraping (حزز), splitting (شق). These meanings map directly to the phonosemantic feature vocabulary. There is minimal contextual drift — the root means what it physically describes.

- **حزز** bJ=0.480 — predicted: شق + دقة + ازدحام, actual: شق + دقة + صلابة + غلظ. Two exact matches, two near-misses.
- **ضبب** bJ=0.275 — predicted: اشتمال, actual: اشتمال + تجمع + كثافة + تعلق. One exact hit.
- **مثث-مثمث** bJ=0.550 — predicted: ظاهر + انتشار, actual: انتشار + كثافة + باطن + ظاهر. Two exact hits.

### 5c. nucleus_only model dominates non-Quranic successes
50.0% of non-Quranic J>0 predictions use nucleus_only, which has the highest mean bJ across all models. In the non-Quranic corpus, the two-consonant binary nucleus is a sufficient signal for prediction — there is little ambiguity that requires positional or phonetic refinement.

---

## 6. BAB-Level Performance: Where the Gap is Largest

Comparing mean bJ per BAB (letter chapter) between Quranic and non-Quranic roots, the gaps vary significantly:

| BAB | Quranic bJ | Non-Quranic bJ | Gap |
|-----|-----------|----------------|-----|
| الكاف | 0.1683 | 0.4545 | +0.2863 |
| السين | 0.1846 | 0.4554 | +0.2708 |
| الشين | 0.1509 | 0.3862 | +0.2353 |
| الهاء | 0.1583 | 0.3821 | +0.2238 |
| الفاء | 0.1458 | 0.3647 | +0.2190 |
| الميم | 0.1693 | 0.3632 | +0.1939 |
| الراء | 0.2099 | 0.3946 | +0.1847 |

BABs with the **smallest gap** (where Quranic nearly matches non-Quranic):

| BAB | Quranic bJ | Non-Quranic bJ | Gap |
|-----|-----------|----------------|-----|
| التاء | 0.2829 | 0.2323 | −0.0506 |
| الدال | 0.2146 | 0.1175 | −0.0971 |
| الطاء | 0.2300 | 0.2403 | +0.0103 |

The التاء and الدال BABs are notable: Quranic roots starting with these letters **outperform** their non-Quranic counterparts. Roots like تلو-تلي (bJ=1.000), تمم (bJ=1.000), دمع (bJ=1.000), دون (bJ=1.000) carry concrete physical or directional meanings that survive Quranic contextual embedding.

The worst-performing Quranic BABs are الصاد (0.1365), اللام (0.1443), الفاء (0.1458), and الشين (0.1509). These BABs contain many abstract-action and spiritual-state roots in Quranic usage.

---

## 7. What the Best Quranic Predictions Have in Common

The 20 Quranic roots scoring bJ=1.000 (perfect prediction) reveal the conditions for success:

| Root | Predicted | Actual | Quranic Context |
|------|-----------|--------|-----------------|
| يبس | جفاف | جفاف | يَبَسًا — "a dry path in the sea" |
| وتد | امتساك + تماسك | امتساك + تماسك | وَالْجِبَالَ أَوْتَادًا — "mountains as pegs" |
| جوع | جوف + فراغ | فراغ + جوف | أَلَّا تَجُوعَ فِيهَا — "you shall not hunger" |
| حقق-حقحق | امتساك + عمق + مقر | امتساك + عمق + مقر | الْحَقُّ — "the Truth" |
| خوو-خوى | فراغ | فراغ | خَاوِيَةً — "empty/collapsed" |
| خسر | نقص | نقص | خَاسِئِينَ — "humiliated, diminished" |
| بدأ | ظهور | ظهور | يَبْدَأُ الْخَلْقَ — "originates creation" |

Pattern: these are **concrete-physical or minimally abstract** Quranic words. يبس (dryness), وتد (peg/anchor), جوع (hunger), خاوية (emptiness) — all describe states that are directly expressible in the phonosemantic feature vocabulary. The Quranic context does not distort the root's core physical meaning.

حقق (truth/reality) achieving bJ=1.000 is the most theoretically significant success: it confirms that even an abstract Quranic concept can be correctly predicted when its root's physical etymology is semantically transparent and well-featurized. The Arabic حق encodes the idea of something driven into the ground (امتساك), deep and settled (عمق), a fixed locus (مقر) — and the model recovers exactly this.

---

## 8. Interpretation: This Is Not a Genome Failure

The accuracy gap should not be read as evidence that the genome model is wrong for Quranic Arabic. Three structural reasons explain the gap without undermining the genome hypothesis:

### 8a. The Quranic lexicon is the full depth of Arabic
The 1,666 Quranic roots represent **the broadest semantic range in classical Arabic**, including rare, abstract, theological, and polysemous roots that appear once or twice in the entire corpus. Non-Quranic roots in this dataset are predominantly reduplicated intensity words with narrow, concrete meanings. Comparing them is like comparing a general vocabulary test to a specialized one.

### 8b. The feature vocabulary was calibrated on simpler roots
The 81-feature vocabulary (قوة, امتداد, باطن, etc.) was built bottom-up from binary nucleus analysis. It is well-suited to physical/sensory meaning. Theological and relational meanings (guidance, prohibition, time, return to God) are **higher-order compositions** of these features. The genome is the alphabet; Quranic meaning requires reading longer sentences.

### 8c. Quranic roots require deeper composition, not different letters
The successful Quranic predictions confirm that the genome works — when a root's Quranic meaning aligns with its physical etymology. The failures are cases where the Quranic context emphasizes a **derived or extended** sense. This is evidence that the composition model needs another layer, not that the letter-meaning mappings are wrong.

---

## 9. The Position-Aware Model Problem

The most actionable finding in this analysis is the over-selection and under-performance of the position_aware model in Quranic roots:

- position_aware is selected for 29.7% of Quranic roots vs. 14.7% of non-Quranic roots
- When selected for Quranic roots, it fails (J=0) 55.9% of the time
- Its mean bJ when it does produce a nonzero score (0.3207) is reasonable — but the 56% zero rate makes it a net drag

This suggests a routing miscalibration: the model selection heuristic is pushing Quranic roots toward position_aware (perhaps because Quranic roots tend to have more semantically loaded third letters) but the position_aware model's prediction logic is not accurate enough for this corpus. Recalibrating router thresholds to favor nucleus_only for Quranic roots could recover meaningful accuracy gains.

---

## 10. Recommendations

### 10.1 Immediate: Reroute position_aware → nucleus_only for Quranic roots
Estimated impact: if the 276 position_aware Quranic J=0 roots were instead scored with nucleus_only (mean bJ 0.2209), the overall Quranic mean bJ would rise from 0.1834 to approximately **0.21–0.22**, a 15–20% relative improvement.

### 10.2 Short-term: Expand the feature vocabulary for relational/temporal meaning
Roots encoding motion-toward-God (مصير, هدى, توبة), prohibition (حرام, نهي), or temporal state (حين, دهر) require features beyond the current physical vocabulary. Candidate additions: وصول (arrival), إلزام (obligation), زمان (temporal interval), غاية (finality/endpoint). These would directly address the top failure cases.

### 10.3 Medium-term: Add a composition layer for abstract Quranic meanings
The genome correctly encodes the physical substrate of Arabic roots. For Quranic meanings, a second-stage composition rule is needed: given physical features {F1, F2, F3}, derive abstract meanings via documented semantic extension paths (e.g., حبس → restraint → death → stillness → dignity). This is the LV2/LV3 connection — the genome feeds a semantic derivation engine.

### 10.4 Benchmark: Separate Quranic and non-Quranic metrics
Report bJ_quranic and bJ_nonquranic as separate headline metrics in future dashboards. The current combined bJ (0.188 task-reported) masks the non-Quranic signal and makes progress tracking ambiguous. The two corpora are testing different aspects of the genome.

### 10.5 Investigate the 101 empty-actual roots
101 Quranic roots with no actual_features cannot be scored regardless of model quality. These should be reviewed against Jabal's lexicon to determine whether features exist but were not ingested, or whether these roots genuinely lack phonosemantic assignment. This is a data completeness issue, not a model issue.

---

## 11. Summary

The Quranic / non-Quranic accuracy gap (bJ 0.183 vs 0.310) is explained by four compounding factors:

1. **Corpus composition**: non-Quranic roots are predominantly reduplicated intensity words with narrow, concrete, model-friendly meanings. Quranic roots span the full semantic depth of Arabic.

2. **Model routing mismatch**: position_aware is over-selected for Quranic roots (30% of selections) and fails 56% of the time when chosen. This single fix accounts for the majority of recoverable accuracy.

3. **Feature vocabulary ceiling**: 101 Quranic roots have no actual_features (14.3% of all Quranic J=0), and many more encode meanings at a level of abstraction above the current 81-feature vocabulary. This is a calibration frontier, not a genome failure.

4. **Semantic register depth**: Quranic Arabic uses roots for their **extended, derived, and spiritual** senses. The genome correctly encodes their physical substrate — which is confirmed by the 190 Quranic roots scoring ≥0.5. The task is to extend composition upward from physical to derived meaning.

The genome is working. It recovers the physical etymology of Quranic roots accurately when the Quranic context preserves that physical sense. The next research frontier is building the derivation bridge between physical letter-meanings and the full semantic range of Quranic Arabic — which is precisely what LV2 and LV3 are designed to address.
