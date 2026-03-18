# Phonetic Merger Reference — LV2 Cross-Lingual Comparison

This document records which Arabic phonemic distinctions each target language has **lost** (merged). Understanding these mergers is critical for correct cognate identification: two Arabic words that are phonemically distinct may have identical reflexes in a target language, and false negatives/positives in cognate benchmarks often trace to unrecognized mergers.

**Machine-readable source:** `phonetic_mergers.jsonl` (same directory)

---

## Notation

| Symbol | Meaning |
|--------|---------|
| A / B → X | Arabic sounds A and B both map to target sound X (merger) |
| A → ∅ | Arabic sound A is dropped entirely |
| A → V | Arabic sound A is vocalized (becomes a vowel onset) |
| (script) | Distinction preserved in writing but lost in speech |

---

## Hebrew (`heb`)

Hebrew and Arabic are sister Semitic languages sharing a large proportion of their consonant inventory, but Hebrew has undergone several mergers that collapse Arabic distinctions.

| Arabic Pair | Merged To | Notes |
|-------------|-----------|-------|
| ع / غ | ע (ayin) | The pharyngeal ʿayn and the velar fricative ghayn both map to Hebrew ayin. No phonemic distinction survives in modern Hebrew. |
| ح / خ | ח (het) | Pharyngeal ḥa and velar kha both collapse to Hebrew het. Classical Hebrew may have preserved the distinction marginally, but it is fully merged today. |
| د / ذ | ד (dalet) | Plain dal and voiced interdental dhal both map to dalet. Hebrew lost the fricative variant entirely. |
| ت / ط | ת / ט | Plain ta → tav (ת); emphatic ṭa → tet (ט). The emphatic–plain distinction is **partially preserved** via a different letter, unlike most other mergers. |
| ث → שׁ | שׁ (shin) | Arabic tha (interdental fricative) regularly corresponds to Hebrew shin. Not a merger of two Arabic sounds but a cross-language sound shift. Example: Arabic ثلاثة → Hebrew שלוש. |
| ص / ض | צ (tsade) | Both emphatic sad and emphatic dad collapse to tsade. The dad was historically a lateral emphatic; its exact Proto-Semitic reflex is debated but both converge to tsade in Hebrew. |
| ظ | צ / ז | Emphatic dha has no direct Hebrew equivalent. It corresponds to tsade (צ) or zayin (ז) depending on the root. |
| س / ش | שׁ / שׂ / ס | Hebrew preserves a shin/sin distinction (שׁ vs שׂ) but it does not map cleanly to Arabic shin/sin. Arabic sin (س) typically → Hebrew sin (שׂ) or samekh (ס); Arabic shin (ش) → Hebrew shin (שׁ). Not a simple merger but a realignment. |
| ق | ק (qof) | **No merger.** Arabic qaf maps cleanly to Hebrew qof; the distinction from kaf (כ) is preserved. |

---

## Aramaic (`arc`)

Aramaic shares the same script as Hebrew (in its square script form) and undergoes largely parallel mergers. Key divergences from Hebrew are noted.

| Arabic Pair | Merged To | Notes |
|-------------|-----------|-------|
| ع / غ | ע (ayin) | Same merger as Hebrew; both map to ayin. |
| ح / خ | ח (het) | Same merger as Hebrew; both map to het. |
| د / ذ | ד (dalet) | Arabic dhal has no separate Aramaic letter; merged to dalet as in Hebrew. |
| ت / ط | ת / ט | Same pattern as Hebrew: plain ta → taw, emphatic ṭa → tet. |
| ص / ض | צ (tsade) | Same merger as Hebrew. |
| ث → ת | ת (taw) | **Aramaic-specific.** Aramaic maps Arabic tha to taw (ת) rather than shin. Example: Arabic ثلاثة vs Aramaic תלתא (tlata). This is a key diagnostic difference from Hebrew. |
| ظ → ט | ט (tet) | **Aramaic-specific.** Aramaic maps emphatic dha to tet more consistently than Hebrew does. |

---

## Ancient Greek (`grc`)

Greek is a separate Indo-European language with no pharyngeal, uvular, or emphatic consonants. Semitic loanwords into Greek (and Proto-Semitic → Proto-IE correspondences) show systematic losses.

