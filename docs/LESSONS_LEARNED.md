# Lessons Learned: Mega Sprint 2026-03-27

## 1. Source Coverage Matters More Than Scoring Sophistication

**Discovery:** Gold pair coverage jumped from 0.24% to 32.1% simply by adding the right Arabic source entries. No scoring algorithm change could have achieved this.

**Lesson:** Before tuning scoring algorithms, ensure your source and target corpora actually contain the entities you're looking for. A perfect scorer can't find what isn't in the input.

**Specific issue:** The Quranic Arabic corpus (4,903 entries) had only 0.9% overlap with the gold benchmark's Arabic lemmas (954 unique). The benchmark uses general Arabic vocabulary (أرض earth, ثور steer, قرن horn) while the Quranic corpus has religious/theological vocabulary.

## 2. Fast-Mode Consonant Matching = Random Chance

**Discovery:** Null model permutation test showed z-score = 0.0 — shuffling Arabic roots produces exactly the same number of consonant matches as real roots.

**Lesson:** Consonant skeleton matching alone has ZERO discriminative power for cross-family cognate detection. Consonant frequency distributions determine match rates, not linguistic relationships. Semantic filtering (meaning comparison) is ESSENTIAL.

**Implication:** All 10 corridor cards, the cognate graph, and discovery leads from fast-mode runs should be treated as "mechanically correct but statistically unvalidated" until re-validated with semantic filtering.

## 3. Anti-Signal Features Are Real

**Discovery:** Reranker v2 training revealed that skeleton (-0.70), orthography (-0.54), family_boost (-1.08), root_match (-0.31), weak_radical_match (-0.63), and hamza_match (-0.63) are all ANTI-correlated with true cognates.

**Lesson:** High surface-level similarity (same spelling, same consonant frame) is actually a counter-indicator for cross-family cognates. Real cognates undergo systematic sound shifts that CHANGE the surface form. If two words look identical across language families, they're more likely loanwords or false friends than inherited cognates.

## 4. Multi-Hop Chain Has Best Precision

**Discovery:** Among 12 methods, multi_hop_chain (Arabic → Latin/Greek → English) has the best precision at 3.4%. Metathesis has the worst at 0.11%.

**Lesson:** Historical transmission pathways (tracing through intermediate languages) are more reliable than pure consonant pattern matching. This makes linguistic sense — words that actually traveled Arabic → Latin → English leave traces in the intermediate language.

## 5. Convergent Evidence Is the Strongest Signal

**Discovery:** 153 Arabic roots connect to 3+ independent target languages. These roots match English AND Latin AND Greek AND Hebrew etc. independently.

**Lesson:** If a pattern appears in multiple independent languages, it's much less likely to be accidental. Cross-pair convergent evidence should be weighted heavily in any scoring system.

## 6. Hebrew/Greek/Aramaic Need IPA Extraction

**Discovery:** Discovery runs for Hebrew and Greek initially returned 0 leads because consonant extraction functions couldn't process Hebrew/Greek script characters.

**Lesson:** Any cross-linguistic system must handle multiple writing systems. The IPA field is the universal bridge — it provides Latin-alphabet phonetic transcriptions regardless of the source script.

## 7. Scale of Computation

**Discovery:** 30 Arabic × 200 English = 6,000 pairs takes ~5 minutes with the full 12-method scorer. 500 × 10,000 = 5,000,000 pairs would take ~70 hours.

**Lesson:** The MultiMethodScorer is too expensive for large-scale brute-force discovery. A fast prefilter (consonant skeleton matching) followed by selective full scoring is essential. The existing 3-phase approach (precompute → prefilter → score top candidates) is architecturally correct.

## 8. Orchestration Wins

**Discovery:** Using Claude Opus for architecture/analysis + Sonnet for implementation + Codex for heavy compute produced 44 commits in a single session.

**Lesson:** Multi-agent orchestration with clear role boundaries (Opus = brain, Sonnet = hands, Codex = muscle) is highly productive. Each agent type has optimal tasks. Trying to use one agent for everything is slower.

## 9. The "Linguistic Genome" Hypothesis Status

After this sprint, the hypothesis stands as follows:

**INTERNALLY VALIDATED (within Arabic):**
- H2: Binary roots define semantic fields (>11σ)
- H5: Consonant order matters (p=0.014)
- H8: Position 1 carries most semantic weight (86%)
- H12: Meaning is 71.6% predictable from structure

**NOT YET VALIDATED (cross-linguistically):**
- Consonant correspondences exist empirically (3,461 alignments from gold pairs)
- BUT the discovery pipeline cannot distinguish them from random chance without semantic filtering
- Cross-linguistic claims require full-mode (embedding-based) validation

**This is honest science.** The internal Arabic structure IS real and measurable. Whether it extends to explain cross-family relationships remains an open question that requires semantic-filtered discovery runs.
