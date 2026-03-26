"""
diagnose_coverage_gap.py
Investigates WHY ~989 Muajam roots are absent from the LV1 genome.

Categories diagnosed:
  1. compound_entry      – tri_root contains '/' or '-' (multiple roots merged)
  2. heh_tatweel         – contains U+0640 ARABIC TATWEEL (rendering artefact for هـ)
  3. bracket_entry       – contains '[' or ']' (editorial notes in tri_root field)
  4. normalization_diff  – hamza/diacritic variant; genome has equivalent stripped form
  5. root_length_mismatch – extracted root (after stripping separators) != 3 letters
  6. genuinely_missing   – no match in genome even after all normalisation attempts

For categories 4+ a fuzzy pass (Levenshtein distance 1-2) is also run against genome
3-letter roots to catch near-misses.

Outputs:
  outputs/reports/coverage_gap_diagnosis.json
"""

import sys
import json
import pathlib
import re
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE        = pathlib.Path(__file__).resolve().parent.parent  # Juthoor-ArabicGenome-LV1/
MUAJAM_FILE = BASE / "data" / "muajam" / "roots.jsonl"
GENOME_DIR  = BASE / "outputs" / "genome"
REPORTS_DIR = BASE / "outputs" / "reports"
REPORT_FILE = REPORTS_DIR / "coverage_gap_diagnosis.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HAMZA_MAP = {
    "\u0623": "\u0627",  # alef with hamza above  -> plain alef
    "\u0625": "\u0627",  # alef with hamza below  -> plain alef
    "\u0622": "\u0627",  # alef with madda        -> plain alef
    "\u0621": "\u0627",  # standalone hamza        -> plain alef
    "\u0626": "\u064A",  # ya with hamza           -> ya
    "\u0624": "\u0648",  # waw with hamza          -> waw
}

DIACRITIC_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")  # harakat + tatweel


def normalize(text: str) -> str:
    """Strip diacritics/tatweel and normalise all hamza variants."""
    text = DIACRITIC_RE.sub("", text)
    for src, dst in HAMZA_MAP.items():
        text = text.replace(src, dst)
    return text


def levenshtein(a: str, b: str) -> int:
    """Pure-stdlib Levenshtein distance (Wagner-Fischer)."""
    if a == b:
        return 0
    m, n = len(a), len(b)
    if m < n:
        a, b, m, n = b, a, n, m
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        curr = [i] + [0] * n
        for j in range(1, n + 1):
            curr[j] = min(
                prev[j] + 1,           # deletion
                curr[j - 1] + 1,       # insertion
                prev[j - 1] + (0 if a[i - 1] == b[j - 1] else 1),  # substitution
            )
        prev = curr
    return prev[n]


def is_arabic_char(c: str) -> bool:
    return "\u0600" <= c <= "\u06FF"


def extract_primary_root(tri_root: str) -> str:
    """
    Return the first token from a compound tri_root field.
    Splits on '/', '-', and whitespace; strips editorial brackets.
    """
    token = re.split(r"[/\-\s]", tri_root)[0]
    token = token.replace("[", "").replace("]", "")
    return DIACRITIC_RE.sub("", token)  # strip diacritics only, keep hamza for now


def arabic_letter_count(s: str) -> int:
    return sum(1 for c in s if is_arabic_char(c))


# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
print("Loading Muajam roots …")
muajam_entries: list[dict] = []
with open(MUAJAM_FILE, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            muajam_entries.append(json.loads(line))

muajam_roots: set[str] = {e["tri_root"] for e in muajam_entries}

print("Loading genome roots …")
genome_roots: set[str] = set()
for gf in sorted(GENOME_DIR.glob("*.jsonl")):
    with open(gf, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                genome_roots.add(json.loads(line).get("root", ""))

genome_roots.discard("")

print(f"  Muajam  : {len(muajam_roots):,} roots")
print(f"  Genome  : {len(genome_roots):,} roots")

# ---------------------------------------------------------------------------
# 2. Identify unmatched roots
# ---------------------------------------------------------------------------
unmatched_raw: set[str] = muajam_roots - genome_roots
print(f"  Unmatched (exact): {len(unmatched_raw):,}")

# Pre-build normalised genome index (norm -> original genome root)
norm_genome_index: dict[str, str] = {}
for gr in genome_roots:
    nk = normalize(gr)
    if nk not in norm_genome_index:
        norm_genome_index[nk] = gr  # keep first; could be multiple

# Genome 3-letter roots for fuzzy pass
genome_3 = [r for r in genome_roots if len(r) == 3 and all(is_arabic_char(c) for c in r)]
print(f"  Genome 3-letter roots for fuzzy: {len(genome_3):,}")

# ---------------------------------------------------------------------------
# 3. Categorise each unmatched root
# ---------------------------------------------------------------------------
categories: dict[str, list[dict]] = defaultdict(list)
TATWEEL = "\u0640"

for tri in sorted(unmatched_raw):
    entry: dict = {
        "tri_root": tri,
        "primary_root": extract_primary_root(tri),
        "fuzzy_candidates": [],
    }

    # --- Category A: compound entry (slash or hyphen) ---
    if "/" in tri or "-" in tri:
        entry["reason"] = "compound_entry"
        # Check if the primary root alone matches
        prim = extract_primary_root(tri)
        if prim in genome_roots:
            entry["primary_found_exact"] = True
        elif normalize(prim) in norm_genome_index:
            entry["primary_found_norm"] = True
            entry["genome_match"] = norm_genome_index[normalize(prim)]
        else:
            entry["primary_found_exact"] = False
        categories["compound_entry"].append(entry)
        continue

    # --- Category B: heh + tatweel artefact ---
    if TATWEEL in tri:
        # Strip tatweel and retry
        stripped = tri.replace(TATWEEL, "")
        entry["stripped_form"] = stripped
        if stripped in genome_roots:
            entry["genome_match"] = stripped
            entry["reason"] = "heh_tatweel"
        elif normalize(stripped) in norm_genome_index:
            entry["genome_match"] = norm_genome_index[normalize(stripped)]
            entry["reason"] = "heh_tatweel"
        else:
            entry["reason"] = "heh_tatweel"
        categories["heh_tatweel"].append(entry)
        continue

    # --- Category C: bracket entry ---
    if "[" in tri or "]" in tri:
        entry["reason"] = "bracket_entry"
        categories["bracket_entry"].append(entry)
        continue

    # --- Category D: normalization difference (hamza/diacritic) ---
    norm_key = normalize(tri)
    if norm_key in norm_genome_index:
        entry["reason"] = "normalization_diff"
        entry["genome_match"] = norm_genome_index[norm_key]
        entry["norm_form"] = norm_key
        # Identify what changed
        if tri != norm_key:
            changed = []
            if any(c in tri for c in HAMZA_MAP):
                changed.append("hamza_variant")
            if re.search(r"[\u064B-\u065F\u0670]", tri):
                changed.append("diacritic")
            entry["normalization_types"] = changed
        categories["normalization_diff"].append(entry)
        continue

    # --- Category E: root length mismatch ---
    prim = extract_primary_root(tri)
    arabic_len = arabic_letter_count(prim)
    if arabic_len != 3:
        entry["reason"] = "root_length_mismatch"
        entry["arabic_letter_count"] = arabic_len
        entry["primary_root"] = prim
        # Try normalised too
        if normalize(prim) in norm_genome_index:
            entry["genome_match"] = norm_genome_index[normalize(prim)]
        categories["root_length_mismatch"].append(entry)
        continue

    # --- Category F: genuinely missing – fuzzy pass ---
    norm_tri = normalize(tri)
    fuzzy_hits = []
    for gr in genome_3:
        d = levenshtein(norm_tri, normalize(gr))
        if d <= 2:
            fuzzy_hits.append({"genome_root": gr, "distance": d})
    fuzzy_hits.sort(key=lambda x: x["distance"])
    entry["fuzzy_candidates"] = fuzzy_hits[:5]

    if fuzzy_hits and fuzzy_hits[0]["distance"] == 1:
        entry["reason"] = "fuzzy_near_miss_d1"
        categories["fuzzy_near_miss_d1"].append(entry)
    elif fuzzy_hits and fuzzy_hits[0]["distance"] == 2:
        entry["reason"] = "fuzzy_near_miss_d2"
        categories["fuzzy_near_miss_d2"].append(entry)
    else:
        entry["reason"] = "genuinely_missing"
        categories["genuinely_missing"].append(entry)

# ---------------------------------------------------------------------------
# 4. Build summary
# ---------------------------------------------------------------------------
total_unmatched = len(unmatched_raw)

summary: dict = {
    "muajam_total": len(muajam_roots),
    "genome_total": len(genome_roots),
    "original_matched": len(muajam_roots) - total_unmatched,
    "original_matched_pct": round((len(muajam_roots) - total_unmatched) / len(muajam_roots) * 100, 1),
    "total_unmatched": total_unmatched,
    "category_counts": {k: len(v) for k, v in categories.items()},
    "potential_coverage_after_normalization": 0,
    "category_details": {},
}

# How many could be recovered by normalisation / compound splitting?
recoverable = (
    len(categories.get("normalization_diff", []))
    + len(categories.get("heh_tatweel", []))
    + sum(
        1 for e in categories.get("compound_entry", [])
        if e.get("primary_found_exact") or e.get("primary_found_norm") or e.get("genome_match")
    )
)
summary["recoverable_by_normalization"] = recoverable
summary["potential_coverage_after_normalization"] = round(
    (summary["original_matched"] + recoverable) / len(muajam_roots) * 100, 1
)

# Per-category detail lists (truncate large lists to 50 entries for readability)
for cat, entries in categories.items():
    summary["category_details"][cat] = entries[:50]

# ---------------------------------------------------------------------------
# 5. Write report
# ---------------------------------------------------------------------------
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
with open(REPORT_FILE, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(f"\nReport written -> {REPORT_FILE}")

# ---------------------------------------------------------------------------
# 6. Human-readable stdout summary
# ---------------------------------------------------------------------------
print()
print("=" * 65)
print("  Muajam Coverage Gap Diagnosis")
print("=" * 65)
print(f"  Muajam total roots              : {summary['muajam_total']:>6,}")
print(f"  Genome total roots              : {summary['genome_total']:>6,}")
print(f"  Originally matched (exact)      : {summary['original_matched']:>6,}  ({summary['original_matched_pct']}%)")
print(f"  Unmatched                       : {summary['total_unmatched']:>6,}")
print()
print("  Breakdown of unmatched roots:")
print(f"    compound_entry (/ or -)       : {len(categories.get('compound_entry', [])):>6,}")
print(f"    heh_tatweel artefact          : {len(categories.get('heh_tatweel', [])):>6,}")
print(f"    bracket_entry                 : {len(categories.get('bracket_entry', [])):>6,}")
print(f"    normalization_diff (hamza/dia): {len(categories.get('normalization_diff', [])):>6,}")
print(f"    root_length_mismatch          : {len(categories.get('root_length_mismatch', [])):>6,}")
print(f"    fuzzy_near_miss d=1           : {len(categories.get('fuzzy_near_miss_d1', [])):>6,}")
print(f"    fuzzy_near_miss d=2           : {len(categories.get('fuzzy_near_miss_d2', [])):>6,}")
print(f"    genuinely_missing             : {len(categories.get('genuinely_missing', [])):>6,}")
print()
print(f"  Recoverable by normalisation    : {summary['recoverable_by_normalization']:>6,}")
print(f"  Potential coverage if fixed     : {summary['potential_coverage_after_normalization']}%")
print("=" * 65)

# Show a few examples from each category
SHOW = 5
for cat, entries in sorted(categories.items(), key=lambda x: -len(x[1])):
    if not entries:
        continue
    print(f"\n  [{cat}]  ({len(entries)} roots)  – first {min(SHOW, len(entries))} examples:")
    for e in entries[:SHOW]:
        tri = e["tri_root"]
        gm = e.get("genome_match", "")
        fc = e.get("fuzzy_candidates", [])
        if gm:
            print(f"    {tri}  ->  genome: {gm}")
        elif fc:
            top = fc[0]
            print(f"    {tri}  ->  fuzzy d={top['distance']}: {top['genome_root']}")
        else:
            print(f"    {tri}")

print()
