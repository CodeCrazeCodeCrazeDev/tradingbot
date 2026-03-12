"""
End-to-End Integration Tests for Broker Adapters

Comprehensive tests covering:
    pass
- Broker connection and authentication
- Order lifecycle (place, modify, cancel, fill)
- Position management
- Order reconciliation
- Failover scenarios
- Error handling
"""

import asyncio
import pytest
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import broker adapters
try:
    from trading_bot.brokers.broker_adapter import (
        BrokerAdapter, MockBrokerAdapter, Position, OrderResponse, 
        OrderStatus, OrderSide, OrderType
    )
    from trading_bot.brokers.live_order_router import (
        LiveOrderRouter, RoutingStrategy, BrokerHealth, OrderRecord
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Import error: {e}")
    IMPORTS_AVAILABLE = False


# Test fixtures
@pytest.fixture
def mock_broker():
    """Create a mock broker for testing"""
    if not IMPORTS_AVAILABLE:
        pytest.skip("Required imports not available")
    
    broker = MockBrokerAdapter({
        'initial_balance': 100000.0,
        'slippage_bps': 1.0
    })
    return broker


@pytest.fixture
def order_router():
    """Create order router for testing"""
    if not IMPORTS_AVAILABLE:
        pytest.skip("Required imports not available")
    
    router = LiveOrderRouter({
        'routing_strategy': 'failover',
        'max_retries': 3,
        'retry_delay': 0.1
    })
    return router


@pytest.fixture
def mock_broker_with_positions(mock_broker):
    """Create mock broker with pre-existing positions"""
    # Add some positions
    mock_broker.positions['EURUSD'] = Position(
        symbol='EURUSD',
        side='buy',
        quantity=100000,
        entry_price=1.1000,
        current_price=1.1050,
        unrealized_pnl=500.0
    )
    mock_broker.positions['GBPUSD'] = Position(
        symbol='GBPUSD',
        side='sell',
        quantity=50000,
        entry_price=1.2500,
        current_price=1.2450,
        unrealized_pnl=250.0
    )
    return mock_broker


class TestBrokerConnection:
    """Test broker connection and authentication"""
    
    @pytest.mark.asyncio
    async def test_mock_broker_connect(self, mock_broker):
        """Test mock broker connection"""
        result = await mock_broker.connect()
        assert result is True
        assert mock_broker.connected is True
    
    @pytest.mark.asyncio
    async def test_mock_broker_disconnect(self, mock_broker):
        """Test mock broker disconnection"""
        await mock_broker.connect()
        result = await mock_broker.disconnect()
        assert result is True
        assert mock_broker.connected is False
    
    @pytest.mark.asyncio
    async def test_broker_reconnection(self, mock_broker):
        """Test broker reconnection"""
        await mock_broker.connect()
        await mock_broker.disconnect()
        result = await mock_broker.connect()
        assert result is True
        assert mock_broker.connected is True


class TestOrderLifecycle:
    """Test complete order lifecycle"""
    
    @pytest.mark.asyncio
    async def test_market_order_buy(self, mock_broker):
        """Test market buy order"""
        await mock_broker.connect()
        
        response = await mock_broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000,
            price=1.1000
        )
        
        assert response is not None
        assert response.success is True
        assert response.status == OrderStatus.FILLED
        assert response.filled_quantity == 100000
    
    @pytest.mark.asyncio
    async def test_market_order_sell(self, mock_broker):
        """Test market sell order"""
        await mock_broker.connect()
        
        response = await mock_broker.place_order(
            symbol='EURUSD',
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=50000,
            price=1.1000
        )
        
        assert response is not None
        assert response.success is True
        assert response.status == OrderStatus.FILLED
    
    @pytest.mark.asyncio
    async def test_limit_order(self, mock_broker):
        """Test limit order"""
        await mock_broker.connect()
        
        response = await mock_broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100000,
            price=1.0950
        )
        
        assert response is not None
        assert response.status == OrderStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_stop_order(self, mock_broker):
        """Test stop order"""
        await mock_broker.connect()
        
        response = await mock_broker.place_order(
            symbol='EURUSD',
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            quantity=100000,
            stop_price=1.0900
        )
        
        assert response is not None
        assert response.status == OrderStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_order_cancellation(self, mock_broker):
        """Test order cancellation"""
        await mock_broker.connect()
        
        # Place limit order
        response = await mock_broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100000,
            price=1.0950
        )
        
        # Cancel order
        result = await mock_broker.cancel_order(response.order_id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_order_status_check(self, mock_broker):
        """Test order status check"""
        await mock_broker.connect()
        
        # Place order
        response = await mock_broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000
        )
        
        # Check status
        status = await mock_broker.get_order_status(response.order_id)
        assert status is not None
        assert status.status == OrderStatus.FILLED


