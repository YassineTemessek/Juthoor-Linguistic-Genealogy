#!/usr/bin/env python3
"""
Eye 2 Phase 1 scorer for Arabic-Latin chunks 126-141.
MASADIQ-FIRST methodology: score semantic overlap between
masadiq_gloss (Arabic dictionary definition) and target_gloss (Latin).
"""

import json
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

INPUT_DIR = "C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_phase1_lat_chunks"
OUTPUT_DIR = "C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_results"


def read_chunk(n):
    path = f"{INPUT_DIR}/lat_new_{n}.jsonl"
    pairs = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))
    return pairs


# =====================================================================
# SEMANTIC CONCEPT CLUSTERS
# Each cluster: (concept_label, arabic_keywords, latin_keywords, score_if_match)
# arabic_keywords checked against masadiq_gloss (Arabic text)
# latin_keywords checked against target_gloss (English)
# =====================================================================

# Arabic semantic keywords (to detect in masadiq_gloss Arabic text)
AR_CONCEPTS = {
    # Body
    "soul_spirit": ["روح", "نفس", "نفسه", "أرواح"],
    "heart": ["قلب", "قلوب", "فؤاد"],
    "head": ["رأس", "رؤوس"],
    "eye": ["عين", "عيون"],
    "ear": ["أذن", "آذان"],
    "nose": ["أنف"],
    "hand": ["يد", "يدين", "أيدي"],
    "foot": ["قدم", "رجل", "رجله"],
    "bone": ["عظم", "عظام"],
    "skin": ["جلد", "جلده"],
    "blood": ["دم", "دماء"],
    "nerve_sinew": ["عصب", "عصبة"],
    "belly_stomach": ["بطن", "معدة"],
    "back_spine": ["ظهر", "فقار", "فقرة"],
    "neck": ["عنق", "رقبة"],
    "mouth": ["فم", "أفواه", "فاه"],
    "tongue": ["لسان", "ألسنة"],
    "tooth": ["سن", "أسنان"],
    "hair": ["شعر", "شعره"],
    "grey_hair": ["شيب", "أشيب", "شيبة"],
    "beard": ["لحية"],
    "bald": ["صلع", "أصلع"],
    "ankle": ["كعب", "كعبين"],
    "finger": ["إصبع", "أصابع"],
    # Animals
    "dog": ["كلب", "كلاب"],
    "horse": ["فرس", "خيل"],
    "camel": ["ناقة", "جمل", "إبل"],
    "sheep": ["غنم", "شاة", "ضأن", "نعجة"],
    "cow": ["بقر", "بقرة"],
    "lion": ["أسد", "ليث"],
    "wolf": ["ذئب", "ذئاب"],
    "bird": ["طير", "طائر", "أطيار"],
    "fish": ["سمك", "سمكة", "حوت"],
    "snake": ["حية", "أفعى", "ثعبان"],
    "crane_bird": ["الكُرْكيّ", "كرك"],
    # Nature
    "water": ["ماء", "مياه"],
    "river": ["نهر", "أنهار", "نهره"],
    "rain": ["مطر", "أمطار", "غيث"],
    "sea": ["بحر", "أبحار"],
    "mountain": ["جبل", "جبال", "هضبة"],
    "fire": ["نار", "حرق"],
    "wind_breath": ["ريح", "رياح", "هواء", "نفخ"],
    "tree": ["شجر", "شجرة"],
    "palm_tree": ["نخل", "نخلة"],
    "grass": ["عشب", "كلأ", "نبت"],
    "earth_ground": ["أرض", "تراب"],
    "star": ["نجم", "نجوم", "كواكب"],
    "sun": ["شمس"],
    "moon": ["قمر"],
    "sky": ["سماء"],
    "sand": ["رمل", "رمله"],
    "stone": ["حجر", "صخر"],
    "turbid_water": ["كَدِر", "كدره", "رنق", "عكر"],
    "mud": ["طين", "وحل", "رنوق"],
    # Food & substances
    "oil": ["زيت", "زيته"],
    "fat_butter": ["سمن", "دسم", "شحم"],
    "honey": ["عسل"],
    "milk": ["لبن", "لبنه"],
    "bread": ["خبز"],
    "wine": ["خمر"],
    "salt": ["ملح"],
    "flour": ["دقيق"],
    "meat": ["لحم"],
    "gum_resin": ["صمغ", "راتنج"],
    "wax": ["شمع"],
    "broth": ["مرق", "مرقة"],
    "fragrance_perfume": ["عطر", "طيب", "ريح طيبة"],
    "dung_manure": ["روث", "روثه", "بعر", "خثي"],
    "senna_plant": ["سنا"],
    "acacia": ["طلح"],
    "pine": ["صنوبر"],
    "grapevine": ["كرم", "العنب"],
    "mushroom": ["فطر"],
    # Actions
    "hear": ["سمع", "يسمع", "سمعه", "استمع"],
    "see_look": ["نظر", "ينظر", "أبصر", "رأى", "رؤية"],
    "speak": ["كلم", "تكلم", "قول", "قال"],
    "write": ["كتب", "يكتب"],
    "read": ["قرأ"],
    "pray": ["صلى", "صلاة", "يصلي"],
    "fast": ["صوم", "صام"],
    "vow": ["نذر", "يُنذر"],
    "curse": ["لعن", "يلعن", "لعنه"],
    "heal": ["شفى", "يشفي", "شفاء"],
    "kill_slaughter": ["ذبح", "نحر", "قتل"],
    "grind": ["طحن", "جشّ", "سحق"],
    "cut": ["قطع", "قطّع"],
    "fry": ["قلى", "يقلي"],
    "skin_flay": ["سلخ", "يسلخ"],
    "boil_scald": ["سلق", "سلقه"],
    "drink": ["شرب", "يشرب"],
    "eat": ["أكل", "يأكل", "طعام"],
    "lick": ["لعق", "يلعق"],
    "swallow": ["ابتلع", "نغب", "جرع"],
    "pluck_pick": ["قطف", "يقطف"],
    "gather": ["جمع", "لقط"],
    "carry": ["حمل", "يحمل"],
    "seek": ["طلب", "يطلب", "روم", "رام"],
    "flee": ["فرّ", "هرب"],
    "play": ["لعب", "يلعب"],
    "sneeze": ["عطس", "يعطس", "عطسة"],
    "blow": ["نفخ", "ينفخ"],
    "walk_march": ["مشى", "يمشي"],
    "descend": ["نزل", "ينزل", "هبط"],
    "rise_high": ["سما", "يسمو", "ارتفع", "علا"],
    "split_crack": ["شق", "انشق", "انفلق"],
    "press_squeeze": ["عصر", "ضغط"],
    "crush": ["سحق", "رهك"],
    "uproot": ["اقتلع", "قلع"],
    "spread_publish": ["نشر", "ينشر"],
    # Concepts / abstract
    "peace": ["صلح", "سلم", "سلام"],
    "knowledge": ["عرف", "معرفة", "علم"],
    "reason_intellect": ["عقل", "ذكاء"],
    "understand": ["فهم", "يفهم", "إدراك"],
    "think": ["فكّر", "تفكير", "يفكر"],
    "soul_spirit2": ["روح", "أرواح"],
    "light_flash": ["وميض", "برق", "سنا"],
    "truth_right": ["حق", "صواب"],
    "power_authority": ["سلطة", "سلطان", "قوة", "قدرة"],
    "generosity": ["كرم", "جود", "سخاء"],
    "poverty": ["فقر", "مسكين", "فقيره"],
    "greed": ["طمع", "جشع"],
    "fear": ["خوف", "فزع", "هلع", "روع"],
    "joy": ["فرح", "سرور", "مرح"],
    "sadness": ["حزن", "حزنه", "غم"],
    "love": ["حب", "عشق", "ودّ"],
    "desire_longing": ["شوق", "شوقه"],
    "hatred": ["كره", "بغض", "مقت"],
    "patience": ["صبر"],
    "pride": ["عزة", "فخر"],
    "arrogance": ["تكبر", "غرور"],
    "asceticism": ["زهد", "زاهد"],
    "purity": ["طهر", "طهارة", "نقاء"],
    "truth_honest": ["صدق", "صادق"],
    "lie": ["كذب"],
    "change_other": ["غير", "آخر"],
    "isolation": ["عزل", "اعتزل"],
    "attribute": ["عزا", "نسب"],
    "vow_promise": ["نذر"],
    "lineage_genealogy": ["نسب", "نسبه", "سلسلة"],
    "contract_knot": ["عقد", "عقده"],
    "justice": ["قسط", "عدل"],
    "freedom": ["حرية", "طلق"],
    "slavery": ["عبد", "عبودية"],
    # Physical properties
    "sharp_thin": ["رهف", "رقيق", "حاد"],
    "hard_solid": ["صلب", "صلابة", "قاسي"],
    "soft_flexible": ["لين", "مرن"],
    "smooth_easy": ["سلس", "سهل"],
    "tall_long": ["طول", "طويل"],
    "short": ["قصر", "قصير"],
    "bitter": ["مرارة", "مرّ", "مرير"],
    "sweet": ["حلو", "حلاوة"],
    "hot": ["حار", "سخن"],
    "cold": ["بارد", "برود"],
    "dark": ["ظلام", "غامض", "عتمة"],
    "bright_light": ["نور", "ضوء", "نضارة"],
    "reddish": ["أحمر", "أصهب", "صهبة"],
    "turbid_murky": ["رنق", "كَدِر", "عكر"],
    # Religious
    "prophet": ["نبي", "أنبياء"],
    "god_divine": ["الله", "إله", "رب"],
    "holy_sacred": ["مقدس", "قدس"],
    "crucifixion": ["صلب", "صلبوه"],
    "prayer": ["صلاة", "دعاء"],
    "church_priest": ["قس", "كنيسة"],
    "passover": ["فصح", "فصيح"],
    # Objects
    "pen_reed": ["قلم", "قصبة"],
    "sword": ["سيف", "سيفه"],
    "tablet_board": ["لوح", "ألواح"],
    "rope": ["حبل", "طنب", "وتر"],
    "ladder": ["سلّم", "درج"],
    "necklace_collar": ["طوق", "قلادة"],
    "throne_chair": ["كرسي", "عرش"],
    "treasure": ["كنز", "كنوزه"],
    "candle_wax": ["شمع", "شمعة"],
    "cymbal": ["صنج", "صنجات"],
    "nail_peg": ["مسمار", "وتد"],
    "ring": ["خاتم", "حلقة"],
    "vessel_jar": ["جرة", "إناء", "وعاء"],
    "pledge": ["رهن", "ضمان"],
    # People/social
    "elder_old": ["شيخ", "مسن", "عجوز"],
    "old_age": ["شيخوخة", "كبر", "هرم"],
    "prophet2": ["نبي", "رسول"],
    "king": ["ملك", "ملوك", "رئيس"],
    "merchant": ["تاجر", "سوق"],
    "goods_merchandise": ["بضاعة", "سلع", "بضائع", "متاع"],
    "predecessor": ["سلف", "أسلاف"],
    "lineage": ["نسب"],
    "vow_promise2": ["نذر", "عهد"],
    # Medicine / body states
    "thirst": ["عطش", "ظمأ"],
    "bitter2": ["مر", "مرارة"],
    "deaf": ["أصم", "صمم", "أصلخ"],
    "deaf2": ["صلخ", "صمم"],
    "bald2": ["صلع", "أقرع"],
    "barren_infertile": ["عقم", "عاقر", "عقر"],
    "wound": ["جرح", "كلم"],
    "phlebotomy": ["فصد"],
    "palsy": ["فالج", "شلل"],
    # Language
    "language_speech": ["لغة", "لسان", "سان"],
    "dialect": ["لهجة"],
    "utterance": ["لفظ", "لفظه"],
    # Geography
    "rome_romans": ["روم", "الروم"],
    "egypt": ["مصر"],
    "mars_planet": ["مريخ"],
}

