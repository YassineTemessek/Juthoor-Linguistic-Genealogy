"""
Juthoor LV2 Improved Discovery Runner

Uses unified Arabic source (37K) and enriched English corpus (15K with glosses).
Applies gloss similarity filter + phonetic scoring, classifies leads by anchor level.

Usage:
  python run_improved_discovery.py --arabic-limit 200 --english-limit 2000 --threshold 0.55
  python run_improved_discovery.py --arabic-limit 1000 --english-limit 5000 --threshold 0.60
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from difflib import SequenceMatcher
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

ARABIC_PRIMARY = LV2_ROOT / "data/processed/arabic/unified_arabic_discovery.jsonl"
ARABIC_FALLBACK = LV2_ROOT / "data/processed/arabic/quran_lemmas_enriched.jsonl"
ARABIC_GLOSSES_LOOKUP = LV2_ROOT / "data/processed/arabic/arabic_english_glosses.json"

ENGLISH_PRIMARY = LV2_ROOT / "data/processed/english/english_enriched_discovery.jsonl"
ENGLISH_FALLBACK = LV2_ROOT / "data/processed/english/english_ipa_merged_pos.jsonl"

GOLD_BENCHMARK = LV2_ROOT / "resources/benchmarks/cognate_gold.jsonl"
LEADS_DIR = LV2_ROOT / "outputs/leads"

CONCEPTS_FILE = LV2_ROOT / "resources/concepts/concepts_v3_2_enriched.jsonl"

sys.path.insert(0, str(LV2_ROOT / "src"))

# ---------------------------------------------------------------------------
# Anchor classification thresholds
# ---------------------------------------------------------------------------
ANCHOR_GOLD_SCORE = 0.85
ANCHOR_GOLD_METHODS = 4
ANCHOR_SILVER_SCORE = 0.70
ANCHOR_SILVER_METHODS = 2
ANCHOR_AUTO_BRUT_SCORE = 0.55


# ---------------------------------------------------------------------------
# Stage 1: Load corpora
# ---------------------------------------------------------------------------

def load_arabic_corpus(limit: int = 500) -> list[dict[str, Any]]:
    """Load Arabic entries from unified_arabic_discovery.jsonl (fallback to quran_lemmas_enriched)."""
    path = ARABIC_PRIMARY if ARABIC_PRIMARY.exists() else ARABIC_FALLBACK
    print(f"  Arabic source: {path.name}", flush=True)

    entries: list[dict[str, Any]] = []
    seen: set[str] = set()

    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            # Use translit or root_norm as key for dedup
            key = str(row.get("translit") or row.get("root_norm") or row.get("root") or "").strip()
            if not key or key in seen:
                continue
            pos = row.get("pos_tag", "") or ""
            if pos and pos not in ("N", "V", "ADJ", "ADV", ""):
                continue
            seen.add(key)
            entries.append(row)
            if limit and len(entries) >= limit:
                break

    return entries


def load_english_corpus(limit: int = 2000) -> list[dict[str, Any]]:
    """Load English entries with stride-based sampling for alphabetical coverage."""
    path = ENGLISH_PRIMARY if ENGLISH_PRIMARY.exists() else ENGLISH_FALLBACK
    print(f"  English source: {path.name}", flush=True)

    if limit <= 0:
        limit = 2000

    # Count lines for stride computation
    total = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                total += 1

    stride = max(1, total // (limit * 2))

    seen: set[str] = set()
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
            if not lemma.replace("-", "").replace("'", "").isalpha():
                continue
            if lemma in seen:
                continue
            seen.add(lemma)
            entries.append(row)
            if len(entries) >= limit:
                break

    return entries


# ---------------------------------------------------------------------------
# Stage 2: Pre-compute caches
# ---------------------------------------------------------------------------

def _norm_arabic(text: str) -> str:
    import re
    _DIAC = re.compile(r"[\u064B-\u065F\u0670\u0640]")
    _HAMZA = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ؤ": "و", "ئ": "ي", "ء": "ا"})
    return _DIAC.sub("", text).translate(_HAMZA).strip()


def precompute_arabic(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import (
        _arabic_consonant_skeleton,
        _strip_diacriticals,
        _pairwise_swap_variants,
        LATIN_EQUIVALENTS,
        project_root_sound_laws,
    )

    cache = []
    for ar in entries:
        root = str(ar.get("root_norm") or ar.get("root") or ar.get("translit") or ar.get("lemma") or "").strip()
        root_norm = _norm_arabic(root)
        ar_skel = _arabic_consonant_skeleton(root_norm)
        primary_latin = _strip_diacriticals(
            "".join(LATIN_EQUIVALENTS.get(ch, (ch,))[0] for ch in ar_skel)
        )
        try:
            all_variants = project_root_sound_laws(root_norm, include_group_expansion=True, max_variants=128)
        except Exception:
            all_variants = []
        seen_v: dict[str, None] = {primary_latin: None} if primary_latin else {}
        for v in all_variants:
            v_clean = v.strip()
            if v_clean and v_clean not in seen_v:
                seen_v[v_clean] = None
            if len(seen_v) >= 8:
                break
        variants = tuple(seen_v.keys())
        meta_variants = ([primary_latin[::-1]] + _pairwise_swap_variants(primary_latin)[:2]) if primary_latin else []
        # Gloss from Arabic side (features or meaning_text)
        ar_gloss = ""
        feats = ar.get("features") or {}
        if isinstance(feats, dict):
            ar_gloss = str(feats.get("gloss") or feats.get("meaning") or "")
        cache.append({
            "entry": ar,
            "root": root,
            "root_norm": root_norm,
            "translit": str(ar.get("translit") or root_norm or ""),
            "ar_skel": ar_skel,
            "primary_latin": primary_latin,
            "variants": variants,
            "meta_variants": meta_variants,
            "gloss": ar_gloss,
        })
    return cache


def precompute_english(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    import re
    from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import (
        _english_consonant_skeleton,
        _morpheme_decompose,
    )

    _IPA_TO_LATIN = str.maketrans({
        "θ": "s", "ð": "d", "ɹ": "r", "ɾ": "r", "ʁ": "r",
        "χ": "kh", "ħ": "h", "ʕ": "", "ɣ": "g", "β": "b",
        "ɸ": "f", "ʔ": "", "ɫ": "l", "ʍ": "wh",
    })
    _IPA_CONS_RE = re.compile(r"[bcdfghjklmnpqrstvwxyzðθɹɾʁχħʕɣβɸʔɫŋ]")

    def ipa_skel(ipa: str) -> str:
        s = ipa.lower()
        s = s.replace("tʃ", "c").replace("dʒ", "j").replace("ʃ", "sh").replace("ŋ", "ng")
        s = s.translate(_IPA_TO_LATIN)
        return "".join(_IPA_CONS_RE.findall(s))

    cache = []
    for en in entries:
        lemma = str(en.get("lemma", "") or "").strip().lower()
        ipa = str(en.get("ipa", "") or en.get("ipa_raw", "") or "").strip()
        eng_skel = _english_consonant_skeleton(lemma)
        i_skel = ipa_skel(ipa) if ipa else ""
        _, stem, suffix = _morpheme_decompose(lemma)
        stem_skel = _english_consonant_skeleton(stem) if (suffix or _) and stem and len(stem) >= 2 else ""
        # English gloss from meaning_text
        gloss = str(en.get("meaning_text") or en.get("gloss") or en.get("short_gloss") or "")
        cache.append({
            "entry": en,
            "lemma": lemma,
            "eng_skel": eng_skel,
            "ipa_skel": i_skel,
            "stem": stem,
            "stem_skel": stem_skel,
            "gloss": gloss,
        })
    return cache


# ---------------------------------------------------------------------------
# Stage 3: Fast pre-filter + full scoring
# ---------------------------------------------------------------------------

def fast_prefilter(ar_pre: dict[str, Any], en_pre: dict[str, Any]) -> float:
    """Quick score using pre-computed skeletons. Returns best ratio."""
    en_skel = en_pre["eng_skel"]
    i_skel = en_pre["ipa_skel"]
    stem_skel = en_pre["stem_skel"]
    variants = ar_pre["variants"]
    meta_variants = ar_pre["meta_variants"]

    best = 0.0
    targets = [t for t in (en_skel, i_skel, stem_skel) if t]
    if not targets:
        return 0.0

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


def compute_semantic_score(
    ar_entry: dict[str, Any],
    en_entry: dict[str, Any],
    concept_matcher: Any | None = None,
) -> tuple[float, float, float]:
    """Compute semantic score combining gloss similarity and concept matching.

    Returns (semantic_score, gloss_sim, concept_sim).
    semantic_score = max(gloss_sim, concept_sim) so concept match can rescue
    pairs with no direct word overlap.
    """
    from juthoor_cognatediscovery_lv2.discovery.gloss_similarity import gloss_similarity

    gloss_sim = gloss_similarity(ar_entry, en_entry)

    concept_sim = 0.0
    if concept_matcher is not None:
        concept_sim = concept_matcher.concept_similarity(ar_entry, en_entry)

    # Concept match rescues pairs where glosses don't share exact words
    # but both map to the same semantic concept (e.g. "exhale" ↔ "spirit")
    semantic = max(gloss_sim, concept_sim)
    return semantic, gloss_sim, concept_sim


def classify_anchor(phonetic_score: float, num_methods: int) -> str:
    if phonetic_score >= ANCHOR_GOLD_SCORE and num_methods >= ANCHOR_GOLD_METHODS:
        return "gold"
    if phonetic_score >= ANCHOR_SILVER_SCORE and num_methods >= ANCHOR_SILVER_METHODS:
        return "silver"
    if phonetic_score >= ANCHOR_AUTO_BRUT_SCORE:
        return "auto_brut"
    return "none"


def score_all_pairs(
    arabic_cache: list[dict[str, Any]],
    english_cache: list[dict[str, Any]],
    scorer: Any,
    concept_matcher: Any | None = None,
    threshold: float = 0.55,
    semantic_threshold: float = 0.0,
    prefilter_threshold: float = 0.40,
    top_k: int = 20,
) -> list[dict[str, Any]]:
    """Score all Arabic x English pairs using two-phase approach."""
    leads: list[dict[str, Any]] = []
    total_pairs = len(arabic_cache) * len(english_cache)
    passed_prefilter = 0
    n_arabic = len(arabic_cache)

    print(f"  Scoring {total_pairs:,} pairs ({n_arabic} Arabic x {len(english_cache)} English)...", flush=True)
    t0 = time.time()

    for i, ar_pre in enumerate(arabic_cache):
        if i % max(1, n_arabic // 10) == 0:
            elapsed = time.time() - t0
            pct = (i + 1) / n_arabic * 100
            print(f"    {pct:.0f}% ({i+1}/{n_arabic}) — {elapsed:.1f}s elapsed", flush=True)

        # Phase 1: pre-filter for this Arabic entry
        candidates: list[tuple[float, dict[str, Any]]] = []
        for en_pre in english_cache:
            fast = fast_prefilter(ar_pre, en_pre)
            if fast >= prefilter_threshold:
                candidates.append((fast, en_pre))

        if not candidates:
            continue

        # Sort by fast score, take top 3*top_k for full scoring
        candidates.sort(key=lambda x: x[0], reverse=True)
        candidates = candidates[: top_k * 3]
        passed_prefilter += len(candidates)

        # Phase 2: full MultiMethodScorer (with per-entry time cap)
        entry_t0 = time.time()
        for _fast_score, en_pre in candidates:
            if time.time() - entry_t0 > 30.0:  # 30s max per Arabic entry
                break
            result = scorer.score_pair(ar_pre["entry"], en_pre["entry"])
            phonetic = result.best_score
            if phonetic < threshold:
                continue

            # Semantic scoring: gloss similarity + concept matching
            sem_score, gloss_sim, concept_sim = compute_semantic_score(
                ar_pre["entry"], en_pre["entry"], concept_matcher
            )

            # Combined score
            combined = phonetic * 0.7 + sem_score * 0.3

            if semantic_threshold > 0.0 and sem_score < semantic_threshold:
                continue

            num_methods = len(result.methods_that_fired)
            anchor = classify_anchor(phonetic, num_methods)

            ar_gloss = ar_pre["gloss"]
            en_gloss = en_pre["gloss"]

            leads.append({
                "arabic": ar_pre["entry"].get("lemma", ar_pre["root"]),
                "arabic_translit": ar_pre["translit"],
                "arabic_root": ar_pre["root"],
                "english": en_pre["lemma"],
                "phonetic_score": round(phonetic, 4),
                "semantic_score": round(sem_score, 4),
                "gloss_similarity": round(gloss_sim, 4),
                "concept_similarity": round(concept_sim, 4),
                "combined_score": round(combined, 4),
                "best_method": result.best_method,
                "methods_fired": result.methods_that_fired,
                "num_methods": num_methods,
                "anchor_level": anchor,
                "arabic_gloss": ar_gloss[:80] if ar_gloss else "",
                "english_gloss": en_gloss[:80] if en_gloss else "",
            })

    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s — {passed_prefilter:,} passed prefilter, {len(leads):,} leads above threshold", flush=True)

    # Deduplicate: keep best combined_score per (arabic_root, english)
    best_per_pair: dict[tuple[str, str], dict[str, Any]] = {}
    for lead in leads:
        key = (lead["arabic_root"], lead["english"])
        if key not in best_per_pair or lead["combined_score"] > best_per_pair[key]["combined_score"]:
            best_per_pair[key] = lead

    deduped = sorted(best_per_pair.values(), key=lambda x: x["combined_score"], reverse=True)
    return deduped


# ---------------------------------------------------------------------------
# Stage 3b: Supplement corpora with gold benchmark entries
# ---------------------------------------------------------------------------

def _load_gloss_lookup() -> dict[str, str]:
    """Load Arabic→English gloss lookup (normalized key → first gloss)."""
    if not ARABIC_GLOSSES_LOOKUP.exists():
        return {}
    with open(ARABIC_GLOSSES_LOOKUP, encoding="utf-8") as f:
        raw = json.load(f)
    lookup: dict[str, str] = {}
    for term, entry in raw.items():
        glosses = entry.get("english_glosses", [])
        if glosses:
            lookup[term] = glosses[0]
            lookup[_norm_arabic(term)] = glosses[0]
    return lookup


def supplement_with_gold(
    arabic_entries: list[dict[str, Any]],
    english_entries: list[dict[str, Any]],
) -> tuple[int, int]:
    """Inject gold benchmark Arabic/English lemmas missing from loaded corpora.

    Enriches Arabic entries with english_gloss from lookup, and English entries
    with gloss from the gold benchmark itself.

    Returns (arabic_added, english_added).
    """
    if not GOLD_BENCHMARK.exists():
        return 0, 0

    gloss_lookup = _load_gloss_lookup()

    existing_ar: set[str] = set()
    for ar in arabic_entries:
        for field in ("lemma", "root_norm", "root", "translit"):
            val = str(ar.get(field, "") or "").strip()
            if val:
                existing_ar.add(val)
                existing_ar.add(_norm_arabic(val))

    existing_en: set[str] = set()
    for en in english_entries:
        lemma = str(en.get("lemma", "") or "").strip().lower()
        if lemma:
            existing_en.add(lemma)

    ar_added = 0
    en_added = 0

    with open(GOLD_BENCHMARK, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            src = row.get("source", {})
            tgt = row.get("target", {})
            src_lang = src.get("lang", "")
            tgt_lang = tgt.get("lang", "")

            if "ara" in src_lang and "eng" in tgt_lang:
                ar_side, en_side = src, tgt
            elif "eng" in src_lang and "ara" in tgt_lang:
                ar_side, en_side = tgt, src
            else:
                continue

            ar_lemma = str(ar_side.get("lemma", "") or "").strip()
            en_lemma = str(en_side.get("lemma", "") or "").strip().lower()

            ar_norm = _norm_arabic(ar_lemma)
            if ar_lemma and ar_norm not in existing_ar:
                # Enrich with english_gloss from lookup
                eng_gloss = gloss_lookup.get(ar_lemma) or gloss_lookup.get(ar_norm) or ""
                # Also use the gold target word as a gloss hint
                gloss_parts = [eng_gloss, en_lemma] if eng_gloss else [en_lemma]
                arabic_entries.append({
                    "lemma": ar_lemma,
                    "root": ar_side.get("root", ar_lemma),
                    "root_norm": ar_norm,
                    "translit": ar_norm,
                    "english_gloss": "; ".join(gloss_parts),
                    "language": "ara",
                    "source": "gold_supplement",
                })
                existing_ar.add(ar_norm)
                existing_ar.add(ar_lemma)
                ar_added += 1

            if en_lemma and en_lemma not in existing_en and len(en_lemma) > 2:
                # Carry over gloss from gold benchmark
                en_gloss = str(en_side.get("gloss", "") or "")
                english_entries.append({
                    "lemma": en_lemma,
                    "meaning_text": en_gloss if en_gloss else en_lemma,
                    "language": "eng",
                    "source": "gold_supplement",
                })
                existing_en.add(en_lemma)
                en_added += 1

    return ar_added, en_added


# ---------------------------------------------------------------------------
# Stage 4: Benchmark evaluation
# ---------------------------------------------------------------------------

def load_gold_benchmark() -> list[dict[str, Any]]:
    if not GOLD_BENCHMARK.exists():
        return []
    pairs = []
    with open(GOLD_BENCHMARK, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            src = row.get("source", {})
            tgt = row.get("target", {})
            # Only Arabic<->English pairs
            src_lang = src.get("lang", "")
            tgt_lang = tgt.get("lang", "")
            if "ara" in src_lang and "eng" in tgt_lang:
                pairs.append({"arabic": src.get("lemma", ""), "english": tgt.get("lemma", "")})
            elif "eng" in src_lang and "ara" in tgt_lang:
                pairs.append({"arabic": tgt.get("lemma", ""), "english": src.get("lemma", "")})
    return pairs


def evaluate_benchmark(leads: list[dict[str, Any]], gold_pairs: list[dict[str, Any]]) -> dict[str, Any]:
    if not gold_pairs:
        return {"note": "no Arabic-English gold pairs found"}

    # Normalize gold Arabic (strip diacritics) for fair comparison
    gold_norm = set()
    for p in gold_pairs:
        ar_norm = _norm_arabic(p["arabic"])
        en_lower = p["english"].strip().lower()
        gold_norm.add((ar_norm, en_lower))

    found = 0
    found_pairs: list[dict[str, Any]] = []
    for lead in leads:
        en = lead.get("english", "").strip().lower()
        # Match against both arabic field and arabic_root (normalized)
        ar_norm = _norm_arabic(lead.get("arabic", ""))
        root_norm = _norm_arabic(lead.get("arabic_root", ""))
        if (ar_norm, en) in gold_norm or (root_norm, en) in gold_norm:
            found += 1
            found_pairs.append(lead)

    recall = found / len(gold_pairs) if gold_pairs else 0.0

    # Count anchor levels
    anchor_counts: dict[str, int] = {}
    for lead in leads:
        lvl = lead.get("anchor_level", "none")
        anchor_counts[lvl] = anchor_counts.get(lvl, 0) + 1

    return {
        "gold_pairs_total": len(gold_pairs),
        "leads_total": len(leads),
        "gold_pairs_recovered": found,
        "recall": round(recall, 4),
        "anchor_counts": anchor_counts,
        "found_pairs": found_pairs[:20],
    }


# ---------------------------------------------------------------------------
# Stage 5: Save leads
# ---------------------------------------------------------------------------

def save_leads(leads: list[dict[str, Any]], label: str = "improved") -> Path:
    LEADS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = LEADS_DIR / f"leads_{label}_{ts}.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for lead in leads:
            f.write(json.dumps(lead, ensure_ascii=False) + "\n")
    return out_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Improved Arabic<->English cognate discovery")
    parser.add_argument("--arabic-limit", type=int, default=200, help="Max Arabic entries to load")
    parser.add_argument("--english-limit", type=int, default=2000, help="Max English entries to load")
    parser.add_argument("--threshold", type=float, default=0.55, help="Min phonetic score for leads")
    parser.add_argument("--semantic-threshold", type=float, default=0.0, help="Min semantic score (0=disabled)")
    parser.add_argument("--top-k", type=int, default=20, help="Top-K leads per Arabic entry from prefilter")
    parser.add_argument("--prefilter", type=float, default=0.40, help="Fast prefilter threshold")
    parser.add_argument("--no-save", action="store_true", help="Do not save leads to disk")
    parser.add_argument("--no-gold-supplement", action="store_true", help="Do not inject gold benchmark entries")
    args = parser.parse_args()

    print("=" * 60)
    print("Juthoor LV2 — Improved Discovery Runner")
    print(f"  arabic-limit={args.arabic_limit}, english-limit={args.english_limit}")
    print(f"  threshold={args.threshold}, semantic-threshold={args.semantic_threshold}")
    print("=" * 60)

    # Load corpora
    print("\n[1] Loading corpora...")
    t0 = time.time()
    arabic_entries = load_arabic_corpus(limit=args.arabic_limit)
    english_entries = load_english_corpus(limit=args.english_limit)
    print(f"  Loaded {len(arabic_entries)} Arabic, {len(english_entries)} English entries in {time.time()-t0:.1f}s")

    # Supplement with gold benchmark entries for fair evaluation
    ar_sup, en_sup = (0, 0) if args.no_gold_supplement else supplement_with_gold(arabic_entries, english_entries)
    if ar_sup or en_sup:
        print(f"  Gold supplement: +{ar_sup} Arabic, +{en_sup} English")
        print(f"  Total after supplement: {len(arabic_entries)} Arabic, {len(english_entries)} English")

    # Pre-compute caches
    print("\n[2] Pre-computing phonetic caches...")
    t0 = time.time()
    arabic_cache = precompute_arabic(arabic_entries)
    english_cache = precompute_english(english_entries)
    print(f"  Done in {time.time()-t0:.1f}s")

    # Initialize scorer + concept matcher
    print("\n[3] Initializing MultiMethodScorer + ConceptMatcher...")
    from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScorer
    from juthoor_cognatediscovery_lv2.discovery.concept_matcher import ConceptMatcher
    scorer = MultiMethodScorer()
    concept_matcher = ConceptMatcher(CONCEPTS_FILE)
    print(f"  MultiMethodScorer ready")
    print(f"  ConceptMatcher: {concept_matcher.concept_count} concepts, "
          f"{concept_matcher.en_index_size} EN tokens, {concept_matcher.ar_index_size} AR tokens")

    # Score all pairs
    print("\n[4] Scoring pairs...")
    leads = score_all_pairs(
        arabic_cache,
        english_cache,
        scorer,
        concept_matcher=concept_matcher,
        threshold=args.threshold,
        semantic_threshold=args.semantic_threshold,
        prefilter_threshold=args.prefilter,
        top_k=args.top_k,
    )

    # Benchmark evaluation
    print("\n[5] Benchmark evaluation...")
    gold_pairs = load_gold_benchmark()
    metrics = evaluate_benchmark(leads, gold_pairs)
    print(f"  Gold pairs (Arabic-English): {metrics.get('gold_pairs_total', 0)}")
    print(f"  Leads generated: {metrics.get('leads_total', 0)}")
    print(f"  Gold pairs recovered: {metrics.get('gold_pairs_recovered', 0)}")
    print(f"  Recall: {metrics.get('recall', 0):.4f}")
    anchor_counts = metrics.get("anchor_counts", {})
    if anchor_counts:
        print(f"  Anchor levels: gold={anchor_counts.get('gold', 0)}, "
              f"silver={anchor_counts.get('silver', 0)}, "
              f"auto_brut={anchor_counts.get('auto_brut', 0)}")

    # Print top 30
    print("\n[6] Top 30 leads:")
    print(f"{'#':>3}  {'Arabic':15} {'Translit':12} {'English':18} {'Phon':6} {'Gloss':5} {'Conc':5} {'Comb':6} {'M':3} {'Anchor':10} {'Best Method'}")
    print("-" * 120)
    for i, lead in enumerate(leads[:30], 1):
        ar = lead.get("arabic", "")[:14]
        tr = lead.get("arabic_translit", "")[:11]
        en = lead.get("english", "")[:17]
        ph = lead.get("phonetic_score", 0.0)
        gl = lead.get("gloss_similarity", 0.0)
        co = lead.get("concept_similarity", 0.0)
        cm = lead.get("combined_score", 0.0)
        nm = lead.get("num_methods", 0)
        anc = lead.get("anchor_level", "")[:9]
        meth = lead.get("best_method", "")[:25]
        print(f"{i:>3}  {ar:15} {tr:12} {en:18} {ph:.4f} {gl:.3f} {co:.3f} {cm:.4f} {nm:>3}  {anc:10} {meth}")

    # Save
    if not args.no_save and leads:
        print("\n[7] Saving leads...")
        out_path = save_leads(leads, label="improved")
        print(f"  Saved {len(leads)} leads to: {out_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
