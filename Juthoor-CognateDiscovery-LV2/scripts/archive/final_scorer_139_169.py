"""
Final comprehensive expert scorer for chunks 139-169.
MASADIQ-FIRST: honest semantic scoring based on Arabic dictionary meaning vs Greek gloss.
Author: Claude Sonnet (sonnet-phase1)
"""
from __future__ import annotations
import json
import re
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# ─── Lookup table for specific high-confidence pairs ─────────────────────────
# Manually verified pairs with their correct scores
SPECIFIC_OVERRIDES: dict[tuple[str, str], tuple[float, str, str]] = {
    # الرزم: الرازم = emaciated camel unable to rise | μαρασμός = wasting away/atrophy
    # Real semantic match: both describe bodily wasting/emaciation
    ('الرزم', 'μαρασμός'): (0.65, 'Arabic rāzim=emaciated camel unable to rise; Greek=wasting away/atrophy: genuine semantic overlap in wasting/emaciation', 'masadiq_direct'),

    # مخض: churning milk laboriously | μοχθέω: to be weary with toil
    # Both involve laborious effort/exertion; mafahim connection through physical labor
    ('مخض', 'μοχθέω'): (0.35, 'churning milk (strenuous effort) vs being weary with toil: shared concept of laborious exertion, faint', 'mafahim_deep'),

    # بسمل: wrote/said Bismillah | βλασφημέω: to blaspheme
    # Opposite but both are formulaic religious speech acts
    ('بسمل', 'βλασφημέω'): (0.15, 'pious formula (Bismillah) vs sacrilege: antonyms in religious speech domain', 'weak'),

    # قرضه: قطعه (to cut) + نسج الشعر (to compose verse) | κριθίδιον: small barley grain
    # Arabic has cutting and verse-making; Greek is barley. No real connection.
    ('قرضه', 'κριθίδιον'): (0.0, 'cutting/verse-making vs small barley grain: no overlap', 'weak'),

    # الغلفق: طحلب/نبت في الماء (aquatic plant) | ἱερόγλυφος: carver of hieroglyphics
    # Both have -glyph- type elements but different: plant vs carving. No semantic match.
    ('الغلفق', 'ἱερόγλυφος'): (0.0, 'aquatic plant vs hieroglyph carver: no semantic connection', 'weak'),

    # صلخد: قوي شديد (strong camel) | σύλλεκτος: gathered/brought together
    # Strong vs gathered - no connection
    ('صلخد', 'σύλλεκτος'): (0.0, 'strong/powerful vs gathered together: no semantic overlap', 'weak'),

    # نمق: كتب/خط = wrote/inscribed | εἰκονομαχία: iconoclasm (fighting images)
    # Writing vs destroying images - no connection
    ('نمق', 'εἰκονομαχία'): (0.0, 'writing vs iconoclasm: no semantic overlap', 'weak'),

    # نمق: wrote | οἰκονομικός: household management
    # Writing vs managing household: no connection
    ('نمق', 'οἰκονομικός'): (0.0, 'writing vs household management: no overlap', 'weak'),

    # مقته: أبغضه = hated/detested | χαμαιάκτη: dwarf elder plant
    # Hatred vs a plant: no connection
    ('مقته', 'χαμαιάκτη'): (0.0, 'hate/detest vs dwarf elder plant: no overlap', 'weak'),

    # ليف: ليف النخل = palm fiber | ἐλαιόφυλλον: dog's mercury (plant)
    # Palm fiber vs a plant: no real semantic connection despite both being plant-related
    ('ليف', 'ἐλαιόφυλλον'): (0.1, 'palm fiber vs dog\'s mercury plant: both plant-derived but different domains', 'weak'),

    # اللوف: نبات = a plant with bulb | ἐλαιόφυλλον: dog's mercury
    # Both plants but different
    ('اللوف', 'ἐλαιόφυλλον'): (0.1, 'bulb plant vs dog\'s mercury: both plants but unrelated species', 'weak'),
}


