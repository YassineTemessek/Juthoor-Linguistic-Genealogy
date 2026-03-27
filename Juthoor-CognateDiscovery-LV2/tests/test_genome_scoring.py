from __future__ import annotations

import json
from pathlib import Path

from unittest.mock import MagicMock

from juthoor_cognatediscovery_lv2.discovery.genome_scoring import (
    GenomeScorer,
    _LETTER_CLASS,
    _extract_binary_root,
    classify_pair,
)
from juthoor_cognatediscovery_lv2.discovery.scoring import (
    _apply_phonetic_law_bonus,
    apply_hybrid_scoring,
)
from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import HybridWeights


def _write_promoted(tmp_path: Path) -> Path:
    features = tmp_path / "promoted_features"
    features.mkdir(parents=True)
    (features / "field_coherence_scores.jsonl").write_text(
        json.dumps({"binary_root": "ʕy", "coherence": 0.72}) + "\n"
        + json.dumps({"binary_root": "by", "coherence": 0.68}) + "\n",
        encoding="utf-8",
    )
    (features / "metathesis_pairs.jsonl").write_text(
        json.dumps({"binary_root_a": "qb", "binary_root_b": "bq"}) + "\n",
        encoding="utf-8",
    )
    (features / "cross_lingual_support.jsonl").write_text(
        json.dumps(
            {
                "binary_root": "ʕy",
                "semitic_support": {"rows": 2, "exact_hit_rate": 0.5, "binary_hit_rate": 1.0},
                "non_semitic_support": {"rows": 0, "exact_hit_rate": 0.0, "binary_hit_rate": 0.0},
                "support_score": 0.85,
            }
        ) + "\n",
        encoding="utf-8",
    )
    return tmp_path


