# Validation Track (Blueprint)

LV4’s Validation Track turns “ranked discovery leads” into “testable claims”.

## When to activate validation

Validation should only activate after:

- The discovery corpus is frozen (stable data + stable scoring configuration).
- Anchor KPIs are met (coverage + quality thresholds).
- Provenance is complete (stage/script/source are tracked for every lexeme used as evidence).

## What changes in validation (vs discovery)

- Constraints become mandatory (chronology/contact, correspondence rules).
- Null models are required (chance similarity baseline).
- Evidence is restricted to vetted anchors (gold/silver), not `auto_brut`.
- Negative results are recorded and reported (not just successes).

## Core validation components

1) Chronology & contact windows
- Enforce plausible direction windows.
- Reject candidate pairs outside admissible contact/chronology constraints.

2) Rule-constrained correspondence paths
- Apply known sound changes where appropriate (e.g., Grimm/Verner, High German shift).
- Apply Semitic constraints (emphatics, pharyngeals, glottal behavior) as explicit rules.

3) Null models & statistics
- Permutation tests with phonotactically matched controls.
- Multiple-testing correction (FDR control).
- Report effect sizes and confidence intervals.

4) Loanword policy
- Distinguish: tag-only in discovery vs exclude/segregate in validation.
- Maintain an explicit “loan suspicion” rubric and audit trail.

## Outputs

- A validation report with:
  - what passed (with evidence)
  - what failed (and why)
  - sensitivity analyses (what changes with different constraints)
- A frozen artifact bundle:
  - exact inputs, versions, manifests
  - reproducible scripts/commands

