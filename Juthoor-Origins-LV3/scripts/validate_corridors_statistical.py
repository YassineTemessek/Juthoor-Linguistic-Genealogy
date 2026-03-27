"""Per-corridor statistical validation via permutation test."""
import json, random, sys, time, math, collections
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LV2_ROOT = REPO_ROOT / "Juthoor-CognateDiscovery-LV2"
sys.path.insert(0, str(LV2_ROOT / "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ARABIC_CORPUS = LV2_ROOT / "data/processed/arabic/quran_lemmas_enriched.jsonl"

CORRIDOR_METHOD_MAP = {
    "C01_guttural": "guttural_projection",
    "C02_emphatic": "emphatic_collapse",
    "C03_article": "article_detection",
    "C04_metathesis": "metathesis",
    "C05_position": "position_weighted",
    "C06_skeleton": "direct_skeleton",
    "C07_morpheme": "morpheme_decomposition",
    "C08_multihop": "multi_hop_chain",
    "C10_reverse": "reverse_root",
}

def load_arabic(limit=20):
    entries = []
    with open(ARABIC_CORPUS, encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            row = json.loads(line)
            if len(row.get("lemma","")) >= 2:
                entries.append(row)
                if len(entries) >= limit: break
    return entries

def load_english(limit=150):
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

def count_by_method(arabic, english, scorer, threshold=0.55):
    """Count matches above threshold, broken down by best_method."""
    method_counts = collections.Counter()
    for ar in arabic:
        for en in english:
            r = scorer.score_pair(ar, en)
            if r.best_score >= threshold:
                method_counts[r.best_method] += 1
    return method_counts

def main():
    random.seed(42)
    from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScorer
    scorer = MultiMethodScorer()

    print("Loading corpora...")
    arabic = load_arabic(15)
    english = load_english(100)
    print(f"  Arabic: {len(arabic)}, English: {len(english)}")

    print("\nReal run...")
    t0 = time.time()
    real_counts = count_by_method(arabic, english, scorer)
    print(f"  Done in {time.time()-t0:.1f}s")

    print("\nNull run (shuffled roots)...")
    shuffled = [dict(ar) for ar in arabic]
    roots = [ar.get("root", ar.get("root_norm", ar.get("lemma",""))) for ar in shuffled]
    random.shuffle(roots)
    for ar, root in zip(shuffled, roots):
        ar["root"] = root
        ar["root_norm"] = root
    t0 = time.time()
    null_counts = count_by_method(shuffled, english, scorer)
    print(f"  Done in {time.time()-t0:.1f}s")

    print(f"\n{'='*70}")
    print(f"PER-CORRIDOR STATISTICAL COMPARISON")
    print(f"{'='*70}")
    print(f"{'Corridor':<20} {'Method':<25} {'Real':>6} {'Null':>6} {'Ratio':>8} {'Signal?':<10}")
    print("-" * 75)

    all_methods = set(list(real_counts.keys()) + list(null_counts.keys()))
    for method in sorted(all_methods):
        real = real_counts.get(method, 0)
        null = null_counts.get(method, 0)
        ratio = real / max(null, 1)
        # Find corridor name
        corridor = next((k for k, v in CORRIDOR_METHOD_MAP.items() if v == method), method)
        signal = "YES" if ratio > 1.5 else ("MAYBE" if ratio > 1.1 else "NO")
        print(f"{corridor:<20} {method:<25} {real:>6} {null:>6} {ratio:>7.2f}x {signal:<10}")

    print(f"{'='*70}")

if __name__ == "__main__":
    main()
