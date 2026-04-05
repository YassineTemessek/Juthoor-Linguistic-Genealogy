"""Lightweight Arabic<->English cognate discovery.

Uses only:
- PhoneticLawScorer (projection + IPA + metathesis + morpheme)
- cross_lingual_skeleton_score (correspondence.py class mapping)
- merger_overlap (phonetic_mergers.py — counts overlapping Arabic letters)

No embeddings. Pure phonetic + consonant-correspondence scoring.

Performance: pre-computes per-Arabic projections and pre-caches English
consonant skeletons to avoid repeating expensive work in the inner loop.
"""
from __future__ import annotations

import heapq
import io
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

# Force UTF-8 output on Windows to handle Arabic characters in print statements
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
LV2_ROOT = REPO_ROOT / "Juthoor-CognateDiscovery-LV2"

ARABIC_CORPUS = LV2_ROOT / "data/processed/arabic/quran_lemmas_enriched.jsonl"
ENGLISH_CORPUS = LV2_ROOT / "data/processed/english/english_ipa_merged_pos.jsonl"
GOLD_BENCHMARK = LV2_ROOT / "data/processed/beyond_name_cognate_gold_candidates.jsonl"
LEADS_DIR = LV2_ROOT / "outputs/leads"

ARABIC_LIMIT = 500
ENGLISH_LIMIT = 5000
TOP_K = 20

PHONETIC_WEIGHT = 0.6
SKELETON_WEIGHT = 0.4

# ---------------------------------------------------------------------------
# Package imports
# ---------------------------------------------------------------------------
sys.path.insert(0, str(LV2_ROOT / "src"))

from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import (
    PhoneticLawScorer,
    _arabic_consonant_skeleton,
    _english_consonant_skeleton,
    _strip_diacriticals,
    _pairwise_swap_variants,
    _morpheme_decompose,
    LATIN_EQUIVALENTS,
    normalize_arabic_root,
    project_root_sound_laws,
    _HIGH_FREQ_WORDS,
    _KNOWN_PREFIXES,
    _KNOWN_SUFFIXES,
)
from juthoor_cognatediscovery_lv2.discovery.correspondence import (
    cross_lingual_skeleton_score,
    correspondence_string,
)
from juthoor_cognatediscovery_lv2.discovery.phonetic_mergers import (
    merger_overlap,
    build_target_to_arabic_map,
    arabic_letter_set,
    load_phonetic_mergers,
)


# ---------------------------------------------------------------------------
# Arabic normalization helper (strip diacritics + tatweel, normalize hamza)
# ---------------------------------------------------------------------------
_ARABIC_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")
_HAMZA_TR = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ؤ": "و", "ئ": "ي", "ء": "ا"})


def _norm_arabic(text: str) -> str:
    """Normalize Arabic lemma for matching: strip diacritics, normalize hamza."""
    text = _ARABIC_DIACRITICS_RE.sub("", text)
    text = text.translate(_HAMZA_TR)
    return text.strip()


# ---------------------------------------------------------------------------
# Pre-built English merger map (avoids re-loading rules on every call)
# ---------------------------------------------------------------------------
_ENG_MERGER_RULES = load_phonetic_mergers()
_ENG_MERGER_MAP: dict[str, set[str]] = build_target_to_arabic_map("eng", rules=_ENG_MERGER_RULES)


def _merger_overlap_fast(ara_letters: set[str], eng_lemma: str) -> set[str]:
    """Fast merger overlap using pre-built map."""
    tgt: set[str] = set()
    for ch in eng_lemma:
        if ch in _ENG_MERGER_MAP:
            tgt.update(_ENG_MERGER_MAP[ch])
    return ara_letters & tgt


# ---------------------------------------------------------------------------
# IPA consonant skeleton helper (mirrors ipa_lookup but inline for speed)
# ---------------------------------------------------------------------------
_IPA_TO_LATIN_TR = str.maketrans({
    "θ": "s", "ð": "d", "ɹ": "r", "ɾ": "r", "ʁ": "r",
    "χ": "kh", "ħ": "h", "ʕ": "", "ɣ": "g", "β": "b",
    "ɸ": "f", "ʔ": "", "ɫ": "l", "ʍ": "wh",
})
_IPA_VOWELS_RE = re.compile(r"[aeiouɪɛæʌɒɔʊəɑɜɐɵøœɶɯɤɨʉˈˌːʔ̃]")
_IPA_CONS_RE = re.compile(r"[bcdfghjklmnpqrstvwxyzðθɹɾʁχħʕɣβɸʔɫŋ]")


