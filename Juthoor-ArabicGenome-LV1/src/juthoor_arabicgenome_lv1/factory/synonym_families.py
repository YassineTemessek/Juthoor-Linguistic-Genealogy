"""Synonym family extraction for cross-lingual projection support.

These families group Arabic roots that share a core semantic concept.
Used to project ALL possible Arabic source roots when searching for
cognates in target languages (e.g., Hebrew lv matches Arabic lb, not qlb).

IMPORTANT: This is for cross-lingual mining, not Quranic interpretation.
In Quranic usage, each root retains its distinct conceptual shade (Neili's
no-synonymy principle applies there, not here).
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from juthoor_arabicgenome_lv1.factory.scoring import blended_jaccard


# ---------------------------------------------------------------------------
# Seed families — manually curated, used for calibration and as anchors
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SynonymFamily:
    family_id: str
    roots: tuple[str, ...]
    shared_concept: str
    confidence: float
    source: str = "seed"  # "seed" | "extracted" | "merged"


SEED_FAMILIES: tuple[SynonymFamily, ...] = (
    SynonymFamily(
        family_id="seed-001",
        roots=("قلب", "فؤاد", "لب"),
        shared_concept="heart / inner core",
        confidence=1.0,
    ),
    SynonymFamily(
        family_id="seed-002",
        roots=("ستر", "خفي", "كتم"),
        shared_concept="conceal / hide",
        confidence=1.0,
    ),
    SynonymFamily(
        family_id="seed-003",
        roots=("جمع", "ضم", "لم", "حشد"),
        shared_concept="gather / collect",
        confidence=1.0,
    ),
    SynonymFamily(
        family_id="seed-004",
        roots=("قطع", "فصل", "بتر"),
        shared_concept="cut / sever / separate",
        confidence=1.0,
    ),
    SynonymFamily(
        family_id="seed-005",
        roots=("بيت", "دار", "منزل", "مأوى"),
        shared_concept="dwelling / house / shelter",
        confidence=1.0,
    ),
    SynonymFamily(
        family_id="seed-006",
        roots=("طريق", "سبيل", "نهج", "صراط"),
        shared_concept="path / way",
        confidence=1.0,
    ),
    SynonymFamily(
        family_id="seed-007",
        roots=("قول", "نطق", "لفظ"),
        shared_concept="speaking / uttering",
        confidence=1.0,
    ),
    SynonymFamily(
        family_id="seed-008",
        roots=("ذهب", "مضى", "مر"),
        shared_concept="go / pass",
        confidence=1.0,
    ),
    SynonymFamily(
        family_id="seed-009",
        roots=("خوف", "خشية", "رهبة"),
        shared_concept="fear",
        confidence=1.0,
    ),
    SynonymFamily(
        family_id="seed-010",
        roots=("حزن", "هم", "كرب"),
        shared_concept="grief / distress",
        confidence=1.0,
    ),
)


# ---------------------------------------------------------------------------
# Extraction from prediction rows
# ---------------------------------------------------------------------------

_OVERLAP_THRESHOLD = 0.70


def _feature_overlap(features_a: list[str], features_b: list[str]) -> float:
    """Blended Jaccard overlap between two feature lists."""
    if not features_a and not features_b:
        return 1.0
    if not features_a or not features_b:
        return 0.0
    return blended_jaccard(tuple(features_a), tuple(features_b))


def extract_families_from_predictions(
    predictions: list[dict[str, Any]],
    *,
    threshold: float = _OVERLAP_THRESHOLD,
) -> list[dict[str, Any]]:
    """Group roots from prediction rows by feature similarity.

    Args:
        predictions: List of root prediction dicts, each with keys
            ``root`` and ``predicted_features`` (list[str]).
        threshold: Minimum blended Jaccard overlap to merge two roots.

    Returns:
        List of family dicts with keys: family_id, roots, shared_concept,
        confidence, source.
    """
    # Filter to rows with non-empty features
    usable = [
        row for row in predictions
        if row.get("root") and row.get("predicted_features")
    ]

    # Union-find style grouping: iterate and cluster greedily
    clusters: list[list[dict[str, Any]]] = []

    for row in usable:
        placed = False
        for cluster in clusters:
            # Compare against the first member of the cluster (centroid proxy)
            rep = cluster[0]
            overlap = _feature_overlap(
                row.get("predicted_features", []),
                rep.get("predicted_features", []),
            )
            if overlap >= threshold:
                cluster.append(row)
                placed = True
                break
        if not placed:
            clusters.append([row])

    families: list[dict[str, Any]] = []
    for cluster in clusters:
        if len(cluster) < 2:
            continue  # singletons are not families

        roots = tuple(r["root"] for r in cluster)
        # Shared concept: join the predicted_features of the representative
        rep_features = cluster[0].get("predicted_features") or []
        shared_concept = " + ".join(rep_features) if rep_features else "unknown"

        # Confidence: mean pairwise overlap within cluster (capped to 3 pairs)
        overlaps: list[float] = []
        for i in range(min(len(cluster), 4)):
            for j in range(i + 1, min(len(cluster), 4)):
                overlaps.append(
                    _feature_overlap(
                        cluster[i].get("predicted_features", []),
                        cluster[j].get("predicted_features", []),
                    )
                )
        confidence = round(sum(overlaps) / len(overlaps), 4) if overlaps else 0.0

        families.append({
            "family_id": f"ext-{uuid.uuid4().hex[:8]}",
            "roots": list(roots),
            "shared_concept": shared_concept,
            "confidence": confidence,
            "source": "extracted",
        })

    return families


# ---------------------------------------------------------------------------
# Merge extracted families with manual seeds
# ---------------------------------------------------------------------------

def merge_with_seeds(
    extracted: list[dict[str, Any]],
    seeds: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Combine automatic extraction results with manual seed families.

    Seed families take precedence; extracted families that overlap an
    existing seed (any root in common) are tagged as ``merged`` and
    de-duplicated.

    Args:
        extracted: Output from :func:`extract_families_from_predictions`.
        seeds: Seed family dicts. Defaults to :data:`SEED_FAMILIES` serialised
            to dicts.

    Returns:
        Combined list with seeds first, then non-overlapping extracted families.
    """
    if seeds is None:
        seeds = [_family_to_dict(f) for f in SEED_FAMILIES]

    # Build a set of all roots already covered by seeds
    seed_roots: set[str] = set()
    for fam in seeds:
        seed_roots.update(fam.get("roots", []))

    merged: list[dict[str, Any]] = list(seeds)

    for ext_fam in extracted:
        ext_roots = set(ext_fam.get("roots", []))
        overlap = ext_roots & seed_roots
        if overlap:
            # Skip — already represented in a seed family
            continue
        merged.append({**ext_fam, "source": "extracted"})

    return merged


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _family_to_dict(family: SynonymFamily) -> dict[str, Any]:
    return {
        "family_id": family.family_id,
        "roots": list(family.roots),
        "shared_concept": family.shared_concept,
        "confidence": family.confidence,
        "source": family.source,
    }


def save_families(families: list[dict[str, Any]], path: str) -> None:
    """Write families to a JSONL file (one JSON object per line).

    Args:
        families: List of family dicts.
        path: Destination file path (created with parent dirs as needed).
    """
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as fh:
        for fam in families:
            fh.write(json.dumps(fam, ensure_ascii=False) + "\n")


def load_families(path: str) -> list[dict[str, Any]]:
    """Read families from a JSONL file.

    Args:
        path: Source file path.

    Returns:
        List of family dicts.
    """
    src = Path(path)
    families: list[dict[str, Any]] = []
    with src.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                families.append(json.loads(line))
    return families


# ---------------------------------------------------------------------------
# Convenience: serialise default seeds to JSONL
# ---------------------------------------------------------------------------

def save_seed_families(path: str) -> None:
    """Write the built-in :data:`SEED_FAMILIES` constant to *path*."""
    save_families([_family_to_dict(f) for f in SEED_FAMILIES], path)
