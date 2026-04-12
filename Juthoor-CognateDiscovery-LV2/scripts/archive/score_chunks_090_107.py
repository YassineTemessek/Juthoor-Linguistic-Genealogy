"""
Eye 2 semantic scorer for ara-lat chunks 090-107.
Applies masadiq-first methodology: genuine meaning overlap only.
"""
import json, os, sys, re

sys.stdout.reconfigure(encoding='utf-8')

base_in = "C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_phase1_lat_chunks"
base_out = "C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_results"

# ─────────────────────────────────────────────────────────────
# HELPER: classify target_gloss type
# ─────────────────────────────────────────────────────────────
PROPER_PAT = [
    r'\b(city|town|river|lake|island|mountain|village|region|country|province|sea|harbor|port|gulf)\b',
    r'a male given name', r'a female given name',
    r'a Roman (nomen|cognomen|praenomen|gens|family)',
    r'character in the (play|poem|work)',
    r'a (small |ancient |legendary )?(island|place|tribe|people|nation)',
    r'mentioned by (Pliny|Strabo|Livy|Tacitus)',
    r'equivalent to English [A-Z]',
    r'a member of the (dynasty|people|tribe)',
    r'a (historical|medieval|legendary) (name|person|figure)',
    r'a [A-Z][a-z]+ general',
    r'a king of',
]
GRAM_PAT = [
    r'(first|second|third)-person',
    r'(nominative|accusative|genitive|dative|ablative|vocative)',
    r'(singular|plural) (of|form of)',
    r'(future|perfect|present) (active|passive)',
    r'comparative degree', r'superlative degree',
    r'alternative (letter-case|spelling|form)',
    r'inflected form', r'past participle', r'gerundive',
    r'(future active|perfect active|present active) (infinitive|indicative|imperative|participle)',
    r'participle of',
    r'^(future|perfect|present|past) ',
    r'dative (singular|plural)',
    r'genitive (singular|plural)',
    r'imperative of',
    r'of [a-z]{3,}[oō]\b',
]

def classify_target(gloss):
    g = gloss.lower()
    for p in PROPER_PAT:
        if re.search(p, g):
            return 'proper'
    for p in GRAM_PAT:
        if re.search(p, g):
            return 'gram'
    return 'word'

def strip_ar_vowels(s):
    return re.sub(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED\u0640]', '', s)

# ─────────────────────────────────────────────────────────────
# SEMANTIC TAG PATTERNS
# ─────────────────────────────────────────────────────────────
AR_CONCEPTS = [
    (r'ماء|المَاء|مَطَر|ندى|ثَرَى|رَطْب|يَسيل|سَيَلان|صَبَّ', 'water/flow'),
    (r'نار|حريق|جَمْر|حرارة|لَهَب|يَحترِق', 'fire/heat'),
    (r'ضَرَب|قَتَل|طَعَن|جُرْح|سَيْف|رُمْح|سِلاح|قِتال|حَرْب', 'strike/weapon/war'),
    (r'طَيْر|طائر|جَناح|يَطير|فَرْخ', 'bird/flight'),
    (r'سَمَك|حُوت|سَمَكة', 'fish'),
    (r'كَلْب|ذِئْب|أسَد|وَحْش|سَبُع|حيوان', 'animal/beast'),
    (r'شَجَر|نَبَات|زَرْع|نَخْل|وَرَق|غُصْن|ثَمَر|عُشْب|كَلأ|رِعي', 'plant/vegetation'),
    (r'أرْض|تُراب|رَمْل|صَخْر|حَجَر|جَبَل|تِلَّة', 'earth/stone/mountain'),
    (r'بَيْت|دَار|قَصْر|خَيْمَة|بِناء|غُرْفة', 'house/building'),
    (r'مَلِك|سُلْطان|أمير|حاكِم|رَئيس', 'king/ruler'),
    (r'خُبْز|طَعَام|أكَل|لَحْم|حَبّ|مَرَق|شَرِب', 'food/eating'),
    (r'ذَهَب|فِضَّة|مَعْدِن|نُحاس|حَديد', 'metal/gold'),
    (r'سَيْر|رَكَض|مَشَى|سُرْعة|عَدَا|جَرَى', 'movement/speed'),
    (r'نَوْم|نَعَاس|راحَ|سَكَن|هُدوء', 'sleep/rest'),
    (r'قال|كَلام|نُطْق|لُغَة|صَوْت|نِداء', 'speech/voice'),
    (r'الصَّغير|الحَقير|القَصير|ضَئيل|دَميم', 'small/short/weak'),
    (r'العَظيم|ضَخْم|الكَبير|طويل|شديد', 'large/tall/strong'),
    (r'شِدَّة|صَعوبة|ضِيق|جَدْب|قَحْط', 'hardship/scarcity'),
    (r'نَسَب|قَوْم|قَبيلة|عَشيرة|جَماعة', 'kin/tribe'),
    (r'دَم|جُرْح|مَرَض|أَلَم|قَيْح', 'blood/wound/pain'),
    (r'ظُلُمات|لَيْل|سَواد|الأسْوَد', 'darkness/black'),
    (r'ضَوْء|نور|شَمْس|قَمَر|إضاءة', 'light/sun'),
    (r'بَحْر|نَهْر|بُحيرة|وادٍ|خَليج', 'sea/river'),
    (r'غَنَم|بَقَر|إبِل|ماشِيَة|شاة|ثَوْر|ناقة', 'livestock/cattle'),
    (r'صَبَّ|سَيَل|فَاض|انهَمَر', 'flow/pour'),
    (r'صَوْت|ضَجَّة|صَياح|عَويل|هَدير', 'sound/noise'),
    (r'لِباس|ثَوْب|كِساء|قُمَاش|رِداء', 'cloth/garment'),
    (r'عِلْم|مَعْرِفة|حِكْمة|فِقْه|فَلسَفة', 'knowledge/wisdom'),
    (r'إبْرَيسَم|حَرير|كَتَّان|قَزّ|دِيباج', 'silk/fabric'),
    (r'مَرَض|سُقْم|داء|سَمّ|عِلَّة', 'disease/poison'),
    (r'جَهْل|حُمْق|سَفاهَة|الأحمَق', 'foolishness'),
    (r'بَرَكة|نِعمة|خَيْر|غِنى|ثَرَوة', 'blessing/wealth'),
    (r'الفَرَح|السُّرور|البَهْجة|مَرِح', 'joy/happiness'),
    (r'الحُزْن|الغَمّ|الحَسْرة|أسَى', 'grief/sorrow'),
    (r'يَقطَع|القَطْع|قَطَعَ|شَقَّ', 'cut/sever'),
    (r'يَرجِع|العَوْدة|الرُّجوع|ارتَدَّ', 'return/revert'),
    (r'الوِسادة|المِخَدَّة|الفِراش|مَوْضِع راحة', 'cushion/rest'),
    (r'لُصوق|يَلصَق|لازِب|ثابِت|لَزِج', 'adhesion/sticky'),
    (r'التَّبَخْتُر|الزَّهْو|يَتَبَختَر|الخُيَلاء', 'strut/swagger'),
    (r'يَتَحَمَّل|الصَّبر|الحِلم|يَصبِر', 'patience/endurance'),
    (r'الحَدّ|الحُدود|التَّخوم|فاصِل', 'boundary/limit'),
    (r'غَسَل|يَغسِل|تَطهير|نَظَّف', 'wash/clean'),
    (r'الطِّيب|العِطْر|أريج|رائحة طَيِّبة', 'fragrance/scent'),
    (r'البُرْج|القَلْعة|الحِصْن|سور', 'tower/fortress'),
    (r'الحَرَكة|الوَثْب|يَثِب|قَفَز', 'leap/movement'),
    (r'فُلوس|حَراشِف|حَرشَف', 'scales'),
    (r'دُودة|حَشَرة|دُوَيِّبَّة', 'worm/insect'),
    (r'المُدَوَّر|تَدوير|كُروي|دائري', 'round/circular'),
]

