from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[4]
LV1_SRC = REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "src"
if str(LV1_SRC) not in sys.path:
    sys.path.append(str(LV1_SRC))

from juthoor_arabicgenome_lv1.core.loaders import load_triliteral_roots  # noqa: E402
from juthoor_arabicgenome_lv1.factory.experiment_runner import ExperimentConfig, run_experiment  # noqa: E402
from juthoor_arabicgenome_lv1.factory.feature_store import load_feature  # noqa: E402


OUTPUT_DIR = REPO_ROOT / "outputs" / "research_factory" / "axis5"
ARABIC_RE = re.compile(r"[ءابتثجحخدذرزسشصضطظعغفقكلمنهويى]")
SPLIT_RE = re.compile(r"(?:/|-|←|\s)+")
NORMALIZE_MAP = str.maketrans({"أ": "ء", "إ": "ء", "آ": "ء", "ى": "ي"})
EMPHATIC_PAIRS = (("ت", "ط"), ("د", "ض"), ("س", "ص"), ("ذ", "ظ"))


def canonical_tri_root(value: str) -> str | None:
    candidate = SPLIT_RE.split(value.strip())[0].translate(NORMALIZE_MAP)
    letters = ARABIC_RE.findall(candidate)
    if len(letters) != 3:
        return None
    return "".join(letters)


def infer_added_letter_and_position(tri_root: str, binary_root: str) -> tuple[str, int] | None:
    tri = canonical_tri_root(tri_root)
    if tri is None:
        return None
    binary = (binary_root or "").translate(NORMALIZE_MAP)
    if len(binary) != 2:
        return None
    if tri[0] == binary[0] and tri[1] == binary[1]:
        return tri[2], 3
    if tri[0] == binary[0] and tri[2] == binary[1]:
        return tri[1], 2
    if tri[1] == binary[0] and tri[2] == binary[1]:
        return tri[0], 1
    return None


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def modifier_effect(binary_vec: np.ndarray, axial_vec: np.ndarray) -> float:
    return 1.0 - cosine_similarity(binary_vec, axial_vec)


def collect_emphatic_pairs() -> list[dict]:
    binary_embeddings, binary_meta = load_feature("binary_meaning_embeddings")
    axial_embeddings, axial_meta = load_feature("axial_meaning_embeddings")
    binary_index = {root: i for i, root in enumerate(binary_meta["entity_ids"])}
    axial_index = {root: i for i, root in enumerate(axial_meta["entity_ids"])}

    grouped: dict[tuple[str, int], dict[str, dict]] = defaultdict(dict)
    for record in load_triliteral_roots():
        inferred = infer_added_letter_and_position(record.tri_root, record.binary_root)
        if inferred is None:
            continue
        added_letter, position = inferred
        if record.binary_root not in binary_index or record.tri_root not in axial_index:
            continue
        grouped[(record.binary_root, position)][added_letter] = {
            "tri_root": record.tri_root,
            "position": position,
            "binary_root": record.binary_root,
            "effect": modifier_effect(
                binary_embeddings[binary_index[record.binary_root]],
                axial_embeddings[axial_index[record.tri_root]],
            ),
        }

    rows: list[dict] = []
    for plain_letter, emphatic_letter in EMPHATIC_PAIRS:
        for (binary_root, position), variants in grouped.items():
            if plain_letter not in variants or emphatic_letter not in variants:
                continue
            plain = variants[plain_letter]
            emphatic = variants[emphatic_letter]
            rows.append(
                {
                    "pair_id": f"{plain_letter}_{emphatic_letter}",
                    "binary_root": binary_root,
                    "position": position,
                    "plain_letter": plain_letter,
                    "emphatic_letter": emphatic_letter,
                    "plain_tri_root": plain["tri_root"],
                    "emphatic_tri_root": emphatic["tri_root"],
                    "plain_effect": round(float(plain["effect"]), 6),
                    "emphatic_effect": round(float(emphatic["effect"]), 6),
                    "effect_diff": round(float(emphatic["effect"] - plain["effect"]), 6),
                }
            )
    return rows


def summarize_emphatic_rows(rows: list[dict]) -> dict:
    pair_summaries: list[dict] = []
    emphatic_effects: list[float] = []
    plain_effects: list[float] = []
    diffs: list[float] = []

    for plain_letter, emphatic_letter in EMPHATIC_PAIRS:
        pair_rows = [row for row in rows if row["pair_id"] == f"{plain_letter}_{emphatic_letter}"]
        if not pair_rows:
            pair_summaries.append(
                {
                    "pair_id": f"{plain_letter}_{emphatic_letter}",
                    "n_pairs": 0,
                    "mean_emphatic_effect": None,
                    "mean_plain_effect": None,
                    "mean_diff": None,
                }
            )
            continue
        pair_emphatic = np.asarray([row["emphatic_effect"] for row in pair_rows], dtype=np.float32)
        pair_plain = np.asarray([row["plain_effect"] for row in pair_rows], dtype=np.float32)
        pair_diff = pair_emphatic - pair_plain
        pair_summaries.append(
            {
                "pair_id": f"{plain_letter}_{emphatic_letter}",
                "n_pairs": len(pair_rows),
                "mean_emphatic_effect": round(float(np.mean(pair_emphatic)), 6),
                "mean_plain_effect": round(float(np.mean(pair_plain)), 6),
                "mean_diff": round(float(np.mean(pair_diff)), 6),
            }
        )
        emphatic_effects.extend(pair_emphatic.tolist())
        plain_effects.extend(pair_plain.tolist())
        diffs.extend(pair_diff.tolist())

    if not diffs:
        return {
            "n_pairs": 0,
            "supports_h9": False,
            "pair_summaries": pair_summaries,
        }

    emphatic_arr = np.asarray(emphatic_effects, dtype=np.float32)
    plain_arr = np.asarray(plain_effects, dtype=np.float32)
    diff_arr = np.asarray(diffs, dtype=np.float32)
    wilcoxon = stats.wilcoxon(diff_arr, alternative="greater", zero_method="wilcox")
    positive = int(np.sum(diff_arr > 0))

    summary = {
        "n_pairs": int(diff_arr.size),
        "mean_emphatic_effect": round(float(np.mean(emphatic_arr)), 6),
        "mean_plain_effect": round(float(np.mean(plain_arr)), 6),
        "mean_diff": round(float(np.mean(diff_arr)), 6),
        "median_diff": round(float(np.median(diff_arr)), 6),
        "positive_differences": positive,
        "negative_differences": int(np.sum(diff_arr < 0)),
        "wilcoxon_statistic": round(float(wilcoxon.statistic), 6),
        "p_value": round(float(wilcoxon.pvalue), 6),
        "supports_h9": bool(float(np.mean(diff_arr)) > 0 and float(wilcoxon.pvalue) < 0.05),
        "pair_summaries": pair_summaries,
    }
    return summary


def run_emphasis_hypothesis() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = collect_emphatic_pairs()
    with (OUTPUT_DIR / "emphatic_pairs.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = summarize_emphatic_rows(rows)
    (OUTPUT_DIR / "emphatic_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    config = ExperimentConfig(
        id="5.2",
        name="emphasis_hypothesis",
        hypotheses=["H9"],
        required_features=["binary_meaning_embeddings", "axial_meaning_embeddings"],
        run_fn=run_emphasis_hypothesis,
    )
    result = run_experiment(config)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
