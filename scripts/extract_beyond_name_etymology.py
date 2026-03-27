"""
Extract Arabic-English etymology pairs from Beyond_the_Name_Etymology_Extraction.md.
Produces:
  - beyond_name_etymology_pairs.csv
  - beyond_name_cognate_gold_candidates.jsonl
"""
import re
import csv
import json
import unicodedata
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE = Path("C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy")
INPUT_MD = BASE / "Juthoor-CognateDiscovery-LV2/docs/Beyond_the_Name_Etymology_Extraction.md"
OUTPUT_DIR = BASE / "Juthoor-CognateDiscovery-LV2/data/processed"
OUT_CSV  = OUTPUT_DIR / "beyond_name_etymology_pairs.csv"
OUT_JSONL = OUTPUT_DIR / "beyond_name_cognate_gold_candidates.jsonl"
GOLD_JSONL = BASE / "Juthoor-CognateDiscovery-LV2/resources/benchmarks/cognate_gold.jsonl"

# ─── Load existing gold pairs to avoid duplicates ────────────────────────────
existing_pairs: set[tuple[str, str]] = set()
if GOLD_JSONL.exists():
    for line in GOLD_JSONL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            src_lemma = obj.get("source", {}).get("lemma", "").lower()
            tgt_lemma = obj.get("target", {}).get("lemma", "").lower()
            if src_lemma and tgt_lemma:
                existing_pairs.add((src_lemma, tgt_lemma))
        except json.JSONDecodeError:
            pass
print(f"Loaded {len(existing_pairs)} existing gold pairs to skip.")

# ─── Transliteration helpers ─────────────────────────────────────────────────
ARABIC_TRANSLIT = {
    'ا': 'a', 'أ': 'a', 'إ': 'i', 'آ': 'aa', 'ء': "'",
    'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j', 'ح': 'h',
    'خ': 'kh', 'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z',
    'س': 's', 'ش': 'sh', 'ص': 's', 'ض': 'd', 'ط': 't',
    'ظ': 'z', 'ع': "'", 'غ': 'gh', 'ف': 'f', 'ق': 'q',
    'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n', 'ه': 'h',
    'و': 'w', 'ي': 'y', 'ى': 'a', 'ة': 'a',
    'َ': 'a', 'ِ': 'i', 'ُ': 'u', 'ّ': '', 'ْ': '',
    'ً': 'an', 'ٍ': 'in', 'ٌ': 'un',
}

def transliterate_arabic(text: str) -> str:
    """Simple ASCII transliteration of Arabic text."""
    result = []
    for ch in text:
        if ch in ARABIC_TRANSLIT:
            result.append(ARABIC_TRANSLIT[ch])
        elif unicodedata.category(ch).startswith('L') and ord(ch) > 127:
            # Unknown Arabic-range char — skip
            pass
        else:
            result.append(ch)
    return "".join(result).strip()

def strip_arabic_diacritics(text: str) -> str:
    """Remove tashkeel (diacritics) from Arabic text."""
    diacritics = 'ًٌٍَُِّْٰ'
    return "".join(c for c in text if c not in diacritics)

# ─── Parse markdown into entries ─────────────────────────────────────────────
def parse_entries(text: str) -> list[dict]:
    """Split the markdown into a list of entry dicts."""
    entries = []
    # Split on --- separator (entry boundaries)
    raw_blocks = re.split(r'\n---\n', text)
    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue
        # Extract heading
        heading_match = re.match(r'^## (.+)', block, re.MULTILINE)
        if not heading_match:
            continue
        heading = heading_match.group(1).strip()

        # Extract Post ID
        post_id_match = re.search(r'\*\*Post ID:\*\*\s*(\S+)', block)
        post_id = post_id_match.group(1).strip() if post_id_match else ""

        # Extract Etymological Story
        story_match = re.search(
            r'\*\*Etymological Story:\*\*\s*(.*?)(?=\n- \*\*Linguistic Link:\*\*)',
            block, re.DOTALL
        )
        story = story_match.group(1).strip() if story_match else ""

        # Extract Linguistic Link
        link_match = re.search(r'\*\*Linguistic Link:\*\*\s*(.*?)$', block, re.DOTALL)
        ling_link = link_match.group(1).strip() if link_match else ""

        entries.append({
            "heading": heading,
            "post_id": post_id,
            "story": story,
            "ling_link": ling_link,
            "full_text": story + "\n" + ling_link,
        })
    return entries

