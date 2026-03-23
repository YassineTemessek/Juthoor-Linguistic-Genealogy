# LV0 Data Expansion + LV2 Genome Integration — Execution Orchestration
## Multi-Agent Work Plan (Claude Code + OpenAI Codex)

**Date:** 2026-03-14
**Baseline:** `deda74b` (LV1 Research Factory complete)
**Goal:** Fill critical LV0 data gaps (Hebrew, Aramaic, Persian), then wire LV1's promoted outputs into LV2's discovery pipeline for genome-informed cognate detection.

---

## Agent Roster (same as Research Factory)

| Agent | Role | Handles |
|-------|------|---------|
| **Opus** | Architect & Reviewer | Design decisions, integration review, benchmarking analysis |
| **Sonnet** | Builder | Data wiring, module creation, tests, mergers |
| **Codex** | Heavy Lifter | Bulk data download, ingestion, embedding computation |

---

## What Already Exists (DO NOT REBUILD)

### LV0 — Ingested Languages
```
COMPLETE:
├── Arabic classical    → 3 sources (~154K rows), but lexemes.jsonl NOT merged
├── Quranic Arabic      → 4,903 rows (merged)
├── Modern English      → 1,442,008 rows
├── Latin               → 883,915 rows (no merged lexemes.jsonl)
├── Ancient Greek       → 56,058 rows (no merged lexemes.jsonl)
├── Middle English      → 49,779 rows
└── Old English         → 7,948 rows
```

### LV1 — Promoted Outputs (ready for LV2)
```
outputs/research_factory/promoted/
├── promoted_features/
│   ├── field_coherence_scores.jsonl    ← 396 binary root family scores
│   ├── positional_profiles.jsonl       ← 28 letter positional data
│   └── metathesis_pairs.jsonl          ← 166 annotated metathesis pairs
├── evidence_cards/                     ← H2, H5, H8 evidence cards
└── promotion_manifest.json
```

### LV2 — Discovery Engine
```
OPERATIONAL:
├── BgeM3Embedder (1024-dim, L2-normalized)
├── ByT5Embedder (1472-dim, byte-level)
├── FAISS flat IP indexing
├── Hybrid scoring: semantic 0.4 + form 0.2 + ortho 0.15 + sound 0.15 + skeleton 0.10
├── Root match bonus (+0.35)
├── Correspondence bonus (+0.12 correspondence + 0.05 weak + 0.04 hamza)
├── Logistic regression reranker (10 features)
├── Benchmark: gold (10 pairs), silver, negatives
└── 150 tests
```

### Kaikki Adapter (LV0)
Currently supports: `grc`, `la`, `ang`, `enm`, `en`
Does NOT support: `he` (Hebrew), `arc` (Aramaic), `fa` (Persian), `sa` (Sanskrit)
Adapter at: `Juthoor-DataCore-LV0/scripts/ingest/ingest_kaikki.py`
Adding a new language = adding entry to `LANG_MAP` + providing source JSONL.

---

## Phase A: LV0 Data Expansion

### Task A.1 — Download Hebrew Kaikki Dump
**Owner: Codex**
**Output:** `Resources/hebrew/kaikki.org-dictionary-Hebrew.jsonl`

1. Download from `https://kaikki.org/dictionary/Hebrew/` (the "All-in-one JSONL" file)
2. Place at `Resources/hebrew/kaikki.org-dictionary-Hebrew.jsonl`
3. Report file size and line count

**Note:** Kaikki.org provides free Wiktionary dumps. Hebrew should be substantial (Wiktionary has good Hebrew coverage).

---

### Task A.2 — Extend Kaikki Adapter for Hebrew
**Owner: Codex**
**Depends on:** A.1
**Output:** Updated `ingest_kaikki.py` with Hebrew support

Add to `LANG_MAP` in `Juthoor-DataCore-LV0/scripts/ingest/ingest_kaikki.py`:
```python
"he": ("heb", "modern", "Hebr"),
```

Add to the input/output path mappings (same pattern as existing languages).

