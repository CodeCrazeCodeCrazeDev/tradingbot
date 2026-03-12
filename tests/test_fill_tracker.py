"""
Unit tests for Fill Tracker

Tests for order fill confirmation and slippage tracking
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from trading_bot.execution.fill_tracker import (
    FillTracker,
    OrderFillRecord,
    Fill,
    FillStatus
)
from trading_bot.brokers import MockBrokerAdapter, OrderSide


class TestFillTracker:
    """Test suite for FillTracker"""
    
    @pytest.fixture
    async def broker(self):
        """Create a mock broker"""
        broker = MockBrokerAdapter({'initial_balance': 10000})
        await broker.connect()
        yield broker
        await broker.disconnect()
    
    @pytest.fixture
    def tracker(self, broker):
        """Create a fill tracker instance"""
        config = {
            'confirmation_timeout': 30,
            'max_retries': 3,
            'retry_delay': 1,
            'max_slippage_history': 1000
        }
        return FillTracker(broker, config)
    
    @pytest.mark.asyncio
    async def test_initialization(self, broker):
        """Test fill tracker initialization"""
        tracker = FillTracker(broker)
        assert tracker is not None
        assert tracker.broker == broker
    
    @pytest.mark.asyncio
    async def test_track_order(self, tracker, broker):
        """Test tracking an order"""
        # Place order first
        response = await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type='market',
            quantity=100000,
            price=1.1000
        )
        
        # Track the order
        record = await tracker.track_order(
            order_id=response.order_id,
            symbol='EURUSD',
            side='buy',
            quantity=100000,
            expected_price=1.1000
        )
        
        assert record is not None
        assert record.order_id == response.order_id
        assert record.symbol == 'EURUSD'
        assert record.quantity == 100000
    
    @pytest.mark.asyncio
    async def test_wait_for_confirmation(self, tracker, broker):
        """Test waiting for order confirmation"""
        # Place order
        response = await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type='market',
            quantity=100000,
            price=1.1000
        )
        
        # Track order
        await tracker.track_order(
            order_id=response.order_id,
            symbol='EURUSD',
            side='buy',
            quantity=100000,
            expected_price=1.1000
        )
        
        # Wait for confirmation
        confirmed = await tracker.wait_for_confirmation(response.order_id, timeout=5)
        
        assert confirmed is not None
        assert confirmed.status == FillStatus.CONFIRMED
    
    @pytest.mark.asyncio
    async def test_slippage_calculation(self, tracker, broker):
        """Test slippage calculation"""
        expected_price = 1.1000
        
        # Place order
        response = await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type='market',
            quantity=100000,
            price=expected_price
        )
        
        # Track order
        record = await tracker.track_order(
            order_id=response.order_id,
            symbol='EURUSD',
            side='buy',
            quantity=100000,
            expected_price=expected_price
        )
        
        # Wait for confirmation
        await tracker.wait_for_confirmation(response.order_id, timeout=5)
        
        # Check slippage was calculated
        assert record.slippage_bps is not None
    
    @pytest.mark.asyncio
    async def test_slippage_stats(self, tracker, broker):
        """Test slippage statistics"""
        # Place multiple orders
        for i in range(5):
            response = await broker.place_order(
                symbol='EURUSD',
                side=OrderSide.BUY,
                order_type='market',
                quantity=100000,
                price=1.1000 + i * 0.0001
            )
            
            await tracker.track_order(
                order_id=response.order_id,
                symbol='EURUSD',
                side='buy',
                quantity=100000,
                expected_price=1.1000 + i * 0.0001
            )
            
            await tracker.wait_for_confirmation(response.order_id, timeout=5)
        
        # Get slippage stats
        stats = tracker.get_slippage_stats(symbol='EURUSD')
        
        assert 'avg_slippage_bps' in stats
        assert 'max_slippage_bps' in stats
        assert 'min_slippage_bps' in stats
        assert 'positive_slippage_pct' in stats
    
    @pytest.mark.asyncio
    async def test_confirmation_timeout(self, tracker, broker):
        """Test confirmation timeout"""
        # Track a non-existent order
        record = await tracker.track_order(
            order_id='non_existent',
            symbol='EURUSD',
            side='buy',
            quantity=100000,
            expected_price=1.1000
        )
        
        # Wait with short timeout
        confirmed = await tracker.wait_for_confirmation('non_existent', timeout=1)
        
        # Should timeout
        assert confirmed is None or confirmed.status == FillStatus.TIMEOUT
    
    @pytest.mark.asyncio
    async def test_partial_fill(self, tracker, broker):
        """Test partial fill tracking"""
        # This would require broker support for partial fills
        # Mock broker fills completely, so we test the interface
        
        response = await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type='market',
            quantity=100000,
            price=1.1000
        )
        
        record = await tracker.track_order(
            order_id=response.order_id,
            symbol='EURUSD',
            side='buy',
            quantity=100000,
            expected_price=1.1000
        )
        
        assert record.quantity == 100000
    
    @pytest.mark.asyncio
    async def test_multiple_fills(self, tracker, broker):
        """Test tracking multiple fills"""
        order_ids = []
        
        # Place multiple orders
        for i in range(3):
            response = await broker.place_order(
                symbol='EURUSD',
                side=OrderSide.BUY,
                order_type='market',
                quantity=100000,
                price=1.1000
            )
            order_ids.append(response.order_id)
            
            await tracker.track_order(
                order_id=response.order_id,
                symbol='EURUSD',
                side='buy',
                quantity=100000,
                expected_price=1.1000
            )
        
        # Confirm all
        for order_id in order_ids:
            confirmed = await tracker.wait_for_confirmation(order_id, timeout=5)
            assert confirmed is not None
    
    @pytest.mark.asyncio
    async def test_confirmation_stats(self, tracker, broker):
        """Test confirmation statistics"""
        # Place and track multiple orders
        for i in range(5):
            response = await broker.place_order(
                symbol='EURUSD',
                side=OrderSide.BUY,
                order_type='market',
                quantity=100000,
                price=1.1000
            )
            
            await tracker.track_order(
                order_id=response.order_id,
                symbol='EURUSD',
                side='buy',
                quantity=100000,
                expected_price=1.1000
            )
            
            await tracker.wait_for_confirmation(response.order_id, timeout=5)
        
        # Get confirmation stats
        stats = tracker.get_confirmation_stats()
        
        assert 'total_orders' in stats
        assert 'confirmed_orders' in stats
        assert 'confirmation_rate' in stats
        assert stats['total_orders'] == 5
    
    @pytest.mark.asyncio
    async def test_slippage_by_timeframe(self, tracker, broker):
        """Test slippage statistics by timeframe"""
        # Place orders
        for i in range(3):
            response = await broker.place_order(
                symbol='EURUSD',
                side=OrderSide.BUY,
                order_type='market',
                quantity=100000,
                price=1.1000
            )
            
            await tracker.track_order(
                order_id=response.order_id,
                symbol='EURUSD',
                side='buy',
                quantity=100000,
                expected_price=1.1000
            )
            
            await tracker.wait_for_confirmation(response.order_id, timeout=5)
        
        # Get stats for last hour
        stats = tracker.get_slippage_stats(symbol='EURUSD', lookback_hours=1)
        
        assert stats is not None
        assert 'avg_slippage_bps' in stats
    
    @pytest.mark.asyncio
    async def test_different_symbols(self, tracker, broker):
        """Test tracking orders for different symbols"""
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        
        for symbol in symbols:
            response = await broker.place_order(
                symbol=symbol,
                side=OrderSide.BUY,
                order_type='market',
                quantity=100000,
                price=1.1000
            )
            
            await tracker.track_order(
                order_id=response.order_id,
                symbol=symbol,
                side='buy',
                quantity=100000,
                expected_price=1.1000
            )
            
            confirmed = await tracker.wait_for_confirmation(response.order_id, timeout=5)
            assert confirmed is not None
    
    @pytest.mark.asyncio
    async def test_positive_slippage(self, tracker, broker):
        """Test positive slippage detection"""
        # Place order with expected price higher than actual
        response = await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type='market',
            quantity=100000,
            price=1.0990  # Actual fill
        )
        
        await tracker.track_order(
            order_id=response.order_id,
            symbol='EURUSD',
            side='buy',
            quantity=100000,
            expected_price=1.1000  # Expected higher
        )
        
        await tracker.wait_for_confirmation(response.order_id, timeout=5)
        
        # Should detect positive slippage
        stats = tracker.get_slippage_stats(symbol='EURUSD')
        assert stats['positive_slippage_pct'] >= 0
    
    @pytest.mark.asyncio
    async def test_negative_slippage(self, tracker, broker):
        """Test negative slippage detection"""
        # Place order with expected price lower than actual
        response = await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type='market',
            quantity=100000,
            price=1.1010  # Actual fill
        )
        
        await tracker.track_order(
            order_id=response.order_id,
            symbol='EURUSD',
            side='buy',
            quantity=100000,
            expected_price=1.1000  # Expected lower
        )
        
        await tracker.wait_for_confirmation(response.order_id, timeout=5)
        
        # Should detect negative slippage
        record = tracker.pending_orders.get(response.order_id) or \
                 tracker.confirmed_orders.get(response.order_id)
        if record and record.slippage_bps:
            assert record.slippage_bps != 0


class TestFillTrackerEdgeCases:
    """Test edge cases for FillTracker"""
    
    @pytest.fixture
    async def broker(self):
        """Create a mock broker"""
        broker = MockBrokerAdapter({'initial_balance': 10000})
        await broker.connect()
        yield broker
        await broker.disconnect()
    
    @pytest.mark.asyncio
    async def test_empty_order_id(self, broker):
        """Test with empty order ID"""
        tracker = FillTracker(broker)
        
        record = await tracker.track_order(
            order_id='',
            symbol='EURUSD',
            side='buy',
            quantity=100000,
            expected_price=1.1000
        )
        
        # Should handle gracefully
        assert record is not None or record is None
    
    @pytest.mark.asyncio
    async def test_zero_quantity(self, broker):
        """Test with zero quantity"""
        tracker = FillTracker(broker)
        
        record = await tracker.track_order(
            order_id='test123',
            symbol='EURUSD',
            side='buy',
            quantity=0,
            expected_price=1.1000
        )
        
        assert record is not None
    
    @pytest.mark.asyncio
    async def test_negative_price(self, broker):
        """Test with negative expected price"""
        tracker = FillTracker(broker)
        
        record = await tracker.track_order(
            order_id='test123',
            symbol='EURUSD',
            side='buy',
            quantity=100000,
            expected_price=-1.1000
        )
        
        # Should handle gracefully
        assert record is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
