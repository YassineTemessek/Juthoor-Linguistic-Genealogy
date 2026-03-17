# Parallel Execution Orchestration — 2026-03-17
## Opus + Sonnet + Codex Work Split

**Date:** 2026-03-17
**Baseline commit:** `15e8c70`
**Context:** Phase A complete (104 gold pairs, 30 negatives). B.4+B.5 done. Codex discovered Persian normalization bug during B.1. C.3+C.4 committed (`3355ad5`).

---

## Known Blockers (Fix First)

### BUG-1: Persian language code mismatch
**Owner: Sonnet (immediate)**
**Files:** `Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/discovery/benchmarking.py`

The gold benchmark uses `lang: "fa"` but the ingested Persian corpus uses `language: "fas"`. The materializer's `_norm()` function (benchmarking.py:10) only does whitespace+casefold — it does NOT map ISO 639-1 to ISO 639-3 codes.

**Fix:** Add a language code normalization map in `_norm()` or in `extract_benchmark_subset()`:
```python
_LANG_ALIASES = {
    "fa": "fas",    # Persian: ISO 639-1 → ISO 639-3
    "he": "heb",    # Hebrew
    "ar": "ara",    # Arabic
    "arc": "arc",   # Aramaic (already 639-3)
}
```
When comparing benchmark lang against corpus lang, normalize both sides through this map. The benchmark can use either code; the corpus uses the 639-3 code from the kaikki adapter.

**Test:** After fix, `materialize_benchmark_slice.py` should find 20 Persian benchmark pairs instead of 0.

---

## Agent Assignments

### Opus 4.6 (Architect + Reviewer)

| ID | Task | When | Deliverable |
|----|------|------|-------------|
| O.1 | Write this orchestration plan | NOW | This file |
| O.2 | B.7 — Multi-pair evaluation review | After Codex finishes B.1-B.3+B.6 | `outputs/reports/lv2_multi_pair_evaluation_review.md` |
| O.3 | Review C.3+C.4 results (H9/H10) | After Codex commits results | Verdict on H9/H10, update hypothesis registry |
| O.4 | Review C.5 Hebrew cross-validation | After Codex finishes | Assess replication strength, update FINAL_SYNTHESIS |
| O.5 | Update STATUS_TRACKER after each milestone | Ongoing | `docs/plans/STATUS_TRACKER.md` |

---

### Sonnet 4.6 (Builder — Claude Code subagents)

All Sonnet tasks are code changes with tests. Run in parallel where dependencies allow.

| ID | Task | Depends on | Files | Tests |
|----|------|-----------|-------|-------|
| S.1 | **Fix BUG-1: Persian lang code normalization** | Nothing (URGENT) | `benchmarking.py`, `test_benchmarking.py` | Verify `fa` ↔ `fas` matching works |
| S.2 | **Fix BUG-1b: Benchmark lang in corpora discovery** | S.1 | `corpora.py` if needed | Verify Persian corpus discovered correctly |
| S.3 | **C.1: Verify Aramaic consonant mapping** | Nothing | `genome_scoring.py`, `test_genome_scoring.py` | Aramaic (Hebrew-script) consonants resolve to classes |
| S.4 | **C.2: Add Persian consonant mapping** | Nothing | `genome_scoring.py`, `test_genome_scoring.py` | Add پ/چ/ژ/گ to `_LETTER_CLASS` |
| S.5 | **Add evaluation harness for multi-pair comparison** | S.1 | New: `scripts/discovery/compare_blind_vs_genome.py` | Script that runs blind+genome for a given lang pair, outputs metrics JSON |
| S.6 | **Add language family metadata to GenomeScorer** | S.3, S.4 | `genome_scoring.py` | `is_semitic_pair()` helper so genome bonuses apply appropriately per family |
| S.7 | **Benchmark quality audit script** | Nothing | New: `scripts/benchmarks/audit_benchmark.py` | Verify all gold lemmas exist in their target corpus, report coverage % |
| S.8 | **Add Recall@10 and Recall@100 to evaluation metrics** | Nothing | `evaluation.py`, `test_evaluation.py` | Currently only Recall@50; add @10 and @100 for finer granularity |

**Execution order:**
1. S.1 + S.2 (URGENT — unblocks Codex B.1)
2. S.3 + S.4 + S.7 + S.8 (parallel, independent)
3. S.5 (after S.1)
4. S.6 (after S.3 + S.4)

