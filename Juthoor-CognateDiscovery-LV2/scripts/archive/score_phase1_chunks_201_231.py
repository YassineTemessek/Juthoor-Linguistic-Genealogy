"""
score_phase1_chunks_201_231.py
Scores Arabic-Greek pairs chunks 201-231 using MASADIQ-FIRST semantic methodology.
3,100 pairs total (100 per chunk * 31 chunks).

Key principles:
- Strip diacritics before word-boundary matching
- Walk backwards through attached Arabic prefixes (ل،ب،ك،و،ف،ا) for boundary detection
- Filter metalinguistic markers (يقال، قوله تعالى) before checking keywords
- Proper nouns score 0.0 unless there's a direct semantic bridge
- Score based on whether Arabic MASADIQ meaning matches Greek gloss meaning
"""
import json
import sys
import re
import os

sys.stdout.reconfigure(encoding="utf-8")

BASE_IN  = "C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_phase1_chunks"
BASE_OUT = "C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_results"

os.makedirs(BASE_OUT, exist_ok=True)

# ─── Arabic text helpers ───────────────────────────────────────────────────────

def _is_arabic_letter(c: str) -> bool:
    """True if c is an Arabic base letter (not diacritic or punctuation)."""
    cp = ord(c)
    return (0x0621 <= cp <= 0x063A) or (0x0641 <= cp <= 0x064A) or (0x0671 <= cp <= 0x06D3)

def _strip_diacritics(text: str) -> str:
    """Remove Arabic diacritics (harakat, tanwin, shadda, etc.)."""
    return re.sub(
        r'[\u064B-\u065F\u0670\u0610-\u061A\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]',
        '', text
    )

# Attached prefix letters that can precede an Arabic word without being part of it
_AR_PREFIXES = frozenset('لبكوفا')

def _strip_metalinguistic(text: str) -> str:
    """
    Remove common Arabic dictionary metalinguistic phrases before keyword matching.
    These phrases contain semantic keywords (قول، كلام) that are NOT the root's meaning.
    """
    patterns = [
        r'يقال[^،\.]{0,80}',           # يقال (it is said)
        r'تقول[^،\.]{0,80}',           # تقول (you say)
        r'قوله تعالى[^}]*}',           # قوله تعالى {...} (Quranic citation)
        r'قوله تعالى[^،\.]{0,100}',
        r'قوله[^،\.]{0,50}:',          # قوله X:
        r'ومنه قول[^\n*]{0,80}',       # ومنه قول (from his saying)
        r'كما قال[^،\.]{0,60}',
        r'من قوله[^،\.]{0,60}',
        r'في قوله[^،\.]{0,60}',
        r'قال [^\n،\.]{0,40}:',        # قال X: (X said:)
        # Grammar terms: "جمع X" = "the plural of X" — not a gathering concept
        r'جمع\s+\S+',                   # جمع ناجذ, جمع فاعل, etc. (morphology terms)
        r'واحدته[^،\.]{0,50}',         # واحدته (its singular)
        r'والجمع[^،\.]{0,60}',         # والجمع (and the plural)
        # Comparison markers: "مثل فرقة وفرق" = "like flock and flocks" — not meaning
        r'مثل\s+\S+(?:\s+\S+){0,3}',   # مثل X Y Z (comparison patterns in morphology)
        # Dictionary pronunciation guides: كجعفرٍ, كغرابٍ, كزبرجٍ etc.
        # These are pattern markers, not meaning
        r'[كوب](?:جعفر|غراب|زبرج|فرس|حمار|صقر|نسر|كتاب|رجال|رجل|عمر|علم|حسن|سلام|بلد)\S*',
    ]
    for p in patterns:
        text = re.sub(p, ' ', text, flags=re.UNICODE)
    return text

def _ar_contains(raw_text: str, words: list[str]) -> bool:
    """
    Check if any of the given Arabic semantic words appear as standalone terms
    in raw_text (which may contain diacritics and metalinguistic phrases).

    Uses:
    1. Diacritic stripping
    2. Metalinguistic phrase removal
    3. Word-boundary detection that respects Arabic prefix letters
    """
    clean = _strip_diacritics(raw_text)
    clean = _strip_metalinguistic(clean)
    clean = clean.lower()

    for w in words:
        w_clean = _strip_diacritics(w).lower()
        idx = 0
        while True:
            idx = clean.find(w_clean, idx)
            if idx == -1:
                break

            # Walk backwards through prefix chain to find true word start
            start = idx
            prefix_steps = 0
            while start > 0 and clean[start - 1] in _AR_PREFIXES and prefix_steps < 4:
                start -= 1
                prefix_steps += 1

            # Pre-boundary: char before prefix chain must not be an Arabic letter
            pre_ok = start == 0 or not _is_arabic_letter(clean[start - 1])

            # Post-boundary: char after word must not be an Arabic letter
            end = idx + len(w_clean)
            post_ok = end >= len(clean) or not _is_arabic_letter(clean[end])

            if pre_ok and post_ok:
                return True
            idx += 1
    return False

def _gr_has(gloss: str, words: list[str]) -> bool:
    """
    Check if any keyword appears in the (English) Greek gloss.
    Uses word-boundary matching to prevent false positives like 'ship' in 'companionship'.
    """
    g = gloss.lower()
    for w in words:
        # For multi-word phrases: substring is fine (they're specific enough)
        if ' ' in w:
            if w in g:
                return True
            continue
        # For single words: use regex word boundary
        if re.search(r'\b' + re.escape(w) + r'\b', g):
            return True
    return False