EN_CONCEPTS = [
    (r'\b(water|moisture|wet|damp|liquid|rain|moist|flood|drench)\b', 'water/flow'),
    (r'\b(flow|pour|stream|run|gush|trickle|overflow|drip)\b', 'water/flow'),
    (r'\b(fire|flame|burn|heat|hot|warm|blaze|ignite)\b', 'fire/heat'),
    (r'\b(strike|hit|wound|cut|stab|sword|spear|lance|weapon|war|fight|battle|attack|combat|warfare|strife)\b', 'strike/weapon/war'),
    (r'\b(bird|wing|fly|flight|feather|fledgling|avian)\b', 'bird/flight'),
    (r'\b(fish|bleak|perch|carp|tuna|piscine|aquatic animal)\b', 'fish'),
    (r'\b(animal|beast|lion|wolf|dog|cat|bear|tiger|fierce|feral)\b', 'animal/beast'),
    (r'\b(plant|tree|bush|leaf|branch|root|herb|shrub|flower|bloom|vegetat|botanical|foliage|grass|graze|pasture|flock)\b', 'plant/vegetation'),
    (r'\b(earth|soil|sand|stone|rock|mountain|hill|ground|dust|boulder)\b', 'earth/stone/mountain'),
    (r'\b(house|home|dwelling|shelter|tent|palace|chamber|room|building|hut|abode)\b', 'house/building'),
    (r'\b(king|ruler|emperor|monarch|sovereign|lord|chief|govern)\b', 'king/ruler'),
    (r'\b(food|eat|bread|grain|meat|meal|nourish|drink|wine|beer|consume)\b', 'food/eating'),
    (r'\b(gold|silver|metal|iron|copper|bronze|mineral)\b', 'metal/gold'),
    (r'\b(move|run|swift|fast|speed|quick|gallop|go|rapid|fleet|motion)\b', 'movement/speed'),
    (r'\b(sleep|rest|drowsy|slumber|dormant|repose|quiet|calm)\b', 'sleep/rest'),
    (r'\b(speak|speech|voice|word|say|talk|utter|sound|language|tongue|utterance)\b', 'speech/voice'),
    (r'\b(small|short|little|tiny|minor|diminutive|thin|slender|lean|slim|slight|dwarf)\b', 'small/short/weak'),
    (r'\b(large|great|big|tall|strong|huge|massive|mighty|powerful|vast|enormous)\b', 'large/tall/strong'),
    (r'\b(hardship|difficulty|harsh|hard|tough|severe|distress|scarce|famine|drought)\b', 'hardship/scarcity'),
    (r'\b(kin|clan|tribe|family|race|kindred|nation|people|lineage)\b', 'kin/tribe'),
    (r'\b(blood|wound|pain|injury|hurt|bleed|pus|sore|ulcer)\b', 'blood/wound/pain'),
    (r'\b(dark|darkness|night|black|shadow|obscure|swarthy)\b', 'darkness/black'),
    (r'\b(light|bright|sun|moon|star|shine|glow|radiant|luminous|illuminate)\b', 'light/sun'),
    (r'\b(sea|ocean|lake|river|stream|flood|coast|shore|maritime)\b', 'sea/river'),
    (r'\b(sheep|cattle|cow|bull|ox|camel|goat|flock|livestock|herd|bovine)\b', 'livestock/cattle'),
    (r'\b(flow|pour|stream|gush|trickle|overflow|drip|cascade)\b', 'flow/pour'),
    (r'\b(sound|noise|cry|shout|roar|buzz|hum|voice|song|clamor)\b', 'sound/noise'),
    (r'\b(cloth|garment|robe|dress|cloak|fabric|textile|wool|linen|mantle|vestment|clothing)\b', 'cloth/garment'),
    (r'\b(knowledge|wisdom|learn|teach|science|philosophy|study|sage)\b', 'knowledge/wisdom'),
    (r'\b(silk|satin|fine fabric|brocade|linen)\b', 'silk/fabric'),
    (r'\b(disease|poison|sick|ill|medicine|cure|remedy|toxin|putrid)\b', 'disease/poison'),
    (r'\b(fool|foolish|stupid|silly|rash|witless|senseless|absurd|dull)\b', 'foolishness'),
    (r'\b(blessing|prosperity|grace|bounty|fertile|fortune|wealth|rich|riches|opulent)\b', 'blessing/wealth'),
    (r'\b(joy|happy|glad|merry|cheerful|delight|jolly|jovial|jubilant)\b', 'joy/happiness'),
    (r'\b(grief|sorrow|sad|mourn|lament|woe|distress|weep)\b', 'grief/sorrow'),
    (r'\b(cut|sever|split|chop|cleave|slice|amputate|lop)\b', 'cut/sever'),
    (r'\b(return|go back|revert|come back|relapse|retreat|recede)\b', 'return/revert'),
    (r'\b(cushion|pillow|pad|bolster|seat|headrest)\b', 'cushion/rest'),
    (r'\b(stick|cling|adhere|adhesive|fix|glue|bond|cohere|tacky)\b', 'adhesion/sticky'),
    (r'\b(strut|swagger|boast|prance|parade|sway|striding|arrogant gait)\b', 'strut/swagger'),
    (r'\b(tolerate|endure|bear|patience|suffer|forbear|put up|withstand)\b', 'patience/endurance'),
    (r'\b(boundary|border|limit|frontier|boundary mark|demarcate)\b', 'boundary/limit'),
    (r'\b(wash|clean|rinse|launder|bathe|scrub|cleanse|purify)\b', 'wash/clean'),
    (r'\b(fragrance|scent|perfume|aromatic|sweet-smelling|odor|aroma)\b', 'fragrance/scent'),
    (r'\b(tower|fortress|fort|citadel|castle|rampart|turret|battlement|wall tower)\b', 'tower/fortress'),
    (r'\b(leap|jump|spring|bound|vault|hop|jump)\b', 'leap/movement'),
    (r'\b(scale|scales|scaly|lamella|lamellate|plated|squamous)\b', 'scales'),
    (r'\b(worm|caterpillar|insect|larva|grub|maggot|moth|bug)\b', 'worm/insect'),
    (r'\b(round|circular|globular|sphere|ball|disc|orb|spherical)\b', 'round/circular'),
]

def get_ar_tags(mas):
    tags = set()
    for pat, tag in AR_CONCEPTS:
        if re.search(pat, mas):
            tags.add(tag)
    return tags

def get_en_tags(tg):
    tags = set()
    g = tg.lower()
    for pat, tag in EN_CONCEPTS:
        if re.search(pat, g):
            tags.add(tag)
    return tags

