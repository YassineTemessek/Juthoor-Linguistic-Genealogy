# LV1 Scoring Dashboard

Generated: 2026-03-26T17:24:53.056655+00:00

Single-page summary of the current LV1 nucleus and root scoring outputs.

## Overall Metrics

| Layer | Tests | Units | Mean J | Mean wJ | Mean bJ | Nonzero Rate |
| --- | --- | --- | --- | --- | --- | --- |
| Nucleus scoring | 11605 | 395 | 0.092 | 0.089 | - | 32.3% |
| Root scoring | 9620 | 1924 | 0.158 | 0.153 | 0.190 | 63.1% |

## Per-Scholar Breakdown

| Scholar | Nucleus Tests | Nucleus J | Nucleus wJ | Nucleus Nonzero | Root Tests | Root J | Root wJ | Root bJ | Root Nonzero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anbar | 1460 | 0.075 | 0.072 | 27.9% | - | - | - | - | - |
| asim_al_masri | 1975 | 0.053 | 0.052 | 19.3% | 1924 | 0.157 | 0.152 | 0.189 | 64.6% |
| consensus_strict | 1975 | 0.112 | 0.109 | 37.6% | 1924 | 0.159 | 0.153 | 0.191 | 62.6% |
| consensus_weighted | 1975 | 0.099 | 0.096 | 38.3% | 1924 | 0.165 | 0.160 | 0.197 | 63.2% |
| hassan_abbas | 1975 | 0.095 | 0.092 | 31.2% | 1924 | 0.150 | 0.145 | 0.183 | 61.9% |
| jabal | 1975 | 0.112 | 0.106 | 39.3% | 1924 | 0.161 | 0.156 | 0.193 | 63.1% |
| neili | 270 | 0.093 | 0.090 | 25.2% | - | - | - | - | - |

## Per-Model Breakdown

| Model | Nucleus Tests | Nucleus J | Nucleus wJ | Nucleus Nonzero | Root Tests | Root J | Root wJ | Root bJ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dialectical | 2321 | 0.103 | 0.099 | 43.1% | - | - | - | - |
| empty | - | - | - | - | 6 | 0.500 | 0.500 | 0.500 |
| intersection | 2321 | 0.082 | 0.079 | 23.3% | 1447 | 0.161 | 0.153 | 0.183 |
| nucleus_only | - | - | - | - | 3116 | 0.200 | 0.193 | 0.237 |
| phonetic_gestural | 2321 | 0.092 | 0.090 | 32.7% | 1594 | 0.163 | 0.161 | 0.194 |
| position_aware | 2321 | 0.084 | 0.082 | 24.8% | 3005 | 0.114 | 0.110 | 0.147 |
| sequence | 2321 | 0.096 | 0.093 | 37.7% | 452 | 0.139 | 0.134 | 0.167 |

## Quranic vs Non-Quranic Split

| Slice | Root Tests | Mean J | Mean wJ | Mean bJ | Nonzero bJ | Neili Valid |
| --- | --- | --- | --- | --- | --- | --- |
| Quranic | 0 | 0.000 | 0.000 | 0.000 | 0.0% | 0.0% |
| Non-Quranic | 9620 | 0.158 | 0.153 | 0.190 | 63.1% | 100.0% |

## Letter Correction Impact

This section measures the current footprint of the four corrected Jabal letters (م, ع, غ, ب) inside the root test set.

| Metric | Value |
| --- | --- |
| Affected Jabal root tests | 361 |
| Share of Jabal root tests | 18.8% |
| Affected-slice mean bJ | 0.195 |
| Overall Jabal mean bJ | 0.193 |
| Delta vs overall Jabal | 0.002 |

| Letter | Affected Tests | Mean bJ | Mean wJ | Nonzero bJ |
| --- | --- | --- | --- | --- |
| ب | 123 | 0.195 | 0.148 | 68.3% |
| ع | 97 | 0.201 | 0.167 | 68.0% |
| غ | 20 | 0.251 | 0.213 | 80.0% |
| م | 121 | 0.179 | 0.146 | 63.6% |

## Test Count

| Metric | Value |
| --- | --- |
| Nucleus row tests | 11605 |
| Unique binary roots scored | 395 |
| Root row tests | 9620 |
| Root tests per scholar | 1924 |
| Scholars included | 5 |
| Models included in root scoring | 6 |
| Models included in nucleus scoring | 5 |
