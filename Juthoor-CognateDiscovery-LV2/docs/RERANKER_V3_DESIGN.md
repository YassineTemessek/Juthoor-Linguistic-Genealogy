# Reranker V3 Design Specification

**Date:** 2026-03-27
**Motivation:** Reranker v2 analysis revealed 6 anti-signal features and 3 missing positive features

## V2 Weight Analysis

| Feature | V2 Weight | Assessment |
|---------|----------|------------|
| multi_method_score | **+1.389** | Strongest positive — KEEP |
| phonetic_law_bonus | +0.107 | Positive — KEEP |
| correspondence | +0.063 | Slight positive — KEEP |
| genome_bonus | -0.014 | Neutral — KEEP (important for Semitic) |
| source_coherence | 0.0 | No signal — KEEP (may help with LV1 data) |
| semantic | 0.0 | No signal (fast mode) — KEEP (vital in full mode) |
| form | 0.0 | No signal (fast mode) — KEEP |
| sound | 0.0 | No signal (fast mode) — KEEP |
| **skeleton** | **-0.697** | ANTI-SIGNAL — REMOVE |
| **orthography** | **-0.536** | ANTI-SIGNAL — REMOVE |
| **family_boost** | **-1.075** | ANTI-SIGNAL — REMOVE |
| **root_match** | **-0.307** | ANTI-SIGNAL — REMOVE |
| **weak_radical_match** | **-0.635** | ANTI-SIGNAL — REMOVE |
| **hamza_match** | **-0.635** | ANTI-SIGNAL — REMOVE |

## V3 Feature Set (11 features)

### Kept from V2 (8 features)
1. `semantic` — BGE-M3 embedding similarity
2. `form` — ByT5 form similarity
3. `sound` — IPA-based consonant similarity
4. `correspondence` — consonant correspondence matrix score
5. `genome_bonus` — LV1 binary root coherence (Semitic pairs only)
6. `phonetic_law_bonus` — sound law projection score
7. `source_coherence` — LV1 field coherence of Arabic root
8. `multi_method_score` — 12-method best score (strongest signal)

### New in V3 (3 features)
9. `cross_pair_evidence` — convergent evidence from cognate graph (0-1, how many target languages match this Arabic root)
10. `root_quality` — H12 meaning predictability score for the Arabic root (0-1)
11. `methods_fired_count` — number of methods that fired for this pair (integer, normalized to 0-1 by dividing by 12)

### Removed from V2 (6 features)
- `skeleton` — anti-correlated with real cognates (-0.697)
- `orthography` — anti-correlated (-0.536)
- `family_boost` — anti-correlated (-1.075). Same-family flag is NOT helpful
- `root_match` — anti-correlated (-0.307). Exact root matches are usually within-language
- `weak_radical_match` — anti-correlated (-0.635)
- `hamza_match` — anti-correlated (-0.635)

## Expected Impact

- Removing 6 noise features should dramatically improve signal-to-noise ratio
- Adding cross_pair_evidence should boost convergent matches (153 roots with 3+ languages)
- Adding root_quality should boost well-formed Arabic roots (H12 validated)
- Adding methods_fired_count rewards diverse evidence (multiple independent methods agreeing)

## Training Data
- 1,889 gold pairs (positive examples)
- 31 negative pairs (explicit negatives)
- ~500 random non-matching pairs from leads (hard negatives)
- Cross-validated 5-fold

## Implementation
Codex dispatched to implement in `rerank.py` and retrain.
