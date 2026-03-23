# S2.4 — Cross-Scholar Comparison Report
**Date:** 2026-03-23
**Analyst:** scorer (Claude Sonnet 4.6)
**Input:** nucleus_score_matrix.json HEAD (4,792 entries, 5 scholars × 4 models)

---

## 1. Overall Scholar Rankings

| Rank | Scholar | Entries | Nonzero Rate | Mean Jaccard | Notes |
|------|---------|---------|--------------|--------------|-------|
| 1 | anbar | 24 | 33.3% | 0.2153 | Small corpus, highly coherent vocabulary |
| 2 | jabal | 1,468 | 27.0% | 0.0695 | Best large-corpus scholar |
| 3 | neili | 216 | 14.8% | 0.0597 | Mid-sized, good precision |
| 4 | asim_al_masri | 1,476 | 12.0% | 0.0554 | Large corpus, moderate match |
| 5 | hassan_abbas | 1,608 | 4.9% | 0.0257 | Weakest alignment with feature vocabulary |

**Winner: Anbar** by Jaccard, but corpus too small (24 entries) for statistical weight.
**Practical winner: Jabal** — best large-corpus scholar at 2.7× the nonzero rate and 2.7× the mean Jaccard of Hassan Abbas.

---

## 2. Per-Scholar × Per-Model Breakdown

| Scholar | dialectical | intersection | phonetic_gestural | sequence |
|---------|-------------|--------------|-------------------|----------|
| anbar | 0.2083 (2/6) | 0.2222 (2/6) | 0.2222 (2/6) | 0.2083 (2/6) |
| asim_al_masri | 0.0576 (51/369) | 0.0551 (41/369) | 0.0549 (41/369) | 0.0540 (44/369) |
| hassan_abbas | 0.0257 (20/402) | 0.0253 (19/402) | 0.0261 (20/402) | 0.0257 (20/402) |
| jabal | **0.0769** (156/367) | 0.0567 (54/367) | 0.0678 (68/367) | **0.0767** (118/367) |
| neili | 0.0577 (9/54) | 0.0633 (7/54) | 0.0602 (7/54) | 0.0577 (9/54) |

**Model rankings (all scholars combined):**
1. dialectical: 0.0536 (19.9% nonzero)
2. sequence: 0.0524 (16.1% nonzero)
3. phonetic_gestural: 0.0503 (11.5% nonzero)
4. intersection: 0.0468 (10.3% nonzero)

**Key observation:** Jabal × dialectical and Jabal × sequence are the highest-performing scholar-model pairs at 0.0769 and 0.0767. Hassan Abbas × intersection is the worst pair (0.0253, 4.7% nonzero).

---

## 3. Phonetic Class Breakdown

### 3a. First-letter phonetic class performance (all scholars combined)

Derived from per-scholar × phonetic-class analysis:

| Phonetic Class | Letters | Jabal Mean J | Jabal Nonzero% | Hassan Abbas Mean J | Asim Mean J |
|---------------|---------|--------------|----------------|---------------------|-------------|
| gutturals | ح,خ,ع,غ,ه | 0.0812 | 32.9% | 0.0172 | 0.0472 |
| sibilants | س,ص,ز,ش | 0.0718 | 28.1% | 0.0319 | 0.0663 |
| emphatics | ق,ك,ط,ظ,ض,ذ,ث | 0.0731 | 25.6% | 0.0399 | 0.0472 |
| liquids | ر,ل,ن | 0.0651 | 27.1% | 0.0310 | 0.0640 |
| labials | ب,م,ف,و | 0.0517 | 21.6% | 0.0074 | 0.0728 |

**Gutturals perform best for Jabal** (0.0812 mean, 32.9% nonzero). This makes theoretical sense: guttural letters (ح,خ,ع,غ,ه) carry strong semantic loading in Arabic root theory — they tend to evoke containment, depth, and intensity, which are well-represented in the atomic feature vocabulary.

**Labials perform worst for Hassan Abbas** (0.0074, 1.5% nonzero) but best for Asim al-Masri (0.0728). This divergence suggests the scholars use fundamentally different vocabulary for labial-rooted nuclei.