# ─── Skip heuristics ─────────────────────────────────────────────────────────
SKIP_PATTERNS = [
    r'^Link only:',
    r'^Image only',
    r'يوسف طيبه',        # Egyptian-Arabic essays
    r'د\. محمد سامح',
    r'محتويات كتاب',    # book table of contents announcements
    r'صفحتنا الشقيقة',
    r'تهنئة كنعانية',
    r'قراءة هيروغليفي',
    r'الترجمة الاحترافية',
    r'Big shout out',
    r'Adding a post',
    r'How to upload',
    r'آخر أخبار',
    r'معلومة قد تفاجِئُك',
    r'Vitali',
    r'قريباً في الأسواق',
    r'جلجامش',
    r'قصيدة المتنبي',
    r'عذلُ العواذلِ',
    r'وَشامِخٍ',
    r'ما زالت الحضارة',
    r'العرنجية',
    r'الترجمة',
]

NON_ETYMOLOGICAL_HEADINGS = {
    'N/A', 'المصرية القديمة واللغة العربية', 'نبارك لصفحتنا', 'معرض القاهرة',
    'قصيدة المتنبي', 'عذلُ العواذلِ', 'وَشامِخٍ مِنَ الجِبالِ',
    'Big shout out', 'محتويات كتاب المدونثر', 'محتويات كتاب كنز',
    'Adding a post', 'How to upload a post', 'آخر أخبار ليلى',
    'معلومة قد تفاجِئُك', 'تعليم الكتابة الهيروغليفية',
    'تهنئة كنعانية', 'قراءة هيروغليفي', 'الترجمة الاحترافية',
    'ما زالت الحضارة', 'عن صفحتنا الشقيقة', 'قريباً في الأسواق',
    'جلجامش', 'العرنجية', 'الترجمة',
    'تأصيل كيبوتس', '"دحية" نبي',
}

def should_skip(entry: dict) -> bool:
    heading = entry["heading"].strip()
    story = entry["story"].strip()
    ling_link = entry["ling_link"].strip()

    # Skip N/A headings explicitly
    if heading == 'N/A':
        return True

    # Check exact non-etymological headings
    for neh in NON_ETYMOLOGICAL_HEADINGS:
        if neh in heading:
            return True

    # Check heading starts with Arabic only (essays)
    if heading and all(ord(c) > 127 or c in ' ،؟!؟' for c in heading) and len(heading) > 15:
        # Long all-Arabic heading = essay, not a word
        return True

    # Check story-only patterns (not ling_link — many have N/A ling_link but valid story)
    # Only run patterns on story (the main content), not on the ling_link field
    for pat in SKIP_PATTERNS:
        if re.search(pat, story, re.MULTILINE):
            return True

    # Skip link-only and image-only entries (ling_link check)
    if re.search(r'^Link only:|^Image only', story, re.MULTILINE):
        return True

    # Skip if heading is N/A and story is trivially short
    full = story + "\n" + ling_link
    if len(full.strip()) < 30:
        return True
    return False

# ─── Group entry detection ────────────────────────────────────────────────────
# Group entries contain patterns like: كلمة X يقابلها "Y"
GROUP_PATTERN = re.compile(
    r'كلمة\s+([A-Za-z][A-Za-z0-9\s\(\)\-\.]*?)\s+(?:يقابلها|تقابلها|يقابله|تقابله|جاءت من كلمة)\s+"([^"]+)"',
    re.MULTILINE
)
# Also: كلمة X يقابلها كلمة "Y"
GROUP_PATTERN2 = re.compile(
    r'([A-Za-z][A-Za-z0-9\(\)\-\.]*)\s+(?:يقابلها|يقابله|تقابلها)\s+"([^"]+)"',
    re.MULTILINE
)
# Pattern for compound words: Subword = Arabic
COMPOUND_PATTERN = re.compile(
    r'"([A-Za-z][A-Za-z0-9\-\.]*?)"\s+(?:يقابلها|يقابله|تقابلها|فيقابلها|فيقابلهما|فيقابلهم)\s+(?:في العربية\s+)?(?:كلمة\s+)?"([^"]+)"',
    re.MULTILINE
)
# Inline يقابلها in main text
INLINE_PATTERN = re.compile(
    r'(?:أن\s+)?(?:كلمة\s+)?"([A-Za-z][A-Za-z0-9\s\(\)\-\.]{0,30}?)"\s+(?:يقابلها|يقابله|تقابلها|فيقابلها)\s+(?:في العربية\s+)?(?:كلمة\s+)?"([^"]{1,60})"',
    re.MULTILINE
)

