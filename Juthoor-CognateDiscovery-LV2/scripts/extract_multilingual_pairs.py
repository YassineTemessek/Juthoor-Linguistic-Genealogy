"""
Extract Arabic↔Latin, Arabic↔Greek, Arabic↔French (and other) multilingual pairs
from the beyond_name_etymology_pairs.csv file.

Two extraction strategies:
  A) Explicit words — quoted or flagged foreign words in the etymology_explanation
     (high confidence: 0.75)
  B) English word as terminus — when intermediate_langs lists Latin/Greek/French,
     the English word represents the end of that borrowing chain; we record it as
     an Arabic↔[intermediate language] pair using the English word as proxy lemma
     (confidence: 0.65 — lower because we don't have the actual Latin/Greek form)

Output:
  data/processed/beyond_name_latin_pairs.jsonl
  data/processed/beyond_name_greek_pairs.jsonl
  data/processed/beyond_name_french_pairs.jsonl
  data/processed/beyond_name_other_pairs.jsonl   (Spanish, Italian, German, etc.)

High-confidence pairs (≥0.7) are also appended to:
  data/processed/beyond_name_cognate_gold_candidates.jsonl
"""

import csv
import json
import re
import sys
import io
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ── paths ──────────────────────────────────────────────────────────────────────
BASE = Path("C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy")
LV2 = BASE / "Juthoor-CognateDiscovery-LV2"
PROCESSED = LV2 / "data" / "processed"

CSV_PATH = PROCESSED / "beyond_name_etymology_pairs.csv"
GOLD_PATH = PROCESSED / "beyond_name_cognate_gold_candidates.jsonl"

OUT_PATHS = {
    "lat": PROCESSED / "beyond_name_latin_pairs.jsonl",
    "grc": PROCESSED / "beyond_name_greek_pairs.jsonl",
    "fra": PROCESSED / "beyond_name_french_pairs.jsonl",
    "other": PROCESSED / "beyond_name_other_pairs.jsonl",
}

# ── language mapping ───────────────────────────────────────────────────────────
LANG_CODE = {
    "Latin": "lat",
    "Greek": "grc",
    "French": "fra",
    "Spanish": "spa",
    "Italian": "ita",
    "German": "deu",
    "Old English": "ang",
    "Old Norse": "non",
    "Persian": "fa",
    "Syriac": "syc",
    "PIE": "ine-pro",
}

# Which codes go to which output file
LANG_FILE = {
    "lat": "lat",
    "grc": "grc",
    "fra": "fra",
    "spa": "other",
    "ita": "other",
    "deu": "other",
    "ang": "other",
    "non": "other",
    "fa": "other",
    "syc": "other",
    "ine-pro": "other",
}

# Languages to exclude from the gold benchmark (too distant or speculative)
EXCLUDE_FROM_GOLD = {"ine-pro", "ang", "non"}

# ── explicit extraction patterns ───────────────────────────────────────────────
# These match a language keyword in Arabic + a following/preceding foreign word

