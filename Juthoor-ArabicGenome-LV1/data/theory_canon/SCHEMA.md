# LV1 Theory Canon Inbox Schema

All files under `inbox/` must be:

- UTF-8
- JSONL
- one JSON object per line
- stable IDs where applicable
- explicit provenance

Allowed canon statuses:

- `empty`
- `draft`
- `curated`
- `tested`
- `promoted`
- `rejected`

Allowed theory claim statuses:

- `asserted`
- `curated`
- `tested`
- `promoted`
- `rejected`

## `inbox/letters/`

Minimal example:

```json
{"letter":"ب","letter_name":"الباء","canonical_semantic_gloss":"تجمع رخو مع تلاصق ما","sources":[{"source_id":"jabal-b","scholar":"jabal","claim_type":"semantic","claim_text":"تجمع رخو مع تلاصق ما","document_ref":"المعجم الاشتقاقي المؤصل","curation_status":"reviewed"}],"agreement_level":"consensus","confidence_tier":"medium","status":"curated"}
```

## `inbox/binary_fields/`

Minimal example:

```json
{"binary_root":"حس","field_gloss":"نفاذ حاد في سطح عريض","field_gloss_source":"jabal","letter1":"ح","letter2":"س","member_roots":["حسب","حسد","حسر"],"member_count":3,"status":"curated"}
```

## `inbox/root_composition/`

Minimal example:

```json
{"root":"حسد","binary_root":"حس","third_letter":"د","conceptual_root_meaning":"انحباس شيء حاد في الباطن","axial_meaning":"الحسد","status":"draft"}
```

## `inbox/theory_claims/`

Minimal example:

```json
{"claim_id":"claim-jabal-binary-field","theme":"binary_derivation","scholar":"jabal","statement":"أول حرفين صحيحين يحددان الحقل الدلالي","scope":"arabic_general","evidence_type":"lexical","source_doc":"ملخص_الدلالة_الصوتية_العربية.md","source_locator":"§7b","status":"curated"}
```

## `inbox/quranic/`

Minimal example:

```json
{"lemma":"قلب","root":"قلب","conceptual_meaning":"التقلب والتحول","lexical_realization":"القلب العضوي أو المعنوي","contextual_constraints":["السياق الوجداني"],"confidence":"low","status":"draft"}
```
