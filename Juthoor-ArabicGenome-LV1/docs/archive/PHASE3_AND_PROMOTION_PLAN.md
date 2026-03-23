# Phase 3 + Promotion Layer — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Phase 3 generative experiments (6.1, 6.2, 2.2, 6.4), build a promotion layer to export validated results to LV2/LV3, and produce the final Research Factory report.

**Architecture:** Three workstreams run in parallel: (A) Codex runs 4 heavy Phase 3 experiments, (B) Sonnet builds the promotion/export infrastructure and updates hypothesis statuses, (C) Opus reviews, writes the final synthesis, and decides promotions.

**Tech Stack:** Python 3.11+, numpy, scipy, sklearn (HDBSCAN, MLP), BGE-M3 embeddings (already computed), matplotlib.

---

## What's Done (DO NOT REBUILD)

### Completed Experiments (Phases 0-2)
| Exp | Hypothesis | Verdict | Output Path |
|-----|-----------|---------|-------------|
| 1.1 | H1 phonetic-semantic | Inconclusive | `axis1/mantel_result.json` |
| 1.2 | H8 positional semantics | **Supported** | `axis1/positional_summary.json` |
| 2.3 | H2 field coherence | **Supported** | `axis2/coherence_summary.json` |
| 3.1 | H3 modifier personality | Weak signal (z=3.5) | `axis3/consistency_scores.json` |
| 4.1 | H4/H5 metathesis | H4 weak, H5 supported | `axis4/classification_counts.json` |
| 4.3 | H6 substitution | Not supported | `axis4/spearman_result.json` |
| 5.1 | H1 CCA | Inconclusive | `axis5/cca_summary.json` |

### Stable Infrastructure
- Feature store: `outputs/research_factory/features/` (4 .npy files)
- Experiment runner: `factory/experiment_runner.py`
- Statistics: `scripts/research_factory/common/statistics.py`
- Visualization: `scripts/research_factory/common/visualization.py`
- Core models + loaders: `core/models.py`, `core/loaders.py`

---

## Workstream A: Phase 3 Experiments (Codex)

All 4 experiments are computation-heavy and independent of each other.

### Task A.1 — Meaning Predictor (Exp 6.1)
**Owner: Codex**
**Hypotheses:** H12 (root meaning is predictable from components)
**Output:** `outputs/research_factory/axis6/`

Script: `scripts/research_factory/axis6/exp_6_1_meaning_predictor.py`

**Method (updated from original plan with H8 finding):**
1. For each of 1,938 tri-roots: build input vector = `concat(binary_meaning_embedding, letter3_embedding, position_one_hot[3])`
   - `binary_meaning_embedding`: 1024-dim from feature store
   - `letter3_embedding`: 1024-dim letter embedding for the added letter
   - `position_one_hot`: [0,0,1] since added letter is always 3rd position
   - Total input: 2051 dims
2. Target: `axial_meaning_embedding` (1024-dim)
3. 80/20 stratified split (stratify by binary root to avoid data leakage)
4. Three models:
   - (a) **MLP**: 2-layer, ReLU, trained to minimize cosine distance
   - (b) **Linear baseline**: simple linear projection
   - (c) **Mean baseline**: predict the mean of all training axial embeddings
5. Metric: mean cosine similarity on held-out test set
6. Output: `prediction_results.json`, `model_comparison.json`, `scatter_predicted_vs_real.png`

**Success criteria:** MLP cosine > 0.6 on test set AND MLP > linear > mean baseline

**Test file:** `tests/test_phase3_meaning_predictor.py`
- Test train/test split preserves binary root groups
- Test MLP forward pass produces correct output shape
- Test cosine metric computation

---

### Task A.2 — Unsupervised Discovery (Exp 6.2)
**Owner: Codex**
**Hypothesis:** H11 (machine discovers binary structure without labels)
**Output:** `outputs/research_factory/axis6/`

Script: `scripts/research_factory/axis6/exp_6_2_unsupervised_discovery.py`

**Method:**
1. Load `axial_meaning_embeddings.npy` (1938 × 1024)
2. Reduce to 50 dims with PCA (preserve ~90% variance)
3. Run HDBSCAN with `min_cluster_size` in [5, 10, 20, 30]
4. For each run: compute Adjusted Rand Index (ARI) against Jabal's binary_root labels
5. Also compute: Normalized Mutual Information (NMI), silhouette score
6. Visualize: UMAP 2D projection colored by (a) HDBSCAN clusters (b) Jabal families
7. Output: `unsupervised_results.json`, `umap_hdbscan.png`, `umap_jabal.png`, `ari_by_min_cluster.json`

**Success criteria:** Best ARI > 0.3

**Test file:** `tests/test_phase3_unsupervised.py`
- Test PCA reduction preserves shape
- Test ARI computation with known clusters

---

### Task A.3 — Missing Combinations (Exp 2.2)
**Owner: Codex**
**Hypothesis:** H7 (missing roots reflect semantic conflict, not randomness)
**Output:** `outputs/research_factory/axis2/`

