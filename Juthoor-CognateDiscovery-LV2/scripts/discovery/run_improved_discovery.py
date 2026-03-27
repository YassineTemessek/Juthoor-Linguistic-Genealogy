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

ENGLISH_PRIMARY = LV2_ROOT / "data/processed/english/english_enriched_discovery.jsonl"
ENGLISH_FALLBACK = LV2_ROOT / "data/processed/english/english_ipa_merged_pos.jsonl"

GOLD_BENCHMARK = LV2_ROOT / "resources/benchmarks/cognate_gold.jsonl"
LEADS_DIR = LV2_ROOT / "outputs/leads"

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


def compute_gloss_similarity(ar_gloss: str, en_gloss: str) -> float:
    """Lightweight Jaccard similarity on gloss content words."""
    import re
    _STOPWORDS = frozenset({
        "a", "an", "the", "of", "in", "to", "for", "and", "or", "is", "it",
        "at", "by", "on", "as", "be", "was", "are", "were", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "shall",
        "should", "may", "might", "can", "could", "not", "no", "but", "if",
        "so", "than", "that", "this", "with", "from", "into", "about", "up",
        "out", "very", "also", "just", "more", "most", "other", "some", "such",
        "only", "over", "any", "each", "all", "both", "few", "many", "much",
    })
    _WORD_RE = re.compile(r"[a-z]{3,}")
    src_words = set(_WORD_RE.findall(ar_gloss.lower())) - _STOPWORDS
    tgt_words = set(_WORD_RE.findall(en_gloss.lower())) - _STOPWORDS
    if not src_words or not tgt_words:
        return 0.0
    intersection = src_words & tgt_words
    union = src_words | tgt_words
    return len(intersection) / len(union) if union else 0.0


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

        # Phase 2: full MultiMethodScorer
        for _fast_score, en_pre in candidates:
            result = scorer.score_pair(ar_pre["entry"], en_pre["entry"])
            phonetic = result.best_score
            if phonetic < threshold:
                continue

            # Gloss similarity
            ar_gloss = ar_pre["gloss"]
            en_gloss = en_pre["gloss"]
            sem_score = compute_gloss_similarity(ar_gloss, en_gloss)

            # Combined score
            combined = phonetic * 0.7 + sem_score * 0.3

            if semantic_threshold > 0.0 and sem_score < semantic_threshold:
                continue

            num_methods = len(result.methods_that_fired)
            anchor = classify_anchor(phonetic, num_methods)

            leads.append({
                "arabic": ar_pre["entry"].get("lemma", ar_pre["root"]),
                "arabic_translit": ar_pre["translit"],
                "arabic_root": ar_pre["root"],
                "english": en_pre["lemma"],
                "phonetic_score": round(phonetic, 4),
                "semantic_score": round(sem_score, 4),
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

    gold_set_arabic = {p["arabic"] for p in gold_pairs}
    gold_set_english = {p["english"] for p in gold_pairs}
    gold_combined = {(p["arabic"], p["english"]) for p in gold_pairs}

    found = 0
    for lead in leads:
        ar = lead.get("arabic", "")
        en = lead.get("english", "")
        if (ar, en) in gold_combined:
            found += 1

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

    # Pre-compute caches
    print("\n[2] Pre-computing phonetic caches...")
    t0 = time.time()
    arabic_cache = precompute_arabic(arabic_entries)
    english_cache = precompute_english(english_entries)
    print(f"  Done in {time.time()-t0:.1f}s")

    # Initialize scorer
    print("\n[3] Initializing MultiMethodScorer...")
    from juthoor_cognatediscovery_lv2.discovery.multi_method_scorer import MultiMethodScorer
    scorer = MultiMethodScorer()
    print("  Ready")

    # Score all pairs
    print("\n[4] Scoring pairs...")
    leads = score_all_pairs(
        arabic_cache,
        english_cache,
        scorer,
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
    print(f"{'#':>3}  {'Arabic':15} {'Translit':12} {'English':18} {'Phon':6} {'Sem':5} {'Comb':6} {'Methods':3} {'Anchor':10} {'Best Method'}")
    print("-" * 110)
    for i, lead in enumerate(leads[:30], 1):
        ar = lead.get("arabic", "")[:14]
        tr = lead.get("arabic_translit", "")[:11]
        en = lead.get("english", "")[:17]
        ph = lead.get("phonetic_score", 0.0)
        sm = lead.get("semantic_score", 0.0)
        cm = lead.get("combined_score", 0.0)
        nm = lead.get("num_methods", 0)
        anc = lead.get("anchor_level", "")[:9]
        meth = lead.get("best_method", "")[:25]
        print(f"{i:>3}  {ar:15} {tr:12} {en:18} {ph:.4f} {sm:.3f} {cm:.4f} {nm:>3}  {anc:10} {meth}")

    # Save
    if not args.no_save and leads:
        print("\n[7] Saving leads...")
        out_path = save_leads(leads, label="improved")
        print(f"  Saved {len(leads)} leads to: {out_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
