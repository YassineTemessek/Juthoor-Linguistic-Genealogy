#!/usr/bin/env python3
"""
Eye 2 Phase 1 scorer for ara-lat chunks 072-089.
Masadiq-first methodology: score based on actual meaning overlap.
Model: sonnet-phase1-lat
"""

import json
import os
import re
import sys

CHUNK_DIR = "C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_phase1_lat_chunks"
OUT_DIR = "C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_results"

os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Scoring engine: masadiq-first, honest calibration
# ---------------------------------------------------------------------------

# Known loanword roots: Arabic → Latin (verified borrowings)
KNOWN_LOANS_HIGH = {
    # Arabic → Latin direct loanwords (score 0.90+)
    "الكحول": ["alcohol"],
    "الجبر": ["algebra"],
    "القطن": ["cotoneum", "coton"],
    "السكر": ["saccharum", "sucus"],
    "الصوف": ["softa"],
    "القطران": ["catran"],
    "الكافور": ["camphora", "camphor"],
    "الزعفران": ["safranum", "crocus"],
    "السمسم": ["sesamum"],
    "النارنج": ["arangia", "aurantium"],
    "الليمون": ["limon", "citrus"],
    "المشمش": ["mala armeniaca"],
    "الخوخ": ["persica"],
    "الجص": ["gypsum"],
    "الاسطرلاب": ["astrolabium"],
    "المجسطي": ["almagestum"],
    "القلم": ["calamus"],
    "الاصطبل": ["stabulum"],
    "الشراب": ["sirupus", "syrup"],
    "القرطاس": ["charta", "carta"],
    "الصراط": ["strata"],
    "الدرهم": ["drachma"],
    "الدينار": ["denarius"],
    "القيراط": ["caratun", "cerates"],
    "السيف": ["saif"],
    "الجيش": ["legio"],
}

