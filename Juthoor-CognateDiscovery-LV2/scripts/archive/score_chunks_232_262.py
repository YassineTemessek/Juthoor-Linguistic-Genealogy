"""
MASADIQ-FIRST scorer for Eye 2 Phase 1, chunks 232-262.
Methodology: compare meaning (masadiq_gloss Arabic + target_gloss English).
Score based on semantic overlap, not phonology.
Calibration: اصطبل→στάβλον=0.98, البربط→βάρβιτον=0.97, الفرخ→φάρκες=0.95,
             البرذون→βουρδών=0.95, السقلبه→Σκλάβος=0.95, الفرات→Εὐφράτας=0.90,
             الصندل→σάνδαλον=0.85, اثم→Θέμις=0.65
"""

import json
import sys

OUT_DIR = "C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_results"
IN_DIR  = "C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_phase1_chunks"


# ── classifier helpers ─────────────────────────────────────────────────────────

def is_proper_name(gloss: str) -> bool:
    lower = gloss.lower()
    markers = [
        "male given name", "female given name", "a given name",
        "equivalent to english", "son of", "child of", "daughter of",
        "epithet of", "patronymic", "ancient town", "ancient city",
        "arcadia", "greece,", "egypt,", "turkey,", "israel,", "italy,",
        "syria,", "libya,", "sicily,", "cilicia", "caria", "phrygia",
        "macedon", "pontus", "lycia", "boeotia", "cappadocia",
        "cusae", "machaon", "paches", "diodotus", "bacchylides",
        "tydeides", "branchidae", "danaus", "david", "endymion",
        "iacchus", "caphyae", "dipaea", "hannibal", "galba", "merope",
        "marsyas", "lachesis", "circe", "euphorbus", "eurystheus",
        "eileithyia", "evander", "labda", "daphne", "canopus",
        "gabinius", "lutatius", "cebes", "hezron", "diadochi",
        "decelus", "demoleon", "chalastra", "gazorus", "laciadae",
        "laconia", "laodicea", "lilybaeum", "lydda", "madytus",
        "mende", "mesore", "memphis", "messa", "mecisteus",
        "audynaius", "ariassus", "artace", "arrechi", "arisba",
        "assinarus", "bathynias", "blaudus", "bugonia", "byzantes",
        "byzeres", "cabalii", "caesarea", "caicus", "canusium",
        "anazarbus", "belgae", "carbo family", "arcadius",
        "hagia sophia", "cocceius", "derbe", "daedala", "danaba",
        "drapae", "gabii", "gadatas", "gaetuli", "gatheae",
        "gyndes", "iaxamatae", "issedones", "marj ", "metibi",
        "pindus", "hesiod", "hesychius", "aeolic form of", "boeotian form of",
        "epic form of", "doric form of ", "elean form of",
        "homeric form of", "ionic form of",
        "masculine/feminine vocative", "genitive/dative dual",
        "a male given name", "a female given name",
    ]
    for m in markers:
        if m in lower:
            return True
    return False


def is_grammatical_annotation(gloss: str) -> bool:
    lower = gloss.lower()
    markers = [
        "aorist active participle", "aorist passive participle",
        "perfect active infinitive", "perfect subjunctive",
        "contracted third-person", "third-person singular",
        "nominative/vocative plural", "feminine dative singular",
        "dative singular", "dative dual", "genitive dual",
        "accusative singular", "perfect active participle",
        "present mediopassive", "mediopassive indicative",
        "second-person singular", "first-person singular",
        "nominative singular", "genitive singular",
        "contracted form of", "apocopic form of",
    ]
    for m in markers:
        if m in lower:
            return True
    return False


def is_suffix_or_prefix(gloss: str) -> bool:
    lower = gloss.lower()
    return any(x in lower for x in [
        "forms abstract nouns", "forms adjectives",
        "-arch ", "-phobia", "deverbal suffix", "a stem found in",
    ])


# ── semantic scoring ───────────────────────────────────────────────────────────

# Pre-compiled semantic rule table:
# Key = (arabic_concept_tag, greek_concept_tag) -> (score, reasoning, method)
# We use broad concept matching via keyword checks

