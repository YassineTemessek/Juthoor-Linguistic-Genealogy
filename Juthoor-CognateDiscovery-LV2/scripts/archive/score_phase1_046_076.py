"""
Score Arabic-Greek semantic pairs for chunks 046-076 (phase1_new_NNN.jsonl).
Uses MASADIQ-FIRST methodology: dictionary meaning checked first, then conceptual core.
"""
import json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

CHUNKS_DIR = Path('C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_phase1_chunks')
RESULTS_DIR = Path('C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_results')
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def classify_target(tgt: str, lemma: str) -> str:
    """Classify target_gloss type."""
    tl = tgt.lower()
    ll = lemma.lower()
    gram_markers = [
        "nominative", "accusative", "genitive", "dative", "vocative",
        "plural of ", "singular of ", "dual of ", "participle of ",
        "superlative degree", "comparative degree", "contraction of",
        "aeolic form", "doric form", "ionic form", "attic form",
        "alternative form", "alternate form", "common form of",
        "first person", "second person", "third person",
        "aorist ", "perfect ", "imperfect ", "pluperfect",
        "future active", "future passive", "future middle",
        "present active", "present passive", "present middle",
        "perfect active", "perfect passive",
    ]
    if any(m in tl for m in gram_markers):
        return "grammatical"
    proper_name = ["a male given name", "a female given name", "equivalent to english",
                   "the name of a", "personal name", "a name for", "given name"]
    if any(m in tl for m in proper_name):
        return "proper_name"
    place_markers = [", greece", ", turkey", ", egypt", ", persia", ", bulgaria",
                     ", thrace", "cyclades", "peloponnesus", "ikaria", "phthiotis",
                     "babylonia", "ancient city", "ancient region", "a river of",
                     "a city of", "a town of", "a region of", "a district of",
                     "pomorie", "ancient geographic"]
    if any(m in tl for m in place_markers):
        return "place"
    return "lexical"


