"""
Expert semantic scorer for chunks 139-169.
MASADIQ-FIRST methodology: read Arabic dictionary gloss, match to Greek semantic field.
"""
from __future__ import annotations
import json
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def expert_score(arabic_root: str, masadiq: str, mafahim: str,
                 target_lemma: str, target_gloss: str) -> tuple[float, str, str]:
    """Return (score, reasoning, method)."""
    ag = (masadiq or '')
    ag_l = ag.lower()
    tg = (target_gloss or '').strip()
    tg_l = tg.lower()

    if not tg:
        return 0.0, 'no target gloss', 'weak'

    # ── PROPER NOUNS ──
    # Check for proper noun / toponym on target side
    proper_indicators = [
        'a male given name', 'a female given name', 'a river in', 'a mountain in',
        'an ancient town', 'an ancient city', 'a city in', 'a town in', 'an island',
        'a cape', 'a sea', 'a region', 'a district', 'a tribe', 'a people',
        'an inhabitant', 'a philosopher', 'a king', 'a queen', 'a poet', 'a hero',
        'a nymph', 'a satyr', 'a nereid', 'son of ', 'daughter of ', 'mythological',
        'a battle', 'a festival', 'a rite', 'a river of', 'a lake', 'charybdis',
        'a vlach', 'a croat', 'a tocharian', 'a persian', 'an achaean', 'a laconian',
        'a disciple', 'equivalent to english', 'from old persian', 'from egyptian',
        'from old', 'a river', 'thermodon', 'spercheios', 'phlegethon', 'ordessus',
    ]
    tg_proper = any(ind in tg_l for ind in proper_indicators)
    # Also if target starts with capital and is short (likely proper noun)
    words = tg.split()
    if words and words[0][0].isupper() and len(words[0]) > 2:
        first_lower = words[0].lower()
        if not first_lower.startswith(('the', 'a ', 'an ')):
            # Looks like a proper name
            tg_proper = True

    if tg_proper:
        # Check if Arabic is also a toponym
        ara_toponym = any(w in ag for w in ['موضع', 'بلد', 'د بين', 'بالرّوم', 'قرية',
                                              'مدينة', 'ثغر', 'بناحي', 'بإصطخر', 'بفيروز',
                                              'همذان', 'بنواحي', 'د من', 'الروم'])
        if ara_toponym:
            return 0.1, 'both possibly toponyms but different places', 'weak'
        return 0.0, 'target is proper noun/place/personal name', 'weak'

    # ── PURELY GRAMMATICAL FORMS (no semantic content) ──
    gram_markers = [
        'nominative/accusative/vocative plural',
        'masculine/feminine/neuter dative plural',
        'masculine/feminine/neuter genitive',
        'masculine accusative plural',
        'masculine vocative singular',
        'feminine genitive/dative dual',
        'aorist active infinitive of',
        'aorist passive participle of',
        'aorist active participle of',
        'passive aorist participle of',
        'present mediopassive infinitive',
        'first-person plural aorist',
        'second-person plural aorist',
        'third-person singular aorist',
        'superlative degree of',
        'neuter nominative/accusative/vocative plural',
    ]
    if any(g in tg_l for g in gram_markers):
        return 0.0, 'purely grammatical form, no semantic content', 'weak'

    # ══════════════════════════════════════════════════════
    # MASADIQ-FIRST SEMANTIC MATCHING
    # Read Arabic dictionary meaning, match against Greek gloss
    # ══════════════════════════════════════════════════════

    # CUTTING / BREAKING / SEVERING
    ara_cut = any(w in ag for w in [
        'قطعه', 'قطعَه', 'يقطع', 'قطع', 'كسره', 'يكسر', 'كسر',
        'شقّه', 'يشق', 'شق', 'بتر', 'حزّ', 'فصله', 'يفصل',
        'يقصف', 'قصفه', 'يقصب', 'يقطل', 'قطله', 'قصمل',
        'قرصبه', 'قرصمه', 'قعطبه', 'قطمه', 'يقطم', 'لتخه',
        'لحته', 'قشر', 'كشط', 'سلخ', 'نحر', 'ذبح', 'كشمر أنفه',
        'بري', 'نحت', 'حفر', 'خرق', 'ثقب', 'شقه', 'قطعًا',
    ])
    grc_cut = any(w in tg_l for w in [
        'cut', 'sever', 'split', 'cleave', 'chop', 'hew', 'slash',
        'slice', 'shear', 'dissect', 'carve', 'engrave', 'incise',
        'scrape', 'scratch', 'sharpen', 'pierce', 'slit', 'bisect',
        'divide', 'truncate', 'amputate', 'lop', 'notch', 'score',
        'snip', 'crop', 'clip', 'trim', 'prune', 'reap',
    ])
    if ara_cut and grc_cut:
        return 0.6, 'cutting/severing sense in both', 'masadiq_direct'

    # STRIKING / BEATING / HITTING
    ara_strike = any(w in ag for w in [
        'ضربه', 'ضربَه', 'يضرب', 'ضرب', 'صفع', 'لطمه', 'لكزه',
        'وجأه', 'طعنه', 'لفحه', 'لتحه', 'لطحه', 'وثم', 'دق',
        'نحزه', 'نخزه', 'وتخه', 'رمى', 'رمى بحجر',
    ])
    grc_strike = any(w in tg_l for w in [
        'strike', 'hit', 'beat', 'smite', 'punch', 'blow', 'buffet',
        'slap', 'lash', 'flog', 'thrash', 'batter', 'pound',
    ])
    if ara_strike and grc_strike:
        return 0.6, 'striking/hitting sense in both', 'masadiq_direct'

    # FLEEING / ESCAPING / RUNNING AWAY
    ara_flee = any(w in ag for w in ['هرب', 'فرّ', 'هاجر', 'رحل', 'ذهب بعيدا'])
    grc_flee = any(w in tg_l for w in ['flee', 'escape', 'fly from', 'run away', 'evade'])
    if ara_flee and grc_flee:
        return 0.5, 'fleeing/escaping sense in both', 'masadiq_direct'

    # MOVEMENT / JUMPING / LEAPING
    ara_move = any(w in ag for w in [
        'وثب', 'يثب', 'قفز', 'يقفز', 'جرى', 'يجري', 'عدا', 'يعدو',
        'ثار', 'نفز', 'وثبان', 'الوثبان', 'قفزان', 'طار',
    ])
    grc_move = any(w in tg_l for w in [
        'jump', 'leap', 'spring', 'bound', 'rush upon', 'charge',
        'dart', 'skip', 'hop', 'pounce',
    ])
    if ara_move and grc_move:
        return 0.5, 'jumping/leaping sense in both', 'masadiq_direct'

    # GENERAL MOVEMENT / WALKING / GOING
    ara_walk = any(w in ag for w in ['مشى', 'سار', 'ذهب', 'عدو', 'الكرنجة', 'يسير'])
    grc_walk = any(w in tg_l for w in [
        'walk', 'march', 'travel', 'go', 'come', 'move', 'proceed',
        'advance', 'approach', 'depart', 'hasten',
    ])
    if ara_walk and grc_walk:
        return 0.4, 'general movement sense in both', 'masadiq_direct'

    # BINDING / TYING / FASTENING
    ara_bind = any(w in ag for w in [
        'شدّ', 'شده', 'ربط', 'عقد', 'قيّد', 'قيده', 'أوثق',
        'شدّ يديه', 'قمطه',
    ])
    grc_bind = any(w in tg_l for w in [
        'bind', 'tie', 'fasten', 'attach', 'chain', 'tether', 'fetter',
        'knot', 'cord', 'rope', 'wrap', 'bundle', 'shackle', 'truss',
    ])
    if ara_bind and grc_bind:
        return 0.6, 'binding/tying sense in both', 'masadiq_direct'

    # COVERING / HIDING / CONCEALING
    ara_cover = any(w in ag for w in [
        'ستره', 'أخفاه', 'تغطّى', 'غطّى', 'لفّ', 'أدخل في',
        'الالتحاف', 'التحف', 'كتمه', 'يكتم', 'كتّم',
    ])
    grc_cover = any(w in tg_l for w in [
        'cover', 'hide', 'conceal', 'veil', 'cloak', 'shroud', 'overlay',
        'wrap', 'mask', 'obscure', 'screen', 'envelop',
    ])
    if ara_cover and grc_cover:
        return 0.5, 'covering/concealing sense in both', 'masadiq_direct'

    # WRITING / MARKING / INSCRIBING
    ara_write = any(w in ag for w in [
        'كتبه', 'خطّه', 'كتاب', 'نقش', 'رسم', 'كاتب',
    ])
    grc_write = any(w in tg_l for w in [
        'write', 'engrave', 'inscribe', 'carve', 'mark', 'paint',
        'draw', 'inscription', 'script', 'etch', 'chisel',
    ])
    if ara_write and grc_write:
        return 0.5, 'writing/marking sense in both', 'masadiq_direct'

    # HANDBOOK / MANUAL / DOCUMENT
    ara_book = any(w in ag for w in ['كتاب', 'مخطوط', 'رسالة', 'كتيب'])
    grc_book = any(w in tg_l for w in ['handbook', 'manual', 'guide', 'compendium'])
    if ara_book and grc_book:
        return 0.4, 'document/handbook sense in both', 'combined'

    # LOOKING / SEEING / OBSERVING
    ara_see = any(w in ag for w in [
        'نظر', 'رأى', 'أبصر', 'بصره', 'لحظه', 'رمق', 'أبصره',
        'نظر بمؤخر عينيه',
    ])
    grc_see = any(w in tg_l for w in [
        'see', 'look', 'gaze', 'observe', 'watch', 'sight', 'behold',
        'view', 'perceive', 'eye', 'vision', 'glance',
    ])
    if ara_see and grc_see:
        return 0.5, 'visual perception sense in both', 'masadiq_direct'

    # FIRE / BURNING
    ara_fire = any(w in ag for w in [
        'حرق', 'أحرقه', 'نار', 'اشتعل', 'وقد', 'لهب',
    ])
    grc_fire = any(w in tg_l for w in [
        'burn', 'fire', 'flame', 'blaze', 'kindle', 'scorch', 'char',
        'cauterize', 'incinerate', 'ignite', 'combust', 'burnt in',
    ])
    if ara_fire and grc_fire:
        return 0.6, 'fire/burning sense in both', 'masadiq_direct'

    # POURING / SCOOPING / SCATTERING
    ara_pour = any(w in ag for w in [
        'صبّ', 'سقى', 'غرف', 'نضح', 'رش', 'نثر', 'أفاض',
        'غرفة بيده',  # scooping
    ])
    grc_pour = any(w in tg_l for w in [
        'pour', 'shower', 'sprinkle', 'drench', 'scatter', 'diffuse',
        'pour down', 'shower down', 'scatter down', 'sprinkle over',
    ])
    if ara_pour and grc_pour:
        return 0.5, 'pouring/scattering sense in both', 'masadiq_direct'

    # MIXING / BLENDING / STIRRING
    ara_mix = any(w in ag for w in [
        'خلطه', 'خلط', 'مزج', 'لوّث', 'خلط بين',
    ])
    grc_mix = any(w in tg_l for w in [
        'mix', 'blend', 'mingle', 'combine', 'stir', 'confuse', 'muddle',
    ])
    if ara_mix and grc_mix:
        return 0.4, 'mixing/blending sense in both', 'masadiq_direct'

    # GATHERING / COLLECTING / AMASSING
    ara_gather = any(w in ag for w in [
        'جمعه', 'جمع', 'ضمّه', 'ضم', 'حشد', 'كنز', 'جمّع', 'تجميع',
        'لمّ', 'القصملة', 'شيء قرمش',
    ])
    grc_gather = any(w in tg_l for w in [
        'gather', 'collect', 'assemble', 'heap', 'accumulate', 'amass',
        'muster', 'bring together', 'gathered together', 'brought together',
    ])
    if ara_gather and grc_gather:
        return 0.5, 'gathering/collecting sense in both', 'masadiq_direct'

    # SOUND / RINGING / CRASHING / NOISE
    ara_sound = any(w in ag for w in [
        'صوت', 'ضجّ', 'رنّ', 'صاح', 'نادى', 'اشتد صوت',
        'قصيفا', 'الصياح',
    ])
    grc_sound = any(w in tg_l for w in [
        'sound', 'ring', 'clang', 'clash', 'noise', 'resound', 'roar',
        'crash', 'rumble', 'thunder', 'clanging', 'clashing',
    ])
    if ara_sound and grc_sound:
        return 0.5, 'sound/noise sense in both', 'masadiq_direct'

    # DECEPTION / CUNNING / TRICKERY
    ara_trick = any(w in ag for w in [
        'خبّ', 'خبيث', 'مكر', 'حيلة', 'خداع', 'دهاء', 'المخرقة',
        'المموّه', 'كذب', 'كذّاب',
    ])
    grc_trick = any(w in tg_l for w in [
        'wily', 'cunning', 'sly', 'crafty', 'deceitful', 'treacherous',
        'devious', 'scheming', 'rogue', 'thief', 'pirate', 'highway robber',
        'trickster', 'fraudulent', 'deception',
    ])
    if ara_trick and grc_trick:
        return 0.5, 'trickery/cunning sense in both', 'masadiq_direct'

    # DIFFICULTY / HARDSHIP / SUFFERING
    ara_hard = any(w in ag for w in [
        'مشقته', 'غمّه', 'شدّة', 'ألم', 'تعب', 'بلغ مشقته',
        'الشدائد', 'جبّنته',
    ])
    grc_hard = any(w in tg_l for w in [
        'suffer', 'hardship', 'distress', 'toil', 'labour', 'pain',
        'difficulty', 'ill', 'wretched', 'miserable', 'be in ill plight',
    ])
    if ara_hard and grc_hard:
        return 0.5, 'hardship/difficulty sense in both', 'masadiq_direct'

    # MILK / DAIRY / CHURNING
    ara_dairy = any(w in ag for w in [
        'لبن', 'زبد', 'مخض', 'حليب', 'دسم', 'سمهج', 'لمهج', 'دسمًا',
    ])
    grc_dairy = any(w in tg_l for w in [
        'milk', 'cream', 'butter', 'churn', 'whey', 'curd', 'dairy',
        'milky', 'creamy',
    ])
    if ara_dairy and grc_dairy:
        return 0.5, 'dairy/milk sense in both', 'masadiq_direct'

    # GRAIN / WHEAT / BARLEY / GROATS
    ara_grain = any(w in ag for w in [
        'حنطة', 'شعير', 'قمح', 'دقيق', 'حبوب', 'عجين',
    ])
    grc_grain = any(w in tg_l for w in [
        'grain', 'wheat', 'barley', 'groat', 'groats', 'flour', 'meal',
        'corn', 'cereal',
    ])
    if ara_grain and grc_grain:
        return 0.5, 'grain/cereal sense in both', 'masadiq_direct'

    # PLANT / HERB / WOOD / ALGAE
    ara_plant = any(w in ag for w in [
        'شجر', 'نبت', 'نبات', 'عود', 'حشيش', 'طحلب', 'عشب',
        'ورق', 'أعواد', 'إذخر',
    ])
    grc_plant = any(w in tg_l for w in [
        'plant', 'herb', 'tree', 'shrub', 'weed', 'wood', 'algae',
        'seaweed', 'moss', 'reed', 'teasel', 'dodder', 'succory',
        'peony', 'elder', 'pennyroyal', 'vervain', 'mercury', 'oxtongue',
        'hemp', 'flax', 'juncea', 'pulegium', 'juniper',
    ])
    if ara_plant and grc_plant:
        return 0.4, 'plant/herb sense in both', 'masadiq_direct'

    # SPEAR / LANCE / WEAPON
    ara_spear = any(w in ag for w in ['رمح', 'حربة', 'سيف', 'سهم', 'طعنه'])
    grc_spear = any(w in tg_l for w in [
        'spear', 'lance', 'javelin', 'spear-head', 'pike', 'shaft',
        'small spear',
    ])
    if ara_spear and grc_spear:
        return 0.6, 'spear/weapon sense in both', 'masadiq_direct'

    # EATING / DEVOURING / CONSUMING
    ara_eat = any(w in ag for w in [
        'أكل', 'ابتلع', 'التقم', 'أكله', 'يأكل', 'يلتقمه',
        'شدة الأكل', 'أكله',
    ])
    grc_eat = any(w in tg_l for w in [
        'eat', 'devour', 'consume', 'swallow', 'gulp', 'feed', 'nibble',
        'munch', 'gnaw', 'chew',
    ])
    if ara_eat and grc_eat:
        return 0.5, 'eating/consuming sense in both', 'masadiq_direct'

    # SULFUR / MINERALS / SALT
    ara_mineral = any(w in ag for w in ['كبريت', 'كبريتا', 'ملح', 'معدن'])
    grc_mineral = any(w in tg_l for w in [
        'sulfur', 'sulphur', 'brimstone', 'salt', 'mineral', 'niter',
    ])
    if ara_mineral and grc_mineral:
        return 0.5, 'mineral/sulfur sense in both', 'masadiq_direct'

    # FRAGRANCE / SCENT / PERFUME / AMBER
    ara_scent = any(w in ag for w in ['عنبر', 'طيّب', 'رائحة', 'عطر', 'بخور'])
    grc_scent = any(w in tg_l for w in [
        'fragrant', 'scent', 'perfume', 'aroma', 'incense', 'aromatic',
        'ointment', 'unguent',
    ])
    if ara_scent and grc_scent:
        return 0.5, 'fragrance/scent sense in both', 'masadiq_direct'

    # RAIN / DOWNPOUR / PRECIPITATION
    ara_rain = any(w in ag for w in [
        'مطرت', 'سالت', 'هطل', 'تهاطل', 'هتن', 'تهاتن', 'السماء',
    ])
    grc_rain = any(w in tg_l for w in [
        'rain', 'shower', 'downpour', 'torrent', 'drizzle', 'deluge',
        'pour', 'drop', 'drip',
    ])
    if ara_rain and grc_rain:
        return 0.4, 'rain/precipitation sense in both', 'masadiq_direct'

    # WATER / RIVER / POOL / LIQUID
    ara_water = any(w in ag for w in [
        'ماء', 'نهر', 'غدير', 'بحر', 'بئر', 'جرى', 'يجري',
        'سيل', 'مياه',
    ])
    grc_water = any(w in tg_l for w in [
        'water', 'river', 'lake', 'sea', 'flow', 'stream', 'spring',
        'flood', 'wet', 'dewy', 'watery', 'aquatic', 'cistern',
        'reservoir', 'pool',
    ])
    if ara_water and grc_water:
        return 0.5, 'water/liquid sense in both', 'masadiq_direct'

    # POISON / VENOM
    ara_poison = any(w in ag for w in ['سمّ', 'سُمّ', 'سما', 'متعتق'])
    grc_poison = any(w in tg_l for w in [
        'poison', 'venom', 'venomous', 'toxic', 'bitten by a viper',
        'serpent', 'snake bite',
    ])
    if ara_poison and grc_poison:
        return 0.5, 'poison/venom sense in both', 'masadiq_direct'

    # WOOD / INCENSE / ALOESWOOD
    ara_wood = any(w in ag for w in ['المندل', 'عود', 'المندلي', 'الرطب'])
    grc_wood = any(w in tg_l for w in [
        'wood', 'aloeswood', 'incense', 'aromatic wood', 'aloe',
    ])
    if ara_wood and grc_wood:
        return 0.4, 'wood/incense sense in both', 'masadiq_direct'

    # AGREEMENT / COVENANT / TREATY
    ara_agree = any(w in ag for w in ['عاهده', 'وافقه', 'يتعاهد', 'عقد'])
    grc_agree = any(w in tg_l for w in [
        'agree', 'covenant', 'treaty', 'accord', 'pact', 'pledge',
        'hold out', 'keep', 'maintain',
    ])
    if ara_agree and grc_agree:
        return 0.4, 'agreement/covenant sense in both', 'combined'

    # SHAKING / TREMBLING / AGITATION
    ara_shake = any(w in ag for w in [
        'زعزعه', 'حرّكه', 'اضطرب', 'ارتجّ', 'يزعزع',
    ])
    grc_shake = any(w in tg_l for w in [
        'shake', 'tremble', 'agitate', 'vibrate', 'quiver', 'quake',
        'shudder', 'stir', 'disturb',
    ])
    if ara_shake and grc_shake:
        return 0.4, 'shaking/agitation sense in both', 'masadiq_direct'

    # STRAPPING / THROTTLING / STRANGLING
    ara_strangle = any(w in ag for w in ['خنق', 'يخنق', 'نخنق'])
    grc_strangle = any(w in tg_l for w in [
        'strangle', 'throttle', 'choke', 'suffocate', 'garrote',
    ])
    if ara_strangle and grc_strangle:
        return 0.5, 'strangling/throttling sense in both', 'masadiq_direct'

    # COUCH / BED / RESTING PLACE
    ara_bed = any(w in ag for w in ['سرير', 'فراش', 'مضجع'])
    grc_bed = any(w in tg_l for w in [
        'couch', 'bed', 'mattress', 'pallet', 'sleeping place', 'bier',
    ])
    if ara_bed and grc_bed:
        return 0.4, 'couch/bed sense in both', 'combined'

    # CROWN / CREST / HELMET
    ara_crown = any(w in ag for w in ['قمّة', 'تاج', 'خوذة'])
    grc_crown = any(w in tg_l for w in [
        'crown', 'crest', 'helmet', 'cap', 'headgear', 'diadem',
    ])
    if ara_crown and grc_crown:
        return 0.4, 'crown/headgear sense in both', 'masadiq_direct'

    # LEISURE / REST / FREE TIME
    ara_leisure = any(w in ag for w in ['جمع', 'يجمع', 'فراغ', 'يفرغ'])
    grc_leisure = any(w in tg_l for w in [
        'leisure', 'spare time', 'idle', 'rest', 'vacation', 'free time',
    ])
    if ara_leisure and grc_leisure:
        return 0.2, 'faint leisure/rest sense', 'weak'

    # SEPARATION / ASUNDER
    ara_sep = any(w in ag for w in ['فصل', 'فرّق', 'فارق', 'ميّز'])
    grc_sep = any(w in tg_l for w in [
        'separate', 'divide', 'sever', 'asunder', 'apart', 'split into',
        'bifurcate', 'sundered',
    ])
    if ara_sep and grc_sep:
        return 0.4, 'separation/dividing sense in both', 'masadiq_direct'

    # STRETCHING / EXTENDING / STRAIGHTENING
    ara_stretch = any(w in ag for w in ['امتد', 'مال', 'اعتدلت', 'استقامت'])
    grc_stretch = any(w in tg_l for w in [
        'extend', 'stretch', 'prolong', 'elongate', 'lengthen',
        'straighten', 'spread out',
    ])
    if ara_stretch and grc_stretch:
        return 0.4, 'stretching/extension sense in both', 'masadiq_direct'

    # HOLDING / CONTAINING / COMPRISING
    ara_hold = any(w in ag for w in ['يسع', 'يضم', 'يحتوي', 'احتوى', 'شملت'])
    grc_hold = any(w in tg_l for w in [
        'hold', 'contain', 'comprise', 'accommodate', 'take in', 'hold in',
        'encompass', 'include',
    ])
    if ara_hold and grc_hold:
        return 0.4, 'holding/containing sense in both', 'masadiq_direct'

    # BREAST / MAMMARY
    ara_breast = any(w in ag for w in ['ثدي', 'ضرع', 'مصص', 'رضع', 'امتص'])
    grc_breast = any(w in tg_l for w in [
        'breast', 'mammary', 'teat', 'udder', 'nipple', 'bosom',
    ])
    if ara_breast and grc_breast:
        return 0.5, 'breast/mammary sense in both', 'masadiq_direct'

    # DRINKING / SUCKING / IMBIBING
    ara_drink = any(w in ag for w in ['شربه', 'امتصه', 'مصه', 'يمص', 'مصص'])
    grc_drink = any(w in tg_l for w in [
        'drink', 'sip', 'imbibe', 'suck', 'absorb', 'draw', 'quaff',
    ])
    if ara_drink and grc_drink:
        return 0.4, 'drinking/sucking sense in both', 'masadiq_direct'

    # LYING DOWN / SLEEPING / COHABITING
    ara_lie = any(w in ag for w in ['اضطجع', 'نكح', 'لخب', 'يضطجع', 'نام'])
    grc_lie = any(w in tg_l for w in [
        'lie with', 'sleep with', 'cohabit', 'lie down', 'recline',
        'lay beside',
    ])
    if ara_lie and grc_lie:
        return 0.4, 'lying/reclining/cohabiting sense in both', 'combined'

    # DISORDER / CONFUSED SPEECH / BABBLE
    ara_babble = any(w in ag for w in ['كلام لا نظام له', 'هذيان', 'ثرثرة'])
    grc_babble = any(w in tg_l for w in [
        'idle talk', 'babble', 'empty talk', 'chatter', 'babbling',
        'meaningless speech',
    ])
    if ara_babble and grc_babble:
        return 0.5, 'babble/idle talk sense in both', 'masadiq_direct'

    # DISPUTING / QUARRELLING / FIGHTING OVER WORDS
    ara_dispute = any(w in ag for w in ['نزاع', 'جدال', 'خصام'])
    grc_dispute = any(w in tg_l for w in [
        'dispute', 'quarrel', 'fight about words', 'war over words',
        'argue',
    ])
    if ara_dispute and grc_dispute:
        return 0.4, 'dispute/quarrel sense in both', 'combined'

    # TRANSFORMING / CHANGING FORM
    ara_transform = any(w in ag for w in ['حوّل صورته', 'مسخ', 'مسخه', 'يمسخ'])
    grc_transform = any(w in tg_l for w in [
        'transform', 'metamorphose', 'change form', 'convert', 'mutate',
    ])
    if ara_transform and grc_transform:
        return 0.4, 'transformation sense in both', 'combined'

    # FLUTE / MUSIC INSTRUMENT CASE
    ara_flute = any(w in ag for w in ['ناي', 'مزمار', 'نفخ'])
    grc_flute = any(w in tg_l for w in ['flute', 'flute-case', 'pipe', 'aulos'])
    if ara_flute and grc_flute:
        return 0.4, 'flute/musical sense in both', 'combined'

    # TOSSING / FLYING LIGHTLY
    ara_flutter = any(w in ag for w in ['تطاير', 'خف', 'هفت'])
    grc_flutter = any(w in tg_l for w in [
        'flutter', 'fly lightly', 'scatter', 'float', 'drift',
    ])
    if ara_flutter and grc_flutter:
        return 0.3, 'light floating/scattering sense', 'weak'

    # DESCENDING / GOING DOWN
    ara_descend = any(w in ag for w in ['نزل', 'هبط', 'انحدر'])
    grc_descend = any(w in tg_l for w in [
        'come down', 'go down', 'descend', 'lower', 'let down', 'sink',
        'fall down', 'down to the ground',
    ])
    if ara_descend and grc_descend:
        return 0.4, 'descending/going-down sense in both', 'masadiq_direct'

    # BLAMING / REBUKING / SCOLDING
    ara_blame = any(w in ag for w in ['لامه', 'عذله', 'أنّبه', 'وبّخه', 'هدّده'])
    grc_blame = any(w in tg_l for w in [
        'blame', 'rebuke', 'scold', 'censure', 'reproach', 'accuse',
    ])
    if ara_blame and grc_blame:
        return 0.4, 'blaming/rebuking sense in both', 'masadiq_direct'

    # DISTRIBUTING / ARRANGING / PLACING
    ara_distribute = any(w in ag for w in ['وزّع', 'رتّب', 'نظّم', 'فرّق'])
    grc_distribute = any(w in tg_l for w in [
        'distribute', 'arrange', 'place separately', 'order', 'dispose',
        'apportion',
    ])
    if ara_distribute and grc_distribute:
        return 0.4, 'distributing/arranging sense in both', 'masadiq_direct'

    # IMPRISONMENT / PRISON
    ara_prison = any(w in ag for w in ['حبس', 'المحبوس', 'سجن'])
    grc_prison = any(w in tg_l for w in ['prison', 'jail', 'confinement', 'detain'])
    if ara_prison and grc_prison:
        return 0.5, 'prison/confinement sense in both', 'masadiq_direct'

    # CHEATING / SWINDLING / DEFRAUDING
    ara_cheat = any(w in ag for w in ['غش', 'احتيال', 'نصب', 'سرق'])
    grc_cheat = any(w in tg_l for w in ['cheat', 'swindle', 'defraud', 'theft', 'rob'])
    if ara_cheat and grc_cheat:
        return 0.4, 'cheating/swindling sense in both', 'combined'

    # FOOT / BOOT / HALF-BOOT (sandal or shoe)
    ara_shoe = any(w in ag for w in ['نعل', 'حذاء', 'خف'])
    grc_shoe = any(w in tg_l for w in [
        'sandal', 'boot', 'shoe', 'slipper', 'half-boot', 'footwear',
    ])
    if ara_shoe and grc_shoe:
        return 0.4, 'footwear sense in both', 'masadiq_direct'

    # MAKING/DOING WORK / LABOR
    ara_work = any(w in ag for w in ['عمل', 'صنع', 'خرط'])
    grc_work = any(w in tg_l for w in [
        'work', 'make', 'craft', 'produce', 'fashion', 'manufacture',
        'toil', 'labour',
    ])
    if ara_work and grc_work:
        return 0.3, 'work/labor sense', 'weak'

    # ELEGANCE / GRACE / BEAUTY / DELICACY
    ara_grace = any(w in ag for w in ['ظريف', 'لطيف', 'ناعم'])
    grc_grace = any(w in tg_l for w in [
        'graceful', 'delicate', 'pretty', 'elegant', 'beautiful',
        'refined', 'dainty',
    ])
    if ara_grace and grc_grace:
        return 0.3, 'grace/elegance sense', 'weak'

    # DARKNESS / GLOOM / SHADOW / CLOUDY
    ara_dark = any(w in ag for w in ['ظلام', 'سحاب', 'كرب', 'ظلمة', 'الطخاء'])
    grc_dark = any(w in tg_l for w in [
        'dark', 'darkness', 'gloom', 'dusk', 'shadow', 'shade',
        'gloomy', 'murky',
    ])
    if ara_dark and grc_dark:
        return 0.4, 'darkness/shadow sense in both', 'masadiq_direct'

    # SNOW / MOUNTAIN PEAKS
    ara_snow = any(w in ag for w in ['ثلج', 'جمد ماؤها', 'برد'])
    grc_snow = any(w in tg_l for w in [
        'snow', 'ice', 'cold', 'icy', 'frost', 'freeze', 'snowed',
        'snow-capped', 'much snowed',
    ])
    if ara_snow and grc_snow:
        return 0.4, 'snow/cold sense in both', 'masadiq_direct'

    # ── DEFAULT ──
    return 0.0, 'no semantic overlap detected', 'weak'


