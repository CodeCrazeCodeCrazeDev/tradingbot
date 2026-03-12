"""
Week 1 Assignment: Async Market Data Fetcher
Learn: asyncio, aiohttp, pandas, error handling

Goal: Fetch real-time data from multiple sources concurrently
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AsyncMarketDataFetcher:
    """Professional async data fetcher with error handling"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.session: aiohttp.ClientSession = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_yahoo_data(self, symbol: str) -> Dict:
        """Fetch data from Yahoo Finance API"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                'interval': '1d',
                'range': '5d'
            }
            
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_yahoo_response(data, symbol)
                else:
                    logger.error(f"Yahoo API error for {symbol}: {response.status}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {symbol} from Yahoo")
            return None
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return None
    
    def _parse_yahoo_response(self, data: Dict, symbol: str) -> Dict:
        """Parse Yahoo Finance response into clean format"""
        try:
            result = data['chart']['result'][0]
            timestamps = result['timestamp']
            quote = result['indicators']['quote'][0]
            
            df = pd.DataFrame({
                'timestamp': pd.to_datetime(timestamps, unit='s'),
                'open': quote['open'],
                'high': quote['high'],
                'low': quote['low'],
                'close': quote['close'],
                'volume': quote['volume']
            })
            
            return {
                'symbol': symbol,
                'data': df,
                'current_price': quote['close'][-1],
                'change_pct': ((quote['close'][-1] - quote['close'][0]) / quote['close'][0]) * 100
            }
        except Exception as e:
            logger.error(f"Error parsing Yahoo data: {e}")
            return None
    
    async def fetch_multiple_symbols(self, symbols: List[str]) -> Dict[str, Dict]:
        """Fetch data for multiple symbols concurrently"""
        tasks = [self.fetch_yahoo_data(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors and None values
        return {
            symbols[i]: results[i] 
            for i in range(len(symbols)) 
            if results[i] and not isinstance(results[i], Exception)
        }


async def main():
    """Main function demonstrating async data fetching"""
    
    # List of symbols to fetch
    symbols = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'SPY', 'GLD']
    
    logger.info(f"Fetching data for {len(symbols)} symbols...")
    start_time = datetime.now()
    
    # Use async context manager
    async with AsyncMarketDataFetcher() as fetcher:
        results = await fetcher.fetch_multiple_symbols(symbols)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Display results
    print(f"\n{'='*60}")
    print(f"Fetched {len(results)} symbols in {elapsed:.2f} seconds")
    print(f"{'='*60}\n")
    
    for symbol, data in results.items():
        if data:
            print(f"{symbol}:")
            print(f"  Current Price: ${data['current_price']:.4f}")
            print(f"  5-Day Change: {data['change_pct']:.2f}%")
            print(f"  Data Points: {len(data['data'])}")
            print()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())


# ============================================================================
# LEARNING EXERCISES:
# ============================================================================
# 
# 1. Add error retry logic with exponential backoff
# 2. Implement caching to avoid redundant API calls
# 3. Add rate limiting (max 5 requests per second)
# 4. Create a real-time streaming version using websockets
# 5. Add data validation (check for missing values, outliers)
# 
# CHALLENGE: Modify to fetch data from Alpha Vantage and FRED APIs
# ============================================================================
