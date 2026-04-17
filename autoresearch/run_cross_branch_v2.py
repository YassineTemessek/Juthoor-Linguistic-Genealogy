"""Cross-branch analysis across all 7 languages (post-Wave 2)."""
import json, sys, os
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LV2 = os.path.join(ROOT, "Juthoor-CognateDiscovery-LV2")

BRANCH = {
    "grc": "Hellenic", "lat": "Italic",
    "got": "Germanic-East", "ang": "Germanic-West", "non": "North-Germanic",
    "sga": "Celtic-Goidelic", "cy": "Celtic-Brythonic",
}

all_findings = []

# Greek + Latin reinvestigation
with open(os.path.join(ROOT, "autoresearch/grc_lat_reinvestigation.json"), encoding="utf-8") as f:
    for r in json.load(f):
        if r.get("verdict") in ("confirmed_cognate", "plausible_link"):
            all_findings.append({
                "lang": r.get("lang", "grc"),
                "arabic_root": r.get("arabic_root", ""),
                "target": r.get("target_lemma", ""),
                "verdict": r.get("verdict", ""),
                "confidence": r.get("confidence", ""),
            })

# Wave 1
with open(os.path.join(ROOT, "autoresearch/wave1_reinvestigation.json"), encoding="utf-8") as f:
    for r in json.load(f):
        if r.get("verdict") == "confirmed":
            all_findings.append({
                "lang": r.get("lang", "got"),
                "arabic_root": r.get("arabic_root", ""),
                "target": r.get("target_lemma", ""),
                "verdict": "confirmed_cognate",
                "confidence": "high",
            })

# Wave 2
for lang in ["non", "cy"]:
    path = os.path.join(LV2, f"outputs/eye2_final_{lang}.jsonl")
    if not os.path.exists(path):
        continue
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("verdict") in ("confirmed_cognate", "plausible_link"):
                all_findings.append({
                    "lang": lang,
                    "arabic_root": r.get("source_lemma", ""),
                    "target": r.get("target_lemma", ""),
                    "verdict": r.get("verdict", ""),
                    "confidence": r.get("confidence", ""),
                })

print(f"Total confirmed + plausible findings: {len(all_findings)}")

# By language
by_lang = defaultdict(lambda: {"confirmed_cognate": 0, "plausible_link": 0})
for f in all_findings:
    by_lang[f["lang"]][f["verdict"]] += 1

print("\nBy language:")
for lang in sorted(by_lang):
    cf = by_lang[lang]["confirmed_cognate"]
    pl = by_lang[lang]["plausible_link"]
    print(f"  {lang} ({BRANCH.get(lang,'?')}): {cf} confirmed + {pl} plausible = {cf+pl}")

# Cross-branch
by_root = defaultdict(list)
for f in all_findings:
    if f["arabic_root"]:
        by_root[f["arabic_root"]].append(f)

cross_branch = []
for root, hits in by_root.items():
    branches = set(BRANCH.get(h["lang"], h["lang"]) for h in hits)
    if len(branches) >= 2:
        cross_branch.append({
            "arabic_root": root,
            "branches": sorted(branches),
            "n_branches": len(branches),
            "hits": [(h["lang"], h["target"], h["verdict"]) for h in hits],
        })

cross_branch.sort(key=lambda x: -x["n_branches"])
print(f"\nCross-branch roots (2+ branches): {len(cross_branch)}")
print("\nTop 20:")
for cb in cross_branch[:20]:
    print(f"  {cb['arabic_root']} [{cb['n_branches']} branches]: {','.join(cb['branches'])}")
    for lang, tgt, v in cb["hits"][:4]:
        print(f"    -> {lang}:{tgt} ({v})")

# Save
out = os.path.join(ROOT, "autoresearch/cross_branch_analysis_v2.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump({
        "total_findings": len(all_findings),
        "by_language": {k: dict(v) for k, v in by_lang.items()},
        "cross_branch_roots": cross_branch,
    }, f, ensure_ascii=False, indent=2)

print(f"\nSaved to {out}")
