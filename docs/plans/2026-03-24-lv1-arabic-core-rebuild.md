# LV1 Arabic Core Rebuild — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild LV1 from verified factual baseline — fix data pipeline, integrate all 5 scholars properly, stabilize Arabic genome (letters → binary nuclei → trilateral roots) before any cross-lingual work.

**Architecture:** Arabic-first, scholar-integrated, Quran-validated. Each layer must be solid before the next.

**Tech Stack:** Python 3.11+, existing LV1 package, JSONL data canon, pytest

---

## Context & Motivation

The Phase 2-3 session (2026-03-23) built good infrastructure (root predictor, scoring, cross-lingual projection) but executed the Arabic genome incompletely:
- Only Jabal was used as primary letter/root source
- Other scholars (Abbas, Asim, Neili, Anbar) were loaded but underused
- Cross-lingual work started before Arabic-core was stable
- Codex ingestion pipeline has data discrepancies vs canonical source
- Quranic application layer (1,666 entries) was never used as validation

**Yassin's directive:** Letter → Binary Root → Trilateral Root. Arabic first. Scholars integrated. Cross-lingual only after.

---

## Verified Factual Baseline (from Yassin + LV1_VERIFIED_DATA_AUDIT.md, 2026-03-24)

| Scholar | Letters | Role |
|---------|---------|------|
| **Jabal** | 28 | Primary empirical baseline. Binary nuclei + roots + Quranic applications. Not automatically absolute truth. |
| **Asim al-Masri** | 28 (+ألف المد=29) | Full alternative semantic system. **Direct continuation of Neili's القصدية project.** Main competitor to Jabal. |
| **Abbas** | 26 (23+3 jawfiyya) | Sensory/articulatory validation. هيجانية/إيمائية/إيحائية per-letter classification. Routing/validation layer. |
| **Neili** | 10 | Primary methodological role: intentionality, concept vs instance, no synonymy, verbal method. Asim completed his 28-letter project. |
| **Anbar** | 25 (21 explicit + 4 contextual) | Articulatory-dialectical source. 4 contextual letters (ج,ك,ت,غ) are lower confidence. Only ط,ث,ظ truly missing. Reversal = hypothesis, not law. |

| Data | Canonical (xlsx) | Current JSONL | Action |
|------|------------------|---------------|--------|
| Roots | 1,924 | 1,938 (+14 extra, 15 duplicates) | Audit and fix to canonical |
| Binary nuclei | 456 | 457 | Verify |
| Quranic apps | 1,666 | 1,739 (+73 extra) | Audit against xlsx |
| Anbar letters | 25 | 3 | Extract from verified NotebookLM audit |
| Abbas letters | 26 | 28 (grouping artifacts) | Re-extract from ABBAS_LETTER_CLASSIFICATION.md |

**Key corrections from verified audit:**
- Anbar = 25 letters (not 3, not 21). Source: NotebookLM extraction, NOT the OCR-damaged raw file.
- Asim = Neili's intellectual heir, not independent. Cites Neili 30+ times.
- Abbas إيماء/إيحاء/هيجانية = fully extracted in ABBAS_LETTER_CLASSIFICATION.md (ready for JSONL).
- Scholar disagreements: keep as alternatives, test separately, do NOT force premature consensus.

---

## Phase 1: Data Audit & Scholar Rebuild (Codex-heavy)

### Task 1.1: Audit root pipeline against canonical xlsx

**Files:**
- Audit: `Juthoor-ArabicGenome-LV1/data/theory_canon/roots/jabal_roots_raw.jsonl`
- Reference: `The Arabic Tongue/Muajam Ishtiqaqi/Tables_Juthoor/*.xlsx` (25 files)

- [x] Audit the mismatch against the canonical xlsx instead of the stale `roots.jsonl` shortcut
- [x] Rebuild Jabal roots directly from `المعجم_الاشتقاقي_Juthoor_v2.xlsx`
- [x] Fix exported canon to match canonical counts exactly: `1,924` roots, `456` nuclei
- [x] Verify `1,666` Quranic applications match the xlsx
- [x] Tag each root: `is_quranic: true/false` based on canonical xlsx
- [ ] Commit: `fix(lv1): audit root pipeline, rebuild from canonical xlsx`

**Owner:** Codex
**Tests:** Count roots, count quranic, assert no duplicates

---

### Task 1.2: Extract Abbas 29 entries from verified classification

