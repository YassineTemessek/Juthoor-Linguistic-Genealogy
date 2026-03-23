# LV2 Evaluation Expansion — Execution Orchestration

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Broaden LV2 evaluation across more language pairs and strengthen the benchmark to produce statistically reliable evidence that genome-informed cognate discovery works.

**Architecture:** Three phases — (A) expand benchmark to 100+ pairs across Arabic-Hebrew/Persian/Aramaic, (B) run multi-pair discovery and promote genome_bonus into the reranker, (C) extend GenomeScorer consonant mappings and revisit LV1 untested hypotheses.

**Tech Stack:** Python 3.11+, pytest, FAISS, BgeM3, ByT5, logistic regression reranker

**Baseline commit:** `91c3006` (CI green, all prior work complete)

---

## Agent Roster

| Agent | Role | Handles |
|-------|------|---------|
| **Opus** | Architect & Reviewer | Plan design, benchmark review, integration analysis |
| **Sonnet** | Builder | Module creation, tests, benchmark authoring, reranker wiring |
| **Codex** | Heavy Lifter | Discovery runs, embedding computation, bulk data work |

---

## What Already Exists (DO NOT REBUILD)

### LV0 — Ingested Languages
```
COMPLETE (9 languages, ~2.64M lexemes):
├── Arabic classical    → 32,687 merged lexemes
├── Quranic Arabic      → 4,903 rows
├── Modern English      → 1,442,008 rows
├── Latin               → 883,915 rows
├── Ancient Greek       → 56,058 rows
├── Middle English      → 49,779 rows
├── Old English         → 7,948 rows
├── Hebrew              → 17,034 rows    ← NEW (commit c133aa6)
├── Persian             → 19,361 rows    ← NEW (commit c133aa6)
└── Aramaic             → 2,176 rows     ← NEW (commit c133aa6)
```

### LV1 — Promoted Outputs (in Git)
```
outputs/research_factory/promoted/
├── promoted_features/
│   ├── field_coherence_scores.jsonl    ← 396 binary root family scores
│   ├── positional_profiles.jsonl       ← 28 letter positional data
│   └── metathesis_pairs.jsonl          ← 166 annotated metathesis pairs
├── evidence_cards/                     ← H2, H5, H8 evidence cards
└── promotion_manifest.json
```

### LV2 — Discovery Engine (operational)
```
├── BgeM3Embedder (1024-dim) + ByT5Embedder (1472-dim)
├── FAISS flat IP indexing
├── Hybrid scoring: semantic 0.4 + form 0.2 + ortho 0.15 + sound 0.15 + skeleton 0.10
├── GenomeScorer: Arabic↔Hebrew consonant mapping, 4 bonus types (max +0.13)
├── Logistic regression reranker (10 features, genome_bonus NOT included)
├── Benchmark: 40 gold pairs, 9 silver, 15 negatives
└── 215 tests passing
```

### Current Benchmark Breakdown
```
cognate_gold.jsonl     → 40 pairs (25 ara-heb, 10 lat-grc, 6 ara-eng)
cognate_silver.jsonl   → 9 pairs
non_cognate_negatives.jsonl → 15 negatives
```

### Current GenomeScorer Consonant Mapping (genome_scoring.py:24-57)
Covers Arabic ↔ Hebrew only. Maps to shared phoneme classes:
```
ب↔ב→"b", ت↔ט/ת→"t", ج↔ג→"g", ح↔ח→"ḥ", خ↔כ→"ḫ", د↔ד→"d",
ر↔ר→"r", ص↔צ→"ṣ", ع↔ע→"ʕ", ف↔פ→"f", ق↔ק→"q", ل↔ל→"l",
م↔מ→"m", ن↔נ→"n", ه↔ה→"h", و↔ו→"w", ي↔י→"y"
```

### Current Reranker Features (rerank.py:13-24)
```
10 features: semantic, form, orthography, sound, skeleton,
             family_boost, root_match, correspondence,
             weak_radical_match, hamza_match
```
genome_bonus is NOT a feature yet.

---

## Phase A: Benchmark Expansion to 100+ Pairs

**Goal:** Expand the gold benchmark from 40 pairs to 100+ pairs across three language pairs, with strengthened negatives and false friends. This is the foundation for all subsequent evaluation.

### Key Files
```
Modify: Juthoor-CognateDiscovery-LV2/resources/benchmarks/cognate_gold.jsonl
Modify: Juthoor-CognateDiscovery-LV2/resources/benchmarks/non_cognate_negatives.jsonl
Create: Juthoor-CognateDiscovery-LV2/tests/test_benchmark_expansion.py
```