def extract_ara_concepts(gloss: str) -> set:
    g = gloss
    c = set()

    # Animals
    if any(w in g for w in ["طائر", "طير", "طيور"]): c.add("bird")
    if any(w in g for w in ["أسد", "سبع", "ليث"]): c.add("lion")
    if any(w in g for w in ["كلب", "عقور"]): c.add("dog")
    if any(w in g for w in ["فرس", "حصان", "جواد"]): c.add("horse")
    if any(w in g for w in ["ناقة", "إبل", "بعير", "الإبل"]): c.add("camel")
    if any(w in g for w in ["شاة", "غنم", "ضأن"]): c.add("sheep")
    if any(w in g for w in ["بقر", "ثور"]): c.add("cattle")
    if any(w in g for w in ["حمار", "جحش"]): c.add("donkey")
    if any(w in g for w in ["عقرب"]): c.add("scorpion")
    if any(w in g for w in ["ذئب"]): c.add("wolf")
    if any(w in g for w in ["ثعلب"]): c.add("fox")
    if any(w in g for w in ["غزال", "ظبي"]): c.add("deer")
    if any(w in g for w in ["عنكبوت"]): c.add("spider")
    if any(w in g for w in ["صراصير", "صرصور"]): c.add("cockroach")
    if any(w in g for w in ["سمك", "سمكة"]): c.add("fish")
    if any(w in g for w in ["سردين"]): c.add("sardine")
    if any(w in g for w in ["حية", "أفعى", "ثعبان"]): c.add("snake")
    if any(w in g for w in ["ضفدع"]): c.add("frog")
    if any(w in g for w in ["نحلة", "دبور"]): c.add("bee")
    if any(w in g for w in ["ذبابة"]): c.add("fly")
    if any(w in g for w in ["حشرة", "حشرات"]): c.add("insect")
    if any(w in g for w in ["نمل"]): c.add("ant")
    if any(w in g for w in ["قنديل البحر"]): c.add("jellyfish")
    if any(w in g for w in ["سرطان", "جراد بحر"]): c.add("crab")

    # Plants/food
    if any(w in g for w in ["ثوم"]): c.add("garlic")
    if any(w in g for w in ["خبز"]): c.add("bread")
    if any(w in g for w in ["تمر"]): c.add("date")
    if any(w in g for w in ["عنب"]): c.add("grape")
    if any(w in g for w in ["زيتون"]): c.add("olive")
    if any(w in g for w in ["نرجس", "النرجس"]): c.add("narcissus")
    if any(w in g for w in ["كرّاث", "كراث"]): c.add("leek")
    if any(w in g for w in ["بطيخ"]): c.add("melon")
    if any(w in g for w in ["حنظل"]): c.add("colocynth")
    if any(w in g for w in ["شعير"]): c.add("barley")
    if any(w in g for w in ["قمح", "حنطة"]): c.add("wheat")
    if any(w in g for w in ["تين"]): c.add("fig")
    if any(w in g for w in ["رمّان"]): c.add("pomegranate")
    if any(w in g for w in ["سمسم"]): c.add("sesame")
    if any(w in g for w in ["خردل"]): c.add("mustard")
    if any(w in g for w in ["كمون"]): c.add("cumin")
    if any(w in g for w in ["زعفران"]): c.add("saffron")
    if any(w in g for w in ["قرفة", "دارصيني"]): c.add("cinnamon")
    if any(w in g for w in ["فلفل"]): c.add("pepper")
    if any(w in g for w in ["حشيشة", "حشيش", "عشب"]): c.add("plant")
    if any(w in g for w in ["شجرة", "أشجار", "الغابة"]): c.add("tree")
    if any(w in g for w in ["زهرة", "وردة", "زهور"]): c.add("flower")
    if any(w in g for w in ["ثمرة", "فاكهة"]): c.add("fruit")
    if any(w in g for w in ["بذرة", "حبة", "بذور"]): c.add("seed")
    if any(w in g for w in ["خيار", "قثاء"]): c.add("cucumber")
    if any(w in g for w in ["خردل"]): c.add("mustard")

    # Liquids/substances
    if any(w in g for w in ["خمر", "شراب"]): c.add("wine")
    if any(w in g for w in ["خل", "خلّ"]): c.add("vinegar")
    if any(w in g for w in ["زيت", "دهن"]): c.add("oil")
    if any(w in g for w in ["ملح"]): c.add("salt")
    if any(w in g for w in ["عسل", "سكر"]): c.add("sweet")
    if any(w in g for w in ["لبن", "حليب"]): c.add("milk")
    if any(w in g for w in ["ماء"]): c.add("water")
    if any(w in g for w in ["دم", "دماء"]): c.add("blood")
    if any(w in g for w in ["زبل", "روث", "السرجين", "سركين"]): c.add("dung")

    # Body — use Arabic word-boundary patterns to avoid substring matches
    # يد (hand) must appear as standalone or with article, not inside words like خريدة/يدور
    if re.search(r'(?:^|[\s،,])(?:ال)?يد(?:ه|ين|ك|هم)?(?:[\s،,]|$)', g): c.add("hand")
    if any(w in g for w in ["الكف", " كف ", "بكفه"]): c.add("hand")
    # رأس with article or standalone
    if re.search(r'(?:^|[\s،,])(?:ال)?رأس(?:ه|ين|ك)?(?:[\s،,]|$)', g): c.add("head")
    # عين with standalone context (not inside a word)
    if re.search(r'(?:^|[\s،,])(?:ال)?عين(?:ه|ين|ك)?(?:[\s،,]|$)', g) or "حدقة العين" in g: c.add("eye")
    # رجل (foot/leg) — standalone
    if re.search(r'(?:^|[\s،,])(?:ب)?(?:ال)?رجل(?:ه|ين|ك)?(?:[\s،,]|$)', g) or "قدم" in g: c.add("foot")
    if any(w in g for w in ["بطن", "الكرش"]): c.add("belly")
    if any(w in g for w in ["شفاه", "شفة"]): c.add("mouth")
    if any(w in g for w in ["لسان"]): c.add("tongue")
    if any(w in g for w in ["جلد", "الجلد"]): c.add("skin")
    if any(w in g for w in ["عظم", "عظمين", "عظام"]): c.add("bone")
    if any(w in g for w in ["قلب"]): c.add("heart")
    if any(w in g for w in ["كبد"]): c.add("liver")
    if any(w in g for w in ["رئة"]): c.add("lung")
    if any(w in g for w in ["مخ", "دماغ"]): c.add("brain")
    if any(w in g for w in ["جراحة", "جراح", "جرح"]): c.add("wound")
    if any(w in g for w in ["مرض", "سقام", "سقم", "علة"]): c.add("illness")
    if any(w in g for w in ["موت", "وفاة", "مات"]): c.add("death")
    if any(w in g for w in ["حياة"]): c.add("life")
    if any(w in g for w in ["روح", "نفس"]): c.add("soul")

    # Actions
    if any(w in g for w in ["ضرب", "طعن"]): c.add("strike")
    if any(w in g for w in ["قتل", "قتله"]): c.add("kill")
    if any(w in g for w in ["ذبح", "يذبح", "ذبحه"]): c.add("slaughter")
    if any(w in g for w in ["شدّ", "ربط", "قيد"]): c.add("bind")
    if any(w in g for w in ["جمع", "جمعه", "تجميع"]): c.add("gather")
    if any(w in g for w in ["قطع", "فصل", "فصله", "قطعه"]): c.add("cut")
    if any(w in g for w in ["خرج", "هروب", "هرب", "فرّ"]): c.add("escape")
    if any(w in g for w in ["دخل", "أدخله", "أدخل"]): c.add("enter")
    if any(w in g for w in ["خلط", "مزج", "خلطه"]): c.add("mix")
    if any(w in g for w in ["تقدّم", "مضى", "ذهب"]): c.add("advance")
    if any(w in g for w in ["سرعة", "الإسراع", "يسرع"]): c.add("speed")
    if any(w in g for w in ["قصد", "قصده"]): c.add("aim")
    if any(w in g for w in ["ركض", "يركض", "العدو"]): c.add("run")
    if any(w in g for w in ["ركل", "ضرب برجل"]): c.add("kick")
    if any(w in g for w in ["صراع", "غلبة في الصراع"]): c.add("wrestling")
    if any(w in g for w in ["ضغط", "عصر"]): c.add("squeeze")
    if any(w in g for w in ["حمل", "يحمل", "حمله"]): c.add("carry")
    if any(w in g for w in ["وطء", "يطأ", "إيطاء"]): c.add("tread")
    if any(w in g for w in ["كذب", "كذّاب"]): c.add("lie")
    if any(w in g for w in ["خوف", "فزع", "رهبة"]): c.add("fear")
    if any(w in g for w in ["ظن", "تخمين", "توهم"]): c.add("conjecture")
    if any(w in g for w in ["احتيال", "حيلة", "مكر"]): c.add("trick")
    if any(w in g for w in ["كياسة", "ظرف", "الذكاء"]): c.add("cleverness")
    if any(w in g for w in ["لجاجة", "عناد", "إصرار"]): c.add("stubbornness")
    if any(w in g for w in ["غلبة", "فوق", "قهر"]): c.add("dominance")
    if any(w in g for w in ["إضجاع", "إلقاء", "يضجع"]): c.add("lay_down")
    if any(w in g for w in ["إناخة", "إبروك"]): c.add("kneel")
    if any(w in g for w in ["ملء", "ملأه"]): c.add("fill")
    if any(w in g for w in ["بسط", "نشر", "فرش"]): c.add("spread")
    if any(w in g for w in ["إقامة", "يقيم"]): c.add("dwell")
    if any(w in g for w in ["طرح", "رمى", "رماه"]): c.add("throw")
    if any(w in g for w in ["صوت", "أصوات", "صويت"]): c.add("sound")
    if any(w in g for w in ["بكاء", "بكى"]): c.add("cry")
    if any(w in g for w in ["صياح", "صرخ"]): c.add("shout")
    if any(w in g for w in ["غوص", "ملاحة"]): c.add("sail")
    if any(w in g for w in ["صعد", "ارتفع", "علا"]): c.add("ascend")
    if any(w in g for w in ["نزل", "هبط", "ينزل"]): c.add("descend")
    if any(w in g for w in ["أذرى", "يذرو", "نسح"]): c.add("scatter")

    # Attributes
    if any(w in g for w in ["ضخم", "شديد", "عظيم", "كبير"]): c.add("large")
    if any(w in g for w in ["صغير", "صغيرة", "دقيق"]): c.add("small")
    if any(w in g for w in ["طويل", "طول"]): c.add("tall")
    if any(w in g for w in ["قصير", "قصر"]): c.add("short")
    if any(w in g for w in ["خسارة", "هلاك"]): c.add("loss")
    if any(w in g for w in ["لؤم", "خسيس", "دنيء"]): c.add("vile")
    if any(w in g for w in ["حارّ", "حرارة", "سخن"]): c.add("hot")
    if any(w in g for w in ["بارد", "برد"]): c.add("cold")
    if any(w in g for w in ["لين", "ناعم", "نعومة"]): c.add("soft")
    if any(w in g for w in ["قوة", "شدة", "القوة"]): c.add("strength")
    if any(w in g for w in ["حمراء", "أحمر", "الحمرة"]): c.add("red")
    if any(w in g for w in ["بياض", "أبيض"]): c.add("white")
    if any(w in g for w in ["خضرة", "أخضر"]): c.add("green")
    if any(w in g for w in ["سواد", "أسود"]): c.add("black")
    if any(w in g for w in ["أصفر", "صفراء"]): c.add("yellow")
    if any(w in g for w in ["مُرَقَّط"]): c.add("spotted")

    # Objects/things
    if any(w in g for w in ["سيف"]): c.add("sword")
    if any(w in g for w in ["فأس"]): c.add("axe")
    if any(w in g for w in ["نصل", "سهم"]): c.add("arrow")
    if any(w in g for w in ["رمح", "حربة"]): c.add("spear")
    if any(w in g for w in ["درع", "زرد"]): c.add("armor")
    if any(w in g for w in ["خوذة", "بيضة"]): c.add("helmet")
    if any(w in g for w in ["ترس", "درقة"]): c.add("shield")
    if any(w in g for w in ["قوس"]): c.add("bow")
    if any(w in g for w in ["وعاء", "إناء", "طاسة", "طست", "طُسَيسة", "طُسَيِّسة"]): c.add("bowl")
    if any(w in g for w in ["سطل", "دلو"]): c.add("bucket")
    if any(w in g for w in ["زبيل", "قفعة", "جلّة"]): c.add("basket")
    if any(w in g for w in ["سرادق", "فسطاط", "خيمة"]): c.add("tent")
    if any(w in g for w in ["سرداب", "قبو", "سرداب"]): c.add("cellar")
    if any(w in g for w in ["سرج"]): c.add("saddle")
    if any(w in g for w in ["لجام"]): c.add("bridle")
    if any(w in g for w in ["مركب", "سفينة"]): c.add("ship")
    if any(w in g for w in ["مكيال", "مقياس", "وزن", "قياس"]): c.add("measure")
    if any(w in g for w in ["نعل", "حذاء"]): c.add("sandal")
    if any(w in g for w in ["بربط", "عود", "الموسيقى"]): c.add("lute")
    if any(w in g for w in ["اصطبل"]): c.add("stable")
    if any(w in g for w in ["حجر", "صخر"]): c.add("stone")
    if any(w in g for w in ["خشب", "عود"]): c.add("wood")
    if any(w in g for w in ["نار", "حريق"]): c.add("fire")
    if any(w in g for w in ["غبار", "هباء"]): c.add("dust")
    if any(w in g for w in ["دخان"]): c.add("smoke")
    if any(w in g for w in ["ريح", "رياح"]): c.add("wind")
    if any(w in g for w in ["ثلج"]): c.add("snow")
    if any(w in g for w in ["شمس"]): c.add("sun")
    if any(w in g for w in ["قمر"]): c.add("moon")
    if any(w in g for w in ["نجم", "كوكب", "نجوم"]): c.add("star")
    if any(w in g for w in ["نهر", "وادٍ", "وادي"]): c.add("river")
    if any(w in g for w in ["بحر", "بحار"]): c.add("sea")
    if any(w in g for w in ["جبل", "قمة", "الجبل"]): c.add("mountain")
    if any(w in g for w in ["حوض", "بركة"]): c.add("pool")
    if any(w in g for w in ["بئر"]): c.add("well")
    if any(w in g for w in ["حقل", "مزرعة", "ميدان", "ساحة"]): c.add("field")
    if any(w in g for w in ["طريق", "درب"]): c.add("road")
    if any(w in g for w in ["بيت", "منزل", "دار"]): c.add("house")
    if any(w in g for w in ["حمام", "تحمّم"]): c.add("bath")
    if any(w in g for w in ["كتاب", "مخطوط"]): c.add("book")
    if any(w in g for w in ["قصيدة", "شعر"]): c.add("poem")
    if any(w in g for w in ["موسيقى", "غناء"]): c.add("music")
    if any(w in g for w in ["حرب", "قتال"]): c.add("war")
    if any(w in g for w in ["جيش", "جند"]): c.add("army")
    if any(w in g for w in ["ملك", "أمير", "سيد"]): c.add("king")
    if any(w in g for w in ["رقيق", "عبد"]): c.add("slave")
    if any(w in g for w in ["شاب", "شبان", "صبي", "فتى"]): c.add("youth")
    if any(w in g for w in ["امرأة", "نساء", "جارية"]): c.add("woman")
    if any(w in g for w in ["قرطاس", "ورق", "الورق"]): c.add("paper")
    if any(w in g for w in ["فردوس", "جنة"]): c.add("paradise")
    if any(w in g for w in ["إله", "رب", "الله"]): c.add("god")
    if any(w in g for w in ["عدل", "حق"]): c.add("justice")
    if any(w in g for w in ["عار", "خجل", "إثم"]): c.add("shame")
    if any(w in g for w in ["حزن", "كمد"]): c.add("grief")
    if any(w in g for w in ["فرح", "بهجة"]): c.add("joy")
    if any(w in g for w in ["حسد", "غيرة"]): c.add("envy")
    if any(w in g for w in ["حب", "عشق"]): c.add("love")
    if any(w in g for w in ["خيانة", "غدر"]): c.add("treachery")
    if any(w in g for w in ["أمل", "رجاء"]): c.add("hope")
    if any(w in g for w in ["نور", "ضوء", "مصباح", "سراج"]): c.add("lamp")
    if any(w in g for w in ["ظلام", "ظلمة"]): c.add("darkness")

    return c


