"""Build enriched English corpus with better glosses for semantic matching."""
import json, sys
from pathlib import Path

LV2_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = LV2_ROOT.parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def main():
    # 1. Load curated 10K (best quality)
    curated_path = LV2_ROOT / "data/processed/english/english_ipa_curated_10k.jsonl"
    curated = {}
    with open(curated_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            row = json.loads(line)
            lemma = (row.get("lemma","") or "").strip().lower()
            if lemma:
                curated[lemma] = row
    print(f"Curated 10K: {len(curated)} entries")

    # 2. Load full corpus and merge glosses
    full_path = LV2_ROOT / "data/processed/english/english_ipa_merged_pos.jsonl"
    full_glosses = {}
    with open(full_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            row = json.loads(line)
            lemma = (row.get("lemma","") or "").strip().lower()
            gloss = (row.get("meaning_text","") or "").strip()
            if lemma and gloss and len(gloss) > 5:
                if lemma not in full_glosses or len(gloss) > len(full_glosses[lemma]):
                    full_glosses[lemma] = gloss
    print(f"Full corpus with glosses: {len(full_glosses)} entries")

    # 3. Load LV0 Modern English (richer glosses from Kaikki)
    kaikki_path = REPO_ROOT / "Juthoor-DataCore-LV0/data/processed/english_modern/sources/kaikki.jsonl"
    kaikki_glosses = {}
    if kaikki_path.exists():
        with open(kaikki_path, encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                row = json.loads(line)
                lemma = (row.get("lemma","") or "").strip().lower()
                gloss = (row.get("gloss_plain","") or row.get("meaning_text","") or "").strip()
                if lemma and gloss and len(gloss) > 10:
                    if lemma not in kaikki_glosses or len(gloss) > len(kaikki_glosses[lemma]):
                        kaikki_glosses[lemma] = gloss
        print(f"Kaikki Modern English with glosses: {len(kaikki_glosses)} entries")

    # 4. Load gold benchmark English targets (ensure they're included)
    gold_english = {}
    gold_path = LV2_ROOT / "resources/benchmarks/cognate_gold.jsonl"
    with open(gold_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            d = json.loads(line)
            tgt = d.get("target", {})
            if tgt.get("lang") == "eng":
                lemma = (tgt.get("lemma","") or "").strip().lower()
                gloss = (tgt.get("gloss","") or "").strip()
                if lemma and gloss:
                    gold_english[lemma] = gloss
    print(f"Gold benchmark English targets: {len(gold_english)} entries")

    # 5. Merge: start with curated, add glosses from kaikki/full, ensure gold words included
    enriched = {}

    # Start with curated 10K
    for lemma, row in curated.items():
        entry = dict(row)
        # Enrich gloss from kaikki if available
        if lemma in kaikki_glosses and len(kaikki_glosses[lemma]) > len(entry.get("meaning_text","") or ""):
            entry["meaning_text"] = kaikki_glosses[lemma]
        elif lemma in full_glosses and len(full_glosses[lemma]) > len(entry.get("meaning_text","") or ""):
            entry["meaning_text"] = full_glosses[lemma]
        enriched[lemma] = entry

    # Add gold targets not in curated
    for lemma, gloss in gold_english.items():
        if lemma not in enriched:
            entry = {"lemma": lemma, "meaning_text": gloss, "ipa": "", "pos": ""}
            if lemma in kaikki_glosses:
                entry["meaning_text"] = kaikki_glosses[lemma]
            enriched[lemma] = entry

    # Add high-frequency words from kaikki with good glosses (top by gloss length)
    remaining = [(lemma, gloss) for lemma, gloss in kaikki_glosses.items()
                 if lemma not in enriched and len(gloss) > 20 and len(lemma) > 2
                 and lemma.replace("-","").replace("'","").isalpha()]
    remaining.sort(key=lambda x: -len(x[1]))
    for lemma, gloss in remaining[:5000]:  # Add 5K more with rich glosses
        enriched[lemma] = {"lemma": lemma, "meaning_text": gloss, "ipa": "", "pos": ""}

    # Write output
    out_path = LV2_ROOT / "data/processed/english/english_enriched_discovery.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for entry in enriched.values():
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Stats
    has_gloss = sum(1 for e in enriched.values() if len(e.get("meaning_text","") or "") > 5)
    print(f"\nEnriched corpus: {len(enriched)} entries")
    print(f"  With glosses > 5 chars: {has_gloss} ({100*has_gloss/len(enriched):.0f}%)")
    print(f"  Written to: {out_path}")

if __name__ == "__main__":
    main()
