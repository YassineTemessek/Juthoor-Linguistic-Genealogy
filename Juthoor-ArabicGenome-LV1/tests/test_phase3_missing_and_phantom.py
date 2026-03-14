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


missing = _load_script(
    REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "scripts" / "research_factory" / "axis2" / "exp_2_2_missing_combinations.py",
    "phase3_missing",
)
phantom = _load_script(
    REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "scripts" / "research_factory" / "axis6" / "exp_6_4_phantom_roots.py",
    "phase3_phantom",
)


def test_all_binary_pairs_count() -> None:
    pairs = missing.all_binary_pairs(["ب", "ت", "ث"])
    assert len(pairs) == 9
    assert "بت" in pairs


def test_generate_candidate_by_position() -> None:
    assert phantom.generate_candidate("بر", "و", 1) == "وبر"
    assert phantom.generate_candidate("بر", "و", 2) == "بور"
    assert phantom.generate_candidate("بر", "و", 3) == "برو"


def test_canonical_tri_root_normalizes_hamza() -> None:
    assert phantom.canonical_tri_root("أوب/أيب") == "ءوب"
