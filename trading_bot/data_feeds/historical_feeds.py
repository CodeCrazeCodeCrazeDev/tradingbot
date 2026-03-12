"""
Historical Data Feeds
=====================

Historical data retrieval from multiple sources.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Historical data sources"""
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"
    TWELVE_DATA = "twelve_data"
    FRED = "fred"
    QUANDL = "quandl"


@dataclass
class HistoricalBar:
    """Historical OHLCV bar"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    adjusted_close: Optional[float] = None
    dividend: Optional[float] = None
    split: Optional[float] = None


class HistoricalDataFeed(ABC):
    """Base class for historical data feeds"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._cache: Dict[str, pd.DataFrame] = {}
        
    @abstractmethod
    async def fetch(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        timeframe: str = "1d"
    ) -> pd.DataFrame:
        """Fetch historical data"""
        pass
        
    def _to_datetime(self, date: Union[str, datetime]) -> datetime:
        """Convert to datetime"""
        if isinstance(date, str):
            return pd.to_datetime(date)
        return date
        
    def _cache_key(self, symbol: str, start: datetime, end: datetime, tf: str) -> str:
        """Generate cache key"""
        return f"{symbol}_{start.date()}_{end.date()}_{tf}"


class YahooFinanceFeed(HistoricalDataFeed):
    """Yahoo Finance historical data feed"""
    
    async def fetch(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        timeframe: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical data from Yahoo Finance.
        
        Args:
            symbol: Stock/ETF symbol
            start_date: Start date
            end_date: End date
            timeframe: Timeframe (1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo)
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            import yfinance as yf
            
            start = self._to_datetime(start_date)
            end = self._to_datetime(end_date)
            
            # Check cache
            cache_key = self._cache_key(symbol, start, end, timeframe)
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            # Map timeframe
            interval_map = {
                "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
                "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1wk", "1M": "1mo"
            }
            interval = interval_map.get(timeframe, "1d")
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start, end=end, interval=interval)
            
            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()
            
            # Standardize column names
            df.columns = [c.lower() for c in df.columns]
            
            # Ensure required columns
            required = ['open', 'high', 'low', 'close', 'volume']
            for col in required:
                if col not in df.columns:
                    df[col] = 0
                    
            # Cache result
            self._cache[cache_key] = df
            
            logger.info(f"Fetched {len(df)} bars for {symbol} from Yahoo Finance")
            return df
            
        except Exception as e:
            logger.error(f"Yahoo Finance fetch failed: {e}")
            return pd.DataFrame()
            
    async def fetch_multiple(
        self,
        symbols: List[str],
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        timeframe: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple symbols"""
        tasks = [
            self.fetch(symbol, start_date, end_date, timeframe)
            for symbol in symbols
        ]
        results = await asyncio.gather(*tasks)
        return dict(zip(symbols, results))
        
    async def fetch_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Fetch fundamental data"""
            
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'peg_ratio': info.get('pegRatio'),
                'price_to_book': info.get('priceToBook'),
                'dividend_yield': info.get('dividendYield'),
                'eps': info.get('trailingEps'),
                'revenue': info.get('totalRevenue'),
                'profit_margin': info.get('profitMargins'),
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'beta': info.get('beta'),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
                'avg_volume': info.get('averageVolume'),
                'sector': info.get('sector'),
                'industry': info.get('industry')
            }
            
        except Exception as e:
            logger.error(f"Fundamentals fetch failed: {e}")
            return {}


class AlphaVantageFeed(HistoricalDataFeed):
    """Alpha Vantage historical data feed"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    async def fetch(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        timeframe: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical data from Alpha Vantage.
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            timeframe: Timeframe (1m, 5m, 15m, 30m, 1h, 1d, 1w, 1M)
            
        Returns:
            DataFrame with OHLCV data
        """
        if not self.api_key:
            logger.warning("Alpha Vantage API key not set")
            return pd.DataFrame()
        try:
            
            import aiohttp
            
            start = self._to_datetime(start_date)
            end = self._to_datetime(end_date)
            
            # Map timeframe to function
            if timeframe in ['1m', '5m', '15m', '30m', '1h']:
                function = "TIME_SERIES_INTRADAY"
                interval = timeframe.replace('m', 'min').replace('h', 'min')
                if timeframe == '1h':
                    interval = '60min'
            elif timeframe == '1d':
                function = "TIME_SERIES_DAILY_ADJUSTED"
                interval = None
            elif timeframe == '1w':
                function = "TIME_SERIES_WEEKLY_ADJUSTED"
                interval = None
            else:
                function = "TIME_SERIES_MONTHLY_ADJUSTED"
                interval = None
                
            params = {
                "function": function,
                "symbol": symbol,
                "apikey": self.api_key,
                "outputsize": "full"
            }
            
            if interval:
                params["interval"] = interval
                
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Alpha Vantage error: {response.status}")
                        return pd.DataFrame()
                        
                    data = await response.json()
                    
            # Find the time series key
            ts_key = None
            for key in data.keys():
                if 'Time Series' in key:
                    ts_key = key
                    break
                    
            if not ts_key:
                logger.error(f"No time series data in response: {data.keys()}")
                return pd.DataFrame()
                
            # Parse data
            records = []
            for timestamp, values in data[ts_key].items():
                record = {
                    'timestamp': pd.to_datetime(timestamp),
                    'open': float(values.get('1. open', 0)),
                    'high': float(values.get('2. high', 0)),
                    'low': float(values.get('3. low', 0)),
                    'close': float(values.get('4. close', 0)),
                    'volume': float(values.get('5. volume', values.get('6. volume', 0)))
                }
                
                # Add adjusted close if available
                if '5. adjusted close' in values:
                    record['adjusted_close'] = float(values['5. adjusted close'])
                    
                records.append(record)
                
            df = pd.DataFrame(records)
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            # Filter by date range
            df = df[(df.index >= start) & (df.index <= end)]
            
            logger.info(f"Fetched {len(df)} bars for {symbol} from Alpha Vantage")
            return df
            
        except Exception as e:
            logger.error(f"Alpha Vantage fetch failed: {e}")
            return pd.DataFrame()


