# حروف الخلاف — 8 Letters Where Scholars Completely Disagree

**Juthoor LV1 — For Yassin's Review**
Date: 2026-03-24

---

## Background

The scoring engine assigns a phonosemantic meaning to each Arabic letter, drawing from five scholars:
**Jabal** (المعجم الاشتقاقي), **Hassan Abbas**, **Asim al-Masri**, **Neili**, and **Anbar**.

For 20 of the 28 consonants the scholars agree on at least one feature (STRONG or PARTIAL). For these 8 letters they completely disagree — no shared atomic feature across any two scholars. The scoring engine currently stores all readings as alternatives, which means these 8 letters introduce the most uncertainty into root predictions.

Each section below presents the raw data and a clear question for you to answer.

---

### حرف ت — التاء

**All scholar readings:**

| Scholar | Atomic Features | Raw Description (first 100 chars) | Sensory/Mechanism |
|---------|----------------|-----------------------------------|-------------------|
| Jabal | ضغط، دقة، وحدة، حدة، إمساك، قطع | ضغط بدقة ووحدة، قد يؤدي إلى إمساك ضعيف أو قطع | — |
| Abbas | رخاوة | طراوة وليونة — كأنامل تجسّ وسادة من قطن | لمسية / إيحائية |
| Asim | قوة | اجتذاب الحركات وتكاثفها لبناء قوّة جديدة | — |
| Neili | تجمع | جمع المتنوع وحشره | — |
| Anbar | قطع | من تحليل ب-ت: قطع، فصل (مكمّل لـ ب = ضيق/انقباض) | سياقية |

**Impact:** 28 binary nuclei, 118 triliteral roots.

**Note:** This is the hardest divergence in the entire dataset. Jabal gives 6 features (the most complex reading in his system). Abbas says *softness* — the opposite register from Jabal's *pressure*. Neili says *gathering*. Asim says *force*. Anbar says *cutting* (derived by contrast with ب). One interpretation: ت is the most contextually sensitive letter and each scholar is capturing a different face of the same articulation. Another: one or more readings are wrong.

**Question for Yassin:** Which reading is closest to the truth? Should we:
- a) Keep all as alternatives (current approach)
- b) Prefer one scholar's reading — if so, whose?
- c) Blend readings — e.g., take Jabal's ضغط/قطع as the core and drop the rest?
- d) This letter's meaning is genuinely contested — accept uncertainty for now

---

### حرف د — الدال

**All scholar readings:**

| Scholar | Atomic Features | Raw Description (first 100 chars) | Sensory/Mechanism |
|---------|----------------|-----------------------------------|-------------------|
| Jabal | احتباس، ضغط، امتداد، طول | احتباس بضغط وامتداد طولي | — |
| Abbas | غلظ، ثقل، قوة | صلابة وثقل وشدة | لمسية / إيحائية |
| Asim | انتقال، إمساك | اندفاعٌ قصدي الدلالة بالحركة لأبعد مدى | — |
| Neili | [] (empty features) | الفعل المقصود المنظم | kinetic_gloss only |
| Anbar | قوة، إمساك، ضغط، اشتداد، احتباس | شديد مجهور مقلقل → الوقوف كالسد، المنع، الاشتداد | صوتية — شديدة |

**Impact:** 20 binary nuclei, 243 triliteral roots.

**Note:** Despite different vocabulary, all scholars are pointing at something in the domain of *bounded, heavy, directed force*. Neili's kinetic_gloss "الفعل المقصود المنظّم" is actually the best meta-description — it encompasses Jabal's احتباس, Asim's اندفاع قصدي, and Abbas's ثقل. Anbar's reading (based on the phonetic class "شديد مجهور مقلقل") agrees with Jabal's احتباس/ضغط most directly. At the category level all four converge on pressure_force + extension_movement, even though no two use the same Arabic term.

**Question for Yassin:** Should we:
- a) Keep all as alternatives (current approach)
- b) Prefer Anbar here — his reading overlaps Jabal and is phonetically grounded?
- c) Blend: احتباس + ضغط + قوة as the working core (covers Jabal, Abbas, Anbar)?
- d) This letter's meaning is genuinely contested — accept uncertainty