def _write_synonym_families(tmp_path: Path) -> Path:
    path = tmp_path / "synonym_families_full.jsonl"
    path.write_text(
        json.dumps(
            {
                "family_id": "seed-001",
                "roots": ["قلب", "لب", "فؤاد"],
                "shared_concept": "heart",
            },
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )
    return path


def test_genome_bonus_uses_cross_script_binary_match(tmp_path: Path):
    scorer = GenomeScorer(_write_promoted(tmp_path))
    bonus = scorer.genome_bonus(
        {"lemma": "عين", "root_norm": "عين"},
        {"lemma": "עין"},
    )
    assert bonus == 0.13


def test_genome_bonus_is_pair_sensitive_not_source_only(tmp_path: Path):
    scorer = GenomeScorer(_write_promoted(tmp_path))
    bonus = scorer.genome_bonus(
        {"lemma": "عين", "root_norm": "عين"},
        {"lemma": "אב"},
    )
    assert bonus == 0.0


def test_genome_bonus_persisted_in_components(tmp_path: Path):
    """After scoring with GenomeScorer, genome_bonus must appear in hybrid.components."""
    scorer = GenomeScorer(_write_promoted(tmp_path))
    candidates = {
        "pair1": {
            "scores": {"semantic": 0.7, "form": 0.5},
            "_source_fields": {"lemma": "عين", "root_norm": "عين"},
            "_target_fields": {"lemma": "עין"},
        }
    }
    apply_hybrid_scoring(candidates, HybridWeights(), genome_scorer=scorer)
    entry = candidates["pair1"]
    components = entry["hybrid"]["components"]
    assert "genome_bonus" in components, "genome_bonus must be stored in hybrid.components"
    assert isinstance(components["genome_bonus"], float)
    assert components["genome_bonus"] == 0.13


def test_genome_bonus_defaults_to_zero_in_components_without_scorer():
    """When no GenomeScorer is used, genome_bonus must default to 0.0 in components."""
    candidates = {
        "pair1": {
            "scores": {"semantic": 0.6, "form": 0.4},
            "_source_fields": {"lemma": "cat"},
            "_target_fields": {"lemma": "chat"},
        }
    }
    apply_hybrid_scoring(candidates, HybridWeights(), genome_scorer=None)
    entry = candidates["pair1"]
    components = entry["hybrid"]["components"]
    assert "genome_bonus" in components
    assert components["genome_bonus"] == 0.0


def test_aramaic_consonants_mapped():
    """Aramaic uses Hebrew script — all consonants should resolve to phoneme classes."""
    # Aramaic shares the Hebrew alphabet, so all 22 Hebrew letters must be present.
    # Test with representative Aramaic vocabulary:
    #   כתב (write) — kaf + tav + bet
    #   מלך (king)  — mem + lamed + kaf
    ktb_binary = _extract_binary_root("כתב")
    assert ktb_binary is not None, "כתב (write) must yield a binary root"
    # kaf → ḫ, tav → t
    assert ktb_binary == "ḫt", f"Expected 'ḫt', got '{ktb_binary}'"

    mlk_binary = _extract_binary_root("מלך")
    assert mlk_binary is not None, "מלך (king) must yield a binary root"
    # mem → m, lamed → l
    assert mlk_binary == "ml", f"Expected 'ml', got '{mlk_binary}'"

    # Confirm every core Aramaic consonant class is mapped
    for ch in "אבגדהוזחטיכלמנסעפצקרשת":
        assert ch in _LETTER_CLASS, f"Hebrew/Aramaic letter {ch!r} (U+{ord(ch):04X}) missing from _LETTER_CLASS"


def test_persian_specific_consonants_mapped():
    """Persian-specific letters (پ, چ, ژ, گ) should resolve to phoneme classes."""
    assert "پ" in _LETTER_CLASS, "Persian pe (U+067E) missing"
    assert "چ" in _LETTER_CLASS, "Persian che (U+0686) missing"
    assert "ژ" in _LETTER_CLASS, "Persian zhe (U+0698) missing"
    assert "گ" in _LETTER_CLASS, "Persian gaf (U+06AF) missing"
    assert _LETTER_CLASS["پ"] == "p"
    assert _LETTER_CLASS["چ"] == "č"
    assert _LETTER_CLASS["ژ"] == "ž"
    assert _LETTER_CLASS["گ"] == "g"


def test_persian_keheh_and_yeh_mapped():
    """Persian ک (U+06A9) and ی (U+06CC) should map to same classes as Arabic ك/ي."""
    assert _LETTER_CLASS.get("ک") == "k", "Persian keheh (U+06A9) must map to 'k'"
    assert _LETTER_CLASS.get("ی") == "y", "Persian yeh (U+06CC) must map to 'y'"


def test_persian_binary_root_extraction():
    """Persian words should yield binary roots via _extract_binary_root."""
    # پادشاه (king) — پ + ا → "pʔ"
    br = _extract_binary_root("پادشاه")
    assert br is not None, "Persian پادشاه must yield a binary root"
    assert br == "pʔ", f"Expected 'pʔ', got '{br!r}'"

    # کتاب (book) — ک + ت → "kt"
    br2 = _extract_binary_root("کتاب")
    assert br2 is not None, "Persian کتاب must yield a binary root"
    assert br2 == "kt", f"Expected 'kt', got '{br2!r}'"


# ---------------------------------------------------------------------------
# Language family classification tests
# ---------------------------------------------------------------------------

def test_classify_pair_semitic():
    assert classify_pair("ara", "heb") == "semitic_semitic"
    assert classify_pair("ara", "arc") == "semitic_semitic"
    assert classify_pair("heb", "arc") == "semitic_semitic"
    assert classify_pair("ara", "ar-qur") == "semitic_semitic"


def test_classify_pair_cross_family():
    assert classify_pair("ara", "eng") == "semitic_ie"
    assert classify_pair("ara", "lat") == "semitic_ie"
    assert classify_pair("ara", "grc") == "semitic_ie"
    assert classify_pair("heb", "fa") == "semitic_ie"
    # reversed order
    assert classify_pair("eng", "ara") == "semitic_ie"
    assert classify_pair("lat", "heb") == "semitic_ie"


def test_classify_pair_ie():
    assert classify_pair("lat", "grc") == "same_family"
    assert classify_pair("eng", "lat") == "same_family"
    assert classify_pair("fa", "enm") == "same_family"


def test_classify_pair_unknown():
    assert classify_pair("zxx", "zzz") == "unknown"


def test_genome_bonus_zero_for_non_semitic(tmp_path: Path):
    scorer = GenomeScorer(_write_promoted(tmp_path))
    source = {"lang": "ara", "lemma": "عين", "root_norm": "عين"}
    target = {"lang": "eng", "lemma": "eye", "root_norm": "eye"}
    bonus = scorer.genome_bonus(source, target)
    assert bonus == 0.0, f"Expected 0.0 for cross-family pair, got {bonus}"


def test_genome_bonus_zero_for_same_family(tmp_path: Path):
    scorer = GenomeScorer(_write_promoted(tmp_path))
    source = {"lang": "lat", "lemma": "oculus", "root_norm": "oculus"}
    target = {"lang": "grc", "lemma": "ὀφθαλμός", "root_norm": "ὀφθαλμός"}
    bonus = scorer.genome_bonus(source, target)
    assert bonus == 0.0, f"Expected 0.0 for same-family IE pair, got {bonus}"


def test_genome_bonus_applies_for_semitic_pair(tmp_path: Path):
    scorer = GenomeScorer(_write_promoted(tmp_path))
    source = {"lang": "ara", "lemma": "عين", "root_norm": "عين"}
    target = {"lang": "heb", "lemma": "עין"}
    bonus = scorer.genome_bonus(source, target)
    assert bonus == 0.13, f"Expected 0.13 for semitic_semitic pair, got {bonus}"


def test_cross_lingual_support_loaded_for_binary_root(tmp_path: Path):
    scorer = GenomeScorer(_write_promoted(tmp_path))
    support = scorer.cross_lingual_support("عين")
    assert support is not None
    assert support["binary_root"] == "ʕy"
    assert support["support_score"] == 0.85


def test_genome_bonus_no_lang_field_falls_through(tmp_path: Path):
    """When lang fields are absent the guard is skipped and scoring proceeds normally."""
    scorer = GenomeScorer(_write_promoted(tmp_path))
    # No 'lang' key — existing behaviour is preserved (binary root match applies)
    bonus = scorer.genome_bonus(
        {"lemma": "عين", "root_norm": "عين"},
        {"lemma": "עין"},
    )
    assert bonus == 0.13


def test_genome_bonus_expands_arabic_root_to_synonym_family(tmp_path: Path):
    features = tmp_path / "promoted_features"
    features.mkdir(parents=True)
    (features / "field_coherence_scores.jsonl").write_text(
        json.dumps({"binary_root": "lb", "coherence": 0.72}) + "\n",
        encoding="utf-8",
    )
    (features / "metathesis_pairs.jsonl").write_text("", encoding="utf-8")
    (features / "cross_lingual_support.jsonl").write_text(
        json.dumps(
            {
                "binary_root": "lb",
                "semitic_support": {"rows": 1, "exact_hit_rate": 1.0, "binary_hit_rate": 1.0},
                "non_semitic_support": {"rows": 0, "exact_hit_rate": 0.0, "binary_hit_rate": 0.0},
                "support_score": 0.91,
            }
        ) + "\n",
        encoding="utf-8",
    )
    scorer = GenomeScorer(
        tmp_path,
        synonym_families_path=_write_synonym_families(tmp_path),
    )

    bonus = scorer.genome_bonus(
        {"lang": "ara", "lemma": "قلب", "root_norm": "قلب"},
        {"lang": "heb", "lemma": "לב"},
    )
    support = scorer.cross_lingual_support("قلب")

    assert bonus == 0.13
    assert support is not None
    assert support["binary_root"] == "lb"


# ---------------------------------------------------------------------------
# cross_family_coherence_signal tests
# ---------------------------------------------------------------------------

def test_cross_family_coherence_signal_returns_float_for_known_root(tmp_path: Path):
    """cross_family_coherence_signal returns a float for a root with known coherence data."""
    scorer = GenomeScorer(_write_promoted(tmp_path))
    # عين maps to binary root ʕy which has coherence 0.72 in _write_promoted
    result = scorer.cross_family_coherence_signal({"root_norm": "عين"})
    assert result is not None
    assert isinstance(result, float)
    assert result == 0.72


def test_cross_family_coherence_signal_returns_none_for_unknown_root(tmp_path: Path):
    """cross_family_coherence_signal returns None when the root has no coherence data."""
    scorer = GenomeScorer(_write_promoted(tmp_path))
    result = scorer.cross_family_coherence_signal({"root_norm": "xyz"})
    assert result is None


def test_cross_family_coherence_signal_uses_lemma_fallback(tmp_path: Path):
    """cross_family_coherence_signal falls back to lemma when root_norm is absent."""
    scorer = GenomeScorer(_write_promoted(tmp_path))
    result = scorer.cross_family_coherence_signal({"lemma": "عين"})
    assert result is not None
    assert result == 0.72


def test_cross_family_coherence_signal_returns_none_for_empty_entry(tmp_path: Path):
    """cross_family_coherence_signal returns None when entry has no root or lemma."""
    scorer = GenomeScorer(_write_promoted(tmp_path))
    result = scorer.cross_family_coherence_signal({})
    assert result is None


# ---------------------------------------------------------------------------
# coherence modulation in _apply_phonetic_law_bonus tests
# ---------------------------------------------------------------------------

def _make_phonetic_scorer(bonus_value: float) -> MagicMock:
    mock = MagicMock()
    mock.phonetic_law_bonus.return_value = bonus_value
    return mock


def test_high_coherence_root_gets_boosted_bonus(tmp_path: Path):
    """High-coherence Arabic root (>0.6) boosts phonetic law bonus by 1.3x."""
    genome_scorer = GenomeScorer(_write_promoted(tmp_path))
    phonetic_scorer = _make_phonetic_scorer(0.10)
    hybrid = {"combined_score": 0.5, "components": {}}
    source_fields = {"root_norm": "عين", "lang": "ara"}  # coherence 0.72 → high
    target_fields = {"lemma": "eye", "lang": "eng"}

    result = _apply_phonetic_law_bonus(
        hybrid,
        source_fields=source_fields,
        target_fields=target_fields,
        phonetic_law_scorer=phonetic_scorer,
        genome_scorer=genome_scorer,
    )

    # 0.10 * 1.3 = 0.13, capped at 0.15
    assert result["components"]["phonetic_law_bonus"] == 0.13
    assert result["components"]["source_coherence"] == 0.72


def test_low_coherence_root_gets_dampened_bonus(tmp_path: Path):
    """Low-coherence Arabic root (<0.3) reduces phonetic law bonus by 0.7x."""
    # Write a custom promoted dir with a low-coherence root
    features = tmp_path / "promoted_features"
    features.mkdir(parents=True)
    (features / "field_coherence_scores.jsonl").write_text(
        json.dumps({"binary_root": "ʕy", "coherence": 0.20}) + "\n",
        encoding="utf-8",
    )
    (features / "metathesis_pairs.jsonl").write_text("", encoding="utf-8")
    (features / "cross_lingual_support.jsonl").write_text("", encoding="utf-8")

    genome_scorer = GenomeScorer(tmp_path)
    phonetic_scorer = _make_phonetic_scorer(0.10)
    hybrid = {"combined_score": 0.5, "components": {}}
    source_fields = {"root_norm": "عين", "lang": "ara"}  # coherence 0.20 → low
    target_fields = {"lemma": "eye", "lang": "eng"}

    result = _apply_phonetic_law_bonus(
        hybrid,
        source_fields=source_fields,
        target_fields=target_fields,
        phonetic_law_scorer=phonetic_scorer,
        genome_scorer=genome_scorer,
    )

    # 0.10 * 0.7 = 0.07
    assert abs(result["components"]["phonetic_law_bonus"] - 0.07) < 1e-6
    assert result["components"]["source_coherence"] == 0.20


def test_mid_coherence_root_passes_through_unchanged(tmp_path: Path):
    """Mid-coherence root (0.3-0.6) leaves the bonus unchanged."""
    features = tmp_path / "promoted_features"
    features.mkdir(parents=True)
    (features / "field_coherence_scores.jsonl").write_text(
        json.dumps({"binary_root": "ʕy", "coherence": 0.45}) + "\n",
        encoding="utf-8",
    )
    (features / "metathesis_pairs.jsonl").write_text("", encoding="utf-8")
    (features / "cross_lingual_support.jsonl").write_text("", encoding="utf-8")

    genome_scorer = GenomeScorer(tmp_path)
    phonetic_scorer = _make_phonetic_scorer(0.10)
    hybrid = {"combined_score": 0.5, "components": {}}
    source_fields = {"root_norm": "عين", "lang": "ara"}
    target_fields = {"lemma": "eye", "lang": "eng"}

    result = _apply_phonetic_law_bonus(
        hybrid,
        source_fields=source_fields,
        target_fields=target_fields,
        phonetic_law_scorer=phonetic_scorer,
        genome_scorer=genome_scorer,
    )

    # 0.10, no multiplier, still capped at 0.15
    assert abs(result["components"]["phonetic_law_bonus"] - 0.10) < 1e-6
    assert result["components"]["source_coherence"] == 0.45


def test_phonetic_bonus_still_capped_at_0_15_after_coherence_boost(tmp_path: Path):
    """Even with high-coherence boost, phonetic_law_bonus must not exceed 0.15."""
    genome_scorer = GenomeScorer(_write_promoted(tmp_path))
    # Base bonus of 0.14 * 1.3 = 0.182 — must be capped to 0.15
    phonetic_scorer = _make_phonetic_scorer(0.14)
    hybrid = {"combined_score": 0.5, "components": {}}
    source_fields = {"root_norm": "عين", "lang": "ara"}  # coherence 0.72 → high
    target_fields = {"lemma": "eye", "lang": "eng"}

    result = _apply_phonetic_law_bonus(
        hybrid,
        source_fields=source_fields,
        target_fields=target_fields,
        phonetic_law_scorer=phonetic_scorer,
        genome_scorer=genome_scorer,
    )

    assert result["components"]["phonetic_law_bonus"] == 0.15


def test_no_genome_scorer_leaves_phonetic_bonus_unchanged():
    """Without a genome_scorer, coherence modulation is skipped and bonus is unchanged."""
    phonetic_scorer = _make_phonetic_scorer(0.10)
    hybrid = {"combined_score": 0.5, "components": {}}
    source_fields = {"root_norm": "عين", "lang": "ara"}
    target_fields = {"lemma": "eye", "lang": "eng"}

    result = _apply_phonetic_law_bonus(
        hybrid,
        source_fields=source_fields,
        target_fields=target_fields,
        phonetic_law_scorer=phonetic_scorer,
        genome_scorer=None,
    )

    assert abs(result["components"]["phonetic_law_bonus"] - 0.10) < 1e-6
    assert "source_coherence" not in result["components"]
