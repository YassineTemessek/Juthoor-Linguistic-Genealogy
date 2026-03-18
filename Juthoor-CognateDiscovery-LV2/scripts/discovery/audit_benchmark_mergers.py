from __future__ import annotations

import argparse
import json
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.benchmark_audit import audit_benchmark_files


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit LV2 benchmark files for merger-sensitive risks.")
    parser.add_argument("--benchmark", action="append", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    report = audit_benchmark_files(args.benchmark)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
