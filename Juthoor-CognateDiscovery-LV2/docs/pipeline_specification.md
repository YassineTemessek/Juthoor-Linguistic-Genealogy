# Juthoor LV2 Reverse Discovery — Pipeline Specification

**Version:** 1.0
**Date:** 2026-03-27
**Audience:** External reviewers, AI assistants, domain specialists
**Purpose:** Complete description of the pipeline — how it works, why each decision was made, and where help is needed.

---

## 1. Project Overview

**Juthoor** (جذور) means "roots" in Arabic. The project is a computational linguistics research engine testing whether Indo-European languages share deep etymological connections to the Arabo-Semitic root system.

### The Core Hypothesis

Arabic is not claimed to be the historical ancestor of Greek or Latin. The claim is more subtle: the **consonant skeleton system** — the triconsonantal root (جذر ثلاثي) that underlies Arabic morphology — may represent a deeper organizational principle shared across language families, one that predates the divergence documented in mainstream historical linguistics.

Under this model, each Arabic root is a **semantic atom**: a three-consonant cluster bound to a core concept that generates a family of words through templated vowel patterns. For example:

- ك-ت-ب (k-t-b) → كتب (to write), كتاب (book), كاتب (writer), مكتب (office)
- ع-ل-م (ʿ-l-m) → علم (to know), عالم (world/scholar), علوم (sciences)

The hypothesis is that cognate consonant skeletons appear in Indo-European words with semantically related meanings — not by coincidence, not by borrowing, but because both families preserve fragments of the same deep ancestral system.

### Why Arabic Has Maximum Phonetic Resolution

Arabic distinguishes 28 consonant phonemes, including:
- Four pharyngeal/velar fricatives (ع ح خ غ) absent from all IE languages
- Three emphatic consonants (ص ط ض) with no IE equivalents
- A uvular stop ق distinct from the velar ك

When Arabic roots map to IE words, the "missing" Arabic consonants are either deleted or merged. The pipeline treats Arabic as the **high-resolution original** and IE languages as lower-resolution projections. This is not a claim about historical direction — it is a signal-processing choice: Arabic provides the most information per root.

### What This Project Is Not

- It does not claim Arabic is the mother of all languages
- It does not use LLMs as judges (trained on mainstream linguistics, they reject the hypothesis by default)
- It does not rely on PIE reconstruction as ground truth (PIE itself is a reconstruction that could be wrong)
- It does not require all cognate connections to be direct — many pass through Latin, Greek, or Aramaic intermediaries

---

## 2. The Reverse Discovery Method

### 2.1 Motivation

The standard discovery approach is Arabic → Target: for each Arabic root (37K), score against each target word (up to 884K for Latin). This produces N × M pairs — up to 33 billion comparisons, completely infeasible at full scale.

**Reverse discovery** inverts this: start from each target word and trace it back to Arabic roots.

### 2.2 Pipeline Overview

```
Target Word (e.g., Latin "september")
    │
    ├─ Morpheme Decomposition → ["september", "septem", "sept"]
    │     Strip -er/-ber suffixes, identify stem
    │
    ├─ Skeleton Extraction → ["sptmbr", "sptm", "spt"]
    │     Remove vowels, normalize consonants
    │
    ├─ Phonetic Variants (per skeleton) → ["spt", "sbt", "zpt", "cpt", ...]
    │     Apply Grimm's Law, Latin/Greek shift rules
    │
    ├─ Reverse Index Lookup
    │     54,000-key index: skeleton → list of Arabic roots
    │     ├─ سبت (s-b-t) "seventh day / Sabbath" ← from "sbt" variant
    │     ├─ سبع (s-b-ʿ) "seven" ← from "sbt" (ع deleted)
    │     └─ صبط ... and more
    │
    ├─ Multi-Method Scoring (12 independent methods)
    │     Each method scores independently; best score is used
    │
    └─ Output: all candidates with scores, no filtering, no rejection
         Interpretation by human experts + Opus
```

### 2.3 Key Design Decisions

**No filtering, no rejection:** Every candidate that passes the minimum phonetic threshold (default 0.40) is kept. The pipeline is a net, not a sieve. False positives are expected and documented; false negatives (missed real cognates) are the primary concern.

**No LLM judges:** Language models trained on mainstream linguistic literature will reject our hypothesis. They are not used to accept or reject candidates.

**No PIE as ground truth:** The benchmark is built from explicit human-identified cognate pairs (the "Beyond the Name" dataset, Wiktionary etymologies, and the gold collection), not from PIE reconstructions.

**Multi-skeleton per word:** After morphological decomposition, each stem produces its own skeleton. All skeletons are looked up in parallel; candidates from all stems are merged (deduplicated by root). This is the key improvement in the current pipeline version.

---

## 3. Target Language Morphology Rules

The morphological decomposer (`target_morphology.py`) strips inflectional and derivational affixes to expose the lexical stem before skeleton extraction. Each language has its own rules.

### 3.1 Latin

**Suffix stripping rules** (applied in order, longest first):

| Suffix | Strip to | Example | Notes |
|--------|----------|---------|-------|
| -tionem, -tionis | stem | *natio* | Accusative/genitive of action nouns |
| -ationem | stem | *portationem* → *port* | |
| -arius, -aria | stem | *librarius* → *libr* | Agent/relating-to |
| -arium | stem | *aquarium* → *aqu* | |
| -ensis | stem | *forensis* → *for* | Pertaining to |
| -mentum | stem | *documentum* → *doc* | Instrument/result |
| -tura, -sura | stem | *scriptura* → *script* | |
| -ber (month names) | stem | *september* → *sept*, *october* → *oct* | Ordinal month suffix |
| -alis, -alis | stem | *regalis* → *reg* | Relating to |
| -iosus | stem | *copiosus* → *copi* | Having quality |
| -are, -ari | stem | infinitive ending | |
| -ere, -eri | stem | *docere* → *doc* | |
| -ire | stem | *audire* → *aud* | |
| -us, -a, -um | stem | *lupus* → *lup* | Nominative endings |
| -ae, -am, -as | stem | genitive/acc. | |
| -i, -is | stem | genitive singular | |
| -em, -es | stem | acc./nom. plural | |

