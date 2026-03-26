# Third Letter Modifier Profiles

**Scope:** consensus-based root predictions only (`consensus_weighted`, `consensus_strict`).

**Method:** aggregate each letter in third position across all roots, using the kept third-letter features, dropped third-letter features, dominant routing model, blended score, and nonzero rate.

## Headline

- This report describes how each Arabic letter behaves specifically as a third-letter modifier, not as an intrinsic letter meaning.
- `supportive` means the letter adds a stable modifier signature with good blended score and little blocked-feature pollution.
- `mixed` means the letter contributes real signal but still depends heavily on routing or generic features.
- `risky` means the letter often collapses into nucleus-only fallback or repeatedly triggers blocked/poison features.

## Summary Table

| Letter | Band | Mean blended | Nonzero rate | Dropped-feature row rate | Stable modifier signature | Shared blocked features |
|---|---|---:|---:|---:|---|---|
| ظ | supportive | 0.293 | 0.750 | 0.000 | ثخانة | — |
| غ | mixed | 0.286 | 0.825 | 0.175 | باطن | باطن |
| ش | mixed | 0.285 | 0.667 | 0.042 | انتشار, تخلخل | — |
| ص | mixed | 0.277 | 0.640 | 0.000 | ثخانة, خلوص | — |
| ج | supportive | 0.274 | 0.782 | 0.000 | اكتناز | — |
| ا | mixed | 0.250 | 0.500 | 0.000 | — | — |
| ي | mixed | 0.239 | 0.646 | 0.040 | — | — |
| ض | mixed | 0.237 | 0.703 | 0.000 | إمساك, ثخانة | — |
| ز | mixed | 0.234 | 0.769 | 0.000 | — | — |
| ذ | mixed | 0.231 | 0.750 | 0.125 | اختراق | — |
| ك | mixed | 0.229 | 0.705 | 0.013 | إمساك, اكتناز | — |
| ط | mixed | 0.223 | 0.682 | 0.023 | اتساع | — |
| ع | risky | 0.222 | 0.711 | 0.552 | ظاهر | ظاهر |
| هـ | mixed | 0.220 | 0.653 | 0.028 | خلوص | — |
| ق | mixed | 0.220 | 0.676 | 0.024 | ثقل | — |
| ن | mixed | 0.208 | 0.598 | 0.036 | انتقال, باطن | — |
| م | mixed | 0.201 | 0.632 | 0.050 | اكتناز | — |
| ف | mixed | 0.192 | 0.640 | 0.041 | اختراق | — |
| ر | risky | 0.191 | 0.688 | 0.998 | انتقال | التحام |
| خ | mixed | 0.190 | 0.542 | 0.000 | بروز, تخلخل, جفاف | — |
| د | mixed | 0.190 | 0.698 | 0.016 | إمساك, احتباس, ثقل | — |
| ء | mixed | 0.188 | 0.723 | 0.000 | انتقال, تأكيد | — |
| ث | mixed | 0.183 | 0.583 | 0.028 | انتشار | — |
| ب | risky | 0.182 | 0.699 | 1.000 | بروز, رجوع | التحام |
| ح | mixed | 0.182 | 0.726 | 0.081 | اتساع, باطن | باطن |
| و | mixed | 0.181 | 0.508 | 0.000 | — | — |
| ل | risky | 0.151 | 0.567 | 0.993 | امتداد | التحام |
| ت | risky | 0.144 | 0.509 | 0.091 | استقلال | استقلال |
| س | risky | 0.139 | 0.483 | 0.000 | امتداد, دقة | — |

## High-Level Findings

- Strongest third-letter enrichers in the current matrix: ج, ظ
- Riskiest third-letter modifiers in the current matrix: ب, ت, ر, س, ع, ل
- The repeated poison pattern is still `التحام` as a third-letter-only feature, especially with `ر`, `ل`, `ب`, and `ع`.
- Many letters route to `nucleus_only`, which means the nucleus still carries more of the signal than the modifier in a large share of roots.

## Per-Letter Profiles

