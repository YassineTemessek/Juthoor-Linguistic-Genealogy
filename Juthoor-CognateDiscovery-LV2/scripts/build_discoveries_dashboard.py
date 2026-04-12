"""Build the Juthoor LV2 Discoveries Dashboard (single HTML file with embedded data).

Enriches each record with:
  - tgt_ipa, tgt_gloss  : from greek_ipa_gloss_lookup.json / latin_ipa_gloss_lookup.json
  - ar_def, ar_translit : from LV0 lexemes.jsonl (root_norm lookup)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LV2  = ROOT / "Juthoor-CognateDiscovery-LV2"
LV0  = ROOT / "Juthoor-DataCore-LV0"


# ── Lookup builders ────────────────────────────────────────────────────────────

def build_ipa_lookup(lang: str) -> dict:
    fname = "greek_ipa_gloss_lookup.json" if lang == "grc" else "latin_ipa_gloss_lookup.json"
    path  = LV2 / "data" / "processed" / fname
    if not path.exists():
        print(f"[warn] IPA lookup not found: {path}", file=sys.stderr)
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    print(f"[{lang}] IPA/gloss lookup: {len(data):,} entries", file=sys.stderr)
    return data


def build_arabic_lookup() -> dict:
    """Build root_norm -> {def, translit} from LV0 lexemes. First occurrence wins."""
    path = LV0 / "data" / "processed" / "arabic" / "classical" / "lexemes.jsonl"
    if not path.exists():
        print(f"[warn] Arabic lexemes not found: {path}", file=sys.stderr)
        return {}
    lookup: dict = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            rn = r.get("root_norm", "")
            if rn and rn not in lookup:
                defn = (r.get("definition") or r.get("short_gloss") or "").strip()
                lookup[rn] = {
                    "def":     defn[:160] if defn else "",
                    "translit": (r.get("translit") or "").strip(),
                }
    print(f"[ara] Lexeme lookup: {len(lookup):,} entries", file=sys.stderr)
    return lookup


# ── Discovery loading & enrichment ─────────────────────────────────────────────

def load_discoveries(ipa_grc: dict, ipa_lat: dict, ar_lookup: dict) -> list:
    """Load ALL scored pairs from every source, merge into unified language categories.

    Language mapping: grc, lat, eng, fra, deu, ang, spa, ita, fa, syc, non, other.
    No separate 'gold reference' category — everything merges into its proper language.
    Dedup by (arabic, target) key — keep the highest score.
    """
    # Unified language normalization
    LANG_MAP = {
        "grc": "grc", "lat": "lat", "eng": "eng", "fra": "fra",
        "deu": "deu", "ang": "ang", "spa": "spa", "ita": "ita",
        "fa": "fa", "syc": "syc", "non": "non",
    }

    # Collect all pairs keyed by (ar, tgt) — keep highest score
    best: dict[tuple, dict] = {}

    def _add(ar, tgt, score, lang, method, reasoning, model, tgt_ipa="", tgt_gloss=""):
        key = (ar, tgt)
        if key in best and best[key]["score"] >= score:
            return
        ar_def = ""
        ar_translit = ""
        if ar in ar_lookup:
            ar_def = ar_lookup[ar]["def"]
            ar_translit = ar_lookup[ar]["translit"]
        # IPA + gloss enrichment from lookup maps
        if not tgt_ipa and not tgt_gloss:
            if lang == "grc" and tgt in ipa_grc:
                tgt_ipa = (ipa_grc[tgt].get("ipa") or "").strip()
                tgt_gloss = (ipa_grc[tgt].get("gloss") or "").strip()
            elif lang == "lat" and tgt in ipa_lat:
                tgt_ipa = (ipa_lat[tgt].get("ipa") or "").strip()
                tgt_gloss = (ipa_lat[tgt].get("gloss") or "").strip()
        best[key] = {
            "ar": ar, "tgt": tgt,
            "score": round(score, 3),
            "lang": LANG_MAP.get(lang, "other"),
            "method": (method or "weak").strip(),
            "reasoning": (reasoning or "").strip()[:200],
            "model": (model or "unknown").strip(),
            "tgt_ipa": tgt_ipa, "tgt_gloss": (tgt_gloss or "")[:120],
            "ar_def": (ar_def or "")[:160], "ar_translit": ar_translit,
        }

    # Source 1: Pipeline discoveries (Greek + Latin)
    for lang, fname in [("grc", "eye2_final_grc.jsonl"), ("lat", "eye2_final_lat.jsonl")]:
        path = LV2 / "outputs" / fname
        if not path.exists():
            continue
        count = 0
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip(): continue
                r = json.loads(line)
                if r.get("semantic_score", 0) < 0.3: continue
                _add(r.get("source_lemma", ""), r.get("target_lemma", ""),
                     r.get("semantic_score", 0), lang,
                     r.get("method", ""), r.get("reasoning", ""),
                     r.get("final_model") or r.get("model", ""))
                count += 1
        print(f"[{lang}] {count} pipeline records", file=sys.stderr)

    # Source 2: Scored pairs from all sources — merge into proper language
    for fname in ["eye2_final_beyond_name.jsonl"]:
        path = LV2 / "outputs" / fname
        if not path.exists():
            continue
        count = 0
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip(): continue
                r = json.loads(line)
                if r.get("semantic_score", 0) < 0.3: continue
                # Use target_lang to route to proper language category
                target_lang = (r.get("target_lang") or "eng").strip()
                _add(r.get("source_lemma", ""), r.get("target_lemma", ""),
                     r.get("semantic_score", 0), target_lang,
                     r.get("method", ""), r.get("reasoning", ""),
                     r.get("model", ""))
                count += 1
        print(f"[merged] {count} records from {fname}", file=sys.stderr)

    # Source 3: Original Eye 2 gold pair scores (English + Latin)
    for gold_fname, default_lang in [
        ("eye2_eng_semantic_scores.jsonl", "eng"),
        ("eye2_semantic_scores.jsonl", "lat"),
    ]:
        path = LV2 / "data" / "llm_annotations" / gold_fname
        if not path.exists():
            continue
        count = 0
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip(): continue
                r = json.loads(line)
                if r.get("semantic_score", 0) < 0.3: continue
                lang_pair = r.get("lang_pair", "")
                lang = lang_pair.split("-")[-1] if "-" in lang_pair else default_lang
                _add(r.get("source_lemma", ""), r.get("target_lemma", ""),
                     r.get("semantic_score", 0), lang,
                     r.get("method", ""), r.get("reasoning", "") or r.get("path", ""),
                     r.get("annotator", "") or "claude")
                count += 1
        print(f"[{default_lang}] {count} original Eye 2 records", file=sys.stderr)

    records = sorted(best.values(), key=lambda x: -x["score"])
    # Print summary by language
    from collections import Counter
    langs = Counter(r["lang"] for r in records)
    print(f"\nTotal unique records: {len(records):,}", file=sys.stderr)
    for lang, cnt in langs.most_common():
        above05 = sum(1 for r in records if r["lang"] == lang and r["score"] >= 0.5)
        print(f"  {lang}: {cnt} records, {above05} >=0.5", file=sys.stderr)
    return records


# ── HTML template ──────────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" dir="ltr" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Juthoor Codex &mdash; Cognate Discoveries</title>
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
  --score-hi-bg:      #d4edda; --score-hi-text:  #1e7a46;
  --score-med-bg:     #fef3c7; --score-med-text: #b8860b;
  --score-lo-bg:      #f0ebe3; --score-lo-text:  #8a7e72;
  --badge-grc-border: #1a3d34; --badge-grc-text: #1a3d34;
  --badge-lat-border: #c2524a; --badge-lat-text: #c2524a;
  --badge-eng-border: #2d6a2d; --badge-eng-text: #2d6a2d;
  --badge-oth-border: #b8860b; --badge-oth-text: #b8860b;
  --chart-grc:        #1a3d34;
  --chart-lat:        #c2524a;
  --chart-btn:        #b8860b;
  --chart-track:      #e8e0d4;
  --stat-grc-color:   #1a3d34;
  --stat-lat-color:   #c2524a;
  --stat-btn-color:   #b8860b;
  --stat-hi-color:    #1e7a46;
  --stat-med-color:   #b8860b;
  --method-masadiq-border:  #1a3d34; --method-masadiq-text:  #1a3d34;
  --method-mafahim-border:  #6b3fa0; --method-mafahim-text:  #6b3fa0;
  --method-combined-border: #b8860b; --method-combined-text: #b8860b;
  --method-weak-border:     #8a7e72; --method-weak-text:     #8a7e72;
  --detail-bg:        #f7f4ef;
  --detail-border:    #b8860b;
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
  --score-hi-bg:      #c8e6c9; --score-hi-text:  #1b5e20;
  --score-med-bg:     #fde8a0; --score-med-text: #92600a;
  --score-lo-bg:      #e8d9be; --score-lo-text:  #7a6040;
  --badge-grc-border: #1a3d34; --badge-grc-text: #1a3d34;
  --badge-lat-border: #b03028; --badge-lat-text: #b03028;
  --badge-eng-border: #256025; --badge-eng-text: #256025;
  --badge-oth-border: #a07010; --badge-oth-text: #a07010;
  --chart-grc:        #1a3d34;
  --chart-lat:        #b03028;
  --chart-btn:        #c49010;
  --chart-track:      #d4be96;
  --stat-grc-color:   #1a3d34;
  --stat-lat-color:   #b03028;
  --stat-btn-color:   #c49010;
  --stat-hi-color:    #1b5e20;
  --stat-med-color:   #92600a;
  --method-masadiq-border:  #1a3d34; --method-masadiq-text:  #1a3d34;
  --method-mafahim-border:  #5a2e90; --method-mafahim-text:  #5a2e90;
  --method-combined-border: #c49010; --method-combined-text: #c49010;
  --method-weak-border:     #7a6040; --method-weak-text:     #7a6040;
  --detail-bg:        #f2e8d5;
  --detail-border:    #c49010;
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
  --score-hi-bg:      #1a3a22; --score-hi-text:  #4cc870;
  --score-med-bg:     #2e2010; --score-med-text: #d4a438;
  --score-lo-bg:      #2e2e3a; --score-lo-text:  #7a7870;
  --badge-grc-border: #2a8060; --badge-grc-text: #2a8060;
  --badge-lat-border: #e06860; --badge-lat-text: #e06860;
  --badge-eng-border: #40a040; --badge-eng-text: #40a040;
  --badge-oth-border: #d4a438; --badge-oth-text: #d4a438;
  --chart-grc:        #2a8060;
  --chart-lat:        #e06860;
  --chart-btn:        #d4a438;
  --chart-track:      #36363e;
  --stat-grc-color:   #2a8060;
  --stat-lat-color:   #e06860;
  --stat-btn-color:   #d4a438;
  --stat-hi-color:    #4cc870;
  --stat-med-color:   #d4a438;
  --method-masadiq-border:  #2a8060; --method-masadiq-text:  #2a8060;
  --method-mafahim-border:  #a070e0; --method-mafahim-text:  #a070e0;
  --method-combined-border: #d4a438; --method-combined-text: #d4a438;
  --method-weak-border:     #7a7870; --method-weak-text:     #7a7870;
  --detail-bg:        #1f1f2c;
  --detail-border:    #d4a438;
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
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--card-shadow-hover);
}
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
.stat-grc .stat-value  { color: var(--stat-grc-color); }
.stat-lat .stat-value  { color: var(--stat-lat-color); }
.stat-btn .stat-value  { color: var(--stat-btn-color); }
.stat-hi  .stat-value  { color: var(--stat-hi-color);  }
.stat-med .stat-value  { color: var(--stat-med-color); }

/* ── Quick filter chips ── */
#chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  padding: 0.85rem 2rem;
  background: var(--bg);
  border-bottom: 1px solid var(--border);
  align-items: center;
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
.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.filter-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  white-space: nowrap;
  font-weight: 500;
  letter-spacing: 0.03em;
}
input[type="range"] {
  -webkit-appearance: none;
  appearance: none;
  width: 140px;
  height: 4px;
  border-radius: 2px;
  background: var(--border);
  outline: none;
  cursor: pointer;
}
input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px; height: 14px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
  border: 2px solid var(--bg);
  box-shadow: 0 0 0 1px var(--accent);
}
#score-val {
  font-family: 'Cascadia Code', 'Consolas', 'Monaco', monospace;
  font-size: 0.80rem;
  color: var(--accent);
  font-weight: 700;
  min-width: 2.8rem;
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
  width: 62px;
  text-align: right;
  flex-shrink: 0;
}
.chart-bars {
  display: flex;
  height: 12px;
  flex: 1;
  border-radius: 3px;
  overflow: hidden;
  background: var(--chart-track);
}
.chart-bar-grc { background: var(--chart-grc); height: 100%; transition: width 0.25s; }
.chart-bar-lat { background: var(--chart-lat); height: 100%; transition: width 0.25s; }
.chart-bar-btn { background: var(--chart-btn); height: 100%; transition: width 0.25s; }
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
#page-info {
  font-size: 0.80rem;
  color: var(--text-muted);
  font-style: italic;
}
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
.export-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

/* ── Data table ── */
#data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.83rem;
}
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
#data-table tr.data-row:hover > td { background: var(--table-hover); cursor: pointer; }
#data-table tr.detail-row > td {
  background: var(--detail-bg);
  border-left: 3px solid var(--detail-border);
  padding: 1rem 1.25rem;
}

/* ── Score display ── */
.score-wrap {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 3px;
}
.score-pill {
  font-family: 'Cascadia Code', 'Consolas', 'Monaco', monospace;
  display: inline-block;
  padding: 0.12rem 0.48rem;
  border-radius: 10px;
  font-weight: 700;
  font-size: 0.78rem;
  min-width: 44px;
  text-align: center;
}
.score-bar {
  width: 40px;
  height: 3px;
  border-radius: 2px;
  background: var(--border);
  overflow: hidden;
}
.score-bar-fill {
  height: 100%;
  border-radius: 2px;
}
.score-hi  { background: var(--score-hi-bg);  color: var(--score-hi-text);  }
.score-med { background: var(--score-med-bg); color: var(--score-med-text); }
.score-lo  { background: var(--score-lo-bg);  color: var(--score-lo-text);  }
.fill-hi   { background: var(--score-hi-text); }
.fill-med  { background: var(--score-med-text); }
.fill-lo   { background: var(--score-lo-text); }

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
.ar-translit {
  font-family: 'Cascadia Code', 'Consolas', 'Monaco', monospace;
  font-size: 0.68rem;
  color: var(--text-muted);
  display: block;
  margin-top: 0.12rem;
  font-style: italic;
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
.tgt-ipa {
  font-family: 'Cascadia Code', 'Consolas', 'Monaco', monospace;
  font-size: 0.68rem;
  color: var(--text-muted);
  display: block;
  margin-top: 0.1rem;
}

/* ── Meaning text ── */
.meaning-text {
  font-size: 0.78rem;
  color: var(--text-muted);
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

/* ── Lang badge ── */
.lang-badge {
  display: inline-block;
  padding: 0.12rem 0.5rem;
  border-radius: 4px;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  background: transparent;
  border-left: 2px solid currentColor;
  padding-left: 0.45rem;
}
.badge-grc { color: var(--badge-grc-text); border-color: var(--badge-grc-border); }
.badge-lat { color: var(--badge-lat-text); border-color: var(--badge-lat-border); }
.badge-eng { color: var(--badge-eng-text); border-color: var(--badge-eng-border); }
.badge-btn { color: var(--badge-oth-text); border-color: var(--badge-oth-border); }

/* ── Method badge ── */
.method-badge {
  display: inline-block;
  padding: 0.10rem 0.45rem;
  border-radius: 10px;
  border: 1px solid currentColor;
  font-size: 0.65rem;
  font-weight: 500;
  white-space: nowrap;
  background: transparent;
}
.method-masadiq  { color: var(--method-masadiq-text);  border-color: var(--method-masadiq-border);  }
.method-mafahim  { color: var(--method-mafahim-text);  border-color: var(--method-mafahim-border);  }
.method-combined { color: var(--method-combined-text); border-color: var(--method-combined-border); }
.method-weak     { color: var(--method-weak-text);     border-color: var(--method-weak-border);     }

/* ── Reasoning cell ── */
.reasoning-cell {
  font-size: 0.75rem;
  color: var(--text-muted);
  max-width: 240px;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Model text ── */
.model-text {
  font-family: 'Cascadia Code', 'Consolas', 'Monaco', monospace;
  font-size: 0.62rem;
  color: var(--text-muted);
  opacity: 0.6;
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
.detail-panel .dp-value {
  color: var(--text);
  line-height: 1.6;
}
.detail-reasoning { grid-column: 1 / -1; }

/* ── No results ── */
#no-results {
  text-align: center;
  padding: 4rem;
  color: var(--text-muted);
  font-size: 0.9rem;
  font-style: italic;
  display: none;
}

/* ── Export section ── */
#export-section { display: flex; gap: 0.4rem; align-items: center; }

/* ── Responsive ── */
@media (max-width: 900px) {
  header, #stats-bar, #chip-row, #filter-bar, #chart-section, #table-section {
    padding-left: 1rem; padding-right: 1rem;
  }
  #data-table th:nth-child(5), #data-table td:nth-child(5),
  #data-table th:nth-child(8), #data-table td:nth-child(8),
  #data-table th:nth-child(9), #data-table td:nth-child(9) { display: none; }
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
    <p>Arabic cognate discoveries &mdash; Greek, Latin, English &amp; other languages</p>
  </div>
  <div class="theme-switcher">
    <button class="theme-btn active" data-t="light"  onclick="setTheme('light')">Light</button>
    <button class="theme-btn"        data-t="warm"   onclick="setTheme('warm')">Warm</button>
    <button class="theme-btn"        data-t="dark"   onclick="setTheme('dark')">Dark</button>
  </div>
</header>

<div id="stats-bar">
  <div class="stat-card stat-total">
    <div class="stat-label">Total</div>
    <div class="stat-value" id="stat-total">&mdash;</div>
  </div>
  <div class="stat-card stat-grc">
    <div class="stat-label">Greek</div>
    <div class="stat-value" id="stat-grc">&mdash;</div>
  </div>
  <div class="stat-card stat-lat">
    <div class="stat-label">Latin</div>
    <div class="stat-value" id="stat-lat">&mdash;</div>
  </div>
  <div class="stat-card stat-btn">
    <div class="stat-label">English</div>
    <div class="stat-value" id="stat-btn">&mdash;</div>
  </div>
  <div class="stat-card stat-hi">
    <div class="stat-label">Score &ge;0.8</div>
    <div class="stat-value" id="stat-hi">&mdash;</div>
  </div>
  <div class="stat-card stat-med">
    <div class="stat-label">Score &ge;0.6</div>
    <div class="stat-value" id="stat-med">&mdash;</div>
  </div>
</div>

<div id="chip-row">
  <button class="chip active" data-chip="all"    onclick="setChip(this)">All</button>
  <button class="chip"        data-chip="top50"  onclick="setChip(this)">Top 50</button>
  <button class="chip"        data-chip="direct" onclick="setChip(this)">Direct Loans</button>
  <button class="chip"        data-chip="hidden" onclick="setChip(this)">Hidden Cognates</button>
  <button class="chip"        data-chip="grc"    onclick="setChip(this)">Greek</button>
  <button class="chip"        data-chip="lat"    onclick="setChip(this)">Latin</button>
  <button class="chip"        data-chip="eng"    onclick="setChip(this)">English</button>
  <button class="chip"        data-chip="other"  onclick="setChip(this)">Other Languages</button>
</div>

<div id="filter-bar">
  <div class="filter-group">
    <label class="filter-label" for="score-slider">Min Score:</label>
    <input type="range" id="score-slider" min="0.3" max="1.0" step="0.05" value="0.3"
           oninput="onScoreChange(this)">
    <span id="score-val">0.30</span>
  </div>
  <div class="filter-group">
    <label class="filter-label" for="method-select">Method:</label>
    <select id="method-select" onchange="applyFilters()">
      <option value="">All methods</option>
      <option value="masadiq_direct">masadiq_direct</option>
      <option value="mafahim_deep">mafahim_deep</option>
      <option value="combined">combined</option>
      <option value="weak">weak</option>
    </select>
  </div>
  <div class="filter-group">
    <label class="filter-label" for="search-input">Search:</label>
    <input type="text" id="search-input" placeholder="Arabic, target, meaning..."
           oninput="applyFilters()">
  </div>
</div>

<div id="chart-section">
  <h3>Score Distribution</h3>
  <div id="chart-container"></div>
  <div class="chart-legend">
    <span><span class="legend-dot" style="background:var(--chart-grc)"></span>Greek</span>
    <span><span class="legend-dot" style="background:var(--chart-lat)"></span>Latin</span>
    <span><span class="legend-dot" style="background:var(--chart-btn)"></span>Other</span>
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
        <th class="sortable sort-desc" data-col="score" onclick="setSort('score')">Score</th>
        <th class="sortable" data-col="ar"    onclick="setSort('ar')">Arabic</th>
        <th>Arabic Meaning</th>
        <th class="sortable" data-col="tgt"   onclick="setSort('tgt')">Target</th>
        <th>Target Meaning</th>
        <th>Lang</th>
        <th>Method</th>
        <th>Reasoning</th>
        <th>Model</th>
      </tr>
    </thead>
    <tbody id="table-body"></tbody>
  </table>
  <div id="no-results">No discoveries match the current filters.</div>
</div>

<script>
/* ─── Data ─────────────────────────────────────────────────────────────────── */
const D = __DATA_PLACEHOLDER__;

/* ─── State ─────────────────────────────────────────────────────────────────── */
const PAGE_SIZE = 50;
let filtered    = [];
let currentPage = 0;
let sortCol     = "score";
let sortDir     = -1;
let activeChip  = "all";
let expandedRow = -1;  // global index in filtered

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
function scorePill(sc) {
  const cls  = sc >= 0.8 ? "score-hi" : sc >= 0.5 ? "score-med" : "score-lo";
  const fcls = sc >= 0.8 ? "fill-hi"  : sc >= 0.5 ? "fill-med"  : "fill-lo";
  const pct  = Math.round(sc * 100);
  return `<div class="score-wrap">
    <span class="score-pill ${cls}">${sc.toFixed(3)}</span>
    <div class="score-bar"><div class="score-bar-fill ${fcls}" style="width:${pct}%"></div></div>
  </div>`;
}
function methodBadge(m) {
  m = m || "weak";
  const cls = m.includes("masadiq") ? "method-masadiq"
            : m.includes("mafahim") ? "method-mafahim"
            : m.includes("combined") ? "method-combined"
            : "method-weak";
  return `<span class="method-badge ${cls}">${esc(m)}</span>`;
}

/* ─── Chip filter ────────────────────────────────────────────────────────────  */
function setChip(el) {
  activeChip = el.dataset.chip;
  document.querySelectorAll(".chip").forEach(c => c.classList.toggle("active", c === el));

  /* Chip presets: adjust slider/method/search then apply */
  const slider = document.getElementById("score-slider");
  const mSel   = document.getElementById("method-select");
  const srch   = document.getElementById("search-input");

  if (activeChip === "top50") {
    slider.value = "0.3";
    document.getElementById("score-val").textContent = "0.30";
    mSel.value = "";
    srch.value = "";
  } else if (activeChip === "direct") {
    mSel.value = "masadiq_direct";
  } else if (activeChip === "hidden") {
    mSel.value = "mafahim_deep";
  } else if (activeChip === "grc" || activeChip === "lat" || activeChip === "btn") {
    mSel.value = "";
  } else {
    /* all — reset method filter if it was set by a chip */
  }
  applyFilters();
}

/* ─── Filters ────────────────────────────────────────────────────────────────  */
function onScoreChange(el) {
  document.getElementById("score-val").textContent = parseFloat(el.value).toFixed(2);
  applyFilters();
}

function applyFilters() {
  const minScore = parseFloat(document.getElementById("score-slider").value);
  const method   = document.getElementById("method-select").value;
  const search   = document.getElementById("search-input").value.trim().toLowerCase();
  const chip     = activeChip;

  filtered = D.filter(d => {
    if (d.score < minScore) return false;
    if (method && d.method !== method) return false;
    if (chip === "grc" && d.lang !== "grc") return false;
    if (chip === "lat" && d.lang !== "lat") return false;
    if (chip === "eng" && d.lang !== "eng") return false;
    if (chip === "other" && ["grc","lat","eng"].includes(d.lang)) return false;
    if (chip === "direct"  && d.method !== "masadiq_direct") return false;
    if (chip === "hidden"  && d.method !== "mafahim_deep")   return false;
    if (search) {
      const hay = (d.ar + " " + d.tgt + " " + (d.ar_def||"") + " " + (d.tgt_gloss||"") + " " + (d.reasoning||"")).toLowerCase();
      if (!hay.includes(search)) return false;
    }
    return true;
  });

  applySort();
  expandedRow = -1;

  if (chip === "top50") {
    filtered = filtered.slice(0, 50);
  }

  updateStats();
  updateChart();
  currentPage = 0;
  renderPage();
}

/* ─── Sorting ────────────────────────────────────────────────────────────────  */
function setSort(col) {
  if (sortCol === col) {
    sortDir = -sortDir;
  } else {
    sortCol = col;
    sortDir = col === "score" ? -1 : 1;
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
    const av = a[sortCol] ?? "", bv = b[sortCol] ?? "";
    if (typeof av === "number") return sortDir * (av - bv);
    return sortDir * String(av).localeCompare(String(bv), undefined, {sensitivity:"base"});
  });
}

/* ─── Stats ──────────────────────────────────────────────────────────────────  */
function updateStats() {
  const total = filtered.length;
  const grcN  = filtered.filter(d => d.lang === "grc").length;
  const latN  = filtered.filter(d => d.lang === "lat").length;
  const engN  = filtered.filter(d => d.lang === "eng").length;
  const hiN   = filtered.filter(d => d.score >= 0.8).length;
  const medN  = filtered.filter(d => d.score >= 0.6).length;
  document.getElementById("stat-total").textContent = total.toLocaleString();
  document.getElementById("stat-grc").textContent   = grcN.toLocaleString();
  document.getElementById("stat-lat").textContent   = latN.toLocaleString();
  document.getElementById("stat-btn").textContent   = engN.toLocaleString();
  document.getElementById("stat-hi").textContent    = hiN.toLocaleString();
  document.getElementById("stat-med").textContent   = medN.toLocaleString();
}

/* ─── Chart ──────────────────────────────────────────────────────────────────  */
const BANDS       = [[0.3,0.4],[0.4,0.5],[0.5,0.6],[0.6,0.7],[0.7,0.8],[0.8,0.9],[0.9,1.01]];
const BAND_LABELS = ["0.3-0.4","0.4-0.5","0.5-0.6","0.6-0.7","0.7-0.8","0.8-0.9","0.9-1.0"];

function updateChart() {
  const container = document.getElementById("chart-container");
  const counts = BANDS.map(([lo, hi]) => ({
    grc: filtered.filter(d => d.lang==="grc" && d.score>=lo && d.score<hi).length,
    lat: filtered.filter(d => d.lang==="lat" && d.score>=lo && d.score<hi).length,
    oth: filtered.filter(d => !["grc","lat"].includes(d.lang) && d.score>=lo && d.score<hi).length,
  }));
  const maxN = Math.max(...counts.map(c => c.grc + c.lat + c.oth), 1);
  container.innerHTML = counts.map((c, i) => {
    const gW = ((c.grc / maxN) * 100).toFixed(1);
    const lW = ((c.lat / maxN) * 100).toFixed(1);
    const oW = ((c.oth / maxN) * 100).toFixed(1);
    const tot = c.grc + c.lat + c.oth;
    return `<div class="chart-row">
      <span class="chart-band-label">${BAND_LABELS[i]}</span>
      <div class="chart-bars" title="Greek: ${c.grc}, Latin: ${c.lat}, Other: ${c.oth}">
        <div class="chart-bar-grc" style="width:${gW}%"></div>
        <div class="chart-bar-lat" style="width:${lW}%"></div>
        <div class="chart-bar-btn" style="width:${oW}%"></div>
      </div>
      <span class="chart-count">${tot > 0 ? tot.toLocaleString() : ""}</span>
    </div>`;
  }).join("");
}

/* ─── Table rendering ────────────────────────────────────────────────────────  */
function renderPage() {
  const tbody    = document.getElementById("table-body");
  const noRes    = document.getElementById("no-results");
  const total    = filtered.length;
  const start    = currentPage * PAGE_SIZE;
  const end      = Math.min(start + PAGE_SIZE, total);
  const slice    = filtered.slice(start, end);

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
    const gi = start + idx;  /* global index into filtered */
    const langBadge = d.lang === "grc"
      ? `<span class="lang-badge badge-grc">GRC</span>`
      : d.lang === "lat"
      ? `<span class="lang-badge badge-lat">LAT</span>`
      : d.lang === "eng"
      ? `<span class="lang-badge badge-eng">ENG</span>`
      : `<span class="lang-badge badge-btn" title="${esc(d.lang.toUpperCase())}">${esc(d.lang.toUpperCase())}</span>`;
    const arTranslit = d.ar_translit ? `<span class="ar-translit">${esc(d.ar_translit)}</span>` : "";
    const tgtIpa     = d.tgt_ipa     ? `<span class="tgt-ipa">${esc(d.tgt_ipa)}</span>`         : "";

    rows.push(`<tr class="data-row" onclick="toggleDetail(${gi})" data-gi="${gi}">
      <td>${scorePill(d.score)}</td>
      <td><span class="ar-text">${esc(d.ar)}</span>${arTranslit}</td>
      <td><span class="meaning-text">${esc(trunc(d.ar_def, 80))}</span></td>
      <td><span class="tgt-word">${esc(d.tgt)}</span>${tgtIpa}</td>
      <td><span class="meaning-text">${esc(trunc(d.tgt_gloss, 80))}</span></td>
      <td>${langBadge}</td>
      <td>${methodBadge(d.method)}</td>
      <td><span class="reasoning-cell">${esc(trunc(d.reasoning, 100))}</span></td>
      <td><span class="model-text">${esc(d.model)}</span></td>
    </tr>`);

    if (expandedRow === gi) {
      rows.push(`<tr class="detail-row">
        <td colspan="9">
          <div class="detail-panel">
            <div>
              <div class="dp-label">Arabic Definition</div>
              <div class="dp-value">${esc(d.ar_def || "(no definition available)")}</div>
            </div>
            <div>
              <div class="dp-label">Target Gloss</div>
              <div class="dp-value">${esc(d.tgt_gloss || "(no gloss available)")}${d.tgt_ipa ? " &mdash; <em>" + esc(d.tgt_ipa) + "</em>" : ""}</div>
            </div>
            <div class="detail-reasoning">
              <div class="dp-label">Reasoning</div>
              <div class="dp-value">${esc(d.reasoning || "(no reasoning)")}</div>
            </div>
            <div>
              <div class="dp-label">Score / Method / Model</div>
              <div class="dp-value">${d.score.toFixed(3)} &mdash; ${esc(d.method)} &mdash; ${esc(d.model)}</div>
            </div>
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
  const cols = ["ar","tgt","lang","score","method","ar_def","ar_translit","tgt_ipa","tgt_gloss","reasoning","model"];
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
    # Build lookup tables
    ipa_grc  = build_ipa_lookup("grc")
    ipa_lat  = build_ipa_lookup("lat")
    ar_lookup = build_arabic_lookup()

    # Load & enrich discoveries
    records = load_discoveries(ipa_grc, ipa_lat, ar_lookup)
    if not records:
        print("[error] No records loaded — exiting", file=sys.stderr)
        sys.exit(1)

    total     = len(records)
    ipa_cov   = sum(1 for r in records if r["tgt_ipa"])
    ar_cov    = sum(1 for r in records if r["ar_def"])
    print(f"\nTotal embedded : {total:,}", file=sys.stderr)
    print(f"IPA coverage   : {ipa_cov:,} / {total:,}  ({100*ipa_cov/total:.1f}%)", file=sys.stderr)
    print(f"AR def coverage: {ar_cov:,} / {total:,}  ({100*ar_cov/total:.1f}%)", file=sys.stderr)

    # Render HTML
    data_json = json.dumps(records, ensure_ascii=False)
    html = HTML_TEMPLATE.replace("__DATA_PLACEHOLDER__", data_json)

    out_path = LV2 / "outputs" / "discoveries_dashboard.html"
    out_path.write_text(html, encoding="utf-8")

    size_kb = out_path.stat().st_size / 1024
    print(f"\nDashboard -> {out_path}  ({size_kb:.0f} KB)", file=sys.stderr)
    if size_kb < 100:
        print("[warn] Dashboard is smaller than expected (<100 KB)", file=sys.stderr)


if __name__ == "__main__":
    main()
