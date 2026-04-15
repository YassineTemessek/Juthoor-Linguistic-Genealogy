"""Phase 1b: Collapse deduplicated lemmas into word families before Eye 1.

Reduces the candidate space by 60-70% by grouping lemmas that share the same
primary stem. One representative is selected per family (shortest lemma with
the most semantic content in its gloss).

Usage
-----
python build_word_families.py --lang lat \
    --input data/processed/latin_unique_lemmas.jsonl \
    --output data/processed/latin_word_families.jsonl

python build_word_families.py --lang grc \
    --input data/processed/greek_unique_lemmas.jsonl \
    --output data/processed/greek_word_families.jsonl
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — allow running from any working directory
# ---------------------------------------------------------------------------
_LV2_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_LV2_ROOT / "src"))

from juthoor_cognatediscovery_lv2.discovery.target_morphology import decompose_target  # noqa: E402

# Try to import literal_skeleton; fall back to a basic consonant extractor
try:
    from juthoor_cognatediscovery_lv2.discovery.correspondence import literal_skeleton as _lit_skel  # noqa: E402
    _USE_LIT_SKEL = True
except ImportError:
    _USE_LIT_SKEL = False

# ---------------------------------------------------------------------------
# Consonant skeleton extraction (target-language, Latin-script)
# ---------------------------------------------------------------------------

_VOWELS_RE = re.compile(r"[aeiouāēīōūæœàáâãäåèéêëìíîïòóôõöùúûüý]", re.IGNORECASE)
_CONSONANT_RE = re.compile(r"[bcdfghjklmnpqrstvwxyz]", re.IGNORECASE)

# Greek-to-Latin transliteration table (mirrors target_morphology._to_latin)
_GRC_MAP: dict[str, str] = {
    "α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e",
    "ζ": "z", "η": "e", "θ": "th", "ι": "i", "κ": "k",
    "λ": "l", "μ": "m", "ν": "n", "ξ": "x", "ο": "o",
    "π": "p", "ρ": "r", "σ": "s", "ς": "s", "τ": "t",
    "υ": "u", "φ": "ph", "χ": "kh", "ψ": "ps", "ω": "o",
}


def _to_latin(word: str) -> str:
    result: list[str] = []
    for ch in unicodedata.normalize("NFC", word.lower()):
        mapped = _GRC_MAP.get(ch)
        if mapped is not None:
            result.append(mapped)
        elif ch.isascii():
            result.append(ch)
    return "".join(result)


def _orth_skeleton(word: str) -> str:
    """Extract a simple consonant skeleton from a Latin-script word."""
    return "".join(_CONSONANT_RE.findall(word.lower()))


def word_skeleton(word: str, lang: str) -> str:
    """Return the consonant skeleton for a word, handling Greek script."""
    w = word.lower().strip()
    if lang == "grc" and any(ord(ch) > 127 for ch in w):
        w = _to_latin(w)
    # Remove leading hyphens/punctuation (prefix markers like "-ādēs")
    w = re.sub(r"^[-\s]+", "", w)
    return _orth_skeleton(w)


# ---------------------------------------------------------------------------
# Gloss quality scoring — prefer glosses with more semantic content
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset({
    "a", "an", "the", "of", "to", "in", "on", "at", "by", "for", "with",
    "and", "or", "is", "are", "be", "been", "that", "this", "it", "its",
    "from", "as", "form", "used", "suffix", "prefix", "variant", "form",
    "genitive", "plural", "singular", "nominative", "accusative", "dative",
    "verb", "noun", "adjective", "adverb", "particle", "word",
})


def _gloss_score(gloss: str) -> int:
    """Higher score = more semantic content. Used to pick the best representative."""
    if not gloss:
        return 0
    tokens = re.findall(r"[a-zA-Z]+", gloss.lower())
    meaningful = [t for t in tokens if t not in _STOP_WORDS and len(t) > 2]
    return len(meaningful)


# ---------------------------------------------------------------------------
# Primary stem extraction
# ---------------------------------------------------------------------------

def primary_stem(word: str, lang: str) -> str:
    """Return the primary (first non-trivial) stem for grouping purposes.

    Uses decompose_target(); falls back to the word itself on failure.
    Strips leading hyphens first (handles suffix/prefix marker lemmas).
    """
    clean = word.strip().lstrip("-")
    if not clean:
        return word.lower()
    try:
        stems = decompose_target(clean, lang)
        # decompose_target returns [original, stem1, stem2, ...]
        # Use the second element (first stripped stem) when available and
        # meaningfully shorter; otherwise use the original.
        if len(stems) >= 2 and stems[1] and len(stems[1]) >= 2:
            return stems[1].lower()
        return stems[0].lower()
    except Exception:
        return clean.lower()


# ---------------------------------------------------------------------------
# Fuzzy stem similarity
# ---------------------------------------------------------------------------

def _stems_are_similar(a: str, b: str, threshold: float = 0.80) -> bool:
    """Return True if two stems are similar enough to be grouped.

    Uses SequenceMatcher ratio, which maps to roughly edit_distance <= 2
    for stems of typical length 3-8 characters.
    """
    if a == b:
        return True
    # Quick length guard: if lengths differ by more than 3, skip expensive check
    if abs(len(a) - len(b)) > 3:
        return False
    ratio = SequenceMatcher(None, a, b).ratio()
    return ratio >= threshold


# ---------------------------------------------------------------------------
# Core grouping algorithm
# ---------------------------------------------------------------------------

def build_families(
    lemmas: list[dict],
    lang: str,
    similarity_threshold: float = 0.80,
) -> list[dict]:
    """Group lemmas into word families by primary stem similarity.

    Algorithm
    ---------
    1. Compute primary_stem() for every lemma.
    2. Sort lemma list by stem so that identical stems cluster together
       (fast path: exact-match grouping first, then fuzzy merge).
    3. For each group, pick the representative: shortest lemma with the
       highest gloss score (ties broken lexicographically).
    4. Fuzzy-merge groups whose representative stems are similar
       (SequenceMatcher ratio >= threshold).

    Returns a list of family dicts sorted by family_id.
    """
    # Step 1: attach stems
    annotated: list[tuple[str, dict]] = []  # (stem, record)
    for rec in lemmas:
        stem = primary_stem(rec["lemma"], lang)
        annotated.append((stem, rec))

    # Step 2: exact-match grouping
    exact_groups: dict[str, list[dict]] = {}
    for stem, rec in annotated:
        exact_groups.setdefault(stem, []).append(rec)

    # Step 3: pick representative per exact group
    # Each group entry: {"stem": str, "members": [rec, ...]}
    groups: list[dict] = []
    for stem, members in exact_groups.items():
        rep = _pick_representative(members)
        groups.append({"stem": stem, "representative": rep, "members": members})

    # Step 4: fuzzy-merge groups
    # Sort by stem so nearby stems are adjacent (speeds up the inner loop)
    groups.sort(key=lambda g: g["stem"])
    merged: list[dict] = []
    used = [False] * len(groups)

    for i, grp in enumerate(groups):
        if used[i]:
            continue
        current_stem = grp["stem"]
        combined_members = list(grp["members"])
        used[i] = True

        for j in range(i + 1, len(groups)):
            if used[j]:
                continue
            other_stem = groups[j]["stem"]
            # Early exit: if stems diverge too much alphabetically, stop scanning
            # (this is a heuristic to keep O(n) near-linear on sorted data)
            if other_stem > current_stem and len(other_stem) > 0 and len(current_stem) > 0:
                # Only look ahead while first char matches or stems are close in length
                if other_stem[0] != current_stem[0]:
                    break
            if _stems_are_similar(current_stem, other_stem, similarity_threshold):
                combined_members.extend(groups[j]["members"])
                used[j] = True

        merged_rep = _pick_representative(combined_members)
        merged.append({
            "stem": current_stem,
            "representative": merged_rep,
            "members": combined_members,
        })

    # Step 5: assign family IDs and build output records
    output: list[dict] = []
    for fid, grp in enumerate(merged, start=1):
        rep = grp["representative"]
        rep_lemma = rep["lemma"]
        rep_gloss = rep.get("gloss", "")
        skel = word_skeleton(rep_lemma, lang)
        output.append({
            "family_id": fid,
            "representative": rep_lemma,
            "representative_gloss": rep_gloss,
            "members": [m["lemma"] for m in grp["members"]],
            "family_size": len(grp["members"]),
            "skeleton": skel,
        })

    return output


def _pick_representative(members: list[dict]) -> dict:
    """Select the best representative from a group of lemma records.

    Criteria (in priority order):
    1. Highest gloss score (most semantic content).
    2. Shortest lemma (more likely to be the base form).
    3. Lexicographic order (deterministic tiebreak).
    """
    def _key(rec: dict) -> tuple:
        gs = _gloss_score(rec.get("gloss", ""))
        lemma = rec["lemma"].lstrip("-")
        return (-gs, len(lemma), lemma)

    return min(members, key=_key)


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def read_lemmas(path: Path) -> list[dict]:
    records: list[dict] = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(f"  Warning: skipping malformed JSON on line {lineno}: {exc}",
                      file=sys.stderr)
    return records


def write_families(families: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for fam in families:
            fh.write(json.dumps(fam, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collapse deduplicated lemmas into word families (Phase 1b)."
    )
    parser.add_argument(
        "--lang",
        required=True,
        help='Language code, e.g. "lat", "grc", "ang".',
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to deduplicated lemma JSONL (output of dedup_corpora.py).",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output path for word families JSONL.",
    )
    parser.add_argument(
        "--similarity",
        type=float,
        default=0.80,
        help="SequenceMatcher ratio threshold for fuzzy stem merging (default: 0.80).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = args.input
    if not input_path.is_absolute():
        input_path = _LV2_ROOT / input_path

    output_path = args.output
    if not output_path.is_absolute():
        output_path = _LV2_ROOT / output_path

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Reading lemmas from: {input_path}")
    lemmas = read_lemmas(input_path)
    print(f"  Loaded {len(lemmas):,} lemma records.")

    if not lemmas:
        print("No lemmas found — nothing to do.", file=sys.stderr)
        sys.exit(1)

    print(f"Building word families (lang={args.lang}, similarity={args.similarity})...")
    families = build_families(lemmas, args.lang, args.similarity)

    print(f"Writing families to: {output_path}")
    write_families(families, output_path)

    # Summary stats
    total_lemmas = len(lemmas)
    total_families = len(families)
    compression = 1.0 - (total_families / total_lemmas) if total_lemmas > 0 else 0.0
    avg_size = total_lemmas / total_families if total_families > 0 else 0.0
    max_size = max((f["family_size"] for f in families), default=0)

    print()
    print("=== Word Family Summary ===")
    print(f"  Total input lemmas : {total_lemmas:,}")
    print(f"  Families created   : {total_families:,}")
    print(f"  Compression ratio  : {compression:.1%}")
    print(f"  Avg family size    : {avg_size:.2f}")
    print(f"  Largest family     : {max_size}")
    print(f"  Output             : {output_path}")


if __name__ == "__main__":
    main()