### ء

- Band: `mixed`
- Mean blended score across consensus layers: `0.188`
- Nonzero rate across consensus layers: `0.723`
- Dropped-feature row rate: `0.000`
- Stable modifier signature: انتقال, تأكيد
- Shared blocked features: —

- `consensus_weighted`: mean `0.195`, nonzero `0.723`, quranic share `0.957`, feature precision `0.184`
- `consensus_weighted` dominant models: nucleus_only (18), phonetic_gestural (16), intersection (7)
- `consensus_weighted` top modifier features: إمساك (47), انتقال (47), تأكيد (47), تقوية (47)
- `consensus_weighted` blocked features: —
- `consensus_strict`: mean `0.181`, nonzero `0.723`, quranic share `0.957`, feature precision `0.167`
- `consensus_strict` dominant models: nucleus_only (21), phonetic_gestural (16), sequence (6)
- `consensus_strict` top modifier features: انتقال (47), تأكيد (47)
- `consensus_strict` blocked features: —

### ا

- Band: `mixed`
- Mean blended score across consensus layers: `0.250`
- Nonzero rate across consensus layers: `0.500`
- Dropped-feature row rate: `0.000`
- Stable modifier signature: —
- Shared blocked features: —

- `consensus_weighted`: mean `0.000`, nonzero `0.000`, quranic share `1.000`, feature precision `0.000`
- `consensus_weighted` dominant models: intersection (1)
- `consensus_weighted` top modifier features: ظاهر (1)
- `consensus_weighted` blocked features: —
- `consensus_strict`: mean `0.500`, nonzero `1.000`, quranic share `1.000`, feature precision `0.500`
- `consensus_strict` dominant models: sequence (1)
- `consensus_strict` top modifier features: —
- `consensus_strict` blocked features: —

### ب

- Band: `risky`
- Mean blended score across consensus layers: `0.182`
- Nonzero rate across consensus layers: `0.699`
- Dropped-feature row rate: `1.000`
- Stable modifier signature: بروز, رجوع
- Shared blocked features: التحام

- `consensus_weighted`: mean `0.197`, nonzero `0.715`, quranic share `0.878`, feature precision `0.215`
- `consensus_weighted` dominant models: nucleus_only (90), phonetic_gestural (18), intersection (14)
- `consensus_weighted` top modifier features: اكتناز (123), بروز (123), رجوع (123), رخاوة (106)
- `consensus_weighted` blocked features: التحام (123), رخاوة (17)
- `consensus_strict`: mean `0.167`, nonzero `0.683`, quranic share `0.878`, feature precision `0.184`
- `consensus_strict` dominant models: phonetic_gestural (77), nucleus_only (41), intersection (4)
- `consensus_strict` top modifier features: بروز (123), رجوع (123)
- `consensus_strict` blocked features: التحام (123)

### ت

- Band: `risky`
- Mean blended score across consensus layers: `0.144`
- Nonzero rate across consensus layers: `0.509`
- Dropped-feature row rate: `0.091`
- Stable modifier signature: استقلال
- Shared blocked features: استقلال

- `consensus_weighted`: mean `0.169`, nonzero `0.527`, quranic share `0.745`, feature precision `0.186`
- `consensus_weighted` dominant models: intersection (21), phonetic_gestural (17), nucleus_only (17)
- `consensus_weighted` top modifier features: إمساك (55), حدة (55), دقة (55), وحدة (55)
- `consensus_weighted` blocked features: استقلال (5)
- `consensus_strict`: mean `0.118`, nonzero `0.491`, quranic share `0.745`, feature precision `0.141`
- `consensus_strict` dominant models: phonetic_gestural (42), intersection (5), sequence (5)
- `consensus_strict` top modifier features: استقلال (50)
- `consensus_strict` blocked features: استقلال (5)

### ث

- Band: `mixed`
- Mean blended score across consensus layers: `0.183`
- Nonzero rate across consensus layers: `0.583`
- Dropped-feature row rate: `0.028`
- Stable modifier signature: انتشار
- Shared blocked features: —

