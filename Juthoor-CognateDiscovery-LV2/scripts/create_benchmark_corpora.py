"""Create mini benchmark corpora for fast CPU-only evaluation.

Reads cognate_gold.jsonl, extracts all ara<->eng pairs, and writes:
  - benchmark_mini_ara.jsonl  (one entry per unique Arabic lemma)
  - benchmark_mini_eng.jsonl  (one entry per unique English lemma + 200 distractors)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve()
LV2_ROOT = HERE.parents[1]
GOLD_PATH = LV2_ROOT / "resources" / "benchmarks" / "cognate_gold.jsonl"
OUT_DIR = LV2_ROOT / "data" / "processed"
ARA_OUT = OUT_DIR / "benchmark_mini_ara.jsonl"
ENG_OUT = OUT_DIR / "benchmark_mini_eng.jsonl"

# ---------------------------------------------------------------------------
# 200 common English distractors (high-frequency words NOT expected to be
# cognates of the Arabic benchmark lemmas).
# ---------------------------------------------------------------------------
DISTRACTOR_WORDS: list[tuple[str, str]] = [
    ("table", "piece of furniture with a flat top"),
    ("chair", "seat with a back"),
    ("window", "opening in a wall for light"),
    ("door", "movable barrier"),
    ("floor", "lower surface of a room"),
    ("wall", "vertical structure dividing space"),
    ("roof", "upper covering of a building"),
    ("road", "paved way for travel"),
    ("bridge", "structure spanning a gap"),
    ("river", "large natural water flow"),
    ("mountain", "large natural elevation"),
    ("forest", "large area covered with trees"),
    ("cloud", "visible mass of water droplets"),
    ("rain", "water falling from clouds"),
    ("snow", "frozen water crystals falling"),
    ("wind", "moving air"),
    ("fire", "rapid oxidation producing heat"),
    ("stone", "hard mineral material"),
    ("tree", "tall woody plant"),
    ("grass", "low green plant"),
    ("flower", "reproductive structure of a plant"),
    ("bird", "feathered vertebrate"),
    ("fish", "aquatic vertebrate"),
    ("horse", "large domesticated mammal"),
    ("cow", "female bovine"),
    ("sheep", "woolly domesticated mammal"),
    ("pig", "domesticated swine"),
    ("cat", "small domesticated feline"),
    ("mouse", "small rodent"),
    ("snake", "legless reptile"),
    ("spider", "eight-legged arachnid"),
    ("bee", "winged insect producing honey"),
    ("bread", "baked food from dough"),
    ("milk", "white liquid produced by mammals"),
    ("meat", "animal flesh as food"),
    ("fruit", "sweet edible plant product"),
    ("vegetable", "edible plant or plant part"),
    ("salt", "sodium chloride seasoning"),
    ("sugar", "sweet crystalline substance"),
    ("oil", "liquid fat or lubricant"),
    ("gold", "precious yellow metal"),
    ("silver", "precious white metal"),
    ("iron", "common metallic element"),
    ("copper", "reddish metallic element"),
    ("wood", "hard fibrous material from trees"),
    ("cloth", "woven fabric material"),
    ("thread", "thin strand of fibre"),
    ("needle", "thin pointed sewing implement"),
    ("knife", "cutting implement with a blade"),
    ("sword", "bladed weapon"),
    ("shield", "protective defensive implement"),
    ("arrow", "projectile shot from a bow"),
    ("bow", "weapon for shooting arrows"),
    ("ship", "large water vessel"),
    ("wheel", "circular rotating object"),
    ("rope", "thick twisted cord"),
    ("bucket", "cylindrical container with handle"),
    ("pot", "deep round cooking vessel"),
    ("cup", "small container for drinking"),
    ("plate", "flat dish for food"),
    ("box", "rigid container"),
    ("bag", "flexible container"),
    ("book", "bound set of written pages"),
    ("letter", "written message or alphabet character"),
    ("paper", "thin material for writing"),
    ("ink", "coloured fluid for writing"),
    ("pen", "writing implement"),
    ("school", "institution for education"),
    ("teacher", "one who instructs"),
    ("student", "one who studies"),
    ("market", "place for buying and selling"),
    ("money", "medium of exchange"),
    ("price", "amount asked for goods"),
    ("gift", "something given freely"),
    ("friend", "person one likes"),
    ("enemy", "person one opposes"),
    ("love", "deep affection"),
    ("hate", "intense dislike"),
    ("fear", "unpleasant emotion from danger"),
    ("joy", "feeling of great pleasure"),
    ("pain", "unpleasant physical sensation"),
    ("sleep", "natural rest state"),
    ("dream", "images during sleep"),
    ("laugh", "express amusement vocally"),
    ("cry", "shed tears"),
    ("walk", "move on foot"),
    ("run", "move fast on foot"),
    ("jump", "spring off the ground"),
    ("sit", "rest on buttocks"),
    ("stand", "be in upright position"),
    ("fall", "drop downward"),
    ("throw", "propel through air"),
    ("catch", "intercept moving object"),
    ("push", "apply force to move away"),
    ("pull", "draw toward oneself"),
    ("cut", "divide with sharp implement"),
    ("build", "construct something"),
    ("break", "separate into pieces"),
    ("clean", "free from dirt"),
    ("wash", "cleanse with water"),
    ("cook", "prepare food by heating"),
    ("eat", "consume food"),
    ("drink", "consume liquid"),
    ("give", "transfer to another"),
    ("take", "acquire or receive"),
    ("bring", "carry to a place"),
    ("send", "cause to go"),
    ("find", "discover by searching"),
    ("lose", "cease to have"),
    ("buy", "obtain by payment"),
    ("sell", "exchange for money"),
    ("speak", "utter words"),
    ("listen", "pay attention to sound"),
    ("look", "direct eyes toward"),
    ("see", "perceive with eyes"),
    ("think", "use the mind"),
    ("know", "be aware of"),
    ("want", "desire something"),
    ("need", "require something"),
    ("help", "assist someone"),
    ("work", "do labour"),
    ("play", "engage in recreation"),
    ("sing", "produce musical sounds with voice"),
    ("dance", "move rhythmically to music"),
    ("pray", "address a deity"),
    ("fight", "engage in combat"),
    ("win", "achieve victory"),
    ("lose_v", "fail to win"),
    ("begin", "start"),
    ("end", "finish"),
    ("open", "make accessible"),
    ("close", "shut"),
    ("enter", "go into"),
    ("leave", "go away from"),
    ("grow", "increase in size"),
    ("die", "cease to live"),
    ("live", "be alive"),
    ("born", "come into existence"),
    ("old", "having lived long"),
    ("young", "not old"),
    ("big", "large in size"),
    ("small", "little in size"),
    ("long", "extended in length"),
    ("short", "brief or not tall"),
    ("tall", "great in height"),
    ("wide", "great in extent across"),
    ("narrow", "little width"),
    ("thick", "large in depth"),
    ("thin", "little depth"),
    ("heavy", "great in weight"),
    ("light", "little weight or luminous"),
    ("hot", "high temperature"),
    ("cold", "low temperature"),
    ("wet", "covered with liquid"),
    ("dry", "free from moisture"),
    ("fast", "moving quickly"),
    ("slow", "moving at low speed"),
    ("hard", "firm to the touch"),
    ("soft", "easily yielding to pressure"),
    ("sharp", "having a keen edge"),
    ("smooth", "even surface without bumps"),
    ("rough", "uneven surface"),
    ("sweet", "having a pleasant sugary taste"),
    ("bitter", "having an acrid taste"),
    ("sour", "acidic taste"),
    ("salty", "tasting of salt"),
    ("black", "darkest colour"),
    ("white", "lightest colour"),
    ("red", "colour of blood"),
    ("green", "colour of grass"),
    ("blue", "colour of sky"),
    ("yellow", "colour of sunlight"),
    ("brown", "dark orange colour"),
    ("purple", "colour between red and blue"),
    ("pink", "pale red colour"),
    ("grey", "neutral colour between black and white"),
    ("north", "direction toward the pole"),
    ("south", "direction away from north pole"),
    ("east", "direction of sunrise"),
    ("west", "direction of sunset"),
    ("left", "opposite of right"),
    ("right", "opposite of left"),
    ("up", "toward higher position"),
    ("down", "toward lower position"),
    ("front", "forward-facing side"),
    ("back", "rearward side"),
    ("inside", "interior part"),
    ("outside", "exterior part"),
    ("near", "close in distance"),
    ("far", "great in distance"),
    ("one", "single unit"),
    ("two", "pair"),
    ("four", "twice two"),
    ("five", "one more than four"),
    ("six", "one more than five"),
    ("eight", "twice four"),
    ("nine", "one less than ten"),
    ("hundred", "ten times ten"),
    ("thousand", "ten times hundred"),
    ("today", "the present day"),
    ("tomorrow", "day after today"),
    ("yesterday", "day before today"),
    ("morning", "early part of day"),
    ("evening", "late part of day"),
    ("night_n", "dark part of day"),
    ("week", "seven-day period"),
    ("month_n", "twelve divisions of a year"),
    ("year", "twelve-month period"),
    ("city", "large urban settlement"),
    ("village", "small rural settlement"),
    ("country", "nation or rural area"),
    ("world", "the earth"),
]


def _to_gloss_from_gold(pairs: list[dict]) -> dict[str, str]:
    """Map Arabic lemma -> gloss from gold pairs."""
    out: dict[str, str] = {}
    for p in pairs:
        lemma = p["source"]["lemma"]
        if lemma not in out:
            out[lemma] = p["source"].get("gloss", "")
    return out


def _eng_gloss_from_gold(pairs: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in pairs:
        lemma = p["target"]["lemma"]
        if lemma not in out:
            out[lemma] = p["target"].get("gloss", "")
    return out


def main() -> None:
    if not GOLD_PATH.exists():
        print(f"ERROR: Gold benchmark not found at {GOLD_PATH}", file=sys.stderr)
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Load ara<->eng pairs
    # ------------------------------------------------------------------
    pairs: list[dict] = []
    with GOLD_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            s, t = d["source"], d["target"]
            if s["lang"] == "ara" and t["lang"] == "eng":
                pairs.append(d)
            elif s["lang"] == "eng" and t["lang"] == "ara":
                # normalise direction
                pairs.append(
                    {
                        "source": t,
                        "target": s,
                        "relation": d["relation"],
                        "confidence": d.get("confidence", 1.0),
                    }
                )

    print(f"Loaded {len(pairs)} ara<->eng cognate pairs from gold benchmark.")

    ara_gloss = _to_gloss_from_gold(pairs)
    eng_gloss = _eng_gloss_from_gold(pairs)

    # ------------------------------------------------------------------
    # Write Arabic mini corpus
    # ------------------------------------------------------------------
    ara_lemmas = list(ara_gloss.keys())
    with ARA_OUT.open("w", encoding="utf-8") as fh:
        for idx, lemma in enumerate(ara_lemmas, start=1):
            entry = {
                "id": f"BM.ara.{idx:04d}",
                "language": "ara",
                "stage": "classical",
                "lemma": lemma,
                "gloss": ara_gloss[lemma],
                "record_type": "lexeme",
            }
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Wrote {len(ara_lemmas)} Arabic entries -> {ARA_OUT}")

    # ------------------------------------------------------------------
    # Write English mini corpus (gold targets + distractors)
    # ------------------------------------------------------------------
    eng_lemmas = list(eng_gloss.keys())
    eng_in_bench = set(eng_lemmas)

    # Filter distractors: skip any word that is already in the benchmark
    distractors_filtered = [
        (w, g) for (w, g) in DISTRACTOR_WORDS if w not in eng_in_bench
    ][:200]

    with ENG_OUT.open("w", encoding="utf-8") as fh:
        # Gold targets first
        for idx, lemma in enumerate(eng_lemmas, start=1):
            entry = {
                "id": f"BM.eng.{idx:04d}",
                "language": "eng",
                "stage": "modern",
                "lemma": lemma,
                "gloss": eng_gloss[lemma],
                "record_type": "lexeme",
            }
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        # Distractors
        for dist_idx, (word, gloss) in enumerate(distractors_filtered, start=len(eng_lemmas) + 1):
            entry = {
                "id": f"BM.eng.{dist_idx:04d}",
                "language": "eng",
                "stage": "modern",
                "lemma": word,
                "gloss": gloss,
                "record_type": "lexeme",
                "is_distractor": True,
            }
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    total_eng = len(eng_lemmas) + len(distractors_filtered)
    print(f"Wrote {len(eng_lemmas)} gold-target English + {len(distractors_filtered)} distractors = {total_eng} total -> {ENG_OUT}")


if __name__ == "__main__":
    main()
