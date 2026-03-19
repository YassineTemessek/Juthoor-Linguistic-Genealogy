from __future__ import annotations

import json
from pathlib import Path

from juthoor_arabicgenome_lv1.core.canon_models import BinaryFieldEntry, LetterSemanticEntry, RootCompositionEntry, SourceEntry
from juthoor_arabicgenome_lv1.core.canon_pipeline import CanonRegistries, process_root


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _seed_promoted_outputs(repo_root: Path) -> None:
    promoted = repo_root / "outputs" / "research_factory" / "promoted" / "promoted_features"
    reports = repo_root / "outputs" / "research_factory" / "reports"
    _write_jsonl(
        promoted / "metathesis_pairs.jsonl",
        [{"binary_root_a": "بر", "binary_root_b": "رب", "score": 0.5}],
    )
    _write_jsonl(
        promoted / "positional_profiles.jsonl",
        [{"letter": "ض", "p_value": 0.001, "positions": {"final": {"mean": 0.9}}}],
    )
    _write_json(
        reports / "3.2_result.json",
        {"metrics": {"supports_compositional_signal": True, "supports_full_compositionality": False}},
    )
    _write_json(
        reports / "5.2_result.json",
        {"metrics": {"supports_h9": False, "p_value": 0.5}},
    )


def _source() -> tuple[SourceEntry, ...]:
    return (
        SourceEntry(
            source_id="s1",
            scholar="jabal",
            claim_type="semantic",
            claim_text="demo",
            document_ref="doc",
            curation_status="accepted",
        ),
    )


def test_process_root_with_complete_data(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    _seed_promoted_outputs(repo_root)
    import juthoor_arabicgenome_lv1.core.canon_pipeline as canon_pipeline

    monkeypatch.setattr(canon_pipeline, "_repo_root", lambda: repo_root)
    registries = CanonRegistries(
        letters={
            "ب": LetterSemanticEntry("ب", "الباء", "بروز", None, None, None, _source(), "majority", "medium", "draft"),
            "ر": LetterSemanticEntry("ر", "الراء", "جريان", None, None, None, _source(), "majority", "medium", "draft"),
            "ض": LetterSemanticEntry("ض", "الضاد", "شدة", None, None, None, _source(), "majority", "medium", "draft"),
        },
        binary_fields={
            "بر": BinaryFieldEntry("بر", "ظهور واتساع", "jabal", "ب", "ر", "بروز", "جريان", ("برض",), 1, 0.72, None, "draft")
        },
        root_composition={
            "برض": RootCompositionEntry("برض", "بر", "ض", "سطح ظاهر", "ظهور واتساع", "أرض بارزة", None, None, None, 0.4, None, "draft")
        },
    )

    analysis = process_root("برض", registries)

    assert analysis.classification == "resolved"
    assert analysis.binary_field_meaning == "ظهور واتساع"
    assert analysis.position_profile is not None
    assert analysis.evidence["field_coherence"] == 0.72
    assert analysis.evidence["h10_partial_compositionality"]["supports_compositional_signal"] is True
    assert analysis.evidence["h9_negative_evidence"]["supports_h9"] is False


def test_process_root_with_missing_canon_content(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    _seed_promoted_outputs(repo_root)
    import juthoor_arabicgenome_lv1.core.canon_pipeline as canon_pipeline

    monkeypatch.setattr(canon_pipeline, "_repo_root", lambda: repo_root)
    registries = CanonRegistries(
        letters={},
        binary_fields={},
        root_composition={"برض": RootCompositionEntry("برض", "بر", "ض", None, None, None, None, None, None, None, None, "draft")},
    )

    analysis = process_root("برض", registries)

    assert analysis.classification == "underdescribed"
    assert "conceptual_meaning" in analysis.missing_layers
    assert "binary_field_meaning" in analysis.missing_layers
    assert "letter_trace" in analysis.missing_layers


def test_process_root_unknown_root() -> None:
    analysis = process_root("xyz", CanonRegistries(letters={}, binary_fields={}, root_composition={}))

    assert analysis.classification == "underdescribed"
    assert analysis.root == "xyz"
