from __future__ import annotations

import json
import re
import sys
import importlib.util
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
LV1_SRC = REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "src"
if str(LV1_SRC) not in sys.path:
    sys.path.append(str(LV1_SRC))

from juthoor_arabicgenome_lv1.core.loaders import load_triliteral_roots  # noqa: E402
from juthoor_arabicgenome_lv1.factory.experiment_runner import ExperimentConfig, run_experiment  # noqa: E402
from juthoor_arabicgenome_lv1.factory.feature_store import load_feature  # noqa: E402


def _load_common_module(name: str):
    common_root = REPO_ROOT / "Juthoor-ArabicGenome-LV1" / "scripts" / "research_factory" / "common"
    path = common_root / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"rf_common_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"rf_common_{name}"] = module
    spec.loader.exec_module(module)
    return module


_statistics = _load_common_module("statistics")
spearman_corr = _statistics.spearman_corr


OUTPUT_DIR = REPO_ROOT / "outputs" / "research_factory" / "axis4"
ARABIC_RE = re.compile(r"[ءابتثجحخدذرزسشصضطظعغفقكلمنهويى]")
SPLIT_RE = re.compile(r"(?:/|-|←|\s)+")
NORMALIZE_MAP = str.maketrans({"أ": "ء", "إ": "ء", "آ": "ء", "ى": "ي"})


def canonical_tri_root(value: str) -> str | None:
    candidate = SPLIT_RE.split(value.strip())[0].translate(NORMALIZE_MAP)
    letters = ARABIC_RE.findall(candidate)
    if len(letters) != 3:
        return None
    return "".join(letters)


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 1.0
    return float(1.0 - (np.dot(a, b) / denom))


def find_single_substitution_pairs(canonical_roots: list[str]) -> list[tuple[str, str, int]]:
    by_pattern: dict[str, list[str]] = defaultdict(list)
    for root in canonical_roots:
        for idx in range(3):
            pattern = f"{root[:idx]}*{root[idx+1:]}"
            by_pattern[pattern].append(root)

    pairs: set[tuple[str, str, int]] = set()
    for pattern, roots in by_pattern.items():
        pos = pattern.index("*")
        for a, b in combinations(sorted(set(roots)), 2):
            if sum(x != y for x, y in zip(a, b)) == 1:
                pairs.add((a, b, pos))
    return sorted(pairs)


def plot_scatter(x: list[float], y: list[float], out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(x, y, s=12, alpha=0.35)
    ax.set_xlabel("Articulatory Distance")
    ax.set_ylabel("Semantic Distance")
    ax.set_title("Phonetic Substitution: Articulation vs Meaning Distance")
    ax.grid(True, alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def run_phonetic_substitution() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    axial_embeddings, axial_meta = load_feature("axial_meaning_embeddings")
    articulatory_vectors, artic_meta = load_feature("articulatory_vectors")

    tri_map = {}
    for record in load_triliteral_roots():
        canonical = canonical_tri_root(record.tri_root)
        if canonical is not None and record.tri_root in axial_meta["entity_ids"]:
            tri_map[canonical] = record
    axial_index = {root: i for i, root in enumerate(axial_meta["entity_ids"])}
    artic_index = {letter: i for i, letter in enumerate(artic_meta["entity_ids"])}

    pairs = find_single_substitution_pairs(list(tri_map))
    rows = []
    articulatory_distances = []
    semantic_distances = []
    for a, b, pos in pairs:
        changed_a = a[pos]
        changed_b = b[pos]
        if changed_a not in artic_index or changed_b not in artic_index:
            continue
        record_a = tri_map[a]
        record_b = tri_map[b]
        if record_a.tri_root not in axial_index or record_b.tri_root not in axial_index:
            continue
        art_dist = float(np.linalg.norm(articulatory_vectors[artic_index[changed_a]] - articulatory_vectors[artic_index[changed_b]]))
        sem_dist = cosine_distance(axial_embeddings[axial_index[record_a.tri_root]], axial_embeddings[axial_index[record_b.tri_root]])
        articulatory_distances.append(art_dist)
        semantic_distances.append(sem_dist)
        rows.append(
            {
                "root_a": a,
                "root_b": b,
                "position": pos + 1,
                "changed_letter_a": changed_a,
                "changed_letter_b": changed_b,
                "articulatory_distance": round(art_dist, 6),
                "semantic_distance": round(sem_dist, 6),
            }
        )

    with (OUTPUT_DIR / "substitution_analysis.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    plot_scatter(articulatory_distances, semantic_distances, OUTPUT_DIR / "scatter_plot.png")
    rho, p_value = spearman_corr(articulatory_distances, semantic_distances)
    summary = {
        "n_pairs": len(rows),
        "spearman_rho": round(float(rho), 6),
        "p_value": round(float(p_value), 6),
        "mean_articulatory_distance": round(float(np.mean(articulatory_distances)), 6),
        "mean_semantic_distance": round(float(np.mean(semantic_distances)), 6),
        "supports_h6": bool(float(rho) > 0.2 and float(p_value) < 0.01),
    }
    (OUTPUT_DIR / "spearman_result.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    config = ExperimentConfig(
        id="4.3",
        name="phonetic_substitution",
        hypotheses=["H6"],
        required_features=["axial_meaning_embeddings", "articulatory_vectors"],
        run_fn=run_phonetic_substitution,
    )
    result = run_experiment(config)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
