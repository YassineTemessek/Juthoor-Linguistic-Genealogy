from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canon_loaders import (
    load_binary_field_registry,
    load_letter_registry,
    load_root_composition_registry,
)
from .canon_models import BinaryFieldEntry, LetterSemanticEntry, RootCompositionEntry


_ARABIC_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670\u0640]")
_AR_ROOT_NORM_MAP = str.maketrans(
    {
        "\u0623": "\u0627",
        "\u0625": "\u0627",
        "\u0622": "\u0627",
        "\u0671": "\u0627",
        "\u0649": "\u064a",
        "\u0624": "\u0648",
        "\u0626": "\u064a",
        "\u0629": "\u0647",
    }
)


def normalize_root(root: str) -> str:
    root = (root or "").strip()
    root = _ARABIC_DIACRITICS.sub("", root)
    return root.translate(_AR_ROOT_NORM_MAP)


@dataclass(frozen=True)
class CanonRegistries:
    letters: dict[str, LetterSemanticEntry]
    binary_fields: dict[str, BinaryFieldEntry]
    root_composition: dict[str, RootCompositionEntry]
    theory_claims: list[dict[str, Any]] | None = None
    quranic_profiles: dict[str, Any] | None = None

    @classmethod
    def from_defaults(cls) -> "CanonRegistries":
        return cls(
            letters=load_letter_registry(),
            binary_fields=load_binary_field_registry(),
            root_composition=load_root_composition_registry(),
        )


@dataclass(frozen=True)
class RootAnalysis:
    root: str
    classification: str
    conceptual_meaning: str | None
    binary_field_meaning: str | None
    lexical_realization: str | None
    letter_trace: tuple[dict[str, Any], ...]
    position_profile: dict[str, Any] | None
    composition_trace: tuple[str, ...]
    evidence: dict[str, Any]
    missing_layers: tuple[str, ...]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _promoted_dir() -> Path:
    return _repo_root() / "outputs" / "research_factory" / "promoted" / "promoted_features"


def _reports_dir() -> Path:
    return _repo_root() / "outputs" / "research_factory" / "reports"


def _load_promoted_evidence() -> dict[str, Any]:
    promoted = _promoted_dir()
    reports = _reports_dir()
    metathesis = _load_jsonl(promoted / "metathesis_pairs.jsonl")
    positional = {
        row["letter"]: row
        for row in _load_jsonl(promoted / "positional_profiles.jsonl")
        if row.get("letter")
    }
    return {
        "metathesis_pairs": metathesis,
        "positional_profiles": positional,
        "h10": _load_json(reports / "3.2_result.json"),
        "h9": _load_json(reports / "5.2_result.json"),
    }


def _build_letter_trace(root: str, letters: dict[str, LetterSemanticEntry]) -> tuple[dict[str, Any], ...]:
    trace: list[dict[str, Any]] = []
    for index, glyph in enumerate(root, start=1):
        entry = letters.get(glyph)
        trace.append(
            {
                "letter": glyph,
                "position": index,
                "semantic_gloss": entry.canonical_semantic_gloss if entry else None,
                "kinetic_gloss": entry.canonical_kinetic_gloss if entry else None,
                "status": entry.status if entry else "missing",
            }
        )
    return tuple(trace)


def process_root(root: str, registries: CanonRegistries) -> RootAnalysis:
    normalized = normalize_root(root)
    entry = registries.root_composition.get(normalized)
    if entry is None:
        return RootAnalysis(
            root=normalized,
            classification="underdescribed",
            conceptual_meaning=None,
            binary_field_meaning=None,
            lexical_realization=None,
            letter_trace=tuple(),
            position_profile=None,
            composition_trace=tuple(),
            evidence={},
            missing_layers=("root", "binary_field", "letters"),
        )

    binary_entry = registries.binary_fields.get(entry.binary_root)
    promoted = _load_promoted_evidence()
    third_letter_profile = promoted["positional_profiles"].get(entry.third_letter)

    letter_trace = _build_letter_trace(normalized, registries.letters)
    conceptual = entry.conceptual_root_meaning
    binary_meaning = entry.binary_field_meaning or (binary_entry.field_gloss if binary_entry else None)
    lexical = entry.axial_meaning

    composition_trace = tuple(
        item
        for item in (
            f"binary:{entry.binary_root}" if entry.binary_root else None,
            f"third_letter:{entry.third_letter}" if entry.third_letter else None,
            "position:promoted" if third_letter_profile else None,
            "composition:partial_signal" if promoted["h10"].get("metrics", {}).get("supports_compositional_signal") else None,
        )
        if item
    )

    evidence = {
        "field_coherence": binary_entry.coherence_score if binary_entry else None,
        "metathesis_pairs": [
            row
            for row in promoted["metathesis_pairs"]
            if row.get("binary_root_a") == entry.binary_root or row.get("binary_root_b") == entry.binary_root
        ],
        "position_profile": third_letter_profile,
        "h10_partial_compositionality": promoted["h10"].get("metrics", {}),
        "h9_negative_evidence": promoted["h9"].get("metrics", {}),
    }

    missing_layers: list[str] = []
    if conceptual is None:
        missing_layers.append("conceptual_meaning")
    if binary_meaning is None:
        missing_layers.append("binary_field_meaning")
    if all(item["semantic_gloss"] is None for item in letter_trace):
        missing_layers.append("letter_trace")
    if third_letter_profile is None:
        missing_layers.append("position_profile")

    if lexical and binary_meaning and not missing_layers:
        classification = "resolved"
    elif conceptual or binary_meaning or lexical:
        classification = "partially_resolved"
    else:
        classification = "underdescribed"

    if binary_entry and binary_entry.status == "rejected":
        classification = "conflicted"

    return RootAnalysis(
        root=normalized,
        classification=classification,
        conceptual_meaning=conceptual,
        binary_field_meaning=binary_meaning,
        lexical_realization=lexical,
        letter_trace=letter_trace,
        position_profile=third_letter_profile or entry.position_profile,
        composition_trace=composition_trace,
        evidence=evidence,
        missing_layers=tuple(missing_layers),
    )
