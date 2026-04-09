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
    records = []
    for lang, fname in [("grc", "eye2_final_grc.jsonl"), ("lat", "eye2_final_lat.jsonl")]:
        path = LV2 / "outputs" / fname
        if not path.exists():
            print(f"[warn] {path} not found, skipping", file=sys.stderr)
            continue
        ipa_map = ipa_grc if lang == "grc" else ipa_lat
        count = 0
        ipa_hits = 0
        ar_hits  = 0
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                r = json.loads(line)
                if r.get("semantic_score", 0) < 0.3:
                    continue

                ar   = r.get("source_lemma", "")
                tgt  = r.get("target_lemma", "")
                method = (r.get("method", "weak") or "weak").strip()

                # IPA + gloss enrichment
                tgt_ipa   = ""
                tgt_gloss = ""
                if tgt in ipa_map:
                    entry     = ipa_map[tgt]
                    tgt_ipa   = (entry.get("ipa")   or "").strip()
                    tgt_gloss = (entry.get("gloss")  or "").strip()
                    ipa_hits += 1

                # Arabic definition enrichment
                ar_def      = ""
                ar_translit = ""
                if ar in ar_lookup:
                    ar_def      = ar_lookup[ar]["def"]
                    ar_translit = ar_lookup[ar]["translit"]
                    ar_hits += 1

                records.append({
                    "ar":          ar,
                    "tgt":         tgt,
                    "score":       round(r.get("semantic_score", 0), 3),
                    "lang":        lang,
                    "method":      method,
                    "reasoning":   (r.get("reasoning", "") or "").strip(),
                    "model":       (r.get("final_model") or r.get("model") or "unknown").strip(),
                    "tgt_ipa":     tgt_ipa,
                    "tgt_gloss":   tgt_gloss[:120] if tgt_gloss else "",
                    "ar_def":      ar_def[:160]     if ar_def     else "",
                    "ar_translit": ar_translit,
                })
                count += 1

        ipa_pct = f"{100*ipa_hits/count:.1f}%" if count else "n/a"
        ar_pct  = f"{100*ar_hits/count:.1f}%"  if count else "n/a"
        print(
            f"[{lang}] {count} records  |  IPA coverage: {ipa_pct}"
            f"  |  AR def coverage: {ar_pct}",
            file=sys.stderr,
        )

    # ── Beyond the Name gold reference pairs ───────────────────────────────────
    btn_path = LV2 / "outputs" / "eye2_final_beyond_name.jsonl"
    if btn_path.exists():
        btn_count = 0
        ar_hits_btn = 0
        with open(btn_path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                r = json.loads(line)
                if r.get("semantic_score", 0) < 0.3:
                    continue

                ar     = r.get("source_lemma", "")
                tgt    = r.get("target_lemma", "")
                method = (r.get("method", "weak") or "weak").strip()

                # Arabic definition enrichment (no IPA map for BTN)
                ar_def      = ""
                ar_translit = ""
                if ar in ar_lookup:
                    ar_def      = ar_lookup[ar]["def"]
                    ar_translit = ar_lookup[ar]["translit"]
                    ar_hits_btn += 1

                records.append({
                    "ar":          ar,
                    "tgt":         tgt,
                    "score":       round(r.get("semantic_score", 0), 3),
                    "lang":        "btn",
                    "sub_lang":    (r.get("target_lang") or "").strip(),
                    "method":      method,
                    "reasoning":   (r.get("reasoning", "") or "").strip(),
                    "model":       (r.get("model") or "unknown").strip(),
                    "tgt_ipa":     "",
                    "tgt_gloss":   "",
                    "ar_def":      ar_def[:160] if ar_def else "",
                    "ar_translit": ar_translit,
                })
                btn_count += 1

        ar_pct_btn = f"{100*ar_hits_btn/btn_count:.1f}%" if btn_count else "n/a"
        print(
            f"[btn] {btn_count} records  |  AR def coverage: {ar_pct_btn}",
            file=sys.stderr,
        )
    else:
        print(f"[warn] {btn_path} not found, skipping BTN", file=sys.stderr)

    records.sort(key=lambda x: -x["score"])
    return records


# ── HTML template ──────────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" dir="ltr" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Juthoor LV2 — Cognate Discoveries</title>
<style>
/* ── CSS custom properties / themes ── */
:root, [data-theme="light"] {
  --bg:         #ffffff;
  --bg-alt:     #f8f9fa;
  --bg-panel:   #f1f3f5;
  --text:        #212529;
  --text-muted:  #6c757d;
  --border:      #dee2e6;
  --card-bg:     #ffffff;
  --card-shadow: 0 1px 4px rgba(0,0,0,0.08);
  --header-bg:   #2d6a4f;
  --header-text: #ffffff;
  --chip-bg:     #e9ecef;
  --chip-text:   #495057;
  --chip-active-bg:   #2d6a4f;
  --chip-active-text: #ffffff;
  --input-bg:    #ffffff;
  --input-border:#ced4da;
  --table-hover: #f0f4f0;
  --score-hi-bg:  #d4edda; --score-hi-text:  #155724;
  --score-med-bg: #fff3cd; --score-med-text: #856404;
  --score-lo-bg:  #e9ecef; --score-lo-text:  #495057;
  --badge-grc-bg: #cce5ff; --badge-grc-text: #004085;
  --badge-lat-bg: #f8d7da; --badge-lat-text: #721c24;
  --badge-btn-bg: #fef3c7; --badge-btn-text: #92400e;
  --chart-btn: #d4a017;
  --stat-btn-color: #b07d10;
  --method-masadiq-bg:  #d1ecf1; --method-masadiq-text:  #0c5460;
  --method-mafahim-bg:  #e2d9f3; --method-mafahim-text:  #4a1d7c;
  --method-combined-bg: #fce8d5; --method-combined-text: #8a3200;
  --method-weak-bg:     #e9ecef; --method-weak-text:     #495057;
  --chart-grc: #1d6fb5;
  --chart-lat: #c0392b;
  --chart-track: #dee2e6;
}
[data-theme="warm"] {
  --bg:         #fdf6e3;
  --bg-alt:     #f5ead0;
  --bg-panel:   #ede3c8;
  --text:        #3d2b1f;
  --text-muted:  #7a5c3a;
  --border:      #c8b08a;
  --card-bg:     #fdf6e3;
  --card-shadow: 0 1px 4px rgba(80,40,0,0.10);
  --header-bg:   #2d6a4f;
  --header-text: #ffffff;
  --chip-bg:     #e8dcc2;
  --chip-text:   #5c4827;
  --chip-active-bg:   #5c4827;
  --chip-active-text: #fdf6e3;
  --input-bg:    #fdf6e3;
  --input-border:#b89c6a;
  --table-hover: #f0e6cc;
  --score-hi-bg:  #c8e6c9; --score-hi-text:  #1b5e20;
  --score-med-bg: #ffe0b2; --score-med-text: #e65100;
  --score-lo-bg:  #e8dcc2; --score-lo-text:  #5c4827;
  --badge-grc-bg: #b3d9ff; --badge-grc-text: #003366;
  --badge-lat-bg: #ffd0d0; --badge-lat-text: #660000;
  --badge-btn-bg: #fde68a; --badge-btn-text: #78350f;
  --chart-btn: #d4a017;
  --stat-btn-color: #b07d10;
  --method-masadiq-bg:  #b2ebf2; --method-masadiq-text:  #00363a;
  --method-mafahim-bg:  #d7bdf7; --method-mafahim-text:  #2d0060;
  --method-combined-bg: #ffd9b0; --method-combined-text: #7a2200;
  --method-weak-bg:     #e8dcc2; --method-weak-text:     #5c4827;
  --chart-grc: #1d6fb5;
  --chart-lat: #c0392b;
  --chart-track: #c8b08a;
}
[data-theme="dark"] {
  --bg:         #1e1e2e;
  --bg-alt:     #181825;
  --bg-panel:   #313244;
  --text:        #e0e0e0;
  --text-muted:  #9090a0;
  --border:      #45475a;
  --card-bg:     #313244;
  --card-shadow: 0 1px 4px rgba(0,0,0,0.40);
  --header-bg:   #2d6a4f;
  --header-text: #ffffff;
  --chip-bg:     #313244;
  --chip-text:   #b0b0c0;
  --chip-active-bg:   #2d6a4f;
  --chip-active-text: #ffffff;
  --input-bg:    #313244;
  --input-border:#45475a;
  --table-hover: #2a2a40;
  --score-hi-bg:  #1a3a20; --score-hi-text:  #50d080;
  --score-med-bg: #2e2010; --score-med-text: #ffa040;
  --score-lo-bg:  #31324400; --score-lo-text:  #707080;
  --badge-grc-bg: #1a2a50; --badge-grc-text: #80b0ff;
  --badge-lat-bg: #3a1a1a; --badge-lat-text: #ff9080;
  --badge-btn-bg: #3a2800; --badge-btn-text: #f6c842;
  --chart-btn: #d4a017;
  --stat-btn-color: #f6c842;
  --method-masadiq-bg:  #0c2e36; --method-masadiq-text:  #5ecfde;
  --method-mafahim-bg:  #2a1a44; --method-mafahim-text:  #c090ff;
  --method-combined-bg: #321a0a; --method-combined-text: #ffaa60;
  --method-weak-bg:     #313244; --method-weak-text:     #707080;
  --chart-grc: #4a9eff;
  --chart-lat: #ff6060;
  --chart-track: #45475a;
}

/* ── Reset ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  transition: background 0.2s, color 0.2s;
}

/* ── Header ── */
header {
  background: var(--header-bg);
  padding: 1rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.header-left h1 {
  font-size: 1.45rem;
  font-weight: 700;
  color: var(--header-text);
  letter-spacing: 0.02em;
}
.header-left p {
  font-size: 0.85rem;
  color: rgba(255,255,255,0.75);
  margin-top: 0.2rem;
}
.theme-switcher {
  display: flex;
  gap: 0.35rem;
}
.theme-btn {
  background: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.3);
  color: rgba(255,255,255,0.85);
  padding: 0.3rem 0.65rem;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 500;
  transition: background 0.15s;
}
.theme-btn:hover { background: rgba(255,255,255,0.25); }
.theme-btn.active { background: rgba(255,255,255,0.30); border-color: rgba(255,255,255,0.7); color: #fff; font-weight: 700; }

/* ── Stats bar ── */
#stats-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 1rem 2rem;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border);
}
.stat-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  box-shadow: var(--card-shadow);
  border-radius: 8px;
  padding: 0.6rem 1.1rem;
  min-width: 100px;
  text-align: center;
  flex: 1 1 100px;
  max-width: 160px;
}
.stat-label {
  font-size: 0.68rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  font-weight: 600;
}
.stat-value {
  font-size: 1.55rem;
  font-weight: 700;
  margin-top: 0.15rem;
  color: var(--text);
}
.stat-grc .stat-value  { color: #1d6fb5; }
.stat-lat .stat-value  { color: #c0392b; }
.stat-btn .stat-value  { color: var(--stat-btn-color, #b07d10); }
.stat-hi  .stat-value  { color: #1e7e34; }
.stat-med .stat-value  { color: #d08000; }

/* ── Quick filter chips ── */
#chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  padding: 0.75rem 2rem;
  background: var(--bg);
  border-bottom: 1px solid var(--border);
}
.chip {
  background: var(--chip-bg);
  color: var(--chip-text);
  border: 1px solid var(--border);
  padding: 0.3rem 0.8rem;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
  transition: background 0.15s, color 0.15s;
  user-select: none;
}
.chip:hover { opacity: 0.85; }
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
  gap: 1rem;
  padding: 0.75rem 2rem;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border);
}
.filter-group {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}
.filter-label {
  font-size: 0.78rem;
  color: var(--text-muted);
  white-space: nowrap;
  font-weight: 500;
}
input[type="range"] {
  -webkit-appearance: none;
  appearance: none;
  width: 130px;
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
  background: #2d6a4f;
  cursor: pointer;
  border: 2px solid var(--bg);
  box-shadow: 0 0 0 1px #2d6a4f;
}
#score-val {
  font-size: 0.82rem;
  color: #2d6a4f;
  font-weight: 700;
  min-width: 2.8rem;
}
select, #search-input {
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  color: var(--text);
  padding: 0.3rem 0.6rem;
  border-radius: 6px;
  font-size: 0.82rem;
  outline: none;
  transition: border-color 0.15s;
}
select:focus, #search-input:focus { border-color: #2d6a4f; }
#search-input { width: 210px; }
#search-input::placeholder { color: var(--text-muted); opacity: 0.6; }

/* ── Chart ── */
#chart-section {
  padding: 1rem 2rem 0.75rem;
  background: var(--bg);
  border-bottom: 1px solid var(--border);
}
#chart-section h3 {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  margin-bottom: 0.6rem;
  font-weight: 600;
}
.chart-row {
  display: flex;
  align-items: center;
  margin-bottom: 0.3rem;
  gap: 0.5rem;
}
.chart-band-label {
  font-size: 0.7rem;
  color: var(--text-muted);
  width: 58px;
  text-align: right;
  flex-shrink: 0;
}
.chart-bars {
  display: flex;
  height: 13px;
  flex: 1;
  border-radius: 3px;
  overflow: hidden;
  background: var(--chart-track);
}
.chart-bar-grc { background: var(--chart-grc); height: 100%; transition: width 0.25s; }
.chart-bar-lat { background: var(--chart-lat); height: 100%; transition: width 0.25s; }
.chart-bar-btn { background: var(--chart-btn); height: 100%; transition: width 0.25s; }
.chart-count {
  font-size: 0.68rem;
  color: var(--text-muted);
  width: 46px;
  flex-shrink: 0;
}
.chart-legend {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
}
.legend-dot {
  display: inline-block;
  width: 10px; height: 10px;
  border-radius: 50%;
  margin-right: 4px;
  vertical-align: middle;
}

