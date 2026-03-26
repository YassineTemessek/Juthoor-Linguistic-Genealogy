# LV1 Execution Orchestration — Claude + Codex Parallel Work Plan

**Date:** 2026-03-22
**Architecture:** `Juthoor-ArabicGenome-LV1/docs/The Arabic Tongue (nature-genome-application)/LV1_ARCHITECTURE_VISION.md`
**Goal:** Build the LV1 semantic engine in 5 phases with no stops between Claude and Codex.

---

## Agent Split

| Agent | Strengths | Assigned Work |
|-------|-----------|---------------|
| **Codex** | Fast, bulk computation, data processing, xlsx parsing, heavy lifting | Data extraction, feature decomposition, scoring engine, statistical analysis |
| **Claude (Opus/Sonnet)** | Arabic semantic understanding, architecture, review, Claude Method A scoring | Schema design, semantic calibration, quality review, Method A judging |

**Key principle:** Codex always has work queued. No blocking on Claude.

---

## Data Assets Available NOW

| Asset | Location | Content |
|-------|----------|---------|
| **Jabal's 28 letter meanings** | `LV1_ARCHITECTURE_VISION.md` Appendix A | Complete table |
| **Asim al-Masri's 28 letters** | `Languistic theories/عاصم المصري/جدول معاني الحروف _.md` + summary in main docs | 10 detailed + 18 names only |
| **Neili's 10 letters** | Main theory doc (updated section 13) | Physical movement meanings with table |
| **Hassan Abbas's 28 letters** | Main theory doc (updated section 8) + `Languistic theories/حسن عباس/` | 6 sensory categories, full classification |
| **Anbar's letter dialectics** | Main theory doc (section 17) + `Languistic theories/محمد عنبر/` | Golden Rule examples, 3 letter meanings |
| **Khashim's 9 sound laws** | Main theory doc (section 18) + `Languistic theories/علي فهمي خشيم/` | Full shift table |
| **24 BAB xlsx files** | `Muajam Ishtiqaqi/Tables_Juthoor/` | Raw Jabal data for all letters |
| **Muajam summaries** | `Muajam Ishtiqaqi/Summaries/` | 3 methodology documents |
| **Atomic feature vocabulary** | `LV1_ARCHITECTURE_VISION.md` Section 6.2 | 9 categories, ~50 features |

---

## Phase 1: Letter Atoms (الحروف) — PARALLEL START

### Codex Wave 1A (start immediately)

| Task | Input | Output | Notes |
|------|-------|--------|-------|
| **C1.1** Parse Jabal's 28 letter table | Appendix A of VISION.md | `data/theory_canon/letters/jabal_letters.jsonl` | Extract letter, name, raw Arabic description, decompose into atomic features |
| **C1.2** Parse Neili's 10 letter table | Section 13 of main theory doc | `data/theory_canon/letters/neili_letters.jsonl` | 10 letters with physical movement meanings |
| **C1.3** Parse Abbas's classification | Section 8 of main theory doc | `data/theory_canon/letters/abbas_letters.jsonl` | 28 letters with sensory categories + detailed descriptions |
| **C1.4** Parse Asim al-Masri's table | `جدول معاني الحروف _.md` + theory doc section 14 | `data/theory_canon/letters/asim_letters.jsonl` | 28 letters with dialectical contradiction meanings |
| **C1.5** Parse Anbar's letter values | Section 17 of theory doc + `جدلية الحرف العربي.md` | `data/theory_canon/letters/anbar_letters.jsonl` | ~20 letters with dialectical meanings |
| **C1.6** Build atomic feature decomposition engine | VISION.md Section 6.2 (9 categories) | `src/juthoor_arabicgenome_lv1/core/feature_decomposition.py` | Takes Arabic text description → returns set of atomic features from the 50-feature vocabulary |
| **C1.7** Parse all 24 BAB xlsx files | `Tables_Juthoor/*.xlsx` | `data/theory_canon/binary_fields/jabal_nuclei_raw.jsonl` | Extract binary nuclei, member roots, shared meanings from ALL 24 files |

**Schema for letter JSONL:**
```json
{
  "letter": "ب",
  "letter_name": "الباء",
  "scholar": "jabal",
  "raw_description": "تجمع رخو مع تلاصق ما",
  "atomic_features": ["تجمع", "رخاوة", "تلاصق"],
  "feature_categories": ["gathering_cohesion", "texture_quality", "gathering_cohesion"],
  "sensory_category": null,
  "kinetic_gloss": null,
  "source_document": "المعجم الاشتقاقي المؤصل",
  "confidence": "high"
}
```

### Claude Wave 1B (parallel with Codex)

