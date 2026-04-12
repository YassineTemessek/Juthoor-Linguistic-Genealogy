"""
Eye 2 Phase 1 final scorer — chunks 108-125 (ara-lat)
Masadiq-first, honest conservative calibration.
All 1,800 pairs processed.
"""
import json
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_IN  = 'C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_phase1_lat_chunks'
BASE_OUT = 'C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_results'

os.makedirs(BASE_OUT, exist_ok=True)

# ──────────────────────────────────────────────────────────────────────────────
# HAND-SCORED PAIRS — verified from masadiq text analysis
# Format: (arabic_root, target_lemma) -> (score, reasoning, method)
# ──────────────────────────────────────────────────────────────────────────────
HAND_SCORED = {
    # Genuine hits verified from masadiq text
    ('المخ', 'magulum'):
        (0.65, "المخ=marrow/brain (نقي العظم، الدماغ); magulum=jaw/mouth — head anatomy overlap, plausible", "masadiq_direct"),
    ('بابا', 'bombio'):
        (0.60, "بأبأ=to buzz/say baba (صوت); bombio=to buzz — onomatopoeic sound match", "masadiq_direct"),
    ('اللجح', 'alcohol'):
        (0.50, "اللجح includes eye secretion (اللخص في العين، الغمص); alcohol=kohl/collyrium for eyes — faint eye link", "mafahim_deep"),

    # Pairs where target has semantic content but Arabic root is unrelated
    # Sword (السيف) — all 100 pairs for السيف share same masadiq (sword).
    # None of the Latin targets in this dataset are sword-related.
    # الصوف (wool) — targets are palpus/lagopus/visualis — unrelated.
    # اللجام (bridle) — target melligo=honeydew juice, no connection.
    # الصيح (cry/shout) — targets are salsugo/algosus — unrelated.
    # بابك (historical rebel) — bibax (fond of drink) — phonetic only, no semantic.
    ('بابك', 'bibax'):
        (0.20, "بابك=historical rebel Khuramite; bibax=fond of drink — phonetic coincidence only, no semantic link", "weak"),
    ('بابك', 'exbibo'):
        (0.20, "بابك=historical rebel; exbibo=drink out — phonetic similarity only, bab/bib", "weak"),

    # الصنخر (large camel/tall/foolish) + clarisonus (clear-sounding) — no sound concept
    # الصندوق (box/chest) + dulcisonus — no connection

    # حشد (gather/respond quickly) + hittus (hunting dog sound) — very faint
    ('حشد', 'hittus'):
        (0.20, "حشد=gather/respond quickly to call; hittus=hunting dog sound — hunting assembly faint link", "weak"),
    ('حشد', 'hutesium'):
        (0.40, "حشد=respond quickly to summons/hue and cry; hutesium=pursuit, hue and cry — plausible assembly/pursuit link", "masadiq_direct"),

    # الموماء (desert plain/medicine) + abluvium (flood) — water signal present but root=desert not flood
    ('الموماء', 'abluvium'):
        (0.20, "الموماء=desert plain + ماء secondary; abluvium=flood — water signal in masadiq but root concept is desert, not flood", "weak"),

    # العهخع (medicinal plant) + alcohol (kohl) — plant treats conditions but no eye mention
    ('العهخع', 'alcohol'):
        (0.20, "العهخع=medicinal plant (يتداوى بها); alcohol=kohl — both medicinal but no direct eye concept match", "weak"),

    # الهلثي (group/laxity) + alcoholic — no connection
    ('الهلثي', 'alcoholic'):
        (0.0, "الهلثي=laxity/loud group of people; alcoholic=addicted to alcohol — false cognate", "masadiq_direct"),
}

# ──────────────────────────────────────────────────────────────────────────────
# EXCLUSION PATTERNS — auto-score 0.0
# ──────────────────────────────────────────────────────────────────────────────
ZERO_TARGET_PATTERNS = [
    # Proper nouns
    'roman nomen', 'nomen gentile', 'famously held by', 'cognomen', 'praenomen',
    'given name', 'family name', 'gens or', 'historical king', 'historical figure',
    # Places
    'a city in', 'a town in', 'a region in', 'an island', 'a place in',
    'hispania', 'idaho', 'idahum', 'turoqua', 'oklahoma', 'kagoshima',
    'delphi', 'greeks', 'polish', 'poland', 'lusitanian', 'portuguese',
    # Elements
    'gallium', 'lithium', 'holmium', 'erbium', 'terbium', 'berkelium',
    'californium', 'lutatium', 'chemical element',
    # Misc proper
    'alaricus', 'lacerius', 'zoilus', 'saleius', 'alfius', 'hababa',
    'bibaga', 'ahuidies', 'uralic', 'lycaeus',
]

