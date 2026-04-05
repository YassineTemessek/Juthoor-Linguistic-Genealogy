from __future__ import annotations
import csv, json, re, sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LV2_ROOT = REPO_ROOT / 'Juthoor-CognateDiscovery-LV2'
INPUT_CSV = LV2_ROOT / 'data' / 'processed' / 'beyond_name_etymology_pairs.csv'
OUTPUT_DIR = LV2_ROOT / 'data' / 'processed'
OUTPUT_MATRIX   = OUTPUT_DIR / 'consonant_correspondence_matrix.json'
OUTPUT_WEIGHTS  = OUTPUT_DIR / 'phonetic_law_weights.json'
OUTPUT_MORPHEMES= OUTPUT_DIR / 'morpheme_correspondences.json'

ARABIC_LETTER_RANGE = re.compile(r'[\u0621-\u064A]')
ARABIC_DIACRITICS   = re.compile(r'[\u064B-\u065F\u0670\u0640]')
HAMZA_MAP = str.maketrans({chr(0x623):chr(0x627),chr(0x625):chr(0x627),chr(0x622):chr(0x627),
    chr(0x671):chr(0x627),chr(0x624):chr(0x648),chr(0x626):chr(0x64A),
    chr(0x649):chr(0x64A),chr(0x629):chr(0x647)})
AL_RE = re.compile(chr(0x5E)+chr(0x627)+chr(0x644))

DIGRAPHS = [('sh','ش'),('kh','خ'),('gh','غ'),('dh','ذ'),('th','ث'),('ph','ف')]
SINGLES  = {'S':'ص','T':'ط','D':'ض','Z':'ظ','H':'ح',"'":'ع','b':'ب','t':'ت','j':'ج','h':'ه','d':'د','r':'ر','z':'ز','s':'س','f':'ف','q':'ق','k':'ك','l':'ل','m':'م','n':'ن','w':'و','y':'ي'}

def translit2ar(t):
    result = []
    repl = [(chr(0x101),'a'),(chr(0x12B),'i'),(chr(0x16B),'u'),
            (chr(0x1E25),'H'),(chr(0x1E63),'S'),(chr(0x1E6D),'T'),
            (chr(0x1E0D),'D'),(chr(0x1E93),'Z'),(chr(0x121),'gh'),
            (chr(0x2BF),chr(0x27)),(chr(0x2BE),'')]
    for old,new in repl: t = t.replace(old,new)
    i = 0
    while i < len(t):
        matched = False
        for dg,ar in DIGRAPHS:
            chunk = t[i:i+2]
            if chunk == dg or chunk.lower() == dg:
                if ar: result.append(ar)
                i += 2; matched = True; break
        if not matched:
            ch = t[i]
            ar = SINGLES.get(ch) or SINGLES.get(ch.lower())
            if ar: result.append(ar)
            i += 1
    return result

def ar_consonants(root):
    root = AL_RE.sub('', root.strip()).translate(HAMZA_MAP)
    return ARABIC_LETTER_RANGE.findall(ARABIC_DIACRITICS.sub('', root))

VOWELS = set('aeiou')
def en_consonants(word):
    return [c for c in re.findall(r'[a-z]', word.lower()) if c not in VOWELS]

LATIN_EQ = {'ا':('a', ''),'ء':('', 'a'),'ب':('b', 'p'),'ت':('t',),'ث':('th', 's'),'ج':('j', 'g', 'c'),'ح':('h',),'خ':('kh', 'h', 'g'),'د':('d', 't'),'ذ':('dh', 'z', 'd'),'ر':('r',),'ز':('z', 's'),'س':('s',),'ش':('sh', 's'),'ص':('s', 'z', 'c'),'ض':('d',),'ط':('t',),'ظ':('z', 'd'),'ع':('', 'h', 'a'),'غ':('g', 'gh'),'ف':('f', 'p'),'ق':('c', 'k', 'g', 'q'),'ك':('k', 'c'),'ل':('l',),'م':('m',),'ن':('n',),'ه':('h',),'و':('w', 'v', 'u'),'ي':('y', 'i')}
KHASHIM   = {'ف':('f', 'p'),'ق':('q', 'c', 'k', 'g'),'ط':('t',),'ص':('s',),'ش':('sh', 's'),'ح':('h', 'k', 'c'),'ع':('', 'h'),'غ':('g',),'خ':('h', 'g')}

