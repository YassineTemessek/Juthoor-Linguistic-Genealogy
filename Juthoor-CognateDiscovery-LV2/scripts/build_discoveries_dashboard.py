"""Build the Juthoor LV2 Discoveries Dashboard — detective-mode findings.

Data sources (in priority order):
  1. autoresearch/grc_lat_reinvestigation.json  — 907 Greek/Latin pairs reinvestigated
  2. autoresearch/wave1_reinvestigation.json     — 137 got/ang/sga pairs reinvestigated
  3. autoresearch/confirmed_cognates_analysis.json — 135 confirmed cognates (cross-branch)
  4. outputs/eye2_results/non/                  — Old Norse pilot batch findings
     (pair metadata: outputs/eye2_agent_batches/non/)
  5. Legacy: eye2_final_*.jsonl                 — old score-based records (backwards compat)
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LV2  = ROOT / "Juthoor-CognateDiscovery-LV2"
AUTORESEARCH = ROOT / "autoresearch"

# ── Language metadata ──────────────────────────────────────────────────────────

BRANCH_MAP = {
    "grc": "Hellenic",
    "lat": "Italic",
    "got": "Germanic-East",
    "ang": "Germanic-West",
    "sga": "Celtic",
    "non": "North-Germanic",
    "eng": "Germanic-West",
    "deu": "Germanic-West",
    "fra": "Italic",
    "spa": "Italic",
    "ita": "Italic",
    "fa":  "Indo-Iranian",
    "syc": "Semitic",
}

LANG_LABEL = {
    "grc": "Ancient Greek",
    "lat": "Latin",
    "got": "Gothic",
    "ang": "Old English",
    "sga": "Old Irish",
    "non": "Old Norse",
    "eng": "English",
    "deu": "German",
    "fra": "French",
    "spa": "Spanish",
    "ita": "Italian",
    "fa":  "Persian",
    "syc": "Syriac",
}


# ── Data loading ───────────────────────────────────────────────────────────────

def load_non_meta() -> dict:
    """Build pair_id -> {arabic_root, target_lemma} from NON agent-batch metadata."""
    meta_dir = LV2 / "outputs" / "eye2_agent_batches" / "non"
    if not meta_dir.exists():
        print("[warn] NON meta dir not found:", meta_dir, file=sys.stderr)
        return {}
    lookup: dict = {}
    for fp in sorted(meta_dir.glob("*_meta.json")):
        with open(fp, encoding="utf-8") as fh:
            records = json.load(fh)
        for r in records:
            pid = r.get("pair_id", "")
            if pid:
                lookup[pid] = {
                    "arabic_root":  r.get("arabic_root", ""),
                    "target_lemma": r.get("target_lemma", ""),
                }
    print(f"[non] Meta lookup: {len(lookup):,} pair IDs", file=sys.stderr)
    return lookup


def load_grc_lat_reinvestigation() -> list:
    """Load grc_lat_reinvestigation.json — 907 pairs."""
    path = AUTORESEARCH / "grc_lat_reinvestigation.json"
    if not path.exists():
        print("[warn] grc_lat_reinvestigation.json not found", file=sys.stderr)
        return []
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    records = []
    for r in data:
        lang = r.get("lang", "grc")
        records.append({
            "lang":            lang,
            "branch":          BRANCH_MAP.get(lang, "Unknown"),
            "arabic_root":     r.get("arabic_root", ""),
            "target_lemma":    r.get("target_lemma", ""),
            "verdict":         r.get("verdict", ""),
            "confidence":      r.get("confidence", ""),
            "journey_type":    r.get("journey_type", ""),
            "semantic_journey": r.get("semantic_journey", ""),
            "key_insight":     r.get("key_insight", ""),
            "original_score":  r.get("original_score", 0.0),
            "original_method": r.get("original_method", ""),
            "source":          "grc_lat_reinvestigation",
        })
    print(f"[grc_lat] Loaded {len(records):,} reinvestigation records", file=sys.stderr)
    return records


def load_wave1_reinvestigation() -> list:
    """Load wave1_reinvestigation.json — 137 got/ang/sga pairs."""
    path = AUTORESEARCH / "wave1_reinvestigation.json"
    if not path.exists():
        print("[warn] wave1_reinvestigation.json not found", file=sys.stderr)
        return []
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    records = []
    for r in data:
        lang = r.get("lang", "got")
        records.append({
            "lang":            lang,
            "branch":          BRANCH_MAP.get(lang, "Unknown"),
            "arabic_root":     r.get("arabic_root", ""),
            "target_lemma":    r.get("target_lemma", ""),
            "verdict":         r.get("verdict", ""),
            "confidence":      r.get("confidence", ""),
            "journey_type":    r.get("journey_type", ""),
            "semantic_journey": r.get("semantic_journey", ""),
            "key_insight":     r.get("key_insight", ""),
            "original_score":  r.get("original_score", 0.0),
            "original_method": "",
            "source":          "wave1_reinvestigation",
        })
    print(f"[wave1] Loaded {len(records):,} reinvestigation records", file=sys.stderr)
    return records


def load_non_pilot(non_meta: dict) -> list:
    """Load Old Norse Eye 2 pilot batch findings, merging with metadata."""
    results_dir = LV2 / "outputs" / "eye2_results" / "non"
    if not results_dir.exists():
        print("[warn] NON results dir not found:", results_dir, file=sys.stderr)
        return []
    records = []
    for fp in sorted(results_dir.glob("batch_*.json")):
        with open(fp, encoding="utf-8") as fh:
            batch = json.load(fh)
        for r in batch:
            pid = r.get("pair_id", "")
            meta = non_meta.get(pid, {})
            ar   = meta.get("arabic_root", "")
            tgt  = meta.get("target_lemma", "")
            if not ar or not tgt:
                continue  # skip if we can't identify the pair
            records.append({
                "lang":            "non",
                "branch":          "North-Germanic",
                "arabic_root":     ar,
                "target_lemma":    tgt,
                "verdict":         r.get("verdict", ""),
                "confidence":      r.get("confidence", ""),
                "journey_type":    r.get("journey_type", ""),
                "semantic_journey": r.get("semantic_journey", ""),
                "key_insight":     r.get("key_insight", ""),
                "original_score":  0.0,
                "original_method": "",
                "source":          "non_pilot",
            })
    print(f"[non] Loaded {len(records):,} pilot records", file=sys.stderr)
    return records


def load_confirmed_analysis() -> dict:
    """Load confirmed_cognates_analysis.json for cross-branch cognate set."""
    path = AUTORESEARCH / "confirmed_cognates_analysis.json"
    if not path.exists():
        print("[warn] confirmed_cognates_analysis.json not found", file=sys.stderr)
        return {"cross_branch_roots": [], "all_confirmed": []}
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data


def load_legacy_records() -> list:
    """Load old eye2_final_*.jsonl files as legacy records (backwards compat)."""
    legacy = []
    for lang, fname in [("grc", "eye2_final_grc.jsonl"),
                        ("lat", "eye2_final_lat.jsonl"),
                        ("got", "eye2_final_got.jsonl"),
                        ("ang", "eye2_final_ang.jsonl"),
                        ("sga", "eye2_final_sga.jsonl")]:
        path = LV2 / "outputs" / fname
        if not path.exists():
            continue
        count = 0
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                r = json.loads(line)
                score = r.get("semantic_score", 0)
                if score < 0.5:
                    continue
                legacy.append({
                    "lang":            lang,
                    "branch":          BRANCH_MAP.get(lang, "Unknown"),
                    "arabic_root":     r.get("source_lemma", ""),
                    "target_lemma":    r.get("target_lemma", ""),
                    "verdict":         "legacy_scored",
                    "confidence":      "medium" if score >= 0.8 else "low",
                    "journey_type":    r.get("method", "unknown"),
                    "semantic_journey": r.get("reasoning", ""),
                    "key_insight":     r.get("reasoning", "")[:120],
                    "original_score":  round(score, 3),
                    "original_method": r.get("method", ""),
                    "source":          "legacy_eye2",
                })
                count += 1
        print(f"[legacy] {count} records from {fname}", file=sys.stderr)
    return legacy


def merge_records(all_records: list, cross_branch_roots: list) -> list:
    """Deduplicate by (arabic_root, target_lemma) — prefer detective findings over legacy.
    Then annotate cross-branch cognates."""
    source_priority = {
        "grc_lat_reinvestigation": 0,
        "wave1_reinvestigation":   1,
        "non_pilot":               2,
        "legacy_eye2":             3,
    }
    best: dict = {}
    for r in all_records:
        key = (r["arabic_root"].strip(), r["target_lemma"].strip())
        if not key[0] or not key[1]:
            continue
        existing = best.get(key)
        if existing is None:
            best[key] = r
        else:
            # prefer lower source priority number (detective > legacy)
            if source_priority.get(r["source"], 99) < source_priority.get(existing["source"], 99):
                best[key] = r

    # Build cross-branch set for annotation
    cross_branch_ar = {r["arabic_root"] for r in cross_branch_roots}

    records = []
    for r in best.values():
        r = dict(r)
        r["cross_branch"] = r["arabic_root"] in cross_branch_ar
        records.append(r)

    # Sort: confirmed first, then by confidence, then alphabetically
    verdict_order = {
        "confirmed_cognate": 0,
        "confirmed":         0,
        "plausible_link":    1,
        "shared_loanword":   2,
        "proper_name":       3,
        "false_positive":    4,
        "legacy_scored":     5,
    }
    confidence_order = {"high": 0, "medium": 1, "low": 2}
    records.sort(key=lambda r: (
        verdict_order.get(r["verdict"], 9),
        confidence_order.get(r["confidence"], 9),
        r["arabic_root"],
    ))
    return records


def print_summary(records: list):
    """Print a summary of the merged records."""
    print(f"\nTotal unique pairs: {len(records):,}", file=sys.stderr)
    verdicts = Counter(r["verdict"] for r in records)
    print("\nBy verdict:", file=sys.stderr)
    for v, cnt in verdicts.most_common():
        print(f"  {v}: {cnt}", file=sys.stderr)

    langs = Counter(r["lang"] for r in records)
    print("\nBy language:", file=sys.stderr)
    for lang, cnt in langs.most_common():
        confirmed = sum(1 for r in records
                        if r["lang"] == lang
                        and r["verdict"] in ("confirmed_cognate", "confirmed"))
        print(f"  {lang} ({LANG_LABEL.get(lang, lang)}): {cnt} total, "
              f"{confirmed} confirmed", file=sys.stderr)

    jtypes = Counter(r["journey_type"] for r in records
                     if r["verdict"] in ("confirmed_cognate", "confirmed"))
    print("\nConfirmed by journey type:", file=sys.stderr)
    for jt, cnt in jtypes.most_common():
        print(f"  {jt}: {cnt}", file=sys.stderr)


# ── HTML template ──────────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" dir="ltr" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Juthoor Codex &mdash; Detective Findings</title>
<style>
/* ── CSS custom properties / themes ── */
:root, [data-theme="light"] {
  --bg:               #f7f4ef;
  --bg-alt:           #faf7f2;
  --bg-panel:         #f0ebe3;
  --text:             #2c2420;
  --text-muted:       #8a7e72;
  --border:           #e8e0d4;
  --card-bg:          #ffffff;
  --card-shadow:      0 2px 8px rgba(120,80,20,0.06), 0 1px 2px rgba(120,80,20,0.04);
  --card-shadow-hover:0 6px 18px rgba(120,80,20,0.10), 0 2px 4px rgba(120,80,20,0.06);
  --header-bg:        #1a3d34;
  --header-grad:      linear-gradient(135deg, #1a3d34 0%, #1e4a3e 50%, #1a3d34 100%);
  --header-text:      #ffffff;
  --accent:           #b8860b;
  --accent-teal:      #1a3d34;
  --chip-bg:          #f0ebe3;
  --chip-text:        #1a3d34;
  --chip-border:      #1a3d34;
  --chip-active-bg:   #1a3d34;
  --chip-active-text: #ffffff;
  --input-bg:         #ffffff;
  --input-border:     #e8e0d4;
  --input-shadow:     inset 0 1px 3px rgba(44,36,32,0.06);
  --table-hover:      rgba(26,61,52,0.04);
  --verdict-confirmed-bg:   #d4edda; --verdict-confirmed-text:  #1e7a46;
  --verdict-plausible-bg:   #fef3c7; --verdict-plausible-text:  #b8860b;
  --verdict-loanword-bg:    #e8f0fe; --verdict-loanword-text:   #3b5bdb;
  --verdict-proper-bg:      #f3e8ff; --verdict-proper-text:     #6b21a8;
  --verdict-false-bg:       #f5f5f5; --verdict-false-text:      #6b7280;
  --verdict-legacy-bg:      #fff7ed; --verdict-legacy-text:     #c2410c;
  --conf-high-color:        #1e7a46;
  --conf-medium-color:      #b8860b;
  --conf-low-color:         #8a7e72;
  --cross-branch-bg:        #fef3c7;
  --cross-branch-border:    #d97706;
  --detail-bg:              #f7f4ef;
  --detail-border:          #b8860b;
  --journey-bg:             #f9f7f4;
  --journey-border:         #e8e0d4;
}
[data-theme="warm"] {
  --bg:               #f2e8d5;
  --bg-alt:           #f7eedc;
  --bg-panel:         #e8d9be;
  --text:             #2e1f10;
  --text-muted:       #7a6040;
  --border:           #d4be96;
  --card-bg:          #fdf5e4;
  --card-shadow:      0 2px 8px rgba(100,60,0,0.08), 0 1px 2px rgba(100,60,0,0.05);
  --card-shadow-hover:0 6px 18px rgba(100,60,0,0.14), 0 2px 4px rgba(100,60,0,0.08);
  --header-bg:        #1a3d34;
  --header-grad:      linear-gradient(135deg, #1a3d34 0%, #1e4a3e 50%, #1a3d34 100%);
  --header-text:      #ffffff;
  --accent:           #c49010;
  --accent-teal:      #1a3d34;
  --chip-bg:          #e8d9be;
  --chip-text:        #1a3d34;
  --chip-border:      #1a3d34;
  --chip-active-bg:   #1a3d34;
  --chip-active-text: #f2e8d5;
  --input-bg:         #fdf5e4;
  --input-border:     #c8a870;
  --input-shadow:     inset 0 1px 3px rgba(60,30,0,0.08);
  --table-hover:      rgba(26,61,52,0.06);
  --verdict-confirmed-bg:   #c8e6c9; --verdict-confirmed-text:  #1b5e20;
  --verdict-plausible-bg:   #fde8a0; --verdict-plausible-text:  #92600a;
  --verdict-loanword-bg:    #dce8fc; --verdict-loanword-text:   #2d4ab8;
  --verdict-proper-bg:      #ead6f5; --verdict-proper-text:     #5b1a8f;
  --verdict-false-bg:       #e8e0d4; --verdict-false-text:      #5a5040;
  --verdict-legacy-bg:      #fde8cc; --verdict-legacy-text:     #a03010;
  --conf-high-color:        #1b5e20;
  --conf-medium-color:      #92600a;
  --conf-low-color:         #7a6040;
  --cross-branch-bg:        #fde8a0;
  --cross-branch-border:    #b07010;
  --detail-bg:              #f2e8d5;
  --detail-border:          #c49010;
  --journey-bg:             #f7f0e0;
  --journey-border:         #d4be96;
}
[data-theme="dark"] {
  --bg:               #1a1a24;
  --bg-alt:           #1f1f2c;
  --bg-panel:         #242430;
  --text:             #d4cec4;
  --text-muted:       #7a7870;
  --border:           #36363e;
  --card-bg:          #242430;
  --card-shadow:      0 2px 8px rgba(0,0,0,0.30), 0 1px 2px rgba(0,0,0,0.20);
  --card-shadow-hover:0 6px 18px rgba(0,0,0,0.50), 0 2px 6px rgba(0,0,0,0.30);
  --header-bg:        #0d1f1a;
  --header-grad:      linear-gradient(135deg, #0d1f1a 0%, #112820 50%, #0d1f1a 100%);
  --header-text:      #e0d8cc;
  --accent:           #d4a438;
  --accent-teal:      #2a8060;
  --chip-bg:          #2e2e3a;
  --chip-text:        #2a8060;
  --chip-border:      #2a8060;
  --chip-active-bg:   #2a8060;
  --chip-active-text: #ffffff;
  --input-bg:         #242430;
  --input-border:     #36363e;
  --input-shadow:     inset 0 1px 3px rgba(0,0,0,0.30);
  --table-hover:      rgba(42,128,96,0.08);
  --verdict-confirmed-bg:   #1a3a22; --verdict-confirmed-text:  #4cc870;
  --verdict-plausible-bg:   #2e2010; --verdict-plausible-text:  #d4a438;
  --verdict-loanword-bg:    #1a2040; --verdict-loanword-text:   #7090e8;
  --verdict-proper-bg:      #2a1840; --verdict-proper-text:     #c080f0;
  --verdict-false-bg:       #2e2e3a; --verdict-false-text:      #7a7870;
  --verdict-legacy-bg:      #2a1808; --verdict-legacy-text:     #e08040;
  --conf-high-color:        #4cc870;
  --conf-medium-color:      #d4a438;
  --conf-low-color:         #7a7870;
  --cross-branch-bg:        #2e2010;
  --cross-branch-border:    #d4a438;
  --detail-bg:              #1f1f2c;
  --detail-border:          #d4a438;
  --journey-bg:             #1a1a24;
  --journey-border:         #36363e;
}

/* ── Reset ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  transition: background 0.25s, color 0.25s;
  font-size: 15px;
  line-height: 1.5;
}

/* ── Header ── */
header {
  background: var(--header-grad);
  border-bottom: 3px solid var(--accent);
  padding: 1.5rem 2rem;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.header-left h1 {
  font-family: Georgia, 'Palatino Linotype', 'Book Antiqua', Palatino, serif;
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--header-text);
  letter-spacing: 0.01em;
  line-height: 1.2;
}
.header-left p {
  font-size: 0.82rem;
  color: rgba(255,255,255,0.65);
  margin-top: 0.35rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 400;
}
.theme-switcher {
  display: flex;
  gap: 0.3rem;
  margin-top: 0.25rem;
}
.theme-btn {
  background: rgba(255,255,255,0.10);
  border: 1px solid rgba(255,255,255,0.22);
  color: rgba(255,255,255,0.70);
  padding: 0.28rem 0.7rem;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.72rem;
  font-weight: 500;
  letter-spacing: 0.04em;
  transition: background 0.15s, color 0.15s;
}
.theme-btn:hover { background: rgba(255,255,255,0.18); color: #fff; }
.theme-btn.active {
  background: rgba(255,255,255,0.22);
  border-color: rgba(255,255,255,0.55);
  color: #fff;
  font-weight: 600;
}

/* ── Stats bar ── */
#stats-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 1.25rem 2rem;
  background: var(--bg);
  border-bottom: 1px solid var(--border);
}
.stat-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-top: 3px solid var(--accent);
  box-shadow: var(--card-shadow);
  border-radius: 6px;
  padding: 0.75rem 1.25rem;
  min-width: 100px;
  text-align: center;
  flex: 1 1 100px;
  max-width: 160px;
  cursor: default;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: var(--card-shadow-hover); }
.stat-label {
  font-size: 0.68rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.09em;
  font-weight: 600;
}
.stat-value {
  font-family: Georgia, 'Palatino Linotype', Palatino, serif;
  font-size: 2.2rem;
  font-weight: 700;
  margin-top: 0.1rem;
  line-height: 1.1;
  color: var(--accent);
}
.stat-confirmed .stat-value { color: var(--verdict-confirmed-text); }
.stat-plausible .stat-value { color: var(--verdict-plausible-text); }
.stat-cross     .stat-value { color: var(--cross-branch-border); }
.stat-hellenic  .stat-value { color: #1a3d34; }
.stat-italic    .stat-value { color: #c2524a; }
.stat-germanic  .stat-value { color: #6b3fa0; }
.stat-celtic    .stat-value { color: #2d6a2d; }

/* ── Filter chips ── */
#chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  padding: 0.85rem 2rem;
  background: var(--bg);
  border-bottom: 1px solid var(--border);
  align-items: center;
}
.chip-section-label {
  font-size: 0.68rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.09em;
  font-weight: 600;
  margin-right: 0.2rem;
  white-space: nowrap;
}
.chip-divider {
  width: 1px;
  height: 20px;
  background: var(--border);
  margin: 0 0.4rem;
}
.chip {
  background: transparent;
  color: var(--chip-text);
  border: 1.5px solid var(--chip-border);
  padding: 0.28rem 0.85rem;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 500;
  transition: background 0.15s, color 0.15s;
  user-select: none;
}
.chip:hover { background: rgba(26,61,52,0.06); }
.chip.active {
  background: var(--chip-active-bg);
  color: var(--chip-active-text);
  border-color: var(--chip-active-bg);
}

/* ── Filter bar ── */
#filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1.25rem;
  padding: 0.85rem 2rem;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border);
}
.filter-group { display: flex; align-items: center; gap: 0.5rem; }
.filter-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  white-space: nowrap;
  font-weight: 500;
  letter-spacing: 0.03em;
}
select, #search-input {
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  box-shadow: var(--input-shadow);
  color: var(--text);
  padding: 0.32rem 0.65rem;
  border-radius: 6px;
  font-size: 0.82rem;
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s;
}
select:focus, #search-input:focus { border-color: var(--accent-teal); }
#search-input { width: 220px; }
#search-input::placeholder { color: var(--text-muted); opacity: 0.6; }

/* ── Chart ── */
#chart-section {
  padding: 1rem 2rem;
  background: var(--bg);
  border-bottom: 1px solid var(--border);
}
#chart-section h3 {
  font-size: 0.68rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.09em;
  margin-bottom: 0.7rem;
  font-weight: 600;
}
.chart-row {
  display: flex;
  align-items: center;
  margin-bottom: 0.28rem;
  gap: 0.6rem;
}
.chart-band-label {
  font-family: 'Cascadia Code', 'Consolas', 'Monaco', monospace;
  font-size: 0.68rem;
  color: var(--text-muted);
  width: 90px;
  text-align: right;
  flex-shrink: 0;
}
.chart-bars {
  display: flex;
  height: 12px;
  flex: 1;
  border-radius: 3px;
  overflow: hidden;
  background: var(--border);
}
.chart-bar-confirmed { background: var(--verdict-confirmed-text); height: 100%; transition: width 0.25s; }
.chart-bar-plausible { background: var(--verdict-plausible-text); height: 100%; transition: width 0.25s; }
.chart-bar-other     { background: var(--text-muted); height: 100%; transition: width 0.25s; }
.chart-count {
  font-family: 'Cascadia Code', 'Consolas', 'Monaco', monospace;
  font-size: 0.66rem;
  color: var(--text-muted);
  width: 46px;
  flex-shrink: 0;
}
.chart-legend {
  display: flex;
  gap: 1.2rem;
  margin-top: 0.6rem;
  font-size: 0.70rem;
  color: var(--text-muted);
}
.legend-dot {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 50%;
  margin-right: 4px;
  vertical-align: middle;
}

/* ── Table section ── */
#table-section { padding: 1.25rem 2rem 3rem; }
#pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}
#page-info { font-size: 0.80rem; color: var(--text-muted); font-style: italic; }
.page-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-muted);
  padding: 0.3rem 0.85rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.80rem;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.page-btn:hover:not(:disabled) {
  border-color: var(--accent-teal);
  color: var(--accent-teal);
  background: rgba(26,61,52,0.05);
}
.page-btn:disabled { opacity: 0.30; cursor: default; }
.page-btn-group { display: flex; gap: 0.4rem; align-items: center; }
.export-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-muted);
  padding: 0.3rem 0.85rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.76rem;
  font-weight: 500;
  transition: border-color 0.15s, color 0.15s;
}
.export-btn:hover { border-color: var(--accent); color: var(--accent); }

/* ── Data table ── */
#data-table { width: 100%; border-collapse: collapse; font-size: 0.83rem; }
#data-table th {
  background: transparent;
  color: var(--text-muted);
  font-weight: 600;
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  padding: 0.6rem 1rem;
  text-align: left;
  border-bottom: 2px solid var(--border);
  white-space: nowrap;
  user-select: none;
}
#data-table th.sortable { cursor: pointer; }
#data-table th.sortable:hover { color: var(--text); }
#data-table th.sort-asc::after  { content: " \25B2"; font-size: 0.58rem; }
#data-table th.sort-desc::after { content: " \25BC"; font-size: 0.58rem; }
#data-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}
#data-table tr:nth-child(even) > td { background: var(--bg-alt); }
#data-table tr.data-row:hover > td  { background: var(--table-hover); cursor: pointer; }
#data-table tr.detail-row > td {
  background: var(--detail-bg);
  border-left: 3px solid var(--detail-border);
  padding: 1rem 1.25rem;
}

/* ── Verdict badge ── */
.verdict-badge {
  display: inline-block;
  padding: 0.14rem 0.55rem;
  border-radius: 10px;
  font-size: 0.68rem;
  font-weight: 600;
  white-space: nowrap;
}
.verdict-confirmed { background: var(--verdict-confirmed-bg); color: var(--verdict-confirmed-text); }
.verdict-plausible { background: var(--verdict-plausible-bg); color: var(--verdict-plausible-text); }
.verdict-loanword  { background: var(--verdict-loanword-bg);  color: var(--verdict-loanword-text);  }
.verdict-proper    { background: var(--verdict-proper-bg);    color: var(--verdict-proper-text);    }
.verdict-false     { background: var(--verdict-false-bg);     color: var(--verdict-false-text);     }
.verdict-legacy    { background: var(--verdict-legacy-bg);    color: var(--verdict-legacy-text);    }

/* ── Confidence dot ── */
.conf-dot {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 50%;
  margin-right: 4px;
  vertical-align: middle;
}
.conf-high   { background: var(--conf-high-color);   }
.conf-medium { background: var(--conf-medium-color);  }
.conf-low    { background: var(--conf-low-color);     }

/* ── Cross-branch indicator ── */
.cross-branch-row > td:first-child {
  border-left: 3px solid var(--cross-branch-border);
}
.cross-tag {
  display: inline-block;
  font-size: 0.60rem;
  background: var(--cross-branch-bg);
  color: var(--cross-branch-border);
  border: 1px solid var(--cross-branch-border);
  border-radius: 3px;
  padding: 0.06rem 0.3rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  margin-left: 4px;
  vertical-align: middle;
}

/* ── Arabic text ── */
.ar-text {
  font-family: 'Simplified Arabic', 'Traditional Arabic', 'Noto Sans Arabic', serif;
  font-size: 1.15em;
  direction: rtl;
  unicode-bidi: bidi-override;
  color: var(--text);
  line-height: 1.6;
  display: block;
}

/* ── Target word ── */
.tgt-word {
  font-family: Georgia, 'Palatino Linotype', Palatino, serif;
  font-size: 0.92rem;
  font-style: italic;
  color: var(--text);
  font-weight: 400;
  display: block;
}

/* ── Lang badge ── */
.lang-badge {
  display: inline-block;
  padding: 0.12rem 0.45rem;
  border-radius: 4px;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  background: transparent;
  border-left: 2px solid currentColor;
}
.badge-grc { color: #1a3d34; }
.badge-lat { color: #c2524a; }
.badge-got { color: #6b3fa0; }
.badge-ang { color: #2d6a2d; }
.badge-sga { color: #8b5cf6; }
.badge-non { color: #0369a1; }
.badge-oth { color: #b8860b; }

/* ── Journey type badge ── */
.journey-badge {
  display: inline-block;
  padding: 0.10rem 0.45rem;
  border-radius: 10px;
  border: 1px solid currentColor;
  font-size: 0.63rem;
  font-weight: 500;
  white-space: nowrap;
  color: var(--text-muted);
  background: transparent;
}

/* ── Key insight cell ── */
.insight-cell {
  font-size: 0.75rem;
  color: var(--text-muted);
  max-width: 260px;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Detail panel ── */
.detail-panel {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  font-size: 0.82rem;
}
.detail-panel .dp-label {
  font-size: 0.64rem;
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  margin-bottom: 0.3rem;
}
.detail-panel .dp-value { color: var(--text); line-height: 1.6; }
.detail-journey { grid-column: 1 / -1; }
.journey-text {
  background: var(--journey-bg);
  border: 1px solid var(--journey-border);
  border-radius: 6px;
  padding: 0.85rem 1rem;
  line-height: 1.7;
  font-size: 0.83rem;
  color: var(--text);
  white-space: pre-wrap;
}

/* ── No results ── */
#no-results {
  text-align: center;
  padding: 4rem;
  color: var(--text-muted);
  font-size: 0.9rem;
  font-style: italic;
  display: none;
}

/* ── Export ── */
#export-section { display: flex; gap: 0.4rem; align-items: center; }

/* ── Responsive ── */
@media (max-width: 900px) {
  header, #stats-bar, #chip-row, #filter-bar, #chart-section, #table-section {
    padding-left: 1rem; padding-right: 1rem;
  }
  #data-table th:nth-child(6), #data-table td:nth-child(6),
  #data-table th:nth-child(7), #data-table td:nth-child(7) { display: none; }
  #search-input { width: 140px; }
  .stat-card { max-width: none; }
  .stat-value { font-size: 1.7rem; }
  .detail-panel { grid-template-columns: 1fr; }
}
</style>
</head>
<body>

<header>
  <div class="header-left">
    <h1>Juthoor Codex</h1>
    <p>Arabic cognate discoveries &mdash; detective-mode semantic journeys</p>
  </div>
  <div class="theme-switcher">
    <button class="theme-btn active" data-t="light"  onclick="setTheme('light')">Light</button>
    <button class="theme-btn"        data-t="warm"   onclick="setTheme('warm')">Warm</button>
    <button class="theme-btn"        data-t="dark"   onclick="setTheme('dark')">Dark</button>
  </div>
</header>

<div id="stats-bar">
  <div class="stat-card">
    <div class="stat-label">Total Pairs</div>
    <div class="stat-value" id="stat-total">&mdash;</div>
  </div>
  <div class="stat-card stat-confirmed">
    <div class="stat-label">Confirmed</div>
    <div class="stat-value" id="stat-confirmed">&mdash;</div>
  </div>
  <div class="stat-card stat-plausible">
    <div class="stat-label">Plausible</div>
    <div class="stat-value" id="stat-plausible">&mdash;</div>
  </div>
  <div class="stat-card stat-cross">
    <div class="stat-label">Cross-Branch</div>
    <div class="stat-value" id="stat-cross">&mdash;</div>
  </div>
  <div class="stat-card stat-hellenic">
    <div class="stat-label">Greek</div>
    <div class="stat-value" id="stat-grc">&mdash;</div>
  </div>
  <div class="stat-card stat-italic">
    <div class="stat-label">Latin</div>
    <div class="stat-value" id="stat-lat">&mdash;</div>
  </div>
  <div class="stat-card stat-germanic">
    <div class="stat-label">Germanic</div>
    <div class="stat-value" id="stat-gmc">&mdash;</div>
  </div>
  <div class="stat-card stat-celtic">
    <div class="stat-label">Celtic</div>
    <div class="stat-value" id="stat-cel">&mdash;</div>
  </div>
</div>

<div id="chip-row">
  <span class="chip-section-label">Verdict:</span>
  <button class="chip active" data-chip="confirmed" onclick="setChip(this)">Confirmed Only</button>
  <button class="chip"        data-chip="positive"  onclick="setChip(this)">All Positive</button>
  <button class="chip"        data-chip="all"        onclick="setChip(this)">All Verdicts</button>
  <div class="chip-divider"></div>
  <span class="chip-section-label">Branch:</span>
  <button class="chip" data-chip="Hellenic"       onclick="setChip(this)">Hellenic</button>
  <button class="chip" data-chip="Italic"         onclick="setChip(this)">Italic</button>
  <button class="chip" data-chip="Germanic-East"  onclick="setChip(this)">Gothic</button>
  <button class="chip" data-chip="Germanic-West"  onclick="setChip(this)">OE/German</button>
  <button class="chip" data-chip="Celtic"         onclick="setChip(this)">Celtic</button>
  <button class="chip" data-chip="North-Germanic" onclick="setChip(this)">Old Norse</button>
  <div class="chip-divider"></div>
  <button class="chip" data-chip="cross_branch"  onclick="setChip(this)">Cross-Branch</button>
</div>

<div id="filter-bar">
  <div class="filter-group">
    <label class="filter-label" for="journey-select">Journey Type:</label>
    <select id="journey-select" onchange="applyFilters()">
      <option value="">All types</option>
      <option value="direct_preservation">direct_preservation</option>
      <option value="material_culture">material_culture</option>
      <option value="semantic_drift">semantic_drift</option>
      <option value="specialization">specialization</option>
      <option value="generalization">generalization</option>
      <option value="metaphorical_extension">metaphorical_extension</option>
      <option value="negation_cognate">negation_cognate</option>
      <option value="mafahim_deep">mafahim_deep</option>
      <option value="no_connection">no_connection</option>
    </select>
  </div>
  <div class="filter-group">
    <label class="filter-label" for="conf-select">Confidence:</label>
    <select id="conf-select" onchange="applyFilters()">
      <option value="">All</option>
      <option value="high">High</option>
      <option value="medium">Medium</option>
      <option value="low">Low</option>
    </select>
  </div>
  <div class="filter-group">
    <label class="filter-label" for="search-input">Search:</label>
    <input type="text" id="search-input" placeholder="Arabic, target, journey..."
           oninput="applyFilters()">
  </div>
</div>

<div id="chart-section">
  <h3>Findings by Language Branch</h3>
  <div id="chart-container"></div>
  <div class="chart-legend">
    <span><span class="legend-dot" style="background:var(--verdict-confirmed-text)"></span>Confirmed</span>
    <span><span class="legend-dot" style="background:var(--verdict-plausible-text)"></span>Plausible</span>
    <span><span class="legend-dot" style="background:var(--text-muted)"></span>Other</span>
  </div>
</div>

<div id="table-section">
  <div id="pagination">
    <span id="page-info"></span>
    <div style="display:flex;gap:0.75rem;align-items:center;flex-wrap:wrap;">
      <div id="export-section">
        <button class="export-btn" onclick="exportCSV()">&#8595; CSV</button>
        <button class="export-btn" onclick="exportJSON()">&#8595; JSON</button>
      </div>
      <div class="page-btn-group">
        <button class="page-btn" id="btn-prev" onclick="changePage(-1)">&larr; Prev</button>
        <button class="page-btn" id="btn-next" onclick="changePage(1)">Next &rarr;</button>
      </div>
    </div>
  </div>

  <table id="data-table">
    <thead>
      <tr>
        <th class="sortable sort-desc" data-col="verdict" onclick="setSort('verdict')">Verdict</th>
        <th class="sortable"           data-col="arabic_root"  onclick="setSort('arabic_root')">Arabic</th>
        <th class="sortable"           data-col="target_lemma" onclick="setSort('target_lemma')">Target</th>
        <th>Lang</th>
        <th>Journey Type</th>
        <th>Key Insight</th>
        <th>Confidence</th>
      </tr>
    </thead>
    <tbody id="table-body"></tbody>
  </table>
  <div id="no-results">No findings match the current filters.</div>
</div>

<script>
/* ─── Data ─────────────────────────────────────────────────────────────────── */
const D = __DATA_PLACEHOLDER__;
const CROSS_BRANCH = __CROSS_BRANCH_PLACEHOLDER__;

/* ─── State ─────────────────────────────────────────────────────────────────── */
const PAGE_SIZE = 50;
let filtered    = [];
let currentPage = 0;
let sortCol     = "verdict";
let sortDir     = 1;
let activeChip  = "confirmed";
let expandedRow = -1;

/* ─── Theme ──────────────────────────────────────────────────────────────────  */
function setTheme(t) {
  document.documentElement.setAttribute("data-theme", t);
  document.querySelectorAll(".theme-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.t === t);
  });
}

/* ─── Helpers ────────────────────────────────────────────────────────────────  */
function esc(s) {
  return String(s || "")
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;");
}
function trunc(s, n) {
  s = String(s || "");
  return s.length > n ? s.slice(0, n) + "\u2026" : s;
}

function verdictBadge(v) {
  const label = {
    "confirmed_cognate": "confirmed",
    "confirmed":         "confirmed",
    "plausible_link":    "plausible",
    "shared_loanword":   "shared loan",
    "proper_name":       "proper name",
    "false_positive":    "false pos.",
    "legacy_scored":     "legacy",
  }[v] || v;
  const cls = v.startsWith("confirmed") ? "verdict-confirmed"
            : v === "plausible_link"     ? "verdict-plausible"
            : v === "shared_loanword"    ? "verdict-loanword"
            : v === "proper_name"        ? "verdict-proper"
            : v === "false_positive"     ? "verdict-false"
            : v === "legacy_scored"      ? "verdict-legacy"
            : "verdict-false";
  return `<span class="verdict-badge ${cls}">${esc(label)}</span>`;
}

function confDot(c) {
  const cls = c === "high" ? "conf-high" : c === "medium" ? "conf-medium" : "conf-low";
  return `<span class="conf-dot ${cls}" title="${esc(c)}"></span>${esc(c)}`;
}

function langBadge(lang) {
  const label = {
    grc: "GRC", lat: "LAT", got: "GOT", ang: "OE",
    sga: "OIR", non: "NON", eng: "ENG", deu: "DEU",
    fra: "FRA", spa: "SPA", ita: "ITA", fa: "FA", syc: "SYC",
  }[lang] || lang.toUpperCase();
  const cls = {
    grc: "badge-grc", lat: "badge-lat", got: "badge-got",
    ang: "badge-ang", sga: "badge-sga", non: "badge-non",
  }[lang] || "badge-oth";
  return `<span class="lang-badge ${cls}">${esc(label)}</span>`;
}

/* ─── Chip filter ────────────────────────────────────────────────────────────  */
function setChip(el) {
  activeChip = el.dataset.chip;
  document.querySelectorAll(".chip").forEach(c => c.classList.toggle("active", c === el));
  applyFilters();
}

/* ─── Filters ────────────────────────────────────────────────────────────────  */
function isPositive(v) {
  return v === "confirmed_cognate" || v === "confirmed" || v === "plausible_link";
}
function isConfirmed(v) {
  return v === "confirmed_cognate" || v === "confirmed";
}

function applyFilters() {
  const journeyType = document.getElementById("journey-select").value;
  const conf        = document.getElementById("conf-select").value;
  const search      = document.getElementById("search-input").value.trim().toLowerCase();
  const chip        = activeChip;

  filtered = D.filter(d => {
    // Chip-level filters
    if (chip === "confirmed"    && !isConfirmed(d.verdict)) return false;
    if (chip === "positive"     && !isPositive(d.verdict))  return false;
    if (chip === "cross_branch" && !d.cross_branch)         return false;
    if (["Hellenic","Italic","Germanic-East","Germanic-West","Celtic","North-Germanic"].includes(chip)
        && d.branch !== chip) return false;

    // Fine-grained filters
    if (journeyType && d.journey_type !== journeyType) return false;
    if (conf && d.confidence !== conf) return false;

    // Search
    if (search) {
      const hay = (
        d.arabic_root + " " + d.target_lemma + " " +
        (d.semantic_journey || "") + " " + (d.key_insight || "") + " " +
        (d.journey_type || "") + " " + (d.branch || "")
      ).toLowerCase();
      if (!hay.includes(search)) return false;
    }
    return true;
  });

  applySort();
  expandedRow = -1;
  updateStats();
  updateChart();
  currentPage = 0;
  renderPage();
}

/* ─── Sorting ────────────────────────────────────────────────────────────────  */
const VERDICT_ORDER = {
  "confirmed_cognate": 0, "confirmed": 0,
  "plausible_link": 1,
  "shared_loanword": 2,
  "proper_name": 3,
  "false_positive": 4,
  "legacy_scored": 5,
};
const CONF_ORDER = { "high": 0, "medium": 1, "low": 2 };

function setSort(col) {
  if (sortCol === col) {
    sortDir = -sortDir;
  } else {
    sortCol = col;
    sortDir = 1;
  }
  document.querySelectorAll("#data-table th").forEach(th => th.classList.remove("sort-asc","sort-desc"));
  const th = document.querySelector(`#data-table th[data-col="${col}"]`);
  if (th) th.classList.add(sortDir === 1 ? "sort-asc" : "sort-desc");
  applySort();
  currentPage = 0;
  expandedRow = -1;
  renderPage();
}
function applySort() {
  filtered.sort((a, b) => {
    let av, bv;
    if (sortCol === "verdict") {
      av = (VERDICT_ORDER[a.verdict] ?? 9) * 10 + (CONF_ORDER[a.confidence] ?? 9);
      bv = (VERDICT_ORDER[b.verdict] ?? 9) * 10 + (CONF_ORDER[b.confidence] ?? 9);
      return sortDir * (av - bv);
    }
    av = a[sortCol] ?? "";
    bv = b[sortCol] ?? "";
    return sortDir * String(av).localeCompare(String(bv), undefined, {sensitivity:"base"});
  });
}

/* ─── Stats ──────────────────────────────────────────────────────────────────  */
function updateStats() {
  const total     = filtered.length;
  const confirmed = filtered.filter(d => isConfirmed(d.verdict)).length;
  const plausible = filtered.filter(d => d.verdict === "plausible_link").length;
  const crossB    = filtered.filter(d => d.cross_branch).length;
  const grc       = filtered.filter(d => d.lang === "grc").length;
  const lat       = filtered.filter(d => d.lang === "lat").length;
  const gmc       = filtered.filter(d => ["got","ang","non","deu","eng"].includes(d.lang)).length;
  const cel       = filtered.filter(d => d.lang === "sga").length;
  document.getElementById("stat-total").textContent     = total.toLocaleString();
  document.getElementById("stat-confirmed").textContent = confirmed.toLocaleString();
  document.getElementById("stat-plausible").textContent = plausible.toLocaleString();
  document.getElementById("stat-cross").textContent     = crossB.toLocaleString();
  document.getElementById("stat-grc").textContent       = grc.toLocaleString();
  document.getElementById("stat-lat").textContent       = lat.toLocaleString();
  document.getElementById("stat-gmc").textContent       = gmc.toLocaleString();
  document.getElementById("stat-cel").textContent       = cel.toLocaleString();
}

/* ─── Chart ──────────────────────────────────────────────────────────────────  */
const BRANCHES = [
  {key: "Hellenic",       label: "Hellenic (GRC)"},
  {key: "Italic",         label: "Italic (LAT)"},
  {key: "Germanic-East",  label: "Gmc-East (GOT)"},
  {key: "Germanic-West",  label: "Gmc-West (OE)"},
  {key: "Celtic",         label: "Celtic (OIR)"},
  {key: "North-Germanic", label: "N-Gmc (NON)"},
];

function updateChart() {
  const container = document.getElementById("chart-container");
  const rows = BRANCHES.map(({key, label}) => {
    const branch_recs = filtered.filter(d => d.branch === key);
    const conf = branch_recs.filter(d => isConfirmed(d.verdict)).length;
    const plaus = branch_recs.filter(d => d.verdict === "plausible_link").length;
    const oth  = branch_recs.length - conf - plaus;
    return {label, conf, plaus, oth, total: branch_recs.length};
  });
  const maxN = Math.max(...rows.map(r => r.total), 1);
  container.innerHTML = rows.map(r => {
    const cW = ((r.conf  / maxN) * 100).toFixed(1);
    const pW = ((r.plaus / maxN) * 100).toFixed(1);
    const oW = ((r.oth   / maxN) * 100).toFixed(1);
    return `<div class="chart-row">
      <span class="chart-band-label">${esc(r.label)}</span>
      <div class="chart-bars" title="Confirmed: ${r.conf}, Plausible: ${r.plaus}, Other: ${r.oth}">
        <div class="chart-bar-confirmed" style="width:${cW}%"></div>
        <div class="chart-bar-plausible" style="width:${pW}%"></div>
        <div class="chart-bar-other"     style="width:${oW}%"></div>
      </div>
      <span class="chart-count">${r.total > 0 ? r.total.toLocaleString() : ""}</span>
    </div>`;
  }).join("");
}

/* ─── Table rendering ────────────────────────────────────────────────────────  */
function renderPage() {
  const tbody = document.getElementById("table-body");
  const noRes = document.getElementById("no-results");
  const total = filtered.length;
  const start = currentPage * PAGE_SIZE;
  const end   = Math.min(start + PAGE_SIZE, total);
  const slice = filtered.slice(start, end);

  if (total === 0) {
    tbody.innerHTML = "";
    noRes.style.display = "block";
    document.getElementById("page-info").textContent = "No results";
    document.getElementById("btn-prev").disabled = true;
    document.getElementById("btn-next").disabled = true;
    return;
  }
  noRes.style.display = "none";
  document.getElementById("page-info").textContent =
    `Showing ${(start+1).toLocaleString()}\u2013${end.toLocaleString()} of ${total.toLocaleString()}`;
  document.getElementById("btn-prev").disabled = currentPage === 0;
  document.getElementById("btn-next").disabled = end >= total;

  const rows = [];
  slice.forEach((d, idx) => {
    const gi = start + idx;
    const crossTag = d.cross_branch ? `<span class="cross-tag">CROSS</span>` : "";
    const rowClass = d.cross_branch ? "data-row cross-branch-row" : "data-row";

    rows.push(`<tr class="${rowClass}" onclick="toggleDetail(${gi})" data-gi="${gi}">
      <td>${verdictBadge(d.verdict)}</td>
      <td><span class="ar-text">${esc(d.arabic_root)}</span></td>
      <td><span class="tgt-word">${esc(d.target_lemma)}</span>${crossTag}</td>
      <td>${langBadge(d.lang)}</td>
      <td><span class="journey-badge">${esc((d.journey_type||"").replace(/_/g," "))}</span></td>
      <td><span class="insight-cell" title="${esc(d.key_insight)}">${esc(trunc(d.key_insight, 110))}</span></td>
      <td>${confDot(d.confidence)}</td>
    </tr>`);

    if (expandedRow === gi) {
      const journey = d.semantic_journey || "(no semantic journey recorded)";
      rows.push(`<tr class="detail-row">
        <td colspan="7">
          <div class="detail-panel">
            <div>
              <div class="dp-label">Arabic Root</div>
              <div class="dp-value"><span class="ar-text">${esc(d.arabic_root)}</span></div>
            </div>
            <div>
              <div class="dp-label">Target &mdash; ${esc(d.lang.toUpperCase())} / ${esc(d.branch)}</div>
              <div class="dp-value"><em>${esc(d.target_lemma)}</em></div>
            </div>
            <div>
              <div class="dp-label">Verdict / Confidence</div>
              <div class="dp-value">${verdictBadge(d.verdict)} &nbsp; ${confDot(d.confidence)}</div>
            </div>
            <div>
              <div class="dp-label">Journey Type</div>
              <div class="dp-value">${esc((d.journey_type||"—").replace(/_/g," "))}</div>
            </div>
            <div class="detail-journey">
              <div class="dp-label">Semantic Journey</div>
              <div class="journey-text">${esc(journey)}</div>
            </div>
            <div>
              <div class="dp-label">Key Insight</div>
              <div class="dp-value">${esc(d.key_insight || "—")}</div>
            </div>
            ${d.original_score > 0 ? `<div>
              <div class="dp-label">Original Eye 2 Score</div>
              <div class="dp-value">${d.original_score.toFixed(3)} &mdash; ${esc(d.original_method || "—")}</div>
            </div>` : ""}
            ${d.cross_branch ? `<div>
              <div class="dp-label">Cross-Branch Cognate</div>
              <div class="dp-value" style="color:var(--cross-branch-border);font-weight:600;">
                This Arabic root appears confirmed in 2+ language branches.
              </div>
            </div>` : ""}
          </div>
        </td>
      </tr>`);
    }
  });
  tbody.innerHTML = rows.join("");
}

function toggleDetail(gi) {
  expandedRow = (expandedRow === gi) ? -1 : gi;
  renderPage();
}

function changePage(delta) {
  const maxPage = Math.ceil(filtered.length / PAGE_SIZE) - 1;
  currentPage = Math.max(0, Math.min(maxPage, currentPage + delta));
  expandedRow = -1;
  renderPage();
  window.scrollTo({ top: document.getElementById("table-section").offsetTop - 20, behavior: "smooth" });
}

/* ─── Export ─────────────────────────────────────────────────────────────────  */
function exportCSV() {
  const cols = ["arabic_root","target_lemma","lang","branch","verdict","confidence",
                "journey_type","key_insight","semantic_journey","cross_branch","source"];
  const header = cols.join(",") + "\n";
  const rows = filtered.map(d =>
    cols.map(c => {
      const v = String(d[c] ?? "").replace(/"/g, '""');
      return (v.includes(",") || v.includes('"') || v.includes("\n")) ? `"${v}"` : v;
    }).join(",")
  ).join("\n");
  dl("discoveries_filtered.csv", "text/csv;charset=utf-8", "\uFEFF" + header + rows);
}
function exportJSON() {
  dl("discoveries_filtered.json", "application/json", JSON.stringify(filtered, null, 2));
}
function dl(name, mime, content) {
  const url = URL.createObjectURL(new Blob([content], {type: mime}));
  const a = Object.assign(document.createElement("a"), {href: url, download: name});
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/* ─── Init ───────────────────────────────────────────────────────────────────  */
applyFilters();
</script>
</body>
</html>"""


