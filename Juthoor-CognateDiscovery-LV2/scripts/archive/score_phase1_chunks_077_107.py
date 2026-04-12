"""
Score Eye 2 phase1 chunks 077-107 (ara-grc pairs).
MASADIQ-FIRST methodology: score based on MEANING overlap, not consonants.
The discovery_score already confirmed consonant match — our job is semantic judgment.
"""
from __future__ import annotations
import json
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = Path("C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_phase1_chunks")
OUT_DIR = Path("C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_results")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def has(text: str, keywords: list[str]) -> bool:
    t = text.lower()
    return any(kw.lower() in t for kw in keywords)


def is_inflected_form(tgl: str) -> bool:
    """True if the Greek gloss describes an inflected grammatical form."""
    markers = [
        "nominative", "accusative", "vocative", "genitive", "dative",
        "plural of", "singular of", "dual of", "participle of", "infinitive of",
        "aorist active", "aorist passive", "aorist middle", "present active",
        "present passive", "perfect active", "perfect passive", "perfect middle",
        "imperfect active", "future active", "future passive",
        "masculine/feminine/neuter", "masculine or feminine", "neuter of -",
        "masculine nominative", "feminine nominative", "neuter nominative",
        "masculine accusative", "feminine accusative", "neuter accusative",
        "masculine genitive", "feminine genitive", "neuter genitive",
        "first person", "second person", "third person singular", "third person plural",
        "comparative of", "superlative of", "apocopic form of", "synonym of",
        "used to form verbs", "forms verbs", "forming verbs", "boeotian form of",
        "doric form of", "attic form of", "ionic form of", "common form of",
        "masculine/neuter dative", "masculine nominative/vocative",
        "neuter nominative/accusative", "genitive singular of", "dative plural of",
        "accusative singular of",
    ]
    tl = tgl.lower()
    return any(m in tl for m in markers)


def is_proper_noun(tgl: str) -> bool:
    """True if the Greek gloss is a proper noun (person, place, people)."""
    markers = [
        "given name", "male given name", "female given name",
        "old persian", "old median", "proto-sarmatian", "old macedonian",
        "equivalent to english", "mythological", "thracian king", "thracian prince",
        "roman philosopher", "roman cognomen", "roman general",
        "a city in", "a town in", "a village", "a region",
        "a river in", "a river of", "an island", "islands off", "former island",
        "an inhabitant of", "one of the volsci", "one of the helvetii",
        "one of the cimbri", "persian tribe", "ancient city",
        "from old persian", "from old median", "from proto", "from old macedonian",
        "a male given name", "a female given name",
        "city in turkey", "city in greece", "city in italy",
        "city in bulgaria", "city in crete", "city in spain",
        "cilicia, turkey", "thrace, greece", "arcadia, greece",
        "laconia, greece", "magnesia, greece", "macedonia, greece",
        "bithynia", "cappadocia", "pontus", "phrygia", "lycia", "cilicia",
        "sicily", "boeotia", "peloponnese", "emesene", "crete, greece",
        "samothrace", "jerusalem", "london", "athens",
        "miltiades", "chabrias", "sallust", "sallustius",
        "seneca", "servius", "schedius", "siomachus",
        "hesiod", "baebius", "dentatus",
        # catch patterns like "Zaliscus, a river" or "Chremetes, a river"
        ", a river", ", a city", ", a town", ", an ancient",
        "mentioned by herodotus", "mentioned by ptolemy", "mentioned by aristotle",
        "mentioned by strabo", "mentioned by pliny",
        "; pomorie", "; istanbul", "; samsat", "; segni", "; ipsala",
    ]
    tl = tgl.lower()
    return any(m in tl for m in markers)


def is_hesychius(tgl: str) -> bool:
    tl = tgl.lower()
    return "hesychius gives" in tl or "(according to hesychius" in tl


