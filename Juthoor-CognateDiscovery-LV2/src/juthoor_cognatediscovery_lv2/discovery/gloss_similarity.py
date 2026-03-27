"""Lightweight semantic similarity via gloss word overlap.

No GPU required. Uses Jaccard similarity on gloss words as a proxy for
semantic relatedness. This is much weaker than BGE-M3 embeddings but
provides SOME semantic filtering to distinguish real cognates from
random consonant overlaps.
"""
from __future__ import annotations
import re
from typing import Any

_STOPWORDS = frozenset({
    "a", "an", "the", "of", "in", "to", "for", "and", "or", "is", "it",
    "at", "by", "on", "as", "be", "was", "are", "were", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "can", "could", "not", "no", "but", "if",
    "so", "than", "that", "this", "with", "from", "into", "about", "up",
    "out", "very", "also", "just", "more", "most", "other", "some", "such",
    "only", "over", "any", "each", "all", "both", "few", "many", "much",
})

_WORD_RE = re.compile(r"[a-z]{3,}")


def _extract_content_words(text: str) -> set[str]:
    """Extract content words (non-stopwords, 3+ chars) from text."""
    words = set(_WORD_RE.findall(text.lower()))
    return words - _STOPWORDS


def gloss_similarity(source: dict[str, Any], target: dict[str, Any]) -> float:
    """Compute Jaccard similarity between source and target glosses.

    Returns 0.0-1.0. Uses meaning_text, gloss, gloss_plain, short_gloss fields.
    """
    src_text = " ".join(filter(None, [
        str(source.get("meaning_text", "") or ""),
        str(source.get("gloss", "") or ""),
        str(source.get("short_gloss", "") or ""),
        str(source.get("gloss_plain", "") or ""),
    ]))
    tgt_text = " ".join(filter(None, [
        str(target.get("meaning_text", "") or ""),
        str(target.get("gloss", "") or ""),
        str(target.get("short_gloss", "") or ""),
        str(target.get("gloss_plain", "") or ""),
    ]))

    src_words = _extract_content_words(src_text)
    tgt_words = _extract_content_words(tgt_text)

    if not src_words or not tgt_words:
        return 0.0

    intersection = src_words & tgt_words
    union = src_words | tgt_words

    return len(intersection) / len(union) if union else 0.0


def has_semantic_overlap(source: dict[str, Any], target: dict[str, Any], min_overlap: float = 0.05) -> bool:
    """Quick check: do source and target share any meaning words?"""
    return gloss_similarity(source, target) >= min_overlap
