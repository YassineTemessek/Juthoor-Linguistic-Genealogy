from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from juthoor_arabicgenome_lv1.core.feature_decomposition import (
    decompose_semantic_text,
    feature_categories,
)
from juthoor_arabicgenome_lv1.factory.scoring import (
    build_nucleus_score_rows,
    invert_features_extended,
)
from juthoor_arabicgenome_lv1.factory.root_predictor import (
    build_root_prediction_rows,
    summarize_root_predictions,
)
from juthoor_arabicgenome_lv1.factory.cross_lingual_projection import (
    build_non_semitic_projection_rows,
    build_semitic_projection_rows,
    load_benchmark_rows,
    non_semitic_projection_summary,
    projection_summary,
)
from juthoor_arabicgenome_lv1.factory.cross_lingual_scoring import (
    score_projection_row,
    summarize_projection_scores,
)


LV1_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = LV1_ROOT.parent
DOC_ROOT = LV1_ROOT / "docs" / "The Arabic Tongue (nature-genome-application)"
THEORY_ROOT = DOC_ROOT / "Languistic theories"
MUAJAM_ROOT = LV1_ROOT / "data" / "muajam"
CANON_ROOT = LV1_ROOT / "data" / "theory_canon"
LETTERS_OUT = CANON_ROOT / "letters"
BINARY_OUT = CANON_ROOT / "binary_fields"
ROOTS_OUT = CANON_ROOT / "roots"
OUTPUT_ROOT = REPO_ROOT / "outputs" / "lv1_scoring"
LV2_BENCHMARK = REPO_ROOT / "Juthoor-CognateDiscovery-LV2" / "resources" / "benchmarks" / "cognate_gold.jsonl"

LETTER_NAME_TO_CHAR = {
    "الهمزة": "ء",
    "ألف المد": "ا",
    "ألف": "ا",
    "باء": "ب",
    "تاء": "ت",
    "ثاء": "ث",
    "جيم": "ج",
    "حاء": "ح",
    "خاء": "خ",
    "دال": "د",
    "ذال": "ذ",
    "راء": "ر",
    "زاء": "ز",
    "زاي": "ز",
    "سين": "س",
    "شين": "ش",
    "صاد": "ص",
    "ضاد": "ض",
    "طاء": "ط",
    "ظاء": "ظ",
    "عين": "ع",
    "غين": "غ",
    "فاء": "ف",
    "قاف": "ق",
    "كاف": "ك",
    "لام": "ل",
    "ميم": "م",
    "نون": "ن",
    "هاء": "هـ",
    "واو": "و",
    "ياء": "ي",
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _letter_row(
    *,
    letter: str,
    scholar: str,
    raw_description: str,
    source_document: str,
    letter_name: str | None = None,
    sensory_category: str | None = None,
    kinetic_gloss: str | None = None,
    confidence: str = "medium",
) -> dict[str, Any]:
    features = decompose_semantic_text(raw_description)
    return {
        "letter": letter,
        "letter_name": letter_name,
        "scholar": scholar,
        "raw_description": raw_description,
        "atomic_features": list(features),
        "feature_categories": list(feature_categories(features)),
        "sensory_category": sensory_category,
        "kinetic_gloss": kinetic_gloss,
        "source_document": source_document,
        "confidence": confidence,
    }


def _load_jabal_letters() -> list[dict[str, Any]]:
    rows = _read_jsonl(MUAJAM_ROOT / "letter_meanings.jsonl")
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            _letter_row(
                letter=row["letter"],
                letter_name=row["letter_name"],
                scholar="jabal",
                raw_description=row["meaning"],
                source_document="data/muajam/letter_meanings.jsonl",
                confidence="high",
            )
        )
    return out


def _extract_markdown_table(text: str, start_marker: str) -> list[list[str]]:
    lines = text.splitlines()
    capture = False
    rows: list[list[str]] = []
    for line in lines:
        if start_marker in line:
            capture = True
            continue
        if capture and line.startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if set(cells[0]) == {"-"}:
                continue
            rows.append(cells)
        elif capture and rows:
            break
    return rows