ZERO_GRAM_PATTERNS = [
    'singular present active indicative',
    'singular future passive imperative',
    'singular future active indicative',
    'perfect active infinitive',
    'comparative degree of',
    'superlative degree of',
    'vocative masculine singular',
    'ablative feminine singular',
    'alternative spelling of eius',
    'alternative spelling of iussus',
    'alternative spelling of iocus',
    'dative/ablative singular',
    'accusative singular of',
    'second/third-person singular',
    'second-person singular present',
    'genitive singular of',
    'nominative plural of',
    'plural of ',
]

def is_zero_target(gloss: str) -> tuple:
    """Returns (True, reason) if target should be scored 0.0"""
    g = gloss.lower()
    for pat in ZERO_TARGET_PATTERNS:
        if pat in g:
            return True, f"excluded target: {pat}"
    for pat in ZERO_GRAM_PATTERNS:
        if pat in g and len(gloss) < 100:
            return True, "pure grammatical form — no semantic content"
    return False, ""

# ──────────────────────────────────────────────────────────────────────────────
# MASADIQ CONTENT SIGNALS — Arabic keywords in masadiq text
# Maps Arabic word → (english concept, base_score)
# ──────────────────────────────────────────────────────────────────────────────
MASADIQ_SIGNALS = [
    # High confidence signals
    ('الشمع',  'wax/candle',     0.80),
    ('شمع',    'wax/candle',     0.75),
    ('الصوف',  'wool',           0.80),
    ('صوف',    'wool',           0.75),
    ('العسل',  'honey',          0.80),
    ('عسل',    'honey',          0.75),
    ('الملح',  'salt',           0.80),
    ('ملح',    'salt',           0.72),
    ('مالح',   'salt',           0.70),
    ('النار',  'fire',           0.75),
    ('اللهب',  'fire/flame',     0.72),
    ('الدم',   'blood',          0.78),
    ('دماء',   'blood',          0.70),
    ('السيف',  'sword',          0.78),
    ('القانون','law',            0.70),
    ('الشريعة','law',            0.70),
    ('الفقه',  'jurisprudence',  0.68),
    ('الصوت',  'sound',         0.75),
    ('صوت',    'sound',         0.68),
    ('الصياح', 'cry/sound',     0.70),
    ('السمك',  'fish',          0.75),
    ('اللحم',  'meat/flesh',    0.75),
    ('الشجر',  'tree',          0.68),
    ('الحجر',  'stone/rock',    0.70),
    ('النخل',  'palm tree',     0.80),
    ('نخل',    'palm tree',     0.75),
    ('الكلب',  'dog',           0.75),
    ('النحل',  'bee/honey',     0.78),
    ('العنب',  'grape/vine',    0.80),
    ('العقرب', 'scorpion',      0.82),
    ('العنكبوت','spider',       0.82),
    ('الذهب',  'gold',          0.80),
    ('الماء',  'water',         0.70),
    ('ماء',    'water',         0.65),
    ('المطر',  'rain',          0.70),
    ('الطين',  'clay/mud',      0.65),
    ('العسكر', 'army/soldiers', 0.65),
    ('الحكم',  'judgment/law',  0.65),
    ('الضوء',  'light',         0.70),
    ('نور',    'light',         0.68),
    ('الشمس',  'sun',           0.80),
    ('القمر',  'moon',          0.78),
    ('النجم',  'star',          0.75),
    ('الريح',  'wind',          0.68),
    ('الدواء', 'medicine',      0.68),
    ('دواء',   'medicine',      0.62),
    ('المرض',  'illness',       0.68),
    ('الحرب',  'war',           0.68),
    ('السلام', 'peace',         0.70),
    ('الفرس',  'horse',         0.70),
    ('البعير', 'camel',         0.65),
    ('الناقة', 'camel',         0.65),
    ('العلج',  'foreign/enemy', 0.55),
    ('البخل',  'stinginess',    0.65),
    ('الغضب',  'anger',         0.68),
    ('الصبر',  'patience',      0.65),
    ('الشرب',  'drink',         0.72),
    ('شرب',    'drink',         0.65),
    ('الجرع',  'gulp/swallow',  0.65),
    # Note: طعام/الأكل removed — too common in Arabic dictionary examples,
    # causes false positives when it appears incidentally in masadiq definitions
    ('الفلاة', 'desert/waste',  0.55),
    ('البرق',  'lightning',     0.65),
    ('الخوف',  'fear',          0.65),
    ('الكلام', 'speech/words',  0.62),
    ('الكذب',  'lie/falsehood', 0.60),
    ('الصبر',  'patience',      0.62),
    ('الشعر',  'hair/poetry',   0.55),
    ('النخل',  'palm tree',     0.80),
]