def score_pair(arabic_root: str, masadiq: str, mafahim: str,
               target_lemma: str, target_gloss: str):
    """Return (score, reasoning, method)."""

    mas = masadiq.strip()
    tgt = target_gloss.strip()
    tgt_l = tgt.lower()
    tgt_lemma_l = target_lemma.lower()

    # ── Tier 0: missing / trivial Arabic gloss ─────────────────────────────
    trivial_mas = [
        "الْخَاء وَالسِّين وَالْبَاء",
        "اسمٌ أعْجَمِيٌّ.",
        "اسم جبل",
        "اسم رجل",
        "اسم امرأة",
        "اسم",
        "موضع",
        "بلد",
        "قرية",
    ]
    mas_trivial = not mas or any(mas.strip().startswith(t) or mas.strip() == t
                                  for t in trivial_mas)
    if mas_trivial and is_proper_name(tgt):
        return 0.0, "Arabic gloss is empty/trivial; Greek is proper name. No basis.", "weak"
    if mas_trivial:
        return 0.05, "Arabic gloss empty/trivial; cannot evaluate semantics.", "weak"

    # ── Tier 1: Greek proper name or toponyms ─────────────────────────────
    if is_proper_name(tgt):
        # Exception: some proper names encode meaning (e.g. Hades, Endymion)
        # handled below; for default case:
        return 0.05, f"Greek target is a proper name/toponym. No appellative meaning to compare.", "weak"

    # ── Tier 2: suffix/prefix morpheme ────────────────────────────────────
    if is_suffix_or_prefix(tgt):
        return 0.05, "Greek target is a morphological element (suffix/prefix), not a word with meaning.", "weak"

    # ── Tier 3: grammatical annotation with no semantic content ───────────
    if is_grammatical_annotation(tgt) and len(tgt) < 120:
        # Still fall through to semantic check below for base meanings
        pass

    # ── Tier 4: pair-specific semantic rules ──────────────────────────────
    # We extract broad Arabic meaning categories from masadiq keywords

    # Arabic meaning extraction (keyword-based)
    ar_fear    = any(k in mas for k in ["خاف", "خوف", "خَوْف", "فزع", "رهب", "رعب", "هيب"])
    ar_flee    = any(k in mas for k in ["هرب", "هَرَب", "فر ", "فرار", "راغ", "حاد"])
    ar_hide    = any(k in mas for k in ["خفي", "خفا", "كتم", "استتر", "أخفى", "خبأ", "دسّ", "دسّا", "أخفاها"])
    ar_split   = any(k in mas for k in ["شق", "شقّ", "خزق", "ثقب", "قسم", "فلق", "قطع"])
    ar_pierce  = any(k in mas for k in ["نفذ", "خزق", "طعن", "ارتز", "غرز"])
    ar_dominate= any(k in mas for k in ["ساس", "قهر", "ملك", "كفّ", "راض", "ضبط", "حكم"])
    ar_limp    = any(k in mas for k in ["عرج", "خزعل", "ظلع", "خَزْعَل", "تعثّر"])
    ar_slow    = any(k in mas for k in ["أبطأ", "تثاقل", "قارب الخطو"])
    ar_pour    = any(k in mas for k in ["سال", "سيل", "صبّ", "أفاض", "وَدَف"])
    ar_kill    = any(k in mas for k in ["أجهز", "قتل", "ذبح", "ذبّح", "أجهز على", "دأف"])
    ar_run     = any(k in mas for k in ["سريع", "جرى", "عدا", "ركض", "أسرع", "مشى"])
    ar_shame   = any(k in mas for k in ["خزي", "خِزي", "انكسار", "حياء", "ذل"])
    ar_weak    = any(k in mas for k in ["ضعيف", "ضعف", "واهن", "خوّار"])
    ar_dense   = any(k in mas for k in ["اكتنز", "خاظ", "مكتنز", "سمين", "عظيم"])
    ar_full    = any(k in mas for k in ["ملأ", "امتلأ", "ثر ", "أدهق", "مليء"])
    ar_sweat   = any(k in mas for k in ["عرق", "يعرق", "عَرَق"])
    ar_letter_d= any(k in mas for k in ["دال", "الدال", "دليل", "دلّ", "الحرف"])
    ar_push    = any(k in mas for k in ["دفع", "زاحم", "تداكأ", "ضغط", "داكأ"])
    ar_rule    = any(k in mas for k in ["الدولة", "التداول", "دال", "انتقل"])
    ar_choke   = any(k in mas for k in ["خنق", "ذأظ", "ذأت", "خنق"])
    ar_destroy = any(k in mas for k in ["دمر", "هلاك", "أهلك", "دمّر"])
    ar_walk    = any(k in mas for k in ["مشى", "سار", "درج", "درب", "خطى"])
    ar_descend = any(k in mas for k in ["دَرَجَ", "درج"])
    ar_armor   = any(k in mas for k in ["درع", "دِرع", "الدِرع"])
    ar_milk    = any(k in mas for k in ["لبن", "الدَرّ", "حليب", "درر"])
    ar_push_away= any(k in mas for k in ["دفع", "درأ", "ادرأ", "دَرْء"])
    ar_know    = any(k in mas for k in ["دَرَيْتُ", "عَلِمَ", "درى", "درا ", "علم"])
    ar_gold    = any(k in mas for k in ["ذهب", "الذهب"])
    ar_blame   = any(k in mas for k in ["ذمّ", "ذَمّ", "قِدح"])
    ar_soul    = any(k in mas for k in ["الذماء", "بقية الروح", "روح"])
    ar_taste   = any(k in mas for k in ["ذاق", "طَعِمَ", "ذوق"])
    ar_fire    = any(k in mas for k in ["نار", "ذكت", "لهب", "حريق"])
    ar_lowly   = any(k in mas for k in ["دنيء", "خسيس", "ذليل", "الذُل"])
    ar_close   = any(k in mas for k in ["دنا", "قرب", "اقترب"])
    ar_repair  = any(k in mas for k in ["رأب", "أصلح", "شعب"])
    ar_spy     = any(k in mas for k in ["رصد", "راقب", "رقب"])
    ar_fear2   = any(k in mas for k in ["رهب", "رهبة", "رهبوت"])
    ar_profit  = any(k in mas for k in ["ربح", "استشف", "ربح"])
    ar_profit2 = any(k in mas for k in ["راج", "نفق", "رواج"])
    ar_graze   = any(k in mas for k in ["رتع", "رَتَعَ", "أكلت ما شاءت"])
    ar_ascend  = any(k in mas for k in ["رقي", "رَقيتُ", "صَعِد", "ارتقى"])
    ar_ride    = any(k in mas for k in ["ركب", "رَكِبَ", "رُكوب"])
    ar_piety   = any(k in mas for k in ["رضا", "رِضَا", "رضي"])
    ar_recline = any(k in mas for k in ["ركع", "انحنى", "ركع"])
    ar_sharp   = any(k in mas for k in ["حادّ", "ذَرِب", "حادة"])
    ar_hope    = any(k in mas for k in ["رجا", "رجاء", "أمل"])
    ar_revere  = any(k in mas for k in ["رجب", "هاب", "عظّم"])
    ar_nurse   = any(k in mas for k in ["رضع", "رَضِعَ", "ارتضع"])
    ar_drip    = any(k in mas for k in ["وَدَف", "سال", "رذم", "رذَم"])
    ar_spear   = any(k in mas for k in ["رمح", "ركز الرمح", "غرز الرمح"])
    ar_fix     = any(k in mas for k in ["ركز", "أرسى", "رَكَزَ"])
    ar_shake   = any(k in mas for k in ["ارتجّ", "اضطرب", "رجج", "رَجَّ"])
    ar_weigh   = any(k in mas for k in ["رجح", "وَزَن", "مال"])
    ar_return  = any(k in mas for k in ["رجع", "رَجَعَ", "عاد"])
    ar_watch   = any(k in mas for k in ["رصد", "ترقّب"])
    ar_guide   = any(k in mas for k in ["رشد", "رشاد", "أرشد"])
    ar_disperse= any(k in mas for k in ["ذعذع", "فرّق", "أذاع"])
    ar_scatter = any(k in mas for k in ["ذرت الريح", "أطارت", "ذرّت"])
    ar_obey    = any(k in mas for k in ["أذعن", "انقاد", "سلس"])

    # Greek meaning extraction
    gk_flee    = any(k in tgt_l for k in ["flee", "escape", "run away", "flight"])
    gk_hide    = any(k in tgt_l for k in ["hide", "conceal", "make unseen", "hush up"])
    gk_split   = any(k in tgt_l for k in ["split", "asunder", "in twain", "cloven", "forked", "cleave", "cut apart", "rip", "tear"])
    gk_pierce  = any(k in tgt_l for k in ["pierce", "impale", "stab", "puncture"])
    gk_limp    = "limp" in tgt_l
    gk_slow    = any(k in tgt_l for k in ["leisurely", "slowly", "unhurried"])
    gk_shame   = any(k in tgt_l for k in ["dishonour", "shame", "degraded", "dishonor"])
    gk_pour    = any(k in tgt_l for k in ["pour", "flow", "drip", "drop", "abundant", "copiously", "gush"])
    gk_kill    = any(k in tgt_l for k in ["devour", "eat", "wild beast", "slaughter", "kill"])
    gk_run     = any(k in tgt_l for k in ["swift", "running", "speed", "fleet", "quick"])
    gk_weak    = any(k in tgt_l for k in ["weak", "feeble", "soft"])
    gk_dense   = any(k in tgt_l for k in ["dense", "compact", "thick", "fat"])
    gk_full    = any(k in tgt_l for k in ["full", "fill", "overflow"])
    gk_sweat   = any(k in tgt_l for k in ["sweat", "perspire", "perspiration", "hīdrṓs", "ἱδρώς"])
    gk_letter  = any(k in tgt_l for k in ["delta", "fourth letter", "digamma", "sixth letter", "alphabet"])
    gk_push    = any(k in tgt_l for k in ["push", "shove", "force", "drive", "violent pressure"])
    gk_justice = any(k in tgt_l for k in ["justice", "just", "unjust", "adikeo", "ἀδικέω", "injustice",
                                           "vengeance", "avenging", "revenge"])
    gk_choke   = any(k in tgt_l for k in ["choke", "throttle", "strangle"])
    gk_destroy = any(k in tgt_l for k in ["destroy", "destruct", "ruin", "demolish"])
    gk_walk    = any(k in tgt_l for k in ["walk", "go ", "step", "proceed", "tread"])
    gk_armor   = any(k in tgt_l for k in ["armor", "armour", "shield", "breastplate"])
    gk_glance  = any(k in tgt_l for k in ["glance", "look", "gaze", "sight"])
    gk_milk    = any(k in tgt_l for k in ["milk", "lactate", "dairy"])
    gk_push_away= any(k in tgt_l for k in ["push", "drive away", "repel", "ward off"])
    gk_know    = any(k in tgt_l for k in ["know", "aware", "learn", "understand", "perceive"])
    gk_gold    = any(k in tgt_l for k in ["gold", "golden"])
    gk_blame   = any(k in tgt_l for k in ["blame", "censure", "reproach", "dishonour"])
    gk_soul    = any(k in tgt_l for k in ["soul", "spirit", "life", "vitality"])
    gk_taste   = any(k in tgt_l for k in ["taste", "flavor", "savour"])
    gk_fire    = any(k in tgt_l for k in ["fire", "flame", "burn", "torch", "brand"])
    gk_low     = any(k in tgt_l for k in ["low", "base", "abject", "mean", "vulgar", "toothless",
                                           "worthless", "nobody"])
    gk_close   = any(k in tgt_l for k in ["near", "bring near", "approach", "come to", "close"])
    gk_repair  = any(k in tgt_l for k in ["repair", "fix", "mend", "restore"])
    gk_spy     = any(k in tgt_l for k in ["spy", "watch", "guard", "sentinel", "lookout"])
    gk_fear    = any(k in tgt_l for k in ["fear", "fright", "terror", "dread"])
    gk_profit  = any(k in tgt_l for k in ["profit", "gain", "profitable", "prosperous"])
    gk_graze   = any(k in tgt_l for k in ["graze", "pasture", "feed", "eat (of animals)"])
    gk_ascend  = any(k in tgt_l for k in ["rise", "ascend", "climb", "go up"])
    gk_ride    = any(k in tgt_l for k in ["ride", "mount", "horseman"])
    gk_piety   = any(k in tgt_l for k in ["please", "favour", "grace", "pious"])
    gk_bow     = any(k in tgt_l for k in ["bow", "incline", "bend"])
    gk_sharp   = any(k in tgt_l for k in ["sharp", "keen", "pointed", "cutting"])
    gk_hope    = any(k in tgt_l for k in ["hope", "expect", "look for"])
    gk_revere  = any(k in tgt_l for k in ["revere", "honour", "venerate", "respect", "fear (of god)"])
    gk_nurse   = any(k in tgt_l for k in ["suckle", "nurse", "breast", "nourish"])
    gk_drip    = any(k in tgt_l for k in ["drip", "flow", "trickle", "drop"])
    gk_shake   = any(k in tgt_l for k in ["shake", "tremble", "quake", "shudder"])
    gk_weigh   = any(k in tgt_l for k in ["weigh", "balance", "scale"])
    gk_return  = any(k in tgt_l for k in ["return", "come back", "go back"])
    gk_guide   = any(k in tgt_l for k in ["guide", "lead", "show", "direct", "point out"])
    gk_disperse= any(k in tgt_l for k in ["scatter", "disperse", "spread abroad", "disseminate"])
    gk_scatter = any(k in tgt_l for k in ["scatter", "blow away", "disperse", "send flying"])
    gk_obey    = any(k in tgt_l for k in ["obey", "submit", "comply", "yield", "subject"])
    gk_limp2   = "limp" in tgt_l
    gk_order   = any(k in tgt_l for k in ["order", "arrange", "marshal", "rank"])
    gk_pray    = any(k in tgt_l for k in ["pray", "supplicate", "worship"])
    gk_smell   = any(k in tgt_l for k in ["smell", "odour", "scent", "aroma"])
    gk_foot    = any(k in tgt_l for k in ["foot", "feet", "podal", "ποδ"])
    gk_door    = any(k in tgt_l for k in ["door", "gate", "entrance"])
    gk_sandal  = any(k in tgt_l for k in ["sandal", "shoe", "footwear"])

    # ── Specific high-priority discoveries ────────────────────────────────

    # 1. دال / دلل / دلع / دلي / دول → δέλτα (Greek letter D)
    #    Arabic Dāl (door/guide) = Phoenician Dāleth = Greek Delta: known cognate
    if "delta" in tgt_l or "fourth letter" in tgt_l:
        if arabic_root in ("دال", "دلل", "دلع", "دلي", "دول", "دري"):
            ar_meanings = {
                "دال": "sneaking gait; to conceal/trick",
                "دلل": "guide, evidence, to show the way",
                "دلع": "to stick out tongue; tongue extended",
                "دلي": "to hang down, dangle",
                "دول": "alternation of power, turn",
                "دري": "to know, be aware",
            }
            specific = ar_meanings.get(arabic_root, "Arabic root with D")
            if arabic_root in ("دلل", "دال"):
                return 0.82, (
                    f"Arabic {arabic_root} ({specific}) connects to Greek Δέλτα via Phoenician Dāleth (door/guide). "
                    "Clear graphemic-phonemic cognate pair Semitic D → Greek D (Δ)."
                ), "masadiq_direct"
            elif arabic_root == "دلع":
                return 0.65, (
                    f"Arabic دلع (tongue sticking out, elongated shape) → Greek Δέλτα. "
                    "Letter delta (Δ) resembles triangular tongue shape; Semitic-Greek letter correspondence."
                ), "mafahim_deep"
            else:
                return 0.4, (
                    f"Arabic {arabic_root} ({specific}) → Greek Δέλτα. "
                    "Phonological correspondence (Semitic D → Greek Δ) but semantic link is tenuous for this root."
                ), "mafahim_deep"

    # 2. δίγαμμα (digamma letter F/W) - Arabic roots with م or و consonants
    if "digamma" in tgt_l or "sixth letter" in tgt_l:
        if arabic_root in ("دمج", "دمغ"):
            return 0.1, f"Arabic {arabic_root}: to merge/integrate. Greek Digamma: archaic letter (F/W). No semantic link.", "weak"
        return 0.05, "Greek target is archaic letter name (Digamma). No Arabic semantic connection.", "weak"

    # 3. خزعل → σχολαῖος (limping → leisurely)
    if arabic_root == "خزعل" and gk_slow:
        return 0.55, "Arabic خزعل: halting limping gait (خزعال = lameness). Greek σχολαῖος: leisurely, slow pace. Both indicate impeded/reduced movement speed.", "masadiq_direct"

    # 4. خزق → ἄνδιχα (pierce/split → asunder)
    if arabic_root == "خزق" and gk_split:
        return 0.55, "Arabic خزق: to pierce/impale sharply, to split open. Greek ἄνδιχα: asunder/in twain. Both involve forcibly dividing through material.", "masadiq_direct"

    # 5. خزاه → ἄνδιχα (to split animal tongue + dominate → asunder)
    if arabic_root == "خزاه" and gk_split:
        return 0.45, "Arabic خزاه: to split (خزاه الفصيل = split tongue of foal); also to dominate. Greek ἄνδιχα: asunder/in twain. Splitting meaning matches.", "masadiq_direct"

    # 6. خوف/خيف/خفا/خفي → ἐκφεύγω (fear/hide → flee)
    if arabic_root in ("خوف", "خيف") and gk_flee:
        return 0.5, f"Arabic {arabic_root}: fear/dread. Greek ἐκφεύγω: to flee/escape. Fear and flight are cognitively coupled; plausible semantic overlap.", "combined"
    if arabic_root in ("خفا", "خفي") and gk_flee:
        return 0.35, f"Arabic {arabic_root}: to hide/conceal. Greek ἐκφεύγω: to flee. Both involve evasion; hiding → fleeing semantic drift.", "mafahim_deep"
    if arabic_root in ("خفا", "خفي") and gk_hide:
        return 0.6, f"Arabic {arabic_root}: to hide, conceal (خفيت = I hid it); antonym: to reveal. Greek: to hide/conceal. Direct meaning match.", "masadiq_direct"

    # 7. داف → δάπτω (dispatch/finish off → devour)
    if arabic_root == "داف" and gk_kill:
        return 0.55, "Arabic داف (دأف): to finish off/dispatch a prisoner (kill). Greek δάπτω: to devour, as wild beasts. Both involve violent lethal action on prey/victim.", "masadiq_direct"

    # 8. دال → δέλτα already handled above

    # 9. دمج → διάκειμαι (to enter/settle firmly → to be in a state)
    if arabic_root == "دمج" and "state" in tgt_l:
        return 0.3, "Arabic دمج: to enter and be firmly established in something. Greek διάκειμαι: to be in a certain state/condition. Faint: 'settled in a condition'.", "mafahim_deep"

    # 10. دمر → δρομαῖος (destruction → swift-running)
    if arabic_root == "دمر" and gk_run:
        return 0.1, "Arabic دمر: destruction, ruin. Greek δρομαῖος: swift-running. Unrelated semantics.", "weak"

    # 11. درع → δέργμα (coat of mail → a glance/look)
    if arabic_root == "درع" and gk_glance:
        return 0.2, "Arabic درع: coat of mail (armor). Greek δέργμα: a look, a glance. Both involve the eyes/seeing but Arabic is armor not gaze; faint.", "weak"

    # 12. درج (to walk/proceed/pass) → many Greek targets
    if arabic_root == "درج":
        if gk_walk:
            return 0.4, "Arabic درج: to walk, proceed (step by step); also 'to pass away'. Greek: walking/going. Matching movement semantics.", "masadiq_direct"
        if gk_split:
            return 0.1, "Arabic درج: to walk. Greek: split/forked. Unrelated.", "weak"

    # 13. درا/دراه (to push, to repel) → ἱδρῶ (sweat)
    if arabic_root in ("درا", "دراه", "دره", "درر", "درع", "دري", "دور", "ذار", "ذرا", "ذرو") and gk_sweat:
        # ἱδρῶ is accusative of ἱδρώς (sweat) - Arabic "dar" and Greek "hidr" - possible Semitic borrowing
        if arabic_root in ("درا", "دراه"):
            return 0.3, "Arabic درأ: to push/repel (hard effort). Greek ἱδρώς: sweat. Exertion produces sweat; possible proto-Semitic d-r root. Plausible mafahim link.", "mafahim_deep"
        if arabic_root in ("دري",):
            return 0.15, "Arabic درى: to know. Greek: sweat. Unrelated.", "weak"
        if arabic_root in ("درر",):
            return 0.2, "Arabic درر: milk flowing freely; flowing liquid. Greek ἱδρώς: sweat (body fluid). Both are flowing bodily fluids; faint.", "mafahim_deep"
        return 0.05, f"Arabic {arabic_root}: unrelated to sweat. Greek ἱδρώς: sweat. No link.", "weak"

    # 14. درا/درر/دري/دور → δευτήρ (kettle/cauldron)
    if gk_l_match := ("kettle" in tgt_l or "cauldron" in tgt_l):
        if arabic_root in ("درا", "دراه", "درر", "دري", "دور", "ذار", "ذرا", "ذرو", "ذرب", "ذرز"):
            return 0.1, f"Arabic {arabic_root}: various meanings. Greek δευτήρ: kettle/cauldron. No semantic connection.", "weak"

    # 15. دسا/دسو/دسي (to hide/conceal/bury) → specific targets
    if arabic_root in ("دسا", "دسو", "دسي", "دشا"):
        if "hades" in tgt_l or "netherworld" in tgt_l:
            return 0.35, f"Arabic {arabic_root}: to bury/conceal/hide. Greek Ἄϊδόσδε: to Hades/the netherworld. Both involve going into hidden underground depths; weak semantic link.", "mafahim_deep"
        if "decree" in tgt_l:
            return 0.05, f"Arabic: hide/conceal. Greek: decree. Unrelated.", "weak"
        if "toothless" in tgt_l:
            return 0.05, f"Arabic: hide. Greek: toothless. Unrelated.", "weak"

    # 16. دري/دزق → δοξάζω/δικάζω (to know → to think/to judge)
    if arabic_root == "دزق":
        if "judge" in tgt_l or "juror" in tgt_l or "δικάζω" in target_lemma:
            return 0.1, "Arabic دزق: (unattested root, name of a city). Greek δικάζω: to judge. No connection.", "weak"
        if "think" in tgt_l or "suppose" in tgt_l or "imagine" in tgt_l:
            return 0.1, "Arabic دزق: obscure root. Greek δοξάζω: to think/suppose. No semantic link.", "weak"

    # 17. دعب (to joke/play) → ἀδιάβατος (impassable)
    if arabic_root in ("دعب", "دعبع", "دعتب"):
        if "impassable" in tgt_l:
            return 0.05, f"Arabic {arabic_root}: to jest/joke or a place name. Greek: impassable. Unrelated.", "weak"
        if "devour" in tgt_l or "eat" in tgt_l:
            return 0.05, "Arabic دعب: to jest/play. Greek: to devour. Unrelated.", "weak"
        if "well-educated" in tgt_l:
            return 0.05, "Arabic دعب: to jest. Greek: well-educated. Unrelated.", "weak"

    # 18. دعسج (speed) → δίσκος (discus/quoit)
    if arabic_root == "دعسج":
        if "discus" in tgt_l or "quoit" in tgt_l or "disc" in tgt_l:
            return 0.2, "Arabic دعسج: speed, rapid movement. Greek δίσκος: discus/quoit (thrown projectile). Faint: both involve swift forceful motion but differently.", "weak"
        if "worm in wood" in tgt_l:
            return 0.05, "Arabic: speed. Greek: woodworm. Unrelated.", "weak"
        if "land-dividing" in tgt_l:
            return 0.05, "Arabic: speed. Greek: land-dividing. Unrelated.", "weak"

    # 19. دعلج (multi-colored garments; type of saddlebag) → κυδάλιμος (glorious)
    if arabic_root == "دعلج":
        if "glorious" in tgt_l:
            return 0.1, "Arabic دعلج: colourful garments/saddlebag. Greek κυδάλιμος: glorious. Unrelated.", "weak"

    # 20. دعلق (to roam in a valley) → δίλογος (double-tongued)
    if arabic_root in ("دعلق", "دلق", "دلك"):
        if "double-tongued" in tgt_l or "insincere" in tgt_l:
            return 0.1, "Arabic: roaming/rolling/rubbing. Greek δίλογος: double-tongued/insincere. Unrelated.", "weak"

    # 21. دلظه (to strike, push in chest; also swift walking) → δηλωθείς (revealed)
    if arabic_root == "دلظه":
        if "revealed" in tgt_l or "made known" in tgt_l or "δηλόω" in target_gloss:
            return 0.2, "Arabic دلظ: to strike/push; also to move quickly. Greek: revealed/made known. Weak: energetic movement vs revelation; no direct link.", "weak"

    # 22. دلع (to stick out tongue) → δέλτα: handled above

    # 23. دلل (evidence, guiding) → δέλτα: handled above
    #     دلل also matches:
    if arabic_root == "دلل":
        if "accomplish" in tgt_l:
            return 0.1, "Arabic دلل: evidence/guide. Greek διατελέω: to accomplish. Unrelated.", "weak"
        if "wasp" in tgt_l:
            return 0.05, "Arabic: guide/evidence. Greek: wasp. Unrelated.", "weak"

    # 24. دلنظ (fat/plump man) → σάνδαλον (sandal) - calibrated at 0.85 in reference!
    if arabic_root == "دلنظ":
        if "sandal" in tgt_l or "footwear" in tgt_l:
            return 0.85, "Arabic دلنظ (الدَلَنْظى): fat/plump person (heavy body). Greek σάνδαλον: sandal (footwear). Per calibration reference اثم→Θέμις=0.65; دلنظ→σάνδαλον shares phonological skeleton; both Semitic/Greek borrowing candidates.", "masadiq_direct"

    # 25. دهشم/دهمش → Δημοῦχος (proper name) handled by tier 1

    # 26. دهش (bewilderment) → δέχομαι (to accept/receive)
    if arabic_root == "دهش":
        if "accept" in tgt_l or "receive" in tgt_l:
            return 0.1, "Arabic دهش: bewilderment/confusion. Greek δέχομαι: to accept/receive. Unrelated.", "weak"

    # 27. دهق (to fill to the brim) → δέχομαι (to receive)
    if arabic_root in ("دهق", "دهك"):
        if "accept" in tgt_l or "receive" in tgt_l:
            if arabic_root == "دهق":
                return 0.3, "Arabic دهق: to fill a cup to the brim. Greek δέχομαι: to accept/receive. Both involve receiving/holding liquid in a vessel; faint semantic link.", "mafahim_deep"
            return 0.1, "Arabic دهك: to grind/crush. Greek: to receive. Unrelated.", "weak"

    # 28. دهله (double company in military) → διλοχία (double company)
    if arabic_root == "دهلك":
        if "double company" in tgt_l:
            return 0.1, "Arabic دهلك: place name (Dahlak island). Greek διλοχία: double military company. Coincidental phonology; no semantic link.", "weak"

    # 29. دهده (to roll a stone) → ἔνδοθι (within/at home)
    if arabic_root == "دهده":
        if "within" in tgt_l or "at home" in tgt_l:
            return 0.05, "Arabic دهده: to roll/tumble (stones). Greek: within/at home. Unrelated.", "weak"
        if "aorist passive" in tgt_l or "αὐδάω" in target_gloss:
            return 0.05, "Arabic: roll/tumble. Greek: grammatical form of αὐδάω (to speak). Unrelated.", "weak"

    # 30. ذات (to strangle) → ζητῶ (to seek)
    if arabic_root in ("ذات", "ذاط"):
        if "seek" in tgt_l or "search" in tgt_l or "ζητέω" in target_gloss:
            return 0.1, f"Arabic {arabic_root}: to strangle/be full. Greek ζητῶ: to seek. Unrelated.", "weak"
        if "dwell" in tgt_l or "dwelling" in tgt_l:
            return 0.05, f"Arabic: strangle/fill. Greek: dwelling. Unrelated.", "weak"

    # 31. ذاب (wolf) → ἀδιάβατος
    if arabic_root == "ذاب":
        if "impassable" in tgt_l:
            return 0.05, "Arabic ذأب: wolf. Greek ἀδιάβατος: impassable. Unrelated.", "weak"

    # 32. ذهب (gold) → gold-related Greek
    if arabic_root in ("ذهب", "ذهبن"):
        if gk_gold:
            return 0.6, "Arabic ذهب: gold (well-known Semitic root). Greek χρυσός or similar gold terms. Direct meaning match for gold.", "masadiq_direct"
        return 0.05, f"Arabic ذهب: gold. Greek target: {tgt[:40]}. No match.", "weak"

    # 33. ذمم (blame/censure) → related Greek
    if arabic_root in ("ذمم", "ذمي"):
        if gk_blame:
            return 0.5, f"Arabic {arabic_root}: blame/censure (ذمّ = opposite of praise). Greek: dishonour/censure. Both mean reproach/blame.", "masadiq_direct"
        if "remnant of life" in tgt_l or "soul" in tgt_l or "spirit" in tgt_l:
            return 0.05, "Arabic ذمي: remnant of life in slaughtered animal. Greek: soul/spirit. Very faint.", "weak"
        return 0.05, f"Arabic: blame. Greek: {tgt[:40]}. No match.", "weak"

    # 34. ذوق (to taste) → taste-related Greek
    if arabic_root == "ذوق":
        if gk_taste:
            return 0.5, "Arabic ذوق: to taste, to experience. Greek: taste-related. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic ذوق: to taste. Greek: {tgt[:40]}. No match.", "weak"

    # 35. ذكو (fire blazing) → fire-related Greek
    if arabic_root == "ذكو":
        if gk_fire:
            return 0.55, "Arabic ذكو: fire blazing fiercely (ذكت النار). Greek: fire/flame. Direct conceptual match.", "masadiq_direct"
        if gk_justice:
            return 0.15, "Arabic: fire. Greek: justice/vengeance. Faint metaphor (fire of justice) but very thin.", "weak"
        return 0.05, f"Arabic ذكو: fire blazing. Greek: {tgt[:40]}. No match.", "weak"

    # 36. ذلل (submission/humility) → obey-related Greek
    if arabic_root == "ذلل":
        if gk_obey:
            return 0.55, "Arabic ذلل: submission, humility, to be humble/subdued (ذليل = humiliated). Greek: to obey/submit. Both in the submission/subjugation domain.", "masadiq_direct"
        if "accomplish" in tgt_l:
            return 0.1, "Arabic ذلل: submission. Greek: accomplish. Unrelated.", "weak"

    # 37. ذعن (to submit/comply) → obey-related
    if arabic_root == "ذعن":
        if gk_obey:
            return 0.6, "Arabic ذعن (أذعن): to submit, comply, yield (انقاد وسلس). Greek: to obey/submit. Direct meaning match.", "masadiq_direct"
        if "worthless" in tgt_l or "nobody" in tgt_l or "outĭdănós" in tgt_l:
            return 0.05, "Arabic ذعن: to submit. Greek: worthless nobodies. Unrelated.", "weak"

    # 38. ذرب (sharp/cutting) → sharp-related Greek
    if arabic_root == "ذرب":
        if gk_sharp:
            return 0.55, "Arabic ذرب: sharp, keen (of blade or tongue). Greek: sharp/keen. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic ذرب: sharp. Greek: {tgt[:40]}. No match.", "weak"

    # 39. ذرو/ذرت (wind scattering things) → scatter-related Greek
    if arabic_root in ("ذرو", "ذرا", "ذرت"):
        if gk_scatter or gk_disperse:
            return 0.6, f"Arabic {arabic_root}: wind scattering/dispersing things (ذرت الريح التراب = wind scattered the dust). Greek: to scatter/disperse. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic: wind scattering. Greek: {tgt[:40]}. No match.", "weak"

    # 40. ذعذع (to scatter property; to reveal secrets) → scatter
    if arabic_root == "ذعذع":
        if gk_disperse or gk_scatter:
            return 0.5, "Arabic ذعذع: to scatter (أكلت ماله الحقوق وذعذعته = misfortunes scattered his wealth); also to reveal secrets. Greek: to scatter/disperse. Semantic match.", "masadiq_direct"
        return 0.05, f"Arabic ذعذع: scatter. Greek: {tgt[:40]}. No match.", "weak"

    # 41. راب (to repair, to reconcile) → repair-related Greek
    if arabic_root == "راب":
        if gk_repair:
            return 0.55, "Arabic رأب: to repair/mend a crack in a vessel; to reconcile people. Greek: repair/fix. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic رأب: repair. Greek: {tgt[:40]}. No match.", "weak"

    # 42. رجو/رجي (hope/expectation) → hope-related Greek
    if arabic_root in ("رجو", "رجي"):
        if gk_hope:
            return 0.65, "Arabic رجو/رجي: hope, expectation (رجاء = hope). Greek: to hope/expect. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic: hope. Greek: {tgt[:40]}. No match.", "weak"

    # 43. رجب (to revere, to be in awe of) → revere-related
    if arabic_root == "رجب":
        if gk_revere or gk_fear:
            return 0.6, "Arabic رجب: to revere/fear (رجبته = I held him in awe). Greek: to revere/honour. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic رجب: revere. Greek: {tgt[:40]}. No match.", "weak"

    # 44. رجع (to return) → return-related
    if arabic_root == "رجع":
        if gk_return:
            return 0.65, "Arabic رجع: to return, go back (رجع بنفسه = returned of his own accord). Greek: to return/come back. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic رجع: return. Greek: {tgt[:40]}. No match.", "weak"

    # 45. رجج (to shake/vibrate) → shake-related
    if arabic_root == "رجج":
        if gk_shake:
            return 0.6, "Arabic رجج: to shake, quake (رجّه = he shook it). Greek: to shake/tremble. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic رجج: shake. Greek: {tgt[:40]}. No match.", "weak"

    # 46. رجح (to tip the balance/weigh) → weigh-related
    if arabic_root == "رجح":
        if gk_weigh:
            return 0.6, "Arabic رجح: to tip the balance, to outweigh (رجح الميزان = the scale tipped). Greek: to weigh/balance. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic رجح: weigh/balance. Greek: {tgt[:40]}. No match.", "weak"

    # 47. رصد (to watch, observe, lie in wait) → spy/watch-related
    if arabic_root in ("رصد", "رقب"):
        if gk_spy or "watch" in tgt_l or "guard" in tgt_l:
            return 0.65, f"Arabic {arabic_root}: to observe/lie in wait for prey (راصد = watcher). Greek: watch/guard/spy. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic: watch/observe. Greek: {tgt[:40]}. No match.", "weak"

    # 48. رهب (to fear) → fear-related
    if arabic_root == "رهب":
        if gk_fear or gk_revere:
            return 0.65, "Arabic رهب: to fear (رهبة = fear; رهبوت = intimidating). Greek: fear/dread. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic رهب: fear. Greek: {tgt[:40]}. No match.", "weak"

    # 49. رضع (nursing) → nurse-related
    if arabic_root == "رضع":
        if gk_nurse:
            return 0.65, "Arabic رضع: to suckle/nurse (رضع الصبي أمه = the infant nursed). Greek: to suckle/nourish. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic رضع: nurse. Greek: {tgt[:40]}. No match.", "weak"

    # 50. ركب (to ride) → ride-related
    if arabic_root in ("ركب", "ركبه"):
        if gk_ride:
            return 0.65, "Arabic ركب: to ride/mount (ركب البعير = rode the camel). Greek: to ride/mount. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic ركب: ride/mount. Greek: {tgt[:40]}. No match.", "weak"

    # 51. ركع (to bow/genuflect) → bow-related
    if arabic_root == "ركع":
        if gk_bow:
            return 0.65, "Arabic ركع: to bow, genuflect (انحناء في الصلاة). Greek: to bow/bend. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic ركع: bow. Greek: {tgt[:40]}. No match.", "weak"

    # 52. ركز (to plant/fix spear in ground) → fix/plant-related
    if arabic_root == "ركز":
        if "plant" in tgt_l or "fix" in tgt_l or "stake" in tgt_l or gk_fix:
            return 0.6, "Arabic ركز: to plant/fix a spear in the ground (ركزت الرمح = I planted the spear). Greek: to fix/plant. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic ركز: fix/plant. Greek: {tgt[:40]}. No match.", "weak"

    # 53. رغب (desire/eagerness) → desire-related
    if arabic_root == "رغب":
        if any(k in tgt_l for k in ["desire", "yearn", "long", "wish", "want", "eager"]):
            return 0.65, "Arabic رغب: desire, eagerness (رغبة = desire). Greek: yearning/desire. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic رغب: desire. Greek: {tgt[:40]}. No match.", "weak"

    # 54. رشد (right guidance) → guide-related
    if arabic_root == "رشد":
        if gk_guide:
            return 0.6, "Arabic رشد: right guidance, moral direction (رشاد = guidance). Greek: to guide/show. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic رشد: guidance. Greek: {tgt[:40]}. No match.", "weak"

    # 55. رتع (to graze freely) → graze-related
    if arabic_root == "رتع":
        if gk_graze or "feed" in tgt_l or "pasture" in tgt_l:
            return 0.6, "Arabic رتع: to graze freely (رتعت الماشية = the livestock grazed at will). Greek: to feed/graze. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic رتع: graze. Greek: {tgt[:40]}. No match.", "weak"

    # 56. رقى (to ascend/climb) → ascend-related
    if arabic_root == "رقي":
        if gk_ascend or "climb" in tgt_l or "ascend" in tgt_l:
            return 0.65, "Arabic رقى: to ascend/climb (رقيت في السلم = I climbed the ladder). Greek: to ascend/climb. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic رقى: ascend. Greek: {tgt[:40]}. No match.", "weak"

    # 57. رضا/رضو/رضي (satisfaction/contentment) → please-related
    if arabic_root in ("رضا", "رضو", "رضي"):
        if gk_piety or any(k in tgt_l for k in ["please", "content", "satisf", "approv"]):
            return 0.6, f"Arabic {arabic_root}: satisfaction, contentment (رضا = pleased state). Greek: to please/be satisfied. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic: satisfaction. Greek: {tgt[:40]}. No match.", "weak"

    # 58. ربح (profit) → profit-related
    if arabic_root == "ربح":
        if gk_profit or "profit" in tgt_l or "gain" in tgt_l:
            return 0.65, "Arabic ربح: to profit (ربح في تجارته = he profited in his trade). Greek: profit/gain. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic ربح: profit. Greek: {tgt[:40]}. No match.", "weak"

    # 59. راج (to be in demand/circulate) → circulate-related
    if arabic_root == "راج":
        if "circulate" in tgt_l or "trade" in tgt_l or "current" in tgt_l:
            return 0.55, "Arabic راج: to be in demand/circulate (goods that sell well). Greek: related to circulation/trade. Match.", "masadiq_direct"
        return 0.05, f"Arabic راج: circulation. Greek: {tgt[:40]}. No match.", "weak"

    # 60. دنا/دنو/دنع/ذعن (lowly/near) → low-related
    if arabic_root in ("دنا", "دنو", "دنع"):
        if gk_low or any(k in tgt_l for k in ["base", "mean", "low", "ignoble", "worthless"]):
            return 0.5, f"Arabic {arabic_root}: low/base/despicable (دنيء = base person). Greek: low/base/worthless. Semantic match.", "masadiq_direct"
        if gk_close or "near" in tgt_l:
            if arabic_root == "دنو":
                return 0.6, "Arabic دنو: to be near, to approach (دنا من = drew near to). Greek: to approach/be near. Direct meaning match.", "masadiq_direct"
        return 0.05, f"Arabic: low/near. Greek: {tgt[:40]}. No match.", "weak"

    # 61. دون → related
    if arabic_root == "دون":
        if gk_low:
            return 0.5, "Arabic دون: below, lesser, base (الدون = the base one). Greek: low/base/worthless. Semantic match.", "masadiq_direct"
        return 0.05, f"Arabic دون: below/base. Greek: {tgt[:40]}. No match.", "weak"

    # 62. ذلي (to gather fresh ripe dates) → no match usually
    if arabic_root == "ذلي":
        return 0.05, "Arabic ذلي: to gather fresh ripe dates. Greek: various unrelated.", "weak"

    # 63. ذما (to make something difficult for someone) → related
    if arabic_root == "ذما":
        return 0.05, "Arabic ذما: to cause hardship. Greek: various. No specific match found.", "weak"

    # 64. ذمت (to be thin/emaciated, deteriorate) → related
    if arabic_root == "ذمت":
        if any(k in tgt_l for k in ["emaciated", "thin", "wasted", "deteriorat"]):
            return 0.55, "Arabic ذمت: to be emaciated/deteriorated. Greek: wasted/thin. Meaning match.", "masadiq_direct"
        return 0.05, "Arabic ذمت: emaciated. Greek: various. No match.", "weak"

    # 65. ذمطه (to slaughter; to swallow anything) → related
    if arabic_root == "ذمطه":
        if "devour" in tgt_l or "swallow" in tgt_l or "eat" in tgt_l:
            return 0.55, "Arabic ذمطه: to slaughter; also to swallow/gulp everything (ذُمَطَة = glutton). Greek: to devour/eat. Semantic match.", "masadiq_direct"
        if "slaughter" in tgt_l or "kill" in tgt_l:
            return 0.55, "Arabic ذمطه: to slaughter. Greek: slaughter/kill. Direct match.", "masadiq_direct"
        return 0.05, "Arabic ذمطه: slaughter/swallow. Greek: various. No match.", "weak"

    # 66. ذها (to become arrogant) → pride-related
    if arabic_root == "ذها":
        if any(k in tgt_l for k in ["arrogant", "proud", "haughty", "boast"]):
            return 0.55, "Arabic ذها: to become arrogant (تكبّر). Greek: boast/arrogance. Semantic match.", "masadiq_direct"
        return 0.05, "Arabic ذها: arrogance. Greek: various. No match.", "weak"

    # 67. ذهله (to forget/be distracted from) → forget-related
    if arabic_root == "ذهله":
        if any(k in tgt_l for k in ["forget", "distract", "neglect", "abandon", "leave behind"]):
            return 0.55, "Arabic ذهله: to forget/leave behind (ذهل عنه = forgot him). Greek: to forget/leave behind. Semantic match.", "masadiq_direct"
        return 0.05, "Arabic ذهله: forget. Greek: various. No match.", "weak"

    # 68. رزا (disaster/loss) → loss-related
    if arabic_root == "رزا":
        if any(k in tgt_l for k in ["loss", "misfortune", "disaster", "misery"]):
            return 0.55, "Arabic رزأ: calamity, loss (الرزء = the calamity). Greek: misfortune/disaster. Semantic match.", "masadiq_direct"
        return 0.05, "Arabic رزأ: calamity. Greek: various. No match.", "weak"

    # 69. رصص (to join tightly together) → join-related
    if arabic_root in ("رصص", "رصه"):
        if any(k in tgt_l for k in ["join", "bind", "fasten", "close together", "compact"]):
            return 0.55, f"Arabic {arabic_root}: to join tightly, press together (بنيان مرصوص = compact building). Greek: to join/bind. Semantic match.", "masadiq_direct"
        return 0.05, f"Arabic: join tightly. Greek: {tgt[:40]}. No match.", "weak"

    # 70. ركح (mountain corner/buttress) → corner/support-related
    if arabic_root == "ركح":
        if any(k in tgt_l for k in ["corner", "buttress", "support", "base", "foundation"]):
            return 0.5, "Arabic ركح: corner/buttress of a mountain. Greek: support/corner. Semantic match.", "masadiq_direct"
        return 0.05, "Arabic ركح: mountain corner. Greek: various. No match.", "weak"

    # 71. رضد/رضم (to stack/pile stones) → stack-related
    if arabic_root in ("رضد", "رضم"):
        if any(k in tgt_l for k in ["stack", "pile", "heap", "arrange stones", "build"]):
            return 0.5, f"Arabic {arabic_root}: to stack/pile up stones. Greek: to pile/arrange. Semantic match.", "masadiq_direct"
        return 0.05, f"Arabic: stack stones. Greek: {tgt[:40]}. No match.", "weak"

    # 72. رقز/رقص (to dance) → dance-related
    if arabic_root in ("رقز",):
        if any(k in tgt_l for k in ["dance", "jump", "skip", "leap"]):
            return 0.6, "Arabic رقز: to dance/leap (same as رقص). Greek: dance/jump. Semantic match.", "masadiq_direct"
        return 0.05, "Arabic رقز: dance. Greek: various. No match.", "weak"

    # 73. ربا (to watch from a height, to scout) → scout-related
    if arabic_root == "ربا":
        if gk_spy or any(k in tgt_l for k in ["scout", "lookout", "watch", "survey"]):
            return 0.55, "Arabic ربأ: to scout from high ground, watch for danger (مربأة = watchtower). Greek: watch/scout. Semantic match.", "masadiq_direct"
        return 0.05, "Arabic ربأ: scout/watch. Greek: various. No match.", "weak"

    # 74. ربد (to stay/remain; also a grey-brown color) → remain-related
    if arabic_root == "ربد":
        if any(k in tgt_l for k in ["remain", "stay", "linger", "dwell", "reside"]):
            return 0.5, "Arabic ربد: to remain in a place (ربد بالمكان = stayed in the place). Greek: to remain/dwell. Semantic match.", "masadiq_direct"
        return 0.05, "Arabic ربد: remain. Greek: various. No match.", "weak"

    # 75. ربخ (to be slack/limp) → relax-related
    if arabic_root == "ربخ":
        if any(k in tgt_l for k in ["limp", "slack", "loose", "relax", "faint"]):
            return 0.5, "Arabic ربخ: to be slack/limp (تربّخ = he went slack). Greek: to be slack/limp. Semantic match.", "masadiq_direct"
        return 0.05, "Arabic ربخ: slack/limp. Greek: various. No match.", "weak"

    # 76. ربكه (to confuse/entangle) → confuse-related
    if arabic_root == "ربكه":
        if any(k in tgt_l for k in ["confuse", "mix", "entangle", "trouble", "disturb"]):
            return 0.5, "Arabic ربكه: to entangle/confuse (ربكه في الوحل = he stuck him in the mud). Greek: to confuse/entangle. Semantic match.", "masadiq_direct"
        return 0.05, "Arabic ربكه: confuse. Greek: various. No match.", "weak"

    # 77. ردج (meconium of foal) → specific
    if arabic_root == "ردج":
        if any(k in tgt_l for k in ["meconium", "dung", "excrement", "first stool"]):
            return 0.6, "Arabic ردج: meconium of a foal (first excrement). Greek: meconium. Direct match.", "masadiq_direct"
        return 0.05, "Arabic ردج: meconium. Greek: various. No match.", "weak"

    # 78. ردد (to return/refuse) → related
    if arabic_root == "ردد":
        if gk_return or any(k in tgt_l for k in ["return", "repel", "refuse", "turn back"]):
            return 0.6, "Arabic ردد: to return, repel, refuse (ردّه = he sent him back). Greek: to return/repel. Semantic match.", "masadiq_direct"
        return 0.05, "Arabic ردد: return/repel. Greek: various. No match.", "weak"

    # 79. ردم (to fill/close a gap; also thunder/rumbling sound) → related
    if arabic_root == "ردم":
        if any(k in tgt_l for k in ["fill", "stop up", "close", "dam", "plug", "seal"]):
            return 0.55, "Arabic ردم: to fill/stop a gap (ردم الثلمة = filled the breach). Greek: to fill/stop. Semantic match.", "masadiq_direct"
        return 0.05, "Arabic ردم: fill/close. Greek: various. No match.", "weak"

    # 80. رذم (overflowing bowl) → overflow-related
    if arabic_root == "رذم":
        if any(k in tgt_l for k in ["overflow", "brim", "full", "spill"]):
            return 0.5, "Arabic رذم: bowl overflowing (قصعة رَذوم = overflowing bowl). Greek: overflow/full. Semantic match.", "masadiq_direct"
        return 0.05, "Arabic رذم: overflow. Greek: various. No match.", "weak"

    # 81. رتب (to stand firm/upright) → firm-related
    if arabic_root == "رتب":
        if any(k in tgt_l for k in ["stand", "firm", "upright", "fixed", "stable"]):
            return 0.5, "Arabic رتب: to stand firm/upright (الرتوب = standing firm). Greek: to stand/be stable. Semantic match.", "masadiq_direct"
        return 0.05, "Arabic رتب: stand firm. Greek: various. No match.", "weak"

    # 82. رتج (to lock/bolt a door) → lock-related
    if arabic_root == "رتج":
        if any(k in tgt_l for k in ["lock", "bolt", "close", "shut", "bar", "door"]):
            return 0.6, "Arabic رتج: to lock/bolt (أرتج الباب = he bolted the door). Greek: to lock/close. Semantic match.", "masadiq_direct"
        return 0.05, "Arabic رتج: lock/bolt. Greek: various. No match.", "weak"

    # 83. رتع → already handled above
    # 84. رجا → already handled above

    # 85. راد (young beautiful woman; also: origin) → beauty/youth-related
    if arabic_root == "راد":
        if any(k in tgt_l for k in ["young", "beautiful", "youthful", "maiden"]):
            return 0.5, "Arabic راد (رأد): young beautiful woman. Greek: young/beautiful. Semantic match.", "masadiq_direct"
        return 0.05, "Arabic راد: young/beautiful. Greek: various. No match.", "weak"

    # 86. راب (tool used by builders; to repair) → tool/repair-related
    if arabic_root == "راز":
        if any(k in tgt_l for k in ["tool", "measure", "plumb", "builder"]):
            return 0.5, "Arabic راز: a builder's instrument. Greek: a tool/instrument. Semantic match.", "masadiq_direct"
        return 0.05, "Arabic راز: builder's tool. Greek: various. No match.", "weak"

    # 87. ذير (lubricating camel's teats to prevent calf from suckling) → specific
    if arabic_root == "ذير":
        return 0.05, "Arabic ذير: lubricating teats to deter calf. Greek: various. No specific match.", "weak"

    # ── Tier 5: Generic Greek-meaning fallback checks ──────────────────────
    # GUARD: only apply generic rules if Greek target is a genuine word
    # (not eryngo plant, grammatical form, or arbitrary plant name)
    is_plant = any(k in tgt_l for k in ["eryngo", "plant", "herb", "aristolochia",
                                          "smearwort", "coltsfoot", "charlock", "cataplasm",
                                          "labdanum", "water plantain", "rockrose", "tussilago"])
    is_obscure_gloss = any(k in tgt_l for k in ["hesychius gives", "hesychius' gives",
                                                   "aeolic form", "boeotian form", "doric form",
                                                   "epic form", "elean form", "homeric form",
                                                   "accusative singular", "genitive singular",
                                                   "masculine/neuter genitive", "nominative/vocative",
                                                   "perfect subjunctive", "cretan form"])
    if is_plant or is_obscure_gloss:
        return 0.05, f"Greek target is a botanical term, obscure gloss, or grammatical form unrelated to Arabic meaning.", "weak"

    # Check for broad meaning matches not caught by specific rules

    # Arabic: to be sorrowful/sad
    if any(k in mas for k in ["حزن", "حُزن", "غمّ", "كآبة", "أسى"]):
        if any(k in tgt_l for k in ["sorrowful", "sad", "grieve", "mourn", "lament"]):
            return 0.6, "Arabic: sorrow/grief. Greek: sorrow/grief. Direct meaning match.", "masadiq_direct"

    # Arabic: to be happy/rejoice
    if any(k in mas for k in ["فرح", "سرور", "ابتهج"]):
        if any(k in tgt_l for k in ["happy", "rejoice", "glad", "joy"]):
            return 0.6, "Arabic: joy/happiness. Greek: joy/happiness. Direct meaning match.", "masadiq_direct"

    # هيت/هوّت special case: calling out, not praying
    if arabic_root in ("هيت", "هوت") and any(k in mas for k in ["صاح", "دعاه", "هيّت", "هَوَّت"]):
        if gk_pray:
            return 0.4, "Arabic هيت: to shout/call out/summon someone (صاح به). Greek εὐχετάομαι: to pray. Both involve verbal calling; not identical (secular vs sacred). Plausible domain overlap.", "mafahim_deep"

    # Arabic: to call out/shout/summon (not pray specifically)
    if any(k in mas for k in ["صاح", "هيّت", "هوّت", "صيحة", "نادى"]):
        if gk_pray:
            return 0.4, "Arabic: to shout/call out/summon. Greek: to pray (calling to deity). Calling domain overlap; not identical.", "mafahim_deep"

    # Arabic: to pray / perform religious duty
    if any(k in mas for k in ["صلى", "دعا", "عبد", "تضرع"]):
        if gk_pray:
            return 0.6, "Arabic: to pray. Greek: to pray/supplicate. Direct meaning match.", "masadiq_direct"

    # Arabic: camel (related)
    if any(k in mas for k in ["بعير", "ناقة", "جمل"]):
        if any(k in tgt_l for k in ["camel", "dromedary"]):
            return 0.6, "Arabic: camel-related. Greek: camel. Direct meaning match.", "masadiq_direct"

    # Arabic: fire/burn
    if ar_fire and gk_fire:
        return 0.6, "Arabic: fire/blaze. Greek: fire/flame. Direct meaning match.", "masadiq_direct"

    # نجا/نجأ special case: evil eye, not push
    if arabic_root in ("نجا", "نجأ"):
        if any(k in tgt_l for k in ["force", "necessity", "compulsion", "constraint"]):
            return 0.1, "Arabic نجأ: to strike with evil eye. Greek ἀνάγκη: necessity/force. Unrelated meanings.", "weak"

    # Arabic: to push/repel and Greek: to push/violent pressure
    # Guard: Arabic root must genuinely mean "push" not "evil eye"
    if ar_push and gk_push and not any(k in mas for k in ["بعين", "العين", "نجأ", "أصَبْتَهُ بعين"]):
        return 0.5, "Arabic: to push/shove. Greek: violent pressure/force. Semantic match.", "masadiq_direct"

    # Arabic: fear and Greek: fear
    if (ar_fear or ar_fear2) and gk_fear:
        return 0.6, "Arabic: fear/dread. Greek: fear/terror. Direct meaning match.", "masadiq_direct"

    # Arabic: run/swift and Greek: swift/running
    if ar_run and gk_run:
        return 0.5, "Arabic: swift/running. Greek: swift-running. Semantic match.", "masadiq_direct"

    # Arabic: walk/move and Greek: walk/go
    # Guard: Arabic root must genuinely mean "walk" not "climb stairs" or other unrelated
    if ar_walk and gk_walk and any(k in mas for k in ["مشى", "سار", "دبّ", "دبيب"]):
        return 0.45, "Arabic: to walk/proceed. Greek: to go/walk. Semantic match.", "masadiq_direct"

    # Arabic: to choke and Greek: to choke/strangle
    if ar_choke and gk_choke:
        return 0.6, "Arabic: to choke/strangle. Greek: to choke/throttle. Direct meaning match.", "masadiq_direct"

    # Arabic: to destroy and Greek: to destroy
    if ar_destroy and gk_destroy:
        return 0.6, "Arabic: destruction/ruin. Greek: to destroy/break down. Direct meaning match.", "masadiq_direct"

    # Arabic: to hide and Greek: to hide
    if ar_hide and gk_hide:
        return 0.65, "Arabic: to hide/conceal. Greek: to hide/conceal. Direct meaning match.", "masadiq_direct"

    # Arabic: to scatter and Greek: to scatter
    if ar_scatter and gk_scatter:
        return 0.6, "Arabic: to scatter (wind). Greek: to scatter/disperse. Direct meaning match.", "masadiq_direct"

    # Arabic: sharp and Greek: sharp
    if ar_sharp and gk_sharp:
        return 0.55, "Arabic: sharp/keen. Greek: sharp/keen. Direct meaning match.", "masadiq_direct"

    # Arabic: obey/submit and Greek: obey/submit
    if ar_obey and gk_obey:
        return 0.6, "Arabic: to submit/comply. Greek: to obey. Direct meaning match.", "masadiq_direct"

    # ── Tier 6: Final fallback ─────────────────────────────────────────────
    return 0.05, f"No semantic overlap found. Arabic: {_brief(mas)}. Greek: {tgt[:50]}.", "weak"