| Task | Input | Output | Notes |
|------|-------|--------|-------|
| **O1.1** Design canon_models.py dataclasses | VISION.md Section 7 | `src/juthoor_arabicgenome_lv1/core/canon_models.py` | LetterAtom, BinaryNucleus, TriliteralRoot, TheoryClaim, AtomicFeature |
| **O1.2** Design canon_loaders.py | Schema from C1.1-C1.5 | `src/juthoor_arabicgenome_lv1/core/canon_loaders.py` | Load all scholar letter files, merge into unified registry |
| **O1.3** Write Phase 1 acceptance tests | VISION.md goals | `tests/test_canon_phase1.py` | 28 letters x 5 scholars, feature decomposition works, no empty entries |
| **O1.4** Create theory_canon folder structure | Plan | `data/theory_canon/` with inbox, letters, binary_fields, roots subfolders |

### Phase 1 Gate
- All 28 letters have entries from Jabal (complete) + Abbas (complete) + Asim (complete) + Neili (10/28) + Anbar (~20/28)
- Feature decomposition engine works on all raw descriptions
- All 24 BAB files parsed into binary nuclei JSONL
- Tests pass

---

## Phase 2: Binary Nucleus Engine (الفصل المعجمي) — CODEX HEAVY

### Codex Wave 2A (after Phase 1 gate)

| Task | Input | Output | Notes |
|------|-------|--------|-------|
| **C2.1** Build composition Model A (Intersection) | Letter features + nuclei data | `src/.../factory/composition_models.py` | Feature set intersection + union weighting |
| **C2.2** Build composition Model B (Sequence) | Letter features + nuclei data | Same file | Ordered: letter1 features as subject, letter2 as predicate |
| **C2.3** Build composition Model C (Dialectical) | Letter features + nuclei data | Same file | Identify contradictions, resolve by synthesis |
| **C2.4** Build composition Model D (Phonetic-Gestural) | Articulatory features + nuclei | Same file | Makhraj+sifat → gestural combination |
| **C2.5** Build Method B scoring engine | VISION.md Section 6.2 | `src/.../factory/scoring.py` | Jaccard similarity on atomic features, weighted variant |
| **C2.6** Run full score matrix | 456 nuclei x 4 models x 5 scholars | `outputs/lv1_scoring/nucleus_score_matrix.json` | The big computation |
| **C2.7** Test Golden Rule (Anbar) | All reversible binary pairs | `outputs/lv1_scoring/golden_rule_report.json` | For each (X,Y) where (Y,X) exists: does meaning invert? |

### Claude Wave 2B (parallel — Method A calibration)

| Task | Input | Output | Notes |
|------|-------|--------|-------|
| **O2.1** Run Method A on 50 sample nuclei | Codex's predictions + Jabal's actuals | `outputs/lv1_scoring/method_a_calibration.json` | Claude scores 0-100 with reasoning |
| **O2.2** Compare Method A vs Method B | Both score sets | `outputs/lv1_scoring/calibration_report.md` | Identify where they agree/diverge, adjust weights |
| **O2.3** Review Golden Rule results | C2.7 output | Review document | Does reversal consistently invert meaning? |

### Phase 2 Gate
- Score matrix for all 456 nuclei exists
- Best composition model identified (overall + per phonetic class)
- Method A and Method B correlation > 0.7
- Golden Rule quantified

---

## Phase 3: Trilateral Root Prediction (الجذر الثلاثي) — CODEX HEAVY

### Codex Wave 3A

| Task | Input | Output | Notes |
|------|-------|--------|-------|
| **C3.1** Build root prediction engine | Best composition model + binary scores + letter features | `src/.../factory/root_predictor.py` | Binary nucleus meaning + third letter modification → predicted root meaning |
| **C3.2** Run prediction on all 1,924 roots | Nucleus scores + letter data | `outputs/lv1_scoring/root_predictions.json` | Predicted vs Jabal's actual المعنى المحوري |
| **C3.3** Score all predictions (Method B) | Predictions + actuals | `outputs/lv1_scoring/root_score_matrix.json` | Per-root, per-BAB, overall accuracy |
| **C3.4** Analyze failure patterns | Low-scoring roots | `outputs/lv1_scoring/failure_analysis.md` | Which roots fail? Why? Systematic patterns? |

### Claude Wave 3B

| Task | Input | Output | Notes |
|------|-------|--------|-------|
| **O3.1** Method A calibration on 50 root samples | Root predictions | Calibration scores | Same as Phase 2 but for trilateral roots |
| **O3.2** Review failure analysis | C3.4 output | Recommendations | Which composition model modifications would fix failures? |

### Phase 3 Gate
- Root prediction accuracy > 60% (target from VISION.md)
- Per-BAB accuracy distribution known
- Failure patterns identified and documented

