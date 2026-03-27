from __future__ import annotations

import json
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.precomputed_assets import (
    build_historical_english_lookup,
    build_reverse_root_index,
    curate_english_corpus,
    english_ipa_skeleton,
)


def test_english_ipa_skeleton_strips_vowels() -> None:
    assert english_ipa_skeleton("kəˈtæb") == "ktb"


def test_curate_english_corpus_prefers_content_words(tmp_path: Path) -> None:
    src = tmp_path / "english.jsonl"
    src.write_text(
        "\n".join(
            [
                json.dumps({"lemma": "the", "ipa": "ðə", "pos": ["article"], "source_priority": 1}),
                json.dumps({"lemma": "track", "ipa": "træk", "pos": ["noun"], "source_priority": 1}),
                json.dumps({"lemma": "track", "ipa": "", "pos": ["noun"], "source_priority": 2}),
                json.dumps({"lemma": "go", "ipa": "goʊ", "pos": ["verb"], "source_priority": 1}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "curated.jsonl"
    summary = curate_english_corpus(src, out, max_entries=10)
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert summary["rows_written"] == 1
    assert rows[0]["lemma"] == "track"
    assert rows[0]["ipa_skeleton"] == "trk"


def test_build_reverse_root_index_groups_by_projected_skeleton(tmp_path: Path) -> None:
    src = tmp_path / "root_families.jsonl"
    src.write_text(
        json.dumps({"lemma": "طرق", "root_norm": "طرق", "binary_root": "طر", "word_count": 5, "meaning_text": "الطرق"}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "index.json"
    summary = build_reverse_root_index(src, out, projector=lambda root, target: ("track", "tarq"))
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert summary["indexed_skeletons"] >= 1
    assert "trck" in payload or "trq" in payload


def test_build_historical_english_lookup_extracts_old_meaning_and_stage_matches(tmp_path: Path) -> None:
    csv_path = tmp_path / "beyond.csv"
    csv_path.write_text(
        "english_word,english_meaning,arabic_root,arabic_translit,arabic_meaning,etymology_explanation,phonetic_rules,intermediate_langs,confidence,source_post_id,entry_type\n"
        "Sad,sad,سد,sd,,English 'Sad' corresponds to Arabic 'سد'. The text notes: أصل الكلمة كان يعني \"الامتلاء، الشبع\".,,Old English,0.65,1,single\n",
        encoding="utf-8",
    )
    old_path = tmp_path / "old.jsonl"
    old_path.write_text(
        json.dumps({"lemma": "sad", "meaning_text": "sated", "ipa": "sad"}) + "\n",
        encoding="utf-8",
    )
    middle_path = tmp_path / "mid.jsonl"
    middle_path.write_text(
        json.dumps({"lemma": "sad", "meaning_text": "firm; full", "ipa": "sad"}) + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "historical.jsonl"
    summary = build_historical_english_lookup(csv_path, old_path, middle_path, out)
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert summary["rows_with_historical_phrase"] == 1
    assert rows[0]["lemma"] == "sad"
    assert "الامتلاء، الشبع" in rows[0]["historical_phrases"]
    assert rows[0]["old_english_matches"][0]["meaning"] == "sated"