# Latin semantic keywords (to detect in target_gloss English text)
LAT_CONCEPTS = {
    "soul_spirit": ["soul", "spirit", "anima", "animus", "spiritus"],
    "heart": ["heart", "cor "],
    "head": ["head"],
    "eye": ["eye", "eyes"],
    "ear": ["ear", "auris"],
    "nose": ["nose"],
    "hand": ["hand"],
    "foot": ["foot", "feet"],
    "bone": ["bone", "bones"],
    "skin": ["skin", "hide"],
    "blood": ["blood"],
    "nerve_sinew": ["nerve", "sinew", "tendon"],
    "belly_stomach": ["belly", "abdomen", "stomach"],
    "back_spine": ["spine", "backbone", "vertebra"],
    "neck": ["neck"],
    "mouth": ["mouth"],
    "tongue": ["tongue"],
    "tooth": ["tooth", "teeth"],
    "hair": ["hair"],
    "grey_hair": ["grey hair", "gray hair", "white hair"],
    "beard": ["beard"],
    "bald": ["bald", "baldness", "calvit"],
    "ankle": ["ankle"],
    "dog": ["dog", "hound", "canine"],
    "horse": ["horse"],
    "camel": ["camel"],
    "sheep": ["sheep", "flock", "lamb"],
    "cow": ["cow", "cattle", "bull"],
    "lion": ["lion"],
    "wolf": ["wolf"],
    "bird": ["bird", "fowl", "avian"],
    "fish": ["fish"],
    "snake": ["snake", "serpent"],
    "crane_bird": ["crane"],
    "water": ["water"],
    "river": ["river", "stream", "fluvius"],
    "rain": ["rain", "shower", "rainfall"],
    "sea": ["sea", "ocean"],
    "mountain": ["mountain", "hill", "peak"],
    "fire": ["fire", "flame", "burn"],
    "wind_breath": ["wind", "breeze", "breath", "blow"],
    "tree": ["tree"],
    "palm_tree": ["palm", "date"],
    "grass": ["grass", "herbage", "herb"],
    "earth_ground": ["earth", "ground", "soil"],
    "star": ["star", "stellar", "astro"],
    "sun": ["sun", "solar"],
    "moon": ["moon", "lunar"],
    "sky": ["sky", "heaven"],
    "sand": ["sand"],
    "stone": ["stone", "rock"],
    "turbid_water": ["turbid", "murky", "muddy"],
    "mud": ["mud", "silt", "sediment"],
    "oil": ["oil", "olive"],
    "fat_butter": ["fat", "butter", "ghee", "lard", "grease"],
    "honey": ["honey"],
    "milk": ["milk"],
    "bread": ["bread"],
    "wine": ["wine", "grape"],
    "salt": ["salt"],
    "flour": ["flour"],
    "meat": ["meat", "flesh"],
    "gum_resin": ["gum", "resin", "latex"],
    "wax": ["wax", "candle"],
    "broth": ["broth", "soup", "stock"],
    "fragrance_perfume": ["perfume", "fragrance", "scent", "aroma", "unguent"],
    "dung_manure": ["dung", "manure", "excrement", "feces", "fimus", "stercus"],
    "senna_plant": ["senna"],
    "acacia": ["acacia"],
    "pine": ["pine", "fir"],
    "grapevine": ["grapevine", "vine", "vinea"],
    "mushroom": ["mushroom", "fungus"],
    "hear": ["hear", "listen", "audio"],
    "see_look": ["see", "look", "sight", "vision", "observe", "behold"],
    "speak": ["speak", "say", "utter"],
    "write": ["write", "inscribe"],
    "read": ["read"],
    "pray": ["pray", "prayer", "supplicat"],
    "fast": ["fast", "fasting", "abstain"],
    "vow": ["vow", "votum"],
    "curse": ["curse", "damn", "imprecation", "malediction"],
    "heal": ["heal", "cure", "remedy", "medicine"],
    "kill_slaughter": ["kill", "slaughter", "slay"],
    "grind": ["grind", "mill", "crush"],
    "cut": ["cut", "sever", "incise", "section"],
    "fry": ["fry", "roast", "parch"],
    "skin_flay": ["skin", "flay", "peel"],
    "boil_scald": ["boil", "scald", "cook"],
    "drink": ["drink", "drinking", "drain"],
    "eat": ["eat", "consume", "food"],
    "lick": ["lick"],
    "swallow": ["swallow", "gulp", "devour"],
    "pluck_pick": ["pick", "pluck", "gather fruit"],
    "gather": ["gather", "collect", "pick up"],
    "carry": ["carry", "bear", "convey"],
    "seek": ["seek", "search", "request", "demand"],
    "flee": ["flee", "escape", "run away"],
    "play": ["play", "game", "sport", "fun"],
    "sneeze": ["sneeze"],
    "blow": ["blow", "inflate", "breathe out"],
    "walk_march": ["walk", "march", "go"],
    "descend": ["descend", "dismount", "go down"],
    "rise_high": ["rise", "high", "lofty", "ascend", "exalt"],
    "split_crack": ["split", "crack", "cleave"],
    "press_squeeze": ["press", "squeeze", "extract", "compress"],
    "crush": ["crush", "grind", "pulverize"],
    "uproot": ["uproot", "extract", "tear out"],
    "spread_publish": ["spread", "publish", "disseminate"],
    "peace": ["peace", "reconciliation", "concord"],
    "knowledge": ["know", "knowledge", "recognize"],
    "reason_intellect": ["reason", "intellect", "rational", "mind"],
    "understand": ["understand", "comprehend"],
    "think": ["think", "thought", "reflect", "meditate"],
    "light_flash": ["flash", "lightning", "light", "gleam"],
    "truth_right": ["truth", "right", "just"],
    "power_authority": ["power", "authority", "dominion"],
    "generosity": ["generosity", "liberal"],
    "poverty": ["poverty", "poor"],
    "greed": ["greed", "avarice", "covet"],
    "fear": ["fear", "terror", "alarm", "fright"],
    "joy": ["joy", "merry", "happy", "gladness"],
    "sadness": ["sad", "grief", "sorrow"],
    "love": ["love", "passion"],
    "desire_longing": ["longing", "desire", "yearn"],
    "hatred": ["hate", "hatred"],
    "patience": ["patience", "endure"],
    "arrogance": ["arrogance", "pride", "haughty"],
    "asceticism": ["ascetic", "abstinence", "frugal"],
    "purity": ["pure", "clean", "purity"],
    "truth_honest": ["honest", "truthful"],
    "lie": ["lie", "deceive", "falsehood"],
    "change_other": ["other", "different", "change"],
    "isolation": ["isolat", "separate", "segregate"],
    "contract_knot": ["contract", "knot", "bind", "tie"],
    "justice": ["justice", "equity", "just"],
    "freedom": ["free", "freedom", "libert"],
    "sharp_thin": ["sharp", "thin", "fine", "keen"],
    "hard_solid": ["hard", "solid", "rigid"],
    "soft_flexible": ["soft", "flexible", "pliable"],
    "smooth_easy": ["smooth", "easy", "flowing"],
    "tall_long": ["long", "tall", "length"],
    "short": ["short", "brief"],
    "bitter": ["bitter", "bitterness"],
    "sweet": ["sweet", "sweetness"],
    "hot": ["hot", "warm", "heat"],
    "cold": ["cold", "cool"],
    "dark": ["dark", "obscure", "dim"],
    "bright_light": ["bright", "brilliant", "shine"],
    "reddish": ["red", "reddish", "auburn"],
    "turbid_murky": ["turbid", "murky", "muddy", "cloudy"],
    "prophet": ["prophet"],
    "god_divine": ["god", "divine", "deity"],
    "holy_sacred": ["sacred", "holy"],
    "crucifixion": ["cross", "crucif"],
    "prayer": ["prayer", "pray"],
    "church_priest": ["priest", "bishop", "clergy"],
    "passover": ["passover", "easter", "pesach"],
    "pen_reed": ["pen", "reed", "stylus"],
    "sword": ["sword", "blade"],
    "tablet_board": ["tablet", "board", "plank"],
    "rope": ["rope", "cord", "string"],
    "ladder": ["ladder", "stair", "step"],
    "necklace_collar": ["necklace", "collar", "torque"],
    "throne_chair": ["throne", "chair", "seat"],
    "treasure": ["treasure", "hoard"],
    "candle_wax": ["wax", "candle"],
    "cymbal": ["cymbal", "timbrel", "bell"],
    "nail_peg": ["nail", "peg", "spike"],
    "ring": ["ring", "circle"],
    "vessel_jar": ["vessel", "jar", "pot", "amphora"],
    "pledge": ["pledge", "deposit", "security", "pawn"],
    "elder_old": ["elder", "old man", "elderly"],
    "old_age": ["old age", "aging", "grey"],
    "king": ["king", "ruler", "rex"],
    "merchant": ["merchant", "trade", "market"],
    "goods_merchandise": ["merchandise", "goods", "commodity", "wares"],
    "predecessor": ["ancestor", "predecessor", "forebear"],
    "lineage": ["lineage", "genealogy", "descent", "family"],
    "thirst": ["thirst", "thirsty"],
    "deaf": ["deaf", "deafness"],
    "barren_infertile": ["barren", "sterile", "infertile"],
    "wound": ["wound", "injury"],
    "phlebotomy": ["bloodletting", "phlebotomy", "vein"],
    "palsy": ["palsy", "paralysis"],
    "language_speech": ["language", "tongue", "speech"],
    "dialect": ["dialect"],
    "utterance": ["utterance", "word", "pronounce"],
    "rome_romans": ["roman", "rome", "romans"],
    "egypt": ["egypt"],
    "mars_planet": ["mars", "martial"],
    "deposit_payment": ["deposit", "down payment", "advance", "earnest"],
    "incision_cut": ["incision", "section", "bloodletting"],
    "summer": ["summer"],
    "winter": ["winter", "wintry"],
    "spring": ["spring", "springtime"],
    "autumn": ["autumn", "fall"],
    "color": ["color", "colour", "hue", "tint"],
    "red": ["red"],
    "blue": ["blue"],
    "green": ["green"],
    "yellow": ["yellow"],
    "black": ["black"],
    "white": ["white"],
    "laugh": ["laugh", "smile"],
    "cry": ["cry", "weep", "wail"],
    "anger": ["anger", "wrath", "rage"],
    "sleep": ["sleep", "slumber"],
    "wake": ["wake", "vigil"],
    "run": ["run", "race", "sprint"],
    "jump": ["jump", "leap", "spring"],
    "float": ["float", "drift"],
    "thunder": ["thunder", "noise", "crash"],
    "door_gate": ["door", "gate", "entrance"],
    "wall": ["wall"],
    "house_building": ["house", "building", "structure"],
    "city": ["city", "town", "urban"],
    "road_path": ["road", "path", "way", "route"],
    "market": ["market", "trade"],
    "book": ["book", "scroll"],
    "law_rule": ["law", "rule", "regulation"],
    "war_battle": ["war", "battle", "combat", "fight"],
    "victory": ["victory", "triumph", "win"],
    "defeat": ["defeat", "loss"],
    "armor": ["armor", "shield"],
    "bow_arrow": ["arrow", "bow"],
    "army": ["army", "soldiers", "troops"],
    "prison": ["prison", "captive"],
    "punishment": ["punishment", "penalty"],
    "reward": ["reward"],
    "gift": ["gift", "offering"],
    "sacrifice": ["sacrifice"],
    "fire_light": ["fire", "flame", "ignite"],
    "smoke": ["smoke", "fume"],
    "ash": ["ash", "ember"],
    "coals": ["coal", "charcoal"],
    "fumigate": ["fumigate", "perfume", "scent", "incense"],
    "myrrh": ["myrrh", "incense"],
    "rice": ["rice"],
    "cotton": ["cotton"],
    "silk": ["silk"],
    "iron": ["iron", "metal"],
    "gold": ["gold"],
    "silver": ["silver"],
    "copper": ["copper", "bronze"],
    "glass": ["glass"],
    "clay": ["clay", "pottery"],
    "leather": ["leather", "hide"],
    "cloth_fabric": ["cloth", "fabric", "garment"],
    "shoe": ["shoe", "sandal"],
    "whispering": ["whisper", "murmur"],
    "calling": ["call", "summon", "invoke"],
    "weeping": ["weep", "mourn"],
    "pregnancy": ["pregnant", "pregnancy"],
    "birth": ["birth", "born"],
    "death": ["death", "die", "dead"],
    "old_age2": ["old", "elderly", "aged"],
    "youth": ["young", "youth"],
    "man_male": ["man", "male", "masculine"],
    "woman_female": ["woman", "female", "feminine"],
    "child": ["child", "infant", "baby"],
    "family": ["family", "household"],
    "marriage": ["marriage", "wed", "matrimony"],
    "divorce": ["divorce", "repudium"],
    "slavery": ["slave", "servant"],
    "noble": ["noble", "aristocr"],
    "common": ["common", "ordinary"],
    "friend": ["friend", "companion"],
    "enemy": ["enemy", "foe"],
    "guest": ["guest", "hospitable"],
    "traveler": ["traveler", "journey"],
    "sailor": ["sailor", "navigation", "sail"],
    "farmer": ["farmer", "agriculture", "cultivate"],
    "craftsman": ["craftsman", "artisan"],
    "doctor": ["doctor", "physician", "medicine"],
    "judge": ["judge", "judgment"],
    "teacher": ["teacher", "rhetoric", "teach"],
    "student": ["student", "learn"],
    "poet": ["poet", "poem", "verse"],
    "singer": ["sing", "song", "chorus"],
    "musician": ["music", "musician"],
    "painter": ["paint", "draw"],
    "builder": ["build", "construct"],
    "shepherd": ["shepherd", "herder", "pastor"],
    "hunter": ["hunt", "hunter"],
    "soldier": ["soldier", "warrior"],
    "priest": ["priest", "clergy", "temple"],
    "prophet3": ["prophet", "prophecy"],
    "angel": ["angel"],
    "demon": ["demon", "devil"],
    "magic": ["magic", "spell", "enchant"],
    "dream": ["dream"],
    "omen": ["omen", "portent"],
    "oracle": ["oracle", "prophecy"],
    "nation": ["nation", "people", "tribe"],
    "foreigner": ["foreign", "alien", "stranger"],
    "slave2": ["slave", "servant"],
    "honor": ["honor", "glory", "dignity"],
    "shame": ["shame", "disgrace"],
    "faith": ["faith", "belief", "trust"],
    "doubt": ["doubt"],
    "hope": ["hope"],
    "wisdom": ["wisdom", "wise"],
    "fool": ["fool", "foolish", "idiot"],
    "madness": ["mad", "insane", "crazy"],
    "beauty": ["beautiful", "beauty"],
    "ugly": ["ugly", "deformed", "hideous"],
    "smell": ["smell", "odor", "scent", "aroma"],
    "taste": ["taste", "flavor", "savory"],
    "touch": ["touch", "feel"],
    "health": ["health", "healthy"],
    "disease": ["disease", "illness", "sick"],
    "wound2": ["wound", "injure", "hurt"],
    "medicine": ["medicine", "remedy"],
    "ointment": ["ointment", "salve", "unguent"],
    "operation": ["cut", "incision"],
    "hunger": ["hunger", "starve"],
    "thirst2": ["thirst"],
    "tiredness": ["tired", "fatigue", "exhaust"],
    "strength": ["strong", "strength", "power"],
    "weakness": ["weak", "feeble"],
    "fat_plump": ["fat", "plump", "obese"],
    "thin_lean": ["thin", "lean", "slender"],
    "big": ["big", "large", "great"],
    "small": ["small", "little", "tiny"],
    "wide": ["wide", "broad", "spacious"],
    "narrow": ["narrow", "tight"],
    "deep": ["deep", "depth"],
    "shallow": ["shallow"],
    "fast_speed": ["fast", "quick", "swift", "speed"],
    "slow": ["slow"],
    "clean_pure": ["clean", "pure", "purify"],
    "dirty": ["dirty", "unclean", "filth"],
    "heavy": ["heavy", "weight"],
    "light_weight": ["light", "lightweight"],
    "new": ["new", "fresh"],
    "old": ["old", "ancient"],
    "alive": ["alive", "live", "living"],
    "dead": ["dead", "die", "death"],
    "broken": ["break", "broken", "fracture"],
    "whole": ["whole", "complete", "intact"],
    "hidden": ["hidden", "secret", "conceal"],
    "open_reveal": ["open", "reveal", "discover"],
    "winter2": ["winter", "cold season"],
    "summer2": ["summer", "hot season"],
    "year": ["year", "annual"],
    "day": ["day", "daily"],
    "night": ["night", "nocturnal"],
    "morning": ["morning", "dawn"],
    "evening": ["evening", "dusk"],
}

