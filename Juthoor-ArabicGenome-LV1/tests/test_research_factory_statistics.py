from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np


def _load_module(name: str, rel_path: str):
    path = Path(__file__).resolve().parents[1] / rel_path
    spec = spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


stats_mod = _load_module("rf_statistics", "scripts/research_factory/common/statistics.py")


def test_mantel_test_detects_positive_correlation():
    a = np.array(
        [
            [0.0, 1.0, 2.0, 3.0],
            [1.0, 0.0, 1.5, 2.5],
            [2.0, 1.5, 0.0, 1.0],
            [3.0, 2.5, 1.0, 0.0],
        ]
    )
    b = np.array(
        [
            [0.0, 1.1, 2.1, 3.2],
            [1.1, 0.0, 1.4, 2.6],
            [2.1, 1.4, 0.0, 1.2],
            [3.2, 2.6, 1.2, 0.0],
        ]
    )
    r, p = stats_mod.mantel_test(a, b, permutations=499, random_state=42)
    assert r > 0.95
    assert p < 0.05


def test_bootstrap_ci_contains_sample_mean():
    values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    low, high = stats_mod.bootstrap_ci(values, np.mean, n_boot=500, random_state=42)
    assert low <= np.mean(values) <= high


def test_permutation_test_detects_group_difference():
    group_a = np.array([10, 11, 12, 13, 14], dtype=float)
    group_b = np.array([1, 2, 3, 4, 5], dtype=float)
    p_value = stats_mod.permutation_test(group_a, group_b, np.mean, n_perm=999, random_state=42)
    assert p_value < 0.05


def test_cohens_d_positive_for_separated_groups():
    d = stats_mod.cohens_d([5, 6, 7, 8], [1, 2, 3, 4])
    assert d > 1.0


def test_stat_wrappers_return_stat_and_pvalue():
    rho, p = stats_mod.spearman_corr([1, 2, 3], [1, 2, 3])
    assert rho == 1.0
    assert p == 0.0
    stat, p2 = stats_mod.wilcoxon_rank_sum([10, 11, 12], [1, 2, 3])
    assert stat != 0.0
    assert 0.0 <= p2 <= 1.0
    stat3, p3 = stats_mod.kruskal_wallis([1, 2, 3], [4, 5, 6], [7, 8, 9])
    assert stat3 > 0.0
    assert 0.0 <= p3 <= 1.0