GD = {
    'guttural_collapse':{"arabic_letters":['ع', 'ح', 'خ', 'غ'],"english_targets":['h', '', 'k', 'g'],"description":'Arabic pharyngeal/velar fricatives collapse in European languages'},
    'emphatic_sibilant_collapse':{"arabic_letters":['ص', 'س', 'ز', 'ش'],"english_targets":['s', 'z', 'c'],"description":'Arabic emphatic and plain sibilants merge to s/z in English'},
    'emphatic_dental_collapse':{"arabic_letters":['ط', 'ت', 'ذ', 'ظ'],"english_targets":['t', 'd'],"description":'Arabic emphatic and plain dentals collapse to t/d in English'},
    'velar_uvular_merge':{"arabic_letters":['ق', 'ك', 'ج'],"english_targets":['k', 'c', 'g', 'j'],"description":'Arabic uvular and velar stops merge in English/Latin'},
    'labial_group':{"arabic_letters":['ب', 'ف', 'م', 'و'],"english_targets":['b', 'f', 'p', 'm', 'v', 'w'],"description":'Arabic labials map to English labials'}
}

SFXPAT = [('ology', 'لغه', 'language/science'),('logy', 'لغه', 'language/science'),('gen', 'جن', 'produce/generate'),('less', 'ليس', 'negation'),('tion', 'ان', 'state/action'),('sion', 'ان', 'state/action'),('ment', 'ما', 'result of action'),('ance', 'ان', 'state/quality'),('ence', 'ان', 'state/quality'),('ness', 'نص', 'state of being'),('ous', 'وص', 'having quality'),('ive', 'يف', 'tending to'),('al', 'ال', 'relating to'),('er', 'ار', 'doer/agent'),('or', 'ار', 'doer/agent'),('ist', 'اسط', 'one who'),('ism', 'اسم', 'doctrine/practice'),('ify', 'ايف', 'to make'),('ize', 'يز', 'to make')]
PFXPAT = [('sub', 'صب', 'pour down/descend'),('ex', 'ءقص', 'exclude/remove'),('es', 'ءقص', 'exclude/remove'),('re', 'رد', 'return/repeat'),('pre', 'قبل', 'before'),('pro', 'فرو', 'forward'),('con', 'كن', 'together'),('com', 'كم', 'together'),('un', 'عن', 'negation'),('in', 'عن', 'negation/in'),('im', 'عن', 'negation/in'),('dis', 'ذيص', 'apart/away'),('de', 'د', 'down/away'),('auto', 'ذات', 'self'),('geo', 'جو', 'earth'),('bio', 'بيو', 'life'),('tele', 'طل', 'distant')]

def score(ar, en):
    cands = LATIN_EQ.get(ar, ())
    if en in cands: return 2
    for c in cands:
        if c and c[0] == en: return 1
    return 0

def align(arabic, english):
    pairs = []; en_used = [False]*len(english); pos = 0
    for ar in arabic:
        best_s, best_j = -1, -1
        for look in range(3):
            j = pos + look
            if j >= len(english): break
            s = score(ar, english[j])
            if s > best_s: best_s, best_j = s, j
        if ar in ('ع','غ') and best_s <= 0:
            pairs.append((ar,'')); continue
        if best_j >= 0 and best_s >= 0:
            for k in range(pos, best_j):
                if not en_used[k]: pairs.append(('',english[k])); en_used[k]=True
            pairs.append((ar, english[best_j])); en_used[best_j]=True; pos=best_j+1
        else:
            pairs.append((ar,''))
    for k in range(pos, len(english)):
        if not en_used[k]: pairs.append(('',english[k]))
    return pairs

def load_pairs(csv_path):
    rows = []
    with open(csv_path, encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f): rows.append(row)
    return rows

