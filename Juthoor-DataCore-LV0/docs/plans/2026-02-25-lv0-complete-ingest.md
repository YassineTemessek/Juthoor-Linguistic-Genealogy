# LV0 Complete Ingest Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ingest all remaining raw data sources (Kaikki.org JSONL for Latin/Greek/Old/Middle/Modern English + 10 Arabic dictionaries) into LV0-compliant JSONL, then apply form_text/meaning_text to all outputs.

**Architecture:** One shared `ingest_kaikki.py` script handles all five Kaikki.org language dumps via a `--lang-code` flag. A separate `ingest_arabic_ten_dicts.py` handles the 10 semicolon-delimited Arabic CSVs. After each ingest step, `build_text_fields.py` is run as a post-process step. New Steps are registered in `runner.py:build_steps()`.

**Tech Stack:** Python 3.11+, `json` stdlib, `csv` stdlib, `processed_schema.py` (ensure_min_schema, normalize_ipa), `ingest/utils.py` (write_manifest), `features/build_text_fields.py` (iter_text_fields)

---

## Reference: Key File Paths

```
Juthoor-DataCore-LV0/
├── scripts/ingest/
│   ├── processed_schema.py          ← ensure_min_schema, normalize_ipa
│   ├── ingest_arabic_hf_roots.py    ← reference adapter pattern
│   ├── ingest_kaikki.py             ← CREATE (Task 1)
│   ├── ingest_arabic_ten_dicts.py   ← CREATE (Task 3)
│   └── run_ingest_all.py            → runner.py wraps this
├── src/juthoor_datacore_lv0/
│   ├── ingest/runner.py             ← MODIFY (Tasks 2, 4, 6)
│   └── features/build_text_fields.py ← already exists, just call it
├── tests/
│   ├── test_ingest_kaikki.py        ← CREATE (Task 1)
│   └── test_ingest_ten_dicts.py     ← CREATE (Task 3)
└── Resources/
    ├── ancient_greek/kaikki.org-dictionary-AncientGreek.jsonl
    ├── latin/kaikki.org-dictionary-Latin.jsonl
    ├── english_old/kaikki.org-dictionary-OldEnglish.jsonl
    ├── english_middle/kaikki.org-dictionary-MiddleEnglish.jsonl
    ├── english_modern/kaikki.org-dictionary-English.jsonl
    └── Ten dictionaries for Arabic language/  (48 CSV files, semicolon-sep)
```

## Reference: Kaikki JSONL record structure
```json
{
  "word": "thesaurus",
  "lang_code": "la",
  "pos": "noun",
  "senses": [{"glosses": ["treasure, hoard"], "tags": [...]}],
  "sounds": [{"tags": ["Classical-Latin"], "ipa": "[tʰeːˈsau̯.rʊs]"}],
  "etymology_text": "..."
}
```

## Reference: lang_code → LV0 mapping
| lang_code | language | stage | script |
|-----------|----------|-------|--------|
| grc | grc | ancient | Grek |
| la | lat | classical | Latn |
| ang | ang | old | Latn |
| enm | enm | middle | Latn |
| en | eng | modern | Latn |

## Reference: 10-dict CSV structure
```
Root;No of derevatives found;derevatives found;Root Length;Has Vowel;Full Text
```
- BOM-prefixed (`\ufeff`) — open with `encoding='utf-8-sig'`
- Semicolon-separated — use `csv.reader(f, delimiter=';')`
- Full Text is long Arabic dictionary prose

---

### Task 1: Kaikki.org ingest script + tests

**Files:**
- Create: `scripts/ingest/ingest_kaikki.py`
- Create: `tests/test_ingest_kaikki.py`

**Step 1: Write the failing test**

Create `tests/test_ingest_kaikki.py`:

```python
"""Tests for ingest_kaikki.py — uses inline fixture data, never reads real files."""
from __future__ import annotations
import json
import sys
from pathlib import Path
import pytest

# Add scripts/ingest to path so we can import directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "ingest"))

from ingest_kaikki import LANG_MAP, parse_record, ingest_lines


GREEK_RECORD = json.dumps({
    "word": "σκύλος", "lang_code": "grc", "pos": "noun",
    "senses": [{"glosses": ["skin, hide"]}],
    "sounds": [{"ipa": "/ský.los/"}]
})

LATIN_RECORD = json.dumps({
    "word": "thesaurus", "lang_code": "la", "pos": "noun",
    "senses": [{"glosses": ["treasure, hoard"]}],
    "sounds": [{"tags": ["Classical-Latin"], "ipa": "[tʰeːˈsau̯.rʊs]"}]
})

OE_RECORD = json.dumps({
    "word": "word", "lang_code": "ang", "pos": "noun",
    "senses": [{"glosses": ["word"]}],
    "sounds": [{"ipa": "/word/"}]
})

ME_RECORD = json.dumps({
    "word": "cat", "lang_code": "enm", "pos": "noun",
    "senses": [{"glosses": ["cat (feline)"]}],
    "sounds": [{"ipa": "/kat/"}]
})

EN_RECORD = json.dumps({
    "word": "house", "lang_code": "en", "pos": "noun",
    "senses": [{"glosses": ["a dwelling"]}],
    "sounds": [{"ipa": "/haʊs/"}]
})


def test_lang_map_covers_all_targets():
    for code in ("grc", "la", "ang", "enm", "en"):
        assert code in LANG_MAP, f"Missing lang_code {code} in LANG_MAP"


def test_parse_greek_record():
    rec = parse_record(json.loads(GREEK_RECORD))
    assert rec["lemma"] == "σκύλος"
    assert rec["language"] == "grc"
    assert rec["stage"] == "ancient"
    assert rec["script"] == "Grek"
    assert rec["pos"] == ["noun"]
    assert rec["gloss_plain"] == "skin, hide"
    assert "los" in rec["ipa"]  # normalized IPA strips /.../ brackets
    assert rec["source"] == "kaikki-wiktionary"
    assert rec["lemma_status"] == "attested"
    assert rec["id"]  # must be non-empty


def test_parse_latin_record():
    rec = parse_record(json.loads(LATIN_RECORD))
    assert rec["language"] == "lat"
    assert rec["stage"] == "classical"
    assert rec["gloss_plain"] == "treasure, hoard"
    assert "sau" in rec["ipa"]


def test_parse_old_english():
    rec = parse_record(json.loads(OE_RECORD))
    assert rec["language"] == "ang"
    assert rec["stage"] == "old"


def test_parse_middle_english():
    rec = parse_record(json.loads(ME_RECORD))
    assert rec["language"] == "enm"
    assert rec["stage"] == "middle"


def test_parse_modern_english():
    rec = parse_record(json.loads(EN_RECORD))
    assert rec["language"] == "eng"
    assert rec["stage"] == "modern"


def test_ingest_lines_deduplicates_ids(tmp_path):
    lines = [GREEK_RECORD, GREEK_RECORD]  # same record twice
    out = tmp_path / "out.jsonl"
    count = ingest_lines(iter(lines), out)
    assert count == 2  # both written; id disambiguator handles collisions
    written = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    ids = [r["id"] for r in written]
    assert ids[0] != ids[1], "Duplicate records must get distinct IDs"


def test_form_text_populated():
    rec = parse_record(json.loads(LATIN_RECORD))
    assert rec.get("form_text"), "form_text must be populated"
    assert "thesaurus" in rec["form_text"]


def test_meaning_text_populated():
    rec = parse_record(json.loads(LATIN_RECORD))
    assert rec.get("meaning_text") == "treasure, hoard"


def test_skips_empty_word():
    bad = {"word": "", "lang_code": "la", "pos": "noun", "senses": [{"glosses": ["x"]}]}
    rec = parse_record(bad)
    assert rec is None
```

**Step 2: Run test to verify it fails**

```
cd Juthoor-DataCore-LV0
pytest tests/test_ingest_kaikki.py -v
```
Expected: `ModuleNotFoundError: No module named 'ingest_kaikki'`

**Step 3: Write `scripts/ingest/ingest_kaikki.py`**

