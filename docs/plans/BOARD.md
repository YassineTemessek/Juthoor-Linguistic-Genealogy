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
| H1 | Adaptive model routing (best-of ensemble) | Claude | DONE | root_predictor.py — 498 tests. nucleus_only wins 15/21 letter families |
| H2 | Method A v5 on consensus_weighted | Claude | DONE | **Method A = 53.0%** (up from 49.5%). First time past 50%! |
| H3 | Quranic roots deep-dive | Claude | DONE | `quranic_deep_dive.md` — failure classification on 50 Quranic roots |
| M1 | LV2 synonym expansion module | Claude | DONE | `synonym_expansion.py` — 12 LV2 tests |
| M2 | Abbas mechanism routing test | Claude | DONE | `abbas_mechanism_routing_test.md` |
| L1 | Merge Abbas reports | Claude | WIP | merging 2→1 |
| L2 | Move session reports to docs/sessions | Claude | WIP | organizing |

## Codex
```
last: All tasks complete. Tokens resetting.
metrics: roots=1924, nuclei=456, tests=495, overall bJ=0.196, consensus_weighted bJ=0.200
suggests: wait for Claude's H1 adaptive routing results before next rebuild
blocked: none
```

## Claude
```
last: Sprint complete. H1 adaptive routing, H2 Method A v5=53.0%, H3 Quranic dive, M1 LV2 synonyms, M2 Abbas routing. 498 tests. 5 new reports. LV2 module added.
verdict: **Method A crossed 50% for the first time (53.0%)**. nucleus_only is the best model for 15/21 letter families. LV2 now has synonym expansion for cross-lingual.
next-codex: rebuild pipeline after H1 lands
next-claude: H1 + H2 + H3 in parallel, then M1
note: Codex tokens reset in 1 hour. Claude working solo until then.
```

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
- Neili no-synonymy is parked for a later Quranic interpretation layer. It is not part of active LV1 scoring or model acceptance.
- Position-aware model: needs adaptive routing (best-of ensemble, not unconditional override)
- Consensus_weighted is now best scholar (bJ=0.200), overtook consensus_strict

## Archive
| Date | Task | Owner | Output |
|------|------|-------|--------|
| 03-26 | I1 Binary Composition Verification | Claude | `BINARY_COMPOSITION_VERIFICATION.md` — 53.5% match, 3 failure families |
| 03-26 | I2 Third Letter Modifier Profiles | Codex | `THIRD_LETTER_MODIFIER_PROFILES.md` + JSON. ج/ظ cleanest, ر/ل/ب riskiest |
| 03-26 | I3 Reverse Pair Analysis | Claude | `REVERSE_PAIR_ANALYSIS.md` — 12% inversion, 79% unrelated |
| 03-26 | A.1 Audit unrecognized tokens in jabal_axial_meaning | Codex | `feature_vocab_gap_report.md` |
| 03-26 | A.2 Expand FEATURE_VOCAB 65→~85 features | Codex | `feature_decomposition.py` expanded |
| 03-26 | A.3 Re-extract jabal_features with expanded vocab | Codex | roots rebuilt |
| 03-26 | A.4 Recover empty-actual roots (113→107) | Codex | `feature_decomposition.py` |
| 03-26 | A.5 Re-run predictions + score matrix | Codex | outputs rebuilt |
| 03-26 | B.1 Classify 495 nucleus-correct-but-root-wrong failures | Claude | `third_letter_failure_analysis.md` |
| 03-26 | C.1 Present 8 DIVERGE letters to Yassin | Claude | `diverge_letters_for_yassin.md` |
| 03-26 | B.2 Semantic compatibility filter + blacklist التحام | Codex | `root_predictor.py` filter |
| 03-26 | B.3 Nucleus-only fallback when intersection over-prunes | Codex | `root_predictor.py` |
| 03-26 | E.2 Empirical letter meaning derivation (8 DIVERGE) | Claude | `empirical_letter_meanings.md` |
| 03-26 | F.1-F.3 Full 28-letter empirical derivation | Claude | `THE_ARABIC_LETTER_GENOME.md` |
| 03-26 | C.2 Yassin confirms 4 letter corrections | Yassin | م=تجمع+تلاصق, ع=ظهور+عمق, غ=باطن+اشتمال, ب=ظهور+خروج |
| 03-26 | F.4 Apply 4 corrections + rebuild consensus | Codex | jabal letters corrected; consensus rebuilt |
| 03-26 | F.5 Method A re-calibration with corrected letters | Claude | Jabal bJ +12%, consensus bJ +7.4%. 415 tests pass |
| 03-26 | A.6 Spot check: did vocab expansion improve Method B? | Claude | reviewed `feature_vocab_gap_report.md` after A.1-A.5 |
| 03-26 | B.6 Spot check: did third-letter fixes recover the poisoned roots? | Claude | reviewed rerun after B.2-B.3 |
| 03-26 | 2.1 Refactor root_predictor.py (extract routing + filtering) | Codex | behavior-preserving helper extraction, tests green |
| 03-26 | 2.2 Refactor independent_letter_derivation.py | Codex | behavior-preserving selection/comparison extraction, tests green |
| 03-26 | 3.1 Pipeline integration test (end-to-end LV1) | Claude | `tests/test_lv1_pipeline_integration.py` — 1924 roots, 456 nuclei, jabal predictions pass |
| 03-26 | 5.1 Build Quranic verse validation module | Claude | `factory/quranic_validation.py` — 30 tests |
| 03-26 | 5.2 Build scholar divergence analysis | Claude | `factory/scholar_divergence.py` — 34 tests |
| 03-26 | PA.1 Re-run LV1 with position-aware model and compare metrics | Codex | 2026-03-26 rebuild lifted overall blended bJ from 0.190419 to 0.195517 |
| 03-26 | FIX test_promotions.py cross_lingual_support pre-existing failure | Codex | resolved by regenerating benchmark support inputs; 28/28 pass |
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
