"""Define validated dataclasses for theory-canon registry content.

The models capture letters, binary nuclei, roots, sources, and scholarly claims
while enforcing controlled vocabularies for curation and agreement metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Constants — scholar and feature-category vocabularies
# ---------------------------------------------------------------------------

VALID_SCHOLARS = (
    "jabal",
    "neili",
    "asim_al_masri",
    "hassan_abbas",
    "anbar",
    "khashim",
    "dhouq",
    "shanawi",
)

FEATURE_CATEGORIES = (
    "pressure_force",
    "extension_movement",
    "penetration_passage",
    "gathering_cohesion",
    "spreading_dispersal",
    "texture_quality",
    "sharpness_cutting",
    "spatial_orientation",
    "independence_distinction",
)

# ---------------------------------------------------------------------------
# Internal validation sets
# ---------------------------------------------------------------------------

_CANON_STATUSES = {"empty", "draft", "curated", "tested", "promoted", "rejected"}
_CLAIM_STATUSES = {"asserted", "draft", "curated", "tested", "promoted", "rejected"}
_AGREEMENT_LEVELS = {"consensus", "majority", "contested", "unknown"}
_CONFIDENCE_TIERS = {"high", "medium", "low", "stub"}
_CURATION_STATUSES = {"raw", "reviewed", "accepted"}


def _require_in(value: str, allowed: set[str], field_name: str) -> str:
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {sorted(allowed)}; got {value!r}")
    return value


def _require_tuple(value: tuple[Any, ...], field_name: str) -> tuple[Any, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    return value


@dataclass(frozen=True)
class SourceEntry:
    source_id: str
    scholar: str
    claim_type: str
    claim_text: str
    document_ref: str
    curation_status: str

    def __post_init__(self) -> None:
        _require_in(self.curation_status, _CURATION_STATUSES, "curation_status")


@dataclass(frozen=True)
class LetterSemanticEntry:
    letter: str
    letter_name: str
    canonical_semantic_gloss: str | None
    canonical_kinetic_gloss: str | None
    canonical_sensory_gloss: str | None
    articulatory_features: dict[str, Any] | None
    sources: tuple[SourceEntry, ...]
    agreement_level: str
    confidence_tier: str
    status: str

    def __post_init__(self) -> None:
        _require_tuple(self.sources, "sources")
        _require_in(self.agreement_level, _AGREEMENT_LEVELS, "agreement_level")
        _require_in(self.confidence_tier, _CONFIDENCE_TIERS, "confidence_tier")
        _require_in(self.status, _CANON_STATUSES, "status")


@dataclass(frozen=True)
class BinaryFieldEntry:
    binary_root: str
    field_gloss: str | None
    field_gloss_source: str | None
    letter1: str
    letter2: str
    letter1_gloss: str | None
    letter2_gloss: str | None
    member_roots: tuple[str, ...]
    member_count: int
    coherence_score: float | None
    cross_lingual_support: dict[str, Any] | None
    status: str

    def __post_init__(self) -> None:
        _require_tuple(self.member_roots, "member_roots")
        _require_in(self.status, _CANON_STATUSES, "status")


@dataclass(frozen=True)
class RootCompositionEntry:
    root: str
    binary_root: str
    third_letter: str
    conceptual_root_meaning: str | None
    binary_field_meaning: str | None
    axial_meaning: str | None
    letter_trace: tuple[dict[str, Any], ...] | None
    position_profile: dict[str, Any] | None
    modifier_profile: dict[str, Any] | None
    compositional_signal: float | None
    agreement_with_observed_gloss: str | None
    status: str
    semantic_score: float | None = None

    def __post_init__(self) -> None:
        if self.letter_trace is not None:
            _require_tuple(self.letter_trace, "letter_trace")
        _require_in(self.status, _CANON_STATUSES, "status")


@dataclass(frozen=True)
class TheoryClaim:
    claim_id: str
    theme: str
    scholar: str
    statement: str
    scope: str
    evidence_type: str
    source_doc: str
    source_locator: str | None
    status: str

    def __post_init__(self) -> None:
        _require_in(self.status, _CLAIM_STATUSES, "status")


@dataclass(frozen=True)
class QuranicSemanticProfile:
    lemma: str
    root: str
    conceptual_meaning: str | None
    binary_field_meaning: str | None
    lexical_realization: str | None
    letter_trace: tuple[dict[str, Any], ...] | None
    contextual_constraints: tuple[str, ...] | None
    contrast_lemmas: tuple[str, ...] | None
    interpretive_notes: str | None
    confidence: str
    status: str

    def __post_init__(self) -> None:
        if self.letter_trace is not None:
            _require_tuple(self.letter_trace, "letter_trace")
        if self.contextual_constraints is not None:
            _require_tuple(self.contextual_constraints, "contextual_constraints")
        if self.contrast_lemmas is not None:
            _require_tuple(self.contrast_lemmas, "contrast_lemmas")
        _require_in(self.confidence, _CONFIDENCE_TIERS, "confidence")
        _require_in(self.status, _CANON_STATUSES, "status")


# ---------------------------------------------------------------------------
# Atomic Feature System — VISION.md Section 6.2
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AtomicFeature:
    """A single irreducible semantic feature from the 9-category vocabulary.

    The vocabulary is extracted from Jabal's 28 letter definitions and
    456 binary nucleus meanings (VISION.md Section 6.2).
    """
    arabic: str     # e.g. "تجمع"
    english: str    # e.g. "gathering"
    category: str   # One of FEATURE_CATEGORIES (snake_case English key)


# ---------------------------------------------------------------------------
# Letter Registry — Layer 0 (الحروف)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LetterAtom:
    """A single scholar's semantic description of one Arabic letter.

    Multiple LetterAtom instances for the same letter (one per scholar)
    are collected in a LetterRegistryEntry.
    """
    letter: str                          # Single Arabic letter e.g. "ب"
    letter_name: str                     # e.g. "الباء"
    scholar: str                         # One of VALID_SCHOLARS
    raw_description: str                 # Original Arabic text of the meaning
    atomic_features: tuple[str, ...]     # Decomposed features e.g. ("تجمع", "رخاوة", "تلاصق")
    feature_categories: tuple[str, ...]  # Category per feature (parallel to atomic_features)
    sensory_category: Optional[str]      # Abbas only: لمسية / ذوقية / بصرية / سمعية /
                                         #   شعورية_غير_حلقية / شعورية_حلقية
    kinetic_gloss: Optional[str]         # Neili/Asim: physical movement description
    source_document: str                 # Book/paper reference
    confidence: str                      # high, medium, low, stub


@dataclass(frozen=True)
class LetterRegistryEntry:
    """Unified entry for one letter across all scholars.

    Aggregates all LetterAtom instances for a letter and records
    the level of inter-scholar agreement on its semantic features.
    """
    letter: str
    letter_name: str
    scholar_entries: tuple[LetterAtom, ...]  # One per scholar who covered this letter
    consensus_features: tuple[str, ...]       # Features where 2+ scholars agree
    agreement_level: str                      # consensus, majority, contested, insufficient
    articulatory_features: Optional[dict]     # Makhraj + sifaat from phonetics data


# ---------------------------------------------------------------------------
# Binary Nucleus Registry — Layer 1 (الفصل المعجمي)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BinaryNucleus:
    """A binary root / lexical field (الفصل المعجمي) from Jabal's data.

    The primary unit for Layer 1 testing. Scoring fields are None until
    the composition engine runs.
    """
    binary_root: str                      # Two-letter nucleus e.g. "حس"
    letter1: str                          # First letter
    letter2: str                          # Second letter
    jabal_shared_meaning: str             # المعنى المشترك from Jabal
    jabal_features: tuple[str, ...]       # Atomic features of the shared meaning
    member_roots: tuple[str, ...]         # Trilateral roots in this family
    member_count: int
    reverse_exists: bool                  # Does the reverse nucleus exist?
    reverse_root: Optional[str]           # The reverse nucleus if it exists e.g. "سح"
    # Scoring fields — filled by the composition engine
    model_a_score: Optional[float]        # Intersection model score
    model_b_score: Optional[float]        # Sequence model score
    model_c_score: Optional[float]        # Dialectical model score
    model_d_score: Optional[float]        # Phonetic-gestural model score
    best_model: Optional[str]             # Which model scored highest
    golden_rule_score: Optional[float]    # If reverse exists: meaning inversion score
    status: str                           # empty, scored, validated, promoted


# ---------------------------------------------------------------------------
# Trilateral Root Registry — Layer 2 (الجذر الثلاثي)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TriliteralRootEntry:
    """A trilateral root with composition analysis.

    Links a root to its binary nucleus and records both Jabal's ground-truth
    meaning and the composition engine's prediction.
    """
    root: str                                      # Three-letter root e.g. "كتب"
    binary_nucleus: str                            # First two letters e.g. "كت"
    third_letter: str                              # Added letter e.g. "ب"
    jabal_axial_meaning: str                       # المعنى المحوري from Jabal
    jabal_features: tuple[str, ...]                # Atomic features of axial meaning
    predicted_meaning: Optional[str]               # From composition engine
    predicted_features: Optional[tuple[str, ...]]  # Predicted atomic features
    prediction_score: Optional[float]              # Method B Jaccard score
    quranic_verse: Optional[str]                   # Example verse if available
    bab: str                                       # Which BAB chapter
    status: str                                    # empty, predicted, scored, validated


# ---------------------------------------------------------------------------
# Composition Result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CompositionResult:
    """Result of applying a composition model to a binary nucleus.

    Produced by running one of the four composition models (A-D) against
    a binary nucleus using a specific scholar's letter values.
    """
    nucleus: str                           # e.g. "حس"
    model: str                             # model_a, model_b, model_c, model_d
    scholar_letters: str                   # Which scholar's letter values were used
    predicted_features: tuple[str, ...]    # Predicted atomic features
    actual_features: tuple[str, ...]       # Jabal's actual features
    jaccard_score: float                   # |intersection| / |union|
    weighted_score: float                  # Weighted Jaccard
    matched_features: tuple[str, ...]      # Features in both predicted and actual
    missed_features: tuple[str, ...]       # In actual but not predicted
    extra_features: tuple[str, ...]        # In predicted but not actual
