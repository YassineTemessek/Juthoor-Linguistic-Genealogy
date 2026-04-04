"""Prepare Arabic genome roots for full-scale Eye 1 discovery."""
import json
import re
import sys
from pathlib import Path
from glob import glob

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
LV1 = REPO / "Juthoor-ArabicGenome-LV1"
LV2 = REPO / "Juthoor-CognateDiscovery-LV2"

GENOME_DIR = LV1 / "outputs" / "genome"
PROFILES_PATH = LV2 / "data" / "llm_annotations" / "arabic_semantic_profiles.jsonl"
OUTPUT_DIR = LV2 / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "arabic_genome_roots_discovery.jsonl"

_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED\u0640]"
)

# Arabic consonant → primary Latin equivalent
_AR_TO_LAT = {
    "ب": "b", "ت": "t", "ث": "th", "ج": "j", "ح": "h", "خ": "kh",
    "د": "d", "ذ": "dh", "ر": "r", "ز": "z", "س": "s", "ش": "sh",
    "ص": "s", "ض": "d", "ط": "t", "ظ": "dh", "ع": "", "غ": "gh",
    "ف": "f", "ق": "q", "ك": "k", "ل": "l", "م": "m", "ن": "n",
    "ه": "h", "و": "w", "ي": "y", "ء": "", "ئ": "", "ؤ": "",
    "أ": "", "إ": "", "آ": "", "ا": "",
}


def normalize(text: str) -> str:
    text = _DIACRITICS.sub("", text)
    text = text.replace("\u0640", "")
    text = re.sub(r"[إأآ]", "ا", text)
    return text.strip("،, \t\n")


def arabic_to_skeleton(root: str) -> str:
    norm = normalize(root)
    parts = []
    for ch in norm:
        lat = _AR_TO_LAT.get(ch)
        if lat is not None and lat:
            parts.append(lat)
    return "".join(parts)


def main():
    # Load profiles indexed by normalized root and lemma
    profiles_by_root: dict[str, dict] = {}
    profiles_by_lemma: dict[str, dict] = {}
    if PROFILES_PATH.exists():
        with open(PROFILES_PATH, encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                r = normalize(obj.get("root") or "")
                if r:
                    profiles_by_root[r] = obj
                ln = normalize(obj.get("lemma") or "")
                if ln:
                    profiles_by_lemma[ln] = obj

    # Load genome roots from all BAB files
    roots: dict[str, dict] = {}  # normalized root → entry
    genome_files = sorted(glob(str(GENOME_DIR / "*.jsonl")))
    for gf in genome_files:
        with open(gf, encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                root = obj.get("root", "")
                if not root:
                    continue
                norm_root = normalize(root)
                if norm_root in roots:
                    # Merge words
                    existing_words = set(roots[norm_root].get("words", []))
                    existing_words.update(obj.get("words", []))
                    roots[norm_root]["words"] = list(existing_words)
                else:
                    roots[norm_root] = {
                        "root_raw": root,
                        "root_norm": norm_root,
                        "binary_root": obj.get("binary_root", norm_root[:2] if len(norm_root) >= 2 else norm_root),
                        "bab": obj.get("bab", ""),
                        "words": obj.get("words", []),
                    }

    # Build discovery entries
    full = partial = no_prof = 0
    skeletons = set()
    entries = []

    for norm_root, rdata in sorted(roots.items()):
        skel = arabic_to_skeleton(rdata["root_raw"])
        skeletons.add(skel)

        # Look up profile
        prof = profiles_by_root.get(norm_root) or profiles_by_lemma.get(norm_root)
        maf = prof.get("mafahim", {}) if prof else {}
        mas = prof.get("masadiq", {}) if prof else {}

        maf_gloss = (
            maf.get("axial_meaning")
            or maf.get("binary_field_gloss")
            or ("; ".join(maf.get("letter_meanings", [])) if maf.get("letter_meanings") else None)
            or ""
        )
        mas_gloss = mas.get("short_gloss") or mas.get("definition") or mas.get("meaning_text") or ""
        if len(mas_gloss) > 200:
            mas_gloss = mas_gloss[:200] + "..."

        has_maf = bool(maf_gloss)
        has_mas = bool(mas_gloss)
        if has_maf and has_mas:
            full += 1
            status = "full"
        elif has_maf or has_mas:
            partial += 1
            status = "partial"
        else:
            no_prof += 1
            status = "no_profile"

        entries.append({
            "root": rdata["root_raw"],
            "root_norm": norm_root,
            "binary_root": rdata["binary_root"],
            "skeleton": skel,
            "mafahim_gloss": maf_gloss or None,
            "masadiq_gloss": mas_gloss or None,
            "has_profile": status,
            "word_count": len(rdata["words"]),
        })

    # Write output
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"Total genome roots: {len(entries):,}")
    print(f"  Full (mafahim+masadiq): {full}")
    print(f"  Partial: {partial}")
    print(f"  No profile: {no_prof}")
    print(f"  Unique skeletons: {len(skeletons):,}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
