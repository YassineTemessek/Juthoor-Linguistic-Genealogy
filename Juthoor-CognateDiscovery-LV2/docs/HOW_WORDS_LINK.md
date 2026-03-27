# How Arabic and English Words Link: Patterns from Beyond the Name

**Based on:** 866 etymology pairs from Mazen Hammoude's "Beyond the Name" research
**Intermediate languages:** Latin (241 pairs), French (202), Greek (125), German (114), Old English (92)

## Pattern 1: Direct Consonant Skeleton Match

The simplest link — Arabic consonants directly correspond to English consonants.

| Arabic | Translit | English | Mechanism |
|--------|---------|---------|-----------|
| قرص (qrs) | q-r-s | curse | q→c, r→r, s→s |
| عند ('nd) | '-n-d | end | '→silent, n→n, d→d |
| ثور (twr) | th-w-r | steer | th→st, w→silent, r→r |
| قرن (qrn) | q-r-n | horn | q→h (via intermediate), r→r, n→n |

**Computational method:** `direct_skeleton`, `position_weighted`

## Pattern 2: Guttural Deletion (ع/غ/ح/خ → silent/h)

Arabic pharyngeal consonants are systematically deleted in English.

| Arabic | Translit | English | Mechanism |
|--------|---------|---------|-----------|
| عند ('nd) | '-n-d | end | ع deleted |
| عصّ ('s) | '-s | ossify | ع deleted, via Latin |
| عقل ('ql) | '-q-l | equal | ع deleted, q→q→c |

**Computational method:** `guttural_projection`
**Empirical rate:** 88% deletion for ع (strongest single correspondence)

## Pattern 3: Article Absorption (al- → English prefix)

The Arabic definite article ال becomes part of the word.

| Arabic | Full Form | English | Notes |
|--------|----------|---------|-------|
| كحل (kuhl) | الكحل (al-kuhl) | alcohol | Meaning shifted: antimony → spirits |
| جبر (jabr) | الجبر (al-jabr) | algebra | Mathematical term |
| قلي (qali) | القلي (al-qali) | alkali | Chemical term |
| مخزن (makhzan) | المخزن (al-makhzan) | magazine | Storage → publication |

**Computational method:** `article_detection`
**Precision:** Near-perfect when detected

## Pattern 4: Multi-Hop via Latin/Greek/French

Words travel Arabic → Latin/Greek → French → English, changing at each step.

| Arabic | Latin/Greek | French | English |
|--------|-----------|--------|---------|
| صفر (sifr) | zephirum | zéro | zero |
| قطن (qutn) | cottō | coton | cotton |
| زفرة (zfra) | spiritus | esprit | spirit |
| قميص (qamis) | camisia | chemise | chemise |

**Computational method:** `multi_hop_chain`
**Best precision:** 3.4% (highest among all methods)

## Pattern 5: Bilabial Exchange (ب↔p, ف↔f↔v)

Arabic labials freely alternate with English labials.

| Arabic | English | Shift |
|--------|---------|-------|
| ب (b) → p | بيت → booth | b→b preserved |
| ب (b) → p | بحر → "piscine" via Latin | b→p voiced→voiceless |
| ف (f) → p | فرس → "palfrey" via Latin | f→p labial shift |
| ف (f) → v | ف → v in intervocalic | f→v lenition |

**Empirical rate:** ب→b 34%, ب→p 22% (nearly equal!)

## Pattern 6: Emphatic Collapse (ص/ض/ط/ظ → s/d/t/z)

Arabic emphatic consonants lose pharyngealization.

| Arabic | English | Shift |
|--------|---------|-------|
| صبر (sabr) | super | ṣ→s |
| طريق (tariq) | track | ṭ→t |
| ضرب (darb) | drub | ḍ→d |

**Computational method:** `emphatic_collapse`

## Pattern 7: Morpheme Decomposition

English prefixes/suffixes obscure the shared stem.

| English | Decomposition | Stem | Arabic Match |
|---------|--------------|------|-------------|
| inscription | in-scrip-tion | scrip | كتب (ktb) → s-c-r-p |
| submarine | sub-mar-ine | mar | مر (mr) |
| astronomy | astro-nom-y | nom | نم (nm) |

**Computational method:** `morpheme_decomposition`

## Pattern 8: Semantic Drift

The meaning changes over time but the consonant link persists.

| Arabic | Arabic Meaning | English | English Meaning | Shift |
|--------|---------------|---------|----------------|-------|
| كحل | antimony powder | alcohol | spirits | cosmetic → chemistry |
| مخزن | warehouse | magazine | publication | storage → information |
| أدمرال | navy commander | admiral | navy officer | preserved meaning |

## Key Phonetic Rules (from the research)

1. **ر↔ل (r↔l):** Common exchange ("إبدال الراء باللام")
2. **س↔ش (s↔sh):** Sibilant variation ("إبدال السين شيناً")
3. **ب↔ف (b↔f/p):** Bilabial cluster ("إبدال الفاء والباء")
4. **ح→h:** Pharyngeal weakening
5. **ق→c/k:** Uvular → velar shift
6. **ع→silent:** Pharyngeal deletion (88%)
7. **ن↔م (n↔m):** Nasal exchange

## Implications for the Discovery Pipeline

The scorer successfully detects patterns 1-7 computationally. The MRR null model confirms it ranks real cognates 1.98x higher than random (significant). The challenge is RETRIEVAL — generating a manageable candidate set from 37K Arabic × 15K English = 555M potential pairs.

**Architecture:** Embedding retrieval (BGE-M3) → MultiMethodScorer reranking → Gloss similarity filter → Anchor classification
