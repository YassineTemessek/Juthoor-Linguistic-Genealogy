from __future__ import annotations

import json
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.corpora import CorpusInfo, CorpusSpec, clean_label, discover_corpora
from juthoor_cognatediscovery_lv2.discovery.reporting import write_leads
from juthoor_cognatediscovery_lv2.discovery.rerank import DiscoveryReranker
from juthoor_cognatediscovery_lv2.discovery.retrieval import get_cache_paths, resolve_corpus_path
from juthoor_cognatediscovery_lv2.discovery.scoring import DiscoveryScorer, rank_candidates


def test_clean_label_strips_noise():
    assert clean_label("Latin-English_Wiktionary_dictionary_stardict_filtered") == "Latin"
    assert clean_label("english_ipa_merged_pos") == "English IPA + POS"


def test_discover_corpora_prefers_lv0_processed(tmp_path: Path):
    base = tmp_path / "Juthoor-DataCore-LV0" / "data" / "processed" / "latin" / "classical"
    base.mkdir(parents=True)
    sample = base / "lexemes.jsonl"
    sample.write_text(
        json.dumps({"language": "lat", "stage": "classical", "lemma": "mater"}) + "\n",
        encoding="utf-8",
    )

    results = discover_corpora(tmp_path)
    assert results
    assert any(c.language == "lat" and c.stage == "classical" for c in results)


def test_discover_corpora_finds_root_family_outputs(tmp_path: Path):
    base = tmp_path / "Juthoor-CognateDiscovery-LV2" / "outputs" / "corpora"
    base.mkdir(parents=True)
    sample = base / "arabic_root_families.jsonl"
    sample.write_text(
        json.dumps(
            {
                "lang": "ara",
                "stage": "classical",
                "record_type": "root_family",
                "lemma": "بتك",
            }
        ) + "\n",
        encoding="utf-8",
    )

    results = discover_corpora(tmp_path)
    assert any(c.record_type == "root_family" and c.group == "Arabic Root Families" for c in results)


def test_write_leads_round_trip(tmp_path: Path):
    out_path = tmp_path / "out" / "leads.jsonl"
    leads = [{"source": {"lemma": "عين"}, "target": {"lemma": "עין"}}]
    write_leads(leads, out_path)
    lines = out_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["target"]["lemma"] == "עין"


def test_discovery_scorer_removes_temp_fields():
    candidates = {
        "x": {
            "scores": {"semantic": 0.9, "form": 0.8},
            "_source_fields": {"lemma": "عين", "lang": "ara", "root_norm": "عين"},
            "_target_fields": {"lemma": "עין", "lang": "heb", "root_norm": "عين"},
            "category": "strong_union",
        }
    }
    scored = DiscoveryScorer().score(candidates)
    assert len(scored) == 1
    assert "hybrid" in scored[0]
    assert scored[0]["hybrid"]["root_match_applied"] is True
    assert "_source_fields" not in scored[0]
    assert "_target_fields" not in scored[0]


def test_rank_candidates_prefers_higher_hybrid():
    rows = [
        {"category": "strong_union", "scores": {"semantic": 0.8, "form": 0.7}, "hybrid": {"combined_score": 0.4}},
        {"category": "strong_union", "scores": {"semantic": 0.7, "form": 0.6}, "hybrid": {"combined_score": 0.9}},
    ]
    ranked = rank_candidates(rows, max_out=10)
    assert ranked[0]["hybrid"]["combined_score"] == 0.9


def test_reranker_reads_hybrid_components():
    entry = {
        "scores": {"semantic": 0.7, "form": 0.6},
        "hybrid": {
            "components": {"orthography": 0.5, "sound": None, "skeleton": 0.4},
            "family_boost_applied": True,
        },
    }
    score = DiscoveryReranker().predict_one(entry)
    assert score > 0.0


def test_cache_paths_differ_for_different_corpora(tmp_path: Path):
    spec_a = CorpusSpec(lang="eng", stage="modern", path=Path("a.jsonl"))
    spec_b = CorpusSpec(lang="eng", stage="modern", path=Path("b.jsonl"))
    paths_a = get_cache_paths(tmp_path, "semantic", spec_a)
    paths_b = get_cache_paths(tmp_path, "semantic", spec_b)
    assert paths_a != paths_b


def test_resolve_corpus_path_prefers_existing_relative_path(tmp_path: Path, monkeypatch):
    corpus = tmp_path / "subset.jsonl"
    corpus.write_text(json.dumps({"lemma": "name"}) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    spec = CorpusSpec(lang="eng", stage="modern", path=Path("subset.jsonl"))
    assert resolve_corpus_path(spec, tmp_path / "repo").resolve() == corpus.resolve()
