# Juthoor LV1 Knowledge Package

**Project:** Juthoor Linguistic Genealogy
**Layer:** LV1 — Arabic Genome (ArabicGenome-LV1)
**Date exported:** 2026-03-26
**Status:** Research complete, findings validated

---

## What This Package Is

This is a self-contained research export from the Juthoor Linguistic Genealogy project. It contains all findings from Layer 1 (LV1) of the project, which investigated whether the Arabic consonant system functions as a *linguistic genome* — a compositional semantic system in which each of the 28 Arabic consonant letters carries a stable, reproducible semantic charge.

You do not need access to the Juthoor codebase, database, or any software to use this package. All findings are fully described in the documents and data files here.

---

## The Core Theory (one paragraph)

Arabic is built on triliteral roots (three-consonant combinations). The Juthoor hypothesis is that these roots are not arbitrary — each of the 28 Arabic consonant letters (الأحرف الهجائية) carries an intrinsic semantic meaning, which compounds when letters combine. A two-letter pair (ثنائي — "binary nucleus") functions as the semantic atom of the root. The third letter then modifies the binary nucleus's meaning. This creates a compositional semantic hierarchy: **letters → binary nuclei → triliteral roots → root families**. The evidence for this comes from 456 binary nuclei analyzed from Ibrahim Mohamed Jabal's *Al-Mu'jam al-Ishtiqaqi al-Mu'assal* (المعجم الاشتقاقي المؤصل), covering approximately 12,000 root instances. Five Arab scholars have independently investigated related questions; their findings are compared and evaluated in this package.

---

## How to Use These Files

### For a human reader (start here)

Read the files in order:

1. `01_THEORY.md` — the full linguistic theory for someone new to Arabic phonosemantics
2. `02_LETTER_MEANINGS.md` — the empirical meaning of all 28 Arabic letters
3. `03_BINARY_NUCLEI.md` — how letter meanings compose into two-letter semantic atoms
4. `04_ROOT_PREDICTION.md` — how binary nuclei combine with a third letter to predict root meanings
5. `05_CROSS_LINGUAL.md` — cross-lingual projection (Semitic and English cognates)
6. `06_DISCOVERIES.md` — what is new in Juthoor not found in prior scholarship

### For an AI or machine reader

The `data/` folder contains machine-readable JSON files:

- `data/letter_meanings.json` — all 28 letters with empirical meanings, confidence, nuclei counts
- `data/scholar_comparison.json` — per-letter scholar feature sets for all 5 scholars
- `data/synonym_families.json` — 326 synonym root families used for cross-lingual validation

---

## Key Results Summary

### Letter genome
- 28 Arabic consonants each carry a stable, empirically derivable semantic charge
- Derivation method: bottom-up from 456 binary nuclei (not from phonetic theory)
- Overall 22/28 letters broadly confirmed vs. prior scholarship
- 4 letters corrected: م (meem), ع (ain), غ (ghain), and ب (ba) reframed
- Low-confidence letters (insufficient data): ء, ظ, ي, and to a degree و

### Binary nucleus composition
- 456 binary nuclei tested for compositional predictability
- Mean Jaccard similarity between predicted and actual nucleus meanings: 0.141
- 56.5% of nuclei show at least some compositional signal
- Strong composition (Jaccard ≥ 0.5): only 21 nuclei (5.1%)
- Best poster case: ضم (pressure + gathering = gathering by pressure) — J=0.75
- Three systematic failure families identified (quality emergence, directional specificity, interaction products)

### Root prediction (Method A)
- Overall accuracy (Method A weighted score): 49.5 / 100
- This is the first LV1 score clearly above the midpoint
- Improvement over earlier baseline (v3): +12.8 percentage points
- Exact-band predictions: 90.9 — partial-high: 65.0 — partial-low: 44.2

### Cross-lingual projection
- Arabic → Hebrew/Aramaic exact consonant match: 67.9% (36/53 pairs)
- Arabic → Hebrew/Aramaic binary-prefix match: **88.7%** (47/53 pairs)
- This validates the binary nucleus as the cross-linguistically stable unit
- Arabic → English preliminary exact hits: 3/11 (بيت→booth, طرق→track, جلد→cold)

### Reverse pairs (Anbar's hypothesis)
- 158 non-empty reversible pairs tested
- True inversion: only 19 pairs (12%) — the reversal law is not general

---

## Scholar Coverage

Five scholars studied Arabic letter meanings independently; Juthoor uses their work as a validation layer:

| Scholar | Full Name | Coverage | Accuracy vs. Juthoor |
|---------|-----------|----------|----------------------|
| Jabal | Ibrahim Mohamed Jabal | 28 letters | ~79% |
| Abbas | Hassan Abbas | 28 letters | ~62% |
| Asim | Asim Al-Masri | 28 letters | ~28% |
| Neili | Neili (kinetic theory) | 10 letters | ~70% |
| Anbar | Mohamed Anbar | 25 letters | ~56% |

Jabal's *Al-Mu'jam al-Ishtiqaqi al-Mu'assal* (المعجم الاشتقاقي المؤصل) is the primary data source. Juthoor's empirical derivation is independent of all five scholars — scholar agreement is validation, not methodology.

---

## What Juthoor Does Not Claim

- That every Arabic root can be generated from letters by a simple formula
- That binary composition works for all nuclei (it does not — about half)
- That meaning predictions transfer cleanly to other languages (structural consonant claims are strong; semantic transfer is not yet validated)
- That the reversal of a root always inverts its meaning (only 12% of cases)

The Juthoor LV1 conclusion is: Arabic letters are semantically non-random. The binary nucleus is the strongest internal semantic unit. Composition works for about half the system. The other half involves emergent interaction effects that follow systematic patterns. The genome is real, but its active unit is the nucleus and its composition law is interactional rather than purely additive.
