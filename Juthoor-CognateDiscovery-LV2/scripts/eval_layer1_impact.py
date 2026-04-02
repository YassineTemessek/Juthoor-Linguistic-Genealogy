"""A/B evaluation: measure Layer 1 morphology annotation impact on ara-lat skeleton matching.

Compares skeleton similarity scores on 244 ara-lat gold pairs with and without
Layer 1 LLM annotations loaded into target_morphology._layer1_cache.

Strategy
--------
1. For each gold pair, extract the Arabic consonant skeleton (Arabic Unicode
   chars, weak letters stripped).
2. Project each Arabic consonant to its primary Latin equivalent(s) using
   LATIN_EQUIVALENTS, producing a set of projected Latin chars.
3. For the target (Latin) word, extract all skeletons via extract_all_skeletons
   — once with empty cache (baseline) and once with Layer 1 annotations loaded.
4. Score: best Jaccard similarity between the Arabic projected char-set and any
   target skeleton char-set.

Usage (from repo root):
    python Juthoor-CognateDiscovery-LV2/scripts/eval_layer1_impact.py
"""
from __future__ import annotations

import sys
import json
import re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Path setup — allow running from repo root or from the scripts/ directory
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent
_LV2_ROOT = _SCRIPT_DIR.parent
_REPO_ROOT = _LV2_ROOT.parent

