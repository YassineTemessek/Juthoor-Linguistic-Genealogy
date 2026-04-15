# Juthoor AutoResearch — Experiment Plan

## Goal

Apply Karpathy's autoresearch hill-climbing loop to the Juthoor cognate-discovery
pipeline. An LLM agent iteratively edits a single mutable file, runs the pipeline
against a frozen evaluation harness, and keeps only changes that improve a
null-model-adjusted metric. The aim is to systematically optimize scoring weights,
correspondence rules, and normalization — work that is currently done by hand.

---

## Architecture (3-file contract)

Karpathy's design has three roles. We map each to Juthoor:

| Role | Karpathy original | Juthoor analog | Rationale |
|------|-------------------|----------------|-----------|
| **prepare.py** | Data loading, tokenizer, eval harness. *Agent cannot touch.* | `prepare.py` — loads corpora, gold set, null-model sampler, scorer. | Protects the null model and test data from being gamed. |
| **train.py** | Model + optimizer + training loop. *Agent edits this.* | `experiment.py` — scoring weights, bonus caps, correspondence maps, normalization rules. | Single file the agent mutates each iteration. |
| **program.md** | Human steering doc. | `program.md` — theory constraints, banned shortcuts, phase gates. | Prevents the agent from statistical trickery. |

Plus an **orchestrator** (`loop.py`) that runs the hill-climbing cycle.

---

## Evaluation Metric

The gating metric must be **null-model-adjusted** so that raw hit-rate inflation
is impossible. We define:

```
Δz = z_candidate − z_baseline
```

Where `z` is the z-score from the existing permutation test
(`validate_corridors_statistical.py`), computed as:

```
z = (real_count − null_mean) / null_std
```

**Acceptance rule**: keep the change if and only if:

1. `z_candidate >= z_baseline` (no regression on null-adjusted significance), AND
2. At least one of:
   - `z_candidate > z_baseline + 0.05` (measurable improvement), OR
   - `real_count_candidate > real_count_baseline` with `z_candidate >= z_baseline`
     (more discoveries without significance loss).

If both conditions fail, **revert**.

### Secondary metrics (logged, never gated)

- Raw hit count at threshold 0.30
- Mean hybrid score (real vs. null)
- Precision on gold cognate pairs (if gold set available)
- Per-bonus contribution breakdown

---

## The Three Files

### 1. `prepare.py` — Frozen Evaluation Harness

**What it does** (agent CANNOT modify):

- Loads Arabic corpus (`unified_arabic_discovery.jsonl`, limit=50)
- Loads English/Greek/Latin corpus (limit=200)
- Loads gold cognate pairs (held-out set the agent never sees during optimization)
- Computes BGE-M3 semantic embeddings and ByT5 form embeddings
- Runs the null-model permutation test (100 shuffles)
- Computes z-score (count-based and mean-based)
- Returns a single JSON result: `{z_count, z_mean, z_best, real_count, real_mean, null_mean, null_std, p_value}`

**Source**: Adapted from `Juthoor-Origins-LV3/scripts/validate_corridors_statistical.py`
with these changes:
- Reads scoring config from `experiment.py` instead of hardcoded `HybridWeights()`
- Adds gold-set precision calculation
- Outputs machine-readable JSON (not just prints)
- Seeds are fixed (42) for reproducibility

### 2. `experiment.py` — The Mutable File

This is the **only file the agent edits**. It exports a single config object
that `prepare.py` imports. Everything tunable lives here:

