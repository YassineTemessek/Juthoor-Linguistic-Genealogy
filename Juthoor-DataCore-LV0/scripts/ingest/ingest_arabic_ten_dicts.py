"""
Ingest Arabic roots from the "Ten dictionaries for Arabic language" CSV dataset.

Each CSV file is semicolon-delimited, BOM-prefixed UTF-8 with columns:
  Root;No of derevatives found;derevatives found;Root Length;Has Vowel;Full Text

Output: data/processed/arabic/classical/sources/ten_dicts.jsonl

If you keep datasets outside the repo, set `LC_RESOURCES_DIR` to point at that
folder and the default input will become:
  %LC_RESOURCES_DIR%/Ten dictionaries for Arabic language/
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

from processed_schema import ensure_min_schema

# Try to import write_manifest from the installed package; fall back to adding src/ to path.
try:
    from ingest.utils import write_manifest
except ImportError:
    _src = Path(__file__).resolve().parents[2] / "src"
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))
    from juthoor_datacore_lv0.ingest.utils import write_manifest  # type: ignore[no-redef]


# ---------------------------------------------------------------------------
# Dictionary name mapping (CSV stem -> display name)
# ---------------------------------------------------------------------------

DICT_NAMES: dict[str, str] = {
    "AlMaghreb": "Al-Maghreb Dictionary",
    "AlMesbah": "Al-Mesbah Al-Muneer",
    "Alsehah1": "Al-Sehah (Vol. 1)",
    "Alsehah2": "Al-Sehah (Vol. 2)",
    "Alsehah3": "Al-Sehah (Vol. 3)",
    "Alsehah4": "Al-Sehah (Vol. 4)",
    "Alsehah5": "Al-Sehah (Vol. 5)",
    "Alsehah6": "Al-Sehah (Vol. 6)",
    "Alsehah7": "Al-Sehah (Vol. 7)",
    "Alsehah8": "Al-Sehah (Vol. 8)",
    "almuheet_1": "Al-Muheet (Vol. 1)",
    "almuheet_2": "Al-Muheet (Vol. 2)",
}

# Internal column key constants
_COL_ROOT = "root"
_COL_N_DERIVATIVES = "n_derivatives"
_COL_DERIVATIVES = "derivatives"
_COL_ROOT_LENGTH = "root_length"
_COL_HAS_VOWEL = "has_vowel"
_COL_FULL_TEXT = "full_text"

# Map raw (lowercased, BOM-stripped) header names to internal keys
_HEADER_MAP: dict[str, str] = {
    "root": _COL_ROOT,
    "no of derevatives found": _COL_N_DERIVATIVES,
    "derevatives found": _COL_DERIVATIVES,
    "root length": _COL_ROOT_LENGTH,
    "has vowel": _COL_HAS_VOWEL,
    "full text": _COL_FULL_TEXT,
}


# ---------------------------------------------------------------------------
# Header normalization
# ---------------------------------------------------------------------------

def _normalize_header(raw_header: list[str]) -> list[str]:
    """Strip BOM and map raw column names to internal keys."""
    result = []
    for i, col in enumerate(raw_header):
        # Strip BOM from first column if present
        if i == 0:
            col = col.lstrip("\ufeff")
        normalized = _HEADER_MAP.get(col.strip().lower(), col.strip().lower())
        result.append(normalized)
    return result


# ---------------------------------------------------------------------------
# Row parsing
# ---------------------------------------------------------------------------

def parse_csv_row(
    row: list[str],
    *,
    header: list[str],
    source_name: str,
    row_num: int,
) -> dict | None:
    """Parse a single CSV data row into an LV0 canonical dict.

    Returns None if the root field is empty.
    """
    # Build a dict from header keys -> cell values
    cell = {key: (row[i].strip() if i < len(row) else "") for i, key in enumerate(header)}

    root = cell.get(_COL_ROOT, "").strip()
    if not root:
        return None

    derivatives = cell.get(_COL_DERIVATIVES, "").strip()
    full_text = cell.get(_COL_FULL_TEXT, "").strip()
    n_derivatives = cell.get(_COL_N_DERIVATIVES, "").strip()

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
        "n_derivatives": n_derivatives,
        "derivatives": derivatives,
        # form_text: form only, no gloss — schema rule
        "form_text": f"AR: {root}",
    }

    # meaning_text: derived from the derivatives field (contains classical Arabic text)
    if derivatives:
        rec["meaning_text"] = derivatives

    ensure_min_schema(rec)
    return rec


# ---------------------------------------------------------------------------
# File-level ingest
# ---------------------------------------------------------------------------

def ingest_csv_file(csv_path: Path, out_path: Path, *, source_name: str) -> int:
    """Ingest one CSV file, write JSONL, disambiguate colliding IDs.

    Returns the number of rows written.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    seen_ids: dict[str, int] = {}
    count = 0

    with (
        csv_path.open("r", encoding="utf-8-sig", newline="") as in_f,
        out_path.open("w", encoding="utf-8") as out_f,
    ):
        reader = csv.reader(in_f, delimiter=";")
        raw_header = next(reader, None)
        if raw_header is None:
            return 0
        header = _normalize_header(raw_header)

        for row_num, row in enumerate(reader, start=1):
            rec = parse_csv_row(row, header=header, source_name=source_name, row_num=row_num)
            if rec is None:
                continue

            # Disambiguate duplicate IDs by appending a collision counter suffix
            base_id = rec["id"]
            if base_id in seen_ids:
                seen_ids[base_id] += 1
                rec["id"] = f"{base_id}:{seen_ids[base_id]}"
            else:
                seen_ids[base_id] = 0

            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count += 1

    return count


