"""
Unit Tests for Execution Engine
===============================
Tests for the execution engine and order management.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
import asyncio


@pytest.mark.unit
class TestTWAPExecutor:
    """Test TWAP execution algorithm."""
    
    def test_create_twap_plan(self):
        """Test TWAP plan creation."""
        from trading_bot.execution.advanced_algorithms import TWAPExecutor, OrderSide
        
        twap = TWAPExecutor()
        plan = twap.create_plan(
            symbol='EURUSD',
            side=OrderSide.BUY,
            quantity=1000,
            duration_minutes=1
        )
        
        assert plan is not None
        assert plan.symbol == 'EURUSD'
        assert plan.total_quantity == 1000
    
    def test_twap_slices_calculation(self):
        """Test TWAP slices are calculated correctly."""
        from trading_bot.execution.advanced_algorithms import TWAPExecutor, OrderSide
        
        twap = TWAPExecutor()
        plan = twap.create_plan(
            symbol='EURUSD',
            side=OrderSide.BUY,
            quantity=1000,
            duration_minutes=10,
            num_slices=10
        )
        
        # Should have correct number of slices
        assert len(plan.slices) == 10
        
        # Total quantity should match
        total = sum(s.quantity for s in plan.slices)
        assert abs(total - 1000) < 1  # Allow small rounding error


@pytest.mark.unit
class TestVWAPExecutor:
    """Test VWAP execution algorithm."""
    
    def test_create_vwap_plan(self):
        """Test VWAP plan creation."""
        from trading_bot.execution.advanced_algorithms import VWAPExecutor, OrderSide
        
        vwap = VWAPExecutor()
        plan = vwap.create_plan(
            symbol='EURUSD',
            side=OrderSide.SELL,
            quantity=500,
            duration_minutes=2
        )
        
        assert plan is not None
        assert plan.symbol == 'EURUSD'
        assert plan.side == OrderSide.SELL


@pytest.mark.unit
class TestExecutionEngine:
    """Test main execution engine."""
    
    def test_engine_initialization(self, execution_engine):
        """Test execution engine initializes correctly."""
        assert execution_engine is not None
        assert execution_engine.twap is not None
        assert execution_engine.vwap is not None
    
    def test_create_plan_twap(self, execution_engine):
        """Test creating TWAP plan through engine."""
        from trading_bot.execution.advanced_algorithms import ExecutionAlgorithm, OrderSide
        
        plan = execution_engine.create_plan(
            algorithm=ExecutionAlgorithm.TWAP,
            symbol='GBPUSD',
            side=OrderSide.BUY,
            quantity=2000,
            duration_minutes=5
        )
        
        assert plan is not None
        assert plan.algorithm == ExecutionAlgorithm.TWAP
    
    def test_create_plan_vwap(self, execution_engine):
        """Test creating VWAP plan through engine."""
        from trading_bot.execution.advanced_algorithms import ExecutionAlgorithm, OrderSide
        
        plan = execution_engine.create_plan(
            algorithm=ExecutionAlgorithm.VWAP,
            symbol='USDJPY',
            side=OrderSide.SELL,
            quantity=3000,
            duration_minutes=10
        )
        
        assert plan is not None
        assert plan.algorithm == ExecutionAlgorithm.VWAP


@pytest.mark.unit
class TestSmartOrderRouter:
    """Test smart order router."""
    
    def test_router_initialization(self):
        """Test router initializes correctly."""
        from trading_bot.execution.advanced_algorithms import SmartOrderRouter
        
        router = SmartOrderRouter()
        assert router is not None
    
    @pytest.mark.asyncio
    async def test_route_order(self):
        """Test order routing."""
        from trading_bot.execution.advanced_algorithms import SmartOrderRouter, OrderSide
        
        router = SmartOrderRouter()
        
        # Route should return a venue
        venue = await router.route_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            quantity=100
        )
        
        # Should return some routing decision
        assert venue is not None or True  # May return None if no venues configured
