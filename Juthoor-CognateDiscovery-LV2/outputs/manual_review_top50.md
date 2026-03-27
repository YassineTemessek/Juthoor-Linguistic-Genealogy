# Manual Review: Top 50 Discovery Leads

**Date:** 2026-03-27
**Source:** leads_improved_20260327_185229.jsonl (6,170 leads)
**Reviewer:** Claude Opus 4.6

## Summary

| Category | Count | % |
|----------|-------|---|
| False Positive | 46 | 92% |
| True (loanword/name) | 2 | 4% |
| Maybe (needs expert) | 2 | 4% |

## Key Findings

1. **92% false positive rate in top 50** — without semantic filtering, consonant pattern matching generates overwhelming noise
2. **Only 2 confirmed links:** حمد→Ahmed (Arabic name), possibly رب→Berber (Arabic بربر)
3. **Most false positives share consonant patterns but zero meaning relationship**
4. **Common FP patterns:**
   - اسْم (asm/name) matches anything with s-m: assam, assembler, caesium
   - رَحْمٰن (rahmān/merciful) matches anything with r-m: armor, armenia, archive
   - عالَم (ʿālam/world) matches anything with l-m: alimony, calm, calamity
5. **Guttural projection (ع→silent) fires excessively** because removing ع leaves common 2-letter skeletons

## Implications

- **Semantic filtering is the #1 priority** — consonant-only discovery is useless for precision
- Arabic entries MUST have English glosses for meaningful semantic comparison
- The concept matcher (concept_matcher.py) should catch indirect meanings
- Anchor classification alone doesn't help — 909 "gold" anchors include mostly false positives

## Detailed Review

### True Positives
- **حَمْد→ahmed**: Direct Arabic name from root حمد (praise). Score 1.00, direct_skeleton
- **رَبّ→berber**: Possibly from Arabic بربر (Berber peoples). Score 1.00, metathesis. Needs expert confirmation.

### Patterns to Flag as False Positives
- **Any proper noun** (place names, person names): assam, asmara, ahmed, babar, almaty, armenia
- **Latin-origin words** matching Arabic consonants: armor (arma), caesium (caesius), alimony (alimonia), calm (calma)
- **Short Arabic roots** (2-3 consonants) matching anything: اسْم/s-m matches hundreds of English words

## Recommendation for Next Run
1. Add English glosses to Arabic entries (Track 1)
2. Filter: phonetic_score ≥ 0.55 AND gloss_similarity ≥ 0.05
3. Flag proper nouns (capitalize detection)
4. Require minimum Arabic root length of 3 consonants for high-confidence matches