- `consensus_weighted`: mean `0.188`, nonzero `0.583`, quranic share `0.778`, feature precision `0.218`
- `consensus_weighted` dominant models: nucleus_only (19), phonetic_gestural (11), intersection (5)
- `consensus_weighted` top modifier features: ثخانة (36), انتشار (35)
- `consensus_weighted` blocked features: انتشار (1)
- `consensus_strict`: mean `0.178`, nonzero `0.583`, quranic share `0.778`, feature precision `0.207`
- `consensus_strict` dominant models: phonetic_gestural (21), nucleus_only (8), intersection (5)
- `consensus_strict` top modifier features: انتشار (35)
- `consensus_strict` blocked features: انتشار (1)

### ج

- Band: `supportive`
- Mean blended score across consensus layers: `0.274`
- Nonzero rate across consensus layers: `0.782`
- Dropped-feature row rate: `0.000`
- Stable modifier signature: اكتناز
- Shared blocked features: —

- `consensus_weighted`: mean `0.271`, nonzero `0.769`, quranic share `0.744`, feature precision `0.291`
- `consensus_weighted` dominant models: phonetic_gestural (18), nucleus_only (16), intersection (5)
- `consensus_weighted` top modifier features: اكتناز (39), حدة (39)
- `consensus_weighted` blocked features: —
- `consensus_strict`: mean `0.277`, nonzero `0.795`, quranic share `0.744`, feature precision `0.273`
- `consensus_strict` dominant models: phonetic_gestural (24), nucleus_only (15)
- `consensus_strict` top modifier features: اكتناز (39)
- `consensus_strict` blocked features: —

### ح

- Band: `mixed`
- Mean blended score across consensus layers: `0.182`
- Nonzero rate across consensus layers: `0.726`
- Dropped-feature row rate: `0.081`
- Stable modifier signature: اتساع, باطن
- Shared blocked features: باطن

- `consensus_weighted`: mean `0.188`, nonzero `0.726`, quranic share `0.774`, feature precision `0.209`
- `consensus_weighted` dominant models: nucleus_only (29), intersection (19), phonetic_gestural (14)
- `consensus_weighted` top modifier features: احتكاك (62), جفاف (62), اتساع (61), باطن (57)
- `consensus_weighted` blocked features: باطن (5), اتساع (1)
- `consensus_strict`: mean `0.176`, nonzero `0.726`, quranic share `0.774`, feature precision `0.201`
- `consensus_strict` dominant models: phonetic_gestural (27), nucleus_only (22), intersection (12)
- `consensus_strict` top modifier features: اتساع (61), باطن (57)
- `consensus_strict` blocked features: باطن (5), اتساع (1)

### خ

- Band: `mixed`
- Mean blended score across consensus layers: `0.190`
- Nonzero rate across consensus layers: `0.542`
- Dropped-feature row rate: `0.000`
- Stable modifier signature: بروز, تخلخل, جفاف
- Shared blocked features: —

- `consensus_weighted`: mean `0.190`, nonzero `0.542`, quranic share `0.458`, feature precision `0.265`
- `consensus_weighted` dominant models: nucleus_only (18), intersection (3), phonetic_gestural (3)
- `consensus_weighted` top modifier features: بروز (24), تخلخل (24), ثخانة (24), جفاف (24)
- `consensus_weighted` blocked features: —
- `consensus_strict`: mean `0.190`, nonzero `0.542`, quranic share `0.458`, feature precision `0.265`
- `consensus_strict` dominant models: nucleus_only (18), intersection (3), phonetic_gestural (3)
- `consensus_strict` top modifier features: بروز (24), تخلخل (24), جفاف (24)
- `consensus_strict` blocked features: —

### د

- Band: `mixed`
- Mean blended score across consensus layers: `0.190`
- Nonzero rate across consensus layers: `0.698`
- Dropped-feature row rate: `0.016`
- Stable modifier signature: إمساك, احتباس, ثقل
- Shared blocked features: —

