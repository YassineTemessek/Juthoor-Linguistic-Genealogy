"""Concept-level semantic matcher using structured concept definitions.

Uses the concepts_v3_2_enriched.jsonl file to find direct and indirect
(figurative / category-level) semantic relationships between Arabic and
English lexeme entries, without any neural embeddings.

Scoring logic
--------------
1.0  — direct concept match  (both entries resolve to the same concept_id)
0.3  — same category match   (both entries resolve to concepts in same category)
0.0  — no match found
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


_WORD_RE = re.compile(r"[a-z]{3,}")

_STOPWORDS = frozenset({
    "a", "an", "the", "of", "in", "to", "for", "and", "or", "is", "it",
    "at", "by", "on", "as", "be", "was", "are", "were", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "can", "could", "not", "no", "but", "if",
    "so", "than", "that", "this", "with", "from", "into", "about",
})


def _content_words(text: str) -> set[str]:
    words = set(_WORD_RE.findall(text.lower()))
    return words - _STOPWORDS


class ConceptMatcher:
    """Lightweight concept-level semantic matcher.

    Builds reverse indexes from word tokens to concept IDs so that any
    lexeme entry can be mapped to one or more concept IDs, then compares
    those concept IDs (or their categories) for a structured similarity
    score.

    Parameters
    ----------
    path:
        Path to ``concepts_v3_2_enriched.jsonl``.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._loaded = False

        # concept_id → concept record
        self._concepts: dict[str, dict] = {}
        # concept_id → category string
        self._category: dict[str, str] = {}

        # Reverse indexes: normalised English token → set of concept IDs
        self._en_token_index: dict[str, set[str]] = defaultdict(set)
        # Reverse indexes: Arabic form token → set of concept IDs
        self._ar_token_index: dict[str, set[str]] = defaultdict(set)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._load()
        self._loaded = True

    def _load(self) -> None:
        if not self._path.exists():
            # Graceful degradation — empty indexes, concept_similarity → 0.0
            return

        with self._path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec: dict = json.loads(line)
                cid: str = rec["concept_id"]
                self._concepts[cid] = rec
                self._category[cid] = rec.get("category", "")

                # Index English tokens from core_gloss_en + synonyms_en + meronyms
                en_tokens = _content_words(rec.get("core_gloss_en", ""))
                for syn in rec.get("synonyms_en", []):
                    en_tokens |= _content_words(syn)
                for mer in rec.get("meronyms", []):
                    en_tokens |= _content_words(mer)
                for tok in en_tokens:
                    self._en_token_index[tok].add(cid)

                # Index Arabic forms from figurative_links
                for link in rec.get("figurative_links", []):
                    form = link.get("form", "")
                    gloss = link.get("gloss", "")
                    if form:
                        for tok in _content_words(form):
                            self._ar_token_index[tok].add(cid)
                    if gloss:
                        for tok in _content_words(gloss):
                            self._en_token_index[tok].add(cid)

    def _entry_to_en_tokens(self, entry: dict[str, Any]) -> set[str]:
        """Extract English content words from a lexeme entry dict."""
        parts: list[str] = []
        for field in ("gloss", "short_gloss", "meaning_text", "english_gloss",
                      "definition", "core_gloss_en"):
            val = entry.get(field)
            if val:
                parts.append(str(val))
        # word form itself
        for field in ("word", "lemma", "form"):
            val = entry.get(field)
            if val:
                parts.append(str(val))
        return _content_words(" ".join(parts))

    def _entry_to_concept_ids(self, entry: dict[str, Any]) -> set[str]:
        """Map a lexeme entry to zero or more concept IDs via the indexes."""
        self._ensure_loaded()
        tokens = self._entry_to_en_tokens(entry)
        result: set[str] = set()
        for tok in tokens:
            result |= self._en_token_index.get(tok, set())
        return result

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def concept_count(self) -> int:
        """Number of concepts loaded."""
        self._ensure_loaded()
        return len(self._concepts)

    @property
    def en_index_size(self) -> int:
        """Number of distinct English tokens in the reverse index."""
        self._ensure_loaded()
        return len(self._en_token_index)

    @property
    def ar_index_size(self) -> int:
        """Number of distinct Arabic-form tokens in the reverse index."""
        self._ensure_loaded()
        return len(self._ar_token_index)

    def concept_similarity(
        self,
        arabic_entry: dict[str, Any],
        english_entry: dict[str, Any],
    ) -> float:
        """Return a structured concept similarity score.

        Parameters
        ----------
        arabic_entry:
            Dict representing an Arabic lexeme (may include ``english_gloss``,
            ``root``, ``gloss``, ``meaning_text``, etc.).
        english_entry:
            Dict representing an English lexeme (may include ``gloss``,
            ``short_gloss``, ``word``, etc.).

        Returns
        -------
        float
            1.0  — direct concept match (shared concept_id)
            0.3  — same-category match
            0.0  — no match
        """
        self._ensure_loaded()

        ar_cids = self._entry_to_concept_ids(arabic_entry)
        en_cids = self._entry_to_concept_ids(english_entry)

        if not ar_cids or not en_cids:
            return 0.0

        # Direct match
        if ar_cids & en_cids:
            return 1.0

        # Same-category match
        ar_cats = {self._category.get(c, "") for c in ar_cids} - {""}
        en_cats = {self._category.get(c, "") for c in en_cids} - {""}
        if ar_cats & en_cats:
            return 0.3

        return 0.0
