"""
Juthoor LV2 — Eye 1 Full-Scale Skeleton Matcher

Fast consonant-skeleton pre-filter for Arabic genome roots × Latin/Greek lemmas.
Uses inverted-index + set-Jaccard to run 12K×50K+ pairs in under 10 minutes.

Usage:
  python scripts/discovery/run_eye1_full_scale.py --target lat --threshold 0.3
  python scripts/discovery/run_eye1_full_scale.py --target grc --threshold 0.3

  # Quick test (100 roots × 1000 lemmas)
  python scripts/discovery/run_eye1_full_scale.py --target lat --threshold 0.3 \\
      --arabic-limit 100 --target-limit 1000
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

# Force UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

LV2_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = LV2_ROOT.parent
LV0_PROCESSED = REPO_ROOT / "Juthoor-DataCore-LV0/data/processed"

sys.path.insert(0, str(LV2_ROOT / "src"))

# ---------------------------------------------------------------------------
# Corpus paths (relative to LV0_PROCESSED)
# ---------------------------------------------------------------------------

CORPUS_PATHS: dict[str, str] = {
    "lat": "latin/classical/sources/kaikki.jsonl",
    "grc": "ancient_greek/sources/kaikki.jsonl",
    "ang": "english_old/sources/kaikki.jsonl",
    "enm": "english_middle/sources/kaikki.jsonl",
}

ARABIC_SOURCES: list[Path] = [
    LV2_ROOT / "data/processed/arabic_genome_roots_discovery.jsonl",  # preferred (pre-built)
    LV2_ROOT / "data/processed/arabic/hf_roots.jsonl",                # fallback: HF classical
    LV0_PROCESSED / "quranic_arabic/sources/quran_lemmas_enriched.jsonl",  # fallback: Quranic
]

# ---------------------------------------------------------------------------
# Imports (imported lazily to give clear error messages)
# ---------------------------------------------------------------------------

def _load_phonetic_modules() -> tuple:
    """Load Arabic skeleton extraction helpers from phonetic_law_scorer."""
    from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import (
        _arabic_consonant_skeleton,
        _strip_diacriticals,
        LATIN_EQUIVALENTS,
    )
    return _arabic_consonant_skeleton, _strip_diacriticals, LATIN_EQUIVALENTS


def _load_target_morphology() -> Any:
    """Load target morphology module."""
    from juthoor_cognatediscovery_lv2.discovery import target_morphology
    return target_morphology


# ---------------------------------------------------------------------------
# Arabic root normalization
# ---------------------------------------------------------------------------

import re as _re

_ARABIC_DIACRITICS_RE = _re.compile(r"[\u064B-\u065F\u0670\u0640]")
_HAMZA_TR = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ؤ": "و", "ئ": "ي", "ء": "ا",
})


def _norm_arabic(text: str) -> str:
    text = _ARABIC_DIACRITICS_RE.sub("", text)
    return text.translate(_HAMZA_TR).strip()


# ---------------------------------------------------------------------------
# POS filter for kaikki corpora
# ---------------------------------------------------------------------------

def _pos_ok(pos: list | str | None) -> bool:
    if pos is None:
        return True
    if isinstance(pos, list):
        return any(p in ("noun", "verb", "adj", "adv", "adjective", "adverb", "") for p in pos)
    return True


# ---------------------------------------------------------------------------
# Step 1: Load Arabic roots
# ---------------------------------------------------------------------------

def load_arabic_roots(
    source_override: Path | None = None,
    limit: int = 0,
) -> list[dict[str, Any]]:
    """Load Arabic genome roots from the best available source.

    Returns a list of dicts with at minimum:
      - arabic_root: Arabic script root string
      - translit: ASCII transliteration (may be empty)
    """
    _arabic_skel, _strip_diac, LATIN_EQ = _load_phonetic_modules()

    # Determine source path
    candidates = [source_override] if source_override else ARABIC_SOURCES
    source_path: Path | None = None
    for c in candidates:
        if c is not None and c.exists():
            source_path = c
            break

    if source_path is None:
        print(
            "WARNING: No Arabic roots file found. Tried:", file=sys.stderr
        )
        for c in candidates:
            print(f"  {c}", file=sys.stderr)
        return []

    print(f"[arabic] Loading roots from: {source_path}", file=sys.stderr)

    roots: list[dict[str, Any]] = []
    seen_roots: set[str] = set()

    with open(source_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Get the Arabic root
            arabic_root = str(
                row.get("root") or row.get("lemma") or ""
            ).strip()
            if not arabic_root:
                continue

            # Normalize the root
            arabic_root_norm = _norm_arabic(arabic_root)
            if len(arabic_root_norm) < 2:
                continue

            # Deduplicate by normalized root
            if arabic_root_norm in seen_roots:
                continue
            seen_roots.add(arabic_root_norm)

            # Extract consonant skeleton
            ar_skel = _arabic_skel(arabic_root_norm)

            # Build Latin skeleton (primary)
            primary_latin = _strip_diac(
                "".join(LATIN_EQ.get(ch, (ch,))[0] for ch in ar_skel)
            )

            roots.append({
                "arabic_root": arabic_root,
                "arabic_root_norm": arabic_root_norm,
                "ar_skel": ar_skel,
                "primary_latin": primary_latin,
                "translit": str(row.get("translit", "") or ""),
                "english_gloss": str(row.get("english_gloss", "") or ""),
            })

            if limit and len(roots) >= limit:
                break

    print(f"[arabic] Loaded {len(roots)} unique roots.", file=sys.stderr)
    return roots


# ---------------------------------------------------------------------------
# Step 2: Load target lemmas
# ---------------------------------------------------------------------------

def load_target_lemmas(
    lang: str,
    source_override: Path | None = None,
    limit: int = 0,
) -> list[dict[str, Any]]:
    """Load unique lemmas for the target language.

    Also checks for a pre-built dedup file at:
      data/processed/{lang}_unique_lemmas.jsonl
    """
    # Check for pre-built dedup file first
    prebuilt = LV2_ROOT / f"data/processed/{lang}_unique_lemmas.jsonl"
    if source_override:
        prebuilt = source_override

    if prebuilt.exists():
        print(f"[{lang}] Loading lemmas from pre-built: {prebuilt}", file=sys.stderr)
        entries: list[dict[str, Any]] = []
        seen: set[str] = set()
        with open(prebuilt, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                lemma = str(row.get("lemma", "") or "").strip().lower()
                if not lemma or lemma in seen:
                    continue
                seen.add(lemma)
                entries.append(row)
                if limit and len(entries) >= limit:
                    break
        print(f"[{lang}] Loaded {len(entries)} unique lemmas.", file=sys.stderr)
        return entries

    # Fall back to raw kaikki corpus
    corpus_rel = CORPUS_PATHS.get(lang)
    if corpus_rel is None:
        raise ValueError(f"No corpus path known for lang={lang!r}")

    corpus_path = LV0_PROCESSED / corpus_rel
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus not found: {corpus_path}")

    print(f"[{lang}] Loading lemmas from raw corpus: {corpus_path}", file=sys.stderr)

    entries = []
    seen_lemmas: set[str] = set()

    with open(corpus_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue

            lemma = str(row.get("lemma", "") or "").strip().lower()
            if not lemma or len(lemma) < 2:
                continue
            pos = row.get("pos")
            if not _pos_ok(pos):
                continue
            if lemma in seen_lemmas:
                continue
            seen_lemmas.add(lemma)

            entries.append({
                "lemma": lemma,
                "ipa": str(row.get("ipa_raw", "") or row.get("ipa", "") or ""),
                "lang": lang,
            })

            if limit and len(entries) >= limit:
                break

    print(f"[{lang}] Loaded {len(entries)} unique lemmas.", file=sys.stderr)
    return entries


# ---------------------------------------------------------------------------
# Step 3: Pre-compute all Arabic skeletons (including phonetic variants)
# ---------------------------------------------------------------------------

def build_arabic_skeleton_index(
    roots: list[dict[str, Any]],
    lang: str,
) -> list[dict[str, Any]]:
    """For each Arabic root, build the full set of consonant skeleton variants.

    Uses:
    1. Primary Latin skeleton from _arabic_consonant_skeleton + LATIN_EQUIVALENTS
    2. All secondary projections from LATIN_EQUIVALENTS (alternate consonant mappings)
    3. Phonetic variants from target_morphology.phonetic_variants

    Returns the list augmented with 'all_skeletons' (set of str) and
    'skel_chars' (frozenset of chars from primary_latin, for inverted index).
    """
    tm = _load_target_morphology()
    _arabic_skel, _strip_diac, LATIN_EQ = _load_phonetic_modules()

    augmented: list[dict[str, Any]] = []
    for root_info in roots:
        ar_skel = root_info["ar_skel"]
        primary_latin = root_info["primary_latin"]

        # Collect all Latin projections from LATIN_EQUIVALENTS
        # Each Arabic consonant can map to multiple Latin equivalents
        all_proj_sets: list[list[str]] = []
        for ch in ar_skel:
            options = list(LATIN_EQ.get(ch, (ch,)))
            # Keep only ASCII-clean options (remove diacriticized equivalents)
            clean_options = [_strip_diac(o) for o in options if o]
            clean_options = [o for o in clean_options if o and o.isascii()]
            if not clean_options:
                clean_options = [_strip_diac(LATIN_EQ.get(ch, (ch,))[0])]
                clean_options = [o for o in clean_options if o]
            if not clean_options:
                clean_options = [ch] if ch.isascii() else []
            all_proj_sets.append(clean_options if clean_options else [""])

        # Build skeleton variants: start with primary, then expand each position
        seen_skels: dict[str, None] = {}

        def _add_skel(s: str) -> None:
            s = s.strip()
            if s and s not in seen_skels:
                seen_skels[s] = None

        _add_skel(primary_latin)

        # Generate one-position substitution variants from LATIN_EQ
        for i, options in enumerate(all_proj_sets):
            for opt in options:
                parts = [all_proj_sets[j][0] for j in range(len(all_proj_sets))]
                parts[i] = opt
                candidate = "".join(parts)
                _add_skel(_strip_diac(candidate))

        # Add phonetic variants of the primary skeleton
        for var in tm.phonetic_variants(primary_latin, lang):
            _add_skel(var)

        all_skels = set(seen_skels.keys()) - {""}
        if not all_skels:
            continue

        augmented.append({
            **root_info,
            "all_skeletons": all_skels,
            # Use primary_latin chars for the inverted index (most common case)
            "skel_chars": frozenset(primary_latin) - {" ", "-"},
        })

    return augmented


# ---------------------------------------------------------------------------
# Step 4: Pre-compute all target skeletons
# ---------------------------------------------------------------------------

def build_target_skeleton_index(
    lemmas: list[dict[str, Any]],
    lang: str,
) -> list[dict[str, Any]]:
    """For each target lemma, build all consonant skeleton variants.

    Uses extract_all_skeletons(word, ipa, lang) from target_morphology.
    Returns augmented list with 'all_skeletons' (set) and 'skel_chars' (frozenset).
    """
    tm = _load_target_morphology()
    augmented: list[dict[str, Any]] = []
    for entry in lemmas:
        lemma = entry["lemma"]
        ipa = entry.get("ipa") or None
        skels = tm.extract_all_skeletons(lemma, ipa, lang)
        if not skels:
            continue

        # Compute union of all chars in all skeletons (for inverted index)
        all_chars: set[str] = set()
        for s in skels:
            all_chars.update(s)

        augmented.append({
            **entry,
            "all_skeletons": set(skels),
            "skel_chars": frozenset(all_chars) - {""},
        })

    return augmented


# ---------------------------------------------------------------------------
# Step 5: Build inverted index (consonant → target lemma indices)
# ---------------------------------------------------------------------------

def build_inverted_index(
    target_entries: list[dict[str, Any]],
) -> dict[str, list[int]]:
    """Map each consonant char → list of target entry indices containing that char."""
    inv: dict[str, list[int]] = defaultdict(list)
    for idx, entry in enumerate(target_entries):
        for ch in entry["skel_chars"]:
            inv[ch].append(idx)
    return dict(inv)


# ---------------------------------------------------------------------------
# Step 6: Jaccard + ordered overlap computation
# ---------------------------------------------------------------------------

def jaccard(a: frozenset | set, b: frozenset | set) -> float:
    inter = len(a & b)
    union = len(a | b)
    if union == 0:
        return 0.0
    return inter / union


def ordered_overlap(skel_a: str, skel_b: str) -> list[str]:
    """Find consonants that appear in both skeletons in the same relative order.

    Uses a greedy left-to-right scan (not full LCS, fast).
    Returns list of matching consonants in order.
    """
    j = 0
    matches: list[str] = []
    for ch in skel_a:
        while j < len(skel_b):
            if skel_b[j] == ch:
                matches.append(ch)
                j += 1
                break
            j += 1
    return matches


# ---------------------------------------------------------------------------
# Step 7: Main matching loop (inverted-index accelerated)
# ---------------------------------------------------------------------------

def run_matching(
    arabic_entries: list[dict[str, Any]],
    target_entries: list[dict[str, Any]],
    inv_index: dict[str, list[int]],
    lang: str,
    threshold: float = 0.3,
    min_overlap: int = 2,
) -> list[dict[str, Any]]:
    """Run the skeleton matching with inverted-index acceleration.

    For each Arabic root:
      1. Find candidate targets sharing >= min_overlap consonant chars via inverted index
      2. For each candidate, compute best Jaccard across all skeleton pair combinations
      3. Also check ordered overlap as fallback
      4. Emit match if Jaccard >= threshold OR ordered_overlap >= min_overlap
    """
    matches: list[dict[str, Any]] = []

    total = len(arabic_entries)
    report_step = max(1, total // 20)  # report every 5%

    t0 = time.time()

    for i, ar_entry in enumerate(arabic_entries):
        if i % report_step == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(
                f"  [{i+1}/{total}] {rate:.0f} roots/s | matches so far: {len(matches)}",
                file=sys.stderr,
            )

        ar_skels = ar_entry["all_skeletons"]
        ar_chars = ar_entry["skel_chars"]

        # Collect candidate target indices via inverted index
        candidate_counts: dict[int, int] = defaultdict(int)
        for ch in ar_chars:
            if ch in inv_index:
                for idx in inv_index[ch]:
                    candidate_counts[idx] += 1

        # Only process targets sharing >= min_overlap consonants
        candidate_indices = [
            idx for idx, cnt in candidate_counts.items()
            if cnt >= min_overlap
        ]

        for idx in candidate_indices:
            tgt_entry = target_entries[idx]
            tgt_skels = tgt_entry["all_skeletons"]

            best_jaccard = 0.0
            best_ar_skel = ""
            best_tgt_skel = ""
            best_overlap: list[str] = []

            # Test all combinations of (Arabic skel variant, target skel variant)
            for ar_skel in ar_skels:
                ar_set = frozenset(ar_skel)
                for tgt_skel in tgt_skels:
                    tgt_set = frozenset(tgt_skel)
                    j_score = jaccard(ar_set, tgt_set)
                    if j_score > best_jaccard:
                        best_jaccard = j_score
                        best_ar_skel = ar_skel
                        best_tgt_skel = tgt_skel
                        best_overlap = list(ar_set & tgt_set)

            # Also check ordered overlap on primary skeletons
            primary_ar = ar_entry["primary_latin"]
            primary_tgt = next(iter(tgt_skels)) if tgt_skels else ""
            ord_overlap = ordered_overlap(primary_ar, primary_tgt) if primary_ar and primary_tgt else []

            # Emit if passes threshold or ordered overlap
            if best_jaccard >= threshold or len(ord_overlap) >= min_overlap:
                matches.append({
                    "arabic_root": ar_entry["arabic_root"],
                    "arabic_skeleton": best_ar_skel or ar_entry["primary_latin"],
                    "target_lemma": tgt_entry["lemma"],
                    "target_skeleton": best_tgt_skel or primary_tgt,
                    "jaccard": round(best_jaccard, 4),
                    "overlap_consonants": sorted(best_overlap),
                    "ordered_overlap": ord_overlap,
                    "lang": lang,
                })

    elapsed = time.time() - t0
    return matches, elapsed


# ---------------------------------------------------------------------------
# CLI + main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Eye 1 full-scale skeleton matcher: Arabic roots × target lemmas"
    )
    p.add_argument(
        "--target",
        required=True,
        choices=list(CORPUS_PATHS.keys()),
        help="Target language code (lat, grc, ang, enm)",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        help="Minimum Jaccard similarity (default 0.3)",
    )
    p.add_argument(
        "--min-overlap",
        type=int,
        default=2,
        help="Minimum consonant overlap count (default 2)",
    )
    p.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: outputs/eye1_full_scale_{target}.jsonl)",
    )
    p.add_argument(
        "--arabic-source",
        type=str,
        default=None,
        help="Path to Arabic roots JSONL file (default: auto-detect)",
    )
    p.add_argument(
        "--target-source",
        type=str,
        default=None,
        help="Path to target lemmas JSONL file (default: auto-detect)",
    )
    p.add_argument(
        "--arabic-limit",
        type=int,
        default=0,
        help="Limit number of Arabic roots (0 = all)",
    )
    p.add_argument(
        "--target-limit",
        type=int,
        default=0,
        help="Limit number of target lemmas (0 = all)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    lang = args.target

    # Resolve output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = LV2_ROOT / "outputs" / f"eye1_full_scale_{lang}.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"=== Eye 1 Full-Scale Skeleton Matcher ===", file=sys.stderr)
    print(f"  Target language : {lang}", file=sys.stderr)
    print(f"  Threshold       : {args.threshold}", file=sys.stderr)
    print(f"  Min overlap     : {args.min_overlap}", file=sys.stderr)
    print(f"  Output          : {output_path}", file=sys.stderr)
    print(file=sys.stderr)

    t_global = time.time()

    # ---- Step 1: Load Arabic roots ----
    t0 = time.time()
    arabic_source = Path(args.arabic_source) if args.arabic_source else None
    raw_arabic = load_arabic_roots(source_override=arabic_source, limit=args.arabic_limit)
    if not raw_arabic:
        print("ERROR: No Arabic roots loaded. Exiting.", file=sys.stderr)
        sys.exit(1)
    print(f"  Arabic roots loaded in {time.time()-t0:.1f}s", file=sys.stderr)

    # ---- Step 2: Load target lemmas ----
    t0 = time.time()
    target_source = Path(args.target_source) if args.target_source else None
    raw_target = load_target_lemmas(lang, source_override=target_source, limit=args.target_limit)
    if not raw_target:
        print(f"ERROR: No target lemmas loaded for lang={lang}. Exiting.", file=sys.stderr)
        sys.exit(1)
    print(f"  Target lemmas loaded in {time.time()-t0:.1f}s", file=sys.stderr)

    # ---- Step 3: Pre-compute Arabic skeletons ----
    t0 = time.time()
    print("[3/6] Pre-computing Arabic skeletons + variants...", file=sys.stderr)
    arabic_entries = build_arabic_skeleton_index(raw_arabic, lang)
    print(f"  {len(arabic_entries)} Arabic entries with skeletons in {time.time()-t0:.1f}s", file=sys.stderr)

    # ---- Step 4: Pre-compute target skeletons ----
    t0 = time.time()
    print("[4/6] Pre-computing target skeletons + variants...", file=sys.stderr)
    target_entries = build_target_skeleton_index(raw_target, lang)
    print(f"  {len(target_entries)} target entries with skeletons in {time.time()-t0:.1f}s", file=sys.stderr)

    # ---- Step 5: Build inverted index ----
    t0 = time.time()
    print("[5/6] Building inverted index (consonant → targets)...", file=sys.stderr)
    inv_index = build_inverted_index(target_entries)
    print(f"  {len(inv_index)} consonant keys in index in {time.time()-t0:.1f}s", file=sys.stderr)

    # ---- Step 6: Run matching ----
    print("[6/6] Running skeleton matching...", file=sys.stderr)
    matches, elapsed = run_matching(
        arabic_entries,
        target_entries,
        inv_index,
        lang=lang,
        threshold=args.threshold,
        min_overlap=args.min_overlap,
    )

    # ---- Write output ----
    print(f"\nWriting {len(matches)} matches to {output_path} ...", file=sys.stderr)
    with open(output_path, "w", encoding="utf-8") as f:
        for m in matches:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

    total_elapsed = time.time() - t_global
    pairs_checked = len(arabic_entries) * len(target_entries)
    rate = pairs_checked / elapsed if elapsed > 0 else 0

    print(file=sys.stderr)
    print("=== Summary ===", file=sys.stderr)
    print(f"  Arabic roots     : {len(arabic_entries)}", file=sys.stderr)
    print(f"  Target lemmas    : {len(target_entries)}", file=sys.stderr)
    print(f"  Pairs (max)      : {pairs_checked:,}", file=sys.stderr)
    print(f"  Matches found    : {len(matches)}", file=sys.stderr)
    print(f"  Match rate       : {len(matches)/max(1,len(arabic_entries)*len(target_entries))*100:.4f}%", file=sys.stderr)
    print(f"  Matching time    : {elapsed:.1f}s", file=sys.stderr)
    print(f"  Total time       : {total_elapsed:.1f}s", file=sys.stderr)
    print(f"  Throughput       : {rate:,.0f} pairs/s (theoretical max)", file=sys.stderr)
    print(f"  Output           : {output_path}", file=sys.stderr)

    # Print sample matches
    if matches:
        print(file=sys.stderr)
        print("Top 5 matches by Jaccard:", file=sys.stderr)
        top5 = sorted(matches, key=lambda x: x["jaccard"], reverse=True)[:5]
        for m in top5:
            print(
                f"  {m['arabic_root']} ({m['arabic_skeleton']}) ↔ "
                f"{m['target_lemma']} ({m['target_skeleton']})  "
                f"J={m['jaccard']:.3f}  overlap={m['overlap_consonants']}",
                file=sys.stderr,
            )


if __name__ == "__main__":
    main()