# ─────────────────────────────────────────────────────────────
# DIRECT MEANING MATCH CHECKS
# Returns (score, method, reason) or None
# ─────────────────────────────────────────────────────────────
DIRECT_CHECKS = [
    # Lion
    (r'الأسَد|السَّبُع|أُسامَة', r'\b(lion)\b', 0.8, 'masadiq_direct', 'Arabic أسد=lion directly matches Latin lion'),
    # Bull/ox
    (r'ثَوْر|ذَكَرُ البَقَر|ثِيران', r'\b(bull|ox|bovine|steer)\b', 0.8, 'masadiq_direct', 'Arabic ثور=bull matches Latin bull/ox'),
    # Milk/milking
    (r'اللَّبَن|الحَلَب|يَحلُب|الحَليب', r'\b(milk|milking|dairy)\b', 0.8, 'masadiq_direct', 'Arabic لبن/حلب=milk matches Latin milk'),
    # Snake/serpent
    (r'الحَيَّة|الأفعَى|الثُّعبان|الحنش', r'\b(snake|serpent|viper|adder)\b', 0.8, 'masadiq_direct', 'Arabic حية=snake matches Latin snake/serpent'),
    # Camel
    (r'النّاقة|الجَمَل|الإِبِل|البَعير|الناقه', r'\b(camel)\b', 0.8, 'masadiq_direct', 'Arabic ناقة/جمل=camel matches Latin camel'),
    # Honey/bee
    (r'العَسَل|النَّحل|شَهد', r'\b(honey|bee|wax|comb|mead)\b', 0.8, 'masadiq_direct', 'Arabic عسل=honey matches Latin honey/bee'),
    # Worm/grub/insect
    (r'الدُّودة|دُوَيِّبَّة|حَشَرة|السُّرفة', r'\b(worm|caterpillar|insect|larva|grub|moth|maggot|bug)\b', 0.6, 'masadiq_direct', 'Arabic دودة/حشرة=worm/insect matches Latin insect/worm'),
    # Scales (fish/armor)
    (r'فُلوس|حَراشِف|حُبوب الدِّرع', r'\b(scale|scales|scaly|lamella|lamellate|plated)\b', 0.6, 'masadiq_direct', 'Arabic فلوس/حراشف=scales matches Latin scales/lamella'),
    # Swift (camel/movement)
    (r'السَّريع|سُرعة|سريعة|يُسرِع|العَدَو', r'\b(swift|fast|quick|rapid|speed|fleet|speedy)\b', 0.6, 'masadiq_direct', 'Arabic سريع=swift matches Latin swift/quick'),
    # Small/short
    (r'الصَّغير|القَصير|الحَقير|ضَئيل', r'\b(small|short|little|tiny|diminutive|dwarf|puny|minor)\b', 0.6, 'masadiq_direct', 'Arabic صغير/قصير=small/short matches Latin small/tiny'),
    # Large/great
    (r'العَظيم|الضَّخم|الكَبير', r'\b(great|large|big|huge|massive|enormous|grand)\b', 0.6, 'masadiq_direct', 'Arabic عظيم=great matches Latin great/large'),
    # Tall
    (r'الطَّويل|يَطول', r'\b(tall|long|lengthy|lofty|high|elongate)\b', 0.6, 'masadiq_direct', 'Arabic طويل=tall matches Latin tall/long'),
    # Stupid/foolish
    (r'الأحمَق|الجاهِل|حُمق|سَفاهة', r'\b(fool|foolish|stupid|idiotic|witless|dull|rash|senseless)\b', 0.6, 'masadiq_direct', 'Arabic أحمق=fool matches Latin fool/stupid'),
    # Darkness/black
    (r'الظُّلمة|الظَّلام|الأسْوَد|سَواد|شِدَّة السَّواد', r'\b(dark|darkness|night|black|shadow|obscure)\b', 0.6, 'masadiq_direct', 'Arabic ظلمة/سواد=darkness/black matches Latin dark/black'),
    # Light/bright
    (r'الضَّوء|النُّور|يُضيء|مُضيء', r'\b(light|bright|radiant|luminous|illuminate|glow|shine)\b', 0.6, 'masadiq_direct', 'Arabic ضوء/نور=light matches Latin light/bright'),
    # Adhesion/clinging
    (r'لاصِق|يَلصَق|لُزوق|لازِب|لازِم', r'\b(stick|cling|adhere|adhesive|glue|bond|tacky|cohere|clingy)\b', 0.6, 'masadiq_direct', 'Arabic لازب/لزوق=clinging matches Latin stick/adhere'),
    # Destruction/ruin
    (r'الإِهلاك|الدَّمار|يُهلِك|هَلَك', r'\b(destroy|ruin|devastate|demolish|waste|annihilate)\b', 0.6, 'masadiq_direct', 'Arabic إهلاك/دمار=destruction matches Latin destroy/ruin'),
    # Coercion/overpower
    (r'قَهَرَ|الإِكراه|يَقهَر|يُكرِه', r'\b(force|coerce|compel|constrain|overpower|coercion)\b', 0.6, 'masadiq_direct', 'Arabic قهر=overpower matches Latin force/coerce'),
    # Pouring/flowing
    (r'الصَّبّ|السَّيَلان|يَسيل|انصَبَّ|يَصُبّ', r'\b(pour|flow|gush|stream|trickle|run|flood|drip)\b', 0.6, 'masadiq_direct', 'Arabic صب/سيلان=pouring/flowing matches Latin pour/flow'),
    # Patience/endurance
    (r'يَتَحَمَّل|الصَّبر|الحِلم|يَصبِر|الحِلْم', r'\b(tolerate|endure|bear|patience|suffer|forbear|withstand|put up)\b', 0.6, 'masadiq_direct', 'Arabic صبر/حلم=patience matches Latin tolerate/endure'),
    # Joy/happiness
    (r'الفَرَح|السُّرور|البَهجة', r'\b(joy|happy|glad|merry|cheerful|delight|jolly|playful)\b', 0.6, 'masadiq_direct', 'Arabic فرح/سرور=joy matches Latin joy/happy'),
    # Boasting/strut
    (r'التَّبَختُر|الزَّهو|يَتَبَختَر', r'\b(strut|swagger|boast|prance|parade|sway|arrogant|vain)\b', 0.6, 'masadiq_direct', 'Arabic تبختر=swaggering matches Latin strut/swagger'),
    # Boundary/limit
    (r'الحَدّ|الحُدود|مَعالِم الحُدود', r'\b(boundary|border|limit|frontier|boundary mark)\b', 0.6, 'masadiq_direct', 'Arabic حدود=boundary matches Latin boundary/limit'),
    # Shepherd/pasture
    (r'الرِّعي|المَرعَى|يَرعَى|الراعي', r'\b(graze|pasture|shepherd|herder|tend|herd|flock)\b', 0.6, 'masadiq_direct', 'Arabic رعي/مرعى=pasture matches Latin graze/pasture'),
    # Cutting/severing
    (r'يَقطَع|قَطَعَ|القَطع|قَطيل', r'\b(cut|sever|split|chop|cleave|slice|amputate|lop)\b', 0.6, 'masadiq_direct', 'Arabic قطع=cutting matches Latin cut/sever'),
    # Returning/reversal
    (r'الرُّجوع|يَرجِع|العَودة|يَعود|النُّزوع|حُسن الرُّجوع', r'\b(return|go back|revert|come back|relapse|retreat|reverse)\b', 0.6, 'masadiq_direct', 'Arabic رجوع/نزوع=returning matches Latin return/revert'),
    # Cushion/pillow
    (r'الوِسادة|المِخَدَّة|الوِسادُ', r'\b(cushion|pillow|pad|bolster|seat|headrest)\b', 0.6, 'masadiq_direct', 'Arabic وسادة=cushion matches Latin cushion/pillow'),
    # Round/circular
    (r'المُدَوَّر|تَدوير|كُروي', r'\b(round|circular|globular|sphere|ball|disc|orb)\b', 0.6, 'masadiq_direct', 'Arabic تدوير=round matches Latin round/circular'),
    # Tower/fortress
    (r'البُرج|القَلعة|الحِصن', r'\b(tower|fortress|fort|citadel|castle|rampart|wall tower)\b', 0.6, 'masadiq_direct', 'Arabic برج/قلعة=tower matches Latin tower/fortress'),
    # Garment/robe
    (r'الثَّوب|الرِّداء|الكِساء|اللِّباس', r'\b(garment|robe|cloak|mantle|vestment|clothing|dress|drape)\b', 0.6, 'masadiq_direct', 'Arabic ثوب/رداء=garment matches Latin garment/robe'),
    # Silk
    (r'الإِبريسَم|الحَرير|القَزّ|الدِّيباج', r'\b(silk|satin|silky|fine fabric|brocade)\b', 0.6, 'masadiq_direct', 'Arabic إبريسم/حرير=silk matches Latin silk'),
    # Boxwood (whitish wood)
    (r'شَجَر.*البَقس|البَقس.*شَجَر|الشِّمشاذ', r'\b(white|whiten|pale|boxwood|privet)\b', 0.4, 'mafahim_deep', 'Arabic بقس=boxwood (whitish wood) has whiteness link to Latin whiten/white, weak'),
    # Linen/plant fiber
    (r'الكَتّان', r'\b(linen|flax|fiber)\b', 0.8, 'masadiq_direct', 'Arabic كتان=linen directly matches Latin linen/flax'),
    # Stilts/elevated walk
    (r'التَّبَختُر|التَّكَبُّر في المَشي', r'\b(stilt|stilts|elevated|high walk)\b', 0.6, 'masadiq_direct', 'Arabic تبختر=swaggering gait on elevated footing matches stilts'),
    # Covering/wrapping
    (r'تَغطية|يُغَطّي|يَستُر|غِطاء|سَتر', r'\b(cover|covering|wrap|veil|conceal|clothe|shroud)\b', 0.6, 'masadiq_direct', 'Arabic تغطية/غطاء=covering matches Latin covering/wrap'),
    # Softness/leniency
    (r'السُّهولة|اللِّين|يَلين|لَيِّن', r'\b(soft|smooth|gentle|mild|supple|pliable|flexible)\b', 0.6, 'masadiq_direct', 'Arabic لين/سهولة=softness matches Latin soft/smooth'),
    # Rolling/tumbling down
    (r'تَتابَع في حُدور|تَدَحرَج|تَدَحرُج', r'\b(roll|tumble|revolve|rotation|tumbling)\b', 0.4, 'mafahim_deep', 'Arabic تدحرج=rolling/tumbling has conceptual link, weak'),
    # Swallowing/devouring
    (r'يَبلَع|الابتِلاع|ازدِراد|يَزدَرِد', r'\b(swallow|devour|gulp|engulf|absorb|ingest)\b', 0.6, 'masadiq_direct', 'Arabic ابتلاع=swallowing matches Latin swallow/devour'),
    # Honey bee hive
    (r'جَماعة النَّحل|النَّحل|عَسَل', r'\b(bee|hive|swarm|apiary|apian)\b', 0.6, 'masadiq_direct', 'Arabic جماعة النحل=bee swarm matches Latin bee/hive'),
    # Hardship/difficulty
    (r'الشِّدَّة|الجَدب|القَحط|الضِّيق', r'\b(hardship|harsh|difficult|severe|distress|harsh|arid|dire)\b', 0.6, 'masadiq_direct', 'Arabic شدة/جدب=hardship/scarcity matches Latin harsh/severe'),
    # Softness of character
    (r'سُهولة الخُلق|لِين الجانب', r'\b(gentle|amiable|good-natured|easy)\b', 0.4, 'mafahim_deep', 'Arabic سهولة الخلق=gentle nature plausibly links to Latin gentle/amiable'),
    # Running/leaping
    (r'الوَثب|يَثِب|القَفز|يَقفِز', r'\b(leap|jump|spring|bound|vault|hop)\b', 0.6, 'masadiq_direct', 'Arabic وثب=leap/jump matches Latin leap/jump'),
    # Lean/thin (poorly nourished)
    (r'المَهزول|يَهزُل|الهُزال|شَحيح اللَّحم', r'\b(lean|thin|emaciated|scrawny|gaunt|wasted|meager)\b', 0.6, 'masadiq_direct', 'Arabic مهزول=lean/emaciated matches Latin lean/thin'),
    # Washing a corpse
    (r'يَغسِل.*ميِّت|غُسل المَيِّت', r'\b(wash.*corpse|corpse.*wash|funerary|funeral.*prep|prepare.*dead)\b', 0.6, 'masadiq_direct', 'Arabic غسل الميت=washing corpse matches Latin funerary washing'),
    # Mixed fighting/raucous
    (r'التَّرَدُّد|في الباطِل|لَعِب الفَرَس', r'\b(wanton|petulant|licentious|riotous|frolic)\b', 0.2, 'mafahim_deep', 'Arabic ترددة في الباطل=idle wantonness has weak link to Latin wanton/licentious'),
    # Solidarity/standing together
    (r'يَتَضامن|تَضامن|الوِفاق|التَّوَحُّد', r'\b(solidarity|unity|togetherness|cohesion|union)\b', 0.6, 'masadiq_direct', 'Arabic تضامن=solidarity matches Latin solidarity'),
    # Playful/sportive
    (r'لَعِب|يَلعَب|مَرِح|اللَّعِب', r'\b(play|playful|sport|frolic|game|amusement|fun|wanton)\b', 0.6, 'masadiq_direct', 'Arabic لعب=play matches Latin playful/sport'),
    # Eating/devouring
    (r'يَأكُل|الأكل|يَلتَهِم|مَأكول', r'\b(eat|devour|consume|gobble|feed|dine)\b', 0.6, 'masadiq_direct', 'Arabic أكل=eating matches Latin eat/devour'),
    # Bearing/producing offshoots
    (r'فِراخ النَّخل|فِراخ الزَّرع|يُفرِّخ', r'\b(offshoot|shoot|sprout|sapling|tillering)\b', 0.6, 'masadiq_direct', 'Arabic فراخ النخل/الزرع=crop offshoots matches Latin shoot/sprout'),
    # Partridge/bird
    (r'القَبَج|الحُجَل|الدُّرَّاج', r'\b(partridge|francolin|grouse|quail|game bird)\b', 0.6, 'masadiq_direct', 'Arabic قبج/حجل=partridge matches Latin partridge/game bird'),
    # Warmth/heat
    (r'الحَرارة|الدِّفء|دافِئ|سُخونة', r'\b(warm|warmth|heat|tepid|calorie|thermal)\b', 0.6, 'masadiq_direct', 'Arabic حرارة=warmth matches Latin warm/heat'),
    # Blood/hemorrhage
    (r'الدَّم|يَنزِف|دَمَوي', r'\b(blood|bleed|hemorrhage|sanguine|phlebotomy|bloodletting)\b', 0.6, 'masadiq_direct', 'Arabic دم=blood matches Latin blood/bleed'),
    # Rolling ball/sphere
    (r'كُرة|كُروي|تَدحرَج', r'\b(ball|sphere|orb|globule|round|globular)\b', 0.6, 'masadiq_direct', 'Arabic كرة=ball matches Latin ball/sphere/orb'),
    # Lineage/descent
    (r'النَّسَب|الأصل|الحَسَب|سَلالة', r'\b(lineage|descent|ancestry|pedigree|genealogy|born of|progeny)\b', 0.6, 'masadiq_direct', 'Arabic نسب/حسب=lineage matches Latin lineage/descent'),
    # Donkey
    (r'الحِمار|حِمارة', r'\b(donkey|ass|mule|asinine)\b', 0.8, 'masadiq_direct', 'Arabic حمار=donkey matches Latin donkey/ass'),
    # Locust
    (r'الجَراد|الجَرادة', r'\b(locust|grasshopper|cricket)\b', 0.8, 'masadiq_direct', 'Arabic جراد=locust matches Latin locust'),
    # Dew/moisture
    (r'النَّدى|النَّديّ|رَطوبة', r'\b(dew|moisture|moist|damp|humid|wet)\b', 0.6, 'masadiq_direct', 'Arabic ندى=dew/moisture matches Latin dew/moisture'),
    # Straight leaves
    (r'وَرَق.*خَطِّي|مُستَقيم', r'\b(linear leaf|straight leaf|narrow leaf)\b', 0.2, 'mafahim_deep', 'Arabic leaf descriptions weakly link to botanical terms'),
    # Colocynth/bitter plant
    (r'الحَنظَل|مُرّ الطَّعم', r'\b(bitter|colocynth|gourd|purgative|cathartic)\b', 0.6, 'masadiq_direct', 'Arabic حنظل=colocynth matches Latin bitter/purgative plant'),
    # Dung/excrement
    (r'الزَّبَل|البَعَر|الرَّوث|فَضَلات', r'\b(dung|excrement|manure|feces|droppings)\b', 0.6, 'masadiq_direct', 'Arabic زبل/بعر=dung matches Latin dung/excrement'),
]