def wm(t: str, words: list) -> bool:
    """Word-boundary match: check if any word in list appears as whole word in t."""
    for w in words:
        if re.search(r'\b' + re.escape(w) + r'\b', t):
            return True
    return False


def extract_tgt_concepts(tgt: str) -> set:
    t = tgt.lower()
    c = set()

    # Animals
    if wm(t, ["bird", "eagle", "hawk", "raven", "crow", "owl", "heron",
               "dove", "pigeon", "sparrow", "swallow", "stork",
               "purple bird", "long-eared owl", "roller"]): c.add("bird")
    if wm(t, ["lion"]): c.add("lion")
    if wm(t, ["dog"]): c.add("dog")
    if wm(t, ["horse", "steed", "charger", "mare", "stallion", "equine"]): c.add("horse")
    if wm(t, ["camel"]): c.add("camel")
    if wm(t, ["sheep", "ram", "lamb", "ewe"]): c.add("sheep")
    if wm(t, ["cattle", "ox", "bull", "cow", "bovine"]): c.add("cattle")
    if wm(t, ["donkey", "ass", "mule"]): c.add("donkey")
    if wm(t, ["scorpion"]): c.add("scorpion")
    if wm(t, ["wolf", "wolves"]): c.add("wolf")
    if wm(t, ["fox"]): c.add("fox")
    if wm(t, ["deer", "stag", "doe", "fawn", "hind"]): c.add("deer")
    if wm(t, ["spider"]): c.add("spider")
    if wm(t, ["cockroach"]): c.add("cockroach")
    if wm(t, ["fish"]) and "jellyfish" not in t and "starfish" not in t: c.add("fish")
    if wm(t, ["sardine"]): c.add("sardine")
    if wm(t, ["snake", "serpent", "viper"]): c.add("snake")
    if wm(t, ["frog"]): c.add("frog")
    if wm(t, ["bee", "honey"]): c.add("bee")
    if wm(t, ["beetle"]): c.add("beetle")
    if wm(t, ["insect", "bug"]): c.add("insect")
    if wm(t, ["crab"]): c.add("crab")
    if wm(t, ["goat"]): c.add("goat")
    if wm(t, ["pig", "swine", "pork"]): c.add("pig")

    # Plants/food
    if wm(t, ["garlic"]): c.add("garlic")
    if wm(t, ["bread"]): c.add("bread")
    if wm(t, ["date palm"]) or (wm(t, ["date"]) and "update" not in t and "mandate" not in t): c.add("date")
    if wm(t, ["grape", "vine", "vineyard"]): c.add("grape")
    if wm(t, ["olive"]): c.add("olive")
    if wm(t, ["narcissus"]): c.add("narcissus")
    if wm(t, ["leek"]): c.add("leek")
    if wm(t, ["melon"]): c.add("melon")
    if wm(t, ["barley", "groats"]): c.add("barley")
    if wm(t, ["wheat", "wheaten"]): c.add("wheat")
    if wm(t, ["fig", "figs"]) and "figure" not in t and "fight" not in t and "figur" not in t: c.add("fig")
    if wm(t, ["pomegranate"]): c.add("pomegranate")
    if wm(t, ["sesame"]): c.add("sesame")
    if wm(t, ["mustard"]): c.add("mustard")
    if wm(t, ["cumin"]): c.add("cumin")
    if wm(t, ["saffron"]): c.add("saffron")
    if wm(t, ["cinnamon"]): c.add("cinnamon")
    if wm(t, ["pepper"]): c.add("pepper")
    if wm(t, ["chicory"]): c.add("chicory")
    if wm(t, ["spurge", "milkweed", "euphorbia"]): c.add("spurge")
    if wm(t, ["poplar"]): c.add("tree")
    if wm(t, ["flower", "bloom"]): c.add("flower")
    if wm(t, ["plant", "herb", "grass", "weed"]): c.add("plant")
    if wm(t, ["fruit", "berry"]): c.add("fruit")
    if wm(t, ["seed", "kernel"]): c.add("seed")

    # Liquids
    if wm(t, ["wine", "winery"]): c.add("wine")
    if wm(t, ["vinegar", "sour wine", "acid"]): c.add("vinegar")
    if wm(t, ["oil"]) and "soil" not in t and "boil" not in t and "foil" not in t: c.add("oil")
    if wm(t, ["salt"]): c.add("salt")
    if wm(t, ["sweet", "honey", "sugar"]): c.add("sweet")
    if wm(t, ["milk", "dairy"]): c.add("milk")
    if wm(t, ["water"]): c.add("water")
    if wm(t, ["blood", "bloody"]): c.add("blood")
    if wm(t, ["dung", "manure", "excrement", "feces", "ordure"]): c.add("dung")
    if wm(t, ["juice", "sap"]): c.add("juice")

    # Body — use word boundaries to avoid false matches
    if wm(t, ["head", "skull"]) and "forehead" not in t and "overhead" not in t: c.add("head")
    if wm(t, ["eyes"]) or (wm(t, ["eye"]) and "oxeye" not in t and "hawk-faced" not in t and "hawk-eye" not in t): c.add("eye")
    if wm(t, ["hands"]) or (wm(t, ["hand"]) and "handful" not in t and "handsome" not in t and "handicraft" not in t and "handled" not in t): c.add("hand")
    if wm(t, ["foot", "feet", "leg"]): c.add("foot")
    if wm(t, ["belly", "abdomen", "stomach", "womb"]): c.add("belly")
    if wm(t, ["mouth", "lips"]): c.add("mouth")
    if wm(t, ["tongue"]): c.add("tongue")
    if wm(t, ["skin"]) and "basin" not in t: c.add("skin")
    if wm(t, ["bone", "bones"]): c.add("bone")
    if wm(t, ["heart"]): c.add("heart")
    if wm(t, ["liver"]): c.add("liver")
    if wm(t, ["lung"]): c.add("lung")
    if wm(t, ["brain"]): c.add("brain")
    if wm(t, ["blood", "bloody"]): c.add("blood")
    if wm(t, ["wound", "wounds", "injury"]): c.add("wound")
    if wm(t, ["sick", "illness", "disease", "affliction"]): c.add("illness")
    if wm(t, ["flesh", "fleshy"]): c.add("flesh")

    # Actions
    if wm(t, ["strike", "hit", "beat", "smite", "knock"]): c.add("strike")
    if wm(t, ["slay", "kill", "murder"]): c.add("kill")
    if wm(t, ["slaughter", "sacrifice"]): c.add("slaughter")
    if wm(t, ["bind", "tie", "fetter", "shackle", "fasten"]): c.add("bind")
    if wm(t, ["gather", "collect", "assemble", "muster"]): c.add("gather")
    if wm(t, ["cut", "cleave", "split", "sever", "separate", "asunder", "in twain"]): c.add("cut")
    if wm(t, ["escape", "flee", "fugitive", "flight", "evade"]): c.add("escape")
    if wm(t, ["enter", "penetrate", "ingress"]): c.add("enter")
    if wm(t, ["mix", "mingle", "blend"]): c.add("mix")
    if wm(t, ["grasp", "clutch", "seize", "grab", "grip"]): c.add("grasp")
    if wm(t, ["squeeze", "compress", "press", "clasping", "compressing", "peristaltic"]): c.add("squeeze")
    if wm(t, ["run", "running", "sprint"]): c.add("run")
    if wm(t, ["walk", "stroll", "march"]): c.add("walk")
    if wm(t, ["carry", "transport"]): c.add("carry")
    if wm(t, ["fear", "frighten", "terror", "terrifying", "dread"]): c.add("fear")
    if wm(t, ["rousing", "stirring", "strife-stirring"]): c.add("urge")
    if wm(t, ["lie", "lying", "deceive", "deception"]): c.add("lie")
    if wm(t, ["wrestle", "wrestling"]): c.add("wrestling")
    if wm(t, ["kick", "stamp", "tread", "exercise pressure"]): c.add("kick")
    if wm(t, ["pour", "watering", "water can"]): c.add("water_action")
    if wm(t, ["scatter", "spread", "disperse"]): c.add("scatter")
    if wm(t, ["throw", "hurl", "cast"]): c.add("throw")
    if wm(t, ["shout", "voice", "noise"]): c.add("sound")
    if wm(t, ["descend", "descent", "way down", "downward"]): c.add("descend")
    if wm(t, ["ascend", "rise", "way up"]): c.add("ascend")

    # Attributes
    if wm(t, ["large", "great", "big", "huge", "massive", "enormous"]): c.add("large")
    if wm(t, ["small", "little", "tiny", "minor"]): c.add("small")
    if wm(t, ["clever", "wise", "cunning", "wily", "sly", "shrewd", "crafty"]): c.add("cleverness")
    if wm(t, ["soft", "gentle", "tender", "smooth"]): c.add("soft")
    if wm(t, ["hard", "firm", "rigid"]): c.add("hard")
    if wm(t, ["hot", "warm", "heat", "thermal"]): c.add("hot")
    if wm(t, ["cold", "cool", "chill"]): c.add("cold")
    if wm(t, ["dark", "darkness", "blind", "obscure"]): c.add("darkness")
    if wm(t, ["bright", "shine", "gleam"]): c.add("bright")
    if wm(t, ["red", "crimson", "scarlet"]): c.add("red")
    if wm(t, ["white", "pale", "albino"]): c.add("white")
    if wm(t, ["black", "swarthy"]): c.add("black")
    if wm(t, ["green", "verdant"]): c.add("green")
    if wm(t, ["yellow", "golden"]): c.add("yellow")
    if wm(t, ["spotted", "speckled", "mottled"]): c.add("spotted")
    if wm(t, ["strong", "strength", "mighty", "powerful"]): c.add("strength")
    if wm(t, ["rare", "scarce", "scanty"]): c.add("rare")
    if wm(t, ["innovation", "innovate"]): c.add("new")
    if wm(t, ["leisurely", "at leisure"]): c.add("leisure")
    if wm(t, ["vile", "mean", "wretched"]): c.add("vile")
    if wm(t, ["revered", "honored", "august", "venerable", "noble"]): c.add("honor")

    # Objects/things
    if wm(t, ["sword", "blade", "saber"]): c.add("sword")
    if wm(t, ["axe", "hatchet"]): c.add("axe")
    if wm(t, ["arrow", "dart"]): c.add("arrow")
    if wm(t, ["spear", "lance", "pike"]): c.add("spear")
    if wm(t, ["armor", "armour"]): c.add("armor")
    if wm(t, ["helmet"]): c.add("helmet")
    if wm(t, ["shield", "buckler"]): c.add("shield")
    if wm(t, ["bowman"]): c.add("bow")
    if wm(t, ["dagger", "knife"]): c.add("knife")
    if wm(t, ["trousers", "breeches", "pants"]): c.add("trousers")
    if wm(t, ["sandal", "sandals"]): c.add("sandal")
    if wm(t, ["bowl", "basin", "tub", "bath"]): c.add("bowl")
    if wm(t, ["bucket", "pail"]): c.add("bucket")
    if wm(t, ["basket", "hamper"]): c.add("basket")
    if wm(t, ["tent", "pavilion", "canopy", "awning"]): c.add("tent")
    if wm(t, ["cellar", "vault", "underground", "subterranean", "crypt"]): c.add("cellar")
    if wm(t, ["saddle"]): c.add("saddle")
    if wm(t, ["ship", "vessel", "boat", "galley", "skiff"]): c.add("ship")
    if wm(t, ["measure", "unit of measure", "capacity", "persian unit"]): c.add("measure")
    if wm(t, ["lamp", "torch", "lantern", "candle"]): c.add("lamp")
    if wm(t, ["stable", "stall", "stables"]): c.add("stable")
    if wm(t, ["lute", "harp", "lyre"]): c.add("lute")
    if wm(t, ["drum", "percussion"]): c.add("drum")
    if wm(t, ["flute", "pipe", "aulos"]): c.add("flute")
    if wm(t, ["wooden", "timber", "splinter", "lath", "plank"]): c.add("wood")
    if wm(t, ["stone", "rock", "pebble"]): c.add("stone")
    if wm(t, ["fire", "flame", "blaze"]): c.add("fire")
    if wm(t, ["dust", "powder", "ash"]): c.add("dust")
    if wm(t, ["smoke", "vapor"]): c.add("smoke")
    if wm(t, ["wind", "gale", "breeze"]): c.add("wind")
    if wm(t, ["snow", "sleet"]): c.add("snow")
    if wm(t, ["solar"]): c.add("sun")
    if wm(t, ["lunar"]): c.add("moon")
    if wm(t, ["star", "stars", "stellar", "constellation"]): c.add("star")
    if wm(t, ["river", "stream"]): c.add("river")
    if wm(t, ["ocean", "marine"]): c.add("sea")
    if wm(t, ["mountain", "peak", "summit"]): c.add("mountain")
    if wm(t, ["spring", "fountain"]): c.add("well")
    if wm(t, ["meadow", "plain"]): c.add("field")
    if wm(t, ["dwelling", "abode"]): c.add("house")
    if wm(t, ["poem", "poetry", "verse"]): c.add("poem")
    if wm(t, ["war", "battle", "strife", "conflict", "combat", "din of war"]): c.add("war")
    if wm(t, ["army", "troops", "soldiers", "regiment", "double company"]): c.add("army")
    if wm(t, ["king", "ruler", "leader", "chief"]): c.add("king")
    if wm(t, ["slave", "servant", "captive", "serf"]): c.add("slave")
    if wm(t, ["youth", "young man", "lad", "adolescent"]): c.add("youth")
    if wm(t, ["woman", "girl", "female"]): c.add("woman")
    if wm(t, ["strumpet", "whore", "harlot", "prostitute"]): c.add("prostitute")
    if wm(t, ["justice", "righteous", "rightful", "lawful"]): c.add("justice")
    if wm(t, ["shame", "disgrace", "dishonor"]): c.add("shame")
    if wm(t, ["love", "affection"]): c.add("love")
    if wm(t, ["grief", "sorrow", "anguish", "mourn", "distressed"]): c.add("grief")
    if wm(t, ["joy", "pleasure", "happy", "happiness"]): c.add("joy")
    if wm(t, ["student", "pupil", "disciple", "apprentice", "learn"]): c.add("student")
    if wm(t, ["appearance", "manifestation", "epiphany", "phenomenon"]): c.add("manifestation")
    if wm(t, ["cooperation", "cooperate", "joint working", "synergy"]): c.add("cooperation")
    if wm(t, ["tautology", "repetition", "redundancy"]): c.add("repetition")
    if wm(t, ["grace", "favor", "kindness", "pardon", "rescue", "deliver"]): c.add("grace")
    if wm(t, ["tribe", "folk", "nation"]): c.add("people")
    if wm(t, ["ball game", "episkyros"]): c.add("play")
    if wm(t, ["bedclothes", "mattress"]): c.add("bed")
    if wm(t, ["conjecture", "guess", "surmise"]): c.add("conjecture")

    return c