def main():
    all_pairs_file = Path('C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy'
                          '/Juthoor-CognateDiscovery-LV2/outputs/eye2_phase1_chunks'
                          '/all_pairs_139_169.jsonl')
    base_out = Path('C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy'
                    '/Juthoor-CognateDiscovery-LV2/outputs/eye2_results')

    with open(all_pairs_file, encoding='utf-8') as f:
        pairs = [json.loads(l) for l in f if l.strip()]

    # Score all pairs
    scored_by_chunk: dict[int, list] = {}
    for p in pairs:
        score, reason, method = expert_score(
            p['arabic_root'],
            p.get('masadiq_gloss', ''),
            p.get('mafahim_gloss', ''),
            p['target_lemma'],
            p.get('target_gloss', ''),
        )
        chunk = p.get('chunk', 0)
        rec = {
            'source_lemma': p['arabic_root'],
            'target_lemma': p['target_lemma'],
            'semantic_score': round(score, 2),
            'reasoning': reason,
            'method': method,
            'lang_pair': 'ara-grc',
            'model': 'sonnet-phase1',
        }
        scored_by_chunk.setdefault(chunk, []).append(rec)

    # Write per-chunk output files
    total_above = 0
    all_scored = []
    for chunk_n in range(139, 170):
        records = scored_by_chunk.get(chunk_n, [])
        out_file = base_out / f'phase1_scored_{chunk_n}.jsonl'
        with open(out_file, 'w', encoding='utf-8') as fo:
            for rec in records:
                fo.write(json.dumps(rec, ensure_ascii=False) + '\n')
        above = [r for r in records if r['semantic_score'] >= 0.5]
        total_above += len(above)
        all_scored.extend(records)
        print(f'Chunk {chunk_n}: {len(records)} pairs, {len(above)} >= 0.5')

    print(f'\nTOTAL: {len(all_scored)} pairs, {total_above} >= 0.5')

    # Top discoveries
    top = sorted(all_scored, key=lambda x: x['semantic_score'], reverse=True)
    top10 = [r for r in top if r['semantic_score'] >= 0.5][:20]
    print('\nTOP DISCOVERIES (>= 0.5):')
    for r in top10:
        print(f"  {r['semantic_score']} | {r['source_lemma']} <-> {r['target_lemma']} | {r['reasoning']}")


if __name__ == '__main__':
    main()