def _ipa_consonant_skeleton_fast(ipa: str) -> str:
    """Extract consonant skeleton from IPA string (fast, inline version)."""
    if not ipa:
        return ""
    s = ipa.lower()
    # Multi-char sequences first
    s = s.replace("tʃ", "c").replace("dʒ", "j").replace("ʃ", "sh").replace("ŋ", "ng")
    s = s.translate(_IPA_TO_LATIN_TR)
    return "".join(_IPA_CONS_RE.findall(s))


# ---------------------------------------------------------------------------
# Pre-computed per-Arabic structures
# ---------------------------------------------------------------------------

def _precompute_arabic(arabic_root: str) -> dict[str, Any]:
    """Compute once per Arabic root: projections, skeleton, primary_latin, metathesis.

    We cap at 8 unique projection variants to keep the inner loop fast (~2min total).
    The first 8 cover the most phonologically likely correspondences.
    """
    ar_skel = _arabic_consonant_skeleton(arabic_root)
    primary_latin = _strip_diacriticals(
        "".join(LATIN_EQUIVALENTS.get(ch, (ch,))[0] for ch in ar_skel)
    )
    all_variants = project_root_sound_laws(arabic_root, include_group_expansion=True, max_variants=256)
    # Deduplicate and cap at 8 for speed; primary_latin always first
    seen: dict[str, None] = {primary_latin: None}
    for v in all_variants:
        if v not in seen:
            seen[v] = None
        if len(seen) >= 8:
            break
    variants = tuple(seen.keys())

    meta_variants = ([primary_latin[::-1]] + _pairwise_swap_variants(primary_latin)[:2]) if primary_latin else []
    corr_str = correspondence_string(arabic_root)
    ara_letters = arabic_letter_set(arabic_root)

    return {
        "ar_skel": ar_skel,
        "primary_latin": primary_latin,
        "variants": variants,
        "meta_variants": meta_variants,
        "corr_str": corr_str,
        "ara_letters": ara_letters,
    }


# ---------------------------------------------------------------------------
# Pre-computed per-English structures
# ---------------------------------------------------------------------------

