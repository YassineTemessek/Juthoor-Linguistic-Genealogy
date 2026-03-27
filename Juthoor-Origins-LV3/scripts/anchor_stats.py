"""Anchor statistics report for LV3 validated leads."""
from __future__ import annotations

import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


LEADS_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "leads"
    / "validated_leads.jsonl"
)


def load_leads(path: Path) -> list[dict]:
    leads = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                leads.append(json.loads(line))
    return leads


def report(leads: list[dict]) -> None:
    total = len(leads)
    print("=" * 60)
    print("JUTHOOR LV3 — ANCHOR STATISTICS REPORT")
    print(f"Total validated leads: {total:,}")
    print("=" * 60)

    # 1. By anchor tier
    tier_counts: Counter = Counter(l.get("anchor_level", "unknown") for l in leads)
    tier_scores: dict[str, list[float]] = defaultdict(list)
    for l in leads:
        tier = l.get("anchor_level", "unknown")
        score = l.get("score")
        if score is not None:
            tier_scores[tier].append(float(score))

    print("\n[1] Leads by anchor tier")
    print(f"  {'Tier':<15} {'Count':>7}  {'Avg Score':>10}")
    print(f"  {'-'*15} {'-'*7}  {'-'*10}")
    for tier in sorted(tier_counts):
        count = tier_counts[tier]
        scores = tier_scores[tier]
        avg = sum(scores) / len(scores) if scores else float("nan")
        print(f"  {tier:<15} {count:>7,}  {avg:>10.4f}")

    # 2. By language pair
    pair_counts: Counter = Counter(
        f"{l.get('source_lang', '?')}->{l.get('target_lang', '?')}" for l in leads
    )
    print("\n[2] Leads by language pair (top 15)")
    print(f"  {'Pair':<20} {'Count':>7}")
    print(f"  {'-'*20} {'-'*7}")
    for pair, count in pair_counts.most_common(15):
        print(f"  {pair:<20} {count:>7,}")

    # 3. By corridor
    corridor_counts: Counter = Counter(
        l.get("corridor_id", "UNKNOWN") for l in leads
    )
    print("\n[3] Leads by corridor (top 15)")
    print(f"  {'Corridor':<20} {'Count':>7}")
    print(f"  {'-'*20} {'-'*7}")
    for corridor, count in corridor_counts.most_common(15):
        print(f"  {corridor:<20} {count:>7,}")

    # 4. Top 20 gold-anchor leads by confidence
    gold_leads = [l for l in leads if l.get("anchor_level") == "gold"]
    top20 = sorted(gold_leads, key=lambda l: l.get("score", 0.0), reverse=True)[:20]
    print(f"\n[4] Top 20 gold-anchor leads (highest confidence)")
    print(f"  {'Source':<20} {'Target':<20} {'Pair':<12} {'Corridor':<14} {'Score':>6}")
    print(f"  {'-'*20} {'-'*20} {'-'*12} {'-'*14} {'-'*6}")
    for l in top20:
        src = l.get("source_lemma", "")[:18]
        tgt = l.get("target_lemma", "")[:18]
        pair = f"{l.get('source_lang','?')}->{l.get('target_lang','?')}"
        corridor = l.get("corridor_id", "?")
        score = l.get("score", 0.0)
        print(f"  {src:<20} {tgt:<20} {pair:<12} {corridor:<14} {score:>6.4f}")

    # 5. Average score per anchor tier (summary)
    print("\n[5] Average score per anchor tier")
    print(f"  {'Tier':<15} {'Avg Score':>10}  {'Min':>8}  {'Max':>8}")
    print(f"  {'-'*15} {'-'*10}  {'-'*8}  {'-'*8}")
    for tier in sorted(tier_scores):
        scores = tier_scores[tier]
        avg = sum(scores) / len(scores)
        print(
            f"  {tier:<15} {avg:>10.4f}  {min(scores):>8.4f}  {max(scores):>8.4f}"
        )

    print("\n" + "=" * 60)


def main() -> None:
    if not LEADS_PATH.exists():
        print(f"ERROR: leads file not found at {LEADS_PATH}")
        return
    leads = load_leads(LEADS_PATH)
    report(leads)


if __name__ == "__main__":
    main()
