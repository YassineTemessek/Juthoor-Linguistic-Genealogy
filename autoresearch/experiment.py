"""
experiment.py — THE MUTABLE FILE

The autoresearch agent edits this file each iteration.
prepare.py imports EXPERIMENT_CONFIG and uses it for scoring.

Rules:
  - Only modify values inside ExperimentConfig.
  - Do not add imports or executable code.
  - class_map and hamza_map are dicts; edit entries freely.
  - See program.md for constraints and strategy hints.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExperimentConfig:
    """All tunable parameters for one experiment iteration."""

    # ---- Hybrid weights (should sum to ~1.0) ----
    semantic_weight: float = 0.55
    form_weight: float = 0.45

    # ---- Bonus caps ----
    phonetic_law_cap: float = 0.15
    genome_cap: float = 0.10
    multi_method_cap: float = 0.12
    cross_pair_cap: float = 0.10
    root_quality_cap: float = 0.08

    # ---- Thresholds ----
    prefilter_threshold: float = 0.50
    final_threshold: float = 0.45
    null_threshold: float = 0.30  # count-above threshold for z-score

    # ---- Correspondence bonus coefficients ----
    correspondence_coeff: float = 0.12
    hamza_coeff: float = 0.04
    weak_radical_coeff: float = 0.05
    correspondence_cap: float = 0.21  # max total correspondence bonus

    # ---- Normalization: weak radicals ----
    weak_radicals_ar: str = "اويى"
    weak_radicals_lat: str = "aeiouy"

    # ---- Class map and hamza map are set via __post_init__ ----

    def __post_init__(self):
        # Correspondence class map: character → abstract phonetic class
        object.__setattr__(self, "class_map", {
            # Arabic consonants
            "ب": "B", "ف": "B", "پ": "B",
            "م": "M",
            "ت": "T", "ط": "T", "ث": "T", "د": "T", "ض": "T", "ذ": "T", "ظ": "T",
            "س": "S", "ص": "S", "ز": "S", "ش": "S", "ج": "S",
            "ر": "R", "ل": "R", "ن": "R",
            "ك": "K", "ق": "K", "گ": "K",
            "و": "W", "ي": "W", "ى": "W",
            "ء": "A", "ا": "A", "أ": "A", "إ": "A", "آ": "A", "ٱ": "A",
            "ه": "H", "ح": "H", "خ": "H",
            "ع": "E", "غ": "E",
            # Latin / IPA consonants
            "b": "B", "f": "B", "v": "B", "p": "B",
            "m": "M",
            "t": "T", "d": "T", "ṭ": "T", "ḍ": "T", "ð": "T", "θ": "T", "ẓ": "T",
            "s": "S", "z": "S", "c": "S", "j": "S", "g": "S",
            "š": "S", "ṣ": "S", "ʃ": "S", "ʒ": "S",
            "r": "R", "l": "R", "n": "R",
            "k": "K", "q": "K",
            "w": "W", "y": "W",
            "h": "H", "ḥ": "H", "ḫ": "H", "x": "H",
            "ʕ": "E", "ġ": "E", "ɣ": "E",
            "ʔ": "A",
            # Greek-specific (add/adjust as needed)
            "φ": "B",   # phi ~ labial
            "χ": "H",   # chi ~ guttural
            "ψ": "B",   # psi = p+s, map to labial component
            "ξ": "K",   # xi = k+s, map to velar component
        })

        # Hamza normalization map
        object.__setattr__(self, "hamza_map", {
            "أ": "ا",
            "إ": "ا",
            "آ": "ا",
            "ٱ": "ا",
            "ؤ": "و",
            "ئ": "ي",
            "ء": "ا",
        })


EXPERIMENT_CONFIG = ExperimentConfig()
