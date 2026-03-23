from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .sound_laws import project_root_by_target


ARABIC_NORMALIZE_MAP = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ؤ": "و",
        "ئ": "ي",
        "ى": "ي",
        "ة": "ه",
    }
)


def normalize_arabic_lemma(text: str) -> str:
    normalized = text.translate(ARABIC_NORMALIZE_MAP)
    return "".join(ch for ch in normalized if "\u0621" <= ch <= "\u064a")


def load_benchmark_rows(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def build_semitic_projection_rows(
    root_prediction_rows: list[dict[str, Any]],
    benchmark_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    root_by_lemma = {
        normalize_arabic_lemma(row["root"]): row
        for row in root_prediction_rows
    }

    projected_rows: list[dict[str, Any]] = []
    for bench in benchmark_rows:
        source = bench.get("source", {})
        target = bench.get("target", {})
        if source.get("lang") != "ara" or target.get("lang") not in {"heb", "arc"}:
            continue

        key = normalize_arabic_lemma(source.get("lemma", ""))
        root_row = root_by_lemma.get(key)
        if root_row is None:
            continue

        family = "hebrew" if target["lang"] == "heb" else "aramaic"
        projected_rows.append(
            {
                "source_root": root_row["root"],
                "source_binary_nucleus": root_row["binary_nucleus"],
                "source_lemma": source["lemma"],
                "source_gloss": source.get("gloss"),
                "target_lang": target["lang"],
                "target_lemma": target["lemma"],
                "target_gloss": target.get("gloss"),
                "relation": bench.get("relation"),
                "confidence": bench.get("confidence"),
                "predicted_meaning": root_row.get("predicted_meaning"),
                "predicted_features": list(root_row.get("predicted_features", ())),
                "actual_features": list(root_row.get("actual_features", ())),
                "meanings_score": {
                    "jaccard": root_row.get("jaccard", 0.0),
                    "weighted_jaccard": root_row.get("weighted_jaccard", 0.0),
                    "blended_jaccard": root_row.get("blended_jaccard", 0.0),
                },
                "projected_variants": list(project_root_by_target(root_row["root"], family)),
                "projection_family": family,
                "quranic_verse": root_row.get("quranic_verse"),
            }
        )

    return projected_rows


def projection_summary(rows: list[dict[str, Any]], benchmark_rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_semitic = sum(
        1
        for row in benchmark_rows
        if row.get("source", {}).get("lang") == "ara"
        and row.get("target", {}).get("lang") in {"heb", "arc"}
    )
    by_lang: dict[str, int] = {}
    for row in rows:
        by_lang[row["target_lang"]] = by_lang.get(row["target_lang"], 0) + 1

    return {
        "benchmark_semitic_pairs": total_semitic,
        "matched_source_roots": len(rows),
        "coverage": round(len(rows) / total_semitic, 4) if total_semitic else 0.0,
        "by_target_lang": by_lang,
    }
