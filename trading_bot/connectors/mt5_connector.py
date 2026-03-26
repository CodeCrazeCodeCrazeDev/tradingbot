"""MetaTrader 5 connector with resilient reconnect logic."""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import logging

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover
    mt5 = None

from .base_connector import (
    BaseConnector, ConnectionStatus, MarketData, 
    OrderBook, Trade, Ticker
)

logger = logging.getLogger(__name__)

class MT5Connector(BaseConnector):
    """
    MetaTrader 5 connector for forex and CFD trading
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        # SECURITY FIX: Validate MT5 configuration inputs
        self.account = self._validate_account(config.get('account'))
        self.password = self._validate_password(config.get('password'))
        self.server = self._validate_server(config.get('server'))
        self.mt5_path = self._validate_path(config.get('mt5_path'))
        
        # Symbol mapping
        self.symbol_mapping = {
            'EUR/USD': 'EURUSD',
            'GBP/USD': 'GBPUSD',
            'USD/JPY': 'USDJPY',
            'BTC/USD': 'BTCUSD',
            'GOLD': 'XAUUSD'
        }
        
        # Monitoring tasks
        self.monitoring_tasks = {}
        self._connect_lock = asyncio.Lock()
        self._monitor_task: Optional[asyncio.Task] = None
        
    async def connect(self):
        """Connect to MT5"""
        if mt5 is None:
            raise RuntimeError("MetaTrader5 package is not installed")

        async with self._connect_lock:
            if self.status in (ConnectionStatus.CONNECTED, ConnectionStatus.AUTHENTICATED):
                return

            try:
                self.status = ConnectionStatus.CONNECTING

                # Clean up any stale MT5 state before reconnect
                mt5.shutdown()
                await asyncio.sleep(0.2)

                # Initialize MT5
                if self.mt5_path:
                    initialized = mt5.initialize(self.mt5_path)
                else:
                    initialized = mt5.initialize()
                if not initialized:
                    raise Exception(f"MT5 initialization failed: {mt5.last_error()}")

                # Login to account
                if self.account and self.password and self.server:
                    authorized = mt5.login(
                        login=int(self.account),
                        password=self.password,
                        server=self.server
                    )

                    if not authorized:
                        raise Exception(f"MT5 login failed: {mt5.last_error()}")

                    self.status = ConnectionStatus.AUTHENTICATED
                else:
                    self.status = ConnectionStatus.CONNECTED

                account_info = mt5.account_info()
                if account_info:
                    logger.info(f"Connected to MT5: {account_info.name} ({account_info.login})")

                if not self._monitor_task or self._monitor_task.done():
                    self._monitor_task = asyncio.create_task(self._monitor_connection())

            except Exception as e:
                logger.error(f"Failed to connect to MT5: {e}")
                self.status = ConnectionStatus.ERROR
                raise
    
    async def disconnect(self):
        """Disconnect from MT5"""
        try:
            # Cancel monitoring tasks
            for task in self.monitoring_tasks.values():
                task.cancel()
            self.monitoring_tasks.clear()
            if self._monitor_task:
                self._monitor_task.cancel()
                self._monitor_task = None
            
            # Shutdown MT5
            if mt5 is not None:
                mt5.shutdown()
            
            self.status = ConnectionStatus.DISCONNECTED
            logger.info("Disconnected from MT5")
            
        except Exception as e:
            logger.error(f"Error disconnecting from MT5: {e}")
    
    async def subscribe_market_data(self, symbols: List[str]):
        """Subscribe to market data"""
        for symbol in symbols:
            mt5_symbol = self._normalize_symbol_for_mt5(symbol)
            
            # Enable symbol in Market Watch
            symbol_info = mt5.symbol_info(mt5_symbol)
            if symbol_info:
                if not symbol_info.visible:
                    if not mt5.symbol_select(mt5_symbol, True):
                        logger.warning(f"Failed to select symbol {mt5_symbol}")
                        continue
                
                # Start monitoring task
                task = asyncio.create_task(self._monitor_symbol(symbol, mt5_symbol))
                self.monitoring_tasks[symbol] = task
                
                logger.info(f"Subscribed to {mt5_symbol}")
            else:
                logger.warning(f"Symbol {mt5_symbol} not found")
    
    async def _monitor_symbol(self, symbol: str, mt5_symbol: str):
        """Monitor symbol for updates"""
        last_tick = None
        
        while self.status in [ConnectionStatus.CONNECTED, ConnectionStatus.AUTHENTICATED]:
            try:
                # Get current tick
                tick = mt5.symbol_info_tick(mt5_symbol)
                
                if tick and (not last_tick or tick.time != last_tick.time):
                    # Create market data
                    market_data = MarketData(
                        symbol=symbol,
                        exchange="MT5",
                        timestamp=datetime.fromtimestamp(tick.time),
                        price=tick.last,
                        bid=tick.bid,
                        ask=tick.ask,
                        volume=tick.volume,
                        open=0,  # Get from daily data
                        high=0,
                        low=0,
                        close=tick.last
                    )
                    
                    # Get daily OHLC
                    rates = mt5.copy_rates_from_pos(mt5_symbol, mt5.TIMEFRAME_D1, 0, 1)
                    if rates is not None and len(rates) > 0:
                        market_data.open = rates[0]['open']
                        market_data.high = rates[0]['high']
                        market_data.low = rates[0]['low']
                    
                    await self.emit_event('market_data', market_data)
                    
                    # Also emit as ticker
                    ticker = Ticker(
                        symbol=symbol,
                        exchange="MT5",
                        timestamp=datetime.fromtimestamp(tick.time),
                        bid=tick.bid,
                        ask=tick.ask,
                        last=tick.last,
                        volume_24h=tick.volume,
                        change_24h=0  # Calculate if needed
                    )
                    
                    await self.emit_event('ticker', ticker)
                    
                    last_tick = tick
                
                await asyncio.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                logger.error(f"Error monitoring {mt5_symbol}: {e}")
                await asyncio.sleep(1)
    
    async def subscribe_order_book(self, symbols: List[str], depth: int = 10):
        """Subscribe to order book (market depth)"""
        for symbol in symbols:
            mt5_symbol = self._normalize_symbol_for_mt5(symbol)
            
            # Start monitoring task for market depth
            task = asyncio.create_task(self._monitor_market_depth(symbol, mt5_symbol, depth))
            self.monitoring_tasks[f"{symbol}_depth"] = task
    
    async def _monitor_market_depth(self, symbol: str, mt5_symbol: str, depth: int):
        """Monitor market depth"""
        while self.status in [ConnectionStatus.CONNECTED, ConnectionStatus.AUTHENTICATED]:
            try:
                # Get market depth
                market_book = mt5.market_book_get(mt5_symbol)
                
                if market_book:
                    bids = []
                    asks = []
                    
                    for item in market_book:
                        if item.type == mt5.BOOK_TYPE_SELL:
                            asks.append((item.price, item.volume))
                        else:
                            bids.append((item.price, item.volume))
                    
                    # Sort bids descending, asks ascending
                    bids.sort(reverse=True)
                    asks.sort()
                    
                    order_book = OrderBook(
                        symbol=symbol,
                        exchange="MT5",
                        timestamp=datetime.now(),
                        bids=bids[:depth],
                        asks=asks[:depth]
                    )
                    
                    await self.emit_event('order_book', order_book)
                
                await asyncio.sleep(0.5)  # Update every 500ms
                
            except Exception as e:
                logger.error(f"Error monitoring market depth for {mt5_symbol}: {e}")
                await asyncio.sleep(1)
    
    async def subscribe_trades(self, symbols: List[str]):
        """Subscribe to trade feed"""
        for symbol in symbols:
            mt5_symbol = self._normalize_symbol_for_mt5(symbol)
            
            # Start monitoring task for trades
            task = asyncio.create_task(self._monitor_trades(symbol, mt5_symbol))
            self.monitoring_tasks[f"{symbol}_trades"] = task
    
    async def _monitor_trades(self, symbol: str, mt5_symbol: str):
        """Monitor trades (deals)"""
        last_deal_ticket = 0
        
        while self.status in [ConnectionStatus.CONNECTED, ConnectionStatus.AUTHENTICATED]:
            try:
                # Get recent deals
                deals = mt5.history_deals_get(symbol=mt5_symbol)
                
                if deals:
                    for deal in deals:
                        if deal.ticket > last_deal_ticket:
                            trade = Trade(
                                symbol=symbol,
                                exchange="MT5",
                                timestamp=datetime.fromtimestamp(deal.time),
                                price=deal.price,
                                size=deal.volume,
                                side='buy' if deal.type == mt5.DEAL_TYPE_BUY else 'sell',
                                trade_id=str(deal.ticket)
                            )
                            
                            await self.emit_event('trade', trade)
                            last_deal_ticket = deal.ticket
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error monitoring trades for {mt5_symbol}: {e}")
                await asyncio.sleep(1)
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """Get current ticker"""
        mt5_symbol = self._normalize_symbol_for_mt5(symbol)
        tick = mt5.symbol_info_tick(mt5_symbol)
        
        if tick:
            return Ticker(
                symbol=symbol,
                exchange="MT5",
                timestamp=datetime.fromtimestamp(tick.time),
                bid=tick.bid,
                ask=tick.ask,
                last=tick.last,
                volume_24h=tick.volume,
                change_24h=0  # Calculate if needed
            )
        
        raise Exception(f"Failed to get ticker for {symbol}")
    
    async def place_order(self, order: Dict) -> Dict:
        """Place an order"""
        # SECURITY FIX: Validate all order parameters
        self._validate_order(order)
        
        mt5_symbol = self._normalize_symbol_for_mt5(order['symbol'])
        
        # Prepare request with validated inputs
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": mt5_symbol,
            "volume": float(order['quantity']),  # Ensure numeric
            "type": mt5.ORDER_TYPE_BUY if order['side'] == 'buy' else mt5.ORDER_TYPE_SELL,
            "price": float(order.get('price', 0)),  # Ensure numeric
            "deviation": int(order.get('slippage', 20)),  # Ensure integer
            "magic": 234000,
            "comment": str(order.get('comment', 'Trading Bot'))[:31],  # MT5 comment limit
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Add stop loss and take profit if provided
        if 'stop_loss' in order:
            request['sl'] = order['stop_loss']
        
        if 'take_profit' in order:
            request['tp'] = order['take_profit']
        
        # Send order
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise Exception(f"Order failed: {result.comment}")
        
        return {
            'order_id': result.order,
            'deal': result.deal,
            'price': result.price,
            'volume': result.volume,
            'comment': result.comment
        }
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": int(order_id),
        }
        
        result = mt5.order_send(request)
        
        return result.retcode == mt5.TRADE_RETCODE_DONE
    
    async def get_order_status(self, order_id: str) -> Dict:
        """Get order status"""
        orders = mt5.orders_get(ticket=int(order_id))
        
        if orders and len(orders) > 0:
            order = orders[0]
            return {
                'order_id': order.ticket,
                'symbol': order.symbol,
                'type': 'buy' if order.type == mt5.ORDER_TYPE_BUY else 'sell',
                'volume': order.volume_current,
                'price': order.price_open,
                'status': 'open',
                'time': datetime.fromtimestamp(order.time_setup)
            }
        
        return {'status': 'not_found'}
    
    async def get_positions(self) -> List[Dict]:
        """Get current positions"""
        positions = mt5.positions_get()
        
        if positions:
            return [
                {
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'buy' if pos.type == mt5.POSITION_TYPE_BUY else 'sell',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'profit': pos.profit,
                    'swap': pos.swap,
                    'time': datetime.fromtimestamp(pos.time)
                }
                for pos in positions
            ]
        
        return []
    
    async def get_balance(self) -> Dict:
        """Get account balance"""
        account_info = mt5.account_info()
        
        if account_info:
            return {
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'free_margin': account_info.margin_free,
                'margin_level': account_info.margin_level,
                'profit': account_info.profit,
                'currency': account_info.currency
            }
        
        return {}
    
    async def _monitor_connection(self):
        """Monitor MT5 connection"""
        while self.status in [ConnectionStatus.CONNECTED, ConnectionStatus.AUTHENTICATED, ConnectionStatus.RECONNECTING]:
            try:
                # Check if terminal is connected
                terminal_info = mt5.terminal_info()
                
                if not terminal_info or not terminal_info.connected:
                    logger.warning("MT5 terminal disconnected")
                    ok = await self.reconnect()
                    if not ok:
                        self.status = ConnectionStatus.ERROR
                        break
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Connection monitor error: {e}")
                await asyncio.sleep(5)
    
    def _normalize_symbol_for_mt5(self, symbol: str) -> str:
        """Normalize symbol for MT5 format"""
        # Check mapping first
        if symbol in self.symbol_mapping:
            return self.symbol_mapping[symbol]
        
        # Remove slashes and dashes
        return symbol.replace('/', '').replace('-', '')
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format"""
        return self._normalize_symbol_for_mt5(symbol)
    
    # SECURITY FIX: Input validation methods
    def _validate_account(self, account) -> Optional[int]:
        """Validate MT5 account number."""
        if account is None:
            return None
        try:
            account_int = int(account)
            if account_int <= 0:
                raise ValueError("Account number must be positive")
            if account_int > 999999999:  # Reasonable upper limit
                raise ValueError("Account number exceeds maximum value")
            return account_int
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid MT5 account number: {e}")
            raise ValueError(f"Invalid MT5 account number: {account}")
    
    def _validate_password(self, password) -> Optional[str]:
        """Validate MT5 password."""
        if password is None:
            return None
        if not isinstance(password, str):
            raise ValueError("Password must be a string")
        if len(password) > 256:  # Reasonable password length limit
            raise ValueError("Password exceeds maximum length")
        # Don't log passwords!
        return password
    
    def _validate_server(self, server) -> Optional[str]:
        """Validate MT5 server name."""
        if server is None:
            return None
        if not isinstance(server, str):
            raise ValueError("Server must be a string")
        # Whitelist allowed characters (alphanumeric, dash, dot)
        import re
        if not re.match(r'^[a-zA-Z0-9\-\.]+$', server):
            raise ValueError("Server name contains invalid characters")
        if len(server) > 128:
            raise ValueError("Server name exceeds maximum length")
        return server
    
    def _validate_path(self, path) -> Optional[str]:
        """Validate MT5 installation path."""
        if path is None:
            return None
        if not isinstance(path, str):
            raise ValueError("Path must be a string")
        # Basic path validation
        import os
        if len(path) > 512:
            raise ValueError("Path exceeds maximum length")
        # Check for path traversal attempts
        if '..' in path or path.startswith('/') and os.name == 'nt':
            logger.warning(f"Suspicious path detected: {path}")
        return path
    
    def _validate_order(self, order: Dict) -> None:
        """Validate order parameters before execution."""
        if not isinstance(order, dict):
            raise ValueError("Order must be a dictionary")
        
        # Required fields
        if 'symbol' not in order:
            raise ValueError("Order missing required field: symbol")
        if 'quantity' not in order:
            raise ValueError("Order missing required field: quantity")
        if 'side' not in order:
            raise ValueError("Order missing required field: side")
        
        # Validate symbol
        if not isinstance(order['symbol'], str) or len(order['symbol']) > 32:
            raise ValueError("Invalid symbol format")

        # Validate quantity
        try:
            quantity = float(order['quantity'])
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            if quantity > 1000:  # Reasonable upper limit
                raise ValueError("Quantity exceeds maximum allowed")
        except (ValueError, TypeError):
            raise ValueError("Invalid quantity value")
        
        # Validate side
        if order['side'] not in ['buy', 'sell']:
            raise ValueError("Side must be 'buy' or 'sell'")
        
        # Validate optional price
        if 'price' in order and order['price'] is not None:
            try:
                price = float(order['price'])
                if price < 0:
                    raise ValueError("Price cannot be negative")
            except (ValueError, TypeError):
                raise ValueError("Invalid price value")
        
        # Validate optional stop loss and take profit
        for field in ['stop_loss', 'take_profit']:
            if field in order and order[field] is not None:
                try:
                    value = float(order[field])
                    if value < 0:
                        raise ValueError(f"{field} cannot be negative")
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid {field} value")
        
        # Validate slippage
        if 'slippage' in order:
            try:
                slippage = int(order['slippage'])
                if slippage < 0 or slippage > 1000:
                    raise ValueError("Slippage must be between 0 and 1000")
            except (ValueError, TypeError):
                raise ValueError("Invalid slippage value")
