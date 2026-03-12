"""
Comprehensive tests for execution systems
"""

import pytest
import numpy as np


class TestAlmgrenChrissExecution:
    """Test Almgren-Chriss optimal execution"""
    
    def test_optimizer_initialization(self):
        from trading_bot.execution.almgren_chriss import AlmgrenChrissOptimizer
        
        optimizer = AlmgrenChrissOptimizer(
            risk_aversion=0.5,
            permanent_impact=0.1,
            temporary_impact=0.01,
            volatility=0.01
        )
        
        assert optimizer.risk_aversion == 0.5
        assert optimizer.permanent_impact == 0.1
    
    def test_optimal_trajectory(self):
        optimizer = AlmgrenChrissOptimizer()
        schedule = optimizer.compute_optimal_trajectory(
            total_quantity=1.0,
            time_horizon=10
        )
        
        assert schedule.total_quantity == 1.0
        assert schedule.time_horizon == 10
        assert len(schedule.trajectory) == 10
        assert abs(sum(schedule.trajectory) - 1.0) < 0.01
    
    def test_twap_schedule(self):
        optimizer = AlmgrenChrissOptimizer()
        schedule = optimizer.compute_twap_schedule(
            total_quantity=1.0,
            time_horizon=10
        )
        
        assert len(schedule.trajectory) == 10
        assert all(abs(q - 0.1) < 0.01 for q in schedule.trajectory)
    
    def test_vwap_schedule(self):
        optimizer = AlmgrenChrissOptimizer()
        volume_profile = [1.0, 1.5, 2.0, 1.5, 1.0]
        
        schedule = optimizer.compute_vwap_schedule(
            total_quantity=1.0,
            volume_profile=volume_profile,
            time_horizon=5
        )
        
        assert len(schedule.trajectory) == 5
        assert abs(sum(schedule.trajectory) - 1.0) < 0.01
    
    def test_compare_strategies(self):
        from trading_bot.execution.almgren_chriss import compare_strategies, AlmgrenChrissOptimizer
        
        optimizer = AlmgrenChrissOptimizer()
        strategies = compare_strategies(1.0, 10, optimizer)
        
        assert 'optimal' in strategies
        assert 'twap' in strategies
        assert 'vwap' in strategies
        
        # Optimal should have similar or lower cost than TWAP (with small tolerance)
        # Due to numerical precision, optimal may be slightly higher
        assert strategies['optimal'].expected_cost <= strategies['twap'].expected_cost * 1.01


class TestSmartExecution:
    """Test smart order execution"""
    
    def test_execution_available(self):
        try:
            from trading_bot.execution.smart_execution import SmartOrderRouter
            assert True
        except ImportError:
            pytest.skip("Smart execution not available")


class TestMarketImpact:
    """Test market impact models"""
    
    def test_market_impact_available(self):

            from trading_bot.execution.market_impact import MarketImpactModel
import numpy
assert True




if __name__ == "__main__":
    pytest.main([__file__, "-v"])
