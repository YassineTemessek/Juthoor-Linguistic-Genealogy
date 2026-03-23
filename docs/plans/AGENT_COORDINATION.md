# Agent Coordination Board

**Both Claude Code and Codex read this file before starting work.**
**Both update it after completing tasks.**
**Check this file every 30 minutes during active sessions.**

---

## Current Sprint: Sprint 1 — Scoring Fixes

## Task Status (update when done)

| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| S1.1 Synonym groups | OPEN | TODO | SYNONYM_GROUPS in scoring — امتداد↔طول, تفشّي↔انتشار, etc. |
| S1.2 Fix empty features | OPEN | TODO | Get zero-feature nuclei under 20 |
| S1.3 Opposition mapping | OPEN | TODO | SEMANTIC_OPPOSITES — تجمع↔تفرق, ضغط↔فراغ, etc. |
| S1.4 Re-run score matrix | BLOCKED | TODO | Needs S1.1+S1.2+S1.3 |
| S1.5 Re-run Golden Rule | BLOCKED | TODO | Needs S1.3 |
| S1.6 Push to main | BLOCKED | TODO | Needs S1.4+S1.5 |
| S1.7 Verify improvement | Claude | DONE | Report at outputs/lv1_scoring/score_matrix_verification.md |
| S1.8 Method A re-calibration | Claude | DONE | Report at outputs/lv1_scoring/method_a_calibration_v2.md |

## Claiming Rules

1. Before starting a task, write your name in the Owner column and push
2. If a task already has an owner, don't duplicate the work
3. If you finish and there's unclaimed work, take it
4. First push wins — second worker rebases

## Latest Metrics (update after each re-run)

```
Last updated: 2026-03-23 by Claude
Score rows:     4,792
Nonzero:        692 (14.4%)
Mean Jaccard:   0.073
Zero-feature nuclei: 44
Golden Rule:    29/166 (17.5%)
LV1 tests:     313 passing
```

## Messages Between Agents

### Claude → Codex
- S1.7 and S1.8 done. Your turn on S1.1-S1.3 scoring fixes.
- Key insight: Jaccard undercounts by ~3x. Synonym groups will fix this.
- Intersection model confirmed as best. Use for Phase 3.

### Codex → Claude
(write here when you have updates)

---

## Next Sprint Preview

After Sprint 1 complete:
- **Sprint 3**: Root prediction (1,924 roots) — Codex builds predictor, Claude does Method A
- **Sprint 4**: Abbas sensory validation — Codex runs stats, Claude reviews
- **Sprint 5**: Khashim sound laws + cross-lingual projection

Full plan: `docs/plans/2026-03-23-lv1-phase2-3-orchestration.md`

---

## How To Use This File

**Codex:** Set a recurring task to `cat docs/plans/AGENT_COORDINATION.md` every 30 min.
If you see TODO tasks with no owner, take them. After completing, update this file and push.

**Claude Code:** Check this file when starting a session or after pulling.
If new Codex messages, act on them. Update your messages section.

**Neither agent waits for the other. Both keep moving.**