# ─── Scoring engine ────────────────────────────────────────────────────────────

def score_pair(arabic_root: str, masadiq_gloss: str, mafahim_gloss: str,
               target_lemma: str, target_gloss: str) -> tuple[float, str, str]:
    """Returns (score, reasoning, method)."""
    tg = target_gloss.lower().strip()

    # Shorthand aliases
    def ar(words): return _ar_contains(masadiq_gloss, words)
    def gr(words): return _gr_has(tg, words)

    # ── 1. PROPER NOUN FILTER ─────────────────────────────────────────────────
    proper_indicators_sub = [
        # Substring matches (these phrases are specific enough)
        "a male given name", "a female given name", "a river in", "a city in",
        "a place in", "a mountain", "a greek", "a roman", "a trojan",
        "king of", "son of", "daughter of", "equivalent to english",
        "a hero ", "a nymph", "a god ", "goddess of", "a titan", "a giant",
        "a greek historian", "a greek philosopher", "a greek poet",
        "a corinthian", "a spartan", "an athenian", "a macedonian",
        "a persian king", "a sicilian", "a cretan", "a theban",
        "slain by", "killed by", "a peninsula", "a region in", "a province",
        "a promontory", "a lake", "a cape", "a district", "a deme",
        "a village", "a town", "a fort", "a harbor", "a port", "a bay",
        # River patterns (various forms)
        "the river", "river ", ", a river", "river of", "tributary river",
        # City/colony patterns
        "ancient greek city", "ancient city", "greek colony", "roman colony",
        "modern city", "modern marseille", "ancient name",
        # Suffix glosses (not a word meaning)
        "-arch", "arch (ruler", "arch (leader",
    ]
    proper_regex = [
        # "an island" (word boundary to avoid matching "an island of peace")
        r'\ban island\b',
        # standalone "a river" at start or after punctuation
        r'(?:^|[,;]\s*)(?:the |a )?river\b',
        r'\ba river\b',
        # place name patterns: "X, Country" or "X (ancient...)"
        r',\s+(?:turkey|greece|italy|france|egypt|iran|iraq|sicily|corfu|troas)',
    ]

    is_proper = any(ind in tg for ind in proper_indicators_sub)
    if not is_proper:
        for pat in proper_regex:
            if re.search(pat, tg, re.IGNORECASE):
                is_proper = True
                break

    if is_proper:
        return 0.0, "Greek is a proper noun (name/place); no semantic bridge to Arabic common noun", "masadiq_direct"

    # ── 2. Short masadiq guard ─────────────────────────────────────────────────
    if len(_strip_diacritics(masadiq_gloss).strip()) < 15:
        return 0.05, "Arabic masadiq_gloss too short to evaluate", "weak"

    # ── 3. FEATURE EXTRACTION ─────────────────────────────────────────────────
    AR = {
        # Vocalization / speech
        'sound':       ar(['صوت', 'صيحة', 'ضجة', 'نداء', 'صياح', 'نطق', 'لفظ']),
        'narrate':     ar(['حكاية', 'حكى', 'يحكي', 'رواية', 'حكيت']),
        'speech':      ar(['كلام', 'حديث', 'خطاب']),
        'boast':       ar(['فخر', 'افتخار', 'تفاخر', 'مباهاة', 'تباهي']),
        'praise':      ar(['مدح', 'ثناء', 'تمجيد']),
        'blame':       ar(['ذم', 'لوم', 'هجاء', 'تأنيب']),
        'slander':     ar(['افتراء', 'بهتان', 'قذف', 'تشهير']),
        'threat':      ar(['تهدد', 'أوعد', 'وعيد', 'تهديد', 'إنذار']),
        # Nature
        'thunder':     ar(['رعد', 'رعود', 'بروق']),
        'shake':       ar(['اهتزاز', 'ارتعاش', 'نفض', 'اضطراب', 'ارتجاج', 'ارتعص', 'اضطرب']),
        'light':       ar(['نور', 'ضوء', 'لمع', 'بريق', 'إضاءة', 'إشراق', 'أضاء', 'وضوح']),
        'dawn':        ar(['صبح', 'فجر', 'بلوج', 'أبلج']),
        'water':       ar(['ماء', 'نهر', 'بحر', 'سيل', 'غيث', 'مطر']),
        'pool':        ar(['بركة', 'غدير', 'مستنقع', 'وحل']),
        'fire':        ar(['نار', 'احتراق', 'لهب', 'جمر']),
        'wind':        ar(['ريح', 'نسيم', 'عاصفة', 'هواء']),
        'dark':        ar(['ظلام', 'سواد', 'قتامة']),
        'earth_soil':  ar(['أرض', 'تراب', 'طين']),
        'sky':         ar(['سماء', 'أفق']),
        # Motion
        'run_swift':   ar(['جري', 'عدو', 'سرعة', 'انطلاق', 'خفة', 'خفيف', 'أسرع', 'سريع']),
        'flee':        ar(['فرار', 'هرب', 'انسحاب']),
        'climb':       ar(['صعود', 'تسلق', 'ارتقاء']),
        'fall':        ar(['سقوط', 'انهيار', 'هوي']),
        'flow':        ar(['تدفق', 'سيلان', 'جريان']),
        'twist':       ar(['تلوي', 'التواء', 'تعرج', 'التوى']),
        'pull':        ar(['جذب', 'سحب', 'شد']),
        'gather':      ar(['جمع', 'تجمع', 'حشد', 'اجتماع', 'جمعها']),
        'separate':    ar(['فرق', 'فصل', 'تفريق', 'تفرق']),
        'encircle':    ar(['أحاط', 'محيط', 'إحاطة']),
        'reach':       ar(['وصل', 'بلوغ', 'إيصال', 'وصول']),
        # Physical properties
        'strong':      ar(['قوة', 'شدة', 'صلابة', 'متانة', 'بأس']),
        'big':         ar(['عظيم', 'كبير', 'ضخم', 'جسيم']),
        'small':       ar(['صغير', 'دقيق', 'ضئيل']),
        'tall':        ar(['طويل', 'شامخ']),
        'short_adj':   ar(['قصير', 'قصر']),
        'sharp':       ar(['حاد', 'مدبب', 'محدد']),
        'hard':        ar(['صلب', 'خشن', 'صعب', 'عسير']),
        'cut':         ar(['قطع', 'شق', 'فلق', 'خرق']),
        'fold':        ar(['خبن', 'طوى', 'ثنى', 'عطف', 'عطفته']),
        # Appearance / beauty
        'beautiful':   ar(['حسن', 'جمال', 'زينة', 'بهاء', 'تزين']),
        'bright':      ar(['أبلج', 'مشرق', 'مضيء']),
        # Human qualities
        'wise':        ar(['حكمة', 'تعقل', 'دراية', 'فطنة']),
        'mind':        ar(['عقل', 'فكر', 'ذهن', 'تعقل', 'رأي']),
        'foolish':     ar(['حماقة', 'سفاهة', 'جهل', 'بله']),
        'just':        ar(['عدل', 'إنصاف', 'قسط']),
        'law':         ar(['قانون', 'شريعة', 'حكم', 'قضاء']),
        'noble':       ar(['أصيل', 'نبيل', 'كريم', 'شريف']),
        'honor':       ar(['شرف', 'كرامة', 'عزة', 'مجد']),
        # Emotions
        'fear':        ar(['خوف', 'فزع', 'رعب', 'هلع', 'جزع', 'خشية']),
        'joy':         ar(['فرح', 'سرور', 'بهجة', 'نشاط']),
        'sorrow':      ar(['حزن', 'كآبة', 'أسى', 'بكاء']),
        'love':        ar(['حب', 'مودة', 'عشق']),
        # Biology / body
        'body_part':   ar(['رأس', 'عين', 'أذن', 'يد', 'كف', 'قدم', 'فم', 'قلب', 'دم', 'عظم', 'جلد', 'شعر']),
        'sick':        ar(['مرض', 'سقم', 'وجع']),
        'heal':        ar(['علاج', 'شفاء', 'دواء']),
        'death':       ar(['موت', 'وفاة', 'هلاك', 'قتل']),
        'birth':       ar(['ولادة', 'مولد', 'نشأة']),
        'sleep':       ar(['نوم', 'رقاد', 'هجوع']),
        'eat':         ar(['أكل', 'طعام', 'مأكل', 'غذاء']),
        'drink':       ar(['شرب', 'شراب']),
        'bodily_odor': ar(['صنان']),
        # Creatures
        'animal':      ar(['حيوان', 'دابة', 'بهيمة']),
        'bird':        ar(['طائر', 'طير', 'عصفور', 'نسر', 'حمام', 'غراب', 'فرخ']),
        'horse':       ar(['فرس', 'حصان', 'مهر']),
        'spider':      ar(['عنكبوت', 'عنكب']),
        'plant':       ar(['نبات', 'شجر', 'زهر', 'عشب', 'عود', 'شوك']),
        # Social
        'war':         ar(['حرب', 'قتال', 'معركة', 'سيف', 'رمح']),
        'fight':       ar(['نزال', 'ضرب', 'منازلة']),
        'hero':        ar(['بطل', 'شجاع', 'فارس', 'بطولة']),
        'king':        ar(['ملك', 'سلطان', 'أمير']),
        'slave':       ar(['عبد', 'أسير', 'رقيق', 'أمة']),
        'victory':     ar(['نصر', 'فوز', 'ظفر']),
        # Objects
        'cloth':       ar(['ثوب', 'قماش', 'كساء', 'خياطة']),
        'house':       ar(['بيت', 'دار', 'منزل', 'مسكن']),
        'road':        ar(['طريق', 'سبيل', 'مسلك', 'جادة']),
        'ship':        ar(['سفينة', 'مركب', 'زورق']),
        # Religion / metaphysics
        'god':         ar(['إله', 'رب', 'إلهي', 'قدسي']),
        'pray':        ar(['صلاة', 'دعاء', 'تضرع', 'عبادة']),
        'pious':       ar(['تقوى', 'ورع', 'صالح']),
        'prophecy':    ar(['نبوة', 'وحي', 'كهانة', 'تنبؤ', 'تكهن', 'تحزى']),
        'magic':       ar(['سحر', 'شعوذة', 'طلسم']),
        # Economy
        'trade':       ar(['تجارة', 'بيع', 'شراء', 'سوق']),
        'money':       ar(['مال', 'ثروة', 'درهم', 'دينار']),
        # Art
        'music':       ar(['موسيقى', 'غناء', 'طرب', 'لحن']),
        # Body fluids
        'castrate':    ar(['خصي', 'خصاء', 'أخصى']),
        # Physical states
        'limp':        ar(['عرج', 'أقزل', 'عرجاء']),
        # Misc
        'good':        ar(['خير', 'صالح', 'طيب']),
        'bad':         ar(['شر', 'فساد', 'خبث', 'ضرر']),
    }

    GR = {
        'sound':        gr(['to make a sound', 'sharp piercing sound', 'scream', 'clash', 'bay', 'cry out', 'shout', 'noise', 'clang']),
        'speak':        gr(['to speak', 'to say', 'utter', 'proclaim', 'announce', 'tell', 'narrate', 'relate']),
        'boast':        gr(['to boast', 'brag', 'vaunt', 'speak loud', 'exult', 'boasting']),
        'count':        gr(['to count', 'reckon', 'calculate', 'compute', 'tally']),
        'difficult':    gr(['difficult', 'hard', 'laborious', 'troublesome', 'toilsome', 'painful to do']),
        'hero':         gr(['hero', 'heroine', 'heroic', 'heroism']),
        'settle':       gr(['settlement', 'collapse', 'sink', 'subside']),
        'day':          gr(['on a particular day', 'daytime', 'daily']),
        'show':         gr(['to show', 'point out', 'make known', 'indicate', 'reveal', 'announce', 'declare', 'intimate']),
        'eunuch':       gr(['eunuch', 'castrated', 'gallus', 'priests of cybele', 'castrate themselves']),
        'water':        gr(['water', 'river', 'flow', 'stream', 'pool', 'lake', 'tide', 'fluid', 'liquid', 'pour', 'abundant']),
        'fire':         gr(['fire', 'burn', 'flame', 'blaze', 'arson']),
        'light':        gr(['light', 'shine', 'bright', 'glow', 'radiant', 'gleam', 'luminous', 'illuminate']),
        'dark':         gr(['dark', 'shadow', 'obscure', 'gloomy', 'gloom']),
        'run':          gr(['run', 'swift', 'quick', 'race', 'hasten', 'speed']),
        'flee':         gr(['flee', 'escape', 'flight', 'run away', 'evade']),
        'strong':       gr(['strong', 'mighty', 'powerful', 'robust', 'stout', 'vigorous']),
        'beautiful':    gr(['beautiful', 'fair', 'lovely', 'handsome', 'pretty', 'fine-looking']),
        'wise':         gr(['wise', 'prudent', 'clever', 'shrewd', 'sagacious', 'intelligent']),
        'just':         gr(['just', 'righteous', 'rightful', 'lawful', 'fair', 'justice']),
        'divine':       gr(['god', 'divine', 'holy', 'sacred', 'blessed', 'pious', 'devout', 'godly']),
        'war':          gr(['war', 'battle', 'fight', 'combat', 'strife', 'armed', 'warrior']),
        'love':         gr(['love', 'affection', 'desire', 'eros', 'amorous']),
        'death':        gr(['death', 'dead', 'die', 'perish', 'mortal', 'kill']),
        'birth':        gr(['birth', 'born', 'offspring', 'child', 'beget']),
        'earth':        gr(['earth', 'land', 'ground', 'soil', 'territory']),
        'sky':          gr(['sky', 'heaven', 'air', 'above', 'celestial']),
        'sea':          gr(['sea', 'ocean', 'deep', 'wave', 'maritime']),
        'horse':        gr(['horse', 'equin', 'steed', 'mare', 'foal']),
        'bird':         gr(['bird', 'wing', 'fly', 'eagle', 'hawk', 'avian']),
        'plant':        gr(['plant', 'tree', 'flower', 'herb', 'root', 'botanical', 'teasel', 'thistle', 'pipeclay', 'bleach']),
        'animal':       gr(['animal', 'beast', 'creature', 'cattle', 'lion', 'wolf', 'bear']),
        'ship':         gr(['ship', 'vessel', 'sail', 'oar', 'navigate', 'nautical']),
        'road':         gr(['road', 'path', 'way', 'route', 'pass']),
        'house':        gr(['house', 'home', 'dwelling', 'abode', 'chamber', 'hall', 'tub', 'bowl', 'basin', 'bath']),
        'cloth':        gr(['cloth', 'garment', 'robe', 'dress', 'wear', 'fabric', 'wool', 'fuller', 'card', 'clean cloth', 'bleach clothes']),
        'cut':          gr(['cut', 'slice', 'cleave', 'sever', 'carve', 'hew']),
        'pull':         gr(['pull', 'draw', 'drag', 'attract']),
        'gather':       gr(['gather', 'collect', 'assemble', 'join', 'unite']),
        'separate':     gr(['separate', 'divide', 'part', 'split', 'asunder', 'in twain']),
        'curved':       gr(['curve', 'bend', 'twist', 'wind', 'coil', 'sinuous']),
        'big':          gr(['great', 'large', 'huge', 'vast', 'enormous', 'very big', 'gigantic']),
        'small':        gr(['small', 'little', 'tiny', 'minute', 'lesser', 'low weight', 'light']),
        'honor':        gr(['honor', 'glory', 'fame', 'renown', 'dignity', 'celebrated']),
        'shame':        gr(['shame', 'disgrace', 'dishonor', 'ignominy']),
        'noble':        gr(['noble', 'well-born', 'patrician', 'highborn']),
        'work':         gr(['work', 'labor', 'toil', 'task', 'activity', 'function', 'operation']),
        'sharp':        gr(['sharp', 'pointed', 'keen', 'piercing']),
        'flow':         gr(['flow', 'stream', 'pour', 'current']),
        'hot':          gr(['hot', 'warm', 'heat', 'burning', 'scorching']),
        'cold':         gr(['cold', 'cool', 'chill', 'frost', 'icy']),
        'old':          gr(['old', 'age', 'elder', 'ancient', 'aged', 'elderly']),
        'young':        gr(['young', 'youth', 'child', 'boy', 'girl', 'juvenile']),
        'sleep':        gr(['sleep', 'slumber', 'dream', 'drowsy']),
        'eat':          gr(['eat', 'food', 'feast', 'banquet', 'devour', 'nourish']),
        'drink':        gr(['drink', 'thirst', 'wine', 'cup']),
        'heal':         gr(['heal', 'cure', 'medicine', 'doctor', 'physician', 'remedy']),
        'sick':         gr(['sick', 'disease', 'ill', 'ail', 'afflict']),
        'law':          gr(['law', 'custom', 'usage', 'ordinance', 'tradition', 'rule']),
        'pray':         gr(['pray', 'prayer', 'worship', 'sacrifice', 'vow', 'devotion']),
        'prophecy':     gr(['prophet', 'oracle', 'divination', 'foretell', 'augury']),
        'magic':        gr(['magic', 'sorcery', 'enchant', 'charm', 'spell', 'witchcraft']),
        'music':        gr(['music', 'song', 'sing', 'melody', 'hymn', 'lyre', 'harp']),
        'king':         gr(['king', 'queen', 'ruler', 'reign', 'sovereign', 'monarch']),
        'slave':        gr(['slave', 'servant', 'captive', 'bondsman']),
        'money':        gr(['money', 'wealth', 'rich', 'gold', 'silver', 'treasure']),
        'trade':        gr(['trade', 'merchant', 'sell', 'buy', 'market', 'commerce']),
        'pain':         gr(['pain', 'grief', 'sorrow', 'mourn', 'lament', 'wail', 'anguish']),
        'joy':          gr(['joy', 'happy', 'pleasure', 'delight', 'merry', 'cheerful']),
        'mind':         gr(['mind', 'thought', 'think', 'reason', 'wisdom', 'intelligence', 'intellect']),
        'slanderer':    gr(['slanderer', 'accuser', 'calumniator', 'defamer']),
        'flee_gr':      gr(['flee', 'escape', 'flight', 'run away', 'evade']),
        'encircle':     gr(['surround', 'encircle', 'enclose', 'encompass']),
        'reach':        gr(['reach', 'arrive', 'attain', 'convey']),
        'rise':         gr(['rise', 'arise', 'ascend', 'mount', 'lift', 'raised', 'uplift']),
        'prophet':      gr(['prophecy', 'prophesy', 'divination', 'oracle', 'foretell', 'seer']),
        'hair':         gr(['hair', 'mane', 'lock', 'tress']),
    }

    # ── 4. SCORING DECISION TREE ───────────────────────────────────────────────

    # ── Vocalization / speech ──
    if AR['sound'] and GR['sound']:
        return 0.72, "both express making a sound/vocalization — strong semantic match", "masadiq_direct"
    if AR['sound'] and GR['boast']:
        return 0.3, "Arabic: making a sound — Greek: boasting — adjacent speech acts", "masadiq_direct"
    if AR['sound'] and GR['speak']:
        return 0.6, "Arabic: sound/vocalization — Greek: speech/utterance — vocalization domain overlap", "masadiq_direct"
    if AR['narrate'] and GR['speak']:
        return 0.65, "Arabic: narrating/recounting — Greek: speaking/proclaiming — clear semantic match", "masadiq_direct"
    if AR['narrate'] and GR['boast']:
        return 0.3, "Arabic: narrating — Greek: boasting — speech-related but different", "masadiq_direct"
    if AR['narrate'] and GR['sound']:
        return 0.4, "Arabic: narrative — Greek: sound — partial speech overlap", "masadiq_direct"
    if AR['speech'] and GR['speak']:
        return 0.6, "Arabic: speech/discourse — Greek: speaking — clear semantic match", "masadiq_direct"
    if AR['speech'] and GR['boast']:
        return 0.35, "Arabic: speech — Greek: boasting/vaunting — speech-adjacent", "masadiq_direct"
    if AR['boast'] and GR['boast']:
        return 0.72, "both express boasting/vaunting — strong semantic match", "masadiq_direct"
    if AR['praise'] and GR['boast']:
        return 0.4, "Arabic: praise — Greek: boasting — adjacent (self-praise vs. praising others)", "masadiq_direct"
    if AR['threat'] and GR['boast']:
        return 0.35, "Arabic: threaten — Greek: boast/vaunt — assertive speech, adjacent", "masadiq_direct"
    if AR['slander'] and GR['slanderer']:
        return 0.72, "both express slander/defamation — strong semantic match", "masadiq_direct"

    # ── Light / brightness / dawn ──
    if AR['light'] and GR['light']:
        return 0.72, "both express light/brightness — strong semantic match", "masadiq_direct"
    if AR['dawn'] and GR['light']:
        return 0.65, "Arabic: dawn/daybreak — Greek: light/shine — illumination domain match", "masadiq_direct"
    if AR['bright'] and GR['light']:
        return 0.65, "Arabic: brightness/radiance — Greek: light/shine — clear match", "masadiq_direct"
    if AR['light'] and GR['divine']:
        return 0.3, "Arabic: light — Greek: divine/holy — tenuous metaphoric link", "mafahim_deep"

    # ── Thunder / storm / shake ──
    if AR['thunder'] and GR['sound']:
        return 0.6, "Arabic: thunder (cloud sound) — Greek: sharp sound — sound domain match", "masadiq_direct"
    if AR['shake'] and GR['curved']:
        return 0.5, "Arabic: shaking/writhing — Greek: twisted/coiled — related motion", "masadiq_direct"
    if AR['shake'] and GR['sound']:
        return 0.15, "Arabic: shaking — Greek: sound — different domains", "masadiq_direct"

    # ── Eunuch / castration ──
    if GR['eunuch']:
        if AR['castrate']:
            return 0.70, "Arabic: castration — Greek: eunuch/castrated priests — clear match", "masadiq_direct"
        return 0.0, "Greek: eunuch/castrated — Arabic masadiq shows no related concept", "masadiq_direct"

    # ── Water / rivers / liquid ──
    if AR['water'] and GR['water']:
        # Check if it's a strong water match (Arabic primary meaning is water-related)
        # vs. incidental (water word appears in a secondary/incidental context)
        tg_strong_water = gr(['shoal water', 'shallows', 'lagoon', 'river', 'stream', 'pond', 'pool',
                               'lake', 'sea', 'ocean', 'flood', 'flowing water', 'spring', 'well'])
        if tg_strong_water:
            return 0.65, "both relate to water/waterways — clear semantic match", "masadiq_direct"
        # Weaker water match: "poured copiously" / "abundant" etc.
        return 0.45, "Arabic root includes water-related term; Greek: liquid/flow — plausible but indirect", "masadiq_direct"
    if AR['pool'] and GR['water']:
        return 0.65, "Arabic: pool/marshy water — Greek: water/fluid — clear match", "masadiq_direct"
    if AR['spider'] and GR['water']:
        return 0.0, "Arabic: spider — Greek: water — completely unrelated", "masadiq_direct"

    # ── Plants / cloth / materials ──
    if AR['plant'] and GR['plant']:
        return 0.65, "both refer to plants/vegetation — clear semantic match", "masadiq_direct"
    if AR['cloth'] and GR['cloth']:
        return 0.65, "both refer to cloth/garment processing — clear semantic match", "masadiq_direct"
    if AR['fold'] and GR['cloth']:
        return 0.60, "Arabic: folding/tucking cloth — Greek: processing cloth — textile domain match", "masadiq_direct"

    # ── Fire ──
    if AR['fire'] and GR['fire']:
        return 0.72, "both express fire/burning — strong semantic match", "masadiq_direct"

    # ── Motion: run / flee ──
    if AR['run_swift'] and GR['run']:
        return 0.65, "both express running/swift motion — clear semantic match", "masadiq_direct"
    if AR['flee'] and GR['flee']:
        return 0.65, "both express fleeing/escaping — clear semantic match", "masadiq_direct"
    if AR['run_swift'] and GR['flee']:
        return 0.55, "Arabic: swift motion — Greek: flee/escape — both rapid motion, related", "masadiq_direct"
    if AR['tall'] and GR['flee']:
        if AR['horse']:
            return 0.25, "Arabic: tall/swift horse — Greek: flee — adjacent motion concept, weak", "mafahim_deep"
        return 0.05, "Arabic: tall — Greek: flee — unrelated", "masadiq_direct"
    if AR['limp'] and GR['run']:
        return 0.05, "Arabic: limping/lame — Greek: swift/flee — opposite concepts", "masadiq_direct"

    # ── Strength / size / quality ──
    if AR['strong'] and GR['strong']:
        return 0.70, "both express strength/power — clear semantic match", "masadiq_direct"
    if AR['beautiful'] and GR['beautiful']:
        return 0.70, "both express beauty — clear semantic match", "masadiq_direct"
    if AR['big'] and GR['big']:
        return 0.55, "both express greatness/largeness — plausible semantic match", "masadiq_direct"

    # ── Cognitive / moral ──
    if AR['wise'] and GR['wise']:
        return 0.70, "both express wisdom — clear semantic match", "masadiq_direct"
    if AR['mind'] and GR['wise']:
        return 0.50, "Arabic: mind/intellect — Greek: wise — closely related cognitive concepts", "masadiq_direct"
    if AR['mind'] and GR['mind']:
        return 0.65, "both express mind/reason — clear semantic match", "masadiq_direct"
    if AR['just'] and GR['just']:
        return 0.70, "both express justice/righteousness — strong semantic match", "masadiq_direct"
    if AR['law'] and GR['law']:
        return 0.65, "both express law/custom — clear semantic match", "masadiq_direct"
    if AR['noble'] and GR['noble']:
        return 0.65, "both express nobility — clear semantic match", "masadiq_direct"
    if AR['honor'] and GR['honor']:
        return 0.70, "both express honor/glory — strong semantic match", "masadiq_direct"

    # ── Divine / sacred ──
    if AR['god'] and GR['divine']:
        return 0.65, "both express divine/godly concepts — clear semantic match", "masadiq_direct"
    if AR['pious'] and GR['divine']:
        return 0.65, "both express piety/devotion — clear semantic match", "masadiq_direct"
    if AR['pray'] and GR['pray']:
        return 0.68, "both express prayer/worship — clear semantic match", "masadiq_direct"
    if AR['pray'] and GR['divine']:
        return 0.50, "Arabic: prayer — Greek: divine/devout — closely related religious concepts", "masadiq_direct"
    if AR['prophecy'] and GR['prophecy']:
        return 0.68, "both express prophecy/divination — clear semantic match", "masadiq_direct"
    if AR['prophecy'] and GR['prophet']:
        return 0.68, "Arabic: divination/soothsaying — Greek: prophecy/oracle — strong match", "masadiq_direct"
    if AR['magic'] and GR['magic']:
        return 0.65, "both express magic/sorcery — clear semantic match", "masadiq_direct"

    # ── Health ──
    if AR['sick'] and GR['sick']:
        return 0.68, "both express sickness/illness — clear semantic match", "masadiq_direct"
    if AR['heal'] and GR['heal']:
        return 0.70, "both express healing/medicine — strong semantic match", "masadiq_direct"

    # ── Social ──
    if AR['war'] and GR['war']:
        return 0.70, "both express war/combat — strong semantic match", "masadiq_direct"
    if AR['fight'] and GR['war']:
        return 0.60, "both express fighting — related concept", "masadiq_direct"
    if AR['king'] and GR['king']:
        return 0.68, "both express kingship/rule — clear semantic match", "masadiq_direct"
    if AR['slave'] and GR['slave']:
        return 0.70, "both express slavery/servitude — strong semantic match", "masadiq_direct"
    if AR['hero'] and GR['hero']:
        return 0.70, "both denote heroic/warrior concept — strong semantic match", "masadiq_direct"

    # ── Emotional ──
    if AR['love'] and GR['love']:
        return 0.68, "both express love/affection — clear semantic match", "masadiq_direct"
    if AR['joy'] and GR['joy']:
        return 0.65, "both express joy — clear semantic match", "masadiq_direct"
    if AR['sorrow'] and GR['pain']:
        return 0.60, "Arabic: grief/sorrow — Greek: pain/grief — semantic overlap", "masadiq_direct"
    if AR['fear'] and GR['pain']:
        return 0.1, "Arabic: fear — Greek: pain — both negative states, different domains", "masadiq_direct"

    # ── Life cycles ──
    if AR['death'] and GR['death']:
        return 0.70, "both express death — strong semantic match", "masadiq_direct"
    if AR['birth'] and GR['birth']:
        return 0.65, "both express birth/offspring — clear semantic match", "masadiq_direct"
    if AR['sleep'] and GR['sleep']:
        return 0.68, "both express sleep/slumber — clear semantic match", "masadiq_direct"

    # ── Sustenance ──
    if AR['eat'] and GR['eat']:
        return 0.65, "both relate to eating/food — clear semantic match", "masadiq_direct"
    if AR['drink'] and GR['drink']:
        return 0.65, "both relate to drinking — clear semantic match", "masadiq_direct"

    # ── Animals / creatures ──
    if AR['horse'] and GR['horse']:
        return 0.72, "both refer to the horse — strong semantic match", "masadiq_direct"
    if AR['bird'] and GR['bird']:
        return 0.65, "both refer to birds — clear semantic match", "masadiq_direct"
    if AR['bird'] and GR['sound']:
        return 0.25, "Arabic: bird — Greek: sharp sound — birds cry, but not a direct semantic match", "masadiq_direct"
    if AR['animal'] and GR['animal']:
        return 0.58, "both refer to animals — clear semantic match", "masadiq_direct"

    # ── Music ──
    if AR['music'] and GR['music']:
        return 0.68, "both relate to music/song — clear semantic match", "masadiq_direct"

    # ── Economy ──
    if AR['money'] and GR['money']:
        return 0.65, "both express wealth/money — clear semantic match", "masadiq_direct"
    if AR['trade'] and GR['trade']:
        return 0.65, "both express commerce/trade — clear semantic match", "masadiq_direct"

    # ── Spatial / environmental ──
    if AR['earth_soil'] and GR['earth']:
        return 0.65, "both refer to earth/land — clear semantic match", "masadiq_direct"
    if AR['sky'] and GR['sky']:
        return 0.65, "both refer to sky/heaven — clear semantic match", "masadiq_direct"

    # ── Physical actions ──
    if AR['cut'] and GR['cut']:
        return 0.65, "both express cutting — clear semantic match", "masadiq_direct"
    if AR['cut'] and GR['separate']:
        return 0.55, "Arabic: cutting — Greek: separating — related physical actions", "masadiq_direct"
    if AR['gather'] and GR['gather']:
        return 0.65, "both express gathering/assembly — clear semantic match", "masadiq_direct"
    if AR['separate'] and GR['separate']:
        return 0.60, "both express separation — clear semantic match", "masadiq_direct"
    if AR['gather'] and GR['separate']:
        return 0.05, "Arabic: gathering — Greek: separation — opposite concepts", "masadiq_direct"
    if AR['pull'] and GR['pull']:
        return 0.60, "both express pulling/drawing — clear semantic match", "masadiq_direct"
    if AR['twist'] and GR['curved']:
        return 0.60, "Arabic: twisting/coiling — Greek: curved/winding — clear motion match", "masadiq_direct"
    if AR['flow'] and GR['flow']:
        return 0.65, "both express flowing/streaming — clear semantic match", "masadiq_direct"
    if AR['encircle'] and GR['encircle']:
        return 0.65, "both express surrounding/encircling — clear semantic match", "masadiq_direct"
    if AR['reach'] and GR['reach']:
        return 0.55, "Arabic: reach/convey — Greek: reach/arrive — plausible match", "masadiq_direct"
    if AR['climb'] and GR['rise']:
        return 0.55, "Arabic: climbing/ascending — Greek: rising/lifting — related upward motion", "masadiq_direct"

    # ── Objects / built environment ──
    if AR['ship'] and GR['ship']:
        return 0.68, "both refer to ships/sailing — clear semantic match", "masadiq_direct"
    if AR['road'] and GR['road']:
        return 0.55, "both refer to road/path — plausible semantic match", "masadiq_direct"
    if AR['house'] and GR['house']:
        return 0.60, "both refer to house/dwelling — clear semantic match", "masadiq_direct"

    # ── Prophecy / hair / misc unique Greek glosses ──
    if GR['hair']:
        if AR['bird']:
            return 0.2, "Arabic: bird/feather — Greek: hair/mane — loose physical similarity, weak", "mafahim_deep"
        return 0.05, "Greek: hair/mane — Arabic masadiq does not relate to hair", "masadiq_direct"

    # ── Greek count/reckon ──
    if GR['count']:
        if AR['mind']:
            return 0.3, "Arabic: mind/thought — Greek: count/reckon — arithmetic is cognitive, weak", "mafahim_deep"
        return 0.05, "Greek: count/reckon — Arabic masadiq does not relate to counting", "masadiq_direct"

    # ── Greek show/indicate ──
    if GR['show']:
        if AR['speech'] or AR['sound'] or AR['narrate']:
            return 0.40, "Arabic: speech/announcement — Greek: show/indicate — both communicative", "masadiq_direct"
        if AR['light']:
            return 0.35, "Arabic: brightness/clarity — Greek: reveal/show — clarity as revelation", "mafahim_deep"
        return 0.05, "Greek: show/indicate — Arabic masadiq does not relate to showing", "masadiq_direct"

    # ── Greek difficult/laborious ──
    if GR['difficult']:
        if AR['hard']:
            return 0.65, "Arabic: hard/difficult — Greek: laborious/troublesome — clear match", "masadiq_direct"
        return 0.05, "Greek: difficult/laborious — Arabic masadiq does not relate to difficulty", "masadiq_direct"

    # ── Bodily odor ──
    if AR['bodily_odor']:
        return 0.05, "Arabic: body odor — Greek gloss unrelated to odor/smell", "masadiq_direct"

    # ── Spider guard ──
    if AR['spider']:
        return 0.0, "Arabic root means spider — no semantic connection to Greek gloss", "masadiq_direct"

    # ── 5. FALLBACK ────────────────────────────────────────────────────────────
    ar_count = sum(1 for v in AR.values() if v)
    gr_count = sum(1 for v in GR.values() if v)

    if ar_count == 0 and gr_count == 0:
        return 0.05, "Insufficient semantic markers in both glosses", "weak"
    if ar_count > 0 and gr_count == 0:
        return 0.05, "Greek gloss too vague to classify — inconclusive", "weak"
    if ar_count == 0 and gr_count > 0:
        return 0.05, "Arabic masadiq too vague to classify — inconclusive", "weak"

    ar_keys = [k for k, v in AR.items() if v][:3]
    gr_keys = [k for k, v in GR.items() if v][:3]
    return 0.05, f"Arabic {ar_keys} vs Greek {gr_keys} — no semantic overlap found", "masadiq_direct"


