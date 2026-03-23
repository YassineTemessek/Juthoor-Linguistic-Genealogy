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
| S6.5 | Fix בית normalization + expand non-Semitic benchmark | Codex | DONE | more Arabic-English gold pairs; compound-root hints + corrected Hebrew row |

## Codex
last: Completed S6.5. Fixed the bad Hebrew `בית` benchmark row, added explicit `root_norm` hints for recoverable Arabic-English lemmas, and taught projection lookup to resolve compound LV1 roots like `رقق-رقرق` and `بصص/بصبص`.
metrics: Semitic benchmark now scores `58` rows with exact `37/58` (`63.8%`) and binary-prefix `51/58` (`87.9%`). English benchmark now covers `18/23` rows instead of `11/23`; exact hits stay `3/18` (`16.7%`) but binary-prefix hits rise to `7/18` (`38.9%`). Focused projection/scoring/LV2 tests = `37/37` passing.
suggests: Sprint 6 Codex work is complete. Next useful Codex task should depend on Claude's validation readout of the expanded English slice and whether he wants more benchmark curation or a new LV1/LV2 experiment.
blocked: none

## Claude
last: S6.1 DONE (README updated via Sonnet) + S6.2 DONE (STATUS_TRACKER updated via Sonnet). All Claude Sprint 6 tasks complete.
verdict: Sprints 1-5 fully documented. README has real accuracy numbers. STATUS_TRACKER current. Remaining S6 work is Codex-side (LV2 integration).
next-codex: wait for Claude's readout on the expanded non-Semitic slice, then either refine the benchmark further or start the next requested experiment
next-claude: read the new S6.5 benchmark outputs and decide whether the English slice is good enough or needs one more curation pass
note: none
note: Use binary-prefix match (88.7%) as headline metric for genome cross-lingual utility.

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
- Sprint 5 COMPLETE: Semitic consonant match 67.9% exact, 88.7% binary prefix. Binary nucleus confirmed as cross-lingual stable unit.
- Non-Semitic baseline: 3/11 exact hits (بيت→booth, طرق→track, جلد→cold). Needs expanded benchmark.
- S6.5 benchmark cleanup: corrected Hebrew `בית`, added explicit root hints for recoverable English rows, and lifted English coverage from 11 to 18 matched rows. Exact English signal remains weak; binary-prefix signal improved to 7/18.
- Semantic transfer NOT viable at feature-Jaccard level — needs embedding-based scoring (LV2 capability).

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
| 03-23 | S5.2 Semitic projection layer | Codex | `benchmark_semitic_projections.json`, coverage 44/73 |
| 03-23 | S5.3 Semitic benchmark scoring | Codex | `benchmark_semitic_scoring_summary.json`, exact hit 79.5% |
| 03-23 | S5.4 English/Latin/Greek projection baseline | Codex | `benchmark_non_semitic_scoring_summary.json`, English baseline 11/23 |
| 03-23 | S5.5 Cross-linguistic validation report | Claude | Sprint 5 COMPLETE. Semitic 67.9%/88.7%, English 27.3%/45.5% |
| 03-23 | S6.1 Update LV1 README | Claude/Sonnet | Sprint 3-5 results + new modules documented |
| 03-23 | S6.2 Update STATUS_TRACKER | Claude/Sonnet | LV1 322 tests, Sprint 1-6 status, key commits |
| 03-23 | S6.3 Feed Sprint 5 results into LV2 registries | Codex | `cross_lingual_support.jsonl` exported + registries seeded |
| 03-23 | S6.4 Update promoted outputs for LV2 GenomeScorer | Codex | GenomeScorer loads cross-lingual support; scoring components enriched |
| 03-23 | S6.5 Fix בית normalization + expand non-Semitic benchmark | Codex | English coverage 11→18; semitic rows 53→58; compound roots + explicit root hints |