```python
# experiment.py — THE MUTABLE FILE
# The autoresearch agent edits this file each iteration.
# prepare.py imports EXPERIMENT_CONFIG and uses it for scoring.

from dataclasses import dataclass

@dataclass(frozen=True)
class ExperimentConfig:
    """All tunable parameters for one experiment iteration."""

    # --- Hybrid weights (must sum to ~1.0) ---
    semantic_weight: float = 0.55
    form_weight: float = 0.45

    # --- Bonus caps ---
    phonetic_law_cap: float = 0.15
    genome_cap: float = 0.10
    multi_method_cap: float = 0.12
    cross_pair_cap: float = 0.10
    root_quality_cap: float = 0.08

    # --- Thresholds ---
    prefilter_threshold: float = 0.50
    final_threshold: float = 0.45
    null_threshold: float = 0.30        # count-above threshold for z-score

    # --- Correspondence class map ---
    # Maps characters → abstract phonetic classes for skeleton comparison.
    # Agent may add/remove/remap entries.
    class_map: dict = None  # populated in __post_init__

    # --- Correspondence bonus coefficients ---
    correspondence_coeff: float = 0.12   # weight for class-trace ratio
    hamza_coeff: float = 0.04            # weight for hamza normalization match
    weak_radical_coeff: float = 0.05     # weight for weak-radical collapse match
    correspondence_cap: float = 0.21     # max total correspondence bonus

    # --- Normalization rules ---
    # Which characters are considered weak radicals (removed in skeleton)
    weak_radicals_ar: str = "اويى"
    weak_radicals_lat: str = "aeiouy"

    # Hamza normalization map (source → canonical form)
    hamza_map: dict = None  # populated in __post_init__

    def __post_init__(self):
        if self.class_map is None:
            object.__setattr__(self, 'class_map', {
                # Arabic → class
                "ب": "B", "ف": "B", "پ": "B",
                "م": "M",
                "ت": "T", "ط": "T", "ث": "T", "د": "T", "ض": "T", "ذ": "T", "ظ": "T",
                "س": "S", "ص": "S", "ز": "S", "ش": "S", "ج": "S",
                "ر": "R", "ل": "R", "ن": "R",
                "ك": "K", "ق": "K", "گ": "K",
                "و": "W", "ي": "W", "ى": "W",
                "ء": "A", "ا": "A", "أ": "A", "إ": "A", "آ": "A", "ٱ": "A",
                "ه": "H", "ح": "H", "خ": "H",
                "ع": "E", "غ": "E",
                # Latin/IPA → class
                "b": "B", "f": "B", "v": "B",
                "m": "M",
                "t": "T", "d": "T", "ṭ": "T", "ḍ": "T", "ð": "T", "θ": "T", "ẓ": "T",
                "s": "S", "z": "S", "c": "S", "j": "S", "g": "S", "š": "S", "ṣ": "S",
                "r": "R", "l": "R", "n": "R",
                "k": "K", "q": "K",
                "w": "W", "y": "W",
                "h": "H", "ḥ": "H", "ḫ": "H", "x": "H",
                "ʕ": "E", "ġ": "E", "ɣ": "E",
                "ʔ": "A",
            })
        if self.hamza_map is None:
            object.__setattr__(self, 'hamza_map', {
                "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
                "ؤ": "و", "ئ": "ي", "ء": "ا",
            })


EXPERIMENT_CONFIG = ExperimentConfig()
```

**What the agent can change:**
- All numeric weights and caps
- The class_map (add classes, split classes, merge classes)
- The hamza_map (change canonical targets)
- The weak_radical sets
- The null_threshold
- Add new fields (e.g. metathesis_tolerance, biliteral_expansion flag)

**What the agent CANNOT do:**
- Import or call external code (prepare.py enforces this by importing only the dataclass)
- Modify the evaluation harness
- Access the gold set directly

### 3. `program.md` — Agent Steering Document

```markdown
# Juthoor AutoResearch — Agent Instructions

## Your task
You are optimizing the scoring configuration for an Arabic phonosemantic
cognate-discovery pipeline. Each iteration you edit `experiment.py`, the
harness runs a null-model-adjusted evaluation, and your change is accepted
only if the z-score does not regress and either the z-score or hit count
improves.

## What you're optimizing
The pipeline compares Arabic roots to Greek/Latin words using:
1. Semantic similarity (BGE-M3 embeddings of glosses)
2. Form similarity (ByT5 embeddings of orthographic forms)
3. Correspondence features (consonant class skeleton matching)
4. Seven bonus layers (root match, correspondence, genome, root quality,
   phonetic law, multi-method, cross-pair)

Your edits control the weights, caps, thresholds, and class mappings.

## Constraints — DO NOT violate
1. **semantic_weight + form_weight must be approximately 1.0** (±0.05).
2. **No bonus cap may exceed 0.40** — individual bonuses should stay small.
3. **Total bonus caps must not exceed 1.0** combined.
4. **The class_map must remain linguistically coherent** — do not merge
   classes arbitrarily (e.g. don't merge labials B with velars K).
5. **Do not remove entries from hamza_map** — only add or retarget.
6. **weak_radicals_ar must contain at least "اوي"** (core weak radicals).
7. **null_threshold must stay in [0.15, 0.50]** — don't game by moving it.

## Strategy hints
- The current z-score is ~3.23 (just below the 3.29 gate). Small targeted
  changes may push it over.
- The correspondence class map is the most undertested lever. Consider:
  - Splitting the S-class (sibilants) into S1 (emphatic) and S2 (plain)
  - Splitting the T-class (dentals/emphatics) similarly
  - Adding Greek-specific mappings (φ→B, θ→T, χ→H, etc.)
- The normalization (weak radicals, hamza) directly affects skeleton matching.
  Overly aggressive stripping loses signal; too little stripping misses matches.
- Try increasing correspondence_coeff — it may be underweighted at 0.12.
- The genome_cap and root_quality_cap are sourced from LV1. They encode
  real Arabic-internal structure and may deserve more weight.

## What NOT to do
- Do not lower null_threshold below 0.20 just to inflate hit counts.
- Do not set all bonus caps to 0 — the bonus stack is where linguistic
  knowledge enters the scoring.
- Do not add Python imports or executable code beyond the dataclass.
- Do not try to optimize for a single known pair — the metric is aggregate.

## Experiment history
The agent log below is updated automatically after each iteration.
Use it to track what worked and what didn't.

### Log
(auto-populated by loop.py)
```

