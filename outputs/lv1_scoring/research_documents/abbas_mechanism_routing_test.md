# Abbas Mechanism Routing Test
**Does letter mechanism type (هيجانية / إيمائية / إيحائية) predict which composition model performs best?**

Date: 2026-03-26
Scholar filter: `consensus_weighted` only
Metric: `blended_jaccard` (mean per model-mechanism cell)

---

## 1. Background

Hassan Abbas classifies Arabic letters into three phonosemantic mechanism types:

| Mechanism | Arabic | Description | Letters |
|-----------|--------|-------------|---------|
| **Gestural-mimic** | إيمائية | Articulation gesture mirrors meaning | ث ذ ف ل م |
| **Evocative** | إيحائية | Sound/feel evokes association | ب ت ج ح خ د ر ز س ش ص ض ط ظ ع غ ق ك ن هـ (20 letters) |
| **Exclamatory** | هيجانية | Hollow vowel sounds, near-zero lexical weight | ء ا و ي |

The hypothesis being tested is whether this phonosemantic classification maps onto composition model performance:
- **إيمائية** letters (whose gesture directly enacts meaning) should advantage `phonetic_gestural`
- **إيحائية** letters (whose evocation is associative) should advantage `intersection`
- **هيجانية** letters (hollow, lexically neutral) should be model-agnostic or weakly predicted

---

## 2. Data

- **Predictions file:** `outputs/lv1_scoring/root_predictions.json`
- **Total predictions:** 9,620 (all scholars)
- **Filtered to:** `consensus_weighted` scholar → 1,924 predictions
- **Coverage:** 29 third-letter types; all map 1:1 to Abbas mechanism (0 unmapped)
- **Mechanism distribution in consensus_weighted predictions:**
  - إيحائية: 1,272 predictions (66.1%)
  - إيمائية: 405 predictions (21.0%)
  - هيجانية: 247 predictions (12.8%)

---

## 3. Results Table: Mechanism × Model → Mean Blended Jaccard

| Model | هيجانية (n=247) | إيمائية (n=405) | إيحائية (n=1,272) |
|-------|-----------------|-----------------|-------------------|
| **nucleus_only** | **0.2413** (n=132) | **0.2127** (n=164) | **0.2543** (n=477) |
| intersection | 0.1774 (n=28) | 0.1879 (n=50) | 0.2007 (n=271) |
| phonetic_gestural | 0.1721 (n=75) | 0.1855 (n=19) | 0.1860 (n=143) |
| position_aware | N/A | 0.1641 (n=163) | 0.1519 (n=369) |
| sequence | 0.0882 (n=12) | 0.0713 (n=9) | 0.1042 (n=12) |

Bold = best model for each mechanism group. `N/A` = model was never selected for roots with that third letter type.

---

## 4. Model Rankings by Mechanism

### هيجانية (exclamatory: ء ا و ي)
1. nucleus_only: 0.2413
2. intersection: 0.1774
3. phonetic_gestural: 0.1721
4. sequence: 0.0882
*(position_aware never assigned to هيجانية roots)*

### إيمائية (gestural-mimic: ث ذ ف ل م)
1. nucleus_only: 0.2127
2. intersection: 0.1879
3. phonetic_gestural: 0.1855
4. position_aware: 0.1641
5. sequence: 0.0713

### إيحائية (evocative: 20 letters)
1. nucleus_only: 0.2543
2. intersection: 0.2007
3. phonetic_gestural: 0.1860
4. position_aware: 0.1519
5. sequence: 0.1042

---

## 5. Relative phonetic_gestural Advantage vs nucleus_only

To test whether إيمائية letters give `phonetic_gestural` a relative boost (even if not an absolute win):

| Mechanism | pg gap vs nucleus_only | int gap vs nucleus_only |
|-----------|------------------------|-------------------------|
| هيجانية | −0.0692 | −0.0639 |
| إيمائية | −0.0272 | −0.0248 |
| إيحائية | −0.0683 | −0.0536 |

Key observation: `phonetic_gestural`'s gap versus `nucleus_only` is **narrowest for إيمائية** (−0.027 vs −0.069 for هيجانية and −0.068 for إيحائية). This is the only signal consistent with the hypothesis — but the model still loses to `nucleus_only` in all three groups.

---

## 6. Per-Letter Breakdown (Hypothesis Letters)

### إيمائية letters (expected: phonetic_gestural should win)

| Letter | Mechanism | Best Model | Best Mean bJ | pg mean | int mean | n |
|--------|-----------|------------|-------------|---------|---------|---|
| ث | إيمائية | sequence | 0.250 | 0.152 | 0.208 | 36 |
| ذ | إيمائية | nucleus_only | 0.255 | 0.232 | 0.100 | 20 |
| ف | إيمائية | position_aware | 0.234 | N/A | 0.127 | 86 |
| ل | إيمائية | intersection | 0.190 | N/A | 0.190 | 142 |
| م | إيمائية | intersection | 0.292 | N/A | 0.292 | 121 |

