# P2.1 Cross-Scholar Letter Comparison Report
**Juthoor Linguistic Genealogy — LV1 ArabicGenome**
Date: 2026-03-24

---

## Section 1: Overview

Four scholars compared in this report. Anbar is pending (will be integrated when P1.3 lands).

| Scholar | Coverage | Confidence | Framework |
|---------|----------|------------|-----------|
| Jabal (المعجم الاشتقاقي) | 28 letters | high | Empirical phonosemantic decomposition |
| Hassan Abbas (ABBAS_LETTER_CLASSIFICATION) | 29 letters (incl. ألف المد) | medium-high | Sensory-mimetic classification |
| Asim al-Masri (LV1_VERIFIED_DATA_AUDIT) | 29 letters (incl. ألف المد) | medium | Kinetic/intentionality framework |
| Neili (ملخص الدلالة الصوتية) | 10 letters | high | Foundational kinetic primitives |

**Methodology:** For each letter, the atomic_features lists from all available scholars are compared. A feature is considered "shared" when the same Arabic term (or a clear synonym at the gloss level) appears in two or more scholars' lists. Agreement levels:

- **STRONG** — 2+ features shared across 2+ scholars
- **PARTIAL** — 1 feature shared across 2+ scholars (or synonyms at category level)
- **DIVERGE** — no shared features despite 2+ scholars covering the letter; or all readings point to different phenomena

Neili covers only 10 letters (ب ت ح د ر ع ك ل م ي), so most comparisons are three-way (Jabal/Abbas/Asim). Where Neili is present it is noted explicitly.

---

## Section 2: Agreement Summary Table (28 Letters)

The table below covers the 28 consonants of the standard Arabic alphabet (excluding ألف المد, which Asim and Abbas include as a 29th entry but Jabal and Neili do not).

Cells show atomic_features as extracted from each JSONL. "—" = scholar does not cover this letter.

