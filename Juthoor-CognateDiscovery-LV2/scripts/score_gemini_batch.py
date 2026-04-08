"""Score an Eye 2 batch via Gemini CLI.

Usage: python scripts/score_gemini_batch.py <batch_file> <output_file>
Example: python scripts/score_gemini_batch.py outputs/eye2_batches/grc_b0024.jsonl outputs/eye2_results/grc_b0024.jsonl
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

LV2_ROOT = Path(__file__).resolve().parents[1]

PROMPT_TEMPLATE = """You are a Juthoor linguistic cognate expert. Arabic preserves the oldest Semitic phonetics. When words traveled into Greek, consonants merged but MEANINGS persisted.

Arabic roots have MASADIQ (dictionary) and MAFAHIM (conceptual core). Read Arabic script directly.

Score 0.0-1.0: 0.0=unrelated, 0.3=faint, 0.5=plausible path, 0.7=clear chain, 0.9=strong, 0.95+=identical.
Method: masadiq_direct, mafahim_deep, combined, weak(<0.3).

Look for: both sides of a concept, semantic drift (concrete to abstract, action to result, agent to place).
Calibration: شرب to absorb=0.85, اثم to Θέμις=0.65, اثكل to λιθόκολλα=0.50.

Score these Arabic-Greek pairs:
{pairs_text}

Return ONLY a raw JSON array starting with [ and ending with ]. No markdown, no backticks, no commentary.
[{{"pair_index":0,"score":0.0,"reasoning":"brief","method":"weak"}},...]"""


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: score_gemini_batch.py <batch.jsonl> <output.jsonl>", file=sys.stderr)
        sys.exit(1)

    batch_path = LV2_ROOT / sys.argv[1] if not Path(sys.argv[1]).is_absolute() else Path(sys.argv[1])
    output_path = LV2_ROOT / sys.argv[2] if not Path(sys.argv[2]).is_absolute() else Path(sys.argv[2])

    # Load pairs
    pairs = []
    with open(batch_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                pairs.append(json.loads(line))

    # Process in sub-batches of 10 (Gemini handles smaller prompts reliably)
    gemini_cmd = "C:/Users/yassi/AppData/Roaming/npm/gemini.cmd"
    sub_batch_size = 10
    output_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    total_subs = (len(pairs) + sub_batch_size - 1) // sub_batch_size

    print(f"[gemini] Scoring {len(pairs)} pairs in {total_subs} sub-batches from {batch_path.name}...", file=sys.stderr)

    with open(output_path, "w", encoding="utf-8") as out_f:
        for sb_start in range(0, len(pairs), sub_batch_size):
            sb = pairs[sb_start:sb_start + sub_batch_size]
            sb_lines = []
            for i, p in enumerate(sb):
                m = (p.get("masadiq_gloss", "") or "")[:150]
                sb_lines.append(f'{i}. Arabic "{p["arabic_root"]}" ({m}) <-> Greek "{p["target_lemma"]}"')

            prompt = PROMPT_TEMPLATE.format(pairs_text="\n".join(sb_lines))
            sub_num = sb_start // sub_batch_size + 1
            print(f"  [{sub_num}/{total_subs}]...", end="", file=sys.stderr, flush=True)

            try:
                result = subprocess.run(
                    [gemini_cmd, "-p", prompt],
                    capture_output=True, text=True, timeout=180,
                    cwd="C:/Users/yassi/AppData/Local/Temp",
                )
            except subprocess.TimeoutExpired:
                print(" timeout, skip", file=sys.stderr)
                continue

            raw = result.stdout.strip()
            if not raw:
                print(" empty, skip", file=sys.stderr)
                continue

            # Strip markdown fences
            if "```" in raw:
                for part in raw.split("```"):
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:].strip()
                    if part.startswith("["):
                        raw = part
                        break

            start_idx = raw.find("[")
            end_idx = raw.rfind("]")
            if start_idx == -1 or end_idx == -1:
                print(" no JSON, skip", file=sys.stderr)
                continue

            try:
                scores = json.loads(raw[start_idx:end_idx + 1])
            except json.JSONDecodeError:
                print(" parse fail, skip", file=sys.stderr)
                continue

            sub_written = 0
            for item in scores:
                idx = item.get("pair_index", 0)
                if idx < len(sb):
                    out_f.write(json.dumps({
                        "source_lemma": sb[idx]["arabic_root"],
                        "target_lemma": sb[idx]["target_lemma"],
                        "semantic_score": float(item.get("score", 0)),
                        "reasoning": str(item.get("reasoning", "")),
                        "method": str(item.get("method", "weak")),
                        "lang_pair": "ara-grc",
                        "model": "gemini",
                    }, ensure_ascii=False) + "\n")
                    sub_written += 1
            out_f.flush()
            written += sub_written
            print(f" {sub_written} scored", file=sys.stderr)

    print(f"[gemini] Total: {written}/{len(pairs)} results to {output_path.name}", file=sys.stderr)


if __name__ == "__main__":
    main()
