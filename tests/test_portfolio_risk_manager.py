"""Unit tests for portfolio risk manager."""

import pytest
import numpy as np
from datetime import datetime, timedelta
from trading_bot.risk.portfolio_risk_manager import PortfolioRiskManager, RiskMetrics


class TestPortfolioRiskManager:
    """Test PortfolioRiskManager class."""
    
    @pytest.fixture
    def manager(self):
        """Create manager instance."""
        config = {
            'max_var': 0.05,
            'max_cvar': 0.08,
            'max_drawdown': 0.15,
            'max_correlation_risk': 0.10,
            'max_sector_exposure': 0.25
        }
        return PortfolioRiskManager(config)
    
    def test_manager_initialization(self, manager):
        """Test manager initializes correctly."""
        assert manager.max_var == 0.05
        assert manager.max_cvar == 0.08
        assert len(manager.positions) == 0
    
    def test_add_position(self, manager):
        """Test adding a position."""
        manager.add_position('pos1', 'EURUSD', 1.0, 1.1000, 'forex')
        assert 'pos1' in manager.positions
        assert manager.positions['pos1']['symbol'] == 'EURUSD'
    
    def test_remove_position(self, manager):
        """Test removing a position."""
        manager.add_position('pos1', 'EURUSD', 1.0, 1.1000, 'forex')
        manager.remove_position('pos1')
        assert 'pos1' not in manager.positions
    
    def test_update_position_price(self, manager):
        """Test updating position price."""
        manager.add_position('pos1', 'EURUSD', 1.0, 1.1000, 'forex')
        manager.update_position_price('pos1', 1.1050)
        assert manager.positions['pos1']['current_price'] == 1.1050
        assert abs(manager.positions['pos1']['pnl'] - 0.0050) < 1e-10  # Float comparison
    
    def test_update_equity(self, manager):
        """Test updating equity."""
        manager.update_equity(10000.0)
        assert manager.current_equity == 10000.0
        assert manager.peak_equity == 10000.0
    
    def test_peak_equity_tracking(self, manager):
        """Test peak equity tracking."""
        manager.update_equity(10000.0)
        manager.update_equity(11000.0)
        manager.update_equity(10500.0)
        assert manager.peak_equity == 11000.0
    
    def test_calculate_var_cvar(self, manager):
        """Test VaR and CVaR calculation."""
        # Add returns history
        for i in range(100):
            daily_return = np.random.normal(0.001, 0.02)
            manager.returns_history.append({
                'timestamp': datetime.now() - timedelta(days=100-i),
                'equity': 10000 * (1 + daily_return),
                'return': daily_return
            })
        
        var_95, cvar_95 = manager.calculate_var_cvar(0.95)
        assert var_95 >= 0
        assert cvar_95 >= 0
        assert cvar_95 >= var_95
    
    def test_calculate_max_drawdown(self, manager):
        """Test maximum drawdown calculation."""
        # Add equity history with drawdown
        equities = [10000, 11000, 10500, 9500, 10000, 11500]
        for equity in equities:
            manager.returns_history.append({
                'timestamp': datetime.now(),
                'equity': equity,
                'return': 0.0
            })
        
        max_dd = manager.calculate_max_drawdown()
        assert max_dd < 0  # Drawdown is negative
        assert max_dd >= -1.0  # Max -100%
    
    def test_get_current_drawdown(self, manager):
        """Test current drawdown calculation."""
        manager.peak_equity = 11000.0
        manager.current_equity = 10000.0
        current_dd = manager.get_current_drawdown()
        assert current_dd < 0
        assert abs(current_dd - (-1000/11000)) < 0.001
    
    def test_calculate_sector_exposure(self, manager):
        """Test sector exposure calculation."""
        manager.add_position('pos1', 'EURUSD', 1.0, 1.1000, 'forex')
        manager.add_position('pos2', 'AAPL', 100.0, 150.0, 'stocks')
        manager.add_position('pos3', 'BTC', 0.5, 40000.0, 'crypto')
        
        exposure = manager.calculate_sector_exposure()
        assert 'forex' in exposure
        assert 'stocks' in exposure
        assert 'crypto' in exposure
        assert sum(exposure.values()) <= 1.01  # Allow for rounding
    
    def test_calculate_total_exposure(self, manager):
        """Test total exposure calculation."""
        manager.add_position('pos1', 'EURUSD', 1.0, 1.1000, 'forex')
        manager.add_position('pos2', 'AAPL', 100.0, 150.0, 'stocks')
        
        total = manager.calculate_total_exposure()
        expected = 1.0 * 1.1000 + 100.0 * 150.0
        assert abs(total - expected) < 0.01
    
    def test_check_risk_limits_safe(self, manager):
        """Test risk limit checking with safe values."""
        manager.update_equity(10000.0)
        manager.add_position('pos1', 'EURUSD', 1.0, 1.1000, 'forex')
        
        metrics = RiskMetrics(
            var_95=0.02,
            cvar_95=0.03,
            portfolio_delta=1.0,
            portfolio_gamma=0.0,
            portfolio_vega=0.0,
            max_drawdown=-0.05,
            current_drawdown=-0.02,
            correlation_risk=0.05,
            sector_exposure={'forex': 0.15},
            total_exposure=1100.0,
            risk_score=30.0
        )
        
        is_safe, violations = manager.check_risk_limits(metrics)
        assert is_safe
        assert len(violations) == 0
    
    def test_check_risk_limits_violations(self, manager):
        """Test risk limit checking detects violations."""
        metrics = RiskMetrics(
            var_95=0.10,  # Exceeds max_var of 0.05
            cvar_95=0.15,  # Exceeds max_cvar of 0.08
            portfolio_delta=1.0,
            portfolio_gamma=0.0,
            portfolio_vega=0.0,
            max_drawdown=-0.20,  # Exceeds max_drawdown of 0.15
            current_drawdown=-0.10,
            correlation_risk=0.15,  # Exceeds max_correlation_risk of 0.10
            sector_exposure={'forex': 0.30},  # Exceeds max_sector_exposure of 0.25
            total_exposure=1100.0,
            risk_score=80.0
        )
        
        is_safe, violations = manager.check_risk_limits(metrics)
        assert not is_safe
        assert len(violations) > 0
    
    def test_get_risk_report(self, manager):
        """Test getting risk report."""
        manager.update_equity(10000.0)
        manager.add_position('pos1', 'EURUSD', 1.0, 1.1000, 'forex')
        
        report = manager.get_risk_report()
        assert 'timestamp' in report
        assert 'is_safe' in report
        assert 'risk_score' in report
        assert 'var_95' in report
        assert 'cvar_95' in report
        assert 'num_positions' in report
    
    def test_multiple_positions_management(self, manager):
        """Test managing multiple positions."""
        positions_data = [
            ('pos1', 'EURUSD', 1.0, 1.1000, 'forex'),
            ('pos2', 'GBPUSD', 1.0, 1.2500, 'forex'),
            ('pos3', 'AAPL', 100.0, 150.0, 'stocks'),
        ]
        
        for pos_id, symbol, size, price, sector in positions_data:
            manager.add_position(pos_id, symbol, size, price, sector)
        
        assert len(manager.positions) == 3
        
        # Update prices
        manager.update_position_price('pos1', 1.1050)
        manager.update_position_price('pos2', 1.2600)
        manager.update_position_price('pos3', 155.0)
        
        # Check P&L (use approximate comparison for floats)
        assert abs(manager.positions['pos1']['pnl'] - 0.0050) < 1e-10
        assert abs(manager.positions['pos2']['pnl'] - 0.0100) < 1e-10
        assert abs(manager.positions['pos3']['pnl'] - 500.0) < 1e-10
    
    def test_sector_exposure_limits(self, manager):
        """Test sector exposure limit enforcement."""
        # Add positions in same sector
        for i in range(5):
            manager.add_position(f'pos{i}', f'STOCK{i}', 100.0, 100.0, 'stocks')
        
        exposure = manager.calculate_sector_exposure()
        assert exposure['stocks'] <= 1.01  # Allow for rounding
    
    def test_equity_history_tracking(self, manager):
        """Test equity history tracking."""
        equities = [10000, 10100, 10050, 10200, 10150]
        for equity in equities:
            manager.update_equity(equity)
        
        assert len(manager.returns_history) == 5
        assert manager.returns_history[-1]['equity'] == 10150
    
    def test_returns_calculation(self, manager):
        """Test returns calculation."""
        manager.update_equity(10000.0)
        manager.update_equity(10100.0)
        
        assert len(manager.returns_history) == 2
        # Second return should be 100/10000 = 0.01
        assert abs(manager.returns_history[1]['return'] - 0.01) < 0.001
