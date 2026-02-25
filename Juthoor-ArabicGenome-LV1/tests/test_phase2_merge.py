"""
Tests for build_genome_phase2.py — merge / overlay logic.

Imports pure functions directly: normalize_root, process_bab_file.
The file-level globals (MUAJAM_ROOTS, etc.) use module-level Path construction
but are never called during import, so the import is safe even without real data.
"""
import json
import pytest
from pathlib import Path

# conftest.py adds scripts/ to sys.path
from build_genome_phase2 import normalize_root, process_bab_file


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


# ---------------------------------------------------------------------------
# normalize_root — diacritic stripping and whitespace removal
# ---------------------------------------------------------------------------

class TestNormalizeRoot:
    def test_strips_leading_trailing_whitespace(self):
        assert normalize_root("  كتب  ") == "كتب"

    def test_strips_arabic_diacritics_fatha(self):
        # fatha U+064E
        assert normalize_root("كَتَبَ") == "كتب"

    def test_strips_arabic_diacritics_shadda(self):
        # shadda U+0651
        assert normalize_root("كَتَّبَ") == "كتب"

    def test_strips_arabic_diacritics_kasra_damma(self):
        # kasra U+0650, damma U+064F
        assert normalize_root("كِتُب") == "كتب"

    def test_empty_string_returns_empty(self):
        assert normalize_root("") == ""

    def test_plain_root_unchanged(self):
        assert normalize_root("بيت") == "بيت"

    def test_strips_tanwin(self):
        # tanwin fathatayn U+064B
        assert normalize_root("كتاباً") == "كتابا"

    def test_mixed_diacritics_and_spaces(self):
        # strip() only removes leading/trailing whitespace; internal spaces preserved
        # diacritics are removed
        assert normalize_root(" بَ بَ ") == "ب ب"


# ---------------------------------------------------------------------------
# process_bab_file — matching and enrichment
# ---------------------------------------------------------------------------