/* ── Table section ── */
#table-section { padding: 1rem 2rem 2rem; }

#pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}
#page-info {
  font-size: 0.82rem;
  color: var(--text-muted);
}
.page-btn {
  background: var(--card-bg);
  border: 1px solid var(--border);
  color: var(--text-muted);
  padding: 0.3rem 0.8rem;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.82rem;
  transition: background 0.15s;
}
.page-btn:hover:not(:disabled) { background: var(--bg-panel); color: var(--text); }
.page-btn:disabled { opacity: 0.35; cursor: default; }
.page-btn-group { display: flex; gap: 0.4rem; align-items: center; }
.export-btn {
  background: var(--card-bg);
  border: 1px solid var(--border);
  color: #2d6a4f;
  padding: 0.3rem 0.8rem;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  transition: background 0.15s;
}
.export-btn:hover { background: var(--bg-panel); }

/* ── Data table ── */
#data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
}
#data-table th {
  background: var(--bg-panel);
  color: var(--text-muted);
  font-weight: 600;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.55rem 0.7rem;
  text-align: left;
  border-bottom: 2px solid var(--border);
  white-space: nowrap;
  user-select: none;
  border-top: 1px solid var(--border);
}
#data-table th.sortable { cursor: pointer; }
#data-table th.sortable:hover { color: var(--text); }
#data-table th.sort-asc::after  { content: " \25B2"; font-size: 0.6rem; }
#data-table th.sort-desc::after { content: " \25BC"; font-size: 0.6rem; }

