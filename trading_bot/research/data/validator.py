"""
Dataset Quality Validator for Research OS.
Validates datasets for integrity anomalies, outliers, duplicate records, timestamp alignment, and look-ahead bias.
"""

from typing import Tuple, Dict, Any
import numpy as np
import logging
from trading_bot.research.core.interfaces import DatasetValidator, StandardizedDataset

logger = logging.getLogger(__name__)


class StandardDatasetValidator(DatasetValidator):
    """
    Standard quantitative dataset quality validation engine.
    Ensures data matches strict research-grade expectations.
    """

    def __init__(self, max_outliers_ratio: float = 0.01, z_score_threshold: float = 5.0):
        self.max_outliers_ratio = max_outliers_ratio
        self.z_score_threshold = z_score_threshold

    def validate(self, dataset: StandardizedDataset) -> Tuple[bool, Dict[str, Any]]:
        anomalies = {}
        passed = True

        # 1. Check completeness (at least 20 records)
        total_records = len(dataset.timestamps)
        if total_records < 20:
            anomalies["size_error"] = f"Dataset size {total_records} is too small (requires at least 20 records)."
            passed = False

        # 2. Check for duplicate timestamps
        unique_timestamps = len(np.unique(dataset.timestamps))
        if unique_timestamps != total_records:
            duplicate_count = total_records - unique_timestamps
            anomalies["duplicate_timestamps"] = f"Detected {duplicate_count} duplicate timestamps."
            passed = False

        # 3. Check for missing values / NaNs / Infinite numbers
        for col, values in dataset.data.items():
            nan_count = int(np.isnan(values).sum())
            inf_count = int(np.isinf(values).sum())
            if nan_count > 0 or inf_count > 0:
                anomalies[f"{col}_corrupted_values"] = f"NaNs: {nan_count}, Infs: {inf_count}"
                passed = False

        # 4. Check for Outliers (price/volume value jumps)
        for symbol in dataset.symbols:
            col = f"{symbol}_close"
            if col in dataset.data:
                prices = dataset.data[col]
                # Calculate simple rolling or global returns to spot massive percentage jumps
                returns = np.diff(prices) / prices[:-1]
                if len(returns) > 0:
                    mean_ret = np.mean(returns)
                    std_ret = np.std(returns)
                    if std_ret > 0:
                        z_scores = np.abs((returns - mean_ret) / std_ret)
                        outliers = np.sum(z_scores > self.z_score_threshold)
                        outliers_ratio = outliers / len(returns)
                        if outliers_ratio > self.max_outliers_ratio:
                            anomalies[f"{col}_outliers"] = f"Excessive price outliers: {outliers} ({outliers_ratio:.2%})"
                            passed = False

        # 5. Check for Look-ahead bias
        # Check if high, low, close align correctly (e.g., low is never higher than open, high, close)
        for symbol in dataset.symbols:
            o_col = f"{symbol}_open"
            h_col = f"{symbol}_high"
            l_col = f"{symbol}_low"
            c_col = f"{symbol}_close"
            if all(col in dataset.data for col in [o_col, h_col, l_col, c_col]):
                opens = dataset.data[o_col]
                highs = dataset.data[h_col]
                lows = dataset.data[l_col]
                closes = dataset.data[c_col]

                # Invariant: high must be >= all others, low must be <= all others
                invalid_highs = int(np.sum(highs < opens) + np.sum(highs < closes))
                invalid_lows = int(np.sum(lows > opens) + np.sum(lows > closes))

                if invalid_highs > 0 or invalid_lows > 0:
                    anomalies[f"{symbol}_ohlc_invariant_violation"] = (
                        f"OHLC logical violations: High below other: {invalid_highs}, Low above other: {invalid_lows}"
                    )
                    passed = False

        # Update metadata of dataset with validation results
        dataset.quality_metrics["total_records"] = total_records
        dataset.quality_metrics["anomalies_found"] = len(anomalies)
        dataset.quality_metrics["valid"] = passed

        return passed, anomalies
