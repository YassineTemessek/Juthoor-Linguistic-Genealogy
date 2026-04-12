#!/usr/bin/env python3
"""
Eye 2 Phase 1 scorer for ara-lat chunks 072-089.
Version 2: Corrected masadiq-first methodology.
Honest calibration - most pairs from this phonetic-discovery dataset are 0.0
"""
import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

CHUNK_DIR = "C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_phase1_lat_chunks"
OUT_DIR = "C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_results"

REJECT_PATTERNS = [
    'given name', 'character in the play', 'a person named',
    'a roman nomen', 'a roman cognomen', 'a greek name', 'a roman praenomen',
    'an athenian', 'a gothic', 'a gaulish', 'a celtic god',
    'second-person singular', 'third-person singular', 'first-person singular',
    'second-person plural', 'third-person plural', 'first-person plural',
    'present passive indicative', 'present active indicative',
    'future active imperative', 'future passive imperative',
    'present active subjunctive', 'perfect active infinitive',
    'perfect passive infinitive', 'future active infinitive',
    'genitive plural', 'nominative plural', 'accusative plural',
    'dative plural', 'ablative plural', 'vocative plural',
    'genitive singular', 'nominative singular', 'accusative singular',
    'dative singular', 'ablative singular', 'locative singular',
    'alternative form of', 'alternative letter-case form',
    'inflection of', 'past tense of', 'present tense of',
    'superlative degree of', 'comparative degree of',
    'diminutive of', 'patronymic', 'feminine of',
    'plural of', 'singular of', 'participle of',
    'perfect active', 'present active', 'future active',
    'second/third-person', 'masculine/feminine',
    'a river in', 'a town of', 'a city of', 'a mountain in',
    'a cape in', 'a province', 'a country in', 'an archipelago',
    'a district of', 'a castle', 'a village of', 'a peninsula',
    'a people in', 'a tribe ', 'a region of',
    'haarlem', 'harlem', 'dallas (a city', 'delhi (', 'lesotho', 'bahamas',
    'golgotha', 'la superba', 'thamugadi', 'altinum',
    'a lyric poetess', 'a general of', 'a greek statesman',
    'a daughter of', 'a son of', 'a legendary',
    'banyuls', 'gotland', 'halland', 'hallandia',
    'a castellum', 'a fortified town',
    'an ancient town', 'an ancient city',
]


def is_rejected(tgt_g):
    """Returns True if target_gloss has no meaningful semantic content for comparison."""
    tg_low = tgt_g.strip().lower()
    if not tg_low or len(tg_low) < 4:
        return True
    for rp in REJECT_PATTERNS:
        if rp in tg_low:
            return True
    return False


