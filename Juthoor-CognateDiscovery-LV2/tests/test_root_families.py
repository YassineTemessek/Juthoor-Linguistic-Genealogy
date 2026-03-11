from __future__ import annotations

import json
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.root_families import (
    build_root_family_corpus,
    build_root_family_record,
)


def test_build_root_family_record_uses_muajam_fields():
    row = build_root_family_record(
        {
            "bab": "ب",
            "binary_root": "بت",
            "root": "بتك",
            "words": ["بتك", "يبتك"],
            "muajam_match": True,
            "semantic_score": 0.67,
            "binary_root_meaning": "القطع والانفصال",
            "axial_meaning": "القطع بدقة",
            "quran_example": "فليبتكن",
        }
    )
    assert row["lemma"] == "بتك"
    assert row["record_type"] == "root_family"
    assert "القطع" in row["meaning_text"]
    assert "words:" in row["form_text"]


def test_build_root_family_corpus_writes_jsonl(tmp_path: Path):
    input_dir = tmp_path / "genome_v2"
    input_dir.mkdir()
    (input_dir / "ب.jsonl").write_text(
        json.dumps({"bab": "ب", "binary_root": "بت", "root": "بتك", "words": ["بتك"], "muajam_match": True}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "root_families.jsonl"
    count = build_root_family_corpus(input_dir, output)
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert count == 1
    assert rows[0]["id"] == "rootfam:ara:بتك"
