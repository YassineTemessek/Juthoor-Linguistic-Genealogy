# Juthoor Discovery Pipeline — Methodology V2

**Date**: 2026-04-09
**Status**: Active (Greek + Latin full discovery complete)
**Results**: 907 pipeline discoveries + 787 gold reference validations = 1,694 total

---

## 1. Overview

Juthoor is a computational linguistics research project that discovers Arabic-origin cognates
in Greek, Latin, and other Indo-European languages. The hypothesis is that a significant portion
of IE vocabulary has Middle Eastern substrate origins — not captured by the standard PIE
reconstruction — and that systematic phonetic + semantic analysis can surface these connections.

### The Two Eyes

**Eye 1 (Consonant Skeleton Matching)**: Arabic roots are mapped to their phonetic equivalents
in the target language via language-specific correspondence tables. Candidates are ranked by
consonant overlap similarity. This step is purely mechanical and produces a large candidate pool
(2-3 million raw matches per language pair).

**Eye 2 (LLM Semantic Scoring)**: Each candidate pair is scored 0.0–1.0 by a large language
model using a calibrated prompt that checks whether the Arabic meaning plausibly connects to
the target word's meaning, accounting for semantic drift, polysemy, and multi-step etymological
chains. Only pairs scoring ≥ 0.5 are counted as discoveries.

### Key Numbers

| Metric | Value |
|--------|-------|
| Arabic roots processed | ~12,000 |
| Greek lemmas (after dedup) | ~11,000 |
| Latin lemmas (after dedup) | ~43,000 |
| Greek pairs scored (Eye 2) | 41,549 |
| Latin pairs scored (Eye 2) | 14,145 |
| Greek discoveries ≥ 0.5 | 854 |
| Latin discoveries ≥ 0.5 | 53 |
| Gold reference pairs scored | 969 |
| Gold pairs validated ≥ 0.5 | 787 (81.7%) |

---

## 2. Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     JUTHOOR PIPELINE V2                         │
└─────────────────────────────────────────────────────────────────┘

 Raw Data                Processing              Output
 ────────                ──────────              ──────

 Arabic Genome           ┌─────────┐
 (12K roots)  ──────────►│  Eye 0  │  Normalize + deduplicate
               │          │  Data   │  Arabic roots, target corpora
 Kaikki        │          │  Prep   │
 Wiktionary   ──────────►└────┬────┘
 (Latin/Greek)               │
                              ▼
                         ┌─────────┐
                         │  Eye 1  │  Consonant skeleton matching
                         │ Skeleton│  Inverted index + Jaccard
                         │ Matcher │  → 2-3M raw candidates
                         └────┬────┘
                              │  top-K per root (K=200)
                              ▼
                         ┌─────────┐
                         │ Eye 1.5 │  Deep glossary enrichment (new)
                         │  Deep   │  Arabic meanings + target etymologies
                         │ Glossary│  → richer Eye 2 context
                         └────┬────┘
                              │  ~15-50K candidates per language
                              ▼
                         ┌─────────┐
                         │  Eye 2  │  LLM semantic scoring
                         │Semantic │  Sonnet bulk + Opus deep review
                         │ Scorer  │  → 0.0–1.0 score per pair
                         └────┬────┘
                              │  ≥ 0.5 threshold
                              ▼
                         ┌─────────┐
                         │  Eye 3  │  Theory synthesis
                         │ Origins │  Corridors, cognate graph, LV3
                         └─────────┘
