from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple


@dataclass(frozen=True)
class TextFieldSpec:
    form_text: str | None
    meaning_text: str | None
    short_gloss: str | None = None
    meaning_fallback: bool = False


_WHITESPACE_RE = re.compile(r"\s+")
_ARABIC_SENTENCE_RE = re.compile(r"[.!?؟]\s*")
_ARABIC_CLAUSE_RE = re.compile(r"[،؛]")
_GENERIC_SPLIT_RE = re.compile(r"[;|/]|(?:\s+-\s+)|(?:\s+[•·]\s+)")
_LEADIN_RE = re.compile(
    r"^(?:to\s+|the\s+|a\s+|an\s+|that\s+which\s+|that\s+|be\s+|being\s+|act\s+of\s+)+",
    flags=re.IGNORECASE,
)
_ARABIC_DEF_MARKERS = ("هو", "هي", "أي", "كل ما", ":")
_ARABIC_STRONG_DEF_MARKERS = ("هو", "هي", "أي", "كل ما", "المعروف", "الذي", "التي")
_ARABIC_META_MARKERS = (
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
    "انما",
    "وحد",
    "لغة في",
    "حكاها",
    "قبل العقوبة",
)


def _is_arabic_language(language: str) -> bool:
    lang = (language or "").strip().lower()
    return lang == "arabic" or lang == "ara" or lang.startswith("ara-")


def build_form_text(*, language: str, lemma: str, translit: str | None = None, ipa: str | None = None) -> str:
    """
    Deterministic form_text builder (scaffold).
    Arabic: include script + translit; others: lemma plus IPA if present.
    """
    parts: list[str] = []
    if lemma:
        if _is_arabic_language(language):
            parts.append(f"AR: {lemma}")
        else:
            parts.append(lemma)
    if translit:
        parts.append(f"TR: {translit}")
    if ipa:
        parts.append(f"IPA: {ipa}")
    return " | ".join(parts).strip()


def _clean_gloss_text(value: str | None) -> str:
    text = _WHITESPACE_RE.sub(" ", str(value or "")).strip(" ;,.:-")
    text = re.sub(r"^\s*[^\s]+?\s+[—\-]\s+\[[^\]]+\]\s*", "", text)
    text = re.sub(r"^\s*\[[^\]]+\]\s*", "", text)
    if text.startswith("وكل "):
        text = text[1:]
    return text


def _is_lexicographic_meta(chunk: str) -> bool:
    lowered = _clean_gloss_text(chunk)
    return any(marker in lowered for marker in _ARABIC_META_MARKERS)


def _gloss_candidate_score(chunk: str) -> float:
    cleaned = _clean_gloss_text(chunk)
    score = 0.0
    if not cleaned:
        return -1e9
    if _is_lexicographic_meta(cleaned):
        score -= 5.0
    if any(marker in cleaned for marker in ("هو", "هي", "كل", "أي")):
        score += 2.0
    if any(marker in cleaned for marker in _ARABIC_STRONG_DEF_MARKERS):
        score += 2.5
    if "من " in cleaned or "لل" in cleaned:
        score += 0.4
    if any(marker in cleaned for marker in ("معروف", "الذكر من", "الانثى", "أسفل", "استماع", "علم")):
        score += 1.0
    if len(cleaned) <= 40:
        score += 1.5
    elif len(cleaned) <= 80:
        score += 0.5
    if len(cleaned.split()) <= 2:
        score -= 0.8
    if cleaned.startswith("(") or cleaned.endswith(")"):
        score -= 0.8
    if cleaned.count(":") > 1:
        score -= 0.5
    score -= len(cleaned) / 200.0
    return score


def build_short_gloss(*, language: str, gloss_plain: str | None = None, fallback_definition: str | None = None) -> str | None:
    raw = gloss_plain or fallback_definition
    text = _clean_gloss_text(raw)
    if not text:
        return None
    if _is_arabic_language(language):
        sentences = [part.strip() for part in _ARABIC_SENTENCE_RE.split(text) if part.strip()]
        if not sentences:
            sentences = [text]
        candidates: list[str] = []
        for sentence in sentences[:8]:
            clauses = [part.strip(" ;,:-") for part in _ARABIC_CLAUSE_RE.split(sentence) if part.strip(" ;,:-")]
            if not clauses:
                clauses = [sentence]
            for clause in clauses:
                parts = [
                    _clean_gloss_text(_LEADIN_RE.sub("", item.strip(" ;,:-")))
                    for item in _GENERIC_SPLIT_RE.split(clause)
                    if item.strip(" ;,:-")
                ]
                candidates.extend(parts)
        pool = [chunk for chunk in candidates if chunk and not _is_lexicographic_meta(chunk)]
        definitional = [chunk for chunk in pool if any(marker in chunk for marker in _ARABIC_DEF_MARKERS)]
        if not definitional:
            definitional = [chunk for chunk in pool if any(marker in chunk for marker in _ARABIC_STRONG_DEF_MARKERS)]
        ranked = sorted(definitional or pool or candidates, key=_gloss_candidate_score, reverse=True)
        selected: list[str] = []
        for chunk in ranked:
            if chunk.casefold() in {item.casefold() for item in selected}:
                continue
            selected.append(chunk)
            if len(selected) >= 2:
                break
        gloss = " / ".join(selected).strip(" /")
        return gloss[:99] + "…" if len(gloss) > 100 else gloss

    parts = [
        _clean_gloss_text(_LEADIN_RE.sub("", item.strip(" ;,:-")))
        for item in _GENERIC_SPLIT_RE.split(text)
        if item.strip(" ;,:-")
    ]
    selected: list[str] = []
    for part in parts:
        if not part or part.casefold() in {item.casefold() for item in selected}:
            continue
        selected.append(part)
        if len(selected) >= 3:
            break
    if not selected:
        return None
    gloss = " / ".join(selected).strip(" /")
    return gloss[:119] + "…" if len(gloss) > 120 else gloss