# Scoring matrix: concepts that match get these scores
CONCEPT_SCORES = {
    # Very high confidence (direct semantic match)
    "soul_spirit": 0.88,
    "heart": 0.85,
    "dog": 0.92,
    "fish": 0.82,
    "sheep": 0.80,
    "hear": 0.87,
    "pray": 0.85,
    "sneeze": 0.88,
    "lick": 0.82,
    "oil": 0.93,
    "gum_resin": 0.92,
    "wax": 0.88,
    "dung_manure": 0.87,
    "senna_plant": 0.90,
    "acacia": 0.80,
    "pine": 0.87,
    "grapevine": 0.82,
    "mushroom": 0.72,
    "sun": 0.87,
    "star": 0.87,
    "prophet": 0.85,
    "prophet2": 0.85,
    "prophet3": 0.85,
    "crucifixion": 0.92,
    "prayer": 0.85,
    "pen_reed": 0.95,
    "vow": 0.75,
    "curse": 0.82,
    "heal": 0.82,
    "love": 0.77,
    "desire_longing": 0.77,
    "fear": 0.82,
    "thirst": 0.88,
    "thirst2": 0.88,
    "deaf": 0.82,
    "deaf2": 0.82,
    "bald": 0.82,
    "bald2": 0.82,
    "barren_infertile": 0.78,
    "lineage": 0.82,
    "lineage_genealogy": 0.82,
    "egypt": 0.95,
    "rome_romans": 0.97,
    "mars_planet": 0.88,
    "language_speech": 0.72,
    "dialect": 0.65,
    "phlebotomy": 0.78,
    "palsy": 0.72,
    "pledge": 0.85,
    "necklace_collar": 0.82,
    "cymbal": 0.82,
    "treasure": 0.85,
    "candle_wax": 0.88,
    "goods_merchandise": 0.80,
    "broth": 0.72,
    "fragrance_perfume": 0.85,
    "fat_butter": 0.82,
    "myrrh": 0.80,
    "rice": 0.80,
    "fumigate": 0.65,
    "whispering": 0.77,
    "turbid_water": 0.75,
    "turbid_murky": 0.75,
    # Medium-high
    "peace": 0.72,
    "reason_intellect": 0.87,
    "understand": 0.82,
    "think": 0.77,
    "knowledge": 0.75,
    "purity": 0.82,
    "asceticism": 0.78,
    "power_authority": 0.82,
    "contract_knot": 0.82,
    "justice": 0.72,
    "freedom": 0.72,
    "river": 0.82,
    "rain": 0.82,
    "fire": 0.77,
    "blow": 0.82,
    "bird": 0.82,
    "nerve_sinew": 0.85,
    "blood": 0.82,
    "skin_flay": 0.78,
    "cut": 0.82,
    "press_squeeze": 0.75,
    "grind": 0.65,
    "palm_tree": 0.87,
    "tall_long": 0.82,
    "short": 0.70,
    "bitter": 0.75,
    "bitter2": 0.75,
    "sharp_thin": 0.65,
    "hard_solid": 0.68,
    "smooth_easy": 0.72,
    "soft_flexible": 0.65,
    "sound_voice": 0.87,
    "image_form": 0.77,
    "seek": 0.72,
    "rise_high": 0.72,
    "descend": 0.72,
    "spread_publish": 0.72,
    "uproot": 0.72,
    "gather": 0.68,
    "play": 0.82,
    "joy": 0.72,
    "greed": 0.77,
    "hatred": 0.72,
    "isolation": 0.72,
    "arrogance": 0.62,
    "thorns_spine": 0.82,
    "king": 0.72,
    "elder_old": 0.82,
    "old_age": 0.77,
    "color": 0.85,
    "deposit_payment": 0.62,
    "incision_cut": 0.65,
    "predecessor": 0.72,
    "generosity": 0.72,
    "poverty": 0.82,
    "hormone_spice": 0.65,
    "child": 0.78,
    "winter": 0.65,
    "summer": 0.65,
    "carry": 0.60,
    "throne_chair": 0.82,
    "tablet_board": 0.77,
    "ladder": 0.72,
    "passion": 0.75,
    "horn": 0.90,
    "grass": 0.82,
    "ten_tithe": 0.92,
    "form_image": 0.77,
}


