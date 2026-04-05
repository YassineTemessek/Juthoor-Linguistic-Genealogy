"""Score gold benchmark pairs directly and analyze findability."""
import json, sys, collections, random
from pathlib import Path

LV2_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LV2_ROOT / "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def main():
    from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScorer
    scorer = MultiMethodScorer()

    # Load gold pairs (ara-eng only)
    gold_path = LV2_ROOT / "resources/benchmarks/cognate_gold.jsonl"
    gold_pairs = []
    with open(gold_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            d = json.loads(line)
            src = d.get("source", {})
            tgt = d.get("target", {})
            if src.get("lang", "").startswith("ara") and tgt.get("lang") == "eng":
                gold_pairs.append(d)

    print(f"Total ara-eng gold pairs: {len(gold_pairs)}")

    # Sample 100 for speed
    random.seed(42)
    sample = random.sample(gold_pairs, min(100, len(gold_pairs)))

    print(f"Scoring {len(sample)} sampled gold pairs...\n")

    results = []
    for i, gp in enumerate(sample):
        src = gp["source"]
        tgt = gp["target"]
        # Build scorer-compatible dicts
        src_dict = {"lemma": src.get("lemma", ""), "root": src.get("root", src.get("lemma", "")), "root_norm": src.get("root", src.get("lemma", "")), "meaning_text": src.get("gloss", "")}
        tgt_dict = {"lemma": tgt.get("lemma", ""), "ipa": tgt.get("ipa", ""), "meaning_text": tgt.get("gloss", "")}

        result = scorer.score_pair(src_dict, tgt_dict)
        results.append({
            "src": src.get("lemma", ""),
            "tgt": tgt.get("lemma", ""),
            "score": result.best_score,
            "method": result.best_method,
            "fired": len(result.methods_that_fired),
            "confidence": gp.get("confidence", 0),
        })
        if (i+1) % 20 == 0:
            print(f"  Scored {i+1}/{len(sample)}...")

    # Analysis
    scores = [r["score"] for r in results]
    scores.sort()

    print(f"\n{'='*60}")
    print(f"GOLD PAIR SCORING ANALYSIS")
    print(f"{'='*60}")

    print(f"\nScore distribution:")
    zero = sum(1 for s in scores if s == 0)
    low = sum(1 for s in scores if 0 < s < 0.55)
    mid = sum(1 for s in scores if 0.55 <= s < 0.70)
    high = sum(1 for s in scores if 0.70 <= s < 0.85)
    very_high = sum(1 for s in scores if s >= 0.85)
    print(f"  score = 0.0 (missed):     {zero} ({100*zero/len(scores):.0f}%)")
    print(f"  0.0 < score < 0.55:       {low} ({100*low/len(scores):.0f}%)")
    print(f"  0.55 <= score < 0.70:     {mid} ({100*mid/len(scores):.0f}%)")
    print(f"  0.70 <= score < 0.85:     {high} ({100*high/len(scores):.0f}%)")
    print(f"  score >= 0.85:            {very_high} ({100*very_high/len(scores):.0f}%)")

    print(f"\nMethod distribution for scored pairs (score > 0):")
    method_counts = collections.Counter(r["method"] for r in results if r["score"] > 0)
    for m, c in method_counts.most_common():
        print(f"  {m}: {c}")

    print(f"\nTop 10 highest-scoring gold pairs:")
    top = sorted(results, key=lambda r: -r["score"])[:10]
    for r in top:
        print(f"  {r['src']} -> {r['tgt']}: {r['score']:.3f} ({r['method']}, {r['fired']} methods)")

    print(f"\nBottom 10 (missed or lowest):")
    bottom = sorted(results, key=lambda r: r["score"])[:10]
    for r in bottom:
        print(f"  {r['src']} -> {r['tgt']}: {r['score']:.3f} ({r['method'] or 'NONE'})")

    # Save full results
    out_path = LV2_ROOT / "outputs" / "gold_pair_analysis.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nFull results saved to {out_path}")

if __name__ == "__main__":
    main()
