from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from juthoor_cognatediscovery_lv2.discovery.root_quality_scorer import RootQualityScorer
from juthoor_cognatediscovery_lv2.discovery.scoring import (
    DiscoveryScorer,
    _apply_root_quality_bonus,
    apply_hybrid_scoring,
)
from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import HybridWeights

_TEST_TMP_DIR = Path(__file__).resolve().parents[2] / ".codex_tmp" / "root_quality_tests"


def _write_predictions() -> Path:
    _TEST_TMP_DIR.mkdir(parents=True, exist_ok=True)
    path = _TEST_TMP_DIR / f"{uuid4().hex}.jsonl"
    path.write_text(
        "\n".join(
            (
                '{"tri_root":"كتب","cosine_similarity":0.731234}',
                '{"tri_root":"ذرو/ذرى","cosine_similarity":0.812345}',
                '{"tri_root":"ملأ","cosine_similarity":0.190001}',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _make_candidates(source_root: str | None = None, semantic: float = 0.5, form: float = 0.4) -> dict[str, dict]:
    src_fields: dict[str, str] = {}
    if source_root is not None:
        src_fields["root_norm"] = source_root
    return {
        "cand1": {
            "scores": {"semantic": semantic, "form": form},
            "_source_fields": src_fields,
            "_target_fields": {},
        }
    }


def test_root_quality_returns_known_root_score():
    scorer = RootQualityScorer(_write_predictions())
    assert scorer.root_quality("كتب") == pytest.approx(0.731234)


def test_root_quality_normalizes_variants():
    scorer = RootQualityScorer(_write_predictions())
    assert scorer.root_quality("ذرى") == pytest.approx(0.812345)
    assert scorer.root_quality("ذرو") == pytest.approx(0.812345)
    assert scorer.root_quality("ملا") == pytest.approx(0.190001)


def test_root_quality_unknown_root_returns_zero():
    scorer = RootQualityScorer(_write_predictions())
    assert scorer.root_quality("جهل") == pytest.approx(0.0)


def test_apply_root_quality_bonus_caps_at_point_zero_eight():
    scorer = RootQualityScorer(_write_predictions())
    result = _apply_root_quality_bonus(
        {"combined_score": 0.5, "components": {}},
        source_fields={"root_norm": "ذرى"},
        root_quality_scorer=scorer,
    )
    assert result["components"]["root_quality_bonus"] == pytest.approx(0.08)
    assert result["combined_score"] == pytest.approx(0.58)


def test_apply_hybrid_scoring_records_root_quality_bonus():
    scorer = RootQualityScorer(_write_predictions())
    candidates = _make_candidates(source_root="كتب")
    apply_hybrid_scoring(candidates, HybridWeights(), root_quality_scorer=scorer)
    hybrid = candidates["cand1"]["hybrid"]
    assert hybrid["components"]["root_quality_bonus"] == pytest.approx(0.08)


def test_apply_hybrid_scoring_sets_zero_bonus_without_scorer():
    candidates = _make_candidates(source_root="كتب")
    apply_hybrid_scoring(candidates, HybridWeights(), root_quality_scorer=None)
    hybrid = candidates["cand1"]["hybrid"]
    assert hybrid["components"]["root_quality_bonus"] == pytest.approx(0.0)


def test_discovery_scorer_applies_root_quality_bonus():
    scorer = RootQualityScorer(_write_predictions())
    discovery_scorer = DiscoveryScorer(root_quality_scorer=scorer)
    results = discovery_scorer.score(_make_candidates(source_root="كتب"))
    assert results[0]["hybrid"]["components"]["root_quality_bonus"] == pytest.approx(0.08)