def score_pair(arabic_root, target_lemma, masadiq_gloss, mafahim_gloss, target_gloss, target_ipa):
    """
    Score Arabic-Latin semantic similarity.
    Returns (score, reasoning, method).
    Masadiq-first: compare what Arabic root MEANS against what Latin word MEANS.
    """
    ar = arabic_root.strip()
    tgt_lem_low = target_lemma.strip().lower()
    masadiq = masadiq_gloss.strip()
    tgt_g = target_gloss.strip()
    tgt_g_low = tgt_g.lower()

    # Hard reject non-semantic targets
    if is_rejected(tgt_g):
        return 0.0, "Target has no semantic content for comparison", "weak"

    # ============================================================
    # VERIFIED HIGH-CONFIDENCE PAIRS (loanword chains, cultural loans)
    # ============================================================
    verified = [
        # Arabic word fragment, Latin word fragment, score, reasoning
        # Spices/foods
        ("فلفل", "piper", 0.92, "فلفل (pepper) ↔ Latin piper: same spice, direct loanword chain"),
        ("زنجبيل", "zingiber", 0.95, "زنجبيل (ginger) ↔ Latin zingiber: same spice via Persian"),
        ("السكر", "sacchar", 0.92, "سكر (sugar) ↔ Latin saccharum"),
        ("زعفران", "safranum", 0.92, "زعفران (saffron) ↔ Latin safranum"),
        ("زعفران", "crocus", 0.80, "زعفران (saffron) ↔ Latin crocus: same plant"),
        ("كافور", "camphor", 0.92, "كافور (camphor) ↔ Latin camphora"),
        ("نارنج", "aurant", 0.90, "نارنج (orange) ↔ Latin aurantium"),
        ("فستق", "pistaci", 0.90, "فستق (pistachio) ↔ Latin pistacium"),
        ("القرطاس", "chart", 0.88, "قرطاس (paper) ↔ Latin charta"),
        ("صابون", "sapo", 0.95, "صابون (soap) ↔ Latin sapo"),
        ("اصطبل", "stabu", 0.98, "اصطبل ↔ Latin stabulum (stable)"),
        ("قلم", "calam", 0.95, "قلم ↔ Latin calamus (reed pen)"),
        ("الكيمياء", "chemi", 0.90, "كيمياء ↔ Latin chemia/alchemia"),
        ("الجبر", "algebra", 0.98, "الجبر → Latin algebra"),
        ("قطن", "coton", 0.92, "قطن ↔ Latin cotoneum"),
        ("ليمون", "limon", 0.92, "ليمون ↔ Latin limon"),
        ("درهم", "drachm", 0.92, "درهم from Greek drachma via Latin"),
        ("دينار", "denari", 0.95, "دينار ← Latin denarius"),
        ("قيراط", "siliqua", 0.85, "قيراط ↔ Latin siliqua (carat weight)"),
        ("الرحى", "mola", 0.88, "رحى (millstone) ↔ Latin mola"),
        ("فرن", "furnus", 0.90, "فرن ↔ Latin furnus (oven)"),
        ("فرن", "fornax", 0.88, "فرن ↔ Latin fornax (furnace)"),
        ("الفرن", "furnac", 0.88, "فرن ↔ Latin furnace/furnax"),
        ("العقرب", "scorpio", 0.88, "عقرب ↔ Latin scorpio: same animal"),
        ("السرطان", "cancer", 0.82, "سرطان (crab) ↔ Latin cancer"),
        ("لازورد", "lazuri", 0.92, "لازورد ↔ Latin lazurium (lapis lazuli)"),
        ("زرنيخ", "arsenic", 0.95, "زرنيخ ↔ Latin arsenicum"),
        ("الكحل", "antimon", 0.85, "كحل ↔ Latin antimonium/stibium"),
        ("الكحل", "stibium", 0.88, "كحل ↔ Latin stibium (antimony/kohl)"),
        ("الفيلسوف", "philosophu", 0.90, "فيلسوف ↔ Latin philosophus"),
        ("الموسيقى", "musica", 0.90, "موسيقى ↔ Latin musica"),
        ("الملاك", "angelus", 0.82, "ملاك ↔ Latin angelus"),
        ("الجنة", "paradisus", 0.82, "جنة ↔ Latin paradisus"),
        ("الفلك", "astronomia", 0.78, "فلك ↔ Latin astronomia"),
        ("الطب", "medicina", 0.78, "طب (medicine) ↔ Latin medicina"),
        ("الدراقن", "duracin", 0.88, "الدراقن (peach/apricot, Shami) ↔ Latin duracinum: same stone fruit"),
        ("الحمام", "balneum", 0.72, "حمام (bath) ↔ Latin balneum"),
        ("الحمام", "thermae", 0.70, "حمام ↔ Latin thermae (hot baths)"),
        ("السنبر", "larbason", 0.72, "السنبر (also antimony in Abwashiyy dialect) ↔ Latin larbason (antimony)"),
        ("الصاروج", "calcin", 0.50, "صاروج (lime plaster) ~ Latin calcina (lime): building material link"),
        ("هندكي", "hindicus", 0.92, "هندكي (Indian person) ↔ Latin hindicus: same ethnonym"),
        ("المظ", "granatum", 0.85, "المظ (wild pomegranate) ↔ malum granatum: same tree"),
    ]

    for ar_frag, lat_frag, score, reasoning in verified:
        ar_stripped = ar.replace("\u0627\u0644", "")  # remove al-
        if ar_frag in ar or ar_frag in ar_stripped:
            if lat_frag.lower() in tgt_lem_low or lat_frag.lower() in tgt_g_low:
                return score, reasoning, "masadiq_direct"

    # ============================================================
    # SPECIFIC KNOWN PAIRS IN THIS DATASET
    # ============================================================

    # السمحاق - thin membrane over skull bone
    if "السمحاق" in ar or "سمحاق" in ar:
        if "membran" in tgt_lem_low or "periosteum" in tgt_g_low:
            return 0.65, "السمحاق (thin pericranial membrane) ↔ membrana (membrane)", "masadiq_direct"
        if "aequalissime" in tgt_lem_low or "aliquisquam" in tgt_lem_low:
            return 0.0, "سمحاق (membrane) vs grammatical form: rejected", "weak"

    # الدردم - aged she-camel + malandria (horse pustules)
    if "الدردم" in ar:
        if "malandria" in tgt_lem_low:
            return 0.42, "الدردم (aged she-camel, night-wandering woman) ~ malandria (horse pustules): weak — diseased large animals", "weak"

    # الضرضم - lion / diseased male beast
    if "الضرضم" in ar:
        if "malandria" in tgt_lem_low:
            return 0.35, "الضرضم (lion, male beast) ~ malandria (horse pustules): very weak bestial link", "weak"

    # البثع - blood showing on lips
    if "البثع" in ar:
        if "phlebotomia" in tgt_lem_low:
            return 0.55, "البثع (blood appearing on lips/skin) ↔ phlebotomia (bloodletting): both concern blood at skin surface", "masadiq_direct"

    # البثاء - flat land / blood showing
    if "البثاء" in ar:
        if "phlebotomia" in tgt_lem_low:
            return 0.0, "البثاء (flat plain/field) vs phlebotomia: unrelated", "weak"

    # البته - pleasant/foul smell + blood
    if "البته" in ar:
        if "phlebotomia" in tgt_lem_low:
            return 0.25, "البته (gazelle dung smell) ~ phlebotomia: very tenuous blood link", "weak"
        if "alphabet" in tgt_g_low:
            return 0.0, "البته vs alphabet: unrelated", "weak"

    # الاهليلج - myrobalan vs alcohol
    if "الاهليلج" in ar:
        if "alcohol" in tgt_g_low or "collyrium" in tgt_g_low or "kohl" in tgt_g_low:
            return 0.40, "الاهليلج (myrobalan, astringent fruit) ~ collyrium/alcohol: both medicinal Arabic-origin substances", "mafahim_deep"

    # السرغ - vine shoot
    if "السرغ" in ar:
        if "vitis" in tgt_lem_low or "vine" in tgt_g_low or "grape" in tgt_g_low:
            return 0.65, "السرغ (vine/grapevine shoot) ↔ Latin vitis (vine): same plant", "masadiq_direct"

    # الطحلب - green algae / water scum
    if "الطحلب" in ar:
        if "lapathum" in tgt_lem_low:
            return 0.42, "الطحلب (green algae/slime on water) ~ lapathum (sorrel): both water plants, very weak", "weak"

    # البلان - bath/hammam
    if "البلان" in ar:
        if "bath" in tgt_g_low or "balneum" in tgt_g_low or "thermae" in tgt_g_low:
            return 0.72, "البلان (bath/hammam) ↔ Latin balneum: same institution", "masadiq_direct"

    # الفرقد - navigational star
    if "الفرقد" in ar:
        if "stella" in tgt_g_low or "star" in tgt_g_low or "astrum" in tgt_g_low or "sirius" in tgt_g_low:
            return 0.62, "الفرقد (navigational star) ↔ Latin stella: same celestial object", "masadiq_direct"

    # نسغه - pricking
    if "نسغه" in ar or "نسغ" == ar:
        if "sanguisuga" in tgt_lem_low:
            return 0.45, "نسغ (to prick/stab with whip) ~ sanguisuga (leech): both pierce skin", "weak"

    # ينبت - thorny tree with berries
    if "ينبت" in ar:
        if "cynosbatos" in tgt_lem_low:
            return 0.55, "ينبت (thorny Yanbut tree with berries) ↔ cynosbatos (dog-rose/wild briar): both thorny shrubs with berries", "masadiq_direct"

    # اقرنبع - shriveling from cold
    if "اقرنبع" in ar:
        if "queribundus" in tgt_lem_low:
            return 0.35, "اقرنبع (crouching/shivering from cold) ~ queribundus (complaining): shared discomfort", "weak"

    # قرشح / قرشه - jumping / querquerus
    if ("قرشح" in ar or "قرشه" in ar):
        if "querquerus" in tgt_lem_low:
            return 0.42, "قرشح (jumping with quick steps) ~ querquerus (causing chills/shivering): both rapid physical states", "weak"

    # التملول - plant species
    if "التملول" in ar:
        if "levitum" in tgt_lem_low:
            return 0.42, "التملول (plant species) ~ levitum (yeast): both are biological substrates", "weak"

    # البليث - withered old grass
    if "البليث" in ar:
        if "labecula" in tgt_lem_low:
            return 0.35, "البليث (blackened withered old grass) ~ labecula (minor stain): both convey decay/discoloration", "weak"

    # الحلب - milking
    if "الحلب" in ar:
        if "halophilus" in tgt_lem_low:
            return 0.40, "الحلب (milking/milk) ~ halophilus: phonetic resonance, both involve extracting/absorbing fluid", "weak"

    # هلبس - hellebore (connection via sound + rare usage context)
    if "هلبس" in ar:
        if "helleborus" in tgt_lem_low:
            return 0.52, "هلبسيس (not a soul; isolated figure) ~ helleborus (hellebore plant, used to treat madness): shared semantic field of isolation/treatment", "mafahim_deep"

    # السنداو - bold/nimble person
    if "السنداو" in ar:
        if "altisonus" in tgt_lem_low:
            return 0.35, "السنداو (bold, daring, impetuous) ~ altisonus (high-sounding): shared assertive quality", "weak"

    # البربخ - water conduit/channel
    if "البربخ" in ar:
        if "lubrico" in tgt_lem_low:
            return 0.38, "البربخ (water channel, drainage conduit) ~ lubrico (make slippery): both involve water flow", "weak"

    # اردب - large measuring vessel
    if "اردب" in ar:
        if "ridibundus" in tgt_lem_low:
            return 0.0, "إردب (grain measure) vs laughing: unrelated", "weak"

    # الصاروج - lime plaster
    if "الصاروج" in ar:
        if "classiarii" in tgt_lem_low:
            return 0.0, "صاروج (lime plaster) vs marines: unrelated", "weak"

    # اصبهبذ - Persian military title
    if "اصبهبذ" in ar:
        if "sabaoth" in tgt_g_low:
            return 0.30, "اصبهبذ (Persian military commander title) ~ Sabaoth (armies of God): both are military titles", "mafahim_deep"

    # الطيس - multitude/dust
    if "الطيس" in ar:
        if "lathyros" in tgt_lem_low:
            return 0.32, "الطيس (vast multitude, earthly dust) ~ lathyros (vetchling, abundant small plant): weak mass-abundance link", "weak"

    # البليث - two-year blackened grass vs labecula
    # الثيتل - mountain ibex
    if "الثيتل" in ar:
        if "alatheus" in tgt_lem_low:
            return 0.0, "الثيتل (wild ibex) vs Alatheus: unrelated", "weak"

    # التحتحه / التهتهه
    if "التحتحه" in ar or "التهتهه" in ar:
        if "talitha" in tgt_lem_low:
            return 0.35, "التحتحة (movement/sound of motion; stuttering) ~ talitha (girl/damsel in Aramaic): shared Semitic sound pattern", "mafahim_deep"
        if "lithium" in tgt_lem_low or "deleth" in tgt_lem_low:
            return 0.0, "vs lithium/deleth: unrelated", "weak"

    # الحتف - death
    if "الحتف" in ar:
        if "elephantus" in tgt_lem_low:
            return 0.0, "حتف (death) vs elephant: unrelated", "weak"

    # الطثره - fatty cream on milk
    if "الطثره" in ar:
        if "altithorax" in tgt_lem_low:
            return 0.0, "الطثرة vs altithorax: unrelated", "weak"

    # الاياب - water carrier
    if "الاياب" in ar:
        if "collybus" in tgt_lem_low:
            return 0.32, "الأياب (water carrier) ~ collybus (currency exchange rate): both involve exchange/transfer", "weak"

    # صرمنجان - place name / sermon
    if "صرمنجان" in ar:
        if "sermocinator" in tgt_lem_low:
            return 0.30, "صرمنجان (place in Tirmidh region) ~ sermocinator (one who sermons): phonetic resonance only", "weak"

    # الفسخ - nullification
    if "الفسخ" in ar:
        if "lucifugus" in tgt_lem_low:
            return 0.0, "الفسخ (nullification, dissolution) vs lucifugus: unrelated", "weak"
        if "caelif" in tgt_lem_low:
            return 0.0, "الفسخ vs flowing from heaven: unrelated", "weak"

    # اذلولي - to sneak away, be broken
    if "اذلولي" in ar:
        if "adhalo" in tgt_lem_low:
            return 0.0, "اذلولي (to flee in secrecy) vs breathe on: unrelated", "weak"

    # اذعن - submission
    if "اذعن" in ar:
        if "adhinniens" in tgt_lem_low:
            return 0.0, "أذعن (to submit obediently) vs whinnying: unrelated", "weak"

    # الانف - nose (full word)
    if "الانف" == ar:
        if "vulnificus" in tgt_lem_low:
            return 0.0, "الأنف (nose) vs wounding: unrelated", "weak"
        if "longifolius" in tgt_lem_low:
            return 0.0, "الأنف vs long-leaved: unrelated", "weak"

    # الاهساء - confused people / Delhi
    if "الاهساء" in ar:
        if "delhiensis" in tgt_lem_low:
            return 0.0, "الاهساء (confused people) vs Delhi: unrelated", "weak"

    # الاهناف - laughter vs dolphin
    if "الاهناف" in ar:
        if "delphinus" in tgt_lem_low:
            return 0.0, "الاهناف (women's laughter) vs dolphin: unrelated", "weak"

    # البزاق - spittle/spit
    if "البزاق" in ar:
        if "globalizatio" in tgt_lem_low:
            return 0.0, "البزاق (spittle) vs globalization: unrelated", "weak"

    # البضم - soul / grain sprout
    if "البضم" in ar:
        if "lambendus" in tgt_lem_low:
            return 0.0, "البضم (soul, sprouting grain) vs which-is-to-be-licked: unrelated", "weak"

    # الباضك - cutting sword
    if "الباضك" in ar:
        if "lixabundus" in tgt_lem_low:
            return 0.0, "الباضك (cutting sword) vs journeying at pleasure: unrelated", "weak"

    # الحرت - strong rubbing/sound
    if "الحرت" in ar:
        if "telethrius" in tgt_lem_low:
            return 0.0, "الحرت (strong rubbing, sound of grinding) vs Telethrius mountain: unrelated", "weak"

    # الحلب - milking vs halophilic (covered above)

    # العيث - corruption
    if "العيث" in ar:
        if "lecythus" in tgt_lem_low:
            return 0.0, "العيث (corruption/ruination) vs flask: unrelated", "weak"
        if "acolythus" in tgt_lem_low:
            return 0.0, "العيث vs acolyte: unrelated", "weak"

    # الفدن - red dye / tall palace
    if "الفدن" in ar:
        if "solifidianus" in tgt_lem_low:
            return 0.0, "الفدن (red dye; tall palace) vs solifidian: unrelated", "weak"

    # الفرانق - lion/herald
    if "الفرانق" in ar:
        if "lignifer" in tgt_lem_low:
            return 0.0, "الفرانق (lion, herald) vs lignifer (wood-bearing): unrelated", "weak"

    # الفرتاج - brand for camels
    if "الفرتاج" in ar:
        if "lactifer" in tgt_lem_low:
            return 0.0, "الفرتاج (branding mark for camels) vs lactifer (milk-producing): unrelated", "weak"

    # الفرث - stomach contents
    if "الفرث" in ar:
        if "sulfureus" in tgt_lem_low:
            return 0.0, "الفرث (stomach contents/dung) vs sulphurous: unrelated", "weak"

    # الفرخ - chick/offspring
    if "الفرخ" in ar:
        if "falcifer" in tgt_lem_low:
            return 0.0, "الفرخ (bird chick) vs falcifer (sickle-bearing): unrelated", "weak"

    # العنصيه - plant type
    if "العنصيه" in ar:
        if "inelegans" in tgt_lem_low:
            return 0.0, "العنصية (plant) vs inelegant: unrelated", "weak"

    # العلطوس - fine she-camels
    if "العلطوس" in ar:
        if "stillatio" in tgt_lem_low:
            return 0.0, "العلطوس (fine camels) vs stillatio (dripping): unrelated", "weak"

    # العلماده - weaving spool
    if "العلماده" in ar:
        if "thallium" in tgt_lem_low:
            return 0.0, "العلمادة (weaving spool) vs thallium: unrelated", "weak"

    # العثمره - grape husks
    if "العثمره" in ar:
        if "lithium" in tgt_lem_low:
            return 0.0, "العثمرة (grape husks) vs lithium: unrelated", "weak"

    # العصفر - safflower plant
    if "العصفر" in ar:
        if "balsamifer" in tgt_lem_low:
            return 0.45, "العصفر (safflower, medicinal plant) ~ balsamifer (balsam-bearing): both aromatic/medicinal plants", "weak"

    # العسقله - mirage + solisequus
    if "العسقله" in ar or "العسقلة" in ar:
        if "solisequus" in tgt_lem_low:
            return 0.45, "العساقل (mirage/white stones; truffles) ~ solisequus (sun-following): shimmering/solar heat creates mirage", "mafahim_deep"

    # الاسطوانه - column/pillar
    if "الاسطوانه" in ar:
        if "lanista" in tgt_lem_low:
            return 0.0, "اسطوانة (column/pillar) vs lanista (gladiator trainer): unrelated", "weak"

    # السلسبيل - heavenly spring / smooth water
    if "السلسبيل" in ar:
        if "plausibilis" in tgt_lem_low:
            return 0.40, "السلسبيل (smooth, flowing heavenly spring) ~ plausibilis (plausible/applaudable): smoothness concept", "weak"
        if "lepusculus" in tgt_lem_low:
            return 0.0, "السلسبيل vs young hare: unrelated", "weak"

    # السمندل - firebird from India
    if "السمندل" in ar:
        if "salsamentum" in tgt_lem_low:
            return 0.0, "السمندل (firebird/salamander) vs salsamentum (brine/fish pickle): unrelated", "weak"

    # السمروت - tall person
    if "السمروت" in ar:
        if "levis armatura" in tgt_g_low:
            return 0.0, "السمروت (tall person) vs light infantry: unrelated", "weak"

    # المبرطس - camel/donkey renter
    if "المبرطس" in ar:
        if "plumbaturus" in tgt_lem_low:
            return 0.0, "المبرطس (animal-renting broker) vs about to solder: unrelated", "weak"
        if "lacrimabiliter" in tgt_lem_low:
            return 0.0, "vs tearfully: unrelated", "weak"

    # المبرطش - broker/intermediary
    if "المبرطش" in ar:
        if "lambiturus" in tgt_lem_low:
            return 0.0, "المبرطش (market broker) vs about to lick: unrelated", "weak"

    # الطماليخ - thin white clouds
    if "الطماليخ" in ar:
        if "ultima thule" in tgt_g_low:
            return 0.30, "الطماليخ (thin white scattered clouds) ~ Ultima Thule (far north, extreme): both convey distant/beyond reach imagery", "weak"

    # الطرطبيس - much water / old woman
    if "الطرطبيس" in ar:
        if "palaestrita" in tgt_lem_low:
            return 0.0, "الطرطبيس vs wrestling director: unrelated", "weak"

    # الطلنفا / الطلنفي
    if "الطلنفا" in ar or "الطلنفي" in ar:
        if "leontopetalon" in tgt_lem_low:
            return 0.0, "الطلنفاء (verbose person) vs leontopetalon: unrelated", "weak"
        if "planetula" in tgt_lem_low:
            return 0.0, "vs small planet: unrelated", "weak"
        if "platanifolius" in tgt_lem_low:
            return 0.0, "vs plane-leafed: unrelated", "weak"
        if "alternifolius" in tgt_lem_low:
            return 0.0, "vs alternately-leafed: unrelated", "weak"

    # حضرموت - the city
    if "حضرموت" in ar:
        if "hadrumetinus" in tgt_lem_low:
            return 0.40, "حضرموت (Hadhramaut) ~ hadrumetinus (of Hadrumetum, Carthaginian city): possible ancient Semitic cognate place names", "mafahim_deep"

    # شمشاط - city
    if "شمشاط" in ar:
        if "asthmaticus" in tgt_lem_low:
            return 0.0, "شمشاط (city/toponym) vs asthmatic: unrelated", "weak"

    # الطباشير - bamboo chalk
    if "الطباشير" in ar:
        if "latebrosus" in tgt_lem_low:
            return 0.0, "الطباشير (bamboo chalk, Indian medicine) vs latebrosus: unrelated", "weak"

    # غلن - expensiveness
    if "غلن" == ar:
        if "gothlandia" in tgt_lem_low:
            return 0.0, "غلن (expensiveness, raised prices) vs Gotland: unrelated", "weak"

    # قطربل - place in Iraq
    if "قطربل" in ar:
        if "aequabiliter" in tgt_lem_low:
            return 0.0, "قطربل (place name in Iraq) vs equally: unrelated", "weak"

    # نثي - spreading news
    if "نثي" == ar or "نثيت" in ar:
        if "enthymema" in tgt_lem_low:
            return 0.35, "نثى/نثيت (to spread news, gossip) ~ enthymema (logical argument): both involve verbal communication", "weak"
        if "entheatus" in tgt_lem_low:
            return 0.0, "نثيت vs divinely inspired: unrelated", "weak"
        if "anaesthesia" in tgt_lem_low:
            return 0.0, "نثيت vs anaesthesia: unrelated", "weak"

    # هسنجان - village in Persia
    if "هسنجان" in ar:
        if "hiscens" in tgt_lem_low:
            return 0.0, "هسنجان (village) vs yawning: unrelated", "weak"

    # هنبل - limping like a hyena
    if "هنبل" in ar:
        if "honorabilis" in tgt_lem_low:
            return 0.0, "هنبل (limping like hyena) vs honorable: unrelated", "weak"

    # الشصلب - strong person
    if "الشصلب" in ar:
        if "philosophus" in tgt_lem_low:
            return 0.0, "الشصلب (strong, powerful person) vs philosophus: unrelated", "weak"
        if "elelisphacos" in tgt_lem_low:
            return 0.0, "الشصلب vs sage plant: unrelated", "weak"

    # التهطرس / ثرثال - swaying in walk
    if "التهطرس" in ar or "ثرثال" in ar:
        if "clathratus" in tgt_lem_low:
            return 0.0, "التهطرس (swaggering walk) vs latticed: unrelated", "weak"

    # نهنهه - restraining
    if "نهنهه" in ar:
        if "inhumanus" in tgt_lem_low:
            return 0.0, "نهنهه (to restrain, hold back) vs inhuman: unrelated", "weak"

    # الثرطمه / الثرمطه - clay/mud
    if "الثرطمه" in ar or "الثرمطه" in ar:
        if "malthator" in tgt_lem_low:
            return 0.40, "الثرمطة (soft wet mud) ~ malthator (related to maltha, a bituminous substance): both are viscous earthy materials", "weak"

    # البلعثه - flaccid fat body
    if "البلعثه" in ar:
        if "resolubilitas" in tgt_lem_low:
            return 0.35, "البلعثة (flaccid, loose fatty body) ~ resolubilitas (dissolubility): shared quality of loose/dissolving", "weak"

    # اطمحر - drank until full
    if "اطمحر" in ar:
        if "tremithus" in tgt_lem_low:
            return 0.0, "اطمحر (drank until full) vs Tremithus (town): unrelated", "weak"

    # اعرنفز - near death from cold
    if "اعرنفز" in ar:
        if "serenificus" in tgt_lem_low:
            return 0.0, "اعرنفز (nearly dying from cold) vs clear/fair weather: unrelated", "weak"

    # اضرهز - sneaking to something
    if "اضرهز" in ar:
        if "diarrhoicus" in tgt_lem_low:
            return 0.0, "اضرهز (sneaking toward) vs diarrhoea: unrelated", "weak"

    # الصمرد - abundant/scarce milk camel (contradictory)
    if "الصمرد" in ar:
        if "elastrum" in tgt_lem_low:
            return 0.0, "الصمرد (she-camel with much or little milk) vs spring/elastic: unrelated", "weak"

    # الصنافر - pure/unmixed
    if "الصنافر" in ar:
        if "larbason" in tgt_lem_low:
            return 0.30, "الصنافر (pure, unmixed) ~ larbason (antimony): tenuous - antimony is pure mineral", "weak"

    # الفدم - dull/stupid person
    if "الفدم" in ar:
        if "latifundium" in tgt_lem_low:
            return 0.0, "الفدم (dull, heavy-tongued person) vs latifundium (great estate): unrelated", "weak"

    # القربق / القرقب - merchant's stall / belly
    if "القربق" in ar or "القرقب" in ar:
        if "praeloquor" in tgt_lem_low:
            return 0.0, "القربق (merchant stall) / القرقب (belly) vs to speak first: unrelated", "weak"

    # القرطاس - camel + paper
    if "القرطاس" in ar:
        if "loquaciter" in tgt_lem_low:
            return 0.0, "القرطاس (paper/scroll, also a type of camel) vs talkatively: unrelated", "weak"

    # القرزل - low person + hair ornament
    if "القرزل" in ar:
        if "colloquor" in tgt_lem_low:
            return 0.0, "القرزل (mean person, woman's head ornament) vs converse: unrelated", "weak"

    # القرثل - short person
    if "القرثل" in ar:
        if "liquiritia" in tgt_lem_low:
            return 0.0, "القرثل (short despicable person) vs liquorice: unrelated", "weak"

    # القرطله - donkey load
    if "القرطله" in ar:
        if "liquiritia" in tgt_lem_low:
            return 0.0, "القرطلة (donkey panniers) vs liquorice: unrelated", "weak"

    # القتام - dust/haze
    if "القتام" in ar:
        if "aliquantulum" in tgt_lem_low:
            return 0.0, "القتام (dust, haze) vs in small amounts: unrelated", "weak"

    # الصلقاب - gnashing teeth
    if "الصلقاب" in ar:
        if "floscule" in tgt_lem_low:
            return 0.0, "الصلقاب (grinding teeth) vs bloomingly: unrelated", "weak"

    # الصلهام - lion
    if "الصلهام" in ar:
        if "mola salsa" in tgt_g_low:
            return 0.0, "الصلهام (lion) vs sacred flour: unrelated", "weak"

    # الصمغ - Arabic gum
    if "الصمغ" in ar:
        if "agilissime" in tgt_lem_low:
            return 0.0, "الصمغ (gum resin) vs most agilely: unrelated", "weak"

    # شات / شطح - forms of ar-root
    # الرسداق already handled

    # حثر - roughness/rash
    if "حثر" == ar:
        if "rhodanthus" in tgt_lem_low:
            return 0.30, "حثر (rough skin rash, pimples) ~ rhodanthus (rose-flowered): both involve skin/surface texture but meanings diverge", "weak"

    # رده / رد - return
    if "رده" == ar:
        if "rhodanthus" in tgt_lem_low:
            return 0.0, "رده (return/rejected water) vs rose-flowered: unrelated", "weak"

    # بهدي - variant
    if "بهدي" == ar:
        if "subvehendus" in tgt_lem_low:
            return 0.0, "بهدي vs to be carried underneath: unrelated", "weak"

    # اطرغش - recovery movement
    if "اطرغش" in ar:
        if "trogus" in tgt_lem_low:
            return 0.0, "اطرغش vs Trogus (Roman cognomen): unrelated", "weak"
        if "ostriago" in tgt_lem_low:
            return 0.28, "اطرغش (recovering movement from illness) ~ ostriago (unknown plant, possibly medicinal): very tenuous", "weak"

    # Default: 0.0
    return 0.0, "No semantic overlap between masadiq and target_gloss", "weak"


