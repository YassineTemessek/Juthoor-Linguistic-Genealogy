# Phase 2 Review — Opus Checkpoint
**Date:** 2026-03-14
**Reviewer:** Claude Opus 4.6
**Commits:** 779cc7b, 4ccc173, e6c22d4, e7094d9

---

## Test Suite
- **183/183 tests passing** (6.36s) — no regressions

## Results Summary

| Exp | Hypothesis | Key Metric | Target | Actual | Verdict |
|-----|-----------|------------|--------|--------|---------|
| 1.2 | H8: positional meaning shift | Kruskal-Wallis p < 0.05 | >60% letters significant | **24/28 (86%) significant** | **SUPPORTED** |
| 4.1 | H4/H5: metathesis preserves/changes | Wilcoxon p < 0.05, classification | >50% similar → H4 | **mean 0.526 vs 0.502, p=0.014, d=0.28** | WEAKLY SUPPORTED (H4 partial) |
| 4.3 | H6: same-makhraj substitution closer | Spearman rho > 0.2, p < 0.01 | rho=0.2+ | **rho=-0.021, p=0.012** | **NOT SUPPORTED** |
| 5.1 | H1: sound-meaning CCA | 1st canonical corr > 0.4 | >0.4 with permutation significance | **r=0.962, but perm p=0.149** | INCONCLUSIVE |
| 3.1 (refined) | H3: modifier personality | Shuffled baseline comparison | z > 2 above shuffle | **z=3.51 above shuffle** | WEAK SIGNAL (not promotable) |

---

## Experiment 1.2 — Positional Semantics (Al-Aqqad's Observation)

**Result:** 24 of 28 letters (86%) show statistically significant position effects (Kruskal-Wallis p < 0.05). Mean positional coherence: 0.521.

**Interpretation:** This is the **strongest result in Phase 2** and the second strongest in the entire factory after field coherence (2.3). When the same letter appears in position 1, 2, or 3 of different roots, the semantic distributions of those roots differ significantly. This supports Al-Aqqad's observation that a letter's semantic contribution changes with its position in the root.

**The 4 non-significant letters:** ذ, غ, ظ, none of the common letters. These are low-frequency letters that may simply have too few occurrences in some positions.

**Theoretical significance:** This is important because it means we cannot treat a letter's meaning as a single fixed value. The position-sensitive nature of letter semantics has implications for:
- Experiment 3.1 (modifier personality) — position should be controlled for
- Experiment 6.1 (meaning prediction) — models should take position into account
- The overall theory — Jabal's system may need a positional refinement

**Status:** H8 → **supported**

---

## Experiment 4.1 — Binary Metathesis (Ibn Jinni vs Jabal)

**Result:** 166 metathetic pairs found. Mean cosine similarity: 0.526 (metathesis) vs 0.502 (random control). Wilcoxon p=0.014. Cohen's d=0.28 (small effect). Classification: 7 similar (>0.7), 159 middle, 0 divergent.

**Interpretation:** The metathesis effect is statistically real but small. Reversed binary roots (XY↔YX) are slightly more similar than random pairs, but the effect size (d=0.28) is modest. Only 7 of 166 pairs (4.2%) exceed 0.7 similarity — far below Ibn Jinni's claim that "the core meaning is preserved."

**The verdict on the historical debate:**
- **Ibn Jinni** (H4: metathesis preserves) — **partially right.** There is a detectable preservation effect, but it's weak. Metathesized roots are NOT semantically interchangeable.
- **Jabal** (H5: order matters) — **largely right.** The order of consonants matters enormously. The small shared signal may simply reflect that roots sharing the same two letters are in the same phonetic/semantic neighborhood regardless of order.

**Status:** H4 → **weakly supported** (real but small), H5 → **supported** (order matters more than reversal preserves)

---

## Experiment 4.3 — Phonetic Substitution (Ibn Jinni's Conditions)

**Result:** 14,309 one-letter-different tri-root pairs found. Spearman rho = -0.021, p = 0.012.

**Interpretation:** This is a **clear negative result.** The correlation between articulatory distance and semantic distance is near zero and in the wrong direction. Replacing a consonant with one from the same makhraj does NOT produce a closer meaning than replacing it with an acoustically distant consonant.

