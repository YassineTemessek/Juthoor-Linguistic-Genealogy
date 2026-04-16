"""Eye 2 Agent Scorer — prepare Eye 1 candidates as prompt files for Claude Code agents.

No Anthropic API key required. Agents read the prompt files and return JSON.

Modes:
  --prepare      Filter Eye 1 output, enrich pairs, write batch prompt .txt files
  --score-batch  Print a batch prompt (agent scores it externally, writes JSONL)
  --merge        Merge all scored batch JSONL files into a final output

Usage:
  python eye2_agent_scorer.py --prepare --lang got --min-ds 0.90 --top-k 3 --batch-size 50
  python eye2_agent_scorer.py --score-batch outputs/eye2_agent_batches/got/batch_000.txt
  python eye2_agent_scorer.py --merge --lang got
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from collections import defaultdict

# Ensure stdout handles UTF-8 (Arabic text) on all platforms including Windows.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path bootstrap — allow running this script directly without package install
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = Path(__file__).resolve().parent           # scripts/discovery/
_LV2_ROOT = _SCRIPTS_DIR.parents[1]                      # Juthoor-CognateDiscovery-LV2/
_SRC_DIR = _LV2_ROOT / "src"

if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

# ---------------------------------------------------------------------------
# Import enrichment helpers from eye2_batch_scorer
# ---------------------------------------------------------------------------

from juthoor_cognatediscovery_lv2.discovery.eye2_batch_scorer import (  # noqa: E402
    _norm_arabic_lookup,
    _load_profiles,
    _load_lv0_definitions,
    _load_deep_glossary,
    _load_target_glosses,
    _extract_masadiq_gloss,
    _extract_mafahim_gloss,
    _default_profiles_path,
    _LANG_NAMES,
    load_eye1_candidates,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _outputs_dir() -> Path:
    return _LV2_ROOT / "outputs"

def _batches_dir(lang: str) -> Path:
    return _outputs_dir() / "eye2_agent_batches" / lang

def _results_dir(lang: str) -> Path:
    return _outputs_dir() / "eye2_results" / lang

def _eye1_path(lang: str) -> Path:
    return _outputs_dir() / f"eye1_full_scale_{lang}.jsonl"

def _final_path(lang: str) -> Path:
    return _outputs_dir() / f"eye2_final_{lang}.jsonl"

# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

_prompt_template_cache: str | None = None


def _load_prompt_template() -> str:
    global _prompt_template_cache
    if _prompt_template_cache is not None:
        return _prompt_template_cache
    template_path = _LV2_ROOT / "config" / "eye2_prompt_template.txt"
    if template_path.exists():
        _prompt_template_cache = template_path.read_text(encoding="utf-8")
    else:
        _prompt_template_cache = (
            "You are scoring semantic connections between Arabic words and {LANG_NAME} words.\n"
            "Score 0.0-1.0. Method: masadiq_direct, mafahim_deep, combined, weak.\n\n"
            "{TASK_INSTRUCTION}\n"
            "Return ONLY a JSON array, no markdown fences."
        )
    return _prompt_template_cache


def _build_prompt(pairs: list[dict[str, Any]], lang: str) -> str:
    """Build a complete, self-contained scoring prompt for a batch of pairs."""
    lang_name = _LANG_NAMES.get(lang, lang.upper())
    lines: list[str] = []
    for i, p in enumerate(pairs):
        ara_m = f"masadiq: {p['masadiq_gloss']}" if p.get("masadiq_gloss") else "(no gloss)"
        if p.get("mafahim_gloss"):
            ara_m += f" | mafahim: {p['mafahim_gloss']}"
        if p.get("arabic_meanings_expanded"):
            senses = [
                m["sense"]
                for m in p["arabic_meanings_expanded"][:7]
                if isinstance(m, dict) and m.get("sense")
            ]
            if senses:
                ara_m += " | ALL MEANINGS: " + "; ".join(senses)
        tgt_p = f' ({p["target_meaning"]})' if p.get("target_meaning") else ""
        lines.append(
            f'{i}. Arabic "{p["arabic_root"]}" ({ara_m}) <-> {lang_name} "{p["target_lemma"]}"{tgt_p}'
        )

    n = len(pairs)
    task_instruction = (
        "Score these pairs:\n"
        + "\n".join(lines)
        + f"\n\nReturn a JSON array of exactly {n} objects: "
        '[{"pair_index":0,"score":0.85,"reasoning":"...","method":"masadiq_direct"},...]\n'
    )

    template = _load_prompt_template()
    return template.replace("{LANG_NAME}", lang_name).replace("{TASK_INSTRUCTION}", task_instruction)

# ---------------------------------------------------------------------------
# Enrichment
# ---------------------------------------------------------------------------

def _enrich_candidates(candidates: list[dict[str, Any]], lang: str) -> list[dict[str, Any]]:
    """Enrich each candidate dict in-place with Arabic and target glosses."""
    profiles = _load_profiles(_default_profiles_path())
    lv0_defs = _load_lv0_definitions()
    target_glosses = _load_target_glosses(lang)
    deep = _load_deep_glossary()

    enriched_ara = 0
    enriched_tgt = 0
    enriched_deep = 0

    for c in candidates:
        ar_key = _norm_arabic_lookup(c["arabic_root"])
        c["_ar_key"] = ar_key

        prof = profiles.get(ar_key, {})
        c["masadiq_gloss"] = prof.get("masadiq_gloss", "")
        c["mafahim_gloss"] = prof.get("mafahim_gloss", "")

        # LV0 fallback when no profile exists
        if not c["masadiq_gloss"] and not c["mafahim_gloss"]:
            c["masadiq_gloss"] = lv0_defs.get(ar_key, "")

        if c["masadiq_gloss"] or c["mafahim_gloss"]:
            enriched_ara += 1

        tgt_entry = target_glosses.get(c["target_lemma"], {})
        c["target_meaning"] = tgt_entry.get("gloss", "")
        if c["target_meaning"]:
            enriched_tgt += 1

        expanded = deep.get(ar_key, {}).get("meanings", [])
        c["arabic_meanings_expanded"] = expanded
        if expanded:
            enriched_deep += 1

    total = len(candidates)
    print(
        f"[info] Arabic enrichment: {enriched_ara}/{total} "
        f"| Target glosses: {enriched_tgt}/{total} "
        f"| Deep glossary: {enriched_deep}/{total}",
        file=sys.stderr,
    )
    return candidates

# ---------------------------------------------------------------------------
# Mode 1: --prepare
# ---------------------------------------------------------------------------

def cmd_prepare(args: argparse.Namespace) -> None:
    lang = args.lang
    min_ds: float = args.min_ds
    top_k: int = args.top_k
    batch_size: int = args.batch_size

    eye1_path = _eye1_path(lang)
    if not eye1_path.exists():
        print(f"[error] Eye 1 file not found: {eye1_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[info] Loading Eye 1 candidates from {eye1_path}", file=sys.stderr)
    candidates = load_eye1_candidates(
        input_path=eye1_path,
        min_discovery_score=min_ds,
        top_n_per_root=top_k,
        lang_filter=lang,
    )
    print(f"[info] {len(candidates)} candidates after filtering (min_ds={min_ds}, top_k={top_k}).", file=sys.stderr)

    if not candidates:
        print("[warn] No candidates to process. Check --min-ds and --top-k.", file=sys.stderr)
        sys.exit(0)

    candidates = _enrich_candidates(candidates, lang)

    # Split into batches and write prompt files
    out_dir = _batches_dir(lang)
    out_dir.mkdir(parents=True, exist_ok=True)

    batches: list[list[dict[str, Any]]] = []
    for start in range(0, len(candidates), batch_size):
        batches.append(candidates[start: start + batch_size])

    batch_meta: list[dict[str, Any]] = []
    for idx, batch in enumerate(batches):
        prompt = _build_prompt(batch, lang)
        batch_file = out_dir / f"batch_{idx:03d}.txt"
        batch_file.write_text(prompt, encoding="utf-8")

        # Store pair metadata alongside prompt so --score-batch can reconstruct results
        meta_file = out_dir / f"batch_{idx:03d}_meta.json"
        meta_pairs = [
            {
                "pair_index": i,
                "arabic_root": p["arabic_root"],
                "target_lemma": p["target_lemma"],
                "lang": p.get("lang", lang),
                "discovery_score": float(p.get("discovery_score", 0.0)),
                "masadiq_gloss": p.get("masadiq_gloss", ""),
                "mafahim_gloss": p.get("mafahim_gloss", ""),
                "target_meaning": p.get("target_meaning", ""),
            }
            for i, p in enumerate(batch)
        ]
        meta_file.write_text(json.dumps(meta_pairs, ensure_ascii=False, indent=2), encoding="utf-8")

        batch_meta.append({"batch_index": idx, "file": str(batch_file), "n_pairs": len(batch)})
        print(f"[info] Wrote batch_{idx:03d}.txt ({len(batch)} pairs)", file=sys.stderr)

    # Write manifest
    manifest = {
        "lang": lang,
        "total_pairs": len(candidates),
        "batch_count": len(batches),
        "batch_size": batch_size,
        "min_ds": min_ds,
        "top_k": top_k,
        "batches": batch_meta,
        "instructions": (
            "For each batch_{NNN}.txt, send the file contents to a Claude Code agent. "
            "The agent returns a JSON array. Pipe that to: "
            f"python eye2_agent_scorer.py --ingest-response --lang {lang} "
            "--batch-index NNN --response-file <agent_output.json>"
        ),
    }
    manifest_file = out_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[done] {len(batches)} batch files written to {out_dir}", file=sys.stderr)
    print(f"[done] Manifest: {manifest_file}", file=sys.stderr)
    print(
        f"\nNext step: for each batch_NNN.txt, send it to a Claude Code agent and save "
        f"the JSON response, then run:\n"
        f"  python eye2_agent_scorer.py --ingest-response --lang {lang} "
        f"--batch-index NNN --response-file <path-to-agent-response.json>",
        file=sys.stderr,
    )

# ---------------------------------------------------------------------------
# Mode 2: --score-batch  (print prompt; agents score externally)
# ---------------------------------------------------------------------------

def cmd_score_batch(args: argparse.Namespace) -> None:
    """Print the prompt for a batch file to stdout (for piping to an agent)."""
    batch_file = Path(args.score_batch)
    if not batch_file.exists():
        print(f"[error] Batch file not found: {batch_file}", file=sys.stderr)
        sys.exit(1)
    # Just print the prompt — the agent is the scorer.
    print(batch_file.read_text(encoding="utf-8"))

    if args.output:
        # If --output given, remind user how to pipe the agent response back.
        print(
            f"\n# [info] After receiving the agent JSON response, save it to a file and run:\n"
            f"#   python eye2_agent_scorer.py --ingest-response "
            f"--batch-meta {batch_file.with_name(batch_file.stem + '_meta.json')} "
            f"--response-file <agent_response.json> --output {args.output}",
            file=sys.stderr,
        )

# ---------------------------------------------------------------------------
# Mode 2b: --ingest-response  (parse agent JSON and write scored JSONL)
# ---------------------------------------------------------------------------

def cmd_ingest_response(args: argparse.Namespace) -> None:
    """Parse agent JSON response for a batch and write JSONL results."""
    lang = args.lang

    # Resolve meta file: either explicit --batch-meta or derived from --batch-index
    if args.batch_meta:
        meta_file = Path(args.batch_meta)
    elif args.batch_index is not None:
        meta_file = _batches_dir(lang) / f"batch_{args.batch_index:03d}_meta.json"
    else:
        print("[error] Provide --batch-meta <path> or --batch-index <N>.", file=sys.stderr)
        sys.exit(1)

    if not meta_file.exists():
        print(f"[error] Batch meta file not found: {meta_file}", file=sys.stderr)
        sys.exit(1)

    response_file = Path(args.response_file)
    if not response_file.exists():
        print(f"[error] Response file not found: {response_file}", file=sys.stderr)
        sys.exit(1)

    meta_pairs: list[dict[str, Any]] = json.loads(meta_file.read_text(encoding="utf-8"))
    raw_response = response_file.read_text(encoding="utf-8").strip()

    # Strip markdown fences if present
    if raw_response.startswith("```"):
        parts = raw_response.split("```", 2)
        inner = parts[1]
        if inner.startswith("json"):
            inner = inner[4:]
        raw_response = inner.strip()

    try:
        results: list[dict[str, Any]] = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        print(f"[error] Failed to parse agent JSON response: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        out_path = Path(args.output)
    else:
        # Default: outputs/eye2_results/{lang}/batch_{NNN}.jsonl
        batch_stem = meta_file.stem.replace("_meta", "")
        out_path = _results_dir(lang) / f"{batch_stem}.jsonl"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    with open(out_path, "w", encoding="utf-8") as fh:
        for item in results:
            idx = item.get("pair_index", 0)
            if not isinstance(idx, int) or idx >= len(meta_pairs):
                print(f"[warn] Skipping item with out-of-range pair_index={idx}", file=sys.stderr)
                continue
            c = meta_pairs[idx]
            fh.write(
                json.dumps(
                    {
                        "source_lemma": c["arabic_root"],
                        "target_lemma": c["target_lemma"],
                        "lang_pair": f"ara-{c.get('lang', lang)}",
                        "semantic_score": float(item.get("score", 0.0)),
                        "reasoning": str(item.get("reasoning", "")),
                        "method": str(item.get("method", "unknown")),
                        "discovery_score": float(c.get("discovery_score", 0.0)),
                        "model": "agent",
                        "batch": meta_file.stem.replace("_meta", ""),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            written += 1

    print(f"[done] Wrote {written} scored pairs to {out_path}", file=sys.stderr)

# ---------------------------------------------------------------------------
# Mode 3: --merge
# ---------------------------------------------------------------------------

def cmd_merge(args: argparse.Namespace) -> None:
    lang = args.lang
    results_dir = _results_dir(lang)

    batch_files = sorted(results_dir.glob("batch_*.jsonl")) if results_dir.exists() else []
    if not batch_files:
        print(f"[error] No batch JSONL files found in {results_dir}", file=sys.stderr)
        sys.exit(1)

    all_records: list[dict[str, Any]] = []
    for bf in batch_files:
        with open(bf, encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    all_records.append(json.loads(raw))
                except json.JSONDecodeError:
                    continue
        print(f"[info] Loaded {bf.name}", file=sys.stderr)

    # Deduplicate: keep highest semantic_score per (source, target) pair
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for rec in all_records:
        key = (rec.get("source_lemma", ""), rec.get("target_lemma", ""))
        existing = best.get(key)
        if existing is None or float(rec.get("semantic_score", 0.0)) > float(existing.get("semantic_score", 0.0)):
            best[key] = rec

    merged = sorted(best.values(), key=lambda r: float(r.get("semantic_score", 0.0)), reverse=True)

    final_path = _final_path(lang)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    with open(final_path, "w", encoding="utf-8") as fh:
        for rec in merged:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # Score distribution summary
    buckets: defaultdict[str, int] = defaultdict(int)
    discoveries = 0
    for rec in merged:
        s = float(rec.get("semantic_score", 0.0))
        if s >= 0.95:
            buckets["≥0.95"] += 1
        elif s >= 0.80:
            buckets["≥0.80"] += 1
        elif s >= 0.65:
            buckets["≥0.65"] += 1
        elif s >= 0.50:
            buckets["≥0.50"] += 1
        elif s >= 0.30:
            buckets["≥0.30"] += 1
        else:
            buckets["<0.30"] += 1
        if s >= 0.50:
            discoveries += 1

    print(f"\n[merge] Total scored: {len(merged)}", file=sys.stderr)
    print(f"[merge] Score distribution:", file=sys.stderr)
    for label in ("≥0.95", "≥0.80", "≥0.65", "≥0.50", "≥0.30", "<0.30"):
        print(f"  {label}: {buckets[label]}", file=sys.stderr)
    print(f"[merge] Discoveries (score ≥ 0.50): {discoveries}", file=sys.stderr)
    print(f"[done] Merged output: {final_path}", file=sys.stderr)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Eye 2 Agent Scorer: prepare/merge LLM-scored Eye 2 batches (no API key).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true", help="Prepare batch prompt files from Eye 1 output.")
    mode.add_argument("--score-batch", metavar="BATCH_FILE", help="Print batch prompt to stdout (agent scores externally).")
    mode.add_argument("--ingest-response", action="store_true", help="Parse agent JSON response and write scored JSONL.")
    mode.add_argument("--merge", action="store_true", help="Merge all scored batch JSONL files into final output.")

    # --prepare options
    p.add_argument("--lang", help="Target language code (got, grc, lat, ...)")
    p.add_argument("--min-ds", type=float, default=0.90, metavar="SCORE",
                   help="Minimum Eye 1 discovery_score to include (default: 0.90).")
    p.add_argument("--top-k", type=int, default=3, metavar="K",
                   help="Max candidates per Arabic root (default: 3).")
    p.add_argument("--batch-size", type=int, default=50, metavar="N",
                   help="Pairs per batch file (default: 50).")

    # --ingest-response options
    p.add_argument("--batch-index", type=int, metavar="N",
                   help="Batch index (used to locate batch_NNN_meta.json).")
    p.add_argument("--batch-meta", metavar="FILE",
                   help="Explicit path to batch_NNN_meta.json.")
    p.add_argument("--response-file", metavar="FILE",
                   help="Path to agent JSON response file.")

    # shared
    p.add_argument("--output", metavar="FILE",
                   help="Output file path (used by --ingest-response and --score-batch).")

    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    if args.prepare:
        if not args.lang:
            print("[error] --prepare requires --lang.", file=sys.stderr)
            sys.exit(1)
        cmd_prepare(args)

    elif args.score_batch:
        cmd_score_batch(args)

    elif args.ingest_response:
        if not args.response_file:
            print("[error] --ingest-response requires --response-file.", file=sys.stderr)
            sys.exit(1)
        if not args.lang and not args.batch_meta:
            print("[error] --ingest-response requires --lang (or --batch-meta).", file=sys.stderr)
            sys.exit(1)
        cmd_ingest_response(args)

    elif args.merge:
        if not args.lang:
            print("[error] --merge requires --lang.", file=sys.stderr)
            sys.exit(1)
        cmd_merge(args)


if __name__ == "__main__":
    main()
