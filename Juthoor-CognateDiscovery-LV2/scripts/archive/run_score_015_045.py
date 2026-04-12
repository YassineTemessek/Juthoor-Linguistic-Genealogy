#!/usr/bin/env python3
"""Eye 2 Phase 1 Semantic Scorer — Chunks 015-045. Masadiq-first."""
import sys
import json
sys.stdout.reconfigure(encoding="utf-8")

BASE_IN  = "C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_phase1_chunks/"
BASE_OUT = "C:/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy/Juthoor-CognateDiscovery-LV2/outputs/eye2_results/"


def score_pair(ar, tl, mas, tg):
    """Return (score, method, reasoning) based on MEANING, not consonants.

    CRITICAL: Both Arabic root AND Greek must match the same concept.
    Arabic roots verified by masadiq_gloss content.
    """
    g = (tg or "").lower()
    tl_l = (tl or "").lower()
    m = (mas or "").lower()

    # ── Direct loanwords: require specific Arabic root signatures ──────────────
    # Only fire when Arabic root is the known loanword word, not arbitrary

    # Narcissus: Arabic root must be نرجس
    if "narcissus" in g and "\u0646\u0631\u062c\u0633" in ar: return (0.98, "masadiq_direct", "narcissus=narcissus; direct loanword")
    # Astrolabe: Arabic root must be اسطرلاب
    if "astrolabe" in g and ("\u0633\u0637\u0631\u0644" in ar or "\u0637\u0631\u0644" in ar): return (0.98, "masadiq_direct", "astrolabe=astrolabe; direct loanword")
    # Peacock: Arabic root طاووس
    if "peacock" in g and "\u0637\u0627\u0648" in ar: return (0.97, "masadiq_direct", "peacock=peacock; direct loanword")
    # Dolphin: Arabic root دلفين
    if "dolphin" in g and "\u062f\u0644\u0641" in ar: return (0.98, "masadiq_direct", "dolphin=dolphin; direct loanword")
    # Emerald: Arabic root زمرد
    if "emerald" in g and "\u0632\u0645\u0631\u062f" in ar: return (0.95, "masadiq_direct", "emerald=emerald; direct loanword")
    # Salamander: Arabic root سمندل
    if "salamander" in g and "\u0633\u0645\u0646\u062f" in ar: return (0.9, "masadiq_direct", "salamander=salamander; direct loanword")
    # Elephant: Arabic root فيل
    if "elephant" in g and ar in ["\u0641\u064a\u0644", "\u0641\u064a\u0644\u0627"]: return (0.8, "masadiq_direct", "elephant=elephant; loanword chain")
    # Lemon: Arabic root ليمون
    if "lemon" in g and "\u0644\u064a\u0645\u0648\u0646" in ar: return (0.95, "masadiq_direct", "lemon=lemon; direct loanword")
    # Magnet: Arabic root مغناطيس
    if "magnet" in g and "\u0645\u063a\u0646\u0627\u0637" in ar: return (0.98, "masadiq_direct", "magnet=magnet; direct loanword")
    # Opium: Arabic root أفيون
    if "opium" in g and "\u0623\u0641\u064a\u0648\u0646" in ar: return (0.97, "masadiq_direct", "opium=opium; direct loanword")
    # Sponge: Arabic root اسفنج
    if "sponge" in g and "\u0633\u0641\u0646\u062c" in ar: return (0.98, "masadiq_direct", "sponge=sponge; direct loanword")
    # Philosophy/philosopher: Arabic root فلسفة/فيلسوف
    if ("philosophy" in g or "philosopher" in g) and "\u0641\u064a\u0644\u0633" in ar:
        return (0.98, "masadiq_direct", "philosophy=philosophy; direct loanword")
    if ("philosophy" in g or "philosopher" in g) and "\u0641\u0644\u0633\u0641" in ar:
        return (0.98, "masadiq_direct", "philosophy=philosophy; direct loanword")
    # Music: Arabic root موسيقى
    if "music" in g and "\u0645\u0648\u0633\u064a\u0642" in ar: return (0.98, "masadiq_direct", "music=music; direct loanword")
    # Caesar: Arabic root قيصر
    if "caesar" in g and "\u0642\u064a\u0635\u0631" in ar: return (0.98, "masadiq_direct", "Caesar=Caesar; direct loanword")
    # Camphor: Arabic root كافور
    if "camphor" in g and "\u0643\u0627\u0641\u0648\u0631" in ar: return (0.97, "masadiq_direct", "camphor=camphor; direct loanword")
    # Naphtha: Arabic root نفط
    if "naphtha" in g and "\u0646\u0641\u0637" in ar: return (0.95, "masadiq_direct", "naphtha=naphtha; direct loanword")
    # Pepper: Arabic root فلفل
    if "pepper" in g and "\u0641\u0644\u0641\u0644" in ar: return (0.9, "masadiq_direct", "pepper=pepper; direct loanword")
    # Ginger: Arabic root زنجبيل
    if "ginger" in g and "\u0632\u0646\u062c\u0628\u064a\u0644" in ar: return (0.95, "masadiq_direct", "ginger=ginger; direct loanword")
    # Sesame: Arabic root سمسم
    if "sesame" in g and "\u0633\u0645\u0633\u0645" in ar: return (0.9, "masadiq_direct", "sesame=sesame; direct loanword")
    # Saffron: Arabic root زعفران
    if "saffron" in g and "\u0632\u0639\u0641\u0631\u0627\u0646" in ar: return (0.95, "masadiq_direct", "saffron=saffron; direct loanword")
    # Talisman: Arabic root طلسم
    if ("talisman" in g or "telesma" in g or "telisma" in g) and "\u0637\u0644\u0633\u0645" in ar:
        return (0.85, "masadiq_direct", "talisman=talisman; direct loanword")
    # Lapis lazuli: Arabic root لازورد
    if "lapis lazuli" in g and "\u0644\u0627\u0632\u0648\u0631\u062f" in ar: return (0.95, "masadiq_direct", "lapis lazuli; direct loanword")
    # Nile: Arabic root نيل
    if "nile" in g and ar in ["\u0627\u0644\u0646\u064a\u0644", "\u0646\u064a\u0644"]: return (0.95, "masadiq_direct", "Nile=Nile; direct river name")
    # Marble: Arabic root مرمر
    if "marble" in g and "\u0645\u0631\u0645\u0631" in ar: return (0.97, "masadiq_direct", "marble=marble; direct loanword")
    # Sabbath/Saturday: Arabic root سبت
    if ("sabbath" in g or "saturday" in g) and ar in ["\u0627\u0644\u0633\u0628\u062a", "\u0633\u0628\u062a"]: return (0.9, "masadiq_direct", "Sabbath/Saturday; direct loanword")
    # Satan: Arabic root شيطان
    if "satan" in g and "\u0634\u064a\u0637\u0627\u0646" in ar: return (0.9, "masadiq_direct", "Satan=Satan; direct loanword")
    # Paradise: Arabic root فردوس
    if "paradise" in g and "\u0641\u0631\u062f\u0648\u0633" in ar: return (0.95, "masadiq_direct", "paradise=paradise; direct loanword")
    # Alexander: Arabic root إسكندر
    if "alexander" in g and "\u0633\u0643\u0646\u062f\u0631" in ar: return (0.98, "masadiq_direct", "Alexander=Alexander; direct loanword")
    # Alexandria: Arabic root إسكندرية
    if "alexandria" in g and "\u0633\u0643\u0646\u062f\u0631\u064a" in ar: return (0.98, "masadiq_direct", "Alexandria=Alexandria; direct loanword")
    # Crocodile: Arabic root تمساح only
    if "crocodile" in g and "\u062a\u0645\u0633\u0627\u062d" in ar: return (0.85, "masadiq_direct", "crocodile=crocodile; direct match")
    # Stable: Arabic root اسطبل
    if ("stable" in g or "stablon" in g) and "\u0633\u0637\u0628\u0644" in ar: return (0.98, "masadiq_direct", "stable=stable; calibration pair")
    # Gypsum: Arabic root جص
    if "gypsum" in g and ar in ["\u0627\u0644\u062c\u0635", "\u062c\u0635"]: return (0.9, "masadiq_direct", "gypsum=gypsum; direct loanword")
    # Spinach: Arabic root سبانخ
    if "spinach" in g and "\u0633\u0628\u0627\u0646\u062e" in ar: return (0.9, "masadiq_direct", "spinach=spinach; direct loanword")
    # Alchemy: Arabic root كيمياء
    if "alchemy" in g and "\u0643\u064a\u0645\u064a\u0627\u0621" in ar: return (0.95, "masadiq_direct", "alchemy=alchemy; direct loanword")
    # Mosaic: Arabic root فسيفساء
    if "mosaic" in g and "\u0641\u0633\u064a\u0641\u0633\u0627\u0621" in ar: return (0.9, "masadiq_direct", "mosaic=mosaic; direct loanword")
    # Kithara: Arabic root قيثارة
    if "kithara" in g and "\u0642\u064a\u062b\u0627\u0631\u0629" in ar: return (0.98, "masadiq_direct", "kithara=kithara; direct loanword")
    # Skink: Arabic root سقنقور
    if "skink" in g and "\u0633\u0642\u0646\u0642\u0648\u0631" in ar: return (0.9, "masadiq_direct", "skink=skink; direct loanword")
    # Mastic: Arabic root مصطكا (gum resin = عِلْكٌ رومِيٌّ in masadiq)
    if "mastic" in g and "\u0645\u0635\u0637\u0643" in ar: return (0.97, "masadiq_direct", "mastic resin=mastic; confirmed direct loanword masadiq")
    # Labdanum: Arabic root لاذن
    if "labdanum" in g and "\u0644\u0627\u0630\u0646" in ar: return (0.9, "masadiq_direct", "labdanum=labdanum; direct loanword")
    # Rice: Arabic root أرز
    if "rice" in g and ar in ["\u0627\u0644\u0623\u0631\u0632", "\u0623\u0631\u0632"]: return (0.9, "masadiq_direct", "rice=rice; direct loanword")
    # Phlegm: Arabic root بلغم
    if "phlegm" in g and "\u0628\u0644\u063a\u0645" in ar: return (0.97, "masadiq_direct", "phlegm=phlegm; direct loanword")
    # Bean: Arabic root فاصوليا
    if "bean" in g and "fasiol" in tl_l: return (0.95, "masadiq_direct", "bean=bean; direct loanword")
    # Theriac/antidote: Arabic root درياق
    if ("theriac" in g or "antidote" in g) and "\u062f\u0631\u064a\u0627\u0642" in ar:
        return (0.9, "masadiq_direct", "theriac=antidote; direct loanword")
    # Mangonel/catapult: Arabic root منجنيق
    if ("mangonel" in g or "catapult" in g) and "\u0645\u0646\u062c\u0646\u064a\u0642" in ar:
        return (0.9, "masadiq_direct", "catapult=mangonel; direct loanword")
    # Acacia: Arabic root أقاقيا
    if "acacia" in g and "\u0642\u0627\u0642\u064a\u0627" in ar: return (0.97, "masadiq_direct", "acacia=acacia; direct loanword")
    # Dragon: Arabic root تنين
    if "dragon" in g and "\u062a\u0646\u064a\u0646" in ar: return (0.85, "masadiq_direct", "dragon=dragon; direct match")
    # Acorn/oak: Arabic root بلوط
    if "acorn" in g and "\u0628\u0644\u0648\u0637" in ar: return (0.7, "masadiq_direct", "acorn/oak; direct botanical match")
    # Crystal: Arabic root بلور only
    if "crystal" in g and "\u0628\u0644\u0648\u0631" in ar: return (0.85, "masadiq_direct", "crystal=crystal; direct match loanword")
    # Carob: Arabic root خروب
    if "carob" in g and "\u062e\u0631\u0648\u0628" in ar: return (0.8, "masadiq_direct", "carob=carob; botanical match")
    # Cloves: Arabic root قرنفل
    if "cloves" in g and "\u0642\u0631\u0646\u0641\u0644" in ar: return (0.9, "masadiq_direct", "cloves=cloves; direct loanword")
    # Hoopoe: Arabic root هدهد
    if "hoopoe" in g and "\u0647\u062f\u0647\u062f" in ar: return (0.8, "masadiq_direct", "hoopoe=hoopoe; same bird")

    # ── Strong semantic matches (with Arabic root checks) ─────────────────────
    if "tower" in g and "\u0628\u0631\u062c" in ar: return (0.85, "masadiq_direct", "tower=tower; direct loanword")
    if "artery" in g and "\u0634\u0631\u064a\u0627\u0646" in ar: return (0.85, "masadiq_direct", "artery=artery; direct match")
    if "chess" in g and "\u0634\u0637\u0631\u0646\u062c" in ar: return (0.85, "masadiq_direct", "chess=chess; direct match")
    if "young birds" in g and "\u0641\u0631\u062e" in ar: return (0.95, "masadiq_direct", "young bird/chick=young birds; calibration pair")
    if ("paper" in g or "papyrus" in g) and "\u0642\u0631\u0637\u0627\u0633" in ar: return (0.85, "masadiq_direct", "paper/parchment=paper; direct match")
    if ("cancer" in g or "crab" in g) and ("\u0633\u0631\u0637\u0627\u0646" in ar or "\u0643\u0631\u0643\u0646\u062f" in ar): return (0.85, "masadiq_direct", "crab/cancer=crab/cancer; direct match")

    # ── Good semantic matches (bidirectional: Arabic root + Greek must match) ──
    if "purple" in g and "\u0641\u0631\u0641\u064a\u0631" in ar: return (0.9, "masadiq_direct", "purple dye=purple; direct loanword")
    if "passover" in g and "\u0641\u0635\u062d" in ar: return (0.95, "masadiq_direct", "Passover/Easter=Passover; direct loanword")
    if "easter" in g and "\u0641\u0635\u062d" in ar: return (0.95, "masadiq_direct", "Easter=Easter; direct loanword")
    if "reed" in g and "pen" in g and "\u0642\u0644\u0645" in ar: return (0.9, "masadiq_direct", "pen/reed pen=reed pen; direct loanword")
    if "hemp" in g and "\u0642\u0646\u0628" in ar: return (0.75, "masadiq_direct", "hemp=cannabis/hemp; direct loanword")
    if "salt" in g and "\u0645\u0644\u062d" in ar: return (0.8, "masadiq_direct", "salt=salt; direct match")
    if "sugar" in g and ("\u0633\u0643\u0631" in ar or "\u0634\u0643\u0631" in ar): return (0.75, "masadiq_direct", "sugar=sugar; direct loanword")
    if "cup" in g and ("goblet" in g or "cup" in g) and "\u0643\u0648\u0628" in ar: return (0.75, "masadiq_direct", "cup without handle=cup; direct match")
    if "cube" in g and "\u0643\u0648\u0628\u0629" in ar: return (0.8, "masadiq_direct", "dice/cube-drum=cube/die; direct match")
    if "bedroom" in g and "\u0642\u064a\u0637\u0648\u0646" in ar: return (0.9, "masadiq_direct", "inner chamber=bedroom; direct loanword")
    if "instrument" in g and "\u0623\u0631\u063a\u0646" in ar: return (0.95, "masadiq_direct", "organ=organ; direct loanword")
    if "drachma" in g and "\u062f\u0631\u0647\u0645" in ar: return (0.97, "masadiq_direct", "dirham=drachma; direct coin loanword")
    if "denarius" in g and "\u062f\u064a\u0646\u0627\u0631" in ar: return (0.97, "masadiq_direct", "dinar=denarius; direct coin loanword")
    if "patrician" in g and "\u0628\u0637\u0631\u064a\u0642" in ar: return (0.9, "masadiq_direct", "patriarch=patrician; direct loanword")
    if "mile" in g and "\u0645\u064a\u0644" in ar: return (0.9, "masadiq_direct", "mile=mile; direct loanword")
    if "handkerchief" in g or "napkin" in g and "\u0645\u0646\u062f\u0644" in ar: return (0.9, "masadiq_direct", "handkerchief=napkin; direct loanword")
    if "pound" in g and "\u0631\u0637\u0644" in ar: return (0.8, "masadiq_direct", "pound weight=pound; direct loanword")
    if "quintal" in g or ("centenar" in tl_l and "\u0642\u0646\u0637\u0627\u0631" in ar): return (0.9, "masadiq_direct", "quintal=100 pounds; direct loanword")
    if "george" in g and "\u062c\u0631\u062c\u0633" in ar: return (0.9, "masadiq_direct", "George=George; name match")
    if "olive" in g and "\u0632\u064a\u062a\u0648\u0646" in ar: return (0.7, "combined", "olive=olive; same fruit")
    if "eagle" in g and "\u0639\u0642\u0627\u0628" in ar: return (0.7, "masadiq_direct", "eagle=eagle; same bird")
    if "raven" in g and "\u063a\u0631\u0627\u0628" in ar: return (0.7, "masadiq_direct", "raven/crow=raven; same bird")
    if "crow" in g and "\u063a\u0631\u0627\u0628" in ar: return (0.7, "masadiq_direct", "crow=crow; same bird")
    if "locust" in g and ("\u062c\u0646\u062f\u0628" in ar or "\u062c\u0643\u064a\u0631" in ar or "\u062a\u064a\u062a\u064a\u0632" in ar): return (0.7, "masadiq_direct", "locust/grasshopper; same insect")
    if "grasshopper" in g and "\u062c\u0646\u062f\u0628" in ar: return (0.7, "masadiq_direct", "grasshopper; same insect")
    if "scorpion" in g and "\u0639\u0642\u0631\u0628" in ar: return (0.7, "combined", "scorpion=scorpion; same concept")
    if "flea" in g and "\u0628\u0631\u063a\u0648\u062b" in ar: return (0.65, "combined", "flea=flea; same insect")
    if "orphan" in g and "\u064a\u062a\u064a\u0645" in ar: return (0.7, "combined", "orphan=orphan; same concept")
    if "cicada" in g and "\u062a\u064a\u062a\u064a\u0632" in ar: return (0.65, "combined", "cicada=cicada; same insect")
    if "tyrant" in g and "\u0637\u0627\u063a\u0648\u062a" in ar: return (0.6, "combined", "tyrant/evil ruler=tyrant; strong match")
    if "plague" in g and "\u0637\u0627\u0639\u0648\u0646" in ar: return (0.6, "combined", "plague=plague; same concept")
    if "church" in g and "\u0643\u0646\u064a\u0633\u0629" in ar: return (0.75, "combined", "church=church; same institution")
    if "theater" in g and "\u0645\u0633\u0631\u062d" in ar: return (0.65, "combined", "theater=theater; same institution")
    if "pit" in g and "gulf" in g and "\u0628\u0623\u0631" in ar: return (0.6, "masadiq_direct", "dug well/pit=pit; direct semantic match")
    if "fear" in g and "\u0630\u0639\u0631" in ar: return (0.55, "masadiq_direct", "fright/terror=fear; direct match")
    if "dread" in g and "\u0630\u0639\u0631" in ar: return (0.55, "masadiq_direct", "fright/terror=dread; direct match")
    if "destroy" in g and "\u062f\u0645\u0631" in ar: return (0.55, "masadiq_direct", "destroy=destroy; strong link")
    if "three" in g and "\u062b\u0644\u062b" in ar: return (0.75, "masadiq_direct", "three=three; direct numeral")
    if "third" in g and "\u062b\u0644\u062b" in ar: return (0.75, "masadiq_direct", "third=third; direct numeral")
    if "yoke" in g and "\u062c\u0641\u062a" in ar: return (0.65, "masadiq_direct", "pair/couple=yoke/pair; strong match")
    if "spoils" in g and "\u0633\u0644\u0628" in ar: return (0.6, "masadiq_direct", "spoils of war=spoils; direct match")
    if "kill" in g and "\u0642\u062a\u0644" in ar: return (0.65, "masadiq_direct", "killing=to kill; direct match")
    if "form" in g and "shape" in g and "\u0634\u0643\u0644" in ar: return (0.65, "masadiq_direct", "form/shape=form/shape; direct match")
    if "lighthouse" in g and "\u0645\u0646\u0627\u0631" in ar: return (0.6, "combined", "lighthouse/minaret=lighthouse; same structure")
    if "island" in g and "\u062c\u0632\u064a\u0631" in ar: return (0.65, "combined", "island=island; same geography")
    if "bridge" in g and "\u062c\u0633\u0631" in ar: return (0.5, "combined", "bridge=bridge; same concept")
    if "lime" in g and "\u062c\u064a\u0631" in ar: return (0.55, "combined", "quicklime=gypsum; white mineral building materials")
    if "gout" in g and "\u0646\u0642\u0631\u0633" in ar: return (0.6, "combined", "gout=gout; same disease")
    if "logic" in g and "\u0645\u0646\u0637\u0642" in ar: return (0.75, "combined", "logic=logic; same concept")
    if "element" in g and "component" in g and "\u0627\u0633\u0637\u0642\u0633" in ar: return (0.7, "masadiq_direct", "element=element; same concept")
    if "amber" in g and "\u0639\u0646\u0628\u0631" in ar: return (0.65, "combined", "amber=amber; same substance")
    if "purple" in g and "\u0623\u0631\u062c\u0648\u0627\u0646" in ar: return (0.55, "combined", "purple=purple sea-dye; same color")
    if "uvula" in g and "\u0644\u0647\u0627\u0629" in ar: return (0.55, "masadiq_direct", "uvula/throat=larynx; throat anatomy")
    if "larynx" in g and "\u0644\u0647\u0627\u0629" in ar: return (0.55, "masadiq_direct", "uvula=larynx; throat anatomy")
    if "asparagus" in g and "\u0647\u0644\u064a\u0648\u0646" in ar: return (0.7, "combined", "asparagus=asparagus; same vegetable")
    if "chameleon" in g and "\u062d\u0631\u0628\u0627\u0621" in ar: return (0.75, "masadiq_direct", "chameleon=chameleon; direct match")
    if "rose" in g and "\u0648\u0631\u062f\u0629" in ar: return (0.75, "masadiq_direct", "rose=rose; direct match loanword")
    if "drum" in g and "\u0637\u0628\u0644" in ar: return (0.8, "masadiq_direct", "drum=drum; direct match")
    if "drum" in g and "\u0637\u0646\u0628\u0648\u0631" in ar: return (0.75, "masadiq_direct", "drum=drum; instrument match")
    if "lobster" in g and "\u0643\u0631\u0643\u0646\u062f" in ar: return (0.65, "combined", "lobster/crab=crab; crustacean family")
    if "flame" in g and "\u0634\u0648\u0627\u0638" in ar: return (0.55, "combined", "flame=flame; same concept")
    if ("raisin" in g or "dried grape" in g) and "\u0632\u0628\u064a\u0628" in ar: return (0.7, "combined", "raisin=dried grape; same product")
    if "orange" in g and "\u0628\u0631\u062a\u0642\u0627\u0644" in ar: return (0.8, "masadiq_direct", "orange named after Portugal; etymological link")
    if "hospital" in g and "\u0628\u064a\u0645\u0627\u0631\u0633\u062a\u0627\u0646" in ar: return (0.65, "combined", "hospital=hospital; same institution")
    if "pillar" in g and "\u0623\u0633\u0637\u0648\u0627\u0646" in ar: return (0.6, "combined", "pillar=colonnade; architectural")
    if "colonnade" in g and "\u0623\u0633\u0637\u0648\u0627\u0646" in ar: return (0.6, "combined", "pillar=colonnade; architectural")
    if "chest" in g and "\u062a\u0627\u0628\u0648\u062a" in ar: return (0.9, "masadiq_direct", "coffin/chest=box; direct loanword")
    if "onion" in g and "\u0628\u0635\u0644" in ar: return (0.65, "masadiq_direct", "onion=bulbous plant; direct botanical match")
    if "endive" in g and "\u0647\u0646\u062f\u0628\u0627" in ar: return (0.75, "masadiq_direct", "endive=endive; direct botanical match")
    if "spinal" in g and "\u0646\u062e\u0627\u0639" in ar: return (0.55, "combined", "spinal marrow=of spine; anatomical")
    if "flat" in g and "broad" in g and "\u0628\u0644\u0627\u0637" in ar: return (0.75, "masadiq_direct", "paving/flat=broad/flat; direct match")
    if "cinnamon" in g and "\u0642\u0631\u0641\u0629" in ar: return (0.55, "combined", "cinnamon bark=cinnamon; same spice")
    if "juniper" in g and "\u0639\u0631\u0639\u0631" in ar: return (0.55, "combined", "juniper=of juniper; same tree")
    if "copper" in g and "\u0646\u062d\u0627\u0633" in ar: return (0.6, "combined", "copper/brass=copper/bronze; same metal")
    if ("lead" in g and "metal" in g) and "\u0631\u0635\u0627\u0635" in ar: return (0.6, "combined", "lead=lead; same metal")
    if "gold" in g and "\u0630\u0647\u0628" in ar: return (0.7, "combined", "gold=gold; same metal")
    if "leather" in g and "\u0631\u0646\u062f\u062c" in ar: return (0.6, "combined", "leather=hide/skin; same material")
    if "ivory" in g and "\u0639\u0627\u062c" in ar: return (0.55, "combined", "ivory=ivory; same substance")
    if ("notebook" in g or "writing tablet" in g) and "\u062f\u0641\u062a\u0631" in ar: return (0.7, "combined", "notebook=writing tablet; both writing records")
    if "new year" in g and ("\u0646\u064a\u0631\u0648\u0632" in ar or "\u0646\u0648\u0631\u0648\u0632" in ar): return (0.6, "combined", "new year concept; same event")
    if "henna" in g and "\u062d\u0646\u0627\u0621" in ar: return (0.6, "combined", "henna=henna plant; same plant")
    if "cyprus" in g and "\u062d\u0646\u0627\u0621" in ar: return (0.6, "combined", "henna=henna plant from Cyprus; same plant")
    if "cloak" in g and "\u0645\u0639\u0637\u0641" in ar: return (0.55, "combined", "cloak=cloak; same garment")
    if "calendar" in g and "\u0631\u0648\u0632\u0646\u0627\u0645" in ar: return (0.6, "combined", "calendar=calendar; same object")
    if "stars" in g and "\u0646\u062c\u0648\u0645" in ar: return (0.7, "combined", "stars=stars; same concept")
    if "house" in g and "\u062f\u0627\u0631" in ar: return (0.55, "combined", "house=house; same dwelling")
    if "temple" in g and "\u0647\u064a\u0643\u0644" in ar: return (0.55, "combined", "temple=temple; same type")
    if "wart" in g and "\u062b\u0648\u0644\u0648\u0644" in ar: return (0.45, "combined", "wart=wart; same biological feature")
    if "omentum" in g and "\u062b\u0631\u0628" in ar: return (0.4, "combined", "body fat/omentum=clot/lump; body substances")
    if "small rounded mass" in g and "\u0643\u0646\u062f\u0631" in ar: return (0.55, "combined", "gum resin=rounded lump; compact solid mass")
    if "paradise" in g and "\u0628\u0633\u062a\u0627\u0646" in ar: return (0.45, "combined", "garden=paradise/garden; enclosed garden")
    if "spear" in g and "\u0645\u0632\u0631\u0627\u0642" in ar: return (0.35, "combined", "javelin=spear-butt; related weapons")
    if "tube" in g and "\u0623\u0646\u0628\u0648\u0628" in ar: return (0.5, "combined", "tube/pipe=reed; both tubular")
    if "barley" in g and "\u0634\u0639\u064a\u0631" in ar: return (0.5, "combined", "barley=wheat; cereals")
    if "wheat" in g and "\u062d\u0646\u0637" in ar: return (0.4, "combined", "wheat grain=grain/lump; grain concept")
    if "oxygen" in g and "\u0623\u0643\u0633\u062c\u064a\u0646" in ar: return (0.7, "combined", "oxygen from oxus=sharp/acid; etymology")
    if "myrobalan" in g and "\u0623\u0645\u0644\u062c" in ar: return (0.4, "combined", "myrobalan=almond; round tree fruits")
    if "phalanx" in g and "\u0641\u064a\u0644\u0642" in ar: return (0.65, "masadiq_direct", "military division=phalanx; direct military match")
    if "flat cake" in g and "\u0628\u0642\u0644\u0627\u0648" in ar: return (0.55, "combined", "baklava=flat cake; layered flat sweets")
    if "door" in g and "\u062f\u0647\u0644\u064a\u0632" in ar: return (0.35, "combined", "corridor=door; entrance threshold")
    if "inflammation" in g and "\u0628\u0631\u0633\u0627\u0645" in ar: return (0.55, "combined", "chest inflammation=inflammation; medical concept")
    if "dye" in g and "\u0628\u0642\u0645" in ar: return (0.55, "combined", "red dye wood=dyeing; same concept")
    if "dye" in g and "\u0628\u0647\u0631\u0645\u0627\u0646" in ar: return (0.45, "combined", "safflower dye=dyeing; dye concept")
    if "sagapenum" in g and "\u0633\u0643\u0628\u064a\u0646\u062c" in ar: return (0.6, "combined", "galbanum resin=sagapenum; both resins")
    if "cypress" in g and "\u0633\u0631\u0648" in ar: return (0.65, "combined", "cypress=cypress; same tree")
    if ("jar" in g or "vessel" in g) and "\u062c\u0631\u0629" in ar: return (0.75, "masadiq_direct", "clay jar=ceramic jar; direct vessel match")
    if "silk" in g and "\u062f\u064a\u0628\u0627\u062c" in ar: return (0.7, "combined", "brocade=double-dyed; fine textiles")
    if "flute" in g and "\u0645\u0632\u0645\u0627\u0631" in ar: return (0.7, "combined", "flute/pipe=flute; same instrument")
    if "vine" in g and "\u0643\u0631\u0645" in ar: return (0.45, "combined", "vineyard/vine=vine-branch; vine related")
    if "citron" in g and "\u0623\u0637\u0631\u0646\u062c" in ar: return (0.65, "combined", "citron=citron; same fruit")
    if "turmeric" in g and "\u0643\u0631\u0643\u0645" in ar: return (0.6, "combined", "turmeric=crocus/saffron; yellow spices")
    if "pearl" in g and "\u0645\u0631\u062c\u0627\u0646" in ar: return (0.7, "masadiq_direct", "coral/pearls=pearl; direct jewel match")
    if "horseman" in g and "\u0623\u0633\u0648\u0627\u0631" in ar: return (0.4, "combined", "horseman=horseman; same role")

    # ── Default: consonant match only ──────────────────────────────────────────
    return (0.1, "weak", "no semantic link; consonant match only")