### Benchmark Schema (existing, preserve exactly)
```json
{
  "source": {"lang": "ara", "lemma": "كتب", "gloss": "to write"},
  "target": {"lang": "heb", "lemma": "כתב", "gloss": "to write"},
  "relation": "cognate",
  "confidence": 1.0,
  "notes": "shared Semitic root k-t-b"
}
```

---

### Task A.1 — Expand Arabic-Hebrew Gold Pairs
**Owner: Sonnet**
**Depends on:** Nothing
**Output:** `cognate_gold.jsonl` expanded from 25 to 50+ Arabic-Hebrew pairs

- [ ] **Step 1: Audit existing Arabic-Hebrew pairs**

Read `Juthoor-CognateDiscovery-LV2/resources/benchmarks/cognate_gold.jsonl` and list all existing Arabic-Hebrew pairs to avoid duplicates.

- [ ] **Step 2: Write test for expanded benchmark**

Create `Juthoor-CognateDiscovery-LV2/tests/test_benchmark_expansion.py`:
```python
"""Tests for benchmark expansion — validates pair counts, schema, and diversity."""

import json
from pathlib import Path
import pytest

_BENCH = Path(__file__).resolve().parents[1] / "resources" / "benchmarks"
GOLD = _BENCH / "cognate_gold.jsonl"
NEGS = _BENCH / "non_cognate_negatives.jsonl"

REQUIRED_FIELDS = {"source", "target", "relation", "confidence"}
SOURCE_TARGET_FIELDS = {"lang", "lemma"}


def _load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text("utf-8").splitlines() if l.strip()]


@pytest.fixture(scope="module")
def gold():
    return _load(GOLD)


@pytest.fixture(scope="module")
def negatives():
    return _load(NEGS)


class TestGoldBenchmarkExpansion:
    def test_total_at_least_100(self, gold):
        assert len(gold) >= 100, f"Gold has {len(gold)} pairs, need >= 100"

    def test_arabic_hebrew_at_least_50(self, gold):
        ah = [p for p in gold if p["source"]["lang"] == "ara" and p["target"]["lang"] == "heb"]
        assert len(ah) >= 50, f"Arabic-Hebrew has {len(ah)} pairs, need >= 50"

    def test_arabic_persian_at_least_20(self, gold):
        ap = [p for p in gold if p["source"]["lang"] == "ara" and p["target"]["lang"] == "fa"]
        assert len(ap) >= 20, f"Arabic-Persian has {len(ap)} pairs, need >= 20"

    def test_arabic_aramaic_at_least_15(self, gold):
        aa = [p for p in gold if p["source"]["lang"] == "ara" and p["target"]["lang"] == "arc"]
        assert len(aa) >= 15, f"Arabic-Aramaic has {len(aa)} pairs, need >= 15"

    def test_schema_valid(self, gold):
        for i, p in enumerate(gold):
            missing = REQUIRED_FIELDS - p.keys()
            assert not missing, f"Pair {i} missing: {missing}"
            for side in ("source", "target"):
                side_missing = SOURCE_TARGET_FIELDS - p[side].keys()
                assert not side_missing, f"Pair {i} {side} missing: {side_missing}"

    def test_no_duplicate_pairs(self, gold):
        seen = set()
        for p in gold:
            key = (p["source"]["lang"], p["source"]["lemma"], p["target"]["lang"], p["target"]["lemma"])
            assert key not in seen, f"Duplicate pair: {key}"
            seen.add(key)


class TestNegativeBenchmarkExpansion:
    def test_at_least_30_negatives(self, negatives):
        assert len(negatives) >= 30, f"Negatives has {len(negatives)}, need >= 30"

    def test_has_false_friends(self, negatives):
        ff = [n for n in negatives if n.get("relation") == "false_friend"]
        assert len(ff) >= 5, f"Only {len(ff)} false friends, need >= 5"

    def test_schema_valid(self, negatives):
        for i, n in enumerate(negatives):
            missing = REQUIRED_FIELDS - n.keys()
            assert not missing, f"Negative {i} missing: {missing}"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest Juthoor-CognateDiscovery-LV2/tests/test_benchmark_expansion.py -v`
Expected: FAIL (currently only 40 gold, 15 negatives)

- [ ] **Step 4: Add 25+ new Arabic-Hebrew pairs to cognate_gold.jsonl**

Add high-confidence Semitic cognate pairs covering these categories:

**Body parts** (5+):
- يد/יד (hand), عين/עין (eye), أنف/אף (nose), رأس/ראש (head), لسان/לשון (tongue), أذن/אוזן (ear), قلب/לב (heart)