```python
"""
Ingest Kaikki.org Wiktionary JSONL dumps into LV0 JSONL.

Handles: Ancient Greek (grc), Latin (la), Old English (ang),
         Middle English (enm), Modern English (en).

Usage:
    python ingest_kaikki.py --input <path.jsonl> --output <out.jsonl> --lang-code la
    # or let it auto-detect lang_code from the first record
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterator

from processed_schema import ensure_min_schema, normalize_ipa

try:
    from ingest.utils import write_manifest  # when imported as package
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from juthoor_datacore_lv0.ingest.utils import write_manifest

# Map Kaikki lang_code → (language, stage, script)
LANG_MAP: dict[str, tuple[str, str, str]] = {
    "grc": ("grc", "ancient", "Grek"),
    "la":  ("lat", "classical", "Latn"),
    "ang": ("ang", "old", "Latn"),
    "enm": ("enm", "middle", "Latn"),
    "en":  ("eng", "modern", "Latn"),
}


def _pick_ipa(sounds: list[dict]) -> str:
    """Return first IPA string found in sounds list."""
    for s in sounds:
        if "ipa" in s:
            return s["ipa"]
    return ""


def _first_gloss(senses: list[dict]) -> str:
    """Return first gloss string from senses list."""
    for sense in senses:
        glosses = sense.get("glosses") or []
        for g in glosses:
            g = str(g).strip()
            if g:
                return g
    return ""


def parse_record(raw: dict) -> dict | None:
    """
    Convert a single Kaikki JSONL record into an LV0 record.
    Returns None if the record should be skipped (empty lemma, unknown lang_code).
    """
    lemma = str(raw.get("word") or "").strip()
    if not lemma:
        return None

    lang_code = str(raw.get("lang_code") or "").strip()
    if lang_code not in LANG_MAP:
        return None

    language, stage, script = LANG_MAP[lang_code]
    pos = str(raw.get("pos") or "").strip()
    ipa_raw = _pick_ipa(raw.get("sounds") or [])
    gloss_plain = _first_gloss(raw.get("senses") or [])
    etym = str(raw.get("etymology_text") or "").strip()

    rec: dict = {
        "lemma": lemma,
        "language": language,
        "stage": stage,
        "script": script,
        "source": "kaikki-wiktionary",
        "lemma_status": "attested",
        "pos": [pos] if pos else [],
        "ipa_raw": ipa_raw,
        "ipa": normalize_ipa(ipa_raw),
        "gloss_plain": gloss_plain,
        "translit": lemma,  # Latin-script: translit = lemma
    }
    if etym:
        rec["etymology_text"] = etym
    if gloss_plain:
        rec["meaning_text"] = gloss_plain

    # form_text: lemma + IPA if available
    ipa_norm = rec["ipa"]
    rec["form_text"] = f"{lemma} | IPA: {ipa_norm}" if ipa_norm else lemma

    return ensure_min_schema(rec)


def ingest_lines(lines: Iterator[str], out_path: Path) -> int:
    """
    Parse lines from a Kaikki JSONL source, write LV0 JSONL to out_path.
    Returns count of records written.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    seen: dict[str, int] = {}
    written = 0

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

            # Disambiguate duplicate IDs
            base_id = rec["id"]
            if base_id in seen:
                disambig = seen[base_id]
                seen[base_id] = disambig + 1
                rec["id"] = f"{base_id}:{disambig}"
            else:
                seen[base_id] = 1

            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1

    return written


def default_resources_dir() -> Path:
    env = os.environ.get("LC_RESOURCES_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / "Resources"


LANG_CODE_TO_FILE: dict[str, str] = {
    "grc": "ancient_greek/kaikki.org-dictionary-AncientGreek.jsonl",
    "la":  "latin/kaikki.org-dictionary-Latin.jsonl",
    "ang":  "english_old/kaikki.org-dictionary-OldEnglish.jsonl",
    "enm": "english_middle/kaikki.org-dictionary-MiddleEnglish.jsonl",
    "en":  "english_modern/kaikki.org-dictionary-English.jsonl",
}

LANG_CODE_TO_OUTPUT: dict[str, str] = {
    "grc": "data/processed/ancient_greek/sources/kaikki.jsonl",
    "la":  "data/processed/latin/classical/sources/kaikki.jsonl",
    "ang": "data/processed/english_old/sources/kaikki.jsonl",
    "enm": "data/processed/english_middle/sources/kaikki.jsonl",
    "en":  "data/processed/english_modern/sources/kaikki.jsonl",
}


def main() -> None:
    ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--lang-code", required=True, choices=list(LANG_MAP.keys()),
                    help="Kaikki lang_code to ingest")
    resources_dir = default_resources_dir()
    ap.add_argument(
        "--input", type=Path,
        default=None,
        help="Path to Kaikki JSONL. Defaults to Resources/<lang>/<file>",
    )
    ap.add_argument(
        "--output", type=Path,
        default=None,
        help="Output JSONL path. Defaults to data/processed/<lang>/sources/kaikki.jsonl",
    )
    ap.add_argument("--manifest", type=Path, default=None,
                    help="Manifest JSON path (defaults to <output>.manifest.json)")
    args = ap.parse_args()

    input_path = args.input or (resources_dir / LANG_CODE_TO_FILE[args.lang_code])
    repo_root = Path(__file__).resolve().parents[2]
    output_path = args.output or (repo_root / LANG_CODE_TO_OUTPUT[args.lang_code])
    manifest_path = args.manifest or output_path.with_suffix(".manifest.json")

    if not input_path.exists():
        raise SystemExit(f"Input not found: {input_path}")

    with input_path.open("r", encoding="utf-8", errors="replace") as fh:
        count = ingest_lines(fh, output_path)

    write_manifest(
        target=output_path,
        manifest_path=manifest_path,
        schema_version="lv0.7",
        generated_by=f"ingest_kaikki:lang_code={args.lang_code}",
        id_policy="lang:stage:source:normalized_lemma:pos:+disambig",
    )
    print(f"Wrote {count:,} records to {output_path}")


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

```
cd Juthoor-DataCore-LV0
pytest tests/test_ingest_kaikki.py -v
```
Expected: all 9 tests PASS

**Step 5: Commit**

```bash
git add scripts/ingest/ingest_kaikki.py tests/test_ingest_kaikki.py
git commit -m "feat(lv0): add Kaikki.org Wiktionary ingest adapter (lat/grc/ang/enm/en)"
```

---

### Task 2: Register Kaikki steps in runner.py

**Files:**
- Modify: `src/juthoor_datacore_lv0/ingest/runner.py:57-197` (inside `build_steps()`)

**Step 1: Open runner.py and locate `build_steps()`**

Find the `return [` line at the end of `build_steps()`. Add new steps **inside** that list, after the existing 8 steps.

**Step 2: Add the 5 Kaikki steps**

Append inside the `return [...]` list in `build_steps()`:

```python
        # ── Kaikki.org Wiktionary dumps ──────────────────────────────────
        *[
            Step(
                name=f"kaikki:{lang_code}",
                tags=frozenset({lang_tag}),
                cmd=[
                    python_exe,
                    str(scripts_dir / "ingest_kaikki.py"),
                    "--lang-code", lang_code,
                    "--output", str(data_processed / out_subpath),
                ],
                required_all_inputs=(resources_root / src_subpath,),
                outputs=(data_processed / out_subpath,),
            )
            for lang_code, lang_tag, src_subpath, out_subpath in [
                ("grc", "ancient_greek",
                 "ancient_greek/kaikki.org-dictionary-AncientGreek.jsonl",
                 "ancient_greek/sources/kaikki.jsonl"),
                ("la", "latin",
                 "latin/kaikki.org-dictionary-Latin.jsonl",
                 "latin/classical/sources/kaikki.jsonl"),
                ("ang", "english_old",
                 "english_old/kaikki.org-dictionary-OldEnglish.jsonl",
                 "english_old/sources/kaikki.jsonl"),
                ("enm", "english_middle",
                 "english_middle/kaikki.org-dictionary-MiddleEnglish.jsonl",
                 "english_middle/sources/kaikki.jsonl"),
                ("en", "english_modern",
                 "english_modern/kaikki.org-dictionary-English.jsonl",
                 "english_modern/sources/kaikki.jsonl"),
            ]
        ],
```

**Step 3: Run smoke test — list steps only**

```
cd Juthoor-DataCore-LV0
python -c "
import sys; sys.path.insert(0,'src')
from juthoor_datacore_lv0.ingest.runner import build_steps
from pathlib import Path
steps = build_steps(python_exe='python', repo_root=Path('.'), resources_dir=None)
for s in steps:
    print(s.name)
"
```
Expected output includes `kaikki:grc`, `kaikki:la`, `kaikki:ang`, `kaikki:enm`, `kaikki:en`

**Step 4: Commit**

```bash
git add src/juthoor_datacore_lv0/ingest/runner.py
git commit -m "feat(lv0): register Kaikki steps in ingest runner"
```

---

### Task 3: Arabic 10-dictionaries ingest script + tests

**Files:**
- Create: `scripts/ingest/ingest_arabic_ten_dicts.py`
- Create: `tests/test_ingest_ten_dicts.py`

**Step 1: Write the failing test**

Create `tests/test_ingest_ten_dicts.py`:

```python
"""Tests for ingest_arabic_ten_dicts.py — inline fixture data."""
from __future__ import annotations
import csv
import io
import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "ingest"))

