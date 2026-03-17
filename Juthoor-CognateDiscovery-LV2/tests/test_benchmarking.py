from __future__ import annotations

import json
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.benchmarking import (
    _norm_lang,
    apply_gloss_overrides,
    build_root_family_benchmark_source,
    compare_metrics,
    compare_lead_runs,
    evaluate_leads_against_benchmarks,
    extract_benchmark_subset,
    filter_available_benchmark_pairs,
    load_gloss_overrides,
    load_combined_benchmark,
    write_jsonl,
)
from juthoor_cognatediscovery_lv2.discovery.evaluation import BenchmarkPair


def test_extract_benchmark_subset_matches_requested_side():
    pairs = [
        BenchmarkPair("ara", "بيت", "eng", "booth", "cognate", source_gloss="house"),
        BenchmarkPair("ara", "كلب", "eng", "dog", "negative_translation", source_gloss="dog"),
    ]
    corpus_rows = [
        {"lang": "ara", "lemma": "بيت", "lexeme_id": "ara1"},
        {"lang": "ara", "lemma": "كلب", "lexeme_id": "ara2"},
        {"lang": "ara", "lemma": "شمس", "lexeme_id": "ara3"},
    ]

    subset = extract_benchmark_subset(corpus_rows, pairs, lang="ara", side="source")
    assert [row["lemma"] for row in subset] == ["بيت", "كلب"]
    assert subset[0]["short_gloss"] == "house"


def test_extract_benchmark_subset_prefers_manual_overrides():
    pairs = [BenchmarkPair("ara", "أرض", "eng", "earth", "cognate", source_gloss="earth")]
    corpus_rows = [{"lang": "ara", "lemma": "أرض", "lexeme_id": "ara1", "short_gloss": "bad gloss"}]
    overrides = {("ara", "أرض"): "الأرض / اليابسة"}
    subset = extract_benchmark_subset(
        corpus_rows,
        pairs,
        lang="ara",
        side="source",
        gloss_overrides=overrides,
    )
    assert subset[0]["short_gloss"] == "الأرض / اليابسة"


def test_load_gloss_overrides_reads_lang_lemma_keys(tmp_path: Path):
    path = tmp_path / "gloss.json"
    path.write_text(json.dumps({"ara:أرض": "الأرض / اليابسة"}, ensure_ascii=False), encoding="utf-8")
    overrides = load_gloss_overrides(path)
    assert overrides[("ara", "أرض")] == "الأرض / اليابسة"


def test_filter_available_benchmark_pairs_only_keeps_present_rows():
    pairs = [
        BenchmarkPair("ara", "بيت", "eng", "booth", "cognate"),
        BenchmarkPair("ara", "كلب", "eng", "dog", "negative_translation"),
    ]
    available = filter_available_benchmark_pairs(
        pairs,
        source_rows=[{"lang": "ara", "lemma": "بيت"}],
        target_rows=[{"lang": "eng", "lemma": "booth"}],
    )
    assert len(available) == 1
    assert available[0]["source"]["lemma"] == "بيت"


def test_build_root_family_benchmark_source_preserves_benchmark_lemma():
    source_rows = [
        {"lang": "ara", "lemma": "بيت", "root_norm": "بيت", "short_gloss": "البيت / المسكن", "meaning_text": "old"}
    ]
    root_family_rows = [
        {
            "lang": "ara",
            "lemma": "بيت",
            "root_norm": "بيت",
            "words": ["بيت", "مبيت"],
            "meaning_text": "dwelling family",
            "gloss_plain": "dwelling family",
            "word_count": 2,
            "binary_root": "بي",
        }
    ]
    rows = build_root_family_benchmark_source(source_rows, root_family_rows)
    assert rows[0]["lemma"] == "بيت"
    assert rows[0]["record_type"] == "root_family_source"
    assert rows[0]["root_family_lemma"] == "بيت"
    assert rows[0]["short_gloss"] == "البيت / المسكن"
    assert "words: بيت, مبيت" in rows[0]["form_text"]


def test_compare_metrics_reports_deltas():
    comparison = compare_metrics(
        {"recall": 1.0, "mrr": 0.5, "ndcg": 0.6},
        {"recall": 1.0, "mrr": 0.7, "ndcg": 0.65},
    )
    assert comparison["delta"]["mrr"] == 0.2
    assert comparison["delta"]["ndcg"] == 0.05
    assert comparison["improved"] is True


def test_write_jsonl_round_trips(tmp_path: Path):
    path = tmp_path / "rows.jsonl"
    write_jsonl(path, [{"lemma": "بيت"}, {"lemma": "كلب"}])
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows[1]["lemma"] == "كلب"


def test_load_combined_benchmark_merges_files(tmp_path: Path):
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    write_jsonl(a, [{"source": {"lang": "ara", "lemma": "بيت"}, "target": {"lang": "eng", "lemma": "booth"}, "relation": "cognate"}])
    write_jsonl(b, [{"source": {"lang": "ara", "lemma": "كلب"}, "target": {"lang": "eng", "lemma": "dog"}, "relation": "negative_translation"}])
    rows = load_combined_benchmark([a, b])
    assert len(rows) == 2


