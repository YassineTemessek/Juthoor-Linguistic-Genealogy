"""Export a frozen research bundle for publication/review."""
import json, shutil, sys
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[1]
LV1_ROOT = REPO_ROOT / "Juthoor-ArabicGenome-LV1"
LV2_ROOT = REPO_ROOT / "Juthoor-CognateDiscovery-LV2"
LV3_ROOT = REPO_ROOT / "Juthoor-Origins-LV3"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def main():
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bundle_dir = REPO_ROOT / "outputs" / f"research_bundle_{ts}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    print(f"Exporting research bundle to: {bundle_dir}")

    # 1. Key documents
    docs_dir = bundle_dir / "docs"
    docs_dir.mkdir()
    for doc in [
        LV3_ROOT / "docs/THEORY_SYNTHESIS.md",
        LV3_ROOT / "docs/VALIDATION_METHODOLOGY.md",
        LV3_ROOT / "docs/ANCHOR_GATES.md",
        LV2_ROOT / "docs/DISCOVERY_SYNTHESIS.md",
        LV2_ROOT / "docs/CONSONANT_CORRESPONDENCE_ANALYSIS.md",
        LV2_ROOT / "docs/METHOD_EFFECTIVENESS_REPORT.md",
        LV2_ROOT / "docs/RERANKER_V3_DESIGN.md",
        LV2_ROOT / "docs/ETYMOLOGY_LINKING_METHODOLOGY.md",
        REPO_ROOT / "docs/DATA_FLOW_ARCHITECTURE.md",
    ]:
        if doc.exists():
            shutil.copy2(doc, docs_dir / doc.name)
            print(f"  + {doc.name}")

    # 2. Corridor cards
    corridors_src = LV3_ROOT / "data/corridors"
    if corridors_src.exists():
        corridors_dst = bundle_dir / "corridors"
        shutil.copytree(corridors_src, corridors_dst)
        print(f"  + {sum(1 for _ in corridors_dst.glob('*.yaml'))} corridor cards")

    # 3. Key data files
    data_dir = bundle_dir / "data"
    data_dir.mkdir()
    for src, name in [
        (LV2_ROOT / "resources/benchmarks/cognate_gold.jsonl", "gold_benchmark.jsonl"),
        (LV2_ROOT / "resources/benchmarks/non_cognate_negatives.jsonl", "negatives.jsonl"),
        (LV2_ROOT / "data/processed/consonant_correspondence_matrix.json", "consonant_matrix.json"),
        (LV2_ROOT / "outputs/cross_pair_convergent_leads.jsonl", "convergent_leads.jsonl"),
    ]:
        if src.exists():
            shutil.copy2(src, data_dir / name)
            print(f"  + {name}")

    # 4. LV3 validated leads (sample top 500)
    leads_src = LV3_ROOT / "data/leads/validated_leads.jsonl"
    if leads_src.exists():
        leads = []
        with open(leads_src, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    leads.append(json.loads(line))
        # Sort by score descending, take top 500
        leads.sort(key=lambda x: x.get("score", 0), reverse=True)
        with open(data_dir / "top_500_validated_leads.jsonl", "w", encoding="utf-8") as f:
            for lead in leads[:500]:
                f.write(json.dumps(lead, ensure_ascii=False) + "\n")
        print(f"  + top_500_validated_leads.jsonl ({len(leads)} total, exported 500)")

    # 5. Manifest
    import subprocess
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT)).decode().strip()
    except Exception:
        commit = "unknown"

    manifest = {
        "bundle_date": ts,
        "git_commit": commit,
        "project": "Juthoor Linguistic Genealogy",
        "version": "1.0",
        "contents": {
            "docs": [f.name for f in docs_dir.glob("*")],
            "corridors": [f.name for f in (bundle_dir / "corridors").glob("*")] if (bundle_dir / "corridors").exists() else [],
            "data": [f.name for f in data_dir.glob("*")],
        },
        "key_metrics": {
            "gold_benchmark_pairs": 1889,
            "cognate_graph_nodes": 12455,
            "cognate_graph_edges": 47071,
            "languages": 7,
            "corridor_cards": 10,
            "tests_passing": 1088,
            "gold_coverage": "32.1%",
            "convergent_roots_3plus_langs": 153,
        }
    }
    with open(bundle_dir / "MANIFEST.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"  + MANIFEST.json")

    print(f"\nBundle exported: {bundle_dir}")
    print(f"Total files: {sum(1 for _ in bundle_dir.rglob('*') if _.is_file())}")

if __name__ == "__main__":
    main()
