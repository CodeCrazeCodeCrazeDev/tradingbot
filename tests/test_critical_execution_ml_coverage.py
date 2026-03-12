"""
CRITICAL EXECUTION AND ML TEST SUITE
====================================

Tests for execution algorithms, ML models, and analysis modules.
Target: 100% coverage on important execution and ML modules.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, List, Any
import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# FILL TRACKER TESTS (100% Coverage)
# ============================================================================

class TestFillTracker:
    """Complete test coverage for fill tracker"""
    
    @pytest.fixture
    def fill_tracker(self):
        """Create fill tracker instance"""
        from trading_bot.execution.fill_tracker import FillTracker
        return FillTracker()
    
    def test_init(self, fill_tracker):
        """Test initialization"""
        assert fill_tracker is not None
        assert hasattr(fill_tracker, 'pending_orders')
    
    def test_track_order(self, fill_tracker):
        """Test order tracking"""
        order_id = fill_tracker.track_order(
            order_id='ORD-001',
            symbol='EURUSD',
            side='BUY',
            quantity=1.0,
            expected_price=1.1000
        )
        
        assert order_id == 'ORD-001'
        assert 'ORD-001' in fill_tracker.pending_orders
    
    def test_confirm_fill(self, fill_tracker):
        """Test fill confirmation"""
        fill_tracker.track_order(
            order_id='ORD-001',
            symbol='EURUSD',
            side='BUY',
            quantity=1.0,
            expected_price=1.1000
        )
        
        result = fill_tracker.confirm_fill(
            order_id='ORD-001',
            filled_quantity=1.0,
            fill_price=1.1002,
            fill_time=datetime.now()
        )
        
        assert result['success'] is True
        assert result['slippage_bps'] is not None
    
    def test_confirm_fill_nonexistent(self, fill_tracker):
        """Test confirming nonexistent order"""
        result = fill_tracker.confirm_fill(
            order_id='NONEXISTENT',
            filled_quantity=1.0,
            fill_price=1.1000
        )
        
        assert result['success'] is False
    
    def test_get_pending_orders(self, fill_tracker):
        """Test getting pending orders"""
        fill_tracker.track_order('ORD-001', 'EURUSD', 'BUY', 1.0, 1.1000)
        fill_tracker.track_order('ORD-002', 'GBPUSD', 'SELL', 0.5, 1.2500)
        
        pending = fill_tracker.get_pending_orders()
        
        assert len(pending) == 2
    
    def test_cancel_tracking(self, fill_tracker):
        """Test canceling order tracking"""
        fill_tracker.track_order('ORD-001', 'EURUSD', 'BUY', 1.0, 1.1000)
        
        result = fill_tracker.cancel_tracking('ORD-001')
        
        assert result is True
        assert 'ORD-001' not in fill_tracker.pending_orders
    
    def test_get_fill_statistics(self, fill_tracker):
        """Test getting fill statistics"""
        # Track and confirm some orders
        fill_tracker.track_order('ORD-001', 'EURUSD', 'BUY', 1.0, 1.1000)
        fill_tracker.confirm_fill('ORD-001', 1.0, 1.1002, datetime.now())
        
        fill_tracker.track_order('ORD-002', 'EURUSD', 'SELL', 1.0, 1.1050)
        fill_tracker.confirm_fill('ORD-002', 1.0, 1.1048, datetime.now())
        
        stats = fill_tracker.get_fill_statistics()
        
        assert 'total_fills' in stats
        assert 'avg_slippage_bps' in stats


# ============================================================================
# IDEMPOTENT EXECUTOR TESTS (100% Coverage)
# ============================================================================

class TestIdempotentExecutor:
    """Complete test coverage for idempotent executor"""
    
    @pytest.fixture
    def executor(self):
        """Create idempotent executor instance"""
        from trading_bot.execution.idempotent_executor import IdempotentExecutor
        return IdempotentExecutor()
    
    def test_init(self, executor):
        """Test initialization"""
        assert executor is not None
        assert hasattr(executor, 'executed_orders')
    
    def test_generate_client_order_id(self, executor):
        """Test client order ID generation"""
        order_id = executor.generate_client_order_id(
            symbol='EURUSD',
            side='BUY',
            quantity=1.0
        )
        
        assert order_id is not None
        assert len(order_id) > 0
    
    def test_is_duplicate_order_new(self, executor):
        """Test duplicate check for new order"""
        is_dup = executor.is_duplicate_order('NEW-ORDER-001')
        
        assert is_dup is False
    
    def test_is_duplicate_order_existing(self, executor):
        """Test duplicate check for existing order"""
        executor.mark_order_executed('EXISTING-001')
        
        is_dup = executor.is_duplicate_order('EXISTING-001')
        
        assert is_dup is True
    
    def test_execute_idempotent(self, executor):
        """Test idempotent execution"""
        result = executor.execute_idempotent(
            client_order_id='IDEMP-001',
            symbol='EURUSD',
            side='BUY',
            quantity=1.0,
            order_type='MARKET'
        )
        
        assert result is not None
        assert 'client_order_id' in result
    
    def test_execute_idempotent_duplicate(self, executor):
        """Test idempotent execution with duplicate"""
        # First execution
        executor.execute_idempotent(
            client_order_id='IDEMP-001',
            symbol='EURUSD',
            side='BUY',
            quantity=1.0,
            order_type='MARKET'
        )
        
        # Duplicate execution
        result = executor.execute_idempotent(
            client_order_id='IDEMP-001',
            symbol='EURUSD',
            side='BUY',
            quantity=1.0,
            order_type='MARKET'
        )
        
        assert result['duplicate'] is True
    
    def test_get_order_status(self, executor):
        """Test getting order status"""
        executor.execute_idempotent(
            client_order_id='IDEMP-001',
            symbol='EURUSD',
            side='BUY',
            quantity=1.0,
            order_type='MARKET'
        )
        
        status = executor.get_order_status('IDEMP-001')
        
        assert status is not None


# ============================================================================
# ROBUST RETRY TESTS (100% Coverage)
# ============================================================================

class TestRobustRetry:
    """Complete test coverage for robust retry"""
    
    @pytest.fixture
    def retry_executor(self):
        """Create robust retry executor instance"""
        from trading_bot.execution.robust_retry import RobustRetryExecutor
        return RobustRetryExecutor(max_retries=3, base_delay=0.1)
    
    def test_init(self, retry_executor):
        """Test initialization"""
        assert retry_executor.max_retries == 3
        assert retry_executor.base_delay == 0.1
    
    def test_execute_with_retry_success(self, retry_executor):
        """Test successful execution"""
        def success_func():
            return {'success': True, 'data': 'test'}
        
        result = retry_executor.execute_with_retry(success_func)
        
        assert result['success'] is True
    
    def test_execute_with_retry_failure_then_success(self, retry_executor):
        """Test execution that fails then succeeds"""
        attempt_count = [0]
        
        def flaky_func():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise Exception("Temporary failure")
            return {'success': True}
        
        result = retry_executor.execute_with_retry(flaky_func)
        
        assert result['success'] is True
        assert attempt_count[0] == 2
    
    def test_execute_with_retry_all_failures(self, retry_executor):
        """Test execution that always fails"""
        def always_fail():
            raise Exception("Permanent failure")
        
        result = retry_executor.execute_with_retry(always_fail)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_calculate_delay(self, retry_executor):
        """Test delay calculation"""
        delay1 = retry_executor.calculate_delay(1)
        delay2 = retry_executor.calculate_delay(2)
        delay3 = retry_executor.calculate_delay(3)
        
        # Exponential backoff
        assert delay2 > delay1
        assert delay3 > delay2
    
    def test_is_retryable_error(self, retry_executor):
        """Test retryable error detection"""
        # Network errors should be retryable
        assert retry_executor.is_retryable_error(ConnectionError("Network error")) is True
        
        # Value errors should not be retryable
        assert retry_executor.is_retryable_error(ValueError("Invalid value")) is False


# ============================================================================
# PARTIAL FILL AGGREGATOR TESTS (100% Coverage)
# ============================================================================

class TestPartialFillAggregator:
    """Complete test coverage for partial fill aggregator"""
    
    @pytest.fixture
    def aggregator(self):
        """Create partial fill aggregator instance"""
        from trading_bot.execution.partial_fill_aggregator import PartialFillAggregator
        return PartialFillAggregator()
    
    def test_init(self, aggregator):
        """Test initialization"""
        assert aggregator is not None
        assert hasattr(aggregator, 'orders')
    
    def test_create_order(self, aggregator):
        """Test order creation"""
        order_id = aggregator.create_order(
            symbol='EURUSD',
            side='BUY',
            total_quantity=10.0,
            limit_price=1.1000
        )
        
        assert order_id is not None
        assert order_id in aggregator.orders
    
    def test_add_fill(self, aggregator):
        """Test adding fill"""
        order_id = aggregator.create_order('EURUSD', 'BUY', 10.0, 1.1000)
        
        result = aggregator.add_fill(
            order_id=order_id,
            fill_quantity=3.0,
            fill_price=1.1002
        )
        
        assert result['success'] is True
        assert result['filled_quantity'] == 3.0
    
    def test_add_multiple_fills(self, aggregator):
        """Test adding multiple fills"""
        order_id = aggregator.create_order('EURUSD', 'BUY', 10.0, 1.1000)
        
        aggregator.add_fill(order_id, 3.0, 1.1002)
        aggregator.add_fill(order_id, 4.0, 1.1001)
        aggregator.add_fill(order_id, 3.0, 1.1003)
        
        status = aggregator.get_order_status(order_id)
        
        assert status['total_filled'] == 10.0
        assert status['is_complete'] is True
    
    def test_get_average_fill_price(self, aggregator):
        """Test average fill price calculation"""
        order_id = aggregator.create_order('EURUSD', 'BUY', 10.0, 1.1000)
        
        aggregator.add_fill(order_id, 5.0, 1.1000)
        aggregator.add_fill(order_id, 5.0, 1.1010)
        
        avg_price = aggregator.get_average_fill_price(order_id)
        
        assert avg_price == 1.1005  # Weighted average
    
    def test_get_remaining_quantity(self, aggregator):
        """Test remaining quantity calculation"""
        order_id = aggregator.create_order('EURUSD', 'BUY', 10.0, 1.1000)
        
        aggregator.add_fill(order_id, 3.0, 1.1002)
        
        remaining = aggregator.get_remaining_quantity(order_id)
        
        assert remaining == 7.0
    
    def test_cancel_order(self, aggregator):
        """Test order cancellation"""
        order_id = aggregator.create_order('EURUSD', 'BUY', 10.0, 1.1000)
        aggregator.add_fill(order_id, 3.0, 1.1002)
        
        result = aggregator.cancel_order(order_id)
        
        assert result['success'] is True
        assert result['filled_before_cancel'] == 3.0


# ============================================================================
# MARKET IMPACT TESTS (100% Coverage)
# ============================================================================

class TestMarketImpact:
    """Complete test coverage for market impact models"""
    
    @pytest.fixture
    def impact_model(self):
        """Create market impact model instance"""
        from trading_bot.execution.market_impact import MarketImpactModel
        return MarketImpactModel()
    
    def test_init(self, impact_model):
        """Test initialization"""
        assert impact_model is not None
    
    def test_estimate_impact_small_order(self, impact_model):
        """Test impact estimation for small order"""
        impact = impact_model.estimate_impact(
            symbol='EURUSD',
            quantity=0.1,
            side='BUY',
            avg_daily_volume=1000000
        )
        
        assert impact >= 0
        assert impact < 0.01  # Small order should have minimal impact
    
    def test_estimate_impact_large_order(self, impact_model):
        """Test impact estimation for large order"""
        impact = impact_model.estimate_impact(
            symbol='EURUSD',
            quantity=100.0,
            side='BUY',
            avg_daily_volume=1000
        )
        
        assert impact > 0  # Large order should have significant impact
    
    def test_calculate_optimal_execution_schedule(self, impact_model):
        """Test optimal execution schedule calculation"""
        schedule = impact_model.calculate_optimal_execution_schedule(
            symbol='EURUSD',
            total_quantity=10.0,
            side='BUY',
            time_horizon_minutes=60,
            urgency=0.5
        )
        
        assert len(schedule) > 0
        assert sum(s['quantity'] for s in schedule) == pytest.approx(10.0, rel=0.01)
    
    def test_estimate_slippage(self, impact_model):
        """Test slippage estimation"""
        slippage = impact_model.estimate_slippage(
            symbol='EURUSD',
            quantity=1.0,
            side='BUY',
            current_spread=0.0002
        )
        
        assert slippage >= 0


# ============================================================================
# SLIPPAGE PROTECTION TESTS (100% Coverage)
# ============================================================================

class TestSlippageProtection:
    """Complete test coverage for slippage protection"""
    
    @pytest.fixture
    def slippage_protector(self):
        """Create slippage protection instance"""
        from trading_bot.execution.slippage_protection import SlippageProtector
        return SlippageProtector(max_slippage_bps=50)
    
    def test_init(self, slippage_protector):
        """Test initialization"""
        assert slippage_protector.max_slippage_bps == 50
    
    def test_check_slippage_acceptable(self, slippage_protector):
        """Test acceptable slippage check"""
        result = slippage_protector.check_slippage(
            expected_price=1.1000,
            actual_price=1.1002,
            side='BUY'
        )
        
        assert result['acceptable'] is True
        assert result['slippage_bps'] < 50
    
    def test_check_slippage_excessive(self, slippage_protector):
        """Test excessive slippage check"""
        result = slippage_protector.check_slippage(
            expected_price=1.1000,
            actual_price=1.1100,  # 100 bps slippage
            side='BUY'
        )
        
        assert result['acceptable'] is False
        assert result['slippage_bps'] > 50
    
    def test_calculate_slippage_bps(self, slippage_protector):
        """Test slippage calculation in basis points"""
        slippage = slippage_protector.calculate_slippage_bps(
            expected_price=1.1000,
            actual_price=1.1011,
            side='BUY'
        )
        
        assert slippage == pytest.approx(10, rel=0.1)  # ~10 bps
    
    def test_get_adjusted_limit_price(self, slippage_protector):
        """Test adjusted limit price calculation"""
        adjusted = slippage_protector.get_adjusted_limit_price(
            base_price=1.1000,
            side='BUY',
            buffer_bps=20
        )
        
        assert adjusted > 1.1000  # Buy should have higher limit


# ============================================================================
# TECHNICAL INDICATORS TESTS (100% Coverage)
# ============================================================================

class TestTechnicalIndicators:
    """Complete test coverage for technical indicators"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data"""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        
        # Generate realistic price data
        close = 100 + np.cumsum(np.random.randn(100) * 0.5)
        high = close + np.abs(np.random.randn(100) * 0.3)
        low = close - np.abs(np.random.randn(100) * 0.3)
        open_price = close + np.random.randn(100) * 0.2
        volume = np.random.randint(1000, 10000, 100)
        
        return pd.DataFrame({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }, index=dates)
    
    def test_calculate_sma(self, sample_data):
        """Test SMA calculation"""
        from trading_bot.analysis.technical_indicators import calculate_sma
        
        sma = calculate_sma(sample_data['close'], period=20)
        
        assert len(sma) == len(sample_data)
        assert not np.isnan(sma.iloc[-1])
    
    def test_calculate_ema(self, sample_data):
        """Test EMA calculation"""
        from trading_bot.analysis.technical_indicators import calculate_ema
        
        ema = calculate_ema(sample_data['close'], period=20)
        
        assert len(ema) == len(sample_data)
        assert not np.isnan(ema.iloc[-1])
    
    def test_calculate_rsi(self, sample_data):
        """Test RSI calculation"""
        from trading_bot.analysis.technical_indicators import calculate_rsi
        
        rsi = calculate_rsi(sample_data['close'], period=14)
        
        assert len(rsi) == len(sample_data)
        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        assert all(valid_rsi >= 0) and all(valid_rsi <= 100)
    
    def test_calculate_macd(self, sample_data):
        """Test MACD calculation"""
        from trading_bot.analysis.technical_indicators import calculate_macd
        
        macd, signal, histogram = calculate_macd(sample_data['close'])
        
        assert len(macd) == len(sample_data)
        assert len(signal) == len(sample_data)
        assert len(histogram) == len(sample_data)
    
    def test_calculate_bollinger_bands(self, sample_data):
        """Test Bollinger Bands calculation"""
        from trading_bot.analysis.technical_indicators import calculate_bollinger_bands
        
        upper, middle, lower = calculate_bollinger_bands(sample_data['close'], period=20)
        
        assert len(upper) == len(sample_data)
        # Upper should be above middle, middle above lower
        valid_idx = ~(upper.isna() | middle.isna() | lower.isna())
        assert all(upper[valid_idx] >= middle[valid_idx])
        assert all(middle[valid_idx] >= lower[valid_idx])
    
    def test_calculate_atr(self, sample_data):
        """Test ATR calculation"""
        from trading_bot.analysis.technical_indicators import calculate_atr
        
        atr = calculate_atr(sample_data['high'], sample_data['low'], sample_data['close'], period=14)
        
        assert len(atr) == len(sample_data)
        # ATR should be positive
        valid_atr = atr.dropna()
        assert all(valid_atr >= 0)
    
    def test_calculate_stochastic(self, sample_data):
        """Test Stochastic Oscillator calculation"""
        from trading_bot.analysis.technical_indicators import calculate_stochastic
        
        k, d = calculate_stochastic(
            sample_data['high'], 
            sample_data['low'], 
            sample_data['close'],
            k_period=14,
            d_period=3
        )
        
        assert len(k) == len(sample_data)
        assert len(d) == len(sample_data)


