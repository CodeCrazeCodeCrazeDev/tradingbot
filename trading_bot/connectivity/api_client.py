"""
Elite Trading Bot - API Client

This module provides specialized API client functionality for interacting with
financial market data providers and trading platforms.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .web_client import WebClient, RequestMethod
from .auth_manager import AuthManager
from .rate_limiter import RateLimiter

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


class APIClient:
    """
    API client for interacting with financial data providers and trading platforms.
    
    Features:
    - Authentication handling with API keys
    - Rate limiting to comply with API restrictions
    - Response parsing and error handling
    - Pagination support
    - Specialized methods for common financial data requests
    """
    
    def __init__(self, 
                 base_url: str,
                 api_name: str,
                 auth_manager: Optional[AuthManager] = None,
                 rate_limiter: Optional[RateLimiter] = None,
                 timeout: int = 30,
                 max_retries: int = 3):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL for the API
            api_name: Name of the API (for logging and identification)
            auth_manager: Authentication manager for handling API keys
            rate_limiter: Rate limiter for respecting API rate limits
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_name = api_name
        self.auth_manager = auth_manager
        self.rate_limiter = rate_limiter
        
        # Initialize web client
        self.client = WebClient(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries
        )
        
        logger.info(f"APIClient initialized for {api_name}")
    
    async def _prepare_request(self, 
                              endpoint: str, 
                              method: RequestMethod,
                              auth_required: bool = True,
                              **kwargs) -> Tuple[str, Dict[str, Any]]:
        """
        Prepare request parameters with authentication and rate limiting.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            auth_required: Whether authentication is required
            **kwargs: Additional request parameters
            
        Returns:
            Tuple of (endpoint, request_kwargs)
        """
        request_kwargs = kwargs.copy()
        
        # Apply authentication if required
        if auth_required and self.auth_manager:
            auth_headers = await self.auth_manager.get_auth_headers(self.api_name)
            
            # Merge with existing headers or create new headers dict
            if 'headers' in request_kwargs:
                request_kwargs['headers'].update(auth_headers)
            else:
                request_kwargs['headers'] = auth_headers
        
        # Apply rate limiting if configured
        if self.rate_limiter:
            await self.rate_limiter.acquire(self.api_name)
        
        return endpoint, request_kwargs
    
    async def request(self, 
                     endpoint: str, 
                     method: RequestMethod = RequestMethod.GET,
                     auth_required: bool = True,
                     parse_json: bool = True,
                     **kwargs) -> Any:
        """
        Make an API request with authentication and rate limiting.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            auth_required: Whether authentication is required
            parse_json: Whether to parse the response as JSON
            **kwargs: Additional request parameters
            
        Returns:
            Parsed response data or raw response
        """
        endpoint, request_kwargs = await self._prepare_request(
            endpoint, method, auth_required, **kwargs
        )
        
        try:
            response = await self.client.async_request(method, endpoint, **request_kwargs)
            
            if parse_json:
                return await response.json()
            else:
                return await response.text()
                
        except Exception as e:
            logger.error(f"API request to {self.api_name} failed: {str(e)}")
            raise
    
    async def get_market_data(self, 
                             symbol: str, 
                             timeframe: str = "1d",
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None,
                             limit: int = 1000) -> Dict[str, Any]:
        """
        Get market data for a specific symbol.
        
        Args:
            symbol: Market symbol (e.g., "BTCUSD", "AAPL")
            timeframe: Data timeframe (e.g., "1m", "5m", "1h", "1d")
            start_time: Start time for data
            end_time: End time for data
            limit: Maximum number of data points
            
        Returns:
            Market data response
        """
        # This is a generic implementation - specific API clients should override this
        params = {
            "symbol": symbol,
            "timeframe": timeframe,
            "limit": limit
        }
        
        if start_time:
            params["start_time"] = int(start_time.timestamp() * 1000)
        
        if end_time:
            params["end_time"] = int(end_time.timestamp() * 1000)
        
        return await self.request("market_data", RequestMethod.GET, params=params)
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current ticker data for a symbol.
        
        Args:
            symbol: Market symbol
            
        Returns:
            Ticker data
        """
        return await self.request(f"ticker/{symbol}", RequestMethod.GET)
    
    async def get_order_book(self, symbol: str, depth: int = 10) -> Dict[str, Any]:
        """
        Get order book data for a symbol.
        
        Args:
            symbol: Market symbol
            depth: Order book depth
            
        Returns:
            Order book data
        """
        return await self.request(f"orderbook/{symbol}", RequestMethod.GET, params={"depth": depth})
    
    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent trades for a symbol.
        
        Args:
            symbol: Market symbol
            limit: Maximum number of trades
            
        Returns:
            List of recent trades
        """
        return await self.request(f"trades/{symbol}", RequestMethod.GET, params={"limit": limit})
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information.
        
        Returns:
            Exchange information
        """
        return await self.request("exchange_info", RequestMethod.GET)
    
    async def close(self):
        """Close the API client and its resources."""
        await self.client.async_close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class AlphaVantageClient(APIClient):
    """API client for Alpha Vantage financial data."""
    
    def __init__(self, api_key: str, **kwargs):
        """
        Initialize Alpha Vantage API client.
        
        Args:
            api_key: Alpha Vantage API key
            **kwargs: Additional client parameters
        """
        super().__init__(
            base_url="https://www.alphavantage.co/query",
            api_name="alpha_vantage",
            **kwargs
        )
        self.api_key = api_key
    
    async def _prepare_request(self, endpoint: str, method: RequestMethod, auth_required: bool = True, **kwargs):
        """Add API key to request parameters."""
        if 'params' not in kwargs:
            kwargs['params'] = {}
        
        kwargs['params']['apikey'] = self.api_key
        
        return await super()._prepare_request(endpoint, method, False, **kwargs)
    
    async def get_market_data(self, 
                             symbol: str, 
                             timeframe: str = "daily",
                             outputsize: str = "compact") -> Dict[str, Any]:
        """
        Get market data from Alpha Vantage.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            timeframe: Data timeframe ("intraday", "daily", "weekly", "monthly")
            outputsize: Output size ("compact" or "full")
            
        Returns:
            Market data
        """
        function = "TIME_SERIES_DAILY"
        if timeframe == "intraday":
            function = "TIME_SERIES_INTRADAY"
        elif timeframe == "weekly":
            function = "TIME_SERIES_WEEKLY"
        elif timeframe == "monthly":
            function = "TIME_SERIES_MONTHLY"
        
        params = {
            "function": function,
            "symbol": symbol,
            "outputsize": outputsize
        }
        
        if timeframe == "intraday":
            params["interval"] = "5min"  # Default interval
        
        return await self.request("", params=params)
    
    async def get_forex_data(self, from_currency: str, to_currency: str) -> Dict[str, Any]:
        """
        Get forex exchange rate data.
        
        Args:
            from_currency: From currency code (e.g., "USD")
            to_currency: To currency code (e.g., "EUR")
            
        Returns:
            Forex data
        """
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency
        }
        
        return await self.request("", params=params)


