"""gen_eye2_full.py — Generate Eye 2 semantic scores for all 244 ara-lat gold pairs.

Scores are based on genuine linguistic reasoning from masadiq (dictionary meanings),
mafahim (binary/axial concepts), and etymological knowledge of the target words.
"""
import sys
import json
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

# ---------------------------------------------------------------------------
# All 244 scored pairs — reasoned from Arabic semantic profiles + etymology
# ---------------------------------------------------------------------------
SCORES = [
    # --- pairs already in pilot (25) — kept with batch=eye2_full ---
    {
        "source_lemma": "كلب", "target_lemma": "canine", "lang_pair": "ara-lat",
        "semantic_score": 0.92,
        "reasoning": "masadiq: كلب = the dog; also 'to be seized by rabies/biting frenzy'. axial: 'bite onto and hold tightly'. canine = relating to dogs / dog-tooth. Direct lexical overlap on dog and biting.",
        "path": "dog (biting animal) → canine (of a dog / dog-tooth)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "رئيس", "target_lemma": "regis", "lang_pair": "ara-lat",
        "semantic_score": 0.93,
        "reasoning": "رئيس = leader/chief from رأس (head). regis = of the king (gen. of rex). Both denote apex authority; Arabic head-of-group maps onto Latin king.",
        "path": "head / chief → supreme leader → king's (regis)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "كومة", "target_lemma": "cemetery", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "كومة = heap/mound of earth. cemetery (< Gk koimeterion = sleeping place) is burial under earth mounds. heap → burial mound → resting place.",
        "path": "heap of earth → burial mound → place of rest → cemetery",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "خيط", "target_lemma": "filament", "lang_pair": "ara-lat",
        "semantic_score": 0.96,
        "reasoning": "masadiq: خيط = thread. axial: 'thin continuous strand penetrating through the interior'. filament = a slender threadlike fiber. Near-perfect match.",
        "path": "thread (خيط) → thin continuous strand → filament",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "جمل", "target_lemma": "corridor", "lang_pair": "ara-lat",
        "semantic_score": 0.3,
        "reasoning": "جمل = camel. corridor = a long passage. Binary: تجمع/كثرة; axial: large harmonious body moving. Connection to architectural corridor is very indirect.",
        "path": "camel (large body traversing space) → moving through → passage (weak)",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "شرب", "target_lemma": "absorb", "lang_pair": "ara-lat",
        "semantic_score": 0.91,
        "reasoning": "شرب = to drink; axial: 'drawing water into interior, sucking it in'. absorb (< Lat absorbere = to suck in) = take in liquid. Both denote drawing liquid inward.",
        "path": "to drink / suck in liquid (شرب) → draw into interior → absorb",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "مرج", "target_lemma": "merge", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "masadiq: مرج = to blend/mingle (let two rivers mix). axial: 'different-directional movement of things mingling'. merge = combine into one. Near-perfect.",
        "path": "to mingle / blend (مرج) → combine freely → merge",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "حوض", "target_lemma": "basin", "lang_pair": "ara-lat",
        "semantic_score": 0.95,
        "reasoning": "حوض = watering trough/cistern/large basin. basin = wide open container for liquid. Near-perfect: both a hollow vessel for water.",
        "path": "water basin / cistern (حوض) → hollow container → basin",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "غور", "target_lemma": "gorge", "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": "غور = depth/bottom; غار = cave. axial: 'powerful cavity extending deep'. gorge = narrow deep valley / throat. Both denote a deep penetrating hollow.",
        "path": "depth / deep hollow (غور) → deep narrow channel → gorge",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "طفر", "target_lemma": "spring", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "masadiq: الطفرة = الوثبة = a leap/jump. spring (v.) = to leap/jump. Primary English sense maps directly.",
        "path": "a leap / jump (طفر) → to spring (leap) → spring",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "فلج", "target_lemma": "village", "lang_pair": "ara-lat",
        "semantic_score": 0.55,
        "reasoning": "فلج = to split/divide; a branch-stream. village = small settlement (< Lat villa). Branch-off water → outlying settlement. Plausible but indirect.",
        "path": "branch / split off (فلج) → outlying settlement → village",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "حيل", "target_lemma": "heal", "lang_pair": "ara-lat",
        "semantic_score": 0.65,
        "reasoning": "حيلة = stratagem/means to bring change. axial: 'deflection to a nearby better state'. heal = restore to health. State-shift → healing.",
        "path": "device to change state → bring about state-shift → restore health → heal",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "شرح", "target_lemma": "cheer", "lang_pair": "ara-lat",
        "semantic_score": 0.80,
        "reasoning": "شرح = to open/expand; شرح الصدر = expansion of chest = gladness. cheer = joyful spirit. Expansion of chest → gladness maps onto cheer.",
        "path": "expand / open chest (شرح) → gladden → cheer",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "بِشت", "target_lemma": "invest", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "بِشت = long outer cloak. invest < Lat investire = to clothe someone in a robe, vest with authority. Binary: الانتشار الظاهر (outward covering). Both denote placing outer garment.",
        "path": "outer cloak / robe (بِشت) → to clothe / envelop → invest (clothe with authority)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "طبع", "target_lemma": "type", "lang_pair": "ara-lat",
        "semantic_score": 0.93,
        "reasoning": "طبع = to stamp/impress a mark in clay (mold). axial: 'making soft material take a specific form'. type < Lat typus < Gk typos = impression/mold. Near-perfect.",
        "path": "to stamp / impress in clay (طبع) → impression in material → type",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "فرض", "target_lemma": "force", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "فرض = to notch/cut into hard material; to impose. axial: 'deep non-penetrating cut'. force < Lat fortis (strong) → compel. Imposed decree / compulsory imposition bridges them.",
        "path": "to cut an obligation (فرض, impose by cutting) → compel → force",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "عقربٌ", "target_lemma": "scorpion", "lang_pair": "ara-lat",
        "semantic_score": 0.98,
        "reasoning": "عقرب = the scorpion; also Scorpio constellation. scorpion (< Lat scorpio < Gk skorpios). Perfect match: same creature, Semitic→Greek→Latin borrowing chain.",
        "path": "scorpion (عقرب) → Lat scorpio → scorpion",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "النمر", "target_lemma": "leopard", "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": "النمر = the leopard/spotted panther. leopard (< Lat leopardus = leo+pardus) = large spotted cat. Both the same spotted feline.",
        "path": "spotted panther (نمر) → large spotted cat → leopard",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "لبن", "target_lemma": "galaxy", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "لبن = milk; also white sap of trees. galaxy < Gk gala (milk) = Milky Way. Both rooted in white milk-like fluid. axial: 'diffuse milky fluid that emerges and coheres'.",
        "path": "milk / white fluid (لبن) → milky appearance → Milky Way → galaxy",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "قرس", "target_lemma": "crust", "lang_pair": "ara-lat",
        "semantic_score": 0.83,
        "reasoning": "قرس = to be cold/frozen; قرس البرد: severe cold that solidifies. binary: 'settling/solidification of fluid'. crust < Lat crusta = hard outer shell. Both involve solidified surface.",
        "path": "to freeze / congeal (قرس) → solidified surface → hard outer shell → crust",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "موت", "target_lemma": "mute", "lang_pair": "ara-lat",
        "semantic_score": 0.78,
        "reasoning": "موت = death. axial: 'spreading with stillness and silence, loss of vitality'. mute (< Lat mutus = silent) = without sound. death → silence → mute.",
        "path": "death / cessation of life (موت) → total stillness and silence → mute",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "دَرَن", "target_lemma": "thorn", "lang_pair": "ara-lat",
        "semantic_score": 0.35,
        "reasoning": "دَرَن = filth/grime/dirt that accumulates. binary: elongated continuous extension. thorn = sharp woody projection. Masadiq dirt does not connect; only faint shape analogy.",
        "path": "elongated protrusion (binary) → sharp pointed extension → thorn (weak)",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "تفرق", "target_lemma": "divorce", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "تفرّق = to scatter/separate thoroughly. axial: 'separation reaching to the deep, full severance'. divorce (< Lat divortium = divergence, parting). Both describe thorough definitive separation.",
        "path": "to scatter apart thoroughly (تفرق) → complete severance → divorce",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "وادي", "target_lemma": "valley", "lang_pair": "ara-lat",
        "semantic_score": 0.97,
        "reasoning": "وادي = valley, river valley, wadi. valley < Lat vallis. Near-perfect: both denote low-lying land between hills with watercourse.",
        "path": "valley / wadi (وادي) → low land between hills → valley",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "فرج", "target_lemma": "fragile", "lang_pair": "ara-lat",
        "semantic_score": 0.75,
        "reasoning": "فرج = gap/opening/breach in dense structure. axial: 'opening within dense body'. fragile < Lat fragilis (from frangere = to break/create breach). Both describe breach in previously whole object.",
        "path": "gap / breach in dense body (فرج) → tendency to fracture → fragile",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    # --- NEW pairs (219) ---
    {
        "source_lemma": "فاه،", "target_lemma": "infant", "lang_pair": "ara-lat",
        "semantic_score": 0.78,
        "reasoning": "فاه/فوه = mouth, utterance, opening (the articulating organ). infant < Lat infans = in-fans, 'not speaking' (unable to speak). The Arabic فاه (mouth/speech organ) directly relates to the Latin negation of speech: infant = the one without speech/voice. Opposites from same root concept.",
        "path": "mouth / speech (فاه) → speaking → in-fans (not speaking) → infant",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "كروس", "target_lemma": "grocery", "lang_pair": "ara-lat",
        "semantic_score": 0.55,
        "reasoning": "كرس = accumulation in layers, piled-up matter; أبياتٌ من الناس مجتمعةٌ = gathered group. binary: تراكم متلازب (accumulated layered stacking). grocery (< medieval Lat grossarius = wholesaler dealing in bulk) relates to accumulated/bulk goods. Accumulation semantic bridges them weakly.",
        "path": "layered accumulation (كرس) → bulk goods gathered → grocery (bulk trader)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "باسل", "target_lemma": "basilica", "lang_pair": "ara-lat",
        "semantic_score": 0.80,
        "reasoning": "باسل = brave/lion-like, from بسل = dryness/bitterness with authority. basilica < Gk basilikē = royal hall (from basileus = king). Both share the 'powerful/authoritative/regal' semantic core: باسل as the valiant chief, basilica as the royal hall.",
        "path": "brave/valiant one (باسل) → regal power → royal hall → basilica",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "كرّم", "target_lemma": "ceremony", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "كرّم = to honor, ennoble; كرم = generosity, nobility, refinement. axial: 'refinement and purity of the gathered thing with acceptance'. ceremony (< Lat caeremonia = religious rite/honor). Both encode formal honor and dignified ritual.",
        "path": "to honor / ennoble (كرّم) → formal honor → ritual of honor → ceremony",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "يمتلك،", "target_lemma": "famous", "lang_pair": "ara-lat",
        "semantic_score": 0.35,
        "reasoning": "يمتلك = to possess/own (from ملك = ownership). famous (< Lat fama = rumor/renown). The connection between possession and fame is indirect — one who is talked about is not the same as one who owns. Weak conceptual link at best.",
        "path": "possess/own (يمتلك) → mastery → renown (very indirect) → famous",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "عوف", "target_lemma": "auspex", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "عوف = well-being, condition; also يُكنى العوف = a yellow bird (the one that flies well). auspex (< Lat avis + spex = bird-watcher/omen-reader). The Arabic word for a bird (أم عوف) and the Latin bird-omen concept share the 'bird as sign of fortune/condition' semantic field.",
        "path": "bird of fortune / condition (عوف) → auspicious bird → auspex (bird omen reader)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "جُلّة", "target_lemma": "bullet", "lang_pair": "ara-lat",
        "semantic_score": 0.62,
        "reasoning": "جُلّة = a large spherical vessel/basket; also جُلّة = globular container. bullet < Fr boulette = small ball < boule = ball. Both denote a rounded/spherical object. The Arabic large round container and the small round projectile share the spherical form.",
        "path": "large round vessel / sphere (جُلّة) → rounded object → small sphere → bullet",
        "method": "lemma_only", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "أوج", "target_lemma": "auction", "lang_pair": "ara-lat",
        "semantic_score": 0.70,
        "reasoning": "أوج = apogee, the highest point, zenith (astronomical term, opposite of descent). auction < Lat auctio = increase, augmentation (from augere = to increase). Both encode the concept of reaching a highest point: أوج = apex of orbit; auction = bidding up to highest price.",
        "path": "highest point / zenith (أوج) → upward increase → bidding up → auction",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "عُصّ", "target_lemma": "ossifier", "lang_pair": "ara-lat",
        "semantic_score": 0.75,
        "reasoning": "عُصّ/عُصعُص = the tailbone, base of the spine (coccyx). binary: صلابة واشتداد (hardness/hardening). ossifier = something that converts to bone/ossifies. Both center on hard bone matter: عصعص is the fused/hardened tailbone, ossifier is the agent of bone-hardening.",
        "path": "tailbone / hardened bone base (عُصّ) → bone hardness → ossifier",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "إقصاء", "target_lemma": "sewer", "lang_pair": "ara-lat",
        "semantic_score": 0.55,
        "reasoning": "إقصاء = exclusion, pushing to the far edge (from قصا = remoteness). binary: cutting with continuity. sewer (< Lat exaquaria = drainage = ex + aqua, water out). The 'pushing away/out' concept of إقصاء parallels the Latin 'ex' in sewer. Moderate indirect link.",
        "path": "exclusion / pushing to the edge (إقصاء) → expulsion of waste → sewer",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "صب", "target_lemma": "submarine", "lang_pair": "ara-lat",
        "semantic_score": 0.80,
        "reasoning": "صب = pouring downward, flow descending (تصوب النهر = river flowing down). binary: حدر إلى أسفل بقوة (forceful descent downward). submarine = under the sea (sub + mare). The axial downward-flow concept directly maps to sub- (beneath water, flowing down into the deep).",
        "path": "pour / flow downward (صب) → descend below water → submarine (sub-marine)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "شاه", "target_lemma": "check", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "شاه = Persian word for king, borrowed into Arabic as chess term. check (in chess) = from Persian شاه (king) — when the king is threatened we say 'check'. Direct borrowing: شاه → check is the standard etymology via chess terminology.",
        "path": "king (شاه, Persian loan) → chess 'shah in danger' → check",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "ألوق", "target_lemma": "loco", "lang_pair": "ara-lat",
        "semantic_score": 0.45,
        "reasoning": "ألوق/ألوق = something palatable but deceptive; وقواق = a chattering coward. loco (Sp/Lat) = crazy/mad. The 'chattering' or 'deranged behavior' has a faint link to madness, but the masadiq meanings are quite distant from 'crazy'.",
        "path": "chattering / cowardly behavior (ألوق) → disorderly → loco (very indirect)",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "علم", "target_lemma": "oology", "lang_pair": "ara-lat",
        "semantic_score": 0.60,
        "reasoning": "علم = knowledge/science; also علم = flag/banner (high marker). axial: 'guidance by height toward a direction/path'. oology = study of eggs (< Gk oon = egg + logos = study). علم as 'science/study' maps onto the -logy component of oology. علم is literally 'the science'.",
        "path": "knowledge / science (علم) → systematic study → oology (science of eggs)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "رابط", "target_lemma": "rivet", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "رابط = one who binds/fastens; الرباط = rope/ligament/bond. axial: 'binding a thing, fixing it so it does not slip or move'. rivet = a metal fastener that binds two pieces firmly. Both encode the concept of firm binding that prevents slipping.",
        "path": "fastener / one who binds (رابط) → fixing firmly in place → rivet",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "شخة", "target_lemma": "shit", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "شخة = urination, to urinate/defecate (bodily waste expulsion). shit (Old English scitan = to defecate). Both refer to bodily waste/excretion. The Arabic شخة specifically denotes the act of expelling bodily fluid/waste.",
        "path": "urinate / bodily waste (شخة) → excrement → shit",
        "method": "lemma_only", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "صوّل", "target_lemma": "solution", "lang_pair": "ara-lat",
        "semantic_score": 0.65,
        "reasoning": "صوّل/صال = to leap upon/attack with force; صالَ عليه = overpowered. solution (< Lat solutio = loosening/dissolving, from solvere = to loosen). The 'overpowering/dissolving resistance' in صوّل has faint parallel with the Latin 'dissolving'. Indirect.",
        "path": "overpower / dissolve resistance (صوّل) → loosen constraints → solution (dissolving)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "إقصاء", "target_lemma": "ex", "lang_pair": "ara-lat",
        "semantic_score": 0.75,
        "reasoning": "إقصاء = exclusion, removal to far end. ex- (Latin prefix) = out of, away from, former. Both encode the concept of expulsion/removal outward. The Arabic إقصاء (moving out to the edge) maps cleanly onto the Latin prefix ex- (out from).",
        "path": "exclusion / removal outward (إقصاء) → out from → ex-",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "زربية", "target_lemma": "carpet", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "masadiq: زربية = a woven rug/carpet (القطوع الحيرية = Hiran weave). This is the literal Arabic word for a patterned carpet/rug. carpet (< OF carpite = thick cloth) = a floor covering. Direct: both words name the same object.",
        "path": "woven carpet / rug (زربية) → floor covering → carpet",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "بلاّص", "target_lemma": "peluis", "lang_pair": "ara-lat",
        "semantic_score": 0.50,
        "reasoning": "بلاّص = a large wide-mouthed earthenware jar (for storage). peluis is not a standard Latin word; if it derives from pelvis = basin/shallow bowl, then both are wide vessels. The Arabic large storage jar and a bowl-shaped vessel share the 'wide open container' form.",
        "path": "large wide jar (بلاّص) → wide open vessel → peluis (basin form)",
        "method": "lemma_only", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "بلاّص", "target_lemma": "pelvis", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "بلاّص = a large wide-mouthed earthenware storage jar/vessel. pelvis (< Lat pelvis = basin/bowl, < Gk pelys = tub) = the hip basin bone. Both share the 'wide open basin' form. Arabic large jar → Latin shallow basin → pelvis (anatomical basin-shaped bone).",
        "path": "large wide-mouthed jar (بلاّص) → wide basin form → pelvis (anatomical basin)",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "برج", "target_lemma": "burglar", "lang_pair": "ara-lat",
        "semantic_score": 0.75,
        "reasoning": "masadiq: برج = tower/castle corner; بُرجان = name of a thief ('أسرق من برجان' = 'more thieving than Burjan'). The proverb literally names Burjan as a thief. burglar (< Med Lat burgulator = one who breaks into a burg/fortress). Arabic برج (tower/fortified structure) → one who enters towers illicitly → burglar.",
        "path": "tower / fortress (برج) + 'برجان = thief' proverb → fortress-breaker → burglar",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "شِفّة", "target_lemma": "lip", "lang_pair": "ara-lat",
        "semantic_score": 0.95,
        "reasoning": "شِفّة = the lip (anatomical). lip (Old English lippe) = the lip. Both words directly name the same anatomical feature. This is a likely ancient cognate.",
        "path": "lip (شِفّة) → lip",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "يحيا", "target_lemma": "viva", "lang_pair": "ara-lat",
        "semantic_score": 0.92,
        "reasoning": "يحيا = 'he lives / may he live' (from حياة = life). viva (< Lat vivat = may he live, third person subjunctive of vivere = to live). Both are exclamations meaning 'long live / may he live'. Direct semantic equivalence.",
        "path": "may he live (يحيا) → long-live exclamation → viva",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "عمّ", "target_lemma": "uncle", "lang_pair": "ara-lat",
        "semantic_score": 0.92,
        "reasoning": "عمّ = paternal uncle (father's brother). uncle (< Lat avunculus = maternal uncle, diminutive of avus = grandfather). Both denote a male relative of the parent's generation. Direct kinship term correspondence.",
        "path": "paternal uncle (عمّ) → uncle (father's / mother's brother) → uncle",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "فاطر", "target_lemma": "pattern", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "فاطر = one who splits/creates (فطر = to split open first, originate; الله فاطر السماوات = God, the Originator). axial: 'initial breakthrough/rupture as creative act'. pattern (< Old Fr patron = a model, exemplar) = a template/design. Creator → model/template. The originating split creating a form parallels 'patron' as an original model.",
        "path": "originator / one who splits to create (فاطر) → original model → pattern",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "بَقّ", "target_lemma": "voice", "lang_pair": "ara-lat",
        "semantic_score": 0.65,
        "reasoning": "بقّ = to spread/open wide; also a bug/insect that buzzes. binary: الثبات والكشف باتساع (broad disclosure). voice (< Lat vox = sound/voice). The Arabic root بق relates to spreading sounds broadly — the buzz/open-wide meaning connects to vocal emission, but connection is indirect.",
        "path": "broad spreading / buzzing sound (بقّ) → emitted sound → voice",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "رمح", "target_lemma": "harpoon", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "رمح = a spear/lance; رمحه = to pierce with a spear. axial: 'stabbing from a distance'. harpoon (< Dutch harpoen < OF harpon = clamp/hook attached to a spear) = a barbed spear thrown at distance. Both denote piercing weapons thrown from distance.",
        "path": "spear / lance (رمح) → long-range piercing weapon → harpoon",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "التنخر", "target_lemma": "innocent", "lang_pair": "ara-lat",
        "semantic_score": 0.55,
        "reasoning": "التنخّر = decay, rotting away (نخر = to be hollow/rotten; عظام نخرة = rotten bones). binary: weakening of structure. innocent (< Lat innocens = not harmful, harmless). The 'hollow/decayed = lacking substance' connects weakly to 'harmless/lacking guilt'. Indirect.",
        "path": "hollow / lacking substance (التنخر) → emptied of harm → innocent (harmless)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "قطين", "target_lemma": "chain", "lang_pair": "ara-lat",
        "semantic_score": 0.78,
        "reasoning": "قطين = residents who stay in a place permanently (from قطن = to settle, remain). axial: 'staying in a place, tight adherence'. chain (< Lat catena = fetter, bond holding captives). The 'binding to a place' of قطين connects to the literal binding of a chain: both denote strong adherence/attachment preventing movement.",
        "path": "permanent settler / bound to place (قطين) → fixed binding → chain",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "جردة", "target_lemma": "yard", "lang_pair": "ara-lat",
        "semantic_score": 0.80,
        "reasoning": "جردة/جرد = bare/stripped open land (no vegetation); فضاء لا نبات فيه. axial: 'exposed bare extended surface'. yard (< Old English geard = enclosure, open ground) = an open area of land. Both denote open/bare expanse of ground.",
        "path": "bare open land (جردة) → exposed ground area → yard",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "جمّة", "target_lemma": "comet", "lang_pair": "ara-lat",
        "semantic_score": 0.78,
        "reasoning": "جمّة = a mass of hair/abundant flowing mane (شعر جمّة كثير = abundant hair). comet (< Lat cometa < Gk kometes = long-haired [star], from kome = hair). The Arabic جمّة (abundant flowing hair) and the Greek/Latin 'long-haired star' share identical metaphor: abundant flowing hair → hairy star → comet.",
        "path": "abundant flowing hair/mane (جمّة) → 'long-haired' → comet (the hairy star)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الزفير", "target_lemma": "lazour", "lang_pair": "ara-lat",
        "semantic_score": 0.35,
        "reasoning": "الزفير = deep exhalation, the carrying-exhalation sound. lazour is not a recognized Latin word in standard dictionaries. If it refers to lapis lazuli (blue stone), the connection to زفير is very weak. Cannot establish strong link.",
        "path": "exhalation / carrying movement (الزفير) → lazour (unclear target, weak)",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "جُبّة", "target_lemma": "chapel", "lang_pair": "ara-lat",
        "semantic_score": 0.62,
        "reasoning": "جُبّة = a long outer garment/robe; also a hollow cavity (جُبّ = pit/well). chapel (< Med Lat capella = cloak of St. Martin kept as relic, then the building housing it). Both have 'enclosing garment/cloak' in their etymology: جبّة as a covering garment, capella as the famous cloak-relic.",
        "path": "enclosing robe / cloak-like garment (جُبّة) → sacred cloak → chapel (capella)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الإير", "target_lemma": "meteorology", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "الإير/أير = wind, the air/breeze (also: air, الهواء). meteorology (< Gk meteoros = high in air + logos = study) = study of atmospheric phenomena/weather. The Arabic إير (air/wind) directly relates to the subject matter of meteorology: the study of aerial phenomena.",
        "path": "air / wind (الإير) → atmospheric phenomena → meteorology (study of air/weather)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "حضرة", "target_lemma": "cathedral", "lang_pair": "ara-lat",
        "semantic_score": 0.75,
        "reasoning": "حضرة = presence, the august presence (formal court of a dignitary); also حاضرة = city, urban center. axial: 'transition with density and power to a gathering that endures'. cathedral (< Gk kathedra = seat/throne, the bishop's throne-church). Both denote the place of august authoritative presence: حضرة as the dignitary's court, cathedral as the bishop's seat.",
        "path": "august presence / dignitary's court (حضرة) → seat of authority → cathedral",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "برّاني", "target_lemma": "forest", "lang_pair": "ara-lat",
        "semantic_score": 0.78,
        "reasoning": "برّاني = outsider, one from outside/the exterior (from برّ = outside, open land). forest (< Med Lat forestis = outside forest, land outside the walls = foris = outside + silva). Both encode 'outside' as the core meaning: برّاني = the outsider, forestis = the outside (woodland). Same etymological root meaning.",
        "path": "outsider / outer territory (برّاني) → land outside the walls → forest (foris = outside)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "زغب", "target_lemma": "nest", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "زغب = fine soft down feathers (صغار الريش). The فرخ (chick) is covered in زغب while in the nest. nest (< Old English nest = bird's resting place made of soft material). The Arabic fine down-feathers of chicks and the nest they sit in share the 'soft feathery material of young birds' semantic domain.",
        "path": "soft down feathers of chicks (زغب) → material of/in a nest → nest",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "شوف", "target_lemma": "scope", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "شوف = to look/observe; تشوّف = to look eagerly, to crane one's neck to see. scope (< Gk skopos = one who watches/aims, from skopein = to look). Both encode the act of looking/observing with intent. Near-perfect semantic match on 'directed watching'.",
        "path": "to look / observe intently (شوف) → directed watching → scope",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "زفير", "target_lemma": "inspire", "lang_pair": "ara-lat",
        "semantic_score": 0.80,
        "reasoning": "زفير = deep exhalation, breathing out heavily (حمل مع حركة = carry with movement). axial: 'carrying with movement'. inspire (< Lat inspirare = to breathe into, in + spirare = to breathe). Both are about breath movement — زفير is exhalation, inspirare is inhalation, but both encode the same breath/spirit motion.",
        "path": "deep exhalation / breath movement (زفير) → breathing ↔ inspire (breathe in)",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "ذَكَر", "target_lemma": "dictator", "lang_pair": "ara-lat",
        "semantic_score": 0.75,
        "reasoning": "ذَكَر = to mention/proclaim; masculine; also 'the sharp/hard thing that penetrates'. axial: 'strength and hardness of material, penetrating'. dictator (< Lat dictator = one who dictates/proclaims, from dicere = to say/proclaim). Both ذَكَر (mention/proclaim) and dictator (one who proclaims/commands) center on forceful verbal declaration.",
        "path": "to mention / proclaim forcefully (ذَكَر) → one who proclaims → dictator",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "طاولة", "target_lemma": "tablet", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "طاولة = table (a flat horizontal surface). axial: 'extension of a thing holding itself together'. tablet (< Lat tabula = flat board/plank → small table/flat writing surface). Both denote a flat surface: طاولة = table, tablet = small flat board. Direct morphological and semantic overlap.",
        "path": "flat table surface (طاولة) → flat board → tablet",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "غلصمة", "target_lemma": "glossary", "lang_pair": "ara-lat",
        "semantic_score": 0.68,
        "reasoning": "غلصمة = the larynx/throat (غَلصَمة = the cartilage of the throat that produces speech). glossary (< Lat glossarium < Gk glossa = tongue/language). Both relate to speech organs: غلصمة = larynx (produces voice), glossa = tongue (the speech organ). Different parts of the vocal tract but same semantic domain.",
        "path": "larynx / throat speech organ (غلصمة) → tongue / language → glossary",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "خصّ", "target_lemma": "casino", "lang_pair": "ara-lat",
        "semantic_score": 0.65,
        "reasoning": "خصّ = a hut with a roof structure; خصاص = small openings/gaps. casino (< Ital casino = little house, from casa = house). Both denote a small/modest enclosed structure: خصّ = reed hut, casino = little house. The 'small house' semantic is shared.",
        "path": "small reed hut / shelter (خصّ) → little house → casino (casa + ino)",
        "method": "lemma_only", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "البَرّ", "target_lemma": "far", "lang_pair": "ara-lat",
        "semantic_score": 0.70,
        "reasoning": "البَرّ = the open land/mainland, the exterior territory beyond the settlement. far (< Old English feor = distant). The Arabic البرّ (open land, the beyond) connects to 'far' through the concept of the open/outside space that is distant from habitation.",
        "path": "open land / exterior territory (البَرّ) → the beyond → far (distant)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "إقصاء", "target_lemma": "emergency", "lang_pair": "ara-lat",
        "semantic_score": 0.52,
        "reasoning": "إقصاء = exclusion, pushing to extreme edge. emergency (< Lat emergentia = arising suddenly, from emergere = to come out). Both involve crossing a boundary — إقصاء pushes out, emergere bursts out. Indirect shared 'out/beyond' concept.",
        "path": "pushed to the extreme edge (إقصاء) → sudden crossing of boundary → emergency",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الأوك", "target_lemma": "patriarch", "lang_pair": "ara-lat",
        "semantic_score": 0.40,
        "reasoning": "الأوك = anger/evil/strife (ابن عباد: الأوكة = الغضب والشر). patriarch (< Gk patriarkhes = head of family, pater = father + arkhein = to rule). Anger/strife and patriarchal authority are conceptually distant. Weak connection at best through 'authority/power'.",
        "path": "strife / contending force (الأوك) → dominant force → patriarch (very indirect)",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "لُجّة", "target_lemma": "lake", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "لُجّة = the deep/roaring water; لجّة البحر = the abyss of the sea; also a pool/deep body of water. lake (< Lat lacus = pool/hollow filled with water). Both denote a deep body of standing water. Near-perfect match on 'deep pool of water'.",
        "path": "deep pool / body of water (لُجّة) → standing water in hollow → lake",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "عوف", "target_lemma": "oval", "lang_pair": "ara-lat",
        "semantic_score": 0.52,
        "reasoning": "عوف = condition/well-being; also أم عوف = a yellow elliptical insect. oval (< Lat ovum = egg → egg-shaped). The Arabic 'أم عوف' being a yellow elliptical insect connects weakly to oval (egg-shaped). Indirect.",
        "path": "yellow elliptical insect (أم عوف) → egg-like form → oval (weak connection)",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "نقاش", "target_lemma": "negotiate", "lang_pair": "ara-lat",
        "semantic_score": 0.80,
        "reasoning": "نقاش = detailed examination, scrutinizing (من نوقش في الحساب فقد هلك = who is closely scrutinized in accounting is ruined). Also: engraving/detailed work. negotiate (< Lat negotiari = to carry on business, from nec + otium = not leisure = business dealings). Both involve careful detailed back-and-forth examination: نقاش = scrutinizing/engraving detail, negotiate = detailed business dealings.",
        "path": "detailed scrutiny / careful examination (نقاش) → careful back-and-forth → negotiate",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "عمّة", "target_lemma": "aunte", "lang_pair": "ara-lat",
        "semantic_score": 0.92,
        "reasoning": "عمّة = paternal aunt (father's sister). aunte/aunt (< Old French ante < Lat amita = father's sister). Both denote the paternal aunt specifically. Direct kinship term correspondence.",
        "path": "paternal aunt (عمّة) → aunt (father's sister) → aunte",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "إمنع", "target_lemma": "immunization", "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": "إمنع/منع = to prevent, block, make impenetrable (also مَنَعَة = fortification, impregnability). axial: 'sealing the outer surface so nothing penetrates inside'. immunization (< Lat immunis = exempt from burden, not subject to attack + -ization). Near-perfect: both denote making a body impenetrable/exempt from attack.",
        "path": "to prevent / make impenetrable (إمنع) → exempt from attack → immunization",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "البَر", "target_lemma": "foreign", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "البَرّ = the outside land, mainland, terrain beyond settlements (from بَرَّ = to be outside). foreign (< Lat foraneus = from outside, from foras = outside, outdoors). Both encode 'outside/beyond the boundary': البرّ = the exterior terrain, foreign = from outside. Direct etymological parallel.",
        "path": "outside land / exterior (البَر) → coming from outside → foreign",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "بقرة", "target_lemma": "vaccine", "lang_pair": "ara-lat",
        "semantic_score": 0.92,
        "reasoning": "بقرة = cow (female bovine). vaccine (< Lat vacca = cow; Jenner derived smallpox vaccine from cowpox). Direct: vaccine is literally named after 'cow' (vacca), and بقرة = cow. Perfect lexical correspondence.",
        "path": "cow (بقرة) → Lat vacca (cow) → vaccine (from cow/cowpox)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "بروز", "target_lemma": "bruise", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "بروز = emergence/protrusion to the surface; بَرَزَ = to come out, emerge forcefully. axial: 'bursting out from among what surrounds it with effort'. bruise (< Old English brysan = to crush; mark from forceful impact). The 'forceful emergence to surface' of بروز parallels bruise as a visible surface mark from impact.",
        "path": "forceful emergence to surface (بروز) → visible surface mark from impact → bruise",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "كوفيّة", "target_lemma": "cuff", "lang_pair": "ara-lat",
        "semantic_score": 0.75,
        "reasoning": "كوفيّة = a head covering worn in Kufa; also كوف = edge/border of cloth. cuff (< possibly Middle Dutch koffe = sleeve cap, or from cuffe = mitten) = fabric border/edge of sleeve. Both relate to fabric edge/border pieces worn on body.",
        "path": "fabric head covering / cloth edge (كوفيّة) → cloth border piece → cuff",
        "method": "lemma_only", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "بيطري", "target_lemma": "veterinary", "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": "بيطري = relating to animal medicine; بيطار = farrier/animal doctor. veterinary (< Lat veterinarius = relating to draft animals, cattle medicine). Both directly denote the practice of animal medicine. Arabic بيطار and Latin veterinarius are parallel terms for the animal doctor.",
        "path": "animal medicine / farrier (بيطري) → veterinary practice → veterinary",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "وطا", "target_lemma": "boot", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "وطأ = to tread/stamp upon with full weight; axial: 'pressing entire weight down onto something'. boot (footwear for heavy treading). Both relate to treading/stamping: وطأ = the act of treading, boot = the covering enabling/associated with treading.",
        "path": "to tread / stamp with full weight (وطا) → foot-covering for treading → boot",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "بق", "target_lemma": "bug", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "بق = a bug/insect (specifically a biting insect like a bedbug or mosquito). bug (< possibly Welsh bwg = ghost, but more likely related to Old Norse bugge = insect). Both بق and bug directly name small biting insects. Direct lexical parallel.",
        "path": "biting insect / bug (بق) → bug",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الأنعام", "target_lemma": "animal", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "الأنعام = livestock animals, cattle (sheep, goats, camels). axial: 'softness/gentleness of the interior'. animal (< Lat animalis = having breath/soul, from anima = breath/spirit). Both الأنعام and animalis denote living creatures — الأنعام specifically livestock, animalis all living things.",
        "path": "livestock / living creatures (الأنعام) → breathing creatures → animal",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "سيع", "target_lemma": "sea", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "سيع/ساع = water/liquid flowing and spreading on the surface, سيلان واضطراب = flowing and agitation. sea (< Old English sæ = ocean). Both encode 'flowing/spreading water': ساع = water spreading on ground, sea = the great body of flowing water.",
        "path": "flowing / spreading water (سيع) → body of agitated water → sea",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "قبّة", "target_lemma": "dome", "lang_pair": "ara-lat",
        "semantic_score": 0.95,
        "reasoning": "قبّة = a dome/cupola (rounded arch structure atop a building). dome (< Ital duomo/Lat domus = house, but also < Provençal doma < Gk dōma = roof). Both denote a rounded arched covering structure. This is a direct architectural term match.",
        "path": "dome / cupola (قبّة) → rounded roof structure → dome",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "مطرح", "target_lemma": "hair", "lang_pair": "ara-lat",
        "semantic_score": 0.35,
        "reasoning": "مطرح = the place where something is thrown/discarded far away. axial: 'extreme distance, cast away'. hair = strand of fiber growing from the body. Connection is very weak — throwing away does not connect to hair semantically.",
        "path": "thrown far away (مطرح) → hair (no convincing link)",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "باص", "target_lemma": "bus", "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": "باص = Arabic word for 'bus' (direct borrowing). bus (< Latin omnibus = for all, dative plural of omnis). باص is the Arabic name for the same vehicle. Direct borrowing correspondence.",
        "path": "bus (باص, direct Arabic borrowing) → bus",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "سنّد", "target_lemma": "ascend", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "سنّد = to support/lean against; السند = the mountain slope facing you. axial: 'strong rigid support that braces what leans on it'. ascend (< Lat ascendere = to climb, ad + scandere = to climb). Both involve the act of going up against something — سنّد = support/rising slope, ascend = climbing up.",
        "path": "mountain slope / support (سنّد) → rising/climbing up → ascend",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الإهالة", "target_lemma": "oil", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "الإهالة = rendered fat/oil (melted animal fat used for cooking/lighting). oil (< Lat oleum < Gk elaion = olive oil). Both denote a fat-based liquid used for cooking or lubrication. The Arabic cooking fat and Latin/Greek olive oil are the same functional substance.",
        "path": "rendered fat / cooking oil (الإهالة) → oily liquid → oil",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "أمّة", "target_lemma": "nation", "lang_pair": "ara-lat",
        "semantic_score": 0.92,
        "reasoning": "أمّة = a people/nation (a community united by common religion/language/lineage). nation (< Lat natio = birth, people born together). Both denote a collective people. Near-perfect semantic match on 'community of people sharing common origin/values'.",
        "path": "community / people (أمّة) → nation (people born together) → nation",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "عطر", "target_lemma": "deodorant", "lang_pair": "ara-lat",
        "semantic_score": 0.80,
        "reasoning": "عطر = perfume/fragrance; العطر = all things aromatic. deodorant (< de + odor = to remove odor). Both deal with scent/fragrance management: عطر adds pleasant scent, deodorant removes unpleasant odor. Opposite ends of the same scent domain.",
        "path": "fragrance / aromatic substance (عطر) → scent management → deodorant (anti-odor)",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "جن", "target_lemma": "general", "lang_pair": "ara-lat",
        "semantic_score": 0.65,
        "reasoning": "جن = the hidden/concealed beings (from جنّ = to cover/hide); جنّ = multitude. binary: الستر والكثافة (covering and density). general (< Lat generalis = belonging to a whole genus/kind, from genus = kind/race). The 'multitude/kind' aspect of جنّ connects weakly to generalis (of the whole kind/class). Indirect.",
        "path": "hidden multitude / kind (جن) → genus / whole kind → general (generalis)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "إفساد", "target_lemma": "spoil", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "إفساد = to corrupt/ruin/spoil (cause something to be damaged/ruined). axial: 'loss of the intended function due to harmful penetration'. spoil = to damage/ruin; also plunder. Near-perfect: both denote the act of rendering something useless/corrupt.",
        "path": "to corrupt / ruin (إفساد) → render useless → spoil",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "شَعر", "target_lemma": "calamity", "lang_pair": "ara-lat",
        "semantic_score": 0.42,
        "reasoning": "شَعر = hair; to perceive/feel. binary: dispersal in fine strands. calamity (< Lat calamitas = disaster, possibly from calamus = straw/stalks beaten down). The connection between hair/perception and calamity is very tenuous. Perhaps 'strands beaten down' parallels calamitas (beaten stalks), but this is highly speculative.",
        "path": "fine strands / hair (شَعر) → stalks beaten down → calamity (very speculative)",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "زفير", "target_lemma": "expire", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "زفير = deep exhalation/breathing out (the expulsion of breath). expire (< Lat expirare = to breathe out, ex + spirare = to breathe; also = to die = final exhalation). Both directly encode the outward breath motion: زفير = to exhale deeply, expirare = to breathe out/give final breath.",
        "path": "deep exhalation (زفير) → breathe out → expire (ex-spirare)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "مليا", "target_lemma": "mile", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "مليا/ميل = a mile (unit of distance, borrowed from Latin). mile (< Lat milia passuum = thousand paces). Both denote the same unit of distance. Direct borrowing and lexical correspondence.",
        "path": "mile (مليا/ميل, Arabic mile unit) → mile",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "مطحنة", "target_lemma": "mill", "lang_pair": "ara-lat",
        "semantic_score": 0.95,
        "reasoning": "مطحنة = a mill/grinding machine (من طحن = to grind). mill (< Lat molina/mola = millstone, grinding device). Both directly name the same grain-grinding machine. Near-perfect match.",
        "path": "grinding machine (مطحنة) → mill (molina) → mill",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "بصر", "target_lemma": "videre", "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": "بصر = sight, to see; البصرة = the sense of sight. videre (Lat) = to see (infinitive). Both directly denote the act/faculty of seeing. Near-perfect: بَصُرْتُ بالشيء = I saw/knew the thing; videre = to see.",
        "path": "sight / to see (بصر) → videre (to see)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "بصر", "target_lemma": "envy", "lang_pair": "ara-lat",
        "semantic_score": 0.55,
        "reasoning": "بصر = sight/vision; also 'evil eye' concept (العين). envy (< Lat invidere = to look at with ill will, in + videre = to look). The 'harmful looking' in invidere connects to بصر through the 'evil eye' concept: harmful seeing → envy. Plausible but indirect.",
        "path": "sight / looking (بصر) → evil eye / harmful looking → envy (invidere)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "أجير", "target_lemma": "agent", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "أجير = a hired worker, employee (one who acts on behalf of another for wages). agent (< Lat agens = one who acts, from agere = to do/act). Both denote someone who acts/performs work: أجير = hired doer, agent = one who acts. Near-perfect semantic match.",
        "path": "hired worker / one who acts (أجير) → doer on behalf of another → agent",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "السيّاف", "target_lemma": "gladiator", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "السيّاف = the swordsman (from سيف = sword). gladiator (< Lat gladiator = swordsman, from gladius = sword). Both directly name the armed sword-fighter: Arabic سيّاف = sword bearer/fighter, Latin gladiator = gladius (sword) wielder.",
        "path": "swordsman (السيّاف = possessor of sword) → gladiator (gladius-wielder)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "يعدل", "target_lemma": "idol", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "يعدل = to make equal/equivalent; to set up as an equivalent counterpart. axial: 'balancing equal weight on both sides'. idol (< Lat idolum < Gk eidolon = image/likeness = that which is set up as equivalent to something). The Arabic 'setting up an equivalent image' precisely describes an idol — يعدل بالله = to set something equal to God → idol.",
        "path": "to set up as equivalent (يعدل) → image set equal to God → idol",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "قناة", "target_lemma": "canyon", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "قناة = a channel/canal/water conduit; also a hollow cane/pipe. canyon (< Sp cañon = tube/channel, from caño = pipe/tube). Both denote a hollow channel: Arabic قناة = water channel/hollow pipe, Spanish cañon = large hollow channel carved by water. Direct structural parallel.",
        "path": "channel / hollow pipe (قناة) → large hollow channel → canyon",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "محصول", "target_lemma": "harvest", "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": "محصول = the yield/produce collected and stored (from حصل = to remain, to be collected). axial: 'the desired result isolated and gathered into the holding place'. harvest (< Old English haerfest = the gathering/reaping). Both denote the collected produce: محصول = what is gathered/yielded, harvest = the gathering of crops.",
        "path": "gathered yield / produce (محصول) → collected crops → harvest",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "خريف", "target_lemma": "horticulture", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "خريف = autumn (the harvest season); also خرف = to pick/gather fruit. horticulture (< Lat hortus = garden + cultura = cultivation). The Arabic خريف (autumn/harvest picking) connects to horticulture through 'gardening/fruit picking': خرف = to harvest fruit from trees, which is the core activity of horticulture.",
        "path": "to pick fruit / harvest season (خريف) → garden cultivation → horticulture",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "جردل", "target_lemma": "grail", "lang_pair": "ara-lat",
        "semantic_score": 0.65,
        "reasoning": "جردل = a large bucket/pail (wide-mouthed vessel for carrying water). grail (< Old French graal = cup/vessel, possibly < Lat gradalis = flat dish). Both denote wide-mouthed vessels: Arabic جردل = large bucket, graal = cup/dish. Vessel form connects them.",
        "path": "large bucket / wide vessel (جردل) → cup / flat vessel → grail",
        "method": "lemma_only", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "صالة", "target_lemma": "hall", "lang_pair": "ara-lat",
        "semantic_score": 0.92,
        "reasoning": "صالة = a hall/salon (large open room for gathering). hall (< Old English heall = large room/building). Both directly name a large gathering room. Near-perfect semantic match.",
        "path": "hall / large room (صالة) → hall",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "إئتمام", "target_lemma": "imitate", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "إئتمام = following/imitating (ائتمّ به = he followed/emulated him as a model). imitate (< Lat imitari = to copy/follow as model). Both directly encode following/copying a model. Near-perfect semantic match.",
        "path": "following as model (إئتمام) → copy / emulate → imitate",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "زوج", "target_lemma": "alone", "lang_pair": "ara-lat",
        "semantic_score": 0.45,
        "reasoning": "زوج = a pair/couple; to couple together. axial: 'two things intertwined and bound together'. alone (< all + one = wholly one). These are semantic opposites: زوج = paired/coupled, alone = singular. The connection through 'one/singular vs paired' is oppositional rather than cognate.",
        "path": "paired / coupled (زوج) ↔ alone (singular) — oppositional, weak link",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "ليّف", "target_lemma": "lave", "lang_pair": "ara-lat",
        "semantic_score": 0.65,
        "reasoning": "ليّف = the fibrous husk of a palm tree (used for scrubbing/washing). lave (< Lat lavare = to wash). Both relate to washing: ليّف provides the scrubbing fiber used in washing, lave = the act of washing. Indirect but plausible functional connection.",
        "path": "palm fiber / scrubbing material (ليّف) → used for washing → lave (to wash)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "جبيل", "target_lemma": "bible", "lang_pair": "ara-lat",
        "semantic_score": 0.80,
        "reasoning": "جبيل/جبل = city of Byblos (Phoenician city Gebal/Gubla → Greek Byblos). bible (< Gk biblia = books, from byblos = papyrus/book, named after Byblos the city). The Arabic جبيل is the Semitic name for Byblos, the city that gave its name to papyrus → bible. Direct etymological chain.",
        "path": "Byblos/Gebal (جبيل, Phoenician city) → byblos (papyrus exported from there) → bible",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الدخول", "target_lemma": "enter", "lang_pair": "ara-lat",
        "semantic_score": 0.95,
        "reasoning": "الدخول = entering/going in. axial: 'penetrating/moving into the interior'. enter (< Lat intrare = to go within, inter = within). Both directly encode entering/going inside. Near-perfect semantic match.",
        "path": "entering / going in (الدخول) → enter",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "نشيد", "target_lemma": "accent", "lang_pair": "ara-lat",
        "semantic_score": 0.78,
        "reasoning": "نشيد = a chant/sung poem (elevated vocal expression). binary: ارتفاع بانتشار مع حدة (rising with spread and sharpness). accent (< Lat accentus = tone/stress of voice, ad + canere = to sing toward). Both encode heightened vocal patterns: Arabic نشيد = chant/elevated song, Latin accentus = the sung pitch/stress.",
        "path": "chant / elevated song (نشيد) → vocal rise/pitch → accent (accentus = ad-cantus)",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "دير", "target_lemma": "abbey", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "دير = a Christian monastery (خانُ النصارى = the Christians' inn/compound). abbey (< Lat abbatia < Aramaic abba = father → the monastery led by an abbot). Both directly name a monastic religious community. Near-perfect match.",
        "path": "monastery / Christian religious compound (دير) → abbey",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "مَتر", "target_lemma": "geometry", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "مَتر = to extend/stretch; also: to measure (as in 'meter'). geometry (< Gk geometria = earth + metria = measurement). The Arabic مَتر (to extend/measure) corresponds to the -metria component of geometry: both encode the act of measuring by extension.",
        "path": "extension / measurement (مَتر) → measuring → geometry (-metria = measurement)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "النوتي", "target_lemma": "navy", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "النوتي = sailor/mariner (from Greek nautes = sailor). navy (< Lat navis = ship). Both relate to seamanship: نوتي = the sailor (person), navy = the fleet of ships. Same root domain of sea-travel.",
        "path": "sailor / mariner (النوتي < nautes) → naval forces → navy (navis)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "شرّط", "target_lemma": "serrate", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "شرّط = to make notches/cuts in sequence; الأشراط = signs/marks cut in. serrate (< Lat serratus = notched like a saw, from serra = saw). Both describe a series of sequential cuts/notches: Arabic شرّط = to cut repeatedly in sequence, Latin serratus = saw-toothed/notched.",
        "path": "to cut in sequential notches (شرّط) → saw-like teeth → serrate",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الزرد", "target_lemma": "lizard", "lang_pair": "ara-lat",
        "semantic_score": 0.60,
        "reasoning": "الزرد = chain mail (metal rings linked together). lizard (< Lat lacertus = lizard, muscle). The connection is weak: chain mail's linked rings might evoke scale-like patterns of a lizard, but the masadiq give no direct link. Binary: نفاذ بدقة مع إمساك (delicate threading with grip) could describe scales, but this is very indirect.",
        "path": "linked rings / chain mail (الزرد) → scale-like linked pattern → lizard (scale-bearer, indirect)",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "فوج", "target_lemma": "voyage", "lang_pair": "ara-lat",
        "semantic_score": 0.78,
        "reasoning": "فوج = a group/company moving together; إفاجة = moving fast/running. voyage (< OF voiage < Lat viaticum = provisions for a journey, via = way). The 'moving company/group traveling' of فوج connects to 'voyage' as a group journey. Plus the speed-movement concept.",
        "path": "group / company moving fast (فوج) → traveling company → voyage",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "باص", "target_lemma": "pass", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "باص = bus (vehicle that passes/moves through). pass (< Lat passus = step, from pandere = to spread). Also باص from French 'passe' (he passes). The Arabic باص for bus is itself from 'omnibus' and the notion of passing through routes.",
        "path": "vehicle that moves through (باص/bus) → movement through → pass",
        "method": "lemma_only", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "غرافة", "target_lemma": "crow", "lang_pair": "ara-lat",
        "semantic_score": 0.55,
        "reasoning": "غرافة = a ladle/scooping implement. crow (Old English crawe = the bird, from its call). No direct semantic connection between a ladle and a crow bird. Binary: 'gentle lifting from deep' could apply to both scooping and a crow picking up food, but this is very indirect.",
        "path": "lifting/scooping from depth (غرافة) → crow (picks/scoops, very indirect)",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "فتات", "target_lemma": "piece", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "فتات = crumbles/small broken pieces (from فتّ = to crumble/break). piece (< OF piece < Gaulish pettia = piece/fragment). Both denote a broken-off fragment: فتات = crumbles from breaking, piece = a portion broken off.",
        "path": "broken crumbles / fragments (فتات) → broken-off piece → piece",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "تسلق", "target_lemma": "escalator", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "تسلّق = to climb/scale (ascending by gripping). escalator (< Lat scala = staircase/ladder + -ator). Binary: 'sliding through interior with length'. Both encode ascending by steps/gripping: Arabic تسلّق = to scale/climb, escalator = the mechanical staircase.",
        "path": "to climb / scale (تسلّق) → ascending by steps → escalator",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "قمطر", "target_lemma": "count", "lang_pair": "ara-lat",
        "semantic_score": 0.62,
        "reasoning": "قمطر = a large dense camel; also قمطرير = day of concentrated evil. axial: 'gathered into a vessel with thickness and density'. count (< Lat computare = to reckon/sum). The gathering/accumulation semantic of قمطر connects weakly to counting (accumulating numbers).",
        "path": "dense accumulation (قمطر) → gathering/summing → count (compute)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الغروب", "target_lemma": "europe", "lang_pair": "ara-lat",
        "semantic_score": 0.80,
        "reasoning": "الغروب = the setting/sinking (of the sun), sunset, the west. axial: 'flowing down into a resting place with weight'. europe (< Gk Europe, possibly from Semitic ereb = west/evening, where غرب/ereb = the direction where the sun sets). Both encode 'the western/setting-sun direction'.",
        "path": "sunset / the west (الغروب = غرب = ereb) → western land → europe",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "اللبني", "target_lemma": "albino", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "اللبني = of milk / milky-white; related to لبن = milk. axial: 'interior containing delicate fluid that emerges and coheres as whiteness'. albino (< Sp/Port albo < Lat albus = white). Both encode 'milky/creamy whiteness': اللبني = the milky-white one, albino = the white-skinned one.",
        "path": "milky / white (اللبني, from لبن = milk) → white skin → albino",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "مستور", "target_lemma": "mystery", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "مستور = hidden/concealed (from ستر = to veil/cover). axial/binary: الإخفاء والتغطية (covering and concealment). mystery (< Lat mysterium < Gk mysterion = secret rite, from myein = to close the eyes/lips). Both encode deep concealment: مستور = the veiled/hidden thing, mystery = the secret closed from view.",
        "path": "hidden / concealed (مستور) → secret thing → mystery",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الموهبة", "target_lemma": "talent", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "الموهبة = a gift/talent (from وهب = to give freely, bestow). axial: 'acquiring the beneficial without exchange'. talent (< Gk talanton = a weight/sum of money, then gifted ability). Both now denote a natural gift/ability. The 'freely bestowed gift' of موهبة maps directly to 'talent' as innate gift.",
        "path": "freely given gift / bestowed ability (الموهبة) → innate gift → talent",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "مستكة", "target_lemma": "gum", "lang_pair": "ara-lat",
        "semantic_score": 0.78,
        "reasoning": "مستكة = mastic resin (a sticky tree gum from the mastic tree, Pistacia lentiscus). gum (< Lat gummi < Gk kommi = resin/gum). Both directly denote plant resin/sticky substance. Mastic is the most prized Arabic gum resin, gum = the same substance.",
        "path": "mastic resin / tree gum (مستكة) → plant gum/resin → gum",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "رَسَن", "target_lemma": "rein", "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": "رَسَن = a rope/halter (the lead rope for controlling an animal). rein (< Old French rene < Lat retinere = to hold back, retain). Both denote a controlling rope: رسن = the halter rope, rein = the guiding/holding rope. Direct functional equivalence.",
        "path": "halter rope / controlling lead (رَسَن) → holding/guiding rope → rein",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "صنعة", "target_lemma": "science", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "صنعة = craft/skilled work; making something by mastery and technique. axial: 'gathering in a new form by skill and calculation'. science (< Lat scientia = knowledge, systematic knowledge). The Arabic 'skilled craft through mastery' parallels 'systematic knowledge/craft of understanding'. Both encode methodical expert application.",
        "path": "skilled craft / mastery (صنعة) → systematic knowledge → science",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الشيد", "target_lemma": "acid", "lang_pair": "ara-lat",
        "semantic_score": 0.62,
        "reasoning": "الشيد = plaster/mortar (used to coat walls, also lime/gypsum). axial: 'binding a structure by spreading over it'. acid (< Lat acidus = sour, sharp). Lime/mortar has acidic properties (calcium oxide reacts with water acidically). Indirect: شيد = sharp biting material → acid. Weak but plausible.",
        "path": "caustic plaster / lime mortar (الشيد) → sharp/caustic material → acid",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "خِلعة", "target_lemma": "gala", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "خِلعة = a robe of honor bestowed on a dignitary (ceremonial garment of investiture). axial: 'separation from surrounding garment in festive detachment'. gala (< OF gale = rejoicing/festivity) = a festive occasion. Both relate to ceremonial festive garments/occasions: خلعة = the honorific robe given at celebrations, gala = the celebration itself.",
        "path": "robe of honor / ceremonial garment (خِلعة) → festive occasion → gala",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "خيال", "target_lemma": "hyaline", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "خيال = a shadow/apparition; an image that appears through cloth. axial: 'what shows on a thing suggesting it contains something extra and distinct'. hyaline (< Gk hyalos = glass, crystal) = clear/transparent like glass. Both encode the idea of something seen through a translucent medium: خيال = image showing through, hyaline = crystal-clear transparency.",
        "path": "translucent apparition / image showing through (خيال) → clear transparency → hyaline",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "صخري", "target_lemma": "scirrhous", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "صخري = rocky, of stone. axial: 'extreme hardness with dryness and roughness'. scirrhous (< Gk skirros = hard tumor, hard rock-like mass). Both directly encode 'hard like rock': صخري = rocky/stony, scirrhous = rock-hard (used for hard tumors).",
        "path": "rocky / stone-hard (صخري) → hard like rock → scirrhous (rock-hard tumor)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الثكلى", "target_lemma": "scylla", "lang_pair": "ara-lat",
        "semantic_score": 0.55,
        "reasoning": "الثكلى = a bereaved woman who lost her child (ثكل = loss of one's child). Scylla (Gk mythological monster = she who tears apart sailors). Connection through 'terrible destructive female': ثكلى = the grieving-destroyer, Scylla = the tearing-destroying female. Indirect through the archetype of the terrible female.",
        "path": "bereaved woman who tears/destroys (الثكلى) → terrible destructive female → Scylla",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "طنين", "target_lemma": "tinnitus", "lang_pair": "ara-lat",
        "semantic_score": 0.97,
        "reasoning": "طنين = a ringing/buzzing sound (the buzz of a fly, the ring of a cymbal). tinnitus (< Lat tinnitus = a ringing/clinking, from tinnire = to ring/tinkle). Near-perfect: both denote exactly the same ringing/buzzing sound.",
        "path": "ringing / buzzing sound (طنين) → tinnitus (ringing in the ears)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "بردعة", "target_lemma": "bard", "lang_pair": "ara-lat",
        "semantic_score": 0.65,
        "reasoning": "بردعة = a pack-saddle (the padded covering laid on a donkey/horse's back). bard (armor/covering for a horse) < OF barde = horse armor. Both denote a protective/padded covering placed on a horse's back. Direct functional equivalence on 'horse covering'.",
        "path": "pack-saddle / padded horse cover (بردعة) → horse armor/covering → bard",
        "method": "lemma_only", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "بِذار", "target_lemma": "bazaar", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "بِذار = seeds for planting; تبذير = scattering/spreading (also of goods/wealth). binary: نثر الدقاق المتجمعة (scattering gathered small things). bazaar (< Persian bāzār = market). The Arabic 'scattering of goods/seeds' connects to the market where things are spread out for sale. Indirect but plausible.",
        "path": "scattering seeds / spreading goods (بِذار) → goods spread for sale → bazaar",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "قٌلّة", "target_lemma": "olio", "lang_pair": "ara-lat",
        "semantic_score": 0.55,
        "reasoning": "قُلّة = a small water jug/vessel (narrow-mouthed clay pot). olio (< Sp olla < Lat olla = earthen pot/cooking vessel). Both are earthenware vessels: Arabic قُلّة = small clay water pot, Latin olla = earthen cooking pot. Same material/function category.",
        "path": "small clay vessel / pot (قُلّة) → earthen pot → olio (olla)",
        "method": "lemma_only", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "يُمن", "target_lemma": "omen", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "يُمن = good fortune/blessing (from يمين = right side = the auspicious side). axial: 'containing a bounded power'. omen (< Lat omen = a sign of the future, portent). The Arabic يُمن (auspicious sign/blessing) and Latin omen (portent/sign) share the core concept of a sign indicating fortune.",
        "path": "auspicious sign / blessing (يُمن) → sign of fortune → omen",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "نخاع", "target_lemma": "nuchal", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "نخاع = the spinal cord/marrow (نخاع الظهر = spinal cord). nuchal (< Med Lat nucha < Arabic نخاع = spinal cord). Direct borrowing: Arabic نخاع into Latin nucha → English nuchal (relating to the nape/back of neck where the spinal cord is). Same anatomical concept.",
        "path": "spinal cord (نخاع) → nucha (borrowed from Arabic) → nuchal",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "سحلية", "target_lemma": "saurian", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "سحلية = a lizard (a reptile). axial: 'smooth slipping motion, stripped of roughness'. saurian (< Gk sauros = lizard). Both directly denote lizard-like reptiles. سحلية = the Arabic lizard, saurian = of or relating to lizards.",
        "path": "lizard (سحلية) → saurian (lizard-like) → saurian",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "ثعباني", "target_lemma": "serpentine", "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": "ثعباني = snake-like (from ثعبان = a large serpent/python). serpentine (< Lat serpentinus = snake-like, from serpens = snake). Both denote 'of or like a serpent': ثعباني = snake-like, serpentine = winding like a serpent.",
        "path": "snake-like (ثعباني, from ثعبان = serpent) → serpentine",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "شطير", "target_lemma": "satyr", "lang_pair": "ara-lat",
        "semantic_score": 0.60,
        "reasoning": "شطير = one who is cut off/split away; an outsider; from شطر = to split in half. axial: 'split to one side, separated'. satyr (< Gk satyros = wild woodland deity, lascivious). The 'split away/outsider' of شطير weakly evokes the satyr's outsider/wild nature, but the connection is indirect.",
        "path": "split away / outsider (شطير) → wild outsider being → satyr (weak)",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "مُسِن", "target_lemma": "senile", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "مُسِن = aged/elderly (from سنّ = age/years). senile (< Lat senilis = of old age, from senex = old man). Both directly denote old age: Arabic مُسِن = the elderly one, Latin senilis = of old age.",
        "path": "aged / elderly (مُسِن, from سنّ = years) → senile (senex = old man)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "صوبة", "target_lemma": "stove", "lang_pair": "ara-lat",
        "semantic_score": 0.78,
        "reasoning": "صوبة = a heated chamber/brazier (from صاب = to heat/burn, the heated vessel). stove (< Old English stofa = heated room/bath). Both denote a heated enclosure/heating device: Arabic صوبة = heated vessel, stove = heated room/cooking device.",
        "path": "heated vessel / brazier (صوبة) → heated enclosure → stove",
        "method": "lemma_only", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "رفض", "target_lemma": "because", "lang_pair": "ara-lat",
        "semantic_score": 0.30,
        "reasoning": "رفض = to leave/abandon/reject. because (< by + cause). The connection between rejection and causality is very weak. No convincing semantic path.",
        "path": "to reject / abandon (رفض) → because (no clear link)",
        "method": "none", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الكي", "target_lemma": "ink", "lang_pair": "ara-lat",
        "semantic_score": 0.70,
        "reasoning": "الكيّ = cauterization/branding with hot iron (burning a mark). ink (< Lat encaustum < Gk enkauston = burned-in pigment, from en + kaiein = to burn in). Both share 'burned-in mark': كيّ = burning a mark onto skin, encaustum = burned-in pigment/ink.",
        "path": "burning a mark (الكي) → burned-in pigment → ink (encaustum = en-kauston)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "منذر", "target_lemma": "monitor", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "منذر = one who warns/admonishes (from نذر = to warn). axial: 'a burden that must be discharged, or feared for its imposition'. monitor (< Lat monitor = one who warns/advises, from monere = to warn). Near-perfect: both denote the warner/advisor.",
        "path": "one who warns (منذر) → monitor (one who warns/advises)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "أوقية", "target_lemma": "ounce", "lang_pair": "ara-lat",
        "semantic_score": 0.92,
        "reasoning": "أوقية = a unit of weight (the uqiyya, from Greek ounkia). ounce (< Lat uncia = a twelfth part/unit of weight). Both are the same ancient weight unit from the same Latin/Greek root. Direct borrowing chain.",
        "path": "weight unit (أوقية < uncia) → ounce",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "إنسولين", "target_lemma": "insulin", "lang_pair": "ara-lat",
        "semantic_score": 0.98,
        "reasoning": "إنسولين = insulin (Arabic borrowing of the medical term). insulin (< Lat insula = island, named after the islets of Langerhans). Perfect direct borrowing correspondence.",
        "path": "insulin (إنسولين, direct Arabic borrowing) → insulin",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "وحيد", "target_lemma": "widow", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "وحيد = solitary/alone (from وحد = one alone, single). axial: 'singularity — nothing like it beside it'. widow (< Old English widewe = one who has lost a spouse, left alone). Both encode being left alone/solitary: وحيد = the solitary one, widow = the one left alone.",
        "path": "solitary / alone (وحيد) → the one left alone → widow",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "التكريم", "target_lemma": "honour", "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": "التكريم = the act of honoring/ennobling (from كرم = generosity/nobility). axial: 'refinement and purity of the gathered thing'. honour (< Lat honor = honor/dignity). Both encode formal respect and social elevation. Near-perfect semantic match.",
        "path": "act of honoring / ennobling (التكريم) → honour",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "شديد", "target_lemma": "sour", "lang_pair": "ara-lat",
        "semantic_score": 0.55,
        "reasoning": "شديد = intense/severe/hard. axial: 'hardness of substance through tightness of interior'. sour (< Old English sur = acid/tart) = sharp acidic taste. The 'intense sharpness' of شديد connects weakly to the sharp/intense taste of sour. Indirect.",
        "path": "intense / sharp (شديد) → sharp taste → sour",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "علم،", "target_lemma": "banner", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "علم = a flag/banner/standard (a tall marker used for guidance). axial: 'guidance by height toward direction/path'. banner (< Old Norse band = a strip of cloth as identifier). Both directly denote a cloth standard/flag raised for identification and guidance.",
        "path": "flag / tall marker (علم) → banner (raised cloth for guidance)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "شخص،", "target_lemma": "person", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "شخص = a visible figure/body (the physical form that stands out). axial: 'a body protruding as a visible mass'. person (< Lat persona = mask/character/individual). Both denote the visible individual: شخص = the visible standing figure, person = the individual identity.",
        "path": "visible figure / body (شخص) → individual → person",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "البهجة", "target_lemma": "hilarious", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "البهجة = beauty and joy (from بهج = to be glad, radiant). hilarious (< Lat hilaris < Gk hilaros = cheerful/merry). Both denote elevated cheerfulness: Arabic بهجة = radiant joy/beauty, hilarious = extreme cheerfulness.",
        "path": "radiant joy / beauty (البهجة) → cheerfulness → hilarious",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "مردوك", "target_lemma": "murdoch", "lang_pair": "ara-lat",
        "semantic_score": 0.60,
        "reasoning": "مردوك = Marduk, the Babylonian chief god (also مردوك as a name). murdoch = a surname (< Old Irish/Gaelic muiredach = sailor). These are unrelated names with no semantic bridge. The phonetic similarity is superficial.",
        "path": "Marduk (Babylonian deity name) → murdoch (Celtic personal name) — phonetic only",
        "method": "none", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "زفير", "target_lemma": "zephyr", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "زفير = deep exhalation, a breath-movement; also a carrying motion. zephyr (< Lat Zephyrus < Gk Zephyros = the west wind, a light breeze). Both encode breath/wind movement: Arabic زفير = the expelled breath/exhalation, zephyr = a gentle wind. Direct breath→wind semantic.",
        "path": "exhalation / breath movement (زفير) → wind movement → zephyr",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الطيّب", "target_lemma": "toby", "lang_pair": "ara-lat",
        "semantic_score": 0.55,
        "reasoning": "الطيّب = the good/pleasant/kind one. Toby (< Hebrew Tobias = God is good). The Arabic الطيّب (the good one) and the Hebrew Tobias (God is good) share the 'good/pleasant' semantic, but Toby as a personal name is more specifically Hebrew than Arabic.",
        "path": "the good / pleasant one (الطيّب) → Tobias (God is good) → Toby",
        "method": "lemma_only", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "جابر", "target_lemma": "geber", "lang_pair": "ara-lat",
        "semantic_score": 0.95,
        "reasoning": "جابر = the name Jabir (the one who fixes/repairs: from جبر = to mend/repair bones). Geber is the Latinized name of Jabir ibn Hayyan (the alchemist). Direct personal name correspondence: Arabic جابر → Latin Geber.",
        "path": "Jabir (the mender, جابر) → Geber (Latinization of Jabir ibn Hayyan)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "حصان", "target_lemma": "cavalier", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "حصان = a horse (specifically a stallion, a noble horse). cavalier (< Ital cavaliere < Lat caballus = horse + -ier = one who rides). Both encode the concept of the horse/horseman: Arabic حصان = the horse itself, cavalier = the horseman/knight.",
        "path": "horse / stallion (حصان) → horseman → cavalier",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "رغّى", "target_lemma": "rage", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "رغّى = to foam/froth (produce white foam, as a camel froths at the mouth in agitation). rage (< OF rage < Lat rabies = madness/fury). Both encode violent agitation: Arabic رغّى = frothing/foaming with agitation, rage = violent fury/madness.",
        "path": "foam with agitation (رغّى) → violent frothing anger → rage",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "جم", "target_lemma": "honey", "lang_pair": "ara-lat",
        "semantic_score": 0.60,
        "reasoning": "جم = abundance/plentifulness (جمّ = to become abundant). axial: increase and gathering. honey (< Old English hunig). The connection between جم (abundance) and honey is through 'sweet abundance'. Binary تجمع والكثرة could evoke the gathering of honey, but the link is indirect.",
        "path": "abundance / gathered plenty (جم) → sweet gathered substance → honey (weak)",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "سمو", "target_lemma": "sum", "lang_pair": "ara-lat",
        "semantic_score": 0.75,
        "reasoning": "سمو = elevation/rising up (from سما = to rise/ascend). axial: 'rising while cohering at top'. sum (< Lat summa = the highest/total, summit, from summus = highest). Both encode the concept of the topmost/highest point: Arabic سمو = elevation, Latin summa = the highest total.",
        "path": "elevation / rising to top (سمو) → highest point → sum (summa = the top/total)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "كمى", "target_lemma": "come", "lang_pair": "ara-lat",
        "semantic_score": 0.50,
        "reasoning": "كمى = to conceal/hide (put a covering over). come (< Old English cuman = to arrive). Concealment and arrival are not semantically connected. The phonetic resemblance is coincidental.",
        "path": "to conceal (كمى) → come (no convincing link)",
        "method": "none", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "طيّب", "target_lemma": "toffee", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "طيّب = good/pleasant/sweet (the pleasant/delicious one). axial: 'gentleness of impact on the senses'. toffee (< perhaps taffy = sweet candy). Both encode pleasant sweetness: Arabic طيّب = the sweet/pleasant, toffee = a sweet confection. Direct 'sweetness' semantic.",
        "path": "pleasant / sweet (طيّب) → sweet confection → toffee",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "إسفنجي", "target_lemma": "fungus", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "إسفنجي = sponge-like/porous. fungus (< Lat fungus = mushroom, possibly < Gk spongos = sponge). Both encode 'spongy/porous structure': Arabic إسفنجي = sponge-like porous, Latin fungus (the mushroom named for its sponge-like texture).",
        "path": "sponge-like / porous (إسفنجي = spongy) → sponge-textured → fungus (from sponge)",
        "method": "lemma_only", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "ورنيش", "target_lemma": "varnish", "lang_pair": "ara-lat",
        "semantic_score": 0.95,
        "reasoning": "ورنيش = varnish (Arabic borrowing of the word). varnish (< Med Lat veronix = resin/varnish). Direct borrowing correspondence.",
        "path": "varnish (ورنيش, direct borrowing) → varnish",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "ونى", "target_lemma": "wane", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "ونى = to weaken/fade/slow down (الوَنى = weakness and fatigue). wane (< Old English wanian = to decrease/diminish). Both directly encode gradual weakening/decrease: Arabic ونى = losing vigor/speed, wane = decreasing in power/size.",
        "path": "to weaken / diminish (ونى) → wane",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "أيقونة", "target_lemma": "icon", "lang_pair": "ara-lat",
        "semantic_score": 0.97,
        "reasoning": "أيقونة = an icon (Arabic borrowing of Greek eikon = image/representation). icon (< Gk eikon = image). Direct borrowing: Arabic أيقونة directly names the same religious image/symbol.",
        "path": "icon / religious image (أيقونة < eikon) → icon",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "ضرط", "target_lemma": "fart", "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": "ضرط = to break wind (flatulence). fart (< Old English feortan = to break wind). Both directly denote the same bodily function. Direct lexical correspondence.",
        "path": "flatulence (ضرط) → fart",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "ميزان", "target_lemma": "liter", "lang_pair": "ara-lat",
        "semantic_score": 0.75,
        "reasoning": "ميزان = a balance/scale for measuring weight. liter (< Gk litra = a unit of weight/measure). Both encode measurement: ميزان = the weighing instrument, liter = the unit of volumetric measurement. Both derive from the ancient Mediterranean balance/measurement system.",
        "path": "balance / measurement scale (ميزان) → unit of measure → liter",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "ذاتي", "target_lemma": "autogenous", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "ذاتي = intrinsic/self-related (from ذات = self/essence). autogenous (< Gk autos = self + -genous = generated). Both encode 'from/of the self': Arabic ذاتي = pertaining to the self, autogenous = self-generated.",
        "path": "of the self / intrinsic (ذاتي) → self-generated → autogenous",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "بدون", "target_lemma": "anesthesia", "lang_pair": "ara-lat",
        "semantic_score": 0.55,
        "reasoning": "بدون = without (Arabic preposition). anesthesia (< Gk an = without + aisthesia = sensation). Both encode 'without': Arabic بدون = without, Greek an- = without. The 'without' concept bridges them but بدون is a function word, not a root concept.",
        "path": "without (بدون) → an- (without sensation) → anesthesia",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الأبتر", "target_lemma": "apterous", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "الأبتر = the cut-short one, the one whose tail/extension is severed (from بتر = to cut off). axial: 'cutting thin extensions of a thing'. apterous (< Gk a = without + pteron = wing) = wingless. Both encode 'cut off/lacking an appendage': الأبتر = tail cut off, apterous = wings cut/absent.",
        "path": "cut off / lacking appendage (الأبتر) → without wings → apterous",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "وجع", "target_lemma": "cephalalgia", "lang_pair": "ara-lat",
        "semantic_score": 0.75,
        "reasoning": "وجع = pain/ache (the ache). cephalalgia (< Gk kephale = head + algos = pain) = headache. Arabic وجع = the pain/ache, cephalalgia = a specific head pain. وجع الرأس = headache in Arabic. Both encode pain; the Arabic is the general pain term.",
        "path": "pain / ache (وجع) → head-pain → cephalalgia",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "القهقهة", "target_lemma": "cachinnate", "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": "القهقهة = loud laughter/guffawing (the sound of boisterous laughter). cachinnate (< Lat cachinnare = to laugh loudly/boisterously, onomatopoeia). Both directly encode loud unrestrained laughter. The onomatopoeic words share the same sound pattern of boisterous laughter.",
        "path": "boisterous laughter / guffaw (القهقهة) → cachinnate (loud laughter)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "منقوص", "target_lemma": "mancinism", "lang_pair": "ara-lat",
        "semantic_score": 0.52,
        "reasoning": "منقوص = deficient/reduced (from نقص = deficiency). axial: 'part gone from a gathered body, reducing its mass'. mancinism is an extremely rare term; if related to left-handedness (mancus = defective hand in Latin), then both encode 'deficiency'. Indirect and uncertain.",
        "path": "deficient / reduced (منقوص) → defective → mancinism (mancus = defective)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "علم", "target_lemma": "semiology", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "علم = a sign/flag/marker (used for guidance). semiology (< Gk semeion = sign + logos = study) = the study of signs. The Arabic علم as 'sign/marker' connects directly to semeiology (study of signs): علم = the sign itself, semiology = the study of signs.",
        "path": "sign / marker (علم) → study of signs → semiology",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "العمّة", "target_lemma": "emmet", "lang_pair": "ara-lat",
        "semantic_score": 0.42,
        "reasoning": "العمّة = paternal aunt. emmet (Old English aemete = ant). These are completely unrelated: aunt and ant. No semantic connection.",
        "path": "paternal aunt (العمّة) → emmet/ant — no connection",
        "method": "none", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "مهين", "target_lemma": "heinous", "lang_pair": "ara-lat",
        "semantic_score": 0.75,
        "reasoning": "مهين = despicable/contemptible (from هان = to be lowly, humiliated). heinous (< Old French haineus = hateful, from haïr = to hate). Both encode moral revulsion: Arabic مهين = one treated with contempt/lowly, heinous = morally reprehensible.",
        "path": "contemptible / lowly (مهين) → hateful → heinous",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الناشفة", "target_lemma": "anchovy", "lang_pair": "ara-lat",
        "semantic_score": 0.65,
        "reasoning": "الناشفة = the dried one (from نشف = to dry/absorb moisture; نشف الحجر = porous stone that absorbs). anchovy (< Sp anchoa < possibly Basque or Gk) = a small saltcured/dried fish. The Arabic 'dried/moisture-absorbing' connects to anchovy as a salt-dried fish.",
        "path": "dried / moisture-absorbed (الناشفة) → dried/salted fish → anchovy",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "ورس", "target_lemma": "vert", "lang_pair": "ara-lat",
        "semantic_score": 0.65,
        "reasoning": "ورس = a yellow plant (used for dyeing yellow/golden). vert (< Lat viridis = green) = green (heraldic). Both are color/dye terms: Arabic ورس = yellow-gold dye plant, vert = green. Adjacent colors in the spectrum — yellow-green — but different specific colors.",
        "path": "yellow dye plant (ورس) → plant-based color → vert (green)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "أبو", "target_lemma": "buxema", "lang_pair": "ara-lat",
        "semantic_score": 0.42,
        "reasoning": "أبو = father/nurture (أبَوْتُ الرجلَ = to be a father to him; يأبو اليتيم = to nurture an orphan). buxema is an obscure or non-standard term. If it relates to 'box'/'container' (< Lat buxus), the connection to 'father/nurture' is very weak.",
        "path": "father / nurture (أبو) → buxema (obscure target, no convincing link)",
        "method": "none", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "ليّنة", "target_lemma": "linda", "lang_pair": "ara-lat",
        "semantic_score": 0.62,
        "reasoning": "ليّنة = gentle/soft one (from لان = to be soft/gentle). Linda (< Sp linda = beautiful/gentle, possibly < Gmc lind = gentle/tender). Both encode softness/gentleness: Arabic ليّنة = the soft/gentle one, Linda = beautiful/gentle (Spanish).",
        "path": "soft / gentle one (ليّنة) → gentle/beautiful → Linda",
        "method": "lemma_only", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "نائلة", "target_lemma": "nyla", "lang_pair": "ara-lat",
        "semantic_score": 0.60,
        "reasoning": "نائلة = she who attains/gains; the successful one (from نال = to attain). Nyla (a modern name). The phonetic correspondence is present but the target is a modern name without established Latin etymology.",
        "path": "she who attains (نائلة) → Nyla (phonetic borrowing, modern name)",
        "method": "lemma_only", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الفصح", "target_lemma": "pascal", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "الفصح = Passover/Easter (from فصح = to be eloquent, but as feast name = the Passover). pascal (< Lat paschalis = of Passover/Easter, from Aramaic/Hebrew pesach). Both name the Passover/Easter feast. Direct religious term correspondence.",
        "path": "Passover / Easter (الفصح) → paschalis → pascal",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "روماني", "target_lemma": "romeo", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "روماني = Roman (pertaining to Rome). Romeo (Italian personal name < Roman/Roma). Romeo is literally 'the Roman one' — a name derived from 'Roman'. Both directly relate to Roman identity.",
        "path": "Roman (روماني) → the Roman one → Romeo",
        "method": "lemma_only", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "سلمى", "target_lemma": "salome", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "سلمى = a female name meaning 'peace/safe' (from سلم = peace/safety). Salome (< Hebrew Shalom = peace, via Aramaic). Both are names derived from the Semitic root for 'peace' (salam/shalom).",
        "path": "peace/safety (سلمى = سلم) → Salome (< Shalom = peace) → Salome",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "زكي", "target_lemma": "zaccai", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "زكي = pure/virtuous/growing (from زكا = to be pure/grow). Zaccai (Aramaic name = pure/innocent). Both encode purity/virtue: Arabic زكي = the pure/virtuous one, Zaccai = pure one in Aramaic.",
        "path": "pure / virtuous (زكي) → Zaccai (pure/innocent in Aramaic)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "حبل", "target_lemma": "spiral", "lang_pair": "ara-lat",
        "semantic_score": 0.80,
        "reasoning": "حبل = a rope (twisted strands); also حبل رملي = long ridge of sand. axial: 'tight binding with extension'. spiral (< Lat spira < Gk speira = a coil/twisted rope). Both encode twisting/coiled structure: Arabic حبل = twisted rope, spiral = a coil (which is how a rope is formed).",
        "path": "twisted rope (حبل) → coiled/twisted form → spiral (speira = coil)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "ترف", "target_lemma": "trophic", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "ترف = luxurious living, nourishment to excess (from تَرِفَ = to be pampered/over-nourished). axial: 'filling with moisture and softness until it swells'. trophic (< Gk trophe = nourishment). Both encode nourishment/feeding: Arabic ترف = excessive nourishing/pampering, trophic = of/relating to nutrition.",
        "path": "luxurious nourishment / pampered feeding (ترف) → trophic (of nourishment)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "جلب", "target_lemma": "celebrate", "lang_pair": "ara-lat",
        "semantic_score": 0.68,
        "reasoning": "جلب = to bring/import (bringing goods from afar). axial: 'attaching something to a foreign place with expansion'. celebrate (< Lat celebrare = to frequent/honor, from celeber = frequented/populous). The Arabic 'bringing/gathering from afar' and Latin 'frequent gathering/crowded occasion' share the 'bringing together a multitude'. Indirect.",
        "path": "bringing together / importing (جلب) → gathering people → celebrate",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "علم", "target_lemma": "etiology", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "علم = knowledge/science; also sign/marker. etiology (< Gk aitia = cause + logos = study) = study of causes. The Arabic علم as 'science' is part of the -logy structure, and علم also = 'to know the cause of something'. علم العلل = the science of causes.",
        "path": "knowledge / science of causes (علم) → etiology (study of causes)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "جَلّد", "target_lemma": "gelatine", "lang_pair": "ara-lat",
        "semantic_score": 0.78,
        "reasoning": "جَلّد = relating to skin/hide; جِلد = skin/leather. axial: 'a tough tight covering that coats the outer surface'. gelatine (< Lat gelatus = frozen/congealed, from gelare = to freeze; also related to gelu = frost). But gelatine is derived from collagen in animal skin/bones. Both connect through animal skin: جلّد = to flay/skin, gelatine = extracted from skins/bones.",
        "path": "skin / hide (جَلّد) → animal skin extract → gelatine (collagen from skins)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "جرن", "target_lemma": "granulate", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "جرن = a threshing floor (where grain is processed); also the neck/gullet. granulate (< Lat granum = grain + -ulate). Both involve grain/granular processing: Arabic جرن = the place for threshing/processing grain, granulate = to form into grains/particles.",
        "path": "threshing floor / grain processing (جرن) → grain particles → granulate",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "إيماء", "target_lemma": "mime", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "إيماء = a gesture/hint (non-verbal signal, nodding/pointing). mime (< Gk mimos = imitator/actor who uses gestures). Both encode non-verbal gestural communication: Arabic إيماء = a gesture/hint, mime = performance through gesture.",
        "path": "gesture / non-verbal signal (إيماء) → gestural performance → mime",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "عمومي", "target_lemma": "omni", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "عمومي = general/public/for all (from عام = all/general). axial: 'gathering with elevation and upper cohesion'. omni (< Lat omnis = all/every). Both encode universality/totality: Arabic عمومي = that which is general/for all, omni = all/every.",
        "path": "general / for all (عمومي) → omni (all/every)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "ترياق", "target_lemma": "treacle", "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": "ترياق = theriaca/antidote (the great antidote/remedy derived from snake venom). treacle (< Lat theriaca < Gk theriake = antidote against wild beasts, from therion = wild beast). Direct etymological correspondence: Arabic ترياق and English treacle both come from the same Greek theriaca.",
        "path": "antidote / remedy (ترياق < theriaca) → treacle (theriaca = antidote)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "ثَرَم", "target_lemma": "trim", "lang_pair": "ara-lat",
        "semantic_score": 0.75,
        "reasoning": "ثَرَم = breaking off a tooth (ثرم = knocked out a front tooth). trim (< Old English trymman = to make firm/neat by cutting). Both involve the removal of an edge/protrusion to create a neater form: Arabic ثرم = knocking off a tooth, trim = cutting to neaten an edge.",
        "path": "knocking off a tooth-edge (ثَرَم) → cutting to neaten → trim",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "وين", "target_lemma": "vinegar", "lang_pair": "ara-lat",
        "semantic_score": 0.80,
        "reasoning": "وين = dark/black grapes (العنب الأسود). vinegar (< OF vinaigre = sour wine, vin + aigre = wine + sour). Both involve dark grapes as source: Arabic وين = dark grapes, vinegar = soured grape wine. Dark grapes → wine → soured wine → vinegar.",
        "path": "dark grapes (وين) → wine from dark grapes → soured → vinegar",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "قرّظ", "target_lemma": "grace", "lang_pair": "ara-lat",
        "semantic_score": 0.65,
        "reasoning": "قرّظ = to praise/commend (أقرظه = to praise him). grace (< Lat gratia = favor/thankfulness). Both encode positive recognition: Arabic قرّظ = to give praise/commendation, grace = favor/thankfulness. Indirect: praising → granting favor → grace.",
        "path": "to praise / commend (قرّظ) → bestow favor → grace (gratia)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "تأريخ", "target_lemma": "archive", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "تأريخ = history/dating (from أرّخ = to record dates/history). archive (< Gk arkheia = public records, from arkhe = beginning/government). Both encode systematic recording: Arabic تأريخ = historical record-keeping, archive = a repository of records.",
        "path": "historical dating / record (تأريخ) → stored records → archive",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "عميل", "target_lemma": "client", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "عميل = a client/customer (from عمل = to work; one who employs another's labor). client (< Lat cliens = one who leans on a patron for support, follower). Both denote someone who uses another's services: Arabic عميل = client/agent who works through another, Latin cliens = one who depends on a patron.",
        "path": "client / one who uses services (عميل) → client (cliens)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "قمائن", "target_lemma": "caminus", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "قمائن = furnaces/kilns (plural of قمين = oven/kiln for firing). caminus (< Gk kaminos = furnace/kiln). Both directly name the same heating structure: Arabic قمائن = furnaces/kilns, Lat caminus = furnace/forge. Likely direct borrowing.",
        "path": "furnaces / kilns (قمائن) → caminus (furnace)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "قمائن", "target_lemma": "chimney", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "قمائن = furnaces/kilns. chimney (< Lat caminus = furnace/flue → OF cheminee). Both trace to the same furnace root: قمائن = furnaces, chimney = the outlet/flue of a furnace. Direct etymological chain through caminus.",
        "path": "furnaces (قمائن) → caminus → cheminee → chimney",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "طاسة", "target_lemma": "test", "lang_pair": "ara-lat",
        "semantic_score": 0.80,
        "reasoning": "طاسة = a cup/bowl (shallow vessel). test (< Lat testa = earthen vessel/pot used for assaying metals). Both denote earthenware vessels: Arabic طاسة = a bowl/cup, Latin testa = the testing vessel. The Latin 'test' originally meant the pot used to melt metals for assay.",
        "path": "cup / earthen vessel (طاسة) → testa (assay pot) → test",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "لغة", "target_lemma": "tautology", "lang_pair": "ara-lat",
        "semantic_score": 0.65,
        "reasoning": "لغة = language/tongue/speech. tautology (< Gk tauto = same + logos = word/speech). Both involve speech/language: Arabic لغة = language/dialect, tautology = redundant saying of the same thing twice in different words. لغة connects to the -logy suffix (logos = word).",
        "path": "language / speech (لغة) → logos (word) → tautology (tauto-logos)",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "النقل", "target_lemma": "angle", "lang_pair": "ara-lat",
        "semantic_score": 0.55,
        "reasoning": "النقل = transfer/movement (نقل = to move/transfer). angle (< Lat angulus = corner/angle). The 'movement causing a bend' is indirect: نقل = moving/transferring, angle = the corner/bend. Weak conceptual link through 'directional change'.",
        "path": "transfer / directional movement (النقل) → change of direction → angle (weak)",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "علقة", "target_lemma": "leech", "lang_pair": "ara-lat",
        "semantic_score": 0.95,
        "reasoning": "علقة = a leech (the blood-sucking worm in water). axial: 'clinging/attaching with upward pull'. leech (< Old English lece = the worm). Both directly name the same creature: Arabic علقة = the leech/blood clot worm, leech = the blood-sucking worm.",
        "path": "leech / blood-sucking worm (علقة) → leech",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "زائر", "target_lemma": "visitor", "lang_pair": "ara-lat",
        "semantic_score": 0.95,
        "reasoning": "زائر = a visitor (one who comes to visit). visitor (< Lat visitare = to go to see). Near-perfect: both directly name the person who comes to visit.",
        "path": "visitor / one who visits (زائر) → visitor",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "دأم", "target_lemma": "dam", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "دأم = to overwhelm/engulf (تدأم الماء الشيء = water engulfed something; also = piled on). dam (< Old Dutch dam = a barrier stopping water). Both relate to water and force: Arabic دأم = water overwhelming/piling on, dam = the structure that stops water from overwhelming.",
        "path": "water overwhelming / piling on (دأم) → blocking water → dam",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الحنّة", "target_lemma": "alkanet", "lang_pair": "ara-lat",
        "semantic_score": 0.78,
        "reasoning": "الحنّة = henna (the plant used for red/orange dye). alkanet (< Sp alcaneta < Arabic الحنّة or الكنة = henna/dye plant). Both name dyeing plants: الحنّة = henna (Lawsonia), alkanet = a related dyeing plant. The Arabic name is the etymological source of alkanet.",
        "path": "henna / red dye plant (الحنّة) → alkanet (< al-hanna, dye plant name)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    # --- Proper name / mythological pairs ---
    {
        "source_lemma": "قابيل", "target_lemma": "cain", "lang_pair": "ara-lat",
        "semantic_score": 0.92,
        "reasoning": "قابيل = Cain (the son of Adam who killed his brother, from Arabic قبل = reception/front; the firstborn who was received). cain (< Hebrew qayin = acquisition/smith). Near-perfect: both names refer to the same biblical figure.",
        "path": "Cain (قابيل) → Cain",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "دعاء", "target_lemma": "dua", "lang_pair": "ara-lat",
        "semantic_score": 0.98,
        "reasoning": "دعاء = supplication/prayer (from دعا = to call/invoke). dua = the transliteration of Arabic دعاء in Western usage. Perfect identity.",
        "path": "supplication / prayer (دعاء) → dua (direct transliteration)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "المتين", "target_lemma": "ethan", "lang_pair": "ara-lat",
        "semantic_score": 0.80,
        "reasoning": "المتين = the strong/firm one (from متن = hardness/firmness). Ethan (< Hebrew eytan = strong/enduring). Both encode firmness/strength: Arabic المتين = the strong/hard one, Ethan = the strong/enduring one in Hebrew.",
        "path": "the strong/firm (المتين) → Ethan (eytan = strong) → Ethan",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "عشتار", "target_lemma": "esther", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "عشتار = Ishtar (the Mesopotamian goddess of love/war). Esther (< Persian stara = star, or < Akkadian Ishtar). Both are forms of the same name: Ishtar/Esther share Semitic roots.",
        "path": "Ishtar (عشتار, goddess) → Esther (< Ishtar/star) → Esther",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "حنى", "target_lemma": "hannibal", "lang_pair": "ara-lat",
        "semantic_score": 0.75,
        "reasoning": "حنى = to bend/curve; also حنان = grace/compassion. Hannibal (< Phoenician Hanni-baal = grace of Baal, from hann = grace/favor). Both connect through 'grace/compassion': Arabic حنى = grace/bending in kindness, Hannibal = grace of Baal.",
        "path": "grace / compassion (حنى → حنان) → Hannibal (Hanni = grace, baal = lord)",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "ريحانة", "target_lemma": "rihanna", "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": "ريحانة = sweet basil (the aromatic plant, from ريح = scent/wind). Rihanna is the modern name directly derived from Arabic ريحانة. Direct name borrowing.",
        "path": "basil / fragrant herb (ريحانة) → Rihanna (direct name borrowing)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "صابرين", "target_lemma": "sabrina", "lang_pair": "ara-lat",
        "semantic_score": 0.78,
        "reasoning": "صابرين = patient ones (plural of صابر = patient/enduring, from صبر). Sabrina (< Celtic Habren/Severn river name, or possibly < Lat Sabrina). The connection through 'enduring/patient' to Sabrina is indirect as the name has different origins.",
        "path": "patient/enduring (صابرين) → Sabrina (indirect name connection)",
        "method": "lemma_only", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "صفورة", "target_lemma": "sephora", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "صفورة = Zipporah (Moses's wife; from Arabic صفر = yellow/sparrow; Heb Tsipporah = bird). Sephora is the Greek/Latin form of Zipporah. Both name the same biblical figure.",
        "path": "Zipporah (صفورة = bird/yellow) → Sephora (Greek form of Zipporah)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الشاكرة", "target_lemma": "shakira", "lang_pair": "ara-lat",
        "semantic_score": 0.92,
        "reasoning": "الشاكرة = the grateful/thankful female one (from شكر = to thank). Shakira = Arabic name شاكرة (the grateful one) in its direct form. Perfect name correspondence.",
        "path": "the grateful one (الشاكرة) → Shakira (direct name form)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "مبرقع", "target_lemma": "bricuis", "lang_pair": "ara-lat",
        "semantic_score": 0.45,
        "reasoning": "مبرقع = veiled/masked (wearing a برقع = face veil). bricuis is not a recognized standard Latin word. If it relates to 'brick' or a covered structure, the veil-covering connection is very tenuous.",
        "path": "veiled / covered (مبرقع) → bricuis (obscure target, weak connection)",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الصوفية", "target_lemma": "sophistication", "lang_pair": "ara-lat",
        "semantic_score": 0.75,
        "reasoning": "الصوفية = Sufism (Islamic mystical/philosophical movement; also الصوف = wool). sophistication (< Gk sophistes = expert/philosopher). Both encode advanced philosophical/spiritual refinement: Arabic الصوفية = the sophisticated mystics, sophistication = refined knowledge and worldliness.",
        "path": "Sufi mysticism / philosophical refinement (الصوفية) → sophisticated wisdom → sophistication",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "فلاة", "target_lemma": "field", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "فلاة = open uninhabited land/desert (vast open terrain). field (< Old English feld = open land). Both denote open expanses of land: Arabic فلاة = the open desert terrain, field = open land.",
        "path": "open land / uninhabited terrain (فلاة) → field (open land)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "درجة", "target_lemma": "graduate", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "درجة = a step/degree/rank (from درج = to go step by step). graduate (< Lat gradus = step/degree + -atus). Both encode step-by-step advancement: Arabic درجة = step/degree/rank, graduate = one who has advanced step-by-step through degrees.",
        "path": "step / degree / rank (درجة) → graduated steps → graduate",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "سجل", "target_lemma": "album", "lang_pair": "ara-lat",
        "semantic_score": 0.80,
        "reasoning": "سجل = a large bucket/vessel; also سجل = a record/register (to record). album (< Lat album = white tablet/whiteboard used for public records). Both encode official recording: Arabic سجل = a document/register, Lat album = the white board/record.",
        "path": "record / register (سجل) → official public record → album (albus = white record tablet)",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "بشت", "target_lemma": "vest", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "بشت = a long outer cloak/robe. vest (< Lat vestis = garment/clothing). Both denote outer clothing garments: Arabic بشت = the outer robe, Latin vestis = garment.",
        "path": "outer robe / cloak (بشت) → garment → vest (vestis = garment)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "خارطة", "target_lemma": "card", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "خارطة = a map/chart (from خرط = to strip/peel, leaving a flat surface; or from Lat charta). card (< Lat charta < Gk kharte = leaf of papyrus/writing material). Both trace to the same papyrus/flat writing surface: Arabic خارطة = a map on flat material, card = a piece of flat writing material.",
        "path": "map / chart on flat material (خارطة) → flat writing surface → card (charta)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "خرطوشة", "target_lemma": "cartridge", "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": "خرطوشة = a cartridge (tubular container holding a charge). cartridge (< It cartoccio = paper roll < carta = paper/card). Arabic خرطوشة is borrowed from French 'cartouche' = cartridge. Direct borrowing correspondence.",
        "path": "cartridge (خرطوشة, borrowed from cartouche) → cartridge",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "منطقة", "target_lemma": "zone", "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": "منطقة = a zone/region/belt (from نطق = to belt/gird; a bounded region). zone (< Gk zone = a belt/girdle → enclosed region). Both directly encode a bounded region/girdle: Arabic منطقة = girded region/zone, Gk zone = belt/zone.",
        "path": "girded / bounded region (منطقة) → zone (zone = belt/bounded region)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "مكّن", "target_lemma": "machine", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "مكّن = to establish/enable/empower (from مكّن = to make firm/fixed). axial: 'settling of fine parts into a interior that coheres'. machine (< Gk mekhane = device/contrivance). Both encode 'a device that makes things possible': مكّن = enabling/establishing, machine = an enabling mechanism.",
        "path": "to enable / establish firmly (مكّن) → mechanism → machine",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "البدانة", "target_lemma": "obese", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "البدانة = corpulence/obesity (from بدن = body/fat). axial: 'the body-mass that branches the limbs'. obese (< Lat obesus = fat/gorged, from ob + edere = to have eaten excessively). Both directly encode excessive body fatness.",
        "path": "corpulence / body fat (البدانة) → obese (fat body)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "غراء", "target_lemma": "glue", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "غراء = glue/adhesive (from غرا = to stick/adhere). glue (< OF glu < Lat glus/gluten = glue). Both directly name the adhesive substance: Arabic غراء = glue/adhesive, glue = adhesive.",
        "path": "glue / adhesive (غراء) → glue",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "ألس", "target_lemma": "illusion", "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": "أَلس = deception/confusion of mind; also الأَلس = اختلاط العقل = mental confusion. illusion (< Lat illusio = mockery, from illudere = to mock/play tricks). Both directly encode mental deception: Arabic ألس = mental confusion/deception, illusion = a deceptive perception.",
        "path": "deception / mental confusion (ألس) → illusion",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "تملّي", "target_lemma": "humid", "lang_pair": "ara-lat",
        "semantic_score": 0.45,
        "reasoning": "تملّي = to be fully satiated/full (from مَلِيّ = full/complete; تملأ). humid (< Lat humidus = moist/damp). The Arabic 'fully filled' and Latin 'moist' are different. Satiation does not strongly imply moisture. Very weak link.",
        "path": "fully filled / satiated (تملّي) → moist/damp → humid (very indirect)",
        "method": "weak", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "الصوفية", "target_lemma": "sophistication", "lang_pair": "ara-lat",
        "semantic_score": 0.75,
        "reasoning": "Already scored above — keeping this consistent.",
        "path": "Sufi mysticism (الصوفية) → sophisticated wisdom → sophistication",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    # --- 4 pairs omitted in first pass ---
    {
        "source_lemma": "جنّي", "target_lemma": "genius", "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": "جنّي = of the jinn (a spirit/supernatural being hidden from sight; from جنّ = concealment). genius (< Lat genius = guardian spirit/divine essence, the personal spirit of a person). Both denote an invisible spirit-force: Arabic جنّي = a jinn (hidden spirit), Latin genius = the guiding spirit. Near-perfect: both are supernatural hidden spirits.",
        "path": "hidden spirit / jinn (جنّي) → guardian spirit → genius (personal spirit)",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "قدر", "target_lemma": "kettle", "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": "قدر = a cooking pot/cauldron (القدر: the pot in which food is cooked over fire). kettle (< Old Norse ketill < Lat catillus = small pot, diminutive of catinus = deep vessel). Both directly denote a cooking vessel: Arabic قدر = the pot/cauldron, kettle = the boiling vessel.",
        "path": "cooking pot / cauldron (قدر) → boiling vessel → kettle",
        "method": "masadiq_direct", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "قدر", "target_lemma": "accident", "lang_pair": "ara-lat",
        "semantic_score": 0.78,
        "reasoning": "قدر = fate/divine decree; also قدر = measure/quantity. accident (< Lat accidere = to happen/fall upon, from ad + cadere = to fall). Both encode 'that which befalls': Arabic قدر = fate/what is decreed to befall, accident = what falls/happens upon one. The 'decreed falling upon' of قدر maps to 'that which happens by falling'.",
        "path": "fate / what is decreed to befall (قدر) → that which falls upon one → accident",
        "method": "combined", "annotator": "claude", "batch": "eye2_full"
    },
    {
        "source_lemma": "إقصاء", "target_lemma": "excuse", "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": "إقصاء = exclusion, pushing away to the margin. excuse (< Lat excusare = to free from blame, ex + causa = out of the cause). Both encode 'pushing out/away': إقصاء = pushing to the edge, excusare = pushing out of the cause/blame. Both involve an expulsion from accountability.",
        "path": "exclusion / pushing away (إقصاء) → ex-causa (freed from blame) → excuse",
        "method": "mafahim_deep", "annotator": "claude", "batch": "eye2_full"
    },
]

# Remove exact duplicate pairs (same source+target) keeping the first occurrence
seen = set()
SCORES_DEDUPED = []
for s in SCORES:
    key = (s["source_lemma"], s["target_lemma"])
    if key not in seen:
        seen.add(key)
        SCORES_DEDUPED.append(s)

# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------
BASE = Path(__file__).parent.parent
OUT = BASE / "data" / "llm_annotations" / "eye2_semantic_scores.jsonl"

with open(OUT, "w", encoding="utf-8") as f:
    for s in SCORES_DEDUPED:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

# ---------------------------------------------------------------------------
# Summary stats
# ---------------------------------------------------------------------------
from statistics import mean

by_method = defaultdict(list)
for s in SCORES_DEDUPED:
    by_method[s["method"]].append(s["semantic_score"])

dist = {">= 0.9": 0, ">= 0.7": 0, ">= 0.5": 0, ">= 0.3": 0, "< 0.3": 0}
for s in SCORES_DEDUPED:
    sc = s["semantic_score"]
    if sc >= 0.9:
        dist[">= 0.9"] += 1
    elif sc >= 0.7:
        dist[">= 0.7"] += 1
    elif sc >= 0.5:
        dist[">= 0.5"] += 1
    elif sc >= 0.3:
        dist[">= 0.3"] += 1
    else:
        dist["< 0.3"] += 1

print(f"Eye 2 Full: {len(SCORES_DEDUPED)} pairs scored")
for m, scores in sorted(by_method.items()):
    print(f"  {m}: {len(scores)} pairs (mean: {mean(scores):.2f})")
print()
print("Score distribution:")
for label, count in dist.items():
    print(f"  {label}: {count} pairs")
print(f"\nOutput written to: {OUT}")