from ingest_arabic_ten_dicts import parse_csv_row, ingest_csv_file, DICT_NAMES

# Simulate a CSV row (semicolon-delimited, BOM-prefixed header)
SAMPLE_HEADER = "\ufeffRoot;No of derevatives found;derevatives found;Root Length;Has Vowel;Full Text"
SAMPLE_ROW = 'أبن;4; الْإِبَّانُ إبَّانِهَا;3;vowel;"*أبن*\t تهيؤ الشيء واستعداده"'
EMPTY_ROOT_ROW = ';0;;0;no vowel;""'


def _make_reader(rows: list[str]):
    text = "\n".join(rows)
    return csv.reader(io.StringIO(text), delimiter=";")


def test_dict_names_not_empty():
    assert len(DICT_NAMES) > 0


def test_parse_valid_row():
    reader = _make_reader([SAMPLE_HEADER, SAMPLE_ROW])
    header = next(reader)
    row = next(reader)
    rec = parse_csv_row(row, header=header, source_name="AlMaghreb", row_num=1)
    assert rec is not None
    assert rec["lemma"] == "أبن"
    assert rec["language"] == "ara"
    assert rec["source"] == "arabic_ten_dicts:AlMaghreb"
    assert rec["lemma_status"] == "attested"
    assert "full_text" in rec
    assert rec["id"]