#data-table td {
  padding: 0.5rem 0.7rem;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}
#data-table tr:nth-child(even) > td { background: var(--bg-alt); }
#data-table tr.data-row:hover > td { background: var(--table-hover); cursor: pointer; }
#data-table tr.detail-row > td {
  background: var(--bg-panel);
  border-left: 3px solid #2d6a4f;
  padding: 0.75rem 1rem;
}

/* ── Score pill ── */
.score-pill {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 10px;
  font-weight: 700;
  font-size: 0.8rem;
  min-width: 44px;
  text-align: center;
  border: 1px solid transparent;
}
.score-hi  { background: var(--score-hi-bg);  color: var(--score-hi-text);  }
.score-med { background: var(--score-med-bg); color: var(--score-med-text); }
.score-lo  { background: var(--score-lo-bg);  color: var(--score-lo-text);  }

/* ── Arabic text ── */
.ar-text {
  font-family: "Segoe UI", "Noto Naskh Arabic", "Arabic Typesetting",
               "Traditional Arabic", "Amiri", serif;
  font-size: 1.25rem;
  direction: rtl;
  unicode-bidi: bidi-override;
  color: var(--text);
  line-height: 1.5;
  display: block;
}
.ar-translit {
  font-size: 0.7rem;
  color: var(--text-muted);
  display: block;
  margin-top: 0.1rem;
  font-style: italic;
}

