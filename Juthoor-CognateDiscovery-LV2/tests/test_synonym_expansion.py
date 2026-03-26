"""Tests for synonym_expansion module."""
from __future__ import annotations

from pathlib import Path

import pytest

from juthoor_cognatediscovery_lv2.discovery.synonym_expansion import (
    expand_root,
    load_synonym_families,
)

_REAL_JSONL = (
    Path(__file__).resolve().parents[2]
    / "Juthoor-ArabicGenome-LV1"
    / "data"
    / "theory_canon"
    / "roots"
    / "synonym_families_full.jsonl"
)


# ---------------------------------------------------------------------------
# load_synonym_families
# ---------------------------------------------------------------------------

class TestLoadSynonymFamilies:
    def test_loads_real_file(self):
        """Real JSONL file produces a non-empty lookup."""
        families = load_synonym_families(str(_REAL_JSONL))
        assert len(families) > 0

    def test_all_roots_are_strings(self):
        families = load_synonym_families(str(_REAL_JSONL))
        for root, members in families.items():
            assert isinstance(root, str)
            assert all(isinstance(m, str) for m in members)

    def test_known_heart_family(self):
        """قلب, فؤاد, لب are all in the same synonym family (seed-001)."""
        families = load_synonym_families(str(_REAL_JSONL))
        assert "قلب" in families
        assert "لب" in families
        assert "فؤاد" in families
        # They should all map to the same family list.
        assert set(families["قلب"]) == set(families["لب"]) == set(families["فؤاد"])

    def test_family_contains_all_roots(self):
        """Every member of a family includes all siblings in its list."""
        families = load_synonym_families(str(_REAL_JSONL))
        qalb_family = set(families["قلب"])
        assert "قلب" in qalb_family
        assert "لب" in qalb_family
        assert "فؤاد" in qalb_family

    def test_tmpfile_roundtrip(self, tmp_path):
        """load_synonym_families works on a minimal synthetic JSONL file."""
        import json
        data = [
            {"family_id": "test-001", "roots": ["ألف", "باء", "تاء"], "shared_concept": "test"},
        ]
        p = tmp_path / "families.jsonl"
        p.write_text("\n".join(json.dumps(r) for r in data), encoding="utf-8")
        families = load_synonym_families(str(p))
        assert set(families["ألف"]) == {"ألف", "باء", "تاء"}

    def test_empty_file_returns_empty(self, tmp_path):
        p = tmp_path / "empty.jsonl"
        p.write_text("", encoding="utf-8")
        families = load_synonym_families(str(p))
        assert families == {}


# ---------------------------------------------------------------------------
# expand_root
# ---------------------------------------------------------------------------

class TestExpandRoot:
    def setup_method(self):
        self.families = load_synonym_families(str(_REAL_JSONL))

    def test_known_root_returns_family(self):
        """قلب expands to its full synonym family."""
        result = expand_root("قلب", self.families)
        assert "قلب" in result
        assert "لب" in result
        assert "فؤاد" in result

    def test_synonym_member_expands_same_family(self):
        """لب expands to the same family as قلب."""
        result_qalb = set(expand_root("قلب", self.families))
        result_lub = set(expand_root("لب", self.families))
        assert result_qalb == result_lub

    def test_unknown_root_returns_itself(self):
        """A root not in any family returns a single-element list of itself."""
        result = expand_root("xyz_unknown", self.families)
        assert result == ["xyz_unknown"]

    def test_unknown_root_list_length(self):
        result = expand_root("qqq_not_a_root", self.families)
        assert len(result) == 1

    def test_returns_copy_not_reference(self):
        """Mutating the returned list must not corrupt the lookup."""
        result = expand_root("قلب", self.families)
        original_len = len(result)
        result.append("intruder")
        # Second call should still return the original family.
        result2 = expand_root("قلب", self.families)
        assert len(result2) == original_len
        assert "intruder" not in result2

    def test_expand_with_synthetic_families(self):
        """Smoke-test with a small hand-built lookup."""
        families: dict[str, list[str]] = {
            "أ": ["أ", "ب", "ت"],
            "ب": ["أ", "ب", "ت"],
            "ت": ["أ", "ب", "ت"],
        }
        assert set(expand_root("أ", families)) == {"أ", "ب", "ت"}
        assert expand_root("غ", families) == ["غ"]