---

### Codex (Heavy Lifter — fast mode, lots of tokens)

Codex handles all compute-heavy discovery runs, reranker training, and the LV1 experiments. Give him maximum parallelism.

#### Wave 1 — Discovery Runs (after Sonnet fixes BUG-1)

| ID | Task | Depends on | Input | Output |
|----|------|-----------|-------|--------|
| X.1 | **B.1: Arabic-Persian blind discovery** | S.1 (Persian fix) | ara classical → fa modern | `outputs/leads/discovery_ara_fa_blind.jsonl` |
| X.2 | **B.1: Arabic-Persian genome discovery** | S.1 | ara classical → fa modern (genome ON) | `outputs/leads/discovery_ara_fa_genome.jsonl` |
| X.3 | **B.2: Arabic-Aramaic blind discovery** | Nothing | ara classical → arc classical | `outputs/leads/discovery_ara_arc_blind.jsonl` |
| X.4 | **B.2: Arabic-Aramaic genome discovery** | Nothing | ara classical → arc classical (genome ON) | `outputs/leads/discovery_ara_arc_genome.jsonl` |
| X.5 | **B.3: Arabic-Hebrew blind discovery (expanded)** | Nothing | ara classical → heb modern, 50+ pairs | `outputs/leads/discovery_ara_heb_blind_v2.jsonl` |
| X.6 | **B.3: Arabic-Hebrew genome discovery (expanded)** | Nothing | ara classical → heb modern (genome ON) | `outputs/leads/discovery_ara_heb_genome_v2.jsonl` |

**Commands:**
```bash
# X.3 + X.4 (Aramaic — can start NOW)
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_retrieval.py \
  --source ara@classical --target arc@classical --no-genome --yes
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_retrieval.py \
  --source ara@classical --target arc@classical --yes

# X.5 + X.6 (Hebrew — can start NOW)
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_retrieval.py \
  --source ara@classical --target heb@modern --no-genome --yes
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_retrieval.py \
  --source ara@classical --target heb@modern --yes

# X.1 + X.2 (Persian — AFTER Sonnet pushes S.1 fix)
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_retrieval.py \
  --source ara@classical --target fa@modern --no-genome --yes
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_retrieval.py \
  --source ara@classical --target fa@modern --yes
```

**After each pair completes**, evaluate against the expanded benchmark:
- Compute: Recall@10, Recall@50, Recall@100, MRR, nDCG
- Save comparison JSON to `outputs/reports/ara_{lang}_blind_vs_genome.json`

#### Wave 2 — Reranker Training (after Wave 1)

| ID | Task | Depends on | Input | Output |
|----|------|-----------|-------|--------|
| X.7 | **B.6a: Train reranker on Arabic-Hebrew genome leads** | X.6 | genome leads + benchmark | `outputs/benchmark_experiments/ara_heb_genome_reranker_v2.json` |
| X.8 | **B.6b: Train reranker on Arabic-Aramaic genome leads** | X.4 | genome leads + benchmark | `outputs/benchmark_experiments/ara_arc_genome_reranker.json` |
| X.9 | **B.6c: Train reranker on Arabic-Persian genome leads** | X.2 | genome leads + benchmark | `outputs/benchmark_experiments/ara_fa_genome_reranker.json` |
| X.10 | **B.6d: Train combined multi-pair reranker** | X.6, X.4, X.2 | All genome leads combined + full benchmark | `outputs/benchmark_experiments/multi_pair_genome_reranker.json` |

**For each reranker, report:**
1. Learned weights for all 11 features (especially genome_bonus weight)
2. MRR/nDCG before and after reranking
3. Whether genome_bonus has positive learned weight (= signal) or near-zero (= noise)

```bash
# X.7
python Juthoor-CognateDiscovery-LV2/scripts/discovery/train_reranker.py \
  --benchmark resources/benchmarks/cognate_gold.jsonl \
  --leads outputs/leads/discovery_ara_heb_genome_v2.jsonl \
  --output outputs/benchmark_experiments/ara_heb_genome_reranker_v2.json

# X.8
python Juthoor-CognateDiscovery-LV2/scripts/discovery/train_reranker.py \
  --benchmark resources/benchmarks/cognate_gold.jsonl \
  --leads outputs/leads/discovery_ara_arc_genome.jsonl \
  --output outputs/benchmark_experiments/ara_arc_genome_reranker.json

# X.9
python Juthoor-CognateDiscovery-LV2/scripts/discovery/train_reranker.py \
  --benchmark resources/benchmarks/cognate_gold.jsonl \
  --leads outputs/leads/discovery_ara_fa_genome.jsonl \
  --output outputs/benchmark_experiments/ara_fa_genome_reranker.json
```

