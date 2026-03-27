"""
build_cognate_graph.py

Merge all discovery leads into a single cognate graph (dict-based, no networkx).

Usage:
    python build_cognate_graph.py [--min-score 0.55] [--output-dir outputs/]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Language normalisation
# ---------------------------------------------------------------------------

_LANG_ALIASES: dict[str, str] = {
    "ara-qur": "ara",
    "ara-classical": "ara",
    "ara-hf": "ara",
    "eng-hist": "eng",
}


def _norm_lang(raw: str) -> str:
    """Collapse dialect / dataset suffixes to canonical language code."""
    raw = raw.strip()
    if raw in _LANG_ALIASES:
        return _LANG_ALIASES[raw]
    # Generic: strip after first hyphen if second segment looks like a dataset tag
    # (e.g. "ara-qur", but keep "grc" untouched)
    parts = raw.split("-", 1)
    if len(parts) == 2 and len(parts[1]) <= 4:
        return parts[0]
    return raw


def _node_id(lang: str, lemma: str) -> str:
    return f"{lang}:{lemma}"


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _iter_leads(leads_dir: Path, patterns: list[str]) -> int:
    """Yield (path, line_number, record) for every matching file."""
    for pattern in patterns:
        for path in sorted(leads_dir.glob(pattern)):
            if path.stat().st_size == 0:
                continue
            with path.open(encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield path, lineno, json.loads(line)
                    except json.JSONDecodeError:
                        print(
                            f"[WARN] JSON parse error in {path.name}:{lineno} — skipped",
                            file=sys.stderr,
                        )


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------

def build_graph(leads_dir: Path, min_score: float) -> dict:
    """
    Read all matching JSONL files and return the cognate graph dict.
    Deduplication: keep highest-scoring record per (source_lemma, target_lemma) pair.
    """
    patterns = ["discovery_ara_*.jsonl", "full_discovery_*.jsonl"]

    # Dedup store: key=(src_lang, src_lemma, tgt_lang, tgt_lemma) → best record
    best: dict[tuple, dict] = {}
    files_read: set[str] = set()

    for path, _lineno, rec in _iter_leads(leads_dir, patterns):
        files_read.add(path.name)

        src = rec.get("source", {})
        tgt = rec.get("target", {})
        scores = rec.get("scores", {})

        src_lang = _norm_lang(src.get("lang", ""))
        tgt_lang = _norm_lang(tgt.get("lang", ""))
        src_lemma = src.get("lemma", "").strip()
        tgt_lemma = tgt.get("lemma", "").strip()

        if not src_lemma or not tgt_lemma or not src_lang or not tgt_lang:
            continue

        score = float(scores.get("multi_method_best", scores.get("final_combined", 0.0)))

        if score < min_score:
            continue

        key = (src_lang, src_lemma, tgt_lang, tgt_lemma)
        if key not in best or score > best[key]["_score"]:
            best[key] = {
                "_score": score,
                "src_lang": src_lang,
                "src_lemma": src_lemma,
                "src_root": src.get("root", src.get("root_norm", "")),
                "src_gloss": src.get("gloss", ""),
                "tgt_lang": tgt_lang,
                "tgt_lemma": tgt_lemma,
                "tgt_gloss": tgt.get("gloss", ""),
                "method": scores.get("best_method", ""),
                "methods_fired": rec.get("evidence", {}).get("methods_fired", []),
                "lang_pair": f"{src_lang}-{tgt_lang}",
            }

    print(
        f"[INFO] Files scanned: {len(files_read)}, "
        f"unique pairs (score≥{min_score}): {len(best)}",
        file=sys.stderr,
    )

    # ------------------------------------------------------------------
    # Build nodes
    # ------------------------------------------------------------------
    nodes: dict[str, dict] = {}
    connection_counter: dict[str, int] = defaultdict(int)

    for r in best.values():
        sid = _node_id(r["src_lang"], r["src_lemma"])
        tid = _node_id(r["tgt_lang"], r["tgt_lemma"])

        if sid not in nodes:
            nodes[sid] = {
                "lang": r["src_lang"],
                "lemma": r["src_lemma"],
                "root": r["src_root"],
                "gloss": r["src_gloss"],
                "connections": 0,
            }
        if tid not in nodes:
            nodes[tid] = {
                "lang": r["tgt_lang"],
                "lemma": r["tgt_lemma"],
                "root": "",
                "gloss": r["tgt_gloss"],
                "connections": 0,
            }

        connection_counter[sid] += 1
        connection_counter[tid] += 1

    for nid, count in connection_counter.items():
        nodes[nid]["connections"] = count

    # ------------------------------------------------------------------
    # Build edges
    # ------------------------------------------------------------------
    edges: list[dict] = []
    for r in best.values():
        edges.append(
            {
                "source": _node_id(r["src_lang"], r["src_lemma"]),
                "target": _node_id(r["tgt_lang"], r["tgt_lemma"]),
                "score": round(r["_score"], 4),
                "method": r["method"],
                "methods_fired": r["methods_fired"],
                "lang_pair": r["lang_pair"],
            }
        )

    # Sort edges by descending score for readability
    edges.sort(key=lambda e: e["score"], reverse=True)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------
    lang_pair_counts: dict[str, int] = defaultdict(int)
    nodes_by_lang: dict[str, int] = defaultdict(int)
    score_sum = 0.0

    for e in edges:
        lang_pair_counts[e["lang_pair"]] += 1
        score_sum += e["score"]

    for n in nodes.values():
        nodes_by_lang[n["lang"]] += 1

    avg_score = round(score_sum / len(edges), 4) if edges else 0.0
    languages = sorted(nodes_by_lang.keys())

    stats = {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "languages": languages,
        "lang_pair_counts": dict(sorted(lang_pair_counts.items(), key=lambda x: -x[1])),
        "avg_score": avg_score,
        "nodes_by_lang": dict(sorted(nodes_by_lang.items())),
        "files_read": sorted(files_read),
        "min_score_filter": min_score,
    }

    return {"nodes": nodes, "edges": edges, "stats": stats}


# ---------------------------------------------------------------------------
# Summary report
# ---------------------------------------------------------------------------

def _safe_print(text: str) -> None:
    """Print with fallback encoding for Windows consoles that lack Unicode support."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