def _precompute_english_batch(english_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pre-compute consonant skeletons for all English entries once."""
    results = []
    for eng in english_entries:
        lemma = str(eng.get("lemma") or "").strip().lower()
        ipa = str(eng.get("ipa") or "").strip()
        eng_skel = _english_consonant_skeleton(lemma)
        ipa_skel = _ipa_consonant_skeleton_fast(ipa)
        corr_str = correspondence_string(lemma)
        _, stem, suffix = _morpheme_decompose(lemma)
        stem_skel = _english_consonant_skeleton(stem) if (suffix or _) and stem and len(stem) >= 2 else ""
        is_high_freq = lemma in _HIGH_FREQ_WORDS
        results.append({
            "entry": eng,
            "lemma": lemma,
            "eng_skel": eng_skel,
            "ipa_skel": ipa_skel,
            "corr_str": corr_str,
            "stem": stem,
            "stem_skel": stem_skel,
            "suffix": suffix,
            "is_high_freq": is_high_freq,
        })
    return results


# ---------------------------------------------------------------------------
# Fast scoring (no repeated expensive calls)
# ---------------------------------------------------------------------------

_IPA_LATIN_MAP = str.maketrans({
    "θ": "s", "ð": "d", "ɹ": "r", "ɾ": "r", "ʁ": "r",
    "χ": "kh", "ħ": "h", "ʕ": "", "ɣ": "g", "β": "b",
    "ɸ": "f", "ʔ": "", "ɫ": "l", "ʍ": "wh",
})


def _score_fast(
    ara_pre: dict[str, Any],
    eng_pre: dict[str, Any],
    scorer: PhoneticLawScorer,
) -> float:
    """Fast combined score using pre-computed structures."""
    ar_skel = ara_pre["ar_skel"]
    primary_latin = ara_pre["primary_latin"]
    variants = ara_pre["variants"]
    meta_variants = ara_pre["meta_variants"]
    ara_corr = ara_pre["corr_str"]

    eng_skel = eng_pre["eng_skel"]
    ipa_skel = eng_pre["ipa_skel"]
    eng_corr = eng_pre["corr_str"]
    stem_skel = eng_pre["stem_skel"]
    is_high_freq = eng_pre["is_high_freq"]
    lemma = eng_pre["lemma"]

    if not ar_skel or len(ar_skel) < 2:
        return 0.0
    if not eng_skel or len(eng_skel) < 2:
        return 0.0

    # Length ratio guard
    ratio = len(eng_skel) / len(ar_skel) if ar_skel else 0.0
    if ratio > 4.0 or ratio < 0.25:
        return 0.0

    # Projection match (variants vs eng_skel)
    proj_score = 0.0
    for var in variants:
        clean = _strip_diacriticals(var)
        s = SequenceMatcher(None, clean, eng_skel).ratio()
        if s > proj_score:
            proj_score = s

    # Direct match (primary_latin vs eng_skel)
    direct_score = (
        SequenceMatcher(None, primary_latin, eng_skel).ratio()
        if primary_latin and eng_skel else 0.0
    )

    # IPA match (variants vs ipa_skel -> latinized)
    ipa_proj_score = 0.0
    if ipa_skel:
        ipa_lat = ipa_skel.replace("tʃ", "ch").replace("dʒ", "j")
        ipa_lat = ipa_lat.replace("ʃ", "sh").replace("ʒ", "zh").replace("ŋ", "ng")
        ipa_lat = ipa_lat.translate(_IPA_LATIN_MAP)
        for var in variants:
            clean = _strip_diacriticals(var)
            s = SequenceMatcher(None, clean, ipa_lat).ratio()
            if s > ipa_proj_score:
                ipa_proj_score = s

    # Metathesis
    metathesis_score = 0.0
    if primary_latin and eng_skel:
        for mv in meta_variants:
            s = SequenceMatcher(None, mv, eng_skel).ratio()
            if s > metathesis_score:
                metathesis_score = s

    # Stem score
    stem_score = 0.0
    if stem_skel:
        stem_proj = max(
            (SequenceMatcher(None, _strip_diacriticals(v), stem_skel).ratio() for v in variants),
            default=0.0,
        )
        stem_direct = (
            SequenceMatcher(None, primary_latin, stem_skel).ratio()
            if primary_latin and stem_skel else 0.0
        )
        stem_score = max(stem_proj, stem_direct)

    # Mined weights (skip for speed — they add <1% improvement)
    base_score = max(proj_score, direct_score, stem_score, ipa_proj_score)
    phonetic = (
        base_score
        + min(metathesis_score * 0.4, 0.12)
    )
    phonetic = min(phonetic, 1.0)

    if is_high_freq:
        phonetic *= 0.6

    # Skeleton (correspondence class similarity)
    skeleton = (
        SequenceMatcher(None, ara_corr, eng_corr).ratio()
        if ara_corr and eng_corr else 0.0
    )

    # Merger overlap bonus (using pre-built map for speed)
    overlap = _merger_overlap_fast(ara_pre.get("ara_letters", set()), lemma)
    merger_bonus = min(len(overlap) * 0.02, 0.10)

    combined = PHONETIC_WEIGHT * phonetic + SKELETON_WEIGHT * skeleton + merger_bonus
    return min(round(combined, 6), 1.0)


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def _load_arabic_entries(path: Path, limit: int) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            root = rec.get("root", "")
            lemma = rec.get("lemma", "")
            pos = rec.get("pos_tag", "")
            if not root or len(lemma.strip()) < 2:
                continue
            if pos in {"P", ""}:
                continue
            entries.append(rec)
            if len(entries) >= limit:
                break
    return entries


def _load_english_entries(path: Path, limit: int) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen_lemmas: set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            ipa = rec.get("ipa", "")
            lemma = (rec.get("lemma") or "").strip().lower()
            if not ipa or not lemma or len(lemma) < 3:
                continue
            if not lemma.replace("'", "").replace("-", "").isalpha():
                continue
            if lemma in seen_lemmas:
                continue
            seen_lemmas.add(lemma)
            entries.append(rec)
            if len(entries) >= limit:
                break
    return entries


def _load_gold_pairs_ara_eng(path: Path) -> dict[str, set[str]]:
    """Load gold pairs, keyed by normalized Arabic lemma for robust matching."""
    gold: dict[str, set[str]] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            src = rec.get("source", {})
            tgt = rec.get("target", {})
            if src.get("lang") == "ara" and tgt.get("lang") == "eng":
                ara_l = _norm_arabic(str(src.get("lemma", "")))
                eng_l = str(tgt.get("lemma", "")).strip().lower()
                if ara_l and eng_l:
                    gold.setdefault(ara_l, set()).add(eng_l)
    return gold


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def run_discovery(
    arabic_entries: list[dict[str, Any]],
    english_entries: list[dict[str, Any]],
    top_k: int = TOP_K,
) -> list[dict[str, Any]]:
    """Score all pairs using pre-computed structures, keep top-K per Arabic entry."""
    scorer = PhoneticLawScorer()

    print("  Pre-computing English features...", flush=True)
    eng_pre_list = _precompute_english_batch(english_entries)
    print(f"  Done. Starting scoring loop...", flush=True)

    leads: list[dict[str, Any]] = []
    total = len(arabic_entries)

    for i, ara in enumerate(arabic_entries):
        if i % 50 == 0:
            print(f"  [{i}/{total}] Arabic entries scored...", flush=True)

        ara_lemma = str(ara.get("lemma", "")).strip()
        ara_root = str(ara.get("root") or "").strip()
        ara_gloss = str(ara.get("gloss") or "").strip()
        ara_translit = str(ara.get("translit") or "").strip()
        ara_pre = _precompute_arabic(ara_root or ara_lemma)

        # Score against all English entries
        # Use a list of (score, index) and get top-K with heapq
        pair_scores: list[tuple[float, int]] = []
        for j, eng_pre in enumerate(eng_pre_list):
            combined = _score_fast(ara_pre, eng_pre, scorer)
            if combined > 0.0:
                pair_scores.append((combined, j))

        top = heapq.nlargest(top_k, pair_scores, key=lambda x: x[0])

        for rank, (combined, j) in enumerate(top):
            eng_pre = eng_pre_list[j]
            eng = eng_pre["entry"]
            eng_lemma = eng_pre["lemma"]
            eng_ipa = str(eng.get("ipa", "")).strip()
            eng_gloss = str(eng.get("gloss") or "").strip()

            overlap = _merger_overlap_fast(ara_pre["ara_letters"], eng_lemma)

            leads.append({
                "source_lemma": ara_lemma,
                "source_lemma_norm": _norm_arabic(ara_lemma),
                "source_root": ara_root,
                "source_gloss": ara_gloss,
                "source_translit": ara_translit,
                "target_lemma": eng_lemma,
                "target_ipa": eng_ipa,
                "target_gloss": eng_gloss,
                "combined_score": combined,
                "rank": rank + 1,
                "merger_overlap": list(overlap),
            })

    return leads


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate_vs_gold(
    leads: list[dict[str, Any]],
    gold: dict[str, set[str]],
    top_ks: tuple[int, ...] = (1, 5, 10, 20),
) -> dict[str, float]:
    # Index by normalized Arabic lemma (gold is already normalized-keyed)
    leads_index: dict[str, list[tuple[int, str]]] = {}
    for lead in leads:
        src = lead.get("source_lemma_norm") or _norm_arabic(lead["source_lemma"])
        leads_index.setdefault(src, []).append((lead["rank"], lead["target_lemma"]))

    reciprocal_ranks: list[float] = []
    hits: dict[int, list[int]] = {k: [] for k in top_ks}
    evaluated = 0

    for ara_lemma, eng_targets in gold.items():
        if ara_lemma not in leads_index:
            continue
        ranked_targets = sorted(leads_index[ara_lemma], key=lambda x: x[0])
        target_set = {t.lower() for t in eng_targets}

        found_rank = None
        for rank, eng_lemma in ranked_targets:
            if eng_lemma.lower() in target_set:
                found_rank = rank
                break

        reciprocal_ranks.append(1.0 / found_rank if found_rank else 0.0)
        for k in top_ks:
            top_k_targets = {t for r, t in ranked_targets if r <= k}
            hits[k].append(1 if target_set & top_k_targets else 0)
        evaluated += 1

    if not evaluated:
        return {"evaluated_queries": 0, "mrr": 0.0, **{f"hit@{k}": 0.0 for k in top_ks}}

    result: dict[str, float] = {
        "evaluated_queries": evaluated,
        "mrr": round(sum(reciprocal_ranks) / evaluated, 4),
    }
    for k in top_ks:
        result[f"hit@{k}"] = round(sum(hits[k]) / evaluated, 4)
    return result


# ---------------------------------------------------------------------------
# New discovery analysis
# ---------------------------------------------------------------------------

def find_new_discoveries(
    leads: list[dict[str, Any]],
    gold: dict[str, set[str]],
    top_n: int = 50,
) -> list[dict[str, Any]]:
    # gold is already keyed by normalized Arabic lemma
    gold_set: set[tuple[str, str]] = set()
    for ara_l, eng_set in gold.items():
        for eng_l in eng_set:
            gold_set.add((ara_l, eng_l.lower()))

    novel = []
    for lead in leads:
        norm_src = lead.get("source_lemma_norm") or _norm_arabic(lead["source_lemma"])
        key = (norm_src, lead["target_lemma"].lower())
        if key not in gold_set:
            novel.append(lead)
    novel.sort(key=lambda x: (-x["combined_score"], x["rank"]))
    return novel[:top_n]


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_top_discoveries(discoveries: list[dict[str, Any]]) -> None:
    print(f"\n=== TOP NEW DISCOVERIES ===")
    for i, lead in enumerate(discoveries[:50], 1):
        source_label = lead["source_lemma"]
        if lead["source_gloss"]:
            source_label += f" ({lead['source_gloss']})"
        elif lead["source_translit"]:
            source_label += f" [{lead['source_translit']}]"

        target_label = lead["target_lemma"]
        if lead["target_ipa"]:
            target_label += f" /{lead['target_ipa']}/"

        overlap_note = ""
        if lead["merger_overlap"]:
            overlap_note = f"  merger-overlap: {','.join(lead['merger_overlap'])}"

        print(f"{i:3}. Arabic {source_label!r} -> English {target_label!r}")
        print(f"     score={lead['combined_score']:.4f}  rank={lead['rank']}{overlap_note}")


def save_leads(leads: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for lead in leads:
            f.write(json.dumps(lead, ensure_ascii=False) + "\n")
    print(f"\nLeads saved to: {output_path}")


def save_report(
    output_path: Path,
    metrics: dict[str, float],
    discoveries: list[dict[str, Any]],
    arabic_count: int,
    english_count: int,
    total_leads: int,
    timestamp: str,
) -> None:
    lines = [
        "# Lightweight Arabic-English Discovery Report",
        "",
        f"**Run:** {timestamp}",
        "",
        "## Pipeline Configuration",
        "",
        "| Parameter | Value |",
        "|-----------|-------|",
        f"| Arabic source | `quran_lemmas_enriched.jsonl` (first {arabic_count} content words) |",
        f"| English target | `english_ipa_merged_pos.jsonl` ({english_count} entries with IPA) |",
        f"| Top-K per Arabic entry | {TOP_K} |",
        f"| Scoring | PhoneticLawFast x {PHONETIC_WEIGHT} + CorrespondenceSkeleton x {SKELETON_WEIGHT} + MergerBonus |",
        "| Embeddings | None (pure phonetic) |",
        "",
        "## Metrics vs Gold Benchmark (ara->eng)",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Evaluated queries | {int(metrics.get('evaluated_queries', 0))} |",
        f"| MRR | {metrics.get('mrr', 0):.4f} |",
        f"| Hit@1 | {metrics.get('hit@1', 0):.4f} |",
        f"| Hit@5 | {metrics.get('hit@5', 0):.4f} |",
        f"| Hit@10 | {metrics.get('hit@10', 0):.4f} |",
        f"| Hit@20 | {metrics.get('hit@20', 0):.4f} |",
        f"| Total leads generated | {total_leads} |",
        "",
        "## Top 20 New Discoveries",
        "",
        "Pairs not found in the gold benchmark, sorted by combined score.",
        "",
    ]
    for i, lead in enumerate(discoveries[:20], 1):
        source_label = lead["source_lemma"]
        if lead["source_gloss"]:
            source_label += f" ({lead['source_gloss']})"
        target_label = lead["target_lemma"]
        if lead["target_ipa"]:
            target_label += f" /{lead['target_ipa']}/"
        overlap = ", ".join(lead["merger_overlap"]) if lead["merger_overlap"] else "-"
        lines.append(f"{i}. Arabic **{source_label}** -> English **{target_label}**")
        lines.append(f"   - score={lead['combined_score']:.4f}, merger-overlap: {overlap}")
        lines.append("")

    lines += [
        "## Known Limitations",
        "",
        "- No semantic guard: high scores may be phonetically plausible but semantically unrelated.",
        "- English corpus sampled to 5000 entries with IPA - many real cognates may not be covered.",
        "- Arabic corpus restricted to Quranic content words (500 entries) - not exhaustive.",
        "- No embedding reranking: ranking is purely consonant-based.",
        "- Merger-overlap bonus is additive, not validated against real cross-family mergers.",
        "- Gold benchmark covers 857 ara<->eng pairs; evaluated_queries will be lower (only pairs",
        "  whose Arabic lemma appears in the sampled 500 Quran entries).",
        "",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Report saved to: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    print("=== Lightweight Arabic<->English Discovery ===")
    print(f"Timestamp: {timestamp}")

    print(f"\nLoading Arabic corpus (limit={ARABIC_LIMIT})...")
    arabic_entries = _load_arabic_entries(ARABIC_CORPUS, ARABIC_LIMIT)
    print(f"  Loaded {len(arabic_entries)} Arabic content entries")

    print(f"\nLoading English corpus (limit={ENGLISH_LIMIT})...")
    english_entries = _load_english_entries(ENGLISH_CORPUS, ENGLISH_LIMIT)
    print(f"  Loaded {len(english_entries)} English entries with IPA")

    print("\nLoading gold benchmark (ara<->eng)...")
    gold = _load_gold_pairs_ara_eng(GOLD_BENCHMARK)
    print(f"  Loaded {len(gold)} unique Arabic query lemmas ({sum(len(v) for v in gold.values())} total pairs)")

    print(f"\nScoring {len(arabic_entries)} x {len(english_entries)} pairs (top-{TOP_K} per Arabic entry)...")
    leads = run_discovery(arabic_entries, english_entries, top_k=TOP_K)
    print(f"  Generated {len(leads)} lead pairs")

    leads_path = LEADS_DIR / f"lightweight_ara_eng_{timestamp}.jsonl"
    save_leads(leads, leads_path)

    print("\nEvaluating against gold benchmark...")
    metrics = evaluate_vs_gold(leads, gold)
    print(f"\n=== METRICS vs GOLD ===")
    print(f"  Evaluated queries : {int(metrics['evaluated_queries'])}")
    print(f"  MRR               : {metrics['mrr']:.4f}")
    print(f"  Hit@1             : {metrics['hit@1']:.4f}")
    print(f"  Hit@5             : {metrics['hit@5']:.4f}")
    print(f"  Hit@10            : {metrics['hit@10']:.4f}")
    print(f"  Hit@20            : {metrics['hit@20']:.4f}")

    print("\nFinding novel discovery candidates (not in gold)...")
    discoveries = find_new_discoveries(leads, gold, top_n=50)
    print(f"  Found {len(discoveries)} novel candidates")
    print_top_discoveries(discoveries)

    report_path = LEADS_DIR / "lightweight_discovery_report.md"
    save_report(
        report_path,
        metrics,
        discoveries,
        arabic_count=len(arabic_entries),
        english_count=len(english_entries),
        total_leads=len(leads),
        timestamp=timestamp,
    )


if __name__ == "__main__":
    main()
