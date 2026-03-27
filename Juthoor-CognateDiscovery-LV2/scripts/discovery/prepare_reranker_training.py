from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np

from juthoor_cognatediscovery_lv2.discovery.evaluation import BenchmarkPair, load_benchmark
from juthoor_cognatediscovery_lv2.discovery.genome_scoring import GenomeScorer
from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScorer
from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import PhoneticLawScorer
from juthoor_cognatediscovery_lv2.discovery.rerank import (
    DiscoveryReranker,
    FEATURE_NAMES,
    TrainingExample,
    _feature_vector,
)
from juthoor_cognatediscovery_lv2.discovery.root_quality_scorer import RootQualityScorer
from juthoor_cognatediscovery_lv2.discovery.scoring import DiscoveryScorer


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _sample_gold(rows: list[BenchmarkPair], sample_size: int, seed: int) -> list[BenchmarkPair]:
    if len(rows) <= sample_size:
        return rows
    rng = random.Random(seed)
    selected_indices = sorted(rng.sample(range(len(rows)), sample_size))
    return [rows[idx] for idx in selected_indices]


def _source_fields(pair: BenchmarkPair) -> dict[str, str]:
    return {
        "lang": pair.source_lang,
        "lemma": pair.source_lemma,
        "gloss": pair.source_gloss,
        "root": pair.source_lemma,
        "root_norm": pair.source_lemma,
    }


def _target_fields(pair: BenchmarkPair) -> dict[str, str]:
    return {
        "lang": pair.target_lang,
        "lemma": pair.target_lemma,
        "gloss": pair.target_gloss,
        "root": pair.target_lemma,
        "root_norm": pair.target_lemma,
    }


def _scored_entry(pair: BenchmarkPair, scorer: DiscoveryScorer) -> dict:
    source = _source_fields(pair)
    target = _target_fields(pair)
    candidate = {
        "source": source,
        "target": target,
        "scores": {
            "semantic": 0.0,
            "form": 0.0,
        },
        "_source_fields": source,
        "_target_fields": target,
    }
    return scorer.score({"pair": candidate})[0]


def _prepared_row(pair: BenchmarkPair, label: int, scorer: DiscoveryScorer) -> tuple[dict, TrainingExample]:
    entry = _scored_entry(pair, scorer)
    features = _feature_vector(entry)
    row = {
        "features": [round(float(value), 6) for value in features.tolist()],
        "label": int(label),
        "source_lang": pair.source_lang,
        "target_lang": pair.target_lang,
        "source_lemma": pair.source_lemma,
        "target_lemma": pair.target_lemma,
    }
    example = TrainingExample(
        features=np.array(row["features"], dtype=np.float32),
        label=float(label),
        source_lang=pair.source_lang,
        source_lemma=pair.source_lemma,
        target_lang=pair.target_lang,
        target_lemma=pair.target_lemma,
        relation=pair.relation,
    )
    return row, example


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    repo_root = _repo_root()
    parser = argparse.ArgumentParser(
        description="Prepare a small LV2 reranker training set from benchmark pairs, then train a v2 reranker."
    )
    parser.add_argument(
        "--gold",
        type=Path,
        default=repo_root / "resources" / "benchmarks" / "cognate_gold.jsonl",
    )
    parser.add_argument(
        "--negatives",
        type=Path,
        default=repo_root / "resources" / "benchmarks" / "non_cognate_negatives.jsonl",
    )
    parser.add_argument(
        "--training-data-output",
        type=Path,
        default=repo_root / "data" / "processed" / "reranker_training_data.jsonl",
    )
    parser.add_argument(
        "--model-output",
        type=Path,
        default=repo_root / "outputs" / "models" / "reranker_v2.json",
    )
    parser.add_argument("--gold-sample-size", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=400)
    parser.add_argument("--learning-rate", type=float, default=0.5)
    parser.add_argument("--l2", type=float, default=0.01)
    args = parser.parse_args()

    gold_rows = load_benchmark(args.gold)
    negative_rows = load_benchmark(args.negatives)
    sampled_gold = _sample_gold(gold_rows, args.gold_sample_size, args.seed)

    discovery_scorer = DiscoveryScorer(
        genome_scorer=GenomeScorer(),
        phonetic_law_scorer=PhoneticLawScorer(),
        multi_method_scorer=MultiMethodScorer(),
        root_quality_scorer=RootQualityScorer(),
    )

    prepared_rows: list[dict] = []
    examples: list[TrainingExample] = []
    for pair in sampled_gold:
        row, example = _prepared_row(pair, 1, discovery_scorer)
        prepared_rows.append(row)
        examples.append(example)
    for pair in negative_rows:
        row, example = _prepared_row(pair, 0, discovery_scorer)
        prepared_rows.append(row)
        examples.append(example)

    _write_jsonl(args.training_data_output, prepared_rows)

    model = DiscoveryReranker(args.model_output)
    metrics = model.train(
        examples,
        learning_rate=args.learning_rate,
        epochs=args.epochs,
        l2=args.l2,
    )

    print(f"Gold loaded: {len(gold_rows)}")
    print(f"Negatives loaded: {len(negative_rows)}")
    print(f"Gold sampled: {len(sampled_gold)}")
    print(f"Training rows written: {len(prepared_rows)} -> {args.training_data_output}")
    print(f"Model written: {args.model_output}")
    print(f"Feature count: {len(FEATURE_NAMES)}")
    print(
        "Accuracy: "
        f"{metrics.accuracy:.4f} "
        f"({metrics.total_examples} examples; "
        f"{metrics.positive_examples} positive, {metrics.negative_examples} negative)"
    )
    print("Feature weights:")
    for feature_name in FEATURE_NAMES:
        print(f"  {feature_name}: {model.weights[feature_name]:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