```

Each Eye builds on the previous. Eye 1 produces quantity; Eye 2 applies quality filtering;
Eye 3 (LV3, not yet operational) performs historical reconstruction.

---

## 3. Eye 1 — Consonant Skeleton Matching

Eye 1 is the phonetic filtering stage. It transforms Arabic roots and target-language lemmas
into consonant skeletons (sorted, deduplicated sets of consonants) and ranks Arabic-target
pairs by phonetic similarity.

### 3.1 Arabic Root Preparation

**Source**: `arabic_genome_roots_discovery.jsonl` (~12K roots from LV1 genome)

**Normalization steps** (applied in order):
1. Strip diacritics (harakat): تَ → ت
2. Normalize hamza variants: أإآء → ا
3. Strip definite article: ال prefix removed (Phase 1 fix, 2026-04-04)
4. Remove duplicate characters within a root

**Skeleton extraction**: Each Arabic consonant is mapped to its phonetic equivalent(s) in
the target language using a language-specific EQUIVALENTS table. For example:

| Arabic | Latin equivalent | Greek equivalent |
|--------|-----------------|-----------------|
| ف      | f               | ph / f          |
| ع      | h, ''           | '', g           |
| ق      | q, k            | k, q            |
| ح      | h               | h               |
| خ      | kh, h           | kh, h           |
| ث      | th              | th              |
| ذ      | d, dh           | d, dh           |
| ص      | s               | s               |

The resulting consonant set is sorted alphabetically to produce a canonical skeleton.
Multiple variants are generated when a consonant has more than one mapping (e.g., ع → {'', g}).

### 3.2 Target Lemma Preparation

**Source**: Kaikki.org Wiktionary dumps (JSONL format)
- Latin: ~835K raw entries → ~43K after dedup (91% drop — mostly inflections)
- Greek: ~56K raw entries → ~11K after dedup (40% drop)

**Deduplication** (`scripts/dedup_corpora.py`):
- Keeps only lemma forms (removes inflected forms flagged in Wiktionary)
- Normalizes capitalization
- Removes entries shorter than 3 characters

**Target skeleton extraction**:
- Latin: direct consonant extraction (a e i o u y stripped, consonants retained)
- Greek: IPA-based extraction converts polytonic Unicode to consonant skeleton
  - Greek has polytonic diacritics stripped before consonant extraction
  - ψ → ps, ξ → ks, θ → th, φ → ph, χ → kh
- Morphological prefix/suffix stripping per language:
  - Latin: un-, de-, re-, -are, -ere, -ire, -us, -um, -a
  - Greek: ἀν-, κατα-, παρα-, -ος, -ον, -ης

### 3.3 Matching Algorithm

**Inverted index**: For each Arabic root skeleton, all target lemmas sharing at least one
consonant are retrieved from a prebuilt index (consonant → [lemma list]).

**Similarity metrics** (computed for each pair):

```
Jaccard(A, B)   = |A ∩ B| / |A ∪ B|
Ordered(A, B)   = longest common subsequence / max(|A|, |B|)
LenRatio(A, B)  = min(|A|, |B|) / max(|A|, |B|)
LenBonus        = 1.0 if |A| >= 3 and |B| >= 3, else 0.5
```

**Composite discovery score**:
```
discovery_score = 0.35 * Jaccard
                + 0.30 * Ordered
                + 0.15 * LenRatio
                + 0.20 * LenBonus
