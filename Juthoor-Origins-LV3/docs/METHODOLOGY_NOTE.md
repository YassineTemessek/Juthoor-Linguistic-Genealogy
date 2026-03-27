# Methodological Note: Computational Comparative Linguistics via Root System Analysis

## Abstract

This note documents the methodology used by the Juthoor project to investigate cross-linguistic relationships through computational analysis of the Arabic consonantal root system. The approach differs from traditional comparative linguistics in three key ways: (1) it is root-centric rather than word-centric, (2) it uses multiple independent discovery methods to reduce false positives, and (3) it applies statistical permutation tests to validate that observed patterns exceed random chance.

## 1. Why Root-Centric?

Traditional comparative linguistics compares whole words across languages (e.g., English "father" ~ Latin "pater" ~ Sanskrit "pitṛ"). The Juthoor approach instead extracts the **consonantal skeleton** from each word, treating it as the fundamental unit of comparison.

**Rationale from LV1 Research Factory:**
- Arabic roots encode meaning through consonant structure (H12: cosine similarity 0.716)
- The binary nucleus (first two consonants) defines a semantic field (H2: >11σ above baseline)
- Consonant position matters — position 1 carries the most semantic weight (H8: 86% of letters show significant positional effects)

This means comparing consonant skeletons is not an arbitrary choice but is grounded in empirically measured linguistic structure.

## 2. Multi-Method Discovery

Rather than a single comparison algorithm, the Juthoor discovery engine applies 12 independent methods simultaneously:

1. **Direct skeleton match** — consonant-to-consonant comparison
2. **Morpheme decomposition** — strip affixes to reveal shared stems
3. **Multi-hop chain** — trace Arabic → Latin/Greek → Modern European
4. **Guttural deletion** — account for systematic ع/غ/ح/خ loss
5. **Emphatic collapse** — account for emphatic → plain consonant shift
6. **Metathesis detection** — consonant order reversal
7. **Dialect variants** — Gulf/Egyptian/Moroccan consonant shifts
8. **Position-weighted scoring** — weight by consonant position importance
9. **IPA-based matching** — use phonetic transcriptions
10. **Reverse root generation** — map English consonants back to possible Arabic roots
11. **Synonym expansion** — check Arabic synonym families
12. **Article detection** — identify absorbed Arabic definite article

**Key insight from method effectiveness analysis:**
- Multi-hop chain has the highest precision (3.4%) — historical transmission pathways are the most reliable signal
- Direct skeleton has the highest recall but lowest signal-to-noise ratio
- Metathesis is unreliable for cross-family pairs (0.11% precision) but valuable for intra-Semitic (9.8% of Arabic-Hebrew leads)

## 3. Convergent Evidence

A single method match between two languages is weak evidence. The Juthoor approach strengthens evidence through **convergent matching**:

- If Arabic root X matches English word Y via skeleton AND matches Latin word Z via multi-hop chain AND matches Greek word W via emphatic collapse — that's three independent methods finding the same root in three independent languages.

**Current results:** 153 Arabic roots connect to 3+ target languages independently. These are the strongest cognate candidates in the dataset.

## 4. Statistical Validation

The critical question: do observed matches exceed what we'd expect by random consonant overlap?

**Null model:** Shuffle Arabic roots randomly (breaking the root-meaning association), re-run the discovery pipeline, count matches. The REAL match count should far exceed the shuffled count.

**Permutation test:** Run the null model N times, compute:
- Z-score: (real_count - null_mean) / null_std
- If z > 3.29: statistically significant at p < 0.001

**Expected result:** Given that Arabic ع is deleted 88% of the time (not a random pattern), and given that consonant correspondences are systematic (ب→b/p, ق→c/g/k), the real match rate should dramatically exceed random chance.

## 5. Anchor Classification

Not all computational matches are equal. The three-tier system:

- **Gold anchors:** Score ≥ 0.85, 4+ methods fired, convergent evidence in 3+ languages
- **Silver anchors:** Score ≥ 0.70, 2+ methods fired, phonetic law or genome match
- **Auto-brut anchors:** Score ≥ 0.55, computational signal only

Only gold and silver anchors are considered evidence-quality. Auto-brut leads require additional validation before they can support theoretical claims.

## 6. Limitations

1. **Directionality:** The pipeline detects correlations, not causal directions. Whether Arabic influenced English, or both descend from a common ancestor, or the similarity is coincidental — requires historical and chronological evidence.

2. **Loanword contamination:** Many Arabic-English matches are medieval loanwords (via Latin/Spanish during Islamic Golden Age), not deep genetic cognates. The article absorption detector catches obvious cases (al-cohol, al-gebra), but subtler borrowings are harder to isolate.

3. **False positive rate:** Even with 5 scoring guards and 12 methods, the fast-mode pipeline (without semantic embeddings) has a high false positive rate. The reranker v3 helps but cannot eliminate all noise.

4. **Corpus bias:** The current Arabic source draws primarily from Quranic vocabulary (4,903 lemmas) supplemented by gold benchmark pairs. The classical Arabic corpus (32,687 lemmas) covers more vocabulary but may over-represent literary/religious terms.

## 7. Reproducibility

The project maintains:
- Frozen research bundles with all key data and documents
- Versioned cognate graph (JSON with provenance)
- All scoring parameters and thresholds documented
- Test suite (1,088+ tests) ensuring pipeline correctness
- Git history tracking every change

Any claim made by the project can be traced back to specific data, specific code, and specific scoring parameters.
