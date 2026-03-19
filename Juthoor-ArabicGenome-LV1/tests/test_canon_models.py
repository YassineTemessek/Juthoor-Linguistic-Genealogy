from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from juthoor_arabicgenome_lv1.core.canon_models import (
    BinaryFieldEntry,
    LetterSemanticEntry,
    QuranicSemanticProfile,
    RootCompositionEntry,
    SourceEntry,
    TheoryClaim,
)


def test_source_entry_minimal() -> None:
    entry = SourceEntry(
        source_id="src-1",
        scholar="jabal",
        claim_type="semantic",
        claim_text="gloss",
        document_ref="doc",
        curation_status="reviewed",
    )
    assert entry.scholar == "jabal"


def test_letter_semantic_entry_minimal() -> None:
    entry = LetterSemanticEntry(
        letter="ب",
        letter_name="الباء",
        canonical_semantic_gloss=None,
        canonical_kinetic_gloss=None,
        canonical_sensory_gloss=None,
        articulatory_features=None,
        sources=(),
        agreement_level="unknown",
        confidence_tier="stub",
        status="empty",
    )
    assert entry.status == "empty"


def test_binary_field_entry_minimal() -> None:
    entry = BinaryFieldEntry(
        binary_root="حس",
        field_gloss=None,
        field_gloss_source=None,
        letter1="ح",
        letter2="س",
        letter1_gloss=None,
        letter2_gloss=None,
        member_roots=(),
        member_count=0,
        coherence_score=None,
        cross_lingual_support=None,
        status="draft",
    )
    assert entry.binary_root == "حس"


def test_root_composition_entry_minimal() -> None:
    entry = RootCompositionEntry(
        root="حسد",
        binary_root="حس",
        third_letter="د",
        conceptual_root_meaning=None,
        binary_field_meaning=None,
        axial_meaning=None,
        letter_trace=None,
        position_profile=None,
        modifier_profile=None,
        compositional_signal=None,
        agreement_with_observed_gloss=None,
        status="draft",
    )
    assert entry.third_letter == "د"


def test_theory_claim_minimal() -> None:
    claim = TheoryClaim(
        claim_id="claim-1",
        theme="intentionality",
        scholar="neili",
        statement="text",
        scope="quranic_only",
        evidence_type="doctrinal",
        source_doc="doc",
        source_locator=None,
        status="asserted",
    )
    assert claim.status == "asserted"


def test_quranic_profile_minimal() -> None:
    profile = QuranicSemanticProfile(
        lemma="قلب",
        root="قلب",
        conceptual_meaning=None,
        binary_field_meaning=None,
        lexical_realization=None,
        letter_trace=None,
        contextual_constraints=None,
        contrast_lemmas=None,
        interpretive_notes=None,
        confidence="stub",
        status="draft",
    )
    assert profile.lemma == "قلب"


@pytest.mark.parametrize(
    ("cls_name", "kwargs"),
    [
        ("letter", dict(
            letter="ب", letter_name="الباء", canonical_semantic_gloss=None,
            canonical_kinetic_gloss=None, canonical_sensory_gloss=None,
            articulatory_features=None, sources=(), agreement_level="bad",
            confidence_tier="stub", status="draft",
        )),
        ("claim", dict(
            claim_id="x", theme="y", scholar="z", statement="s",
            scope="a", evidence_type="b", source_doc="c",
            source_locator=None, status="bad",
        )),
    ],
)
def test_status_validation(cls_name: str, kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        if cls_name == "letter":
            LetterSemanticEntry(**kwargs)
        else:
            TheoryClaim(**kwargs)


def test_frozen_immutability() -> None:
    entry = LetterSemanticEntry(
        letter="ب",
        letter_name="الباء",
        canonical_semantic_gloss=None,
        canonical_kinetic_gloss=None,
        canonical_sensory_gloss=None,
        articulatory_features=None,
        sources=(),
        agreement_level="unknown",
        confidence_tier="stub",
        status="draft",
    )
    with pytest.raises(FrozenInstanceError):
        entry.status = "curated"  # type: ignore[misc]
