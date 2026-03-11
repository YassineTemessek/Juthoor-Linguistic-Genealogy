"""
Phase 3 Semantic Validation Script
Scores how well each tri-root's axial_meaning relates to its binary_root_meaning
using BGE-M3 cosine similarity.

Input:
  data/muajam/roots.jsonl         — 1,938 triconsonantal root entries
  outputs/genome_v2/<bab>.jsonl   — Phase 2 enriched genome files

Output:
  outputs/genome_v2/<bab>.jsonl   — Updated with semantic_score on matched entries
  outputs/reports/semantic_validation.json — Distribution stats + top/bottom roots
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

# Ensure stdout handles Arabic characters
sys.stdout.reconfigure(encoding="utf-8")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent
MUAJAM_ROOTS = BASE / "data" / "muajam" / "roots.jsonl"
GENOME_V2_DIR = BASE / "outputs" / "genome_v2"
REPORTS_DIR = BASE / "outputs" / "reports"


# ── Pure scoring functions (no model dependency) ──────────────────────────────

def cosine_score(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two L2-normalized vectors (= dot product)."""
    return float(np.dot(a, b))


def build_text_index(
    records: list[dict],
) -> tuple[dict[str, int], dict[str, int]]:
    """
    Extract unique non-empty texts from records.
    Returns two dicts mapping text -> unique index:
      (binary_root_meaning_index, axial_meaning_index)
    """
    brm_texts: dict[str, int] = {}
    ax_texts: dict[str, int] = {}
    for rec in records:
        brm = rec.get("binary_root_meaning", "").strip()
        ax = rec.get("axial_meaning", "").strip()
        if brm and brm not in brm_texts:
            brm_texts[brm] = len(brm_texts)
        if ax and ax not in ax_texts:
            ax_texts[ax] = len(ax_texts)
    return brm_texts, ax_texts


def compute_scores(
    records: list[dict],
    brm_embeddings: dict[str, np.ndarray],
    ax_embeddings: dict[str, np.ndarray],
) -> list[dict]:
    """
    For each record, compute cosine similarity between its axial_meaning
    and binary_root_meaning embeddings. Returns list of scored dicts.
    Skips records where either embedding is missing.
    """
    scored = []
    for rec in records:
        brm = rec.get("binary_root_meaning", "").strip()
        ax = rec.get("axial_meaning", "").strip()
        if brm not in brm_embeddings or ax not in ax_embeddings:
            continue
        score = cosine_score(brm_embeddings[brm], ax_embeddings[ax])
        scored.append({
            "tri_root": rec["tri_root"],
            "binary_root": rec.get("binary_root", ""),
            "binary_root_meaning": brm,
            "axial_meaning": ax,
            "semantic_score": round(score, 6),
        })
    return scored


def build_report(scored: list[dict]) -> dict:
    """Build distribution report from scored entries."""
    if not scored:
        return {}
    
    scores = [s["semantic_score"] for s in scored]
    arr = np.array(scores, dtype="float32")

    sorted_by_score = sorted(scored, key=lambda x: x["semantic_score"], reverse=True)

    # Histogram: 10 bins from min to max
    hist_counts, hist_edges = np.histogram(arr, bins=10)
    histogram = [
        {"bin_start": round(float(hist_edges[i]), 4),
         "bin_end": round(float(hist_edges[i + 1]), 4),
         "count": int(hist_counts[i])}
        for i in range(len(hist_counts))
    ]

    return {
        "total_scored": len(scores),
        "mean": round(float(np.mean(arr)), 6),
        "median": round(float(np.median(arr)), 6),
        "std": round(float(np.std(arr)), 6),
        "min": round(float(np.min(arr)), 6),
        "max": round(float(np.max(arr)), 6),
        "q25": round(float(np.percentile(arr, 25)), 6),
        "q75": round(float(np.percentile(arr, 75)), 6),
        "histogram": histogram,
        "top_10": sorted_by_score[:10],
        "bottom_10": sorted(scored, key=lambda x: x["semantic_score"])[:10],
    }


# ── I/O functions ─────────────────────────────────────────────────────────────

