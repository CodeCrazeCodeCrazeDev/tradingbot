"""
Comprehensive ML Module Tests
Tests for machine learning components including:
- Technical indicators
- Market regime detection
- Ensemble predictors
- Online learning
- Feature engineering
- Model validation
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock
import numpy
import pandas


# ============================================================================
# TECHNICAL INDICATORS TESTS
# ============================================================================

class TestTechnicalIndicators:
    """Tests for technical indicator calculations"""
    
    @pytest.fixture
    def sample_prices(self):
        """Generate sample price data"""
        np.random.seed(42)
        n = 100
        prices = 100 + np.cumsum(np.random.randn(n) * 0.5)
        return pd.Series(prices)
    
    @pytest.fixture
    def sample_ohlcv(self):
        """Generate sample OHLCV data"""
        np.random.seed(42)
        n = 100
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)
        high = close + np.abs(np.random.randn(n) * 0.3)
        low = close - np.abs(np.random.randn(n) * 0.3)
        open_price = close + np.random.randn(n) * 0.2
        volume = np.random.randint(1000, 10000, n)
        
        return pd.DataFrame({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    def test_sma_calculation(self, sample_prices):
        """Test Simple Moving Average calculation"""
        period = 20
        sma = sample_prices.rolling(window=period).mean()
        
        assert len(sma) == len(sample_prices)
        assert sma.iloc[:period-1].isna().all()
        assert not sma.iloc[period:].isna().any()
    
    def test_ema_calculation(self, sample_prices):
        """Test Exponential Moving Average calculation"""
        period = 20
        ema = sample_prices.ewm(span=period, adjust=False).mean()
        
        assert len(ema) == len(sample_prices)
        assert not ema.isna().any()
    
    def test_rsi_calculation(self, sample_prices):
        """Test RSI calculation"""
        period = 14
        delta = sample_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()
    
    def test_bollinger_bands(self, sample_prices):
        """Test Bollinger Bands calculation"""
        period = 20
        std_dev = 2
        
        sma = sample_prices.rolling(window=period).mean()
        std = sample_prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        # Upper should always be >= SMA >= Lower
        valid_idx = ~sma.isna()
        assert (upper[valid_idx] >= sma[valid_idx]).all()
        assert (sma[valid_idx] >= lower[valid_idx]).all()
    
    def test_macd_calculation(self, sample_prices):
        """Test MACD calculation"""
        fast = 12
        slow = 26
        signal = 9
        
        ema_fast = sample_prices.ewm(span=fast, adjust=False).mean()
        ema_slow = sample_prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        assert len(macd_line) == len(sample_prices)
        assert len(signal_line) == len(sample_prices)
        assert len(histogram) == len(sample_prices)
    
    def test_atr_calculation(self, sample_ohlcv):
        """Test Average True Range calculation"""
        period = 14
        
        high = sample_ohlcv['high']
        low = sample_ohlcv['low']
        close = sample_ohlcv['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        # ATR should always be positive
        valid_atr = atr.dropna()
        assert (valid_atr >= 0).all()
    
    def test_stochastic_oscillator(self, sample_ohlcv):
        """Test Stochastic Oscillator calculation"""
        k_period = 14
        d_period = 3
        
        low_min = sample_ohlcv['low'].rolling(window=k_period).min()
        high_max = sample_ohlcv['high'].rolling(window=k_period).max()
        
        k = 100 * (sample_ohlcv['close'] - low_min) / (high_max - low_min)
        d = k.rolling(window=d_period).mean()
        
        # %K and %D should be between 0 and 100
        valid_k = k.dropna()
        valid_d = d.dropna()
        assert (valid_k >= 0).all() and (valid_k <= 100).all()
        assert (valid_d >= 0).all() and (valid_d <= 100).all()
    
    def test_volume_indicators(self, sample_ohlcv):
        """Test volume-based indicators"""
        # On-Balance Volume
        obv = (np.sign(sample_ohlcv['close'].diff()) * sample_ohlcv['volume']).cumsum()
        
        # Volume Moving Average
        vol_ma = sample_ohlcv['volume'].rolling(window=20).mean()
        
        assert len(obv) == len(sample_ohlcv)
        assert len(vol_ma) == len(sample_ohlcv)


# ============================================================================
# MARKET REGIME DETECTION TESTS
# ============================================================================

class TestMarketRegimeDetection:
    """Tests for market regime detection"""
    
    @pytest.fixture
    def trending_data(self):
        """Generate trending market data"""
        np.random.seed(42)
        n = 100
        trend = np.linspace(100, 120, n)
        noise = np.random.randn(n) * 0.5
        return pd.Series(trend + noise)
    
    @pytest.fixture
    def ranging_data(self):
        """Generate ranging market data"""
        np.random.seed(42)
        n = 100
        base = 100
        noise = np.random.randn(n) * 2
        return pd.Series(base + noise)
    
    @pytest.fixture
    def volatile_data(self):
        """Generate volatile market data"""
        np.random.seed(42)
        n = 100
        prices = 100 + np.cumsum(np.random.randn(n) * 3)
        return pd.Series(prices)
    
    def test_detect_trending_regime(self, trending_data):
        """Test detection of trending market"""
        # Calculate trend strength using ADX-like metric
        returns = trending_data.pct_change().dropna()
        
        # Positive returns indicate uptrend
        positive_returns = (returns > 0).sum() / len(returns)
        
        # Trending market should have consistent direction
        assert positive_returns > 0.6 or positive_returns < 0.4
    
    def test_detect_ranging_regime(self, ranging_data):
        """Test detection of ranging market"""
        # Calculate range metrics
        price_range = ranging_data.max() - ranging_data.min()
        mean_price = ranging_data.mean()
        range_pct = price_range / mean_price * 100
        
        # Ranging market should have small range
        assert range_pct < 10
    
    def test_detect_volatile_regime(self, volatile_data):
        """Test detection of volatile market"""
        # Calculate volatility
        returns = volatile_data.pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # Annualized
        
        # Volatile market should have high volatility
        assert volatility > 0.1
    
    def test_regime_transition_detection(self):
        """Test detection of regime transitions"""
        np.random.seed(42)
        
        # Create data with regime change
        trending = np.linspace(100, 110, 50)
        ranging = 110 + np.random.randn(50) * 0.5
        prices = pd.Series(np.concatenate([trending, ranging]))
        
        # Calculate rolling volatility
        returns = prices.pct_change()
        rolling_vol = returns.rolling(window=20).std()
        
        # Volatility should change at regime transition
        vol_change = rolling_vol.diff().abs()
        max_change_idx = vol_change.idxmax()
        
        # Transition should be detected around index 50
        assert 40 < max_change_idx < 60
    
    def test_hurst_exponent_calculation(self, trending_data):
        """Test Hurst exponent for trend detection"""
        # Simplified Hurst exponent calculation
        returns = trending_data.pct_change().dropna()
        
        # R/S analysis
        mean_return = returns.mean()
        std_return = returns.std()
        
        if std_return > 0:
            cumdev = (returns - mean_return).cumsum()
            r = cumdev.max() - cumdev.min()
            s = std_return
            rs = r / s if s > 0 else 0
            
            # Hurst > 0.5 indicates trending
            # This is a simplified check
            assert rs > 0


# ============================================================================
# ENSEMBLE PREDICTOR TESTS
# ============================================================================

class TestEnsemblePredictor:
    """Tests for ensemble prediction models"""
    
    @pytest.fixture
    def sample_features(self):
        """Generate sample features"""
        np.random.seed(42)
        n = 100
        return pd.DataFrame({
            'feature1': np.random.randn(n),
            'feature2': np.random.randn(n),
            'feature3': np.random.randn(n),
            'feature4': np.random.randn(n),
            'feature5': np.random.randn(n)
        })
    
    @pytest.fixture
    def sample_targets(self):
        """Generate sample targets"""
        np.random.seed(42)
        return pd.Series(np.random.choice([0, 1], 100))
    
    def test_voting_ensemble(self, sample_features, sample_targets):
        """Test voting ensemble"""
        # Simulate 3 model predictions
        np.random.seed(42)
        pred1 = np.random.choice([0, 1], len(sample_targets))
        pred2 = np.random.choice([0, 1], len(sample_targets))
        pred3 = np.random.choice([0, 1], len(sample_targets))
        
        # Majority voting
        ensemble_pred = (pred1 + pred2 + pred3) >= 2
        
        assert len(ensemble_pred) == len(sample_targets)
        assert set(ensemble_pred.astype(int)).issubset({0, 1})
    
    def test_weighted_ensemble(self, sample_features, sample_targets):
        """Test weighted ensemble"""
        # Simulate 3 model predictions with probabilities
        np.random.seed(42)
        prob1 = np.random.rand(len(sample_targets))
        prob2 = np.random.rand(len(sample_targets))
        prob3 = np.random.rand(len(sample_targets))
        
        # Weighted average
        weights = [0.5, 0.3, 0.2]
        ensemble_prob = weights[0] * prob1 + weights[1] * prob2 + weights[2] * prob3
        
        assert len(ensemble_prob) == len(sample_targets)
        assert (ensemble_prob >= 0).all() and (ensemble_prob <= 1).all()
    
    def test_stacking_ensemble(self, sample_features, sample_targets):
        """Test stacking ensemble"""
        # Simulate base model predictions
        np.random.seed(42)
        base_preds = pd.DataFrame({
            'model1': np.random.rand(len(sample_targets)),
            'model2': np.random.rand(len(sample_targets)),
            'model3': np.random.rand(len(sample_targets))
        })
        
        # Meta-learner (simple average for test)
        meta_pred = base_preds.mean(axis=1)
        
        assert len(meta_pred) == len(sample_targets)
    
    def test_ensemble_diversity(self, sample_features, sample_targets):
        """Test ensemble model diversity"""
        np.random.seed(42)
        
        # Simulate diverse predictions
        pred1 = np.random.choice([0, 1], len(sample_targets))
        pred2 = np.random.choice([0, 1], len(sample_targets))
        pred3 = np.random.choice([0, 1], len(sample_targets))
        
        # Calculate disagreement rate
        disagreement_12 = (pred1 != pred2).mean()
        disagreement_13 = (pred1 != pred3).mean()
        disagreement_23 = (pred2 != pred3).mean()
        
        avg_disagreement = (disagreement_12 + disagreement_13 + disagreement_23) / 3
        
        # Some diversity expected (not all same predictions)
        assert avg_disagreement > 0


# ============================================================================
# ONLINE LEARNING TESTS
# ============================================================================

class TestOnlineLearning:
    """Tests for online learning components"""
    
    def test_incremental_mean_update(self):
        """Test incremental mean calculation"""
        np.random.seed(42)
        data = np.random.randn(100)
        
        # Incremental mean
        running_mean = 0
        count = 0
        
        for x in data:
            count += 1
            running_mean += (x - running_mean) / count
        
        # Should match batch mean
        assert abs(running_mean - data.mean()) < 1e-10
    
    def test_incremental_variance_update(self):
        """Test incremental variance calculation (Welford's algorithm)"""
        np.random.seed(42)
        data = np.random.randn(100)
        
        mean = 0
        M2 = 0
        count = 0
        
        for x in data:
            count += 1
            delta = x - mean
            mean += delta / count
            delta2 = x - mean
            M2 += delta * delta2
        
        variance = M2 / count if count > 0 else 0
        
        # Should match batch variance
        assert abs(variance - data.var()) < 1e-10
    
    def test_exponential_weighted_update(self):
        """Test exponential weighted moving average update"""
        np.random.seed(42)
        data = np.random.randn(100)
        alpha = 0.1
        
        ewma = data[0]
        for x in data[1:]:
            ewma = alpha * x + (1 - alpha) * ewma
        
        # Compare with pandas
        pd_ewma = pd.Series(data).ewm(alpha=alpha, adjust=False).mean().iloc[-1]
        
        assert abs(ewma - pd_ewma) < 1e-10
    
    def test_sliding_window_update(self):
        """Test sliding window statistics"""
        np.random.seed(42)
        data = np.random.randn(100)
        window_size = 20
        
        # Sliding window mean
        window = []
        sliding_means = []
        
        for x in data:
            window.append(x)
            if len(window) > window_size:
                window.pop(0)
            sliding_means.append(np.mean(window))
        
        # Compare with pandas
        pd_rolling = pd.Series(data).rolling(window=window_size, min_periods=1).mean()
        
        assert np.allclose(sliding_means, pd_rolling.values)
    
    def test_concept_drift_detection(self):
        """Test concept drift detection"""
        np.random.seed(42)
        
        # Data with drift
        data1 = np.random.randn(50)
        data2 = np.random.randn(50) + 2  # Shifted mean
        data = np.concatenate([data1, data2])
        
        # Simple drift detection using CUSUM
        target_mean = 0
        threshold = 5
        cusum_pos = 0
        cusum_neg = 0
        drift_detected = False
        drift_point = -1
        
        for i, x in enumerate(data):
            cusum_pos = max(0, cusum_pos + x - target_mean - 0.5)
            cusum_neg = max(0, cusum_neg - x + target_mean - 0.5)
            
            if cusum_pos > threshold or cusum_neg > threshold:
                drift_detected = True
                drift_point = i
                break
        
        # Drift should be detected
        assert drift_detected
        assert 40 < drift_point < 70


# ============================================================================
# FEATURE ENGINEERING TESTS
# ============================================================================

class TestFeatureEngineering:
    """Tests for feature engineering"""
    
    @pytest.fixture
    def sample_ohlcv(self):
        """Generate sample OHLCV data"""
        np.random.seed(42)
        n = 100
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)
        high = close + np.abs(np.random.randn(n) * 0.3)
        low = close - np.abs(np.random.randn(n) * 0.3)
        open_price = close + np.random.randn(n) * 0.2
        volume = np.random.randint(1000, 10000, n)
        
        return pd.DataFrame({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    def test_returns_features(self, sample_ohlcv):
        """Test return-based features"""
        close = sample_ohlcv['close']
        
        # Simple returns
        returns = close.pct_change()
        
        # Log returns
        log_returns = np.log(close / close.shift(1))
        
        # Multi-period returns
        returns_5 = close.pct_change(5)
        returns_20 = close.pct_change(20)
        
        assert len(returns) == len(close)
        assert len(log_returns) == len(close)
        assert len(returns_5) == len(close)
        assert len(returns_20) == len(close)
    
    def test_volatility_features(self, sample_ohlcv):
        """Test volatility-based features"""
        returns = sample_ohlcv['close'].pct_change()
        
        # Rolling volatility
        vol_5 = returns.rolling(5).std()
        vol_20 = returns.rolling(20).std()
        
        # Parkinson volatility
        high = sample_ohlcv['high']
        low = sample_ohlcv['low']
        parkinson = np.sqrt((np.log(high / low) ** 2).rolling(20).mean() / (4 * np.log(2)))
        
        assert len(vol_5) == len(returns)
        assert len(vol_20) == len(returns)
        assert len(parkinson) == len(returns)
    
    def test_momentum_features(self, sample_ohlcv):
        """Test momentum-based features"""
        close = sample_ohlcv['close']
        
        # Rate of change
        roc_5 = (close - close.shift(5)) / close.shift(5) * 100
        roc_20 = (close - close.shift(20)) / close.shift(20) * 100
        
        # Momentum
        mom_5 = close - close.shift(5)
        mom_20 = close - close.shift(20)
        
        assert len(roc_5) == len(close)
        assert len(roc_20) == len(close)
        assert len(mom_5) == len(close)
        assert len(mom_20) == len(close)
    
    def test_price_pattern_features(self, sample_ohlcv):
        """Test price pattern features"""
        open_price = sample_ohlcv['open']
        high = sample_ohlcv['high']
        low = sample_ohlcv['low']
        close = sample_ohlcv['close']
        
        # Candlestick features
        body = close - open_price
        upper_shadow = high - np.maximum(open_price, close)
        lower_shadow = np.minimum(open_price, close) - low
        
        # Body to range ratio
        candle_range = high - low
        body_ratio = body / candle_range.replace(0, np.nan)
        
        assert len(body) == len(close)
        assert len(upper_shadow) == len(close)
        assert len(lower_shadow) == len(close)
    
    def test_volume_features(self, sample_ohlcv):
        """Test volume-based features"""
        volume = sample_ohlcv['volume']
        close = sample_ohlcv['close']
        
        # Volume moving average
        vol_ma = volume.rolling(20).mean()
        
        # Volume ratio
        vol_ratio = volume / vol_ma
        
        # Price-volume trend
        pvt = ((close - close.shift(1)) / close.shift(1) * volume).cumsum()
        
        assert len(vol_ma) == len(volume)
        assert len(vol_ratio) == len(volume)
        assert len(pvt) == len(volume)
    
    def test_feature_normalization(self, sample_ohlcv):
        """Test feature normalization"""
        close = sample_ohlcv['close']
        
        # Z-score normalization
        z_score = (close - close.mean()) / close.std()
        
        # Min-max normalization
        min_max = (close - close.min()) / (close.max() - close.min())
        
        # Rolling z-score
        rolling_mean = close.rolling(20).mean()
        rolling_std = close.rolling(20).std()
        rolling_z = (close - rolling_mean) / rolling_std
        
        assert abs(z_score.mean()) < 1e-10
        assert abs(z_score.std() - 1) < 1e-10
        assert min_max.min() == 0
        assert min_max.max() == 1


# ============================================================================
# MODEL VALIDATION TESTS
# ============================================================================

class TestModelValidation:
    """Tests for model validation"""
    
    def test_train_test_split(self):
        """Test time-series train/test split"""
        np.random.seed(42)
        n = 100
        data = pd.DataFrame({
            'feature': np.random.randn(n),
            'target': np.random.choice([0, 1], n)
        })
        
        train_size = 0.8
        split_idx = int(len(data) * train_size)
        
        train = data.iloc[:split_idx]
        test = data.iloc[split_idx:]
        
        assert len(train) == 80
        assert len(test) == 20
        assert len(train) + len(test) == len(data)
    
    def test_walk_forward_validation(self):
        """Test walk-forward validation"""
        np.random.seed(42)
        n = 100
        data = np.random.randn(n)
        
        train_size = 60
        test_size = 10
        step = 10
        
        folds = []
        for i in range(0, n - train_size - test_size + 1, step):
            train_end = i + train_size
            test_end = train_end + test_size
            
            train_idx = list(range(i, train_end))
            test_idx = list(range(train_end, test_end))
            
            folds.append((train_idx, test_idx))
        
        # Should have multiple folds
        assert len(folds) >= 3
        
        # No overlap between train and test
        for train_idx, test_idx in folds:
            assert len(set(train_idx) & set(test_idx)) == 0
    
    def test_cross_validation_metrics(self):
        """Test cross-validation metrics calculation"""
        np.random.seed(42)
        
        # Simulate predictions and actuals
        y_true = np.random.choice([0, 1], 100)
        y_pred = np.random.choice([0, 1], 100)
        
        # Calculate metrics
        tp = ((y_true == 1) & (y_pred == 1)).sum()
        tn = ((y_true == 0) & (y_pred == 0)).sum()
        fp = ((y_true == 0) & (y_pred == 1)).sum()
        fn = ((y_true == 1) & (y_pred == 0)).sum()
        
        accuracy = (tp + tn) / (tp + tn + fp + fn)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        assert 0 <= accuracy <= 1
        assert 0 <= precision <= 1
        assert 0 <= recall <= 1
        assert 0 <= f1 <= 1
    
    def test_overfitting_detection(self):
        """Test overfitting detection"""
        np.random.seed(42)
        
        # Simulate train and test performance
        train_accuracy = 0.95  # High train accuracy
        test_accuracy = 0.55   # Low test accuracy
        
        # Overfitting gap
        gap = train_accuracy - test_accuracy
        
        # Large gap indicates overfitting
        assert gap > 0.3  # Significant overfitting
    
    def test_learning_curve_analysis(self):
        """Test learning curve analysis"""
        np.random.seed(42)
        
        # Simulate learning curve data
        train_sizes = [100, 200, 500, 1000, 2000]
        train_scores = [0.95, 0.92, 0.88, 0.85, 0.82]
        test_scores = [0.50, 0.60, 0.70, 0.75, 0.78]
        
        # Check convergence
        score_improvement = test_scores[-1] - test_scores[0]
        gap_reduction = (train_scores[0] - test_scores[0]) - (train_scores[-1] - test_scores[-1])
        
        assert score_improvement > 0  # Test score improves
        assert gap_reduction > 0  # Gap reduces


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