---

## Phase 4: Abbas Sensory Validation — PARALLEL

### Codex Wave 4A

| Task | Input | Output | Notes |
|------|-------|--------|-------|
| **C4.1** Test same-category nucleus behavior | Abbas categories + composition results | Statistical analysis | Do same-sensory-category nuclei compose differently? |
| **C4.2** Test إيماء vs إيحاء | Abbas dual mechanism | Correlation analysis | Does composition model accuracy differ by mechanism? |

### Claude Wave 4B

| Task | Input | Output | Notes |
|------|-------|--------|-------|
| **O4.1** Review sensory validation results | C4.1-C4.2 | Validation report | Does Abbas's classification predict composition behavior? |

---

## Phase 5: Intra-Semitic Extension — CODEX HEAVY

### Codex Wave 5A

| Task | Input | Output | Notes |
|------|-------|--------|-------|
| **C5.1** Implement Khashim's 9 sound laws | Theory doc section 18 | `src/.../factory/sound_laws.py` | ف↔P, ق↔C/K/G, etc. as transformation functions |
| **C5.2** Project Arabic root meanings → Hebrew/Aramaic | Sound laws + root data + LV0 Hebrew/Aramaic data | Predicted cognate meanings | Does the meaning survive the phonetic shift? |
| **C5.3** Score projections against LV2 benchmark | Predictions + gold benchmark | Cross-validation report | How well do LV1 root meanings predict LV2 cognate pairs? |

---

## Execution Timeline (No Stops)

```
CODEX ──────────────────────────────────────────────────────────────
  C1.1-C1.5 parse letters ─┐
  C1.6 feature decomp      ├→ C2.1-C2.4 composition models ─→ C3.1-C3.4 root prediction
  C1.7 parse 24 BAB xlsx  ─┘  C2.5 scoring engine              C3.2 run all 1924 roots
                               C2.6 full matrix (BIG)           C3.3 score all
                               C2.7 golden rule                 C3.4 failure analysis
                                                              ─→ C4.1-C4.2 Abbas validation
                                                              ─→ C5.1-C5.3 Semitic extension

CLAUDE ─────────────────────────────────────────────────────────────
  O1.1-O1.4 schemas+tests ─→ O2.1 Method A 50 sample ─→ O3.1 Method A roots
                               O2.2 calibration          O3.2 failure review
                               O2.3 golden rule review    O4.1 sensory review
```

**Key:** Codex never waits for Claude. Each Codex wave has enough work to stay busy. Claude reviews happen in parallel and feed into the next calibration cycle.

---

## Immediate Start Instructions

### For Codex (start NOW):

**Priority order:**
1. **C1.7** — Parse all 24 BAB xlsx files into `jabal_nuclei_raw.jsonl` (biggest data extraction)
2. **C1.1** — Parse Jabal's 28 letters from VISION.md Appendix A into JSONL
3. **C1.6** — Build feature decomposition engine using the 9-category vocabulary
4. **C1.2-C1.5** — Parse remaining scholars' letter tables
5. Then immediately start **C2.1-C2.5** — composition models and scoring engine

**Read these files first:**
- `Juthoor-ArabicGenome-LV1/docs/The Arabic Tongue (nature-genome-application)/LV1_ARCHITECTURE_VISION.md`
- `Juthoor-ArabicGenome-LV1/docs/The Arabic Tongue (nature-genome-application)/ملخص_الدلالة_الصوتية_العربية.md`
- All files in `Languistic theories/` subfolders

### For Claude (start NOW):

1. **O1.1** — Design canon_models.py with dataclasses from VISION.md Section 7
2. **O1.2** — Design canon_loaders.py
3. **O1.3** — Write acceptance tests
4. **O1.4** — Create theory_canon folder structure

---

## Quality Gates

1. Every letter entry has raw Arabic description + atomic features + source scholar
2. Every binary nucleus has shared meaning from Jabal + 4 model predictions + scores
3. Method A and Method B scores correlate > 0.7
4. Golden Rule quantified with confidence interval
5. All existing 275 LV1 tests still pass
6. New tests for every new module

---

## Success Metrics (from VISION.md)

| Metric | Target | Phase |
|--------|--------|-------|
| Binary nucleus prediction accuracy (best model) | >70% | Phase 2 |
| Trilateral root prediction accuracy | >60% | Phase 3 |
| Golden Rule confirmation rate | Quantified % | Phase 2 |
| Method A ↔ Method B correlation | >0.8 | Phase 2 |
| Abbas sensory grouping significance | p < 0.05 | Phase 4 |

---

*LV1 Execution Orchestration*
*Juthoor Linguistic Genealogy*
*2026-03-22*
