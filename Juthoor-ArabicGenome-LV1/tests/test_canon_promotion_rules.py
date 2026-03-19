from __future__ import annotations

from juthoor_arabicgenome_lv1.core.canon_models import BinaryFieldEntry, LetterSemanticEntry, QuranicSemanticProfile, SourceEntry
from juthoor_arabicgenome_lv1.factory.canon_feedback import (
    attach_lv1_support,
    attach_lv2_cross_lingual_support,
    is_promotable_binary_field,
    is_promotable_letter_semantics,
    is_promotable_positional_profile,
    is_promotable_quranic_profile,
)


def _source() -> tuple[SourceEntry, ...]:
    return (
        SourceEntry(
            source_id="seed",
            scholar="jabal",
            claim_type="semantic",
            claim_text="demo",
            document_ref="doc",
            curation_status="accepted",
        ),
    )


def test_attach_lv1_support_marks_tested() -> None:
    entry = BinaryFieldEntry("بر", "gloss", "jabal", "ب", "ر", None, None, (), 0, None, None, "draft")
    updated = attach_lv1_support(entry, coherence_score=0.7, provenance_exists=True)

    assert updated.coherence_score == 0.7
    assert updated.status == "tested"


def test_cross_lingual_support_attaches_language() -> None:
    entry = BinaryFieldEntry("بر", "gloss", "jabal", "ب", "ر", None, None, (), 0, None, None, "draft")
    updated = attach_lv2_cross_lingual_support(entry, language="hebrew", replicated=True)

    assert updated.cross_lingual_support == {"hebrew": {"replicated": True}}


def test_promotion_predicates() -> None:
    binary = BinaryFieldEntry("بر", "gloss", "jabal", "ب", "ر", None, None, (), 0, 0.5, None, "tested")
    letter = LetterSemanticEntry("ب", "الباء", "بروز", None, None, None, _source(), "majority", "medium", "draft")
    quranic = QuranicSemanticProfile("الأرض", "ارض", "surface", "expanse", "earth", None, (), (), None, "medium", "tested")

    assert is_promotable_binary_field(binary) is True
    assert is_promotable_letter_semantics(letter) is True
    assert is_promotable_positional_profile({"p_value": 0.001}) is True
    assert is_promotable_quranic_profile(quranic) is True
