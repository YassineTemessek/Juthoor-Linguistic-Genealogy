"""
gen_eye2_pilot.py — Eye 2 semantic scoring for 25 ara-lat gold pairs.

Pairs are selected from cognate_gold.jsonl where the Arabic source has
lookup_status == 'full' in arabic_semantic_profiles.jsonl.

Scoring rules:
  - Check masadiq (dictionary meaning) FIRST.
  - Use mafahim (deep genome meaning) only when masadiq doesn't obviously connect.
  - Score 0.0–1.0; be generous on clear connections (do not underrate).

Methods:
  masadiq_direct  — dictionary meaning gives obvious connection
  mafahim_deep    — needed genome root meaning to find the link
  combined        — both masadiq and mafahim contribute
  weak            — connection is tenuous
  none            — no semantic connection found
"""

import json
import os
import collections

OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "llm_annotations",
    "eye2_semantic_scores.jsonl",
)

# ---------------------------------------------------------------------------
# 25 scored pairs
# Each entry was scored by reasoning over the Arabic profile data:
#   masadiq short_gloss / definition  →  masadiq_meaning
#   mafahim axial_meaning / binary_field_gloss  →  mafahim fields
#   layer2 core_meaning  →  target_meaning
# ---------------------------------------------------------------------------

SCORED_PAIRS = [
    # 1. كلب → canine
    # masadiq: "to seize / bite hard"; core of كلب is the biting dog / rabid dog.
    # canine = relating to dogs / dog-tooth.  Direct: the dog that bites.
    {
        "source_lemma": "كلب",
        "target_lemma": "canine",
        "lang_pair": "ara-lat",
        "semantic_score": 0.92,
        "reasoning": (
            "masadiq: كلب = the dog (animal), also 'to be seized by rabies/biting frenzy'. "
            "canine = relating to dogs, a dog tooth. Direct lexical overlap: both centre on "
            "the dog and its biting nature."
        ),
        "path": "dog (biting animal) → canine (of a dog / dog-tooth)",
        "method": "masadiq_direct",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 2. رئيس → regis
    # masadiq: رأَسَ = to lead / be the head / chief.
    # regis = gen. of rex = 'of the king'.  Both = supreme authority figure.
    {
        "source_lemma": "رئيس",
        "target_lemma": "regis",
        "lang_pair": "ara-lat",
        "semantic_score": 0.93,
        "reasoning": (
            "masadiq: رئيس = leader, chief, head (from رأس = head). "
            "regis (gen. of rex) = of the king / the king's. Both denote the apex "
            "authority figure; Arabic 'head-of-group' and Latin 'king' map onto the "
            "same governance semantic field."
        ),
        "path": "head / chief → supreme leader → king's (regis)",
        "method": "masadiq_direct",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 3. كومة → cemetery
    # masadiq: كومة = a heap, mound, pile of earth.
    # cemetery = sleeping place (Greek koimeterion).
    # masadiq alone gives 'heap of earth'; mafahim needed for burial/sleep link.
    {
        "source_lemma": "كومة",
        "target_lemma": "cemetery",
        "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": (
            "masadiq: كومة = heap, mound of earth. cemetery (< Gk koimeterion = "
            "sleeping place) is the place of burial under mounds of earth. "
            "masadiq gives 'heap of earth'; mafahim (التجمع والكثرة = accumulation) "
            "reinforces the gathered-mass → burial mound → resting place path."
        ),
        "path": "heap of earth (كومة) → burial mound → place of rest → cemetery",
        "method": "combined",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 4. خيط → filament
    # masadiq: خيط = thread, a thin continuous line. axial: امتداد الجرم دقيقا متصلا
    # filament = slender threadlike fiber.  Direct.
    {
        "source_lemma": "خيط",
        "target_lemma": "filament",
        "lang_pair": "ara-lat",
        "semantic_score": 0.96,
        "reasoning": (
            "masadiq: خيط = thread, a thin continuous strand (والخيط الأبيض: the white "
            "thread of dawn). axial: 'the extension of a body, thin and continuous, "
            "penetrating through the interior'. filament = a slender threadlike fiber. "
            "Near-perfect semantic match: both denote a fine, continuous, elongated strand."
        ),
        "path": "thread (خيط) → thin continuous strand → filament",
        "method": "masadiq_direct",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 5. جمل → corridor
    # masadiq: جمل = camel (large moving body). axial: عظم الجرم مع تمام وتجانس
    # corridor < Ital. corridore < correre (to run). A passage you run through.
    # Connection is weak: camel ≠ passage.  Mafahim: large body moving through space.
    {
        "source_lemma": "جمل",
        "target_lemma": "corridor",
        "lang_pair": "ara-lat",
        "semantic_score": 0.30,
        "reasoning": (
            "masadiq: جمل = camel. corridor = a long passage (< Lat currere, to run). "
            "The semantic overlap is weak: the camel moves through desert passages but "
            "the connection to an architectural corridor is indirect. mafahim axial "
            "(large body moving harmoniously) provides only a faint motion-through-space "
            "link. This appears to be a false positive in the gold set."
        ),
        "path": "camel (large body traversing space) → moving through → passage (stretch)",
        "method": "weak",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 6. شرب → absorb
    # masadiq: شرب = to drink, to draw liquid into the body / سحب الماء إلى الجوف
    # absorb = to take in or soak up a substance.  Direct.
    {
        "source_lemma": "شرب",
        "target_lemma": "absorb",
        "lang_pair": "ara-lat",
        "semantic_score": 0.91,
        "reasoning": (
            "masadiq: شرب = to drink; also والمشرب = the direction from which one drinks. "
            "axial: 'drawing water/liquid into the interior, sucking it in and conducting "
            "it through'. absorb (< Lat absorbere = ab + sorbere, to suck in) = to take in "
            "or soak up liquid. Both denote drawing liquid inward by suction."
        ),
        "path": "to drink / suck in liquid (شرب) → draw into interior → absorb",
        "method": "masadiq_direct",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 7. مرج → merge
    # masadiq: مرج = to mix / blend, to leave (two things) unconstrained so they mingle.
    # axial: حركة مختلفة الاتجاهات (multi-directional motion, blending/mixing).
    # merge = to combine into one entity.  Direct.
    {
        "source_lemma": "مرج",
        "target_lemma": "merge",
        "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": (
            "masadiq: مرج = to blend, to mingle (leave two rivers free so they mix); "
            "also the pasture where animals graze together. axial: 'different-directional "
            "movement of things expected to be stable — blending'. merge = to combine "
            "into a single entity. Both share the core 'distinct things mingling into one'."
        ),
        "path": "to mingle / blend (مرج) → combine freely → merge",
        "method": "masadiq_direct",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 8. حوض → basin
    # masadiq: حوض = a basin, cistern, watering trough; أدور حوله = I go around it.
    # basin = wide open container; circular valley.  Direct.
    {
        "source_lemma": "حوض",
        "target_lemma": "basin",
        "lang_pair": "ara-lat",
        "semantic_score": 0.95,
        "reasoning": (
            "masadiq: حوض = a watering trough, cistern, large basin for collecting water. "
            "binary_field: 'containment and possession with strength'. basin = a wide "
            "open container for liquid; also a circular valley. Near-perfect match: "
            "both denote a hollow vessel for holding water."
        ),
        "path": "water basin / cistern (حوض) → hollow container → basin",
        "method": "masadiq_direct",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 9. غور → gorge
    # masadiq: غور = the depth / bottom of a thing; غائر = sunken/deep.
    # axial: تجويف قوي يمتد متعمقًا في أثناء شيء (a powerful cavity extending deep).
    # gorge = a narrow, deep valley; also the throat.  Direct.
    {
        "source_lemma": "غور",
        "target_lemma": "gorge",
        "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": (
            "masadiq: غور = the depth/bottom of something; غار = cave, hollow recess. "
            "axial: 'a powerful cavity extending deep into the interior of a thing'. "
            "gorge = a narrow deep valley between hills; also the throat (deep channel). "
            "Both denote a deep, penetrating hollow or channel."
        ),
        "path": "depth / deep hollow (غور) → deep narrow channel → gorge",
        "method": "masadiq_direct",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 10. طفر → spring
    # masadiq: الطَفرة = الوثبة = the leap, the jump.
    # binary_field: الوصول إلى نهاية الشيء بزيادة = reaching the end of a thing by a leap.
    # spring = to leap; the season of new growth; a water source.  Direct (leap sense).
    {
        "source_lemma": "طفر",
        "target_lemma": "spring",
        "lang_pair": "ara-lat",
        "semantic_score": 0.85,
        "reasoning": (
            "masadiq: الطفرة = الوثبة = a leap, a jump. spring (v.) = to leap or jump; "
            "(n.) the season when things leap into growth; a water source that leaps up. "
            "The primary English sense 'to spring = to leap' maps directly onto الطفرة."
        ),
        "path": "a leap / jump (طفر) → to spring (leap) → spring",
        "method": "masadiq_direct",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 11. فلج → village
    # masadiq: فلج = to split/divide; also فلج النهر = a stream branch; فَلَج = gap between teeth.
    # mafahim binary_field: انفصال ندورًا أو نتوءًا (separation forming a protrusion).
    # village = a small settlement. The semantic connection goes: split off / branch →
    # a small outlying settlement (a branch-off from the main group).
    {
        "source_lemma": "فلج",
        "target_lemma": "village",
        "lang_pair": "ara-lat",
        "semantic_score": 0.55,
        "reasoning": (
            "masadiq: فلج = to split, divide; a branch-stream (فلج النهر). "
            "binary_field: separation forming a protrusion or outlier. village = a small "
            "rural settlement (< Lat villa, farm estate). The connection is indirect: a "
            "branch-off stream → outlying agricultural settlement. Plausible but not "
            "strongly direct."
        ),
        "path": "branch / split off (فلج) → outlying settlement → village",
        "method": "mafahim_deep",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 12. حيل → heal
    # masadiq: حيلة = a means, a stratagem, a device to achieve change.
    # axial: عدول جرم الشيء عن مكانه المعتاد إلى آخر قريب (deflection from habitual state).
    # heal = to restore to health (change from sick state back to healthy state).
    {
        "source_lemma": "حيل",
        "target_lemma": "heal",
        "lang_pair": "ara-lat",
        "semantic_score": 0.65,
        "reasoning": (
            "masadiq: حيل/حيلة = a stratagem, device, means to bring about change (أكثر "
            "حيلة = more resourceful). axial: 'deflection of a thing from its habitual "
            "place/state to a nearby other'. heal = to restore to good health (change "
            "from illness back to wellness). The mafahim axial 'shifting to a better "
            "nearby state' is the bridge: resourceful change of state → healing."
        ),
        "path": "device to change state (حيلة) → bring about state-shift → restore health → heal",
        "method": "combined",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 13. شرح → cheer
    # masadiq: شرح = to open, expand, explain; شرح صدره = to open/expand one's chest (gladden).
    # axial: شق ما هو كتلة حتى تصير رقيقة (slice open a dense mass until it becomes light).
    # cheer = a shout of joy; a cheerful disposition; to gladden.
    {
        "source_lemma": "شرح",
        "target_lemma": "cheer",
        "lang_pair": "ara-lat",
        "semantic_score": 0.80,
        "reasoning": (
            "masadiq: شرح = to open, expand, explain; شرح الصدر (Quran) = expansion of "
            "the chest = gladness, relief. shرحت الغامض = I explained the obscure. "
            "cheer = joyful spirit, to gladden; etymologically 'face, expression of joy'. "
            "The 'expansion of chest → gladness' in Arabic masadiq maps directly onto "
            "cheer as a feeling of openness and joy."
        ),
        "path": "expand / open chest (شرح) → gladden → cheer",
        "method": "masadiq_direct",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 14. بِشت → invest
    # masadiq: بِشت = a type of outer cloak/garment (Persian loanword used in Arabic).
    # invest (< Lat investire = in + vestire) = to clothe; to commit resources.
    # The primary Latin meaning is literally 'to clothe, to envelop'.
    {
        "source_lemma": "بِشت",
        "target_lemma": "invest",
        "lang_pair": "ara-lat",
        "semantic_score": 0.82,
        "reasoning": (
            "بِشت = a long outer cloak/robe (garment placed over one). invest < Lat "
            "investire = in + vestire (to clothe) → original meaning: to clothe someone "
            "in a robe, to formally vest with authority by placing a garment on them. "
            "binary_field: الانتشار الظاهر (outward spreading / covering). Both words "
            "denote placing an outer garment over a body."
        ),
        "path": "outer cloak / robe (بِشت) → to clothe / envelop → invest (to clothe with authority)",
        "method": "masadiq_direct",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 15. طبع → type
    # masadiq: طبع = to stamp, impress a shape in soft material; التأثير في الطين (impression in clay).
    # axial: making material into a form, smoothing its surface.
    # type (< Lat typus < Gk typos = impression, blow, mold) = a printed impression; a category.
    {
        "source_lemma": "طبع",
        "target_lemma": "type",
        "lang_pair": "ara-lat",
        "semantic_score": 0.93,
        "reasoning": (
            "masadiq: طبع = to stamp / impress a mark in soft material (clay); in the "
            "origin it is a مصدر (verbal noun). axial: 'making soft material take a "
            "specific form, smoothing its surface'. type < Lat typus < Gk typos = a "
            "blow, impression, mold → printed type. Both centre on the act of pressing "
            "a form into material to leave a permanent impression."
        ),
        "path": "to stamp / impress in clay (طبع) → impression in material → type",
        "method": "masadiq_direct",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 16. فرض → force
    # masadiq: فرض = to cut/notch into hard material; also to decree/obligate (impose by cutting decree).
    # axial: قطع غائر (غير نافذ) في جرم غليظ = a deep non-penetrating cut in a thick body.
    # force (< Lat fortis = strong, then forzare = to impose by strength).
    # Semantic link: to impose a deep cut / decree by power → force.
    {
        "source_lemma": "فرض",
        "target_lemma": "force",
        "lang_pair": "ara-lat",
        "semantic_score": 0.72,
        "reasoning": (
            "masadiq: فرض = to notch/cut into hard material; to impose an obligation "
            "(decree). axial: 'a deep, non-penetrating cut in a thick body'. force < "
            "Lat fortis (strong) → to compel by strength. The 'imposed decree' sense "
            "of فرض (cutting one's will into another) maps onto force as compulsion. "
            "Not the most direct path but the 'compulsory imposition' meaning bridges them."
        ),
        "path": "to cut an obligation (فرض, impose by cutting) → compel → force",
        "method": "combined",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 17. عقربٌ → scorpion
    # masadiq: عقرب = the scorpion (arachnid); also the zodiac sign Scorpio.
    # scorpion = venomous arachnid. Direct.
    {
        "source_lemma": "عقربٌ",
        "target_lemma": "scorpion",
        "lang_pair": "ara-lat",
        "semantic_score": 0.98,
        "reasoning": (
            "masadiq: عقرب = the scorpion (the arachnid); also the zodiac constellation "
            "Scorpio (برج العقرب). scorpion (< Lat scorpio < Gk skorpios) = the "
            "venomous arachnid. Perfect lexical match: both words name the same creature. "
            "This is a straightforward Semitic–Greek–Latin borrowing chain."
        ),
        "path": "scorpion (عقرب) → Lat scorpio → scorpion",
        "method": "masadiq_direct",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 18. النمر → leopard
    # masadiq: النمر = the leopard / panther (spotted wild cat).
    # mafahim: تخلل في الأثناء إلى الظاهر بلطف (subtle seeping of spots to the surface).
    # leopard = the large spotted wild cat.
    {
        "source_lemma": "النمر",
        "target_lemma": "leopard",
        "lang_pair": "ara-lat",
        "semantic_score": 0.90,
        "reasoning": (
            "masadiq: النمر = the leopard / spotted panther. axial: 'subtle penetration "
            "from the interior to the surface with delicacy' — describing spot-patterning "
            "emerging from within the hide. leopard (< Lat leopardus = leo + pardus, "
            "lion-panther) = the large spotted cat. Both refer to the same spotted "
            "feline; the Arabic also etymologically encodes the spotting pattern."
        ),
        "path": "spotted panther (نمر) → large spotted cat → leopard",
        "method": "masadiq_direct",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 19. لبن → galaxy
    # masadiq: لبن = milk; also the white sap of any tree (كل شجرة لها ماء أبيض فهو لبنها).
    # axial: احتواء الباطن على لطيف يخرج ثم يتماسك.
    # galaxy < Lat galaxias < Gk gala (milk) = the Milky Way (white milky band of stars).
    {
        "source_lemma": "لبن",
        "target_lemma": "galaxy",
        "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": (
            "masadiq: لبن = milk; also white sap of any tree. galaxy < Gk gala (milk) = "
            "the Milky Way; the visual metaphor is the white milky streak across the sky. "
            "Both are rooted in the concept of white milk-like fluid. axial: 'the "
            "interior containing a delicate fluid that emerges and coheres' — exactly "
            "describing the diffuse milky light of the galaxy."
        ),
        "path": "milk / white fluid (لبن) → milky appearance → Milky Way → galaxy",
        "method": "masadiq_direct",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 20. قرس → crust
    # masadiq: قرس = to freeze / congeal (بردٍ / أي جامداً = frozen solid).
    # binary_field: استقرار ما شأنه التسيب في قاع عميق (solidification of what was fluid).
    # crust (< Lat crusta = hard outer shell, frozen coating) = the hard outer layer.
    {
        "source_lemma": "قرس",
        "target_lemma": "crust",
        "lang_pair": "ara-lat",
        "semantic_score": 0.83,
        "reasoning": (
            "masadiq: قرس = to be cold/frozen, to congeal (أي جامداً = frozen solid). "
            "binary_field: 'settling/solidification of what would otherwise flow'. "
            "crust < Lat crusta = a hard outer shell (ice crust, bread crust). Both "
            "involve the solidification of a surface into a hard frozen or baked shell."
        ),
        "path": "to freeze / congeal (قرس) → solidified surface → hard outer shell → crust",
        "method": "combined",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 21. موت → mute
    # masadiq: موت = death; ضد الحياة = opposite of life.
    # axial: تمدد مع همود وسكون وذهاب الحدة = extension with stillness, silence, loss of edge.
    # mute = unable to speak; producing no sound; total silence.
    {
        "source_lemma": "موت",
        "target_lemma": "mute",
        "lang_pair": "ara-lat",
        "semantic_score": 0.78,
        "reasoning": (
            "masadiq: موت = death (ضد الحياة). axial: 'spreading with stillness and "
            "silence, loss of sharpness/vitality'. mute (< Lat mutus = silent, speechless) "
            "= without sound. The core semantic link is: death → absolute silence / "
            "stillness → mute. axial reinforces with 'loss of the expected activity/sound'."
        ),
        "path": "death / cessation of life (موت) → total stillness and silence → mute",
        "method": "combined",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 22. دَرَن → thorn
    # masadiq: دَرَن = filth, grime, encrustation; also a river name.
    # binary_field: الجريان باسترسال أو الامتداد بتوالٍ (flowing with continuity / elongated extension).
    # thorn = a sharp woody projection from a plant.
    # Connection: masadiq gives filth/encrustation (not thorn); mafahim elongated protrusion is closer.
    {
        "source_lemma": "دَرَن",
        "target_lemma": "thorn",
        "lang_pair": "ara-lat",
        "semantic_score": 0.35,
        "reasoning": (
            "masadiq: دَرَن = filth, grime, dirt (dirt that accumulates on skin/surface). "
            "binary_field: elongated continuous extension. thorn = a sharp woody projection. "
            "The masadiq (dirt/encrustation) does not connect to thorn. The mafahim "
            "elongated-extension gives only a faint shape analogy. Connection is tenuous."
        ),
        "path": "elongated protrusion (binary_field) → sharp pointed extension → thorn (weak)",
        "method": "weak",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 23. تفرق → divorce
    # masadiq: تفرّق = to scatter apart, to separate into pieces (التفاريق).
    # axial: فصل بعض شيء من بعضها الآخر فصلا واصلا إلى العمق (deep separation of parts from each other).
    # divorce = legal dissolution of a marriage (deep, formal separation).
    {
        "source_lemma": "تفرق",
        "target_lemma": "divorce",
        "lang_pair": "ara-lat",
        "semantic_score": 0.88,
        "reasoning": (
            "masadiq: تفرّق = to scatter, separate into distinct groups; التفاريق (the "
            "individual pieces). axial: 'separation of parts from each other reaching "
            "to the deep' — full, thorough severance. divorce (< Lat divortium = a "
            "divergence, a parting of ways) = legal dissolution of marriage. Both "
            "describe a thorough, definitive separation of formerly joined parties."
        ),
        "path": "to scatter apart thoroughly (تفرق) → complete severance → divorce",
        "method": "masadiq_direct",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 24. وادي → valley
    # masadiq: وادي = a valley, a river valley, a wadi (dry riverbed).
    # valley < Lat vallis = a valley. Direct.
    {
        "source_lemma": "وادي",
        "target_lemma": "valley",
        "lang_pair": "ara-lat",
        "semantic_score": 0.97,
        "reasoning": (
            "masadiq: وادي = a valley, river valley, wadi. valley < Lat vallis (valley). "
            "Near-perfect semantic match: both denote a low-lying land area between hills, "
            "typically with a watercourse. The words are likely cognate through early "
            "Mediterranean language contact."
        ),
        "path": "valley / wadi (وادي) → low land between hills → valley",
        "method": "masadiq_direct",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
    # 25. فرج → fragile
    # masadiq: فرج = an opening, a gap, a relief (فرجة = a gap; فروج = openings).
    # axial: انفتاح في أثناء جرم كثيف أو بين أجرام (an opening in a dense body, or between bodies).
    # fragile < Lat fragilis = easily broken (from frangere = to break, create gaps).
    {
        "source_lemma": "فرج",
        "target_lemma": "fragile",
        "lang_pair": "ara-lat",
        "semantic_score": 0.75,
        "reasoning": (
            "masadiq: فرج = a gap, opening, breach in a dense structure; relief from "
            "distress (opening of a closed situation). axial: 'an opening or space "
            "within a dense body or between bodies'. fragile < Lat fragilis (from "
            "frangere = to break, create a breach). Both describe the creation of a "
            "breach/opening in a previously whole dense object; fragile = prone to such "
            "breakage."
        ),
        "path": "gap / breach in dense body (فرج) → tendency to fracture → fragile",
        "method": "mafahim_deep",
        "annotator": "claude",
        "batch": "eye2_pilot",
    },
]


def write_output(pairs: list[dict], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        for pair in pairs:
            fh.write(json.dumps(pair, ensure_ascii=False) + "\n")


def print_summary(pairs: list[dict]) -> None:
    method_groups: dict[str, list[float]] = collections.defaultdict(list)
    for p in pairs:
        method_groups[p["method"]].append(p["semantic_score"])

    total = len(pairs)
    print(f"Eye 2 Pilot: {total} pairs scored")
    for method in ["masadiq_direct", "mafahim_deep", "combined", "weak", "none"]:
        scores = method_groups.get(method, [])
        if scores:
            mean = sum(scores) / len(scores)
            print(f"  {method}: {len(scores)} pairs (mean score: {mean:.2f})")
        else:
            print(f"  {method}: 0 pairs")


if __name__ == "__main__":
    assert len(SCORED_PAIRS) == 25, f"Expected 25 pairs, got {len(SCORED_PAIRS)}"

    write_output(SCORED_PAIRS, OUTPUT_PATH)
    print(f"Wrote {len(SCORED_PAIRS)} scored pairs to:\n  {OUTPUT_PATH}\n")
    print_summary(SCORED_PAIRS)
