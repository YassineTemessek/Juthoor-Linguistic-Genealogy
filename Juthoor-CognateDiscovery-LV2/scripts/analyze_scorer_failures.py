"""Analyze bottom-scoring gold ara<->eng pairs to identify failure modes."""
from __future__ import annotations

import io
import json
import sys
from collections import Counter
from pathlib import Path

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent
LV2_ROOT = SCRIPT_DIR.parent
SRC_ROOT = LV2_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import PhoneticLawScorer

BENCHMARK_DIR = LV2_ROOT / "resources" / "benchmarks"
GOLD_PATH = BENCHMARK_DIR / "cognate_gold.jsonl"

# Known prefixes/suffixes that obscure the root
KNOWN_PREFIXES = {
    "sub", "ex", "re", "pre", "de", "dis", "in", "un", "im", "auto",
    "con", "com", "geo", "es", "per", "pro", "trans", "over", "out",
    "mis", "fore", "anti", "semi", "hyper", "super", "inter",
}
KNOWN_SUFFIXES = {
    "gen", "less", "logy", "ology", "tion", "sion", "ment", "ous",
    "al", "ive", "er", "or", "fy", "ify", "ism", "ist", "ize", "ise",
    "ance", "ence", "ness", "ful", "ward", "ship", "hood", "dom",
    "age", "ure", "ary", "ory", "ity",
}

# Pairs known to be metathesis-mediated (consonant order swap)
METATHESIS_GLOSSES = {"path/track", "track", "bull", "steer/bull", "leg", "arm"}


def has_morpheme_affix(word: str) -> tuple[str, str, str]:
    """Return (prefix, stem, suffix). Empty string if not found."""
    w = word.lower()
    for p in sorted(KNOWN_PREFIXES, key=len, reverse=True):
        if w.startswith(p) and len(w) > len(p) + 2:
            stem = w[len(p):]
            # Check if the remaining part also has a suffix
            for s in sorted(KNOWN_SUFFIXES, key=len, reverse=True):
                if stem.endswith(s) and len(stem) > len(s) + 1:
                    return p, stem[: -len(s)], s
            return p, stem, ""
    for s in sorted(KNOWN_SUFFIXES, key=len, reverse=True):
        if w.endswith(s) and len(w) > len(s) + 2:
            return "", w[: -len(s)], s
    return "", w, ""


def categorize_failure(pair: dict, score: float, details: dict) -> str:
    src = pair.get("source", {})
    tgt = pair.get("target", {})
    ara = src.get("lemma", "")
    eng = tgt.get("lemma", "").lower()
    gloss = tgt.get("gloss", "").lower() + " " + src.get("gloss", "").lower()
    notes = pair.get("notes", "").lower()
    ar_skel = details.get("arabic_skeleton", "")
    eng_skel = details.get("english_skeleton", "")

    # short_root: Arabic skeleton is 1-2 consonants
    if len(ar_skel) <= 2:
        return "short_root"

    # metathesis: hints in notes or gloss, or reversed skeleton scores well
    if "metathesis" in notes or any(g in gloss for g in METATHESIS_GLOSSES):
        return "metathesis"
    # Check if reversing arabic skel gives a better match
    if ar_skel and eng_skel:
        from difflib import SequenceMatcher
        primary_latin = details.get("primary_latin", "")
        if primary_latin:
            rev_score = SequenceMatcher(None, primary_latin[::-1], eng_skel).ratio()
            fwd_score = SequenceMatcher(None, primary_latin, eng_skel).ratio()
            if rev_score > fwd_score + 0.1 and rev_score > 0.3:
                return "metathesis"

    # morpheme: word has a known affix that hides the root
    prefix, stem, suffix = has_morpheme_affix(eng)
    if prefix or suffix:
        return "morpheme"

    # multi_hop: chain through Latin/French - often indicated in notes
    if any(kw in notes for kw in ("latin", "french", "greek", "via", "from old", "proto")):
        return "multi_hop"
    # If English word is > 2x the Arabic skeleton in consonants, likely multi-hop
    if eng_skel and ar_skel and len(eng_skel) > len(ar_skel) * 2:
        return "multi_hop"

    # semantic_only: forms very different, no morphological or sound connection
    return "semantic_only"


