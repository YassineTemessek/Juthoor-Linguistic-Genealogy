from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .canon_models import (
    BinaryFieldEntry,
    BinaryNucleus,
    LetterAtom,
    LetterRegistryEntry,
    LetterSemanticEntry,
    QuranicSemanticProfile,
    RootCompositionEntry,
    SourceEntry,
    TheoryClaim,
    TriliteralRootEntry,
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


# ---------------------------------------------------------------------------
# Legacy registry loaders (LetterSemanticEntry / BinaryFieldEntry /
# RootCompositionEntry) — single flat JSONL files in a registries/ dir.
# ---------------------------------------------------------------------------

def load_letter_registry(path: Path | None = None) -> dict[str, LetterSemanticEntry]:
    """Load the flat letter registry (one LetterSemanticEntry per letter).

    Reads a single ``letters.jsonl`` file from the given directory (or the
    default registries/ directory when *path* is None).
    """
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
    """Load theory claims from a JSONL file or directory of JSONL files.

    When *path* is a directory, all ``*.jsonl`` files inside it are read and
    combined. When *path* is a file, that file is read directly. When *path*
    is None the default registries/ directory is used (single-file mode).

    Accepts both ``source_doc`` (dataclass field name) and ``source_document``
    (SCHEMA.md field name) in the JSON rows.
    """
    if path is None:
        rows = _read_jsonl(_resolve_registry_path(None, "theory_claims.jsonl"))
    elif path.is_dir():
        # Legacy registry pattern: directory contains a named theory_claims.jsonl
        legacy_file = path / "theory_claims.jsonl"
        if legacy_file.exists():
            rows = _read_jsonl(legacy_file)
        else:
            # New pattern: directory contains multiple per-theme JSONL files
            rows = _read_all_jsonl_in_dir(path)
    else:
        rows = _read_jsonl(path)

    claims: list[TheoryClaim] = []
    for row in rows:
        source_doc = row.get("source_doc") or row.get("source_document", "")
        claims.append(
            TheoryClaim(
                claim_id=row["claim_id"],
                theme=row["theme"],
                scholar=row["scholar"],
                statement=row["statement"],
                scope=row["scope"],
                evidence_type=row["evidence_type"],
                source_doc=source_doc,
                source_locator=row.get("source_locator"),
                status=row["status"],
            )
        )
    return claims


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


# ---------------------------------------------------------------------------
# Phase 1 canon loaders — multi-scholar JSONL directories.
# These use the LetterAtom / LetterRegistryEntry / BinaryNucleus /
# TriliteralRootEntry dataclasses introduced in canon_models.py.
# ---------------------------------------------------------------------------

_CANON_DIR = _lv1_root() / "data" / "theory_canon"


def _read_all_jsonl_in_dir(directory: Path) -> list[dict[str, Any]]:
    """Read all *.jsonl files in *directory* and return combined rows.

    Returns an empty list if the directory does not exist or contains no
    JSONL files.
    """
    if not directory.exists() or not directory.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for jsonl_file in sorted(directory.glob("*.jsonl")):
        file_rows = _read_jsonl(jsonl_file)
        rows.extend(file_rows)
    return rows


def load_letter_atoms(letters_dir: Path | None = None) -> list[LetterAtom]:
    """Load all scholar letter entries from JSONL files in the letters/ directory.

    Reads all ``*.jsonl`` files in *letters_dir*. Each line becomes one
    :class:`LetterAtom`. Returns an empty list if the directory does not
    exist or is empty.
    """
    directory = letters_dir if letters_dir is not None else _CANON_DIR / "letters"
    rows = _read_all_jsonl_in_dir(directory)
    atoms: list[LetterAtom] = []
    for row in rows:
        atoms.append(
            LetterAtom(
                letter=row["letter"],
                letter_name=row["letter_name"],
                scholar=row["scholar"],
                raw_description=row["raw_description"],
                atomic_features=tuple(row.get("atomic_features") or []),
                feature_categories=tuple(row.get("feature_categories") or []),
                sensory_category=row.get("sensory_category"),
                kinetic_gloss=row.get("kinetic_gloss"),
                source_document=row["source_document"],
                confidence=row["confidence"],
            )
        )
    return atoms


def _compute_agreement_level(scholar_count: int, consensus_feature_count: int) -> str:
    """Derive an agreement_level string from scholar coverage.

    Rules:
      - ``consensus``:   3+ scholars agree on at least one feature
      - ``majority``:    exactly 2 scholars agree on at least one feature
      - ``contested``:   2+ scholars present but no shared feature
      - ``unknown``:     0 or 1 scholar (insufficient data)
    """
    if scholar_count <= 1:
        return "unknown"
    if consensus_feature_count >= 1 and scholar_count >= 3:
        return "consensus"
    if consensus_feature_count >= 1:
        return "majority"
    return "contested"


def load_letter_atom_registry(letters_dir: Path | None = None) -> dict[str, LetterRegistryEntry]:
    """Load letter atoms and merge into unified registry entries, one per letter.

    Returns a dict keyed by letter (e.g. ``"ب"`` -> :class:`LetterRegistryEntry`).
    Computes ``consensus_features`` (features where 2+ scholars agree) and
    ``agreement_level`` based on inter-scholar consensus.
    Returns an empty dict if the directory does not exist or is empty.
    """
    atoms = load_letter_atoms(letters_dir)
    if not atoms:
        return {}

    # Group atoms by letter
    groups: dict[str, list[LetterAtom]] = {}
    for atom in atoms:
        groups.setdefault(atom.letter, []).append(atom)

    registry: dict[str, LetterRegistryEntry] = {}
    for letter, letter_atoms in groups.items():
        # Count how many scholars mention each feature (once per scholar per feature)
        feature_counter: Counter[str] = Counter()
        for atom in letter_atoms:
            for feature in set(atom.atomic_features):
                feature_counter[feature] += 1

        # Consensus = features mentioned by 2+ scholars
        consensus_features = tuple(
            feature for feature, count in feature_counter.items() if count >= 2
        )

        agreement_level = _compute_agreement_level(
            scholar_count=len(letter_atoms),
            consensus_feature_count=len(consensus_features),
        )

        letter_name = letter_atoms[0].letter_name

        registry[letter] = LetterRegistryEntry(
            letter=letter,
            letter_name=letter_name,
            scholar_entries=tuple(letter_atoms),
            consensus_features=consensus_features,
            agreement_level=agreement_level,
            articulatory_features=None,
        )

    return registry


def load_binary_nuclei(binary_dir: Path | None = None) -> dict[str, BinaryNucleus]:
    """Load binary nucleus entries from JSONL files in *binary_dir*.

    Returns a dict keyed by ``binary_root`` (e.g. ``"حس"`` ->
    :class:`BinaryNucleus`). Returns an empty dict if the directory does not
    exist or is empty.
    """
    directory = binary_dir if binary_dir is not None else _CANON_DIR / "binary_fields"
    rows = _read_all_jsonl_in_dir(directory)
    out: dict[str, BinaryNucleus] = {}
    for row in rows:
        nucleus = BinaryNucleus(
            binary_root=row["binary_root"],
            letter1=row["letter1"],
            letter2=row["letter2"],
            jabal_shared_meaning=row["jabal_shared_meaning"],
            jabal_features=tuple(row.get("jabal_features") or []),
            member_roots=tuple(row.get("member_roots") or []),
            member_count=int(row.get("member_count", 0)),
            reverse_exists=bool(row.get("reverse_exists", False)),
            reverse_root=row.get("reverse_root"),
            model_a_score=row.get("model_a_score"),
            model_b_score=row.get("model_b_score"),
            model_c_score=row.get("model_c_score"),
            model_d_score=row.get("model_d_score"),
            best_model=row.get("best_model"),
            golden_rule_score=row.get("golden_rule_score"),
            status=row.get("status", "empty"),
        )
        out[nucleus.binary_root] = nucleus
    return out


def load_trilateral_roots(roots_dir: Path | None = None) -> dict[str, TriliteralRootEntry]:
    """Load trilateral root entries from JSONL files in *roots_dir*.

    Returns a dict keyed by ``root`` (e.g. ``"كتب"`` ->
    :class:`TriliteralRootEntry`). Returns an empty dict if the directory does
    not exist or is empty.

    Accepts both ``binary_nucleus`` and ``binary_root`` as the nucleus field
    name to cover both the task schema and the SCHEMA.md schema.
    """
    directory = roots_dir if roots_dir is not None else _CANON_DIR / "roots"
    rows = _read_all_jsonl_in_dir(directory)
    out: dict[str, TriliteralRootEntry] = {}
    for row in rows:
        binary_nucleus = row.get("binary_nucleus") or row.get("binary_root", "")
        entry = TriliteralRootEntry(
            root=row["root"],
            binary_nucleus=binary_nucleus,
            third_letter=row["third_letter"],
            jabal_axial_meaning=row["jabal_axial_meaning"],
            jabal_features=tuple(row.get("jabal_features") or []),
            predicted_meaning=row.get("predicted_meaning"),
            predicted_features=tuple(row["predicted_features"]) if row.get("predicted_features") is not None else None,
            prediction_score=row.get("prediction_score"),
            quranic_verse=row.get("quranic_verse"),
            bab=row.get("bab", ""),
            status=row.get("status", "empty"),
        )
        out[entry.root] = entry
    return out