**Numbers** (4+):
- ثلاثة/שלוש (three), سبعة/שבע (seven), عشرة/עשר (ten), مئة/מאה (hundred)

**Basic verbs** (5+):
- أكل/אכל (eat), شرب/שתה (drink), قتل/קטל (kill), جلس/ישב (sit), سمع/שמע (hear), فتح/פתח (open)

**Nature/world** (4+):
- أرض/ארץ (earth), ماء/מים (water), نار/אש (fire), شمس/שמש (sun), ليل/לילה (night)

**Family/social** (3+):
- أخ/אח (brother), ابن/בן (son), ملك/מלך (king), عبد/עבד (servant)

Each pair must use the existing schema exactly. Set confidence: 1.0 for well-established cognates, 0.8 for those with phonological shifts.

- [ ] **Step 5: Run test to check Arabic-Hebrew count**

Run: `pytest Juthoor-CognateDiscovery-LV2/tests/test_benchmark_expansion.py::TestGoldBenchmarkExpansion::test_arabic_hebrew_at_least_50 -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add Juthoor-CognateDiscovery-LV2/resources/benchmarks/cognate_gold.jsonl \
       Juthoor-CognateDiscovery-LV2/tests/test_benchmark_expansion.py
git commit -m "feat(lv2): expand Arabic-Hebrew gold benchmark to 50+ pairs"
```

---

### Task A.2 — Add Arabic-Persian Gold Pairs
**Owner: Sonnet**
**Depends on:** A.1

- [ ] **Step 1: Add 20+ Arabic-Persian cognate pairs to cognate_gold.jsonl**

Persian has extensive Arabic loanwords AND genuine Semitic-Iranian cognates. Include:

**Shared Semitic loanwords in Persian** (clear Arabic origin):
- کتاب/كتاب (book), مدرسه/مدرسة (school), علم/علم (science), دین/دين (religion), حق/حق (right/truth)

**Older shared vocabulary** (may predate Islam):
- نام/اسم (name — Iranian vs Semitic), آب/أب (father), مادر/أم (mother — different roots, negative)

**Note:** Use source lang="ara", target lang="fa". For Persian lemmas use Arabic-script forms as stored in the kaikki ingest.

- [ ] **Step 2: Run test to check Arabic-Persian count**

Run: `pytest Juthoor-CognateDiscovery-LV2/tests/test_benchmark_expansion.py::TestGoldBenchmarkExpansion::test_arabic_persian_at_least_20 -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add Juthoor-CognateDiscovery-LV2/resources/benchmarks/cognate_gold.jsonl
git commit -m "feat(lv2): add 20+ Arabic-Persian gold pairs to benchmark"
```

---

### Task A.3 — Add Arabic-Aramaic Gold Pairs
**Owner: Sonnet**
**Depends on:** A.1

- [ ] **Step 1: Add 15+ Arabic-Aramaic cognate pairs to cognate_gold.jsonl**

Aramaic and Arabic are closely related Semitic languages with many cognates:

**Core Semitic vocabulary:**
- كتب/כתב (write), ملك/מלך (king), ابن/בר (son), بيت/בית (house), شلام/שלם (peace)
- أرض/ארע (earth), يوم/יום (day), ليل/ליל (night), ماء/מיא (water)

Use source lang="ara", target lang="arc". The Aramaic kaikki ingest uses Hebrew script ("Hebr").

- [ ] **Step 2: Run test to check Arabic-Aramaic count**

Run: `pytest Juthoor-CognateDiscovery-LV2/tests/test_benchmark_expansion.py::TestGoldBenchmarkExpansion::test_arabic_aramaic_at_least_15 -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add Juthoor-CognateDiscovery-LV2/resources/benchmarks/cognate_gold.jsonl
git commit -m "feat(lv2): add 15+ Arabic-Aramaic gold pairs to benchmark"
```

---

### Task A.4 — Strengthen Negatives and False Friends
**Owner: Sonnet**
**Depends on:** A.1

- [ ] **Step 1: Expand non_cognate_negatives.jsonl to 30+ entries**

Add negatives across all three language pairs:

**False friends** (look/sound similar but unrelated):
- Arabic غرب (west) vs Hebrew ערב (evening) — different semantic fields
- Arabic حمار (donkey) vs Persian خمار (hangover)
- Arabic كلب (dog) vs Hebrew כלב (dog) — actually cognate, so DON'T include

**Borrowings** (not cognates — one language borrowed from another via contact):
- Tag relation="borrowing" for Arabic loanwords in Persian that entered post-Islam