**Prefix stripping rules:**

| Prefix | Strip | Example | Notes |
|--------|-------|---------|-------|
| con-, com-, cor- | → bare stem | *com-plex* → *plex* | Together/with |
| in-, im-, ir- | → bare stem | *im-port* → *port* | In/into/negation |
| ex-, e-, ef- | → bare stem | *ex-port* → *port* | Out of |
| re- | → bare stem | *re-gio* → *gio* | Back/again |
| de- | → bare stem | *de-scribe* → *scribe* | Down/away |
| sub-, sus- | → bare stem | *sub-terra* → *terra* | Under |
| pre-, pro- | → bare stem | *pro-fundus* → *fund* | Before/forward |
| ad-, ac-, af-, ag- | → bare stem | *ac-cedo* → *ced* | To/toward |
| dis-, di-, dif- | → bare stem | *dis-crete* → *cret* | Apart |
| per- | → bare stem | *per-fect* → *fect* | Through/completely |

**Compound splitting rules:**

Latin compound words are split at recognizable boundaries: *aqua + duct*, *terra + form*, *bene + dict*. The pipeline looks for known Latin elements (aqua, terra, bene, male, omni, semi, etc.) as prefixes.

**Worked examples:**

1. **september** → strip -ber → stem *septem* → strip -em → *sept* → skeleton `spt`
   Arabic candidate: سبت (s-b-t) "Sabbath / seventh day" — phonetically `sbt` (b/p interchange)

2. **documentum** → strip -mentum → *docu* → strip -u → *doc* → skeleton `dk`
   Arabic candidate: دكّ (d-k) "to push down, to flatten" — weak match on form, interesting semantic

3. **aquarius** → strip -arius → *aqua* → strip vowels → skeleton `qw` / `kw`
   Arabic candidate: قوى (q-w) "strength, power" — low match; better: عقو (ʿ-q-w) but ع deleted → `qw`

4. **scriptura** → strip -tura → *script* → skeleton `skrpt`
   Arabic candidate: سرط / سكر — multi-consonant skeleton, harder match

5. **forensis** → strip -ensis → *for* → skeleton `fr`
   Arabic candidate: فرّ (f-r) "to flee, to run" — semantic gap; فرز "to sort" — closer if legal meaning

### 3.2 Ancient Greek

Greek presents unique challenges: the script is non-Latin, aspirate consonants (φ θ χ) have systematic IE correspondences, and the augment prefix ε- must be stripped.

**Suffix stripping rules:**

| Suffix | Strip to | Example | Notes |
|--------|----------|---------|-------|
| -ος, -ον, -α | stem | *λόγος* → *λογ* | Nominative endings |
| -εως, -ου | stem | genitive forms | |
| -ειν | stem | *γράφειν* → *γραφ* | Infinitive |
| -ιζειν | stem | *νομίζειν* → *νομ* | Denominative verbs |
| -ικος, -ικη | stem | *φυσικός* → *φυσ* | Relating to |
| -ωτος, -ητος | stem | perfect passive | |
| -της, -τες | stem | *ποιητής* → *ποιη* | Agent nouns |
| -μα, -ματος | stem | *πράγμα* → *πραγ* | Result nouns |

**Aspirate consonant rules (IPA-based):**

Because Greek uses non-Latin script, skeleton extraction uses IPA when available. Aspirates map as follows before skeleton extraction:
- φ (phi) → f or p
- θ (theta) → t or th (treated as single consonant t for matching)
- χ (chi) → k or h
- ψ (psi) → ps → p or s
- ξ (xi) → ks → k or s

**Prefix stripping rules:**

| Prefix | Strip | Example | Notes |
|--------|-------|---------|-------|
| ἀ-, ἀν- | → bare | *ἄ-θεος* → *θεος* | Alpha-privative (negation) |
| εὐ- | → bare | *εὖ-λογος* → *λογ* | Good/well |
| συν-, συμ- | → bare | *σύν-θεσις* → *θεσ* | Together |
| ἀπο- | → bare | *ἀπο-λύω* → *λυ* | Away from |
| κατα- | → bare | *κατα-γράφω* → *γραφ* | Down |
| ἐπι- | → bare | *ἐπι-στήμη* → *στημ* | Upon |
| ε- (augment) | → bare | *ἔ-λεγε* → *λεγ* | Past tense augment |

**Worked examples:**

1. **φυσικός** (phusikos, "natural") → strip -ικος → *φυσ* → IPA /fʊs/ → skeleton `fs`
   Arabic candidate: فاس (f-s) "axe/to pierce" — phonetic match; also نفس (n-f-s) "breath/soul/nature"

2. **λόγος** (logos, "word/reason") → strip -ος → *λογ* → skeleton `lg`
   Arabic candidate: لغة (l-gh) "language" (gh = غ, velar fricative) — semantic + phonetic match

3. **θεός** (theos, "god") → strip -ος → *θε* → IPA /θe/ → skeleton `th` = `t`
   Arabic candidate: ذات (dh-t) "self/essence" — theta/dh correspondence (ذ → θ is a known Semitic-Greek link)

4. **ἄνθρωπος** (anthropos, "human") → strip -ος → *ἄνθρωπ* → strip ἀ- → *νθρωπ* → skeleton `nthrp`
   Arabic candidates: searching `ntrp`, `ndrb` (with b/p swap)

5. **γράφω** (grapho, "to write") → strip -ω → *γραφ* → IPA /ɡraf/ → skeleton `grf`
   Arabic candidate: قرطاس (q-r-ṭ) or كرف — phonetic similarity; also غرف (gh-r-f) "to scoop/ladle"

