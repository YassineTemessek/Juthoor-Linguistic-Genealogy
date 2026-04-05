from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.append(str(SRC_ROOT))

from juthoor_cognatediscovery_lv2.discovery.benchmarking import load_combined_benchmark, read_jsonl
from juthoor_cognatediscovery_lv2.discovery.corpora import CorpusSpec
from juthoor_cognatediscovery_lv2.discovery.retrieval import resolve_corpus_path


def _norm(text: str) -> str:
    return " ".join(str(text or "").split()).strip().casefold()


def main() -> int:
    parser = argparse.ArgumentParser(description="Report benchmark pair coverage against explicit source/target corpora.")
    parser.add_argument("--benchmark", action="append", required=True, help="Benchmark JSONL path (repeatable).")
    parser.add_argument("--source", required=True, help="Source corpus spec: <lang>[@<stage>]=<path>.")
    parser.add_argument("--target", required=True, help="Target corpus spec: <lang>[@<stage>]=<path>.")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    def parse_spec(value: str) -> CorpusSpec:
        left, right = value.split("=", 1)
        parts = [part for part in left.split("@") if part]
        return CorpusSpec(lang=parts[0], stage=parts[1] if len(parts) > 1 else "unknown", path=Path(right))

    source_spec = parse_spec(args.source)
    target_spec = parse_spec(args.target)
    source_rows = read_jsonl(resolve_corpus_path(source_spec, REPO_ROOT))
    target_rows = read_jsonl(resolve_corpus_path(target_spec, REPO_ROOT))
    source_lemmas = {_norm(row.get("lemma")) for row in source_rows}
    target_lemmas = {_norm(row.get("lemma")) for row in target_rows}

    pairs = load_combined_benchmark([Path(item) for item in args.benchmark])
    covered = []
    missing = []
    for pair in pairs:
        src_ok = pair.source_key[1] in source_lemmas and pair.source_key[0] == _norm(source_spec.lang)
        tgt_ok = pair.target_key[1] in target_lemmas and pair.target_key[0] == _norm(target_spec.lang)
        record = {
            "source": {"lang": pair.source_lang, "lemma": pair.source_lemma},
            "target": {"lang": pair.target_lang, "lemma": pair.target_lemma},
            "relation": pair.relation,
            "covered": bool(src_ok and tgt_ok),
        }
        (covered if record["covered"] else missing).append(record)

    summary = {
        "source_corpus": str(resolve_corpus_path(source_spec, REPO_ROOT)),
        "target_corpus": str(resolve_corpus_path(target_spec, REPO_ROOT)),
        "total_pairs": len(pairs),
        "covered_pairs": len(covered),
        "missing_pairs": len(missing),
        "coverage": round(len(covered) / len(pairs), 6) if pairs else 0.0,
        "by_relation": {},
        "missing": missing,
    }
    rel_counts: dict[str, dict[str, int]] = {}
    for record in covered:
        rel_counts.setdefault(record["relation"], {"covered": 0, "total": 0})
        rel_counts[record["relation"]]["covered"] += 1
    for record in pairs:
        rel_counts.setdefault(record.relation, {"covered": 0, "total": 0})
        rel_counts[record.relation]["total"] += 1
    summary["by_relation"] = {
        rel: {
            **counts,
            "coverage": round(counts["covered"] / counts["total"], 6) if counts["total"] else 0.0,
        }
        for rel, counts in sorted(rel_counts.items())
    }

    payload = json.dumps(summary, ensure_ascii=False, indent=2)
    print(payload)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