Script: `scripts/research_factory/axis2/exp_2_2_missing_combinations.py`

**Method:**
1. Generate all 784 possible 2-letter combinations from 28 letters (28×28, excluding same-letter)
   - Actually: 28 letters, pairs (a,b) where a≠b = 28×27 = 756, plus 28 same-letter = 784
2. Identify 457 existing vs 327 missing binary roots
3. For each combination (existing or missing): compute semantic compatibility score
   - `compatibility = cosine(letter1_embedding, letter2_embedding)`
4. Compare distributions: existing vs missing compatibility scores
5. Statistical test: Wilcoxon rank-sum + Cohen's d
6. Output: `missing_analysis.json`, `compatibility_violin.png`, `missing_heatmap.png`

**Success criteria:** Significant difference (p < 0.01) between existing and missing compatibility scores

**Test file:** `tests/test_phase3_missing.py`
- Test all 784 combinations generated correctly
- Test existing/missing partition matches known counts

---

### Task A.4 — Phantom Roots (Exp 6.4)
**Owner: Codex**
**Hypothesis:** H12 (predictive power — theory is not just descriptive)
**Output:** `outputs/research_factory/axis6/`

Script: `scripts/research_factory/axis6/exp_6_4_phantom_roots.py`

**Method:**
1. Using modifier profiles from 3.1 + field coherence from 2.3:
   - "Compatible" phantom: take a high-coherence binary root + a letter whose modifier personality aligns with the family's semantic direction → predict this root SHOULD exist
   - "Incompatible" phantom: take a binary root + a letter whose modifier goes against the field → predict this root should NOT exist
2. Generate 200 compatible + 200 incompatible phantom tri-root strings
3. Check each against the full 12,333 genome_v2 entries: does it exist?
4. Compare: do compatible phantoms exist more often than incompatible ones?
5. Output: `phantom_results.json`, `phantom_accuracy.json`

**Success criteria:** Compatible phantoms found at significantly higher rate than incompatible

**Note:** This experiment depends on modifier profiles (3.1) having SOME signal. Given z=3.5 above shuffle, there is enough signal to attempt this, but results may be noisy.

**Test file:** `tests/test_phase3_phantom.py`
- Test phantom generation produces valid Arabic letter combinations
- Test existence check against genome_v2

---

## Workstream B: Promotion Layer + Registry Updates (Sonnet via Claude Code)

These are structural/infrastructure tasks that don't need heavy computation.

### Task B.1 — Update Hypothesis Registry with Phase 1+2 Verdicts
**Owner: Sonnet**
**Output:** `resources/hypotheses.yaml` (update statuses)

Update the YAML with actual verdicts:
```yaml
# Change status field for each tested hypothesis:
H1: status: "inconclusive"    # was "pending"
H2: status: "supported"       # was "pending"
H3: status: "weak_signal"     # was "pending"
H4: status: "weakly_supported" # was "pending"
H5: status: "supported"       # was "pending"
H6: status: "not_supported"   # was "pending"
H8: status: "supported"       # was "pending"
# H7, H9, H10, H11, H12 remain "pending"
```

Also add these fields to each tested hypothesis:
```yaml
  evidence:
    experiment_id: "2.3"
    key_metric: "real_mean=0.540 vs baseline=0.518, >11σ"
    verdict_date: "2026-03-14"
```

**Test:** Existing `test_hypotheses_yaml.py` must still pass (update the "all pending" assertion to allow new statuses).

---

### Task B.2 — Promotion Export Module
**Owner: Sonnet**
**Output:** `src/juthoor_arabicgenome_lv1/factory/promotions.py`

Create a module that exports promoted results into a format LV2 and LV3 can consume:

```python
def export_promoted_results(output_dir: Path) -> dict:
    """Export all promoted (supported) findings to a structured directory.

    Creates:
      output_dir/
        promoted_features/
          field_coherence_scores.jsonl    # per-family coherence (from H2/2.3)
          positional_profiles.jsonl       # per-letter positional data (from H8/1.2)
          metathesis_pairs.jsonl          # annotated pairs (from H5/4.1)
        evidence_cards/
          H2_field_coherence.json         # structured evidence card
          H5_order_matters.json
          H8_positional_semantics.json
        promotion_manifest.json           # what was promoted and when
    """
```

Each **evidence card** is a structured JSON:
```json
{
  "hypothesis_id": "H2",
  "claim": "The binary root defines a stable semantic field",
  "source": "Jabal",
  "experiment_id": "2.3",
  "status": "supported",
  "key_metric": "real_mean=0.540 vs baseline=0.518",
  "significance": ">11 sigma above random baseline",
  "families_tested": 396,
  "promotion_date": "2026-03-14",
  "data_file": "promoted_features/field_coherence_scores.jsonl"
}
```

**Test file:** `tests/test_promotions.py`
- Test export creates expected directory structure
- Test evidence cards have required fields
- Test promotion manifest is valid JSON
- Use `tmp_path`

