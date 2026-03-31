from __future__ import annotations

import json
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.artifact_paths import resolve_cognate_graph_path


class CrossPairScorer:
    """Count cross-language convergence support for Arabic graph nodes."""

    def __init__(self, graph_path: Path | str | None = None) -> None:
        self._graph_path = Path(graph_path) if graph_path is not None else self._default_graph_path()
        graph = self._load_graph(self._graph_path)
        self._nodes: dict[str, dict] = graph.get("nodes", {})
        self._edges: list[dict] = graph.get("edges", [])

    @staticmethod
    def _default_graph_path() -> Path:
        return resolve_cognate_graph_path()

    @staticmethod
    def _load_graph(graph_path: Path) -> dict:
        with graph_path.open(encoding="utf-8") as fh:
            return json.load(fh)

    def _matching_arabic_node_ids(self, root: str) -> list[str]:
        query = root.strip()
        if not query:
            return []

        exact_node_id = f"ara:{query}"
        if exact_node_id in self._nodes:
            return [exact_node_id]

        matches: list[str] = []
        for node_id, node in self._nodes.items():
            if node.get("lang") != "ara":
                continue
            if node.get("root") == query or node.get("lemma") == query:
                matches.append(node_id)
        return matches

    def convergent_evidence(self, root: str) -> dict:
        matched_node_ids = set(self._matching_arabic_node_ids(root))
        languages = {
            target_node.get("lang")
            for edge in self._edges
            if edge.get("source") in matched_node_ids
            for target_node in [self._nodes.get(edge.get("target"), {})]
            if target_node.get("lang") and target_node.get("lang") != "ara"
        }
        languages_matched = sorted(languages)
        total_target_langs = len(languages_matched)
        convergence_score = min(total_target_langs / 5.0, 1.0)
        return {
            "languages_matched": languages_matched,
            "total_target_langs": total_target_langs,
            "convergence_score": convergence_score,
        }
