"""
Production Monitoring and Drift Detection Subsystem for Research OS.
Measures concept drift, feature distribution shifts via KS-Test, and Population Stability Index (PSI).
Automatically triggers alert signals on alpha decay or statistical degradation.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import scipy.stats as stats
import logging

logger = logging.getLogger(__name__)


class ProductionResearchMonitor:
    """
    Monitors live strategy inputs, outputs, and alpha metrics in real time.
    Flags feature or concept drift before live strategy performance decays.
    """

    def calculate_psi(self, baseline: np.ndarray, actual: np.ndarray, num_bins: int = 10) -> float:
        """
        Calculates the Population Stability Index (PSI) between a baseline feature distribution
        and live/actual production inputs.
        PSI threshold rules of thumb:
          - PSI < 0.1: No significant change/stable.
          - 0.1 <= PSI < 0.25: Moderate shift/drift.
          - PSI >= 0.25: Significant shift/severe drift.
        """
        # Clean inputs
        b_clean = baseline[~np.isnan(baseline) & ~np.isinf(baseline)]
        a_clean = actual[~np.isnan(actual) & ~np.isinf(actual)]

        if len(b_clean) < 10 or len(a_clean) < 10:
            return 0.0

        # Define quantiles based on baseline to bin the datasets
        percentiles = np.linspace(0, 100, num_bins + 1)
        bins = np.percentile(b_clean, percentiles)
        # Adjust boundaries slightly to prevent binning edge errors
        bins[0] -= 1e-5
        bins[-1] += 1e-5
        # Ensure unique bins
        bins = np.unique(bins)
        if len(bins) < 2:
            return 0.0

        # Calculate frequencies in bins
        b_counts, _ = np.histogram(b_clean, bins=bins)
        a_counts, _ = np.histogram(a_clean, bins=bins)

        # Convert to percentages
        b_pct = b_counts / len(b_clean)
        a_pct = a_counts / len(a_clean)

        # Avoid division by zero by smoothing
        b_pct = np.where(b_pct == 0, 0.0001, b_pct)
        a_pct = np.where(a_pct == 0, 0.0001, a_pct)

        # Recalculate normalized percentages
        b_pct /= np.sum(b_pct)
        a_pct /= np.sum(a_pct)

        # Compute PSI
        psi_value = np.sum((a_pct - b_pct) * np.log(a_pct / b_pct))
        return float(psi_value)

    def detect_kolmogorov_smirnov_drift(self, baseline: np.ndarray, actual: np.ndarray) -> Tuple[float, float, bool]:
        """
        Runs a two-sample Kolmogorov-Smirnov test to detect distribution changes.
        Returns:
          - ks_statistic
          - p_value
          - drift_detected (boolean, true if p-value < 0.05)
        """
        b_clean = baseline[~np.isnan(baseline) & ~np.isinf(baseline)]
        a_clean = actual[~np.isnan(actual) & ~np.isinf(actual)]

        if len(b_clean) < 5 or len(a_clean) < 5:
            return 0.0, 1.0, False

        res = stats.ks_2samp(b_clean, a_clean)
        p_val = float(res.pvalue)
        stat = float(res.statistic)

        # If p-value is extremely small (< 0.05), we reject the null hypothesis that
        # both samples originate from the same distribution (drift detected).
        drift_detected = p_val < 0.05
        return stat, p_val, drift_detected

    def check_alpha_decay(self, live_ic: float, baseline_ic: float, tolerance_pct: float = 0.5) -> bool:
        """
        Triggers on severe alpha decay. Returns true if live IC drops below tolerance_pct of baseline IC.
        """
        if abs(baseline_ic) == 0:
            return False
        # If live IC has degraded past our threshold percentage of baseline performance
        return live_ic < (baseline_ic * (1.0 - tolerance_pct))
