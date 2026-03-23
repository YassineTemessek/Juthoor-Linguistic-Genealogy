# LV1 Phase 2-3 Orchestration — Continuous Work Plan

**Date:** 2026-03-23
**Status:** ACTIVE
**Last checkpoint:** Sprint 5 projection work is active; Sprint 3 is closed and Sprint 5 evaluation is underway

---

## Current State

| Asset | Count | Status |
|-------|-------|--------|
| Jabal letters | 28/28 | Complete |
| Abbas letters | 28/28 | Complete |
| Asim letters | 28/28 | Complete |
| Neili letters | 10/28 | Complete (he only covered 10) |
| Anbar letters | 3/28 | Main source still too prose-heavy for reliable large-scale extraction |
| Binary nuclei | 457 | Loaded, scored (first pass) |
| Trilateral roots | 1,938 | Loaded, predicted (first pass) |
| Score matrix rows | 4,792 | 1,005 nonzero (21.0%) |
| Root prediction rows | 1,938 | 782 nonzero Jaccard (40.4%), 1092 nonzero blended (56.3%) |
| Root prediction mean Jaccard | 0.1457 | Precision-capped rerun after S3.14-S3.17 |
| Method A estimate | 40-55% real accuracy | Method B undercounts due to vocabulary mismatch |
| Golden Rule | 19.9% confirmed (33/166) | Improved after extended opposition mapping |
| Tests passing | 313+ LV1 and growing | Focused Sprint 1/3 suite currently 34/34 |

---

## Task Queue — Execute Top to Bottom

Each task has an owner. Work the next unblocked item and update status directly in the shared board.

### SPRINT 1: Scoring Fixes (Codex heavy)

| # | Task | Owner | Depends | Output | Done? |
|---|------|-------|---------|--------|-------|
| S1.1 | **Add synonym groups to scoring engine** | Codex | Nothing | Updated `scoring.py` with SYNONYM_GROUPS mapping | [x] |
| | Groups needed: امتداد↔طول, تفشّي↔انتشار, دقة↔رقة↔لطف, تعقد↔كثافة, اكتناز↔تجمع, خروج↔بروز↔ظهور, احتباس↔ضغط, نفاذ↔اختراق | | | | |
| | Jaccard scoring should treat synonyms as the same feature | | | | |
| S1.2 | **Fix empty actual_features extraction** | Codex | Nothing | Updated `feature_decomposition.py` | [x] |
| | Many nuclei have Jabal meaning text but 0 extracted features. Scan ALL Jabal shared meanings against the full 50-feature vocab + synonyms | | | | |
| S1.3 | **Add semantic opposition mapping** | Codex | Nothing | `SEMANTIC_OPPOSITES` dict in scoring.py | [x] |
| | تجمع↔تفرق, ضغط↔فراغ, نقص↔اتساع, باطن↔ظاهر, قوة↔رخاوة, غلظ↔رقة, خروج↔دخول | | | | |
| S1.4 | **Re-run full score matrix** | Codex | S1.1+S1.2 | Updated `nucleus_score_matrix.json` | [x] |
| S1.5 | **Re-run Golden Rule with opposition matching** | Codex | S1.3 | Updated `golden_rule_report.json` | [x] |
| S1.6 | **Push all Sprint 1 outputs** | Codex | S1.4+S1.5 | Commit to main | [x] |
| S1.7 | **Pull and verify improvement** | Claude | S1.6 | Compare old vs new and write verification report | [x] |
| S1.8 | **Method A re-calibration on 50 nuclei** | Claude | S1.6 | Updated `method_a_calibration.md` | [x] |

**Sprint 1 result:** Nonzero Jaccard improved from 14.4% to 21.0%. Golden Rule improved from 17.5% to 19.9%. Zero-feature nuclei fell to 29.

### SPRINT 2: Anbar Extraction + Scholar Comparison (Codex heavy)

