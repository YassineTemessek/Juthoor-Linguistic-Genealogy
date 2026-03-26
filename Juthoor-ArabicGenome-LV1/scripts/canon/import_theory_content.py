# ACTIVE: maintained CLI wrapper around `core.canon_import.ingest_from_inbox`, with dedicated tests.
from __future__ import annotations

import argparse
import json
from pathlib import Path

from juthoor_arabicgenome_lv1.core.canon_import import ingest_from_inbox


def main() -> int:
    parser = argparse.ArgumentParser(description="Import curated theory content from the canon inbox.")
    parser.add_argument("--inbox-root", type=Path, default=None)
    parser.add_argument("--registry-root", type=Path, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    report = ingest_from_inbox(
        inbox_root=args.inbox_root,
        registry_root=args.registry_root,
        force=args.force,
        dry_run=args.dry_run,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
