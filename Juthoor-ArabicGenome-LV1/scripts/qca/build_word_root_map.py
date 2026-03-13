import argparse
import csv
from pathlib import Path

"""
Build a word→root map from the Quranic Arabic Corpus morphology dump (quran-morphology.txt).
Output columns: sura, ayah, position, word, lemma, root.
Notes: the morphology file is colon-delimited for the ID (sura:ayah:word:segment) and tab-delimited for columns.
"""


def parse_features(raw: str) -> dict:
    """Parse pipe-delimited features into a dict (ROOT:xxx, LEM:xxx, etc.)."""
    feats = {}
    for part in raw.split("|"):
        if ":" in part:
            k, v = part.split(":", 1)
            feats[k] = v
    return feats


def build_map(morph_path: Path, out_path: Path) -> None:
    rows = []
    current = {}
    with morph_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Format: sura:ayah:word:segment\tTOKEN\tFEATS
            try:
                id_part, token, feats_part = line.split("\t", 2)
            except ValueError:
                # Skip malformed lines but keep track if needed
                continue
            sura, ayah, word_idx, _segment = id_part.split(":")
            key = (sura, ayah, word_idx)
            feats = parse_features(feats_part)
            root = feats.get("ROOT")
            lemma = feats.get("LEM")

            if key not in current:
                # seed new word
                current[key] = {
                    "sura": int(sura),
                    "ayah": int(ayah),
                    "position": int(word_idx),
                    "word": token,
                    "lemma": lemma,
                    "root": root,
                }
            else:
                # update if we find a ROOT/LEM later in the segments
                if root and not current[key].get("root"):
                    current[key]["root"] = root
                if lemma and not current[key].get("lemma"):
                    current[key]["lemma"] = lemma
                # prefer a token that has a root tag
                if root:
                    current[key]["word"] = token

            # When we finish segments for a word, we flush on next new word
            # But simpler: flush when key changes
            # (done after loop by gathering values)

    rows = list(current.values())
    rows.sort(key=lambda r: (r["sura"], r["ayah"], r["position"]))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=["sura", "ayah", "position", "word", "lemma", "root"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"[saved] {out_path} ({len(rows)} rows)")


def main():
    parser = argparse.ArgumentParser(description="Build word_root_map.csv from quran-morphology.txt")
    parser.add_argument(
        "--morph",
        default=Path("..") / "Resources" / "qac_morphology" / "quran-morphology.txt",
        help="Path to quran-morphology.txt",
    )
    parser.add_argument(
        "--output",
        default=Path("..") / "Resources" / "word_root_map.csv",
        help="Output CSV path",
    )
    args = parser.parse_args()
    build_map(Path(args.morph), Path(args.output))


if __name__ == "__main__":
    main()