---

## The Loop (`loop.py`)

### Pseudocode

```
load baseline z-score from last accepted run (or run fresh baseline)

while True:
    1. Read program.md + experiment.py + last 10 log entries
    2. Ask LLM: "Propose ONE targeted change to experiment.py. Explain why."
    3. Write the LLM's proposed experiment.py to disk
    4. Run: python prepare.py  →  result.json
    5. Parse z_candidate, real_count_candidate from result.json
    6. If ACCEPT(z_candidate, z_baseline, real_count_candidate, real_count_baseline):
         - z_baseline = z_candidate
         - real_count_baseline = real_count_candidate
         - git commit experiment.py -m "exp-{N}: {description} | z={z_candidate:.2f}"
         - Append ✅ to program.md log
       Else:
         - git checkout experiment.py  (revert)
         - Append ❌ to program.md log
    7. N += 1
    8. If N >= MAX_ITERATIONS: break
```

### Time budget

- Each `prepare.py` run: ~3–8 min (50×200 pairs + 100 permutations)
  - Embedding computation: ~60s (cached after first run)
  - 100 null permutations × re-embed: ~2–5 min
  - Scoring + z-score: <10s
- LLM proposal: ~15–30s
- **Per iteration: ~4–9 min**
- **Overnight (8h): ~50–120 experiments**

### Optimizations for speed

1. **Cache embeddings**: ByT5 form embeddings never change (based on lemma orthography).
   Cache to disk on first run.
2. **Reduce permutations for screening**: Run 20 permutations during the loop
   (fast z-estimate). If z_candidate < z_baseline - 0.5, reject immediately.
   Run full 100 permutations only for candidates that pass the screen.
3. **Parallel embedding**: Pre-compute all English embeddings once (they never change).

---

## Three Experiment Phases

### Phase 1: Normalization (PRIORITY — start here)

**Target**: Fix the normalization rules that inflate the 854 Greek / 53 Latin
provisional counts.

**What the agent mutates**:
- `weak_radicals_ar` / `weak_radicals_lat` (what gets stripped)
- `hamza_map` (Arabic normalization targets)
- `class_map` entries for Greek characters (φ, θ, χ, ψ, etc.)
- `null_threshold` (within bounds)

**Success gate**: z ≥ 3.29 (p < 0.001) — the current blocker.

**program.md addendum for Phase 1**:
- Focus on Greek-specific mappings. The pipeline was tuned on English first;
  Greek has aspirates (φ, θ, χ) and clusters (ψ=ps, ξ=ks) that may need
  their own class entries.
- The Latin corpus is small (53 pairs). Changes that help Greek but hurt Latin
  should be flagged, not automatically accepted.

### Phase 2: Scoring Weights & Bonus Caps

**Target**: Optimize the hybrid weight balance and bonus stack.

**What the agent mutates**:
- `semantic_weight`, `form_weight`
- All `*_cap` fields
- `correspondence_coeff`, `hamza_coeff`, `weak_radical_coeff`

**Success gate**: z ≥ 3.50 + real_count improvement over Phase 1 baseline.

**program.md addendum for Phase 2**:
- Phase 1 has already fixed normalization. Now you're tuning how much each
  scoring signal contributes.
