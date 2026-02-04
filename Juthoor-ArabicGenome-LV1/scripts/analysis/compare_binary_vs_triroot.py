"""
Compare Arabic tri-root grouping vs binary-root grouping (LV2 QA).

Input:
  - data/processed/arabic/<stage>/lexemes.jsonl

Output:
  - outputs/qa/binary_vs_triroot_report.json
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def main() -> None:
    ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--input", type=Path, default=Path("data/processed/arabic/classical/lexemes.jsonl"))
    ap.add_argument("--output", type=Path, default=Path("outputs/qa/binary_vs_triroot_report.json"))
    args = ap.parse_args()

    tri_to_bin: dict[str, set[str]] = defaultdict(set)
    bin_to_tri: dict[str, set[str]] = defaultdict(set)
    rows = 0
    for rec in iter_jsonl(args.input):
        rows += 1
        root = str(rec.get("root_norm") or rec.get("root") or "").strip()
        binary_root = str(rec.get("binary_root") or "").strip()
        if not root or not binary_root:
            continue
        tri_to_bin[root].add(binary_root)
        bin_to_tri[binary_root].add(root)

    tri_single = sum(1 for k, v in tri_to_bin.items() if len(v) == 1)
    tri_multi = sum(1 for k, v in tri_to_bin.items() if len(v) > 1)
    bin_single = sum(1 for k, v in bin_to_tri.items() if len(v) == 1)
    bin_multi = sum(1 for k, v in bin_to_tri.items() if len(v) > 1)

    payload = {
        "input": str(args.input),
        "rows_scanned": rows,
        "tri_roots_total": len(tri_to_bin),
        "tri_roots_single_binary": tri_single,
        "tri_roots_multiple_binary": tri_multi,
        "binary_roots_total": len(bin_to_tri),
        "binary_roots_single_tri": bin_single,
        "binary_roots_multiple_tri": bin_multi,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