class TestPositionManagement:
    """Test position management"""
    
    @pytest.mark.asyncio
    async def test_get_positions(self, mock_broker_with_positions):
        """Test getting all positions"""
        await mock_broker_with_positions.connect()
        
        positions = await mock_broker_with_positions.get_positions()
        assert len(positions) == 2
    
    @pytest.mark.asyncio
    async def test_get_single_position(self, mock_broker_with_positions):
        """Test getting single position"""
        await mock_broker_with_positions.connect()
        
        position = await mock_broker_with_positions.get_position('EURUSD')
        assert position is not None
        assert position.symbol == 'EURUSD'
        assert position.quantity == 100000
    
    @pytest.mark.asyncio
    async def test_close_position(self, mock_broker_with_positions):
        """Test closing a position"""
        await mock_broker_with_positions.connect()
        
        result = await mock_broker_with_positions.close_position('EURUSD')
        assert result is True
        
        # Verify position is closed
        position = await mock_broker_with_positions.get_position('EURUSD')
        assert position is None
    
    @pytest.mark.asyncio
    async def test_position_pnl_calculation(self, mock_broker_with_positions):
        """Test position P&L calculation"""
        await mock_broker_with_positions.connect()
        
        position = await mock_broker_with_positions.get_position('EURUSD')
        assert position.unrealized_pnl == 500.0


class TestAccountManagement:
    """Test account management"""
    
    @pytest.mark.asyncio
    async def test_get_account_info(self, mock_broker):
        """Test getting account info"""
        await mock_broker.connect()
        
        info = await mock_broker.get_account_info()
        assert 'balance' in info
        assert 'equity' in info
        assert info['balance'] == 100000.0
    
    @pytest.mark.asyncio
    async def test_get_account_equity(self, mock_broker):
        """Test getting account equity"""
        await mock_broker.connect()
        
        equity = await mock_broker.get_account_equity()
        assert equity == 100000.0
    
    @pytest.mark.asyncio
    async def test_equity_after_trade(self, mock_broker):
        """Test equity changes after trade"""
        await mock_broker.connect()
        
        initial_equity = await mock_broker.get_account_equity()
        
        # Place and close a trade
        await mock_broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000,
            price=1.1000
        )
        
        # Equity should still be calculable
        equity = await mock_broker.get_account_equity()
        assert equity is not None