def check_direct(mas, tg):
    tg_l = tg.lower()
    for ar_pat, en_pat, score, method, reason in DIRECT_CHECKS:
        if re.search(ar_pat, mas) and re.search(en_pat, tg_l):
            return (score, method, reason)
    return None

# ─────────────────────────────────────────────────────────────
# PAIR-LEVEL OVERRIDES (manual review of specific pairs)
# ─────────────────────────────────────────────────────────────
OVERRIDES = {
    # Chunk 090
    ('الحبتك', 'alphabetum'): (0.0, 'masadiq_direct', 'حبتك=small-bodied; alphabet; unrelated'),
    ('الحبتك', 'male habitus'): (0.0, 'masadiq_direct', 'حبتك=small-bodied; male habitus=in poor condition; both mean weak/poor but different registers'),
    ('الحلا', 'solidarietas'): (0.0, 'masadiq_direct', 'حلى=jewelry/sweetness; solidarity; unrelated'),
    ('الحلب', 'calendarium'): (0.0, 'masadiq_direct', 'حلب=milking; calendarium=account book; unrelated'),
    ('الحلم', 'alsbergum'): (0.0, 'masadiq_direct', 'حلم=tolerance; hauberk=neck armor; unrelated'),
    ('الحلم', 'ligustrum'): (0.0, 'masadiq_direct', 'حلم=tolerance/dream; ligustrum=privet shrub; unrelated'),
    ('الحلم', 'linearifolius'): (0.0, 'masadiq_direct', 'حلم=tolerance; linear-leaved; unrelated'),
    ('التحرقص', 'clathri'): (0.2, 'mafahim_deep', 'تقبّض=contraction/shrinking; clathri=lattice/grate; both involve constriction, weak'),
    ('التحرقص', 'Eleutherus'): (0.0, 'masadiq_direct', 'تقبّض=contraction; Eleutherus=river proper noun; unrelated'),
    ('الترنوك', 'Claterna'): (0.0, 'masadiq_direct', 'ترنوك=thin/poor; Claterna=town name; proper noun'),
    ('الثري', 'lathyros'): (0.0, 'masadiq_direct', 'ثرى=moist earth/wealth; lathyros=vetchling; unrelated'),
    ('الجرشع', 'falsijurius'): (0.0, 'masadiq_direct', 'جرشع=large-chested animal; falsijurius=perjurer; unrelated'),
    # Chunk 091
    ('نهض', 'contrahendus'): (0.0, 'masadiq_direct', 'نهوض=rising/launching; contrahendus=to be contracted; unrelated'),
    ('الشمطاله', 'blasphematio'): (0.0, 'masadiq_direct', 'شمطالة=meat morsel; blasphematio=censure; unrelated'),
    ('الغرنوق', 'oligochronius'): (0.0, 'masadiq_direct', 'غرنوق=crane/water bird; short-lived; unrelated'),
    ('الهرنصانه', 'oligochronius'): (0.0, 'masadiq_direct', 'هرنصانة=worm (surfa); short-lived; unrelated'),
    ('الهرنصانه', 'Lotharingus'): (0.0, 'masadiq_direct', 'هرنصانة=worm; Lotharingus=proper noun; unrelated'),
    # Chunk 092
    ('الثهمد', 'malthato'): (0.0, 'masadiq_direct', 'ثهمد=large fat (place name context); malthato=gram form; unrelated'),
    ('الثور', 'Waltharius'): (0.0, 'masadiq_direct', 'ثور=bull/agitation; Waltharius=proper name; unrelated'),
    ('الثول', 'Waltharius'): (0.0, 'masadiq_direct', 'ثول=bee swarm/madness; Waltharius=proper name; unrelated'),
    ('الثيتل', 'Lesothum'): (0.0, 'masadiq_direct', 'ثيتل=wild goat; Lesotho=country; unrelated'),
    ('الثيل', 'platyphyllus'): (0.0, 'masadiq_direct', 'ثيل=camel organ/plant; flat-leaved; unrelated'),
    # Chunk 093
    ('الدمور', 'Vladimirus'): (0.0, 'masadiq_direct', 'دمور=destruction; Vladimir=proper name; unrelated'),
    ('الدنفصه', 'Aspledon'): (0.0, 'masadiq_direct', 'دنفصة=weak woman; Aspledon=city name; unrelated'),
    ('الدنقسه', 'caledonius'): (0.0, 'masadiq_direct', 'دنقسة=sowing discord/bowing; Caledonian=Scottish; unrelated'),
    ('الدنقسه', 'Laodicenus'): (0.0, 'masadiq_direct', 'دنقسة=sowing discord; Laodicean=proper noun; unrelated'),
    ('الدهس', 'Philadelphus'): (0.0, 'masadiq_direct', 'دهس=smooth ground; Philadelphus=proper name; unrelated'),
    # Chunk 094
    ('الشذب', 'Elisabeth'): (0.0, 'masadiq_direct', 'شذب=pruning/bark; Elisabeth=proper name; unrelated'),
    ('الشصب', 'blasphemia'): (0.0, 'masadiq_direct', 'شصب=hardship/skinning; blasphemia=blasphemy; unrelated'),
    ('الشطء', 'philosophatus'): (0.0, 'masadiq_direct', 'شطء=crop shoots; philosophatus=gram form; unrelated'),
    ('الشطء', 'philosophator'): (0.0, 'masadiq_direct', 'شطء=crop shoots; philosophator=gram form; unrelated'),
    # Chunk 095
    ('العنبس', 'invulnerabilis'): (0.2, 'mafahim_deep', 'عنبس=lion (fierce); invulnerable; loose link via lion invincibility, very weak'),
    ('الغث', 'oliganthus'): (0.2, 'mafahim_deep', 'غثّ=lean/poor quality; oligo=few/scarce; shared scarcity notion, weak'),
    ('الغثاء', 'oliganthus'): (0.0, 'masadiq_direct', 'غثاء=froth/debris in flood; oliganthus=few-flowered; unrelated'),
    # Chunk 096
    ('الملاذ', 'lamellatus'): (0.0, 'masadiq_direct', 'ملاذ=deceitful flatterer; lamellatus=scaly; unrelated'),
    ('الملث', 'Ultima Thule'): (0.0, 'masadiq_direct', 'ملث=beginning of darkness; ultima Thule=proper noun; unrelated'),
    ('الملخ', 'legumlator'): (0.0, 'masadiq_direct', 'ملخ=swift movement/lust; legumlator=legislator; unrelated'),
    ('الملخ', 'glomellum'): (0.0, 'masadiq_direct', 'ملخ=swift movement; glomellum=ball of yarn; unrelated'),
    # Chunk 097
    ('دربح', 'desorbeo'): (0.2, 'mafahim_deep', 'دربح=bow down/bend low; swallow down; both express downward motion, weak'),
    ('درحبت', 'deprehendo'): (0.0, 'masadiq_direct', 'درحبت=camel nurturing calf; deprehendo=seize/catch; unrelated'),
    ('درنجق', 'draconigena'): (0.0, 'masadiq_direct', 'درنجق=place names; draconigena=dragon-born; unrelated'),
    ('درنجق', 'quadraginta'): (0.0, 'masadiq_direct', 'درنجق=village names; quadraginta=forty; unrelated'),
    ('دحرجه', 'Adricharius'): (0.0, 'masadiq_direct', 'دحرجة=rolling/tumbling; Adricharius=proper name; unrelated'),
    # Chunk 098
    ('قسره', 'equester'): (0.0, 'masadiq_direct', 'قسر=coerce; equester=equestrian; unrelated'),
    ('قطربل', 'praeloquitor'): (0.0, 'masadiq_direct', 'قطربل=place name; praeloquitor=gram form; unrelated'),
    ('قطله', 'aquatilis'): (0.0, 'masadiq_direct', 'قطل=cut/sever; aquatilis=aquatic; unrelated'),
    ('قعطره', 'sequitor'): (0.0, 'masadiq_direct', 'قعطر=throw down/bind; sequitor=gram form; unrelated'),
    ('قعطره', 'aequaturus'): (0.0, 'masadiq_direct', 'قعطر=throw down; aequaturus=about to equalize; unrelated'),
    # Chunk 099
    ('اللزوب', 'lapis lazuli'): (0.2, 'mafahim_deep', 'لزوب=adhesion/clinging (لازب); lapis lazuli=blue stone; phonetic laz-laz overlap, semantics diverge'),
    # Chunk 100
    ('الحظ', 'deleth'): (0.0, 'masadiq_direct', 'حظ=fortune/luck; deleth=Hebrew letter dalet; unrelated'),
    ('الحفا', 'alpha'): (0.0, 'masadiq_direct', 'حفا=bare-footed; alpha=Greek letter; unrelated'),
    ('الحقل', 'alcohol'): (0.0, 'masadiq_direct', 'حقل=cultivated field; alcohol=kohl pigment; unrelated'),
    ('الحقط', 'Goliath'): (0.0, 'masadiq_direct', 'حقط=light-bodied/active; Goliath=proper name; unrelated'),
    # Tag-overlap false positives
    # قتله = to kill/mix drink with water; aquatilis = aquatic -> water senses diverge
    ('قتله', 'aquatilis'): (0.0, 'masadiq_direct', 'قتل=to kill; also: mix wine with water; aquatilis=aquatic; water senses diverge, unrelated'),
    # ندله = grab/transfer bread/dates; sandala = type of white grain
    ('ندله', 'sandala'): (0.4, 'masadiq_direct', 'ندل=grab handfuls of bread/dates; sandala=white grain; both involve handling grain/bread food'),
    # نقره = to strike/peck/pursue; insequor = to follow/pursue/attack -> genuine pursuit link
    ('نقره', 'insequor'): (0.6, 'masadiq_direct', 'نقر=to strike/peck/pursue; insequor=follow/pursue/attack; both involve striking pursuit'),
    # الاداف = penis/ear; lapido = to stone -> no connection
    ('الاداف', 'lapido'): (0.0, 'masadiq_direct', 'أداف=penis/ear; lapido=to stone; unrelated'),
    # الاداف = penis/ear; livedo = blueness -> no connection
    ('الاداف', 'livedo'): (0.0, 'masadiq_direct', 'أداف=penis/ear; livedo=blueness; unrelated'),
    # الاراك = toothbrush tree (Salvadora persica) / vegetation; larix = larch tree -> both trees
    ('الاراك', 'larix'): (0.6, 'masadiq_direct', 'أراك=toothbrush-tree (Salvadora persica); larix=larch tree; both are specific named trees'),
    # الاراك = vegetation/miswak tree; large = vocative of largus -> grammatical
    ('الاراك', 'large'): (0.0, 'masadiq_direct', 'أراك=toothbrush tree; large=gram form of largus; unrelated'),
    # الاراك / eloquor = to speak out -> no connection
    ('الاراك', 'eloquor'): (0.0, 'masadiq_direct', 'أراك=miswak tree; eloquor=speak out; unrelated'),
    # البزاق = spittle/saliva; albesco = become white -> no
    ('البزاق', 'albesco'): (0.0, 'masadiq_direct', 'بزاق=spittle/saliva; albesco=become white; unrelated'),
    # البزاق = spittle; Luca bos = elephant -> no
    ('البزاق', 'Luca bos'): (0.0, 'masadiq_direct', 'بزاق=spittle; Luca bos=elephant; unrelated'),
    # الدفء = warmth; lapido = to stone -> no
    ('الدفء', 'lapido'): (0.0, 'masadiq_direct', 'دفء=warmth; lapido=to stone; unrelated'),
    # الدفء = warmth; livedo = blueness -> no
    ('الدفء', 'livedo'): (0.0, 'masadiq_direct', 'دفء=warmth; livedo=blueness; unrelated'),
    # الرق = thin skin/parchment; larix = larch -> no
    ('الرق', 'larix'): (0.0, 'masadiq_direct', 'رق=thin parchment/thin skin; larix=larch tree; unrelated'),
    # الرق = thin skin; large = gram form
    ('الرق', 'large'): (0.0, 'masadiq_direct', 'رق=thin parchment; large=gram form; unrelated'),
    # الريف = fertile cultivated land; refloreo = to bloom again -> both vegetation flourishing
    ('الريف', 'refloreo'): (0.4, 'masadiq_direct', 'ريف=fertile land with crops/vegetation; refloreo=bloom again; both involve vegetative flourishing'),
    # الريف = fertile land; relabor = slide back -> no
    ('الريف', 'relabor'): (0.0, 'masadiq_direct', 'ريف=fertile cultivated land; relabor=slide back/relapse; unrelated'),
    # الريف = fertile land; pugilor = boxer -> no
    ('الريف', 'pugilor'): (0.0, 'masadiq_direct', 'ريف=fertile land; pugilor=boxer; unrelated'),
    # ندله / indoles = innate quality -> no
    ('ندله', 'indoles'): (0.0, 'masadiq_direct', 'ندل=grab handfuls of food; indoles=innate quality; unrelated'),
    # Chunk 101 - اقن = stone house; quinque = five
    ('اقن', 'quinque'): (0.0, 'masadiq_direct', 'اقنة=stone house; quinque=five; unrelated'),
    ('اقن', 'quandiu'): (0.0, 'masadiq_direct', 'اقنة=stone house; quandiu=for how long; unrelated'),
    ('الاب', 'ullibi'): (0.0, 'masadiq_direct', 'الأب=pasture/grass; ullibi=anywhere; unrelated'),
    ('الاب', 'exalbo'): (0.0, 'masadiq_direct', 'الأب=pasture/grass; exalbo=make white; unrelated'),
    ('الاباءه', 'Helbo'): (0.0, 'masadiq_direct', 'أباءة=reed/cane; Helbo=island name; proper noun'),
    ('ابم', 'bombio'): (0.0, 'masadiq_direct', 'أبم=place name; bombio=to buzz; unrelated'),
    ('ابم', 'bimus'): (0.0, 'masadiq_direct', 'أبم=place name; bimus=two-year-old; unrelated'),
    ('ابن', 'obvenio'): (0.0, 'masadiq_direct', 'اين=exhaustion/snake; obvenio=meet face-to-face; unrelated'),
    ('ابن', 'obnubo'): (0.0, 'masadiq_direct', 'اين=exhaustion; obnubo=veil/conceal; unrelated'),
    # Chunk 102
    ('البعو', 'Helbo'): (0.0, 'masadiq_direct', 'بعو=crime/borrowed horse; Helbo=proper noun; unrelated'),
    ('البقس', 'albesco'): (0.2, 'mafahim_deep', 'بقس=boxwood (white-wood shrub); albesco=become white; whiteness link, weak'),
    ('البقس', 'Luca bos'): (0.0, 'masadiq_direct', 'بقس=boxwood; Luca bos=elephant (Lucanian cow); unrelated'),
    ('البقس', 'Calbis'): (0.0, 'masadiq_direct', 'بقس=boxwood; Calbis=river; proper noun'),
    # Chunk 103
    ('التملول', 'velamentum'): (0.2, 'mafahim_deep', 'تملول=spring plant; velamentum=covering; plant-as-covering mafahim link, weak'),
    ('التهبرس', 'colobathra'): (0.6, 'masadiq_direct', 'تهبرس=swaggering strut; colobathra=stilts; elevated swaggering gait connection'),
    ('التهبرس', 'Waltharius'): (0.0, 'masadiq_direct', 'تهبرس=swagger; Waltharius=proper name; unrelated'),
    ('التهبرس', 'Spalathra'): (0.0, 'masadiq_direct', 'تهبرس=swagger; Spalathra=town name; proper noun'),
    ('التو', 'avolato'): (0.0, 'masadiq_direct', 'التو=single rope/present moment; avolato=gram form; unrelated'),
    # Chunk 104
    ('الرعي', 'lyra'): (0.0, 'masadiq_direct', 'رعي=grazing/pasture; lyra=lyre; unrelated'),
    ('الرعيق', 'hariolor'): (0.0, 'masadiq_direct', 'رعيق=belly-sound of running animal; hariolor=prophesy; unrelated'),
    ('الرعيق', 'lyrica'): (0.2, 'mafahim_deep', 'رعيق=sound from running animal belly; lyrica=lyric (song); both involve sound, very weak'),
    ('الرعو', 'Elaver'): (0.0, 'masadiq_direct', 'رعو=turning from foolishness; Elaver=river name; proper noun'),
    # Chunk 105
    ('السح', 'exilis'): (0.0, 'masadiq_direct', 'سح=pouring/flowing; exilis=thin/lean; unrelated'),
    ('السح', 'Saleius'): (0.0, 'masadiq_direct', 'سح=pouring; Saleius=proper noun; unrelated'),
    ('السح', 'Lamse'): (0.0, 'masadiq_direct', 'سح=pouring; Lamse=island name; proper noun'),
    # Chunk 106
    ('الدكر', 'lucidior'): (0.0, 'masadiq_direct', 'دكر=remembrance dialect; lucidior=comparative of bright; unrelated'),
    ('الدكر', 'liquidior'): (0.0, 'masadiq_direct', 'دكر=remembrance; liquidior=more liquid; unrelated'),
    ('الدكس', 'liquidius'): (0.0, 'masadiq_direct', 'دوكس=lion/large flock; liquidius=gram form; unrelated'),
    # Chunk 107
    ('الديك', 'occludo'): (0.0, 'masadiq_direct', 'ديك=rooster; occludo=close/shut; unrelated'),
    ('الرعي', 'lyra'): (0.0, 'masadiq_direct', 'رعي=pasture; lyra=lyre; unrelated'),
    ('الرعيق', 'lyrica'): (0.2, 'mafahim_deep', 'رعيق=belly sound; lyrica=lyric; sound connection very weak'),
    ('الحجل', 'Oclahoma'): (0.0, 'masadiq_direct', 'حجل=partridge; Oklahoma=US state; unrelated'),
    ('الفرضم', 'multifariam'): (0.0, 'masadiq_direct', 'فرضم=old large ewe; multifariam=in many ways; unrelated'),
    ('السور', 'alvarius'): (0.0, 'masadiq_direct', 'سؤر=remainder; alvarius=of the belly; unrelated'),
    ('الاذط', 'altitudo'): (0.0, 'masadiq_direct', 'اذط=crooked jaw; altitudo=height; unrelated'),
    ('المسمقر', 'calamarius'): (0.0, 'masadiq_direct', 'مسمقر=extremely hot; calamarius=writing reed; unrelated'),
    ('الدلاث', 'callidulus'): (0.0, 'masadiq_direct', 'دلاث=swift camel; callidulus=cunning/sly; unrelated'),
    ('الفعل', 'flabellifolius'): (0.0, 'masadiq_direct', 'فعل=action; fan-shaped leaves; unrelated'),
    ('برفطي', 'berfredus'): (0.4, 'masadiq_direct', 'برفطى=village near river fortress; berfredus=wall tower; place-fortress semantic link plausible'),
    ('الهنداز', 'delhiensis'): (0.2, 'mafahim_deep', 'هنداز=measure/boundary (Arabized Persian andaze); delhiensis=of Delhi; shared Indo-Persian substrate'),
    ('النسطوريه', 'lanista'): (0.0, 'masadiq_direct', 'النسطورية=Nestorian Christian sect; lanista=gladiator manager; unrelated'),
    ('الحنظل', 'lithuanus'): (0.0, 'masadiq_direct', 'حنظل=colocynth gourd; Lithuanian; unrelated'),
    ('اللغيف', 'pollingo'): (0.2, 'mafahim_deep', 'لغيف=parasite eating with bandits/guarding; pollingo=wash/prepare corpse; marginal service roles, very weak'),
    ('الركم', 'lacrima'): (0.0, 'masadiq_direct', 'ركم=piling/heaping; lacrima=tear from eye; unrelated'),
    ('الريب', 'relabor'): (0.2, 'mafahim_deep', 'ريب=suspicion/returning doubt; relabor=relapse/slide back; both involve reversal/doubt'),
    ('شربق', 'sphragis'): (0.0, 'masadiq_direct', 'شربق=tearing apart; sphragis=seal-stone; unrelated'),
    ('الميحار', 'Halmyris'): (0.0, 'masadiq_direct', 'ميحار=polo mallet; Halmyris=salt lake; proper noun'),
    ('النمرق', 'gallinarium'): (0.0, 'masadiq_direct', 'نمرق=small cushion/saddle cloth; gallinarium=henhouse; unrelated'),
    ('السلغد', 'legislatio'): (0.0, 'masadiq_direct', 'سلغد=fool/weak; legislatio=law-giving; unrelated'),
    ('الحدقله', 'Lichades'): (0.0, 'masadiq_direct', 'حدقلة=rotating eyes; Lichades=island group; proper noun'),
    ('الدقع', 'Gildo'): (0.0, 'masadiq_direct', 'دقع=contentment with little; Gildo=proper name; unrelated'),
    ('الارفي', 'pugilor'): (0.0, 'masadiq_direct', 'أرفي=large-eared droopy; pugilor=boxer; unrelated'),
    ('خاس', 'kagoshimensis'): (0.0, 'masadiq_direct', 'خاس=betray/decay; kagoshimensis=of Kagoshima; unrelated'),
    ('الحشل', 'delhiensis'): (0.0, 'masadiq_direct', 'حشل=dregs/mean; delhiensis=of Delhi; unrelated'),
    ('الشطس', 'Lacus Asphaltites'): (0.0, 'masadiq_direct', 'شطس=cunning/clever; Lacus Asphaltites=Dead Sea; proper noun'),
    ('الشلط', 'Lacus Asphaltites'): (0.0, 'masadiq_direct', 'شلط=long arrow/knife; Dead Sea; proper noun unrelated'),
    ('الصمكيك', 'Clysma'): (0.0, 'masadiq_direct', 'صمكيك=rash idiot; Clysma=port city; proper noun'),
    ('الطلحام', 'Ultima Thule'): (0.0, 'masadiq_direct', 'طلحام=place name; ultima Thule=proper noun; unrelated'),
    ('الطلمه', 'Ultima Thule'): (0.0, 'masadiq_direct', 'طلمة=flatbread; ultima Thule; unrelated'),
    ('الهلدم', 'Ultima Thule'): (0.0, 'masadiq_direct', 'هلدم=patched cloak; ultima Thule; unrelated'),
    ('المطمه', 'Ultima Thule'): (0.0, 'masadiq_direct', 'مطمة=elongated; ultima Thule; unrelated'),
    ('الملث', 'Ultima Thule'): (0.0, 'masadiq_direct', 'ملث=beginning of darkness; ultima Thule; proper noun'),
    ('الهرث', 'Telethrius'): (0.0, 'masadiq_direct', 'هرث=old garment; Telethrius=mountain name; proper noun'),
    ('الهرطال', 'Telethrius'): (0.0, 'masadiq_direct', 'هرطال=tall person; Telethrius=mountain name; proper noun'),
    ('الحرث', 'Telethrius'): (0.0, 'masadiq_direct', 'حرث=plowing/earning; Telethrius=mountain name; proper noun'),
    ('الاثفيه', 'Eblythaei'): (0.0, 'masadiq_direct', 'أثفية=tripod stone; Eblythaei=mountain range proper noun; unrelated'),
    ('البرثن', 'alburnus'): (0.0, 'masadiq_direct', 'برثن=claw/palm; alburnus=white fish; unrelated'),
    ('البرزين', 'alburnus'): (0.0, 'masadiq_direct', 'برزين=vessel from palm-bark; alburnus=white fish; unrelated'),
    ('البعثط', 'phlebotomia'): (0.4, 'mafahim_deep', 'بعثط=belly-button/anus area; phlebotomia=bloodletting; both involve body opening and fluid, weak'),
    ('الترفه', 'heliotropium'): (0.0, 'masadiq_direct', 'ترفة=luxury/fine food/elegant thing; heliotrope=plant/stone; unrelated'),
    ('الحتفل', 'alphabetum'): (0.0, 'masadiq_direct', 'حتفل=sediment in broth; alphabet; unrelated'),
    ('الحربش', 'sulphur'): (0.0, 'masadiq_direct', 'حربش=snake with rough scales; sulphur=sulfur; unrelated'),
    ('الحرشف', 'sulphur'): (0.0, 'masadiq_direct', 'حرشف=fish scales/armor rings; sulphur=sulfur; unrelated'),
    ('الفرح', 'sulfur'): (0.0, 'masadiq_direct', 'فرح=joy/happiness; sulfur=sulfur; unrelated'),
    ('الحلجز', 'alcoholicus'): (0.0, 'masadiq_direct', 'الجلحز=unrelated root; alcoholicus=alcoholic; coincidental'),
    ('الحلقه', 'alcoholicus'): (0.0, 'masadiq_direct', 'حلقة=circle/ring; alcoholicus=alcoholic; unrelated'),
    ('الحلكه', 'alcoholicus'): (0.0, 'masadiq_direct', 'حلكة=extreme blackness; alcoholicus; unrelated'),
    ('الهلقس', 'alcoholicus'): (0.0, 'masadiq_direct', 'هلقس=extreme hunger; alcoholicus; unrelated'),
    ('الهلكس', 'alcoholicus'): (0.0, 'masadiq_direct', 'هلكس=low character; alcoholicus; unrelated'),
    ('الحشك', 'Gislaharius'): (0.0, 'masadiq_direct', 'حشك=milk urgency in udder; Gislaharius=proper name; unrelated'),
    ('الطلسم', 'talisman'): (0.95, 'masadiq_direct', 'طلسم=talisman/magical inscription; talisman=talisman; direct Arabic loanword to Latin/English'),
    ('ترياض', 'thyreohyoides'): (0.0, 'masadiq_direct', 'تِرياض=female proper name; thyreohyoides=anatomical term; unrelated'),
    ('بربح', 'absorbeo'): (0.0, 'masadiq_direct', 'بربح=play game; absorbeo=swallow/devour; unrelated'),
    ('بسبه', 'absorbeo'): (0.0, 'masadiq_direct', 'بسبة=village name; absorbeo=swallow; proper noun'),
    ('الحجل', 'Oclahoma'): (0.0, 'masadiq_direct', 'حجل=partridge; Oklahoma=state; unrelated'),
    ('الصعمور', 'virilissime'): (0.0, 'masadiq_direct', 'صعمور=waterwheel bucket; virilissime=gram form; unrelated'),
    ('العصمور', 'virilissime'): (0.0, 'masadiq_direct', 'عصمور=waterwheel; virilissime=gram form; unrelated'),
    ('القداحس', 'liquidissime'): (0.0, 'masadiq_direct', 'قداحس=lion/brave; liquidissime=gram form; unrelated'),
    ('القدح', 'liquidius'): (0.0, 'masadiq_direct', 'قدح=arrow/cup; liquidius=gram form; unrelated'),
    ('القضاعه', 'liquidius'): (0.0, 'masadiq_direct', 'قضاعة=otter/flour dust; liquidius=gram form; unrelated'),
    ('القنيل', 'delinquentia'): (0.0, 'masadiq_direct', 'قنئل=elephant neck/short woman; delinquentia=gram form; unrelated'),
    ('الدمقس', 'liquidissime'): (0.0, 'masadiq_direct', 'دمقس=silk; liquidissime=gram form of liquidissimus; unrelated'),
    ('الدمقص', 'liquidissime'): (0.0, 'masadiq_direct', 'دمقص=raw silk; liquidissime=gram form; unrelated'),
    ('السنبله', 'pulsans'): (0.0, 'masadiq_direct', 'سنبلة=grain ear/Virgo constellation; pulsans=striking/beating; unrelated'),
    ('السرادق', 'lustricus'): (0.0, 'masadiq_direct', 'سرادق=tent canopy; lustricus=purificatory; unrelated'),
    ('اللغن', 'allegandus'): (0.0, 'masadiq_direct', 'لغن=youth/ear membrane; allegandus=to be delegated; unrelated'),
    ('العسقفه', 'falsiloquium'): (0.0, 'masadiq_direct', 'عسقفة=wanting to cry/craving; falsiloquium=false speaking; unrelated'),
    ('القسود', 'dulciloquus'): (0.0, 'masadiq_direct', 'قسود=thick-necked/powerful; dulciloquus=speaking sweetly; unrelated'),
    ('القسود', 'doctiloquus'): (0.0, 'masadiq_direct', 'قسود=thick-necked; doctiloquus=speaking learnedly; unrelated'),
    ('القشوان', 'inaniloquus'): (0.0, 'masadiq_direct', 'قشوان=thin-fleshed man; inaniloquus=talking vainly; unrelated'),
    ('القعسري', 'largiloquus'): (0.0, 'masadiq_direct', 'قعسري=large/strong/hand-mill stick; largiloquus=talkative; unrelated'),
    ('الرغس', 'largiloquus'): (0.0, 'masadiq_direct', 'رغس=blessing/prosperity; largiloquus=talkative; unrelated'),
    ('الزمح', 'eleozomus'): (0.0, 'masadiq_direct', 'زمح=mean/short/black; seasoned with oil; unrelated'),
    ('الزمعه', 'eleozomus'): (0.0, 'masadiq_direct', 'زمعة=extra digit on animal; seasoned with oil; unrelated'),
    ('الزمه', 'eleozomus'): (0.0, 'masadiq_direct', 'زمة=binding together; seasoned with oil; unrelated'),
    ('السبد', 'lascivibundus'): (0.0, 'masadiq_direct', 'سبد=shaving/wolf/clever one; lascivibundus=wanton; unrelated'),
    ('السدفه', 'falsidicus'): (0.0, 'masadiq_direct', 'سدفة=darkness/light (antonymic); falsidicus=false-speaking; unrelated'),
    ('الصعمور', 'virilissime'): (0.0, 'masadiq_direct', 'صعمور=waterwheel bucket; gram form; unrelated'),
    ('دحرجه', 'Adricharius'): (0.0, 'masadiq_direct', 'دحرجة=rolling; Adricharius=proper name; unrelated'),
    ('درنجق', 'quadragenus'): (0.0, 'masadiq_direct', 'درنجق=village; quadragenus=forty each; unrelated'),
    ('العيده', 'Lydus'): (0.0, 'masadiq_direct', 'عيدة=bad character; Lydus=proper name; unrelated'),
}

