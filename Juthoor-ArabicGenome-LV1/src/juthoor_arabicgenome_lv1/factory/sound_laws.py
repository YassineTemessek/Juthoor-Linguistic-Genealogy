from __future__ import annotations

import itertools
import re
from collections import OrderedDict


ARABIC_NORMALIZE_MAP = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ؤ": "و",
        "ئ": "ي",
        "ى": "ي",
        "ة": "ه",
    }
)

ARABIC_CONSONANT_RE = re.compile(r"[\u0621-\u064A]")


KHASHIM_SOUND_LAWS: dict[str, tuple[str, ...]] = {
    "ف": ("f", "p"),
    "ق": ("q", "c", "k", "g"),
    "ط": ("ṭ", "t"),
    "ص": ("ṣ", "s"),
    "ش": ("sh", "s"),
    "ح": ("ḥ", "k", "c", "h"),
    "ع": ("ʕ", "", "h"),
    "غ": ("gh", "g"),
    "خ": ("kh", "h", "g"),
}


PHONETIC_SUCCESSION_GROUPS: dict[str, tuple[str, ...]] = {
    "labials": ("ب", "م", "ف", "و"),
    "sibilants": ("س", "ز", "ص", "ش"),
    "dentals": ("ت", "د", "ط"),
    "liquidals": ("ل", "ن", "ر"),
    "gutturals": ("ع", "ح", "غ", "خ", "ه", "ا"),
    "velars": ("ق", "ك", "ج"),
}

LATIN_EQUIVALENTS: dict[str, tuple[str, ...]] = {
    "ا": ("a", ""),
    "أ": ("a", ""),
    "ء": ("", "a"),
    "ب": ("b", "p"),
    "ت": ("t",),
    "ث": ("th", "s"),
    "ج": ("j", "g", "c"),
    "ح": ("ḥ", "h"),
    "خ": ("kh", "h", "g"),
    "د": ("d", "t"),
    "ذ": ("dh", "z", "d"),
    "ر": ("r",),
    "ز": ("z", "s"),
    "س": ("s",),
    "ش": ("sh", "s"),
    "ص": ("ṣ", "s"),
    "ض": ("ḍ", "d"),
    "ط": ("ṭ", "t"),
    "ظ": ("ẓ", "z"),
    "ع": ("ʕ", "h", ""),
    "غ": ("gh", "g"),
    "ك": ("k", "c"),
    "ق": ("q", "k", "c", "g"),
    "ل": ("l",),
    "م": ("m",),
    "ن": ("n",),
    "ه": ("h",),
    "و": ("w", "v", "u"),
    "ي": ("y", "i"),
}


def normalize_arabic_root(root: str) -> str:
    normalized = root.translate(ARABIC_NORMALIZE_MAP)
    letters = ARABIC_CONSONANT_RE.findall(normalized)
    return "".join(letters)


def succession_group(letter: str) -> str | None:
    normalized = normalize_arabic_root(letter)
    if not normalized:
        return None
    char = normalized[0]
    for group_name, members in PHONETIC_SUCCESSION_GROUPS.items():
        if char in members:
            return group_name
    return None


def are_in_same_succession_group(letter_a: str, letter_b: str) -> bool:
    group_a = succession_group(letter_a)
    group_b = succession_group(letter_b)
    return bool(group_a and group_a == group_b)


def substitution_options(letter: str, include_group_expansion: bool = True) -> tuple[str, ...]:
    normalized = normalize_arabic_root(letter)
    if not normalized:
        return ("",)

    char = normalized[0]
    ordered: OrderedDict[str, None] = OrderedDict()

    for candidate in KHASHIM_SOUND_LAWS.get(char, ()):
        ordered[candidate] = None

    for candidate in LATIN_EQUIVALENTS.get(char, ()):
        ordered[candidate] = None

    if include_group_expansion:
        group_name = succession_group(char)
        if group_name:
            for sibling in PHONETIC_SUCCESSION_GROUPS[group_name]:
                for candidate in KHASHIM_SOUND_LAWS.get(sibling, ()):
                    ordered[candidate] = None
                for candidate in LATIN_EQUIVALENTS.get(sibling, ()):
                    ordered[candidate] = None

    if not ordered:
        ordered[char] = None

    return tuple(ordered.keys())


def project_root_sound_laws(
    root: str,
    *,
    include_group_expansion: bool = False,
    max_variants: int = 128,
) -> tuple[str, ...]:
    normalized = normalize_arabic_root(root)
    if not normalized:
        return ()

    option_lists = [
        substitution_options(letter, include_group_expansion=include_group_expansion)
        for letter in normalized
    ]

    variants: OrderedDict[str, None] = OrderedDict()
    for combination in itertools.product(*option_lists):
        variant = "".join(combination)
        if variant:
            variants[variant] = None
        if len(variants) >= max_variants:
            break

    return tuple(variants.keys())


def project_root_by_target(root: str, target_family: str) -> tuple[str, ...]:
    family = target_family.lower()
    if family in {"hebrew", "aramaic", "semitic"}:
        return project_root_sound_laws(root, include_group_expansion=True, max_variants=96)
    if family in {"english", "latin", "greek", "european", "indo_european"}:
        return project_root_sound_laws(root, include_group_expansion=True, max_variants=128)
    return project_root_sound_laws(root, include_group_expansion=False, max_variants=64)
