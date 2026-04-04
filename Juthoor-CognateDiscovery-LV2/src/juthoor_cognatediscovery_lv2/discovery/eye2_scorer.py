"""Eye 2 LLM semantic scorer — loads pre-computed semantic scores.

Provides a lazy-loaded cache of LLM-annotated semantic similarity scores for
(source_lemma, target_lemma) pairs. When an Eye 2 score exists for a pair,
it replaces the gloss-based Jaccard score in the scoring pipeline.
"""
from __future__ import annotations

import json

from juthoor_cognatediscovery_lv2.discovery.artifact_paths import (
    eye2_eng_scores_path,
    eye2_scores_path,
)

_eye2_cache: dict[tuple[str, str], float] | None = None


def _load_eye2_scores() -> dict[tuple[str, str], float]:
    """Lazy-load Eye 2 scores from JSONL files.

    Key = (source_lemma, target_lemma). Source lemma is stripped of leading/
    trailing whitespace; target lemma is lowercased and stripped.
    """
    global _eye2_cache
    if _eye2_cache is not None:
        return _eye2_cache
    _eye2_cache = {}
    for path_fn in [eye2_scores_path, eye2_eng_scores_path]:
        path = path_fn()
        if not path.exists():
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                key = (obj["source_lemma"].strip(), obj["target_lemma"].lower().strip())
                _eye2_cache[key] = float(obj["semantic_score"])
    return _eye2_cache


def eye2_semantic_score(source_lemma: str, target_lemma: str) -> float | None:
    """Return pre-computed Eye 2 score for a pair, or None if not available.

    Parameters
    ----------
    source_lemma:
        The Arabic (source) lemma string.
    target_lemma:
        The target-language lemma string.

    Returns
    -------
    float | None
        A score in [0.0, 1.0], or None when no Eye 2 annotation exists for
        this pair. Callers should fall through to gloss-based scoring when
        None is returned.
    """
    cache = _load_eye2_scores()
    key = (source_lemma.strip(), target_lemma.lower().strip())
    return cache.get(key)
