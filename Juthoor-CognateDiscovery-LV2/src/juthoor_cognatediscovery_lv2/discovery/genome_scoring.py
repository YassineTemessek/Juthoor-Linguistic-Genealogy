"""Genome-informed scoring using LV1 Research Factory promoted outputs.

Loads field coherence scores, metathesis pairs, and positional profiles
from LV1's promotion gateway and provides scoring functions for the
cognate discovery pipeline.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# Resolve promoted outputs relative to the monorepo root.
# Path depth from this file to repo root:
#   parents[0] = discovery/
#   parents[1] = juthoor_cognatediscovery_lv2/
#   parents[2] = src/
#   parents[3] = Juthoor-CognateDiscovery-LV2/
#   parents[4] = repo root (Juthoor-Linguistic-Genealogy/)
_REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_PROMOTED_DIR = _REPO_ROOT / "outputs" / "research_factory" / "promoted"

# Arabic + Hebrew normalization to a shared Semitic comparison space.
_NORMALIZE_MAP = str.maketrans(
    {
        "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ؤ": "و", "ئ": "ي", "ة": "ه",
        "ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ",
    }
)
_SEMITIC_RE = re.compile(r"[\u0621-\u064A\u05D0-\u05EA]")
_LETTER_CLASS = {
    "ا": "ʔ", "א": "ʔ",
    "ب": "b", "ב": "b",
    "ت": "t", "ט": "t", "ת": "t",
    "ث": "s", "س": "s", "ش": "s", "ש": "s", "ס": "s",
    "ج": "g", "ג": "g",
    "ح": "ḥ", "ח": "ḥ",
    "خ": "ḫ", "כ": "ḫ",
    "د": "d", "ד": "d",
    "ذ": "z", "ز": "z", "ז": "z",
    "ر": "r", "ר": "r",
    "ص": "ṣ", "צ": "ṣ",
    "ض": "ḍ",
    "ط": "ṭ",
    "ظ": "ẓ",
    "ع": "ʕ", "ע": "ʕ",
    "غ": "ġ",
    "ف": "f", "פ": "f",
    "ق": "q", "ק": "q",
    "ك": "k",
    "ل": "l", "ל": "l",
    "م": "m", "מ": "m",
    "ن": "n", "נ": "n",
    "ه": "h", "ה": "h",
    "و": "w", "ו": "w",
    "ي": "y", "י": "y",
}


def _extract_binary_root(root: str) -> str | None:
    """Extract the first two Semitic consonant classes from a root or lemma."""
    letters = _SEMITIC_RE.findall(root.translate(_NORMALIZE_MAP))
    classes = [_LETTER_CLASS.get(ch, ch) for ch in letters]
    if len(classes) >= 2:
        return "".join(classes[:2])
    return None


class GenomeScorer:
    """Scores cognate candidates using LV1 genome data."""

    def __init__(self, promoted_dir: Path | None = None):
        self._dir = promoted_dir or _DEFAULT_PROMOTED_DIR
        self._coherence: dict[str, float] = {}
        self._metathesis_set: set[tuple[str, str]] = set()
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        features_dir = self._dir / "promoted_features"

        # Load field coherence scores
        coherence_path = features_dir / "field_coherence_scores.jsonl"
        if coherence_path.exists():
            for line in coherence_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                br = row.get("binary_root", "")
                score = row.get("coherence")
                if br and score is not None:
                    self._coherence[br] = float(score)

        # Load metathesis pairs
        metathesis_path = features_dir / "metathesis_pairs.jsonl"
        if metathesis_path.exists():
            for line in metathesis_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                a = row.get("binary_root_a", "")
                b = row.get("binary_root_b", "")
                if a and b:
                    self._metathesis_set.add((a, b))
                    self._metathesis_set.add((b, a))

        self._loaded = True

    def root_coherence_score(self, root: str) -> float | None:
        """Return the field coherence score for a root's binary nucleus.

        Extracts the first two Arabic consonants from ``root``, then looks
        up the pre-computed coherence score from LV1's field_coherence_scores
        promoted feature.  Returns ``None`` if the binary nucleus is not found
        in the loaded data.
        """
        self._ensure_loaded()
        br = _extract_binary_root(root)
        if br is None:
            return None
        return self._coherence.get(br)

    def is_metathesis_pair(self, root1: str, root2: str) -> bool:
        """Check if two roots share a metathesized binary nucleus.

        Returns ``True`` when the binary nuclei of ``root1`` and ``root2``
        appear as a pair in LV1's promoted metathesis_pairs feature (order
        independent).
        """
        self._ensure_loaded()
        br1 = _extract_binary_root(root1)
        br2 = _extract_binary_root(root2)
        if br1 is None or br2 is None:
            return False
        return (br1, br2) in self._metathesis_set

    def genome_bonus(self, source_entry: dict, target_entry: dict) -> float:
        """Compute a genome-informed bonus for a candidate pair.

        Components:
        1. Exact shared binary Semitic nucleus: +0.08
        2. High-coherence Arabic family for an exact binary match (>0.6): +0.05
        3. Metathesis relation between binary nuclei: +0.05
        4. High-coherence Arabic family for a metathesis relation: +0.03

        Returns: float in [0.0, 0.13]
        """
        self._ensure_loaded()
        bonus = 0.0

        source_root = source_entry.get("root_norm") or source_entry.get("root", "")
        target_root = target_entry.get("root_norm") or target_entry.get("root", "")
        if not source_root:
            source_root = source_entry.get("lemma", "")
        if not target_root:
            target_root = target_entry.get("lemma", "")

        if not source_root or not target_root:
            return bonus

        source_binary = _extract_binary_root(source_root)
        target_binary = _extract_binary_root(target_root)
        coherence = self.root_coherence_score(source_root)

        if source_binary and target_binary and source_binary == target_binary:
            bonus += 0.08
            if coherence is not None and coherence > 0.6:
                bonus += 0.05
        elif self.is_metathesis_pair(source_root, target_root):
            bonus += 0.05
            if coherence is not None and coherence > 0.6:
                bonus += 0.03

        return bonus
