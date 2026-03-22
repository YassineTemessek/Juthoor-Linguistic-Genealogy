"""Phase 1 acceptance tests for the LV1 semantic canon."""

import json
from pathlib import Path
import pytest

from juthoor_arabicgenome_lv1.core.canon_loaders import (
    load_letter_atoms,
    load_letter_atom_registry,
    load_binary_nuclei,
    load_trilateral_roots,
    load_theory_claims,
)
from juthoor_arabicgenome_lv1.core.canon_models import (
    LetterAtom, LetterRegistryEntry, BinaryNucleus,
    TriliteralRootEntry, TheoryClaim, VALID_SCHOLARS, FEATURE_CATEGORIES,
)


# --- Sample data fixtures ---

SAMPLE_JABAL_LETTER = {
    "letter": "\u0628",
    "letter_name": "\u0627\u0644\u0628\u0627\u0621",
    "scholar": "jabal",
    "raw_description": "\u062a\u062c\u0645\u0639 \u0631\u062e\u0648 \u0645\u0639 \u062a\u0644\u0627\u0635\u0642 \u0645\u0627",
    "atomic_features": ["\u062a\u062c\u0645\u0639", "\u0631\u062e\u0627\u0648\u0629", "\u062a\u0644\u0627\u0635\u0642"],
    "feature_categories": ["gathering_cohesion", "texture_quality", "gathering_cohesion"],
    "sensory_category": None,
    "kinetic_gloss": None,
    "source_document": "\u0627\u0644\u0645\u0639\u062c\u0645 \u0627\u0644\u0627\u0634\u062a\u0642\u0627\u0642\u064a \u0627\u0644\u0645\u0624\u0635\u0644",
    "confidence": "high",
}

SAMPLE_ABBAS_LETTER = {
    "letter": "\u0628",
    "letter_name": "\u0627\u0644\u0628\u0627\u0621",
    "scholar": "hassan_abbas",
    "raw_description": "\u0627\u062a\u0633\u0627\u0639 \u0648\u0627\u0646\u0628\u062b\u0627\u0642",
    "atomic_features": ["\u0627\u0646\u0628\u062b\u0627\u0642", "\u0627\u062a\u0633\u0627\u0639"],
    "feature_categories": ["extension_movement", "extension_movement"],
    "sensory_category": "\u0628\u0635\u0631\u064a\u0629",
    "kinetic_gloss": None,
    "source_document": "\u062e\u0635\u0627\u0626\u0635 \u0627\u0644\u062d\u0631\u0648\u0641 \u0627\u0644\u0639\u0631\u0628\u064a\u0629 \u0648\u0645\u0639\u0627\u0646\u064a\u0647\u0627",
    "confidence": "high",
}

SAMPLE_NUCLEUS = {
    "binary_root": "\u062d\u0633",
    "letter1": "\u062d",
    "letter2": "\u0633",
    "jabal_shared_meaning": "\u0646\u0641\u0627\u0630 \u062d\u0627\u062f \u0641\u064a \u0633\u0637\u062d \u0639\u0631\u064a\u0636",
    "jabal_features": ["\u0646\u0641\u0627\u0630", "\u062d\u062f\u0629", "\u0633\u0637\u062d"],
    "member_roots": ["\u062d\u0633\u0628", "\u062d\u0633\u062f", "\u062d\u0633\u0631"],
    "member_count": 3,
    "reverse_exists": False,
    "reverse_root": None,
    "model_a_score": None,
    "model_b_score": None,
    "model_c_score": None,
    "model_d_score": None,
    "best_model": None,
    "golden_rule_score": None,
    "status": "empty",
}


def _write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")


