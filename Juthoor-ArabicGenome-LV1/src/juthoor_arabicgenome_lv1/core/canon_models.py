from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
