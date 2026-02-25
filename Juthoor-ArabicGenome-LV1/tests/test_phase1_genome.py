"""
Tests for build_genome_phase1.py — grouping logic.

Tests the build_genome() function in isolation using in-memory JSONL fixtures
written to tmp_path; no real LV0 data files are required.
"""
import json
import pytest
from pathlib import Path

# conftest.py already adds scripts/ to sys.path
from build_genome_phase1 import build_genome


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    results = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


# ---------------------------------------------------------------------------
# BAB extraction — first char of root_norm
# ---------------------------------------------------------------------------

class TestBabExtraction:
    def test_bab_is_first_char_of_root_norm(self, tmp_path):
        records = [{"root_norm": "كتب", "binary_root": "كت", "lemma": "كاتب"}]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        counts, _ = build_genome(inp, tmp_path / "out")
        assert "ك" in counts

    def test_multiple_bab_files_created(self, tmp_path):
        records = [
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "كاتب"},
            {"root_norm": "بيت", "binary_root": "بي", "lemma": "بائت"},
        ]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        out_dir = tmp_path / "out"
        counts, _ = build_genome(inp, out_dir)
        assert set(counts.keys()) == {"ك", "ب"}
        assert (out_dir / "ك.jsonl").exists()
        assert (out_dir / "ب.jsonl").exists()

    def test_bab_derived_from_root_norm_first_char(self, tmp_path):
        # binary_root provided explicitly — BAB should still come from root_norm[0]
        records = [{"root_norm": "فعل", "binary_root": "فع", "lemma": "فاعل"}]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        out_dir = tmp_path / "out"
        counts, _ = build_genome(inp, out_dir)
        assert "ف" in counts
        entry = read_jsonl(out_dir / "ف.jsonl")[0]
        assert entry["bab"] == "ف"


# ---------------------------------------------------------------------------
# binary_root extraction and fallback derivation
# ---------------------------------------------------------------------------

class TestBinaryRootExtraction:
    def test_binary_root_from_record(self, tmp_path):
        records = [{"root_norm": "بوب", "binary_root": "بب", "lemma": "باب"}]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        out_dir = tmp_path / "out"
        build_genome(inp, out_dir)
        entry = read_jsonl(out_dir / "ب.jsonl")[0]
        assert entry["binary_root"] == "بب"

    def test_binary_root_derived_from_root_norm_when_missing(self, tmp_path):
        # no binary_root field — should derive first 2 chars of root_norm
        records = [{"root_norm": "درس", "lemma": "مدرسة"}]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        out_dir = tmp_path / "out"
        build_genome(inp, out_dir)
        entry = read_jsonl(out_dir / "د.jsonl")[0]
        assert entry["binary_root"] == "در"

    def test_binary_root_empty_string_treated_as_missing(self, tmp_path):
        # binary_root present but empty — should fall back to first 2 chars
        records = [{"root_norm": "حمل", "binary_root": "", "lemma": "حامل"}]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        out_dir = tmp_path / "out"
        build_genome(inp, out_dir)
        entry = read_jsonl(out_dir / "ح.jsonl")[0]
        assert entry["binary_root"] == "حم"


# ---------------------------------------------------------------------------
# Deduplication — unique words (set semantics)
# ---------------------------------------------------------------------------

class TestDeduplication:
    def test_duplicate_lemmas_deduped_within_root(self, tmp_path):
        records = [
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "كاتب"},
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "كاتب"},  # exact dup
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "كتاب"},
        ]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        out_dir = tmp_path / "out"
        build_genome(inp, out_dir)
        entry = read_jsonl(out_dir / "ك.jsonl")[0]
        assert entry["words"].count("كاتب") == 1
        assert len(entry["words"]) == 2

    def test_words_are_sorted(self, tmp_path):
        # Insert in reverse Unicode order; output should be sorted
        records = [
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "ي"},
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "أ"},
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "م"},
        ]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        out_dir = tmp_path / "out"
        build_genome(inp, out_dir)
        entry = read_jsonl(out_dir / "ك.jsonl")[0]
        assert entry["words"] == sorted(entry["words"])


# ---------------------------------------------------------------------------
# Sorting — binary_root then root within each BAB file
# ---------------------------------------------------------------------------

class TestSorting:
    def test_roots_sorted_within_binary_root_group(self, tmp_path):
        records = [
            {"root_norm": "كتم", "binary_root": "كت", "lemma": "كتوم"},
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "كاتب"},
        ]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        out_dir = tmp_path / "out"
        build_genome(inp, out_dir)
        entries = read_jsonl(out_dir / "ك.jsonl")
        roots = [e["root"] for e in entries]
        assert roots == sorted(roots)

    def test_binary_roots_sorted_within_bab_file(self, tmp_path):
        records = [
            {"root_norm": "كنز", "binary_root": "كن", "lemma": "كنوز"},
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "كاتب"},
        ]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        out_dir = tmp_path / "out"
        build_genome(inp, out_dir)
        entries = read_jsonl(out_dir / "ك.jsonl")
        brs = [e["binary_root"] for e in entries]
        assert brs == sorted(brs)