| # | Task | Owner | Depends | Output | Done? |
|---|------|-------|---------|--------|-------|
| S2.1 | **Extract Anbar letters from جدلية الحرف العربي.md** | Codex | Nothing (parallel with S1) | Updated `anbar_letters.jsonl` 3→20+ | [ ] |
| S2.2 | **Extract Anbar from main theory doc sections** | Codex | Nothing | Additional letter meanings from sections 17 | [ ] |
| S2.3 | **Re-run score matrix with Anbar data** | Codex | S2.1+S1.4 | New Anbar entries in matrix | [ ] |
| S2.4 | **Cross-scholar comparison report** | Claude | S2.3 | Which scholar's letters predict best per phonetic class? | [ ] |

**Sprint 2 note:** A direct pass on `جدلية الحرف العربي.md` found real semantic clues but not enough explicit letter-level statements to support a reliable canon expansion beyond the current 3 Anbar rows. Sprint 2 remains open, but it is no longer the best use of active Codex time until a better source or a cleaner extraction path appears.

### SPRINT 3: Phase 3 — Root Prediction (Codex heavy)

| # | Task | Owner | Depends | Output | Done? |
|---|------|-------|---------|--------|-------|
| S3.1 | **Build root prediction engine** | Codex | S1.6 (scoring fixes landed) | `src/.../factory/root_predictor.py` | [x] |
| | Strategy: for each of 1,924 roots, get binary nucleus meaning + third letter features → predict المعنى المحوري | | | | |
| | Use Intersection model primarily, Phonetic-Gestural fallback if empty | | | | |
| | Apply synonym-aware scoring | | | | |
| S3.2 | **Run prediction on all 1,924 roots** | Codex | S3.1 | `outputs/lv1_scoring/root_predictions.json` | [x] |
| S3.3 | **Score all predictions (Method B)** | Codex | S3.2 | `outputs/lv1_scoring/root_score_matrix.json` | [x] |
| | Per-root, per-BAB, overall accuracy | | | | |
| S3.4 | **Identify top/bottom predictions** | Codex | S3.3 | Top 50 best, bottom 50 worst, with Jabal meanings | [x] |
| S3.5 | **Push Phase 3 outputs** | Codex | S3.4 | Commit to main | [ ] |
| S3.6 | **Method A calibration on 60 root predictions** | Claude | S3.5 | `outputs/lv1_scoring/root_method_a_calibration.md` | [x] |
| S3.7 | **Failure pattern analysis** | Claude | S3.5 | 6 patterns: phon_gest dominance, feature truncation, sifaat contamination, empty actuals, synonym gaps, BAB variance | [x] |
| S3.8 | **Phase 3 verdict** | Claude | S3.6+S3.7 | Method A ~32% (target >55%). Bottleneck = composition model. 6 recommendations (R1-R6). | [x] |
| S3.9 | **Implement R1+R3 (fix phonetic_gestural)** | Codex | S3.8 | Use all features, drop sifaat, weight nucleus 0.7 | [x] |
| S3.10 | **Implement R2 (expand synonyms)** | Codex | S3.8 | 5 new synonym groups | [x] |
| S3.11 | **Implement R4 (recover empty-actual)** | Codex | S3.8 | 207→139 roots recovered | [x] |
| S3.12 | **Re-run predictions after fixes** | Codex | S3.9+S3.10+S3.11 | nonzero 692→899, mean_J 0.135→0.150 | [x] |
| S3.13 | **Method A re-calibration v2** | Claude | S3.12 | Method A ~33.8% (+1.4pp). Phon_gest over-predicts. | [x] |
| S3.14 | **R7: Cap phonetic_gestural to 2+1 features** | Claude | S3.13 | `composition_models.py` — precision filter | [x] |
| S3.15 | **R9: Targeted empty-actual Quranic extraction** | Codex | S3.13 | 50 high-value roots | [x] |
| S3.16 | **R10: Category-level blended_jaccard** | Claude | S3.13 | `scoring.py` — 0.7*feat + 0.3*category | [x] |
| S3.17 | **Re-run predictions after S3.14-S3.16** | Codex | S3.14+S3.15+S3.16 | Updated outputs | [x] |
| S3.18 | **Method A v3 calibration** | Claude | S3.17 | Method A ~36.7%, blended 0.175, 56.3% coverage. **SPRINT 3 CLOSED.** | [x] |