EXPLICIT_PATTERNS = [
    # Arabic language name + following foreign word (with optional quotes/spaces)
    (r'اللاتينية\s+(?:القديمة\s+)?["\u201c]?([A-Za-z][A-Za-z\u00c0-\u024f\-]{1,25})["\u201d]?', "lat"),
    (r'["\u201c]([A-Za-z][A-Za-z\u00c0-\u024f\-]{2,25})["\u201d]\s+اللاتينية', "lat"),
    (r'الكلمة اللاتينية\s+([A-Za-z][A-Za-z\u00c0-\u024f\-]{1,25})', "lat"),
    (r'من اللاتينية\s+([a-z][a-z\u00c0-\u024f\-]{2,25})', "lat"),
    (r'من اللاتينية\s*["\u201c]([A-Za-z][A-Za-z\u00c0-\u024f\-]{1,25})["\u201d]', "lat"),

    (r'اليونانية\s+(?:القديمة\s+)?["\u201c]?([A-Za-z][A-Za-z\u00c0-\u024f\u03b1-\u03c9\-]{1,30})["\u201d]?', "grc"),
    (r'["\u201c]([A-Za-z][A-Za-z\u00c0-\u024f\-]{2,30})["\u201d]\s+اليونانية', "grc"),
    (r'الكلمة اليونانية\s+([A-Za-z][A-Za-z\u00c0-\u024f\-]{1,25})', "grc"),
    (r'من اليونانية\s+([a-z][a-z\u00c0-\u024f\-]{2,25})', "grc"),

    (r'الفرنسية\s+(?:القديمة\s+)?["\u201c]?([A-Za-z][A-Za-z\u00c0-\u024f\-]{1,25})["\u201d]?', "fra"),
    (r'["\u201c]([A-Za-z][A-Za-z\u00c0-\u024f\-]{2,25})["\u201d]\s+الفرنسية', "fra"),

    (r'الإسبانية\s+([A-Za-z][A-Za-z\u00c0-\u024f\-]{1,25})', "spa"),
    (r'الإيطالية\s+([A-Za-z][A-Za-z\u00c0-\u024f\-]{1,25})', "ita"),
    (r'الألمانية\s+(?:القديمة\s+)?["\u201c]?([A-Za-z][A-Za-z\u00c0-\u024f\-]{1,25})["\u201d]?', "deu"),
    (r'["\u201c]([A-Za-z][A-Za-z\u00c0-\u024f\-]{2,25})["\u201d]\s+الألمانية', "deu"),
]

# ── quoted word + language context ────────────────────────────────────────────
# Specific rows where quoted words appear next to language keywords in explanation
LANG_PROXIMITY_PATTERNS = [
    # "komētēs" اليونانية  OR  اليونانية "komētēs"
    (r'["\u201c]([A-Za-z][A-Za-z\u00c0-\u024f\u0101\u0113\u012b\-]{2,30})["\u201d]\s{0,10}اليونانية', "grc"),
    (r'اليونانية\s{0,10}["\u201c]([A-Za-z][A-Za-z\u00c0-\u024f\-]{2,25})["\u201d]', "grc"),
    (r'["\u201c]([A-Za-z][A-Za-z\u00c0-\u024f\-]{2,25})["\u201d]\s{0,10}اللاتينية', "lat"),
    (r'اللاتينية\s{0,10}["\u201c]([A-Za-z][A-Za-z\u00c0-\u024f\-]{2,25})["\u201d]', "lat"),
    (r'["\u201c]([A-Za-z][A-Za-z\u00c0-\u024f\-]{2,25})["\u201d]\s{0,10}الفرنسية', "fra"),
    (r'الفرنسية\s{0,10}["\u201c]([A-Za-z][A-Za-z\u00c0-\u024f\-]{2,25})["\u201d]', "fra"),
    (r'["\u201c]([A-Za-z][A-Za-z\u00c0-\u024f\-]{2,25})["\u201d]\s{0,10}الألمانية', "deu"),
    (r'الألمانية\s{0,10}["\u201c]([A-Za-z][A-Za-z\u00c0-\u024f\-]{2,25})["\u201d]', "deu"),
]

# Words that are clearly just English words repeated (not useful as intermediates)
ENGLISH_STOPWORDS = {
    "young goat", "the", "of", "and", "in", "a", "an", "it", "is", "was", "has",
}


def clean_word(w: str) -> str:
    """Strip punctuation and normalize extracted word."""
    return w.strip().rstrip("،.؛;,!؟?").lstrip("-").strip()


def is_useful_foreign_word(w: str, english_word: str) -> bool:
    """Return True if the extracted word is likely a genuine intermediate form."""
    w_lower = w.lower()
    if w_lower in ENGLISH_STOPWORDS:
        return False
    if w_lower == english_word.lower():
        return False  # same as English — not useful
    if len(w) < 2:
        return False
    if not re.search(r"[a-zA-Z]", w):
        return False  # no ASCII letters
    # Reject if it's only digits
    if w.isdigit():
        return False
    return True


