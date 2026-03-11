"""
Scoring and reranking logic for LV2 discovery.
Includes hybrid scoring and interfaces for future learned rerankers.
"""
from __future__ import annotations

from typing import Any
from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import HybridWeights, compute_hybrid

def apply_hybrid_scoring(
    candidates: dict[str, dict[str, Any]],
    weights: HybridWeights,
) -> None:
    """
    Applies heuristic hybrid scoring to a dictionary of candidates.
    Modifies candidates in-place by adding a 'hybrid' key.
    """
    for entry in candidates.values():
        # Field-aware access to source/target data for heuristic comparison
        # Note: These fields are temporarily stored in the entry during retrieval
        src_fields = entry.get("_source_fields", {})
        tgt_fields = entry.get("_target_fields", {})
        
        entry["hybrid"] = compute_hybrid(
            source=src_fields,
            target=tgt_fields,
            semantic=entry["scores"].get("semantic"),
            form=entry["scores"].get("form"),
            weights=weights,
        )

def rank_candidates(
    candidates: list[dict[str, Any]],
    max_out: int = 200,
    min_hybrid: float = 0.0,
) -> list[dict[str, Any]]:
    """
    Sorts candidates by hybrid score and category strength.
    """
    def sort_key(e: dict[str, Any]):
        scores = e.get("scores", {})
        hybrid = e.get("hybrid") or {}
        combined = hybrid.get("combined_score")
        return (
            float(combined) if combined is not None else -1e9,
            2 if e.get("category") == "strong_union" else 1,
            float(scores.get("semantic", -1e9)),
            float(scores.get("form", -1e9)),
        )

    ranked = sorted(candidates, key=sort_key, reverse=True)[:max_out]
    
    if min_hybrid > 0:
        ranked = [
            e for e in ranked
            if (e.get("hybrid") or {}).get("combined_score", 0) >= min_hybrid
        ]
        
    return ranked

class DiscoveryScorer:
    """
    Placeholder for a learned reranker (Phase 4).
    Currently defaults to the hybrid baseline.
    """
    def __init__(self, weights: HybridWeights | None = None):
        self.weights = weights or HybridWeights()

    def score(self, candidates: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        apply_hybrid_scoring(candidates, self.weights)
        # Clean up temporary fields used for scoring but not needed in output
        for entry in candidates.values():
            entry.pop("_source_fields", None)
            entry.pop("_target_fields", None)
        return list(candidates.values())
