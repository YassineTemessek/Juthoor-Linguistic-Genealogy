from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _meaning_text(record: dict[str, Any]) -> str:
    parts: list[str] = []
    if record.get("binary_root_meaning"):
        parts.append(str(record["binary_root_meaning"]).strip())
    if record.get("axial_meaning"):
        parts.append(str(record["axial_meaning"]).strip())
    if record.get("quran_example"):
        parts.append(f"Quran: {str(record['quran_example']).strip()}")
    return " | ".join(part for part in parts if part)


def _form_text(root: str, words: list[str]) -> str:
    preview = ", ".join(words[:8])
    return f"{root} | words: {preview}" if preview else root


def build_root_family_record(record: dict[str, Any], *, lang: str = "ara", stage: str = "classical") -> dict[str, Any]:
    root = str(record.get("root") or "").strip()
    words = [str(item).strip() for item in record.get("words", []) if str(item).strip()]
    meaning_text = _meaning_text(record)
    return {
        "id": f"rootfam:{lang}:{root}",
        "lemma": root,
        "lang": lang,
        "stage": stage,
        "record_type": "root_family",
        "bab": record.get("bab"),
        "binary_root": record.get("binary_root"),
        "root_norm": root,
        "words": words,
        "word_count": len(words),
        "muajam_match": bool(record.get("muajam_match")),
        "semantic_score": record.get("semantic_score"),
        "binary_root_meaning": record.get("binary_root_meaning"),
        "axial_meaning": record.get("axial_meaning"),
        "quran_example": record.get("quran_example"),
        "form_text": _form_text(root, words),
        "meaning_text": meaning_text,
        "gloss_plain": meaning_text,
    }


def build_root_family_corpus(
    input_dir: Path,
    output_path: Path,
    *,
    lang: str = "ara",
    stage: str = "classical",
) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output_path.open("w", encoding="utf-8") as out_handle:
        for path in sorted(input_dir.glob("*.jsonl")):
            with path.open("r", encoding="utf-8") as in_handle:
                for line in in_handle:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    root = str(record.get("root") or "").strip()
                    if not root:
                        continue
                    out_handle.write(
                        json.dumps(build_root_family_record(record, lang=lang, stage=stage), ensure_ascii=False) + "\n"
                    )
                    count += 1
    return count
