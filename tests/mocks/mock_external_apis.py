"""
Mock external API implementations for testing.
Simulates NewsAPI, CoinGecko, Yahoo Finance, and other external services.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json


class MockNewsAPI:
    """
    Mock NewsAPI for testing news-related functionality.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or 'mock_api_key'
        self.connected = False
        
        # Sample news data
        self.sample_headlines = [
            "Fed signals potential rate cut in upcoming meeting",
            "EUR/USD reaches monthly high amid dollar weakness",
            "Oil prices surge on OPEC+ production cut announcement",
            "Tech stocks rally as inflation fears ease",
            "Bank of England holds rates steady",
            "China GDP growth exceeds expectations",
            "US jobless claims fall to historic low",
            "Gold prices hit record high on geopolitical tensions",
            "European markets close higher on positive earnings",
            "Cryptocurrency market sees increased institutional interest",
        ]
        
        self.sample_sources = [
            {'id': 'reuters', 'name': 'Reuters'},
            {'id': 'bloomberg', 'name': 'Bloomberg'},
            {'id': 'cnbc', 'name': 'CNBC'},
            {'id': 'financial-times', 'name': 'Financial Times'},
            {'id': 'wall-street-journal', 'name': 'Wall Street Journal'},
        ]
    
    def connect(self) -> bool:
        self.connected = True
        return True
    
    def get_top_headlines(
        self,
        category: str = 'business',
        country: str = 'us',
        page_size: int = 10
    ) -> Dict:
        """Get top headlines."""
        articles = []
        for i in range(min(page_size, len(self.sample_headlines))):
            articles.append({
                'source': random.choice(self.sample_sources),
                'author': f'Author {i}',
                'title': self.sample_headlines[i],
                'description': f'Description for {self.sample_headlines[i]}',
                'url': f'https://example.com/article/{i}',
                'publishedAt': (datetime.now() - timedelta(hours=i)).isoformat(),
                'content': f'Full content for article {i}...',
            })
        
        return {
            'status': 'ok',
            'totalResults': len(articles),
            'articles': articles,
        }
    
    def get_everything(
        self,
        q: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        language: str = 'en',
        sort_by: str = 'publishedAt',
        page_size: int = 10
    ) -> Dict:
        """Search for articles."""
        # Filter headlines containing query
        matching = [h for h in self.sample_headlines if q.lower() in h.lower()]
        if not matching:
            matching = self.sample_headlines[:page_size]
        
        articles = []
        for i, headline in enumerate(matching[:page_size]):
            articles.append({
                'source': random.choice(self.sample_sources),
                'author': f'Author {i}',
                'title': headline,
                'description': f'Description for {headline}',
                'url': f'https://example.com/article/{i}',
                'publishedAt': (datetime.now() - timedelta(hours=i)).isoformat(),
                'content': f'Full content for article {i}...',
            })
        
        return {
            'status': 'ok',
            'totalResults': len(articles),
            'articles': articles,
        }
    
    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of text (mock implementation)."""
        # Simple keyword-based sentiment
        positive_words = ['surge', 'rally', 'high', 'growth', 'positive', 'exceeds', 'record']
        negative_words = ['fall', 'drop', 'low', 'fears', 'tensions', 'decline', 'crash']
        
        text_lower = text.lower()
        positive_count = sum(1 for w in positive_words if w in text_lower)
        negative_count = sum(1 for w in negative_words if w in text_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
            score = 0.5 + 0.1 * positive_count
        elif negative_count > positive_count:
            sentiment = 'negative'
            score = -0.5 - 0.1 * negative_count
        else:
            sentiment = 'neutral'
            score = 0.0
        
        return {
            'sentiment': sentiment,
            'score': min(max(score, -1.0), 1.0),
            'confidence': random.uniform(0.7, 0.95),
        }


class MockCoinGeckoAPI:
    """
    Mock CoinGecko API for cryptocurrency data.
    """
    
    def __init__(self):
        self.connected = False
        
        # Sample crypto data
        self.crypto_prices = {
            'bitcoin': {'usd': 43500, 'eur': 40000, 'gbp': 34500},
            'ethereum': {'usd': 2250, 'eur': 2070, 'gbp': 1780},
            'ripple': {'usd': 0.62, 'eur': 0.57, 'gbp': 0.49},
            'cardano': {'usd': 0.58, 'eur': 0.53, 'gbp': 0.46},
            'solana': {'usd': 98, 'eur': 90, 'gbp': 78},
        }
    
    def connect(self) -> bool:
        self.connected = True
        return True
    
    def get_price(
        self,
        ids: List[str],
        vs_currencies: List[str] = ['usd']
    ) -> Dict:
        """Get current prices."""
        result = {}
        for coin_id in ids:
            if coin_id in self.crypto_prices:
                result[coin_id] = {}
                for currency in vs_currencies:
                    if currency in self.crypto_prices[coin_id]:
                        # Add small random variation
                        base_price = self.crypto_prices[coin_id][currency]
                        variation = base_price * random.uniform(-0.01, 0.01)
                        result[coin_id][currency] = base_price + variation
        return result
    
    def get_coin_market_chart(
        self,
        coin_id: str,
        vs_currency: str = 'usd',
        days: int = 30
    ) -> Dict:
        """Get historical market data."""
        if coin_id not in self.crypto_prices:
            return {'prices': [], 'market_caps': [], 'total_volumes': []}
        
        base_price = self.crypto_prices[coin_id].get(vs_currency, 1000)
        
        prices = []
        market_caps = []
        volumes = []
        
        now = datetime.now()
        for i in range(days * 24):  # Hourly data
            timestamp = int((now - timedelta(hours=days*24-i)).timestamp() * 1000)
            
            # Random walk
            variation = base_price * random.uniform(-0.02, 0.02)
            price = base_price + variation * (i / (days * 24))
            
            prices.append([timestamp, price])
            market_caps.append([timestamp, price * 1e9])
            volumes.append([timestamp, random.uniform(1e8, 1e10)])
        
        return {
            'prices': prices,
            'market_caps': market_caps,
            'total_volumes': volumes,
        }
    
    def get_coins_list(self) -> List[Dict]:
        """Get list of all coins."""
        return [
            {'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin'},
            {'id': 'ethereum', 'symbol': 'eth', 'name': 'Ethereum'},
            {'id': 'ripple', 'symbol': 'xrp', 'name': 'XRP'},
            {'id': 'cardano', 'symbol': 'ada', 'name': 'Cardano'},
            {'id': 'solana', 'symbol': 'sol', 'name': 'Solana'},
        ]


class MockYahooFinanceAPI:
    """
    Mock Yahoo Finance API for stock and forex data.
    """
    
    def __init__(self):
        self.connected = False
        
        # Sample stock data
        self.stock_prices = {
            'AAPL': 185.50,
            'GOOGL': 141.20,
            'MSFT': 378.90,
            'AMZN': 153.40,
            'TSLA': 248.70,
            'META': 354.80,
            'NVDA': 495.20,
        }
        
        # Sample forex data
        self.forex_prices = {
            'EURUSD=X': 1.0850,
            'GBPUSD=X': 1.2650,
            'USDJPY=X': 149.50,
            'AUDUSD=X': 0.6550,
        }
    
    def connect(self) -> bool:
        self.connected = True
        return True
    
    def get_quote(self, symbol: str) -> Dict:
        """Get current quote for symbol."""
        if symbol in self.stock_prices:
            price = self.stock_prices[symbol]
            variation = price * random.uniform(-0.005, 0.005)
            current = price + variation
            
            return {
                'symbol': symbol,
                'regularMarketPrice': current,
                'regularMarketOpen': price * 0.998,
                'regularMarketDayHigh': current * 1.01,
                'regularMarketDayLow': current * 0.99,
                'regularMarketVolume': random.randint(10000000, 50000000),
                'regularMarketPreviousClose': price,
                'regularMarketChange': variation,
                'regularMarketChangePercent': (variation / price) * 100,
            }
        elif symbol in self.forex_prices:
            price = self.forex_prices[symbol]
            variation = price * random.uniform(-0.001, 0.001)
            current = price + variation
            
            return {
                'symbol': symbol,
                'regularMarketPrice': current,
                'bid': current - 0.0001,
                'ask': current + 0.0001,
            }
        
        return {}
    
    def get_historical_data(
        self,
        symbol: str,
        period: str = '1mo',
        interval: str = '1d'
    ) -> List[Dict]:
        """Get historical data."""
        # Determine number of data points
        period_map = {'1d': 1, '5d': 5, '1mo': 30, '3mo': 90, '1y': 365}
        days = period_map.get(period, 30)
        
        base_price = self.stock_prices.get(symbol, self.forex_prices.get(symbol, 100))
        
        data = []
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i)
            variation = base_price * random.uniform(-0.02, 0.02)
            close = base_price + variation * (i / days)
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': close * random.uniform(0.99, 1.01),
                'high': close * random.uniform(1.0, 1.02),
                'low': close * random.uniform(0.98, 1.0),
                'close': close,
                'volume': random.randint(1000000, 10000000),
            })
        
        return data
    
    def get_options_chain(self, symbol: str) -> Dict:
        """Get options chain for symbol."""
        base_price = self.stock_prices.get(symbol, 100)
        
        calls = []
        puts = []
        
        for strike_offset in range(-5, 6):
            strike = base_price + strike_offset * 5
            
            calls.append({
                'strike': strike,
                'lastPrice': max(0, base_price - strike) + random.uniform(1, 5),
                'bid': max(0, base_price - strike) + random.uniform(0.5, 4),
                'ask': max(0, base_price - strike) + random.uniform(1.5, 6),
                'volume': random.randint(100, 10000),
                'openInterest': random.randint(1000, 50000),
                'impliedVolatility': random.uniform(0.2, 0.5),
            })
            
            puts.append({
                'strike': strike,
                'lastPrice': max(0, strike - base_price) + random.uniform(1, 5),
                'bid': max(0, strike - base_price) + random.uniform(0.5, 4),
                'ask': max(0, strike - base_price) + random.uniform(1.5, 6),
                'volume': random.randint(100, 10000),
                'openInterest': random.randint(1000, 50000),
                'impliedVolatility': random.uniform(0.2, 0.5),
            })
        
        return {
            'calls': calls,
            'puts': puts,
            'expirationDate': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
        }


class MockFREDAPI:
    """
    Mock FRED (Federal Reserve Economic Data) API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or 'mock_api_key'
        self.connected = False
        
        # Sample economic indicators
        self.indicators = {
            'GDP': {'value': 27.36, 'unit': 'Trillions of Dollars'},
            'UNRATE': {'value': 3.7, 'unit': 'Percent'},
            'CPIAUCSL': {'value': 308.42, 'unit': 'Index 1982-1984=100'},
            'FEDFUNDS': {'value': 5.33, 'unit': 'Percent'},
            'DGS10': {'value': 4.25, 'unit': 'Percent'},
            'M2SL': {'value': 20.87, 'unit': 'Trillions of Dollars'},
        }
    
    def connect(self) -> bool:
        self.connected = True
        return True
    
    def get_series(self, series_id: str, limit: int = 100) -> List[Dict]:
        """Get time series data."""
        if series_id not in self.indicators:
            return []
        
        base_value = self.indicators[series_id]['value']
        
        data = []
        for i in range(limit):
            date = datetime.now() - timedelta(days=limit-i)
            variation = base_value * random.uniform(-0.01, 0.01)
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': base_value + variation * (i / limit),
            })
        
        return data
    
    def get_series_info(self, series_id: str) -> Dict:
        """Get series metadata."""
        if series_id not in self.indicators:
            return {}
        
        return {
            'id': series_id,
            'title': f'{series_id} Economic Indicator',
            'units': self.indicators[series_id]['unit'],
            'frequency': 'Monthly',
            'seasonal_adjustment': 'Seasonally Adjusted',
        }


