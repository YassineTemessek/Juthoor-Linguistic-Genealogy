from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any


LV2_ROOT = Path(__file__).resolve().parents[2]
LEADS_DIR = LV2_ROOT / "outputs" / "leads"
GOLD_PATH = LV2_ROOT / "resources" / "benchmarks" / "cognate_gold.jsonl"
OUTPUT_PATH = LV2_ROOT / "outputs" / "evaluation_all_pairs.json"
HIT_KS = (1, 5, 10, 20, 50, 100)

ARABIC_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")
ARABIC_HAMZA_TR = str.maketrans({
    "أ": "ا",
    "إ": "ا",
    "آ": "ا",
    "ٱ": "ا",
    "ؤ": "و",
    "ئ": "ي",
    "ء": "ا",
})
LANG_ALIASES = {
    "ara-qur": "ara",
    "ara_classical": "ara",
    "fas": "fa",
    "per": "fa",
}


def normalize_lang(lang: Any) -> str:
    text = " ".join(str(lang or "").split()).strip().casefold()
    return LANG_ALIASES.get(text, text)


def strip_combining_marks(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize_lemma(text: Any, lang: str) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    value = strip_combining_marks(value)
    if lang == "ara":
        value = ARABIC_DIACRITICS_RE.sub("", value)
        value = value.translate(ARABIC_HAMZA_TR)
    return " ".join(value.split()).strip().casefold()


def load_gold(path: Path) -> dict[tuple[str, str], list[tuple[str, str]]]:
    gold_by_pair: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rec = json.loads(line)
            src_lang = normalize_lang(rec.get("source", {}).get("lang"))
            tgt_lang = normalize_lang(rec.get("target", {}).get("lang"))
            src_lemma = normalize_lemma(rec.get("source", {}).get("lemma"), src_lang)
            tgt_lemma = normalize_lemma(rec.get("target", {}).get("lemma"), tgt_lang)
            if not (src_lang and tgt_lang and src_lemma and tgt_lemma):
                continue
            gold_by_pair[(src_lang, tgt_lang)].append((src_lemma, tgt_lemma))
    return gold_by_pair


def extract_lead_fields(rec: dict[str, Any]) -> tuple[str, str, str, str] | None:
    if isinstance(rec.get("source"), dict) and isinstance(rec.get("target"), dict):
        source = rec["source"]
        target = rec["target"]
        src_lang = normalize_lang(source.get("lang"))
        tgt_lang = normalize_lang(target.get("lang"))
        src_lemma = normalize_lemma(source.get("lemma"), src_lang)
        tgt_lemma = normalize_lemma(target.get("lemma"), tgt_lang)
        if src_lang and tgt_lang and src_lemma and tgt_lemma:
            return src_lang, src_lemma, tgt_lang, tgt_lemma

    tgt_lang = normalize_lang(rec.get("target_lang"))
    src_lang = "ara" if rec.get("source_lemma") else ""
    src_lemma = normalize_lemma(rec.get("source_lemma"), src_lang)
    tgt_lemma = normalize_lemma(rec.get("target_lemma"), tgt_lang)
    if src_lang and tgt_lang and src_lemma and tgt_lemma:
        return src_lang, src_lemma, tgt_lang, tgt_lemma

    return None


def score_hint(rec: dict[str, Any]) -> float:
    candidates = (
        rec.get("scores", {}).get("final_combined"),
        rec.get("scores", {}).get("multi_method_best"),
        rec.get("hybrid", {}).get("combined_score"),
        rec.get("combined_score"),
        rec.get("scores", {}).get("semantic"),
    )
    for value in candidates:
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return 0.0


def rank_hint(rec: dict[str, Any], fallback_index: int) -> int:
    value = rec.get("rank")
    try:
        parsed = int(value)
        if parsed > 0:
            return parsed
    except (TypeError, ValueError):
        pass
    return fallback_index


def collect_leads(
    leads_dir: Path,
) -> tuple[
    dict[tuple[str, str], dict[tuple[str, str], dict[str, Any]]],
    dict[tuple[str, str], set[str]],
    dict[tuple[str, str], int],
]:
    pooled: dict[tuple[str, str], dict[tuple[str, str], dict[str, Any]]] = defaultdict(dict)
    files_by_pair: dict[tuple[str, str], set[str]] = defaultdict(set)
    raw_rows_by_pair: dict[tuple[str, str], int] = defaultdict(int)

    for path in sorted(leads_dir.glob("*.jsonl")):
        if path.stat().st_size == 0:
            continue
        with path.open("r", encoding="utf-8") as handle:
            file_row_index = 0
            for line in handle:
                if not line.strip():
                    continue
                file_row_index += 1
                rec = json.loads(line)
                fields = extract_lead_fields(rec)
                if fields is None:
                    continue
                src_lang, src_lemma, tgt_lang, tgt_lemma = fields
                pair_key = (src_lang, tgt_lang)
                candidate_key = (src_lemma, tgt_lemma)
                score = score_hint(rec)
                rank = rank_hint(rec, file_row_index)

                files_by_pair[pair_key].add(path.name)
                raw_rows_by_pair[pair_key] += 1

                existing = pooled[pair_key].get(candidate_key)
                if existing is None or (score, -rank, path.name) > (
                    existing["score"],
                    -existing["rank_hint"],
                    existing["file"],
                ):
                    pooled[pair_key][candidate_key] = {
                        "source_lemma": src_lemma,
                        "target_lemma": tgt_lemma,
                        "score": score,
                        "rank_hint": rank,
                        "file": path.name,
                    }

    return pooled, files_by_pair, raw_rows_by_pair


def build_rank_lookup(
    candidates: dict[tuple[str, str], dict[str, Any]],
) -> dict[tuple[str, str], int]:
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates.values():
        by_source[row["source_lemma"]].append(row)

    rank_lookup: dict[tuple[str, str], int] = {}
    for source_lemma, rows in by_source.items():
        rows.sort(key=lambda row: (-row["score"], row["rank_hint"], row["target_lemma"]))
        for idx, row in enumerate(rows, start=1):
            rank_lookup[(source_lemma, row["target_lemma"])] = idx
    return rank_lookup


def evaluate_pair(
    gold_pairs: list[tuple[str, str]],
    rank_lookup: dict[tuple[str, str], int],
) -> dict[str, Any]:
    found = 0
    reciprocal_sum = 0.0
    hit_counts = {k: 0 for k in HIT_KS}

    for gold_key in gold_pairs:
        rank = rank_lookup.get(gold_key)
        if rank is None:
            continue
        found += 1
        reciprocal_sum += 1.0 / rank
        for k in HIT_KS:
            if rank <= k:
                hit_counts[k] += 1

    total = len(gold_pairs)
    return {
        "gold_pairs": total,
        "found": found,
        "coverage": round(found / total, 6) if total else 0.0,
        "MRR": round(reciprocal_sum / total, 6) if total else 0.0,
        **{f"Hit@{k}": round(hit_counts[k] / total, 6) if total else 0.0 for k in HIT_KS},
    }


def print_table(rows: list[dict[str, Any]]) -> None:
    headers = [
        "Pair",
        "Gold",
        "Found",
        "MRR",
        "H@1",
        "H@5",
        "H@10",
        "H@20",
        "H@50",
        "H@100",
        "Sources",
        "Leads",
        "Files",
    ]
    table_rows = []
    for row in rows:
        table_rows.append([
            row["pair"],
            str(row["gold_pairs"]),
            str(row["found"]),
            f"{row['MRR']:.4f}",
            f"{row['Hit@1']:.4f}",
            f"{row['Hit@5']:.4f}",
            f"{row['Hit@10']:.4f}",
            f"{row['Hit@20']:.4f}",
            f"{row['Hit@50']:.4f}",
            f"{row['Hit@100']:.4f}",
            str(row["unique_sources"]),
            str(row["unique_leads"]),
            str(row["files_loaded"]),
        ])

    widths = [
        max(len(headers[idx]), *(len(r[idx]) for r in table_rows)) if table_rows else len(headers[idx])
        for idx in range(len(headers))
    ]

    def format_row(values: list[str]) -> str:
        return " | ".join(value.ljust(widths[idx]) for idx, value in enumerate(values))

    print(format_row(headers))
    print("-+-".join("-" * width for width in widths))
    for values in table_rows:
        print(format_row(values))


def main() -> None:
    if not LEADS_DIR.exists():
        raise FileNotFoundError(f"Leads directory not found: {LEADS_DIR}")
    if not GOLD_PATH.exists():
        raise FileNotFoundError(f"Gold benchmark not found: {GOLD_PATH}")

    print(f"Loading gold benchmark: {GOLD_PATH}")
    gold_by_pair = load_gold(GOLD_PATH)
    total_gold = sum(len(rows) for rows in gold_by_pair.values())
    print(f"Loaded {total_gold} gold pairs across {len(gold_by_pair)} language pairs.")

    print(f"Loading leads from: {LEADS_DIR}")
    pooled, files_by_pair, raw_rows_by_pair = collect_leads(LEADS_DIR)
    total_files = len(list(LEADS_DIR.glob('*.jsonl')))
    print(f"Scanned {total_files} leads files.")

    rows: list[dict[str, Any]] = []
    for pair_key in sorted(gold_by_pair):
        src_lang, tgt_lang = pair_key
        pair_candidates = pooled.get(pair_key, {})
        rank_lookup = build_rank_lookup(pair_candidates)
        metrics = evaluate_pair(gold_by_pair[pair_key], rank_lookup)
        unique_sources = len({src for src, _tgt in pair_candidates})
        row = {
            "pair": f"{src_lang}->{tgt_lang}",
            "source_lang": src_lang,
            "target_lang": tgt_lang,
            "unique_sources": unique_sources,
            "unique_leads": len(pair_candidates),
            "raw_lead_rows": raw_rows_by_pair.get(pair_key, 0),
            "files_loaded": len(files_by_pair.get(pair_key, set())),
            "files": sorted(files_by_pair.get(pair_key, set())),
            **metrics,
        }
        rows.append(row)

    print()
    print_table(rows)

    summary = {
        "gold_path": str(GOLD_PATH),
        "leads_dir": str(LEADS_DIR),
        "output_path": str(OUTPUT_PATH),
        "hit_ks": list(HIT_KS),
        "total_gold_pairs": total_gold,
        "total_language_pairs": len(gold_by_pair),
        "total_leads_files_scanned": total_files,
        "pairs": rows,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print()
    print(f"Saved evaluation to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