class YahooFinanceClient(APIClient):
    """API client for Yahoo Finance data."""
    
    def __init__(self, **kwargs):
        """
        Initialize Yahoo Finance API client.
        
        Args:
            **kwargs: Additional client parameters
        """
        super().__init__(
            base_url="https://query1.finance.yahoo.com/v8/finance",
            api_name="yahoo_finance",
            **kwargs
        )
    
    async def get_market_data(self, 
                             symbol: str, 
                             interval: str = "1d",
                             range_str: str = "1mo") -> Dict[str, Any]:
        """
        Get market data from Yahoo Finance.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            interval: Data interval ("1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo")
            range_str: Data range ("1d", "5d", "1mo", "3mo", "6mo", "1y", "5y", "max")
            
        Returns:
            Market data
        """
        params = {
            "interval": interval,
            "range": range_str
        }
        
        return await self.request(f"chart/{symbol}", params=params)
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get quote data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Quote data
        """
        params = {
            "symbols": symbol
        }
        
        return await self.request("quote", params=params)


class CryptoExchangeClient(APIClient):
    """Base API client for cryptocurrency exchanges."""
    
    async def get_market_data(self, 
                             symbol: str, 
                             timeframe: str = "1d",
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None,
                             limit: int = 1000) -> Dict[str, Any]:
        """
        Get cryptocurrency market data.
        
        Args:
            symbol: Crypto pair (e.g., "BTCUSDT")
            timeframe: Data timeframe (e.g., "1m", "5m", "1h", "1d")
            start_time: Start time for data
            end_time: End time for data
            limit: Maximum number of data points
            
        Returns:
            Market data
        """
        # Default implementation using mock data
        logger.warning(f"Using mock data for {symbol} - implement in subclass for real data")
        import numpy as np
        
        # Generate mock OHLCV data
        num_points = min(limit or 100, 1000)
        base_price = 100.0
        timestamps = [start_time + timedelta(minutes=i) for i in range(num_points)]
        
        data = []
        for ts in timestamps:
            open_price = base_price + np.random.randn() * 2
            high_price = open_price + abs(np.random.randn())
            low_price = open_price - abs(np.random.randn())
            close_price = (high_price + low_price) / 2 + np.random.randn() * 0.5
            volume = abs(np.random.randn() * 1000)
            
            data.append({
                'timestamp': ts.isoformat(),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
        
        return {'symbol': symbol, 'timeframe': timeframe, 'data': data}
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current ticker data for a symbol.
        
        Args:
            symbol: Crypto pair
            
        Returns:
            Ticker data
        """
        # Default implementation using mock data
        logger.warning(f"Using mock ticker for {symbol} - implement in subclass for real data")
        
        base_price = 100.0
        return {
            'symbol': symbol,
            'last': base_price + np.random.randn() * 2,
            'bid': base_price - 0.05,
            'ask': base_price + 0.05,
            'volume': abs(np.random.randn() * 10000),
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_order_book(self, symbol: str, depth: int = 10) -> Dict[str, Any]:
        """
        Get order book data for a symbol.
        
        Args:
            symbol: Crypto pair
            depth: Order book depth
            
        Returns:
            Order book data
        """
        # Default implementation using mock data
        logger.warning(f"Using mock order book for {symbol} - implement in subclass for real data")
        
        base_price = 100.0
        bids = [[base_price - i * 0.01, abs(np.random.randn() * 100)] for i in range(1, depth + 1)]
        asks = [[base_price + i * 0.01, abs(np.random.randn() * 100)] for i in range(1, depth + 1)]
        
        return {
            'symbol': symbol,
            'bids': bids,
            'asks': asks,
            'timestamp': datetime.now().isoformat()
        }


class BinanceClient(CryptoExchangeClient):
    """API client for Binance cryptocurrency exchange."""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = False, **kwargs):
        """
        Initialize Binance API client.
        
        Args:
            api_key: Binance API key (optional for public endpoints)
            api_secret: Binance API secret (optional for public endpoints)
            testnet: Use testnet instead of mainnet
            **kwargs: Additional client parameters
        """
        base_url = "https://testnet.binance.vision/api/v3" if testnet else "https://api.binance.com/api/v3"
        super().__init__(
            base_url=base_url,
            api_name="binance",
            **kwargs
        )
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
    
    def _get_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for authenticated requests."""
        import hmac
        import hashlib
        
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def _prepare_request(self, endpoint: str, method: RequestMethod, auth_required: bool = True, **kwargs):
        """Add authentication headers and signature if required."""
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        
        if self.api_key:
            kwargs['headers']['X-MBX-APIKEY'] = self.api_key
        
        if auth_required and self.api_secret:
            if 'params' not in kwargs:
                kwargs['params'] = {}
            kwargs['params']['timestamp'] = int(time.time() * 1000)
            kwargs['params']['signature'] = self._get_signature(kwargs['params'])
        
        return await super()._prepare_request(endpoint, method, False, **kwargs)
    
    async def get_market_data(self, 
                             symbol: str, 
                             timeframe: str = "1d",
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None,
                             limit: int = 1000) -> List[List]:
        """
        Get kline/candlestick data from Binance.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            timeframe: Kline interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            start_time: Start time
            end_time: End time
            limit: Number of klines (max 1000)
            
        Returns:
            List of klines [open_time, open, high, low, close, volume, ...]
        """
        params = {
            "symbol": symbol.upper(),
            "interval": timeframe,
            "limit": min(limit, 1000)
        }
        
        if start_time:
            params["startTime"] = int(start_time.timestamp() * 1000)
        if end_time:
            params["endTime"] = int(end_time.timestamp() * 1000)
        
        return await self.request("klines", RequestMethod.GET, auth_required=False, params=params)
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get 24hr ticker price change statistics."""
        params = {"symbol": symbol.upper()}
        return await self.request("ticker/24hr", RequestMethod.GET, auth_required=False, params=params)
    
    async def get_ticker_price(self, symbol: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get latest price for a symbol or all symbols."""
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()
        return await self.request("ticker/price", RequestMethod.GET, auth_required=False, params=params)
    
    async def get_order_book(self, symbol: str, depth: int = 100) -> Dict[str, Any]:
        """Get order book depth."""
        params = {
            "symbol": symbol.upper(),
            "limit": min(depth, 5000)
        }
        return await self.request("depth", RequestMethod.GET, auth_required=False, params=params)
    
    async def get_recent_trades(self, symbol: str, limit: int = 500) -> List[Dict[str, Any]]:
        """Get recent trades."""
        params = {
            "symbol": symbol.upper(),
            "limit": min(limit, 1000)
        }
        return await self.request("trades", RequestMethod.GET, auth_required=False, params=params)
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange trading rules and symbol information."""
        return await self.request("exchangeInfo", RequestMethod.GET, auth_required=False)
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get current account information (requires authentication)."""
        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret required for account info")
        return await self.request("account", RequestMethod.GET, auth_required=True)
    
    async def place_order(self, 
                         symbol: str, 
                         side: str, 
                         order_type: str,
                         quantity: Optional[float] = None,
                         quote_quantity: Optional[float] = None,
                         price: Optional[float] = None,
                         time_in_force: str = "GTC",
                         stop_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Place a new order.
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            order_type: LIMIT, MARKET, STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, TAKE_PROFIT_LIMIT, LIMIT_MAKER
            quantity: Order quantity
            quote_quantity: Quote order quantity (for MARKET orders)
            price: Order price (required for LIMIT orders)
            time_in_force: GTC, IOC, FOK
            stop_price: Stop price (for stop orders)
            
        Returns:
            Order response
        """
        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret required for placing orders")
        
        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": order_type.upper()
        }
        
        if quantity:
            params["quantity"] = quantity
        if quote_quantity:
            params["quoteOrderQty"] = quote_quantity
        if price:
            params["price"] = price
        if order_type.upper() in ["LIMIT", "STOP_LOSS_LIMIT", "TAKE_PROFIT_LIMIT", "LIMIT_MAKER"]:
            params["timeInForce"] = time_in_force
        if stop_price:
            params["stopPrice"] = stop_price
        
        return await self.request("order", RequestMethod.POST, auth_required=True, params=params)
    
    async def cancel_order(self, symbol: str, order_id: Optional[int] = None, client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """Cancel an active order."""
        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret required for cancelling orders")
        
        params = {"symbol": symbol.upper()}
        if order_id:
            params["orderId"] = order_id
        elif client_order_id:
            params["origClientOrderId"] = client_order_id
        else:
            raise ValueError("Either order_id or client_order_id required")
        
        return await self.request("order", RequestMethod.DELETE, auth_required=True, params=params)
    
    async def get_order_status(self, symbol: str, order_id: Optional[int] = None, client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """Get order status."""
        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret required for order status")
        
        params = {"symbol": symbol.upper()}
        if order_id:
            params["orderId"] = order_id
        elif client_order_id:
            params["origClientOrderId"] = client_order_id
        else:
            raise ValueError("Either order_id or client_order_id required")
        
        return await self.request("order", RequestMethod.GET, auth_required=True, params=params)
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all open orders."""
        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret required for open orders")
        
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()
        
        return await self.request("openOrders", RequestMethod.GET, auth_required=True, params=params)
    
    async def get_all_orders(self, symbol: str, limit: int = 500) -> List[Dict[str, Any]]:
        """Get all orders (active, canceled, filled)."""
        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret required for order history")
        
        params = {
            "symbol": symbol.upper(),
            "limit": min(limit, 1000)
        }
        
        return await self.request("allOrders", RequestMethod.GET, auth_required=True, params=params)


class CoinGeckoClient(APIClient):
    """API client for CoinGecko (free, no API key required)."""
    
    def __init__(self, **kwargs):
        """Initialize CoinGecko API client."""
        super().__init__(
            base_url="https://api.coingecko.com/api/v3",
            api_name="coingecko",
            **kwargs
        )
    
    async def get_price(self, ids: Union[str, List[str]], vs_currencies: Union[str, List[str]] = "usd") -> Dict[str, Any]:
        """
        Get current price of coins.
        
        Args:
            ids: Coin IDs (e.g., "bitcoin" or ["bitcoin", "ethereum"])
            vs_currencies: Target currencies (e.g., "usd" or ["usd", "eur"])
            
        Returns:
            Price data
        """
        if isinstance(ids, list):
            ids = ",".join(ids)
        if isinstance(vs_currencies, list):
            vs_currencies = ",".join(vs_currencies)
        
        params = {
            "ids": ids,
            "vs_currencies": vs_currencies
        }
        
        return await self.request("simple/price", RequestMethod.GET, auth_required=False, params=params)
    
    async def get_market_data(self, 
                             coin_id: str = "bitcoin",
                             vs_currency: str = "usd",
                             days: Union[int, str] = 30) -> Dict[str, Any]:
        """
        Get historical market data.
        
        Args:
            coin_id: Coin ID (e.g., "bitcoin")
            vs_currency: Target currency
            days: Number of days (1, 7, 14, 30, 90, 180, 365, max)
            
        Returns:
            Market chart data with prices, market_caps, total_volumes
        """
        params = {
            "vs_currency": vs_currency,
            "days": days
        }
        
        return await self.request(f"coins/{coin_id}/market_chart", RequestMethod.GET, auth_required=False, params=params)
    
    async def get_coin_list(self) -> List[Dict[str, Any]]:
        """Get list of all supported coins."""
        return await self.request("coins/list", RequestMethod.GET, auth_required=False)
    
    async def get_coin_markets(self, 
                              vs_currency: str = "usd",
                              order: str = "market_cap_desc",
                              per_page: int = 100,
                              page: int = 1) -> List[Dict[str, Any]]:
        """
        Get coin market data with rankings.
        
        Args:
            vs_currency: Target currency
            order: Sort order (market_cap_desc, gecko_desc, volume_desc, etc.)
            per_page: Results per page (max 250)
            page: Page number
            
        Returns:
            List of coins with market data
        """
        params = {
            "vs_currency": vs_currency,
            "order": order,
            "per_page": min(per_page, 250),
            "page": page,
            "sparkline": "false"
        }
        
        return await self.request("coins/markets", RequestMethod.GET, auth_required=False, params=params)
    
    async def get_coin_details(self, coin_id: str) -> Dict[str, Any]:
        """Get detailed coin information."""
        return await self.request(f"coins/{coin_id}", RequestMethod.GET, auth_required=False)
    
    async def get_trending(self) -> Dict[str, Any]:
        """Get trending coins."""
        return await self.request("search/trending", RequestMethod.GET, auth_required=False)
    
    async def get_global_data(self) -> Dict[str, Any]:
        """Get global cryptocurrency market data."""
        return await self.request("global", RequestMethod.GET, auth_required=False)


class FREDClient(APIClient):
    """API client for Federal Reserve Economic Data (FRED)."""
    
    def __init__(self, api_key: str, **kwargs):
        """
        Initialize FRED API client.
        
        Args:
            api_key: FRED API key (free from https://fred.stlouisfed.org/docs/api/api_key.html)
            **kwargs: Additional client parameters
        """
        super().__init__(
            base_url="https://api.stlouisfed.org/fred",
            api_name="fred",
            **kwargs
        )
        self.api_key = api_key
    
    async def _prepare_request(self, endpoint: str, method: RequestMethod, auth_required: bool = True, **kwargs):
        """Add API key to request parameters."""
        if 'params' not in kwargs:
            kwargs['params'] = {}
        
        kwargs['params']['api_key'] = self.api_key
        kwargs['params']['file_type'] = 'json'
        
        return await super()._prepare_request(endpoint, method, False, **kwargs)
    
    async def get_series(self, series_id: str) -> Dict[str, Any]:
        """
        Get economic data series information.
        
        Args:
            series_id: FRED series ID (e.g., "GDP", "UNRATE", "CPIAUCSL")
            
        Returns:
            Series information
        """
        params = {"series_id": series_id}
        return await self.request("series", RequestMethod.GET, params=params)
    
    async def get_series_observations(self, 
                                      series_id: str,
                                      start_date: Optional[str] = None,
                                      end_date: Optional[str] = None,
                                      limit: int = 100000) -> Dict[str, Any]:
        """
        Get observations for an economic data series.
        
        Args:
            series_id: FRED series ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum observations
            
        Returns:
            Series observations
        """
        params = {
            "series_id": series_id,
            "limit": limit
        }
        
        if start_date:
            params["observation_start"] = start_date
        if end_date:
            params["observation_end"] = end_date
        
        return await self.request("series/observations", RequestMethod.GET, params=params)
    
    async def search_series(self, search_text: str, limit: int = 100) -> Dict[str, Any]:
        """
        Search for economic data series.
        
        Args:
            search_text: Search query
            limit: Maximum results
            
        Returns:
            Search results
        """
        params = {
            "search_text": search_text,
            "limit": limit
        }
        
        return await self.request("series/search", RequestMethod.GET, params=params)
    
    async def get_releases(self) -> Dict[str, Any]:
        """Get all economic data releases."""
        return await self.request("releases", RequestMethod.GET)
    
    async def get_category(self, category_id: int = 0) -> Dict[str, Any]:
        """
        Get category information.
        
        Args:
            category_id: Category ID (0 for root)
            
        Returns:
            Category information
        """
        params = {"category_id": category_id}
        return await self.request("category", RequestMethod.GET, params=params)
