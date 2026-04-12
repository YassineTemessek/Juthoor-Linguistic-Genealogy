# Juthoor Next Moves — Detailed Plan (April 2026, Pro 20x)

## Where We Are Now

| Level | Status | Key Numbers |
|-------|--------|-------------|
| LV0 (DataCore) | Stable | 12 languages, ~2.76M entries |
| LV1 (ArabicGenome) | Working | 12,333 roots, binary nuclei validated (>11σ) |
| LV2 (CognateDiscovery) | Producing results, BUT unvalidated | Greek: 854, Latin: 53 discoveries |
| LV3 (Origins) | Theory complete, validation suspended | Null model z=0.0 on March 27 |

**The one thing blocking everything:** On March 27, a test showed our consonant matching finds the same number of matches with REAL Arabic roots as with SHUFFLED (random) Arabic roots. That means the pipeline might be matching common letter patterns, not real linguistic connections. The team added meaning-based filtering (AI checks if words actually mean similar things), but nobody re-ran the test to confirm this actually fixes the problem.

Until we prove the improved method beats random, all 854 Greek and 53 Latin discoveries are unconfirmed.

### Execution Mode: Claude Code Pro 20x

All development, orchestration, and code generation runs under a **Claude Code Pro 20x subscription**. This changes the plan economics fundamentally:

| Resource | Constraint | Impact |
|----------|-----------|--------|
| Claude Code orchestration (agent spawning, code gen, review) | **Included in Pro 20x** | Parallel builder agents for per-language setup — no serialization bottleneck |
| Eye 2 scoring (Anthropic API via `eye2_batch_scorer.py`) | **API credits (separate)** | Budget uncapped — use Opus everywhere, score broader candidate pools |
| Tier 3 AI matching (Anthropic API) | **API credits (separate)** | Use Sonnet instead of Haiku — better etymological reasoning |

**Model routing (upgraded from original plan):**

| Task | Original Plan | Pro 20x Plan | Why |
|------|--------------|-------------|-----|
| Tier 3 phonetic reasoning | Haiku (~$0.001/call) | **Sonnet** | Better at chain reconstruction, cost no longer gates |
| Eye 2 semantic scoring | Sonnet (bulk) + Opus (ambiguous) | **Opus for all** | Deeper catches on negation, polysemy, both-sides-of-concept |
| Eye 2 candidate threshold | top-3 per root at ds≥0.85 | **top-10 per root at ds≥0.70** | Broader net, Opus handles the noise |
| Latin rescore | 83K candidates | **200K+ candidates** | Lower threshold, more discoveries |
| Per-language setup code | Manual, serial | **Parallel builder-sonnet agents** | 2-3 languages built simultaneously |

---

## The Languages We Want to Add

### What's Available (Wiktionary/Kaikki lemma counts)

**Large enough for meaningful analysis (>2,000 lemmas):**

| Language | Lemmas | Date | Branch | Why It Matters |
|----------|--------|------|--------|----------------|
| Welsh | ~16,889 | Modern | Celtic (Brythonic) | Largest old-branch corpus. Keeps PIE *p that Irish lost |
| Old Norse | ~4,374 | 12th-14th c. | Germanic (North) | Sagas, Eddas. Archaic Germanic, different branch from English |
| Gothic | ~3,649 | 4th c. CE | Germanic (East) | OLDEST Germanic text. Wulfila Bible. Dead language, no modern influence |
| Old Irish | ~3,236 | 6th-10th c. | Celtic (Goidelic) | OLDEST Celtic. Radical sound changes test skeleton matching limits |
| Tocharian B | ~2,410 | 6th-8th c. | Tocharian | Central Asian IE — geographically between Arabic and European worlds |
| Old High German | ~2,347 | 8th-11th c. | Germanic (West) | Continental Germanic, ancestor of modern German |
| Old Saxon | ~2,115 | 8th-12th c. | Germanic (West) | Continental West Germanic, close to Old English |

**Too small for standalone analysis (<600 lemmas):**

| Language | Lemmas | Note |
|----------|--------|------|
| Breton | ~1,639 | Borderline. Another Brythonic Celtic, similar to Welsh |
| Old Frisian | ~581 | Too small. English's closest relative but not enough data |
| Hittite | ~248 | Too small ON WIKTIONARY. Oldest IE language (17th c. BCE). Need special sources |
| Middle Welsh | ~170 | Too small. Use modern Welsh instead |
| Luwian | ~72 | Too small. Sister of Hittite |

**Already in the pipeline:**

| Language | Entries | Branch |
|----------|---------|--------|
| Old English | 7,948 | Germanic (West) |
| Ancient Greek | 56,058 | Hellenic |
| Latin | 883,915 | Italic |
| Middle English | 49,779 | Germanic (West) |
| Modern English | 1,442,008 | Germanic (West) |

### What Each Language Adds to Your Theory

**Your theory says:** Arabic tongue evolved from single sounds → binary (2-letter) roots → trilateral (3-letter) roots. Languages split off at different stages. Older languages should show more connections, especially to binary roots.

**The test:** If the theory is correct, we should see:

1. **Time gradient within a branch** — Gothic (4th c.) matches Arabic better than Old English (8th c.) which matches better than Middle English which matches better than Modern English
2. **Binary vs trilateral gradient** — Very old languages (Gothic, Old Irish) match Arabic 2-letter roots more. Less old languages (Old English, Latin) match 3-letter roots more
3. **Cross-branch consistency** — The pattern holds independently in Germanic AND Celtic AND other branches

**What each language tests:**

- **Gothic** → Oldest Germanic. Baseline for the Germanic time gradient
- **Old Irish** → Oldest Celtic. Independent branch test. If Gothic AND Old Irish both show the gradient, that's much stronger than one branch alone
- **Welsh** → Brythonic Celtic (different sub-branch from Irish). Large corpus. Tests if Celtic-Arabic connections are consistent within Celtic
- **Old Norse** → North Germanic (different sub-branch from English/Gothic). Tests if Germanic-Arabic connections are consistent within Germanic
- **Old High German** → Continental West Germanic. With Old English (island West Germanic), tests if geography matters within a sub-branch
- **Tocharian B** → Eastern IE, geographically close to ancient trade routes. Tests if proximity to Arabic-speaking world creates stronger matches (contact vs inheritance)

### The Anatolian Problem

Hittite is the most important language we CANNOT easily add. It's the oldest attested IE language (17th-12th century BCE) — if ANY IE language shows deep Arabic connections, it should be Hittite. But Wiktionary only has 248 lemmas.

**Possible sources:**
- Chicago Hittite Dictionary (CHD) — the standard reference, but not freely machine-readable
- Hethitologie-Portal Mainz — academic portal with Hittite texts
- UT Austin Linguistics Research Center — has Hittite glossary online
- Manual curation from published Hittite word lists (~1,500-2,000 known Hittite words exist)

**Recommendation:** Treat Hittite as a special project. Build a small curated dataset (~500-1,000 words) from published sources. Even a small Hittite corpus with strong Arabic matches would be extraordinary evidence.

---

## Architecture Upgrade: LV0 Deep Dedup + Word Families

### The Economic Insight

Every duplicate word we process costs us tokens, time, and money downstream. Right now:
- Latin: 884K raw → 73K after inflection filter → but many of these are STILL variants of the same word
- "saccharum", "saccharon", "saccharinus" = 3 lemmas, 1 concept, 3x the cost

If we collapse word families BEFORE Eye 1, we reduce the candidate space dramatically. And that reduced space lets us afford SMARTER processing per candidate.

**Current funnel (Latin):**
```
884K raw entries
 → 836K after exact dedup
 → 73K after inflection filter (dedup_corpora.py strips "plural of", "genitive of", etc.)
 → 73K units enter Eye 1 (each matched against 11K Arabic roots)
 → ~800M potential pairs, filtered to 2.2M candidates
```

**Improved funnel with word families:**
```
884K raw entries
 → 836K after exact dedup
 → 73K after inflection filter
 → ~20-25K word families (group by shared stem within edit distance 2)
 → ~20K units enter Eye 1
 → ~220M potential pairs (70% reduction)
 → Can now afford Tier 2/3 smart matching on remaining candidates
```

### How to Build Word Families

**Step 1: Stem extraction**
Use existing `target_morphology.py` decomposition. For each lemma, extract the base stem:
- `_decompose_latin("saccharum")` → `"sacchar"`
- `_decompose_latin("saccharinus")` → `"sacchar"`
- `_decompose_latin("agricultura")` → `["agr", "cultur"]` (compound split)

**Step 2: Family grouping**
Group lemmas sharing the same primary stem. Use edit distance ≤ 2 for fuzzy matching to catch irregular derivations:
```
SACCHAR- family: saccharum, saccharon, saccharinus, saccharides (4 members)
SCRIPT- family: scribo, scriptum, scriptura, descriptor (4 members)
AGR- family: ager, agricola, agricultura, agrarius (4 members)
```

**Step 3: Representative selection**
For each family, pick ONE representative — the shortest lemma with the best gloss (most semantic content). Keep metadata about family size and members.

**Step 4: Output format**
```jsonl
{"family_id": "sacchar", "representative": "saccharum", "gloss": "sugar", 
 "members": ["saccharum", "saccharon", "saccharinus"], "family_size": 3,
 "skeleton": "skrm", "ipa": "sak.kʰa.rum"}
```

**Implementation location:** New script `build_word_families.py` in `scripts/discovery/`, runs AFTER `dedup_corpora.py` and BEFORE `run_eye1_full_scale.py`. The Eye 1 script loads family representatives instead of raw lemmas.

### Expected compression ratios per language

| Language | After inflection filter | After word families | Reduction |
|----------|------------------------|--------------------|-----------| 
| Latin | ~73,000 | ~20-25,000 | ~65-70% |
| Greek | ~32,000 | ~15-18,000 | ~45-55% |
| Old English | ~5,000 | ~3,000-3,500 | ~30-40% |
| Gothic | ~3,649 | ~2,000-2,500 | ~30-40% |
| Old Irish | ~3,236 | ~2,000-2,500 | ~25-35% |
| Welsh | ~16,889 | ~8,000-10,000 | ~40-50% |