**Files:**
- Primary source: `The Arabic Tongue/ABBAS_LETTER_CLASSIFICATION.md` (166 lines, fully extracted 2026-03-24)
- Secondary: `The Arabic Tongue/Languistic theories/حسن عباس/خصائص الحروف العربية ومعانيها - حسن عباس.md` (5,155 lines)
- Target: `Juthoor-ArabicGenome-LV1/data/theory_canon/letters/hassan_abbas_letters.jsonl`

- [x] Convert ABBAS_LETTER_CLASSIFICATION.md complete table → JSONL
- [x] Preserve: `sensory_category`, `mechanism_type`, `raw_description`, `atomic_features`, `confidence`
- [x] Produce 29 entries (28 letters + ألف المد) — ء/ا/و/ي treated as jawfiyya/هيجانية entries in Abbas's scheme
- [x] Cross-reference atomic_features with the detailed sections (B and C tables + bounded alias expansion)
- [x] Replace current hassan_abbas_letters.jsonl
- [x] Commit: `fix(lv1): rebuild Abbas 29 entries from verified classification`

**Owner:** Codex (extraction) + Claude (review atomic_features decomposition)
**Tests:** Assert 29 entries, all have sensory_category + mechanism_type, 4 هيجانية + 5 إيمائية + 19-20 إيحائية

---

### Task 1.3: Extract Anbar 25 letters from verified audit

**Files:**
- Source: `The Arabic Tongue/LV1_VERIFIED_DATA_AUDIT.md` (table at lines 99-120, verified from NotebookLM)
- Target: `Juthoor-ArabicGenome-LV1/data/theory_canon/letters/anbar_letters.jsonl`

- [x] Extract 25 entries from the verified audit table (21 explicit incl. `الفتحة` + 4 contextual)
- [x] Each entry: letter, scholar, phonetic_group, raw_description, atomic_features, confidence
- [x] Mark 21 explicit letters as `confidence: "high"`
- [x] Mark 4 contextual letters (ج,ك,ت,غ) as `confidence: "medium"` with `derivation: "contextual"`
- [x] DO NOT extract from the OCR-damaged raw file — use the verified audit only
- [x] Replace current 3-entry anbar_letters.jsonl
- [x] Commit: `fix(lv1): expand Anbar from 3 to 25 letters (verified audit)`

**Owner:** Codex
**Tests:** Assert 25 entries, 21 high-confidence + 4 medium-confidence, ط/ث/ظ absent
**Resolved:** `LV1_VERIFIED_DATA_AUDIT.md` now includes `الفتحة` as the 21st explicit Anbar entry, eliminating the old 24/25 mismatch.

---

### Task 1.4: Verify Asim al-Masri complete table (+ ألف المد)

**Files:**
- Current: `Juthoor-ArabicGenome-LV1/data/theory_canon/letters/asim_al_masri_letters.jsonl`
- Source: `The Arabic Tongue/Languistic theories/عاصم المصري/جدول معاني الحروف _.md` (partial, 11 letters)

- [x] Rebuild from the verified complete table in `LV1_VERIFIED_DATA_AUDIT.md`
- [x] Fix the 3 letters that previously had missing atomic_features
- [x] Add field: `continues_neili: true/false` to mark which letters extend Neili's 10
- [x] Commit: `fix(lv1): verify and complete Asim al-Masri complete table`

**Owner:** Codex
**Tests:** Assert all exported entries have atomic_features

---

### Task 1.5: Formalize Neili's 10 letters + methodological constraints

**Files:**
- Current: `Juthoor-ArabicGenome-LV1/data/theory_canon/letters/neili_letters.jsonl`
- New: `Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/core/neili_constraints.py`

- [ ] Verify 10-entry JSONL is correct
- [ ] Create `neili_constraints.py` encoding his hard rules:
  - `no_synonymy(root1, root2) -> bool` — two Quranic roots cannot be synonyms
  - `is_conceptual(meaning) -> bool` — meaning must be abstract/conceptual, not instance-specific
  - `intentionality_score(root, meaning) -> float` — how intentional/non-metaphorical is the mapping
- [ ] These constraints become validation filters, not scoring weights
- [ ] Commit: `feat(lv1): add Neili methodological constraints as hard filters`

**Owner:** Claude/Sonnet (design) + Codex (implementation)
**Tests:** Test constraints on known Quranic root pairs

---

### Task 1.6: Update letter registry with all scholars

**Files:**
- Modify: `Juthoor-ArabicGenome-LV1/data/theory_canon/registries/letters.jsonl`