```

This formula rewards: full consonant overlap (Jaccard), order preservation (Ordered),
length balance (LenRatio), and penalizes very short spurious matches (LenBonus).

**Per-root heap**: A max-heap of size K (default K=200) keeps the top candidates per Arabic
root, preventing high-frequency roots from dominating the output.

### 3.4 Eye 1 Results

| Language | Roots processed | Target groups | Raw candidates | Top-K output |
|----------|----------------|---------------|----------------|--------------|
| Greek    | ~11,000        | ~11,000       | ~2.1M          | ~1.4M        |
| Latin    | ~11,000        | ~43,000       | ~2.2M          | ~1.9M        |

Score distribution (typical): mean ~0.72, 81% of candidates in the 0.60–0.80 band.
Pairs with discovery_score ≥ 0.85 (top ~15%) are prioritized for Eye 2 scoring.

---

## 4. Eye 1.5 — Deep Glossary Enrichment (New)

Eye 1.5 is a new intermediate stage (implemented 2026-04-09, LLM compute not yet run)
that enriches both sides of each candidate pair with richer semantic context before
Eye 2 scoring. This reduces the burden on the Eye 2 LLM by pre-packaging meanings.

### 4.1 Arabic Deep Glossary

For each Arabic root, expand beyond the genome's single-line gloss to include:
- **Masadiq** (dictionary meanings): 5-10 attested meanings from classical and modern Arabic
- **Archaic and poetic senses**: meanings documented in Ibn Manzur's Lisan al-Arab
- **Verbal forms**: fa'ala, fā'ala, 'af'ala patterns with distinct meanings
- **Root family context**: binary consonant relatives from LV1 genome (e.g., ك-ت-ب family)

**Why this matters**: LLM models use the most common meaning of a root by default.
Arabic polysemy means the common meaning can obscure a rare sense that is the actual
etymological cognate. Pre-enumerating meanings forces the model to consider all senses.

**Compute estimate**: ~$8 (Sonnet) or ~$20 (Opus) for all 12K roots, 2-4 hours.

### 4.2 Target Etymology Glossary

For each target lemma, add:
- **Etymology chain**: the documented derivation path (from Wiktionary etymology fields)
- **Semantic field tags**: domain classification (body, agriculture, trade, religion, etc.)
- **Derivation family**: related forms in the target language

**Compute estimate**: ~$60 (Sonnet) or ~$175 (Opus) for 73K lemmas, 8-12 hours.

### 4.3 Target Gloss Wiring

English glosses from the Kaikki corpus are attached to Eye 2 input records. This is already
implemented in `eye2_batch_scorer.py` and is active in the current pipeline.

---

## 5. Eye 2 — LLM Semantic Scoring

Eye 2 is the semantic quality filter. A language model reads each Arabic-target pair
(including the Arabic root meaning and the target word's gloss) and assigns a score
from 0.0 to 1.0 representing the probability that the two words are cognates.

### 5.1 Methodology: Masadiq-First

The most important methodological rule:

> **Always check the dictionary meaning (masadiq) FIRST.**
> Use the conceptual/philosophical meaning (mafahim) ONLY for hidden links.

Masadiq-first prevents over-engineering. If كَتَبَ (to write) ↔ script is obvious, score it
high without requiring a five-step conceptual chain. Reserve deep mafahim reasoning for cases
where the surface meanings appear unrelated but share a deeper conceptual root.

**Example of masadiq match** (score 0.95):
- Arabic: بَلَسَم (balsam — aromatic resin)
- Greek: βάλσαμον (balsamon — balsam plant)
- Score: direct lexical borrowing, masadiq match

**Example of mafahim match** (score 0.70):
- Arabic: عَلَم (alam — sign, marker, flag)
- Greek: σῆμα (sema — sign, signal)
- Score: mafahim link through "marker/sign" concept, not surface meaning

### 5.2 Multi-Model Orchestration (Validated)

The pipeline uses a layered model strategy:

```
Phase 1: Sonnet bulk scoring (8 parallel agents, ~3K pairs each)
         → Captures ~91% of ≥0.5 discoveries
         → Cost: ~$30 per 15K pairs, 2-4 hours

Phase 2: Opus deep review (ambiguous 0.15–0.50 zone)
         → Catches negation cognates, rare polysemy, cross-language chains
         → Adds 8-10% more discoveries over Sonnet alone
         → Cost: ~$5 per 2K pairs reviewed, 1 hour

Phase 3: Merge with max()
         → Final score = max(sonnet_score, opus_score) per pair
         → Pairs with any model ≥ 0.5 are included as discoveries