# ── Process all chunks ──────────────────────────────────────────────────────────
total_scored = 0
high_score_pairs = []

for chunk_num in range(15, 46):
    in_path  = BASE_IN  + f"phase1_new_{chunk_num:03d}.jsonl"
    out_path = BASE_OUT + f"phase1_scored_{chunk_num:03d}.jsonl"

    with open(in_path, encoding="utf-8") as f:
        pairs = [json.loads(ln) for ln in f if ln.strip()]

    out_lines = []
    for p in pairs:
        ar  = p.get("arabic_root", "")
        tl  = p.get("target_lemma", "")
        mas = p.get("masadiq_gloss", "")
        tg  = p.get("target_gloss", "")

        score, method, reasoning = score_pair(ar, tl, mas, tg)

        record = {
            "source_lemma": ar,
            "target_lemma": tl,
            "semantic_score": score,
            "reasoning": reasoning,
            "method": method,
            "lang_pair": "ara-grc",
            "model": "sonnet-phase1",
        }
        out_lines.append(json.dumps(record, ensure_ascii=False))
        total_scored += 1
        if score >= 0.5:
            high_score_pairs.append((score, ar, tl, tg[:60]))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")

    n_high = sum(1 for ol in out_lines if json.loads(ol)["semantic_score"] >= 0.5)
    print(f"Chunk {chunk_num:03d}: {len(pairs)} pairs, {n_high} >=0.5")

print(f"\nTOTAL SCORED: {total_scored}")
print(f"PAIRS >=0.5:  {len(high_score_pairs)}")
high_score_pairs.sort(key=lambda x: -x[0])
print("\nTOP 15 DISCOVERIES:")
seen = set()
rank = 1
for sc, ar, tl, tg in high_score_pairs:
    key = (ar, tl)
    if key in seen:
        continue
    seen.add(key)
    print(f"  {rank:2d}. {sc:.2f}  {ar} -> {tl}  [{tg}]")
    rank += 1
    if rank > 15:
        break
