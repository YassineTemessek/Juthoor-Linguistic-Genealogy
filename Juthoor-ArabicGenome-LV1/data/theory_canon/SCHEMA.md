# Theory Canon — Data Schemas

This folder holds the structured semantic data for LV1's canonical registries.

## How It Works

1. **Codex/Claude** extract scholar data → write JSONL files to the appropriate subfolder
2. **Yassine** drops manually curated files into `inbox/`
3. **Import pipeline** validates and ingests from inbox → moves to `imported/`
4. **Rejected files** go to `rejected/` with error reports

## Letter Schema (letters/*.jsonl)

Each line is one scholar's entry for one letter:

```json
{
  "letter": "ب",
  "letter_name": "الباء",
  "scholar": "jabal",
  "raw_description": "تجمع رخو مع تلاصق ما",
  "atomic_features": ["تجمع", "رخاوة", "تلاصق"],
  "feature_categories": ["gathering_cohesion", "texture_quality", "gathering_cohesion"],
  "sensory_category": null,
  "kinetic_gloss": null,
  "source_document": "المعجم الاشتقاقي المؤصل",
  "confidence": "high"
}
```

**Valid scholars:** jabal, neili, asim_al_masri, hassan_abbas, anbar, khashim, dhouq, shanawi

**Valid feature categories:** pressure_force, extension_movement, penetration_passage, gathering_cohesion, spreading_dispersal, texture_quality, sharpness_cutting, spatial_orientation, independence_distinction

**Valid confidence:** high, medium, low, stub

## Binary Field Schema (binary_fields/*.jsonl)

Each line is one binary nucleus:

```json
{
  "binary_root": "حس",
  "letter1": "ح",
  "letter2": "س",
  "jabal_shared_meaning": "نفاذ حاد في سطح عريض",
  "jabal_features": ["نفاذ", "حدة", "سطح"],
  "member_roots": ["حسب", "حسد", "حسر", "حسك", "حسم", "حسن"],
  "member_count": 6,
  "bab": "الحاء",
  "source": "المعجم الاشتقاقي المؤصل"
}
```

## Root Schema (roots/*.jsonl)

Each line is one trilateral root:

```json
{
  "root": "حسب",
  "binary_nucleus": "حس",
  "third_letter": "ب",
  "jabal_axial_meaning": "تجميع المتفرق كالحشو",
  "jabal_features": ["تجمع", "تلاصق"],
  "bab": "الحاء",
  "quranic_verse": null,
  "source": "المعجم الاشتقاقي المؤصل"
}
```

## Theory Claim Schema (theory_claims/*.jsonl)

```json
{
  "claim_id": "jabal_binary_field_001",
  "theme": "binary_derivation",
  "scholar": "jabal",
  "statement": "أول حرفين صحيحين في الجذر يحددان الحقل الدلالي",
  "scope": "arabic_general",
  "evidence_type": "lexical",
  "source_document": "المعجم الاشتقاقي المؤصل",
  "source_locator": "المقدمة",
  "status": "curated"
}
```

**Valid themes:** letter_semantics, binary_derivation, positional, intentionality, no_synonymy, golden_rule, sound_laws, pictographic, comparative

**Valid status:** asserted, curated, tested, promoted, rejected
