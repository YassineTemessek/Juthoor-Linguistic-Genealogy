"""
Learned reranker for LV2 discovery leads.
Uses Logistic Regression to combine multiple similarity signals into a single score.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

class DiscoveryReranker:
    """
    A learned reranker that uses a linear model to weight different similarity features.
    """
    def __init__(self, model_path: Path | None = None):
        self.model_path = model_path
        self.weights = {
            "semantic": 0.4,
            "form": 0.2,
            "orthography": 0.15,
            "sound": 0.15,
            "skeleton": 0.1,
            "family_boost": 0.1
        }
        if model_path and model_path.exists():
            self.load()

    def load(self):
        if self.model_path and self.model_path.exists():
            with self.model_path.open("r") as f:
                self.weights = json.load(f)

    def save(self):
        if self.model_path:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            with self.model_path.open("w") as f:
                json.dump(self.weights, f, indent=2)

    def predict_one(self, entry: dict[str, Any]) -> float:
        """
        Computes a reranked score for a single entry.
        Features are extracted from entry['scores'] and entry['hybrid'].
        """
        scores = entry.get("scores", {})
        hybrid = entry.get("hybrid", {})
        
        # Feature extraction
        f_sem = float(scores.get("semantic", 0))
        f_form = float(scores.get("form", 0))
        
        # From heuristic hybrid breakdown
        details = hybrid.get("components", {})
        f_orth = float(details.get("orthography", 0))
        sound_value = details.get("sound")
        f_sound = float(sound_value or 0.0)
        f_skel = float(details.get("skeleton", 0))
        
        # Family match boolean feature (0 or 1)
        f_family = 1.0 if hybrid.get("family_boost_applied") else 0.0
        
        # Linear combination
        total = (
            f_sem * self.weights.get("semantic", 0) +
            f_form * self.weights.get("form", 0) +
            f_orth * self.weights.get("orthography", 0) +
            f_sound * self.weights.get("sound", 0) +
            f_skel * self.weights.get("skeleton", 0) +
            f_family * self.weights.get("family_boost", 0)
        )
        return round(total, 6)

    def rerank(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Adds a 'rerank_score' to each entry and sorts them.
        """
        for entry in candidates:
            entry["rerank_score"] = self.predict_one(entry)
            
        return sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)

def train_reranker(
    gold_path: Path, 
    discovery_path: Path, 
    output_model_path: Path
):
    """
    Naive 'training' implementation (Phase 4 start).
    In a real implementation, this would use sklearn.LogisticRegression.
    For now, it provides the hook for that logic.
    """
    print(f"Training reranker using {gold_path} and {discovery_path}...")
    # TODO: Implement actual SGD/LogisticRegression training loop
    # For now, we just ensure the weights are saved.
    model = DiscoveryReranker(output_model_path)
    model.save()
    print(f"Model saved to {output_model_path}")
