"""Discovery project dashboard — single command for full status."""
import json, sys, glob, collections
from pathlib import Path

LV2_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = LV2_ROOT.parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def main():
    print("=" * 70)
    print("JUTHOOR LV2 DISCOVERY DASHBOARD")
    print("=" * 70)

    # 1. Gold benchmark
    gold_path = LV2_ROOT / "resources/benchmarks/cognate_gold.jsonl"
    gold_counts = collections.Counter()
    if gold_path.exists():
        with open(gold_path, encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                d = json.loads(line)
                pair = f"{d.get('source',{}).get('lang','?')}-{d.get('target',{}).get('lang','?')}"
                gold_counts[pair] += 1
    print(f"\nGold Benchmark: {sum(gold_counts.values())} pairs")
    for pair, n in sorted(gold_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {pair}: {n}")

    # 2. Cognate graph
    graph_path = REPO_ROOT / "outputs" / "cognate_graph.json"
    if not graph_path.exists():
        graph_path = LV2_ROOT / "outputs" / "cognate_graph.json"
    if graph_path.exists():
        with open(graph_path, encoding="utf-8") as f:
            g = json.load(f)
        stats = g.get("stats", {})
        print(f"\nCognate Graph: {stats.get('total_nodes',0)} nodes, {stats.get('total_edges',0)} edges")
        print(f"  Languages: {stats.get('languages', [])}")
        for pair, n in stats.get("lang_pair_counts", {}).items():
            print(f"  {pair}: {n}")

    # 3. Discovery leads summary
    leads_dir = LV2_ROOT / "outputs/leads"
    if leads_dir.exists():
        jsonl_files = sorted(leads_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
        print(f"\nDiscovery Runs: {len(jsonl_files)} lead files")
        for f in jsonl_files[:5]:
            lines = sum(1 for _ in open(f, encoding="utf-8") if _.strip())
            print(f"  {f.name}: {lines} leads ({f.stat().st_size/1024:.0f}KB)")

    # 4. Tests
    print(f"\nTest Suite: run 'python -m pytest' to verify")

    # 5. Convergent evidence
    conv_path = REPO_ROOT / "outputs" / "cross_pair_convergent_leads.jsonl"
    if not conv_path.exists():
        conv_path = LV2_ROOT / "outputs" / "cross_pair_convergent_leads.jsonl"
    if conv_path.exists():
        conv_count = sum(1 for _ in open(conv_path, encoding="utf-8") if _.strip())
        print(f"\nConvergent Leads: {conv_count} roots with 3+ language evidence")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
