"""Multiple-hypothesis correction and backtest-overfitting statistics.

Every helper returns ``None`` when its statistical preconditions are unmet —
the caller must treat ``None`` as "unsupported", never as a pass.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
from typing import Any, Dict, List, Optional, Sequence

import numpy as np


def block_bootstrap_lower(
    diffs: Sequence[float],
    block_size: int,
    alpha: float,
    seed: int,
    draws: int = 256,
) -> Optional[float]:
    """Lower alpha-confidence bound on the mean of paired differences.

    Stationary-style block resampling preserves local dependence. Returns
    ``None`` when fewer than 5 blocks fit (insufficient effective sample).
    """
    n = len(diffs)
    if block_size < 1 or n // block_size < 5:
        return None
    rng = random.Random(seed)
    boot: List[float] = []
    for _ in range(draws):
        chunk: List[float] = []
        while len(chunk) < n:
            start = rng.randrange(n)
            chunk.extend(diffs[(start + j) % n] for j in range(block_size))
        boot.append(sum(chunk[:n]) / n)
    boot.sort()
    return boot[max(0, int(alpha * len(boot)))]


def contract_seed(contract: Dict[str, Any], salt: str = "") -> int:
    payload = json.dumps(contract, sort_keys=True, default=str).encode() + salt.encode()
    return int(hashlib.sha256(payload).hexdigest()[:16], 16)


def bonferroni_alpha(trial_count: int, confidence: float) -> float:
    if trial_count < 1 or not 0 < confidence < 1:
        raise ValueError("invalid trial count or confidence")
    return (1.0 - confidence) / trial_count


def holm_rejections(p_values: Sequence[float], alpha: float) -> Optional[List[bool]]:
    """Holm step-down family-wise control over a family of p-values."""
    if not p_values or not 0 < alpha < 1:
        return None
    indexed = sorted(enumerate(p_values), key=lambda kv: kv[1])
    m = len(indexed)
    out = [False] * m
    for rank, (idx, p) in enumerate(indexed):
        if p <= alpha / (m - rank):
            out[idx] = True
        else:
            break
    return out


def deflated_sharpe_ratio(
    observed_sr: float,
    trial_srs: Sequence[float],
    n_obs: int,
    skew: float = 0.0,
    kurtosis: float = 3.0,
) -> Optional[Dict[str, float]]:
    """Bailey & Lopez de Prado deflated Sharpe ratio.

    Probability that `observed_sr` exceeds the expected maximum Sharpe of the
    trial family under non-normal returns. ``None`` when <2 trials or too few
    observations make the estimate meaningless.
    """
    from scipy import stats

    n_trials = len(trial_srs)
    if n_trials < 2 or n_obs < 10 or not math.isfinite(observed_sr):
        return None
    sr_std = float(np.std(trial_srs, ddof=1))
    if sr_std <= 0:
        return None
    gamma = 0.5772156649015329  # Euler-Mascheroni
    e_max = sr_std * (
        (1.0 - gamma) * stats.norm.ppf(1.0 - 1.0 / n_trials)
        + gamma * stats.norm.ppf(1.0 - 1.0 / (n_trials * math.e))
    )
    denom = 1.0 - skew * observed_sr + ((kurtosis - 1.0) / 4.0) * observed_sr ** 2
    if denom <= 0:
        return None
    z = (observed_sr - e_max) * math.sqrt(n_obs - 1) / math.sqrt(denom)
    return {
        "dsr": float(stats.norm.cdf(z)),
        "expected_max_sr": float(e_max),
        "n_trials": float(n_trials),
    }


def pbo_cscv(performance_matrix: Sequence[Sequence[float]]) -> Optional[float]:
    """Probability of backtest overfitting via combinatorially symmetric CV.

    `performance_matrix` is candidates x folds of comparable per-fold metrics.
    Returns PBO in [0, 1] or ``None`` below 4 folds / 4 candidates.
    """
    matrix = np.asarray(performance_matrix, dtype=float)
    n_candidates, n_folds = matrix.shape
    if n_candidates < 4 or n_folds < 4 or n_folds % 2 != 0:
        return None
    fold_ids = list(range(n_folds))
    half = n_folds // 2
    overfit = 0
    combos = 0
    for train_folds in itertools.combinations(fold_ids, half):
        test_folds = tuple(f for f in fold_ids if f not in train_folds)
        train_perf = matrix[:, list(train_folds)].mean(axis=1)
        test_perf = matrix[:, list(test_folds)].mean(axis=1)
        best = int(np.argmax(train_perf))
        rank = int(np.sum(test_perf > test_perf[best]))
        # position of the IS winner in the OOS distribution
        rel_rank = (n_candidates - rank) / (n_candidates + 1.0)
        if rel_rank <= 0.5:
            overfit += 1
        combos += 1
    return overfit / combos if combos else None
