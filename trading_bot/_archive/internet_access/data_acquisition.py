"""
Phase 2: Multi-Source Data Acquisition System
Pulls market data, news, sentiment, and macroeconomic data from the internet.
"""

import asyncio
import json
import random
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from enum import Enum

try:
    import aiohttp
except ImportError:
    aiohttp = None

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Types of data sources"""
    MARKET_DATA = "market_data"
    NEWS = "news"
    SENTIMENT = "sentiment"
    MACRO = "macro"
    TECHNICAL = "technical"


@dataclass
class DataPoint:
    """Single data point with metadata"""
    source: DataSource
    timestamp: datetime
    symbol: Optional[str]
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'source': self.source.value,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'data': self.data,
            'metadata': self.metadata
        }


class DataAcquisitionEngine:
    """
    Acquires data from multiple internet sources and caches it locally.
    Supports multi-timeframe market data, news, sentiment, and macro data.
    """
    
    def __init__(self, config: Dict, cache_dir: str = "data_cache"):
        self.config = config
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # API configurations
        self.api_keys = config.get('api_keys', {})
        self.endpoints = config.get('endpoints', {})
        
        # Data cache
        self.data_cache: Dict[str, List[DataPoint]] = {
            source.value: [] for source in DataSource
        }
        
        # Rate limiting
        self.rate_limits: Dict[str, int] = {}
        self.last_request: Dict[str, datetime] = {}
        
    async def _rate_limit_check(self, source: str, requests_per_minute: int = 60):
        """Implement rate limiting for API calls"""
        if source in self.last_request:
            elapsed = (datetime.now() - self.last_request[source]).total_seconds()
            min_interval = 60.0 / requests_per_minute
            
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                logger.debug(f"Rate limiting {source}: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
        
        self.last_request[source] = datetime.now()
    
    async def fetch_market_data(
        self,
        symbol: str,
        timeframes: List[str] = ['1m', '5m', '1h', '4h', '1d', '1w']
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch multi-timeframe market data for a symbol.
        Returns dict of {timeframe: DataFrame}
        """
        logger.info(f"📊 Fetching market data for {symbol} across {len(timeframes)} timeframes")
        
        market_data = {}
        
        for tf in timeframes:
            try:
                await self._rate_limit_check('market_data')
                
                # Fetch data (implement your broker API here)
                df = await self._fetch_ohlcv(symbol, tf)
                
                if df is not None and not df.empty:
                    market_data[tf] = df
                    
                    # Cache the data
                    data_point = DataPoint(
                        source=DataSource.MARKET_DATA,
                        timestamp=datetime.now(),
                        symbol=symbol,
                        data={
                            'timeframe': tf,
                            'bars': len(df),
                            'latest_close': float(df['close'].iloc[-1]) if len(df) > 0 else None
                        },
                        metadata={'timeframe': tf}
                    )
                    self._cache_data(data_point)
                    
                    logger.debug(f"  ✓ {tf}: {len(df)} bars")
                else:
                    logger.warning(f"  ✗ {tf}: No data received")
            
            except Exception as e:
                logger.error(f"Error fetching {symbol} {tf}: {e}")
        
        # Save to disk
        self._save_market_data(symbol, market_data)
        
        return market_data
    
    async def _fetch_ohlcv(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data from broker/data provider.
        This is a placeholder - implement with your actual data provider.
        """
        # Example implementation for Alpha Vantage, Yahoo Finance, or your broker
        endpoint = self.endpoints.get('market_data', {}).get('url')
        
        if not endpoint:
            # Return mock data for demonstration
            logger.warning("No market data endpoint configured, using mock data")
            return self._generate_mock_ohlcv(symbol, timeframe)
        try:
        
            async with aiohttp.ClientSession() as session:
                params = {
                    'symbol': symbol,
                    'interval': timeframe,
                    'apikey': self.api_keys.get('market_data')
                }
                
                async with session.get(endpoint, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Parse response into DataFrame
                        return self._parse_market_data(data)
                    else:
                        logger.error(f"Market data API returned {response.status}")
                        return None
        
        except Exception as e:
            logger.error(f"Error fetching OHLCV: {e}")
            return None
    
    def _generate_mock_ohlcv(self, symbol: str, timeframe: str, bars: int = 100) -> pd.DataFrame:
        """Generate mock OHLCV data for testing"""
        import numpy as np
        
        dates = pd.date_range(end=datetime.now(), periods=bars, freq='1min')
        base_price = 1.1000
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': base_price + np.random.randn(bars) * 0.001,
            'high': base_price + np.random.randn(bars) * 0.001 + 0.0005,
            'low': base_price + np.random.randn(bars) * 0.001 - 0.0005,
            'close': base_price + np.random.randn(bars) * 0.001,
            'volume': np.random.randint(1000, 10000, bars)
        })
        
        return df
    
    def _parse_market_data(self, data: Dict) -> pd.DataFrame:
        """Parse API response into DataFrame"""
        # Implement based on your data provider's format
        # This is a placeholder
        return pd.DataFrame()
    
    async def fetch_news_headlines(
        self,
        symbols: List[str],
        limit: int = 50
    ) -> List[Dict]:
        """
        Fetch top news headlines related to trading assets.
        """
        logger.info(f"📰 Fetching news headlines for {len(symbols)} symbols")
        
        await self._rate_limit_check('news', requests_per_minute=30)
        
        headlines = []
        
        try:
            # Use NewsAPI, Finnhub, or similar
            endpoint = self.endpoints.get('news', {}).get('url', 'https://newsapi.org/v2/everything')
            api_key = self.api_keys.get('news')
            
            if not api_key:
                logger.warning("No news API key configured, using mock data")
                headlines = self._generate_mock_news(symbols, limit)
            else:
                async with aiohttp.ClientSession() as session:
                    query = ' OR '.join(symbols)
                    params = {
                        'q': query,
                        'apiKey': api_key,
                        'language': 'en',
                        'sortBy': 'publishedAt',
                        'pageSize': limit
                    }
                    
                    async with session.get(endpoint, params=params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            headlines = data.get('articles', [])
                        else:
                            logger.error(f"News API returned {response.status}")
            
            # Cache news data
            for article in headlines:
                data_point = DataPoint(
                    source=DataSource.NEWS,
                    timestamp=datetime.now(),
                    symbol=None,
                    data=article,
                    metadata={'source': 'news_api'}
                )
                self._cache_data(data_point)
            
            # Save to disk
            self._save_news(headlines)
            
            logger.info(f"  ✓ Retrieved {len(headlines)} news articles")
        
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
        
        return headlines
    
    def _generate_mock_news(self, symbols: List[str], limit: int) -> List[Dict]:
        """Generate mock news for testing"""
        news = []
        for i in range(min(limit, 10)):
            news.append({
                'title': f'Market Update: {symbols[0] if symbols else "Markets"} shows movement',
                'description': 'Analysis of recent market movements and trends',
                'publishedAt': datetime.now().isoformat(),
                'source': {'name': 'Mock News'},
                'sentiment': 'neutral'
            })
        return news
    
    async def fetch_sentiment_metrics(
        self,
        symbols: List[str]
    ) -> Dict[str, Dict]:
        """
        Gather social sentiment metrics from Twitter, Reddit, etc.
        """
        logger.info(f"💬 Fetching sentiment metrics for {len(symbols)} symbols")
        
        await self._rate_limit_check('sentiment', requests_per_minute=20)
        
        sentiment_data = {}
        
        for symbol in symbols:
            try:
                # Use sentiment API (e.g., Sentiment Investor, LunarCrush)
                endpoint = self.endpoints.get('sentiment', {}).get('url')
                api_key = self.api_keys.get('sentiment')
                
                if not api_key:
                    # Mock sentiment data
                    sentiment = self._generate_mock_sentiment(symbol)
                else:
                    async with aiohttp.ClientSession() as session:
                        params = {
                            'symbol': symbol,
                            'apikey': api_key
                        }
                        
                        async with session.get(endpoint, params=params, timeout=10) as response:
                            if response.status == 200:
                                sentiment = await response.json()
                            else:
                                sentiment = self._generate_mock_sentiment(symbol)
                
                sentiment_data[symbol] = sentiment
                
                # Cache sentiment
                data_point = DataPoint(
                    source=DataSource.SENTIMENT,
                    timestamp=datetime.now(),
                    symbol=symbol,
                    data=sentiment,
                    metadata={'source': 'sentiment_api'}
                )
                self._cache_data(data_point)
                
                logger.debug(f"  ✓ {symbol}: sentiment score {sentiment.get('score', 0):.2f}")
            
            except Exception as e:
                logger.error(f"Error fetching sentiment for {symbol}: {e}")
        
        # Save to disk
        self._save_sentiment(sentiment_data)
        
        return sentiment_data
    
    def _generate_mock_sentiment(self, symbol: str) -> Dict:
        """Generate mock sentiment data"""
        return {
            'symbol': symbol,
            'score': random.uniform(-1, 1),
            'volume': random.randint(1000, 100000),
            'positive': random.uniform(0.3, 0.7),
            'negative': random.uniform(0.1, 0.3),
            'neutral': random.uniform(0.2, 0.4)
        }
    
    async def fetch_macro_data(self) -> Dict[str, Any]:
        """
        Collect macroeconomic data (unemployment, interest rates, etc.)
        """
        logger.info("📈 Fetching macroeconomic indicators")
        
        await self._rate_limit_check('macro', requests_per_minute=10)
        
        macro_data = {}
        
        try:
            # Use FRED API, Trading Economics, or similar
            endpoint = self.endpoints.get('macro', {}).get('url')
            api_key = self.api_keys.get('macro')
            
            indicators = [
                'unemployment_rate',
                'interest_rate',
                'inflation_rate',
                'gdp_growth',
                'consumer_confidence'
            ]
            
            if not api_key:
                # Mock macro data
                for indicator in indicators:
                    macro_data[indicator] = self._generate_mock_macro(indicator)
            else:
                async with aiohttp.ClientSession() as session:
                    for indicator in indicators:
                        try:
                            params = {
                                'series_id': indicator,
                                'api_key': api_key
                            }
                            
                            async with session.get(endpoint, params=params, timeout=10) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    macro_data[indicator] = data
                                else:
                                    macro_data[indicator] = self._generate_mock_macro(indicator)
                        
                        except Exception as e:
                            logger.error(f"Error fetching {indicator}: {e}")
                            macro_data[indicator] = self._generate_mock_macro(indicator)
            
            # Cache macro data
            data_point = DataPoint(
                source=DataSource.MACRO,
                timestamp=datetime.now(),
                symbol=None,
                data=macro_data,
                metadata={'indicators': list(macro_data.keys())}
            )
            self._cache_data(data_point)
            
            # Save to disk
            self._save_macro(macro_data)
            
            logger.info(f"  ✓ Retrieved {len(macro_data)} macro indicators")
        
        except Exception as e:
            logger.error(f"Error fetching macro data: {e}")
        
        return macro_data
    
    def _generate_mock_macro(self, indicator: str) -> Dict:
        """Generate mock macro data"""
        return {
            'indicator': indicator,
            'value': random.uniform(0, 10),
            'timestamp': datetime.now().isoformat(),
            'unit': '%'
        }
    
    def _cache_data(self, data_point: DataPoint):
        """Add data point to in-memory cache"""
        source_key = data_point.source.value
        self.data_cache[source_key].append(data_point)
        
        # Keep only last 1000 points per source
        if len(self.data_cache[source_key]) > 1000:
            self.data_cache[source_key] = self.data_cache[source_key][-1000:]
    
    def _save_market_data(self, symbol: str, data: Dict[str, pd.DataFrame]):
        """Save market data to disk"""
        try:
            market_dir = self.cache_dir / 'market_data'
            market_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            for tf, df in data.items():
                filename = market_dir / f"{symbol}_{tf}_{timestamp}.csv"
                df.to_csv(filename, index=False)
            
            logger.debug(f"Saved market data for {symbol}")
        
        except Exception as e:
            logger.error(f"Error saving market data: {e}")
    
    def _save_news(self, headlines: List[Dict]):
        """Save news to disk"""
        try:
            news_dir = self.cache_dir / 'news'
            news_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = news_dir / f"news_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'count': len(headlines),
                    'articles': headlines
                }, f, indent=2)
            
            logger.debug(f"Saved {len(headlines)} news articles")
        
        except Exception as e:
            logger.error(f"Error saving news: {e}")
    
    def _save_sentiment(self, sentiment_data: Dict):
        """Save sentiment data to disk"""
        try:
            sentiment_dir = self.cache_dir / 'sentiment'
            sentiment_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = sentiment_dir / f"sentiment_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'data': sentiment_data
                }, f, indent=2)
            
            logger.debug(f"Saved sentiment data for {len(sentiment_data)} symbols")
        
        except Exception as e:
            logger.error(f"Error saving sentiment: {e}")
    
    def _save_macro(self, macro_data: Dict):
        """Save macro data to disk"""
        try:
            macro_dir = self.cache_dir / 'macro'
            macro_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = macro_dir / f"macro_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'data': macro_data
                }, f, indent=2)
            
            logger.debug(f"Saved macro data")
        
        except Exception as e:
            logger.error(f"Error saving macro data: {e}")
    
    async def acquire_all_data(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Acquire all data types concurrently.
        Returns comprehensive data package.
        """
        logger.info(f"🌐 Starting comprehensive data acquisition for {len(symbols)} symbols")
        
        # Run all acquisitions concurrently
        results = await asyncio.gather(
            self.fetch_market_data(symbols[0] if symbols else 'EURUSD'),
            self.fetch_news_headlines(symbols),
            self.fetch_sentiment_metrics(symbols),
            self.fetch_macro_data(),
            return_exceptions=True
        )
        
        market_data, news, sentiment, macro = results
        
        # Handle exceptions
        if isinstance(market_data, Exception):
            logger.error(f"Market data acquisition failed: {market_data}")
            market_data = {}
        
        if isinstance(news, Exception):
            logger.error(f"News acquisition failed: {news}")
            news = []
        
        if isinstance(sentiment, Exception):
            logger.error(f"Sentiment acquisition failed: {sentiment}")
            sentiment = {}
        
        if isinstance(macro, Exception):
            logger.error(f"Macro acquisition failed: {macro}")
            macro = {}
        
        data_package = {
            'timestamp': datetime.now().isoformat(),
            'symbols': symbols,
            'market_data': market_data,
            'news': news,
            'sentiment': sentiment,
            'macro': macro
        }
        
        logger.info("✅ Data acquisition complete")
        
        return data_package
    
    def get_cached_data(
        self,
        source: DataSource,
        symbol: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[DataPoint]:
        """Retrieve cached data with optional filtering"""
        data = self.data_cache.get(source.value, [])
        
        # Filter by symbol
        if symbol:
            data = [d for d in data if d.symbol == symbol]
        
        # Filter by time
        if since:
            data = [d for d in data if d.timestamp >= since]
        
        return data
