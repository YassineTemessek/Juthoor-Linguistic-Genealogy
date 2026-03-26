# LV1 Dashboard

Generated: 2026-03-26T18:48:10.102179+00:00

Clean summary of the current LV1 scoring outputs from `root_score_matrix.json` and `nucleus_score_matrix.json`.

## Overall Metrics

| Layer | Tests | Units | Scholars | Models | Mean J | Mean wJ | Mean bJ | Nonzero Rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Nucleus scoring | 11605 | 395 | 7 | 5 | 0.089 | 0.086 | - | 31.2% |
| Root scoring | 9620 | 1924 | 5 | 6 | 0.177 | 0.172 | 0.208 | 62.5% |

## Per-Scholar Breakdown

| Scholar | Nucleus Tests | Nucleus J | Nucleus wJ | Nucleus Nonzero | Root Tests | Root J | Root wJ | Root bJ | Root Nonzero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anbar | 1460 | 0.073 | 0.069 | 26.8% | - | - | - | - | - |
| asim_al_masri | 1975 | 0.052 | 0.052 | 18.8% | 1924 | 0.176 | 0.171 | 0.206 | 64.0% |
| consensus_strict | 1975 | 0.106 | 0.104 | 35.5% | 1924 | 0.182 | 0.176 | 0.213 | 62.8% |
| consensus_weighted | 1975 | 0.098 | 0.095 | 37.9% | 1924 | 0.180 | 0.175 | 0.210 | 62.1% |
| hassan_abbas | 1975 | 0.092 | 0.089 | 29.7% | 1924 | 0.174 | 0.168 | 0.205 | 62.2% |
| jabal | 1975 | 0.107 | 0.101 | 38.3% | 1924 | 0.174 | 0.169 | 0.204 | 61.6% |
| neili | 270 | 0.089 | 0.085 | 23.3% | - | - | - | - | - |

## Per-Model Breakdown

| Model | Nucleus Tests | Nucleus J | Nucleus wJ | Nucleus Nonzero | Root Tests | Root J | Root wJ | Root bJ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dialectical | 2321 | 0.103 | 0.099 | 43.1% | - | - | - | - |
| empty | - | - | - | - | 6 | 0.500 | 0.500 | 0.500 |
| intersection | 2321 | 0.082 | 0.079 | 23.3% | 1447 | 0.161 | 0.153 | 0.183 |
| nucleus_only | - | - | - | - | 5785 | 0.182 | 0.177 | 0.213 |
| phonetic_gestural | 2321 | 0.092 | 0.090 | 32.7% | 1594 | 0.163 | 0.161 | 0.194 |
| position_aware | 2321 | 0.070 | 0.067 | 19.1% | 336 | 0.277 | 0.264 | 0.325 |
| sequence | 2321 | 0.096 | 0.093 | 37.7% | 452 | 0.139 | 0.134 | 0.167 |

## Quranic vs Non-Quranic Split

| Slice | Root Tests | Mean J | Mean wJ | Mean bJ | Nonzero bJ | Neili Valid |
| --- | --- | --- | --- | --- | --- | --- |
| Quranic | 0 | 0.000 | 0.000 | 0.000 | 0.0% | 0.0% |
| Non-Quranic | 9620 | 0.177 | 0.172 | 0.208 | 62.5% | 100.0% |

## Top 10 Best Roots

| Root | Scholar | Model | bJ | wJ | J | Bab | Quranic | Actual Features | Predicted Features |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| أبي | jabal | nucleus_only | 1.000 | 1.000 | 1.000 | الباء | Yes | تلاصق + احتباس | تلاصق + احتباس |
| أوب-أيب | jabal | nucleus_only | 1.000 | 1.000 | 1.000 | الباء | Yes | رجوع + استقرار | رجوع + استقرار |
| يبس | jabal | nucleus_only | 1.000 | 1.000 | 1.000 | الباء | Yes | جفاف | جفاف |
| بشر | jabal | nucleus_only | 1.000 | 1.000 | 1.000 | الباء | Yes | انتشار + ظاهر | انتشار + ظاهر |
| وتد | jabal | nucleus_only | 1.000 | 1.000 | 1.000 | التاء | Yes | امتساك + تماسك | امتساك + تماسك |
| تلو-تلي | jabal | intersection | 1.000 | 1.000 | 1.000 | التاء | Yes | اتصال | اتصال |
| تمم | jabal | nucleus_only | 1.000 | 1.000 | 1.000 | التاء | Yes | تميز | تميز |
| تيهـ-توهـ | jabal | intersection | 1.000 | 1.000 | 1.000 | التاء | Yes | فراغ | فراغ |
| جوع | jabal | nucleus_only | 1.000 | 1.000 | 1.000 | الجيم | Yes | فراغ + جوف | جوف + فراغ |
| حثث-حثحث | jabal | nucleus_only | 1.000 | 1.000 | 1.000 | الحاء | Yes | تخلخل + قطع + جفاف | تخلخل + قطع + جفاف |

## Top 10 Worst Roots

| Root | Scholar | Model | bJ | wJ | J | Bab | Quranic | Actual Features | Predicted Features |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| أبو | jabal | nucleus_only | 0.000 | 0.000 | 0.000 | الباء | Yes | - | تلاصق + احتباس |
| بيت | jabal | intersection | 0.000 | 0.000 | 0.000 | الباء | Yes | حيز | قطع |
| بحث | jabal | nucleus_only | 0.000 | 0.000 | 0.000 | الباء | Yes | تماسك + تفرق | ظهور + فراغ |
| بحر | jabal | nucleus_only | 0.060 | 0.000 | 0.000 | الباء | Yes | شق + فجوة + قوة + باطن + انتقال | ظهور + فراغ |
| بخخ-بخبخ | jabal | nucleus_only | 0.000 | 0.000 | 0.000 | الباء | No | قوة + ظاهر + تخلخل + غلظ | نقص + فراغ |
| بخل | jabal | nucleus_only | 0.000 | 0.000 | 0.000 | الباء | Yes | إمساك | نقص + فراغ |
| بدد-بدبد | jabal | nucleus_only | 0.000 | 0.000 | 0.000 | الباء | No | تفرق + إبعاد + فراغ | ظهور |
| بدو | jabal | phonetic_gestural | 0.000 | 0.000 | 0.000 | الباء | Yes | بروز + قوة + امتداد + اتساع | ظهور + اشتمال |
| أبد | jabal | nucleus_only | 0.000 | 0.000 | 0.000 | الباء | Yes | امتداد | ظهور |
| بدر | jabal | nucleus_only | 0.000 | 0.000 | 0.000 | الباء | Yes | امتداد | ظهور |

## Test Count

| Metric | Value |
| --- | --- |
| Requested test count | 495 |
| Nucleus row tests | 11605 |
| Unique binary roots in nucleus matrix | 395 |
| Root row tests | 9620 |
| Root tests per scholar | 1924 |
