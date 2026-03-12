"""
Unit tests for Broker Adapter

Tests for MT5BrokerAdapter and MockBrokerAdapter
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from trading_bot.brokers import (
    BrokerAdapter,
    MT5BrokerAdapter,
    MockBrokerAdapter,
    OrderSide,
    OrderType,
    OrderStatus,
    Position,
    OrderResponse
)


class TestMockBrokerAdapter:
    """Test suite for MockBrokerAdapter"""
    
    @pytest.fixture
    async def broker(self):
        """Create a mock broker instance"""
        config = {
            'initial_balance': 10000.0,
            'leverage': 100,
            'commission': 0.0001
        }
        broker = MockBrokerAdapter(config)
        await broker.connect()
        yield broker
        await broker.disconnect()
    
    @pytest.mark.asyncio
    async def test_connection(self):
        """Test broker connection"""
        broker = MockBrokerAdapter({'initial_balance': 10000})
        
        # Test connect
        result = await broker.connect()
        assert result is True
        assert broker.connected is True
        
        # Test disconnect
        await broker.disconnect()
        assert broker.connected is False
    
    @pytest.mark.asyncio
    async def test_market_order_buy(self, broker):
        """Test market buy order"""
        response = await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000,
            price=1.1000
        )
        
        assert response is not None
        assert response.success is True
        assert response.order_id is not None
        assert response.filled_quantity == 100000
        assert response.status == OrderStatus.FILLED
        assert response.average_fill_price > 0
    
    @pytest.mark.asyncio
    async def test_market_order_sell(self, broker):
        """Test market sell order"""
        response = await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=100000,
            price=1.1000
        )
        
        assert response is not None
        assert response.success is True
        assert response.filled_quantity == 100000
        assert response.status == OrderStatus.FILLED
    
    @pytest.mark.asyncio
    async def test_limit_order(self, broker):
        """Test limit order placement"""
        response = await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100000,
            price=1.0950
        )
        
        assert response is not None
        assert response.success is True
        assert response.status == OrderStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_stop_order(self, broker):
        """Test stop order placement"""
        response = await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            quantity=100000,
            price=1.0900
        )
        
        assert response is not None
        assert response.success is True
        assert response.status == OrderStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_get_positions(self, broker):
        """Test getting open positions"""
        # Place a market order first
        await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000,
            price=1.1000
        )
        
        # Get positions
        positions = await broker.get_positions()
        
        assert len(positions) == 1
        assert positions[0].symbol == 'EURUSD'
        assert positions[0].quantity == 100000
        assert positions[0].side == 'buy'
    
    @pytest.mark.asyncio
    async def test_close_position(self, broker):
        """Test closing a position"""
        # Open position
        response = await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000,
            price=1.1000
        )
        
        # Close position
        result = await broker.close_position('EURUSD')
        
        assert result is True
        
        # Verify position closed
        positions = await broker.get_positions()
        assert len(positions) == 0
    
    @pytest.mark.asyncio
    async def test_get_account_equity(self, broker):
        """Test getting account equity"""
        equity = await broker.get_account_equity()
        
        assert equity > 0
        assert equity == 10000.0  # Initial balance
    
    @pytest.mark.asyncio
    async def test_account_equity_after_trade(self, broker):
        """Test account equity changes after trade"""
        initial_equity = await broker.get_account_equity()
        
        # Place and close a profitable trade
        await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000,
            price=1.1000
        )
        
        # Simulate price increase
        broker.mock_prices['EURUSD'] = 1.1050
        
        await broker.close_position('EURUSD')
        
        final_equity = await broker.get_account_equity()
        
        # Should have profit (minus commission)
        assert final_equity > initial_equity
    
    @pytest.mark.asyncio
    async def test_invalid_symbol(self, broker):
        """Test order with invalid symbol"""
        response = await broker.place_order(
            symbol='INVALID',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000,
            price=1.0000
        )
        
        assert response is not None
        # Mock broker should still accept it
        assert response.success is True
    
    @pytest.mark.asyncio
    async def test_zero_quantity(self, broker):
        """Test order with zero quantity"""
        response = await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0,
            price=1.1000
        )
        
        assert response is not None
        assert response.filled_quantity == 0
    
    @pytest.mark.asyncio
    async def test_negative_quantity(self, broker):
        """Test order with negative quantity"""
        response = await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=-100000,
            price=1.1000
        )
        
        # Should handle gracefully
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_multiple_positions(self, broker):
        """Test multiple open positions"""
        # Open multiple positions
        await broker.place_order('EURUSD', OrderSide.BUY, OrderType.MARKET, 100000, 1.1000)
        await broker.place_order('GBPUSD', OrderSide.BUY, OrderType.MARKET, 100000, 1.3000)
        await broker.place_order('USDJPY', OrderSide.SELL, OrderType.MARKET, 100000, 110.00)
        
        positions = await broker.get_positions()
        
        assert len(positions) == 3
        symbols = [p.symbol for p in positions]
        assert 'EURUSD' in symbols
        assert 'GBPUSD' in symbols
        assert 'USDJPY' in symbols
    
    @pytest.mark.asyncio
    async def test_order_without_connection(self):
        """Test placing order without connection"""
        broker = MockBrokerAdapter({'initial_balance': 10000})
        
        # Don't connect
        response = await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000,
            price=1.1000
        )
        
        # Should fail or handle gracefully
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_slippage_simulation(self, broker):
        """Test slippage in order execution"""
        response = await broker.place_order(
            symbol='EURUSD',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100000,
            price=1.1000
        )
        
        # Fill price should be slightly different due to slippage
        assert response.average_fill_price != 1.1000
        
        # Slippage should be small
        slippage = abs(response.average_fill_price - 1.1000)
        assert slippage < 0.001  # Less than 10 pips


class TestMT5BrokerAdapter:
    """Test suite for MT5BrokerAdapter (integration tests)"""
    
    @pytest.mark.skipif(True, reason="Requires MT5 connection")
    @pytest.mark.asyncio
    async def test_mt5_connection(self):
        """Test MT5 connection (requires MT5 installed)"""
        config = {
            'login': 12345,
            'password': 'test',
            'server': 'test_server'
        }
        broker = MT5BrokerAdapter(config)
        
        # This will fail without real MT5, but tests the interface
        result = await broker.connect()
        assert isinstance(result, bool)


class TestBrokerAdapterInterface:
    """Test BrokerAdapter abstract interface"""
    
    def test_abstract_methods(self):
        """Test that BrokerAdapter cannot be instantiated"""
        with pytest.raises(TypeError):
            broker = BrokerAdapter()


class TestOrderEnums:
    """Test order enums and data classes"""
    
    def test_order_side_enum(self):
        """Test OrderSide enum"""
        assert OrderSide.BUY.value == 'buy'
        assert OrderSide.SELL.value == 'sell'
    
    def test_order_type_enum(self):
        """Test OrderType enum"""
        assert OrderType.MARKET.value == 'market'
        assert OrderType.LIMIT.value == 'limit'
        assert OrderType.STOP.value == 'stop'
    
    def test_order_status_enum(self):
        """Test OrderStatus enum"""
        assert OrderStatus.PENDING.value == 'pending'
        assert OrderStatus.FILLED.value == 'filled'
        assert OrderStatus.CANCELLED.value == 'cancelled'
        assert OrderStatus.REJECTED.value == 'rejected'
    
    def test_position_dataclass(self):
        """Test Position dataclass"""
        position = Position(
            symbol='EURUSD',
            side='buy',
            quantity=100000,
            entry_price=1.1000,
            current_price=1.1050,
            unrealized_pnl=500.0
        )
        
        assert position.symbol == 'EURUSD'
        assert position.quantity == 100000
        assert position.unrealized_pnl == 500.0
    
    def test_order_response_dataclass(self):
        """Test OrderResponse dataclass"""
        response = OrderResponse(
            order_id='12345',
            status=OrderStatus.FILLED,
            filled_quantity=100000,
            average_fill_price=1.1000,
            commission=10.0,
            timestamp=datetime.now(),
            metadata={}
        )
        
        assert response.success is True  # Uses property
        assert response.order_id == '12345'
        assert response.filled_quantity == 100000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
