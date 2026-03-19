from __future__ import annotations

from dataclasses import replace
from typing import Any

from juthoor_arabicgenome_lv1.core.canon_models import BinaryFieldEntry, LetterSemanticEntry, QuranicSemanticProfile


def attach_lv1_support(binary_entry: BinaryFieldEntry, *, coherence_score: float | None, provenance_exists: bool) -> BinaryFieldEntry:
    status = binary_entry.status
    if provenance_exists and coherence_score is not None and status not in {"promoted", "rejected"}:
        status = "tested"
    return replace(
        binary_entry,
        coherence_score=coherence_score if coherence_score is not None else binary_entry.coherence_score,
        status=status,
    )


def attach_lv2_cross_lingual_support(binary_entry: BinaryFieldEntry, *, language: str, replicated: bool) -> BinaryFieldEntry:
    support = dict(binary_entry.cross_lingual_support or {})
    support[language] = {"replicated": replicated}
    return replace(binary_entry, cross_lingual_support=support)


def is_promotable_binary_field(entry: BinaryFieldEntry) -> bool:
    return entry.coherence_score is not None and entry.coherence_score > 0 and bool(entry.field_gloss_source)


def is_promotable_letter_semantics(entry: LetterSemanticEntry) -> bool:
    return bool(entry.canonical_semantic_gloss and entry.sources)


def is_promotable_positional_profile(position_profile: dict[str, Any] | None) -> bool:
    if not position_profile:
        return False
    p_value = position_profile.get("p_value")
    return p_value is not None and p_value < 0.01


def is_promotable_quranic_profile(profile: QuranicSemanticProfile) -> bool:
    return profile.status in {"tested", "promoted"} and bool(profile.conceptual_meaning)