# ---------------------------------------------------------------------------
# Default path helpers
# ---------------------------------------------------------------------------

def _default_input_dir() -> Path:
    resources_dir = os.environ.get("LC_RESOURCES_DIR")
    if resources_dir:
        return Path(resources_dir) / "Ten dictionaries for Arabic language"
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "Resources" / "Ten dictionaries for Arabic language"


def _default_output_path() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "data" / "processed" / "arabic" / "classical" / "sources" / "ten_dicts.jsonl"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Ingest Ten Arabic Dictionaries CSV dataset into LV0 canonical JSONL.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument(
        "--input-dir",
        type=Path,
        default=_default_input_dir(),
        help="Directory containing *.csv files from the Ten Dictionaries dataset.",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=_default_output_path(),
        help="Output JSONL path.",
    )
    ap.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Optional manifest JSON path to write after ingest.",
    )
    args = ap.parse_args()

    input_dir: Path = args.input_dir
    out_path: Path = args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(input_dir.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in {input_dir}")
        return

    total = 0
    # Write all rows into a single merged output file
    with out_path.open("w", encoding="utf-8") as merged_f:
        seen_ids: dict[str, int] = {}

        for csv_path in csv_files:
            stem = csv_path.stem
            source_name = stem  # use stem directly; DICT_NAMES is for display only

            file_count = 0
            with csv_path.open("r", encoding="utf-8-sig", newline="") as in_f:
                reader = csv.reader(in_f, delimiter=";")
                raw_header = next(reader, None)
                if raw_header is None:
                    continue
                header = _normalize_header(raw_header)

                for row_num, row in enumerate(reader, start=1):
                    rec = parse_csv_row(row, header=header, source_name=source_name, row_num=row_num)
                    if rec is None:
                        continue

                    # Global ID disambiguation across all files
                    base_id = rec["id"]
                    if base_id in seen_ids:
                        seen_ids[base_id] += 1
                        rec["id"] = f"{base_id}:{seen_ids[base_id]}"
                    else:
                        seen_ids[base_id] = 0

                    merged_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    file_count += 1

            display = DICT_NAMES.get(stem, stem)
            print(f"  {display} ({stem}): {file_count} rows")
            total += file_count

    print(f"\nTotal: {total} records written to {out_path}")

    if args.manifest:
        payload = write_manifest(
            target=out_path,
            manifest_path=args.manifest,
            schema_version="LV0.7",
            generated_by="ingest_arabic_ten_dicts",
        )
        print(f"Manifest written to {args.manifest} (sha256={payload['sha256'][:12]}...)")


if __name__ == "__main__":
    main()