- `consensus_weighted`: mean `0.185`, nonzero `0.643`, quranic share `0.953`, feature precision `0.163`
- `consensus_weighted` dominant models: phonetic_gestural (49), intersection (40), nucleus_only (39)
- `consensus_weighted` top modifier features: إمساك (129), امتداد (129), ثقل (129), احتباس (127)
- `consensus_weighted` blocked features: احتباس (2)
- `consensus_strict`: mean `0.194`, nonzero `0.752`, quranic share `0.953`, feature precision `0.156`
- `consensus_strict` dominant models: phonetic_gestural (85), nucleus_only (31), intersection (12)
- `consensus_strict` top modifier features: إمساك (129), ثقل (129), احتباس (127)
- `consensus_strict` blocked features: احتباس (2)

### ذ

- Band: `mixed`
- Mean blended score across consensus layers: `0.231`
- Nonzero rate across consensus layers: `0.750`
- Dropped-feature row rate: `0.125`
- Stable modifier signature: اختراق
- Shared blocked features: —

- `consensus_weighted`: mean `0.238`, nonzero `0.750`, quranic share `0.600`, feature precision `0.240`
- `consensus_weighted` dominant models: nucleus_only (11), phonetic_gestural (8), intersection (1)
- `consensus_weighted` top modifier features: اختراق (20), ثخانة (20), رخاوة (15)
- `consensus_weighted` blocked features: رخاوة (5)
- `consensus_strict`: mean `0.224`, nonzero `0.750`, quranic share `0.600`, feature precision `0.222`
- `consensus_strict` dominant models: phonetic_gestural (14), nucleus_only (6)
- `consensus_strict` top modifier features: اختراق (20)
- `consensus_strict` blocked features: —

### ر

- Band: `risky`
- Mean blended score across consensus layers: `0.191`
- Nonzero rate across consensus layers: `0.688`
- Dropped-feature row rate: `0.998`
- Stable modifier signature: انتقال
- Shared blocked features: التحام

- `consensus_weighted`: mean `0.194`, nonzero `0.678`, quranic share `0.966`, feature precision `0.207`
- `consensus_weighted` dominant models: phonetic_gestural (113), nucleus_only (54), intersection (38)
- `consensus_weighted` top modifier features: استرسال (208), انتقال (208), باطن (194), التحام (1)
- `consensus_weighted` blocked features: التحام (207), باطن (14)
- `consensus_strict`: mean `0.188`, nonzero `0.697`, quranic share `0.966`, feature precision `0.197`
- `consensus_strict` dominant models: phonetic_gestural (139), nucleus_only (55), intersection (11)
- `consensus_strict` top modifier features: انتقال (208), التحام (1)
- `consensus_strict` blocked features: التحام (207)

### ز

- Band: `mixed`
- Mean blended score across consensus layers: `0.234`
- Nonzero rate across consensus layers: `0.769`
- Dropped-feature row rate: `0.000`
- Stable modifier signature: —
- Shared blocked features: —

- `consensus_weighted`: mean `0.240`, nonzero `0.821`, quranic share `0.692`, feature precision `0.322`
- `consensus_weighted` dominant models: phonetic_gestural (20), nucleus_only (16), intersection (3)
- `consensus_weighted` top modifier features: ازدحام (39), اكتناز (39)
- `consensus_weighted` blocked features: —
- `consensus_strict`: mean `0.228`, nonzero `0.718`, quranic share `0.692`, feature precision `0.360`
- `consensus_strict` dominant models: sequence (39)
- `consensus_strict` top modifier features: —
- `consensus_strict` blocked features: —

### س

- Band: `risky`
- Mean blended score across consensus layers: `0.139`
- Nonzero rate across consensus layers: `0.483`
- Dropped-feature row rate: `0.000`
- Stable modifier signature: امتداد, دقة
- Shared blocked features: —