# ─── Arabic root extraction helpers ──────────────────────────────────────────
ARABIC_WORD_RE = re.compile(r'[\u0600-\u06FF\u0750-\u077F]+')

def extract_arabic_words_from_text(text: str) -> list[str]:
    """Extract meaningful Arabic words from text."""
    return [w for w in ARABIC_WORD_RE.findall(text) if len(w) >= 2]

def extract_meaning_from_context(text: str, arabic_root: str) -> str:
    """Try to extract meaning of Arabic root from surrounding context."""
    # Look for patterns like: "X" وتعني "Y" or X: Y or X أي Y
    patterns = [
        rf'"{re.escape(arabic_root)}"\s+(?:وتعني|وتعني|أي|يعني|تعني)\s+"?([^"،\n]{2,60})"?',
        rf'{re.escape(arabic_root)}\s*:\s*([^،\n]{2,50})',
        rf'{re.escape(arabic_root)}\s+أي\s+"?([^"،\n]{2,50})"?',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()
    return ""

# ─── Main extraction logic ───────────────────────────────────────────────────
def extract_pairs_from_entry(entry: dict) -> list[dict]:
    """Extract one or more etymology pairs from a single entry."""
    pairs = []
    heading = entry["heading"].strip()
    post_id = entry["post_id"]
    story = entry["story"]
    ling_link = entry["ling_link"]
    full_text = story + "\n" + ling_link

    # ── GROUP ENTRIES (المجموعة) ──────────────────────────────────────────────
    is_group = "المجموعة" in story[:300] or "المجموعة" in heading
    if is_group:
        pairs.extend(_extract_group_pairs(heading, post_id, full_text))
        if pairs:
            return pairs

    # ── COMPOUND WORD ENTRIES ─────────────────────────────────────────────────
    # If heading is multi-word compound like "Submarine", "Mastectomy"
    # Check if the text discusses morpheme-by-morpheme breakdown
    is_compound = bool(re.search(r'مكونة? من (?:شقين|جزئين|جزأين|مقطعين)', full_text))
    if is_compound:
        comp_pairs = _extract_compound_pairs(heading, post_id, full_text)
        if comp_pairs:
            pairs.extend(comp_pairs)
            return pairs

    # ── SINGLE WORD ENTRY ─────────────────────────────────────────────────────
    single = _extract_single_pair(heading, post_id, story, ling_link, full_text)
    if single:
        pairs.append(single)

    return pairs


def _extract_group_pairs(heading: str, post_id: str, full_text: str) -> list[dict]:
    """Extract word pairs from group entries."""
    pairs = []
    seen = set()

    # Pattern: كلمة X يقابلها "Y"
    for pat in [GROUP_PATTERN, GROUP_PATTERN2]:
        for m in pat.finditer(full_text):
            eng = m.group(1).strip().split('\n')[0].strip()
            ara = m.group(2).strip()
            # Clean up english word
            eng_clean = re.sub(r'\s*\([^)]*\)', '', eng).strip()
            eng_clean = re.sub(r'\s+\d+$', '', eng_clean).strip()
            if not eng_clean or len(eng_clean) > 40:
                continue
            if (eng_clean.lower(), ara) in seen:
                continue
            seen.add((eng_clean.lower(), ara))

            ara_words = ARABIC_WORD_RE.findall(ara)
            arabic_root = ara_words[0] if ara_words else ""
            arabic_meaning = extract_meaning_from_context(full_text, arabic_root)

            # Extract brief meaning hint from the rest of the match context
            # Try to find meaning in same line as the pair
            line_match = re.search(
                rf'(?:كلمة\s+)?{re.escape(eng_clean)}\s+(?:يقابلها|يقابله|تقابلها).*?(?:وتعني|أي|تعني|ومن معانيها|:)\s*"?([^"\n،]{2,80})"?',
                full_text
            )
            if line_match:
                arabic_meaning = line_match.group(1).strip()

            pairs.append({
                "english_word": eng_clean,
                "english_meaning": _guess_english_meaning(eng_clean, full_text),
                "arabic_root": arabic_root,
                "arabic_translit": transliterate_arabic(strip_arabic_diacritics(arabic_root)),
                "arabic_meaning": arabic_meaning,
                "etymology_explanation": f"{eng_clean} corresponds to Arabic '{ara}'. Sound/meaning match from group entry.",
                "phonetic_rules": _extract_phonetic_rules(full_text),
                "intermediate_langs": _extract_intermediate_langs(full_text),
                "confidence": 0.75,
                "source_post_id": post_id,
                "entry_type": "group",
            })
    return pairs


def _extract_compound_pairs(heading: str, post_id: str, full_text: str) -> list[dict]:
    """Extract morpheme pairs from compound word entries."""
    pairs = []
    seen = set()

    # Find compound sub-parts
    for pat in [COMPOUND_PATTERN, INLINE_PATTERN]:
        for m in pat.finditer(full_text):
            eng = m.group(1).strip()
            ara = m.group(2).strip()
            if not eng or not ara or len(eng) > 30:
                continue
            key = (eng.lower(), strip_arabic_diacritics(ara))
            if key in seen:
                continue
            seen.add(key)

            ara_words = ARABIC_WORD_RE.findall(ara)
            arabic_root = ara_words[0] if ara_words else ""
            arabic_meaning = extract_meaning_from_context(full_text, arabic_root)

            pairs.append({
                "english_word": eng,
                "english_meaning": _guess_english_meaning(eng, full_text),
                "arabic_root": arabic_root,
                "arabic_translit": transliterate_arabic(strip_arabic_diacritics(arabic_root)),
                "arabic_meaning": arabic_meaning,
                "etymology_explanation": f"Compound morpheme '{eng}' of '{heading}' corresponds to Arabic '{ara}'. Part of compound word analysis.",
                "phonetic_rules": _extract_phonetic_rules(full_text),
                "intermediate_langs": _extract_intermediate_langs(full_text),
                "confidence": 0.70,
                "source_post_id": post_id,
                "entry_type": "compound",
            })

    return pairs


def _extract_single_pair(heading: str, post_id: str, story: str, ling_link: str, full_text: str) -> dict | None:
    """Extract a single pair from a dedicated word entry."""
    # The heading IS the English word (mostly)
    eng_word_match = re.match(r'^([A-Za-z][A-Za-z0-9\-\s]*?)(?:\s*[\(\[].*)?$', heading)
    if not eng_word_match:
        return None

    eng_word = eng_word_match.group(1).strip()
    # Clean trailing parenthetical
    eng_word = re.sub(r'\s+\(.*', '', eng_word).strip()
    if not eng_word or len(eng_word) > 50:
        return None

    # Get English meaning from story (first sentence often says "هذه الكلمة تعني X")
    eng_meaning = ""
    meaning_match = re.search(r'هذه الكلمة تعني[ى]?\s+"?([^"\n،.]{2,60})"?', full_text)
    if not meaning_match:
        meaning_match = re.search(r'معناه[ا]?\s+(?:هو\s+)?"?([^"\n،.]{2,60})"?', full_text)
    if meaning_match:
        eng_meaning = meaning_match.group(1).strip()

    # Find primary Arabic root
    arabic_root = ""
    arabic_meaning = ""

    # Common stopwords we don't want as roots
    ARABIC_STOPWORDS = {'في', 'من', 'إلى', 'على', 'أن', 'هو', 'هي', 'لا', 'ما', 'كل', 'مع', 'عن',
                        'ليس', 'إن', 'أي', 'هذا', 'هذه', 'ذلك', 'التي', 'الذي', 'كما', 'حين',
                        'قد', 'لم', 'أو', 'و', 'عند', 'بعد', 'قبل', 'عن', 'ثم', 'لكن', 'لو'}

    def _is_valid_arabic_root(word: str) -> bool:
        if len(word) < 2:
            return False
        if not any('\u0600' <= c <= '\u06FF' for c in word):
            return False
        stripped = re.sub(r'[ًٌٍَُِّْال]', '', word)
        if stripped in ARABIC_STOPWORDS or word in ARABIC_STOPWORDS:
            return False
        return True

    # Common patterns for finding the primary Arabic correspondence
    explicit_patterns = [
        # Most reliable: يقابلها كلمة "X"
        r'(?:يقابلها|يقابله|تقابلها|فيقابلها)\s+(?:كلمة\s+)?"([^"]{1,40})"',
        # "نجد كلمة X" or "لوجدنا كلمة X"
        r'(?:نجد كلمة|لوجدنا كلمة)\s+"([^"]{1,30})"',
        # "وهي كلمة X والتي"
        r'وهي كلمة\s+"([^"]{1,30})"',
        # "كلمة X والتي"
        r'كلمة\s+"([^"]{1,30})"\s+(?:والتي|التي)',
        # "هي/هو كلمة X"
        r'(?:هي|هو)\s+كلمة\s+"([^"]{1,30})"',
        # "كلمة X" — Arabic quoted (last resort explicit)
        r'كلمة\s+"([\u0600-\u06FF][^"]{1,30})"',
    ]

    # Strategy 1: Run explicit patterns on STORY first (story has explicit "يقابلها" claims)
    for pat in explicit_patterns:
        m = re.search(pat, story, re.DOTALL)
        if m:
            candidate = m.group(1).strip()
            ara_words = ARABIC_WORD_RE.findall(candidate)
            if ara_words and _is_valid_arabic_root(ara_words[0]):
                arabic_root = ara_words[0]
                arabic_meaning = extract_meaning_from_context(full_text, arabic_root)
                break

    # Strategy 2: For ling_link (when it's not N/A), the FIRST quoted Arabic word is the primary root.
    # The post author typically introduces the correspondence in the ling_link's first sentence.
    if not arabic_root and ling_link and ling_link.strip() not in ('N/A', ''):
        # First try explicit patterns on ling_link
        for pat in explicit_patterns:
            m = re.search(pat, ling_link, re.DOTALL)
            if m:
                candidate = m.group(1).strip()
                ara_words = ARABIC_WORD_RE.findall(candidate)
                if ara_words and _is_valid_arabic_root(ara_words[0]):
                    arabic_root = ara_words[0]
                    arabic_meaning = extract_meaning_from_context(full_text, arabic_root)
                    break
        # Then first quoted word in ling_link
        if not arabic_root:
            quoted = re.findall(r'"([^"]{1,40})"', ling_link)
            for q in quoted:
                ara_words = ARABIC_WORD_RE.findall(q)
                if ara_words and _is_valid_arabic_root(ara_words[0]):
                    arabic_root = ara_words[0]
                    arabic_meaning = extract_meaning_from_context(full_text, arabic_root)
                    break

    # Strategy 3: Last resort — first quoted Arabic word in story
    if not arabic_root:
        quoted = re.findall(r'"([^"]{1,30})"', story)
        for q in quoted:
            ara_words = ARABIC_WORD_RE.findall(q)
            if ara_words and _is_valid_arabic_root(ara_words[0]):
                arabic_root = ara_words[0]
                arabic_meaning = extract_meaning_from_context(full_text, arabic_root)
                break

    if not arabic_root:
        return None

    # Build explanation
    explanation = _build_explanation(eng_word, arabic_root, full_text)
    phonetic_rules = _extract_phonetic_rules(full_text)
    intermediate = _extract_intermediate_langs(full_text)
    confidence = _score_confidence(eng_word, arabic_root, full_text, phonetic_rules, intermediate)

    return {
        "english_word": eng_word,
        "english_meaning": eng_meaning,
        "arabic_root": arabic_root,
        "arabic_translit": transliterate_arabic(strip_arabic_diacritics(arabic_root)),
        "arabic_meaning": arabic_meaning,
        "etymology_explanation": explanation,
        "phonetic_rules": phonetic_rules,
        "intermediate_langs": intermediate,
        "confidence": confidence,
        "source_post_id": post_id,
        "entry_type": "single",
    }


def _guess_english_meaning(word: str, context: str) -> str:
    """Try to guess the English meaning of a word from context."""
    # Look for explicit meaning statements
    patterns = [
        rf'(?:كلمة\s+)?"{re.escape(word)}"\s+(?:وتعني|تعني|يعني)\s+"?([^"\n،.{{}}]{2,50})"?',
        rf'{re.escape(word)}\s+(?:meaning|means|=)\s+"?([^"\n]{2,40})"?',
    ]
    for pat in patterns:
        m = re.search(pat, context, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def _build_explanation(eng: str, arabic: str, full_text: str) -> str:
    """Build a concise English explanation of the etymology."""
    # Look for phonetic correspondence mentions
    phonetic_hint = ""
    p = re.search(r'(?:حيث|إذ|مع)\s+(.{10,80}(?:إبدال|قلب|حذف|تحول)[^.،\n]{5,60})', full_text)
    if p:
        phonetic_hint = f" Phonetic note: {p.group(1).strip()}"

    # Look for semantic explanation
    sem = re.search(r'(?:كما نرى|كما نلاحظ|فكما ترون)\s+(.{10,150})', full_text)
    sem_text = sem.group(1).strip()[:150] if sem else ""

    base = f"English '{eng}' corresponds to Arabic '{arabic}'."
    if sem_text:
        base += f" The text notes: ...{sem_text[:100]}..."
    return base + phonetic_hint


def _extract_phonetic_rules(text: str) -> str:
    """Extract phonetic transformation rules mentioned in the text."""
    rules = []
    patterns = [
        r'حيث\s+([A-Za-zء-ي]+\s*=\s*[A-Za-zء-ي]+)',
        r'(?:إبدال|تبديل)\s+(?:حرف\s+)?"?([^"،\n]{3,40})"?\s+(?:بحرف|ب)"?([^"،\n]{1,20})"?',
        r'([ء-ي])\s*↔\s*([A-Za-z]+)',
        r'([A-Za-z]+)\s*↔\s*([ء-ي])',
    ]
    for pat in patterns:
        for m in re.finditer(pat, text):
            rules.append(m.group(0).strip()[:50])
    return "; ".join(rules[:3]) if rules else ""


def _extract_intermediate_langs(text: str) -> str:
    """Extract intermediate languages mentioned in the etymology chain."""
    langs = []
    lang_patterns = [
        (r'الفرنسية', 'French'), (r'اللاتينية', 'Latin'), (r'اليونانية', 'Greek'),
        (r'الإسبانية', 'Spanish'), (r'الألمانية', 'German'), (r'الإيطالية', 'Italian'),
        (r'الفارسية', 'Persian'), (r'الأرامية', 'Aramaic'), (r'الهندو-أوروبية', 'PIE'),
        (r'النوردية القديمة', 'Old Norse'), (r'الإنجليزية القديمة', 'Old English'),
        (r'السريانية', 'Syriac'), (r'الآكدية', 'Akkadian'),
    ]
    for pattern, lang in lang_patterns:
        if re.search(pattern, text):
            langs.append(lang)
    return ", ".join(langs[:4]) if langs else ""


def _score_confidence(eng: str, arabic: str, full_text: str, phonetic_rules: str, intermediate: str) -> float:
    """Score confidence of the etymology pair."""
    score = 0.7  # base

    # Direct phonetic match mentioned
    if re.search(r'(?:مماثل|متطابق|نفس اللفظ|مشابه)\s+(?:في اللفظ|في النطق)', full_text):
        score = min(score + 0.1, 0.9)

    # Both phonetic AND semantic match
    if re.search(r'(?:اللفظ والمعنى|النطق والمعنى)', full_text):
        score = min(score + 0.1, 0.9)

    # "Unknown origin" in foreign sources = our root is speculative
    if re.search(r'أصل.*?غير مع?روف|مجهول.*?لديهم', full_text):
        # Slight bump — we're filling a gap
        score = min(score + 0.05, 0.85)

    # Long intermediate chain = lower confidence
    if len(intermediate.split(',')) >= 3:
        score = max(score - 0.1, 0.5)

    # Speculative / research paper references = lower
    if re.search(r'يُحتمل|من المحتمل|يبدو أن|ربما', full_text):
        score = max(score - 0.05, 0.55)

    # If phonetic rules are explicit = higher
    if phonetic_rules:
        score = min(score + 0.05, 0.9)

    return round(score, 2)


# ─── JSONL record builder ─────────────────────────────────────────────────────
def pair_to_jsonl(pair: dict) -> dict | None:
    """Convert a pair dict to a JSONL cognate record."""
    eng = pair["english_word"].lower().strip()
    ara = strip_arabic_diacritics(pair["arabic_root"])
    if not eng or not ara:
        return None

    # Skip if already in gold
    if (ara, eng) in existing_pairs or (eng, ara) in existing_pairs:
        return None
    if (ara.lower(), eng.lower()) in existing_pairs:
        return None

    notes = pair["etymology_explanation"]
    if pair["phonetic_rules"]:
        notes += f" Rules: {pair['phonetic_rules']}"
    if pair["intermediate_langs"]:
        notes += f" Via: {pair['intermediate_langs']}"

    return {
        "source": {
            "lang": "ara",
            "lemma": ara,
            "gloss": pair["arabic_meaning"] or ""
        },
        "target": {
            "lang": "eng",
            "lemma": eng,
            "gloss": pair["english_meaning"] or pair["english_word"]
        },
        "relation": "cognate",
        "confidence": pair["confidence"],
        "notes": notes[:500]
    }


# ─── Main pipeline ────────────────────────────────────────────────────────────
def main():
    print(f"Reading {INPUT_MD} ...")
    text = INPUT_MD.read_text(encoding="utf-8")
    print(f"  File size: {len(text):,} chars")

    entries = parse_entries(text)
    print(f"  Parsed {len(entries)} entries")

    all_pairs = []
    skipped = 0
    for entry in entries:
        if should_skip(entry):
            skipped += 1
            continue
        pairs = extract_pairs_from_entry(entry)
        all_pairs.extend(pairs)

    print(f"  Skipped {skipped} non-etymological entries")
    print(f"  Extracted {len(all_pairs)} raw pairs")

    # Deduplicate pairs by (english_word, arabic_root)
    seen_pairs: set[tuple[str, str]] = set()
    deduped = []
    for p in all_pairs:
        key = (p["english_word"].lower(), strip_arabic_diacritics(p["arabic_root"]))
        if key not in seen_pairs and p["arabic_root"]:
            seen_pairs.add(key)
            deduped.append(p)

    print(f"  After dedup: {len(deduped)} pairs")

    # Write CSV
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "english_word", "english_meaning", "arabic_root", "arabic_translit",
        "arabic_meaning", "etymology_explanation", "phonetic_rules",
        "intermediate_langs", "confidence", "source_post_id", "entry_type"
    ]
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in deduped:
            writer.writerow({k: p.get(k, "") for k in fieldnames})
    print(f"\nWrote CSV: {OUT_CSV} ({len(deduped)} rows)")

    # Write JSONL
    jsonl_records = []
    for p in deduped:
        rec = pair_to_jsonl(p)
        if rec:
            jsonl_records.append(rec)

    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for rec in jsonl_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Wrote JSONL: {OUT_JSONL} ({len(jsonl_records)} records)")

    # ── Verification ─────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)

    import csv as csv_module
    with open(OUT_CSV, encoding="utf-8") as f:
        reader = list(csv_module.DictReader(f))
    print(f"\nCSV total rows: {len(reader)}")
    print("\nFirst 3 CSV rows:")
    for row in reader[:3]:
        print(f"  [{row['english_word']}] -> [{row['arabic_root']}] | {row['arabic_translit']} | conf={row['confidence']}")

    jsonl_rows = []
    with open(OUT_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                jsonl_rows.append(json.loads(line))
    print(f"\nJSONL total entries: {len(jsonl_rows)}")
    print("\nFirst 3 JSONL entries:")
    for r in jsonl_rows[:3]:
        print(f"  {r['source']['lemma']} -> {r['target']['lemma']} (conf={r['confidence']})")

    # Spot-check
    print("\nSpot-check targets: Ruthless→رثى, Fog→فيج, Left→لفت, Dam→دأم, Surgery→سرّاج")
    targets = {
        "ruthless": "رثى",
        "fog": "فيج",
        "left": "لفت",
        "dam": "دأم",
        "surgery": "سرّاج",
    }
    for eng, ara in targets.items():
        found = any(
            r["english_word"].lower() == eng and strip_arabic_diacritics(r["arabic_root"]) == strip_arabic_diacritics(ara)
            for r in reader
        )
        status = "FOUND" if found else "MISSING"
        # Also check partial (root without hamza etc)
        if not found:
            found_partial = any(
                r["english_word"].lower() == eng
                for r in reader
            )
            if found_partial:
                match = next(r for r in reader if r["english_word"].lower() == eng)
                status = f"FOUND (root={match['arabic_root']})"
        print(f"  {eng} → {ara}: {status}")


if __name__ == "__main__":
    main()
