# Juthoor Quick Start Guide

## Setup (5 minutes)

```bash
# Clone and install
git clone https://github.com/YassineTemessek/Juthoor-Linguistic-Genealogy.git
cd Juthoor-Linguistic-Genealogy
uv pip install -e . -e Juthoor-DataCore-LV0 -e Juthoor-ArabicGenome-LV1 -e Juthoor-CognateDiscovery-LV2

# Verify
python -m pytest Juthoor-CognateDiscovery-LV2/tests/ -q  # Should see 400+ tests pass
```

## Run Discovery (10 minutes)

### Arabic → English (fast mode)
```bash
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_full_discovery.py \
  --fast --arabic-limit 200 --english-limit 5000
```

### Arabic → Hebrew / Latin / Greek / Persian / Aramaic
```bash
python Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_multilang.py \
  --source ara --target heb --limit 200 --target-limit 2000 --fast
```

### Check Project Status
```bash
python Juthoor-CognateDiscovery-LV2/scripts/discovery/dashboard.py
```

## Key Outputs

| File | What It Contains |
|------|-----------------|
| `outputs/cognate_graph.json` | Cross-language cognate network (12K nodes, 47K edges) |
| `outputs/cross_pair_convergent_leads.jsonl` | Arabic roots matching 3+ languages |
| `outputs/leads/*.jsonl` | Raw discovery leads per run |
| `resources/benchmarks/cognate_gold.jsonl` | 1,889 gold benchmark pairs |

## Key Findings

1. **ع (pharyngeal) is deleted 88% of the time** in IE languages — strongest correspondence
2. **153 Arabic roots** match across 3+ independent languages (convergent evidence)
3. **Multi-hop chain** (Arabic→Latin/Greek→English) has best precision at 3.4%
4. **Binary root nucleus** (first 2 consonants) defines semantic field with >11σ significance
5. **Meaning is 71.6% predictable** from root consonant structure (H12)

## Architecture

```
LV0 (DataCore)  →  LV1 (ArabicGenome)  →  LV2 (CognateDiscovery)  →  LV3 (Origins)
  Raw corpora        Root genome + RF       Scoring + Discovery        Theory + Corridors
  2.64M lexemes      4 hypotheses           47K-edge graph             10 corridor cards
  11 languages       498 tests              422 tests                  14K validated leads
```
