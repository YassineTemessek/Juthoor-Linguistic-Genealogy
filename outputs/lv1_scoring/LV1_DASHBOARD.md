# LV1 Dashboard

Generated: 2026-03-26T17:52:20.703842+00:00

Clean summary of the current LV1 scoring outputs from `root_score_matrix.json` and `nucleus_score_matrix.json`.

## Overall Metrics

| Layer | Tests | Units | Scholars | Models | Mean J | Mean wJ | Mean bJ | Nonzero Rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Nucleus scoring | 11605 | 395 | 7 | 5 | 0.092 | 0.089 | - | 32.3% |
| Root scoring | 9620 | 1924 | 5 | 6 | 0.167 | 0.162 | 0.196 | 59.8% |

## Per-Scholar Breakdown

| Scholar | Nucleus Tests | Nucleus J | Nucleus wJ | Nucleus Nonzero | Root Tests | Root J | Root wJ | Root bJ | Root Nonzero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anbar | 1460 | 0.075 | 0.072 | 27.9% | - | - | - | - | - |
| asim_al_masri | 1975 | 0.053 | 0.052 | 19.3% | 1924 | 0.165 | 0.160 | 0.194 | 61.4% |
| consensus_strict | 1975 | 0.112 | 0.109 | 37.6% | 1924 | 0.170 | 0.164 | 0.198 | 59.5% |
| consensus_weighted | 1975 | 0.099 | 0.096 | 38.3% | 1924 | 0.172 | 0.167 | 0.200 | 59.8% |
| hassan_abbas | 1975 | 0.095 | 0.092 | 31.2% | 1924 | 0.161 | 0.156 | 0.190 | 58.9% |
| jabal | 1975 | 0.112 | 0.106 | 39.3% | 1924 | 0.167 | 0.161 | 0.195 | 59.4% |
| neili | 270 | 0.093 | 0.090 | 25.2% | - | - | - | - | - |

## Per-Model Breakdown

| Model | Nucleus Tests | Nucleus J | Nucleus wJ | Nucleus Nonzero | Root Tests | Root J | Root wJ | Root bJ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dialectical | 2321 | 0.103 | 0.099 | 43.1% | - | - | - | - |
| empty | - | - | - | - | 6 | 0.500 | 0.500 | 0.500 |
| intersection | 2321 | 0.082 | 0.079 | 23.3% | 1447 | 0.161 | 0.153 | 0.183 |
| nucleus_only | - | - | - | - | 3116 | 0.200 | 0.193 | 0.237 |
| phonetic_gestural | 2321 | 0.092 | 0.090 | 32.7% | 1594 | 0.163 | 0.161 | 0.194 |
| position_aware | 2321 | 0.084 | 0.082 | 24.8% | 3005 | 0.141 | 0.137 | 0.163 |
| sequence | 2321 | 0.096 | 0.093 | 37.7% | 452 | 0.139 | 0.134 | 0.167 |

## Quranic vs Non-Quranic Split

| Slice | Root Tests | Mean J | Mean wJ | Mean bJ | Nonzero bJ | Neili Valid |
| --- | --- | --- | --- | --- | --- | --- |
| Quranic | 0 | 0.000 | 0.000 | 0.000 | 0.0% | 0.0% |
| Non-Quranic | 9620 | 0.167 | 0.162 | 0.196 | 59.8% | 100.0% |

## Top 10 Best Roots

| Root | Scholar | Model | bJ | wJ | J | Bab | Quranic | Actual Features | Predicted Features |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| أبي | jabal | nucleus_only | 1.000 | 1.000 | 1.000 | الباء | Yes | تلاصق + احتباس | تلاصق + احتباس |
| أوب-أيب | jabal | nucleus_only | 1.000 | 1.000 | 1.000 | الباء | Yes | رجوع + استقرار | رجوع + استقرار |
| يبس | jabal | nucleus_only | 1.000 | 1.000 | 1.000 | الباء | Yes | جفاف | جفاف |
| بشر | jabal | position_aware | 1.000 | 1.000 | 1.000 | الباء | Yes | انتشار + ظاهر | انتشار + ظاهر |
| وتد | jabal | nucleus_only | 1.000 | 1.000 | 1.000 | التاء | Yes | امتساك + تماسك | امتساك + تماسك |
| تلو-تلي | jabal | intersection | 1.000 | 1.000 | 1.000 | التاء | Yes | اتصال | اتصال |
| تمم | jabal | position_aware | 1.000 | 1.000 | 1.000 | التاء | Yes | تميز | تميز |
| تيهـ-توهـ | jabal | intersection | 1.000 | 1.000 | 1.000 | التاء | Yes | فراغ | فراغ |
| جوع | jabal | nucleus_only | 1.000 | 1.000 | 1.000 | الجيم | Yes | فراغ + جوف | جوف + فراغ |
| حثث-حثحث | jabal | nucleus_only | 1.000 | 1.000 | 1.000 | الحاء | Yes | تخلخل + قطع + جفاف | تخلخل + قطع + جفاف |

## Top 10 Worst Roots

| Root | Scholar | Model | bJ | wJ | J | Bab | Quranic | Actual Features | Predicted Features |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| أبو | jabal | nucleus_only | 0.000 | 0.000 | 0.000 | الباء | Yes | - | تلاصق + احتباس |
| بيت | jabal | intersection | 0.000 | 0.000 | 0.000 | الباء | Yes | حيز | قطع |
| بحح-بحبح | jabal | position_aware | 0.000 | 0.000 | 0.000 | الباء | No | فراغ | ظهور |
| بحث | jabal | nucleus_only | 0.000 | 0.000 | 0.000 | الباء | Yes | تماسك + تفرق | ظهور + فراغ |
| بحر | jabal | nucleus_only | 0.060 | 0.000 | 0.000 | الباء | Yes | شق + فجوة + قوة + باطن + انتقال | ظهور + فراغ |
| بخخ-بخبخ | jabal | nucleus_only | 0.000 | 0.000 | 0.000 | الباء | No | قوة + ظاهر + تخلخل + غلظ | نقص + فراغ |
| بخل | jabal | position_aware | 0.000 | 0.000 | 0.000 | الباء | Yes | إمساك | نقص + فراغ |
| بدد-بدبد | jabal | nucleus_only | 0.000 | 0.000 | 0.000 | الباء | No | تفرق + إبعاد + فراغ | ظهور |
| بدو | jabal | phonetic_gestural | 0.000 | 0.000 | 0.000 | الباء | Yes | بروز + قوة + امتداد + اتساع | ظهور + اشتمال |
| أبد | jabal | nucleus_only | 0.000 | 0.000 | 0.000 | الباء | Yes | امتداد | ظهور |

## Test Count

| Metric | Value |
| --- | --- |
| Requested test count | 495 |
| Nucleus row tests | 11605 |
| Unique binary roots in nucleus matrix | 395 |
| Root row tests | 9620 |
| Root tests per scholar | 1924 |
