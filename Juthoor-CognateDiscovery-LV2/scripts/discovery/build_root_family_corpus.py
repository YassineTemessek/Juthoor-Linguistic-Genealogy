from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.append(str(SRC_ROOT))

from juthoor_cognatediscovery_lv2.discovery.root_families import build_root_family_corpus


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a discovery-ready LV2 root-family corpus from LV1 genome_v2 JSONL files.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=REPO_ROOT.parent / "Juthoor-ArabicGenome-LV1" / "outputs" / "genome_v2",
        help="Directory containing LV1 genome_v2 BAB JSONL files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "outputs" / "corpora" / "arabic_root_families.jsonl",
        help="Output JSONL path for the root-family corpus.",
    )
    parser.add_argument("--lang", default="ara")
    parser.add_argument("--stage", default="classical")
    args = parser.parse_args()

    count = build_root_family_corpus(args.input_dir, args.output, lang=args.lang, stage=args.stage)
    print(f"Wrote {count} root-family rows to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