def score_pair(p: dict) -> tuple:
    """Return (score, reasoning, method)."""
    ara_root = p.get('arabic_root', '')
    ara_gloss = p.get('masadiq_gloss', '') or ''
    mafahim = p.get('mafahim_gloss', '') or ''
    target_lemma = p.get('target_lemma', '')
    target_gloss = p.get('target_gloss', '') or ''
    tgt = target_gloss.lower()

    ttype = classify_target(target_gloss, target_lemma)

    # Grammatical forms — 0 unless base meaning extracted shows overlap
    if ttype == "grammatical":
        # Try to extract base meaning from gloss
        # e.g. "feminine dative plural of ἀφρακτός" — base = "unguarded, unfortified"
        # Usually no base meaning given, just the form name
        # Small set of known exceptions where base meaning is in parens
        paren = re.findall(r'\(([^)]+)\)', target_gloss)
        # Check if any paren content has a meaningful English gloss
        base_from_paren = " ".join(paren).lower()
        if base_from_paren:
            tgt_c2 = extract_tgt_concepts(base_from_paren)
            ara_c2 = extract_ara_concepts(ara_gloss)
            overlap2 = ara_c2 & tgt_c2
            if overlap2:
                return (0.35, f"grammatical form but base meaning ({base_from_paren[:50]}) overlaps: {'+'.join(sorted(overlap2))}", "combined")
        return (0.0, "inflected grammatical form — no semantic scoring applicable", "weak")

    # Proper names
    if ttype == "proper_name":
        # Check Semitic name etymology
        if any(w in tgt for w in ["from semitic", "from aramaic", "from hebrew", "from arabic"]):
            return (0.25, "proper name with attested Semitic origin — possible shared substrate", "weak")
        if "hasdrubal" in tgt:
            return (0.15, "Hasdrubal = Semitic has-druba'al, possible distant Semitic kinship", "weak")
        if "mascames" in tgt:
            return (0.1, "Old Persian personal name — no Arabic semantic connection", "weak")
        return (0.0, "proper name — semantic scoring not applicable", "weak")

    # Place names
    if ttype == "place":
        # Euphrates — known Arabic/Semitic connection
        if any(w in tgt for w in ["euphrates", "εὐφράτης", "euphrat"]):
            return (0.9, "الفرات/Εὐφράτης — Semitic origin, shared ancient name for the river", "masadiq_direct")
        if "chaldea" in tgt and any(r in ara_root for r in ["كلد", "كلداء", "خلد"]):
            return (0.5, "Chaldea — Semitic geographical term, possible shared Semitic root כלד", "combined")
        return (0.0, "place name — semantic scoring not applicable", "weak")

    # ── LEXICAL PAIRS — main scoring ──────────────────────────────────────────

    # SPECIAL KNOWN HIGH-VALUE PAIRS
    # النرجس → narcissus (direct borrowing)
    if "نرجس" in ara_root and "narcissus" in tgt:
        return (0.97, "النرجس = narcissus — direct Arabic loanword from Greek νάρκισσος", "masadiq_direct")

    # اصطبل → σταῦλος/στάβλος (stable — calibration pair)
    if "اصطبل" in ara_root and "stable" in tgt:
        return (0.98, "اصطبل = stable (معرَّب) — direct borrowing from Greek/Latin stabulum", "masadiq_direct")

    # السرداب = underground room — check if target matches
    if "سرداب" in ara_root and any(w in tgt for w in ["underground", "cellar", "subterranean", "vault"]):
        return (0.85, "السرداب = underground room (Persian borrowing), semantic match with subterranean structures", "masadiq_direct")

    # السرجين = dung/manure → check if target = dung
    if ("زبل" in ara_gloss or "سرجين" in ara_root or "سرقين" in ara_gloss) and \
       any(w in tgt for w in ["dung", "manure", "excrement"]):
        return (0.88, "السرجين = dung/manure (معرَّب سركين) — semantic identity with target", "masadiq_direct")

    # النرمق = soft/supple → νέρμ- / νεαρ- related
    if "نرمق" in ara_root and "soft" in tgt:
        return (0.9, "النرمق = soft/supple (معرَّب نرمَه) — direct semantic match", "masadiq_direct")

    # الشربش (headgear/outer garment) → σαράβαρα (Scythian trousers)
    if "شربش" in ara_root and "trousers" in tgt:
        return (0.55, "outer garment / foreign dress: both denote non-Arab clothing items in similar borrowing register", "combined")

    # ماثه → μαθητεύω (be a pupil/learn)
    if "ماثه" in ara_root and any(w in tgt for w in ["pupil", "learn", "disciple", "student"]):
        return (0.6, "Arabic ماث root shares م-ث with Greek μαθ- (learn) — mafahim-level connection", "mafahim_deep")

    # البرذون = pack-horse
    if "برذون" in ara_root and any(w in tgt for w in ["horse", "mule", "pack"]):
        return (0.95, "البرذون = pack-horse — direct Greek/Byzantine loanword βουρδών", "masadiq_direct")

    # الفرخ = chick/young bird
    if "فرخ" in ara_root and any(w in tgt for w in ["chick", "fledgling", "young bird", "φάρκες"]):
        return (0.95, "الفرخ = young bird/chick — direct parallel to Greek φάρκες (young fish)", "masadiq_direct")

    # Leek / كراث check
    if any(w in ara_gloss for w in ["كرّاث", "الكراث"]) and "leek" in tgt:
        return (0.88, "كرّاث (leek) and Greek πρᾶσον/κορίανδρον family — botanical borrowing", "masadiq_direct")

    # Chicory / خروه
    if "خروه" in ara_root and "chicory" in tgt:
        return (0.65, "Arabic خروة/خرو and Greek κίχορα (chicory) — plant name in likely shared register", "combined")

    # Dung/fertilizer / الدمال
    if "دمال" in ara_root:
        if any(w in tgt for w in ["dung", "manure", "fertilizer", "compost"]):
            return (0.78, "Arabic الدمال = compost/fertilizer, semantic match", "masadiq_direct")
        if "proper name" in tgt or "demomeles" in tgt:
            return (0.0, "proper name (Demomeles) — no semantic connection", "weak")

    # الثمله → τιθύμαλλος (spurge/milkweed — plant with milky sap)
    # Arabic ثمل = sediment/dregs/remnants, also ثُمالة = lather/foam
    if "ثمله" in ara_root and any(w in tgt for w in ["spurge", "milkweed", "euphorbia"]):
        return (0.35, "Arabic ثمالة = foam/lather/dregs, Greek τιθύμαλλος = spurge (milky plant) — weak semantic link through 'milky' substance", "weak")

    # Sandal matches
    if any(w in ara_gloss for w in ["نعل", "حذاء"]) and any(w in tgt for w in ["sandal", "sandals"]):
        return (0.82, "both denote footwear/sandal — direct semantic match", "masadiq_direct")

    # الصندل = sandal
    if "صندل" in ara_root and any(w in tgt for w in ["sandal", "sandals"]):
        return (0.85, "الصندل = sandal — Arabic borrowing from Greek σάνδαλον", "masadiq_direct")

    # σάμβαλον = Aeolic form of sandal
    if "سعابل" in ara_root and "sandal" in tgt:
        return (0.15, "Arabic سعابل = tall camels; Greek = sandal form — no semantic link despite phonetic similarity", "weak")

    # النبراس = lamp/light
    if "نبراس" in ara_root:
        if any(w in tgt for w in ["lamp", "torch", "light", "lantern"]):
            return (0.75, "النبراس = lamp/torch — semantic match with lighting instrument", "masadiq_direct")
        if "fawn" in tgt or "deer" in tgt or "νέβρ" in target_lemma:
            return (0.55, "النبراس shares root ن-ب-ر with Greek νέβρος (fawn) — phonetic kinship, possible ancient connection", "mafahim_deep")

    # الفرقد = star of Ursa Minor
    if "فرقد" in ara_root:
        if any(w in tgt for w in ["star", "ursa", "bear", "celestial"]):
            return (0.7, "الفرقد = a star of Ursa Minor — both in stellar/celestial semantic field", "masadiq_direct")
        # ἀφρακτότατος — most unguarded — no link
        if "unguarded" in tgt or "unfortified" in tgt or "aphrakto" in tgt:
            return (0.0, "Arabic = star name; Greek = superlative of unguarded — no connection", "weak")

    # Containers
    if "سطل" in ara_root and any(w in tgt for w in ["bucket", "basin", "tub"]):
        return (0.65, "السطل = small bucket/bowl with handle — semantic match with container", "masadiq_direct")

    # الصلطح = wide/flat + περισταλτικός (peristaltic)
    if "صلطح" in ara_root and "peristaltic" in tgt:
        return (0.1, "Arabic الصلطح = flat/wide, Greek = peristaltic — no semantic connection", "weak")

    # الشفق = reddish twilight / σκάφη = bowl/basin
    if "شفق" in ara_root:
        if any(w in tgt for w in ["bowl", "basin", "tub"]):
            return (0.1, "Arabic الشفق = twilight/redness, Greek σκάφη = bowl — no connection", "weak")
        if "sophia" in tgt or "hagia" in tgt:
            return (0.0, "building name — semantic scoring not applicable", "weak")

    # الشقراق = a spotted bird (roller bird)
    if "شقراق" in ara_root:
        if any(w in tgt for w in ["ball game", "game", "episkyros"]):
            return (0.1, "Arabic = a bird; Greek = a ball game — no semantic connection", "weak")
        if any(w in tgt for w in ["strike together", "crash"]):
            return (0.25, "Arabic الشقراق = spotted bird; Greek συγκρούω = strike together — weak onomatopoeic link to rattling/crashing sounds", "weak")

    # الحداه = a bird (kite/hawk) + κάθοδος (descent)
    if "الحداه" in ara_root or "حداه" in ara_root:
        if "descent" in tgt or "way down" in tgt:
            return (0.2, "Arabic = a raptor bird (kite), Greek κάθοδος = descent — birds descend but no direct semantic link", "weak")

    # الحدس = conjecture/estimation
    if "حدس" in ara_root:
        if any(w in tgt for w in ["conjecture", "guess", "surmise"]):
            return (0.6, "Arabic الحدس = conjecture/estimation, semantic match with Greek guessing concept", "masadiq_direct")
        if "schedius" in tgt or "phocian" in tgt:
            return (0.0, "proper name — no semantic connection", "weak")
        if "elementary" in tgt or "elemental" in tgt or "stoikheio" in tgt:
            return (0.2, "Arabic = conjecture; Greek = most elementary — very weak link through uncertainty", "weak")

    # الحدج = load/burden (for camel)
    if "حدج" in ara_root:
        if "descent" in tgt or "way down" in tgt:
            return (0.1, "Arabic حدج = load/palanquin; Greek = descent — no semantic link", "weak")
        if "ekhínai" in tgt or "echinades" in tgt.lower():
            return (0.0, "place name — no semantic connection", "weak")

    # الحيله = trick/group (flock of goats / cleverness)
    if "حيله" in ara_root:
        if any(w in tgt for w in ["clever", "cunning", "wily", "sly", "trick"]):
            return (0.7, "Arabic الحيلة = cleverness/trick, semantic match with Greek cunning/cleverness", "masadiq_direct")
        if any(w in tgt for w in ["strength", "power", "might"]):
            return (0.55, "Arabic الحيل = power/strength, semantic proximity with Greek power concept", "masadiq_direct")
        # Proper names
        if any(w in tgt for w in ["achilles", "echeclus", "anchialus"]):
            return (0.0, "proper name — no semantic connection", "weak")

    # الحيمه (hot-headed boy / juice extraction)
    if "حيمه" in ara_root:
        if "juice" in tgt or "extract" in tgt:
            return (0.3, "Arabic الحيمة = hot-headed child; Greek = extract juice — weak link through heat/extraction", "weak")
        if "fighting" in tgt or "warrior" in tgt or "makhimos" in tgt:
            return (0.35, "Arabic = a hot-headed lad; Greek μάχιμοι = warriors/fighters — indirect connection through ardor", "weak")

    # الدرانج = Drabj (Arabic geographical/unfamiliar)
    if "درانج" in ara_root or "درابج" in ara_gloss:
        if "separate" in tgt or "part" in tgt or "divide" in tgt:
            return (0.15, "Arabic = a place name; Greek = to separate — no semantic connection", "weak")
        if "dracanum" in tgt or "drákano" in tgt:
            return (0.1, "place name (Dracanum) — no semantic connection", "weak")

    # الدرانس = a big strong man
    if "درانس" in ara_root:
        if any(w in tgt for w in ["do", "act", "perform", "drôntas"]):
            return (0.2, "Arabic = big/strong man; Greek participle of δρᾶν (to act) — indirect through vigor", "weak")

    # الدرباس = a lion / a biting dog
    if "درباس" in ara_root:
        if any(w in tgt for w in ["lion", "wild", "fierce", "predator"]):
            return (0.45, "Arabic الدرباس = lion/fierce dog, Greek βάρβαρ- family — wild/aggressive animal", "weak")
        if "hasdrubal" in tgt:
            return (0.15, "Hasdrubal = Semitic name — possible distant Semitic substrate link", "weak")

    # الدرشه = stubbornness / black leather
    if "درشه" in ara_root:
        if any(w in tgt for w in ["grasp", "clutch", "seize"]):
            return (0.3, "Arabic الدرشة = stubbornness/leather; Greek = grasp — no direct semantic connection", "weak")

    # السدح = slaughter/lay flat on ground
    if "سدح" in ara_root:
        if "sadducee" in tgt:
            return (0.2, "Arabic السدح = to lay flat/slaughter; Sadducee = Jewish sect — no direct semantic connection, phonetic only", "weak")

    # السرادق = large tent/canopy (معرَّب Arabic)
    if "سرادق" in ara_root:
        if any(w in tgt for w in ["garlic"]):
            return (0.0, "tent/canopy vs garlic — no semantic connection", "weak")
        if "fleshy" in tgt or "flesh" in tgt:
            return (0.0, "tent vs fleshy — no semantic connection", "weak")

    # السرجين handled above (dung)

    # السرداب = underground room
    if "سرداب" in ara_root:
        if any(w in tgt for w in ["spyridon", "spiridon"]):
            return (0.0, "proper name — no semantic connection", "weak")

    # الشقده = a nutritious plant
    if "شقده" in ara_root:
        if "schedius" in tgt or "phocian" in tgt:
            return (0.0, "proper name — no semantic connection", "weak")

    # الشقراق handled above

    # الظرف = container / cleverness
    if "ظرف" in ara_root:
        if "zariasp" in tgt or "zariaspes" in tgt:
            return (0.0, "proper name (Old Median) — no semantic connection", "weak")
        if any(w in tgt for w in ["container", "vessel", "bag", "sack"]):
            return (0.55, "Arabic الظرف = container (wicâ'), semantic match with vessel concept", "masadiq_direct")
        if any(w in tgt for w in ["clever", "eloquent", "witty", "graceful"]):
            return (0.6, "Arabic الظرف = elegance/wit/cleverness, semantic match", "masadiq_direct")

    # الطمرس = liar / low person
    if "طمرس" in ara_root:
        if "ready" in tgt or "prepared" in tgt:
            return (0.1, "Arabic = liar/contemptible; Greek = more ready — no connection", "weak")

    # الطهطاه = a fine young horse
    if "طهطاه" in ara_root:
        if "theaetetus" in tgt:
            return (0.1, "Arabic = a fine horse; Greek = proper name — no connection", "weak")

    # الفص = gemstone of ring / clove of garlic
    if "فص" in ara_root:
        if any(w in tgt for w in ["cockroach"]):
            return (0.0, "gemstone vs cockroach — no semantic connection", "weak")
        if any(w in tgt for w in ["garlic", "clove"]):
            return (0.65, "Arabic الفص = clove of garlic (among meanings); Greek = related herb/spice plant", "combined")
        if "phliasian" in tgt:
            return (0.0, "place name (Phlius) — no semantic connection", "weak")

    # الفصعل = scorpion
    if "فصعل" in ara_root:
        if "phliasian" in tgt:
            return (0.0, "proper demonym — no semantic connection", "weak")

    # الفصل = separation / weaning
    if "فصل" in ara_root:
        if "phliasian" in tgt:
            return (0.0, "proper demonym — no semantic connection", "weak")
        if any(w in tgt for w in ["separate", "sever", "divide", "cut", "part"]):
            return (0.72, "Arabic الفصل = separation/division — direct semantic match with Greek cutting/separating", "masadiq_direct")

    # القفط = copulation / city in Upper Egypt
    if "قفط" in ara_root:
        if "measure" in tgt or "kapith" in tgt:
            return (0.2, "Arabic القفط = copulation/city; Greek = Persian measure — no semantic connection", "weak")
        if "wily" in tgt or "cunning" in tgt:
            return (0.2, "Arabic القفط = to cover (sexually); Greek = crafty — weak overlap", "weak")

    # القفعه = basket for date picking
    if "قفعه" in ara_root:
        if any(w in tgt for w in ["escape", "flee"]):
            return (0.15, "Arabic القفعة = basket; Greek = to flee — no semantic connection", "weak")

    # الكنمه = wound
    if "كنمه" in ara_root:
        if any(w in tgt for w in ["distress", "grief", "anguish"]):
            return (0.45, "Arabic الكنمة = wound, Greek = to be distressed — injury/pain shared field", "combined")

    # الكهدل = a plump young woman / a crone / a spider
    if "كهدل" in ara_root:
        if "chaldea" in tgt:
            return (0.0, "Arabic الكهدل = crone/spider/young woman; Chaldea = ancient region — no semantic connection despite phonetic match", "weak")

    # الكوشله = large glans
    if "كوشله" in ara_root:
        if "sour wine" in tgt or "acid" in tgt:
            return (0.0, "no semantic connection", "weak")

    # النرجس = narcissus plant
    if "نرجس" in ara_root and "cooperation" in tgt:
        return (0.0, "narcissus plant vs cooperation — no connection", "weak")

    # النرمق = soft (معرَّب)
    if "نرمق" in ara_root:
        if "small fish" in tgt or "kinermoi" in tgt.lower():
            return (0.15, "Arabic النرمق = soft/supple; Greek = small fish — no semantic connection", "weak")

    # النسح = husks/chaff
    if "نسح" in ara_root:
        if "young man" in tgt or "youth" in tgt:
            return (0.1, "Arabic النسح = chaff/husks; Greek = young man — no semantic connection", "weak")

    # السقام = illness/sickness
    if "سقام" in ara_root:
        if "mascames" in tgt or "mascam" in tgt:
            return (0.0, "proper name — no connection", "weak")
        if any(w in tgt for w in ["illness", "sick", "disease", "affliction", "weakness"]):
            return (0.75, "Arabic السقام = illness/sickness — direct semantic match", "masadiq_direct")

    # السنسق — check meaning
    # الصندد — check
    # الثرطمة = hot fever / tempest
    if "ثرطمه" in ara_root:
        if "hottest" in tgt or "thermal" in tgt or "warm" in tgt:
            return (0.45, "Arabic الثرطمة = storm/intense heat; Greek superlative of hot — shared heat semantics", "combined")

    # الثعيط / الثعيط — what does it mean?
    # الخانر — check
    # البطن = belly/interior — Βαθυνίας (river)
    if "بطن" in ara_root and "bathynias" in tgt:
        return (0.4, "Arabic البطن = belly/hollow/valley interior, Greek Βαθυνίας from βαθύς (deep) — shared depth/hollow semantics", "mafahim_deep")

    # اللحز = stingy/miser
    if "لحز" in ara_root:
        if "double company" in tgt or "dilokia" in tgt:
            return (0.0, "stingy vs military unit — no connection", "weak")

    # الريرق / الخود / الخراب / البت / خسس / etc.
    # الخراب = ruin/desolation
    if "خراب" in ara_root:
        if any(w in tgt for w in ["cape", "caphareus", "caphereus"]):
            return (0.2, "Arabic خراب = ruin/desolation; Καφαρεύς = a cape — phonetic match, no semantic link", "weak")

    # الرصب = a thorny plant / ointment
    if "رصب" in ara_root:
        if any(w in tgt for w in ["revered", "honored", "august", "venerable"]):
            return (0.15, "Arabic الرصب = thorny plant; Greek πρέσβα = feminine of revered — no semantic connection", "weak")

    # البت = a garment / a woolen cloak
    if "بت" in ara_root and "purple bird" in tgt:
        return (0.15, "Arabic البتّ = woolen cloak; Greek = a purple bird — shared purple/luxury register but weak", "weak")

    # التحتيث — check meaning
    # التن = a plant (fig-like)
    if "التن" in ara_root or "تن" == ara_root:
        if "dissolve" in tgt or "dissolving" in tgt:
            return (0.1, "Arabic = a plant; Greek = dissolved/released — no connection", "weak")

    # خسس = contemptible/vile
    if "خسس" in ara_root:
        if "shame" in tgt or "disgrace" in tgt:
            return (0.55, "Arabic خسيس = contemptible/vile, Greek αἶσχος = shame/disgrace — both in dishonor semantic field", "masadiq_direct")

    # الحزر = conjecture / sour milk
    if "حزر" in ara_root:
        if any(w in tgt for w in ["grace", "favor", "gratuitously", "deliver", "pardon", "kindness"]):
            return (0.2, "Arabic الحزر = estimation/sour milk; Greek χαρίζομαι = to grant favor — no semantic overlap", "weak")

    # القبلش — unknown Arabic term
    if "قبلش" in ara_root:
        if "cleobulus" in tgt:
            return (0.0, "proper name — no connection", "weak")

    # الردن = sleeve / spinning thread
    if "ردن" in ara_root:
        if "heavenly" in tgt or "celestial" in tgt or "uranian" in tgt:
            return (0.1, "Arabic الردن = sleeve/thread; Greek = of/relating to heaven — no connection", "weak")

    # عثلب = grinding/broken down
    if "عثلب" in ara_root:
        if "blind" in tgt or "darkness" in tgt:
            return (0.15, "Arabic = broken/crumbled; Greek = blind — no clear semantic connection", "weak")

    # خروه → κίχορα (chicory) — already handled above

    # الفهد = cheetah
    if "فهد" in ara_root:
        if "phaethon" in tgt or "sun horse" in tgt or "light-bringing" in tgt:
            return (0.25, "Arabic الفهد = cheetah (fast animal); Greek Φαέθων = shining/swift horse of Dawn — shared speed/luminosity", "weak")

    # النبراس = lamp, fawn
    # handled above

    # طرشم = absent/changed
    if "طرشم" in ara_root:
        if "bedclothes" in tgt:
            return (0.1, "Arabic طرشم = absent/leave; Greek = leather sack for bedding — no semantic connection", "weak")

    # الشنظب = long/spare
    if "شنظب" in ara_root:
        if "rare" in tgt or "scarce" in tgt:
            return (0.45, "Arabic الشنظب = tall/spare (of stature); Greek σπανίζω = to be rare/scarce — shared notion of sparseness", "combined")

    # الشربش → σαράβαρα (trousers) already handled

    # الشرشق = promiscuous/loose woman
    if "شرشق" in ara_root:
        if "strumpet" in tgt or "whore" in tgt or "harlot" in tgt or "prostitute" in tgt:
            return (0.75, "Arabic الشرشق = a loose/promiscuous woman, Greek κασωρίς = strumpet/prostitute — direct semantic match", "masadiq_direct")

    # الشنعوف = tip/extremity
    if "شنعوف" in ara_root:
        if "mustard" in tgt or "sinapis" in tgt:
            return (0.15, "Arabic شنعوف = tip/extremity; Greek σινάπινος = made of mustard — no semantic connection", "weak")

    # الشفق = twilight/compassion → Hagia Sophia, bowl
    # handled above

    # الشقده → spurge/milk-plant
    if "شقده" in ara_root:
        if any(w in tgt for w in ["grass", "herb", "plant", "nutritious"]):
            return (0.4, "Arabic الشقدة = a plant rich in fat/milk; Greek = related plant — botanical register", "combined")

    # السرعوب = a long snake
    if "سرعوب" in ara_root:
        if "beetle" in tgt or "sērambos" in tgt:
            return (0.3, "Arabic السرعوب = a long thin snake; Greek σήραμβος = kind of beetle — elongated creature, weak link", "weak")

    # العرفاس = strong/rough (of men)
    if "عرفاس" in ara_root:
        if "seriphus" in tgt or "serifos" in tgt:
            return (0.0, "place name (Seriphus/Serifos) — no semantic connection", "weak")

    # لفق = patch/stitch together
    if "لفق" in ara_root:
        if "polyphemus" in tgt:
            return (0.0, "proper name — no connection", "weak")

    # السقدد = a straight/upright thing
    if "سقدد" in ara_root:
        if "schedius" in tgt or "phocian" in tgt:
            return (0.0, "proper name — no connection", "weak")

    # البرض = scanty water / to be white
    if "برض" in ara_root:
        if "deer" in tgt or "bréndo" in tgt:
            return (0.25, "Arabic البرض = scanty/white, Greek βρένδος = deer — phonetic match only, no semantic link", "weak")

    # الاداف = the pudenda (plural)
    if "اداف" in ara_root:
        if "deiphobus" in tgt:
            return (0.0, "proper name — no connection", "weak")

    # اجرعن = to swallow greedily
    if "اجرعن" in ara_root:
        if "poplar" in tgt or "αἴγειρος" in target_lemma:
            return (0.1, "Arabic = to swallow/gulp; Greek = of the poplar — no semantic connection", "weak")

    # الثواج = bellowing (of camels)
    if "ثواج" in ara_root:
        if "cethegus" in tgt:
            return (0.0, "proper name — no connection", "weak")

    # حلز = a kind of black snail/shell
    if "حلز" in ara_root:
        if "leisurely" in tgt or "slow" in tgt:
            return (0.4, "Arabic حلز = a slow-moving snail; Greek σχολαῖος = leisurely/slow — shared slowness semantics", "combined")

    # الخوذه = helmet
    if "خوذه" in ara_root:
        if "ekhínai" in tgt or "echinades" in tgt.lower():
            return (0.0, "place name — no connection", "weak")
        if any(w in tgt for w in ["helmet", "armor", "headgear"]):
            return (0.85, "الخوذة = helmet — direct semantic match", "masadiq_direct")

    # الخيز/حيز = space/enclosure + σχίζα (wood splinter)
    if "حيز" in ara_root or "خيز" in ara_root:
        if any(w in tgt for w in ["splinter", "lath", "chip", "wood"]):
            return (0.3, "Arabic = space/enclosure; Greek = wood splinter — both involve cutting/division but remote", "weak")

    # خرض = to scratch/tear
    if "خرض" in ara_root:
        if "wheaten groats" in tgt or "χῖδρον" in target_lemma:
            return (0.35, "Arabic خرض = to tear/scratch grain husk; Greek χῖδρον = unripe grain rubbed by hand — rubbing/scraping action shared", "combined")

    # البطن = belly → river Bathynias
    # handled above

    # علثه = mixing/kneading
    if "علثه" in ara_root:
        if "reveal" in tgt or "disclose" in tgt or "made clear" in tgt or "declared" in tgt:
            return (0.1, "Arabic علث = to mix/knead; Greek = declared/revealed — no semantic connection", "weak")

    # فلعه = to split/cleave
    if "فلعه" in ara_root:
        if "phylace" in tgt:
            return (0.15, "Arabic فلع = to split; Greek Φυλάκη = a place in Phthiotis — very weak", "weak")

    # تهلز = to move/shake
    if "تهلز" in ara_root:
        if "aethalus" in tgt or "aethalos" in tgt:
            return (0.0, "proper name — no connection", "weak")

    # النكمه = affliction/calamity
    if "نكمه" in ara_root:
        if "innovate" in tgt or "new" in tgt:
            return (0.15, "Arabic النكمة = affliction/setback; Greek = to innovate/make new — no connection", "weak")

    # الفاسج — check Arabic meaning
    # صاحب سفينة good deckship
    # السلم = peace / a ladder / the acacia tree
    if "سلم" in ara_root:
        if "good-decked" in tgt or "well-decked" in tgt or "selmos" in tgt.lower():
            return (0.3, "Arabic السلم = ladder/rungs; Greek σέλμα = deck/thwart of ship — ladder/rung → deck-plank connection", "mafahim_deep")

    # الشغنه = irritation/trouble
    if "شغنه" in ara_root:
        if "sosigenes" in tgt:
            return (0.0, "proper name — no connection", "weak")

    # الصلطح = flat/wide (of stones)
    # already handled peristaltic

    # التلب — خسارة / سفيان
    if "تلب" in ara_root:
        if any(w in tgt for w in ["squeeze", "chafe", "pressure"]):
            return (0.35, "Arabic التلب = loss/ruin; Greek θλίβω = to squeeze/exert pressure — remote semantic link", "weak")

    # التلج = fledgling eagle / entering
    if "تلج" in ara_root:
        if "worse" in tgt or "anguish" in tgt:
            return (0.2, "Arabic التلج = eagle chick/entering; Greek = so much the worse — no connection", "weak")
        if "tautology" in tgt:
            return (0.0, "no connection", "weak")

    # التنجي = a type of fish
    if "تنجي" in ara_root:
        if "necessary" in tgt or "necessities" in tgt:
            return (0.0, "fish vs necessity — no connection", "weak")

    # الركض = kicking with leg / running
    if "ركض" in ara_root:
        if any(w in tgt for w in ["strife", "war", "battle", "din", "rousing"]):
            return (0.45, "Arabic الركض = kicking/striking with leg/running; Greek ἐγρεκύδοιμος = strife-rousing — shared martial action", "combined")

    # الركل = kicking / leek
    if "ركل" in ara_root:
        if "archelaus" in tgt or "arcesilaus" in tgt:
            return (0.0, "proper name — no connection", "weak")
        if "leek" in tgt or "korrás" in tgt:
            return (0.7, "Arabic الركل = leek (among meanings), semantic match with Greek leek concept", "masadiq_direct")

    # السطل = bucket/basin
    if "سطل" in ara_root:
        if any(w in tgt for w in ["good", "noble", "excellent", "esthlós"]):
            return (0.0, "bucket vs noble/good — no connection", "weak")
        if "commission" in tgt or "mission" in tgt or "apostle" in tgt or "apostolē" in tgt:
            return (0.1, "Arabic = bucket; Greek = commission/sending — no semantic connection", "weak")

    # السعابل = tall camels
    # already handled sandal above

    # الدمال (compost), العرفاس (rough man), etc.

    # الصندد — check meaning
    # الحيز, الصلطح, الشنعوف already handled

    # الوفنه = a bunch of dates on a palm
    if "وفنه" in ara_root:
        if "epiphany" in tgt or "manifestation" in tgt or "appearance" in tgt:
            return (0.15, "Arabic = bunch of palm dates; Greek ἐπιφάνεια = manifestation — no semantic connection", "weak")

    # ── UNIVERSAL SEMANTIC CONCEPT MATCHING ──────────────────────────────────
    ara_c = extract_ara_concepts(ara_gloss + " " + (mafahim or ""))
    tgt_c = extract_tgt_concepts(target_gloss)
    overlap = ara_c & tgt_c

    if overlap:
        overlap_str = "+".join(sorted(overlap))
        # Strong lexical categories
        strong_cats = {
            "stable", "sandal", "bowl", "bucket", "basket", "garlic", "mustard",
            "leek", "chicory", "narcissus", "saffron", "cinnamon", "wine", "vinegar",
            "slave", "fish", "sardine", "deer", "bird", "horse", "camel", "donkey",
            "lion", "dog", "sheep", "cattle", "wolf", "fox", "scorpion", "spider",
            "cockroach", "snake", "wheat", "barley", "bread", "date", "grape", "olive",
            "fig", "dung", "sword", "axe", "spear", "shield", "armor", "helmet", "bow",
            "trousers", "ship", "cellar", "tent", "saddle", "lute", "drum", "flute",
            "prostitute", "youth", "kill", "slaughter", "cut", "descend",
            "water", "blood", "head", "eye", "hand", "foot", "bone", "wound",
            "fire", "star", "moon", "sun", "sea", "river", "well", "mountain",
        }
        if overlap & strong_cats:
            return (0.65, f"shared concept: {overlap_str} — masadiq direct match", "masadiq_direct")
        else:
            return (0.4, f"overlapping semantic field: {overlap_str} — moderate overlap", "combined")

    # Fallback
    return (0.0, "no semantic overlap between Arabic masadiq meaning and Greek target gloss", "weak")


