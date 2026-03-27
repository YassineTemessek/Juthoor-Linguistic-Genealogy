"""Root quality scoring backed by LV1 meaning-predictor outputs."""
from __future__ import annotations

import json
from pathlib import Path

# Path depth from this file to repo root:
#   parents[0] = discovery/
#   parents[1] = juthoor_cognatediscovery_lv2/
#   parents[2] = src/
#   parents[3] = Juthoor-CognateDiscovery-LV2/
#   parents[4] = repo root (Juthoor-Linguistic-Genealogy/)
_REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_PREDICTIONS_CANDIDATES = (
    _REPO_ROOT
    / "Juthoor-ArabicGenome-LV1"
    / "outputs"
    / "research_factory"
    / "axis6"
    / "meaning_predictor_predictions.jsonl",
    _REPO_ROOT / "outputs" / "research_factory" / "axis6" / "meaning_predictor_predictions.jsonl",
    _REPO_ROOT
    / "outputs"
    / "research_factory"
    / "promoted"
    / "promoted_features"
    / "meaning_predictor_predictions.jsonl",
)
_NORMALIZE_MAP = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
    }
)


def _normalize_root(root: str) -> str:
    return "".join(str(root or "").split()).translate(_NORMALIZE_MAP)


class RootQualityScorer:
    """Lookup cosine similarity for Arabic roots predicted by LV1."""

    def __init__(self, predictions_path: Path | None = None):
        self._predictions_path = predictions_path
        self._root_scores: dict[str, float] = {}
        self._loaded = False

    def _resolve_predictions_path(self) -> Path | None:
        if self._predictions_path is not None:
            return self._predictions_path
        for candidate in _DEFAULT_PREDICTIONS_CANDIDATES:
            if candidate.exists():
                return candidate
        return None

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        predictions_path = self._resolve_predictions_path()
        if predictions_path is None or not predictions_path.exists():
            self._loaded = True
            return

        for line in predictions_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            tri_root = str(row.get("tri_root") or "").strip()
            cosine = row.get("cosine_similarity")
            if not tri_root or cosine is None:
                continue

            score = float(cosine)
            variants = [tri_root]
            if "/" in tri_root:
                variants.extend(part for part in tri_root.split("/") if part)

            for variant in variants:
                normalized = _normalize_root(variant)
                if not normalized:
                    continue
                self._root_scores[normalized] = max(score, self._root_scores.get(normalized, 0.0))

        self._loaded = True

    def root_quality(self, root: str) -> float:
        """Return the LV1 prediction cosine for a known root, else 0.0."""
        self._ensure_loaded()
        normalized = _normalize_root(root)
        if not normalized:
            return 0.0
        return self._root_scores.get(normalized, 0.0)
