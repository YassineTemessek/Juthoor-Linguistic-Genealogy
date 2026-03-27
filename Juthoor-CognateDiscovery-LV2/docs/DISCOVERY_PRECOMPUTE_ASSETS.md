# Discovery Precompute Assets

This note records the one-time LV2 prep assets built to speed up repeated discovery runs.

## Built assets

### 1. Curated English IPA corpus

- Path:
  - `Juthoor-CognateDiscovery-LV2/data/processed/english/english_ipa_curated_10k.jsonl`
- Built from:
  - `Juthoor-CognateDiscovery-LV2/data/processed/english/english_ipa_merged_pos.jsonl`
- Current summary:
  - scanned `268,889` rows
  - deduplicated to `156,673` lemmas
  - kept `10,000` high-value entries

Selection policy:
- requires IPA
- prefers content POS (`noun`, `verb`, `adj`, `adv`, `name`)
- downranks function words, punctuation-heavy forms, apostrophe variants, and ultra-short lemmas
- adds:
  - `ipa_skeleton`
  - `orth_skeleton`
  - `curation_score`

Primary use:
- fast English-side discovery runs without rescanning the full 88MB corpus

Builder:
- `python Juthoor-CognateDiscovery-LV2/scripts/discovery/build_curated_english_corpus.py`

### 2. Reverse Arabic root index

- Path:
  - `Juthoor-CognateDiscovery-LV2/data/processed/reverse_arabic_root_index.json`
- Built from:
  - `Juthoor-CognateDiscovery-LV2/outputs/corpora/arabic_root_families.jsonl`
- Current summary:
  - roots seen: `12,333`
  - indexed skeletons: `54,347`
  - projection rows considered: `992,936`

What it stores:
- English-style consonant skeleton (`2-4` consonants) ->
  - candidate Arabic roots
  - projected Latin forms
  - binary root
  - meaning text
  - word count

Primary use:
- instant reverse lookup for Method 10 / reverse-root generation
- avoids recomputing sound-law projections per pair

Builder:
- `python Juthoor-CognateDiscovery-LV2/scripts/discovery/build_reverse_root_index.py`

### 3. Historical English lookup

- Path:
  - `Juthoor-CognateDiscovery-LV2/data/processed/english/english_historical_meanings.jsonl`
- Built from:
  - `Juthoor-CognateDiscovery-LV2/data/processed/beyond_name_etymology_pairs.csv`
  - `Juthoor-DataCore-LV0/data/processed/english_old/sources/kaikki.jsonl`
  - `Juthoor-DataCore-LV0/data/processed/english_middle/sources/kaikki.jsonl`
- Current summary:
  - scanned `863` Beyond-the-Name rows
  - wrote `853` lookup rows
  - extracted explicit historical phrases: `3`
  - exact Old English lemma matches: `73`
  - exact Middle English lemma matches: `211`

What it stores per lemma:
- `modern_gloss`
- `historical_phrases`
- `beyond_name_note`
- `old_english_matches`
- `middle_english_matches`
- `intermediate_langs`

Primary use:
- semantic rescue for English forms whose modern gloss hides the older sense

Builder:
- `python Juthoor-CognateDiscovery-LV2/scripts/discovery/build_historical_english_lookup.py`

## Recommended next integration

1. Make discovery runners accept `english_ipa_curated_10k.jsonl` as the default fast English target.
2. Use `reverse_arabic_root_index.json` before brute-force Arabic projection loops.
3. Let the scorer or validator consult `english_historical_meanings.jsonl` before discarding low-modern-semantic pairs.
