# LV1 Phase 2-3 Orchestration — Continuous Work Plan

**Date:** 2026-03-23
**Status:** ACTIVE
**Last checkpoint:** Sprint 1 scoring fixes landed; next work continues from the task queue below

---

## Current State

| Asset | Count | Status |
|-------|-------|--------|
| Jabal letters | 28/28 | Complete |
| Abbas letters | 28/28 | Complete |
| Asim letters | 28/28 | Complete |
| Neili letters | 10/28 | Complete (he only covered 10) |
| Anbar letters | 3/28 | Needs extraction |
| Binary nuclei | 457 | Loaded, scored (first pass) |
| Trilateral roots | 1,938 | Loaded, NOT predicted yet |
| Score matrix rows | 4,792 | 1,005 nonzero (21.0%) |
| Method A estimate | 40-55% real accuracy | Method B undercounts due to vocabulary mismatch |
| Golden Rule | 19.9% confirmed (33/166) | Improved after extended opposition mapping |
| Tests passing | 313+ LV1 and growing | Focused Sprint 1 suite currently 26/26 |

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

### SPRINT 3: Phase 3 — Root Prediction (Codex heavy)

| # | Task | Owner | Depends | Output | Done? |
|---|------|-------|---------|--------|-------|
| S3.1 | **Build root prediction engine** | Codex | S1.6 (scoring fixes landed) | `src/.../factory/root_predictor.py` | [ ] |
| | Strategy: for each of 1,924 roots, get binary nucleus meaning + third letter features → predict المعنى المحوري | | | | |
| | Use Intersection model primarily, Phonetic-Gestural fallback if empty | | | | |
| | Apply synonym-aware scoring | | | | |
| S3.2 | **Run prediction on all 1,924 roots** | Codex | S3.1 | `outputs/lv1_scoring/root_predictions.json` | [ ] |
| S3.3 | **Score all predictions (Method B)** | Codex | S3.2 | `outputs/lv1_scoring/root_score_matrix.json` | [ ] |
| | Per-root, per-BAB, overall accuracy | | | | |
| S3.4 | **Identify top/bottom predictions** | Codex | S3.3 | Top 50 best, bottom 50 worst, with Jabal meanings | [ ] |
| S3.5 | **Push Phase 3 outputs** | Codex | S3.4 | Commit to main | [ ] |
| S3.6 | **Method A calibration on 50 root predictions** | Claude | S3.5 | `outputs/lv1_scoring/root_method_a_calibration.md` | [ ] |
| S3.7 | **Failure pattern analysis** | Claude | S3.5 | Which roots fail? Why? Systematic patterns? | [ ] |
| S3.8 | **Phase 3 verdict** | Claude | S3.6+S3.7 | Root prediction accuracy verdict + recommendations | [ ] |

**Target:** Root prediction accuracy >60% Method A, >30% Method B (after synonym fix)

### SPRINT 4: Abbas Sensory Validation (parallel with Sprint 3)

| # | Task | Owner | Depends | Output | Done? |
|---|------|-------|---------|--------|-------|
| S4.1 | **Group nuclei by Abbas sensory categories** | Codex | S1.6 | Analysis: do same-category nuclei score differently? | [ ] |
| S4.2 | **Test إيماء vs إيحاء composition accuracy** | Codex | S1.6 | Does mechanism type predict which model works best? | [ ] |
| S4.3 | **Sensory validation report** | Claude | S4.1+S4.2 | Does Abbas's classification predict composition behavior? | [ ] |

### SPRINT 5: Intra-Semitic Extension (after Sprint 3)

| # | Task | Owner | Depends | Output | Done? |
|---|------|-------|---------|--------|-------|
| S5.1 | **Implement Khashim's 9 sound laws** | Codex | S3.8 (Phase 3 done) | `src/.../factory/sound_laws.py` | [ ] |
| | ف↔P, ق↔C/K/G, ط↔T, ص↔S, ش↔S, ح↔K/C/H, ع→drop, غ→G, خ→H/G | | | | |
| S5.2 | **Project Arabic root meanings → Hebrew/Aramaic** | Codex | S5.1 | Predicted cognate meanings via sound laws | [ ] |
| S5.3 | **Score projections against LV2 benchmark** | Codex | S5.2 | Cross-validation: do LV1 meanings predict LV2 cognates? | [ ] |
| S5.4 | **Project Arabic root meanings → English/Latin/Greek** | Codex | S5.1 | Using Khashim's + Beyond the Word consonant shifts | [ ] |
| S5.5 | **Cross-linguistic validation report** | Claude | S5.3+S5.4 | Do Arabic root predictions survive cross-linguistically? | [ ] |

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

Sprint 2 (parallel with S1):
  S2.1+S2.2 Anbar extraction ─→ S2.3 re-run with Anbar

Sprint 3 (after S1.6):
  S3.1 root predictor ─→ S3.2 run 1924 roots ─→ S3.3 score ─→ S3.4 top/bottom ─→ S3.5 PUSH

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

1. Update the shared board in `docs/plans/AGENT_COORDINATION.md`
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
| Root prediction (Method B) | — | >30% | Sprint 3 |
| Root prediction (Method A) | — | >55% | Sprint 3 |
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
