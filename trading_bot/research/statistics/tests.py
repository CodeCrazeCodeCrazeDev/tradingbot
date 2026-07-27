"""
Statistical Validation Engine for Research OS.
Wraps statsmodels and scipy into stable implementations of the StatisticalTest interface.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.stattools import grangercausalitytests
from statsmodels.stats.multitest import multipletests

from trading_bot.research.core.interfaces import StatisticalTest

import logging
logger = logging.getLogger(__name__)


class ADFStationarityTest(StatisticalTest):
    """
    Augmented Dickey-Fuller unit root stationarity test.
    Checks if a time series has a unit root (is non-stationary).
    """

    @property
    def test_name(self) -> str:
        return "Augmented_Dickey_Fuller_Stationarity"

    def run_test(self, data: np.ndarray, **kwargs) -> Dict[str, Any]:
        """
        Run ADF test.
        """
        # Clean input: drop infinite or NaN values
        clean_data = data[~np.isnan(data) & ~np.isinf(data)]
        if len(clean_data) < 15:
            return {
                "passed": False,
                "statistic": 0.0,
                "p_value": 1.0,
                "critical_values": {},
                "conclusion": "Insufficient clean data to run ADF test."
            }

        try:
            res = adfuller(clean_data, maxlag=kwargs.get("maxlag", None))
            adf_stat = float(res[0])
            p_val = float(res[1])
            crit_vals = {k: float(v) for k, v in res[4].items()}

            # If ADF statistic is less than the 5% critical value, reject the null hypothesis of non-stationarity
            passed = p_val < 0.05

            return {
                "passed": passed,
                "statistic": adf_stat,
                "p_value": p_val,
                "critical_values": crit_vals,
                "conclusion": "Stationary (reject unit root)" if passed else "Non-Stationary (fail to reject unit root)"
            }
        except Exception as e:
            logger.error(f"Error running ADF test: {e}")
            return {
                "passed": False,
                "statistic": 0.0,
                "p_value": 1.0,
                "critical_values": {},
                "conclusion": f"ADF test failed: {e}"
            }


class LjungBoxAutocorrelationTest(StatisticalTest):
    """
    Ljung-Box test for autocorrelation at multiple lag intervals.
    """

    @property
    def test_name(self) -> str:
        return "Ljung_Box_Autocorrelation"

    def run_test(self, data: np.ndarray, **kwargs) -> Dict[str, Any]:
        clean_data = data[~np.isnan(data) & ~np.isinf(data)]
        lags = kwargs.get("lags", 5)

        if len(clean_data) <= lags + 5:
            return {
                "passed": False,
                "statistic": 0.0,
                "p_value": 1.0,
                "conclusion": "Insufficient data for Ljung-Box test."
            }

        try:
            # We use sm.stats.acorr_ljungbox
            res = sm.stats.acorr_ljungbox(clean_data, lags=[lags], return_df=True)
            stat = float(res.iloc[0, 0])
            p_val = float(res.iloc[0, 1])

            # If p-value < 0.05, we reject the null hypothesis of no autocorrelation (meaning autocorrelation exists)
            has_autocorr = p_val < 0.05

            return {
                "passed": has_autocorr,  # if has_autocorr is true, the series has predictability (autocorr)
                "statistic": stat,
                "p_value": p_val,
                "conclusion": "Significant autocorrelation present (predictable)" if has_autocorr else "No significant autocorrelation (white noise)"
            }
        except Exception as e:
            logger.error(f"Error running Ljung-Box test: {e}")
            return {
                "passed": False,
                "statistic": 0.0,
                "p_value": 1.0,
                "conclusion": f"Ljung-Box test failed: {e}"
            }


class GrangerCausalityTest(StatisticalTest):
    """
    Granger causality test to determine if a candidate feature causes/predicts target price returns.
    """

    @property
    def test_name(self) -> str:
        return "Granger_Causality"

    def run_test(self, data: np.ndarray, **kwargs) -> Dict[str, Any]:
        """
        data: a 2D numpy array of shape (N, 2), where:
              data[:, 0] is the target series,
              data[:, 1] is the causing predictor feature.
        """
        maxlag = kwargs.get("maxlag", 2)
        if len(data) < maxlag * 3 + 10:
            return {
                "passed": False,
                "p_value": 1.0,
                "conclusion": "Insufficient rows to run Granger Causality."
            }

        try:
            # Clean missing data
            mask = ~np.isnan(data).any(axis=1) & ~np.isinf(data).any(axis=1)
            clean_data = data[mask]

            if len(clean_data) < maxlag * 3 + 10:
                return {"passed": False, "p_value": 1.0, "conclusion": "Insufficient clean rows."}

            res = grangercausalitytests(clean_data, maxlag=[maxlag], verbose=False)
            # Fetch F-test p-value
            ssr_ftest = res[maxlag][0]['ssr_ftest']
            p_val = float(ssr_ftest[1])

            passed = p_val < 0.05

            return {
                "passed": passed,
                "p_value": p_val,
                "f_statistic": float(ssr_ftest[0]),
                "conclusion": f"Predictor Granger-causes target (p-val {p_val:.4f})" if passed else "No Granger causation found."
            }
        except Exception as e:
            logger.error(f"Error running Granger test: {e}")
            return {
                "passed": False,
                "p_value": 1.0,
                "conclusion": f"Granger test failed: {e}"
            }


class FDRCorrection:
    """
    False Discovery Rate (FDR) Benjamini-Hochberg multi-test correction.
    Combats look-ahead selection bias and p-hacking in feature/alpha discovery.
    """

    @staticmethod
    def adjust_p_values(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
        """
        Returns:
          - List of booleans indicating whether each hypothesis is accepted (statistically significant after correction)
          - Adjusted p-values
        """
        if len(p_values) == 0:
            return [], []

        p_arr = np.array(p_values)
        rejected, adjusted_p, _, _ = multipletests(p_arr, alpha=alpha, method='fdr_bh')

        return list(rejected), list(adjusted_p)
