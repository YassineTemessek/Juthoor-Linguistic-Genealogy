"""
One-off post-process fix: strip ال prefix from arabic_root field in Eye 1 output.

Background:
  Eye 1 output stored the ORIGINAL unnormalized Arabic root (with ال) instead
  of the normalized form. This breaks Eye 2 lookups and dashboard display.
  The skeleton and Jaccard fields were already computed from the normalized
  form, so only the displayed `arabic_root` field is inconsistent.

This script:
  1. Reads each line of the target .jsonl file
  2. Strips ال from `arabic_root` if present (len >= 4)
  3. Writes to a .fixed temp file
  4. Atomically replaces the original

Also patches `arabic_root_original` with the pre-fix value so we keep history.

Usage:
    python scripts/fix_alif_lam_prefix.py  # fixes both grc and lat
    python scripts/fix_alif_lam_prefix.py --dry-run  # just reports counts
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Force UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


LV2_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = LV2_ROOT / "outputs"

TARGETS = [
    OUTPUTS / "eye1_full_scale_grc.jsonl",
    OUTPUTS / "eye1_full_scale_lat.jsonl",
]


def _strip_alif_lam(root: str) -> str:
    """Strip ال prefix if present and remaining root has at least 2 letters."""
    if root.startswith("ال") and len(root) >= 4:
        return root[2:]
    return root


def process_file(path: Path, dry_run: bool = False) -> dict:
    """Process one Eye 1 output file. Returns before/after stats."""
    if not path.exists():
        return {"file": str(path), "error": "not_found"}

    tmp_path = path.with_suffix(path.suffix + ".fixed")

    total_lines = 0
    changed_lines = 0
    roots_before: set[str] = set()
    roots_after: set[str] = set()

    writer = None
    if not dry_run:
        writer = open(tmp_path, "w", encoding="utf-8")

    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                total_lines += 1
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    if writer:
                        writer.write(line)
                    continue

                original_root = obj.get("arabic_root", "")
                roots_before.add(original_root)

                fixed_root = _strip_alif_lam(original_root)
                if fixed_root != original_root:
                    changed_lines += 1
                    obj["arabic_root"] = fixed_root
                    # Keep the original for traceability
                    if "arabic_root_original" not in obj:
                        obj["arabic_root_original"] = original_root

                roots_after.add(obj["arabic_root"])

                if writer:
                    writer.write(json.dumps(obj, ensure_ascii=False) + "\n")

                if total_lines % 500000 == 0:
                    print(
                        f"  [{path.name}] processed {total_lines:,} lines...",
                        file=sys.stderr,
                    )
    finally:
        if writer:
            writer.close()

    stats = {
        "file": path.name,
        "total_lines": total_lines,
        "changed_lines": changed_lines,
        "unique_roots_before": len(roots_before),
        "unique_roots_after": len(roots_after),
        "roots_with_al_before": sum(1 for r in roots_before if r.startswith("ال")),
        "roots_with_al_after": sum(1 for r in roots_after if r.startswith("ال")),
    }

    if not dry_run and writer is not None:
        # Atomic replace
        os.replace(tmp_path, path)
        stats["status"] = "replaced"
    else:
        stats["status"] = "dry_run"
        if tmp_path.exists():
            tmp_path.unlink()

    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report counts without modifying files",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Process a single file instead of defaults",
    )
    args = parser.parse_args()

    targets = [args.file] if args.file else TARGETS

    print("=" * 70, file=sys.stderr)
    print("Fix ال prefix in Eye 1 output", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    if args.dry_run:
        print("DRY RUN MODE — no files will be modified", file=sys.stderr)
    print(file=sys.stderr)

    all_stats = []
    for target in targets:
        print(f"Processing {target.name}...", file=sys.stderr)
        stats = process_file(target, dry_run=args.dry_run)
        all_stats.append(stats)
        print(json.dumps(stats, ensure_ascii=False, indent=2), file=sys.stderr)
        print(file=sys.stderr)

    # Summary
    print("=" * 70, file=sys.stderr)
    print("SUMMARY", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    for s in all_stats:
        if "error" in s:
            print(f"  {s['file']}: {s['error']}", file=sys.stderr)
            continue
        print(
            f"  {s['file']}: "
            f"{s['changed_lines']:,}/{s['total_lines']:,} lines fixed, "
            f"ال roots: {s['roots_with_al_before']} → {s['roots_with_al_after']}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