/* ── Target word ── */
.tgt-word { font-size: 0.9rem; color: var(--text); font-weight: 500; display: block; }
.tgt-ipa  { font-size: 0.7rem; color: var(--text-muted); font-style: italic; display: block; margin-top: 0.1rem; }

/* ── Meaning text ── */
.meaning-text { font-size: 0.78rem; color: var(--text-muted); }

/* ── Lang badge ── */
.lang-badge {
  display: inline-block;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.badge-grc { background: var(--badge-grc-bg); color: var(--badge-grc-text); }
.badge-lat { background: var(--badge-lat-bg); color: var(--badge-lat-text); }
.badge-btn { background: var(--badge-btn-bg); color: var(--badge-btn-text); }

/* ── Method badge ── */
.method-badge {
  display: inline-block;
  padding: 0.1rem 0.45rem;
  border-radius: 4px;
  font-size: 0.67rem;
  font-weight: 600;
  white-space: nowrap;
}
.method-masadiq  { background: var(--method-masadiq-bg);  color: var(--method-masadiq-text);  }
.method-mafahim  { background: var(--method-mafahim-bg);  color: var(--method-mafahim-text);  }
.method-combined { background: var(--method-combined-bg); color: var(--method-combined-text); }
.method-weak     { background: var(--method-weak-bg);     color: var(--method-weak-text);     }

/* ── Reasoning cell ── */
.reasoning-cell { font-size: 0.77rem; color: var(--text-muted); max-width: 260px; }

/* ── Model text ── */
.model-text { font-size: 0.68rem; color: var(--text-muted); white-space: nowrap; }

/* ── Detail panel ── */
.detail-panel {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  font-size: 0.82rem;
}
.detail-panel .dp-label {
  font-size: 0.68rem;
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.2rem;
}
.detail-panel .dp-value { color: var(--text); line-height: 1.5; }
.detail-reasoning { grid-column: 1 / -1; }

/* ── No results ── */
#no-results {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
  font-size: 0.9rem;
  display: none;
}

