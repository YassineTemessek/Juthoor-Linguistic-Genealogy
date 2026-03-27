"""Ranking-based null model: does the scorer rank gold pairs higher than random?"""
import json, random, sys, time
from pathlib import Path

LV2_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LV2_ROOT / "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def main():
    random.seed(42)
    from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScorer
    scorer = MultiMethodScorer()

    # Load gold pairs
    gold_path = LV2_ROOT / "resources/benchmarks/cognate_gold.jsonl"
    gold_pairs = []
    with open(gold_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            d = json.loads(line)
            src = d.get("source", {})
            tgt = d.get("target", {})
            if src.get("lang", "").startswith("ara") and tgt.get("lang") == "eng":
                gold_pairs.append((
                    {"lemma": src.get("lemma",""), "root": src.get("root", src.get("lemma","")), "root_norm": src.get("root", src.get("lemma","")), "meaning_text": src.get("gloss","")},
                    {"lemma": tgt.get("lemma",""), "ipa": tgt.get("ipa",""), "meaning_text": tgt.get("gloss","")},
                ))

    random.shuffle(gold_pairs)
    sample = gold_pairs[:30]  # 30 gold pairs

    # Load random English words as distractors
    eng_path = LV2_ROOT / "data/processed/english/english_ipa_merged_pos.jsonl"
    all_english = []
    total = sum(1 for l in open(eng_path, encoding="utf-8") if l.strip())
    stride = max(1, total // 500)
    n = 0
    with open(eng_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            n += 1
            if (n-1) % stride != 0: continue
            row = json.loads(line)
            lemma = (row.get("lemma","") or "").strip().lower()
            if lemma and len(lemma) > 2:
                all_english.append(row)

    n_distractors = 20
    print(f"Gold pairs: {len(sample)}, English pool: {len(all_english)}, Distractors per pair: {n_distractors}")

    # Compute MRR for real pairs
    print("\nComputing real MRR...")
    t0 = time.time()
    rrs = []
    for i, (ar, correct_en) in enumerate(sample):
        # Score correct pair
        gold_result = scorer.score_pair(ar, correct_en)
        gold_score = gold_result.best_score

        # Score distractors
        distractors = random.sample(all_english, n_distractors)
        all_scores = [(gold_score, True)]
        for dist in distractors:
            r = scorer.score_pair(ar, dist)
            all_scores.append((r.best_score, False))

        # Rank (descending by score)
        all_scores.sort(key=lambda x: -x[0])
        rank = next(j+1 for j, (_, is_gold) in enumerate(all_scores) if is_gold)
        rrs.append(1.0 / rank)

        if (i+1) % 10 == 0:
            print(f"  {i+1}/{len(sample)} done...")

    mrr_real = sum(rrs) / len(rrs)
    print(f"  Real MRR: {mrr_real:.4f} ({time.time()-t0:.0f}s)")

    # Null model: shuffle which English word is "correct"
    print("\nComputing null MRR (random assignment)...")
    t0 = time.time()
    null_rrs = []
    for i, (ar, _) in enumerate(sample):
        # Pick a random English word as "correct"
        fake_correct = random.choice(all_english)
        gold_result = scorer.score_pair(ar, fake_correct)
        gold_score = gold_result.best_score

        distractors = random.sample(all_english, n_distractors)
        all_scores = [(gold_score, True)]
        for dist in distractors:
            r = scorer.score_pair(ar, dist)
            all_scores.append((r.best_score, False))

        all_scores.sort(key=lambda x: -x[0])
        rank = next(j+1 for j, (_, is_gold) in enumerate(all_scores) if is_gold)
        null_rrs.append(1.0 / rank)

        if (i+1) % 10 == 0:
            print(f"  {i+1}/{len(sample)} done...")

    mrr_null = sum(null_rrs) / len(null_rrs)
    print(f"  Null MRR: {mrr_null:.4f} ({time.time()-t0:.0f}s)")

    # Compare
    print(f"\n{'='*50}")
    print(f"MRR-BASED NULL MODEL TEST")
    print(f"{'='*50}")
    print(f"Real MRR:  {mrr_real:.4f}")
    print(f"Null MRR:  {mrr_null:.4f}")
    print(f"Ratio:     {mrr_real/max(mrr_null, 0.001):.2f}x")
    if mrr_real > mrr_null * 1.2:
        print(f"RESULT:    SIGNIFICANT -- real cognates rank higher than random")
    else:
        print(f"RESULT:    NOT SIGNIFICANT -- ranking doesn't distinguish cognates")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