Run: `python ingest_kaikki.py --lang-code he`

**Output:** `Juthoor-DataCore-LV0/data/processed/hebrew/sources/kaikki.jsonl`

**Acceptance:** File exists, schema matches LV0 canonical format (id, lemma, language, stage, script, etc.), row count reported.

---

### Task A.3 — Download & Ingest Aramaic/Syriac
**Owner: Codex**
**Output:** Aramaic data in LV0 processed format

Options (Codex to evaluate):
1. Kaikki.org may not have Aramaic — check first
2. LV2 already has raw Syriac data at `Juthoor-CognateDiscovery-LV2/data/raw/aramaic/`
3. If Kaikki unavailable, write a custom adapter for the existing Syriac corpus data

**Acceptance:** At least one Aramaic/Syriac source ingested with >1,000 rows.

---

### Task A.4 — Download & Ingest Persian (Farsi)
**Owner: Codex**
**Output:** `Resources/persian/kaikki.org-dictionary-Persian.jsonl` → processed

Same pattern as Hebrew: download Kaikki dump, extend adapter with:
```python
"fa": ("fas", "modern", "Arab"),
```

Run ingestion. Persian uses Arabic script, which is valuable for form-level cognate matching.

---

### Task A.5 — Run LV0 Housekeeping Mergers
**Owner: Sonnet**
**Depends on:** None (can start immediately)
**Output:** Merged `lexemes.jsonl` files

1. **Arabic classical merger:**
   ```bash
   python Juthoor-DataCore-LV0/scripts/ingest/merge_arabic_classical_lexemes.py
   ```
   Verify output at `data/processed/arabic/classical/lexemes.jsonl`

2. **Latin lexemes.jsonl:** Create a simple pass-through or copy script that generates `data/processed/latin/classical/lexemes.jsonl` from `sources/kaikki.jsonl` (or run the merge script if one exists)

3. **Ancient Greek lexemes.jsonl:** Same as Latin.

**Acceptance:** All three `lexemes.jsonl` files exist, valid JSONL, row counts match sources.

---

### Task A.6 — LV0 Tests for New Languages
**Owner: Sonnet**
**Depends on:** A.2 (Hebrew ingested)
**Output:** `Juthoor-DataCore-LV0/tests/test_hebrew_ingest.py`

- Test Hebrew JSONL exists and has expected schema
- Test row count is reasonable (>10K)
- Test required fields present: id, lemma, language="heb", script="Hebr"

---

### Task A.7 — Expand Benchmark with Hebrew Pairs
**Owner: Sonnet**
**Depends on:** A.2
**Output:** Updated `Juthoor-CognateDiscovery-LV2/resources/benchmarks/cognate_gold.jsonl`

Add known Arabic-Hebrew cognate pairs to the gold benchmark:
```jsonl
{"source_lang":"ara","source_lemma":"كتب","target_lang":"heb","target_lemma":"כתב","relation":"cognate","confidence":1.0,"shared_concept":"write","source_gloss":"to write","target_gloss":"to write"}
{"source_lang":"ara","source_lemma":"سلام","target_lang":"heb","target_lemma":"שלום","relation":"cognate","confidence":1.0,"shared_concept":"peace","source_gloss":"peace","target_gloss":"peace"}
{"source_lang":"ara","source_lemma":"بيت","target_lang":"heb","target_lemma":"בית","relation":"cognate","confidence":1.0,"shared_concept":"house","source_gloss":"house","target_gloss":"house"}
```

Add at least 20 high-confidence Arabic-Hebrew cognate pairs covering:
- Common Semitic roots (k-t-b, sh-l-m, b-y-t, m-l-k, q-r-b, etc.)
- Body parts (يد/יד, عين/עין, أنف/אף)
- Numbers (ثلاثة/שלוש, سبعة/שבע)
- Basic verbs (أكل/אכל, شرب/שתה, قتل/קטל)

Also add 10 Arabic-Hebrew negative pairs (false friends or unrelated words).

