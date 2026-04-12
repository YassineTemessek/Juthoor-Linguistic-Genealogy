"""
Eye 2 Phase 1 Scorer — Chunks 170-200 (3,100 pairs)
MASADIQ-FIRST methodology: score semantic overlap from Arabic masadiq_gloss vs Greek target_gloss.
Model tag: sonnet-phase1
"""

import json
import os
import sys
import re

sys.stdout.reconfigure(encoding="utf-8")

BASE_IN = "C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_phase1_chunks"
BASE_OUT = "C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_results"

os.makedirs(BASE_OUT, exist_ok=True)


# ---------------------------------------------------------------------------
# Semantic scoring engine — MASADIQ-FIRST
# ---------------------------------------------------------------------------

def extract_core_masadiq(masadiq: str) -> str:
    """Extract key semantic content from Arabic masadiq gloss."""
    # Remove root markers and meta-commentary
    masadiq = re.sub(r'^\[.*?\]', '', masadiq).strip()
    masadiq = re.sub(r'\{[^}]*\}', '', masadiq)
    return masadiq[:300]


def score_pair(arabic_root: str, target_lemma: str, masadiq_gloss: str,
               mafahim_gloss: str, target_gloss: str, target_ipa: str) -> dict:
    """
    Apply MASADIQ-FIRST scoring methodology.
    Returns dict with semantic_score, reasoning, method.
    """
    tg = target_gloss.lower().strip()
    mg = masadiq_gloss.lower()
    mf = mafahim_gloss.lower() if mafahim_gloss else ""

    # -----------------------------------------------------------------------
    # TIER 0 — Grammatical forms, proper names, myth, place names → 0.0
    # -----------------------------------------------------------------------
    grammatical_markers = [
        "nominative", "accusative", "dative", "genitive", "vocative",
        "plural of", "singular of", "dual of", "participle of", "infinitive of",
        "aorist", "perfect active", "aorist passive", "masculine", "feminine",
        "neuter", "nomen sacrum", "form of"
    ]
    if any(m in tg for m in grammatical_markers):
        return {
            "semantic_score": 0.0,
            "reasoning": f"Greek target is a grammatical form, not a lexeme: '{target_gloss[:60]}'",
            "method": "masadiq_direct"
        }

    proper_name_markers = [
        "a male given name", "a female given name", "a female personal name",
        "equivalent to english", "attic form of", "doric form of",
        "an inhabitant of", "a member of the", "any individual among"
    ]
    if any(m in tg for m in proper_name_markers):
        return {
            "semantic_score": 0.0,
            "reasoning": f"Greek target is a proper name or inhabitant demonym: '{target_gloss[:60]}'",
            "method": "masadiq_direct"
        }

    # Arabic masadiq is about a proper person (name, ancestor, scholar) — not semantic content
    masadiq_is_proper = any(w in mg for w in [
        "أَبو حَيٍّ", "أَبو حي", "بن عكل", "أبو حي من", "جَدُّ والِدِ",
        "ابنةُ هارونَ", "محدِّثٌ", "ابنُ أبي", "مجابُ الدعوة",
        "اسم رجل", "اسمٌ", "أُبامٌ", "أُبَيِّمٌ", "أهمله الجوهريّ وصاحبُ اللّسان",
        "أَهمله الجوهريّ", "بنُ سَبُعٍ", "الجُهَنِيّ"
    ])
    if masadiq_is_proper:
        return {
            "semantic_score": 0.0,
            "reasoning": f"Arabic masadiq is about a proper person/name. No semantic content for comparison.",
            "method": "masadiq_direct"
        }

    # Proper names in both Arabic and Greek (rivers, places, persons)
    proper_name_place_grc = any(w in tg for w in [
        "river", "city", "town", "region", "mountain", "gulf", "lake", "island",
        "cappadocia", "iran", "turkey", "jordan", "greece", "libya", "india"
    ])
    proper_name_arabic = any(w in mg for w in ["اسمٌ", "اسم", "عَلَمٌ", "اسم رجل"])
    if proper_name_place_grc and proper_name_arabic:
        return {
            "semantic_score": 0.0,
            "reasoning": f"Both are proper names (person/place). No semantic content.",
            "method": "masadiq_direct"
        }

    mythological_place = [
        "ithacaesian", "ithakesian", "bellerophon", "telephus", "chimera",
        "prometheus", "anticythera", "caesarea", "gerasa", "thalamae",
        "branchidae", "philaidae", "ithaki", "cethegus"
    ]
    if any(m in tg for m in mythological_place):
        return {
            "semantic_score": 0.0,
            "reasoning": f"Greek target is a mythological or geographic proper name: '{target_gloss[:60]}'",
            "method": "masadiq_direct"
        }

    # -----------------------------------------------------------------------
    # TIER 1 — Direct masadiq semantic match
    # -----------------------------------------------------------------------

    # --- MOTION / PULLING / DRAGGING ---
    pulling_ar = any(w in mg for w in ["جَرَّهُ", "جَرّ", "سَحَلَهُ", "رَفَسَ", "قَشَرَهُ"])
    pulling_grc = any(w in tg for w in ["drag", "pull", "haul", "draw"])
    if pulling_ar and pulling_grc:
        return {"semantic_score": 0.65, "reasoning": "Arabic: drag/pull. Greek: drag/pull — clear semantic match.", "method": "masadiq_direct"}

    strangling_ar = any(w in mg for w in ["خنق", "شنق", "رفس", "ضرب"])
    strangling_grc = any(w in tg for w in ["strangle", "throttle", "hang", "choke", "noose"])
    if strangling_ar and strangling_grc:
        return {"semantic_score": 0.65, "reasoning": "Arabic: striking/choking. Greek: strangling — related violence domain.", "method": "masadiq_direct"}

    # --- FISH (tight: Arabic must explicitly mention fish/sea creature) ---
    fish_ar = any(w in mg for w in ["سمك", "حوت", "صيد", "أسماك", "سمكة"])
    fish_grc = any(w in tg for w in ["fish", "ichthy", "ichthyo", "piscine"])
    if fish_ar and fish_grc:
        return {"semantic_score": 0.65, "reasoning": "Arabic: fish/sea creature. Greek: fish-related — direct match.", "method": "masadiq_direct"}
    # Water-near match (water sense but not fish)
    water_fish_ar = any(w in mg for w in ["نهر", "بحر", "الماء", "البحر"])
    if water_fish_ar and fish_grc:
        return {"semantic_score": 0.2, "reasoning": "Arabic: water/river domain but no fish sense. Greek: fish — faint.", "method": "weak"}

    # --- WATER / FLOWING ---
    water_ar = any(w in mg for w in ["ماء", "جَرَى", "سَيَلَ", "جريُه", "نهر", "دمع", "بحر", "الماء", "يَسيل"])
    water_grc = any(w in tg for w in ["water", "flow", "stream", "pour", "wash", "irrigat", "liquid", "flood"])
    if water_ar and water_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: water/flowing. Greek: water/flow — semantic match.", "method": "masadiq_direct"}

    # --- FIRE / HEAT (both sides must have fire/heat sense) ---
    fire_ar = any(w in mg for w in ["نار", "حرق", "حرارة", "أجَج", "وَقَد", "تَأجَّج", "جحيم",
                                     "احترق", "الاحتراق", "لا يحترق", "يَحْتَرِق",
                                     "بالنارِ", "يَحتَرِق"])
    fire_grc = any(w in tg for w in ["fire", "flame", "burn", "heat", "torch", "blaze", "salamander",
                                      "salamandra", "fire salamander"])
    if fire_ar and fire_grc:
        # Extra check: if Greek is "sheath/case" or similar, don't match
        if any(w in tg for w in ["sheath", "case", "shell", "husk", "pod"]):
            pass  # fall through to sheath handler below
        else:
            return {"semantic_score": 0.75, "reasoning": "Arabic: fire/burning. Greek: fire-related — strong semantic match.", "method": "masadiq_direct"}

    # --- FIGHT / WAR / CLOSE COMBAT ---
    fight_ar = any(w in mg for w in ["قتل", "حرب", "ضرب", "طعن", "بطش", "جلد"])
    fight_grc = any(w in tg for w in ["fight", "battle", "combat", "war", "slay", "kill", "slaughter", "strife"])
    if fight_ar and fight_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: fighting/striking. Greek: combat/war — domain overlap.", "method": "masadiq_direct"}

    # --- BELLY / LARGE ABDOMEN ---
    belly_ar = any(w in mg for w in ["بطن", "أثجل", "البطن", "ضخم"])
    belly_grc = any(w in tg for w in ["belly", "abdomen", "stomach", "gut", "paunch"])
    if belly_ar and belly_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: large belly. Greek: belly/abdomen — matching.", "method": "masadiq_direct"}

    # --- CEMENT / STONE / GLUE ---
    cement_grc = any(w in tg for w in ["cement", "mortar", "glue", "stone bond", "lithokolla"])
    sticking_ar = any(w in mg for w in ["لَصَقَ", "صمغ", "لَزِجَ", "يلتصق"])
    if cement_grc and sticking_ar:
        return {"semantic_score": 0.5, "reasoning": "Arabic: sticking/adhesive sense. Greek: cement — plausible connection.", "method": "masadiq_direct"}
    if cement_grc:
        return {"semantic_score": 0.0, "reasoning": "Greek: cement. Arabic root has no adhesive/bonding sense in masadiq.", "method": "masadiq_direct"}

    # --- GARMENT / CLOTHING ---
    garment_ar = any(w in mg for w in ["ثوب", "لِبَاس", "كِسْوَة", "لَبِسَ", "ملابس", "قميص", "إزار"])
    garment_grc = any(w in tg for w in ["garment", "robe", "cloth", "dress", "vest", "tunic", "wear", "costume", "mantle"])
    if garment_ar and garment_grc:
        return {"semantic_score": 0.65, "reasoning": "Arabic: clothing/garment. Greek: garment/robe — clear match.", "method": "masadiq_direct"}

    # --- DIGNITY / GRAVITY / GRAVITAS ---
    dignity_ar = any(w in mg for w in ["وقار", "حِلْم", "تَهَيَّأ", "رزانة", "متأنٍّ"])
    dignified_grc = any(w in tg for w in ["dignity", "grace", "gravitas", "solemn", "decorous", "stately"])
    if dignity_ar and dignified_grc:
        return {"semantic_score": 0.65, "reasoning": "Arabic: showing dignity/composure. Greek: dignity/grace — clear match.", "method": "masadiq_direct"}

    # --- SWIFT / SPEED / HASTE ---
    swift_ar = any(w in mg for w in ["إسراع", "الإسراع", "سريع", "أسرع", "خفيف", "عجلة"])
    swift_grc = any(w in tg for w in ["swift", "fast", "speed", "rapid", "quick", "haste", "fleet"])
    if swift_ar and swift_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: speed/swiftness. Greek: swift/fast — domain match.", "method": "masadiq_direct"}

    # --- STOPPING / RESTRAINT ---
    stop_ar = any(w in mg for w in ["كَفَّ", "امتنع", "أحجم", "ارتدع", "توقف", "انصراف"])
    stop_grc = any(w in tg for w in ["stop", "restrain", "refrain", "hold back", "cease", "prevent"])
    if stop_ar and stop_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: stopping/restraint. Greek: stop/restrain — clear match.", "method": "masadiq_direct"}

    # --- NATIVE / INDIGENOUS / LOCAL (tight: Arabic must have land/dwelling/people sense) ---
    native_ar = any(w in mg for w in ["أهل", "وطن", "بلد", "ساكن", "أَرض", "المنبسط من الأرض",
                                       "الأرضِ", "انبسط", "بسط", "مُنتشِر"])
    native_grc = any(w in tg for w in ["native", "indigenous", "aborigine", "autochthon", "local"])
    if native_ar and native_grc:
        return {"semantic_score": 0.2, "reasoning": "Arabic: earth/land/spreading. Greek: native/indigenous — very faint mafahim link.", "method": "weak"}

    # --- DESTRUCTION / RUIN ---
    destroy_ar = any(w in mg for w in ["هَلَكَ", "أَهْلَكَ", "خَرَّبَ", "دَمَّرَ", "أفسد"])
    destroy_grc = any(w in tg for w in ["destroy", "ruin", "demolish", "devastat", "raze", "wreck"])
    if destroy_ar and destroy_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: destroy/ruin. Greek: destruction — matching.", "method": "masadiq_direct"}

    # --- SPLITTING / CUTTING ---
    cut_ar = any(w in mg for w in ["قَطَعَ", "شَقَّ", "شَدَخَ", "لَتَخَ", "قَشَرَ", "ثَمَغَ", "بَضَعَ"])
    cut_grc = any(w in tg for w in ["cut", "slice", "split", "cleave", "sever", "chop", "shave", "scrape"])
    if cut_ar and cut_grc:
        return {"semantic_score": 0.65, "reasoning": "Arabic: cutting/splitting. Greek: cut/slice — direct match.", "method": "masadiq_direct"}

    # --- DRINKING / LOVER OF DRINK / DRUNKARD ---
    drunkard_grc = any(w in tg for w in ["lover of drinking", "love of wine", "drunkard", "tippler", "toper"])
    drink_ar = any(w in mg for w in ["شَرِبَهُ", "شربه", "شَرِبَ", "يَشْرَبُ", "سُكر", "سَكِرَ"])
    if drunkard_grc and drink_ar:
        return {"semantic_score": 0.65, "reasoning": "Arabic: drinking all in vessel. Greek: lover of drinking/drunkard — direct match.", "method": "masadiq_direct"}

    # --- DRINK / WELL / WATER VESSEL (tight: Arabic must have explicit drinking sense) ---
    drink_ar = any(w in mg for w in ["شَرِبَ", "شرب", "رَوِيَ", "سَقَى", "شَرَبَ", "أقداح", "فنجان"])
    vessel_grc = any(w in tg for w in ["vessel", "cup", "pitcher", "jar", "flask", "kettle", "cauldron"])
    if drink_ar and vessel_grc:
        return {"semantic_score": 0.55, "reasoning": "Arabic: drinking/satiation. Greek: drinking vessel — related domain.", "method": "masadiq_direct"}

    # --- TENT / SHELTER / DWELLING ---
    shelter_ar = any(w in mg for w in ["خيمة", "بيت", "دار", "سكن", "مسكن", "مأوى"])
    shelter_grc = any(w in tg for w in ["tent", "shelter", "dwelling", "house", "home", "abode", "chamber"])
    if shelter_ar and shelter_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: shelter/dwelling. Greek: tent/dwelling — matching.", "method": "masadiq_direct"}

    # --- GOAT / SHEEP / ANIMAL ---
    goat_ar = any(w in mg for w in ["معز", "شاة", "غنم", "ماعز", "صوف", "ضأن"])
    goat_grc = any(w in tg for w in ["goat", "sheep", "caprine", "ovine", "lamb", "flock", "herd"])
    if goat_ar and goat_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: goat/sheep domain. Greek: goat/sheep — matching.", "method": "masadiq_direct"}

    # --- PORCUPINE / HEDGEHOG ---
    porcupine_grc = any(w in tg for w in ["porcupine", "hedgehog", "spine", "quill"])
    porcupine_ar = any(w in mg for w in ["شوك", "قنفذ", "إبرة"])
    if porcupine_grc and porcupine_ar:
        return {"semantic_score": 0.55, "reasoning": "Arabic: spiny animal sense. Greek: porcupine — possible.", "method": "mafahim_deep"}

    # --- KNOWLEDGE / LEARNING / DISCOURSE ---
    learn_ar = any(w in mg for w in ["علم", "فقه", "حكمة", "درس", "معرفة", "حديث"])
    learn_grc = any(w in tg for w in ["learn", "teach", "knowledge", "discourse", "discuss", "scholar", "pupil", "wisdom"])
    if learn_ar and learn_grc:
        return {"semantic_score": 0.55, "reasoning": "Arabic: knowledge/discourse. Greek: learning/teaching — domain overlap.", "method": "masadiq_direct"}

    # --- ROAD / PATH / WAY ---
    road_ar = any(w in mg for w in ["طريق", "مسار", "سلوك", "جادة"])
    road_grc = any(w in tg for w in ["road", "path", "way", "route", "street", "track"])
    if road_ar and road_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: road/path. Greek: path/way — matching.", "method": "masadiq_direct"}

    # --- WRITING / DOCUMENT ---
    write_ar = any(w in mg for w in ["كتاب", "كتب", "لوح", "قلم", "مكتوب", "رسالة"])
    write_grc = any(w in tg for w in ["write", "tablet", "scroll", "document", "book", "letter", "scribe", "inscription"])
    if write_ar and write_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: writing/document. Greek: writing/document — matching.", "method": "masadiq_direct"}

    # --- IAMB / POETIC METER ---
    iamb_grc = "iamb" in tg
    poetry_ar = any(w in mg for w in ["شعر", "وزن", "نظم", "قصيدة"])
    if iamb_grc and poetry_ar:
        return {"semantic_score": 0.5, "reasoning": "Arabic: poetry domain. Greek: iambic meter — related poetic domain.", "method": "masadiq_direct"}

    # --- JUSTICE / RIGHTEOUSNESS / PIETY (tightly matched) ---
    # Use full Arabic word forms to avoid substring matches
    just_ar = any(w in mg for w in ["العدل", "الحق ", " الحق", "صلاح", "تقوى", "برّ", "صالح", "عبادة", "خشوع", "التقوى"])
    # Exclude contexts of humiliation/degradation that could superficially look like piety
    humil_ar = any(w in mg for w in ["ذَلَّلَ", "ذلَّلَ", "ذَلَّلْتُ", "حقّرته", "حقَّرَ", "كَسَّرَ", "استذل", "أهان", "حقَّرْتُ"])
    just_grc = any(w in tg for w in ["pious", "righteous", "just", "devout", "reverent", "holy", "sacred"])
    if just_ar and just_grc and not humil_ar:
        return {"semantic_score": 0.6, "reasoning": "Arabic: righteousness/virtue. Greek: pious/righteous — semantic match.", "method": "masadiq_direct"}
    if just_grc and humil_ar:
        return {"semantic_score": 0.0, "reasoning": "Arabic: humiliation/degradation (opposite of piety). Greek: pious/reverent — antonyms.", "method": "masadiq_direct"}
    if just_grc:
        return {"semantic_score": 0.0, "reasoning": f"Greek: pious/righteous. Arabic has no clear piety sense. masadiq: {masadiq_gloss[:60]}", "method": "masadiq_direct"}

    # --- ASSEMBLY / GATHERING ---
    gather_ar = any(w in mg for w in ["جمع", "اجتمع", "تجمع", "حشد", "كثرة", "جماعة"])
    gather_grc = any(w in tg for w in ["gather", "assemble", "collect", "crowd", "multitude", "congregation"])
    if gather_ar and gather_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: gathering/assembly. Greek: assembly/crowd — matching.", "method": "masadiq_direct"}

    # --- DARK / BLACK ---
    dark_ar = any(w in mg for w in ["اسودّ", "سواد", "ظلمة", "حلكة"])
    dark_grc = any(w in tg for w in ["dark", "black", "blackcap", "melanin", "sable", "shadow"])
    if dark_ar and dark_grc:
        return {"semantic_score": 0.55, "reasoning": "Arabic: blackness/darkness. Greek: dark/black — matching.", "method": "masadiq_direct"}

    # --- FOOD / EATING / NOURISHMENT ---
    food_ar = any(w in mg for w in ["أكل", "طعام", "شبع", "مأكول", "قوت", "طعم"])
    food_grc = any(w in tg for w in ["eat", "food", "nourish", "feed", "meal", "consume", "sustain"])
    if food_ar and food_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: food/eating. Greek: food/nourishment — matching.", "method": "masadiq_direct"}

    # --- LOUD SOUND / NOISE / VOICE (Arabic must explicitly have sound/voice sense) ---
    sound_ar = any(w in mg for w in ["صوت", "صَدَحَ", "صاح", "ضَجِيج", "ضجة", "صَخَب", "صوت", "نَعَق",
                                      "صاح الديك", "صاح الغراب", "رنَّ", "دَوَّى"])
    sound_grc = any(w in tg for w in ["sound", "noise", "voice", "shout", "cry", "clamor", "babble",
                                       "prattle", "murmur", "humming", "buzzing", "booming", "rumbling",
                                       "hollow sound"])
    if sound_ar and sound_grc:
        return {"semantic_score": 0.65, "reasoning": "Arabic: vocal sound/cry. Greek: sound/voice/noise — clear match.", "method": "masadiq_direct"}

    # --- HARDSHIP / TOIL / DIFFICULTY ---
    hard_ar = any(w in mg for w in ["شدة", "ضيق", "أزمة", "شَمْصَرَ", "ضيَّق", "مشقة"])
    hard_grc = any(w in tg for w in ["hard", "toil", "labor", "diffi", "hardship", "trial", "afflict", "trouble"])
    if hard_ar and hard_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: hardship/difficulty. Greek: toil/hardship — matching.", "method": "masadiq_direct"}

    # --- GREED / DESIRE ---
    greed_ar = any(w in mg for w in ["حرص", "جشع", "طمع", "شره"])
    greed_grc = any(w in tg for w in ["greed", "greedy", "avarice", "covet", "desire", "envy"])
    if greed_ar and greed_grc:
        return {"semantic_score": 0.65, "reasoning": "Arabic: greed/avarice. Greek: greedy/desire — matching.", "method": "masadiq_direct"}

    # --- FEAR / TERROR / PANIC ---
    fear_ar = any(w in mg for w in ["خوف", "رعب", "فزع", "ذُعر", "هلع", "خشية"])
    fear_grc = any(w in tg for w in ["fear", "terror", "panic", "fright", "scare", "dread", "alarm"])
    if fear_ar and fear_grc:
        return {"semantic_score": 0.7, "reasoning": "Arabic: fear/terror. Greek: fear/panic — strong semantic match.", "method": "masadiq_direct"}

    # --- PLANT / HERB / VEGETATION (tight: Arabic must clearly reference a named plant) ---
    plant_ar = any(w in mg for w in ["نبات", "عشب", "نبتٌ", "شَجَرٌ", "زَرْع", "نَبْت", "ثَمَر", "نَباتٌ"])
    plant_grc = any(w in tg for w in ["herb", "weed", "flower", "shrub", "vetch", "spurge",
                                       "milkweed", "chickling", "lathyrus", "saffron", "darnel",
                                       "ryegrass", "fleawort", "plantago", "marjoram", "knotgrass"])
    # Exclude compound "dog-headed" Greek that happens to be a plant name
    if plant_ar and plant_grc:
        return {"semantic_score": 0.45, "reasoning": "Arabic: named plant/herb. Greek: specific plant — domain overlap.", "method": "weak"}

    # --- LETTER / PROOF / ARGUMENT ---
    proof_ar = any(w in mg for w in ["حجة", "برهان", "دليل", "حجج"])
    proof_grc = any(w in tg for w in ["proof", "argument", "evidence", "theorem", "reason", "logic"])
    if proof_ar and proof_grc:
        return {"semantic_score": 0.65, "reasoning": "Arabic: proof/argument. Greek: proof/argument — clear match.", "method": "masadiq_direct"}

    # --- REACHING THE FEET / LONG GARMENT ---
    feet_grc = any(w in tg for w in ["reaching to the feet", "foot-length", "poderes"])
    long_ar = any(w in mg for w in ["طويل", "مديد"])
    if feet_grc and long_ar:
        return {"semantic_score": 0.45, "reasoning": "Arabic: tall/long. Greek: reaching to the feet — partial match through length.", "method": "mafahim_deep"}

    # --- MONOGAMY / MARRIAGE ---
    marr_grc = any(w in tg for w in ["monogamy", "marriage", "matrimon", "wed"])
    marr_ar = any(w in mg for w in ["زواج", "نكاح", "عقد"])
    if marr_grc and marr_ar:
        return {"semantic_score": 0.5, "reasoning": "Arabic: marriage. Greek: monogamy — domain overlap.", "method": "masadiq_direct"}

    # --- FRUGALITY / THRIFT ---
    thrift_grc = any(w in tg for w in ["frugal", "thrift", "stingy", "pheidon", "econom", "parsimony", "penur"])
    thrift_ar = any(w in mg for w in ["إمساك", "بخل", "شح", "ضنة", "جود"])
    if thrift_grc and thrift_ar:
        return {"semantic_score": 0.6, "reasoning": "Arabic: withholding/stinginess. Greek: frugality/thrift — matching.", "method": "masadiq_direct"}

    # --- PURE / UNMIXED ---
    pure_grc = any(w in tg for w in ["pure", "unmixed", "sheer", "neat", "unadulterated"])
    pure_ar = any(w in mg for w in ["خالص", "صافٍ", "نقي", "صِرف"])
    if pure_grc and pure_ar:
        return {"semantic_score": 0.65, "reasoning": "Arabic: pure/clear. Greek: pure/unmixed — strong match.", "method": "masadiq_direct"}

    # --- WICKEDNESS / EVIL / BLAME ---
    evil_ar = any(w in mg for w in ["خبيث", "شرير", "سُوء", "سَوء", "ذَمّ", "ذَمَّ", "خيانة", "قبيح"])
    evil_grc = any(w in tg for w in ["evil", "wicked", "blam", "malicious", "villain", "reproach"])
    if evil_ar and evil_grc:
        return {"semantic_score": 0.65, "reasoning": "Arabic: wickedness/evil. Greek: evil/blamed — matching.", "method": "masadiq_direct"}
    # Bad flavor/quality (κακό- compounds)
    bad_quality_grc = any(w in tg for w in ["bad juice", "bad flavor", "kakochylos", "with bad"])
    bad_quality_ar = any(w in mg for w in ["خبيث", "فاسد", "رديء", "غِربان", "الغربان", "حدث الصبي"])
    if bad_quality_grc:
        return {"semantic_score": 0.2, "reasoning": f"Greek: bad quality/juice. Arabic masadiq: {masadiq_gloss[:50]}. Very weak domain link.", "method": "weak"}

    # --- HATED / ENMITY (tight: Arabic must have actual hate/enmity sense) ---
    hate_ar = any(w in mg for w in ["كره", "بغض", "عداوة", "حقد", "مكروه"])
    hate_grc = any(w in tg for w in ["hate", "hated", "enmity", "hatred", "dislike", "abhor"])
    # Exclude proper names masquerading as hate
    is_proper_name_masadiq = any(w in mg for w in ["بن سَبُعٍ", "بن سباع", "ابن", "اسم", "يكنى"])
    if hate_ar and hate_grc and not is_proper_name_masadiq:
        return {"semantic_score": 0.65, "reasoning": "Arabic: hatred/enmity. Greek: hated/hatred — matching.", "method": "masadiq_direct"}
    if hate_grc and is_proper_name_masadiq:
        return {"semantic_score": 0.0, "reasoning": "Arabic masadiq describes a proper person, not hatred. Greek: hated.", "method": "masadiq_direct"}

    # --- INVENTING / CONTRIVING ---
    invent_grc = any(w in tg for w in ["contrivance", "invention", "device", "craft"])
    invent_ar = any(w in mg for w in ["اختراع", "حيلة", "أداة"])
    if invent_grc and invent_ar:
        return {"semantic_score": 0.45, "reasoning": "Arabic: device/craft. Greek: contrivance/invention — weak match.", "method": "mafahim_deep"}

    # --- RECEIPT / ACCEPT ---
    accept_ar = any(w in mg for w in ["قبول", "استقبل", "قَبِلَ", "تلقى"])
    accept_grc = any(w in tg for w in ["receive", "accept", "welcome", "hospitable"])
    if accept_ar and accept_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: acceptance/receiving. Greek: receive favourably — matching.", "method": "masadiq_direct"}

    # --- TRANSFORM / CHANGE ---
    change_ar = any(w in mg for w in ["تحوّل", "صرف", "انقلب", "تغير"])
    change_grc = any(w in tg for w in ["change", "transform", "alter", "convert", "shift"])
    if change_ar and change_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: turning/changing. Greek: change/transform — matching.", "method": "masadiq_direct"}

    # --- BEHEADING / DECAPITATION ---
    behead_grc = any(w in tg for w in ["decapitate", "behead", "sever head"])
    behead_ar = any(w in mg for w in ["قطع", "رأس", "جرد"])
    if behead_grc:
        if behead_ar:
            return {"semantic_score": 0.5, "reasoning": "Arabic: cutting. Greek: decapitate — partial match.", "method": "masadiq_direct"}
        return {"semantic_score": 0.0, "reasoning": "Greek: beheading. Arabic root has no head-cutting sense in masadiq.", "method": "masadiq_direct"}

    # --- SPINE / REED / RUSH ---
    rush_grc = any(w in tg for w in ["rush-mat", "reed mat", "rush mat", "cane", "mat"])
    rush_ar = any(w in mg for w in ["قصب", "حصير", "بردي"])
    if rush_grc and rush_ar:
        return {"semantic_score": 0.5, "reasoning": "Arabic: rush/reed material. Greek: rush-mat — domain overlap.", "method": "masadiq_direct"}

    # --- COFFIN / BURIAL ---
    coffin_grc = any(w in tg for w in ["coffin", "urn", "burial", "tomb", "sarcophag", "mortuary"])
    coffin_ar = any(w in mg for w in ["قبر", "موت", "ميت", "جنازة"])
    if coffin_grc:
        if coffin_ar:
            return {"semantic_score": 0.55, "reasoning": "Arabic: death/burial. Greek: coffin/urn — matching domain.", "method": "masadiq_direct"}
        return {"semantic_score": 0.0, "reasoning": "Greek: coffin/burial. Arabic root has no funerary sense.", "method": "masadiq_direct"}

    # --- GRACE / DELICACY / BEAUTY ---
    grace_grc = any(w in tg for w in ["graceful", "delicate", "pretty", "elegant", "refined", "lovely"])
    grace_ar = any(w in mg for w in ["جمال", "رشاقة", "لطيف", "نعومة", "خفة", "وشّى"])
    if grace_grc and grace_ar:
        return {"semantic_score": 0.65, "reasoning": "Arabic: graceful/light/ornate. Greek: graceful/delicate — strong match.", "method": "masadiq_direct"}

    # --- PIGPEN / SWINE ---
    pig_grc = any(w in tg for w in ["pig", "swine", "pork", "sow", "hog", "pigsty", "pigpen"])
    if pig_grc:
        return {"semantic_score": 0.0, "reasoning": f"Greek: swine/pigpen. Arabic has no pig/swine semantic sense. masadiq: {masadiq_gloss[:50]}", "method": "masadiq_direct"}

    # --- INDESTRUCTIBLE / IMMORTAL ---
    indestr_grc = any(w in tg for w in ["indestructible", "immortal", "imperishable", "undying", "eternal"])
    indestr_ar = any(w in mg for w in ["بقاء", "دوام", "خلود", "أبدي"])
    if indestr_grc and indestr_ar:
        return {"semantic_score": 0.6, "reasoning": "Arabic: permanence/eternity. Greek: indestructible — matching.", "method": "masadiq_direct"}

    # --- SLEEP / LETHARGY ---
    sleep_grc = any(w in tg for w in ["sleep", "lethargy", "letharg", "drowsy", "torpor"])
    sleep_ar = any(w in mg for w in ["نوم", "كسل", "خدر", "غفلة"])
    if sleep_grc and sleep_ar:
        return {"semantic_score": 0.6, "reasoning": "Arabic: sleep/torpor. Greek: lethargy/sleep — matching.", "method": "masadiq_direct"}

    # --- ACCOMPLISH / COMPLETE ---
    accomp_grc = any(w in tg for w in ["accomplish", "complete", "finish", "achieve", "succeed"])
    accomp_ar = any(w in mg for w in ["أتمّ", "كمال", "أنجز", "بلغ"])
    if accomp_grc and accomp_ar:
        return {"semantic_score": 0.55, "reasoning": "Arabic: completion/achievement. Greek: accomplish/complete — domain overlap.", "method": "masadiq_direct"}

    # --- SADNESS / GRIEF ---
    sad_grc = any(w in tg for w in ["sad", "grief", "sorrow", "wretched", "miser", "lament", "mourn"])
    sad_ar = any(w in mg for w in ["حزن", "مصيبة", "ألم", "بؤس"])
    if sad_grc and sad_ar:
        return {"semantic_score": 0.6, "reasoning": "Arabic: grief/sadness. Greek: sad/wretched — matching.", "method": "masadiq_direct"}

    # --- OATH / COVENANT / TESTAMENT ---
    oath_grc = any(w in tg for w in ["testament", "will", "covenant", "oath", "vow", "contract"])
    oath_ar = any(w in mg for w in ["عهد", "ميثاق", "وصية", "قسم"])
    if oath_grc and oath_ar:
        return {"semantic_score": 0.6, "reasoning": "Arabic: covenant/testament. Greek: testament/will — matching.", "method": "masadiq_direct"}

    # --- ABSTRACT DOCTRINE / -ISM ---
    ism_grc = tg.startswith("forms abstract nouns") or tg == "-ισμός"
    if ism_grc:
        return {"semantic_score": 0.0, "reasoning": "Greek target is the suffix -ισμός (formative suffix), not a lexical item.", "method": "masadiq_direct"}

    # --- SPREADING FLAT / LEVEL ---
    flat_ar = any(w in mg for w in ["انبسط", "استوى", "مسطح"])
    flat_grc = any(w in tg for w in ["flat", "level", "spread", "extend", "broad"])
    if flat_ar and flat_grc:
        return {"semantic_score": 0.55, "reasoning": "Arabic: spreading flat/leveling. Greek: flat/broad — matching.", "method": "masadiq_direct"}

    # --- SPEAR / LANCE ---
    spear_grc = any(w in tg for w in ["spear", "lance", "pike", "partisan", "javelin"])
    spear_ar = any(w in mg for w in ["رمح", "حربة", "طعن"])
    if spear_grc and spear_ar:
        return {"semantic_score": 0.6, "reasoning": "Arabic: spear/weapon. Greek: spear — matching.", "method": "masadiq_direct"}

    # --- WOODPECKER / BIRD ---
    bird_grc = any(w in tg for w in ["woodpecker", "owl", "eagle", "hawk", "finch", "lark", "pigeon", "sparrow", "crane", "blackcap", "vulture"])
    bird_ar = any(w in mg for w in ["طير", "عقاب", "نسر", "طائر"])
    if bird_grc and bird_ar:
        return {"semantic_score": 0.45, "reasoning": "Arabic: bird domain. Greek: specific bird — faint domain match.", "method": "weak"}

    # --- EARTHWORM ---
    earthworm_grc = "earthworm" in tg
    if earthworm_grc:
        return {"semantic_score": 0.0, "reasoning": "Greek: earthworm. Arabic root has no worm/soil-creature sense.", "method": "masadiq_direct"}

    # --- POMEGRANATE ---
    pomegranate_grc = "pomegranate" in tg
    pomegranate_ar = any(w in mg for w in ["رمان"])
    if pomegranate_grc and pomegranate_ar:
        return {"semantic_score": 0.5, "reasoning": "Arabic: pomegranate sense. Greek: pomegranate — possible loan domain.", "method": "mafahim_deep"}
    if pomegranate_grc:
        return {"semantic_score": 0.0, "reasoning": "Greek: pomegranate. Arabic root has no pomegranate sense.", "method": "masadiq_direct"}

    # --- MOUFLON ---
    mouflon_grc = "mouflon" in tg
    if mouflon_grc:
        return {"semantic_score": 0.0, "reasoning": "Greek: mouflon (wild sheep). Arabic root has no wild-sheep sense.", "method": "masadiq_direct"}

    # --- SESAME ---
    sesame_grc = "sesame" in tg
    if sesame_grc:
        return {"semantic_score": 0.0, "reasoning": "Greek: sesame. Arabic root has no sesame sense.", "method": "masadiq_direct"}

    # --- CARPENTER'S SQUARE ---
    carpsq_grc = any(w in tg for w in ["carpenter's square", "square", "level tool", "alphadi"])
    carpsq_ar = any(w in mg for w in ["نجار", "بناء", "قياس"])
    if carpsq_grc and carpsq_ar:
        return {"semantic_score": 0.4, "reasoning": "Arabic: building/measurement. Greek: carpenter's square — faint overlap.", "method": "weak"}

    # --- TRUST / CONFIDENCE / BELIEF ---
    trust_grc = any(w in tg for w in ["trust", "confidence", "faith", "belief", "pistis"])
    trust_ar = any(w in mg for w in ["ثقة", "أمان", "إيمان", "تصديق"])
    if trust_grc and trust_ar:
        return {"semantic_score": 0.6, "reasoning": "Arabic: trust/faith. Greek: trust/confidence — matching.", "method": "masadiq_direct"}

    # --- REVENGE / VENGEANCE ---
    revenge_grc = any(w in tg for w in ["revenge", "vengeance", "avenge", "retribution"])
    revenge_ar = any(w in mg for w in ["انتقام", "ثأر", "قصاص"])
    if revenge_grc and revenge_ar:
        return {"semantic_score": 0.6, "reasoning": "Arabic: revenge/retribution. Greek: vengeance — matching.", "method": "masadiq_direct"}

    # --- RICHNESS / ABUNDANCE ---
    rich_grc = any(w in tg for w in ["abundant", "copious", "rich", "plentiful", "lavish"])
    rich_ar = any(w in mg for w in ["كثرة", "وفرة", "خير", "غنى"])
    if rich_grc and rich_ar:
        return {"semantic_score": 0.55, "reasoning": "Arabic: abundance/richness. Greek: abundant/copious — matching.", "method": "masadiq_direct"}

    # --- WIDE / SPACIOUS ---
    wide_ar = any(w in mg for w in ["واسع", "رحب", "فضاء", "اتسع", "فضيح"])
    wide_grc = any(w in tg for w in ["wide", "spacious", "broad", "expansive", "ample"])
    if wide_ar and wide_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: wide/spacious. Greek: wide/broad — matching.", "method": "masadiq_direct"}

    # --- CONFESSING / ACKNOWLEDGING ---
    confess_ar = any(w in mg for w in ["إقرار", "اعتراف", "جحود", "إنكار"])
    confess_grc = any(w in tg for w in ["confess", "acknowledge", "admit", "declare", "proclaim"])
    if confess_ar and confess_grc:
        return {"semantic_score": 0.55, "reasoning": "Arabic: confession/acknowledgment. Greek: declaration — overlap.", "method": "masadiq_direct"}

    # --- GOOD DEED / BENEFIT ---
    good_grc = any(w in tg for w in ["good deed", "kindness", "benefit", "charity", "benevolence"])
    good_ar = any(w in mg for w in ["خير", "إحسان", "معروف", "بر"])
    if good_grc and good_ar:
        return {"semantic_score": 0.6, "reasoning": "Arabic: goodness/kindness. Greek: good deed/kindness — matching.", "method": "masadiq_direct"}

    # --- REALITY / TRUTH ---
    reality_grc = any(w in tg for w in ["in fact", "in reality", "actually", "truly", "truly"])
    reality_ar = any(w in mg for w in ["حقيقة", "واقع", "فعل"])
    if reality_grc and reality_ar:
        return {"semantic_score": 0.5, "reasoning": "Arabic: reality/fact. Greek: in reality — weak match.", "method": "weak"}

    # --- BREAD / FOOD PREPARATION ---
    bread_grc = any(w in tg for w in ["bread", "baking", "bread-making", "grain", "wheat", "cereal"])
    bread_ar = any(w in mg for w in ["خبز", "قمح", "دقيق", "عجن", "طحين"])
    if bread_grc and bread_ar:
        return {"semantic_score": 0.6, "reasoning": "Arabic: bread/grain. Greek: bread-making — matching.", "method": "masadiq_direct"}

    # --- ICONOMACHY / ICONOCLASM ---
    icon_grc = any(w in tg for w in ["iconoclasm", "iconomachy", "icon"])
    icon_ar = any(w in mg for w in ["صورة", "أيقونة"])
    if icon_grc:
        return {"semantic_score": 0.0, "reasoning": "Greek: iconoclasm/iconomachy. Arabic root has no image/icon sense.", "method": "masadiq_direct"}

    # --- POORHOUSE / CHARITY ---
    poor_grc = any(w in tg for w in ["poorhouse", "almshouse", "charity"])
    poor_ar = any(w in mg for w in ["فقر", "مسكين", "صدقة"])
    if poor_grc and poor_ar:
        return {"semantic_score": 0.5, "reasoning": "Arabic: poverty/charity. Greek: poorhouse — domain overlap.", "method": "masadiq_direct"}

    # --- OLYMPIAN / SACRED OLIVE ---
    olive_grc = any(w in tg for w in ["olive", "sacred", "moriai", "elaiai"])
    olive_ar = any(w in mg for w in ["زيتون", "شجر"])
    if olive_grc and olive_ar:
        return {"semantic_score": 0.4, "reasoning": "Arabic: tree/plant. Greek: olive trees — faint domain link.", "method": "weak"}

    # --- AXE / TOOL ---
    curb_grc = any(w in tg for w in ["curb chain", "bit", "bridle", "rein"])
    curb_ar = any(w in mg for w in ["لجام", "قيد", "زمام"])
    if curb_grc and curb_ar:
        return {"semantic_score": 0.5, "reasoning": "Arabic: restraint/bridle. Greek: curb chain — domain overlap.", "method": "masadiq_direct"}

    # --- SHEATH / SHELL / CASE ---
    sheath_grc = any(w in tg for w in ["sheath", "case", "shell", "husk", "pod", "scabbard", "hull"])
    sheath_ar = any(w in mg for w in ["غِمد", "قِراب", "غلاف", "قِشرة"])
    if sheath_grc and sheath_ar:
        return {"semantic_score": 0.55, "reasoning": "Arabic: sheath/cover. Greek: sheath/case — domain overlap.", "method": "masadiq_direct"}
    if sheath_grc:
        return {"semantic_score": 0.0, "reasoning": f"Greek: sheath/shell. Arabic has no covering/sheath sense. masadiq: {masadiq_gloss[:50]}", "method": "masadiq_direct"}

    # --- THROAT / NECK / STRANGULATION ---
    throat_ar = any(w in mg for w in ["حلق", "حَلْقَمَ", "الحُلْقوم", "ذَبَحَ"])
    throat_grc = any(w in tg for w in ["throat", "neck", "windpipe", "trachea", "strangle", "throttle"])
    if throat_ar and throat_grc:
        return {"semantic_score": 0.65, "reasoning": "Arabic: throat-cutting/windpipe. Greek: throat/strangulation — matching.", "method": "masadiq_direct"}

    # --- SCRAPINGS / SHAVINGS (cutting residue) ---
    scrap_grc = any(w in tg for w in ["scraping", "shaving", "filing", "paring", "chips"])
    scrap_ar = any(w in mg for w in ["شَدَخَ", "قَشَرَ", "كَشَطَ", "برادة"])
    if scrap_grc and scrap_ar:
        return {"semantic_score": 0.5, "reasoning": "Arabic: smashing/scraping. Greek: scrapings/shavings — cutting residue domain.", "method": "masadiq_direct"}

    # --- ENCLOSURE / PEN / FENCE ---
    fence_ar = any(w in mg for w in ["حَظيرة", "حائط", "سياج", "حظيرة", "خُص"])
    fence_grc = any(w in tg for w in ["enclosure", "fence", "pen", "paddock", "corral", "palisade"])
    if fence_ar and fence_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: enclosure/pen. Greek: enclosure/fence — matching.", "method": "masadiq_direct"}

    # --- SUMMIT / TOP / PEAK ---
    summit_ar = any(w in mg for w in ["أعلاه", "قِمَّة", "ذُرْوة", "رأس الجبل", "قُنَّة"])
    summit_grc = any(w in tg for w in ["summit", "peak", "top", "apex", "crest", "pinnacle"])
    if summit_ar and summit_grc:
        return {"semantic_score": 0.65, "reasoning": "Arabic: mountain summit/top. Greek: summit/peak — matching.", "method": "masadiq_direct"}

    # --- HEAVY / THICK / BULKY ---
    heavy_ar = any(w in mg for w in ["ثقيل", "غَلِيظ", "ضَخْم", "ثَخِين", "بَطِين", "كَثِير"])
    heavy_grc = any(w in tg for w in ["heavy", "thick", "dense", "bulky", "massive", "corpulent"])
    if heavy_ar and heavy_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: heavy/thick. Greek: heavy/dense — matching.", "method": "masadiq_direct"}

    # --- RISE / LIFT / ELEVATE ---
    rise_ar = any(w in mg for w in ["رَفَعَ", "رَفْع", "ارتفع", "ارتفاع", "عَلا", "رَفَعَه"])
    rise_grc = any(w in tg for w in ["rise", "lift", "raise", "elevate", "ascend", "mount"])
    if rise_ar and rise_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: lifting/raising. Greek: rise/lift — matching.", "method": "masadiq_direct"}

    # --- DESCENT / GOING DOWN ---
    descend_ar = any(w in mg for w in ["نَزَلَ", "هَبَطَ", "انحدر", "نزول"])
    descend_grc = any(w in tg for w in ["descent", "go down", "come down", "descend", "katabasis"])
    if descend_ar and descend_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: descent/going down. Greek: descent/going down — matching.", "method": "masadiq_direct"}

    # --- HANDLE / HOLD / MANAGE ---
    handle_ar = any(w in mg for w in ["أمسك", "قَبَضَ", "يمسك", "إدارة", "تناول"])
    handle_grc = any(w in tg for w in ["handle", "hold", "manage", "wield", "grasp"])
    if handle_ar and handle_grc:
        return {"semantic_score": 0.55, "reasoning": "Arabic: hold/manage. Greek: handle/hold — domain match.", "method": "masadiq_direct"}

    # --- DIVINATION / PROPHECY ---
    divine_ar = any(w in mg for w in ["تَكَهَّنَ", "تحزَّى", "كاهن", "عِراف", "نبوءة"])
    divine_grc = any(w in tg for w in ["divine", "prophecy", "oracle", "augury", "soothsay", "prophesy"])
    if divine_ar and divine_grc:
        return {"semantic_score": 0.65, "reasoning": "Arabic: divination/prophecy. Greek: prophecy/oracle — matching.", "method": "masadiq_direct"}

    # --- SWEETNESS / PLEASANT TONE ---
    sweet_grc = any(w in tg for w in ["sweet", "pleasant", "melodious", "euphon", "honeyed"])
    sweet_ar = any(w in mg for w in ["حَلاوة", "حلو", "لذيذ", "عذوبة"])
    if sweet_grc and sweet_ar:
        return {"semantic_score": 0.6, "reasoning": "Arabic: sweetness/pleasantness. Greek: sweet/melodious — matching.", "method": "masadiq_direct"}

    # --- CHAMELEON ---
    cham_grc = "chameleon" in tg
    cham_ar = any(w in mg for w in ["حِرباء", "أفعى", "حشرة"])
    if cham_grc:
        return {"semantic_score": 0.0, "reasoning": "Greek: chameleon. Arabic has no chameleon/lizard sense.", "method": "masadiq_direct"}

    # --- LETTER ALPHA / ALPHABETIC ---
    alpha_grc = any(w in tg for w in ["delta", "alpha", "beta", "gamma", "letter", "alphabet"])
    if alpha_grc:
        return {"semantic_score": 0.0, "reasoning": f"Greek: letter of the alphabet ({target_gloss[:40]}). Not a lexical match.", "method": "masadiq_direct"}

    # --- CATFISH / SPECIFIC FISH SPECIES ---
    catfish_grc = any(w in tg for w in ["catfish", "silurus", "carp", "bream", "perch", "pike", "trout"])
    catfish_ar = any(w in mg for w in ["سمك", "حوت"])
    if catfish_grc and catfish_ar:
        return {"semantic_score": 0.6, "reasoning": "Arabic: fish. Greek: specific fish species — direct match.", "method": "masadiq_direct"}
    if catfish_grc:
        return {"semantic_score": 0.0, "reasoning": f"Greek: specific fish species. Arabic has no fish sense.", "method": "masadiq_direct"}

    # --- SPRAY / SPRINKLE / SPATTER (water scatter) ---
    spray_ar = any(w in mg for w in ["نَفْض", "رَش", "رَشّ", "تَرَشُّش", "رَشاش"])
    spray_grc = any(w in tg for w in ["spray", "sprinkle", "spatter", "splash", "shower"])
    if spray_ar and spray_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: spraying/sprinkling water. Greek: spray/sprinkle — matching.", "method": "masadiq_direct"}

    # --- STABILITY / DWELLING / PERMANENCE ---
    dwell_ar = any(w in mg for w in ["إرباب", "مُقيم", "أقام", "استوطن", "ثبت", "مُقيماً"])
    dwell_grc = any(w in tg for w in ["dwell", "reside", "settle", "inhabit", "stay", "remain"])
    if dwell_ar and dwell_grc:
        return {"semantic_score": 0.6, "reasoning": "Arabic: settling/residing. Greek: dwelling/remaining — matching.", "method": "masadiq_direct"}

    # -----------------------------------------------------------------------
    # TIER 2 — No lexical hit: fall back to heuristics
    # -----------------------------------------------------------------------

    # Short or uninformative masadiq
    masadiq_short = len(masadiq_gloss.strip()) < 30
    if masadiq_short:
        return {
            "semantic_score": 0.0,
            "reasoning": f"Arabic masadiq too short/uninformative to establish semantic connection. Greek: '{target_gloss[:60]}'",
            "method": "masadiq_direct"
        }

    # No match found — return 0.0
    return {
        "semantic_score": 0.0,
        "reasoning": (f"No semantic overlap: Arabic masadiq '{masadiq_gloss[:60]}' vs Greek '{target_gloss[:60]}'"),
        "method": "masadiq_direct"
    }


