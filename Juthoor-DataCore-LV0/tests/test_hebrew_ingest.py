"""
Data-quality tests for the Hebrew, Persian, and Aramaic kaikki ingest outputs.

These tests read the real processed JSONL files and assert structural
and statistical properties. They require the data files to have been
generated locally (they are gitignored for size reasons).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_LV0 = Path(__file__).resolve().parents[1]

HEBREW_PATH  = _LV0 / "data/processed/hebrew/sources/kaikki.jsonl"
PERSIAN_PATH = _LV0 / "data/processed/persian/modern/sources/kaikki.jsonl"
ARAMAIC_PATH = _LV0 / "data/processed/aramaic/classical/sources/kaikki.jsonl"

REQUIRED_FIELDS = {"id", "lemma", "language", "stage", "script"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load(path: Path) -> list[dict]:
    """Load all non-blank lines from a JSONL file."""
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def hebrew_rows():
    pytest.importorskip("json")  # always available; keeps fixture lazy
    if not HEBREW_PATH.exists():
        pytest.skip("Hebrew kaikki.jsonl not found — run ingest first")
    return _load(HEBREW_PATH)


@pytest.fixture(scope="module")
def persian_rows():
    if not PERSIAN_PATH.exists():
        pytest.skip("Persian kaikki.jsonl not found — run ingest first")
    return _load(PERSIAN_PATH)


@pytest.fixture(scope="module")
def aramaic_rows():
    if not ARAMAIC_PATH.exists():
        pytest.skip("Aramaic kaikki.jsonl not found — run ingest first")
    return _load(ARAMAIC_PATH)


# ===========================================================================
# Hebrew tests
# ===========================================================================

class TestHebrewIngest:
    def test_file_exists_and_nonempty(self):
        if not HEBREW_PATH.exists():
            pytest.skip("Hebrew kaikki.jsonl not found — run ingest first")
        assert HEBREW_PATH.stat().st_size > 0, "File is empty"

    def test_row_count(self, hebrew_rows):
        assert abs(len(hebrew_rows) - 17034) <= 100, (
            f"Expected ~17034 rows, got {len(hebrew_rows)}"
        )

    def test_required_fields_present(self, hebrew_rows):
        for i, row in enumerate(hebrew_rows):
            missing = REQUIRED_FIELDS - row.keys()
            assert not missing, f"Row {i} missing fields: {missing}"

    def test_language_is_heb(self, hebrew_rows):
        bad = [r["id"] for r in hebrew_rows if r.get("language") != "heb"]
        assert not bad, f"{len(bad)} rows with wrong language (first: {bad[0]})"

    def test_script_is_Hebr(self, hebrew_rows):
        bad = [r["id"] for r in hebrew_rows if r.get("script") != "Hebr"]
        assert not bad, f"{len(bad)} rows with wrong script (first: {bad[0]})"

    def test_lemma_coverage_90pct(self, hebrew_rows):
        total = len(hebrew_rows)
        filled = sum(1 for r in hebrew_rows if r.get("lemma", "").strip())
        pct = filled / total
        assert pct >= 0.90, f"Lemma coverage {pct:.1%} < 90%"

    def test_meaning_or_gloss_coverage_50pct(self, hebrew_rows):
        total = len(hebrew_rows)
        filled = sum(
            1 for r in hebrew_rows
            if r.get("meaning_text", "").strip() or r.get("gloss_plain", "").strip()
        )
        pct = filled / total
        assert pct >= 0.50, f"meaning/gloss coverage {pct:.1%} < 50%"

    def test_spot_check_ktb_or_shalom(self, hebrew_rows):
        """At least one row contains a well-known Hebrew lemma (write or peace)."""
        ktb   = "\u05db\u05ea\u05d1"   # כתב
        shalom = "\u05e9\u05dc\u05d5\u05dd"  # שלום
        hits = [
            r for r in hebrew_rows
            if ktb in r.get("lemma", "") or shalom in r.get("lemma", "")
        ]
        assert hits, "No row found containing 'כתב' or 'שלום' in lemma"


# ===========================================================================
# Persian tests
# ===========================================================================

class TestPersianIngest:
    def test_file_exists_and_nonempty(self):
        if not PERSIAN_PATH.exists():
            pytest.skip("Persian kaikki.jsonl not found — run ingest first")
        assert PERSIAN_PATH.stat().st_size > 0, "File is empty"

    def test_row_count(self, persian_rows):
        assert abs(len(persian_rows) - 19361) <= 100, (
            f"Expected ~19361 rows, got {len(persian_rows)}"
        )

    def test_required_fields_present(self, persian_rows):
        for i, row in enumerate(persian_rows):
            missing = REQUIRED_FIELDS - row.keys()
            assert not missing, f"Row {i} missing fields: {missing}"

    def test_language_is_fas(self, persian_rows):
        bad = [r["id"] for r in persian_rows if r.get("language") != "fas"]
        assert not bad, f"{len(bad)} rows with wrong language (first: {bad[0]})"

    def test_script_is_Arab(self, persian_rows):
        bad = [r["id"] for r in persian_rows if r.get("script") != "Arab"]
        assert not bad, f"{len(bad)} rows with wrong script (first: {bad[0]})"

    def test_lemma_coverage_90pct(self, persian_rows):
        total = len(persian_rows)
        filled = sum(1 for r in persian_rows if r.get("lemma", "").strip())
        pct = filled / total
        assert pct >= 0.90, f"Lemma coverage {pct:.1%} < 90%"

    def test_meaning_or_gloss_coverage_50pct(self, persian_rows):
        total = len(persian_rows)
        filled = sum(
            1 for r in persian_rows
            if r.get("meaning_text", "").strip() or r.get("gloss_plain", "").strip()
        )
        pct = filled / total
        assert pct >= 0.50, f"meaning/gloss coverage {pct:.1%} < 50%"


# ===========================================================================
# Aramaic tests
# ===========================================================================

class TestAramaicIngest:
    def test_file_exists_and_nonempty(self):
        if not ARAMAIC_PATH.exists():
            pytest.skip("Aramaic kaikki.jsonl not found — run ingest first")
        assert ARAMAIC_PATH.stat().st_size > 0, "File is empty"

    def test_row_count(self, aramaic_rows):
        assert abs(len(aramaic_rows) - 2176) <= 100, (
            f"Expected ~2176 rows, got {len(aramaic_rows)}"
        )

    def test_required_fields_present(self, aramaic_rows):
        for i, row in enumerate(aramaic_rows):
            missing = REQUIRED_FIELDS - row.keys()
            assert not missing, f"Row {i} missing fields: {missing}"

    def test_language_is_arc(self, aramaic_rows):
        bad = [r["id"] for r in aramaic_rows if r.get("language") != "arc"]
        assert not bad, f"{len(bad)} rows with wrong language (first: {bad[0]})"

    def test_script_is_Hebr(self, aramaic_rows):
        """Aramaic classical uses Hebrew script (Hebr)."""
        bad = [r["id"] for r in aramaic_rows if r.get("script") != "Hebr"]
        assert not bad, f"{len(bad)} rows with wrong script (first: {bad[0]})"

    def test_lemma_coverage_90pct(self, aramaic_rows):
        total = len(aramaic_rows)
        filled = sum(1 for r in aramaic_rows if r.get("lemma", "").strip())
        pct = filled / total
        assert pct >= 0.90, f"Lemma coverage {pct:.1%} < 90%"

    def test_meaning_or_gloss_coverage_50pct(self, aramaic_rows):
        total = len(aramaic_rows)
        filled = sum(
            1 for r in aramaic_rows
            if r.get("meaning_text", "").strip() or r.get("gloss_plain", "").strip()
        )
        pct = filled / total
        assert pct >= 0.50, f"meaning/gloss coverage {pct:.1%} < 50%"