---

## Phase B: LV2 Genome Integration

### Task B.1 — Genome Scoring Module
**Owner: Sonnet**
**Depends on:** None (uses promoted outputs already in Git)
**Output:** `Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/discovery/genome_scoring.py`

A module that loads LV1's promoted outputs and provides scoring functions:

```python
class GenomeScorer:
    """Scores cognate candidates using LV1 genome data."""

    def __init__(self, promoted_dir: Path | None = None):
        """Load promoted features from LV1."""
        # Load field_coherence_scores.jsonl → dict[binary_root, coherence]
        # Load metathesis_pairs.jsonl → set of known metathesis pairs
        # Load positional_profiles.jsonl → letter positional data

    def root_coherence_score(self, root: str) -> float | None:
        """Return the field coherence score for a root's binary nucleus.

        Looks up the first two consonants as the binary root,
        returns the coherence score (0-1) or None if not found.
        """

    def is_metathesis_pair(self, root1: str, root2: str) -> bool:
        """Check if two binary roots are a known metathesis pair."""

    def genome_bonus(self, source_entry: dict, target_entry: dict) -> float:
        """Compute a genome-informed bonus for a candidate pair.

        Components:
        - If source has a high-coherence root family: small bonus (trust the root)
        - If source and target share a metathesized root: cross-lingual metathesis bonus
        - Scaled 0.0 to 0.15 (comparable to other bonus magnitudes)
        """
```

**Test file:** `Juthoor-CognateDiscovery-LV2/tests/test_genome_scoring.py`
- Test loading from real promoted outputs
- Test root_coherence_score returns valid float
- Test metathesis pair detection
- Test genome_bonus returns value in expected range

---

### Task B.2 — Wire Genome Scorer into Discovery Pipeline
**Owner: Sonnet**
**Depends on:** B.1
**Output:** Modified `discovery/scoring.py`

Add genome bonus to the scoring pipeline:

1. In `scoring.py`, add an optional `GenomeScorer` parameter
2. After `_apply_correspondence_bonus()`, add `_apply_genome_bonus()` that:
   - Extracts `root_norm` from source and target entries
   - Calls `genome_scorer.genome_bonus(source, target)`
   - Adds bonus to combined score (same pattern as existing bonuses)
3. The genome scorer should be **optional** — pipeline works without it (backward compatible)

**Test:** Existing 150 tests must still pass. Add tests showing genome bonus is applied when scorer is provided.

---

### Task B.3 — First Hebrew-Arabic Discovery Run
**Owner: Codex**
**Depends on:** A.2 (Hebrew ingested), B.2 (genome wired)
**Output:** `outputs/leads/discovery_heb_ara_genome.jsonl`

Run the full discovery pipeline:
- Source: Arabic classical (`data/processed/arabic/classical/`)
- Target: Hebrew (`data/processed/hebrew/`)
- Backend: local (BgeM3 + ByT5)
- Genome scoring: enabled

Produce:
- Discovery leads JSONL
- Evaluation against the expanded gold benchmark (from A.7)
- Metrics: recall@10, recall@50, MRR, nDCG

---

### Task B.4 — Baseline Comparison (Genome vs Blind)
**Owner: Codex**
**Depends on:** B.3
**Output:** `outputs/reports/genome_vs_blind_comparison.json`

Run the same discovery twice:
1. **Blind run:** genome scorer disabled
2. **Genome run:** genome scorer enabled

Compare metrics:
- Does genome-informed scoring improve recall? MRR? nDCG?
- Which pairs benefit most from the genome bonus?
- Are there cases where the genome hurts?

This is the payoff measurement for the entire LV1 Research Factory.

---

### Task B.5 — Benchmark Review
**Owner: Opus**
**When:** After B.3 and B.4 complete
**Output:** `outputs/reports/lv2_genome_integration_review.md`

Review:
- Hebrew-Arabic discovery quality
- Genome vs blind comparison
- Whether promoted features actually help
- Recommendations for tuning weights

---

