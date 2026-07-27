"""
Alpha Discovery and Candidate Signal Generators for Research OS.
Computes predictive alpha metrics: Information Coefficient (IC), turnover, capacity, stability, and decay.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
import scipy.stats as stats
import logging
from trading_bot.research.core.interfaces import AlphaGenerator, AlphaSignal, StandardizedDataset, EngineeredFeature

logger = logging.getLogger(__name__)


class QuantitativeAlphaGenerator(AlphaGenerator):
    """
    Candidate alpha signal generator that executes mathematical combinations (symbolic-regression-like)
    and scores predictive performance.
    """

    def generate_alpha(self, dataset: StandardizedDataset, features: List[EngineeredFeature]) -> List[AlphaSignal]:
        if len(features) < 2:
            logger.warning("Fewer than 2 features supplied. Cannot generate composite symbolic alphas.")
            return []

        alphas = []
        symbol = dataset.symbols[0]
        close_col = f"{symbol}_close"
        if close_col not in dataset.data:
            return []

        prices = dataset.data[close_col]

        # Calculate forward 5-period price returns for IC validation
        fwd_periods = 5
        fwd_returns = np.zeros_like(prices)
        fwd_returns[:-fwd_periods] = (prices[fwd_periods:] - prices[:-fwd_periods]) / prices[:-fwd_periods]

        # Candidate 1: Interaction of Volatility and Entropy
        f_vol = next((f for f in features if "volatility" in f.name), features[0])
        f_ent = next((f for f in features if "entropy" in f.name), features[1])

        # Symbolic product: Volatility * Entropy (normalized via Z-score)
        v_norm = self._z_score(f_vol.values)
        e_norm = self._z_score(f_ent.values)
        interaction_signal = v_norm * e_norm

        metrics = self.calculate_alpha_metrics(interaction_signal, prices, fwd_returns, fwd_periods)

        alphas.append(AlphaSignal(
            alpha_id=f"alpha_{symbol.lower()}_vol_entropy_interaction",
            hypothesis_id="hyp_vpin_vol_regime",  # will be linked dynamically
            values=interaction_signal,
            timestamps=dataset.timestamps,
            metrics=metrics,
            lineage_feature_ids=[f_vol.feature_id, f_ent.feature_id],
            metadata={"type": "interaction_symbolic", "combination": "Z(Volatility) * Z(Entropy)"}
        ))

        # Candidate 2: Realized Variance divided by Fractal Dimension
        f_rv = next((f for f in features if "realized_variance" in f.name), features[0])
        f_frac = next((f for f in features if "fractal_dim" in f.name), features[1])

        # Prevent division by zero
        frac_adjusted = np.where(f_frac.values == 0, 1.0, f_frac.values)
        rv_frac_ratio = self._z_score(f_rv.values / frac_adjusted)

        metrics_rv = self.calculate_alpha_metrics(rv_frac_ratio, prices, fwd_returns, fwd_periods)

        alphas.append(AlphaSignal(
            alpha_id=f"alpha_{symbol.lower()}_rv_fractal_ratio",
            hypothesis_id="hyp_fractal_variance",
            values=rv_frac_ratio,
            timestamps=dataset.timestamps,
            metrics=metrics_rv,
            lineage_feature_ids=[f_rv.feature_id, f_frac.feature_id],
            metadata={"type": "ratio_symbolic", "combination": "Z(RealizedVariance / FractalDimension)"}
        ))

        return alphas

    def _z_score(self, x: np.ndarray) -> np.ndarray:
        mean = np.mean(x)
        std = np.std(x)
        if std == 0:
            return np.zeros_like(x)
        return (x - mean) / std

    def calculate_alpha_metrics(self, signal: np.ndarray, prices: np.ndarray, fwd_returns: np.ndarray, fwd_periods: int) -> Dict[str, Any]:
        """
        Rigorously calculates performance indicators: IC, stability, turnover, capacity, and decay.
        """
        # Ensure we drop any trailing zeros or warm-up periods
        valid_mask = (signal != 0) & (~np.isnan(signal)) & (~np.isnan(fwd_returns))

        if np.sum(valid_mask) < 20:
            return {"ic": 0.0, "p_value": 1.0, "turnover": 1.0, "stability": 0.0, "capacity_usd": 0.0, "decay_rate": 1.0}

        # 1. Information Coefficient (IC) - Spearman rank correlation
        ic, p_val = stats.spearmanr(signal[valid_mask], fwd_returns[valid_mask])
        ic = float(ic) if not np.isnan(ic) else 0.0
        p_val = float(p_val) if not np.isnan(p_val) else 1.0

        # 2. Signal Turnover: absolute changes divided by average exposure
        signal_diff = np.diff(signal)
        sum_abs_diff = np.sum(np.abs(signal_diff))
        sum_abs_sig = np.sum(np.abs(signal))
        turnover = float(sum_abs_diff / sum_abs_sig) if sum_abs_sig > 0 else 1.0

        # 3. Stability: sub-window IC consistency (variance of rolling 50-period IC)
        ic_slices = []
        step = 50
        for i in range(0, len(signal) - step, step):
            slice_mask = valid_mask[i:i+step]
            if np.sum(slice_mask) > 15:
                sub_ic, _ = stats.spearmanr(signal[i:i+step][slice_mask], fwd_returns[i:i+step][slice_mask])
                if not np.isnan(sub_ic):
                    ic_slices.append(sub_ic)
        stability = float(np.mean(ic_slices) / np.std(ic_slices)) if len(ic_slices) > 1 and np.std(ic_slices) > 0 else 0.0

        # 4. Capacity Scaling (USD) - proxy calculation based on market properties
        # Real-world square-root model: Capacity scales inversely with signal turnover and daily volatility
        avg_daily_vol = float(np.std(np.diff(prices) / prices[:-1]))
        capacity = float(10000000.0 * (ic ** 2) / max(0.0001, turnover * avg_daily_vol))

        # 5. Decay Analysis (IC decay at longer horizons)
        # Check IC at 2x forward period
        fwd_periods_long = fwd_periods * 2
        fwd_returns_long = np.zeros_like(prices)
        fwd_returns_long[:-fwd_periods_long] = (prices[fwd_periods_long:] - prices[:-fwd_periods_long]) / prices[:-fwd_periods_long]

        long_mask = (signal != 0) & (~np.isnan(signal)) & (~np.isnan(fwd_returns_long))
        ic_long, _ = stats.spearmanr(signal[long_mask], fwd_returns_long[long_mask])
        ic_long = float(ic_long) if not np.isnan(ic_long) else 0.0

        # Decay is the percentage reduction of IC per timestep lag
        decay_rate = float((ic - ic_long) / max(0.01, abs(ic))) if ic != 0 else 1.0

        return {
            "ic": ic,
            "p_value": p_val,
            "turnover": turnover,
            "stability": stability,
            "capacity_usd": capacity,
            "decay_rate": decay_rate
        }
