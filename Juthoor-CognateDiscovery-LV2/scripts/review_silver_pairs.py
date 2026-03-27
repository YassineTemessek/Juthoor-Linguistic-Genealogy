"""Quality review of silver cognate pairs.

Scores each silver pair with PhoneticLawScorer and:
  - Promotes to gold: phonetic_law_score > 0.65 AND confidence >= 0.6
  - Flags for removal: phonetic_law_score < 0.25
  - Keeps as silver: everything else

Moves promoted pairs from silver JSONL to gold JSONL.
Prints counts: promoted, flagged, remaining silver.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve()
LV2_ROOT = HERE.parents[1]
SRC_DIR = LV2_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import PhoneticLawScorer

BENCHMARK_DIR = LV2_ROOT / "resources" / "benchmarks"
GOLD_PATH = BENCHMARK_DIR / "cognate_gold.jsonl"
SILVER_PATH = BENCHMARK_DIR / "cognate_silver.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def save_jsonl(path: Path, records: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main() -> None:
    silver = load_jsonl(SILVER_PATH)
    gold = load_jsonl(GOLD_PATH)
    print(f"Loaded {len(silver)} silver pairs, {len(gold)} gold pairs.")

    scorer = PhoneticLawScorer()

    promoted: list[dict] = []
    flagged: list[dict] = []
    remaining: list[dict] = []

    for pair in silver:
        src = pair.get("source", {})
        tgt = pair.get("target", {})
        confidence = pair.get("confidence", 0.0)

        result = scorer.score_pair(src, tgt)
        score = result["phonetic_law_score"]

        pair_annotated = {**pair, "_phonetic_law_score": round(score, 4)}

        if score > 0.65 and confidence >= 0.6:
            promoted.append(pair_annotated)
        elif score < 0.25:
            flagged.append(pair_annotated)
        else:
            remaining.append(pair)

    print(f"\n--- Silver Pair Quality Review ---")
    print(f"  Promoted to gold (score > 0.65 AND conf >= 0.6): {len(promoted)}")
    print(f"  Flagged for removal (score < 0.25):              {len(flagged)}")
    print(f"  Remaining silver:                                 {len(remaining)}")

    if promoted:
        print("\nPromoted pairs:")
        for p in promoted:
            ara = p["source"].get("lemma", "")
            eng = p["target"].get("lemma", "")
            score = p["_phonetic_law_score"]
            conf = p.get("confidence", "?")
            print(f"  {ara:20s} -> {eng:20s}  score={score:.4f}  conf={conf}")

        # Write promoted pairs to gold (strip the internal _phonetic_law_score annotation)
        gold_new = gold + [
            {k: v for k, v in p.items() if not k.startswith("_")} for p in promoted
        ]
        save_jsonl(GOLD_PATH, gold_new)
        print(f"\nGold JSONL updated: {len(gold)} -> {len(gold_new)} entries.")

        # Write remaining silver (flagged are dropped)
        save_jsonl(SILVER_PATH, remaining)
        print(f"Silver JSONL updated: {len(silver)} -> {len(remaining)} entries.")
    else:
        print("\nNo pairs promoted — files unchanged.")

    if flagged:
        print(f"\nFlagged pairs (score < 0.25, dropped from silver):")
        for p in flagged:
            ara = p["source"].get("lemma", "")
            eng = p["target"].get("lemma", "")
            score = p["_phonetic_law_score"]
            print(f"  {ara:20s} -> {eng:20s}  score={score:.4f}")

    print("\nDone.")


if __name__ == "__main__":
    main()