| Arabic Sound(s) | Greek Reflex | Notes |
|-----------------|-------------|-------|
| ع | ∅ (dropped) | No pharyngeal series in Greek. Arabic ʿayn is dropped entirely or becomes a vowel onset. Example: Arabic عنبر → Greek ἄμβαρ. |
| غ | ∅ / γ | Ghayn is lost; occasionally rendered as gamma (γ) in loanwords. |
| ح / خ | χ / ∅ | Both pharyngeal ḥa and velar kha collapse to chi (χ) or are dropped. Kha → chi is the more consistent correspondence; ḥa more often drops. |
| ق | κ (kappa) | Uvular qaf maps to velar kappa; the uvular–velar distinction is lost. |
| ط | τ / θ | Emphatic ṭa maps to tau (τ) or theta (θ); pharyngealization is lost entirely. |
| ص | σ (sigma) | Emphatic sad maps to sigma; emphasis lost. |
| ض | δ / σ | Emphatic dad maps variably to delta or sigma; emphasis lost. |
| ث | θ (theta) | Arabic tha (interdental) maps to Greek theta (θ). A strong correspondence in Semitic–Greek cognate pairs; Proto-Semitic interdentals → Greek aspirates. |
| ذ | δ (delta) | Voiced interdental dhal maps to delta; the fricative quality is lost in favor of a plain stop. |
| ظ | δ / σ | Emphatic dha has no Greek equivalent; maps variably; all distinctions lost. |

---

## Latin (`lat`)

Latin, like Greek, has no pharyngeal or emphatic consonants. Most Semitic loans entered Latin via Greek, adding a second layer of phonological reduction.

| Arabic Sound(s) | Latin Reflex | Notes |
|-----------------|-------------|-------|
| ع | ∅ / V | Dropped or becomes a vowel. Example: Arabic عرق → Latin arak (vowel onset). |
| غ | ∅ / g | Dropped or occasionally g; no systematic pattern. |
| ح / خ | h / ∅ | Both map to Latin h or are dropped. Since Classical Latin h was largely silent, even this mapping loses phonetic weight. |
| ق | c / qu | Uvular qaf → velar c/qu. Example: Arabic قيثارة → Latin cithara; Arabic قرطاس → Latin charta. |
| ط | t | Emphatic ṭa → t; pharyngealization lost entirely. |
| ص | s | Emphatic sad → s; emphasis lost. Example: Arabic صفر → Medieval Latin cifra. |
| ض | d | Emphatic dad → d; emphasis lost. |
| ث | t / s / f | No single correspondent; maps variably depending on borrowing period and intermediary language. |
| ذ | d | Voiced interdental dhal → d; fricative quality lost. |
| ظ | d / z | No Latin equivalent; maps variably; all distinctions lost. |

---

## English (`eng`)

English receives Arabic loans via multiple paths, each with different phonological outcomes. The borrowing path determines the reflex.

**Borrowing paths:**
1. Direct Arabic → English (modern technical/cultural borrowings)
2. Arabic → Medieval Latin → English (scientific/scholarly vocabulary)
3. Arabic → Greek → Latin → English (ancient cultural vocabulary)
4. Arabic → Spanish/Italian → English (words entering via Iberian/Mediterranean contact)
5. Proto-Semitic → Proto-Indo-European → Germanic → English (deep cognates, highly debated)

| Arabic Sound(s) | English Reflex | Notes |
|-----------------|---------------|-------|
| ع | ∅ / V | Lost across all borrowing paths. |
| غ | ∅ / g | Lost; occasional g via early Latin path. |
| ح | h / ∅ | Maps to h in direct borrowings; dropped via Latin/French path (where h was already silent). |
| خ | h / k / ch / ∅ | Via Greek path: ch (e.g., Arabic كيمياء → English chemistry); via Latin: h or dropped; via direct borrowing: k. |
| ق | c / k / qu | Example: Arabic قيثارة → English guitar (via Spanish); Arabic قرطاس → English card (via Latin charta). |
| ط | t | Emphatic ṭa → t across all paths; emphasis universally lost. |
| ص | s / z / c | Example: Arabic صفر → English zero (via Arabic → Italian zefiro) or cipher (via Latin cifra). |
| ض | d | Emphatic dad → d; emphasis lost. |
| ث | th / t / s | Direct borrowings may preserve th (English has the interdental fricative); via Latin → t; via Greek → s. |
| ذ | d / th | Most borrowings arrive via Latin/French where dhal had already become d; direct borrowings could map to voiced th. |
| ظ | d / z / ∅ | No English equivalent; all distinctions lost across all paths. |
| ج | j / g / y | Example: Arabic جبر → English algebra (via Medieval Latin); Arabic جيراف → English giraffe (via Italian). |

---

## Persian (`fas`)

Persian is in a unique position: it borrowed Arabic vocabulary wholesale after the Islamic conquest, preserving Arabic letters in the script even when the corresponding sounds were absorbed into Persian phonology. This creates a systematic **script–speech divergence**.