**Sprint 3 final result:** Method A ~36.7% (target was >55%). Blended Jaccard 0.175 with 56.3% nonzero blended coverage. Precision cap improved partial-low band from 42→52 Method A. 310 category-only matches revealed by blended metric. Ceiling ~40-45% without neural/embedding models. Sprint 3 closed — LV1 genome accepted as hypothesis generator for Sprint 5 cross-lingual projection.

**Report:** `outputs/lv1_scoring/root_method_a_calibration_v3.md`

### SPRINT 4: Abbas Sensory Validation (parallel with Sprint 3)

| # | Task | Owner | Depends | Output | Done? |
|---|------|-------|---------|--------|-------|
| S4.1 | **Group nuclei by Abbas sensory categories** | Codex | S1.6 | Analysis: do same-category nuclei score differently? | [x] |
| S4.2 | **Test إيماء vs إيحاء composition accuracy** | Codex | S1.6 | Does mechanism type predict which model works best? | [x] |
| S4.3 | **Sensory validation report** | Claude | S4.1+S4.2 | Abbas NOT a scoring prior; ذوقية+لمسية strongest; إيماء+إيماء weakest. Parked. | [x] |

**Sprint 4 checkpoint:** `outputs/lv1_scoring/abbas_sensory_validation.md` is now written. Current result does **not** support a simple Abbas same-category advantage in the mechanical nucleus matrix: same-category rows underperform mixed rows (`0.0234` vs `0.0311` mean Jaccard), and pure `إيماء + إيماء` rows scored `0/36` nonzero in this pass.

### SPRINT 5: Intra-Semitic Extension (after Sprint 3)

| # | Task | Owner | Depends | Output | Done? |
|---|------|-------|---------|--------|-------|
| S5.1 | **Implement Khashim's 9 sound laws** | Codex | S3.8 (Phase 3 done) | `src/.../factory/sound_laws.py` | [x] |
| | ف↔P, ق↔C/K/G, ط↔T, ص↔S, ش↔S, ح↔K/C/H, ع→drop, غ→G, خ→H/G | | | | |
| S5.2 | **Project Arabic root meanings → Hebrew/Aramaic** | Codex | S5.1 | Predicted cognate meanings via sound laws | [x] |
| S5.3 | **Score projections against LV2 benchmark** | Codex | S5.2 | Cross-validation: do LV1 meanings predict LV2 cognates? | [ ] |
| S5.4 | **Project Arabic root meanings → English/Latin/Greek** | Codex | S5.1 | Using Khashim's + Beyond the Word consonant shifts | [ ] |
| S5.5 | **Cross-linguistic validation report** | Claude | S5.3+S5.4 | Do Arabic root predictions survive cross-linguistically? | [ ] |

**Sprint 5 checkpoint:** `factory/sound_laws.py` is now live, and `factory/cross_lingual_projection.py` materializes the first benchmark-aligned Semitic projection set. Current direct Arabic benchmark coverage is `44/73` pairs (`60.3%`): `32` Hebrew and `12` Aramaic rows written to `outputs/lv1_scoring/benchmark_semitic_projections.json`.

### SPRINT 6: Integration + Cleanup

| # | Task | Owner | Depends | Output | Done? |
|---|------|-------|---------|--------|-------|
| S6.1 | **Update LV1 README with Phase 2-3 results** | Claude | S3.8 | Updated README with real accuracy numbers | [ ] |
| S6.2 | **Update STATUS_TRACKER** | Claude | S3.8 | Current state of all tasks | [ ] |
| S6.3 | **Update LV1_COMPLETE_OVERVIEW.md** | Claude | S3.8 | For external reference | [ ] |
| S6.4 | **Feed LV1 results back to LV2 registries** | Codex | S3.8 | Update Binary Field + Root registries with scores | [ ] |
| S6.5 | **Update promoted outputs for LV2 GenomeScorer** | Codex | S6.4 | Refreshed coherence scores, positional profiles | [ ] |

---

## Execution Timeline

