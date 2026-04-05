"""Compare fast phonetic-only discovery against semantic-filtered scoring.

This script demonstrates that consonant-only discovery has high recall but
also many more matches than a semantically constrained variant. It runs:

1. A real pass over Arabic x English pairs using MultiMethodScorer.
2. A semantic-filtered pass requiring both phonetic score >= threshold and
   gloss similarity > 0.
3. A null model where Arabic roots are shuffled and both modes are re-run.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path
from typing import Any, Callable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LV2_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LV2_ROOT / "src"))

ARABIC_CORPUS = LV2_ROOT / "data/processed/arabic/quran_lemmas_enriched.jsonl"
ENGLISH_CORPUS = LV2_ROOT / "data/processed/english/english_ipa_merged_pos.jsonl"

DEFAULT_ARABIC_LIMIT = 30
DEFAULT_ENGLISH_LIMIT = 200
DEFAULT_THRESHOLD = 0.55
DEFAULT_NULL_ITERATIONS = 1
DEFAULT_SEED = 42


def _fallback_gloss_similarity(source: dict[str, Any], target: dict[str, Any]) -> float:
    """Basic word-overlap fallback if the module import is unavailable."""
    import re

    stopwords = {
        "a", "an", "the", "of", "in", "to", "for", "and", "or", "is", "it",
        "at", "by", "on", "as", "be", "was", "are", "were", "with", "from",
    }
    word_re = re.compile(r"[a-z]{3,}")

    def extract_words(row: dict[str, Any]) -> set[str]:
        text = " ".join(
            str(row.get(field, "") or "")
            for field in ("meaning_text", "gloss", "short_gloss", "gloss_plain")
        )
        return {word for word in word_re.findall(text.lower()) if word not in stopwords}

    src_words = extract_words(source)
    tgt_words = extract_words(target)
    if not src_words or not tgt_words:
        return 0.0
    return 1.0 if (src_words & tgt_words) else 0.0


def load_gloss_similarity() -> tuple[Callable[[dict[str, Any], dict[str, Any]], float], str]:
    try:
        from juthoor_cognatediscovery_lv2.discovery.gloss_similarity import gloss_similarity

        return gloss_similarity, "module"
    except ImportError:
        return _fallback_gloss_similarity, "fallback"


def load_arabic(limit: int) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    with ARABIC_CORPUS.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            lemma = str(row.get("lemma", "") or "").strip()
            if not lemma or len(lemma) < 2 or lemma in seen:
                continue
            seen.add(lemma)
            entries.append(row)
            if len(entries) >= limit:
                break
    return entries


def load_english(limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []

    total_lines = 0
    with ENGLISH_CORPUS.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                total_lines += 1

    stride = max(1, total_lines // (limit * 2))
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    line_number = 0

    with ENGLISH_CORPUS.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            line_number += 1
            if stride > 1 and (line_number - 1) % stride != 0:
                continue
            row = json.loads(line)
            lemma = str(row.get("lemma", "") or "").strip().lower()
            if not lemma or len(lemma) <= 2:
                continue
            if not lemma.replace("-", "").replace("'", "").isalpha():
                continue
            if lemma in seen:
                continue
            seen.add(lemma)
            entries.append(row)
            if len(entries) >= limit:
                break
    return entries


def shuffle_roots(arabic_entries: list[dict[str, Any]], rng: random.Random) -> list[dict[str, Any]]:
    shuffled = [dict(entry) for entry in arabic_entries]
    roots = [
        str(entry.get("root_norm") or entry.get("root") or entry.get("lemma") or "").strip()
        for entry in shuffled
    ]
    rng.shuffle(roots)
    for entry, root in zip(shuffled, roots):
        entry["root"] = root
        entry["root_norm"] = root
    return shuffled


def score_pairs(
    arabic_entries: list[dict[str, Any]],
    english_entries: list[dict[str, Any]],
    scorer: Any,
    gloss_fn: Callable[[dict[str, Any], dict[str, Any]], float],
    threshold: float,
) -> dict[str, Any]:
    fast_only_matches = 0
    semantic_filtered_matches = 0
    total_pairs = len(arabic_entries) * len(english_entries)

    for source in arabic_entries:
        for target in english_entries:
            result = scorer.score_pair(source, target)
            if result.best_score < threshold:
                continue
            fast_only_matches += 1
            if gloss_fn(source, target) > 0.0:
                semantic_filtered_matches += 1

    return {
        "pairs": total_pairs,
        "fast_only_matches": fast_only_matches,
        "semantic_filtered_matches": semantic_filtered_matches,
    }


def summarize_null_counts(counts: list[int]) -> str:
    if not counts:
        return "n/a"
    mean = sum(counts) / len(counts)
    minimum = min(counts)
    maximum = max(counts)
    return f"mean={mean:.1f}, min={minimum}, max={maximum}"


def print_report(
    real_counts: dict[str, Any],
    null_fast_counts: list[int],
    null_semantic_counts: list[int],
    *,
    arabic_count: int,
    english_count: int,
    threshold: float,
    null_iterations: int,
    gloss_source: str,
    elapsed_seconds: float,
) -> None:
    fast_count = int(real_counts["fast_only_matches"])
    semantic_count = int(real_counts["semantic_filtered_matches"])
    reduction = fast_count - semantic_count
    reduction_pct = (reduction / fast_count * 100.0) if fast_count else 0.0

    print("=" * 64)
    print("Fast vs Semantic-Filtered Discovery")
    print("=" * 64)
    print(f"Arabic entries loaded:      {arabic_count}")
    print(f"English entries loaded:     {english_count}")
    print(f"Total pairs scored:         {real_counts['pairs']:,}")
    print(f"Phonetic threshold:         {threshold:.2f}")
    print(f"Gloss similarity source:    {gloss_source}")
    print(f"Null iterations:            {null_iterations}")
    print()
    print("Real run")
    print(f"  Fast-only matches:        {fast_count}")
    print(f"  Semantic-filtered matches:{semantic_count}")
    print(f"  Reduction:                {reduction} ({reduction_pct:.1f}%)")
    print()
    print("Null model (shuffled Arabic roots)")
    print(f"  Fast-only:                {summarize_null_counts(null_fast_counts)}")
    print(f"  Semantic-filtered:        {summarize_null_counts(null_semantic_counts)}")
    print()
    if semantic_count < fast_count:
        print("Result: semantic filtering reduces matches dramatically.")
    else:
        print("Result: semantic filtering did not reduce matches in this sample.")
    print(f"Elapsed: {elapsed_seconds:.1f}s")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare fast phonetic discovery vs semantic-filtered scoring."
    )
    parser.add_argument("--arabic-limit", type=int, default=DEFAULT_ARABIC_LIMIT)
    parser.add_argument("--english-limit", type=int, default=DEFAULT_ENGLISH_LIMIT)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--null-iterations", type=int, default=DEFAULT_NULL_ITERATIONS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScorer

    rng = random.Random(args.seed)
    gloss_fn, gloss_source = load_gloss_similarity()
    scorer = MultiMethodScorer()

    started_at = time.time()
    arabic_entries = load_arabic(args.arabic_limit)
    english_entries = load_english(args.english_limit)

    real_counts = score_pairs(
        arabic_entries=arabic_entries,
        english_entries=english_entries,
        scorer=scorer,
        gloss_fn=gloss_fn,
        threshold=args.threshold,
    )

    null_fast_counts: list[int] = []
    null_semantic_counts: list[int] = []
    for _ in range(args.null_iterations):
        shuffled_arabic = shuffle_roots(arabic_entries, rng)
        null_counts = score_pairs(
            arabic_entries=shuffled_arabic,
            english_entries=english_entries,
            scorer=scorer,
            gloss_fn=gloss_fn,
            threshold=args.threshold,
        )
        null_fast_counts.append(int(null_counts["fast_only_matches"]))
        null_semantic_counts.append(int(null_counts["semantic_filtered_matches"]))

    elapsed_seconds = time.time() - started_at
    print_report(
        real_counts,
        null_fast_counts,
        null_semantic_counts,
        arabic_count=len(arabic_entries),
        english_count=len(english_entries),
        threshold=args.threshold,
        null_iterations=args.null_iterations,
        gloss_source=gloss_source,
        elapsed_seconds=elapsed_seconds,
    )


if __name__ == "__main__":
    main()