**Unrelated translations** (same meaning, different roots):
- Arabic جمل (camel) vs Hebrew גמל (camel) — actually cognate, DON'T include
- Arabic سيارة (car) vs Hebrew מכונית (car) — modern, unrelated

- [ ] **Step 2: Run full test suite**

Run: `pytest Juthoor-CognateDiscovery-LV2/tests/test_benchmark_expansion.py -v`
Expected: ALL PASS (100+ gold, 30+ negatives, schema valid, no duplicates)

- [ ] **Step 3: Run existing LV2 tests to check nothing broke**

Run: `pytest Juthoor-CognateDiscovery-LV2/tests/ -v --tb=short -m "not slow"`
Expected: All 215+ tests pass

- [ ] **Step 4: Commit**

```bash
git add Juthoor-CognateDiscovery-LV2/resources/benchmarks/non_cognate_negatives.jsonl
git commit -m "feat(lv2): expand negatives to 30+ with false friends across 3 lang pairs"
```

---

## Phase B: Multi-Pair Discovery + Reranker Enhancement

**Goal:** Run genome-informed discovery on Arabic-Persian and Arabic-Aramaic, compare blind vs genome across all pairs, and promote genome_bonus into the reranker's feature set.

### Key Files
```
Modify: Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/discovery/rerank.py
Modify: Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/discovery/genome_scoring.py
Create: Juthoor-CognateDiscovery-LV2/tests/test_reranker_genome_feature.py
Discovery runs produce: outputs/leads/ and outputs/reports/
```

---

### Task B.1 — Arabic-Persian Discovery Run (Blind + Genome)
**Owner: Codex**
**Depends on:** A.2 (Persian pairs in benchmark)

- [ ] **Step 1: Run blind Arabic-Persian discovery**

```bash
cd Juthoor-CognateDiscovery-LV2
python scripts/discovery/run_discovery_retrieval.py \
  --source ara@classical \
  --target fa@modern \
  --backend local \
  --models semantic form \
  --topk 200 \
  --no-genome \
  --yes
```

Save leads to `outputs/leads/discovery_ara_fa_blind.jsonl`

- [ ] **Step 2: Run genome-informed Arabic-Persian discovery**

Same as above without `--no-genome`. Save to `outputs/leads/discovery_ara_fa_genome.jsonl`

**Note:** GenomeScorer currently maps Arabic↔Hebrew only. For Arabic-Persian, the genome bonus will be limited since Persian uses Arabic script but the consonant mapping may partially work (shared letters like ب، ت، ک). Record the genome impact honestly even if small.

- [ ] **Step 3: Evaluate both runs against the benchmark**

Compute: Recall@10, Recall@50, MRR, nDCG for both. Save comparison to `outputs/reports/ara_fa_blind_vs_genome.json`

- [ ] **Step 4: Commit**

```bash
git add outputs/reports/ara_fa_blind_vs_genome.json
git commit -m "feat(lv2): Arabic-Persian discovery run — blind vs genome comparison"
```

---

### Task B.2 — Arabic-Aramaic Discovery Run (Blind + Genome)
**Owner: Codex**
**Depends on:** A.3 (Aramaic pairs in benchmark)

- [ ] **Step 1: Run blind Arabic-Aramaic discovery**

```bash
python scripts/discovery/run_discovery_retrieval.py \
  --source ara@classical \
  --target arc@classical \
  --backend local \
  --models semantic form \
  --topk 200 \
  --no-genome \
  --yes
```

Save leads to `outputs/leads/discovery_ara_arc_blind.jsonl`

- [ ] **Step 2: Run genome-informed Arabic-Aramaic discovery**

Same without `--no-genome`. Save to `outputs/leads/discovery_ara_arc_genome.jsonl`

**Note:** Aramaic uses Hebrew script, so the existing Arabic↔Hebrew consonant mapping should work for Arabic↔Aramaic too. This is a key test — if genome helps for Aramaic as well as Hebrew, it validates the cross-Semitic consonant class approach.

- [ ] **Step 3: Evaluate both runs against the benchmark**

Compute metrics, save to `outputs/reports/ara_arc_blind_vs_genome.json`

- [ ] **Step 4: Commit**

```bash
git add outputs/reports/ara_arc_blind_vs_genome.json
git commit -m "feat(lv2): Arabic-Aramaic discovery run — blind vs genome comparison"
```

---

### Task B.3 — Re-run Arabic-Hebrew with Expanded Benchmark
**Owner: Codex**
**Depends on:** A.1 (expanded benchmark)

- [ ] **Step 1: Re-run blind Arabic-Hebrew discovery**