- [x] Populate `canonical_kinetic_gloss` from Asim data
- [x] Populate `canonical_sensory_gloss` from Abbas data
- [x] Add `sources` array citing all scholars who cover each letter
- [x] Compute `agreement_level` per letter: strong/moderate/weak/conflicting
- [x] Update `confidence_tier` from "stub" to actual tier based on scholar agreement
- [x] Commit: `feat(lv1): enrich letter registry with all 5 scholars`

**Owner:** Codex
**Tests:** Assert the merged flat registry is rebuilt from scholar atoms; current export is `29` entries because it retains `ألف المد` but excludes Anbar's non-core `الفتحة`.

---

## Phase 2: Scholar Comparison & Integration (Claude-heavy)

### Task 2.1: Cross-scholar letter comparison report

**Files:**
- New: `outputs/lv1_scoring/scholar_letter_comparison.md`

- [ ] For each of 28 letters, compare atomic_features across Jabal, Asim, Abbas, (Neili where available), (Anbar where available)
- [ ] Classify each letter as: `agreement` (scholars converge), `complementary` (scholars add different dimensions), `conflicting` (scholars disagree)
- [ ] Identify which letters have strongest cross-scholar support
- [ ] Identify which letters are most disputed
- [ ] Recommend: for disputed letters, which scholar's interpretation to use as primary
- [ ] Commit: `docs(lv1): cross-scholar letter comparison report`

**Owner:** Claude (semantic analysis)

---

### Task 2.2: Build consensus letter features

**Files:**
- Modify: `Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/factory/scoring.py`
- Modify: `Juthoor-ArabicGenome-LV1/scripts/canon/build_lv1_theory_assets.py`

- [x] For each letter, produce generated consensus feature sets using this logic:
  - Features agreed by 3+ scholars → high confidence
  - Features from 2 scholars → medium confidence
  - Features from 1 scholar only → low confidence (retained only in weighted mode)
- [x] Emit two generated consensus scholar options:
  - `consensus_strict` = shared features only
  - `consensus_weighted` = Jabal base + shared features
- [x] This becomes an additional consensus scoring layer alongside individual scholars
- [x] Commit: `feat(lv1): consensus letter features across 5 scholars`

**Owner:** Claude (design consensus logic) + Codex (implementation)
**Tests:** Assert generated consensus scholar maps rebuild successfully and score against all nuclei

---

### Task 2.3: Re-score binary nuclei with all scholars + consensus

**Files:**
- Modify: `outputs/lv1_scoring/nucleus_score_matrix.json`

- [x] Re-run score matrix using:
  - Jabal letters (baseline)
  - Asim letters (full alternative)
  - Abbas letters (sensory validation)
  - Neili letters (where available)
  - Anbar letters (25-entry verified rebuild)
  - `consensus_strict`
  - `consensus_weighted`
- [x] Compare: which scholar's letters produce best prediction of Jabal's binary nucleus meanings?
- [x] Report: per-scholar accuracy on binary nuclei
- [x] Commit: `feat(lv1): multi-scholar nucleus scoring`

**Owner:** Codex (computation) + Claude (analysis)
**Checkpoint:** `consensus_strict` currently has the best mean Jaccard (`0.1207`), while `consensus_weighted` has the best nonzero coverage (`648/1580`).

---

## Phase 3: Trilateral Root Prediction Rebuild (Both)

### Task 3.1: Rebuild root predictor with scholar-aware routing

**Files:**
- Modify: `Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/factory/root_predictor.py`

- [ ] Add `scholar` parameter to prediction pipeline
- [ ] Support running predictions with: jabal, asim, abbas, consensus letter sets
- [ ] Keep Jabal's binary nucleus meanings as ground truth (they define المعنى المحوري)
- [ ] Third letter features come from the selected scholar's letter meanings
- [ ] Commit: `feat(lv1): scholar-aware root prediction pipeline`

**Owner:** Codex
**Tests:** Run predictions with each scholar, compare results

---

### Task 3.2: Add Neili constraints as validation filters

**Files:**
- Modify: `Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/factory/root_predictor.py`

- [ ] After prediction, apply Neili filters:
  - Flag predictions that violate no-synonymy (two roots predicted with identical meanings)
  - Flag predictions where meaning is instance-specific rather than conceptual
- [ ] Add `neili_flags` field to prediction output
- [ ] Commit: `feat(lv1): apply Neili constraints as post-prediction filters`

**Owner:** Claude/Sonnet
**Tests:** Test with known Quranic root pairs

---

### Task 3.3: Add Quranic-first validation

**Files:**
- New: `Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/factory/quranic_validation.py`

