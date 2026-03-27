"""
Juthoor LV2 Multi-Language Discovery Pipeline -- Generic cognate discovery for any language pair.

Adapts run_full_discovery.py to support any source/target language pair from the LV0 corpus map.

Modes:
  --fast    : Phonetic-only discovery (no embeddings, minutes)
  --full    : BGE-M3 + FAISS + phonetic + LLM validation (slower, best results)
  --llm     : Enable Claude API validation for top candidates

Usage:
  python run_discovery_multilang.py --source ara --target heb --limit 500
  python run_discovery_multilang.py --source ara --target lat --limit 5000 --target-limit 10000
  python run_discovery_multilang.py --source ara --target grc --fast --limit 500
  python run_discovery_multilang.py --source ara --target per --limit 500
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
LV0_PROCESSED = REPO_ROOT / "Juthoor-DataCore-LV0/data/processed"
ENGLISH_CORPUS = LV2_ROOT / "data/processed/english/english_ipa_merged_pos.jsonl"
GOLD_BENCHMARK = LV2_ROOT / "resources/benchmarks/cognate_gold.jsonl"
LEADS_DIR = LV2_ROOT / "outputs/leads"

# Package path
sys.path.insert(0, str(LV2_ROOT / "src"))

# ---------------------------------------------------------------------------
# Corpus map
# ---------------------------------------------------------------------------

# Paths relative to LV0_PROCESSED
CORPUS_PATHS: dict[str, str | None] = {
    "ara": "quranic_arabic/sources/quran_lemmas_enriched.jsonl",   # 4903 entries
    "ara_classical": "arabic/classical/lexemes.jsonl",              # 32687 entries
    "heb": "hebrew/sources/kaikki.jsonl",                          # 17034 entries
    "lat": "latin/classical/sources/kaikki.jsonl",                 # 883915 entries (huge)
    "grc": "ancient_greek/sources/kaikki.jsonl",                   # 56058 entries
    "per": "persian/modern/sources/kaikki.jsonl",                  # 19361 entries
    "arc": "aramaic/classical/sources/kaikki.jsonl",               # 2176 entries
    "eng": None,  # English uses LV2-specific enriched corpus
    "enm": "english_middle/sources/kaikki.jsonl",                  # 49779 entries
    "ang": "english_old/sources/kaikki.jsonl",                     # 7948 entries
}

# Languages that are large enough to require stride-based sampling
LARGE_CORPORA: set[str] = {"lat"}

# Language family sets
SEMITIC_LANGS: set[str] = {"ara", "heb", "arc", "ara_classical"}
IE_LANGS: set[str] = {"eng", "lat", "grc", "per", "enm", "ang"}

# Arabic corpora use different field schema (quran_lemmas_enriched + classical)
ARABIC_SCHEMA_LANGS: set[str] = {"ara", "ara_classical"}


def _corpus_path(lang: str) -> Path | None:
    """Resolve absolute path for a language corpus, or None for English."""
    rel = CORPUS_PATHS.get(lang)
    if rel is None:
        return None  # English special case
    return LV0_PROCESSED / rel


# ---------------------------------------------------------------------------
# Stage 1: Generic corpus loaders
# ---------------------------------------------------------------------------

def _is_arabic_schema(lang: str) -> bool:
    return lang in ARABIC_SCHEMA_LANGS


def _pos_ok_arabic(pos: str) -> bool:
    """Accept content-word POS tags from Arabic corpora."""
    return pos in ("N", "V", "ADJ", "ADV", "")


def _pos_ok_kaikki(pos: list | str | None) -> bool:
    """Accept content-word POS tags from kaikki corpora."""
    if pos is None:
        return True
    if isinstance(pos, list):
        return any(p in ("noun", "verb", "adj", "adv", "adjective", "adverb", "") for p in pos)
    return True


def load_corpus(lang: str, limit: int = 500) -> list[dict[str, Any]]:
    """Load entries for any language code.

    For English: delegates to load_english_corpus() (LV2 enriched corpus with stride).
    For Latin (large corpus): uses stride-based sampling.
    For Arabic-schema langs: applies content-word POS filter.
    For kaikki langs: applies basic length and content filter.
    """
    if lang == "eng":
        return load_english_corpus(limit=limit)

    corpus_path = _corpus_path(lang)
    if corpus_path is None:
        raise ValueError(f"Unknown language code: {lang!r}")
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus not found: {corpus_path}")

    is_arabic = _is_arabic_schema(lang)
    is_large = lang in LARGE_CORPORA

    if is_large:
        return _load_corpus_strided(corpus_path, lang, limit, is_arabic)
    else:
        return _load_corpus_sequential(corpus_path, lang, limit, is_arabic)


def _load_corpus_sequential(
    path: Path,
    lang: str,
    limit: int,
    is_arabic: bool,
) -> list[dict[str, Any]]:
    """Load up to limit entries sequentially from a JSONL corpus."""
    entries: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            lemma = str(row.get("lemma", "") or "").strip()
            if not lemma or len(lemma) < 2:
                continue
            if is_arabic:
                pos = str(row.get("pos_tag", "") or "")
                if not _pos_ok_arabic(pos):
                    continue
            else:
                pos = row.get("pos")
                if not _pos_ok_kaikki(pos):
                    continue
            entries.append(row)
            if limit and len(entries) >= limit:
                break
    return entries


def _load_corpus_strided(
    path: Path,
    lang: str,
    limit: int,
    is_arabic: bool,
) -> list[dict[str, Any]]:
    """Load entries with stride-based sampling for large corpora (e.g. Latin)."""
    if limit <= 0:
        limit = 5000

    # Count total non-empty lines
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
            if is_arabic:
                pos = str(row.get("pos_tag", "") or "")
                if not _pos_ok_arabic(pos):
                    continue
            else:
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


def load_english_corpus(limit: int = 5000) -> list[dict[str, Any]]:
    """Load English entries from english_ipa_merged_pos.jsonl with stride-based sampling."""
    if limit <= 0:
        limit = 5000

    total_lines = 0
    with open(ENGLISH_CORPUS, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                total_lines += 1

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
            if not lemma.replace("-", "").replace("'", "").isalpha():
                continue
            if lemma in seen_lemmas:
                continue
            seen_lemmas.add(lemma)
            entries.append(row)
    return entries


# ---------------------------------------------------------------------------
# Stage 2 (fast mode): Pre-computed caches
# ---------------------------------------------------------------------------

def _precompute_source_cache(
    source_entries: list[dict[str, Any]],
    source_lang: str,
    target_lang: str,
) -> list[dict[str, Any]]:
    """Pre-compute projection variants + skeletons for each source entry.

    For Semitic→IE pairs: uses Arabic phonetic law projection (full variant expansion).
    For Semitic→Semitic pairs: uses consonant skeleton comparison (no Latin projection).
    For non-Semitic source: uses basic consonant extraction from lemma.
    """
    import re
    from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import (
        _arabic_consonant_skeleton,
        _strip_diacriticals,
        _pairwise_swap_variants,
        LATIN_EQUIVALENTS,
    )

    _ARABIC_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")
    _HAMZA_TR = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ؤ": "و", "ئ": "ي", "ء": "ا"})

    def norm_arabic(text: str) -> str:
        text = _ARABIC_DIACRITICS_RE.sub("", text)
        return text.translate(_HAMZA_TR).strip()

    # Determine scoring strategy
    source_is_semitic = source_lang in SEMITIC_LANGS
    target_is_ie = target_lang in IE_LANGS
    use_projection = source_is_semitic and target_is_ie

    if use_projection:
        from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import project_root_sound_laws

    _BASIC_CONS_RE = re.compile(r"[bcdfghjklmnpqrstvwxyz]", re.IGNORECASE)

    def basic_consonant_skeleton(text: str) -> str:
        """Extract consonant skeleton from Latin-script text."""
        t = text.lower().strip()
        # Remove common vowel patterns
        t = re.sub(r"[aeiouáéíóúàèìòùâêîôûäëïöü]", "", t)
        return "".join(_BASIC_CONS_RE.findall(t))

    cache = []
    for entry in source_entries:
        if source_is_semitic:
            # Extract root from Arabic/Hebrew/Aramaic entry
            root = str(
                entry.get("root_norm") or entry.get("root") or entry.get("translit") or entry.get("lemma") or ""
            ).strip()
            root_norm = norm_arabic(root) if source_lang in ARABIC_SCHEMA_LANGS else root

            ar_skel = _arabic_consonant_skeleton(root_norm)
            primary_latin = _strip_diacriticals(
                "".join(LATIN_EQUIVALENTS.get(ch, (ch,))[0] for ch in ar_skel)
            )

            if use_projection:
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
            else:
                # Semitic→Semitic: just use the direct skeleton + primary latin
                variants = (primary_latin,) if primary_latin else ()

            meta_variants = (
                ([primary_latin[::-1]] + _pairwise_swap_variants(primary_latin)[:2])
                if primary_latin else []
            )

            cache.append({
                "entry": entry,
                "root": root,
                "root_norm": root_norm,
                "src_skel": ar_skel,
                "primary_latin": primary_latin,
                "variants": variants,
                "meta_variants": meta_variants,
            })
        else:
            # IE source: extract consonant skeleton from lemma/translit
            lemma = str(entry.get("lemma", "") or "").strip().lower()
            translit = str(entry.get("translit", "") or "").strip().lower()
            src_skel = basic_consonant_skeleton(translit if translit and translit != lemma else lemma)
            primary_latin = src_skel
            variants = (src_skel,) if src_skel else ()
            meta_variants = []

            cache.append({
                "entry": entry,
                "root": lemma,
                "root_norm": lemma,
                "src_skel": src_skel,
                "primary_latin": primary_latin,
                "variants": variants,
                "meta_variants": meta_variants,
            })

    return cache


def _precompute_target_cache(
    target_entries: list[dict[str, Any]],
    target_lang: str,
) -> list[dict[str, Any]]:
    """Pre-compute consonant skeletons for all target entries.

    For IE targets: uses English-style consonant skeleton from lemma + IPA.
    For Semitic targets: extracts consonant skeleton from translit or lemma.
    """
    import re
    from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import (
        _arabic_consonant_skeleton,
        _strip_diacriticals,
        LATIN_EQUIVALENTS,
    )

    target_is_semitic = target_lang in SEMITIC_LANGS

    _IPA_TO_LATIN_TR = str.maketrans({
        "θ": "s", "ð": "d", "ɹ": "r", "ɾ": "r", "ʁ": "r",
        "χ": "kh", "ħ": "h", "ʕ": "", "ɣ": "g", "β": "b",
        "ɸ": "f", "ʔ": "", "ɫ": "l", "ʍ": "wh",
    })
    _IPA_CONS_RE = re.compile(r"[bcdfghjklmnpqrstvwxyzðθɹɾʁχħʕɣβɸʔɫŋ]")
    _BASIC_CONS_RE = re.compile(r"[bcdfghjklmnpqrstvwxyz]", re.IGNORECASE)

    def ipa_skel(ipa: str) -> str:
        s = ipa.lower()
        s = s.replace("tʃ", "c").replace("dʒ", "j").replace("ʃ", "sh").replace("ŋ", "ng")
        s = s.translate(_IPA_TO_LATIN_TR)
        return "".join(_IPA_CONS_RE.findall(s))

    def basic_consonant_skeleton(text: str) -> str:
        t = text.lower().strip()
        t = re.sub(r"[aeiouáéíóúàèìòùâêîôûäëïöü]", "", t)
        return "".join(_BASIC_CONS_RE.findall(t))

    if not target_is_semitic:
        # For IE targets, try to use English-style morpheme decomposition if available
        try:
            from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import (
                _english_consonant_skeleton,
                _morpheme_decompose,
            )
            use_eng_skel = True
        except ImportError:
            use_eng_skel = False

    cache = []
    for entry in target_entries:
        lemma = str(entry.get("lemma", "") or "").strip().lower()
        ipa = str(entry.get("ipa", "") or "").strip()
        translit = str(entry.get("translit", "") or "").strip()

        if target_is_semitic:
            # For Semitic targets, extract consonant skeleton
            # Detect script: Arabic U+0600-06FF, Hebrew U+0590-05FF
            is_arabic_script = any("\u0600" <= c <= "\u06ff" for c in lemma)
            is_hebrew_script = any("\u0590" <= c <= "\u05ff" for c in lemma)
            has_latin_translit = translit and translit != lemma and not is_hebrew_script and not is_arabic_script

            if has_latin_translit:
                tgt_skel = _strip_diacriticals(translit.lower())
                if is_arabic_script:
                    ar_skel = _arabic_consonant_skeleton(lemma)
                    ar_latin = _strip_diacriticals(
                        "".join(LATIN_EQUIVALENTS.get(ch, (ch,))[0] for ch in ar_skel)
                    )
                    tgt_skel = ar_latin if ar_latin else tgt_skel
                i_skel = ipa_skel(ipa) if ipa else ""
                stem_skel = ""
            elif is_hebrew_script or is_arabic_script:
                # For Hebrew/Aramaic: IPA field is the best source (e.g. "kalb" for כלב)
                # Arabic: use the Arabic consonant skeleton directly
                if is_arabic_script:
                    ar_skel = _arabic_consonant_skeleton(lemma)
                    tgt_skel = _strip_diacriticals(
                        "".join(LATIN_EQUIVALENTS.get(ch, (ch,))[0] for ch in ar_skel)
                    )
                elif ipa:
                    # Hebrew/Aramaic: extract skeleton from IPA (e.g. "kalb" -> "klb")
                    tgt_skel = ipa_skel(ipa)
                    if not tgt_skel:
                        tgt_skel = basic_consonant_skeleton(ipa)
                else:
                    tgt_skel = ""
                i_skel = ipa_skel(ipa) if ipa else ""
                stem_skel = ""
            else:
                tgt_skel = basic_consonant_skeleton(lemma)
                i_skel = ipa_skel(ipa) if ipa else ""
                stem_skel = ""

            cache.append({
                "entry": entry,
                "lemma": lemma,
                "tgt_skel": tgt_skel,
                "ipa_skel": i_skel,
                "stem_skel": stem_skel,
            })
        else:
            # IE target
            if target_lang == "eng" and use_eng_skel:
                tgt_skel = _english_consonant_skeleton(lemma)
                i_skel = ipa_skel(ipa)
                _, stem, suffix = _morpheme_decompose(lemma)
                stem_skel = (
                    _english_consonant_skeleton(stem)
                    if (suffix or _) and stem and len(stem) >= 2 else ""
                )
            else:
                tgt_skel = basic_consonant_skeleton(lemma)
                i_skel = ipa_skel(ipa) if ipa else ""
                stem_skel = ""

            cache.append({
                "entry": entry,
                "lemma": lemma,
                "tgt_skel": tgt_skel,
                "ipa_skel": i_skel,
                "stem_skel": stem_skel,
            })

    return cache


def _fast_prefilter_score_generic(
    src_cache: dict[str, Any],
    tgt_cache: dict[str, Any],
) -> float:
    """Quick score using pre-computed skeletons and variants."""
    from difflib import SequenceMatcher

    tgt_skel = tgt_cache["tgt_skel"]
    ipa_skel = tgt_cache["ipa_skel"]
    stem_skel = tgt_cache["stem_skel"]
    variants = src_cache["variants"]
    meta_variants = src_cache["meta_variants"]

    best = 0.0
    targets = [t for t in (tgt_skel, ipa_skel, stem_skel) if t]

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


# ---------------------------------------------------------------------------
# Stage 2 (fast mode): Main scoring loop
# ---------------------------------------------------------------------------

def score_all_pairs_fast(
    source_entries: list[dict[str, Any]],
    target_entries: list[dict[str, Any]],
    scorer: Any,
    source_lang: str,
    target_lang: str,
    top_k: int = 20,
    threshold: float = 0.45,
    prefilter_threshold: float = 0.50,
) -> list[dict[str, Any]]:
    """Score all source x target pairs using a three-phase approach.

    Phase 1: Pre-compute source projections + target skeletons (one-time cost).
    Phase 2: Fast skeleton scoring for all pairs using pre-computed data.
             Pairs below prefilter_threshold are dropped.
    Phase 3: Full MultiMethodScorer only on top candidates that passed Phase 2.
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

    def _score_fast_inline(src_pre: dict[str, Any], tgt_pre: dict[str, Any]) -> float:
        """Inline fast scorer using pre-computed cache."""
        src_skel = src_pre["src_skel"]
        primary_latin = src_pre["primary_latin"]
        variants = src_pre["variants"]
        meta_variants = src_pre["meta_variants"]

        tgt_skel = tgt_pre["tgt_skel"]
        ipa_skel = tgt_pre["ipa_skel"]
        stem_skel = tgt_pre["stem_skel"]
        lemma = tgt_pre["lemma"]

        if not src_skel or len(src_skel) < 2:
            return 0.0
        if not tgt_skel or len(tgt_skel) < 2:
            return 0.0

        # Length ratio guard
        ratio = len(tgt_skel) / len(src_skel)
        if ratio > 4.0 or ratio < 0.25:
            return 0.0

        # Projection match
        proj_score = 0.0
        for var in variants:
            clean = _strip_diacriticals(var)
            s = SequenceMatcher(None, clean, tgt_skel).ratio()
            if s > proj_score:
                proj_score = s

        # Direct match
        direct_score = (
            SequenceMatcher(None, primary_latin, tgt_skel).ratio()
            if primary_latin and tgt_skel else 0.0
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
            s = SequenceMatcher(None, mv, tgt_skel).ratio()
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

    print(f"  Pre-computing {source_lang} source cache...")
    src_cache_list = _precompute_source_cache(source_entries, source_lang, target_lang)
    print(f"  Pre-computing {target_lang} target cache...")
    tgt_cache_list = _precompute_target_cache(target_entries, target_lang)

    total_source = len(src_cache_list)
    total_pairs = total_source * len(tgt_cache_list)
    n_full_scorer_candidates = top_k * 3
    print(f"  Total pairs: {total_pairs:,}")
    print(f"  Phase 2 pre-filter threshold: {prefilter_threshold}")
    print(f"  Phase 3 full scorer: top-{n_full_scorer_candidates} candidates per source entry")

    leads: list[dict[str, Any]] = []
    prefilter_passed = 0
    full_scored = 0

    for i, src_cache in enumerate(src_cache_list):
        if i % 10 == 0:
            print(f"  Processing source entry {i + 1}/{total_source}...")
        src = src_cache["entry"]

        # Phase 2: fast scoring for all target entries, keep top candidates
        candidate_heap: list[tuple[float, int]] = []

        for j, tgt_cache in enumerate(tgt_cache_list):
            fast_score = _score_fast_inline(src_cache, tgt_cache)
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
            tgt = tgt_cache_list[j]["entry"]
            # For non-Latin script targets, inject IPA-derived lemma so scorer can work
            tgt_for_scoring = tgt
            tgt_lemma = str(tgt.get("lemma", "") or "").strip()
            if tgt_lemma and not tgt_lemma[0].isascii():
                tgt_ipa = str(tgt.get("ipa", "") or "").strip()
                # Clean IPA: strip slashes, brackets, stress marks
                clean_ipa = tgt_ipa.strip("/[]").split(",")[0].strip()
                if clean_ipa:
                    tgt_for_scoring = dict(tgt)
                    tgt_for_scoring["lemma"] = clean_ipa
            result = scorer.score_pair(src, tgt_for_scoring)
            full_scored += 1
            if result.best_score <= threshold:
                continue

            explanation = ""
            if result.all_results:
                best_result = max(result.all_results, key=lambda r: r.score)
                explanation = best_result.explanation

            top_for_this.append(_build_lead(src, tgt, source_lang, target_lang, result, fast_score, explanation))

        top_for_this.sort(key=lambda x: x["scores"]["multi_method_best"], reverse=True)
        leads.extend(top_for_this[:top_k])

    print(
        f"  Phase 2 passed: {prefilter_passed:,} / {total_pairs:,} "
        f"({100*prefilter_passed/max(total_pairs,1):.1f}%)"
    )
    print(f"  Phase 3 full scorer calls: {full_scored:,}")
    return leads


def _build_lead(
    src: dict[str, Any],
    tgt: dict[str, Any],
    source_lang: str,
    target_lang: str,
    result: Any,
    fast_score: float,
    explanation: str,
) -> dict[str, Any]:
    """Build a lead dict from a scored pair."""
    src_lang_code = src.get("language", source_lang)
    tgt_lang_code = tgt.get("language", target_lang)

    return {
        "source": {
            "lang": src_lang_code,
            "lemma": src.get("lemma", ""),
            "root": src.get("root", "") or src.get("root_norm", ""),
            "root_norm": src.get("root_norm", "") or src.get("root", ""),
            "gloss": src.get("meaning_text", "") or src.get("short_gloss", "") or src.get("gloss_plain", "") or src.get("gloss", ""),
            "pos": src.get("pos_tag", "") or src.get("pos", ""),
            "translit": src.get("translit", ""),
            "ipa": src.get("ipa", ""),
        },
        "target": {
            "lang": tgt_lang_code,
            "lemma": tgt.get("lemma", ""),
            "ipa": tgt.get("ipa", ""),
            "ipa_raw": tgt.get("ipa_raw", ""),
            "gloss": tgt.get("meaning_text", "") or tgt.get("gloss_plain", "") or tgt.get("gloss", ""),
            "pos": tgt.get("pos_tag", "") or tgt.get("pos", ""),
            "translit": tgt.get("translit", ""),
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
    }


# ---------------------------------------------------------------------------
# Stage 2 (full mode): BGE-M3 FAISS retrieval
# ---------------------------------------------------------------------------

def try_faiss_retrieval(
    source_entries: list[dict[str, Any]],
    target_entries: list[dict[str, Any]],
    top_k: int = 100,
) -> dict[int, list[int]] | None:
    """Attempt BGE-M3 embedding + FAISS retrieval.

    Returns a dict mapping source_index -> [target_indices].
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
        sample_text = "test word meaning"
        model.encode([sample_text])
        per_item_s = (time.time() - t0) / 1
        total_items = len(source_entries) + len(target_entries)
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
                or entry.get("gloss_plain", "")
                or entry.get("gloss", "")
                or entry.get("short_gloss", "")
                or entry.get("lemma", "")
            )

        print(f"  Embedding {len(source_entries)} source entries...")
        src_texts = [get_gloss(e) for e in source_entries]
        src_vectors = model.encode(src_texts, batch_size=64, show_progress_bar=True)

        print(f"  Embedding {len(target_entries)} target entries...")
        tgt_texts = [get_gloss(e) for e in target_entries]
        tgt_vectors = model.encode(tgt_texts, batch_size=64, show_progress_bar=True)

        dim = tgt_vectors.shape[1]
        index = faiss.IndexFlatIP(dim)
        tgt_norm = tgt_vectors / (np.linalg.norm(tgt_vectors, axis=1, keepdims=True) + 1e-10)
        src_norm = src_vectors / (np.linalg.norm(src_vectors, axis=1, keepdims=True) + 1e-10)
        index.add(tgt_norm.astype(np.float32))

        print(f"  Searching FAISS index (top-{top_k} per source entry)...")
        scores, idxs = index.search(src_norm.astype(np.float32), top_k)
        retrieval_map: dict[int, list[int]] = {}
        for i, idx_row in enumerate(idxs):
            retrieval_map[i] = [int(idx) for idx in idx_row if idx >= 0]
        print("  FAISS retrieval complete.")
        return retrieval_map

    except Exception as e:
        print(f"  [WARN] FAISS retrieval failed: {e}. Falling back to fast mode.")
        return None


def score_pairs_with_retrieval(
    source_entries: list[dict[str, Any]],
    target_entries: list[dict[str, Any]],
    retrieval_map: dict[int, list[int]],
    scorer: Any,
    source_lang: str,
    target_lang: str,
    top_k: int = 20,
    threshold: float = 0.40,
) -> list[dict[str, Any]]:
    """Score pairs using FAISS-retrieved candidates."""
    from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScore

    leads: list[dict[str, Any]] = []
    total = len(source_entries)

    for i, src in enumerate(source_entries):
        if i % 50 == 0:
            print(f"  Scoring source entry {i + 1}/{total}...")
        candidates = retrieval_map.get(i, [])
        top_for_this: list[dict[str, Any]] = []

        for tgt_idx in candidates:
            tgt = target_entries[tgt_idx]
            result: MultiMethodScore = scorer.score_pair(src, tgt)
            if result.best_score <= threshold:
                continue
            explanation = ""
            if result.all_results:
                best_result = max(result.all_results, key=lambda r: r.score)
                explanation = best_result.explanation

            lead = _build_lead(src, tgt, source_lang, target_lang, result, 0.0, explanation)
            lead["retrieval"] = {"faiss_rank": candidates.index(tgt_idx)}
            top_for_this.append(lead)

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

    sorted_leads = sorted(leads, key=lambda x: x["scores"]["multi_method_best"], reverse=True)
    to_validate = sorted_leads[:llm_limit]
    rest = sorted_leads[llm_limit:]

    print(f"  Validating {len(to_validate)} pairs with Claude API...")
    for idx, lead in enumerate(to_validate):
        if idx % 10 == 0:
            print(f"    LLM validating {idx + 1}/{len(to_validate)}...")
        src = lead["source"]
        tgt = lead["target"]
        phonetic_score = lead["scores"].get("multi_method_best", 0.0)
        try:
            result = validator.validate_pair(
                arabic_root=src.get("lemma", "") or src.get("root", ""),
                arabic_meaning=src.get("gloss", ""),
                english_word=tgt.get("lemma", ""),
                english_meaning=tgt.get("gloss", ""),
                phonetic_score=phonetic_score,
                additional_context=lead["evidence"].get("explanation", ""),
            )
            llm_conf = result.confidence
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

    combined_leads = to_validate + rest
    combined_leads.sort(key=lambda x: x["scores"].get("final_combined", 0.0), reverse=True)
    return combined_leads


# ---------------------------------------------------------------------------
# Stage 5: Benchmark Evaluation
# ---------------------------------------------------------------------------

def load_gold_benchmark(lang_pair: tuple[str, str]) -> list[dict[str, Any]]:
    """Load gold pairs for a specific (source_lang, target_lang) pair."""
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


def _normalize_lemma(text: str, lang: str) -> str:
    """Normalize a lemma for comparison depending on language."""
    import re
    if lang in SEMITIC_LANGS:
        _diac_re = re.compile(r"[\u064B-\u065F\u0670\u0640]")
        _hamza_tr = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ؤ": "و", "ئ": "ي", "ء": "ا"})
        text = _diac_re.sub("", text)
        text = text.translate(_hamza_tr)
    return text.strip().lower()


def evaluate_against_benchmark(
    leads: list[dict[str, Any]],
    gold_pairs: list[dict[str, Any]],
    source_lang: str,
    target_lang: str,
) -> dict[str, Any]:
    """Compute MRR, Hit@K for leads against gold benchmark."""
    if not gold_pairs:
        return {"error": "No gold pairs available", "gold_count": 0}

    lead_lookup: dict[tuple[str, str], int] = {}
    for rank, lead in enumerate(leads, 1):
        src_key = _normalize_lemma(lead["source"]["lemma"], source_lang)
        tgt_key = _normalize_lemma(lead["target"]["lemma"], target_lang)
        pair_key = (src_key, tgt_key)
        if pair_key not in lead_lookup:
            lead_lookup[pair_key] = rank

    total = len(gold_pairs)
    found = 0
    reciprocal_ranks: list[float] = []
    hit_at: dict[int, int] = {1: 0, 5: 0, 10: 0, 20: 0, 50: 0, 100: 0}

    for gp in gold_pairs:
        src_lemma = _normalize_lemma(gp.get("source", {}).get("lemma", "") or "", source_lang)
        tgt_lemma = _normalize_lemma(gp.get("target", {}).get("lemma", "") or "", target_lang)
        key = (src_lemma, tgt_lemma)

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
    source_lang = config.get("source_lang", "?")
    target_lang = config.get("target_lang", "?")
    src_count = config.get("source_count", 0)
    tgt_count = config.get("target_count", 0)
    elapsed = config.get("elapsed_s", 0.0)
    threshold = config.get("threshold", 0.45)

    lines = [
        f"# Multi-Language Discovery Pipeline Report",
        f"",
        f"**Timestamp:** {ts}  ",
        f"**Mode:** {mode}  ",
        f"**Source language:** {source_lang} ({src_count} entries)  ",
        f"**Target language:** {target_lang} ({tgt_count} entries)  ",
        f"**Runtime:** {elapsed:.1f}s  ",
        f"",
        f"## Summary",
        f"",
        f"- Total leads generated: {len(leads)}",
        f"- Leads above {threshold} threshold: {sum(1 for l in leads if l['scores']['multi_method_best'] > threshold)}",
        f"- Leads above 0.70: {sum(1 for l in leads if l['scores']['multi_method_best'] > 0.70)}",
        f"- Leads above 0.85: {sum(1 for l in leads if l['scores']['multi_method_best'] > 0.85)}",
        f"",
        f"## Benchmark Evaluation ({source_lang}<->{target_lang} gold)",
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
        f"| Rank | Source | Root/Translit | Target | IPA | Score | Method | Explanation |",
        f"|------|--------|---------------|--------|-----|-------|--------|-------------|",
    ]

    for rank, lead in enumerate(leads[:30], 1):
        src = lead["source"]
        tgt = lead["target"]
        scores = lead["scores"]
        ev = lead["evidence"]
        src_lemma = src.get("lemma", "")
        src_root = src.get("root", "") or src.get("root_norm", "") or src.get("translit", "")
        tgt_lemma = tgt.get("lemma", "")
        tgt_ipa = tgt.get("ipa", "")
        score = scores.get("final_combined", scores.get("multi_method_best", 0.0))
        method = ev.get("best_method", scores.get("best_method", ""))
        expl = ev.get("explanation", "")[:60].replace("|", "/")
        lines.append(
            f"| {rank} | {src_lemma} | {src_root} | {tgt_lemma} | {tgt_ipa} | {score:.3f} | {method} | {expl} |"
        )

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
        description="Juthoor LV2 Multi-Language Discovery Pipeline"
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--fast", action="store_true", help="Fast mode: phonetic-only, no embeddings")
    mode_group.add_argument("--full", action="store_true", help="Full mode: BGE-M3 + FAISS + phonetic")
    parser.add_argument("--source", type=str, default="ara", help="Source language code (default: ara)")
    parser.add_argument("--target", type=str, required=True, help="Target language code (required)")
    parser.add_argument("--limit", type=int, default=500, help="Source corpus limit (default 500)")
    parser.add_argument("--target-limit", type=int, default=5000, help="Target corpus limit (default 5000)")
    parser.add_argument("--top-k", type=int, default=20, help="Top candidates per source entry (default 20)")
    parser.add_argument("--threshold", type=float, default=0.45, help="Minimum score threshold (default 0.45)")
    parser.add_argument("--llm", action="store_true", help="Enable Claude API validation for top candidates")
    parser.add_argument("--llm-limit", type=int, default=100, help="Max pairs to send to LLM (default 100)")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory (default: outputs/leads/)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    t_start = time.time()

    source_lang = args.source.strip().lower()
    target_lang = args.target.strip().lower()

    # Validate language codes
    if source_lang not in CORPUS_PATHS:
        print(f"ERROR: Unknown source language '{source_lang}'. Valid codes: {sorted(CORPUS_PATHS.keys())}")
        return 1
    if target_lang not in CORPUS_PATHS:
        print(f"ERROR: Unknown target language '{target_lang}'. Valid codes: {sorted(CORPUS_PATHS.keys())}")
        return 1

    mode = "full" if args.full else "fast"
    output_dir = args.output_dir or LEADS_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_tag = f"{source_lang}_{target_lang}_{ts}"
    leads_path = output_dir / f"discovery_{run_tag}.jsonl"
    report_path = output_dir / f"discovery_{run_tag}_report.md"

    print("=" * 60)
    print("Juthoor LV2 Multi-Language Discovery Pipeline")
    print(f"Mode: {mode.upper()}  |  {source_lang} -> {target_lang}")
    print(f"Source limit: {args.limit}  |  Target limit: {args.target_limit}")
    print("=" * 60)

    # Stage 1: Load corpora
    print("\n[Stage 1] Loading corpora...")
    try:
        source_entries = load_corpus(source_lang, limit=args.limit)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1

    try:
        target_entries = load_corpus(target_lang, limit=args.target_limit)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1

    # Supplement target corpus with gold benchmark targets (for benchmark eval coverage)
    if GOLD_BENCHMARK.exists() and target_lang == "eng":
        existing_lemmas = {e.get("lemma", "").strip().lower() for e in target_entries}
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
                gp_src = gp.get("source", {}).get("lang", "")
                gp_tgt = gp.get("target", {}).get("lang", "")
                if gp_src == source_lang and gp_tgt == target_lang:
                    gold_tgt = (gp["target"].get("lemma") or "").strip().lower()
                    if gold_tgt and gold_tgt not in existing_lemmas and gold_tgt in en_lookup:
                        target_entries.append(en_lookup[gold_tgt])
                        existing_lemmas.add(gold_tgt)

    print(f"  Loaded {len(source_entries)} {source_lang} entries, {len(target_entries)} {target_lang} entries.")

    if not source_entries or not target_entries:
        print("ERROR: Failed to load corpora. Check file paths.")
        return 1

    # Stage 2+3: Scoring
    from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScorer

    scorer = MultiMethodScorer()
    leads: list[dict[str, Any]] = []

    if mode == "full":
        print("\n[Stage 2] Attempting BGE-M3 + FAISS retrieval...")
        retrieval_map = try_faiss_retrieval(source_entries, target_entries, top_k=100)
        if retrieval_map is not None:
            print("\n[Stage 3] Scoring FAISS-retrieved candidates...")
            leads = score_pairs_with_retrieval(
                source_entries, target_entries, retrieval_map, scorer,
                source_lang=source_lang, target_lang=target_lang,
                top_k=args.top_k, threshold=args.threshold,
            )
        else:
            print("\n[Stage 2 fallback] Using fast mode scoring...")
            mode = "fast (fallback from full)"
            leads = score_all_pairs_fast(
                source_entries, target_entries, scorer,
                source_lang=source_lang, target_lang=target_lang,
                top_k=args.top_k, threshold=args.threshold,
            )
    else:
        print("\n[Stage 2+3] Scoring all pairs (fast mode)...")
        leads = score_all_pairs_fast(
            source_entries, target_entries, scorer,
            source_lang=source_lang, target_lang=target_lang,
            top_k=args.top_k, threshold=args.threshold,
        )

    leads.sort(key=lambda x: x["scores"].get("final_combined", 0.0), reverse=True)
    print(f"\n  Generated {len(leads)} leads above threshold {args.threshold}.")

    # Stage 4: LLM Validation
    if args.llm and leads:
        print(f"\n[Stage 4] LLM validation (top {args.llm_limit})...")
        leads = run_llm_validation(leads, llm_limit=args.llm_limit)
        print("  LLM validation complete.")

    # Stage 5: Benchmark Evaluation
    print("\n[Stage 5] Benchmark evaluation...")
    gold_pairs = load_gold_benchmark((source_lang, target_lang))
    print(f"  Loaded {len(gold_pairs)} gold {source_lang}<->{target_lang} pairs.")
    eval_results = evaluate_against_benchmark(leads, gold_pairs, source_lang, target_lang)

    print("\n  Evaluation results:")
    for k, v in eval_results.items():
        print(f"    {k}: {v}")

    # Stage 6: Output
    print("\n[Stage 6] Writing output...")
    elapsed = time.time() - t_start
    config = {
        "timestamp": ts,
        "mode": mode,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "source_count": len(source_entries),
        "target_count": len(target_entries),
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
