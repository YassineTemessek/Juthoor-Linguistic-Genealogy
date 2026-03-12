"""
Reporting and output logic for LV2 discovery.
Handles result serialization and HTML report generation.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .correspondence import best_radical_text, correspondence_string, explain_correspondence_rules, literal_skeleton


_WHITESPACE_RE = re.compile(r"\s+")
_GLOSS_SPLIT_RE = re.compile(r"[;|/]|(?:\s+-\s+)|(?:\s+[•·]\s+)")
_ARABIC_GLOSS_SPLIT_RE = re.compile(r"[،؛]")
_LEADIN_RE = re.compile(
    r"^(?:to\s+|the\s+|a\s+|an\s+|that\s+which\s+|that\s+|be\s+|being\s+|act\s+of\s+)+",
    flags=re.IGNORECASE,
)
_ARABIC_DEF_MARKERS = ("هو", "هي", "كل", "أي", ":")


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


def _clean_gloss_text(value: Any) -> str:
    text = _WHITESPACE_RE.sub(" ", str(value or "")).strip(" ;,.:-")
    if text.startswith("وكل "):
        text = text[1:]
    return text


def _strip_dictionary_preamble(text: str) -> str:
    text = re.sub(r"^\s*[^\s]+?\s+[—\-]\s+\[[^\]]+\]\s*", "", text)
    text = re.sub(r"^\s*\[[^\]]+\]\s*", "", text)
    return text.strip()


def _is_lexicographic_meta(chunk: str) -> bool:
    lowered = _clean_gloss_text(chunk)
    markers = (
        "يقال",
        "قال",
        "الجمع",
        "الواحدة",
        "مؤنثة",
        "مذكر",
        "اسم جنس",
        "على غير قياس",
        "بالواو والنون",
        "تجمع",
        "زعم",
        "وربما",
        "كقولهم",
        "ولكنهم",
        "لانهم",
        "ثم قالوا",
    )
    return any(marker in lowered for marker in markers)


def _is_arabic_side(side: dict[str, Any]) -> bool:
    lang = str(side.get("lang") or "").casefold()
    text = "".join(str(side.get(key) or "") for key in ("lemma", "gloss", "meaning_text"))
    return lang.startswith("ara") or any("\u0600" <= ch <= "\u06FF" for ch in text)


def _gloss_candidate_score(chunk: str) -> float:
    cleaned = _clean_gloss_text(chunk)
    score = 0.0
    if not cleaned:
        return -1e9
    if _is_lexicographic_meta(cleaned):
        score -= 5.0
    if any(marker in cleaned for marker in ("هو", "هي", "كل", "أي")):
        score += 2.0
    if len(cleaned) <= 40:
        score += 1.5
    elif len(cleaned) <= 80:
        score += 0.5
    score -= len(cleaned) / 200.0
    return score


def _extract_gloss_candidates(text: str) -> list[str]:
    if not text:
        return []
    sentences = [part.strip() for part in re.split(r"[.!?]\s+", text) if part.strip()]
    if not sentences:
        sentences = [text]
    filler_terms = {
        "وهى اسم جنس",
        "وهو اسم جنس",
        "مؤنثة",
        "مذكر",
        "اسم جنس",
        "الارض مؤنثة",
    }
    candidates: list[str] = []
    for sentence in sentences[:8]:
        sentence_parts = [part.strip(" ;,:-") for part in _ARABIC_GLOSS_SPLIT_RE.split(sentence) if part.strip(" ;,:-")]
        trial_chunks: list[str] = []
        for part in sentence_parts or [sentence]:
            trial_chunks.extend(_LEADIN_RE.sub("", item.strip(" ;,:-")) for item in _GLOSS_SPLIT_RE.split(part))
        trial_chunks = [chunk for chunk in trial_chunks if chunk]
        trial_chunks = [chunk for chunk in trial_chunks if chunk not in filler_terms]
        candidates.extend(trial_chunks)
    if not candidates:
        candidates = [sentences[0]]
    chunks = [_clean_gloss_text(re.sub(r"\s{2,}", " ", chunk).strip(" ;,:-")) for chunk in candidates if chunk.strip(" ;,:-")]
    return [chunk for chunk in chunks if chunk and chunk not in filler_terms]


def _select_arabic_gloss(value: Any, *, max_items: int = 2, max_chars: int = 100) -> str | None:
    text = _clean_gloss_text(value)
    if not text:
        return None
    text = _strip_dictionary_preamble(text)
    chunks = _extract_gloss_candidates(text)
    if not chunks:
        return None
    definitional = [chunk for chunk in chunks if any(marker in chunk for marker in _ARABIC_DEF_MARKERS) and not _is_lexicographic_meta(chunk)]
    pool = definitional or [chunk for chunk in chunks if not _is_lexicographic_meta(chunk)] or chunks
    ordered = sorted(pool, key=_gloss_candidate_score, reverse=True)
    selected: list[str] = []
    for chunk in ordered:
        if chunk.casefold() in {item.casefold() for item in selected}:
            continue
        selected.append(chunk)
        if len(selected) >= max_items:
            break
    gloss = " / ".join(selected).strip(" /")
    if len(gloss) <= max_chars:
        return gloss
    trimmed = gloss[: max_chars - 1].rstrip(" ,;/:-")
    return trimmed + "…"


def _compact_gloss(value: Any, *, max_items: int = 3, max_chars: int = 120) -> str | None:
    text = _clean_gloss_text(value)
    if not text:
        return None
    text = _strip_dictionary_preamble(text)
    chunks = _extract_gloss_candidates(text)
    if not chunks:
        return None
    chunks = sorted(chunks, key=_gloss_candidate_score, reverse=True)
    selected: list[str] = []
    for chunk in chunks:
        if chunk.casefold() in {item.casefold() for item in selected}:
            continue
        selected.append(chunk)
        if len(selected) >= max_items:
            break
    gloss = " / ".join(selected).strip(" /")
    if len(gloss) <= max_chars:
        return gloss
    trimmed = gloss[: max_chars - 1].rstrip(" ,;/:-")
    return trimmed + "…"


def _preferred_gloss(side: dict[str, Any]) -> str | None:
    for key in ("gloss", "gloss_plain", "meaning_text", "definition", "sense"):
        if _is_arabic_side(side):
            compact = _select_arabic_gloss(side.get(key))
        else:
            compact = _compact_gloss(side.get(key))
        if compact:
            return compact
    return None


def _shared_concept(source_gloss: str | None, target_gloss: str | None) -> str | None:
    if source_gloss and target_gloss:
        if any("a" <= ch.lower() <= "z" for ch in target_gloss):
            return target_gloss
        return source_gloss if len(source_gloss) <= len(target_gloss) else target_gloss
    return target_gloss or source_gloss


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
    existing = entry.get("candidate_category") or entry.get("category")
    if existing:
        return str(existing)
    scores = entry.get("scores", {})
    hybrid = entry.get("hybrid", {})
    components = hybrid.get("components", {})
    semantic = float(scores.get("semantic", 0.0) or 0.0)
    form = float(scores.get("form", 0.0) or 0.0)
    corr = float(components.get("correspondence", 0.0) or 0.0)
    skeleton = float(components.get("skeleton", 0.0) or 0.0)
    if hybrid.get("root_match_applied") or (semantic >= 0.6 and (corr >= 0.6 or skeleton >= 0.6 or form >= 0.6)):
        return "likely_cognate_candidate"
    if semantic >= 0.7 and form < 0.35 and corr < 0.35 and skeleton < 0.35:
        return "translation_only_candidate"
    if semantic < 0.45 and (form >= 0.55 or corr >= 0.55):
        return "shape_only_resemblance"
    return "tentative_candidate"


def _category_label(category: str) -> str:
    return {
        "likely_cognate_candidate": "strong cognate candidate",
        "translation_only_candidate": "translation-led candidate",
        "shape_only_resemblance": "shape-led resemblance",
        "tentative_candidate": "tentative candidate",
    }.get(category, category.replace("_", " "))


def _why_this_candidate(entry: dict[str, Any]) -> str:
    scores = entry.get("scores", {})
    hybrid = entry.get("hybrid", {})
    components = hybrid.get("components", {})
    semantic = _strength_label(scores.get("semantic"))
    form = _strength_label(scores.get("form"))
    corr = _strength_label(components.get("correspondence"))
    skeleton = _strength_label(components.get("skeleton"))
    root_support = bool(hybrid.get("root_match_applied"))
    category = _candidate_category(entry)

    strengths: list[str] = []
    cautions: list[str] = []
    if semantic in {"high", "medium"}:
        strengths.append(f"{semantic} semantic alignment")
    else:
        cautions.append("semantic support is weak")
    if form in {"high", "medium"}:
        strengths.append(f"{form} form similarity")
    elif form == "low":
        cautions.append("surface-form similarity is limited")
    if skeleton in {"high", "medium"}:
        strengths.append(f"{skeleton} consonantal skeleton support")
    elif skeleton == "low":
        cautions.append("skeleton support is weak")
    if corr in {"high", "medium"}:
        strengths.append(f"{corr} correspondence evidence")
    elif corr == "low":
        cautions.append("correspondence evidence is weak")
    if root_support:
        strengths.append("direct root-family support")

    if not strengths:
        return "Signals are weak; treat this candidate as tentative."

    if category == "likely_cognate_candidate":
        if root_support:
            return "Strong cognate candidate with direct root-family support and " + ", ".join(strengths[:-1] or strengths) + "."
        return "Strong cognate candidate with " + ", ".join(strengths) + "."
    if category == "translation_only_candidate":
        base = "Meaning aligns strongly, but form and correspondence support stay weak; this may be translation-led rather than genealogical."
        if cautions:
            return base + " " + cautions[0].capitalize() + "."
        return base
    if category == "shape_only_resemblance":
        base = "Form-level resemblance is stronger than the semantic signal, so this may be accidental or borrowing-like."
        if strengths:
            return base + " Best evidence: " + ", ".join(strengths) + "."
        return base

    message = f"{_category_label(category).capitalize()} with " + ", ".join(strengths) + "."
    if cautions:
        message += " " + cautions[0].capitalize() + "."
    return message


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
    source_gloss = _preferred_gloss(source)
    target_gloss = _preferred_gloss(target)
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
            "source_gloss": source_gloss,
            "target_gloss": target_gloss,
            "shared_concept": _shared_concept(source_gloss, target_gloss),
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