- `consensus_weighted`: mean `0.140`, nonzero `0.483`, quranic share `0.900`, feature precision `0.159`
- `consensus_weighted` dominant models: nucleus_only (23), phonetic_gestural (19), intersection (18)
- `consensus_weighted` top modifier features: امتداد (60), حدة (60), دقة (60), وحدة (60)
- `consensus_weighted` blocked features: —
- `consensus_strict`: mean `0.137`, nonzero `0.483`, quranic share `0.900`, feature precision `0.153`
- `consensus_strict` dominant models: nucleus_only (22), phonetic_gestural (22), intersection (16)
- `consensus_strict` top modifier features: امتداد (60), دقة (60)
- `consensus_strict` blocked features: —

### ش

- Band: `mixed`
- Mean blended score across consensus layers: `0.285`
- Nonzero rate across consensus layers: `0.667`
- Dropped-feature row rate: `0.042`
- Stable modifier signature: انتشار, تخلخل
- Shared blocked features: —

- `consensus_weighted`: mean `0.300`, nonzero `0.667`, quranic share `0.542`, feature precision `0.522`
- `consensus_weighted` dominant models: intersection (11), phonetic_gestural (9), nucleus_only (4)
- `consensus_weighted` top modifier features: انتشار (24), دقة (24), تخلخل (23)
- `consensus_weighted` blocked features: تخلخل (1)
- `consensus_strict`: mean `0.270`, nonzero `0.667`, quranic share `0.542`, feature precision `0.522`
- `consensus_strict` dominant models: phonetic_gestural (12), intersection (11), nucleus_only (1)
- `consensus_strict` top modifier features: انتشار (24), تخلخل (23)
- `consensus_strict` blocked features: تخلخل (1)

### ص

- Band: `mixed`
- Mean blended score across consensus layers: `0.277`
- Nonzero rate across consensus layers: `0.640`
- Dropped-feature row rate: `0.000`
- Stable modifier signature: ثخانة, خلوص
- Shared blocked features: —

- `consensus_weighted`: mean `0.281`, nonzero `0.640`, quranic share `0.800`, feature precision `0.281`
- `consensus_weighted` dominant models: nucleus_only (17), intersection (5), phonetic_gestural (3)
- `consensus_weighted` top modifier features: اختراق (25), ثخانة (25), ثقل (25), خلوص (25)
- `consensus_weighted` blocked features: —
- `consensus_strict`: mean `0.274`, nonzero `0.640`, quranic share `0.800`, feature precision `0.276`
- `consensus_strict` dominant models: nucleus_only (15), intersection (5), phonetic_gestural (5)
- `consensus_strict` top modifier features: ثخانة (25), خلوص (25)
- `consensus_strict` blocked features: —

### ض

- Band: `mixed`
- Mean blended score across consensus layers: `0.237`
- Nonzero rate across consensus layers: `0.703`
- Dropped-feature row rate: `0.000`
- Stable modifier signature: إمساك, ثخانة
- Shared blocked features: —

- `consensus_weighted`: mean `0.237`, nonzero `0.703`, quranic share `0.838`, feature precision `0.204`
- `consensus_weighted` dominant models: nucleus_only (27), phonetic_gestural (10)
- `consensus_weighted` top modifier features: إمساك (37), ثخانة (37)
- `consensus_weighted` blocked features: —
- `consensus_strict`: mean `0.237`, nonzero `0.703`, quranic share `0.838`, feature precision `0.204`
- `consensus_strict` dominant models: nucleus_only (27), phonetic_gestural (10)
- `consensus_strict` top modifier features: إمساك (37), ثخانة (37)
- `consensus_strict` blocked features: —

### ط

- Band: `mixed`
- Mean blended score across consensus layers: `0.223`
- Nonzero rate across consensus layers: `0.682`
- Dropped-feature row rate: `0.023`
- Stable modifier signature: اتساع
- Shared blocked features: —

