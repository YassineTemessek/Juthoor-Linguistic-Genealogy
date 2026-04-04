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

            # Use pre-computed skeleton field if present (genome discovery format)
            # Otherwise extract from Arabic script
            prebuilt_skeleton = str(row.get("skeleton", "") or "").strip()
            if prebuilt_skeleton and prebuilt_skeleton.isascii():
                # genome roots file has a pre-computed ASCII skeleton
                primary_latin = prebuilt_skeleton
                ar_skel = arabic_root_norm  # keep original for display
            else:
                # Extract consonant skeleton from Arabic script
                ar_skel = _arabic_skel(arabic_root_norm)
                primary_latin = _strip_diac(
                    "".join(LATIN_EQ.get(ch, (ch,))[0] for ch in ar_skel)
                )

            if not primary_latin or len(primary_latin) < 2:
                continue

            roots.append({
                "arabic_root": arabic_root,
                "arabic_root_norm": arabic_root_norm,
                "ar_skel": ar_skel,
                "primary_latin": primary_latin,
                "translit": str(row.get("translit", "") or ""),
                "english_gloss": (
                    str(row.get("english_gloss", "") or "")
                    or str(row.get("mafahim_gloss", "") or "")
                    or str(row.get("masadiq_gloss", "") or "")
                ),
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
      data/processed/{name}_unique_lemmas.jsonl
    """
    # Check for pre-built dedup file first
    # Dedup script uses full language names, not ISO codes
    DEDUP_NAMES = {"lat": "latin", "grc": "greek", "ang": "english_old", "enm": "english_middle"}
    dedup_name = DEDUP_NAMES.get(lang, lang)
    prebuilt = LV2_ROOT / f"data/processed/{dedup_name}_unique_lemmas.jsonl"
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
# Step 3: Pre-compute all Arabic skeletons (primary + alternates only)
# ---------------------------------------------------------------------------

def build_arabic_skeleton_index(
    roots: list[dict[str, Any]],
    lang: str,
) -> list[dict[str, Any]]:
    """For each Arabic root, build consonant skeleton variants.

    Strategy (performance-first):
    - Primary Latin skeleton (from LATIN_EQUIVALENTS primary mapping)
    - Alternate skeletons: one-position substitutions from LATIN_EQUIVALENTS
      (limited to max 8 per root to control candidate explosion)
    - skel_chars: frozenset of chars in PRIMARY skeleton only (for tight inverted index)
    - all_skels_sets: list of frozensets for fast Jaccard in inner loop

    The primary skeleton chars drive the inverted index. Only targets sharing
    >= min_overlap primary chars become candidates. This is the key pre-filter.
    """
    _arabic_skel, _strip_diac, LATIN_EQ = _load_phonetic_modules()

    augmented: list[dict[str, Any]] = []
    for root_info in roots:
        ar_skel = root_info["ar_skel"]
        primary_latin = root_info["primary_latin"]

        if not primary_latin or len(primary_latin) < 2:
            continue

        # Build alternate projections (one-position substitution from LATIN_EQ)
        all_proj_sets: list[list[str]] = []
        for ch in ar_skel:
            options = list(LATIN_EQ.get(ch, (ch,)))
            clean = [_strip_diac(o) for o in options if o]
            clean = [o for o in clean if o and o.isascii()]
            if not clean:
                clean = [primary_latin[len(all_proj_sets)] if len(all_proj_sets) < len(primary_latin) else ""]
            all_proj_sets.append(clean if clean else [""])

        seen_skels: dict[str, None] = {primary_latin: None}

        def _add_skel(s: str) -> None:
            s = s.strip()
            if s and len(s) >= 2 and s not in seen_skels and len(seen_skels) < 8:
                seen_skels[s] = None

        # One-position substitutions
        for i, options in enumerate(all_proj_sets):
            for opt in options[1:]:  # skip [0] = primary
                parts = [all_proj_sets[j][0] for j in range(len(all_proj_sets))]
                parts[i] = opt
                _add_skel(_strip_diac("".join(parts)))

        all_skels = list(seen_skels.keys())

        # Pre-compute frozensets for fast Jaccard in inner loop
        all_skels_sets = [frozenset(s) for s in all_skels]

        augmented.append({
            **root_info,
            "all_skeletons": all_skels,
            "all_skels_sets": all_skels_sets,
            # skel_chars kept for compatibility; bigrams used for actual filtering
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
    """For each target lemma, build consonant skeleton variants.

    DEDUPLICATION: Multiple lemmas sharing the same primary skeleton are
    collapsed into one entry (representative lemma kept, others in 'alt_lemmas').
    This reduces ~815K Latin lemmas to ~236K unique-skeleton groups, making
    the inner matching loop 3-4x faster.

    Uses extract_all_skeletons(word, ipa, lang) from target_morphology.
    Pre-computes:
      - all_skeletons: list of skeleton strings (from primary lemma)
      - all_skels_sets: list of frozensets for fast Jaccard
    """
    tm = _load_target_morphology()

    # Track by primary skeleton for deduplication
    by_primary_skel: dict[str, dict[str, Any]] = {}
    total_in = 0
    total_skipped = 0

    for entry in lemmas:
        lemma = entry["lemma"]
        ipa = entry.get("ipa") or None
        skels = tm.extract_all_skeletons(lemma, ipa, lang)
        if not skels:
            total_skipped += 1
            continue

        # Filter: skip short skeletons (single-char are too noisy)
        skels = [s for s in skels if len(s) >= 2]
        if not skels:
            total_skipped += 1
            continue

        primary_skel = skels[0]
        total_in += 1

        if primary_skel not in by_primary_skel:
            all_skels_sets = [frozenset(s) for s in skels]
            by_primary_skel[primary_skel] = {
                "lemma": lemma,
                "lang": lang,
                "all_skeletons": skels,
                "all_skels_sets": all_skels_sets,
                "alt_lemmas": [],
            }
        else:
            # Collapse into existing entry — just record the lemma
            by_primary_skel[primary_skel]["alt_lemmas"].append(lemma)

    augmented = list(by_primary_skel.values())
    print(
        f"  Deduplicated {total_in} lemmas → {len(augmented)} unique-skeleton groups "
        f"({total_skipped} skipped, skeleton dedup ratio: {total_in/max(1,len(augmented)):.1f}x)",
        file=sys.stderr,
    )
    return augmented


# ---------------------------------------------------------------------------
# Step 5: Build inverted index (sorted consonant pairs)
# ---------------------------------------------------------------------------

def _sorted_pairs(skel: str) -> set[str]:
    """Return all sorted 2-char consonant combinations from a skeleton.

    E.g., "krm" → {"km", "kr", "mr"}
    These are order-insensitive, so "krm" and "mkr" produce the same pairs.
    Using sorted pairs (vs consecutive bigrams) gives a much tighter pre-filter:
    requiring 2+ pair hits means the target shares effectively all consonants.
    """
    chars = list(skel)
    pairs: set[str] = set()
    for i in range(len(chars)):
        for j in range(i + 1, len(chars)):
            pairs.add("".join(sorted([chars[i], chars[j]])))
    return pairs


def build_inverted_index(
    target_entries: list[dict[str, Any]],
) -> dict[str, list[int]]:
    """Map each sorted consonant PAIR → list of target indices containing that pair.

    Using sorted pairs (2-consonant combos) as keys creates a much tighter index:
    - A 3-char skeleton like "krm" produces 3 pairs: {km, kr, mr}
    - Requiring 2+ hits means a target must share 2 of 3 consonant pairs
    - This reduces candidate set to ~4-8% vs 33-40% with unigrams

    A target is indexed under all pairs from ALL its skeleton variants.
    """
    inv: dict[str, list[int]] = defaultdict(list)
    for idx, entry in enumerate(target_entries):
        all_pairs: set[str] = set()
        for skel in entry["all_skeletons"]:
            if len(skel) >= 2:
                all_pairs.update(_sorted_pairs(skel))
        for pair in all_pairs:
            inv[pair].append(idx)
    return dict(inv)


# ---------------------------------------------------------------------------
# Step 6: Jaccard + ordered overlap computation
# ---------------------------------------------------------------------------

def best_jaccard_pair(
    ar_skel_sets: list[frozenset],
    tgt_skel_sets: list[frozenset],
) -> tuple[float, int, int]:
    """Find the best Jaccard score across all Arabic×target skeleton pairs.

    Fast path: if only one skel on each side, compute directly.
    Returns (best_score, ar_idx, tgt_idx).
    """
    best_score = 0.0
    best_ai = 0
    best_ti = 0

    if len(ar_skel_sets) == 1 and len(tgt_skel_sets) == 1:
        a, b = ar_skel_sets[0], tgt_skel_sets[0]
        inter = len(a & b)
        if inter > 0:
            best_score = inter / len(a | b)
        return best_score, 0, 0

    for ai, a in enumerate(ar_skel_sets):
        for ti, b in enumerate(tgt_skel_sets):
            inter = len(a & b)
            if inter == 0:
                continue
            score = inter / len(a | b)
            if score > best_score:
                best_score = score
                best_ai = ai
                best_ti = ti
                if best_score >= 1.0:
                    return best_score, best_ai, best_ti

    return best_score, best_ai, best_ti


def ordered_overlap(skel_a: str, skel_b: str) -> list[str]:
    """Find consonants appearing in both skeletons in the same relative order.

    Uses a greedy left-to-right scan. Returns matching consonants in order.
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
) -> tuple[list[dict[str, Any]], float]:
    """Run skeleton matching with inverted-index acceleration.

    Performance strategy:
    1. For each Arabic root, look up candidates via primary-skeleton inverted index
    2. Count per-target how many Arabic PRIMARY chars it shares
    3. Only process targets sharing >= min_overlap chars
    4. Compute best Jaccard using pre-computed frozensets (fast set ops)
    5. Ordered overlap only as tie-breaker on primary skeletons
    6. Emit match if Jaccard >= threshold OR ordered_overlap >= min_overlap
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

        ar_skel_sets = ar_entry["all_skels_sets"]
        primary_latin = ar_entry["primary_latin"]

        # 1. Sorted-pair inverted index lookup from primary Latin skeleton
        # sorted_pairs are order-insensitive consonant combos — highly selective
        ar_pairs = _sorted_pairs(primary_latin) if len(primary_latin) >= 2 else set()
        # Also add pairs from alternate skeletons (up to first 3 variants)
        for alt_skel in ar_entry["all_skeletons"][1:4]:
            if len(alt_skel) >= 2:
                ar_pairs.update(_sorted_pairs(alt_skel))

        candidate_counts: dict[int, int] = defaultdict(int)
        for pair in ar_pairs:
            if pair in inv_index:
                for idx in inv_index[pair]:
                    candidate_counts[idx] += 1

        # 2. Require >= 2 shared consonant pairs (much tighter filter than unigrams)
        # A 3-char skeleton has 3 pairs total, so 2+ hits means 2/3 consonants match
        required_hits = min_overlap if min_overlap >= 2 else 2
        for idx, cnt in candidate_counts.items():
            if cnt < required_hits:
                continue

            tgt_entry = target_entries[idx]
            tgt_skel_sets = tgt_entry["all_skels_sets"]

            # 3. Best Jaccard across all skel pair combinations
            best_j, best_ai, best_ti = best_jaccard_pair(ar_skel_sets, tgt_skel_sets)

            # 4. Ordered overlap on primary skeletons (fallback / bonus)
            primary_tgt = tgt_entry["all_skeletons"][0]
            ord_ov = ordered_overlap(primary_latin, primary_tgt)

            # 5. Emit if passes threshold or ordered overlap
            if best_j >= threshold or len(ord_ov) >= min_overlap:
                best_ar_skel = ar_entry["all_skeletons"][best_ai]
                best_tgt_skel = tgt_entry["all_skeletons"][best_ti]
                overlap_chars = sorted(ar_skel_sets[best_ai] & tgt_skel_sets[best_ti])
                alt_lemmas = tgt_entry.get("alt_lemmas", [])

                matches.append({
                    "arabic_root": ar_entry["arabic_root"],
                    "arabic_skeleton": best_ar_skel,
                    "target_lemma": tgt_entry["lemma"],
                    "target_skeleton": best_tgt_skel,
                    "jaccard": round(best_j, 4),
                    "overlap_consonants": overlap_chars,
                    "ordered_overlap": ord_ov,
                    "lang": lang,
                    # alt_lemmas: other lemmas sharing the same primary skeleton
                    "n_lemmas": 1 + len(alt_lemmas),
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
