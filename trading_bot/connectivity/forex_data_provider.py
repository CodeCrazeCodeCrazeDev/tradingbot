"""
Forex Data Provider
===================

Real-time and historical forex data from free sources.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
import aiohttp

logger = logging.getLogger(__name__)


class ForexPair(Enum):
    """Major forex pairs"""
    EURUSD = "EURUSD"
    GBPUSD = "GBPUSD"
    USDJPY = "USDJPY"
    USDCHF = "USDCHF"
    AUDUSD = "AUDUSD"
    USDCAD = "USDCAD"
    NZDUSD = "NZDUSD"
    EURGBP = "EURGBP"
    EURJPY = "EURJPY"
    GBPJPY = "GBPJPY"


@dataclass
class ForexQuote:
    """Forex quote data"""
    pair: str
    bid: float
    ask: float
    mid: float
    spread: float
    timestamp: datetime
    source: str = ""
    
    @property
    def spread_pips(self) -> float:
        """Spread in pips"""
        if 'JPY' in self.pair:
            return self.spread * 100
        return self.spread * 10000


@dataclass
class ForexOHLCV:
    """Forex OHLCV data"""
    pair: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0


class ForexDataProvider:
    """
    Forex data provider using free APIs.
    
    Sources:
    - exchangerate-api.com (free tier: 1500 requests/month)
    - frankfurter.app (free, unlimited)
    - fcsapi.com (free tier available)
    """
    
    # Currency codes for API calls
    PAIR_TO_CURRENCIES = {
        'EURUSD': ('EUR', 'USD'),
        'GBPUSD': ('GBP', 'USD'),
        'USDJPY': ('USD', 'JPY'),
        'USDCHF': ('USD', 'CHF'),
        'AUDUSD': ('AUD', 'USD'),
        'USDCAD': ('USD', 'CAD'),
        'NZDUSD': ('NZD', 'USD'),
        'EURGBP': ('EUR', 'GBP'),
        'EURJPY': ('EUR', 'JPY'),
        'GBPJPY': ('GBP', 'JPY'),
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 60  # seconds
        
    async def get_quote(self, pair: str) -> Optional[ForexQuote]:
        """
        Get real-time forex quote.
        
        Args:
            pair: Currency pair (e.g., 'EURUSD')
            
        Returns:
            ForexQuote or None
        """
        pair = pair.upper().replace('/', '')
        
        # Check cache
        cache_key = f"quote_{pair}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if (datetime.now() - cached['timestamp']).total_seconds() < self._cache_ttl:
                return cached['data']
        
        # Try multiple sources
        quote = await self._get_frankfurter_quote(pair)
        if not quote:
            quote = await self._get_exchangerate_quote(pair)
            
        if quote:
            self._cache[cache_key] = {
                'data': quote,
                'timestamp': datetime.now()
            }
            
        return quote
    
    async def _get_frankfurter_quote(self, pair: str) -> Optional[ForexQuote]:
        """Get quote from Frankfurter API (free, unlimited)"""
        try:
            if pair not in self.PAIR_TO_CURRENCIES:
                return None
                
            base, quote_curr = self.PAIR_TO_CURRENCIES[pair]
            url = f"https://api.frankfurter.app/latest?from={base}&to={quote_curr}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        rate = data.get('rates', {}).get(quote_curr)
                        
                        if rate:
                            # Frankfurter doesn't provide bid/ask, estimate spread
                            spread = rate * 0.0002  # ~2 pip spread estimate
                            
                            return ForexQuote(
                                pair=pair,
                                bid=rate - spread/2,
                                ask=rate + spread/2,
                                mid=rate,
                                spread=spread,
                                timestamp=datetime.now(),
                                source='frankfurter'
                            )
            return None
            
        except Exception as e:
            logger.error(f"Frankfurter API error: {e}")
            return None
    
    async def _get_exchangerate_quote(self, pair: str) -> Optional[ForexQuote]:
        """Get quote from ExchangeRate-API (free tier)"""
        try:
            if pair not in self.PAIR_TO_CURRENCIES:
                return None
                
            base, quote_curr = self.PAIR_TO_CURRENCIES[pair]
            url = f"https://api.exchangerate-api.com/v4/latest/{base}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        rate = data.get('rates', {}).get(quote_curr)
                        
                        if rate:
                            spread = rate * 0.0002
                            
                            return ForexQuote(
                                pair=pair,
                                bid=rate - spread/2,
                                ask=rate + spread/2,
                                mid=rate,
                                spread=spread,
                                timestamp=datetime.now(),
                                source='exchangerate-api'
                            )
            return None
            
        except Exception as e:
            logger.error(f"ExchangeRate-API error: {e}")
            return None
    
    async def get_multiple_quotes(self, pairs: List[str]) -> Dict[str, Optional[ForexQuote]]:
        """Get quotes for multiple pairs"""
        tasks = [self.get_quote(pair) for pair in pairs]
        results = await asyncio.gather(*tasks)
        return dict(zip(pairs, results))
    
    async def get_historical(
        self,
        pair: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[ForexOHLCV]:
        """
        Get historical forex data.
        
        Args:
            pair: Currency pair
            start_date: Start date
            end_date: End date
            
        Returns:
            List of ForexOHLCV
        """
        try:
            if pair not in self.PAIR_TO_CURRENCIES:
                return []
                
            base, quote_curr = self.PAIR_TO_CURRENCIES[pair]
            
            # Frankfurter supports historical data
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            url = f"https://api.frankfurter.app/{start_str}..{end_str}?from={base}&to={quote_curr}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = data.get('rates', {})
                        
                        ohlcv_list = []
                        for date_str, rate_data in sorted(rates.items()):
                            rate = rate_data.get(quote_curr)
                            if rate:
                                ohlcv = ForexOHLCV(
                                    pair=pair,
                                    timestamp=datetime.strptime(date_str, '%Y-%m-%d'),
                                    open=rate,
                                    high=rate * 1.001,  # Estimate
                                    low=rate * 0.999,
                                    close=rate,
                                    volume=0
                                )
                                ohlcv_list.append(ohlcv)
                                
                        return ohlcv_list
            return []
            
        except Exception as e:
            logger.error(f"Historical data error: {e}")
            return []
    
    async def get_all_major_quotes(self) -> Dict[str, Optional[ForexQuote]]:
        """Get quotes for all major pairs"""
        major_pairs = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF',
            'AUDUSD', 'USDCAD', 'NZDUSD'
        ]
        return await self.get_multiple_quotes(major_pairs)
    
    def get_supported_pairs(self) -> List[str]:
        """Get list of supported pairs"""
        return list(self.PAIR_TO_CURRENCIES.keys())


# Factory function
def create_forex_provider(config: Optional[Dict] = None) -> ForexDataProvider:
    """Create forex data provider"""
    return ForexDataProvider(config)


if __name__ == "__main__":
    async def main():
        provider = create_forex_provider()
        
        print("=== Forex Data Provider Demo ===\n")
        
        # Get single quote
        print("1. Single Quote:")
        quote = await provider.get_quote('EURUSD')
        if quote:
            print(f"   EUR/USD: {quote.mid:.5f} (spread: {quote.spread_pips:.1f} pips)")
        
        # Get all major quotes
        print("\n2. Major Pairs:")
        quotes = await provider.get_all_major_quotes()
        for pair, q in quotes.items():
            if q:
                print(f"   {pair}: {q.mid:.5f}")
        
        # Get historical data
        print("\n3. Historical Data (last 7 days):")
        end = datetime.now()
        start = end - timedelta(days=7)
        history = await provider.get_historical('EURUSD', start, end)
        for ohlcv in history[-3:]:
            print(f"   {ohlcv.timestamp.date()}: {ohlcv.close:.5f}")
            
    asyncio.run(main())
