"""Scholar divergence analysis for LV1 letter meanings.

Quantifies agreement and disagreement across 5 scholars per letter.
Used to identify which letters have strongest/weakest cross-scholar support.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from juthoor_arabicgenome_lv1.factory.scoring import _canonicalize


# ---------------------------------------------------------------------------
# Core divergence computation
# ---------------------------------------------------------------------------

def compute_letter_divergence(
    scholar_letters: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """For each letter, compute divergence metrics across all scholars.

    Parameters
    ----------
    scholar_letters:
        Mapping of scholar -> letter -> payload.  Each payload is expected to
        have an ``"atomic_features"`` key (sequence of Arabic feature strings).
        Scholars whose name starts with ``"consensus"`` are skipped.

    Returns
    -------
    list[dict[str, Any]]
        One dict per letter, sorted by ``agreement_score`` descending:

        ``letter``
            The Arabic letter.
        ``scholars_covering``
            Sorted list of scholar names that provided a reading for this letter.
        ``n_scholars``
            Number of scholars covering this letter.
        ``all_features``
            Mapping of (canonical) feature -> list of scholars that mention it.
        ``shared_features``
            Features mentioned by 2 or more scholars (after canonicalization).
        ``unique_features``
            Per-scholar dict of features mentioned by *only* that scholar.
        ``agreement_score``
            ``len(shared_features) / len(all_unique_features)`` — 0.0 if no
            features exist, 1.0 if all features are shared.
        ``classification``
            ``"STRONG"`` if ≥2 shared features, ``"PARTIAL"`` if exactly 1,
            ``"DIVERGE"`` if 0.
    """
    # Collect per-letter data, skipping consensus scholars
    by_letter: dict[str, dict[str, frozenset[str]]] = defaultdict(dict)
    for scholar, letters in scholar_letters.items():
        if scholar.startswith("consensus"):
            continue
        for letter, payload in letters.items():
            raw = payload.get("atomic_features") or ()
            by_letter[letter][scholar] = _canonicalize(tuple(raw))

    results: list[dict[str, Any]] = []
    for letter, scholar_feats in by_letter.items():
        scholars_covering = sorted(scholar_feats.keys())

        # feature -> list of scholars that mention it
        feature_support: dict[str, list[str]] = defaultdict(list)
        for scholar in scholars_covering:
            for feat in scholar_feats[scholar]:
                feature_support[feat].append(scholar)

        all_features: dict[str, list[str]] = {
            feat: sorted(scholars) for feat, scholars in sorted(feature_support.items())
        }

        shared_features: list[str] = sorted(
            feat for feat, scholars in feature_support.items() if len(scholars) >= 2
        )

        unique_features: dict[str, list[str]] = {}
        for scholar in scholars_covering:
            solo = sorted(
                feat
                for feat in scholar_feats[scholar]
                if len(feature_support[feat]) == 1
            )
            if solo:
                unique_features[scholar] = solo

        total_unique = len(all_features)
        agreement_score = (
            round(len(shared_features) / total_unique, 6) if total_unique else 0.0
        )

        n_shared = len(shared_features)
        if n_shared >= 2:
            classification = "STRONG"
        elif n_shared == 1:
            classification = "PARTIAL"
        else:
            classification = "DIVERGE"

        results.append(
            {
                "letter": letter,
                "scholars_covering": scholars_covering,
                "n_scholars": len(scholars_covering),
                "all_features": all_features,
                "shared_features": shared_features,
                "unique_features": unique_features,
                "agreement_score": agreement_score,
                "classification": classification,
            }
        )

    results.sort(key=lambda r: r["agreement_score"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# Scholar accuracy vs. empirical ground truth
# ---------------------------------------------------------------------------

def scholar_accuracy_vs_empirical(
    scholar_letters: dict[str, dict[str, dict[str, Any]]],
    empirical_meanings: dict[str, list[str]],
) -> dict[str, dict[str, Any]]:
    """Compare each scholar's features against empirical derivations.

    A scholar feature is counted as:

    * ``"confirmed"`` — its canonical form is in the canonicalized empirical set.
    * ``"wrong"``     — it is not present and not a synonym of anything empirical.

    (``"partial"`` is reserved for future category-level matching; currently
    always 0.)

    Parameters
    ----------
    scholar_letters:
        Same shape as in :func:`compute_letter_divergence`.
    empirical_meanings:
        Mapping of letter -> list of empirically-derived feature strings.

    Returns
    -------
    dict[str, dict[str, Any]]
        Per-scholar summary::

            {
                "jabal": {
                    "confirmed": 22,
                    "partial": 0,
                    "wrong": 3,
                    "total": 25,
                    "accuracy": 0.88,
                },
                ...
            }
    """
    # Pre-canonicalize empirical meanings per letter
    empirical_canon: dict[str, frozenset[str]] = {
        letter: _canonicalize(tuple(feats))
        for letter, feats in empirical_meanings.items()
    }

    tally: dict[str, dict[str, int]] = defaultdict(lambda: {"confirmed": 0, "partial": 0, "wrong": 0, "total": 0})

    for scholar, letters in scholar_letters.items():
        if scholar.startswith("consensus"):
            continue
        for letter, payload in letters.items():
            raw = payload.get("atomic_features") or ()
            scholar_canon = _canonicalize(tuple(raw))
            emp = empirical_canon.get(letter, frozenset())
            for feat in scholar_canon:
                tally[scholar]["total"] += 1
                if feat in emp:
                    tally[scholar]["confirmed"] += 1
                else:
                    tally[scholar]["wrong"] += 1

    result: dict[str, dict[str, Any]] = {}
    for scholar, counts in tally.items():
        total = counts["total"]
        accuracy = round(counts["confirmed"] / total, 6) if total else 0.0
        result[scholar] = {
            "confirmed": counts["confirmed"],
            "partial": counts["partial"],
            "wrong": counts["wrong"],
            "total": total,
            "accuracy": accuracy,
        }
    return result


# ---------------------------------------------------------------------------
# Convenience ranking helpers
# ---------------------------------------------------------------------------

def most_disputed_letters(
    divergence: list[dict[str, Any]],
    *,
    n: int = 10,
) -> list[dict[str, Any]]:
    """Return the N most disputed letters (lowest ``agreement_score`` first)."""
    sorted_asc = sorted(divergence, key=lambda r: r["agreement_score"])
    return sorted_asc[:n]


def most_agreed_letters(
    divergence: list[dict[str, Any]],
    *,
    n: int = 10,
) -> list[dict[str, Any]]:
    """Return the N most agreed-upon letters (highest ``agreement_score`` first)."""
    sorted_desc = sorted(divergence, key=lambda r: r["agreement_score"], reverse=True)
    return sorted_desc[:n]
