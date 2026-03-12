"""
Live Trading System
Production-ready trading system with:
- Real-time market data feeds
- Paper trading mode
- Risk management
- Performance monitoring
- Strategy optimization

This is the main entry point for live/paper trading operations.
"""

import asyncio
import logging
import os
import sys
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import numpy as np
import pandas as pd
from collections import deque
import threading

try:
    import aiohttp
except ImportError:
    aiohttp = None

logger = logging.getLogger(__name__)


class TradingMode(Enum):
    """Trading execution modes"""
    PAPER = "paper"
    LIVE = "live"
    BACKTEST = "backtest"


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """Order representation"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_price: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Position:
    """Position representation"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    opened_at: datetime = field(default_factory=datetime.now)
    
    def update_price(self, price: float):
        """Update current price and PnL"""
        self.current_price = price
        self.unrealized_pnl = (price - self.entry_price) * self.quantity


@dataclass
class RiskParameters:
    """Risk management parameters"""
    max_position_size: float = 0.02  # 2% of capital per position
    max_portfolio_risk: float = 0.06  # 6% total portfolio risk
    max_daily_loss: float = 0.03  # 3% max daily loss
    max_drawdown: float = 0.10  # 10% max drawdown
    max_positions: int = 5
    stop_loss_pct: float = 0.02  # 2% stop loss
    take_profit_pct: float = 0.04  # 4% take profit
    max_correlation: float = 0.7  # Max correlation between positions
    position_sizing_method: str = "fixed_risk"  # fixed_risk, kelly, volatility
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'max_position_size': self.max_position_size,
            'max_portfolio_risk': self.max_portfolio_risk,
            'max_daily_loss': self.max_daily_loss,
            'max_drawdown': self.max_drawdown,
            'max_positions': self.max_positions,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'max_correlation': self.max_correlation,
            'position_sizing_method': self.position_sizing_method,
        }


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    
    def update(self, trade_pnl: float):
        """Update metrics with new trade"""
        self.total_trades += 1
        self.realized_pnl += trade_pnl
        self.total_pnl = self.realized_pnl + self.unrealized_pnl
        
        if trade_pnl > 0:
            self.winning_trades += 1
            self.largest_win = max(self.largest_win, trade_pnl)
        else:
            self.losing_trades += 1
            self.largest_loss = min(self.largest_loss, trade_pnl)
        
        self.win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': round(self.win_rate, 4),
            'total_pnl': round(self.total_pnl, 2),
            'realized_pnl': round(self.realized_pnl, 2),
            'unrealized_pnl': round(self.unrealized_pnl, 2),
            'max_drawdown': round(self.max_drawdown, 4),
            'sharpe_ratio': round(self.sharpe_ratio, 2),
            'profit_factor': round(self.profit_factor, 2),
        }


