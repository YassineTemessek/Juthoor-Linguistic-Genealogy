"""Tests for scoring_profiles module and cross-pair bonus integration."""
from __future__ import annotations

import warnings
import pytest

from juthoor_cognatediscovery_lv2.discovery.scoring_profiles import (
    PROFILES,
    ScoringProfile,
    get_profile,
)


# ---------------------------------------------------------------------------
# Profile registry
# ---------------------------------------------------------------------------

class TestProfilesRegistry:
    def test_profiles_dict_nonempty(self):
        assert len(PROFILES) >= 4

    def test_required_profiles_exist(self):
        required = {"ara_eng_default", "ara_eng_precision", "ara_eng_recall", "semitic_semitic"}
        missing = required - set(PROFILES)
        assert not missing, f"Missing profiles: {missing}"

    def test_all_profiles_are_scoring_profile_instances(self):
        for name, profile in PROFILES.items():
            assert isinstance(profile, ScoringProfile), f"{name!r} is not a ScoringProfile"

    def test_profile_names_match_dict_keys(self):
        for key, profile in PROFILES.items():
            assert profile.name == key, f"Key {key!r} != profile.name {profile.name!r}"


# ---------------------------------------------------------------------------
# get_profile()
# ---------------------------------------------------------------------------

class TestGetProfile:
    def test_get_known_profile_returns_correct_instance(self):
        profile = get_profile("ara_eng_default")
        assert profile.name == "ara_eng_default"

    def test_get_all_known_profiles(self):
        for name in PROFILES:
            p = get_profile(name)
            assert p.name == name

    def test_get_unknown_profile_warns_and_falls_back(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            profile = get_profile("nonexistent_profile_xyz")
        assert profile.name == "ara_eng_default"
        assert len(w) == 1
        assert "nonexistent_profile_xyz" in str(w[0].message)

    def test_get_profile_returns_frozen_dataclass(self):
        profile = get_profile("ara_eng_default")
        with pytest.raises((AttributeError, TypeError)):
            profile.name = "modified"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ScoringProfile fields and constraints
# ---------------------------------------------------------------------------

class TestScoringProfileFields:
    def test_cross_pair_cap_field_exists(self):
        profile = get_profile("ara_eng_default")
        assert hasattr(profile, "cross_pair_cap")

    def test_cross_pair_cap_is_float(self):
        for name, profile in PROFILES.items():
            assert isinstance(profile.cross_pair_cap, float), f"{name!r}.cross_pair_cap is not float"

    def test_cross_pair_cap_at_most_010(self):
        """All profiles must cap cross_pair bonus at <= 0.10 per spec."""
        for name, profile in PROFILES.items():
            assert profile.cross_pair_cap <= 0.10, (
                f"{name!r}.cross_pair_cap={profile.cross_pair_cap} exceeds 0.10"
            )

    def test_cross_pair_cap_nonnegative(self):
        for name, profile in PROFILES.items():
            assert profile.cross_pair_cap >= 0.0, f"{name!r}.cross_pair_cap is negative"

    def test_semantic_form_weights_sum_to_one(self):
        for name, profile in PROFILES.items():
            total = profile.semantic_weight + profile.form_weight
            assert abs(total - 1.0) < 1e-9, (
                f"{name!r}: semantic_weight + form_weight = {total} != 1.0"
            )

    def test_thresholds_in_valid_range(self):
        for name, profile in PROFILES.items():
            assert 0.0 <= profile.prefilter_threshold <= 1.0, f"{name!r}.prefilter_threshold out of range"
            assert 0.0 <= profile.final_threshold <= 1.0, f"{name!r}.final_threshold out of range"

    def test_as_dict_contains_cross_pair_cap(self):
        profile = get_profile("ara_eng_default")
        d = profile.as_dict()
        assert "cross_pair_cap" in d
        assert d["cross_pair_cap"] == profile.cross_pair_cap

    def test_as_dict_contains_all_expected_keys(self):
        expected_keys = {
            "name", "semantic_weight", "form_weight", "phonetic_law_cap",
            "genome_cap", "multi_method_cap", "cross_pair_cap",
            "root_quality_cap", "prefilter_threshold", "final_threshold", "description",
        }
        profile = get_profile("ara_eng_default")
        d = profile.as_dict()
        assert expected_keys == set(d.keys())


# ---------------------------------------------------------------------------
# Backwards compatibility: scoring.py still works without cross_pair_scorer
# ---------------------------------------------------------------------------

class TestScoringBackwardsCompat:
    """Verify that apply_hybrid_scoring and DiscoveryScorer accept no cross_pair_scorer."""

    def _make_candidates(self) -> dict:
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import HybridWeights
        return {
            "pair_0": {
                "_source_fields": {"lemma": "kitab", "root": "ktb", "root_norm": "كتب"},
                "_target_fields": {"lemma": "book", "ipa": "bʊk"},
                "scores": {"semantic": 0.5, "form": 0.3},
            }
        }

    def test_apply_hybrid_scoring_no_cross_pair(self):
        from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import HybridWeights
        from juthoor_cognatediscovery_lv2.discovery.scoring import apply_hybrid_scoring

        candidates = self._make_candidates()
        # Should not raise even without cross_pair_scorer
        apply_hybrid_scoring(candidates, HybridWeights())
        entry = candidates["pair_0"]
        assert "hybrid" in entry
        components = entry["hybrid"].get("components", {})
        # cross_pair_bonus should be zeroed out via else-branch
        assert "cross_pair_bonus" in components
        assert components["cross_pair_bonus"] == 0.0

    def test_discovery_scorer_default_no_cross_pair(self):
        from juthoor_cognatediscovery_lv2.discovery.scoring import DiscoveryScorer

        scorer = DiscoveryScorer()
        assert scorer.cross_pair_scorer is None

    def test_discovery_scorer_accepts_cross_pair_none(self):
        from juthoor_cognatediscovery_lv2.discovery.scoring import DiscoveryScorer

        scorer = DiscoveryScorer(cross_pair_scorer=None)
        assert scorer.cross_pair_scorer is None
