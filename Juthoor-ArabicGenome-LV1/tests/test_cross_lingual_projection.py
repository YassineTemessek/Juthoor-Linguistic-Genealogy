from __future__ import annotations

from juthoor_arabicgenome_lv1.factory.cross_lingual_projection import (
    build_semitic_projection_rows,
    normalize_arabic_lemma,
    projection_summary,
)


def test_normalize_arabic_lemma_handles_hamza_variants() -> None:
    assert normalize_arabic_lemma("أرض") == "ارض"
    assert normalize_arabic_lemma("رأى") == "راي"


def test_build_semitic_projection_rows_matches_arabic_benchmark_entries() -> None:
    root_rows = [
        {
            "root": "كتب",
            "binary_nucleus": "كت",
            "predicted_meaning": "جمع + نقش",
            "predicted_features": ["تجمع", "ظاهر"],
            "actual_features": ["تجمع"],
            "jaccard": 0.5,
            "weighted_jaccard": 0.5,
            "blended_jaccard": 0.65,
            "quranic_verse": "الكتاب",
        }
    ]
    benchmark_rows = [
        {
            "source": {"lang": "ara", "lemma": "كتب", "gloss": "write"},
            "target": {"lang": "heb", "lemma": "כתב", "gloss": "write"},
            "relation": "cognate",
            "confidence": 1.0,
        },
        {
            "source": {"lang": "lat", "lemma": "pater", "gloss": "father"},
            "target": {"lang": "grc", "lemma": "πατήρ", "gloss": "father"},
            "relation": "cognate",
            "confidence": 1.0,
        },
    ]

    rows = build_semitic_projection_rows(root_rows, benchmark_rows)
    assert len(rows) == 1
    assert rows[0]["source_root"] == "كتب"
    assert rows[0]["target_lang"] == "heb"
    assert rows[0]["relation"] == "cognate"
    assert rows[0]["projected_variants"]


def test_projection_summary_reports_coverage() -> None:
    benchmark_rows = [
        {"source": {"lang": "ara", "lemma": "كتب"}, "target": {"lang": "heb", "lemma": "כתב"}},
        {"source": {"lang": "ara", "lemma": "ملك"}, "target": {"lang": "arc", "lemma": "ܡܠܟ"}},
        {"source": {"lang": "lat", "lemma": "mater"}, "target": {"lang": "grc", "lemma": "μήτηρ"}},
    ]
    rows = [{"target_lang": "heb"}, {"target_lang": "arc"}]
    summary = projection_summary(rows, benchmark_rows)
    assert summary["benchmark_semitic_pairs"] == 2
    assert summary["matched_source_roots"] == 2
    assert summary["coverage"] == 1.0
    assert summary["by_target_lang"] == {"heb": 1, "arc": 1}
