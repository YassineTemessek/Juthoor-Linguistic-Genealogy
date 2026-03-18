from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .phonetic_mergers import ambiguous_target_chars, has_merger_ambiguity, merger_overlap

_SAFE_NEGATIVE_NOTE_TOKENS = (
    "modern coinage",
    "modern coinages",
    "borrowed directly",
    "borrowed from",
    "technology terms",
    "independently derived",
)


@dataclass(frozen=True)
class BenchmarkAuditFinding:
    source_lang: str
    source_lemma: str
    target_lang: str
    target_lemma: str
    relation: str
    severity: str
    finding: str
    overlap_letters: tuple[str, ...]
    notes: str = ""


def _norm(value: Any) -> str:
    return " ".join(str(value or "").split()).strip().casefold()


def _norm_lang(code: str) -> str:
    aliases = {"fa": "fas", "fas": "fas", "he": "heb", "heb": "heb", "arc": "arc", "ara": "ara", "ar": "ara"}
    return aliases.get(_norm(code), _norm(code))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def audit_benchmark_rows(rows: list[dict[str, Any]]) -> list[BenchmarkAuditFinding]:
    findings: list[BenchmarkAuditFinding] = []
    semitic_targets = {"heb", "arc", "fas"}
    risky_negative_relations = {"negative_translation", "false_friend"}
    for row in rows:
        source = row.get("source", {})
        target = row.get("target", {})
        source_lang = _norm_lang(source.get("lang"))
        target_lang = _norm_lang(target.get("lang"))
        relation = str(row.get("relation", "unknown"))
        notes = str(row.get("notes", ""))
        if source_lang != "ara" or target_lang not in semitic_targets:
            continue
        ambiguous_chars = ambiguous_target_chars(target_lang)
        target_lemma = str(target.get("lemma", ""))
        uses_ambiguous_char = any(char in ambiguous_chars for char in target_lemma)
        overlap = tuple(sorted(merger_overlap(source_lang, source.get("lemma", ""), target_lang, target.get("lemma", ""))))
        note_marks_safe_negative = any(token in notes.casefold() for token in _SAFE_NEGATIVE_NOTE_TOKENS)
        if relation in risky_negative_relations and overlap:
            if note_marks_safe_negative:
                continue
            findings.append(
                BenchmarkAuditFinding(
                    source_lang=source_lang,
                    source_lemma=str(source.get("lemma", "")),
                    target_lang=target_lang,
                    target_lemma=str(target.get("lemma", "")),
                    relation=relation,
                    severity="review",
                    finding="negative_or_false_friend_has_merger_overlap",
                    overlap_letters=overlap,
                    notes=notes,
                )
            )
        if relation == "cognate" and uses_ambiguous_char and has_merger_ambiguity(source_lang, source.get("lemma", ""), target_lang, target_lemma):
            findings.append(
                BenchmarkAuditFinding(
                    source_lang=source_lang,
                    source_lemma=str(source.get("lemma", "")),
                    target_lang=target_lang,
                    target_lemma=str(target.get("lemma", "")),
                    relation=relation,
                    severity="info",
                    finding="cognate_uses_merger_sensitive_mapping",
                    overlap_letters=overlap,
                    notes=notes,
                )
            )
        if relation in risky_negative_relations and not overlap and target_lang == "fas":
            if any(token in notes.casefold() for token in ("avestan", "old persian", "root connection", "hvar", "حور")):
                findings.append(
                    BenchmarkAuditFinding(
                        source_lang=source_lang,
                        source_lemma=str(source.get("lemma", "")),
                        target_lang=target_lang,
                        target_lemma=str(target.get("lemma", "")),
                        relation=relation,
                        severity="review",
                        finding="negative_notes_already_admit_deeper_root_connection",
                        overlap_letters=overlap,
                        notes=notes,
                    )
                )
    return findings


def audit_benchmark_files(paths: list[Path]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.extend(_read_jsonl(path))
    findings = audit_benchmark_rows(rows)
    by_finding: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for item in findings:
        by_finding[item.finding] = by_finding.get(item.finding, 0) + 1
        by_severity[item.severity] = by_severity.get(item.severity, 0) + 1
    return {
        "total_rows": len(rows),
        "findings": [item.__dict__ for item in findings],
        "summary": {
            "total_findings": len(findings),
            "by_finding": by_finding,
            "by_severity": by_severity,
        },
    }
