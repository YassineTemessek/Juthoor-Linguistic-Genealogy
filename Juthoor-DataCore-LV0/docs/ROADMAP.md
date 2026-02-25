# LV0 Roadmap (Ordered)

LV0 is the shared data core: raw → canonical processed datasets → validated → released as per-language bundles (date versioning).

This roadmap is focused on keeping data stable and reproducible for LV2/LV3/LV4.

Last updated: 2026-02-25

## Phase 0: Stabilize contracts (COMPLETE)

- [x] Freeze the canonical “lexeme row” contract (required keys + optional keys) and document it. → `docs/SCHEMA_LV0_7.md`
- [x] Define stable file naming conventions under `data/processed/` per language/source.
- [x] Ensure every processed file has provenance fields (source name, stage/script, and stable ids).
- [x] For Arabic rows with a known `root`, include `root_norm` and `binary_root` (canonical: first 2 letters of the accepted root). → Present in `arabic/classical/lexemes.jsonl`
- [ ] Expand language coverage beyond the initial core:
  - German (`deu`) and additional eastern Indo-European targets — not yet ingested
- [x] Standardize layout per dataset:
  - `data/processed/<language>/<stage>/sources/<source>.jsonl` — in place for all languages
  - `data/processed/<language>/<stage>/lexemes.jsonl` — in place for Arabic classical and Quranic Arabic; Latin/Greek/English have sources only (no merged canonical yet)

## Phase 1: Validation gates (IN PROGRESS)

- [x] `validation.py` module exists in package
- [ ] Expand `scripts/ingest/validate_processed.py` to enforce:
  - required keys present (`id`, `lemma`, `language/lang`, `source` as applicable)
  - `translit` and `ipa` fields exist (may be empty early)
  - no empty `lemma`
  - `id` uniqueness within each file
  - consistent encoding and JSONL correctness
- [ ] Add KPI reports that are treated as “release blockers”:
  - row counts
  - missing IPA/translit rates
  - duplicates by `(language, stage, lemma)` and by `id`
- [ ] Arabic classical and Quranic Arabic lexemes.jsonl are missing `stage`, `script`, `form_text`, `meaning_text` — these are schema gaps that must be closed before validation gates can pass

## Phase 2: Per-language release bundles (NOT STARTED)

Release format:

- Tag: `YYYY.MM.DD`
- Assets (per language): `<language>_<YYYY.MM.DD>.zip`
- Manifest: `manifest_<YYYY.MM.DD>.json` (file lists + counts + source versions)

Milestones:

- [ ] Ensure `ldc package --version YYYY.MM.DD` produces:
  - Quranic Arabic bundle (`ara-qur`, Quran-only)
  - Arabic bundle (`ara`, general Arabic tables)
  - English bundle (including parts if present)
  - Greek bundle
  - Latin bundle
  - Concepts bundle (`resources/concepts`)
  - Anchors bundle (`resources/anchors`)
- [ ] Ensure `ldc fetch --release <tag|latest> --dest <path>` downloads and extracts bundles into `data/processed/...`.
- Note: `release/package.py` and `release/fetch.py` stubs exist in the package but are not fully implemented.

## Phase 3: Dataset registry API (NOT STARTED)

- [ ] Provide a small Python API that downstream repos can use:
  - list available datasets by `(language, stage, source)`
  - resolve canonical paths
  - load JSONL with consistent types
- Note: `data/processed/registry/datasets.json` as described in SCHEMA_LV0_7.md does not yet exist.

## Phase 4: Normalization improvements (PARTIAL)

- [x] Transliteration: `translit` field present in Arabic classical, Quranic Arabic, and kaikki outputs
- [x] IPA: `ipa_raw` and `ipa` fields present across all outputs
- [ ] Formal IPA normalization policy not yet implemented
- [ ] Transliteration policy per script not yet formally documented
- [ ] “Stage normalization” helper not yet built

## Phase 5: Downstream integration checks (NOT STARTED)

- [ ] Add “consumer smoke tests”:
  - LV2 expects Arabic bundle contains binary-root-ready tables
  - LV3 expects multilingual bundles contain lexeme tables compatible with discovery retrieval
- Note: LV2 discovery pipeline (`scripts/discovery/run_discovery_retrieval.py`) already reads from LV0 processed outputs in practice; formal smoke tests not yet automated.

## Open questions (to decide once contributors join)

- Which processed outputs are “required canonicals” vs “optional extras” per language?
- What’s the minimal provenance schema that all sources must include?
- Should bundle manifests include content hashes for each file?
- Arabic classical merged `lexemes.jsonl` does not have `form_text`/`meaning_text`; should the merge step apply text-field enrichment, or should the ten_dicts source file be used directly by LV2?
