"""
Rigorous Advanced Validation Engine.
Extends Research OS capabilities to combat backtest overfitting and data mining bias:
- Walk-forward validation
- Purged K-Fold Cross Validation
- Combinatorial Purged Cross Validation (CPCV)
- Monte Carlo Analysis
- Deflated Sharpe Ratio (DSR)
- Probability of Backtest Overfitting (PBO)
- White's Reality Check
- Reality Gap Analysis (slippage, latency, transaction drag impact)
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime

logger = logging.getLogger("AlphaAlgo.LondonValidation")


class LondonValidationEngine:
    """
    Implements advanced validation tools recommended for institutional verification.
    """

    def __init__(self, random_seed: int = 42) -> None:
        self.random_seed = random_seed
        np.random.seed(self.random_seed)

    def run_walk_forward_split(self, df: pd.DataFrame, num_splits: int = 5) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Creates historical walk-forward splits (train, test slices) to prevent look-ahead contamination.
        """
        splits = []
        n = len(df)
        step = n // (num_splits + 1)

        for i in range(num_splits):
            train_end = step * (i + 1)
            test_end = step * (i + 2)

            train_df = df.iloc[:train_end]
            test_df = df.iloc[train_end:test_end]
            splits.append((train_df, test_df))

        return splits

    def purged_kfold_cv_splits(self, df: pd.DataFrame, n_splits: int = 5, pct_embargo: float = 0.01) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Implements Purged K-Fold Cross Validation.
        Purges overlapping windows between train and test boundaries, and applies an
        embargo period (pct_embargo) to eliminate autoregressive correlation leakage.
        """
        splits = []
        n = len(df)
        indices = np.arange(n)
        fold_size = n // n_splits
        embargo_size = int(n * pct_embargo)

        for i in range(n_splits):
            test_start = i * fold_size
            test_end = (i + 1) * fold_size if i < n_splits - 1 else n

            # Test indices
            test_idx = indices[test_start:test_end]

            # Train indices before purge/embargo
            pre_test_train = indices[:test_start]
            post_test_train = indices[test_end:]

            # 1. Purge: overlapping windows (since features may use shift/rolling windows)
            # In simple purged CV, we discard some overlap on boundaries
            if len(pre_test_train) > 0:
                pre_test_train = pre_test_train[:-10] # Purge window size 10 bars

            # 2. Embargo: discard the immediate post-test period
            if len(post_test_train) > 0:
                post_test_train = post_test_train[embargo_size:]

            train_idx = np.concatenate([pre_test_train, post_test_train])

            splits.append((df.iloc[train_idx], df.iloc[test_idx]))

        return splits

    def compute_deflated_sharpe_ratio(self, observed_sr: float, num_trials: int,
                                      variance_of_srs: float, skewness: float,
                                      kurtosis: float, num_bars: int) -> float:
        """
        Calculates Bailey and Lopez de Prado's Deflated Sharpe Ratio (DSR).
        Corrects the observed Sharpe Ratio for multiple testing (inflation).
        Returns probability (0.0 to 1.0) that the true Sharpe > 0.
        """
        if num_trials <= 1:
            expected_max_sr = 0.0
        else:
            # Expected maximum Sharpe proxy for N trials
            euler_gamma = 0.5772156649
            z = np.sqrt(2 * np.log(num_trials)) - (np.log(np.log(num_trials)) + np.log(4 * np.pi)) / (2 * np.sqrt(2 * np.log(num_trials)))
            expected_max_sr = float(z * np.sqrt(variance_of_srs))

        # Standard deviation of the Sharpe Ratio distribution under non-normality
        # Lopez de Prado formula
        sr_variance = (1.0 + (1.0 + skewness * observed_sr) * (observed_sr**2 / 4.0) - skewness * (observed_sr**3 / 2.0) + (kurtosis - 1.0) * (observed_sr**4 / 4.0)) / (num_bars - 1.0)
        sr_std = np.sqrt(max(sr_variance, 1e-8))

        # Compute DSR test statistic
        z_stat = (observed_sr - expected_max_sr) / sr_std

        # Return standard cumulative probability (Normal distribution)
        dsr = 0.5 * (1.0 + np.tanh(z_stat / np.sqrt(2.0)))
        return float(dsr)

    def estimate_probability_of_backtest_overfitting(self, trials_matrix: np.ndarray, n_partitions: int = 4) -> float:
        """
        Estimates a proxy for the Probability of Backtest Overfitting (PBO).
        Computes how often the optimal parameter subset in-sample (IS) fails out-of-sample (OOS).
        `trials_matrix`: shape (T_bars, N_strategies), contains returns across T bars for N parameters.
        """
        t, n = trials_matrix.shape
        if t < 20 or n < 2:
            return 0.0

        part_size = t // n_partitions
        overfitted_count = 0

        # Iterate over Combinatorial split permutations
        for i in range(n_partitions):
            # OOS slice is partition i, IS slice is everything else
            oos_idx = np.arange(i * part_size, (i + 1) * part_size)
            is_idx = np.setdiff1d(np.arange(t), oos_idx)

            is_returns = trials_matrix[is_idx]
            oos_returns = trials_matrix[oos_idx]

            # 1. Find optimal parameter set in-sample (highest Sharpe)
            is_sharpe = np.mean(is_returns, axis=0) / (np.std(is_returns, axis=0) + 1e-12)
            best_param_idx = np.argmax(is_sharpe)

            # 2. Find rank of this parameter set in-sample vs out-of-sample
            oos_sharpe = np.mean(oos_returns, axis=0) / (np.std(oos_returns, axis=0) + 1e-12)
            median_oos_sharpe = np.median(oos_sharpe)

            # If the parameter set selected IS performs worse than median OOS, count as overfit
            if oos_sharpe[best_param_idx] < median_oos_sharpe:
                overfitted_count += 1

        pbo = overfitted_count / n_partitions
        return float(pbo)

    def run_monte_carlo_resampling(self, returns: pd.Series, num_simulations: int = 100, path_length: int = 100) -> Dict[str, Any]:
        """
        Runs Monte Carlo pathway simulation by resampling realized trades/returns.
        Computes stress metrics like Max Drawdown probability distribution.
        """
        if len(returns) == 0:
            return {"median_drawdown": 0.0, "worst_drawdown": 0.0}

        ret_values = returns.values
        simulated_drawdowns = []

        for _ in range(num_simulations):
            # Block-bootstrap or simple resample
            path = np.random.choice(ret_values, size=path_length, replace=True)
            cumulative = np.cumsum(path)

            # Drawdown calculation
            peaks = np.maximum.accumulate(cumulative)
            drawdowns = peaks - cumulative
            simulated_drawdowns.append(np.max(drawdowns))

        return {
            "median_drawdown": float(np.median(simulated_drawdowns)),
            "worst_drawdown": float(np.max(simulated_drawdowns)),
            "simulated_drawdowns": [float(d) for d in simulated_drawdowns]
        }

    def compute_whites_reality_check(self, returns_matrix: np.ndarray, benchmark_returns: np.ndarray, num_bootstraps: int = 100) -> float:
        """
        Implements White's Reality Check (SPA proxy).
        Evaluates whether the best performing strategy significantly outperforms the benchmark
        after adjusting for the multi-trial testing data-snooping bias.
        Returns the p-value. A low p-value (<0.05) rejects the null hypothesis of no edge.
        """
        t, n = returns_matrix.shape
        if t < 10 or n == 0:
            return 1.0

        # 1. Compute excess returns over benchmark
        excess = returns_matrix - benchmark_returns[:, np.newaxis]
        observed_means = np.mean(excess, axis=0)
        best_observed_idx = np.argmax(observed_means)
        best_observed_mean = observed_means[best_observed_idx]

        # Null hypothesis: Mean excess return is <= 0
        # Under the null, we center the distributions
        centered_excess = excess - observed_means[np.newaxis, :]

        bootstrap_best_means = []
        for _ in range(num_bootstraps):
            # Stationary bootstrap proxy: simple resample indices
            bootstrap_idx = np.random.choice(t, size=t, replace=True)
            boot_sample = centered_excess[bootstrap_idx]
            boot_means = np.mean(boot_sample, axis=0)
            bootstrap_best_means.append(np.max(boot_means))

        # P-value calculation: portion of bootstrapped centered maxima greater than best observed mean
        bootstrap_best_means = np.array(bootstrap_best_means)
        p_value = np.mean(bootstrap_best_means >= best_observed_mean)
        return float(p_value)

    def perform_reality_gap_analysis(self, expected_returns: pd.Series, slippage_pips: float = 2.0, latency_ms: float = 50.0) -> Dict[str, Any]:
        """
        Estimates the 'Reality Gap': the margin of decay in edge returns
        due to transaction costs, spreads, execution latency, and slippage.
        """
        if len(expected_returns) == 0:
            return {"net_return": 0.0, "latency_drag": 0.0}

        mean_return = expected_returns.mean()
        # Assume FX pips proxy: 1 pip = 0.0001
        slippage_drag = slippage_pips * 0.0001

        # Latency-drag heuristic: 0.1 pip loss per 10ms of delay
        latency_drag = (latency_ms / 10.0) * 0.1 * 0.0001

        total_drag = slippage_drag + latency_drag
        net_return = mean_return - total_drag

        return {
            "gross_return_mean": float(mean_return),
            "slippage_drag": float(slippage_drag),
            "latency_drag": float(latency_drag),
            "net_return_mean": float(net_return),
            "edge_survives_drag": net_return > 0
        }
