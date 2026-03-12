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

## Practical Tools

Evaluate a run:

```bash
python "scripts/discovery/evaluate.py" \
  "outputs/leads/discovery_YYYYMMDD_HHMMSS.jsonl" \
  --benchmark "resources/benchmarks/cognate_gold.jsonl"
```

Compare a new run to an older baseline:

```bash
python "scripts/discovery/evaluate.py" \
  "outputs/leads/new_run.jsonl" \
  --benchmark "resources/benchmarks/cognate_gold.jsonl" \
  --compare-to "outputs/leads/baseline_run.jsonl"
```

Check benchmark coverage against explicit corpora:

```bash
python "scripts/discovery/benchmark_coverage.py" \
  --benchmark "resources/benchmarks/cognate_gold.jsonl" \
  --source lat@classical="../Juthoor-DataCore-LV0/data/processed/latin/classical/sources/kaikki.jsonl" \
  --target grc@ancient="../Juthoor-DataCore-LV0/data/processed/ancient_greek/sources/kaikki.jsonl"
```

Materialize runnable benchmark slices:

```bash
python "scripts/discovery/materialize_benchmark_slice.py" \
  --benchmark "resources/benchmarks/cognate_gold.jsonl" \
  --source lat@classical="../Juthoor-DataCore-LV0/data/processed/latin/classical/sources/kaikki.jsonl" \
  --target grc@ancient="../Juthoor-DataCore-LV0/data/processed/ancient_greek/sources/kaikki.jsonl" \
  --output-dir "outputs/benchmark_slices/lat_grc_gold"
```

## Current Status

- Arabic-English benchmark slice is runnable and used for correspondence-aware scoring/reranking checks.
- Latin-Greek gold slice is fully materialized with `10/10` available benchmark pairs from existing corpora.
- Weighted metrics (`wMRR`, `wnDCG`) are available for confidence-aware comparisons.