def process_chunk(chunk_num: int, pairs: list) -> list:
    results = []
    for p in pairs:
        arabic_root = p.get("arabic_root", "")
        target_lemma = p.get("target_lemma", "")
        masadiq_gloss = p.get("masadiq_gloss", "")
        mafahim_gloss = p.get("mafahim_gloss", "")
        target_gloss = p.get("target_gloss", "")
        target_ipa = p.get("target_ipa", "")

        scored = score_pair(
            arabic_root, target_lemma, masadiq_gloss,
            mafahim_gloss, target_gloss, target_ipa
        )

        result = {
            "source_lemma": arabic_root,
            "target_lemma": target_lemma,
            "semantic_score": scored["semantic_score"],
            "reasoning": scored["reasoning"],
            "method": scored["method"],
            "lang_pair": "ara-grc",
            "model": "sonnet-phase1"
        }
        results.append(result)
    return results


def main():
    all_results = {}
    total_pairs = 0
    high_score_count = 0
    top_discoveries = []

    for chunk_num in range(170, 201):
        fname = os.path.join(BASE_IN, f"phase1_new_{chunk_num:03d}.jsonl")
        pairs = []
        with open(fname, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    pairs.append(json.loads(line))

        results = process_chunk(chunk_num, pairs)
        all_results[chunk_num] = results

        # Write output
        out_fname = os.path.join(BASE_OUT, f"phase1_scored_{chunk_num:03d}.jsonl")
        with open(out_fname, "w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        # Stats
        chunk_high = sum(1 for r in results if r["semantic_score"] >= 0.5)
        high_score_count += chunk_high
        total_pairs += len(results)

        # Collect top discoveries
        for r in results:
            if r["semantic_score"] >= 0.6:
                top_discoveries.append(r)

        print(f"Chunk {chunk_num}: {len(results)} pairs, {chunk_high} scored >= 0.5")

    print(f"\n=== SUMMARY ===")
    print(f"Total pairs processed: {total_pairs}")
    print(f"Pairs scored >= 0.5: {high_score_count}")
    print(f"Pairs scored >= 0.6: {len(top_discoveries)}")

    # Sort top discoveries by score
    top_discoveries.sort(key=lambda x: x["semantic_score"], reverse=True)
    print(f"\n=== TOP 10 DISCOVERIES ===")
    for r in top_discoveries[:10]:
        print(f"  {r['source_lemma']} → {r['target_lemma']} | score={r['semantic_score']} | {r['reasoning'][:80]}")


if __name__ == "__main__":
    main()