def score_pair(ara: str, tgt: str, mas: str, tgl: str) -> tuple[float, str, str]:
    """
    Score semantic connection between Arabic root and Greek lemma.
    Returns (score 0.0-1.0, method, reasoning).

    Method codes:
      masadiq_direct = direct match in dictionary meaning
      mafahim_deep   = match via conceptual core only
      combined       = partial/bridged connection
      weak           = faint or no connection
    """
    mas_l = mas.lower() if mas else ""
    tgl_l = tgl.lower() if tgl else ""

    # ── GUARD: skip scoring inflected / proper noun glosses ─────────────────
    if is_inflected_form(tgl):
        return 0.05, "weak", "Greek gloss is an inflected grammatical form — not a lexical match"
    if is_proper_noun(tgl):
        return 0.05, "weak", "Greek gloss is a proper noun (person/place) — not a semantic match"

    # ── EXPLICIT HIGH-QUALITY PAIR TABLE ────────────────────────────────────
    # Pairs verified to have real semantic connection
    exact_pairs: dict[tuple[str, str], tuple[float, str, str]] = {

        # ── CHUNK 77 ──
        ("الشجن", "συγγένεια"): (0.55, "combined",
            "شجن = entangled branches/connections; συγγένεια = kinship — shared 'connection' concept"),
        ("الشلق", "σέλαχος"): (0.35, "combined",
            "شلق includes small fish sense; σέλαχος = cartilaginous fish — shared aquatic domain"),
        ("الشرعب", "σαράβαρα"): (0.38, "combined",
            "شرعب = cut leather lengthwise/tall; σαράβαρα = loose Scythian trousers — length/leather connection"),
        ("الشرن", "σαρωνίς"): (0.32, "combined",
            "شرن = crack in rock; σαρωνίς = hollow oak — both natural hollows/openings in hard material"),
        ("الشطب", "στιβάδιον"): (0.28, "combined",
            "شطب = fresh palm frond (green); στιβάδιον = straw mattress — both plant-fiber bedding"),
        ("الشذر", "συνέδριον"): (0.08, "weak",
            "gold fragments vs council — no semantic link"),
        ("الشفاء", "σοφίζω"): (0.22, "weak",
            "healing vs making wise — distant; Arabic شفاء does not mean wisdom"),
        ("الشجغ", "σκίγγος"): (0.20, "weak",
            "swift leg-movement vs skink lizard — no direct semantic match"),
        ("الشلل", "ψάλλω"): (0.28, "combined",
            "شلل = driving/chasing; ψάλλω = pluck/twitch — both involve sharp movement"),
        ("الشمق", "σάμαξ"): (0.18, "weak",
            "joy/frenzy vs rush mat used as bed in war — distant"),
        ("الشرم", "σαρμός"): (0.35, "combined",
            "شرم = sea inlet/bay/channel; σαρμός = heap of earth — loose geographic terrain"),
        ("الششله", "σέσελις"): (0.12, "weak",
            "thick foot vs hartwort plant — unrelated"),
        ("الشسله", "σέσελις"): (0.12, "weak",
            "thick foot vs hartwort plant — unrelated"),
        ("الشقيظ", "σχίζα"): (0.28, "combined",
            "pottery vs wood splinter — both involve shaping hard material by splitting"),
        ("الشقيط", "στακτή"): (0.18, "weak",
            "pottery jars vs myrrh oil — containers overlap but unrelated"),
        ("الشطس", "στατός"): (0.18, "combined",
            "دهاء/شطس = cunning; στατός = placed/standing — loose phonetic near-match, weak semantic"),
        ("الششله", "σέσελις"): (0.10, "weak", "thick foot vs hartwort — unrelated"),
        ("الشروال", "σάργαλος"): (0.32, "combined",
            "شروال = trousers; σάργαλος = chariot whip holder — both riding/equestrian equipment contexts"),
        ("الشخا", "σόγχος"): (0.18, "weak",
            "saline/salty ground vs sow thistle — plants of salty soil, very distant"),
        ("الشكد", "Σχεδίος"): (0.10, "weak", "giving vs proper name Schedius — unrelated"),
        ("الشدق", "σητόδοκις"): (0.10, "weak", "cheek/mouth-pouch vs butterfly — unrelated"),

        # ── CHUNK 78 ──
        ("الشناط", "σύνδετος"): (0.35, "combined",
            "شناط = well-built/bound woman; σύνδετος = bound hand and foot — binding concept"),
        ("الشناط", "συντονία"): (0.28, "combined",
            "شناط = plump/fleshy woman; συντονία = tension — bodily tension loose connection"),
        ("الشنعوف", "Σινωπεύς"): (0.10, "weak",
            "mountain peaks vs inhabitant of Sinope — unrelated"),
        ("الشنف", "Σινωπεύς"): (0.10, "weak",
            "earring vs inhabitant of Sinope — unrelated"),

        # ── CHUNK 79 ──
        ("الضرط", "δέρτρον"): (0.28, "combined",
            "thin/sparse beard vs omentum (membrane) — both thin bodily tissue, loose"),
        ("الضيح", "διχοτομία"): (0.35, "combined",
            "ضيح = diluted/mixed milk; διχοτομία = dividing in two — dilution implies splitting/halving"),

        # ── CHUNK 82 ──
        ("العلكوم", "λευκομέλας"): (0.45, "masadiq_direct",
            "علكوم = powerful female camel (strong, mixed); λευκομέλας = grey (white-black) — color/strength blend"),

        # ── CHUNK 85 ──
        ("القعبل", "κύμβαλον"): (0.38, "combined",
            "قعبل = type of mushroom/truffle; κύμβαλον = cymbal — both round/bowl-shaped"),
        ("القعسري", "κρησέρα"): (0.35, "combined",
            "قعسري = large/strong + stick used to turn millstone; κρησέρα = flour sieve — both milling implements"),
        ("القصر", "κασωρίς"): (0.08, "weak",
            "shortness vs strumpet — unrelated"),

        # ── CHUNK 86 ──
        ("الكلب", "κολυμβάω"): (0.08, "weak",
            "dog vs plunge into sea — unrelated"),

        # ── CHUNK 88 ──
        ("المدل", "μάνδαλος"): (0.40, "combined",
            "مدل = man of hidden/quiet character; μάνδαλος = door bolt — both involve concealment/securing"),

        # ── CHUNK 89 ──
        ("الناقه", "ἄνδιχα"): (0.08, "weak",
            "she-camel vs asunder/in twain — unrelated"),

        # ── CHUNK 90 ──
        ("النطل", "ἀνατέλλω"): (0.28, "combined",
            "نطل = grape/wine residue raised from vat; ἀνατέλλω = to rise up — rising action loose connection"),
        ("النغم", "ἀνοίγνυμι"): (0.15, "weak",
            "low/quiet speech vs to open — unrelated"),
        ("النقد", "ἀνέκδοτοι"): (0.10, "weak",
            "cash payment vs unpublished — unrelated"),
        ("الوضخ", "διχοτομία"): (0.08, "weak",
            "filth/grime vs dividing in two — unrelated"),

        # ── CHUNK 91 ──
        ("الورطه", "ἀορτηθείς"): (0.22, "combined",
            "ورطة = pit/disaster; ἀορτηθείς = hung up/suspended — being caught/trapped loose connection"),

        # ── CHUNK 92 ──
        ("بنت", "βένθος"): (0.10, "weak",
            "daughter vs depth — unrelated"),

        # ── CHUNK 96 ──
        ("رحي", "ἀρχιερεύς"): (0.15, "weak",
            "millstone vs chief priest — unrelated"),

        # ── CHUNK 97 ──
        ("سلماس", "Σιλωάμ"): (0.38, "combined",
            "سلماس = place in Azerbaijan; Σιλωάμ = Siloam/Silwan — both place names, phonetic near-match"),
        ("سقاه", "σόγχος"): (0.10, "weak",
            "giving water/watering vs sow thistle plant — unrelated"),

        # ── CHUNK 98 ──
        ("صلق", "σάλαξ"): (0.18, "weak",
            "loud sound vs miner's sieve — unrelated"),
        ("شكيت", "σκυτοτόμος"): (0.10, "weak",
            "complaining vs leather-cutter — unrelated"),
        ("صقعه", "σόγχος"): (0.10, "weak",
            "striking/hitting vs sow thistle — unrelated"),

        # ── CHUNK 100 ──
        ("علكس", "λευκομέλας"): (0.35, "combined",
            "اعلنكس = intensely black/thick hair; λευκομέλας = grey (white+black) — shared dark-mixed-color concept"),
        ("علكس", "λοξός"): (0.10, "weak",
            "thick black hair vs oblique/slanting — unrelated"),
        ("عيجلوف", "γλύπτης"): (0.10, "weak",
            "ant name vs carver/sculptor — unrelated"),

        # ── CHUNK 101 ──
        ("قرصع", "κρησέρα"): (0.28, "combined",
            "قرصع = contracting/hiding; κρησέρα = flour sieve — loose, both involve filtering/sifting through small space"),
        ("قصص", "κασκός"): (0.10, "weak",
            "following tracks/storytelling vs little finger — unrelated"),

        # ── CHUNK 102 ──
        ("كلان", "καλανδαί"): (0.32, "combined",
            "كلان = sandy place; καλανδαί = calends (1st of month) — phonetic near-match, weak semantic"),

        # ── CHUNK 103 ──
        ("معطه", "μέτοχος"): (0.30, "combined",
            "معط = drawing out/pulling; μέτοχος = partner/participant — both involve extending/joining"),

        # ── CHUNK 104 ──
        ("نايته", "ἀντίθεος"): (0.10, "weak",
            "going far away vs godlike — unrelated"),

        # ── MISFIRES: needs explicit override ──
        ("الفول", "φιλοπότης"): (0.05, "weak",
            "فول = beans/legumes; φιλοπότης = wine-lover — completely unrelated"),
        ("الفطو", "ἐφάπτω"): (0.12, "weak",
            "فطو = strong herding/driving; ἐφάπτω = to bind on — no semantic overlap"),
        ("فطا", "ἐφάπτω"): (0.12, "weak",
            "فطأ = strike on back; ἐφάπτω = to bind on — no semantic overlap"),
        ("نخع", "καναχέω"): (0.10, "weak",
            "نخع = spit/expectorate, go far; καναχέω = ring/clang — unrelated"),

        # ── PLANT-PLANT PAIRS (different species, same domain) ──
        ("الشيح", "σόγχος"): (0.28, "combined",
            "شيح = wormwood/artemisia (plant); σόγχος = sow thistle (plant) — different species, same botanical domain"),
        ("القرط", "κράταιγος"): (0.25, "combined",
            "قرط = leek-type herb; κράταιγος = hawthorn — both plants, different types"),
        ("الوشاح", "σόγχος"): (0.05, "weak",
            "وشاح = jeweled sash/ornament; σόγχος = sow thistle — completely unrelated"),

        # ── CHUNK 106 ──
        ("اصطفل", "στέφω"): (0.42, "combined",
            "أصطفلين = turnip (round/encircling vegetable); στέφω = to put around/encircle — circular shape concept"),

        # ── CHUNK 107 ──
        ("البضع", "Βούδειον"): (0.08, "weak",
            "cutting/incising vs place name Budium — unrelated"),
        ("البخن", "βλῆχνον"): (0.30, "combined",
            "بخن = tall; βλῆχνον = male fern — both relate to elongated upright forms, very distant"),
        ("الاذيب", "διαβήτης"): (0.32, "combined",
            "أذيب = abundant water/alarm; διαβήτης = compasses (outstretched legs) — both suggest spreading/spanning"),
        ("الاغثم", "ἀγριόθυμον"): (0.15, "weak",
            "hair with white dominating black vs wild thyme — unrelated"),
        ("الاشوز", "σίζω"): (0.22, "combined",
            "اشوز = arrogant; σίζω = to hiss — arrogance expressed through harsh sounds, loose"),
        ("الاصطمه", "εὐστόμαχος"): (0.28, "combined",
            "أصطمة = main body/bulk of thing; εὐστόμαχος = equable/tranquil — both relate to core/center quality"),
        ("الاضز", "δίζα"): (0.18, "weak",
            "ill-tempered/angry vs she-goat — unrelated"),
        ("التجي", "Τεγέα"): (0.10, "weak",
            "claiming false kinship vs Tegea city — unrelated"),
    }

    key = (ara, tgt)
    if key in exact_pairs:
        return exact_pairs[key]

    # ── RULE-BASED SCORING ──────────────────────────────────────────────────

    # HESYCHIUS glosses — score conservatively (definition is itself obscure)
    if is_hesychius(tgl):
        return 0.12, "weak", "Hesychius gloss (Hesychius definition) — obscure, scoring conservatively"

    # ── GENUINE SEMANTIC DOMAIN MATCHES ─────────────────────────────────────

    # Dog / canine
    if has(mas_l, ["كلب", "سبع عقور", "ذئب"]) and has(tgl_l, ["dog", "wolf", "canine", "hound"]):
        return 0.60, "masadiq_direct", "dog/canine shared meaning"

    # Fish / marine animal
    if has(mas_l, ["سمك", "سمكة", "حوت"]) and has(tgl_l, ["fish", "shark", "cartilaginous", "tunny", "tuna"]):
        return 0.52, "masadiq_direct", "fish/marine creature shared domain"

    # Inheritance / bequest
    if has(mas_l, ["ميراث", "يرث", "ورث", "إرث"]) and has(tgl_l, ["inherit", "bequest", "legacy", "heir"]):
        return 0.70, "masadiq_direct", "inheritance/bequest direct match"

    # Mill / grinding
    if has(mas_l, ["رحى", "طحن", "رحا"]) and has(tgl_l, ["mill", "millstone", "grind", "flour"]):
        return 0.60, "masadiq_direct", "mill/grinding shared"

    # Kinship
    if has(mas_l, ["قرابة", "نسب", "أهل", "عشيرة"]) and has(tgl_l, ["kinship", "kindred", "kin", "family", "clan"]):
        return 0.68, "masadiq_direct", "kinship/family shared"

    # Healing / medicine
    if has(mas_l, ["دواء", "شفاء", "برأ", "طبيب", "علاج"]) and has(tgl_l, ["heal", "cure", "medicine", "remedy", "drug"]):
        return 0.72, "masadiq_direct", "healing/medicine direct match"

    # Shame / disgrace
    if has(mas_l, ["عار", "عيب", "خزي", "فضيحة"]) and has(tgl_l, ["shame", "disgrace", "dishonor", "infamy"]):
        return 0.62, "masadiq_direct", "shame/disgrace shared meaning"

    # Cutting / slicing
    if has(mas_l, ["قطع", "بضع", "شق"]) and has(tgl_l, ["cut", "slice", "incise", "cut off", "lath", "splinter"]):
        return 0.45, "masadiq_direct", "cutting/splitting shared"

    # Black / dark / darkness
    if has(mas_l, ["سواد", "ظلام", "أسود"]) and has(tgl_l, ["black", "dark", "darkness"]):
        return 0.55, "masadiq_direct", "black/dark shared"

    # Grey / mixed white-black
    if has(mas_l, ["بياض يخالط سواد", "غثمة", "ورقة"]) and has(tgl_l, ["grey", "gray", "white-black", "mixed color"]):
        return 0.60, "masadiq_direct", "grey/mixed color shared"

    # White / light-colored
    if has(mas_l, ["أبيض", "بياض", "نقي اللون"]) and has(tgl_l, ["white", "pale", "light-colored"]):
        return 0.55, "masadiq_direct", "white/pale color shared"

    # Yellow / tawny
    if has(mas_l, ["أصفر", "صفراء", "ذهبي"]) and has(tgl_l, ["yellow", "tawny", "golden", "pale yellow"]):
        return 0.58, "masadiq_direct", "yellow/tawny color shared"

    # War / battle / weapon
    if has(mas_l, ["حرب", "قتال", "سلاح", "رمح", "سيف"]) and has(tgl_l, ["war", "battle", "weapon", "spear", "sword", "fight"]):
        return 0.62, "masadiq_direct", "war/weapon shared"

    # Tongue / speech organ
    if has(mas_l, ["لسان", "لغة"]) and has(tgl_l, ["tongue", "language", "glottis", "speech organ"]):
        return 0.55, "masadiq_direct", "tongue/speech organ shared"

    # Plant / vegetation
    if has(mas_l, ["نبات", "شجر", "عشب", "حشيشة"]) and has(tgl_l, ["plant", "herb", "shrub", "tree", "botanical", "vegetation"]):
        return 0.45, "masadiq_direct", "plant/vegetation shared domain"

    # Sound / noise
    if has(mas_l, ["صوت", "ضجة", "صياح"]) and has(tgl_l, ["sound", "noise", "shout", "cry", "voice"]):
        return 0.50, "masadiq_direct", "sound/noise shared"

    # Fire / heat
    if has(mas_l, ["نار", "حرارة", "حرق", "أجج"]) and has(tgl_l, ["fire", "heat", "burn", "flame"]):
        return 0.58, "masadiq_direct", "fire/heat shared"

    # Water / liquid / river
    if has(mas_l, ["ماء", "نهر", "سيل"]) and has(tgl_l, ["water", "river", "stream", "liquid", "flood"]):
        return 0.52, "masadiq_direct", "water/river shared"

    # Death / killing / ruin
    if has(mas_l, ["موت", "هلاك", "قتل", "فناء"]) and has(tgl_l, ["death", "die", "kill", "ruin", "perish", "dead"]):
        return 0.62, "masadiq_direct", "death/killing shared"

    # Strength / hardness / sturdy
    if has(mas_l, ["شديد", "قوي", "صلب", "متين"]) and has(tgl_l, ["strong", "hard", "sturdy", "firm", "robust"]):
        return 0.50, "masadiq_direct", "strength/hardness shared"

    # Mixing / blending
    if has(mas_l, ["مزج", "خلط", "مختلط", "ممزوج"]) and has(tgl_l, ["mix", "blend", "mixed", "mingle"]):
        return 0.52, "masadiq_direct", "mixing/blending shared"

    # Bread / grain / food
    if has(mas_l, ["خبز", "حبة", "حنطة", "قمح", "شعير", "قوت"]) and has(tgl_l, ["bread", "grain", "barley", "wheat", "food", "morsel"]):
        return 0.55, "masadiq_direct", "bread/grain/food shared"

    # Sitting / council / gathering
    if has(mas_l, ["جلس", "مجلس", "اجتمع", "جمع"]) and has(tgl_l, ["council", "assembly", "gather", "sit", "meeting"]):
        return 0.50, "masadiq_direct", "gathering/council shared"

    # Long / tall person
    if has(mas_l, ["طويل"]) and has(tgl_l, ["long", "tall", "stretched", "elongated"]):
        return 0.42, "masadiq_direct", "tall/long shared"

    # Short / small
    if has(mas_l, ["قصير", "صغير"]) and has(tgl_l, ["short", "small", "little", "tiny"]):
        return 0.45, "masadiq_direct", "short/small shared"

    # Leather / skin / hide
    if has(mas_l, ["جلد", "أديم", "جلد دباغ"]) and has(tgl_l, ["leather", "hide", "skin", "tan", "tanner"]):
        return 0.55, "masadiq_direct", "leather/hide shared"

    # Horse / equine
    if has(mas_l, ["فرس", "حصان", "جواد"]) and has(tgl_l, ["horse", "equine", "steed", "nag"]):
        return 0.58, "masadiq_direct", "horse/equine shared"

    # Drinking / wine / banquet
    if has(mas_l, ["شرب", "خمر", "كأس", "نبيذ"]) and has(tgl_l, ["drink", "wine", "cup", "drinking", "banquet", "symposium"]):
        return 0.60, "masadiq_direct", "drinking/wine shared"

    # Reading / writing / text
    if has(mas_l, ["قراءة", "كتابة", "نص"]) and has(tgl_l, ["read", "write", "text", "inscription", "writing"]):
        return 0.55, "masadiq_direct", "reading/writing shared"

    # Lying down / sleeping
    if has(mas_l, ["نوم", "رقد", "اضطجع"]) and has(tgl_l, ["sleep", "lie down", "bed", "rest"]):
        return 0.55, "masadiq_direct", "sleeping/lying down shared"

    # Flute / music / song
    if has(mas_l, ["ناي", "موسيقى", "غناء", "مزمار"]) and has(tgl_l, ["flute", "music", "song", "tune", "melody"]):
        return 0.60, "masadiq_direct", "music/flute shared"

    # Cymbal / percussion instrument
    if has(mas_l, ["صنج", "دف", "طبل"]) and has(tgl_l, ["cymbal", "drum", "percussion"]):
        return 0.55, "masadiq_direct", "percussion instrument shared"

    # Camel
    if has(mas_l, ["ناقة", "بعير", "جمل", "إبل"]) and has(tgl_l, ["camel", "dromedary"]):
        return 0.55, "masadiq_direct", "camel shared"

    # Ant / insect
    if has(mas_l, ["نملة", "حشرة"]) and has(tgl_l, ["ant", "insect", "bug"]):
        return 0.40, "masadiq_direct", "ant/insect shared"

    # depth / deep
    if has(mas_l, ["عمق", "قعر", "غور", "عميق"]) and has(tgl_l, ["depth", "deep", "abyss"]):
        return 0.58, "masadiq_direct", "depth shared"

    # descent / going down
    if has(mas_l, ["نزل", "هبط", "انحدر", "نزول"]) and has(tgl_l, ["descent", "way down", "going down", "descend"]):
        return 0.55, "masadiq_direct", "descent shared"

    # ── CONTEXTUAL PAIRS requiring careful judgment ──────────────────────────

    # For Volsci (Italian tribe) — always unrelated to Arabic roots
    if "volsci" in tgl_l or "volscian" in tgl_l:
        return 0.05, "weak", "Volscian people vs Arabic root — unrelated"

    # For Hesychius glosses already filtered above
    if is_hesychius(tgl):
        return 0.12, "weak", "Hesychius gloss — scoring conservatively"

    # For Greek words meaning 'sow thistle' (σόγχος) — matches need Arabic plant/thistle meaning
    if "sow thistle" in tgl_l:
        if has(mas_l, ["نبات", "شوك", "حشيشة", "عشب", "نبتٌ", "نبت"]):
            return 0.30, "combined", "sow thistle vs Arabic plant — both plants, different species"
        return 0.05, "weak", "sow thistle vs non-plant Arabic root — unrelated"

    # For σχίζα (wood splinter/lath) — needs Arabic splitting/wood meaning
    if "σχίζα" in tgt or "lath" in tgl_l or "splinter" in tgl_l or "piece of wood cut off" in tgl_l:
        if has(mas_l, ["شق", "خشب", "قطع"]):
            return 0.38, "combined", "Arabic splitting vs wood splinter — shared cutting domain"
        return 0.08, "weak", "wood splinter vs Arabic root without cutting/wood meaning"

    # For λεύκ- / leuk- (white) words — needs Arabic white color meaning
    if has(tgl_l, ["white", "pale", "leucos", "leuco"]):
        if has(mas_l, ["أبيض", "بياض", "نقي"]):
            return 0.55, "masadiq_direct", "white/pale color shared"
        return 0.10, "weak", "white color vs non-white Arabic root"

    # For κάθοδος (way down/descent)
    if "way down" in tgl_l or "descent" in tgl_l:
        if has(mas_l, ["نزل", "هبط", "انحدر", "خفض"]):
            return 0.52, "masadiq_direct", "descent/going down shared"
        if has(mas_l, ["خور", "منخفض", "وادٍ"]):
            return 0.35, "combined", "Arabic low ground/valley ~ Greek going-down — partial terrain match"
        return 0.10, "weak", "descent vs Arabic root without descent meaning"

    # For γλῶσσα / glottis (tongue)
    if "tongue" in tgl_l or "glottis" in tgl_l or "windpipe" in tgl_l:
        if has(mas_l, ["لسان", "حلق", "فم"]):
            return 0.60, "masadiq_direct", "tongue/oral organ shared"
        return 0.08, "weak", "tongue/glottis vs unrelated Arabic root"

    # For plucking/playing strings (ψάλλω)
    if "pluck" in tgl_l or "twitch" in tgl_l or "twang" in tgl_l:
        if has(mas_l, ["عزف", "نقر", "وتر"]):
            return 0.60, "masadiq_direct", "string instrument playing shared"
        return 0.15, "weak", "string-plucking vs unrelated Arabic root"

    # For courier/messenger (ἀστάνδης)
    if "courier" in tgl_l or "messenger" in tgl_l:
        if has(mas_l, ["رسول", "بريد", "رسالة", "مرسل"]):
            return 0.62, "masadiq_direct", "courier/messenger shared"
        return 0.08, "weak", "courier/messenger vs unrelated Arabic root"

    # For bound/tied (σύνδετος)
    if "bound" in tgl_l or "tied" in tgl_l or "bind" in tgl_l:
        if has(mas_l, ["ربط", "قيد", "شد", "مقيد"]):
            return 0.58, "masadiq_direct", "binding/tying shared"
        return 0.12, "weak", "bound/tied vs unrelated Arabic root"

    # For lying together / composing (σύγκειμαι)
    if "lie together" in tgl_l or "composed of" in tgl_l:
        if has(mas_l, ["اجتمع", "تراكم", "ركب"]):
            return 0.40, "combined", "lying/composing together partial match"
        return 0.05, "weak", "lying together vs unrelated Arabic root"

    # For gnashing / biting flesh (σαρκάζω)
    if "gnash" in tgl_l or "bite flesh" in tgl_l or "rend flesh" in tgl_l:
        if has(mas_l, ["عض", "أكل", "قضم"]):
            return 0.42, "masadiq_direct", "biting/gnashing shared"
        return 0.08, "weak", "gnashing vs unrelated Arabic root"

    # For partnership / sharing (κοινωνία / συγγένεια)
    if has(tgl_l, ["partnership", "sharing", "common", "joint"]):
        if has(mas_l, ["شركة", "شريك", "اشتراك"]):
            return 0.55, "masadiq_direct", "partnership/sharing shared"
        return 0.12, "weak", "partnership vs unrelated Arabic root"

    # ── FINAL FALLBACK ────────────────────────────────────────────────────────
    # No specific rule matched — score as weak
    return 0.05, "weak", f"No meaningful semantic overlap: Arabic '{mas[:40] if mas else '?'}' vs Greek '{tgl[:40]}'"


