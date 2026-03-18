"""Evaluate Persian (ara-fa) blind vs genome leads and write comparison report."""
from __future__ import annotations

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE / "src"))

from juthoor_cognatediscovery_lv2.discovery.evaluation import (
    load_benchmark,
    load_leads,
    evaluate_pairs,
    build_metrics,
    recall_at_k,
    find_rank,
    MatchResult,
)


def eval_leads(benchmark_path: Path, leads_path: Path, lang_filter: str) -> dict:
    """Evaluate leads against benchmark, filtering for a specific target language."""
    all_pairs = load_benchmark(benchmark_path)
    fa_pairs = [p for p in all_pairs if p.target_lang == lang_filter]

    leads_by_source = load_leads(leads_path)

    # Use top_k=100 for full evaluation
    results = [
        MatchResult(
            pair=pair,
            found_rank=find_rank(pair, leads_by_source, top_k=100),
            top_k=100,
        )
        for pair in fa_pairs
    ]
    return build_metrics(results)


def main() -> int:
    lv2_root = Path(__file__).resolve().parent.parent.parent

    benchmark_path = lv2_root / "resources" / "benchmarks" / "cognate_gold.jsonl"
    blind_leads_path = lv2_root / "outputs" / "leads" / "discovery_ara_fa_blind_semfast.jsonl"
    genome_leads_path = lv2_root / "outputs" / "leads" / "discovery_ara_fa_genome_semfast.jsonl"

    # Also write individual eval JSONs for parity with Hebrew/Aramaic
    blind_eval_out = lv2_root / "outputs" / "leads" / "ara_fa_blind_semfast_eval.json"
    genome_eval_out = lv2_root / "outputs" / "leads" / "ara_fa_genome_semfast_eval.json"
    comparison_out = lv2_root / "outputs" / "reports" / "ara_fa_blind_vs_genome.json"

    print("Evaluating blind leads...")
    blind_metrics = eval_leads(benchmark_path, blind_leads_path, "fa")
    print(f"  Blind: total_pairs={blind_metrics['total_pairs']}, recall@10={blind_metrics['recall@10']}, mrr={blind_metrics['mrr']}")

    print("Evaluating genome leads...")
    genome_metrics = eval_leads(benchmark_path, genome_leads_path, "fa")
    print(f"  Genome: total_pairs={genome_metrics['total_pairs']}, recall@10={genome_metrics['recall@10']}, mrr={genome_metrics['mrr']}")

    # Write individual eval files
    blind_eval_out.write_text(json.dumps(blind_metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    genome_eval_out.write_text(json.dumps(genome_metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Written: {blind_eval_out}")
    print(f"Written: {genome_eval_out}")

    # Build delta
    delta = {
        "recall@10": round(genome_metrics["recall@10"] - blind_metrics["recall@10"], 6),
        "recall@50": round(genome_metrics["recall@50"] - blind_metrics["recall@50"], 6),
        "recall@100": round(genome_metrics["recall@100"] - blind_metrics["recall@100"], 6),
        "mrr": round(genome_metrics["mrr"] - blind_metrics["mrr"], 6),
        "ndcg": round(genome_metrics["ndcg"] - blind_metrics["ndcg"], 6),
        "weighted_mrr": round(genome_metrics["weighted_mrr"] - blind_metrics["weighted_mrr"], 6),
        "weighted_ndcg": round(genome_metrics["weighted_ndcg"] - blind_metrics["weighted_ndcg"], 6),
    }

    comparison = {
        "pair": "ara_fa",
        "blind": blind_metrics,
        "genome": genome_metrics,
        "delta": delta,
    }

    comparison_out.parent.mkdir(parents=True, exist_ok=True)
    comparison_out.write_text(json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Written: {comparison_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