def load_muajam_records() -> list[dict]:
    """Load all records from muajam roots.jsonl."""
    records = []
    with MUAJAM_ROOTS.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a list of texts using BGE-M3. Returns (N, 1024) L2-normalized."""
    from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import BgeM3Embedder

    embedder = BgeM3Embedder()
    return embedder.embed(texts)


def enrich_genome_v2(score_map: dict[str, float]) -> int:
    """
    Read each genome_v2 file, add semantic_score to matched entries
    whose root has a score, and rewrite the file.
    Returns count of entries enriched.
    """
    import re

    _ARABIC_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670\u0640]")
    _AR_ROOT_NORM_MAP = str.maketrans({
        "\u0623": "\u0627", "\u0625": "\u0627", "\u0622": "\u0627",
        "\u0671": "\u0627", "\u0649": "\u064a", "\u0624": "\u0648",
        "\u0626": "\u064a", "\u0629": "\u0647",
    })

    def _norm(root: str) -> str:
        root = (root or "").strip()
        root = _ARABIC_DIACRITICS.sub("", root)
        return root.translate(_AR_ROOT_NORM_MAP)

    enriched = 0
    if not GENOME_V2_DIR.exists():
        return 0
        
    for bab_path in sorted(GENOME_V2_DIR.glob("*.jsonl")):
        entries = []
        with bab_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))

        changed = False
        for entry in entries:
            if not entry.get("muajam_match"):
                continue
            key = _norm(entry.get("root", ""))
            if key in score_map:
                entry["semantic_score"] = score_map[key]
                enriched += 1
                changed = True

        if changed:
            with bab_path.open("w", encoding="utf-8") as f:
                for entry in entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return enriched


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== Phase 3: Semantic Validation ===\n")

    # 1. Load muajam records
    if not MUAJAM_ROOTS.exists():
        print(f"ERROR: Muajam roots file not found at {MUAJAM_ROOTS}")
        sys.exit(1)
        
    records = load_muajam_records()
    print(f"Loaded {len(records)} muajam records")

    # 2. Build text indices (unique texts to embed)
    brm_index, ax_index = build_text_index(records)
    brm_texts = list(brm_index.keys())
    ax_texts = list(ax_index.keys())
    print(f"Unique binary_root_meaning texts: {len(brm_texts)}")
    print(f"Unique axial_meaning texts: {len(ax_texts)}")

    # 3. Embed all texts
    print("\nEmbedding binary_root_meaning texts...")
    brm_vectors = embed_texts(brm_texts)
    print(f"  Shape: {brm_vectors.shape}")

    print("Embedding axial_meaning texts...")
    ax_vectors = embed_texts(ax_texts)
    print(f"  Shape: {ax_vectors.shape}")

    # 4. Build text -> vector lookup
    brm_embeddings = {text: brm_vectors[i] for i, text in enumerate(brm_texts)}
    ax_embeddings = {text: ax_vectors[i] for i, text in enumerate(ax_texts)}

    # 5. Compute scores
    print("\nComputing semantic scores...")
    scored = compute_scores(records, brm_embeddings, ax_embeddings)
    print(f"Scored {len(scored)} triconsonantal roots")

    # 6. Build report
    report = build_report(scored)
    if not report:
        print("ERROR: No roots were scored.")
        sys.exit(1)
        
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / "semantic_validation.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nReport written to: {report_path}")
    print(f"  Mean score:   {report['mean']:.4f}")
    print(f"  Median score: {report['median']:.4f}")
    print(f"  Std dev:      {report['std']:.4f}")
    print(f"  Q25-Q75:      [{report['q25']:.4f}, {report['q75']:.4f}]")

    # 7. Enrich genome_v2 files
    print("\nEnriching genome_v2 files with semantic_score...")
    score_map = {s["tri_root"]: s["semantic_score"] for s in scored}
    enriched = enrich_genome_v2(score_map)
    print(f"Enriched {enriched} genome_v2 entries")

    # 8. Print top/bottom 5
    print("\n── Top 5 (highest semantic coherence) ──")
    for s in report["top_10"][:5]:
        print(f"  {s['tri_root']:>6}  {s['semantic_score']:.4f}  "
              f"brm=\"{s['binary_root_meaning']}\"  ax=\"{s['axial_meaning']}\"")
    print("\n── Bottom 5 (lowest semantic coherence) ──")
    for s in report["bottom_10"][:5]:
        print(f"  {s['tri_root']:>6}  {s['semantic_score']:.4f}  "
              f"brm=\"{s['binary_root_meaning']}\"  ax=\"{s['axial_meaning']}\"")

    print("\n=== Phase 3 complete ===")


if __name__ == "__main__":
    main()
