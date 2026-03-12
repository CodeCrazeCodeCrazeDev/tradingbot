"""
Mock market data generators for testing.
Generates realistic OHLCV, tick, and order book data.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import random
import numpy
import pandas


def generate_ohlcv_data(
    symbol: str = 'EURUSD',
    periods: int = 1000,
    timeframe: str = 'H1',
    start_price: float = 1.1000,
    volatility: float = 0.0002,
    trend: float = 0.0,
    start_date: Optional[datetime] = None
) -> pd.DataFrame:
    """
    Generate realistic OHLCV data for testing.
    
    Args:
        symbol: Trading symbol
        periods: Number of bars to generate
        timeframe: Timeframe (M1, M5, M15, H1, H4, D1)
        start_price: Starting price
        volatility: Price volatility (standard deviation)
        trend: Trend direction (-1 to 1)
        start_date: Starting date
    
    Returns:
        DataFrame with OHLCV data
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(hours=periods)
    
    # Timeframe to timedelta mapping
    tf_map = {
        'M1': timedelta(minutes=1),
        'M5': timedelta(minutes=5),
        'M15': timedelta(minutes=15),
        'M30': timedelta(minutes=30),
        'H1': timedelta(hours=1),
        'H4': timedelta(hours=4),
        'D1': timedelta(days=1),
    }
    delta = tf_map.get(timeframe, timedelta(hours=1))
    
    # Generate timestamps
    timestamps = [start_date + delta * i for i in range(periods)]
    
    # Generate price movements using geometric Brownian motion
    returns = np.random.normal(trend * volatility, volatility, periods)
    prices = start_price * np.exp(np.cumsum(returns))
    
    # Generate OHLC from prices
    data = []
    for i, (ts, close) in enumerate(zip(timestamps, prices)):
        # Add intrabar volatility
        intrabar_vol = volatility * 2
        high_offset = abs(np.random.normal(0, intrabar_vol))
        low_offset = abs(np.random.normal(0, intrabar_vol))
        
        if i == 0:
            open_price = start_price
        else:
            open_price = data[-1]['close']
        
        high = max(open_price, close) + high_offset
        low = min(open_price, close) - low_offset
        
        # Generate volume (higher during volatile periods)
        base_volume = 10000
        volume_multiplier = 1 + abs(close - open_price) / volatility
        volume = int(base_volume * volume_multiplier * random.uniform(0.5, 1.5))
        
        data.append({
            'timestamp': ts,
            'open': round(open_price, 5),
            'high': round(high, 5),
            'low': round(low, 5),
            'close': round(close, 5),
            'volume': volume,
            'symbol': symbol,
        })
    
    return pd.DataFrame(data)


def generate_order_book(
    mid_price: float = 1.1000,
    spread_pips: float = 1.0,
    levels: int = 10,
    base_size: int = 1000000,
    imbalance: float = 0.0
) -> Dict[str, List[Tuple[float, int]]]:
    """
    Generate a realistic order book.
    
    Args:
        mid_price: Middle price
        spread_pips: Spread in pips
        levels: Number of price levels
        base_size: Base order size
        imbalance: Order book imbalance (-1 to 1, positive = more bids)
    
    Returns:
        Dictionary with 'bids' and 'asks' lists of (price, size) tuples
    """
    pip_size = 0.0001
    half_spread = spread_pips * pip_size / 2
    
    bid_price = mid_price - half_spread
    ask_price = mid_price + half_spread
    
    bids = []
    asks = []
    
    for i in range(levels):
        # Price levels
        bid_level = bid_price - i * pip_size
        ask_level = ask_price + i * pip_size
        
        # Size decreases with distance from mid
        decay = 0.8 ** i
        
        # Apply imbalance
        bid_multiplier = 1 + imbalance * 0.5
        ask_multiplier = 1 - imbalance * 0.5
        
        bid_size = int(base_size * decay * bid_multiplier * random.uniform(0.8, 1.2))
        ask_size = int(base_size * decay * ask_multiplier * random.uniform(0.8, 1.2))
        
        bids.append((round(bid_level, 5), bid_size))
        asks.append((round(ask_level, 5), ask_size))
    
    return {'bids': bids, 'asks': asks}


