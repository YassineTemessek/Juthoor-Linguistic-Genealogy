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

# Arabic letter normalization (same as LV1)
_NORMALIZE_MAP = str.maketrans(
    {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ؤ": "و", "ئ": "ي", "ة": "ه"}
)
_ARABIC_RE = re.compile(r"[\u0621-\u064A]")  # Arabic letter range (bare consonants)


def _extract_binary_root(root: str) -> str | None:
    """Extract the first two Arabic consonants from a root string."""
    letters = _ARABIC_RE.findall(root.translate(_NORMALIZE_MAP))
    if len(letters) >= 2:
        return letters[0] + letters[1]
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
        1. If source root has a high-coherence family (>0.6): +0.05
           (roots from coherent families are more trustworthy anchors)
        2. If source and target share a metathesized binary root: +0.10
           (cross-lingual metathesis is a strong cognate signal)

        Returns: float in [0.0, 0.15]
        """
        self._ensure_loaded()
        bonus = 0.0

        # Component 1: root family coherence
        source_root = source_entry.get("root_norm") or source_entry.get("root", "")
        if source_root:
            coherence = self.root_coherence_score(source_root)
            if coherence is not None and coherence > 0.6:
                bonus += 0.05

        # Component 2: cross-lingual metathesis
        target_root = target_entry.get("root_norm") or target_entry.get("root", "")
        if source_root and target_root:
            if self.is_metathesis_pair(source_root, target_root):
                bonus += 0.10

        return bonus