---

### حرف ز — الزاي

**All scholar readings:**

| Scholar | Atomic Features | Raw Description (first 100 chars) | Sensory/Mechanism |
|---------|----------------|-----------------------------------|-------------------|
| Jabal | اكتناز، ازدحام | اكتناز وازدحام | — |
| Abbas | تخلخل | اهتزاز وطنين وارتجاج | سمعية / إيحائية |
| Asim | انتقال | إبرازٌ تكرار الحركة مادياً | — |
| Neili | — (not covered) | — | — |
| Anbar | احتكاك، التحام | محتد مصفور ملتز → الاحتكاك، الالتحام، الالتزاز، التماس | صوتية — صفيرية |

**Impact:** 29 binary nuclei, 131 triliteral roots.

**Note:** This is the sharpest methodological split in the dataset. Jabal says *dense packing/crowding* (from lexical patterns in roots with ز). Abbas says *rarefaction/vibration/buzzing* (from the auditory quality of the voiced sibilant). These are near-antonyms. Asim's انتقال resolves nothing. Anbar's احتكاك/التحام (friction, contact — from phonetic class "مصفور") is a third position, closer to the sound's physical production. The core question is: which method should win — lexical evidence (Jabal) or articulatory/auditory mimesis (Abbas/Anbar)?

**Question for Yassin:** Should we:
- a) Keep all as alternatives (current approach)
- b) Prefer Jabal's lexical evidence (اكتناز/ازدحام) as more relevant to the scoring engine?
- c) Prefer Abbas/Anbar's articulatory reading (اهتزاز/احتكاك) as more phonetically grounded?
- d) This letter's meaning is genuinely contested — this divergence may be methodologically irreducible

---

### حرف ع — العين

**All scholar readings:**

| Scholar | Atomic Features | Raw Description (first 100 chars) | Sensory/Mechanism |
|---------|----------------|-----------------------------------|-------------------|
| Jabal | التحام، رقة، حدة، رخاوة | التحام على رقة مع حدة ما / رخاوة جرم ملتحم | — |
| Abbas | عمق | عمق وإشراق وإفصاح | شعورية حلقية / إيحائية |
| Asim | ظاهر، انتقال | مَعاينةٌ داخلية وخارجية للمبهم في الحركة ووجهتها | — |
| Neili | ظهور | الكشف والتوضيح | — |
| Anbar | خروج، ظهور | حلقي مظهر متفجر → التفجر، الإشراق، الظهور، الإفصاح | صوتية — حلقية |

**Impact:** 40 binary nuclei, 260 triliteral roots.

**Note:** This may be a case of *two real clusters* rather than true divergence. Asim's ظاهر and Neili's ظهور are near-synonyms — they agree. Anbar also says ظهور/إفصاح. That's three scholars on one side: the ع signals *appearance, becoming visible, disclosure*. On the other side, Jabal's التحام/رخاوة (fusion, softness) and Abbas's عمق (depth) point to an internal/connective quality. So there may be a ظاهر/باطن duality: Asim+Neili+Anbar capture the disclosure face, while Jabal and Abbas describe the connective depth. These may be complementary rather than competing.

**Question for Yassin:** Should we:
- a) Keep all as alternatives (current approach)
- b) Prefer the Asim+Neili+Anbar cluster (ظهور/إفصاح) — it has three-scholar support?
- c) Blend: acknowledge ع has two faces — ظهور (outer disclosure) + التحام/عمق (inner depth)?
- d) This letter's meaning is genuinely contested — accept uncertainty

---

### حرف م — الميم

**All scholar readings:**