## Dependency Graph

```
Phase A (LV0 Expansion)                Phase B (LV2 Integration)
════════════════════                    ════════════════════════

A.1 download Hebrew ──→ A.2 ingest     B.1 genome scorer module
         │                 │                      │
         │                 ├──→ A.6 tests         │
         │                 │                      ▼
A.3 Aramaic download/     ├──→ A.7 benchmark  B.2 wire into pipeline
    ingest                 │       pairs             │
                           │                         │
A.4 Persian download/      ▼                         ▼
    ingest              [Hebrew ready]         [Pipeline ready]
                           │                         │
A.5 LV0 mergers           └───────────┬─────────────┘
    (independent)                      ▼
                              B.3 first discovery run
                                       │
                                       ▼
                              B.4 genome vs blind
                                       │
                                       ▼
                              B.5 Opus review
```

---

## Execution Order

### Immediate — Start NOW in parallel:

**Codex (Heavy Lifter):**
- A.1: Download Hebrew Kaikki dump
- A.3: Check Aramaic availability, download/ingest
- A.4: Download Persian Kaikki dump
- Then A.2: Extend adapter + ingest Hebrew

**Sonnet (Builder):**
- A.5: Run LV0 mergers (Arabic, Latin, Greek)
- B.1: Build genome scoring module
- (These are independent, can run in parallel)

### After Hebrew is ingested:

**Sonnet:**
- A.6: Hebrew ingest tests
- A.7: Expand benchmark with Arabic-Hebrew pairs
- B.2: Wire genome scorer into pipeline

### After pipeline is ready + Hebrew ingested:

**Codex:**
- B.3: First Hebrew-Arabic discovery run
- B.4: Genome vs blind comparison

### After discovery runs complete:

**Opus:**
- B.5: Review and analysis

---

## Assignment Summary

### Sonnet Tasks (Claude Code subagents)

| Task | Description | Depends on |
|------|-------------|-----------|
| A.5 | Run LV0 mergers (Arabic/Latin/Greek) | Nothing (start now) |
| A.6 | Hebrew ingest tests | A.2 |
| A.7 | Expand benchmark with 20+ Arabic-Hebrew pairs | A.2 |
| B.1 | Build GenomeScorer module | Nothing (start now) |
| B.2 | Wire genome scorer into discovery pipeline | B.1 |

### Codex Tasks (autonomous)

| Task | Description | Depends on |
|------|-------------|-----------|
| A.1 | Download Hebrew Kaikki dump | Nothing (start now) |
| A.2 | Extend Kaikki adapter + ingest Hebrew | A.1 |
| A.3 | Aramaic/Syriac download + ingest | Nothing (start now) |
| A.4 | Persian download + ingest | Nothing (start now) |
| B.3 | First Hebrew-Arabic discovery run | A.2, B.2 |
| B.4 | Genome vs blind comparison | B.3 |

### Opus Tasks (review)

| Task | Description | When |
|------|-------------|------|
| B.5 | Review discovery results and genome integration | After B.3+B.4 |

---

## Context Files for All Agents

Before starting, read:
1. **This file** — your task assignments
2. **`Juthoor-DataCore-LV0/scripts/ingest/ingest_kaikki.py`** — the Kaikki adapter to extend
3. **`Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_retrieval.py`** — the discovery pipeline
4. **`outputs/research_factory/promoted/promotion_manifest.json`** — what LV1 promotes
5. **`Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/discovery/scoring.py`** — where genome bonus plugs in

## Quality Gates

1. **No import errors** after changes
2. **All existing tests pass** (LV0: 145, LV1: 227, LV2: 150)
3. **New tests for new code**
4. **Hebrew data validates** against LV0 canonical schema
5. **Genome scoring is optional** — LV2 works identically without it (backward compatible)
6. **Benchmark expanded** before measuring — no self-fulfilling evaluation

---

*LV0 Data Expansion + LV2 Genome Integration — Execution Orchestration*
*Juthoor Linguistic Genealogy*
*2026-03-14*
