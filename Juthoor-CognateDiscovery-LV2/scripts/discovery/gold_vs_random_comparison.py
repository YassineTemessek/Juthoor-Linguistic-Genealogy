"""Compare MultiMethodScorer scores for gold cognates vs random non-cognates."""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LV2_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LV2_ROOT / "src"))

GOLD_PATH = LV2_ROOT / "resources" / "benchmarks" / "cognate_gold.jsonl"
DEFAULT_SAMPLE_SIZE = 50
DEFAULT_SEED = 42
HISTOGRAM_BINS = 10


def normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def sample_variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = mean(values)
    return sum((value - mu) ** 2 for value in values) / (len(values) - 1)


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def cohens_d(group_a: list[float], group_b: list[float]) -> float:
    if len(group_a) < 2 or len(group_b) < 2:
        return 0.0
    var_a = sample_variance(group_a)
    var_b = sample_variance(group_b)
    pooled_num = (len(group_a) - 1) * var_a + (len(group_b) - 1) * var_b
    pooled_den = len(group_a) + len(group_b) - 2
    if pooled_den <= 0:
        return 0.0
    pooled_sd = math.sqrt(max(pooled_num / pooled_den, 0.0))
    if pooled_sd == 0.0:
        return 0.0
    return (mean(group_a) - mean(group_b)) / pooled_sd


def wilcoxon_rank_sum(group_a: list[float], group_b: list[float]) -> tuple[float, float, str]:
    try:
        from scipy.stats import mannwhitneyu

        statistic, p_value = mannwhitneyu(group_a, group_b, alternative="two-sided")
        return float(statistic), float(p_value), "scipy.mannwhitneyu"
    except ImportError:
        combined = [(value, 0) for value in group_a] + [(value, 1) for value in group_b]
        combined.sort(key=lambda item: item[0])

        ranks = [0.0] * len(combined)
        tie_sizes: list[int] = []
        index = 0
        while index < len(combined):
            end = index + 1
            while end < len(combined) and combined[end][0] == combined[index][0]:
                end += 1
            avg_rank = (index + 1 + end) / 2.0
            for pos in range(index, end):
                ranks[pos] = avg_rank
            tie_sizes.append(end - index)
            index = end

        rank_sum_a = sum(rank for rank, (_, group_id) in zip(ranks, combined) if group_id == 0)
        n1 = len(group_a)
        n2 = len(group_b)
        u1 = rank_sum_a - n1 * (n1 + 1) / 2.0
        mean_u = n1 * n2 / 2.0

        total = n1 + n2
        tie_term = sum(size**3 - size for size in tie_sizes)
        variance_u = (n1 * n2 / 12.0) * ((total + 1) - tie_term / (total * (total - 1)))
        if variance_u <= 0.0:
            return u1, 1.0, "normal-approx-fallback"

        z = (u1 - mean_u) / math.sqrt(variance_u)
        p_value = 2.0 * (1.0 - normal_cdf(abs(z)))
        return u1, max(0.0, min(1.0, p_value)), "normal-approx-fallback"


def load_ara_eng_gold_pairs() -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    with GOLD_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            source = row.get("source", {})
            target = row.get("target", {})
            if source.get("lang", "").startswith("ara") and target.get("lang") == "eng":
                pairs.append(row)
    return pairs


def build_source_dict(source: dict[str, Any]) -> dict[str, Any]:
    root = str(source.get("root") or source.get("root_norm") or source.get("lemma") or "").strip()
    gloss = str(source.get("gloss") or source.get("meaning_text") or "").strip()
    return {
        "lemma": str(source.get("lemma") or "").strip(),
        "root": root,
        "root_norm": root,
        "gloss": gloss,
        "meaning_text": gloss,
    }


def build_target_dict(target: dict[str, Any]) -> dict[str, Any]:
    gloss = str(target.get("gloss") or target.get("meaning_text") or "").strip()
    return {
        "lemma": str(target.get("lemma") or "").strip(),
        "ipa": str(target.get("ipa") or "").strip(),
        "gloss": gloss,
        "meaning_text": gloss,
    }


def sample_gold_pairs(gold_pairs: list[dict[str, Any]], sample_size: int, rng: random.Random) -> list[dict[str, Any]]:
    if len(gold_pairs) < sample_size:
        raise ValueError(f"Requested {sample_size} gold pairs, but only found {len(gold_pairs)} ara-eng pairs.")
    return rng.sample(gold_pairs, sample_size)


