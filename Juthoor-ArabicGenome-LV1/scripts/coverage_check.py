"""
coverage_check.py
Cross-references Muajam roots (data/muajam/roots.jsonl) with
Phase 1 genome word lists (outputs/genome/*.jsonl).

Writes a JSON report to outputs/reports/muajam_coverage.json
and prints a human-readable summary to stdout.
"""

import sys
import json
import pathlib
from glob import glob

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Paths (relative to repo root of LV1)
# ---------------------------------------------------------------------------
BASE = pathlib.Path(__file__).resolve().parent.parent  # Juthoor-ArabicGenome-LV1/
MUAJAM_FILE = BASE / "data" / "muajam" / "roots.jsonl"
GENOME_DIR  = BASE / "outputs" / "genome"
REPORTS_DIR = BASE / "outputs" / "reports"
REPORT_FILE = REPORTS_DIR / "muajam_coverage.json"

# ---------------------------------------------------------------------------
# 1. Load Muajam roots
# ---------------------------------------------------------------------------
print("Loading Muajam roots …")
muajam_roots: set[str] = set()
with open(MUAJAM_FILE, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        tri = entry.get("tri_root", "").strip()
        if tri:
            muajam_roots.add(tri)

muajam_total = len(muajam_roots)
print(f"  Muajam roots loaded : {muajam_total}")

# ---------------------------------------------------------------------------
# 2. Load Phase 1 genome roots
# ---------------------------------------------------------------------------
print("Loading Phase 1 genome roots …")
genome_root_to_words: dict[str, list[str]] = {}

genome_files = sorted(GENOME_DIR.glob("*.jsonl"))
print(f"  Genome files found  : {len(genome_files)}")

for gf in genome_files:
    with open(gf, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            root  = entry.get("root", "").strip()
            words = entry.get("words", [])
            if root:
                # If root appears in multiple files keep union of words
                if root in genome_root_to_words:
                    genome_root_to_words[root].extend(words)
                else:
                    genome_root_to_words[root] = list(words)

genome_roots = set(genome_root_to_words.keys())
genome_total = len(genome_roots)
print(f"  Genome roots loaded : {genome_total}")

# ---------------------------------------------------------------------------
# 3. Compute coverage statistics
# ---------------------------------------------------------------------------
matched_roots  = muajam_roots & genome_roots
unmatched_muajam = muajam_roots - genome_roots   # in Muajam, not in genome
genome_only    = genome_roots - muajam_roots      # in genome, not in Muajam

matched      = len(matched_roots)
matched_pct  = round(matched / muajam_total * 100, 1) if muajam_total else 0.0
muajam_unmatched_count = len(unmatched_muajam)
genome_only_count = len(genome_only)

# Average words per matched root
if matched:
    total_words = sum(len(genome_root_to_words[r]) for r in matched_roots)
    avg_words = round(total_words / matched, 1)
else:
    avg_words = 0.0

# Full sorted list of unmatched Muajam roots (all of them, not just a sample)
unmatched_roots_list = sorted(unmatched_muajam)

# ---------------------------------------------------------------------------
# 4. Write JSON report
# ---------------------------------------------------------------------------
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

report = {
    "muajam_total":               muajam_total,
    "genome_total":               genome_total,
    "matched":                    matched,
    "matched_pct":                matched_pct,
    "muajam_unmatched":           muajam_unmatched_count,
    "genome_only":                genome_only_count,
    "avg_words_per_matched_root": avg_words,
    "unmatched_roots_sample":     unmatched_roots_list,
}

with open(REPORT_FILE, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"\nReport written → {REPORT_FILE}")

# ---------------------------------------------------------------------------
# 5. Human-readable summary
# ---------------------------------------------------------------------------
print()
print("=" * 55)
print("  Muajam x Phase-1 Genome  —  Coverage Report")
print("=" * 55)
print(f"  Muajam total roots          : {muajam_total:>6,}")
print(f"  Genome total roots          : {genome_total:>6,}")
print(f"  Matched (Muajam ∩ Genome)   : {matched:>6,}  ({matched_pct}%)")
print(f"  Muajam roots NOT in genome  : {muajam_unmatched_count:>6,}")
print(f"  Genome roots NOT in Muajam  : {genome_only_count:>6,}")
print(f"  Avg words / matched root    : {avg_words:>6}")
print("=" * 55)
if unmatched_roots_list:
    preview = unmatched_roots_list[:20]
    print(f"\n  First 20 unmatched Muajam roots:")
    for r in preview:
        print(f"    {r}")
    if muajam_unmatched_count > 20:
        print(f"    … and {muajam_unmatched_count - 20} more (see full list in report JSON)")
print()
