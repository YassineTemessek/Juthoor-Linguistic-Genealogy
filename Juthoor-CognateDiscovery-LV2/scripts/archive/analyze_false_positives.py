"""Analyze top false positives in PhoneticLawScorer.

Steps:
1. Load gold benchmark (ara<->eng pairs)
2. Generate 300 negative pairs (shuffle)
3. Score all with PhoneticLawScorer
4. Find the top 20 false positives (highest-scoring negatives)
5. Print: pair, score, consonant classes, diversity
"""
from __future__ import annotations

import io
import json
import random
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent
LV2_ROOT = SCRIPT_DIR.parent
SRC_ROOT = LV2_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import PhoneticLawScorer
from juthoor_cognatediscovery_lv2.discovery.correspondence import _CLASS_MAP

BENCHMARK_DIR = LV2_ROOT / "resources" / "benchmarks"
GOLD_PATH = BENCHMARK_DIR / "cognate_gold.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def get_classes(skeleton: str) -> set[str]:
    """Get the set of consonant class labels for a skeleton string."""
    classes = {_CLASS_MAP.get(c, "?") for c in skeleton if c in _CLASS_MAP}
    classes.discard("?")
    return classes


def main() -> None:
    print("Loading gold benchmark...")
    gold_all = load_jsonl(GOLD_PATH)
    gold_ara_eng = [
        p for p in gold_all
        if p.get("source", {}).get("lang") == "ara"
        and p.get("target", {}).get("lang") == "eng"
    ]
    print(f"Gold ara<->eng: {len(gold_ara_eng)} pairs")

    # Generate 300 negative pairs
    rng = random.Random(42)
    arabic_sources = [p["source"] for p in gold_ara_eng]
    english_targets = [p["target"] for p in gold_ara_eng]

    # Create a larger pool by shuffling with multiple offsets
    negatives_raw = []
    gold_pairs_set = {
        (p["source"]["lemma"], p["target"]["lemma"]) for p in gold_ara_eng
    }
    for offset in range(1, 20):
        for i, src in enumerate(arabic_sources):
            tgt = english_targets[(i + offset) % len(english_targets)]
            pair_key = (src["lemma"], tgt["lemma"])
            if pair_key not in gold_pairs_set:
                negatives_raw.append({"source": src, "target": tgt})
            if len(negatives_raw) >= 300:
                break
        if len(negatives_raw) >= 300:
            break

    negatives_raw = negatives_raw[:300]
    print(f"Negatives generated: {len(negatives_raw)}")

    print("\nScoring negatives...")
    scorer = PhoneticLawScorer()
    scored = []
    for p in negatives_raw:
        src = p["source"]
        tgt = p["target"]
        result = scorer.score_pair(src, tgt)
        det = result.get("projection_details", {})
        ar_skel = det.get("arabic_skeleton", "")
        eng_skel = det.get("english_skeleton", "")
        ar_classes = get_classes(ar_skel)
        eng_classes = get_classes(eng_skel)
        shared_classes = ar_classes & eng_classes
        diversity = det.get("consonant_diversity", len(shared_classes))
        scored.append({
            "ara": src.get("lemma", ""),
            "eng": tgt.get("lemma", ""),
            "score": result["phonetic_law_score"],
            "ar_skel": ar_skel,
            "eng_skel": eng_skel,
            "ar_classes": ar_classes,
            "eng_classes": eng_classes,
            "shared_classes": shared_classes,
            "diversity": diversity,
            "diversity_penalty": det.get("diversity_penalty_applied", False),
            "freq_penalty": det.get("freq_penalty_applied", False),
        })

    # Sort by score descending — top = worst false positives
    scored.sort(key=lambda x: x["score"], reverse=True)

    # Stats
    bonus_threshold = 0.55  # V6 sigmoid threshold
    fps = [s for s in scored if s["score"] > bonus_threshold]
    fp_rate = len(fps) / len(scored) * 100 if scored else 0.0
    print(f"\nFalse positive rate (score > {bonus_threshold}): {fp_rate:.1f}% ({len(fps)}/{len(scored)})")

    print("\n" + "=" * 70)
    print("  TOP 20 FALSE POSITIVES (highest-scoring negatives)")
    print("=" * 70)
    print(f"{'#':>3}  {'Arabic':>20}  {'English':<20}  {'Score':>6}  {'Div':>3}  {'AR-cls':>8}  {'ENG-cls':>8}  {'Shared'}")
    print("-" * 100)
    for i, r in enumerate(scored[:20], 1):
        shared_str = ",".join(sorted(r["shared_classes"])) or "none"
        ar_str = ",".join(sorted(r["ar_classes"])) or "?"
        eng_str = ",".join(sorted(r["eng_classes"])) or "?"
        flags = ""
        if r["diversity_penalty"]:
            flags += "[DIV_PEN]"
        if r["freq_penalty"]:
            flags += "[FREQ_PEN]"
        print(
            f"{i:>3}. {r['ara']:>20}  {r['eng']:<20}  {r['score']:>6.4f}  "
            f"{r['diversity']:>3}  {ar_str:>8}  {eng_str:>8}  {shared_str}  {flags}"
        )

    print("\n" + "=" * 70)
    print("  DIVERSITY DISTRIBUTION (all negatives)")
    print("=" * 70)
    from collections import Counter
    div_counts = Counter(r["diversity"] for r in scored)
    for div_val in sorted(div_counts.keys()):
        n = div_counts[div_val]
        high = sum(1 for r in scored if r["diversity"] == div_val and r["score"] > bonus_threshold)
        print(f"  diversity={div_val}: {n} pairs, {high} above threshold ({high/n*100:.1f}% FP rate within group)")

    print("\nDone.")


if __name__ == "__main__":
    main()
