# Phonetic Laws Reference
**Project:** Juthoor Linguistic Genealogy — LV2 CognateDiscovery
**Date:** 2026-03-27
**Dataset:** 861 Arabic-English pairs from "Beyond the Name" (consonant_correspondence_matrix.json)

---

## 1. Overview

Phonetic laws describe systematic, rule-governed sound correspondences between languages that share a common ancestor or sustained contact. They are not random approximations — they are patterned shifts where a specific phoneme in Language A predictably maps to a specific phoneme (or cluster) in Language B.

For Arabic↔English cognate discovery, phonetic laws serve three purposes:

1. **Scoring:** Given an Arabic root and an English word, a phonetic law scorer can compute how well the English consonant skeleton matches the projected Arabic form. A high match score is evidence of cognate relationship.
2. **Projection:** By applying known sound laws, we can generate all plausible English realisations of an Arabic root and search for matches in large corpora.
3. **Disambiguation:** Many Arabic consonants that are phonetically distinct have merged in European languages. Knowing which Arabic letters collapse to the same English sound prevents over-penalising semantically strong candidates for superficial phonetic differences.

The Arabic consonantal root system provides maximum phonetic resolution. English (via Proto-Germanic → Old English → Middle English → Modern English) and its Latin/Greek borrowings represent the collapsed end: many Arabic distinctions — pharyngeals vs. velars, emphatics vs. plain dentals, emphatic vs. plain sibilants — are flattened to single English phonemes.

---

## 2. Khashim Sound Laws

The following 9 correspondences are drawn from LV1 `factory/sound_laws.py`, encoding the scholarly work of Khashim on Arabic-Latin-English phoneme mappings. Confirmation status is based on 861 pairs from the "Beyond the Name" dataset (6/9 laws directly confirmed; 3 laws require transliteration data not available in this dataset).

| # | Arabic | Transliteration | English Targets | Dataset Status | Primary Observed |
|---|--------|-----------------|-----------------|----------------|-----------------|
| 1 | ف | f | f, p | Confirmed | f (39), p (31) |
| 2 | ق | q | q, k, c, g | Confirmed — primary: c | c (53), g (21), k (10) |
| 3 | ش | sh | sh, s | Confirmed | s (35) |
| 4 | ع | ʿ | (deleted), h | Confirmed — primary: deletion | O (108), h (15) |
| 5 | غ | gh | gh, g | Confirmed | O/deletion (18), g (11) |
| 6 | خ | kh | kh, h, g | Confirmed | h (10), c (8), g (4) |
| 7 | ط | t (emphatic) | t | Insufficient translit data | — |
| 8 | ص | s (emphatic) | s | Insufficient translit data | — |
| 9 | ح | h (pharyngeal) | h, k, c | Insufficient translit data | — |

**Notes:**
- "O" in observed distributions denotes deletion/zero realisation (the Arabic consonant leaves no English reflex).
- ع is the most consistent law: 87.8% deletion rate (108/123 occurrences). When ع does surface, it becomes English h.
- ق shows a surprising primary realisation as English c (Latin c/k) rather than q, reflecting the Latin pathway through which most Arabic loanwords entered English.
- The 3 emphatic laws (ط, ص, ح) are logically sound but cannot be confirmed from this dataset because the pairs rely on Arabic transliteration which is absent from most entries.

---

## 3. Mined Correspondence Table

Top 20 Arabic→English consonant mappings by frequency, mined from 861 pairs (3,461 total consonant alignments). Source: `consonant_correspondence_matrix.json`.

| Rank | Arabic | English | Count | Total (Arabic) | Weight |
|------|--------|---------|-------|----------------|--------|
| 1 | ر | r | 199 | 305 | 0.652 |
| 2 | ل | l | 159 | 349 | 0.456 |
| 3 | ع | (deleted) | 108 | 123 | 0.878 |
| 4 | ت | t | 98 | 163 | 0.601 |
| 5 | م | m | 89 | 175 | 0.509 |
| 6 | ن | n | 86 | 172 | 0.500 |
| 7 | س | s | 85 | 152 | 0.559 |
| 8 | ي | (deleted) | 68 | 220 | 0.309 |
| 9 | ب | b | 56 | 165 | 0.339 |
| 10 | ق | c | 53 | 136 | 0.390 |
| 11 | د | d | 49 | 123 | 0.398 |
| 12 | ل | (deleted) | 43 | 349 | 0.123 |
| 13 | ج | g | 41 | 103 | 0.398 |
| 14 | ر | (deleted) | 40 | 305 | 0.131 |
| 15 | ف | f | 39 | 125 | 0.312 |
| 16 | ن | (deleted) | 39 | 172 | 0.227 |
| 17 | ب | p | 37 | 165 | 0.224 |
| 18 | ش | s | 35 | 71 | 0.493 |
| 19 | ف | p | 31 | 125 | 0.248 |
| 20 | ك | c | 29 | 65 | 0.446 |

