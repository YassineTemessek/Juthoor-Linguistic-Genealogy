# Abbas Sensory Analysis
**Date:** 2026-03-23
**Scope:** S4.1 same-category sensory behavior, S4.2 إيماء vs إيحاء mechanism split, S4.3 verdict
**Reviewer:** Claude Opus 4.6
**Inputs:**
- Abbas letter registry: `Juthoor-ArabicGenome-LV1/data/theory_canon/letters/hassan_abbas_letters.jsonl`
- Nucleus score matrix: `outputs/lv1_scoring/nucleus_score_matrix.json`
- Rows analyzed: 1,484 Hassan Abbas nucleus/model rows with two recoverable Abbas letters

---

## 1. Sensory Category Testing (S4.1)

Abbas sensory categories: `لمسية`, `ذوقية`, `بصرية`, `سمعية`, `شعورية غير حلقية`, `شعورية حلقية`

| Metric | Same-category | Mixed-category |
|--------|--------------|----------------|
| Row count | 280 | 1,204 |
| Mean Jaccard | 0.0234 | 0.0311 |
| Nonzero rate | 8.6% (24/280) | 12.3% (148/1204) |

Two-proportion z-test on nonzero rate: `z = -1.75`, `p ≈ 0.080`

Same-category nuclei do **not** outperform mixed-category. Mixed pairs slightly outperform.

**Why this makes sense:** Jabal's composition model is about semantic tension between letter meanings, not sensory similarity. A nucleus combining taste (ذوقية) with touch (لمسية) creates a richer semantic field. The intersection model finds overlap across different angles, which is where meaning emerges.

**Strongest pair families:**

| Pair | Mean Jaccard | Nonzero Rate |
|------|-------------|--------------|
| `ذوقية + لمسية` | 0.0966 | 43.8% |
| `بصرية + ذوقية` | 0.0569 | 30.4% |
| `بصرية + سمعية` | 0.0542 | 18.8% |

**Weakest pair families:** `شعورية غير حلقية + لمسية` and `شعورية حلقية + شعورية غير حلقية` — both 0.0% nonzero.

Abbas's sensory grouping does not act as a "same type composes better" law. Any real Abbas effect is pair-specific, not category-homogeneous.

---

## 2. إيماء vs إيحاء Testing (S4.2)

Operational mapping: `إيماء` = `ف، ل، م، ث، ذ` (articulatory/imitative layer) | `إيحاء` = all other Abbas letters (dominant expressive layer)

| Pair | Count | Mean Jaccard | Nonzero |
|------|-------|-------------|---------|
| `إيحاء + إيحاء` | 968 | 0.0319 | 122 |
| `إيحاء + إيماء` | 284 | 0.0277 | 29 |
| `إيماء + إيحاء` | 196 | 0.0268 | 21 |
| `إيماء + إيماء` | 36 | 0.0000 | 0 |

Same-mechanism vs mixed-mechanism: `z = 0.98`, `p ≈ 0.329` (not significant).
Pure `إيماء + إيماء` vs all others: `z = -2.20`, `p ≈ 0.028` (significantly worse).

**Why إيماء fails in our system:** Gestural letters have meanings rooted in physical articulation (lip closure, tongue position), but Jabal describes roots with abstract semantic terms (تجمع, نفاذ, etc.). There is a vocabulary mismatch between Abbas's gestural layer and Jabal's semantic layer — this is a failure of current feature extraction, not of Abbas's theory.

---

## 3. Verdict (S4.3)

**Abbas's sensory classification does NOT function as a global scoring prior.** Do not use same-category status to weight or filter predictions.

**But it IS a useful diagnostic lens:**
- Cross-category pairs (especially ذوقية+لمسية) are the strongest composition combinations
- Pure إيماء pairs are reliably weak — flag for manual review rather than trusting mechanical predictions
- Sensory categories may become more predictive after the scoring reforms (S3.14–S3.16) reduce noise

**Summary table:**

| Test | Result | p-value |
|------|--------|---------|
| Same-category vs mixed nuclei | Mixed outperforms same (0.031 vs 0.023 mean J) | p≈0.080 |
| إيماء+إيماء vs all others | 0/36 nonzero — significantly worse | p≈0.028 |
| Same-mechanism vs mixed-mechanism | No significant difference | p≈0.329 |
| Best pair family | ذوقية+لمسية (taste+touch): 43.8% nonzero | — |

**Concrete recommendations:**
1. Do NOT add Abbas categories to the scoring pipeline — no evidence they improve predictions
2. Do add a diagnostic flag for إيماء+إيماء pairs in root predictions — these need manual semantic review
3. Re-run S4.1–S4.2 after S3.17 — improved scoring may change the picture
4. Park Sprint 4 findings as "not yet validated" — revisit after Sprint 5 (cross-lingual)

**Status: Sprint 4 COMPLETE (parked as "not yet validated")**

---

## 4. Mechanism Routing Test

See `outputs/lv1_scoring/research_documents/abbas_mechanism_routing_test.md` for the follow-on S4.3 mechanism routing experiment, which tests whether Abbas's إيماء/إيحاء split predicts routing to different scoring mechanisms (intersection vs union vs weighted).