def is_proper_noun(target_gloss: str) -> bool:
    """Check if target gloss is a proper noun (place, name, myth)."""
    tg = target_gloss.strip()
    if not tg:
        return True

    tg_l = tg.lower()

    # Explicit proper noun markers
    proper_markers = [
        'a male given name', 'a female given name',
        'a river in', 'a river of', 'the river ', 'a mountain in',
        'an ancient town', 'an ancient city', 'an ancient district',
        'an ancient region', 'an ancient geographic', 'a city in',
        'a town in', 'an island', 'a cape', 'a sea', 'a region of',
        'a district of', 'a tribe of', 'a tribe in', 'a people',
        'an inhabitant of', 'a philosopher', 'a king', 'a queen',
        'a poet', 'a hero', 'a nymph', 'a satyr', 'a nereid',
        'son of ', 'daughter of ', 'mythological', 'legendary',
        'a battle', 'a festival', 'a rite', 'a vlach', 'a croat',
        'a tocharian', 'a persian commander', 'an achaean',
        'a laconian', 'a disciple of', 'equivalent to english',
        'from old persian', 'from egyptian', 'a philosopher of',
        'a lake in', 'a cape at',
    ]
    if any(m in tg_l for m in proper_markers):
        return True

    # Check if starts with capital and is short/looks like name
    words = tg.split()
    if not words:
        return True

    first_word = words[0]
    if first_word[0].isupper() and len(first_word) > 2:
        # Not a proper noun if it starts with these
        not_proper_starts = [
            'A ', 'An ', 'The ', 'To ', 'Of ', 'For ', 'Made ',
            'Any ', 'All ', 'Attic ', 'Boeotian ', 'Aeolic ',
            'Doric ', 'Half-', 'Double ',
        ]
        if not any(tg.startswith(p) for p in not_proper_starts):
            return True

    return False


def is_grammatical_form(target_gloss: str) -> bool:
    """Check if target is a purely grammatical form with no semantic content."""
    tg_l = target_gloss.lower()
    gram_markers = [
        'nominative/accusative/vocative plural',
        'masculine/feminine/neuter dative plural',
        'masculine/feminine/neuter genitive',
        'masculine accusative plural',
        'masculine vocative singular',
        'feminine genitive/dative dual',
        'masculine/feminine/neuter genitive singular',
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
        'masculine/neuter dative singular of',
        'genitive singular of',
        '/(attic)',
        '/(attic) aorist',
        '/(attic) first',
        '/(attic) second',
        '/(attic) third',
    ]
    return any(g in tg_l for g in gram_markers)


