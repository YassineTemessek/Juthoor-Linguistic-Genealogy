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
<!--    - docs/plans/2026-03-24-lv1-arabic-core-rebuild.md        -->
<!--      (if metrics, status, or checkpoint text changed)        -->
<!--                                                              -->
<!-- 5. Status values: NEXT / WIP / DONE / BLOCKED               -->
<!-- 6. Max 15 active rows. DONE tasks move to Archive.           -->
<!-- 7. Archive is append-only safety trail.                      -->
<!-- ============================================================ -->

## Tasks
| # | Task | Owner | Status | Output |
|---|------|-------|--------|--------|
| P1.1 | Audit root pipeline against canonical xlsx | Codex | DONE | `jabal_roots_raw.jsonl` rebuilt to `1924` roots / `1666` quranic / `456` nuclei |
| P1.2 | Re-extract Abbas 29 entries from ABBAS_LETTER_CLASSIFICATION.md | Codex+Claude | DONE | `hassan_abbas_letters.jsonl` rebuilt with `sensory_category` + `mechanism_type` |
| P1.3 | Extract Anbar 25 letters from LV1_VERIFIED_DATA_AUDIT.md | Codex | BLOCKED | visible audit table exposes `20` explicit + `4` contextual, while prose claims `25` and says only `ط/ث/ظ` are missing |
| P1.4 | Verify Asim al-Masri complete table (+ألف المد) | Codex | DONE | `asim_al_masri_letters.jsonl` rebuilt to `29` entries with `continues_neili` |
| P1.5 | Formalize Neili constraints as hard filters | Claude/Sonnet | DONE | `core/neili_constraints.py` + 29 tests |
| P3.4 | Synonym family extraction (seed + auto) | Claude/Sonnet | DONE | `factory/synonym_families.py` + 28 tests |
| P1.6 | Update letter registry with all 5 scholars | Codex | BLOCKED | depends on resolving Anbar source mismatch in P1.3 |

## Codex
last: P1.1, P1.2, and P1.4 are complete. Jabal now rebuilds directly from the canonical xlsx; Abbas now comes from `ABBAS_LETTER_CLASSIFICATION.md`; Asim now comes from the verified complete table with `continues_neili`.
metrics: roots=`1924`, quranic=`1666`, nuclei=`456`, Jabal letters=`28`, Abbas entries=`29`, Asim entries=`29`, Neili=`10`, Anbar still loaded=`3`, focused tests=`56/56`
suggests: Claude can review the rebuilt Jabal/Abbas/Asim outputs now. Next Codex task is either resolve the Anbar source inconsistency or proceed to P1.6 using the stable four-scholar set plus an explicit Anbar placeholder state.
blocked: P1.3 source mismatch. `LV1_VERIFIED_DATA_AUDIT.md` and `LV1_ARCHITECTURE_VISION.md` say Anbar is `25/28` with only `ط/ث/ظ` missing, but the visible extracted table currently exposes `20` explicit rows plus `4` contextual (`ج/ك/ت/غ`). `ذ` and `هـ` are implied by the prose but not documented in the visible table.

## Claude
last: P1.5 DONE (neili_constraints.py, 29 tests) + P3.4 DONE (synonym_families.py, 28 tests). 57 new tests, all passing. Also ran pre-P2.1 analysis: current scholar features have extraction artifacts (Asim overuses انتقال, Abbas overuses احتكاك+حدة). P1.2-P1.4 re-extraction is critical.
verdict: Claude-side Phase 1 infrastructure complete. Waiting for Codex P1.1-P1.4 to land corrected scholar data before P2.1 comparison.
next-codex: P1.1 + P1.2 + P1.3 + P1.4 (all parallel)
next-claude: P2.1 scholar comparison after Codex delivers corrected letter data
note: Pre-analysis shows only 2/28 letters have strong cross-scholar agreement with CURRENT data. This will improve dramatically after re-extraction.

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
- Final English diagnostic: `non_semitic_gap_report.md` classifies the remaining misses as reduced-form derivation gaps, unmodeled sound-law gaps, or benchmark rows that are not fair direct exact-match targets.
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
| 03-23 | S6.6 English gap diagnosis | Codex | `non_semitic_gap_report.md`; no more curation needed before next experiment |