def build_meaning_text(gloss_plain: str | None, lemma: str | None = None, fallback_definition: str | None = None) -> Tuple[str | None, bool]:
    """
    Deterministic meaning_text builder (scaffold).
    - Prefer gloss_plain.
    - If missing but fallback_definition exists, use "<lemma> — <fallback_definition>" and flag meaning_fallback=True.
    - Otherwise return (None, False).
    """
    if gloss_plain and gloss_plain.strip():
        return gloss_plain.strip(), False
    if fallback_definition and fallback_definition.strip():
        base = (lemma or "").strip()
        if base:
            return f"{base} — {fallback_definition.strip()}", True
        return fallback_definition.strip(), True
    return None, False


def iter_text_fields(rows: Iterable[dict]) -> Iterable[dict]:
    """
    Given iterable of LV0 rows, yield rows with form_text / meaning_text populated when possible.
    This is a placeholder; final implementation should read from JSONL and write back deterministically.
    """
    for rec in rows:
        lang = rec.get("language", "")
        lemma = rec.get("lemma", "")
        translit = rec.get("translit") or None
        ipa = rec.get("ipa") or rec.get("ipa_raw") or None
        form = build_form_text(language=lang, lemma=lemma, translit=translit, ipa=ipa)
        meaning, fallback = build_meaning_text(
            gloss_plain=rec.get("gloss_plain"),
            lemma=lemma,
            fallback_definition=rec.get("definition") or rec.get("gloss"),
        )
        short_gloss = build_short_gloss(
            language=lang,
            gloss_plain=rec.get("gloss_plain"),
            fallback_definition=rec.get("definition") or rec.get("gloss"),
        )
        rec = dict(rec)
        rec["form_text"] = form
        if meaning:
            rec["meaning_text"] = meaning
            rec["meaning_fallback"] = fallback
        if short_gloss:
            rec["short_gloss"] = short_gloss
        yield rec


def main() -> int:
    """
    CLI for adding form_text and meaning_text fields to JSONL lexeme files.

    Usage:
        python -m juthoor_datacore_lv0.features.build_text_fields \\
            input.jsonl output.jsonl --overwrite
    """
    import argparse
    import json

    ap = argparse.ArgumentParser(
        description="Add form_text and meaning_text fields to LV0 JSONL rows.",
        epilog="Fields are generated deterministically from existing lemma/translit/ipa/gloss data.",
    )
    ap.add_argument("input_jsonl", type=Path, help="Input JSONL file.")
    ap.add_argument("output_jsonl", type=Path, help="Output JSONL file.")
    ap.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing form_text/meaning_text fields (default: skip rows with existing fields).",
    )
    args = ap.parse_args()

    if not args.input_jsonl.exists():
        print(f"ERROR: Input file not found: {args.input_jsonl}")
        return 1

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    input_path = args.input_jsonl.resolve()
    output_path = args.output_jsonl.resolve()
    same_path = input_path == output_path
    temp_output_path = output_path.with_suffix(output_path.suffix + ".tmp") if same_path else output_path

    processed = 0
    skipped = 0
    enriched = 0

    with input_path.open("r", encoding="utf-8", errors="replace") as inp, \
         temp_output_path.open("w", encoding="utf-8") as out:
        for line in inp:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)

            # Skip if fields exist and not overwriting
            has_form = bool(rec.get("form_text"))
            has_meaning = bool(rec.get("meaning_text"))
            if not args.overwrite and has_form and has_meaning:
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                skipped += 1
                continue

            # Build text fields
            lang = rec.get("language", "")
            lemma = rec.get("lemma", "")
            translit = rec.get("translit") or None
            ipa = rec.get("ipa") or rec.get("ipa_raw") or None
            form = build_form_text(language=lang, lemma=lemma, translit=translit, ipa=ipa)
            meaning, fallback = build_meaning_text(
                gloss_plain=rec.get("gloss_plain"),
                lemma=lemma,
                fallback_definition=rec.get("definition") or rec.get("gloss"),
            )
            short_gloss = build_short_gloss(
                language=lang,
                gloss_plain=rec.get("gloss_plain"),
                fallback_definition=rec.get("definition") or rec.get("gloss"),
            )

            if form:
                rec["form_text"] = form
            if meaning:
                rec["meaning_text"] = meaning
                rec["meaning_fallback"] = fallback
                enriched += 1
            if short_gloss:
                rec["short_gloss"] = short_gloss

            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            processed += 1

    if same_path:
        os.replace(temp_output_path, output_path)

    print(f"Processed: {processed}, Enriched: {enriched}, Skipped (existing): {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
