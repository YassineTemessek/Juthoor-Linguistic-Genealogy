"""Extract best examples for each corridor card from validated leads."""
import json, sys, collections
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LV3_ROOT = REPO_ROOT / "Juthoor-Origins-LV3"
LV2_ROOT = REPO_ROOT / "Juthoor-CognateDiscovery-LV2"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Map corridor IDs to discovery methods
CORRIDOR_METHOD_MAP = {
    "CORRIDOR_01": "guttural_projection",
    "CORRIDOR_02": "emphatic_collapse",
    "CORRIDOR_03": "article_detection",
    "CORRIDOR_04": "metathesis",
    "CORRIDOR_05": "position_weighted",
    "CORRIDOR_06": "direct_skeleton",
    "CORRIDOR_07": "morpheme_decomposition",
    "CORRIDOR_08": "multi_hop_chain",
    "CORRIDOR_09": "direct_skeleton",
    "CORRIDOR_10": "reverse_root",
}

def main():
    # Load validated leads
    leads_path = LV3_ROOT / "data" / "leads" / "validated_leads.jsonl"
    leads = []
    with open(leads_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                leads.append(json.loads(line))

    print(f"Loaded {len(leads)} validated leads\n")

    # Load all discovery leads for method info
    all_discovery_leads = []
    leads_dir = LV2_ROOT / "outputs" / "leads"
    for f in sorted(leads_dir.glob("*.jsonl")):
        try:
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        d = json.loads(line)
                        if d.get("scores", {}).get("best_method"):
                            all_discovery_leads.append(d)
        except Exception:
            continue

    print(f"Loaded {len(all_discovery_leads)} discovery leads for method info\n")

    # Group by method
    method_examples = collections.defaultdict(list)
    for lead in all_discovery_leads:
        method = lead.get("scores", {}).get("best_method", "")
        score = lead.get("scores", {}).get("multi_method_best", 0) or lead.get("scores", {}).get("final_combined", 0)
        src = lead.get("source", {})
        tgt = lead.get("target", {})
        if method and score >= 0.70:
            method_examples[method].append({
                "source_lemma": src.get("lemma", ""),
                "source_root": src.get("root", ""),
                "source_gloss": src.get("gloss", "")[:50],
                "target_lemma": tgt.get("lemma", ""),
                "target_lang": tgt.get("lang", ""),
                "target_gloss": tgt.get("gloss", "")[:50],
                "score": score,
                "method": method,
                "explanation": lead.get("evidence", {}).get("explanation", "")[:80],
            })

    # For each corridor, print top 5 examples
    output = {}
    for cid in sorted(CORRIDOR_METHOD_MAP.keys()):
        method = CORRIDOR_METHOD_MAP[cid]
        examples = sorted(method_examples.get(method, []), key=lambda x: -x["score"])
        # Deduplicate by (source, target)
        seen = set()
        unique = []
        for ex in examples:
            key = (ex["source_lemma"], ex["target_lemma"])
            if key not in seen:
                seen.add(key)
                unique.append(ex)
            if len(unique) >= 10:
                break

        output[cid] = unique[:10]
        print(f"\n{'='*60}")
        print(f"{cid} ({method}) — Top 5 examples:")
        print(f"{'='*60}")
        for i, ex in enumerate(unique[:5], 1):
            print(f"  {i}. {ex['source_lemma']} ({ex['source_root']}) -> {ex['target_lemma']} [{ex['target_lang']}]")
            print(f"     Score: {ex['score']:.3f} | {ex['explanation'][:60]}")

    # Save to file
    out_path = LV3_ROOT / "data" / "corridor_examples.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n\nSaved examples to {out_path}")

if __name__ == "__main__":
    main()