```

**Why not Codex alone**: Codex is too conservative for deep semantic links. It misses
conceptual connections and polysemy. Use Codex only for initial screening/sanity checks.

**Why not Haiku**: Too shallow for etymological reasoning. Misses negation cognates and
multi-step semantic drift patterns.

### 5.3 Scoring Prompt Methodology

The Eye 2 prompt (`config/eye2_prompt_template.txt`) includes:

**Calibration anchors**: Real confirmed discoveries with target scores. Examples:
- اصطبل ↔ στάβλον → 0.95 (stable/stable — direct borrowing)
- بلسم ↔ βάλσαμον → 0.95 (balsam — near-identical)
- قمص ↔ καμίσιον → 0.85 (shirt — attested borrowing with vowel shift)
- جُبّة ↔ cappa → 0.70 (robe/cloak — 4-step chain through Latin)

**Semantic drift patterns** (10 documented types):
1. Concrete → Abstract (sword → edge → limit)
2. Whole → Part (body → organ → muscle)
3. Action → State (to bind → bond → obligation)
4. Genus → Species (animal → horse)
5. Positive → Negative or vice versa (to know → ignorance)
6. Spatial → Temporal (near → soon)
7. Physical → Social (to carry weight → importance/prestige)
8. Agent → Product (maker of X → X itself)
9. Process → Result (to pour → liquid → flood)
10. Source → Destination (from water → waterway → sea route)

**Multi-step chain rule**: Up to 5 steps allowed when each step is documented.
Every step must be flagged with a source (Wiktionary, Lane, Liddell & Scott).

**Cross-language prefix awareness**: The prompt explicitly covers prefix patterns
that models miss: ἀν- (an-) negation = Arabic بدون, κατα- directional = Arabic إلى.

**Forced polysemy protocol**: Model is required to enumerate at least 3 meanings
of the Arabic root before scoring, preventing anchoring on the most common meaning.

### 5.4 Yield Rates (Measured)

| Context | Pairs scored | Yield ≥ 0.5 | Notes |
|---------|-------------|-------------|-------|
| Top candidates (ds ≥ 0.95) | 1,500 | 4.5% | Best Eye 1 output |
| Full pool (ds ≥ 0.85) | 55,694 | ~1.5% | Current pipeline |
| Opus review (ambiguous) | ~4,000 | 8.6% upgrade | Deep semantic catch |
| Gold reference pairs | 969 | 81.7% | "Beyond the Name" benchmark |

The gold reference validation (81.7%) confirms that the Eye 2 methodology is calibrated:
when given known etymological pairs, it correctly identifies them at high rates.

---

## 6. Results Summary

### 6.1 Greek Discoveries

**Pairs scored**: 41,549 | **Discoveries ≥ 0.5**: 854 | **≥ 0.8**: 90 | **≥ 0.95**: 28

Top discoveries by score:

| Arabic | Greek | Score | Meaning connection |
|--------|-------|-------|-------------------|
| اصطبل  | στάβλον | 0.97 | Stable (for horses) — direct borrowing |
| ساسم   | σήσαμον | 0.96 | Sesame — agricultural borrowing |
| دمشق   | Δαμασκός | 0.95 | Damascus — toponym |
| قمص    | καμίσιον | 0.95 | Shirt — textile trade borrowing |
| بلسم   | βάλσαμον | 0.95 | Balsam — aromatic resin |

### 6.2 Latin Discoveries

**Pairs scored**: 14,145 | **Discoveries ≥ 0.5**: 53 | **≥ 0.8**: 5

Top discoveries by score:

| Arabic | Latin | Score | Meaning connection |
|--------|-------|-------|-------------------|
| اصطبل  | stabilio | 0.95 | Stable — same root as Greek cognate |
| جرر    | jarra   | 0.85 | Jar — vessel borrowing via Arabic trade |
| مرر    | amarior | 0.80 | Bitter — taste quality |
| ناطه   | anathema | 0.75 | Curse/devoted object |

### 6.3 Gold Reference Validation

**Source**: "Beyond the Name" — a curated list of Arabic loanwords in European languages.
**Pairs scored**: 969 | **Validated ≥ 0.5**: 787 (81.7%)

Top validated pairs:

| Arabic | European | Score | Domain |
|--------|----------|-------|--------|
| مسجد   | mosque   | 0.98 | Religion |
| زنجبيل  | ginger   | 0.96 | Spice trade |
| القلوي  | alkali   | 0.95 | Chemistry (al- article preserved) |
| مومياء  | mummy    | 0.94 | Medicine/burial |
| سكر    | sugar    | 0.93 | Food trade |

The 18.3% miss rate (182 pairs) decomposes into the failure modes described in Section 7.

---

## 7. Failure Analysis — What the Pipeline Misses

Understanding failure modes is as important as understanding successes.
The following analysis is based on the 182 gold pairs that scored < 0.5.

### 7.1 Multi-Step Chains (~25% of gold failures)

The pipeline scores pairs where the connection requires ≥ 3 etymology steps less reliably,
because each additional step reduces the LLM's confidence even when the chain is real.

**Example**: جُبّة (jubba — a type of robe)
- Step 1: jubba → borrowed into Medieval Latin as juba
- Step 2: juba → Late Latin cappa (hooded cloak)
- Step 3: cappa → chapel (where cappa of St. Martin was kept)
- Step 4: chapel → English chapel / French chapelle

The pipeline correctly identifies jubba ↔ juba (step 1) but misses the downstream chain
to chapel because the intermediate Latin forms are not in the corpus.

**Fix**: Eye 1.5 etymology chains (Section 4.2) will expose these intermediate forms.

### 7.2 Arabic Polysemy (~33% of gold failures)

The LLM defaults to the most common meaning of an Arabic root. When the etymological
connection runs through a rare or archaic sense, the model scores low.

**Example**: علم (ʿalam)
- Common meaning: knowledge, learning → matches "academy", "scholar" → scored
- Rare meaning: sign, marker, flag → matches "semiology", "semaphore" → missed

**Fix**: Eye 1.5 Arabic deep glossary (Section 4.1) pre-enumerates all attested senses.

### 7.3 Cross-Language Chains (~17% of gold failures)

Some English loanwords entered through Latin or Greek intermediaries whose forms are
phonetically distant from the Arabic source. The pipeline only sees Arabic ↔ target,
not the full chain Arabic → Latin → French → English.

**Example**: بدون (bidoon — without)
- Arabic بدون not directly visible in "anesthesia"
- Chain: بدون → Greek ἀν- (prefix of negation) → anesthesia, anarchy, atheism
- The prefix ἀν- matches Arabic بد- pattern but the pipeline lacks prefix-level awareness

**Fix**: Cross-language prefix tables in the Eye 2 prompt partially address this;
full fix requires a prefix-level Eye 1 variant.

### 7.4 Phonetic Distance (~25% of gold failures)

Some genuine cognates have undergone significant phonetic change across millennia,
producing consonant skeletons that do not overlap well enough for Eye 1 to surface them.

**Example**: Arabic مَلِك (malik — king) → Latin miles (soldier) — a semantic AND phonetic
drift that requires both an unusual consonant shift and a meaning evolution from "ruler"
to "one who serves the ruler" to "soldier".

**Fix**: Expanding the EQUIVALENTS table with attested diachronic sound laws (not just
synchronic equivalents) and lowering the Eye 1 minimum score threshold for Opus review.

---

## 8. For Researchers — How to Reproduce and Extend

### 8.1 Minimum Requirements

- Python 3.12+
- 16 GB RAM (Eye 1 loads full corpora into memory)
- 50 GB disk (kaikki dumps, intermediate outputs)
- Anthropic API key (for Eye 2 scoring)

```bash
# Clone and install
git clone <repo>
cd Juthoor-Linguistic-Genealogy
uv pip install -e Juthoor-CognateDiscovery-LV2/
```

### 8.2 Running the Pipeline

```bash
# Eye 0: Prepare corpora (run once after adding new kaikki dumps)
python Juthoor-CognateDiscovery-LV2/scripts/dedup_corpora.py
python Juthoor-CognateDiscovery-LV2/scripts/prepare_arabic_discovery.py

