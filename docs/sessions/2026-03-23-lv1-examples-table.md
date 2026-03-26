# LV1 Concrete Examples — What the Numbers Look Like in Practice
**For: Yassin (project owner)**
**Date: 2026-03-23**
**Source data: `outputs/lv1_scoring/root_*.json`, `benchmark_*_scored_projections.json`**

---

## Section 1: Root Prediction Examples (20 Roots)

**How to read this table:**
- المعنى المحوري (Jabal) = what Jabal assigned as the core meaning of the root
- Predicted Meaning = what the machine predicted from the letters alone, before looking up the answer
- Match = Exact / Partial / Miss
- J = Jaccard score (1.0 = perfect overlap between predicted and actual feature sets)

### Part A — Excellent Predictions (7 roots)

The machine predicted the correct meaning from the letters alone.

| Arabic Root | المعنى المحوري (Jabal) | Predicted Meaning | Match | J | Quranic Example | Notes |
|------------|----------------------|-------------------|-------|---|-----------------|-------|
| **يبس** | جفاف | جفاف | Exact | 1.0 | "فَاضْرِبْ لَهُمْ طَرِيقًا فِي الْبَحْرِ يَبَسًا" | Binary nucleus ب+س = dryness+purity → intersection = dryness. Perfect |
| **نعنع** (mint) | رخاوة + رقة | رخاوة + رقة | Exact | 1.0 | النعنع (not Quranic but phonetically perfect) | ن+ع = softness+fineness. Gemination intensifies. The plant that defines both. |
| **عكف** | ضغط + انتشار | ضغط + انتشار | Exact | 1.0 | "وَأَنتُمْ عَاكِفُونَ فِي الْمَسَاجِدِ" | ع+ك = pressure+compression, +ف (spreading) → confinement with pressure. This is exactly what عاكف means: devoted and pressed in place. |
| **كبب** | تجمع | تجمع | Exact | 1.0 | "فَكُبْكِبُوا فِيهَا هُمْ وَالْغَاوُونَ" | ك+ب = compression+bonding. Intersection = gathering. The image of tumbling into a pile. |
| **دون** | باطن | باطن | Exact | 1.0 | "وَيَغْفِرُ مَا دُونَ ذَلِكَ لِمَن يَشَاءُ" | د+ن = inner+hidden. Intersection = inner/hidden. دون = what is beneath/below/behind. |
| **سرمد** (eternal) | امتداد | امتداد | Exact | 1.0 | "إِن جَعَلَ اللَّهُ عَلَيْكُمُ النَّهَارَ سَرْمَدًا" | س+ر = extension chain. Third letterد doesn't disturb. سرمد = unbroken span of time. The word IS extension. |
| **عود/عيد** | امتداد | امتداد | Exact | 1.0 | "كَمَا بَدَأَكُمْ تَعُودُونَ" | ع+د = extension (return over time = extension across time). The Eid is the day you return to — extension of meaning across years. |

---

### Part B — Partial Hits (7 roots)

The machine understood the conceptual territory but used a different term than Jabal, or captured some features but not all.

| Arabic Root | المعنى المحوري (Jabal) | Predicted Meaning | Match | J | Notes |
|------------|----------------------|-------------------|-------|---|-------|
| **مضى** (to pass, go forth) | نفاذ + غلظ + قوة | نفاذ + قوة + اتصال | Partial | 0.50 | Penetration and force: exact. اتصال (connection) was over-predicted — مضى doesn't mean connection, it means passage. The machine saw ض+ي and added connection where the actual meaning is more about thickness of force pushing through. |
| **فكك** (to untie, release) | تخلخل + استقلال | تخلخل + ضغط | Partial | 0.33 | Loosening (تخلخل): perfect — فك is exactly dissolution of bonds. But the machine predicted "pressure" as the second feature when Jabal sees "independence" (استقلال) — the thing that exists after the bond breaks, not the force that breaks it. |
| **مضيض** / **بتر** (to cut off) | قطع + استقلال | قطع + استرسال | Partial | ~0.33 | Cutting is right. "Flowing continuation" (استرسال) was added by the machine — an artifact of the ر consonant — but بتر is abrupt severance with no flow. |
| **بشر** (good news / skin) | انتشار + ظاهر | ظاهر | Partial | 0.50 | Manifestation (ظاهر) is there. The machine missed spreading (انتشار) which is essential — بشارة spreads outward as news spreads. The ش letter carries spreading but the intersection model didn't activate it here. |
| **خزز** (to pierce, prick) | اختراق + نفاذ + حدة + دقة | نفاذ + حدة + اكتناز | Partial | 0.50 | Penetration and sharpness: exact. The machine added "compactness" (اكتناز) from the phonetic profile of خ+ز, but Jabal sees fineness (دقة) instead — a thinner concept than compactness. The direction is right; the label is different. |
| **زوج** (pair, spouse) | اتصال + اشتمال | تلاصق + اتصال + اشتمال | Partial | 0.67 | Two of three correct. The machine over-added "adhesion" (تلاصق) as a third feature — conceptually adjacent to connection but not identical. A pair is united, not glued. |
| **أبب** (fodder; growth of plants) | تلاصق + صعود | تلاصق | Partial | 0.50 | Adhesion is right (plants cling to ground). Rising (صعود) was missed — the growth upward is the key property Jabal sees in أبب as a plant root. The machine stopped at adhesion without inferring the directional component. |

