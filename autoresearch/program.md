# Juthoor AutoResearch — Agent Instructions

## Your task

You are optimizing the scoring configuration for an Arabic phonosemantic
cognate-discovery pipeline. Each iteration you edit `experiment.py`, the
harness runs a null-model-adjusted evaluation, and your change is accepted
only if the z-score does not regress and either the z-score or hit count
improves.

## What you're optimizing

The pipeline compares Arabic roots to Greek/Latin words using:

1. **Semantic similarity** (BGE-M3 embeddings of glosses)
2. **Form similarity** (ByT5 embeddings of orthographic forms)
3. **Correspondence features** (consonant class skeleton matching)
4. **Seven bonus layers**: root match, correspondence, genome, root quality,
   phonetic law, multi-method, cross-pair

Your edits control the weights, caps, thresholds, and class mappings in
`experiment.py`. That is the ONLY file you may edit.

## How scoring works

The hybrid score for each Arabic–target pair is:

```
base = semantic_weight × sem_sim + form_weight × form_sim
bonus = min(cap, coeff × feature) for each bonus layer
final = min(1.0, base + sum(bonuses))
```

The **z-score** compares how many pairs exceed `null_threshold` in the real
pipeline vs. 100 random permutations (shuffled root–gloss associations):

```
z = (real_count - null_mean) / null_std
```

**Gate**: z ≥ 3.29 → validated (p < 0.001). Current baseline: ~3.23.

## Constraints — DO NOT violate

1. `semantic_weight + form_weight` must be approximately 1.0 (±0.05).
2. No individual bonus cap may exceed 0.40.
3. Total bonus caps must not exceed 1.0 combined.
4. The `class_map` must remain linguistically coherent — do not merge
   unrelated classes (e.g., don't merge labials B with velars K).
5. Do not remove entries from `hamza_map` — only add or retarget.
6. `weak_radicals_ar` must contain at least "اوي" (core weak radicals).
7. `null_threshold` must stay in [0.15, 0.50].
8. Do not add Python imports or executable code beyond the dataclass.

## Strategy hints

- The current z-score is ~3.23 (just below 3.29). Small targeted changes
  may push it over.
- **Correspondence class map**: the most undertested lever. Consider:
  - Splitting S-class (sibilants) into S1 (emphatic ص) and S2 (plain س/ش)
  - Splitting T-class (dentals/emphatics) into T1 (emphatic ط/ض) and T2 (plain ت/د)
  - Adding Greek-specific mappings: φ→B, θ→T, χ→H, ψ→BS, ξ→KS
  - Adding Latin-specific mappings as needed
- **Normalization**: weak radical stripping directly affects skeleton matching.
  Overly aggressive stripping loses signal; too little misses matches.
- `correspondence_coeff` may be underweighted at 0.12 — try increasing it.
- `genome_cap` and `root_quality_cap` encode real Arabic-internal structure.
  They may deserve more weight.
- The phonetic_law_cap covers known sound correspondences. It should be the
  second-largest bonus after correspondence.

## What NOT to do

- Do not lower `null_threshold` below 0.20 just to inflate hit counts.
- Do not set all bonus caps to 0.
- Do not add Python imports or side effects.
- Do not optimize for a single known pair — the metric is aggregate.
- Do not change more than 2–3 parameters at once — isolate what works.

## Experiment history

The log below is updated automatically after each iteration. Read it to
understand what has been tried, what worked, and what failed. Avoid
repeating failed experiments unless you have a new hypothesis about why
the previous attempt failed.

### Log

(auto-populated by loop.py)
