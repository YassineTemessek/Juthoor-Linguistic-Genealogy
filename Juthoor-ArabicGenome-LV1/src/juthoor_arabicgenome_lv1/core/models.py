from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Letter:
    """Single Arabic letter with its phonosemantic meaning.

    Source: letter_meanings.jsonl
    Fields: letter, letter_name, meaning
    """
    letter: str
    letter_name: str
    meaning: str
    phonetic_features: Optional[str] = None


@dataclass(frozen=True)
class BinaryRoot:
    """Two-letter Arabic root with combined meaning.

    Source: roots.jsonl
    Fields used: binary_root, binary_root_meaning, letter1, letter1_meaning,
                 letter2, letter2_meaning, bab, bab_meaning.
    """
    binary_root: str
    meaning: str
    letter1: str
    letter2: str
    letter1_meaning: str
    letter2_meaning: str
    bab: Optional[str] = None
    bab_meaning: Optional[str] = None


@dataclass(frozen=True)
class TriliteralRoot:
    """Three-letter Arabic root derived from a binary root.

    Source: roots.jsonl
    Fields: tri_root, binary_root, added_letter, axial_meaning, quran_example.
    Notes:
    - tri_root may contain '/' for compound forms (e.g. aawb/aayb).
    - quran_example is empty string when no Quranic usage exists.
    - semantic_score from Phase 3 BGE-M3 scoring; present in genome_v2.
    """
    tri_root: str
    binary_root: str
    added_letter: str
    axial_meaning: str
    quran_example: str
    semantic_score: Optional[float] = None


@dataclass(frozen=True)
class RootFamily:
    """Family of triliteral roots sharing the same binary root.

    Source: genome_v2/*.jsonl grouped by binary_root.
    Each genome entry has: bab, binary_root, root, words (list), muajam_match (bool).
    """
    binary_root: str
    roots: tuple
    word_forms: tuple
    bab: Optional[str] = None
    matched_count: int = 0


@dataclass(frozen=True)
class MetathesisPair:
    """Binary roots that are letter-transpositions of each other (XY / YX).

    Computed entity; no direct source file.
    """
    br1: str
    br2: str
    meaning1: str
    meaning2: str
    similarity: Optional[float] = None


@dataclass(frozen=True)
class SubstitutionPair:
    """Triliteral roots differing by exactly one letter (minimal pair).

    Computed entity; no direct source file.
    """
    root1: str
    root2: str
    changed_position: int
    original_letter: str
    substitute_letter: str
    makhraj_distance: Optional[float] = None


@dataclass(frozen=True)
class PermutationGroup:
    """Set of roots that are permutations of the same three letters.

    Computed entity; no direct source file.
    """
    group_key: str
    shared_letters: tuple
    roots: tuple
    mean_similarity: Optional[float] = None
