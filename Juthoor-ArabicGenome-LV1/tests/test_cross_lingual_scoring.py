from __future__ import annotations

from juthoor_arabicgenome_lv1.factory.cross_lingual_scoring import (
    best_similarity,
    latin_target_variants,
    score_projection_row,
    summarize_projection_scores,
    target_variants,
)


def test_target_variants_expand_hebrew_letters() -> None:
    variants = target_variants("כתב")
    assert "ktb" in variants
    assert "ctb" in variants


def test_score_projection_row_detects_exact_hit() -> None:
    row = {
        "target_lang": "heb",
        "target_lemma": "כתב",
        "projected_variants": ["ktb", "kdb"],
    }
    scored = score_projection_row(row)
    assert scored["exact_projection_hit"] is True
    assert scored["binary_prefix_hit"] is True
    assert scored["best_projection_similarity"] == 1.0


def test_best_similarity_finds_close_variant() -> None:
    score, variant = best_similarity(["mlk"], "מלך")
    assert score > 0.5
    assert variant is not None


def test_latin_target_variants_expand_common_spelling_equivalents() -> None:
    variants = latin_target_variants("rack")
    assert "rack" in variants
    assert "rak" in variants
    assert "rck" in variants


def test_score_projection_row_detects_latin_script_exact_hit_after_normalization() -> None:
    row = {
        "target_lang": "eng",
        "target_lemma": "rack",
        "projected_variants": ["rak", "raq"],
    }
    scored = score_projection_row(row)
    assert scored["exact_projection_hit"] is True
    assert "rak" in scored["target_variants"]
    assert "rak" in scored["normalized_projected_variants"]


def test_summarize_projection_scores_aggregates_by_language() -> None:
    rows = [
        {"target_lang": "heb", "exact_projection_hit": True, "binary_prefix_hit": True, "best_projection_similarity": 1.0},
        {"target_lang": "heb", "exact_projection_hit": False, "binary_prefix_hit": True, "best_projection_similarity": 0.66},
        {"target_lang": "arc", "exact_projection_hit": False, "binary_prefix_hit": False, "best_projection_similarity": 0.25},
    ]
    summary = summarize_projection_scores(rows)
    assert summary["rows"] == 3
    assert summary["exact_hits"] == 1
    assert summary["binary_hits"] == 2
    assert summary["by_target_lang"]["heb"]["count"] == 2
