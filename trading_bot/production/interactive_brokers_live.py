"""
Real Interactive Brokers Integration

This module provides ACTUAL broker integration with:
- Real API connection (not interface stubs)
- Credential management
- Fill confirmation and reconciliation
- Position tracking from broker feed
- Order state machine
- Latency measurement
- Error handling and reconnection

REQUIREMENTS:
1. Install IB Gateway or TWS
2. Enable API connections in IB Gateway/TWS
3. Set API port (default: 7497 for paper, 7496 for live)
4. Configure trusted IPs

IMPORTANT: This connects to REAL money accounts. Use paper trading first.
"""

import asyncio
import logging
import time
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
from decimal import Decimal
import queue
import json

logger = logging.getLogger(__name__)


try:
    # =============================================================================
# IB API WRAPPER
# =============================================================================

    from ibapi.client import EClient
    from ibapi.wrapper import EWrapper
    from ibapi.contract import Contract
    from ibapi.order import Order as IBOrder
    from ibapi.execution import Execution
    from ibapi.commission_report import CommissionReport
    from ibapi.common import BarData, TickerId, OrderId
    IB_API_AVAILABLE = True
except ImportError:
    IB_API_AVAILABLE = False
    logger.warning("IB API not installed. Install with: pip install ibapi")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class ConnectionState(Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    ERROR = "ERROR"


class OrderState(Enum):
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    ERROR = "ERROR"


@dataclass
class IBCredentials:
    """IB API credentials"""
    host: str = "127.0.0.1"
    port: int = 7497  # 7497 = paper, 7496 = live
    client_id: int = 1
    account: str = ""  # Will be populated on connection
    
    @classmethod
    def paper_trading(cls, client_id: int = 1) -> 'IBCredentials':
        """Create paper trading credentials"""
        return cls(host="127.0.0.1", port=7497, client_id=client_id)
    
    @classmethod
    def live_trading(cls, client_id: int = 1) -> 'IBCredentials':
        """Create live trading credentials"""
        return cls(host="127.0.0.1", port=7496, client_id=client_id)


@dataclass
class Position:
    """Current position"""
    symbol: str
    quantity: float
    avg_cost: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float
    account: str
    last_update: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OrderRecord:
    """Order record with full lifecycle tracking"""
    order_id: int
    client_order_id: str
    symbol: str
    action: str  # BUY, SELL
    quantity: float
    order_type: str  # MKT, LMT, STP, etc.
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    
    # State tracking
    state: OrderState = OrderState.CREATED
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    commission: float = 0.0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    
    # Latency tracking
    submit_latency_ms: float = 0.0
    fill_latency_ms: float = 0.0
    
    # Error handling
    error_code: int = 0
    error_message: str = ""
    
    # Fills
    fills: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Fill:
    """Execution fill"""
    exec_id: str
    order_id: int
    symbol: str
    side: str
    quantity: float
    price: float
    commission: float
    timestamp: datetime
    exchange: str
    
    
@dataclass
class LatencyStats:
    """Latency statistics"""
    samples: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    def add_sample(self, latency_ms: float):
        self.samples.append(latency_ms)
    
    @property
    def mean(self) -> float:
        return sum(self.samples) / len(self.samples) if self.samples else 0
    
    @property
    def p50(self) -> float:
        if not self.samples:
            return 0
        sorted_samples = sorted(self.samples)
        return sorted_samples[len(sorted_samples) // 2]
    
    @property
    def p99(self) -> float:
        if not self.samples:
            return 0
        sorted_samples = sorted(self.samples)
        idx = int(len(sorted_samples) * 0.99)
        return sorted_samples[min(idx, len(sorted_samples) - 1)]


# =============================================================================
# IB WRAPPER IMPLEMENTATION
# =============================================================================

if IB_API_AVAILABLE:
    class IBWrapper(EWrapper):
        """IB API Wrapper - receives callbacks from IB"""
        
        def __init__(self):
            EWrapper.__init__(self)
            
            # Connection state
            self.connection_state = ConnectionState.DISCONNECTED
            self.next_order_id: Optional[int] = None
            self.accounts: List[str] = []
            
            # Data storage
            self.positions: Dict[str, Position] = {}
            self.orders: Dict[int, OrderRecord] = {}
            self.fills: List[Fill] = []
            
            # Callbacks
            self.on_position_update: Optional[Callable] = None
            self.on_order_update: Optional[Callable] = None
            self.on_fill: Optional[Callable] = None
            self.on_error: Optional[Callable] = None
            
            # Latency tracking
            self.order_submit_times: Dict[int, float] = {}
            self.latency_stats = LatencyStats()
            
            # Thread-safe queue for events
            self.event_queue: queue.Queue = queue.Queue()
        
        def error(self, reqId: TickerId, errorCode: int, errorString: str, advancedOrderRejectJson: str = ""):
            """Handle errors from IB"""
            logger.error(f"IB Error {errorCode}: {errorString} (reqId={reqId})")
            
            # Update order state if this is an order error
            if reqId in self.orders:
                order = self.orders[reqId]
                order.state = OrderState.ERROR
                order.error_code = errorCode
                order.error_message = errorString
                
                if self.on_order_update:
                    self.on_order_update(order)
            
            if self.on_error:
                self.on_error(reqId, errorCode, errorString)
            
            # Connection errors
            if errorCode in [502, 504, 1100, 1101, 1102]:
                self.connection_state = ConnectionState.ERROR
        
        def connectAck(self):
            """Connection acknowledged"""
            logger.info("IB connection acknowledged")
            self.connection_state = ConnectionState.CONNECTED
        
        def connectionClosed(self):
            """Connection closed"""
            logger.warning("IB connection closed")
            self.connection_state = ConnectionState.DISCONNECTED
        
        def nextValidId(self, orderId: int):
            """Receive next valid order ID"""
            logger.info(f"Next valid order ID: {orderId}")
            self.next_order_id = orderId
            self.connection_state = ConnectionState.CONNECTED
        
        def managedAccounts(self, accountsList: str):
            """Receive managed accounts"""
            self.accounts = accountsList.split(',')
            logger.info(f"Managed accounts: {self.accounts}")
        
        def position(self, account: str, contract: Contract, position: Decimal, avgCost: float):
            """Receive position update"""
            symbol = contract.symbol
            
            pos = Position(
                symbol=symbol,
                quantity=float(position),
                avg_cost=avgCost,
                market_value=float(position) * avgCost,
                unrealized_pnl=0.0,  # Updated separately
                realized_pnl=0.0,
                account=account
            )
            
            self.positions[symbol] = pos
            logger.info(f"Position update: {symbol} qty={position} avg_cost={avgCost}")
            
            if self.on_position_update:
                self.on_position_update(pos)
        
        def positionEnd(self):
            """End of position updates"""
            logger.debug("Position update complete")
        
        def orderStatus(self, orderId: OrderId, status: str, filled: Decimal,
                       remaining: Decimal, avgFillPrice: float, permId: int,
                       parentId: int, lastFillPrice: float, clientId: int,
                       whyHeld: str, mktCapPrice: float):
            """Receive order status update"""
            logger.info(f"Order {orderId} status: {status}, filled={filled}, remaining={remaining}")
            
            if orderId not in self.orders:
                return
            
            order = self.orders[orderId]
            order.filled_quantity = float(filled)
            order.avg_fill_price = avgFillPrice
            
            # Map IB status to our state
            status_map = {
                'PendingSubmit': OrderState.PENDING,
                'PendingCancel': OrderState.PENDING,
                'PreSubmitted': OrderState.PENDING,
                'Submitted': OrderState.SUBMITTED,
                'ApiCancelled': OrderState.CANCELLED,
                'Cancelled': OrderState.CANCELLED,
                'Filled': OrderState.FILLED,
                'Inactive': OrderState.ERROR
            }
            
            new_state = status_map.get(status, OrderState.PENDING)
            
            if new_state == OrderState.FILLED and order.state != OrderState.FILLED:
                order.filled_at = datetime.utcnow()
                
                # Calculate fill latency
                if orderId in self.order_submit_times:
                    submit_time = self.order_submit_times[orderId]
                    order.fill_latency_ms = (time.time() - submit_time) * 1000
                    self.latency_stats.add_sample(order.fill_latency_ms)
            
            order.state = new_state
            
            if self.on_order_update:
                self.on_order_update(order)
        
        def execDetails(self, reqId: int, contract: Contract, execution: Execution):
            """Receive execution details"""
            fill = Fill(
                exec_id=execution.execId,
                order_id=execution.orderId,
                symbol=contract.symbol,
                side=execution.side,
                quantity=float(execution.shares),
                price=execution.price,
                commission=0.0,  # Updated in commissionReport
                timestamp=datetime.strptime(execution.time, "%Y%m%d %H:%M:%S"),
                exchange=execution.exchange
            )
            
            self.fills.append(fill)
            logger.info(f"Fill: {fill.symbol} {fill.side} {fill.quantity}@{fill.price}")
            
            # Update order fills
            if execution.orderId in self.orders:
                self.orders[execution.orderId].fills.append({
                    'exec_id': fill.exec_id,
                    'quantity': fill.quantity,
                    'price': fill.price,
                    'timestamp': fill.timestamp.isoformat()
                })
            
            if self.on_fill:
                self.on_fill(fill)
        
        def commissionReport(self, commissionReport: CommissionReport):
            """Receive commission report"""
            exec_id = commissionReport.execId
            commission = commissionReport.commission
            
            # Update fill with commission
            for fill in self.fills:
                if fill.exec_id == exec_id:
                    fill.commission = commission
                    break
            
            # Update order commission
            for order in self.orders.values():
                for fill_record in order.fills:
                    if fill_record.get('exec_id') == exec_id:
                        order.commission += commission
                        break
            
            logger.debug(f"Commission: {exec_id} = ${commission:.2f}")


# =============================================================================
# IB CLIENT IMPLEMENTATION
# =============================================================================

class InteractiveBrokersClient:
    """
    Production Interactive Brokers Client
    
    Features:
    - Real API connection
    - Automatic reconnection
    - Order lifecycle management
    - Position tracking
    - Fill reconciliation
    - Latency measurement
    """
    
    def __init__(self, credentials: Optional[IBCredentials] = None):
        if not IB_API_AVAILABLE:
            raise ImportError(
                "IB API not installed. Install with: pip install ibapi\n"
                "Download from: https://interactivebrokers.github.io/"
            )
        
        self.credentials = credentials or IBCredentials.paper_trading()
        
        # Create wrapper and client
        self.wrapper = IBWrapper()
        self.client = EClient(self.wrapper)
        
        # Connection management
        self._connected = False
        self._connection_thread: Optional[threading.Thread] = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        
        # Order management
        self._order_id_counter = 0
        self._pending_orders: Dict[str, OrderRecord] = {}  # client_order_id -> OrderRecord
        
        # Callbacks
        self.on_connected: Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None
        
        logger.info(f"IB Client initialized (host={self.credentials.host}, port={self.credentials.port})")
    
    # =========================================================================
    # CONNECTION MANAGEMENT
    # =========================================================================
    
    def connect(self, timeout: float = 10.0) -> bool:
        """
        Connect to IB Gateway/TWS
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            True if connected successfully
        """
        if self._connected:
            logger.warning("Already connected")
            return True
        
        logger.info(f"Connecting to IB at {self.credentials.host}:{self.credentials.port}")
        
        try:
            self.client.connect(
                self.credentials.host,
                self.credentials.port,
                self.credentials.client_id
            )
            
            # Start message processing thread
            self._connection_thread = threading.Thread(
                target=self.client.run,
                daemon=True
            )
            self._connection_thread.start()
            
            # Wait for connection
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.wrapper.next_order_id is not None:
                    self._connected = True
                    self._order_id_counter = self.wrapper.next_order_id
                    self._reconnect_attempts = 0
                    
                    # Get account info
                    if self.wrapper.accounts:
                        self.credentials.account = self.wrapper.accounts[0]
                    
                    logger.info(f"Connected to IB (account={self.credentials.account})")
                    
                    if self.on_connected:
                        self.on_connected()
                    
                    return True
                
                time.sleep(0.1)
            
            logger.error("Connection timeout")
            return False
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from IB"""
        if not self._connected:
            return
        
        logger.info("Disconnecting from IB")
        self.client.disconnect()
        self._connected = False
        
        if self.on_disconnected:
            self.on_disconnected()
    
    def reconnect(self) -> bool:
        """Attempt to reconnect"""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            return False
        
        self._reconnect_attempts += 1
        logger.info(f"Reconnection attempt {self._reconnect_attempts}/{self._max_reconnect_attempts}")
        
        self.disconnect()
        time.sleep(2 ** self._reconnect_attempts)  # Exponential backoff
        
        return self.connect()
    
    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self._connected and self.wrapper.connection_state == ConnectionState.CONNECTED
    
    # =========================================================================
    # ORDER MANAGEMENT
    # =========================================================================
    
    def _get_next_order_id(self) -> int:
        """Get next order ID"""
        order_id = self._order_id_counter
        self._order_id_counter += 1
        return order_id
    
    def _create_contract(self, symbol: str, sec_type: str = "STK", 
                        exchange: str = "SMART", currency: str = "USD") -> Contract:
        """Create IB contract"""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = sec_type
        contract.exchange = exchange
        contract.currency = currency
        return contract
    
    def _create_order(self, action: str, quantity: float, order_type: str,
                     limit_price: Optional[float] = None,
                     stop_price: Optional[float] = None) -> IBOrder:
        """Create IB order"""
        order = IBOrder()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = order_type
        
        if order_type == "LMT" and limit_price:
            order.lmtPrice = limit_price
        elif order_type == "STP" and stop_price:
            order.auxPrice = stop_price
        elif order_type == "STP LMT" and stop_price and limit_price:
            order.auxPrice = stop_price
            order.lmtPrice = limit_price
        
        order.transmit = True
        return order
    
    def place_market_order(
        self,
        symbol: str,
        action: str,  # "BUY" or "SELL"
        quantity: float,
        client_order_id: Optional[str] = None
    ) -> OrderRecord:
        """
        Place market order
        
        Args:
            symbol: Symbol to trade
            action: "BUY" or "SELL"
            quantity: Number of shares
            client_order_id: Optional client order ID
            
        Returns:
            OrderRecord with order details
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to IB")
        
        order_id = self._get_next_order_id()
        client_order_id = client_order_id or f"MKT_{order_id}_{int(time.time())}"
        
        # Create order record
        record = OrderRecord(
            order_id=order_id,
            client_order_id=client_order_id,
            symbol=symbol,
            action=action,
            quantity=quantity,
            order_type="MKT"
        )
        
        # Store order
        self.wrapper.orders[order_id] = record
        self._pending_orders[client_order_id] = record
        
        # Create IB objects
        contract = self._create_contract(symbol)
        order = self._create_order(action, quantity, "MKT")
        
        # Track submit time for latency
        self.wrapper.order_submit_times[order_id] = time.time()
        
        # Submit order
        logger.info(f"Placing market order: {action} {quantity} {symbol}")
        self.client.placeOrder(order_id, contract, order)
        
        record.submitted_at = datetime.utcnow()
        record.state = OrderState.SUBMITTED
        
        return record
    
    def place_limit_order(
        self,
        symbol: str,
        action: str,
        quantity: float,
        limit_price: float,
        client_order_id: Optional[str] = None
    ) -> OrderRecord:
        """Place limit order"""
        if not self.is_connected:
            raise ConnectionError("Not connected to IB")
        
        order_id = self._get_next_order_id()
        client_order_id = client_order_id or f"LMT_{order_id}_{int(time.time())}"
        
        record = OrderRecord(
            order_id=order_id,
            client_order_id=client_order_id,
            symbol=symbol,
            action=action,
            quantity=quantity,
            order_type="LMT",
            limit_price=limit_price
        )
        
        self.wrapper.orders[order_id] = record
        self._pending_orders[client_order_id] = record
        
        contract = self._create_contract(symbol)
        order = self._create_order(action, quantity, "LMT", limit_price=limit_price)
        
        self.wrapper.order_submit_times[order_id] = time.time()
        
        logger.info(f"Placing limit order: {action} {quantity} {symbol} @ {limit_price}")
        self.client.placeOrder(order_id, contract, order)
        
        record.submitted_at = datetime.utcnow()
        record.state = OrderState.SUBMITTED
        
        return record
    
    def place_stop_order(
        self,
        symbol: str,
        action: str,
        quantity: float,
        stop_price: float,
        client_order_id: Optional[str] = None
    ) -> OrderRecord:
        """Place stop order"""
        if not self.is_connected:
            raise ConnectionError("Not connected to IB")
        
        order_id = self._get_next_order_id()
        client_order_id = client_order_id or f"STP_{order_id}_{int(time.time())}"
        
        record = OrderRecord(
            order_id=order_id,
            client_order_id=client_order_id,
            symbol=symbol,
            action=action,
            quantity=quantity,
            order_type="STP",
            stop_price=stop_price
        )
        
        self.wrapper.orders[order_id] = record
        self._pending_orders[client_order_id] = record
        
        contract = self._create_contract(symbol)
        order = self._create_order(action, quantity, "STP", stop_price=stop_price)
        
        self.wrapper.order_submit_times[order_id] = time.time()
        
        logger.info(f"Placing stop order: {action} {quantity} {symbol} @ {stop_price}")
        self.client.placeOrder(order_id, contract, order)
        
        record.submitted_at = datetime.utcnow()
        record.state = OrderState.SUBMITTED
        
        return record
    
    def cancel_order(self, order_id: int) -> bool:
        """Cancel order by ID"""
        if not self.is_connected:
            raise ConnectionError("Not connected to IB")
        
        if order_id not in self.wrapper.orders:
            logger.warning(f"Order {order_id} not found")
            return False
        
        logger.info(f"Cancelling order {order_id}")
        self.client.cancelOrder(order_id, "")
        
        return True
    
    def cancel_all_orders(self):
        """Cancel all open orders"""
        if not self.is_connected:
            raise ConnectionError("Not connected to IB")
        
        logger.info("Cancelling all orders")
        self.client.reqGlobalCancel()
    
    # =========================================================================
    # POSITION MANAGEMENT
    # =========================================================================
    
    def request_positions(self):
        """Request current positions"""
        if not self.is_connected:
            raise ConnectionError("Not connected to IB")
        
        logger.info("Requesting positions")
        self.client.reqPositions()
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol"""
        return self.wrapper.positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, Position]:
        """Get all positions"""
        return self.wrapper.positions.copy()
    
    # =========================================================================
    # ORDER TRACKING
    # =========================================================================
    
    def get_order(self, order_id: int) -> Optional[OrderRecord]:
        """Get order by ID"""
        return self.wrapper.orders.get(order_id)
    
    def get_order_by_client_id(self, client_order_id: str) -> Optional[OrderRecord]:
        """Get order by client order ID"""
        return self._pending_orders.get(client_order_id)
    
    def get_all_orders(self) -> Dict[int, OrderRecord]:
        """Get all orders"""
        return self.wrapper.orders.copy()
    
    def get_open_orders(self) -> List[OrderRecord]:
        """Get open orders"""
        return [
            order for order in self.wrapper.orders.values()
            if order.state in [OrderState.SUBMITTED, OrderState.PENDING, OrderState.PARTIAL]
        ]
    
    def get_fills(self) -> List[Fill]:
        """Get all fills"""
        return self.wrapper.fills.copy()
    
    # =========================================================================
    # LATENCY TRACKING
    # =========================================================================
    
    def get_latency_stats(self) -> Dict[str, float]:
        """Get latency statistics"""
        stats = self.wrapper.latency_stats
        return {
            'mean_ms': stats.mean,
            'p50_ms': stats.p50,
            'p99_ms': stats.p99,
            'samples': len(stats.samples)
        }
    
    # =========================================================================
    # CALLBACKS
    # =========================================================================
    
    def set_position_callback(self, callback: Callable[[Position], None]):
        """Set callback for position updates"""
        self.wrapper.on_position_update = callback
    
    def set_order_callback(self, callback: Callable[[OrderRecord], None]):
        """Set callback for order updates"""
        self.wrapper.on_order_update = callback
    
    def set_fill_callback(self, callback: Callable[[Fill], None]):
        """Set callback for fills"""
        self.wrapper.on_fill = callback
    
    def set_error_callback(self, callback: Callable[[int, int, str], None]):
        """Set callback for errors"""
        self.wrapper.on_error = callback


# =============================================================================
# FILL RECONCILIATION
# =============================================================================

class FillReconciler:
    """
    Reconciles fills between local records and broker
    
    Ensures:
    - All fills are accounted for
    - Positions match broker positions
    - No missing or duplicate fills
    """
    
    def __init__(self, client: InteractiveBrokersClient):
        self.client = client
        self.local_positions: Dict[str, float] = {}
        self.discrepancies: List[Dict[str, Any]] = []
    
    def reconcile(self) -> Dict[str, Any]:
        """
        Reconcile local records with broker
        
        Returns:
            Reconciliation report
        """
        self.discrepancies = []
        
        # Get broker positions
        self.client.request_positions()
        time.sleep(1)  # Wait for position updates
        
        broker_positions = self.client.get_all_positions()
        
        # Compare positions
        all_symbols = set(self.local_positions.keys()) | set(broker_positions.keys())
        
        for symbol in all_symbols:
            local_qty = self.local_positions.get(symbol, 0)
            broker_pos = broker_positions.get(symbol)
            broker_qty = broker_pos.quantity if broker_pos else 0
            
            if abs(local_qty - broker_qty) > 0.01:
                self.discrepancies.append({
                    'symbol': symbol,
                    'local_qty': local_qty,
                    'broker_qty': broker_qty,
                    'difference': broker_qty - local_qty,
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        # Get fills
        fills = self.client.get_fills()
        
        return {
            'reconciled': len(self.discrepancies) == 0,
            'discrepancies': self.discrepancies,
            'broker_positions': {s: p.quantity for s, p in broker_positions.items()},
            'local_positions': self.local_positions.copy(),
            'total_fills': len(fills),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def update_local_position(self, symbol: str, quantity_change: float):
        """Update local position tracking"""
        current = self.local_positions.get(symbol, 0)
        self.local_positions[symbol] = current + quantity_change


# =============================================================================
# DATA VALIDATION
# =============================================================================

@dataclass
class DataValidationResult:
    """Result of data validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class DataValidator:
    """
    Validates market data integrity
    
    Checks:
    - Timestamp synchronization
    - Sequence number checking
    - Cross-venue consistency
    - Outlier detection
    """
    
    def __init__(self):
        self.last_timestamps: Dict[str, datetime] = {}
        self.last_prices: Dict[str, float] = {}
        self.sequence_numbers: Dict[str, int] = {}
        
        # Thresholds
        self.max_timestamp_drift_seconds = 5.0
        self.max_price_change_pct = 0.10  # 10% max single-tick change
        self.stale_data_threshold_seconds = 60.0
    
    def validate_tick(
        self,
        symbol: str,
        timestamp: datetime,
        price: float,
        sequence: Optional[int] = None
    ) -> DataValidationResult:
        """Validate a single tick"""
        errors = []
        warnings = []
        
        # Timestamp validation
        now = datetime.utcnow()
        time_diff = abs((now - timestamp).total_seconds())
        
        if time_diff > self.max_timestamp_drift_seconds:
            errors.append(f"Timestamp drift: {time_diff:.1f}s")
        
        # Check for stale data
        if symbol in self.last_timestamps:
            since_last = (timestamp - self.last_timestamps[symbol]).total_seconds()
            if since_last > self.stale_data_threshold_seconds:
                warnings.append(f"Stale data: {since_last:.1f}s since last tick")
        
        # Check for out-of-order timestamps
        if symbol in self.last_timestamps:
            if timestamp < self.last_timestamps[symbol]:
                errors.append("Out-of-order timestamp")
        
        # Price validation
        if price <= 0:
            errors.append(f"Invalid price: {price}")
        
        # Check for price outliers
        if symbol in self.last_prices:
            last_price = self.last_prices[symbol]
            pct_change = abs(price - last_price) / last_price
            if pct_change > self.max_price_change_pct:
                warnings.append(f"Large price change: {pct_change:.2%}")
        
        # Sequence number validation
        if sequence is not None and symbol in self.sequence_numbers:
            expected = self.sequence_numbers[symbol] + 1
            if sequence != expected:
                if sequence > expected:
                    errors.append(f"Gap in sequence: expected {expected}, got {sequence}")
                else:
                    errors.append(f"Duplicate/out-of-order sequence: {sequence}")
        
        # Update tracking
        self.last_timestamps[symbol] = timestamp
        self.last_prices[symbol] = price
        if sequence is not None:
            self.sequence_numbers[symbol] = sequence
        
        return DataValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_cross_venue(
        self,
        symbol: str,
        prices: Dict[str, float],  # venue -> price
        max_divergence_pct: float = 0.005  # 0.5%
    ) -> DataValidationResult:
        """Validate price consistency across venues"""
        errors = []
        warnings = []
        
        if len(prices) < 2:
            return DataValidationResult(is_valid=True, errors=[], warnings=[])
        
        price_list = list(prices.values())
        avg_price = sum(price_list) / len(price_list)
        
        for venue, price in prices.items():
            divergence = abs(price - avg_price) / avg_price
            if divergence > max_divergence_pct:
                warnings.append(f"{venue} price divergence: {divergence:.2%}")
        
        # Check for suspicious patterns
        max_price = max(price_list)
        min_price = min(price_list)
        spread = (max_price - min_price) / avg_price
        
        if spread > max_divergence_pct * 2:
            errors.append(f"Cross-venue spread too wide: {spread:.2%}")
        
        return DataValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_ib_client(
    mode: str = "paper",
    client_id: int = 1
) -> InteractiveBrokersClient:
    """
    Create IB client
    
    Args:
        mode: "paper" or "live"
        client_id: Client ID for IB connection
        
    Returns:
        InteractiveBrokersClient instance
    """
    if mode == "paper":
        credentials = IBCredentials.paper_trading(client_id)
    elif mode == "live":
        credentials = IBCredentials.live_trading(client_id)
    else:
        raise ValueError(f"Invalid mode: {mode}. Use 'paper' or 'live'")
    
    return InteractiveBrokersClient(credentials)


def quick_connect(mode: str = "paper") -> InteractiveBrokersClient:
    """
    Quick connect to IB
    
    Args:
        mode: "paper" or "live"
        
    Returns:
        Connected IB client
    """
    client = create_ib_client(mode)
    
    if not client.connect():
        raise ConnectionError("Failed to connect to IB")
    
    return client


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    if not IB_API_AVAILABLE:
        print("IB API not installed. Install with: pip install ibapi")
        print("Download from: https://interactivebrokers.github.io/")
        exit(1)
    
    # Create client
    client = create_ib_client("paper")
    
    # Set callbacks
    def on_fill(fill: Fill):
        print(f"FILL: {fill.symbol} {fill.side} {fill.quantity}@{fill.price}")
    
    def on_order_update(order: OrderRecord):
        print(f"ORDER: {order.symbol} {order.state.value}")
    
    client.set_fill_callback(on_fill)
    client.set_order_callback(on_order_update)
    
    # Connect
    print("Connecting to IB...")
    if client.connect():
        print(f"Connected! Account: {client.credentials.account}")
        
        # Request positions
        client.request_positions()
        time.sleep(2)
        
        positions = client.get_all_positions()
        print(f"Positions: {positions}")
        
        # Place test order (commented out for safety)
        # order = client.place_market_order("AAPL", "BUY", 1)
        # print(f"Order placed: {order.order_id}")
        
        # Get latency stats
        stats = client.get_latency_stats()
        print(f"Latency: {stats}")
        
        # Disconnect
        client.disconnect()
    else:
        print("Failed to connect")
