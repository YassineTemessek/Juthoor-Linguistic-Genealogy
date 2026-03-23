# LV1 Phase 3 — Semantic Validation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Score how well each triconsonantal root's `axial_meaning` semantically relates to its parent `binary_root_meaning`, using BGE-M3 cosine similarity, to validate the Muajam Ishtiqaqi linguistic theory.

**Architecture:** Load Muajam roots.jsonl (1,938 entries), embed all unique `binary_root_meaning` and `axial_meaning` texts with BGE-M3, compute cosine similarity per matched triconsonantal root, enrich genome_v2 JSONL files with a `semantic_score` field, and produce a summary report with distribution statistics.

**Tech Stack:** Python 3.11+, BGE-M3 via LV2's `BgeM3Embedder` (FlagEmbedding), numpy, json

---

## Key References

| What | Path |
|------|------|
| Muajam roots data | `Juthoor-ArabicGenome-LV1/data/muajam/roots.jsonl` (1,938 lines) |
| Genome v2 output | `Juthoor-ArabicGenome-LV1/outputs/genome_v2/<bab>.jsonl` (30 files, 1,384 matched) |
| BgeM3Embedder class | `Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/lv3/discovery/embeddings.py:59-94` |
| Phase 2 build script | `Juthoor-ArabicGenome-LV1/scripts/build_genome_phase2.py` |
| Existing LV1 tests | `Juthoor-ArabicGenome-LV1/tests/` |
| Reports dir | `Juthoor-ArabicGenome-LV1/outputs/reports/` |

## Data Shapes

**Muajam roots.jsonl** (each line):
```json
{
  "binary_root": "بب",
  "binary_root_meaning": "الانفتاح والمنفذ",
  "tri_root": "بوب",
  "axial_meaning": "انفتاح مع اتصال دائم",
  "bab": "ب", "added_letter": "و", "quran_example": "..."
}
```

**Genome_v2 matched entry** (current — before Phase 3):
```json
{
  "bab": "ب", "binary_root": "با", "root": "بار", "words": ["بأر"],
  "muajam_match": true,
  "binary_root_meaning": "التجرد والخلوص",
  "axial_meaning": "حَفْرٌ في ظاهر الأرض ممتد إلى جوفها",
  "added_letter": "أ", "quran_example": "...", ...
}
```

**After Phase 3**, matched entries gain:
```json
{ "semantic_score": 0.73, ... }
```

**BgeM3Embedder API:**
```python
from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import BgeM3Embedder
embedder = BgeM3Embedder()
vectors = embedder.embed(["text1", "text2"])  # returns np.ndarray shape (N, 1024), L2-normalized
# Cosine similarity of L2-normalized vectors = dot product
```

---

### Task 1: Core scoring function (unit-testable, no model dependency)

**Files:**
- Create: `Juthoor-ArabicGenome-LV1/scripts/semantic_validation_phase3.py`
- Create: `Juthoor-ArabicGenome-LV1/tests/test_phase3_scoring.py`

**Step 1: Write the failing test**

Create `Juthoor-ArabicGenome-LV1/tests/test_phase3_scoring.py`:

