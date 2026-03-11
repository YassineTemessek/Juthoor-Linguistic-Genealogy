# LV2 Benchmarks

Tracked benchmark assets for discovery evaluation.

- `cognate_gold.jsonl`: small expert-facing benchmark with higher-confidence positive pairs.
- `cognate_silver.jsonl`: easier starter benchmark for rapid regression checks.
- `non_cognate_negatives.jsonl`: obvious negatives, borrowings, and false-friend style controls.

Each row is JSON with:

```json
{
  "source": {"lang": "ara", "lemma": "عين", "gloss": "eye"},
  "target": {"lang": "heb", "lemma": "עין", "gloss": "eye"},
  "relation": "cognate",
  "confidence": 1.0,
  "notes": "Optional provenance note"
}
```

These files are intentionally small and auditable. They are for evaluation discipline, not for making strong historical claims on their own.
