from __future__ import annotations

import json
from pathlib import Path

from juthoor_cognatediscovery_lv2.discovery.genome_scoring import (
    GenomeScorer,
    _LETTER_CLASS,
    _extract_binary_root,
    classify_pair,
)
from juthoor_cognatediscovery_lv2.discovery.scoring import apply_hybrid_scoring
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
    return tmp_path


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


def test_genome_bonus_no_lang_field_falls_through(tmp_path: Path):
    """When lang fields are absent the guard is skipped and scoring proceeds normally."""
    scorer = GenomeScorer(_write_promoted(tmp_path))
    # No 'lang' key — existing behaviour is preserved (binary root match applies)
    bonus = scorer.genome_bonus(
        {"lemma": "عين", "root_norm": "عين"},
        {"lemma": "עין"},
    )
    assert bonus == 0.13