def mine(rows):
    ar2en = defaultdict(Counter); en2ar = defaultdict(Counter)
    law_ex = defaultdict(list); sfx_hits = defaultdict(list); pfx_hits = defaultdict(list)
    n_analyzed = n_skipped = n_alignments = 0
    for row in rows:
        eng   = row.get('english_word','').strip()
        aroot = row.get('arabic_root','').strip()
        atrans= row.get('arabic_translit','').strip()
        if not eng: n_skipped+=1; continue
        arc = translit2ar(atrans) if atrans else []
        if not arc and aroot: arc = ar_consonants(aroot)
        enc = en_consonants(eng)
        if not arc or not enc: n_skipped+=1; continue
        if abs(len(arc)-len(enc)) > 4: n_skipped+=1; continue
        n_analyzed += 1; pairs = align(arc, enc); n_alignments += len(pairs)
        ex = aroot + '->' + eng
        for ar,en in pairs:
            if ar: ar2en[ar][en]+=1; law_ex[(ar,en)].append(ex)
            if en: en2ar[en][ar]+=1
        el = eng.lower()
        for sfx,ac,gl in SFXPAT:
            if el.endswith(sfx) and len(el)>len(sfx)+1: sfx_hits[sfx].append((aroot,eng))
        for pfx,ac,gl in PFXPAT:
            if el.startswith(pfx) and len(el)>len(pfx)+1: pfx_hits[pfx].append((aroot,eng))
    print('\n=== Mining stats ===')
    print(f'  Rows analyzed:         {n_analyzed}')
    print(f'  Rows skipped:          {n_skipped}')
    print(f'  Total alignment pairs: {n_alignments}')

    def build_side(cd):
        r = {}
        for letter, counts in sorted(cd.items()):
            total = sum(counts.values())
            if total < 2: continue
            primary = max(counts, key=lambda k: counts[k])
            entry = {(k if k else 'O'):v for k,v in sorted(counts.items(),key=lambda x:-x[1])}
            entry['total'] = total; entry['primary'] = primary if primary else 'O'
            r[letter] = entry
        return r

    matrix_data = {
        'metadata':{'source':'beyond_name_etymology_pairs.csv','n_pairs_analyzed':n_analyzed,'n_alignments':n_alignments,'date':str(date.today())},
        'arabic_to_english': build_side(ar2en),
        'english_to_arabic': build_side(en2ar),
    }
    individual_laws = []
    for ar_l, counts in sorted(ar2en.items()):
        total = sum(counts.values())
        if total < 3: continue
        for en_l, freq in sorted(counts.items(), key=lambda x:-x[1]):
            if freq < 2: continue
            w = round(freq/total,3)
            exs = list(dict.fromkeys(law_ex.get((ar_l,en_l),[])[:5]))
            individual_laws.append({'arabic':ar_l,'english':en_l if en_l else 'O','frequency':freq,'total_for_arabic':total,'weight':w,'examples':exs})
    individual_laws.sort(key=lambda x:-x['frequency'])
    merger_groups = []
    for gname, gdef in GD.items():
        ft = 0; obs = Counter()
        for ar in gdef['arabic_letters']:
            if ar in ar2en:
                for en,cnt in ar2en[ar].items():
                    if en in gdef['english_targets'] or en=='': ft+=cnt; obs[en if en else 'O']+=cnt
        ta = sum(sum(ar2en.get(ar,Counter()).values()) for ar in gdef['arabic_letters'])
        w = round(ft/ta,3) if ta else 0.0
        merger_groups.append({'name':gname,'arabic_letters':gdef['arabic_letters'],'english_targets':gdef['english_targets'],'frequency':ft,'total_occurrences':ta,'weight':w,'observed_distribution':dict(obs.most_common()),'description':gdef['description']})
    merger_groups.sort(key=lambda x:-x['weight'])
    kv = []
    for ar_l, vt in KHASHIM.items():
        counts = ar2en.get(ar_l, Counter()); total = sum(counts.values())
        if total == 0: kv.append({'arabic':ar_l,'khashim_targets':list(vt),'confirmed':False,'note':'no data'}); continue
        primary = max(counts, key=lambda k: counts[k])
        pl = primary if primary else 'O'
        confirmed = primary in vt or primary == ''
        ex = list(dict.fromkeys(law_ex.get((ar_l,primary),[])[:3]))
        kv.append({'arabic':ar_l,'khashim_targets':list(vt),'confirmed':confirmed,'primary_mined':pl,'frequency_primary':counts[primary],'total':total,'examples':ex,'observed_distribution':{(k if k else 'O'):v for k,v in counts.most_common(6)}})
    cc = sum(1 for k in kv if k.get('confirmed'))
    print(f'\n=== Khashim validation: {cc}/{len(KHASHIM)} laws confirmed ===')
    weights_data = {
        'metadata':{'source':'beyond_name_etymology_pairs.csv','n_pairs_analyzed':n_analyzed,'date':str(date.today()),'khashim_confirmation_rate':f'{cc}/{len(KHASHIM)}'},
        'merger_groups':merger_groups,'individual_laws':individual_laws,'khashim_validation':kv}
    sd = {s:(ar,gl) for s,ar,gl in SFXPAT}
    pd = {p:(ar,gl) for p,ar,gl in PFXPAT}
    so = []
    for sfx,(arc,gl) in sd.items():
        hits = sfx_hits.get(sfx,[])
        if not hits: continue
        so.append({'english':f'-{sfx}','arabic_cognate':arc,'meaning':gl,'frequency':len(hits),'attested_arabic_roots':list(dict.fromkeys(r for r,_ in hits if r))[:5],'examples':list(dict.fromkeys(w for _,w in hits))[:8]})
    so.sort(key=lambda x:-x['frequency'])
    po = []
    for pfx,(arc,gl) in pd.items():
        hits = pfx_hits.get(pfx,[])
        if not hits: continue
        po.append({'english':f'{pfx}-','arabic_cognate':arc,'meaning':gl,'frequency':len(hits),'attested_arabic_roots':list(dict.fromkeys(r for r,_ in hits if r))[:5],'examples':list(dict.fromkeys(w for _,w in hits))[:8]})
    po.sort(key=lambda x:-x['frequency'])
    morpheme_data = {'metadata':{'source':'beyond_name_etymology_pairs.csv','n_pairs_analyzed':n_analyzed,'date':str(date.today())},'suffixes':so,'prefixes':po}
    return matrix_data, weights_data, morpheme_data