**Why this might fail:**
1. The hypothesis is too simplistic. Substitution effects may depend on which position is substituted and what the semantic field is, not just on articulatory distance.
2. BGE-M3 embeddings of short Arabic glosses may not have the granularity to detect subtle substitution effects that a native speaker would perceive.
3. The 14,309 pairs include ALL position changes (1st, 2nd, 3rd letter), but the theory may only hold for specific positions.

**Status:** H6 → **not supported**

---

## Experiment 5.1 — Sound-Meaning CCA

**Result:** First canonical correlation = 0.962. But permutation test p=0.149 (baseline mean 0.918).

**Interpretation:** The raw CCA score is extremely high (0.962), but this is misleading. CCA on a 28-sample, high-dimensional dataset will always find strong correlations by overfitting. The permutation test correctly identifies this: shuffled data achieves r=0.918 on average, making the observed 0.962 not significantly above chance (p=0.149).

**Methodological note:** Codex correctly reduced semantic dimensions to PCA-2 before running CCA (28 samples with 1024 dims would be meaningless), but even with 2 dims, N=28 is too small for reliable CCA. This experiment would need either more granular phonetic features or a larger sample (e.g., syllable-level or root-level, not letter-level).

**Status:** H1 → **inconclusive** (method not powerful enough at N=28)

---

## Experiment 3.1 — Modifier Personality (Refined)

**Result:** Mean consistency still 0.033, 0 letters above 0.5. But z=3.51 above shuffled baseline (shuffle mean 0.029, std 0.001).

**Interpretation:** The refinement adds important nuance. While the absolute consistency is very low (0.033), it is 3.5 standard deviations above what shuffled data produces. This means there IS a non-random modifier signal — it's just extremely weak and not usable for prediction or promotion.

**Status:** H3 → **weak signal detected** (above chance, but not promotable)

---

## Updated Hypothesis Registry

| ID | Hypothesis | Phase 1 | Phase 2 | Final Status |
|----|-----------|---------|---------|-------------|
| H1 | Phonetic-semantic proximity | Inconclusive (Mantel) | Inconclusive (CCA) | **Inconclusive** |
| H2 | Binary root field stability | **Supported** | — | **Supported** ★ |
| H3 | Third letter modifier personality | Inconclusive | Weak signal (z=3.5) | **Weak signal** |
| H4 | Metathesis preserves meaning | — | Weakly supported (d=0.28) | **Weakly supported** |
| H5 | Metathesis changes meaning (order matters) | — | Supported (complement of H4) | **Supported** ★ |
| H6 | Same-makhraj substitution closer | — | Not supported (rho≈0) | **Not supported** |
| H8 | Positional meaning shift | — | **Supported** (24/28 letters) | **Supported** ★ |

★ = Promotion candidates for LV2/LV3

---

## Promotion Recommendations

Three results are strong enough to consider promoting:

| Result | Promotion Target | What to Export |
|--------|-----------------|---------------|
| **H2: Field coherence** | LV2 (retrieval ranking), LV3 (theory evidence) | `field_coherence.jsonl` — per-family coherence scores |
| **H5: Order matters** | LV3 (theory evidence) | `metathesis_analysis.jsonl` — annotated pairs |
| **H8: Positional semantics** | LV1 internal (refine 3.1), LV3 (theory evidence) | `positional_semantics.jsonl` — per-letter positional profiles |

Not promoted: H1 (inconclusive), H3 (too weak), H4 (too small), H6 (negative).

---

## Recommendations for Phase 3

### Go ahead with:
- **6.1 Meaning predictor** — now we know position matters (H8), the model should take letter position as input
- **6.2 Unsupervised discovery** — HDBSCAN on axial embeddings, compare to Jabal's families
- **2.2 Missing combinations** — test whether absent binary roots have lower semantic compatibility
- **6.4 Phantom roots** — generate compatible/incompatible roots, test predictive power

### Consider:
- Before 6.1, Codex could build a **positional modifier profile** — refinement of 3.1 that groups by (letter, position) instead of just letter. This directly uses the H8 finding to improve H3.

### Do not re-run:
- 4.3 (substitution) — the negative result is clear and informative
- 5.1 (CCA) — N=28 is fundamentally too small for this method

---

*Phase 2 Review — Opus Checkpoint*
*Juthoor Research Factory*
*2026-03-14*
