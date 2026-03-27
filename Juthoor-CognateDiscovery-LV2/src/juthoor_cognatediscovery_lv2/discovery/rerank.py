from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .evaluation import BenchmarkPair, load_benchmark, load_leads


FEATURE_NAMES = (
    "semantic",
    "form",
    "orthography",
    "sound",
    "skeleton",
    "family_boost",
    "root_match",
    "correspondence",
    "weak_radical_match",
    "hamza_match",
    "genome_bonus",
    "phonetic_law_bonus",
    "source_coherence",
    "multi_method_score",
)


def _feature_vector(entry: dict[str, Any]) -> np.ndarray:
    scores = entry.get("scores", {})
    hybrid = entry.get("hybrid", {})
    components = hybrid.get("components", {})
    sound_value = components.get("sound")
    return np.array(
        [
            float(scores.get("semantic", 0.0)),
            float(scores.get("form", 0.0)),
            float(components.get("orthography", 0.0)),
            float(sound_value or 0.0),
            float(components.get("skeleton", 0.0)),
            1.0 if hybrid.get("family_boost_applied") else 0.0,
            float(components.get("root_match", 0.0)),
            float(components.get("correspondence", 0.0)),
            float(components.get("weak_radical_match", 0.0)),
            float(components.get("hamza_match", 0.0)),
            float(components.get("genome_bonus", 0.0)),
            float(components.get("phonetic_law_bonus", 0.0)),
            float(components.get("source_coherence", 0.0)),
            float(components.get("multi_method_best_score", 0.0)),
        ],
        dtype=np.float32,
    )


def _sigmoid(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-clipped))


@dataclass(frozen=True)
class TrainingExample:
    features: np.ndarray
    label: float
    source_lang: str
    source_lemma: str
    target_lang: str
    target_lemma: str
    relation: str


@dataclass(frozen=True)
class TrainingMetrics:
    accuracy: float
    total_examples: int
    positive_examples: int
    negative_examples: int
    epochs: int
    learning_rate: float
    l2: float


