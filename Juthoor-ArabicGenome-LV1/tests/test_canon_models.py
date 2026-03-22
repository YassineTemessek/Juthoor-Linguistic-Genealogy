from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from juthoor_arabicgenome_lv1.core.canon_models import (
    AtomicFeature,
    BinaryFieldEntry,
    BinaryNucleus,
    CompositionResult,
    FEATURE_CATEGORIES,
    LetterAtom,
    LetterRegistryEntry,
    LetterSemanticEntry,
    QuranicSemanticProfile,
    RootCompositionEntry,
    SourceEntry,
    TheoryClaim,
    TriliteralRootEntry,
    VALID_SCHOLARS,
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


# ---------------------------------------------------------------------------
# New dataclasses — AtomicFeature, LetterAtom, LetterRegistryEntry,
# BinaryNucleus, TriliteralRootEntry, CompositionResult + constants
# ---------------------------------------------------------------------------

def test_valid_scholars_is_tuple_with_expected_values() -> None:
    assert isinstance(VALID_SCHOLARS, tuple)
    assert "jabal" in VALID_SCHOLARS
    assert "hassan_abbas" in VALID_SCHOLARS
    assert "anbar" in VALID_SCHOLARS
    assert len(VALID_SCHOLARS) == 8


def test_feature_categories_is_tuple_with_9_entries() -> None:
    assert isinstance(FEATURE_CATEGORIES, tuple)
    assert len(FEATURE_CATEGORIES) == 9
    assert "gathering_cohesion" in FEATURE_CATEGORIES
    assert "pressure_force" in FEATURE_CATEGORIES
    assert "independence_distinction" in FEATURE_CATEGORIES


def test_atomic_feature_minimal() -> None:
    feat = AtomicFeature(
        arabic="تجمع",
        english="gathering",
        category="gathering_cohesion",
    )
    assert feat.arabic == "تجمع"
    assert feat.category == "gathering_cohesion"


def test_atomic_feature_frozen() -> None:
    feat = AtomicFeature(arabic="تجمع", english="gathering", category="gathering_cohesion")
    with pytest.raises(FrozenInstanceError):
        feat.arabic = "ضغط"  # type: ignore[misc]


def test_letter_atom_full_fields() -> None:
    atom = LetterAtom(
        letter="ب",
        letter_name="الباء",
        scholar="hassan_abbas",
        raw_description="الباء حرف شفوي يدل على الاحتواء والتجمع",
        atomic_features=("تجمع", "رخاوة", "تلاصق"),
        feature_categories=("gathering_cohesion", "texture_quality", "gathering_cohesion"),
        sensory_category="لمسية",
        kinetic_gloss=None,
        source_document="خصائص الحروف العربية",
        confidence="high",
    )
    assert atom.scholar == "hassan_abbas"
    assert atom.sensory_category == "لمسية"
    assert len(atom.atomic_features) == 3
    assert atom.kinetic_gloss is None


def test_letter_atom_neili_with_kinetic_gloss() -> None:
    atom = LetterAtom(
        letter="ر",
        letter_name="الراء",
        scholar="neili",
        raw_description="الراء حرف يدل على الاسترسال والتدفق",
        atomic_features=("استرسال", "امتداد"),
        feature_categories=("extension_movement", "extension_movement"),
        sensory_category=None,
        kinetic_gloss="تدفق مستمر للأمام",
        source_document="قصدية الإشارة",
        confidence="medium",
    )
    assert atom.kinetic_gloss == "تدفق مستمر للأمام"
    assert atom.sensory_category is None


def test_letter_atom_frozen() -> None:
    atom = LetterAtom(
        letter="ب",
        letter_name="الباء",
        scholar="jabal",
        raw_description="gloss",
        atomic_features=(),
        feature_categories=(),
        sensory_category=None,
        kinetic_gloss=None,
        source_document="doc",
        confidence="stub",
    )
    with pytest.raises(FrozenInstanceError):
        atom.confidence = "high"  # type: ignore[misc]


def test_letter_registry_entry_minimal() -> None:
    atom = LetterAtom(
        letter="ب",
        letter_name="الباء",
        scholar="jabal",
        raw_description="gloss",
        atomic_features=("تجمع",),
        feature_categories=("gathering_cohesion",),
        sensory_category=None,
        kinetic_gloss=None,
        source_document="doc",
        confidence="stub",
    )
    entry = LetterRegistryEntry(
        letter="ب",
        letter_name="الباء",
        scholar_entries=(atom,),
        consensus_features=("تجمع",),
        agreement_level="insufficient",
        articulatory_features=None,
    )
    assert entry.letter == "ب"
    assert len(entry.scholar_entries) == 1
    assert entry.articulatory_features is None


def test_binary_nucleus_without_scoring() -> None:
    nucleus = BinaryNucleus(
        binary_root="حس",
        letter1="ح",
        letter2="س",
        jabal_shared_meaning="الإحساس الظاهر",
        jabal_features=("نفاذ", "ظاهر"),
        member_roots=("حسد", "حسن", "حسب"),
        member_count=3,
        reverse_exists=True,
        reverse_root="سح",
        model_a_score=None,
        model_b_score=None,
        model_c_score=None,
        model_d_score=None,
        best_model=None,
        golden_rule_score=None,
        status="empty",
    )
    assert nucleus.binary_root == "حس"
    assert nucleus.reverse_exists is True
    assert nucleus.model_a_score is None
    assert nucleus.status == "empty"


def test_binary_nucleus_with_scoring() -> None:
    nucleus = BinaryNucleus(
        binary_root="كت",
        letter1="ك",
        letter2="ت",
        jabal_shared_meaning="الكتابة والتسجيل",
        jabal_features=("تجمع", "تلاصق"),
        member_roots=("كتب", "كتم"),
        member_count=2,
        reverse_exists=False,
        reverse_root=None,
        model_a_score=0.65,
        model_b_score=0.72,
        model_c_score=0.58,
        model_d_score=0.61,
        best_model="model_b",
        golden_rule_score=None,
        status="scored",
    )
    assert nucleus.model_b_score == 0.72
    assert nucleus.best_model == "model_b"
    assert nucleus.reverse_root is None


def test_trilateral_root_entry_without_prediction() -> None:
    entry = TriliteralRootEntry(
        root="كتب",
        binary_nucleus="كت",
        third_letter="ب",
        jabal_axial_meaning="الكتابة والتسجيل",
        jabal_features=("تجمع", "تلاصق"),
        predicted_meaning=None,
        predicted_features=None,
        prediction_score=None,
        quranic_verse=None,
        bab="BAB_01",
        status="empty",
    )
    assert entry.root == "كتب"
    assert entry.predicted_meaning is None
    assert entry.prediction_score is None


def test_trilateral_root_entry_with_prediction() -> None:
    entry = TriliteralRootEntry(
        root="فهم",
        binary_nucleus="فه",
        third_letter="م",
        jabal_axial_meaning="الإدراك والفهم",
        jabal_features=("نفاذ", "خلوص"),
        predicted_meaning="اختراق المعنى",
        predicted_features=("نفاذ", "اختراق"),
        prediction_score=0.67,
        quranic_verse="وَلَقَدْ آتَيْنَا دَاوُودَ وَسُلَيْمَانَ عِلْمًا",
        bab="BAB_05",
        status="scored",
    )
    assert entry.prediction_score == 0.67
    assert entry.predicted_features == ("نفاذ", "اختراق")
    assert entry.quranic_verse is not None


def test_composition_result_valid_scores() -> None:
    result = CompositionResult(
        nucleus="حس",
        model="model_b",
        scholar_letters="hassan_abbas",
        predicted_features=("نفاذ", "ظاهر", "تجمع"),
        actual_features=("نفاذ", "ظاهر"),
        jaccard_score=0.667,
        weighted_score=0.71,
        matched_features=("نفاذ", "ظاهر"),
        missed_features=(),
        extra_features=("تجمع",),
    )
    assert result.jaccard_score == pytest.approx(0.667)
    assert result.matched_features == ("نفاذ", "ظاهر")
    assert result.missed_features == ()
    assert result.extra_features == ("تجمع",)


def test_composition_result_frozen() -> None:
    result = CompositionResult(
        nucleus="حس",
        model="model_a",
        scholar_letters="jabal",
        predicted_features=(),
        actual_features=(),
        jaccard_score=0.0,
        weighted_score=0.0,
        matched_features=(),
        missed_features=(),
        extra_features=(),
    )
    with pytest.raises(FrozenInstanceError):
        result.jaccard_score = 1.0  # type: ignore[misc]