### 3.3 Old English (ang) / Middle English (enm)

Old English inflections are heavy; Middle English has partially simplified them.

**Suffix stripping rules:**

| Suffix | Strip to | Example | Notes |
|--------|----------|---------|-------|
| -an (infinitive) | stem | *helpan* → *help* | |
| -on (pl. verb) | stem | *helpon* → *help* | |
| -ung, -ing (noun) | stem | *heortung* → *heort* | Verbal noun |
| -ness, -nyss | stem | *godness* → *god* | Abstraction |
| -dom | stem | *cyningdom* → *cyn* | State/realm |
| -scipe | stem | *freondscipe* → *freond* | Ship/state |
| -ere (agent) | stem | *writere* → *writ* | |
| -ian (weak v.) | stem | *lufian* → *luf* | |
| -es (gen. sg.) | stem | *cyninges* → *cyn* | |
| -um (dat. pl.) | stem | *cyningum* → *cyn* | |
| -ra (gen. pl.) | stem | *cyninga* → *cyn* | |
| -lic | stem | *wundorlic* → *wund* | Like/having quality |
| -lice (adv.) | stem | *gearolice* → *gear* | |

**Prefix stripping rules:**

| Prefix | Strip | Example | Notes |
|--------|-------|---------|-------|
| ge- | → bare | *ge-faran* → *far* | Perfective prefix |
| be- | → bare | *be-cuman* → *cum* | About/by |
| for- | → bare | *for-gyfan* → *gyf* | Intensive/away |
| un- | → bare | *un-gerīm* → *rīm* | Negation |
| ofer- | → bare | *ofer-cuman* → *cum* | Over |
| ymb- | → bare | *ymb-faran* → *far* | Around |
| wiþ- | → bare | *wiþ-standan* → *stand* | Against |

**Epenthetic consonant removal:**

Old English occasionally inserts vowels or glide consonants between consonant clusters. Strip silent/epenthetic consonants in common clusters:
- -ht- (night, light) → the h is epenthetic before Germanic back-shifted t; match skeleton `ngt` or `nkt`
- -wh- initial → treat as `hw` (Old English hw- = Modern wh-)
- -kn- initial → strip k: *cniht* → skeleton `nht` or `nt`

**Worked examples:**

1. **heorte** (heart) → strip -e → *heort* → skeleton `hrt`
   Arabic candidate: حرت → ح deleted (guttural) → `rt`; or قلب (q-l-b) "heart" — different root family

2. **wæter** (water) → strip -er → *wæt* → skeleton `wt`
   Arabic candidate: وطأ (w-ṭ) "to tread/to press" — weak; or ماء + ط → different approach needed

3. **niht** (night) → skeleton `nht` → drop epenthetic h → `nt`
   Arabic candidate: ليل (l-y-l) "night" — different root; نام (n-m) "sleep" — weak; نوب (n-w-b) → `nb`

4. **writere** (writer) → strip -ere → *writ* → skeleton `wrt`
   Arabic candidate: ورط → وَرَط "to entangle/inscribe" → `wrt` — direct skeleton match

5. **cyning** (king) → strip -ing → *cyn* → skeleton `kn`
   Arabic candidate: كان (k-n) "to be/exist" — weak semantic; قن (q-n) "slave/subject" — interesting if royal connection

---

## 4. Phonetic Shift Rules

### 4.1 Grimm's Law

Grimm's Law describes the systematic consonant shift from Proto-Indo-European to Proto-Germanic. Because Arabic and IE languages diverged before PIE, Arabic roots may correspond to either the pre-Grimm (PIE-like) or post-Grimm (Germanic) form. The pipeline generates variants for both.

| PIE/Arabic | Proto-Germanic | Example | Arabic Correspondence |
|------------|----------------|---------|----------------------|
| p | f | pater → father | ف (f) — same |
| t | th / d | tres → three | ت (t) / ث (th) |
| k / q | h / g | centum → hundred | ق/ك (q/k) → h or k |
| b | p | PIE *bh → English f | ب (b) → p or f |
| d | t | PIE *dh → English d | د (d) → t or d |
| g | k | PIE *gh → English g | ج (j/g) → k or g |
| bh | b | PIE *bh → b | ب (b) |
| dh | d | PIE *dh → d | د (d) |
| gh | g | PIE *gh → g | غ (gh) → g |

**Key insight for the pipeline:** When a Latin word contains p, t, k, the corresponding Old English word may have f, th, h. Arabic roots should be looked up against BOTH forms. Latin *pater* (father) and English *father* are the same word — their Arabic skeleton should be matched against `ptr` AND `fthr`.

### 4.2 Latin Phonetic Equivalences

Latin developed specific consonant clusters that represent Arabic consonants:

| Latin Spelling | Phonetic Value | Arabic Correspondence | Example |
|----------------|----------------|----------------------|---------|
| qu- | /kw/ | ق (q) + و | *quam* → ق |
| x | /ks/ | ق+س or كس | *rex* → `rks` → Arabic ركس or رقص |
| ph | /f/ | ف (f) | *philosophia* → `flsf` → Arabic فلسفة |
| th | /t/ | ت or ث | *thesis* → Arabic تاسيس |
| ch | /k/ or /x/ | خ or ك | *chorus* → Arabic خور |
| gn | /n/ (g silent) | ن | *agnus* → `an` → Arabic عَن (ʿ deleted) |
| sc before e/i | /s/ | س | *scio* → Arabic سيو or عيو |
| v | /w/ | و or ب | *via* → Arabic وية |
| j | /y/ | ي or ج | *Janus* → Arabic يانع |

### 4.3 Greek Aspirate Correspondences

