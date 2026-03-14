"""Export promoted (supported) Research Factory results for LV2 and LV3 consumption."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

# factory/promotions.py -> factory/ -> juthoor_arabicgenome_lv1/ -> src/ -> LV1 root -> repo root
# parents[3] = Juthoor-ArabicGenome-LV1, parents[4] = monorepo root
_LV1_ROOT = Path(__file__).resolve().parents[3]
_REPO_ROOT = Path(__file__).resolve().parents[4]
_RF_OUTPUTS = _REPO_ROOT / "outputs" / "research_factory"

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
        ],
        "source_experiments": ["2.3", "4.1", "1.2"],
    }
    (out / "promotion_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return manifest
