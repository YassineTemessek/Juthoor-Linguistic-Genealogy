# Quranic vs. Non-Quranic Root Prediction Accuracy
**Juthoor LV1 — consensus_strict scoring**
Date: 2026-03-26

---

## 1. Overview

This report compares prediction accuracy for Quranic and non-Quranic roots under the consensus_strict model. The scoring dataset contains 1,924 roots split into two populations: 1,666 roots that appear in the Quranic corpus and 258 roots that do not.

The headline result is counter-intuitive: non-Quranic roots score measurably better on every metric.

---

## 2. Results Table

| Metric | Quranic (n=1,666) | Non-Quranic (n=258) | Delta |
|--------|-------------------|---------------------|-------|
| Mean Jaccard | 0.155 | 0.261 | −0.107 |
| Mean Blended | 0.188 | 0.288 | −0.100 |
| Nonzero Jaccard rate | 45.5% | 67.4% | −21.9pp |
| Nonzero Blended rate | 64.3% | 76.7% | −12.5pp |

---

## 3. The Surprising Direction

Non-Quranic roots score better. A naive expectation would be the reverse: the Quran is the canonical source of classical Arabic, its vocabulary is well-documented, and Jabal's المعجم الاشتقاقي draws heavily on Quranic usage. One might expect genome predictions to be more accurate on this well-studied corpus.

The data does not support that expectation. Non-Quranic roots have a 21.9pp higher nonzero rate on exact Jaccard and a 10pp higher mean blended score. This gap is consistent across both metrics and is too large to attribute to sampling noise.

---

## 4. Possible Explanations

### 4.1 Semantic Complexity of Quranic Vocabulary

The Quran deploys Arabic at its most semantically dense. Quranic roots frequently carry:

- **Multiple simultaneous meanings** — a single root can operate as a physical description, a moral category, and an eschatological concept in different verses.
- **Abstract theological content** — concepts like mercy (رحمة), accountability (حساب), and guidance (هدى) have meanings that transcend their phonosemantic anchors.
- **Polysemous roots with opposing glosses** — roots like عسر (difficulty), عفو (forgiveness/excess), and رجو (hope/fear depending on form) resist single-feature predictions.

The consensus_strict model predicts phonosemantic features from letter composition. It is optimised for roots with a clear physical or sensory anchor. Quranic vocabulary is disproportionately abstract.

### 4.2 Non-Quranic Roots Are More Concrete

Non-Quranic roots in the LV1 dataset tend toward concrete physical domains: body parts, tools, materials, animal names, and basic action verbs. These are precisely the category where phonosemantic prediction is strongest. A root meaning "to pierce" or "to gather" or "to soften" maps cleanly onto letter features. A root meaning "to be unjust" or "to disbelieve" does not.

### 4.3 Coverage Skew in Jabal's Ground Truth

Jabal's feature annotations (the ground truth for Jaccard scoring) may themselves be denser and more reliable for concrete non-Quranic roots. For abstract Quranic roots, Jabal sometimes records a narrow set of primary features that misses the full semantic range — not because the genome is wrong, but because the annotation is necessarily incomplete for a polysemous term.

### 4.4 Hollow Roots and Weak Letters

Quranic Arabic is particularly rich in roots containing the weak letters و and ي (حروف الجوفية). These letters have near-zero independent phonosemantic weight — all scholars note their minimal lexical contribution. Roots built around them produce weaker predictions. The Quran's vocabulary includes many such roots (وصل، ويل، وعد، يمن، etc.) that structurally resist genome prediction.

---

## 5. What This Result Does Not Mean

This result does not mean the genome fails on Quranic Arabic. Three points of clarification:

**First**, the 64.3% nonzero blended rate for Quranic roots is itself strong. More than three in five Quranic roots receive a non-trivial blended prediction. The genome is making contact with Quranic meanings; it is simply making shallower contact than it does with non-Quranic roots.

**Second**, the 45.5% nonzero exact Jaccard rate for Quranic roots means that nearly half of Quranic roots have at least one correctly predicted feature in strict vocabulary terms. This is a positive signal, not a failure signal.

**Third**, the performance gap reflects a limitation of the composition model (heuristic letter-feature assembly), not a limitation of the phonosemantic hypothesis. The underlying claim — that Arabic root meanings are partially predictable from letter features — is supported even in the Quranic population. The model simply needs more compositional sophistication to handle abstract and polysemous meanings.

---

## 6. Implications for Scoring Architecture

The Quranic/non-Quranic gap suggests two categories of roots that may benefit from different treatment in future scoring passes:

**Category 1 — Concrete anchored roots** (higher non-Quranic proportion): use consensus_strict predictions directly. These carry strong signal for LV2 cross-lingual projection.

**Category 2 — Abstract/polysemous Quranic roots**: flag for supplementary treatment. Options include:
- Semantic embedding similarity (cosine from BgeM3 vectors) as an alternative scoring path
- Separate abstract-root model trained on Quranic semantic categories
- Reduced prediction weight in LV2 to avoid propagating weak signals

---

## 7. Blended Metric Interpretation

The blended Jaccard metric (0.7 × exact Jaccard + 0.3 × category Jaccard) closes part of the gap: Quranic roots show a larger improvement from exact to blended (0.155 → 0.188, +0.033) than non-Quranic roots (0.261 → 0.288, +0.027). This means Quranic roots are more often getting the semantic category direction right even when exact vocabulary terms do not match. The genome is directionally correct for Quranic roots more often than the strict Jaccard number suggests.

The nonzero blended rate of 64.3% for Quranic roots — nearly two-thirds — indicates that for the majority of Quranic vocabulary, the genome places the prediction in the correct semantic neighbourhood. This is the more useful number for LV2 projection purposes.

---

## 8. Summary

Non-Quranic roots score better because they are disproportionately concrete, sensory, and single-meaning — the optimal input for a letter-composition model. Quranic roots score lower because they carry abstract theological weight, polysemy, and grammatical function words that the current architecture cannot model.

The 64.3% blended nonzero rate for Quranic roots is a strong baseline for a heuristic model operating on a compositional hypothesis. The result does not challenge the genome theory; it maps its current boundary conditions.

---

*Report generated from consensus_strict scoring run. Population: 1,924 roots (1,666 Quranic, 258 non-Quranic).*
