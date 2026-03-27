# Juthoor Project Metrics Dashboard

**Last updated:** 2026-03-27 (Mega Sprint)

## Data Scale

| Metric | Value |
|--------|-------|
| Total lexemes ingested | ~2.64M |
| Languages in LV0 | 11 (+ Turkish, Akkadian test corpora) |
| Gold benchmark pairs | 1,889 across 13 language pairs |
| Negative benchmark pairs | 31 |
| Cognate graph nodes | 12,455 |
| Cognate graph edges | 47,071 |
| Graph languages | 7 (ara, eng, lat, grc, heb, per/fas, arc) |
| LV3 validated leads | 14,494 |
| Convergent roots (3+ langs) | 153 |

## LV1 Research Factory

| Hypothesis | Status | Key Metric |
|-----------|--------|------------|
| H2: Field coherence | **Supported** | >11σ above baseline |
| H5: Order matters | **Supported** | Wilcoxon p=0.014 |
| H8: Positional semantics | **Supported** | 24/28 letters (86%) |
| H12: Meaning predictability | **Supported** | cosine=0.716, AUC=0.739 |
| H1, H3, H4, H6, H7, H9-H11 | Various | See FINAL_SYNTHESIS.md |

## LV2 Discovery Engine

| Component | Value |
|-----------|-------|
| Scoring methods | 12 (MultiMethodScorer) |
| Reranker features | 11 (v3, anti-signals removed) |
| Scoring profiles | 6 per-language-pair |
| Best method precision | multi_hop_chain at 3.4% |
| Gold coverage (ara-eng) | 32.1% (269/837) |
| Scoring guards | 5 (min-consonant, length-ratio, min-score, diversity, short-root) |
| Bonus systems | 7 (root_match, correspondence, genome, phonetic_law, multi_method, root_quality, cross_pair) |

## LV3 Theory

| Component | Value |
|-----------|-------|
| Corridor cards | 10 |
| Corridors confirmed | 8/10 (automated Tier 1+2 validation) |
| Corridors provisional | 2/10 (guttural deletion, article absorption) |
| Anchor tiers | gold: 10,177 (70.2%), silver: 4,068 (28.1%), auto_brut: 249 (1.7%) |
| Theory documents | Theory synthesis, validation methodology, methodology note |

## Consonant Correspondence (empirical, 3,461 alignments)

| Arabic | English Primary | Rate | Notable |
|--------|----------------|------|---------|
| ع (ʿayn) | DELETED | **88%** | Strongest single correspondence |
| ر (rā') | r | 65% | Most stable consonant |
| ت (tā') | t | 60% | |
| س (sīn) | s | 56% | |
| م (mīm) | m | 51% | |
| ب (bā') | b | 34% | p at 22% — nearly equal! |
| ف (fā') | f | 31% | 3-way split: f/p/v |
| ق (qāf) | c | 39% | Not k or q |

## Test Suite

| Level | Tests | Status |
|-------|-------|--------|
| LV0 | 167 | All passing |
| LV1 | 498 | All passing |
| LV2 | 422+ | All passing |
| **Total** | **1,097+** | **All passing** |

## Session Stats (2026-03-27 Mega Sprint)

| Metric | Value |
|--------|-------|
| Commits | 38 |
| Lines of code added | ~8,000+ |
| New Python modules | 15+ |
| New documents | 12 |
| Codex tasks dispatched | 15+ |
| Sonnet agents spawned | 10+ |
| Research bundles exported | 1 (25 files) |
