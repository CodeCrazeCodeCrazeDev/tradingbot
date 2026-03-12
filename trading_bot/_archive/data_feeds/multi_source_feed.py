"""
Multi-Source Data Feed
======================

Aggregates data from multiple sources with failover and quality scoring.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from collections import deque
import threading
import numpy as np

logger = logging.getLogger(__name__)


class DataFeedSource(Enum):
    """Available data feed sources"""
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    FRED = "fred"
    QUANDL = "quandl"
    IEX_CLOUD = "iex_cloud"
    FINNHUB = "finnhub"
    TWELVE_DATA = "twelve_data"
    COINGECKO = "coingecko"


class DataQuality(Enum):
    """Data quality levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    UNUSABLE = "unusable"


@dataclass
class FeedConfig:
    """Configuration for a data feed source"""
    source: DataFeedSource
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    rate_limit: int = 100  # requests per minute
    timeout: float = 30.0
    retry_count: int = 3
    priority: int = 1  # Lower is higher priority
    enabled: bool = True
    supported_symbols: List[str] = field(default_factory=list)
    supported_timeframes: List[str] = field(default_factory=list)


@dataclass
class DataPoint:
    """Single data point from a feed"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: DataFeedSource
    quality_score: float = 1.0
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeedHealth:
    """Health status of a data feed"""
    source: DataFeedSource
    is_healthy: bool = True
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    success_rate: float = 1.0
    avg_latency_ms: float = 0.0
    error_count: int = 0
    consecutive_failures: int = 0


class DataFeedAdapter:
    """Base adapter for data feeds"""
    
    def __init__(self, config: FeedConfig):
        self.config = config
        self.health = FeedHealth(source=config.source)
        self._request_times: deque = deque(maxlen=100)
        self._latencies: deque = deque(maxlen=100)
        
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100
    ) -> List[DataPoint]:
        """Fetch OHLCV data - to be implemented by subclasses"""
        
        """Fetch real-time price - to be implemented by subclasses"""
        
    def _record_success(self, latency_ms: float):
        """Record successful request"""
        self.health.last_success = datetime.now()
        self.health.consecutive_failures = 0
        self._latencies.append(latency_ms)
        self.health.avg_latency_ms = np.mean(self._latencies)
        self._update_success_rate()
        
    def _record_failure(self, error: str):
        """Record failed request"""
        self.health.last_failure = datetime.now()
        self.health.error_count += 1
        self.health.consecutive_failures += 1
        self._update_success_rate()
        
        if self.health.consecutive_failures >= 5:
            self.health.is_healthy = False
            logger.warning(f"Feed {self.config.source.value} marked unhealthy after {self.health.consecutive_failures} failures")
            
    def _update_success_rate(self):
        """Update success rate"""
        total = len(self._request_times) + self.health.error_count
        if total > 0:
            self.health.success_rate = len(self._request_times) / total


class YahooFinanceAdapter(DataFeedAdapter):
    """Yahoo Finance data adapter"""
    
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100
    ) -> List[DataPoint]:
        """Fetch OHLCV from Yahoo Finance"""
        try:
            import yfinance as yf
            
            start_time = datetime.now()
            
            # Map timeframe to yfinance interval
            interval_map = {
                "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
                "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1wk", "1M": "1mo"
            }
            interval = interval_map.get(timeframe, "1h")
            
            # Calculate period based on limit
            period_map = {
                "1m": "7d", "5m": "60d", "15m": "60d", "30m": "60d",
                "1h": "730d", "4h": "730d", "1d": "max", "1w": "max", "1M": "max"
            }
            period = period_map.get(timeframe, "60d")
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                self._record_failure("No data returned")
                return []
            
            # Limit results
            df = df.tail(limit)
            
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self._record_success(latency)
            
            data_points = []
            for idx, row in df.iterrows():
                dp = DataPoint(
                    symbol=symbol,
                    timestamp=idx.to_pydatetime(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=float(row['Volume']),
                    source=DataFeedSource.YAHOO_FINANCE,
                    latency_ms=latency
                )
                data_points.append(dp)
                
            return data_points
            
        except Exception as e:
            self._record_failure(str(e))
            logger.error(f"Yahoo Finance fetch failed: {e}")
            return []
            
    async def fetch_realtime(self, symbol: str) -> Optional[DataPoint]:
        """Fetch real-time price from Yahoo Finance"""
            
        try:
            start_time = datetime.now()
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self._record_success(latency)
            
            price = info.get('regularMarketPrice') or info.get('currentPrice')
            if price is None:
                return None
                
            return DataPoint(
                symbol=symbol,
                timestamp=datetime.now(),
                open=price,
                high=info.get('dayHigh', price),
                low=info.get('dayLow', price),
                close=price,
                volume=info.get('volume', 0),
                source=DataFeedSource.YAHOO_FINANCE,
                latency_ms=latency,
                metadata={
                    'bid': info.get('bid'),
                    'ask': info.get('ask'),
                    'market_cap': info.get('marketCap')
                }
            )
            
        except Exception as e:
            self._record_failure(str(e))
            logger.error(f"Yahoo Finance realtime fetch failed: {e}")
            return None


class CoinGeckoAdapter(DataFeedAdapter):
    """CoinGecko data adapter for crypto"""
    
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100
    ) -> List[DataPoint]:
        """Fetch OHLCV from CoinGecko"""
        try:
            import aiohttp
            
            start_time = datetime.now()
            
            # Map symbol to CoinGecko ID
            symbol_map = {
                'BTC': 'bitcoin', 'ETH': 'ethereum', 'BNB': 'binancecoin',
                'SOL': 'solana', 'XRP': 'ripple', 'ADA': 'cardano',
                'DOGE': 'dogecoin', 'DOT': 'polkadot', 'MATIC': 'matic-network'
            }
            coin_id = symbol_map.get(symbol.upper().replace('USDT', '').replace('USD', ''), symbol.lower())
            
            # Calculate days based on timeframe
            days_map = {"1h": 30, "4h": 90, "1d": 365, "1w": 730}
            days = days_map.get(timeframe, 30)
            
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
            params = {"vs_currency": "usd", "days": days}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as response:
                    if response.status != 200:
                        self._record_failure(f"HTTP {response.status}")
                        return []
                        
                    data = await response.json()
                    
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self._record_success(latency)
            
            data_points = []
            for candle in data[-limit:]:
                timestamp, open_p, high, low, close = candle
                dp = DataPoint(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(timestamp / 1000),
                    open=float(open_p),
                    high=float(high),
                    low=float(low),
                    close=float(close),
                    volume=0,  # CoinGecko OHLC doesn't include volume
                    source=DataFeedSource.COINGECKO,
                    latency_ms=latency
                )
                data_points.append(dp)
                
            return data_points
            
        except Exception as e:
            self._record_failure(str(e))
            logger.error(f"CoinGecko fetch failed: {e}")
            return []
            
    async def fetch_realtime(self, symbol: str) -> Optional[DataPoint]:
        """Fetch real-time price from CoinGecko"""
            
        try:
            start_time = datetime.now()
            
            symbol_map = {
                'BTC': 'bitcoin', 'ETH': 'ethereum', 'BNB': 'binancecoin',
                'SOL': 'solana', 'XRP': 'ripple', 'ADA': 'cardano'
            }
            coin_id = symbol_map.get(symbol.upper().replace('USDT', '').replace('USD', ''), symbol.lower())
            
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_vol": "true",
                "include_24hr_change": "true"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as response:
                    if response.status != 200:
                        self._record_failure(f"HTTP {response.status}")
                        return None
                        
                    data = await response.json()
                    
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self._record_success(latency)
            
            if coin_id not in data:
                return None
                
            price_data = data[coin_id]
            price = price_data.get('usd', 0)
            
            return DataPoint(
                symbol=symbol,
                timestamp=datetime.now(),
                open=price,
                high=price,
                low=price,
                close=price,
                volume=price_data.get('usd_24h_vol', 0),
                source=DataFeedSource.COINGECKO,
                latency_ms=latency,
                metadata={
                    'change_24h': price_data.get('usd_24h_change')
                }
            )
            
        except Exception as e:
            self._record_failure(str(e))
            logger.error(f"CoinGecko realtime fetch failed: {e}")
            return None


class MultiSourceDataFeed:
    """
    Multi-source data feed with automatic failover and quality scoring.
    
    Features:
    - Multiple data source support
    - Automatic failover on source failure
    - Data quality scoring
    - Latency tracking
    - Rate limiting
    """
    
    def __init__(self, configs: Optional[List[FeedConfig]] = None):
        self.configs = configs or []
        self.adapters: Dict[DataFeedSource, DataFeedAdapter] = {}
        self._lock = threading.Lock()
        self._cache: Dict[str, DataPoint] = {}
        self._cache_ttl = 5  # seconds
        
        # Initialize default adapters
        self._init_default_adapters()
        
        logger.info(f"MultiSourceDataFeed initialized with {len(self.adapters)} adapters")
        
    def _init_default_adapters(self):
        """Initialize default adapters"""
        # Yahoo Finance (free, no API key needed)
        yahoo_config = FeedConfig(
            source=DataFeedSource.YAHOO_FINANCE,
            priority=1,
            rate_limit=100
        )
        self.adapters[DataFeedSource.YAHOO_FINANCE] = YahooFinanceAdapter(yahoo_config)
        
        # CoinGecko (free, no API key needed)
        coingecko_config = FeedConfig(
            source=DataFeedSource.COINGECKO,
            priority=2,
            rate_limit=50
        )
        self.adapters[DataFeedSource.COINGECKO] = CoinGeckoAdapter(coingecko_config)
        
    def add_adapter(self, adapter: DataFeedAdapter):
        """Add a data feed adapter"""
        with self._lock:
            self.adapters[adapter.config.source] = adapter
            logger.info(f"Added adapter: {adapter.config.source.value}")
            
    def get_healthy_adapters(self) -> List[DataFeedAdapter]:
        """Get list of healthy adapters sorted by priority"""
        healthy = [a for a in self.adapters.values() if a.health.is_healthy]
        return sorted(healthy, key=lambda x: x.config.priority)
        
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
        preferred_source: Optional[DataFeedSource] = None
    ) -> List[DataPoint]:
        """
        Fetch OHLCV data with automatic failover.
        
        Args:
            symbol: Trading symbol
            timeframe: Candle timeframe
            limit: Number of candles
            preferred_source: Preferred data source
            
        Returns:
            List of DataPoint objects
        """
        adapters = self.get_healthy_adapters()
        
        # Put preferred source first if specified
        if preferred_source and preferred_source in self.adapters:
            preferred = self.adapters[preferred_source]
            if preferred.health.is_healthy:
                adapters = [preferred] + [a for a in adapters if a != preferred]
                
        for adapter in adapters:
            try:
                data = await adapter.fetch_ohlcv(symbol, timeframe, limit)
                if data:
                    # Score data quality
                    for dp in data:
                        dp.quality_score = self._calculate_quality_score(dp, adapter)
                    return data
            except Exception as e:
                logger.warning(f"Adapter {adapter.config.source.value} failed: {e}")
                continue
                
        logger.error(f"All adapters failed for {symbol}")
        return []
        
    async def fetch_realtime(
        self,
        symbol: str,
        use_cache: bool = True
    ) -> Optional[DataPoint]:
        """
        Fetch real-time price with caching.
        
        Args:
            symbol: Trading symbol
            use_cache: Whether to use cached data
            
        Returns:
            DataPoint or None
        """
        # Check cache
        if use_cache:
            cache_key = f"rt_{symbol}"
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                age = (datetime.now() - cached.timestamp).total_seconds()
                if age < self._cache_ttl:
                    return cached
                    
        adapters = self.get_healthy_adapters()
        
        for adapter in adapters:
            try:
                data = await adapter.fetch_realtime(symbol)
                if data:
                    data.quality_score = self._calculate_quality_score(data, adapter)
                    self._cache[f"rt_{symbol}"] = data
                    return data
            except Exception as e:
                logger.warning(f"Realtime fetch failed for {adapter.config.source.value}: {e}")
                continue
                
        return None
        
    async def fetch_multiple(
        self,
        symbols: List[str],
        timeframe: str = "1h",
        limit: int = 100
    ) -> Dict[str, List[DataPoint]]:
        """
        Fetch data for multiple symbols concurrently.
        
        Args:
            symbols: List of trading symbols
            timeframe: Candle timeframe
            limit: Number of candles per symbol
            
        Returns:
            Dictionary mapping symbols to DataPoint lists
        """
        tasks = [
            self.fetch_ohlcv(symbol, timeframe, limit)
            for symbol in symbols
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        data = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {symbol}: {result}")
                data[symbol] = []
            else:
                data[symbol] = result
                
        return data
        
    def _calculate_quality_score(
        self,
        data_point: DataPoint,
        adapter: DataFeedAdapter
    ) -> float:
        """Calculate data quality score"""
        score = 1.0
        
        # Penalize high latency
        if data_point.latency_ms > 1000:
            score -= 0.1
        elif data_point.latency_ms > 5000:
            score -= 0.3
            
        # Penalize low success rate
        if adapter.health.success_rate < 0.9:
            score -= 0.1
        elif adapter.health.success_rate < 0.7:
            score -= 0.3
            
        # Penalize stale data
        age = (datetime.now() - data_point.timestamp).total_seconds()
        if age > 60:
            score -= 0.1
        elif age > 300:
            score -= 0.3
            
        # Validate OHLC consistency
        if not (data_point.low <= data_point.open <= data_point.high and
                data_point.low <= data_point.close <= data_point.high):
            score -= 0.5
            
        return max(0.0, min(1.0, score))
        
    def get_health_report(self) -> Dict[str, Any]:
        """Get health report for all adapters"""
        return {
            source.value: {
                'is_healthy': adapter.health.is_healthy,
                'success_rate': adapter.health.success_rate,
                'avg_latency_ms': adapter.health.avg_latency_ms,
                'error_count': adapter.health.error_count,
                'last_success': adapter.health.last_success.isoformat() if adapter.health.last_success else None,
                'last_failure': adapter.health.last_failure.isoformat() if adapter.health.last_failure else None
            }
            for source, adapter in self.adapters.items()
        }


def create_multi_source_feed(configs: Optional[List[FeedConfig]] = None) -> MultiSourceDataFeed:
    """Factory function to create MultiSourceDataFeed"""
    return MultiSourceDataFeed(configs)


if __name__ == "__main__":
    
    async def main():
        feed = create_multi_source_feed()
        
        # Test Yahoo Finance
        print("\n=== Testing Yahoo Finance ===")
        data = await feed.fetch_ohlcv("AAPL", "1d", 10)
        print(f"Got {len(data)} candles for AAPL")
        if data:
            print(f"Latest: {data[-1].close} at {data[-1].timestamp}")
            
        # Test CoinGecko
        print("\n=== Testing CoinGecko ===")
        data = await feed.fetch_ohlcv("BTC", "1d", 10)
        print(f"Got {len(data)} candles for BTC")
        if data:
            print(f"Latest: {data[-1].close} at {data[-1].timestamp}")
            
        # Test realtime
        print("\n=== Testing Realtime ===")
        rt = await feed.fetch_realtime("AAPL")
        if rt:
            print(f"AAPL realtime: ${rt.close}")
            
        # Health report
        print("\n=== Health Report ===")
        health = feed.get_health_report()
        for source, status in health.items():
            print(f"{source}: healthy={status['is_healthy']}, success_rate={status['success_rate']:.2%}")
            
    asyncio.run(main())
