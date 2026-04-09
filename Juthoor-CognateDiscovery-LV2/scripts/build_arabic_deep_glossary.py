"""Build deep Arabic glossary — expand each root to 5-10 meanings.

Usage:
  python scripts/build_arabic_deep_glossary.py --limit 100 --model sonnet --dry-run
  python scripts/build_arabic_deep_glossary.py --model opus --resume
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

LV2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = LV2_ROOT.parent

PRIMARY_ROOTS = LV2_ROOT / "data" / "processed" / "arabic_genome_roots_discovery.jsonl"
PROFILES_FILE = LV2_ROOT / "data" / "llm_annotations" / "arabic_semantic_profiles.jsonl"
OUTPUT_FILE = LV2_ROOT / "data" / "enriched" / "arabic_deep_glossary.jsonl"

SONNET_MODEL = "claude-sonnet-4-5"
OPUS_MODEL = "claude-opus-4-5"

PROMPT_TEMPLATE = """\
You are an expert in Classical Arabic lexicography. For the Arabic root "{root}" ({definition}), list 5-10 distinct meanings including:
1. Primary dictionary meaning (masadiq)
2. Secondary meanings
3. Archaic or poetic meanings
4. Derived verbal forms (Form II-X) and their meanings
5. Related nouns and their meanings

Format as JSON array: [{{"sense": "English meaning", "arabic": "Arabic form", "type": "masadiq|archaic|verb|noun|conceptual"}}]
Only output valid JSON — no prose before or after."""


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def load_roots() -> list[dict]:
    """Load Arabic roots from primary file, fall back to profiles."""
    roots = load_jsonl(PRIMARY_ROOTS)
    if roots:
        print(f"[info] Loaded {len(roots)} roots from {PRIMARY_ROOTS.name}", file=sys.stderr)
        return roots
    profiles = load_jsonl(PROFILES_FILE)
    if profiles:
        print(f"[info] Falling back to {len(profiles)} profiles from {PROFILES_FILE.name}", file=sys.stderr)
        return profiles
    print("[warn] No root source found — checked primary file and profiles.", file=sys.stderr)
    return []


def extract_root_info(record: dict) -> tuple[str, str]:
    root = record.get("root", record.get("lemma", ""))
    definition = record.get("definition", record.get("gloss", record.get("english", "")))
    return root, definition


def build_prompt(root: str, definition: str) -> str:
    return PROMPT_TEMPLATE.format(root=root, definition=definition or "no gloss available")


def call_llm(prompt: str, model: str) -> str | None:
    """Call Anthropic API. Imported lazily so --dry-run works without a key."""
    import anthropic  # noqa: PLC0415

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text if msg.content else None


def parse_meanings(raw: str, root: str) -> list[dict]:
    """Extract JSON array from LLM response."""
    raw = raw.strip()
    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start == -1 or end == 0:
        print(f"[warn] No JSON array found for root {root!r}", file=sys.stderr)
        return []
    try:
        meanings = json.loads(raw[start:end])
        return [m for m in meanings if isinstance(m, dict) and "sense" in m]
    except json.JSONDecodeError as exc:
        print(f"[warn] JSON parse error for root {root!r}: {exc}", file=sys.stderr)
        return []


def infer_semantic_fields(meanings: list[dict]) -> list[str]:
    fields: set[str] = set()
    field_keywords = {
        "knowledge": ["know", "science", "learn", "teach", "wisdom"],
        "movement": ["move", "walk", "travel", "flow", "run"],
        "communication": ["speak", "say", "call", "name", "sign"],
        "physical": ["body", "hand", "eye", "head", "foot", "stone"],
        "nature": ["water", "earth", "fire", "sky", "tree", "plant"],
        "power": ["strong", "force", "rule", "command", "king"],
        "religion": ["god", "holy", "sacred", "pray", "worship"],
    }
    senses = " ".join(m.get("sense", "").lower() for m in meanings)
    for field, keywords in field_keywords.items():
        if any(kw in senses for kw in keywords):
            fields.add(field)
    return sorted(fields)


def process_roots(
    roots: list[dict],
    existing_keys: set[str],
    model_id: str,
    dry_run: bool,
    batch_size: int,
) -> list[dict]:
    results: list[dict] = []
    pending = [r for r in roots if extract_root_info(r)[0] not in existing_keys]
    print(f"[info] {len(pending)} roots to process ({len(existing_keys)} already done)", file=sys.stderr)

    for i in range(0, len(pending), batch_size):
        batch = pending[i : i + batch_size]
        for record in batch:
            root, definition = extract_root_info(record)
            if not root:
                continue
            prompt = build_prompt(root, definition)
            if dry_run:
                print(f"[dry-run] Would process root: {root!r}", file=sys.stderr)
                continue
            print(f"[info] Processing root {root!r} ({i + 1}/{len(pending)})...", file=sys.stderr)
            raw = call_llm(prompt, model_id)
            if raw is None:
                continue
            meanings = parse_meanings(raw, root)
            if not meanings:
                continue
            entry = {
                "root": root,
                "root_norm": root.replace("ا", "").replace("و", "").replace("ي", ""),
                "meanings": meanings,
                "binary_root": root[:2] if len(root) >= 2 else root,
                "semantic_fields": infer_semantic_fields(meanings),
            }
            results.append(entry)
            time.sleep(0.2)  # gentle rate limiting
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Build deep Arabic glossary via LLM.")
    parser.add_argument("--limit", type=int, default=0, help="Max roots to process (0=all)")
    parser.add_argument("--model", choices=["sonnet", "opus"], default="sonnet")
    parser.add_argument("--resume", action="store_true", help="Skip roots already in output file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without calling LLM")
    parser.add_argument("--batch-size", type=int, default=10, help="Roots per LLM call chunk")
    args = parser.parse_args()

    model_id = OPUS_MODEL if args.model == "opus" else SONNET_MODEL

    if not args.dry_run and not os.environ.get("ANTHROPIC_API_KEY"):
        print("[error] ANTHROPIC_API_KEY not set. Use --dry-run to skip API calls.", file=sys.stderr)
        sys.exit(1)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    existing: list[dict] = []
    existing_keys: set[str] = set()
    if args.resume:
        existing = load_jsonl(OUTPUT_FILE)
        existing_keys = {e["root"] for e in existing}
        print(f"[info] Resume: {len(existing_keys)} roots already in glossary", file=sys.stderr)

    roots = load_roots()
    if not roots:
        print("[error] No roots to process.", file=sys.stderr)
        sys.exit(1)

    if args.limit:
        roots = roots[: args.limit]

    new_entries = process_roots(roots, existing_keys, model_id, args.dry_run, args.batch_size)

    if args.dry_run:
        print(f"[dry-run] Would write {len(roots) - len(existing_keys)} entries to {OUTPUT_FILE}", file=sys.stderr)
        return

    all_entries = existing + new_entries
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for entry in all_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"[done] Wrote {len(all_entries)} entries to {OUTPUT_FILE}", file=sys.stderr)


if __name__ == "__main__":
    main()
