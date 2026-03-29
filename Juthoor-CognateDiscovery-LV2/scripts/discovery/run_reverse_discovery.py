"""
Juthoor LV2 Reverse Discovery Pipeline

Instead of Arabic->Target (N*M pairs), starts from each target word
and traces it back to Arabic roots via reverse index lookup.

Usage:
  python run_reverse_discovery.py --target ang
  python run_reverse_discovery.py --target lat --limit 5000
  python run_reverse_discovery.py --target grc --phonetic-threshold 0.60
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Force UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
LV2_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = LV2_ROOT.parent
LV0_PROCESSED = REPO_ROOT / "Juthoor-DataCore-LV0/data/processed"
REVERSE_INDEX = LV2_ROOT / "data/processed/reverse_arabic_root_index.json"
CONCEPTS_FILE = LV2_ROOT / "resources/concepts/concepts_v3_2_enriched.jsonl"

# Package path
sys.path.insert(0, str(LV2_ROOT / "src"))

# Optional target morphology module (may not yet be installed)
try:
    from juthoor_cognatediscovery_lv2.discovery.target_morphology import extract_all_skeletons
except ImportError:
    extract_all_skeletons = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Corpus map (copied from run_discovery_multilang.py — do not import)
# ---------------------------------------------------------------------------

CORPUS_PATHS: dict[str, str | None] = {
    "ara": "quranic_arabic/sources/quran_lemmas_enriched.jsonl",
    "ara_classical": "arabic/classical/lexemes.jsonl",
    "heb": "hebrew/sources/kaikki.jsonl",
    "lat": "latin/classical/sources/kaikki.jsonl",
    "grc": "ancient_greek/sources/kaikki.jsonl",
    "per": "persian/modern/sources/kaikki.jsonl",
    "fas": "persian/modern/sources/kaikki.jsonl",  # alias
    "arc": "aramaic/classical/sources/kaikki.jsonl",
    "enm": "english_middle/sources/kaikki.jsonl",
    "ang": "english_old/sources/kaikki.jsonl",
}

LARGE_CORPORA: set[str] = {"lat"}

NON_SEMITIC_TARGETS: set[str] = {"ang", "enm", "lat", "grc", "per", "fas"}

# ---------------------------------------------------------------------------
# Corpus loaders (copied logic from run_discovery_multilang.py)
# ---------------------------------------------------------------------------


def _pos_ok_kaikki(pos: list | str | None) -> bool:
    if pos is None:
        return True
    if isinstance(pos, list):
        return any(p in ("noun", "verb", "adj", "adv", "adjective", "adverb", "") for p in pos)
    return True


def _load_corpus_sequential(path: Path, lang: str, limit: int) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            lemma = str(row.get("lemma", "") or "").strip()
            if not lemma or len(lemma) < 2:
                continue
            pos = row.get("pos")
            if not _pos_ok_kaikki(pos):
                continue
            entries.append(row)
            if limit and len(entries) >= limit:
                break
    return entries


def _load_corpus_strided(path: Path, lang: str, limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        limit = 5000

    total_lines = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                total_lines += 1

    stride = max(1, total_lines // (limit * 2))

    seen_lemmas: set[str] = set()
    entries: list[dict[str, Any]] = []
    line_num = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            line_num += 1
            if stride > 1 and (line_num - 1) % stride != 0:
                continue
            row = json.loads(line)
            lemma = str(row.get("lemma", "") or "").strip().lower()
            if not lemma or len(lemma) <= 2:
                continue
            pos = row.get("pos")
            if not _pos_ok_kaikki(pos):
                continue
            if lemma in seen_lemmas:
                continue
            seen_lemmas.add(lemma)
            entries.append(row)
            if len(entries) >= limit:
                break
    return entries


def load_corpus(lang: str, limit: int = 0) -> list[dict[str, Any]]:
    # Resolve alias
    canonical = "per" if lang == "fas" else lang
    rel = CORPUS_PATHS.get(canonical)
    if rel is None:
        raise ValueError(f"Unknown language code: {lang!r}")
    corpus_path = LV0_PROCESSED / rel
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus not found: {corpus_path}")

    if canonical in LARGE_CORPORA:
        return _load_corpus_strided(corpus_path, canonical, limit)
    else:
        return _load_corpus_sequential(corpus_path, canonical, limit)


# ---------------------------------------------------------------------------
# Skeleton extraction
# ---------------------------------------------------------------------------

_BASIC_CONS_RE = re.compile(r"[bcdfghjklmnpqrstvwxyz]", re.IGNORECASE)
_IPA_TO_LATIN = str.maketrans({
    "θ": "s", "ð": "d", "ɹ": "r", "ɾ": "r", "ʁ": "r",
    "χ": "k", "ħ": "h", "ʕ": "", "ɣ": "g", "β": "b",
    "ɸ": "f", "ʔ": "", "ɫ": "l", "ʍ": "w",
})
_IPA_CONS_RE = re.compile(r"[bcdfghjklmnpqrstvwxyzðθɹɾʁχħʕɣβɸʔɫŋ]")


def extract_skeleton(lemma: str, ipa: str | None = None) -> str:
    """Extract consonant skeleton from lemma or IPA."""
    if not lemma:
        return ""
    is_latin = lemma[0].isascii() and lemma[0].isalpha()
    if is_latin:
        skel = re.sub(r"[aeiouáéíóúàèìòùâêîôûäëïöü]", "", lemma.lower())
        skel = "".join(_BASIC_CONS_RE.findall(skel))
    elif ipa:
        s = ipa.lower()
        s = s.replace("tʃ", "c").replace("dʒ", "j").replace("ʃ", "sh").replace("ŋ", "ng")
        s = s.translate(_IPA_TO_LATIN)
        skel = "".join(_IPA_CONS_RE.findall(s))
    else:
        skel = ""
    return skel


def _lookup_variants(skeleton: str) -> list[str]:
    """Generate all lookup key variants for a skeleton."""
    variants: list[str] = []
    if not skeleton:
        return variants

    # Direct
    variants.append(skeleton)

    # Truncated: drop first or last consonant (handles prefixes/suffixes)
    if len(skeleton) >= 3:
        variants.append(skeleton[1:])   # drop first
        variants.append(skeleton[:-1])  # drop last

    # Metathesis: permutations of first 3 consonants
    first3 = skeleton[:3]
    if len(first3) == 3:
        for perm in itertools.permutations(first3):
            v = "".join(perm)
            if v != first3:
                variants.append(v)

    # If 4+ consonants, try first-3 and last-3 subsets
    if len(skeleton) >= 4:
        variants.append(skeleton[:3])
        variants.append(skeleton[-3:])

    return list(dict.fromkeys(variants))  # deduplicate, preserve order


# ---------------------------------------------------------------------------
# Timeout helper (SIGALRM not available on Windows; use threading)
# ---------------------------------------------------------------------------

import threading
import concurrent.futures


class _TimeoutError(Exception):
    pass


def _score_with_timeout(scorer: Any, arabic_entry: dict, target_entry: dict, timeout: float) -> Any:
    """Run scorer.score_pair with a timeout. Returns None on timeout."""
    result_holder: list[Any] = []
    exc_holder: list[BaseException] = []

    def _run() -> None:
        try:
            result_holder.append(scorer.score_pair(arabic_entry, target_entry))
        except Exception as e:
            exc_holder.append(e)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=timeout)
    if t.is_alive():
        return None  # timed out — thread continues in background but we skip
    if exc_holder:
        return None
    if result_holder:
        return result_holder[0]
    return None


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def build_reverse_lookup(
    reverse_index: dict[str, Any],
    skeleton: str,
) -> list[dict[str, Any]]:
    """Fetch all Arabic root candidates for a given skeleton via lookup variants."""
    seen_roots: set[str] = set()
    candidates: list[dict[str, Any]] = []

    for variant in _lookup_variants(skeleton):
        entry = reverse_index.get(variant)
        if not entry:
            continue
        for cand in entry.get("candidates", []):
            root = cand.get("root", "")
            if root and root not in seen_roots:
                seen_roots.add(root)
                candidates.append(cand)

    return candidates


def process_word(
    target_entry: dict[str, Any],
    reverse_index: dict[str, Any],
    scorer: Any,
    concept_matcher: Any,
    phonetic_threshold: float,
    max_candidates: int,
    no_semantic: bool,
    score_timeout: float = 5.0,
    target_lang: str = "",
) -> dict[str, Any] | None:
    """Process one target word and return a result record, or None if no candidates pass."""
    lemma = str(target_entry.get("lemma", "") or "").strip()
    if not lemma:
        return None

    ipa = target_entry.get("ipa") or target_entry.get("ipa_raw") or None

    # Use morphological decomposition if available, otherwise fall back to single skeleton
    if extract_all_skeletons is not None:
        skeletons = extract_all_skeletons(lemma, ipa, target_lang or target_entry.get("language", ""))
    else:
        single = extract_skeleton(lemma, ipa)
        skeletons = [single] if single else []

    if not skeletons:
        return None

    # Primary skeleton (first) used for the output record
    skeleton = skeletons[0]

    # Lookup candidates from ALL skeletons and deduplicate by root
    raw_candidates: list[dict[str, Any]] = []
    seen_roots: set[str] = set()
    for skel in skeletons:
        for cand in build_reverse_lookup(reverse_index, skel):
            root = cand.get("root", "")
            if root not in seen_roots:
                seen_roots.add(root)
                raw_candidates.append(cand)

    if not raw_candidates:
        return None

    target_meaning = (
        target_entry.get("meaning_text")
        or target_entry.get("gloss")
        or target_entry.get("short_gloss")
        or ""
    )

    scored: list[dict[str, Any]] = []

    # Pre-rank candidates by projection similarity to skeleton (cheap)
    from difflib import SequenceMatcher
    for cand in raw_candidates:
        proj = cand.get("projection", "")
        cand["_prescore"] = SequenceMatcher(None, proj, skeleton).ratio() if proj else 0.0
    raw_candidates.sort(key=lambda c: c["_prescore"], reverse=True)
    # Score top 20 candidates with full scorer
    top_candidates = raw_candidates[:20]

    for cand in top_candidates:
        arabic_entry: dict[str, Any] = {
            "lemma": cand.get("root", ""),
            "root": cand.get("root", ""),
            "root_norm": cand.get("root", ""),
            "meaning_text": cand.get("meaning_text", ""),
            "language": "ara",
        }

        # Phonetic scoring with timeout — NO filtering by methods count
        result = _score_with_timeout(scorer, arabic_entry, target_entry, score_timeout)
        if result is None:
            continue

        phonetic_score: float = result.best_score
        if phonetic_score < phonetic_threshold:
            continue

        # NO semantic filter — collect everything
        scored.append({
            "arabic_root": cand.get("root", ""),
            "arabic_projection": cand.get("projection", ""),
            "arabic_meaning": cand.get("meaning_text", "")[:200],
            "phonetic_score": round(phonetic_score, 4),
            "prescore": round(cand.get("_prescore", 0), 4),
            "methods_fired": len(result.methods_that_fired),
            "best_method": result.best_method,
        })

    # Also add candidates that didn't go through full scoring but have high prescore
    # (pure skeleton similarity — fast, no scorer needed)
    scored_roots = {s["arabic_root"] for s in scored}
    for cand in raw_candidates:
        root = cand.get("root", "")
        if root in scored_roots:
            continue
        prescore = cand.get("_prescore", 0)
        if prescore >= 0.50:  # decent skeleton match
            scored.append({
                "arabic_root": root,
                "arabic_projection": cand.get("projection", ""),
                "arabic_meaning": cand.get("meaning_text", "")[:200],
                "phonetic_score": round(prescore, 4),
                "prescore": round(prescore, 4),
                "methods_fired": 0,
                "best_method": "skeleton_only",
            })

    if not scored:
        return None

    # Rank by phonetic score, keep ALL (max_candidates=0 means unlimited)
    scored.sort(key=lambda x: x["phonetic_score"], reverse=True)
    top = scored if max_candidates <= 0 else scored[:max_candidates]

    return {
        "target_word": lemma,
        "target_lang": target_entry.get("language", ""),
        "target_meaning": str(target_meaning)[:200],
        "target_ipa": str(ipa) if ipa else "",
        "skeleton": skeleton,
        "skeletons": skeletons,
        "candidate_count": len(top),
        "candidates": top,
    }


def run(args: argparse.Namespace) -> None:
    t_start = time.time()
    lang = args.target

    if lang not in NON_SEMITIC_TARGETS:
        print(f"ERROR: --target must be one of {sorted(NON_SEMITIC_TARGETS)}")
        sys.exit(1)

    print(f"=== Juthoor LV2 Reverse Discovery: {lang.upper()} ===")
    print(f"Started at {datetime.now(timezone.utc).isoformat()}")

    # Step 1: Load target corpus
    print(f"\n[1/5] Loading {lang} corpus (limit={args.limit or 'all'})...")
    entries = load_corpus(lang, limit=args.limit)
    # Tag language onto entries if missing
    for e in entries:
        if not e.get("language"):
            e["language"] = lang
    print(f"      Loaded {len(entries):,} entries")

    # Step 2: Load reverse index
    print(f"\n[2/5] Loading reverse Arabic root index from {REVERSE_INDEX}...")
    with open(REVERSE_INDEX, encoding="utf-8") as f:
        reverse_index: dict[str, Any] = json.load(f)
    print(f"      {len(reverse_index):,} skeleton keys loaded")

    # Step 3+4+5: Score
    print(f"\n[3/5] Initialising scorer and concept matcher...")
    from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScorer
    scorer = MultiMethodScorer()

    concept_matcher = None
    if not args.no_semantic:
        from juthoor_cognatediscovery_lv2.discovery.concept_matcher import ConceptMatcher
        concept_matcher = ConceptMatcher(CONCEPTS_FILE)
        concept_matcher._ensure_loaded()
        print("      ConceptMatcher loaded")

    # Output setup
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = output_dir / f"reverse_{lang}_{ts}.jsonl"

    print(f"\n[4/5] Processing {len(entries):,} target words...")
    print(f"      phonetic_threshold={args.phonetic_threshold}  max_candidates={args.max_candidates}")
    print(f"      output -> {out_path}")

    results: list[dict[str, Any]] = []
    words_with_candidates = 0
    words_with_semantic = 0
    processed = 0

    with open(out_path, "w", encoding="utf-8") as out_f:
        for entry in entries:
            processed += 1
            if processed % 500 == 0:
                elapsed = time.time() - t_start
                print(f"      [{processed:>6}/{len(entries):,}] elapsed={elapsed:.1f}s  hits={words_with_candidates}")

            result = process_word(
                target_entry=entry,
                reverse_index=reverse_index,
                scorer=scorer,
                concept_matcher=concept_matcher,
                phonetic_threshold=args.phonetic_threshold,
                max_candidates=args.max_candidates,
                no_semantic=args.no_semantic,
                score_timeout=5.0,
                target_lang=lang,
            )

            if result is not None:
                words_with_candidates += 1
                if any(c.get("semantic_score", 0) > 0 for c in result["candidates"]):
                    words_with_semantic += 1
                results.append(result)
                out_f.write(json.dumps(result, ensure_ascii=False) + "\n")

    # Step 6: Summary
    elapsed_total = time.time() - t_start
    print(f"\n[5/5] Summary")
    print(f"  Total words processed     : {processed:,}")
    print(f"  Words with >=1 candidate  : {words_with_candidates:,} ({words_with_candidates/max(processed,1)*100:.1f}%)")
    print(f"  Words with semantic > 0   : {words_with_semantic:,}")
    print(f"  Total runtime             : {elapsed_total:.1f}s")
    print(f"  Output                    : {out_path}")

    # Distribution of candidate counts
    if results:
        from collections import Counter
        dist = Counter(r["candidate_count"] for r in results)
        print("\n  Candidate count distribution:")
        for k in sorted(dist.keys()):
            print(f"    {k} candidate(s): {dist[k]:,} words")

    # Top 30 by best phonetic score
    if results:
        top30 = sorted(results, key=lambda r: r["candidates"][0]["phonetic_score"], reverse=True)[:30]
        print(f"\n  Top 30 words by best phonetic score:")
        print(f"  {'Word':<20} {'Skeleton':<10} {'Arabic Root':<12} {'Phonetic':>8} {'#Cand':>6} {'Method'}")
        print(f"  {'-'*20} {'-'*10} {'-'*12} {'-'*8} {'-'*6} {'-'*20}")
        for r in top30:
            c = r["candidates"][0]
            print(
                f"  {r['target_word']:<20} {r['skeleton']:<10} {c['arabic_root']:<12} "
                f"{c['phonetic_score']:>8.3f} {len(r['candidates']):>6} "
                f"{c['best_method']}"
            )

    print(f"\nDone in {elapsed_total:.1f}s")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Juthoor LV2 Reverse Discovery — trace target words back to Arabic roots"
    )
    parser.add_argument(
        "--target",
        required=True,
        choices=sorted(NON_SEMITIC_TARGETS),
        help="Target language code (non-Semitic only)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max target words to process (0 = all)",
    )
    parser.add_argument(
        "--phonetic-threshold",
        type=float,
        default=0.40,
        help="Minimum phonetic score to keep a candidate (default: 0.40)",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=0,
        help="Max Arabic root candidates per word (0 = keep all, default: 0)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(LV2_ROOT / "outputs/reverse_discovery"),
        help="Output directory for JSONL results",
    )
    parser.add_argument(
        "--no-semantic",
        action="store_true",
        help="Skip semantic filter — keep all phonetic matches",
    )
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
