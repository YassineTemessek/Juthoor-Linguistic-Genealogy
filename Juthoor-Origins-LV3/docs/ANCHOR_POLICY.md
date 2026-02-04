# Anchor Policy (LV4)

Anchors are the bridge from “discovery” to “evidence”.

## Status levels

- `auto_brut`: heuristic / unverified; allowed in discovery but not evidence.
- `silver`: attested and mostly aligned, but with remaining ambiguity.
- `gold`: attested and clearly aligned to the concept definition.

## What anchors are for

- Provide a stable, auditable lemma reference per concept per anchor language.
- Improve interpretability of cross-language candidates.
- Enable validation by restricting evidence to high-confidence items.

## Policy rules

- Discovery can use `auto_brut` for navigation, but must visibly tag it.
- Validation can only use `gold` and carefully documented `silver`.
- Anchor changes must be versioned (anchor set v1.0, v1.1, …) and reproducible.