**Key principle:** Persian orthography preserves Arabic distinctions; Persian phonology often does not.

| Arabic Distinction | Script Status | Pronunciation | Notes |
|--------------------|--------------|---------------|-------|
| ع vs غ | Both preserved (ع / غ) | Often merged to glottal stop or dropped | In colloquial Persian both frequently reduce to [ʔ] or ∅; formal speech preserves more distinction |
| ح vs ه | Both preserved in Arabic loans | Both → [h] in Persian | Arabic ḥa (ح) is preserved in script for loans but pronounced as plain h, identical to Persian he (ه) |
| ح vs خ | Both preserved (ح / خ) | ح → [h], خ → [x] | **Persian preserves the خ distinction** in speech; Persian has the velar fricative [x] natively so kha retains its pronunciation |
| ث / س / ص | Three distinct letters in script | All → [s] | The "three s's" of Persian: interdental ث, plain س, and emphatic ص all collapse to [s] in speech |
| ذ / ز / ض / ظ | Four distinct letters in script | All → [z] | The famous **"four z's" of Persian**: voiced interdental ذ, plain ز, emphatic ض, and emphatic dha ظ all collapse to [z] in speech |
| ت vs ط | Both preserved (ت / ط) | Both → [t] | Emphatic distinction lost in pronunciation; orthographic distinction maintained for Arabic loans |
| ق | Preserved (ق) | [q] or [ʔ] | Persian retains uvular qaf orthographically; in formal/classical speech [q] is pronounced; in colloquial Tehran Persian it often shifts to glottal stop [ʔ] |

### Summary: Persian's "merger by pronunciation, distinction by script"

| Pronunciation class | Arabic letters collapsed |
|--------------------|--------------------------|
| [s] | ث س ص |
| [z] | ذ ز ض ظ |
| [t] | ت ط |
| [h] | ح ه |
| [x] | خ (preserved distinctly) |
| [ʔ] / ∅ | ع (in colloquial speech) |

---

## Quick-Reference Cross-Language Merger Matrix

This matrix shows which Arabic consonants are collapsed to a single reflex (or lost) in each target language. "=" means preserved as distinct; "M" means merged with another Arabic sound; "L" means lost/dropped.

| Arabic | Hebrew | Aramaic | Greek | Latin | English | Persian (speech) |
|--------|--------|---------|-------|-------|---------|-----------------|
| ع (ʿayn) | M→ע | M→ע | L | L | L | M→∅/ʔ |
| غ (ghayn) | M→ע | M→ע | L/M→γ | L | L | =(script only) |
| ح (ḥa) | M→ח | M→ח | M→χ/L | M→h/L | M→h/L | M→h |
| خ (kha) | M→ח | M→ח | M→χ | M→h/L | M→h/k | =(x) |
| ق (qaf) | = | = | M→κ | M→c | M→k/c | =(q/ʔ) |
| ك (kaf) | = | = | = | = | = | = |
| ص (sad) | M→צ | M→צ | M→σ | M→s | M→s | M→s |
| ض (dad) | M→צ | M→צ | M→δ | M→d | M→d | M→z |
| ط (tta) | =(ט) | =(ט) | M→τ | M→t | M→t | M→t |
| ظ (dha) | M→צ/ז | M→ט | L/M | L/M | L | M→z |
| ث (tha) | M→שׁ | M→ת | M→θ | M→t/s | M→th/t | M→s |
| ذ (dhal) | M→ד | M→ד | M→δ | M→d | M→d | M→z |
| ش (shin) | =(שׁ) | = | M→σ/∅ | M→s | = | = |
| س (sin) | =(שׂ/ס) | = | M→σ | M→s | = | M→s |

Legend: = preserved, M merged, L lost

---

## Using This Table in LV2 Cognate Discovery

1. **Benchmark construction:** When building gold pairs between Arabic and a target language, check this table to confirm the expected phonetic correspondence is a valid merger and not a false cognate.

2. **Scoring adjustment:** The `GenomeScorer` can use merger mappings to allow cross-lingual matches where the merger is expected (e.g., Arabic عين and Hebrew עין should score high despite ع → ע substitution, because this is a documented merger).

3. **False negative prevention:** If an Arabic root contains ح and the candidate Hebrew root contains ח, do not penalize the mismatch between ح and ח; consult this table to confirm they are expected merger equivalents.

4. **Borrowing path disambiguation (English):** For English cognate candidates, the expected reflex depends on borrowing path. Track path metadata in benchmark annotations when possible.
