"""
prepare.py — FROZEN EVALUATION HARNESS

This file MUST NOT be edited by the autoresearch agent.
It loads corpora, computes embeddings, runs the null-model permutation test,
and outputs a machine-readable JSON result that loop.py uses for accept/reject.

Usage:
    python prepare.py                  # run evaluation, print JSON result
    python prepare.py --verbose        # also print human-readable report
    python prepare.py --permutations 20  # quick screening mode
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
AUTORESEARCH_ROOT = Path(__file__).resolve().parent
REPO_ROOT = AUTORESEARCH_ROOT.parent
LV2_ROOT = REPO_ROOT / "Juthoor-CognateDiscovery-LV2"

# Add LV2 source to path so we can import scoring modules
sys.path.insert(0, str(LV2_ROOT / "src"))

# Corpora paths (symlink these into autoresearch/data/ if preferred)
ARABIC_CORPUS = LV2_ROOT / "data/processed/arabic/unified_arabic_discovery.jsonl"
ENGLISH_CORPUS = LV2_ROOT / "data/processed/english/english_ipa_merged_pos.jsonl"
ARABIC_GLOSSES = LV2_ROOT / "data/processed/arabic/arabic_english_glosses.json"

# Optional: Greek/Latin corpora for multi-language evaluation
GREEK_CORPUS = LV2_ROOT / "data/processed/greek/greek_lexemes.jsonl"
LATIN_CORPUS = LV2_ROOT / "data/processed/latin/latin_lexemes.jsonl"

# Embedding cache directory
CACHE_DIR = AUTORESEARCH_ROOT / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Results directory
RESULTS_DIR = AUTORESEARCH_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Import experiment config (the ONLY thing that changes between iterations)
# ---------------------------------------------------------------------------
def load_experiment_config():
    """Safely import EXPERIMENT_CONFIG from experiment.py."""
    try:
        sys.path.insert(0, str(AUTORESEARCH_ROOT))
        from experiment import EXPERIMENT_CONFIG
        return EXPERIMENT_CONFIG
    except Exception as e:
        print(json.dumps({
            "error": f"Failed to import experiment.py: {e}",
            "z_best": -999,
            "accepted": False,
        }))
        sys.exit(1)


# ---------------------------------------------------------------------------
# Validation: enforce constraints on experiment config
# ---------------------------------------------------------------------------
def validate_config(cfg) -> list[str]:
    """Check that the experiment config respects all constraints.

    Returns list of violation messages (empty = valid).
    """
    violations = []

    # Weight sum
    wsum = cfg.semantic_weight + cfg.form_weight
    if abs(wsum - 1.0) > 0.05:
        violations.append(
            f"semantic_weight + form_weight = {wsum:.3f}, must be ~1.0 (±0.05)"
        )

    # Individual bonus caps
    caps = {
        "phonetic_law_cap": cfg.phonetic_law_cap,
        "genome_cap": cfg.genome_cap,
        "multi_method_cap": cfg.multi_method_cap,
        "cross_pair_cap": cfg.cross_pair_cap,
        "root_quality_cap": cfg.root_quality_cap,
        "correspondence_cap": cfg.correspondence_cap,
    }
    for name, val in caps.items():
        if val > 0.40:
            violations.append(f"{name} = {val:.3f} exceeds 0.40 maximum")

    # Total bonus caps
    total_caps = sum(caps.values())
    if total_caps > 1.0:
        violations.append(f"Total bonus caps = {total_caps:.3f} exceeds 1.0")

    # Null threshold bounds
    if not (0.15 <= cfg.null_threshold <= 0.50):
        violations.append(
            f"null_threshold = {cfg.null_threshold} outside [0.15, 0.50]"
        )

    # Weak radicals must include core set
    for ch in "اوي":
        if ch not in cfg.weak_radicals_ar:
            violations.append(f"weak_radicals_ar missing core radical '{ch}'")

    return violations


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_corpus(path: Path, limit: int = 200, require_gloss: bool = True,
                require_root: bool = False, stride: int = 1) -> list[dict]:
    """Load a JSONL corpus with optional filtering."""
    if not path.exists():
        return []
    entries = []
    n = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            n += 1
            if stride > 1 and (n - 1) % stride != 0:
                continue
            row = json.loads(line)
            lemma = (row.get("lemma") or "").strip()
            if len(lemma) < 2:
                continue
            if require_gloss:
                gloss = str(
                    row.get("english_gloss") or row.get("meaning_text")
                    or row.get("gloss") or row.get("short_gloss") or ""
                ).strip()
                if not gloss or len(gloss) < 2:
                    continue
            if require_root and not (row.get("root") or "").strip():
                continue
            entries.append(row)
            if len(entries) >= limit:
                break
    return entries


# Grammatical labels that leak into Wiktionary glosses — filter these out
_GRAMMAR_NOISE = frozenset({
    "transitive", "intransitive", "ditransitive", "reflexive", "causative",
    "passive", "imperfective", "perfective", "verbal noun", "participle",
    "active", "stative", "denominative", "elative", "diminutive",
    "masculine", "feminine", "plural", "singular", "dual",
    "form i", "form ii", "form iii", "form iv", "form v",
    "form vi", "form vii", "form viii", "form ix", "form x",
})

_GLOSS_CACHE: dict[str, str] | None = None


def _load_good_glosses() -> dict[str, str]:
    """Load arabic_english_glosses.json and build a clean lookup."""
    global _GLOSS_CACHE
    if _GLOSS_CACHE is not None:
        return _GLOSS_CACHE

    import re
    _GLOSS_CACHE = {}
    if not ARABIC_GLOSSES.exists():
        return _GLOSS_CACHE

    raw = json.loads(ARABIC_GLOSSES.read_text(encoding="utf-8"))
    diacritics_re = re.compile(r"[\u064B-\u065F\u0670\u0640]")

    for ar_word, entry in raw.items():
        glosses = entry.get("english_glosses", [])
        # Filter out grammar noise and very short labels
        clean = [
            g for g in glosses
            if g.lower().strip() not in _GRAMMAR_NOISE
            and len(g.strip()) >= 3
            and not g.strip().lower().startswith("form ")
        ]
        if not clean:
            continue
        # Take the first 3 meaningful glosses
        best = ", ".join(clean[:3])
        # Store under both raw and stripped-diacritics keys
        _GLOSS_CACHE[ar_word] = best
        stripped = diacritics_re.sub("", ar_word)
        if stripped != ar_word and stripped not in _GLOSS_CACHE:
            _GLOSS_CACHE[stripped] = best

    # Manual overrides for known bad Wiktionary entries
    _GLOSS_CACHE["الله"] = "God, deity, the supreme being"
    _GLOSS_CACHE["اللَّه"] = "God, deity, the supreme being"
    _GLOSS_CACHE["بصر"] = "sight, vision, eyesight"
    _GLOSS_CACHE["بَصَر"] = "sight, vision, eyesight"
    _GLOSS_CACHE["هدى"] = "guidance, right path, to guide"
    _GLOSS_CACHE["هَدَى"] = "guidance, right path, to guide"
    _GLOSS_CACHE["هُدًى"] = "guidance, right path, to guide"

    return _GLOSS_CACHE


def _enrich_arabic_glosses(entries: list[dict]) -> list[dict]:
    """Replace noisy english_gloss with better Wiktionary glosses where available."""
    import re
    glosses = _load_good_glosses()
    diacritics_re = re.compile(r"[\u064B-\u065F\u0670\u0640]")
    enriched = 0
    for entry in entries:
        lemma = entry.get("lemma", "")
        root = entry.get("root", "")
        stripped = diacritics_re.sub("", lemma)
        # Try: stripped lemma, raw lemma, root
        better = glosses.get(stripped) or glosses.get(lemma) or glosses.get(root)
        if better:
            entry["english_gloss"] = better
            enriched += 1
    return entries


def load_arabic(limit: int = 100) -> list[dict]:
    entries = load_corpus(ARABIC_CORPUS, limit=limit * 3, require_root=True)
    entries = _enrich_arabic_glosses(entries)
    # Keep only entries with a reasonable gloss after enrichment
    good = [e for e in entries
            if len(str(e.get("english_gloss") or "").strip()) >= 3]
    return good[:limit]


def load_english(limit: int = 200) -> list[dict]:
    total = sum(1 for l in open(ENGLISH_CORPUS, encoding="utf-8") if l.strip())
    stride = max(1, total // (limit * 2))
    # English corpus has no gloss fields — embed the lemma directly
    return load_corpus(ENGLISH_CORPUS, limit=limit, stride=stride,
                       require_gloss=False)


# ---------------------------------------------------------------------------
# Embedding helpers (with disk caching)
# ---------------------------------------------------------------------------
def _text_for_embedding(entry: dict) -> str:
    lemma = str(entry.get("lemma") or "").strip()
    gloss = str(
        entry.get("english_gloss") or entry.get("meaning_text")
        or entry.get("gloss") or entry.get("short_gloss") or ""
    ).strip()
    return f"{lemma}: {gloss}" if gloss else lemma


def compute_embeddings(entries: list[dict], embedder, cache_key: str = "") -> np.ndarray:
    """Compute L2-normalized embeddings, with optional disk cache."""
    if cache_key:
        cache_path = CACHE_DIR / f"{cache_key}.npy"
        if cache_path.exists():
            return np.load(cache_path)

    texts = [_text_for_embedding(e) for e in entries]
    vecs = embedder.embed(texts)

    if cache_key:
        np.save(CACHE_DIR / f"{cache_key}.npy", vecs)
    return vecs


def pairwise_cosine(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return a @ b.T


# ---------------------------------------------------------------------------
# Scoring (uses experiment config)
# ---------------------------------------------------------------------------
def score_all_pairs(arabic, english, sem_sim, form_sim, cfg):
    """Score all Arabic×English pairs using the experiment config weights."""
    from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import (
        compute_hybrid, HybridWeights,
    )
    # Build HybridWeights from experiment config
    weights = HybridWeights(
        semantic=cfg.semantic_weight,
        form=cfg.form_weight,
    )
    scores = []
    for i, ar in enumerate(arabic):
        for j, en in enumerate(english):
            semantic = float(sem_sim[i, j])
            form = float(form_sim[i, j])
            result = compute_hybrid(
                source=ar, target=en,
                semantic=semantic, form=form,
                weights=weights,
            )
            scores.append(result["combined_score"])
    return scores


def count_above_threshold(scores: list[float], threshold: float) -> int:
    return sum(1 for s in scores if s >= threshold)


# ---------------------------------------------------------------------------
# Main evaluation
# ---------------------------------------------------------------------------
def run_evaluation(n_permutations: int = 100, verbose: bool = False) -> dict:
    """Run full evaluation and return result dict."""
    cfg = load_experiment_config()

    # Validate config
    violations = validate_config(cfg)
    if violations:
        result = {
            "error": "Config validation failed",
            "violations": violations,
            "z_best": -999,
            "accepted": False,
        }
        print(json.dumps(result, indent=2))
        return result

    random.seed(42)
    np.random.seed(42)

    if verbose:
        print("=" * 70)
        print("AUTORESEARCH EVALUATION — Null Model Validation")
        print("=" * 70)

    # ---- Load data ----
    if verbose:
        print("\n[1/5] Loading corpora...")
    arabic = load_arabic(50)
    english = load_english(200)
    if verbose:
        print(f"  Arabic: {len(arabic)} | English: {len(english)} | "
              f"Pairs: {len(arabic) * len(english):,}")

    if len(arabic) < 5 or len(english) < 10:
        result = {
            "error": f"Too few entries (Arabic={len(arabic)}, English={len(english)})",
            "z_best": -999,
            "accepted": False,
        }
        print(json.dumps(result, indent=2))
        return result

    # ---- Compute embeddings ----
    if verbose:
        print("\n[2/5] Computing semantic embeddings (BGE-M3)...")
    t0 = time.time()
    from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import BgeM3Embedder
    sem_embedder = BgeM3Embedder()
    ar_sem = compute_embeddings(arabic, sem_embedder)
    # English semantic embeddings are cached (they never change)
    en_sem = compute_embeddings(english, sem_embedder, cache_key="en_sem_200")
    if verbose:
        print(f"  Done in {time.time() - t0:.1f}s")

    if verbose:
        print("\n[3/5] Computing form embeddings (ByT5)...")
    t0 = time.time()
    from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import ByT5Embedder
    form_embedder = ByT5Embedder()
    # Form embeddings depend on lemma orthography only — cache both
    ar_form = compute_embeddings(arabic, form_embedder, cache_key="ar_form_50")
    en_form = compute_embeddings(english, form_embedder, cache_key="en_form_200")
    if verbose:
        print(f"  Done in {time.time() - t0:.1f}s")

    # ---- Real run ----
    if verbose:
        print("\n[4/5] Scoring REAL pairs...")
    t0 = time.time()
    real_sem_sim = pairwise_cosine(ar_sem, en_sem)
    real_form_sim = pairwise_cosine(ar_form, en_form)
    real_scores = score_all_pairs(arabic, english, real_sem_sim, real_form_sim, cfg)
    real_count = count_above_threshold(real_scores, cfg.null_threshold)
    real_mean = float(np.mean(real_scores))
    if verbose:
        print(f"  Done in {time.time() - t0:.1f}s | "
              f"Mean: {real_mean:.4f} | Above {cfg.null_threshold}: {real_count}")

    # ---- Null permutations ----
    if verbose:
        print(f"\n[5/5] Running {n_permutations} null permutations...")
    t0 = time.time()
    null_counts = []
    null_means = []

    for perm in range(n_permutations):
        shuffled_arabic = [dict(ar) for ar in arabic]
        glosses = [
            {k: ar.get(k) for k in
             ("english_gloss", "meaning_text", "gloss", "short_gloss",
              "gloss_plain", "root", "root_norm")}
            for ar in shuffled_arabic
        ]
        random.shuffle(glosses)
        for ar, g_val in zip(shuffled_arabic, glosses):
            ar.update(g_val)

        ar_sem_shuffled = compute_embeddings(shuffled_arabic, sem_embedder)
        null_sem_sim = pairwise_cosine(ar_sem_shuffled, en_sem)
        null_scores = score_all_pairs(
            shuffled_arabic, english, null_sem_sim, real_form_sim, cfg
        )
        null_counts.append(count_above_threshold(null_scores, cfg.null_threshold))
        null_means.append(float(np.mean(null_scores)))

        if verbose and (perm + 1) % 10 == 0:
            elapsed = time.time() - t0
            eta = elapsed / (perm + 1) * (n_permutations - perm - 1)
            print(f"  Permutation {perm + 1}/{n_permutations} "
                  f"({elapsed:.0f}s, ~{eta:.0f}s remaining)")

    # ---- Compute statistics ----
    null_count_mean = float(np.mean(null_counts))
    null_count_std = float(np.std(null_counts))
    null_mean_mean = float(np.mean(null_means))
    null_mean_std = float(np.std(null_means))

    z_count = (real_count - null_count_mean) / null_count_std if null_count_std > 0 else 0.0
    z_mean = (real_mean - null_mean_mean) / null_mean_std if null_mean_std > 0 else 0.0
    z_best = max(z_count, z_mean)

    p_count = 1.0 - 0.5 * (1 + math.erf(z_count / math.sqrt(2)))
    p_mean = 1.0 - 0.5 * (1 + math.erf(z_mean / math.sqrt(2)))

    ratio_count = real_count / max(null_count_mean, 1)

    # ---- Build result ----
    result = {
        "z_count": round(z_count, 4),
        "z_mean": round(z_mean, 4),
        "z_best": round(z_best, 4),
        "real_count": real_count,
        "real_mean": round(real_mean, 6),
        "null_count_mean": round(null_count_mean, 2),
        "null_count_std": round(null_count_std, 2),
        "null_mean_mean": round(null_mean_mean, 6),
        "null_mean_std": round(null_mean_std, 6),
        "p_count": round(p_count, 8),
        "p_mean": round(p_mean, 8),
        "ratio_count": round(ratio_count, 2),
        "null_threshold": cfg.null_threshold,
        "n_permutations": n_permutations,
        "n_arabic": len(arabic),
        "n_english": len(english),
        "config": {
            "semantic_weight": cfg.semantic_weight,
            "form_weight": cfg.form_weight,
            "phonetic_law_cap": cfg.phonetic_law_cap,
            "genome_cap": cfg.genome_cap,
            "multi_method_cap": cfg.multi_method_cap,
            "cross_pair_cap": cfg.cross_pair_cap,
            "root_quality_cap": cfg.root_quality_cap,
            "correspondence_coeff": cfg.correspondence_coeff,
            "hamza_coeff": cfg.hamza_coeff,
            "weak_radical_coeff": cfg.weak_radical_coeff,
            "correspondence_cap": cfg.correspondence_cap,
            "null_threshold": cfg.null_threshold,
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    # ---- Verbose report ----
    if verbose:
        print(f"\n{'=' * 70}")
        print("RESULTS")
        print(f"{'=' * 70}")
        print(f"  z_count:    {z_count:.4f}  (p = {p_count:.6f})")
        print(f"  z_mean:     {z_mean:.4f}  (p = {p_mean:.6f})")
        print(f"  z_best:     {z_best:.4f}")
        print(f"  real_count: {real_count}  vs  null_mean: {null_count_mean:.1f}")
        print(f"  ratio:      {ratio_count:.2f}x")
        gate = "PASS" if z_best > 3.29 else "PARTIAL" if z_best > 2.0 else "FAIL"
        print(f"  GATE:       {gate}")
        print(f"{'=' * 70}")

    # Output machine-readable JSON
    print(json.dumps(result, indent=2))
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autoresearch evaluation harness")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print human-readable report")
    parser.add_argument("--permutations", "-p", type=int, default=100,
                        help="Number of null permutations (default: 100)")
    args = parser.parse_args()
    run_evaluation(n_permutations=args.permutations, verbose=args.verbose)