/* ── Export section ── */
#export-section { display: flex; gap: 0.5rem; align-items: center; }

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
  .detail-panel { grid-template-columns: 1fr; }
}
</style>
</head>
<body>

<header>
  <div class="header-left">
    <h1>Juthoor LV2 &mdash; Cognate Discoveries</h1>
    <p>Arabic &harr; Greek, Latin &amp; Gold Reference Pairs</p>
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
    <div class="stat-label">Gold Ref</div>
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
  <button class="chip active" data-chip="all"         onclick="setChip(this)">All</button>
  <button class="chip"        data-chip="top50"       onclick="setChip(this)">Top 50</button>
  <button class="chip"        data-chip="direct"      onclick="setChip(this)">Direct Loans</button>
  <button class="chip"        data-chip="hidden"      onclick="setChip(this)">Hidden Cognates</button>
  <button class="chip"        data-chip="grc"         onclick="setChip(this)">Greek</button>
  <button class="chip"        data-chip="lat"         onclick="setChip(this)">Latin</button>
  <button class="chip"        data-chip="btn"         onclick="setChip(this)" style="border-color:#d4a017;color:#92400e;">Gold Reference</button>
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
      <option value="">All</option>
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
  <div class="chart-legend" style="font-size:0.72rem; color:var(--text-muted); margin-top:0.3rem;">
    <span><span class="legend-dot" style="background:var(--chart-grc)"></span>Greek</span>
    <span><span class="legend-dot" style="background:var(--chart-lat)"></span>Latin</span>
    <span><span class="legend-dot" style="background:var(--chart-btn)"></span>Gold Ref</span>
  </div>