| # | Letter | Jabal features | Asim features | Abbas features | Neili features | Agreement Level | Shared features |
|---|--------|---------------|---------------|----------------|----------------|-----------------|-----------------|
| 1 | ء | تأكيد، ضغط، تقوية، قوة | انتقال | تأكيد | — | **PARTIAL** | تأكيد (Jabal ↔ Abbas) |
| 2 | ب | تجمع، رخاوة، تلاصق | خروج، اختراق، اتساع | بروز | ظهور، خروج | **PARTIAL** | خروج (Asim ↔ Neili) |
| 3 | ت | ضغط، دقة، وحدة، حدة، إمساك، قطع | قوة | رخاوة | تجمع | **DIVERGE** | none — four different readings |
| 4 | ث | كثافة، غلظ، تفشي، انتشار | امتساك | تفشي | — | **PARTIAL** | تفشي (Jabal ↔ Abbas) |
| 5 | ج | تجمع، حدة | تجمع | رخاوة | — | **PARTIAL** | تجمع (Jabal ↔ Asim) |
| 6 | ح | احتكاك، جفاف، باطن | انتقال | اتساع، باطن | اتساع | **STRONG** | باطن (Jabal ↔ Abbas); اتساع (Abbas ↔ Neili) |
| 7 | خ | تخلخل، جفاف، غلظ | خروج، انتقال | تخلخل، جفاف، خروج | — | **STRONG** | تخلخل + جفاف (Jabal ↔ Abbas); خروج (Asim ↔ Abbas) |
| 8 | د | احتباس، ضغط، امتداد، طول | انتقال، إمساك | غلظ، ثقل، قوة | [] | **DIVERGE** | none — Neili's entry is empty features; no atomic overlap |
| 9 | ذ | نفاذ، رخاوة، غلظ | نفاذ، انتقال، التحام | نفاذ | — | **STRONG** | نفاذ (all three: Jabal ↔ Asim ↔ Abbas) |
| 10 | ر | استرسال، باطن، تماسك | انتقال | انتقال | [] | **PARTIAL** | انتقال (Asim ↔ Abbas); Neili entry empty |
| 11 | ز | اكتناز، ازدحام | انتقال | تخلخل | — | **DIVERGE** | none |
| 12 | س | امتداد، دقة، وحدة، حدة | امتداد، ظهور | دقة، امتداد | — | **STRONG** | امتداد (all three: Jabal ↔ Asim ↔ Abbas); دقة (Jabal ↔ Abbas) |
| 13 | ش | تفشي، انتشار، دقة | انتشار، انتقال، تجمع | انتشار، تفرق | — | **PARTIAL** | انتشار (all three) |
| 14 | ص | نفاذ، غلظ، قوة، خلوص، فراغ | انتقال | غلظ، خلوص، فراغ | — | **STRONG** | غلظ + خلوص + فراغ (Jabal ↔ Abbas) — triple match |
| 15 | ض | ضغط، كثافة، غلظ | إمساك | ضغط، كثافة | — | **STRONG** | ضغط + كثافة (Jabal ↔ Abbas) — exact match |
| 16 | ط | ضغط، اتساع، غلظ | انتقال | اتساع | — | **PARTIAL** | اتساع (Jabal ↔ Abbas) |
| 17 | ظ | نفاذ، غلظ، حدة، كثافة | ظهور، انتقال، ظاهر | غلظ، بروز | — | **PARTIAL** | غلظ (Jabal ↔ Abbas) |
| 18 | ع | التحام، رقة، حدة، رخاوة | ظاهر، انتقال | عمق | ظهور | **DIVERGE** | none — but note: Asim ظاهر ≈ Neili ظهور (near-synonym) |
| 19 | غ | تخلخل، رخاوة، كثافة | ظهور، انتقال، إمساك، باطن | باطن | — | **PARTIAL** | باطن (Asim ↔ Abbas) |
| 20 | ف | طرد، إبعاد، نفاذ، قوة | تفرق، انتقال | نفاذ | — | **PARTIAL** | نفاذ (Jabal ↔ Abbas) |
| 21 | ق | تعقد، اشتداد، قوة، عمق | قوة، انتقال | قوة | — | **STRONG** | قوة (all three: Jabal ↔ Asim ↔ Abbas) |
| 22 | ك | ضغط، دقة، امتساك، قطع | تجمع، احتواء | ضغط، تماسك | تجمع | **STRONG** | ضغط (Jabal ↔ Abbas); تجمع (Asim ↔ Neili) — double pair |
| 23 | ل | تعلق، امتداد، استقلال، تميز | انتقال | تلاصق | تلاصق، اتصال | **PARTIAL** | تلاصق (Abbas ↔ Neili) |
| 24 | م | امتساك، استواء، ظاهر | انتقال | تجمع | [] | **DIVERGE** | none — Neili empty features |
| 25 | ن | امتداد، لطف، باطن | انتقال، جوف | خروج، نفاذ، باطن | — | **PARTIAL** | باطن (Jabal ↔ Abbas) |
| 26 | هـ | فراغ، إفراغ، جوف | انتقال، جوف | تخلخل، فراغ | — | **DIVERGE** | جوف might link Jabal/Asim but Jabal uses it differently; فراغ (Jabal ↔ Abbas) — borderline PARTIAL. Classified DIVERGE pending Yassin review |
| 27 | و | اشتمال، احتواء | حيز، انتقال | تلاصق | — | **DIVERGE** | none |
| 28 | ي | اتصال، وحدة، تفرق، رقة | تعلق، انتقال | باطن | امتداد | **DIVERGE** | none across all four |

**Summary counts:**
- STRONG: ح، خ، ذ، س، ص، ض، ق، ك — **8 letters**
- PARTIAL: ء، ب، ث، ج، ش، ط، ظ، غ، ف، ل، ن، ر — **12 letters**
- DIVERGE: ت، د، ز، ع، م، هـ، و، ي — **8 letters**

> Note: ذ and ق are STRONG based on data; the original task brief listed 6 STRONG letters (before ذ and ق were reconfirmed). The table reflects the actual data.