| Scholar | Atomic Features | Raw Description (first 100 chars) | Sensory/Mechanism |
|---------|----------------|-----------------------------------|-------------------|
| Jabal | امتساك، استواء، ظاهر | امتساك واستواء ظاهري | — |
| Abbas | تجمع | إطباق، ضم، انغلاق | لمسية / إيمائية (يقيناً) |
| Asim | انتقال | تكميل النواقص لإتمام العمل والحركة | — |
| Neili | [] (empty features) | الإتمام والاكتمال | kinetic_gloss only |
| Anbar | تجمع، تماسك، احتواء | إطباق الشفتين → التجمع، الانقباض، التراكم، الطي، الاحتواء | صوتية — شفوية |

**Impact:** 44 binary nuclei, 294 triliteral roots. The highest-impact DIVERGE letter.

**Note:** Abbas's تجمع is mechanistically the strongest reading here — the bilabial closure of م (lips press together = gathering/closing) is articulatory mimesis at its clearest. Abbas rates this يقيناً (certain). Anbar independently arrives at the same reading (تجمع/احتواء) from the phonetic class "إطباق الشفتين". That makes Abbas and Anbar a strong pair. Jabal's امتساك (holding/clinging) is related but different. Neili's empty features are a data gap, not disagreement — his kinetic_gloss "الإتمام والاكتمال" (completion) aligns more with Asim than with Abbas. So the split is: Jabal/Asim/Neili on one axis (completion, evenness) vs. Abbas/Anbar on another (gathering, enclosure).

**Question for Yassin:** Should we:
- a) Keep all as alternatives (current approach)
- b) Prefer Abbas+Anbar's تجمع/احتواء — two scholars, mechanistically grounded, bilabial closure is clear?
- c) Blend: تجمع (Abbas+Anbar) as primary + امتساك (Jabal) as secondary?
- d) This letter's meaning is genuinely contested — accept uncertainty

---

### حرف هـ — الهاء

**All scholar readings:**

| Scholar | Atomic Features | Raw Description (first 100 chars) | Sensory/Mechanism |
|---------|----------------|-----------------------------------|-------------------|
| Jabal | فراغ، إفراغ، جوف | فراغ أو إفراغ ما في الجوف | — |
| Abbas | تخلخل، فراغ | اهتزاز واضطراب وفراغ | شعورية حلقية / إيحائية |
| Asim | انتقال، جوف | انتقالٌ محمول غير مستقر، فإذا استقرّ جذب | — |
| Neili | — (not covered) | — | — |
| Anbar | — (not covered) | — | — |

**Impact:** 29 binary nuclei, 146 triliteral roots.

**Note:** This is actually a borderline case. Jabal and Abbas both say فراغ — that is a genuine shared feature. The comparison table in the system currently classifies هـ as DIVERGE because Asim's انتقال/جوف doesn't confirm it, but Asim uses جوف (hollow/cavity) which is semantically close to Jabal's جوف. There is a real case that هـ should be reclassified to PARTIAL with فراغ as a confirmed cross-scholar feature. Only Asim is the weak link here, and his جوف points in the same spatial direction.

**Question for Yassin:** Should we:
- a) Keep as DIVERGE — three readings, keep all as alternatives
- b) Reclassify to PARTIAL, taking فراغ (Jabal+Abbas) as the confirmed feature?
- c) Blend: فراغ/جوف as unified reading — "hollow emptiness" covers both Jabal and Asim?
- d) This letter's meaning is genuinely contested — accept uncertainty

---

### حرف و — الواو

**All scholar readings:**

| Scholar | Atomic Features | Raw Description (first 100 chars) | Sensory/Mechanism |
|---------|----------------|-----------------------------------|-------------------|
| Jabal | اشتمال، احتواء | اشتمال واحتواء | — |
| Abbas | تلاصق | اتجاه للأمام | بصرية / هيجانية (يقيناً) |
| Asim | حيز، انتقال | تموضعٌ مكاني يحدّد حيّز الحركة | — |
| Neili | — (not covered) | — | — |
| Anbar | تجمع | ضم الشفتين → مصارعة الجاذبية، الانحصار، الضيق | صوتية — حركات (شفوية) |

**Impact:** 18 binary nuclei, 374 triliteral roots.