def _print_summary(graph: dict) -> None:
    stats = graph["stats"]
    nodes = graph["nodes"]
    edges = graph["edges"]

    _safe_print("\n" + "=" * 60)
    print("COGNATE GRAPH SUMMARY")
    print("=" * 60)
    print(f"Total nodes : {stats['total_nodes']:,}")
    print(f"Total edges : {stats['total_edges']:,}")
    print(f"Languages   : {', '.join(stats['languages'])}")
    print(f"Avg score   : {stats['avg_score']}")
    print(f"Min-score   : {stats['min_score_filter']}")

    print("\n--- Nodes per language ---")
    for lang, count in sorted(stats["nodes_by_lang"].items()):
        print(f"  {lang:<10} {count:>6,}")

    print("\n--- Edges per language pair ---")
    for pair, count in stats["lang_pair_counts"].items():
        print(f"  {pair:<16} {count:>6,}")

    # Top 20 most-connected Arabic roots
    ara_nodes = [
        (nid, n) for nid, n in nodes.items() if n["lang"] == "ara"
    ]
    ara_nodes.sort(key=lambda x: x[1]["connections"], reverse=True)
    top20 = ara_nodes[:20]

    if top20:
        print("\n--- Top 20 most-connected Arabic roots ---")
        print(f"  {'Root':<12} {'Lemma':<20} {'Connections':>11}")
        print("  " + "-" * 45)
        for nid, n in top20:
            root = n["root"] or n["lemma"]
            print(f"  {root:<12} {n['lemma']:<20} {n['connections']:>11,}")

    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build a cross-language cognate graph from discovery leads."
    )
    p.add_argument(
        "--min-score",
        type=float,
        default=0.55,
        help="Minimum multi_method_best score to include an edge (default: 0.55)",
    )
    p.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help=(
            "Directory where cognate_graph.json is written. "
            "Defaults to <script_dir>/../../outputs/ relative to this script."
        ),
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent  # scripts/discovery → scripts → LV2 root
    leads_dir = repo_root / "outputs" / "leads"

    if not leads_dir.exists():
        print(f"[ERROR] Leads directory not found: {leads_dir}", file=sys.stderr)
        sys.exit(1)

    if args.output_dir is not None:
        out_dir = Path(args.output_dir)
    else:
        out_dir = repo_root / "outputs"

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "cognate_graph.json"

    print(f"[INFO] Scanning leads in: {leads_dir}", file=sys.stderr)
    print(f"[INFO] min-score = {args.min_score}", file=sys.stderr)

    graph = build_graph(leads_dir, min_score=args.min_score)

    print(f"[INFO] Writing graph to: {out_path}", file=sys.stderr)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(graph, fh, ensure_ascii=False, indent=2)

    _print_summary(graph)
    print(f"[DONE] {out_path}")


if __name__ == "__main__":
    main()
