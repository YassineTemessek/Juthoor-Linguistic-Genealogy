# Board
<!-- ============================================================ -->
<!-- PROTOCOL — both agents MUST follow on EVERY task completion   -->
<!--                                                              -->
<!-- 1. MICRO-UPDATE after EACH task (not batch):                 -->
<!--    - Move your finished task to DONE in Tasks table          -->
<!--    - Overwrite your section (last, metrics, suggests, etc.)  -->
<!--    - Update the orchestration plan if metrics/status changed -->
<!--    - git add BOARD.md + orchestration plan, commit, push     -->
<!--                                                              -->
<!-- 2. BEFORE starting work, ALWAYS:                             -->
<!--    - git pull                                                -->
<!--    - Read BOARD.md — check the OTHER agent's section         -->
<!--    - Pick the top NEXT task assigned to you                  -->
<!--    - If the other agent's output unblocks you, start it      -->
<!--                                                              -->
<!-- 3. Your role (Yassin): just pull, read board, say "ok" or    -->
<!--    redirect. No need to explain what the other AI did.       -->
<!--                                                              -->
<!-- 4. Files to micro-update together:                           -->
<!--    - docs/plans/BOARD.md (always)                            -->
<!--    - docs/plans/2026-03-23-lv1-phase2-3-orchestration.md     -->
<!--      (if metrics, status, or checkpoint text changed)        -->
<!--                                                              -->
<!-- 5. Status values: NEXT / WIP / DONE / BLOCKED               -->
<!-- 6. Max 15 active rows. DONE tasks move to Archive.           -->
<!-- 7. Archive is append-only safety trail.                      -->
<!-- ============================================================ -->

## Tasks
| # | Task | Owner | Status | Output |
|---|------|-------|--------|--------|
| S5.3 | Score projections against LV2 benchmark (73 Semitic gold pairs) | Codex | NEXT | cross-validation output |
| S5.4 | Project Arabic root meanings → English/Latin/Greek | Codex | NEXT | Khashim + Beyond the Word shifts |
| S5.5 | Cross-linguistic validation report | Claude | BLOCKED | do LV1 predictions survive cross-linguistically? |

## Codex
last: Completed S5.2. Added `factory/cross_lingual_projection.py` and materialized benchmark Semitic projections at `outputs/lv1_scoring/benchmark_semitic_projections.json`.
metrics: direct Semitic benchmark coverage = 44/73 (60.3%) = 32 Hebrew + 12 Aramaic; `test_cross_lingual_projection.py` + `test_sound_laws.py` = 10/10 passing.
suggests: Sprint 5 is now in evaluation mode. Next Codex step is S5.3 scoring on the 44 matched Semitic rows, while S5.4 can begin in parallel if the Semitic scorer is straightforward.
blocked: none

## Claude
last: S3.18 DONE — Sprint 3 CLOSED. Method A v3 ~36.7% (target was >55%). Report at `root_method_a_calibration_v3.md`. Recommended closing Sprint 3 and moving to Sprint 5 cross-lingual validation.
verdict: LV1 genome is a hypothesis generator, not a proof engine. 37% Method A + 56% blended coverage = majority of roots have directionally correct predictions. Strong enough to project cross-linguistically.
next-codex: S5.2 → S5.3 → S5.4 (project Arabic roots to Hebrew/Aramaic/English via sound laws, score against LV2 benchmark)
next-claude: S5.5 cross-linguistic validation report after S5.3+S5.4.
note: Use `mean_blended_jaccard` (0.175) as primary automated metric going forward. Sprint 3 ceiling ~40-45% without neural/embedding models.

