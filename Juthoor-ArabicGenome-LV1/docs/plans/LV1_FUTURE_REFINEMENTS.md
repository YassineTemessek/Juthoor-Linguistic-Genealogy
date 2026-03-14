# LV1 Future Refinements — Backlog

**Baseline checkpoint:** `65733d5` (2026-03-14)
**Status:** Research Factory Phase 0-3 complete. 4 supported, 227 tests.

This file tracks ideas for future LV1 exploration sessions.

---

## Hypotheses to Revisit

### H3 — Modifier Personality (weak signal, z=3.5)
- Current method: embedding subtraction (axial - binary) in BGE-M3 space
- Ideas to try:
  - Position-aware modifier profiles: group by (letter, position) instead of just letter
  - Use the H8 finding: since position matters, control for it
  - Try learned projection instead of raw subtraction
  - Try a contrastive approach: does the same letter consistently push meaning in the same direction relative to shuffled controls?
  - Consider a fine-tuned Arabic semantic model instead of BGE-M3

### H1 — Phonetic-Semantic Link (inconclusive)
- Both Mantel and CCA failed at N=28
- Ideas to try:
  - Sub-letter phonetic features (formant frequencies, spectrograms)
  - Root-level analysis (N=1938) instead of letter-level (N=28)
  - Restrict to specific semantic domains where sound symbolism is known
  - Cross-linguistic comparison (same test on Hebrew, Akkadian)

### H7 — Missing Combinations (not supported, but interesting)
- Result was inverted: missing roots are MORE compatible
- The real explanation is phonological — explore:
  - Articulatory distance as predictor of absence (instead of semantic compatibility)
  - Geminate exclusion rules
  - Weak-letter (ha, waw, ya) patterns in missing roots

### H9, H10 — Untested
- H9 (emphatic stronger): compare emphatic/non-emphatic pairs (ت/ط, د/ض, س/ص, ذ/ظ)
- H10 (full compositionality): test whether letter1_meaning + letter2_meaning + letter3_meaning approximates axial_meaning

## Methods to Explore

- **Fine-tuned Arabic embedder:** BGE-M3 is multilingual but not Arabic-specialized. A fine-tuned model on Arabic semantic fields might capture subtler patterns.
- **Cross-lingual validation:** Run the same experiments on Hebrew roots (same Semitic structure). If H2 holds for Hebrew too, the theory gains weight.
- **Larger root inventory:** The 1,938 Muajam roots are a curated subset. The full genome has 12,333. Running experiments on the larger set might reveal patterns lost in the smaller one.
- **Interactive exploration:** Build a lightweight web dashboard for exploring root families, modifier vectors, and metathesis pairs visually.

---

*Last updated: 2026-03-14*
