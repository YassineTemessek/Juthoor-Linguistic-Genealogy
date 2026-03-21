# Juthoor — Master Status Tracker
**Purpose:** Single source of truth for resuming work after any interruption.
**Last updated:** 2026-03-21 (LV2 Evaluation Expansion complete; LV1 Core Restructure parked)

---

## Active Plan 1: LV1 Core Restructure (Codex)
**Plan file:** `docs/plans/2026-03-18-lv1-core-restructure.md`
**Baseline commit:** `a2a5893`
**Design:** Structure first, curated theory content later via import inbox

| Phase | Task | Owner | Status | Notes |
|-------|------|-------|--------|-------|
| 1 | Registry dataclasses (canon_models.py) | Codex | TODO | 6 frozen dataclasses |
| 1 | Canon loaders (canon_loaders.py) | Codex | TODO | Load from JSONL |
| 1 | Seed registries from existing data | Codex | TODO | Muajam + genome + promoted outputs |
| 1 | Theory content inbox folder | Codex | TODO | Folder structure + SCHEMA.md |
| 1 | Phase 1 acceptance tests | Codex | TODO | 28 letters, all binary roots |
| 2 | Import validators | Codex | TODO | Validate before ingestion |
| 2 | Merge policy | Codex | TODO | Status transitions, no silent overwrite |
| 2 | Import CLI + reports | Codex | TODO | JSON reports per import |
| 3 | Processing pipeline | Codex | TODO | 8-step, graceful degradation |
| 4 | Attach Research Factory outputs | Codex | TODO | H2/H5/H8/H10/H9 → registries |
| 5 | Quranic bridge + QCA contracts | Codex | TODO | Phase 3 must be stable first |

---

## Active Plan 2: LV2 Evaluation Expansion (Sonnet/Opus)
**Plan file:** `docs/plans/2026-03-16-lv2-evaluation-expansion.md`
**Orchestration:** `docs/plans/2026-03-17-parallel-execution-orchestration.md`
**Baseline commit:** `91c3006`

### Phase A: Benchmark Expansion to 100+ Pairs

| Task | Owner | Status | Commit | Notes |
|------|-------|--------|--------|-------|
| A.1 Expand Arabic-Hebrew gold to 50+ | Sonnet | DONE | `9d9e9be` | 50 ara-heb pairs |
| A.2 Add 20+ Arabic-Persian pairs | Sonnet | DONE | `460f72c` | 20 ara-fa pairs |
| A.3 Add 15+ Arabic-Aramaic pairs | Sonnet | DONE | `460f72c` | 18 ara-arc pairs |
| A.4 Strengthen negatives to 30+ | Sonnet | DONE | `460f72c` | 30 negatives, 13 false friends |

### Phase B: Multi-Pair Discovery + Reranker

| Task | Owner | Status | Commit | Notes |
|------|-------|--------|--------|-------|
| B.1 Arabic-Persian discovery (blind+genome) | Codex | DONE | — | 5/20 covered, genome delta=0 (loanwords) |
| B.2 Arabic-Aramaic discovery (blind+genome) | Codex | DONE | — | 13 pairs, MRR +0.109 (strongest effect) |
| B.3 Arabic-Hebrew re-eval (50+ pairs) | Codex | DONE | — | 37 pairs, Recall@10 +0.108, MRR +0.029 |
| B.4 Add genome_bonus to reranker features | Sonnet | DONE | `37872b6` | 11th feature, backward compatible |
| B.5 Persist genome_bonus in lead components | Sonnet | DONE | `460f72c` | Fixed: was at hybrid level, now in components |
| B.6 Train reranker with genome feature | Sonnet | DONE | — | 3 rerankers; genome_bonus weight: heb=0.459, arc=0.185, fa=0.117 |
| B.7 Multi-pair evaluation review | Opus | DONE | — | `outputs/reports/lv2_multi_pair_evaluation_review.md` |

### Phase C: GenomeScorer Extension + LV1 Refinements

| Task | Owner | Status | Commit | Notes |
|------|-------|--------|--------|-------|
| C.1 Aramaic consonant mapping | Sonnet | DONE | `f80876a` | All 22 Hebrew-script letters verified |
| C.2 Persian consonant mapping | Sonnet | DONE | `f80876a` | Added پ/چ/ژ/گ/ک/ی, extended regex range |
| C.3 H9 emphatic experiment | Codex | DONE | `3355ad5` | Not supported |
| C.4 H10 compositionality experiment | Codex | DONE | `3355ad5` | Real signal, not full compositionality |
| C.5 Hebrew cross-lingual H2/H5/H8 | Codex | TODO | | Depends on C.3, C.4, B.7 |

### Orchestration Tasks (from 2026-03-17-parallel-execution-orchestration.md)

| Task | Status | Notes |
|------|--------|-------|
| S.5 Multi-pair evaluation harness | DONE | compare_blind_vs_genome.py implemented |
| S.6 Family-aware GenomeScorer | DONE | `is_semitic_pair()` + family gating live |
| S.7 Benchmark quality audit script | DONE | audit_benchmark.py implemented |
| S.8 Recall@10 and Recall@100 metrics | DONE | Added to evaluation.py |

