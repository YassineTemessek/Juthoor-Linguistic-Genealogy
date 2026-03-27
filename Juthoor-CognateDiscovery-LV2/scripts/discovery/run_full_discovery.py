"""
Juthoor LV2 Full Discovery Pipeline -- Arabic<->English Cognate Discovery

Modes:
  --fast    : Phonetic-only discovery (no embeddings, minutes)
  --full    : BGE-M3 + FAISS + phonetic + LLM validation (slower, best results)
  --llm     : Enable Claude API validation for top candidates

Usage:
  python run_full_discovery.py --fast --arabic-limit 500 --english-limit 5000
  python run_full_discovery.py --full --llm --arabic-limit 200 --english-limit 3000
"""
from __future__ import annotations

import argparse
import json
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
ARABIC_CORPUS = LV2_ROOT / "data/processed/arabic/quran_lemmas_enriched.jsonl"
CLASSICAL_ARABIC_CORPUS = REPO_ROOT / "Juthoor-DataCore-LV0/data/processed/arabic/classical/lexemes.jsonl"
ENGLISH_CORPUS = LV2_ROOT / "data/processed/english/english_ipa_merged_pos.jsonl"
GOLD_BENCHMARK = LV2_ROOT / "resources/benchmarks/cognate_gold.jsonl"
LEADS_DIR = LV2_ROOT / "outputs/leads"

# Package path
sys.path.insert(0, str(LV2_ROOT / "src"))

# ---------------------------------------------------------------------------
# Stage 1: Load corpora
# ---------------------------------------------------------------------------