def generate_tick_data(
    symbol: str = 'EURUSD',
    count: int = 1000,
    start_price: float = 1.1000,
    spread_pips: float = 1.0,
    volatility: float = 0.00005,
    start_time: Optional[datetime] = None
) -> List[Dict]:
    """
    Generate realistic tick data.
    
    Args:
        symbol: Trading symbol
        count: Number of ticks
        start_price: Starting mid price
        spread_pips: Spread in pips
        volatility: Tick-to-tick volatility
        start_time: Starting timestamp
    
    Returns:
        List of tick dictionaries
    """
    if start_time is None:
        start_time = datetime.now() - timedelta(seconds=count)
    
    pip_size = 0.0001
    half_spread = spread_pips * pip_size / 2
    
    ticks = []
    mid_price = start_price
    
    for i in range(count):
        # Random walk for mid price
        mid_price += np.random.normal(0, volatility)
        
        # Variable spread
        current_spread = half_spread * random.uniform(0.8, 1.5)
        
        bid = mid_price - current_spread
        ask = mid_price + current_spread
        
        # Random time increment (average 1 second)
        time_delta = timedelta(milliseconds=random.randint(100, 2000))
        timestamp = start_time + timedelta(seconds=i) + time_delta
        
        ticks.append({
            'symbol': symbol,
            'timestamp': timestamp,
            'bid': round(bid, 5),
            'ask': round(ask, 5),
            'last': round(mid_price, 5),
            'volume': random.randint(1, 100),
        })
    
    return ticks


def generate_trade_data(
    symbol: str = 'EURUSD',
    count: int = 100,
    start_price: float = 1.1000,
    volatility: float = 0.0001,
    start_time: Optional[datetime] = None
) -> List[Dict]:
    """
    Generate realistic trade/execution data.
    
    Args:
        symbol: Trading symbol
        count: Number of trades
        start_price: Starting price
        volatility: Price volatility
        start_time: Starting timestamp
    
    Returns:
        List of trade dictionaries
    """
    if start_time is None:
        start_time = datetime.now() - timedelta(hours=count)
    
    trades = []
    price = start_price
    
    for i in range(count):
        # Random price movement
        price += np.random.normal(0, volatility)
        
        # Random trade characteristics
        side = random.choice(['buy', 'sell'])
        size = random.randint(1000, 100000)
        
        # Slippage
        slippage = random.uniform(-0.00005, 0.00005)
        execution_price = price + slippage
        
        # Fees
        fees = size * 0.00001  # 1 pip per 100k
        
        trades.append({
            'trade_id': f'T{i:06d}',
            'symbol': symbol,
            'side': side,
            'size': size,
            'price': round(execution_price, 5),
            'slippage': round(slippage, 6),
            'fees': round(fees, 2),
            'timestamp': start_time + timedelta(hours=i),
            'status': 'filled',
        })
    
    return trades