Same pipeline as the original B.3/B.4 from the previous plan, but now evaluated against the expanded 50+ pair benchmark instead of the old 19-pair one.

Save to `outputs/leads/discovery_ara_heb_blind_v2.jsonl`

- [ ] **Step 2: Re-run genome-informed Arabic-Hebrew discovery**

Save to `outputs/leads/discovery_ara_heb_genome_v2.jsonl`

- [ ] **Step 3: Evaluate and compare**

The key question: does the +0.04 MRR improvement hold with 50+ pairs, or was it noise?

Save to `outputs/reports/ara_heb_blind_vs_genome_v2.json`

- [ ] **Step 4: Commit**

```bash
git add outputs/reports/ara_heb_blind_vs_genome_v2.json
git commit -m "feat(lv2): re-evaluate Arabic-Hebrew genome impact with 50+ pair benchmark"
```

---

### Task B.4 — Add genome_bonus to Reranker Feature Set
**Owner: Sonnet**
**Depends on:** Nothing (can start in parallel with B.1-B.3)

- [ ] **Step 1: Write failing test**

Create `Juthoor-CognateDiscovery-LV2/tests/test_reranker_genome_feature.py`:

```python
"""Tests for genome_bonus as reranker feature."""

import json
import numpy as np
from pathlib import Path
import pytest

from juthoor_cognatediscovery_lv2.discovery.rerank import FEATURE_NAMES, _feature_vector


def test_genome_bonus_in_feature_names():
    assert "genome_bonus" in FEATURE_NAMES, "genome_bonus must be a reranker feature"


def test_genome_bonus_is_last_feature():
    """genome_bonus should be the 11th feature (index 10)."""
    assert FEATURE_NAMES.index("genome_bonus") == 10


def test_feature_vector_extracts_genome_bonus():
    entry = {
        "scores": {"semantic": 0.8, "form": 0.5},
        "hybrid": {
            "components": {
                "orthography": 0.3, "sound": 0.2, "skeleton": 0.1,
                "root_match": 0.0, "correspondence": 0.0,
                "weak_radical_match": 0.0, "hamza_match": 0.0,
                "genome_bonus": 0.08,
            },
            "family_boost_applied": False,
        },
    }
    vec = _feature_vector(entry)
    assert len(vec) == 11
    assert vec[10] == pytest.approx(0.08)


def test_feature_vector_defaults_genome_bonus_to_zero():
    entry = {
        "scores": {"semantic": 0.5, "form": 0.3},
        "hybrid": {"components": {}, "family_boost_applied": False},
    }
    vec = _feature_vector(entry)
    assert len(vec) == 11
    assert vec[10] == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest Juthoor-CognateDiscovery-LV2/tests/test_reranker_genome_feature.py -v`
Expected: FAIL (genome_bonus not in FEATURE_NAMES yet)

- [ ] **Step 3: Add genome_bonus to FEATURE_NAMES in rerank.py**

Modify `Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/discovery/rerank.py`:

Change FEATURE_NAMES (line 13-24) to add "genome_bonus" as the 11th feature:
```python
FEATURE_NAMES = (
    "semantic",
    "form",
    "orthography",
    "sound",
    "skeleton",
    "family_boost",
    "root_match",
    "correspondence",
    "weak_radical_match",
    "hamza_match",
    "genome_bonus",      # NEW: LV1 genome-informed bonus
)
```

Update `_feature_vector()` (line 27-46) to extract the new feature:
```python
def _feature_vector(entry: dict[str, Any]) -> np.ndarray:
    scores = entry.get("scores", {})
    hybrid = entry.get("hybrid", {})
    components = hybrid.get("components", {})
    sound_value = components.get("sound")
    return np.array(
        [
            float(scores.get("semantic", 0.0)),
            float(scores.get("form", 0.0)),
            float(components.get("orthography", 0.0)),
            float(sound_value or 0.0),
            float(components.get("skeleton", 0.0)),
            1.0 if hybrid.get("family_boost_applied") else 0.0,
            float(components.get("root_match", 0.0)),
            float(components.get("correspondence", 0.0)),
            float(components.get("weak_radical_match", 0.0)),
            float(components.get("hamza_match", 0.0)),
            float(components.get("genome_bonus", 0.0)),
        ],
        dtype=np.float32,
    )
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest Juthoor-CognateDiscovery-LV2/tests/test_reranker_genome_feature.py -v`
Expected: PASS

- [ ] **Step 5: Run ALL LV2 tests to check backward compatibility**