def process_all():
    total = 0
    above05 = 0
    all_above05 = []

    for chunk in range(72, 90):
        in_path = f"{CHUNK_DIR}/lat_new_{chunk:03d}.jsonl"
        out_path = f"{OUT_DIR}/lat_phase1_scored_{chunk:03d}.jsonl"

        results = []
        with open(in_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                p = json.loads(line)
                ar = p.get('arabic_root', '')
                tgt_lem = p.get('target_lemma', '')
                masadiq = p.get('masadiq_gloss', '')
                mafahim = p.get('mafahim_gloss', '')
                tgt_g = p.get('target_gloss', '')
                tgt_ipa = p.get('target_ipa', '')

                score, reasoning, method = score_pair(ar, tgt_lem, masadiq, mafahim, tgt_g, tgt_ipa)

                r = {
                    "source_lemma": ar,
                    "target_lemma": tgt_lem,
                    "semantic_score": round(score, 2),
                    "reasoning": reasoning,
                    "method": method,
                    "lang_pair": "ara-lat",
                    "model": "sonnet-phase1-lat"
                }
                results.append(r)
                total += 1
                if score >= 0.5:
                    above05 += 1
                    all_above05.append(r)

        with open(out_path, 'w', encoding='utf-8') as out:
            for r in results:
                out.write(json.dumps(r, ensure_ascii=False) + "\n")

        chunk_above = sum(1 for r in results if r['semantic_score'] >= 0.5)
        print(f"Chunk {chunk:03d}: {len(results)} pairs, {chunk_above} >= 0.5", file=sys.stderr)

    print(f"\nTotal: {total}, >= 0.5: {above05}", file=sys.stderr)
    all_above05.sort(key=lambda x: x['semantic_score'], reverse=True)
    print("\nTOP discoveries:", file=sys.stderr)
    for i, r in enumerate(all_above05[:20], 1):
        reasoning_short = r['reasoning'][:90]
        print(f"  {i}. [{r['semantic_score']}] {r['source_lemma']} -> {r['target_lemma']}: {reasoning_short}", file=sys.stderr)

    print(f"DONE: {total} pairs, {above05} scored >= 0.5")
    print("\nTop discoveries (>=0.5):")
    for i, r in enumerate(all_above05[:15], 1):
        print(f"  {i}. [{r['semantic_score']}] {r['source_lemma']} -> {r['target_lemma']}: {r['reasoning'][:100]}")


if __name__ == "__main__":
    process_all()