```
CODEX (fast, heavy computation) ────────────────────────────────────

Sprint 1 (NOW):
  S1.1 synonym groups ──┐
  S1.2 fix empty features├→ S1.4 re-run matrix ─→ S1.6 PUSH
  S1.3 opposition mapping┘  S1.5 re-run golden rule

Sprint 2 (still open, lower priority until source quality improves):
  S2.1+S2.2 Anbar extraction ─→ S2.3 re-run with Anbar

Sprint 3 (active):
  S3.1 root predictor ─→ S3.2 run 1938 roots ─→ S3.3 score ─→ S3.4 top/bottom ─→ S3.5 PUSH

Sprint 4 (parallel with S3):
  S4.1+S4.2 Abbas sensory tests

Sprint 5 (after S3):
  S5.1 Khashim sound laws ─→ S5.2 project to Hebrew ─→ S5.3+S5.4 cross-lingual

Sprint 6:
  S6.4+S6.5 integration


CLAUDE (semantic review, architecture) ─────────────────────────────

Sprint 1:
  (wait for S1.6) ─→ S1.7 verify ─→ S1.8 re-calibrate

Sprint 2:
  (wait for S2.3) ─→ S2.4 scholar comparison

Sprint 3:
  (wait for S3.5) ─→ S3.6 Method A roots ─→ S3.7 failure analysis ─→ S3.8 verdict

Sprint 4:
  (wait for S4.1+S4.2) ─→ S4.3 sensory report

Sprint 5:
  (wait for S5.3+S5.4) ─→ S5.5 cross-lingual report

Sprint 6:
  S6.1+S6.2+S6.3 documentation updates
```

---

## Communication Protocol

1. Update the dispatch board in `docs/plans/BOARD.md` (old board archived at `AGENT_COORDINATION_ARCHIVE.md`)
2. Push completed work to `main`
3. Read the board at the next session start and continue from the next unblocked task
4. Document unexpected results in the relevant output/report file

---

## Decision Points Already Made

| Decision | Answer | Basis |
|----------|--------|-------|
| Best composition model | Intersection (Phonetic-Gestural fallback) | Method A calibration: 0.463 mean, highest quality |
| Primary letter values | Jabal's 28 | Most complete dataset, designed for composition |
| Scoring method | Method B (Jaccard) calibrated by Method A (Claude) | Method A shows B undercounts by ~3x |
| Golden Rule status | Plausible but underpowered | 17.5% on testable pairs, needs opposition mapping |
| Feature vocabulary | VISION.md Section 6.2 (~50 terms) + synonym expansion | Direct from Jabal's descriptive vocabulary |

---

## Success Metrics

| Metric | Current | Target | Sprint |
|--------|---------|--------|--------|
| Nonzero Jaccard (nuclei) | 21.0% | 30-40% | Sprint 1 |
| Golden Rule confirmation | 19.9% | 25-35% | Sprint 1 |
| Root prediction (Method B) | 14.6% (40.4% nonzero) | >30% | Sprint 3 — CLOSED |
| Root prediction (Method A) | ~36.7% | >55% | Sprint 3 — CLOSED, ceiling ~40-45% |
| Root prediction (blended) | 17.5% (56.3% nonzero) | — | Sprint 3 — new primary metric |
| Abbas sensory significance | — | p < 0.05 | Sprint 4 |
| Cross-lingual projection accuracy | — | >40% | Sprint 5 |
| Scholar coverage | 78 letters / 5 scholars | 100+ / 5 scholars | Sprint 2 |

---

## Files Both Agents Must Read

| File | What | When |
|------|------|------|
| **This file** | Task queue and current stage | At session start when resuming work |
| `outputs/lv1_scoring/method_a_calibration.md` | Claude's semantic assessment | Codex: understand what Method B misses |
| `outputs/lv1_scoring/golden_rule_verdict.md` | Golden Rule + model recommendation | Codex: use recommended model for Phase 3 |
| `LV1_ARCHITECTURE_VISION.md` | Full architecture and scoring methods | Both: reference for any design question |
| `data/theory_canon/SCHEMA.md` | JSONL formats | Codex: for any data file creation |

---

*LV1 Phase 2-3 Orchestration*
*Updated: 2026-03-23*
*Next update: after Sprint 1 push*