class MockAlpacaAPI:
    """
    Mock Alpaca Trading API for paper trading.
    """
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        self.api_key = api_key or 'mock_api_key'
        self.secret_key = secret_key or 'mock_secret_key'
        self.connected = False
        
        self.account = {
            'id': 'mock_account_id',
            'status': 'ACTIVE',
            'currency': 'USD',
            'cash': 100000.0,
            'portfolio_value': 100000.0,
            'buying_power': 400000.0,
            'equity': 100000.0,
        }
        
        self.positions = []
        self.orders = []
    
    def connect(self) -> bool:
        self.connected = True
        return True
    
    def get_account(self) -> Dict:
        """Get account information."""
        return self.account.copy()
    
    def get_positions(self) -> List[Dict]:
        """Get all positions."""
        return self.positions.copy()
    
    def submit_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        type: str = 'market',
        time_in_force: str = 'day'
    ) -> Dict:
        """Submit an order."""
        order = {
            'id': f'order_{len(self.orders)}',
            'symbol': symbol,
            'qty': qty,
            'side': side,
            'type': type,
            'time_in_force': time_in_force,
            'status': 'filled',
            'filled_at': datetime.now().isoformat(),
        }
        self.orders.append(order)
        return order
    
    def get_orders(self, status: str = 'all') -> List[Dict]:
        """Get orders."""
        if status == 'all':
            return self.orders.copy()
        return [o for o in self.orders if o['status'] == status]
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        for order in self.orders:
            if order['id'] == order_id and order['status'] == 'pending':
                order['status'] = 'cancelled'
                return True
        return False
