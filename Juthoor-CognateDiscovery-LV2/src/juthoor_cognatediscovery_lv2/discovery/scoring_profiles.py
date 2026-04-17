"""
Scoring profiles for LV2 discovery pipeline.

Each profile is a named configuration of weights and bonus caps tuned for a
specific language pair or discovery mode. Profiles are selected at runtime
via get_profile() and passed into apply_hybrid_scoring() / DiscoveryScorer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ScoringProfile:
    """Named configuration of scoring weights and bonus caps.

    Attributes
    ----------
    name:
        Human-readable identifier (e.g. "ara_eng_default").
    semantic_weight:
        Weight for semantic similarity in hybrid score (0–1).
    form_weight:
        Weight for form/phonetic similarity in hybrid score (0–1).
    phonetic_law_cap:
        Maximum bonus that the PhoneticLawScorer may add.
    genome_cap:
        Maximum bonus that the GenomeScorer may add.
    multi_method_cap:
        Maximum bonus that the MultiMethodScorer may add.
    cross_pair_cap:
        Maximum bonus that the CrossPairScorer may add.
    root_quality_cap:
        Maximum bonus that the RootQualityScorer may add.
    prefilter_threshold:
        Minimum fast-prefilter score to pass a pair to the full scorer.
    final_threshold:
        Minimum combined score to emit a lead.
    description:
        Optional human-readable description of the profile's intent.
    """

    name: str
    semantic_weight: float = 0.55
    form_weight: float = 0.45
    phonetic_law_cap: float = 0.15
    genome_cap: float = 0.10
    multi_method_cap: float = 0.12
    cross_pair_cap: float = 0.10
    root_quality_cap: float = 0.08
    prefilter_threshold: float = 0.50
    final_threshold: float = 0.45
    description: str = ""

    def as_dict(self) -> dict[str, Any]:
        """Return profile as a plain dict for serialisation."""
        return {
            "name": self.name,
            "semantic_weight": self.semantic_weight,
            "form_weight": self.form_weight,
            "phonetic_law_cap": self.phonetic_law_cap,
            "genome_cap": self.genome_cap,
            "multi_method_cap": self.multi_method_cap,
            "cross_pair_cap": self.cross_pair_cap,
            "root_quality_cap": self.root_quality_cap,
            "prefilter_threshold": self.prefilter_threshold,
            "final_threshold": self.final_threshold,
            "description": self.description,
        }


# ---------------------------------------------------------------------------
# Built-in profiles
# ---------------------------------------------------------------------------

PROFILES: dict[str, ScoringProfile] = {
    # Default Arabic-English profile — balanced weights, all bonuses active
    "ara_eng_default": ScoringProfile(
        name="ara_eng_default",
        semantic_weight=0.55,
        form_weight=0.45,
        phonetic_law_cap=0.15,
        genome_cap=0.10,
        multi_method_cap=0.12,
        cross_pair_cap=0.10,
        root_quality_cap=0.08,
        prefilter_threshold=0.50,
        final_threshold=0.45,
        description="Balanced Arabic-English discovery with all scorers active.",
    ),

    # High-precision mode — stricter thresholds, lower caps to reduce false positives
    "ara_eng_precision": ScoringProfile(
        name="ara_eng_precision",
        semantic_weight=0.60,
        form_weight=0.40,
        phonetic_law_cap=0.12,
        genome_cap=0.08,
        multi_method_cap=0.10,
        cross_pair_cap=0.08,
        root_quality_cap=0.06,
        prefilter_threshold=0.60,
        final_threshold=0.60,
        description="High-precision mode: stricter thresholds, tighter bonus caps.",
    ),

    # High-recall mode — permissive thresholds, larger caps to catch distant cognates
    "ara_eng_recall": ScoringProfile(
        name="ara_eng_recall",
        semantic_weight=0.50,
        form_weight=0.50,
        phonetic_law_cap=0.18,
        genome_cap=0.12,
        multi_method_cap=0.15,
        cross_pair_cap=0.10,
        root_quality_cap=0.10,
        prefilter_threshold=0.40,
        final_threshold=0.35,
        description="High-recall mode: permissive thresholds for distant cognate discovery.",
    ),

    # Semitic-to-Semitic profile — no phonetic projection, heavier genome weight
    "semitic_semitic": ScoringProfile(
        name="semitic_semitic",
        semantic_weight=0.45,
        form_weight=0.55,
        phonetic_law_cap=0.08,
        genome_cap=0.15,
        multi_method_cap=0.12,
        cross_pair_cap=0.10,
        root_quality_cap=0.10,
        prefilter_threshold=0.50,
        final_threshold=0.45,
        description="Semitic-Semitic pairs: higher genome weight, reduced phonetic projection.",
    ),

    # Arabic-Latin/Greek profile — classical IE, no IPA enrichment
    "ara_classical_ie": ScoringProfile(
        name="ara_classical_ie",
        semantic_weight=0.55,
        form_weight=0.45,
        phonetic_law_cap=0.14,
        genome_cap=0.10,
        multi_method_cap=0.12,
        cross_pair_cap=0.08,
        root_quality_cap=0.08,
        prefilter_threshold=0.48,
        final_threshold=0.42,
        description="Arabic to classical IE (Latin/Greek): balanced with moderate phonetic law cap.",
    ),

    # Fast-only profile — low compute, no cross-pair bonus
    "fast_phonetic_only": ScoringProfile(
        name="fast_phonetic_only",
        semantic_weight=0.40,
        form_weight=0.60,
        phonetic_law_cap=0.15,
        genome_cap=0.00,
        multi_method_cap=0.00,
        cross_pair_cap=0.00,
        root_quality_cap=0.00,
        prefilter_threshold=0.55,
        final_threshold=0.50,
        description="Fast phonetic-only mode: no embedding-dependent bonuses.",
    ),

    # Arabic to Old English — balanced weights, less phonetic drift than modern English
    "ara_old_english": ScoringProfile(
        name="ara_old_english",
        semantic_weight=0.50,
        form_weight=0.50,
        phonetic_law_cap=0.16,
        genome_cap=0.10,
        multi_method_cap=0.12,
        cross_pair_cap=0.08,
        root_quality_cap=0.08,
        prefilter_threshold=0.40,
        final_threshold=0.40,
        description="Arabic to Old English: balanced weights, less phonetic drift than modern English",
    ),

    # Arabic to Middle English — higher semantic weight due to poor IPA coverage (26%)
    "ara_middle_english": ScoringProfile(
        name="ara_middle_english",
        semantic_weight=0.55,
        form_weight=0.45,
        phonetic_law_cap=0.14,
        genome_cap=0.10,
        multi_method_cap=0.12,
        cross_pair_cap=0.08,
        root_quality_cap=0.08,
        prefilter_threshold=0.40,
        final_threshold=0.42,
        description="Arabic to Middle English: higher semantic weight due to poor IPA coverage (26%)",
    ),

    # Arabic to Gothic — slightly higher form weight: single-scribe orthography is very consistent
    "ara_gothic": ScoringProfile(
        name="ara_gothic",
        semantic_weight=0.48,
        form_weight=0.52,
        phonetic_law_cap=0.16,
        genome_cap=0.10,
        multi_method_cap=0.12,
        cross_pair_cap=0.08,
        root_quality_cap=0.08,
        prefilter_threshold=0.40,
        final_threshold=0.40,
        description=(
            "Arabic to Gothic: slightly higher form weight because Wulfila's single-scribe "
            "orthography is highly consistent; Grimm's Law stop series applied."
        ),
    ),

    # Arabic to Old Irish — heavy radical sound changes (p-loss, lenition system)
    # Reduce form weight significantly; rely more on semantics and genome signals.
    "ara_old_irish": ScoringProfile(
        name="ara_old_irish",
        semantic_weight=0.62,
        form_weight=0.38,
        phonetic_law_cap=0.14,
        genome_cap=0.10,
        multi_method_cap=0.12,
        cross_pair_cap=0.08,
        root_quality_cap=0.08,
        prefilter_threshold=0.38,
        final_threshold=0.40,
        description=(
            "Arabic to Old Irish: reduced form weight for radical sound changes "
            "(p-loss, lenition mutations); higher semantic weight to compensate."
        ),
    ),

    # Arabic to Old Norse — North Germanic; þ/ð preserved, z > r rhotacism,
    # consistent Grimm's Law stop series. Balanced weights close to Gothic.
    "ara_old_norse": ScoringProfile(
        name="ara_old_norse",
        semantic_weight=0.48,
        form_weight=0.52,
        phonetic_law_cap=0.16,
        genome_cap=0.10,
        multi_method_cap=0.12,
        cross_pair_cap=0.08,
        root_quality_cap=0.08,
        prefilter_threshold=0.40,
        final_threshold=0.40,
        description=(
            "Arabic to Old Norse: balanced Germanic profile; þ/ð preserved, "
            "z>r rhotacism handled, Grimm's Law stop series applied."
        ),
    ),

    # Arabic to Welsh — moderate form weight; Welsh keeps PIE *p (unlike Old Irish)
    # but has a complex mutation system (soft/nasal/aspirate) that shifts initial
    # consonants. Balanced between Old English and Old Irish profiles.
    "ara_welsh": ScoringProfile(
        name="ara_welsh",
        semantic_weight=0.55,
        form_weight=0.45,
        phonetic_law_cap=0.15,
        genome_cap=0.10,
        multi_method_cap=0.12,
        cross_pair_cap=0.08,
        root_quality_cap=0.08,
        prefilter_threshold=0.40,
        final_threshold=0.40,
        description=(
            "Arabic to Welsh: balanced weights; Welsh keeps PIE *p but has "
            "soft/nasal/aspirate mutation system that shifts initial consonants."
        ),
    ),
}


def get_profile(name: str) -> ScoringProfile:
    """Return a named ScoringProfile.

    Parameters
    ----------
    name:
        Profile name as defined in PROFILES. Falls back to 'ara_eng_default'
        if the name is not found, emitting a warning.

    Returns
    -------
    ScoringProfile
    """
    if name in PROFILES:
        return PROFILES[name]
    import warnings
    warnings.warn(
        f"Unknown scoring profile {name!r}. Falling back to 'ara_eng_default'.",
        stacklevel=2,
    )
    return PROFILES["ara_eng_default"]


# ---------------------------------------------------------------------------
# Language-pair routing
# ---------------------------------------------------------------------------

_PAIR_TO_PROFILE: dict[tuple[str, str], str] = {
    ("ara", "ang"): "ara_old_english",
    ("ara", "enm"): "ara_middle_english",
    ("ara", "lat"): "ara_classical_ie",
    ("ara", "grc"): "ara_classical_ie",
    ("ara", "eng"): "ara_eng_default",
    ("ara", "got"): "ara_gothic",
    ("ara", "sga"): "ara_old_irish",
    ("ara", "non"): "ara_old_norse",
    ("ara", "cy"):  "ara_welsh",
}


def get_profile_for_pair(source_lang: str, target_lang: str) -> str:
    """Return the profile name for a (source_lang, target_lang) pair.

    Parameters
    ----------
    source_lang:
        ISO 639-3 / BCP-47 language code for the source language (e.g. "ara").
    target_lang:
        ISO 639-3 / BCP-47 language code for the target language (e.g. "ang").

    Returns
    -------
    str
        Profile name suitable for passing to :func:`get_profile`.
        Falls back to ``"ara_eng_default"`` for unrecognised pairs.
    """
    return _PAIR_TO_PROFILE.get((source_lang, target_lang), "ara_eng_default")
