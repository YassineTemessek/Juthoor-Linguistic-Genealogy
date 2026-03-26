from __future__ import annotations

from juthoor_arabicgenome_lv1.factory.third_letter_profiles import (
    build_third_letter_modifier_profiles,
    render_third_letter_modifier_profiles_markdown,
)


def test_build_third_letter_modifier_profiles_aggregates_shared_features() -> None:
    rows = [
        {
            "third_letter": "ر",
            "scholar": "consensus_weighted",
            "model": "phonetic_gestural",
            "filtered_third_letter_features": ["انتقال", "استرسال"],
            "dropped_third_letter_features": [],
            "predicted_features": ["انتقال", "استرسال"],
            "actual_features": ["انتقال"],
            "blended_jaccard": 0.3,
            "quranic_verse": "x",
        },
        {
            "third_letter": "ر",
            "scholar": "consensus_weighted",
            "model": "phonetic_gestural",
            "filtered_third_letter_features": ["انتقال", "استرسال"],
            "dropped_third_letter_features": [],
            "predicted_features": ["انتقال", "استرسال"],
            "actual_features": ["استرسال"],
            "blended_jaccard": 0.2,
            "quranic_verse": None,
        },
        {
            "third_letter": "ر",
            "scholar": "consensus_strict",
            "model": "phonetic_gestural",
            "filtered_third_letter_features": ["انتقال", "استرسال"],
            "dropped_third_letter_features": [],
            "predicted_features": ["انتقال"],
            "actual_features": ["انتقال"],
            "blended_jaccard": 0.4,
            "quranic_verse": "y",
        },
        {
            "third_letter": "ر",
            "scholar": "consensus_strict",
            "model": "nucleus_only",
            "filtered_third_letter_features": ["انتقال", "استرسال"],
            "dropped_third_letter_features": [],
            "predicted_features": ["استرسال"],
            "actual_features": ["استرسال"],
            "blended_jaccard": 0.4,
            "quranic_verse": None,
        },
    ]

    profiles = build_third_letter_modifier_profiles(rows)
    assert len(profiles) == 1
    profile = profiles[0]
    assert profile["letter"] == "ر"
    assert profile["shared_stable_modifier_features"] == ["استرسال", "انتقال"]
    assert profile["shared_blocked_features"] == []
    assert profile["summary_band"] == "supportive"


def test_render_third_letter_modifier_profiles_markdown_contains_key_sections() -> None:
    profiles = [
        {
            "letter": "ر",
            "summary_band": "supportive",
            "shared_stable_modifier_features": ["استرسال", "انتقال"],
            "shared_blocked_features": ["التحام"],
            "mean_blended_jaccard": 0.31,
            "nonzero_rate": 0.75,
            "dropped_feature_row_rate": 0.05,
            "scholar_profiles": {
                "consensus_weighted": {
                    "mean_blended_jaccard": 0.3,
                    "nonzero_rate": 0.7,
                    "quranic_rate": 0.5,
                    "feature_precision": 0.5,
                    "dominant_models": [{"model": "phonetic_gestural", "count": 3}],
                    "top_modifier_features": [{"feature": "انتقال", "count": 4}],
                    "top_blocked_features": [{"feature": "التحام", "count": 2}],
                },
                "consensus_strict": {
                    "mean_blended_jaccard": 0.32,
                    "nonzero_rate": 0.8,
                    "quranic_rate": 0.4,
                    "feature_precision": 0.6,
                    "dominant_models": [{"model": "nucleus_only", "count": 2}],
                    "top_modifier_features": [{"feature": "استرسال", "count": 4}],
                    "top_blocked_features": [{"feature": "التحام", "count": 2}],
                },
            },
        }
    ]

    markdown = render_third_letter_modifier_profiles_markdown(profiles)
    assert "# Third Letter Modifier Profiles" in markdown
    assert "| ر | supportive |" in markdown
    assert "Stable modifier signature: استرسال, انتقال" in markdown
    assert "`consensus_weighted` dominant models: phonetic_gestural (3)" in markdown
