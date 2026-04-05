"""Null model permutation test for statistical validation of cognate discovery."""
from __future__ import annotations
import argparse, json, random, sys, time, math
from pathlib import Path

LV2_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = LV2_ROOT.parent
sys.path.insert(0, str(LV2_ROOT / "src"))

ARABIC_CORPUS = LV2_ROOT / "data/processed/arabic/quran_lemmas_enriched.jsonl"

def load_arabic(limit=50):
    entries = []
    with open(ARABIC_CORPUS, encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            row = json.loads(line)
            if len(row.get("lemma","")) >= 2:
                entries.append(row)
                if len(entries) >= limit: break
    return entries

def load_english(limit=500):
    path = LV2_ROOT / "data/processed/english/english_ipa_merged_pos.jsonl"
    total = sum(1 for l in open(path, encoding="utf-8") if l.strip())
    stride = max(1, total // (limit * 2))
    entries, seen, n = [], set(), 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            n += 1
            if stride > 1 and (n-1) % stride != 0: continue
            row = json.loads(line)
            lemma = (row.get("lemma","") or "").strip().lower()
            if not lemma or len(lemma) <= 2 or lemma in seen: continue
            if not lemma.replace("-","").replace("'","").isalpha(): continue
            seen.add(lemma)
            entries.append(row)
    return entries

def run_scoring(arabic, english, scorer, threshold):
    count = 0
    for ar in arabic:
        for en in english:
            r = scorer.score_pair(ar, en)
            if r.best_score >= threshold:
                count += 1
    return count

def run_null(arabic, english, scorer, threshold):
    shuffled = [dict(ar) for ar in arabic]
    roots = [ar.get("root", ar.get("root_norm", ar.get("lemma",""))) for ar in shuffled]
    random.shuffle(roots)
    for ar, root in zip(shuffled, roots):
        ar["root"] = root
        ar["root_norm"] = root
    return run_scoring(shuffled, english, scorer, threshold)

def main():
    parser = argparse.ArgumentParser(description="Null model permutation test")
    parser.add_argument("--arabic-limit", type=int, default=30)
    parser.add_argument("--english-limit", type=int, default=200)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--threshold", type=float, default=0.55)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    random.seed(args.seed)

    from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScorer
    scorer = MultiMethodScorer()

    print("Loading corpora...")
    arabic = load_arabic(args.arabic_limit)
    english = load_english(args.english_limit)
    print(f"  Arabic: {len(arabic)}, English: {len(english)}")
    total_pairs = len(arabic) * len(english)
    print(f"  Total pairs: {total_pairs:,}")

    print(f"\nReal run (threshold={args.threshold})...")
    t0 = time.time()
    real_count = run_scoring(arabic, english, scorer, args.threshold)
    real_time = time.time() - t0
    print(f"  Real matches: {real_count} ({real_time:.1f}s)")

    print(f"\nNull model ({args.iterations} iterations)...")
    null_counts = []
    for i in range(args.iterations):
        t0 = time.time()
        nc = run_null(arabic, english, scorer, args.threshold)
        elapsed = time.time() - t0
        null_counts.append(nc)
        print(f"  Iteration {i+1}: {nc} matches ({elapsed:.1f}s)")

    null_mean = sum(null_counts) / len(null_counts)
    null_std = (sum((x - null_mean)**2 for x in null_counts) / max(len(null_counts)-1, 1)) ** 0.5
    z_score = (real_count - null_mean) / max(null_std, 0.001)
    effect = real_count / max(null_mean, 0.001)

    # p-value approximation
    try:
        from scipy.stats import norm
        p_value = 1 - norm.cdf(z_score)
    except ImportError:
        # Abramowitz & Stegun approximation
        t = 1.0 / (1.0 + 0.2316419 * abs(z_score))
        d = 0.3989422804014327
        p = d * math.exp(-z_score*z_score/2.0) * t * (0.319381530 + t*(-0.356563782 + t*(1.781477937 + t*(-1.821255978 + t*1.330274429))))
        p_value = p if z_score > 0 else 1.0 - p

    print(f"\n{'='*50}")
    print(f"Null Model Permutation Test")
    print(f"{'='*50}")
    print(f"Real matches:     {real_count}")
    print(f"Null model:       mean={null_mean:.1f} +/- {null_std:.1f}")
    print(f"Z-score:          {z_score:.1f}")
    print(f"Effect size:      {effect:.1f}x expected by chance")
    print(f"p-value:          {'< 0.001' if p_value < 0.001 else f'{p_value:.4f}'}")
    print(f"RESULT:           {'SIGNIFICANT -- matches exceed random chance' if z_score > 2.58 else 'NOT SIGNIFICANT'}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