## Decided
- Best composition model: Intersection (Phonetic-Gestural fallback) — Method A calibration Sprint 1
- Primary letter values: Jabal's 28 — most complete, designed for composition
- Scoring: Method B (Jaccard) calibrated by Method A (Claude) — B undercounts ~1.7x
- Feature vocabulary: VISION.md Section 6.2 (~50 terms) + synonym expansion
- Sprint 2 Anbar: parked — source too prose-heavy for reliable extraction
- Root predictor routing: intersection if inputs share features, else phonetic_gestural, else sequence
- Phonetic_gestural went from under-prediction (v1: 2 features) to over-prediction (v2: 4-7). Fixed: precision cap at 2+1 features
- Abbas sensory categories: NOT a scoring prior. Do not add to pipeline. إيماء+إيماء pairs need manual review. Re-test after S3.17.
- Sprint 3 CLOSED at Method A ~36.7%, blended J 0.175, 56.3% blended coverage. Ceiling ~40-45% without neural models. Move to Sprint 5.
- Use blended_jaccard (0.7*feat + 0.3*category) as primary automated metric going forward.

## Archive
| Date | Task | Owner | Output |
|------|------|-------|--------|
| 03-23 | S1.1 Synonym groups | Codex | `scoring.py` |
| 03-23 | S1.2 Fix empty features | Codex | `feature_decomposition.py` |
| 03-23 | S1.3 Opposition mapping | Codex | `scoring.py` |
| 03-23 | S1.4 Re-run score matrix | Codex | `nucleus_score_matrix.json` |
| 03-23 | S1.5 Re-run Golden Rule | Codex | `golden_rule_report.json` |
| 03-23 | S1.6 Push Sprint 1 | Codex | commit `5fbd510` |
| 03-23 | S1.7 Verify improvement | Claude | `score_matrix_verification.md` |
| 03-23 | S1.8 Method A re-calibration | Claude | `method_a_calibration_v2.md` |
| 03-23 | S3.1 Build root predictor | Codex | `factory/root_predictor.py` |
| 03-23 | S3.2 Run prediction on all roots | Codex | `root_predictions.json` |
| 03-23 | S3.3 Score root predictions | Codex | `root_score_matrix.json` |
| 03-23 | S3.4 Identify top/bottom | Codex | in `root_score_matrix.json` |
| 03-23 | S3.6 Method A root calibration | Claude | `root_method_a_calibration.md` |
| 03-23 | S3.7 Failure pattern analysis | Claude | 6 patterns in calibration report |
| 03-23 | S3.8 Phase 3 verdict | Claude | Method A ~32%, 6 recommendations |
| 03-23 | S3.9 Fix phonetic_gestural | Codex | full-feature fallback, no sifaat noise |
| 03-23 | S3.10 Expand root synonyms | Codex | updated `scoring.py` |
| 03-23 | S3.11 Recover empty-actual roots | Codex | `feature_decomposition.py`, 207→139 |
| 03-23 | S3.12 Re-run improved root predictions | Codex | nonzero 692→899, `root_score_matrix.json` |
| 03-23 | S3.13 Method A v2 calibration | Claude | Method A ~33.8%, new recs R7-R10 |
| 03-23 | S3.14 Cap phonetic_gestural to 2+1 features | Claude | `composition_models.py` |
| 03-23 | S3.16 Category-level blended_jaccard | Claude | `scoring.py`, 0.7*feat+0.3*cat |
| 03-23 | S3.15 Quranic empty-actual extraction | Codex | `feature_decomposition.py`, empty_actual 139→113 |
| 03-23 | S3.17 Re-run with S3.14+S3.15+S3.16 | Codex | `root_predictions.json`, `root_score_matrix.json`, blended metrics live |
| 03-23 | S4.1 Abbas sensory grouping stats | Codex | no same-category lift in current matrix |
| 03-23 | S4.2 عباس إيماء vs إيحاء test | Codex | `إيماء+إيماء` weakest block; report written |
| 03-23 | S4.3 Abbas sensory verdict | Claude | NOT a scoring prior; park as "not yet validated" |
| 03-23 | S3.18 Method A v3 calibration | Claude | Sprint 3 CLOSED. Method A ~36.7%, blended 0.175 |
| 03-23 | S5.1 Khashim sound laws | Codex | `factory/sound_laws.py`, projection helpers + tests |
