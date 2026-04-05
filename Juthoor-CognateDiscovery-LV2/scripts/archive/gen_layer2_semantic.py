"""
Generate Layer 2 semantic normalization annotations for all 244 ara-lat gold pairs.
Writes to data/llm_annotations/layer2_semantic_mapping.jsonl
"""
import json
import os

# All 244 ara-lat gold pairs with English semantic annotations.
# No Arabic text in source -- Arabic cognate data is loaded from gold file at runtime.
ANNOTATIONS = [
    # 1
    {"word": "infant", "lang": "lat", "english_glosses": ["infant", "baby", "newborn", "young child", "suckling"], "semantic_fields": ["family", "body"], "core_meaning": "a very young child not yet able to speak", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 2
    {"word": "grocery", "lang": "lat", "english_glosses": ["grocery", "foodstuff", "provisions", "food store", "market goods"], "semantic_fields": ["food", "trade"], "core_meaning": "food and household goods sold in a shop", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 3
    {"word": "basilica", "lang": "lat", "english_glosses": ["basilica", "large hall", "royal hall", "church", "public building"], "semantic_fields": ["building", "religion"], "core_meaning": "a large oblong building used as a court or church", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 4
    {"word": "ceremony", "lang": "lat", "english_glosses": ["ceremony", "sacred rite", "religious worship", "ritual", "observance"], "semantic_fields": ["religion", "ritual"], "core_meaning": "a formal religious or public occasion with prescribed rites", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 5
    {"word": "famous", "lang": "lat", "english_glosses": ["famous", "renowned", "celebrated", "well-known", "famed"], "semantic_fields": ["emotion", "social"], "core_meaning": "widely known and esteemed", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 6
    {"word": "auspex", "lang": "lat", "english_glosses": ["augur", "diviner", "bird-watcher", "oracle", "omen-reader", "soothsayer"], "semantic_fields": ["religion", "ritual"], "core_meaning": "a Roman official who divined omens from the flight of birds", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 7
    {"word": "bullet", "lang": "lat", "english_glosses": ["bullet", "projectile", "ball", "small sphere", "shot"], "semantic_fields": ["war", "tool"], "core_meaning": "a small metal projectile fired from a gun", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 8
    {"word": "auction", "lang": "lat", "english_glosses": ["auction", "public sale", "bidding", "increase", "offer"], "semantic_fields": ["trade"], "core_meaning": "a public sale where goods are sold to the highest bidder", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 9
    {"word": "ossifier", "lang": "lat", "english_glosses": ["bone-maker", "ossifier", "calcifier", "hardener", "bone-forming agent"], "semantic_fields": ["body"], "core_meaning": "something that causes tissue to harden into bone", "arabic_cognate_gloss": None, "confidence": "moderate", "annotator": "claude", "batch": "layer2_batch1"},
    # 10
    {"word": "sewer", "lang": "lat", "english_glosses": ["sewer", "drain", "underground channel", "conduit", "waste pipe"], "semantic_fields": ["building", "tool"], "core_meaning": "an underground pipe or channel for carrying away waste water", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 11
    {"word": "submarine", "lang": "lat", "english_glosses": ["submarine", "underwater vessel", "underwater", "below the sea", "submerged"], "semantic_fields": ["nature", "war", "movement"], "core_meaning": "a vessel or thing that operates under the sea", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 12
    {"word": "check", "lang": "lat", "english_glosses": ["check", "halt", "king in chess", "control", "verify", "stop"], "semantic_fields": ["trade", "movement"], "core_meaning": "a stop or verification; in chess, threatening the king", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 13
    {"word": "heal", "lang": "lat", "english_glosses": ["heal", "cure", "restore to health", "mend", "recover"], "semantic_fields": ["body", "emotion"], "core_meaning": "to restore to good health or soundness", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 14
    {"word": "loco", "lang": "lat", "english_glosses": ["place", "location", "site", "mad", "crazy", "insane"], "semantic_fields": ["movement", "emotion"], "core_meaning": "a place or location; colloquially, mentally deranged", "arabic_cognate_gloss": None, "confidence": "moderate", "annotator": "claude", "batch": "layer2_batch1"},
    # 15
    {"word": "oology", "lang": "lat", "english_glosses": ["study of eggs", "egg science", "ornithology branch", "egg collection"], "semantic_fields": ["animal", "nature"], "core_meaning": "the branch of ornithology dealing with the study of birds' eggs", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 16
    {"word": "rivet", "lang": "lat", "english_glosses": ["rivet", "metal pin", "fastener", "bolt", "nail"], "semantic_fields": ["tool", "building"], "core_meaning": "a short metal pin or bolt used to join metal plates", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 17
    {"word": "regis", "lang": "lat", "english_glosses": ["king", "ruler", "sovereign", "monarch", "of the king"], "semantic_fields": ["social"], "core_meaning": "genitive form of rex meaning 'of the king' or 'king's'", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 18
    {"word": "shit", "lang": "lat", "english_glosses": ["excrement", "feces", "dung", "waste", "defecate"], "semantic_fields": ["body"], "core_meaning": "fecal matter; the act of defecating", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 19
    {"word": "solution", "lang": "lat", "english_glosses": ["solution", "answer", "dissolution", "liquid mixture", "resolution"], "semantic_fields": ["tool", "emotion"], "core_meaning": "the act of solving a problem, or a liquid mixture", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 20
    {"word": "canine", "lang": "lat", "english_glosses": ["dog", "canine", "of a dog", "dog tooth", "hound"], "semantic_fields": ["animal"], "core_meaning": "relating to dogs; a dog tooth", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 21
    {"word": "ex", "lang": "lat", "english_glosses": ["out of", "from", "former", "outside", "beyond"], "semantic_fields": ["movement"], "core_meaning": "Latin preposition meaning out of or from; prefix of removal", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 22
    {"word": "carpet", "lang": "lat", "english_glosses": ["carpet", "rug", "floor covering", "cloth", "tapestry"], "semantic_fields": ["trade", "tool"], "core_meaning": "a thick woven fabric used as a floor covering", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 23
    {"word": "peluis", "lang": "lat", "english_glosses": ["basin", "bowl", "washing vessel", "tub", "pelvis"], "semantic_fields": ["body", "tool"], "core_meaning": "a basin-shaped vessel; variant spelling related to pelvis", "arabic_cognate_gloss": None, "confidence": "moderate", "annotator": "claude", "batch": "layer2_batch1"},
    # 24
    {"word": "pelvis", "lang": "lat", "english_glosses": ["pelvis", "basin", "hip bone", "lower trunk", "bowl"], "semantic_fields": ["body"], "core_meaning": "the bony basin-shaped structure at the base of the spine", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 25
    {"word": "burglar", "lang": "lat", "english_glosses": ["burglar", "thief", "house-breaker", "robber", "intruder"], "semantic_fields": ["social"], "core_meaning": "a person who breaks into a building to commit theft", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 26
    {"word": "lip", "lang": "lat", "english_glosses": ["lip", "mouth edge", "labium", "rim", "oral border"], "semantic_fields": ["body"], "core_meaning": "either of the two fleshy parts forming the edges of the mouth", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 27
    {"word": "viva", "lang": "lat", "english_glosses": ["live", "alive", "long live", "vivid", "hurrah"], "semantic_fields": ["emotion", "body"], "core_meaning": "exclamation meaning 'long live'; alive or vivid", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 28
    {"word": "uncle", "lang": "lat", "english_glosses": ["uncle", "father's brother", "mother's brother", "avunculus", "male relative"], "semantic_fields": ["family"], "core_meaning": "the brother of one's father or mother", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 29
    {"word": "pattern", "lang": "lat", "english_glosses": ["pattern", "model", "template", "patron", "protector", "example"], "semantic_fields": ["tool", "social"], "core_meaning": "a model or template serving as an example or guide", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 30
    {"word": "spring", "lang": "lat", "english_glosses": ["spring", "leap", "jump", "season of growth", "water source", "well"], "semantic_fields": ["nature", "movement"], "core_meaning": "the season of new growth; to leap; a source of water", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 31
    {"word": "voice", "lang": "lat", "english_glosses": ["voice", "sound", "speech", "vocal expression", "vox"], "semantic_fields": ["body", "emotion"], "core_meaning": "the sound produced in the larynx and used for speech", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 32
    {"word": "cemetery", "lang": "lat", "english_glosses": ["cemetery", "graveyard", "burial ground", "sleeping place", "necropolis"], "semantic_fields": ["religion", "building"], "core_meaning": "a place where the dead are buried", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 33
    {"word": "harpoon", "lang": "lat", "english_glosses": ["harpoon", "spear", "hook", "whale-hunting lance", "barbed dart"], "semantic_fields": ["war", "tool", "animal"], "core_meaning": "a barbed spear-like weapon thrown at whales or large fish", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 34
    {"word": "innocent", "lang": "lat", "english_glosses": ["innocent", "not guilty", "harmless", "pure", "blameless", "guiltless"], "semantic_fields": ["emotion", "social"], "core_meaning": "free from guilt or wrongdoing; not causing harm", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 35
    {"word": "chain", "lang": "lat", "english_glosses": ["chain", "fetter", "linked rings", "bond", "shackle", "series"], "semantic_fields": ["tool", "trade"], "core_meaning": "a series of linked metal rings used to bind or connect", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 36
    {"word": "yard", "lang": "lat", "english_glosses": ["yard", "enclosed ground", "courtyard", "garden", "enclosure"], "semantic_fields": ["building", "nature"], "core_meaning": "a piece of enclosed ground adjoining a building", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 37
    {"word": "comet", "lang": "lat", "english_glosses": ["comet", "long-haired star", "celestial body", "heavenly body", "meteor"], "semantic_fields": ["nature"], "core_meaning": "a celestial body with a long luminous tail visible from earth", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 38
    {"word": "lazour", "lang": "lat", "english_glosses": ["azure", "blue", "lapis lazuli", "sky blue", "blue pigment"], "semantic_fields": ["nature", "trade"], "core_meaning": "a bright blue color derived from lapis lazuli", "arabic_cognate_gloss": None, "confidence": "moderate", "annotator": "claude", "batch": "layer2_batch1"},
    # 39
    {"word": "chapel", "lang": "lat", "english_glosses": ["chapel", "small church", "oratory", "place of worship", "sanctuary"], "semantic_fields": ["religion", "building"], "core_meaning": "a small place of Christian worship", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 40
    {"word": "meteorology", "lang": "lat", "english_glosses": ["meteorology", "weather science", "atmospheric science", "climate study", "weather forecasting"], "semantic_fields": ["nature"], "core_meaning": "the scientific study of the atmosphere and weather", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 41
    {"word": "cathedral", "lang": "lat", "english_glosses": ["cathedral", "bishop's church", "seat of bishop", "principal church", "great church"], "semantic_fields": ["religion", "building"], "core_meaning": "the principal church of a diocese, containing the bishop's throne", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 42
    {"word": "forest", "lang": "lat", "english_glosses": ["forest", "woodland", "wilderness", "outside land", "unenclosed wood"], "semantic_fields": ["nature"], "core_meaning": "a large area covered with trees and undergrowth", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 43
    {"word": "nest", "lang": "lat", "english_glosses": ["nest", "bird's dwelling", "shelter", "snug place", "home"], "semantic_fields": ["animal", "nature"], "core_meaning": "a structure built by a bird for laying eggs and rearing young", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 44
    {"word": "scope", "lang": "lat", "english_glosses": ["scope", "range", "field of vision", "aim", "purpose", "extent"], "semantic_fields": ["tool", "movement"], "core_meaning": "the range or extent of an area, subject, or activity", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 45
    {"word": "inspire", "lang": "lat", "english_glosses": ["inspire", "breathe into", "motivate", "encourage", "animate", "stimulate"], "semantic_fields": ["emotion", "body"], "core_meaning": "to breathe life into; to fill with creative energy or enthusiasm", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 46
    {"word": "dictator", "lang": "lat", "english_glosses": ["dictator", "absolute ruler", "tyrant", "one who dictates", "commander"], "semantic_fields": ["social", "war"], "core_meaning": "a ruler with total power over a country", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 47
    {"word": "filament", "lang": "lat", "english_glosses": ["filament", "thread", "thin fiber", "slender wire", "fine strand"], "semantic_fields": ["tool", "trade"], "core_meaning": "a slender threadlike object or fiber", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 48
    {"word": "tablet", "lang": "lat", "english_glosses": ["tablet", "flat slab", "writing surface", "stone slab", "pill", "flat plate"], "semantic_fields": ["tool", "building"], "core_meaning": "a flat slab used for writing or inscription; a medicinal pill", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 49
    {"word": "glossary", "lang": "lat", "english_glosses": ["glossary", "word list", "dictionary", "terminology", "lexicon"], "semantic_fields": ["tool"], "core_meaning": "an alphabetical list of terms with definitions", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 50
    {"word": "invest", "lang": "lat", "english_glosses": ["invest", "clothe", "put on", "endow", "surround", "commit resources"], "semantic_fields": ["trade", "tool"], "core_meaning": "to surround or clothe; to commit money or resources for gain", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 51
    {"word": "casino", "lang": "lat", "english_glosses": ["casino", "small house", "gambling house", "little cottage", "summer house"], "semantic_fields": ["building", "trade"], "core_meaning": "a small house; a place for gambling and entertainment", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 52
    {"word": "far", "lang": "lat", "english_glosses": ["far", "distant", "remote", "spelt grain", "emmer wheat"], "semantic_fields": ["nature", "food", "movement"], "core_meaning": "at a great distance; also a type of grain (Latin far)", "arabic_cognate_gloss": None, "confidence": "moderate", "annotator": "claude", "batch": "layer2_batch1"},
    # 53
    {"word": "emergency", "lang": "lat", "english_glosses": ["emergency", "crisis", "urgent situation", "sudden occurrence", "arising"], "semantic_fields": ["movement", "emotion"], "core_meaning": "a serious unexpected situation requiring immediate action", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 54
    {"word": "corridor", "lang": "lat", "english_glosses": ["corridor", "passageway", "hall", "running path", "gallery"], "semantic_fields": ["building", "movement"], "core_meaning": "a long passage in a building or between buildings", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 55
    {"word": "patriarch", "lang": "lat", "english_glosses": ["patriarch", "founding father", "elder", "religious leader", "head of family"], "semantic_fields": ["family", "religion", "social"], "core_meaning": "the male head of a family or religious community", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 56
    {"word": "lake", "lang": "lat", "english_glosses": ["lake", "body of water", "pond", "pool", "lacus"], "semantic_fields": ["nature"], "core_meaning": "a large inland body of standing water", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 57
    {"word": "oval", "lang": "lat", "english_glosses": ["oval", "egg-shaped", "ellipse", "oblong", "rounded shape"], "semantic_fields": ["tool", "nature"], "core_meaning": "having the shape of an egg; an elliptical form", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 58
    {"word": "negotiate", "lang": "lat", "english_glosses": ["negotiate", "bargain", "trade", "deal", "discuss terms", "transact"], "semantic_fields": ["trade", "social"], "core_meaning": "to discuss terms and reach an agreement", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 59
    {"word": "merge", "lang": "lat", "english_glosses": ["merge", "combine", "blend", "unite", "immerse", "join together"], "semantic_fields": ["movement", "trade"], "core_meaning": "to combine or cause to combine to form a single entity", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 60
    {"word": "aunte", "lang": "lat", "english_glosses": ["aunt", "father's sister", "mother's sister", "female relative", "amita"], "semantic_fields": ["family"], "core_meaning": "the sister of one's father or mother", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 61
    {"word": "immunization", "lang": "lat", "english_glosses": ["immunization", "vaccination", "protection", "inoculation", "immunity"], "semantic_fields": ["body"], "core_meaning": "the process of making a person immune to infection by vaccination", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 62
    {"word": "foreign", "lang": "lat", "english_glosses": ["foreign", "alien", "from outside", "exotic", "belonging to another country"], "semantic_fields": ["social", "movement"], "core_meaning": "belonging to or characteristic of another country", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 63
    {"word": "vaccine", "lang": "lat", "english_glosses": ["vaccine", "inoculation", "cowpox preparation", "immunity booster", "biological injection"], "semantic_fields": ["body", "animal"], "core_meaning": "a preparation used to stimulate immunity against disease", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 64
    {"word": "bruise", "lang": "lat", "english_glosses": ["bruise", "contusion", "crush", "wound", "discolored injury"], "semantic_fields": ["body"], "core_meaning": "an injury appearing as an area of discolored skin from a blow", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 65
    {"word": "cuff", "lang": "lat", "english_glosses": ["cuff", "sleeve end", "wristband", "sleeve border", "blow with hand"], "semantic_fields": ["tool", "body"], "core_meaning": "the end part of a sleeve; a blow with the open hand", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 66
    {"word": "veterinary", "lang": "lat", "english_glosses": ["veterinary", "animal doctor", "beast of burden care", "animal medicine", "livestock treatment"], "semantic_fields": ["animal", "body"], "core_meaning": "relating to the medical treatment of animals", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 67
    {"word": "boot", "lang": "lat", "english_glosses": ["boot", "footwear", "shoe", "high shoe", "leg covering"], "semantic_fields": ["tool", "body"], "core_meaning": "a sturdy item of footwear covering the foot and ankle", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 68
    {"word": "bug", "lang": "lat", "english_glosses": ["bug", "insect", "creeping creature", "ghost", "goblin", "pest"], "semantic_fields": ["animal", "nature"], "core_meaning": "an insect or small creeping creature; a frightening creature", "arabic_cognate_gloss": None, "confidence": "moderate", "annotator": "claude", "batch": "layer2_batch1"},
    # 69
    {"word": "animal", "lang": "lat", "english_glosses": ["animal", "living creature", "beast", "creature with breath", "fauna"], "semantic_fields": ["animal", "nature"], "core_meaning": "a living organism that feeds and moves voluntarily", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 70
    {"word": "sea", "lang": "lat", "english_glosses": ["sea", "ocean", "large body of saltwater", "mare", "maritime"], "semantic_fields": ["nature"], "core_meaning": "a large body of saltwater covering most of the earth's surface", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 71
    {"word": "dome", "lang": "lat", "english_glosses": ["dome", "rounded roof", "cupola", "cathedral", "domus", "house"], "semantic_fields": ["building"], "core_meaning": "a rounded vault forming the roof of a building", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 72
    {"word": "hair", "lang": "lat", "english_glosses": ["hair", "strand", "fiber", "capillus", "fur", "filament on skin"], "semantic_fields": ["body", "nature"], "core_meaning": "fine threadlike strands growing from the skin of mammals", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 73
    {"word": "bus", "lang": "lat", "english_glosses": ["bus", "omnibus", "vehicle for all", "public transport", "carriage"], "semantic_fields": ["movement", "tool"], "core_meaning": "a large road vehicle for carrying many passengers", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 74
    {"word": "ascend", "lang": "lat", "english_glosses": ["ascend", "climb", "go up", "rise", "mount", "scale"], "semantic_fields": ["movement"], "core_meaning": "to go up or climb to a higher position", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 75
    {"word": "oil", "lang": "lat", "english_glosses": ["oil", "olive oil", "fat", "lubricant", "oleum", "ointment"], "semantic_fields": ["food", "trade", "tool"], "core_meaning": "a viscous liquid derived from plants or minerals used in cooking and lubrication", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 76
    {"word": "nation", "lang": "lat", "english_glosses": ["nation", "people", "birth group", "tribe", "race", "country"], "semantic_fields": ["social"], "core_meaning": "a large group of people sharing common descent, culture, or territory", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 77
    {"word": "village", "lang": "lat", "english_glosses": ["village", "small settlement", "hamlet", "rural community", "villa community"], "semantic_fields": ["building", "social"], "core_meaning": "a small collection of houses in a rural area", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 78
    {"word": "cheer", "lang": "lat", "english_glosses": ["cheer", "joy", "face", "good spirit", "expression", "happiness"], "semantic_fields": ["emotion"], "core_meaning": "a shout of joy or encouragement; a cheerful disposition", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 79
    {"word": "cartridge", "lang": "lat", "english_glosses": ["cartridge", "paper tube", "ammunition case", "charge holder", "scroll"], "semantic_fields": ["war", "tool"], "core_meaning": "a case containing a charge for a firearm or ink for a printer", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 80
    {"word": "genius", "lang": "lat", "english_glosses": ["genius", "spirit", "guardian spirit", "innate ability", "intellect", "brilliance"], "semantic_fields": ["religion", "emotion"], "core_meaning": "exceptional intellectual or creative power; a Roman tutelary spirit", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 81
    {"word": "zone", "lang": "lat", "english_glosses": ["zone", "belt", "region", "area", "girdle", "band"], "semantic_fields": ["nature", "building"], "core_meaning": "a belt or band; a defined region or area", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 82
    {"word": "deodorant", "lang": "lat", "english_glosses": ["deodorant", "odor remover", "smell-masker", "antiperspirant", "fragrance"], "semantic_fields": ["body", "tool"], "core_meaning": "a substance applied to the body to prevent or mask unpleasant odors", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 83
    {"word": "general", "lang": "lat", "english_glosses": ["general", "military commander", "overall", "widespread", "common", "of a kind"], "semantic_fields": ["war", "social"], "core_meaning": "a senior military officer; relating to the whole rather than a specific part", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 84
    {"word": "spoil", "lang": "lat", "english_glosses": ["spoil", "plunder", "booty", "ruin", "corrupt", "war trophy"], "semantic_fields": ["war", "trade"], "core_meaning": "to damage or ruin; goods seized in war or robbery", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 85
    {"word": "calamity", "lang": "lat", "english_glosses": ["calamity", "disaster", "misfortune", "catastrophe", "crop damage", "ruin"], "semantic_fields": ["emotion", "nature"], "core_meaning": "an event causing great and often sudden damage or distress", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 86
    {"word": "expire", "lang": "lat", "english_glosses": ["expire", "breathe out", "die", "end", "run out", "exhale"], "semantic_fields": ["body", "movement"], "core_meaning": "to breathe one's last; to come to an end", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 87
    {"word": "mile", "lang": "lat", "english_glosses": ["mile", "thousand paces", "mille passuum", "distance unit", "road measure"], "semantic_fields": ["number", "movement"], "core_meaning": "a unit of linear measure equal to 1,760 yards; Latin mille (thousand)", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 88
    {"word": "mill", "lang": "lat", "english_glosses": ["mill", "grinder", "millstone", "grind", "flour machine", "mola"], "semantic_fields": ["food", "tool", "building"], "core_meaning": "a building with machinery for grinding grain into flour", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 89
    {"word": "videre", "lang": "lat", "english_glosses": ["to see", "see", "perceive", "look", "observe", "view"], "semantic_fields": ["body", "movement"], "core_meaning": "Latin infinitive meaning 'to see'", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 90
    {"word": "envy", "lang": "lat", "english_glosses": ["envy", "jealousy", "covetousness", "resentment", "grudge", "invidia"], "semantic_fields": ["emotion"], "core_meaning": "a feeling of discontented longing for another's advantages", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 91
    {"word": "agent", "lang": "lat", "english_glosses": ["agent", "doer", "actor", "representative", "one who acts", "operator"], "semantic_fields": ["social", "trade"], "core_meaning": "a person who acts on behalf of another; one who takes action", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 92
    {"word": "gladiator", "lang": "lat", "english_glosses": ["gladiator", "sword fighter", "arena combatant", "armed fighter", "swordsman"], "semantic_fields": ["war", "social"], "core_meaning": "a trained fighter in Roman arenas who fought for public entertainment", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 93
    {"word": "idol", "lang": "lat", "english_glosses": ["idol", "image", "false god", "icon", "effigy", "worshipped image"], "semantic_fields": ["religion"], "core_meaning": "an image or statue worshipped as a god; an object of devotion", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 94
    {"word": "canyon", "lang": "lat", "english_glosses": ["canyon", "gorge", "deep ravine", "chasm", "deep valley", "tube"], "semantic_fields": ["nature"], "core_meaning": "a deep gorge typically with a river flowing through it", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 95
    {"word": "harvest", "lang": "lat", "english_glosses": ["harvest", "crop", "reaping", "gather crops", "autumn yield", "produce"], "semantic_fields": ["food", "nature"], "core_meaning": "the process of gathering ripe crops from the fields", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 96
    {"word": "horticulture", "lang": "lat", "english_glosses": ["horticulture", "garden cultivation", "gardening", "growing plants", "garden science"], "semantic_fields": ["nature", "food"], "core_meaning": "the art or practice of garden cultivation and management", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 97
    {"word": "grail", "lang": "lat", "english_glosses": ["grail", "cup", "bowl", "holy vessel", "sacred chalice", "dish"], "semantic_fields": ["religion", "tool"], "core_meaning": "a cup or dish; especially the Holy Grail of Arthurian legend", "arabic_cognate_gloss": None, "confidence": "moderate", "annotator": "claude", "batch": "layer2_batch1"},
    # 98
    {"word": "hall", "lang": "lat", "english_glosses": ["hall", "large room", "entrance passage", "meeting room", "corridor", "manor"], "semantic_fields": ["building"], "core_meaning": "a large room for meetings or events; an entrance passage", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 99
    {"word": "gorge", "lang": "lat", "english_glosses": ["gorge", "narrow pass", "throat", "ravine", "eat greedily", "gullet"], "semantic_fields": ["nature", "body", "food"], "core_meaning": "a narrow valley between hills; the throat; to eat greedily", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 100
    {"word": "imitate", "lang": "lat", "english_glosses": ["imitate", "copy", "mimic", "emulate", "reproduce", "simulate"], "semantic_fields": ["movement", "social"], "core_meaning": "to copy or follow as a model", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 101
    {"word": "alone", "lang": "lat", "english_glosses": ["alone", "solitary", "by oneself", "single", "isolated", "only"], "semantic_fields": ["emotion", "social"], "core_meaning": "having no one else present; on one's own", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 102
    {"word": "lave", "lang": "lat", "english_glosses": ["lave", "wash", "bathe", "cleanse", "flow over", "lavare"], "semantic_fields": ["body", "nature"], "core_meaning": "to wash or bathe; (of water) to flow along or against", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 103
    {"word": "bible", "lang": "lat", "english_glosses": ["bible", "book", "sacred scripture", "holy text", "book of books"], "semantic_fields": ["religion"], "core_meaning": "the Christian scriptures; any authoritative book", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 104
    {"word": "enter", "lang": "lat", "english_glosses": ["enter", "go in", "come in", "intrude", "penetrate", "pass inside"], "semantic_fields": ["movement"], "core_meaning": "to come or go into a place", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 105
    {"word": "accent", "lang": "lat", "english_glosses": ["accent", "stress", "pronunciation", "tone", "emphasis", "dialect"], "semantic_fields": ["body", "social"], "core_meaning": "a distinctive way of pronouncing words; emphasis placed on a syllable", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 106
    {"word": "abbey", "lang": "lat", "english_glosses": ["abbey", "monastery", "convent", "abbot's dwelling", "religious house"], "semantic_fields": ["religion", "building"], "core_meaning": "a monastery or convent headed by an abbot or abbess", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 107
    {"word": "geometry", "lang": "lat", "english_glosses": ["geometry", "earth measurement", "mathematics of shape", "spatial science", "mensuration"], "semantic_fields": ["number", "nature"], "core_meaning": "the branch of mathematics concerned with shapes, sizes, and properties of space", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 108
    {"word": "absorb", "lang": "lat", "english_glosses": ["absorb", "suck up", "swallow", "soak in", "assimilate", "engulf"], "semantic_fields": ["body", "movement"], "core_meaning": "to take in or soak up a substance; to assimilate knowledge", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 109
    {"word": "divorce", "lang": "lat", "english_glosses": ["divorce", "separation", "dissolution of marriage", "turning away", "marital split"], "semantic_fields": ["family", "social"], "core_meaning": "the legal dissolution of a marriage", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 110
    {"word": "navy", "lang": "lat", "english_glosses": ["navy", "fleet", "naval force", "warships", "sea force", "navis"], "semantic_fields": ["war", "movement"], "core_meaning": "the branch of a country's armed forces that operates at sea", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 111
    {"word": "serrate", "lang": "lat", "english_glosses": ["serrate", "saw-toothed", "notched", "jagged edge", "toothed like a saw"], "semantic_fields": ["tool", "nature"], "core_meaning": "having a jagged edge like the teeth of a saw", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 112
    {"word": "lizard", "lang": "lat", "english_glosses": ["lizard", "reptile", "lacertus", "small scaled animal", "cold-blooded creature"], "semantic_fields": ["animal", "nature"], "core_meaning": "a small reptile with four legs and a long tail", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 113
    {"word": "voyage", "lang": "lat", "english_glosses": ["voyage", "journey", "sea travel", "expedition", "trip", "viaticum"], "semantic_fields": ["movement"], "core_meaning": "a long journey, especially by sea or in space", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 114
    {"word": "pass", "lang": "lat", "english_glosses": ["pass", "go by", "mountain passage", "step", "passage", "move through"], "semantic_fields": ["movement", "nature"], "core_meaning": "to go by or beyond; a route through mountains", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 115
    {"word": "crow", "lang": "lat", "english_glosses": ["crow", "black bird", "corvid", "raven-like bird", "cry of rooster"], "semantic_fields": ["animal", "nature"], "core_meaning": "a large black bird; the cry of a rooster", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 116
    {"word": "piece", "lang": "lat", "english_glosses": ["piece", "fragment", "part", "portion", "chunk", "bit"], "semantic_fields": ["tool", "trade"], "core_meaning": "a portion of something separated from the whole", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 117
    {"word": "escalator", "lang": "lat", "english_glosses": ["escalator", "moving staircase", "stairs", "climb mechanism", "ascending machine"], "semantic_fields": ["building", "movement"], "core_meaning": "a moving staircase that carries people between floors", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 118
    {"word": "count", "lang": "lat", "english_glosses": ["count", "nobleman", "companion", "enumerate", "tally", "comes"], "semantic_fields": ["number", "social"], "core_meaning": "to determine the total of; a European nobleman (from Latin comes)", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 119
    {"word": "europe", "lang": "lat", "english_glosses": ["Europe", "continent", "western lands", "broad land", "the West"], "semantic_fields": ["nature", "social"], "core_meaning": "the continent west of Asia and north of Africa", "arabic_cognate_gloss": None, "confidence": "moderate", "annotator": "claude", "batch": "layer2_batch1"},
    # 120
    {"word": "albino", "lang": "lat", "english_glosses": ["albino", "white", "lacking pigment", "whitened", "albus"], "semantic_fields": ["body", "nature"], "core_meaning": "a person or animal lacking normal pigmentation, appearing very pale", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 121
    {"word": "fragile", "lang": "lat", "english_glosses": ["fragile", "breakable", "brittle", "delicate", "easily broken", "frail"], "semantic_fields": ["tool", "body"], "core_meaning": "easily broken or damaged; delicate", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 122
    {"word": "type", "lang": "lat", "english_glosses": ["type", "kind", "sort", "category", "impression", "model", "stamp"], "semantic_fields": ["tool", "trade"], "core_meaning": "a category of things with common characteristics; a printed impression", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 123
    {"word": "force", "lang": "lat", "english_glosses": ["force", "strength", "power", "compel", "physical power", "fortis"], "semantic_fields": ["movement", "war", "emotion"], "core_meaning": "physical strength or energy; power or compulsion", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 124
    {"word": "kettle", "lang": "lat", "english_glosses": ["kettle", "pot", "boiling vessel", "cauldron", "caldarium", "cooking pot"], "semantic_fields": ["food", "tool"], "core_meaning": "a metal pot used for boiling water or cooking", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 125
    {"word": "accident", "lang": "lat", "english_glosses": ["accident", "mishap", "chance event", "unforeseen occurrence", "falling upon"], "semantic_fields": ["emotion", "movement"], "core_meaning": "an unfortunate event that occurs unexpectedly and unintentionally", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 126
    {"word": "humid", "lang": "lat", "english_glosses": ["humid", "moist", "damp", "wet", "moisture-laden", "humidus"], "semantic_fields": ["nature", "body"], "core_meaning": "having a high level of moisture in the air; damp", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 127
    {"word": "illusion", "lang": "lat", "english_glosses": ["illusion", "deception", "false appearance", "hallucination", "vision", "delusion"], "semantic_fields": ["emotion", "movement"], "core_meaning": "a false belief or impression; something that deceives the senses", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 128
    {"word": "machine", "lang": "lat", "english_glosses": ["machine", "device", "mechanism", "engine", "contrivance", "machina"], "semantic_fields": ["tool", "building"], "core_meaning": "an apparatus using mechanical power to perform a task", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 129
    {"word": "obese", "lang": "lat", "english_glosses": ["obese", "fat", "overweight", "corpulent", "having eaten too much", "grossly fat"], "semantic_fields": ["body", "food"], "core_meaning": "grossly overweight; having an excessive accumulation of fat", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 130
    {"word": "glue", "lang": "lat", "english_glosses": ["glue", "adhesive", "paste", "binder", "gluey substance", "gluten"], "semantic_fields": ["tool", "food"], "core_meaning": "a sticky substance used for joining things together", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 131
    {"word": "sophistication", "lang": "lat", "english_glosses": ["sophistication", "refinement", "worldliness", "adulteration", "clever argumentation", "subtlety"], "semantic_fields": ["social", "emotion"], "core_meaning": "the quality of being worldly-wise and knowledgeable; refinement", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 132
    {"word": "field", "lang": "lat", "english_glosses": ["field", "open land", "battlefield", "meadow", "domain", "area"], "semantic_fields": ["nature", "war"], "core_meaning": "an area of open land; a battlefield; a domain of activity", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 133
    {"word": "graduate", "lang": "lat", "english_glosses": ["graduate", "step", "degree holder", "earn a diploma", "advance by steps", "rank"], "semantic_fields": ["social", "number"], "core_meaning": "to complete an academic degree; to advance by steps or grades", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 134
    {"word": "album", "lang": "lat", "english_glosses": ["album", "white tablet", "record collection", "blank white surface", "official register"], "semantic_fields": ["tool", "trade"], "core_meaning": "a blank white board for notices; a collection of music or photos", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 135
    {"word": "vest", "lang": "lat", "english_glosses": ["vest", "garment", "clothing", "vestment", "waistcoat", "body covering"], "semantic_fields": ["tool", "body"], "core_meaning": "a sleeveless garment worn over a shirt; clothing in general", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 136
    {"word": "card", "lang": "lat", "english_glosses": ["card", "paper sheet", "tablet", "written message", "charta", "papyrus"], "semantic_fields": ["tool", "trade"], "core_meaning": "a thin flat piece of paper or cardboard for writing or playing", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 137
    {"word": "bricuis", "lang": "lat", "english_glosses": ["spotted", "speckled", "freckled", "variegated", "mottled"], "semantic_fields": ["body", "nature"], "core_meaning": "a term possibly meaning spotted or speckled (rare Latin/Celtic)", "arabic_cognate_gloss": None, "confidence": "uncertain", "annotator": "claude", "batch": "layer2_batch1"},
    # 138
    {"word": "cain", "lang": "lat", "english_glosses": ["Cain", "first murderer", "biblical fratricide", "son of Adam", "smith", "metalworker"], "semantic_fields": ["religion", "family"], "core_meaning": "biblical figure; eldest son of Adam who killed his brother Abel; name meaning 'acquired' or 'smith'", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 139
    {"word": "dua", "lang": "lat", "english_glosses": ["two", "duality", "a pair", "prayer", "supplication"], "semantic_fields": ["number", "religion"], "core_meaning": "the number two (Latin duo) or a prayer/supplication (Arabic/Islamic)", "arabic_cognate_gloss": None, "confidence": "moderate", "annotator": "claude", "batch": "layer2_batch1"},
    # 140
    {"word": "ethan", "lang": "lat", "english_glosses": ["strong", "enduring", "firm", "solid", "steadfast", "biblical name"], "semantic_fields": ["emotion", "religion"], "core_meaning": "a Hebrew/biblical name meaning strong, enduring, or firm", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 141
    {"word": "esther", "lang": "lat", "english_glosses": ["star", "hidden", "myrtle", "biblical queen", "Persian name"], "semantic_fields": ["nature", "religion"], "core_meaning": "a biblical name meaning star or hidden; a Hebrew queen", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 142
    {"word": "hannibal", "lang": "lat", "english_glosses": ["Hannibal", "grace of Baal", "Carthaginian general", "Semitic name", "favor of god"], "semantic_fields": ["religion", "war", "social"], "core_meaning": "a Semitic name meaning 'grace of Baal'; the famous Carthaginian general", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 143
    {"word": "rihanna", "lang": "lat", "english_glosses": ["sweet basil", "queen", "fragrant", "joy", "Semitic name"], "semantic_fields": ["nature", "emotion"], "core_meaning": "a Semitic name meaning sweet basil, fragrance, or joy", "arabic_cognate_gloss": None, "confidence": "moderate", "annotator": "claude", "batch": "layer2_batch1"},
    # 144
    {"word": "sabrina", "lang": "lat", "english_glosses": ["Sabrina", "river Severn", "boundary river", "Celtic goddess", "mythical figure"], "semantic_fields": ["nature", "religion"], "core_meaning": "a name of Celtic origin relating to the River Severn; a legendary figure", "arabic_cognate_gloss": None, "confidence": "moderate", "annotator": "claude", "batch": "layer2_batch1"},
    # 145
    {"word": "sephora", "lang": "lat", "english_glosses": ["Sephora", "bird", "sparrow", "biblical figure", "wife of Moses"], "semantic_fields": ["animal", "religion", "family"], "core_meaning": "biblical figure, wife of Moses; from Hebrew meaning 'bird'", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 146
    {"word": "shakira", "lang": "lat", "english_glosses": ["grateful", "thankful", "graceful", "Semitic name"], "semantic_fields": ["emotion", "religion"], "core_meaning": "a Semitic name meaning grateful or thankful", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 147
    {"word": "mystery", "lang": "lat", "english_glosses": ["mystery", "secret", "hidden thing", "religious rite", "enigma", "puzzle"], "semantic_fields": ["religion", "emotion"], "core_meaning": "something unexplained or secret; a religious rite known only to initiates", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 148
    {"word": "mute", "lang": "lat", "english_glosses": ["mute", "silent", "unable to speak", "soundless", "dumb", "voiceless"], "semantic_fields": ["body", "emotion"], "core_meaning": "unable to speak; producing no sound", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 149
    {"word": "talent", "lang": "lat", "english_glosses": ["talent", "gift", "ability", "weight unit", "monetary unit", "natural skill"], "semantic_fields": ["trade", "emotion", "number"], "core_meaning": "a natural aptitude or skill; an ancient unit of weight and money", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 150
    {"word": "gum", "lang": "lat", "english_glosses": ["gum", "resin", "sticky substance", "gingiva", "chewing gum", "rubber"], "semantic_fields": ["body", "food", "trade"], "core_meaning": "a sticky substance from plants; the tissue surrounding the teeth", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 151
    {"word": "rein", "lang": "lat", "english_glosses": ["rein", "strap", "bridle", "control", "restraint", "harness"], "semantic_fields": ["animal", "tool", "movement"], "core_meaning": "a strap used to guide and control a horse", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 152
    {"word": "science", "lang": "lat", "english_glosses": ["science", "knowledge", "learning", "scientia", "systematic study", "understanding"], "semantic_fields": ["tool", "social"], "core_meaning": "systematic study of the natural world through observation and experiment", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 153
    {"word": "acid", "lang": "lat", "english_glosses": ["acid", "sour", "sharp", "acidic substance", "corrosive", "tart"], "semantic_fields": ["food", "tool", "nature"], "core_meaning": "a sharp-tasting substance; a corrosive chemical", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 154
    {"word": "gala", "lang": "lat", "english_glosses": ["gala", "festivity", "celebration", "festive occasion", "cheerful event", "milk"], "semantic_fields": ["emotion", "food"], "core_meaning": "a festive celebration or entertainment; also Greek for milk", "arabic_cognate_gloss": None, "confidence": "moderate", "annotator": "claude", "batch": "layer2_batch1"},
    # 155
    {"word": "hyaline", "lang": "lat", "english_glosses": ["hyaline", "glassy", "transparent", "clear", "crystal-like", "vitreous"], "semantic_fields": ["nature", "body"], "core_meaning": "glassy or transparent in appearance; resembling glass", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 156
    {"word": "scirrhous", "lang": "lat", "english_glosses": ["scirrhous", "hard tumor", "indurated", "hardened", "fibrous cancer"], "semantic_fields": ["body"], "core_meaning": "denoting a hard type of cancer or tumor", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 157
    {"word": "scylla", "lang": "lat", "english_glosses": ["Scylla", "sea monster", "whirlpool danger", "mythological creature", "rocky hazard"], "semantic_fields": ["nature", "religion"], "core_meaning": "a mythological sea monster from Greek legend; a dangerous rocky hazard", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 158
    {"word": "tinnitus", "lang": "lat", "english_glosses": ["tinnitus", "ringing in ears", "ear noise", "buzzing sound", "bell-like ringing"], "semantic_fields": ["body"], "core_meaning": "a ringing or buzzing sound in the ears", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 159
    {"word": "bard", "lang": "lat", "english_glosses": ["bard", "poet", "singer", "Celtic poet", "horse armor", "storyteller"], "semantic_fields": ["social", "animal"], "core_meaning": "a Celtic poet-singer; a person who composed and recited epic poetry", "arabic_cognate_gloss": None, "confidence": "moderate", "annotator": "claude", "batch": "layer2_batch1"},
    # 160
    {"word": "bazaar", "lang": "lat", "english_glosses": ["bazaar", "market", "marketplace", "oriental market", "fair", "trading place"], "semantic_fields": ["trade", "building"], "core_meaning": "a market in an Eastern country; a sale of goods for charity", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 161
    {"word": "olio", "lang": "lat", "english_glosses": ["olio", "medley", "mixture", "stew", "hodgepodge", "assortment"], "semantic_fields": ["food", "trade"], "core_meaning": "a miscellaneous mixture; a type of stew with varied ingredients", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 162
    {"word": "omen", "lang": "lat", "english_glosses": ["omen", "sign", "portent", "augury", "foreboding", "prophetic sign"], "semantic_fields": ["religion", "emotion"], "core_meaning": "an event regarded as a prophetic sign of good or evil", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 163
    {"word": "nuchal", "lang": "lat", "english_glosses": ["nuchal", "nape of neck", "back of neck", "cervical", "neck region"], "semantic_fields": ["body"], "core_meaning": "relating to the nape or back of the neck", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 164
    {"word": "saurian", "lang": "lat", "english_glosses": ["saurian", "lizard-like", "reptilian", "dinosaur-like", "of lizards"], "semantic_fields": ["animal", "nature"], "core_meaning": "relating to or resembling lizards or large reptiles", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 165
    {"word": "serpentine", "lang": "lat", "english_glosses": ["serpentine", "snake-like", "winding", "coiling", "sinuous", "snake green mineral"], "semantic_fields": ["animal", "nature", "movement"], "core_meaning": "resembling or characteristic of a serpent; winding and twisting", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 166
    {"word": "satyr", "lang": "lat", "english_glosses": ["satyr", "woodland deity", "lustful creature", "half-goat man", "forest spirit"], "semantic_fields": ["religion", "nature", "animal"], "core_meaning": "a woodland deity in Greek mythology, part man part goat, known for revelry", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 167
    {"word": "senile", "lang": "lat", "english_glosses": ["senile", "old", "aged", "of old age", "mentally deteriorated", "senex"], "semantic_fields": ["body", "emotion"], "core_meaning": "relating to old age; having mental decline associated with old age", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 168
    {"word": "stove", "lang": "lat", "english_glosses": ["stove", "furnace", "heated room", "cooking appliance", "heater", "oven"], "semantic_fields": ["food", "building", "tool"], "core_meaning": "an appliance for cooking or heating", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 169
    {"word": "because", "lang": "lat", "english_glosses": ["because", "for the reason that", "by cause", "since", "as", "owing to"], "semantic_fields": ["emotion"], "core_meaning": "for the reason that; by reason of", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 170
    {"word": "ink", "lang": "lat", "english_glosses": ["ink", "writing fluid", "dye", "encaustum", "pigment", "coloring liquid"], "semantic_fields": ["trade", "tool"], "core_meaning": "a colored fluid used for writing, drawing, or printing", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 171
    {"word": "basin", "lang": "lat", "english_glosses": ["basin", "bowl", "vessel", "hollow container", "washbowl", "drainage area"], "semantic_fields": ["tool", "building", "nature"], "core_meaning": "a wide open container; a circular valley or drainage area", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 172
    {"word": "excuse", "lang": "lat", "english_glosses": ["excuse", "pardon", "justification", "reason", "exemption", "free from blame"], "semantic_fields": ["social", "emotion"], "core_meaning": "a reason to justify a fault; to release from obligation or blame", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 173
    {"word": "monitor", "lang": "lat", "english_glosses": ["monitor", "overseer", "warning device", "screen", "adviser", "one who warns"], "semantic_fields": ["tool", "social"], "core_meaning": "a device for observing or warning; one who oversees", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 174
    {"word": "ounce", "lang": "lat", "english_glosses": ["ounce", "weight unit", "one-twelfth", "uncia", "measure"], "semantic_fields": ["number", "trade"], "core_meaning": "a unit of weight equal to one-sixteenth of a pound", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 175
    {"word": "insulin", "lang": "lat", "english_glosses": ["insulin", "pancreatic hormone", "blood sugar regulator", "island hormone", "insula"], "semantic_fields": ["body"], "core_meaning": "a hormone produced in the pancreas that regulates blood sugar", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 176
    {"word": "widow", "lang": "lat", "english_glosses": ["widow", "widowed woman", "bereaved wife", "woman without husband", "vidua"], "semantic_fields": ["family", "emotion"], "core_meaning": "a woman whose husband has died and who has not remarried", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 177
    {"word": "honour", "lang": "lat", "english_glosses": ["honour", "glory", "respect", "dignity", "reputation", "esteem"], "semantic_fields": ["emotion", "social"], "core_meaning": "high respect and great esteem; moral integrity", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 178
    {"word": "sour", "lang": "lat", "english_glosses": ["sour", "acidic", "tart", "fermented", "sharp taste", "acrid"], "semantic_fields": ["food", "body"], "core_meaning": "having an acidic taste; fermented; harsh in manner", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 179
    {"word": "banner", "lang": "lat", "english_glosses": ["banner", "flag", "standard", "ensign", "battle flag", "proclamation"], "semantic_fields": ["war", "social"], "core_meaning": "a flag or standard; a headline or slogan", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 180
    {"word": "scorpion", "lang": "lat", "english_glosses": ["scorpion", "stinging arachnid", "venomous creature", "scorpio", "siege weapon"], "semantic_fields": ["animal", "war", "nature"], "core_meaning": "a venomous arachnid with a curved stinging tail", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 181
    {"word": "person", "lang": "lat", "english_glosses": ["person", "individual", "human being", "persona", "mask", "character"], "semantic_fields": ["social", "body"], "core_meaning": "a human being; from Latin persona (mask, character)", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 182
    {"word": "hilarious", "lang": "lat", "english_glosses": ["hilarious", "very funny", "cheerful", "merry", "hilaris", "joyful"], "semantic_fields": ["emotion"], "core_meaning": "extremely amusing; very cheerful and merry", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 183
    {"word": "galaxy", "lang": "lat", "english_glosses": ["galaxy", "Milky Way", "galactic system", "milky circle", "stellar system"], "semantic_fields": ["nature", "food"], "core_meaning": "a system of millions of stars; the Milky Way (from Greek gala, milk)", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 184
    {"word": "murdoch", "lang": "lat", "english_glosses": ["Murdoch", "sea warrior", "mariner", "Celtic name", "sailor"], "semantic_fields": ["war", "nature", "social"], "core_meaning": "a Gaelic name meaning 'sea warrior' or 'mariner'", "arabic_cognate_gloss": None, "confidence": "moderate", "annotator": "claude", "batch": "layer2_batch1"},
    # 185
    {"word": "zephyr", "lang": "lat", "english_glosses": ["zephyr", "west wind", "gentle breeze", "light wind", "Zephyrus"], "semantic_fields": ["nature"], "core_meaning": "a soft gentle breeze; the west wind personified", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 186
    {"word": "toby", "lang": "lat", "english_glosses": ["Tobias", "God is good", "Hebrew name", "biblical figure", "goodness of God"], "semantic_fields": ["religion", "social"], "core_meaning": "a name derived from Hebrew Tobiah meaning 'God is good'", "arabic_cognate_gloss": None, "confidence": "moderate", "annotator": "claude", "batch": "layer2_batch1"},
    # 187
    {"word": "geber", "lang": "lat", "english_glosses": ["man", "strong man", "hero", "Jabir", "alchemist name", "warrior"], "semantic_fields": ["social", "war"], "core_meaning": "from Semitic root meaning 'man' or 'strong man'; name of the famous alchemist Jabir", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 188
    {"word": "cavalier", "lang": "lat", "english_glosses": ["cavalier", "horseman", "knight", "cavalryman", "caballarius", "mounted soldier"], "semantic_fields": ["war", "animal", "social"], "core_meaning": "a horseman or knight; a supporter of King Charles I", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 189
    {"word": "rage", "lang": "lat", "english_glosses": ["rage", "anger", "fury", "violent anger", "rabies", "madness"], "semantic_fields": ["emotion"], "core_meaning": "violent uncontrollable anger; from Latin rabies (madness)", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 190
    {"word": "honey", "lang": "lat", "english_glosses": ["honey", "sweet liquid", "nectar", "bee product", "mel", "sweetness"], "semantic_fields": ["food", "animal", "nature"], "core_meaning": "a sweet sticky substance made by bees from flower nectar", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 191
    {"word": "sum", "lang": "lat", "english_glosses": ["sum", "total", "amount", "summation", "add up", "the whole"], "semantic_fields": ["number", "trade"], "core_meaning": "the total amount resulting from addition; the whole", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 192
    {"word": "come", "lang": "lat", "english_glosses": ["come", "arrive", "approach", "move toward", "venire", "reach"], "semantic_fields": ["movement"], "core_meaning": "to move toward a place; to arrive", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 193
    {"word": "toffee", "lang": "lat", "english_glosses": ["toffee", "candy", "sweet", "confection", "sugar candy", "taffy"], "semantic_fields": ["food", "trade"], "core_meaning": "a hard sticky sweet made from sugar and butter", "arabic_cognate_gloss": None, "confidence": "moderate", "annotator": "claude", "batch": "layer2_batch1"},
    # 194
    {"word": "fungus", "lang": "lat", "english_glosses": ["fungus", "mushroom", "mold", "sponge", "fungal growth", "toadstool"], "semantic_fields": ["nature", "food"], "core_meaning": "a plant-like organism that includes mushrooms, molds, and yeasts", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 195
    {"word": "valley", "lang": "lat", "english_glosses": ["valley", "dale", "vale", "lowland between hills", "vallis"], "semantic_fields": ["nature"], "core_meaning": "a low area of land between hills or mountains", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 196
    {"word": "varnish", "lang": "lat", "english_glosses": ["varnish", "resin coating", "lacquer", "protective gloss", "polish"], "semantic_fields": ["trade", "tool"], "core_meaning": "a resinous liquid applied to wood or metal to give a hard shiny finish", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 197
    {"word": "wane", "lang": "lat", "english_glosses": ["wane", "decrease", "diminish", "fade", "moon shrinking", "decline"], "semantic_fields": ["nature", "movement"], "core_meaning": "to decrease in vigor or extent; the moon growing smaller", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 198
    {"word": "icon", "lang": "lat", "english_glosses": ["icon", "image", "religious picture", "symbol", "likeness", "eikon"], "semantic_fields": ["religion", "tool"], "core_meaning": "a painting of a sacred figure; a symbol or representation", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 199
    {"word": "fart", "lang": "lat", "english_glosses": ["fart", "flatulence", "intestinal gas", "break wind", "ventus"], "semantic_fields": ["body"], "core_meaning": "intestinal gas expelled through the anus", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 200
    {"word": "liter", "lang": "lat", "english_glosses": ["liter", "volume unit", "litre", "liquid measure", "one thousand millilitres"], "semantic_fields": ["number", "food"], "core_meaning": "a metric unit of volume equal to one cubic decimetre", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 201
    {"word": "autogenous", "lang": "lat", "english_glosses": ["autogenous", "self-produced", "self-generated", "indigenous", "spontaneous"], "semantic_fields": ["body", "nature"], "core_meaning": "produced by or from itself; self-generated", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 202
    {"word": "anesthesia", "lang": "lat", "english_glosses": ["anesthesia", "loss of sensation", "numbness", "insensibility", "pain relief"], "semantic_fields": ["body"], "core_meaning": "the loss of sensation, especially induced for medical procedures", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 203
    {"word": "apterous", "lang": "lat", "english_glosses": ["apterous", "wingless", "without wings", "flightless", "a-pterous"], "semantic_fields": ["animal", "nature", "body"], "core_meaning": "lacking wings; (of insects) wingless", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 204
    {"word": "cephalalgia", "lang": "lat", "english_glosses": ["headache", "head pain", "cephalalgia", "migraine", "cranial pain"], "semantic_fields": ["body"], "core_meaning": "pain in the head; a headache", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 205
    {"word": "cachinnate", "lang": "lat", "english_glosses": ["cachinnate", "laugh loudly", "guffaw", "roar with laughter", "cackle"], "semantic_fields": ["emotion", "body"], "core_meaning": "to laugh loudly and immoderately", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 206
    {"word": "mancinism", "lang": "lat", "english_glosses": ["left-handedness", "sinistral", "mancinism", "left-hand preference", "sinistrality"], "semantic_fields": ["body"], "core_meaning": "left-handedness; preference for using the left hand", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 207
    {"word": "semiology", "lang": "lat", "english_glosses": ["semiology", "study of signs", "sign science", "semiotics", "symptomology"], "semantic_fields": ["tool", "body"], "core_meaning": "the study of signs and symbols; the study of disease symptoms", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 208
    {"word": "emmet", "lang": "lat", "english_glosses": ["emmet", "ant", "formicant", "formica", "small insect"], "semantic_fields": ["animal", "nature"], "core_meaning": "an ant (archaic English); related to Old English aemette", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 209
    {"word": "thorn", "lang": "lat", "english_glosses": ["thorn", "spine", "prickle", "sharp point", "briar", "spina"], "semantic_fields": ["nature", "tool"], "core_meaning": "a sharp woody projection from a plant", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 210
    {"word": "heinous", "lang": "lat", "english_glosses": ["heinous", "wicked", "odious", "atrocious", "evil", "hateful"], "semantic_fields": ["emotion", "social"], "core_meaning": "utterly odious or wicked; morally criminal", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 211
    {"word": "anchovy", "lang": "lat", "english_glosses": ["anchovy", "small fish", "salted fish", "mediterranean fish", "engraulis"], "semantic_fields": ["animal", "food"], "core_meaning": "a small, common saltwater fish often used as a food", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 212
    {"word": "vert", "lang": "lat", "english_glosses": ["vert", "green", "verde", "heraldic green", "forest vegetation"], "semantic_fields": ["nature", "trade"], "core_meaning": "green; the heraldic term for the color green", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 213
    {"word": "buxema", "lang": "lat", "english_glosses": ["boxwood", "buxus", "box tree", "dense shrub", "evergreen wood"], "semantic_fields": ["nature", "tool"], "core_meaning": "possibly related to boxwood (buxus); a dense evergreen shrub", "arabic_cognate_gloss": None, "confidence": "uncertain", "annotator": "claude", "batch": "layer2_batch1"},
    # 214
    {"word": "linda", "lang": "lat", "english_glosses": ["beautiful", "pretty", "gentle", "soft", "serpent", "Germanic name"], "semantic_fields": ["emotion", "nature"], "core_meaning": "a name meaning beautiful or gentle; also relates to Germanic lind (soft, gentle)", "arabic_cognate_gloss": None, "confidence": "moderate", "annotator": "claude", "batch": "layer2_batch1"},
    # 215
    {"word": "nyla", "lang": "lat", "english_glosses": ["Nyla", "winner", "champion", "successful", "feminine name"], "semantic_fields": ["emotion", "social"], "core_meaning": "a name of uncertain origin, possibly meaning 'winner' or 'champion'", "arabic_cognate_gloss": None, "confidence": "uncertain", "annotator": "claude", "batch": "layer2_batch1"},
    # 216
    {"word": "pascal", "lang": "lat", "english_glosses": ["Pascal", "Easter", "Passover", "Easter lamb", "paschal"], "semantic_fields": ["religion"], "core_meaning": "a name derived from Latin paschalis relating to Easter or Passover", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 217
    {"word": "romeo", "lang": "lat", "english_glosses": ["Romeo", "Roman pilgrim", "pilgrimage to Rome", "lover", "romantic figure"], "semantic_fields": ["religion", "social"], "core_meaning": "a name meaning 'pilgrim to Rome'; Shakespeare's romantic hero", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 218
    {"word": "salome", "lang": "lat", "english_glosses": ["Salome", "peace", "shalom", "biblical dancer", "Hebrew name"], "semantic_fields": ["religion", "social", "emotion"], "core_meaning": "a Hebrew name meaning peace; the biblical figure who danced for Herod", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 219
    {"word": "zaccai", "lang": "lat", "english_glosses": ["Zaccai", "pure", "innocent", "clean", "biblical name", "righteous"], "semantic_fields": ["religion", "emotion"], "core_meaning": "a biblical name meaning pure or innocent", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 220
    {"word": "spiral", "lang": "lat", "english_glosses": ["spiral", "coil", "helix", "winding curve", "spira", "scroll"], "semantic_fields": ["nature", "tool"], "core_meaning": "a curve that winds around a point in an ever-increasing radius", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 221
    {"word": "trophic", "lang": "lat", "english_glosses": ["trophic", "nutritional", "feeding", "nourishment", "relating to food"], "semantic_fields": ["food", "body", "nature"], "core_meaning": "relating to feeding or nutrition; relating to food chains in ecology", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 222
    {"word": "celebrate", "lang": "lat", "english_glosses": ["celebrate", "honor", "observe festivity", "commemorate", "frequent", "praise"], "semantic_fields": ["religion", "emotion", "social"], "core_meaning": "to observe a day or event with ceremonies; to honor with praise", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 223
    {"word": "etiology", "lang": "lat", "english_glosses": ["etiology", "cause study", "origin of disease", "causation science", "aetiology"], "semantic_fields": ["body", "tool"], "core_meaning": "the study of causes or origins, especially of diseases", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 224
    {"word": "gelatine", "lang": "lat", "english_glosses": ["gelatine", "gelatin", "jelly", "collagen extract", "thickening agent", "gelled substance"], "semantic_fields": ["food", "tool"], "core_meaning": "a protein substance derived from animal collagen, used as a thickener", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 225
    {"word": "granulate", "lang": "lat", "english_glosses": ["granulate", "form granules", "divide into grains", "granular", "particle formation"], "semantic_fields": ["food", "tool", "nature"], "core_meaning": "to form into grains or granules; to make grainy", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 226
    {"word": "mime", "lang": "lat", "english_glosses": ["mime", "mimic", "actor", "silent actor", "imitate", "gesticulate"], "semantic_fields": ["social", "movement"], "core_meaning": "a form of theatrical performance using gesture and movement without words", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 227
    {"word": "omni", "lang": "lat", "english_glosses": ["omni", "all", "every", "universal", "total", "complete"], "semantic_fields": ["number"], "core_meaning": "a Latin prefix meaning all, every, or universal", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 228
    {"word": "treacle", "lang": "lat", "english_glosses": ["treacle", "molasses", "antidote", "syrup", "theriac", "healing medicine"], "semantic_fields": ["food", "body"], "core_meaning": "a thick sticky dark liquid; historically an antidote to poison", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 229
    {"word": "trim", "lang": "lat", "english_glosses": ["trim", "cut", "neaten", "decorate", "arrange", "neat condition"], "semantic_fields": ["tool", "body"], "core_meaning": "to cut away irregular parts; to make neat or tidy", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 230
    {"word": "vinegar", "lang": "lat", "english_glosses": ["vinegar", "sour wine", "vinum acre", "acetic acid", "condiment"], "semantic_fields": ["food", "trade"], "core_meaning": "a sour liquid made from fermented wine, used in cooking", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 231
    {"word": "grace", "lang": "lat", "english_glosses": ["grace", "elegance", "divine favor", "gratia", "charm", "mercy"], "semantic_fields": ["religion", "emotion", "social"], "core_meaning": "elegance and beauty; the favor and love of God; charm", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 232
    {"word": "archive", "lang": "lat", "english_glosses": ["archive", "records store", "document repository", "public records", "official papers"], "semantic_fields": ["building", "trade"], "core_meaning": "a collection of historical records or the place where they are kept", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 233
    {"word": "client", "lang": "lat", "english_glosses": ["client", "customer", "patron's dependent", "cliens", "follower", "dependent person"], "semantic_fields": ["social", "trade"], "core_meaning": "a person using the services of a professional; a Roman patron's dependent", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 234
    {"word": "caminus", "lang": "lat", "english_glosses": ["fireplace", "furnace", "chimney", "hearth", "oven", "forge"], "semantic_fields": ["building", "food", "tool"], "core_meaning": "a Latin word for fireplace, furnace, or chimney", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 235
    {"word": "chimney", "lang": "lat", "english_glosses": ["chimney", "flue", "smoke duct", "furnace", "hearth passage", "caminus"], "semantic_fields": ["building"], "core_meaning": "a vertical channel in a building for smoke to escape from a fireplace", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 236
    {"word": "test", "lang": "lat", "english_glosses": ["test", "trial", "examination", "testa", "earthen vessel", "crucible", "assay"], "semantic_fields": ["tool", "trade"], "core_meaning": "a procedure to determine quality or ability; Latin testa (earthenware pot for assaying metal)", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 237
    {"word": "tautology", "lang": "lat", "english_glosses": ["tautology", "repetition", "redundancy", "saying the same thing twice", "circular reasoning"], "semantic_fields": ["tool", "emotion"], "core_meaning": "the saying of the same thing twice in different words; needless repetition", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 238
    {"word": "angle", "lang": "lat", "english_glosses": ["angle", "corner", "geometric angle", "angulus", "hook", "fish"], "semantic_fields": ["number", "nature", "tool"], "core_meaning": "a corner; the space between two lines meeting at a point; to fish with a hook", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 239
    {"word": "crust", "lang": "lat", "english_glosses": ["crust", "outer shell", "hard covering", "rind", "crusta", "bread crust"], "semantic_fields": ["food", "nature", "body"], "core_meaning": "the hard outer layer of bread or a pie; any hard outer coating", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 240
    {"word": "leopard", "lang": "lat", "english_glosses": ["leopard", "large spotted cat", "leopardus", "lion-panther", "spotted predator"], "semantic_fields": ["animal", "nature"], "core_meaning": "a large African and Asian spotted wild cat", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 241
    {"word": "leech", "lang": "lat", "english_glosses": ["leech", "bloodsucker", "annelid worm", "doctor", "healer", "parasite"], "semantic_fields": ["animal", "body", "nature"], "core_meaning": "a blood-sucking worm; archaic term for a physician", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 242
    {"word": "visitor", "lang": "lat", "english_glosses": ["visitor", "guest", "one who visits", "caller", "visitator", "inspector"], "semantic_fields": ["social", "movement"], "core_meaning": "a person who visits a place", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 243
    {"word": "dam", "lang": "lat", "english_glosses": ["dam", "barrier", "flood barrier", "water barrier", "mother animal", "obstruction"], "semantic_fields": ["building", "nature", "animal"], "core_meaning": "a barrier built across a river to hold back water; mother of an animal", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
    # 244
    {"word": "alkanet", "lang": "lat", "english_glosses": ["alkanet", "red dye plant", "anchusa", "borage family herb", "henna-like plant"], "semantic_fields": ["nature", "trade"], "core_meaning": "a plant of the borage family yielding a red dye; related to Arabic al-hinna", "arabic_cognate_gloss": None, "confidence": "high", "annotator": "claude", "batch": "layer2_batch1"},
]


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_path = os.path.join(base_dir, "data", "llm_annotations", "layer2_semantic_mapping.jsonl")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        for entry in ANNOTATIONS:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Written {len(ANNOTATIONS)} annotations to {out_path}")

    # Validation
    with open(out_path, encoding="utf-8") as f:
        count = sum(1 for _ in f)
    print(f"Layer 2 annotations: {count}")

    # Basic sanity checks
    required_keys = {"word", "lang", "english_glosses", "semantic_fields", "core_meaning",
                     "arabic_cognate_gloss", "confidence", "annotator", "batch"}
    errors = []
    with open(out_path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            d = json.loads(line)
            missing = required_keys - set(d.keys())
            if missing:
                errors.append(f"Line {i} ({d.get('word')}): missing keys {missing}")
            if not isinstance(d.get("english_glosses"), list) or len(d["english_glosses"]) < 2:
                errors.append(f"Line {i} ({d.get('word')}): english_glosses must be list with >=2 entries")
            if d.get("arabic_cognate_gloss") is not None:
                errors.append(f"Line {i} ({d.get('word')}): arabic_cognate_gloss must be null")

    if errors:
        print(f"\nVALIDATION ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
    else:
        print("All validation checks passed.")


if __name__ == "__main__":
    main()
