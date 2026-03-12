"""
Layer 1: Market State Detection Engine (Foundation Layer)

Purpose: Detect the current market regime and trigger the appropriate integration mode.

Components:
- RegimeClassifier: Uses Hurst Exponent, FRAMA, volatility clustering, sentiment volatility
- VolatilityScanner: Detects transitions between Normal / Volatile / Extreme
- TrendRegimeAnalyzer: Identifies Trending vs Ranging
- TransitionDetector: Recognizes regime shifts and uncertain transitions

Outputs:
- Signals which of the 6 integration tiers should activate
- Confidence score for regime classification
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import logging
import numpy
import pandas

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classification"""
    NORMAL = "normal"
    VOLATILE = "volatile"
    EXTREME = "extreme"
    TRENDING = "trending"
    RANGING = "ranging"
    TRANSITIONING = "transitioning"


@dataclass
class RegimeSignal:
    """Output signal from market state detection"""
    regime: MarketRegime
    confidence: float
    integration_mode: str
    metrics: Dict[str, float]
    timestamp: pd.Timestamp


class RegimeClassifier:
    """
    Classifies market regime using advanced statistical methods
    
    Methods:
    - Hurst Exponent: Measures long-term memory and trend persistence
    - FRAMA (Fractal Adaptive Moving Average): Adapts to market fractality
    - Volatility Clustering: Detects periods of high/low volatility
    - Sentiment Volatility: Measures sentiment uncertainty
    """
    
    def __init__(self, lookback: int = 100):
        self.lookback = lookback
        
    def calculate_hurst_exponent(self, prices: np.ndarray) -> float:
        """
        Calculate Hurst Exponent
        
        H < 0.5: Mean-reverting
        H = 0.5: Random walk
        H > 0.5: Trending
        """
        try:
            lags = range(2, min(20, len(prices) // 2))
            tau = [np.std(np.subtract(prices[lag:], prices[:-lag])) for lag in lags]
            
            # Linear regression on log-log plot
            poly = np.polyfit(np.log(lags), np.log(tau), 1)
            hurst = poly[0]
            
            return np.clip(hurst, 0.0, 1.0)
        except Exception:
            return 0.5  # Default to random walk
    
    def calculate_frama(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate Fractal Adaptive Moving Average
        
        Adapts smoothing based on market fractality
        """
        n = len(prices)
        frama = pd.Series(index=prices.index, dtype=float)
        
        for i in range(period, n):
            window = prices.iloc[i-period:i].values
            
            # Calculate fractal dimension
            high_low = np.max(window) - np.min(window)
            
            if high_low > 0:
                # Split window in half
                mid = period // 2
                h1 = np.max(window[:mid]) - np.min(window[:mid])
                h2 = np.max(window[mid:]) - np.min(window[mid:])
                
                # Fractal dimension
                n1 = (h1 + h2) / high_low
                dimension = (np.log(n1 + 1) / np.log(2)) if n1 > 0 else 1
                
                # Alpha (smoothing factor)
                alpha = np.exp(-4.6 * (dimension - 1))
                alpha = np.clip(alpha, 0.01, 1.0)
            else:
                alpha = 0.5
            
            # Calculate FRAMA
            if i == period:
                frama.iloc[i] = prices.iloc[i]
            else:
                frama.iloc[i] = alpha * prices.iloc[i] + (1 - alpha) * frama.iloc[i-1]
        
        return frama
    
    def detect_volatility_clustering(self, returns: pd.Series) -> float:
        """
        Detect volatility clustering using GARCH-like approach
        
        Returns clustering coefficient (0-1)
        """
        # Calculate rolling volatility
        vol = returns.rolling(window=20).std()
        
        # Autocorrelation of squared returns (proxy for clustering)
        squared_returns = returns ** 2
        autocorr = squared_returns.autocorr(lag=1)
        
        # Clustering coefficient
        clustering = abs(autocorr) if not np.isnan(autocorr) else 0.0
        
        return np.clip(clustering, 0.0, 1.0)
    
    def calculate_sentiment_volatility(self, sentiment_scores: Optional[pd.Series] = None) -> float:
        """
        Calculate sentiment volatility
        
        High sentiment volatility indicates uncertainty
        """
        if sentiment_scores is None or len(sentiment_scores) < 10:
            return 0.5  # Neutral
        
        # Standard deviation of sentiment
        sent_vol = sentiment_scores.rolling(window=20).std().iloc[-1]
        
        # Normalize to 0-1
        normalized = np.clip(sent_vol / 0.5, 0.0, 1.0)
        
        return normalized
    
    def classify(self, market_data: pd.DataFrame, 
                 sentiment_data: Optional[pd.Series] = None) -> Dict[str, float]:
        """
        Classify market regime using all methods
        
        Returns:
            Dictionary with regime metrics
        """
        prices = market_data['close'].values
        returns = market_data['close'].pct_change().dropna()
        
        # Calculate metrics
        hurst = self.calculate_hurst_exponent(prices[-self.lookback:])
        frama = self.calculate_frama(market_data['close'])
        clustering = self.detect_volatility_clustering(returns)
        sent_vol = self.calculate_sentiment_volatility(sentiment_data)
        
        # Current volatility
        current_vol = returns.iloc[-20:].std() * np.sqrt(252)
        
        metrics = {
            'hurst_exponent': hurst,
            'frama_value': frama.iloc[-1] if not frama.empty else prices[-1],
            'volatility_clustering': clustering,
            'sentiment_volatility': sent_vol,
            'current_volatility': current_vol,
            'trend_strength': abs(hurst - 0.5) * 2  # 0 = no trend, 1 = strong trend
        }
        
        return metrics


class VolatilityScanner:
    """
    Detects volatility regime transitions
    
    Classifies into: Normal / Volatile / Extreme
    """
    
    def __init__(self, 
                 normal_threshold: float = 0.015,
                 volatile_threshold: float = 0.03,
                 extreme_threshold: float = 0.05):
        self.normal_threshold = normal_threshold
        self.volatile_threshold = volatile_threshold
        self.extreme_threshold = extreme_threshold
    
    def scan(self, market_data: pd.DataFrame) -> Tuple[str, float]:
        """
        Scan volatility and classify regime
        
        Returns:
            (regime_name, volatility_value)
        """
        returns = market_data['close'].pct_change().dropna()
        
        # Annualized volatility
        volatility = returns.std() * np.sqrt(252)
        
        # Classify
        if volatility >= self.extreme_threshold:
            regime = "extreme"
        elif volatility >= self.volatile_threshold:
            regime = "volatile"
        else:
            regime = "normal"
        
        return regime, volatility


class TrendRegimeAnalyzer:
    """
    Identifies Trending vs Ranging markets
    
    Uses multiple indicators:
    - ADX (Average Directional Index)
    - Price vs Moving Averages
    - Linear regression slope
    """
    
    def __init__(self, adx_threshold: float = 25):
        self.adx_threshold = adx_threshold
    
    def calculate_adx(self, market_data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average Directional Index"""
        high = market_data['high']
        low = market_data['low']
        close = market_data['close']
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Directional Movement
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Smoothed indicators
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * pd.Series(plus_dm).rolling(window=period).mean() / atr
        minus_di = 100 * pd.Series(minus_dm).rolling(window=period).mean() / atr
        
        # ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx.iloc[-1] if not adx.empty else 0.0
    
    def calculate_trend_strength(self, market_data: pd.DataFrame) -> float:
        """
        Calculate trend strength using multiple methods
        
        Returns: 0 (ranging) to 1 (strong trend)
        """
        close = market_data['close']
        
        # Method 1: ADX
        adx = self.calculate_adx(market_data)
        adx_score = min(adx / 50, 1.0)  # Normalize to 0-1
        
        # Method 2: Price vs MA
        sma_20 = close.rolling(window=20).mean()
        sma_50 = close.rolling(window=50).mean()
        
        price_above_ma = (close.iloc[-1] - sma_20.iloc[-1]) / sma_20.iloc[-1]
        ma_alignment = 1.0 if (sma_20.iloc[-1] > sma_50.iloc[-1]) else 0.0
        
        # Method 3: Linear regression slope
        x = np.arange(len(close[-20:]))
        y = close[-20:].values
        slope = np.polyfit(x, y, 1)[0]
        slope_score = min(abs(slope) / (y.mean() * 0.01), 1.0)  # Normalize
        
        # Combine scores
        trend_strength = (adx_score * 0.5 + slope_score * 0.3 + ma_alignment * 0.2)
        
        return np.clip(trend_strength, 0.0, 1.0)
    
    def analyze(self, market_data: pd.DataFrame) -> Tuple[str, float]:
        """
        Analyze trend regime
        
        Returns:
            (regime_type, trend_strength)
        """
        trend_strength = self.calculate_trend_strength(market_data)
        
        if trend_strength > 0.6:
            regime = "trending"
        else:
            regime = "ranging"
        
        return regime, trend_strength


class TransitionDetector:
    """
    Recognizes regime shifts and uncertain transitions
    
    Uses:
    - Regime probability tracking
    - Change point detection
    - Entropy measurement
    """
    
    def __init__(self, transition_threshold: float = 0.6):
        self.transition_threshold = transition_threshold
        self.regime_history = []
    
    def calculate_regime_entropy(self, regime_probs: Dict[str, float]) -> float:
        """
        Calculate entropy of regime probabilities
        
        High entropy = uncertain/transitioning
        """
        probs = np.array(list(regime_probs.values()))
        probs = probs / probs.sum()  # Normalize
        
        # Shannon entropy
        entropy = -np.sum(probs * np.log2(probs + 1e-10))
        
        # Normalize to 0-1 (max entropy for 6 regimes = log2(6) ≈ 2.58)
        normalized_entropy = entropy / 2.58
        
        return normalized_entropy
    
    def detect_change_point(self, metric_series: pd.Series, window: int = 20) -> bool:
        """
        Detect change point in time series
        
        Uses CUSUM (Cumulative Sum) approach
        """
        if len(metric_series) < window * 2:
            return False
        
        # Split into two windows
        recent = metric_series.iloc[-window:]
        previous = metric_series.iloc[-2*window:-window]
        
        # Statistical test
        mean_diff = abs(recent.mean() - previous.mean())
        std_pooled = np.sqrt((recent.std()**2 + previous.std()**2) / 2)
        
        # Normalized difference
        if std_pooled > 0:
            z_score = mean_diff / std_pooled
            change_detected = z_score > 2.0  # 2 standard deviations
        else:
            change_detected = False
        
        return change_detected
    
    def detect(self, regime_metrics: Dict[str, float], 
               market_data: pd.DataFrame) -> Tuple[bool, float]:
        """
        Detect if market is in transition
        
        Returns:
            (is_transitioning, confidence)
        """
        # Calculate regime probabilities (simplified)
        regime_probs = {
            'normal': 1.0 - regime_metrics.get('current_volatility', 0.01) / 0.05,
            'volatile': regime_metrics.get('volatility_clustering', 0.5),
            'extreme': regime_metrics.get('current_volatility', 0.01) / 0.05,
            'trending': regime_metrics.get('trend_strength', 0.5),
            'ranging': 1.0 - regime_metrics.get('trend_strength', 0.5),
            'transitioning': regime_metrics.get('sentiment_volatility', 0.5)
        }
        
        # Normalize
        total = sum(regime_probs.values())
        regime_probs = {k: v/total for k, v in regime_probs.items()}
        
        # Calculate entropy
        entropy = self.calculate_regime_entropy(regime_probs)
        
        # Detect change point in volatility
        returns = market_data['close'].pct_change().dropna()
        vol_series = returns.rolling(window=20).std() * np.sqrt(252)
        change_point = self.detect_change_point(vol_series)
        
        # Transition detected if high entropy or change point
        is_transitioning = (entropy > 0.7) or change_point
        confidence = entropy if is_transitioning else (1.0 - entropy)
        
        return is_transitioning, confidence


class MarketStateEngine:
    """
    Main engine that combines all detection components
    
    Outputs:
    - Market regime classification
    - Confidence score
    - Recommended integration mode
    - Detailed metrics
    """
    
    def __init__(self):
        self.regime_classifier = RegimeClassifier()
        self.volatility_scanner = VolatilityScanner()
        self.trend_analyzer = TrendRegimeAnalyzer()
        self.transition_detector = TransitionDetector()
        
        # Regime to integration mode mapping
        self.regime_to_mode = {
            MarketRegime.NORMAL: "full_tier",
            MarketRegime.VOLATILE: "fast_track",
            MarketRegime.EXTREME: "emergency",
            MarketRegime.TRENDING: "trend_focused",
            MarketRegime.RANGING: "mean_reversion",
            MarketRegime.TRANSITIONING: "adaptive"
        }
    
    def detect_market_state(self, market_data: pd.DataFrame,
                           sentiment_data: Optional[pd.Series] = None) -> RegimeSignal:
        """
        Detect current market state and recommend integration mode
        
        Args:
            market_data: OHLCV DataFrame
            sentiment_data: Optional sentiment scores
            
        Returns:
            RegimeSignal with regime, confidence, and integration mode
        """
        # Get regime metrics
        regime_metrics = self.regime_classifier.classify(market_data, sentiment_data)
        
        # Scan volatility
        vol_regime, volatility = self.volatility_scanner.scan(market_data)
        
        # Analyze trend
        trend_regime, trend_strength = self.trend_analyzer.analyze(market_data)
        
        # Detect transitions
        is_transitioning, transition_conf = self.transition_detector.detect(
            regime_metrics, market_data
        )
        
        # Determine primary regime
        if is_transitioning:
            regime = MarketRegime.TRANSITIONING
            confidence = transition_conf
        elif vol_regime == "extreme":
            regime = MarketRegime.EXTREME
            confidence = min(volatility / 0.05, 1.0)
        elif vol_regime == "volatile":
            regime = MarketRegime.VOLATILE
            confidence = min(volatility / 0.03, 1.0)
        elif trend_regime == "trending":
            regime = MarketRegime.TRENDING
            confidence = trend_strength
        elif trend_regime == "ranging":
            regime = MarketRegime.RANGING
            confidence = 1.0 - trend_strength
        else:
            regime = MarketRegime.NORMAL
            confidence = 1.0 - min(volatility / 0.015, 1.0)
        
        # Get integration mode
        integration_mode = self.regime_to_mode[regime]
        
        # Compile all metrics
        all_metrics = {
            **regime_metrics,
            'volatility': volatility,
            'vol_regime': vol_regime,
            'trend_regime': trend_regime,
            'trend_strength': trend_strength,
            'is_transitioning': is_transitioning,
            'transition_confidence': transition_conf
        }
        
        # Create signal
        signal = RegimeSignal(
            regime=regime,
            confidence=confidence,
            integration_mode=integration_mode,
            metrics=all_metrics,
            timestamp=market_data.index[-1] if hasattr(market_data.index[-1], 'timestamp') else pd.Timestamp.now()
        )
        
        logger.info(f"Market State: {regime.value} (confidence: {confidence:.2%}) -> Mode: {integration_mode}")
        
        return signal


# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start='2025-01-01', periods=200, freq='1H')
    np.random.seed(42)
    
    # Normal market
    prices = 1.1000 + np.cumsum(np.random.normal(0, 0.0005, 200))
    market_data = pd.DataFrame({
        'timestamp': dates,
        'open': prices + np.random.normal(0, 0.0002, 200),
        'high': prices + np.random.normal(0.0003, 0.0002, 200),
        'low': prices + np.random.normal(-0.0003, 0.0002, 200),
        'close': prices,
        'volume': np.random.randint(1000, 5000, 200)
    })
    market_data.set_index('timestamp', inplace=True)
    
    # Initialize engine
    engine = MarketStateEngine()
    
    # Detect state
    signal = engine.detect_market_state(market_data)
    
    logger.info(f"\nMarket State Detection:")
    logger.info(f"  Regime: {signal.regime.value}")
    logger.info(f"  Confidence: {signal.confidence:.2%}")
    logger.info(f"  Integration Mode: {signal.integration_mode}")
    logger.info(f"\nMetrics:")
    for key, value in signal.metrics.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.4f}")
        else:
            logger.info(f"  {key}: {value}")
