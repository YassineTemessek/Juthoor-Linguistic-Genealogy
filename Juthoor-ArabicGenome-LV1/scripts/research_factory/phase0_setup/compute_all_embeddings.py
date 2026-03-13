from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.append(str(SRC_ROOT))

from juthoor_arabicgenome_lv1.core.loaders import (  # noqa: E402
    load_binary_roots,
    load_letters,
    load_triliteral_roots,
)
from juthoor_arabicgenome_lv1.factory.feature_store import (  # noqa: E402
    FEATURES_DIR,
    save_feature,
)
from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import BgeM3Embedder  # noqa: E402


@dataclass(frozen=True)
class EmbeddingJob:
    name: str
    ids: list[str]
    texts: list[str]
    meta: dict[str, Any]


def build_embedding_jobs() -> list[EmbeddingJob]:
    letters = load_letters()
    binary_roots = load_binary_roots()
    triliteral_roots = load_triliteral_roots()
    return [
        EmbeddingJob(
            name="letter_embeddings",
            ids=[record.letter for record in letters],
            texts=[record.meaning for record in letters],
            meta={
                "entity_type": "Letter",
                "entity_ids": [record.letter for record in letters],
                "text_field": "meaning",
                "source": "data/muajam/letter_meanings.jsonl",
            },
        ),
        EmbeddingJob(
            name="binary_meaning_embeddings",
            ids=[record.binary_root for record in binary_roots],
            texts=[record.meaning for record in binary_roots],
            meta={
                "entity_type": "BinaryRoot",
                "entity_ids": [record.binary_root for record in binary_roots],
                "text_field": "meaning",
                "source": "data/muajam/roots.jsonl",
            },
        ),
        EmbeddingJob(
            name="axial_meaning_embeddings",
            ids=[record.tri_root for record in triliteral_roots],
            texts=[record.axial_meaning for record in triliteral_roots],
            meta={
                "entity_type": "TriliteralRoot",
                "entity_ids": [record.tri_root for record in triliteral_roots],
                "text_field": "axial_meaning",
                "source": "data/muajam/roots.jsonl",
            },
        ),
    ]


def compute_and_save_embeddings(
    *,
    embedder: Any | None = None,
    features_dir: Path | None = None,
) -> list[dict[str, Any]]:
    embedder = embedder or BgeM3Embedder()
    summaries: list[dict[str, Any]] = []
    for job in build_embedding_jobs():
        vectors = embedder.embed(job.texts)
        meta = {
            **job.meta,
            "model_used": "BAAI/bge-m3",
        }
        save_feature(job.name, vectors, meta, features_dir=features_dir)
        summaries.append(
            {
                "name": job.name,
                "shape": list(vectors.shape),
                "count": len(job.ids),
                "feature_path": str((features_dir or FEATURES_DIR) / f"{job.name}.npy"),
            }
        )
    return summaries


def main() -> int:
    summaries = compute_and_save_embeddings()
    print(json.dumps({"features_dir": str(FEATURES_DIR), "saved": summaries}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
