# LV0 DataCore — Progress Log

Last updated: 2026-03-14

## Current State: Complete

All 7 adapters are implemented, tested, and ingesting into a canonical JSONL schema.

## Ingested Data

| Language | Rows | Adapter |
|----------|------|---------|
| Modern English | 1,442,008 | `ingest_kaikki.py --lang-code en` |
| Latin | 883,915 | `ingest_kaikki.py --lang-code la` |
| Arabic (10 dicts) | 70,118 | `ingest_arabic_ten_dicts.py` |
| Arabic (HF roots) | 56,606 | `ingest_arabic_hf_roots.py` |
| Ancient Greek | 56,058 | `ingest_kaikki.py --lang-code grc` |
| Middle English | 49,779 | `ingest_kaikki.py --lang-code enm` |
| Arabic classical (merged) | 32,687 | `merge_arabic_classical_lexemes.py` |
| Old English | 7,948 | `ingest_kaikki.py --lang-code ang` |
| Quranic Arabic | 4,903 | `ingest_quran_morphology.py` |

**Total: ~2.6M lexemes**

## Schema

- Canonical JSONL with normalized fields: `lemma`, `language`, `script`, `form_text`, `meaning_text`, `stage`, `source`
- Arabic normalization: strip diacritics + tatweel, map hamza variants, ى→ي, ة→ه

## Tests

- 145 tests passing across 7 adapters, processed_schema, and build_text_fields

## Known Gaps

- Arabic classical missing `stage`, `script`, `form_text`, `meaning_text` fields in some entries
- Greek/Latin/English lack merged `lexemes.jsonl` (only raw `sources/kaikki.jsonl`)
- Text-field enrichment not yet run on Modern English 1.44M records