</div>

<div id="table-section">
  <div id="pagination">
    <span id="page-info"></span>
    <div style="display:flex;gap:0.75rem;align-items:center;flex-wrap:wrap;">
      <div id="export-section">
        <button class="export-btn" onclick="exportCSV()">Export CSV</button>
        <button class="export-btn" onclick="exportJSON()">Export JSON</button>
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
  const cls = sc >= 0.8 ? "score-hi" : sc >= 0.5 ? "score-med" : "score-lo";
  return `<span class="score-pill ${cls}">${sc.toFixed(3)}</span>`;
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
    if (chip === "btn" && d.lang !== "btn") return false;
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
  const btnN  = filtered.filter(d => d.lang === "btn").length;
  const hiN   = filtered.filter(d => d.score >= 0.8).length;
  const medN  = filtered.filter(d => d.score >= 0.6).length;
  document.getElementById("stat-total").textContent = total.toLocaleString();
  document.getElementById("stat-grc").textContent   = grcN.toLocaleString();
  document.getElementById("stat-lat").textContent   = latN.toLocaleString();
  document.getElementById("stat-btn").textContent   = btnN.toLocaleString();
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
    btn: filtered.filter(d => d.lang==="btn" && d.score>=lo && d.score<hi).length,
  }));
  const maxN = Math.max(...counts.map(c => c.grc + c.lat + c.btn), 1);
  container.innerHTML = counts.map((c, i) => {
    const gW = ((c.grc / maxN) * 100).toFixed(1);
    const lW = ((c.lat / maxN) * 100).toFixed(1);
    const bW = ((c.btn / maxN) * 100).toFixed(1);
    const tot = c.grc + c.lat + c.btn;
    return `<div class="chart-row">
      <span class="chart-band-label">${BAND_LABELS[i]}</span>
      <div class="chart-bars" title="Greek: ${c.grc}, Latin: ${c.lat}, Gold Ref: ${c.btn}">
        <div class="chart-bar-grc" style="width:${gW}%"></div>
        <div class="chart-bar-lat" style="width:${lW}%"></div>
        <div class="chart-bar-btn" style="width:${bW}%"></div>
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
      : `<span class="lang-badge badge-btn" title="Gold Reference">${esc((d.sub_lang || "btn").toUpperCase())}</span>`;
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
  const cols = ["ar","tgt","lang","sub_lang","score","method","ar_def","ar_translit","tgt_ipa","tgt_gloss","reasoning","model"];
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