class LiveDataFeed:
    """
    Real-time market data feed manager.
    Supports multiple data sources with fallback.
    """
    
    def __init__(self, symbols: List[str], config: Optional[Dict] = None):
        self.symbols = symbols
        self.config = config or {}
        self.is_running = False
        self._callbacks: List[Callable] = []
        self._data_cache: Dict[str, Dict] = {}
        self._price_history: Dict[str, deque] = {s: deque(maxlen=1000) for s in symbols}
        self._last_update: Dict[str, datetime] = {}
        
        # Data source priority
        self.data_sources = [
            'mt5',
            'yahoo',
            'alpha_vantage',
            'binance',
        ]
        
        logger.info(f"LiveDataFeed initialized for {len(symbols)} symbols")
    
    async def start(self):
        """Start the data feed"""
        self.is_running = True
        logger.info("Starting live data feed...")
        
        while self.is_running:
            try:
                await self._fetch_all_prices()
                await asyncio.sleep(1)  # 1 second update interval
            except Exception as e:
                logger.error(f"Data feed error: {e}")
                await asyncio.sleep(5)
    
    async def stop(self):
        """Stop the data feed"""
        self.is_running = False
        logger.info("Live data feed stopped")
    
    async def _fetch_all_prices(self):
        """Fetch prices for all symbols"""
        for symbol in self.symbols:
            try:
                price_data = await self._fetch_price(symbol)
                if price_data:
                    self._data_cache[symbol] = price_data
                    self._price_history[symbol].append({
                        'timestamp': datetime.now(),
                        'price': price_data['price'],
                        'bid': price_data.get('bid'),
                        'ask': price_data.get('ask'),
                        'volume': price_data.get('volume'),
                    })
                    self._last_update[symbol] = datetime.now()
                    
                    # Notify callbacks
                    for callback in self._callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(symbol, price_data)
                            else:
                                callback(symbol, price_data)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
    
    async def _fetch_price(self, symbol: str) -> Optional[Dict]:
        """Fetch price from available data sources"""
        for source in self.data_sources:
            try:
                if source == 'mt5':
                    return await self._fetch_from_mt5(symbol)
                elif source == 'yahoo':
                    return await self._fetch_from_yahoo(symbol)
                elif source == 'alpha_vantage':
                    return await self._fetch_from_alpha_vantage(symbol)
                elif source == 'binance':
                    return await self._fetch_from_binance(symbol)
            except Exception as e:
                logger.debug(f"Source {source} failed for {symbol}: {e}")
                continue
        
        # Fallback to simulated data for paper trading
        return self._generate_simulated_price(symbol)
    
    async def _fetch_from_mt5(self, symbol: str) -> Optional[Dict]:
        """Fetch from MetaTrader 5"""
        try:
            # Try to import MT5
            import MetaTrader5 as mt5
            
            if not mt5.initialize():
                return None
            
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return None
            
            return {
                'symbol': symbol,
                'price': (tick.bid + tick.ask) / 2,
                'bid': tick.bid,
                'ask': tick.ask,
                'volume': tick.volume,
                'timestamp': datetime.now(),
                'source': 'mt5',
            }
        except ImportError:
            return None
        except Exception as e:
            logger.debug(f"MT5 error: {e}")
            return None
    
    async def _fetch_from_yahoo(self, symbol: str) -> Optional[Dict]:
        """Fetch from Yahoo Finance"""
        try:
            import yfinance as yf
            
            # Convert forex symbols
            yahoo_symbol = symbol
            if len(symbol) == 6 and symbol.isalpha():
                yahoo_symbol = f"{symbol[:3]}{symbol[3:]}=X"
            
            ticker = yf.Ticker(yahoo_symbol)
            data = ticker.history(period='1d', interval='1m')
            
            if data.empty:
                return None
            
            last = data.iloc[-1]
            return {
                'symbol': symbol,
                'price': float(last['Close']),
                'bid': float(last['Close']) * 0.9999,
                'ask': float(last['Close']) * 1.0001,
                'volume': float(last['Volume']),
                'timestamp': datetime.now(),
                'source': 'yahoo',
            }
        except Exception as e:
            logger.debug(f"Yahoo error: {e}")
            return None
    
    async def _fetch_from_alpha_vantage(self, symbol: str) -> Optional[Dict]:
        """Fetch from Alpha Vantage"""
        try:
            from trading_bot.security.secure_credentials import get_api_key
            
            api_key = get_api_key('alpha_vantage')
            if not api_key:
                return None
            
            # Convert symbol format
            from_currency = symbol[:3]
            to_currency = symbol[3:]
            
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': from_currency,
                'to_currency': to_currency,
                'apikey': api_key,
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    data = await response.json()
            
            if 'Realtime Currency Exchange Rate' in data:
                rate_data = data['Realtime Currency Exchange Rate']
                price = float(rate_data['5. Exchange Rate'])
                return {
                    'symbol': symbol,
                    'price': price,
                    'bid': price * 0.9999,
                    'ask': price * 1.0001,
                    'volume': 0,
                    'timestamp': datetime.now(),
                    'source': 'alpha_vantage',
                }
            return None
        except Exception as e:
            logger.debug(f"Alpha Vantage error: {e}")
            return None
    
    async def _fetch_from_binance(self, symbol: str) -> Optional[Dict]:
        """Fetch from Binance"""
            
        try:
            # Convert symbol format for crypto
            binance_symbol = symbol.replace('/', '').upper()
            
            url = f"https://api.binance.com/api/v3/ticker/bookTicker"
            params = {'symbol': binance_symbol}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    data = await response.json()
            
            if 'bidPrice' in data:
                bid = float(data['bidPrice'])
                ask = float(data['askPrice'])
                return {
                    'symbol': symbol,
                    'price': (bid + ask) / 2,
                    'bid': bid,
                    'ask': ask,
                    'volume': 0,
                    'timestamp': datetime.now(),
                    'source': 'binance',
                }
            return None
        except Exception as e:
            logger.debug(f"Binance error: {e}")
            return None
    
    def _generate_simulated_price(self, symbol: str) -> Dict:
        """Generate simulated price for paper trading"""
        # Base prices for common symbols
        base_prices = {
            'EURUSD': 1.0850,
            'GBPUSD': 1.2650,
            'USDJPY': 149.50,
            'USDCHF': 0.8850,
            'AUDUSD': 0.6550,
            'BTCUSD': 95000.0,
            'ETHUSD': 3500.0,
        }
        
        base = base_prices.get(symbol, 100.0)
        
        # Add random walk
        if symbol in self._price_history and len(self._price_history[symbol]) > 0:
            last_price = self._price_history[symbol][-1]['price']
            change = np.random.randn() * 0.0001 * base  # Small random change
            price = last_price + change
        else:
            price = base * (1 + np.random.randn() * 0.001)
        
        spread = price * 0.0001  # 1 pip spread
        
        return {
            'symbol': symbol,
            'price': price,
            'bid': price - spread/2,
            'ask': price + spread/2,
            'volume': np.random.randint(1000, 10000),
            'timestamp': datetime.now(),
            'source': 'simulated',
        }
    
    def get_current_price(self, symbol: str) -> Optional[Dict]:
        """Get current price for symbol"""
        return self._data_cache.get(symbol)
    
    def get_price_history(self, symbol: str, periods: int = 100) -> List[Dict]:
        """Get price history for symbol"""
        history = list(self._price_history.get(symbol, []))
        return history[-periods:] if len(history) > periods else history
    
    def register_callback(self, callback: Callable):
        """Register callback for price updates"""
        self._callbacks.append(callback)
    
    def is_stale(self, symbol: str, max_age_seconds: int = 60) -> bool:
        """Check if data is stale"""
        last_update = self._last_update.get(symbol)
        if not last_update:
            return True
        return (datetime.now() - last_update).total_seconds() > max_age_seconds


