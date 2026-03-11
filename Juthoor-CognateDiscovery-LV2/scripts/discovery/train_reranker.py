from __future__ import annotations

import argparse
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.rerank import train_reranker


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the LV2 logistic reranker from benchmark files and a discovery leads JSONL.")
    parser.add_argument("leads", type=Path, help="Discovery leads JSONL used as training candidates.")
    parser.add_argument("--benchmark", action="append", required=True, help="Benchmark JSONL file (repeatable).")
    parser.add_argument("--output", type=Path, required=True, help="Where to write the trained model JSON.")
    parser.add_argument("--epochs", type=int, default=400)
    parser.add_argument("--learning-rate", type=float, default=0.5)
    parser.add_argument("--l2", type=float, default=0.01)
    args = parser.parse_args()

    model = train_reranker(
        [Path(item) for item in args.benchmark],
        args.leads,
        args.output,
        learning_rate=args.learning_rate,
        epochs=args.epochs,
        l2=args.l2,
    )
    print(f"Model written to: {args.output}")
    print(f"Model type: {model.model_type}")
    print(f"Weights: {model.weights}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
