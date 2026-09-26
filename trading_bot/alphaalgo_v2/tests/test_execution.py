"""
Tests for execution layer
"""

import pytest
import asyncio
import uuid
from datetime import datetime

from ..core.types import Signal, SignalType, Order, OrderType, OrderStatus
from ..execution.engine import ExecutionEngine
from ..execution.brokers.paper import PaperBroker
from ..execution.algorithms.smart import SmartOrderRouter, ExecutionAlgorithm
from typing import Set

import logging

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


logger = logging.getLogger(__name__)



class TestPaperBroker:
    """Tests for PaperBroker"""
    
    @pytest.fixture
    def broker(self):
        return PaperBroker({
            "initial_balance": 10000,
            "slippage_pips": 0.5,
        })
    
    @pytest.mark.asyncio
    async def test_connect(self, broker):
        """Test connection"""
        result = await broker.connect()
        
        assert result is True
        assert broker.is_connected
        assert broker.is_paper_mode
    
    @pytest.mark.asyncio
    async def test_execute_order(self, broker):
        """Test order execution"""
        await broker.connect()
        
        order = Order(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            order_type=OrderType.MARKET,
            side=SignalType.BUY,
            volume=0.1,
            price=1.0850,
            stop_loss=1.0800,
            take_profit=1.0900,
        )
        
        result = await broker.execute(order)
        
        assert result.success
        assert result.fill_price > 0
        assert result.fill_volume == 0.1
    
    @pytest.mark.asyncio
    async def test_get_position(self, broker):
        """Test position tracking"""
        await broker.connect()
        
        order = Order(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            order_type=OrderType.MARKET,
            side=SignalType.BUY,
            volume=0.1,
            price=1.0850,
        )
        
        await broker.execute(order)
        
        position = await broker.get_position("EURUSD")
        
        assert position is not None
        assert position.symbol == "EURUSD"
        assert position.volume == 0.1
    
    @pytest.mark.asyncio
    async def test_close_position(self, broker):
        """Test position closing"""
        await broker.connect()
        broker.set_price("EURUSD", 1.0850)
        
        # Open position
        order = Order(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            order_type=OrderType.MARKET,
            side=SignalType.BUY,
            volume=0.1,
            price=1.0850,
        )
        await broker.execute(order)
        
        # Set new price and close
        broker.set_price("EURUSD", 1.0900)
        result = await broker.close_position("EURUSD")
        
        assert result.success
        assert result.metadata.get("pnl") is not None
        
        # Position should be gone
        position = await broker.get_position("EURUSD")
        assert position is None
    
    @pytest.mark.asyncio
    async def test_cancel_order(self, broker):
        """Test order cancellation"""
        await broker.connect()
        
        order = Order(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            order_type=OrderType.LIMIT,
            side=SignalType.BUY,
            volume=0.1,
            price=1.0800,  # Limit order
        )
        
        # Note: Paper broker fills immediately, so this tests the cancel path
        result = await broker.cancel(order.id)
        # Will be False since order wasn't added as pending
        assert result is False
    
    @pytest.mark.asyncio
    async def test_modify_order(self, broker):
        """Test order modification"""
        await broker.connect()
        
        order = Order(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            order_type=OrderType.MARKET,
            side=SignalType.BUY,
            volume=0.1,
            price=1.0850,
            stop_loss=1.0800,
            take_profit=1.0900,
        )
        
        await broker.execute(order)
        
        result = await broker.modify(
            order.id,
            stop_loss=1.0810,
            take_profit=1.0950,
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_account_info(self, broker):
        """Test account info"""
        await broker.connect()
        
        info = await broker.get_account_info()
        
        assert info["balance"] == 10000
        assert info["equity"] == 10000
    
    def test_get_stats(self, broker):
        """Test statistics"""
        stats = broker.get_stats()
        
        assert stats["total_trades"] == 0
        assert stats["win_rate"] == 0.0


class TestSmartOrderRouter:
    """Tests for SmartOrderRouter"""
    
    @pytest.fixture
    def router(self):
        return SmartOrderRouter({
            "large_order_threshold": 10.0,
            "medium_order_threshold": 1.0,
        })
    
    def test_small_order_plan(self, router):
        """Test plan for small orders"""
        order = Order(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            order_type=OrderType.MARKET,
            side=SignalType.BUY,
            volume=0.5,  # Small
            price=1.0850,
        )
        
        plan = router.create_execution_plan(order)
        
        assert plan.algorithm == ExecutionAlgorithm.MARKET
        assert plan.slices == 1
        assert plan.urgency == 1.0
    
    def test_medium_order_plan(self, router):
        """Test plan for medium orders"""
        order = Order(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            order_type=OrderType.MARKET,
            side=SignalType.BUY,
            volume=5.0,  # Medium
            price=1.0850,
        )
        
        plan = router.create_execution_plan(order)
        
        assert plan.algorithm == ExecutionAlgorithm.SMART
        assert plan.slices > 1
    
    def test_large_order_plan(self, router):
        """Test plan for large orders"""
        order = Order(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            order_type=OrderType.MARKET,
            side=SignalType.BUY,
            volume=20.0,  # Large
            price=1.0850,
        )
        
        plan = router.create_execution_plan(order)
        
        assert plan.algorithm == ExecutionAlgorithm.TWAP
        assert plan.slices >= 10
        assert plan.urgency < 0.5
    
    def test_slice_order(self, router):
        """Test order slicing"""
        order = Order(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            order_type=OrderType.MARKET,
            side=SignalType.BUY,
            volume=10.0,
            price=1.0850,
        )
        
        plan = router.create_execution_plan(order)
        slices = router.slice_order(order, plan)
        
        assert len(slices) == plan.slices
        
        # Total volume should match
        total_volume = sum(s.volume for s in slices)
        assert abs(total_volume - order.volume) < 0.001
    
    def test_optimal_timing(self, router):
        """Test optimal timing"""
        timing = router.get_optimal_timing(
            symbol="EURUSD",
            side=SignalType.BUY,
            conditions={"volatility": 1.0, "spread": 0.0001},
        )
        
        assert "delay_seconds" in timing
        assert "reason" in timing


class TestExecutionEngine:
    """Tests for ExecutionEngine"""
    
    @pytest.fixture
    def engine(self):
        return ExecutionEngine({})
    
    @pytest.fixture
    def signal(self):
        return Signal(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            signal_type=SignalType.BUY,
            price=1.0850,
            confidence=0.75,
            stop_loss=1.0800,
            take_profit=1.0900,
            timeframe="M15",
            source="test",
        )
    
    @pytest.mark.asyncio
    async def test_initialize(self, engine):
        """Test engine initialization"""
        result = await engine.initialize()
        
        assert result is True
        assert engine._broker is not None
    
    @pytest.mark.asyncio
    async def test_execute_signal(self, engine, signal):
        """Test signal execution"""
        await engine.initialize()
        
        result = await engine.execute_signal(
            signal=signal,
            position_size=0.1,
        )
        
        assert result.success
        assert result.fill_price > 0
    
    @pytest.mark.asyncio
    async def test_close_position(self, engine, signal):
        """Test position closing"""
        await engine.initialize()
        
        # Open position
        await engine.execute_signal(signal=signal, position_size=0.1)
        
        # Close position
        result = await engine.close_position("EURUSD")
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_get_positions(self, engine, signal):
        """Test getting positions"""
        await engine.initialize()
        
        await engine.execute_signal(signal=signal, position_size=0.1)
        
        positions = await engine.get_positions()
        
        assert len(positions) == 1
        assert positions[0].symbol == "EURUSD"
    
    @pytest.mark.asyncio
    async def test_close_all_positions(self, engine, signal):
        """Test closing all positions"""
        await engine.initialize()
        
        await engine.execute_signal(signal=signal, position_size=0.1)
        
        results = await engine.close_all_positions()
        
        assert len(results) == 1
        assert results[0].success
    
    def test_get_stats(self, engine):
        """Test statistics"""
        stats = engine.get_stats()
        
        assert "total_orders" in stats
        assert "success_rate" in stats
        assert "avg_slippage_pips" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