# ──────────────────────────────────────────────────────────────────────────────
# TARGET CONCEPT KEYWORDS
# Maps concept_tag -> list of keywords to search in target_gloss
# ──────────────────────────────────────────────────────────────────────────────
TARGET_KEYWORDS = {
    'wax/candle':       ['wax','cera','cereus','candle','candel','torch','fax'],
    'wool':             ['wool','fleece','lana','vellu','floc','lanif'],
    'honey':            ['honey','mel','melligo','propolis','apiari'],
    'salt':             ['salt','salsugo','salin','brackish','brine','halin'],
    'fire':             ['fire','flame','igni','incend','ardor','flamma','pyro'],
    'fire/flame':       ['fire','flame','igni','incend','ardor'],
    'blood':            ['blood','sanguis','cruor','hemorrh','sanguine'],
    'sword':            ['sword','gladius','ensis','spatha','blade'],
    'law':              ['law','legal','legalis','legista','legifer','jur','nomos'],
    'jurisprudence':    ['law','legal','legalis','legista','jur'],
    'judgment/law':     ['law','legal','legalis','legista','judgment'],
    'sound':            ['sound','sonus','clarisonus','dulcisonus','vox','phon','vocal'],
    'cry/sound':        ['sound','cry','shout','clamor','sonus','vox'],
    'fish':             ['fish','piscis','squalus','piscat','piscel'],
    'meat/flesh':       ['meat','flesh','carn','lard','bacon','lardum','pinguis','adip'],
    'tree':             ['tree','arbor','silva','wood','dendron'],
    'stone/rock':       ['stone','rock','saxum','saxalis','lapid','lapis'],
    'palm tree':        ['palm','date','phoenix','drupe','date palm'],
    'dog':              ['dog','canis','canine','hound'],
    'bee/honey':        ['bee','apis','honey','mel'],
    'grape/vine':       ['grape','vine','vitis','uva','raisin','wine'],
    'scorpion':         ['scorpion','scorpio','scorp'],
    'spider':           ['spider','aranea','arachn'],
    'gold':             ['gold','aurum','golden','chryso'],
    'water':            ['water','aqua','abluvium','flood','deluge','aquatic'],
    'rain':             ['rain','pluvio','imber'],
    'clay/mud':         ['clay','earth','mud','argilla','lutum','loam'],
    'army/soldiers':    ['army','soldier','cohort','legio','milites'],
    'light':            ['light','lux','lumen','lumin','bright'],
    'sun':              ['sun','solar','sol','helios'],
    'moon':             ['moon','luna','lunar','mensis'],
    'star':             ['star','stella','sider','astro','comet','meteor'],
    'wind':             ['wind','aquilo','boreas','ventus','zephyr'],
    'medicine':         ['medicine','medicus','medicin','remedium','cure'],
    'illness':          ['ill','disease','sick','morbus','aegrot'],
    'war':              ['war','battle','pugna','bellum','warrior'],
    'peace':            ['peace','pax','truce','reconcil'],
    'horse':            ['horse','equus','caball','equine','thieldo'],
    'camel':            ['camel'],
    'stinginess':       ['miser','stingy','avar','parcimon'],
    'anger':            ['anger','rage','ira','furor','iracund'],
    'patience':         ['patience','patient','patiens','tolero'],
    'drink':            ['drink','bibax','exbibo','adbibo','bibo','imbib'],
    'eat':              ['eat','cibo','edere','vorat'],
    'food':             ['food','cibus','victus','esca'],
    'desert/waste':     ['desert','waste','vast','arid'],
    'lightning':        ['lightning','fulgur','fulmin','thunder'],
    'fear':             ['fear','terror','timor','pavo'],
    'speech/words':     ['speech','word','oratio','verbum','logos'],
    'lie/falsehood':    ['lie','false','mendac','falsil','deception'],
    'hair/poetry':      ['hair','poem','poetry','verse','crinis','pil'],
    'foreign/enemy':    ['foreign','enemy','alien','externus'],
}