def main():
    # Load NON metadata for pair_id lookup
    non_meta = load_non_meta()

    # Load all detective-mode findings
    grc_lat  = load_grc_lat_reinvestigation()
    wave1    = load_wave1_reinvestigation()
    non_pilot = load_non_pilot(non_meta)

    # Load cross-branch analysis
    analysis      = load_confirmed_analysis()
    cross_branch_roots = analysis.get("cross_branch_roots", [])

    # Merge all records
    all_records = grc_lat + wave1 + non_pilot

    # Load legacy eye2 records (backwards compat, lower priority)
    legacy = load_legacy_records()
    all_records += legacy

    if not all_records:
        print("[error] No records loaded — exiting", file=sys.stderr)
        sys.exit(1)

    records = merge_records(all_records, cross_branch_roots)
    print_summary(records)

    # Build serialisable cross-branch lookup
    cross_branch_data = [
        {
            "arabic_root": r.get("arabic_root", ""),
            "n_branches":  r.get("n_branches", 0),
            "branches":    r.get("branches", []),
        }
        for r in cross_branch_roots
    ]

    # Render HTML
    data_json   = json.dumps(records, ensure_ascii=False)
    cross_json  = json.dumps(cross_branch_data, ensure_ascii=False)
    html = HTML_TEMPLATE.replace("__DATA_PLACEHOLDER__", data_json)
    html = html.replace("__CROSS_BRANCH_PLACEHOLDER__", cross_json)

    out_path = LV2 / "outputs" / "discoveries_dashboard.html"
    out_path.write_text(html, encoding="utf-8")

    size_kb = out_path.stat().st_size / 1024
    print(f"\nDashboard -> {out_path}  ({size_kb:.0f} KB)", file=sys.stderr)
    if size_kb < 50:
        print("[warn] Dashboard is smaller than expected (<50 KB)", file=sys.stderr)

    # Final counts by language and verdict for reporting
    print("\n=== Final counts by language + verdict ===", file=sys.stderr)
    for lang in ["grc", "lat", "got", "ang", "sga", "non"]:
        lang_recs = [r for r in records if r["lang"] == lang]
        if not lang_recs:
            continue
        verdicts = Counter(r["verdict"] for r in lang_recs)
        label = LANG_LABEL.get(lang, lang)
        print(f"  {lang} ({label}): {len(lang_recs)} total", file=sys.stderr)
        for v, cnt in sorted(verdicts.items()):
            print(f"    {v}: {cnt}", file=sys.stderr)


if __name__ == "__main__":
    main()
