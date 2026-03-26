from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCORING_ROOT = REPO_ROOT / "outputs" / "lv1_scoring"
ROOT_SCORE_PATH = SCORING_ROOT / "root_score_matrix.json"
NUCLEUS_SCORE_PATH = SCORING_ROOT / "nucleus_score_matrix.json"
ROOT_PREDICTIONS_PATH = SCORING_ROOT / "root_predictions.json"
DASHBOARD_PATH = SCORING_ROOT / "LV1_DASHBOARD.md"
CORRECTED_LETTERS = ("م", "ع", "غ", "ب")


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:.1f}%"


def _score(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.3f}"


def _table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def _summarize_nucleus(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_scholar: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        by_scholar[str(row["scholar"])].append(row)
        by_model[str(row["model"])].append(row)

    def summarize(group_rows: list[dict[str, Any]]) -> dict[str, Any]:
        nonzero = [
            row for row in group_rows
            if float(row.get("jaccard", 0.0)) > 0.0 or float(row.get("weighted_jaccard", 0.0)) > 0.0
        ]
        return {
            "count": len(group_rows),
            "mean_jaccard": _mean([float(row.get("jaccard", 0.0)) for row in group_rows]),
            "mean_weighted_jaccard": _mean([float(row.get("weighted_jaccard", 0.0)) for row in group_rows]),
            "nonzero_count": len(nonzero),
            "nonzero_rate": len(nonzero) / len(group_rows) if group_rows else 0.0,
        }

    return {
        "overall": summarize(rows),
        "binary_roots": len({str(row["binary_root"]) for row in rows}),
        "scholars": {key: summarize(value) for key, value in sorted(by_scholar.items())},
        "models": {key: summarize(value) for key, value in sorted(by_model.items())},
    }


def _summarize_letter_corrections(
    rows: list[dict[str, Any]],
    *,
    root_summary: dict[str, Any],
) -> dict[str, Any]:
    jabal_rows = [row for row in rows if str(row.get("scholar")) == "jabal"]
    affected = [row for row in jabal_rows if str(row.get("third_letter")) in CORRECTED_LETTERS]
    per_letter: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in affected:
        per_letter[str(row["third_letter"])].append(row)

    overall_jabal = (
        root_summary.get("by_scholar", {})
        .get("jabal", {})
        .get("mean_blended_jaccard")
    )
    affected_mean = _mean([float(row.get("blended_jaccard", 0.0)) for row in affected])

    return {
        "corrected_letters": list(CORRECTED_LETTERS),
        "affected_tests": len(affected),
        "affected_share_of_jabal": len(affected) / len(jabal_rows) if jabal_rows else 0.0,
        "mean_blended_jaccard": affected_mean,
        "overall_jabal_mean_blended_jaccard": overall_jabal,
        "delta_vs_jabal_overall": (
            affected_mean - float(overall_jabal)
            if overall_jabal is not None and affected
            else None
        ),
        "per_letter": {
            key: {
                "count": len(value),
                "mean_blended_jaccard": _mean([float(row.get("blended_jaccard", 0.0)) for row in value]),
                "mean_weighted_jaccard": _mean([float(row.get("weighted_jaccard", 0.0)) for row in value]),
                "nonzero_rate": (
                    sum(1 for row in value if float(row.get("blended_jaccard", 0.0)) > 0.0) / len(value)
                    if value else 0.0
                ),
            }
            for key, value in sorted(per_letter.items())
        },
    }


def build_dashboard_markdown() -> str:
    root_score = _load_json(ROOT_SCORE_PATH)
    nucleus_rows = _load_json(NUCLEUS_SCORE_PATH)
    root_predictions = _load_json(ROOT_PREDICTIONS_PATH) if ROOT_PREDICTIONS_PATH.exists() else None

    nucleus_summary = _summarize_nucleus(nucleus_rows)
    root_overall = root_score["overall"]
    root_scholars = root_score["by_scholar"]
    root_models = root_score["by_model"]
    quranic = root_score["quranic_validation"]
    correction_summary = (
        _summarize_letter_corrections(root_predictions, root_summary=root_score)
        if isinstance(root_predictions, list)
        else None
    )

    scholar_names = sorted(set(nucleus_summary["scholars"]) | set(root_scholars))
    model_names = sorted(set(nucleus_summary["models"]) | set(root_models))

    overall_rows = [
        [
            "Nucleus scoring",
            str(nucleus_summary["overall"]["count"]),
            str(nucleus_summary["binary_roots"]),
            _score(nucleus_summary["overall"]["mean_jaccard"]),
            _score(nucleus_summary["overall"]["mean_weighted_jaccard"]),
            "-",
            _pct(nucleus_summary["overall"]["nonzero_rate"]),
        ],
        [
            "Root scoring",
            str(root_overall["roots"]),
            str(root_overall["roots"] // max(len(root_scholars), 1)),
            _score(root_overall["mean_jaccard"]),
            _score(root_overall["mean_weighted_jaccard"]),
            _score(root_overall["mean_blended_jaccard"]),
            _pct(root_overall["nonzero_blended_rate"]),
        ],
    ]

    scholar_rows: list[list[str]] = []
    for scholar in scholar_names:
        nucleus = nucleus_summary["scholars"].get(scholar, {})
        root = root_scholars.get(scholar, {})
        scholar_rows.append(
            [
                scholar,
                str(nucleus.get("count", "-")),
                _score(nucleus.get("mean_jaccard")),
                _score(nucleus.get("mean_weighted_jaccard")),
                _pct(nucleus.get("nonzero_rate")),
                str(root.get("count", "-")),
                _score(root.get("mean_jaccard")),
                _score(root.get("mean_weighted_jaccard")),
                _score(root.get("mean_blended_jaccard")),
                _pct(
                    (
                        float(root.get("nonzero_predictions", 0)) / float(root["count"])
                        if root.get("count") else None
                    )
                ),
            ]
        )

    model_rows: list[list[str]] = []
    for model in model_names:
        nucleus = nucleus_summary["models"].get(model, {})
        root = root_models.get(model, {})
        model_rows.append(
            [
                model,
                str(nucleus.get("count", "-")),
                _score(nucleus.get("mean_jaccard")),
                _score(nucleus.get("mean_weighted_jaccard")),
                _pct(nucleus.get("nonzero_rate")),
                str(root.get("count", "-")),
                _score(root.get("mean_jaccard")),
                _score(root.get("mean_weighted_jaccard")),
                _score(root.get("mean_blended_jaccard")),
            ]
        )

    quranic_rows = [
        [
            "Quranic",
            str(quranic["quranic"]["count"]),
            _score(quranic["quranic"]["mean_jaccard"]),
            _score(quranic["quranic"]["mean_weighted_jaccard"]),
            _score(quranic["quranic"]["mean_blended_jaccard"]),
            _pct(quranic["quranic"]["nonzero_blended_rate"]),
            _pct(quranic["quranic"]["neili_valid_rate"]),
        ],
        [
            "Non-Quranic",
            str(quranic["non_quranic"]["count"]),
            _score(quranic["non_quranic"]["mean_jaccard"]),
            _score(quranic["non_quranic"]["mean_weighted_jaccard"]),
            _score(quranic["non_quranic"]["mean_blended_jaccard"]),
            _pct(quranic["non_quranic"]["nonzero_blended_rate"]),
            _pct(quranic["non_quranic"]["neili_valid_rate"]),
        ],
    ]

    test_count_rows = [
        ["Nucleus row tests", str(len(nucleus_rows))],
        ["Unique binary roots scored", str(nucleus_summary["binary_roots"])],
        ["Root row tests", str(root_overall["roots"])],
        ["Root tests per scholar", str(root_overall["roots"] // max(len(root_scholars), 1))],
        ["Scholars included", str(len(root_scholars))],
        ["Models included in root scoring", str(len(root_models))],
        ["Models included in nucleus scoring", str(len(nucleus_summary["models"]))],
    ]

    lines = [
        "# LV1 Scoring Dashboard",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Single-page summary of the current LV1 nucleus and root scoring outputs.",
        "",
        "## Overall Metrics",
        "",
        _table(
            ["Layer", "Tests", "Units", "Mean J", "Mean wJ", "Mean bJ", "Nonzero Rate"],
            overall_rows,
        ),
        "",
        "## Per-Scholar Breakdown",
        "",
        _table(
            [
                "Scholar",
                "Nucleus Tests",
                "Nucleus J",
                "Nucleus wJ",
                "Nucleus Nonzero",
                "Root Tests",
                "Root J",
                "Root wJ",
                "Root bJ",
                "Root Nonzero",
            ],
            scholar_rows,
        ),
        "",
        "## Per-Model Breakdown",
        "",
        _table(
            [
                "Model",
                "Nucleus Tests",
                "Nucleus J",
                "Nucleus wJ",
                "Nucleus Nonzero",
                "Root Tests",
                "Root J",
                "Root wJ",
                "Root bJ",
            ],
            model_rows,
        ),
        "",
        "## Quranic vs Non-Quranic Split",
        "",
        _table(
            ["Slice", "Root Tests", "Mean J", "Mean wJ", "Mean bJ", "Nonzero bJ", "Neili Valid"],
            quranic_rows,
        ),
        "",
        "## Letter Correction Impact",
        "",
    ]

    if correction_summary is None:
        lines.extend(
            [
                "Correction-impact detail is unavailable because `root_predictions.json` was not found.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                (
                    "This section measures the current footprint of the four corrected Jabal letters "
                    f"({', '.join(correction_summary['corrected_letters'])}) inside the root test set."
                ),
                "",
                _table(
                    ["Metric", "Value"],
                    [
                        ["Affected Jabal root tests", str(correction_summary["affected_tests"])],
                        ["Share of Jabal root tests", _pct(correction_summary["affected_share_of_jabal"])],
                        ["Affected-slice mean bJ", _score(correction_summary["mean_blended_jaccard"])],
                        ["Overall Jabal mean bJ", _score(correction_summary["overall_jabal_mean_blended_jaccard"])],
                        ["Delta vs overall Jabal", _score(correction_summary["delta_vs_jabal_overall"])],
                    ],
                ),
                "",
                _table(
                    ["Letter", "Affected Tests", "Mean bJ", "Mean wJ", "Nonzero bJ"],
                    [
                        [
                            letter,
                            str(data["count"]),
                            _score(data["mean_blended_jaccard"]),
                            _score(data["mean_weighted_jaccard"]),
                            _pct(data["nonzero_rate"]),
                        ]
                        for letter, data in correction_summary["per_letter"].items()
                    ],
                ),
                "",
            ]
        )

    lines.extend(
        [
            "## Test Count",
            "",
            _table(["Metric", "Value"], test_count_rows),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    DASHBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_PATH.write_text(build_dashboard_markdown(), encoding="utf-8")
    print(f"Wrote {DASHBOARD_PATH}")


if __name__ == "__main__":
    main()