### 3b. Best phonetic class pairs (by mean Jaccard across all scholars)

| Pair | n | Mean J | Nonzero% |
|------|---|--------|----------|
| emphatics/emphatics | 140 | 0.0801 | 19.3% |
| labials/sibilants | 144 | 0.0778 | 16.7% |
| sibilants/labials | 168 | 0.0647 | 17.9% |
| gutturals/sibilants | 208 | 0.0670 | 13.9% |
| gutturals/liquids | 184 | 0.0597 | 14.7% |

**Emphatic-emphatic nuclei** (e.g., ضك, ثق, كظ) score highest overall. These roots tend to carry dense, thick, pressure-related meanings that map cleanly onto the scoring vocabulary.

**Labial-sibilant** and **sibilant-labial** pairs also perform well — these nuclei often encode motion and extension semantics that the prediction models capture effectively.

### 3c. Weakest phonetic combinations

| Pair | n | Mean J | Nonzero% |
|------|---|--------|----------|
| liquids/emphatics | 140 | 0.0281 | 10.0% |
| emphatics/gutturals | 148 | 0.0328 | 12.2% |
| gutturals/emphatics | 220 | 0.0328 | 15.0% |

Liquid-first nuclei followed by emphatics are the weakest performers. Liquids (ر,ل,ن) introduce flowing/spreading semantics that don't combine with emphatic thickness/pressure in ways the intersection model captures.

---

## 4. Why Jabal Outperforms Other Scholars

Jabal's superiority has three sources:

**4a. Systematic letter-feature methodology.** Jabal explicitly decomposes nucleus meanings by tracing each letter's articulatory and semantic contribution. This structural approach produces feature vocabulary that closely matches our prediction models' letter-feature framework.

**4b. Consistent vocabulary.** Jabal uses a stable set of Arabic semantic primitives (غلظ, رخاوة, امتداد, نفاذ, etc.) that map well onto the atomic feature set. Hassan Abbas uses a more idiomatic, literary vocabulary that the feature extractor cannot reliably parse.

**4c. Binary-root focus.** Jabal's methodology is explicitly about the two-letter nucleus, not the triliteral root or surface word meaning. This makes his data the most semantically granular and aligned with what our models predict.

**Why Hassan Abbas scores lowest:**
- His vocabulary is literary/semantic rather than articulatory (he describes results, not mechanisms)
- His descriptions are often longer prose that the feature extractor fails to decompose
- He does not consistently assign single-concept meanings per nucleus

---

## 5. Recommendations

1. **Prioritize Jabal data** for scoring calibration, benchmarking, and validation. Jabal × dialectical is the highest-signal pair.
2. **Anbar, despite small corpus, is a strong validator** — 0.2153 mean Jaccard suggests exceptional vocabulary alignment. Expand Anbar coverage if possible.
3. **Neili is undersampled** (216 entries) but shows strong liquid/emphatic performance (0.107 mean for liquids). Worth expanding.
4. **Hassan Abbas data requires feature extraction improvements** before it contributes meaningfully to scoring. His 4.9% nonzero rate is almost certainly a feature-extractor failure, not a true semantic mismatch — his corpus is large and structurally rich.
5. **Emphatic+emphatic root pairs** represent the easiest wins for improving benchmark coverage — high precision, well-defined semantics.
6. **Labials for Asim al-Masri** are his strongest class (0.0728) — good region for targeted evaluation.

---

## 6. Method A Adjustment by Scholar

Based on the calibration in method_a_calibration_v2.md (Jabal baseline: ~40% real accuracy), approximate Method A estimates for other scholars:

| Scholar | Method B Mean | Method A Est. | Rationale |
|---------|---------------|---------------|-----------|
| jabal | 0.0695 | ~40% | Calibrated directly (v2 report) |
| anbar | 0.2153 | ~55-60% | Higher Jaccard floor → higher real accuracy |
| neili | 0.0597 | ~35-40% | Similar to Jabal structure |
| asim_al_masri | 0.0554 | ~30-35% | Vocabulary more diffuse |
| hassan_abbas | 0.0257 | ~20-25% | Feature extraction failure dominates |