```python
"""Tests for Phase 3 semantic validation scoring logic."""
import json
import numpy as np
import pytest


def test_cosine_score_identical_vectors():
    """Identical L2-normalized vectors should score 1.0."""
    from scripts.semantic_validation_phase3 import cosine_score

    a = np.array([1.0, 0.0, 0.0], dtype="float32")
    b = np.array([1.0, 0.0, 0.0], dtype="float32")
    assert cosine_score(a, b) == pytest.approx(1.0, abs=1e-6)


def test_cosine_score_orthogonal_vectors():
    """Orthogonal vectors should score 0.0."""
    from scripts.semantic_validation_phase3 import cosine_score

    a = np.array([1.0, 0.0, 0.0], dtype="float32")
    b = np.array([0.0, 1.0, 0.0], dtype="float32")
    assert cosine_score(a, b) == pytest.approx(0.0, abs=1e-6)


def test_cosine_score_opposite_vectors():
    """Opposite vectors should score -1.0."""
    from scripts.semantic_validation_phase3 import cosine_score

    a = np.array([1.0, 0.0], dtype="float32")
    b = np.array([-1.0, 0.0], dtype="float32")
    assert cosine_score(a, b) == pytest.approx(-1.0, abs=1e-6)


def test_build_text_index_unique_texts():
    """build_text_index should deduplicate texts and return text->index mapping."""
    from scripts.semantic_validation_phase3 import build_text_index

    records = [
        {"binary_root_meaning": "meaning A", "axial_meaning": "axial 1"},
        {"binary_root_meaning": "meaning A", "axial_meaning": "axial 2"},
        {"binary_root_meaning": "meaning B", "axial_meaning": "axial 1"},
    ]
    brm_index, ax_index = build_text_index(records)
    # binary_root_meaning has 2 unique texts
    assert len(brm_index) == 2
    assert "meaning A" in brm_index
    assert "meaning B" in brm_index
    # axial_meaning has 2 unique texts
    assert len(ax_index) == 2
    assert "axial 1" in ax_index
    assert "axial 2" in ax_index


def test_build_text_index_skips_empty():
    """build_text_index should skip records with empty meanings."""
    from scripts.semantic_validation_phase3 import build_text_index

    records = [
        {"binary_root_meaning": "", "axial_meaning": "axial 1"},
        {"binary_root_meaning": "meaning A", "axial_meaning": ""},
        {"binary_root_meaning": "meaning A", "axial_meaning": "axial 1"},
    ]
    brm_index, ax_index = build_text_index(records)
    assert len(brm_index) == 1  # only "meaning A"
    assert len(ax_index) == 1  # only "axial 1"


def test_compute_scores_with_mock_embeddings():
    """compute_scores should pair each record with its correct vectors and score."""
    from scripts.semantic_validation_phase3 import compute_scores

    # Fake embeddings: 3-dim, L2-normalized
    brm_embeddings = {
        "meaning A": np.array([1.0, 0.0, 0.0], dtype="float32"),
        "meaning B": np.array([0.0, 1.0, 0.0], dtype="float32"),
    }
    ax_embeddings = {
        "axial 1": np.array([1.0, 0.0, 0.0], dtype="float32"),  # identical to meaning A
        "axial 2": np.array([0.0, 0.0, 1.0], dtype="float32"),  # orthogonal to both
    }
    records = [
        {"tri_root": "abc", "binary_root_meaning": "meaning A", "axial_meaning": "axial 1"},
        {"tri_root": "def", "binary_root_meaning": "meaning A", "axial_meaning": "axial 2"},
        {"tri_root": "ghi", "binary_root_meaning": "meaning B", "axial_meaning": "axial 1"},
    ]
    scores = compute_scores(records, brm_embeddings, ax_embeddings)
    assert len(scores) == 3
    assert scores[0]["tri_root"] == "abc"
    assert scores[0]["semantic_score"] == pytest.approx(1.0, abs=1e-6)  # identical
    assert scores[1]["semantic_score"] == pytest.approx(0.0, abs=1e-6)  # orthogonal
    assert scores[2]["semantic_score"] == pytest.approx(0.0, abs=1e-6)  # orthogonal


def test_compute_scores_skips_missing_embeddings():
    """Records whose meaning text wasn't embedded should be skipped."""
    from scripts.semantic_validation_phase3 import compute_scores

    brm_embeddings = {"meaning A": np.array([1.0, 0.0], dtype="float32")}
    ax_embeddings = {"axial 1": np.array([1.0, 0.0], dtype="float32")}
    records = [
        {"tri_root": "abc", "binary_root_meaning": "meaning A", "axial_meaning": "axial 1"},
        {"tri_root": "def", "binary_root_meaning": "UNKNOWN", "axial_meaning": "axial 1"},
    ]
    scores = compute_scores(records, brm_embeddings, ax_embeddings)
    assert len(scores) == 1
    assert scores[0]["tri_root"] == "abc"


def test_build_report_structure():
    """build_report should produce correct distribution stats."""
    from scripts.semantic_validation_phase3 import build_report

    scored = [
        {"tri_root": "abc", "binary_root": "ab", "binary_root_meaning": "m1", "axial_meaning": "a1", "semantic_score": 0.9},
        {"tri_root": "def", "binary_root": "de", "binary_root_meaning": "m2", "axial_meaning": "a2", "semantic_score": 0.5},
        {"tri_root": "ghi", "binary_root": "gh", "binary_root_meaning": "m3", "axial_meaning": "a3", "semantic_score": 0.1},
    ]
    report = build_report(scored)
    assert report["total_scored"] == 3
    assert report["mean"] == pytest.approx(0.5, abs=1e-6)
    assert report["median"] == pytest.approx(0.5, abs=1e-6)
    assert "q25" in report
    assert "q75" in report
    assert "std" in report
    assert len(report["top_10"]) == 3  # only 3 items, so all shown
    assert len(report["bottom_10"]) == 3
    assert report["top_10"][0]["tri_root"] == "abc"  # highest first
    assert report["bottom_10"][0]["tri_root"] == "ghi"  # lowest first
    assert "histogram" in report
```