Run: `pytest Juthoor-CognateDiscovery-LV2/tests/ -v --tb=short -m "not slow"`
Expected: All pass. Existing reranker models (10-feature) must still load. Check that `DiscoveryReranker.__init__` handles models with fewer features than FEATURE_NAMES gracefully — if not, add backward-compat logic.

- [ ] **Step 6: Commit**

```bash
git add Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/discovery/rerank.py \
       Juthoor-CognateDiscovery-LV2/tests/test_reranker_genome_feature.py
git commit -m "feat(lv2): add genome_bonus as 11th reranker feature"
```

---

### Task B.5 — Ensure genome_bonus Appears in Discovery Leads
**Owner: Sonnet**
**Depends on:** B.4

The GenomeScorer currently applies its bonus to the combined score in `scoring.py`, but the bonus value also needs to be stored in `hybrid.components.genome_bonus` so the reranker can learn from it.

- [ ] **Step 1: Check if scoring.py already stores genome_bonus in components**

Read `Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/discovery/scoring.py` and find `_apply_genome_bonus` or similar. Check whether the genome bonus value is stored in `entry["hybrid"]["components"]["genome_bonus"]`.

- [ ] **Step 2: If not stored, add it**

In the genome bonus application code in `scoring.py`, ensure the bonus value is written to the entry:
```python
entry["hybrid"]["components"]["genome_bonus"] = bonus
```

This way when leads are written to JSONL, the genome_bonus value persists and the reranker can extract it.

- [ ] **Step 3: Test that genome_bonus appears in scored entries**

Add a test in `test_genome_scoring.py` or `test_hybrid_scoring.py` that creates a scorer with GenomeScorer, scores a pair, and asserts `entry["hybrid"]["components"]["genome_bonus"]` exists and is a float.

- [ ] **Step 4: Run tests**

Run: `pytest Juthoor-CognateDiscovery-LV2/tests/ -v --tb=short -m "not slow"`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/discovery/scoring.py \
       Juthoor-CognateDiscovery-LV2/tests/
git commit -m "feat(lv2): persist genome_bonus in lead components for reranker consumption"
```

---

### Task B.6 — Train Reranker with Genome Feature
**Owner: Codex**
**Depends on:** B.3 (expanded Arabic-Hebrew leads), B.4 (genome feature in reranker), B.5 (genome_bonus in leads)

- [ ] **Step 1: Train reranker on Arabic-Hebrew genome leads**

```bash
python scripts/discovery/train_reranker.py \
  --benchmark resources/benchmarks/cognate_gold.jsonl \
  --leads outputs/leads/discovery_ara_heb_genome_v2.jsonl \
  --output outputs/benchmark_experiments/ara_heb_genome_reranker.json
```

- [ ] **Step 2: Apply reranker and compare**

Compare MRR/nDCG:
1. Genome scoring only (no reranker)
2. Genome scoring + reranker with genome_bonus feature
3. Blind scoring + reranker without genome_bonus

- [ ] **Step 3: Report reranker weights**

Inspect `ara_heb_genome_reranker.json` — what weight did the reranker learn for genome_bonus? If positive and significant, genome is a genuinely useful signal. If near zero, the reranker doesn't find it useful beyond what other features capture.

- [ ] **Step 4: Commit**

```bash
git add outputs/benchmark_experiments/ara_heb_genome_reranker.json \
       outputs/reports/
