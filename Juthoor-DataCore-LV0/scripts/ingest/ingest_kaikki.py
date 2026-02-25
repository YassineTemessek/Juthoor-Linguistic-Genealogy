"""
Ingest Kaikki.org Wiktionary JSONL dumps into LV0 canonical JSONL.

Supports: Ancient Greek (grc), Latin (la), Old English (ang),
          Middle English (enm), Modern English (en).

Default input locations (relative to repo root, or under LC_RESOURCES_DIR):
  grc  -> Resources/ancient_greek/kaikki.org-dictionary-AncientGreek.jsonl
  la   -> Resources/latin/kaikki.org-dictionary-Latin.jsonl
  ang  -> Resources/english_old/kaikki.org-dictionary-OldEnglish.jsonl
  enm  -> Resources/english_middle/kaikki.org-dictionary-MiddleEnglish.jsonl
  en   -> Resources/english_modern/kaikki.org-dictionary-English.jsonl

Default output locations (relative to repo root):
  grc  -> data/processed/ancient_greek/sources/kaikki.jsonl
  la   -> data/processed/latin/classical/sources/kaikki.jsonl
  ang  -> data/processed/english_old/sources/kaikki.jsonl
  enm  -> data/processed/english_middle/sources/kaikki.jsonl
  en   -> data/processed/english_modern/sources/kaikki.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Iterator

from processed_schema import ensure_min_schema, normalize_ipa

# Try to import write_manifest from the installed package; fall back to adding src/ to path.
try:
    from ingest.utils import write_manifest
except ImportError:
    _src = Path(__file__).resolve().parents[2] / "src"
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))
    from juthoor_datacore_lv0.ingest.utils import write_manifest  # type: ignore[no-redef]


# ---------------------------------------------------------------------------
# Language mapping
# ---------------------------------------------------------------------------

# lang_code -> (language, stage, script)
LANG_MAP: dict[str, tuple[str, str, str]] = {
    "grc": ("grc", "ancient", "Grek"),
    "la":  ("lat", "classical", "Latn"),
    "ang": ("ang", "old", "Latn"),
    "enm": ("enm", "middle", "Latn"),
    "en":  ("eng", "modern", "Latn"),
}

# lang_code -> relative path WITHIN Resources/ (no Resources/ prefix)
LANG_CODE_TO_FILE: dict[str, str] = {
    "grc": "ancient_greek/kaikki.org-dictionary-AncientGreek.jsonl",
    "la":  "latin/kaikki.org-dictionary-Latin.jsonl",
    "ang": "english_old/kaikki.org-dictionary-OldEnglish.jsonl",
    "enm": "english_middle/kaikki.org-dictionary-MiddleEnglish.jsonl",
    "en":  "english_modern/kaikki.org-dictionary-English.jsonl",
}

_DEFAULT_OUTPUT: dict[str, str] = {
    "grc": "data/processed/ancient_greek/sources/kaikki.jsonl",
    "la":  "data/processed/latin/classical/sources/kaikki.jsonl",
    "ang": "data/processed/english_old/sources/kaikki.jsonl",
    "enm": "data/processed/english_middle/sources/kaikki.jsonl",
    "en":  "data/processed/english_modern/sources/kaikki.jsonl",
}

# Latin-script languages where translit == lemma
_LATIN_SCRIPT_LANGS = {"la", "ang", "enm", "en"}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_record(raw: dict) -> dict | None:
    """Parse a single Kaikki.org JSONL record into an LV0 canonical dict.

    Returns None if the record should be skipped (empty word or unknown lang_code).
    """
    word: str = (raw.get("word") or "").strip()
    if not word:
        return None

    lang_code: str = (raw.get("lang_code") or "").strip()
    if lang_code not in LANG_MAP:
        return None

    language, stage, script = LANG_MAP[lang_code]

    # POS: wrap string in list
    pos_raw = raw.get("pos") or ""
    pos = [pos_raw.strip()] if pos_raw.strip() else []

    # IPA: first sounds entry that has an "ipa" key
    ipa_raw = ""
    for sound in raw.get("sounds") or []:
        if "ipa" in sound:
            ipa_raw = sound["ipa"]
            break

    ipa_norm = normalize_ipa(ipa_raw)

    # Gloss: first non-empty glosses list in senses
    gloss_plain = ""
    for sense in raw.get("senses") or []:
        glosses = sense.get("glosses") or []
        for g in glosses:
            g = str(g).strip()
            if g:
                gloss_plain = g
                break
        if gloss_plain:
            break

    # form_text and meaning_text
    form_text = f"{word} | IPA: {ipa_norm}" if ipa_norm else word
    meaning_text = gloss_plain if gloss_plain else ""

    rec: dict = {
        "lemma": word,
        "language": language,
        "stage": stage,
        "script": script,
        "source": "kaikki-wiktionary",
        "lemma_status": "attested",
        "pos": pos,
        "ipa_raw": ipa_raw,
        "gloss_plain": gloss_plain,
        "form_text": form_text,
    }

    if meaning_text:
        rec["meaning_text"] = meaning_text

    # translit = lemma for Latin-script languages
    if lang_code in _LATIN_SCRIPT_LANGS:
        rec["translit"] = word

    rec = ensure_min_schema(rec)
    return rec


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------

def ingest_lines(lines: Iterator[str], out_path: Path) -> int:
    """Parse and write LV0 JSONL records from an iterator of raw JSON lines.

    Handles ID disambiguation: if the base ID is already seen, appends :{n}.
    Returns the count of records written.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    seen_ids: dict[str, int] = {}
    count = 0

    with out_path.open("w", encoding="utf-8") as out_f:
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue

            rec = parse_record(raw)
            if rec is None:
                continue

            base_id: str = rec["id"]
            if base_id in seen_ids:
                seen_ids[base_id] += 1
                rec["id"] = f"{base_id}:{seen_ids[base_id]}"
            else:
                seen_ids[base_id] = 0

            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count += 1

    return count


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _default_input(lang_code: str) -> Path:
    resources_dir = os.environ.get("LC_RESOURCES_DIR")
    if resources_dir:
        return Path(resources_dir) / LANG_CODE_TO_FILE[lang_code]
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "Resources" / LANG_CODE_TO_FILE[lang_code]


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Ingest Kaikki.org Wiktionary JSONL into LV0 canonical JSONL.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument(
        "--lang-code",
        required=True,
        choices=list(LANG_MAP.keys()),
        help="Kaikki lang_code to ingest.",
    )
    ap.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to Kaikki JSONL input file. Defaults to Resources/<lang>/kaikki.jsonl.",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path for canonical JSONL output.",
    )
    ap.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to write a manifest JSON file.",
    )
    args = ap.parse_args()

    lang_code: str = args.lang_code
    repo_root = Path(__file__).resolve().parents[2]

    in_path: Path = args.input if args.input else _default_input(lang_code)
    out_path: Path = args.output if args.output else (repo_root / _DEFAULT_OUTPUT[lang_code])

    if not in_path.exists():
        raise SystemExit(f"Input file not found: {in_path}")

    with in_path.open("r", encoding="utf-8", errors="replace") as fh:
        count = ingest_lines(fh, out_path)

    print(f"Wrote {count} records to {out_path}")

    manifest_path: Path | None = args.manifest
    if manifest_path is None:
        manifest_path = out_path.parent / "kaikki_manifest.json"

    write_manifest(
        target=out_path,
        manifest_path=manifest_path,
        schema_version="lv0.7",
        generated_by=f"ingest_kaikki.py:{lang_code}",
    )
    print(f"Wrote manifest to {manifest_path}")


if __name__ == "__main__":
    main()
