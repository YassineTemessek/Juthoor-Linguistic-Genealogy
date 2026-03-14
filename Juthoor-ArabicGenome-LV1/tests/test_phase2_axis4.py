from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1].parent


def _load_script(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


axis4_metathesis = _load_script(
    REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "scripts" / "research_factory" / "axis4" / "exp_4_1_binary_metathesis.py",
    "phase2_axis4_metathesis",
)
axis4_substitution = _load_script(
    REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "scripts" / "research_factory" / "axis4" / "exp_4_3_phonetic_substitution.py",
    "phase2_axis4_substitution",
)


def test_build_metathesis_pairs_detects_reversals() -> None:
    pairs = axis4_metathesis.build_metathesis_pairs(["بر", "رب", "بت", "تب", "دد"])
    assert ("بر", "رب") in pairs
    assert ("بت", "تب") in pairs
    assert all(a < b for a, b in pairs)


def test_classify_similarity_thresholds() -> None:
    assert axis4_metathesis.classify_similarity(0.8) == "similar"
    assert axis4_metathesis.classify_similarity(0.2) == "divergent"
    assert axis4_metathesis.classify_similarity(0.5) == "middle"


def test_canonical_tri_root_normalizes_variants() -> None:
    assert axis4_substitution.canonical_tri_root("أوب/أيب") == "ءوب"
    assert axis4_substitution.canonical_tri_root("حصحص-حصحص") is None


def test_find_single_substitution_pairs_groups_by_single_change() -> None:
    pairs = axis4_substitution.find_single_substitution_pairs(["بوب", "بيب", "بوب", "توب"])
    assert ("بوب", "بيب", 1) in pairs
    assert ("بوب", "توب", 0) in pairs