def main() -> None:
    print("Loading gold benchmark...")
    with open(GOLD_PATH, encoding="utf-8") as f:
        gold_all = [json.loads(line) for line in f if line.strip()]

    ara_eng = [
        p for p in gold_all
        if p.get("source", {}).get("lang") == "ara"
        and p.get("target", {}).get("lang") == "eng"
    ]
    print(f"Total ara<->eng gold pairs: {len(ara_eng)}")

    scorer = PhoneticLawScorer()
    scored = []
    for p in ara_eng:
        src = p.get("source", {})
        tgt = p.get("target", {})
        result = scorer.score_pair(src, tgt)
        scored.append({
            "pair": p,
            "score": result["phonetic_law_score"],
            "details": result.get("projection_details", {}),
            "best_projection": result.get("best_projection", ""),
        })

    scored.sort(key=lambda x: x["score"])

    print("\n" + "=" * 70)
    print("  BOTTOM 30 SCORING PAIRS")
    print("=" * 70)
    print(f"{'#':3s}  {'Arabic':20s}  {'English':20s}  {'Score':7s}  {'ar_skel':10s}  {'eng_skel':12s}  {'Category'}")
    print("-" * 90)

    categories = []
    bottom30 = scored[:30]
    for i, entry in enumerate(bottom30, 1):
        pair = entry["pair"]
        src = pair.get("source", {})
        tgt = pair.get("target", {})
        det = entry["details"]
        cat = categorize_failure(pair, entry["score"], det)
        categories.append(cat)
        ar_skel = det.get("arabic_skeleton", "")
        eng_skel = det.get("english_skeleton", "")
        proj = det.get("projection_match", 0)
        direct = det.get("direct_match", 0)
        print(
            f"{i:3d}  {src.get('lemma',''):20s}  {tgt.get('lemma',''):20s}  "
            f"{entry['score']:7.4f}  {ar_skel:10s}  {eng_skel:12s}  {cat}"
        )
        # Print sub-scores for diagnosis
        print(
            f"       proj={proj:.3f}  direct={direct:.3f}  "
            f"meta={det.get('metathesis_match', 0):.3f}  "
            f"notes={pair.get('notes','')[:60]}"
        )

    print("\n" + "=" * 70)
    print("  FAILURE CATEGORY DISTRIBUTION (bottom 30)")
    print("=" * 70)
    dist = Counter(categories)
    for cat, count in dist.most_common():
        pct = count / len(categories) * 100
        print(f"  {cat:20s}: {count:3d}  ({pct:.1f}%)")

    print("\n" + "=" * 70)
    print("  SCORE DISTRIBUTION SUMMARY (all ara<->eng pairs)")
    print("=" * 70)
    all_scores = [e["score"] for e in scored]
    import statistics
    print(f"  N pairs:      {len(all_scores)}")
    print(f"  Mean score:   {statistics.mean(all_scores):.4f}")
    print(f"  Median:       {statistics.median(all_scores):.4f}")
    print(f"  Min:          {min(all_scores):.4f}")
    print(f"  Max:          {max(all_scores):.4f}")
    thresholds = [0.2, 0.3, 0.4, 0.5, 0.6]
    for t in thresholds:
        n = sum(1 for s in all_scores if s >= t)
        print(f"  >= {t:.1f}:        {n:4d}  ({n/len(all_scores)*100:.1f}%)")

    print("\n" + "=" * 70)
    print("  ALL CATEGORY DISTRIBUTION (all ara<->eng pairs)")
    print("=" * 70)
    all_cats = [
        categorize_failure(e["pair"], e["score"], e["details"])
        for e in scored
        if e["score"] < 0.35  # focus on low-scoring pairs
    ]
    dist_all = Counter(all_cats)
    print(f"  (Pairs with score < 0.35: {len(all_cats)})")
    for cat, count in dist_all.most_common():
        pct = count / len(all_cats) * 100 if all_cats else 0
        print(f"  {cat:20s}: {count:3d}  ({pct:.1f}%)")


if __name__ == "__main__":
    main()
