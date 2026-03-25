from __future__ import annotations

from juthoor_arabicgenome_lv1.factory.independent_letter_derivation import (
    compare_scholars,
    derive_independent_letter_meanings,
    derive_letter_meaning,
    render_independent_letter_genome_markdown,
)


def test_derive_letter_meaning_prefers_shared_exact_features() -> None:
    entry = {
        "letter": "ب",
        "as_letter1": [
            {"nucleus": "بد", "shared_meaning": "ظهور", "features": ["ظهور"], "member_count": 9},
            {"nucleus": "بع", "shared_meaning": "خروج", "features": ["خروج"], "member_count": 8},
        ],
        "as_letter2": [
            {"nucleus": "جب", "shared_meaning": "بروز", "features": ["بروز"], "member_count": 9},
            {"nucleus": "نب", "shared_meaning": "صعود", "features": ["صعود"], "member_count": 4},
        ],
        "count_l1": 2,
        "count_l2": 2,
        "total": 4,
    }
    derived = derive_letter_meaning(entry)
    assert derived["selected_features"] == ["بروز"]
    assert derived["structure"] == "sparse"
    assert derived["confidence"] == "low"


def test_derive_letter_meaning_uses_category_fallback_when_exact_overlap_missing() -> None:
    entry = {
        "letter": "ت",
        "as_letter1": [
            {"nucleus": "تر", "shared_meaning": "قوة", "features": ["قوة"], "member_count": 6},
            {"nucleus": "تن", "shared_meaning": "ضغط", "features": ["ضغط"], "member_count": 4},
        ],
        "as_letter2": [
            {"nucleus": "قط", "shared_meaning": "ضغط", "features": ["ضغط"], "member_count": 7},
            {"nucleus": "بط", "shared_meaning": "إمساك", "features": ["إمساك"], "member_count": 5},
        ],
        "count_l1": 2,
        "count_l2": 2,
        "total": 4,
    }
    derived = derive_letter_meaning(entry)
    assert derived["selected_features"] == ["إمساك"]
    assert derived["empirical_meaning_ar"] == "إمساك + احتباس"


def test_compare_scholars_classifies_match_and_conflict() -> None:
    derived_rows = [
        {
            "letter": "ب",
            "selected_features": ["خروج"],
        }
    ]
    scholar_rows = [
        {"letter": "ب", "scholar": "jabal", "atomic_features": ["تجمع"]},
        {"letter": "ب", "scholar": "asim_al_masri", "atomic_features": ["خروج"]},
    ]
    compared = compare_scholars(derived_rows, scholar_rows)[0]["scholar_comparison"]
    assert compared["asim_al_masri"]["classification"] == "match"
    assert compared["jabal"]["classification"] in {"partial", "conflict"}


def test_render_independent_letter_genome_markdown_contains_letter_sections() -> None:
    rows = compare_scholars(
        [
            {
                "letter": "ب",
                "count_l1": 2,
                "count_l2": 2,
                "total_nuclei": 4,
                "position_summaries": {
                    "as_letter1": {"top_features": [{"item": "خروج", "weight": 8, "rate": 0.8}]},
                    "as_letter2": {"top_features": [{"item": "خروج", "weight": 9, "rate": 0.9}]},
                },
                "shared_features": [{"feature": "خروج", "left_rate": 0.8, "right_rate": 0.9, "intersection_score": 0.8}],
                "shared_categories": [],
                "selected_features": ["خروج"],
                "raw_semantic_skeleton_ar": "خروج",
                "raw_semantic_skeleton_en": "emergence",
                "semantic_clusters": [
                    {
                        "label_ar": "ظهور + خروج",
                        "left_rate": 0.8,
                        "right_rate": 0.9,
                        "anchor_overlap": ["خروج"],
                    }
                ],
                "empirical_meaning_ar": "خروج",
                "empirical_gloss_en": "emergence",
                "structure": "unified",
                "confidence": "high",
                "evidence_as_letter1": [],
                "evidence_as_letter2": [],
            }
        ],
        [{"letter": "ب", "scholar": "asim_al_masri", "atomic_features": ["خروج"]}],
    )
    rendered = render_independent_letter_genome_markdown(rows)
    assert "# الجينوم الحرفي العربي المستقل" in rendered
    assert "### ب" in rendered
    assert "Empirical meaning" in rendered


def test_derive_independent_letter_meanings_runs_on_corpus_map() -> None:
    evidence = {
        "ب": {
            "letter": "ب",
            "as_letter1": [{"nucleus": "بد", "shared_meaning": "ظهور", "features": ["ظهور"], "member_count": 9}],
            "as_letter2": [{"nucleus": "جب", "shared_meaning": "بروز", "features": ["بروز"], "member_count": 9}],
            "count_l1": 1,
            "count_l2": 1,
            "total": 2,
        }
    }
    rows = derive_independent_letter_meanings(
        evidence,
        [{"letter": "ب", "scholar": "asim_al_masri", "atomic_features": ["خروج"]}],
    )
    assert len(rows) == 1
    assert rows[0]["letter"] == "ب"
    assert rows[0]["scholar_comparison"]["asim_al_masri"]["classification"] == "match"
