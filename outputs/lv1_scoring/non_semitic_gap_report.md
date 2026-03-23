# Non-Semitic Gap Report

Date: 2026-03-23
Scope: Arabic-English benchmark rows after `S6.5`

## Summary

- Total matched English rows: `18`
- Exact hits: `3`
- Binary-prefix-only hits: `4`
- Remaining unmatched rows: `11`

The current English slice is no longer mainly blocked by missing Arabic roots. After the `S6.5` cleanup, the remaining misses split into three narrower categories:

1. Sound-law coverage is still too weak for some obvious consonant correspondences.
2. Several English targets are morphologically longer than the current projection scorer expects.
3. A few rows are semantically plausible but benchmark-noisy, so consonant projection alone is unlikely to produce exact matches.

## Binary-Prefix-Only Rows

These rows now show structural signal, but not exact projected forms:

| Arabic | Root | English | Best variant | Similarity | Likely issue |
|---|---|---|---|---:|---|
| برج | برج | burglar | `brglr` | 0.75 | English derivational length exceeds current direct-form matching |
| فاه | فوهـ | famous | `fms` | 0.80 | Vowel/derivational compression; consonants align better than full form |
| باص | بصص/بصبص | bus | `bus` | 0.67 | Compound-root projection generates good prefix signal but too many expanded forms |
| نفس | نفس | inspire | `nspr` | 0.67 | Semantic/derivational drift; prefix alignment without direct lexical identity |

## Remaining Unmatched Rows

| Arabic | Root | English | Best variant | Similarity | Likely issue |
|---|---|---|---|---:|---|
| أرض | أرض | earth | `eart` | 0.57 | English target keeps final `th`; current mapping lands near-match only |
| ثور | ثور | steer | `str` | 0.80 | Missing vowel/length mediation between `swr`-like outputs and `steer` |
| قرن | قرن | horn | `hrn` | 0.67 | Initial consonant loss / reshaping not modeled directly |
| رقّ | رقق-رقرق | rack | `rck` | 0.67 | Compound-root projections are now found, but scorer still lacks exact collapse to `rack` |
| بنصر | بصر | finger | `fngr` | 0.57 | Multi-step shift plus derivational growth; current scorer undercounts this class |
| آدم | أدم | human | `hmn` | 0.67 | Relation is semantic-historical, not a clean consonantal exact match |
| كرّار | كرر-كركر | garage | `grg` | 0.44 | Weak benchmark row for exact projection; likely too distant for current model |
| عمّ | عمم | uncle | `uncle` | 0.33 | Benchmark relation is lexical, not recoverable by consonant projection alone |
| قطين | قطن | chain | `cn` | 0.80 | Strong prefix resemblance but different lexical growth path |
| قناة | قنو-قنى | canyon | `cn` | 0.67 | Same issue: strong reduced prefix, weak direct-form identity |
| دنّ | دنن-دندن | tunnel | `tnl` | 0.67 | Good reduced path, but extra consonantal development not modeled |

## Interpretation

- The English slice now has enough coverage to be diagnostically useful.
- The remaining misses are no longer mostly data-loading failures.
- The next gain will not come from more root hint curation alone.
- The next gain should come from one of two directions:
  - better reduced-form English comparison for longer derivations like `burglar`, `famous`, `finger`, `tunnel`
  - or explicit benchmark partitioning into:
    - direct consonant-projection rows
    - semantic/historical rows that are not fair exact-match targets

## Recommendation

Do not keep inflating the English benchmark blindly.

Next useful task:
1. Partition the English slice into `direct_projection` vs `historical_semantic` rows.
2. Score direct rows mechanically as before.
3. Treat historical/semantic rows as qualitative support, not exact-hit failures.

This should make the non-Semitic baseline more honest without weakening the Semitic result.