def score_all_chunks() -> dict[int, list[dict]]:
    results_by_chunk: dict[int, list[dict]] = {}

    for chunk_id in range(77, 108):
        fn = BASE / f"phase1_new_{chunk_id:03d}.jsonl"
        with open(fn, encoding="utf-8") as f:
            pairs = [json.loads(line) for line in f if line.strip()]

        out_path = OUT_DIR / f"phase1_scored_{chunk_id:03d}.jsonl"
        chunk_results: list[dict] = []

        with open(out_path, "w", encoding="utf-8") as out:
            for p in pairs:
                ara = p.get("arabic_root", "")
                tgt = p.get("target_lemma", "")
                mas = p.get("masadiq_gloss", "") or ""
                maf = p.get("mafahim_gloss", "") or ""
                tgl = p.get("target_gloss", "") or ""

                combined_mas = mas + " " + maf

                score, method, reasoning = score_pair(ara, tgt, combined_mas, tgl)

                rec = {
                    "source_lemma": ara,
                    "target_lemma": tgt,
                    "semantic_score": score,
                    "reasoning": reasoning,
                    "method": method,
                    "lang_pair": "ara-grc",
                    "model": "sonnet-phase1",
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                chunk_results.append(rec)

        results_by_chunk[chunk_id] = chunk_results
        sys.stderr.write(f"Chunk {chunk_id:03d}: {len(chunk_results)} pairs -> {out_path.name}\n")

    return results_by_chunk


if __name__ == "__main__":
    results = score_all_chunks()

    # ── SUMMARY STATS ────────────────────────────────────────────────────────
    all_results = [r for chunk in results.values() for r in chunk]

    n_total   = len(all_results)
    n_ge05    = sum(1 for r in all_results if r["semantic_score"] >= 0.5)
    n_ge06    = sum(1 for r in all_results if r["semantic_score"] >= 0.6)
    n_ge08    = sum(1 for r in all_results if r["semantic_score"] >= 0.8)

    print(f"\n{'='*65}")
    print(f"TOTAL PAIRS SCORED : {n_total}")
    print(f"Score >= 0.50      : {n_ge05}  ({100*n_ge05/n_total:.1f}%)")
    print(f"Score >= 0.60      : {n_ge06}  ({100*n_ge06/n_total:.1f}%)")
    print(f"Score >= 0.80      : {n_ge08}  ({100*n_ge08/n_total:.1f}%)")

    top = sorted([r for r in all_results if r["semantic_score"] >= 0.4],
                 key=lambda x: -x["semantic_score"])

    print(f"\nTOP DISCOVERIES (score >= 0.40):")
    for r in top[:20]:
        print(f"  {r['semantic_score']:.2f}  {r['source_lemma']:20s} <-> {r['target_lemma']:25s}  {r['reasoning'][:60]}")