- [ ] Load the 1,666 canonical Quranic applications
- [ ] For each Quranic root, check: does predicted meaning align with Quranic usage?
- [ ] Separate accuracy metrics for Quranic roots (higher bar) vs non-Quranic roots
- [ ] Report: Quranic roots accuracy vs overall accuracy
- [ ] Commit: `feat(lv1): Quranic-first validation layer`

**Owner:** Codex (pipeline) + Claude (semantic validation)

---

### Task 3.4: Build synonym-family mapping

**Files:**
- New: `Juthoor-ArabicGenome-LV1/data/theory_canon/roots/synonym_families.jsonl`

- [ ] Extract from LV0 Arabic dictionary data: roots that share المعنى المحوري
- [ ] Example: قلب and لب both mean "heart/core" — they're a synonym family
- [ ] Each family: `family_id, roots[], shared_concept, confidence`
- [ ] This is prerequisite for correct cross-lingual work later (قלب→לב via لب)
- [ ] Commit: `feat(lv1): Arabic root synonym families from LV0 dictionary`

**Owner:** Codex (extraction) + Claude (review)
**Tests:** Verify known synonym families (قلب/لب, etc.)

---

## Phase 4: Method A at Scale (Claude)

### Task 4.1: Method A calibration on 200+ binary nuclei

- [ ] Claude semantically judges 200 binary nuclei (not just 50)
- [ ] Calibrate Method B feature weights against Method A results
- [ ] Produce optimal feature weight vector
- [ ] Commit: `docs(lv1): Method A at-scale calibration, 200 nuclei`

**Owner:** Claude

---

### Task 4.2: Method A on Quranic roots (100 roots)

- [ ] Select 100 Quranic roots stratified across BABs
- [ ] Claude judges: does the predicted meaning match the Quranic usage?
- [ ] Apply Neili's concept-vs-instance lens (is the prediction conceptual enough?)
- [ ] Report: Quranic root accuracy with Neili discipline
- [ ] Commit: `docs(lv1): Quranic root Method A calibration`

**Owner:** Claude

---

## Phase 5: Arabic Genome Verdict (Claude)

### Task 5.1: Final Arabic genome status report

- [ ] Compile results from Phases 1-4
- [ ] Answer: Can we predict Arabic root meanings from letter composition?
- [ ] Per-scholar accuracy comparison
- [ ] Consensus vs individual scholar performance
- [ ] Quranic vs non-Quranic accuracy
- [ ] Honest assessment of what works and what doesn't
- [ ] Recommendations for Phase 6 (cross-lingual, only if Arabic core is stable)

**Owner:** Claude

---

## Execution Order & Dependencies

```
Phase 1 (parallel where possible):
  1.1 Root audit ──────────────────────── Codex
  1.2 Abbas extraction ────────────────── Codex + Claude review
  1.3 Anbar extraction ────────────────── BLOCKED on Yassin help
  1.4 Asim verification ───────────────── Codex
  1.5 Neili constraints ───────────────── Claude/Sonnet
  1.6 Letter registry update ──────────── Codex (after 1.2-1.4)

Phase 2 (after Phase 1):
  2.1 Scholar comparison ──────────────── Claude
  2.2 Consensus features ──────────────── Claude + Codex
  2.3 Multi-scholar nucleus scoring ───── Codex + Claude

Phase 3 (after Phase 2):
  3.1 Scholar-aware root predictor ────── Codex
  3.2 Neili constraint filters ────────── Claude/Sonnet
  3.3 Quranic validation layer ────────── Codex + Claude
  3.4 Synonym families ────────────────── Codex + Claude

Phase 4 (parallel with Phase 3):
  4.1 Method A at scale (nuclei) ──────── Claude
  4.2 Method A Quranic roots ─────────── Claude

Phase 5 (after Phase 3+4):
  5.1 Arabic genome verdict ───────────── Claude
```

---

## Resolved Decisions (from Yassin, 2026-03-24)

1. **Anbar:** 25 letters available from verified NotebookLM extraction. 4 contextual (lower confidence). Only ط,ث,ظ missing. **RESOLVED.**
2. **Scholar disagreement policy:** Keep as alternatives. Test separately against Jabal's binary/root data. No premature consensus. Only ask Yassin case-by-case for unclear extractions. **RESOLVED.**
3. **Synonym family seeds:** 10 families provided (قلب/فؤاد/لب, ستر/خفي/كتم, جمع/ضم/لم/حشد, etc.). Extract from LV0, manually review strongest. NOT a denial of Neili's no-synonymy — these are cross-lingual mining seeds. **RESOLVED.**

---

*Plan created: 2026-03-24*
*Plan updated: 2026-03-24 (all blockers resolved by Yassin)*
*Status: READY FOR EXECUTION*
