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
**Checkpoint:** `consensus_strict` currently has the best mean Jaccard (`0.1207`), while `consensus_weighted` has the best nonzero coverage (`648/1580`). After the later vocabulary + third-letter rerun, the root layer improved more than the nucleus layer; see Phase 3 checkpoints below.

---

## Phase 3: Trilateral Root Prediction Rebuild (Both)

### Task 3.1: Rebuild root predictor with scholar-aware routing

**Files:**
- Modify: `Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/factory/root_predictor.py`

- [x] Add `scholar` parameter to prediction pipeline
- [x] Support running predictions with: `jabal`, `asim_al_masri`, `hassan_abbas`, `consensus_strict`, `consensus_weighted`
- [x] Keep Jabal's binary nucleus meanings as ground truth (they define المعنى المحوري)
- [x] Third letter features come from the selected scholar's letter meanings
- [x] Add scholar-level summary metrics to `root_score_matrix.json`
- [x] Commit: `feat(lv1): scholar-aware root prediction pipeline`

**Owner:** Codex
**Tests:** Run predictions with each scholar, compare results
**Checkpoint:** Initial scholar-aware rebuild: `consensus_strict` led on root means (`0.187543`), while `hassan_abbas` was marginally highest on nonzero count (`1129` vs `1128` for strict consensus).

---

### Task 3.2: Add Neili constraints as validation filters

**Files:**
- Modify: `Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/factory/root_predictor.py`
- Modify: `Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/core/neili_constraints.py`

- [x] After prediction, apply Neili filters:
  - Flag predictions that violate no-synonymy (two roots predicted with identical meanings)
  - Flag predictions where meaning is instance-specific rather than conceptual
- [x] Add `neili_flags` field to prediction output
- [x] Add Neili validity summary to `root_score_matrix.json`
- [x] Commit: `feat(lv1): apply Neili constraints as post-prediction filters`

**Owner:** Claude/Sonnet
**Tests:** Test with known Quranic root pairs
**Checkpoint:** This was implemented and tested as a diagnostic experiment, then explicitly parked. User direction is to keep Neili's no-synonymy for a later Quran-word interpretation stage, not active LV1 genome scoring.

### Phase 3A/3B: Feature-vocabulary expansion and third-letter correction

- [x] Expand the semantic vocabulary around modulation/substance/location terms and re-extract all `jabal_features`
- [x] Audit the post-expansion gaps in `outputs/lv1_scoring/feature_vocab_gap_report.md`
- [x] Add a third-letter compatibility filter, including a blacklist for `التحام` as a third-letter poison feature
- [x] Add `nucleus_only` fallback for category-only pseudo-overlap cases where intersection collapses back to the nucleus
- [x] Re-run root predictions and score matrix after both fixes

**Current checkpoint after A/B rerun (2026-03-24):**
- Canonical counts remain fixed: `1,924` roots, `456` nuclei, `1,666` Quranic applications
- Root empty-actual improved modestly: `113 -> 107`
- Mean actual features per root: `2.5333`
- Root layer improved materially after B.2-B.3:
  - overall blended Jaccard: `0.195562`
  - nonzero predictions: `4550 / 9620` (`47.3%`)
  - `consensus_weighted`: `0.201593`
  - `consensus_strict`: `0.201172`
  - `jabal`: `0.195026`
  - `asim_al_masri`: `0.190801`
  - `hassan_abbas`: `0.189219`
- Third-letter compatibility filter impact:
  - rows with dropped third-letter features: `1551`
  - rows dropping blacklisted `التحام`: `1156`
  - `nucleus_only` fallback rows: `3178`

**Interpretation:** vocab expansion alone had diminishing returns, but the third-letter correction materially improved the root layer and moved both consensus models above `0.20` blended Jaccard.

