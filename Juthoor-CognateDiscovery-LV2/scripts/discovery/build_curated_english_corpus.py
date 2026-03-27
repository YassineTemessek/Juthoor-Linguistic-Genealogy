from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LV2_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = LV2_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.append(str(SRC_ROOT))

from juthoor_cognatediscovery_lv2.discovery.precomputed_assets import curate_english_corpus


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a discovery-optimized curated English IPA corpus.")
    parser.add_argument(
        "--input",
        type=Path,
        default=LV2_ROOT / "data" / "processed" / "english" / "english_ipa_merged_pos.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=LV2_ROOT / "data" / "processed" / "english" / "english_ipa_curated_10k.jsonl",
    )
    parser.add_argument("--max-entries", type=int, default=10_000)
    args = parser.parse_args()

    summary = curate_english_corpus(args.input, args.output, max_entries=args.max_entries)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