Smaller languages compress less (fewer derivations per root), but the absolute numbers get small enough to afford smart Eye 1 processing on ALL candidates.

---

## Architecture Upgrade: Tiered Eye 1 (Smart Matching)

### The Problem with Current Eye 1

Eye 1 is fast and cheap but blind. It works like this:
1. Extract consonant skeleton from Arabic root: كتب → "ktb"
2. Extract consonant skeleton from target: "scriptum" → "skrptm"  
3. Compute Jaccard similarity of consonant sets: {k,t,b} ∩ {s,k,r,p,t,m} = {k,t} → Jaccard = 0.29
4. Gate: pass if Jaccard ≥ 0.3 OR ordered overlap ≥ 2

This catches obvious matches but misses connections where sound shifts have changed the consonants. مطر (mtr, "rain") ↔ "water" (wtr) requires knowing that m→w is a possible shift. The current system doesn't know that.

### The Solution: Three Tiers

**TIER 1 — Mechanical skeleton matching (free, run on everything)**

This is what Eye 1 does today. Keep it as the first pass. It catches:
- Direct consonant overlap (سكر ↔ saccharum)
- Near-matches caught by the EQUIVALENTS table (ب→b/p, ق→c/k/g)
- ~55% of Latin lemmas match some Arabic root at this tier

**Current implementation:** `run_eye1_full_scale.py` lines 200-400 (inverted index + Jaccard scoring)
**No changes needed.** Just runs first, outputs candidates with discovery_score.

**TIER 2 — Extended sound law engine (cheap, rule-based, run on Tier 1 misses)**

For the ~45% of lemmas that don't match in Tier 1, apply a richer set of sound correspondences that go beyond the basic EQUIVALENTS table. This is NOT an LLM — it's an expanded rule engine.

**What it adds beyond current EQUIVALENTS:**

1. **Cross-family shifts** (correspondences between language families, not just within):
   - م (m) ↔ w (documented in some Nostratic proposals)
   - ع (ʕ) ↔ Ø (guttural deletion — already documented in LV3 corridors)
   - ه (h) ↔ Ø (aspiration loss)
   - ن (n) ↔ l (liquid interchange, documented in Semitic)

2. **Conditional equivalents** (sound depends on position):
   - Arabic ق word-initial → Latin/Greek k, but word-medial → g
   - Arabic ع word-initial → Ø (deleted), but word-medial → sometimes preserved as h/g

3. **Consonant cluster resolution:**
   - Latin "str" → Arabic could be: س + ت + ر (s-t-r, three separate consonants)
   - Latin "gn" → Arabic could be: ج + ن (j-n) or ق + ن (q-n)
   - These clusters are currently opaque to skeleton matching

4. **Compound decomposition before matching:**
   - "agriculture" → "agri" + "culture" → match EACH part separately against Arabic roots
   - "philosophy" → "philo" + "sophia" → match "sophia" against Arabic صوف (wisdom)?

**Implementation:**
```python
def tier2_extended_match(arabic_skeleton, target_skeletons, lang):
    """Try extended sound laws on Tier 1 misses."""
    
    # 1. Apply cross-family shift table
    extended_arabic_variants = expand_with_cross_family_shifts(arabic_skeleton)
    # مطر "mtr" → also try "wtr", "ntr", "mdr" 
    
    # 2. Apply conditional equivalents 
    conditional_variants = apply_positional_rules(arabic_skeleton, lang)
    
    # 3. Try compound decomposition on target
    target_parts = split_compound(target_word, lang)
    
    # 4. Match all variant combinations
    best_score = 0
    for ar_var in extended_arabic_variants + conditional_variants:
        for tgt_part in target_parts:
            score = jaccard_with_ordered_overlap(ar_var, tgt_part)
            best_score = max(best_score, score)
    
    return best_score, match_details
```

**Location:** New module `tier2_matcher.py` in `src/discovery/`. Called from `run_eye1_full_scale.py` after Tier 1, only on unmatched lemmas.

**Cost:** Still just computation — no LLM calls. Runs in seconds per language.
**Expected catch rate:** Additional 10-15% of lemmas find an Arabic match.

**TIER 3 — AI-assisted phonetic reasoning (expensive, run on selected candidates only)**

For the remaining ~30% of lemmas that neither Tier 1 nor Tier 2 matched, use a fast LLM to attempt chain reconstruction. But NOT on everything — only on candidates where there's a REASON to think a connection might exist.

**Selection criteria for Tier 3 (must meet at least one):**
- Tier 2 found a partial match (score 0.2-0.4) — close but not quite
- Target lemma's English gloss shares a semantic field with an Arabic root's known meanings
- Target lemma is a known loanword candidate (from published etymological databases)
- Target word family is large (≥5 members) — suggests it's a core vocabulary item worth investigating

**The Tier 3 prompt:**
```
You are a historical linguist specializing in deep etymological connections.

Given:
- Arabic root: {root} ({root_meaning})
- Target word: {word} ({language}, meaning: {gloss})
- Consonant skeletons: Arabic {ar_skel} vs Target {tgt_skel}

Question: Is there a plausible phonetic chain connecting these words?

Consider:
1. Known sound shifts between Semitic and {language_family}
2. Intermediate languages the word may have passed through
3. Whether the meaning connection is direct, metaphorical, or via semantic drift
4. Whether the consonant pattern can be explained by documented sound laws

Rate confidence 0.0-1.0 and explain your reasoning in 2-3 sentences.
```

