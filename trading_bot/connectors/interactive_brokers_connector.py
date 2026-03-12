"""
Interactive Brokers Connector
=============================

Full-featured IB connector with:
- TWS/Gateway connection
- Real-time market data
- Order execution
- Account management
- Options support
- Futures support

Author: Elite Trading Bot
Version: 1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum, auto
import threading
from collections import defaultdict
import queue

logger = logging.getLogger(__name__)

# Try to import IB API
try:
    from ibapi.client import EClient
    from ibapi.wrapper import EWrapper
    from ibapi.contract import Contract, ContractDetails
    from ibapi.order import Order as IBOrder
    from ibapi.execution import Execution
    from ibapi.common import BarData, TickerId, TickType
    IB_AVAILABLE = True
except ImportError:
    IB_AVAILABLE = False
    logger.debug("ibapi not installed. Install with: pip install ibapi")


class IBOrderType(Enum):
    """IB Order types"""
    MARKET = "MKT"
    LIMIT = "LMT"
    STOP = "STP"
    STOP_LIMIT = "STP LMT"
    TRAILING_STOP = "TRAIL"
    TRAILING_STOP_LIMIT = "TRAIL LIMIT"
    MOC = "MOC"  # Market on Close
    LOC = "LOC"  # Limit on Close
    MIT = "MIT"  # Market if Touched


class IBSecurityType(Enum):
    """IB Security types"""
    STOCK = "STK"
    OPTION = "OPT"
    FUTURE = "FUT"
    FOREX = "CASH"
    INDEX = "IND"
    CFD = "CFD"
    BOND = "BOND"
    COMMODITY = "CMDTY"
    CRYPTO = "CRYPTO"


@dataclass
class IBPosition:
    """IB Position data"""
    account: str
    symbol: str
    security_type: str
    exchange: str
    currency: str
    quantity: float
    avg_cost: float
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


@dataclass
class IBOrder:
    """IB Order data"""
    order_id: int
    client_id: int
    perm_id: int
    symbol: str
    action: str  # BUY or SELL
    order_type: str
    quantity: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    status: str = "Submitted"
    filled: float = 0.0
    remaining: float = 0.0
    avg_fill_price: float = 0.0
    commission: float = 0.0


@dataclass
class IBAccountInfo:
    """IB Account information"""
    account_id: str
    net_liquidation: float = 0.0
    total_cash: float = 0.0
    buying_power: float = 0.0
    gross_position_value: float = 0.0
    maintenance_margin: float = 0.0
    available_funds: float = 0.0
    excess_liquidity: float = 0.0
    cushion: float = 0.0
    day_trades_remaining: int = 0
    leverage: float = 0.0


class IBWrapper(EWrapper if IB_AVAILABLE else object):
    """IB API Wrapper for handling callbacks"""
    
    def __init__(self):
        if IB_AVAILABLE:
            super().__init__()
        
        # Data storage
        self.positions: Dict[str, IBPosition] = {}
        self.orders: Dict[int, IBOrder] = {}
        self.account_info = IBAccountInfo(account_id="")
        self.contract_details: Dict[int, ContractDetails] = {}
        
        # Market data
        self.tickers: Dict[int, Dict[str, Any]] = defaultdict(dict)
        self.bars: Dict[int, List[Dict]] = defaultdict(list)
        
        # Callbacks
        self.on_position_update: List[Callable] = []
        self.on_order_update: List[Callable] = []
        self.on_tick: List[Callable] = []
        self.on_bar: List[Callable] = []
        self.on_error: List[Callable] = []
        
        # Request tracking
        self.next_order_id = 0
        self.next_req_id = 1
        
        # Event queues
        self.data_queue = queue.Queue()
        
    def nextValidId(self, orderId: int):
        """Callback for next valid order ID"""
        self.next_order_id = orderId
        logger.info(f"Next valid order ID: {orderId}")
    
    def error(self, reqId: int, errorCode: int, errorString: str, advancedOrderRejectJson: str = ""):
        """Error callback"""
        if errorCode in [2104, 2106, 2158]:  # Connection messages
            logger.info(f"IB: {errorString}")
        else:
            logger.error(f"IB Error {errorCode}: {errorString}")
            for callback in self.on_error:
                callback(reqId, errorCode, errorString)
    
    def position(self, account: str, contract, pos: float, avgCost: float):
        """Position callback"""
        if IB_AVAILABLE:
            position = IBPosition(
                account=account,
                symbol=contract.symbol,
                security_type=contract.secType,
                exchange=contract.exchange,
                currency=contract.currency,
                quantity=pos,
                avg_cost=avgCost
            )
            self.positions[f"{contract.symbol}_{contract.secType}"] = position
            
            for callback in self.on_position_update:
                callback(position)
    
    def positionEnd(self):
        """End of position updates"""
        logger.debug("Position update complete")
    
    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        """Account summary callback"""
        self.account_info.account_id = account
        
        try:
            val = float(value)
        except ValueError:
            val = value
        
        if tag == "NetLiquidation":
            self.account_info.net_liquidation = val
        elif tag == "TotalCashValue":
            self.account_info.total_cash = val
        elif tag == "BuyingPower":
            self.account_info.buying_power = val
        elif tag == "GrossPositionValue":
            self.account_info.gross_position_value = val
        elif tag == "MaintMarginReq":
            self.account_info.maintenance_margin = val
        elif tag == "AvailableFunds":
            self.account_info.available_funds = val
        elif tag == "ExcessLiquidity":
            self.account_info.excess_liquidity = val
        elif tag == "Cushion":
            self.account_info.cushion = val
        elif tag == "DayTradesRemaining":
            self.account_info.day_trades_remaining = int(val)
        elif tag == "Leverage-S":
            self.account_info.leverage = val
    
    def accountSummaryEnd(self, reqId: int):
        """End of account summary"""
        logger.debug("Account summary complete")
    
    def orderStatus(self, orderId: int, status: str, filled: float, remaining: float,
                    avgFillPrice: float, permId: int, parentId: int, lastFillPrice: float,
                    clientId: int, whyHeld: str, mktCapPrice: float):
        """Order status callback"""
        if orderId in self.orders:
            order = self.orders[orderId]
            order.status = status
            order.filled = filled
            order.remaining = remaining
            order.avg_fill_price = avgFillPrice
            order.perm_id = permId
            
            for callback in self.on_order_update:
                callback(order)
    
    def openOrder(self, orderId: int, contract, order, orderState):
        """Open order callback"""
        if IB_AVAILABLE:
            ib_order = IBOrder(
                order_id=orderId,
                client_id=order.clientId,
                perm_id=order.permId,
                symbol=contract.symbol,
                action=order.action,
                order_type=order.orderType,
                quantity=order.totalQuantity,
                limit_price=order.lmtPrice if order.lmtPrice != 0 else None,
                stop_price=order.auxPrice if order.auxPrice != 0 else None,
                status=orderState.status,
                commission=orderState.commission if orderState.commission != 1.7976931348623157e+308 else 0
            )
            self.orders[orderId] = ib_order
    
    def tickPrice(self, reqId: int, tickType: int, price: float, attrib):
        """Tick price callback"""
        if IB_AVAILABLE:
            tick_name = TickType.toStr(tickType)
            self.tickers[reqId][tick_name] = price
            self.tickers[reqId]['timestamp'] = datetime.now()
            
            for callback in self.on_tick:
                callback(reqId, tick_name, price)
    
    def tickSize(self, reqId: int, tickType: int, size: int):
        """Tick size callback"""
        if IB_AVAILABLE:
            tick_name = TickType.toStr(tickType)
            self.tickers[reqId][f"{tick_name}_size"] = size
    
    def historicalData(self, reqId: int, bar):
        """Historical data callback"""
        if IB_AVAILABLE:
            bar_data = {
                'timestamp': bar.date,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'wap': bar.wap,
                'count': bar.barCount
            }
            self.bars[reqId].append(bar_data)
    
    def historicalDataEnd(self, reqId: int, start: str, end: str):
        """End of historical data"""
        logger.debug(f"Historical data complete for request {reqId}")
    
    def contractDetails(self, reqId: int, contractDetails):
        """Contract details callback"""
        self.contract_details[reqId] = contractDetails
    
    def contractDetailsEnd(self, reqId: int):
        """End of contract details"""
        logger.debug(f"Contract details complete for request {reqId}")


class IBClient(EClient if IB_AVAILABLE else object):
    """IB API Client for sending requests"""
    
    def __init__(self, wrapper):
        if IB_AVAILABLE:
            super().__init__(wrapper)


class InteractiveBrokersConnector:
    """
    Interactive Brokers Connector
    
    Provides full access to IB TWS/Gateway for:
    - Stocks, Options, Futures, Forex
    - Real-time and historical data
    - Order execution
    - Account management
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.host = config.get('host', '127.0.0.1')
        self.port = config.get('port', 7497)  # 7497 for TWS paper, 7496 for live
        self.client_id = config.get('client_id', 1)
        
        self.connected = False
        self.wrapper = None
        self.client = None
        self.thread = None
        
        # Request ID tracking
        self.next_req_id = 1
        self._req_id_lock = threading.Lock()
        
        # Symbol to request ID mapping
        self.symbol_req_map: Dict[str, int] = {}
        
        logger.info(f"IB Connector initialized: {self.host}:{self.port}")
    
    def _get_next_req_id(self) -> int:
        """Get next request ID"""
        with self._req_id_lock:
            req_id = self.next_req_id
            self.next_req_id += 1
            return req_id
    
    async def connect(self) -> bool:
        """Connect to IB TWS/Gateway"""
        if not IB_AVAILABLE:
            logger.error("ibapi not installed")
            return False
        try:
        
            self.wrapper = IBWrapper()
            self.client = IBClient(self.wrapper)
            
            self.client.connect(self.host, self.port, self.client_id)
            
            # Start message processing thread
            self.thread = threading.Thread(target=self.client.run, daemon=True)
            self.thread.start()
            
            # Wait for connection
            await asyncio.sleep(1)
            
            if self.client.isConnected():
                self.connected = True
                logger.info("Connected to Interactive Brokers")
                
                # Request account updates
                self.client.reqAccountSummary(
                    self._get_next_req_id(),
                    "All",
                    "NetLiquidation,TotalCashValue,BuyingPower,GrossPositionValue,"
                    "MaintMarginReq,AvailableFunds,ExcessLiquidity,Cushion,"
                    "DayTradesRemaining,Leverage-S"
                )
                
                # Request positions
                self.client.reqPositions()
                
                return True
            else:
                logger.error("Failed to connect to IB")
                return False
                
        except Exception as e:
            logger.error(f"IB connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from IB"""
        try:
            if self.client and self.client.isConnected():
                self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from Interactive Brokers")
            return True
        except Exception as e:
            logger.error(f"IB disconnect error: {e}")
            return False
    
    def _create_contract(
        self,
        symbol: str,
        sec_type: str = "STK",
        exchange: str = "SMART",
        currency: str = "USD",
        expiry: str = "",
        strike: float = 0.0,
        right: str = ""
    ) -> 'Contract':
        """Create an IB Contract object"""
        if not IB_AVAILABLE:
            return None
        
        contract = Contract()
        contract.symbol = symbol
        contract.secType = sec_type
        contract.exchange = exchange
        contract.currency = currency
        
        if sec_type in ["OPT", "FUT", "FOP"]:
            contract.lastTradeDateOrContractMonth = expiry
        
        if sec_type == "OPT":
            contract.strike = strike
            contract.right = right  # "C" for call, "P" for put
        
        return contract
    
    async def get_ticker(self, symbol: str, sec_type: str = "STK") -> Optional[Dict]:
        """Get current ticker data"""
        if not self.connected:
            return None
        
        contract = self._create_contract(symbol, sec_type)
        req_id = self._get_next_req_id()
        self.symbol_req_map[symbol] = req_id
        
        self.client.reqMktData(req_id, contract, "", False, False, [])
        
        # Wait for data
        await asyncio.sleep(0.5)
        
        ticker_data = self.wrapper.tickers.get(req_id, {})
        
        return {
            'symbol': symbol,
            'bid': ticker_data.get('BID', 0),
            'ask': ticker_data.get('ASK', 0),
            'last': ticker_data.get('LAST', 0),
            'volume': ticker_data.get('VOLUME_size', 0),
            'timestamp': ticker_data.get('timestamp', datetime.now())
        }
    
    async def get_historical_data(
        self,
        symbol: str,
        duration: str = "1 D",
        bar_size: str = "1 hour",
        sec_type: str = "STK",
        what_to_show: str = "TRADES"
    ) -> List[Dict]:
        """Get historical bar data"""
        if not self.connected:
            return []
        
        contract = self._create_contract(symbol, sec_type)
        req_id = self._get_next_req_id()
        
        self.client.reqHistoricalData(
            req_id,
            contract,
            "",  # End date/time (empty = now)
            duration,
            bar_size,
            what_to_show,
            1,  # Use RTH
            1,  # Format date
            False,  # Keep up to date
            []
        )
        
        # Wait for data
        await asyncio.sleep(2)
        
        return self.wrapper.bars.get(req_id, [])
    
    async def place_order(
        self,
        symbol: str,
        action: str,  # "BUY" or "SELL"
        quantity: float,
        order_type: str = "MKT",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        sec_type: str = "STK",
        tif: str = "DAY",
        **kwargs
    ) -> Optional[int]:
        """Place an order"""
        if not self.connected or not IB_AVAILABLE:
            return None
        
        contract = self._create_contract(symbol, sec_type)
        
        order = IBOrder()
        order.action = action.upper()
        order.totalQuantity = quantity
        order.orderType = order_type
        order.tif = tif
        
        if limit_price:
            order.lmtPrice = limit_price
        if stop_price:
            order.auxPrice = stop_price
        
        # Additional order attributes
        if kwargs.get('oca_group'):
            order.ocaGroup = kwargs['oca_group']
            order.ocaType = kwargs.get('oca_type', 1)
        
        if kwargs.get('parent_id'):
            order.parentId = kwargs['parent_id']
        
        order_id = self.wrapper.next_order_id
        self.wrapper.next_order_id += 1
        
        self.client.placeOrder(order_id, contract, order)
        
        logger.info(f"Order placed: {order_id} {action} {quantity} {symbol}")
        
        return order_id
    
    async def cancel_order(self, order_id: int) -> bool:
        """Cancel an order"""
        if not self.connected:
            return False
        try:
        
            self.client.cancelOrder(order_id, "")
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    async def get_positions(self) -> List[IBPosition]:
        """Get all positions"""
        if not self.connected:
            return []
        
        self.client.reqPositions()
        await asyncio.sleep(0.5)
        
        return list(self.wrapper.positions.values())
    
    async def get_account_info(self) -> Optional[IBAccountInfo]:
        """Get account information"""
        if not self.connected:
            return None
        
        return self.wrapper.account_info
    
    async def get_open_orders(self) -> List[IBOrder]:
        """Get all open orders"""
        if not self.connected:
            return []
        
        self.client.reqOpenOrders()
        await asyncio.sleep(0.5)
        
        return list(self.wrapper.orders.values())
    
    async def place_bracket_order(
        self,
        symbol: str,
        action: str,
        quantity: float,
        entry_price: Optional[float],
        stop_loss: float,
        take_profit: float,
        sec_type: str = "STK"
    ) -> Tuple[int, int, int]:
        """Place a bracket order (entry + stop loss + take profit)"""
        if not self.connected or not IB_AVAILABLE:
            return (0, 0, 0)
        
        contract = self._create_contract(symbol, sec_type)
        
        # Parent order
        parent_id = self.wrapper.next_order_id
        self.wrapper.next_order_id += 1
        
        parent = IBOrder()
        parent.orderId = parent_id
        parent.action = action.upper()
        parent.totalQuantity = quantity
        parent.orderType = "LMT" if entry_price else "MKT"
        if entry_price:
            parent.lmtPrice = entry_price
        parent.transmit = False
        
        # Stop loss order
        sl_id = self.wrapper.next_order_id
        self.wrapper.next_order_id += 1
        
        sl_order = IBOrder()
        sl_order.orderId = sl_id
        sl_order.action = "SELL" if action.upper() == "BUY" else "BUY"
        sl_order.totalQuantity = quantity
        sl_order.orderType = "STP"
        sl_order.auxPrice = stop_loss
        sl_order.parentId = parent_id
        sl_order.transmit = False
        
        # Take profit order
        tp_id = self.wrapper.next_order_id
        self.wrapper.next_order_id += 1
        
        tp_order = IBOrder()
        tp_order.orderId = tp_id
        tp_order.action = "SELL" if action.upper() == "BUY" else "BUY"
        tp_order.totalQuantity = quantity
        tp_order.orderType = "LMT"
        tp_order.lmtPrice = take_profit
        tp_order.parentId = parent_id
        tp_order.transmit = True  # Transmit all orders
        
        # Place orders
        self.client.placeOrder(parent_id, contract, parent)
        self.client.placeOrder(sl_id, contract, sl_order)
        self.client.placeOrder(tp_id, contract, tp_order)
        
        logger.info(f"Bracket order placed: parent={parent_id}, sl={sl_id}, tp={tp_id}")
        
        return (parent_id, sl_id, tp_id)
    
    async def place_oco_order(
        self,
        symbol: str,
        orders: List[Dict],
        sec_type: str = "STK"
    ) -> List[int]:
        """Place OCO (One-Cancels-Other) orders"""
        if not self.connected or not IB_AVAILABLE:
            return []
        
        contract = self._create_contract(symbol, sec_type)
        oca_group = f"OCA_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        order_ids = []
        
        for i, order_spec in enumerate(orders):
            order_id = self.wrapper.next_order_id
            self.wrapper.next_order_id += 1
            
            order = IBOrder()
            order.orderId = order_id
            order.action = order_spec['action'].upper()
            order.totalQuantity = order_spec['quantity']
            order.orderType = order_spec.get('order_type', 'LMT')
            order.lmtPrice = order_spec.get('limit_price', 0)
            order.auxPrice = order_spec.get('stop_price', 0)
            order.ocaGroup = oca_group
            order.ocaType = 1  # Cancel all remaining orders
            order.transmit = (i == len(orders) - 1)
            
            self.client.placeOrder(order_id, contract, order)
            order_ids.append(order_id)
        
        logger.info(f"OCO orders placed: {order_ids}")
        
        return order_ids
    
    def register_callback(self, event_type: str, callback: Callable):
        """Register a callback for events"""
        if self.wrapper:
            if event_type == 'position':
                self.wrapper.on_position_update.append(callback)
            elif event_type == 'order':
                self.wrapper.on_order_update.append(callback)
            elif event_type == 'tick':
                self.wrapper.on_tick.append(callback)
            elif event_type == 'bar':
                self.wrapper.on_bar.append(callback)
            elif event_type == 'error':
                self.wrapper.on_error.append(callback)


# Export
__all__ = [
    'InteractiveBrokersConnector',
    'IBWrapper',
    'IBClient',
    'IBPosition',
    'IBOrder',
    'IBAccountInfo',
    'IBOrderType',
    'IBSecurityType',
    'IB_AVAILABLE'
]