def score_semantic(arabic_root: str, masadiq: str, mafahim: str,
                   target_lemma: str, target_gloss: str) -> tuple[float, str, str]:
    """
    Main scoring function.
    Returns (score 0.0-1.0, reasoning, method).
    """
    ag = masadiq or ''
    tg = (target_gloss or '').strip()
    tg_l = tg.lower()

    # ── Check specific overrides first ──
    key = (arabic_root, target_lemma)
    if key in SPECIFIC_OVERRIDES:
        return SPECIFIC_OVERRIDES[key]

    if not tg or len(tg) < 3:
        return 0.0, 'empty target gloss', 'weak'

    # ── Proper noun → automatic fail ──
    if is_proper_noun(tg):
        return 0.0, 'target is proper noun/place/personal name', 'weak'

    # ── Purely grammatical form → fail ──
    if is_grammatical_form(tg):
        return 0.0, 'purely grammatical form, no semantic content', 'weak'

    # ─────────────────────────────────────────────────────────────────────────
    # MASADIQ-FIRST SEMANTIC MATCHING
    # ─────────────────────────────────────────────────────────────────────────

    # ── CUTTING / BREAKING / SEVERING ──
    ara_cut = any(w in ag for w in [
        'قطع', 'كسر', 'شق', 'يقطع', 'يكسر', 'يشق', 'بتر', 'حزّ',
        'يقصف', 'قصفه', 'يقطل', 'يقصب', 'قرصبه', 'قرصمه', 'قعطبه',
        'لتخه', 'لحته', 'قشر', 'كشط', 'سلخ', 'نحر', 'ذبح', 'نحت',
        'حفر', 'خرق', 'ثقب', 'خرذل', 'قطّع',
    ])
    grc_cut = any(w in tg_l for w in [
        'cut', 'sever', 'split', 'cleave', 'chop', 'hew', 'slash',
        'slice', 'shear', 'carve', 'engrave', 'incise', 'scrape',
        'scratch', 'sharpen', 'pierce', 'slit', 'dissect', 'bisect',
        'divide', 'truncate', 'amputate', 'notch', 'score', 'snip',
        'trim', 'prune', 'shave',
    ])
    if ara_cut and grc_cut:
        return 0.6, 'cutting/severing sense in both', 'masadiq_direct'

    # ── STRIKING / BEATING ──
    ara_strike = any(w in ag for w in [
        'ضرب', 'صفع', 'لطم', 'لكز', 'وجأ', 'طعن', 'لفح', 'لتح',
        'لطح', 'وثم', 'دقّ', 'نحز', 'نخز', 'وتخ', 'رمى بحجر',
        'ضربه', 'يضرب',
    ])
    grc_strike = any(w in tg_l for w in [
        'strike', 'hit', 'beat', 'smite', 'punch', 'blow', 'buffet',
        'slap', 'lash', 'flog', 'thrash', 'batter', 'pound', 'knock',
    ])
    if ara_strike and grc_strike:
        return 0.6, 'striking/beating sense in both', 'masadiq_direct'

    # ── WATER / RIVER / LIQUID ──
    ara_water = any(w in ag for w in [
        'ماء', 'نهر', 'غدير', 'بحر', 'بئر', 'يجري', 'سيل',
        'جرى', 'اضطراب الماء', 'الماء الجاري',
    ])
    grc_water = any(w in tg_l for w in [
        'water', 'river', 'lake', 'sea', 'flow', 'stream', 'spring',
        'flood', 'wet', 'dewy', 'watery', 'aquatic', 'cistern',
        'reservoir', 'pool', 'pond',
    ])
    if ara_water and grc_water:
        return 0.5, 'water/liquid sense in both', 'masadiq_direct'

    # ── MOVEMENT / JUMPING / LEAPING ──
    ara_jump = any(w in ag for w in [
        'وثب', 'يثب', 'قفز', 'يقفز', 'ثار', 'نفز', 'وثبان',
        'قفزان', 'الوثب',
    ])
    grc_jump = any(w in tg_l for w in [
        'jump', 'leap', 'spring', 'bound', 'rush upon', 'dart',
        'skip', 'hop', 'pounce', 'burst forth',
    ])
    if ara_jump and grc_jump:
        return 0.5, 'jumping/leaping sense in both', 'masadiq_direct'

    # ── GENERAL MOVEMENT / RUNNING / FLEEING ──
    ara_move = any(w in ag for w in [
        'جرى', 'يعدو', 'مشى', 'سار', 'هرب', 'فرّ', 'يعدو',
        'الكرنجة', 'عدو', 'السير',
    ])
    grc_move = any(w in tg_l for w in [
        'run', 'walk', 'flee', 'escape', 'march', 'hasten', 'travel',
        'go in pursuit', 'pursue',
    ])
    if ara_move and grc_move:
        return 0.4, 'movement/running sense in both', 'masadiq_direct'

    # ── BINDING / TYING ──
    ara_bind = any(w in ag for w in [
        'شدّ', 'شده', 'ربط', 'عقد', 'قيّد', 'قيده', 'أوثق',
        'شدّ يديه', 'قمطه', 'شدّ يدي',
    ])
    grc_bind = any(w in tg_l for w in [
        'bind', 'tie', 'fasten', 'attach', 'chain', 'tether',
        'fetter', 'knot', 'shackle', 'truss',
    ])
    if ara_bind and grc_bind:
        return 0.6, 'binding/tying sense in both', 'masadiq_direct'

    # ── COVERING / CONCEALING / HIDING ──
    ara_cover = any(w in ag for w in [
        'ستره', 'أخفاه', 'تغطّى', 'غطّاه', 'لفّ', 'أدخله', 'يستر',
        'الالتحاف', 'التحف', 'كتمه', 'يكتم', 'غطّاه', 'طمسه',
    ])
    grc_cover = any(w in tg_l for w in [
        'cover', 'hide', 'conceal', 'veil', 'cloak', 'shroud',
        'overlay', 'wrap', 'mask', 'obscure', 'envelop', 'seal',
    ])
    if ara_cover and grc_cover:
        return 0.5, 'covering/concealing sense in both', 'masadiq_direct'

    # ── WRITING / MARKING / INSCRIBING ──
    ara_write = any(w in ag for w in [
        'كتبه', 'خطّه', 'كتب', 'نقش', 'رسم', 'كاتب', 'يكتب',
        'كتاب',
    ])
    grc_write = any(w in tg_l for w in [
        'write', 'engrave', 'inscribe', 'carve', 'mark', 'paint',
        'draw', 'script', 'etch', 'chisel', 'handbook', 'manual',
    ])
    if ara_write and grc_write:
        return 0.5, 'writing/marking sense in both', 'masadiq_direct'

    # ── FIRE / BURNING ──
    ara_fire = any(w in ag for w in [
        'حرق', 'أحرقه', 'نار', 'اشتعل', 'وقد', 'لهب', 'خمدت النار',
    ])
    grc_fire = any(w in tg_l for w in [
        'burn', 'fire', 'flame', 'blaze', 'kindle', 'scorch', 'char',
        'cauterize', 'incinerate', 'ignite', 'combust', 'burnt in',
        'baked in', 'roast',
    ])
    if ara_fire and grc_fire:
        return 0.6, 'fire/burning sense in both', 'masadiq_direct'

    # ── POURING / SCOOPING / SHOWERING ──
    ara_pour = any(w in ag for w in [
        'صبّ', 'سقى', 'غرف', 'نضح', 'رشّ', 'نثر', 'أفاض',
        'غرفة بيده',
    ])
    grc_pour = any(w in tg_l for w in [
        'pour', 'shower', 'sprinkle', 'drench', 'scatter', 'diffuse',
        'pour down', 'shower down', 'cast down',
    ])
    if ara_pour and grc_pour:
        return 0.5, 'pouring/scattering sense in both', 'masadiq_direct'

    # ── MIXING / BLENDING ──
    ara_mix = any(w in ag for w in ['خلطه', 'خلط', 'مزج', 'لوّث', 'خلط بين'])
    grc_mix = any(w in tg_l for w in [
        'mix', 'blend', 'mingle', 'combine', 'stir', 'confuse',
        'muddle', 'intermingle',
    ])
    if ara_mix and grc_mix:
        return 0.4, 'mixing/blending sense in both', 'masadiq_direct'

    # ── GATHERING / COLLECTING ──
    ara_gather = any(w in ag for w in [
        'جمعه', 'جمع', 'ضمّه', 'ضم', 'حشد', 'كنز', 'جمّع', 'لمّ',
    ])
    grc_gather = any(w in tg_l for w in [
        'gather', 'collect', 'assemble', 'heap', 'accumulate', 'amass',
        'muster', 'bring together', 'gathered together', 'brought together',
    ])
    if ara_gather and grc_gather:
        return 0.5, 'gathering/collecting sense in both', 'masadiq_direct'

    # ── SOUND / RINGING / RESONANCE ──
    ara_sound = any(w in ag for w in [
        'صوت', 'ضجّ', 'رنّ', 'صاح', 'نادى', 'اشتد صوت',
        'قصيفا', 'الصياح', 'السير العنيف',
    ])
    grc_sound = any(w in tg_l for w in [
        'sound', 'ring', 'clang', 'clash', 'noise', 'resound', 'roar',
        'crash', 'rumble', 'thunder', 'clanging', 'clashing', 'resonance',
    ])
    if ara_sound and grc_sound:
        return 0.5, 'sound/resonance sense in both', 'masadiq_direct'

    # ── DECEPTION / CUNNING / TRICKERY ──
    ara_trick = any(w in ag for w in [
        'خبّ', 'خبيث', 'مكر', 'حيلة', 'خداع', 'دهاء', 'المخرقة',
        'المموّه', 'كذب', 'كذّاب',
    ])
    grc_trick = any(w in tg_l for w in [
        'wily', 'cunning', 'sly', 'crafty', 'deceitful', 'treacherous',
        'devious', 'scheming', 'rogue', 'thief', 'pirate', 'highway robber',
    ])
    if ara_trick and grc_trick:
        return 0.5, 'trickery/cunning sense in both', 'masadiq_direct'

    # ── HARDSHIP / DIFFICULTY / DISTRESS ──
    ara_hard = any(w in ag for w in [
        'مشقته', 'غمّه', 'الشدائد', 'ألم', 'تعب', 'بلغ مشقته',
        'جبّنته', 'المرض', 'الدنف',
    ])
    grc_hard = any(w in tg_l for w in [
        'suffer', 'hardship', 'distress', 'toil', 'labour', 'pain',
        'difficulty', 'ill', 'wretched', 'miserable', 'be in ill plight',
        'in distress', 'suffering',
    ])
    if ara_hard and grc_hard:
        return 0.5, 'hardship/difficulty sense in both', 'masadiq_direct'

    # ── SHAKING / AGITATION ──
    ara_shake = any(w in ag for w in [
        'زعزعه', 'حرّكه', 'اضطرب', 'ارتجّ', 'يزعزع',
    ])
    grc_shake = any(w in tg_l for w in [
        'shake', 'tremble', 'agitate', 'vibrate', 'quiver', 'quake',
        'shudder', 'stir', 'disturb', 'leap or rush',
    ])
    if ara_shake and grc_shake:
        return 0.4, 'shaking/agitation sense in both', 'masadiq_direct'

    # ── SCENT / FRAGRANCE ──
    ara_scent = any(w in ag for w in [
        'عنبر', 'طيّب', 'رائحة', 'عطر', 'بخور', 'فاح',
        'نفح الطيب', 'نفحة طيبة',
    ])
    grc_scent = any(w in tg_l for w in [
        'fragrant', 'scent', 'perfume', 'aroma', 'incense', 'aromatic',
        'ointment', 'unguent', 'fragrance',
    ])
    if ara_scent and grc_scent:
        return 0.5, 'fragrance/scent sense in both', 'masadiq_direct'

    # ── MILK / DAIRY ──
    ara_dairy = any(w in ag for w in [
        'لبن', 'زبد', 'مخض', 'حليب', 'دسم', 'سمهج', 'لمهج',
    ])
    grc_dairy = any(w in tg_l for w in [
        'milk', 'cream', 'butter', 'churn', 'whey', 'curd', 'dairy',
    ])
    if ara_dairy and grc_dairy:
        return 0.5, 'dairy/milk sense in both', 'masadiq_direct'

    # ── GRAIN / BARLEY / WHEAT / GROATS ──
    ara_grain = any(w in ag for w in [
        'حنطة', 'شعير', 'قمح', 'دقيق', 'حبوب',
    ])
    grc_grain = any(w in tg_l for w in [
        'grain', 'wheat', 'barley', 'groat', 'groats', 'flour', 'meal',
        'corn', 'cereal', 'barley flour',
    ])
    if ara_grain and grc_grain:
        return 0.5, 'grain/cereal sense in both', 'masadiq_direct'

    # ── PLANT / HERB / AQUATIC VEGETATION ──
    ara_plant = any(w in ag for w in [
        'نبت', 'نبات', 'عود', 'حشيش', 'طحلب', 'عشب',
        'ورقه عراض', 'من النبات',
    ])
    grc_plant = any(w in tg_l for w in [
        'plant', 'herb', 'shrub', 'algae', 'seaweed', 'aquatic plant',
        'weed', 'moss',
    ])
    if ara_plant and grc_plant:
        return 0.4, 'plant/herb sense in both', 'masadiq_direct'

    # ── PRISON / CONFINEMENT ──
    ara_prison = any(w in ag for w in ['حبس', 'للحبس', 'المحبوس', 'سجن'])
    grc_prison = any(w in tg_l for w in ['prison', 'jail', 'confinement', 'detain'])
    if ara_prison and grc_prison:
        return 0.5, 'prison/confinement sense in both', 'masadiq_direct'

    # ── STRANGLING / THROTTLING ──
    ara_strangle = any(w in ag for w in ['خنق', 'يخنق'])
    grc_strangle = any(w in tg_l for w in [
        'strangle', 'throttle', 'choke', 'suffocate',
    ])
    if ara_strangle and grc_strangle:
        return 0.5, 'strangling/throttling sense in both', 'masadiq_direct'

    # ── TURBIDITY / DARKNESS / MURKINESS ──
    ara_turb = any(w in ag for w in [
        'الكدر', 'كدِر', 'نقيض الصفاء', 'كدرة', 'ظلام', 'الطخاء',
        'السحاب',
    ])
    grc_turb = any(w in tg_l for w in [
        'dark', 'darkness', 'gloom', 'dusk', 'murky', 'turbid',
        'muddy', 'opaque',
    ])
    if ara_turb and grc_turb:
        return 0.4, 'turbidity/darkness sense in both', 'masadiq_direct'

    # ── SNOW / ICE / COLD ──
    ara_snow = any(w in ag for w in ['ثلج', 'جمد ماؤها', 'برد صادق', 'الكبريت أبيض'])
    grc_snow = any(w in tg_l for w in [
        'snow', 'ice', 'cold', 'icy', 'frost', 'freeze', 'snowed',
        'snow-capped', 'much snowed',
    ])
    if ara_snow and grc_snow:
        return 0.4, 'snow/cold sense in both', 'masadiq_direct'

    # ── SULFUR / MINERAL ──
    ara_sulf = any(w in ag for w in ['كبريت', 'كبريتا', 'كبريتاً'])
    grc_sulf = any(w in tg_l for w in ['sulfur', 'sulphur', 'brimstone', 'mineral'])
    if ara_sulf and grc_sulf:
        return 0.5, 'sulfur/mineral sense in both', 'masadiq_direct'

    # ── COUCH / BED / LYING DOWN ──
    ara_bed = any(w in ag for w in ['سرير', 'فراش', 'مضجع', 'اضطجع'])
    grc_bed = any(w in tg_l for w in [
        'couch', 'bed', 'mattress', 'pallet', 'sleeping place', 'bier',
        'couch, hence',
    ])
    if ara_bed and grc_bed:
        return 0.4, 'couch/bed sense in both', 'combined'

    # ── WEARING / PUTTING ON / CLOTHING ──
    ara_cloth = any(w in ag for w in ['لبس', 'ثوب', 'كساء', 'رداء', 'كسا'])
    grc_cloth = any(w in tg_l for w in [
        'garment', 'robe', 'tunic', 'cloak', 'linen', 'wear', 'dress',
        'tortoiseshell', 'made of', 'chiton',
    ])
    if ara_cloth and grc_cloth:
        return 0.4, 'clothing/wearing sense in both', 'combined'

    # ── BASKET / CONTAINER / VESSEL ──
    ara_vessel = any(w in ag for w in ['وعاء', 'ظرف', 'غمد', 'قراب', 'إناء'])
    grc_vessel = any(w in tg_l for w in [
        'basket', 'case', 'box', 'chest', 'container', 'vessel',
        'case for', 'holder', 'sheath', 'quiver',
    ])
    if ara_vessel and grc_vessel:
        return 0.4, 'container/vessel sense in both', 'masadiq_direct'

    # ── PEONY / SWEET / RICH TASTE ──
    # لمهج: دسم حلو (rich and sweet milk) | γλυκυσίδη: male peony
    # Both relate to sweetness/pleasant quality — faint
    if 'دسم' in ag and 'حلو' in ag and 'sweet' in tg_l:
        return 0.3, 'richness/sweetness sense - both connote pleasant quality', 'mafahim_deep'

    # ── HEMP / FIBER MATERIAL ──
    # قنبس = a name only; καννάβινος = hempen
    # No semantic match without meaning in Arabic

    # ── SEPARATION / ASUNDER ──
    ara_sep = any(w in ag for w in ['فصل', 'فرّق', 'فارق', 'ميّز'])
    grc_sep = any(w in tg_l for w in [
        'separate', 'divide', 'sever', 'asunder', 'apart', 'bisect',
        'cleave asunder', 'split in two',
    ])
    if ara_sep and grc_sep:
        return 0.4, 'separation/division sense in both', 'masadiq_direct'

    # ── AGREEMENT / ALLIANCE ──
    ara_agree = any(w in ag for w in ['عاهده', 'وافقه', 'يتعاهد', 'الموافقة'])
    grc_agree = any(w in tg_l for w in [
        'agree', 'covenant', 'treaty', 'accord', 'pact', 'pledge',
        'alliance', 'compact',
    ])
    if ara_agree and grc_agree:
        return 0.4, 'agreement/covenant sense in both', 'masadiq_direct'

    # ── DENOUNCING / POINTING OUT / INDICATING ──
    ara_denoun = any(w in ag for w in ['أنكر', 'نقم', 'نقمه', 'يُنقَم'])
    grc_denoun = any(w in tg_l for w in [
        'denounce', 'mark out', 'point out', 'indicate', 'expose',
        'accuse', 'charge',
    ])
    if ara_denoun and grc_denoun:
        return 0.3, 'denunciation/pointing-out sense - faint', 'mafahim_deep'

    # ── BLAMING / SCOLDING ──
    ara_blame = any(w in ag for w in ['لامه', 'عذله', 'أنّبه', 'وبّخه', 'هدّده'])
    grc_blame = any(w in tg_l for w in [
        'blame', 'rebuke', 'scold', 'censure', 'reproach', 'accuse',
    ])
    if ara_blame and grc_blame:
        return 0.4, 'blaming/reproaching sense in both', 'masadiq_direct'

    # ── SEAT / THRONE / SITTING ──
    ara_sit = any(w in ag for w in ['قعد', 'جلس', 'مقعد', 'كرسي', 'سرير'])
    grc_sit = any(w in tg_l for w in [
        'seat', 'throne', 'chair', 'sit', 'sitting place',
    ])
    if ara_sit and grc_sit:
        return 0.4, 'seat/sitting sense in both', 'combined'

    # ── DISTRIBUTING / ARRANGING ──
    ara_distr = any(w in ag for w in ['وزّع', 'رتّب', 'فرّق', 'قسّم', 'نثر'])
    grc_distr = any(w in tg_l for w in [
        'distribute', 'arrange', 'place separately', 'order', 'apportion',
        'dispose', 'place in order',
    ])
    if ara_distr and grc_distr:
        return 0.4, 'distributing/arranging sense in both', 'masadiq_direct'

    # ── FULLNESS / FILLING ──
    ara_full = any(w in ag for w in ['امتلأ', 'ملأ', 'اكتنز', 'امتلاء الجسم'])
    grc_full = any(w in tg_l for w in [
        'full', 'fill', 'filled', 'filled up', 'replete', 'round',
        'plump', 'complete', 'whole',
    ])
    if ara_full and grc_full:
        return 0.4, 'fullness/completeness sense in both', 'masadiq_direct'

    # ── ANGER / RAGE ──
    ara_anger = any(w in ag for w in ['غضب', 'امتلأ غضبا', 'غاضب', 'حرد'])
    grc_anger = any(w in tg_l for w in [
        'anger', 'rage', 'furious', 'wrath', 'angry', 'irate',
        'become angry',
    ])
    if ara_anger and grc_anger:
        return 0.5, 'anger/rage sense in both', 'masadiq_direct'

    # ── LYING / DECEIT / FALSEHOOD ──
    ara_lie = any(w in ag for w in ['كذب', 'كذّاب', 'يكذب'])
    grc_lie = any(w in tg_l for w in [
        'lie', 'liar', 'falsehood', 'deceive', 'untrue', 'mendacity',
    ])
    if ara_lie and grc_lie:
        return 0.5, 'lying/falsehood sense in both', 'masadiq_direct'

    # ── SHOUTING / CRYING OUT ──
    ara_shout = any(w in ag for w in ['الصيّاح', 'صاح', 'نادى', 'صرخ'])
    grc_shout = any(w in tg_l for w in [
        'shout', 'cry out', 'call', 'exclaim', 'yell', 'bawl',
    ])
    if ara_shout and grc_shout:
        return 0.5, 'shouting/calling sense in both', 'masadiq_direct'

    # ── DEFAULT ──
    return 0.0, 'no semantic overlap detected', 'weak'