| Greek Letter | Romanization | Arabic | Notes |
|-------------|--------------|--------|-------|
| φ (phi) | ph | ف (f) | Direct — phi = f in Arabic phonology |
| θ (theta) | th | ث or ذ | Interdentals correspond: both are dental fricatives |
| χ (chi) | kh | خ (kh) | Direct — chi = kha in Arabic phonology |
| ψ (psi) | ps | Decompose: p→ب, s→س | |
| ξ (xi) | ks | Decompose: k→ق/ك, s→س | |
| γγ | ng | ن+غ | Double gamma = ng |
| κκ | kk | ك | Double consonant = single |

### 4.4 Epenthetic Consonant Patterns

Epenthetic consonants are inserted into clusters with no etymological basis. The pipeline strips them before skeleton comparison:

| Pattern | Epenthetic | Example | Stripped skeleton |
|---------|-----------|---------|-----------------|
| -mpt- | p | *exempt* | `emt` → `xmt` |
| -nct- | c | *distinct* | `dstnkt` → `dstnt` |
| -ndth- | d | *hundredth* | drop epenthetic d |
| -ght- | gh | *night, light* | `nght` → `nt`, `lt` |
| -dg- | d | *bridge* | `brdj` → `brj` |
| -tch- | t | *catch* | treat as `ch` = c |
| -str- | no epenthetic | *strong* | `strng` — keep all |

### 4.5 Double Consonant Simplification

Arabic uses shaddah (ّ) for gemination (consonant doubling), which is phonemically meaningful. IE languages often double orthographically without phonemic gemination.

Rule: before skeleton extraction, collapse runs of the same letter: `ll` → `l`, `ss` → `s`, `tt` → `t`, etc.

Exception: some clusters represent different sounds, e.g., Latin `cc` before e/i = `ks`.

### 4.6 Arabic-Side Transformations

When generating skeleton lookup variants from an Arabic root projection:

**Guttural deletion:** ع ح خ غ → (deleted) or h
Apply: generate variant with these consonants removed AND variant with → h
Example: عرف (ʿ-r-f) → lookup `arf`, `rf`, `hrf`

**Emphatic collapse:** ص→s, ط→t, ض→d, ظ→th
Apply: generate de-emphatic variant
Example: صبر (ṣ-b-r) → lookup `sbr` (same as سبر) — the pipeline treats emphatic and plain as equivalent for lookup

**Bilabial interchange:** ب↔p↔f↔v
Apply: generate b/p/f/v variants of any labial
Example: قلب (q-l-b) → lookup `qlb`, `qlp`, `qlf`

**Sibilant shift:** ش→s/sh, ص→s, ز→z/s
Apply: generate s/z/sh variants
Example: شمس (sh-m-s) → lookup `sms`, `shms`

**Metathesis:** For Semitic-Semitic pairs only (Arabic↔Hebrew, Arabic↔Aramaic)
Generate all permutations of 3-consonant roots
Example: لفت (l-f-t) → also try `ftl`, `tlf`, etc.
Note: Metathesis is disabled for Arabic↔IE pairs (precision 0.11% — noise only)

---

## 5. The 12 Scoring Methods

The `MultiMethodScorer` runs 12 independent methods. Each method produces a score in [0, 1]. The best score across all methods becomes the `best_score`; the number of methods that fired becomes `methods_fired`.

### Method 1: direct_skeleton

**What it does:** Projects the Arabic root to Latin consonant script using the phonetic law table, then compares the projected form directly to the target word's consonant skeleton.

**What it catches:** Words where the Arabic→IE phonetic shift was minimal — roots that survived largely intact. The most common method (fires for 41.5% of all leads).

**Precision:** 1.70% (120 gold hits from 7,052 leads — high recall, low precision)

**Example:** Arabic سبع (s-b-ʿ) "seven" → project → `sb` (ع deleted) → matches Latin *septem* skeleton `sptm` at partial overlap → score reflects shared `s`, `b` consonants

**Caution:** This method produces the most false positives. Use only as one signal among many.

---

### Method 2: reverse_root

**What it does:** Reverses the direction — takes the target word's consonant skeleton and maps it back through the sound law table to find plausible Arabic root forms, then looks up those forms.

**What it catches:** Cases where the IE word preserves consonants that shifted systematically from Arabic. Complements direct_skeleton by working from the IE end.

**Precision:** 2.23% (57 gold hits from 2,560 leads)

**Example:** Latin *filius* (son) → skeleton `fls` → reverse map f→ف, l→ل, s→س → Arabic فلس (f-l-s) "to go bankrupt/peel" or search Arabic roots containing f-l consonants

---

### Method 3: multi_hop_chain

**What it does:** Arabic → known Latin or Greek cognate (from Wiktionary) → target word. Traces the actual historical transmission path rather than relying on direct phonetic similarity.

**What it catches:** Words that entered target languages through documented intermediate stages. This is the most reliable method because it follows attestable etymological chains.

**Precision:** 3.40% (best of all 12 methods; 25 gold hits from 736 leads)

**Example:** Arabic علم (ʿ-l-m) "knowledge" → Greek *ἐπιστήμη* (intermediate) → Latin *scientia* → English "science"

**Note:** This method requires the Arabic→Latin/Greek link to be in the Wiktionary etymology database. It only fires when that intermediate link is documented.

---

### Method 4: metathesis

**What it does:** Tests consonant reversal — checks if the target skeleton is an anagram/permutation of the Arabic root consonants.

**What it catches:** Cases where the root was borrowed with consonant order changed (common in Semitic-Semitic contact, rare cross-family).

**Precision:** 0.11% for Arabic↔IE (effectively noise). 9.8% for Arabic↔Hebrew (genuine Semitic phenomenon).

**Status:** Disabled by default for cross-family pairs. Enabled only for Arabic↔Hebrew and Arabic↔Aramaic.

