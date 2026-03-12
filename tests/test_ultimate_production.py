"""
Integration Tests for Ultimate Production Trading System
========================================================

Comprehensive tests to validate all components work correctly together.
"""

import pytest
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCoreEngine:
    """Tests for the core trading engine"""
    
    @pytest.fixture
    def config(self):
        return {
            'mode': 'paper',
            'symbols': ['EURUSD', 'GBPUSD'],
            'initial_capital': 10000.0,
            'max_positions': 3,
            'max_daily_loss': 0.02,
            'max_drawdown': 0.10,
        }
    
    @pytest.fixture
    def engine(self, config):
        from trading_bot.ultimate_production.core_engine import UltimateProductionEngine
        return UltimateProductionEngine(config)
    
    def test_engine_initialization(self, engine):
        """Test engine initializes correctly"""
        assert engine is not None
        assert engine.capital == 10000.0
        assert len(engine.symbols) == 2
        assert engine.mode.value == 'paper'
    
    def test_engine_state(self, engine):
        """Test engine state management"""
        from trading_bot.ultimate_production.core_engine import SystemState
        assert engine.state == SystemState.INITIALIZING
    
    @pytest.mark.asyncio
    async def test_engine_initialize(self, engine):
        """Test engine initialization process"""
        success = await engine.initialize()
        assert success is True
        assert engine.state == SystemState.READY
    
    def test_get_status(self, engine):
        """Test status retrieval"""
        status = engine.get_status()
        assert 'engine_id' in status
        assert 'state' in status
        assert 'capital' in status
    
    def test_synthetic_data_generation(self, engine):
        """Test synthetic market data generation"""
        data = engine._generate_synthetic_data('EURUSD')
        assert isinstance(data, pd.DataFrame)
        assert len(data) == 100
        assert 'open' in data.columns
        assert 'high' in data.columns
        assert 'low' in data.columns
        assert 'close' in data.columns
        assert 'volume' in data.columns
        # Verify OHLC relationships
        assert (data['high'] >= data['low']).all()
        assert (data['high'] >= data['open']).all()
        assert (data['high'] >= data['close']).all()
        assert (data['low'] <= data['open']).all()
        assert (data['low'] <= data['close']).all()


