from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple


@dataclass(frozen=True)
class TextFieldSpec:
    form_text: str | None
    meaning_text: str | None
    meaning_fallback: bool = False


def build_form_text(*, language: str, lemma: str, translit: str | None = None, ipa: str | None = None) -> str:
    """
    Deterministic form_text builder (scaffold).
    Arabic: include script + translit; others: lemma plus IPA if present.
    """
    lang = (language or "").lower()
    parts: list[str] = []
    if lemma:
        if lang.startswith("ar"):
            parts.append(f"AR: {lemma}")
        else:
            parts.append(lemma)
    if translit:
        parts.append(f"TR: {translit}")
    if ipa:
        parts.append(f"IPA: {ipa}")
    return " | ".join(parts).strip()


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
        gloss = rec.get("gloss_plain") or rec.get("definition")
        form = build_form_text(language=lang, lemma=lemma, translit=translit, ipa=ipa)
        meaning, fallback = build_meaning_text(gloss_plain=gloss, lemma=lemma)
        rec = dict(rec)
        rec["form_text"] = form
        if meaning:
            rec["meaning_text"] = meaning
            rec["meaning_fallback"] = fallback
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

    processed = 0
    skipped = 0
    enriched = 0

    with args.input_jsonl.open("r", encoding="utf-8", errors="replace") as inp, \
         args.output_jsonl.open("w", encoding="utf-8") as out:
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
            gloss = rec.get("gloss_plain") or rec.get("definition") or rec.get("gloss")

            form = build_form_text(language=lang, lemma=lemma, translit=translit, ipa=ipa)
            meaning, fallback = build_meaning_text(gloss_plain=gloss, lemma=lemma)

            if form:
                rec["form_text"] = form
            if meaning:
                rec["meaning_text"] = meaning
                rec["meaning_fallback"] = fallback
                enriched += 1

            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            processed += 1

    print(f"Processed: {processed}, Enriched: {enriched}, Skipped (existing): {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