---

### Task B.3 — LV1 README Update with Phase 2 Results
**Owner: Sonnet**
**Output:** Update `Juthoor-ArabicGenome-LV1/README.md`

Update the hypothesis table and Phase results section to include Phase 2 verdicts.
Update test count from 175 to current (183).

---

### Task B.4 — Final Hypothesis Dashboard Script
**Owner: Sonnet**
**Output:** `scripts/research_factory/common/build_dashboard.py`

A simple script that reads all `*_result.json` files from `outputs/research_factory/reports/` and `hypothesis_status.json`, then generates a single `outputs/research_factory/reports/hypothesis_dashboard.json`:

```json
{
  "generated": "2026-03-14T...",
  "hypotheses": [
    {
      "id": "H1", "name": "...", "status": "inconclusive",
      "experiments": [
        {"id": "1.1", "metric": "mantel_r=-0.152", "verdict": "not_significant"},
        {"id": "5.1", "metric": "cca_r=0.962,perm_p=0.149", "verdict": "not_significant"}
      ]
    },
    ...
  ],
  "summary": {
    "supported": 3, "weakly_supported": 1, "weak_signal": 1,
    "not_supported": 1, "inconclusive": 1, "pending": 5
  }
}
```

**Test file:** `tests/test_build_dashboard.py`

---

## Workstream C: Opus Review + Final Synthesis

### Task C.1 — Phase 3 Review Checkpoint
**Owner: Opus**
**When:** After Codex completes all 4 Phase 3 experiments
**Output:** `outputs/research_factory/reports/phase3_summary.md`

Review all Phase 3 results. Update H7, H11, H12 statuses.

---

### Task C.2 — Final Research Factory Report
**Owner: Opus**
**When:** After B.2 (promotions) and C.1 (Phase 3 review) are complete
**Output:** `outputs/research_factory/reports/FINAL_SYNTHESIS.md`

The definitive summary of the entire Research Factory:
- Which hypotheses survived, which fell
- What the data tells us about Jabal's theory
- What LV2 and LV3 should do with the promoted results
- What questions remain open
- Comparison: what classical Arabic grammarians claimed vs what computation shows

---

### Task C.3 — Promotion Decisions
**Owner: Opus**
**When:** After C.1
**Output:** Run `promotions.py` with final decisions, push promoted features

Decide which Phase 3 results (if any) get promoted alongside H2, H5, H8.

---

## Dependency Graph

```
Workstream A (Codex)          Workstream B (Sonnet)          Workstream C (Opus)
═══════════════════          ═══════════════════          ═══════════════════

A.1 meaning predictor ─┐     B.1 update hypotheses ──┐
A.2 unsupervised    ───┤     B.2 promotion module  ──┤
A.3 missing combos  ───┤     B.3 README update     ──┤
A.4 phantom roots   ───┘     B.4 dashboard script  ──┘
        │                            │
        ▼                            ▼
   [all A done]              [all B done]
        │                            │
        └──────────┬─────────────────┘
                   ▼
           C.1 Phase 3 review (Opus)
                   │
                   ▼
           C.2 Final synthesis (Opus)
                   │
                   ▼
           C.3 Run promotions (Opus)
                   │
                   ▼
              COMMIT + PUSH
```

**Key:** A and B run fully in parallel. C starts only after both complete.

---

## Execution Order

### Immediate (can start NOW in parallel):

**Claude Code (Sonnet subagents):** B.1 + B.2 + B.3 + B.4
- B.1 and B.3 are independent
- B.2 is independent
- B.4 is independent
- All 4 can run in parallel

**Codex (autonomous):** A.1 + A.2 + A.3 + A.4
- All 4 experiments are independent
- A.1 and A.2 are the most valuable (H12, H11)
- A.3 and A.4 are supplementary
- Can run in parallel if compute allows

### After both complete:

**Claude Code (Opus):** C.1 → C.2 → C.3

---

## Context Files for Codex

Before starting ANY Phase 3 task, read:
1. `docs/plans/RESEARCH_FACTORY_MASTER_PLAN.md` — experiment specs
2. `outputs/research_factory/reports/phase2_summary.md` — H8 finding (important for A.1)
3. Feature store contents: `outputs/research_factory/features/` (4 .npy + .meta.json)
4. `data/muajam/roots.jsonl` — source data
5. `src/juthoor_arabicgenome_lv1/core/loaders.py` — data loading API
6. `src/juthoor_arabicgenome_lv1/factory/feature_store.py` — feature loading API
7. `src/juthoor_arabicgenome_lv1/factory/experiment_runner.py` — experiment runner API

## Quality Gates

Same as Phase 0-2:
1. No import errors
2. Tests exist and pass
3. Scripts run on real data
4. Outputs at expected paths
5. No modification to core data or stable outputs

---

*Phase 3 + Promotion Layer Plan*
*Juthoor Research Factory*
*2026-03-14*
