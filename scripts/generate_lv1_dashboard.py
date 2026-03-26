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
DASHBOARD_PATH = SCORING_ROOT / "LV1_DASHBOARD.md"
REQUESTED_TEST_COUNT = 495


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _score(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.3f}"


def _pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:.1f}%"


def _cell(value: Any) -> str:
    if value is None:
        return "-"
    text = str(value).replace("\n", " ").replace("|", "\\|").strip()
    return text or "-"


def _feature_text(features: Any) -> str:
    if not isinstance(features, list) or not features:
        return "-"
    return " + ".join(str(item) for item in features)


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    rendered_rows = [[_cell(value) for value in row] for row in rows]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rendered_rows)
    return "\n".join(lines)


def _summarize_nucleus(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_scholar: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        by_scholar[str(row["scholar"])].append(row)
        by_model[str(row["model"])].append(row)

    def summarize(group_rows: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "count": len(group_rows),
            "mean_jaccard": _mean([float(row.get("jaccard", 0.0)) for row in group_rows]),
            "mean_weighted_jaccard": _mean(
                [float(row.get("weighted_jaccard", 0.0)) for row in group_rows]
            ),
            "nonzero_rate": (
                sum(
                    1
                    for row in group_rows
                    if float(row.get("jaccard", 0.0)) > 0.0
                    or float(row.get("weighted_jaccard", 0.0)) > 0.0
                )
                / len(group_rows)
                if group_rows
                else 0.0
            ),
        }

    return {
        "overall": summarize(rows),
        "unique_binary_roots": len({str(row["binary_root"]) for row in rows}),
        "scholars": {key: summarize(value) for key, value in sorted(by_scholar.items())},
        "models": {key: summarize(value) for key, value in sorted(by_model.items())},
    }


def _top_unique_roots(rows: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique_rows: list[dict[str, Any]] = []
    for row in rows:
        root = str(row.get("root", ""))
        if root in seen:
            continue
        seen.add(root)
        unique_rows.append(row)
        if len(unique_rows) >= limit:
            break
    return unique_rows


def build_dashboard_markdown() -> str:
    root_score = _load_json(ROOT_SCORE_PATH)
    nucleus_rows = _load_json(NUCLEUS_SCORE_PATH)

    nucleus_summary = _summarize_nucleus(nucleus_rows)
    root_overall = root_score["overall"]
    root_scholars = root_score["by_scholar"]
    root_models = root_score["by_model"]
    quranic = root_score["quranic_validation"]
    best_roots = _top_unique_roots(root_score.get("top_predictions", []), limit=10)
    worst_roots = _top_unique_roots(root_score.get("bottom_predictions", []), limit=10)

    scholar_names = sorted(set(nucleus_summary["scholars"]) | set(root_scholars))
    model_names = sorted(set(nucleus_summary["models"]) | set(root_models))
    root_tests_per_scholar = (
        root_overall["roots"] // len(root_scholars) if root_scholars else 0
    )

    overall_rows = [
        [
            "Nucleus scoring",
            len(nucleus_rows),
            nucleus_summary["unique_binary_roots"],
            len(nucleus_summary["scholars"]),
            len(nucleus_summary["models"]),
            _score(nucleus_summary["overall"]["mean_jaccard"]),
            _score(nucleus_summary["overall"]["mean_weighted_jaccard"]),
            "-",
            _pct(nucleus_summary["overall"]["nonzero_rate"]),
        ],
        [
            "Root scoring",
            root_overall["roots"],
            root_tests_per_scholar,
            len(root_scholars),
            len(root_models),
            _score(root_overall["mean_jaccard"]),
            _score(root_overall["mean_weighted_jaccard"]),
            _score(root_overall["mean_blended_jaccard"]),
            _pct(root_overall["nonzero_blended_rate"]),
        ],
    ]

    scholar_rows: list[list[Any]] = []
    for scholar in scholar_names:
        nucleus = nucleus_summary["scholars"].get(scholar, {})
        root = root_scholars.get(scholar, {})
        scholar_rows.append(
            [
                scholar,
                nucleus.get("count", "-"),
                _score(nucleus.get("mean_jaccard")),
                _score(nucleus.get("mean_weighted_jaccard")),
                _pct(nucleus.get("nonzero_rate")),
                root.get("count", "-"),
                _score(root.get("mean_jaccard")),
                _score(root.get("mean_weighted_jaccard")),
                _score(root.get("mean_blended_jaccard")),
                _pct(
                    (
                        float(root.get("nonzero_predictions", 0)) / float(root["count"])
                        if root.get("count")
                        else None
                    )
                ),
            ]
        )

    model_rows: list[list[Any]] = []
    for model in model_names:
        nucleus = nucleus_summary["models"].get(model, {})
        root = root_models.get(model, {})
        model_rows.append(
            [
                model,
                nucleus.get("count", "-"),
                _score(nucleus.get("mean_jaccard")),
                _score(nucleus.get("mean_weighted_jaccard")),
                _pct(nucleus.get("nonzero_rate")),
                root.get("count", "-"),
                _score(root.get("mean_jaccard")),
                _score(root.get("mean_weighted_jaccard")),
                _score(root.get("mean_blended_jaccard")),
            ]
        )

    quranic_rows = [
        [
            "Quranic",
            quranic["quranic"]["count"],
            _score(quranic["quranic"]["mean_jaccard"]),
            _score(quranic["quranic"]["mean_weighted_jaccard"]),
            _score(quranic["quranic"]["mean_blended_jaccard"]),
            _pct(quranic["quranic"]["nonzero_blended_rate"]),
            _pct(quranic["quranic"]["neili_valid_rate"]),
        ],
        [
            "Non-Quranic",
            quranic["non_quranic"]["count"],
            _score(quranic["non_quranic"]["mean_jaccard"]),
            _score(quranic["non_quranic"]["mean_weighted_jaccard"]),
            _score(quranic["non_quranic"]["mean_blended_jaccard"]),
            _pct(quranic["non_quranic"]["nonzero_blended_rate"]),
            _pct(quranic["non_quranic"]["neili_valid_rate"]),
        ],
    ]

    best_root_rows = [
        [
            row.get("root"),
            row.get("scholar"),
            row.get("model"),
            _score(float(row.get("blended_jaccard", 0.0))),
            _score(float(row.get("weighted_jaccard", 0.0))),
            _score(float(row.get("jaccard", 0.0))),
            row.get("bab"),
            "Yes" if row.get("quranic_verse") else "No",
            _feature_text(row.get("actual_features")),
            _feature_text(row.get("predicted_features")),
        ]
        for row in best_roots
    ]

    worst_root_rows = [
        [
            row.get("root"),
            row.get("scholar"),
            row.get("model"),
            _score(float(row.get("blended_jaccard", 0.0))),
            _score(float(row.get("weighted_jaccard", 0.0))),
            _score(float(row.get("jaccard", 0.0))),
            row.get("bab"),
            "Yes" if row.get("quranic_verse") else "No",
            _feature_text(row.get("actual_features")),
            _feature_text(row.get("predicted_features")),
        ]
        for row in worst_roots
    ]

    test_count_rows = [
        ["Requested test count", REQUESTED_TEST_COUNT],
        ["Nucleus row tests", len(nucleus_rows)],
        ["Unique binary roots in nucleus matrix", nucleus_summary["unique_binary_roots"]],
        ["Root row tests", root_overall["roots"]],
        ["Root tests per scholar", root_tests_per_scholar],
    ]

    lines = [
        "# LV1 Dashboard",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Clean summary of the current LV1 scoring outputs from `root_score_matrix.json` and `nucleus_score_matrix.json`.",
        "",
        "## Overall Metrics",
        "",
        _table(
            [
                "Layer",
                "Tests",
                "Units",
                "Scholars",
                "Models",
                "Mean J",
                "Mean wJ",
                "Mean bJ",
                "Nonzero Rate",
            ],
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
        "## Top 10 Best Roots",
        "",
        _table(
            [
                "Root",
                "Scholar",
                "Model",
                "bJ",
                "wJ",
                "J",
                "Bab",
                "Quranic",
                "Actual Features",
                "Predicted Features",
            ],
            best_root_rows,
        ),
        "",
        "## Top 10 Worst Roots",
        "",
        _table(
            [
                "Root",
                "Scholar",
                "Model",
                "bJ",
                "wJ",
                "J",
                "Bab",
                "Quranic",
                "Actual Features",
                "Predicted Features",
            ],
            worst_root_rows,
        ),
        "",
        "## Test Count",
        "",
        _table(["Metric", "Value"], test_count_rows),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    DASHBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_PATH.write_text(build_dashboard_markdown(), encoding="utf-8")
    print(f"Wrote {DASHBOARD_PATH}")


if __name__ == "__main__":
    main()