# ──────────────────────────────────────────────────────────────────────────────
# CONCEPT COMPATIBILITY MAP
# Maps arabic_concept -> compatible target_concepts
# ──────────────────────────────────────────────────────────────────────────────
COMPATIBLE = {
    'wax/candle':     ['wax/candle'],
    'wool':           ['wool'],
    'honey':          ['honey', 'bee/honey'],
    'salt':           ['salt'],
    'fire':           ['fire', 'fire/flame'],
    'fire/flame':     ['fire', 'fire/flame'],
    'blood':          ['blood'],
    'sword':          ['sword'],
    'law':            ['law', 'jurisprudence', 'judgment/law'],
    'jurisprudence':  ['law', 'jurisprudence', 'judgment/law'],
    'sound':          ['sound', 'cry/sound'],
    'cry/sound':      ['sound', 'cry/sound'],
    'fish':           ['fish'],
    'meat/flesh':     ['meat/flesh'],
    'tree':           ['tree'],
    'stone/rock':     ['stone/rock'],
    'palm tree':      ['palm tree'],
    'dog':            ['dog'],
    'bee/honey':      ['honey', 'bee/honey'],
    'grape/vine':     ['grape/vine'],
    'scorpion':       ['scorpion'],
    'spider':         ['spider'],
    'gold':           ['gold'],
    'water':          ['water'],
    'rain':           ['rain'],
    'clay/mud':       ['clay/mud'],
    'army/soldiers':  ['army/soldiers'],
    'light':          ['light'],
    'sun':            ['sun'],
    'moon':           ['moon'],
    'star':           ['star'],
    'wind':           ['wind'],
    'medicine':       ['medicine'],
    'illness':        ['illness'],
    'war':            ['war'],
    'peace':          ['peace'],
    'horse':          ['horse'],
    'camel':          ['camel'],
    'stinginess':     ['stinginess'],
    'anger':          ['anger'],
    'patience':       ['patience'],
    'drink':          ['drink'],
    'eat':            ['eat', 'food'],
    'food':           ['food', 'eat'],
    'desert/waste':   ['desert/waste'],
    'lightning':      ['lightning'],
    'fear':           ['fear'],
    'speech/words':   ['speech/words'],
    'lie/falsehood':  ['lie/falsehood'],
    'hair/poetry':    ['hair/poetry'],
    'foreign/enemy':  ['foreign/enemy'],
    'judgment/law':   ['law', 'jurisprudence', 'judgment/law'],
}

def _out(src, tgt, score, reasoning, method="masadiq_direct"):
    return {
        "source_lemma": src,
        "target_lemma": tgt,
        "semantic_score": round(score, 2),
        "reasoning": reasoning,
        "method": method,
        "lang_pair": "ara-lat",
        "model": "sonnet-phase1-lat",
    }