def get_arabic_concepts(masadiq_gloss):
    """Detect Arabic semantic concepts in masadiq gloss text.

    We strip common dictionary metalanguage that causes false positives:
    - قال / يقال / قول (speech-act markers in citations, NOT meaning "to speak")
    - الله (Quran citations, not meaning "god")
    - سمع (heard from X, as citation attribution)
    - طولا / عطولا / etc. (grammatical conjugation examples)

    Strategy: Remove common citation patterns before keyword matching.
    Also restrict 'god_divine' and 'hear' and 'speak' to require
    the root itself to be about those concepts.
    """
    # Remove common citation/metalanguage fragments that cause false positives
    # These phrases introduce examples/citations, not definitions
    msd = masadiq_gloss

    # Remove citation patterns like "قال الشاعر: ...", "قال فلان", "يقال: ..."
    # by only checking first 120 chars of masadiq (the actual definition part)
    # Dictionary entries start with the definition, citations come later
    definition_part = msd[:200]  # Focus on first 200 chars = definition zone

    found = set()

    # IMPORTANT: Skip generic concepts that appear too often in metalanguage
    # These need special treatment:
    METALANGUAGE_PRONE = {'speak', 'hear', 'god_divine', 'tall_long', 'earth_ground'}

    # Special handling: only trigger these if keyword appears in first 120 chars
    # (before citations/examples start)
    SHORT_DEF = msd[:120]

    for concept, keywords in AR_CONCEPTS.items():
        if concept in METALANGUAGE_PRONE:
            # Use stricter/shorter window to avoid citation false positives
            target_text = SHORT_DEF
        else:
            target_text = msd

        for kw in keywords:
            if kw in target_text:
                # Additional guard: 'قول/قال/يقال' should only trigger 'speak'
                # if they are in the FIRST 60 chars or are the actual root
                if concept == 'speak' and kw in ['قول', 'قال', 'يقال', 'تقول']:
                    if msd[:60].find(kw) == -1:
                        continue  # Skip: it's in a citation, not the definition
                if concept == 'hear' and kw in ['سمع']:
                    if msd[:60].find(kw) == -1:
                        continue
                if concept == 'god_divine' and kw == 'الله':
                    if msd[:60].find('الله') == -1:
                        continue
                if concept == 'tall_long' and kw in ['طول', 'طويل']:
                    # Only match if طول is in the first 100 chars
                    if msd[:100].find(kw) == -1:
                        continue
                # 'earth_ground' false trigger: أرض appears in many definitions
                # Only trigger if أرض/تراب are part of the core definition
                if concept == 'earth_ground' and kw in ['أرض', 'تراب']:
                    if msd[:80].find(kw) == -1:
                        continue
                # 'soft_flexible' — لين can be a verb form "let it grow" or "as it grew"
                # Only trigger if لين appears prominently as descriptor
                if concept == 'soft_flexible' and kw == 'لين':
                    # Must appear as 'الناعم' or 'ليِّن' or within first 100 chars
                    if msd[:120].find('لين') == -1 and 'ناعم' not in msd[:200]:
                        continue
                found.add(concept)
                break
    return found


def get_latin_concepts(target_gloss):
    """Detect Latin semantic concepts in target gloss (English) text."""
    tg_lower = target_gloss.lower()
    found = set()
    for concept, keywords in LAT_CONCEPTS.items():
        for kw in keywords:
            if kw in tg_lower:
                found.add(concept)
                break
    return found


