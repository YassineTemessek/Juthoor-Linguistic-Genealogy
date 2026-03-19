from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .canon_models import (
    BinaryFieldEntry,
    LetterSemanticEntry,
    QuranicSemanticProfile,
    RootCompositionEntry,
    SourceEntry,
    TheoryClaim,
)


def _lv1_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _canon_root() -> Path:
    return _lv1_root() / "data" / "theory_canon"


def _registries_dir() -> Path:
    return _canon_root() / "registries"


def _resolve_registry_path(path: Path | None, filename: str) -> Path:
    if path is None:
        return _registries_dir() / filename
    if path.is_dir():
        return path / filename
    return path


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Malformed JSONL in {path} line {idx}: {exc}") from exc
    return rows


def _to_sources(rows: Iterable[dict[str, Any]]) -> tuple[SourceEntry, ...]:
    return tuple(SourceEntry(**row) for row in rows)


def load_letter_registry(path: Path | None = None) -> dict[str, LetterSemanticEntry]:
    records = _read_jsonl(_resolve_registry_path(path, "letters.jsonl"))
    out: dict[str, LetterSemanticEntry] = {}
    for row in records:
        entry = LetterSemanticEntry(
            letter=row["letter"],
            letter_name=row["letter_name"],
            canonical_semantic_gloss=row.get("canonical_semantic_gloss"),
            canonical_kinetic_gloss=row.get("canonical_kinetic_gloss"),
            canonical_sensory_gloss=row.get("canonical_sensory_gloss"),
            articulatory_features=row.get("articulatory_features"),
            sources=_to_sources(row.get("sources", [])),
            agreement_level=row["agreement_level"],
            confidence_tier=row["confidence_tier"],
            status=row["status"],
        )
        if entry.letter in out:
            raise ValueError(f"Duplicate letter registry key: {entry.letter}")
        out[entry.letter] = entry
    return out


def load_binary_field_registry(path: Path | None = None) -> dict[str, BinaryFieldEntry]:
    records = _read_jsonl(_resolve_registry_path(path, "binary_fields.jsonl"))
    out: dict[str, BinaryFieldEntry] = {}
    for row in records:
        entry = BinaryFieldEntry(
            binary_root=row["binary_root"],
            field_gloss=row.get("field_gloss"),
            field_gloss_source=row.get("field_gloss_source"),
            letter1=row["letter1"],
            letter2=row["letter2"],
            letter1_gloss=row.get("letter1_gloss"),
            letter2_gloss=row.get("letter2_gloss"),
            member_roots=tuple(row.get("member_roots", [])),
            member_count=int(row.get("member_count", 0)),
            coherence_score=row.get("coherence_score"),
            cross_lingual_support=row.get("cross_lingual_support"),
            status=row["status"],
        )
        if entry.binary_root in out:
            raise ValueError(f"Duplicate binary field key: {entry.binary_root}")
        out[entry.binary_root] = entry
    return out


def load_root_composition_registry(path: Path | None = None) -> dict[str, RootCompositionEntry]:
    records = _read_jsonl(_resolve_registry_path(path, "root_composition.jsonl"))
    out: dict[str, RootCompositionEntry] = {}
    for row in records:
        entry = RootCompositionEntry(
            root=row["root"],
            binary_root=row["binary_root"],
            third_letter=row["third_letter"],
            conceptual_root_meaning=row.get("conceptual_root_meaning"),
            binary_field_meaning=row.get("binary_field_meaning"),
            axial_meaning=row.get("axial_meaning"),
            letter_trace=tuple(row["letter_trace"]) if row.get("letter_trace") is not None else None,
            position_profile=row.get("position_profile"),
            modifier_profile=row.get("modifier_profile"),
            compositional_signal=row.get("compositional_signal"),
            agreement_with_observed_gloss=row.get("agreement_with_observed_gloss"),
            status=row["status"],
            semantic_score=row.get("semantic_score"),
        )
        if entry.root in out:
            raise ValueError(f"Duplicate root composition key: {entry.root}")
        out[entry.root] = entry
    return out


def load_theory_claims(path: Path | None = None) -> list[TheoryClaim]:
    records = _read_jsonl(_resolve_registry_path(path, "theory_claims.jsonl"))
    return [
        TheoryClaim(
            claim_id=row["claim_id"],
            theme=row["theme"],
            scholar=row["scholar"],
            statement=row["statement"],
            scope=row["scope"],
            evidence_type=row["evidence_type"],
            source_doc=row["source_doc"],
            source_locator=row.get("source_locator"),
            status=row["status"],
        )
        for row in records
    ]


def load_quranic_profiles(path: Path | None = None) -> dict[str, QuranicSemanticProfile]:
    records = _read_jsonl(_resolve_registry_path(path, "quranic_profiles.jsonl"))
    out: dict[str, QuranicSemanticProfile] = {}
    for row in records:
        entry = QuranicSemanticProfile(
            lemma=row["lemma"],
            root=row["root"],
            conceptual_meaning=row.get("conceptual_meaning"),
            binary_field_meaning=row.get("binary_field_meaning"),
            lexical_realization=row.get("lexical_realization"),
            letter_trace=tuple(row["letter_trace"]) if row.get("letter_trace") is not None else None,
            contextual_constraints=tuple(row["contextual_constraints"]) if row.get("contextual_constraints") is not None else None,
            contrast_lemmas=tuple(row["contrast_lemmas"]) if row.get("contrast_lemmas") is not None else None,
            interpretive_notes=row.get("interpretive_notes"),
            confidence=row["confidence"],
            status=row["status"],
        )
        if entry.lemma in out:
            raise ValueError(f"Duplicate Quranic profile key: {entry.lemma}")
        out[entry.lemma] = entry
    return out