def _load_neili_letters() -> list[dict[str, Any]]:
    summary = (DOC_ROOT / "ملخص_الدلالة_الصوتية_العربية.md").read_text(encoding="utf-8")
    rows = _extract_markdown_table(summary, "### الحروف العشرة المستكشفة")
    out: list[dict[str, Any]] = []
    for row in rows[1:]:
        letter = row[0].replace("*", "").replace(" ", "")
        kinetic = row[1]
        gloss = row[2]
        out.append(
            _letter_row(
                letter=letter,
                scholar="neili",
                raw_description=gloss,
                kinetic_gloss=kinetic,
                source_document=str(DOC_ROOT / "ملخص_الدلالة_الصوتية_العربية.md"),
                confidence="high",
            )
        )
    return out


def _load_abbas_letters() -> list[dict[str, Any]]:
    summary = (DOC_ROOT / "ملخص_الدلالة_الصوتية_العربية.md").read_text(encoding="utf-8")
    source_document = str(DOC_ROOT / "ملخص_الدلالة_الصوتية_العربية.md")
    rows = _extract_markdown_table(summary, "#### نظام التصنيف الحسي الشامل")
    out: dict[str, dict[str, Any]] = {}
    for row in rows[1:]:
        category = row[0].replace("*", "")
        letters = [item.strip() for item in row[1].split("،")]
        for letter in letters:
            if not letter:
                continue
            out[letter] = _letter_row(
                letter=letter,
                scholar="hassan_abbas",
                raw_description=row[2],
                sensory_category=category,
                source_document=source_document,
            )

    # The summary table omits Abbas's separate treatment of الواو and الياء.
    out["و"] = _letter_row(
        letter="و",
        letter_name="الواو",
        scholar="hassan_abbas",
        raw_description="فعالية وامتداد إلى الأمام من غير إحساس حسي آخر.",
        sensory_category="بصرية",
        source_document=str(THEORY_ROOT / "حسن عباس" / "خصائص الحروف العربية ومعانيها - حسن عباس.md"),
        confidence="medium",
    )
    out["ي"] = _letter_row(
        letter="ي",
        letter_name="الياء",
        scholar="hassan_abbas",
        raw_description="جوف وباطن واستقرار في الصميم أو في حفرة.",
        sensory_category="بصرية",
        source_document=str(THEORY_ROOT / "حسن عباس" / "خصائص الحروف العربية ومعانيها - حسن عباس.md"),
        confidence="medium",
    )
    return list(out.values())


def _extract_asim_full_table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4:
            continue
        if cells[0] in {"الترتيب", "---"}:
            continue
        if not re.fullmatch(r"[١٢٣٤٥٦٧٨٩٠]+", cells[0]):
            continue
        rows.append(cells)
    return rows


def _normalize_letter_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip())


def _load_asim_letters() -> list[dict[str, Any]]:
    source_path = THEORY_ROOT / "عاصم المصري" / "الأبجدية-ودلالاتها-عاصم-المصري.md"
    rows = _extract_asim_full_table_rows(source_path.read_text(encoding="utf-8"))
    out: list[dict[str, Any]] = []
    for _, _, raw_name, raw_gloss in rows:
        letter_name = _normalize_letter_name(raw_name)
        letter = LETTER_NAME_TO_CHAR.get(letter_name)
        if not letter:
            continue
        out.append(
            _letter_row(
                letter=letter,
                letter_name=letter_name,
                scholar="asim_al_masri",
                raw_description=raw_gloss,
                kinetic_gloss=raw_gloss,
                source_document=str(source_path),
            )
        )
    return out


def _load_anbar_letters() -> list[dict[str, Any]]:
    summary = (DOC_ROOT / "ملخص_الدلالة_الصوتية_العربية.md").read_text(encoding="utf-8")
    pattern = re.compile(r"- \*\*(.+?) \((.)\)\*\*: (.+)")
    section = summary.split("### دلالات الحروف الأساسية حسب عنبر", 1)[1].split("## ١٨.", 1)[0]
    out: list[dict[str, Any]] = []
    for match in pattern.finditer(section):
        letter_name, letter, gloss = match.groups()
        out.append(
            _letter_row(
                letter=letter,
                letter_name=letter_name,
                scholar="anbar",
                raw_description=gloss,
                kinetic_gloss=gloss,
                source_document=str(DOC_ROOT / "ملخص_الدلالة_الصوتية_العربية.md"),
            )
        )
    return out


