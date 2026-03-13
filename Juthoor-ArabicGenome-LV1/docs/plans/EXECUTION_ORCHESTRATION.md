# Research Factory — Execution Orchestration
## Multi-Agent Work Plan (Claude Code + OpenAI Codex)

**Date:** 2026-03-13
**Master Plan:** `docs/plans/RESEARCH_FACTORY_MASTER_PLAN.md`
**Repo:** `Juthoor-Linguistic-Genealogy` (monorepo, Python workspace)

---

## Agent Roster

| Agent | Model | Role | Strengths | Session Type |
|-------|-------|------|-----------|--------------|
| **Opus** | Claude Opus 4.6 | Architect & Reviewer | Design decisions, integration, code review, orchestration | Claude Code (interactive) |
| **Sonnet** | Claude Sonnet 4.6 | Builder | Fast implementation, tests, boilerplate, data wiring | Claude Code (subagent / parallel) |
| **Codex** | OpenAI Codex 5.4 | Heavy Lifter | Computation scripts, statistical analysis, visualization, bulk processing | Codex CLI (autonomous tasks) |

**Rule:** Every task has ONE owner. No shared ownership. Dependencies are explicit.

---

## What Already Exists (DO NOT REBUILD)

Before writing any code, read these to understand the current state:

```
STABLE — read-only references:
├── data/muajam/roots.jsonl              ← 1,938 tri-roots with meanings
├── data/muajam/letter_meanings.jsonl    ← 28 letters with semantic axioms
├── outputs/genome_v2/<bab>.jsonl        ← 12,333 roots enriched (Phase 1+2)
├── outputs/reports/semantic_validation.json  ← Phase 3 scores (mean 0.558)
└── LV2 embedder (importable):
    from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import BgeM3Embedder
    # .embed(texts: list[str]) -> np.ndarray  (1024-dim, L2-normalized)
```

The Research Factory builds ON TOP of this. It never modifies these files.

---

## Phase 0: Infrastructure (Week 1)

### Task 0.1 — Core Data Models
**Owner: Sonnet**
**Output:** `src/juthoor_arabicgenome_lv1/core/models.py`

Create frozen dataclasses for the 7 entity types from the master plan.
Read `data/muajam/roots.jsonl` and `letter_meanings.jsonl` to understand exact field names.

```python
# Expected entities (frozen dataclasses):
# Letter, BinaryRoot, TriliteralRoot, RootFamily,
# MetathesisPair, SubstitutionPair, PermutationGroup
```

**Acceptance:** `pytest` imports all 7 classes, constructs each from sample data.

---

### Task 0.2 — Core Data Loaders
**Owner: Sonnet**
**Depends on:** 0.1
**Output:** `src/juthoor_arabicgenome_lv1/core/loaders.py`

Functions to load all core data into the dataclass models:
- `load_letters() -> list[Letter]` — from `letter_meanings.jsonl`
- `load_binary_roots() -> list[BinaryRoot]` — from `roots.jsonl` (deduplicate by binary_root)
- `load_triliteral_roots() -> list[TriliteralRoot]` — from `roots.jsonl`
- `load_root_families() -> dict[str, RootFamily]` — group triliterals by binary_root
- `load_genome_v2(bab: str) -> list[dict]` — from `outputs/genome_v2/<bab>.jsonl`

**Acceptance:** Unit tests for each loader with real data paths.

---

### Task 0.3 — Phonetic Resources (Makhaarij + Sifaat)
**Owner: Codex**
**Output:** `resources/phonetics/makhaarij.json` + `resources/phonetics/sifaat.json`

