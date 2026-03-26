# S4.3 — Abbas Sensory Validation Verdict
**Date:** 2026-03-23
**Reviewer:** Claude Opus 4.6
**Input:** `outputs/lv1_scoring/abbas_sensory_validation.md` (Codex S4.1+S4.2)

---

## Summary of Codex's Findings

| Test | Result | p-value |
|------|--------|---------|
| Same-category vs mixed nuclei | Mixed **outperforms** same (0.031 vs 0.023 mean J) | p≈0.080 |
| إيماء+إيماء vs all others | 0/36 nonzero — significantly worse | p≈0.028 |
| Same-mechanism vs mixed-mechanism | No significant difference | p≈0.329 |
| Best pair family | ذوقية+لمسية (taste+touch): 43.8% nonzero | — |

---

## Interpretation

### 1. Abbas's Categories Are Not a Composition Law

The hypothesis was: letters from the same sensory category should compose better because they share a perceptual substrate. The data says the opposite — mixed-category pairs slightly outperform same-category pairs.

**Why this makes sense in Jabal's framework:** Jabal's composition model is about *semantic tension* between letter meanings, not sensory similarity. A nucleus combining taste (ذوقية) with touch (لمسية) creates a richer semantic field than taste+taste. The intersection model finds overlap across *different* angles, which is where meaning emerges.

### 2. The إيماء Failure Is Informative

Abbas's إيماء (gestural/imitative) letters (ف، ل، م، ث، ذ) scored 0/36 when paired together. These are the letters Abbas considers most directly physical/articulatory — their meaning comes from mouth gesture, not abstract expression.

**Why this fails in our system:** Our scoring compares Jabal's *semantic* feature vocabulary against predicted compositions. Gestural letters have meanings rooted in physical articulation (lip closure, tongue position), but Jabal describes roots with abstract semantic terms (تجمع, نفاذ, etc.). There's a vocabulary mismatch between Abbas's gestural layer and Jabal's semantic layer.

This is not a failure of Abbas's theory — it's a failure of our current feature extraction to bridge the gap between physical gesture and semantic abstraction.

### 3. Specific Cross-Category Pairs Are Valuable

The ذوقية+لمسية pair (43.8% nonzero, mean J 0.097) is by far the strongest. This suggests that certain *specific* sensory combinations have predictive power, even though the broad same-vs-mixed category distinction doesn't.

This is consistent with Abbas's own nuanced view: he doesn't claim all categories compose equally. He identifies specific interaction patterns between sensory families.

---

## Verdict

**Abbas's sensory classification does NOT function as a global scoring prior.** We should not use same-category status to weight or filter predictions.

**But it IS a useful diagnostic lens:**
- Cross-category pairs (especially ذوقية+لمسية) are the strongest composition combinations
- Pure إيماء pairs are reliably weak — flag them for manual review rather than trusting mechanical predictions
- The sensory categories may become more predictive *after* the scoring reforms (S3.14-S3.16) reduce noise

**Concrete recommendations:**
1. **Do NOT add Abbas categories to the scoring pipeline** — no evidence they improve predictions
2. **Do add a diagnostic flag** for إيماء+إيماء pairs in root predictions — these need manual semantic review
3. **Re-run S4.1-S4.2 after S3.17** — the improved scoring may change the picture, especially with category-level blended_jaccard which directly addresses the vocabulary gap
4. **Park Sprint 4 findings** as "not yet validated" — revisit after Sprint 5 (cross-lingual) to see if Abbas categories predict better across languages where gestural features may map more directly

---

## Status: Sprint 4 COMPLETE (parked as "not yet validated")
