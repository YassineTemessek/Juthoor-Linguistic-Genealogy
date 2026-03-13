"""Data loaders for the LV1 ArabicGenome core models.

All functions read from files relative to the Juthoor-ArabicGenome-LV1 project
root, resolved via __file__ so they work regardless of the working directory.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .models import BinaryRoot, Letter, RootFamily, TriliteralRoot


def _lv1_root() -> Path:
    """Return the Juthoor-ArabicGenome-LV1 directory.

    File layout:
        Juthoor-ArabicGenome-LV1/
            src/
                juthoor_arabicgenome_lv1/
                    core/
                        loaders.py   <- __file__
    Four parents up from loaders.py lands at the LV1 root.
    """
    return Path(__file__).resolve().parents[3]


def load_letters() -> list[Letter]:
    """Load all Arabic letters from data/muajam/letter_meanings.jsonl.

    Returns one Letter per line (28 letters).
    """
    path = _lv1_root() / "data" / "muajam" / "letter_meanings.jsonl"
    letters: list[Letter] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            letters.append(
                Letter(
                    letter=obj["letter"],
                    letter_name=obj["letter_name"],
                    meaning=obj["meaning"],
                    phonetic_features=obj.get("phonetic_features"),
                )
            )
    return letters


def load_binary_roots() -> list[BinaryRoot]:
    """Load deduplicated BinaryRoot records from data/muajam/roots.jsonl.

    Each row in roots.jsonl repeats binary_root data for every triliteral.
    Deduplicates by binary_root, keeping the first occurrence.

    JSON field mapping:
        binary_root         -> binary_root
        binary_root_meaning -> meaning
        letter1             -> letter1
        letter2             -> letter2
        letter1_meaning     -> letter1_meaning
        letter2_meaning     -> letter2_meaning
        bab                 -> bab
        bab_meaning         -> bab_meaning
    """
    path = _lv1_root() / "data" / "muajam" / "roots.jsonl"
    seen: set[str] = set()
    binary_roots: list[BinaryRoot] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            br_key = obj["binary_root"]
            if br_key in seen:
                continue
            seen.add(br_key)
            binary_roots.append(
                BinaryRoot(
                    binary_root=br_key,
                    meaning=obj["binary_root_meaning"],
                    letter1=obj["letter1"],
                    letter2=obj["letter2"],
                    letter1_meaning=obj["letter1_meaning"],
                    letter2_meaning=obj["letter2_meaning"],
                    bab=obj.get("bab"),
                    bab_meaning=obj.get("bab_meaning"),
                )
            )
    return binary_roots


def load_triliteral_roots() -> list[TriliteralRoot]:
    """Load all TriliteralRoot records from data/muajam/roots.jsonl.

    JSON field mapping:
        tri_root      -> tri_root
        binary_root   -> binary_root
        added_letter  -> added_letter
        axial_meaning -> axial_meaning
        quran_example -> quran_example
    semantic_score defaults to None (populated by Phase 3 scoring).
    """
    path = _lv1_root() / "data" / "muajam" / "roots.jsonl"
    tri_roots: list[TriliteralRoot] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            tri_roots.append(
                TriliteralRoot(
                    tri_root=obj["tri_root"],
                    binary_root=obj["binary_root"],
                    added_letter=obj["added_letter"],
                    axial_meaning=obj["axial_meaning"],
                    quran_example=obj.get("quran_example", ""),
                    semantic_score=obj.get("semantic_score"),
                )
            )
    return tri_roots


def load_root_families() -> dict[str, RootFamily]:
    """Group TriliteralRoot records by binary_root into RootFamily objects.

    Returns a dict keyed by binary_root string. Each RootFamily contains:
        - roots: tuple of tri_root strings
        - word_forms: tuple of axial_meaning strings (semantic labels per root)
        - bab: from the corresponding BinaryRoot record
        - matched_count: number of triliterals with a non-empty quran_example

    Note: RootFamily.word_forms stores axial meanings as proxy word-form labels
    because roots.jsonl carries no inflected word-form list. Inflected forms
    live in genome_v2 files keyed by root string.
    """
    tri_roots = load_triliteral_roots()
    binary_root_map: dict[str, BinaryRoot] = {
        br.binary_root: br for br in load_binary_roots()
    }

    groups: dict[str, list[TriliteralRoot]] = {}
    for tr in tri_roots:
        groups.setdefault(tr.binary_root, []).append(tr)

    families: dict[str, RootFamily] = {}
    for br_key, members in groups.items():
        br = binary_root_map.get(br_key)
        bab: Optional[str] = br.bab if br else None
        roots_tuple = tuple(tr.tri_root for tr in members)
        word_forms_tuple = tuple(tr.axial_meaning for tr in members)
        matched = sum(1 for tr in members if tr.quran_example)
        families[br_key] = RootFamily(
            binary_root=br_key,
            roots=roots_tuple,
            word_forms=word_forms_tuple,
            bab=bab,
            matched_count=matched,
        )
    return families


def load_genome_v2(bab: str) -> list[dict]:
    """Load raw genome_v2 records for a given BAB letter.

    Args:
        bab: Arabic letter string for the BAB file (e.g. "ب", "ء").

    Returns:
        List of dicts with keys: bab, binary_root, root, words, muajam_match.

    Raises:
        FileNotFoundError: if the BAB file does not exist in outputs/genome_v2/.
    """
    path = _lv1_root() / "outputs" / "genome_v2" / f"{bab}.jsonl"
    records: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records