def test_parse_empty_root_returns_none():
    reader = _make_reader([SAMPLE_HEADER, EMPTY_ROOT_ROW])
    header = next(reader)
    row = next(reader)
    rec = parse_csv_row(row, header=header, source_name="AlMaghreb", row_num=2)
    assert rec is None


def test_ingest_csv_file_writes_jsonl(tmp_path):
    # Create a minimal CSV file
    csv_content = SAMPLE_HEADER + "\n" + SAMPLE_ROW + "\n"
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(csv_content, encoding="utf-8")
    out_file = tmp_path / "out.jsonl"

    count = ingest_csv_file(csv_file, out_file, source_name="AlMaghreb")
    assert count == 1
    rec = json.loads(out_file.read_text(encoding="utf-8").strip())
    assert rec["lemma"] == "أبن"


def test_form_text_populated():
    reader = _make_reader([SAMPLE_HEADER, SAMPLE_ROW])
    header = next(reader)
    row = next(reader)
    rec = parse_csv_row(row, header=header, source_name="AlMaghreb", row_num=1)
    assert rec.get("form_text"), "form_text must be set"
    assert "أبن" in rec["form_text"]
```

**Step 2: Run test to verify it fails**

```
cd Juthoor-DataCore-LV0
pytest tests/test_ingest_ten_dicts.py -v
```
Expected: `ModuleNotFoundError: No module named 'ingest_arabic_ten_dicts'`

**Step 3: Write `scripts/ingest/ingest_arabic_ten_dicts.py`**

```python
"""
Ingest the 10 classical Arabic dictionaries (semicolon-delimited CSVs).

Each CSV has: Root;No of derevatives found;derevatives found;Root Length;Has Vowel;Full Text
Files are BOM-prefixed UTF-8, semicolon-separated.

Usage:
    python ingest_arabic_ten_dicts.py --input-dir <Resources/Ten dictionaries for Arabic language> --output <out.jsonl>
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

from processed_schema import ensure_min_schema

try:
    from ingest.utils import write_manifest
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from juthoor_datacore_lv0.ingest.utils import write_manifest

# Known dictionary file stems (without .csv) → display name
DICT_NAMES: dict[str, str] = {
    "AlMaghreb": "Al-Maghreb",
    "AlMesbah": "Al-Mesbah",
    "Alsehah1": "Al-Sehah-1",
    "Alsehah2": "Al-Sehah-2",
    "Alsehah3": "Al-Sehah-3",
    "Alsehah4": "Al-Sehah-4",
    "Alsehah5": "Al-Sehah-5",
    "Alsehah6": "Al-Sehah-6",
    "Alsehah7": "Al-Sehah-7",
    "Alsehah8": "Al-Sehah-8",
    "almuheet_1": "Al-Muheet-1",
    "almuheet_2": "Al-Muheet-2",
}

_HEADER_COLS = ["root", "n_derivatives", "derivatives", "root_length", "has_vowel", "full_text"]


def _normalize_header(raw_header: list[str]) -> list[str]:
    """Map raw CSV header columns to internal names."""
    # Strip BOM and lowercase
    cols = [c.lstrip("\ufeff").strip().lower() for c in raw_header]
    mapping = {
        "root": "root",
        "no of derevatives found": "n_derivatives",
        "derevatives found": "derivatives",
        "root length": "root_length",
        "has vowel": "has_vowel",
        "full text": "full_text",
    }
    return [mapping.get(c, c) for c in cols]


def parse_csv_row(
    row: list[str],
    *,
    header: list[str],
    source_name: str,
    row_num: int,
) -> dict | None:
    """Convert a single CSV row into an LV0 record. Returns None to skip."""
    norm_header = _normalize_header(header)
    fields: dict[str, str] = {}
    for i, col in enumerate(norm_header):
        fields[col] = row[i].strip() if i < len(row) else ""

    root = fields.get("root", "").strip()
    if not root:
        return None

    full_text = fields.get("full_text", "").strip().strip('"')

    rec: dict = {
        "lemma": root,
        "root": root,
        "language": "ara",
        "stage": "classical",
        "script": "Arab",
        "source": f"arabic_ten_dicts:{source_name}",
        "source_ref": f"arabic_ten_dicts:{source_name}:row:{row_num}",
        "lemma_status": "attested",
        "full_text": full_text,
        "n_derivatives": fields.get("n_derivatives", ""),
        "derivatives": fields.get("derivatives", ""),
    }

    # form_text: Arabic script root only (no gloss in form_text per schema)
    rec["form_text"] = f"AR: {root}"

    # meaning_text: full dictionary text is too long; use derivatives list as proxy
    derivatives = fields.get("derivatives", "").strip()
    if derivatives:
        rec["meaning_text"] = derivatives

    return ensure_min_schema(rec)


def ingest_csv_file(csv_path: Path, out_path: Path, *, source_name: str) -> int:
    """Ingest one CSV dictionary file. Returns row count written."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    seen: dict[str, int] = {}

    with (
        csv_path.open("r", encoding="utf-8-sig", errors="replace") as fh,
        out_path.open("w", encoding="utf-8") as out_f,
    ):
        reader = csv.reader(fh, delimiter=";")
        header = next(reader, None)
        if header is None:
            return 0
        for row_num, row in enumerate(reader, start=1):
            rec = parse_csv_row(row, header=header, source_name=source_name, row_num=row_num)
            if rec is None:
                continue
            # Disambiguate IDs
            base_id = rec["id"]
            if base_id in seen:
                disambig = seen[base_id]
                seen[base_id] = disambig + 1
                rec["id"] = f"{base_id}:{disambig}"
            else:
                seen[base_id] = 1
            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1

    return written


