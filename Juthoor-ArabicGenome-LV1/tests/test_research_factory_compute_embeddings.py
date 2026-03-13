from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

import numpy as np


def _load_module(name: str, rel_path: str):
    path = Path(__file__).resolve().parents[1] / rel_path
    spec = spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


module = _load_module(
    "rf_compute_embeddings",
    "scripts/research_factory/phase0_setup/compute_all_embeddings.py",
)


class DummyEmbedder:
    def embed(self, texts):
        rows = len(texts)
        base = np.arange(rows * 4, dtype=np.float32).reshape(rows, 4)
        return base


def test_build_embedding_jobs_reads_expected_counts():
    jobs = module.build_embedding_jobs()
    names = [job.name for job in jobs]
    assert names == ["letter_embeddings", "binary_meaning_embeddings", "axial_meaning_embeddings"]
    assert len(jobs[0].ids) == 28
    assert len(jobs[1].ids) == 457
    assert len(jobs[2].ids) == 1938


def test_compute_and_save_embeddings_round_trip(tmp_path: Path):
    summaries = module.compute_and_save_embeddings(embedder=DummyEmbedder(), features_dir=tmp_path)
    assert len(summaries) == 3
    for summary in summaries:
        npy = tmp_path / f"{summary['name']}.npy"
        meta = tmp_path / f"{summary['name']}.meta.json"
        assert npy.exists()
        assert meta.exists()