def test_compare_lead_runs_reports_improvement(tmp_path: Path):
    benchmark = tmp_path / "benchmark.jsonl"
    baseline = tmp_path / "baseline.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    write_jsonl(
        benchmark,
        [{"source": {"lang": "ara", "lemma": "بيت"}, "target": {"lang": "eng", "lemma": "booth"}, "relation": "cognate"}],
    )
    write_jsonl(
        baseline,
        [
            {"source": {"lang": "ara", "lemma": "بيت"}, "target": {"lang": "eng", "lemma": "stall"}},
            {"source": {"lang": "ara", "lemma": "بيت"}, "target": {"lang": "eng", "lemma": "booth"}},
        ],
    )
    write_jsonl(
        candidate,
        [{"source": {"lang": "ara", "lemma": "بيت"}, "target": {"lang": "eng", "lemma": "booth"}}],
    )
    comparison = compare_lead_runs(baseline, candidate, [benchmark], top_k=5)
    assert comparison["delta"]["mrr"] > 0.0


def test_evaluate_leads_against_benchmarks(tmp_path: Path):
    benchmark = tmp_path / "benchmark.jsonl"
    leads = tmp_path / "leads.jsonl"
    write_jsonl(
        benchmark,
        [{"source": {"lang": "ara", "lemma": "بيت"}, "target": {"lang": "eng", "lemma": "booth"}, "relation": "cognate"}],
    )
    write_jsonl(
        leads,
        [{"source": {"lang": "ara", "lemma": "بيت"}, "target": {"lang": "eng", "lemma": "booth"}}],
    )
    metrics = evaluate_leads_against_benchmarks(leads, [benchmark], top_k=5)
    assert metrics["mrr"] == 1.0


# --- ISO 639-1 / 639-3 normalization tests ---

def test_norm_lang_maps_fa_to_fas():
    assert _norm_lang("fa") == "fas"
    assert _norm_lang("fas") == "fas"
    assert _norm_lang("FA") == "fas"   # case insensitive


def test_norm_lang_maps_he_to_heb():
    assert _norm_lang("he") == "heb"
    assert _norm_lang("heb") == "heb"
    assert _norm_lang("HEB") == "heb"


def test_norm_lang_maps_ar_to_ara():
    assert _norm_lang("ar") == "ara"
    assert _norm_lang("ara") == "ara"


def test_norm_lang_maps_en_to_eng():
    assert _norm_lang("en") == "eng"
    assert _norm_lang("eng") == "eng"


def test_norm_lang_passes_through_unknown_codes():
    assert _norm_lang("grc") == "grc"
    assert _norm_lang("arc") == "arc"
    assert _norm_lang("xyz") == "xyz"


def test_extract_benchmark_subset_matches_persian_corpus():
    """Benchmark pairs with lang='fa' must match corpus rows with language='fas'."""
    pairs = [
        BenchmarkPair("ara", "باد", "fa", "باد", "cognate", target_gloss="wind"),
    ]
    corpus_rows = [
        {"language": "fas", "lemma": "باد", "lexeme_id": "fas1"},
        {"language": "fas", "lemma": "آب", "lexeme_id": "fas2"},
    ]
    subset = extract_benchmark_subset(corpus_rows, pairs, lang="fa", side="target")
    assert len(subset) == 1
    assert subset[0]["lemma"] == "باد"
    assert subset[0]["short_gloss"] == "wind"


def test_extract_benchmark_subset_fa_and_fas_are_equivalent():
    """Calling with lang='fas' should find the same rows as lang='fa'."""
    pairs = [
        BenchmarkPair("ara", "باد", "fa", "باد", "cognate"),
    ]
    corpus_rows = [{"language": "fas", "lemma": "باد"}]
    subset_fa = extract_benchmark_subset(corpus_rows, pairs, lang="fa", side="target")
    subset_fas = extract_benchmark_subset(corpus_rows, pairs, lang="fas", side="target")
    assert len(subset_fa) == 1
    assert len(subset_fas) == 1


def test_filter_available_benchmark_pairs_persian_cross_code():
    """Benchmark pair with target_lang='fa' should match corpus row with language='fas'."""
    pairs = [
        BenchmarkPair("ara", "باد", "fa", "باد", "cognate"),
        BenchmarkPair("ara", "آب", "fa", "آب", "cognate"),
    ]
    available = filter_available_benchmark_pairs(
        pairs,
        source_rows=[
            {"lang": "ara", "lemma": "باد"},
            {"lang": "ara", "lemma": "آب"},
        ],
        target_rows=[
            {"language": "fas", "lemma": "باد"},
            # آب intentionally absent to test partial match
        ],
    )
    assert len(available) == 1
    assert available[0]["target"]["lemma"] == "باد"
