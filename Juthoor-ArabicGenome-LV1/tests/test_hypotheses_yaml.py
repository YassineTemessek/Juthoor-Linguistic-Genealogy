"""Tests for the hypotheses.yaml registry file."""
import pathlib

import yaml
import pytest

YAML_PATH = (
    pathlib.Path(__file__).parent.parent / "resources" / "hypotheses.yaml"
)

REQUIRED_FIELDS = {"id", "name", "claim", "source", "experiments", "status"}
EXPECTED_IDS = {f"H{i}" for i in range(1, 13)}


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


def test_all_statuses_are_pending(hypotheses):
    for entry in hypotheses:
        assert entry["status"] == "pending", (
            f"Entry {entry['id']} has status '{entry['status']}', expected 'pending'"
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
