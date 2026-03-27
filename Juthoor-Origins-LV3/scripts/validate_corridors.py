"""Validate corridor cards against cognate graph evidence."""
import json, sys, yaml, collections
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LV2_ROOT = REPO_ROOT / "Juthoor-CognateDiscovery-LV2"
LV3_ROOT = REPO_ROOT / "Juthoor-Origins-LV3"

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
    "CORRIDOR_09": "direct_skeleton",  # bilabial subset — can't isolate
    "CORRIDOR_10": "reverse_root",  # meaning predictability via reverse root
}


def main():
    # Load cognate graph
    graph_path = LV2_ROOT / "outputs" / "cognate_graph.json"
    with open(graph_path, encoding="utf-8") as f:
        g = json.load(f)

    # Load corridor cards
    corridors_dir = LV3_ROOT / "data" / "corridors"
    corridors = {}
    for f in sorted(corridors_dir.glob("CORRIDOR_*.yaml")):
        with open(f, encoding="utf-8") as fh:
            card = yaml.safe_load(fh)
        corridors[card["id"]] = card

    # Count edges by method
    method_counts = collections.Counter()
    method_by_root = collections.defaultdict(lambda: collections.defaultdict(set))

    for edge in g["edges"]:
        method = edge.get("method", "")
        src = edge["source"]
        tgt_lang = edge["target"].split(":")[0]
        if method:
            method_counts[method] += 1
            if src.startswith("ara:"):
                root = src.split(":", 1)[1]
                method_by_root[method][root].add(tgt_lang)

    total_edges = g["stats"]["total_edges"]

    print("=" * 70)
    print("CORRIDOR VALIDATION REPORT")
    print("=" * 70)
    print(f"\nCognate graph: {total_edges} edges, {g['stats']['total_nodes']} nodes")
    print(f"Corridors defined: {len(corridors)}")

    print(f"\n{'Corridor':<15} {'Method':<25} {'Edges':>8} {'% Total':>8} {'Roots 2+Lang':>12} {'Status':<15}")
    print("-" * 85)

    for cid, card in sorted(corridors.items()):
        method = CORRIDOR_METHOD_MAP.get(cid, "unknown")
        edge_count = method_counts.get(method, 0)
        pct = 100 * edge_count / max(total_edges, 1)

        # Tier 2: roots with 2+ target languages via this method
        roots_multi = sum(
            1 for root, langs in method_by_root.get(method, {}).items()
            if len(langs) >= 2
        )

        # Status assessment
        if edge_count >= 100 and roots_multi >= 10:
            status = "CONFIRMED"
        elif edge_count >= 20 and roots_multi >= 3:
            status = "PROVISIONAL"
        elif edge_count > 0:
            status = "WEAK"
        else:
            status = "NO DATA"

        print(f"{cid:<15} {method:<25} {edge_count:>8} {pct:>7.1f}% {roots_multi:>12} {status:<15}")

    print("\n" + "=" * 70)
    print("Tier 1: Edge count > 100 AND Tier 2: 10+ roots with 2+ languages = CONFIRMED")
    print("=" * 70)


if __name__ == "__main__":
    main()