def build_random_pairs(
    gold_pairs: list[dict[str, Any]],
    sample_size: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    sources_by_lemma: dict[str, dict[str, Any]] = {}
    targets_by_lemma: dict[str, dict[str, Any]] = {}
    gold_pair_keys: set[tuple[str, str]] = set()

    for pair in gold_pairs:
        source = pair.get("source", {})
        target = pair.get("target", {})
        source_lemma = str(source.get("lemma") or "").strip()
        target_lemma = str(target.get("lemma") or "").strip()
        if source_lemma:
            sources_by_lemma.setdefault(source_lemma, source)
        if target_lemma:
            targets_by_lemma.setdefault(target_lemma, target)
        if source_lemma and target_lemma:
            gold_pair_keys.add((source_lemma, target_lemma))

    sources = list(sources_by_lemma.values())
    targets = list(targets_by_lemma.values())
    if not sources or not targets:
        raise ValueError("Could not build source/target pools for random sampling.")

    random_pairs: list[dict[str, Any]] = []
    seen_random_keys: set[tuple[str, str]] = set()
    max_attempts = sample_size * 100
    attempts = 0

    while len(random_pairs) < sample_size and attempts < max_attempts:
        attempts += 1
        source = rng.choice(sources)
        target = rng.choice(targets)
        key = (str(source.get("lemma") or "").strip(), str(target.get("lemma") or "").strip())
        if not key[0] or not key[1]:
            continue
        if key in gold_pair_keys or key in seen_random_keys:
            continue
        seen_random_keys.add(key)
        random_pairs.append({"source": source, "target": target})

    if len(random_pairs) < sample_size:
        raise ValueError(
            f"Could only construct {len(random_pairs)} random non-gold pairs from benchmark pools."
        )
    return random_pairs


def score_pairs(
    pairs: list[dict[str, Any]],
    scorer: Any,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for pair in pairs:
        source = build_source_dict(pair["source"])
        target = build_target_dict(pair["target"])
        score = scorer.score_pair(source, target)
        results.append(
            {
                "source_lemma": source["lemma"],
                "source_root": source["root_norm"],
                "target_lemma": target["lemma"],
                "score": float(score.best_score),
                "method": score.best_method,
                "methods_fired": list(score.methods_that_fired),
            }
        )
    return results


def format_histogram(values: list[float], label: str, width: int = 28) -> str:
    counts = [0] * HISTOGRAM_BINS
    for value in values:
        index = min(int(value * HISTOGRAM_BINS), HISTOGRAM_BINS - 1)
        counts[index] += 1

    peak = max(counts) if counts else 1
    lines = [f"{label} distribution"]
    for idx, count in enumerate(counts):
        start = idx / HISTOGRAM_BINS
        end = (idx + 1) / HISTOGRAM_BINS
        bar_len = 0 if peak == 0 else round((count / peak) * width)
        bar = "#" * bar_len
        lines.append(f"  {start:0.1f}-{end:0.1f}: {count:>2} {bar}")
    return "\n".join(lines)


def print_summary(
    gold_scores: list[float],
    random_scores: list[float],
    effect_size: float,
    rank_sum_stat: float,
    rank_sum_p: float,
    p_method: str,
) -> None:
    gold_mean = mean(gold_scores)
    random_mean = mean(random_scores)

    print("=" * 72)
    print("Gold vs Random Pair Score Comparison")
    print("=" * 72)
    print(f"Gold sample size:            {len(gold_scores)}")
    print(f"Random sample size:          {len(random_scores)}")
    print(f"Gold mean score:             {gold_mean:.4f}")
    print(f"Random mean score:           {random_mean:.4f}")
    print(f"Gold median score:           {median(gold_scores):.4f}")
    print(f"Random median score:         {median(random_scores):.4f}")
    print(f"Mean difference:             {gold_mean - random_mean:.4f}")
    print(f"Cohen's d:                  {effect_size:.4f}")
    print(f"Wilcoxon rank-sum statistic: {rank_sum_stat:.4f}")
    print(f"Wilcoxon rank-sum p-value:   {rank_sum_p:.6g}")
    print(f"Rank-sum implementation:     {p_method}")
    print()
    print("Interpretation:")
    print(
        "  GOLD scores HIGHER than random."
        if gold_mean > random_mean
        else "  GOLD scores do NOT exceed random in this sample."
    )
    print()
    print(format_histogram(gold_scores, "Gold"))
    print()
    print(format_histogram(random_scores, "Random"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare scorer distributions for gold ara-eng cognates vs random non-gold pairs."
    )
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScorer

    rng = random.Random(args.seed)
    gold_pairs = load_ara_eng_gold_pairs()
    gold_sample = sample_gold_pairs(gold_pairs, args.sample_size, rng)
    random_sample = build_random_pairs(gold_pairs, args.sample_size, rng)

    scorer = MultiMethodScorer()
    gold_results = score_pairs(gold_sample, scorer)
    random_results = score_pairs(random_sample, scorer)

    gold_scores = [row["score"] for row in gold_results]
    random_scores = [row["score"] for row in random_results]
    effect_size = cohens_d(gold_scores, random_scores)
    rank_sum_stat, rank_sum_p, p_method = wilcoxon_rank_sum(gold_scores, random_scores)

    print_summary(
        gold_scores=gold_scores,
        random_scores=random_scores,
        effect_size=effect_size,
        rank_sum_stat=rank_sum_stat,
        rank_sum_p=rank_sum_p,
        p_method=p_method,
    )


if __name__ == "__main__":
    main()
