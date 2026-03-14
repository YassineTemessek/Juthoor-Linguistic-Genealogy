"""Tests for the hypotheses.yaml registry file."""
import pathlib

import yaml
import pytest

YAML_PATH = (
    pathlib.Path(__file__).parent.parent / "resources" / "hypotheses.yaml"
)

REQUIRED_FIELDS = {"id", "name", "claim", "source", "experiments", "status"}
EXPECTED_IDS = {f"H{i}" for i in range(1, 13)}
VALID_STATUSES = {
    "pending",
    "supported",
    "weakly_supported",
    "weak_signal",
    "not_supported",
    "inconclusive",
}

TESTED_IDS = {"H1", "H2", "H3", "H4", "H5", "H6", "H8"}
EVIDENCE_REQUIRED_FIELDS = {"experiment_id", "key_metric", "verdict_date"}


@pytest.fixture(scope="module")
def hypotheses():
    with open(YAML_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["hypotheses"]


def test_yaml_loads(hypotheses):
    assert isinstance(hypotheses, list)


def test_count_is_12(hypotheses):
    assert len(hypotheses) == 12, f"Expected 12 hypotheses, got {len(hypotheses)}"


def test_all_required_fields_present(hypotheses):
    for entry in hypotheses:
        missing = REQUIRED_FIELDS - set(entry.keys())
        assert not missing, f"Entry {entry.get('id')} is missing fields: {missing}"


def test_all_statuses_are_valid(hypotheses):
    for entry in hypotheses:
        assert entry["status"] in VALID_STATUSES, (
            f"Entry {entry['id']} has invalid status '{entry['status']}'. "
            f"Valid statuses: {VALID_STATUSES}"
        )


def test_all_ids_are_h1_through_h12(hypotheses):
    ids = {entry["id"] for entry in hypotheses}
    assert ids == EXPECTED_IDS, (
        f"ID mismatch. Got: {sorted(ids)}, Expected: {sorted(EXPECTED_IDS)}"
    )


def test_experiments_are_lists(hypotheses):
    for entry in hypotheses:
        assert isinstance(entry["experiments"], list), (
            f"Entry {entry['id']} 'experiments' field is not a list"
        )
        assert len(entry["experiments"]) >= 1, (
            f"Entry {entry['id']} has no experiment IDs"
        )


def test_ids_are_unique(hypotheses):
    ids = [entry["id"] for entry in hypotheses]
    assert len(ids) == len(set(ids)), "Duplicate hypothesis IDs found"


def test_tested_hypotheses_have_evidence(hypotheses):
    by_id = {entry["id"]: entry for entry in hypotheses}
    for hid in TESTED_IDS:
        entry = by_id[hid]
        assert "evidence" in entry, (
            f"Entry {hid} has a non-pending status but is missing an 'evidence' field"
        )
        evidence = entry["evidence"]
        missing = EVIDENCE_REQUIRED_FIELDS - set(evidence.keys())
        assert not missing, (
            f"Entry {hid} evidence block is missing fields: {missing}"
        )


def test_pending_hypotheses_have_no_evidence(hypotheses):
    for entry in hypotheses:
        if entry["status"] == "pending":
            assert "evidence" not in entry, (
                f"Entry {entry['id']} is still pending but has an 'evidence' field"
            )


def test_verdict_dates_are_correct(hypotheses):
    for entry in hypotheses:
        if "evidence" in entry:
            assert entry["evidence"]["verdict_date"] == "2026-03-14", (
                f"Entry {entry['id']} has unexpected verdict_date "
                f"'{entry['evidence']['verdict_date']}'"
            )
