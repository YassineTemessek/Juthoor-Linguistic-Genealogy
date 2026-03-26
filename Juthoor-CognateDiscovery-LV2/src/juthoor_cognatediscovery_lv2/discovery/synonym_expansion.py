"""Expand Arabic root queries using LV1 synonym families.

When searching for cross-lingual cognates, expand the query root
to include all members of its synonym family. This catches cases
like Hebrew לב matching Arabic لب (not قلب).
"""
from __future__ import annotations

import json
from pathlib import Path


def load_synonym_families(path: str) -> dict[str, list[str]]:
    """Load synonym families and build a root→family lookup.

    Each JSONL line is a family with a ``roots`` list. Every root in the
    family maps to the complete list of sibling roots (including itself).

    Args:
        path: Absolute or relative path to the synonym_families_full.jsonl file.

    Returns:
        Mapping from Arabic root string to all roots in its synonym family.
    """
    lookup: dict[str, list[str]] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        family = json.loads(line)
        roots: list[str] = family.get("roots", [])
        if not roots:
            continue
        for root in roots:
            # Store the full family list for every member root.
            lookup[root] = roots
    return lookup


def expand_root(root: str, families: dict[str, list[str]]) -> list[str]:
    """Given a root, return all roots in its synonym family (including itself).

    If the root is not found in any family, returns a single-element list
    containing only the root itself.

    Args:
        root: An Arabic root string to look up.
        families: Lookup produced by :func:`load_synonym_families`.

    Returns:
        List of Arabic root strings that share the same synonym family,
        always including ``root`` itself.
    """
    if root in families:
        # Return a copy to avoid mutation of the shared lookup.
        return list(families[root])
    return [root]