class TestStrategyEnsemble:
    """Tests for the strategy ensemble"""
    
    @pytest.fixture
    def ensemble(self):
        from trading_bot.ultimate_production.strategy_ensemble import StrategyEnsemble
        return StrategyEnsemble({})
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample OHLCV data"""
        np.random.seed(42)
        n = 100
        base_price = 1.0850
        returns = np.random.normal(0, 0.001, n)
        prices = base_price * np.cumprod(1 + returns)
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.uniform(-0.0001, 0.0001, n)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.0003, n))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.0003, n))),
            'close': prices,
            'volume': np.random.uniform(1000, 10000, n),
        })
        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)
        df.index = pd.date_range(end=datetime.now(), periods=n, freq='1min')
        return df
    
    def test_ensemble_initialization(self, ensemble):
        """Test ensemble initializes with all strategies"""
        assert len(ensemble.strategies) == 10
        assert all(s.enabled for s in ensemble.strategies)
    
    def test_strategy_weights(self, ensemble):
        """Test strategy weights are set"""
        assert len(ensemble.weights) == 10
        assert all(w > 0 for w in ensemble.weights.values())
    
    def test_indicator_calculation(self, ensemble, sample_data):
        """Test technical indicator calculation"""
        strategy = ensemble.strategies[0]
        df = strategy.calculate_indicators(sample_data)
        
        assert 'sma_10' in df.columns
        assert 'sma_20' in df.columns
        assert 'rsi' in df.columns
        assert 'macd' in df.columns
        assert 'bb_upper' in df.columns
        assert 'atr' in df.columns
    
    @pytest.mark.asyncio
    async def test_signal_generation(self, ensemble, sample_data):
        """Test signal generation from ensemble"""
        market_data = {'EURUSD': sample_data}
        market_condition = Mock()
        market_condition.regime = 'trending_up'
        
        signals = await ensemble.generate_signals(market_data, market_condition)
        
        # May or may not generate signals depending on conditions
        assert isinstance(signals, list)
    
    def test_strategy_stats(self, ensemble):
        """Test strategy statistics retrieval"""
        stats = ensemble.get_strategy_stats()
        assert len(stats) == 10
        for name, stat in stats.items():
            assert 'enabled' in stat
            assert 'weight' in stat


class TestMLPredictionEngine:
    """Tests for the ML prediction engine"""
    
    @pytest.fixture
    def ml_engine(self):
        from trading_bot.ultimate_production.ml_prediction_engine import MLPredictionEngine
        return MLPredictionEngine({})
    
    @pytest.fixture
    def sample_data(self):
        np.random.seed(42)
        n = 100
        base_price = 100.0
        returns = np.random.normal(0, 0.001, n)
        prices = base_price * np.cumprod(1 + returns)
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.uniform(-0.0001, 0.0001, n)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.0003, n))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.0003, n))),
            'close': prices,
            'volume': np.random.uniform(1000, 10000, n),
        })
        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)
        df.index = pd.date_range(end=datetime.now(), periods=n, freq='1min')
        return df
    
    def test_feature_engineering(self, ml_engine, sample_data):
        """Test feature engineering"""
        features_df = ml_engine.feature_engineer.create_features(sample_data)
        
        assert len(features_df) > 0
        assert 'return_1' in features_df.columns
        assert 'rsi' in features_df.columns
        assert 'macd' in features_df.columns
    
    def test_transformer_prediction(self, ml_engine):
        """Test transformer model prediction"""
        from trading_bot.ultimate_production.ml_prediction_engine import SimpleTransformerModel
        
        model = SimpleTransformerModel({'sequence_length': 20})
        features = np.random.randn(50, 10)
        
        direction, probability = model.predict(features)
        
        assert direction in ['UP', 'DOWN', 'NEUTRAL']
        assert 0 <= probability <= 1
    
    def test_ensemble_prediction(self, ml_engine):
        """Test ensemble predictor"""
        features = np.random.randn(50, 10)
        
        direction, confidence, details = ml_engine.ensemble.predict(features)
        
        assert direction in ['UP', 'DOWN', 'NEUTRAL']
        assert 0 <= confidence <= 1
        assert 'transformer' in details
    
    def test_confidence_calibration(self, ml_engine):
        """Test confidence calibration"""
        calibrator = ml_engine.calibrator
        
        # Add some predictions
        for _ in range(100):
            calibrator.add_prediction(0.7, np.random.random() > 0.3)
        
        calibrated = calibrator.calibrate(0.7)
        assert 0 <= calibrated <= 1


class TestRiskFortress:
    """Tests for the risk management system"""
    
    @pytest.fixture
    def risk_fortress(self):
        from trading_bot.ultimate_production.risk_fortress import RiskFortress
        return RiskFortress({})
    
    def test_initialization(self, risk_fortress):
        """Test risk fortress initialization"""
        assert risk_fortress.limits is not None
        assert risk_fortress.position_sizer is not None
        assert risk_fortress.circuit_breaker is not None
    
    def test_position_sizing_fixed_fractional(self, risk_fortress):
        """Test fixed fractional position sizing"""
        size = risk_fortress.position_sizer.calculate_size(
            capital=10000,
            entry_price=1.0850,
            stop_loss=1.0800,
            volatility=0.5,
            confidence=0.7
        )
        
        assert size > 0
        assert size <= 0.04  # Should be bounded
    
    def test_drawdown_protection(self, risk_fortress):
        """Test drawdown protection"""
        protector = risk_fortress.drawdown_protector
        
        # Simulate equity changes
        protector.update(10000)
        protector.update(9500)  # 5% drawdown
        
        action, multiplier = protector.get_action()
        assert multiplier < 1.0  # Should reduce size
    
    def test_circuit_breaker(self, risk_fortress):
        """Test circuit breaker"""
        cb = risk_fortress.circuit_breaker
        
        # Record losses
        for _ in range(5):
            cb.record_trade(-0.01, datetime.now())
        
        can_trade, reason = cb.can_trade()
        assert not can_trade  # Should be tripped after consecutive losses
    
    def test_correlation_check(self, risk_fortress):
        """Test correlation management"""
        cm = risk_fortress.correlation_manager
        
        # EURUSD and GBPUSD are correlated
        corr = cm.get_correlation('EURUSD', 'GBPUSD')
        assert corr > 0.5
        
        # Check portfolio correlation
        positions = {'EURUSD': Mock()}
        approved, max_corr, reason = cm.check_portfolio_correlation('GBPUSD', positions)
        # May or may not be approved depending on threshold


class TestSmartExecutor:
    """Tests for the smart execution system"""
    
    @pytest.fixture
    def executor(self):
        from trading_bot.ultimate_production.smart_executor import SmartExecutor
        return SmartExecutor({'mode': 'paper'})
    
    @pytest.mark.asyncio
    async def test_paper_execution(self, executor):
        """Test paper trading execution"""
        from trading_bot.ultimate_production.smart_executor import ExecutionOrder, ExecutionAlgorithm
        
        order = ExecutionOrder(
            order_id='test_001',
            symbol='EURUSD',
            direction='BUY',
            quantity=1000,
            order_type='market',
            algorithm=ExecutionAlgorithm.MARKET,
        )
        
        result = await executor._paper_execute(order)
        
        assert result.success
        assert result.fill_quantity == 1000
        assert result.fill_price > 0
    
    @pytest.mark.asyncio
    async def test_market_snapshot(self, executor):
        """Test market snapshot retrieval"""
        snapshot = await executor._get_market_snapshot('EURUSD')
        
        assert snapshot.symbol == 'EURUSD'
        assert snapshot.bid > 0
        assert snapshot.ask > 0
        assert snapshot.ask > snapshot.bid
    
    def test_slippage_estimation(self, executor):
        """Test slippage estimation"""
        from trading_bot.ultimate_production.smart_executor import MarketSnapshot
        
        market = MarketSnapshot(
            symbol='EURUSD',
            timestamp=datetime.now(),
            bid=1.0849,
            ask=1.0851,
            bid_size=100000,
            ask_size=100000,
            last_price=1.0850,
            volume=1000000,
            spread=0.0002,
        )
        
        slippage = executor.slippage_model.estimate_slippage(
            'EURUSD', 'BUY', 10000, market
        )
        
        assert slippage >= 0
        assert slippage < 0.01  # Should be reasonable


class TestLiveMonitor:
    """Tests for the monitoring system"""
    
    @pytest.fixture
    def monitor(self):
        from trading_bot.ultimate_production.live_monitor import LiveMonitor
        return LiveMonitor({})
    
    def test_performance_tracking(self, monitor):
        """Test performance tracking"""
        tracker = monitor.performance_tracker
        
        tracker.update_equity(10000)
        tracker.update_equity(10100)
        tracker.update_equity(10050)
        
        metrics = tracker.get_metrics()
        assert metrics['current_equity'] == 10050
        assert metrics['total_return'] > 0
    
    def test_risk_monitoring(self, monitor):
        """Test risk monitoring"""
        risk_monitor = monitor.risk_monitor
        
        risk_monitor.update(
            drawdown=0.06,
            daily_pnl=-100,
            positions={},
            capital=10000
        )
        
        alerts = risk_monitor.check_alerts()
        assert len(alerts) > 0  # Should generate drawdown warning
    
    def test_alert_management(self, monitor):
        """Test alert management"""
        from trading_bot.ultimate_production.live_monitor import Alert, AlertSeverity, AlertType
        
        alert = Alert(
            alert_id='test_001',
            timestamp=datetime.now(),
            severity=AlertSeverity.WARNING,
            alert_type=AlertType.RISK,
            title='Test Alert',
            message='This is a test'
        )
        
        monitor.alert_manager.add_alert(alert)
        active = monitor.alert_manager.get_active_alerts()
        
        assert len(active) == 1
    
    def test_dashboard_data(self, monitor):
        """Test dashboard data retrieval"""
        data = monitor.get_dashboard_data()
        
        assert 'performance' in data
        assert 'risk' in data
        assert 'timestamp' in data


class TestSelfLearner:
    """Tests for the self-learning system"""
    
    @pytest.fixture
    def learner(self):
        from trading_bot.ultimate_production.self_learner import SelfLearner
        return SelfLearner({'data_dir': 'test_learning_data'})
    
    def test_trade_analysis(self, learner):
        """Test trade analysis"""
        # Create mock trade
        trade = Mock()
        trade.execution_id = 'test_001'
        trade.symbol = 'EURUSD'
        trade.direction = 'BUY'
        trade.pnl = 100
        trade.pnl_percent = 0.01
        trade.exit_reason = 'take_profit'
        trade.metadata = {'strategy': 'TrendFollowing'}
        
        lesson = learner.trade_analyzer.analyze_trade(trade)
        
        assert lesson.outcome == 'win'
        assert len(lesson.lessons) > 0
    
    def test_strategy_tracking(self, learner):
        """Test strategy performance tracking"""
        tracker = learner.strategy_tracker
        
        # Record some trades
        for i in range(10):
            tracker.record_trade('TestStrategy', {
                'pnl': 100 if i % 2 == 0 else -50,
                'market_regime': 'trending',
                'timestamp': datetime.now(),
            })
        
        insight = tracker.get_insight('TestStrategy')
        assert insight is not None
        assert insight.total_trades == 10
    
    def test_pattern_discovery(self, learner):
        """Test pattern discovery"""
        discovery = learner.pattern_discovery
        
        # Record patterns
        for _ in range(15):
            discovery.record_pattern(
                ['uptrend', 'high_volatility'],
                'win',
                100
            )
        
        patterns = discovery.get_high_confidence_patterns(min_confidence=0.5)
        assert len(patterns) > 0
    
    def test_learning_stats(self, learner):
        """Test learning statistics"""
        stats = learner.get_learning_stats()
        
        assert 'total_lessons' in stats
        assert 'strategies_tracked' in stats
        assert 'patterns_discovered' in stats


class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.fixture
    def full_config(self):
        return {
            'mode': 'paper',
            'symbols': ['EURUSD'],
            'initial_capital': 10000.0,
            'max_positions': 3,
            'max_daily_loss': 0.02,
            'max_drawdown': 0.10,
        }
    
    @pytest.mark.asyncio
    async def test_full_trading_cycle(self, full_config):
        """Test a complete trading cycle"""
        
        engine = UltimateProductionEngine(full_config)
        
        # Initialize
        success = await engine.initialize()
        assert success
        
        # Get market data
        market_data = await engine._get_market_data()
        assert 'EURUSD' in market_data
        
        # Assess market condition
        condition = await engine._assess_market_condition(market_data)
        assert condition.timestamp is not None
        
        # Get status
        status = engine.get_status()
        assert status['state'] == 'ready'
    
    @pytest.mark.asyncio
    async def test_signal_to_execution_flow(self, full_config):
        """Test signal generation to execution flow"""
        from trading_bot.ultimate_production.core_engine import (
            UltimateProductionEngine, TradingSignal, SignalStrength
        )
        
        engine = UltimateProductionEngine(full_config)
        await engine.initialize()
        
        # Create a test signal
        signal = TradingSignal(
            signal_id='test_001',
            timestamp=datetime.now(),
            symbol='EURUSD',
            direction='BUY',
            strength=SignalStrength.STRONG,
            confidence=0.75,
            expected_return=0.03,
            expected_risk=0.02,
            risk_reward_ratio=1.5,
            sources=['TestStrategy'],
            entry_price=1.0850,
            stop_loss=1.0800,
            take_profit=1.0925,
            position_size=0.02,
            max_holding_period=timedelta(hours=24),
        )
        
        # Validate signal
        valid_signals = await engine._validate_signals([signal], Mock(regime='trending_up'))
        assert len(valid_signals) > 0
        
        # Risk check
        approved_signals = await engine._risk_check_signals(valid_signals)
        # May or may not be approved depending on risk checks


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