**Note:** الواو is one of the حروف الجوفية (weak letters / letters of extension). Hassan Abbas explicitly states that its lexical influence is "شبه معدوم" (near-zero) — it functions primarily as a grammatical connector, not a phonosemantic carrier. This is a special case: the divergence may not matter much because the letter's contribution to root meaning is minimal regardless of which reading is used. Anbar's approach (from bilabial rounding of the دمة = ضم الشفتين) gives تجمع/ضيق, which differs entirely from Jabal's احتواء. Asim's حيز (spatial location) is different again.

**Question for Yassin:** Should we:
- a) Keep all as alternatives (current approach)
- b) Treat و as phonosemantically weak and assign it minimal weight in scoring — regardless of which reading?
- c) Prefer Jabal's احتواء/اشتمال as the working reading for scoring purposes?
- d) This letter's meaning is genuinely contested — and its low lexical impact makes this a low-priority question

---

### حرف ي — الياء

**All scholar readings:**

| Scholar | Atomic Features | Raw Description (first 100 chars) | Sensory/Mechanism |
|---------|----------------|-----------------------------------|-------------------|
| Jabal | اتصال، وحدة، تفرق، رقة | اتصال الممتد شيئاً واحداً وعدم تفرقه | — |
| Abbas | باطن | اتجاه للأسفل | بصرية / هيجانية (يقيناً) |
| Asim | تعلق، انتقال | ملازمة الحركة في البُعد الزمني المستمر | — |
| Neili | امتداد | الاستمرار والديمومة | — |
| Anbar | نقص | مطل الكسرة → مساوقة الجاذبية الأرضية (الانحدار) | صوتية — حركات |

**Impact:** 6 binary nuclei, 166 triliteral roots.

**Note:** Like و, الياء is a حرف جوفي with near-zero independent lexical influence per Abbas. The four scholars who cover it describe four different phenomena: Jabal sees continuity/connection, Abbas sees downward direction, Asim sees temporal persistence, Neili sees extension, and Anbar sees gravitational descent (from the kasra vowel's downward phonetics). There is a possible soft cluster around continuity: Jabal's اتصال, Asim's ملازمة (adherence/persistence), and Neili's امتداد/ديمومة all point at "sustained connection through time." Abbas and Anbar are outliers in a spatial/directional reading.

**Question for Yassin:** Should we:
- a) Keep all as alternatives (current approach)
- b) Treat ي as phonosemantically weak (same as و) and assign minimal scoring weight?
- c) Prefer the Jabal+Asim+Neili continuity cluster (اتصال/ملازمة/امتداد)?
- d) This letter's meaning is genuinely contested — accept uncertainty

---

## Summary: Priority for Your Review

| Letter | Binary Nuclei | Triliteral Roots | Urgency | Current Recommendation |
|--------|--------------|-----------------|---------|----------------------|
| م | 44 | 294 | HIGH | Abbas+Anbar تجمع has mechanical grounding — consider (b) |
| ع | 40 | 260 | HIGH | Three-scholar cluster on ظهور — consider (c) blend |
| و | 18 | 374 | MEDIUM | Low phonosemantic weight — consider (b) or (d) |
| ي | 6 | 166 | LOW | Low phonosemantic weight — consider (b) or (d) |
| ز | 29 | 131 | MEDIUM | Methodological split — consider (b) or (d) |
| هـ | 29 | 146 | MEDIUM | Jabal+Abbas share فراغ — likely should be PARTIAL, consider (b) |
| ت | 28 | 118 | MEDIUM | Hardest case — no recommendation, needs your judgment |
| د | 20 | 243 | MEDIUM | All converge at category level — consider (c) blend |

---

## Response Template

Please fill this in and return it. Your decisions will be written directly into the scoring engine.

```
## My Decisions

### ت — [a/b/c/d] — notes:
### د — [a/b/c/d] — notes:
### ز — [a/b/c/d] — notes:
### ع — [a/b/c/d] — notes:
### م — [a/b/c/d] — notes:
### هـ — [a/b/c/d] — notes:
### و — [a/b/c/d] — notes:
### ي — [a/b/c/d] — notes:
```
