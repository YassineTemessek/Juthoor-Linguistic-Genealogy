from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.append(str(SRC_ROOT))

from juthoor_cognatediscovery_lv2.discovery.benchmarking import (  # noqa: E402
    build_root_family_benchmark_source,
    read_jsonl,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-subset", type=Path, required=True)
    parser.add_argument("--root-family-corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_rows = read_jsonl(args.source_subset)
    root_family_rows = read_jsonl(args.root_family_corpus)
    materialized = build_root_family_benchmark_source(source_rows, root_family_rows)
    write_jsonl(args.output, materialized)
    payload = {
        "source_rows": len(source_rows),
        "root_family_rows": len(root_family_rows),
        "materialized_rows": len(materialized),
        "output": str(args.output.resolve()),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
