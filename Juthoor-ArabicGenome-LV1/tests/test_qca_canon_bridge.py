from __future__ import annotations

from juthoor_arabicgenome_lv1.core.canon_models import BinaryFieldEntry, LetterSemanticEntry, RootCompositionEntry, SourceEntry
from juthoor_arabicgenome_lv1.core.canon_pipeline import CanonRegistries
from juthoor_arabicgenome_lv1.qca.canon_bridge import build_interpretation_evidence_card, build_quranic_profile


def _source() -> tuple[SourceEntry, ...]:
    return (
        SourceEntry(
            source_id="seed",
            scholar="jabal",
            claim_type="semantic",
            claim_text="demo",
            document_ref="doc",
            curation_status="accepted",
        ),
    )


def test_build_quranic_profile_preserves_three_layers(tmp_path, monkeypatch) -> None:
    import juthoor_arabicgenome_lv1.core.canon_pipeline as canon_pipeline

    repo_root = tmp_path / "repo"
    (repo_root / "outputs" / "research_factory" / "promoted" / "promoted_features").mkdir(parents=True)
    (repo_root / "outputs" / "research_factory" / "reports").mkdir(parents=True)
    (repo_root / "outputs" / "research_factory" / "reports" / "3.2_result.json").write_text('{"metrics":{"supports_compositional_signal":true}}', encoding="utf-8")
    (repo_root / "outputs" / "research_factory" / "reports" / "5.2_result.json").write_text('{"metrics":{"supports_h9":false}}', encoding="utf-8")
    monkeypatch.setattr(canon_pipeline, "_repo_root", lambda: repo_root)

    registries = CanonRegistries(
        letters={"ا": LetterSemanticEntry("ا", "الألف", "ابتداء", None, None, None, _source(), "majority", "medium", "draft")},
        binary_fields={"ار": BinaryFieldEntry("ار", "امتداد", "jabal", "ا", "ر", "ابتداء", "جريان", ("ارض",), 1, 0.5, None, "draft")},
        root_composition={"ارض": RootCompositionEntry("ارض", "ار", "ض", "سطح", "امتداد", "الأرض", None, None, None, None, None, "draft")},
    )

    profile = build_quranic_profile("الأرض", "ارض", registries)

    assert profile.conceptual_meaning == "سطح"
    assert profile.lexical_realization == "الأرض"
    assert isinstance(profile.contextual_constraints, tuple)


def test_build_evidence_card_marks_incompleteness(tmp_path, monkeypatch) -> None:
    import juthoor_arabicgenome_lv1.core.canon_pipeline as canon_pipeline

    repo_root = tmp_path / "repo"
    (repo_root / "outputs" / "research_factory" / "promoted" / "promoted_features").mkdir(parents=True)
    (repo_root / "outputs" / "research_factory" / "reports").mkdir(parents=True)
    (repo_root / "outputs" / "research_factory" / "reports" / "3.2_result.json").write_text("{}", encoding="utf-8")
    (repo_root / "outputs" / "research_factory" / "reports" / "5.2_result.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(canon_pipeline, "_repo_root", lambda: repo_root)

    registries = CanonRegistries(
        letters={},
        binary_fields={},
        root_composition={"ارض": RootCompositionEntry("ارض", "ار", "ض", None, None, None, None, None, None, None, None, "draft")},
    )
    card = build_interpretation_evidence_card("الأرض", "ارض", registries)

    assert "contextual_constraints" in card
    assert any(item.startswith("missing:") for item in card["contextual_constraints"])
