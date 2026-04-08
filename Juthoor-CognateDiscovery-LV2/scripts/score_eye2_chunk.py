"""Score a chunk of Eye 2 pairs — designed to be run by Codex CLI.

Usage (from Codex):
  codex exec --full-auto "Run python Juthoor-CognateDiscovery-LV2/scripts/score_eye2_chunk.py \
      Juthoor-CognateDiscovery-LV2/outputs/eye2_chunks/grc_chunk_000.jsonl \
      Juthoor-CognateDiscovery-LV2/outputs/eye2_results/grc_chunk_000.jsonl \
      grc"

Reads pairs from chunk JSONL, scores each batch of 10 by printing a prompt
and having Codex/LLM evaluate, writes results to output JSONL.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def format_batch_prompt(pairs: list[dict], lang_name: str) -> str:
    lines = []
    for i, p in enumerate(pairs):
        ara_m = p.get("masadiq_gloss", "") or "(unknown)"
        if p.get("mafahim_gloss"):
            ara_m += f" | conceptual: {p['mafahim_gloss']}"
        lines.append(f'{i}. Arabic "{p["arabic_root"]}" ({ara_m[:200]}) <-> {lang_name} "{p["target_lemma"]}"')

    return (
        f"Score semantic connections between Arabic and {lang_name} words.\n"
        "Arabic meaning is provided (may be Arabic script — read directly).\n"
        f"You know {lang_name} vocabulary — use your knowledge.\n\n"
        "Score 0.0-1.0: 0.0=none, 0.5=weak, 0.8+=strong, 0.95+=certain\n"
        'method: "masadiq_direct"|"mafahim_deep"|"combined"|"weak"(<0.3)\n\n'
        "Pairs:\n" + "\n".join(lines) + "\n\n"
        f"Return JSON array of {len(pairs)} objects: "
        '[{"pair_index":0,"score":0.5,"reasoning":"...","method":"masadiq_direct"},...]\n'
        "ONLY JSON, no markdown."
    )


def main():
    if len(sys.argv) < 4:
        print("Usage: score_eye2_chunk.py <input.jsonl> <output.jsonl> <lang>", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    lang = sys.argv[3]
    lang_names = {"grc": "Ancient Greek", "lat": "Latin", "eng": "English"}
    lang_name = lang_names.get(lang, lang)

    # Load all pairs
    pairs = []
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                pairs.append(json.loads(line))

    print(f"Loaded {len(pairs)} pairs from {input_path}", file=sys.stderr)

    # Process in batches of 10
    output_path.parent.mkdir(parents=True, exist_ok=True)
    batch_size = 10
    total_batches = (len(pairs) + batch_size - 1) // batch_size

    with open(output_path, "w", encoding="utf-8") as out:
        for b in range(0, len(pairs), batch_size):
            batch = pairs[b:b + batch_size]
            prompt = format_batch_prompt(batch, lang_name)

            # Print the prompt — Codex will see this and respond
            print(f"\n--- BATCH {b // batch_size + 1}/{total_batches} ---")
            print(prompt)
            print("--- END PROMPT ---\n")

            # When run interactively by Codex, it processes the prompt
            # For now, write placeholder — Codex will fill in actual scores
            for i, p in enumerate(batch):
                out.write(json.dumps({
                    "source_lemma": p["arabic_root"],
                    "target_lemma": p["target_lemma"],
                    "lang_pair": f"ara-{lang}",
                    "discovery_score": p.get("discovery_score", 0),
                    "semantic_score": -1,  # placeholder — needs scoring
                    "model": "codex",
                    "batch": f"eye2_discovery_{lang}",
                }, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(pairs)} placeholders to {output_path}", file=sys.stderr)
    print("NOTE: This script generates prompts. Run via Codex to get actual scores.", file=sys.stderr)


if __name__ == "__main__":
    main()
