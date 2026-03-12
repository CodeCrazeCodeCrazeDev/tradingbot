"""
Standalone Orchestrator Tests - Direct imports without main package
"""

import sys
import os

# Add the trading_bot directory to path for direct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
import asyncio
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_config():
    return {
        'capital': 100000,
        'max_risk_per_trade': 0.02,
        'max_portfolio_risk': 0.06,
        'max_correlation': 0.7,
        'max_slippage': 0.002,
        'urgency_threshold': 0.7,
        'chunk_size': 1000,
        'var_confidence': 0.95,
        'lookback_period': 252
    }


@pytest.fixture
def sample_opportunities():
    return [
        {'type': 'MOMENTUM', 'symbol': 'AAPL', 'confidence': 0.75, 'expected_return': 0.03, 'risk': 0.4, 'direction': 'BUY'},
        {'type': 'ARBITRAGE', 'symbol': 'GOOGL', 'confidence': 0.85, 'expected_return': 0.01, 'risk': 0.2, 'direction': 'BUY'},
        {'type': 'NEWS', 'symbol': 'MSFT', 'confidence': 0.65, 'expected_return': 0.02, 'risk': 0.5, 'direction': 'SELL'}
    ]


@pytest.fixture
def sample_positions():
    return {
        'AAPL': {'value': 15000, 'quantity': 100, 'entry_price': 150},
        'GOOGL': {'value': 28000, 'quantity': 10, 'entry_price': 2800},
        'MSFT': {'value': 9000, 'quantity': 30, 'entry_price': 300}
    }


@pytest.fixture
def sample_market_data():
    return {
        'AAPL': {'price': 150.0, 'volume': 1000000, 'volatility': 0.25,
                 'price_history': np.random.uniform(140, 160, 100).tolist()},
        'GOOGL': {'price': 2800.0, 'volume': 500000, 'volatility': 0.30,
                  'price_history': np.random.uniform(2700, 2900, 100).tolist()},
        'MSFT': {'price': 300.0, 'volume': 800000, 'volatility': 0.22,
                 'price_history': np.random.uniform(290, 310, 100).tolist()}
    }


@pytest.fixture
def sample_trades():
    trades = []
    for i in range(50):
        pnl = np.random.normal(100, 500)
        trades.append({
            'trade_id': f'TRADE_{i}',
            'timestamp': datetime.now() - timedelta(hours=i),
            'symbol': np.random.choice(['AAPL', 'GOOGL', 'MSFT']),
            'pnl': pnl,
            'strategy': np.random.choice(['momentum', 'arbitrage', 'news']),
            'opportunity_type': np.random.choice(['MOMENTUM', 'ARBITRAGE', 'NEWS']),
            'success': pnl > 0
        })
    return trades


# ============================================================================
# MASTER ORCHESTRATOR TESTS
# ============================================================================

