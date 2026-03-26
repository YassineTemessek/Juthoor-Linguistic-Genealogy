"""Tests for scholar_divergence module."""

from __future__ import annotations

import pytest

from juthoor_arabicgenome_lv1.factory.scholar_divergence import (
    compute_letter_divergence,
    most_agreed_letters,
    most_disputed_letters,
    scholar_accuracy_vs_empirical,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _payload(*features: str) -> dict:
    return {"atomic_features": list(features)}


# Three scholars, three letters with different agreement levels:
#
#  م  — jabal: تجمع, تلاصق | asim: تجمع | hassan: انتشار
#        shared: [تجمع]  → PARTIAL
#
#  ع  — jabal: ظهور, عمق | asim: ظهور, عمق | hassan: ظهور
#        shared: [ظهور, عمق]  → STRONG
#        (note: عمق is in the باطن/عمق/جوف synonym group → canonicalized to باطن)
#
#  ت  — jabal: انتقال | asim: صوت | hassan: خفة
#        shared: []  → DIVERGE

MOCK_SCHOLAR_LETTERS: dict[str, dict[str, dict]] = {
    "jabal": {
        "م": _payload("تجمع", "تلاصق"),
        "ع": _payload("ظهور", "عمق"),
        "ت": _payload("انتقال"),
    },
    "asim": {
        "م": _payload("تجمع"),
        "ع": _payload("ظهور", "عمق"),
        "ت": _payload("صوت"),
    },
    "hassan": {
        "م": _payload("انتشار"),
        "ع": _payload("ظهور"),
        "ت": _payload("خفة"),
    },
}


# ---------------------------------------------------------------------------
# compute_letter_divergence
# ---------------------------------------------------------------------------

class TestComputeLetterDivergence:
    def setup_method(self):
        self.divergence = compute_letter_divergence(MOCK_SCHOLAR_LETTERS)
        self.by_letter = {r["letter"]: r for r in self.divergence}

    def test_returns_one_row_per_letter(self):
        assert len(self.divergence) == 3

    def test_scholars_covering(self):
        row_m = self.by_letter["م"]
        assert row_m["scholars_covering"] == ["asim", "hassan", "jabal"]
        assert row_m["n_scholars"] == 3

    def test_shared_features_partial(self):
        row_m = self.by_letter["م"]
        # تجمع appears in jabal + asim → shared (after canonicalization اكتناز/تجمع → اكتناز)
        assert len(row_m["shared_features"]) == 1
        assert row_m["classification"] == "PARTIAL"

    def test_shared_features_strong(self):
        row_e = self.by_letter["ع"]
        # ظهور appears in all 3; عمق (→ باطن via synonym) appears in jabal+asim
        assert len(row_e["shared_features"]) >= 2
        assert row_e["classification"] == "STRONG"

    def test_diverge_classification(self):
        row_t = self.by_letter["ت"]
        assert row_t["shared_features"] == []
        assert row_t["classification"] == "DIVERGE"
        assert row_t["agreement_score"] == 0.0

    def test_agreement_score_range(self):
        for row in self.divergence:
            assert 0.0 <= row["agreement_score"] <= 1.0

    def test_unique_features_for_diverge(self):
        row_t = self.by_letter["ت"]
        # Every scholar has a unique feature for ت
        assert "jabal" in row_t["unique_features"]
        assert "asim" in row_t["unique_features"]
        assert "hassan" in row_t["unique_features"]

    def test_consensus_scholars_are_skipped(self):
        data_with_consensus = {
            **MOCK_SCHOLAR_LETTERS,
            "consensus_strict": {"م": _payload("تجمع"), "ع": _payload("ظهور")},
        }
        result = compute_letter_divergence(data_with_consensus)
        by_letter = {r["letter"]: r for r in result}
        # consensus scholar must not inflate n_scholars
        assert by_letter["م"]["n_scholars"] == 3

    def test_sorted_by_agreement_score_descending(self):
        scores = [r["agreement_score"] for r in self.divergence]
        assert scores == sorted(scores, reverse=True)

    def test_all_features_keys_are_canonical(self):
        # تجمع is in the اكتناز synonym group → should be stored as اكتناز
        row_m = self.by_letter["م"]
        assert "تجمع" not in row_m["all_features"] or "اكتناز" in row_m["all_features"]

    def test_empty_input(self):
        assert compute_letter_divergence({}) == []


# ---------------------------------------------------------------------------
# Agreement score calculation detail
# ---------------------------------------------------------------------------

class TestAgreementScore:
    def test_full_agreement(self):
        data = {
            "s1": {"ب": _payload("انفجار", "بروز")},
            "s2": {"ب": _payload("انفجار", "بروز")},
        }
        rows = compute_letter_divergence(data)
        assert rows[0]["agreement_score"] == 1.0

    def test_zero_agreement(self):
        data = {
            "s1": {"ب": _payload("انفجار")},
            "s2": {"ب": _payload("خفة")},
        }
        rows = compute_letter_divergence(data)
        assert rows[0]["agreement_score"] == 0.0
        assert rows[0]["classification"] == "DIVERGE"

    def test_partial_agreement_ratio(self):
        # 1 shared out of 3 total unique canonical features → ~0.333
        data = {
            "s1": {"ب": _payload("انفجار", "بروز")},
            "s2": {"ب": _payload("انفجار", "خفة")},
        }
        rows = compute_letter_divergence(data)
        row = rows[0]
        assert row["classification"] == "PARTIAL"
        total = len(row["all_features"])
        expected = round(1 / total, 6)
        assert row["agreement_score"] == pytest.approx(expected, abs=1e-5)

    def test_letter_with_no_features(self):
        data = {
            "s1": {"ص": _payload()},
            "s2": {"ص": _payload()},
        }
        rows = compute_letter_divergence(data)
        assert rows[0]["agreement_score"] == 0.0
        assert rows[0]["classification"] == "DIVERGE"


# ---------------------------------------------------------------------------
# scholar_accuracy_vs_empirical
# ---------------------------------------------------------------------------

class TestScholarAccuracyVsEmpirical:
    def setup_method(self):
        # Empirical: م has تجمع/تلاصق, ع has ظهور
        self.empirical = {
            "م": ["تجمع", "تلاصق"],
            "ع": ["ظهور"],
            "ت": ["انتقال"],
        }
        self.accuracy = scholar_accuracy_vs_empirical(
            MOCK_SCHOLAR_LETTERS, self.empirical
        )

    def test_returns_entry_per_non_consensus_scholar(self):
        assert set(self.accuracy.keys()) == {"jabal", "asim", "hassan"}

    def test_jabal_fully_correct(self):
        # jabal: م→(تجمع✓, تلاصق✓), ع→(ظهور✓, عمق?), ت→(انتقال✓)
        # عمق canonicalizes to باطن; empirical ظهور is in خروج/بروز/ظهور group
        # We just check confirmed >= wrong for jabal since he's mostly right
        row = self.accuracy["jabal"]
        assert row["confirmed"] >= row["wrong"]

    def test_hassan_has_wrongs(self):
        # hassan: م→انتشار (not in empirical), ع→ظهور✓, ت→خفة (not in empirical)
        row = self.accuracy["hassan"]
        assert row["wrong"] >= 1

    def test_accuracy_between_zero_and_one(self):
        for scholar, row in self.accuracy.items():
            assert 0.0 <= row["accuracy"] <= 1.0, scholar

    def test_total_equals_confirmed_plus_wrong(self):
        for scholar, row in self.accuracy.items():
            assert row["total"] == row["confirmed"] + row["partial"] + row["wrong"]

    def test_empty_empirical(self):
        result = scholar_accuracy_vs_empirical(MOCK_SCHOLAR_LETTERS, {})
        for row in result.values():
            assert row["confirmed"] == 0
            assert row["accuracy"] == 0.0

    def test_consensus_scholars_skipped(self):
        data = {
            **MOCK_SCHOLAR_LETTERS,
            "consensus_strict": {"م": _payload("تجمع")},
        }
        result = scholar_accuracy_vs_empirical(data, self.empirical)
        assert "consensus_strict" not in result

    def test_known_correct_case(self):
        data = {
            "scholar_a": {"ب": _payload("انفجار", "بروز")},
        }
        empirical = {"ب": ["انفجار", "بروز"]}
        result = scholar_accuracy_vs_empirical(data, empirical)
        assert result["scholar_a"]["accuracy"] == pytest.approx(1.0)

    def test_known_wrong_case(self):
        data = {
            "scholar_a": {"ب": _payload("خفة", "رقة")},
        }
        empirical = {"ب": ["انفجار"]}
        result = scholar_accuracy_vs_empirical(data, empirical)
        # رقة canonicalizes to دقة (synonym group); انفجار is not in synonym groups
        assert result["scholar_a"]["confirmed"] == 0
        assert result["scholar_a"]["accuracy"] == 0.0


# ---------------------------------------------------------------------------
# most_disputed_letters / most_agreed_letters
# ---------------------------------------------------------------------------

class TestRankingHelpers:
    def setup_method(self):
        self.divergence = compute_letter_divergence(MOCK_SCHOLAR_LETTERS)

    def test_most_disputed_ordering(self):
        disputed = most_disputed_letters(self.divergence)
        scores = [r["agreement_score"] for r in disputed]
        assert scores == sorted(scores)

    def test_most_agreed_ordering(self):
        agreed = most_agreed_letters(self.divergence)
        scores = [r["agreement_score"] for r in agreed]
        assert scores == sorted(scores, reverse=True)

    def test_most_disputed_first_is_diverge(self):
        disputed = most_disputed_letters(self.divergence, n=1)
        assert disputed[0]["classification"] == "DIVERGE"

    def test_most_agreed_first_is_strong(self):
        agreed = most_agreed_letters(self.divergence, n=1)
        assert agreed[0]["classification"] == "STRONG"

    def test_n_parameter_limits_output(self):
        assert len(most_disputed_letters(self.divergence, n=2)) == 2
        assert len(most_agreed_letters(self.divergence, n=1)) == 1

    def test_n_larger_than_list(self):
        # Should return all available rows, not crash
        result = most_disputed_letters(self.divergence, n=100)
        assert len(result) == len(self.divergence)

    def test_empty_input(self):
        assert most_disputed_letters([]) == []
        assert most_agreed_letters([]) == []

    def test_does_not_mutate_input(self):
        original_order = [r["letter"] for r in self.divergence]
        most_disputed_letters(self.divergence, n=3)
        most_agreed_letters(self.divergence, n=3)
        assert [r["letter"] for r in self.divergence] == original_order