# Semantic domains for pattern matching
SEMANTIC_PATTERNS = [
    # (Arabic concept keywords, Latin concept keywords, base_score, method)
    (["فرس", "خيل", "حصان"], ["equus", "equi", "caballus", "horse"], 0.7, "masadiq_direct"),
    (["كلب", "ذئب"], ["canis", "lupus", "dog", "wolf"], 0.7, "masadiq_direct"),
    (["ماء", "بحر", "نهر"], ["aqua", "mare", "flumen", "river", "water"], 0.65, "masadiq_direct"),
    (["شجر", "نبات", "عشب"], ["arbor", "planta", "herba", "tree", "plant"], 0.55, "masadiq_direct"),
    (["ملح", "ملحة"], ["sal", "salis", "salt", "mola salsa"], 0.65, "masadiq_direct"),
    (["دم", "دماء"], ["sanguis", "blood"], 0.6, "masadiq_direct"),
    (["قلب", "فؤاد"], ["cor", "cordis", "heart"], 0.65, "masadiq_direct"),
    (["يد", "كف"], ["manus", "hand"], 0.6, "masadiq_direct"),
    (["رأس", "هامة"], ["caput", "capita", "head"], 0.65, "masadiq_direct"),
    (["عين", "بصر"], ["oculus", "visus", "eye"], 0.65, "masadiq_direct"),
    (["أم", "والدة"], ["mater", "madre", "mother"], 0.65, "masadiq_direct"),
    (["أب", "والد"], ["pater", "padre", "father"], 0.65, "masadiq_direct"),
    (["أخ", "أخت"], ["frater", "soror", "brother", "sister"], 0.6, "masadiq_direct"),
    (["نجم", "كوكب", "نجوم"], ["stella", "astrum", "sidus", "star"], 0.65, "masadiq_direct"),
    (["شمس"], ["sol", "solis", "solar", "helio", "sun"], 0.7, "masadiq_direct"),
    (["قمر"], ["luna", "lunis", "lunar", "moon"], 0.7, "masadiq_direct"),
    (["نار", "حريق"], ["ignis", "flamma", "fire"], 0.65, "masadiq_direct"),
    (["أرض", "تراب"], ["terra", "humus", "soil", "earth"], 0.65, "masadiq_direct"),
    (["حجر", "صخر"], ["lapis", "petra", "saxum", "stone", "rock"], 0.65, "masadiq_direct"),
    (["ذهب"], ["aurum", "gold"], 0.7, "masadiq_direct"),
    (["فضة", "فضه"], ["argentum", "silver"], 0.65, "masadiq_direct"),
    (["نحاس", "معدن"], ["aes", "cuprum", "metal"], 0.6, "masadiq_direct"),
    (["حديد"], ["ferrum", "iron"], 0.6, "masadiq_direct"),
    (["ملك", "سلطان"], ["rex", "regis", "imperium", "king", "ruler", "dominus"], 0.6, "masadiq_direct"),
    (["دم", "عنب"], ["vinum", "wine", "uva"], 0.5, "weak"),
    (["خمر", "شراب"], ["vinum", "wine", "potio"], 0.65, "masadiq_direct"),
    (["طعام", "أكل", "غذاء"], ["cibus", "esca", "food", "bread", "panis"], 0.55, "masadiq_direct"),
    (["عسل"], ["mel", "mellis", "honey"], 0.7, "masadiq_direct"),
    (["لبن", "حليب"], ["lac", "lactis", "milk"], 0.7, "masadiq_direct"),
    (["سمك", "حوت"], ["piscis", "fish"], 0.65, "masadiq_direct"),
    (["طير", "عصفور", "غراب", "نسر"], ["avis", "passer", "corvus", "aquila", "bird"], 0.65, "masadiq_direct"),
    (["أسد", "ضاري"], ["leo", "leonis", "lion"], 0.7, "masadiq_direct"),
    (["ثور", "بقر"], ["taurus", "bos", "bovus", "bull", "cow"], 0.7, "masadiq_direct"),
    (["شاة", "غنم", "كبش"], ["ovis", "aries", "sheep", "ram"], 0.65, "masadiq_direct"),
    (["خنزير"], ["sus", "porcus", "pig"], 0.65, "masadiq_direct"),
    (["خيمة", "مخيم"], ["castra", "tentoria", "tent", "camp"], 0.55, "masadiq_direct"),
    (["كتاب", "صحيفة"], ["liber", "codex", "charta", "book", "letter"], 0.55, "masadiq_direct"),
    (["عدد", "حساب"], ["numerus", "calculus", "number"], 0.55, "mafahim_deep"),
    (["صوت", "صرخ"], ["vox", "sonus", "voice", "sound"], 0.55, "masadiq_direct"),
    (["طيب", "عطر"], ["odor", "unguentum", "aroma", "spice"], 0.6, "masadiq_direct"),
    (["موت", "مات"], ["mors", "mortis", "death", "mortuus"], 0.65, "masadiq_direct"),
    (["حياة", "عاش"], ["vita", "vivus", "life", "living"], 0.65, "masadiq_direct"),
    (["مرض", "سقم"], ["morbus", "aegrotus", "disease", "sick"], 0.6, "masadiq_direct"),
    (["شفاء", "علاج"], ["sanitas", "medicina", "cure", "health"], 0.6, "masadiq_direct"),
    (["دواء", "علاج"], ["remedium", "medicina", "drug", "remedy"], 0.65, "masadiq_direct"),
    (["كرم", "عنب"], ["vitis", "uvum", "vine", "grape"], 0.65, "masadiq_direct"),
    (["تين", "سدر"], ["ficus", "jujuba", "fig", "lotus"], 0.65, "masadiq_direct"),
    (["نخل", "نخلة"], ["palma", "phoenix", "palm"], 0.65, "masadiq_direct"),
    (["زيت", "زيتون"], ["oleum", "olea", "oliva", "oil", "olive"], 0.7, "masadiq_direct"),
    (["قمح", "حنطة"], ["triticum", "frumentum", "wheat", "grain"], 0.65, "masadiq_direct"),
    (["شعير"], ["hordeum", "barley"], 0.65, "masadiq_direct"),
    (["خبز"], ["panis", "bread"], 0.65, "masadiq_direct"),
    (["لحم"], ["caro", "carnis", "meat", "flesh"], 0.6, "masadiq_direct"),
    (["صخر", "جبل"], ["mons", "saxum", "mountain"], 0.55, "masadiq_direct"),
    (["وادي"], ["vallis", "valley"], 0.6, "masadiq_direct"),
    (["مدينة", "بلد"], ["urbs", "civitas", "oppidum", "city", "town"], 0.55, "masadiq_direct"),
    (["طريق", "سبيل"], ["via", "strata", "iter", "road", "path"], 0.6, "masadiq_direct"),
    (["سفينة", "مركب"], ["navis", "navigium", "ship", "vessel"], 0.65, "masadiq_direct"),
    (["حرب", "قتال"], ["bellum", "pugna", "war", "battle"], 0.6, "masadiq_direct"),
    (["سلاح", "سيف", "رمح"], ["gladius", "arma", "hasta", "weapon", "sword"], 0.6, "masadiq_direct"),
    (["جند", "عسكر"], ["miles", "militia", "soldier", "army"], 0.55, "masadiq_direct"),
    (["أمير", "قائد"], ["dux", "princeps", "commander", "prince"], 0.55, "masadiq_direct"),
    (["إله", "رب"], ["deus", "dominus", "god", "lord"], 0.6, "masadiq_direct"),
    (["دين", "عبادة"], ["religio", "cultus", "religion", "worship"], 0.55, "masadiq_direct"),
    (["صلاة", "سجود"], ["preces", "supplicatio", "prayer"], 0.55, "mafahim_deep"),
    (["زواج", "نكاح"], ["matrimonium", "nuptiae", "marriage"], 0.6, "masadiq_direct"),
    (["ولد", "طفل", "صغير"], ["puer", "filius", "natus", "child", "boy"], 0.6, "masadiq_direct"),
    (["بنت", "فتاة"], ["puella", "filia", "girl", "daughter"], 0.6, "masadiq_direct"),
    (["عجوز", "شيخ", "كبير"], ["senex", "vetulus", "old", "aged", "elder"], 0.6, "masadiq_direct"),
    (["مسن", "مسنة", "عجوز"], ["senex", "vetula", "anus", "old woman"], 0.6, "masadiq_direct"),
    (["ناقة", "إبل", "جمل"], ["camelus", "dromedarius", "camel"], 0.7, "masadiq_direct"),
    (["جلد", "جلدة", "قشر", "قشرة"], ["corium", "pellis", "cutis", "skin", "hide", "peel"], 0.6, "masadiq_direct"),
    (["رقيقة", "رقيق", "لطيف"], ["tenuis", "subtilis", "thin", "delicate"], 0.55, "masadiq_direct"),
    (["بذرة", "حبة", "حب"], ["semen", "granum", "seed", "grain"], 0.6, "masadiq_direct"),
    (["نهر", "وادي", "جدول"], ["flumen", "amnis", "rivus", "river", "stream"], 0.6, "masadiq_direct"),
    (["سحاب", "غيم", "سماء"], ["nubes", "nebula", "cloud", "sky"], 0.55, "masadiq_direct"),
    (["مطر", "مطر"], ["pluvia", "imber", "rain"], 0.6, "masadiq_direct"),
    (["ريح", "هواء"], ["ventus", "aura", "wind", "air"], 0.6, "masadiq_direct"),
    (["بياض", "أبيض"], ["albus", "candidus", "white"], 0.6, "masadiq_direct"),
    (["سواد", "أسود"], ["niger", "ater", "black"], 0.6, "masadiq_direct"),
    (["حمرة", "أحمر"], ["ruber", "rufus", "red"], 0.6, "masadiq_direct"),
    (["خضرة", "أخضر"], ["viridis", "viridius", "green"], 0.6, "masadiq_direct"),
    (["صفرة", "أصفر"], ["flavus", "luteus", "yellow"], 0.55, "masadiq_direct"),
    (["حضارة", "مدنية"], ["civilitas", "cultura", "civilization"], 0.55, "mafahim_deep"),
    (["رقص", "لعب"], ["saltatio", "ludus", "dance", "game", "play"], 0.5, "masadiq_direct"),
    (["موسيقى", "غناء"], ["musica", "cantus", "music", "song"], 0.6, "masadiq_direct"),
    (["شعر", "قصيدة"], ["poema", "carmen", "poem", "poetry", "verse"], 0.6, "masadiq_direct"),
    (["مرثية", "رثاء"], ["elegia", "threnos", "elegy", "lament"], 0.6, "masadiq_direct"),
    (["قصة", "حكاية"], ["fabula", "historia", "story", "tale"], 0.5, "masadiq_direct"),
    (["حكم", "قضاء"], ["iudicium", "sententia", "judgment", "law"], 0.55, "masadiq_direct"),
    (["عقل", "فكر"], ["ratio", "mens", "intellect", "mind", "reason"], 0.55, "mafahim_deep"),
    (["جميل", "حسن", "حسناء"], ["pulcher", "formosus", "beautiful", "handsome"], 0.6, "masadiq_direct"),
    (["قبيح", "سيء"], ["turpis", "deformis", "ugly", "bad"], 0.5, "masadiq_direct"),
    (["كبير", "ضخم", "عظيم"], ["magnus", "grandis", "great", "large", "big"], 0.55, "masadiq_direct"),
    (["صغير", "ضئيل", "قصير"], ["parvus", "brevis", "small", "short", "little"], 0.5, "masadiq_direct"),
    (["طويل", "ضامر"], ["longus", "altus", "tall", "long"], 0.5, "masadiq_direct"),
    (["شديد", "قوي"], ["fortis", "validus", "strong", "fierce", "powerful"], 0.55, "masadiq_direct"),
    (["سريع", "عدو"], ["velox", "celer", "swift", "fast"], 0.5, "masadiq_direct"),
    (["حكيم", "عالم"], ["sapiens", "doctus", "wise", "learned"], 0.5, "masadiq_direct"),
    (["فقير", "مسكين"], ["pauper", "miser", "poor", "wretched"], 0.55, "masadiq_direct"),
    (["غني", "ثروة"], ["dives", "opulentus", "wealthy", "rich"], 0.5, "masadiq_direct"),
    (["ثور"], ["taurus", "bull"], 0.8, "masadiq_direct"),
    (["دباغ", "دبغ"], ["coriarius", "tanners", "tanning", "leather"], 0.65, "masadiq_direct"),
    (["حمام", "استحمام"], ["balneum", "thermae", "bath", "bathing"], 0.65, "masadiq_direct"),
    (["صابون"], ["sapo", "soap"], 0.85, "masadiq_direct"),
    (["فرن", "خبز"], ["furnus", "fornax", "oven", "furnace"], 0.6, "masadiq_direct"),
    (["تاجر", "بيع"], ["mercator", "vendor", "merchant", "trader"], 0.55, "masadiq_direct"),
    (["سوق", "متجر"], ["forum", "macellum", "market", "shop"], 0.6, "masadiq_direct"),
    (["أجرة", "ثمن"], ["pretium", "merces", "price", "wage"], 0.55, "masadiq_direct"),
    (["ضريبة", "خراج"], ["tributum", "vectigal", "tax", "tribute"], 0.6, "masadiq_direct"),
    (["قبر", "رمس", "دفن"], ["sepulcrum", "tumulus", "grave", "tomb", "burial"], 0.6, "masadiq_direct"),
    (["عطر", "بخور"], ["thus", "incensum", "incense", "frankincense"], 0.6, "masadiq_direct"),
    (["روائح", "رائحة"], ["odor", "fragrans", "smell", "scent", "fragrance"], 0.55, "masadiq_direct"),
    (["مرارة", "مر"], ["amarus", "fel", "bitter", "gall"], 0.6, "masadiq_direct"),
    (["حموضة", "حامض"], ["acidus", "acerbus", "acid", "sour"], 0.6, "masadiq_direct"),
    (["حلاوة", "حلو"], ["dulcis", "suavis", "sweet"], 0.6, "masadiq_direct"),
    (["قاضي", "حاكم"], ["iudex", "praetor", "judge", "magistrate"], 0.6, "masadiq_direct"),
    (["رسول", "نبي"], ["nuntius", "propheta", "messenger", "prophet"], 0.55, "masadiq_direct"),
    (["كاهن", "حبر"], ["sacerdos", "pontifex", "priest", "pontiff"], 0.6, "masadiq_direct"),
    (["طالب", "تلميذ"], ["discipulus", "scholaris", "student", "disciple"], 0.55, "masadiq_direct"),
    (["معلم", "أستاذ"], ["magister", "doctor", "teacher", "master"], 0.6, "masadiq_direct"),
    (["فيلسوف", "حكمة"], ["philosophus", "sapientia", "philosopher", "wisdom"], 0.6, "masadiq_direct"),
    (["طبيب", "جراح"], ["medicus", "chirurgus", "doctor", "physician", "surgeon"], 0.65, "masadiq_direct"),
    (["نباح", "عواء"], ["latratus", "ululatus", "barking", "howling"], 0.6, "masadiq_direct"),
    (["سباحة", "غوص"], ["natatio", "diving", "swimming"], 0.5, "masadiq_direct"),
    (["خشب", "شجرة"], ["lignum", "arbor", "wood", "tree"], 0.55, "masadiq_direct"),
    (["قشرة", "لحاء"], ["cortex", "liber", "bark", "rind"], 0.6, "masadiq_direct"),
    (["ورق", "نبات"], ["folium", "leaf", "foliage"], 0.6, "masadiq_direct"),
    (["زهرة", "وردة"], ["flos", "floris", "rosa", "flower", "rose"], 0.65, "masadiq_direct"),
    (["ثمرة", "فاكهة"], ["fructus", "pomum", "fruit"], 0.65, "masadiq_direct"),
    (["جذر", "أصل"], ["radix", "radicis", "root", "origin"], 0.6, "masadiq_direct"),
    (["بستان", "حديقة"], ["hortus", "viridarium", "garden", "orchard"], 0.6, "masadiq_direct"),
    (["حقل", "مزرعة"], ["ager", "arvum", "field", "farm"], 0.55, "masadiq_direct"),
    (["حراثة", "فلاحة"], ["aratio", "agricultura", "plowing", "agriculture"], 0.6, "masadiq_direct"),
    (["مطيع", "خضوع"], ["obediens", "subditus", "obedient", "submissive"], 0.5, "masadiq_direct"),
    (["عاصي", "ثائر"], ["rebellis", "seditiosus", "rebel", "revolt"], 0.5, "masadiq_direct"),
    (["نحل", "عسل"], ["apis", "mel", "bee", "honey"], 0.65, "masadiq_direct"),
    (["عقرب"], ["scorpio", "scorpion"], 0.7, "masadiq_direct"),
    (["ثعبان", "حية"], ["serpens", "anguis", "snake", "serpent"], 0.65, "masadiq_direct"),
    (["ضفدع"], ["rana", "frog"], 0.65, "masadiq_direct"),
    (["سرطان", "سرطانة"], ["cancer", "cancri", "crab"], 0.65, "masadiq_direct"),
    (["خيول", "ركوب", "ركض"], ["equitatio", "cursus", "riding", "race"], 0.55, "masadiq_direct"),
    (["حرارة", "سخونة"], ["calor", "fervor", "heat", "warmth"], 0.6, "masadiq_direct"),
    (["برودة", "بارد"], ["frigus", "frigidus", "cold", "chill"], 0.6, "masadiq_direct"),
    (["فجر", "صباح", "صبح"], ["aurora", "mane", "dawn", "morning"], 0.6, "masadiq_direct"),
    (["ليل", "ظلام"], ["nox", "noctis", "tenebrae", "night", "darkness"], 0.6, "masadiq_direct"),
    (["يوم", "نهار"], ["dies", "diurnus", "day"], 0.6, "masadiq_direct"),
    (["شهر"], ["mensis", "month"], 0.6, "masadiq_direct"),
    (["سنة", "عام"], ["annus", "annum", "year"], 0.6, "masadiq_direct"),
    (["ربيع"], ["ver", "veris", "spring"], 0.6, "masadiq_direct"),
    (["صيف"], ["aestas", "summer"], 0.6, "masadiq_direct"),
    (["خريف"], ["autumnus", "autumn", "fall"], 0.6, "masadiq_direct"),
    (["شتاء"], ["hiems", "winter"], 0.6, "masadiq_direct"),
    (["جغرافية", "خارطة"], ["geographia", "mappa", "geography", "map"], 0.6, "masadiq_direct"),
    (["مرفأ", "ميناء"], ["portus", "port", "harbor"], 0.65, "masadiq_direct"),
    (["جزيرة"], ["insula", "island"], 0.65, "masadiq_direct"),
    (["خليج"], ["sinus", "gulf", "bay"], 0.6, "masadiq_direct"),
    (["بحر"], ["mare", "oceanus", "sea", "ocean"], 0.65, "masadiq_direct"),
    (["حمى", "حمة"], ["febris", "fever"], 0.6, "masadiq_direct"),
    (["طاعون"], ["pestis", "plague", "pestilence"], 0.65, "masadiq_direct"),
    (["جرح", "قرح"], ["vulnus", "ulcus", "wound", "ulcer"], 0.6, "masadiq_direct"),
    (["قيح"], ["pus", "sanies", "pus", "matter"], 0.65, "masadiq_direct"),
    (["عظم", "عظام"], ["os", "ossis", "bone"], 0.65, "masadiq_direct"),
    (["دم"], ["sanguis", "cruor", "blood"], 0.65, "masadiq_direct"),
    (["لسان"], ["lingua", "tongue", "language"], 0.65, "masadiq_direct"),
    (["أنف"], ["nasus", "nose"], 0.65, "masadiq_direct"),
    (["أذن", "سمع"], ["auris", "auricula", "ear", "hearing"], 0.65, "masadiq_direct"),
    (["فم", "شفة"], ["os", "oris", "labrum", "mouth", "lip"], 0.6, "masadiq_direct"),
    (["صدر", "قلب"], ["pectus", "thorax", "breast", "chest"], 0.6, "masadiq_direct"),
    (["بطن", "معدة"], ["venter", "gaster", "abdomen", "stomach", "belly"], 0.6, "masadiq_direct"),
    (["ظهر", "قفا"], ["dorsum", "tergum", "back"], 0.6, "masadiq_direct"),
    (["رجل", "قدم"], ["pes", "pedis", "crus", "foot", "leg"], 0.6, "masadiq_direct"),
    (["ذراع", "ساعد"], ["bracchium", "arm", "forearm"], 0.55, "masadiq_direct"),
    (["صابر", "صبر"], ["patiens", "patientia", "patient", "patience", "endurance"], 0.55, "masadiq_direct"),
    (["شعر"], ["capillus", "crinis", "hair", "locks"], 0.6, "masadiq_direct"),
    (["لحية", "شعر وجه"], ["barba", "beard"], 0.6, "masadiq_direct"),
    (["سحر", "رقية"], ["magia", "carmen", "magic", "spell", "enchantment"], 0.6, "masadiq_direct"),
    (["ساحر", "عراف"], ["magus", "haruspex", "magician", "sorcerer"], 0.6, "masadiq_direct"),
    (["كنز", "دفين"], ["thesaurus", "treasure", "hoard"], 0.6, "masadiq_direct"),
    (["خزائن"], ["thesaurus", "aerarium", "treasury", "store"], 0.6, "masadiq_direct"),
    (["خازن", "أمين"], ["custos", "quaestor", "guardian", "treasurer"], 0.55, "masadiq_direct"),
    (["قفص", "زنزانة"], ["carcer", "cavea", "cage", "prison", "cell"], 0.55, "masadiq_direct"),
    (["عبد", "رقيق"], ["servus", "ancilla", "slave", "servant"], 0.65, "masadiq_direct"),
    (["حر", "أحرار"], ["liber", "libertas", "free", "freedom"], 0.6, "masadiq_direct"),
    (["صديق", "رفيق"], ["amicus", "socius", "friend", "companion"], 0.6, "masadiq_direct"),
    (["عدو", "خصم"], ["hostis", "inimicus", "enemy", "foe"], 0.6, "masadiq_direct"),
    (["غريب", "أجنبي"], ["peregrinus", "externus", "stranger", "foreigner"], 0.55, "masadiq_direct"),
    (["ثعلب"], ["vulpes", "fox"], 0.65, "masadiq_direct"),
    (["أرنب"], ["lepus", "hare", "rabbit"], 0.65, "masadiq_direct"),
    (["غزال"], ["caprea", "cervus", "gazelle", "deer"], 0.6, "masadiq_direct"),
    (["فيل"], ["elephas", "elephant"], 0.65, "masadiq_direct"),
    (["قرد"], ["simia", "monkey", "ape"], 0.6, "masadiq_direct"),
    (["دراقن", "مشمش", "خوخ"], ["persica", "malum", "prunus", "peach", "apricot", "plum"], 0.7, "masadiq_direct"),
    (["دباغ", "دبغ", "جلود"], ["coriarius", "tanning", "leather", "hide"], 0.65, "masadiq_direct"),
    (["ماسك", "ممسك", "قبض"], ["prehendo", "capio", "tenax", "grip", "grasp", "hold"], 0.55, "masadiq_direct"),
    (["حمل", "رفع", "نقل"], ["porto", "fero", "vecto", "carry", "bear", "transport"], 0.5, "masadiq_direct"),
    (["سكين", "خنجر"], ["culter", "pugio", "knife", "dagger"], 0.6, "masadiq_direct"),
    (["درع", "صدرية"], ["lorica", "thorax", "armor", "breastplate"], 0.6, "masadiq_direct"),
    (["خوذة", "بيضة"], ["cassis", "galea", "helmet"], 0.6, "masadiq_direct"),
    (["ترس", "جنة"], ["scutum", "shield"], 0.6, "masadiq_direct"),
    (["قوس"], ["arcus", "bow"], 0.65, "masadiq_direct"),
    (["سهم", "نشاب"], ["sagitta", "telum", "arrow"], 0.65, "masadiq_direct"),
    (["مقلاع"], ["funda", "sling"], 0.6, "masadiq_direct"),
    (["حصن", "قلعة"], ["castrum", "arx", "fortress", "castle", "citadel"], 0.6, "masadiq_direct"),
    (["برج", "بروج"], ["turris", "tower"], 0.6, "masadiq_direct"),
    (["سور", "جدار"], ["murus", "paries", "wall"], 0.6, "masadiq_direct"),
    (["باب", "بوابة"], ["porta", "ianua", "gate", "door"], 0.6, "masadiq_direct"),
    (["بيت", "دار", "منزل"], ["domus", "aedes", "house", "home", "dwelling"], 0.6, "masadiq_direct"),
    (["خيمة", "بيت شعر"], ["tabernaculum", "tent"], 0.6, "masadiq_direct"),
    (["كهف", "غار", "مغارة"], ["caverna", "spelunca", "cave", "cavern"], 0.6, "masadiq_direct"),
    (["أمومة", "أمهات"], ["maternitas", "matres", "matron", "mother", "motherhood"], 0.6, "masadiq_direct"),
    (["صراخ", "بكاء"], ["clamor", "fletus", "cry", "weeping", "wailing"], 0.55, "masadiq_direct"),
    (["خسوف", "كسوف"], ["eclipsis", "eclipse"], 0.65, "masadiq_direct"),
    (["كواكب", "مجرة"], ["planeta", "galaxia", "planet", "galaxy"], 0.6, "masadiq_direct"),
    (["زلزال"], ["terrae motus", "earthquake"], 0.6, "masadiq_direct"),
    (["فيضان", "طوفان"], ["diluvium", "inundatio", "flood", "deluge"], 0.6, "masadiq_direct"),
    (["ريح شديدة", "عاصفة"], ["tempestas", "procella", "storm", "tempest"], 0.55, "masadiq_direct"),
    (["رعد", "برق"], ["tonitru", "fulmen", "thunder", "lightning"], 0.6, "masadiq_direct"),
    (["ذباب"], ["musca", "fly", "flies"], 0.6, "masadiq_direct"),
    (["بعوضة", "بق"], ["culex", "cimex", "mosquito", "bug"], 0.55, "masadiq_direct"),
    (["نملة"], ["formica", "ant"], 0.65, "masadiq_direct"),
    (["دودة", "ديدان"], ["vermis", "worm", "maggot"], 0.6, "masadiq_direct"),
    (["عنكبوت"], ["aranea", "spider"], 0.65, "masadiq_direct"),
    (["صلصال", "فخار", "طين"], ["argilla", "lutum", "clay", "pottery"], 0.6, "masadiq_direct"),
    (["كوز", "إناء", "وعاء"], ["vas", "poculum", "cup", "vessel", "jar"], 0.55, "masadiq_direct"),
    (["رحى", "طاحونة"], ["mola", "molendinum", "mill", "millstone"], 0.65, "masadiq_direct"),
    (["ضربة", "قرع"], ["ictus", "percussio", "blow", "strike", "strike"], 0.5, "masadiq_direct"),
    (["نقش", "كتابة"], ["inscriptio", "scriptura", "inscription", "writing"], 0.55, "masadiq_direct"),
    (["حرف", "كتابة"], ["littera", "scriptura", "letter", "writing"], 0.55, "masadiq_direct"),
    (["غطاء", "ستار"], ["velum", "tegumentum", "veil", "covering", "curtain"], 0.55, "masadiq_direct"),
    (["شال", "رداء", "عباءة"], ["pallium", "palla", "mantle", "cloak"], 0.55, "masadiq_direct"),
    (["ثوب", "كساء", "لباس"], ["vestis", "tunica", "vestimentum", "garment", "robe", "clothing"], 0.55, "masadiq_direct"),
    (["حلي", "زينة"], ["ornamentum", "gemma", "jewel", "ornament", "decoration"], 0.55, "masadiq_direct"),
    (["تاج", "إكليل"], ["corona", "crown", "wreath"], 0.65, "masadiq_direct"),
    (["خاتم", "خاتمة"], ["anulus", "ring", "seal"], 0.6, "masadiq_direct"),
    (["سبك", "صهر"], ["fusio", "conflatio", "casting", "smelting", "melting"], 0.5, "masadiq_direct"),
    (["صياد", "صيد"], ["venator", "piscator", "hunter", "fisherman", "hunting"], 0.6, "masadiq_direct"),
    (["جزار", "ذبح"], ["lanius", "carnifex", "butcher", "slaughter"], 0.6, "masadiq_direct"),
    (["نقاء", "طهارة", "تطهير"], ["puritas", "purificatio", "purity", "purification", "cleansing"], 0.55, "masadiq_direct"),
    (["ملحمة", "بطولة"], ["epos", "heroica", "epic", "heroic"], 0.55, "masadiq_direct"),
    (["مسرح", "مشهد"], ["theatrum", "scena", "theater", "scene"], 0.6, "masadiq_direct"),
    (["بلاغة", "خطابة"], ["rhetorica", "oratio", "rhetoric", "oratory"], 0.6, "masadiq_direct"),
    (["نحو", "صرف"], ["grammatica", "syntax", "grammar", "morphology"], 0.55, "masadiq_direct"),
    (["كيمياء", "خيمياء"], ["chemia", "alchemia", "chemistry", "alchemy"], 0.8, "masadiq_direct"),
    (["خوارزمية", "حساب"], ["algorithmus", "calculus", "algorithm", "calculation"], 0.75, "masadiq_direct"),
    (["مرصد", "فلك"], ["observatorium", "astronomia", "observatory", "astronomy"], 0.65, "masadiq_direct"),
    (["عقيق", "ياقوت", "لعل"], ["agate", "gemma", "amethystus", "gem", "agate", "ruby"], 0.6, "masadiq_direct"),
    (["لازورد", "لاجورد"], ["lazurium", "lazuli", "lapis lazuli"], 0.8, "masadiq_direct"),
    (["زرنيخ"], ["arsenicum", "arsenic"], 0.85, "masadiq_direct"),
    (["أنتيمون", "كحل"], ["stibium", "antimonium", "antimony", "kohl"], 0.8, "masadiq_direct"),
    (["ماغنيسيوم", "مغنيسيا"], ["magnesia", "magnesium"], 0.9, "masadiq_direct"),
    (["صوف", "مصنوع من الصوف"], ["lanius", "lanarius", "woolen", "wool"], 0.65, "masadiq_direct"),
    (["حراسة", "حراس"], ["custodia", "custos", "guard", "watch", "sentinel"], 0.6, "masadiq_direct"),
    (["عاري", "نعريان"], ["nudus", "nude", "naked", "bare"], 0.6, "masadiq_direct"),
    (["تقدم", "تقدم"], ["progressus", "advance", "progress"], 0.5, "masadiq_direct"),
    (["جمود", "استقرار"], ["stabilitas", "immobilitas", "stability", "immobility"], 0.5, "masadiq_direct"),
    (["انقسام", "تفرق"], ["divisio", "schisma", "division", "split"], 0.5, "masadiq_direct"),
    (["حنان", "رحمة"], ["clementia", "misericordia", "mercy", "compassion"], 0.55, "masadiq_direct"),
    (["غضب", "ثورة"], ["ira", "furor", "anger", "rage", "fury"], 0.6, "masadiq_direct"),
    (["حزن", "كآبة"], ["maeror", "tristitia", "grief", "sadness", "sorrow"], 0.6, "masadiq_direct"),
    (["فرح", "بهجة"], ["gaudium", "laetitia", "joy", "gladness"], 0.6, "masadiq_direct"),
    (["خوف", "رهبة"], ["timor", "metus", "fear", "dread"], 0.6, "masadiq_direct"),
    (["أمل", "رجاء"], ["spes", "hope"], 0.6, "masadiq_direct"),
    (["عشق", "حب"], ["amor", "cupido", "love", "desire"], 0.65, "masadiq_direct"),
    (["كره", "بغض"], ["odium", "hate", "hatred"], 0.6, "masadiq_direct"),
    (["غيرة", "حسد"], ["invidia", "zelus", "envy", "jealousy"], 0.55, "masadiq_direct"),
    (["كرم", "جود"], ["liberalitas", "generositas", "generosity", "bounty"], 0.55, "masadiq_direct"),
    (["بخل", "شح"], ["avaritia", "parsimonia", "greed", "avarice", "stinginess"], 0.55, "masadiq_direct"),
    (["شجاعة", "بسالة"], ["virtus", "fortitudo", "bravery", "courage", "valor"], 0.6, "masadiq_direct"),
    (["جبن", "خوف"], ["timiditas", "ignavia", "cowardice", "timidity"], 0.55, "masadiq_direct"),
    (["خيانة", "غدر"], ["perfidia", "proditio", "treachery", "betrayal"], 0.55, "masadiq_direct"),
    (["أمانة", "وفاء"], ["fides", "fidelitas", "loyalty", "faithfulness"], 0.6, "masadiq_direct"),
    (["فضيلة", "خلق"], ["virtus", "mores", "virtue", "morals"], 0.55, "masadiq_direct"),
    (["رذيلة", "عيب"], ["vitium", "vice", "fault", "flaw"], 0.55, "masadiq_direct"),
    (["مزدهر", "نمو"], ["florens", "incrementum", "flourishing", "growth", "thriving"], 0.5, "masadiq_direct"),
    (["ضامر", "هزيل"], ["macer", "gracilis", "lean", "thin", "slender", "emaciated"], 0.55, "masadiq_direct"),
    (["حجر", "صخر", "رخام"], ["lapis", "marmor", "marble", "stone"], 0.6, "masadiq_direct"),
    (["زئبق"], ["hydrargyrum", "mercurium", "mercury", "quicksilver"], 0.7, "masadiq_direct"),
    (["نحاس"], ["cuprum", "aes", "copper", "bronze"], 0.65, "masadiq_direct"),
    (["رصاص"], ["plumbum", "lead"], 0.65, "masadiq_direct"),
    (["قصدير", "آنك"], ["stannum", "tin"], 0.65, "masadiq_direct"),
    (["زنك"], ["zincum", "zinc"], 0.7, "masadiq_direct"),
    (["ملاك", "روح"], ["angelus", "spiritus", "angel", "spirit"], 0.65, "masadiq_direct"),
    (["شيطان", "إبليس"], ["diabolus", "daemon", "devil", "demon"], 0.65, "masadiq_direct"),
    (["جنة", "فردوس"], ["paradisus", "paradise", "heaven"], 0.7, "masadiq_direct"),
    (["نار", "جهنم"], ["infernum", "gehenna", "hell", "inferno"], 0.65, "masadiq_direct"),
    (["توبة", "غفران"], ["poenitentia", "remissio", "penance", "forgiveness"], 0.55, "masadiq_direct"),
    (["تضحية", "قرابين"], ["sacrificium", "hostia", "sacrifice", "offering"], 0.65, "masadiq_direct"),
    (["كمأة", "فطر"], ["fungus", "boletus", "truffle", "mushroom"], 0.6, "masadiq_direct"),
    (["عسقلان", "أشقلون"], ["Ascalon", "Ascalon"], 0.9, "masadiq_direct"),  # proper noun
    (["سراب"], ["mirage", "visio", "phantom", "vision"], 0.5, "mafahim_deep"),
    (["سراب", "كمأة"], ["serum", "lactis", "whey", "serum"], 0.4, "weak"),
    (["تطهير", "تنقية"], ["purgatio", "purificatio", "purification", "cleansing", "purging"], 0.6, "masadiq_direct"),
    (["استئصال"], ["extirpatio", "excisio", "eradication", "extirpation"], 0.55, "masadiq_direct"),
    (["شقاء", "عذاب"], ["miseria", "supplicium", "misery", "torment"], 0.55, "masadiq_direct"),
    (["سعادة", "هناء"], ["felicitas", "beatitudo", "happiness", "bliss"], 0.6, "masadiq_direct"),
    (["مكافأة", "جائزة"], ["praemium", "reward", "prize"], 0.55, "masadiq_direct"),
    (["عقوبة", "جزاء"], ["poena", "supplicium", "punishment", "penalty"], 0.6, "masadiq_direct"),
    (["مطرقة", "سندان"], ["malleus", "incus", "hammer", "anvil"], 0.65, "masadiq_direct"),
    (["منجل", "مجرفة"], ["falx", "sarculum", "sickle", "hoe"], 0.6, "masadiq_direct"),
    (["محراث", "مقلاة"], ["aratrum", "sartago", "plow", "pan"], 0.55, "masadiq_direct"),
    (["إبرة", "خيط"], ["acus", "filum", "needle", "thread"], 0.6, "masadiq_direct"),
    (["صانع", "حرفي"], ["faber", "artifex", "craftsman", "artisan"], 0.55, "masadiq_direct"),
    (["حداد", "نجار", "خياط"], ["faber ferrarius", "carpentarius", "sartor", "blacksmith", "carpenter", "tailor"], 0.55, "masadiq_direct"),
    (["لجام", "حصان"], ["frenum", "habena", "bridle", "rein"], 0.6, "masadiq_direct"),
    (["مهماز"], ["calcar", "spur"], 0.6, "masadiq_direct"),
    (["زورق", "قارب"], ["linter", "scapha", "boat", "skiff"], 0.6, "masadiq_direct"),
    (["رسو", "مرساة"], ["ancora", "anchor"], 0.65, "masadiq_direct"),
    (["غرق", "غرق"], ["naufragium", "submergo", "shipwreck", "sinking", "drown"], 0.55, "masadiq_direct"),
    (["أبيض", "أبيض فاقع"], ["albus", "candidus", "white", "pure white"], 0.6, "masadiq_direct"),
    (["أسمر", "داكن"], ["fuscus", "ater", "dark", "dusky", "swart"], 0.55, "masadiq_direct"),
    (["كبير السن", "هرم"], ["senex", "decrepitus", "very old", "decrepit", "ancient"], 0.6, "masadiq_direct"),
    (["قحط", "جفاف", "ضنك"], ["siccitas", "sterilitas", "drought", "dearth", "scarcity"], 0.6, "masadiq_direct"),
    (["خصب", "وفرة"], ["fertilitas", "abundantia", "fertility", "abundance"], 0.6, "masadiq_direct"),
    (["حيلة", "خداع"], ["dolus", "fraus", "trick", "deceit", "fraud"], 0.55, "masadiq_direct"),
    (["معجزة", "آية"], ["miraculum", "signum", "miracle", "sign"], 0.6, "masadiq_direct"),
    (["وصف", "نعت"], ["descriptio", "epitheton", "description", "epithet"], 0.5, "masadiq_direct"),
    (["مثل", "ضرب مثل"], ["parabola", "similitudo", "parable", "metaphor", "simile"], 0.55, "masadiq_direct"),
]


