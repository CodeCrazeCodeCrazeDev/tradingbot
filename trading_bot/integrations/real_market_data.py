"""
Real Market Data Integration
Replaces mock implementations with actual free API integrations
"""

import asyncio
try:
    import aiohttp
except ImportError:
    aiohttp = None
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd
import numpy as np
import json
import os
from typing import Set
from enum import auto
import numpy
import pandas

logger = logging.getLogger(__name__)


class DataProvider(Enum):
    """Available data providers"""
    YAHOO_FINANCE = "yahoo"
    COINGECKO = "coingecko"
    ALPHA_VANTAGE = "alphavantage"
    FRED = "fred"
    FINNHUB = "finnhub"
    POLYGON = "polygon"
    BINANCE = "binance"


@dataclass
class MarketDataConfig:
    """Configuration for market data providers"""
    alpha_vantage_key: str = ""
    fred_key: str = ""
    finnhub_key: str = ""
    polygon_key: str = ""
    cache_ttl_seconds: int = 60
    rate_limit_per_minute: int = 5


class RealMarketDataProvider:
    """
    Unified real market data provider using FREE APIs
    Replaces Bloomberg mock with actual data sources
    """
    
    def __init__(self, config: Optional[MarketDataConfig] = None):
        self.config = config or MarketDataConfig()
        
        # Load API keys from environment
        self.config.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', self.config.alpha_vantage_key)
        self.config.fred_key = os.getenv('FRED_API_KEY', self.config.fred_key)
        self.config.finnhub_key = os.getenv('FINNHUB_API_KEY', self.config.finnhub_key)
        self.config.polygon_key = os.getenv('POLYGON_API_KEY', self.config.polygon_key)
        
        # Cache for rate limiting
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # Rate limiting
        self._request_times: List[datetime] = []
        
        # Session for async requests
        self._session: Optional[aiohttp.ClientSession] = None
        
        logger.info("Real market data provider initialized")
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
        
    async def _rate_limit(self):
        """Enforce rate limiting"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self._request_times = [t for t in self._request_times if t > minute_ago]
        
        # Wait if at limit
        if len(self._request_times) >= self.config.rate_limit_per_minute:
            wait_time = (self._request_times[0] - minute_ago).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                
        self._request_times.append(now)
        
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self._cache:
            timestamp = self._cache_timestamps.get(key)
            if timestamp and (datetime.now() - timestamp).total_seconds() < self.config.cache_ttl_seconds:
                return self._cache[key]
        return None
        
    def _set_cached(self, key: str, value: Any):
        """Set cached value"""
        self._cache[key] = value
        self._cache_timestamps[key] = datetime.now()
        
    # ==================== YAHOO FINANCE (FREE, NO API KEY) ====================
    
    async def get_stock_price_yahoo(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time stock price from Yahoo Finance
        FREE - No API key required
        """
        cache_key = f"yahoo_price_{symbol}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
            
        await self._rate_limit()
        
        try:
            session = await self._get_session()
            
            # Yahoo Finance API endpoint
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                'interval': '1d',
                'range': '5d'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    result = data.get('chart', {}).get('result', [{}])[0]
                    meta = result.get('meta', {})
                    
                    price_data = {
                        'symbol': symbol,
                        'price': meta.get('regularMarketPrice', 0),
                        'previous_close': meta.get('previousClose', 0),
                        'open': meta.get('regularMarketOpen', 0),
                        'high': meta.get('regularMarketDayHigh', 0),
                        'low': meta.get('regularMarketDayLow', 0),
                        'volume': meta.get('regularMarketVolume', 0),
                        'market_cap': meta.get('marketCap', 0),
                        'currency': meta.get('currency', 'USD'),
                        'exchange': meta.get('exchangeName', ''),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'yahoo_finance'
                    }
                    
                    self._set_cached(cache_key, price_data)
                    logger.info(f"Yahoo Finance: {symbol} = ${price_data['price']:.2f}")
                    return price_data
                else:
                    logger.warning(f"Yahoo Finance API error: {response.status}")
                    return {'error': f'API error: {response.status}'}
                    
        except Exception as e:
            logger.error(f"Yahoo Finance request failed: {e}")
            return {'error': str(e)}
            
    async def get_historical_data_yahoo(self, symbol: str, period: str = '1y') -> pd.DataFrame:
        """
        Get historical OHLCV data from Yahoo Finance
        FREE - No API key required
        """
        cache_key = f"yahoo_hist_{symbol}_{period}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
            
        await self._rate_limit()
        
        try:
            session = await self._get_session()
            
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                'interval': '1d',
                'range': period
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    result = data.get('chart', {}).get('result', [{}])[0]
                    timestamps = result.get('timestamp', [])
                    indicators = result.get('indicators', {}).get('quote', [{}])[0]
                    
                    df = pd.DataFrame({
                        'timestamp': pd.to_datetime(timestamps, unit='s'),
                        'open': indicators.get('open', []),
                        'high': indicators.get('high', []),
                        'low': indicators.get('low', []),
                        'close': indicators.get('close', []),
                        'volume': indicators.get('volume', [])
                    })
                    
                    df.set_index('timestamp', inplace=True)
                    df.dropna(inplace=True)
                    
                    self._set_cached(cache_key, df)
                    logger.info(f"Yahoo Finance historical: {symbol} - {len(df)} bars")
                    return df
                    
        except Exception as e:
            logger.error(f"Yahoo Finance historical request failed: {e}")
            
        return pd.DataFrame()
        
    # ==================== COINGECKO (FREE, NO API KEY) ====================
    
    async def get_crypto_price_coingecko(self, coin_id: str) -> Dict[str, Any]:
        """
        Get real-time crypto price from CoinGecko
        FREE - No API key required (rate limited)
        """
        cache_key = f"coingecko_price_{coin_id}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
            
        await self._rate_limit()
        
        try:
            session = await self._get_session()
            
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'community_data': 'false',
                'developer_data': 'false'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    market_data = data.get('market_data', {})
                    
                    price_data = {
                        'symbol': data.get('symbol', '').upper(),
                        'name': data.get('name', ''),
                        'price': market_data.get('current_price', {}).get('usd', 0),
                        'market_cap': market_data.get('market_cap', {}).get('usd', 0),
                        'volume_24h': market_data.get('total_volume', {}).get('usd', 0),
                        'change_24h': market_data.get('price_change_percentage_24h', 0),
                        'change_7d': market_data.get('price_change_percentage_7d', 0),
                        'ath': market_data.get('ath', {}).get('usd', 0),
                        'atl': market_data.get('atl', {}).get('usd', 0),
                        'circulating_supply': market_data.get('circulating_supply', 0),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'coingecko'
                    }
                    
                    self._set_cached(cache_key, price_data)
                    logger.info(f"CoinGecko: {coin_id} = ${price_data['price']:.2f}")
                    return price_data
                    
        except Exception as err:
            logger.error(f"CoinGecko request failed: {err}")
            return {'error': str(err)}
        
    async def get_crypto_historical_coingecko(self, coin_id: str, days: int = 365) -> pd.DataFrame:
        """
        Get historical crypto data from CoinGecko
        FREE - No API key required
        """
        cache_key = f"coingecko_hist_{coin_id}_{days}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
            
        await self._rate_limit()
        
        try:
            session = await self._get_session()
            
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    prices = data.get('prices', [])
                    volumes = data.get('total_volumes', [])
                    
                    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df['volume'] = [v[1] for v in volumes] if volumes else 0
                    df.set_index('timestamp', inplace=True)
                    
                    self._set_cached(cache_key, df)
                    logger.info(f"CoinGecko historical: {coin_id} - {len(df)} data points")
                    return df
                    
        except Exception as e:
            logger.error(f"CoinGecko historical request failed: {e}")
            
        return pd.DataFrame()
        
    # ==================== FRED (FREE WITH API KEY) ====================
    
    async def get_economic_data_fred(self, series_id: str) -> pd.DataFrame:
        """
        Get economic data from FRED (Federal Reserve)
        FREE - Requires API key
        
        Popular series:
        - GDP: Gross Domestic Product
        - UNRATE: Unemployment Rate
        - CPIAUCSL: Consumer Price Index
        - FEDFUNDS: Federal Funds Rate
        - T10Y2Y: 10Y-2Y Treasury Spread
        - VIXCLS: VIX Index
        """
        if not self.config.fred_key:
            logger.warning("FRED API key not configured")
            return pd.DataFrame()
            
        cache_key = f"fred_{series_id}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
            
        await self._rate_limit()
        
        try:
            session = await self._get_session()
            
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.config.fred_key,
                'file_type': 'json',
                'observation_start': (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    observations = data.get('observations', [])
                    
                    df = pd.DataFrame(observations)
                    df['date'] = pd.to_datetime(df['date'])
                    df['value'] = pd.to_numeric(df['value'], errors='coerce')
                    df.set_index('date', inplace=True)
                    df = df[['value']].dropna()
                    
                    self._set_cached(cache_key, df)
                    logger.info(f"FRED: {series_id} - {len(df)} observations")
                    return df
                    
        except Exception as e:
            logger.error(f"FRED request failed: {e}")
            
        return pd.DataFrame()
        
    # ==================== BINANCE (FREE, NO API KEY FOR PUBLIC DATA) ====================
    
    async def get_crypto_price_binance(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time crypto price from Binance
        FREE - No API key required for public data
        """
        cache_key = f"binance_price_{symbol}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
            
        await self._rate_limit()
        
        try:
            session = await self._get_session()
            
            url = "https://api.binance.com/api/v3/ticker/24hr"
            params = {'symbol': symbol}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    price_data = {
                        'symbol': data.get('symbol', ''),
                        'price': float(data.get('lastPrice', 0)),
                        'bid': float(data.get('bidPrice', 0)),
                        'ask': float(data.get('askPrice', 0)),
                        'high_24h': float(data.get('highPrice', 0)),
                        'low_24h': float(data.get('lowPrice', 0)),
                        'volume_24h': float(data.get('volume', 0)),
                        'quote_volume_24h': float(data.get('quoteVolume', 0)),
                        'change_24h': float(data.get('priceChangePercent', 0)),
                        'trades_24h': int(data.get('count', 0)),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'binance'
                    }
                    
                    self._set_cached(cache_key, price_data)
                    logger.info(f"Binance: {symbol} = ${price_data['price']:.2f}")
                    return price_data
                    
        except Exception as err:
            logger.error(f"Binance request failed: {err}")
            return {'error': str(err)}
        
    async def get_crypto_klines_binance(self, symbol: str, interval: str = '1d', 
                                        limit: int = 500) -> pd.DataFrame:
        """
        Get historical klines (OHLCV) from Binance
        FREE - No API key required
        """
        cache_key = f"binance_klines_{symbol}_{interval}_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
            
        await self._rate_limit()
        
        try:
            session = await self._get_session()
            
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    df = pd.DataFrame(data, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                        'taker_buy_quote', 'ignore'
                    ])
                    
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = pd.to_numeric(df[col])
                        
                    df.set_index('timestamp', inplace=True)
                    df = df[['open', 'high', 'low', 'close', 'volume']]
                    
                    self._set_cached(cache_key, df)
                    logger.info(f"Binance klines: {symbol} - {len(df)} bars")
                    return df
                    
        except Exception as e:
            logger.error(f"Binance klines request failed: {e}")
            
        return pd.DataFrame()
        
    # ==================== ALPHA VANTAGE (FREE WITH API KEY) ====================
    
    async def get_stock_quote_alphavantage(self, symbol: str) -> Dict[str, Any]:
        """
        Get stock quote from Alpha Vantage
        FREE tier: 5 calls/minute, 500 calls/day
        """
        if not self.config.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return {'error': 'API key not configured'}
            
        cache_key = f"av_quote_{symbol}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
            
        await self._rate_limit()
        
        try:
            session = await self._get_session()
            
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.config.alpha_vantage_key
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    quote = data.get('Global Quote', {})
                    
                    price_data = {
                        'symbol': quote.get('01. symbol', symbol),
                        'price': float(quote.get('05. price', 0)),
                        'open': float(quote.get('02. open', 0)),
                        'high': float(quote.get('03. high', 0)),
                        'low': float(quote.get('04. low', 0)),
                        'volume': int(quote.get('06. volume', 0)),
                        'previous_close': float(quote.get('08. previous close', 0)),
                        'change': float(quote.get('09. change', 0)),
                        'change_percent': quote.get('10. change percent', '0%'),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'alpha_vantage'
                    }
                    
                    self._set_cached(cache_key, price_data)
                    return price_data
                    
        except Exception as err:
            logger.error(f"Alpha Vantage request failed: {err}")
            return {'error': str(err)}
        
    # ==================== UNIFIED INTERFACE ====================
    
    async def get_price(self, symbol: str, asset_type: str = 'auto') -> Dict[str, Any]:
        """
        Get price for any asset type
        Automatically selects the best data source
        """
        # Determine asset type
        if asset_type == 'auto':
            if symbol.endswith('USDT') or symbol.endswith('BTC'):
                asset_type = 'crypto_binance'
            elif symbol.lower() in ['bitcoin', 'ethereum', 'solana', 'cardano']:
                asset_type = 'crypto_coingecko'
            else:
                asset_type = 'stock'
                
        # Route to appropriate provider
        if asset_type == 'crypto_binance':
            return await self.get_crypto_price_binance(symbol)
        elif asset_type == 'crypto_coingecko':
            return await self.get_crypto_price_coingecko(symbol)
        elif asset_type == 'stock':
            # Try Yahoo first (free), then Alpha Vantage
            result = await self.get_stock_price_yahoo(symbol)
            if 'error' not in result:
                return result
            return await self.get_stock_quote_alphavantage(symbol)
        else:
            return {'error': f'Unknown asset type: {asset_type}'}
            
    async def get_historical(self, symbol: str, asset_type: str = 'auto', 
                            period: str = '1y') -> pd.DataFrame:
        """
        Get historical data for any asset type
        """
        if asset_type == 'auto':
            if symbol.endswith('USDT') or symbol.endswith('BTC'):
                asset_type = 'crypto_binance'
            elif symbol.lower() in ['bitcoin', 'ethereum', 'solana', 'cardano']:
                asset_type = 'crypto_coingecko'
            else:
                asset_type = 'stock'
                
        if asset_type == 'crypto_binance':
            return await self.get_crypto_klines_binance(symbol, '1d', 365)
        elif asset_type == 'crypto_coingecko':
            return await self.get_crypto_historical_coingecko(symbol, 365)
        elif asset_type == 'stock':
            return await self.get_historical_data_yahoo(symbol, period)
        else:
            return pd.DataFrame()
            
    async def close(self):
        """Close the session"""
        if self._session and not self._session.closed:
            await self._session.close()


# Convenience function
async def get_real_market_data():
    """Get a configured real market data provider"""
    return RealMarketDataProvider()