#### Wave 3 — Apply Rerankers and Final Evaluation (after Wave 2)

| ID | Task | Depends on | Output |
|----|------|-----------|--------|
| X.11 | **Apply reranker to Hebrew leads, re-evaluate** | X.7 | MRR/nDCG with reranking vs without |
| X.12 | **Apply reranker to Aramaic leads, re-evaluate** | X.8 | Same |
| X.13 | **Apply reranker to Persian leads, re-evaluate** | X.9 | Same |
| X.14 | **Apply multi-pair reranker to all three, compare** | X.10 | Does a combined reranker generalize? |

```bash
# For each language pair:
python Juthoor-CognateDiscovery-LV2/scripts/discovery/apply_reranker.py \
  --model outputs/benchmark_experiments/ara_heb_genome_reranker_v2.json \
  --leads outputs/leads/discovery_ara_heb_genome_v2.jsonl \
  --output outputs/leads/discovery_ara_heb_reranked_v2.jsonl
```

**Produce a final metrics table** saved to `outputs/reports/multi_pair_evaluation_matrix.json`:

```json
{
  "ara_heb": {
    "blind":    {"recall@10": 0, "recall@50": 0, "mrr": 0, "ndcg": 0},
    "genome":   {"recall@10": 0, "recall@50": 0, "mrr": 0, "ndcg": 0},
    "reranked": {"recall@10": 0, "recall@50": 0, "mrr": 0, "ndcg": 0},
    "genome_bonus_weight": 0
  },
  "ara_arc": {},
  "ara_fa":  {}
}
```

#### Wave 4 — LV1 Experiments (parallel with Waves 1-3)

These are independent of LV2 work. Start immediately.

| ID | Task | Depends on | Output |
|----|------|-----------|--------|
| X.15 | **C.3: H9 emphatic experiment** | Nothing (check if done at `3355ad5`) | `outputs/research_factory/experiments/h9_emphatic/` |
| X.16 | **C.4: H10 compositionality experiment** | Nothing (check if done at `3355ad5`) | `outputs/research_factory/experiments/h10_compositionality/` |
| X.17 | **C.5: Hebrew cross-validation of H2 (field coherence)** | X.15, X.16 | Do Hebrew trilateral roots show field coherence? |
| X.18 | **C.5: Hebrew cross-validation of H5 (order matters)** | X.17 | Do Hebrew metathesis pairs show order-dependent meaning? |
| X.19 | **C.5: Hebrew cross-validation of H8 (positional semantics)** | X.17 | Do Hebrew letters shift meaning by position? |

**C.5 is the most ambitious task.** It requires:
1. Extract Hebrew trilateral roots from LV0 Hebrew data (17K lexemes)
2. Group by consonant skeleton → Hebrew "root families"
3. Compute embeddings for Hebrew root families
4. Run the same statistical tests (Kruskal-Wallis for H8, permutation for H5, cosine coherence for H2)
5. Compare effect sizes: Arabic vs Hebrew

**If H2/H5/H8 replicate in Hebrew, the theory gains massive weight.**

#### Wave 5 — LV0 Data Expansion (parallel, lower priority)

| ID | Task | Depends on | Output |
|----|------|-----------|--------|
| X.20 | **Ingest Akkadian from Kaikki** | Nothing | Check kaikki.org for Akkadian, add `akk` to LANG_MAP, ingest |
| X.21 | **Ingest Amharic from Kaikki** | Nothing | Check kaikki.org for Amharic, add `am` to LANG_MAP, ingest |
| X.22 | **Ingest Syriac (TEI format)** | Nothing | The deferred TEI adapter from the previous plan. Raw data at `Juthoor-CognateDiscovery-LV2/data/raw/aramaic/` |
| X.23 | **Add Arabic-Akkadian gold pairs** | X.20 | 10+ pairs for the oldest attested Semitic language |
| X.24 | **Add Arabic-Amharic gold pairs** | X.21 | 10+ pairs for the Ethiopian Semitic branch |

These are stretch goals. Only do them if Waves 1-4 finish cleanly.

---

## Execution Timeline

