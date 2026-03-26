"""Tests for synonym_families module."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from juthoor_arabicgenome_lv1.factory.synonym_families import (
    SEED_FAMILIES,
    SynonymFamily,
    extract_families_from_predictions,
    load_families,
    merge_with_seeds,
    save_families,
    save_seed_families,
    _family_to_dict,
)


# ---------------------------------------------------------------------------
# Seed family tests
# ---------------------------------------------------------------------------

class TestSeedFamilies:
    def test_ten_seed_families_defined(self):
        assert len(SEED_FAMILIES) == 10

    def test_all_seeds_are_frozen_dataclasses(self):
        for fam in SEED_FAMILIES:
            assert isinstance(fam, SynonymFamily)

    def test_seed_ids_unique(self):
        ids = [f.family_id for f in SEED_FAMILIES]
        assert len(ids) == len(set(ids))

    def test_seed_confidence_is_one(self):
        for fam in SEED_FAMILIES:
            assert fam.confidence == 1.0

    def test_seed_source_is_seed(self):
        for fam in SEED_FAMILIES:
            assert fam.source == "seed"

    def test_heart_family_roots(self):
        heart = next(f for f in SEED_FAMILIES if "heart" in f.shared_concept)
        assert "قلب" in heart.roots
        assert "لب" in heart.roots

    def test_fear_family_roots(self):
        fear = next(f for f in SEED_FAMILIES if "fear" in f.shared_concept)
        assert "خوف" in fear.roots
        assert "رهبة" in fear.roots

    def test_gather_family_has_four_roots(self):
        gather = next(f for f in SEED_FAMILIES if "gather" in f.shared_concept)
        assert len(gather.roots) == 4

    def test_family_to_dict_keys(self):
        d = _family_to_dict(SEED_FAMILIES[0])
        assert set(d.keys()) == {"family_id", "roots", "shared_concept", "confidence", "source"}
        assert isinstance(d["roots"], list)


# ---------------------------------------------------------------------------
# Extraction tests
# ---------------------------------------------------------------------------

class TestExtractFamilies:
    def _make_prediction(self, root: str, features: list[str]) -> dict:
        return {"root": root, "predicted_features": features}

    def test_empty_input_returns_empty(self):
        result = extract_families_from_predictions([])
        assert result == []

    def test_singletons_not_returned(self):
        preds = [self._make_prediction("قلب", ["باطن", "قوة"])]
        result = extract_families_from_predictions(preds)
        assert result == []

    def test_identical_features_grouped(self):
        features = ["باطن", "قوة", "ضغط"]
        preds = [
            self._make_prediction("أ", features),
            self._make_prediction("ب", features),
        ]
        result = extract_families_from_predictions(preds, threshold=0.7)
        assert len(result) == 1
        fam = result[0]
        assert set(fam["roots"]) == {"أ", "ب"}

    def test_dissimilar_features_not_grouped(self):
        preds = [
            self._make_prediction("أ", ["باطن", "قوة"]),
            self._make_prediction("ب", ["فراغ", "تخلخل", "رقة"]),
        ]
        result = extract_families_from_predictions(preds, threshold=0.7)
        assert result == []

    def test_family_has_required_keys(self):
        features = ["باطن", "عمق"]
        preds = [
            self._make_prediction("أ", features),
            self._make_prediction("ب", features),
        ]
        result = extract_families_from_predictions(preds)
        fam = result[0]
        assert "family_id" in fam
        assert "roots" in fam
        assert "shared_concept" in fam
        assert "confidence" in fam
        assert fam["source"] == "extracted"

    def test_family_id_prefixed_ext(self):
        features = ["باطن"]
        preds = [
            self._make_prediction("أ", features),
            self._make_prediction("ب", features),
        ]
        result = extract_families_from_predictions(preds)
        assert result[0]["family_id"].startswith("ext-")

    def test_confidence_in_range(self):
        features = ["باطن", "قوة"]
        preds = [
            self._make_prediction("أ", features),
            self._make_prediction("ب", features),
            self._make_prediction("ج", features),
        ]
        result = extract_families_from_predictions(preds)
        assert 0.0 <= result[0]["confidence"] <= 1.0

    def test_rows_without_features_skipped(self):
        preds = [
            {"root": "أ"},  # missing predicted_features
            {"root": "ب", "predicted_features": []},
            {"root": "ج", "predicted_features": ["باطن"]},
        ]
        result = extract_families_from_predictions(preds)
        # Only one usable row => no family formed
        assert result == []


# ---------------------------------------------------------------------------
# Merge tests
# ---------------------------------------------------------------------------

class TestMergeWithSeeds:
    def test_merge_returns_seeds_first(self):
        merged = merge_with_seeds([])
        # All 10 seeds present
        assert len(merged) >= 10
        assert merged[0]["source"] == "seed"

    def test_extracted_family_added_when_no_overlap(self):
        ext = [{"family_id": "ext-abc", "roots": ["xyz", "abc"],
                "shared_concept": "test", "confidence": 0.8, "source": "extracted"}]
        merged = merge_with_seeds(ext)
        ids = [f["family_id"] for f in merged]
        assert "ext-abc" in ids

    def test_extracted_family_dropped_when_root_in_seed(self):
        # قلب is in seed-001
        ext = [{"family_id": "ext-dup", "roots": ["قلب", "xyz"],
                "shared_concept": "duplicate", "confidence": 0.9, "source": "extracted"}]
        merged = merge_with_seeds(ext)
        ids = [f["family_id"] for f in merged]
        assert "ext-dup" not in ids

    def test_custom_seeds_accepted(self):
        custom_seeds = [{"family_id": "cs-001", "roots": ["ر", "ز"],
                         "shared_concept": "custom", "confidence": 1.0, "source": "seed"}]
        ext = [{"family_id": "ext-new", "roots": ["س", "ش"],
                "shared_concept": "new", "confidence": 0.75, "source": "extracted"}]
        merged = merge_with_seeds(ext, seeds=custom_seeds)
        assert len(merged) == 2

    def test_total_count_seeds_plus_non_overlapping(self):
        ext = [
            {"family_id": "ext-a", "roots": ["new1", "new2"],
             "shared_concept": "new-a", "confidence": 0.8, "source": "extracted"},
            {"family_id": "ext-b", "roots": ["قلب", "new3"],  # overlaps seed
             "shared_concept": "new-b", "confidence": 0.8, "source": "extracted"},
        ]
        merged = merge_with_seeds(ext)
        # 10 seeds + 1 non-overlapping
        assert len(merged) == 11


# ---------------------------------------------------------------------------
# Serialisation tests
# ---------------------------------------------------------------------------

class TestSerialisation:
    def _sample_families(self) -> list[dict]:
        return [
            {"family_id": "t-001", "roots": ["قلب", "لب"],
             "shared_concept": "heart", "confidence": 1.0, "source": "seed"},
            {"family_id": "t-002", "roots": ["ستر", "كتم"],
             "shared_concept": "hide", "confidence": 0.9, "source": "extracted"},
        ]

    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "families.jsonl")
            families = self._sample_families()
            save_families(families, path)
            loaded = load_families(path)
            assert len(loaded) == 2
            assert loaded[0]["family_id"] == "t-001"
            assert loaded[1]["roots"] == ["ستر", "كتم"]

    def test_save_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "deep" / "nested" / "families.jsonl")
            save_families(self._sample_families(), path)
            assert Path(path).exists()

    def test_jsonl_format_one_object_per_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "families.jsonl")
            save_families(self._sample_families(), path)
            lines = Path(path).read_text(encoding="utf-8").strip().splitlines()
            assert len(lines) == 2
            for line in lines:
                obj = json.loads(line)
                assert isinstance(obj, dict)

    def test_arabic_characters_preserved(self):
        fam = [{"family_id": "t-001", "roots": ["قلب", "فؤاد"],
                "shared_concept": "قلب", "confidence": 1.0, "source": "seed"}]
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "f.jsonl")
            save_families(fam, path)
            loaded = load_families(path)
            assert "قلب" in loaded[0]["roots"]
            assert loaded[0]["shared_concept"] == "قلب"

    def test_save_seed_families_writes_ten_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "seeds.jsonl")
            save_seed_families(path)
            lines = Path(path).read_text(encoding="utf-8").strip().splitlines()
            assert len(lines) == 10

    def test_load_empty_file_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "empty.jsonl")
            Path(path).write_text("", encoding="utf-8")
            assert load_families(path) == []
