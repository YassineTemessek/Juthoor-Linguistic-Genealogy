from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LV2_ROOT = REPO_ROOT / "Juthoor-CognateDiscovery-LV2"
SRC_ROOT = LV2_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.append(str(SRC_ROOT))

from juthoor_cognatediscovery_lv2.discovery.precomputed_assets import build_historical_english_lookup


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an English historical-meaning lookup from Beyond-the-Name + Old/Middle English.")
    parser.add_argument(
        "--beyond-csv",
        type=Path,
        default=LV2_ROOT / "data" / "processed" / "beyond_name_etymology_pairs.csv",
    )
    parser.add_argument(
        "--old-english",
        type=Path,
        default=REPO_ROOT / "Juthoor-DataCore-LV0" / "data" / "processed" / "english_old" / "sources" / "kaikki.jsonl",
    )
    parser.add_argument(
        "--middle-english",
        type=Path,
        default=REPO_ROOT / "Juthoor-DataCore-LV0" / "data" / "processed" / "english_middle" / "sources" / "kaikki.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=LV2_ROOT / "data" / "processed" / "english" / "english_historical_meanings.jsonl",
    )
    args = parser.parse_args()

    summary = build_historical_english_lookup(
        args.beyond_csv,
        args.old_english,
        args.middle_english,
        args.output,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