**Step 2: Run test to verify it fails**

Run: `cd Juthoor-ArabicGenome-LV1 && python -m pytest tests/test_phase3_scoring.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.semantic_validation_phase3'`

**Step 3: Write minimal implementation**

Create `Juthoor-ArabicGenome-LV1/scripts/semantic_validation_phase3.py`:

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `cd Juthoor-ArabicGenome-LV1 && python -m pytest tests/test_phase3_scoring.py -v`
Expected: All 8 tests PASS

**Step 5: Commit**

```bash
git add Juthoor-ArabicGenome-LV1/scripts/semantic_validation_phase3.py Juthoor-ArabicGenome-LV1/tests/test_phase3_scoring.py
git commit -m "feat(lv1): add Phase 3 semantic validation scoring logic with tests"
```

---

### Task 2: Integration test with real muajam data (no model)

**Files:**
- Modify: `Juthoor-ArabicGenome-LV1/tests/test_phase3_scoring.py`

**Step 1: Write the failing test**

Append to `test_phase3_scoring.py`:

```python
def test_load_muajam_records_real_data():
    """Verify we can load the real muajam roots.jsonl and get expected structure."""
    from scripts.semantic_validation_phase3 import load_muajam_records

    records = load_muajam_records()
    assert len(records) == 1938
    # Check first record has required fields
    rec = records[0]
    assert "binary_root_meaning" in rec
    assert "axial_meaning" in rec
    assert "tri_root" in rec
    assert "binary_root" in rec


def test_build_text_index_real_data():
    """Verify text index from real data produces reasonable counts."""
    from scripts.semantic_validation_phase3 import load_muajam_records, build_text_index

    records = load_muajam_records()
    brm_index, ax_index = build_text_index(records)
    # We expect ~200-300 unique binary_root_meaning texts
    assert 100 < len(brm_index) < 500
    # We expect ~1500-1900 unique axial_meaning texts
    assert 1000 < len(ax_index) < 2000
    # All index values should be sequential
    assert set(brm_index.values()) == set(range(len(brm_index)))
    assert set(ax_index.values()) == set(range(len(ax_index)))
```

**Step 2: Run test to verify it fails (or passes — these depend on real data)**

Run: `cd Juthoor-ArabicGenome-LV1 && python -m pytest tests/test_phase3_scoring.py::test_load_muajam_records_real_data tests/test_phase3_scoring.py::test_build_text_index_real_data -v`
Expected: PASS if data file exists at correct path

**Step 3: Commit**

```bash
git add Juthoor-ArabicGenome-LV1/tests/test_phase3_scoring.py
git commit -m "test(lv1): add integration tests for Phase 3 muajam data loading"
```

---

### Task 3: Run the full pipeline (requires GPU/CPU + BGE-M3)

This task runs the actual script. It is NOT TDD — it's an execution step.

**Files:**
- Run: `Juthoor-ArabicGenome-LV1/scripts/semantic_validation_phase3.py`
- Output: `Juthoor-ArabicGenome-LV1/outputs/reports/semantic_validation.json`
- Modified: `Juthoor-ArabicGenome-LV1/outputs/genome_v2/*.jsonl` (30 files gain `semantic_score`)