class DiscoveryReranker:
    """Small logistic reranker over existing LV2 similarity features."""

    def __init__(self, model_path: Path | None = None):
        self.model_path = model_path
        self.bias = 0.0
        self.weights = {
            "semantic": 0.4,
            "form": 0.2,
            "orthography": 0.15,
            "sound": 0.15,
            "skeleton": 0.1,
            "family_boost": 0.1,
            "root_match": 0.25,
            "correspondence": 0.2,
            "weak_radical_match": 0.1,
            "hamza_match": 0.05,
            "genome_bonus": 0.0,
            "phonetic_law_bonus": 0.3,
            "source_coherence": 0.1,
            "multi_method_score": 0.0,
        }
        self.model_type = "linear_baseline"
        if model_path and model_path.exists():
            self.load()

    def _weight_vector(self) -> np.ndarray:
        return np.array([float(self.weights[name]) for name in FEATURE_NAMES], dtype=np.float32)

    def load(self):
        if not self.model_path or not self.model_path.exists():
            return
        with self.model_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self.model_type = str(payload.get("model_type", "linear_baseline"))
        self.bias = float(payload.get("bias", 0.0))
        weights = payload.get("weights", payload)
        self.weights = {name: float(weights.get(name, self.weights.get(name, 0.0))) for name in FEATURE_NAMES}

    def save(self):
        if not self.model_path:
            return
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "model_type": self.model_type,
            "bias": self.bias,
            "weights": self.weights,
            "feature_names": list(FEATURE_NAMES),
        }
        with self.model_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def predict_one(self, entry: dict[str, Any]) -> float:
        features = _feature_vector(entry)
        score = float(np.dot(features, self._weight_vector()) + self.bias)
        if self.model_type == "logistic_regression":
            return round(float(_sigmoid(np.array([score], dtype=np.float32))[0]), 6)
        return round(score, 6)

    def rerank(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for entry in candidates:
            entry["rerank_score"] = self.predict_one(entry)
        return sorted(candidates, key=lambda item: item["rerank_score"], reverse=True)

    def train(
        self,
        examples: list[TrainingExample],
        *,
        learning_rate: float = 0.5,
        epochs: int = 400,
        l2: float = 0.01,
    ) -> TrainingMetrics:
        if not examples:
            raise ValueError("No training examples were provided.")

        labels = np.array([row.label for row in examples], dtype=np.float32)
        if len(set(labels.tolist())) < 2:
            raise ValueError("Training requires at least one positive and one negative example.")

        features = np.stack([row.features for row in examples], axis=0)
        weights = np.zeros(features.shape[1], dtype=np.float32)
        bias = 0.0

        for _ in range(max(int(epochs), 1)):
            logits = features @ weights + bias
            probs = _sigmoid(logits)
            error = probs - labels
            grad_w = (features.T @ error) / len(features) + (l2 * weights)
            grad_b = float(np.mean(error))
            weights -= learning_rate * grad_w
            bias -= learning_rate * grad_b

        logits = features @ weights + bias
        probs = _sigmoid(logits)
        predictions = (probs >= 0.5).astype(np.float32)
        accuracy = float(np.mean(predictions == labels))

        self.model_type = "logistic_regression"
        self.bias = float(bias)
        self.weights = {name: float(weights[idx]) for idx, name in enumerate(FEATURE_NAMES)}
        self.save()
        return TrainingMetrics(
            accuracy=round(accuracy, 6),
            total_examples=len(examples),
            positive_examples=int(np.sum(labels == 1.0)),
            negative_examples=int(np.sum(labels == 0.0)),
            epochs=max(int(epochs), 1),
            learning_rate=float(learning_rate),
            l2=float(l2),
        )


def _candidate_key(entry: dict[str, Any]) -> tuple[str, str, str, str]:
    source = entry.get("source", {})
    target = entry.get("target", {})
    return (
        str(source.get("lang", "")).casefold(),
        str(source.get("lemma", "")).casefold(),
        str(target.get("lang", "")).casefold(),
        str(target.get("lemma", "")).casefold(),
    )


def build_training_examples(
    benchmark_paths: list[Path],
    discovery_path: Path,
    *,
    positive_relations: set[str] | None = None,
    negatives_per_positive: int = 3,
) -> list[TrainingExample]:
    positive_relations = positive_relations or {"cognate"}
    leads_by_source = load_leads(discovery_path)
    benchmark_rows: list[BenchmarkPair] = []
    for path in benchmark_paths:
        benchmark_rows.extend(load_benchmark(path))

    examples: list[TrainingExample] = []
    positives_by_source: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for pair in benchmark_rows:
        positives_by_source.setdefault(pair.source_key, set()).add(pair.target_key)

    for pair in benchmark_rows:
        source_leads = leads_by_source.get(pair.source_key, [])
        for entry in leads_by_source.get(pair.source_key, []):
            if _candidate_key(entry) != (
                pair.source_key[0],
                pair.source_key[1],
                pair.target_key[0],
                pair.target_key[1],
            ):
                continue
            label = 1.0 if pair.relation in positive_relations else 0.0
            examples.append(
                TrainingExample(
                    features=_feature_vector(entry),
                    label=label,
                    source_lang=pair.source_lang,
                    source_lemma=pair.source_lemma,
                    target_lang=pair.target_lang,
                    target_lemma=pair.target_lemma,
                    relation=pair.relation,
                )
            )
        if pair.relation in positive_relations and negatives_per_positive > 0:
            added = 0
            allowed_targets = positives_by_source.get(pair.source_key, set())
            for entry in source_leads:
                candidate_key = _candidate_key(entry)
                target_key = (candidate_key[2], candidate_key[3])
                if target_key in allowed_targets:
                    continue
                examples.append(
                    TrainingExample(
                        features=_feature_vector(entry),
                        label=0.0,
                        source_lang=pair.source_lang,
                        source_lemma=pair.source_lemma,
                        target_lang=str(entry.get("target", {}).get("lang", "")),
                        target_lemma=str(entry.get("target", {}).get("lemma", "")),
                        relation="implicit_negative",
                    )
                )
                added += 1
                if added >= negatives_per_positive:
                    break
    return examples


def train_reranker(
    benchmark_paths: list[Path],
    discovery_path: Path,
    output_model_path: Path,
    *,
    learning_rate: float = 0.5,
    epochs: int = 400,
    l2: float = 0.01,
    negatives_per_positive: int = 3,
) -> DiscoveryReranker:
    examples = build_training_examples(
        benchmark_paths,
        discovery_path,
        negatives_per_positive=negatives_per_positive,
    )
    if not examples:
        raise ValueError("No training examples matched the discovery leads.")

    model = DiscoveryReranker(output_model_path)
    model.train(
        examples,
        learning_rate=learning_rate,
        epochs=epochs,
        l2=l2,
    )
    return model


def rerank_leads_file(model_path: Path, leads_path: Path, output_path: Path) -> Path:
    reranker = DiscoveryReranker(model_path)
    grouped = load_leads(leads_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for _, candidates in grouped.items():
            ranked = reranker.rerank(candidates)
            for row in ranked:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return output_path
