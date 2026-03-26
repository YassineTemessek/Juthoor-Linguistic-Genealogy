from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
from scipy import stats


ArrayLike = Sequence[float] | np.ndarray


def _as_1d(values: ArrayLike) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1:
        raise ValueError("expected a 1D array")
    return arr


def _upper_triangle(matrix: np.ndarray) -> np.ndarray:
    arr = np.asarray(matrix, dtype=float)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise ValueError("Mantel test requires square matrices")
    idx = np.triu_indices(arr.shape[0], k=1)
    return arr[idx]


def mantel_test(
    dist_matrix_1: ArrayLike,
    dist_matrix_2: ArrayLike,
    permutations: int = 9999,
    *,
    random_state: int | None = 0,
) -> tuple[float, float]:
    a = np.asarray(dist_matrix_1, dtype=float)
    b = np.asarray(dist_matrix_2, dtype=float)
    if a.shape != b.shape:
        raise ValueError("distance matrices must have the same shape")
    x = _upper_triangle(a)
    y = _upper_triangle(b)
    if x.size == 0:
        raise ValueError("distance matrices must be at least 2x2")
    observed = float(np.corrcoef(x, y)[0, 1])
    rng = np.random.default_rng(random_state)
    hits = 0
    for _ in range(int(permutations)):
        perm = rng.permutation(a.shape[0])
        permuted = b[np.ix_(perm, perm)]
        perm_y = _upper_triangle(permuted)
        perm_r = float(np.corrcoef(x, perm_y)[0, 1])
        if abs(perm_r) >= abs(observed):
            hits += 1
    p_value = (hits + 1) / float(permutations + 1)
    return observed, p_value


def bootstrap_ci(
    values: ArrayLike,
    stat_fn: Callable[[np.ndarray], float],
    n_boot: int = 10000,
    alpha: float = 0.05,
    *,
    random_state: int | None = 0,
) -> tuple[float, float]:
    arr = _as_1d(values)
    if arr.size == 0:
        raise ValueError("values must be non-empty")
    rng = np.random.default_rng(random_state)
    stats_boot = np.empty(int(n_boot), dtype=float)
    for i in range(int(n_boot)):
        sample = rng.choice(arr, size=arr.size, replace=True)
        stats_boot[i] = float(stat_fn(sample))
    low = float(np.quantile(stats_boot, alpha / 2))
    high = float(np.quantile(stats_boot, 1 - alpha / 2))
    return low, high


def permutation_test(
    group_a: ArrayLike,
    group_b: ArrayLike,
    stat_fn: Callable[[np.ndarray], float],
    n_perm: int = 9999,
    *,
    random_state: int | None = 0,
) -> float:
    a = _as_1d(group_a)
    b = _as_1d(group_b)
    if a.size == 0 or b.size == 0:
        raise ValueError("both groups must be non-empty")
    observed = float(stat_fn(a) - stat_fn(b))
    combined = np.concatenate([a, b])
    size_a = a.size
    rng = np.random.default_rng(random_state)
    hits = 0
    for _ in range(int(n_perm)):
        perm = rng.permutation(combined)
        perm_a = perm[:size_a]
        perm_b = perm[size_a:]
        diff = float(stat_fn(perm_a) - stat_fn(perm_b))
        if abs(diff) >= abs(observed):
            hits += 1
    return (hits + 1) / float(n_perm + 1)


def cohens_d(group_a: ArrayLike, group_b: ArrayLike) -> float:
    a = _as_1d(group_a)
    b = _as_1d(group_b)
    if a.size < 2 or b.size < 2:
        raise ValueError("Cohen's d requires at least two values per group")
    var_a = np.var(a, ddof=1)
    var_b = np.var(b, ddof=1)
    pooled = np.sqrt(((a.size - 1) * var_a + (b.size - 1) * var_b) / (a.size + b.size - 2))
    if pooled == 0:
        return 0.0
    return float((np.mean(a) - np.mean(b)) / pooled)


def spearman_corr(x: ArrayLike, y: ArrayLike) -> tuple[float, float]:
    result = stats.spearmanr(_as_1d(x), _as_1d(y))
    return float(result.statistic), float(result.pvalue)


def wilcoxon_rank_sum(group_a: ArrayLike, group_b: ArrayLike) -> tuple[float, float]:
    result = stats.ranksums(_as_1d(group_a), _as_1d(group_b))
    return float(result.statistic), float(result.pvalue)


def kruskal_wallis(*groups: ArrayLike) -> tuple[float, float]:
    if len(groups) < 2:
        raise ValueError("kruskal_wallis requires at least two groups")
    arrays = [_as_1d(group) for group in groups]
    result = stats.kruskal(*arrays)
    return float(result.statistic), float(result.pvalue)

