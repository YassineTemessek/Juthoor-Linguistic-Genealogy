from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LV2_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = LV2_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.append(str(SRC_ROOT))

from juthoor_cognatediscovery_lv2.discovery.precomputed_assets import build_reverse_root_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a reverse English-skeleton -> Arabic-root index.")
    parser.add_argument(
        "--input",
        type=Path,
        default=LV2_ROOT / "outputs" / "corpora" / "arabic_root_families.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=LV2_ROOT / "data" / "processed" / "reverse_arabic_root_index.json",
    )
    args = parser.parse_args()

    summary = build_reverse_root_index(args.input, args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
