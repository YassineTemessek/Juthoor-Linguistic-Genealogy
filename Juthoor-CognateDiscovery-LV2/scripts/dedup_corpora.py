"""Deduplicate Latin and Greek corpora to unique base lemmas."""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
LV0 = REPO / "Juthoor-DataCore-LV0"
LV2 = REPO / "Juthoor-CognateDiscovery-LV2"

CORPORA = {
    "lat": LV0 / "data/processed/latin/classical/sources/kaikki.jsonl",
    "grc": LV0 / "data/processed/ancient_greek/sources/kaikki.jsonl",
}

OUTPUT_DIR = LV2 / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

_FORM_REF = re.compile(
    r"^(first|second|third)[- ]person|^present |^past |^nominative|^genitive|"
    r"^accusative|^dative|^ablative|^vocative|^plural of|^singular of|"
    r"^inflection of|^alternative form"
)


def _better_gloss(existing: str, candidate: str) -> str:
    if not existing:
        return candidate
    if not candidate:
        return existing
    if _FORM_REF.match(existing.lower()) and not _FORM_REF.match(candidate.lower()):
        return candidate
    if len(candidate) > len(existing) and not _FORM_REF.match(candidate.lower()):
        return candidate
    return existing


def dedup(lang: str, path: Path) -> int:
    lemmas: dict[str, dict] = {}
    total = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            total += 1
            obj = json.loads(line)
            lem = (obj.get("lemma") or "").strip()
            if not lem:
                continue
            if lem in lemmas:
                lemmas[lem]["form_count"] += 1
                lemmas[lem]["gloss"] = _better_gloss(
                    lemmas[lem]["gloss"], obj.get("gloss_plain", "")
                )
                if not lemmas[lem].get("ipa") and obj.get("ipa"):
                    lemmas[lem]["ipa"] = obj["ipa"]
            else:
                lemmas[lem] = {
                    "lemma": lem,
                    "lang": lang,
                    "gloss": obj.get("gloss_plain", "") or "",
                    "ipa": obj.get("ipa", "") or "",
                    "form_count": 1,
                }

    out_name = {"lat": "latin_unique_lemmas.jsonl", "grc": "greek_unique_lemmas.jsonl"}
    out_path = OUTPUT_DIR / out_name[lang]
    with open(out_path, "w", encoding="utf-8") as f:
        for entry in sorted(lemmas.values(), key=lambda x: x["lemma"]):
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"{lang}: {total:,} forms → {len(lemmas):,} unique lemmas → {out_path.name}")
    return len(lemmas)


if __name__ == "__main__":
    for lang, path in CORPORA.items():
        if path.exists():
            dedup(lang, path)
        else:
            print(f"{lang}: file not found at {path}")