class TestMasterOrchestrator:
    """Tests for MasterOrchestrator"""

    def test_import(self):
        from trading_bot.orchestrator.master_orchestrator import MasterOrchestrator
        assert MasterOrchestrator is not None

    def test_trading_mode_import(self):
        from trading_bot.orchestrator.master_orchestrator import TradingMode
        assert TradingMode.BALANCED.value == "balanced"
        assert TradingMode.AGGRESSIVE.value == "aggressive"

    def test_initialization(self, sample_config):
        from trading_bot.orchestrator.master_orchestrator import MasterOrchestrator, TradingMode
        orchestrator = MasterOrchestrator(sample_config)
        assert orchestrator.total_capital == 100000
        assert orchestrator.max_risk_per_trade == 0.02
        assert orchestrator.trading_mode == TradingMode.BALANCED

    def test_filter_by_mode(self, sample_config, sample_opportunities):
        orchestrator = MasterOrchestrator(sample_config)
        orchestrator.trading_mode = TradingMode.BALANCED
        filtered = orchestrator._filter_by_mode_and_risk(sample_opportunities)
        assert len(filtered) == 3

    def test_kelly_fraction(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        kelly = orchestrator._calculate_kelly_fraction(0.05, 0.02, 0.7)
        assert 0 <= kelly <= 0.25

    def test_determine_action(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        assert orchestrator._determine_action({'direction': 'BUY'}) == 'BUY'
        assert orchestrator._determine_action({'direction': 'SELL'}) == 'SELL'

    def test_extract_symbols(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        assert orchestrator._extract_symbols({'symbol': 'AAPL'}) == ['AAPL']
        assert orchestrator._extract_symbols({'symbols': ['AAPL', 'GOOGL']}) == ['AAPL', 'GOOGL']

    def test_adjust_trading_mode(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        orchestrator.adjust_trading_mode({'volatility': 0.5, 'trend_strength': 0.5, 'volume': 'normal'})
        assert orchestrator.trading_mode == TradingMode.DEFENSIVE

    def test_performance_summary(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        summary = orchestrator.get_performance_summary()
        assert 'win_rate' in summary
        assert 'total_capital' in summary


# ============================================================================
# EXECUTION ENGINE TESTS
# ============================================================================

class TestExecutionEngine:
    """Tests for ExecutionEngine"""

    def test_import(self):
        from trading_bot.orchestrator.execution_engine import ExecutionEngine
        assert ExecutionEngine is not None

    def test_order_type_import(self):
        from trading_bot.orchestrator.execution_engine import OrderType
        assert OrderType.MARKET.value == "market"
        assert OrderType.LIMIT.value == "limit"

    def test_initialization(self, sample_config):
        engine = ExecutionEngine(sample_config)
        assert engine.max_slippage == 0.002
        assert len(engine.algorithms) == 8

    def test_algorithm_selection(self, sample_config):
        from trading_bot.orchestrator.execution_engine import ExecutionEngine, ExecutionAlgorithm
        engine = ExecutionEngine(sample_config)
        params = {'urgency': 0.9, 'quantity': 500}
        algo = engine._select_algorithm(params)
        assert algo == ExecutionAlgorithm.SNIPER

    def test_slippage_calculation(self, sample_config):
        engine = ExecutionEngine(sample_config)
        slippage = engine._calculate_slippage(100.0, 100.5)
        assert slippage == pytest.approx(0.005, rel=0.01)

    def test_guerrilla_chunks(self, sample_config):
        engine = ExecutionEngine(sample_config)
        chunks = engine._create_guerrilla_chunks(10000)
        assert len(chunks) > 0
        assert sum(chunks) == pytest.approx(10000, rel=0.01)


# ============================================================================
# ML PREDICTOR TESTS
# ============================================================================

class TestMLPredictor:
    """Tests for ML Predictor"""

    def test_import(self):
        from trading_bot.orchestrator.ml_predictor import OpportunityPredictor
        assert OpportunityPredictor is not None

    def test_initialization(self, sample_config):
        predictor = OpportunityPredictor(sample_config)
        assert predictor.lookback_window == 100
        assert 'success_classifier' in predictor.models

    def test_feature_extractor(self, sample_opportunities):
        from trading_bot.orchestrator.ml_predictor import MLFeatureExtractor
        extractor = MLFeatureExtractor()
        features = extractor.extract_features(sample_opportunities[0])
        assert isinstance(features, np.ndarray)
        assert len(features) == 20

    def test_heuristic_success_probability(self, sample_config):
        predictor = OpportunityPredictor(sample_config)
        prob = predictor._heuristic_success_probability({'type': 'ARBITRAGE', 'confidence': 0.8})
        assert 0 <= prob <= 0.95

    @pytest.mark.asyncio
    async def test_predict_batch(self, sample_config, sample_opportunities):
        predictor = OpportunityPredictor(sample_config)
        predictions = await predictor.predict_batch(sample_opportunities)
        assert len(predictions) == len(sample_opportunities)


# ============================================================================
# RISK MANAGER TESTS
# ============================================================================

class TestRiskManager:
    """Tests for Risk Manager"""

    def test_import(self):
        from trading_bot.orchestrator.risk_manager import PortfolioRiskManager
        assert PortfolioRiskManager is not None

    def test_initialization(self, sample_config):
        manager = PortfolioRiskManager(sample_config)
        assert manager.max_portfolio_var == 0.05
        assert manager.var_confidence == 0.95

    def test_position_weights(self, sample_config, sample_positions):
        manager = PortfolioRiskManager(sample_config)
        manager.positions = sample_positions
        weights = manager._get_position_weights()
        assert len(weights) == len(sample_positions)
        assert np.sum(weights) == pytest.approx(1.0, rel=0.01)

    def test_concentration_risk(self, sample_config, sample_positions):
        manager = PortfolioRiskManager(sample_config)
        manager.positions = sample_positions
        concentration = manager._assess_concentration_risk()
        assert 0 <= concentration <= 1

    def test_stress_test(self, sample_config, sample_positions):
        manager = PortfolioRiskManager(sample_config)
        manager.positions = sample_positions
        loss = manager._stress_test_scenario(market_shock=-0.20, vol_shock=2.0)
        assert loss > 0
        assert loss < 1

    def test_validate_trade(self, sample_config, sample_positions):
        manager = PortfolioRiskManager(sample_config)
        manager.positions = sample_positions
        valid, msg = manager.validate_trade({'symbol': 'AAPL', 'risk': 0.01, 'size': 1000})
        assert valid == True


# ============================================================================
# POSITION SIZER TESTS
# ============================================================================

class TestPositionSizer:
    """Tests for Position Sizer"""

    def test_import(self):
        from trading_bot.orchestrator.risk_manager import PositionSizer
        assert PositionSizer is not None

    def test_kelly_criterion(self):
        sizer = PositionSizer()
        opportunity = {'success_probability': 0.6, 'expected_return': 0.03, 'risk': 0.02}
        portfolio = {'available_capital': 100000}
        size = sizer._kelly_criterion(opportunity, portfolio)
        assert size > 0
        assert size <= 100000 * 0.25

    def test_fixed_fractional(self):
        sizer = PositionSizer()
        opportunity = {'stop_loss_percent': 0.05}
        portfolio = {'available_capital': 100000}
        size = sizer._fixed_fractional(opportunity, portfolio)
        expected = (100000 * 0.02) / 0.05
        assert size == pytest.approx(expected, rel=0.01)

    def test_risk_parity(self):
        sizer = PositionSizer()
        high_vol = {'volatility': 0.4}
        low_vol = {'volatility': 0.1}
        portfolio = {'available_capital': 100000}
        high_vol_size = sizer._risk_parity(high_vol, portfolio)
        low_vol_size = sizer._risk_parity(low_vol, portfolio)
        assert low_vol_size > high_vol_size


# ============================================================================
# DRAWDOWN CONTROLLER TESTS
# ============================================================================

class TestDrawdownController:
    """Tests for Drawdown Controller"""

    def test_import(self):
        from trading_bot.orchestrator.risk_manager import DrawdownController
        assert DrawdownController is not None

    def test_normal_drawdown(self):
        controller = DrawdownController()
        controller.equity_peak = 100000
        action, recommendations = controller.check_drawdown(98000)
        assert action == 'normal'
        assert recommendations['new_trades_allowed'] == True

    def test_warning_drawdown(self):
        controller = DrawdownController()
        controller.equity_peak = 100000
        action, recommendations = controller.check_drawdown(94000)
        assert action == 'warning'

    def test_stop_drawdown(self):
        controller = DrawdownController()
        controller.equity_peak = 100000
        action, recommendations = controller.check_drawdown(78000)
        assert action == 'stop'
        assert recommendations['emergency_exit'] == True


# ============================================================================
# PERFORMANCE TRACKER TESTS
# ============================================================================

class TestPerformanceTracker:
    """Tests for Performance Tracker"""

    def test_import(self):
        from trading_bot.orchestrator.performance_tracker import PerformanceTracker
        assert PerformanceTracker is not None

    def test_initialization(self, sample_config):
        tracker = PerformanceTracker(sample_config)
        assert len(tracker.trade_history) == 0
        assert len(tracker.equity_curve) == 0

    def test_track_trade(self, sample_config, sample_trades):
        tracker = PerformanceTracker(sample_config)
        for trade in sample_trades[:10]:
    pass
            tracker.track_trade(trade)
        assert len(tracker.trade_history) == 10
        assert len(tracker.equity_curve) == 10

    def test_equity_curve_update(self, sample_config):
        tracker = PerformanceTracker(sample_config)
        tracker._update_equity_curve({'pnl': 500})
        assert tracker.equity_curve[-1] == 100500


# ============================================================================
# METRICS CALCULATOR TESTS
# ============================================================================

class TestMetricsCalculator:
    """Tests for Metrics Calculator"""

    def test_import(self):
        from trading_bot.orchestrator.performance_tracker import MetricsCalculator
        assert MetricsCalculator is not None

    def test_empty_metrics(self):
        calculator = MetricsCalculator()
        metrics = calculator.calculate_metrics([], [], [])
        assert metrics.total_trades == 0
        assert metrics.win_rate == 0

    def test_sharpe_ratio(self):
        calculator = MetricsCalculator()
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        sharpe = calculator._calculate_sharpe_ratio(returns)
        assert sharpe > 0

    def test_max_drawdown(self):
        calculator = MetricsCalculator()
        equity_curve = [100, 110, 105, 115, 100]
        max_dd = calculator._calculate_max_drawdown(equity_curve)
        assert max_dd == pytest.approx(0.13, rel=0.01)


# ============================================================================
# AUTO OPTIMIZER TESTS
# ============================================================================

class TestAutoOptimizer:
    """Tests for Auto Optimizer"""

    def test_import(self):
        from trading_bot.orchestrator.performance_tracker import AutoOptimizer
        assert AutoOptimizer is not None

    def test_analyze_performance(self, sample_trades):
        optimizer = AutoOptimizer()
        performance = optimizer._analyze_performance(sample_trades)
        assert 'win_rate' in performance
        assert 'by_type' in performance

    def test_generate_suggestions(self):
        optimizer = AutoOptimizer()
        performance = {
            'win_rate': 0.4, 'avg_win': 100, 'avg_loss': 150,
            'by_type': {'MOMENTUM': {'win_rate': 0.3, 'wins': 3, 'total': 10}},
            'by_time': {10: {'wins': 2, 'total': 10}}
        }
        suggestions = optimizer._generate_suggestions(performance)
        assert 'reduce_size' in suggestions['position_sizing']


# ============================================================================
# SMART ORDER ROUTER TESTS
# ============================================================================

class TestSmartOrderRouter:
    """Tests for Smart Order Router"""

    def test_import(self):
        from trading_bot.orchestrator.execution_engine import SmartOrderRouter
        assert SmartOrderRouter is not None

    def test_initialization(self):
        router = SmartOrderRouter()
        assert router.routing_cache == {}

    @pytest.mark.asyncio
    async def test_score_venues(self):
    pass
import numpy
        router = SmartOrderRouter()
        venues = {
            'exchange1': {'fee_rate': 0.001, 'latency': 5, 'liquidity': 10000, 'fill_rate': 0.98},
            'exchange2': {'fee_rate': 0.002, 'latency': 10, 'liquidity': 5000, 'fill_rate': 0.95}
        }
        scores = await router._score_venues('AAPL', 1000, venues)
        assert scores['exchange1'] > scores['exchange2']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
