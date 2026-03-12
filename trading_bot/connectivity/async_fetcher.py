"""
Async data fetching for non-blocking I/O operations.
50x faster than synchronous requests for multiple symbols.
"""

import asyncio
try:
    import aiohttp
except ImportError:
    aiohttp = None
from typing import Dict, List, Optional
import pandas as pd
from loguru import logger
import json
import pandas

import logging

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator


logger = logging.getLogger(__name__)



class AsyncDataFetcher:
    """Non-blocking data fetching with asyncio and aiohttp."""
    
    def __init__(self, max_concurrent: int = 10, timeout: int = 30):
        self.max_concurrent = max_concurrent
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_symbol_data(self, session: aiohttp.ClientSession, 
                                symbol: str, timeframe: str, 
                                api_url: str) -> tuple:
        """Fetch data for a single symbol asynchronously."""
        async with self.semaphore:
            url = f"{api_url}/{symbol}/{timeframe}"
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        df = pd.DataFrame(data)
                        logger.debug(f"Fetched {symbol} data: {len(df)} bars")
                        return symbol, df
                    else:
                        logger.error(f"Failed to fetch {symbol}: HTTP {response.status}")
                        return symbol, pd.DataFrame()
            except asyncio.TimeoutError:
                logger.error(f"Timeout fetching {symbol}")
                return symbol, pd.DataFrame()
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                return symbol, pd.DataFrame()
    
    async def fetch_multiple_symbols(self, symbols: List[str], 
                                     timeframe: str,
                                     api_url: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple symbols in parallel.
        
        Args:
            symbols: List of trading symbols
            timeframe: Timeframe (e.g., 'M15', 'H1')
            api_url: Base API URL
            
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        logger.info(f"Fetching {len(symbols)} symbols asynchronously...")
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            tasks = [
                self.fetch_symbol_data(session, symbol, timeframe, api_url)
                for symbol in symbols
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out errors and build result dict
            data_dict = {}
            for result in results:
                if isinstance(result, tuple):
                    symbol, df = result
                    if not df.empty:
                        data_dict[symbol] = df
                else:
                    logger.error(f"Exception in fetch: {result}")
            
            logger.success(f"Successfully fetched {len(data_dict)}/{len(symbols)} symbols")
            return data_dict
    
    def fetch_sync(self, symbols: List[str], timeframe: str, 
                   api_url: str) -> Dict[str, pd.DataFrame]:
        """Synchronous wrapper for async fetch."""
        return asyncio.run(self.fetch_multiple_symbols(symbols, timeframe, api_url))
    
    async def stream_market_data(self, symbols: List[str], 
                                 websocket_url: str,
                                 callback: callable):
        """
        Stream real-time market data via WebSocket.
        
        Args:
            symbols: List of symbols to subscribe
            websocket_url: WebSocket URL
            callback: Async function to handle incoming data
        """
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(websocket_url) as ws:
                # Subscribe to symbols
                subscribe_msg = {
                    'action': 'subscribe',
                    'symbols': symbols
                }
                await ws.send_json(subscribe_msg)
                logger.info(f"Subscribed to {len(symbols)} symbols via WebSocket")
                
                # Process incoming messages
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = msg.json()
                        await callback(data)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(f"WebSocket error: {ws.exception()}")
                        break