**Step 1: Verify FlagEmbedding is installed**

Run: `python -c "from FlagEmbedding import BGEM3FlagModel; print('OK')"`
If FAIL: `pip install FlagEmbedding`

**Step 2: Run the script**

Run: `cd Juthoor-ArabicGenome-LV1 && python scripts/semantic_validation_phase3.py`

Expected output (approximate):
```
=== Phase 3: Semantic Validation ===

Loaded 1938 muajam records
Unique binary_root_meaning texts: ~200-300
Unique axial_meaning texts: ~1500-1800

Embedding binary_root_meaning texts...
  Shape: (~250, 1024)
Embedding axial_meaning texts...
  Shape: (~1600, 1024)

Computing semantic scores...
Scored ~1900 triconsonantal roots

Report written to: outputs/reports/semantic_validation.json
  Mean score:   <unknown — this is exploratory>
  ...

Enriching genome_v2 files with semantic_score...
Enriched ~1384 genome_v2 entries

=== Phase 3 complete ===
```

**Step 3: Verify output files**

Run: `python -c "import json; r=json.load(open('outputs/reports/semantic_validation.json',encoding='utf-8')); print('Scored:', r['total_scored'], 'Mean:', r['mean'], 'Median:', r['median'])"`

Run: `head -3 outputs/genome_v2/ب.jsonl` — verify matched entries have `"semantic_score":` field

**Step 4: Commit results**

```bash
git add Juthoor-ArabicGenome-LV1/outputs/reports/semantic_validation.json
git commit -m "data(lv1): Phase 3 semantic validation report"
```

Note: Do NOT commit genome_v2 changes yet — review scores first.

---

### Task 4: Review results and commit genome_v2

**Step 1: Analyze the report**

Run: `cd Juthoor-ArabicGenome-LV1 && python -c "
import json
r = json.load(open('outputs/reports/semantic_validation.json', encoding='utf-8'))
print('=== Semantic Validation Results ===')
print(f'Total scored: {r[\"total_scored\"]}')
print(f'Mean:   {r[\"mean\"]:.4f}')
print(f'Median: {r[\"median\"]:.4f}')
print(f'Std:    {r[\"std\"]:.4f}')
print(f'Range:  [{r[\"min\"]:.4f}, {r[\"max\"]:.4f}]')
print(f'IQR:    [{r[\"q25\"]:.4f}, {r[\"q75\"]:.4f}]')
print()
print('Histogram:')
for b in r['histogram']:
    bar = '#' * (b['count'] // 10)
    print(f'  [{b[\"bin_start\"]:.2f}, {b[\"bin_end\"]:.2f}): {b[\"count\"]:>4}  {bar}')
print()
print('Top 5:')
for s in r['top_10'][:5]:
    print(f'  {s[\"tri_root\"]:>6}  {s[\"semantic_score\"]:.4f}')
print('Bottom 5:')
for s in r['bottom_10'][:5]:
    print(f'  {s[\"tri_root\"]:>6}  {s[\"semantic_score\"]:.4f}')
"`

**Step 2: If distribution looks reasonable, commit genome_v2**

```bash
git add Juthoor-ArabicGenome-LV1/outputs/genome_v2/
git commit -m "data(lv1): enrich genome_v2 with semantic_score from Phase 3"
```

**Step 3: Update memory/docs**

Update `docs/plans/2026-02-25-genome-phase1-design.md` or create a Phase 3 summary note in the reports directory with key findings.

---

### Task 5: Final verification

**Step 1: Run all LV1 tests**

Run: `cd Juthoor-ArabicGenome-LV1 && python -m pytest tests/ -v`
Expected: All tests pass (existing 61 + new 10 = ~71 tests)

**Step 2: Run full monorepo tests**

Run: `python -m pytest Juthoor-DataCore-LV0/tests/ Juthoor-ArabicGenome-LV1/tests/ Juthoor-CognateDiscovery-LV2/tests/ -v -m "not slow"`
Expected: All ~366+ tests pass

**Step 3: Push**

```bash
git push origin main
```