def default_input_dir() -> Path:
    env = os.environ.get("LC_RESOURCES_DIR")
    if env:
        return Path(env) / "Ten dictionaries for Arabic language"
    return Path(__file__).resolve().parents[2] / "Resources" / "Ten dictionaries for Arabic language"


def main() -> None:
    ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--input-dir", type=Path, default=default_input_dir(),
                    help="Folder containing the 10 dictionary CSV files")
    ap.add_argument("--output", type=Path,
                    default=Path("data/processed/arabic/classical/sources/ten_dicts.jsonl"))
    ap.add_argument("--manifest", type=Path, default=None)
    args = ap.parse_args()

    if not args.input_dir.exists():
        raise SystemExit(f"Input directory not found: {args.input_dir}")

    manifest_path = args.manifest or args.output.with_suffix(".manifest.json")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    csv_files = sorted(args.input_dir.glob("*.csv"))
    if not csv_files:
        raise SystemExit(f"No CSV files found in {args.input_dir}")

    # Write all sources merged into one output file
    seen_ids: dict[str, int] = {}
    with args.output.open("w", encoding="utf-8") as out_f:
        for csv_path in csv_files:
            source_name = csv_path.stem
            with csv_path.open("r", encoding="utf-8-sig", errors="replace") as fh:
                reader = csv.reader(fh, delimiter=";")
                header = next(reader, None)
                if header is None:
                    continue
                for row_num, row in enumerate(reader, start=1):
                    rec = parse_csv_row(row, header=header, source_name=source_name, row_num=row_num)
                    if rec is None:
                        continue
                    base_id = rec["id"]
                    if base_id in seen_ids:
                        disambig = seen_ids[base_id]
                        seen_ids[base_id] = disambig + 1
                        rec["id"] = f"{base_id}:{disambig}"
                    else:
                        seen_ids[base_id] = 1
                    out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    total += 1
            print(f"  {csv_path.name}: done")

    write_manifest(
        target=args.output,
        manifest_path=manifest_path,
        schema_version="lv0.7",
        generated_by="ingest_arabic_ten_dicts",
        id_policy="lang:stage:source:normalized_lemma:pos:+disambig",
    )
    print(f"Total: wrote {total:,} records to {args.output}")


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

