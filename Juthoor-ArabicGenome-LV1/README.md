# Juthoor ArabicGenome (LV1)

![level](https://img.shields.io/badge/level-LV1-6f42c1)
![license](https://img.shields.io/badge/license-MIT-blue)

**LV1 is the Arabic linguistic genome and computational research factory.** It encodes the hypothesis that Arabic's consonantal root system carries a structured layer of meaning *before* morphological derivation -- from the single letter, through the biconsonantal (2-letter) nucleus, to the triconsonantal root.

## The Core Idea

Arabic words derive from 3-consonant roots (e.g. **k-t-b** = writing). But beneath these roots lies a deeper **binary nucleus** -- the first two consonants define a *semantic field*, and the third consonant *modifies* that field in a predictable way. This is the theory of Jabal's *Mu'jam al-Ishtiqaqi al-Mu'assal* (The Systematized Etymological Dictionary).

LV1 tests this theory computationally.

## Two Layers

### LV1-CORE (Stable)

The genome -- a read-only data foundation built in three phases:

| Phase | What | Output | Status |
|-------|------|--------|--------|
| **Phase 1** | Brute grouping of Arabic lexemes by binary root | 30 BAB files, 12,333 roots, 22,908 words | Complete |
| **Phase 2** | Muajam Ishtiqaqi overlay (semantic enrichment) | 1,335 matched roots with axial meanings | Complete |
| **Phase 3** | Semantic validation (BGE-M3 cosine scoring) | Mean score 0.558 | Complete |

**Key data assets:**
- `data/muajam/letter_meanings.jsonl` -- 28 Arabic letters with semantic axioms
- `data/muajam/roots.jsonl` -- 1,938 triconsonantal roots with binary nuclei, axial meanings, and Quranic examples
- `outputs/genome_v2/` -- 12,333 genome entries across 30 BAB (chapter) files

### LV1-RESEARCH FACTORY (Experimental)

A computational research engine that tests **12 formal hypotheses** about Arabic sound-meaning structure through **19 planned experiments** across 7 research axes.

**Architecture:**

```
Research Factory
├── Data Contracts       -- 7 entity types (Letter, BinaryRoot, TriliteralRoot, ...)
├── Feature Store        -- Precomputed embeddings & phonetic vectors (.npy files)
├── Experiment Engine    -- Standardized runner with hypothesis tracking
├── Hypothesis Registry  -- 12 hypotheses from Jabal, Ibn Jinni, Al-Khalil, Al-Aqqad
└── Promotion Gateway    -- experimental -> measured -> stable -> promoted to LV2/LV3
```

**The golden rule:** The factory reads from the core. It never modifies it.

## Hypothesis Registry

| ID | Hypothesis | Source | Status |
|----|-----------|--------|--------|
| H1 | Letters with similar articulation have similar meanings | Al-Khalil | Inconclusive |
| H2 | The binary root defines a stable semantic field | Jabal | **Supported** |
| H3 | Each third letter has a stable "modifier personality" | Jabal | Weak signal |
| H4 | Metathesis preserves core meaning | Ibn Jinni | Weakly supported |
| H5 | Metathesis changes meaning (order matters) | Jabal | **Supported** |
| H6 | Same-makhraj substitution produces closer meanings | Ibn Jinni | Not supported |
| H7 | Missing root combinations reflect semantic conflict | Najah Univ. | Not supported |
| H8 | A letter's meaning shifts by position | Al-Aqqad | **Supported** |
| H9 | Emphatic letters carry stronger semantics | Ibn Jinni / Ohala | Untested |
| H10 | Root meaning = composition of letter meanings | Jabal | Untested |
| H11 | Machines can discover binary structure unsupervised | Independent | Not supported |
| H12 | Root meaning is predictable from components | Generative test | **Supported** |

## Research Factory Results

### Phase 1-2 (Axes 1-5)

| Experiment | Metric | Result | Verdict |
|-----------|--------|--------|---------|
| **1.1** Letter Similarity | Mantel r (phonetic vs semantic) | r=-0.15, p=0.16 | Not significant |
| **1.2** Positional Semantics | Kruskal-Wallis significance | 24/28 letters significant | **Supported** |
| **2.3** Field Coherence | Real vs random baseline | 0.540 vs 0.518, >11 sigma | **Supported** |
| **3.1** Modifier Personality | Consistency > 0.5 | 0/27 letters pass | Needs refinement |
| **4.1** Binary Metathesis | Wilcoxon + Cohen's d | mean 0.526 vs 0.502, d=0.28 | Weakly supported |
| **4.3** Phonetic Substitution | Spearman rho | rho=-0.021 | Not supported |
| **5.1** Sound-Meaning CCA | Canonical correlation + perm test | r=0.962, perm p=0.149 | Inconclusive |

**Key finding:** Binary root families are significantly more semantically coherent than random groupings. This is the strongest quantitative evidence for Jabal's theory to date.

### Sprint 3: Root Prediction (Phase 2-3 Generative)

Predicting triliteral roots from binary nucleus + third-letter composition (1,938 roots).

| Model | Blended Jaccard | Regular Jaccard | Nonzero Coverage |
|-------|----------------|----------------|-----------------|
| Intersection | — | 0.146 | 40.4% |
| Phonetic-Gestural (capped 2+1) | — | — | 38% fallback |
| **Combined (Method A)** | **0.201** (consensus_strict) | 0.146 | **65.2%** |

- Method A (semantic) overall accuracy: **49.5%** (post Arabic Core Rebuild + consensus)
- Blended Jaccard improved from 0.175 to 0.201 after consensus scoring
- Nonzero coverage improved from 56.3% to 65.2%
- 4 letter-meaning corrections (م, ع, غ, ب) improved Jabal bJ by +12%
- Best model by root count: Intersection (58% of roots), Phonetic-Gestural fallback (38%)
- Empty-actual roots reduced from 207 to 113 across 3 targeted fix passes

### Letter Corrections (Arabic Core Rebuild)

Four letter meanings were corrected empirically after observing systematic scoring failures:

| Letter | Original label | Corrected meaning |
|--------|---------------|-------------------|
| م | (generic gathering) | تجمع + تلاصق (gathering + adhesion) |
| ع | (generic depth) | ظهور + عمق (manifestation + depth) |
| غ | (concealment) | باطن + اشتمال (interior + encompassing) |
| ب | (generic emergence) | ظهور + خروج (emergence + outward motion) |

Full 28-letter empirical derivation: `outputs/lv1_scoring/research_documents/THE_ARABIC_LETTER_GENOME.md`

Key structural discoveries:
- **Labial triad** (ب/م/ف): three distinct emergence modes — outward, adhesive, dispersive
- **Depth axis** (ع/غ/هـ): graded concealment from manifest depth to interior to exhaled release
- **Positional modifier reversal**: several letters reverse their dominant meaning when shifted from position 1 to position 3

### Binary & Trilateral Investigations

| Investigation | Finding |
|--------------|---------|
| **I1: Binary composition verification** | 53.5% match rate between predicted binary fields and attested roots |
| **I2: Third letter modifier profiles** | 28 profiles derived; positional shift confirmed in 19/28 letters |
| **I3: Reverse pair analysis** | 12% semantic inversion, 79% unrelated — metathesis rarely inverts cleanly |

### Sprint 4: Abbas Sensory Validation

- Abbas sensory categories do **not** function as a scoring prior
- إيماء+إيماء block is the weakest: 0/36 nonzero pairs
- Verdict: sensory-category weighting not viable at current feature resolution

### Sprint 5: Cross-Linguistic Projection

Khashim's 9 sound laws implemented. Arabic roots projected onto Semitic and non-Semitic cognates (64 pairs total).

| Language family | Exact consonant match | Binary-prefix match | Pairs tested |
|----------------|----------------------|--------------------:|:------------|
| Semitic (Hebrew/Aramaic) | 67.9% | 88.7% | 53 |
| Non-Semitic (English) | 27.3% | 45.5% | 11 |

Notable Arabic→English hits: بيت→booth, طرق→track, جلد→cold

Semantic meaning transfer not yet viable at feature-Jaccard level; phonetic projection is strong for Semitic, plausible for English.

## Project Structure

```
Juthoor-ArabicGenome-LV1/
├── src/juthoor_arabicgenome_lv1/
│   ├── core/                        -- Data models & loaders
│   │   ├── models.py                -- 7 frozen dataclasses
│   │   ├── loaders.py               -- Load letters, roots, families
│   │   └── neili_constraints.py     -- Parked: Quranic exegesis constraints (future)
│   ├── factory/                     -- Research engine
│   │   ├── feature_store.py         -- Save/load numpy features
│   │   ├── experiment_runner.py     -- Run & log experiments
│   │   ├── root_predictor.py        -- Root-level prediction engine
│   │   ├── composition_models.py    -- Intersection, phonetic_gestural, sequence models
│   │   ├── scoring.py               -- Jaccard, weighted_jaccard, blended_jaccard
│   │   ├── synonym_families.py      -- Synonym cluster construction for roots
│   │   ├── sound_laws.py            -- Khashim's 9 sound laws
│   │   └── cross_lingual_projection.py -- Arabic→Hebrew/Aramaic/English projection
│   └── qca/                         -- Quranic Corpus Analysis
│
├── scripts/
│   ├── build_genome_phase1.py       -- Brute binary-root grouping
│   ├── build_genome_phase2.py       -- Muajam overlay
│   ├── semantic_validation_phase3.py
│   └── research_factory/
│       ├── phase0_setup/            -- Embeddings, articulatory vectors
│       ├── common/                  -- Statistics, visualization
│       ├── axis1_letter/            -- Letter-level experiments
│       ├── axis2_binary/            -- Binary root experiments
│       ├── axis3_third_letter/      -- Modifier personality
│       ├── axis4_permutation/       -- Metathesis & substitution
│       ├── axis5_phonetics/         -- Sound-meaning correlation
│       ├── axis6_generative/        -- AI prediction experiments
│       └── axis7_validation/        -- Cross-validation
│
├── data/muajam/                     -- Source data (Muajam Ishtiqaqi)
├── resources/
│   ├── hypotheses.yaml              -- 12 hypotheses (machine-readable)
│   └── phonetics/                   -- Makhaarij & sifaat JSON
├── outputs/
│   ├── genome_v2/                   -- 30 BAB files (stable core)
│   └── research_factory/            -- Experiment results & features
└── tests/                           -- 227 tests
```

## Numbers

| Dimension | Count | Source |
|-----------|-------|--------|
| Letters with meanings | 28 | `letter_meanings.jsonl` |
| Binary roots (documented) | 457 of 784 theoretical | `roots.jsonl` |
| Missing binary combinations | 327 | Computed |
| Triliteral roots with axial meanings | 1,938 | `roots.jsonl` |
| Genome entries (full) | 12,333 | `genome_v2/` |
| Binary metathesis pairs | 166 | Computed |
| Roots with Quranic examples | 1,739 (90%) | `roots.jsonl` |
| Formal hypotheses | 12 | `hypotheses.yaml` |
| Planned experiments | 19 | 7 axes |

## Quickstart

```bash
# Install (from monorepo root)
uv pip install -e . -e Juthoor-DataCore-LV0 -e Juthoor-ArabicGenome-LV1 -e Juthoor-CognateDiscovery-LV2

# Run tests
pytest Juthoor-ArabicGenome-LV1/tests/ -v

# Build genome
python Juthoor-ArabicGenome-LV1/scripts/build_genome_phase1.py
python Juthoor-ArabicGenome-LV1/scripts/build_genome_phase2.py

# Compute research factory features (requires BGE-M3 model)
python Juthoor-ArabicGenome-LV1/scripts/research_factory/phase0_setup/compute_all_embeddings.py
python Juthoor-ArabicGenome-LV1/scripts/research_factory/phase0_setup/build_articulatory_vectors.py
```

## Role in the Stack

```
LV0 (data) --> LV1 (genome + research factory) --> LV3 (theory)
                    |
                    +--> promotes features to LV2 (cognate discovery)
```

LV1 does not feed LV2 directly. It feeds **LV3** for theory validation. Stable, promoted features (modifier profiles, field coherence scores) can be exported to LV2 as retrieval features.

## Documentation

- **[Research Factory Master Plan](./docs/plans/RESEARCH_FACTORY_MASTER_PLAN.md)** -- Full theory, hypothesis registry, and experiment specs
- **[Execution Orchestration](./docs/plans/EXECUTION_ORCHESTRATION.md)** -- Multi-agent work plan
- **[Phase 1 Review](../outputs/research_factory/reports/phase1_summary.md)** -- Opus analysis of Phase 1 results
- **[QCA Documentation](./docs/qca/START_HERE.md)** -- Quranic Corpus Analysis

## License

MIT License. See [LICENSE](../LICENSE).

**Author:** Yassine Temessek
