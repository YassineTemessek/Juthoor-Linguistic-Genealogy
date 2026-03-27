# Etymology Linking Methodology: How Arabic Words Connect to English/European Words

## The 14 Linking Methods (from 863 studied examples)

Understanding these patterns is the foundation for automated cognate discovery. Each method represents a different WAY that an Arabic root can surface in a European language.

---

## METHOD 1: Direct Consonant Skeleton Match
**The simplest and most common pattern (~30% of pairs)**

The Arabic root's consonants map directly to the English word's consonants, with known sound shifts.

| Arabic | English | Consonants | Sound shift |
|--------|---------|------------|-------------|
| لفت (laft) | left | l-f-t → l-f-t | Exact match |
| دأم (da'm) | dam | d-'-m → d-m | Hamza deletion |
| فرو (farw) | fur | f-r-w → f-r | Waw drops |
| شبه (shabah) | shape | sh-b-h → sh-p | ب→p, ه drops |
| قرص (qaraṣ) | curse | q-r-ṣ → c-r-s | ق→c, ص→s |

**Key principle:** Arabic has MORE consonant distinctions. European languages MERGE them:
- ق/ك both → K/C
- ع/ح/خ/غ all → H or nothing
- ص/س both → S
- ط/ت both → T

---

## METHOD 2: Morphological Decomposition (Compound Breakdown)
**Break a long English word into prefix + root + suffix, match each part (~25%)**

### Example: SUBMARINE
- sub- = صب (ṣabb = pour down, descend)
- marine = مار (mār = sea flowing, waves)
- Combined: "descending into the sea"

### Example: INNOCENT
- in- = إن النافية (in = negation, "not")
- nocent = نخر (nakhr = decay, death, harm)
- Combined: "not causing harm" = بريء

### Example: HYDROGEN
- hydro = عدر ('adr = heavy rain, abundant water)
- -gen = جن (jann = produce, generate)
- Combined: "water-producer"

### Example: RUTHLESS
- ruth = رثى (rathā = to feel pity, compassion)
- -less = ليس (laysa = is not)
- Combined: "without compassion" = قاسٍ

**Recurring morpheme patterns:**

| Morpheme | Arabic origin | Meaning | Examples |
|----------|--------------|---------|----------|
| -gen | جن | produce/birth | hydrogen, nitrogen, oxygen, genesis |
| -less | ليس | is not | ruthless, hopeless, meaningless |
| -logy | لغة | language/science | zoology, osteology, sinology |
| sub- | صب | pour down | submarine, submerge |
| ex- | إقصاء | exclude | escape, expire, excuse |
| in-/im- | إن النافية | not | infant, innocent, impossible |
| re- | ردّ | return/repeat | rewrite, region, rest |
| auto- | ذات | self | autonomy, autoclave |
| pre- | قبل | before | pregnant, preach |
| -tion | ان | state/action | nation, friction, auction |
| -er/-or | ار | doer/agent | slaughter, dictator |
| -al | ال | relating to | funeral, animal, deal |

---

## METHOD 3: Multi-Hop Chain Etymology
**Arabic → Latin/Greek → French → English, tracing the FULL path (~15%)**

### Example: CHAIN
- Arabic قطين (qaṭīn = captive, bound, settled)
- → Latin catena (catēna = chain, fetter) — ق→c, ط→t
- → Old French chaeine
- → English chain

### Example: SEWER
- Arabic إقصاء (iqṣā' = exclusion) + عقّ ('aqq = bitter water)
- → Gaelic-Romance *exaquaria (ex + aqua = out + water)
- → Old French esseveur
- → English sewer

### Example: CANVAS
- Arabic قنب (qanab = hemp)
- → Greek kannabis
- → Latin cannabis
- → Anglo-French canevaz
- → English canvas

**Key insight:** The word may look NOTHING like Arabic at the end of 3-4 hops, but each hop follows known phonetic rules.

---

## METHOD 4: Semantic Drift + Phonetic Match
**Same sound, meaning shifted over centuries (~10%)**

### Example: SAD
- Arabic سدّ (sadd = to fill, block, stuff)
  - "سدّت منافسه" = his appetite was blocked from overeating
- Old English sæd = "satisfied, full, sated"
- Then meaning shifted: "overfull" → "weary" → "unhappy"
- Modern English: sad = unhappy

### Example: FRUIT
- Arabic فرات (furāt = extremely sweet, fresh)
- → Latin fructus (enjoyment, delight from produce)
- → Old French fruit
- Modern: fruit = sweet produce

### Example: HAPPY
- Arabic حظّ (ḥaẓẓ = luck, fortune)
- Old English hap = luck
- Then: "lucky" → "fortunate" → "joyful"
- حرف ظ → p (documented in Sicilian/Morisco records: ظفر → Pafar)

**Key insight:** The ORIGINAL Arabic meaning often matches the OLD English meaning, not the modern one. You must check historical definitions.

---

## METHOD 5: Guttural Deletion (The Khashim Core Rule)
**Arabic gutturals (ع ح خ غ) disappear in European languages**

This is THE most systematic pattern. Arabic has 4 pharyngeal/velar consonants that European languages cannot pronounce:

### ع (Ain) → NOTHING
| Arabic | English | What happened |
|--------|---------|---------------|
| عمّ ('amm) | uncle | ع deleted, Old English eam = عمّ |
| عدر ('adr) | hydro | ع → h (partial) |
| عصّ ('aṣṣ) | ossify | ع deleted |

### ح (Ḥa) → H or nothing
| Arabic | English | What happened |
|--------|---------|---------------|
| حربة (ḥarba) | harpoon | ح → h |
| حيل (ḥayl) | heal | ح → h |
| حظّ (ḥaẓẓ) | happy | ح → h |

### خ (Kha) → H, K, or CH
| Arabic | English | What happened |
|--------|---------|---------------|
| خليفة (khalīfa) | caliph | خ → c |
| خطاف (khaṭṭāf) | hook | خ → h |

### غ (Ghayn) → G
| Arabic | English | What happened |
|--------|---------|---------------|
| غزال (ghazāl) | gazelle | غ → g |
| غارة (ghāra) | guerrilla | غ → g |

**For discovery:** When matching Arabic→English, ALWAYS try deleting ع and converting ح→h, خ→k, غ→g.

---

## METHOD 6: Emphatic Collapse
**Arabic emphatic consonants lose their emphasis**

| Arabic emphatic | Becomes | Example |
|----------------|---------|---------|
| ص (ṣād) | s | صري → serum |
| ط (ṭā') | t | طاولة → table |
| ض (ḍād) | d | ضرر → damage (via Latin) |
| ظ (ẓā') | z, d, or p! | ظفر → Pafar (Sicilian records) |

The ظ→p shift is rare but documented: Morisco scribes mapped ظ to p because they had no better option.

---

## METHOD 7: Consonant Metathesis (Order Reversal)
**Consonants swap positions during transfer (~3%)**

### Example: LEG
- Arabic رجل (r-j-l = leg)
- Written right-to-left: ل-ج-ر
- Read left-to-right by foreign scribe: l-g-r → leg
- The author explains: early writing had no fixed direction

### Example: SHOVEL
- Arabic رفش (r-f-sh = shovel)
- Reversed: sh-f-r → shovel (with r→l)

**Key insight:** Metathesis happens when scripts with opposite writing directions interact, or when words pass through oral transmission.

---

## METHOD 8: Dialectal Variant as Source
**A specific Arabic dialect pronunciation matches the European word**

### Example: YARD
- Standard Arabic: جريد (jarīd = stripped palm frond, stick)
- Gulf dialect: يَرد (yard) — because Gulf Arabic pronounces ج as Y
- Written in Latin letters: y-a-r-d = yard!

### Example: GIVE
- Standard Arabic: جاب (jāb = bring)
- Levantine dialect: "جيب لي" (jīb lī = bring me = give me)
- English: give, gave — g↔j, v↔b

### Example: WHAT
- Moroccan Arabic: واش (wāsh = what?) from "أيّ شيء"
- German: was = what
- English: what

**Key insight:** Don't just check Classical Arabic. Check dialects — Gulf, Levantine, Moroccan, Egyptian. Each preserved different archaic features.

---

## METHOD 9: PIE Root = Arabic Root
**The Proto-Indo-European "reconstruction" matches an actual Arabic word**

### Example: FOAL
- PIE *pulo- = "small animal"
- Arabic فِلو (filw) = young horse (from Fiqh al-Lugha by al-Tha'ālibī)
- F↔P interchange (labial shift)
- The PIE "reconstruction" IS the Arabic word with a p/f swap

### Example: ACCIDENT
- PIE *kad- = "to fall"
- Arabic قدر (qadr) = fate, destiny, what befalls
- Latin cadere = to fall → accidentem → accident

**Key insight:** Many PIE reconstructed roots are simply Arabic roots in disguise. The asterisk (*) means "unattested" — but Arabic preserves the word.

---

## METHOD 10: Functional Object Naming
**Both languages named the same thing by its function**

### Example: HARPOON
- Arabic حربة (ḥarba) = pointed weapon for hunting/stabbing
- European harpoon = pointed weapon for whale hunting
- Both = "the pointed thing you stab with"

### Example: RODEO
- Arabic روّض (rawwaḍ) = to tame, break (a horse)
- Spanish rodeo = horse-riding skill show
- Both = "the act of taming/controlling animals"

---

## METHOD 11: Article Absorption
**The Arabic "ال" (al-) gets absorbed into the European word**

| Arabic | European | The "al-" became |
|--------|----------|-------------------|
| الكحول (al-kuḥūl) | alcohol | "al" kept |
| الجبر (al-jabr) | algebra | "al" kept |
| الحنّة (al-ḥinna) | alkanet | "al" kept |
| القُسط (al-qusṭ) | costus | "al" dropped |

Sometimes the article is kept (alcohol, algebra), sometimes dropped (costus, chemistry from كيمياء).

---

## METHOD 12: Sound Shift + Semantic Extension
**One Arabic sound shifts AND the meaning extends**

### Example: CHAIR
- Arabic كرسي (kursī = chair)
- K→Ch shift (same as Karl→Charles, كشكشة)
- Chair = ch-a-i-r vs kursī = k-r-s-ī
- Also: kata (Greek, = قعد "sit down") → cathedra → chair

### Example: ALSO
- Arabic كلّه سواء (kulluh sawā' = all the same)
- Old English eallswa = "wholly so"
- all = كل (with k dropped), so = سواء
- Modern: also = أيضاً

---

## METHOD 13: Cross-Semitic Triangulation
**Use Hebrew/Aramaic as intermediate evidence**

### Example: ANONYMOUS
- Greek an- (negation) + onyma (name)
- Hebrew אין (ain = does not exist) — matches an-
- Arabic إن النافية (negation) — matches an-
- Greek → Hebrew → Arabic all share the negation prefix

### Example: ZOO
- Greek zoion (animal)
- Originally pronounced Yoion (J→Z shift documented in Greek)
- Arabic حيوان (ḥayawān = animal)
- ح→ي substitution documented in Banu Namir dialect
- So: حيوان → يويون → zoion → zoo

---

## METHOD 14: Positional Consonant Importance
**Position 1 (first consonant) carries the most weight**

From LV1 Research Factory (Hypothesis H8): The first consonant of an Arabic root is the "anchor" — it defines the semantic field. The third is the "modifier."

This means:
- When the FIRST consonant matches between Arabic and English, it's strong evidence
- When only the LAST consonant matches, it's weak evidence
- Position weights: 1st = 1.5×, 2nd = 1.0×, 3rd = 0.7×

### Example: كتب (k-t-b = write)
- Position 1 (ك=k): defines the action domain
- Position 2 (ت=t): specifies the manner
- Position 3 (ب=b): modifies the quality
- If English word starts with K/C sound and has a T → strong match

---

## Summary: What Makes a Good Link?

A convincing Arabic→English etymology link has:

1. **Phonetic match** — consonant skeletons align after applying known sound laws
2. **Semantic match** — meanings overlap (check HISTORICAL meaning, not just modern)
3. **Documented path** — intermediate languages (Latin, Greek, French) are identified
4. **Dialect evidence** — an Arabic dialect preserves the pronunciation closer to the European form
5. **PIE confirmation** — the reconstructed PIE root matches the Arabic root
6. **Cross-Semitic support** — Hebrew/Aramaic has a cognate that bridges the gap

A WEAK link has only one of these. A STRONG link has 3+.