```
cd Juthoor-DataCore-LV0
pytest tests/test_ingest_ten_dicts.py -v
```
Expected: all 5 tests PASS

**Step 5: Commit**

```bash
git add scripts/ingest/ingest_arabic_ten_dicts.py tests/test_ingest_ten_dicts.py
git commit -m "feat(lv0): add Arabic 10-dictionaries ingest adapter"
```

---

### Task 4: Register ten-dicts step in runner.py

**Files:**
- Modify: `src/juthoor_datacore_lv0/ingest/runner.py`

**Step 1: Add step inside `build_steps()` return list**

After the Kaikki steps added in Task 2, append:

```python
        # ── Arabic: 10 classical dictionaries ────────────────────────────
        Step(
            name="arabic:ingest_ten_dicts",
            tags=frozenset({"arabic"}),
            cmd=[
                python_exe,
                str(scripts_dir / "ingest_arabic_ten_dicts.py"),
                "--input-dir",
                str(
                    (resources_root / "Ten dictionaries for Arabic language")
                    if resources_dir is not None
                    else (repo_root / "Resources" / "Ten dictionaries for Arabic language")
                ),
                "--output",
                str(arabic_sources / "ten_dicts.jsonl"),
            ],
            required_all_inputs=(
                (resources_root / "Ten dictionaries for Arabic language")
                if resources_dir is not None
                else (repo_root / "Resources" / "Ten dictionaries for Arabic language"),
            ),
            outputs=(arabic_sources / "ten_dicts.jsonl",),
        ),
```

**Step 2: Smoke-test step listing**

```
python -c "
import sys; sys.path.insert(0,'src')
from juthoor_datacore_lv0.ingest.runner import build_steps
from pathlib import Path
steps = build_steps(python_exe='python', repo_root=Path('.'), resources_dir=None)
names = [s.name for s in steps]
assert 'arabic:ingest_ten_dicts' in names
print('OK:', [n for n in names if 'ten_dicts' in n or 'kaikki' in n])
"
```

**Step 3: Commit**

```bash
git add src/juthoor_datacore_lv0/ingest/runner.py
git commit -m "feat(lv0): register Arabic 10-dicts step in runner"
```

---

### Task 5: Add form_text/meaning_text post-process steps in runner.py

The `build_text_fields.py` module already exists at `src/juthoor_datacore_lv0/features/build_text_fields.py` and has a `__main__` entry that accepts `input.jsonl output.jsonl --overwrite`.

**Files:**
- Modify: `src/juthoor_datacore_lv0/ingest/runner.py`

**Step 1: Add text-field enrichment steps for all new outputs**

Add these steps after the ingest steps in `build_steps()`. They write enriched JSONL to a sibling `_enriched.jsonl` file, then the final lexemes merge step can use those.

The pattern: run `python -m juthoor_datacore_lv0.features.build_text_fields <input> <output> --overwrite`

```python
        # ── Text-field enrichment (form_text + meaning_text) ─────────────
        *[
            Step(
                name=f"text_fields:{lang_tag}",
                tags=frozenset({lang_tag, "text_fields"}),
                cmd=[
                    python_exe, "-m", "juthoor_datacore_lv0.features.build_text_fields",
                    str(data_processed / src_subpath),
                    str(data_processed / src_subpath),  # in-place (overwrite)
                    "--overwrite",
                ],
                required_all_inputs=(data_processed / src_subpath,),
                outputs=(data_processed / src_subpath,),
            )
            for lang_tag, src_subpath in [
                ("ancient_greek",   "ancient_greek/sources/kaikki.jsonl"),
                ("latin",           "latin/classical/sources/kaikki.jsonl"),
                ("english_old",     "english_old/sources/kaikki.jsonl"),
                ("english_middle",  "english_middle/sources/kaikki.jsonl"),
                ("english_modern",  "english_modern/sources/kaikki.jsonl"),
                ("arabic",          "arabic/classical/sources/ten_dicts.jsonl"),
            ]
        ],
```

**Step 2: Smoke-test step listing**

```
python -c "
import sys; sys.path.insert(0,'src')
from juthoor_datacore_lv0.ingest.runner import build_steps
from pathlib import Path
steps = build_steps(python_exe='python', repo_root=Path('.'), resources_dir=None)
tf = [s.name for s in steps if 'text_fields' in s.name]
print('text_field steps:', tf)
assert len(tf) == 6
"
```

