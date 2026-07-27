"""
Robustness and Walk-Forward Validation Engine for Research OS.
Rejects fragile or overfitted strategies through rolling walk-forward slices and regime stress tests.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
from datetime import datetime
from trading_bot.research.core.interfaces import StandardizedDataset, ResearchStrategy
from trading_bot.research.validation.backtest import RealisticResearchBacktester

import logging
logger = logging.getLogger(__name__)


class RobustnessTester:
    """
    Validates parameter sensitivity, structural breaks,
    and out-of-sample performance across rolling market windows.
    """

    def __init__(self, backtester: RealisticResearchBacktester = None):
        self.backtester = backtester or RealisticResearchBacktester()

    def walk_forward_validation(
        self,
        strategy_class: Any,
        alpha_signal: Any,
        dataset: StandardizedDataset,
        train_ratio: float = 0.7,
        num_windows: int = 4
    ) -> Dict[str, Any]:
        """
        Executes sliding out-of-sample checks.
        Splits data chronologically into rolling train/test validation segments.
        """
        total_len = len(dataset.timestamps)
        window_size = int(total_len / (num_windows + 1))

        train_perf = []
        test_perf = []

        for w in range(num_windows):
            start_idx = w * window_size
            train_end_idx = start_idx + int(window_size * train_ratio)
            test_end_idx = start_idx + window_size

            if test_end_idx > total_len:
                break

            # Create sub-datasets
            train_sub = self._slice_dataset(dataset, start_idx, train_end_idx)
            test_sub = self._slice_dataset(dataset, train_end_idx, test_end_idx)

            # Synthesize strategies for the slices
            # Since strategy instances contain frozen signals, we slice their alpha arrays accordingly
            sliced_alpha_train = self._slice_alpha(alpha_signal, start_idx, train_end_idx)
            sliced_alpha_test = self._slice_alpha(alpha_signal, train_end_idx, test_end_idx)

            strat_train = strategy_class(
                strategy_id=f"strat_wf_train_{w}",
                name="WF_Train",
                alpha_signal=sliced_alpha_train,
                threshold=1.0
            )
            strat_test = strategy_class(
                strategy_id=f"strat_wf_test_{w}",
                name="WF_Test",
                alpha_signal=sliced_alpha_test,
                threshold=1.0
            )

            # Backtest
            try:
                train_res = self.backtester.run_backtest(strat_train, train_sub)
                test_res = self.backtester.run_backtest(strat_test, test_sub)

                train_perf.append(train_res["sharpe"])
                test_perf.append(test_res["sharpe"])
            except Exception as e:
                logger.error(f"Error in walk-forward window {w}: {e}")

        # Robustness Criteria: if test Sharpe is drastically lower than train Sharpe,
        # or negative, the strategy is deemed fragile/overfitted.
        avg_train_sharpe = float(np.mean(train_perf)) if train_perf else 0.0
        avg_test_sharpe = float(np.mean(test_perf)) if test_perf else 0.0

        passed = (avg_test_sharpe > 0.5) and (avg_test_sharpe >= 0.5 * avg_train_sharpe)

        return {
            "passed": passed,
            "avg_train_sharpe": avg_train_sharpe,
            "avg_test_sharpe": avg_test_sharpe,
            "train_sharpes": train_perf,
            "test_sharpes": test_perf,
            "conclusion": "Passed Walk-Forward (Robust)" if passed else "Failed Walk-Forward (Overfitted/Fragile)"
        }

    def regime_stress_test(self, strategy: ResearchStrategy, dataset: StandardizedDataset) -> Dict[str, Any]:
        """
        Runs the backtester on high-volatility versus low-volatility regimes.
        Rejects strategies that blow up or fail during market transitions.
        """
        symbol = dataset.symbols[0]
        close_col = f"{symbol}_close"
        prices = dataset.data[close_col]

        # Determine rolling volatility to classify regimes
        returns = np.zeros_like(prices)
        returns[1:] = np.diff(prices) / prices[:-1]

        window = 20
        rolling_vol = np.zeros_like(prices)
        for i in range(window, len(prices)):
            rolling_vol[i] = np.std(returns[i-window:i])

        median_vol = np.median(rolling_vol[window:])

        # Slices indices matching regimes
        high_vol_mask = rolling_vol > median_vol
        low_vol_mask = rolling_vol <= median_vol

        high_vol_indices = np.where(high_vol_mask)[0]
        low_vol_indices = np.where(low_vol_mask)[0]

        # Run stress test on combined periods or contiguous blocks
        # For simplicity, we run a unified stress-test of high-vol segment performance
        high_vol_sub = self._slice_indexed_dataset(dataset, high_vol_indices)
        low_vol_sub = self._slice_indexed_dataset(dataset, low_vol_indices)

        # Slices strategy alpha
        alpha_high = self._slice_indexed_alpha(strategy.alpha_signal, high_vol_indices)
        alpha_low = self._slice_indexed_alpha(strategy.alpha_signal, low_vol_indices)

        strat_high = strategy.__class__(
            strategy_id="strat_regime_high",
            name="Regime_High",
            alpha_signal=alpha_high,
            threshold=strategy.threshold
        )
        strat_low = strategy.__class__(
            strategy_id="strat_regime_low",
            name="Regime_Low",
            alpha_signal=alpha_low,
            threshold=strategy.threshold
        )

        try:
            high_res = self.backtester.run_backtest(strat_high, high_vol_sub)
            low_res = self.backtester.run_backtest(strat_low, low_vol_sub)

            # Robustness condition: Max drawdown in high-vol regime must not exceed 25%
            passed = (high_res["max_drawdown"] > -0.25) and (low_res["max_drawdown"] > -0.20)

            return {
                "passed": passed,
                "high_vol_regime": {
                    "sharpe": high_res["sharpe"],
                    "max_drawdown": high_res["max_drawdown"],
                    "return": high_res["total_return"]
                },
                "low_vol_regime": {
                    "sharpe": low_res["sharpe"],
                    "max_drawdown": low_res["max_drawdown"],
                    "return": low_res["total_return"]
                },
                "conclusion": "Robust across regimes" if passed else "Fragile under stress (excessive high-vol drawdown)"
            }
        except Exception as e:
            logger.error(f"Error in regime stress testing: {e}")
            return {"passed": False, "error": str(e)}

    def _slice_dataset(self, dataset: StandardizedDataset, start: int, end: int) -> StandardizedDataset:
        sliced_data = {}
        for col, arr in dataset.data.items():
            sliced_data[col] = arr[start:end]

        return StandardizedDataset(
            dataset_id=f"{dataset.dataset_id}_slice_{start}_{end}",
            asset_class=dataset.asset_class,
            symbols=dataset.symbols,
            timeframe=dataset.timeframe,
            start_time=dataset.start_time,
            end_time=dataset.end_time,
            data=sliced_data,
            timestamps=dataset.timestamps[start:end],
            metadata=dataset.metadata,
            provenance=dataset.provenance
        )

    def _slice_indexed_dataset(self, dataset: StandardizedDataset, indices: np.ndarray) -> StandardizedDataset:
        sliced_data = {}
        for col, arr in dataset.data.items():
            sliced_data[col] = arr[indices]

        return StandardizedDataset(
            dataset_id=f"{dataset.dataset_id}_indexed_slice",
            asset_class=dataset.asset_class,
            symbols=dataset.symbols,
            timeframe=dataset.timeframe,
            start_time=dataset.start_time,
            end_time=dataset.end_time,
            data=sliced_data,
            timestamps=dataset.timestamps[indices],
            metadata=dataset.metadata,
            provenance=dataset.provenance
        )

    def _slice_alpha(self, alpha_signal: Any, start: int, end: int) -> Any:
        from copy import copy
        new_alpha = copy(alpha_signal)
        new_alpha.values = alpha_signal.values[start:end]
        new_alpha.timestamps = alpha_signal.timestamps[start:end]
        return new_alpha

    def _slice_indexed_alpha(self, alpha_signal: Any, indices: np.ndarray) -> Any:
        from copy import copy
        new_alpha = copy(alpha_signal)
        new_alpha.values = alpha_signal.values[indices]
        new_alpha.timestamps = alpha_signal.timestamps[indices]
        return new_alpha
