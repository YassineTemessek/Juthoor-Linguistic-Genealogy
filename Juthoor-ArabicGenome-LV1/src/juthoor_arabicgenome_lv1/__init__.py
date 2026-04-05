"""
Juthoor Arabic Genome (LV1)

Decodes the Arabic root system:
- Phase 1: Group Arabic lexemes by BAB → binary root → triconsonantal root → words
- Phase 2: Overlay Muajam Ishtiqaqi meanings (letter → binary root → axial meanings)
- Phase 3: Semantic validation of binary root ↔ word meaning connections
"""

from juthoor_arabicgenome_lv1.core import (
    Letter,
    BinaryRoot,
    TriliteralRoot,
    RootFamily,
    load_letters,
    load_binary_roots,
    load_triliteral_roots,
    load_root_families,
    load_genome_v2,
)
from juthoor_arabicgenome_lv1.factory.sound_laws import (
    LATIN_EQUIVALENTS,
    KHASHIM_SOUND_LAWS,
    normalize_arabic_root,
    project_root_sound_laws,
    project_root_by_target,
)

__all__ = [
    "Letter",
    "BinaryRoot",
    "TriliteralRoot",
    "RootFamily",
    "load_letters",
    "load_binary_roots",
    "load_triliteral_roots",
    "load_root_families",
    "load_genome_v2",
    "LATIN_EQUIVALENTS",
    "KHASHIM_SOUND_LAWS",
    "normalize_arabic_root",
    "project_root_sound_laws",
    "project_root_by_target",
]