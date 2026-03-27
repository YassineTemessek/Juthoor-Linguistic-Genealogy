from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

METHOD_CORRIDOR_MAP: dict[str, str] = {
    "article_detection": "CORRIDOR_01",
    "direct_skeleton": "CORRIDOR_02",
    "emphatic_collapse": "CORRIDOR_03",
    "guttural_projection": "CORRIDOR_04",
    "ipa_scoring": "CORRIDOR_05",
    "metathesis": "CORRIDOR_06",
    "morpheme_decomposition": "CORRIDOR_07",
    "multi_hop_chain": "CORRIDOR_08",
    "position_weighted": "CORRIDOR_09",
    "reverse_root": "CORRIDOR_10",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def input_graph_path() -> Path:
    return repo_root() / "Juthoor-CognateDiscovery-LV2" / "outputs" / "cognate_graph.json"


def output_leads_path() -> Path:
    return repo_root() / "Juthoor-Origins-LV3" / "data" / "leads" / "validated_leads.jsonl"


def load_cognate_graph(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_methods(edge: dict[str, Any]) -> list[str]:
    methods = edge.get("methods_fired") or []
    if not methods and edge.get("method"):
        methods = [edge["method"]]
    return sorted({str(method) for method in methods if method})


def build_root_language_counts(
    edges: list[dict[str, Any]],
    nodes: dict[str, dict[str, Any]],
) -> dict[str, int]:
    languages_by_root: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        if float(edge.get("score", 0.0)) < 0.7:
            continue

        source = nodes.get(edge.get("source", ""), {})
        target = nodes.get(edge.get("target", ""), {})
        if source.get("lang") != "ara":
            continue
        if target.get("lang") in {None, "", "ara"}:
            continue

        root = str(source.get("root") or "").strip()
        if not root:
            continue

        languages_by_root[root].add(str(target["lang"]))
    return {root: len(languages) for root, languages in languages_by_root.items()}


def classify_anchor_level(
    *,
    score: float,
    target_language_count: int,
    method_count: int,
) -> str:
    if score > 0.85 and target_language_count >= 3:
        return "gold"
    if score > 0.70 and method_count >= 2:
        return "silver"
    return "auto_brut"


def build_leads(graph: dict[str, Any]) -> list[dict[str, Any]]:
    edges = graph.get("edges", [])
    nodes = graph.get("nodes", {})
    root_language_counts = build_root_language_counts(edges, nodes)
    leads: list[dict[str, Any]] = []

    for edge in edges:
        score = float(edge.get("score", 0.0))
        if score < 0.7:
            continue

        source = nodes.get(edge.get("source", ""), {})
        target = nodes.get(edge.get("target", ""), {})
        if source.get("lang") != "ara":
            continue
        if target.get("lang") in {None, "", "ara"}:
            continue

        root = str(source.get("root") or "").strip()
        if root_language_counts.get(root, 0) < 2:
            continue

        method = str(edge.get("method") or "").strip()
        if method not in METHOD_CORRIDOR_MAP:
            raise ValueError(f"Unmapped method for corridor assignment: {method!r}")

        methods = canonical_methods(edge)
        lead = {
            "source_lang": str(source.get("lang") or ""),
            "source_lemma": str(source.get("lemma") or ""),
            "target_lang": str(target.get("lang") or ""),
            "target_lemma": str(target.get("lemma") or ""),
            "score": score,
            "method": method,
            "corridor_id": METHOD_CORRIDOR_MAP[method],
            "anchor_level": classify_anchor_level(
                score=score,
                target_language_count=root_language_counts[root],
                method_count=len(methods),
            ),
        }
        leads.append(lead)
    return leads


def write_jsonl(leads: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for lead in leads:
            handle.write(json.dumps(lead, ensure_ascii=False) + "\n")


def print_summary(leads: list[dict[str, Any]]) -> None:
    by_anchor = Counter(lead["anchor_level"] for lead in leads)
    by_corridor = Counter(lead["corridor_id"] for lead in leads)
    by_language_pair = Counter(
        f"{lead['source_lang']}-{lead['target_lang']}" for lead in leads
    )

    print(f"total leads: {len(leads)}")
    print("by anchor level:")
    for anchor_level, count in sorted(by_anchor.items()):
        print(f"  {anchor_level}: {count}")

    print("by corridor:")
    for corridor_id, count in sorted(by_corridor.items()):
        print(f"  {corridor_id}: {count}")

    print("by language pair:")
    for language_pair, count in sorted(by_language_pair.items()):
        print(f"  {language_pair}: {count}")


def main() -> None:
    graph = load_cognate_graph(input_graph_path())
    leads = build_leads(graph)
    write_jsonl(leads, output_leads_path())
    print_summary(leads)


if __name__ == "__main__":
    main()
