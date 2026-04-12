import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')
BASE = 'C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_phase1_lat_chunks'

all_pairs = []
for i in range(108, 126):
    with open(f'{BASE}/lat_new_{i}.jsonl', encoding='utf-8') as f:
        for line in f:
            all_pairs.append(json.loads(line))

# Arabic signals in masadiq text -> (concept, score)
ARABIC_SIGNALS = {
    'الشمع': ('wax', 0.80),
    'شمع': ('wax', 0.75),
    'الصوت': ('sound', 0.70),
    'صوت': ('sound', 0.65),
    'الملح': ('salt', 0.80),
    'ملح': ('salt', 0.70),
    'مالح': ('salt', 0.70),
    'العسل': ('honey', 0.80),
    'عسل': ('honey', 0.75),
    'النار': ('fire', 0.75),
    'الماء': ('water', 0.70),
    'ماء': ('water', 0.65),
    'الدم': ('blood', 0.75),
    'دم': ('blood', 0.65),
    'الشجر': ('tree', 0.65),
    'الحجر': ('stone', 0.70),
    'السيف': ('sword', 0.75),
    'العين': ('eye', 0.65),
    'الفرس': ('horse', 0.60),
    'الدواء': ('medicine', 0.65),
    'دواء': ('medicine', 0.60),
    'الشرب': ('drink', 0.70),
    'شرب': ('drink', 0.65),
    'البخل': ('stingy', 0.60),
    'الصوف': ('wool', 0.75),
    'صوف': ('wool', 0.70),
    'السمك': ('fish', 0.70),
    'اللحم': ('meat', 0.70),
    'النخل': ('palm', 0.75),
    'نخل': ('palm', 0.70),
    'الكلب': ('dog', 0.70),
    'المطر': ('rain', 0.65),
}

# Target gloss keywords -> concept tag
TARGET_CONCEPTS = {
    'wax': ['cera','cereus','ceum','wax'],
    'candle': ['candel','candela','torch','fax','cereus'],
    'sound': ['sonus','clarisonus','dulcisonus','clangor','sound','sounding'],
    'salt': ['salsugo','salin','brackish','saltiness','salinity'],
    'honey': ['melligo','mel','honey','propolis'],
    'drink': ['bibax','exbibo','adbibo','bibo','drink out','to drink','drinking'],
    'water': ['aqua','abluvium','flood','deluge','water'],
    'blood': ['sanguis','cruor','blood'],
    'tree': ['arbor','silva','tree'],
    'stone': ['saxum','saxalis','lapido','stone','rock'],
    'sword': ['gladius','ensis','sword'],
    'medicine': ['medicin','medicus','remedium','cure'],
    'wool': ['lana','vellu','wool','fleece'],
    'fire': ['igni','incend','ardor','flame','fire'],
    'fish': ['piscis','squalus','fish'],
    'eye': ['alcohol','collyrium','kohl','stibium','ocul'],
    'meat': ['caro','carnis','lard','lardum','fat','lard','bacon'],
    'palm': ['palm tree','date palm','phoenix'],
    'dog': ['canis','dog'],
    'rain': ['pluvio','imber','rain'],
    'stingy': ['parcimon','avar'],
}

# Concept pairs that could match
SAME_CONCEPT = {
    'wax': ['wax', 'candle'],
    'sound': ['sound'],
    'salt': ['salt'],
    'honey': ['honey'],
    'fire': ['fire'],
    'water': ['water'],
    'blood': ['blood'],
    'tree': ['tree'],
    'stone': ['stone'],
    'sword': ['sword'],
    'medicine': ['medicine'],
    'wool': ['wool'],
    'drink': ['drink'],
    'fish': ['fish'],
    'eye': ['eye'],
    'meat': ['meat'],
    'palm': ['palm'],
    'dog': ['dog'],
    'rain': ['rain'],
    'stingy': ['stingy'],
}

skip_tg = ['given name','family name','roman nomen','famously held by','nomen gentile',
           'gallium','lithium','holmium','erbium','terbium','berkelium','californium',
           'idaho','idahum','uralic','a city in','an island','a town in']

hits = []
for p in all_pairs:
    mg = p.get('masadiq_gloss', '')
    tg = p['target_gloss']
    tg_lower = tg.lower()
    ar = p['arabic_root']
    lat = p['target_lemma']

    if any(s in tg_lower for s in skip_tg):
        continue

    ar_concepts_found = []
    for ar_word, (concept, base_score) in ARABIC_SIGNALS.items():
        if ar_word in mg:
            ar_concepts_found.append((concept, base_score, ar_word))

    if not ar_concepts_found:
        continue

    for ar_concept, base_score, ar_signal in ar_concepts_found:
        if ar_concept not in SAME_CONCEPT:
            continue
        for tgt_concept, tgt_kws in TARGET_CONCEPTS.items():
            if tgt_concept not in SAME_CONCEPT[ar_concept]:
                continue
            for kw in tgt_kws:
                if kw in tg_lower:
                    hits.append({
                        'ar': ar, 'lat': lat,
                        'ar_signal': ar_signal, 'concept': ar_concept,
                        'tg': tg[:70], 'score': base_score,
                        'ar_gloss': mg[:120]
                    })
                    break

print(f'Bidirectional semantic hits: {len(hits)}')
for h in hits:
    print(f"  {h['score']:.2f}  {h['ar']:20s}  {h['lat']:22s}  {h['concept']:10s}")
    print(f"       TG: {h['tg']}")
    print(f"       AR signal '{h['ar_signal']}' in: {h['ar_gloss'][:80]}")
    print()