**Example (valid):** Arabic כבד / كبد (k-b-d) "liver" ↔ Hebrew בכד — metathesis of same root is documented in Semitic linguistics.

---

### Method 5: ipa_scoring

**What it does:** Uses International Phonetic Alphabet transcriptions (when available) to score consonant-by-consonant similarity, weighted by consonant class (place and manner of articulation).

**What it catches:** Cases where the orthographic form is misleading but the pronunciation is similar. Particularly useful for English where spelling diverged from pronunciation (knight, write, etc.).

**Precision:** 0.69% (17 gold hits from 2,476 leads — surprisingly low given the quality of IPA data)

**Example:** English "night" → IPA /naɪt/ → consonants n, t → skeleton `nt`; compared to Arabic نوط (n-w-ṭ) IPA → `nwt` → score reflects n and t shared, w and (emphatic→plain) collapsed

---

### Method 6: guttural_projection

**What it does:** Specifically handles the guttural collapse — inserts ع ح خ غ at every possible position in the target skeleton and searches for Arabic roots that include those consonants.

**What it catches:** Words that lost Arabic pharyngeal/velar consonants entirely. These are the hardest pairs to find because the Arabic distinctive consonant has vanished.

**Precision:** 0.81% (6 gold hits from 745 leads — specialized but reliable when it fires)

**Example:** English "army" → skeleton `rm` → insert ع possibilities → `ʿrm`, `rʿm`, `rmʿ` → Arabic عرم (ʿ-r-m) "to be strong/massive" — the ع at the start of the Arabic root has vanished entirely in English

---

### Method 7: emphatic_collapse

**What it does:** Treats Arabic emphatic consonants (ص ط ض ظ) as equivalent to their plain counterparts (س ت د ذ) when scoring. Also generates variants where emphatics are substituted.

**What it catches:** Latin and Greek borrowed from Semitic intermediaries that had already collapsed emphatics to plain consonants. The pipeline recovers these by making emphatics and plain equivalents.

**Precision:** 1.88% (10 gold hits from 531 leads — highly selective and reliable)

**Example:** Arabic صبر (ṣ-b-r) "to endure/patience" → collapsed form `sbr` → matches Latin *sobrius* (sober) skeleton `sbr` — emphatic ص mapped to plain s

---

### Method 8: morpheme_decomposition

**What it does:** Strips known prefixes and suffixes from both the Arabic and target word, then scores the bare stems against each other.

**What it catches:** Compound words where only one morpheme is cognate. Also catches cases where agglutinative affixes obscure the root.

**Precision:** 0.45% (10 gold hits from 2,210 leads — over-decomposes, too many false stems)

**Example:** Latin *documentum* → strip -mentum → stem *docu* → score against Arabic دوك or similar; English *ruthless* → strip -less → *ruth* → Arabic رثى (r-th-y) "to lament/pity" — direct stem match

---

### Method 9: position_weighted

**What it does:** Scores consonant matches with higher weight for consonants in early positions of the root. This is based on LV1 hypothesis H8 (positional semantics): in Semitic roots, the first consonant carries the most semantic weight.

**What it catches:** Partial matches where the beginning of the root aligns but the end diverges (common with suffixes not fully stripped).

**Precision:** 1.35% (23 gold hits from 1,708 leads)

**Example:** Arabic قوم (q-w-m) "to stand/people" → position-weighted: q scores highest, w second, m third → matches against any target with q or k at the start

---

### Method 10: synonym_expansion

**What it does:** Uses the LV1 Arabic Genome to find the synonym family of each Arabic root, then scores the target word against all synonyms in the family. If a close synonym matches, the original root is credited.

**What it catches:** Cases where the borrowed word captured a slightly different shade of meaning from the same semantic cluster.

**Requires:** LV1 genome data (loaded when available)

**Example:** Arabic فعل (f-ʿ-l) "to do/act" — its synonym family includes عمل "to work", صنع "to make", جعل "to make/cause" — if a target word matches عمل semantically, فعل gets a bonus

---

### Method 11: article_detection

**What it does:** Detects Arabic definite article al- absorbed into loanwords (alcohol → al + kohol, algebra → al + jabr, algorithm → al + khwarizmi).

**What it catches:** High-confidence Arabic loanwords where the article has become fossilized in the target language.

**Precision:** 0.00% in current gold benchmark (0 gold hits from 43 leads) — but this is almost certainly because well-known al- loanwords were excluded from the discovery benchmark as "too obvious".

**Example:** English "alcohol" → detect al- prefix → strip → *cohol* → Arabic كحل (k-ḥ-l) "antimony/kohl" — the etymology is certain; the method correctly identifies it

---

### Method 12: concept_similarity (also: synonym_expansion variant)

**What it does:** Uses BGE-M3 multilingual embeddings to compare the semantic space of the Arabic root meaning against the target word's gloss. A high cosine similarity between meaning vectors is scored as additional evidence.

**What it catches:** Cases where the phonetic match is moderate but the semantic match is strong — these are higher-confidence candidates than pure phonetic matches.

**Note:** This method is the most expensive (requires embedding lookups) and is disabled in fast mode. In the full pipeline, it is the primary filter for reducing false positives.

---

## 6. Data Sources

### 6.1 Arabic Corpus

| Source | Entries | Notes |
|--------|---------|-------|
| Arabic 10-dicts | 70,118 | Ten classical Arabic dictionaries merged |
| Arabic HF roots | 56,606 | Hugging Face structured root database |
| Arabic classical merged | 32,687 | Cross-dictionary deduplication |
| Quranic Arabic | 4,903 | Morphological analysis of Quran text |
| **Total unified** | **~37,000** | After deduplication, used as primary corpus |

### 6.2 Reverse Index