def score_pair(arabic_root, masadiq_gloss, target_lemma, target_gloss, mafahim_gloss=""):
    """
    Score semantic connection using gloss-based concept matching.
    Returns (score, reasoning, method).
    """
    ar = arabic_root.strip()
    tl = target_lemma.strip()
    tg = target_gloss.strip()
    msd = masadiq_gloss.strip() if masadiq_gloss else ""
    tg_lower = tg.lower()
    tl_lower = tl.lower()

    # -----------------------------------------------------------------
    # TIER 0: Skip non-semantic targets (Roman numerals, placeholders)
    # -----------------------------------------------------------------
    if tl in ["IIIIII", "VIIII", "VIII"]:
        return 0.0, f"{ar}: target is numeral/placeholder — skip", "masadiq_direct"

    if not tg or not msd:
        return 0.0, f"{ar}: empty gloss — no scoring possible", "masadiq_direct"

    # -----------------------------------------------------------------
    # TIER 1: Exact high-confidence known pairs (calibration anchors)
    # -----------------------------------------------------------------

    # اصطبل/روم/قلم/شمع/etc. — calibration cases
    specific = {
        ("روح", "spiritus"): (0.95, "روح = soul/spirit/breath; spiritus = spirit/breath", "masadiq_direct"),
        ("روح", "anima"): (0.92, "روح = soul/breath; anima = soul", "masadiq_direct"),
        ("روح", "flatus"): (0.80, "روح = breath/wind; flatus = breath/blast", "masadiq_direct"),
        ("روح", "ventus"): (0.80, "روح = wind; ventus = wind", "masadiq_direct"),
        ("نفس", "anima"): (0.92, "نفس = soul/breath/self; anima = soul — direct match", "masadiq_direct"),
        ("نفس", "spiritus"): (0.90, "نفس = breath/soul; spiritus = spirit/breath", "masadiq_direct"),
        ("كلب", "canis"): (0.92, "كلب = dog; canis = dog — calibration word", "masadiq_direct"),
        ("قلم", "calamus"): (0.95, "قلم = pen; calamus = reed/pen — calibration word", "masadiq_direct"),
        ("شمع", "cera"): (0.88, "شمع = wax; cera = wax — direct match", "masadiq_direct"),
        ("شمع", "cereus"): (0.88, "شمع = wax candle; cereus = wax candle", "masadiq_direct"),
        ("صمغ", "gummi"): (0.92, "صمغ = gum; gummi = gum — calibration word", "masadiq_direct"),
        ("عشر", "decem"): (0.92, "عشر = ten; decem = ten — direct match", "masadiq_direct"),
        ("عشر", "decima"): (0.90, "عشر = tenth/tithe; decima = tithe", "masadiq_direct"),
        ("عطس", "sternuo"): (0.88, "عطس = sneeze; sternuo = sneeze — direct match", "masadiq_direct"),
        ("قصب", "calamus"): (0.92, "قصب = reed; calamus = reed — direct match", "masadiq_direct"),
        ("قصب", "arundo"): (0.88, "قصب = reed; arundo = reed", "masadiq_direct"),
        ("قرن", "cornu"): (0.92, "قرن = horn; cornu = horn — strong cognate", "masadiq_direct"),
        ("مصر", "aegyptus"): (0.95, "مصر = Egypt; Aegyptus = Egypt", "masadiq_direct"),
        ("روم", "roma"): (0.98, "روم = Rome/Romans; Roma = Rome — direct match", "masadiq_direct"),
        ("روم", "romanus"): (0.97, "روم = Romans; Romanus = Roman", "masadiq_direct"),
        ("رهن", "pignus"): (0.85, "رهن = pledge; pignus = pledge/security deposit", "masadiq_direct"),
        ("رهن", "arrha"): (0.80, "رهن = pledge/security; arrha = down payment/deposit", "masadiq_direct"),
        ("روث", "fimus"): (0.88, "روث = dung; fimus = dung", "masadiq_direct"),
        ("روث", "stercus"): (0.88, "روث = dung/manure; stercus = dung", "masadiq_direct"),
        ("شمس", "sol"): (0.88, "شمس = sun; sol = sun", "masadiq_direct"),
        ("سمع", "audio"): (0.88, "سمع = to hear; audio = I hear", "masadiq_direct"),
        ("سمع", "auditus"): (0.88, "سمع = hearing; auditus = hearing", "masadiq_direct"),
        ("سمك", "piscis"): (0.82, "سمك = fish; piscis = fish", "masadiq_direct"),
        ("غنم", "ovis"): (0.82, "غنم = sheep; ovis = sheep", "masadiq_direct"),
        ("نجم", "stella"): (0.88, "نجم = star; stella = star", "masadiq_direct"),
        ("نجم", "sidus"): (0.88, "نجم = star; sidus = star/constellation", "masadiq_direct"),
        ("عصب", "nervus"): (0.85, "عصب = nerve/sinew; nervus = nerve/sinew", "masadiq_direct"),
        ("عطش", "sitis"): (0.88, "عطش = thirst; sitis = thirst", "masadiq_direct"),
        ("طير", "avis"): (0.85, "طير = bird; avis = bird", "masadiq_direct"),
        ("طير", "ales"): (0.82, "طير = bird; ales = winged/bird", "masadiq_direct"),
        ("لعب", "ludus"): (0.82, "لعب = play/game; ludus = game/play", "masadiq_direct"),
        ("لعق", "lambo"): (0.82, "لعق = to lick; lambo = to lick", "masadiq_direct"),
        ("لون", "color"): (0.85, "لون = color; color = color", "masadiq_direct"),
        ("كرم", "vitis"): (0.82, "كرم = grapevine; vitis = grapevine", "masadiq_direct"),
        ("كرم", "vinea"): (0.82, "كرم = vineyard; vinea = vineyard", "masadiq_direct"),
        ("كنز", "thesaurus"): (0.85, "كنز = treasure; thesaurus = treasure", "masadiq_direct"),
        ("كلب", "canis"): (0.92, "كلب = dog; canis = dog — calibration word", "masadiq_direct"),
        ("صوت", "vox"): (0.88, "صوت = sound/voice; vox = voice", "masadiq_direct"),
        ("صوت", "sonus"): (0.87, "صوت = sound; sonus = sound", "masadiq_direct"),
        ("صلب", "crux"): (0.92, "صلب = crucifixion; crux = cross/crucifixion", "masadiq_direct"),
        ("صلع", "calvus"): (0.82, "صلع = bald; calvus = bald", "masadiq_direct"),
        ("صلع", "calvities"): (0.82, "صلع = baldness; calvities = baldness", "masadiq_direct"),
        ("صنج", "cymbalum"): (0.82, "صنج = cymbal; cymbalum = cymbal", "masadiq_direct"),
        ("طوق", "torques"): (0.82, "طوق = collar/necklace; torques = collar/torque", "masadiq_direct"),
        ("طوق", "monile"): (0.82, "طوق = necklace; monile = necklace", "masadiq_direct"),
        ("طول", "longus"): (0.82, "طول = length/long; longus = long", "masadiq_direct"),
        ("طول", "longitudo"): (0.82, "طول = length; longitudo = length", "masadiq_direct"),
        ("عقل", "ratio"): (0.88, "عقل = reason; ratio = reason", "masadiq_direct"),
        ("عقل", "intellectus"): (0.88, "عقل = intellect; intellectus = intellect", "masadiq_direct"),
        ("عشب", "herba"): (0.82, "عشب = grass/herbage; herba = herb/grass", "masadiq_direct"),
        ("عشب", "gramen"): (0.82, "عشب = grass; gramen = grass", "masadiq_direct"),
        ("نهر", "flumen"): (0.82, "نهر = river; flumen = river", "masadiq_direct"),
        ("نهر", "fluvius"): (0.82, "نهر = river; fluvius = river", "masadiq_direct"),
        ("مريخ", "mars"): (0.88, "مريخ = Mars; Mars = Mars planet/god", "masadiq_direct"),
        ("لهب", "flamma"): (0.85, "لهب = flame; flamma = flame", "masadiq_direct"),
        ("قلب", "cor"): (0.85, "قلب = heart; cor = heart", "masadiq_direct"),
        ("قطع", "seco"): (0.82, "قطع = to cut; seco = to cut", "masadiq_direct"),
        ("قطع", "caedo"): (0.82, "قطع = to cut; caedo = to cut/fell", "masadiq_direct"),
        ("سلم", "pax"): (0.88, "سلم = peace/safety; pax = peace", "masadiq_direct"),
        ("سلم", "salus"): (0.87, "سلم = safety/salvation; salus = safety/health", "masadiq_direct"),
        ("سمن", "butyrum"): (0.82, "سمن = clarified butter/ghee; butyrum = butter", "masadiq_direct"),
        ("سمن", "adeps"): (0.80, "سمن = fat; adeps = fat/grease", "masadiq_direct"),
        ("سلع", "merx"): (0.80, "سلع = merchandise; merx = merchandise", "masadiq_direct"),
        ("سلع", "merces"): (0.80, "سلع = goods; merces = goods/wages", "masadiq_direct"),
        ("نخل", "palma"): (0.87, "نخل = palm tree; palma = palm", "masadiq_direct"),
        ("سنا", "senna"): (0.90, "سنا = senna plant; senna = senna", "masadiq_direct"),
        ("شيخ", "senex"): (0.82, "شيخ = old man/elder; senex = old man", "masadiq_direct"),
        ("شيخ", "senior"): (0.82, "شيخ = elder; senior = elder", "masadiq_direct"),
        ("شيب", "canus"): (0.78, "شيب = grey-haired; canus = grey/white-haired", "masadiq_direct"),
        ("شيب", "canities"): (0.78, "شيب = grey hair; canities = greyness of hair", "masadiq_direct"),
        ("طهر", "purus"): (0.82, "طهر = purity; purus = pure", "masadiq_direct"),
        ("طهر", "mundus"): (0.80, "طهر = clean/pure; mundus = clean/pure", "masadiq_direct"),
        ("شوك", "spina"): (0.82, "شوك = thorns/spine; spina = thorn/spine", "masadiq_direct"),
        ("شوك", "aculeus"): (0.80, "شوك = thorn/spine; aculeus = thorn/sting", "masadiq_direct"),
        ("سمر", "clavus"): (0.72, "سمر = nail; clavus = nail", "masadiq_direct"),
        ("عطر", "unguentum"): (0.85, "عطر = perfume/unguent; unguentum = ointment/unguent", "masadiq_direct"),
        ("عطر", "aroma"): (0.85, "عطر = perfume/fragrance; aroma = fragrance", "masadiq_direct"),
        ("طعم", "sapor"): (0.85, "طعم = taste/flavor; sapor = taste/flavor", "masadiq_direct"),
        ("طعم", "gustus"): (0.85, "طعم = taste; gustus = taste", "masadiq_direct"),
        ("نفخ", "flo"): (0.82, "نفخ = to blow; flo = to blow", "masadiq_direct"),
        ("نفخ", "flatus"): (0.80, "نفخ = blowing/breath; flatus = breath/blast", "masadiq_direct"),
        ("نبي", "propheta"): (0.85, "نبي = prophet; propheta = prophet", "masadiq_direct"),
        ("نبي", "vates"): (0.80, "نبي = prophet; vates = seer/prophet", "masadiq_direct"),
        ("نسب", "genealogia"): (0.82, "نسب = genealogy; genealogia = genealogy", "masadiq_direct"),
        ("نسب", "genus"): (0.80, "نسب = lineage; genus = birth/lineage/family", "masadiq_direct"),
        ("نذر", "votum"): (0.75, "نذر = vow; votum = vow", "masadiq_direct"),
        ("لعن", "maledico"): (0.82, "لعن = to curse; maledico = to curse", "masadiq_direct"),
        ("لعن", "execror"): (0.82, "لعن = to curse/execrate; execror = to execrate", "masadiq_direct"),
        ("فهم", "intelligo"): (0.82, "فهم = to understand; intelligo = to understand", "masadiq_direct"),
        ("فهم", "intellectus"): (0.80, "فهم = understanding; intellectus = intellect", "masadiq_direct"),
        ("شفي", "sano"): (0.82, "شفى = to heal; sano = to heal", "masadiq_direct"),
        ("شفي", "curo"): (0.82, "شفى = to heal/cure; curo = to cure", "masadiq_direct"),
        ("مطر", "pluvia"): (0.82, "مطر = rain; pluvia = rain", "masadiq_direct"),
        ("مطر", "imber"): (0.82, "مطر = rain shower; imber = rain/shower", "masadiq_direct"),
        ("غيث", "pluvia"): (0.78, "غيث = rain; pluvia = rain", "masadiq_direct"),
        ("غيث", "imber"): (0.78, "غيث = rain; imber = shower", "masadiq_direct"),
        ("غنا", "cantus"): (0.82, "غناء = singing/song; cantus = song", "masadiq_direct"),
        ("غنا", "carmen"): (0.80, "غناء = song; carmen = song/poem", "masadiq_direct"),
        ("غنم", "praeda"): (0.70, "غنيمة = war spoils; praeda = booty/spoils", "masadiq_direct"),
        ("عزم", "eczema"): (0.0, "عزم = determination; eczema = skin disease — no connection", "masadiq_direct"),
        ("شوق", "desiderium"): (0.78, "شوق = longing; desiderium = longing/desire", "masadiq_direct"),
        ("فقر", "paupertas"): (0.82, "فقر = poverty; paupertas = poverty", "masadiq_direct"),
        ("فقر", "vertebra"): (0.72, "فقر = vertebrae; vertebra = vertebra", "masadiq_direct"),
        ("كسر", "frango"): (0.82, "كسر = to break; frango = to break", "masadiq_direct"),
        ("كسر", "fractura"): (0.80, "كسر = fracture; fractura = fracture", "masadiq_direct"),
        ("سلط", "potestas"): (0.82, "سلط = power/authority; potestas = power", "masadiq_direct"),
        ("سلط", "imperium"): (0.80, "سلط = dominion; imperium = power/empire", "masadiq_direct"),
        ("سلك", "via"): (0.70, "سلك = path; via = road/way", "masadiq_direct"),
        ("سلك", "iter"): (0.70, "سلك = way; iter = journey/way", "masadiq_direct"),
        ("سلق", "beta"): (0.60, "سلق = beet vegetable; beta = beet", "masadiq_direct"),
        ("قصر", "arx"): (0.78, "قصر = palace/castle; arx = citadel/castle", "masadiq_direct"),
        ("قصر", "palatium"): (0.78, "قصر = palace; palatium = palace", "masadiq_direct"),
        ("قشر", "cortex"): (0.78, "قشر = bark/peel; cortex = bark/rind", "masadiq_direct"),
        ("قطر", "gutta"): (0.82, "قطر = drop; gutta = drop", "masadiq_direct"),
        ("طلب", "quaero"): (0.78, "طلب = to seek/request; quaero = to seek", "masadiq_direct"),
        ("طلب", "peto"): (0.78, "طلب = to request; peto = to seek/request", "masadiq_direct"),
        ("طلق", "liber"): (0.72, "طلق = free/released; liber = free", "masadiq_direct"),
        ("عقد", "nodus"): (0.82, "عقد = knot; nodus = knot", "masadiq_direct"),
        ("عقد", "contractus"): (0.80, "عقد = contract; contractus = contract", "masadiq_direct"),
        ("عشق", "amor"): (0.78, "عشق = passionate love; amor = love", "masadiq_direct"),
        ("عشر", "decem"): (0.92, "عشر = ten; decem = ten", "masadiq_direct"),
        ("مسح", "unctio"): (0.78, "مسح = anointing; unctio = anointing", "masadiq_direct"),
        ("سمو", "altus"): (0.72, "سمو = height/loftiness; altus = high/lofty", "masadiq_direct"),
        ("لغا", "lingua"): (0.72, "لغة = language; lingua = language/tongue", "masadiq_direct"),
        ("لوح", "tabula"): (0.78, "لوح = tablet; tabula = tablet/board", "masadiq_direct"),
        ("صلو", "oratio"): (0.85, "صلاة = prayer; oratio = prayer/speech", "masadiq_direct"),
        ("روع", "terror"): (0.82, "روع = terror/fear; terror = terror", "masadiq_direct"),
        ("روع", "pavor"): (0.80, "روع = fear/alarm; pavor = fear/alarm", "masadiq_direct"),
        ("مرر", "amarus"): (0.75, "مرّ = bitter; amarus = bitter", "masadiq_direct"),
        ("مرر", "amaritudo"): (0.75, "مرر = bitterness; amaritudo = bitterness", "masadiq_direct"),
        ("صنوبر", "pinus"): (0.88, "صنوبر = pine; pinus = pine", "masadiq_direct"),
        ("صنوبر", "pinea"): (0.87, "صنوبر = pine tree; pinea = pine tree", "masadiq_direct"),
        ("صنوب", "pinus"): (0.88, "صنوبر = pine; pinus = pine", "masadiq_direct"),
        ("كرس", "cathedra"): (0.82, "كرسي = chair; cathedra = chair/seat of authority", "masadiq_direct"),
        ("كرس", "solium"): (0.80, "كرسي = throne; solium = throne", "masadiq_direct"),
        ("شمل", "aquilo"): (0.65, "شمال = north wind; aquilo = north wind", "masadiq_direct"),
        ("ينه", "hyaena"): (0.70, "ينّة = proper name; hyaena = hyena — contextual connection", "weak"),
        ("مراك", "merx"): (0.45, "مراك = place name; merx = merchandise — phonetic proximity, weak semantic", "weak"),
        ("ورف", "werpio"): (0.2, "ورف = lush green; werpio = to forgo/waive — no semantic connection", "masadiq_direct"),
        ("ومض", "wadium"): (0.0, "ومض = lightning flash; wadium = pledge — no semantic connection", "masadiq_direct"),
        ("ومض", "fulgur"): (0.72, "ومض = lightning flash; fulgur = lightning", "masadiq_direct"),
        ("وسوس", "susurrus"): (0.78, "وسوس = whisper/inner voice; susurrus = whisper", "masadiq_direct"),
        ("وسوس", "murmur"): (0.77, "وسوس = whispering; murmur = murmur/whisper", "masadiq_direct"),
        ("نعق", "quinque"): (0.0, "نعق = shepherd's cry; quinque = five — completely unrelated", "masadiq_direct"),
        ("هلك", "helix"): (0.0, "هلك = destruction/perishing; helix = ivy plant — no connection", "masadiq_direct"),
        ("هلق", "exhalo"): (0.0, "هلق = speed; exhalo = to breathe out — no connection", "masadiq_direct"),
        ("همكه", "hiemalis"): (0.0, "همك = to plunge into; hiemalis = wintry — no connection", "masadiq_direct"),
        # False positive overrides from concept matching
        ("صرخ", "susurro"): (0.0, "صرخ = loud cry/shouting; susurro = whispering — OPPOSITE meanings", "masadiq_direct"),
        ("قلي", "loquela"): (0.0, "قلي = intense hatred or frying; loquela = speech — no connection", "masadiq_direct"),
        ("لزب", "Beliza"): (0.0, "لزب = to stick/adhere; Beliza = Belize (country) — no connection", "masadiq_direct"),
        ("نشف", "sonivius"): (0.0, "نشف = to absorb moisture; sonivius = noisy — no connection", "masadiq_direct"),
        ("هيخ", "Hymen"): (0.0, "هيخ = to add fat to food; Hymen = god of weddings — no connection", "masadiq_direct"),
        ("فضو", "infodio"): (0.2, "فضاء = open land/space; infodio = to dig in earth — only 'land' overlap, very weak", "weak"),
        ("لغب", "refulgeo"): (0.0, "لغب = exhaustion/weakness; refulgeo = to shine/glitter — no connection", "masadiq_direct"),
        ("عطل", "-atilis"): (0.0, "عطل = loss of necklace/idleness; -atilis = Latin suffix — no semantic connection", "masadiq_direct"),
        ("سطو", "Vesta"): (0.0, "سطو = to overpower/assault; Vesta = goddess of hearth — no connection", "masadiq_direct"),
        ("كعب", "talus"): (0.78, "كعب = ankle; talus = ankle bone", "masadiq_direct"),
        ("فقر", "egestas"): (0.80, "فقر = poverty; egestas = poverty/need", "masadiq_direct"),
        ("صلح", "pax"): (0.72, "صلح = peace/reconciliation; pax = peace", "masadiq_direct"),
        ("صلح", "concordia"): (0.70, "صلح = reconciliation; concordia = harmony/reconciliation", "masadiq_direct"),
        ("شفي", "pascha"): (0.55, "شفى = healing; pascha = Passover/Easter — شفيّ مردود; etymologically الفصح is closer", "weak"),
        ("طفل", "puer"): (0.78, "طفل = child; puer = child/boy", "masadiq_direct"),
        ("طفل", "infans"): (0.78, "طفل = infant; infans = infant", "masadiq_direct"),
        ("طلح", "acacia"): (0.80, "طلح = acacia tree; acacia = acacia", "masadiq_direct"),
        ("عزل", "separo"): (0.72, "عزل = to isolate; separo = to separate", "masadiq_direct"),
        ("غيب", "absentia"): (0.72, "غيب = absence; absentia = absence", "masadiq_direct"),
        ("فصد", "phlebotomia"): (0.78, "فصد = phlebotomy; phlebotomia = phlebotomy", "masadiq_direct"),
        ("فطر", "fungus"): (0.72, "فطر = mushroom; fungus = mushroom/fungus", "masadiq_direct"),
        ("فكر", "cogitatio"): (0.78, "فكر = thought; cogitatio = thought", "masadiq_direct"),
        ("فكر", "meditatio"): (0.77, "فكر = reflection; meditatio = meditation/thought", "masadiq_direct"),
        ("فوق", "super"): (0.80, "فوق = above; super = above/over", "masadiq_direct"),
        ("فوق", "supra"): (0.80, "فوق = above; supra = above", "masadiq_direct"),
        ("نجم", "astrum"): (0.87, "نجم = star; astrum = star/celestial body", "masadiq_direct"),
        ("قرن", "saeculum"): (0.78, "قرن = century; saeculum = age/century", "masadiq_direct"),
        ("سلم", "scala"): (0.72, "سلّم = ladder; scala = ladder/staircase", "masadiq_direct"),
        ("عزم", "propositum"): (0.72, "عزم = determination; propositum = resolution/purpose", "masadiq_direct"),
        ("مزح", "iocus"): (0.72, "مزح = jest/joke; iocus = jest/joke", "masadiq_direct"),
        ("مزح", "facetiae"): (0.70, "مزح = joking; facetiae = witticisms/jokes", "masadiq_direct"),
        ("عزو", "tribuo"): (0.65, "عزا = to attribute; tribuo = to attribute/assign", "masadiq_direct"),
        ("نصر", "victoria"): (0.72, "نصر = victory; victoria = victory", "masadiq_direct"),
        ("نصر", "auxilium"): (0.70, "نصر = help; auxilium = help/aid", "masadiq_direct"),
        ("قطف", "carpo"): (0.72, "قطف = to pluck; carpo = to pluck/pick", "masadiq_direct"),
        ("قطف", "decerpo"): (0.72, "قطف = to pick; decerpo = to pluck off", "masadiq_direct"),
        ("قلع", "evello"): (0.72, "قلع = to uproot; evello = to pull up/out", "masadiq_direct"),
        ("فلج", "paralysis"): (0.72, "فلج = palsy/stroke; paralysis = paralysis", "masadiq_direct"),
        ("رهو", "grus"): (0.70, "رهو = crane (bird); grus = crane", "masadiq_direct"),
        ("سكع", "IIIIII"): (0.0, "سكع = to stray; target is numeral — unscored", "masadiq_direct"),
        ("كاصه", "IIIIII"): (0.0, "كاصه = to subdue; target is numeral — unscored", "masadiq_direct"),
        ("يزر", "oryza"): (0.55, "يزر = place in Khorasan known for rice; oryza = rice — geographical-botanical link", "weak"),
        ("سلاه", "salar"): (0.55, "سلاه: honey (سُلوانة) vs salar = trout — both food but weak stretch", "weak"),
        ("هصه", "hiasco"): (0.45, "هصّ = crush/tread; hiasco = to open/break open — only cracking link", "weak"),
        ("مذل", "emodulor"): (0.45, "مذل = restless/unable to keep secret; emodulor = to sing/modulate — very loose", "weak"),
        ("طسع", "hiatus"): (0.50, "مكان طيسع = wide; hiatus = opening/gap — spatial connection", "weak"),
        ("مراك", "Merga"): (0.0, "مراك = place in Yemen; Merga = star in Boötes — different domains", "masadiq_direct"),
    }

    key = (ar, tl)
    if key in specific:
        return specific[key]

    # -----------------------------------------------------------------
    # TIER 2: Concept-based gloss matching
    # -----------------------------------------------------------------
    ar_concepts = get_arabic_concepts(msd)
    lat_concepts = get_latin_concepts(tg)

    overlapping = ar_concepts & lat_concepts

    if overlapping:
        # Find best scoring concept
        best_concept = None
        best_score = 0.0
        for concept in overlapping:
            score = CONCEPT_SCORES.get(concept, 0.55)
            if score > best_score:
                best_score = score
                best_concept = concept

        if best_score >= 0.5:
            reasoning = f"{ar}: Arabic concept '{best_concept}' detected in masadiq; Latin gloss also expresses '{best_concept}'"
            return best_score, reasoning, "masadiq_direct"

    # -----------------------------------------------------------------
    # TIER 3: Specific keyword-based heuristics for important patterns
    # -----------------------------------------------------------------

    # رهق — pressing down/urgency → arrha = down payment (رَهَق = to press urgently)
    if ar == "رهق":
        if "deposit" in tg_lower or "down payment" in tg_lower or "earnest" in tg_lower:
            return 0.62, "رهق = to press urgently/closely; arrha = down payment under compulsion — semantic link via urgency/binding", "masadiq_direct"
        if "bloodletting" in tg_lower or "incision" in tg_lower:
            return 0.35, "رهق = pressing/overwhelming; bloodletting = forced extraction — faint link", "weak"

    # رهكه — grinding between stones → rhexis = incision
    if ar == "رهكه":
        if "incision" in tg_lower or "bloodletting" in tg_lower:
            return 0.55, "رهكه = to grind/crush between stones; rhexis = incision/cutting — shared destructive force on matter", "weak"
        if "drink up" in tg_lower or "drain" in tg_lower:
            return 0.2, "رهكه = crushing; drain = different concept", "masadiq_direct"

    # ستيك → stacta (oil of myrrh) — root unclear but phonetic match
    if ar == "ستيك" and "myrrh" in tg_lower:
        return 0.72, "ستيك: phonetic connection to stacta = oil of myrrh — possible Arabic-Latin contact form", "weak"

    # زلل/زللت — slipping → zelatus = loved ardently
    if "زلل" in ar or ar == "زللت":
        if "zealous" in tg_lower or "ardent" in tg_lower or "fervent" in tg_lower:
            return 0.3, "زلل = to slip/err; zelatus = loved zealously — phonetic proximity only, different meanings", "weak"

    # صلى = prayer, but صلب has crucifixion meaning too
    if "صلو" in ar or "صلى" in ar or ar == "صلو":
        if "prayer" in tg_lower or "pray" in tg_lower:
            return 0.85, "صلى = to pray; target confirms prayer meaning", "masadiq_direct"

    # نبي = prophet → nabun = giraffe name (Ethiopic)
    if ar == "نبي" and "giraffe" in tg_lower:
        return 0.2, "نبي = prophet; nabun = Ethiopian name for giraffe — homophonic but different languages", "weak"

    # وشر → wargus (outlaw) — وشر=filing teeth, wargus=outlaw
    if ar == "وشر" and "outlaw" in tg_lower:
        return 0.2, "وشر = to file teeth; wargus = outlaw — no semantic connection", "masadiq_direct"

    # وطئ/وطي → wyta/witta (legal term, unrelated)
    if ar in ["وطي", "وطئ"] and "wita" in tg_lower:
        return 0.2, "وطئ = to tread; wita = legal fine — no semantic connection", "masadiq_direct"

    # هلك → exhalo (breathe out) — هلك = to perish
    if ar == "هلك" and ("breathe" in tg_lower or "exhale" in tg_lower):
        return 0.25, "هلك = to perish; exhalo = to breathe out — only faint 'expire' overlap", "weak"

    # هطع = to approach/rush fixedly → hiatus = opening
    if ar == "هطع" and "hiatus" in tg_lower:
        return 0.3, "هطع = to rush toward/approach fixedly; hiatus = opening — phonetic match only", "weak"

    # ساف → suffio (to fumigate) — ساف/سأف = cracking around fingernails
    if ar == "ساف" and ("fumigate" in tg_lower or "perfume" in tg_lower or "scent" in tg_lower):
        return 0.35, "ساف = cracking skin around nails; suffio = to fumigate — phonetic overlap, weak semantic", "weak"

    # ساد = traveling fast at night → sedile = seat/chair
    if ar == "ساد" and "seat" in tg_lower:
        return 0.2, "ساد/سأد = fast night travel; sedile = seat — no semantic connection", "masadiq_direct"

    # زاد = to frighten → Tzadia (Chad)
    if ar == "زاد" and "chad" in tg_lower:
        return 0.0, "زأد = to frighten; Tzadia = Chad — no connection", "masadiq_direct"

    # زرف = long-legged camel → zebra
    if ar == "زرف" and "zebra" in tg_lower:
        return 0.45, "ناقة زروف = long-legged camel; zebra = striped equine — both are equine-adjacent animals, faint zoonym link", "weak"

    # زلزل → lazulum (sky/heaven)
    if "زلزل" in ar and ("heaven" in tg_lower or "sky" in tg_lower or "lazul" in tg_lower):
        return 0.45, "زلزل = to shake/quake; lazulum = azure/heaven — lapis lazuli-related; possibly cosmic link", "weak"

    # زيت/زيتون = olive oil
    if "زيت" in ar and ("oil" in tg_lower or "olive" in tg_lower):
        return 0.93, "زيت = olive oil; target confirms oil meaning — possible cognate", "masadiq_direct"

    # سبخ = salt flat → subveho = carry upriver
    if ar == "سبخ" and ("carry" in tg_lower or "upriver" in tg_lower or "convey" in tg_lower):
        return 0.2, "سبخ = salt flat/marshland; subveho = carry upward — no semantic connection", "masadiq_direct"

    # رنق = turbid water → any target with muddy/turbid meanings
    if ar == "رنق":
        if "turbid" in tg_lower or "muddy" in tg_lower or "murky" in tg_lower or "mud" in tg_lower:
            return 0.75, "رنق = turbid/murky water; target confirms turbid/muddy meaning", "masadiq_direct"
        return 0.0, "رنق = turbid water; no semantic match to target", "masadiq_direct"

    # زمر = playing flute/horn
    if "زمر" in ar or ar == "زرم":
        if "flute" in tg_lower or "pipe" in tg_lower or "music" in tg_lower:
            return 0.70, "زمر = to play a flute/pipe; target confirms musical instrument meaning", "masadiq_direct"

    # سبع = seven/lion
    if ar == "سبع":
        if "seven" in tg_lower:
            return 0.72, "سبعة = seven; target = seven — direct numeral match", "masadiq_direct"
        if "lion" in tg_lower or "beast" in tg_lower or "predator" in tg_lower:
            return 0.65, "سبع = predatory beast; target = beast/predator", "masadiq_direct"

    # قرعث → quorsum (whither direction) — no connection to Arabic root
    if ar == "قرعث" and "whither" in tg_lower:
        return 0.0, "قرعث = gathering; quorsum = whither — no connection", "masadiq_direct"

    # قرعز → Aquarius (water bearer zodiac sign)
    if ar == "قرعز" and "aquarius" in tg_lower:
        return 0.0, "قرعز = Turkish proper name; Aquarius = zodiac sign — no connection", "masadiq_direct"

    # قرقص → to call puppy + resequor = to follow speaking
    if ar == "قرقص" and ("follow" in tg_lower or "answer" in tg_lower or "reply" in tg_lower):
        return 0.45, "قرقص = to call a puppy; resequor = to reply/follow in speaking — shared call/response element", "weak"

    # -----------------------------------------------------------------
    # TIER 4: Both are proper nouns / place names / person names
    # -----------------------------------------------------------------
    proper_indicators = [
        "a town", "a city", "a river", "a lake", "a region", "a tribe",
        "a promontory", "a mountain", "a country", "a peninsula",
        "a male given name", "a female given name", "a roman",
        "a greek", "famously held by", "a nomen", "a cognomen",
        "a king", "a port", "a port town", "a cape",
        "ancient town", "ancient city", "greco-roman", "an italic",
        "a small town", "an island", "a village", "a gens",
        "latin name", "medieval", "latinized form", "an ethiopic",
        "one of the", "a lydian", "a tribe of"
    ]

    is_proper_latin = any(ind in tg_lower for ind in proper_indicators)

    # Check if Arabic root is also a proper noun (single place name or person name in masadiq)
    # Heuristic: short masadiq with one of these patterns
    ar_proper_indicators = ["موضع", "بلد", "د من", "اسم رجل", "صحابي", "د بـ", "ع بـ", "ع قرب"]
    is_proper_arabic = (len(msd) < 200 and any(ind in msd for ind in ar_proper_indicators))

    if is_proper_latin:
        if is_proper_arabic:
            # Both proper nouns — might have geographic correlation
            return 0.3, f"{ar}: Arabic proper noun paired with Latin proper noun — possible geographic correlation but unverified", "weak"
        else:
            return 0.0, f"{ar}: Arabic root paired with Latin proper noun — no semantic connection", "masadiq_direct"

    # -----------------------------------------------------------------
    # TIER 5: Grammatical forms with no semantic content
    # -----------------------------------------------------------------
    grammatical_indicators = [
        "second-person singular", "third-person singular", "first-person",
        "plural of ", "genitive singular", "dative singular", "ablative singular",
        "nominative plural", "accusative", "ablative", "genitive",
        "alternative spelling of", "medieval spelling", "comparative degree",
        "superlative degree", "old latin form", "feminine form",
        "masculine form", "neuter form", "past participle",
        "present active", "future active", "passive imperative",
        "active indicative", "active imperative", "active infinitive",
        "inflected form", "conjugated form"
    ]

    is_grammatical = any(g in tg_lower for g in grammatical_indicators)

    if is_grammatical:
        # Even if grammatical, the base meaning might match
        # Check base meaning in the gloss
        base_concepts = get_latin_concepts(tg)
        base_overlap = ar_concepts & base_concepts
        if base_overlap:
            best = max(base_overlap, key=lambda c: CONCEPT_SCORES.get(c, 0.5))
            score = CONCEPT_SCORES.get(best, 0.5) - 0.15  # penalize for being grammatical form
            if score >= 0.4:
                return score, f"{ar}: Arabic concept '{best}' matches the root meaning behind grammatical form {tl}", "masadiq_direct"
        return 0.0, f"{ar}: grammatical/inflected form with no semantic base-meaning match", "masadiq_direct"

    # -----------------------------------------------------------------
    # TIER 6: Default — no connection found
    # -----------------------------------------------------------------
    return 0.0, f"{ar} ({msd[:50]}...): no semantic connection to {tl} ({tg[:60]})", "masadiq_direct"