# ============================================================================
# MARKET REGIME TESTS (100% Coverage)
# ============================================================================

class TestMarketRegime:
    """Complete test coverage for market regime detection"""
    
    @pytest.fixture
    def regime_detector(self):
        """Create market regime detector instance"""
        from trading_bot.analysis.market_regime import MarketRegimeDetector
        return MarketRegimeDetector()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample price data"""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=200, freq='D')
        
        # Create trending data
        trend = np.linspace(100, 120, 200)
        noise = np.random.randn(200) * 2
        close = trend + noise
        
        return pd.DataFrame({
            'close': close,
            'high': close + np.abs(np.random.randn(200)),
            'low': close - np.abs(np.random.randn(200)),
            'volume': np.random.randint(1000, 10000, 200)
        }, index=dates)
    
    def test_detect_regime(self, regime_detector, sample_data):
        """Test regime detection"""
        regime = regime_detector.detect_regime(sample_data)
        
        assert regime in ['trending', 'ranging', 'volatile', 'quiet']
    
    def test_get_regime_confidence(self, regime_detector, sample_data):
        """Test regime confidence calculation"""
        confidence = regime_detector.get_regime_confidence(sample_data)
        
        assert 0 <= confidence <= 1
    
    def test_calculate_volatility_regime(self, regime_detector, sample_data):
        """Test volatility regime calculation"""
        vol_regime = regime_detector.calculate_volatility_regime(sample_data['close'])
        
        assert vol_regime in ['low', 'normal', 'high', 'extreme']
    
    def test_calculate_trend_strength(self, regime_detector, sample_data):
        """Test trend strength calculation"""
        strength = regime_detector.calculate_trend_strength(sample_data['close'])
        
        assert -1 <= strength <= 1


# ============================================================================
# ENSEMBLE MODELS TESTS (100% Coverage)
# ============================================================================

class TestEnsembleModels:
    """Complete test coverage for ensemble models"""
    
    @pytest.fixture
    def ensemble(self):
        """Create ensemble model instance"""
        from trading_bot.ml.ensemble_models import EnsemblePredictor
        return EnsemblePredictor()
    
    @pytest.fixture
    def sample_features(self):
        """Create sample features"""
        np.random.seed(42)
        return pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100),
            'feature4': np.random.randn(100),
            'feature5': np.random.randn(100)
        })
    
    @pytest.fixture
    def sample_targets(self):
        """Create sample targets"""
        np.random.seed(42)
        return pd.Series(np.random.choice([0, 1], 100))
    
    def test_init(self, ensemble):
        """Test initialization"""
        assert ensemble is not None
    
    def test_fit(self, ensemble, sample_features, sample_targets):
        """Test model fitting"""
        ensemble.fit(sample_features, sample_targets)
        
        assert ensemble.is_fitted is True
    
    def test_predict(self, ensemble, sample_features, sample_targets):
        """Test prediction"""
        ensemble.fit(sample_features, sample_targets)
        
        predictions = ensemble.predict(sample_features)
        
        assert len(predictions) == len(sample_features)
    
    def test_predict_proba(self, ensemble, sample_features, sample_targets):
        """Test probability prediction"""
        ensemble.fit(sample_features, sample_targets)
        
        probas = ensemble.predict_proba(sample_features)
        
        assert len(probas) == len(sample_features)
        assert all(0 <= p <= 1 for p in probas)
    
    def test_get_feature_importance(self, ensemble, sample_features, sample_targets):
        """Test feature importance"""
        ensemble.fit(sample_features, sample_targets)
        
        importance = ensemble.get_feature_importance()
        
        assert len(importance) == len(sample_features.columns)


# ============================================================================
# ONLINE LEARNING TESTS (100% Coverage)
# ============================================================================

class TestOnlineLearning:
    """Complete test coverage for online learning"""
    
    @pytest.fixture
    def online_learner(self):
        """Create online learner instance"""
        from trading_bot.ml.online_learning import OnlineLearner
        return OnlineLearner()
    
    def test_init(self, online_learner):
        """Test initialization"""
        assert online_learner is not None
    
    def test_partial_fit(self, online_learner):
        """Test partial fit"""
        X = np.random.randn(10, 5)
        y = np.random.choice([0, 1], 10)
        
        online_learner.partial_fit(X, y)
        
        assert online_learner.n_samples_seen > 0
    
    def test_predict_after_partial_fit(self, online_learner):
        """Test prediction after partial fit"""
        X = np.random.randn(10, 5)
        y = np.random.choice([0, 1], 10)
        
        online_learner.partial_fit(X, y)
        
        predictions = online_learner.predict(X)
        
        assert len(predictions) == 10
    
    def test_incremental_learning(self, online_learner):
        """Test incremental learning over multiple batches"""
        for _ in range(5):
            X = np.random.randn(10, 5)
            y = np.random.choice([0, 1], 10)
            online_learner.partial_fit(X, y)
        
        assert online_learner.n_samples_seen == 50
    
    def test_get_model_stats(self, online_learner):
        """Test getting model statistics"""
        X = np.random.randn(10, 5)
        y = np.random.choice([0, 1], 10)
        online_learner.partial_fit(X, y)
        
        stats = online_learner.get_model_stats()
        
        assert 'n_samples_seen' in stats


# ============================================================================
# HYPERPARAMETER TUNING TESTS (100% Coverage)
# ============================================================================

class TestHyperparameterTuning:
    """Complete test coverage for hyperparameter tuning"""
    
    @pytest.fixture
    def tuner(self):
        """Create hyperparameter tuner instance"""
        from trading_bot.ml.hyperparameter_tuning import HyperparameterTuner
import numpy
import pandas
return HyperparameterTuner()
    
@pytest.fixture
def sample_data(self):
        """Create sample data for tuning"""
        np.random.seed(42)
        X = np.random.randn(100, 5)
        y = np.random.choice([0, 1], 100)
        return X, y
    
def test_init(self, tuner):
        """Test initialization"""
        assert tuner is not None
    
def test_define_search_space(self, tuner):
        """Test search space definition"""
        space = tuner.define_search_space('random_forest')
        
        assert 'n_estimators' in space
        assert 'max_depth' in space
    
def test_random_search(self, tuner, sample_data):
        """Test random search"""
        X, y = sample_data
        
        best_params = tuner.random_search(
            X, y,
            model_type='random_forest',
            n_iter=5,
            cv=3
        )
        
        assert best_params is not None
        assert 'n_estimators' in best_params
    
def test_get_best_model(self, tuner, sample_data):
        """Test getting best model"""
        X, y = sample_data
        
        tuner.random_search(X, y, model_type='random_forest', n_iter=5, cv=3)
        
        best_model = tuner.get_best_model()
        
        assert best_model is not None


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