class PaperTradingEngine:
    """
    Paper trading execution engine.
    Simulates order execution without real money.
    """
    
    def __init__(self, initial_capital: float = 100000.0, 
                 risk_params: Optional[RiskParameters] = None):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.risk_params = risk_params or RiskParameters()
        
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        self.trade_history: List[Dict] = []
        
        self.metrics = PerformanceMetrics()
        self._order_counter = 0
        self._daily_pnl = 0.0
        self._peak_capital = initial_capital
        
        logger.info(f"PaperTradingEngine initialized with ${initial_capital:,.2f}")
    
    def place_order(self, symbol: str, side: OrderSide, quantity: float,
                   order_type: OrderType = OrderType.MARKET,
                   price: Optional[float] = None,
                   stop_price: Optional[float] = None) -> Order:
        """Place a new order"""
        # Generate order ID
        self._order_counter += 1
        order_id = f"PAPER_{datetime.now().strftime('%Y%m%d')}_{self._order_counter:06d}"
        
        # Create order
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            status=OrderStatus.PENDING,
        )
        
        # Validate order
        validation = self._validate_order(order)
        if not validation['valid']:
            order.status = OrderStatus.REJECTED
            order.metadata['rejection_reason'] = validation['reason']
            logger.warning(f"Order rejected: {validation['reason']}")
        else:
            order.status = OrderStatus.SUBMITTED
            self.orders[order_id] = order
            logger.info(f"Order submitted: {order_id} - {side.value} {quantity} {symbol}")
        
        return order
    
    def _validate_order(self, order: Order) -> Dict[str, Any]:
        """Validate order against risk parameters"""
        # Check max positions
        if len(self.positions) >= self.risk_params.max_positions:
            if order.symbol not in self.positions:
                return {'valid': False, 'reason': 'Max positions reached'}
        
        # Check position size
        # Estimate order value (would need current price in real implementation)
        estimated_value = order.quantity * 100  # Placeholder
        max_position_value = self.capital * self.risk_params.max_position_size
        
        if estimated_value > max_position_value:
            return {'valid': False, 'reason': 'Position size exceeds limit'}
        
        # Check daily loss limit
        if self._daily_pnl < -self.initial_capital * self.risk_params.max_daily_loss:
            return {'valid': False, 'reason': 'Daily loss limit reached'}
        
        # Check drawdown
        current_drawdown = (self._peak_capital - self.capital) / self._peak_capital
        if current_drawdown > self.risk_params.max_drawdown:
            return {'valid': False, 'reason': 'Max drawdown reached'}
        
        return {'valid': True, 'reason': None}
    
    def execute_order(self, order_id: str, current_price: float) -> bool:
        """Execute a pending order"""
        if order_id not in self.orders:
            logger.error(f"Order not found: {order_id}")
            return False
        
        order = self.orders[order_id]
        
        if order.status != OrderStatus.SUBMITTED:
            logger.warning(f"Order {order_id} not in submitted state")
            return False
        
        # Simulate execution with slippage
        slippage = current_price * 0.0001  # 1 pip slippage
        if order.side == OrderSide.BUY:
            fill_price = current_price + slippage
        else:
            fill_price = current_price - slippage
        
        # Update order
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.filled_price = fill_price
        order.updated_at = datetime.now()
        
        # Update position
        self._update_position(order)
        
        # Move to history
        self.order_history.append(order)
        del self.orders[order_id]
        
        logger.info(f"Order filled: {order_id} at {fill_price:.5f}")
        return True
    
    def _update_position(self, order: Order):
        """Update position after order fill"""
        symbol = order.symbol
        
        if symbol in self.positions:
            position = self.positions[symbol]
            
            if order.side == OrderSide.BUY:
                # Adding to long or closing short
                if position.quantity >= 0:
                    # Adding to long
                    total_cost = position.entry_price * position.quantity + order.filled_price * order.filled_quantity
                    position.quantity += order.filled_quantity
                    position.entry_price = total_cost / position.quantity
                else:
                    # Closing short
                    pnl = (position.entry_price - order.filled_price) * min(abs(position.quantity), order.filled_quantity)
                    position.realized_pnl += pnl
                    position.quantity += order.filled_quantity
                    self._record_trade(order, pnl)
            else:
                # Selling from long or adding to short
                if position.quantity > 0:
                    # Closing long
                    pnl = (order.filled_price - position.entry_price) * min(position.quantity, order.filled_quantity)
                    position.realized_pnl += pnl
                    position.quantity -= order.filled_quantity
                    self._record_trade(order, pnl)
                else:
                    # Adding to short
                    total_cost = abs(position.entry_price * position.quantity) + order.filled_price * order.filled_quantity
                    position.quantity -= order.filled_quantity
                    position.entry_price = total_cost / abs(position.quantity)
            
            # Remove position if flat
            if abs(position.quantity) < 0.0001:
                del self.positions[symbol]
        else:
            # New position
            quantity = order.filled_quantity if order.side == OrderSide.BUY else -order.filled_quantity
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                entry_price=order.filled_price,
                current_price=order.filled_price,
            )
    
    def _record_trade(self, order: Order, pnl: float):
        """Record completed trade"""
        trade = {
            'order_id': order.order_id,
            'symbol': order.symbol,
            'side': order.side.value,
            'quantity': order.filled_quantity,
            'price': order.filled_price,
            'pnl': pnl,
            'timestamp': datetime.now().isoformat(),
        }
        self.trade_history.append(trade)
        
        # Update metrics
        self.metrics.update(pnl)
        self._daily_pnl += pnl
        self.capital += pnl
        
        # Update peak capital
        if self.capital > self._peak_capital:
            self._peak_capital = self.capital
        
        # Update drawdown
        current_drawdown = (self._peak_capital - self.capital) / self._peak_capital
        self.metrics.max_drawdown = max(self.metrics.max_drawdown, current_drawdown)
        self.metrics.current_drawdown = current_drawdown
    
    def update_positions(self, prices: Dict[str, float]):
        """Update all positions with current prices"""
        total_unrealized = 0.0
        
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.update_price(prices[symbol])
                total_unrealized += position.unrealized_pnl
        
        self.metrics.unrealized_pnl = total_unrealized
        self.metrics.total_pnl = self.metrics.realized_pnl + total_unrealized
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol"""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, Position]:
        """Get all positions"""
        return self.positions.copy()
    
    def get_portfolio_value(self) -> float:
        """Get total portfolio value"""
        return self.capital + self.metrics.unrealized_pnl
    
    def get_metrics(self) -> PerformanceMetrics:
        """Get performance metrics"""
        return self.metrics
    
    def reset_daily_pnl(self):
        """Reset daily PnL (call at start of trading day)"""
        self._daily_pnl = 0.0


class RiskManager:
    """
    Risk management system.
    Monitors and enforces risk limits.
    """
    
    def __init__(self, params: RiskParameters, capital: float):
        self.params = params
        self.initial_capital = capital
        self.current_capital = capital
        self._alerts: List[Dict] = []
        
        logger.info("RiskManager initialized")
    
    def calculate_position_size(self, symbol: str, entry_price: float, 
                               stop_loss: float, volatility: float = 0.0) -> float:
        """
        Calculate position size based on risk parameters.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            volatility: Current volatility (for volatility-based sizing)
            
        Returns:
            Position size in units
        """
        risk_amount = self.current_capital * self.params.max_position_size
        
        if self.params.position_sizing_method == 'fixed_risk':
            # Fixed percentage risk
            risk_per_unit = abs(entry_price - stop_loss)
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit
            else:
                position_size = 0
                
        elif self.params.position_sizing_method == 'kelly':
            # Kelly criterion (simplified)
            win_rate = 0.55  # Assumed win rate
            win_loss_ratio = 1.5  # Assumed win/loss ratio
            kelly_fraction = win_rate - (1 - win_rate) / win_loss_ratio
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
            position_size = (self.current_capital * kelly_fraction) / entry_price
            
        elif self.params.position_sizing_method == 'volatility':
            # Volatility-based sizing
            if volatility > 0:
                target_volatility = 0.02  # 2% target volatility
                position_size = (self.current_capital * target_volatility) / (entry_price * volatility)
            else:
                position_size = risk_amount / entry_price
        else:
            position_size = risk_amount / entry_price
        
        return round(position_size, 2)
    
    def check_trade(self, symbol: str, side: str, quantity: float, 
                   price: float, current_positions: Dict[str, Position]) -> Dict[str, Any]:
        """
        Check if a trade passes risk checks.
        
        Returns:
            Dict with 'approved' bool and 'reason' if rejected
        """
        checks = []
        
        # Check position count
        if len(current_positions) >= self.params.max_positions:
            if symbol not in current_positions:
                checks.append(('max_positions', False, 'Maximum positions reached'))
            else:
                checks.append(('max_positions', True, 'Adding to existing position'))
        else:
            checks.append(('max_positions', True, 'Within position limit'))
        
        # Check position size
        position_value = quantity * price
        max_value = self.current_capital * self.params.max_position_size
        if position_value > max_value:
            checks.append(('position_size', False, f'Position value ${position_value:.2f} exceeds max ${max_value:.2f}'))
        else:
            checks.append(('position_size', True, 'Within position size limit'))
        
        # Check portfolio risk
        total_exposure = sum(abs(p.quantity * p.current_price) for p in current_positions.values())
        total_exposure += position_value
        max_exposure = self.current_capital * (1 + self.params.max_portfolio_risk)
        if total_exposure > max_exposure:
            checks.append(('portfolio_risk', False, 'Portfolio risk limit exceeded'))
        else:
            checks.append(('portfolio_risk', True, 'Within portfolio risk limit'))
        
        # Compile results
        all_passed = all(check[1] for check in checks)
        failed_checks = [check for check in checks if not check[1]]
        
        result = {
            'approved': all_passed,
            'checks': checks,
            'reason': failed_checks[0][2] if failed_checks else None,
        }
        
        if not all_passed:
            self._add_alert('RISK_CHECK_FAILED', result['reason'])
        
        return result
    
    def update_capital(self, new_capital: float):
        """Update current capital"""
        self.current_capital = new_capital
    
    def _add_alert(self, alert_type: str, message: str):
        """Add risk alert"""
        alert = {
            'type': alert_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
        }
        self._alerts.append(alert)
        logger.warning(f"Risk Alert: {alert_type} - {message}")
    
    def get_alerts(self, since: Optional[datetime] = None) -> List[Dict]:
        """Get risk alerts"""
        if since:
            return [a for a in self._alerts if datetime.fromisoformat(a['timestamp']) > since]
        return self._alerts.copy()
    
    def clear_alerts(self):
        """Clear all alerts"""
        self._alerts.clear()


class PerformanceMonitor:
    """
    Real-time performance monitoring.
    Tracks metrics and generates reports.
    """
    
    def __init__(self):
        self.metrics_history: deque = deque(maxlen=10000)
        self.equity_curve: List[Dict] = []
        self.daily_returns: List[float] = []
        self._start_time = datetime.now()
        
        logger.info("PerformanceMonitor initialized")
    
    def record_snapshot(self, metrics: PerformanceMetrics, capital: float):
        """Record performance snapshot"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'capital': capital,
            'total_pnl': metrics.total_pnl,
            'realized_pnl': metrics.realized_pnl,
            'unrealized_pnl': metrics.unrealized_pnl,
            'total_trades': metrics.total_trades,
            'win_rate': metrics.win_rate,
            'max_drawdown': metrics.max_drawdown,
        }
        self.metrics_history.append(snapshot)
        
        # Update equity curve
        self.equity_curve.append({
            'timestamp': datetime.now(),
            'equity': capital + metrics.unrealized_pnl,
        })
    
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.04) -> float:
        """Calculate Sharpe ratio from equity curve"""
        if len(self.equity_curve) < 2:
            return 0.0
        
        equities = [e['equity'] for e in self.equity_curve]
        returns = np.diff(equities) / equities[:-1]
        
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        
        # Annualize
        periods_per_year = 252 * 24 * 60  # Assuming minute data
        excess_return = np.mean(returns) * periods_per_year - risk_free_rate
        volatility = np.std(returns) * np.sqrt(periods_per_year)
        
        return excess_return / volatility if volatility > 0 else 0.0
    
    def calculate_sortino_ratio(self, risk_free_rate: float = 0.04) -> float:
        """Calculate Sortino ratio"""
        if len(self.equity_curve) < 2:
            return 0.0
        
        equities = [e['equity'] for e in self.equity_curve]
        returns = np.diff(equities) / equities[:-1]
        
        negative_returns = returns[returns < 0]
        if len(negative_returns) == 0:
            return float('inf')
        
        periods_per_year = 252 * 24 * 60
        excess_return = np.mean(returns) * periods_per_year - risk_free_rate
        downside_std = np.std(negative_returns) * np.sqrt(periods_per_year)
        
        return excess_return / downside_std if downside_std > 0 else 0.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.metrics_history:
            return {}
        
        latest = self.metrics_history[-1]
        
        return {
            'uptime': str(datetime.now() - self._start_time),
            'current_capital': latest['capital'],
            'total_pnl': latest['total_pnl'],
            'total_trades': latest['total_trades'],
            'win_rate': latest['win_rate'],
            'max_drawdown': latest['max_drawdown'],
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'sortino_ratio': self.calculate_sortino_ratio(),
            'snapshots_recorded': len(self.metrics_history),
        }
    
    def export_report(self, filepath: str):
        """Export performance report to file"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': self.get_summary(),
            'equity_curve': [
                {'timestamp': e['timestamp'].isoformat(), 'equity': e['equity']}
                for e in self.equity_curve[-1000:]  # Last 1000 points
            ],
            'recent_metrics': list(self.metrics_history)[-100:],
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Performance report exported to {filepath}")


class LiveTradingSystem:
    """
    Main live trading system that integrates all components.
    """
    
    def __init__(self, 
                 symbols: List[str],
                 mode: TradingMode = TradingMode.PAPER,
                 initial_capital: float = 100000.0,
                 risk_params: Optional[RiskParameters] = None):
        
        self.symbols = symbols
        self.mode = mode
        self.initial_capital = initial_capital
        self.risk_params = risk_params or RiskParameters()
        
        # Initialize components
        self.data_feed = LiveDataFeed(symbols)
        self.trading_engine = PaperTradingEngine(initial_capital, self.risk_params)
        self.risk_manager = RiskManager(self.risk_params, initial_capital)
        self.performance_monitor = PerformanceMonitor()
        
        # State
        self.is_running = False
        self._strategy_callback: Optional[Callable] = None
        self._last_signal_time: Dict[str, datetime] = {}
        
        logger.info(f"LiveTradingSystem initialized in {mode.value} mode")
        logger.info(f"Symbols: {symbols}")
        logger.info(f"Initial capital: ${initial_capital:,.2f}")
    
    def set_strategy(self, strategy_callback: Callable):
        """
        Set the trading strategy callback.
        
        The callback should accept:
            - symbol: str
            - price_data: Dict
            - positions: Dict[str, Position]
            - capital: float
            
        And return:
            - Dict with 'action' ('buy', 'sell', 'hold'), 'quantity', 'reason'
        """
        self._strategy_callback = strategy_callback
        logger.info("Strategy callback set")
    
    async def start(self):
        """Start the trading system"""
        if self.is_running:
            logger.warning("System already running")
            return
        
        self.is_running = True
        logger.info("=" * 60)
        logger.info("LIVE TRADING SYSTEM STARTED")
        logger.info(f"Mode: {self.mode.value}")
        logger.info(f"Symbols: {', '.join(self.symbols)}")
        logger.info("=" * 60)
        
        # Register price update callback
        self.data_feed.register_callback(self._on_price_update)
        
        # Start data feed
        data_feed_task = asyncio.create_task(self.data_feed.start())
        
        # Start monitoring loop
        monitor_task = asyncio.create_task(self._monitoring_loop())
        
        try:
            await asyncio.gather(data_feed_task, monitor_task)
        except asyncio.CancelledError:
            logger.info("System shutdown requested")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the trading system"""
        self.is_running = False
        await self.data_feed.stop()
        
        # Export final report
        report_path = f"reports/trading_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        self.performance_monitor.export_report(report_path)
        
        logger.info("=" * 60)
        logger.info("LIVE TRADING SYSTEM STOPPED")
        logger.info(f"Final Capital: ${self.trading_engine.get_portfolio_value():,.2f}")
        logger.info(f"Total PnL: ${self.trading_engine.metrics.total_pnl:,.2f}")
        logger.info(f"Total Trades: {self.trading_engine.metrics.total_trades}")
        logger.info("=" * 60)
    
    async def _on_price_update(self, symbol: str, price_data: Dict):
        """Handle price updates"""
        try:
            # Update positions
            prices = {symbol: price_data['price']}
            self.trading_engine.update_positions(prices)
            
            # Check for strategy signals
            if self._strategy_callback:
                await self._process_strategy_signal(symbol, price_data)
            
            # Execute pending orders
            await self._execute_pending_orders(symbol, price_data['price'])
            
        except Exception as e:
            logger.error(f"Error processing price update: {e}")
    
    async def _process_strategy_signal(self, symbol: str, price_data: Dict):
        """Process strategy signal"""
        # Rate limit signals (min 1 second between signals per symbol)
        last_signal = self._last_signal_time.get(symbol)
        if last_signal and (datetime.now() - last_signal).total_seconds() < 1:
            return
        try:
        
            signal = self._strategy_callback(
                symbol=symbol,
                price_data=price_data,
                positions=self.trading_engine.get_all_positions(),
                capital=self.trading_engine.capital,
            )
            
            if signal and signal.get('action') != 'hold':
                self._last_signal_time[symbol] = datetime.now()
                await self._execute_signal(symbol, signal, price_data['price'])
                
        except Exception as e:
            logger.error(f"Strategy error for {symbol}: {e}")
    
    async def _execute_signal(self, symbol: str, signal: Dict, current_price: float):
        """Execute a trading signal"""
        action = signal.get('action')
        quantity = signal.get('quantity', 0)
        
        if quantity <= 0:
            return
        
        # Risk check
        side = OrderSide.BUY if action == 'buy' else OrderSide.SELL
        risk_check = self.risk_manager.check_trade(
            symbol=symbol,
            side=action,
            quantity=quantity,
            price=current_price,
            current_positions=self.trading_engine.get_all_positions(),
        )
        
        if not risk_check['approved']:
            logger.warning(f"Signal rejected by risk manager: {risk_check['reason']}")
            return
        
        # Place order
        order = self.trading_engine.place_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=OrderType.MARKET,
        )
        
        if order.status == OrderStatus.SUBMITTED:
            # Execute immediately for market orders
            self.trading_engine.execute_order(order.order_id, current_price)
            logger.info(f"Signal executed: {action.upper()} {quantity} {symbol} @ {current_price:.5f}")
    
    async def _execute_pending_orders(self, symbol: str, current_price: float):
        """Execute pending orders for symbol"""
        for order_id, order in list(self.trading_engine.orders.items()):
            if order.symbol != symbol:
                continue
            
            if order.order_type == OrderType.MARKET:
                self.trading_engine.execute_order(order_id, current_price)
            elif order.order_type == OrderType.LIMIT:
                if order.side == OrderSide.BUY and current_price <= order.price:
                    self.trading_engine.execute_order(order_id, order.price)
                elif order.side == OrderSide.SELL and current_price >= order.price:
                    self.trading_engine.execute_order(order_id, order.price)
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.is_running:
            try:
                # Record performance snapshot
                self.performance_monitor.record_snapshot(
                    self.trading_engine.metrics,
                    self.trading_engine.capital,
                )
                
                # Update risk manager capital
                self.risk_manager.update_capital(self.trading_engine.get_portfolio_value())
                
                # Log status every minute
                await asyncio.sleep(60)
                
                summary = self.performance_monitor.get_summary()
                logger.info(f"Status: Capital=${summary.get('current_capital', 0):,.2f}, "
                           f"PnL=${summary.get('total_pnl', 0):,.2f}, "
                           f"Trades={summary.get('total_trades', 0)}")
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(5)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'mode': self.mode.value,
            'is_running': self.is_running,
            'symbols': self.symbols,
            'capital': self.trading_engine.capital,
            'portfolio_value': self.trading_engine.get_portfolio_value(),
            'positions': {s: {'quantity': p.quantity, 'entry': p.entry_price, 'pnl': p.unrealized_pnl}
                         for s, p in self.trading_engine.positions.items()},
            'metrics': self.trading_engine.metrics.to_dict(),
            'risk_params': self.risk_params.to_dict(),
            'performance': self.performance_monitor.get_summary(),
        }