def _build_jabal_nuclei() -> list[dict[str, Any]]:
    rows = _read_jsonl(MUAJAM_ROOT / "roots.jsonl")
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row["binary_root"]
        grouped.setdefault(
            key,
            {
                "binary_root": key,
                "letter1": row["letter1"],
                "letter2": row["letter2"],
                "jabal_shared_meaning": row["binary_root_meaning"],
                "jabal_features": list(decompose_semantic_text(row["binary_root_meaning"])),
                "member_roots": [],
                "member_count": 0,
                "reverse_exists": False,
                "reverse_root": None,
                "model_a_score": None,
                "model_b_score": None,
                "model_c_score": None,
                "model_d_score": None,
                "best_model": None,
                "golden_rule_score": None,
                "status": "empty",
                "bab": row.get("bab_name") or row.get("bab"),
                "source": "المعجم الاشتقاقي المؤصل",
            },
        )
        if row["tri_root"] not in grouped[key]["member_roots"]:
            grouped[key]["member_roots"].append(row["tri_root"])
    keys = set(grouped)
    for key, payload in grouped.items():
        payload["member_count"] = len(payload["member_roots"])
        payload["reverse_exists"] = key[::-1] in keys and key[::-1] != key
        payload["reverse_root"] = key[::-1] if payload["reverse_exists"] else None
    return sorted(grouped.values(), key=lambda item: item["binary_root"])


def _build_jabal_roots() -> list[dict[str, Any]]:
    rows = _read_jsonl(MUAJAM_ROOT / "roots.jsonl")
    out: list[dict[str, Any]] = []
    for row in rows:
        root = row["tri_root"]
        third_letter = row.get("added_letter", "")
        if len(third_letter) != 1 and len(root) >= 3:
            third_letter = root[-1]
        out.append(
            {
                "root": root,
                "binary_nucleus": row["binary_root"],
                "third_letter": third_letter,
                "jabal_axial_meaning": row["axial_meaning"],
                "jabal_features": list(decompose_semantic_text(row["axial_meaning"])),
                "predicted_meaning": None,
                "predicted_features": None,
                "prediction_score": None,
                "quranic_verse": row.get("quran_example") or None,
                "bab": row.get("bab_name") or row.get("bab"),
                "source": "المعجم الاشتقاقي المؤصل",
                "status": "empty",
            }
        )
    return out


def _scholar_letter_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[row["scholar"]][row["letter"]] = row
    return dict(grouped)