# ---------------------------------------------------------------------------
# Quality filters
# ---------------------------------------------------------------------------

class TestQualityFilters:
    def test_skip_root_shorter_than_3_chars(self, tmp_path):
        records = [
            {"root_norm": "كت", "binary_root": "كت", "lemma": "كات"},   # len 2 — skip
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "كاتب"}, # len 3 — keep
        ]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        out_dir = tmp_path / "out"
        counts, _ = build_genome(inp, out_dir)
        entries = read_jsonl(out_dir / "ك.jsonl")
        assert len(entries) == 1
        assert entries[0]["root"] == "كتب"

    def test_skip_entry_with_no_root_norm(self, tmp_path):
        records = [
            {"root_norm": "", "binary_root": "كت", "lemma": "شيء"},
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "كاتب"},
        ]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        out_dir = tmp_path / "out"
        counts, _ = build_genome(inp, out_dir)
        entries = read_jsonl(out_dir / "ك.jsonl")
        assert len(entries) == 1

    def test_skip_entry_with_no_lemma(self, tmp_path):
        records = [
            {"root_norm": "كتب", "binary_root": "كت", "lemma": ""},
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "كاتب"},
        ]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        out_dir = tmp_path / "out"
        build_genome(inp, out_dir)
        entry = read_jsonl(out_dir / "ك.jsonl")[0]
        assert entry["words"] == ["كاتب"]

    def test_skip_entry_where_only_word_is_root_itself(self, tmp_path):
        # Filter 4: words == [root] -> skip entirely
        records = [
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "كتب"},  # only word = root
            {"root_norm": "درس", "binary_root": "در", "lemma": "مدرسة"},
        ]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        out_dir = tmp_path / "out"
        build_genome(inp, out_dir)
        # "ك" entry should be absent (filtered out)
        k_entries = read_jsonl(out_dir / "ك.jsonl") if (out_dir / "ك.jsonl").exists() else []
        assert not any(e["root"] == "كتب" for e in k_entries)
        # "د" entry should be present
        d_entries = read_jsonl(out_dir / "د.jsonl")
        assert len(d_entries) == 1

    def test_skip_binary_root_shorter_than_2_chars(self, tmp_path):
        # edge: root_norm is exactly 2 chars long would produce binary_root of 2 (filtered earlier),
        # but if someone passes binary_root of 1 char explicitly
        records = [
            {"root_norm": "بوب", "binary_root": "ب", "lemma": "باب"},   # 1-char binary — skip
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "كاتب"},
        ]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        out_dir = tmp_path / "out"
        build_genome(inp, out_dir)
        # بوب skipped, only كتب written
        b_entries = read_jsonl(out_dir / "ب.jsonl") if (out_dir / "ب.jsonl").exists() else []
        assert not any(e["root"] == "بوب" for e in b_entries)

    def test_root_field_used_as_fallback_for_root_norm(self, tmp_path):
        # record has "root" but not "root_norm"
        records = [{"root": "حمل", "binary_root": "حم", "lemma": "حامل"}]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        out_dir = tmp_path / "out"
        build_genome(inp, out_dir)
        entries = read_jsonl(out_dir / "ح.jsonl")
        assert len(entries) == 1
        assert entries[0]["root"] == "حمل"


# ---------------------------------------------------------------------------
# Return values
# ---------------------------------------------------------------------------

class TestReturnValues:
    def test_counts_dict_maps_bab_to_root_count(self, tmp_path):
        records = [
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "كاتب"},
            {"root_norm": "كتم", "binary_root": "كت", "lemma": "كتوم"},
            {"root_norm": "بيت", "binary_root": "بي", "lemma": "بائت"},
        ]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        out_dir = tmp_path / "out"
        counts, total_words = build_genome(inp, out_dir)
        assert counts["ك"] == 2
        assert counts["ب"] == 1
        assert total_words == 3  # one unique word per root

    def test_total_words_counts_unique_words(self, tmp_path):
        records = [
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "كاتب"},
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "كتاب"},
            {"root_norm": "كتب", "binary_root": "كت", "lemma": "كاتب"},  # dup
        ]
        inp = tmp_path / "lexemes.jsonl"
        write_jsonl(inp, records)
        out_dir = tmp_path / "out"
        _, total_words = build_genome(inp, out_dir)
        assert total_words == 2  # deduped

    def test_empty_input_returns_empty_counts(self, tmp_path):
        inp = tmp_path / "lexemes.jsonl"
        inp.write_text("", encoding="utf-8")
        out_dir = tmp_path / "out"
        counts, total_words = build_genome(inp, out_dir)
        assert counts == {}
        assert total_words == 0

    def test_malformed_json_lines_skipped_gracefully(self, tmp_path):
        inp = tmp_path / "lexemes.jsonl"
        with inp.open("w", encoding="utf-8") as f:
            f.write("{not valid json}\n")
            f.write(json.dumps({"root_norm": "كتب", "binary_root": "كت", "lemma": "كاتب"}, ensure_ascii=False) + "\n")
        out_dir = tmp_path / "out"
        counts, _ = build_genome(inp, out_dir)
        assert "ك" in counts
