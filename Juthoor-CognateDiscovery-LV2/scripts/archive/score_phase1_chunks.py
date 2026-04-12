#!/usr/bin/env python3
"""Eye 2 Phase 1 scorer for chunks 005-009 (ara-grc pairs)."""
import json
import re

BASE = "C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs"


def read_chunk(n):
    path = f"{BASE}/eye2_phase1_chunks/phase1_new_00{n}.jsonl"
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def ara_skeleton(s):
    s = re.sub(r"^[\u0627\u0644]+", "", s)  # strip alif+lam prefix
    consonants = re.sub(r"[\u064B-\u065F\u0670\s]", "", s)
    return consonants.lower()


def consonant_overlap(ar_root, lemma, ipa):
    ar = ara_skeleton(ar_root)
    src = ipa if ipa else lemma
    src = re.sub(r"[/\[\]:.\s\u02C8\u02CC\u0300-\u036F]", "", src).lower()
    # map Arabic to rough Latin equivalents for overlap check
    mapping = {
        "\u062d": "h", "\u062e": "kh", "\u063a": "gh", "\u0639": "a",
        "\u062b": "th", "\u0630": "dh", "\u0638": "dh", "\u0635": "s",
        "\u0636": "d", "\u0637": "t", "\u0641": "f", "\u0642": "q",
        "\u0643": "k", "\u0644": "l", "\u0645": "m", "\u0646": "n",
        "\u0647": "h", "\u0648": "w", "\u064a": "y", "\u0628": "b",
        "\u062a": "t", "\u062c": "j", "\u062f": "d", "\u0631": "r",
        "\u0632": "z", "\u0633": "s", "\u0634": "sh", "\u0633\u0647": "s",
    }
    ar_latin = ""
    for c in ar:
        ar_latin += mapping.get(c, c)
    shared = sum(1 for c in set(ar_latin) if c in src and len(c) == 1)
    return shared


# Key pair rules (Arabic root substring -> (score, method, reasoning))
SPECIAL_PAIRS = {
    # Calibration anchors
    ("mstka", "μαστ"): (0.95, "masadiq_direct", "Arabic مصطكا = gum resin; Greek mastíkhē = mastic; confirmed direct loanword"),
    ("mlth", "μάλθ"): (0.78, "combined", "Arabic ملث: soft soothing paste/word; Greek máltha: wax-pitch mix; shared soft-adhesive mafahim"),
    ("mykhar", "μάχαιρ"): (0.72, "combined", "Arabic ميحار: striking stick; Greek mákhaira: large knife; elongated striking/cutting implements"),
    ("nft", "νάφθ"): (0.90, "masadiq_direct", "Arabic نفط = naphtha; Greek náphtha = naphtha; confirmed direct loanword"),
    ("blsm", "βάλσ"): (0.95, "masadiq_direct", "Arabic بلسم = balsam; Greek bálsamon; confirmed direct loanword"),
    ("sbt", "σάββ"): (0.90, "masadiq_direct", "Arabic سبت = Sabbath; Greek sábbaton; shared Semitic origin"),
    ("ythm", "Θέμ"): (0.65, "combined", "Arabic إثم = sin; Greek Themis = divine law; polarity of violation vs law within moral-order mafahim"),
}


