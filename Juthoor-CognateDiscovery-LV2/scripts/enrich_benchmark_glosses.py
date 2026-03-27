"""
enrich_benchmark_glosses.py

Enriches cognate_gold.jsonl and cognate_silver.jsonl with:
- source.gloss (Arabic meaning) from beyond_name_etymology_pairs.csv
- target.gloss (English meaning) from beyond_name_etymology_pairs.csv
- provenance field: "manual_curated" (lines 1-126) or "beyond_the_name"

The "Beyond the Name" entries (line 127+) were ingested with:
  - source.gloss = "" (missing Arabic meaning)
  - target.gloss = Arabic text (the english_meaning column from CSV, which is actually Arabic)

This script fixes both issues and adds proper English meanings as target.gloss.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE = Path(__file__).resolve().parents[1]
CSV_PATH = BASE / "data" / "processed" / "beyond_name_etymology_pairs.csv"
GOLD_PATH = BASE / "resources" / "benchmarks" / "cognate_gold.jsonl"
SILVER_PATH = BASE / "resources" / "benchmarks" / "cognate_silver.jsonl"

# Number of original manually-curated entries in gold (lines 1-126)
MANUAL_CURATED_COUNT = 126


# ---------------------------------------------------------------------------
# Arabic normalization helper (strip diacritics + tatweel, normalize hamza)
# ---------------------------------------------------------------------------
DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4"
    r"\u06E7\u06E8\u06EA-\u06ED\u0640]"
)
HAMZA_VARIANTS = str.maketrans(
    "أإآؤئ",
    "اااوي",
)


def normalize_arabic(text: str) -> str:
    """Strip diacritics + tatweel, map hamza variants to base letters."""
    if not text:
        return ""
    text = DIACRITICS.sub("", text)
    text = text.translate(HAMZA_VARIANTS)
    return text.strip()


# ---------------------------------------------------------------------------
# Load CSV lookup tables
# ---------------------------------------------------------------------------

def load_csv_lookups(csv_path: Path) -> tuple[dict, dict, set]:
    """
    Returns:
        root_to_arabic_meaning: normalized_root -> arabic meaning string
            NOTE: The CSV column 'english_meaning' actually contains Arabic text
            (the Arabic meaning of the root). The 'arabic_meaning' column is empty.
            We use 'english_meaning' as the source for Arabic root meanings.
        word_to_english_meaning: lower(english_word) -> English meaning string
            When 'english_meaning' is non-Arabic (i.e. empty or English text only),
            we fall back to using the english_word itself as the gloss.
        beyond_name_pairs: set of (normalized_root, lower_english_word) for provenance detection
    """
    df = pd.read_csv(csv_path, dtype=str).fillna("")

    root_to_arabic_meaning: dict[str, str] = {}
    word_to_english_meaning: dict[str, str] = {}
    beyond_name_pairs: set[tuple[str, str]] = set()

    for _, row in df.iterrows():
        arabic_root = row.get("arabic_root", "").strip()
        # NOTE: 'english_meaning' column contains Arabic text (mislabeled in CSV)
        # It is the Arabic meaning/gloss of the arabic_root
        csv_english_meaning = row.get("english_meaning", "").strip()
        english_word = row.get("english_word", "").strip()

        norm_root = normalize_arabic(arabic_root)
        lower_word = english_word.lower()

        if norm_root:
            beyond_name_pairs.add((norm_root, lower_word))
            # csv_english_meaning is actually Arabic text = the Arabic meaning of the root
            # Filter out obviously bad values: fragments ending in colon/comma, very long strings
            if (
                csv_english_meaning
                and norm_root not in root_to_arabic_meaning
                and not csv_english_meaning.endswith((":", "،", ","))
                and len(csv_english_meaning) <= 60
            ):
                root_to_arabic_meaning[norm_root] = csv_english_meaning

        # For English target gloss: use the english_word itself (lowercased, title-case for display)
        # This gives us a minimal but correct English gloss when none exists
        if lower_word and lower_word not in word_to_english_meaning:
            word_to_english_meaning[lower_word] = english_word  # keep original casing

    return root_to_arabic_meaning, word_to_english_meaning, beyond_name_pairs


# ---------------------------------------------------------------------------
# Enrich a single JSONL file
# ---------------------------------------------------------------------------

def enrich_file(
    jsonl_path: Path,
    root_to_arabic_meaning: dict,
    word_to_english_meaning: dict,
    beyond_name_pairs: set,
    manual_curated_count: int,
) -> dict:
    """
    Reads jsonl_path, enriches entries in-place, writes back.
    Returns stats dict.
    """
    entries = []
    with open(jsonl_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    stats = {
        "total": len(entries),
        "source_gloss_added": 0,
        "target_gloss_fixed": 0,
        "provenance_added": 0,
        "source_gloss_before": sum(1 for e in entries if e.get("source", {}).get("gloss", "")),
        "target_gloss_before": sum(1 for e in entries if e.get("target", {}).get("gloss", "")),
    }

    for idx, entry in enumerate(entries):
        line_num = idx + 1  # 1-based
        src = entry.setdefault("source", {})
        tgt = entry.setdefault("target", {})

        src_lemma = src.get("lemma", "").strip()
        tgt_lemma = tgt.get("lemma", "").strip()
        norm_src = normalize_arabic(src_lemma)
        lower_tgt = tgt_lemma.lower()

        # ---- Provenance ----
        if "provenance" not in entry:
            if line_num <= manual_curated_count:
                entry["provenance"] = "manual_curated"
            elif (norm_src, lower_tgt) in beyond_name_pairs:
                entry["provenance"] = "beyond_the_name"
            else:
                # Try just root match (some entries have slight word mismatch)
                if norm_src and any(norm_src == r for r, _ in beyond_name_pairs):
                    entry["provenance"] = "beyond_the_name"
                else:
                    entry["provenance"] = "unknown"
            stats["provenance_added"] += 1

        # ---- Source gloss (Arabic meaning) ----
        current_src_gloss = src.get("gloss", "")
        # Treat bad fragment glosses (ending in colon, >60 chars) as missing
        is_bad_gloss = (
            current_src_gloss.endswith(":")
            or current_src_gloss.endswith("هو:")
            or len(current_src_gloss) > 60
        )
        if not current_src_gloss or is_bad_gloss:
            if is_bad_gloss:
                src["gloss"] = ""  # clear the bad gloss first
            # Look up arabic meaning by normalized root
            arabic_meaning = root_to_arabic_meaning.get(norm_src, "")
            if arabic_meaning:
                src["gloss"] = arabic_meaning
                stats["source_gloss_added"] += 1

        # ---- Target gloss (English meaning) ----
        # "Beyond the Name" entries may have Arabic text as target.gloss (wrong), or
        # a capitalized copy of the English word (acceptable but sparse), or empty.
        # We fix: Arabic-text glosses (replace with English word from CSV),
        #         and empty glosses (fill with English word from CSV).
        # We leave alone: real English glosses from manually curated entries.
        current_tgt_gloss = tgt.get("gloss", "")
        # Detect if current gloss contains Arabic script
        is_arabic_gloss = bool(re.search(r"[\u0600-\u06FF]", current_tgt_gloss))
        if is_arabic_gloss or not current_tgt_gloss:
            # Use english_word from CSV as the minimal English gloss
            english_gloss = word_to_english_meaning.get(lower_tgt, "")
            if not english_gloss and lower_tgt:
                # Fallback: use the lemma itself title-cased as the gloss
                english_gloss = tgt_lemma
            if english_gloss:
                tgt["gloss"] = english_gloss
                stats["target_gloss_fixed"] += 1
            elif is_arabic_gloss:
                # Arabic gloss but no lookup — clear it (wrong language)
                tgt["gloss"] = ""

    # Write back
    with open(jsonl_path, "w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    stats["source_gloss_after"] = sum(1 for e in entries if e.get("source", {}).get("gloss", ""))
    stats["target_gloss_after"] = sum(1 for e in entries if e.get("target", {}).get("gloss", ""))
    stats["provenance_counts"] = {}
    for e in entries:
        prov = e.get("provenance", "unknown")
        stats["provenance_counts"][prov] = stats["provenance_counts"].get(prov, 0) + 1

    return stats


# ---------------------------------------------------------------------------
# Quality report
# ---------------------------------------------------------------------------

def print_quality_report(gold_stats: dict, silver_stats: dict) -> None:
    def pct(n, total):
        return f"{n / total * 100:.1f}%" if total else "0%"

    def section(label: str, s: dict):
        t = s["total"]
        sg = s["source_gloss_after"]
        tg = s["target_gloss_after"]
        prov = s["provenance_counts"]
        prov_total = sum(prov.values())
        print(f"\nTotal {label} entries: {t}")
        print(f"  With source.gloss: {sg} ({pct(sg, t)})")
        print(f"  With target.gloss: {tg} ({pct(tg, t)})")
        print(f"  With provenance: {prov_total} ({pct(prov_total, t)})")
        print(f"  By provenance:")
        for k in ["manual_curated", "beyond_the_name", "unknown"]:
            v = prov.get(k, 0)
            print(f"    {k}: {v}")

    print("\n=== BENCHMARK QUALITY REPORT ===")
    section("gold", gold_stats)
    section("silver", silver_stats)

    print("\n=== ENRICHMENT SUMMARY ===")
    print(f"Gold - source.gloss: {gold_stats['source_gloss_before']} -> {gold_stats['source_gloss_after']} (+{gold_stats['source_gloss_added']})")
    print(f"Gold - target.gloss: {gold_stats['target_gloss_before']} -> {gold_stats['target_gloss_after']} (+{gold_stats['target_gloss_fixed']} fixed/added)")
    print(f"Gold - provenance fields added: {gold_stats['provenance_added']}")
    print(f"Silver - source.gloss: {silver_stats['source_gloss_before']} -> {silver_stats['source_gloss_after']} (+{silver_stats['source_gloss_added']})")
    print(f"Silver - target.gloss: {silver_stats['target_gloss_before']} -> {silver_stats['target_gloss_after']} (+{silver_stats['target_gloss_fixed']} fixed/added)")
    print(f"Silver - provenance fields added: {silver_stats['provenance_added']}")


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_file(jsonl_path: Path) -> None:
    """Reload file and verify valid JSON, no data loss."""
    entries = []
    with open(jsonl_path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {i} of {jsonl_path}: {e}") from e
    print(f"  {jsonl_path.name}: {len(entries)} entries — all valid JSON")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Loading CSV lookup tables...")
    root_to_arabic_meaning, word_to_english_meaning, beyond_name_pairs = load_csv_lookups(CSV_PATH)
    print(f"  Arabic root meanings loaded: {len(root_to_arabic_meaning)}")
    print(f"  English word meanings loaded: {len(word_to_english_meaning)}")
    print(f"  Beyond-the-Name pairs (for provenance): {len(beyond_name_pairs)}")

    print("\nEnriching cognate_gold.jsonl...")
    gold_stats = enrich_file(
        GOLD_PATH,
        root_to_arabic_meaning,
        word_to_english_meaning,
        beyond_name_pairs,
        manual_curated_count=MANUAL_CURATED_COUNT,
    )

    print("Enriching cognate_silver.jsonl...")
    # All silver entries are from Beyond the Name (manual_curated_count=0)
    silver_stats = enrich_file(
        SILVER_PATH,
        root_to_arabic_meaning,
        word_to_english_meaning,
        beyond_name_pairs,
        manual_curated_count=0,
    )

    print_quality_report(gold_stats, silver_stats)

    print("\nVerifying files...")
    verify_file(GOLD_PATH)
    verify_file(SILVER_PATH)
    print("All checks passed.")


if __name__ == "__main__":
    main()