def main():
    if not INPUT_CSV.exists(): print(f'ERROR: {INPUT_CSV}', file=sys.stderr); sys.exit(1)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f'Loading pairs from: {INPUT_CSV}')
    rows = load_pairs(INPUT_CSV); print(f'Loaded {len(rows)} rows')
    md, wd, mrd = mine(rows)
    with open(OUTPUT_MATRIX,'w',encoding='utf-8') as f: json.dump(md,f,ensure_ascii=False,indent=2)
    print(f'\nWrote: {OUTPUT_MATRIX}')
    with open(OUTPUT_WEIGHTS,'w',encoding='utf-8') as f: json.dump(wd,f,ensure_ascii=False,indent=2)
    print(f'Wrote: {OUTPUT_WEIGHTS}')
    with open(OUTPUT_MORPHEMES,'w',encoding='utf-8') as f: json.dump(mrd,f,ensure_ascii=False,indent=2)
    print(f'Wrote: {OUTPUT_MORPHEMES}')
    print('\n=== Top 10 Arabic->English mappings ===')
    laws = []
    for ar,entry in md['arabic_to_english'].items():
        primary = entry.get('primary','?'); pc = entry.get(primary,0)
        laws.append((ar,primary,pc,entry.get('total',0)))
    laws.sort(key=lambda x:-x[2])
    for i,(ar,en,freq,total) in enumerate(laws[:10],1):
        print(f'  {i:2}. {ar} -> {en!r:6}  (freq={freq}, total={total})')
    print('\n=== Merger groups ===')
    for mg in wd['merger_groups']:
        lets = ' '.join(mg['arabic_letters']); tgts = '/'.join(t if t else 'O' for t in mg['english_targets'])
        print(f"  [{mg['name']}]  {lets} -> {tgts}  freq={mg['frequency']}  weight={mg['weight']}")
        dist = mg.get('observed_distribution',{})
        if dist: print(f'      dist: {list(dist.items())[:4]}')
    print('\n=== Morpheme correspondences ===')
    print('  Suffixes:')
    for s in mrd['suffixes']: print(f"    {s['english']:14}  freq={s['frequency']}  ex={s['examples'][:3]}")
    print('  Prefixes:')
    for p in mrd['prefixes']: print(f"    {p['english']:14}  freq={p['frequency']}  ex={p['examples'][:3]}")
    print('\n=== Khashim law validation ===')
    confirmed = 0
    for k in wd['khashim_validation']:
        status = 'CONFIRMED' if k.get('confirmed') else 'NOT CONFIRMED'
        if k.get('confirmed'): confirmed+=1
        primary = k.get('primary_mined','no data'); freq = k.get('frequency_primary',0)
        print(f"  {k['arabic']}  khashim={k['khashim_targets']}  mined={primary!r}(n={freq})  [{status}]")
        dist = k.get('observed_distribution',{})
        if dist: print(f'      dist: {dict(list(dist.items())[:5])}')
    print(f'\n  Result: {confirmed}/{len(wd[chr(0x6B)+chr(0x68)+chr(0x61)+chr(0x73)+chr(0x68)+chr(0x69)+chr(0x6D)+chr(0x5F)+chr(0x76)+chr(0x61)+chr(0x6C)+chr(0x69)+chr(0x64)+chr(0x61)+chr(0x74)+chr(0x69)+chr(0x6F)+chr(0x6E)])} Khashim laws confirmed')
    print('\n=== Verification ===')
    for path in [OUTPUT_MATRIX, OUTPUT_WEIGHTS, OUTPUT_MORPHEMES]:
        size = path.stat().st_size; print(f'  {path.name}: {size:,} bytes  EXISTS={path.exists()}')
    print('\nDone.')

if __name__ == '__main__':
    main()