class FREDFeed(HistoricalDataFeed):
    """FRED (Federal Reserve Economic Data) feed"""
    
    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
    
    # Common FRED series
    SERIES = {
        'GDP': 'GDP',
        'UNEMPLOYMENT': 'UNRATE',
        'INFLATION': 'CPIAUCSL',
        'FED_FUNDS': 'FEDFUNDS',
        'TREASURY_10Y': 'DGS10',
        'TREASURY_2Y': 'DGS2',
        'VIX': 'VIXCLS',
        'SP500': 'SP500',
        'HOUSING_STARTS': 'HOUST',
        'RETAIL_SALES': 'RSAFS',
        'INDUSTRIAL_PRODUCTION': 'INDPRO',
        'CONSUMER_SENTIMENT': 'UMCSENT'
    }
    
    async def fetch(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        timeframe: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch economic data from FRED.
        
        Args:
            symbol: FRED series ID or common name
            start_date: Start date
            end_date: End date
            timeframe: Ignored for FRED (uses native frequency)
            
        Returns:
            DataFrame with economic data
        """
        if not self.api_key:
            logger.warning("FRED API key not set")
            return pd.DataFrame()
        try:
            
            
            start = self._to_datetime(start_date)
            end = self._to_datetime(end_date)
            
            # Map common names to series IDs
            series_id = self.SERIES.get(symbol.upper(), symbol)
            
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "observation_start": start.strftime("%Y-%m-%d"),
                "observation_end": end.strftime("%Y-%m-%d")
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params) as response:
                    if response.status != 200:
                        logger.error(f"FRED error: {response.status}")
                        return pd.DataFrame()
                        
                    data = await response.json()
                    
            observations = data.get('observations', [])
            
            records = []
            for obs in observations:
                if obs['value'] != '.':  # FRED uses '.' for missing values
                    records.append({
                        'timestamp': pd.to_datetime(obs['date']),
                        'value': float(obs['value'])
                    })
                    
            df = pd.DataFrame(records)
            if not df.empty:
                df.set_index('timestamp', inplace=True)
                
            logger.info(f"Fetched {len(df)} observations for {series_id} from FRED")
            return df
            
        except Exception as e:
            logger.error(f"FRED fetch failed: {e}")
            return pd.DataFrame()
            
    async def fetch_multiple_series(
        self,
        series: List[str],
        start_date: Union[str, datetime],
        end_date: Union[str, datetime]
    ) -> pd.DataFrame:
        """Fetch multiple FRED series and combine"""
        tasks = [
            self.fetch(s, start_date, end_date)
            for s in series
        ]
        results = await asyncio.gather(*tasks)
        
        # Combine into single DataFrame
        combined = pd.DataFrame()
        for series_name, df in zip(series, results):
            if not df.empty:
                combined[series_name] = df['value']
                
        return combined


def create_historical_feed(
    source: str = "yahoo",
    api_key: Optional[str] = None
) -> HistoricalDataFeed:
    """
    Factory function to create historical data feed.
    
    Args:
        source: Data source (yahoo, alpha_vantage, fred)
        api_key: API key if required
        
    Returns:
        HistoricalDataFeed instance
    """
    source = source.lower()
    
    if source in ['yahoo', 'yahoo_finance', 'yf']:
        return YahooFinanceFeed(api_key)
    elif source in ['alpha_vantage', 'av']:
        return AlphaVantageFeed(api_key)
    elif source == 'fred':
        return FREDFeed(api_key)
    else:
        raise ValueError(f"Unknown source: {source}")


if __name__ == "__main__":
    async def main():
        # Test Yahoo Finance
        print("\n=== Yahoo Finance ===")
        yahoo = create_historical_feed('yahoo')
        df = await yahoo.fetch('AAPL', '2024-01-01', '2024-12-01', '1d')
        print(f"AAPL: {len(df)} bars")
        print(df.tail())
        
        # Test fundamentals
        print("\n=== Fundamentals ===")
        fundamentals = await yahoo.fetch_fundamentals('AAPL')
        for key, value in list(fundamentals.items())[:5]:
            print(f"  {key}: {value}")
            
        # Test multiple symbols
        print("\n=== Multiple Symbols ===")
        data = await yahoo.fetch_multiple(['AAPL', 'MSFT', 'GOOGL'], '2024-01-01', '2024-12-01')
        for symbol, df in data.items():
            print(f"  {symbol}: {len(df)} bars")
            
    asyncio.run(main())
