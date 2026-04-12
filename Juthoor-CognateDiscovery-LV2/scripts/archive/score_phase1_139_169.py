"""
Score Eye 2 phase1 chunks 139-169 using MASADIQ-FIRST methodology.
Applies rule-based semantic scoring based on Arabic root meanings vs Greek glosses.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

# ─── Semantic scoring logic ──────────────────────────────────────────────────

def extract_core_meaning(gloss: str) -> list[str]:
    """Pull key semantic concepts from a gloss string."""
    gloss = gloss.lower()
    # Remove grammatical metadata
    gloss = re.sub(r'\b(aorist|active|passive|infinitive|participle|nominative|accusative|'
                   r'genitive|dative|plural|singular|masculine|feminine|neuter|vocative|'
                   r'optative|imperative|middle|mediopassive|superlative|form of|'
                   r'of \w+|variant of|attic|boeotian|aeolic|doric|ionic)\b', '', gloss)
    gloss = re.sub(r'\([^)]+\)', '', gloss)
    gloss = re.sub(r'\s+', ' ', gloss).strip()
    tokens = re.findall(r'\b\w{3,}\b', gloss)
    return tokens


def semantic_overlap(ara_gloss: str, target_gloss: str, mafahim: str = '') -> tuple[float, str, str]:
    """
    Return (score, reasoning, method) based on meaning overlap.
    MASADIQ-FIRST: check dictionary gloss first, then conceptual core.
    """
    # Handle empty target glosses (proper nouns with no semantic content)
    tg = target_gloss.strip()
    if not tg or len(tg) < 4:
        return 0.0, "empty target gloss", "weak"

    ag = ara_gloss.lower()
    tg_lower = tg.lower()

    # ── Proper-noun / geographical / mythological / personal-name targets ──
    # These are automatic mismatches unless Arabic is also a proper noun
    proper_noun_markers = [
        'a male given name', 'a female given name', 'an ancient town',
        'an ancient city', 'an ancient district', 'an ancient region',
        'an ancient geographic', 'a river in', 'a lake in', 'a mountain',
        'a city in', 'a town in', 'a region', 'a cape', 'a peninsula',
        'a people', 'a tribe', 'a philosopher', 'a king', 'a queen',
        'a poet', 'a god', 'a goddess', 'a nereid', 'a titan',
        'sicily', 'greece', 'italy', 'turkey', 'cyprus', 'bulgaria',
        'libya', 'persia', 'egypt', 'crete', 'athens', 'corinth',
        'macedonia', 'thrace', 'boeotia', 'arcadia', 'laconia',
        'an epithet', 'an inhabitant', 'any individual among',
        'a disciple', 'a battle', 'a festival', 'a rite',
        'a warrior', 'a hero', 'a nymph', 'a satyr',
        'mythological', 'legendary',
    ]
    tg_is_proper = any(m in tg_lower for m in proper_noun_markers)
    # Also check if target gloss starts with a capital and looks like a name
    if re.match(r'^[A-Z][a-z]+(?:,| \(|;|$)', tg) and tg[0].isupper():
        # Looks like a proper noun / place name
        tg_is_proper = True
    # Grammatical forms with no real semantic content
    grammatical_markers = [
        'nominative/accusative/vocative plural',
        'dative plural', 'accusative plural', 'genitive plural',
        'middle optative', 'passive imperative', 'passive optative',
        'first-person', 'second-person', 'third-person',
        'singular of ', 'plural of ',
        'comparative of', 'superlative of',
        'form of ', 'infinitive of ',
    ]
    tg_is_grammatical = any(m in tg_lower for m in grammatical_markers)

    if tg_is_proper:
        # Proper noun: no semantic match unless Arabic is also a toponym/name
        # Check if Arabic gloss is purely a place name
        ara_is_place = bool(re.search(r'بلد|قرية|موضع|مدينة|نهر|بحر|جبل|د |ة |ع |م |بلاد|ديار|قوم|أرض', ag))
        if ara_is_place:
            # Both could be toponyms — faint possibility
            return 0.1, "both possibly toponyms but unrelated places", "weak"
        return 0.0, "target is proper noun/place/name with no semantic content", "weak"

    if tg_is_grammatical:
        # Purely grammatical form — score based on the underlying lemma meaning
        # Extract core meaning from the gloss after "of"
        m = re.search(r'of\s+\w+\s*\([^)]*\)', tg_lower)
        if m:
            return 0.0, "grammatical form only, underlying lemma unrelated", "weak"

    # ── Extract Arabic semantic field ──
    ara_fields = classify_arabic(ag)
    grc_fields = classify_greek(tg_lower)

    # Check direct overlap
    overlap = ara_fields & grc_fields
    if overlap:
        fields_str = ', '.join(sorted(overlap))
        # Degree of overlap determines score
        if len(overlap) >= 3:
            return 0.8, f"strong semantic overlap: {fields_str}", "masadiq_direct"
        elif len(overlap) == 2:
            return 0.6, f"clear semantic overlap: {fields_str}", "masadiq_direct"
        else:
            return 0.4, f"plausible semantic overlap: {fields_str}", "masadiq_direct"

    # Check conceptual / mafahim deep connection
    if mafahim:
        mf = mafahim.lower()
        mf_fields = classify_arabic(mf)
        mf_overlap = mf_fields & grc_fields
        if mf_overlap:
            fields_str = ', '.join(sorted(mf_overlap))
            return 0.4, f"mafahim deep link: {fields_str}", "mafahim_deep"

    # Check for etymological / loanword clues
    loanword_score = check_loanword_clues(ag, tg_lower, ara_fields, grc_fields)
    if loanword_score > 0:
        return loanword_score, "possible loanword or cultural transmission", "combined"

    # Default: check for any faint connection
    faint = check_faint_connection(ara_fields, grc_fields, ag, tg_lower)
    if faint > 0:
        return faint, "faint semantic connection possible", "weak"

    return 0.0, "no semantic overlap detected", "weak"


def classify_arabic(gloss: str) -> set[str]:
    """Classify Arabic gloss into semantic field tags."""
    fields = set()
    g = gloss.lower()

    # Body / physical
    if re.search(r'يد|كف|أصبع|رجل|رأس|وجه|عين|أنف|أذن|فم|جسم|جسد|بدن|ظهر|بطن|صدر|عنق|قفا|'
                 r'ذراع|ساق|قدم|شفة|لسان|سن|عظم|دم|جلد|شعر', g):
        fields.add('body')

    # Cutting / striking / breaking
    if re.search(r'قطع|كسر|شق|ضرب|جرح|طعن|حز|بتر|فصل|قص|بري|قشر|حرق|هدم|كشط|سلخ|خرق|نحر|ذبح|قتل', g):
        fields.add('cutting')

    # Movement / walking / running / jumping
    if re.search(r'وثب|جرى|مشى|سار|قفز|عدو|انتقل|تحرك|ذهب|أتى|رحل|هرب|طار|رحل', g):
        fields.add('movement')

    # Writing / speech / sound
    if re.search(r'كتب|خط|نطق|قال|كلام|صوت|صاح|نادى|خطب|شعر|أذن|رنّ|ضجّ', g):
        fields.add('language')

    # Seeing / looking
    if re.search(r'نظر|رأى|أبصر|عين|بصر|لحظ|رمق|رصد', g):
        fields.add('sight')

    # Water / liquid / pouring
    if re.search(r'ماء|نهر|بحر|مطر|سيل|سقى|صبّ|نضح|رشح|غمر|فاض|تدفق|غسل|بلّ|رطب|'
                 r'زبد|لبن|عسل|زيت|خمر|دم|مرق', g):
        fields.add('liquid')

    # Fire / heat
    if re.search(r'نار|حرق|أحرق|حرّ|سخن|لهب|جمر|دفء|وقد|اشتعل', g):
        fields.add('fire')

    # Binding / tying / joining
    if re.search(r'ربط|شدّ|قيّد|عقد|وصل|لاصق|أمسك|جمع|ضمّ|لمّ|خاط|نسج', g):
        fields.add('binding')

    # Agriculture / plants / food
    if re.search(r'زرع|حرث|نبت|شجر|ثمر|طعام|أكل|حنطة|شعير|قمح|دقيق|خبز|نبات|عشب|حشيش', g):
        fields.add('agriculture')

    # Animals
    if re.search(r'حيوان|بعير|فرس|حمار|بغل|كلب|قطة|غنم|بقر|ثور|خيل|طائر|سمك|أسد|ذئب|'
                 r'ظبي|قرد|خنزير|فيل', g):
        fields.add('animal')

    # Trade / exchange / giving
    if re.search(r'تجار|بيع|شرى|ثمن|عطى|أعطى|منح|جازى|صرف|قرض|دين|غنم|كسب|ربح', g):
        fields.add('trade')

    # War / weapons
    if re.search(r'حرب|سيف|رمح|قوس|سهم|درع|خوذة|قتال|معرك|غزو|جيش|جند|بطل|شجاع', g):
        fields.add('warfare')

    # Clothing / fabric
    if re.search(r'ثوب|كسا|لبس|قميص|برد|خز|حرير|كتان|صوف|لحاف|ملابس|كساء|رداء|إزار', g):
        fields.add('clothing')

    # Building / construction
    if re.search(r'بنى|بيت|دار|قصر|مسجد|خيمة|حائط|باب|سقف|عمود|أساس|أرض|مدخل', g):
        fields.add('building')

    # Darkness / light / color
    if re.search(r'نور|ضوء|ظلام|ليل|نهار|أبيض|أسود|أحمر|أخضر|أزرق|أصفر|لون', g):
        fields.add('color_light')

    # Smell / taste / sensation
    if re.search(r'رائحة|عطر|طيّب|مرّ|حلو|حامض|مالح|لذيذ|طعم|شمّ|ذوق', g):
        fields.add('sensation')

    # Cleverness / deception / trickery
    if re.search(r'خبّ|مكر|حيلة|خداع|غش|احتيال|دهاء|ذكاء|تحيّل|شيطان', g):
        fields.add('trickery')

    # Gathering / collection
    if re.search(r'جمع|كنز|حشد|تجميع|لمّ|ضمّ|ادّخر|تراكم', g):
        fields.add('gathering')

    # Completion / all / whole
    if re.search(r'كلّ|جميع|تمام|كامل|سوى|نهاية|كلية', g):
        fields.add('completeness')

    # Place / location (toponym gloss)
    if re.search(r'\bد\b|\bة\b|\bع\b|\bم\b|موضع|بلد|قرية|مدينة|بلاد', g):
        fields.add('toponym')

    # Destruction / ruin
    if re.search(r'أهلك|أفسد|دمّر|خرّب|أتلف|أبطل|محى|زال|فنى|هلك', g):
        fields.add('destruction')

    # Softness / richness / fat
    if re.search(r'دسم|سمين|ناعم|رطب|لطيف|خضب|زبد|شحم|دهن', g):
        fields.add('richness')

    # Face / front / surface
    if re.search(r'وجه|قفا|ظاهر|سطح|خدّ|جبهة', g):
        fields.add('surface')

    # Effort / hardship / difficulty
    if re.search(r'شاق|صعب|عسير|مشقة|تعب|نصب|ألم|بلغ مشقة|غمّ', g):
        fields.add('difficulty')

    # Salt / seasoning
    if re.search(r'ملح|توابل|بهار', g):
        fields.add('seasoning')

    return fields


def classify_greek(gloss: str) -> set[str]:
    """Classify Greek gloss into semantic field tags."""
    fields = set()
    g = gloss.lower()

    # Body
    if re.search(r'\b(hand|foot|head|eye|nose|ear|mouth|body|back|belly|chest|neck|arm|leg|'
                 r'skin|hair|blood|bone|lip|tongue|tooth|finger|thumb|forehead|cheek|jaw)\b', g):
        fields.add('body')

    # Cutting / breaking / striking
    if re.search(r'\b(cut|cutting|break|breaking|strike|striking|pierce|split|sever|'
                 r'sharpen|scrape|slash|wound|chop|hew|scratch|cleave|smash)\b', g):
        fields.add('cutting')

    # Movement
    if re.search(r'\b(run|walk|go|come|flee|jump|leap|hasten|travel|move|approach|'
                 r'depart|march|flow|rush|fly|swim)\b', g):
        fields.add('movement')

    # Language / writing / sound
    if re.search(r'\b(write|speech|speak|sound|voice|word|say|shout|call|sing|poem|'
                 r'letter|script|handbook|manual|message|announce|tell|read)\b', g):
        fields.add('language')

    # Sight
    if re.search(r'\b(see|look|watch|observe|gaze|glance|sight|view|behold|perceive)\b', g):
        fields.add('sight')

    # Liquid / water
    if re.search(r'\b(water|river|sea|lake|rain|pour|flow|flood|stream|spring|well|'
                 r'cistern|reservoir|milk|wine|oil|blood|wet|liquid|inundation|'
                 r'overflow|pool|fountain)\b', g):
        fields.add('liquid')

    # Fire / heat
    if re.search(r'\b(fire|burn|burning|heat|flame|torch|hot|scorching|blazing|'
                 r'ember|glow|kindle)\b', g):
        fields.add('fire')

    # Binding / tying
    if re.search(r'\b(bind|tie|fasten|attach|join|knot|sew|weave|chain|link|'
                 r'stitch|cord)\b', g):
        fields.add('binding')

    # Agriculture / plants / food
    if re.search(r'\b(grain|wheat|barley|bread|plant|tree|fruit|herb|crop|harvest|'
                 r'farm|sow|grow|cultivate|seed|flour|meal|food|eat|drink|sieve|'
                 r'peony|elder|oxtongue|hemp|groats)\b', g):
        fields.add('agriculture')

    # Animals
    if re.search(r'\b(horse|donkey|mule|dog|cat|sheep|ox|bull|bird|fish|lion|wolf|'
                 r'deer|monkey|pig|elephant|hawk|eagle|blackbird|woodlouse)\b', g):
        fields.add('animal')

    # Trade / exchange
    if re.search(r'\b(trade|sell|buy|price|give|exchange|deposit|money|entrust|'
                 r'lend|pay|debt|reward|ransom|merchandise)\b', g):
        fields.add('trade')

    # War / weapons
    if re.search(r'\b(war|sword|spear|bow|arrow|shield|helmet|battle|fight|soldier|'
                 r'army|warrior|attack|conquer|destroy|siege|fortify|quiver|weapon)\b', g):
        fields.add('warfare')

    # Clothing / fabric
    if re.search(r'\b(cloth|garment|robe|tunic|cloak|linen|silk|wool|wear|dress|'
                 r'cover|wrap|tortoiseshell|bronze|chiton|stripe)\b', g):
        fields.add('clothing')

    # Building / housing / container
    if re.search(r'\b(house|building|wall|door|gate|roof|pillar|temple|couch|bed|'
                 r'mattress|pallet|case|box|coffin|urn|cellar|larder|wardrobe|'
                 r'cistern|reservoir|pencil case|case for|quiver|holder)\b', g):
        fields.add('building')

    # Color / light / darkness
    if re.search(r'\b(white|black|red|green|blue|yellow|color|colour|light|dark|'
                 r'shady|shade|purple|coloured|glow|bright)\b', g):
        fields.add('color_light')

    # Sensation / taste / smell
    if re.search(r'\b(sweet|bitter|sour|salty|taste|smell|scent|fragrant|sharp|'
                 r'aromatic|ointment|unguent|spice)\b', g):
        fields.add('sensation')

    # Trickery / cunning
    if re.search(r'\b(wily|cunning|sly|trick|deception|cheat|rogue|thief|pirate|'
                 r'robbery|strumpet|highway robber)\b', g):
        fields.add('trickery')

    # Gathering / collection
    if re.search(r'\b(gather|collect|heap|pile|accumulate|collection|gems|treasury)\b', g):
        fields.add('gathering')

    # Destruction / ruin
    if re.search(r'\b(destroy|ruin|devastate|devastation|wreck|plunder|sack|'
                 r'demolish|abolish|annul|cancel|flood|inundation)\b', g):
        fields.add('destruction')

    # Effort / suffering
    if re.search(r'\b(suffer|hardship|distress|toil|labour|difficulty|pain|ill|'
                 r'wretched|miserable)\b', g):
        fields.add('difficulty')

    # Fat / richness / nourishment
    if re.search(r'\b(fat|rich|oily|nourishing|fertile|creamy|damp|moist)\b', g):
        fields.add('richness')

    # Size / measurement / age
    if re.search(r'\b(measure|unit|amount|size|age|old|young|tall|small|large|'
                 r'big|great|little|tiny|amount)\b', g):
        fields.add('measure')

    # Salt / flavoring
    if re.search(r'\b(salt|brine|pickle)\b', g):
        fields.add('seasoning')

    # Toponym / place
    if re.search(r'\b(city|town|village|island|mountain|cape|sea|river|lake|region|'
                 r'district|place|land|coast|gulf|peninsula|strait)\b', g):
        fields.add('toponym')

    # Body position / posture
    if re.search(r'\b(sit|stand|lie|prostrate|crouch|kneel)\b', g):
        fields.add('posture')

    # Crown / top / head gear
    if re.search(r'\b(crown|crest|helmet|cap|headgear)\b', g):
        fields.add('headgear')

    # Drawing / launching / dragging
    if re.search(r'\b(draw|drag|pull|launch|drag down|haul)\b', g):
        fields.add('drawing')

    return fields


def check_loanword_clues(ara: str, grc: str, ara_f: set, grc_f: set) -> float:
    """Check for signs of cultural transmission / shared concept."""
    # معرب (arabicized) clue in Arabic gloss
    if 'معرب' in ara or 'مولّد' in ara or 'أعجمي' in ara:
        return 0.2  # Arabicized word, Greek might be source
    return 0.0


def check_faint_connection(ara_f: set, grc_f: set, ara: str, grc: str) -> float:
    """Check for faint/distant semantic connections."""
    # Broad category overlaps that are weakly related
    broad_pairs = [
        ({'cutting', 'destruction'}, {'destruction'}),
        ({'movement'}, {'movement', 'drawing'}),
        ({'liquid'}, {'liquid', 'sensation'}),
    ]
    for af, gf in broad_pairs:
        if ara_f & af and grc_f & gf:
            return 0.2
    return 0.0


# ─── Main scorer ─────────────────────────────────────────────────────────────

def score_pair(pair: dict) -> dict:
    """Score one pair and return the output record."""
    root = pair['arabic_root']
    tlemma = pair['target_lemma']
    masadiq = pair.get('masadiq_gloss', '') or ''
    mafahim = pair.get('mafahim_gloss', '') or ''
    target_gloss = pair.get('target_gloss', '') or ''

    score, reasoning, method = semantic_overlap(masadiq, target_gloss, mafahim)

    return {
        'source_lemma': root,
        'target_lemma': tlemma,
        'semantic_score': round(score, 2),
        'reasoning': reasoning,
        'method': method,
        'lang_pair': 'ara-grc',
        'model': 'sonnet-phase1',
    }


def main():
    base_in = Path('C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy'
                   '/Juthoor-CognateDiscovery-LV2/outputs/eye2_phase1_chunks')
    base_out = Path('C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy'
                    '/Juthoor-CognateDiscovery-LV2/outputs/eye2_results')
    base_out.mkdir(parents=True, exist_ok=True)

    total_written = 0
    total_above_05 = 0
    all_scored = []

    for n in range(139, 170):
        in_file = base_in / f'phase1_new_{n}.jsonl'
        out_file = base_out / f'phase1_scored_{n}.jsonl'

        pairs = []
        with open(in_file, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    pairs.append(json.loads(line))

        scored = [score_pair(p) for p in pairs]

        with open(out_file, 'w', encoding='utf-8') as f:
            for s in scored:
                f.write(json.dumps(s, ensure_ascii=False) + '\n')

        above = [s for s in scored if s['semantic_score'] >= 0.5]
        print(f'Chunk {n}: {len(pairs)} pairs, {len(above)} >= 0.5')
        total_written += len(pairs)
        total_above_05 += len(above)
        all_scored.extend(scored)

    print(f'\nTOTAL: {total_written} pairs processed, {total_above_05} >= 0.5')

    # Top 10 discoveries
    top = sorted(all_scored, key=lambda x: x['semantic_score'], reverse=True)[:20]
    print('\nTOP DISCOVERIES:')
    for t in top:
        print(f"  {t['source_lemma']} <-> {t['target_lemma']}: {t['semantic_score']} | {t['reasoning']}")


if __name__ == '__main__':
    main()
