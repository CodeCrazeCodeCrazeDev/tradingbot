"""
Modular Machine Learning Models for London Session Intelligence:
1. Baseline Model (Naive persistence and deterministic rule).
2. Market Regime Model (LightGBM classifier: volatility & session expansion).
3. Liquidity & Market Structure Model (LightGBM sweep/breakout classifier).
4. Probabilistic Forecasting Model (Gaussian conditional distribution and direction probabilities).
5. Meta-Labeling Model (LightGBM net profitability classifier after transaction cost drag).

Designed for CPU-efficiency and strict memory boundaries (<= 8GB RAM).
"""

import logging
import pickle
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score, log_loss
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
import lightgbm as lgb

logger = logging.getLogger("AlphaAlgo.LondonMLModels")


class BaselineModel:
    """
    Deterministic rule and naive persistence baseline.
    Used as benchmark to prove that ML models provide genuine incremental predictive power.
    """

    def __init__(self, mode: str = "majority_class") -> None:
        self.mode = mode
        self.majority_class: int = 1
        self.prior_prob: float = 0.5

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "BaselineModel":
        if len(y) > 0:
            counts = pd.Series(y).value_counts(normalize=True)
            self.majority_class = int(counts.index[0])
            self.prior_prob = float(counts.iloc[0])
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.full(len(X), self.majority_class)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        prob = np.full((len(X), 2), [1.0 - self.prior_prob, self.prior_prob])
        return prob


class MarketRegimeModel:
    """
    Classifies market regime into Expansion vs Contraction / Choppy.
    Uses LightGBM with conservative tree depth and CPU threading.
    """

    def __init__(self, n_estimators: int = 60, max_depth: int = 4, learning_rate: float = 0.05) -> None:
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.model: Optional[lgb.LGBMClassifier] = None
        self.feature_names: List[str] = []

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "MarketRegimeModel":
        self.feature_names = list(X.columns)
        self.model = lgb.LGBMClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=42,
            n_jobs=2,
            verbosity=-1
        )
        self.model.fit(X, y)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise ValueError("Model not fitted.")
        return self.model.predict(X[self.feature_names])

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise ValueError("Model not fitted.")
        return self.model.predict_proba(X[self.feature_names])


class LiquidityStructureModel:
    """
    Detects whether an Asian high/low sweep or London breakout will expand directionally (+1)
    or fail / mean revert (0).
    """

    def __init__(self, n_estimators: int = 80, max_depth: int = 4, learning_rate: float = 0.04) -> None:
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.model: Optional[lgb.LGBMClassifier] = None
        self.feature_names: List[str] = []

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "LiquidityStructureModel":
        self.feature_names = list(X.columns)
        self.model = lgb.LGBMClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=42,
            n_jobs=2,
            verbosity=-1
        )
        self.model.fit(X, y)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise ValueError("Model not fitted.")
        return self.model.predict(X[self.feature_names])

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise ValueError("Model not fitted.")
        return self.model.predict_proba(X[self.feature_names])


class ProbabilisticForecastingModel:
    """
    Estimates conditional forward return distribution parameters (mean, standard deviation)
    and directional probabilities using calibrated probability estimators.
    """

    def __init__(self, n_estimators: int = 70, max_depth: int = 4) -> None:
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.mean_model: Optional[lgb.LGBMRegressor] = None
        self.vol_model: Optional[lgb.LGBMRegressor] = None
        self.feature_names: List[str] = []

    def fit(self, X: pd.DataFrame, y_returns: pd.Series) -> "ProbabilisticForecastingModel":
        self.feature_names = list(X.columns)
        # 1. Expected return (mean)
        self.mean_model = lgb.LGBMRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=0.04,
            random_state=42,
            n_jobs=2,
            verbosity=-1
        )
        self.mean_model.fit(X, y_returns)

        # 2. Expected volatility (residuals)
        preds = self.mean_model.predict(X)
        residuals = np.abs(y_returns.values - preds)

        self.vol_model = lgb.LGBMRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=0.04,
            random_state=42,
            n_jobs=2,
            verbosity=-1
        )
        self.vol_model.fit(X, residuals)
        return self

    def predict_distribution(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Returns:
        - mu (expected conditional return)
        - sigma (conditional standard deviation)
        - p_up (probability that next return > 0 under Gaussian assumption)
        """
        if self.mean_model is None or self.vol_model is None:
            raise ValueError("Forecasting model not fitted.")

        mu = self.mean_model.predict(X[self.feature_names])
        sigma = np.maximum(self.vol_model.predict(X[self.feature_names]), 1e-6)

        # Probability that return > 0: P(Z > -mu / sigma) = 1 - Phi(-mu / sigma) = Phi(mu / sigma)
        # Using tanh approximation for erf/Phi to remain lightweight and dependency-free
        z = mu / sigma
        p_up = 0.5 * (1.0 + np.tanh(z / np.sqrt(2.0)))
        return mu, sigma, p_up


class MetaLabelingModel:
    """
    Second-stage filter estimating whether a proposed London setup will be net profitable
    after realistic transaction costs, slippage, and spread drag.
    Uses calibrated probability estimates to enable threshold tuning.
    """

    def __init__(self, n_estimators: int = 90, max_depth: int = 4, learning_rate: float = 0.03) -> None:
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.model: Optional[lgb.LGBMClassifier] = None
        self.feature_names: List[str] = []

    def fit(self, X: pd.DataFrame, y_meta: pd.Series) -> "MetaLabelingModel":
        self.feature_names = list(X.columns)
        self.model = lgb.LGBMClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=42,
            n_jobs=2,
            verbosity=-1
        )
        self.model.fit(X, y_meta)
        return self

    def predict(self, X: pd.DataFrame, threshold: float = 0.50) -> np.ndarray:
        proba = self.predict_proba(X)
        return (proba[:, 1] >= threshold).astype(int)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise ValueError("Meta-labeling model not fitted.")
        return self.model.predict_proba(X[self.feature_names])