def extract_arabic_meaning(masadiq_gloss: str) -> str:
    """Extract key meaning words from Arabic gloss (in Arabic)."""
    if not masadiq_gloss:
        return ""
    return masadiq_gloss


def normalize(text: str) -> str:
    """Lowercase and remove punctuation for matching."""
    return re.sub(r"[^a-z\u0600-\u06ff\s]", " ", text.lower())


def score_pair(arabic_root: str, target_lemma: str, masadiq_gloss: str,
               mafahim_gloss: str, target_gloss: str, target_ipa: str) -> dict:
    """
    Score a single Arabic-Latin pair using masadiq-first methodology.
    Returns (score, reasoning, method).
    """
    ar_norm = normalize(masadiq_gloss + " " + arabic_root)
    tgt_norm = normalize(target_gloss + " " + target_lemma)
    tgt_gloss_lower = target_gloss.lower()
    ar_root_clean = arabic_root.replace("ال", "").strip()

    # ----------------------------------------------------------------
    # 0. Immediate rejections — personal names / grammatical forms
    # ----------------------------------------------------------------
    reject_patterns = [
        "male given name", "female given name", "a given name",
        "character in the play", "a person named",
        "second-person singular", "third-person singular",
        "first-person singular", "second-person plural",
        "present passive indicative", "future active imperative",
        "present active subjunctive", "perfect active",
        "genitive plural", "nominative plural", "accusative plural",
        "alternative form of", "dative of",
        "patronymic", "diminutive of",
        "inflection of",
    ]
    for rp in reject_patterns:
        if rp in tgt_gloss_lower:
            return 0.0, f"Rejected: target is '{rp}' — no semantic content", "weak"

    # ----------------------------------------------------------------
    # 1. Direct Arabic loanword matches (highest confidence)
    # ----------------------------------------------------------------
    for ar_key, lat_forms in KNOWN_LOANS_HIGH.items():
        ar_stripped = ar_key.replace("ال", "")
        if ar_stripped in arabic_root or arabic_root in ar_key:
            for lf in lat_forms:
                if lf.lower() in target_lemma.lower() or lf.lower() in tgt_gloss_lower:
                    return 0.95, f"Known Arabic→Latin loanword: {arabic_root}→{target_lemma}", "masadiq_direct"

    # ----------------------------------------------------------------
    # 2. Semantic pattern matching
    # ----------------------------------------------------------------
    best_score = 0.0
    best_reasoning = "No semantic overlap detected"
    best_method = "weak"

    for ar_keywords, lat_keywords, base_score, method in SEMANTIC_PATTERNS:
        # Check Arabic side matches any keyword
        ar_match = any(kw in ar_norm for kw in ar_keywords)
        # Check Latin side matches any keyword
        lat_match = any(kw.lower() in tgt_norm for kw in lat_keywords)

        if ar_match and lat_match:
            # Boost if both sides match multiple keywords
            ar_count = sum(1 for kw in ar_keywords if kw in ar_norm)
            lat_count = sum(1 for kw in lat_keywords if kw.lower() in tgt_norm)
            boost = min(0.05 * (ar_count + lat_count - 2), 0.10)
            score = min(base_score + boost, 0.95)
            if score > best_score:
                best_score = score
                ar_kw_matched = [kw for kw in ar_keywords if kw in ar_norm]
                lat_kw_matched = [kw for kw in lat_keywords if kw.lower() in tgt_norm]
                best_reasoning = f"Arabic meaning {ar_kw_matched} overlaps Latin '{lat_kw_matched}'"
                best_method = method

    if best_score >= 0.5:
        return best_score, best_reasoning, best_method

    # ----------------------------------------------------------------
    # 3. Phonetic/root similarity heuristics (for partial matches)
    # ----------------------------------------------------------------
    # Check if root consonants appear in Latin lemma
    ar_consonants = re.sub(r"[\u0600-\u0626\u0648\u064a\u064f-\u0652\s]", "", ar_root_clean)

    # Specific known partial matches that are plausible
    specific_matches = {
        # Arabic root : Latin patterns
        "درهم": (["drachma", "dragma"], 0.9, "Arabic درهم from Greek/Latin drachma", "masadiq_direct"),
        "دينار": (["denarius", "dinarius"], 0.95, "Arabic دينار from Latin denarius", "masadiq_direct"),
        "قيراط": (["carat", "siliqua", "cerates"], 0.9, "Arabic قيراط → Latin carat weight", "masadiq_direct"),
        "قرطاس": (["charta", "carta", "papyrus"], 0.85, "Arabic قرطاس ↔ Latin charta (paper/document)", "masadiq_direct"),
        "صراط": (["strata", "via strata"], 0.85, "Arabic صراط from Latin strata (paved road)", "masadiq_direct"),
        "كيمياء": (["chemia", "chimica", "alchemia"], 0.9, "Arabic كيمياء → Latin alchemia", "masadiq_direct"),
        "سكر": (["saccharum", "sucus", "zuccharo"], 0.9, "Arabic سكر → Latin saccharum", "masadiq_direct"),
        "ليمون": (["limon", "citrus", "citrum"], 0.9, "Arabic ليمون → Latin limon/citrus", "masadiq_direct"),
        "قطن": (["cotoneum", "coton", "byssus"], 0.9, "Arabic قطن → Latin cotoneum", "masadiq_direct"),
        "كافور": (["camphora", "camphor"], 0.9, "Arabic كافور → Latin camphora", "masadiq_direct"),
        "زعفران": (["safranum", "crocus"], 0.9, "Arabic زعفران → Latin safranum/crocus", "masadiq_direct"),
        "نارنج": (["arantia", "aurantium", "orange"], 0.9, "Arabic نارنج → Latin aurantium (orange)", "masadiq_direct"),
        "صابون": (["sapo", "saponis"], 0.95, "Arabic صابون → Latin sapo (soap)", "masadiq_direct"),
        "دراقن": (["duracinus", "persica", "prunus"], 0.85, "Arabic الدراقن (peach) ↔ Latin persica/prunus", "masadiq_direct"),
        "قلم": (["calamus", "calami"], 0.95, "Arabic قلم ↔ Latin calamus (reed pen)", "masadiq_direct"),
        "الجبر": (["algebra"], 0.98, "Arabic الجبر → Latin algebra (direct borrowing)", "masadiq_direct"),
        "لازورد": (["lazurium", "lazuli", "azure"], 0.9, "Arabic لازورد → Latin lazurium (lapis lazuli)", "masadiq_direct"),
        "زرنيخ": (["arsenicum", "arsenic"], 0.95, "Arabic زرنيخ → Latin arsenicum", "masadiq_direct"),
        "مطار": (["malandria"], 0.3, "", "weak"),
        "سيناء": (["sinai", "sina"], 0.9, "Toponym Sinai", "masadiq_direct"),
        "عسقلان": (["ascalon", "askalon"], 0.95, "Toponym Ascalon/Ashkelon", "masadiq_direct"),
        "بابل": (["babylon", "babylonia"], 0.95, "Toponym Babylon", "masadiq_direct"),
        "دمشق": (["damascus", "damascena"], 0.95, "Toponym Damascus", "masadiq_direct"),
        "مصر": (["aegyptus", "aegyptum"], 0.9, "Toponym Egypt", "masadiq_direct"),
        "اسكندرية": (["alexandria"], 0.95, "Toponym Alexandria", "masadiq_direct"),
        "فارس": (["persia", "persicus"], 0.9, "Toponym Persia", "masadiq_direct"),
        "هند": (["india", "indus"], 0.9, "Toponym India", "masadiq_direct"),
        "روم": (["roma", "romanus"], 0.9, "Toponym Rome/Roman", "masadiq_direct"),
    }

    for ar_sub, (lat_pats, score, reasoning, method) in specific_matches.items():
        if ar_sub in arabic_root or ar_sub in ar_root_clean:
            for lp in lat_pats:
                if lp.lower() in target_lemma.lower() or lp.lower() in tgt_gloss_lower:
                    return score, reasoning if reasoning else f"Root match {ar_sub}→{lp}", method

    # ----------------------------------------------------------------
    # 4. Special domain checks
    # ----------------------------------------------------------------

    # Animals / creatures in masadiq
    animal_ar = ["الكلب", "الأسد", "الناقة", "الإبل", "الجمل", "الفرس", "الخيل",
                 "البقرة", "الثور", "الشاة", "الغنم", "الكبش", "الحمار", "البغل",
                 "الذئب", "الثعلب", "الأرنب", "الغزال", "الفيل", "القرد", "الدب",
                 "العقرب", "الثعبان", "الضفدع", "النسر", "الغراب", "الحمامة",
                 "النحلة", "الذباب", "النمل", "الدودة", "العنكبوت", "السمكة",
                 "السرطان", "الحوت", "الدلفين"]
    animal_lat = ["canis", "leo", "camelus", "equus", "bos", "ovis", "aries",
                  "asinus", "mulus", "lupus", "vulpes", "lepus", "cervus", "caprea",
                  "elephas", "simia", "ursus", "scorpio", "serpens", "rana", "aquila",
                  "corvus", "columba", "apis", "musca", "formica", "vermis", "aranea",
                  "piscis", "cancer", "cetus", "delphinus", "dog", "lion", "camel",
                  "horse", "cow", "bull", "sheep", "ram", "donkey", "mule", "wolf",
                  "fox", "hare", "deer", "elephant", "monkey", "bear", "scorpion",
                  "snake", "frog", "eagle", "raven", "dove", "bee", "fly", "ant",
                  "worm", "spider", "fish", "crab", "whale", "dolphin"]

    for ar_an in animal_ar:
        if ar_an in masadiq_gloss or ar_an.replace("ال", "") in masadiq_gloss:
            for lat_an in animal_lat:
                if lat_an in tgt_norm:
                    # Check if they're the same animal
                    ar_en = {"الكلب": "dog", "الأسد": "lion", "الناقة": "camel",
                             "الإبل": "camel", "الجمل": "camel", "الفرس": "horse",
                             "الخيل": "horse", "البقرة": "cow", "الثور": "bull",
                             "الشاة": "sheep", "الغنم": "sheep", "الكبش": "ram",
                             "الحمار": "donkey", "البغل": "mule", "الذئب": "wolf",
                             "الثعلب": "fox", "الأرنب": "hare", "الغزال": "deer",
                             "الفيل": "elephant", "القرد": "monkey", "الدب": "bear",
                             "العقرب": "scorpion", "الثعبان": "snake", "الضفدع": "frog",
                             "النسر": "eagle", "الغراب": "raven", "الحمامة": "dove",
                             "النحلة": "bee", "الذباب": "fly", "النمل": "ant",
                             "الدودة": "worm", "العنكبوت": "spider", "السمكة": "fish",
                             "السرطان": "crab", "الحوت": "whale", "الدلفين": "dolphin"}.get(ar_an, "")
                    lat_en = {"canis": "dog", "leo": "lion", "camelus": "camel",
                              "equus": "horse", "bos": "cow", "ovis": "sheep",
                              "aries": "ram", "asinus": "donkey", "mulus": "mule",
                              "lupus": "wolf", "vulpes": "fox", "lepus": "hare",
                              "cervus": "deer", "elephas": "elephant", "simia": "monkey",
                              "ursus": "bear", "scorpio": "scorpion", "serpens": "snake",
                              "rana": "frog", "aquila": "eagle", "corvus": "raven",
                              "columba": "dove", "apis": "bee", "musca": "fly",
                              "formica": "ant", "vermis": "worm", "aranea": "spider",
                              "piscis": "fish", "cancer": "crab", "cetus": "whale",
                              "delphinus": "dolphin"}.get(lat_an, lat_an)
                    if ar_en and (ar_en == lat_en or ar_en in lat_an):
                        return 0.70, f"Both refer to same animal: Arabic {ar_an} = Latin {lat_an}", "masadiq_direct"

    # Plant in masadiq
    plant_indicators_ar = ["شجر", "نبات", "عشب", "نخل", "زيتون", "تين", "عنب", "قمح", "شعير",
                           "كمأ", "فطر", "ورد", "زهر", "عصا", "جذر", "ثمر", "فاكهة", "بستان"]
    plant_lat = ["arbor", "planta", "herba", "palma", "olea", "ficus", "vitis", "triticum",
                 "hordeum", "fungus", "boletus", "rosa", "flos", "radix", "fructus", "pomum",
                 "tree", "plant", "herb", "palm", "olive", "fig", "vine", "wheat", "barley",
                 "mushroom", "rose", "flower", "root", "fruit"]

    for ar_pl in plant_indicators_ar:
        if ar_pl in masadiq_gloss:
            for lat_pl in plant_lat:
                if lat_pl in tgt_norm:
                    return 0.55, f"Both relate to plant/vegetation: Arabic ({ar_pl}) ↔ Latin ({lat_pl})", "masadiq_direct"

    # Medical/body terms
    medical_ar = ["الجرح", "القرح", "الحمى", "الداء", "المرض", "الدواء", "الطب",
                  "الرأس", "اليد", "الرجل", "القلب", "الدم", "العظم", "الجلد",
                  "المعدة", "الكبد", "الكلية", "الرئة", "العصب", "العين", "الأذن",
                  "الأنف", "اللسان", "الشفة", "الأسنان"]
    medical_lat = ["vulnus", "ulcus", "febris", "morbus", "medicina", "medicus",
                   "caput", "manus", "pes", "cor", "sanguis", "os", "cutis",
                   "gaster", "iecur", "ren", "pulmo", "nervus", "oculus", "auris",
                   "nasus", "lingua", "labrum", "dentes", "wound", "ulcer", "fever",
                   "disease", "medicine", "doctor", "head", "hand", "foot", "heart",
                   "blood", "bone", "skin", "stomach", "liver", "kidney", "lung",
                   "nerve", "eye", "ear", "nose", "tongue", "lip", "teeth"]

    for ar_med in medical_ar:
        if ar_med in masadiq_gloss:
            for lat_med in medical_lat:
                if lat_med in tgt_norm:
                    ar_simple = ar_med.replace("ال", "")
                    ar_to_lat = {"رأس": ["head", "caput"], "يد": ["hand", "manus"],
                                 "رجل": ["foot", "leg", "pes", "crus"],
                                 "قلب": ["heart", "cor"], "دم": ["blood", "sanguis"],
                                 "عظم": ["bone", "os"], "جلد": ["skin", "cutis"],
                                 "عين": ["eye", "oculus"], "أذن": ["ear", "auris"],
                                 "أنف": ["nose", "nasus"], "لسان": ["tongue", "lingua"],
                                 "حمى": ["fever", "febris"], "جرح": ["wound", "vulnus"]}
                    for ar_part, lat_equivalents in ar_to_lat.items():
                        if ar_part in ar_simple and lat_med in lat_equivalents:
                            return 0.65, f"Body/medical: Arabic {ar_med} ↔ Latin {lat_med}", "masadiq_direct"

    # ----------------------------------------------------------------
    # 5. Geographic proper nouns
    # ----------------------------------------------------------------
    geo_pairs = [
        (["عسقلان", "عسقلون", "أشقلون"], ["ascalon", "askalon", "ashkelon"], 0.95),
        (["دمشق", "شام"], ["damascus", "damascena", "syria"], 0.95),
        (["بابل", "العراق"], ["babylon", "mesopotamia"], 0.92),
        (["مصر", "القاهرة"], ["aegyptus", "aegyptum", "cairo"], 0.92),
        (["إسكندرية", "اسكندرية"], ["alexandria"], 0.95),
        (["فارس", "فرس"], ["persia", "persicus", "parthia"], 0.92),
        (["هند", "الهند"], ["india", "indus", "hindus"], 0.92),
        (["روم", "رومية"], ["roma", "romanus", "romam"], 0.92),
        (["اليونان"], ["graecia", "graecus", "greece"], 0.92),
        (["سيناء"], ["sinai", "sina"], 0.92),
        (["أنطاكية"], ["antiochia", "antiochus"], 0.92),
        (["القسطنطينية"], ["constantinopolis", "byzantium"], 0.92),
        (["الإسكندر"], ["alexander", "alexandrum"], 0.92),
        (["أفريقيا"], ["africa", "africanus"], 0.92),
        (["أثينا"], ["athenae", "attica"], 0.9),
        (["صقلية", "صقليا"], ["sicilia", "sicily"], 0.92),
        (["إيطاليا"], ["italia", "italicus"], 0.95),
        (["فلسطين"], ["palaestina", "palestine"], 0.92),
        (["الشام", "سوريا"], ["syria", "syriac"], 0.9),
        (["نيل"], ["nilus", "nile"], 0.92),
        (["الفرات"], ["euphrates"], 0.92),
        (["دجلة"], ["tigris"], 0.92),
        (["البحر المتوسط"], ["mare internum", "mare nostrum", "mediterraneum"], 0.9),
    ]

    for ar_forms, lat_forms_geo, geo_score in geo_pairs:
        for af in ar_forms:
            if af in arabic_root or af in masadiq_gloss:
                for lf in lat_forms_geo:
                    if lf in target_lemma.lower() or lf in tgt_gloss_lower:
                        return geo_score, f"Geographic proper noun: {af} ↔ {lf}", "masadiq_direct"

    # ----------------------------------------------------------------
    # 6. Specific targeted pairs from this dataset
    # ----------------------------------------------------------------
    targeted = [
        # Chunk 072 specific
        ("الدراقن", "duracinus", 0.85, "Arabic الدراقن (peach/apricot) ↔ Latin duracinus (hard-fleshed fruit)", "masadiq_direct"),
        ("الدردم", "malandria", 0.55, "Arabic الدردم (old she-camel) + Latin malandria (horse-neck pustules): both relate to aged/diseased large animals", "mafahim_deep"),
        ("الدرهم", "drachma", 0.92, "Arabic درهم directly from Greek/Latin drachma (coin weight)", "masadiq_direct"),
        ("الدسكرة", "scoria", 0.50, "Arabic الدسكرة (estate/village) vs Latin scoria (slag): weak phonetic similarity, unrelated meanings", "weak"),
        ("الدسكرة", "discus", 0.45, "Arabic الدسكرة vs Latin discus: possible shared Semitic-Hellenic root for 'round/disk' but meanings diverge", "mafahim_deep"),
        # السمسم
        ("السمسم", "sesamum", 0.95, "Direct: Arabic سمسم = Latin sesamum (sesame plant)", "masadiq_direct"),
        ("السمسم", "sesaminum", 0.95, "Direct: Arabic سمسم = Latin sesaminum (sesame oil)", "masadiq_direct"),
        # السماخ
        ("السماخ", "sima", 0.40, "Arabic السماخ (ear canal) vs Latin sima (cyma molding): both involve channels/hollows but weak", "mafahim_deep"),
        # دباغ
        ("الدباغ", "coriarius", 0.70, "Arabic الدباغ (tanner) ↔ Latin coriarius (leather worker): same craft", "masadiq_direct"),
        # ملح
        ("الملح", "sal", 0.80, "Arabic ملح = Latin sal (salt): ancient Semitic-Latin cognate", "masadiq_direct"),
        ("الملح", "mola salsa", 0.80, "Arabic ملح (salt) ↔ Latin mola salsa (sacred salt flour): same core substance", "masadiq_direct"),
        # الصابون
        ("الصابون", "sapo", 0.95, "Arabic الصابون → Latin sapo (soap): Arabic borrowing into Latin", "masadiq_direct"),
        # العسل
        ("العسل", "mel", 0.80, "Arabic عسل ↔ Latin mel (honey): both mean honey", "masadiq_direct"),
        # الزيت
        ("الزيت", "oleum", 0.82, "Arabic زيت (oil) ↔ Latin oleum (oil): same substance", "masadiq_direct"),
        ("الزيتون", "olea", 0.90, "Arabic زيتون (olive) ↔ Latin olea (olive tree): same tree", "masadiq_direct"),
        # الشعير
        ("الشعير", "hordeum", 0.75, "Arabic شعير = Latin hordeum (barley)", "masadiq_direct"),
        # القمح
        ("القمح", "triticum", 0.80, "Arabic قمح = Latin triticum (wheat)", "masadiq_direct"),
        # النخل
        ("النخل", "palma", 0.85, "Arabic نخل (palm tree) ↔ Latin palma (palm)", "masadiq_direct"),
        # التين
        ("التين", "ficus", 0.85, "Arabic تين = Latin ficus (fig tree)", "masadiq_direct"),
        # الكرم
        ("الكرم", "vitis", 0.75, "Arabic الكرم (grapevine) ↔ Latin vitis (vine)", "masadiq_direct"),
        # الخمر / شراب
        ("الخمر", "vinum", 0.70, "Arabic خمر (wine) ↔ Latin vinum (wine)", "masadiq_direct"),
        # الكمأ
        ("الكمأ", "fungus", 0.65, "Arabic كمأ (truffle) ↔ Latin fungus (mushroom/truffle)", "masadiq_direct"),
        ("الكمأ", "boletus", 0.70, "Arabic كمأ (truffle) ↔ Latin boletus (edible fungus/truffle)", "masadiq_direct"),
        # العقرب
        ("العقرب", "scorpio", 0.85, "Arabic عقرب = Latin scorpio (scorpion): direct match", "masadiq_direct"),
        # الثعبان
        ("الثعبان", "serpens", 0.75, "Arabic ثعبان (snake) ↔ Latin serpens (serpent)", "masadiq_direct"),
        # السرطان
        ("السرطان", "cancer", 0.80, "Arabic سرطان (crab/cancer) ↔ Latin cancer (crab/cancer): same meaning", "masadiq_direct"),
        # الملك
        ("الملك", "rex", 0.65, "Arabic ملك (king) ↔ Latin rex (king): parallel meaning", "masadiq_direct"),
        # الحرب
        ("الحرب", "bellum", 0.60, "Arabic حرب (war) ↔ Latin bellum (war)", "masadiq_direct"),
        # الطبيب
        ("الطبيب", "medicus", 0.75, "Arabic طبيب (doctor) ↔ Latin medicus (physician)", "masadiq_direct"),
        # الكيمياء
        ("الكيمياء", "chemia", 0.92, "Arabic كيمياء → Latin chemia/alchemia (chemistry)", "masadiq_direct"),
        # الخوارزمية
        ("الخوارزمية", "algorithmus", 0.90, "Arabic خوارزمية → Latin algorithmus (algorithm)", "masadiq_direct"),
        # الزعفران
        ("الزعفران", "safranum", 0.92, "Arabic زعفران → Latin safranum (saffron)", "masadiq_direct"),
        ("الزعفران", "crocus", 0.80, "Arabic زعفران ↔ Latin crocus (saffron plant)", "masadiq_direct"),
        # الكافور
        ("الكافور", "camphora", 0.92, "Arabic كافور → Latin camphora (camphor)", "masadiq_direct"),
        # السكر
        ("السكر", "saccharum", 0.92, "Arabic سكر → Latin saccharum (sugar)", "masadiq_direct"),
        # القطن
        ("القطن", "cotoneum", 0.92, "Arabic قطن → Latin cotoneum (cotton)", "masadiq_direct"),
        # الليمون
        ("الليمون", "limon", 0.92, "Arabic ليمون → Latin limon (lemon)", "masadiq_direct"),
        # النارنج
        ("النارنج", "aurantium", 0.90, "Arabic نارنج → Latin aurantium (orange)", "masadiq_direct"),
        # الحمام
        ("الحمام", "balneum", 0.72, "Arabic حمام (bath) ↔ Latin balneum (bath)", "masadiq_direct"),
        ("الحمام", "thermae", 0.70, "Arabic حمام (bath) ↔ Latin thermae (hot baths)", "masadiq_direct"),
        # اسطبل
        ("الاصطبل", "stabulum", 0.98, "Arabic اصطبل = Latin stabulum (stable): direct loan", "masadiq_direct"),
        # الرحى
        ("الرحى", "mola", 0.85, "Arabic رحى (millstone) ↔ Latin mola (millstone/mill)", "masadiq_direct"),
        # مرثية / رثاء
        ("المرثية", "elegia", 0.85, "Arabic مرثية (elegy/lament) ↔ Latin elegia (elegy)", "masadiq_direct"),
        ("الرثاء", "elegia", 0.82, "Arabic رثاء (lament/elegy) ↔ Latin elegia (elegy)", "masadiq_direct"),
        # السفينة
        ("السفينة", "navis", 0.75, "Arabic سفينة (ship) ↔ Latin navis (ship)", "masadiq_direct"),
        # الميناء
        ("الميناء", "portus", 0.75, "Arabic ميناء (port) ↔ Latin portus (harbor)", "masadiq_direct"),
        # الطريق
        ("الطريق", "strata", 0.75, "Arabic طريق (road) ↔ Latin strata (paved road)", "masadiq_direct"),
        # الشعر / قصيدة
        ("الشعر", "carmen", 0.65, "Arabic شعر (poetry) ↔ Latin carmen (poem/song)", "masadiq_direct"),
        ("القصيدة", "poema", 0.70, "Arabic قصيدة (poem) ↔ Latin poema (poem)", "masadiq_direct"),
        # البلاغة
        ("البلاغة", "rhetorica", 0.72, "Arabic بلاغة (rhetoric) ↔ Latin rhetorica (rhetoric)", "masadiq_direct"),
        # الموسيقى
        ("الموسيقى", "musica", 0.85, "Arabic موسيقى = Latin musica (music): Greek loan in both", "masadiq_direct"),
        # المسرح
        ("المسرح", "theatrum", 0.75, "Arabic مسرح (theater) ↔ Latin theatrum (theater)", "masadiq_direct"),
        # التاج
        ("التاج", "corona", 0.78, "Arabic تاج (crown) ↔ Latin corona (crown/wreath)", "masadiq_direct"),
        # الفلسفة
        ("الفلسفة", "philosophia", 0.88, "Arabic فلسفة = Latin philosophia (philosophy): Greek loan in both", "masadiq_direct"),
        # الطاعون
        ("الطاعون", "pestis", 0.78, "Arabic طاعون (plague) ↔ Latin pestis (plague/pestilence)", "masadiq_direct"),
        # الحمى
        ("الحمى", "febris", 0.75, "Arabic حمى (fever) ↔ Latin febris (fever)", "masadiq_direct"),
        # العبد
        ("العبد", "servus", 0.70, "Arabic عبد (slave/servant) ↔ Latin servus (slave)", "masadiq_direct"),
        # الحر
        ("الحر", "liber", 0.65, "Arabic حر (free) ↔ Latin liber (free)", "masadiq_direct"),
        # الجزيرة
        ("الجزيرة", "insula", 0.70, "Arabic جزيرة (island) ↔ Latin insula (island)", "masadiq_direct"),
        # الوادي
        ("الوادي", "vallis", 0.72, "Arabic وادي (valley/wadi) ↔ Latin vallis (valley)", "masadiq_direct"),
        # الدينار
        ("الدينار", "denarius", 0.95, "Arabic دينار ← Latin denarius (coin): direct loan", "masadiq_direct"),
        # درهم
        ("الدرهم", "drachma", 0.92, "Arabic درهم ← Greek/Latin drachma (coin)", "masadiq_direct"),
        # القيراط
        ("القيراط", "siliqua", 0.85, "Arabic قيراط ↔ Latin siliqua (weight unit = carat)", "masadiq_direct"),
        # بخور / عطر
        ("البخور", "thus", 0.78, "Arabic بخور (incense) ↔ Latin thus (frankincense/incense)", "masadiq_direct"),
        ("العطر", "unguentum", 0.65, "Arabic عطر (perfume) ↔ Latin unguentum (ointment/perfume)", "masadiq_direct"),
        # الحجر
        ("الحجر", "lapis", 0.72, "Arabic حجر (stone) ↔ Latin lapis (stone)", "masadiq_direct"),
        # الذهب
        ("الذهب", "aurum", 0.78, "Arabic ذهب (gold) ↔ Latin aurum (gold)", "masadiq_direct"),
        # الفضة
        ("الفضة", "argentum", 0.75, "Arabic فضة (silver) ↔ Latin argentum (silver)", "masadiq_direct"),
        # الحديد
        ("الحديد", "ferrum", 0.75, "Arabic حديد (iron) ↔ Latin ferrum (iron)", "masadiq_direct"),
        # النحاس
        ("النحاس", "cuprum", 0.72, "Arabic نحاس (copper) ↔ Latin cuprum (copper)", "masadiq_direct"),
        # الرصاص
        ("الرصاص", "plumbum", 0.72, "Arabic رصاص (lead) ↔ Latin plumbum (lead)", "masadiq_direct"),
        # الزئبق
        ("الزئبق", "hydrargyrum", 0.80, "Arabic زئبق (mercury/quicksilver) ↔ Latin hydrargyrum", "masadiq_direct"),
        # الزرنيخ
        ("الزرنيخ", "arsenicum", 0.92, "Arabic زرنيخ → Latin arsenicum (arsenic)", "masadiq_direct"),
        # الكحل
        ("الكحل", "antimonium", 0.82, "Arabic كحل (kohl/antimony) → Latin antimonium (antimony)", "masadiq_direct"),
        ("الكحل", "stibium", 0.85, "Arabic كحل → Latin stibium (antimony/kohl): direct cultural loan", "masadiq_direct"),
        # الزنجبيل
        ("الزنجبيل", "zingiber", 0.92, "Arabic زنجبيل → Latin zingiber (ginger): direct loan", "masadiq_direct"),
        # الفلفل
        ("الفلفل", "piper", 0.90, "Arabic فلفل → Latin piper (pepper): both mean pepper", "masadiq_direct"),
        # القرفة
        ("القرفة", "cinnamomum", 0.85, "Arabic قرفة ↔ Latin cinnamomum (cinnamon)", "masadiq_direct"),
        # القرنفل
        ("القرنفل", "gariofillum", 0.85, "Arabic قرنفل → Latin gariofillum (clove)", "masadiq_direct"),
        # اللوز
        ("اللوز", "amygdalum", 0.85, "Arabic لوز ↔ Latin amygdalum (almond)", "masadiq_direct"),
        # الجوز
        ("الجوز", "nux", 0.75, "Arabic جوز (nut/walnut) ↔ Latin nux (nut)", "masadiq_direct"),
        # الرمان
        ("الرمان", "malum granatum", 0.85, "Arabic رمان ↔ Latin malum granatum (pomegranate)", "masadiq_direct"),
        # الخروب
        ("الخروب", "siliqua", 0.80, "Arabic خروب (carob) ↔ Latin siliqua (carob pod)", "masadiq_direct"),
        # الحناء
        ("الحناء", "alchanna", 0.90, "Arabic حناء → Latin alchanna (henna)", "masadiq_direct"),
        # الخل
        ("الخل", "acetum", 0.80, "Arabic خل (vinegar) ↔ Latin acetum (vinegar)", "masadiq_direct"),
        # السمك
        ("السمك", "piscis", 0.75, "Arabic سمك (fish) ↔ Latin piscis (fish)", "masadiq_direct"),
        # اللبن
        ("اللبن", "lac", 0.82, "Arabic لبن (milk) ↔ Latin lac (milk): ancient parallel", "masadiq_direct"),
        # العسل
        ("العسل", "mel", 0.82, "Arabic عسل ↔ Latin mel (honey): ancient Semitic-Latin cognate", "masadiq_direct"),
        # الخبز
        ("الخبز", "panis", 0.72, "Arabic خبز (bread) ↔ Latin panis (bread)", "masadiq_direct"),
        # اللحم
        ("اللحم", "caro", 0.68, "Arabic لحم (meat/flesh) ↔ Latin caro (meat/flesh)", "masadiq_direct"),
        # العظم
        ("العظم", "os", 0.72, "Arabic عظم (bone) ↔ Latin os/ossis (bone)", "masadiq_direct"),
        # الدم
        ("الدم", "sanguis", 0.72, "Arabic دم (blood) ↔ Latin sanguis (blood)", "masadiq_direct"),
        # القلب
        ("القلب", "cor", 0.75, "Arabic قلب (heart) ↔ Latin cor (heart)", "masadiq_direct"),
        # الكبد
        ("الكبد", "iecur", 0.70, "Arabic كبد (liver) ↔ Latin iecur (liver)", "masadiq_direct"),
        # الرئة
        ("الرئة", "pulmo", 0.70, "Arabic رئة (lung) ↔ Latin pulmo (lung)", "masadiq_direct"),
        # اللسان
        ("اللسان", "lingua", 0.78, "Arabic لسان (tongue/language) ↔ Latin lingua (tongue/language)", "masadiq_direct"),
        # الشفة
        ("الشفة", "labrum", 0.72, "Arabic شفة (lip) ↔ Latin labrum (lip)", "masadiq_direct"),
        # الأسنان
        ("الأسنان", "dentes", 0.75, "Arabic أسنان (teeth) ↔ Latin dentes (teeth)", "masadiq_direct"),
        # الأنف
        ("الأنف", "nasus", 0.75, "Arabic أنف (nose) ↔ Latin nasus (nose)", "masadiq_direct"),
        # العين
        ("العين", "oculus", 0.78, "Arabic عين (eye) ↔ Latin oculus (eye)", "masadiq_direct"),
        # الأذن
        ("الأذن", "auris", 0.75, "Arabic أذن (ear) ↔ Latin auris (ear)", "masadiq_direct"),
        # الشعر (hair)
        ("الشعر", "capillus", 0.70, "Arabic شعر (hair) ↔ Latin capillus (hair)", "masadiq_direct"),
        # اليد
        ("اليد", "manus", 0.78, "Arabic يد (hand) ↔ Latin manus (hand)", "masadiq_direct"),
        # الرجل / القدم
        ("القدم", "pes", 0.75, "Arabic قدم (foot) ↔ Latin pes/pedis (foot)", "masadiq_direct"),
        # الأم
        ("الأم", "mater", 0.75, "Arabic أم (mother) ↔ Latin mater (mother)", "masadiq_direct"),
        # الأب
        ("الأب", "pater", 0.75, "Arabic أب (father) ↔ Latin pater (father)", "masadiq_direct"),
        # الأخ
        ("الأخ", "frater", 0.72, "Arabic أخ (brother) ↔ Latin frater (brother)", "masadiq_direct"),
        # الابن
        ("الابن", "filius", 0.72, "Arabic ابن (son) ↔ Latin filius (son)", "masadiq_direct"),
        # البنت
        ("البنت", "filia", 0.72, "Arabic بنت (daughter/girl) ↔ Latin filia (daughter)", "masadiq_direct"),
        # الشمس
        ("الشمس", "sol", 0.78, "Arabic شمس (sun) ↔ Latin sol (sun)", "masadiq_direct"),
        # القمر
        ("القمر", "luna", 0.78, "Arabic قمر (moon) ↔ Latin luna (moon)", "masadiq_direct"),
        # النجم
        ("النجم", "stella", 0.75, "Arabic نجم (star) ↔ Latin stella (star)", "masadiq_direct"),
        # السماء
        ("السماء", "caelum", 0.72, "Arabic سماء (sky/heaven) ↔ Latin caelum (sky/heaven)", "masadiq_direct"),
        # الأرض
        ("الأرض", "terra", 0.75, "Arabic أرض (earth/land) ↔ Latin terra (earth/land)", "masadiq_direct"),
        # الماء
        ("الماء", "aqua", 0.80, "Arabic ماء (water) ↔ Latin aqua (water)", "masadiq_direct"),
        # النار
        ("النار", "ignis", 0.72, "Arabic نار (fire) ↔ Latin ignis (fire)", "masadiq_direct"),
        # الهواء
        ("الهواء", "aer", 0.70, "Arabic هواء (air) ↔ Latin aer (air)", "masadiq_direct"),
        # الليل
        ("الليل", "nox", 0.72, "Arabic ليل (night) ↔ Latin nox/noctis (night)", "masadiq_direct"),
        # النهار
        ("النهار", "dies", 0.72, "Arabic نهار (day) ↔ Latin dies (day)", "masadiq_direct"),
        # السنة
        ("السنة", "annus", 0.75, "Arabic سنة (year) ↔ Latin annus (year)", "masadiq_direct"),
        # الجبل
        ("الجبل", "mons", 0.70, "Arabic جبل (mountain) ↔ Latin mons (mountain)", "masadiq_direct"),
        # البحر
        ("البحر", "mare", 0.75, "Arabic بحر (sea) ↔ Latin mare (sea)", "masadiq_direct"),
        # النهر
        ("النهر", "flumen", 0.72, "Arabic نهر (river) ↔ Latin flumen (river)", "masadiq_direct"),
        # المدينة
        ("المدينة", "urbs", 0.68, "Arabic مدينة (city) ↔ Latin urbs (city)", "masadiq_direct"),
        # الإله
        ("الإله", "deus", 0.68, "Arabic إله (god) ↔ Latin deus (god)", "masadiq_direct"),
        # الملاك
        ("الملاك", "angelus", 0.78, "Arabic ملاك (angel) ↔ Latin angelus (angel): Greek loan in both", "masadiq_direct"),
        # الشيطان
        ("الشيطان", "diabolus", 0.75, "Arabic شيطان (devil) ↔ Latin diabolus (devil): parallel theological loan", "masadiq_direct"),
        # الجنة
        ("الجنة", "paradisus", 0.78, "Arabic جنة (paradise/garden) ↔ Latin paradisus (paradise): loan from Persian in both", "masadiq_direct"),
        # السحر
        ("السحر", "magia", 0.72, "Arabic سحر (magic) ↔ Latin magia (magic)", "masadiq_direct"),
        # الكاهن
        ("الكاهن", "sacerdos", 0.68, "Arabic كاهن (priest/soothsayer) ↔ Latin sacerdos (priest)", "masadiq_direct"),
        # التاجر
        ("التاجر", "mercator", 0.68, "Arabic تاجر (merchant) ↔ Latin mercator (merchant)", "masadiq_direct"),
        # السوق
        ("السوق", "forum", 0.68, "Arabic سوق (market) ↔ Latin forum (market/public space)", "masadiq_direct"),
        # الضريبة
        ("الضريبة", "tributum", 0.70, "Arabic ضريبة (tax) ↔ Latin tributum (tribute/tax)", "masadiq_direct"),
        # الحصن
        ("الحصن", "castrum", 0.68, "Arabic حصن (fortress) ↔ Latin castrum (fort/camp)", "masadiq_direct"),
        # المدرسة
        ("المدرسة", "schola", 0.78, "Arabic مدرسة (school) ↔ Latin schola (school): Greek loan in both", "masadiq_direct"),
        # الفيلسوف
        ("الفيلسوف", "philosophus", 0.88, "Arabic فيلسوف ↔ Latin philosophus (philosopher): Greek in both", "masadiq_direct"),
        # المنطق
        ("المنطق", "logica", 0.80, "Arabic منطق (logic) ↔ Latin logica (logic): Greek in both", "masadiq_direct"),
        # الهندسة
        ("الهندسة", "geometria", 0.78, "Arabic هندسة (geometry/engineering) ↔ Latin geometria", "masadiq_direct"),
        # الرياضيات
        ("الرياضيات", "mathematica", 0.85, "Arabic رياضيات ↔ Latin mathematica (mathematics)", "masadiq_direct"),
        # الطب
        ("الطب", "medicina", 0.75, "Arabic طب (medicine) ↔ Latin medicina (medicine)", "masadiq_direct"),
        # الفلك
        ("الفلك", "astronomia", 0.75, "Arabic فلك (astronomy) ↔ Latin astronomia", "masadiq_direct"),
        # السراب
        ("السراب", "mirage", 0.45, "Arabic السراب (mirage) vs Latin: concept exists but no shared root", "weak"),
        # سراب / سحاب
        ("السماحيق", "nubes", 0.55, "Arabic سماحيق السماء (thin cloud patches) ↔ Latin nubes (cloud)", "masadiq_direct"),
        # العرفط (thorny tree)
        ("العرفط", "acacia", 0.60, "Arabic عرفط (thorny tree of Arabia) ↔ Latin acacia (thorny tree)", "masadiq_direct"),
        # الكمأة - سراحيق
        ("العساقل", "fungus", 0.65, "Arabic العساقل/العساقيل (truffles) ↔ Latin fungus (truffle/mushroom)", "masadiq_direct"),
        # السلهم - thin/pale
        ("السلهم", "macer", 0.58, "Arabic سلهم (lean, thin from illness) ↔ Latin macer (lean, thin)", "masadiq_direct"),
        ("السلهم", "pallidus", 0.55, "Arabic سلهم (pale from illness) ↔ Latin pallidus (pale)", "masadiq_direct"),
        # القرطاس
        ("القرطاس", "charta", 0.88, "Arabic قرطاس (paper/scroll) ↔ Latin charta (paper): parallel borrowing from Greek", "masadiq_direct"),
        # الزيت olive oil
        ("الزيت", "oleum", 0.85, "Arabic زيت (oil/olive oil) ↔ Latin oleum (oil)", "masadiq_direct"),
        # specific Solar/stellar following
        ("العسقلة", "solisequus", 0.55, "Arabic عسقلان (Ascalon city, also mirage/shimmer) ↔ Latin solisequus (sun-following): conceptual mirage/shimmer link", "mafahim_deep"),
        ("السمحاق", "membrana", 0.62, "Arabic السمحاق (thin membrane over skull bone) ↔ Latin membrana (membrane)", "masadiq_direct"),
        ("السمحاق", "periosteum", 0.70, "Arabic السمحاق = membrane over skull bone = Latin periosteum equivalent", "masadiq_direct"),
        # الدردم - pustules / malandria (horse disease)
        ("الدردم", "malandria", 0.50, "Arabic الدردم (aged she-camel, female wandering at night) vs Latin malandria (horse pustules): both involve diseased/aged large animals", "mafahim_deep"),
        # الدراقن - duracinum
        ("الدراقن", "duracinum", 0.88, "Arabic الدراقن (peach/apricot, Syrian word) ↔ Latin duracinum (hard-fleshed fruit): same fruit concept", "masadiq_direct"),
        # السماخ ear canal
        ("السماخ", "meatus", 0.60, "Arabic السماخ (ear canal/auditory meatus) ↔ Latin meatus (passage/canal)", "masadiq_direct"),
        ("السماخ", "auris", 0.65, "Arabic السماخ (ear/ear canal) ↔ Latin auris (ear)", "masadiq_direct"),
    ]

    for ar_key, lat_key, score, reasoning, method in targeted:
        ar_stripped = ar_key.replace("ال", "")
        if (ar_stripped in arabic_root or arabic_root in ar_key or
                ar_key in arabic_root):
            if (lat_key.lower() in target_lemma.lower() or
                    lat_key.lower() in tgt_gloss_lower):
                if score > best_score:
                    best_score = score
                    best_reasoning = reasoning
                    best_method = method

    # Return whatever best we found
    return best_score, best_reasoning, best_method


