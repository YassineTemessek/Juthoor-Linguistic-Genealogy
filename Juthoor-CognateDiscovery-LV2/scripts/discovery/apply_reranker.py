from __future__ import annotations

import argparse
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.rerank import rerank_leads_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a trained LV2 reranker model to an existing leads JSONL.")
    parser.add_argument("leads", type=Path, help="Input discovery leads JSONL.")
    parser.add_argument("--model", type=Path, required=True, help="Trained reranker model JSON.")
    parser.add_argument("--output", type=Path, required=True, help="Output reranked leads JSONL.")
    args = parser.parse_args()

    output = rerank_leads_file(args.model, args.leads, args.output)
    print(f"Reranked leads written to: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