**Step 3: Commit**

```bash
git add src/juthoor_datacore_lv0/ingest/runner.py
git commit -m "feat(lv0): add text-field enrichment steps for all new ingest outputs"
```

---

### Task 6: Run the full pipeline and verify outputs

**Step 1: Run existing Arabic + Quranic steps (fast, already working)**

```
cd Juthoor-DataCore-LV0
python src/juthoor_datacore_lv0/cli.py ingest --tags arabic,quranic_arabic --skip-missing-inputs
```
Expected: exits 0, existing processed files unchanged.

**Step 2: Run new Kaikki steps for small languages first (grc, ang, enm)**

```
cd Juthoor-DataCore-LV0
python scripts/ingest/ingest_kaikki.py --lang-code grc
python scripts/ingest/ingest_kaikki.py --lang-code ang
python scripts/ingest/ingest_kaikki.py --lang-code enm
```
Expected: 3 JSONL files created in `data/processed/`. Print row counts.

**Step 3: Run Latin (large ~1 GB, may take a few minutes)**

```
python scripts/ingest/ingest_kaikki.py --lang-code la
```

**Step 4: Run 10-dicts Arabic**

```
python scripts/ingest/ingest_arabic_ten_dicts.py
```
Expected: `data/processed/arabic/classical/sources/ten_dicts.jsonl` created.

**Step 5: Verify output counts**

```python
python -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
files = [
    'data/processed/ancient_greek/sources/kaikki.jsonl',
    'data/processed/latin/classical/sources/kaikki.jsonl',
    'data/processed/english_old/sources/kaikki.jsonl',
    'data/processed/english_middle/sources/kaikki.jsonl',
    'data/processed/arabic/classical/sources/ten_dicts.jsonl',
]
for f in files:
    p = Path(f)
    if p.exists():
        count = sum(1 for l in p.open(encoding='utf-8') if l.strip())
        print(f'{f}: {count:,} rows')
    else:
        print(f'{f}: MISSING')
"
```

**Step 6: Spot-check form_text/meaning_text coverage**

```python
python -c "
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
p = Path('data/processed/latin/classical/sources/kaikki.jsonl')
total = has_form = has_meaning = 0
with p.open(encoding='utf-8') as f:
    for line in f:
        if not line.strip(): continue
        r = json.loads(line)
        total += 1
        if r.get('form_text'): has_form += 1
        if r.get('meaning_text'): has_meaning += 1
print(f'Latin: {total:,} total, {has_form:,} form_text, {has_meaning:,} meaning_text')
"
```
Expected: form_text ~100%, meaning_text ~90%+ (some records have no gloss)

**Step 7: Skip Modern English for now (2.7 GB — flag as deferred)**

Modern English (`kaikki.org-dictionary-English.jsonl` = 2.7 GB) will work with the same script but takes significant time. Run it as a separate manual step:
```
python scripts/ingest/ingest_kaikki.py --lang-code en
```

**Step 8: Commit**

```bash
git add data/processed/
git commit -m "data(lv0): add processed JSONL for grc, lat, ang, enm, arabic-10dicts"
```

---

## Summary of New Files

| File | Purpose |
|------|---------|
| `scripts/ingest/ingest_kaikki.py` | Ingest any Kaikki.org language dump |
| `scripts/ingest/ingest_arabic_ten_dicts.py` | Ingest 10 classical Arabic dictionary CSVs |
| `tests/test_ingest_kaikki.py` | Unit tests for Kaikki adapter |
| `tests/test_ingest_ten_dicts.py` | Unit tests for 10-dicts adapter |
| `src/.../ingest/runner.py` (modified) | 12 new steps registered |

## New processed outputs

| Path | Language | Source |
|------|----------|--------|
| `data/processed/ancient_greek/sources/kaikki.jsonl` | Ancient Greek | Kaikki/Wiktionary |
| `data/processed/latin/classical/sources/kaikki.jsonl` | Latin | Kaikki/Wiktionary |
| `data/processed/english_old/sources/kaikki.jsonl` | Old English | Kaikki/Wiktionary |
| `data/processed/english_middle/sources/kaikki.jsonl` | Middle English | Kaikki/Wiktionary |
| `data/processed/arabic/classical/sources/ten_dicts.jsonl` | Classical Arabic | 10 dictionaries |