- **54,000 skeleton keys** — each key is a consonant string (3–6 consonants)
- **Built from:** All Arabic root projections using the phonetic law table + guttural/emphatic variants
- **Format:** `{ "sbt": { "candidates": [ { "root": "سبت", "projection": "sbt", "meaning_text": "..." }, ... ] } }`
- **Location:** `Juthoor-CognateDiscovery-LV2/data/processed/reverse_arabic_root_index.json`

### 6.3 Target Language Corpora (from Kaikki.org Wiktionary dumps)

| Language | Code | Entries | IPA Coverage | Notes |
|----------|------|---------|-------------|-------|
| Latin | lat | 883,915 | ~60% | Largest corpus; stride-sampled in runs |
| Ancient Greek | grc | 56,058 | ~70% | IPA critical for non-Latin script |
| Old English | ang | 7,948 | ~40% | Small but high quality |
| Middle English | enm | 49,779 | ~30% | Transitional forms |
| Hebrew | he | 17,034 | ~50% | Semitic-mode; IPA-based extraction |
| Persian | fa/per | 19,361 | ~45% | Iranian branch |
| Aramaic | arc | 2,176 | ~20% | Closest Semitic relative to Arabic |

### 6.4 Benchmark / Gold Pairs

| Source | Pairs | Languages |
|--------|-------|-----------|
| "Beyond the Name" etymologies | 861 | Arabic↔English |
| Wiktionary gold collection | ~1,000+ | Multi-language |
| Expert-identified pairs (manual) | ~30 | Arabic↔English |
| **Total** | **1,889** | 13 language pairs |

---

## 7. Known Errors and Lessons Learned

### 7.1 The September Problem: Treating Compounds as Monolithic

**Error:** *september* is a compound — *septem* (seven) + *-ber* (a month-name suffix). The original pipeline extracted skeleton `sptmbr` from the full word and found no clean match. The real signal is in *sept-* alone.

**Fix:** Morphological decomposition must happen before skeleton extraction. For month names, ordinal suffixes (-ber, -ber), and other Latin compounds, the pipeline now generates multiple skeletons: one for the full form, one for each identified stem.

**Impact:** This pattern likely affects hundreds of Latin words — any compound where one element is cognate but the other is not.

---

### 7.2 PIE as Noise

**Error:** An early version of the pipeline used Proto-Indo-European (PIE) reconstruction as ground truth. Any pair where the IE word had a documented PIE etymology was rejected as "explained by PIE."

**Why this is wrong:** PIE is itself a reconstruction, not attested. Our hypothesis is precisely that Arabic roots encode earlier structure than PIE does. Using PIE as a filter eliminated the most interesting candidates — the ones where Arabic and IE share features that PIE notation does not explain.

**Fix:** PIE etymology data is now stored for reference only, never used for rejection.

---

### 7.3 Semantic Filtering Killed Valid Candidates

**Error:** The pipeline used Gemini to semantically validate pairs. Gemini marked Arabic بلس (Iblis/devil) as "UNLIKELY" to relate to English "false" — but *falsum* (Latin "false") shares phonetic AND semantic overlap with بلس in the context of deception and negation.

**Why LLMs fail here:** Language models are trained on mainstream linguistic literature, which does not recognize our hypothesis. They apply learned priors ("Arabic and English are unrelated") as pseudo-evidence. Their rejections are not independent evidence.

**Fix:** No LLM semantic filtering in the pipeline. All phonetically plausible candidates are kept. Human + Opus review happens at the end, with access to full context.

---

### 7.4 97% of Phonetic Matches Are Coincidental

**Measurement:** The null model test (permutation test with 1,000 random label shuffles) shows that phonetic skeleton matching alone produces a precision of approximately 1.5–3.4% depending on the method. The vast majority of matches are coincidental.

**Implication:** The pipeline is a hypothesis generator, not a classifier. No output should be treated as a confirmed cognate without:
1. Independent semantic analysis
2. Historical pathway plausibility
3. Ideally, multi-method convergence (at least 2 independent methods firing)

---

### 7.5 The Arabic Source Coverage Problem

**Error:** The initial LV2 pipeline was built against a single Arabic corpus (Quranic lemmas, ~5K entries). Only 0.9% of Arabic roots were being sampled in discovery runs.

**Fix:** Supplemented with the full classical Arabic corpus (37K roots). This was the single biggest improvement — gold pair recall went from 1/837 (0.1%) to 269/837 (32.1%).

**Lesson:** Data coverage matters more than algorithm sophistication. Before tuning scoring, ensure the corpus covers the space.

---

### 7.6 Skeleton and Orthography Are Anti-Signals

**Unexpected finding from reranker training:** Features that measure orthographic similarity (skeleton overlap, character n-gram similarity) are negatively correlated with actual cognates in the labeled data.

**Interpretation:** Real cross-family cognates do NOT look like each other on the surface. If an Arabic root and a Latin word share obvious letter sequences, that is probably coincidence (common consonants like s, r, l appear everywhere). Real cognates are recognized by phonetic LAW (systematic shift) and semantic alignment, not surface appearance.

**Fix:** Reranker v3 removed skeleton, orthography, family_boost, root_match, weak_radical_match, and hamza_match — all six were anti-correlated features. Kept: semantic, form, sound, correspondence, genome_bonus, phonetic_law_bonus, source_coherence, multi_method_score (strongest: +1.389), cross_pair_evidence, root_quality, methods_fired_count.

---

