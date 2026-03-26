# Abbas Sensory Validation
**Date:** 2026-03-23
**Scope:** `S4.1` same-category sensory behavior, `S4.2` إيماء vs إيحاء mechanism split

## Inputs
- Abbas letter registry: `Juthoor-ArabicGenome-LV1/data/theory_canon/letters/hassan_abbas_letters.jsonl`
- Current nucleus score matrix: `outputs/lv1_scoring/nucleus_score_matrix.json`
- Rows analyzed: `1,484` Hassan Abbas nucleus/model rows with two recoverable Abbas letters

## S4.1 — Same-category vs mixed-category nuclei

Abbas sensory categories used:
- `لمسية`
- `ذوقية`
- `بصرية`
- `سمعية`
- `شعورية غير حلقية`
- `شعورية حلقية`

Headline result:
- same-category rows: `280`
- mixed-category rows: `1,204`
- same-category mean Jaccard: `0.0234`
- mixed-category mean Jaccard: `0.0311`
- same-category nonzero rows: `24/280` = `8.6%`
- mixed-category nonzero rows: `148/1204` = `12.3%`

Interpretation:
- In the current mechanical scoring, Abbas same-category nuclei do **not** outperform mixed-category nuclei.
- The gap is modest and only weakly directional against same-category grouping.
- Simple two-proportion z-test on nonzero rate: `z = -1.75`, `p ≈ 0.080`.
- So this pass does **not** support a strong same-category advantage.

Strongest sensory pair families in the current matrix:
- `ذوقية + لمسية`: mean Jaccard `0.0966`, nonzero rate `43.8%`
- `بصرية + ذوقية`: mean Jaccard `0.0569`, nonzero rate `30.4%`
- `بصرية + سمعية`: mean Jaccard `0.0542`, nonzero rate `18.8%`

Weakest pair families:
- `شعورية غير حلقية + لمسية`: mean Jaccard `0.0000`, nonzero rate `0.0%`
- `شعورية حلقية + شعورية غير حلقية`: mean Jaccard `0.0000`, nonzero rate `0.0%`

Takeaway:
- Abbas’s sensory grouping is not currently acting like a simple “same type composes better” law.
- If there is a real Abbas effect, it is more likely pair-specific than category-homogeneous.

## S4.2 — إيماء vs إيحاء mechanism split

Operational mapping used:
- `إيماء`: `ف، ل، م، ث، ذ`
- `إيحاء`: all other Abbas letters

This follows Abbas’s own historical split:
- older articulatory/imitative layer = `إيماء وتمثيل`
- later dominant expressive layer = `إيحاء`

Mechanism-pair results:

| Pair | Count | Mean Jaccard | Nonzero |
|------|-------|--------------|---------|
| `إيحاء + إيحاء` | `968` | `0.0319` | `122` |
| `إيحاء + إيماء` | `284` | `0.0277` | `29` |
| `إيماء + إيحاء` | `196` | `0.0268` | `21` |
| `إيماء + إيماء` | `36` | `0.0000` | `0` |

Statistical notes:
- same-mechanism vs mixed-mechanism nonzero rate difference is not significant in this pass:
  - `z = 0.98`, `p ≈ 0.329`
- but the fully `إيماء + إيماء` block is notably bad:
  - `0/36` nonzero
  - compared against all other Abbas rows: `z = -2.20`, `p ≈ 0.028`

Interpretation:
- Current evidence does **not** show that `إيماء` letters compose better gesturally.
- In fact, pure `إيماء + إيماء` combinations are the weakest Abbas segment in the current matrix.
- That cuts against a naive “gesture-heavy letters should score better” reading.

## Example high-scoring Abbas rows

Representative best rows in the current matrix:
- `خز` via `intersection`: predicted `["حدة"]`, actual `["نفاذ","حدة"]`, weighted `0.50`
- `رج` via `intersection`: predicted `["انتقال","احتكاك"]`, actual `["انتقال"]`, weighted `0.50`
- `زل` via `intersection`: predicted `["انتقال"]`, actual `["انتقال","استواء"]`, weighted `0.50`
- `كت` across several models: predicted `["اتصال"]`, actual `["اتصال","اشتمال"]`, weighted `0.50`

These examples suggest Abbas contributes best when his compressed sensory profile happens to intersect one dominant Jabal feature cleanly.

## Verdict

Current Phase 4 status:
- `S4.1`: completed
- `S4.2`: completed

What this means:
- Abbas’s categories are **not yet** a strong positive validation layer in the current LV1 mechanical scoring.
- The current matrix suggests:
  - mixed sensory pairs outperform same-category pairs
  - `إيحاء + إيحاء` outperforms all other mechanism pairings
  - `إيماء + إيماء` is currently the weakest block

Recommended next step for Claude in `S4.3`:
- treat Abbas as a **selective validation lens**, not a global scoring prior
- ask whether specific sensory pairings, not broad same-category grouping, predict model success
- compare these results against the improved root-level scoring reforms before drawing a stronger verdict
