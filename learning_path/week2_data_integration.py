"""
Week 2 Assignment: Multi-Source Data Integration
Learn: API integration, data validation, error handling

APIs to integrate:
1. Alpha Vantage (forex, stocks)
2. FRED (economic data)
3. Yahoo Finance (backup)
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MarketData:
    """Standardized market data structure"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str


class DataIntegrationHub:
    """Professional multi-source data integration"""
    
    def __init__(self, alpha_vantage_key: str = None, fred_key: str = None):
        self.av_key = alpha_vantage_key or os.getenv('ALPHA_VANTAGE_KEY')
        self.fred_key = fred_key or os.getenv('FRED_API_KEY')
        self.session: aiohttp.ClientSession = None
        
        # Data cache to reduce API calls
        self.cache: Dict[str, pd.DataFrame] = {}
        self.cache_expiry: Dict[str, datetime] = {}
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_forex_data(self, symbol: str, interval: str = '5min') -> Optional[pd.DataFrame]:
        """Fetch forex data from Alpha Vantage"""
        if not self.av_key:
            logger.error("Alpha Vantage API key not set")
            return None
        
        # Check cache first
        cache_key = f"{symbol}_{interval}"
        if self._is_cache_valid(cache_key):
            logger.info(f"Using cached data for {symbol}")
            return self.cache[cache_key]
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'FX_INTRADAY',
                'from_symbol': symbol[:3],
                'to_symbol': symbol[3:],
                'interval': interval,
                'apikey': self.av_key,
                'outputsize': 'full'
            }
            
            async with self.session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    df = self._parse_alpha_vantage_forex(data, symbol)
                    
                    # Cache the result
                    self.cache[cache_key] = df
                    self.cache_expiry[cache_key] = datetime.now() + timedelta(minutes=5)
                    
                    return df
                else:
                    logger.error(f"Alpha Vantage API error: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching forex data: {e}")
            return None
    
    def _parse_alpha_vantage_forex(self, data: Dict, symbol: str) -> pd.DataFrame:
        """Parse Alpha Vantage forex response"""
        try:
            time_series_key = [k for k in data.keys() if 'Time Series' in k][0]
            time_series = data[time_series_key]
            
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df.columns = ['open', 'high', 'low', 'close']
            df = df.astype(float)
            df['symbol'] = symbol
            df['source'] = 'AlphaVantage'
            
            return df.sort_index()
        except Exception as e:
            logger.error(f"Error parsing Alpha Vantage data: {e}")
            return pd.DataFrame()
    
    async def fetch_economic_data(self, series_id: str) -> Optional[pd.DataFrame]:
        """Fetch economic data from FRED"""
        if not self.fred_key:
            logger.error("FRED API key not set")
            return None
        
        try:
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.fred_key,
                'file_type': 'json'
            }
            
            async with self.session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_fred_data(data, series_id)
                else:
                    logger.error(f"FRED API error: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching FRED data: {e}")
            return None
    
    def _parse_fred_data(self, data: Dict, series_id: str) -> pd.DataFrame:
        """Parse FRED response"""
        try:
            observations = data['observations']
            df = pd.DataFrame(observations)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df['series_id'] = series_id
            
            return df[['value', 'series_id']].dropna()
        except Exception as e:
            logger.error(f"Error parsing FRED data: {e}")
            return pd.DataFrame()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        if cache_key not in self.cache_expiry:
            return False
        return datetime.now() < self.cache_expiry[cache_key]
    
    async def get_multi_source_data(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """Fetch data from multiple sources and compare"""
        tasks = {
            'alpha_vantage': self.fetch_forex_data(symbol),
            # Add more sources here
        }
        
        results = {}
        for source, task in tasks.items():
            try:
                data = await task
                if data is not None and not data.empty:
                    results[source] = data
            except Exception as e:
                logger.error(f"Error fetching from {source}: {e}")
        
        return results
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """Validate data quality"""
        if df.empty:
            logger.warning("Empty dataframe")
            return False
        
        # Check for missing values
        missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
        if missing_pct > 5:
            logger.warning(f"High missing data: {missing_pct:.1f}%")
            return False
        
        # Check for outliers (price changes > 10%)
        if 'close' in df.columns:
            returns = df['close'].pct_change()
            outliers = (returns.abs() > 0.10).sum()
            if outliers > len(df) * 0.01:  # More than 1% outliers
                logger.warning(f"High number of outliers: {outliers}")
                return False
        
        logger.info("Data validation passed ✅")
        return True


async def main():
    """Demonstration of data integration"""
    
    print("="*70)
    print("MULTI-SOURCE DATA INTEGRATION DEMO")
    print("="*70)
    
    # You need to set these environment variables or pass them directly
    # export ALPHA_VANTAGE_KEY="your_key"
    # export FRED_API_KEY="your_key"
    
    async with DataIntegrationHub() as hub:
        
        # Test 1: Fetch forex data
        print("\n1. Fetching EURUSD data from Alpha Vantage...")
        forex_data = await hub.fetch_forex_data('EURUSD', interval='5min')
        
        if forex_data is not None:
            print(f"   ✅ Received {len(forex_data)} data points")
            print(f"   Latest price: {forex_data['close'].iloc[-1]:.5f}")
            
            # Validate data
            is_valid = hub.validate_data(forex_data)
            print(f"   Data quality: {'✅ PASS' if is_valid else '❌ FAIL'}")
        
        # Test 2: Fetch economic data
        print("\n2. Fetching Federal Funds Rate from FRED...")
        fed_funds = await hub.fetch_economic_data('DFF')
        
        if fed_funds is not None:
            print(f"   ✅ Received {len(fed_funds)} data points")
            print(f"   Latest rate: {fed_funds['value'].iloc[-1]:.2f}%")
        
        # Test 3: Multi-source comparison
        print("\n3. Fetching from multiple sources...")
        multi_data = await hub.get_multi_source_data('EURUSD')
        
        for source, data in multi_data.items():
            print(f"   {source}: {len(data)} points")


if __name__ == "__main__":
    asyncio.run(main())
    
    print("\n" + "="*70)
    print("EXERCISES:")
    print("="*70)
    print("""
1. Add Yahoo Finance as a backup data source
2. Implement data reconciliation (compare prices from different sources)
3. Add automatic failover (if one source fails, use another)
4. Implement data storage (save to SQLite/PostgreSQL)
5. Add real-time streaming using websockets
6. Create data quality dashboard

CHALLENGE: Build a data pipeline that:
- Fetches data every 5 minutes
- Validates quality
- Stores in database
- Alerts on anomalies
    """)
