# Autonomous Work Protocol — Claude + Codex 4-Hour Sessions

**Goal:** Both agents work continuously for 4+ hours without user intervention.

---

## The Problem

Currently: Codex works → pushes → waits for user → user tells Claude → Claude reviews → pushes → waits for user → user tells Codex. Each handoff wastes 10-30 minutes.

## The Solution: Git-Based Async Communication

Both agents communicate through **git commits on main**. No user relay needed.

### Protocol

1. **Codex** works through his task list, commits and pushes after each task
2. **Claude** runs a monitoring loop that:
   - Pulls main every 5 minutes
   - Checks for new Codex commits
   - If new work found → reviews, calibrates, pushes response
   - If no new work → continues own tasks
3. **The plan file** (`2026-03-23-lv1-phase2-3-orchestration.md`) is the shared task board
4. **Both agents mark tasks done** by editing the plan file with `[x]`

### Codex Gets a 4-Hour Task List

Codex should receive this as his session prompt:

```
Read docs/plans/2026-03-23-lv1-phase2-3-orchestration.md

Execute ALL tasks marked [ ] in order. For each task:
1. Do the work
2. Run tests
3. Commit with clear message
4. Push to main
5. Mark the task [x] in the plan file
6. Move to the next task immediately

Do NOT stop between tasks. Do NOT ask for confirmation.
Do NOT wait for Claude. Work through the entire Sprint queue.

If a task fails, note it in the commit message and skip to the next.

Priority order:
- Sprint 1: S1.1-S1.6 (scoring fixes)
- Sprint 2: S2.1-S2.3 (Anbar extraction)
- Sprint 3: S3.1-S3.5 (root prediction — the big one)
- Sprint 4: S4.1-S4.2 (Abbas validation)
- Sprint 5: S5.1-S5.4 (Khashim sound laws + cross-lingual)

This is 4+ hours of work. Do it all.
```

### Claude Runs a Monitor Loop

Claude Code uses `/loop` to check Codex's work every 10 minutes:

```
/loop 10m check-codex
```

The check script:
1. `git pull origin main`
2. Check `git log --oneline -5` for new Codex commits
3. If new scoring data → run Method A re-calibration
4. If new root predictions → run Method A on roots
5. If new Golden Rule data → review and update verdict
6. Push any reviews/calibrations
7. Update the plan file with review status

### What the User Does

**Start of session:**
1. Open Codex → paste the 4-hour task prompt
2. Open Claude Code → run the monitor loop
3. Walk away for 4 hours

**End of session:**
1. Read `docs/plans/2026-03-23-lv1-phase2-3-orchestration.md` to see what got done
2. Read any new reports in `outputs/lv1_scoring/`
3. Check `git log --oneline -20` for the work trail

---

## Fallback: Manual Batch Mode

If the automated loop doesn't work, use manual batch mode:

1. Give Codex the full task list (he works for 2-4 hours)
2. Come back, tell Claude: "Codex finished, review everything"
3. Claude pulls, reviews all at once, pushes
4. Repeat

This is less efficient but requires zero tooling.

---

## Task Density: What 4 Hours Looks Like

### Codex (compute-heavy, 4 hours)

| Sprint | Tasks | Est. Time |
|--------|-------|-----------|
| S1 remaining | S1.1-S1.6 scoring fixes + re-run | 45 min |
| S2 | S2.1-S2.3 Anbar extraction | 30 min |
| S3 | S3.1-S3.5 root prediction (1,924 roots) | 90 min |
| S4 | S4.1-S4.2 Abbas sensory validation | 30 min |
| S5 | S5.1-S5.4 Khashim + cross-lingual | 60 min |
| **Total** | **20 tasks** | **~4 hours** |

### Claude (review + calibration, triggered by Codex pushes)

| Trigger | Task | Est. Time |
|---------|------|-----------|
| After S1.6 | S1.7-S1.8 verify + re-calibrate | 20 min |
| After S2.3 | S2.4 scholar comparison | 15 min |
| After S3.5 | S3.6-S3.8 Method A roots + failure analysis + verdict | 45 min |
| After S4.2 | S4.3 sensory validation report | 15 min |
| After S5.4 | S5.5 cross-lingual report | 20 min |
| Ongoing | S6.1-S6.3 documentation updates | 15 min |
| **Total** | **12 tasks** | **~2 hours** |

---

*Autonomous Work Protocol*
*2026-03-23*
