"""Export promoted (supported) Research Factory results for LV2 and LV3 consumption."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# factory/promotions.py -> factory/ -> juthoor_arabicgenome_lv1/ -> src/ -> LV1 root -> repo root
# parents[3] = Juthoor-ArabicGenome-LV1, parents[4] = monorepo root
_LV1_ROOT = Path(__file__).resolve().parents[3]
_REPO_ROOT = Path(__file__).resolve().parents[4]
_RF_OUTPUTS = _REPO_ROOT / "outputs" / "research_factory"
_LV1_SCORING = _REPO_ROOT / "outputs" / "lv1_scoring"

_DEFAULT_OUTPUT_DIR = _RF_OUTPUTS / "promoted"

# Evidence card definitions for each promoted hypothesis
_EVIDENCE_CARDS: list[dict] = [
    {
        "hypothesis_id": "H2",
        "hypothesis_name": "binary_root_field_stability",
        "claim": "The binary root defines a stable semantic field",
        "source": "Jabal",
        "experiment_id": "2.3",
        "experiment_name": "field_coherence",
        "status": "supported",
        "key_metric": "real_mean=0.540 vs baseline=0.518, >11 sigma",
        "families_tested": 396,
        "promotion_date": "2026-03-14",
        "data_file": "promoted_features/field_coherence_scores.jsonl",
    },
    {
        "hypothesis_id": "H5",
        "hypothesis_name": "metathesis_order_matters",
        "claim": "The order of consonants in the binary root determines meaning; reversal changes semantic field",
        "source": "Jabal",
        "experiment_id": "4.1",
        "experiment_name": "binary_metathesis",
        "status": "supported",
        "key_metric": "metathesis mean=0.526 vs random=0.502, Wilcoxon p=0.014, Cohen d=0.28",
        "families_tested": 166,
        "promotion_date": "2026-03-14",
        "data_file": "promoted_features/metathesis_pairs.jsonl",
    },
    {
        "hypothesis_id": "H8",
        "hypothesis_name": "positional_meaning_shift",
        "claim": "A letter's semantic contribution changes with its position in the root",
        "source": "Al-Aqqad",
        "experiment_id": "1.2",
        "experiment_name": "positional_semantics",
        "status": "supported",
        "key_metric": "24/28 letters significant (86%), Kruskal-Wallis p<0.05, mean coherence=0.521",
        "families_tested": 28,
        "promotion_date": "2026-03-14",
        "data_file": "promoted_features/positional_profiles.jsonl",
    },
]


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _copy_jsonl(src: Path, dst: Path) -> int:
    """Copy a JSONL file verbatim. Returns line count written."""
    lines = src.read_text(encoding="utf-8").splitlines(keepends=True)
    dst.write_text("".join(lines), encoding="utf-8")
    return len(lines)


def _filter_jsonl(src: Path, dst: Path, pair_type: str) -> int:
    """Copy only rows where pair_type matches. Returns line count written."""
    kept: list[str] = []
    for raw in src.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        record = json.loads(raw)
        if record.get("pair_type") == pair_type:
            kept.append(raw + "\n")
    dst.write_text("".join(kept), encoding="utf-8")
    return len(kept)


def _normalize_binary_root(value: object) -> str:
    text = "".join(ch for ch in str(value or "").strip() if "\u0621" <= ch <= "\u064a")
    return text[:2] if len(text) >= 2 else ""


def _resolve_binary_root(row: dict) -> str:
    binary_root = _normalize_binary_root(
        row.get("binary_root")
        or row.get("source_binary_nucleus")
        or row.get("binary_nucleus")
    )
    if binary_root:
        return binary_root
    return _normalize_binary_root(row.get("source_root"))


def _write_cross_lingual_support(dst: Path) -> int:
    support: dict[str, dict] = defaultdict(
        lambda: {
            "binary_root": None,
            "semitic_rows": 0,
            "semitic_exact_hits": 0,
            "semitic_binary_hits": 0,
            "semitic_similarity_total": 0.0,
            "semitic_target_langs": set(),
            "non_semitic_rows": 0,
            "non_semitic_exact_hits": 0,
            "non_semitic_binary_hits": 0,
            "non_semitic_similarity_total": 0.0,
            "non_semitic_target_langs": set(),
        }
    )

    def consume_rows(path: Path, bucket: str) -> None:
        if not path.exists():
            return
        rows = json.loads(path.read_text(encoding="utf-8"))
        for row in rows:
            binary_root = _resolve_binary_root(row)
            if not binary_root:
                continue
            entry = support[binary_root]
            entry["binary_root"] = binary_root
            entry[f"{bucket}_rows"] += 1
            entry[f"{bucket}_exact_hits"] += 1 if row.get("exact_projection_hit") else 0
            entry[f"{bucket}_binary_hits"] += 1 if row.get("binary_prefix_hit") else 0
            entry[f"{bucket}_similarity_total"] += float(row.get("best_projection_similarity", 0.0) or 0.0)
            target_lang = row.get("target_lang")
            if target_lang:
                entry[f"{bucket}_target_langs"].add(str(target_lang))

    consume_rows(_LV1_SCORING / "benchmark_semitic_scored_projections.json", "semitic")
    consume_rows(_LV1_SCORING / "benchmark_non_semitic_scored_projections.json", "non_semitic")

    lines: list[str] = []
    for binary_root in sorted(support):
        entry = support[binary_root]
        semitic_rows = entry["semitic_rows"]
        non_semitic_rows = entry["non_semitic_rows"]
        record = {
            "binary_root": binary_root,
            "semitic_support": {
                "rows": semitic_rows,
                "exact_hits": entry["semitic_exact_hits"],
                "exact_hit_rate": round(entry["semitic_exact_hits"] / semitic_rows, 6) if semitic_rows else 0.0,
                "binary_hits": entry["semitic_binary_hits"],
                "binary_hit_rate": round(entry["semitic_binary_hits"] / semitic_rows, 6) if semitic_rows else 0.0,
                "mean_similarity": round(entry["semitic_similarity_total"] / semitic_rows, 6) if semitic_rows else 0.0,
                "target_langs": sorted(entry["semitic_target_langs"]),
            },
            "non_semitic_support": {
                "rows": non_semitic_rows,
                "exact_hits": entry["non_semitic_exact_hits"],
                "exact_hit_rate": round(entry["non_semitic_exact_hits"] / non_semitic_rows, 6) if non_semitic_rows else 0.0,
                "binary_hits": entry["non_semitic_binary_hits"],
                "binary_hit_rate": round(entry["non_semitic_binary_hits"] / non_semitic_rows, 6) if non_semitic_rows else 0.0,
                "mean_similarity": round(entry["non_semitic_similarity_total"] / non_semitic_rows, 6) if non_semitic_rows else 0.0,
                "target_langs": sorted(entry["non_semitic_target_langs"]),
            },
            "support_score": round(
                (
                    (entry["semitic_binary_hits"] / semitic_rows) * 0.7
                    + (entry["semitic_exact_hits"] / semitic_rows) * 0.3
                ) if semitic_rows else 0.0,
                6,
            ),
        }
        lines.append(json.dumps(record, ensure_ascii=False) + "\n")

    dst.write_text("".join(lines), encoding="utf-8")
    return len(lines)


def export_promoted_results(output_dir: Path | None = None) -> dict:
    """Export all promoted (supported) findings to a structured directory.

    Creates::

        output_dir/
            promoted_features/
                field_coherence_scores.jsonl
                positional_profiles.jsonl
                metathesis_pairs.jsonl
            evidence_cards/
                H2_field_coherence.json
                H5_order_matters.json
                H8_positional_semantics.json
            promotion_manifest.json

    Args:
        output_dir: Destination directory. Defaults to
            ``<repo_root>/outputs/research_factory/promoted``.

    Returns:
        The promotion manifest as a dict.
    """
    out = output_dir if output_dir is not None else _DEFAULT_OUTPUT_DIR

    features_dir = out / "promoted_features"
    cards_dir = out / "evidence_cards"
    _ensure_dir(features_dir)
    _ensure_dir(cards_dir)

    # --- promoted_features/ ---
    _copy_jsonl(
        _RF_OUTPUTS / "axis2" / "field_coherence.jsonl",
        features_dir / "field_coherence_scores.jsonl",
    )
    _copy_jsonl(
        _RF_OUTPUTS / "axis1" / "positional_semantics.jsonl",
        features_dir / "positional_profiles.jsonl",
    )
    _filter_jsonl(
        _RF_OUTPUTS / "axis4" / "metathesis_analysis.jsonl",
        features_dir / "metathesis_pairs.jsonl",
        pair_type="metathesis",
    )
    _write_cross_lingual_support(features_dir / "cross_lingual_support.jsonl")

    # --- evidence_cards/ ---
    card_filenames = {
        "H2": "H2_field_coherence.json",
        "H5": "H5_order_matters.json",
        "H8": "H8_positional_semantics.json",
    }

    written_cards: list[str] = []
    for card in _EVIDENCE_CARDS:
        filename = card_filenames[card["hypothesis_id"]]
        card_path = cards_dir / filename
        card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
        written_cards.append(f"evidence_cards/{filename}")

    # --- promotion_manifest.json ---
    manifest: dict = {
        "promotion_date": datetime.now(timezone.utc).isoformat(),
        "promoted_hypotheses": ["H2", "H5", "H8"],
        "evidence_cards": written_cards,
        "promoted_features": [
            "promoted_features/field_coherence_scores.jsonl",
            "promoted_features/positional_profiles.jsonl",
            "promoted_features/metathesis_pairs.jsonl",
            "promoted_features/cross_lingual_support.jsonl",
        ],
        "source_experiments": ["2.3", "4.1", "1.2", "5.3", "5.4"],
    }
    (out / "promotion_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return manifest