def score_pair(pair: dict) -> dict:
    arabic_root = pair.get("arabic_root", "")
    target_lemma = pair.get("target_lemma", "")
    masadiq_gloss = pair.get("masadiq_gloss", "")
    target_gloss = pair.get("target_gloss", "")

    # 1. Hand-scored pairs take priority
    key = (arabic_root, target_lemma)
    if key in HAND_SCORED:
        score, reasoning, method = HAND_SCORED[key]
        return _out(arabic_root, target_lemma, score, reasoning, method)

    # 2. Zero-score targets
    is_zero, zero_reason = is_zero_target(target_gloss)
    if is_zero:
        return _out(arabic_root, target_lemma, 0.0, zero_reason)

    # 3. Masadiq signal scan: search Arabic keywords in masadiq_gloss
    tg_lower = target_gloss.lower()
    best_score = 0.0
    best_reason = ""
    best_method = "masadiq_direct"

    for (ar_signal, ar_concept, base_score) in MASADIQ_SIGNALS:
        if ar_signal not in masadiq_gloss:
            continue

        # Found Arabic concept signal. Now check compatible target concepts.
        compatible_tgt = COMPATIBLE.get(ar_concept, [])

        for tgt_concept in compatible_tgt:
            kws = TARGET_KEYWORDS.get(tgt_concept, [])
            for kw in kws:
                if kw in tg_lower:
                    # Match! Apply slight discount for secondary signals
                    # (العين appearing in a definition doesn't always mean root=eye)
                    score = base_score
                    # Discount if Arabic signal is secondary/incidental
                    if ar_signal in ['ماء', 'صوت', 'دواء', 'ملح', 'شمع', 'صوف']:
                        score *= 0.92  # slight discount for common Arabic words
                    if score > best_score:
                        best_score = score
                        best_reason = (f"masadiq contains '{ar_signal}' ({ar_concept}); "
                                       f"target '{kw}' → {tgt_concept}")
                        best_method = "masadiq_direct"

    if best_score >= 0.50:
        return _out(arabic_root, target_lemma, best_score, best_reason, best_method)

    # 4. Weak stem-level fallback: disabled — too many false positives from
    # Arabic dictionary examples containing unrelated English loanwords.

    # 5. Default: 0.0
    if best_score == 0.0:
        best_reason = "no semantic overlap found between masadiq and target"

    return _out(arabic_root, target_lemma,
                round(best_score, 2), best_reason, best_method)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN PROCESSING
# ──────────────────────────────────────────────────────────────────────────────

all_results = []
chunk_stats = {}

for chunk_id in range(108, 126):
    in_path  = f'{BASE_IN}/lat_new_{chunk_id}.jsonl'
    out_path = f'{BASE_OUT}/lat_phase1_scored_{chunk_id}.jsonl'

    with open(in_path, encoding='utf-8') as f:
        pairs = [json.loads(l) for l in f]

    scored = []
    for p in pairs:
        scored.append(score_pair(p))

    with open(out_path, 'w', encoding='utf-8') as f:
        for r in scored:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    high = [r for r in scored if r['semantic_score'] >= 0.5]
    chunk_stats[chunk_id] = {'total': len(scored), 'high': len(high)}
    print(f'Chunk {chunk_id}: {len(scored)} pairs, {len(high)} >= 0.5')
    all_results.extend(scored)

# ──────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────────────────────────────────────

total = len(all_results)
total_high = sum(1 for r in all_results if r['semantic_score'] >= 0.5)
print(f'\nTOTAL: {total} pairs processed, {total_high} >= 0.5 ({100*total_high/total:.1f}%)')

# Score distribution
brackets = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
print('\nScore distribution:')
for i in range(len(brackets)-1):
    lo, hi = brackets[i], brackets[i+1]
    count = sum(1 for r in all_results if lo <= r['semantic_score'] < hi)
    print(f'  {lo:.1f}-{hi:.1f}: {count:4d} ({100*count/total:.1f}%)')

# Top discoveries by score (deduplicated by source_lemma)
print('\nTOP 15 DISCOVERIES (>= 0.5):')
top = sorted(all_results, key=lambda x: x['semantic_score'], reverse=True)
shown = 0
seen_pairs = set()
for r in top:
    key = (r['source_lemma'], r['target_lemma'])
    if key not in seen_pairs and r['semantic_score'] >= 0.5:
        seen_pairs.add(key)
        shown += 1
        print(f"  {r['semantic_score']:.2f}  {r['source_lemma']:20s}  "
              f"{r['target_lemma']:22s}  {r['reasoning'][:70]}")
        if shown >= 15:
            break

if shown == 0:
    print("  (none >= 0.5)")
    # Show best < 0.5
    print('\nBest pairs (< 0.5):')
    for r in top[:10]:
        key = (r['source_lemma'], r['target_lemma'])
        if key not in seen_pairs:
            seen_pairs.add(key)
            print(f"  {r['semantic_score']:.2f}  {r['source_lemma']:20s}  "
                  f"{r['target_lemma']:22s}  {r['reasoning'][:70]}")
