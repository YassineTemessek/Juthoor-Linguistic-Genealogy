# Juthoor-Origins-LV3

![level](https://img.shields.io/badge/level-LV3-6f42c1)
![license](https://img.shields.io/badge/license-MIT-blue)

LV3 is the **theory synthesis layer**. It consumes all evidence from LV0 (data), LV1 (Arabic genome), and LV2 (cognate discovery) to build and test a coherent alternative to Proto-Indo-European (PIE) reconstruction.

## The Thesis

### Beyond PIE: The Old Arab Tongue Hypothesis

Standard historical linguistics reconstructs Proto-Indo-European (PIE) as the common ancestor of the Indo-European language family. PIE is unattested — it is a theoretical reconstruction based on systematic correspondences between daughter languages.

LV3 proposes an alternative: an **ancestral tongue older than both Classical Arabic and PIE**, whose structure is better preserved in the Arabic triconsonantal root system than in any PIE reconstruction. This is not a claim that Arabic is the mother of all languages. It is a claim that:

1. **Arabic preserves more phonemic resolution** than any IE language. Its 28 consonants — including 4 pharyngeals (ع ح خ غ), 3 emphatics (ص ط ض), and a uvular stop (ق) — represent distinctions that were lost (merged or deleted) in every IE language. The ancestral system had at least this many distinctions.

2. **The consonant skeleton system is older than both families.** The Arabic root template (3-consonant kernel + vowel pattern = word family) is not an innovation of Semitic — it is a survival of the ancestral organizational principle. IE languages lost this structure through vowel-dominant morphology.

3. **Systematic correspondences are not coincidental.** LV2 discovered 153 Arabic roots that show cognate evidence across 3+ target languages (Latin, Greek, Old English, Hebrew, Aramaic, Persian) with average convergent score >0.91. These converge on the same Arabic root from independent language families — a pattern that random chance cannot produce (null model Z > 2.58).

4. **PIE laryngeals may be Arabic gutturals.** PIE theory reconstructs three "laryngeal" consonants (*h₁, *h₂, *h₃) that disappeared from all attested IE languages but left traces in vowel coloring. Arabic has actual consonants in these positions: ه/ء (h₁), ح/خ (h₂), ع/غ (h₃). If this correspondence holds, Arabic didn't "borrow" from PIE — it preserved what PIE lost.

5. **The direction of information loss points upstream.** Arabic → IE shows systematic deletion and merger (pharyngeals disappear, emphatics collapse to plain consonants, uvular merges with velar). IE → Arabic shows no such pattern. Information flows from high-resolution to low-resolution, not the reverse.

### What This Theory Is Not

- It does not claim Arabic is the ancestor of Greek or Latin
- It does not claim the Quran is the oldest text
- It does not reject all of comparative linguistics — it proposes a deeper layer beneath PIE
- It does not use LLMs as judges (they are trained on mainstream linguistics and reject this by default)
- It does not rely on cherry-picked examples — it requires statistically validated convergent evidence

## Evidence Inputs from Lower Levels

| Source | Evidence | Status |
|--------|----------|--------|
| **LV1 Genome** | 12,333 Arabic roots with semantic coherence scores, 4 supported hypotheses (H2, H5, H8, H12) | Complete |
| **LV2 Discovery** | 153 convergent roots (3+ languages), 47,071-edge cognate graph, 1,889 gold benchmark pairs | Operational |
| **LV2 Phonetic Laws** | 5 empirical merger groups, 861-pair consonant correspondence matrix, position-weighted scoring | Operational |
| **LV2 Semantic Filter** | 97% FP reduction validated, concept matcher with 287 structured concepts | Operational |

## Theory Framework

### 10 Phonetic Corridors

Each corridor describes a systematic sound change pattern from the ancestral system to IE languages:

1. **Guttural Deletion** — ع ح خ غ → Ø or h (88% deletion rate for ع)
2. **Emphatic Collapse** — ص→s, ط→t, ض→d, ظ→th
3. **Article Absorption** — Arabic al- fossilized into loanwords (alcohol, algebra, algorithm)
4. **Bilabial Interchange** — ب↔p↔f↔v (cross-family interchangeable)
5. **Sibilant Shift** — ش→s/sh, ص→s, ز→z/s
6. **Uvular-Velar Merger** — ق→c/k/g (Latin c is primary reflex at 39%)
7. **Dental Shift** — ت↔d↔th↔ð (Grimm's Law as a special case)
8. **Metathesis** — consonant reordering (productive in Semitic-Semitic, rare cross-family)
9. **Weak Radical Loss** — و ي ا may delete in non-Semitic languages
10. **Gemination Simplification** — Arabic shaddah (doubled consonant) → single consonant in IE

### 3-Tier Anchor Gates

| Tier | Requirement | Purpose |
|------|-------------|---------|
| **Gold** | In gold benchmark with confidence ≥0.9 | Core evidence — human-verified |
| **Silver** | Convergent across 2+ languages, score >0.85 | Strong machine evidence |
| **Auto-brut** | Single-language hit, score >0.70 | Candidates for review |

### 4-Tier Validation Methodology

1. **Statistical** — null model test, permutation significance (Z > 2.58)
2. **Replication** — same root found independently in multiple languages
3. **Expert** — human review of top candidates by domain specialists
4. **Chronological** — historical plausibility of transmission routes

## Current Status

- 14,494 validated leads flowing from LV2
- Theory synthesis document written (`Master FoundationV3.2.md`)
- LV2 entering LLM-assisted annotation phase to improve morphology, semantics, and phonetic correspondence data — results will strengthen LV3 evidence base
- Next: systematic evaluation of convergent roots against the 10 corridors

## Supported Deployment Model

LV3 is supported inside the full **Juthoor monorepo checkout** with editable installs. Its runtime inputs assume the repo-root shared artifact layout, especially `outputs/cognate_graph.json`.

## Project Map

- LV0 (data core): `Juthoor-DataCore-LV0`
- LV1 (Arabic genome + Research Factory): `Juthoor-ArabicGenome-LV1`
- LV2 (cognate discovery): `Juthoor-CognateDiscovery-LV2`
- LV3 (theory & validation, this package): `Juthoor-Origins-LV3`

## Start Here

- Main document: `Master FoundationV3.2.md`
- Docs navigation: `docs/README.md`
- Ordered plan: `docs/ROADMAP.md`

## Contact

For collaboration: `yassine.temessek@hotmail.com`
