from __future__ import annotations

from juthoor_arabicgenome_lv1.factory.cross_lingual_projection import (
    build_non_semitic_projection_rows,
    build_semitic_projection_rows,
    non_semitic_projection_summary,
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


def test_build_non_semitic_projection_rows_matches_english_entries() -> None:
    root_rows = [
        {
            "root": "برج",
            "binary_nucleus": "بر",
            "predicted_meaning": "ظهور + علو",
            "predicted_features": ["بروز", "ارتفاع"],
            "actual_features": ["بروز"],
            "jaccard": 0.5,
            "weighted_jaccard": 0.5,
            "blended_jaccard": 0.65,
            "quranic_verse": "بروج",
        }
    ]
    benchmark_rows = [
        {
            "source": {"lang": "ara", "lemma": "برج", "gloss": "tower"},
            "target": {"lang": "eng", "lemma": "burglar", "gloss": "burglar"},
            "relation": "cognate",
            "confidence": 0.9,
        },
        {
            "source": {"lang": "lat", "lemma": "pater", "gloss": "father"},
            "target": {"lang": "grc", "lemma": "πατήρ", "gloss": "father"},
            "relation": "cognate",
            "confidence": 1.0,
        },
    ]

    rows = build_non_semitic_projection_rows(root_rows, benchmark_rows)
    assert len(rows) == 1
    assert rows[0]["source_root"] == "برج"
    assert rows[0]["target_lang"] == "eng"
    assert rows[0]["projection_family"] == "english"


def test_build_non_semitic_projection_rows_resolves_simple_surface_form_to_root() -> None:
    root_rows = [
        {
            "root": "طرق",
            "binary_nucleus": "طر",
            "predicted_meaning": "امتداد + وصول",
            "predicted_features": ["امتداد", "وصول"],
            "actual_features": ["امتداد"],
            "jaccard": 0.5,
            "weighted_jaccard": 0.5,
            "blended_jaccard": 0.65,
            "quranic_verse": "الطارق",
        }
    ]
    benchmark_rows = [
        {
            "source": {"lang": "ara", "lemma": "طريق", "gloss": "path"},
            "target": {"lang": "eng", "lemma": "track", "gloss": "track"},
            "relation": "cognate",
            "confidence": 0.5,
        }
    ]

    rows = build_non_semitic_projection_rows(root_rows, benchmark_rows)
    assert len(rows) == 1
    assert rows[0]["source_root"] == "طرق"


def test_build_non_semitic_projection_rows_prefers_explicit_root_hint_for_compound_root() -> None:
    root_rows = [
        {
            "root": "رقق-رقرق",
            "binary_nucleus": "رق",
            "predicted_meaning": "امتداد + سطح",
            "predicted_features": ["امتداد", "سطح"],
            "actual_features": ["امتداد"],
            "jaccard": 0.5,
            "weighted_jaccard": 0.5,
            "blended_jaccard": 0.65,
            "quranic_verse": "رق",
        }
    ]
    benchmark_rows = [
        {
            "source": {"lang": "ara", "lemma": "رقّ", "gloss": "stretch", "root_norm": "رقق"},
            "target": {"lang": "eng", "lemma": "rack", "gloss": "rack"},
            "relation": "cognate",
            "confidence": 0.7,
        }
    ]

    rows = build_non_semitic_projection_rows(root_rows, benchmark_rows)
    assert len(rows) == 1
    assert rows[0]["source_root"] == "رقق-رقرق"


def test_non_semitic_projection_summary_reports_coverage() -> None:
    benchmark_rows = [
        {"source": {"lang": "ara", "lemma": "برج"}, "target": {"lang": "eng", "lemma": "burglar"}},
        {"source": {"lang": "ara", "lemma": "رق"}, "target": {"lang": "eng", "lemma": "rack"}},
        {"source": {"lang": "lat", "lemma": "mater"}, "target": {"lang": "grc", "lemma": "μήτηρ"}},
    ]
    rows = [{"target_lang": "eng"}]
    summary = non_semitic_projection_summary(rows, benchmark_rows)
    assert summary["benchmark_non_semitic_pairs"] == 2
    assert summary["matched_source_roots"] == 1
    assert summary["coverage"] == 0.5
    assert summary["by_target_lang"] == {"eng": 1}