for _sub in (
    "Juthoor-CognateDiscovery-LV2/src",
    "Juthoor-ArabicGenome-LV1/src",
    "Juthoor-DataCore-LV0/src",
):
    _p = str(_REPO_ROOT / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import juthoor_cognatediscovery_lv2.discovery.target_morphology as tm
from juthoor_cognatediscovery_lv2.discovery.target_morphology import extract_all_skeletons

# Import the Arabic normaliser and LATIN_EQUIVALENTS from the phonetic law scorer
try:
    from juthoor_arabicgenome_lv1.factory.sound_laws import (
        normalize_arabic_root,
        LATIN_EQUIVALENTS,
    )
except ImportError:
    # Minimal inline fallback
    _HAMZA_NORM = str.maketrans(
        {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ؤ": "و", "ئ": "ي", "ى": "ي", "ة": "ه"}
    )
    _AR_CONS_RE = re.compile(r"[\u0621-\u064A]")

    def normalize_arabic_root(root: str) -> str:  # type: ignore[misc]
        return "".join(_AR_CONS_RE.findall(root.translate(_HAMZA_NORM)))

    LATIN_EQUIVALENTS: dict[str, tuple[str, ...]] = {  # type: ignore[misc]
        "ا": ("a", ""),
        "ب": ("b", "p"),
        "ت": ("t",),
        "ث": ("th", "s"),
        "ج": ("j", "g", "c"),
        "ح": ("h",),
        "خ": ("kh", "h", "g"),
        "د": ("d", "t"),
        "ذ": ("dh", "z", "d"),
        "ر": ("r",),
        "ز": ("z", "s"),
        "س": ("s",),
        "ش": ("sh", "s"),
        "ص": ("s",),
        "ض": ("d",),
        "ط": ("t",),
        "ظ": ("z",),
        "ع": ("", "h"),
        "غ": ("gh", "g"),
        "ف": ("f", "p"),
        "ق": ("q", "k", "c", "g"),
        "ك": ("k", "c"),
        "ل": ("l",),
        "م": ("m",),
        "ن": ("n",),
        "ه": ("h",),
        "و": ("w", "v", "u"),
        "ي": ("y", "i"),
    }

# ---------------------------------------------------------------------------
# Arabic-side skeleton: project Arabic consonants to Latin chars
# ---------------------------------------------------------------------------

_ARABIC_WEAK = frozenset("اويى")


def _arabic_consonant_chars(lemma: str) -> str:
    """Return the Arabic consonant skeleton (Arabic Unicode, weak letters stripped)."""
    norm = normalize_arabic_root(lemma)
    return "".join(ch for ch in norm if ch not in _ARABIC_WEAK)


def _project_arabic_to_latin_set(ara_skel: str) -> set[str]:
    """Project an Arabic consonant string to a set of Latin chars.

    For each Arabic consonant, take only its primary Latin equivalent(s)
    (first entry in LATIN_EQUIVALENTS).  Multi-char equivalents like "th" or
    "kh" are split into individual chars so set-based Jaccard works cleanly.
    """
    chars: set[str] = set()
    for ar_ch in ara_skel:
        equivs = LATIN_EQUIVALENTS.get(ar_ch, ())
        if equivs:
            primary = equivs[0]  # most likely Latin realisation
            for ch in primary:
                if ch.isalpha():
                    chars.add(ch)
    return chars


# ---------------------------------------------------------------------------
# Arabic diacritic / tatweel / trailing punctuation stripper
# ---------------------------------------------------------------------------

_ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4"
    r"\u06E7\u06E8\u06EA-\u06ED\u0640]"
)
_TRAILING_PUNCT = re.compile(r"[،,;:.،؟!]+$")


def _normalise_arabic(lemma: str) -> str:
    lemma = _ARABIC_DIACRITICS.sub("", lemma)
    lemma = _TRAILING_PUNCT.sub("", lemma)
    return lemma.strip()


# ---------------------------------------------------------------------------
# Skeleton similarity
# ---------------------------------------------------------------------------

def _target_skel_chars(skel: str) -> set[str]:
    """Return set of single chars from a target skeleton string."""
    return set(skel)


def skeleton_similarity(ara_latin_set: set[str], tgt_skels: list[str]) -> float:
    """Best Jaccard similarity between the Arabic projected Latin char-set
    and any target skeleton char-set."""
    if not ara_latin_set:
        return 0.0
    best = 0.0
    for t in tgt_skels:
        t_set = _target_skel_chars(t)
        if not t_set:
            continue
        union = ara_latin_set | t_set
        if not union:
            continue
        jaccard = len(ara_latin_set & t_set) / len(union)
        if jaccard > best:
            best = jaccard
    return best


# ---------------------------------------------------------------------------
# Gold pair loading
# ---------------------------------------------------------------------------

_GOLD_PATH = _LV2_ROOT / "resources" / "benchmarks" / "cognate_gold.jsonl"


def load_ara_lat_pairs() -> list[dict]:
    pairs = []
    with open(_GOLD_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj["source"]["lang"] == "ara" and obj["target"]["lang"] == "lat":
                pairs.append(obj)
    return pairs


# ---------------------------------------------------------------------------
# Cache control helpers
# ---------------------------------------------------------------------------

def _force_empty_cache() -> None:
    """Baseline mode: no Layer 1 annotations."""
    tm._layer1_cache = {}


def _force_reload_cache() -> None:
    """Layer1 mode: reload from disk on next call."""
    tm._layer1_cache = None


# ---------------------------------------------------------------------------
# Per-pair scoring
# ---------------------------------------------------------------------------

def score_pair(pair: dict) -> tuple[float, float]:
    """Return (baseline_score, layer1_score) for one gold pair."""
    ara_lemma = _normalise_arabic(pair["source"]["lemma"])
    tgt_lemma = pair["target"]["lemma"].strip().lower()

    # Arabic side: project to Latin chars (same for both modes)
    ara_skel = _arabic_consonant_chars(ara_lemma)
    ara_latin_set = _project_arabic_to_latin_set(ara_skel)

    # --- Baseline (empty cache, rule-based only) ---
    _force_empty_cache()
    tgt_skels_base = extract_all_skeletons(tgt_lemma, ipa=None, lang="lat")
    base_score = skeleton_similarity(ara_latin_set, tgt_skels_base)

    # --- Layer 1 (annotations loaded from disk) ---
    _force_reload_cache()
    tgt_skels_l1 = extract_all_skeletons(tgt_lemma, ipa=None, lang="lat")
    l1_score = skeleton_similarity(ara_latin_set, tgt_skels_l1)

    return base_score, l1_score


# ---------------------------------------------------------------------------
# Main evaluation
# ---------------------------------------------------------------------------

def _threshold_hits(scores: list[float], threshold: float) -> int:
    return sum(1 for s in scores if s > threshold)


def main() -> None:
    pairs = load_ara_lat_pairs()
    n = len(pairs)

    base_scores: list[float] = []
    l1_scores: list[float] = []
    # (tgt_lemma, ara_lemma, base_score, l1_score)
    details: list[tuple[str, str, float, float]] = []

    for pair in pairs:
        base, l1 = score_pair(pair)
        base_scores.append(base)
        l1_scores.append(l1)
        details.append((
            pair["target"]["lemma"].strip(),
            _normalise_arabic(pair["source"]["lemma"]),
            base,
            l1,
        ))

    improved = sum(1 for b, l in zip(base_scores, l1_scores) if l > b)
    degraded = sum(1 for b, l in zip(base_scores, l1_scores) if l < b)
    unchanged = n - improved - degraded

    mean_base = sum(base_scores) / n if n else 0.0
    mean_l1 = sum(l1_scores) / n if n else 0.0

    thresholds = [0.55, 0.45, 0.35]

    print()
    print("=== Layer 1 Impact on ara-lat Gold Pairs ===")
    print(f"Total pairs evaluated: {n}")
    print()
    print(f"{'Metric':<26} {'Baseline':>10} {'Layer1':>10} {'Delta':>10}")
    print("\u2500" * 58)

    for thr in thresholds:
        b_hits = _threshold_hits(base_scores, thr)
        l_hits = _threshold_hits(l1_scores, thr)
        delta = l_hits - b_hits
        sign = "+" if delta >= 0 else ""
        label = f"Skeleton hits (>{thr})"
        print(f"{label:<26} {b_hits:>10} {l_hits:>10} {sign + str(delta):>10}")

    delta_mean = mean_l1 - mean_base
    sign = "+" if delta_mean >= 0 else ""
    print(
        f"{'Mean skeleton score':<26} "
        f"{mean_base:>10.3f} {mean_l1:>10.3f} {sign + f'{delta_mean:.3f}':>10}"
    )
    print(f"{'Pairs improved':<26} {'--':>10} {improved:>10} {'--':>10}")
    print(f"{'Pairs degraded':<26} {'--':>10} {degraded:>10} {'--':>10}")
    print(f"{'Pairs unchanged':<26} {'--':>10} {unchanged:>10} {'--':>10}")

    # Top 10 biggest improvements
    sorted_details = sorted(details, key=lambda x: x[3] - x[2], reverse=True)
    print()
    print("Top 10 biggest improvements:")
    for tgt, ara, base, l1 in sorted_details[:10]:
        d = l1 - base
        sign = "+" if d >= 0 else ""
        print(f"  {tgt}: {ara}  {base:.2f} \u2192 {l1:.2f} ({sign}{d:.2f})")

    # Regressions
    worst = [x for x in sorted_details if x[3] - x[2] < 0]
    if worst:
        print()
        print("Top 5 biggest regressions:")
        for tgt, ara, base, l1 in worst[-5:][::-1]:
            d = l1 - base
            print(f"  {tgt}: {ara}  {base:.2f} \u2192 {l1:.2f} ({d:.2f})")

    print()


if __name__ == "__main__":
    main()