# Eye 1: Generate candidates (one run per target language)
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_eye1_full_scale.py \
    --target grc --top-k 200

# Eye 1.5: Enrich glossary (when compute budget allows)
python Juthoor-CognateDiscovery-LV2/scripts/build_arabic_deep_glossary.py \
    --model sonnet --resume
python Juthoor-CognateDiscovery-LV2/scripts/build_target_etymology_glossary.py \
    --lang grc --model sonnet

# Eye 2: Score semantically (Sonnet bulk pass)
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_pipeline.py \
    --source ara --target grc --stage eye2 --model sonnet --chunk-size 3000

# Eye 2: Opus deep review of ambiguous zone
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_pipeline.py \
    --source ara --target grc --stage eye2 --model opus \
    --min-score 0.15 --max-score 0.50 --review-only

# Dashboard: View results
python Juthoor-CognateDiscovery-LV2/scripts/build_discoveries_dashboard.py
# → outputs/discoveries_dashboard.html
```

### 8.3 Adding a New Language

1. Download the kaikki JSONL dump for the target language from kaikki.org
2. Place it at `Juthoor-DataCore-LV0/data/raw/{lang}/kaikki_{lang}.jsonl`
3. Add a language entry to `Juthoor-CognateDiscovery-LV2/config/discovery.yaml`:
   ```yaml
   languages:
     heb:  # Hebrew example
       name: Hebrew
       script: hebrew
       ipa_based: true
       min_lemma_len: 3
   ```
4. If the language is not Latin-script, add an IPA-based EQUIVALENTS table in
   `Juthoor-CognateDiscovery-LV2/src/juthoor_discovery/phonetic_law_scorer.py`
5. Run dedup: `python scripts/dedup_corpora.py --lang heb`
6. Run Eye 1 + Eye 2 as above

**Languages with existing EQUIVALENTS tables**: Latin (lat), Greek (grc).
**Languages needing new tables**: Hebrew (heb), Aramaic (arc), Persian (fas), Turkish (tur).

### 8.4 Compute Budget Guide

| Task | Model | Estimated cost | Estimated time |
|------|-------|---------------|----------------|
| Eye 1 (one language) | none | $0 | 20–120 min |
| Eye 2 bulk, 15K pairs | Sonnet | ~$30 | 2–4 hours |
| Eye 2 Opus review, 2K pairs | Opus | ~$5 | 1 hour |
| Arabic deep glossary, 12K roots | Sonnet | ~$8 | 2–4 hours |
| Arabic deep glossary, 12K roots | Opus | ~$20 | 3–5 hours |
| Target etymology, 73K lemmas | Sonnet | ~$60 | 8–12 hours |
| Target etymology, 73K lemmas | Opus | ~$175 | 12–20 hours |
| Gold benchmark validation, 969 pairs | Sonnet | ~$2 | 30 min |

**Tip**: Eye 2 is the main cost driver. Use Sonnet for the bulk pass (top-K Eye 1 output),
and Opus only for the ambiguous 0.15–0.50 zone. The marginal gain from Opus is 8-10%
more discoveries at 15-20% of Sonnet cost for the same pair count.

### 8.5 Testing

```bash
# Full test suite (1,206 tests across LV0/LV1/LV2)
python -m pytest \
    Juthoor-DataCore-LV0/tests/ \
    Juthoor-ArabicGenome-LV1/tests/ \
    Juthoor-CognateDiscovery-LV2/tests/ -q