**Key observations:**
- ر→r is the most frequent single correspondence (199 occurrences), and r is highly stable.
- ع→(deleted) has the highest weight (0.878), meaning deletion is by far the most reliable prediction for ع.
- Deletion (marked "O") appears prominently for weak consonants ل, ي, ن, ر — these frequently drop in European phonology.
- ق maps primarily to c (Latin c) not k, reflecting the dominant Latin/French entry channel.

---

## 4. Five Major Merger Groups

These groups capture the most consequential phonological collapses. Source: `phonetic_law_weights.json` (861 pairs analysed).

### 4.1 Guttural Collapse — weight 0.886
**Arabic letters:** ع ح خ غ
**English targets:** h, (deleted), k, g
**Frequency:** 171/193 occurrences (88.6%)
**Observed distribution:** deletion (129), h (25), g (15), k (2)

Arabic has four distinct pharyngeal/velar fricatives that European languages cannot produce. All four collapse:
- ع (voiced pharyngeal) → almost always deleted; occasionally → h
- ح (voiceless pharyngeal) → h (when present) or deleted
- خ (voiceless velar fricative) → h, g, or c
- غ (voiced velar fricative) → g or deleted

This is the single most important merger for Arabic-English cognate discovery. Many Arabic roots appear unrecognisable in English because the prominent ع at the start has simply vanished.

### 4.2 Emphatic Dental Collapse — weight 0.754
**Arabic letters:** ط ت ذ ظ
**English targets:** t, d
**Frequency:** 132/175 occurrences (75.4%)
**Observed distribution:** t (102), deletion (19), d (11)

Arabic distinguishes plain ت, emphatic ط, interdental ذ, and emphatic interdental ظ. English collapses all four to t/d (with ط→t being the most common).

### 4.3 Velar/Uvular Merge — weight 0.727
**Arabic letters:** ق ك ج
**English targets:** k, c, g, j
**Frequency:** 221/304 occurrences (72.7%)
**Observed distribution:** c (93), g (65), deletion (39), k (17), j (7)

Arabic uvular stop ق, velar stop ك, and palatal affricate ج all merge to the English k/c/g cluster. The dominant English realisation is c (reflecting Latin orthography), not k. ج often surfaces as g.

### 4.4 Emphatic Sibilant Collapse — weight 0.707
**Arabic letters:** ص س ز ش
**English targets:** s, z, c
**Frequency:** 183/259 occurrences (70.7%)
**Observed distribution:** s (129), deletion (23), c (20), z (11)

Arabic emphatic ص, plain س, fricative ز, and palatal ش all merge to s in English. ز sometimes retains z. ش occasionally becomes c (when via Latin/French).

### 4.5 Labial Group — weight 0.649
**Arabic letters:** ب ف م و
**English targets:** b, f, p, m, v, w
**Frequency:** 386/595 occurrences (64.9%)
**Observed distribution:** m (98), p (71), b (64), deletion (63), f (48), v (29), w (13)

Arabic labials are relatively well-preserved compared to gutturals. ب→b/p, ف→f/p, م→m, و→w/v. The relatively lower weight reflects the wide spread of targets and frequent deletion of و (semivowel).

---

## 5. Morpheme Correspondences

Prefix and suffix patterns extracted from the 861-pair dataset. Source: `morpheme_correspondences.json`.

### Suffixes

| English Suffix | Arabic Cognate | Meaning | Frequency | Example Words |
|----------------|----------------|---------|-----------|---------------|
| -er | ار | doer/agent | 41 | ossifier, father, finger, cider |
| -al | ال | relating to | 21 | funeral, heal, cathedral, oval |
| -or | ار | doer/agent | 17 | vapor, matador, corridor, motor |
| -ous | وص | having quality | 13 | famous, furious, anonymous |
| -tion | ان | state/action | 12 | auction, solution, nation, friction |
| -logy | لغه | language/science | 9 | sinology, meteorology, carpology |
| -ology | لغه | language/science | 8 | tautology, etiology, semiology |
| -ive | يف | tending to | 6 | arrive, negative, captive, archive |
| -sion | ان | state/action | 2 | mansion, illusion |
| -ist | اسط | one who | 2 | moist, wrist |
| -ism | اسم | doctrine/practice | 2 | narcissism |
| -ify | ايف | to make | 2 | ossify, mollify |
| -less | ليس | negation | 1 | ruthless |
| -ment | ما | result of action | 1 | filament |
| -ence | ان | state/quality | 1 | science |
| -ize | يز | to make | 1 | galvanize |

### Prefixes