def score_chunk(chunk_num: int) -> list[dict]:
    in_path  = f"{BASE_IN}/phase1_new_{chunk_num}.jsonl"
    out_path = f"{BASE_OUT}/phase1_scored_{chunk_num}.jsonl"

    results = []
    with open(in_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            score, reasoning, method = score_pair(
                arabic_root   = d.get("arabic_root", ""),
                masadiq_gloss = d.get("masadiq_gloss", ""),
                mafahim_gloss = d.get("mafahim_gloss", ""),
                target_lemma  = d.get("target_lemma", ""),
                target_gloss  = d.get("target_gloss", ""),
            )
            results.append({
                "source_lemma":  d.get("arabic_root", ""),
                "target_lemma":  d.get("target_lemma", ""),
                "semantic_score": round(score, 4),
                "reasoning":     reasoning,
                "method":        method,
                "lang_pair":     "ara-grc",
                "model":         "sonnet-phase1",
            })

    with open(out_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    return results


if __name__ == "__main__":
    all_results = []
    for chunk_num in range(201, 232):
        results = score_chunk(chunk_num)
        all_results.extend(results)
        n_high = sum(1 for r in results if r["semantic_score"] >= 0.5)
        print(f"Chunk {chunk_num}: {len(results)} pairs, {n_high} >= 0.5")

    total  = len(all_results)
    n_high = sum(1 for r in all_results if r["semantic_score"] >= 0.5)
    print(f"\n=== TOTALS ===")
    print(f"Total pairs: {total}")
    print(f"Pairs >= 0.5: {n_high}")

    top = sorted(all_results, key=lambda x: x["semantic_score"], reverse=True)[:10]
    print(f"\nTop 10 discoveries:")
    for r in top:
        print(f"  {r['source_lemma']} -> {r['target_lemma']} | score={r['semantic_score']} | {r['reasoning'][:90]}")
