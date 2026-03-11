"""
LV2 discovery-first retrieval CLI.
Orchestrates corpus discovery, embedding, search, and scoring using modular components.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure we can import from src/
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.append(str(SRC_ROOT))

from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import (
    BgeM3Config, ByT5Config, estimate_cost, estimate_tokens,
)
from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import HybridWeights
from juthoor_cognatediscovery_lv2.lv3.discovery.lang import get_language_family

# Modular components
from juthoor_cognatediscovery_lv2.discovery.corpora import (
    CorpusSpec, discover_corpora
)
from juthoor_cognatediscovery_lv2.discovery.retrieval import (
    load_lexemes, embed_corpus, build_or_load_index, search_index
)
from juthoor_cognatediscovery_lv2.discovery.scoring import DiscoveryScorer, rank_candidates
from juthoor_cognatediscovery_lv2.discovery.reporting import write_leads, generate_discovery_report

def parse_spec(value: str) -> CorpusSpec:
    if "=" not in value:
        raise ValueError(f"Invalid spec {value!r}. Expected <lang>[@<stage>]=<path>.")
    left, right = value.split("=", 1)
    parts = [p for p in left.split("@") if p != ""]
    if not parts:
        raise ValueError(f"Invalid spec {value!r}: missing <lang>.")
    lang = parts[0]
    stage = parts[1] if len(parts) >= 2 else "unknown"
    return CorpusSpec(lang=lang, stage=stage, path=Path(right))

def _show_cost_estimate(corpora: dict[str, int], n_passes: int) -> bool:
    total_texts = sum(corpora.values()) * n_passes
    tokens = estimate_tokens(["word"] * total_texts)
    cost, is_free = estimate_cost(tokens)
    cost_str = "FREE (within 3.5M free tier)" if is_free else f"${cost:.4f}"
    print(f"\nAPI Estimate: {total_texts:,} texts, ~{tokens:,} tokens -> {cost_str}")
    return True

def interactive_wizard() -> list[str]:
    print("\n" + "=" * 55 + "\n  Juthoor LV2 — Cognate Discovery Wizard\n" + "=" * 55)
    
    # Backend
    backend = "api" if input("\n  Backend: 1. API [default], 2. Local: ").strip() != "2" else "local"
    
    # Discovery
    corpora = discover_corpora(REPO_ROOT)
    if not corpora:
        print("\n  No corpora found. Run ingestion first.")
        return []

    # Display groups
    from collections import OrderedDict
    groups = OrderedDict()
    for g in ["Arabic", "English", "Latin", "Ancient Greek", "Hebrew", "Other"]:
        for i, c in enumerate(corpora):
            if c.group == g: groups.setdefault(g, []).append((i, c))

    # Source
    print("\n  ── Source ──")
    for g, items in groups.items():
        print(f"  {g}:")
        for idx, c in items: print(f"    {idx + 1:3d}. {c.label:<40s} {c.n_rows:>8,d} words")
    
    src_idx = int(input("\n  Source number [1]: ").strip() or "1") - 1
    src = corpora[src_idx]

    # Targets
    print(f"\n  ── Targets (searching '{src.label}') ──")
    for g, items in groups.items():
        filtered = [(i, c) for i, c in items if i != src_idx]
        if not filtered: continue
        print(f"  {g}:")
        for idx, c in filtered: print(f"    {idx + 1:3d}. {c.label:<40s} {c.n_rows:>8,d} words")

    tgt_input = input("\n  Target numbers (comma-separated): ").strip()
    tgt_specs = [corpora[int(n)-1] for n in tgt_input.split(",") if n.strip()]

    # Build argv
    argv = ["--backend", backend]
    argv += ["--source", f"{src.language}@{src.stage or 'modern'}={src.path}"]
    for c in tgt_specs: argv += ["--target", f"{c.language}@{c.stage or 'modern'}={c.path}"]
    argv += ["--yes"]
    return argv

def main() -> int:
    if len(sys.argv) == 1 or "--interactive" in sys.argv:
        argv = interactive_wizard()
        if not argv: return 1
        sys.argv = [sys.argv[0]] + argv

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--target", action="append", default=[])
    parser.add_argument("--backend", choices=["local", "api"], default="local")
    parser.add_argument("--models", nargs="+", default=["semantic", "form"], choices=["semantic", "form"])
    parser.add_argument("--topk", type=int, default=200)
    parser.add_argument("--max-out", type=int, default=200)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--device", type=str, default=os.environ.get("LV2_DEVICE", "cpu"))
    parser.add_argument("--rebuild-cache", action="store_true")
    parser.add_argument("--rebuild-index", action="store_true")
    parser.add_argument("--no-hybrid", action="store_true")
    parser.add_argument("--w-semantic", type=float, default=HybridWeights.semantic)
    parser.add_argument("--w-form", type=float, default=HybridWeights.form)
    parser.add_argument("--w-orth", type=float, default=HybridWeights.orthography)
    parser.add_argument("--w-sound", type=float, default=HybridWeights.sound)
    parser.add_argument("--w-skeleton", type=float, default=HybridWeights.skeleton)
    parser.add_argument("--pair-id", type=str, default=None)
    parser.add_argument("--min-hybrid", type=float, default=0.0)
    parser.add_argument("--no-report", action="store_true")
    parser.add_argument("-y", "--yes", action="store_true")
    args = parser.parse_args()

    sources = [parse_spec(s) for s in args.source]
    targets = [parse_spec(t) for t in args.target]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    
    if not args.pair_id:
        args.pair_id = f"{'_'.join(s.lang for s in sources)}_vs_{'_'.join(t.lang for t in targets)}"

    # Configuration objects
    weights = HybridWeights(
        semantic=args.w_semantic, form=args.w_form, orthography=args.w_orth,
        sound=args.w_sound, skeleton=args.w_skeleton
    )
    scorer = DiscoveryScorer(weights=weights)

    # 1. Embed and Index targets
    target_data = {m: [] for m in args.models}
    for model in args.models:
        for spec in targets:
            rows = load_lexemes(spec, REPO_ROOT, limit=args.limit)
            vecs, cached_rows = embed_corpus(
                repo_root=REPO_ROOT, model=model, spec=spec, rows=rows,
                device=args.device, rebuild_cache=args.rebuild_cache, backend=args.backend
            )
            idx_name = f"api_{model}" if args.backend == "api" else model
            index = build_or_load_index(repo_root=REPO_ROOT, model=idx_name, spec=spec, vectors=vecs, rebuild_index=args.rebuild_index)
            target_data[model].append((spec, index, cached_rows))

    # 2. Process Sources
    all_leads = []
    for src_spec in sources:
        base_rows = load_lexemes(src_spec, REPO_ROOT, limit=args.limit)
        print(f"[debug] Processing {src_spec.label}...")
        
        src_vectors = {}
        src_rows = None
        for model in args.models:
            vecs, synced_rows = embed_corpus(
                repo_root=REPO_ROOT, model=model, spec=src_spec, rows=base_rows,
                device=args.device, rebuild_cache=args.rebuild_cache, backend=args.backend
            )
            src_vectors[model] = vecs
            if src_rows is None:
                src_rows = synced_rows
        
        if src_rows is None:
            continue

        print(f"[debug] Synced source rows: {len(src_rows)}")

        # 3. Search and Score
        for i, row in enumerate(src_rows):
            candidates = {}
            for model in args.models:
                src_vec = src_vectors[model][i : i + 1]
                for tgt_spec, index, tgt_rows in target_data[model]:
                    scores, idxs = search_index(index, src_vec, topk=args.topk)
                    if len(scores) == 0: continue
                    for score, idx in zip(scores[0], idxs[0]):
                        if idx < 0: continue
                        tgt_row = tgt_rows[idx]
                        key = f"{tgt_spec.label}|{tgt_row.lexeme_id}"
                        entry = candidates.setdefault(key, {
                            "run_id": run_id, "pair_id": args.pair_id,
                            "source": {
                                "id": row.lexeme_id, "lemma": row.lemma, "lang": src_spec.lang,
                                "translit": row.data.get("translit"), "ipa": row.data.get("ipa")
                            },
                            "target": {
                                "id": tgt_row.lexeme_id, "lemma": tgt_row.lemma, "lang": tgt_spec.lang,
                                "translit": tgt_row.data.get("translit"), "ipa": tgt_row.data.get("ipa")
                            },
                            "scores": {}, "retrieved_by": [],
                            "_source_fields": row.data, "_target_fields": tgt_row.data
                        })
                        entry["scores"][model] = float(score)
                        if model not in entry["retrieved_by"]: entry["retrieved_by"].append(model)
            
            # Post-retrieval scoring
            scored = scorer.score(candidates)
            ranked = rank_candidates(scored, max_out=args.max_out, min_hybrid=args.min_hybrid)
            all_leads.extend(ranked)

    # 4. Reporting
    out_path = REPO_ROOT / "outputs" / "leads" / f"discovery_{run_id}.jsonl"
    write_leads(all_leads, out_path)
    print(f"Wrote {len(all_leads)} leads to: {out_path}")
    
    if not args.no_report:
        generate_discovery_report(out_path, Path(__file__).parent)

    return 0

if __name__ == "__main__":
    sys.exit(main())