```
TIME →→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→

SONNET ─────────────────────────────────────────────────────
  S.1+S.2 Persian fix ─┐
  S.3+S.4 consonant maps├→ S.5 compare script → S.6 family metadata
  S.7 audit script      │
  S.8 eval metrics      │
                        │
CODEX ──────────────────┼──────────────────────────────────
  X.3+X.4 Aramaic runs ─┤
  X.5+X.6 Hebrew runs ──┤─→ X.7 train reranker ─→ X.11 apply+eval ──┐
  X.15+X.16 H9/H10     │   X.8 train reranker ─→ X.12 apply+eval    │
                        │   X.10 multi reranker ─→ X.14 compare      │
  (wait for S.1) ──────┘                                              │
  X.1+X.2 Persian runs ──→ X.9 train reranker ─→ X.13 apply+eval    │
  X.17-X.19 Hebrew H2/H5/H8 cross-validation                         │
  X.20-X.24 Akkadian/Amharic (stretch)                                │
                                                                      │
OPUS ──────────────────────────────────────────────────────────────────┘
  O.3 Review H9/H10 results
  O.2 B.7 Multi-pair evaluation review (BIG)
  O.4 Review Hebrew cross-validation
  O.5 Update STATUS_TRACKER throughout
```

---

## Dependency Graph

```
              S.1 Persian fix ──────────────→ X.1+X.2 Persian discovery
              │                                       │
              S.2 Corpora fix                         ▼
                                              X.9 Persian reranker
                                                      │
X.3+X.4 Aramaic discovery ──→ X.8 Aramaic reranker   ▼
                                      │         X.13 Persian eval
X.5+X.6 Hebrew discovery ───→ X.7 Hebrew reranker    │
                                      │               │
                                      ▼               │
                               X.10 Multi reranker    │
                                      │               │
                                      ▼               ▼
                               X.11-X.14 Final evals ──→ O.2 Opus review
                                                              │
X.15+X.16 H9/H10 ─────────→ O.3 Opus H9/H10 review          │
                                      │                       │
                                      ▼                       │
                               X.17-X.19 Hebrew validation ──→ O.4 Opus review
                                                              │
S.3+S.4 Consonant maps ──→ S.6 Family metadata               │
                                                              │
X.20-X.24 LV0 expansion (stretch) ───────────────────────────┘
```

---

## Deliverables Checklist

### Codex Must Produce:
- [ ] 6 discovery lead files (blind + genome for 3 language pairs)
- [ ] 4 reranker model JSONs (per-pair + combined)
- [ ] 3 blind-vs-genome comparison JSONs (one per language pair)
- [ ] 1 multi-pair evaluation matrix JSON
- [ ] H9 experiment results + verdict
- [ ] H10 experiment results + verdict
- [ ] Hebrew cross-validation results for H2/H5/H8

### Sonnet Must Produce:
- [ ] Persian normalization fix (BUG-1)
- [ ] Aramaic + Persian consonant mappings (C.1, C.2)
- [ ] Evaluation harness improvements (Recall@10/@100)
- [ ] Benchmark audit script
- [ ] All changes must have tests

### Opus Must Produce:
- [ ] B.7: Multi-pair evaluation review (the big analysis document)
- [ ] H9/H10 verdict (update hypothesis registry)
- [ ] Hebrew cross-validation assessment
- [ ] Updated STATUS_TRACKER at each milestone

---

## Quality Gates

1. **Persian fix verified** before Codex runs X.1/X.2
2. **All existing 231 LV2 tests pass** after every Sonnet change
3. **Every discovery run** produces leads JSONL + metrics JSON
4. **Reranker weights inspected** — genome_bonus weight reported for each model
5. **No evaluation on unstable benchmark** — all runs use the frozen 104-pair benchmark
6. **Hebrew cross-validation uses same methods** as Arabic experiments for comparability
7. **Commits are atomic** — one task per commit, clear messages

---

## Communication Protocol

1. **Sonnet pushes S.1 fix** → signals Codex "Persian unblocked, pull and run X.1/X.2"
2. **Codex finishes each Wave** → pushes leads/reports, signals Opus for review
3. **Opus reviews** → writes analysis, updates tracker, signals next wave
4. **If any discovery run produces 0 covered pairs** → STOP, report, debug before continuing

---

*Parallel Execution Orchestration*
*Juthoor Linguistic Genealogy*
*2026-03-17*
