import argparse
from pathlib import Path
from typing import List, Set

import pandas as pd

import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def parse_roots(spec: str) -> List[str]:
    roots = [r.strip() for r in spec.split(",") if r.strip()]
    if not roots:
        raise ValueError("No roots provided. Use --roots \"???,???\"")
    return roots


def load_word_root_map(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"sura", "ayah", "root"}
    if not required.issubset(df.columns):
        raise ValueError(f"word_root_map is missing required columns {required}")
    return df


def load_quran_text(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Accept common column names
    text_cols = [c for c in ("text_with_diacritics", "text_clean", "text") if c in df.columns]
    if not text_cols:
        raise ValueError("quran_text is missing text columns (text_with_diacritics/text_clean/text).")
    return df


def _normalize_quran_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "sura" not in df.columns and "surah_no" in df.columns:
        df["sura"] = df["surah_no"]
    if "ayah" not in df.columns and "ayah_no" in df.columns:
        df["ayah"] = df["ayah_no"]
    return df


def build_examples(
    word_root_map: pd.DataFrame, quran_text: pd.DataFrame, roots: Set[str], drop_duplicates: bool
) -> pd.DataFrame:
    df_sel = word_root_map.copy()
    df_sel = _normalize_quran_cols(df_sel)
    df_sel = df_sel[df_sel["root"].isin(roots)]
    # keep first occurrence per sura/ayah if requested
    if drop_duplicates:
        df_sel = df_sel.drop_duplicates(subset=["sura", "ayah", "root"])

    # join text
    text_cols = [c for c in ("text_with_diacritics", "text_clean", "text") if c in quran_text.columns]
    join_cols = ["sura", "ayah"]
    quran_text = _normalize_quran_cols(quran_text)
    df_join = quran_text[join_cols + text_cols]
    merged = df_sel.merge(df_join, on=join_cols, how="left")

    # rename a canonical text column for downstream scripts
    if "text_with_diacritics" in merged.columns:
        merged["text_ayah"] = merged["text_with_diacritics"]
    elif "text_clean" in merged.columns:
        merged["text_ayah"] = merged["text_clean"]
    elif "text" in merged.columns:
        merged["text_ayah"] = merged["text"]

    merged = merged.rename(columns={"root": "root3"})
    merged["root2"] = merged["root3"]  # placeholder; Level 2 can overwrite
    cols_order = ["sura", "ayah", "position", "word", "lemma", "root2", "root3", "text_ayah"]
    # keep existing cols if present
    existing = [c for c in cols_order if c in merged.columns]
    tail = [c for c in merged.columns if c not in existing]
    merged = merged[existing + tail]
    return merged


def main():
    parser = argparse.ArgumentParser(
        description="Create root-based verse examples from word_root_map + quran_text (no substring matching)."
    )
    parser.add_argument(
        "--word-root-map",
        default=Path("..") / "Resources" / "word_root_map.csv",
        help="CSV with sura, ayah, position, word, lemma, root.",
    )
    parser.add_argument(
        "--quran-text",
        default=Path("..") / "Resources" / "quran_dataset including CSV" / "quran_text.csv",
        help="CSV with sura/ayah and text columns.",
    )
    parser.add_argument(
        "--roots",
        required=True,
        help="Comma-separated roots to extract (e.g., \"???,???,???\").",
    )
    parser.add_argument(
        "--drop-duplicates",
        action="store_true",
        help="Keep only one row per sura/ayah/root (dedupe multiple occurrences in same verse).",
    )
    parser.add_argument(
        "--output",
        default=Path("output") / "examples_roots.csv",
        help="Where to write the examples CSV.",
    )
    args = parser.parse_args()

    roots = set(parse_roots(args.roots))
    df_map = load_word_root_map(Path(args.word_root_map))
    df_quran = load_quran_text(Path(args.quran_text))

    out_df = build_examples(df_map, df_quran, roots, drop_duplicates=args.drop_duplicates)
    args_output = Path(args.output)
    args_output.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(args_output, index=False)
    print(f"[saved] {args_output} with {len(out_df)} rows for roots: {', '.join(sorted(roots))}")


if __name__ == "__main__":
    main()
