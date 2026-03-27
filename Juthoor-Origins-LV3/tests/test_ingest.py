from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from juthoor_origins_lv3.ingest import build_leads


def test_build_leads_filters_and_classifies_edges() -> None:
    graph = {
        "nodes": {
            "ara:alpha": {"lang": "ara", "lemma": "ألف", "root": "الف"},
            "ara:beta": {"lang": "ara", "lemma": "باء", "root": "باء"},
            "eng:one": {"lang": "eng", "lemma": "one"},
            "lat:unus": {"lang": "lat", "lemma": "unus"},
            "grc:heis": {"lang": "grc", "lemma": "heis"},
            "eng:bee": {"lang": "eng", "lemma": "bee"},
        },
        "edges": [
            {
                "source": "ara:alpha",
                "target": "eng:one",
                "score": 0.9,
                "method": "direct_skeleton",
                "methods_fired": ["direct_skeleton", "position_weighted"],
            },
            {
                "source": "ara:alpha",
                "target": "lat:unus",
                "score": 0.86,
                "method": "reverse_root",
                "methods_fired": ["reverse_root", "ipa_scoring"],
            },
            {
                "source": "ara:alpha",
                "target": "grc:heis",
                "score": 0.8,
                "method": "metathesis",
                "methods_fired": ["metathesis"],
            },
            {
                "source": "ara:beta",
                "target": "eng:bee",
                "score": 0.95,
                "method": "direct_skeleton",
                "methods_fired": ["direct_skeleton", "position_weighted"],
            },
            {
                "source": "ara:alpha",
                "target": "eng:bee",
                "score": 0.65,
                "method": "ipa_scoring",
                "methods_fired": ["ipa_scoring"],
            },
        ],
    }

    leads = build_leads(graph)

    assert len(leads) == 3
    assert leads[0]["corridor_id"] == "CORRIDOR_02"
    assert leads[0]["anchor_level"] == "gold"
    assert leads[1]["corridor_id"] == "CORRIDOR_10"
    assert leads[1]["anchor_level"] == "gold"
    assert leads[2]["corridor_id"] == "CORRIDOR_06"
    assert leads[2]["anchor_level"] == "auto_brut"
