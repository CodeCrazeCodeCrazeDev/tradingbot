"""
Week 2 Assignment: Data Integration (Fixed Version)
Uses your Alpha Vantage and FRED API keys
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DataIntegrationHub:
    """Multi-source data integration with your API keys"""
    
    def __init__(self):
        self.av_key = os.getenv('ALPHA_VANTAGE_KEY')
        self.fred_key = os.getenv('FRED_API_KEY')
        self.session: aiohttp.ClientSession = None
        
        print(f"Alpha Vantage Key: {self.av_key[:10]}..." if self.av_key else "No AV key")
        print(f"FRED Key: {self.fred_key[:10]}..." if self.fred_key else "No FRED key")
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_forex_daily(self, from_currency: str = 'EUR', to_currency: str = 'USD'):
        """Fetch daily forex data from Alpha Vantage"""
        if not self.av_key:
            print("ERROR: Alpha Vantage API key not set")
            return None
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'FX_DAILY',
                'from_symbol': from_currency,
                'to_symbol': to_currency,
                'apikey': self.av_key,
                'outputsize': 'compact'
            }
            
            print(f"\nFetching {from_currency}/{to_currency} from Alpha Vantage...")
            
            async with self.session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for API limit
                    if 'Note' in data:
                        print(f"  API Limit: {data['Note']}")
                        return None
                    
                    if 'Time Series FX (Daily)' in data:
                        time_series = data['Time Series FX (Daily)']
                        
                        df = pd.DataFrame.from_dict(time_series, orient='index')
                        df.index = pd.to_datetime(df.index)
                        df.columns = ['open', 'high', 'low', 'close']
                        df = df.astype(float)
                        df = df.sort_index()
                        
                        print(f"  SUCCESS: Received {len(df)} days of data")
                        print(f"  Latest: {df.index[-1].date()} - Close: {df['close'].iloc[-1]:.5f}")
                        
                        return df
                    else:
                        print(f"  ERROR: Unexpected response format")
                        print(f"  Keys: {list(data.keys())}")
                        return None
                else:
                    print(f"  ERROR: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            print(f"  ERROR: {e}")
            return None
    
    async def fetch_economic_data(self, series_id: str = 'DFF'):
        """Fetch economic data from FRED"""
        if not self.fred_key:
            print("ERROR: FRED API key not set")
            return None
        
        try:
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.fred_key,
                'file_type': 'json',
                'limit': 100
            }
            
            print(f"\nFetching {series_id} from FRED...")
            
            async with self.session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'observations' in data:
                        observations = data['observations']
                        df = pd.DataFrame(observations)
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.set_index('date')
                        df['value'] = pd.to_numeric(df['value'], errors='coerce')
                        df = df[['value']].dropna()
                        
                        print(f"  SUCCESS: Received {len(df)} observations")
                        print(f"  Latest: {df.index[-1].date()} - Value: {df['value'].iloc[-1]:.2f}%")
                        
                        return df
                    else:
                        print(f"  ERROR: No observations in response")
                        return None
                else:
                    print(f"  ERROR: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            print(f"  ERROR: {e}")
            return None


async def main():
    """Demonstration of data integration"""
    
    print("="*70)
    print("MULTI-SOURCE DATA INTEGRATION DEMO")
    print("="*70)
    
    async with DataIntegrationHub() as hub:
        
        # Test 1: Fetch EURUSD
        eurusd = await hub.fetch_forex_daily('EUR', 'USD')
        
        # Test 2: Fetch GBPUSD
        gbpusd = await hub.fetch_forex_daily('GBP', 'USD')
        
        # Test 3: Fetch Federal Funds Rate
        fed_funds = await hub.fetch_economic_data('DFF')
        
        # Test 4: Fetch GDP
        gdp = await hub.fetch_economic_data('GDP')
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        
        success_count = sum([
            eurusd is not None,
            gbpusd is not None,
            fed_funds is not None,
            gdp is not None
        ])
        
        print(f"\nSuccessful fetches: {success_count}/4")
        
        if success_count >= 2:
            print("\nCONGRATULATIONS! Data integration working!")
            print("\nNext steps:")
            print("1. Add more currency pairs")
            print("2. Implement caching")
            print("3. Add data validation")
            print("4. Store in database")
        else:
            print("\nNote: Alpha Vantage has rate limits (5 calls/minute)")
            print("Wait 1 minute and try again if you hit the limit")


if __name__ == "__main__":
    asyncio.run(main())
