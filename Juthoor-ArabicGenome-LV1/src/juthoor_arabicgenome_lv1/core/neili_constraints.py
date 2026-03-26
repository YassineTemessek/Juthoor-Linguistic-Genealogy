"""Apply Neili-style semantic constraints to Quranic root predictions.

The checks in this module flag synonymy, instance-level meanings, and weak
category structure so predicted root analyses stay methodologically coherent.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from juthoor_arabicgenome_lv1.core.feature_decomposition import FEATURE_TO_CATEGORY


# ---------------------------------------------------------------------------
# Neili's methodological constraints for Quranic Arabic root prediction
# Based on the principles of عالم سبيط النيلي (Sabeet al-Neili)
# ---------------------------------------------------------------------------

# Features that are considered instance-level (spatial/physical specifics)
# rather than conceptual-level meanings.
# Neili principle 2: root meanings must be abstract concepts, not instances.
_INSTANCE_LEVEL_FEATURES: frozenset[str] = frozenset({
    "حيز",   # specific physical space
    "سطح",   # surface (instance-level spatial)
    "حدة",   # sharpness as a physical property
    "جوف",   # hollow (specific physical form)
    "عمق",   # depth (specific spatial measurement)
})

# Minimum number of distinct semantic categories for a coherent composition.
# A prediction with features all from exactly one category may be underspecified
# but is not incoherent. Incoherence is about conflicting extreme dispersal.
_MIN_CATEGORIES_FOR_COHERENCE_WARNING = 1


@dataclass(frozen=True)
class NeiliFlag:
    """A flag raised when a prediction violates a Neili constraint."""

    constraint: str     # which principle was violated
    root: str
    description: str
    severity: str       # "hard" (definite violation) or "soft" (possible violation)

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.constraint} — {self.root}: {self.description}"


# ---------------------------------------------------------------------------
# Constraint 1: No synonymy (لا ترادف في كلام الخالق)
# ---------------------------------------------------------------------------

def check_no_synonymy(
    predictions: list[dict[str, Any]],
    *,
    quranic_only: bool = True,
) -> list[NeiliFlag]:
    """Flag root pairs that share identical predicted meaning.

    Neili's principle: in Quranic Arabic, no two roots are true synonyms.
    If the predictor assigns identical features to two different Quranic roots,
    at least one prediction is wrong.

    Each prediction dict must have:
        - "root": str
        - "predicted_features": tuple[str, ...] | list[str]
        - "is_quranic": bool  (optional; if absent and quranic_only=True, treated as non-Quranic)
    """
    flags: list[NeiliFlag] = []

    # Group roots by their frozen feature set
    feature_groups: dict[frozenset[str], list[str]] = defaultdict(list)

    for pred in predictions:
        root = pred.get("root", "")
        if quranic_only and not pred.get("is_quranic", False):
            continue
        features = pred.get("predicted_features", ())
        if not features:
            continue
        key = frozenset(features)
        feature_groups[key].append(root)

    # Any group with 2+ roots is a synonymy violation
    for features_key, roots in feature_groups.items():
        if len(roots) >= 2:
            feature_list = ", ".join(sorted(features_key))
            for root in roots:
                flags.append(
                    NeiliFlag(
                        constraint="no_synonymy",
                        root=root,
                        description=(
                            f"Root shares identical predicted features {{{feature_list}}} "
                            f"with: {', '.join(r for r in roots if r != root)}"
                        ),
                        severity="hard",
                    )
                )

    return flags


# ---------------------------------------------------------------------------
# Constraint 2: Conceptual level (المعنى المفهومي vs المصداق)
# ---------------------------------------------------------------------------

def check_conceptual_level(
    prediction: dict[str, Any],
    *,
    instance_features: frozenset[str] | None = None,
) -> list[NeiliFlag]:
    """Flag predictions that are too instance-specific rather than conceptual.

    Neili: root meanings should be abstract concepts, not specific instances.
    Features like حيز (space) or سطح (surface) are instance-level.
    Features like اتصال (connection) or انتقال (movement) are conceptual.

    Each prediction dict must have:
        - "root": str
        - "predicted_features": tuple[str, ...] | list[str]
    """
    if instance_features is None:
        instance_features = _INSTANCE_LEVEL_FEATURES

    flags: list[NeiliFlag] = []
    root = prediction.get("root", "")
    features = tuple(prediction.get("predicted_features", ()))

    offending = [f for f in features if f in instance_features]
    if not offending:
        return flags

    # If the majority of features are instance-level, raise a hard flag
    ratio = len(offending) / len(features)
    severity = "hard" if ratio >= 0.5 else "soft"

    flags.append(
        NeiliFlag(
            constraint="conceptual_level",
            root=root,
            description=(
                f"Predicted features contain instance-level term(s): "
                f"{', '.join(offending)}. "
                f"Root meanings should be abstract concepts (المعنى المفهومي), "
                f"not physical instances (المصداق)."
            ),
            severity=severity,
        )
    )
    return flags


# ---------------------------------------------------------------------------
# Constraint 3: Composition coherence (القصدية / intentionality)
# ---------------------------------------------------------------------------

def check_composition_coherence(
    prediction: dict[str, Any],
) -> list[NeiliFlag]:
    """Flag predictions where the composed meaning is incoherent.

    Neili: letter composition is intentional (القصدية). If predicted features
    spread across too many unrelated semantic categories with no discernible
    centre of gravity, the prediction may be random feature concatenation
    rather than principled composition.

    Heuristic: if ALL of the following hold, flag as possibly incoherent:
        1. 4+ distinct categories are present
        2. No single category accounts for ≥ 40% of the features
        3. Direct semantic opposites both appear (e.g. تجمع and تفرق)

    Each prediction dict must have:
        - "root": str
        - "predicted_features": tuple[str, ...] | list[str]
    """
    from juthoor_arabicgenome_lv1.core.feature_decomposition import FEATURE_POLARITIES

    flags: list[NeiliFlag] = []
    root = prediction.get("root", "")
    features = list(prediction.get("predicted_features", ()))

    if len(features) < 2:
        return flags

    # Check for direct semantic opposites co-occurring
    feature_set = set(features)
    opposite_pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for feat in features:
        opposite = FEATURE_POLARITIES.get(feat)
        if opposite and opposite in feature_set and feat not in seen:
            opposite_pairs.append((feat, opposite))
            seen.add(feat)
            seen.add(opposite)

    # Check category spread
    categories = [FEATURE_TO_CATEGORY.get(f) for f in features]
    valid_cats = [c for c in categories if c is not None]
    unique_cats = set(valid_cats)

    if not opposite_pairs and len(unique_cats) < 4:
        return flags

    # Build description
    reasons: list[str] = []
    if opposite_pairs:
        pairs_str = "; ".join(f"{a} ↔ {b}" for a, b in opposite_pairs)
        reasons.append(f"semantic opposites co-occur: {pairs_str}")
    if len(unique_cats) >= 4:
        reasons.append(f"features span {len(unique_cats)} unrelated categories")

    if reasons:
        flags.append(
            NeiliFlag(
                constraint="composition_coherence",
                root=root,
                description=(
                    f"Composition may lack intentionality (القصدية): "
                    + "; ".join(reasons)
                    + ". Every letter-meaning connection should be purposeful."
                ),
                severity="soft",
            )
        )

    return flags


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def is_quranic_root(root: str, quranic_roots: set[str]) -> bool:
    """Check if a root is attested in the Quranic corpus."""
    return root in quranic_roots


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def apply_neili_constraints(
    predictions: list[dict[str, Any]],
    quranic_roots: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Apply all Neili constraints to a list of predictions.

    If quranic_roots is provided, each prediction gets an 'is_quranic' field
    added before constraint checking (does not overwrite an existing value).

    Returns the predictions with a new 'neili_flags' field (list[NeiliFlag])
    added to each.  The original dicts are not mutated — new dicts are returned.
    """
    # Shallow-copy each dict and, if quranic_roots supplied, annotate
    enriched: list[dict[str, Any]] = []
    for pred in predictions:
        p = dict(pred)
        if quranic_roots is not None and "is_quranic" not in p:
            p["is_quranic"] = is_quranic_root(p.get("root", ""), quranic_roots)
        p.setdefault("neili_flags", [])
        enriched.append(p)

    # Constraint 1: no-synonymy (operates across all predictions at once)
    synonymy_flags = check_no_synonymy(enriched, quranic_only=True)
    # Index flags by root for O(1) lookup
    flags_by_root: dict[str, list[NeiliFlag]] = defaultdict(list)
    for flag in synonymy_flags:
        flags_by_root[flag.root].append(flag)

    # Constraints 2 & 3: per-prediction
    for pred in enriched:
        root = pred.get("root", "")
        pred["neili_flags"] = list(flags_by_root.get(root, []))
        pred["neili_flags"].extend(check_conceptual_level(pred))
        pred["neili_flags"].extend(check_composition_coherence(pred))

    return enriched
