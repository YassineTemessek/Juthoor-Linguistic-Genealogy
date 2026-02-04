import argparse
import sys
from pathlib import Path
from typing import List, Tuple

import pandas as pd

# Robust console output for Arabic
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def parse_patterns(spec: str) -> List[Tuple[str, List[str]]]:
    """
    Parse pattern spec like "رح:رحم,رجع:رجع,رجم:رجم|مرجوم,خرج:خرج".
    Returns list of (label, substrings).
    """
    pairs = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            raise ValueError(f"Bad pattern entry '{part}'. Expected label:sub|sub2.")
        label, subs = part.split(":", 1)
        subs_list = [s.strip() for s in subs.split("|") if s.strip()]
        if not subs_list:
            raise ValueError(f"No substrings provided for label '{label}'.")
        pairs.append((label.strip(), subs_list))
    return pairs


def build_subset(df: pd.DataFrame, text_col: str, patterns: List[Tuple[str, List[str]]]) -> pd.DataFrame:
    rows = []
    seen = set()
    for idx, row in df.iterrows():
        text = str(row[text_col])
        dedupe_id = row.get("id", idx)
        for label, subs in patterns:
            for sub in subs:
                if sub and sub in text:
                    key = (dedupe_id, label)
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append(
                        {
                            "sura": row.get("surah_no", row.get("sura", "")),
                            "ayah": row.get("ayah_no", row.get("ayah", "")),
                            "word_form": sub,
                            "root2": label,
                            "root3": label,
                            "text_ayah": text,
                            "id": dedupe_id,
                        }
                    )
                    break  # avoid duplicate subs for same label on this row
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Create a verse subset by substring patterns for quick clustering samples."
    )
    parser.add_argument(
        "--input",
        default=Path("..") / "Resources" / "quran_text.csv",
        help="Path to full Quran CSV.",
    )
    parser.add_argument(
        "--output",
        default=Path("..") / "Resources" / "examples_rj.csv",
        help="Where to write the subset CSV.",
    )
    parser.add_argument(
        "--patterns",
        default="رجع:رجع|يرجع,رجم:رجم|مرجوم,رحم:رحم|رحمه|رحمت,خرج:خرج|يخرج|مخرج",
        help="Comma-separated label:substr|substr2 list.",
    )
    parser.add_argument(
        "--text-column",
        default="text_clean",
        help="Which column to search for substrings (default text_clean).",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    if args.text_column not in df.columns:
        raise ValueError(f"Column '{args.text_column}' not found in {args.input}")
    patterns = parse_patterns(args.patterns)
    subset = build_subset(df, args.text_column, patterns)
    subset.to_csv(args.output, index=False)
    print(f"[info] wrote {len(subset)} rows to {args.output}")
    for label, _ in patterns:
        count = (subset["root2"] == label).sum()
        print(f"  {label}: {count} rows")


if __name__ == "__main__":
    main()