def extract_explicit_pairs(row: dict) -> list[dict]:
    """
    Strategy A: Extract explicitly mentioned foreign words from etymology_explanation.
    Returns list of pair dicts.
    """
    expl = row.get("etymology_explanation", "")
    if not expl or len(expl) < 60:
        return []

    arabic_root = row["arabic_root"].strip()
    english_word = row["english_word"].strip()
    arabic_gloss = row.get("arabic_meaning", "") or row.get("english_meaning", "")
    english_gloss = row.get("english_meaning", "") or ""
    confidence_base = float(row.get("confidence", 0.7) or 0.7)
    source_id = row.get("source_post_id", "")
    inter_langs = row.get("intermediate_langs", "")

    found = []
    seen_words = set()

    all_patterns = EXPLICIT_PATTERNS + LANG_PROXIMITY_PATTERNS

    for pat, lang_code in all_patterns:
        for m in re.finditer(pat, expl):
            w = clean_word(m.group(1))
            if not is_useful_foreign_word(w, english_word):
                continue
            key = (lang_code, w.lower())
            if key in seen_words:
                continue
            seen_words.add(key)

            # Confidence: 0.75 if word is explicitly mentioned next to a language name
            conf = min(0.75, confidence_base + 0.05)

            pair = {
                "source": {
                    "lang": "ara",
                    "lemma": arabic_root,
                    "gloss": arabic_gloss,
                },
                "target": {
                    "lang": lang_code,
                    "lemma": w,
                    "gloss": "",
                },
                "relation": "cognate",
                "confidence": conf,
                "notes": (
                    f"Explicit intermediate word extracted from etymology. "
                    f"English: {english_word}. "
                    f"Via: {inter_langs}. "
                    f"Post: {source_id}"
                ),
                "via_english": english_word,
                "extraction_method": "explicit",
            }
            found.append(pair)

    return found


def extract_terminus_pairs(row: dict) -> list[dict]:
    """
    Strategy B: For each language in intermediate_langs, create a pair using the
    English word as proxy lemma (the English word is the descendant of the Latin/
    Greek/French form).
    Returns list of pair dicts.
    """
    inter_langs_str = row.get("intermediate_langs", "")
    if not inter_langs_str:
        return []

    arabic_root = row["arabic_root"].strip()
    english_word = row["english_word"].strip()
    if not arabic_root or not english_word:
        return []

    arabic_gloss = row.get("arabic_meaning", "") or ""
    english_gloss = row.get("english_meaning", "") or ""
    confidence_base = float(row.get("confidence", 0.65) or 0.65)
    source_id = row.get("source_post_id", "")
    entry_type = row.get("entry_type", "single")

    langs = [l.strip() for l in inter_langs_str.split(",") if l.strip()]

    # For terminus pairs, use slightly lower confidence (no explicit form)
    conf = max(0.60, confidence_base - 0.05)

    found = []
    for lang_name in langs:
        lang_code = LANG_CODE.get(lang_name)
        if not lang_code:
            continue
        # Skip very speculative languages for terminus pairs
        if lang_code in {"ine-pro"}:
            continue

        pair = {
            "source": {
                "lang": "ara",
                "lemma": arabic_root,
                "gloss": arabic_gloss,
            },
            "target": {
                "lang": lang_code,
                # English word is used as proxy for the intermediate form
                "lemma": english_word.lower(),
                "gloss": english_gloss,
            },
            "relation": "cognate",
            "confidence": conf,
            "notes": (
                f"English '{english_word}' borrowed via {lang_name}. "
                f"English word used as proxy for intermediate form. "
                f"Post: {source_id}"
            ),
            "via_english": english_word,
            "extraction_method": "terminus",
        }
        found.append(pair)

    return found


def pair_key(pair: dict) -> str:
    return f"{pair['source']['lemma']}|{pair['target']['lang']}|{pair['target']['lemma']}"