**Third-letter profile follow-up (I2, 2026-03-26):**
- `THIRD_LETTER_MODIFIER_PROFILES.md` is now generated from `root_predictions.json`
- strongest stable third-letter enrichers in the current matrix: `ج`, `ظ`
- high-value but still mixed enrichers: `غ`, `ش`, `ص`, `ض`, `ك`, `هـ`, `ق`
- riskiest modifiers: `ب`, `ت`, `ر`, `س`, `ع`, `ل`
- persistent poison pattern: third-letter-only `التحام`, especially with `ر`, `ل`, `ب`, and `ع`
- practical reading: the nucleus still carries most of the reliable signal; third-letter contributions are selective and should be treated as profilers/modifiers, not as equally strong semantic cores

**Letter-correction follow-up (F.4, 2026-03-26):**
- Yassin-confirmed Jabal corrections are now live in the canonical builder path:
  - `ب = ظهور + خروج`
  - `م = تجمع + تلاصق`
  - `ع = ظهور + عمق`
  - `غ = باطن + اشتمال`
- rebuilt outputs now reflect those corrected letter values before consensus composition
- current post-correction root checkpoint:
  - overall blended Jaccard: `0.196015`
  - nonzero predictions: `4552 / 9620`
  - `consensus_weighted`: `0.201964`
  - `consensus_strict`: `0.201399`
- next semantic checkpoint is Claude's `F.5` Method A recalibration on the corrected matrices

**Refactor checkpoint (2.1 + 2.2, 2026-03-26):**
- `root_predictor.py` refactored into smaller routing, intersection-fallback, cohort-summary, and row-serialization helpers
- `independent_letter_derivation.py` refactored into smaller feature-selection, position-payload, and scholar-classification helpers
- focused suites remained green with no intended metric drift; this was maintenance/polish for the active LV1 pipeline, not a semantic-model change

**Position-aware rerun checkpoint (2026-03-26):**
- Claude's `position_aware_composer` is wired and runnable, but the full rerun did **not** improve LV1
- 2026-03-26 confirmation rerun of `build_lv1_theory_assets.py` reproduced the same checkpoint exactly, so the regression is stable rather than a stale-output artifact
- current rerun metrics:
  - overall blended Jaccard: `0.190419` (down from `0.196015`)
  - nonzero predictions: `4352 / 9620` (down from `4552 / 9620`)
  - `consensus_weighted`: `0.196644` (down from `0.201964`)
  - `consensus_strict`: `0.190738` (down from `0.201399`)
  - `position_aware` rows: `3005`, mean blended `0.146678`
- improvement vs current on-disk pre-rerun baseline: `0.000000` on all reported root metrics; rebuild is deterministic
- practical decision for now: keep the position-aware model **experimental**, not promoted as the new default root composer
- side effect: regenerating the benchmark support files also cleared the pre-existing `test_promotions.py` failure

---

### Task 3.3: Add Quranic-first validation

**Files:**
- New: `Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/factory/quranic_validation.py`

- [x] Load the 1,666 canonical Quranic applications
- [x] For each Quranic root, check: does predicted meaning align with Quranic usage?
- [x] Separate accuracy metrics for Quranic roots (higher bar) vs non-Quranic roots
- [x] Report: Quranic roots accuracy vs overall accuracy
- [x] Commit: `feat(lv1): Quranic-first validation layer`

**Owner:** Codex (pipeline) + Claude (semantic validation)
**Checkpoint:** The split is now explicit in `root_score_matrix.json`. Quranic rows (`8330`) score materially lower than non-Quranic rows (`1290`) and nearly all current Neili-valid rows come from the non-Quranic cohort (`95.35%` valid vs `0.60%` for Quranic). This shows the present `no_synonymy` implementation is too coarse for Quranic final gating and needs application-aware refinement.

**Decision update:** Neili no-synonymy is no longer part of the active LV1 acceptance/scoring path. Keep the Quranic split, but reserve Neili for a later Quranic explanation layer.

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
*Plan updated: 2026-03-26 (position-aware rerun reconfirmed as a regression with no metric lift)*
*Status: READY FOR EXECUTION*
