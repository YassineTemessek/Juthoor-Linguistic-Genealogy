"""
Eye 2 Phase 1 scorer — chunks 108-125 (ara-lat)
Masadiq-first methodology, conservative calibration.
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

# ── Arabic root → core English meanings (masadiq-derived) ──────────────────
MASADIQ = {
    "السيف":   ["sword","blade","weapon"],
    "السين":   ["letter","sibilant","hiss","whistle","sound"],
    "الش":     ["city","Andalusia","place","town"],
    "الشاو":   ["lead rope","camel rein","goal","dung","bucket"],
    "الشبث":   ["insect","tick","grub","creature"],
    "الشبر":   ["cubit","span","measure","give"],
    "الشبع":   ["satiety","fullness","satisfy","fill"],
    "الشبق":   ["lust","desire","longing"],
    "الشبك":   ["net","entangle","weave","intertwine"],
    "الشبل":   ["lion cub","young lion","cub"],
    "الشبم":   ["cold water","cool","chill"],
    "الشبه":   ["resemblance","likeness","similar","bronze"],
    "الشبو":   ["thorn","spike","prick","sting"],
    "الشبوط":  ["fish","barbel","carp"],
    "الشبيب":  ["youth","young","vigor"],
    "الشتا":   ["winter","rain","cold season"],
    "الشتم":   ["insult","revile","slander","abuse"],
    "الشجا":   ["sorrow","grief","sadness","bone stuck in throat"],
    "الشجر":   ["tree","shrub","plant","wood"],
    "الشجع":   ["courage","brave","bold"],
    "الشجن":   ["branch","grief","sorrow","longing"],
    "الشح":    ["stinginess","miser","greed"],
    "الشحذ":   ["sharpen","whet","edge","hunger"],
    "الشحم":   ["fat","grease","lard","marrow"],
    "الشحن":   ["load","fill","cargo","hatred","anger"],
    "الشخص":   ["person","individual","figure","body"],
    "الشد":    ["tie","bind","tighten","strong"],
    "الشدق":   ["corner of mouth","jaw","cheek"],
    "الشذا":   ["pungent smell","splinter","fragment","sting"],
    "الشرب":   ["drink","drinking","water","imbibe"],
    "الشرح":   ["explain","open","expand","exposition"],
    "الشرط":   ["condition","stipulation","incision","cut","police"],
    "الشرع":   ["law","religion","reach water","hang"],
    "الشرف":   ["honor","nobility","elevation","high ground"],
    "الشرق":   ["east","sunrise","choke","splinter"],
    "الشرك":   ["polytheism","trap","snare","partner","share"],
    "الشره":   ["gluttony","greed","voracity"],
    "الشري":   ["colocynth","bitter plant","exchange","sell"],
    "الشسع":   ["sandal strap","thong"],
    "الشط":    ["shore","bank","river bank","extravagance"],
    "الشطر":   ["half","side","direction","milking"],
    "الشعب":   ["people","tribe","nation","mountain pass","divide"],
    "الشعر":   ["hair","poetry","feel","know"],
    "الشعل":   ["flame","blaze","light fire"],
    "الشغف":   ["passion","love deeply","heart lining"],
    "الشفا":   ["edge","brink","lip","cure","healing"],
    "الشفع":   ["pair","even number","intercede"],
    "الشفق":   ["twilight","dawn glow","pity","compassion"],
    "الشق":    ["crack","split","difficulty","half","side"],
    "الشقر":   ["red","blonde","poppy","anemone"],
    "الشكا":   ["complain","lament","illness","pain"],
    "الشكر":   ["gratitude","thanks","genitals"],
    "الشكل":   ["shape","form","similar","kind","type"],
    "الشلل":   ["paralysis","scatter","drive"],
    "الشمال":  ["north","left side","wind","character"],
    "الشمر":   ["tuck up","resolve","bold","fennel"],
    "الشمس":   ["sun","solar","sunshine"],
    "الشمع":   ["wax","candle"],
    "الشمل":   ["gather","include","encompass","total"],
    "الشنأ":   ["hate","dislike","enmity"],
    "الشنع":   ["ugly","abominable","denounce"],
    "الشهب":   ["white streaked","gray","shooting star"],
    "الشهد":   ["honey","witness","honeycomb"],
    "الشهر":   ["month","moon","fame","renowned"],
    "الشوق":   ["longing","yearning","desire","love"],
    "الشوك":   ["thorn","spine","weapon","spine of fish"],
    "الشيب":   ["white hair","graying","old age"],
    "الشيح":   ["wormwood","artemisia","noble"],
    "الشيخ":   ["old man","elder","chief","sheikh"],
    "الشيد":   ["plaster","build high","lime"],
    "الصقر":   ["falcon","hawk","predator bird"],
    "الصلب":   ["hard","firm","cross","spine","backbone"],
    "الصلح":   ["peace","reconciliation","goodness"],
    "الصمت":   ["silence","quiet","mute"],
    "الصمد":   ["solid","eternal","lord","aim"],
    "الصمغ":   ["gum","resin","sap"],
    "الصنج":   ["cymbal","bell"],
    "الصنعه":  ["craft","art","make","manufacture","skill"],
    "الصنف":   ["type","kind","category","sort"],
    "الصنم":   ["idol","statue"],
    "الصهر":   ["melt","son-in-law","family by marriage","heat"],
    "الصوب":   ["rain","direction","pour down","correct"],
    "الصوت":   ["sound","voice","noise"],
    "الصوف":   ["wool","fleece"],
    "الصول":   ["attack","rush at","lion"],
    "الصوم":   ["fasting","abstain","fast"],
    "الصون":   ["preserve","protect","guard"],
    "الصيد":   ["hunt","hunting","game","pride"],
    "الصيف":   ["summer","summer rain"],
    "الضفف":   ["crowd","narrow","hardship","many people"],
    "الضفو":   ["abundant","overflow","loose garment"],
    "الضلع":   ["rib","side","lean","slant"],
    "الضم":    ["embrace","press","join","add","vowel"],
    "الضمر":   ["thin","emaciate","lean body"],
    "الضنك":   ["narrow","tight","hardship"],
    "الضوأ":   ["light","shine","illuminate"],
    "الضوع":   ["spread fragrance","waft","agitate"],
    "الضيف":   ["guest","stranger","visitor"],
    "الضيق":   ["narrow","tight","anxiety"],
    "الطفل":   ["child","infant","baby"],
    "الطفو":   ["float","rise to surface"],
    "الطلب":   ["request","seek","pursue"],
    "الطلح":   ["acacia","tired","weary"],
    "الطلع":   ["emerge","rise","palm shoot"],
    "الطلق":   ["free","release","childbirth","lightning"],
    "الطم":    ["cover","fill","sea","flood"],
    "الطمح":   ["high","ambition","aspire"],
    "الطمع":   ["greed","covet","desire"],
    "الطمن":   ["calm","reassure","tranquil"],
    "الطوط":   ["cotton","fluff","wool"],
    "الظل":    ["shadow","shade","protection","umbrella"],
    "الظلم":   ["injustice","oppression","wrong","darkness"],
    "الظمأ":   ["thirst","thirsty"],
    "الظن":    ["think","suspect","opinion","doubt"],
    "الظهر":   ["back","noon","power","above","surface"],
    "العبث":   ["play","idle","nonsense","tamper"],
    "العبد":   ["slave","servant","worship"],
    "العبر":   ["lesson","cross over","tears","interpret"],
    "العتق":   ["freedom","old","noble","release from slavery"],
    "العجب":   ["wonder","amazement","tail bone"],
    "العجز":   ["weakness","buttocks","hind part","incapacity"],
    "العجل":   ["calf","haste","quick"],
    "العجم":   ["non-Arab","Persian","foreign","chew"],
    "العد":    ["count","number","prepare","many"],
    "العدس":   ["lentil","mole on body"],
    "العدل":   ["justice","equal","balance"],
    "العدم":   ["poverty","lack","nonexistence"],
    "العدن":   ["settle","mine","Eden"],
    "العدو":   ["enemy","run","attack"],
    "العرب":   ["Arab","Arabic","clarity","eloquence"],
    "العرج":   ["lame","limp","goats"],
    "العرس":   ["wedding","bride","weasel"],
    "العرش":   ["throne","trellis","shade structure"],
    "العرض":   ["width","offer","honor","flank","present"],
    "العرف":   ["custom","mane","fragrance","know"],
    "العرق":   ["sweat","vein","root","race","origin"],
    "العري":   ["naked","bare","strip"],
    "العفز":   ["walnut","play with wife","make kneel","nuts"],
    "العفزر":  ["swift driver","loud noise","racket"],
    "العفقل":  ["big face man"],
    "العفكل":  ["stupid","fool","idiotic"],
    "العفو":   ["pardon","forgive","efface","erase","grass"],
    "العقب":   ["heel","consequence","result","offspring","follow"],
    "العقد":   ["knot","contract","count beads","stronghold"],
    "العقرب":  ["scorpion","whip end"],
    "العقل":   ["mind","intellect","reason","blood money","tie"],
    "العلق":   ["leech","hang","cling","love deeply","coagulate blood"],
    "العلقم":  ["colocynth","bitter","bitter plant"],
    "العلك":   ["chew gum","gum","resin"],
    "العلم":   ["knowledge","flag","landmark","know"],
    "العلو":   ["high","ascend","above","elevation"],
    "العم":    ["uncle","nation","resolve","intend"],
    "العمل":   ["work","action","labor"],
    "العمر":   ["age","life span","lifetime"],
    "العمق":   ["depth","deep","profound"],
    "العنب":   ["grape","grapes"],
    "العنكب":  ["spider"],
    "العنو":   ["submit","surrender","yield","spring of water"],
    "الغبط":   ["envy good fortune","admire","saddle","press"],
    "الغرب":   ["west","bucket","vein in eye","foreign"],
    "الغرق":   ["drown","sink","immerse"],
    "الغرم":   ["fine","debt","loss","pay"],
    "الغزل":   ["spin thread","flirt","gazelle"],
    "الغزو":   ["raid","attack","invasion","war"],
    "الغسل":   ["wash","clean","bathe"],
    "الغضب":   ["anger","rage","wrath"],
    "الغطس":   ["dive","plunge","dip"],
    "الغلث":   ["mix bad food","adulterate"],
    "الفظ":    ["harsh","rude","rough","coarse"],
    "الفقر":   ["poverty","need","vertebra"],
    "الفقه":   ["understand","jurisprudence","Islamic law"],
    "الفك":    ["jaw","unlock","release","ransom"],
    "الفكر":   ["think","thought","reflection"],
    "الفلج":   ["succeed","victory","water channel","paralysis"],
    "الفلح":   ["success","farming","cultivate"],
    "الفلز":   ["metal","ore","mineral"],
    "الفلس":   ["coin","scale of fish","bankruptcy"],
    "الفلق":   ["dawn","split","calamity","crack"],
    "الفلك":   ["orbit","ship","spindle"],
    "الفم":    ["mouth"],
    "الفن":    ["art","kind","type","technique"],
    "الفهد":   ["cheetah","leopard"],
    "الفهم":   ["understanding","comprehend"],
    "الفوت":   ["miss","pass by","loss"],
    "الفوج":   ["group","troop","crowd"],
    "الفوح":   ["fragrance waft","spread smell"],
    "الفور":   ["immediately","boil","rush"],
    "الفوز":   ["success","win","escape"],
    "الفوق":   ["above","arrow notch","higher"],
    "الفول":   ["broad bean","fava"],
    "الفيض":   ["overflow","flood","abundance"],
    "القبس":   ["firebrand","spark","torch"],
    "القبض":   ["grasp","seize","receive","contract"],
    "القبل":   ["before","kiss","accept","forward"],
    "القبو":   ["vault","arch","cellar"],
    "القتل":   ["kill","murder","slay"],
    "القحط":   ["drought","dryness","famine"],
    "اللجام":  ["bridle","rein","bit","muzzle"],
    "اللجأ":   ["refuge","shelter","resort to"],
    "اللحم":   ["meat","flesh","muscle"],
    "اللحن":   ["melody","tune","grammatical error","understand"],
    "اللحي":   ["jaw","beard"],
    "اللذ":    ["pleasure","taste","enjoy"],
    "اللسن":   ["tongue","eloquence","language"],
    "اللطف":   ["gentleness","kindness","subtle","gift"],
    "اللعب":   ["play","game","saliva"],
    "اللعن":   ["curse","damn","expel"],
    "اللغز":   ["riddle","enigma","puzzle"],
    "اللغو":   ["vain talk","nonsense","excess"],
    "اللفظ":   ["word","utterance","pronounce","speak"],
    "المخ":    ["marrow","brain","spinal cord","pure","essence"],
    "المدر":   ["dry clay","clod","mud brick","earth"],
    "المده":   ["praise","eulogize","commend"],
    "المرج":   ["meadow","pasture","mix","confuse"],
    "المرح":   ["joy","exuberance","frolic","swagger"],
    "المرض":   ["illness","disease","sick"],
    "المرق":   ["broth","soup","split arrow","exit"],
    "المري":   ["ruminant","massage udder","Roman condiment"],
    "المز":    ["sour","acerbic","acid"],
    "المسك":   ["musk","hold","grasp","skin"],
    "المشط":   ["comb","spine"],
    "النبل":   ["arrows","nobility","intelligence","excellent"],
    "النبي":   ["prophet","prophecy"],
    "النجح":   ["success","achieve"],
    "النجم":   ["star","planet","plant spring up"],
    "النحت":   ["carve","chisel","trim","whittle"],
    "النحر":   ["slaughter","neck","chest"],
    "النحس":   ["misfortune","evil omen","mars","copper"],
    "النحل":   ["bee","grant freely","attribute falsely"],
    "النخل":   ["palm tree","sieve","date palm"],
    "الندم":   ["regret","remorse","companion"],
    "الندي":   ["dew","moist","generous","council"],
    "الهبط":   ["descend","lower","fall","valley"],
    "الهجر":   ["abandon","desert","nonsense","migration"],
    "الهدف":   ["target","goal","aim"],
    "الهدم":   ["demolish","destroy","tear down"],
    "الهدن":   ["calm","truce","pacify"],
    "الهرب":   ["escape","flee","run away"],
    "الهرم":   ["pyramid","old age","decrepit"],
    "انداق":   ["pour out","overflow"],
    "بابا":    ["father","daddy","pope","buzz"],
    "باباج":   ["ancestor name","grandfather"],
    "باباه":   ["say baba to","caress child","origin","foundation"],
    "بابك":    ["historical rebel","Khuramite"],
    "بابل":    ["Babylon","confusion","magic"],
    "باج":     ["tax","tribute","contribution"],
    "باح":     ["reveal","expose","became free"],
    "بازي":    ["falcon","hawk"],
    "باق":     ["permanent","lasting","remaining"],
    "باكر":    ["early morning","dawn"],
    "بال":     ["mind","heart","whale","condition"],
    "بان":     ["clear","obvious","separate","ben tree"],
    "برع":     ["excel","surpass","outstanding"],
    "برك":     ["kneel","bless","pool of water","chest"],
    "برهن":    ["prove","demonstrate","evidence"],
    "بز":      ["cloth","merchandise","nipple","overcome"],
    "بزل":     ["pierce","tap barrel","wisdom molar"],
    "بسط":     ["spread","expand","carpet"],
    "بشر":     ["skin","human being","good news","announce"],
    "تاف":     ["become disgusted","rotten"],
    "ترك":     ["leave","abandon","Turk","Turkish"],
    "تموز":    ["July","Tammuz","pagan god"],
    "تنر":     ["oven","furnace","tanur"],
    "جشا":     ["belch","burp","rise up"],
    "جشات":    ["soul surged","rose up","recoiled"],
    "جشب":     ["plain food","without sauce","rough"],
    "جشه":     ["crush","pound","sweep","clean well"],
    "جشع":     ["greed","gluttony","covet"],
    "جص":      ["plaster","gypsum","chalk"],
    "جعل":     ["make","put","dung beetle","wage"],
    "جف":      ["dry","desiccate","quiver for arrows"],
    "جفن":     ["eyelid","vine","dish"],
    "جلب":     ["bring","import","wound crust","shout"],
    "جلح":     ["bald forehead","hairless"],
    "حشرجه":   ["death rattle","gurgle","rattle in throat"],
    "حظر":     ["fence","forbid","prohibit","enclosure"],
    "حفد":     ["serve","hasten","grandson"],
    "حفر":     ["dig","excavate","hollow"],
    "حفظ":     ["memorize","protect","guard","preserve"],
    "حفل":     ["gather","full","ceremony","event"],
    "حق":      ["right","truth","due","reality"],
    "حقد":     ["grudge","malice","hatred"],
    "حقل":     ["field","farm","cultivate"],
    "حكم":     ["judge","rule","wisdom","command"],
    "حلب":     ["milk","Aleppo city"],
    "حلف":     ["oath","swear","alliance"],
    "حلق":     ["shave","circle","ring"],
    "حلم":     ["dream","patience","forbear"],
    "حلو":     ["sweet","fresh water","beautiful"],
    "حلي":     ["jewelry","ornament"],
    "حم":      ["fever","hot coal","in-law"],
    "حمد":     ["praise","thank","commend"],
    "حمر":     ["red","donkey","peel"],
    "حمص":     ["chickpea","Homs city"],
    "حمض":     ["sour","acid","salty plant"],
    "حمل":     ["carry","bear","load","pregnancy"],
    "حمي":     ["protect","fever","forbidden"],
    "دثا":     ["enrich","prosper","plenty"],
    "دحو":     ["push away","spread","throw"],
    "دخل":     ["enter","inside","income"],
    "دخن":     ["smoke","fume"],
    "درب":     ["practice","path","gate"],
    "درج":     ["steps","drawer","walk gradually"],
    "درس":     ["study","thresh grain","old ruins"],
    "درع":     ["armor","coat of mail"],
    "درك":     ["reach","attain","comprehend"],
    "دفق":     ["pour","flow","gush"],
    "دفن":     ["bury","conceal","hide"],
    "دق":      ["crush","pound","fine","knock"],
    "دكن":     ["dark color","storage room"],
    "دلع":     ["tongue out","relaxed"],
    "دلو":     ["bucket","Aquarius"],
    "دمر":     ["destroy","ruin","enter without permission"],
    "دمع":     ["tear drop","weep"],
    "دمل":     ["abscess","heal sore"],
    "دمي":     ["blood","bleed"],
    "دنو":     ["near","approach","close"],
    "دهاع":    ["call to goats","herding cry"],
    "دهر":     ["time","age","era","fate"],
    "دهش":     ["astonish","perplex","confuse"],
    "دهن":     ["oil","anoint","grease","fat"],
    "دور":     ["house","circle","age","revolve"],
    "دوس":     ["trample","press","thresh"],
    "دول":     ["state","nation","alternate","turn"],
    "دون":     ["below","without","inferior","near"],
    "دير":     ["monastery","church"],
    "ديك":     ["rooster","cock"],
    "ديم":     ["lasting rain","continuous rain"],
    "دين":     ["religion","debt","judgment","obey"],
    "دينا":    ["gold coin","dinar"],
    "راغ":     ["turn aside","be cunning","disgusted"],
    "رتك":     ["trot","quick walk"],
    "رجع":     ["return","repeat","answer","echo"],
    "رجف":     ["shake","tremble","quake"],
    "رجل":     ["man","foot","walk"],
    "رجم":     ["stone","kill by stoning","divination","guess"],
    "رجو":     ["hope","expect","fear"],
    "رحب":     ["spacious","wide","welcome"],
    "رحل":     ["travel","saddle","depart"],
    "رحم":     ["womb","mercy","kinship"],
    "رحو":     ["millstone","grind"],
    "رخا":     ["comfort","ease","prosperity"],
    "رخص":     ["cheap","low price","permission"],
    "رد":      ["return","reject","reply"],
    "ردع":     ["stop","restrain","deter"],
    "ردم":     ["fill rubble","cover","mend"],
    "ردي":     ["perish","ruined","bad"],
    "رذل":     ["vile","despise","worthless"],
    "رضو":     ["content","satisfied","please"],
}

# ── Scoring helpers ─────────────────────────────────────────────────────────

PROPER_NOUN_KEYWORDS = [
    'roman nomen','nomen gentile','famously held by','cognomen','praenomen',
    'given name','family name','gens or','historical king','historical figure',
    'an island','a city in','a town in','a region in','hispania',
    'idahum','idaho','turoqua','alaricus','lacerius','zoilus','saleius',
    'alfius','hababa','bibaga','ahuidies','justus',
    'gallium','lithium','lysine','uralic','ajoensis',
]

GRAM_FORM_KEYWORDS = [
    'singular present active indicative',
    'singular future passive imperative',
    'singular future active indicative',
    'perfect active infinitive',
    'comparative degree of',
    'vocative masculine singular',
    'ablative feminine singular',
    'alternative spelling of eius',
    'alternative spelling of iussus',
    'alternative spelling of iocus',
    'second/third-person',
    'second-person singular',
]

def is_proper(gloss):
    g = gloss.lower()
    return any(k in g for k in PROPER_NOUN_KEYWORDS)

def is_gram_form_only(gloss):
    g = gloss.lower()
    return any(k in g for k in GRAM_FORM_KEYWORDS) and len(gloss) < 80

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

# Concept buckets: (ar_meanings_subset, target_keywords, score, tag)
CONCEPT_RULES = [
    # Drinking
    (["drink","drinking","imbibe","pure wine"],
     ["drink","imbib","bib","biber","bibax","potus","poto","sip","absorp","ebri"],
     0.80, "drink/imbibe concept match"),
    # Honey / sweet
    (["honey","honeycomb","sweet","fresh water","beautiful"],
     ["honey","mel","sweet","dulc","apis","sacchar"],
     0.78, "honey/sweet concept match"),
    # Sun
    (["sun","solar","sunshine"],
     ["sun","solar","sol","helios","radiant"],
     0.85, "sun concept direct match"),
    # Light / illuminate
    (["light","shine","illuminate"],
     ["light","lux","lumen","lumin","bright","shin","illumin","lucid"],
     0.75, "light/shine concept match"),
    # Water / rain / pour / flow
    (["rain","water","pour","flood","flow","gush","pour out","overflow","lasting rain","continuous rain"],
     ["rain","aqua","water","pour","flood","flow","river","irrig","pluvio","imber","dilu"],
     0.70, "water/rain/flow concept match"),
    # Fire / flame
    (["fire","flame","blaze","burn","spark","firebrand","spark","torch"],
     ["fire","flame","blaze","burn","spark","igni","pyr","candl","torch","incend"],
     0.75, "fire/flame concept match"),
    # Meat / flesh / lard
    (["meat","flesh","muscle","fat","grease","lard","marrow"],
     ["meat","flesh","carn","muscl","pork","beef","lard","bacon","fat","adip","pinguis"],
     0.75, "meat/flesh/fat concept match"),
    # Wool / fleece
    (["wool","fleece","cotton","fluff"],
     ["wool","fleece","vellu","lan","floc","texti","cotton"],
     0.75, "wool/fleece concept match"),
    # Shadow / shade
    (["shadow","shade","protection","umbrella"],
     ["shadow","shade","umbra","dark","obsc"],
     0.75, "shadow/shade concept match"),
    # Month / moon / fame
    (["month","moon","fame","renowned"],
     ["month","moon","luna","mensis","calendar","famous"],
     0.70, "month/moon concept match"),
    # Star / planet
    (["star","planet","shooting star"],
     ["star","stella","sider","astro","planet","celest","meteor","comet"],
     0.75, "star/celestial concept match"),
    # Sound / voice
    (["sound","voice","noise"],
     ["sound","voice","noise","vox","sono","phon","vocal","cry"],
     0.70, "sound/voice concept match"),
    # Peace / reconcile
    (["peace","reconciliation","goodness"],
     ["peace","reconcil","pax","truce","calm","quiet"],
     0.75, "peace/reconciliation concept match"),
    # Prophet
    (["prophet","prophecy"],
     ["prophet","proph","vates","oracle","divin"],
     0.80, "prophet/prophecy concept match"),
    # Law / jurisprudence
    (["law","religion","jurisprudence","Islamic law","understand","jurisprudence"],
     ["law","legal","jur","religio","sacred","nomos","legifer","legisl"],
     0.65, "law/jurisprudence concept match"),
    # Tree / plant
    (["tree","shrub","plant","wood","acacia","wormwood","artemisia"],
     ["tree","plant","shrub","arbor","silva","wood","forest","vegetat","arbust"],
     0.65, "tree/plant concept match"),
    # Palm tree
    (["palm tree","date palm","palm shoot"],
     ["palm","date","phoenix","drupe"],
     0.80, "palm tree concept direct match"),
    # Bee
    (["bee"],
     ["bee","apis","mel"],
     0.80, "bee concept match"),
    # Fish
    (["fish","barbel","carp"],
     ["fish","piscis","piscat","barbel","carp"],
     0.70, "fish concept match"),
    # Scorpion
    (["scorpion"],
     ["scorpion","scorpio","scorp"],
     0.85, "scorpion direct concept match"),
    # Spider
    (["spider"],
     ["spider","aranea","arachn"],
     0.85, "spider direct concept match"),
    # Grape / vine / wine
    (["grape","grapes"],
     ["grape","vine","vitis","uva","raisin","wine","vinum","bacch"],
     0.80, "grape/vine concept match"),
    # Wedding / marriage
    (["wedding","bride","weasel"],
     ["wedding","bride","marry","matrimon","nupt","conjug"],
     0.75, "wedding/marriage concept match"),
    # Slave / servant
    (["slave","servant","worship"],
     ["slave","servant","serv","ancilla","famulus"],
     0.70, "slave/servant concept match"),
    # Kill / slay
    (["kill","murder","slay"],
     ["kill","slay","murder","neco","occid","interf"],
     0.70, "kill/slay concept match"),
    # Praise
    (["praise","thank","commend","praise","eulogize","commend"],
     ["praise","laud","commend","glorif","extol","laudo"],
     0.70, "praise concept match"),
    # Mercy / womb
    (["mercy","womb","kinship"],
     ["mercy","womb","compassion","misericord","uterus"],
     0.70, "mercy/womb concept match"),
    # Oath / swear
    (["oath","swear","alliance"],
     ["oath","swear","vow","jur","promis","pact"],
     0.70, "oath/swear concept match"),
    # Hope / expect
    (["hope","expect","fear"],
     ["hope","expect","spe","spero"],
     0.65, "hope/expectation concept match"),
    # Return / echo
    (["return","repeat","answer","echo"],
     ["return","echo","replic","respond","rever"],
     0.65, "return/echo concept match"),
    # Religion / debt
    (["religion","debt","judgment","obey"],
     ["religion","faith","debt","judgment","obey","piety"],
     0.65, "religion/debt/obedience concept match"),
    # Marrow / brain / jaw
    (["marrow","brain","spinal cord","pure","essence"],
     ["marrow","brain","medullarum","medulla","cerebr","jaw","mouth"],
     0.65, "marrow/brain anatomical concept match"),
    # Bridle / rein
    (["bridle","rein","bit","muzzle"],
     ["bridle","rein","bit","halter","frenum","equin","freno"],
     0.80, "bridle/rein concept match — Arabic اللجام loan candidate"),
    # Plaster / gypsum
    (["plaster","gypsum","chalk","plaster","build high","lime"],
     ["plaster","gypsum","chalk","calx","calcium","gyps"],
     0.75, "plaster/gypsum concept match"),
    # Smell / fragrance
    (["pungent smell","smell","fragrance","scent","fragrance waft","spread smell","spread fragrance","waft","agitate"],
     ["smell","fragranc","scent","odor","arom","olfact","perfum"],
     0.70, "smell/fragrance concept match"),
    # Bitter plant
    (["colocynth","bitter plant","bitter","bitter"],
     ["bitter","colocynth","absinth","wormwood","artemisia","aloe"],
     0.70, "bitter plant concept match"),
    # Falcon / hawk
    (["falcon","hawk","predator bird"],
     ["falcon","hawk","eagle","accipiter","raptor","aquila","falc"],
     0.75, "falcon/hawk concept match"),
    # Father / pope
    (["father","daddy","pope","buzz"],
     ["father","papa","pater","pope","pontif","patri"],
     0.80, "father/pope concept match — بابا/papa family"),
    # Buzz / hum
    (["buzz"],
     ["buzz","hum","murmur","bombio","bomd"],
     0.60, "buzz/hum sound match"),
    # Stone / rock
    (["stone","grindstone","flint stone","hard rock","stony","stone"],
     ["stone","rock","flint","silex","saxum","lapis","lith"],
     0.65, "stone/rock concept match"),
    # Wax / candle
    (["wax","candle"],
     ["wax","candle","cera","candel","torch"],
     0.80, "wax/candle concept match"),
    # Hair / poetry (ambiguous polysemy)
    (["hair","poetry","feel","know"],
     ["hair","poem","poetry","verse","pil","caes","crinis"],
     0.60, "hair/poetry concept ambiguous match"),
    # Monastery / church
    (["monastery","church"],
     ["monasteri","church","monach","monachus","ecclesiast","abbey"],
     0.80, "monastery/church concept match"),
    # Summer
    (["summer","summer rain"],
     ["summer","aestiv","aestas","canicul"],
     0.75, "summer concept match"),
    # Winter / cold
    (["winter","rain","cold season","cold water","cool","chill"],
     ["winter","rain","hiems","hiber","cold season","pluvial","frigid"],
     0.65, "winter/cold/rain concept match"),
    # North / wind
    (["north","left side","wind","character"],
     ["north","wind","aquilo","boreas","septentri","borealis"],
     0.65, "north/wind concept match"),
    # Near / approach
    (["near","approach","close"],
     ["near","close","approach","proxim","propinqu"],
     0.65, "near/approach concept match"),
    # Knowledge / know
    (["knowledge","flag","landmark","know"],
     ["know","science","signif","signal","flag","mark","doctr","cogn"],
     0.60, "knowledge/mark concept match"),
    # Cure / heal
    (["cure","healing","edge","brink","lip"],
     ["cure","heal","remedy","medicin","sano","sanare","salus"],
     0.70, "cure/healing concept match"),
    # Mind / intellect
    (["mind","intellect","reason","blood money","tie"],
     ["mind","intellect","reason","ratio","mens","cogit"],
     0.65, "mind/intellect concept match"),
    # Sweat / vein / root
    (["sweat","vein","root","race","origin"],
     ["sweat","vein","root","race","origin","sudor","vena","radix"],
     0.65, "sweat/vein/root concept match"),
    # Knot / contract
    (["knot","contract","count beads","stronghold"],
     ["knot","contract","bond","nexus","liga","nod"],
     0.65, "knot/contract concept match"),
    # Oil / anoint
    (["oil","anoint","grease","fat"],
     ["oil","oleum","anoint","ungu","lubric","grease"],
     0.70, "oil/anoint concept match"),
    # Shake / tremble
    (["shake","tremble","quake"],
     ["shake","tremble","quak","vibrat","trepidat"],
     0.65, "shake/tremble concept match"),
    # Destroy / ruin
    (["destroy","ruin","enter without permission"],
     ["destroy","ruin","demol","delet","perd","evert"],
     0.65, "destroy/ruin concept match"),
    # Touch / feel
    (["touch","feel"],
     ["touch","feel","tang","tact","palp","grope"],
     0.65, "touch/feel concept match"),
    # Bury / conceal / hide
    (["bury","conceal","hide"],
     ["bury","conceal","hide","inter","occult","sepelio","cond"],
     0.65, "bury/conceal concept match"),
    # Satiety / fill
    (["satiety","fullness","satisfy","fill"],
     ["sati","full","fill","satiet","saturo","plenus","abund"],
     0.65, "satiety/fullness concept match"),
    # Courage / bravery
    (["courage","brave","bold"],
     ["courage","brave","bold","fortis","audax","virt"],
     0.65, "courage/bravery concept match"),
    # Justice / equal
    (["justice","equal","balance"],
     ["justice","equal","fair","justitia","aequal","libell"],
     0.65, "justice/equality concept match"),
    # Anger / rage
    (["anger","rage","wrath"],
     ["anger","rage","wrath","ira","furor","irascib"],
     0.65, "anger/rage concept match"),
    # Depth / deep
    (["depth","deep","profound"],
     ["deep","depth","profund","altus","immer"],
     0.65, "depth concept match"),
    # Work / labor
    (["work","action","labor"],
     ["work","labor","oper","actio","industri"],
     0.60, "work/labor concept match"),
    # Dew / generous
    (["dew","moist","generous","council"],
     ["dew","generous","ros","libera","benign","munific"],
     0.60, "dew/generosity concept match"),
    # Man / person
    (["man","foot","walk"],
     ["man","person","human","homo","vir","individ","pedestr"],
     0.60, "man/person/foot concept match"),
    # Back / surface / noon
    (["back","noon","power","above","surface"],
     ["back","dors","surface","noon","meridi","terg"],
     0.60, "back/surface concept match"),
    # Gold
    (["gold","gold coin","dinar"],
     ["gold","aurum","golden","chryso","dinar","denar","nummis"],
     0.80, "gold/coin concept match"),
    # Tax / tribute
    (["tax","tribute","contribution"],
     ["tax","tribute","contrib","tribut","vectig","stipend"],
     0.70, "tax/tribute concept match"),
    # Oven / furnace
    (["oven","furnace","tanur"],
     ["oven","furnace","clibanus","fornax","forn"],
     0.80, "oven/furnace concept match — تنور loanword"),
    # Rooster
    (["rooster","cock"],
     ["rooster","cock","gallus","alector"],
     0.70, "rooster/cock concept match"),
    # Riddle / enigma
    (["riddle","enigma","puzzle"],
     ["riddle","enigma","puzzle","aenigm","obscure"],
     0.75, "riddle/enigma concept match"),
    # Dry clay / earth
    (["dry clay","clod","mud brick","earth"],
     ["clay","earth","mud","argilla","lutum","loam"],
     0.60, "clay/earth concept match"),
    # Spread / expand
    (["spread","expand","carpet"],
     ["spread","expand","extend","open","expans","pateo"],
     0.60, "spread/expand concept match"),
    # Escape / flee
    (["escape","flee","run away"],
     ["escape","flee","fugit","fugae","effugio","elabo"],
     0.60, "escape/flee concept match"),
    # Silence / quiet
    (["silence","quiet","mute","still"],
     ["silence","quiet","silent","calm","tacit","taceo","still"],
     0.65, "silence/quiet concept match"),
    # Calm / truce
    (["calm","truce","pacify","calm","reassure","tranquil"],
     ["calm","truce","pacif","still","tranquil","placid","truce"],
     0.65, "calm/truce concept match"),
    # Regret / remorse
    (["regret","remorse","companion"],
     ["regret","remorse","poenitet","poenitent","dolor"],
     0.65, "regret/remorse concept match"),
    # Dig / excavate
    (["dig","excavate","hollow"],
     ["dig","excavat","hollow","foss","defod","delv"],
     0.65, "dig/excavate concept match"),
    # Protect / guard
    (["memorize","protect","guard","preserve"],
     ["protect","guard","preserv","custod","defendo","tutor"],
     0.60, "protect/guard concept match"),
    # Judge / rule / wisdom
    (["judge","rule","wisdom","command"],
     ["judge","rule","wisdom","command","judicat","rector"],
     0.60, "judge/rule concept match"),
    # Dream / patience
    (["dream","patience","forbear"],
     ["dream","patience","forbear","somnium","patiens","tolero"],
     0.60, "dream/patience concept match"),
    # Chickpea
    (["chickpea"],
     ["chickpea","cicer","legum"],
     0.80, "chickpea direct concept match"),
    # Belch / burp
    (["belch","burp","rise up"],
     ["belch","burp","eruct","ructus"],
     0.65, "belch/burp concept match"),
    # Crush / pound / grind
    (["crush","pound","sweep","clean well","pound fine","examine"],
     ["crush","pound","grind","tero","contund","pinsere"],
     0.60, "crush/pound concept match"),
    # Jump / leap
    (["jump","leap","hop"],
     ["jump","leap","hop","salio","saltus","exilio"],
     0.60, "jump/leap concept match"),
    # Illness / disease
    (["illness","disease","sick"],
     ["ill","disease","sick","morbus","aegrot","patholog"],
     0.65, "illness/disease concept match"),
    # Travel / depart
    (["travel","saddle","depart"],
     ["travel","depart","journey","iter","proficis","peregrin"],
     0.60, "travel/depart concept match"),
    # Condition / stipulation
    (["condition","stipulation","incision","cut","police"],
     ["condition","stipulat","pact","foedus","condit"],
     0.60, "condition/stipulation concept match"),
    # Lust / desire
    (["lust","desire","longing","longing","yearning","desire","love"],
     ["lust","desire","long","cupid","libidin","concupis"],
     0.60, "lust/desire concept match"),
    # Net / weave
    (["net","entangle","weave","intertwine"],
     ["net","weave","entangl","rete","plectere","nect"],
     0.60, "net/weave concept match"),
    # Youth / young
    (["youth","young","vigor"],
     ["youth","young","vigor","juven","iuven","puber","viridis"],
     0.60, "youth/vigor concept match"),
    # Stingy / miser
    (["stinginess","miser","greed","stingy"],
     ["stingy","miser","greed","avid","avar","parcimon"],
     0.60, "stingy/miser concept match"),
    # East / sunrise
    (["east","sunrise"],
     ["east","orient","oriens","solis"],
     0.65, "east/sunrise concept match"),
    # Pardon / forgive
    (["pardon","forgive","efface","erase","grass"],
     ["pardon","forgiv","erase","efface","absolver","remit"],
     0.65, "pardon/forgiveness concept match"),
    # Luxury / comfort
    (["luxury","comfort","ease","prosperity"],
     ["luxuri","comfort","ease","prosper","mollis","delicatus"],
     0.60, "luxury/comfort concept match"),
    # Melting / heat
    (["melt","son-in-law","family by marriage","heat"],
     ["melt","heat","liquefy","fuso","calor","fundere"],
     0.65, "melt/heat concept match"),
    # Group / crowd / troop
    (["group","troop","crowd","people","tribe","nation"],
     ["group","crowd","troop","popul","natio","cohort","turba","grex"],
     0.60, "group/crowd concept match"),
    # Carry / bear / load
    (["carry","bear","load","pregnancy"],
     ["carry","bear","load","ferre","porter","gest"],
     0.60, "carry/bear concept match"),
    # Forbid / prohibit
    (["fence","forbid","prohibit","enclosure"],
     ["forbid","prohibit","prohibeo","veto","interdico"],
     0.65, "forbid/prohibit concept match"),
    # Memory / recollect / narrate
    (["narrate","tell","imitate"],
     ["narrate","tell","recount","narrat","recit"],
     0.60, "narrate/tell concept match"),
    # Smile
    (["smile"],
     ["smile","rideo","ridere","risus"],
     0.65, "smile concept match"),
    # Dusk / twilight
    (["twilight","dawn glow","pity","compassion"],
     ["twilight","dawn","dusk","crepuscul","aurora"],
     0.60, "twilight/dawn concept match"),
    # Sword directly
    (["sword","blade","weapon"],
     ["sword","blade","weapon","ensis","gladius","spatha","saber","sabre"],
     0.80, "sword/blade concept match"),
    # Milk
    (["milk","Aleppo city"],
     ["milk","lac","lacti","galact"],
     0.65, "milk concept match"),
    # Field / farm
    (["field","farm","cultivate"],
     ["field","farm","cultivat","ager","agrarian","campus","arv"],
     0.65, "field/farm concept match"),
    # Weep / tear
    (["tear drop","weep"],
     ["weep","tear","lacrim","fletus","plorare"],
     0.65, "weep/tear concept match"),
    # Smoke / fume
    (["smoke","fume"],
     ["smoke","fume","fumus","vapor","fumig"],
     0.65, "smoke/fume concept match"),
    # Armor
    (["armor","coat of mail"],
     ["armor","armour","lorica","tegm","squama"],
     0.65, "armor concept match"),
    # Trample / thresh
    (["trample","press","thresh"],
     ["trample","thresh","press","calco","tero","conculc"],
     0.60, "trample/thresh concept match"),
    # Wound / scar
    (["wound crust","shout"],
     ["wound","scar","vulnus","cicatrix","laesio"],
     0.55, "wound/scar concept match"),
    # Content / satisfied
    (["content","satisfied","please"],
     ["content","satisf","pleas","placid","gratus"],
     0.60, "content/satisfaction concept match"),
    # Trot / walk
    (["trot","quick walk"],
     ["trot","walk","ambul","incessus","grad"],
     0.50, "trot/walk concept match"),
    # Proof / evidence
    (["prove","demonstrate","evidence"],
     ["proof","evident","probo","demonstrat","testis"],
     0.65, "prove/evidence concept match"),
    # Time / age / era
    (["time","age","era","fate"],
     ["time","age","era","tempus","aetas","saecul"],
     0.60, "time/age/era concept match"),
    # Iron / metal
    (["metal","ore","mineral"],
     ["metal","ore","iron","mineral","ferrum","aes","metallum"],
     0.70, "metal/ore concept match"),
    # Millstone / grind
    (["millstone","grind"],
     ["millstone","grind","mola","molere","pinsere"],
     0.70, "millstone/grind concept match"),
    # Musk / skin / grasp
    (["musk","hold","grasp","skin"],
     ["musk","grasp","hold","skin","pellis","cori"],
     0.60, "musk/skin concept match"),
    # Path / gate / practice
    (["practice","path","gate"],
     ["path","gate","way","via","porta","pass"],
     0.55, "path/gate concept match"),
]

def score_pair(pair):
    arabic_root = pair.get("arabic_root", "")
    target_lemma = pair.get("target_lemma", "")
    masadiq_gloss = pair.get("masadiq_gloss", "")
    target_gloss = pair.get("target_gloss", "")
    tg = target_gloss.lower()

    # Rule 1: Proper nouns → 0.0
    if is_proper(target_gloss):
        return _out(arabic_root, target_lemma, 0.0,
                    "proper noun/place name — no semantic cognate value")

    # Rule 2: Pure grammatical forms (no semantic content) → 0.0
    if is_gram_form_only(target_gloss):
        return _out(arabic_root, target_lemma, 0.0,
                    "grammatical form entry — no semantic content to compare")

    # Rule 3: Unknown root → 0.0
    ar_meanings = MASADIQ.get(arabic_root, [])
    if not ar_meanings:
        return _out(arabic_root, target_lemma, 0.0,
                    "Arabic root not in masadiq lexicon — cannot score")

    # Rule 4: Apply concept rules (masadiq-first)
    for (ar_subset, tgt_kws, score, tag) in CONCEPT_RULES:
        ar_hit = any(m in ar_meanings for m in ar_subset)
        tg_hit = any(k in tg for k in tgt_kws)
        if ar_hit and tg_hit:
            return _out(arabic_root, target_lemma, score, tag)

    # Rule 5: Generic stem overlap fallback
    tg_words = set(re.findall(r'\b\w{4,}\b', tg))
    for m in ar_meanings:
        for mw in re.findall(r'\b\w{4,}\b', m.lower()):
            for tw in tg_words:
                if mw == tw or (len(mw) >= 5 and (mw[:5] == tw[:5])):
                    return _out(arabic_root, target_lemma, 0.40,
                                f"stem overlap '{mw}'/'{tw}' — weak", "weak")

    return _out(arabic_root, target_lemma, 0.0, "no semantic overlap found")


# ── Main processing loop ────────────────────────────────────────────────────

all_results = []

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
    print(f'Chunk {chunk_id}: {len(scored)} pairs, {len(high)} >= 0.5')
    all_results.extend(scored)

# ── Summary ─────────────────────────────────────────────────────────────────

total = len(all_results)
total_high = sum(1 for r in all_results if r['semantic_score'] >= 0.5)
print(f'\nTOTAL: {total} pairs, {total_high} >= 0.5')

top = sorted(all_results, key=lambda x: x['semantic_score'], reverse=True)
print('\nTOP 20 DISCOVERIES:')
seen = set()
shown = 0
for r in top:
    key = (r['source_lemma'], r['target_lemma'])
    if key not in seen and shown < 20:
        seen.add(key)
        shown += 1
        print(f"  {r['semantic_score']:.2f}  {r['source_lemma']:18s}  "
              f"{r['target_lemma']:25s}  {r['reasoning'][:65]}")
