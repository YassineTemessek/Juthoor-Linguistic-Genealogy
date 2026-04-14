"""Null model validation: does the hybrid scoring pipeline beat random chance?

Compares real Arabic roots against shuffled (random) roots to determine
whether the discovery pipeline finds genuine linguistic connections.

Gate: z > 3.29 (p < 0.001) = method validated.
       z > 2.00 = partial signal, needs tuning.
       z < 2.00 = method fails, redesign required.
"""
import json, random, sys, time, math, collections
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
LV2_ROOT = REPO_ROOT / "Juthoor-CognateDiscovery-LV2"
sys.path.insert(0, str(LV2_ROOT / "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ARABIC_CORPUS = LV2_ROOT / "data/processed/arabic/unified_arabic_discovery.jsonl"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_arabic(limit=50):
    """Load Arabic entries with glosses for semantic comparison."""
    entries = []
    with open(ARABIC_CORPUS, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            lemma = row.get("lemma", "")
            if len(lemma) < 2:
                continue
            # Need some English gloss for semantic comparison
            gloss = str(row.get("english_gloss") or row.get("meaning_text")
                        or row.get("gloss") or row.get("short_gloss") or "").strip()
            if not gloss or len(gloss) < 2:
                continue
            # Need a root for shuffling
            if not (row.get("root") or "").strip():
                continue
            entries.append(row)
            if len(entries) >= limit:
                break
    return entries


def load_english(limit=200):
    """Load English entries with glosses, sampled across the corpus."""
    path = LV2_ROOT / "data/processed/english/english_ipa_merged_pos.jsonl"
    total = sum(1 for l in open(path, encoding="utf-8") if l.strip())
    stride = max(1, total // (limit * 2))
    entries, seen, n = [], set(), 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            n += 1
            if stride > 1 and (n - 1) % stride != 0:
                continue
            row = json.loads(line)
            lemma = (row.get("lemma", "") or "").strip().lower()
            if not lemma or len(lemma) <= 2 or lemma in seen:
                continue
            if not lemma.replace("-", "").replace("'", "").isalpha():
                continue
            seen.add(lemma)
            entries.append(row)
    return entries


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

def _text_for_embedding(entry: dict) -> str:
    """Build a text representation for semantic embedding."""
    lemma = str(entry.get("lemma", "") or "").strip()
    gloss = str(
        entry.get("english_gloss") or entry.get("meaning_text")
        or entry.get("gloss") or entry.get("short_gloss") or ""
    ).strip()
    if gloss:
        return f"{lemma}: {gloss}"
    return lemma


def compute_embeddings(entries: list[dict], embedder) -> np.ndarray:
    """Compute L2-normalized embeddings for a list of entries."""
    if not entries:
        return np.empty((0, 0), dtype="float32")
    texts = [_text_for_embedding(e) for e in entries]
    return embedder.embed(texts)


def pairwise_cosine(vecs_a: np.ndarray, vecs_b: np.ndarray) -> np.ndarray:
    """Compute cosine similarity matrix (already L2-normalized)."""
    return vecs_a @ vecs_b.T


# ---------------------------------------------------------------------------
# Hybrid scoring
# ---------------------------------------------------------------------------

def score_all_pairs(arabic, english, sem_sim_matrix, form_sim_matrix):
    """Score all Arabic x English pairs using hybrid scoring.

    Returns list of scores (one per pair).
    """
    from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import (
        compute_hybrid, HybridWeights,
    )
    weights = HybridWeights()
    scores = []
    for i, ar in enumerate(arabic):
        for j, en in enumerate(english):
            semantic = float(sem_sim_matrix[i, j])
            form = float(form_sim_matrix[i, j])
            result = compute_hybrid(
                source=ar, target=en,
                semantic=semantic, form=form,
                weights=weights,
            )
            scores.append(result["combined_score"])
    return scores


def count_above_threshold(scores, threshold=0.30):
    """Count how many scores exceed the threshold."""
    return sum(1 for s in scores if s >= threshold)


# ---------------------------------------------------------------------------
# Main validation
# ---------------------------------------------------------------------------

def main():
    random.seed(42)
    np.random.seed(42)
    n_permutations = 100

    print("=" * 70)
    print("NULL MODEL VALIDATION — Hybrid Scoring Pipeline")
    print("=" * 70)

    # ---- Load data ----
    print("\n[1/5] Loading corpora...")
    arabic = load_arabic(50)
    english = load_english(200)
    print(f"  Arabic: {len(arabic)} entries")
    print(f"  English: {len(english)} entries")
    print(f"  Total pairs: {len(arabic) * len(english):,}")

    if len(arabic) < 5:
        print(f"\nERROR: Too few Arabic entries ({len(arabic)}). "
              f"Check corpus path: {ARABIC_CORPUS}")
        sys.exit(1)
    if len(english) < 10:
        print(f"\nERROR: Too few English entries ({len(english)}).")
        sys.exit(1)

    # ---- Compute embeddings ----
    print("\n[2/5] Computing semantic embeddings (BGE-M3)...")
    t0 = time.time()
    from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import BgeM3Embedder
    sem_embedder = BgeM3Embedder()
    ar_sem = compute_embeddings(arabic, sem_embedder)
    en_sem = compute_embeddings(english, sem_embedder)
    print(f"  Done in {time.time() - t0:.1f}s  (Arabic: {ar_sem.shape}, English: {en_sem.shape})")

    print("\n[3/5] Computing form embeddings (ByT5)...")
    t0 = time.time()
    from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import ByT5Embedder
    form_embedder = ByT5Embedder()
    ar_form = compute_embeddings(arabic, form_embedder)
    en_form = compute_embeddings(english, form_embedder)
    print(f"  Done in {time.time() - t0:.1f}s  (Arabic: {ar_form.shape}, English: {en_form.shape})")

    # ---- Real run ----
    print("\n[4/5] Scoring REAL pairs...")
    t0 = time.time()
    real_sem_sim = pairwise_cosine(ar_sem, en_sem)
    real_form_sim = pairwise_cosine(ar_form, en_form)
    real_scores = score_all_pairs(arabic, english, real_sem_sim, real_form_sim)
    real_count = count_above_threshold(real_scores)
    real_mean = float(np.mean(real_scores))
    print(f"  Done in {time.time() - t0:.1f}s")
    print(f"  Mean score: {real_mean:.4f}")
    print(f"  Pairs above 0.30: {real_count} / {len(real_scores)}")

    # ---- Null runs (permutation test) ----
    print(f"\n[5/5] Running {n_permutations} null permutations...")
    t0 = time.time()
    null_counts = []
    null_means = []

    for perm in range(n_permutations):
        # Shuffle Arabic entries: break the root-meaning association
        # by randomly reassigning glosses across Arabic entries
        shuffled_arabic = [dict(ar) for ar in arabic]
        glosses = [
            {k: ar.get(k) for k in
             ("english_gloss", "meaning_text", "gloss", "short_gloss",
              "gloss_plain", "root", "root_norm")}
            for ar in shuffled_arabic
        ]
        random.shuffle(glosses)
        for ar, g in zip(shuffled_arabic, glosses):
            ar.update(g)

        # Recompute semantic embeddings for shuffled Arabic
        # (the semantic content changed because glosses were reassigned)
        ar_sem_shuffled = compute_embeddings(shuffled_arabic, sem_embedder)

        # Form embeddings stay the same (based on lemma orthography, not meaning)
        # But we need to rebuild the similarity matrices
        null_sem_sim = pairwise_cosine(ar_sem_shuffled, en_sem)
        null_form_sim = real_form_sim  # form is lemma-based, unchanged

        null_scores = score_all_pairs(
            shuffled_arabic, english, null_sem_sim, null_form_sim,
        )
        null_counts.append(count_above_threshold(null_scores))
        null_means.append(float(np.mean(null_scores)))

        if (perm + 1) % 10 == 0:
            elapsed = time.time() - t0
            eta = elapsed / (perm + 1) * (n_permutations - perm - 1)
            print(f"  Permutation {perm + 1}/{n_permutations} "
                  f"({elapsed:.0f}s elapsed, ~{eta:.0f}s remaining)")

    print(f"  All permutations done in {time.time() - t0:.1f}s")

    # ---- Statistical comparison ----
    null_count_mean = float(np.mean(null_counts))
    null_count_std = float(np.std(null_counts))
    null_mean_mean = float(np.mean(null_means))
    null_mean_std = float(np.std(null_means))

    # z-score on count of pairs above threshold
    z_count = ((real_count - null_count_mean) / null_count_std
               if null_count_std > 0 else 0.0)
    # z-score on mean score
    z_mean = ((real_mean - null_mean_mean) / null_mean_std
              if null_mean_std > 0 else 0.0)

    # Effect size (ratio)
    ratio_count = real_count / max(null_count_mean, 1)
    ratio_mean = real_mean / max(null_mean_mean, 1e-6)

    # p-value approximation (one-tailed)
    p_count = 1.0 - 0.5 * (1 + math.erf(z_count / math.sqrt(2)))
    p_mean = 1.0 - 0.5 * (1 + math.erf(z_mean / math.sqrt(2)))

    # ---- Report ----
    print(f"\n{'=' * 70}")
    print(f"RESULTS — NULL MODEL VALIDATION")
    print(f"{'=' * 70}")

    print(f"\n--- Count-based test (pairs above 0.30 threshold) ---")
    print(f"  Real:          {real_count}")
    print(f"  Null mean:     {null_count_mean:.1f} +/- {null_count_std:.1f}")
    print(f"  Ratio:         {ratio_count:.2f}x")
    print(f"  Z-score:       {z_count:.2f}")
    print(f"  p-value:       {p_count:.6f}")

    print(f"\n--- Mean-score test ---")
    print(f"  Real mean:     {real_mean:.4f}")
    print(f"  Null mean:     {null_mean_mean:.4f} +/- {null_mean_std:.4f}")
    print(f"  Ratio:         {ratio_mean:.2f}x")
    print(f"  Z-score:       {z_mean:.2f}")
    print(f"  p-value:       {p_mean:.6f}")

    # ---- Gate decision ----
    z_best = max(z_count, z_mean)
    print(f"\n{'=' * 70}")
    if z_best > 3.29:
        print(f"PASS  (z = {z_best:.2f} > 3.29, p < 0.001)")
        print(f"The hybrid scoring pipeline finds significantly more")
        print(f"real connections than random chance. Proceed to Phase 1.")
    elif z_best > 2.00:
        print(f"PARTIAL  (z = {z_best:.2f}, between 2.00 and 3.29)")
        print(f"Some signal detected but not strong enough.")
        print(f"Investigate which scoring components contribute signal.")
    else:
        print(f"FAIL  (z = {z_best:.2f} < 2.00)")
        print(f"The pipeline does not beat random chance.")
        print(f"STOP. Redesign scoring before adding new languages.")
    print(f"{'=' * 70}")

    # ---- Score distribution breakdown ----
    print(f"\nScore distribution (real):")
    thresholds = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
    for t in thresholds:
        n = sum(1 for s in real_scores if s >= t)
        print(f"  >= {t:.2f}: {n:>6} ({n / len(real_scores) * 100:.1f}%)")

    # ---- Top real pairs ----
    print(f"\nTop 20 highest-scoring pairs (real):")
    pair_scores = []
    for i, ar in enumerate(arabic):
        for j, en in enumerate(english):
            pair_scores.append((real_scores[i * len(english) + j], ar, en))
    pair_scores.sort(key=lambda x: -x[0])
    for rank, (score, ar, en) in enumerate(pair_scores[:20], 1):
        ar_lemma = ar.get("lemma", "?")
        ar_gloss = str(ar.get("english_gloss") or ar.get("short_gloss") or "")[:40]
        en_lemma = en.get("lemma", "?")
        print(f"  {rank:>2}. {score:.3f}  {ar_lemma} ({ar_gloss}) <-> {en_lemma}")


if __name__ == "__main__":
    main()
