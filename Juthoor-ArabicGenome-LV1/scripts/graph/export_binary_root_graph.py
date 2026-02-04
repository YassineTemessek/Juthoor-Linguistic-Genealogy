"""
Export a graph-friendly view of LV2 Arabic root relations (nodes + edges).

Input:
  - data/processed/arabic/arabic_words_binary_roots.jsonl

Outputs (default):
  - outputs/graphs/binary_root_nodes.csv
  - outputs/graphs/binary_root_edges.csv

This format is intentionally simple (CSV) so it can be loaded into tools like
Gephi, Cytoscape, Neo4j importers, or used as a base for GraphRAG pipelines.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def iter_jsonl(path: Path) -> Any:
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def node_id(kind: str, value: str) -> str:
    return f"{kind}:{value}"


def export_graph(input_path: Path, nodes_csv: Path, edges_csv: Path) -> dict[str, int]:
    nodes_csv.parent.mkdir(parents=True, exist_ok=True)
    edges_csv.parent.mkdir(parents=True, exist_ok=True)

    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    def upsert_node(nid: str, *, kind: str, label: str, **attrs: Any) -> None:
        cur = nodes.get(nid)
        if cur is None:
            cur = {"id": nid, "type": kind, "label": label}
            nodes[nid] = cur
        for k, v in attrs.items():
            if v is None or v == "" or v == []:
                continue
            if k not in cur or cur.get(k) in (None, "", []):
                cur[k] = v

    total_rows = 0
    for rec in iter_jsonl(input_path):
        total_rows += 1
        lemma = str(rec.get("lemma") or "").strip()
        root_norm = str(rec.get("root_norm") or rec.get("root") or "").strip()
        binary_root = str(rec.get("binary_root") or "").strip()

        if not lemma:
            continue

        lemma_nid = node_id("lemma", lemma)
        upsert_node(
            lemma_nid,
            kind="lemma",
            label=lemma,
            language=rec.get("language"),
            script=rec.get("script") or "",
            lemma_status=rec.get("lemma_status"),
            translit=rec.get("translit"),
            ipa=rec.get("ipa"),
        )

        if root_norm:
            root_nid = node_id("root", root_norm)
            upsert_node(root_nid, kind="root", label=root_norm, language=rec.get("language"), script=rec.get("script") or "")
            edges.append(
                {
                    "src": lemma_nid,
                    "dst": root_nid,
                    "type": "lemma_has_root",
                    "source": rec.get("source"),
                    "source_ref": rec.get("source_ref"),
                }
            )

        if binary_root:
            bin_nid = node_id("binary_root", binary_root)
            upsert_node(bin_nid, kind="binary_root", label=binary_root, language=rec.get("language"), script=rec.get("script") or "")
            if root_norm:
                edges.append({"src": root_nid, "dst": bin_nid, "type": "root_has_binary_root", "method": rec.get("binary_root_method")})
            else:
                edges.append({"src": lemma_nid, "dst": bin_nid, "type": "lemma_has_binary_root", "method": rec.get("binary_root_method")})

    with nodes_csv.open("w", encoding="utf-8", newline="") as fh:
        fieldnames = ["id", "type", "label", "language", "script", "lemma_status", "translit", "ipa"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for nid, row in sorted(nodes.items(), key=lambda kv: kv[0]):
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    with edges_csv.open("w", encoding="utf-8", newline="") as fh:
        fieldnames = ["src", "dst", "type", "method", "source", "source_ref"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for e in edges:
            writer.writerow({k: e.get(k, "") for k in fieldnames})

    return {"rows_in": total_rows, "nodes": len(nodes), "edges": len(edges)}


def main() -> None:
    ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--input", type=Path, default=Path("data/processed/arabic/classical/lexemes.jsonl"))
    ap.add_argument("--out-dir", type=Path, default=None, help="Output directory for nodes/edges CSVs (ignored if --nodes/--edges are set).")
    ap.add_argument("--nodes", type=Path, default=None, help="Path to nodes CSV (overrides --out-dir).")
    ap.add_argument("--edges", type=Path, default=None, help="Path to edges CSV (overrides --out-dir).")
    args = ap.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Missing input: {args.input}")

    out_dir = args.out_dir or Path("outputs/graphs")
    nodes_path = args.nodes or (out_dir / "binary_root_nodes.csv")
    edges_path = args.edges or (out_dir / "binary_root_edges.csv")

    stats = export_graph(args.input, nodes_path, edges_path)
    print(f"Wrote nodes: {nodes_path} (n={stats['nodes']})")
    print(f"Wrote edges: {edges_path} (n={stats['edges']})")


if __name__ == "__main__":
    main()
