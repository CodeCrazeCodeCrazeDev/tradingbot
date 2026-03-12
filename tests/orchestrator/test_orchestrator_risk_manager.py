"""
Comprehensive Test Suite for Portfolio Risk Manager Components
"""

import pytest
import numpy as np
from datetime import datetime


@pytest.fixture
def sample_config():
    return {
        'max_portfolio_var': 0.05,
        'max_position_risk': 0.02,
        'max_correlation': 0.7,
        'max_concentration': 0.2,
        'var_confidence': 0.95,
        'lookback_period': 252
    }


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
        'AAPL': {'price': 150.0, 'volume': 1000000, 'price_history': np.random.uniform(140, 160, 100).tolist()},
        'GOOGL': {'price': 2800.0, 'volume': 500000, 'price_history': np.random.uniform(2700, 2900, 100).tolist()},
        'MSFT': {'price': 300.0, 'volume': 800000, 'price_history': np.random.uniform(290, 310, 100).tolist()}
    }


class TestRiskManagerImport:
    def test_import_portfolio_risk_manager(self):
        from trading_bot.orchestrator.risk_manager import PortfolioRiskManager
        assert PortfolioRiskManager is not None

    def test_import_position_sizer(self):
        from trading_bot.orchestrator.risk_manager import PositionSizer
        assert PositionSizer is not None

    def test_import_hedge_calculator(self):
        from trading_bot.orchestrator.risk_manager import HedgeCalculator
        assert HedgeCalculator is not None

    def test_import_risk_metrics(self):
        from trading_bot.orchestrator.risk_manager import RiskMetrics
        assert RiskMetrics is not None

    def test_import_drawdown_controller(self):
        from trading_bot.orchestrator.risk_manager import DrawdownController
        assert DrawdownController is not None


class TestRiskManagerInit:
    def test_initialization(self, sample_config):
        manager = PortfolioRiskManager(sample_config)
        assert manager.max_portfolio_var == 0.05
        assert manager.max_position_risk == 0.02
        assert manager.max_correlation == 0.7
        assert manager.var_confidence == 0.95

    def test_default_initialization(self):
        manager = PortfolioRiskManager()
        assert manager.max_portfolio_var == 0.05
        assert manager.positions == {}


class TestRiskMetricsDataclass:
    def test_risk_metrics_creation(self):
        metrics = RiskMetrics(
            portfolio_var=0.02, portfolio_cvar=0.03, sharpe_ratio=1.5,
            sortino_ratio=2.0, max_drawdown=0.15, current_drawdown=0.05,
            beta=1.2, correlation_risk=0.5, concentration_risk=0.3,
            liquidity_risk=0.2, tail_risk=0.1, stress_test_results={'market_crash': 0.2}
        )
        assert metrics.portfolio_var == 0.02
        assert metrics.sharpe_ratio == 1.5
        assert metrics.max_drawdown == 0.15


class TestPositionWeights:
    def test_get_position_weights(self, sample_config, sample_positions):
        manager = PortfolioRiskManager(sample_config)
        manager.positions = sample_positions
        weights = manager._get_position_weights()
        assert len(weights) == len(sample_positions)
        assert np.sum(weights) == pytest.approx(1.0, rel=0.01)
        assert all(w >= 0 for w in weights)

    def test_empty_positions_weights(self, sample_config):
        manager = PortfolioRiskManager(sample_config)
        manager.positions = {}
        weights = manager._get_position_weights()
        assert len(weights) == 0


class TestConcentrationRisk:
    def test_assess_concentration_risk(self, sample_config, sample_positions):
        manager = PortfolioRiskManager(sample_config)
        manager.positions = sample_positions
        concentration = manager._assess_concentration_risk()
        assert 0 <= concentration <= 1

    def test_empty_concentration_risk(self, sample_config):
        manager = PortfolioRiskManager(sample_config)
        manager.positions = {}
        concentration = manager._assess_concentration_risk()
        assert concentration == 0


class TestLiquidityRisk:
    def test_assess_liquidity_risk(self, sample_config, sample_positions, sample_market_data):
        manager = PortfolioRiskManager(sample_config)
        manager.positions = sample_positions
        liquidity_risk = manager._assess_liquidity_risk(sample_market_data)
        assert 0 <= liquidity_risk <= 1

    def test_empty_liquidity_risk(self, sample_config, sample_market_data):
        manager = PortfolioRiskManager(sample_config)
        manager.positions = {}
        liquidity_risk = manager._assess_liquidity_risk(sample_market_data)
        assert liquidity_risk == 0.5


class TestStressTesting:
    def test_stress_test_market_crash(self, sample_config, sample_positions):
        manager = PortfolioRiskManager(sample_config)
        manager.positions = sample_positions
        loss = manager._stress_test_scenario(market_shock=-0.20, vol_shock=2.0)
        assert loss > 0
        assert loss < 1

    def test_stress_test_flash_crash(self, sample_config, sample_positions):
        manager = PortfolioRiskManager(sample_config)
        manager.positions = sample_positions
        loss = manager._stress_test_scenario(market_shock=-0.10, vol_shock=3.0)
        assert loss > 0

    def test_run_all_stress_tests(self, sample_config, sample_positions, sample_market_data):
        manager = PortfolioRiskManager(sample_config)
        manager.positions = sample_positions
        results = manager._run_stress_tests(sample_market_data)
        assert 'market_crash' in results
        assert 'flash_crash' in results
        assert 'rate_shock' in results
        assert 'liquidity_crisis' in results
        assert 'correlation_breakdown' in results