---

## Completed Plans

### LV0 Data Expansion + LV2 Genome Integration (COMPLETE)
**Plan file:** `docs/plans/LV0_LV2_EXECUTION_ORCHESTRATION.md`
**Final commit:** `89f812c`
**Review:** `outputs/reports/lv2_genome_integration_review.md`

| Phase | Status | Key Results |
|-------|--------|-------------|
| Phase A: LV0 Data Expansion | DONE (7/7) | Hebrew 17K, Persian 19K, Aramaic 2.2K ingested |
| Phase B: LV2 Genome Integration | DONE (5/5) | GenomeScorer works, MRR +0.040, nDCG +0.032 |

---

### LV1 Research Factory (COMPLETE)
**Plan file:** `docs/plans/RESEARCH_FACTORY_MASTER_PLAN.md`
**Orchestration:** `docs/plans/EXECUTION_ORCHESTRATION.md`
**Final commit:** `deda74b`
**Final synthesis:** `outputs/research_factory/reports/FINAL_SYNTHESIS.md`

| Phase | Status | Tests | Key Results |
|-------|--------|-------|-------------|
| Phase 0: Infrastructure | DONE | 90 | Models, loaders, feature store, experiment runner, embeddings, articulatory vectors |
| Phase 1: Core Science | DONE | +8 | H2 supported (field coherence), H1 inconclusive, H3 inconclusive |
| Phase 2: Metathesis & Position | DONE | +8 | H8 supported (positional), H5 supported (order), H6 not supported, H4 weak |
| Phase 3: Generative | DONE | +8 | H12 supported (prediction + phantom), H11 not supported, H7 not supported |
| Promotion | DONE | — | H2, H5, H8 evidence cards exported |
| Final Synthesis | DONE | — | 4 supported, 1 weak, 1 signal, 3 not supported, 1 inconclusive, 2 untested |

**Total LV1 tests:** 275

### Hypothesis Registry (final)
| ID | Status | Experiment(s) |
|----|--------|---------------|
| H1 | Inconclusive | 1.1, 5.1 |
| H2 | **Supported** | 2.3 |
| H3 | Weak signal | 3.1 |
| H4 | Weakly supported | 4.1 |
| H5 | **Supported** | 4.1 |
| H6 | Not supported | 4.3 |
| H7 | Not supported | 2.2 |
| H8 | **Supported** | 1.2 |
| H9 | Untested | — |
| H10 | Untested | — |
| H11 | Not supported | 6.2 |
| H12 | **Supported** | 6.1, 6.4 |

---

## Parked Work

### LV1 Future Refinements
**File:** `docs/plans/LV1_FUTURE_REFINEMENTS.md`
- Revisit H3 (position-aware modifier profiles)
- Revisit H1 (sub-letter features, root-level analysis)
- Explore H9, H10 (untested)
- Try fine-tuned Arabic embedder, cross-lingual validation

### LV3 Theory Bootstrap
**File:** `docs/plans/NEXT_STEPS_ROADMAP.md` (Lane 3)
- Build evidence ingestion pipeline
- Create corridor models
- Formalize genealogical hypotheses
- Parked until LV0+LV2 are solid

---

## Test Counts (current)

| Level | Tests | Last verified |
|-------|-------|---------------|
| LV0 | 174 | 2026-03-21 |
| LV1 | 275 | 2026-03-21 |
| LV2 | 262 | 2026-03-21 |
| **Total** | **711** | |

---

## How to Resume

**If interrupted, read this file first, then:**

1. Check `git log --oneline -5` to see where things stopped
2. Find the first BLOCKED or IN PROGRESS task above
3. Check if its dependencies are DONE
4. If dependencies are done → start the task
5. If dependencies are still in progress → wait or check with the other agent

**Key commits:**
| Commit | What |
|--------|------|
| `deda74b` | LV1 Research Factory complete |
| `1879e32` | LV0+LV2 orchestration plan pushed |
| `1a55505` | GenomeScorer module + LV0 mergers verified |
| `6c95e8e` | GenomeScorer wired into LV2 scoring pipeline |
| `89f812c` | First genome-informed Arabic-Hebrew discovery run |
| `91c3006` | CI fixes (green), LV2 Evaluation Expansion plan baseline |
| `9d9e9be` | Expand Arabic-Hebrew gold benchmark to 50+ pairs |
| `460f72c` | Add Arabic-Persian + Arabic-Aramaic pairs, expand negatives; persist genome_bonus |
| `37872b6` | Add genome_bonus as 11th reranker feature |
| `b9850a8` | Fix stale READMEs + add LV2 evaluation expansion plan |
| `15e8c70` | Persist genome_bonus in lead components for reranker consumption |

---

*Last updated: 2026-03-21 — LV2 Evaluation Expansion complete; test counts updated (LV0=174, LV1=275, LV2=262, Total=711)*