git commit -m "feat(lv2): train reranker with genome_bonus — report learned weights"
```

---

### Task B.7 — Opus Review: Multi-Pair Evaluation Analysis
**Owner: Opus**
**Depends on:** B.1, B.2, B.3, B.6 all complete

- [ ] **Step 1: Review all comparison reports**

Read:
- `outputs/reports/ara_heb_blind_vs_genome_v2.json` — expanded Hebrew evaluation
- `outputs/reports/ara_fa_blind_vs_genome.json` — Persian evaluation
- `outputs/reports/ara_arc_blind_vs_genome.json` — Aramaic evaluation
- `outputs/benchmark_experiments/ara_heb_genome_reranker.json` — reranker weights

- [ ] **Step 2: Write analysis report**

Save to `outputs/reports/lv2_multi_pair_evaluation_review.md`:

Key questions to answer:
- Does the genome improvement hold with 50+ pairs (statistically significant)?
- Does genome help for Aramaic (same script mapping as Hebrew)?
- Does genome help for Persian (shared Arabic-script letters, but not Semitic)?
- What weight did the reranker assign to genome_bonus?
- What are the hardest pairs for the pipeline?
- Recommendations for Phase C

---

## Phase C: GenomeScorer Extension + LV1 Refinements

**Goal:** Extend cross-lingual consonant mappings beyond Hebrew, test untested LV1 hypotheses (H9, H10), and validate LV1 findings cross-linguistically on Hebrew.

**Depends on:** Phase B complete

### Key Files
```
Modify: Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/discovery/genome_scoring.py
Create: Juthoor-ArabicGenome-LV1/tests/test_h9_emphatic.py
Create: Juthoor-ArabicGenome-LV1/tests/test_h10_compositionality.py
Create: Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/factory/experiments/exp_h9_emphatic.py
Create: Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/factory/experiments/exp_h10_compositionality.py
```

---

### Task C.1 — Extend GenomeScorer Consonant Mapping for Aramaic
**Owner: Sonnet**
**Depends on:** B.7 review recommendations

- [ ] **Step 1: Write test for Aramaic consonant mapping**

The existing `_LETTER_CLASS` in `genome_scoring.py` already maps Hebrew-script letters. Aramaic in the LV0 ingest uses Hebrew script ("Hebr"), so the mapping should largely work already. Test this explicitly:

```python
def test_aramaic_consonants_mapped():
    """Aramaic uses Hebrew script — verify consonants resolve to classes."""
    scorer = GenomeScorer()
    # Aramaic כתב → consonants כ,ת,ב → classes ḫ,t,b
    classes = scorer._extract_consonant_classes("כתב")
    assert classes is not None
    assert len(classes) >= 2
```

- [ ] **Step 2: If gaps exist, add missing Aramaic-specific letter mappings**

Some Aramaic letters may differ from Hebrew. Check and extend `_LETTER_CLASS` if needed.

- [ ] **Step 3: Run tests and commit**

---

### Task C.2 — Extend GenomeScorer Consonant Mapping for Persian
**Owner: Sonnet**
**Depends on:** B.7 review recommendations

- [ ] **Step 1: Add Persian-specific letters to _LETTER_CLASS**

Persian uses Arabic script plus 4 extra letters: پ (pe), چ (che), ژ (zhe), گ (gaf). Add:
```python
"پ": "p",   # Persian pe — no Arabic/Hebrew equivalent
"چ": "č",   # Persian che
"ژ": "ž",   # Persian zhe
"گ": "g",   # Persian gaf (vs Arabic ج/Hebrew ג)
```

- [ ] **Step 2: Write tests for Persian consonant extraction**

- [ ] **Step 3: Run tests and commit**

---

### Task C.3 — LV1 Hypothesis H9: Emphatic Letters Are Stronger
**Owner: Codex**
**Depends on:** Nothing (independent of LV2 work)

- [ ] **Step 1: Design experiment**

H9 claims emphatic consonants (ط vs ت, ض vs د, ص vs س, ظ vs ذ) carry stronger semantic impact than their non-emphatic counterparts.

Test by comparing semantic coherence of root families that differ only in emphatic vs non-emphatic letter.

- [ ] **Step 2: Implement experiment**

Create `exp_h9_emphatic.py` following the experiment runner pattern in LV1.

- [ ] **Step 3: Write tests, run, and commit**

---

### Task C.4 — LV1 Hypothesis H10: Full Compositionality
**Owner: Codex**
**Depends on:** Nothing

- [ ] **Step 1: Design experiment**

H10 claims root meaning approximates letter1_meaning + letter2_meaning + letter3_meaning. Test by computing cosine similarity between root embedding and sum/average of positional letter embeddings.

- [ ] **Step 2: Implement, test, and commit**

---

### Task C.5 — Cross-Lingual Validation: H2/H5/H8 on Hebrew Roots
**Owner: Codex**
**Depends on:** C.3, C.4 (do new hypotheses first)

Run the same field coherence (H2), order matters (H5), and positional semantics (H8) experiments on Hebrew trilateral roots. If the findings replicate across Arabic and Hebrew, the theory gains significant weight.

This requires:
1. Extracting Hebrew trilateral roots from the LV0 Hebrew data
2. Computing embeddings for Hebrew root families
3. Running the same statistical tests

**This is the most ambitious Phase C task.** Details TBD based on B.7 review recommendations.

---

## Dependency Graph

```
Phase A (Benchmark)                    Phase B (Discovery + Reranker)           Phase C (Extension)
═══════════════════                    ═══════════════════════════════           ══════════════════

A.1 expand ara-heb ──┐
                     │
A.2 add ara-fa pairs ├──→ [100+ pairs] ──→ B.1 ara-fa discovery
                     │                     B.2 ara-arc discovery
A.3 add ara-arc pairs┤                     B.3 ara-heb re-eval ──┐
                     │                                            ├──→ B.7 Opus review ──→ C.1 Aramaic mapping
