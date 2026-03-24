# A.1 Feature Vocab Gap Report
Date: 2026-03-24

## Purpose
Audit high-frequency unrecognized tokens in Jabal's `jabal_axial_meaning` so vocabulary expansion targets real semantic gaps rather than random Arabic glue words.

## Main Finding
Most misses were not unknown theory concepts. They clustered into:

- modulation/intensity: `صلابة`, `جلادة`, `نصاعة`, `غزارة`, `امتلاء`
- closure/blockage: `انسداد`
- emission/overflow: `فوران`, `فيض`, `نضح`, `تسرب`
- location/stability: `فجوة`, `استقرار`, `مقر`
- motion refinement: `رجوع`, `اندفاع`
- cutting/fracture: `شق`, `كسر`, `سحق`

The top raw unmatched tokens also contained a lot of low-value noise:

- prepositional/context words: `إلى`, `على`, `منه`, `فيه`, `حتى`
- generic substance nouns: `جرم`, `مادة`
- descriptive wrappers: `شديد`, `لطيف`, `غليظ`

## Representative Frequent Misses

| Token | Count | Example |
|---|---:|---|
| `اثناء` | 109 | `تفتق أثناء الشيء أو تفتحه واتساعه` |
| `جرم` | 70 | `فجوة عظيمة في جرم شديد` |
| `امتلاء` | 21 | `امتلاء باطن الشيء بلطيف يصلحه` |
| `تسيب` | 21 | `تسيب الدقاق الجافة بتسريب مائع بينها` |
| `اندفاع` | 19 | `اندفاع الشيء نافذًا أو ممتدًا من عمقه` |
| `ارتفاع` | 19 | `ارتفاع أو نتوء محدود مع تجمع جرم` |
| `صلابه` | 21 | `اندفاع مع صلابة في الشيء المجتمع` |
| `نصاعة` | 17+ | `ينضح على الظاهر نصاعة أو رقة` |

## A.2 Expansion Applied

Added direct features:

- `انسداد`
- `رجوع`
- `اندفاع`
- `تسرب`
- `امتلاء`
- `غزارة`
- `فوران`
- `فيض`
- `نضح`
- `صلابة`
- `جلادة`
- `نصاعة`
- `شق`
- `كسر`
- `سحق`
- `فجوة`
- `استقرار`
- `مقر`

Also expanded bounded aliases around:

- `بقوة / وقوة`
- `باطنه / الباطن / الظاهر / ظاهره`
- `مقره / مستقر / الاستقرار`
- `فجوة / الفجوة`

## A.3-A.5 Result

After rebuild:

- roots: `1924`
- empty actual roots: `107`
- mean actual features per root: `2.5333`
- median actual features per root: `2`

Comparison to the pre-expansion state:

- empty actual roots improved: `113 -> 107`
- coverage improved slightly
- scoring did **not** improve proportionally because the target meanings became richer faster than the current prediction models

Current scholar-by-root means after the rebuild:

- `consensus_strict`: blended `0.183079`
- `consensus_weighted`: blended `0.175488`
- `hassan_abbas`: blended `0.173994`
- `jabal`: blended `0.170509`
- `asim_al_masri`: blended `0.169197`

## Verdict

This expansion was useful for coverage, but it is not the whole fix.

The next gains are more likely to come from:

1. `B.2` semantic compatibility filtering
2. `B.3` nucleus-only fallback
3. Yassin's decisions on the 8 diverging letters

Vocabulary expansion alone is helping, but with diminishing returns.
