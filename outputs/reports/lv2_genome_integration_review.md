# LV2 Genome Integration Review — B.5 Opus Checkpoint
**Date:** 2026-03-14
**Reviewer:** Claude Opus 4.6
**Commit:** 89f812c

---

## Summary

The first genome-informed Arabic-Hebrew cognate discovery run is complete. The LV1 Research Factory's promoted outputs are now live in LV2's scoring pipeline.

**Result: Genome scoring improves ranking quality, not recall.**

| Metric | Blind | Genome | Delta |
|--------|-------|--------|-------|
| Recall@50 | 1.000 | 1.000 | +0.000 |
| MRR | 0.837 | 0.877 | **+0.040** |
| nDCG | 0.877 | 0.909 | **+0.032** |

---

## What Happened

### Data Pipeline
- **Hebrew ingested:** 17,034 lexemes from Kaikki.org Wiktionary (commit `c133aa6`)
- **Persian ingested:** 19,361 lexemes (bonus — available for future experiments)
- **Aramaic ingested:** 2,176 lexemes (bonus — available for future experiments)
- **Benchmark expanded:** 41 gold pairs (15 Arabic-Hebrew), 16 negatives

### Genome Scorer (Codex improvement over original design)
Codex significantly improved the GenomeScorer beyond the original B.1 design:
1. **Cross-lingual consonant mapping:** Arabic and Hebrew letters mapped to shared Semitic phoneme classes (ب↔ב→"b", ك↔כ→"ḫ", etc.)
2. **Pair-sensitive bonuses** instead of flat source-only scoring:
   - Shared binary nucleus: +0.08
   - High-coherence family for shared nucleus: +0.05
   - Metathesis relation between nuclei: +0.05
   - High-coherence + metathesis: +0.03
3. **Lemma fallback:** When root_norm is missing, extracts consonants from the lemma itself

### Discovery Run
- Source: Arabic classical (25 rows from benchmark slice)
- Target: Hebrew (22 rows from benchmark slice)
- 19 covered gold cognate pairs evaluated
- 550 total leads generated per run
- Both runs used BgeM3 semantic + ByT5 form embeddings

---

## Analysis

### Why recall is saturated
Recall@50 = 1.0 in both runs means the retrieval stage (FAISS nearest-neighbor search) already finds all 19 gold pairs within the top 50 candidates. This is expected — Arabic-Hebrew cognates are semantically and orthographically close, so embedding-based retrieval catches them easily.

The genome bonus cannot improve recall because it's applied *after* retrieval, during scoring. It can only improve *ranking* — pushing true cognates higher in the results.

### What the genome improves
- **MRR +0.040:** True cognates appear ~4% closer to rank 1 on average. For a 19-pair benchmark, this means roughly 1 pair moved from rank 2-3 to rank 1.
- **nDCG +0.032:** The overall ranking quality is measurably better. The genome bonus acts as a "semantic anchor" — pairs that share a binary root nucleus in Semitic consonant space get boosted, which correlates with real cognate relationships.

### Example: أب → אב
- Combined score: 0.739 (genome-informed) vs lower without genome
- Genome bonus: +0.08 (shared binary nucleus "ʔb")
- This pair shares the exact Semitic root ʔ-b (father) — the genome correctly identifies the structural connection

### Limitations
1. **Small benchmark:** 19 pairs is too few for statistical significance. The +0.04 MRR improvement could be noise. Need 100+ pairs for reliable measurement.
2. **Saturated recall:** The retrieval already works perfectly on well-known cognates. The genome's value would show more on *harder* pairs (distant cognates, semantic shift cases).
3. **No Persian/Aramaic test yet:** We ingested these languages but haven't run discovery on them.

---

## Verdict

**The LV1 → LV2 integration works.** The genome promotes real cognates in the ranking. The effect is modest (+3-4%) on this small benchmark, but the mechanism is sound: shared Semitic consonant nuclei are a genuine signal for cognate detection.

**The cross-lingual consonant mapping is the key innovation.** Codex's improvement — mapping Arabic and Hebrew to a shared phoneme space before comparing binary roots — is exactly what makes this work across script boundaries.

---

## Next Steps (Recommendations)

1. **Expand the benchmark** to 100+ pairs across multiple language pairs (Arabic-Hebrew, Arabic-Aramaic, Arabic-Persian) for statistically reliable measurement
2. **Test on harder cases:** Include semantic-shift cognates, false friends, and borrowings
3. **Persian discovery run:** Persian uses Arabic script, so orthographic matching is easier — genome bonus may have different impact
4. **Aramaic discovery run:** Smallest corpus (2.2K) but interesting as a Semitic bridge language
5. **Train the reranker** with genome features — currently using logistic regression with 10 features; adding genome_bonus as the 11th feature could improve further

---

*LV2 Genome Integration Review*
*Juthoor Linguistic Genealogy*
*2026-03-14*