A.4 strengthen negs ─┘                     B.4 genome→reranker ──┤                       C.2 Persian mapping
                                           B.5 persist bonus ────┤                       C.3 H9 emphatic
                                           B.6 train reranker ───┘                       C.4 H10 compositionality
                                                                                          C.5 Hebrew cross-validation
```

---

## Execution Order

### Immediate — Start NOW in parallel:

**Sonnet (Builder):**
- A.1: Expand Arabic-Hebrew gold pairs (25+ new pairs)
- B.4: Add genome_bonus to reranker features (independent of benchmark)

**Codex (Heavy Lifter):**
- C.3: H9 emphatic experiment (independent, can start immediately)
- C.4: H10 compositionality experiment (independent)

### After A.1:

**Sonnet:**
- A.2: Add Arabic-Persian pairs
- A.3: Add Arabic-Aramaic pairs
- A.4: Strengthen negatives

### After A.2, A.3, A.4:

**Codex:**
- B.1: Arabic-Persian discovery (blind + genome)
- B.2: Arabic-Aramaic discovery (blind + genome)
- B.3: Arabic-Hebrew re-evaluation with expanded benchmark

### After B.4, B.5:

**Sonnet:**
- B.5: Ensure genome_bonus persists in lead components

### After B.1-B.3 + B.5:

**Codex:**
- B.6: Train reranker with genome feature

### After B.1-B.3 + B.6:

**Opus:**
- B.7: Multi-pair evaluation review

### After B.7:

**Sonnet:**
- C.1: Aramaic consonant mapping
- C.2: Persian consonant mapping

**Codex:**
- C.5: Hebrew cross-lingual validation (if recommended by B.7)

---

## Assignment Summary

### Sonnet Tasks

| Task | Description | Depends on |
|------|-------------|-----------|
| A.1 | Expand Arabic-Hebrew gold to 50+ pairs | Nothing (start now) |
| A.2 | Add 20+ Arabic-Persian pairs | A.1 |
| A.3 | Add 15+ Arabic-Aramaic pairs | A.1 |
| A.4 | Strengthen negatives to 30+ | A.1 |
| B.4 | Add genome_bonus to reranker features | Nothing (start now) |
| B.5 | Persist genome_bonus in lead components | B.4 |
| C.1 | Extend consonant mapping for Aramaic | B.7 |
| C.2 | Extend consonant mapping for Persian | B.7 |

### Codex Tasks

| Task | Description | Depends on |
|------|-------------|-----------|
| B.1 | Arabic-Persian discovery (blind + genome) | A.2 |
| B.2 | Arabic-Aramaic discovery (blind + genome) | A.3 |
| B.3 | Arabic-Hebrew re-eval with 50+ pairs | A.1 |
| B.6 | Train reranker with genome feature | B.3, B.5 |
| C.3 | H9 emphatic experiment (LV1) | Nothing (start now) |
| C.4 | H10 compositionality experiment (LV1) | Nothing (start now) |
| C.5 | Hebrew cross-lingual H2/H5/H8 validation | C.3, C.4, B.7 |

### Opus Tasks

| Task | Description | When |
|------|-------------|------|
| B.7 | Multi-pair evaluation review | After B.1-B.3 + B.6 |

---

## Context Files for All Agents

Before starting, read:
1. **This file** — your task assignments
2. **`docs/plans/STATUS_TRACKER.md`** — current project state
3. **`Juthoor-CognateDiscovery-LV2/resources/benchmarks/cognate_gold.jsonl`** — benchmark to expand
4. **`Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/discovery/genome_scoring.py`** — GenomeScorer
5. **`Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/discovery/rerank.py`** — reranker to extend
6. **`Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/discovery/scoring.py`** — scoring pipeline
7. **`Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_retrieval.py`** — discovery entry point
8. **`outputs/reports/lv2_genome_integration_review.md`** — previous review

## Quality Gates

1. **Benchmark has 100+ gold pairs** across 3 language pairs before any Phase B evaluation
2. **All existing tests pass** (LV0: 174, LV1: 227, LV2: 215+)
3. **New tests for every new feature** (benchmark expansion tests, reranker genome feature tests)
4. **GenomeScorer remains optional** — pipeline works identically without it
5. **Reranker backward compatible** — old 10-feature models still load
6. **Each discovery run produces** leads JSONL + metrics JSON for reproducibility
7. **No evaluation runs before benchmark expansion** — measure on the expanded benchmark, not the old one

---

*LV2 Evaluation Expansion — Execution Orchestration*
*Juthoor Linguistic Genealogy*
*2026-03-16*