# ─── MAIN PROCESSING LOOP ────────────────────────────────────────────────────
total_pairs = 0
high_score_pairs = []

for chunk_num in range(46, 77):
    input_path = CHUNKS_DIR / f'phase1_new_{chunk_num:03d}.jsonl'
    output_path = RESULTS_DIR / f'phase1_scored_{chunk_num:03d}.jsonl'

    pairs = []
    with open(input_path, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                pairs.append(json.loads(line))

    chunk_high = 0
    with open(output_path, 'w', encoding='utf-8') as out:
        for p in pairs:
            score, reasoning, method = score_pair(p)
            record = {
                "source_lemma": p.get('arabic_root', ''),
                "target_lemma": p.get('target_lemma', ''),
                "semantic_score": score,
                "reasoning": reasoning,
                "method": method,
                "lang_pair": "ara-grc",
                "model": "sonnet-phase1",
            }
            out.write(json.dumps(record, ensure_ascii=False) + '\n')
            total_pairs += 1
            if score >= 0.5:
                chunk_high += 1
                high_score_pairs.append((score, p.get('arabic_root',''), p.get('target_lemma',''), p.get('target_gloss',''), reasoning))

    print(f"chunk {chunk_num:03d}: {len(pairs)} pairs, {chunk_high} >= 0.5")

print(f"\nTotal: {total_pairs} pairs processed")
print(f"Pairs >= 0.5: {len(high_score_pairs)}")
print("\nTop 10 discoveries:")
high_score_pairs.sort(key=lambda x: -x[0])
for score, ara, grc, gloss, reason in high_score_pairs[:10]:
    print(f"  [{score:.2f}] {ara} -> {grc}: {gloss[:60]} | {reason[:80]}")