**Model choice (Pro 20x):** Sonnet for all Tier 3 calls — better etymological chain reasoning than Haiku, budget uncapped.

**Cost math with word families:**
- 20K Latin families, ~30% reach Tier 3 = 6K families
- Each family tested against ~5 Arabic roots (semantic pre-filter) = 30K calls
- At Sonnet prices (~$0.002/call) = ~$60 per language
- Compare to current approach: $0 for Eye 1 but $200+ for Eye 2 on unfiltered candidates
- **Pro 20x tradeoff:** 2x Haiku cost buys significantly better chain reconstruction quality

**Implementation:**
```python
def tier3_ai_match(arabic_root, target_family, lang, model="sonnet"):
    """Use LLM reasoning for difficult phonetic connections."""
    
    # Pre-filter: only try if semantic fields overlap
    if not semantic_overlap(arabic_root.mafahim, target_family.gloss):
        return None
    
    prompt = build_tier3_prompt(arabic_root, target_family, lang)
    response = call_llm(prompt, model=model)
    
    return {
        "confidence": response.score,
        "chain": response.explanation,
        "model": model,
        "tier": 3
    }
```

**Location:** New module `tier3_ai_matcher.py` in `src/discovery/`. Called from pipeline after Tier 2.

### How the Three Tiers Flow Together

```
Target lemmas (after word family grouping)
    │
    ▼
┌─────────────────────────────────┐
│  TIER 1: Mechanical skeleton    │  Cost: FREE
│  Jaccard + EQUIVALENTS table    │  Catches: ~55% of lemmas
│  Current Eye 1 logic            │  Time: seconds
└────────────┬────────────────────┘
             │
     ┌───────┴───────┐
     │ MATCHED       │ UNMATCHED (~45%)
     │ (scored,      │     │
     │  ranked)      │     ▼
     │               │ ┌─────────────────────────────────┐
     │               │ │  TIER 2: Extended sound laws     │  Cost: FREE  
     │               │ │  Cross-family shifts,            │  Catches: ~10-15% more
     │               │ │  conditional rules, compounds    │  Time: seconds
     │               │ └────────────┬────────────────────┘
     │               │              │
     │               │      ┌───────┴───────┐
     │               │      │ MATCHED       │ UNMATCHED (~30%)
     │               │      │               │     │
     │               │      │               │     ▼
     │               │      │               │ ┌─────────────────────────────────┐
     │               │      │               │ │  TIER 3: AI phonetic reasoning  │  Cost: ~$60/lang
     │               │      │               │ │  Sonnet for all (Pro 20x)      │  Catches: ~5-10% more
     │               │      │               │ │  Better chain reconstruction    │  Time: hours
     │               │      │               │ │  (only if semantic overlap)     │
     │               │      │               │ └────────────┬────────────────────┘
     │               │      │               │              │
     ▼               ▼      ▼               ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│                 ALL CANDIDATES MERGED                         │
│  Each tagged with tier (1/2/3), score, match details         │
│  Ranked by composite score                                    │
│  Top candidates → Eye 2 (deep LLM semantic validation)       │
└──────────────────────────────────────────────────────────────┘
```

### Why This Changes the Economics

**Current approach:**
- Eye 1 (free but dumb) → produces 2.2M candidates
- Eye 2 (expensive, smart) → can only afford to score 14K (0.6%)
- Result: 99.4% of candidates NEVER evaluated intelligently

**New approach with word families + tiered Eye 1 (Pro 20x):**
- Word families reduce candidate base by 65-70%
- Tier 1 handles the easy matches (free)
- Tier 2 catches sound-law matches (free)
- Tier 3 catches deep connections (~$60/lang with Sonnet — better quality than Haiku)
- Eye 2 with **Opus** on **top-10 per root at ds≥0.70** — much broader net, deeper semantic catches
- Pro 20x covers all orchestration — parallel agent development compresses timeline from 10-14 weeks to 4-6 weeks

**The key insight:** By spending ~$60/language on smart Eye 1 (Sonnet Tier 3), we send BETTER candidates to Eye 2 (Opus). Higher input quality × better scoring model = dramatically higher discovery yield per language.

---

## The Plan — Step by Step

### PHASE 0: Prove the Method Works (1 day)

**What:** Re-run the March 27 null model test, but now with the semantic filtering that was added in April.

**How it works:**
1. Take the real Arabic genome (12,333 roots)
2. Shuffle the roots randomly (scramble which root connects to which meaning)
3. Run Eye 1 + hybrid scoring (50% meaning + 22% sound + 18% form) on BOTH real and shuffled
4. Compare: do real roots get significantly higher scores than shuffled roots?

