"""Tests for the promotions export module."""
import json
from pathlib import Path

import pytest

from juthoor_arabicgenome_lv1.factory.promotions import export_promoted_results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Directory structure
# ---------------------------------------------------------------------------

def test_export_creates_promoted_features_dir(tmp_path):
    manifest = export_promoted_results(tmp_path)
    assert (tmp_path / "promoted_features").is_dir()


def test_export_creates_evidence_cards_dir(tmp_path):
    export_promoted_results(tmp_path)
    assert (tmp_path / "evidence_cards").is_dir()


def test_export_creates_manifest_json(tmp_path):
    export_promoted_results(tmp_path)
    assert (tmp_path / "promotion_manifest.json").is_file()


def test_promoted_feature_files_exist(tmp_path):
    export_promoted_results(tmp_path)
    features_dir = tmp_path / "promoted_features"
    assert (features_dir / "field_coherence_scores.jsonl").is_file()
    assert (features_dir / "positional_profiles.jsonl").is_file()
    assert (features_dir / "metathesis_pairs.jsonl").is_file()
    assert (features_dir / "cross_lingual_support.jsonl").is_file()


def test_evidence_card_files_exist(tmp_path):
    export_promoted_results(tmp_path)
    cards_dir = tmp_path / "evidence_cards"
    assert (cards_dir / "H2_field_coherence.json").is_file()
    assert (cards_dir / "H5_order_matters.json").is_file()
    assert (cards_dir / "H8_positional_semantics.json").is_file()


# ---------------------------------------------------------------------------
# Evidence card content
# ---------------------------------------------------------------------------

_REQUIRED_CARD_FIELDS = {
    "hypothesis_id",
    "hypothesis_name",
    "claim",
    "source",
    "experiment_id",
    "experiment_name",
    "status",
    "key_metric",
    "families_tested",
    "promotion_date",
    "data_file",
}


def _load_card(tmp_path: Path, filename: str) -> dict:
    return json.loads((tmp_path / "evidence_cards" / filename).read_text(encoding="utf-8"))


@pytest.mark.parametrize("filename,expected_id", [
    ("H2_field_coherence.json", "H2"),
    ("H5_order_matters.json", "H5"),
    ("H8_positional_semantics.json", "H8"),
])
def test_evidence_card_required_fields(tmp_path, filename, expected_id):
    export_promoted_results(tmp_path)
    card = _load_card(tmp_path, filename)
    missing = _REQUIRED_CARD_FIELDS - card.keys()
    assert not missing, f"Card {filename} missing fields: {missing}"
    assert card["hypothesis_id"] == expected_id


@pytest.mark.parametrize("filename", [
    "H2_field_coherence.json",
    "H5_order_matters.json",
    "H8_positional_semantics.json",
])
def test_evidence_card_status_supported(tmp_path, filename):
    export_promoted_results(tmp_path)
    card = _load_card(tmp_path, filename)
    assert card["status"] == "supported"


def test_h2_card_references_field_coherence_file(tmp_path):
    export_promoted_results(tmp_path)
    card = _load_card(tmp_path, "H2_field_coherence.json")
    assert "field_coherence" in card["data_file"]


def test_h5_card_references_metathesis_file(tmp_path):
    export_promoted_results(tmp_path)
    card = _load_card(tmp_path, "H5_order_matters.json")
    assert "metathesis" in card["data_file"]


def test_h8_card_references_positional_file(tmp_path):
    export_promoted_results(tmp_path)
    card = _load_card(tmp_path, "H8_positional_semantics.json")
    assert "positional" in card["data_file"]


# ---------------------------------------------------------------------------
# Promotion manifest
# ---------------------------------------------------------------------------

def test_manifest_lists_all_three_hypotheses(tmp_path):
    manifest = export_promoted_results(tmp_path)
    assert set(manifest["promoted_hypotheses"]) == {"H2", "H5", "H8", "H12"}


def test_manifest_lists_three_evidence_cards(tmp_path):
    manifest = export_promoted_results(tmp_path)
    assert len(manifest["evidence_cards"]) == 4


def test_manifest_lists_three_promoted_features(tmp_path):
    manifest = export_promoted_results(tmp_path)
    assert len(manifest["promoted_features"]) == 5


def test_manifest_lists_source_experiments(tmp_path):
    manifest = export_promoted_results(tmp_path)
    assert set(manifest["source_experiments"]) == {"2.3", "4.1", "1.2", "5.3", "5.4", "6.4"}


def test_manifest_has_promotion_date(tmp_path):
    manifest = export_promoted_results(tmp_path)
    assert "promotion_date" in manifest
    assert manifest["promotion_date"]  # non-empty


def test_manifest_on_disk_matches_return_value(tmp_path):
    manifest = export_promoted_results(tmp_path)
    on_disk = json.loads((tmp_path / "promotion_manifest.json").read_text(encoding="utf-8"))
    assert on_disk["promoted_hypotheses"] == manifest["promoted_hypotheses"]
    assert on_disk["source_experiments"] == manifest["source_experiments"]


# ---------------------------------------------------------------------------
# Metathesis filtering
# ---------------------------------------------------------------------------

def test_metathesis_pairs_contain_only_metathesis(tmp_path):
    export_promoted_results(tmp_path)
    rows = _lines(tmp_path / "promoted_features" / "metathesis_pairs.jsonl")
    assert rows, "metathesis_pairs.jsonl is empty"
    for row in rows:
        assert row["pair_type"] == "metathesis", f"Unexpected pair_type: {row['pair_type']}"


def test_metathesis_pairs_excludes_control_rows(tmp_path):
    export_promoted_results(tmp_path)
    rows = _lines(tmp_path / "promoted_features" / "metathesis_pairs.jsonl")
    control_rows = [r for r in rows if r.get("pair_type") == "control"]
    assert control_rows == [], f"Found {len(control_rows)} control rows that should have been filtered"


def test_metathesis_pairs_nonempty(tmp_path):
    export_promoted_results(tmp_path)
    rows = _lines(tmp_path / "promoted_features" / "metathesis_pairs.jsonl")
    assert len(rows) > 0


# ---------------------------------------------------------------------------
# Field coherence (copy-as-is sanity check)
# ---------------------------------------------------------------------------

def test_field_coherence_scores_nonempty(tmp_path):
    export_promoted_results(tmp_path)
    rows = _lines(tmp_path / "promoted_features" / "field_coherence_scores.jsonl")
    assert len(rows) > 0


def test_field_coherence_rows_have_binary_root(tmp_path):
    export_promoted_results(tmp_path)
    rows = _lines(tmp_path / "promoted_features" / "field_coherence_scores.jsonl")
    for row in rows[:5]:
        assert "binary_root" in row


# ---------------------------------------------------------------------------
# Positional profiles (copy-as-is sanity check)
# ---------------------------------------------------------------------------

def test_positional_profiles_nonempty(tmp_path):
    export_promoted_results(tmp_path)
    rows = _lines(tmp_path / "promoted_features" / "positional_profiles.jsonl")
    assert len(rows) > 0


def test_positional_profiles_have_positions_key(tmp_path):
    export_promoted_results(tmp_path)
    rows = _lines(tmp_path / "promoted_features" / "positional_profiles.jsonl")
    for row in rows[:5]:
        assert "positions" in row


def test_cross_lingual_support_rows_have_binary_root(tmp_path):
    export_promoted_results(tmp_path)
    rows = _lines(tmp_path / "promoted_features" / "cross_lingual_support.jsonl")
    assert len(rows) > 0
    for row in rows[:5]:
        assert "binary_root" in row
        assert "semitic_support" in row
        assert "support_score" in row