class TestLetterLoading:
    def test_load_empty_dir_returns_empty(self, tmp_path):
        d = tmp_path / "letters"
        d.mkdir()
        atoms = load_letter_atoms(d)
        assert atoms == []

    def test_load_single_scholar(self, tmp_path):
        d = tmp_path / "letters"
        _write_jsonl(d / "jabal.jsonl", [SAMPLE_JABAL_LETTER])
        atoms = load_letter_atoms(d)
        assert len(atoms) == 1
        assert atoms[0].letter == "\u0628"
        assert atoms[0].scholar == "jabal"

    def test_load_multiple_scholars(self, tmp_path):
        d = tmp_path / "letters"
        _write_jsonl(d / "jabal.jsonl", [SAMPLE_JABAL_LETTER])
        _write_jsonl(d / "abbas.jsonl", [SAMPLE_ABBAS_LETTER])
        atoms = load_letter_atoms(d)
        assert len(atoms) == 2

    def test_registry_merges_scholars(self, tmp_path):
        d = tmp_path / "letters"
        _write_jsonl(d / "jabal.jsonl", [SAMPLE_JABAL_LETTER])
        _write_jsonl(d / "abbas.jsonl", [SAMPLE_ABBAS_LETTER])
        registry = load_letter_atom_registry(d)
        assert "\u0628" in registry
        entry = registry["\u0628"]
        assert len(entry.scholar_entries) == 2

    def test_registry_computes_consensus(self, tmp_path):
        d = tmp_path / "letters"
        # Both scholars agree on no features (different sets)
        _write_jsonl(d / "jabal.jsonl", [SAMPLE_JABAL_LETTER])
        _write_jsonl(d / "abbas.jsonl", [SAMPLE_ABBAS_LETTER])
        registry = load_letter_atom_registry(d)
        entry = registry["\u0628"]
        # consensus_features should be empty since jabal and abbas have different features
        # OR they may share some — this test just checks the field exists
        assert isinstance(entry.consensus_features, tuple)

    def test_atoms_have_correct_features(self, tmp_path):
        d = tmp_path / "letters"
        _write_jsonl(d / "jabal.jsonl", [SAMPLE_JABAL_LETTER])
        atoms = load_letter_atoms(d)
        assert atoms[0].atomic_features == ("\u062a\u062c\u0645\u0639", "\u0631\u062e\u0627\u0648\u0629", "\u062a\u0644\u0627\u0635\u0642")
        assert atoms[0].feature_categories == ("gathering_cohesion", "texture_quality", "gathering_cohesion")

    def test_registry_agreement_level_contested_when_no_shared_features(self, tmp_path):
        d = tmp_path / "letters"
        _write_jsonl(d / "jabal.jsonl", [SAMPLE_JABAL_LETTER])
        _write_jsonl(d / "abbas.jsonl", [SAMPLE_ABBAS_LETTER])
        registry = load_letter_atom_registry(d)
        entry = registry["\u0628"]
        # 2 scholars but no shared features -> contested
        assert entry.agreement_level == "contested"

    def test_registry_majority_when_two_scholars_share_feature(self, tmp_path):
        d = tmp_path / "letters"
        shared_feature = "\u062a\u062c\u0645\u0639"
        jabal = dict(SAMPLE_JABAL_LETTER)
        abbas = dict(SAMPLE_ABBAS_LETTER)
        # Give both scholars a shared feature
        abbas["atomic_features"] = [shared_feature, "\u0627\u062a\u0633\u0627\u0639"]
        abbas["feature_categories"] = ["gathering_cohesion", "extension_movement"]
        _write_jsonl(d / "jabal.jsonl", [jabal])
        _write_jsonl(d / "abbas.jsonl", [abbas])
        registry = load_letter_atom_registry(d)
        entry = registry["\u0628"]
        assert shared_feature in entry.consensus_features
        assert entry.agreement_level == "majority"


class TestBinaryNucleusLoading:
    def test_load_nucleus(self, tmp_path):
        d = tmp_path / "binary_fields"
        _write_jsonl(d / "nuclei.jsonl", [SAMPLE_NUCLEUS])
        nuclei = load_binary_nuclei(d)
        assert "\u062d\u0633" in nuclei
        assert nuclei["\u062d\u0633"].member_count == 3

    def test_nucleus_member_roots_are_tuple(self, tmp_path):
        d = tmp_path / "binary_fields"
        _write_jsonl(d / "nuclei.jsonl", [SAMPLE_NUCLEUS])
        nuclei = load_binary_nuclei(d)
        assert isinstance(nuclei["\u062d\u0633"].member_roots, tuple)

    def test_nucleus_scoring_fields_default_none(self, tmp_path):
        d = tmp_path / "binary_fields"
        _write_jsonl(d / "nuclei.jsonl", [SAMPLE_NUCLEUS])
        nucleus = load_binary_nuclei(d)["\u062d\u0633"]
        assert nucleus.model_a_score is None
        assert nucleus.best_model is None
        assert nucleus.golden_rule_score is None


