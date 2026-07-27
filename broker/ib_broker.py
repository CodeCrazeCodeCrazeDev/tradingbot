"""
Interactive Brokers implementation for AlphaAlgo 2.0
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import asyncio
from ib_insync import IB, Contract, Order as IBOrder, MarketOrder, LimitOrder
from .broker_interface import (
    BrokerInterface,
    Order,
    OrderType,
    OrderSide,
    OrderStatus,
    Position
)

# Set up logger
logger = logging.getLogger(__name__)


class IBBroker(BrokerInterface):
    """
    Interactive Brokers implementation.
    Handles IB TWS/Gateway API integration.
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 7497,  # 7497 for TWS, 4002 for Gateway
        client_id: int = 1,
        account_id: Optional[str] = None,
        readonly: bool = False
    ):
        super().__init__(
            api_key='',  # Not used for IB
            api_secret='',
            base_url='',
            testnet=False
        )
        
        self.host = host
        self.port = port
        self.client_id = client_id
        self.account_id = account_id
        self.readonly = readonly
        
        # IB client
        self.ib = IB()
        
        # Contract cache
        self.contracts = {}
        
        # Order mapping
        self.order_mapping = {}
        
        logger.info("✅ IB Broker initialized")
        logger.info(f"   Host: {host}:{port}")
        logger.info(f"   Client ID: {client_id}")
    
    async def connect(self):
        """Connect to IB TWS/Gateway."""
        try:
            # Connect to IB
            self.ib.connect(
                host=self.host,
                port=self.port,
                clientId=self.client_id,
                readonly=self.readonly
            )
            
            # Wait for connection
            timeout = 30
            start_time = datetime.now()
            while not self.ib.isConnected():
                await asyncio.sleep(0.1)
                if (datetime.now() - start_time).total_seconds() > timeout:
                    raise TimeoutError("Connection timeout")
            
            # Set up callbacks
            self.ib.orderStatusEvent += self._handle_order_status
            self.ib.positionEvent += self._handle_position_update
            self.ib.accountValueEvent += self._handle_account_update
            
            logger.info("✅ Connected to Interactive Brokers")
            
            # Get account info
            account = await self.get_account()
            if account:
                logger.info(f"   Account: {account['id']}")
            
        except Exception as e:
            logger.error(f"❌ Connection error: {str(e)}")
            raise
    
    async def disconnect(self):
        """Disconnect from IB."""
        if self.ib.isConnected():
            self.ib.disconnect()
            logger.info("✅ Disconnected from Interactive Brokers")
    
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Order:
        """Place order through IB."""
        try:
            # Get contract
            contract = await self._get_contract(symbol)
            
            # Create IB order
            ib_order = self._create_ib_order(
                side,
                type,
                quantity,
                price,
                stop_price
            )
            
            # Create order object
            order = Order(
                symbol=symbol,
                side=side,
                type=type,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                client_order_id=self._generate_order_id()
            )
            
            # Place order
            trade = self.ib.placeOrder(contract, ib_order)
            
            # Map order IDs
            self.order_mapping[trade.order.orderId] = order.client_order_id
            self.orders[order.client_order_id] = order
            
            logger.info(f"✅ Order placed: {order.client_order_id}")
            logger.info(f"   {side.value} {quantity} {symbol}")
            if price:
                logger.info(f"   Price: {price}")
            
            return order
            
        except Exception as e:
            logger.error(f"❌ Order error: {str(e)}")
            raise
    
    async def cancel_order(
        self,
        symbol: str,
        order_id: str
    ) -> bool:
        """Cancel IB order."""
        try:
            # Find IB order
            trades = self.ib.trades()
            for trade in trades:
                if (trade.order.orderId in self.order_mapping and
                    self.order_mapping[trade.order.orderId] == order_id):
                    # Cancel order
                    self.ib.cancelOrder(trade.order)
                    
                    # Update status
                    if order_id in self.orders:
                        self.orders[order_id].status = OrderStatus.CANCELLED
                    
                    logger.info(f"✅ Order cancelled: {order_id}")
                    return True
            
            logger.warning(f"⚠️ Order {order_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"❌ Cancel error: {str(e)}")
            return False
    
    async def get_positions(self) -> Dict[str, Position]:
        """Get current IB positions."""
        try:
            positions = {}
            
            # Get portfolio
            portfolio = self.ib.portfolio()
            
            for item in portfolio:
                # Create position object
                position = Position(
                    symbol=self._get_symbol(item.contract),
                    quantity=item.position,
                    entry_price=item.averageCost,
                    current_price=item.marketPrice,
                    unrealized_pnl=item.unrealizedPNL,
                    realized_pnl=item.realizedPNL
                )
                
                positions[position.symbol] = position
            
            self.positions = positions
            return positions
            
        except Exception as e:
            logger.error(f"❌ Position query error: {str(e)}")
            return {}
    
    async def get_account(self) -> Dict:
        """Get IB account information."""
        try:
            # Get account summary
            summary = {}
            
            if self.account_id:
                tags = ['NetLiquidation', 'AvailableFunds', 'MaintMarginReq']
                account_values = self.ib.accountSummary(self.account_id)
                
                for value in account_values:
                    if value.tag in tags:
                        summary[value.tag] = float(value.value)
            
            return {
                'id': self.account_id,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"❌ Account query error: {str(e)}")
            return {}
    
    async def get_market_data(
        self,
        symbol: str,
        data_type: str = 'TRADES'
    ) -> Dict:
        """Get real-time market data."""
        try:
            contract = await self._get_contract(symbol)
            
            # Request market data
            self.ib.reqMktData(contract, '', False, False)
            
            # Wait for data
            await asyncio.sleep(1)
            
            # Get ticker
            ticker = self.ib.ticker(contract)
            
            return {
                'last': ticker.last,
                'bid': ticker.bid,
                'ask': ticker.ask,
                'volume': ticker.volume,
                'high': ticker.high,
                'low': ticker.low,
                'close': ticker.close
            }
            
        except Exception as e:
            logger.error(f"❌ Market data error: {str(e)}")
            return {}
    
    async def _get_contract(self, symbol: str) -> Contract:
        """Get or create IB contract."""
        if symbol in self.contracts:
            return self.contracts[symbol]
        
        # Parse symbol
        parts = symbol.split('.')
        if len(parts) == 2:
            symbol, exchange = parts
        else:
            exchange = 'SMART'
        
        # Create contract
        if symbol.endswith('USD'):  # Crypto
            contract = Contract(
                symbol=symbol[:-3],
                secType='CRYPTO',
                exchange=exchange,
                currency='USD'
            )
        else:  # Stock
            contract = Contract(
                symbol=symbol,
                secType='STK',
                exchange=exchange,
                currency='USD'
            )
        
        # Qualify contract
        contract = self.ib.qualifyContracts(contract)[0]
        
        # Cache contract
        self.contracts[symbol] = contract
        
        return contract
    
    def _create_ib_order(
        self,
        side: OrderSide,
        type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> IBOrder:
        """Create IB order object."""
        action = 'BUY' if side == OrderSide.BUY else 'SELL'
        
        if type == OrderType.MARKET:
            order = MarketOrder(
                action=action,
                totalQuantity=quantity
            )
        
        elif type == OrderType.LIMIT:
            order = LimitOrder(
                action=action,
                totalQuantity=quantity,
                lmtPrice=price
            )
        
        elif type == OrderType.STOP:
            order = IBOrder(
                orderType='STP',
                action=action,
                totalQuantity=quantity,
                auxPrice=stop_price
            )
        
        elif type == OrderType.STOP_LIMIT:
            order = IBOrder(
                orderType='STP LMT',
                action=action,
                totalQuantity=quantity,
                lmtPrice=price,
                auxPrice=stop_price
            )
        
        else:
            raise ValueError(f"Unsupported order type: {type}")
        
        return order
    
    def _get_symbol(self, contract: Contract) -> str:
        """Get symbol from contract."""
        if contract.exchange == 'SMART':
            return contract.symbol
        else:
            return f"{contract.symbol}.{contract.exchange}"
    
    def _handle_order_status(
        self,
        trade: object
    ):
        """Handle IB order status updates."""
        if trade.order.orderId in self.order_mapping:
            order_id = self.order_mapping[trade.order.orderId]
            
            if order_id in self.orders:
                order = self.orders[order_id]
                
                # Update status
                order.status = self._convert_order_status(trade.orderStatus.status)
                order.filled_quantity = trade.orderStatus.filled
                if trade.orderStatus.avgFillPrice:
                    order.filled_price = trade.orderStatus.avgFillPrice
                
                logger.info(f"📊 Order update: {order_id}")
                logger.info(f"   Status: {order.status.value}")
                logger.info(f"   Filled: {order.filled_quantity}")
    
    def _handle_position_update(
        self,
        position: object
    ):
        """Handle IB position updates."""
        symbol = self._get_symbol(position.contract)
        
        # Update position
        if symbol in self.positions:
            pos = self.positions[symbol]
            pos.quantity = position.position
            pos.entry_price = position.avgCost
            pos.timestamp = datetime.now()
    
    def _handle_account_update(
        self,
        value: object
    ):
        """Handle IB account updates."""
        # Implement account update handling
        pass
    
    def _convert_order_status(self, status: str) -> OrderStatus:
        """Convert IB order status."""
        mapping = {
            'PendingSubmit': OrderStatus.PENDING,
            'PendingCancel': OrderStatus.PENDING,
            'PreSubmitted': OrderStatus.PENDING,
            'Submitted': OrderStatus.OPEN,
            'Filled': OrderStatus.FILLED,
            'Cancelled': OrderStatus.CANCELLED,
            'Inactive': OrderStatus.EXPIRED
        }
        return mapping.get(status, OrderStatus.PENDING)