class TestTradeValidation:
    def test_validate_valid_trade(self, sample_config, sample_positions):
        manager = PortfolioRiskManager(sample_config)
        manager.positions = sample_positions
        valid, msg = manager.validate_trade({'symbol': 'AAPL', 'risk': 0.01, 'size': 1000})
        assert valid == True

    def test_validate_high_risk_trade(self, sample_config, sample_positions):
        manager = PortfolioRiskManager(sample_config)
        manager.positions = sample_positions
        valid, msg = manager.validate_trade({'symbol': 'AAPL', 'risk': 0.5, 'size': 50000})
        assert valid == False


class TestPortfolioRiskAssessment:
    def test_assess_portfolio_risk(self, sample_config, sample_positions, sample_market_data):
        manager = PortfolioRiskManager(sample_config)
        metrics = manager.assess_portfolio_risk(sample_positions, sample_market_data)
        assert metrics is not None
        assert hasattr(metrics, 'portfolio_var')
        assert hasattr(metrics, 'sharpe_ratio')
        assert hasattr(metrics, 'max_drawdown')


class TestPositionSizer:
    def test_initialization(self):
        sizer = PositionSizer()
        assert 'kelly' in sizer.methods
        assert 'fixed_fractional' in sizer.methods
        assert 'optimal_f' in sizer.methods
        assert 'risk_parity' in sizer.methods

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

    def test_calculate_position_size_kelly(self):
        sizer = PositionSizer()
        opportunity = {'success_probability': 0.6, 'expected_return': 0.03, 'risk': 0.02}
        portfolio = {'available_capital': 100000}
        size = sizer.calculate_position_size(opportunity, portfolio, 'kelly')
        assert size > 0


class TestHedgeCalculator:
    def test_initialization(self):
        calculator = HedgeCalculator()
        assert 'VIX' in calculator.hedge_instruments
        assert 'PUT_OPTIONS' in calculator.hedge_instruments
        assert 'GOLD' in calculator.hedge_instruments

    def test_calculate_tail_hedge(self, sample_positions):
        calculator = HedgeCalculator()
        hedge = calculator._calculate_tail_hedge(sample_positions)
        assert hedge['instrument'] == 'PUT_OPTIONS'
        assert hedge['size'] > 0

    def test_calculate_correlation_hedge(self, sample_positions):
        calculator = HedgeCalculator()
        hedge = calculator._calculate_correlation_hedge(sample_positions)
        assert hedge['instrument'] == 'VIX'
        assert hedge['size'] > 0

    def test_calculate_drawdown_hedge(self, sample_positions):
        calculator = HedgeCalculator()
        hedge = calculator._calculate_drawdown_hedge(sample_positions)
        assert hedge['instrument'] == 'INVERSE_ETF'
        assert hedge['size'] > 0


class TestDrawdownController:
    def test_initialization(self):
        controller = DrawdownController()
        assert controller.max_drawdown == 0.20
        assert controller.equity_peak == 100000
        assert len(controller.drawdown_levels) == 4

    def test_check_drawdown_normal(self):
        controller = DrawdownController()
        controller.equity_peak = 100000
        action, recommendations = controller.check_drawdown(98000)
        assert action == 'normal'
        assert recommendations['new_trades_allowed'] == True
        assert recommendations['position_adjustment'] == 1.0

    def test_check_drawdown_warning(self):
        controller = DrawdownController()
        controller.equity_peak = 100000
        action, recommendations = controller.check_drawdown(94000)
        assert action == 'warning'
        assert recommendations['position_adjustment'] == 0.9

    def test_check_drawdown_reduce(self):
        controller = DrawdownController()
        controller.equity_peak = 100000
        action, recommendations = controller.check_drawdown(88000)
        assert action == 'reduce'
        assert recommendations['position_adjustment'] == 0.7
        assert recommendations['hedge_required'] == True

    def test_check_drawdown_defensive(self):
        controller = DrawdownController()
        controller.equity_peak = 100000
        action, recommendations = controller.check_drawdown(83000)
        assert action == 'defensive'
        assert recommendations['position_adjustment'] == 0.5
        assert recommendations['new_trades_allowed'] == False

    def test_check_drawdown_stop(self):
        controller = DrawdownController()
        controller.equity_peak = 100000
        action, recommendations = controller.check_drawdown(78000)
        assert action == 'stop'
        assert recommendations['position_adjustment'] == 0.2
        assert recommendations['emergency_exit'] == True

    def test_peak_update(self):
        controller = DrawdownController()
        controller.equity_peak = 100000
        controller.check_drawdown(105000)
        assert controller.equity_peak == 105000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