class TestTriliteralRootLoading:
    def test_load_root(self, tmp_path):
        d = tmp_path / "roots"
        root_data = {
            "root": "\u062d\u0633\u0628",
            "binary_nucleus": "\u062d\u0633",
            "third_letter": "\u0628",
            "jabal_axial_meaning": "\u062a\u062c\u0645\u064a\u0639 \u0627\u0644\u0645\u062a\u0641\u0631\u0642",
            "jabal_features": ["\u062a\u062c\u0645\u0639", "\u062a\u0644\u0627\u0635\u0642"],
            "predicted_meaning": None,
            "predicted_features": None,
            "prediction_score": None,
            "quranic_verse": None,
            "bab": "\u0627\u0644\u062d\u0627\u0621",
            "status": "empty",
        }
        _write_jsonl(d / "roots.jsonl", [root_data])
        roots = load_trilateral_roots(d)
        assert "\u062d\u0633\u0628" in roots

    def test_root_links_to_binary_nucleus(self, tmp_path):
        d = tmp_path / "roots"
        root_data = {
            "root": "\u062d\u0633\u0628",
            "binary_nucleus": "\u062d\u0633",
            "third_letter": "\u0628",
            "jabal_axial_meaning": "\u062a\u062c\u0645\u064a\u0639 \u0627\u0644\u0645\u062a\u0641\u0631\u0642",
            "jabal_features": ["\u062a\u062c\u0645\u0639"],
            "predicted_meaning": None,
            "predicted_features": None,
            "prediction_score": None,
            "quranic_verse": None,
            "bab": "\u0627\u0644\u062d\u0627\u0621",
            "status": "empty",
        }
        _write_jsonl(d / "roots.jsonl", [root_data])
        roots = load_trilateral_roots(d)
        assert roots["\u062d\u0633\u0628"].binary_nucleus == "\u062d\u0633"
        assert roots["\u062d\u0633\u0628"].third_letter == "\u0628"


class TestTheoryClaimLoading:
    def test_load_claim(self, tmp_path):
        d = tmp_path / "theory_claims"
        claim = {
            "claim_id": "jabal_001",
            "theme": "binary_derivation",
            "scholar": "jabal",
            "statement": "\u0623\u0648\u0644 \u062d\u0631\u0641\u064a\u0646 \u064a\u062d\u062f\u062f\u0627\u0646 \u0627\u0644\u062d\u0642\u0644 \u0627\u0644\u062f\u0644\u0627\u0644\u064a",
            "scope": "arabic_general",
            "evidence_type": "lexical",
            "source_document": "\u0627\u0644\u0645\u0639\u062c\u0645 \u0627\u0644\u0627\u0634\u062a\u0642\u0627\u0642\u064a \u0627\u0644\u0645\u0624\u0635\u0644",
            "source_locator": None,
            "status": "curated",
        }
        _write_jsonl(d / "claims.jsonl", [claim])
        claims = load_theory_claims(d)
        assert len(claims) == 1
        assert claims[0].claim_id == "jabal_001"

    def test_load_claim_with_source_doc_field(self, tmp_path):
        """Ensure the legacy 'source_doc' field name also works."""
        d = tmp_path / "theory_claims"
        claim = {
            "claim_id": "jabal_002",
            "theme": "letter_semantics",
            "scholar": "jabal",
            "statement": "\u0643\u0644 \u062d\u0631\u0641 \u0644\u0647 \u0645\u0639\u0646\u0649 \u062c\u0648\u0647\u0631\u064a",
            "scope": "arabic_general",
            "evidence_type": "lexical",
            "source_doc": "\u0627\u0644\u0645\u0639\u062c\u0645 \u0627\u0644\u0627\u0634\u062a\u0642\u0627\u0642\u064a \u0627\u0644\u0645\u0624\u0635\u0644",
            "source_locator": None,
            "status": "curated",
        }
        _write_jsonl(d / "claims.jsonl", [claim])
        claims = load_theory_claims(d)
        assert len(claims) == 1
        assert claims[0].claim_id == "jabal_002"


class TestGracefulDegradation:
    def test_missing_dir_returns_empty(self, tmp_path):
        missing = tmp_path / "nonexistent"
        assert load_letter_atoms(missing) == []
        assert load_letter_atom_registry(missing) == {}
        assert load_binary_nuclei(missing) == {}
        assert load_trilateral_roots(missing) == {}
        assert load_theory_claims(missing) == []