class TestProcessBabFile:
    def _make_muajam(self) -> dict:
        """Minimal muajam dict keyed by normalized tri_root."""
        return {
            "كتب": {
                "tri_root": "كتب",
                "binary_root_meaning": "التثبيت",
                "axial_meaning": "الكتابة والتدوين",
                "added_letter": "ب",
                "quran_example": "كَتَبَ رَبُّكُمْ",
                "letter1": "ك",
                "letter1_meaning": "الشمول",
                "letter2": "ت",
                "letter2_meaning": "التأنيث",
                "bab_meaning": "الكاف باب الشمول",
            }
        }

    def test_matched_entry_has_muajam_match_true(self, tmp_path):
        bab_file = tmp_path / "ك.jsonl"
        write_jsonl(bab_file, [
            {"bab": "ك", "binary_root": "كت", "root": "كتب", "words": ["كاتب"]}
        ])
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        matched, unmatched = process_bab_file(bab_file, self._make_muajam(), {}, out_dir)
        assert matched == 1
        assert unmatched == 0
        result = read_jsonl(out_dir / "ك.jsonl")
        assert result[0]["muajam_match"] is True

    def test_unmatched_entry_has_muajam_match_false(self, tmp_path):
        bab_file = tmp_path / "ك.jsonl"
        write_jsonl(bab_file, [
            {"bab": "ك", "binary_root": "كر", "root": "كرم", "words": ["كريم"]}
        ])
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        matched, unmatched = process_bab_file(bab_file, self._make_muajam(), {}, out_dir)
        assert matched == 0
        assert unmatched == 1
        result = read_jsonl(out_dir / "ك.jsonl")
        assert result[0]["muajam_match"] is False

    def test_matched_entry_carries_axial_meaning(self, tmp_path):
        bab_file = tmp_path / "ك.jsonl"
        write_jsonl(bab_file, [
            {"bab": "ك", "binary_root": "كت", "root": "كتب", "words": ["كاتب"]}
        ])
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        process_bab_file(bab_file, self._make_muajam(), {}, out_dir)
        entry = read_jsonl(out_dir / "ك.jsonl")[0]
        assert entry["axial_meaning"] == "الكتابة والتدوين"

    def test_matched_entry_carries_all_muajam_fields(self, tmp_path):
        bab_file = tmp_path / "ك.jsonl"
        write_jsonl(bab_file, [
            {"bab": "ك", "binary_root": "كت", "root": "كتب", "words": ["كاتب"]}
        ])
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        process_bab_file(bab_file, self._make_muajam(), {}, out_dir)
        entry = read_jsonl(out_dir / "ك.jsonl")[0]
        expected_fields = {
            "binary_root_meaning", "axial_meaning", "added_letter",
            "quran_example", "letter1", "letter1_meaning",
            "letter2", "letter2_meaning", "bab_meaning",
        }
        assert expected_fields.issubset(entry.keys())

    def test_unmatched_entry_only_has_core_fields(self, tmp_path):
        bab_file = tmp_path / "ك.jsonl"
        write_jsonl(bab_file, [
            {"bab": "ك", "binary_root": "كر", "root": "كرم", "words": ["كريم"]}
        ])
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        process_bab_file(bab_file, self._make_muajam(), {}, out_dir)
        entry = read_jsonl(out_dir / "ك.jsonl")[0]
        # Must NOT have muajam-enrichment fields
        assert "axial_meaning" not in entry
        assert "binary_root_meaning" not in entry
        # Must have core fields
        assert {"bab", "binary_root", "root", "words", "muajam_match"}.issubset(entry.keys())

    def test_words_preserved_from_phase1(self, tmp_path):
        words = ["كاتب", "كتاب", "مكتبة"]
        bab_file = tmp_path / "ك.jsonl"
        write_jsonl(bab_file, [
            {"bab": "ك", "binary_root": "كت", "root": "كتب", "words": words}
        ])
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        process_bab_file(bab_file, self._make_muajam(), {}, out_dir)
        entry = read_jsonl(out_dir / "ك.jsonl")[0]
        assert set(entry["words"]) == set(words)

    def test_output_sorted_by_binary_root_then_root(self, tmp_path):
        bab_file = tmp_path / "ك.jsonl"
        write_jsonl(bab_file, [
            {"bab": "ك", "binary_root": "كن", "root": "كنز", "words": ["كنوز"]},
            {"bab": "ك", "binary_root": "كت", "root": "كتم", "words": ["كتوم"]},
            {"bab": "ك", "binary_root": "كت", "root": "كتب", "words": ["كاتب"]},
        ])
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        process_bab_file(bab_file, {}, {}, out_dir)
        entries = read_jsonl(out_dir / "ك.jsonl")
        keys = [(e["binary_root"], e["root"]) for e in entries]
        assert keys == sorted(keys)

    def test_match_via_normalized_root_diacritics_stripped(self, tmp_path):
        # Phase 1 root has no diacritics; muajam key is also normalized
        muajam_with_diacritics = {
            # key must be normalized (no diacritics) as produced by normalize_root
            "كتب": {
                "tri_root": "كَتَبَ",
                "binary_root_meaning": "التثبيت",
                "axial_meaning": "الكتابة",
                "added_letter": "",
                "quran_example": "",
                "letter1": "ك",
                "letter1_meaning": "",
                "letter2": "ت",
                "letter2_meaning": "",
                "bab_meaning": "",
            }
        }
        bab_file = tmp_path / "ك.jsonl"
        write_jsonl(bab_file, [
            {"bab": "ك", "binary_root": "كت", "root": "كتب", "words": ["كاتب"]}
        ])
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        matched, _ = process_bab_file(bab_file, muajam_with_diacritics, {}, out_dir)
        assert matched == 1

    def test_empty_bab_file_produces_empty_output(self, tmp_path):
        bab_file = tmp_path / "ك.jsonl"
        bab_file.write_text("", encoding="utf-8")
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        matched, unmatched = process_bab_file(bab_file, {}, {}, out_dir)
        assert matched == 0
        assert unmatched == 0
        assert read_jsonl(out_dir / "ك.jsonl") == []

    def test_returns_correct_matched_unmatched_counts(self, tmp_path):
        bab_file = tmp_path / "ك.jsonl"
        write_jsonl(bab_file, [
            {"bab": "ك", "binary_root": "كت", "root": "كتب", "words": ["كاتب"]},  # match
            {"bab": "ك", "binary_root": "كر", "root": "كرم", "words": ["كريم"]},  # no match
            {"bab": "ك", "binary_root": "كن", "root": "كنز", "words": ["كنز"]},   # no match
        ])
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        matched, unmatched = process_bab_file(bab_file, self._make_muajam(), {}, out_dir)
        assert matched == 1
        assert unmatched == 2


# ---------------------------------------------------------------------------
# normalize_root integration with process_bab_file lookup
# ---------------------------------------------------------------------------

class TestNormalizeRootIntegration:
    def test_phase1_root_with_trailing_space_still_matches(self, tmp_path):
        """normalize_root strips whitespace so a padded Phase1 root still matches."""
        muajam = {
            "درس": {
                "tri_root": "درس",
                "binary_root_meaning": "الإتقان",
                "axial_meaning": "الدراسة",
                "added_letter": "س",
                "quran_example": "",
                "letter1": "د",
                "letter1_meaning": "",
                "letter2": "ر",
                "letter2_meaning": "",
                "bab_meaning": "",
            }
        }
        bab_file = tmp_path / "د.jsonl"
        write_jsonl(bab_file, [
            # root has a trailing space that normalize_root should strip
            {"bab": "د", "binary_root": "در", "root": "درس ", "words": ["مدرسة"]}
        ])
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        matched, unmatched = process_bab_file(bab_file, muajam, {}, out_dir)
        assert matched == 1
        assert unmatched == 0