## 8. Pipeline Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       INPUT                                       │
│           Target Corpus (e.g., 50K Latin entries)                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  MORPHEME DECOMPOSITION                           │
│  strip inflections → split compounds → enumerate stems           │
│                                                                   │
│  "september" → ["september", "septem", "sept"]                    │
│  "documentum" → ["documentum", "docu"]                            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SKELETON EXTRACTION                              │
│  per-language rules → remove vowels → normalize consonants       │
│                                                                   │
│  "sept" → "spt"                                                   │
│  "docu" → "dk"                                                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  LOOKUP VARIANT GENERATION                        │
│  per skeleton: direct + drop-first + drop-last + metathesis(3)   │
│  + phonetic variants: b/p swap, guttural insert, emphatic deemph │
│                                                                   │
│  "spt" → ["spt", "pt", "sp", "tsp", "pst", "sbt", "zpt", ...]   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  REVERSE INDEX LOOKUP                             │
│  54,000-key index: consonant string → Arabic root candidates      │
│  Merge candidates from all skeletons (deduplicate by root)        │
│                                                                   │
│  "spt" → سبت (Sabbath), سبط (tribe), سفط (basket), ...           │
│  "sbt" → سبت (again), سبد, ...                                   │
│  merged: سبت, سبط, سفط, سبد (deduplicated)                       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PRE-RANKING (fast)                               │
│  SequenceMatcher(projection, skeleton) → prescore               │
│  Sort by prescore; score top 20 with full scorer                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  MULTI-METHOD SCORING (12 methods)               │
│  Each method runs independently → best_score, methods_fired      │
│  Timeout: 5s per candidate                                        │
│                                                                   │
│  direct_skeleton   0.82  │  reverse_root      0.71               │
│  multi_hop_chain   0.91  │  emphatic_collapse 0.68               │
│  ...                     │  ...                                   │
│                                                                   │
│  best_score = 0.91 (multi_hop_chain)                              │
│  methods_fired = 4                                                │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  OUTPUT (JSONL)                                    │
│  One record per target word with >=1 candidate passing threshold │
│                                                                   │
│  {                                                                │
│    "target_word": "september",                                    │
│    "target_lang": "lat",                                          │
│    "target_meaning": "September",                                 │
│    "skeleton": "spt",                                             │
│    "skeletons": ["spt", "sptm", "sptmbr"],                       │
│    "candidates": [                                                │
│      { "arabic_root": "سبت", "phonetic_score": 0.91,             │
│        "best_method": "multi_hop_chain", ... }                   │
│    ]                                                              │
│  }                                                                │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  POST-PROCESSING (separate)                       │
│  Reranker v3 → cognate graph → convergent root analysis          │
│  Human expert review → Opus synthesis → LV3 theory               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. What We Need Help With

### 9.1 Morpheme Decomposition Rules — Are We Missing Patterns?

Our current suffix and prefix lists (Section 3) are built from inspection of common cases. We likely miss:

- **Latin deponent verbs** with unusual stem forms
- **Greek irregular stems** (e.g., *ἐρχ-* as root of *ἦλθον*)
- **Old English strong verb ablaut** — the "present" and "past" stems are different (drive/drove, give/gave)
- **Latin consonant stem nouns** (cor → cord-, lac → lact-, os → oss-)
- **Greek compound-specific patterns** in scientific/technical vocabulary

**Request:** Review Section 3 and identify morphological patterns we are not handling. Specifically: for Latin, Greek, and Old English, what inflectional or derivational processes regularly produce forms where the phonetic stem is hidden?

### 9.2 Phonetic Shift Correspondences — Are the Arabic↔IE Mappings Correct?

The correspondences in Section 4 are based on:
- Khashim's sound law work (9 rules)
- Empirical measurement from 861 pairs (3,461 consonant alignments)
- Standard Grimm's Law as applied to Arabic

**Request:** Are there systematic correspondences we are missing? Are any of the mappings incorrect? We are particularly uncertain about:
- The th/ذ correspondence (Arabic interdental ذ ↔ Greek θ ↔ English th)
- The q/c correspondence through Latin (does ق really map to c more than k?)
- The behavior of Arabic ج across languages (→ g in English, → y in some European languages, → dj in Persian)
- Whether PIE *h₁ h₂ h₃* laryngeals correspond to specific Arabic gutturals

### 9.3 Additional Scoring Methods

We currently have 12 methods. Methods we have considered but not implemented:

- **Chronological gate:** weight candidates higher if the IE word's first attestation is from a period when Arabic-IE contact was historically plausible (medieval Arabic scholarship → Latin, pre-Islamic trade routes → Greek)
- **Morphological template matching:** Arabic broken plural forms vs. IE collective nouns (e.g., Arabic *fuʿūl* plurals matching Latin -uli plurals)
- **Phonosemantic clustering:** Some researchers argue certain consonant clusters carry universal phonosemantic meaning (gr- = rough/grain, fl- = flow). Does our Arabic root inventory show similar patterns?
- **Vowel pattern scoring:** We strip vowels for skeleton matching, but Arabic root vowel patterns (fa'ala, fi'āl, fu'ūl) may correspond to systematic IE patterns

**Request:** Which of these methods would yield the best signal? Are there methods from established historical linguistics (comparative method, internal reconstruction) that we should be implementing?

### 9.4 Independent Evaluation of Top Candidates

The pipeline currently identifies ~12,455 unique nodes in the cognate graph (7 languages, 47,071 edges). From these, 153 Arabic roots connect to 3+ target languages — these are the strongest convergent evidence candidates.

**Request:** We need independent evaluation of the top 50 candidates from the convergent evidence set. The evaluation criteria should be:
1. Is the phonetic correspondence systematic (follows known laws)?
2. Is the semantic alignment plausible (same or related meaning field)?
3. Is there a known historical pathway (trade, religious text transmission, conquest)?
4. What is the probability that this match is coincidental given the search space?

We are explicitly NOT asking whether the candidate is accepted by mainstream historical linguistics — we know it is not. We are asking whether it is internally consistent and whether the phonetic and semantic evidence is compelling enough to warrant further investigation.

---

## Appendix A: Output Format Reference

Each discovery run produces a JSONL file where each line is a JSON object:

```json
{
  "target_word": "string — lemma from target corpus",
  "target_lang": "string — ISO 639-3 code",
  "target_meaning": "string — gloss (up to 200 chars)",
  "target_ipa": "string — IPA transcription if available",
  "skeleton": "string — primary consonant skeleton",
  "skeletons": ["array of all skeletons tried (one per morpheme)"],
  "candidate_count": "integer",
  "candidates": [
    {
      "arabic_root": "string — Arabic script",
      "arabic_projection": "string — Latin-script projection",
      "arabic_meaning": "string — meaning (up to 200 chars)",
      "phonetic_score": "float [0, 1]",
      "prescore": "float — fast skeleton similarity",
      "methods_fired": "integer — number of methods that scored this pair",
      "best_method": "string — name of highest-scoring method"
    }
  ]
}
```

## Appendix B: Key File Locations

| File | Path | Purpose |
|------|------|---------|
| Reverse discovery runner | `Juthoor-CognateDiscovery-LV2/scripts/discovery/run_reverse_discovery.py` | Main pipeline |
| Multi-language runner | `Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_multilang.py` | Forward discovery |
| Multi-method scorer | `Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/discovery/multi_method_scorer.py` | 12-method scoring |
| Target morphology | `Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/discovery/target_morphology.py` | Morpheme decomposition (in development) |
| Reverse index | `Juthoor-CognateDiscovery-LV2/data/processed/reverse_arabic_root_index.json` | 54K-key lookup index |
| Phonetic laws | `Juthoor-CognateDiscovery-LV2/docs/PHONETIC_LAWS_REFERENCE.md` | Sound law documentation |
| Reranker v3 design | `Juthoor-CognateDiscovery-LV2/docs/RERANKER_V3_DESIGN.md` | Reranker architecture |
| Method effectiveness | `Juthoor-CognateDiscovery-LV2/docs/METHOD_EFFECTIVENESS_REPORT.md` | Per-method precision data |
| Consonant correspondence | `Juthoor-CognateDiscovery-LV2/data/processed/consonant_correspondence_matrix.json` | Empirical correspondence weights |
| LLM annotations | `Juthoor-CognateDiscovery-LV2/data/llm_annotations/` | Morphology, semantics, correspondence annotations |

---

## 10. LLM-Assisted Annotation Phase (Active)

### 10.1 Rationale

The pipeline is operational and producing real signal (153 convergent roots, Z > 2.58 null model significance). However, scripts are blind in three areas where per-word linguistic knowledge is required:

1. **Target morphology** — `_strip_prefix()` has no guard against false prefix matches (e.g., "regio" → "gio" when the root is "reg-"). Latin consonant stem nouns (rex→reg-, cor→cord-) have hidden consonants.
2. **Semantic coverage** — The gloss similarity filter works for English (83% coverage) but returns 0.0 for Latin/Greek/OE because glosses are in the source language, not English.
3. **Consonant correspondences** — The correspondence matrix covers only Arabic-English (861 pairs). No positional data, no per-language breakdowns.

These are knowledge gaps, not algorithm problems. An LLM can fill them temporarily as an annotation instrument — returning structural facts that scripts will eventually encode as deterministic rules.

### 10.2 Design Principles

- **LLM as annotator, not judge.** The LLM returns structural morphological facts, English translations, and consonant mappings. It never decides whether a pair is cognate.
- **Small batches, iterative review.** Every layer runs in batches of 30-50 items. After each batch, results are reviewed before proceeding. No bulk runs.
- **Confirmation bias control.** Layer 3 (consonant mapping) includes matched unconfirmed controls at 1:1 ratio. Only correspondences significantly more frequent in confirmed positives than in controls are promoted.
- **Promotion requires held-out improvement.** A learned rule must improve gold evaluation metrics, not just show high annotation frequency.
- **Language-specific rules stay in LV2.** Learned correspondences go into `scoring_profiles.py` (LV2), not into global `sound_laws.py` (LV1), unless confirmed across 3+ target languages.
- **Original data preserved.** Enriched fields are added alongside original glosses, never replacing them.

### 10.3 The 4 Layers

**Layer 1: Target Morphology** — LLM decomposes Latin/Greek/OE words into true stems, identifying false prefix matches and consonant stem nouns. Output stored as a lookup dictionary.

**Layer 2: Semantic Normalization** — LLM translates historical-language lemmas into English semantic fields (translations, semantic extensions, derivational class). One-time enrichment enabling the semantic filter for historical languages.

**Layer 3: Consonant Correspondence** — LLM maps each Arabic consonant to its target-language reflex, annotated with position and mapping type. Matched unconfirmed controls prevent overfitting to positive examples.

**Layer 4: Pre-Ranker Redesign** — Engineering analysis (no LLM) on data cleaned by Layers 1-3. The current SequenceMatcher pre-filter is anti-correlated with true cognates (reranker weight -0.70) and will be replaced based on actual failure-mode analysis.

### 10.4 Transition to Automation

For each layer, the LLM-assisted phase ends when:
- Automated rules reproduce LLM decisions at 95%+ accuracy on held-out data
- Or the enrichment is a one-time data product (Layer 2)

Annotation files are stored in `data/llm_annotations/` as JSONL for reproducibility and auditability.

---

## 11. Toward LV3: The Old Arab Tongue Hypothesis

The pipeline exists to generate evidence for a specific theoretical claim: that an ancestral tongue older than both Classical Arabic and Proto-Indo-European is better preserved in the Arabic root system than in any PIE reconstruction.

LV2 discovery feeds LV3 theory synthesis. The 153 convergent roots, the systematic phonetic corridors (guttural deletion, emphatic collapse, bilabial interchange), and the cross-language replication pattern are the empirical foundation. LV3 interprets this evidence and proposes a coherent alternative to the PIE model.

This pipeline is not neutral infrastructure — it is built to test a specific hypothesis. The design choices (Arabic as high-resolution source, no PIE filtering, no LLM judging) follow from this hypothesis. If the evidence does not support the claim, the pipeline will show that too.