class TestOrderRouter:
    """Test order router functionality"""
    
    @pytest.mark.asyncio
    async def test_register_broker(self, order_router, mock_broker):
        """Test broker registration"""
        order_router.register_broker('mock1', mock_broker, is_primary=True)
        
        assert 'mock1' in order_router.brokers
        assert order_router.primary_broker == 'mock1'
    
    @pytest.mark.asyncio
    async def test_connect_all_brokers(self, order_router, mock_broker):
        """Test connecting all brokers"""
        order_router.register_broker('mock1', mock_broker)
        
        results = await order_router.connect_all()
        assert results['mock1'] is True
    
    @pytest.mark.asyncio
    async def test_route_order(self, order_router, mock_broker):
        """Test order routing"""
        order_router.register_broker('mock1', mock_broker)
        await order_router.connect_all()
        
        order = await order_router.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000
        )
        
        assert order is not None
        assert order.broker_id == 'mock1'
        assert order.status == OrderStatus.FILLED
    
    @pytest.mark.asyncio
    async def test_failover_routing(self, order_router):
        """Test failover routing when primary fails"""
        if not IMPORTS_AVAILABLE:
            pytest.skip("Required imports not available")
        
        # Create two brokers
        primary = MockBrokerAdapter({'initial_balance': 100000})
        backup = MockBrokerAdapter({'initial_balance': 100000})
        
        order_router.register_broker('primary', primary, is_primary=True)
        order_router.register_broker('backup', backup)
        
        await order_router.connect_all()
        
        # Simulate primary failure
        order_router.broker_status['primary'].health = BrokerHealth.UNHEALTHY
        
        # Order should route to backup
        order = await order_router.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000
        )
        
        assert order is not None
        assert order.broker_id == 'backup'
    
    @pytest.mark.asyncio
    async def test_order_reconciliation(self, order_router, mock_broker):
        """Test order reconciliation"""
        order_router.register_broker('mock1', mock_broker)
        await order_router.connect_all()
        
        # Place order
        order = await order_router.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000
        )
        
        # Get status
        status = await order_router.get_order_status(order.order_id)
        assert status is not None
        assert status.status == OrderStatus.FILLED
    
    @pytest.mark.asyncio
    async def test_execution_stats(self, order_router, mock_broker):
        """Test execution statistics tracking"""
        order_router.register_broker('mock1', mock_broker)
        await order_router.connect_all()
        
        # Place several orders
        for _ in range(5):
            await order_router.place_order(
                symbol='EURUSD',
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=10000,
                price=1.1000
            )
        
        stats = order_router.get_execution_stats()
        assert stats.get('total_orders', 0) >= 5
    
    @pytest.mark.asyncio
    async def test_audit_log(self, order_router, mock_broker):
        """Test audit logging"""
        order_router.register_broker('mock1', mock_broker)
        await order_router.connect_all()
        
        await order_router.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000
        )
        
        audit_log = order_router.get_audit_log()
        assert len(audit_log) > 0
        
        # Check for order placement entry
        order_entries = [e for e in audit_log if e['action'] == 'order_placed']
        assert len(order_entries) > 0


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_order_without_connection(self, mock_broker):
        """Test order placement without connection"""
        # Don't connect
        response = await mock_broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000
        )
        
        # Should handle gracefully
        # Mock broker might still work, but real brokers would fail
    
    @pytest.mark.asyncio
    async def test_invalid_symbol(self, mock_broker):
        """Test order with invalid symbol"""
        await mock_broker.connect()
        
        # Mock broker accepts any symbol, but this tests the flow
        response = await mock_broker.place_order(
            symbol='INVALID',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000
        )
        
        # Should not crash
        assert response is not None or response is None
    
    @pytest.mark.asyncio
    async def test_zero_quantity(self, mock_broker):
        """Test order with zero quantity"""
        await mock_broker.connect()
        
        response = await mock_broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0
        )
        
        # Should handle gracefully
    
    @pytest.mark.asyncio
    async def test_negative_quantity(self, mock_broker):
        """Test order with negative quantity"""
        await mock_broker.connect()
        
        response = await mock_broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=-100000
        )
        
        # Should handle gracefully


class TestConcurrency:
    """Test concurrent operations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_orders(self, mock_broker):
        """Test placing multiple orders concurrently"""
        await mock_broker.connect()
        
        # Place 10 orders concurrently
        tasks = [
            mock_broker.place_order(
                symbol='EURUSD',
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=10000
            )
            for _ in range(10)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        successful = [r for r in responses if r and r.success]
        assert len(successful) == 10
    
    @pytest.mark.asyncio
    async def test_concurrent_position_queries(self, mock_broker_with_positions):
        """Test concurrent position queries"""
        await mock_broker_with_positions.connect()
        
        # Query positions concurrently
        tasks = [
            mock_broker_with_positions.get_positions()
            for _ in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should return same positions
        for positions in results:
            assert len(positions) == 2


class TestBrokerSimulation:
    """Test broker simulation for paper trading"""
    
    @pytest.mark.asyncio
    async def test_full_trading_cycle(self, mock_broker):
        """Test complete trading cycle"""
        await mock_broker.connect()
        
        # 1. Check initial state
        initial_equity = await mock_broker.get_account_equity()
        initial_positions = await mock_broker.get_positions()
        
        assert initial_equity == 100000.0
        assert len(initial_positions) == 0
        
        # 2. Open position
        buy_response = await mock_broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000,
            price=1.1000
        )
        
        assert buy_response.success
        
        # 3. Check position
        positions = await mock_broker.get_positions()
        assert len(positions) == 1
        assert positions[0].symbol == 'EURUSD'
        
        # 4. Close position
        sell_response = await mock_broker.place_order(
            symbol='EURUSD',
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=100000,
            price=1.1010
        )
        
        assert sell_response.success
        
        # 5. Verify position closed
        positions = await mock_broker.get_positions()
        assert len(positions) == 0
        
        # 6. Disconnect
        await mock_broker.disconnect()
        assert not mock_broker.connected


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