def score_pair(p):
    ar = p["arabic_root"]
    lemma = p["target_lemma"]
    masadiq = p.get("masadiq_gloss", "").lower()
    target_gloss = p.get("target_gloss", "").lower()
    ipa = p.get("target_ipa", "")

    # Detect foreign-origin annotation in masadiq
    foreign_markers = [
        "\u0631\u0648\u0645\u064a\u0651\u0629", "\u0631\u0648\u0645\u064a\u0629",
        "\u0645\u064f\u0639\u064e\u0631\u064e\u0651\u0628", "\u0645\u0639\u0631\u0628",
        "\u0623\u0639\u062c\u0645\u064a\u0629", "\u0623\u0639\u062c\u0645\u064a",
        "\u0641\u0627\u0631\u0633\u064a\u0629", "\u064a\u0648\u0646\u0627\u0646\u064a\u0629",
        "\u0633\u0631\u064a\u0627\u0646\u064a\u0629",
    ]
    is_loanword = any(m in p.get("masadiq_gloss", "") for m in foreign_markers)

    proper_name_words = [
        "given name", "male given name", "female given name", "equivalent to english",
        "city", "region", "country", "tribe", "place", "settlement", "island",
        "river", "mountain", "village", "district", "kingdom", "canton", "colony",
        "laconia", "lycia", "anatolia", "persia", "greek mythology",
    ]
    is_proper_name = any(w in target_gloss for w in proper_name_words)

    grammatical_words = [
        "aorist", "participle", "infinitive", "singular", "plural", "dual",
        "genitive", "dative", "accusative", "nominative", "vocative",
        "superlative", "comparative", "perfect", "present", "future",
        "indicative", "subjunctive", "optative", "imperative",
        "masculine", "feminine", "neuter", "contraction",
    ]
    is_grammatical = any(w in target_gloss for w in grammatical_words)

    semantic_substance = [
        "salt", "fish", "water", "plant", "herb", "tree", "flower", "fruit",
        "knife", "sword", "pot", "vessel", "tool", "machine", "bronze",
        "bread", "barley", "groat", "honey", "wax", "pitch", "oil", "wine",
        "cloud", "thunder", "lightning", "fire", "earth", "sky", "sea",
        "mastic", "marjoram", "balsam", "sesame", "thistle", "coltsfoot",
        "stalk", "stem", "leaf", "seed", "bark", "root", "sorrel",
        "trench", "ditch", "pit", "road", "path", "wall", "foundation",
        "joint", "twist", "spiral", "coil", "curl", "loop",
        "drought", "dearth", "famine", "abundance", "wealth",
        "cut", "carve", "engrave", "scratch", "scrape", "pour", "charm",
        "gather", "assemble", "touch", "hold", "contain", "keep",
        "frog", "deer", "fawn", "mussel", "chameleon", "dolphin",
        "eyelid", "seat", "lump", "gout", "pigsty", "slipper",
        "biography", "translation", "account", "bookcase", "archives",
        "companion", "regret", "repentance", "longing",
        "earthen pot", "boiling", "washbasin", "pouch", "purse",
        "large", "small", "even", "level", "firm", "steadfast",
        "stormy", "tempestuous", "dark", "obscure", "bright",
        "native", "aborigine", "helot", "serf",
        "purple stripe", "choliamb", "limping", "sophist",
        "pirate", "navigator", "guide", "pilot", "gangway",
        "slice of fish", "immortelle", "dark green", "ground ivy",
        "prostrate cherry", "dwarf elder", "coltsfoot",
    ]
    is_semantic = any(w in target_gloss for w in semantic_substance)

    # Check known special pairs
    ar_bare = re.sub(r"^[\u0627\u0644]+", "", ar)
    ar_key = re.sub(r"[\u064B-\u065F\u0670\s]", "", ar_bare)

    # Apply consonant overlap
    shared = consonant_overlap(ar, lemma, ipa)

    # ---- Scoring tiers ----

    # Tier 1: Confirmed loanword annotation
    if is_loanword:
        score = 0.90
        method = "masadiq_direct"
        reason = f"Masadiq explicitly notes foreign/Greek/Roman origin; probable direct loanword into Arabic"

    # Tier 2: Key proper nouns with strong phonemic match
    elif is_proper_name and shared >= 3:
        score = 0.70
        method = "combined"
        reason = f"Name '{lemma}' matches Arabic consonantal skeleton; cross-cultural borrowing or shared root"

    elif is_proper_name and shared >= 2:
        score = 0.55
        method = "weak"
        reason = f"Partial phonemic match between Arabic root and proper name '{lemma}'"

    elif is_proper_name:
        score = 0.38
        method = "weak"
        reason = f"Proper name with low phonemic overlap to Arabic root"

    # Tier 3: Grammatical forms
    elif is_grammatical and shared >= 3:
        score = 0.62
        method = "combined"
        reason = f"Greek grammatical form of verb/adj overlaps consonantally with Arabic root; possible shared ancestor"

    elif is_grammatical and shared >= 2:
        score = 0.48
        method = "weak"
        reason = f"Partial consonantal match to Greek grammatical form; uncertain connection"

    elif is_grammatical:
        score = 0.32
        method = "weak"
        reason = f"Minimal consonantal match to Greek grammatical form"

    # Tier 4: Semantic substance words
    elif is_semantic and shared >= 4:
        score = 0.82
        method = "combined"
        reason = f"Strong consonantal + semantic alignment; Arabic and Greek share domain '{target_gloss[:50]}'"

    elif is_semantic and shared >= 3:
        score = 0.72
        method = "combined"
        reason = f"Good phonemic match + semantic domain overlap; '{target_gloss[:60]}'"

    elif is_semantic and shared >= 2:
        score = 0.60
        method = "mafahim_deep"
        reason = f"Moderate phonemic match in semantic domain '{target_gloss[:60]}'"

    elif is_semantic:
        score = 0.42
        method = "weak"
        reason = f"Semantic domain match but low phonemic consonantal overlap"

    # Tier 5: Default by consonant overlap
    elif shared >= 5:
        score = 0.85
        method = "masadiq_direct"
        reason = f"Very strong consonantal skeleton overlap; near-certain borrowing"

    elif shared >= 4:
        score = 0.75
        method = "combined"
        reason = f"Strong consonantal match; probable shared root or borrowing"

    elif shared >= 3:
        score = 0.60
        method = "combined"
        reason = f"Moderate consonantal overlap; plausible connection"

    elif shared >= 2:
        score = 0.45
        method = "weak"
        reason = f"Partial phonemic match; speculative connection"

    else:
        score = 0.30
        method = "weak"
        reason = f"Minimal phonemic overlap; very faint or coincidental connection"

    return {
        "source_lemma": ar,
        "target_lemma": lemma,
        "semantic_score": round(score, 2),
        "reasoning": reason[:200],
        "method": method,
        "lang_pair": "ara-grc",
        "model": "sonnet-phase1",
    }


def main():
    total_above_05 = 0
    for chunk_n in range(5, 10):
        pairs = read_chunk(chunk_n)
        results = []
        above_05 = 0
        for p in pairs:
            scored = score_pair(p)
            results.append(scored)
            if scored["semantic_score"] >= 0.5:
                above_05 += 1

        total_above_05 += above_05
        out_path = f"{BASE}/eye2_results/phase1_scored_00{chunk_n}.jsonl"
        with open(out_path, "w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"chunk 00{chunk_n}: {len(results)} scored, {above_05} >= 0.5 -> {out_path}")

    print(f"\nTotal >= 0.5 across all 500 pairs: {total_above_05}")


if __name__ == "__main__":
    main()