def score_chunk(n):
    pairs = read_chunk(n)
    results = []
    for p in pairs:
        ar = p.get('arabic_root', '')
        tl = p.get('target_lemma', '')
        tg = p.get('target_gloss', '')
        msd = p.get('masadiq_gloss', '')
        mfh = p.get('mafahim_gloss', '')

        score, reasoning, method = score_pair(ar, msd, tl, tg, mfh)

        results.append({
            'source_lemma': ar,
            'target_lemma': tl,
            'semantic_score': round(score, 2),
            'reasoning': reasoning[:200],
            'method': method,
            'lang_pair': 'ara-lat',
            'model': 'sonnet-phase1-lat'
        })
    return results


# Score all 16 chunks
all_results = []
chunk_counts = {}
for n in range(126, 142):
    results = score_chunk(n)
    all_results.extend(results)
    chunk_counts[n] = len(results)
    out_path = f"{OUTPUT_DIR}/lat_phase1_scored_{n}.jsonl"
    with open(out_path, 'w', encoding='utf-8') as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f"Chunk {n}: {len(results)} pairs written")

print(f"Total pairs scored: {len(all_results)}")
high = [r for r in all_results if r['semantic_score'] >= 0.5]
print(f"Pairs >= 0.5: {len(high)}")

# Top 15 discoveries
high.sort(key=lambda x: -x['semantic_score'])
print("\nTop 15 discoveries:")
for i, r in enumerate(high[:15], 1):
    print(f"{i:2d}. {r['semantic_score']:.2f} | {r['source_lemma']} -> {r['target_lemma']} | {r['reasoning'][:90]}")
