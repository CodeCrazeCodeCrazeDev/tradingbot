"""
Advanced Market Regime Detection System
Uses ML techniques to identify market regimes and adapt trading strategies
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
import logging
import asyncio
from dataclasses import dataclass
import joblib
import os
from pathlib import Path
import json
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.ensemble import IsolationForest
from hmmlearn import hmm
from scipy.stats import norm, t, chi2
import warnings
import numpy
import pandas

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



# Suppress specific sklearn warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

logger = logging.getLogger(__name__)

@dataclass
class MarketRegime:
    """Market regime classification"""
    regime_id: int
    name: str
    volatility: float
    trend: float
    liquidity: float
    correlation: float
    start_time: datetime
    confidence: float
    features: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'regime_id': self.regime_id,
            'name': self.name,
            'volatility': self.volatility,
            'trend': self.trend,
            'liquidity': self.liquidity,
            'correlation': self.correlation,
            'start_time': self.start_time.isoformat(),
            'confidence': self.confidence,
            'features': self.features
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketRegime':
        """Create from dictionary"""
        return cls(
            regime_id=data['regime_id'],
            name=data['name'],
            volatility=data['volatility'],
            trend=data['trend'],
            liquidity=data['liquidity'],
            correlation=data['correlation'],
            start_time=datetime.fromisoformat(data['start_time']),
            confidence=data['confidence'],
            features=data['features']
        )


class MarketRegimeDetector:
    """
    Advanced market regime detection using multiple ML techniques
    
    Features:
    - Hidden Markov Models for regime transitions
    - Gaussian Mixture Models for distribution analysis
    - Clustering for regime identification
    - Anomaly detection for regime breaks
    - Adaptive parameter tuning
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Model parameters
        self.n_regimes = self.config.get('n_regimes', 5)
        self.lookback_window = self.config.get('lookback_window', 100)
        self.min_samples = self.config.get('min_samples', 30)
        self.feature_importance = self.config.get('feature_importance', {})
        
        # Initialize models
        self.hmm_model = None
        self.gmm_model = None
        self.kmeans_model = None
        self.anomaly_detector = None
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=3)
        
        # Regime tracking
        self.current_regime = None
        self.regime_history = []
        self.regime_transitions = []
        
        # Feature tracking
        self.feature_history = []
        
        # Model storage
        self.models_dir = Path(self.config.get('models_dir', 'models/market_regimes'))
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Regime names mapping
        self.regime_names = {
            0: "Trending Bull",
            1: "Trending Bear",
            2: "Range-Bound Low Vol",
            3: "Volatile Sideways",
            4: "Crisis/Panic"
        }
        
        logger.info("Market regime detector initialized")
    
    async def detect_regime(self, market_data: Dict[str, pd.DataFrame]) -> MarketRegime:
        """
        Detect current market regime from market data
        
        Args:
            market_data: Dictionary of market data frames by symbol
            
        Returns:
            Current market regime
        """
        # Extract features
        features = await self._extract_features(market_data)
        
        # Store features
        self.feature_history.append(features)
        if len(self.feature_history) > self.lookback_window:
            self.feature_history = self.feature_history[-self.lookback_window:]
        
        # Check if we have enough data
        if len(self.feature_history) < self.min_samples:
            logger.warning(f"Not enough data for regime detection: {len(self.feature_history)}/{self.min_samples}")
            return self._default_regime(features)
        
        # Prepare feature matrix
        feature_matrix = self._prepare_feature_matrix()
        
        # Detect regime
        regime_id, confidence = self._detect_regime_with_ensemble(feature_matrix)
        
        # Check for regime change
        is_new_regime = (self.current_regime is None or 
                         regime_id != self.current_regime.regime_id)
        
        # Create regime object
        regime = MarketRegime(
            regime_id=regime_id,
            name=self.regime_names.get(regime_id, f"Regime {regime_id}"),
            volatility=features.get('volatility', 0),
            trend=features.get('trend', 0),
            liquidity=features.get('liquidity', 0),
            correlation=features.get('correlation', 0),
            start_time=datetime.now(),
            confidence=confidence,
            features=features
        )
        
        # Update tracking
        if is_new_regime and self.current_regime is not None:
            self.regime_transitions.append({
                'from': self.current_regime.regime_id,
                'to': regime_id,
                'time': datetime.now(),
                'confidence': confidence
            })
            logger.info(f"Regime change detected: {self.current_regime.name} -> {regime.name}")
        
        self.current_regime = regime
        self.regime_history.append(regime)
        
        return regime
    
    async def _extract_features(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """Extract regime-relevant features from market data"""
        features = {}
        
        # Get primary symbol data (use first symbol if multiple)
        symbol = next(iter(market_data.keys()))
        df = market_data[symbol]
        
        if df.empty:
            return features
        
        # Basic features
        if 'close' in df.columns:
            # Volatility features
            returns = df['close'].pct_change().dropna()
            features['volatility'] = returns.std() * np.sqrt(252)  # Annualized
            features['realized_vol_10d'] = returns.rolling(10).std().iloc[-1] * np.sqrt(252) if len(returns) >= 10 else 0
            features['realized_vol_30d'] = returns.rolling(30).std().iloc[-1] * np.sqrt(252) if len(returns) >= 30 else 0
            
            # Trend features
            features['trend_5d'] = self._calculate_trend_strength(df['close'], 5)
            features['trend_20d'] = self._calculate_trend_strength(df['close'], 20)
            features['trend'] = features['trend_20d']  # Overall trend
            
            # Momentum features
            features['momentum_10d'] = returns.rolling(10).mean().iloc[-1] * 100 if len(returns) >= 10 else 0
            features['momentum_30d'] = returns.rolling(30).mean().iloc[-1] * 100 if len(returns) >= 30 else 0
            
            # Mean reversion features
            features['mean_reversion'] = self._calculate_mean_reversion(df['close'])
            
            # Distribution features
            features['skew'] = returns.skew() if len(returns) >= 30 else 0
            features['kurtosis'] = returns.kurtosis() if len(returns) >= 30 else 0
            features['tail_ratio'] = self._calculate_tail_ratio(returns)
        
        # Volume features
        if 'volume' in df.columns:
            features['volume_trend'] = self._calculate_trend_strength(df['volume'], 10)
            features['liquidity'] = df['volume'].mean() / df['volume'].rolling(30).mean().iloc[-1] if len(df) >= 30 else 1
        else:
            features['liquidity'] = 1.0
        
        # Correlation features (if multiple symbols)
        if len(market_data) > 1:
            features['correlation'] = await self._calculate_correlation(market_data)
        else:
            features['correlation'] = 0.5  # Neutral
        
        return features
    
    def _calculate_trend_strength(self, series: pd.Series, window: int) -> float:
        """Calculate trend strength using linear regression R²"""
        if len(series) < window:
            return 0
        
        y = series.iloc[-window:].values
        x = np.arange(len(y))
        
        # Simple linear regression
        slope, intercept = np.polyfit(x, y, 1)
        y_pred = slope * x + intercept
        
        # R² calculation
        ss_total = np.sum((y - np.mean(y)) ** 2)
        ss_residual = np.sum((y - y_pred) ** 2)
        
        r_squared = 1 - (ss_residual / ss_total) if ss_total > 0 else 0
        
        # Sign by slope direction
        return r_squared * (1 if slope > 0 else -1)
    
    def _calculate_mean_reversion(self, series: pd.Series, window: int = 20) -> float:
        """Calculate mean reversion tendency"""
        if len(series) < window:
            return 0
        
        # Calculate distance from moving average
        ma = series.rolling(window).mean()
        distance = (series - ma) / ma
        
        # Calculate mean reversion coefficient (autocorrelation of returns)
        returns = series.pct_change().dropna()
        if len(returns) < 2:
            return 0
        
        # Negative autocorrelation indicates mean reversion
        autocorr = returns.autocorr(1)
        
        return -autocorr  # Positive value = stronger mean reversion
    
    def _calculate_tail_ratio(self, returns: pd.Series) -> float:
        """Calculate ratio of upside to downside tail risk"""
        if len(returns) < 30:
            return 1.0
        
        # Calculate 95% VaR for both tails
        upside_var = np.percentile(returns, 95)
        downside_var = np.percentile(returns, 5)
        
        # Avoid division by zero
        if downside_var == 0:
            return 1.0
        
        # Higher ratio means upside volatility dominates
        return abs(upside_var / downside_var) if downside_var != 0 else 1.0
    
    async def _calculate_correlation(self, market_data: Dict[str, pd.DataFrame]) -> float:
        """Calculate average correlation between symbols"""
        symbols = list(market_data.keys())
        if len(symbols) < 2:
            return 0.5
        
        # Extract close prices
        closes = {}
        for symbol, df in market_data.items():
            if 'close' in df.columns:
                closes[symbol] = df['close']
        
        if len(closes) < 2:
            return 0.5
        
        # Calculate returns
        returns = pd.DataFrame({symbol: series.pct_change().dropna() 
                               for symbol, series in closes.items()})
        
        # Calculate correlation matrix
        corr_matrix = returns.corr()
        
        # Average correlation (excluding self-correlations)
        n = len(corr_matrix)
        total_corr = corr_matrix.sum().sum() - n  # Subtract diagonal
        avg_corr = total_corr / (n * (n - 1))  # n(n-1) pairs
        
        return avg_corr
    
    def _prepare_feature_matrix(self) -> np.ndarray:
        """Prepare feature matrix from history"""
        # Convert feature history to DataFrame
        feature_df = pd.DataFrame(self.feature_history)
        
        # Select relevant features
        relevant_features = [
            'volatility', 'trend', 'liquidity', 'correlation',
            'realized_vol_10d', 'realized_vol_30d',
            'trend_5d', 'trend_20d',
            'momentum_10d', 'momentum_30d',
            'mean_reversion', 'skew', 'kurtosis', 'tail_ratio'
        ]
        
        # Filter features that exist
        features = [f for f in relevant_features if f in feature_df.columns]
        
        if not features:
            return np.array([])
        
        # Extract feature matrix
        X = feature_df[features].values
        
        # Scale features
        X = self.scaler.fit_transform(X)
        
        return X
    
    def _detect_regime_with_ensemble(self, feature_matrix: np.ndarray) -> Tuple[int, float]:
        """Detect regime using ensemble of models"""
        if feature_matrix.size == 0:
            return 0, 0.0
        
        # Ensure models are initialized
        self._ensure_models_initialized(feature_matrix)
        
        # Get latest feature vector
        latest_features = feature_matrix[-1].reshape(1, -1)
        
        # Get predictions from each model
        hmm_regime = self.hmm_model.predict(latest_features)[0]
        gmm_probs = self.gmm_model.predict_proba(latest_features)[0]
        gmm_regime = np.argmax(gmm_probs)
        kmeans_regime = self.kmeans_model.predict(latest_features)[0]
        
        # Check for anomalies (potential regime breaks)
        is_anomaly = self.anomaly_detector.predict(latest_features)[0] == -1
        anomaly_score = -self.anomaly_detector.score_samples(latest_features)[0]
        
        # Ensemble voting with weights
        votes = {
            hmm_regime: 0.4,
            gmm_regime: 0.3,
            kmeans_regime: 0.3
        }
        
        # Aggregate votes
        regime_votes = {}
        for regime, weight in votes.items():
            if regime not in regime_votes:
                regime_votes[regime] = 0
            regime_votes[regime] += weight
        
        # Get regime with highest vote
        regime_id = max(regime_votes.items(), key=lambda x: x[1])[0]
        
        # Calculate confidence
        if regime_id == gmm_regime:
            confidence = gmm_probs[regime_id]
        else:
            confidence = max(0.5, 1.0 - anomaly_score / 10)  # Scale anomaly score
        
        # If anomaly detected, might be a regime break
        if is_anomaly and anomaly_score > 2.0:
            logger.warning(f"Potential regime break detected: anomaly score {anomaly_score:.2f}")
            # Could trigger model retraining here
        
        return regime_id, confidence
    
    def _ensure_models_initialized(self, feature_matrix: np.ndarray):
        """Ensure all models are initialized"""
        if feature_matrix.size == 0:
            return
        
        # Try to load models first
        if self._try_load_models():
            return
        
        # Initialize models if loading failed
        logger.info("Initializing regime detection models")
        
        # Hidden Markov Model
        self.hmm_model = hmm.GaussianHMM(
            n_components=self.n_regimes,
            covariance_type="full",
            n_iter=100,
            random_state=42
        )
        self.hmm_model.fit(feature_matrix)
        
        # Gaussian Mixture Model
        self.gmm_model = GaussianMixture(
            n_components=self.n_regimes,
            covariance_type="full",
            random_state=42
        )
        self.gmm_model.fit(feature_matrix)
        
        # K-Means Clustering
        self.kmeans_model = KMeans(
            n_clusters=self.n_regimes,
            random_state=42
        )
        self.kmeans_model.fit(feature_matrix)
        
        # Anomaly detector
        self.anomaly_detector = IsolationForest(
            contamination=0.05,
            random_state=42
        )
        self.anomaly_detector.fit(feature_matrix)
        
        # Save models
        self._save_models()
    
    def _try_load_models(self) -> bool:
        """Try to load models from disk"""
        try:
            hmm_path = self.models_dir / "hmm_model.pkl"
            gmm_path = self.models_dir / "gmm_model.pkl"
            kmeans_path = self.models_dir / "kmeans_model.pkl"
            anomaly_path = self.models_dir / "anomaly_detector.pkl"
            scaler_path = self.models_dir / "scaler.pkl"
            
            if all(p.exists() for p in [hmm_path, gmm_path, kmeans_path, anomaly_path, scaler_path]):
                self.hmm_model = joblib.load(hmm_path)
                self.gmm_model = joblib.load(gmm_path)
                self.kmeans_model = joblib.load(kmeans_path)
                self.anomaly_detector = joblib.load(anomaly_path)
                self.scaler = joblib.load(scaler_path)
                logger.info("Loaded regime detection models from disk")
                return True
        except Exception as e:
            logger.error(f"Error loading models: {e}")
        
        return False
    
    def _save_models(self):
        """Save models to disk"""
        try:
            joblib.dump(self.hmm_model, self.models_dir / "hmm_model.pkl")
            joblib.dump(self.gmm_model, self.models_dir / "gmm_model.pkl")
            joblib.dump(self.kmeans_model, self.models_dir / "kmeans_model.pkl")
            joblib.dump(self.anomaly_detector, self.models_dir / "anomaly_detector.pkl")
            joblib.dump(self.scaler, self.models_dir / "scaler.pkl")
            logger.info("Saved regime detection models to disk")
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def _default_regime(self, features: Dict[str, float]) -> MarketRegime:
        """Return default regime when not enough data"""
        # Determine basic regime type from limited features
        volatility = features.get('volatility', 0.2)
        trend = features.get('trend', 0)
        
        if volatility > 0.3:
            if trend > 0.3:
                regime_id = 0  # Trending Bull
            elif trend < -0.3:
                regime_id = 1  # Trending Bear
            else:
                regime_id = 3  # Volatile Sideways
        else:
            if abs(trend) < 0.2:
                regime_id = 2  # Range-Bound Low Vol
            elif trend > 0:
                regime_id = 0  # Trending Bull
            else:
                regime_id = 1  # Trending Bear
        
        return MarketRegime(
            regime_id=regime_id,
            name=self.regime_names.get(regime_id, f"Regime {regime_id}"),
            volatility=volatility,
            trend=trend,
            liquidity=features.get('liquidity', 1.0),
            correlation=features.get('correlation', 0.5),
            start_time=datetime.now(),
            confidence=0.6,  # Lower confidence for default regime
            features=features
        )
    
    def get_regime_history(self) -> List[Dict[str, Any]]:
        """Get regime history as list of dictionaries"""
        return [regime.to_dict() for regime in self.regime_history]
    
    def get_regime_transitions(self) -> List[Dict[str, Any]]:
        """Get regime transitions"""
        return self.regime_transitions
    
    def plot_regime_history(self, save_path: Optional[str] = None):
        """Plot regime history"""
        if not self.regime_history:
            logger.warning("No regime history to plot")
            return
        
        # Extract data
        dates = [r.start_time for r in self.regime_history]
        regimes = [r.regime_id for r in self.regime_history]
        confidences = [r.confidence for r in self.regime_history]
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # Plot regimes
        ax1.scatter(dates, regimes, c=regimes, cmap='viridis', s=50, alpha=0.7)
        ax1.set_yticks(range(self.n_regimes))
        ax1.set_yticklabels([self.regime_names.get(i, f"Regime {i}") for i in range(self.n_regimes)])
        ax1.set_ylabel("Market Regime")
        ax1.set_title("Market Regime History")
        ax1.grid(True)
        
        # Plot confidence
        ax2.plot(dates, confidences, 'r-', alpha=0.7)
        ax2.set_ylabel("Confidence")
        ax2.set_xlabel("Date")
        ax2.grid(True)
        ax2.set_ylim(0, 1)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Saved regime history plot to {save_path}")
        else:
            plt.show()
        
        plt.close(fig)
    
    def plot_feature_importance(self, save_path: Optional[str] = None):
        """Plot feature importance for regime detection"""
        if not self.feature_history:
            logger.warning("No feature history to plot")
            return
        
        # Convert to DataFrame
        feature_df = pd.DataFrame(self.feature_history)
        
        # Calculate correlation with regime
        if self.regime_history and len(self.regime_history) == len(feature_df):
            regimes = [r.regime_id for r in self.regime_history]
            feature_df['regime'] = regimes
            
            # Calculate correlation
            correlations = {}
            for col in feature_df.columns:
                if col != 'regime':
                    correlations[col] = feature_df[col].corr(feature_df['regime'])
            
            # Plot
            plt.figure(figsize=(10, 6))
            sns.barplot(x=list(correlations.keys()), y=list(correlations.values()))
            plt.xticks(rotation=45, ha='right')
            plt.title("Feature Importance for Regime Detection")
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path)
                logger.info(f"Saved feature importance plot to {save_path}")
            else:
                plt.show()
            
            plt.close()