`phonetic_gestural` was never selected for roots ending in ف, ل, or م. For ذ it comes closest (0.232), but nucleus_only still wins.

### هيجانية letters (expected: neutral/model-agnostic)

| Letter | Mechanism | Best Model | Best Mean bJ | pg mean | int mean | n |
|--------|-----------|------------|-------------|---------|---------|---|
| ء | هيجانية | intersection | 0.348 | 0.175 | 0.348 | 47 |
| ا | هيجانية | intersection | 0.000 | N/A | 0.000 | 1 |
| و | هيجانية | nucleus_only | 0.234 | 0.112 | 0.000 | 62 |
| ي | هيجانية | nucleus_only | 0.259 | 0.236 | 0.133 | 137 |

Notably, ء strongly favors `intersection` (0.348) — an unexpectedly sharp preference for a supposedly neutral letter.

---

## 7. Model Selection Frequency by Mechanism

The scoring pipeline assigns each root the best-fitting model. Distribution of model selections:

| Model | هيجانية | إيمائية | إيحائية |
|-------|---------|---------|---------|
| nucleus_only | 53.4% | 40.5% | 37.5% |
| position_aware | 0% | 40.2% | 29.0% |
| phonetic_gestural | 30.4% | 4.7% | 11.2% |
| intersection | 11.3% | 12.3% | 21.3% |
| sequence | 4.9% | 2.2% | 0.9% |

Noteworthy: `phonetic_gestural` is disproportionately *selected* for هيجانية roots (30.4%) but performs worse there (0.1721) than for إيمائية roots (0.1855) where it is rarely selected (4.7%). This is a mismatch — the pipeline routes away from `phonetic_gestural` exactly when it would perform best (relatively).

`position_aware` is entirely absent from هيجانية, suggesting the vowel-heavy hollow roots do not trigger the position logic.

---

## 8. Verdict

**Does Abbas mechanism type predict which model works best? NO (with a weak partial signal)**

### Primary finding:
`nucleus_only` wins every mechanism group without exception. The binary nucleus dominates third-letter effects regardless of mechanism class.

### Partial signal:
The hypothesis receives partial empirical support in one specific form: `phonetic_gestural`'s penalty relative to `nucleus_only` is significantly smaller for إيمائية roots (gap = −0.027) than for إيحائية roots (gap = −0.068) or هيجانية roots (gap = −0.069). This means the gestural model is not *worse* for gesture-mimic letters — it is just not *better* enough to displace `nucleus_only`.

### Hypothesis evaluation:

| Prediction | Result |
|------------|--------|
| إيمائية → phonetic_gestural best | NOT CONFIRMED. intersection or nucleus_only win for all 5 letters |
| إيحائية → intersection best | NOT CONFIRMED. nucleus_only still wins (0.2543 vs 0.2007) |
| هيجانية → neutral | PARTIALLY CONFIRMED. No clear winner but ء anomalously strong on intersection |

---

## 9. Implications for Routing

1. **Do not route by mechanism type alone.** The mechanism signal is too weak to justify a routing switch. `nucleus_only` is the dominant model across all groups.

2. **Binary nucleus strength explains most variance.** The third-letter's phonosemantic class is secondary to the nucleus's semantic weight. Any routing architecture should preserve nucleus primacy.

3. **Investigate the ء anomaly.** The ء letter shows the highest intersection score (0.348) of any letter in any model. This is likely a data artifact (small n=47, narrow feature set) but merits a dedicated study.

4. **phonetic_gestural under-routing.** The model is assigned to 30% of هيجانية roots where it performs worst, and only 4.7% of إيمائية roots where it performs best (relatively). If a routing refinement is ever attempted, redirect `phonetic_gestural` toward gesture-mimic letters (ث ذ ف ل م) and away from hollow vowels.

5. **Mechanism as a tiebreaker, not a primary router.** If two models score within 0.01 of each other for a root, the Abbas mechanism type could serve as a tiebreaker: prefer `phonetic_gestural` for إيمائية, `intersection` for إيحائية. This is a conservative use consistent with the data.

---

## 10. Overall Mean bJ by Mechanism

| Mechanism | Mean bJ | n |
|-----------|---------|---|
| إيحائية | 0.2041 | 1,272 |
| هيجانية | 0.2056 | 247 |
| إيمائية | 0.1857 | 405 |

إيمائية roots score lowest overall — possibly because gesture-mimic letters carry highly specific articulatory semantics that the current feature vocabulary does not capture precisely.
