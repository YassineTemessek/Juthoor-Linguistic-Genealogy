# LV4 Roadmap (Ordered)

This roadmap assumes LV3 generates discovery artifacts (processed lexeme tables + ranked leads) and LV4 defines how to interpret and validate them.

## Phase 0: Keep LV4 readable and versioned

- Treat `Master FoundationV3.2.md` as the canonical spec.
- When a new version is needed, create `Master FoundationV3.3.md` rather than editing history.
- Record major changes in `docs/ROADMAP.md` (this file).

## Phase 1: Anchor layer becomes “real”

Goal: move from `auto_brut` (UI/discovery) to `silver`/`gold` (evidence/validation).

- Build/maintain anchor style guides per language (start with Latin, then Greek/Hittite).
- Define concrete quality gates:
  - coverage threshold (e.g., >= 90% of Tier-A concepts have an anchor)
  - confidence threshold (e.g., >= 70% are gold/silver)
- Keep a changelog for anchor set versions.

## Phase 2: Corridors become explicit “cards”

Goal: corridors stay soft during discovery, but become explicit, testable rules during validation.

- Maintain corridor definitions and examples in `docs/CORRIDORS.md`.
- Create corridor cards in `docs/templates/corridor_card.yaml` format.
- Track corridor overuse and “red flag” patterns in QA reporting.

## Phase 3: Validation track (designed, then activated)

Goal: once the discovery corpus is stable and anchors are strong, activate validation:

- Chronology locks and contact windows.
- Rule-constrained paths per language family.
- Null models / permutation tests / FDR control.
- Loanword handling (exclude vs tag) with explicit policy.

See `docs/VALIDATION_TRACK.md`.

## Phase 4: Publishable outputs

- A frozen discovery corpus version (with manifest + provenance)
- A validation report describing what survives strict tests and what fails
- A reproducible artifact bundle (inputs, outputs, scripts, versions)