def make_result(ar, tl, score, method, reason):
    return {
        "source_lemma": ar,
        "target_lemma": tl,
        "semantic_score": round(score, 2),
        "reasoning": reason[:200],
        "method": method,
        "lang_pair": "ara-lat",
        "model": "sonnet-phase1-lat"
    }

def score_pair(p):
    ar = p['arabic_root']
    tl = p['target_lemma']
    mas = p.get('masadiq_gloss', '')
    tg = p.get('target_gloss', '')

    # 1. Check specific overrides
    key = (ar, tl)
    if key in OVERRIDES:
        sc, meth, reason = OVERRIDES[key]
        return make_result(ar, tl, sc, meth, reason)

    # 2. Grammatical/inflected forms -> 0.0
    tcat = classify_target(tg)
    if tcat == 'gram':
        return make_result(ar, tl, 0.0, 'masadiq_direct',
            f"Grammatical form: '{tg[:60]}'; no semantic content to compare")

    # 3. Proper noun -> 0.0
    if tcat == 'proper':
        return make_result(ar, tl, 0.0, 'masadiq_direct',
            f"Proper noun/place/name: '{tg[:60]}'; Arabic root meaning not compared")

    # 4. Direct meaning check
    dm = check_direct(mas, tg)
    if dm:
        sc, meth, reason = dm
        return make_result(ar, tl, sc, meth, reason)

    # 5. Semantic tag overlap
    ar_tags = get_ar_tags(mas)
    en_tags = get_en_tags(tg)
    overlap = ar_tags & en_tags

    if not overlap:
        # No overlap at all
        return make_result(ar, tl, 0.0, 'masadiq_direct',
            f"No semantic overlap. AR: {strip_ar_vowels(mas[:50])} | LAT: {tg[:50]}")

    n = len(overlap)
    tag_sample = ', '.join(list(overlap)[:2])

    # Assess quality
    strong_tags = {'water/flow', 'fire/heat', 'strike/weapon/war', 'bird/flight', 'fish',
                   'animal/beast', 'plant/vegetation', 'earth/stone/mountain', 'house/building',
                   'king/ruler', 'food/eating', 'metal/gold', 'livestock/cattle',
                   'blood/wound/pain', 'cloth/garment', 'disease/poison', 'silk/fabric',
                   'worm/insect', 'scales', 'sea/river'}
    weak_tags = {'movement/speed', 'sleep/rest', 'speech/voice', 'small/short/weak',
                 'large/tall/strong', 'hardship/scarcity', 'kin/tribe', 'darkness/black',
                 'light/sun', 'flow/pour', 'sound/noise', 'knowledge/wisdom',
                 'blessing/wealth', 'joy/happiness', 'grief/sorrow', 'cut/sever',
                 'return/revert', 'cushion/rest', 'adhesion/sticky', 'strut/swagger',
                 'patience/endurance', 'boundary/limit', 'wash/clean', 'fragrance/scent',
                 'tower/fortress', 'leap/movement', 'round/circular', 'foolishness'}

    strong_overlap = overlap & strong_tags
    weak_overlap = overlap & weak_tags

    if strong_overlap and n >= 2:
        return make_result(ar, tl, 0.4, 'combined',
            f"Multi-domain match ({n} tags): {tag_sample}")
    elif strong_overlap and n == 1:
        return make_result(ar, tl, 0.4, 'combined',
            f"Domain match: {tag_sample}")
    elif weak_overlap:
        return make_result(ar, tl, 0.2, 'mafahim_deep',
            f"Weak domain link: {tag_sample}")
    else:
        return make_result(ar, tl, 0.2, 'mafahim_deep',
            f"Faint shared domain: {tag_sample}")

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
chunks = ['lat_new_{:03d}.jsonl'.format(n) for n in range(90, 108)]
all_pairs = []
for fname in chunks:
    fpath = os.path.join(base_in, fname)
    with open(fpath, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                d = json.loads(line)
                d['_chunk'] = fname.replace('lat_new_', '').replace('.jsonl', '')
                all_pairs.append(d)

print(f"Loaded {len(all_pairs)} pairs", file=sys.stderr)

results_by_chunk = {}
all_results = []
for p in all_pairs:
    res = score_pair(p)
    chunk = p['_chunk']
    if chunk not in results_by_chunk:
        results_by_chunk[chunk] = []
    results_by_chunk[chunk].append(res)
    all_results.append(res)

print(f"Scored {len(all_results)} pairs", file=sys.stderr)

os.makedirs(base_out, exist_ok=True)
for chunk_num, results in sorted(results_by_chunk.items()):
    out_fname = f"lat_phase1_scored_{chunk_num}.jsonl"
    out_path = os.path.join(base_out, out_fname)
    with open(out_path, 'w', encoding='utf-8') as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f"Wrote {len(results)} -> {out_fname}", file=sys.stderr)

above_05 = [r for r in all_results if r['semantic_score'] >= 0.5]
above_04 = [r for r in all_results if r['semantic_score'] >= 0.4]
above_06 = [r for r in all_results if r['semantic_score'] >= 0.6]
above_08 = [r for r in all_results if r['semantic_score'] >= 0.8]
nonzero = [r for r in all_results if r['semantic_score'] > 0.0]

print(f"\n=== SUMMARY ===", file=sys.stderr)
print(f"Total: {len(all_results)}", file=sys.stderr)
print(f">=0.8: {len(above_08)}", file=sys.stderr)
print(f">=0.6: {len(above_06)}", file=sys.stderr)
print(f">=0.5: {len(above_05)}", file=sys.stderr)
print(f">=0.4: {len(above_04)}", file=sys.stderr)
print(f">0.0 : {len(nonzero)}", file=sys.stderr)

top15 = sorted(all_results, key=lambda x: x['semantic_score'], reverse=True)[:15]
print(f"\n=== TOP 15 ===", file=sys.stderr)
for i, r in enumerate(top15, 1):
    print(f"{i:2d}. {r['source_lemma']:25s} | {r['target_lemma']:28s} | {r['semantic_score']:.2f} | {r['reasoning'][:80]}", file=sys.stderr)