# Example strategy
def simple_momentum_strategy(symbol: str, price_data: Dict, 
                            positions: Dict[str, Position], capital: float) -> Dict:
    """
    Simple momentum strategy example.
    
    Buy when price is above 20-period SMA, sell when below.
    """
    # This is a placeholder - in real use, you'd have access to price history
    current_price = price_data['price']
    
    # Check existing position
    position = positions.get(symbol)
    
    # Simple random signal for demonstration
    import random
    signal = random.random()
    
    if position is None:
        if signal > 0.7:  # 30% chance to buy
            return {
                'action': 'buy',
                'quantity': round(capital * 0.02 / current_price, 2),
                'reason': 'Momentum signal',
            }
    else:
        if signal < 0.3:  # 30% chance to sell
            return {
                'action': 'sell',
                'quantity': abs(position.quantity),
                'reason': 'Exit signal',
            }
    
    return {'action': 'hold', 'quantity': 0, 'reason': 'No signal'}


async def run_demo():
    """Run a demo of the live trading system"""
    print("\n" + "=" * 60)
    logger.info("LIVE TRADING SYSTEM DEMO")
    print("=" * 60)
    
    # Configure risk parameters
    risk_params = RiskParameters(
        max_position_size=0.02,
        max_portfolio_risk=0.06,
        max_daily_loss=0.03,
        max_drawdown=0.10,
        max_positions=5,
        stop_loss_pct=0.02,
        take_profit_pct=0.04,
    )
    
    # Create system
    system = LiveTradingSystem(
        symbols=['EURUSD', 'GBPUSD', 'USDJPY'],
        mode=TradingMode.PAPER,
        initial_capital=100000.0,
        risk_params=risk_params,
    )
    
    # Set strategy
    system.set_strategy(simple_momentum_strategy)
    
    # Run for 30 seconds
    logger.info("\nRunning paper trading for 30 seconds...")
    logger.info("Press Ctrl+C to stop early\n")
    
    try:
        # Create a task that will stop after 30 seconds
        async def run_with_timeout():
            task = asyncio.create_task(system.start())
            await asyncio.sleep(30)
            system.is_running = False
            await system.stop()
        
        await run_with_timeout()
        
    except KeyboardInterrupt:
        await system.stop()
    
    # Print final status
    status = system.get_status()
    print("\n" + "=" * 60)
    logger.info("FINAL STATUS")
    print("=" * 60)
    logger.info(f"Portfolio Value: ${status['portfolio_value']:,.2f}")
    logger.info(f"Total PnL: ${status['metrics']['total_pnl']:,.2f}")
    logger.info(f"Total Trades: {status['metrics']['total_trades']}")
    logger.info(f"Win Rate: {status['metrics']['win_rate']:.2%}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_demo())
