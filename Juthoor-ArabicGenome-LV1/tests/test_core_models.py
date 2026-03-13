"""Tests for core frozen dataclass models (Task 0.1)."""
from __future__ import annotations
import pytest
from dataclasses import FrozenInstanceError
from juthoor_arabicgenome_lv1.core.models import (
    Letter, BinaryRoot, TriliteralRoot, RootFamily,
    MetathesisPair, SubstitutionPair, PermutationGroup,
)

# Arabic strings via unicode escapes
BA     = 'ب'
HA     = 'ح'
RA     = 'ر'
DAL    = 'د'
KHAL   = 'خ'
KAF    = 'ك'
TAA    = 'ت'
WAW    = 'و'
YAA    = 'ي'
ALF    = 'ا'
LAM    = 'ل'
JIM    = 'ج'
MEM    = 'م'
AIN    = 'ع'
TA2    = 'ة'
HMZ    = 'ء'
FA     = 'ف'
DAD    = 'ض'
SIN2   = 'س'
NUN    = 'ن'

BH   = BA+HA
BD   = BA+DAL
BHR  = BA+HA+RA
BKR  = BA+KHAL+RA
BRH  = BA+RA+HA
HBR  = HA+BA+RA
HRB  = HA+RA+BA
RBH  = RA+BA+HA
RHB  = RA+HA+BA
BDR  = BA+DAL+RA
RBD  = RA+BA+DAL
KTB  = KAF+TAA+BA
TKB  = TAA+KAF+BA
BHL  = BA+HA+LAM
HBA  = HA+BA
DAB  = DAL+BA

BA_NAME  = BA+ALF+HMZ
KAF_NAME = KAF+ALF+FA
SIN_NAME = SIN2+YAA+NUN

BA_MEAN  = ALF+LAM+JIM+MEM+AIN
HA_MEAN  = ALF+LAM+HMZ+HA+ALF+'ط'+TA2
RA_MEAN  = ALF+LAM+ALF+MEM+TAA+DAL+ALF+DAL
KAF_MEAN = ALF+LAM+TAA+'ش'+'ب'+YAA+HA
SIN_MEAN = ALF+LAM+SIN2+YAA+LAM+ALF+NUN
BH_MEAN  = ALF+LAM+ALF+TAA+SIN2+ALF+AIN
HABS     = HA+BA+SIN2
BAB_NAME = BA+ALF+'ب'+' '+ALF+LAM+BA+ALF+HMZ
IBTIDAA  = ALF+BA+TAA+DAL+ALF+HMZ
IMTIDAD  = ALF+MEM+TAA+DAL+ALF+DAL
DABEEB   = DAL+BA+YAA+BA
BUDUR    = BA+DAL+WAW+RA
BHR_AX   = BH_MEAN+' '+FA+YAA+' '+ALF+LAM+AIN+RA+DAD
COMPOUND = 'أ'+WAW+BA+'/'+'أ'+YAA+BA
CPND_BR  = 'أ'+BA
BHR_QRN  = WAW+'َ'+HA+'ُ'+WAW+'َ'+' '+ALF+'ّ'+'َ'+'ذ'+'ِ'+YAA



class TestLetter:
    def test_construction_real_data(self):
        letter = Letter(letter=BA, letter_name=BA_NAME, meaning=BA_MEAN)
        assert letter.letter == BA
        assert letter.letter_name == BA_NAME
        assert letter.phonetic_features is None
    def test_optional_phonetic_features_set(self):
        letter = Letter(letter=SIN2, letter_name=SIN_NAME, meaning=SIN_MEAN, phonetic_features='sibilant')
        assert letter.phonetic_features == 'sibilant'
    def test_frozen_raises_on_mutation(self):
        letter = Letter(letter=BA, letter_name=BA_NAME, meaning=BA_MEAN)
        with pytest.raises(FrozenInstanceError):
            letter.letter = KAF  # type: ignore[misc]
    def test_equality_and_hash(self):
        a = Letter(letter=BA, letter_name=BA_NAME, meaning=BA_MEAN)
        b = Letter(letter=BA, letter_name=BA_NAME, meaning=BA_MEAN)
        assert a == b
        assert hash(a) == hash(b)


class TestBinaryRoot:
    def test_construction_real_data(self):
        br = BinaryRoot(binary_root=BH, meaning=BH_MEAN, letter1=BA, letter2=HA,
                        letter1_meaning=BA_MEAN, letter2_meaning=HA_MEAN)
        assert br.binary_root == BH
        assert br.bab is None
        assert br.bab_meaning is None
    def test_optional_bab_set(self):
        br = BinaryRoot(binary_root=BH, meaning=BH_MEAN, letter1=BA, letter2=HA,
                        letter1_meaning=BA_MEAN, letter2_meaning=HA_MEAN,
                        bab=BAB_NAME, bab_meaning=BA_MEAN)
        assert br.bab == BAB_NAME
        assert br.bab_meaning == BA_MEAN
    def test_frozen_raises_on_mutation(self):
        br = BinaryRoot(binary_root=BH, meaning=BH_MEAN, letter1=BA, letter2=HA,
                        letter1_meaning=BA_MEAN, letter2_meaning=HA_MEAN)
        with pytest.raises(FrozenInstanceError):
            br.binary_root = BD  # type: ignore[misc]
    def test_hashable_as_dict_key(self):
        br = BinaryRoot(binary_root=BD, meaning=IBTIDAA, letter1=BA, letter2=DAL,
                        letter1_meaning=BA_MEAN, letter2_meaning=IMTIDAD)
        d = {br: 'ok'}
        assert d[br] == 'ok'