**Success = z > 3.29** (meaning there's less than 1-in-1000 chance the result is random)

**What to do with the result:**
- If z > 3.29 → the method works. All discoveries are validated. Proceed to Phase 1
- If z is between 2.0 and 3.29 → the method partially works. Investigate which scoring components add signal. Tune weights
- If z < 2.0 → the method still doesn't beat random. STOP. Redesign the scoring before adding any new languages

**Who does the work:** The null model test script already exists (validate_corridors_statistical.py in LV3). It needs to be pointed at the current hybrid scoring pipeline instead of the old consonant-only scorer.

---

### PHASE 1: Fix Known Issues + Build Word Families (3-4 days)

> **Pro 20x acceleration:** Word families, Tier 2 matcher, and Latin rescore are independent — run as 3 parallel builder-sonnet agents.

**1a. Fix the ال (al-) prefix normalization** ✅ DONE (commit `0cbac2e`, April 12 2026)

The ال normalization has been fixed in both Eye 1 and Eye 2:
- `run_eye1_full_scale.py`: threshold changed to `len >= 4`, garbage root filter added, normalized root stored
- `eye2_batch_scorer.py`: `_norm_arabic_lookup()` added for symmetric profile/LV0/deep-glossary lookups
- Regression sanity check added at Eye 1 output

Remaining check: verify `prepare_arabic_discovery.py` also strips ال before skeleton extraction. If not, fix and re-run Eye 1 for Latin and Greek.

**1b. Build the word family pipeline**

Create `scripts/discovery/build_word_families.py`:
1. Read deduplicated lemmas from `dedup_corpora.py` output
2. Run `decompose_target()` on each lemma to extract stem
3. Group lemmas by stem (edit distance ≤ 2 for fuzzy matching)
4. Select representative per family (shortest lemma with best gloss)
5. Output: `{lang}_word_families.jsonl` with family_id, representative, members, family_size
6. Verify: Latin should compress from ~73K to ~20-25K families

**1c. Build Tier 2 extended matcher**

Create `src/discovery/tier2_matcher.py`:
1. Define CROSS_FAMILY_SHIFTS table (m↔w, ʕ↔Ø, h↔Ø, n↔l, etc.)
2. Define POSITIONAL_RULES (conditional equivalents by word position)
3. Implement compound splitter (reuse `_decompose_*` logic, split on known morpheme boundaries)
4. Run on Tier 1 misses only
5. Verify: should catch additional 10-15% of Latin lemmas

**1d. Rescore Latin with V2 prompt (expanded scope)**

Latin only has 53 discoveries because:
- Only 14K of 2.2M Eye 1 candidates were scored (top-3 per root at ds≥0.85)
- All scoring used the old V1 prompt (no target meanings, no multi-step chains)

Action: Score **200K+ candidates at ds≥0.70** using V2 prompt with **Opus** (not Sonnet). Lower threshold + better model = maximum discovery yield.
Expected: Latin jumps from 53 to **500-800+ discoveries**.

---

### PHASE 2: Diachronic Test — Does Older = More Arabic? (1-2 days)

**What:** Run Old English (already in LV0, 7,948 entries) through the full Eye 1 + Eye 2 pipeline and compare its match rate against Modern English.

**Why this matters:** Your theory predicts that older languages match Arabic better because they're closer in time to the divergence point. This is a FREE test — the data is already there.

**What to measure:**
- Match rate: What % of OE lemmas match an Arabic root in Eye 1? Compare to Modern English
- Score distribution: Are OE-Arabic scores higher on average than ModEng-Arabic scores?
- Binary vs trilateral: Do OE words match 2-letter Arabic roots more than ModEng words do?

**What to build:** Old English needs an EQUIVALENTS table and morphology handler. Old English is close to modern English phonologically, so the Latin equivalents table is a reasonable starting point with adjustments for OE-specific sounds (þ/ð → Arabic ث/ذ, etc.)

**If OE matches better than ModEng:** Strong evidence for the time gradient. Proceed with confidence to add more old languages.
**If OE matches the same as ModEng:** The time gradient doesn't hold for this branch. Rethink before investing in more languages.

---

### PHASE 3: Wave 1 — Gothic + Old Irish + Tier 3 AI Matcher (4-5 days)

> **Pro 20x acceleration:** Tier 3 module built by one agent while Gothic + Old Irish setup runs in parallel agents. All three workstreams are independent.

Two languages from two completely independent branches. If BOTH show the pattern, that's convergent evidence.

**3a. Build Tier 3 AI matcher** (before adding languages — build once, use for all)

Create `src/discovery/tier3_ai_matcher.py`:
1. Implement semantic pre-filter: check if Arabic root's mafahim (meaning fields) overlap with target's English gloss using cosine similarity on BGE-M3 embeddings (infrastructure already exists in LV2)
2. Build the Tier 3 prompt template (phonetic chain reconstruction request)
3. Implement **Sonnet** batch caller with retry logic (reuse `eye2_batch_scorer.py` patterns) — upgraded from Haiku for better etymological reasoning
4. Tag all Tier 3 results with model, confidence, and chain explanation
5. Test on known cognates that Tier 1 and Tier 2 miss (مطر↔water, etc.)

This gets built ONCE and then used for every language going forward.

**Gothic (East Germanic, 4th century)**

What's needed:
- Download Kaikki Gothic data (~3,649 lemmas)
- Add to LV0: 3 dict entries in `ingest_kaikki.py` (lang code: `got`)
- Build GOTHIC_EQUIVALENTS in `phonetic_law_scorer.py`:
  - Gothic preserves aspirated stops (𝑝𝑕, 𝑡𝑕, 𝑘𝑕) → map to Arabic emphatics
  - Gothic has no /p/ in native words (Grimm's Law: PIE *p → Germanic *f → Gothic f)
  - Gothic ƕ (hw) → possible Arabic خ correspondence
  - Gothic q (kw) → possible Arabic ق correspondence
- Build `_decompose_gothic()` in `target_morphology.py`:
  - Gothic prefixes: ga-, us-, bi-, dis-, and-, fair-, fra-, du-
  - Gothic suffixes: -s, -is, -us, -a (noun declensions), -an, -jan, -on (verb classes)
- Add scoring profile `ara_gothic` in `scoring_profiles.py`
- Run Eye 1 → Eye 2

**Old Irish (Goidelic Celtic, 6th-10th century)**

What's needed:
- Download Kaikki Old Irish data (~3,236 lemmas)
- Add to LV0: lang code `sga`
- Build OLD_IRISH_EQUIVALENTS:
  - Old Irish lost PIE *p entirely (Latin pater = Old Irish athir) → Arabic ف/ب have NO Irish match for p
  - Lenition: c→ch, t→th, p→ph, b→bh, d→dh, g→gh, m→mh, s→sh, f→fh
  - This is HARD because one Irish letter can represent very different sounds depending on position
  - The lenition system means the EQUIVALENTS table needs to be context-aware (or we match against base consonants only)
- Build `_decompose_old_irish()`:
  - Old Irish prefixes: ad-, air-, as-, com-, di-, do-, ess-, fo-, for-, frith-, imm-, in-, ro-
  - Very complex verbal system — might need to focus on nouns/adjectives only
- Add scoring profile `ara_old_irish`
- Run Eye 1 → Eye 2

**What we learn from Wave 1:**
- Does Gothic match Arabic better than Old English? (Germanic time gradient)
- Does Old Irish match Arabic despite radical Celtic sound changes? (cross-branch test)
- Do both languages match binary roots more than trilateral? (staged divergence test)

---

### PHASE 4: Wave 2 — Welsh + Old Norse (3-4 days)

> **Pro 20x acceleration:** Both languages built in parallel. Pipeline proven by Phase 3, just replicate the pattern.

Fill out both branches with a second language each.

**Welsh (Brythonic Celtic, modern but archaic features, ~16,889 lemmas)**

Why Welsh and not Middle Welsh: Middle Welsh only has 170 lemmas on Wiktionary. Modern Welsh has 16,889 — by far the largest corpus among our target languages. Welsh is also extremely conservative (Welsh speakers can partially read medieval Welsh texts).

What's needed:
- Download Kaikki Welsh data
- Lang code: `cy`
- WELSH_EQUIVALENTS:
  - Welsh KEEPS PIE *p (unlike Irish) → Arabic ف/ب map to Welsh p/b
  - Welsh mutations: soft (c→g, p→b, t→d), nasal (c→ngh, p→mh, t→nh), aspirate (c→ch, p→ph, t→th)
  - Match against citation (unmutated) forms
  - Welsh ff = /f/, f = /v/, dd = /ð/, th = /θ/, ch = /x/, ll = /ɬ/
- Build `_decompose_welsh()`:
  - Welsh prefixes: ad-, all-, am-, an-, cyd-, cyf-, cyn-, dad-, dar-, di-, go-, gor-, gwrth-, hy-, rhag-, tra-, ym-
  - Welsh suffixes: -ach, -ad, -aeth, -aid, -aint, -an, -dod, -edd, -eg, -en, -es, -i, -iant, -id, -ig, -in, -og, -ol, -rwydd, -wch, -wr, -ydd, -yn
- Scoring profile `ara_welsh`

**Old Norse (North Germanic, ~4,374 lemmas)**

What's needed:
- Download Kaikki Old Norse data
- Lang code: `non`
- OLD_NORSE_EQUIVALENTS:
  - Old Norse preserves Germanic *ð (ð) and *þ (þ) → Arabic ذ/ث
  - ON has /x/ (written g in some positions) → Arabic خ
  - Umlaut vowels don't affect consonant matching
  - ON stafróf: b, d, ð, f, g, h, j, k, l, m, n, p, r, s, t, v, x, z, þ
- Build `_decompose_old_norse()`:
  - ON prefixes: af-, al-, and-, at-, be-, for-, fram-, gagn-, mis-, of-, sam-, um-, ú-, van-
  - ON suffixes: -r, -ar, -ir, -ur (noun declensions), -a, -i, -ja, -na (verb classes)
- Scoring profile `ara_old_norse`

**What we learn from Wave 2:**
- Welsh vs Old Irish: Two Celtic sub-branches. Same pattern = Celtic consistency
- Old Norse vs Gothic vs Old English: Three Germanic sub-branches. Time gradient within Germanic
- Welsh (large corpus) improves statistical power significantly

---

### PHASE 5: Wave 3 — Continental + Eastern IE (3-4 days)

> **Pro 20x acceleration:** Both languages in parallel. Templated from Phases 3-4.

**Old High German (~2,347 lemmas)**
- Lang code: `goh`
- Continental West Germanic — ancestor of modern German
- With Old English (island) and Old Saxon (coastal), tests geography within West Germanic
- Similar EQUIVALENTS to Old English but with High German consonant shift (p→pf/ff, t→ts/ss, k→kch/hh)

**Tocharian B (~2,410 lemmas)**
- Lang code: `txb`
- The wildcard. An IE language spoken in Central Asia (modern Xinjiang)
- Geographically closest to the Arabic-speaking world among IE languages
- If Tocharian shows STRONG Arabic matches → supports contact/proximity hypothesis
- If Tocharian shows WEAK matches despite proximity → supports deep inheritance over contact
- Either result is informative

---

### PHASE 6: Hittite Special Project (1-2 weeks, parallel with other work)

Hittite (17th-12th century BCE) is too important to skip, but too small on Wiktionary (248 lemmas).

**Step 1:** Collect Hittite vocabulary from published sources:
- UT Austin Linguistics Research Center glossary
- Chicago Hittite Dictionary (CHD) headword list
- Published Hittite word lists in academic papers
- Target: 800-1,500 unique lemmas with English glosses

**Step 2:** Build custom ingest (not Kaikki):
- Manual JSONL creation with lemma, gloss, IPA (from published transcriptions)
- Hittite is written in cuneiform but has standard Latin transliteration

**Step 3:** Build HITTITE_EQUIVALENTS:
- Hittite preserves laryngeals (ḫ) → possible Arabic ح/خ/ع/غ correspondence
- This is the KEY test of the LV3 claim that PIE *h₁/h₂/h₃ = Arabic gutturals
- Hittite consonants: p, t, k, kw, s, z, ḫ, m, n, l, r, w, y
- Much simpler system than Arabic — mapping is straightforward

**Why this matters:** If Hittite (oldest IE, preserves laryngeals) shows strong Arabic connections through gutturals, that's the single strongest piece of evidence for your theory. Even 50 Hittite-Arabic matches with laryngeal correspondence would be publishable.

---

### PHASE 7: The Big Test — Binary Root Hypothesis (after all languages added)

**The prediction:** Languages that diverged EARLIER match Arabic 2-letter roots more. Languages that diverged LATER match 3-letter roots more.

**The test:**

For each language pair (Arabic ↔ target), calculate:
- Binary match rate: What % of matches involve Arabic 2-consonant nuclei?
- Trilateral match rate: What % of matches involve full 3-consonant roots?
- Binary/trilateral ratio

**Expected pattern (if theory is correct):**

| Language | Era | Expected binary ratio |
|----------|-----|-----------------------|
| Hittite | 17th c. BCE | HIGHEST (diverged earliest) |
| Gothic | 4th c. CE | High |
| Old Irish | 6th c. CE | High |
| Old Norse | ~10th c. CE | Medium-high |
| Old English | 8th c. CE | Medium |
| Latin | Classical | Medium |
| Ancient Greek | Classical | Medium (but high contact = more trilateral) |
| Middle English | 12th c. CE | Lower |
| Welsh | Modern | Lower |
| Modern English | Modern | LOWEST |

**If the data shows this gradient:** That's strong evidence for staged divergence. Languages that split off during the binary root phase retained binary root connections. Languages that stayed in contact longer (or split later) picked up trilateral root connections.

**If the data doesn't show this gradient:** The theory needs revision — either the divergence model is wrong, or the binary/trilateral distinction doesn't map to time depth.

---

## Implementation Checklist Per Language

For each new target language, this is exactly what needs to happen:

**LV0 (Data ingestion):**
1. Download Kaikki JSONL file from kaikki.org
2. Place in `Resources/<lang>/kaikki.org-dictionary-<Language>.jsonl`
3. Add 3 entries to `scripts/ingest/ingest_kaikki.py`: LANG_MAP, LANG_CODE_TO_FILE, _DEFAULT_OUTPUT
4. Run: `python scripts/ingest/ingest_kaikki.py --lang-code <code>`
5. Verify output in `data/processed/<language>/sources/kaikki.jsonl`

**LV0 (Dedup + Word Families):**
1. Run `dedup_corpora.py` on new language → `{lang}_unique_lemmas.jsonl`
2. Run `build_word_families.py` on deduplicated lemmas → `{lang}_word_families.jsonl`
3. Verify compression ratio (expect 30-70% reduction depending on language morphology)

**LV2 (Discovery pipeline — per-language setup):**
1. Create `<LANG>_EQUIVALENTS` dict in `phonetic_law_scorer.py` (Arabic consonant → target consonant mappings)
2. Create `_decompose_<lang>()` function in `target_morphology.py` (prefix/suffix tables, special handling)
3. Update `decompose_target()` dispatcher in `target_morphology.py`
4. Add entry to `config/discovery.yaml`
5. Create scoring profile in `scoring_profiles.py` and register in `_PAIR_TO_PROFILE`
6. Add corpus path to `CORPUS_PATHS` and `DEDUP_NAMES` in `run_eye1_full_scale.py`

**LV2 (Discovery pipeline — running the tiers):**
1. Run Tier 1: `run_eye1_full_scale.py --target <code>` (mechanical skeleton, free)
2. Run Tier 2: `tier2_matcher.py --target <code> --input tier1_misses` (extended sound laws, free)
3. Run Tier 3: `tier3_ai_matcher.py --target <code> --input tier2_misses --model sonnet` (AI reasoning, Sonnet for quality)
4. Merge all tier results into unified candidate list
5. Run Eye 2: batch scorer with V2 prompt on top merged candidates
6. Generate discoveries dashboard entry

**Estimated time per language:** 2-3 days (setup parallelized via builder agents, 1 day tiered Eye 1 compute, 1 day Eye 2 + review)

---

## Timeline Summary (Pro 20x)

| Phase | What | Duration | API Cost | Depends on |
|-------|------|----------|----------|------------|
| 0 | Null model validation | 1 day | $0 | Nothing |
| 1 | Fix normalization + word families + Tier 2 + rescore Latin | 3-4 days | ~$70 | Phase 0 passes |
| 2 | Old English diachronic test (with new tiered Eye 1) | 1-2 days | ~$30 | Phase 1 |
| 3 | Build Tier 3 AI matcher + Gothic + Old Irish | 4-5 days | ~$150 | Phase 2 shows gradient |
| 4 | Welsh + Old Norse | 3-4 days | ~$150 | Phase 3 |
| 5 | Old High German + Tocharian B | 3-4 days | ~$150 | Phase 4 |
| 6 | Hittite special project | 1-2 weeks | ~$50 | Can start in parallel with Phase 3 |
| 7 | Binary root hypothesis test | 2-3 days | $0 | All languages added |

**Total: ~4-6 weeks, ~$600 in API compute + Pro 20x subscription for orchestration**

### Cost Breakdown (Pro 20x — upgraded models)

| Item | What | Cost |
|------|------|------|
| Latin V2 rescore | 200K+ candidates × **Opus** | ~$70 |
| Tier 3 per language | ~30K **Sonnet** calls × 8 languages | ~$480 |
| Eye 2 per new language | 10-25K × **Opus** × 6 new languages | ~$300-450 |
| Hittite special | Small corpus, Opus | ~$50 |
| **Total API** | | **~$600** |
| Claude Code orchestration | Agent spawning, code gen, review, debugging | **$0 (Pro 20x)** |

### What Pro 20x Saves

| Without Pro 20x | With Pro 20x |
|----------------|--------------|
| 10-14 weeks (serial development) | **4-6 weeks** (parallel builder agents) |
| Haiku for Tier 3 (shallow reasoning) | **Sonnet** (better chain reconstruction) |
| Sonnet for Eye 2 (good enough) | **Opus** (catches negation, polysemy, deep links) |
| top-3 per root at ds≥0.85 | **top-10 per root at ds≥0.70** (broader net) |
| 83K Latin rescore | **200K+ Latin rescore** |
| ~$360 API but weeks of manual coding | **~$600 API + free orchestration** |

The old approach of scoring ALL 2.2M Latin Eye 1 candidates blindly would cost $300+ for ONE language. The tiered approach with Pro 20x costs ~$600 for EIGHT languages with better models and broader coverage.

---

## What Success Looks Like

At the end of this plan, you will have:

1. **Statistical proof** that the discovery method beats random chance (Phase 0)
2. **A smarter pipeline** — word families reduce waste, tiered Eye 1 catches connections the old method missed, Opus scoring everywhere catches deep semantic links that Sonnet/Haiku miss (Phases 1-3)
3. **Time gradient evidence** across Germanic (Gothic → OE → ME → ModEng) and Celtic (Old Irish → Welsh)
4. **Cross-branch evidence** from 4+ independent IE branches (Germanic, Celtic, Hellenic, Italic, possibly Tocharian and Anatolian)
5. **Binary root hypothesis data** — the first empirical test of whether languages that diverged earlier connect more to 2-letter Arabic roots
6. **A discovery corpus** of potentially **5,000-12,000** validated Arabic-IE cognate pairs across 10+ languages (Opus scoring + broader candidate pool + Sonnet Tier 3 should significantly increase yield per language vs original Haiku/Sonnet plan)
7. **Publication-ready methodology** with null model validation, multi-branch consistency, and transparent tiered discovery process

## New Files to Create (Summary)

| File | Location | Purpose |
|------|----------|---------|
| `build_word_families.py` | `scripts/discovery/` | Collapse lemmas into word families after dedup |
| `tier2_matcher.py` | `src/discovery/` | Extended sound law matching for Tier 1 misses |
| `tier3_ai_matcher.py` | `src/discovery/` | AI-assisted phonetic chain reasoning |
| `cross_family_shifts.py` | `src/discovery/` | CROSS_FAMILY_SHIFTS table + POSITIONAL_RULES |
| `family_merger.py` | `src/discovery/` | Merge Tier 1+2+3 results into unified candidate list |

These are built ONCE (Phases 1 and 3) and reused for every language.
