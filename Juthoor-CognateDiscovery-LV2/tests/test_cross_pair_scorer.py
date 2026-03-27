from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.cross_pair_scorer import CrossPairScorer


def _make_local_tmp_dir() -> Path:
    base = Path("Juthoor-CognateDiscovery-LV2/.pytest_local")
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"cross-pair-{uuid.uuid4().hex}"
    path.mkdir()
    return path


def test_convergent_evidence_counts_distinct_target_languages():
    tmp_dir = _make_local_tmp_dir()
    graph_path = tmp_dir / "cognate_graph.json"
    graph_path.write_text(
        json.dumps(
            {
                "nodes": {
                    "ara:اسم": {"lang": "ara", "lemma": "اسم", "root": "سمو"},
                    "eng:name": {"lang": "eng", "lemma": "name", "root": ""},
                    "eng:nomen": {"lang": "eng", "lemma": "nomen", "root": ""},
                    "lat:nomen": {"lang": "lat", "lemma": "nomen", "root": ""},
                },
                "edges": [
                    {"source": "ara:اسم", "target": "eng:name"},
                    {"source": "ara:اسم", "target": "eng:nomen"},
                    {"source": "ara:اسم", "target": "lat:nomen"},
                ],
                "stats": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    try:
        scorer = CrossPairScorer(graph_path)
        assert scorer.convergent_evidence("اسم") == {
            "languages_matched": ["eng", "lat"],
            "total_target_langs": 2,
            "convergence_score": 0.4,
        }
    finally:
        shutil.rmtree(tmp_dir)


def test_convergent_evidence_matches_root_across_multiple_arabic_nodes():
    tmp_dir = _make_local_tmp_dir()
    graph_path = tmp_dir / "cognate_graph.json"
    graph_path.write_text(
        json.dumps(
            {
                "nodes": {
                    "ara:اسم": {"lang": "ara", "lemma": "اسم", "root": "سمو"},
                    "ara:سمة": {"lang": "ara", "lemma": "سمة", "root": "سمو"},
                    "eng:name": {"lang": "eng", "lemma": "name", "root": ""},
                    "lat:nomen": {"lang": "lat", "lemma": "nomen", "root": ""},
                    "grc:ὄνομα": {"lang": "grc", "lemma": "ὄνομα", "root": ""},
                    "heb:שם": {"lang": "heb", "lemma": "שם", "root": ""},
                    "arc:ܫܡܐ": {"lang": "arc", "lemma": "ܫܡܐ", "root": ""},
                    "uga:šm": {"lang": "uga", "lemma": "šm", "root": ""},
                    "ara:وسم": {"lang": "ara", "lemma": "وسم", "root": "وسم"},
                },
                "edges": [
                    {"source": "ara:اسم", "target": "eng:name"},
                    {"source": "ara:اسم", "target": "lat:nomen"},
                    {"source": "ara:سمة", "target": "grc:ὄνομα"},
                    {"source": "ara:سمة", "target": "heb:שם"},
                    {"source": "ara:سمة", "target": "arc:ܫܡܐ"},
                    {"source": "ara:سمة", "target": "uga:šm"},
                    {"source": "ara:وسم", "target": "eng:name"},
                ],
                "stats": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    try:
        scorer = CrossPairScorer(graph_path)
        result = scorer.convergent_evidence("سمو")
        assert result["languages_matched"] == ["arc", "eng", "grc", "heb", "lat", "uga"]
        assert result["total_target_langs"] == 6
        assert result["convergence_score"] == 1.0
    finally:
        shutil.rmtree(tmp_dir)


def test_convergent_evidence_uses_default_lv2_graph_asset():
    scorer = CrossPairScorer()
    graph_path = Path("Juthoor-CognateDiscovery-LV2/outputs/cognate_graph.json")
    graph = json.loads(graph_path.read_text(encoding="utf-8"))

    first_ara_node_id, first_ara_node = next(
        (node_id, node) for node_id, node in graph["nodes"].items() if node.get("lang") == "ara"
    )
    expected_languages = sorted(
        {
            graph["nodes"][edge["target"]]["lang"]
            for edge in graph["edges"]
            if edge.get("source") == first_ara_node_id and graph["nodes"][edge["target"]]["lang"] != "ara"
        }
    )

    assert scorer.convergent_evidence(first_ara_node["lemma"]) == {
        "languages_matched": expected_languages,
        "total_target_langs": len(expected_languages),
        "convergence_score": min(len(expected_languages) / 5.0, 1.0),
    }
