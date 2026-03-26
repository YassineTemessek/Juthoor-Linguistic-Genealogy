"""Import curated theory-canon records from inbox files into registry JSONL data.

The module normalizes Arabic keys, validates imported rows, and writes the
canonical letter, binary-field, root-composition, theory, and Quranic datasets.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable

from .canon_loaders import (
    load_binary_field_registry,
    load_letter_registry,
    load_quranic_profiles,
    load_root_composition_registry,
    load_theory_claims,
)
from .canon_models import (
    BinaryFieldEntry,
    LetterSemanticEntry,
    QuranicSemanticProfile,
    RootCompositionEntry,
    SourceEntry,
    TheoryClaim,
)


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

_INBOX_TO_FILENAME = {
    "letters": "letters.jsonl",
    "binary_fields": "binary_fields.jsonl",
    "root_composition": "root_composition.jsonl",
    "theory_claims": "theory_claims.jsonl",
    "quranic": "quranic_profiles.jsonl",
}


def _lv1_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _canon_root() -> Path:
    return _lv1_root() / "data" / "theory_canon"


def _normalize_arabic_text(value: str) -> str:
    value = (value or "").strip()
    value = _ARABIC_DIACRITICS.sub("", value)
    return value.translate(_AR_ROOT_NORM_MAP)


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return _serialize(asdict(value))
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_serialize(item) for item in value]
    return value


def _write_jsonl(path: Path, rows: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(_serialize(row), ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Malformed JSON in {path} line {line_no}: {exc}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"Expected object in {path} line {line_no}")
            rows.append(payload)
    return rows


def _build_sources(rows: list[dict[str, Any]]) -> tuple[SourceEntry, ...]:
    return tuple(SourceEntry(**row) for row in rows)


def _require_fields(payload: dict[str, Any], required: tuple[str, ...]) -> None:
    missing = [field for field in required if payload.get(field) in (None, "")]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")


def validate_letter_import(payload: dict[str, Any]) -> LetterSemanticEntry:
    _require_fields(payload, ("letter", "letter_name", "agreement_level", "confidence_tier", "status"))
    payload = dict(payload)
    payload["letter"] = _normalize_arabic_text(payload["letter"])
    return LetterSemanticEntry(
        letter=payload["letter"],
        letter_name=str(payload["letter_name"]).strip(),
        canonical_semantic_gloss=payload.get("canonical_semantic_gloss"),
        canonical_kinetic_gloss=payload.get("canonical_kinetic_gloss"),
        canonical_sensory_gloss=payload.get("canonical_sensory_gloss"),
        articulatory_features=payload.get("articulatory_features"),
        sources=_build_sources(payload.get("sources", [])),
        agreement_level=payload["agreement_level"],
        confidence_tier=payload["confidence_tier"],
        status=payload["status"],
    )


def validate_binary_field_import(payload: dict[str, Any]) -> BinaryFieldEntry:
    _require_fields(payload, ("binary_root", "letter1", "letter2", "status"))
    payload = dict(payload)
    payload["binary_root"] = _normalize_arabic_text(payload["binary_root"])
    payload["letter1"] = _normalize_arabic_text(payload["letter1"])
    payload["letter2"] = _normalize_arabic_text(payload["letter2"])
    return BinaryFieldEntry(
        binary_root=payload["binary_root"],
        field_gloss=payload.get("field_gloss"),
        field_gloss_source=payload.get("field_gloss_source"),
        letter1=payload["letter1"],
        letter2=payload["letter2"],
        letter1_gloss=payload.get("letter1_gloss"),
        letter2_gloss=payload.get("letter2_gloss"),
        member_roots=tuple(_normalize_arabic_text(item) for item in payload.get("member_roots", [])),
        member_count=int(payload.get("member_count", len(payload.get("member_roots", [])))),
        coherence_score=payload.get("coherence_score"),
        cross_lingual_support=payload.get("cross_lingual_support"),
        status=payload["status"],
    )


def validate_root_composition_import(payload: dict[str, Any]) -> RootCompositionEntry:
    _require_fields(payload, ("root", "binary_root", "third_letter", "status"))
    payload = dict(payload)
    payload["root"] = _normalize_arabic_text(payload["root"])
    payload["binary_root"] = _normalize_arabic_text(payload["binary_root"])
    payload["third_letter"] = _normalize_arabic_text(payload["third_letter"])
    trace = payload.get("letter_trace")
    return RootCompositionEntry(
        root=payload["root"],
        binary_root=payload["binary_root"],
        third_letter=payload["third_letter"],
        conceptual_root_meaning=payload.get("conceptual_root_meaning"),
        binary_field_meaning=payload.get("binary_field_meaning"),
        axial_meaning=payload.get("axial_meaning"),
        letter_trace=tuple(trace) if trace is not None else None,
        position_profile=payload.get("position_profile"),
        modifier_profile=payload.get("modifier_profile"),
        compositional_signal=payload.get("compositional_signal"),
        agreement_with_observed_gloss=payload.get("agreement_with_observed_gloss"),
        status=payload["status"],
        semantic_score=payload.get("semantic_score"),
    )


def validate_theory_claim_import(payload: dict[str, Any]) -> TheoryClaim:
    _require_fields(
        payload,
        ("claim_id", "theme", "scholar", "statement", "scope", "evidence_type", "source_doc", "status"),
    )
    return TheoryClaim(
        claim_id=str(payload["claim_id"]).strip(),
        theme=str(payload["theme"]).strip(),
        scholar=str(payload["scholar"]).strip(),
        statement=str(payload["statement"]).strip(),
        scope=str(payload["scope"]).strip(),
        evidence_type=str(payload["evidence_type"]).strip(),
        source_doc=str(payload["source_doc"]).strip(),
        source_locator=payload.get("source_locator"),
        status=payload["status"],
    )


def validate_quranic_import(payload: dict[str, Any]) -> QuranicSemanticProfile:
    _require_fields(payload, ("lemma", "root", "confidence", "status"))
    payload = dict(payload)
    payload["root"] = _normalize_arabic_text(payload["root"])
    trace = payload.get("letter_trace")
    constraints = payload.get("contextual_constraints")
    contrast = payload.get("contrast_lemmas")
    return QuranicSemanticProfile(
        lemma=str(payload["lemma"]).strip(),
        root=payload["root"],
        conceptual_meaning=payload.get("conceptual_meaning"),
        binary_field_meaning=payload.get("binary_field_meaning"),
        lexical_realization=payload.get("lexical_realization"),
        letter_trace=tuple(trace) if trace is not None else None,
        contextual_constraints=tuple(constraints) if constraints is not None else None,
        contrast_lemmas=tuple(contrast) if contrast is not None else None,
        interpretive_notes=payload.get("interpretive_notes"),
        confidence=payload["confidence"],
        status=payload["status"],
    )


def _merge_sources(current: tuple[SourceEntry, ...], incoming: tuple[SourceEntry, ...]) -> tuple[SourceEntry, ...]:
    seen = {item.source_id for item in current}
    merged = list(current)
    for item in incoming:
        if item.source_id not in seen:
            merged.append(item)
            seen.add(item.source_id)
    return tuple(merged)


def _status_rank(status: str) -> int:
    order = {"empty": 0, "draft": 1, "curated": 2, "tested": 3, "promoted": 4, "rejected": 5}
    return order.get(status, -1)


def _can_overwrite(current_status: str, incoming_status: str, force: bool) -> bool:
    if current_status == "promoted":
        return False
    if current_status in {"curated", "tested"}:
        return force
    if current_status == "empty":
        return incoming_status in {"draft", "curated", "tested", "promoted"}
    if current_status == "draft":
        return incoming_status in {"curated", "tested", "promoted"} or force
    return force


def _merge_non_null(current: dict[str, Any], incoming: dict[str, Any], preserve: set[str]) -> dict[str, Any]:
    merged = dict(current)
    for key, value in incoming.items():
        if key in preserve:
            continue
        if value is not None:
            merged[key] = value
    return merged


def _merge_letter(current: LetterSemanticEntry, incoming: LetterSemanticEntry, force: bool) -> LetterSemanticEntry:
    if current.status == "promoted" and not force:
        return validate_letter_import(
            {
                **_serialize(current),
                "sources": _serialize(_merge_sources(current.sources, incoming.sources)),
            }
        )
    current_dict = _serialize(current)
    incoming_dict = _serialize(incoming)
    merged = _merge_non_null(current_dict, incoming_dict, preserve={"letter", "sources"})
    merged["sources"] = _serialize(_merge_sources(current.sources, incoming.sources))
    merged["status"] = incoming.status if _can_overwrite(current.status, incoming.status, force) else current.status
    if _status_rank(incoming.status) > _status_rank(current.status) and _can_overwrite(current.status, incoming.status, force):
        merged["agreement_level"] = incoming.agreement_level
        merged["confidence_tier"] = incoming.confidence_tier
    return validate_letter_import(merged)


def _merge_binary(current: BinaryFieldEntry, incoming: BinaryFieldEntry, force: bool) -> BinaryFieldEntry:
    if current.status == "promoted" and not force:
        return current
    current_dict = _serialize(current)
    incoming_dict = _serialize(incoming)
    merged = _merge_non_null(current_dict, incoming_dict, preserve={"binary_root"})
    merged["member_roots"] = list(dict.fromkeys([*current.member_roots, *incoming.member_roots]))
    merged["member_count"] = max(current.member_count, incoming.member_count, len(merged["member_roots"]))
    merged["status"] = incoming.status if _can_overwrite(current.status, incoming.status, force) else current.status
    return validate_binary_field_import(merged)


def _merge_root(current: RootCompositionEntry, incoming: RootCompositionEntry, force: bool) -> RootCompositionEntry:
    if current.status == "promoted" and not force:
        return current
    current_dict = _serialize(current)
    incoming_dict = _serialize(incoming)
    merged = _merge_non_null(current_dict, incoming_dict, preserve={"root"})
    merged["status"] = incoming.status if _can_overwrite(current.status, incoming.status, force) else current.status
    return validate_root_composition_import(merged)


def _merge_claim(current: TheoryClaim, incoming: TheoryClaim, force: bool) -> TheoryClaim:
    if current.status == "promoted" and not force:
        return current
    merged = _serialize(current)
    incoming_dict = _serialize(incoming)
    merged.update({key: value for key, value in incoming_dict.items() if value is not None})
    if current.status in {"curated", "tested"} and not force:
        merged["status"] = current.status
    return validate_theory_claim_import(merged)


def _merge_quranic(current: QuranicSemanticProfile, incoming: QuranicSemanticProfile, force: bool) -> QuranicSemanticProfile:
    if current.status == "promoted" and not force:
        return current
    current_dict = _serialize(current)
    incoming_dict = _serialize(incoming)
    merged = _merge_non_null(current_dict, incoming_dict, preserve={"lemma"})
    if current.letter_trace or incoming.letter_trace:
        merged["letter_trace"] = incoming_dict.get("letter_trace") or current_dict.get("letter_trace")
    if current.contextual_constraints or incoming.contextual_constraints:
        merged["contextual_constraints"] = list(
            dict.fromkeys([*(current.contextual_constraints or ()), *(incoming.contextual_constraints or ())])
        )
    if current.contrast_lemmas or incoming.contrast_lemmas:
        merged["contrast_lemmas"] = list(dict.fromkeys([*(current.contrast_lemmas or ()), *(incoming.contrast_lemmas or ())]))
    merged["status"] = incoming.status if _can_overwrite(current.status, incoming.status, force) else current.status
    return validate_quranic_import(merged)


def _load_registry(registry_name: str, registry_root: Path) -> dict[str, Any] | list[Any]:
    if registry_name == "letters":
        return load_letter_registry(registry_root)
    if registry_name == "binary_fields":
        return load_binary_field_registry(registry_root)
    if registry_name == "root_composition":
        return load_root_composition_registry(registry_root)
    if registry_name == "theory_claims":
        return load_theory_claims(registry_root)
    if registry_name == "quranic":
        return load_quranic_profiles(registry_root)
    raise ValueError(f"Unknown registry name: {registry_name}")


def _save_registry(registry_name: str, registry: dict[str, Any] | list[Any], registry_root: Path) -> None:
    filename = _INBOX_TO_FILENAME[registry_name]
    path = registry_root / filename
    if isinstance(registry, dict):
        rows = list(registry.values())
    else:
        rows = registry
    if registry_name == "theory_claims":
        rows = sorted(rows, key=lambda item: item.claim_id)
    elif registry_name == "letters":
        rows = sorted(rows, key=lambda item: item.letter)
    elif registry_name == "binary_fields":
        rows = sorted(rows, key=lambda item: item.binary_root)
    elif registry_name == "root_composition":
        rows = sorted(rows, key=lambda item: item.root)
    elif registry_name == "quranic":
        rows = sorted(rows, key=lambda item: item.lemma)
    _write_jsonl(path, rows)


def _registry_key(entry: Any) -> str:
    if isinstance(entry, LetterSemanticEntry):
        return entry.letter
    if isinstance(entry, BinaryFieldEntry):
        return entry.binary_root
    if isinstance(entry, RootCompositionEntry):
        return entry.root
    if isinstance(entry, TheoryClaim):
        return entry.claim_id
    if isinstance(entry, QuranicSemanticProfile):
        return entry.lemma
    raise TypeError(f"Unsupported entry type: {type(entry)!r}")


def _validator(registry_name: str) -> Callable[[dict[str, Any]], Any]:
    return {
        "letters": validate_letter_import,
        "binary_fields": validate_binary_field_import,
        "root_composition": validate_root_composition_import,
        "theory_claims": validate_theory_claim_import,
        "quranic": validate_quranic_import,
    }[registry_name]


def _merge_entry(current: Any, incoming: Any, force: bool) -> Any:
    if isinstance(current, LetterSemanticEntry):
        return _merge_letter(current, incoming, force)
    if isinstance(current, BinaryFieldEntry):
        return _merge_binary(current, incoming, force)
    if isinstance(current, RootCompositionEntry):
        return _merge_root(current, incoming, force)
    if isinstance(current, TheoryClaim):
        return _merge_claim(current, incoming, force)
    if isinstance(current, QuranicSemanticProfile):
        return _merge_quranic(current, incoming, force)
    raise TypeError(f"Unsupported entry type: {type(current)!r}")


def ingest_from_inbox(
    inbox_root: Path | None = None,
    registry_root: Path | None = None,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    default_canon_root = _canon_root()
    inbox = inbox_root or default_canon_root / "inbox"
    registries = registry_root or default_canon_root / "registries"
    if inbox_root is not None:
        canon_root = inbox
        if canon_root.name == "inbox":
            canon_root = canon_root.parent
    elif registry_root is not None:
        canon_root = registries
        if canon_root.name == "registries":
            canon_root = canon_root.parent
    else:
        canon_root = default_canon_root
    imported_dir = canon_root / "imported"
    rejected_dir = canon_root / "rejected"
    reports_dir = canon_root / "import_reports"
    report: dict[str, Any] = {
        "added": 0,
        "updated": 0,
        "rejected": 0,
        "processed_files": [],
        "dry_run": dry_run,
        "force": force,
        "conflicts": [],
    }

    for registry_name in _INBOX_TO_FILENAME:
        folder = inbox / registry_name
        if not folder.exists():
            continue
        registry = _load_registry(registry_name, registries)
        validator = _validator(registry_name)
        for source_file in sorted(folder.glob("*.jsonl")):
            file_result = {"file": str(source_file), "registry": registry_name, "added": 0, "updated": 0, "rejected": 0}
            try:
                rows = _read_jsonl(source_file)
                incoming_entries = [validator(row) for row in rows]
                if isinstance(registry, dict):
                    for entry in incoming_entries:
                        key = _registry_key(entry)
                        if key in registry:
                            merged = _merge_entry(registry[key], entry, force)
                            if merged != registry[key]:
                                registry[key] = merged
                                file_result["updated"] += 1
                        else:
                            registry[key] = entry
                            file_result["added"] += 1
                else:
                    existing = {entry.claim_id: entry for entry in registry}
                    for entry in incoming_entries:
                        key = _registry_key(entry)
                        if key in existing:
                            merged = _merge_entry(existing[key], entry, force)
                            if merged != existing[key]:
                                existing[key] = merged
                                file_result["updated"] += 1
                        else:
                            existing[key] = entry
                            file_result["added"] += 1
                    registry = list(existing.values())
                if not dry_run:
                    _save_registry(registry_name, registry, registries)
                    target = imported_dir / registry_name / source_file.name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source_file), str(target))
                report["added"] += file_result["added"]
                report["updated"] += file_result["updated"]
            except Exception as exc:  # noqa: BLE001
                file_result["rejected"] = 1
                file_result["error"] = str(exc)
                report["rejected"] += 1
                if not dry_run:
                    target = rejected_dir / registry_name / source_file.name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source_file), str(target))
            report["processed_files"].append(file_result)

    if not dry_run:
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / "last_import_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        report["report_path"] = str(report_path)
    return report
