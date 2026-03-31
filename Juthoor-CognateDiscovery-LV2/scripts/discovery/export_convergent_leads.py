"""Export top Arabic roots with convergent cross-language evidence."""
import json, sys, collections
from pathlib import Path

LV2_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = LV2_ROOT.parent

def main():
    graph_path = REPO_ROOT / "outputs" / "cognate_graph.json"
    if not graph_path.exists():
        graph_path = LV2_ROOT / "outputs" / "cognate_graph.json"
    output_path = REPO_ROOT / "outputs" / "cross_pair_convergent_leads.jsonl"

    with open(graph_path, encoding="utf-8") as f:
        g = json.load(f)

    # Group edges by Arabic source root
    arabic_roots = collections.defaultdict(lambda: collections.defaultdict(list))
    for edge in g["edges"]:
        src = edge["source"]
        if src.startswith("ara:"):
            root = src.split(":", 1)[1]
            tgt_lang = edge["target"].split(":", 1)[0]
            arabic_roots[root][tgt_lang].append({
                "target_lemma": edge["target"].split(":", 1)[1],
                "score": edge["score"],
                "method": edge.get("method", ""),
            })

    # Filter: 3+ target languages
    convergent = []
    for root, langs in arabic_roots.items():
        if len(langs) >= 3:
            total_edges = sum(len(v) for v in langs.values())
            avg_score = sum(e["score"] for v in langs.values() for e in v) / total_edges
            best_per_lang = {}
            for lang, edges in langs.items():
                best = max(edges, key=lambda e: e["score"])
                best_per_lang[lang] = best
            convergent.append({
                "arabic_root": root,
                "n_languages": len(langs),
                "total_edges": total_edges,
                "avg_score": round(avg_score, 4),
                "languages": sorted(langs.keys()),
                "best_per_language": best_per_lang,
            })

    convergent.sort(key=lambda x: (-x["n_languages"], -x["avg_score"]))

    # Write top 200
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for entry in convergent[:200]:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Exported {min(200, len(convergent))} convergent leads to {output_path}")
    print(f"Total roots with 3+ languages: {len(convergent)}")

if __name__ == "__main__":
    main()
