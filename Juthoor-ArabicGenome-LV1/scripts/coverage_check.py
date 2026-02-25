"""
coverage_check.py
Cross-references Muajam roots (data/muajam/roots.jsonl) with
Phase 1 genome word lists (outputs/genome/*.jsonl).

Writes a JSON report to outputs/reports/muajam_coverage.json
and prints a human-readable summary to stdout.

Normalization applied to both sides before matching:
  - Strip Arabic diacritics (harakat, shadda, etc.)
  - Strip tatweel (U+0640)
  - Normalize hamza variants: أ إ آ ٱ → ا, ى → ي, ؤ → و, ئ → ي, ة → ه
  - Compound entries (containing / or -) are split and each part checked
"""

import sys
import re
import json
import pathlib

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
# Normalization helpers
# ---------------------------------------------------------------------------
_AR_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")  # harakat + tatweel
_AR_ROOT_NORM_MAP = str.maketrans(
    {
        "\u0623": "\u0627",  # أ → ا
        "\u0625": "\u0627",  # إ → ا
        "\u0622": "\u0627",  # آ → ا
        "\u0671": "\u0627",  # ٱ → ا
        "\u0649": "\u064a",  # ى → ي
        "\u0624": "\u0648",  # ؤ → و
        "\u0626": "\u064a",  # ئ → ي
        "\u0629": "\u0647",  # ة → ه
    }
)


def normalize_root(root: str) -> str:
    """Normalize an Arabic root for comparison matching."""
    root = (root or "").strip()
    if not root:
        return ""
    root = _AR_DIACRITICS_RE.sub("", root)   # strip diacritics + tatweel (U+0640)
    root = root.translate(_AR_ROOT_NORM_MAP)  # normalize hamza/letter variants
    return root


def expand_muajam_root(tri: str) -> list[str]:
    """
    Expand a raw Muajam tri_root into one or more normalized lookup keys.
    Handles compound entries joined by / or - by checking each part.
    """
    tri = tri.strip()
    if not tri:
        return []
    # Split on / or - for compound entries
    parts = re.split(r"[/\-]", tri)
    keys = []
    for p in parts:
        n = normalize_root(p)
        if n:
            keys.append(n)
    return keys


# ---------------------------------------------------------------------------
# 1. Load Muajam roots
# ---------------------------------------------------------------------------
print("Loading Muajam roots …")
muajam_raw: list[str] = []        # original tri_root strings
muajam_key_to_raw: dict[str, str] = {}  # normalized_key -> original tri_root

with open(MUAJAM_FILE, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        tri = entry.get("tri_root", "").strip()
        if not tri:
            continue
        muajam_raw.append(tri)
        for key in expand_muajam_root(tri):
            muajam_key_to_raw.setdefault(key, tri)

muajam_total = len(muajam_raw)
muajam_norm_keys: set[str] = set(muajam_key_to_raw.keys())
print(f"  Muajam roots loaded        : {muajam_total}")
print(f"  Muajam normalized keys     : {len(muajam_norm_keys)} (after expansion+normalization)")

# ---------------------------------------------------------------------------
# 2. Load Phase 1 genome roots
# ---------------------------------------------------------------------------
print("Loading Phase 1 genome roots …")
genome_norm_to_words: dict[str, list[str]] = {}

genome_files = sorted(GENOME_DIR.glob("*.jsonl"))
print(f"  Genome files found         : {len(genome_files)}")

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
                key = normalize_root(root)
                if key in genome_norm_to_words:
                    genome_norm_to_words[key].extend(words)
                else:
                    genome_norm_to_words[key] = list(words)

genome_norm_keys = set(genome_norm_to_words.keys())
genome_total_raw = sum(1 for gf in genome_files for line in open(gf, encoding="utf-8") if line.strip())
genome_total = len(genome_norm_keys)
print(f"  Genome unique norm. roots  : {genome_total}")

# ---------------------------------------------------------------------------
# 3. Compute coverage statistics
# ---------------------------------------------------------------------------
matched_norm_keys  = muajam_norm_keys & genome_norm_keys
unmatched_norm_keys = muajam_norm_keys - genome_norm_keys

# Recover original tri_roots for matched/unmatched reporting
matched_tri_roots = sorted({muajam_key_to_raw[k] for k in matched_norm_keys})
unmatched_tri_roots = sorted({muajam_key_to_raw[k] for k in unmatched_norm_keys})

# Deduplicate: a raw tri_root is matched if ANY of its expansion keys matched
raw_matched = set(matched_tri_roots)
raw_unmatched = set(muajam_raw) - raw_matched

matched      = len(raw_matched)
matched_pct  = round(matched / muajam_total * 100, 1) if muajam_total else 0.0
muajam_unmatched_count = len(raw_unmatched)
genome_only_count = len(genome_norm_keys - muajam_norm_keys)

# Average words per matched norm key
if matched_norm_keys:
    total_words = sum(len(genome_norm_to_words[k]) for k in matched_norm_keys)
    avg_words = round(total_words / len(matched_norm_keys), 1)
else:
    avg_words = 0.0

# Full sorted list of unmatched Muajam roots (all of them, not just a sample)
unmatched_roots_list = sorted(raw_unmatched)

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
    "normalization": "hamza+tatweel+compound_split",
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
print("  (with hamza, tatweel, compound normalization)")
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
