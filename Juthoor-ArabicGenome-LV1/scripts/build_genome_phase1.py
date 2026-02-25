"""
LV1 Arabic Genome — Phase 1: Brute word list

Groups LV0 Arabic lexemes by: BAB (first letter of root) → binary_root → root_norm → unique lemmas.

Output: outputs/genome/<bab_letter>.jsonl  (one file per BAB letter)
Each line: {"bab": "ب", "binary_root": "بب", "root": "بوب", "words": ["باب", "بوّاب"]}

Usage:
    python scripts/build_genome_phase1.py
    python scripts/build_genome_phase1.py --input <path> --output-dir <dir>
"""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path


def default_input() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "Juthoor-DataCore-LV0" / "data" / "processed" / "arabic" / "classical" / "lexemes.jsonl"


def build_genome(input_path: Path, output_dir: Path) -> dict[str, int]:
    """
    Read LV0 Arabic lexemes, group into genome structure, write per-BAB JSONL files.
    Returns dict: bab_letter -> count of root entries written.
    """
    # Structure: bab -> binary_root -> root_norm -> set of lemmas
    genome: dict[str, dict[str, dict[str, set[str]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(set))
    )

    skipped = 0
    total = 0

    with input_path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            root_norm = str(rec.get("root_norm") or rec.get("root") or "").strip()
            if not root_norm:
                skipped += 1
                continue

            binary_root = str(rec.get("binary_root") or "").strip()
            if not binary_root:
                # derive from first 2 chars of root_norm
                binary_root = root_norm[:2] if len(root_norm) >= 2 else root_norm

            bab = root_norm[0]
            lemma = str(rec.get("lemma") or "").strip()
            if not lemma:
                skipped += 1
                continue

            genome[bab][binary_root][root_norm].add(lemma)
            total += 1

    output_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}

    for bab in sorted(genome.keys()):
        out_path = output_dir / f"{bab}.jsonl"
        binary_roots = genome[bab]
        written = 0

        with out_path.open("w", encoding="utf-8") as out_f:
            for binary_root in sorted(binary_roots.keys()):
                roots = binary_roots[binary_root]
                for root in sorted(roots.keys()):
                    words = sorted(roots[root])
                    rec = {
                        "bab": bab,
                        "binary_root": binary_root,
                        "root": root,
                        "words": words,
                    }
                    out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    written += 1

        counts[bab] = written

    print(f"Read {total:,} lemmas, skipped {skipped:,} (no root/lemma)")
    return counts


def main() -> None:
    import sys
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--input", type=Path, default=default_input())
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/genome"))
    args = ap.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input not found: {args.input}")

    counts = build_genome(args.input, args.output_dir)

    total_roots = sum(counts.values())
    print(f"\nWrote {len(counts)} BAB files, {total_roots:,} root entries total:")
    for bab, count in sorted(counts.items()):
        out_path = args.output_dir / f"{bab}.jsonl"
        print(f"  {bab}.jsonl  ->  {count} roots  ({out_path})")


if __name__ == "__main__":
    main()
