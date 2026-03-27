"""Build unified Arabic discovery source from all available corpora."""
import json, csv, sys
from pathlib import Path

LV2_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = LV2_ROOT.parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def main():
    unified = {}  # keyed by lemma to dedup

    # 1. Quranic Arabic
    quran_path = LV2_ROOT / "data/processed/arabic/quran_lemmas_enriched.jsonl"
    with open(quran_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            row = json.loads(line)
            lemma = (row.get("lemma","") or "").strip()
            if lemma and len(lemma) >= 2:
                unified[lemma] = row
    print(f"Quranic: {len(unified)} entries")

    # 2. Classical Arabic
    classical_path = REPO_ROOT / "Juthoor-DataCore-LV0/data/processed/arabic/classical/lexemes.jsonl"
    added_classical = 0
    with open(classical_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            row = json.loads(line)
            lemma = (row.get("lemma","") or "").strip()
            if lemma and len(lemma) >= 2 and lemma not in unified:
                unified[lemma] = row
                added_classical += 1
    print(f"Classical (new): {added_classical} entries")

    # 3. Beyond the Name roots
    btn_path = LV2_ROOT / "data/processed/beyond_name_etymology_pairs.csv"
    added_btn = 0
    with open(btn_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            root = (row.get("arabic_root","") or "").strip()
            translit = (row.get("arabic_translit","") or "").strip()
            meaning = (row.get("arabic_meaning","") or "").strip()
            eng_word = (row.get("english_word","") or "").strip()
            if root and root not in unified:
                unified[root] = {
                    "lemma": root,
                    "root": root,
                    "root_norm": root,
                    "translit": translit,
                    "meaning_text": meaning if meaning else f"linked to English '{eng_word}'",
                    "pos_tag": "N",
                    "source": "beyond_the_name",
                }
                added_btn += 1
    print(f"Beyond the Name (new): {added_btn} entries")

    # 4. Gold benchmark
    gold_path = LV2_ROOT / "resources/benchmarks/cognate_gold.jsonl"
    added_gold = 0
    with open(gold_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            d = json.loads(line)
            src = d.get("source", {})
            if src.get("lang","").startswith("ara"):
                lemma = (src.get("lemma","") or "").strip()
                if lemma and len(lemma) >= 2 and lemma not in unified:
                    unified[lemma] = {
                        "lemma": lemma,
                        "root": src.get("root", lemma),
                        "root_norm": src.get("root", lemma),
                        "meaning_text": src.get("gloss", ""),
                        "pos_tag": "N",
                        "source": "gold_benchmark",
                    }
                    added_gold += 1
    print(f"Gold benchmark (new): {added_gold} entries")

    # Write unified corpus
    out_path = LV2_ROOT / "data/processed/arabic/unified_arabic_discovery.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for entry in unified.values():
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"\nUnified Arabic corpus: {len(unified)} entries")
    print(f"Written to: {out_path}")

if __name__ == "__main__":
    main()