---

## Section 3: Scholar Pair Analysis

### Jabal ↔ Abbas — Strongest Pair

This is the strongest alignment in the dataset. After Abbas's re-extraction from the verified ABBAS_LETTER_CLASSIFICATION (phonosemantic mechanism types: إيمائية, إيحائية, هيجانية), the Jabal-Abbas overlap improved substantially.

**15/28 letters share at least one feature** (ء، خ، ذ، س، ص، ض، ط، ظ، غ، ف، ح، ك، ن، ث، ق — though overlap varies in depth from a single term like نفاذ to triple matches like ص).

The alignment is strongest for the emphatic consonants (ص ض ط ظ) and the fricatives (خ ف). Both scholars work from a materialist decomposition — Jabal from lexical patterning across the المعجم الاشتقاقي, Abbas from articulatory-sensory mimesis — and their convergence on texture features (غلظ، جفاف، كثافة) reflects that both tracks are capturing real phonosemantic substance.

### Jabal ↔ Asim — Weakest Pair

**Approximately 5/28 letters share features** at the lexical level (ج:تجمع, ذ:نفاذ, ق:قوة, ك:ضغط via category, ش:انتشار via Asim's secondary). Asim's kinetic/intentionality framework produces a heavily verbal vocabulary (انبثاق، اندفاع، هيمنة، تكرار) that rarely maps directly onto Jabal's nominal/adjectival decomposition (تخلخل، جفاف، رخاوة).

However, this may understate real agreement. For example:

- **ر:** Jabal's استرسال ("flowing continuity") and Asim's انتقال ("movement/transit") both describe sustained directional motion. Different words, same phenomenon.
- **س:** Asim's هيمنة يبسط نفوذاً فوقياً translates partially to امتداد in his atomic_features, which directly matches Jabal.
- **ت:** Jabal's ضغط/دقة/وحدة framework and Asim's "gathering of movements to build new force" may be describing the same convergent articulation from different angles — one physical, one intentional.

**The Jabal-Asim gap is partly a vocabulary problem, not a theoretical one.** A normalization pass mapping Asim's kinetic vocabulary to Jabal's texture/pressure/spatial categories would likely raise overlap to 10-12 letters.

### Asim ↔ Neili — Unexpectedly Low

**2/10 letters share features at the lexical level** (ك:تجمع, ل:تلاصق via Neili↔Abbas more than Asim). Given that Asim is widely regarded as an intellectual heir of Neili and his framework continues_neili=true for 8 of 10 shared letters, this surface disagreement is striking.

The explanation is scope: Neili's 10 letters provide only sparse atomic_features (several have empty lists: د، ر، م), suggesting Neili's document was captured at a summary level. The kinetic_gloss entries are richer ("ترتب الحركة وانتظامها بتكرار" for ر, "اندفاع الحركة بتدبير مقصود" for د) and these do align with Asim. Neili's atomic_features as stored are under-extracted, not necessarily divergent. **Do not conclude Asim broke from Neili — the low overlap is a data artifact.**

### Abbas ↔ Neili

**3/10 letters share features** (ح:اتساع, ك:تجمع, ل:تلاصق+اتصال). Small sample but the matches are clean. Abbas and Neili agree on ح being about expansiveness/openness (Neili:اتساع, Abbas:اتساع+باطن), which is one of the cleaner cross-framework confirmations in the dataset.

---

## Section 4: Notable Strong Agreements

### ح — "Inner Expansiveness"

- Jabal: احتكاك، **جفاف**، **باطن**
- Abbas: **اتساع**، **باطن**
- Neili: **اتساع**
- Asim: انتقال (diverges)

باطن is confirmed by Jabal and Abbas. اتساع is confirmed by Abbas and Neili. Three scholars in partial agreement. The picture is: ح signals inward space that opens — the حلقي (pharyngeal) articulation itself mimics a broadening internal passage. Asim's انتقال is too generic to contribute here; this may be the clearest case where Asim's framework loses resolution.

**Consensus reading for scoring:** باطن + اتساع (2 cross-validated features).

### خ — "Rarefying Exit"

- Jabal: **تخلخل**، **جفاف**، غلظ
- Abbas: **تخلخل**، **جفاف**، **خروج**
- Asim: **خروج**، انتقال

تخلخل + جفاف is a near-perfect Jabal-Abbas match. خروج ties Asim and Abbas. خ is the best-confirmed letter in the dataset — three scholars, three shared features across pairings. The خاء is the "dry rarefaction that exits."

**Consensus reading for scoring:** تخلخل + جفاف + خروج (triple cross-validated).

### ذ — "Penetrating Passage"

- Jabal: **نفاذ**، رخاوة، غلظ
- Asim: **نفاذ**، انتقال، التحام
- Abbas: **نفاذ**

All three scholars agree on نفاذ. Abbas's mechanism is إيمائية (articulatory mimesis: the tongue slides between the teeth = penetration). This is textbook confirmation — the phonosemantic content of ذ is نفاذ beyond reasonable doubt.

**Consensus reading for scoring:** نفاذ (unanimous across three scholars).

### س — "Flowing Extension"

- Jabal: **امتداد**، **دقة**، وحدة، حدة
- Asim: **امتداد**، ظهور
- Abbas: **دقة**، **امتداد**

All three agree on امتداد. Jabal and Abbas also agree on دقة. س is the clearest "extension" letter in the system — the long sustained sibilant embodies linear outward flow. This is the most reliable three-way match after ذ.

**Consensus reading for scoring:** امتداد + دقة (both cross-validated).

### ص — "Dense Pure Void" (triple feature match)

- Jabal: نفاذ، **غلظ**، قوة، **خلوص**، **فراغ**
- Abbas: **غلظ**، **خلوص**، **فراغ**
- Asim: انتقال (no overlap)

غلظ + خلوص + فراغ — three features, two scholars, exact match. This is the deepest lexical agreement in the entire dataset. Asim contributes nothing here; his single-feature kinetic entry is too coarse. The emphatic ص carries a paradoxical semantic charge: it is thick (غلظ) yet pure/clear (خلوص) and somehow hollow (فراغ). This triad may be the signature of the emphatic-pharyngeal articulation class generally.

**Consensus reading for scoring:** غلظ + خلوص + فراغ (triple match, highest confidence in dataset).

### ض — "Dense Pressure"

- Jabal: **ضغط**، **كثافة**، غلظ
- Abbas: **ضغط**، **كثافة**
- Asim: إمساك

ضغط + كثافة: exact two-feature match between Jabal and Abbas. The emphatic lateral ض is the "pressure letter" par excellence. Asim's إمساك ("holding/restraint") is semantically adjacent (restrained pressure) but uses different vocabulary.

**Consensus reading for scoring:** ضغط + كثافة (exact Jabal-Abbas match).

### ق — "Deep Force"

- Jabal: تعقد، اشتداد، **قوة**، عمق
- Asim: **قوة**، انتقال
- Abbas: **قوة**

قوة confirmed by all three. This is clean and unsurprising given the uvular plosive's articulatory force. Worth noting that Jabal's عمق adds a spatial dimension (depth) that neither Asim nor Abbas recover — possibly unique to Jabal's lexical analysis.

**Consensus reading for scoring:** قوة (unanimous); عمق as Jabal-only secondary.

### ك — "Double Pair Agreement"

- Jabal: **ضغط**، دقة، امتساك، قطع
- Asim: **تجمع**، احتواء
- Abbas: **ضغط**، تماسك
- Neili: **تجمع**

Two independent scholar pairs agree on two different features: ضغط (Jabal ↔ Abbas) and تجمع (Asim ↔ Neili). The ك letter appears to encode both "cohesive gathering" and "focused pressure" — these are not contradictory but may represent different aspects of the same articulation (the velar stop that binds and cuts simultaneously).

**Consensus reading for scoring:** ضغط (Jabal-Abbas validated) + تجمع (Asim-Neili validated) — both features carry cross-scholar evidence.

---

## Section 5: Notable Divergences

The 8 DIVERGE letters — and what the divergences mean:

### ت — "Four Completely Different Readings"

| Scholar | Reading |
|---------|---------|
| Jabal | ضغط، دقة، وحدة، حدة، إمساك، قطع (6 features — most complex letter in Jabal's system) |
| Asim | قوة (1 feature — gathering of movements toward a new force) |
| Abbas | رخاوة (1 feature — softness/touch, likened to fingertips on cotton) |
| Neili | تجمع (1 feature — gathering of the diverse) |

This is the hardest divergence in the dataset. Four scholars, four different primary categories: pressure/precision (Jabal), force (Asim), softness (Abbas), gathering (Neili). Abbas's رخاوة is opposite in register to Jabal's ضغط.

One interpretation: ت is the most contextually sensitive letter — its phonosemantic content shifts depending on what binary class it pairs with. Jabal's 6-feature reading may be capturing all possible roles simultaneously, while the other scholars each emphasize one face.

**Flag for Yassin:** Should ت be treated as a multi-valent letter with conditional feature activation? Or is one reading wrong?

### د — Intentional Force vs. Structural Containment

- Jabal: احتباس، ضغط، امتداد، طول
- Asim: انتقال، إمساك
- Abbas: غلظ، ثقل، قوة
- Neili: [] (empty — kinetic_gloss describes "intentional organized action")

No lexical overlap. But all four describe something in the domain of bounded, heavy, directed force. This may be a case of genuine vocabulary fragmentation around a single underlying concept. Neili's kinetic_gloss "الفعل المقصود المنظّم" (intentional organized action) is actually the best meta-description — it encompasses Jabal's احتباس, Asim's انتقال القصدي, and Abbas's ثقل.

**Recommendation:** Treat as DIVERGE for the scoring system, but note that all readings converge at the category level on pressure_force + extension_movement.

### ز — Three Incompatible Readings

- Jabal: اكتناز، ازدحام (packed density, crowding)
- Asim: انتقال (generic movement)
- Abbas: تخلخل (rarefaction/vibration, citing "buzz and resonance")

Jabal says dense packing. Abbas says rarefaction/vibration. These are near-antonyms. Asim's انتقال resolves nothing. The auditory quality of ز (voiced buzzing sibilant) is what drives Abbas's تخلخل — he is describing the vibration of the sound. Jabal is describing lexical patterns derived from roots containing ز. They are measuring different things.

**This divergence is methodologically instructive:** Abbas's sensory-mimetic method and Jabal's lexical-pattern method can produce contradictory outputs for the same letter. Flag for theoretical review.

### ع — Near-Synonyms Masquerading as Divergence

- Jabal: التحام، رقة، حدة، رخاوة
- Asim: **ظاهر**، انتقال
- Abbas: عمق
- Neili: **ظهور**

At first glance, four different readings. But Asim's ظاهر and Neili's ظهور are near-synonyms (both: "manifestation/appearance/becoming visible"). The Asim-Neili pair actually agrees. Jabal's التحام (joining/fusion) and Abbas's عمق (depth) point to an internal/connective quality. So there may be two clusters: ظهور/ظاهر (appearance) vs. التحام/عمق (internal depth).

**Flag for Yassin:** The ع may have a ظاهر/باطن duality — Asim and Neili are capturing the ظهور face, while Jabal and Abbas disagree about the باطن face (التحام vs. عمق). These may be complementary rather than competing.

### م، هـ، و، ي

These four show no clear shared features but for different reasons:

- **م**: Jabal's امتساك/استواء/ظاهر vs. Asim's انتقال vs. Abbas's تجمع (from lip closure mimesis) vs. Neili's empty features. Abbas's تجمع is the most mechanistically grounded (bilabial closure = gathering). No cross-scholar agreement.

- **هـ**: Jabal has فراغ/إفراغ/جوف. Abbas has تخلخل/فراغ — فراغ overlaps! This may actually be PARTIAL, not DIVERGE. Flagged as borderline; currently classified DIVERGE because Asim's انتقال/جوف doesn't add cross-validation to Jabal's reading. **Recommend Yassin reconsider to PARTIAL (Jabal-Abbas share فراغ).**

- **و** and **ي**: The weak letters (حروف المد/الليّنة). Abbas explicitly notes these have "شبه معدوم" lexical influence. Jabal's اشتمال/احتواء for و vs. Abbas's تلاصق reflects the fundamental theoretical question about whether و carries semantic weight at all. These divergences may be expected and acceptable.

---

## Section 6: Recommendations

### 1. The 8 STRONG Letters — Use with High Confidence

For ح، خ، ذ، س، ص، ض، ق، ك: use the consensus features as the primary scoring atoms. Confidence level: high. The cross-scholar validation eliminates single-source noise.

Priority for nucleus prediction testing: ص (غلظ+خلوص+فراغ triple match) and خ (تخلخل+جفاف+خروج) — these are the most robust.

### 2. The 12 PARTIAL Letters — Use Jabal as Primary, Flag Shared Feature

For ء، ب، ث، ج، ش، ط، ظ، غ، ف، ل، ن، ر: retain Jabal's full feature set as the primary atomic description. Mark the shared feature (e.g., نفاذ for ف، باطن for ن) as "cross-validated" in the scoring system. The shared feature can carry a confidence bonus in nucleus predictions.

### 3. The 8 DIVERGE Letters — Keep All Readings as Alternatives

For ت، د، ز، ع، م، هـ، و، ي: do not force a single reading. Store all four interpretations and test each independently against binary nucleus predictions to see which scholar's atomic features produce better predictions.

Specific guidance:
- **ت**: Test Jabal's multi-feature set vs. each single-feature reading against root outcomes. This will empirically resolve the theoretical disagreement.
- **ع**: Run Asim+Neili's ظهور cluster and Jabal+Abbas's internal-depth cluster separately against roots with ع in different positions.
- **هـ**: Reclassify to PARTIAL — Jabal and Abbas share فراغ. Yassin should confirm.
- **ز**: Flag as "methodological divergence" — the buzz/vibration (Abbas) vs. dense packing (Jabal) contrast is a data quality issue, not a theoretical one. Jabal's lexical evidence is likely more relevant for the scoring engine.

### 4. Abbas as Primary Validation Scholar

Abbas-Jabal alignment is the strongest in the dataset (15/28 letters, 8 letters with 2+ shared features). Going forward, Abbas should be the first scholar to consult when Jabal's reading needs external validation. His sensory-mimetic mechanism types (إيمائية especially) provide articulatory grounding that complements Jabal's lexical analysis.

### 5. Asim-Neili Vocabulary Normalization (Future Work)

Before measuring true Asim-Neili agreement, a normalization pass is needed: map Asim's kinetic vocabulary (انبثاق → خروج, استبطن → باطن, اندفاع → امتداد etc.) to the canonical feature set. The continues_neili=true flags in Asim's JSONL already identify the letters where Asim explicitly claims to extend Neili — start there. Expected outcome: overlap rises from ~2/10 to 6-7/10.

---

## Appendix: Data Notes

- Jabal's data is sourced from the lexical patterns of the المعجم الاشتقاقي — this is the empirical backbone of LV1. Features are derived from corpus evidence, not theory.
- Abbas's classification types range from يقيناً (certain) for the جوفية letters to "possible earlier origin" for many consonants. The يقيناً entries (ء، ا، و، ي) are mechanistically grounded and most reliable.
- Asim's confidence is uniformly "medium" — his framework is more speculative and his atomic_features were extracted from kinetic glosses that are philosophically rich but semantically diffuse.
- Neili's 10-letter subset has sparse atomic_features (3 letters have empty lists). The kinetic_gloss column is richer and should be used for any Neili-Asim comparison work.
- Anbar's letters will be added to this table in a P2.1b update when P1.3 lands.
