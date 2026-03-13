"""Tests for juthoor_arabicgenome_lv1.core.loaders using real data files."""
from __future__ import annotations

import pytest
from juthoor_arabicgenome_lv1.core.loaders import (
    load_binary_roots,
    load_genome_v2,
    load_letters,
    load_root_families,
    load_triliteral_roots,
)
from juthoor_arabicgenome_lv1.core.models import (
    BinaryRoot,
    Letter,
    RootFamily,
    TriliteralRoot,
)


# ---------------------------------------------------------------------------
# load_letters
# ---------------------------------------------------------------------------

def test_load_letters_count():
    letters = load_letters()
    assert len(letters) == 28, f"Expected 28 letters, got {len(letters)}"


def test_load_letters_type():
    letters = load_letters()
    for ltr in letters:
        assert isinstance(ltr, Letter)


def test_load_letters_fields_non_empty():
    letters = load_letters()
    for ltr in letters:
        assert ltr.letter, "letter field must not be empty"
        assert ltr.letter_name, "letter_name field must not be empty"
        assert ltr.meaning, "meaning field must not be empty"


def test_load_letters_phonetic_features_optional():
    letters = load_letters()
    # phonetic_features is optional; at least verify it is None or str
    for ltr in letters:
        assert ltr.phonetic_features is None or isinstance(ltr.phonetic_features, str)


# ---------------------------------------------------------------------------
# load_binary_roots
# ---------------------------------------------------------------------------

def test_load_binary_roots_type():
    brs = load_binary_roots()
    for br in brs:
        assert isinstance(br, BinaryRoot)


def test_load_binary_roots_deduplicated():
    brs = load_binary_roots()
    keys = [br.binary_root for br in brs]
    assert len(keys) == len(set(keys)), "binary_root values must be unique"


def test_load_binary_roots_approximate_count():
    brs = load_binary_roots()
    # Muajam covers ~457 unique binary roots (memory: ~457)
    assert 400 <= len(brs) <= 600, f"Unexpected binary root count: {len(brs)}"


def test_load_binary_roots_meaning_is_string():
    """meaning is a str; some entries legitimately have empty meaning in the source."""
    brs = load_binary_roots()
    for br in brs:
        assert isinstance(br.meaning, str), f"BinaryRoot {br.binary_root!r} meaning must be str"


# ---------------------------------------------------------------------------
# load_triliteral_roots
# ---------------------------------------------------------------------------

def test_load_triliteral_roots_type():
    trs = load_triliteral_roots()
    for tr in trs:
        assert isinstance(tr, TriliteralRoot)


def test_load_triliteral_roots_approximate_count():
    trs = load_triliteral_roots()
    # Muajam has ~1938 triliteral entries
    assert 1800 <= len(trs) <= 2100, f"Unexpected triliteral count: {len(trs)}"


def test_load_triliteral_roots_fields():
    trs = load_triliteral_roots()
    for tr in trs:
        assert tr.tri_root, "tri_root must not be empty"
        assert tr.binary_root, "binary_root must not be empty"
        assert isinstance(tr.quran_example, str), "quran_example must be a str"
        assert tr.semantic_score is None or isinstance(tr.semantic_score, float)


# ---------------------------------------------------------------------------
# load_root_families
# ---------------------------------------------------------------------------

def test_load_root_families_type():
    families = load_root_families()
    assert isinstance(families, dict)
    for fam in families.values():
        assert isinstance(fam, RootFamily)


def test_load_root_families_keys_match_binary_roots():
    families = load_root_families()
    brs = load_binary_roots()
    br_keys = {br.binary_root for br in brs}
    # Every family key should come from the known binary roots
    for key in families:
        assert key in br_keys, f"Family key {key!r} not found in binary roots"


def test_load_root_families_roots_are_tuples():
    families = load_root_families()
    for fam in families.values():
        assert isinstance(fam.roots, tuple)
        assert isinstance(fam.word_forms, tuple)
        assert len(fam.roots) == len(fam.word_forms)


def test_load_root_families_coverage():
    families = load_root_families()
    # Should have roughly the same count as unique binary roots in triliterals
    assert len(families) >= 400, f"Too few families: {len(families)}"


def test_load_root_families_grouping_correct():
    """All triliterals for a binary_root must appear in that family."""
    trs = load_triliteral_roots()
    families = load_root_families()
    for tr in trs:
        fam = families[tr.binary_root]
        assert tr.tri_root in fam.roots, (
            f"{tr.tri_root!r} missing from family {tr.binary_root!r}"
        )


def test_load_root_families_matched_count():
    """matched_count must equal number of triliterals with quran_example."""
    families = load_root_families()
    trs = load_triliteral_roots()
    from collections import defaultdict
    expected: dict[str, int] = defaultdict(int)
    for tr in trs:
        if tr.quran_example:
            expected[tr.binary_root] += 1
    for br_key, fam in families.items():
        assert fam.matched_count == expected[br_key], (
            f"matched_count mismatch for {br_key!r}: "
            f"got {fam.matched_count}, expected {expected[br_key]}"
        )


# ---------------------------------------------------------------------------
# load_genome_v2
# ---------------------------------------------------------------------------

def test_load_genome_v2_ba():
    records = load_genome_v2("ب")  # "ب"
    assert len(records) > 0, "Expected records for bab ب"
    for rec in records:
        assert "bab" in rec
        assert "binary_root" in rec
        assert "root" in rec
        assert "words" in rec
        assert isinstance(rec["words"], list)
        assert "muajam_match" in rec


def test_load_genome_v2_hamza():
    records = load_genome_v2("ء")  # "ء"
    assert len(records) > 0, "Expected records for bab ء"


def test_load_genome_v2_missing_bab():
    with pytest.raises(FileNotFoundError):
        load_genome_v2("NONEXISTENT_BAB")


def test_load_genome_v2_returns_list_of_dicts():
    records = load_genome_v2("ب")
    assert isinstance(records, list)
    for rec in records:
        assert isinstance(rec, dict)
