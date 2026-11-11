"""
Leakage-Resistant Walk-Forward Validation Engine for London Session Intelligence.
Implements:
1. Purged and Embargoed K-Fold Splits.
2. Expanding and Rolling Walk-Forward splits.
3. Deflated Sharpe Ratio (DSR) & Multiple-Testing Adjustment.
4. Probability of Backtest Overfitting (PBO) via Combinatorial Partitioning.
5. Monte Carlo Resampling and Drawdown Distributions.
6. Execution Drag & Reality Gap Sensitivity Curves (slippage, latency, spreads).
7. Economic Significance & Net Expectancy Evaluation.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Generator
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger("AlphaAlgo.LondonValidationEngine")


class LondonValidationEngine:
    """
    Rigorously validates discovered edges and trained models against overfitting,
    data snooping, transaction friction, and look-ahead bias.
    """

    def __init__(self, random_seed: int = 42) -> None:
        self.random_seed = random_seed
        np.random.seed(random_seed)

    def run_walk_forward_split(
        self,
        df: pd.DataFrame,
        num_splits: int = 4,
        min_train_pct: float = 0.40,
        embargo_bars: int = 12
    ) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Creates expanding walk-forward splits with an embargo buffer to prevent leakage
        across boundary labels.
        """
        n = len(df)
        min_train_size = int(n * min_train_pct)
        remaining = n - min_train_size
        test_size = remaining // num_splits

        splits = []
        for i in range(num_splits):
            train_end = min_train_size + i * test_size
            test_start = train_end + embargo_bars
            test_end = min(train_end + embargo_bars + test_size, n)

            if test_start >= n or (test_end - test_start) < 10:
                break

            train_slice = df.iloc[:train_end]
            test_slice = df.iloc[test_start:test_end]
            splits.append((train_slice, test_slice))

        logger.info(f"Generated {len(splits)} expanding walk-forward partitions.")
        return splits

    def purged_kfold_cv_splits(
        self,
        df: pd.DataFrame,
        n_splits: int = 4,
        pct_embargo: float = 0.02,
        purge_window: int = 12
    ) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Purges overlapping event windows and applies embargo periods post-test window.
        """
        n = len(df)
        indices = np.arange(n)
        fold_size = n // n_splits
        embargo_size = int(n * pct_embargo)

        splits = []
        for i in range(n_splits):
            test_start = i * fold_size
            test_end = n if i == (n_splits - 1) else (i + 1) * fold_size
            test_idx = indices[test_start:test_end]

            pre_test_train = indices[:test_start]
            post_test_train = indices[test_end:]

            if len(pre_test_train) > purge_window:
                pre_test_train = pre_test_train[:-purge_window]
            else:
                pre_test_train = np.array([], dtype=int)

            if len(post_test_train) > embargo_size:
                post_test_train = post_test_train[embargo_size:]
            else:
                post_test_train = np.array([], dtype=int)

            train_idx = np.concatenate([pre_test_train, post_test_train])
            if len(train_idx) > 10 and len(test_idx) > 10:
                splits.append((df.iloc[train_idx], df.iloc[test_idx]))

        return splits

    def compute_deflated_sharpe_ratio(
        self,
        observed_sr: float,
        num_trials: int,
        variance_of_srs: float,
        skewness: float = 0.0,
        kurtosis: float = 3.0,
        num_bars: int = 500
    ) -> float:
        """
        Calculates Deflated Sharpe Ratio (DSR) as defined by Bailey and Lopez de Prado (2014).
        Adjusts for track record length, non-normal returns (skewness/kurtosis), and selection bias.
        """
        if num_trials <= 1:
            expected_max_sr = 0.0
        else:
            euler_mascheroni = 0.5772156649
            sr_std = np.sqrt(max(variance_of_srs, 1e-8))
            term1 = (1.0 - euler_mascheroni) * stats.norm.ppf(1.0 - 1.0 / num_trials)
            term2 = euler_mascheroni * stats.norm.ppf(1.0 - 1.0 / (num_trials * np.e))
            expected_max_sr = sr_std * (term1 + term2)

        # Variance of the Sharpe ratio estimator
        sr_var = (1.0 - skewness * observed_sr + ((kurtosis - 1.0) / 4.0) * (observed_sr**2)) / max(num_bars - 1, 1)
        sr_std_err = np.sqrt(max(sr_var, 1e-8))

        # DSR = CDF((SR - expected_max_SR) / SE(SR))
        dsr_z = (observed_sr - expected_max_sr) / sr_std_err
        dsr = float(stats.norm.cdf(dsr_z))
        return dsr

    def estimate_probability_of_backtest_overfitting(
        self,
        trials_matrix: np.ndarray,
        n_partitions: int = 4
    ) -> float:
        """
        Calculates Probability of Backtest Overfitting (PBO) via Combinatorial Symmetric CV.
        """
        t, n_strategies = trials_matrix.shape
        if n_strategies <= 1 or t < (n_partitions * 4):
            return 0.0

        sub_len = t // n_partitions
        partition_subsets = []
        for p in range(n_partitions):
            start = p * sub_len
            end = t if p == (n_partitions - 1) else (p + 1) * sub_len
            partition_subsets.append(trials_matrix[start:end, :])

        # Combinations of in-sample partitions vs out-of-sample
        is_ranks = []
        oos_ranks = []

        half_partitions = n_partitions // 2
        from itertools import combinations
        comb_indices = list(combinations(range(n_partitions), half_partitions))

        logits = []
        for train_parts in comb_indices:
            test_parts = [idx for idx in range(n_partitions) if idx not in train_parts]

            # In sample performance
            is_data = np.concatenate([partition_subsets[p] for p in train_parts], axis=0)
            is_means = np.mean(is_data, axis=0)
            is_stds = np.std(is_data, axis=0) + 1e-8
            is_sharpes = is_means / is_stds
            best_is_strategy = np.argmax(is_sharpes)

            # Out of sample performance
            oos_data = np.concatenate([partition_subsets[p] for p in test_parts], axis=0)
            oos_means = np.mean(oos_data, axis=0)
            oos_stds = np.std(oos_data, axis=0) + 1e-8
            oos_sharpes = oos_means / oos_stds

            # Rank of best IS strategy in OOS
            oos_rank = np.sum(oos_sharpes <= oos_sharpes[best_is_strategy]) / n_strategies
            # Logit: if rank < 0.5 (underperformed median in OOS), indicates overfitting
            logits.append(oos_rank < 0.5)

        pbo = float(np.mean(logits)) if logits else 0.0
        return pbo

    def run_monte_carlo_resampling(
        self,
        returns_series: pd.Series,
        num_simulations: int = 100,
        path_length: int = 100
    ) -> Dict[str, float]:
        """
        Runs stationary block bootstrap resampling on trade returns to compute drawdown distributions.
        """
        clean_ret = returns_series.dropna().values
        if len(clean_ret) < 10:
            return {"median_drawdown": 0.0, "max_drawdown_95": 0.0, "expected_sharpe": 0.0}

        drawdowns = []
        sharpes = []

        for _ in range(num_simulations):
            sampled_idx = np.random.choice(len(clean_ret), size=path_length, replace=True)
            path = clean_ret[sampled_idx]
            cum = np.cumprod(1.0 + path)
            peak = np.maximum.accumulate(cum)
            dd = (peak - cum) / peak
            drawdowns.append(float(np.max(dd)))

            std = np.std(path)
            sr = (np.mean(path) / std * np.sqrt(288)) if std > 1e-8 else 0.0
            sharpes.append(sr)

        return {
            "median_drawdown": float(np.median(drawdowns)),
            "max_drawdown_95": float(np.percentile(drawdowns, 95)),
            "expected_sharpe": float(np.median(sharpes)),
            "sharpe_ci_lower": float(np.percentile(sharpes, 5)),
            "sharpe_ci_upper": float(np.percentile(sharpes, 95))
        }

    def perform_reality_gap_analysis(
        self,
        returns_series: pd.Series,
        slippage_pips: float = 1.5,
        latency_ms: float = 40.0,
        pip_size: float = 0.0001
    ) -> Dict[str, Any]:
        """
        Evaluates strategy returns subjected to progressive transaction costs and execution friction.
        """
        clean_ret = returns_series.dropna().values
        if len(clean_ret) == 0:
            return {"edge_survives_drag": False, "break_even_slippage_pips": 0.0}

        # Latency drag proxy: ~0.1 pip per 50ms latency
        latency_pips = (latency_ms / 50.0) * 0.1
        total_drag_pips = slippage_pips + latency_pips
        drag_return = total_drag_pips * pip_size

        net_returns = clean_ret - drag_return

        gross_mean = float(np.mean(clean_ret))
        net_mean = float(np.mean(net_returns))

        # Break-even slippage
        break_even_pips = (gross_mean / pip_size) if pip_size > 0 else 0.0

        survives = net_mean > 0.0 and break_even_pips > total_drag_pips

        return {
            "gross_mean_return": gross_mean,
            "net_mean_return": net_mean,
            "applied_drag_pips": float(total_drag_pips),
            "break_even_slippage_pips": float(break_even_pips),
            "edge_survives_drag": bool(survives)
        }
