from __future__ import annotations

import json
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.rerank import rerank_leads_file


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def test_rerank_leads_file_sorts_within_source(tmp_path: Path):
    model_path = tmp_path / "model.json"
    model_path.write_text(
        json.dumps(
            {
                "model_type": "logistic_regression",
                "bias": 0.0,
                "weights": {
                    "semantic": 1.0,
                    "form": 0.0,
                    "orthography": 0.0,
                    "sound": 0.0,
                    "skeleton": 0.0,
                    "family_boost": 0.0,
                },
            }
        ),
        encoding="utf-8",
    )
    leads_path = tmp_path / "leads.jsonl"
    out_path = tmp_path / "reranked.jsonl"
    _write_jsonl(
        leads_path,
        [
            {"source": {"lang": "ara", "lemma": "عين"}, "target": {"lang": "eng", "lemma": "eye"}, "scores": {"semantic": 0.2}, "hybrid": {"components": {}, "family_boost_applied": False}},
            {"source": {"lang": "ara", "lemma": "عين"}, "target": {"lang": "eng", "lemma": "spring"}, "scores": {"semantic": 0.8}, "hybrid": {"components": {}, "family_boost_applied": False}},
        ],
    )

    rerank_leads_file(model_path, leads_path, out_path)
    rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows[0]["target"]["lemma"] == "spring"