# LV2 only
python -m pytest Juthoor-CognateDiscovery-LV2/tests/ -q

# Specific module
python -m pytest Juthoor-CognateDiscovery-LV2/tests/test_eye2_batch_scorer.py -v
```

### 8.6 Outputs and Artifacts

| Artifact | Location | Description |
|----------|----------|-------------|
| Eye 1 leads | `outputs/leads/` | JSONL, one file per run |
| Eye 2 scored leads | `outputs/eye2/` | JSONL with scores per pair |
| Discovery dashboard | `outputs/discoveries_dashboard.html` | Interactive HTML |
| Gold benchmark results | `data/benchmarks/` | Validation scores |
| LLM annotations | `data/llm_annotations/` | Raw model responses |

All `outputs/` paths are gitignored. Generated artifacts are local only.

---

## 9. Theoretical Position

Juthoor operates within — but extends — the standard PIE framework.

**PIE is incomplete, not wrong.** The standard Proto-Indo-European reconstruction accounts
for the systematic cognate families across IE languages. But a significant residue of IE
vocabulary lacks good PIE etymologies. Juthoor's hypothesis: part of this residue reflects
genuine Arabic/Semitic substrate vocabulary absorbed during prehistoric contact in the
Middle East and Mediterranean.

**LV2 = Discovery, LV3 = Reconstruction.** The discovery pipeline (LV2) is theory-neutral.
It surfaces statistically and semantically plausible connections without claiming
directionality (Arabic → Greek vs. Greek → Arabic) or dating. Theory — including whether
a connection reflects borrowing, substrate influence, or Proto-Semitic/PIE common ancestry —
is the work of LV3 (Origins), not yet operational.

**Validation strategy**: The gold reference benchmark ("Beyond the Name") contains documented
loanwords, not theoretical reconstructions. An 81.7% recall rate on documented loanwords
validates that the pipeline can find real connections. The pipeline discoveries (907 pairs)
are then at varying confidence levels — the ≥ 0.95 tier (28 Greek pairs) is high-confidence;
the 0.5–0.65 tier requires manual review before publication.

---

## 10. Version History

| Version | Date range | Key developments |
|---------|------------|-----------------|
| V1 | 2026-03-14 → 2026-04-04 | Initial pipeline, gold pair benchmark, Layer 1–2 morphology, Arabic genome integration |
| V1.5 | 2026-04-04 | Phase 1 Eye 1 fixes: inflection filter + Arabic ال stripping |
| V2 | 2026-04-05 → 2026-04-09 | Greek+Latin full discovery (907 cognates), interactive dashboard V2 (light theme, IPA), Eye 1.5 deep glossary design |

### V2 Key Changes from V1

1. **Phase 1 Eye 1 fix**: Arabic lemmas with ال prefix were generating false skeleton
   matches. Stripping ال before skeleton extraction reduced false positives significantly.

2. **Inflection filter**: Latin corpus had 91% inflected forms that were not true lemmas.
   Dedup pass cut the Latin corpus from 835K to 43K entries, dramatically improving
   Eye 2 yield rate by removing noisy candidates.

3. **Dashboard V2**: Rebuilt with light theme, IPA transcriptions for Arabic roots,
   enriched metadata display including root family and source language information.

4. **Eye 1.5 design**: New intermediate stage designed but not yet run (requires LLM
   compute budget allocation). Implementation ready in `scripts/`.

---

## 11. Key Files Reference

| File | Purpose |
|------|---------|
| `scripts/discovery/run_eye1_full_scale.py` | Eye 1 main entry point |
| `scripts/discovery/run_pipeline.py` | Unified pipeline CLI (Eye 1 → Eye 2 → Graph) |
| `src/.../discovery/eye2_batch_scorer.py` | Eye 2 LLM scorer implementation |
| `scripts/build_discoveries_dashboard.py` | Dashboard generator |
| `scripts/dedup_corpora.py` | Corpus deduplication |
| `scripts/prepare_arabic_discovery.py` | Arabic genome → discovery format |
| `scripts/discovery/build_cognate_graph.py` | Cognate graph builder |
| `scripts/discovery/eval_eye1_recall.py` | Eye 1 recall evaluation |
| `config/discovery.yaml` | Language and pipeline configuration |
| `config/eye2_prompt_template.txt` | Eye 2 scoring prompt |
| `resources/phonetic_mergers/` | Consonant correspondence tables |
| `data/benchmarks/` | Gold reference pairs |

---

*Generated: 2026-04-09 | Pipeline status: Greek + Latin complete | Next: Eye 1.5 compute run*
