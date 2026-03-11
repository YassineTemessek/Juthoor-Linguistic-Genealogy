from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class BenchmarkPair:
    source_lang: str
    source_lemma: str
    target_lang: str
    target_lemma: str
    relation: str
    confidence: float = 1.0
    notes: str = ""

    @property
    def source_key(self) -> tuple[str, str]:
        return (_norm(self.source_lang), _norm(self.source_lemma))

    @property
    def target_key(self) -> tuple[str, str]:
        return (_norm(self.target_lang), _norm(self.target_lemma))


@dataclass(frozen=True)
class MatchResult:
    pair: BenchmarkPair
    found_rank: int | None
    top_k: int

    @property
    def hit(self) -> bool:
        return self.found_rank is not None and self.found_rank <= self.top_k

    @property
    def reciprocal_rank(self) -> float:
        if not self.hit or self.found_rank is None:
            return 0.0
        return 1.0 / float(self.found_rank)

    @property
    def ndcg(self) -> float:
        if not self.hit or self.found_rank is None:
            return 0.0
        return 1.0 / math.log2(float(self.found_rank) + 1.0)


def _norm(value: Any) -> str:
    return " ".join(str(value or "").split()).strip().casefold()


def load_benchmark(path: Path, *, relations: set[str] | None = None) -> list[BenchmarkPair]:
    out: list[BenchmarkPair] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rec = json.loads(line)
            pair = BenchmarkPair(
                source_lang=rec["source"]["lang"],
                source_lemma=rec["source"]["lemma"],
                target_lang=rec["target"]["lang"],
                target_lemma=rec["target"]["lemma"],
                relation=rec.get("relation", "unknown"),
                confidence=float(rec.get("confidence", 1.0)),
                notes=str(rec.get("notes", "")),
            )
            if relations and pair.relation not in relations:
                continue
            out.append(pair)
    return out


def load_leads(path: Path) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rec = json.loads(line)
            source = rec.get("source", {})
            key = (_norm(source.get("lang")), _norm(source.get("lemma")))
            grouped.setdefault(key, []).append(rec)
    return grouped


def find_rank(
    pair: BenchmarkPair,
    leads_by_source: dict[tuple[str, str], list[dict[str, Any]]],
    *,
    top_k: int,
) -> int | None:
    candidates = leads_by_source.get(pair.source_key, [])
    target_key = pair.target_key
    for idx, cand in enumerate(candidates[:top_k], start=1):
        target = cand.get("target", {})
        cand_key = (_norm(target.get("lang")), _norm(target.get("lemma")))
        if cand_key == target_key:
            return idx
    return None


def evaluate_pairs(
    benchmark: Iterable[BenchmarkPair],
    leads_by_source: dict[tuple[str, str], list[dict[str, Any]]],
    *,
    top_k: int,
) -> tuple[list[MatchResult], dict[str, Any]]:
    results = [
        MatchResult(pair=pair, found_rank=find_rank(pair, leads_by_source, top_k=top_k), top_k=top_k)
        for pair in benchmark
    ]
    return results, build_metrics(results)


def build_metrics(results: Iterable[MatchResult]) -> dict[str, Any]:
    items = list(results)
    total = len(items)
    hits = sum(1 for item in items if item.hit)
    mrr = sum(item.reciprocal_rank for item in items)
    ndcg = sum(item.ndcg for item in items)
    relation_counts: dict[str, dict[str, int]] = {}
    for item in items:
        bucket = relation_counts.setdefault(item.pair.relation, {"total": 0, "hits": 0})
        bucket["total"] += 1
        bucket["hits"] += int(item.hit)

    by_relation = {
        relation: {
            **counts,
            "recall": round(counts["hits"] / counts["total"], 6) if counts["total"] else 0.0,
        }
        for relation, counts in sorted(relation_counts.items())
    }

    return {
        "total_pairs": total,
        "hits": hits,
        "recall": round(hits / total, 6) if total else 0.0,
        "mrr": round(mrr / total, 6) if total else 0.0,
        "ndcg": round(ndcg / total, 6) if total else 0.0,
        "by_relation": by_relation,
    }


def format_summary(metrics: dict[str, Any], *, top_k: int) -> str:
    lines = [
        f"Recall@{top_k}: {metrics['recall']:.4f} ({metrics['hits']}/{metrics['total_pairs']})",
        f"MRR:       {metrics['mrr']:.4f}",
        f"nDCG:      {metrics['ndcg']:.4f}",
    ]
    by_relation = metrics.get("by_relation") or {}
    if by_relation:
        lines.append("By relation:")
        for relation, counts in by_relation.items():
            lines.append(
                f"  {relation}: recall={counts['recall']:.4f} ({counts['hits']}/{counts['total']})"
            )
    return "\n".join(lines)
