"""
Feature Engineering Engine for Research OS.
Auto-engineers quantitative features (volatility, entropy, realized variance, fractal dimension) and scores them.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.feature_selection import mutual_info_regression
from trading_bot.research.core.interfaces import EngineeredFeature, StandardizedDataset, FeatureScorer

import logging
logger = logging.getLogger(__name__)


class FeatureDiscoveryEngine(FeatureScorer):
    """
    Automated feature mining and scoring engine.
    Calculates advanced microstructural, statistical, and mathematical features.
    """

    def generate_features(self, dataset: StandardizedDataset, symbol: str) -> List[EngineeredFeature]:
        features = []
        close_col = f"{symbol}_close"
        volume_col = f"{symbol}_volume"

        if close_col not in dataset.data:
            logger.warning(f"Close column '{close_col}' not found. Cannot generate features.")
            return []

        prices = dataset.data[close_col]
        volumes = dataset.data.get(volume_col, np.ones_like(prices))
        timestamps = dataset.timestamps

        # 1. Volatility (rolling standard deviation of returns)
        vol_values = self._calculate_rolling_volatility(prices, window=10)
        features.append(EngineeredFeature(
            feature_id=f"feat_{symbol.lower()}_volatility_10",
            name="rolling_volatility_10",
            values=vol_values,
            timestamps=timestamps,
            dependencies=[close_col],
            pipeline_code="np.std(returns) of window=10",
            metadata={"window": 10, "type": "statistical"}
        ))

        # 2. Entropy (Shannon entropy of price changes)
        entropy_values = self._calculate_rolling_entropy(prices, window=15)
        features.append(EngineeredFeature(
            feature_id=f"feat_{symbol.lower()}_entropy_15",
            name="rolling_shannon_entropy_15",
            values=entropy_values,
            timestamps=timestamps,
            dependencies=[close_col],
            pipeline_code="shannon_entropy of price returns of window=15",
            metadata={"window": 15, "type": "information_theory"}
        ))

        # 3. Realized Variance (rolling sum of squared returns)
        rv_values = self._calculate_realized_variance(prices, window=10)
        features.append(EngineeredFeature(
            feature_id=f"feat_{symbol.lower()}_realized_variance_10",
            name="realized_variance_10",
            values=rv_values,
            timestamps=timestamps,
            dependencies=[close_col],
            pipeline_code="sum(returns**2) of window=10",
            metadata={"window": 10, "type": "variance"}
        ))

        # 4. Fractal Dimension (approximate Hurst or box-counting fractal dimension)
        fractal_values = self._calculate_fractal_dimension(prices, window=20)
        features.append(EngineeredFeature(
            feature_id=f"feat_{symbol.lower()}_fractal_dim_20",
            name="fractal_dimension_20",
            values=fractal_values,
            timestamps=timestamps,
            dependencies=[close_col],
            pipeline_code="fractal_dimension using box-counting approximation on window=20",
            metadata={"window": 20, "type": "mathematical"}
        ))

        return features

    def _calculate_rolling_volatility(self, prices: np.ndarray, window: int) -> np.ndarray:
        returns = np.zeros_like(prices)
        returns[1:] = np.diff(prices) / prices[:-1]

        vol = np.zeros_like(prices)
        for i in range(window, len(prices)):
            vol[i] = np.std(returns[i-window:i])
        return vol

    def _calculate_rolling_entropy(self, prices: np.ndarray, window: int) -> np.ndarray:
        returns = np.zeros_like(prices)
        returns[1:] = np.diff(prices) / prices[:-1]

        entropy = np.zeros_like(prices)
        for i in range(window, len(prices)):
            window_ret = returns[i-window:i]
            # Discretize into 5 bins
            hist, _ = np.histogram(window_ret, bins=5)
            probs = hist / max(1, np.sum(hist))
            probs = probs[probs > 0]
            entropy[i] = -np.sum(probs * np.log2(probs)) if len(probs) > 0 else 0.0
        return entropy

    def _calculate_realized_variance(self, prices: np.ndarray, window: int) -> np.ndarray:
        returns = np.zeros_like(prices)
        returns[1:] = np.diff(prices) / prices[:-1]

        rv = np.zeros_like(prices)
        for i in range(window, len(prices)):
            rv[i] = np.sum(returns[i-window:i] ** 2)
        return rv

    def _calculate_fractal_dimension(self, prices: np.ndarray, window: int) -> np.ndarray:
        # Approximate using standard variation of high/low spread over the window
        # For simplicity, we approximate using box-counting log range ratio
        fractal = np.zeros_like(prices)
        for i in range(window, len(prices)):
            window_prices = prices[i-window:i]
            r = np.max(window_prices) - np.min(window_prices)
            if r > 0:
                # Approximate log(range)/log(window) as fractal index
                fractal[i] = float(np.log(r) / np.log(window))
            else:
                fractal[i] = 1.0
        return np.clip(fractal, 1.0, 2.0)

    # Implement FeatureScorer interface
    def score_features(self, features: List[EngineeredFeature], target: np.ndarray) -> Dict[str, float]:
        """
        Calculates relative mutual information (MI) scores between generated features and a target array.
        """
        scores = {}
        if len(features) == 0:
            return scores

        for feature in features:
            # Drop NaNs or zeros at the beginning due to rolling window warmups
            valid_mask = (feature.values != 0) & (~np.isnan(feature.values)) & (~np.isnan(target))
            if np.sum(valid_mask) > 10:
                X = feature.values[valid_mask].reshape(-1, 1)
                y = target[valid_mask]
                try:
                    mi = mutual_info_regression(X, y)[0]
                    scores[feature.feature_id] = float(mi)
                except Exception as e:
                    logger.error(f"Error calculating MI for feature '{feature.feature_id}': {e}")
                    scores[feature.feature_id] = 0.0
            else:
                scores[feature.feature_id] = 0.0

        return scores

    def prune_redundant_features(self, features: List[EngineeredFeature], threshold: float = 0.85) -> List[EngineeredFeature]:
        """
        Computes pairwise Pearson correlation across all features and drops redundant candidates.
        """
        if len(features) <= 1:
            return features

        pruned_features = []
        dropped_ids = set()

        for i, f1 in enumerate(features):
            if f1.feature_id in dropped_ids:
                continue
            pruned_features.append(f1)

            for j in range(i + 1, len(features)):
                f2 = features[j]
                if f2.feature_id in dropped_ids:
                    continue

                # Pairwise correlation
                mask = (f1.values != 0) & (f2.values != 0)
                if np.sum(mask) > 10:
                    corr = np.corrcoef(f1.values[mask], f2.values[mask])[0, 1]
                    if abs(corr) >= threshold:
                        dropped_ids.add(f2.feature_id)
                        logger.info(f"Feature '{f2.feature_id}' pruned due to correlation {corr:.2f} with '{f1.feature_id}'.")

        return pruned_features
