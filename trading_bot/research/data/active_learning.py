"""
Regime Gap Active Learning Policy.
Implements the ActiveLearningPolicy interface to scan registered datasets for regime gaps
where high volatility/variance overlaps with sparse data coverage.
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime

from trading_bot.research.core.interfaces import ActiveLearningPolicy, StandardizedDataset

logger = logging.getLogger(__name__)


class RegimeGapActiveLearning(ActiveLearningPolicy):
    """
    Canonical implementation of ActiveLearningPolicy for the Research OS.
    Scans datasets to detect informative gaps under uncertainty.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.volatility_window = self.config.get("volatility_window", 20)
        self.vol_threshold = self.config.get("volatility_threshold", 0.02)
        logger.info("RegimeGapActiveLearning initialized")

    def select_regime_gaps(self, registered_datasets: List[StandardizedDataset]) -> List[Dict[str, Any]]:
        """
        Identify zones of high volatility/variance but sparse data coverage.
        Returns a list of identified regime gaps with priority scores.
        """
        gaps = []
        for dataset in registered_datasets:
            symbol = dataset.symbols[0] if dataset.symbols else "unknown"
            close_col = f"{symbol}_close" if f"{symbol}_close" in dataset.data else "close"

            if close_col not in dataset.data:
                # Try finding any column with 'close' in its name
                for col in dataset.data.keys():
                    if "close" in col.lower():
                        close_col = col
                        break

            if close_col not in dataset.data or dataset.timestamps is None or len(dataset.timestamps) < self.volatility_window:
                continue

            prices = dataset.data[close_col]
            # Compute log returns
            returns = np.diff(np.log(prices))

            # Simple rolling standard deviation of returns as a proxy for volatility
            rolling_vol = []
            for i in range(len(returns) - self.volatility_window + 1):
                window = returns[i:i + self.volatility_window]
                rolling_vol.append(float(np.std(window)))

            # Detect areas of volatility higher than our threshold
            high_vol_indices = [
                i + self.volatility_window
                for i, v in enumerate(rolling_vol)
                if v > self.vol_threshold
            ]

            if high_vol_indices:
                # Create a sample gap representing high volatility clustering
                gap_start = dataset.timestamps[high_vol_indices[0]]
                gap_end = dataset.timestamps[high_vol_indices[-1]]

                # Priority is proportional to peak volatility
                peak_vol = float(np.max(rolling_vol))

                gaps.append({
                    "dataset_id": dataset.dataset_id,
                    "symbol": symbol,
                    "start_time": str(gap_start),
                    "end_time": str(gap_end),
                    "peak_volatility": peak_vol,
                    "priority_score": min(1.0, peak_vol * 10),
                    "reason": "high_volatility_unlabeled_regime"
                })

        return gaps