| English Prefix | Arabic Cognate | Meaning | Frequency | Example Words |
|----------------|----------------|---------|-----------|---------------|
| in- | عن | negation/in | 10 | infant, innocent, inspire, invest |
| re- | رد | return/repeat | 8 | rest, region, resin, rein |
| de- | د | down/away | 5 | decor, deal, death, dear |
| es- | ءقص | exclude/remove | 3 | escalator, esther, estivate |
| im- | عن | negation/in | 3 | immunization, immerse, imitate |
| auto- | ذات | self | 3 | autoclave, autonomy, autogenous |
| ex- | ءقص | exclude/remove | 2 | expire, excuse |
| pre- | قبل | before | 2 | pregnant, preach |
| con- | كن | together | 2 | conquer, constantine |
| com- | كم | together | 2 | comet, comic |
| sub- | صب | pour down/descend | 1 | submarine |
| un- | عن | negation | 1 | uncle |
| dis- | ذيص | apart/away | 1 | disease |
| geo- | جو | earth | 1 | geometry |

**Note on morpheme scoring:** When a known English prefix or suffix matches an entry in this table, `PhoneticLawScorer` awards a +0.05 bonus. The stem (after stripping the affix) is scored independently for a potentially higher base match.

---

## 6. Exemplary Pairs

Ten high-quality pairs that demonstrate the laws in action. Drawn from the "Beyond the Name" dataset.

### 6.1 Left ← لفت (l-f-t)
Direct consonant preservation: ل→l, ف→f, ت→t. Perfect 3-consonant match with no deletion or merger. Demonstrates that when phonetic distance between Arabic and English is short, roots survive intact.

### 6.2 Dam ← دأم (d-ʔ-m → d-a-m)
Hamza (ء/أ) deletion: Arabic hamza is a glottal stop that consistently vanishes in English. دأم → dam: د→d, أ→(deleted), م→m. Hamza deletion is the most common form of vowel/semi-consonant erasure.

### 6.3 Ruthless ← رثى + ليس (ruth + less)
Compound morpheme analysis: English "ruth" (archaic "pity") ← Arabic رثى (to lament/pity). The suffix "-less" ← Arabic ليس (negation particle: "is not"). This pair demonstrates both the phonetic law (ر→r, ث→th) and the suffix morpheme correspondence (-less ↔ ليس).

### 6.4 Fog ← فيج (f-y-j → f-g)
Two rules at once: ف→f (direct), ي→(deleted), ج→g. The medial weak consonant ي is lost; ج undergoes the velar/palatal merger to g. The dataset notes explicit orthographic and semantic similarity between فيج and fog.

### 6.5 Curse ← قرص (q-r-s → c/k-r-s)
Velar/uvular merge + emphatic sibilant collapse: ق→c (Merger Group 3), ر→r (preserved), ص→s (Merger Group 4). The emphatic realisation of ق as c (not k) is characteristic of the Latin pathway.

### 6.6 Submarine ← صب + مار (sub + marine)
Prefix morpheme correspondence: English prefix sub- ← Arabic صب ("to pour down, to descend"). The prefix meaning aligns semantically and phonetically: ص→s (emphatic sibilant collapse), ب→b (labial group). Marine ← Arabic مار (one who goes through water).

### 6.7 Infant ← إن + فاه (in- + fāh)
Prefix + root decomposition: English prefix in- (negation) ← Arabic عن/إن. Root fāh ← Arabic فاه ("to speak, to utter"). Infant = "one who does not speak" — matching the Latin etymology (in + fans = not speaking). ف→f, ا→(vowel), ه→(deleted).

### 6.8 Ruthless ← رثى + ليس
See 6.3 above. Repeated here as the canonical example of the -less ↔ ليس morpheme correspondence.

### 6.9 Hydrogen ← عدر + جن (ʿ-d-r + j-n → hydro + gen)
Guttural collapse + velar merge: ع→(deleted, with h surfacing as aspirate in "hydro"), د→d, ر→r. The second element جن (spirit, substance) → English suffix -gen (generator/source). This is a compound etymological hypothesis requiring multi-hop analysis through Greek.

### 6.10 Surgery ← سرّاج (s-r-j → s-r-g-r-y)
Sibilant + velar: س→s (emphatic sibilant), ر→r (preserved), ج→g (velar/palatal merge). The doubling of ر (shaddah) in Arabic corresponds to the doubled consonant cluster in the English medial syllable. Route through Latin *chirurgia* → Old French → English.

---

*Source files: `data/processed/consonant_correspondence_matrix.json`, `data/processed/phonetic_law_weights.json`, `data/processed/morpheme_correspondences.json`*
*Dataset: 861 pairs, 3,461 consonant alignments, mined 2026-03-27*
