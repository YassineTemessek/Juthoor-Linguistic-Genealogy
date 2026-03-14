# Juthoor — Master Status Tracker
**Purpose:** Single source of truth for resuming work after any interruption.
**Last updated:** 2026-03-14

---

## Active Plan: LV0 Data Expansion + LV2 Genome Integration
**Plan file:** `docs/plans/LV0_LV2_EXECUTION_ORCHESTRATION.md`
**Baseline commit:** `1879e32`

### Phase A: LV0 Data Expansion

| Task | Owner | Status | Commit | Notes |
|------|-------|--------|--------|-------|
| A.1 Download Hebrew Kaikki | Codex | IN PROGRESS | — | Codex working on it |
| A.2 Extend adapter + ingest Hebrew | Codex | BLOCKED on A.1 | — | Add `"he"` to LANG_MAP |
| A.3 Aramaic/Syriac download + ingest | Codex | IN PROGRESS | — | Check Kaikki availability first |
| A.4 Persian download + ingest | Codex | IN PROGRESS | — | Same Kaikki pattern |
| A.5 Run LV0 mergers | Sonnet | DONE (nothing needed) | `1a55505` | Arabic already merged, Latin/Greek use kaikki.jsonl |
| A.6 Hebrew ingest tests | Sonnet | BLOCKED on A.2 | — | Test schema, row count |
| A.7 Expand benchmark (Arabic-Hebrew pairs) | Sonnet | BLOCKED on A.2 | — | 20+ gold pairs, 10 negatives |

### Phase B: LV2 Genome Integration

| Task | Owner | Status | Commit | Notes |
|------|-------|--------|--------|-------|
| B.1 GenomeScorer module | Sonnet | DONE | `1a55505` | 396 coherence, 166 metathesis pairs, 13 tests |
| B.2 Wire into scoring pipeline | Sonnet | DONE | `6c95e8e` | Optional genome_scorer param, 226 LV2 tests pass |
| B.3 First Hebrew-Arabic discovery run | Codex | BLOCKED on A.2 + B.2 | — | Genome-enabled run |
| B.4 Genome vs blind comparison | Codex | BLOCKED on B.3 | — | Compare metrics |
| B.5 Review & analysis | Opus | BLOCKED on B.4 | — | Final review |

---

## Completed Plans

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

**Total LV1 tests:** 227

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
| LV0 | 145 | 2026-03-14 |
| LV1 | 227 | 2026-03-14 |
| LV2 | 226 | 2026-03-14 |
| **Total** | **598** | |

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

---

*Last updated: 2026-03-14 — after B.2 completion*