- `consensus_weighted`: mean `0.234`, nonzero `0.682`, quranic share `0.705`, feature precision `0.217`
- `consensus_weighted` dominant models: nucleus_only (29), phonetic_gestural (11), intersection (4)
- `consensus_weighted` top modifier features: إمساك (44), ثخانة (44), اتساع (43)
- `consensus_weighted` blocked features: اتساع (1)
- `consensus_strict`: mean `0.212`, nonzero `0.682`, quranic share `0.705`, feature precision `0.223`
- `consensus_strict` dominant models: phonetic_gestural (24), nucleus_only (19), sequence (1)
- `consensus_strict` top modifier features: اتساع (43)
- `consensus_strict` blocked features: اتساع (1)

### ظ

- Band: `supportive`
- Mean blended score across consensus layers: `0.293`
- Nonzero rate across consensus layers: `0.750`
- Dropped-feature row rate: `0.000`
- Stable modifier signature: ثخانة
- Shared blocked features: —

- `consensus_weighted`: mean `0.271`, nonzero `0.714`, quranic share `0.643`, feature precision `0.344`
- `consensus_weighted` dominant models: phonetic_gestural (7), nucleus_only (5), intersection (2)
- `consensus_weighted` top modifier features: اختراق (14), ثخانة (14), حدة (14)
- `consensus_weighted` blocked features: —
- `consensus_strict`: mean `0.315`, nonzero `0.786`, quranic share `0.643`, feature precision `0.316`
- `consensus_strict` dominant models: phonetic_gestural (11), nucleus_only (3)
- `consensus_strict` top modifier features: ثخانة (14)
- `consensus_strict` blocked features: —

### ع

- Band: `risky`
- Mean blended score across consensus layers: `0.222`
- Nonzero rate across consensus layers: `0.711`
- Dropped-feature row rate: `0.552`
- Stable modifier signature: ظاهر
- Shared blocked features: ظاهر

- `consensus_weighted`: mean `0.209`, nonzero `0.670`, quranic share `0.814`, feature precision `0.226`
- `consensus_weighted` dominant models: intersection (35), nucleus_only (33), phonetic_gestural (28)
- `consensus_weighted` top modifier features: حدة (97), دقة (97), ظاهر (87), رخاوة (85)
- `consensus_weighted` blocked features: التحام (97), رخاوة (12), ظاهر (10)
- `consensus_strict`: mean `0.235`, nonzero `0.753`, quranic share `0.814`, feature precision `0.255`
- `consensus_strict` dominant models: phonetic_gestural (63), nucleus_only (13), sequence (11)
- `consensus_strict` top modifier features: ظاهر (87)
- `consensus_strict` blocked features: ظاهر (10)

### غ

- Band: `mixed`
- Mean blended score across consensus layers: `0.286`
- Nonzero rate across consensus layers: `0.825`
- Dropped-feature row rate: `0.175`
- Stable modifier signature: باطن
- Shared blocked features: باطن

- `consensus_weighted`: mean `0.311`, nonzero `0.850`, quranic share `0.550`, feature precision `0.395`
- `consensus_weighted` dominant models: intersection (8), phonetic_gestural (6), nucleus_only (6)
- `consensus_weighted` top modifier features: تخلخل (20), ثخانة (20), باطن (18), رخاوة (16)
- `consensus_weighted` blocked features: رخاوة (4), باطن (2)
- `consensus_strict`: mean `0.260`, nonzero `0.800`, quranic share `0.550`, feature precision `0.327`
- `consensus_strict` dominant models: phonetic_gestural (16), sequence (2), intersection (2)
- `consensus_strict` top modifier features: باطن (18)
- `consensus_strict` blocked features: باطن (2)

### ف

- Band: `mixed`
- Mean blended score across consensus layers: `0.192`
- Nonzero rate across consensus layers: `0.640`
- Dropped-feature row rate: `0.041`
- Stable modifier signature: اختراق
- Shared blocked features: —

- `consensus_weighted`: mean `0.200`, nonzero `0.616`, quranic share `0.884`, feature precision `0.216`
- `consensus_weighted` dominant models: nucleus_only (49), phonetic_gestural (28), intersection (8)
- `consensus_weighted` top modifier features: اختراق (86), ثقل (86), طرد (86), إبعاد (79)
- `consensus_weighted` blocked features: إبعاد (7)
- `consensus_strict`: mean `0.184`, nonzero `0.663`, quranic share `0.884`, feature precision `0.188`
- `consensus_strict` dominant models: phonetic_gestural (61), nucleus_only (24), sequence (1)
- `consensus_strict` top modifier features: اختراق (86)
- `consensus_strict` blocked features: —