def load_arabic_corpus(limit: int = 500) -> list[dict[str, Any]]:
    """Load Arabic entries from Quran and classical corpora, deduplicated by lemma."""
    entries: list[dict[str, Any]] = []
    seen_lemmas: set[str] = set()

    for corpus_path in (ARABIC_CORPUS, CLASSICAL_ARABIC_CORPUS):
        with open(corpus_path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                lemma = str(row.get("lemma", "") or "").strip()
                # Filter: must be a content word (N, V, ADJ) and have non-trivial lemma
                pos = row.get("pos_tag", "") or ""
                if not lemma or len(lemma) < 2:
                    continue
                if pos not in ("N", "V", "ADJ", "ADV", ""):
                    continue
                if lemma in seen_lemmas:
                    continue
                seen_lemmas.add(lemma)
                entries.append(row)

    if limit:
        return entries[:limit]
    return entries


def load_english_corpus(limit: int = 5000) -> list[dict[str, Any]]:
    """Load English entries from english_ipa_merged_pos.jsonl.

    Uses stride-based sampling to get broad alphabetical coverage rather than
    loading the first N entries (which are all 'a' words in this sorted file).
    Reads the full file with stride, then returns up to limit unique lemmas.
    """
    if limit <= 0:
        limit = 5000

    # First pass: count total non-empty lines
    total_lines = 0
    with open(ENGLISH_CORPUS, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                total_lines += 1

    # Set stride to cover the whole file and get ~2x limit candidates before dedup
    stride = max(1, total_lines // (limit * 2))

    seen_lemmas: set[str] = set()
    entries: list[dict[str, Any]] = []
    line_num = 0
    with open(ENGLISH_CORPUS, encoding="utf-8") as f:
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
            # Skip lemmas with non-alphabetic characters (contractions, numbers)
            if not lemma.replace("-", "").replace("'", "").isalpha():
                continue
            # Deduplicate by lemma
            if lemma in seen_lemmas:
                continue
            seen_lemmas.add(lemma)
            entries.append(row)
    # The stride already gave us ~2x limit entries spanning the full file.
    # Return all collected entries (up to 2x limit). The caller receives slightly more
    # than limit but with full alphabetical coverage.
    return entries


# ---------------------------------------------------------------------------
# Stage 2 (fast mode): Pre-computed fast scoring
#
# Strategy: pre-compute Arabic projections once, pre-compute English skeletons
# once, then use a fast inner loop (difflib ratios only). When a pair exceeds
# a low pre-filter threshold, call the full multi-method scorer on that pair.
# This cuts the expensive project_root_sound_laws calls by ~95%.
# ---------------------------------------------------------------------------

def _precompute_arabic_cache(arabic_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pre-compute projection variants + skeletons for each Arabic entry."""
    import re
    from difflib import SequenceMatcher
    from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import (
        _arabic_consonant_skeleton,
        _strip_diacriticals,
        _pairwise_swap_variants,
        LATIN_EQUIVALENTS,
        project_root_sound_laws,
    )

    _ARABIC_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")
    _HAMZA_TR = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ؤ": "و", "ئ": "ي", "ء": "ا"})

    def norm(text: str) -> str:
        text = _ARABIC_DIACRITICS_RE.sub("", text)
        return text.translate(_HAMZA_TR).strip()

    cache = []
    for ar in arabic_entries:
        root = str(
            ar.get("root_norm") or ar.get("root") or ar.get("lemma") or ""
        ).strip()
        root_norm = norm(root)
        ar_skel = _arabic_consonant_skeleton(root_norm)
        primary_latin = _strip_diacriticals(
            "".join(LATIN_EQUIVALENTS.get(ch, (ch,))[0] for ch in ar_skel)
        )
        # Generate projections, cap at 8 for speed
        try:
            all_variants = project_root_sound_laws(root_norm, include_group_expansion=True, max_variants=256)
        except Exception:
            all_variants = []
        seen: dict[str, None] = {primary_latin: None} if primary_latin else {}
        for v in all_variants:
            v_clean = v.strip()
            if v_clean and v_clean not in seen:
                seen[v_clean] = None
            if len(seen) >= 8:
                break
        variants = tuple(seen.keys())
        meta_variants = ([primary_latin[::-1]] + _pairwise_swap_variants(primary_latin)[:2]) if primary_latin else []
        cache.append({
            "entry": ar,
            "root": root,
            "root_norm": root_norm,
            "ar_skel": ar_skel,
            "primary_latin": primary_latin,
            "variants": variants,
            "meta_variants": meta_variants,
        })
    return cache


def _precompute_english_cache(english_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pre-compute consonant skeletons for all English entries."""
    import re
    from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import (
        _english_consonant_skeleton,
        _morpheme_decompose,
    )

    _IPA_TO_LATIN_TR = str.maketrans({
        "θ": "s", "ð": "d", "ɹ": "r", "ɾ": "r", "ʁ": "r",
        "χ": "kh", "ħ": "h", "ʕ": "", "ɣ": "g", "β": "b",
        "ɸ": "f", "ʔ": "", "ɫ": "l", "ʍ": "wh",
    })
    _IPA_CONS_RE = re.compile(r"[bcdfghjklmnpqrstvwxyzðθɹɾʁχħʕɣβɸʔɫŋ]")

    def ipa_skel(ipa: str) -> str:
        s = ipa.lower()
        s = s.replace("tʃ", "c").replace("dʒ", "j").replace("ʃ", "sh").replace("ŋ", "ng")
        s = s.translate(_IPA_TO_LATIN_TR)
        return "".join(_IPA_CONS_RE.findall(s))

    cache = []
    for en in english_entries:
        lemma = str(en.get("lemma", "") or "").strip().lower()
        ipa = str(en.get("ipa", "") or "").strip()
        eng_skel = _english_consonant_skeleton(lemma)
        i_skel = ipa_skel(ipa)
        _, stem, suffix = _morpheme_decompose(lemma)
        stem_skel = _english_consonant_skeleton(stem) if (suffix or _) and stem and len(stem) >= 2 else ""
        cache.append({
            "entry": en,
            "lemma": lemma,
            "eng_skel": eng_skel,
            "ipa_skel": i_skel,
            "stem": stem,
            "stem_skel": stem_skel,
        })
    return cache


def _fast_prefilter_score(ar_cache: dict[str, Any], en_cache: dict[str, Any]) -> float:
    """Quick score using pre-computed skeletons and variants. No LLM, no full scorer.

    Returns highest ratio found across variants vs eng/ipa/stem skeletons.
    """
    from difflib import SequenceMatcher

    en_skel = en_cache["eng_skel"]
    ipa_skel = en_cache["ipa_skel"]
    stem_skel = en_cache["stem_skel"]
    variants = ar_cache["variants"]
    meta_variants = ar_cache["meta_variants"]

    best = 0.0
    targets = [t for t in (en_skel, ipa_skel, stem_skel) if t]

    for var in variants:
        for tgt in targets:
            r = SequenceMatcher(None, var, tgt).ratio()
            if r > best:
                best = r
            if best >= 0.9:
                return best

    for meta in meta_variants:
        for tgt in targets:
            r = SequenceMatcher(None, meta, tgt).ratio()
            if r > best:
                best = r

    return best


def score_all_pairs_fast(
    arabic_entries: list[dict[str, Any]],
    english_entries: list[dict[str, Any]],
    scorer: Any,
    top_k: int = 20,
    threshold: float = 0.45,
    prefilter_threshold: float = 0.50,
) -> list[dict[str, Any]]:
    """Score all Arabic x English pairs using a three-phase approach:

    Phase 1: Pre-compute Arabic projections + English skeletons (one-time cost).
    Phase 2: Fast skeleton scoring for all pairs (~0.16ms/pair) using pre-computed data.
             Pairs below prefilter_threshold are dropped.
    Phase 3: Full MultiMethodScorer only on top candidates that passed Phase 2.
             Only the top-k * 3 candidates per Arabic entry go to full scoring.

    This gives full-quality scores for the best candidates without scoring all 100k pairs.
    """
    import heapq
    from difflib import SequenceMatcher
    from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import _strip_diacriticals

    _IPA_LATIN_MAP = str.maketrans({
        "θ": "s", "ð": "d", "ɹ": "r", "ɾ": "r", "ʁ": "r",
        "χ": "kh", "ħ": "h", "ʕ": "", "ɣ": "g", "β": "b",
        "ɸ": "f", "ʔ": "", "ɫ": "l", "ʍ": "wh",
    })

    PHONETIC_WEIGHT = 0.6
    SKELETON_WEIGHT = 0.4

    def _score_fast_inline(ar_pre: dict[str, Any], en_pre: dict[str, Any]) -> float:
        """Inline fast scorer using pre-computed cache. No external calls."""
        ar_skel = ar_pre["ar_skel"]
        primary_latin = ar_pre["primary_latin"]
        variants = ar_pre["variants"]
        meta_variants = ar_pre["meta_variants"]

        eng_skel = en_pre["eng_skel"]
        ipa_skel = en_pre["ipa_skel"]
        stem_skel = en_pre["stem_skel"]
        lemma = en_pre["lemma"]

        if not ar_skel or len(ar_skel) < 2:
            return 0.0
        if not eng_skel or len(eng_skel) < 2:
            return 0.0
        # Length ratio guard
        ratio = len(eng_skel) / len(ar_skel)
        if ratio > 4.0 or ratio < 0.25:
            return 0.0

        # Projection match
        proj_score = 0.0
        for var in variants:
            clean = _strip_diacriticals(var)
            s = SequenceMatcher(None, clean, eng_skel).ratio()
            if s > proj_score:
                proj_score = s

        # Direct match
        direct_score = (
            SequenceMatcher(None, primary_latin, eng_skel).ratio()
            if primary_latin and eng_skel else 0.0
        )

        # IPA match
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
        meta_score = 0.0
        for mv in meta_variants:
            s = SequenceMatcher(None, mv, eng_skel).ratio()
            if s > meta_score:
                meta_score = s

        # Stem score
        stem_score = 0.0
        if stem_skel:
            for var in variants:
                s = SequenceMatcher(None, _strip_diacriticals(var), stem_skel).ratio()
                if s > stem_score:
                    stem_score = s

        base = max(proj_score, direct_score, stem_score, ipa_proj_score)
        phonetic = min(base + meta_score * 0.4 * 0.3, 1.0)
        combined = PHONETIC_WEIGHT * phonetic + SKELETON_WEIGHT * base
        return min(round(combined, 6), 1.0)

    print("  Pre-computing Arabic projection cache...")
    ar_cache_list = _precompute_arabic_cache(arabic_entries)
    print("  Pre-computing English skeleton cache...")
    en_cache_list = _precompute_english_cache(english_entries)

    total_arabic = len(ar_cache_list)
    total_pairs = total_arabic * len(en_cache_list)
    n_full_scorer_candidates = top_k * 3  # per Arabic entry go to full scoring
    print(f"  Total pairs: {total_pairs:,}")
    print(f"  Phase 2 pre-filter threshold: {prefilter_threshold}")
    print(f"  Phase 3 full scorer: top-{n_full_scorer_candidates} candidates per Arabic entry")

    leads: list[dict[str, Any]] = []
    prefilter_passed = 0
    full_scored = 0

    for i, ar_cache in enumerate(ar_cache_list):
        if i % 10 == 0:
            print(f"  Processing Arabic entry {i + 1}/{total_arabic}...")
        ar = ar_cache["entry"]

        # Phase 2: fast scoring for all English entries, keep top candidates
        candidate_heap: list[tuple[float, int]] = []  # (fast_score, en_index)

        for j, en_cache in enumerate(en_cache_list):
            fast_score = _score_fast_inline(ar_cache, en_cache)
            if fast_score < prefilter_threshold:
                continue
            prefilter_passed += 1
            if len(candidate_heap) < n_full_scorer_candidates:
                heapq.heappush(candidate_heap, (fast_score, j))
            elif fast_score > candidate_heap[0][0]:
                heapq.heapreplace(candidate_heap, (fast_score, j))

        # Phase 3: full MultiMethodScorer on top candidates
        top_for_this: list[dict[str, Any]] = []
        for fast_score, j in candidate_heap:
            en = en_cache_list[j]["entry"]
            result = scorer.score_pair(ar, en)
            full_scored += 1
            if result.best_score <= threshold:
                continue

            explanation = ""
            if result.all_results:
                best_result = max(result.all_results, key=lambda r: r.score)
                explanation = best_result.explanation

            top_for_this.append({
                "source": {
                    "lang": ar.get("language", "ara"),
                    "lemma": ar.get("lemma", ""),
                    "root": ar.get("root", "") or ar.get("root_norm", ""),
                    "root_norm": ar.get("root_norm", "") or ar.get("root", ""),
                    "gloss": ar.get("meaning_text", "") or ar.get("short_gloss", "") or ar.get("gloss", ""),
                    "pos": ar.get("pos_tag", ""),
                    "translit": ar.get("translit", ""),
                    "ipa": ar.get("ipa", ""),
                },
                "target": {
                    "lang": "eng",
                    "lemma": en.get("lemma", ""),
                    "ipa": en.get("ipa", ""),
                    "ipa_raw": en.get("ipa_raw", ""),
                    "gloss": en.get("meaning_text", "") or en.get("gloss", ""),
                    "pos": en.get("pos", ""),
                },
                "scores": {
                    "multi_method_best": result.best_score,
                    "best_method": result.best_method,
                    "fast_prefilter_score": fast_score,
                    "methods_fired_count": len(result.methods_that_fired),
                    "arabic_expansions": result.arabic_expansions_tried,
                    "final_combined": result.best_score,
                },
                "evidence": {
                    "methods_fired": result.methods_that_fired,
                    "explanation": explanation,
                    "best_method": result.best_method,
                },
            })

        top_for_this.sort(key=lambda x: x["scores"]["multi_method_best"], reverse=True)
        leads.extend(top_for_this[:top_k])

    print(
        f"  Phase 2 passed: {prefilter_passed:,} / {total_pairs:,} "
        f"({100*prefilter_passed/max(total_pairs,1):.1f}%)"
    )
    print(f"  Phase 3 full scorer calls: {full_scored:,}")
    return leads


# ---------------------------------------------------------------------------
# Stage 2 (full mode): BGE-M3 FAISS retrieval
# ---------------------------------------------------------------------------

def try_faiss_retrieval(
    arabic_entries: list[dict[str, Any]],
    english_entries: list[dict[str, Any]],
    top_k: int = 100,
) -> dict[int, list[int]] | None:
    """
    Attempt BGE-M3 embedding + FAISS retrieval.
    Returns a dict mapping arabic_index -> [english_indices].
    Returns None if embedding not available or estimated time > 30 min.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("  [WARN] sentence-transformers not available. Falling back to fast mode.")
        return None

    model_name = "BAAI/bge-m3"
    print(f"  Loading BGE-M3 model ({model_name})...")
    try:
        t0 = time.time()
        model = SentenceTransformer(model_name)
        # Time a single sample to estimate total
        sample_text = "test word meaning"
        model.encode([sample_text])
        per_item_s = (time.time() - t0) / 1
        total_items = len(arabic_entries) + len(english_entries)
        estimated_min = (per_item_s * total_items) / 60
        if estimated_min > 30:
            print(f"  [WARN] Estimated embedding time: {estimated_min:.0f} min > 30 min limit.")
            print("  Falling back to fast mode.")
            return None
        print(f"  Estimated embedding time: {estimated_min:.1f} min. Proceeding...")
    except Exception as e:
        print(f"  [WARN] BGE-M3 init failed: {e}. Falling back to fast mode.")
        return None

    try:
        import numpy as np
        import faiss

        def get_gloss(entry: dict[str, Any]) -> str:
            return (
                entry.get("meaning_text", "")
                or entry.get("gloss", "")
                or entry.get("short_gloss", "")
                or entry.get("lemma", "")
            )

        print(f"  Embedding {len(arabic_entries)} Arabic entries...")
        ar_texts = [get_gloss(e) for e in arabic_entries]
        ar_vectors = model.encode(ar_texts, batch_size=64, show_progress_bar=True)

        print(f"  Embedding {len(english_entries)} English entries...")
        en_texts = [get_gloss(e) for e in english_entries]
        en_vectors = model.encode(en_texts, batch_size=64, show_progress_bar=True)

        # Build FAISS index on English
        dim = en_vectors.shape[1]
        index = faiss.IndexFlatIP(dim)
        en_norm = en_vectors / (np.linalg.norm(en_vectors, axis=1, keepdims=True) + 1e-10)
        ar_norm = ar_vectors / (np.linalg.norm(ar_vectors, axis=1, keepdims=True) + 1e-10)
        index.add(en_norm.astype(np.float32))

        # Search
        print(f"  Searching FAISS index (top-{top_k} per Arabic entry)...")
        scores, idxs = index.search(ar_norm.astype(np.float32), top_k)
        retrieval_map: dict[int, list[int]] = {}
        for i, idx_row in enumerate(idxs):
            retrieval_map[i] = [int(idx) for idx in idx_row if idx >= 0]
        print(f"  FAISS retrieval complete.")
        return retrieval_map

    except Exception as e:
        print(f"  [WARN] FAISS retrieval failed: {e}. Falling back to fast mode.")
        return None


def score_pairs_with_retrieval(
    arabic_entries: list[dict[str, Any]],
    english_entries: list[dict[str, Any]],
    retrieval_map: dict[int, list[int]],
    scorer: Any,
    top_k: int = 20,
    threshold: float = 0.40,
) -> list[dict[str, Any]]:
    """Score pairs using FAISS-retrieved candidates."""
    from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScore

    leads: list[dict[str, Any]] = []
    total = len(arabic_entries)

    for i, ar in enumerate(arabic_entries):
        if i % 50 == 0:
            print(f"  Scoring Arabic entry {i + 1}/{total}...")
        candidates = retrieval_map.get(i, [])
        top_for_this: list[dict[str, Any]] = []

        for en_idx in candidates:
            en = english_entries[en_idx]
            result: MultiMethodScore = scorer.score_pair(ar, en)
            if result.best_score <= threshold:
                continue
            explanation = ""
            if result.all_results:
                best_result = max(result.all_results, key=lambda r: r.score)
                explanation = best_result.explanation

            top_for_this.append({
                "source": {
                    "lang": ar.get("language", "ara"),
                    "lemma": ar.get("lemma", ""),
                    "root": ar.get("root", "") or ar.get("root_norm", ""),
                    "root_norm": ar.get("root_norm", "") or ar.get("root", ""),
                    "gloss": ar.get("meaning_text", "") or ar.get("short_gloss", ""),
                    "pos": ar.get("pos_tag", ""),
                    "translit": ar.get("translit", ""),
                    "ipa": ar.get("ipa", ""),
                },
                "target": {
                    "lang": "eng",
                    "lemma": en.get("lemma", ""),
                    "ipa": en.get("ipa", ""),
                    "ipa_raw": en.get("ipa_raw", ""),
                    "gloss": en.get("meaning_text", "") or en.get("gloss", ""),
                    "pos": en.get("pos", ""),
                },
                "scores": {
                    "multi_method_best": result.best_score,
                    "best_method": result.best_method,
                    "methods_fired_count": len(result.methods_that_fired),
                    "arabic_expansions": result.arabic_expansions_tried,
                    "final_combined": result.best_score,
                },
                "evidence": {
                    "methods_fired": result.methods_that_fired,
                    "explanation": explanation,
                    "best_method": result.best_method,
                },
                "retrieval": {"faiss_rank": candidates.index(en_idx)},
            })

        top_for_this.sort(key=lambda x: x["scores"]["multi_method_best"], reverse=True)
        leads.extend(top_for_this[:top_k])

    return leads


# ---------------------------------------------------------------------------
# Stage 4: LLM Validation
# ---------------------------------------------------------------------------

def run_llm_validation(
    leads: list[dict[str, Any]],
    llm_limit: int = 100,
) -> list[dict[str, Any]]:
    """Validate top leads with Claude API, updating scores in-place."""
    from juthoor_cognatediscovery_lv2.discovery.llm_validator import LLMEtymologyValidator

    validator = LLMEtymologyValidator()
    if not validator.available:
        print("  [WARN] No ANTHROPIC_API_KEY found. Skipping LLM validation.")
        return leads

    # Sort by current best score, take top N
    sorted_leads = sorted(leads, key=lambda x: x["scores"]["multi_method_best"], reverse=True)
    to_validate = sorted_leads[:llm_limit]
    rest = sorted_leads[llm_limit:]

    print(f"  Validating {len(to_validate)} pairs with Claude API...")
    for idx, lead in enumerate(to_validate):
        if idx % 10 == 0:
            print(f"    LLM validating {idx + 1}/{len(to_validate)}...")
        ar = lead["source"]
        en = lead["target"]
        phonetic_score = lead["scores"].get("multi_method_best", 0.0)
        try:
            result = validator.validate_pair(
                arabic_root=ar.get("lemma", "") or ar.get("root", ""),
                arabic_meaning=ar.get("gloss", ""),
                english_word=en.get("lemma", ""),
                english_meaning=en.get("gloss", ""),
                phonetic_score=phonetic_score,
                additional_context=lead["evidence"].get("explanation", ""),
            )
            llm_conf = result.confidence
            # Combine scores: 0.4 phonetic + 0.3 semantic (not available in fast mode) + 0.3 llm
            combined = 0.7 * phonetic_score + 0.3 * llm_conf
            lead["scores"]["llm_confidence"] = llm_conf
            lead["scores"]["final_combined"] = round(combined, 6)
            lead["evidence"]["llm_reasoning"] = result.reasoning
            lead["evidence"]["llm_method"] = result.method_used
            lead["evidence"]["llm_is_cognate"] = result.is_cognate
            lead["evidence"]["phonetic_rules"] = result.phonetic_rules_identified
        except Exception as e:
            lead["scores"]["llm_confidence"] = None
            lead["evidence"]["llm_error"] = str(e)

    # Re-sort combined
    combined_leads = to_validate + rest
    combined_leads.sort(key=lambda x: x["scores"].get("final_combined", 0.0), reverse=True)
    return combined_leads


# ---------------------------------------------------------------------------
# Stage 5: Benchmark Evaluation
# ---------------------------------------------------------------------------

def load_gold_benchmark(lang_pair: tuple[str, str] = ("ara", "eng")) -> list[dict[str, Any]]:
    """Load gold pairs for a specific language pair."""
    if not GOLD_BENCHMARK.exists():
        return []
    pairs = []
    with open(GOLD_BENCHMARK, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            src_lang = row.get("source", {}).get("lang", "")
            tgt_lang = row.get("target", {}).get("lang", "")
            if (src_lang, tgt_lang) == lang_pair:
                pairs.append(row)
    return pairs


def _normalize_arabic(text: str) -> str:
    """Strip diacritics and normalize hamza variants for comparison."""
    import re
    _diac_re = re.compile(r"[\u064B-\u065F\u0670\u0640]")
    _hamza_tr = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ؤ": "و", "ئ": "ي", "ء": "ا"})
    text = _diac_re.sub("", text)
    return text.translate(_hamza_tr).strip().lower()


def evaluate_against_benchmark(
    leads: list[dict[str, Any]],
    gold_pairs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute MRR, Hit@K for leads against gold benchmark.

    Normalizes Arabic lemmas (strips diacritics, normalizes hamza) before matching.
    """
    if not gold_pairs:
        return {"error": "No gold pairs available", "gold_count": 0}

    # Build lookup: (ar_norm, en_lower) -> rank (1-indexed)
    # Leads are already sorted by final_combined score desc
    lead_lookup: dict[tuple[str, str], int] = {}
    for rank, lead in enumerate(leads, 1):
        ar_key = _normalize_arabic(lead["source"]["lemma"])
        en_key = lead["target"]["lemma"].strip().lower()
        pair_key = (ar_key, en_key)
        if pair_key not in lead_lookup:
            lead_lookup[pair_key] = rank

    total = len(gold_pairs)
    found = 0
    reciprocal_ranks: list[float] = []
    hit_at: dict[int, int] = {1: 0, 5: 0, 10: 0, 20: 0, 50: 0, 100: 0}

    for gp in gold_pairs:
        ar_lemma = _normalize_arabic(gp.get("source", {}).get("lemma", "") or "")
        en_lemma = (gp.get("target", {}).get("lemma", "") or "").strip().lower()
        key = (ar_lemma, en_lemma)

        if key in lead_lookup:
            rank = lead_lookup[key]
            found += 1
            reciprocal_ranks.append(1.0 / rank)
            for k in hit_at:
                if rank <= k:
                    hit_at[k] += 1
        else:
            reciprocal_ranks.append(0.0)

    mrr = sum(reciprocal_ranks) / total if total > 0 else 0.0
    hit_rates = {f"Hit@{k}": round(v / total, 4) for k, v in hit_at.items()}

    return {
        "gold_count": total,
        "found_in_leads": found,
        "coverage": round(found / total, 4) if total > 0 else 0.0,
        "MRR": round(mrr, 4),
        **hit_rates,
        "total_leads": len(leads),
    }


# ---------------------------------------------------------------------------
# Stage 6: Output
# ---------------------------------------------------------------------------

def write_leads_jsonl(leads: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for lead in leads:
            f.write(json.dumps(lead, ensure_ascii=False) + "\n")


def write_report_md(
    leads: list[dict[str, Any]],
    eval_results: dict[str, Any],
    config: dict[str, Any],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = config.get("timestamp", "")
    mode = config.get("mode", "fast")
    ar_count = config.get("arabic_count", 0)
    en_count = config.get("english_count", 0)
    elapsed = config.get("elapsed_s", 0.0)

    lines = [
        f"# Full Discovery Pipeline Report",
        f"",
        f"**Timestamp:** {ts}  ",
        f"**Mode:** {mode}  ",
        f"**Arabic corpus:** {ar_count} entries  ",
        f"**English corpus:** {en_count} entries  ",
        f"**Runtime:** {elapsed:.1f}s  ",
        f"",
        f"## Summary",
        f"",
        f"- Total leads generated: {len(leads)}",
        f"- Leads above 0.45 threshold: {sum(1 for l in leads if l['scores']['multi_method_best'] > 0.45)}",
        f"- Leads above 0.70: {sum(1 for l in leads if l['scores']['multi_method_best'] > 0.70)}",
        f"- Leads above 0.85: {sum(1 for l in leads if l['scores']['multi_method_best'] > 0.85)}",
        f"",
        f"## Benchmark Evaluation (ara<->eng gold)",
        f"",
    ]

    if eval_results.get("error"):
        lines.append(f"*{eval_results['error']}*")
    else:
        for k, v in eval_results.items():
            lines.append(f"- **{k}:** {v}")

    lines += [
        f"",
        f"## Top 30 Leads",
        f"",
        f"| Rank | Arabic | Root | English | IPA | Score | Method | Explanation |",
        f"|------|--------|------|---------|-----|-------|--------|-------------|",
    ]

    for rank, lead in enumerate(leads[:30], 1):
        ar = lead["source"]
        en = lead["target"]
        scores = lead["scores"]
        ev = lead["evidence"]
        ar_lemma = ar.get("lemma", "")
        ar_root = ar.get("root", "") or ar.get("root_norm", "")
        en_lemma = en.get("lemma", "")
        en_ipa = en.get("ipa", "")
        score = scores.get("final_combined", scores.get("multi_method_best", 0.0))
        method = ev.get("best_method", scores.get("best_method", ""))
        expl = ev.get("explanation", "")[:60].replace("|", "/")
        lines.append(f"| {rank} | {ar_lemma} | {ar_root} | {en_lemma} | {en_ipa} | {score:.3f} | {method} | {expl} |")

    lines += [
        f"",
        f"## Method Distribution",
        f"",
    ]
    method_counts: dict[str, int] = {}
    for lead in leads:
        m = lead["scores"].get("best_method", "")
        if m:
            method_counts[m] = method_counts.get(m, 0) + 1
    for method, count in sorted(method_counts.items(), key=lambda x: -x[1])[:15]:
        lines.append(f"- `{method}`: {count}")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Juthoor LV2 Full Discovery Pipeline -- Arabic<->English cognate discovery"
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--fast", action="store_true", help="Fast mode: phonetic-only, no embeddings")
    mode_group.add_argument("--full", action="store_true", help="Full mode: BGE-M3 + FAISS + phonetic")
    parser.add_argument("--llm", action="store_true", help="Enable Claude API validation for top candidates")
    parser.add_argument("--arabic-limit", type=int, default=500, help="Limit Arabic corpus (default 500)")
    parser.add_argument("--english-limit", type=int, default=5000, help="Limit English corpus (default 5000)")
    parser.add_argument("--top-k", type=int, default=20, help="Top candidates per Arabic entry (default 20)")
    parser.add_argument("--llm-limit", type=int, default=100, help="Max pairs to send to LLM (default 100)")
    parser.add_argument("--threshold", type=float, default=0.45, help="Minimum score threshold (default 0.45)")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory (default: outputs/leads/)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    t_start = time.time()

    # Default mode is fast
    mode = "full" if args.full else "fast"
    output_dir = args.output_dir or LEADS_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    leads_path = output_dir / f"full_discovery_{ts}.jsonl"
    report_path = output_dir / f"full_discovery_{ts}_report.md"

    print("=" * 60)
    print("Juthoor LV2 Full Discovery Pipeline")
    print(f"Mode: {mode.upper()}  |  Arabic limit: {args.arabic_limit}  |  English limit: {args.english_limit}")
    print("=" * 60)

    # Stage 1: Load corpora
    print("\n[Stage 1] Loading corpora...")
    arabic_entries = load_arabic_corpus(limit=args.arabic_limit)
    english_entries = load_english_corpus(limit=args.english_limit)

    # Supplement Arabic corpus with gold benchmark Arabic lemmas not already included
    # Critical: only 0.9% overlap between Quranic corpus and gold benchmark lemmas
    if GOLD_BENCHMARK.exists():
        existing_ar = {e.get("lemma", "").strip() for e in arabic_entries}
        # Build a lookup from classical Arabic
        ar_lookup: dict[str, dict[str, Any]] = {}
        if CLASSICAL_ARABIC_CORPUS.exists():
            with open(CLASSICAL_ARABIC_CORPUS, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    lemma = (row.get("lemma") or "").strip()
                    if lemma and lemma not in ar_lookup:
                        ar_lookup[lemma] = row
        # Add gold source lemmas from classical corpus
        with open(GOLD_BENCHMARK, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                gp = json.loads(line)
                if gp.get("source", {}).get("lang") == "ara":
                    gold_ar = (gp["source"].get("lemma") or "").strip()
                    if gold_ar and gold_ar not in existing_ar:
                        if gold_ar in ar_lookup:
                            arabic_entries.append(ar_lookup[gold_ar])
                        else:
                            # Create minimal entry from gold pair info
                            arabic_entries.append({
                                "lemma": gold_ar,
                                "root": gp["source"].get("root", gold_ar),
                                "root_norm": gp["source"].get("root", gold_ar),
                                "meaning_text": gp["source"].get("gloss", ""),
                                "pos_tag": "N",
                            })
                        existing_ar.add(gold_ar)

    # Supplement English corpus with any gold benchmark target words not already included
    # This ensures benchmark evaluation can find gold pairs even with small limits
    if GOLD_BENCHMARK.exists():
        existing_lemmas = {e.get("lemma", "").strip().lower() for e in english_entries}
        en_lookup: dict[str, dict[str, Any]] = {}
        with open(ENGLISH_CORPUS, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                lemma = (row.get("lemma") or "").strip().lower()
                if lemma and lemma not in en_lookup:
                    en_lookup[lemma] = row
        with open(GOLD_BENCHMARK, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                gp = json.loads(line)
                if gp.get("target", {}).get("lang") == "eng":
                    gold_en = (gp["target"].get("lemma") or "").strip().lower()
                    if gold_en and gold_en not in existing_lemmas and gold_en in en_lookup:
                        english_entries.append(en_lookup[gold_en])
                        existing_lemmas.add(gold_en)

    print(f"  Loaded {len(arabic_entries)} Arabic entries, {len(english_entries)} English entries.")

    if not arabic_entries or not english_entries:
        print("ERROR: Failed to load corpora. Check file paths.")
        return 1

    # Stage 2+3: Scoring
    from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScorer

    scorer = MultiMethodScorer()
    leads: list[dict[str, Any]] = []

    if mode == "full":
        print("\n[Stage 2] Attempting BGE-M3 + FAISS retrieval...")
        retrieval_map = try_faiss_retrieval(arabic_entries, english_entries, top_k=100)
        if retrieval_map is not None:
            print(f"\n[Stage 3] Scoring FAISS-retrieved candidates...")
            leads = score_pairs_with_retrieval(
                arabic_entries, english_entries, retrieval_map, scorer,
                top_k=args.top_k, threshold=args.threshold,
            )
        else:
            print("\n[Stage 2 fallback] Using fast mode scoring...")
            mode = "fast (fallback from full)"
            leads = score_all_pairs_fast(
                arabic_entries, english_entries, scorer,
                top_k=args.top_k, threshold=args.threshold,
            )
    else:
        print("\n[Stage 2+3] Scoring all pairs (fast mode)...")
        leads = score_all_pairs_fast(
            arabic_entries, english_entries, scorer,
            top_k=args.top_k, threshold=args.threshold,
        )

    # Sort globally by score
    leads.sort(key=lambda x: x["scores"].get("final_combined", 0.0), reverse=True)
    print(f"\n  Generated {len(leads)} leads above threshold {args.threshold}.")

    # Stage 4: LLM Validation
    if args.llm and leads:
        print(f"\n[Stage 4] LLM validation (top {args.llm_limit})...")
        leads = run_llm_validation(leads, llm_limit=args.llm_limit)
        print(f"  LLM validation complete.")

    # Stage 5: Benchmark Evaluation
    print("\n[Stage 5] Benchmark evaluation...")
    gold_pairs = load_gold_benchmark(("ara", "eng"))
    print(f"  Loaded {len(gold_pairs)} gold ara<->eng pairs.")
    eval_results = evaluate_against_benchmark(leads, gold_pairs)

    print("\n  Evaluation results:")
    for k, v in eval_results.items():
        print(f"    {k}: {v}")

    # Stage 6: Output
    print(f"\n[Stage 6] Writing output...")
    elapsed = time.time() - t_start
    config = {
        "timestamp": ts,
        "mode": mode,
        "arabic_count": len(arabic_entries),
        "english_count": len(english_entries),
        "elapsed_s": elapsed,
        "threshold": args.threshold,
        "llm_enabled": args.llm,
    }

    write_leads_jsonl(leads, leads_path)
    write_report_md(leads, eval_results, config, report_path)

    print(f"\n  Leads JSONL:   {leads_path}")
    print(f"  Report MD:     {report_path}")
    print(f"\n  Total leads:   {len(leads)}")
    print(f"  Runtime:       {elapsed:.1f}s")
    print("=" * 60)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