Create two JSON files based on classical Arabic phonetics (Al-Khalil's 17 makhaarij):

**makhaarij.json** — For each of 28 letters, its place of articulation:
```json
{
  "ء": {"makhraj": "الحلق_أقصى", "makhraj_id": 1, "makhraj_en": "deepest_throat"},
  "ه": {"makhraj": "الحلق_أقصى", "makhraj_id": 1, "makhraj_en": "deepest_throat"},
  "ع": {"makhraj": "الحلق_وسط", "makhraj_id": 2, "makhraj_en": "mid_throat"},
  ...
}
```

**sifaat.json** — For each of 28 letters, binary articulatory features:
```json
{
  "ب": {
    "jahr": true,       // voiced
    "shidda": true,     // plosive (vs. rakhawa/fricative)
    "itbaq": false,     // emphatic (pharyngealized)
    "isti3la": false,    // raised (uvular/pharyngeal)
    "qalqala": true,    // bouncy release
    "safeer": false,    // whistling
    "ghunna": false,    // nasality
    "inhiraf": false,   // lateral
    "takrir": false,    // trill
    "istitala": false   // elongation
  },
  ...
}
```

**Context files to read:**
- `docs/plans/RESEARCH_FACTORY_MASTER_PLAN.md` — for the full plan
- `data/muajam/letter_meanings.jsonl` — for the 28 letters

**Acceptance:** Valid JSON, all 28 letters present in both files, no missing letters.

---

### Task 0.4 — Hypothesis Registry YAML
**Owner: Sonnet**
**Output:** `resources/hypotheses.yaml`

Transcribe the 12 hypotheses from the master plan into machine-readable YAML.
Each entry: `id`, `name`, `claim`, `source`, `experiments` (list), `status: pending`.

**Acceptance:** Valid YAML, 12 entries, parseable by PyYAML.

---

### Task 0.5 — Feature Store Module
**Owner: Sonnet**
**Depends on:** 0.1
**Output:** `src/juthoor_arabicgenome_lv1/factory/feature_store.py`

Simple read/write for numpy arrays and metadata:
- `save_feature(name: str, array: np.ndarray, meta: dict)` — saves `.npy` + `.meta.json` to `outputs/research_factory/features/`
- `load_feature(name: str) -> tuple[np.ndarray, dict]`
- `feature_exists(name: str) -> bool`
- `list_features() -> list[str]`

**Acceptance:** Round-trip test (save then load, compare arrays).

---

### Task 0.6 — Experiment Runner Framework
**Owner: Sonnet**
**Depends on:** 0.4, 0.5
**Output:** `src/juthoor_arabicgenome_lv1/factory/experiment_runner.py`

Lightweight runner that:
1. Reads experiment config from YAML or dict
2. Checks that required features exist in the store
3. Logs start/end time, status, metrics to `outputs/research_factory/reports/<exp_id>_result.json`
4. Updates hypothesis status in a local `outputs/research_factory/hypothesis_status.json`

NOT a complex framework. Just a thin wrapper with logging.

**Acceptance:** Can run a dummy experiment that reads a feature and writes a result JSON.

---

### Task 0.7 — Statistics Utilities
**Owner: Codex**
**Output:** `scripts/research_factory/common/statistics.py`

Implement these statistical functions (used across multiple experiments):
- `mantel_test(dist_matrix_1, dist_matrix_2, permutations=9999) -> (r, p)` — matrix correlation test
- `bootstrap_ci(values, stat_fn, n_boot=10000, alpha=0.05) -> (low, high)` — confidence intervals
- `permutation_test(group_a, group_b, stat_fn, n_perm=9999) -> p` — generic permutation test
- `cohens_d(group_a, group_b) -> float` — effect size

Also wrap scipy: `spearman_corr`, `wilcoxon_rank_sum`, `kruskal_wallis`.

**Context files to read:**
- `docs/plans/RESEARCH_FACTORY_MASTER_PLAN.md` — experiments 1.1 (Mantel), 4.1 (Wilcoxon), 4.3 (Spearman)

**Acceptance:** Each function tested with synthetic data. Mantel test verified against known correlation.

---

### Task 0.8 — Visualization Utilities
**Owner: Codex**
**Output:** `scripts/research_factory/common/visualization.py`

Reusable plotting functions (matplotlib, Arabic-safe fonts):
- `plot_heatmap(matrix, labels, title, out_path)` — 28x28 or NxN with Arabic letter labels
- `plot_dendrogram(linkage, labels, title, out_path)` — hierarchical clustering
- `plot_violin(groups: dict[str, list], title, out_path)` — comparison distributions
- `plot_scatter_with_labels(x, y, labels, title, out_path)` — PCA/UMAP plots
- `plot_distribution(values, title, out_path, bins=50)` — histogram with stats overlay

All functions must:
- Support Arabic text (use a font that renders Arabic correctly)
- Save to PNG at 300 DPI
- Return the figure object for optional display

**Acceptance:** Each function produces a valid PNG from synthetic data.

---

### Task 0.9 — Compute All Embeddings (Feature Store Population)
**Owner: Codex**
**Depends on:** 0.1, 0.2, 0.5
**Output:** `outputs/research_factory/features/` — 3 `.npy` files + metadata

Script: `scripts/research_factory/phase0_setup/compute_all_embeddings.py`

1. Load 28 letter meanings → embed → save as `letter_embeddings.npy` (28 × 1024)
2. Load ~457 unique binary_root_meanings → embed → save as `binary_meaning_embeddings.npy`
3. Load ~1,938 axial_meanings → embed → save as `axial_meaning_embeddings.npy`

Each `.meta.json` must record: entity IDs in same order as rows, model used, timestamp.

**Import:** `from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import BgeM3Embedder`

**Context files to read:**
- `Juthoor-ArabicGenome-LV1/scripts/semantic_validation_phase3.py` — shows how Phase 3 already uses BgeM3Embedder
- `data/muajam/roots.jsonl` — source data
- `data/muajam/letter_meanings.jsonl` — source data

**Acceptance:** All 3 .npy files exist, shapes correct, metadata JSON valid.

---

### Task 0.10 — Build Articulatory Vectors
**Owner: Sonnet**
**Depends on:** 0.3, 0.5
**Output:** `outputs/research_factory/features/articulatory_vectors.npy` + metadata

Script: `scripts/research_factory/phase0_setup/build_articulatory_vectors.py`

Load `makhaarij.json` + `sifaat.json` → build a feature vector per letter:
- One-hot makhraj (17 positions)
- Binary sifaat (10 features from sifaat.json)
- Total: 28 letters × 27 features → save to feature store

**Acceptance:** Shape (28, 27), metadata maps row index to letter.

---

## Phase 0 Dependency Graph

```
         0.1 (models)
        / |  \
      /   |   \
    0.2  0.4  0.5
    |     |    |
    |     0.6--+
    |          |
    0.9--------+--- 0.3
    |               |
    |              0.10
    |
    0.7 (independent)
    0.8 (independent)
```

**Parallel execution:**
- Batch 1 (parallel): 0.1, 0.3, 0.4, 0.7, 0.8
- Batch 2 (after 0.1): 0.2, 0.5
- Batch 3 (after 0.2 + 0.5): 0.6, 0.9
- Batch 4 (after 0.3 + 0.5): 0.10

---

## Phase 1: Core Science (Weeks 2-5)

### Task 1.1 — Letter Similarity Matrix (Exp 1.1)
**Owner: Codex**
**Depends on:** 0.9 (embeddings), 0.10 (articulatory), 0.7 (statistics), 0.8 (visualization)
**Output:** `outputs/research_factory/axis1/`

Script: `scripts/research_factory/axis1/exp_1_1_letter_similarity.py`

1. Load `letter_embeddings.npy` → compute 28×28 cosine similarity matrix (semantic)
2. Load `articulatory_vectors.npy` → compute 28×28 distance matrix (phonetic)
3. Hierarchical clustering on semantic matrix → dendrogram
4. Mantel test: correlation between phonetic distance and semantic distance
5. Output: `letter_similarity.jsonl`, `semantic_heatmap.png`, `dendrogram.png`, `mantel_result.json`

**Success criteria:** Mantel r > 0.3, p < 0.01

**Context files to read:**
- `docs/plans/RESEARCH_FACTORY_MASTER_PLAN.md` — experiment 1.1 spec
- `resources/phonetics/makhaarij.json` — for makhraj grouping validation

---

### Task 1.2 — Field Coherence (Exp 2.3)
**Owner: Codex**
**Depends on:** 0.9 (embeddings), 0.7 (statistics), 0.8 (visualization)
**Output:** `outputs/research_factory/axis2/`

Script: `scripts/research_factory/axis2/exp_2_3_field_coherence.py`

1. Group 1,938 tri-roots by binary_root → ~457 families
2. For each family (≥2 members): mean pairwise cosine of `axial_meaning_embeddings`
3. Random baseline: shuffle family assignments, repeat 1000×, compute same metric
4. Rank families by coherence
5. Output: `field_coherence.jsonl` (per-family scores), `coherence_distribution.png`, `top_bottom_20.json`

**Success criteria:** Mean real coherence > random baseline by 2σ

---

### Task 1.3 — Modifier Personality (Exp 3.1) ★★★★★
**Owner: Codex**
**Depends on:** 0.9 (embeddings), 0.7 (statistics), 0.8 (visualization)
**Output:** `outputs/research_factory/axis3/`

Script: `scripts/research_factory/axis3/exp_3_1_modifier_personality.py`

This is the FLAGSHIP experiment. The most important test of the entire theory.

1. For each tri-root: compute `modifier_vector = embed(axial_meaning) - embed(binary_root_meaning)`
2. Group modifier_vectors by `added_letter` (the 3rd letter)
3. For each letter as 3rd: compute `personality = mean(modifier_vectors)`
4. `consistency = mean(pairwise_cosine(modifier_vectors))` within same letter group
5. Compare: does the personality direction correlate with the letter's own meaning embedding?
6. Output: `modifier_profiles.jsonl` (28 cards), `consistency_scores.json`, `modifier_heatmap.png`, `personality_vs_letter_meaning.png`

**Success criteria:** consistency > 0.5 for >60% of letters

**Context files to read:**
- `docs/plans/RESEARCH_FACTORY_MASTER_PLAN.md` — experiment 3.1 spec (read carefully)
- `data/muajam/roots.jsonl` — `added_letter` field is the third letter
- `data/muajam/letter_meanings.jsonl` — letter meaning to compare personality against

---

### Phase 1 Review Checkpoint
**Owner: Opus**

After all 3 experiments complete:
1. Review all result JSONs and plots
2. Write `outputs/research_factory/reports/phase1_summary.md` — what passed, what failed, what it means
3. Decide: proceed to Phase 2, or re-run experiments with adjustments?
4. Update hypothesis statuses (H1, H2, H3)

---

## Phase 2: Metathesis, Substitution, Position (Weeks 6-9)

### Task 2.1 — Binary Metathesis (Exp 4.1)
**Owner: Codex**
**Depends on:** Phase 0 complete
**Output:** `outputs/research_factory/axis4/`

Script: `scripts/research_factory/axis4/exp_4_1_binary_metathesis.py`

1. Find all (XY, YX) pairs among 457 binary roots → ~166 pairs
2. For each pair: `cosine(embed(meaning_XY), embed(meaning_YX))`
3. Control group: 166 random non-metathetic pairs → same metric
4. Wilcoxon rank-sum test between real vs control
5. Classify: (a) similar >0.7 (b) divergent <0.3 (c) middle
6. Output: `metathesis_analysis.jsonl`, `violin_plot.png`, `classification_counts.json`

**The key question:** If >50% are category (a) → Ibn Jinni's claim holds. If <20% → Jabal's view wins.

---

### Task 2.2 — Phonetic Substitution (Exp 4.3)
**Owner: Codex**
**Depends on:** Phase 0 complete
**Output:** `outputs/research_factory/axis4/`

Script: `scripts/research_factory/axis4/exp_4_3_phonetic_substitution.py`

1. Find all tri-root pairs (XYZ, XY'Z) that differ by exactly one letter
2. Compute `makhraj_distance(Y, Y')` from articulatory vectors
3. Compute `semantic_distance(meaning_XYZ, meaning_XY'Z)` from embeddings
4. Spearman correlation between the two distances
5. Output: `substitution_analysis.jsonl`, `scatter_plot.png`, `spearman_result.json`

**Success criteria:** ρ > 0.2, p < 0.01

---

### Task 2.3 — Sound-Meaning CCA (Exp 5.1)
**Owner: Codex**
**Depends on:** Phase 0 complete
**Output:** `outputs/research_factory/axis5/`

Script: `scripts/research_factory/axis5/exp_5_1_sound_meaning_matrix.py`

Canonical Correlation Analysis between articulatory features and semantic embeddings.
Uses `sklearn.cross_decomposition.CCA` or manual implementation.

**Success criteria:** First canonical correlation > 0.4

---

### Task 2.4 — Positional Semantics (Exp 1.2)
**Owner: Codex**
**Depends on:** Phase 0 complete
**Output:** `outputs/research_factory/axis1/`

Script: `scripts/research_factory/axis1/exp_1_2_positional_semantics.py`

1. For each of 28 letters: 3 groups (as 1st letter, as 2nd, as 3rd in tri-roots)
2. Compute intra-group coherence (mean pairwise cosine of axial_meanings)
3. Compare: does coherence differ by position?
4. Kruskal-Wallis test across the 3 positions per letter

---

### Phase 2 Review Checkpoint
**Owner: Opus**

Review all Phase 2 results. Update H4, H5, H6, H8 statuses.
Write `outputs/research_factory/reports/phase2_summary.md`.

---

## Phase 3: Generative AI (Weeks 10-13)

### Task 3.1 — Meaning Predictor (Exp 6.1)
**Owner: Codex**

Train a model to predict `axial_meaning` from `binary_root_meaning + letter3_meaning`.
Three approaches: (a) Claude few-shot, (b) MLP on embeddings, (c) small Transformer.
80/20 train/test split. Metric: cosine similarity on held-out set.

---

### Task 3.2 — Unsupervised Discovery (Exp 6.2)
**Owner: Codex**

HDBSCAN clustering on axial_meaning_embeddings with binary_root labels hidden.
Evaluate with Adjusted Rand Index against Jabal's classification.

---

### Task 3.3 — Missing Combinations (Exp 2.2)
**Owner: Codex**

Identify 327 missing binary combinations. Compare semantic compatibility scores between
existing (457) vs missing (327) combinations. Statistical test for difference.

---

### Task 3.4 — Phantom Roots (Exp 6.4)
**Owner: Codex**

Generate "compatible" and "incompatible" root combinations using the modifier profiles.
Check against real data: do compatible inventions tend to exist? Do incompatible ones tend to be absent?

---

### Phase 3 Review Checkpoint
**Owner: Opus**

Review all Phase 3 results. Update H7, H11, H12. Decide on promotions.
Write `outputs/research_factory/reports/phase3_summary.md`.

---

## Task Assignment Summary

### Sonnet 4.6 Tasks (Fast Builder — via Claude Code subagents)

| Task | Description | Est. Time |
|------|-------------|-----------|
| 0.1 | Core data models (7 dataclasses) | 30 min |
| 0.2 | Core data loaders (5 functions) | 45 min |
| 0.4 | Hypotheses YAML (transcribe 12 entries) | 20 min |
| 0.5 | Feature store module (save/load numpy) | 30 min |
| 0.6 | Experiment runner framework | 45 min |
| 0.10 | Build articulatory vectors script | 30 min |

**Total: ~6 tasks, ~3.5 hours**
Sonnet handles all boilerplate, data wiring, and framework code. These are well-specified tasks with clear inputs/outputs.

### Codex 5.4 Tasks (Heavy Lifter — autonomous)

| Task | Description | Est. Time |
|------|-------------|-----------|
| 0.3 | Phonetic resources (makhaarij + sifaat JSON) | 1 hour |
| 0.7 | Statistics utilities (Mantel, bootstrap, permutation) | 2 hours |
| 0.8 | Visualization utilities (heatmap, dendrogram, violin) | 2 hours |
| 0.9 | Compute all embeddings (batch BGE-M3) | 1.5 hours |
| 1.1 | Letter similarity matrix experiment | 2 hours |
| 1.2 | Field coherence experiment | 2 hours |
| 1.3 | Modifier personality experiment ★ | 3 hours |
| 2.1 | Binary metathesis experiment | 2 hours |
| 2.2 | Phonetic substitution experiment | 2 hours |
| 2.3 | Sound-meaning CCA experiment | 1.5 hours |
| 2.4 | Positional semantics experiment | 1.5 hours |
| 3.1-3.4 | Phase 3 generative experiments | 8 hours |

**Total: ~12 tasks, ~28 hours**
Codex handles all computation-heavy work: embeddings, statistical analysis, visualization, and experiment scripts.

### Opus 4.6 Tasks (Architect & Reviewer — interactive)

| Task | Description | When |
|------|-------------|------|
| Architecture design | Already done (master plan) | Done |
| This orchestration plan | Assigns all work | Done |
| Phase 0 review | Verify infrastructure before experiments | After Phase 0 |
| Phase 1 review | Analyze results, update hypotheses | After Phase 1 |
| Phase 2 review | Analyze results, decide promotions | After Phase 2 |
| Phase 3 review | Final analysis, write conclusions | After Phase 3 |
| Integration decisions | When agents hit ambiguity or conflicts | On demand |

**Total: ~4 review checkpoints + on-demand consultation**
Opus stays lean. Reviews results, makes judgment calls, doesn't write bulk code.

---

## Execution Order (Gantt-style)

```
Week 1 — Phase 0: Infrastructure
├─ Day 1-2: Sonnet → 0.1, 0.4 (parallel) | Codex → 0.3, 0.7, 0.8 (parallel)
├─ Day 2-3: Sonnet → 0.2, 0.5 (after 0.1) | Codex continues 0.7, 0.8
├─ Day 3-4: Sonnet → 0.6 (after 0.5), 0.10 (after 0.3) | Codex → 0.9 (after 0.2+0.5)
├─ Day 5: Opus → Phase 0 review checkpoint
│
Week 2-3 — Phase 1: Core Science
├─ Codex → 1.1, 1.2, 1.3 (can run in parallel if GPU allows)
├─ Opus → Phase 1 review checkpoint (after all 3 complete)
│
Week 4-5 — Phase 2: Metathesis + Substitution
├─ Codex → 2.1, 2.2, 2.3, 2.4 (parallel)
├─ Opus → Phase 2 review checkpoint
│
Week 6-8 — Phase 3: Generative
├─ Codex → 3.1, 3.2, 3.3, 3.4
├─ Opus → Phase 3 review + final report
```

---

## File Naming Conventions

All agents must follow these conventions:

| Type | Location | Pattern |
|------|----------|---------|
| Source modules | `src/juthoor_arabicgenome_lv1/core/` | `models.py`, `loaders.py` |
| Factory modules | `src/juthoor_arabicgenome_lv1/factory/` | `feature_store.py`, etc. |
| Shared utilities | `scripts/research_factory/common/` | `statistics.py`, `visualization.py` |
| Experiment scripts | `scripts/research_factory/axis<N>/` | `exp_<N>_<M>_<name>.py` |
| Setup scripts | `scripts/research_factory/phase0_setup/` | `compute_all_embeddings.py`, etc. |
| Resources | `resources/` | `hypotheses.yaml`, `phonetics/*.json` |
| Feature outputs | `outputs/research_factory/features/` | `<name>.npy` + `<name>.meta.json` |
| Experiment outputs | `outputs/research_factory/axis<N>/` | varies per experiment |
| Reports | `outputs/research_factory/reports/` | `<exp_id>_result.json`, `phase<N>_summary.md` |
| Figures | `outputs/research_factory/figures/` | `<exp_id>_<name>.png` |

---

## Context Files Every Agent Must Read

Before starting ANY task, read these:

1. **`docs/plans/RESEARCH_FACTORY_MASTER_PLAN.md`** — The full theory and experiment specs
2. **`data/muajam/roots.jsonl`** (first 10 lines) — Understand the data schema
3. **`data/muajam/letter_meanings.jsonl`** — All 28 letters
4. **This file** — Your task assignment and dependencies

For implementation details:
5. **`scripts/semantic_validation_phase3.py`** — Shows how embeddings are already used in LV1
6. **LV2 embeddings module** — `Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/lv3/discovery/embeddings.py`

---

## Quality Gates

Every piece of code must pass before merge:

1. **No import errors** — `python -c "from juthoor_arabicgenome_lv1.core.models import Letter"` works
2. **Tests exist** — Every module has at least basic tests in `tests/`
3. **Real data runs** — Scripts run on actual `data/muajam/` files, not just synthetic data
4. **Outputs verified** — Generated files exist at expected paths with expected shapes/schemas
5. **No core modification** — Nothing in `data/muajam/`, `outputs/genome_v2/`, or existing scripts is changed

---

## How to Start

**If you are Sonnet (Claude Code subagent):**
Start with Task 0.1. Read `data/muajam/roots.jsonl` and `letter_meanings.jsonl`, then create the dataclasses in `src/juthoor_arabicgenome_lv1/core/models.py`.

**If you are Codex:**
Start with Tasks 0.3 + 0.7 + 0.8 in parallel. These have zero dependencies.
For 0.3: research classical Arabic phonetics (Al-Khalil's makhaarij) and create the JSON files.
For 0.7: implement the statistical functions with scipy.
For 0.8: implement the visualization functions with matplotlib.

**If you are Opus:**
Wait for Phase 0 to complete. Your first action is the Phase 0 review checkpoint.

---

*Orchestration Plan — Juthoor Research Factory*
*Authored by: Claude Opus 4.6*
*2026-03-13*
