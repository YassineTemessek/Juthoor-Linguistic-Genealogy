# مصنع البحث — Juthoor Research Factory
## الخطة الشاملة المتكاملة (النسخة النهائية)

---

## الصياغة النظرية للمشروع

> **LV1 هو مصنع بحث حاسوبي يختبر فرضية أن البنية الصوتية-الجذرية للعربية
> تحمل طبقة منتظمة من المعنى قبل الصرف، يمكن قياسها من الحرف المفرد إلى
> الجذر المركب، ثم إعادة استخدامها في الاسترجاع المقارن (LV2) والتفسير
> النظري (LV3).**

---

## الهندسة المعمارية: فصل النواة عن المصنع

```
Juthoor-ArabicGenome-LV1/
│
├── LV1-CORE (مستقر — ثابت — يخدم كل المستويات)
│   ├── letter_meanings              ← 28 حرفاً بمعانيها
│   ├── binary_root_inventory        ← 457 جذراً ثنائياً
│   ├── triliteral_root_inventory    ← 1,938 جذراً ثلاثياً
│   ├── genome_v1 / genome_v2        ← 12,333 مدخلة
│   └── semantic_validation          ← Phase 3 scores
│
├── LV1-RESEARCH FACTORY (تجريبي — يعمل فوق النواة)
│   ├── Data Contracts               ← تعريف صارم لكل كيان
│   ├── Feature Store                ← ميزات مستخرجة قابلة لإعادة الاستخدام
│   ├── Experiment Engine            ← محرك تشغيل التجارب
│   ├── Hypothesis Registry          ← سجل الفرضيات الرسمي
│   └── Publication Layer            ← مخرجات بشرية مفهومة
│
└── بوابة الترقية → LV2 / LV3
    experimental → measured → stable → promoted
```

**القاعدة الذهبية:** المصنع لا يعدّل النواة. يقرأ منها فقط وينتج فوقها.

---

## الطبقة 1: عقود البيانات (Data Contracts)

كل كيان في المصنع له تعريف صارم:

| الكيان | المعرف | الحقول الأساسية | المصدر |
|--------|--------|-----------------|--------|
| **Letter** | حرف واحد | letter, meaning, phonetic_features | letter_meanings.jsonl |
| **BinaryRoot** | حرفان | binary_root, meaning, letter1, letter2, letter1_meaning, letter2_meaning | roots.jsonl |
| **TriliteralRoot** | ثلاثة حروف | tri_root, binary_root, added_letter, axial_meaning, quran_example | roots.jsonl |
| **RootFamily** | binary_root | كل الجذور الثلاثية المنتمية | genome_v2/ |
| **MetathesisPair** | (XY, YX) | br1, br2, meaning1, meaning2, similarity | محسوبة (166 زوجاً) |
| **SubstitutionPair** | (XYZ, XY'Z) | root1, root2, changed_letter, substitute, makhraj_distance | محسوبة |
| **PermutationGroup** | مجموعة تقاليب | roots[], shared_letters, mean_similarity | محسوبة |

---

## الطبقة 2: سجل الفرضيات (Hypothesis Registry)

| المعرف | الفرضية | المصدر النظري | التجربة | الحالة |
|--------|---------|--------------|---------|--------|
| **H1** | الحروف المتقاربة مخرجاً متقاربة معنًى | الخليل (ضمنياً) | 1.1 + 5.1 | pending |
| **H2** | الثنائي يحدد الحقل الدلالي بثبات | جبل (الفصل المعجمي) | 2.3 | pending |
| **H3** | للحرف الثالث شخصية تعديلية مستقرة | جبل (التركيب التتابعي) | 3.1 ★ | pending |
| **H4** | القلب الثنائي يحفظ جزءاً من النواة الدلالية | ابن جني (الاشتقاق الأكبر) | 4.1 | pending |
| **H5** | القلب يغيّر المعنى (الترتيب مهم) | جبل (ضد ابن جني) | 4.1 | pending |
| **H6** | الإبدال من نفس المخرج أقرب دلالياً | ابن جني (شروطه الثلاثة) | 4.3 | pending |
| **H7** | بعض التركيبات المفقودة غائبة بسبب تناقض دلالي | جامعة النجاح | 2.2 | pending |
| **H8** | الحرف يتغير معناه بتغير موضعه | العقاد | 1.2 | pending |
| **H9** | المطبقة أقوى دلالياً من نظيراتها غير المطبقة | ابن جني + أوهالا | 5.2 | pending |
| **H10** | معنى الجذر = تركيب معاني حروفه | جبل (المعادلات الكيميائية) | 3.2 | pending |
| **H11** | الآلة تستطيع اكتشاف البنية الثنائية بدون إشراف | اختبار استقلالي | 6.2 | pending |
| **H12** | يمكن التنبؤ بمعنى جذر جديد من مكوناته | القوة التوليدية | 6.1 | pending |

---

## الطبقة 3: مخزن الميزات (Feature Store)

ميزات تُحسب مرة واحدة وتُعاد استخدامها عبر كل التجارب:

| الميزة | الوصف | يُحسب في | يُستخدم في |
|--------|-------|----------|-----------|
| `letter_embedding` | تمثيل متجهي لمعنى كل حرف | Phase 0 | كل التجارب |
| `binary_meaning_embedding` | تمثيل معنى الجذر الثنائي | Phase 0 | 2.1, 2.3, 4.1, 6.3 |
| `axial_meaning_embedding` | تمثيل المعنى المحوري للثلاثي | Phase 0 | 3.1, 3.2, 4.2, 6.1, 6.2 |
| `articulatory_vector` | [مخرج، جهر، شدة، إطباق، ...] لكل حرف | Phase 0 | 5.1, 5.2, 4.3 |
| `modifier_effect` | المسافة الدلالية: ثلاثي - ثنائي | Phase 1 | 3.1, 3.2, 6.1 |
| `field_coherence` | تماسك كل فصل معجمي | Phase 1 | 2.3, 7.1 |
| `metathesis_score` | تشابه كل زوج قلب | Phase 1 | 4.1, H4/H5 |
| `positional_stats` | إحصائيات الحرف في كل موضع | Phase 2 | 1.2 |
| `sensory_class` | تصنيف حسي للمعنى (لمس، بصر، سمع...) | Phase 2 | 1.3 |

---

## الطبقة 4: محرك التجارب (Experiment Engine)

كل تجربة تتبع مواصفة موحدة:

```yaml
experiment:
  id: "3.1"
  name: "modifier_personality"
  hypothesis: ["H3"]
  inputs:
    - data/muajam/roots.jsonl
    - features/letter_embedding
    - features/binary_meaning_embedding
    - features/axial_meaning_embedding
  method: |
    لكل حرف كثالث: جمع كل الجذور → حساب modifier_effect
    → قياس اتساق الاتجاه → اختبار إحصائي
  metrics:
    - consistency_score (0-1)
    - effect_direction (semantic vector)
    - significance (p-value)
  outputs:
    - outputs/research_factory/axis3/modifier_profiles.jsonl
    - outputs/research_factory/axis3/modifier_heatmap.png
  success_criteria: |
    consistency > 0.6 لأغلب الحروف = H3 مدعومة
    consistency < 0.3 = H3 مرفوضة
  status: pending
```

---

## خطة التنفيذ: 4 مراحل + مرحلة صفرية

### Phase 0: بناء المنصة (أسبوع 1)

**الهدف:** بنية تحتية مشتركة لكل التجارب

```
scripts/research_factory/
  common/
    embeddings.py          ← حساب BGE-M3 لكل الكيانات
    phonetic_features.py   ← متجهات صوتية لـ28 حرفاً
    statistics.py          ← اختبارات إحصائية موحدة
    visualization.py       ← رسم بياني موحد
    experiment_runner.py   ← تشغيل + تسجيل نتائج
  
resources/
    hypotheses.yaml        ← سجل الفرضيات
    phonetics/
      makhaarij.json       ← 17 مخرجاً حسب الخليل
      sifaat.json          ← صفات كل حرف

outputs/research_factory/
    features/              ← Feature Store
    axis1/ ... axis7/      ← نتائج كل محور
    reports/               ← تقارير تجميعية
```

**المنتج:** `features/` محمّل بكل الـembeddings والمتجهات الصوتية

---

### Phase 1: النواة العلمية (أسابيع 2-5)

**3 تجارب فقط** — تبني العمود الفقري لكل شيء بعدها:

#### التجربة 1.1 — مصفوفة تشابه الحروف الـ28
| البُعد | التفصيل |
|--------|---------|
| **الفرضية** | H1: المتقارب مخرجاً متقارب معنًى |
| **المدخل** | 28 letter_embedding + 28 articulatory_vector |
| **العملية** | مصفوفة تشابه جيبي 28×28 + تجميع هرمي + مقارنة مع مخارج الخليل |
| **المخرج** | heatmap + dendrogram + Mantel test (r, p-value) |
| **معيار النجاح** | Mantel r > 0.3, p < 0.01 |
| **القيمة** | أساس لكل تجارب الإبدال والمخارج |

#### التجربة 2.3 — تماسك الفصول المعجمية
| البُعد | التفصيل |
|--------|---------|
| **الفرضية** | H2: الثنائي يحدد حقلاً دلالياً متماسكاً |
| **المدخل** | 457 binary_root × أعضاء كل فصل (1-18 ثلاثي) |
| **العملية** | لكل فصل: mean pairwise cosine(axial_meanings) → ترتيب |
| **المخرج** | coherence_scores.jsonl + توزيع + أقوى/أضعف 20 فصلاً |
| **معيار النجاح** | mean coherence > random baseline بـ 2σ |
| **القيمة** | يقيس قوة نظرية جبل كمياً |

#### التجربة 3.1 — شخصية الحرف المعدِّل ★★★★★
| البُعد | التفصيل |
|--------|---------|
| **الفرضية** | H3: لكل حرف ثالث "شخصية تعديلية" مستقرة |
| **المدخل** | 1,938 tri-root مع binary_root_meaning + axial_meaning |
| **العملية** | 1. لكل حرف كثالث: جمع كل (binary→tri) pairs |
|  | 2. حساب modifier_vector = embed(axial) - embed(binary) |
|  | 3. لكل حرف: mean(modifier_vectors) = "شخصيته" |
|  | 4. consistency = mean cosine بين modifier_vectors نفس الحرف |
|  | 5. مقارنة مع معنى الحرف عند جبل |
| **المخرج** | modifier_profiles.jsonl (28 بطاقة) + consistency_scores + heatmap |
| **معيار النجاح** | consistency > 0.5 لـ >60% من الحروف |
| **القيمة** | **أقوى اختبار حاسوبي للدلالة الصوتية ممكن** |

**لماذا هذه الثلاثة أولاً:**
- 1.1 تبني الأساس (هل الحروف نفسها منتظمة؟)
- 2.3 تختبر المستوى الثنائي (هل الفصل حقيقي؟)
- 3.1 تختبر المستوى الثلاثي (هل التعديل منتظم؟)

إذا نجحت الثلاثة → النظرية قوية من الأسفل إلى الأعلى

---

### Phase 2: القلب والإبدال والموضع (أسابيع 6-9)

#### التجربة 4.1 — القلب المكاني الثنائي
| البُعد | التفصيل |
|--------|---------|
| **الفرضيتان** | H4 (ابن جني: يحفظ) vs H5 (جبل: يغيّر) |
| **المدخل** | 166 زوج (XY, YX) مع معانيهما |
| **العملية** | 1. cosine(embed(meaning_XY), embed(meaning_YX)) لكل زوج |
|  | 2. مجموعة ضابطة: 166 زوج عشوائي |
|  | 3. Wilcoxon rank-sum test |
|  | 4. تصنيف: (أ) تشابه >0.7 (ب) تباين <0.3 (ج) وسط |
| **المخرج** | metathesis_analysis.jsonl + violin plot + p-value |
| **السؤال الحاسم** | كم نسبة (أ)؟ إذا >50% = ابن جني محق جزئياً. إذا <20% = جبل محق |

#### التجربة 4.3 — الإبدال اللغوي
| البُعد | التفصيل |
|--------|---------|
| **الفرضية** | H6: الإبدال من نفس المخرج أقرب دلالياً |
| **المدخل** | articulatory_vectors + كل أزواج الجذور المختلفة بحرف واحد |
| **العملية** | 1. إيجاد كل أزواج (XYZ, XY'Z) حيث Y≠Y' |
|  | 2. قياس makhraj_distance(Y, Y') |
|  | 3. قياس semantic_distance(meaning_XYZ, meaning_XY'Z) |
|  | 4. ارتباط Spearman بين المسافتين |
| **معيار النجاح** | ρ > 0.2, p < 0.01 |

#### التجربة 5.1 — مصفوفة الصوت والمعنى
| البُعد | التفصيل |
|--------|---------|
| **الفرضية** | H1 (الشق الفيزيائي) |
| **العملية** | CCA بين مصفوفة articulatory (28×N) ومصفوفة semantic (28×D) |
| **المعيار** | أول canonical correlation > 0.4 |

#### التجربة 1.2 — الدلالة الموضعية (العقاد)
| البُعد | التفصيل |
|--------|---------|
| **الفرضية** | H8: معنى الحرف يتغير بموضعه |
| **العملية** | لكل حرف: 3 مجموعات (أول/ثاني/ثالث) → intra-group coherence |
|  | مقارنة coherence(حرف_في_الأول) vs coherence(حرف_في_الثالث) |
| **القيمة** | يختبر ملاحظة العقاد عن الحاء |

---

### Phase 3: الذكاء الاصطناعي التوليدي (أسابيع 10-13)

#### التجربة 6.1 — التنبؤ بالمعنى المحوري
| البُعد | التفصيل |
|--------|---------|
| **الفرضية** | H12: يمكن التنبؤ بمعنى جذر من مكوناته |
| **العملية** | 80/20 split → input: binary_meaning + letter3_meaning → output: axial_meaning |
| **النماذج** | (أ) Claude few-shot (ب) MLP (ج) Transformer صغير |
| **المعيار** | cosine > 0.6 على مجموعة الاختبار |

#### التجربة 6.2 — اكتشاف بدون إشراف
| البُعد | التفصيل |
|--------|---------|
| **الفرضية** | H11: الآلة تكتشف البنية الثنائية وحدها |
| **العملية** | إخفاء binary_root → HDBSCAN على axial_meaning_embeddings |
| **المعيار** | Adjusted Rand Index > 0.3 مقابل تصنيف جبل |

#### التجربة 2.2 — الخانات المفقودة
| البُعد | التفصيل |
|--------|---------|
| **الفرضية** | H7: الغياب دلالي لا عشوائي |
| **العملية** | 1. تحديد 327 تركيبة غائبة |
|  | 2. لكل واحدة: حساب "التوافق الدلالي" من معنيَي الحرفين |
|  | 3. مقارنة: هل التركيبات الموجودة أكثر توافقاً من الغائبة؟ |
| **المعيار** | فرق معنوي بين التوزيعين |

#### التجربة 6.4 — الجذور الوهمية
| البُعد | التفصيل |
|--------|---------|
| **العملية** | توليد جذور "متوافقة" و"متناقضة" → التحقق من وجودها/غيابها |
| **القيمة** | قوة تنبؤية = النظرية ليست وصفية فقط بل تنبؤية |

---

### Phase 4: الترقية والتصدير (أسابيع 14-16)

| المنتج | الوجهة | الشرط |
|--------|--------|-------|
| `modifier_profiles` | → LV2 كـfeature | consistency > 0.5 |
| `metathesis_scores` | → LV3 كـevidence | p < 0.01 |
| `field_coherence` | → LV2 لترتيب النتائج | stable |
| `letter_clusters` | → LV2 لـcorridor modeling | validated |
| Evidence cards | → LV3 كأدلة نظرية | promoted |
| Dashboards | → واجهة عامة | بعد Phase 3 |

**بوابة الترقية:**
```
experimental  →  قيد التشغيل، لا يعتمد عليه أحد
measured      →  نتائج أولية، لم تُراجع
stable        →  نتائج مكررة، معايير واضحة
promoted      →  جاهز لـ LV2/LV3
```

---

## البنية البرمجية النهائية

```
Juthoor-ArabicGenome-LV1/
│
├── src/juthoor_arabicgenome_lv1/
│   ├── core/                          ← الجينوم الثابت
│   │   ├── models.py                  ← dataclasses للكيانات
│   │   └── loaders.py                 ← قراءة البيانات المعيارية
│   │
│   └── factory/                       ← محرك المصنع
│       ├── experiment_runner.py        ← تشغيل + تسجيل
│       ├── feature_store.py           ← قراءة/كتابة الميزات
│       ├── hypothesis_registry.py     ← إدارة الفرضيات
│       └── metrics.py                 ← مقاييس موحدة
│
├── scripts/research_factory/
│   ├── phase0_setup/
│   │   ├── compute_all_embeddings.py
│   │   ├── build_articulatory_vectors.py
│   │   └── initialize_feature_store.py
│   │
│   ├── axis1_letter/
│   │   ├── exp_1_1_letter_similarity.py
│   │   ├── exp_1_2_positional_semantics.py
│   │   └── exp_1_3_sensory_classification.py
│   │
│   ├── axis2_binary/
│   │   ├── exp_2_1_binary_landscape.py
│   │   ├── exp_2_2_missing_combinations.py
│   │   └── exp_2_3_field_coherence.py
│   │
│   ├── axis3_third_letter/
│   │   ├── exp_3_1_modifier_personality.py   ★
│   │   └── exp_3_2_compositionality.py
│   │
│   ├── axis4_permutation/
│   │   ├── exp_4_1_binary_metathesis.py
│   │   ├── exp_4_2_triliteral_permutations.py
│   │   └── exp_4_3_phonetic_substitution.py
│   │
│   ├── axis5_phonetics/
│   │   ├── exp_5_1_sound_meaning_matrix.py
│   │   └── exp_5_2_emphasis_hypothesis.py
│   │
│   ├── axis6_generative/
│   │   ├── exp_6_1_meaning_predictor.py
│   │   ├── exp_6_2_unsupervised_discovery.py
│   │   ├── exp_6_3_vector_arithmetic.py
│   │   └── exp_6_4_phantom_roots.py
│   │
│   └── axis7_validation/
│       ├── exp_7_1_quranic_correlation.py
│       └── exp_7_2_dictionary_crosscheck.py
│
├── resources/
│   ├── hypotheses.yaml
│   └── phonetics/
│       ├── makhaarij.json
│       └── sifaat.json
│
└── outputs/research_factory/
    ├── features/                      ← Feature Store
    │   ├── letter_embeddings.npy
    │   ├── binary_meaning_embeddings.npy
    │   ├── axial_meaning_embeddings.npy
    │   └── articulatory_vectors.npy
    │
    ├── axis1/ axis2/ ... axis7/       ← نتائج كل محور
    ├── reports/                        ← تقارير تجميعية
    └── figures/                        ← رسوم بيانية
```

---

## ملخص الأرقام الكاملة

| البُعد | العدد | المصدر |
|--------|-------|--------|
| حروف بمعانٍ | 28 | `letter_meanings.jsonl` |
| جذور ثنائية موثقة | 457 (من 784 نظرية) | `roots.jsonl` |
| جذور ثنائية مفقودة | 327 | محسوبة |
| جذور ثلاثية بمعانٍ محورية | 1,938 | `roots.jsonl` |
| جذور في الجينوم الكامل | 12,333 | `genome_v2/` |
| أزواج قلب ثنائي | 166 | محسوبة |
| جذور بشواهد قرآنية | 1,739 (90%) | `roots.jsonl` |
| فرضيات رسمية | 12 | hypothesis registry |
| تجارب مخططة | 19 | 7 محاور |
| درجة التحقق الحالية | 0.558 (mean) | Phase 3 |

---

## القاعدة التشغيلية

1. **لا تبدأ كل المحاور دفعة واحدة** — تشتيت علمي + تكرار أدوات
2. **Phase 0 أولاً** — بدون البنية التحتية لا فائدة من التجارب
3. **3 تجارب فقط في Phase 1** — 1.1 + 2.3 + 3.1 = العمود الفقري
4. **المصنع لا يكسر النواة** — يقرأ فقط، لا يعدّل
5. **بوابة الترقية** — لا شيء يذهب لـ LV2/LV3 إلا بعد promotion
6. **كل تجربة = فرضية + مدخلات + طريقة + مقياس + معيار نجاح**

---

*مصنع البحث — النسخة النهائية المتكاملة*
*Juthoor-ArabicGenome-LV1*
*2026-03-13*
