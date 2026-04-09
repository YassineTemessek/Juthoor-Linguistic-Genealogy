"""Build target etymology glossary — add etymology chains for Greek/Latin lemmas.

Usage:
  python scripts/build_target_etymology_glossary.py --lang grc --limit 100 --dry-run
  python scripts/build_target_etymology_glossary.py --lang lat --model sonnet --resume
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

LANG_CONFIG = {
    "grc": {
        "label": "Ancient Greek",
        "lemma_file": "greek_unique_lemmas.jsonl",
    },
    "lat": {
        "label": "Latin",
        "lemma_file": "latin_unique_lemmas.jsonl",
    },
}

SONNET_MODEL = "claude-sonnet-4-5"
OPUS_MODEL = "claude-opus-4-5"

PROMPT_TEMPLATE = """\
For the {language} word "{lemma}" (meaning: "{gloss}"):
1. Trace its etymology back through intermediate languages (e.g., English ← French ← Latin ← Greek ← ?)
2. List its derivation family (related words from the same root in the same or daughter languages)
3. Assign 1-3 semantic field tags (e.g., "religion", "nature", "body", "motion", "cognition")

Format as JSON (no prose before or after):
{{"etymology_chain": "step ← step ← ...", "derivation_family": ["word1", "word2"], "semantic_fields": ["field1"], "root_form": "reconstructed or attested root", "possible_semitic_origin": "yes|no|uncertain"}}"""


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


def load_lemmas(lang: str) -> list[dict]:
    cfg = LANG_CONFIG[lang]
    lemma_path = LV2_ROOT / "data" / "processed" / cfg["lemma_file"]
    lemmas = load_jsonl(lemma_path)
    if lemmas:
        print(f"[info] Loaded {len(lemmas)} lemmas from {lemma_path.name}", file=sys.stderr)
        return lemmas
    print(f"[warn] Lemma file not found: {lemma_path}", file=sys.stderr)
    return []


def extract_lemma_info(record: dict) -> tuple[str, str, str]:
    lemma = record.get("lemma", record.get("word", ""))
    gloss = record.get("gloss", record.get("definition", record.get("english", "")))
    ipa = record.get("ipa", "")
    return lemma, gloss, ipa


def build_prompt(lemma: str, gloss: str, language: str) -> str:
    return PROMPT_TEMPLATE.format(
        language=language,
        lemma=lemma,
        gloss=gloss or "no gloss available",
    )


def call_llm(prompt: str, model: str) -> str | None:
    """Call Anthropic API. Imported lazily so --dry-run works without a key."""
    import anthropic  # noqa: PLC0415

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model=model,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text if msg.content else None


def parse_etymology(raw: str, lemma: str) -> dict | None:
    """Extract JSON object from LLM response."""
    raw = raw.strip()
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        print(f"[warn] No JSON object found for lemma {lemma!r}", file=sys.stderr)
        return None
    try:
        obj = json.loads(raw[start:end])
        required = {"etymology_chain", "derivation_family", "semantic_fields", "root_form", "possible_semitic_origin"}
        if not required.issubset(obj.keys()):
            print(f"[warn] Incomplete response for lemma {lemma!r}", file=sys.stderr)
            return None
        return obj
    except json.JSONDecodeError as exc:
        print(f"[warn] JSON parse error for lemma {lemma!r}: {exc}", file=sys.stderr)
        return None


def process_lemmas(
    lemmas: list[dict],
    existing_keys: set[str],
    language_label: str,
    model_id: str,
    dry_run: bool,
    batch_size: int,
) -> list[dict]:
    results: list[dict] = []
    pending = [r for r in lemmas if extract_lemma_info(r)[0] not in existing_keys]
    print(f"[info] {len(pending)} lemmas to process ({len(existing_keys)} already done)", file=sys.stderr)

    for i in range(0, len(pending), batch_size):
        batch = pending[i : i + batch_size]
        for record in batch:
            lemma, gloss, ipa = extract_lemma_info(record)
            if not lemma:
                continue
            prompt = build_prompt(lemma, gloss, language_label)
            if dry_run:
                print(f"[dry-run] Would process lemma: {lemma!r}", file=sys.stderr)
                continue
            print(f"[info] Processing lemma {lemma!r} ({i + 1}/{len(pending)})...", file=sys.stderr)
            raw = call_llm(prompt, model_id)
            if raw is None:
                continue
            parsed = parse_etymology(raw, lemma)
            if parsed is None:
                continue
            entry = {
                "lemma": lemma,
                "gloss": gloss,
                "ipa": ipa,
                **parsed,
            }
            results.append(entry)
            time.sleep(0.2)  # gentle rate limiting
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Build target language etymology glossary via LLM.")
    parser.add_argument("--lang", choices=list(LANG_CONFIG.keys()), required=True, help="Target language code")
    parser.add_argument("--limit", type=int, default=0, help="Max lemmas to process (0=all)")
    parser.add_argument("--model", choices=["sonnet", "opus"], default="sonnet")
    parser.add_argument("--resume", action="store_true", help="Skip lemmas already in output file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without calling LLM")
    parser.add_argument("--batch-size", type=int, default=10, help="Lemmas per processing chunk")
    args = parser.parse_args()

    model_id = OPUS_MODEL if args.model == "opus" else SONNET_MODEL
    cfg = LANG_CONFIG[args.lang]
    output_file = LV2_ROOT / "data" / "enriched" / f"{args.lang}_etymology_glossary.jsonl"

    if not args.dry_run and not os.environ.get("ANTHROPIC_API_KEY"):
        print("[error] ANTHROPIC_API_KEY not set. Use --dry-run to skip API calls.", file=sys.stderr)
        sys.exit(1)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    existing: list[dict] = []
    existing_keys: set[str] = set()
    if args.resume:
        existing = load_jsonl(output_file)
        existing_keys = {e["lemma"] for e in existing}
        print(f"[info] Resume: {len(existing_keys)} lemmas already in glossary", file=sys.stderr)

    lemmas = load_lemmas(args.lang)
    if not lemmas:
        print(f"[error] No lemmas found for language {args.lang!r}.", file=sys.stderr)
        sys.exit(1)

    if args.limit:
        lemmas = lemmas[: args.limit]

    new_entries = process_lemmas(lemmas, existing_keys, cfg["label"], model_id, args.dry_run, args.batch_size)

    if args.dry_run:
        print(f"[dry-run] Would write entries to {output_file}", file=sys.stderr)
        return

    all_entries = existing + new_entries
    with open(output_file, "w", encoding="utf-8") as f:
        for entry in all_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"[done] Wrote {len(all_entries)} entries to {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