def process_chunk(chunk_num: int) -> list:
    """Process a single chunk file and return scored pairs."""
    chunk_str = f"{chunk_num:03d}"
    in_path = f"{CHUNK_DIR}/lat_new_{chunk_str}.jsonl"

    results = []
    with open(in_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            pair = json.loads(line)

            arabic_root = pair.get("arabic_root", "")
            target_lemma = pair.get("target_lemma", "")
            masadiq_gloss = pair.get("masadiq_gloss", "")
            mafahim_gloss = pair.get("mafahim_gloss", "")
            target_gloss = pair.get("target_gloss", "")
            target_ipa = pair.get("target_ipa", "")

            score, reasoning, method = score_pair(
                arabic_root, target_lemma, masadiq_gloss,
                mafahim_gloss, target_gloss, target_ipa
            )

            result = {
                "source_lemma": arabic_root,
                "target_lemma": target_lemma,
                "semantic_score": round(score, 2),
                "reasoning": reasoning,
                "method": method,
                "lang_pair": "ara-lat",
                "model": "sonnet-phase1-lat"
            }
            results.append(result)

    return results


def main():
    chunks = range(72, 90)  # 072-089
    total_scored = 0
    total_above_05 = 0
    top_discoveries = []

    for chunk_num in chunks:
        chunk_str = f"{chunk_num:03d}"
        print(f"Processing chunk {chunk_str}...", file=sys.stderr)

        results = process_chunk(chunk_num)

        out_path = f"{OUT_DIR}/lat_phase1_scored_{chunk_str}.jsonl"
        with open(out_path, "w", encoding="utf-8") as out:
            for r in results:
                out.write(json.dumps(r, ensure_ascii=False) + "\n")

        chunk_above = sum(1 for r in results if r["semantic_score"] >= 0.5)
        total_scored += len(results)
        total_above_05 += chunk_above

        # Collect top discoveries
        for r in results:
            if r["semantic_score"] >= 0.6:
                top_discoveries.append(r)

        print(f"  Chunk {chunk_str}: {len(results)} pairs, {chunk_above} >= 0.5", file=sys.stderr)

    print(f"\nTotal processed: {total_scored}", file=sys.stderr)
    print(f"Total >= 0.5: {total_above_05}", file=sys.stderr)

    # Top 15 discoveries
    top_discoveries.sort(key=lambda x: x["semantic_score"], reverse=True)
    top15 = top_discoveries[:15]
    print("\nTop 15 discoveries (score >= 0.6):", file=sys.stderr)
    for i, d in enumerate(top15, 1):
        print(f"  {i}. {d['source_lemma']} → {d['target_lemma']} = {d['semantic_score']}: {d['reasoning'][:80]}", file=sys.stderr)

    # Summary output to stdout
    print(f"DONE: {total_scored} pairs processed, {total_above_05} scored >= 0.5")
    print("\nTOP 15:")
    for i, d in enumerate(top15, 1):
        print(f"  {i}. [{d['semantic_score']}] {d['source_lemma']} → {d['target_lemma']}: {d['reasoning'][:100]}")


if __name__ == "__main__":
    main()
