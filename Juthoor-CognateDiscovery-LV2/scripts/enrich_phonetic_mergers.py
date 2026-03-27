"""
Enrich phonetic_mergers.jsonl with mined merger rules from phonetic_law_weights.json.

Generates new English merger rules for Arabic letter pairs that are NOT already covered,
based on the 5 major merger groups identified from 861 analyzed pairs.
"""

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

MERGERS_PATH = BASE / "resources" / "phonetic_mergers.jsonl"
WEIGHTS_PATH = BASE / "data" / "processed" / "phonetic_law_weights.json"


def load_existing_rules():
    rules = []
    with open(MERGERS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rules.append(json.loads(line))
    return rules


def existing_eng_pairs(rules):
    """Return a set of frozensets of arabic_pair for English rules."""
    covered = set()
    for r in rules:
        if r.get("target_lang") == "eng":
            pair = r.get("arabic_pair", [])
            covered.add(frozenset(pair))
    return covered


def generate_new_rules(covered):
    """
    Generate new English merger rules for pairs not already covered.
    Based on the 5 merger groups mined from 861 pairs.
    """
    new_rules = []

    # ---------------------------------------------------------------------------
    # Group 1: guttural_collapse  (ع ح خ غ → h/∅/k/g)
    # frequency: 171/193, weight: 0.886
    # observed: O=129, h=25, g=15, k=2
    # Pairs NOT yet covered as a joint merger rule
    # ---------------------------------------------------------------------------
    guttural_pairs = [
        {
            "arabic_pair": ["ع", "ح"],
            "merged_to": "h",
            "notes": (
                "Guttural collapse (mined, 861 pairs): pharyngeal ayin (ع) and "
                "pharyngeal fricative ha (ح) both yield h or deletion in English. "
                "Group frequency 171/193 (weight 0.886); dominant reflex is deletion "
                "(129 obs), h-retention secondary (25 obs)."
            ),
        },
        {
            "arabic_pair": ["ع", "خ"],
            "merged_to": None,
            "notes": (
                "Guttural collapse (mined): pharyngeal ayin (ع) and velar kha (خ) "
                "both lose their guttural quality in English; ع → ∅/V, خ → h/k/∅. "
                "Part of the 4-letter guttural group (weight 0.886, 193 obs)."
            ),
        },
        {
            "arabic_pair": ["ح", "خ"],
            "merged_to": "h",
            "notes": (
                "Guttural collapse (mined): pharyngeal ha (ح) and velar kha (خ) both "
                "map to English h or are dropped. Group weight 0.886 (171/193 obs). "
                "Extends existing Latin/Greek rules to English with mined frequency support."
            ),
        },
        {
            "arabic_pair": ["ح", "غ"],
            "merged_to": None,
            "notes": (
                "Guttural collapse (mined): pharyngeal ha (ح) → h/∅ and ghayin (غ) "
                "→ ∅/g in English; both gutturals collapse with deletion as dominant "
                "reflex (129/193 obs). Part of 4-letter guttural group, weight 0.886."
            ),
        },
        {
            "arabic_pair": ["خ", "غ"],
            "merged_to": None,
            "notes": (
                "Guttural collapse (mined): velar kha (خ) and velar ghayin (غ) both "
                "reduce in English; kha → h/k/∅, ghayin → ∅/g. Part of 4-letter "
                "guttural group, weight 0.886 (171/193 obs)."
            ),
        },
    ]

    # ---------------------------------------------------------------------------
    # Group 2: emphatic_dental_collapse  (ط ت ذ ظ → t/d)
    # frequency: 132/175, weight: 0.754
    # observed: t=102, O=19, d=11
    # ---------------------------------------------------------------------------
    dental_pairs = [
        {
            "arabic_pair": ["ط", "ت"],
            "merged_to": "t",
            "notes": (
                "Emphatic dental collapse (mined, 861 pairs): emphatic ṭa (ط) and "
                "plain ta (ت) both map to English t; emphatic pharyngealization "
                "entirely lost. t dominant (102/175 obs), weight 0.754."
            ),
        },
        {
            "arabic_pair": ["ط", "ذ"],
            "merged_to": "t",
            "notes": (
                "Emphatic dental collapse (mined): emphatic ṭa (ط) → t and voiced "
                "interdental dhal (ذ) → d/th in English; both lose emphatic/fricative "
                "quality. Weight 0.754 (132/175 obs). Dominant reflex: t."
            ),
        },
        {
            "arabic_pair": ["ط", "ظ"],
            "merged_to": "t",
            "notes": (
                "Emphatic dental collapse (mined): both emphatic ṭa (ط) and emphatic "
                "dha (ظ) map to t/d in English with total loss of pharyngealization. "
                "Part of 4-letter dental group, weight 0.754."
            ),
        },
        {
            "arabic_pair": ["ت", "ذ"],
            "merged_to": "t",
            "notes": (
                "Emphatic dental collapse (mined): plain ta (ت) → t and voiced "
                "interdental dhal (ذ) → d/th merge to the t/d region in English. "
                "Weight 0.754 (132/175 obs)."
            ),
        },
        {
            "arabic_pair": ["ت", "ظ"],
            "merged_to": "t",
            "notes": (
                "Emphatic dental collapse (mined): plain ta (ت) and emphatic dha (ظ) "
                "both collapse to t in English. Part of 4-letter dental merger, "
                "weight 0.754."
            ),
        },
        {
            "arabic_pair": ["ذ", "ظ"],
            "merged_to": None,
            "notes": (
                "Emphatic dental collapse (mined): voiced interdental dhal (ذ) and "
                "emphatic dha (ظ) both reduce to d/z in English with loss of fricative "
                "and emphatic features. Part of 4-letter dental merger, weight 0.754."
            ),
        },
    ]

    # ---------------------------------------------------------------------------
    # Group 3: velar_uvular_merge  (ق ك ج → k/c/g/j)
    # frequency: 221/304, weight: 0.727
    # observed: c=93, g=65, O=39, k=17, j=7
    # ق+ك and ق+ج partially covered; ك+ج not covered
    # ---------------------------------------------------------------------------
    velar_pairs = [
        {
            "arabic_pair": ["ق", "ك"],
            "merged_to": "k",
            "notes": (
                "Velar/uvular merger (mined, 861 pairs): uvular qaf (ق) and velar kaf "
                "(ك) both map to English k/c; the uvular-velar distinction is entirely "
                "lost. c dominant (93 obs), g secondary (65), k tertiary (17). "
                "Group weight 0.727 (221/304 obs)."
            ),
        },
        {
            "arabic_pair": ["ك", "ج"],
            "merged_to": "k",
            "notes": (
                "Velar/uvular merger (mined): velar kaf (ك) and palatal jim (ج) both "
                "fall in the k/c/g region in English. Jim → g/j, kaf → k/c; the "
                "palatal-velar distinction collapses. Part of 3-letter velar merger, "
                "weight 0.727."
            ),
        },
    ]

    # ---------------------------------------------------------------------------
    # Group 4: emphatic_sibilant_collapse  (ص س ز ش → s/z/c)
    # frequency: 183/259, weight: 0.707
    # observed: s=129, O=23, c=20, z=11
    # ص+س partially covered; new pairs: ص+ز, ص+ش, س+ز, س+ش, ز+ش
    # ---------------------------------------------------------------------------
    sibilant_pairs = [
        {
            "arabic_pair": ["ص", "س"],
            "merged_to": "s",
            "notes": (
                "Emphatic sibilant collapse (mined, 861 pairs): emphatic sad (ص) and "
                "plain sin (س) both map to English s; emphatic pharyngealization lost. "
                "s dominant (129/259 obs), weight 0.707. Extends existing entry with "
                "mined frequency data."
            ),
        },
        {
            "arabic_pair": ["ص", "ز"],
            "merged_to": "s",
            "notes": (
                "Emphatic sibilant collapse (mined): emphatic sad (ص) → s/c and zayin "
                "(ز) → z/s in English; both collapse to the s/z region. Group weight "
                "0.707 (183/259 obs)."
            ),
        },
        {
            "arabic_pair": ["ص", "ش"],
            "merged_to": "s",
            "notes": (
                "Emphatic sibilant collapse (mined): emphatic sad (ص) and shin (ش) "
                "both reduce to s/c in English with loss of emphatic and palatal "
                "features. Part of 4-letter sibilant group, weight 0.707."
            ),
        },
        {
            "arabic_pair": ["س", "ز"],
            "merged_to": "s",
            "notes": (
                "Emphatic sibilant collapse (mined): plain sin (س) and zayin (ز) both "
                "map to s/z in English; the voicing distinction is often neutralized. "
                "Part of 4-letter sibilant group, weight 0.707 (183/259 obs)."
            ),
        },
        {
            "arabic_pair": ["س", "ش"],
            "merged_to": "s",
            "notes": (
                "Emphatic sibilant collapse (mined): plain sin (س) and shin (ش) both "
                "reduce to s in English; the palatal feature of shin is lost. Part of "
                "4-letter sibilant group, weight 0.707."
            ),
        },
        {
            "arabic_pair": ["ز", "ش"],
            "merged_to": "s",
            "notes": (
                "Emphatic sibilant collapse (mined): zayin (ز) → z/s and shin (ش) → "
                "s/sh in English; both fall in the sibilant region. Part of 4-letter "
                "sibilant group, weight 0.707 (183/259 obs)."
            ),
        },
    ]

    # ---------------------------------------------------------------------------
    # Group 5: labial_group  (ب ف م و → b/f/p/m/v/w)
    # frequency: 386/595, weight: 0.649
    # observed: m=98, p=71, b=64, O=63, f=48, v=29, w=13
    # ب+ف partially covered; new cross-pairs: ب+م, ب+و, ف+م, ف+و, م+و
    # ---------------------------------------------------------------------------
    labial_pairs = [
        {
            "arabic_pair": ["ب", "م"],
            "merged_to": None,
            "notes": (
                "Labial group merger (mined, 861 pairs): ba (ب) and mim (م) both fall "
                "in the labial region in English; ba → b/f/p, mim → m/n. The labial "
                "stop and nasal are related via bilabial place of articulation. Group "
                "weight 0.649 (386/595 obs)."
            ),
        },
        {
            "arabic_pair": ["ب", "و"],
            "merged_to": None,
            "notes": (
                "Labial group merger (mined): ba (ب) and waw (و) both occupy the "
                "bilabial/labiodental zone; ba → b/p/f, waw → v/w/b in English. Part "
                "of 4-letter labial group, weight 0.649."
            ),
        },
        {
            "arabic_pair": ["ف", "م"],
            "merged_to": "f",
            "notes": (
                "Labial group merger (mined): fa (ف) and mim (م) both map to English "
                "labials; fa → f/p/b, mim → m. Bilabial–labiodental alternation in "
                "labial group, weight 0.649 (386/595 obs)."
            ),
        },
        {
            "arabic_pair": ["ف", "و"],
            "merged_to": "f",
            "notes": (
                "Labial group merger (mined): fa (ف) → f/p and waw (و) → v/w/f in "
                "English; the labial fricatives interchange. Part of 4-letter labial "
                "group, weight 0.649."
            ),
        },
        {
            "arabic_pair": ["م", "و"],
            "merged_to": None,
            "notes": (
                "Labial group merger (mined): mim (م) and waw (و) both occupy the "
                "bilabial region; mim → m, waw → v/w. The nasal-approximant alternation "
                "is attested in labial weakening environments. Part of 4-letter labial "
                "group, weight 0.649 (386/595 obs)."
            ),
        },
    ]

    # Collect all candidate rules
    candidate_groups = [
        guttural_pairs,
        dental_pairs,
        velar_pairs,
        sibilant_pairs,
        labial_pairs,
    ]

    for group in candidate_groups:
        for rule in group:
            pair_set = frozenset(rule["arabic_pair"])
            if pair_set not in covered:
                new_rules.append(
                    {
                        "target_lang": "eng",
                        "arabic_pair": rule["arabic_pair"],
                        "merged_to": rule["merged_to"],
                        "notes": rule["notes"],
                    }
                )
                covered.add(pair_set)  # prevent within-batch duplicates

    return new_rules


def main():
    print(f"Reading existing rules from: {MERGERS_PATH}")
    existing = load_existing_rules()
    covered = existing_eng_pairs(existing)

    print(f"Total existing rules: {len(existing)}")
    eng_existing = [r for r in existing if r.get("target_lang") == "eng"]
    print(f"Existing English rules: {len(eng_existing)}")
    print(f"Existing English pair-sets covered: {len(covered)}")

    new_rules = generate_new_rules(covered)
    print(f"New rules to append: {len(new_rules)}")

    if not new_rules:
        print("No new rules to add. File unchanged.")
        return

    # Append new rules preserving existing content exactly
    with open(MERGERS_PATH, "a", encoding="utf-8") as f:
        for rule in new_rules:
            f.write(json.dumps(rule, ensure_ascii=False) + "\n")

    print(f"Appended {len(new_rules)} rules.")

    # Verify
    all_rules = load_existing_rules()
    all_eng = [r for r in all_rules if r.get("target_lang") == "eng"]
    print(f"\nVerification:")
    print(f"  Total rules: {len(all_rules)}, English rules: {len(all_eng)}")


if __name__ == "__main__":
    main()
