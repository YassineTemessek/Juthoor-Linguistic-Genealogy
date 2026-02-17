"""Juthoor LV2 — HTML Report Generator.

Reads a discovery leads JSONL file and produces a self-contained HTML report
with run summary, score distribution, component analysis, top leads table,
by-source grouping, and language pair matrix.

Usage:
    python report.py outputs/leads/discovery_YYYYMMDD_HHMMSS.jsonl
    python report.py <path> --output my_report.html --min-score 0.5 --top-n 500
    python report.py <path> --summary-only
"""
from __future__ import annotations

import argparse
import html
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_leads(path: Path, min_score: float = 0.0) -> list[dict[str, Any]]:
    leads: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if min_score > 0:
                hybrid = row.get("hybrid") or {}
                score = hybrid.get("combined_score", 0) or 0
                if score < min_score:
                    continue
            leads.append(row)
    return leads


# ---------------------------------------------------------------------------
# Statistics computation
# ---------------------------------------------------------------------------


def compute_stats(leads: list[dict[str, Any]]) -> dict[str, Any]:
    if not leads:
        return {}

    # Run metadata from first lead
    first = leads[0]
    run_id = first.get("run_id", "unknown")
    pair_id = first.get("pair_id")
    language_group = first.get("language_group")
    prov = first.get("provenance", {})
    models = prov.get("models", [])
    backend = "API" if any("api" in str(m).lower() for m in models) else "Local"

    # Source/target language summary
    src_langs: set[str] = set()
    tgt_langs: set[str] = set()
    for lead in leads:
        src = lead.get("source", {})
        tgt = lead.get("target", {})
        src_langs.add(f"{src.get('lang','')} {src.get('stage','')}".strip())
        tgt_langs.add(f"{tgt.get('lang','')} {tgt.get('stage','')}".strip())

    # Score tiers
    strong = medium = weak = 0
    for lead in leads:
        s = (lead.get("hybrid") or {}).get("combined_score", 0) or 0
        if s >= 0.7:
            strong += 1
        elif s >= 0.5:
            medium += 1
        else:
            weak += 1

    # Histogram (0.0–1.0 in 0.1 buckets)
    buckets = [0] * 10
    for lead in leads:
        s = (lead.get("hybrid") or {}).get("combined_score", 0) or 0
        idx = min(9, int(s * 10))
        buckets[idx] += 1

    # Component averages and null rates
    comp_totals: dict[str, float] = defaultdict(float)
    comp_counts: dict[str, int] = defaultdict(int)
    comp_nulls: dict[str, int] = defaultdict(int)
    score_totals: dict[str, float] = defaultdict(float)
    score_counts: dict[str, int] = defaultdict(int)

    for lead in leads:
        hybrid = lead.get("hybrid") or {}
        comps = hybrid.get("components", {})
        for k in ("orthography", "sound", "skeleton"):
            v = comps.get(k)
            if v is None:
                comp_nulls[k] += 1
            else:
                comp_totals[k] += float(v)
                comp_counts[k] += 1

        scores = lead.get("scores", {})
        for k in ("semantic", "form"):
            v = scores.get(k)
            if v is not None:
                score_totals[k] += float(v)
                score_counts[k] += 1
            else:
                comp_nulls[k] += 1

    def avg(k: str, totals: dict, counts: dict) -> float | None:
        return round(totals[k] / counts[k], 3) if counts.get(k) else None

    component_stats = {}
    for k in ("semantic", "form"):
        component_stats[k] = {
            "avg": avg(k, score_totals, score_counts),
            "null_rate": comp_nulls.get(k, 0),
        }
    for k in ("orthography", "sound", "skeleton"):
        component_stats[k] = {
            "avg": avg(k, comp_totals, comp_counts),
            "null_rate": comp_nulls.get(k, 0),
        }

    # Language pair matrix
    pair_totals: dict[tuple[str, str], float] = defaultdict(float)
    pair_counts: dict[tuple[str, str], int] = defaultdict(int)
    for lead in leads:
        src_lang = lead.get("source", {}).get("lang", "?")
        tgt_lang = lead.get("target", {}).get("lang", "?")
        s = (lead.get("hybrid") or {}).get("combined_score", 0) or 0
        pair_totals[(src_lang, tgt_lang)] += s
        pair_counts[(src_lang, tgt_lang)] += 1

    pair_matrix = {
        f"{k[0]}→{k[1]}": round(pair_totals[k] / pair_counts[k], 3)
        for k in pair_totals
    }

    # Category breakdown
    categories: dict[str, int] = defaultdict(int)
    for lead in leads:
        categories[lead.get("category", "unknown")] += 1

    return {
        "run_id": run_id,
        "pair_id": pair_id,
        "language_group": language_group,
        "models": models,
        "backend": backend,
        "src_langs": sorted(src_langs),
        "tgt_langs": sorted(tgt_langs),
        "total": len(leads),
        "strong": strong,
        "medium": medium,
        "weak": weak,
        "buckets": buckets,
        "component_stats": component_stats,
        "pair_matrix": pair_matrix,
        "categories": dict(categories),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


# ---------------------------------------------------------------------------
# HTML rendering helpers
# ---------------------------------------------------------------------------


def _e(text: Any) -> str:
    """HTML-escape a value."""
    return html.escape(str(text) if text is not None else "")


def _score_color(score: float | None) -> str:
    if score is None:
        return "#999"
    if score >= 0.7:
        return "#2d8a4e"
    if score >= 0.5:
        return "#c78a00"
    return "#c0392b"


def _score_badge(score: float | None) -> str:
    if score is None:
        return '<span style="color:#999">—</span>'
    color = _score_color(score)
    return f'<span style="color:{color};font-weight:600">{score:.3f}</span>'


def _lemma_span(lemma: str, lang: str) -> str:
    """Wrap lemma in RTL span for Arabic/Hebrew scripts."""
    rtl_langs = {"ara", "ara-qur", "heb", "akk", "uga", "gez", "syr", "syc", "arc"}
    if lang in rtl_langs:
        return f'<span dir="rtl" lang="{_e(lang)}" style="font-size:1.1em">{_e(lemma)}</span>'
    return _e(lemma)


# ---------------------------------------------------------------------------
# HTML sections
# ---------------------------------------------------------------------------


def _render_summary(stats: dict[str, Any]) -> str:
    total = stats["total"]
    strong = stats["strong"]
    medium = stats["medium"]
    weak = stats["weak"]
    src = ", ".join(stats["src_langs"]) or "—"
    tgt = ", ".join(stats["tgt_langs"]) or "—"

    return f"""
<section class="card" id="summary">
  <h2>Run Summary</h2>
  <table class="info-table">
    <tr><td>Run ID</td><td><code>{_e(stats['run_id'])}</code></td></tr>
    <tr><td>Pair ID</td><td><code>{_e(stats['pair_id'] or '—')}</code></td></tr>
    <tr><td>Language group</td><td>{_e(stats['language_group'] or '—')}</td></tr>
    <tr><td>Source</td><td>{_e(src)}</td></tr>
    <tr><td>Targets</td><td>{_e(tgt)}</td></tr>
    <tr><td>Models</td><td>{_e(', '.join(stats['models']))}</td></tr>
    <tr><td>Backend</td><td>{_e(stats['backend'])}</td></tr>
    <tr><td>Total leads</td><td><strong>{total:,}</strong></td></tr>
    <tr><td>Score tiers</td><td>
      <span style="color:#2d8a4e">&#9632; Strong (&ge;0.7): {strong:,}</span> &nbsp;
      <span style="color:#c78a00">&#9632; Medium (0.5–0.7): {medium:,}</span> &nbsp;
      <span style="color:#c0392b">&#9632; Weak (&lt;0.5): {weak:,}</span>
    </td></tr>
    <tr><td>Generated</td><td>{_e(stats['generated_at'])}</td></tr>
  </table>
</section>"""


def _render_histogram(stats: dict[str, Any]) -> str:
    buckets = stats["buckets"]
    total = stats["total"] or 1
    max_count = max(buckets) or 1

    bars = ""
    labels = [f"{i/10:.1f}–{(i+1)/10:.1f}" for i in range(10)]
    for i, (label, count) in enumerate(zip(labels, buckets)):
        pct = count / total * 100
        bar_pct = count / max_count * 100
        color = _score_color(i / 10)
        bars += f"""
      <div class="hist-row">
        <div class="hist-label">{label}</div>
        <div class="hist-bar-wrap">
          <div class="hist-bar" style="width:{bar_pct:.1f}%;background:{color}"></div>
        </div>
        <div class="hist-count">{count:,} ({pct:.1f}%)</div>
      </div>"""

    return f"""
<section class="card" id="histogram">
  <h2>Score Distribution</h2>
  <div class="histogram">{bars}
  </div>
</section>"""


def _render_component_table(stats: dict[str, Any]) -> str:
    cs = stats["component_stats"]
    total = stats["total"] or 1

    rows = ""
    for comp in ("semantic", "form", "orthography", "sound", "skeleton"):
        info = cs.get(comp, {})
        avg = info.get("avg")
        nulls = info.get("null_rate", 0)
        null_pct = nulls / total * 100
        avg_str = f"{avg:.3f}" if avg is not None else "—"
        null_str = f"{nulls:,} ({null_pct:.1f}%)"
        null_style = ' style="color:#c0392b"' if null_pct > 10 else ""
        rows += f"""
    <tr>
      <td><strong>{_e(comp)}</strong></td>
      <td style="text-align:right">{avg_str}</td>
      <td{null_style} style="text-align:right">{null_str}</td>
    </tr>"""

    return f"""
<section class="card" id="components">
  <h2>Component Score Analysis</h2>
  <table class="data-table">
    <thead><tr><th>Component</th><th>Avg Score</th><th>Null / Missing</th></tr></thead>
    <tbody>{rows}
    </tbody>
  </table>
  <p class="note">Null rate &gt;10% (red) indicates missing data for that component (e.g. no IPA for sound score).</p>
</section>"""


def _render_categories(stats: dict[str, Any]) -> str:
    cats = stats.get("categories", {})
    if not cats:
        return ""
    rows = ""
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        rows += f"<tr><td>{_e(cat)}</td><td style='text-align:right'>{count:,}</td></tr>"
    return f"""
<section class="card" id="categories">
  <h2>Category Breakdown</h2>
  <table class="data-table">
    <thead><tr><th>Category</th><th>Count</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <p class="note"><strong>strong_union</strong>: found by both semantic &amp; form models — highest confidence.<br>
  <strong>semantic_only</strong>: meaning match without orthographic similarity.<br>
  <strong>form_only</strong>: shape/sound match without semantic alignment.</p>
</section>"""


def _render_leads_table(leads: list[dict[str, Any]], top_n: int) -> str:
    subset = leads[:top_n]
    rows = ""
    for rank, lead in enumerate(subset, 1):
        src = lead.get("source", {})
        tgt = lead.get("target", {})
        hybrid = lead.get("hybrid") or {}
        scores = lead.get("scores", {})
        comps = hybrid.get("components", {})
        combined = hybrid.get("combined_score")
        family_boost = hybrid.get("family_boost_applied", False)

        src_ipa = _e(src.get("ipa") or "")
        tgt_ipa = _e(tgt.get("ipa") or "")
        src_lemma = _lemma_span(src.get("lemma") or "", src.get("lang") or "")
        tgt_lemma = _lemma_span(tgt.get("lemma") or "", tgt.get("lang") or "")

        src_tip = f' title="IPA: {src_ipa}"' if src_ipa else ""
        tgt_tip = f' title="IPA: {tgt_ipa}"' if tgt_ipa else ""

        cat = _e(lead.get("category", ""))
        cat_abbr = {"strong_union": "SU", "semantic_only": "SEM", "form_only": "FORM"}.get(
            lead.get("category", ""), cat
        )

        family_marker = ' <span title="Same language family" style="color:#2d8a4e;font-size:0.8em">&#9650;</span>' if family_boost else ""

        rows += f"""
    <tr>
      <td style="text-align:right;color:#666">{rank}</td>
      <td{src_tip}>{src_lemma}</td>
      <td><code>{_e(src.get('lang',''))}</code></td>
      <td{tgt_tip}>{tgt_lemma}</td>
      <td><code>{_e(tgt.get('lang',''))}</code></td>
      <td style="text-align:right">{_score_badge(scores.get('semantic'))}</td>
      <td style="text-align:right">{_score_badge(scores.get('form'))}</td>
      <td style="text-align:right">{_score_badge(comps.get('sound'))}</td>
      <td style="text-align:right">{_score_badge(comps.get('skeleton'))}</td>
      <td style="text-align:right">{_score_badge(combined)}{family_marker}</td>
      <td><span class="cat cat-{_e(lead.get('category',''))}">{cat_abbr}</span></td>
    </tr>"""

    return f"""
<section class="card" id="leads">
  <h2>Top {top_n:,} Leads <span class="note">(click column header to sort)</span></h2>
  <div style="overflow-x:auto">
  <table class="data-table sortable" id="leads-table">
    <thead>
      <tr>
        <th>#</th>
        <th>Source</th><th>Lang</th>
        <th>Target</th><th>Lang</th>
        <th>Semantic</th><th>Form</th><th>Sound</th><th>Skeleton</th>
        <th>Hybrid &#8645;</th><th>Cat</th>
      </tr>
    </thead>
    <tbody>{rows}
    </tbody>
  </table>
  </div>
  <p class="note">Hover over a lemma to see its IPA. &#9650; = same language family boost applied.</p>
</section>"""


def _render_by_source(leads: list[dict[str, Any]], top_sources: int = 50) -> str:
    # Group by source lemma
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for lead in leads:
        src = lead.get("source", {})
        key = f"{src.get('lang','?')}:{src.get('lemma','?')}"
        by_source[key].append(lead)

    # Sort sources by best score desc, take top N
    def best_score(group: list[dict[str, Any]]) -> float:
        return max(
            ((l.get("hybrid") or {}).get("combined_score") or 0) for l in group
        )

    top_keys = sorted(by_source, key=lambda k: best_score(by_source[k]), reverse=True)[:top_sources]

    blocks = ""
    for key in top_keys:
        group = sorted(
            by_source[key],
            key=lambda l: (l.get("hybrid") or {}).get("combined_score") or 0,
            reverse=True,
        )[:5]
        first = group[0].get("source", {})
        lemma_display = _lemma_span(first.get("lemma") or key, first.get("lang") or "")
        lang_code = _e(first.get("lang", ""))
        ipa_str = _e(first.get("ipa") or "")
        ipa_part = f" <span style='color:#666;font-size:0.9em'>/{ipa_str}/</span>" if ipa_str else ""

        rows = ""
        for i, lead in enumerate(group, 1):
            tgt = lead.get("target", {})
            hybrid = lead.get("hybrid") or {}
            comps = hybrid.get("components", {})
            combined = hybrid.get("combined_score")
            tgt_lemma = _lemma_span(tgt.get("lemma") or "", tgt.get("lang") or "")
            tgt_ipa = _e(tgt.get("ipa") or "")
            snd = comps.get("sound")
            skel = comps.get("skeleton")
            snd_str = f"{snd:.2f}" if snd is not None else "—"
            skel_str = f"{skel:.2f}" if skel is not None else "—"
            rows += f"""
          <tr>
            <td style="color:#666;padding-right:8px">{i}.</td>
            <td>{tgt_lemma}</td>
            <td><code style="font-size:0.85em">{_e(tgt.get('lang',''))}</code></td>
            <td style="color:#666;font-size:0.9em">/{tgt_ipa}/</td>
            <td style="text-align:right">{_score_badge(combined)}</td>
            <td style="text-align:right;color:#666;font-size:0.9em">snd:{snd_str}</td>
            <td style="text-align:right;color:#666;font-size:0.9em">skel:{skel_str}</td>
          </tr>"""

        blocks += f"""
  <details>
    <summary>
      <strong>{lemma_display}</strong>{ipa_part}
      <code style="font-size:0.8em;color:#666;margin-left:8px">{lang_code}</code>
      <span style="margin-left:8px;color:#999;font-size:0.85em">{len(by_source[key])} matches</span>
    </summary>
    <table style="margin:8px 0 4px 16px;border-collapse:collapse">{rows}
    </table>
  </details>"""

    return f"""
<section class="card" id="by-source">
  <h2>By Source Word <span class="note">(top {top_sources} source words, top 5 matches each)</span></h2>
  <p class="note">Click a word to expand its best matches. Scores show hybrid combined, sound, and consonant skeleton similarity.</p>
{blocks}
</section>"""


def _render_pair_matrix(stats: dict[str, Any]) -> str:
    matrix = stats.get("pair_matrix", {})
    if not matrix:
        return ""

    src_langs = sorted({k.split("→")[0] for k in matrix})
    tgt_langs = sorted({k.split("→")[1] for k in matrix})

    header = "<tr><th>Source → Target</th>" + "".join(f"<th>{_e(t)}</th>" for t in tgt_langs) + "</tr>"
    body = ""
    for s in src_langs:
        cells = ""
        for t in tgt_langs:
            v = matrix.get(f"{s}→{t}")
            if v is None:
                cells += "<td style='color:#ccc'>—</td>"
            else:
                color = _score_color(v)
                cells += f'<td style="text-align:center;color:{color};font-weight:600">{v:.3f}</td>'
        body += f"<tr><td><code>{_e(s)}</code></td>{cells}</tr>"

    return f"""
<section class="card" id="matrix">
  <h2>Language Pair Matrix <span class="note">(avg hybrid score)</span></h2>
  <div style="overflow-x:auto">
  <table class="data-table">
    <thead>{header}</thead>
    <tbody>{body}</tbody>
  </table>
  </div>
  <p class="note">Higher scores = stronger average similarity between the two language corpora in this run.</p>
</section>"""


# ---------------------------------------------------------------------------
# JavaScript for sortable table
# ---------------------------------------------------------------------------

_SORT_JS = """
<script>
(function() {
  function sortTable(table, col, asc) {
    var tbody = table.querySelector('tbody');
    var rows = Array.from(tbody.querySelectorAll('tr'));
    rows.sort(function(a, b) {
      var av = a.cells[col] ? a.cells[col].innerText.trim() : '';
      var bv = b.cells[col] ? b.cells[col].innerText.trim() : '';
      var an = parseFloat(av), bn = parseFloat(bv);
      if (!isNaN(an) && !isNaN(bn)) return asc ? an - bn : bn - an;
      return asc ? av.localeCompare(bv) : bv.localeCompare(av);
    });
    rows.forEach(function(r) { tbody.appendChild(r); });
  }
  document.querySelectorAll('table.sortable thead th').forEach(function(th, i) {
    th.style.cursor = 'pointer';
    th.title = 'Click to sort';
    var asc = false;
    th.addEventListener('click', function() {
      asc = !asc;
      var table = th.closest('table');
      sortTable(table, i, asc);
      table.querySelectorAll('thead th').forEach(function(h) {
        h.style.background = '';
      });
      th.style.background = '#e8f4fd';
    });
  });
})();
</script>
"""

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

_CSS = """
<style>
*, *::before, *::after { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 14px; line-height: 1.6; color: #2c2c2c;
  margin: 0; padding: 0; background: #f4f6f8;
}
header {
  background: #1a2e4a; color: white; padding: 20px 32px;
  border-bottom: 3px solid #c0392b;
}
header h1 { margin: 0; font-size: 1.5em; font-weight: 700; }
header p  { margin: 4px 0 0; opacity: 0.7; font-size: 0.9em; }
nav {
  background: #1a2e4a; padding: 0 32px 12px;
  display: flex; gap: 20px; flex-wrap: wrap;
}
nav a { color: #a8c4e0; text-decoration: none; font-size: 0.85em; }
nav a:hover { color: white; }
main { max-width: 1200px; margin: 24px auto; padding: 0 16px 48px; }
.card {
  background: white; border-radius: 8px; padding: 20px 24px;
  margin-bottom: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
h2 { font-size: 1.1em; margin: 0 0 16px; color: #1a2e4a;
     border-bottom: 2px solid #e8ecf0; padding-bottom: 8px; }
.info-table { border-collapse: collapse; width: 100%; }
.info-table td { padding: 5px 12px 5px 0; vertical-align: top; }
.info-table td:first-child { color: #666; width: 160px; white-space: nowrap; }
.data-table { border-collapse: collapse; width: 100%; font-size: 0.9em; }
.data-table th {
  background: #f0f4f8; padding: 8px 10px; text-align: left;
  border-bottom: 2px solid #dde3ea; font-weight: 600; white-space: nowrap;
}
.data-table td { padding: 6px 10px; border-bottom: 1px solid #edf0f4; }
.data-table tr:hover td { background: #f8fafc; }
.histogram { display: flex; flex-direction: column; gap: 6px; }
.hist-row { display: flex; align-items: center; gap: 8px; }
.hist-label { width: 80px; color: #555; font-size: 0.85em; text-align: right; flex-shrink: 0; }
.hist-bar-wrap { flex: 1; background: #edf0f4; border-radius: 3px; height: 18px; overflow: hidden; }
.hist-bar { height: 100%; border-radius: 3px; transition: width 0.3s; }
.hist-count { width: 110px; color: #555; font-size: 0.85em; flex-shrink: 0; }
.note { color: #888; font-size: 0.85em; margin-top: 10px; }
code { background: #f0f4f8; padding: 1px 5px; border-radius: 3px; font-size: 0.9em; }
details { border: 1px solid #e8ecf0; border-radius: 6px; margin: 4px 0; padding: 0; }
details[open] { background: #f8fafc; }
summary {
  padding: 8px 14px; cursor: pointer; list-style: none; display: flex;
  align-items: center; gap: 4px; border-radius: 6px;
}
summary::-webkit-details-marker { display: none; }
summary:hover { background: #f0f4f8; }
.cat { font-size: 0.78em; padding: 2px 6px; border-radius: 10px; font-weight: 600; }
.cat-strong_union  { background: #d4edda; color: #155724; }
.cat-semantic_only { background: #cce5ff; color: #004085; }
.cat-form_only     { background: #fff3cd; color: #856404; }
</style>
"""


# ---------------------------------------------------------------------------
# Full HTML assembly
# ---------------------------------------------------------------------------


def render_html(
    stats: dict[str, Any],
    leads: list[dict[str, Any]],
    *,
    top_n: int = 500,
    summary_only: bool = False,
) -> str:
    run_id = stats.get("run_id", "unknown")
    generated = stats.get("generated_at", "")

    nav_links = """
    <a href="#summary">Summary</a>
    <a href="#histogram">Distribution</a>
    <a href="#components">Components</a>
    <a href="#categories">Categories</a>"""
    if not summary_only:
        nav_links += """
    <a href="#leads">Top Leads</a>
    <a href="#by-source">By Source</a>
    <a href="#matrix">Pair Matrix</a>"""

    sections = (
        _render_summary(stats)
        + _render_histogram(stats)
        + _render_component_table(stats)
        + _render_categories(stats)
    )
    if not summary_only:
        sections += (
            _render_leads_table(leads, top_n)
            + _render_by_source(leads)
            + _render_pair_matrix(stats)
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Juthoor LV2 — {_e(run_id)}</title>
  {_CSS}
</head>
<body>
<header>
  <h1>Juthoor LV2 — Cognate Discovery Report</h1>
  <p>Run: {_e(run_id)} &nbsp;|&nbsp; Generated: {_e(generated)}</p>
</header>
<nav>{nav_links}
</nav>
<main>
{sections}
</main>
{_SORT_JS}
</body>
</html>"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_report(
    leads_path: Path,
    output_path: Path | None = None,
    *,
    min_score: float = 0.0,
    top_n: int = 500,
    summary_only: bool = False,
) -> Path:
    """Generate an HTML report from a leads JSONL file. Returns the output path."""
    leads_path = Path(leads_path)
    if output_path is None:
        output_path = leads_path.with_suffix(".html")
    output_path = Path(output_path)

    leads = load_leads(leads_path, min_score=min_score)
    stats = compute_stats(leads)
    html_content = render_html(stats, leads, top_n=top_n, summary_only=summary_only)

    output_path.write_text(html_content, encoding="utf-8")
    return output_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate HTML report from LV2 discovery leads JSONL.")
    parser.add_argument("leads", type=Path, help="Path to discovery_*.jsonl file")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output HTML path (default: same dir as input)")
    parser.add_argument("--min-score", type=float, default=0.0, help="Minimum hybrid score to include (default: 0.0 = all)")
    parser.add_argument("--top-n", type=int, default=500, help="Max rows in the top leads table (default: 500)")
    parser.add_argument("--summary-only", action="store_true", help="Only render summary sections (no lead table)")
    args = parser.parse_args()

    out = generate_report(
        args.leads,
        args.output,
        min_score=args.min_score,
        top_n=args.top_n,
        summary_only=args.summary_only,
    )
    print(f"Wrote HTML report: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
