"""
Juthoor LV2 — Eye 1 Recall Evaluator

Checks how many gold benchmark pairs appear in Eye 1's ranked output.
Quality gate: if recall drops, something is broken in the pipeline.

Usage:
  python scripts/discovery/eval_eye1_recall.py \\
      --eye1 outputs/eye1_full_scale_grc.jsonl --lang grc

  python scripts/discovery/eval_eye1_recall.py \\
      --eye1 outputs/eye1_full_scale_lat.jsonl --lang lat \\
      --top-k 50,100,200
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

# Force UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LV2_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOLD = LV2_ROOT / "resources/benchmarks/cognate_gold.jsonl"

# ---------------------------------------------------------------------------
# Arabic normalization (mirrors run_eye1_full_scale._norm_arabic)
# ---------------------------------------------------------------------------

_DIAC_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")
_HAMZA_TR = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ؤ": "و", "ئ": "ي", "ء": "ا",
})


def _norm_arabic(text: str) -> str:
    text = _DIAC_RE.sub("", text)
    return text.translate(_HAMZA_TR).strip()


# ---------------------------------------------------------------------------
# Target lemma normalization (lowercase + strip accents/diacritics)
# ---------------------------------------------------------------------------

def _norm_target(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_gold_pairs(gold_path: Path, lang: str) -> list[dict]:
    """Load gold pairs where source=ara and target=<lang>, OR source=<lang> target=ara."""
    pairs: list[dict] = []
    with open(gold_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            src = rec.get("source", {})
            tgt = rec.get("target", {})
            # Accept ara→lang and lang→ara orientations
            if src.get("lang") == "ara" and tgt.get("lang") == lang:
                pairs.append({
                    "arabic_lemma": src.get("lemma", ""),
                    "target_lemma": tgt.get("lemma", ""),
                    "gloss": src.get("gloss") or tgt.get("gloss") or "",
                })
            elif src.get("lang") == lang and tgt.get("lang") == "ara":
                pairs.append({
                    "arabic_lemma": tgt.get("lemma", ""),
                    "target_lemma": src.get("lemma", ""),
                    "gloss": tgt.get("gloss") or src.get("gloss") or "",
                })
    return pairs


def build_eye1_index(eye1_path: Path, lang: str) -> dict[str, list[str]]:
    """Build mapping: norm_arabic_root → [norm_target_lemma, ...] in ranked order.

    Rows are kept in file order (already sorted by discovery_score desc from the runner).
    """
    index: dict[str, list[str]] = defaultdict(list)
    with open(eye1_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("lang") != lang:
                continue
            root_key = _norm_arabic(rec.get("arabic_root", ""))
            lemma_key = _norm_target(rec.get("target_lemma", ""))
            index[root_key].append(lemma_key)
    return dict(index)


# ---------------------------------------------------------------------------
# Recall computation
# ---------------------------------------------------------------------------

def compute_recall(
    gold_pairs: list[dict],
    eye1_index: dict[str, list[str]],
    k_values: list[int],
) -> dict[int, list[dict]]:
    """Return {k: list_of_missing_gold_pairs} for each k in k_values."""
    missing: dict[int, list[dict]] = {k: [] for k in k_values}

    for pair in gold_pairs:
        ara_key = _norm_arabic(pair["arabic_lemma"])
        tgt_key = _norm_target(pair["target_lemma"])
        candidates = eye1_index.get(ara_key, [])
        for k in k_values:
            top_k = candidates[:k]
            if tgt_key not in top_k:
                missing[k].append(pair)
    return missing


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Eye 1 recall evaluator against gold pairs")
    p.add_argument("--eye1", required=True, help="Path to Eye 1 output JSONL")
    p.add_argument("--lang", required=True, help="Target language code (e.g. grc, lat)")
    p.add_argument(
        "--gold",
        default=str(DEFAULT_GOLD),
        help=f"Gold pairs JSONL (default: {DEFAULT_GOLD})",
    )
    p.add_argument(
        "--top-k",
        default="20,50,100,200",
        help="Comma-separated K values for recall@K (default: 20,50,100,200)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    k_values = sorted(int(k.strip()) for k in args.top_k.split(",") if k.strip())
    gold_path = Path(args.gold)
    eye1_path = Path(args.eye1)

    # Resolve relative paths against LV2_ROOT
    if not gold_path.is_absolute():
        gold_path = LV2_ROOT / gold_path
    if not eye1_path.is_absolute():
        eye1_path = LV2_ROOT / eye1_path

    print(f"[eval] Loading gold pairs from: {gold_path}", file=sys.stderr)
    gold_pairs = load_gold_pairs(gold_path, args.lang)

    print(f"[eval] Loading Eye 1 output from: {eye1_path}", file=sys.stderr)
    eye1_index = build_eye1_index(eye1_path, args.lang)

    total_eye1 = sum(len(v) for v in eye1_index.values())
    n_gold = len(gold_pairs)

    missing_by_k = compute_recall(gold_pairs, eye1_index, k_values)

    # Print report
    out = sys.stderr
    print("", file=out)
    print("=== Eye 1 Recall on Gold Pairs ===", file=out)
    print(f"  Language pair : ara-{args.lang}", file=out)
    print(f"  Gold pairs    : {n_gold}", file=out)
    print(f"  Eye 1 matches : {total_eye1:,}", file=out)
    print("", file=out)

    max_k = max(k_values)
    for k in k_values:
        n_missing = len(missing_by_k[k])
        n_found = n_gold - n_missing
        pct = (n_found / n_gold * 100) if n_gold else 0.0
        label = f"Recall@{k}"
        print(f"  {label:<20} {n_found}/{n_gold} ({pct:.1f}%)", file=out)

    print("", file=out)
    top_missing = missing_by_k[max_k]
    if top_missing:
        print(f"  Missing gold pairs (not in Eye 1 top-{max_k}):", file=out)
        for pair in top_missing:
            gloss = f" ({pair['gloss']})" if pair["gloss"] else ""
            print(f"    {pair['arabic_lemma']} → {pair['target_lemma']}{gloss}", file=out)
    else:
        print(f"  All gold pairs found in Eye 1 top-{max_k}.", file=out)
    print("", file=out)


if __name__ == "__main__":
    main()