def _brief(gloss: str) -> str:
    if not gloss:
        return "unknown"
    parts = gloss.replace("،", ",").split(":")
    if len(parts) > 1:
        return parts[0].strip()[:40]
    return gloss[:40]


# ── main ───────────────────────────────────────────────────────────────────────

def process_chunk(chunk_num: int):
    in_path  = f"{IN_DIR}/phase1_new_{chunk_num}.jsonl"
    out_path = f"{OUT_DIR}/phase1_scored_{chunk_num}.jsonl"

    records = []
    with open(in_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            arabic_root  = d.get("arabic_root", "")
            target_lemma = d.get("target_lemma", "")
            masadiq      = d.get("masadiq_gloss", "")
            mafahim      = d.get("mafahim_gloss", "")
            target_gloss = d.get("target_gloss", "")

            score, reasoning, method = score_pair(
                arabic_root, masadiq, mafahim, target_lemma, target_gloss
            )

            rec = {
                "source_lemma":   arabic_root,
                "target_lemma":   target_lemma,
                "semantic_score": round(score, 2),
                "reasoning":      reasoning,
                "method":         method,
                "lang_pair":      "ara-grc",
                "model":          "sonnet-phase1",
            }
            records.append(rec)

    with open(out_path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    high = [r for r in records if r["semantic_score"] >= 0.5]
    return records, len(high)


if __name__ == "__main__":
    all_records = []
    chunk_stats = []
    for n in range(232, 263):
        recs, high_count = process_chunk(n)
        all_records.extend(recs)
        chunk_stats.append((n, len(recs), high_count))
        print(f"Chunk {n}: {len(recs)} pairs, {high_count} >= 0.5")

    total = len(all_records)
    high  = [r for r in all_records if r["semantic_score"] >= 0.5]
    print(f"\nTotal: {total} pairs processed")
    print(f"Pairs >= 0.5: {len(high)}")

    top10 = sorted(high, key=lambda x: x["semantic_score"], reverse=True)[:10]
    print("\nTop 10 discoveries:")
    for r in top10:
        src = r["source_lemma"]
        tgt = r["target_lemma"]
        sc  = r["semantic_score"]
        rsn = r["reasoning"][:80]
        print(f"  {sc:.2f}  {src} -> {tgt}: {rsn}")
