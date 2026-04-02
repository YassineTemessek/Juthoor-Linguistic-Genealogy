"""Integration tests for Layer 1 morphology annotation override."""
from __future__ import annotations

import pytest
from juthoor_cognatediscovery_lv2.discovery.target_morphology import decompose_target


class TestLayer1AnnotationOverride:
    """Verify that Layer 1 annotations override rule-based decomposition."""

    # Category A: False prefix fixes
    def test_regis_no_false_re_prefix(self):
        stems = decompose_target("regis", "lat")
        assert "gis" not in stems, "False re- prefix should not produce 'gis'"
        assert "reg" in stems, "Correct stem 'reg' must be present"

    def test_comet_no_false_com_prefix(self):
        stems = decompose_target("comet", "lat")
        assert "et" not in stems, "False com- prefix should not produce 'et'"
        assert "comet" in stems

    def test_person_no_false_per_prefix(self):
        stems = decompose_target("person", "lat")
        assert "son" not in stems, "False per- prefix should not produce 'son'"

    def test_abbey_no_false_ab_prefix(self):
        stems = decompose_target("abbey", "lat")
        assert "bey" not in stems, "False ab- prefix should not produce 'bey'"
        assert "abb" in stems

    def test_corridor_no_false_cor_prefix(self):
        stems = decompose_target("corridor", "lat")
        assert "rid" not in stems, "False cor- prefix should not produce 'rid'"
        assert "curr" in stems

    def test_rein_no_false_re_prefix(self):
        stems = decompose_target("rein", "lat")
        assert "in" not in stems, "False re- prefix should not produce 'in'"
        assert "retin" in stems

    def test_enter_correct_stem(self):
        stems = decompose_target("enter", "lat")
        assert "intr" in stems

    # Category B: Previously no decomposition, now has stems
    def test_pattern_has_stem(self):
        stems = decompose_target("pattern", "lat")
        assert "patron" in stems

    def test_filament_has_stem(self):
        stems = decompose_target("filament", "lat")
        assert "fil" in stems

    def test_animal_has_stem(self):
        stems = decompose_target("animal", "lat")
        assert "anim" in stems

    def test_chain_has_stem(self):
        stems = decompose_target("chain", "lat")
        assert "caten" in stems

    def test_ceremony_has_stem(self):
        stems = decompose_target("ceremony", "lat")
        assert "caerimon" in stems

    def test_forest_has_stem(self):
        stems = decompose_target("forest", "lat")
        assert "for" in stems

    def test_mill_has_stem(self):
        stems = decompose_target("mill", "lat")
        assert "mol" in stems

    def test_cemetery_has_stem(self):
        stems = decompose_target("cemetery", "lat")
        assert "coemet" in stems

    def test_scorpion_has_stem(self):
        stems = decompose_target("scorpion", "lat")
        assert "scorp" in stems

    def test_valley_has_stem(self):
        stems = decompose_target("valley", "lat")
        assert "vall" in stems

    def test_cathedral_has_compound_parts(self):
        stems = decompose_target("cathedral", "lat")
        assert "cathedr" in stems
        assert "hedra" in stems

    def test_leopard_has_compound_parts(self):
        stems = decompose_target("leopard", "lat")
        assert "leo" in stems
        assert "pardus" in stems

    # Category C: Controls — existing correct decompositions preserved
    def test_canine_still_works(self):
        stems = decompose_target("canine", "lat")
        assert "can" in stems

    def test_basilica_still_works(self):
        stems = decompose_target("basilica", "lat")
        assert "basil" in stems

    def test_viva_still_works(self):
        stems = decompose_target("viva", "lat")
        assert "viv" in stems

    def test_submarine_still_works(self):
        stems = decompose_target("submarine", "lat")
        assert "marin" in stems

    # General: original word always first
    def test_original_word_always_first(self):
        for word in ["regis", "comet", "ceremony", "canine"]:
            stems = decompose_target(word, "lat")
            assert stems[0] == word.lower(), f"First stem must be original word for '{word}'"

    # Non-annotated words still use rule-based fallback
    def test_unannotated_word_uses_fallback(self):
        stems = decompose_target("dominus", "lat")
        assert len(stems) > 1, "Rule-based fallback should still work for unannotated words"