class TestTriliteralRoot:
    def test_construction_real_data(self):
        tri = TriliteralRoot(tri_root=BHR, binary_root=BH, added_letter=RA,
                             axial_meaning=BHR_AX, quran_example=BHR_QRN)
        assert tri.tri_root == BHR
        assert tri.semantic_score is None
    def test_compound_slash_form(self):
        tri = TriliteralRoot(tri_root=COMPOUND, binary_root=CPND_BR,
                             added_letter=WAW, axial_meaning=BH_MEAN, quran_example='')
        assert '/' in tri.tri_root
    def test_empty_quran_example_allowed(self):
        tri = TriliteralRoot(tri_root=BHL, binary_root=BH, added_letter=LAM,
                             axial_meaning=BH_MEAN, quran_example='')
        assert tri.quran_example == ''
    def test_semantic_score_set(self):
        tri = TriliteralRoot(tri_root=BHR, binary_root=BH, added_letter=RA,
                             axial_meaning=BHR_AX, quran_example='', semantic_score=0.87)
        assert abs(tri.semantic_score - 0.87) < 1e-9
    def test_frozen_raises_on_mutation(self):
        tri = TriliteralRoot(tri_root=BHR, binary_root=BH, added_letter=RA,
                             axial_meaning=BHR_AX, quran_example='')
        with pytest.raises(FrozenInstanceError):
            tri.semantic_score = 0.5  # type: ignore[misc]


class TestRootFamily:
    def test_construction_real_data(self):
        family = RootFamily(binary_root=BH, roots=(BHR, BHL), word_forms=(BHR, BUDUR),
                            bab=BAB_NAME, matched_count=2)
        assert family.binary_root == BH
        assert len(family.roots) == 2
        assert family.matched_count == 2
    def test_optional_bab_defaults(self):
        family = RootFamily(binary_root=BD, roots=(BDR,), word_forms=(BDR,))
        assert family.bab is None
        assert family.matched_count == 0
    def test_roots_and_word_forms_are_tuples(self):
        family = RootFamily(binary_root=BH, roots=(BHR,), word_forms=(BHR,))
        assert isinstance(family.roots, tuple)
        assert isinstance(family.word_forms, tuple)
    def test_frozen_raises_on_mutation(self):
        family = RootFamily(binary_root=BH, roots=(BHR,), word_forms=(BHR,))
        with pytest.raises(FrozenInstanceError):
            family.binary_root = BD  # type: ignore[misc]


class TestMetathesisPair:
    def test_construction_basic(self):
        pair = MetathesisPair(br1=BH, br2=HBA, meaning1=BH_MEAN, meaning2=HABS)
        assert pair.br1 == BH
        assert pair.similarity is None
    def test_similarity_set(self):
        pair = MetathesisPair(br1=BH, br2=HBA, meaning1=BH_MEAN, meaning2=HABS, similarity=0.72)
        assert pair.similarity == pytest.approx(0.72)
    def test_frozen_raises_on_mutation(self):
        pair = MetathesisPair(br1=BD, br2=DAB, meaning1=IBTIDAA, meaning2=DABEEB)
        with pytest.raises(FrozenInstanceError):
            pair.similarity = 0.5  # type: ignore[misc]
    def test_hashable(self):
        pair = MetathesisPair(br1=BH, br2=HBA, meaning1=BH_MEAN, meaning2=HABS)
        assert hash(pair) is not None


class TestSubstitutionPair:
    def test_construction_basic(self):
        pair = SubstitutionPair(root1=BHR, root2=BKR, changed_position=1,
                                original_letter=HA, substitute_letter=KHAL)
        assert pair.changed_position == 1
        assert pair.makhraj_distance is None
    def test_makhraj_distance_set(self):
        pair = SubstitutionPair(root1=BHR, root2=BKR, changed_position=1,
                                original_letter=HA, substitute_letter=KHAL, makhraj_distance=0.15)
        assert pair.makhraj_distance == pytest.approx(0.15)
    def test_changed_position_all_slots(self):
        for pos in (0, 1, 2):
            pair = SubstitutionPair(root1=BHR, root2=BKR, changed_position=pos,
                                    original_letter=HA, substitute_letter=KHAL)
            assert pair.changed_position == pos
    def test_frozen_raises_on_mutation(self):
        pair = SubstitutionPair(root1=BHR, root2=BKR, changed_position=1,
                                original_letter=HA, substitute_letter=KHAL)
        with pytest.raises(FrozenInstanceError):
            pair.changed_position = 2  # type: ignore[misc]


class TestPermutationGroup:
    def test_construction_real_letters(self):
        group = PermutationGroup(group_key=BHR, shared_letters=(BA, HA, RA),
                                 roots=(BHR, BRH, HBR, HRB, RBH, RHB))
        assert group.group_key == BHR
        assert len(group.roots) == 6
        assert group.mean_similarity is None
    def test_mean_similarity_set(self):
        group = PermutationGroup(group_key=BHR, shared_letters=(BA, HA, RA),
                                 roots=(BHR, RHB), mean_similarity=0.68)
        assert group.mean_similarity == pytest.approx(0.68)
    def test_shared_letters_is_tuple(self):
        group = PermutationGroup(group_key=KTB, shared_letters=(KAF, TAA, BA), roots=(KTB, TKB))
        assert isinstance(group.shared_letters, tuple)
        assert isinstance(group.roots, tuple)
    def test_frozen_raises_on_mutation(self):
        group = PermutationGroup(group_key=BHR, shared_letters=(BA, HA, RA), roots=(BHR,))
        with pytest.raises(FrozenInstanceError):
            group.mean_similarity = 0.5  # type: ignore[misc]
    def test_partial_permutation_group(self):
        group = PermutationGroup(group_key=BDR, shared_letters=(BA, DAL, RA), roots=(BDR, RBD))
        assert len(group.roots) == 2