def main() -> None:
    all_pairs_file = Path(
        'C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy'
        '/Juthoor-CognateDiscovery-LV2/outputs/eye2_phase1_chunks'
        '/all_pairs_139_169.jsonl'
    )
    base_out = Path(
        'C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy'
        '/Juthoor-CognateDiscovery-LV2/outputs/eye2_results'
    )

    with open(all_pairs_file, encoding='utf-8') as f:
        pairs = [json.loads(line) for line in f if line.strip()]

    # Score all pairs
    scored_by_chunk: dict[int, list[dict]] = {}
    for p in pairs:
        score, reason, method = score_semantic(
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
    all_scored: list[dict] = []
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

    print(f'\nTOTAL: {len(all_scored)} pairs processed')
    print(f'Pairs >= 0.5: {total_above}')
    print(f'Pairs >= 0.4: {sum(1 for r in all_scored if r["semantic_score"] >= 0.4)}')
    print(f'Pairs == 0.0: {sum(1 for r in all_scored if r["semantic_score"] == 0.0)}')

    # Top discoveries
    top = sorted(all_scored, key=lambda x: x['semantic_score'], reverse=True)
    print('\nTOP DISCOVERIES (score >= 0.4):')
    for r in top:
        if r['semantic_score'] < 0.4:
            break
        print(f"  {r['semantic_score']} | {r['source_lemma']} <-> {r['target_lemma']}")
        print(f"      {r['reasoning']}")


if __name__ == '__main__':
    main()