### ق

- Band: `mixed`
- Mean blended score across consensus layers: `0.220`
- Nonzero rate across consensus layers: `0.676`
- Dropped-feature row rate: `0.024`
- Stable modifier signature: ثقل
- Shared blocked features: —

- `consensus_weighted`: mean `0.216`, nonzero `0.694`, quranic share `0.847`, feature precision `0.184`
- `consensus_weighted` dominant models: phonetic_gestural (40), nucleus_only (33), intersection (11)
- `consensus_weighted` top modifier features: اشتداد (85), تعقد (85), ثقل (85), باطن (81)
- `consensus_weighted` blocked features: باطن (4)
- `consensus_strict`: mean `0.223`, nonzero `0.659`, quranic share `0.847`, feature precision `0.167`
- `consensus_strict` dominant models: phonetic_gestural (60), nucleus_only (24), sequence (1)
- `consensus_strict` top modifier features: ثقل (85)
- `consensus_strict` blocked features: —

### ك

- Band: `mixed`
- Mean blended score across consensus layers: `0.229`
- Nonzero rate across consensus layers: `0.705`
- Dropped-feature row rate: `0.013`
- Stable modifier signature: إمساك, اكتناز
- Shared blocked features: —

- `consensus_weighted`: mean `0.227`, nonzero `0.667`, quranic share `0.769`, feature precision `0.226`
- `consensus_weighted` dominant models: nucleus_only (21), intersection (9), phonetic_gestural (7)
- `consensus_weighted` top modifier features: إمساك (39), اكتناز (39), دقة (39), استقلال (38)
- `consensus_weighted` blocked features: استقلال (1)
- `consensus_strict`: mean `0.232`, nonzero `0.744`, quranic share `0.769`, feature precision `0.221`
- `consensus_strict` dominant models: nucleus_only (17), phonetic_gestural (16), intersection (4)
- `consensus_strict` top modifier features: إمساك (39), اكتناز (39)
- `consensus_strict` blocked features: —

### ل

- Band: `risky`
- Mean blended score across consensus layers: `0.151`
- Nonzero rate across consensus layers: `0.567`
- Dropped-feature row rate: `0.993`
- Stable modifier signature: امتداد
- Shared blocked features: التحام

- `consensus_weighted`: mean `0.141`, nonzero `0.549`, quranic share `0.986`, feature precision `0.148`
- `consensus_weighted` dominant models: phonetic_gestural (63), nucleus_only (40), intersection (32)
- `consensus_weighted` top modifier features: امتداد (142), تميز (142), استقلال (137), تعلق (136)
- `consensus_weighted` blocked features: التحام (141), تعلق (6), استقلال (5)
- `consensus_strict`: mean `0.160`, nonzero `0.585`, quranic share `0.986`, feature precision `0.192`
- `consensus_strict` dominant models: phonetic_gestural (73), nucleus_only (38), intersection (24)
- `consensus_strict` top modifier features: امتداد (142), التحام (1)
- `consensus_strict` blocked features: التحام (141)

### م

- Band: `mixed`
- Mean blended score across consensus layers: `0.201`
- Nonzero rate across consensus layers: `0.632`
- Dropped-feature row rate: `0.050`
- Stable modifier signature: اكتناز
- Shared blocked features: —

- `consensus_weighted`: mean `0.191`, nonzero `0.595`, quranic share `0.934`, feature precision `0.215`
- `consensus_weighted` dominant models: nucleus_only (55), phonetic_gestural (40), intersection (26)
- `consensus_weighted` top modifier features: إمساك (121), استواء (121), اكتناز (121), ظاهر (109)
- `consensus_weighted` blocked features: ظاهر (12)
- `consensus_strict`: mean `0.211`, nonzero `0.669`, quranic share `0.934`, feature precision `0.183`
- `consensus_strict` dominant models: phonetic_gestural (72), nucleus_only (48), intersection (1)
- `consensus_strict` top modifier features: اكتناز (121)
- `consensus_strict` blocked features: —