def main():
    # Load CSV
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"=== MULTILINGUAL PAIR EXTRACTION ===")
    print(f"Rows scanned: {len(rows)}")
    print()

    # Collect all pairs
    all_pairs: list[dict] = []
    seen_keys: set[str] = set()

    for row in rows:
        # Strategy A: explicit words from explanations (higher confidence)
        explicit = extract_explicit_pairs(row)
        for p in explicit:
            k = pair_key(p)
            if k not in seen_keys:
                seen_keys.add(k)
                all_pairs.append(p)

        # Strategy B: english word as terminus of language chain
        terminus = extract_terminus_pairs(row)
        for p in terminus:
            k = pair_key(p)
            if k not in seen_keys:
                seen_keys.add(k)
                all_pairs.append(p)

    # ── bucket by target language ──────────────────────────────────────────────
    buckets: dict[str, list[dict]] = defaultdict(list)
    for p in all_pairs:
        lang = p["target"]["lang"]
        file_bucket = LANG_FILE.get(lang, "other")
        buckets[file_bucket].append(p)

    # ── write output files ─────────────────────────────────────────────────────
    for file_key, pairs in buckets.items():
        out_path = OUT_PATHS[file_key]
        with open(out_path, "w", encoding="utf-8") as f:
            for p in pairs:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

    # ── append high-confidence to gold candidates ──────────────────────────────
    gold_pairs = [
        p for p in all_pairs
        if p["confidence"] >= 0.70
        and p["target"]["lang"] not in EXCLUDE_FROM_GOLD
    ]

    # Avoid duplicates in gold file — load existing keys
    existing_gold_keys: set[str] = set()
    if GOLD_PATH.exists():
        with open(GOLD_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    src = obj.get("source", {})
                    tgt = obj.get("target", {})
                    k = f"{src.get('lemma','')}|{tgt.get('lang','')}|{tgt.get('lemma','')}"
                    existing_gold_keys.add(k)
                except json.JSONDecodeError:
                    pass

    new_gold = [p for p in gold_pairs if pair_key(p) not in existing_gold_keys]

    with open(GOLD_PATH, "a", encoding="utf-8") as f:
        for p in new_gold:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    # ── counts by language code ────────────────────────────────────────────────
    by_lang: dict[str, int] = defaultdict(int)
    by_method: dict[str, int] = defaultdict(int)
    for p in all_pairs:
        by_lang[p["target"]["lang"]] += 1
        by_method[p["extraction_method"]] += 1

    lang_label = {v: k for k, v in LANG_CODE.items()}

    print(f"Total unique pairs extracted: {len(all_pairs)}")
    print()
    print("By language:")
    for code in sorted(by_lang, key=lambda c: -by_lang[c]):
        label = lang_label.get(code, code)
        print(f"  {label:20s} ({code})  {by_lang[code]:4d}")
    print()
    print(f"By extraction method:")
    print(f"  explicit (quoted word)  : {by_method['explicit']:4d}")
    print(f"  terminus (english proxy): {by_method['terminus']:4d}")
    print()
    print(f"High-confidence pairs (≥0.70) added to gold: {len(new_gold)}")
    print()

    # ── sample pairs ──────────────────────────────────────────────────────────
    for lang_name, lang_code in [("Latin", "lat"), ("Greek", "grc"), ("French", "fra")]:
        lang_pairs = [p for p in all_pairs if p["target"]["lang"] == lang_code]
        explicit_sample = [p for p in lang_pairs if p["extraction_method"] == "explicit"]
        print(f"Sample {lang_name} pairs (explicit):")
        if explicit_sample:
            for p in explicit_sample[:6]:
                src = p["source"]["lemma"]
                tgt = p["target"]["lemma"]
                eng = p.get("via_english", "")
                print(f"  {src} → {tgt}  (via English: {eng})")
        else:
            sample = lang_pairs[:6]
            for p in sample:
                src = p["source"]["lemma"]
                tgt = p["target"]["lemma"]
                print(f"  {src} → {tgt}  (terminus proxy)")
        print()

    print("Output files written:")
    for key, path in OUT_PATHS.items():
        count = len(buckets.get(key, []))
        print(f"  {path.name}: {count} pairs")
    print(f"  {GOLD_PATH.name}: +{len(new_gold)} pairs appended")


if __name__ == "__main__":
    main()
