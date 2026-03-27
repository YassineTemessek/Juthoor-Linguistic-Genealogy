from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LV2_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = LV2_ROOT.parent

DEFAULT_INPUT = REPO_ROOT / "outputs" / "cognate_graph.json"
FALLBACK_INPUT = LV2_ROOT / "outputs" / "cognate_graph.json"
DEFAULT_OUTPUT = REPO_ROOT / "outputs" / "arabic_root_semantic_map.jsonl"


def resolve_input_path(path: Path) -> Path:
    if path.exists():
        return path
    if path == DEFAULT_INPUT and FALLBACK_INPUT.exists():
        return FALLBACK_INPUT
    raise FileNotFoundError(
        f"Could not find cognate graph at {path} or fallback {FALLBACK_INPUT}"
    )


def load_graph(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        graph = json.load(handle)
    if not isinstance(graph, dict):
        raise ValueError("Cognate graph must be a JSON object")
    if not isinstance(graph.get("nodes"), dict) or not isinstance(graph.get("edges"), list):
        raise ValueError("Cognate graph must contain object 'nodes' and list 'edges'")
    return graph


def _canonical_root(raw_root: Any, lemma: str) -> str:
    root = str(raw_root or "").strip()
    return root or lemma.strip()


def build_root_map(graph: dict[str, Any]) -> list[dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = graph["nodes"]
    edges: list[dict[str, Any]] = graph["edges"]

    roots: dict[str, dict[str, Any]] = {}

    for edge in edges:
        source_id = str(edge.get("source", ""))
        target_id = str(edge.get("target", ""))
        source_node = nodes.get(source_id)
        target_node = nodes.get(target_id)

        if not source_node or not target_node:
            continue
        if source_node.get("lang") != "ara":
            continue

        source_lemma = str(source_node.get("lemma", "")).strip()
        root = _canonical_root(source_node.get("root"), source_lemma)
        if not root:
            continue

        bucket = roots.setdefault(
            root,
            {
                "root": root,
                "source_lemmas": set(),
                "target_languages": set(),
                "scores": [],
                "method_counts": Counter(),
                "method_score_sums": defaultdict(float),
                "target_lemmas_by_language": defaultdict(set),
                "total_edges": 0,
            },
        )

        target_lang = str(target_node.get("lang", "")).strip()
        target_lemma = str(target_node.get("lemma", "")).strip()
        method = str(edge.get("method", "")).strip() or "unknown"

        try:
            score = float(edge.get("score", 0.0) or 0.0)
        except (TypeError, ValueError):
            score = 0.0

        bucket["source_lemmas"].add(source_lemma)
        if target_lang:
            bucket["target_languages"].add(target_lang)
        if target_lang and target_lemma:
            bucket["target_lemmas_by_language"][target_lang].add(target_lemma)
        bucket["scores"].append(score)
        bucket["method_counts"][method] += 1
        bucket["method_score_sums"][method] += score
        bucket["total_edges"] += 1

    rows: list[dict[str, Any]] = []
    for root, bucket in roots.items():
        scores = bucket["scores"]
        method_counts: Counter[str] = bucket["method_counts"]
        method_score_sums: dict[str, float] = bucket["method_score_sums"]

        dominant_method = "unknown"
        if method_counts:
            dominant_method = sorted(
                method_counts,
                key=lambda method: (
                    -method_counts[method],
                    -method_score_sums[method],
                    method,
                ),
            )[0]

        rows.append(
            {
                "root": root,
                "source_lemmas": sorted(x for x in bucket["source_lemmas"] if x),
                "target_languages": sorted(bucket["target_languages"]),
                "target_language_count": len(bucket["target_languages"]),
                "total_edges": bucket["total_edges"],
                "average_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
                "dominant_method": dominant_method,
                "target_lemmas_by_language": {
                    lang: sorted(lemmas)
                    for lang, lemmas in sorted(bucket["target_lemmas_by_language"].items())
                },
            }
        )

    rows.sort(key=lambda row: (-row["total_edges"], row["root"]))
    return rows


def write_jsonl(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def print_summary(rows: list[dict[str, Any]], input_path: Path, output_path: Path) -> None:
    total_roots = len(rows)
    avg_connections = (
        round(sum(row["total_edges"] for row in rows) / total_roots, 2)
        if total_roots
        else 0.0
    )
    top_roots = rows[:10]

    print(f"Input graph: {input_path}")
    print(f"Output map : {output_path}")
    print(f"Total roots: {total_roots}")
    print(f"Avg connections per root: {avg_connections}")
    print("Most connected roots:")
    for row in top_roots:
        print(
            f"  {row['root']}: "
            f"{row['total_edges']} edges, "
            f"{row['target_language_count']} languages, "
            f"avg_score={row['average_score']}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an Arabic root semantic map from the cognate graph."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to cognate_graph.json (defaults to outputs/cognate_graph.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to JSONL output (defaults to outputs/arabic_root_semantic_map.jsonl)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = resolve_input_path(args.input)
    graph = load_graph(input_path)
    rows = build_root_map(graph)
    write_jsonl(rows, args.output)
    print_summary(rows, input_path, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
