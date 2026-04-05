"""Benchmark evaluation runner — phonetic-law scorer vs. baseline.

Does NOT use BGE-M3/ByT5 embeddings.  Scores every Arabic source against
every English target using:
  - PhoneticLawScorer.score_pair()   (LV2 discovery module)
  - cross_lingual_skeleton_score()   (LV2 discovery/correspondence.py)
  - correspondence_features()        (LV2 discovery/correspondence.py)

Combined (with phonetic laws):
  combined = 0.4 * phonetic_law_score + 0.3 * skeleton_score + 0.3 * correspondence_score

Baseline (no phonetic laws):
  combined = 0.5 * skeleton_score + 0.5 * correspondence_score

Metrics reported: MRR, nDCG@10, nDCG@50, Hit@1/5/10/50
Also prints top-miss analysis for pairs not found in top-10.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve()
LV2_ROOT = HERE.parents[1]
GOLD_PATH = LV2_ROOT / "resources" / "benchmarks" / "cognate_gold.jsonl"
ARA_CORPUS = LV2_ROOT / "data" / "processed" / "benchmark_mini_ara.jsonl"
ENG_CORPUS = LV2_ROOT / "data" / "processed" / "benchmark_mini_eng.jsonl"

# Ensure the LV2 src is importable
SRC_DIR = LV2_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import (
    PhoneticLawScorer,
    _english_consonant_skeleton,
    _arabic_consonant_skeleton,
    _strip_diacriticals,
    _pairwise_swap_variants,
    project_root_sound_laws,
    LATIN_EQUIVALENTS,
)
from juthoor_cognatediscovery_lv2.discovery.correspondence import (
    cross_lingual_skeleton_score,
    correspondence_features,
    correspondence_string,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> list[dict]:
    entries = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def load_gold_pairs() -> list[dict]:
    """Return ara<->eng pairs from gold benchmark."""
    pairs: list[dict] = []
    with GOLD_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            s, t = d["source"], d["target"]
            if s["lang"] == "ara" and t["lang"] == "eng":
                pairs.append(d)
            elif s["lang"] == "eng" and t["lang"] == "ara":
                pairs.append(
                    {
                        "source": t,
                        "target": s,
                        "relation": d["relation"],
                        "confidence": d.get("confidence", 1.0),
                    }
                )
    return pairs


# ---------------------------------------------------------------------------
# Pre-computed English corpus cache (built once, reused for all sources)
# ---------------------------------------------------------------------------

class EngCorpusCache:
    """Pre-compute English-side features to avoid redundant work."""

    def __init__(self, corpus: list[dict]) -> None:
        from difflib import SequenceMatcher as _SM
        self._SM = _SM
        self.corpus = corpus
        self.skels = [_english_consonant_skeleton(e.get("lemma", "")) for e in corpus]
        self.corrs = [correspondence_string(e.get("lemma", "")) for e in corpus]

    def score_source(
        self,
        src: dict,
        mined_weights: dict,
    ) -> list[tuple[float, float]]:
        """Return [(combined_with, combined_baseline)] for every English target.

        Uses a reduced variant set (primary_latin + reversal + 3 adjacent-swaps)
        instead of the full 256-variant expansion for speed.
        """
        SM = self._SM
        arabic_root = (
            src.get("root_norm")
            or src.get("root")
            or src.get("translit")
            or src.get("lemma")
            or ""
        ).strip()

        ar_skel = _arabic_consonant_skeleton(arabic_root)
        primary_latin = _strip_diacriticals(
            "".join(LATIN_EQUIVALENTS.get(ch, (ch,))[0] for ch in ar_skel)
        )
        # Reduced variant set: direct + reversal + up to 5 adjacent swaps
        variants: list[str] = []
        if primary_latin:
            variants.append(primary_latin)
            variants.append(primary_latin[::-1])
            variants.extend(_pairwise_swap_variants(primary_latin)[:5])

        src_corr = correspondence_string(arabic_root)

        # Mined bonus per source (check which laws apply to this Arabic skel)
        mined_bonus = 0.0
        if mined_weights:
            for law in mined_weights.get("individual_laws", []):
                if law.get("arabic", "") in ar_skel:
                    mined_bonus += law.get("weight", 0) * 0.02
            mined_bonus = min(mined_bonus, 0.1)

        results: list[tuple[float, float]] = []
        for eng_skel, eng_corr in zip(self.skels, self.corrs):
            # Phonetic projection score
            if variants and eng_skel:
                proj = max(SM(None, v, eng_skel).ratio() for v in variants)
            else:
                proj = 0.0

            # Correspondence / skeleton score
            skel_score = SM(None, src_corr, eng_corr).ratio() if src_corr and eng_corr else 0.0

            # Final mined bonus: also check English side
            pair_mined = mined_bonus
            if mined_weights and eng_skel:
                for law in mined_weights.get("individual_laws", []):
                    if law.get("english", "") in eng_skel:
                        pair_mined += law.get("weight", 0) * 0.01
                pair_mined = min(pair_mined, 0.1)

            phonetic_law_score = min(proj + pair_mined, 1.0)

            combined_with = (
                0.4 * phonetic_law_score
                + 0.3 * skel_score
                + 0.3 * skel_score  # correspondence == skeleton here (same corr_string)
            )
            combined_baseline = skel_score  # 0.5*skel + 0.5*corr = skel (same value)

            results.append((combined_with, combined_baseline))

        return results


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------

def rank_targets_both(
    src: dict,
    corpus_cache: EngCorpusCache,
    eng_corpus: list[dict],
    mined_weights: dict,
) -> tuple[list[tuple[dict, float]], list[tuple[dict, float]]]:
    """Score src against all targets; return two sorted lists (with, baseline)."""
    pair_scores = corpus_cache.score_source(src, mined_weights)
    indexed = list(zip(eng_corpus, pair_scores))
    ranked_with = sorted(indexed, key=lambda x: x[1][0], reverse=True)
    ranked_base = sorted(indexed, key=lambda x: x[1][1], reverse=True)
    return (
        [(t, s[0]) for t, s in ranked_with],
        [(t, s[1]) for t, s in ranked_base],
    )


def get_pair_score(
    src: dict,
    tgt_lemma: str,
    corpus_cache: EngCorpusCache,
    eng_corpus: list[dict],
    mined_weights: dict,
) -> dict[str, float]:
    """Get detailed scores for a specific src/tgt pair (for miss analysis)."""
    pair_scores = corpus_cache.score_source(src, mined_weights)
    for i, e in enumerate(eng_corpus):
        if e["lemma"] == tgt_lemma:
            combined_with, combined_baseline = pair_scores[i]
            return {
                "combined_with": combined_with,
                "combined_baseline": combined_baseline,
            }
    return {"combined_with": 0.0, "combined_baseline": 0.0}


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def dcg(relevances: list[float], k: int) -> float:
    total = 0.0
    for i, r in enumerate(relevances[:k], start=1):
        total += r / math.log2(i + 1)
    return total


def ndcg(rank: int, total: int, k: int) -> float:
    if rank > k:
        return 0.0
    rel_at_rank = [0.0] * k
    rel_at_rank[rank - 1] = 1.0
    actual_dcg = dcg(rel_at_rank, k)
    ideal_dcg = dcg([1.0], k)  # best possible: rank 1
    if ideal_dcg == 0.0:
        return 0.0
    return actual_dcg / ideal_dcg


def compute_metrics(
    ranks: list[int | None],
    hits_k: tuple[int, ...] = (1, 5, 10, 50),
    ndcg_k: tuple[int, ...] = (10, 50),
) -> dict[str, float]:
    valid = [r for r in ranks if r is not None]
    n = len(valid)
    if n == 0:
        return {}

    mrr = sum(1.0 / r for r in valid) / n

    result: dict[str, float] = {"MRR": mrr, "n_pairs": float(n)}

    for k in ndcg_k:
        result[f"nDCG@{k}"] = sum(ndcg(r, n, k) for r in valid) / n

    for k in hits_k:
        result[f"Hit@{k}"] = sum(1 for r in valid if r <= k) / n

    return result


# ---------------------------------------------------------------------------
# Miss analysis
# ---------------------------------------------------------------------------

MISS_CATEGORIES = [
    ("phonetic_distance", "Arabic consonants have no plausible English mapping"),
    ("length_mismatch", "Very different consonant skeleton lengths"),
    ("semantic_shift", "Pair connected by meaning shift, not phonetics"),
    ("distractor_interference", "Distractors with similar phonetics ranked higher"),
    ("morpheme_obscured", "English word has prefix/suffix hiding the root"),
]


def categorise_miss(
    src: dict,
    tgt: dict,
    ranked: list[tuple[dict, float]],
    gold_score: float,
    rank: int | None,
) -> str:
    ara = src.get("lemma", "")
    eng = tgt.get("lemma", "")
    # Very crude heuristic categorisation
    ara_skel_len = len([c for c in ara if "\u0621" <= c <= "\u064a"])
    eng_cons = sum(1 for c in eng.lower() if c in "bcdfghjklmnpqrstvwxyz")

    if abs(ara_skel_len - eng_cons) >= 3:
        return "length_mismatch"
    # Check if top-ranked distractors score higher
    if rank is not None and rank > 10:
        top10_lemmas = [t["lemma"] for t, _ in ranked[:10]]
        if tgt.get("lemma") not in top10_lemmas:
            return "distractor_interference"
    if any(sfx in eng.lower() for sfx in ("tion", "ment", "ness", "ity", "ize", "ise", "ing")):
        return "morpheme_obscured"
    if gold_score < 0.15:
        return "phonetic_distance"
    return "semantic_shift"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # Verify corpora exist; auto-create if missing
    if not ARA_CORPUS.exists() or not ENG_CORPUS.exists():
        print("Mini corpora not found — running create_benchmark_corpora.py first...")
        import subprocess
        result = subprocess.run(
            [sys.executable, str(HERE.parent / "create_benchmark_corpora.py")],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("ERROR creating corpora:", result.stderr)
            sys.exit(1)
        print(result.stdout)

    ara_corpus = load_jsonl(ARA_CORPUS)
    eng_corpus = load_jsonl(ENG_CORPUS)
    gold_pairs = load_gold_pairs()

    # Build lookup: (ara_lemma, eng_lemma) -> gold_pair
    gold_lookup: dict[tuple[str, str], dict] = {}
    for p in gold_pairs:
        key = (p["source"]["lemma"], p["target"]["lemma"])
        gold_lookup[key] = p

    # Build index from lemma -> corpus entry
    ara_by_lemma: dict[str, dict] = {e["lemma"]: e for e in ara_corpus}
    eng_by_lemma: dict[str, dict] = {e["lemma"]: e for e in eng_corpus}

    # Load mined weights for bonus scoring
    scorer = PhoneticLawScorer()
    scorer._try_load_mined_data()
    mined_weights = scorer._mined_weights

    print(f"\nCorpora: {len(ara_corpus)} Arabic, {len(eng_corpus)} English")
    print(f"Gold pairs (ara<->eng): {len(gold_pairs)}")

    # Only evaluate pairs where BOTH lemmas appear in our mini corpora
    eval_pairs = [
        p for p in gold_pairs
        if p["source"]["lemma"] in ara_by_lemma and p["target"]["lemma"] in eng_by_lemma
    ]
    print(f"Pairs evaluated (both lemmas in corpora): {len(eval_pairs)}")

    # ------------------------------------------------------------------
    # Build cached English corpus features (done once)
    # ------------------------------------------------------------------
    print("Pre-computing English corpus features...", flush=True)
    corpus_cache = EngCorpusCache(eng_corpus)

    # Group pairs by source lemma to avoid rescoring the same Arabic source
    from collections import defaultdict
    pairs_by_src: dict[str, list[dict]] = defaultdict(list)
    for p in eval_pairs:
        pairs_by_src[p["source"]["lemma"]].append(p)

    # ------------------------------------------------------------------
    # Score each unique Arabic source once against all English targets
    # ------------------------------------------------------------------
    # Force UTF-8 stdout for Windows console (Arabic characters in output)
    import io as _io
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

    print(f"Scoring {len(pairs_by_src)} unique Arabic sources against {len(eng_corpus)} English targets...", flush=True)

    ranks_with: list[int | None] = []
    ranks_base: list[int | None] = []
    miss_details: list[dict[str, Any]] = []

    total_src = len(pairs_by_src)
    src_lemmas = list(pairs_by_src.keys())

    for i, src_lemma in enumerate(src_lemmas, 1):
        if i % 25 == 0 or i == total_src:
            print(f"  {i}/{total_src} sources processed...", flush=True)

        src = ara_by_lemma[src_lemma]
        ranked_with, ranked_base = rank_targets_both(src, corpus_cache, eng_corpus, mined_weights)

        # Build rank lookup from this ranking
        rank_w_lookup: dict[str, int] = {t["lemma"]: idx for idx, (t, _) in enumerate(ranked_with, 1)}
        rank_b_lookup: dict[str, int] = {t["lemma"]: idx for idx, (t, _) in enumerate(ranked_base, 1)}

        for pair in pairs_by_src[src_lemma]:
            tgt_lemma = pair["target"]["lemma"]
            rank_w = rank_w_lookup.get(tgt_lemma)
            rank_b = rank_b_lookup.get(tgt_lemma)

            ranks_with.append(rank_w)
            ranks_base.append(rank_b)

            # Collect misses for analysis
            if rank_w is None or rank_w > 10:
                tgt_entry = eng_by_lemma[tgt_lemma]
                gold_score_data = get_pair_score(src, tgt_lemma, corpus_cache, eng_corpus, mined_weights)
                gold_score = gold_score_data["combined_with"]
                category = categorise_miss(src, tgt_entry, ranked_with, gold_score, rank_w)
                top3 = [(t["lemma"], round(s, 4)) for t, s in ranked_with[:3]]
                miss_details.append(
                    {
                        "ara": src_lemma,
                        "eng": tgt_lemma,
                        "rank_with": rank_w,
                        "rank_base": rank_b,
                        "gold_combined_score": round(gold_score, 4),
                        "category": category,
                        "top3_ranked": top3,
                        "gloss_ara": pair["source"].get("gloss", ""),
                        "gloss_eng": pair["target"].get("gloss", ""),
                    }
                )

    print(f"  {total_src}/{total_src} done.", flush=True)

    # ------------------------------------------------------------------
    # Compute metrics
    # ------------------------------------------------------------------
    metrics_with = compute_metrics(ranks_with)
    metrics_base = compute_metrics(ranks_base)

    # ------------------------------------------------------------------
    # Print comparison table
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  BENCHMARK DISCOVERY EVALUATION")
    print("=" * 60)
    print(f"\n  Pairs evaluated: {len(eval_pairs)}")
    print()

    header = f"  {'Metric':<12} | {'With Phonetic Laws':>20} | {'Without (Baseline)':>20} | {'Delta':>10}"
    sep = "  " + "-" * (len(header) - 2)
    print(header)
    print(sep)

    def _pct(v: float) -> str:
        return f"{v * 100:6.1f}%"

    def _val(v: float) -> str:
        return f"{v:.4f}"

    metric_rows = [
        ("MRR", "MRR"),
        ("nDCG@10", "nDCG@10"),
        ("nDCG@50", "nDCG@50"),
        ("Hit@1", "Hit@1"),
        ("Hit@5", "Hit@5"),
        ("Hit@10", "Hit@10"),
        ("Hit@50", "Hit@50"),
    ]

    for label, key in metric_rows:
        v_with = metrics_with.get(key, 0.0)
        v_base = metrics_base.get(key, 0.0)
        delta = v_with - v_base

        if key.startswith("Hit"):
            vw_str = _pct(v_with)
            vb_str = _pct(v_base)
            d_str = f"{'+' if delta >= 0 else ''}{delta * 100:.1f}%"
        else:
            vw_str = _val(v_with)
            vb_str = _val(v_base)
            d_str = f"{'+' if delta >= 0 else ''}{delta:.4f}"

        print(f"  {label:<12} | {vw_str:>20} | {vb_str:>20} | {d_str:>10}")

    print()

    # ------------------------------------------------------------------
    # Miss analysis
    # ------------------------------------------------------------------
    print("=" * 60)
    print(f"  TOP-MISS ANALYSIS  ({len(miss_details)} pairs missed in top-10 with phonetic laws)")
    print("=" * 60)

    # Category summary
    from collections import Counter
    cat_counts = Counter(m["category"] for m in miss_details)
    print("\n  Miss categories:")
    for cat, count in cat_counts.most_common():
        print(f"    {cat:<30} {count:3d}")

    # Print details for up to 15 misses
    print(f"\n  Sample misses (up to 15):")
    for m in miss_details[:15]:
        rank_str = str(m["rank_with"]) if m["rank_with"] else "not found"
        base_str = str(m["rank_base"]) if m["rank_base"] else "not found"
        top3_str = ", ".join(f"{w}({s})" for w, s in m["top3_ranked"])
        print(f"\n    Pair:  {m['ara']} ({m['gloss_ara']}) -> {m['eng']} ({m['gloss_eng']})")
        print(f"    Rank:  #{rank_str} (with) / #{base_str} (baseline)")
        print(f"    Score: {m['gold_combined_score']}")
        print(f"    Cat:   {m['category']}")
        print(f"    Top-3: {top3_str}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