def _build_golden_rule_report(nuclei_rows: list[dict[str, Any]]) -> dict[str, Any]:
    lookup = {row["binary_root"]: row for row in nuclei_rows}
    seen: set[str] = set()
    pair_rows: list[dict[str, Any]] = []
    confirmed = 0
    for root, row in lookup.items():
        reverse = root[::-1]
        if reverse not in lookup or root == reverse or reverse in seen:
            continue
        seen.add(root)
        seen.add(reverse)
        forward_features = tuple(row["jabal_features"])
        reverse_features = tuple(lookup[reverse]["jabal_features"])
        inverted_forward = set(invert_features_extended(forward_features))
        overlap = sorted(inverted_forward & set(reverse_features))
        is_confirmed = bool(overlap)
        if is_confirmed:
            confirmed += 1
        pair_rows.append(
            {
                "forward": root,
                "reverse": reverse,
                "forward_features": list(forward_features),
                "reverse_features": list(reverse_features),
                "inverted_forward_features": list(inverted_forward),
                "overlap_with_reverse": overlap,
                "confirmed": is_confirmed,
            }
        )
    total = len(pair_rows)
    return {
        "reversible_pairs": total,
        "confirmed_pairs": confirmed,
        "confirmation_rate": round(confirmed / total, 6) if total else 0.0,
        "pairs": pair_rows,
    }


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")

    scholar_rows = (
        _load_jabal_letters()
        + _load_neili_letters()
        + _load_abbas_letters()
        + _load_asim_letters()
        + _load_anbar_letters()
    )
    nuclei_rows = _build_jabal_nuclei()
    root_rows = _build_jabal_roots()
    scholar_map = _scholar_letter_map(scholar_rows)
    score_rows = build_nucleus_score_rows(nuclei_rows, scholar_map)
    golden_rule = _build_golden_rule_report(nuclei_rows)
    root_prediction_rows = build_root_prediction_rows(root_rows, nuclei_rows, scholar_map, scholar="jabal")
    root_score_matrix = summarize_root_predictions(root_prediction_rows)
    benchmark_rows = load_benchmark_rows(LV2_BENCHMARK)
    semitic_projection_rows = build_semitic_projection_rows(root_prediction_rows, benchmark_rows)
    semitic_projection_summary = projection_summary(semitic_projection_rows, benchmark_rows)
    semitic_scored_rows = [score_projection_row(row) for row in semitic_projection_rows]
    semitic_scoring_summary = summarize_projection_scores(semitic_scored_rows)
    non_semitic_projection_rows = build_non_semitic_projection_rows(root_prediction_rows, benchmark_rows)
    non_semitic_projection_summary_payload = non_semitic_projection_summary(
        non_semitic_projection_rows,
        benchmark_rows,
    )
    non_semitic_scored_rows = [score_projection_row(row) for row in non_semitic_projection_rows]
    non_semitic_scoring_summary = summarize_projection_scores(non_semitic_scored_rows)

    prediction_by_root = {row["root"]: row for row in root_prediction_rows}
    for row in root_rows:
        prediction = prediction_by_root.get(row["root"])
        if not prediction:
            continue
        row["predicted_meaning"] = prediction["predicted_meaning"]
        row["predicted_features"] = prediction["predicted_features"]
        row["prediction_score"] = prediction["weighted_jaccard"]
        row["status"] = "predicted" if prediction["predicted_features"] else "empty"

    by_scholar: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scholar_rows:
        by_scholar[row["scholar"]].append(row)
    for scholar, rows in by_scholar.items():
        _write_jsonl(LETTERS_OUT / f"{scholar}_letters.jsonl", sorted(rows, key=lambda item: item["letter"]))
    _write_jsonl(BINARY_OUT / "jabal_nuclei_raw.jsonl", nuclei_rows)
    _write_jsonl(ROOTS_OUT / "jabal_roots_raw.jsonl", root_rows)
    _write_json(OUTPUT_ROOT / "nucleus_score_matrix.json", score_rows)
    _write_json(OUTPUT_ROOT / "golden_rule_report.json", golden_rule)
    _write_json(OUTPUT_ROOT / "root_predictions.json", root_prediction_rows)
    _write_json(OUTPUT_ROOT / "root_score_matrix.json", root_score_matrix)
    _write_json(OUTPUT_ROOT / "benchmark_semitic_projections.json", semitic_projection_rows)
    _write_json(OUTPUT_ROOT / "benchmark_semitic_projection_summary.json", semitic_projection_summary)
    _write_json(OUTPUT_ROOT / "benchmark_semitic_scored_projections.json", semitic_scored_rows)
    _write_json(OUTPUT_ROOT / "benchmark_semitic_scoring_summary.json", semitic_scoring_summary)
    _write_json(OUTPUT_ROOT / "benchmark_non_semitic_projections.json", non_semitic_projection_rows)
    _write_json(OUTPUT_ROOT / "benchmark_non_semitic_projection_summary.json", non_semitic_projection_summary_payload)
    _write_json(OUTPUT_ROOT / "benchmark_non_semitic_scored_projections.json", non_semitic_scored_rows)
    _write_json(OUTPUT_ROOT / "benchmark_non_semitic_scoring_summary.json", non_semitic_scoring_summary)

    summary = {
        "scholars": {scholar: len(rows) for scholar, rows in by_scholar.items()},
        "nuclei": len(nuclei_rows),
        "roots": len(root_rows),
        "score_rows": len(score_rows),
        "root_prediction_rows": len(root_prediction_rows),
        "golden_rule_pairs": golden_rule["reversible_pairs"],
        "benchmark_semitic_rows": len(semitic_projection_rows),
        "benchmark_non_semitic_rows": len(non_semitic_projection_rows),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
