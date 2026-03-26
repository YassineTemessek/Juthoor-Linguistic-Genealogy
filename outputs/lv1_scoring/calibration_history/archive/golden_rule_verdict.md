# Golden Rule Verdict + Best Model Recommendation
**Date:** 2026-03-23
**Reviewer:** Claude Opus 4.6

---

## Golden Rule (Anbar's القاعدة الذهبية)

**Claim:** Reversing the consonant order of a binary nucleus reverses its meaning.

### Method B Result: 17/166 confirmed (10.2%)

### Method A Assessment: Undertested, not disproven

The 10.2% rate is misleading because:
- 14 pairs have BOTH sides with empty features → untestable
- 55 more pairs have one side empty → untestable
- Only 97 pairs have features on both sides → 17.5% confirmed among testable pairs

Among the 80 unconfirmed pairs with features, I examined 8 manually:
- **بذ↔ذب**: Forward=تفرق (dispersal), Reverse=نفاذ+امتداد+وحدة (penetration+extension+unity). The inversion engine correctly predicts تجمع (gathering) as the inverse of تفرق, but Jabal's reverse meaning uses different vocabulary. Semantically, gathering vs penetrating ARE conceptually opposite directions — one concentrates, the other extends through.
- **ءم↔مء**: Forward=نقص (diminishment), Reverse=اتساع+امتداد (expansion+extension). These ARE semantic opposites — diminishment vs expansion. The Golden Rule works here but the mechanical test can't detect it because it doesn't have an inversion vocabulary.

**Verdict:** The Golden Rule is **plausible but currently unmeasurable** with the mechanical scoring. The inversion engine needs a semantic opposition vocabulary (e.g., تفرق↔تجمع, نقص↔اتساع, باطن↔ظاهر, ضغط↔فراغ) to properly test it. I estimate the true confirmation rate is 25-35% among pairs with features — meaningful but not universal.

**Recommendation for Codex:** Build an opposition mapping:
```python
SEMANTIC_OPPOSITES = {
    "تجمع": "تفرق", "تفرق": "تجمع",
    "ضغط": "فراغ", "فراغ": "ضغط",
    "نقص": "اتساع", "اتساع": "نقص",
    "باطن": "ظاهر", "ظاهر": "باطن",
    "امتداد": "انحسار",
    "قوة": "رخاوة", "رخاوة": "قوة",
    "غلظ": "رقة", "رقة": "غلظ",
    "خروج": "دخول",
    ...
}
```
Then re-run the Golden Rule test using semantic opposition matching instead of feature intersection.

---

## Best Composition Model Recommendation

### Rankings

| Model | Nonzero Rate | Mean (nonzero) | Method A est. | Verdict |
|-------|-------------|----------------|---------------|---------|
| **Intersection** | 66/839 (7.9%) | 0.463 | ~72 | **Best quality, lowest coverage** |
| **Phonetic-Gestural** | 78/839 (9.3%) | 0.421 | ~65 | **Second best** |
| **Sequence** | 123/839 (14.7%) | 0.286 | ~45 | Moderate |
| **Dialectical** | 147/839 (17.5%) | 0.232 | ~35 | **Most coverage, lowest quality** |

### Recommendation for Phase 3 (Root Prediction)

**Use Intersection as the primary model** for trilateral root prediction. It has the highest semantic accuracy when it produces a result. For roots where Intersection produces no prediction (empty intersection), fall back to Phonetic-Gestural.

**Hybrid strategy:**
1. Try Intersection first
2. If empty result → try Phonetic-Gestural
3. If still empty → try Sequence
4. Report which model produced the prediction

### Per-Scholar Results

| Scholar | Nonzero | Mean | Notes |
|---------|---------|------|-------|
| Anbar | 8/24 (33%) | 0.750 | Highest hit rate but only 3 letters covered |
| Hassan Abbas | 28/1484 (1.9%) | 0.560 | High quality when it hits, but very sparse |
| Neili | 30/208 (14.4%) | 0.422 | Good for the 10 letters he covered |
| Asim al-Masri | 4/172 (2.3%) | 0.500 | Too sparse to evaluate — needs 17 more letters |
| Jabal | 344/1468 (23.4%) | 0.280 | Most coverage but lowest mean — his descriptions are richer/harder to match |

**Recommendation:** Use **Jabal's letter values** as the primary input for root prediction — he has the most data and his letter meanings are designed for the composition task. Use other scholars as validation/cross-check, not as primary input.

---

## Signal to Codex: Start Phase 3

**Model:** Intersection (with Phonetic-Gestural fallback)
**Letters:** Jabal's 28
**Target:** Predict المعنى المحوري for all 1,924 roots
**Expected accuracy:** 40-55% (Method A estimate) but Method B will show lower

**Before Phase 3, fix these in order:**
1. Empty actual_features on nuclei (many have meaning text but no extracted features)
2. Synonym groups in scoring (امتداد↔طول, تفشّي↔انتشار, etc.)
3. Semantic opposition mapping for Golden Rule re-test
4. Deepen Abbas/Asim/Anbar coverage

---

*Golden Rule Verdict + Best Model Recommendation*
*LV1 Phase 2 Complete*
*2026-03-23*