- The genome and root-quality bonuses encode Arabic-internal structure from LV1.
  They should be non-zero; try increasing them.
- The phonetic_law_cap covers known sound correspondences. It should be the
  second-largest bonus after correspondence.

### Phase 3: Diachronic Generalization Test

**Target**: Validate that Phase 1+2 optimizations generalize to unseen languages.

**Method**: Hold out Gothic + Old Irish (when available). Optimize on Greek+Latin.
Run the frozen optimized config on the held-out languages.

**What the agent mutates**: Nothing — this is an evaluation-only phase.

**Success gate**: z ≥ 2.00 on held-out languages without any tuning.

---

## File Layout

```
autoresearch/
├── PLAN.md              ← this file
├── program.md           ← agent steering document (human-edited)
├── experiment.py        ← the ONLY file the agent edits
├── prepare.py           ← frozen evaluation harness
├── loop.py              ← hill-climbing orchestrator
├── baseline.json        ← last accepted z-score + config snapshot
├── results/             ← per-iteration result JSONs
│   ├── exp-001.json
│   ├── exp-002.json
│   └── ...
└── logs/
    └── agent.log        ← full agent interaction log
```

---

## Setup Checklist

Before running the loop:

- [ ] **Gold set**: Extract a held-out set of known cognate pairs from
      `Juthoor-CognateDiscovery-LV2/data/processed/` that `prepare.py` uses
      for precision measurement but the agent never sees.
- [ ] **Corpus files**: Symlink or copy Arabic + English/Greek/Latin corpora
      into `autoresearch/data/` so prepare.py can load them without reaching
      into the main repo.
- [ ] **Dependencies**: Ensure `juthoor_cognatediscovery_lv2` is importable
      (add LV2/src to PYTHONPATH or install in editable mode).
- [ ] **Embeddings cache**: Run `prepare.py` once manually to warm the
      embedding cache. Verify the baseline z-score matches expectations (~3.23).
- [ ] **Git init**: Initialize a git repo in `autoresearch/` so the loop can
      commit accepted changes and revert rejected ones.
- [ ] **LLM API key**: The loop needs an API key for the agent LLM (Claude or
      GPT-4). Set via `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`.
- [ ] **Screen/tmux**: Run the loop in a persistent session so it survives
      terminal disconnection.

---

## Risk Mitigations

| Risk | Mitigation |
|------|-----------|
| Agent games the metric by lowering null_threshold | Hard-capped at [0.15, 0.50] in constraints + prepare.py validates |
| Agent breaks experiment.py syntax | loop.py catches ImportError, logs ❌, reverts |
| Overfitting to Greek (854 pairs dominate) | Phase 3 held-out test on Gothic/Old Irish; log per-language z-scores |
| Embedding drift if agent changes semantic preprocessing | Agent cannot touch prepare.py; embeddings computed by the harness |
| Agent writes executable code in experiment.py | prepare.py imports only the dataclass; no exec()/eval() |
| Gold set leakage | Gold set loaded only inside prepare.py; agent sees only the scalar z-score |
| Loss of best config after crash | Every accepted experiment is git-committed with its z-score |

---

## Expected Outcomes

**Optimistic**: z crosses 3.29 in Phase 1 (overnight), reaching 3.5+ in Phase 2.
The normalization fix reduces the 854 Greek count to a smaller but defensible number.
Phase 3 shows z ≥ 2.0 on Gothic/Old Irish, confirming generalization.

**Realistic**: Phase 1 takes 2–3 overnight runs to cross 3.29. Phase 2 adds ~0.2
to z. Some experiments reveal that specific class_map splits (e.g., separating
emphatics) account for most of the gain — a publishable finding.

**Pessimistic**: z plateaus below 3.29 despite 200+ experiments. This means the
bottleneck is not in the scoring config but in the underlying embeddings or corpus
quality — which is itself a valuable finding that redirects effort.

---

## How to Run

```bash
cd autoresearch/
git init
python prepare.py                  # warm cache, verify baseline
python loop.py --max-iterations 100 --model claude-sonnet-4-5-20250514
# or: python loop.py --max-iterations 50 --model gpt-4o
```

Monitor progress:
```bash
tail -f logs/agent.log
git log --oneline                  # see accepted experiments
cat baseline.json                  # current best z-score
```

---

*Created 2026-04-15 for Juthoor-Linguistic-Genealogy autoresearch experiments.*
