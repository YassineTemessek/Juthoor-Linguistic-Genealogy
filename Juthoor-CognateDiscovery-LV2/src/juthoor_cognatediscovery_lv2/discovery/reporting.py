"""
Reporting and output logic for LV2 discovery.
Handles result serialization and HTML report generation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .correspondence import best_radical_text, correspondence_string, explain_correspondence_rules, literal_skeleton


def _strength_label(value: float | None) -> str:
    if value is None:
        return "missing"
    if value >= 0.75:
        return "high"
    if value >= 0.4:
        return "medium"
    return "low"


def _surface_forms(side: dict[str, Any]) -> list[str]:
    values = [side.get("lemma"), side.get("translit")]
    return [str(item).strip() for item in values if str(item or "").strip()]


def _correspondence_note(entry: dict[str, Any]) -> str:
    rules = explain_correspondence_rules(entry.get("source", {}), entry.get("target", {}))
    if rules:
        return "; ".join(rules)
    hybrid = entry.get("hybrid", {})
    components = hybrid.get("components", {})
    if float(components.get("correspondence", 0.0)) >= 0.7:
        return "strong consonant-class correspondence"
    if float(components.get("correspondence", 0.0)) >= 0.4:
        return "partial consonant-class correspondence"
    return "correspondence evidence is weak or tentative"


def _candidate_category(entry: dict[str, Any]) -> str:
    return str(entry.get("category") or "tentative_candidate")


def _why_this_candidate(entry: dict[str, Any]) -> str:
    scores = entry.get("scores", {})
    hybrid = entry.get("hybrid", {})
    components = hybrid.get("components", {})
    parts: list[str] = []
    semantic = _strength_label(scores.get("semantic"))
    form = _strength_label(scores.get("form"))
    corr = _strength_label(components.get("correspondence"))
    skeleton = _strength_label(components.get("skeleton"))
    if semantic in {"high", "medium"}:
        parts.append(f"{semantic} semantic alignment")
    if form in {"high", "medium"}:
        parts.append(f"{form} form similarity")
    if skeleton in {"high", "medium"}:
        parts.append(f"{skeleton} skeleton support")
    if corr in {"high", "medium"}:
        parts.append(f"{corr} correspondence support")
    if hybrid.get("root_match_applied"):
        parts.append("direct root-family support")
    if not parts:
        return "Signals are weak; treat this candidate as tentative."
    return "This candidate shows " + ", ".join(parts) + "."


def build_evidence_card(entry: dict[str, Any]) -> dict[str, Any]:
    source = entry.get("source", {})
    target = entry.get("target", {})
    scores = entry.get("scores", {})
    hybrid = entry.get("hybrid", {})
    components = hybrid.get("components", {})
    source_root = best_radical_text(source)
    target_root = best_radical_text(target)
    source_skeleton = literal_skeleton(source_root)
    target_skeleton = literal_skeleton(target_root)
    source_classes = correspondence_string(source_root)
    target_classes = correspondence_string(target_root)
    category = _candidate_category(entry)
    return {
        "surface_shape": {
            "source": _surface_forms(source),
            "target": _surface_forms(target),
        },
        "phonetic_form": {
            "source_ipa": source.get("ipa"),
            "target_ipa": target.get("ipa"),
        },
        "root_or_skeleton": {
            "source_root": source.get("root_norm"),
            "target_root": target.get("root_norm"),
            "source_skeleton": source_skeleton,
            "target_skeleton": target_skeleton,
            "source_classes": source_classes,
            "target_classes": target_classes,
        },
        "meaning": {
            "source_gloss": source.get("gloss") or source.get("meaning_text"),
            "target_gloss": target.get("gloss") or target.get("meaning_text"),
        },
        "score_breakdown": {
            "semantic": {"value": scores.get("semantic"), "strength": _strength_label(scores.get("semantic"))},
            "form": {"value": scores.get("form"), "strength": _strength_label(scores.get("form"))},
            "orthography": {"value": components.get("orthography"), "strength": _strength_label(components.get("orthography"))},
            "sound": {"value": components.get("sound"), "strength": _strength_label(components.get("sound"))},
            "skeleton": {"value": components.get("skeleton"), "strength": _strength_label(components.get("skeleton"))},
            "correspondence": {"value": components.get("correspondence"), "strength": _strength_label(components.get("correspondence"))},
        },
        "root_family_support": bool(hybrid.get("root_match_applied")),
        "candidate_category": category,
        "correspondence_note": _correspondence_note(entry),
        "confidence_note": "tentative" if float(hybrid.get("combined_score", 0.0) or 0.0) < 0.6 else "promising",
        "why_this_candidate": _why_this_candidate(entry),
    }


def write_leads(leads: list[dict[str, Any]], out_path: Path) -> None:
    """
    Writes lead records to a JSONL file.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as out_fh:
        for row in leads:
            row = dict(row)
            row["candidate_category"] = _candidate_category(row)
            row["evidence_card"] = build_evidence_card(row)
            out_fh.write(json.dumps(row, ensure_ascii=False) + "\n")

def generate_discovery_report(out_path: Path, script_dir: Path) -> None:
    """
    Attempts to generate an HTML report for a discovery run.
    Uses the co-located report.py script.
    """
    try:
        # Import report generator from scripts/discovery/
        import sys
        if str(script_dir) not in sys.path:
            sys.path.append(str(script_dir))
            
        from report import generate_report
        report_path = out_path.with_suffix(".html")
        generate_report(out_path, report_path)
        print(f"Wrote HTML report:     {report_path}")
    except Exception as exc:
        print(f"[warn] Could not generate HTML report: {exc}")