### ن

- Band: `mixed`
- Mean blended score across consensus layers: `0.208`
- Nonzero rate across consensus layers: `0.598`
- Dropped-feature row rate: `0.036`
- Stable modifier signature: انتقال, باطن
- Shared blocked features: —

- `consensus_weighted`: mean `0.213`, nonzero `0.580`, quranic share `0.875`, feature precision `0.241`
- `consensus_weighted` dominant models: intersection (43), nucleus_only (40), phonetic_gestural (26)
- `consensus_weighted` top modifier features: امتداد (112), انتقال (112), دقة (112), باطن (108)
- `consensus_weighted` blocked features: باطن (4)
- `consensus_strict`: mean `0.203`, nonzero `0.616`, quranic share `0.875`, feature precision `0.218`
- `consensus_strict` dominant models: phonetic_gestural (43), nucleus_only (39), intersection (27)
- `consensus_strict` top modifier features: انتقال (112), باطن (108)
- `consensus_strict` blocked features: باطن (4)

### هـ

- Band: `mixed`
- Mean blended score across consensus layers: `0.220`
- Nonzero rate across consensus layers: `0.653`
- Dropped-feature row rate: `0.028`
- Stable modifier signature: خلوص
- Shared blocked features: —

- `consensus_weighted`: mean `0.231`, nonzero `0.611`, quranic share `0.500`, feature precision `0.221`
- `consensus_weighted` dominant models: nucleus_only (25), intersection (6), phonetic_gestural (5)
- `consensus_weighted` top modifier features: إفراغ (36), خلوص (36), باطن (34)
- `consensus_weighted` blocked features: باطن (2)
- `consensus_strict`: mean `0.209`, nonzero `0.694`, quranic share `0.500`, feature precision `0.170`
- `consensus_strict` dominant models: intersection (18), phonetic_gestural (11), nucleus_only (7)
- `consensus_strict` top modifier features: خلوص (36)
- `consensus_strict` blocked features: —

### و

- Band: `mixed`
- Mean blended score across consensus layers: `0.181`
- Nonzero rate across consensus layers: `0.508`
- Dropped-feature row rate: `0.000`
- Stable modifier signature: —
- Shared blocked features: —

- `consensus_weighted`: mean `0.162`, nonzero `0.532`, quranic share `0.968`, feature precision `0.176`
- `consensus_weighted` dominant models: phonetic_gestural (31), nucleus_only (28), sequence (2)
- `consensus_weighted` top modifier features: احتواء (62)
- `consensus_weighted` blocked features: —
- `consensus_strict`: mean `0.200`, nonzero `0.484`, quranic share `0.968`, feature precision `0.231`
- `consensus_strict` dominant models: sequence (60), empty (2)
- `consensus_strict` top modifier features: —
- `consensus_strict` blocked features: —

### ي

- Band: `mixed`
- Mean blended score across consensus layers: `0.239`
- Nonzero rate across consensus layers: `0.646`
- Dropped-feature row rate: `0.040`
- Stable modifier signature: —
- Shared blocked features: —

- `consensus_weighted`: mean `0.231`, nonzero `0.672`, quranic share `1.000`, feature precision `0.248`
- `consensus_weighted` dominant models: nucleus_only (86), phonetic_gestural (28), intersection (19)
- `consensus_weighted` top modifier features: دقة (137), وحدة (137), اتصال (134), تخلخل (129)
- `consensus_weighted` blocked features: تخلخل (8), اتصال (3)
- `consensus_strict`: mean `0.248`, nonzero `0.620`, quranic share `1.000`, feature precision `0.310`
- `consensus_strict` dominant models: sequence (133), empty (4)
- `consensus_strict` top modifier features: —
- `consensus_strict` blocked features: —