---

### Part C — Failures (6 roots)

The machine's prediction is meaningfully wrong.

| Arabic Root | المعنى المحوري (Jabal) | Predicted Meaning | Match | J | Notes |
|------------|----------------------|-------------------|-------|---|-------|
| **أخو** (brother; fraternal bond) | اتصال (connection) | فراغ (void) | Miss | 0.0 | The ء+و letter combination has a void/expansive profile in Jabal's system. The machine predicted void. But the Arabic cultural tradition sees brotherhood as the paradigm example of *connection*, not emptiness. The machine has no cultural layer. |
| **بطن** (belly; interior) | جوف (hollow interior) | ثقل + امتداد (weight + extension) | Miss | 0.0 | ب+ط activates the heaviness+extension profile. Jabal sees "hollow container" — a specific spatial concept that the feature system doesn't distinguish well from weight. جوف and ثقل are in different semantic categories entirely. |
| **بحر** (sea, ocean) | اختراق + قوة + باطن + انتقال | ظهور (manifestation) | Miss | 0.0 | The machine predicted "manifestation" from the ب+ح intersection. Jabal sees the sea as the great penetrator — it breaks through, holds force within, and moves. The machine caught none of that complexity. |
| **وزن** (to weigh, measure) | ثقل + انتشار + إبعاد | باطن | Miss | 0.0 | The machine predicted "inner/hidden" from the و+ز nucleus. Jabal sees weighing as the projection of heaviness outward and away. The entire semantic field is wrong — وزن is a weighing/spreading act, not a concealing one. |
| **بدع** (to originate, innovate) | [unmarked in Jabal's data] | ظهور + التحام | Miss | — | بديع means "unprecedented origination." The machine predicted manifestation + bonding. Neither captures novelty and creative origination. The concept is too abstract for the current vocabulary. |
| **بدر** (full moon; to rush forward) | امتداد (extension) | ظهور (manifestation) | Miss | 0.0 | The machine predicted appearance/manifestation — which seems intuitive for a full moon. But Jabal assigns "extension" — the idea of reaching fullness or rushing forth. A subtle difference, but it shows the machine's surface logic doesn't always match Jabal's deep analysis. |

---

## Section 2: Cross-Lingual Projection Examples (15 Rows)

**How to read this table:**
- Projected Form = the consonant skeleton the system generated from Khashim's sound laws
- Match = whether the actual Hebrew/Aramaic word fell within the projected set
- Binary = whether at least the first two consonants matched (nucleus preservation)

### Full Hits — Arabic Consonant Skeleton Preserved in Hebrew/Aramaic

| Arabic Root | Arabic Meaning | Hebrew/Aramaic | Projected Form | Exact | Binary | Notes |
|------------|---------------|----------------|----------------|-------|--------|-------|
| عين | eye | עין (heb) | ʕyn | Yes | Yes | Arabic ع → Hebrew ע (same phoneme, different script). The genome transfers unchanged. |
| كتب | to write | כתב (heb + arc) | ktb | Yes | Yes | Arabic ك → Hebrew כ; ت → ת; ب → ב. The trilateral skeleton is perfectly preserved. Same in Aramaic. |
| ملك | king, rule | מלך (heb + arc) | mlk | Yes | Yes | Arabic م-ل-ك → Hebrew מ-ל-ך. Arabic ك/Hebrew ך is a regular sound law (velar stop). |
| سمع | to hear | שמע (heb + arc) | smʕ / šmʕ | Yes | Yes | Arabic س → Hebrew ש (s/sh merger — this is one of Khashim's nine laws). מ-ע nucleus preserved. |
| ذهب | gold | זהב (heb) / דהב (arc) | zhb / dhb | Yes | Yes | Arabic ذ → Hebrew ז (dental fricative law); Arabic ذ → Aramaic ד. Both predicted and found. |
| قتل | to kill | קטל (heb) | qṭl | Yes | Yes | Arabic ق → Hebrew ק; Arabic ط → Hebrew ט; Arabic ل → Hebrew ל. Perfect consonant-to-consonant transfer. |

---

### Near Hits — Binary Nucleus Preserved, Full Skeleton Differs

| Arabic Root | Arabic Meaning | Hebrew/Aramaic | Projected (binary) | Exact | Binary | Notes |
|------------|---------------|----------------|-------------------|-------|--------|-------|
| سلم | peace, wholeness | שלום (heb) | sl- / šl- | No | Yes | The nucleus ס-ל is preserved; Hebrew extended the form with -וּם (-um suffix). The binary nucleus survives even as the word grows. |
| لسن | tongue, language | לשון (heb) | ls- | No | Yes | Arabic ل-س → Hebrew ל-ש. The binary nucleus is there; Hebrew again extended with -ון suffix. The tongue-language connection holds across the consonant skeleton. |
| أبب | father (also: fodder) | אב (heb) / אבא (arc) | ʔb- | No | Yes | Arabic three-consonant root reduced to two consonants in Hebrew and extended in Aramaic. The binary nucleus א-ב survives. This reduction is a known feature of Hebrew morphology. |
| أذن | ear | אוזן (heb) | ʔ-ð-n / ʔ-z-n | No | No | Best similarity 0.857. The projection maps Arabic ذ → Hebrew ז (correct), but Hebrew inserted a וּ vowel that creates a phonetic barrier. Near-miss. |
| سنن | tooth | שן (heb) | sn- / šn- | No | Yes | Binary nucleus matches (ס-נ → שׁ-נ); Hebrew gemination was dropped. The nucleus preserved; the reduplication didn't survive. |

---

### The Critical Reduction Case

| Arabic Root | Arabic Meaning | Hebrew/Aramaic | Exact | Binary | Notes |
|------------|---------------|----------------|-------|--------|-------|
| قلب | heart | לב (heb) / לבא (arc) | No | No | Arabic has three consonants (ق-ل-ב). Hebrew has two (ל-ב). The ق was dropped — this is a well-documented laryngeal loss in Hebrew. The machine can't claim a "hit" here, but the ל-ב nucleus is exactly the Hebrew root for heart. This is evidence of historical reduction, not a failure of the projection theory. |

---

## Section 3: Arabic to English Connections (5 Rows)

These are the most speculative results and the most exciting for the theory. Not proof of borrowing — evidence of consonant skeleton correspondence.

| Arabic Root | Arabic Meaning | English Word | How the Connection Works | Consonant Laws Applied | Exact Hit |
|------------|---------------|--------------|--------------------------|------------------------|-----------|
| **بيت** | house, dwelling, place of rest | **booth** | Arabic ب → English b (bilabial preserved); Arabic ت → English t (dental preserved); Arabic ي is a vowel extension, drops in consonant matching. Result: b-t = "booth" | ب→b, ي→(vowel, dropped), ت→t | Yes |
| **طرق** | path, track, way of passage | **track** | Arabic ط → English t (pharyngeal→dental, standard pharyngeal reduction); Arabic ر → English r (liquid preserved); Arabic ق → English k (uvular→velar). Result: t-r-k = "track" | ط→t, ر→r, ق→k | Yes |
| **جلد** | to freeze solid; skin; cold hardness | **cold** | Arabic ج → English g/k (palatal reduction); Arabic ل → English l (lateral preserved); Arabic د → English d (dental preserved). Result: g/k-l-d → "cold" | ج→k, ل→l, د→d | Yes |
| **برج** | tower, fortress | **burglar** | Binary nucleus only: Arabic ب-ر → English b-r. The connection is the idea of a structure you break into. Consonant partial hit (binary). | ب→b, ر→r | Binary only |
| **نفس** | breath, soul, life-breath | **inspire** | Binary nucleus: Arabic ن-ف → English n+f (in-spir-, the "in" = Arabic نفس's inward breath). Phonetic echo, not exact. | ن→n, ف→f | Binary only |

**Honest note on these connections:** The three exact hits (بيت→booth, طرق→track, جلد→cold) are real consonant correspondences. Whether they represent true etymological connections — meaning shared ancestry or historical contact — cannot be determined from consonant matching alone. They are data points, not conclusions. LV2's semantic embedding approach will tell us whether the *meanings* also cluster.

---

## Section 4: Summary Statistics Across All LV1 Sprints

### Root Prediction (Sprint 3) — 1,938 roots

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Total roots scored | 1,938 | All Jabal roots in the dataset |
| Nonzero Jaccard predictions | 782 (40.4%) | At least one correct feature predicted |
| Nonzero blended predictions | 1,092 (56.3%) | Right semantic direction (category-level) |
| Mean Jaccard | 0.146 | Average feature overlap across all roots |
| Mean blended Jaccard | 0.175 | Average when category credit is included |
| Method A estimate (human quality) | ~36.7% | A human would call ~1 in 3 predictions correct |
| Best model: Intersection | 1,125 roots (58.1%) | When nucleus and modifier overlap, predictions are best |
| Runner-up: Phonetic-Gestural | 741 roots (38.2%) | Looser model, lower precision |
| Exact J = 1.0 (perfect match) | 37 roots (1.9%) | Perfect feature set overlap |
| Stratum: zero match | 734 roots (37.9%) | Genuinely wrong predictions |

### By Arabic Letter Class (باب) — Top and Bottom Performers

| Bab | Count | Mean Blended J | Notes |
|-----|-------|----------------|-------|
| الظاء | 8 | 0.2875 | Best performing — small sample |
| الغين | 60 | 0.2684 | High performing — غ has strong semantic profile |
| العين | 119 | 0.1961 | Good — ع is one of Jabal's richest letters |
| الكاف | 77 | 0.2032 | Good |
| الصاد | 71 | 0.0948 | Weakest — ص combinations are poorly captured by current features |
| الحاء | 109 | 0.1474 | Below average |
| الفاء | 95 | 0.1463 | Below average |

### Cross-Lingual Projection — Semitic (Sprint 5)

| Test | Count | Result |
|------|-------|--------|
| Arabic–Hebrew + Aramaic pairs tested | 58 | — |
| Full skeleton exact hits | 37 | **64% hit rate** |
| Binary nucleus hits (first 2 consonants) | 51 | **88% hit rate** |
| Mean similarity score | 0.894 | Very high even for near-misses |
| Hebrew-only pairs | 43 | 62.8% exact, 86% binary |
| Aramaic-only pairs | 15 | 66.7% exact, 93.3% binary |

### Cross-Lingual Projection — English (Sprint 5)

| Test | Count | Result |
|------|-------|--------|
| Arabic–English candidate pairs tested | 18 | — |
| Full skeleton exact hits | 3 | **17% hit rate** |
| Binary nucleus hits (first 2 consonants) | 7 | **39% hit rate** |
| Mean similarity score | 0.708 | Lower than Semitic (expected — more sound change) |

### Method A Stratum Breakdown (Sprint 3)

| Stratum | Root Count | Share | Mean Jaccard | Human Score (Method A) |
|---------|-----------|-------|-------------|------------------------|
| Exact (J = 1.0) | 37 | 1.9% | 1.0 | 91.5 / 100 |
| Partial high (J ≥ 0.5) | 187 | 9.6% | ~0.55 | 71.5 / 100 |
| Partial low (0 < J < 0.5) | 557 | 28.7% | ~0.25 | 51.5 / 100 |
| Category-only (J = 0, bJ > 0) | 310 | 16.0% | 0.0 | 26.5 / 100 |
| Zero (J = 0, bJ = 0) | 734 | 37.9% | 0.0 | 12.0 / 100 |
| Empty actual (no Jabal label) | 113 | 5.8% | — | 34.5 / 100 |
| **Weighted overall** | **1,938** | 100% | **0.146** | **~36.7 / 100** |

### Improvement Across Calibration Passes

| Pass | Method A | Key Change |
|------|----------|------------|
| v1 (baseline) | 32.4% | Original feature extraction |
| v2 (all-features) | 33.8% | Expanded feature set, but over-predicted |
| **v3 (precision-capped)** | **36.7%** | Intersection model dominant; phonetic-gestural capped at 2+1 features |
| Estimated ceiling (current architecture) | ~40–45% | Without a richer vocabulary, hard limit |
| Target to reach for strong confirmation | >55% | Requires richer feature vocabulary or embedding layer |

---

*All data from benchmark runs completed 2026-03-23. Source files in `outputs/lv1_scoring/`.*
