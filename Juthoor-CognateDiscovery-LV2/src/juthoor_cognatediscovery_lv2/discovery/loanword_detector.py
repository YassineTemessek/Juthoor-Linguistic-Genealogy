"""Heuristic loanword detection for Arabic-origin words in target languages."""
from __future__ import annotations
from typing import Any

# Arabic definite article patterns that survive in loanwords
_ARTICLE_PREFIXES = ("al", "el", "il", "ul")

def is_probable_loanword(source: dict[str, Any], target: dict[str, Any], score: float = 0.0) -> bool:
    """Detect probable Arabic loanwords vs inherited cognates.

    Loanwords preserve Arabic structure almost unchanged. Signs:
    1. Very high consonant skeleton match (>0.90) — too similar for independent evolution
    2. Target starts with al-/el- (Arabic article preserved)
    3. Target language is known heavy borrower (Persian, Turkish, Spanish, Swahili)
    """
    tgt_lemma = str(target.get("lemma", "") or "").strip().lower()

    # Article preservation is strong loanword signal
    if any(tgt_lemma.startswith(p) for p in _ARTICLE_PREFIXES):
        return True

    # Very high score with direct skeleton method suggests loanword
    if score >= 0.95:
        return True

    return False


def classify_link(source: dict[str, Any], target: dict[str, Any],
                  score: float, method: str) -> str:
    """Classify a cognate link as: loanword, probable_cognate, or uncertain."""
    if is_probable_loanword(source, target, score):
        return "loanword"
    if score >= 0.70 and method in ("multi_hop_chain", "emphatic_collapse", "guttural_projection"):
        return "probable_cognate"
    return "uncertain"