@dataclass
class MockMarketDataFeed:
    """
    Mock market data feed for testing.
    Simulates real-time market data streaming.
    """
    
    symbols: List[str] = None
    connected: bool = False
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        
        self.prices: Dict[str, Dict] = {}
        self.subscribers: Dict[str, List] = {}
        self._initialize_prices()
    
    def _initialize_prices(self):
        """Initialize prices for all symbols."""
        base_prices = {
            'EURUSD': 1.0850,
            'GBPUSD': 1.2650,
            'USDJPY': 149.50,
            'AUDUSD': 0.6550,
            'USDCAD': 1.3650,
            'USDCHF': 0.8850,
            'NZDUSD': 0.6050,
            'EURGBP': 0.8580,
            'EURJPY': 162.20,
            'GBPJPY': 189.10,
        }
        
        for symbol in self.symbols:
            base = base_prices.get(symbol, 1.0)
            spread = 0.0001 if 'JPY' not in symbol else 0.01
            
            self.prices[symbol] = {
                'bid': base - spread/2,
                'ask': base + spread/2,
                'last': base,
                'timestamp': datetime.now(),
            }
    
    def connect(self) -> bool:
        """Connect to data feed."""
        self.connected = True
        return True
    
    def disconnect(self) -> bool:
        """Disconnect from data feed."""
        self.connected = False
        return True
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self.connected
    
    def subscribe(self, symbol: str, callback=None) -> bool:
        """Subscribe to symbol updates."""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        if callback:
            self.subscribers[symbol].append(callback)
        return True
    
    def unsubscribe(self, symbol: str) -> bool:
        """Unsubscribe from symbol."""
        if symbol in self.subscribers:
            del self.subscribers[symbol]
        return True
    
    def get_price(self, symbol: str) -> Optional[Dict]:
        """Get current price for symbol."""
        if not self.connected:
            return None
        
        if symbol in self.prices:
            # Add small random variation
            price = self.prices[symbol].copy()
            variation = random.uniform(-0.00005, 0.00005)
            price['bid'] += variation
            price['ask'] += variation
            price['last'] += variation
            price['timestamp'] = datetime.now()
            return price
        
        return None
    
    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = 'H1',
        count: int = 100
    ) -> pd.DataFrame:
        """Get historical OHLCV data."""
        if not self.connected:
            return pd.DataFrame()
        
        start_price = self.prices.get(symbol, {}).get('last', 1.0)
        return generate_ohlcv_data(
            symbol=symbol,
            periods=count,
            timeframe=timeframe,
            start_price=start_price,
        )
    
    def get_order_book(self, symbol: str, levels: int = 10) -> Dict:
        """Get order book for symbol."""
        if not self.connected:
            return {'bids': [], 'asks': []}
        
        mid_price = self.prices.get(symbol, {}).get('last', 1.0)
        return generate_order_book(mid_price=mid_price, levels=levels)
    
    def simulate_tick(self, symbol: str):
        """Simulate a tick update."""
        if symbol in self.prices:
            # Random price movement
            variation = random.uniform(-0.0001, 0.0001)
            self.prices[symbol]['bid'] += variation
            self.prices[symbol]['ask'] += variation
            self.prices[symbol]['last'] += variation
            self.prices[symbol]['timestamp'] = datetime.now()
            
            # Notify subscribers
            for callback in self.subscribers.get(symbol, []):
                callback(self.prices[symbol])


def generate_correlation_matrix(symbols: List[str]) -> pd.DataFrame:
    """
    Generate a realistic correlation matrix for symbols.
    
    Args:
        symbols: List of trading symbols
    
    Returns:
        DataFrame with correlation matrix
    """
    n = len(symbols)
    
    # Start with identity matrix
    corr = np.eye(n)
    
    # Add realistic correlations
    for i in range(n):
        for j in range(i + 1, n):
            # Similar pairs have higher correlation
            if symbols[i][:3] == symbols[j][:3] or symbols[i][3:] == symbols[j][3:]:
                corr[i, j] = random.uniform(0.5, 0.9)
            else:
                corr[i, j] = random.uniform(-0.3, 0.5)
            corr[j, i] = corr[i, j]
    
    return pd.DataFrame(corr, index=symbols, columns=symbols)


def generate_volatility_surface(
    symbol: str = 'EURUSD',
    strikes: int = 10,
    expirations: int = 5
) -> pd.DataFrame:
    """
    Generate a volatility surface for options testing.
    
    Args:
        symbol: Trading symbol
        strikes: Number of strike prices
        expirations: Number of expiration dates
    
    Returns:
        DataFrame with volatility surface
    """
    # Generate strikes around ATM
    atm = 1.1000
    strike_range = np.linspace(atm * 0.95, atm * 1.05, strikes)
    
    # Generate expirations (days)
    exp_days = [7, 14, 30, 60, 90][:expirations]
    
    # Generate volatility surface with smile
    data = []
    for exp in exp_days:
        for strike in strike_range:
            # Base vol increases with time
            base_vol = 0.08 + 0.02 * np.sqrt(exp / 365)
            
            # Smile effect
            moneyness = strike / atm
            smile = 0.02 * (moneyness - 1) ** 2
            
            vol = base_vol + smile
            
            data.append({
                'symbol': symbol,
                'strike': round(strike, 4),
                'expiration_days': exp,
                'implied_vol': round(vol, 4),
            })
    
    return pd.DataFrame(data)
