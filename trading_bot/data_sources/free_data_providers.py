"""
Free Data Providers ($0 Budget)
All data sources are 100% FREE with no API keys required
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
try:
    import yfinance as yf
except ImportError:
    yf = None


class CoinGeckoProvider:
    """Free cryptocurrency data from CoinGecko (NO API KEY NEEDED)"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.cost = 0  # FREE
        
    def get_crypto_price(self, symbol: str) -> Dict:
        """Get current crypto price"""
        try:
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': symbol.lower(),
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true'
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if symbol.lower() in data:
                return {
                    'symbol': symbol,
                    'price': data[symbol.lower()]['usd'],
                    'market_cap': data[symbol.lower()].get('usd_market_cap'),
                    'volume_24h': data[symbol.lower()].get('usd_24h_vol'),
                    'change_24h': data[symbol.lower()].get('usd_24h_change'),
                    'timestamp': datetime.now(),
                    'cost': 0
                }
        except Exception as e:
            print(f"Error fetching CoinGecko data: {e}")
        
        return None
    
    def get_historical_data(self, symbol: str, days: int = 30) -> List[Dict]:
        """Get historical crypto data"""
        try:
            url = f"{self.base_url}/coins/{symbol.lower()}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily'
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            prices = data.get('prices', [])
            
            return [
                {
                    'timestamp': datetime.fromtimestamp(p[0]/1000),
                    'price': p[1],
                    'cost': 0
                }
                for p in prices
            ]
        except Exception as e:
            print(f"Error fetching historical data: {e}")
        
        return []


class YahooFinanceProvider:
    """Free stock data from Yahoo Finance (NO API KEY NEEDED)"""
    
    def __init__(self):
        self.cost = 0  # FREE
        
    def get_stock_price(self, symbol: str) -> Dict:
        """Get current stock price"""
        try:
            # Using yfinance library (free)
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d')
            
            if not data.empty:
                latest = data.iloc[-1]
                return {
                    'symbol': symbol,
                    'price': latest['Close'],
                    'high': latest['High'],
                    'low': latest['Low'],
                    'volume': latest['Volume'],
                    'timestamp': datetime.now(),
                    'cost': 0
                }
        except Exception as e:
            print(f"Error fetching Yahoo Finance data: {e}")
        
        return None
    
    def get_historical_data(self, symbol: str, period: str = '1mo') -> List[Dict]:
        """Get historical stock data"""
            
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            return [
                {
                    'timestamp': idx,
                    'open': row['Open'],
                    'high': row['High'],
                    'low': row['Low'],
                    'close': row['Close'],
                    'volume': row['Volume'],
                    'cost': 0
                }
                for idx, row in data.iterrows()
            ]
        except Exception as e:
            print(f"Error fetching historical data: {e}")
        
        return []


class ForexDataProvider:
    """Free forex data from exchangerate-api.com"""
    
    def __init__(self):
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
        self.cost = 0  # FREE (1,500 requests/month)
        
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Dict:
        """Get exchange rate"""
        try:
            url = f"{self.base_url}/{from_currency}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            rate = data['rates'].get(to_currency)
            
            if rate:
                return {
                    'from': from_currency,
                    'to': to_currency,
                    'rate': rate,
                    'timestamp': datetime.now(),
                    'cost': 0
                }
        except Exception as e:
            print(f"Error fetching forex data: {e}")
        
        return None
    
    def get_all_rates(self, base_currency: str) -> Dict:
        """Get all exchange rates for a currency"""
        try:
            url = f"{self.base_url}/{base_currency}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                'base': base_currency,
                'rates': data['rates'],
                'timestamp': datetime.now(),
                'cost': 0
            }
        except Exception as e:
            print(f"Error fetching rates: {e}")
        
        return None


class FREDProvider:
    """Free economic data from Federal Reserve (FRED)"""
    
    def __init__(self, api_key: str = "free"):
        # FRED API is free, but you can get a free key from fred.stlouisfed.org
        self.base_url = "https://api.stlouisfed.org/fred"
        self.api_key = api_key
        self.cost = 0  # FREE
        
    def get_economic_data(self, series_id: str, limit: int = 100) -> List[Dict]:
        """Get economic data series"""
        try:
            url = f"{self.base_url}/series/observations"
            params = {
                'series_id': series_id,
                'limit': limit,
                'api_key': self.api_key,
                'file_type': 'json'
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            observations = data.get('observations', [])
            
            return [
                {
                    'date': obs['date'],
                    'value': float(obs['value']) if obs['value'] != '.' else None,
                    'cost': 0
                }
                for obs in observations
            ]
        except Exception as e:
            print(f"Error fetching FRED data: {e}")
        
        return []


class NewsAPIProvider:
    """Free news data from NewsAPI (100 requests/day)"""
    
    def __init__(self):
        self.base_url = "https://newsapi.org/v2"
        self.cost = 0  # FREE (100 requests/day)
        
    def search_news(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for news articles"""
        try:
            url = f"{self.base_url}/everything"
            params = {
                'q': query,
                'sortBy': 'publishedAt',
                'pageSize': limit,
                'language': 'en'
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            return [
                {
                    'title': article['title'],
                    'description': article['description'],
                    'source': article['source']['name'],
                    'url': article['url'],
                    'published_at': article['publishedAt'],
                    'cost': 0
                }
                for article in articles
            ]
        except Exception as e:
            print(f"Error fetching news: {e}")
        
        return []


class RedditSentimentProvider:
    """Free sentiment data from Reddit (NO API KEY NEEDED for basic)"""
    
    def __init__(self):
        self.cost = 0  # FREE
        
    def get_subreddit_sentiment(self, subreddit: str, limit: int = 25) -> Dict:
        """Get sentiment from subreddit"""
        try:
            url = f"https://www.reddit.com/r/{subreddit}.json"
            headers = {'User-Agent': 'TradingBot/1.0'}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            posts = data['data']['children']
            
            # Simple sentiment analysis
            positive_keywords = ['bullish', 'moon', 'pump', 'gain', 'profit', 'buy']
            negative_keywords = ['bearish', 'crash', 'dump', 'loss', 'sell', 'short']
            
            positive_count = 0
            negative_count = 0
            
            for post in posts[:limit]:
                title = post['data']['title'].lower()
                
                for keyword in positive_keywords:
                    if keyword in title:
                        positive_count += 1
                
                for keyword in negative_keywords:
                    if keyword in title:
                        negative_count += 1
            
            total = positive_count + negative_count
            sentiment = (positive_count - negative_count) / total if total > 0 else 0
            
            return {
                'subreddit': subreddit,
                'sentiment': sentiment,  # -1 to 1
                'positive': positive_count,
                'negative': negative_count,
                'total_posts': len(posts),
                'timestamp': datetime.now(),
                'cost': 0
            }
        except Exception as e:
            print(f"Error fetching Reddit sentiment: {e}")
        
        return None


class FreeDataAggregator:
    """Aggregates all free data providers"""
    
    def __init__(self):
        self.coingecko = CoinGeckoProvider()
        self.yahoo = YahooFinanceProvider()
        self.forex = ForexDataProvider()
        self.fred = FREDProvider()
        self.news = NewsAPIProvider()
        self.reddit = RedditSentimentProvider()
        
    def get_market_data(self, symbol: str, asset_type: str = 'crypto') -> Dict:
        """Get market data for any symbol"""
        
        if asset_type == 'crypto':
            return self.coingecko.get_crypto_price(symbol)
        elif asset_type == 'stock':
            return self.yahoo.get_stock_price(symbol)
        
        return None
    
    def get_total_cost(self) -> Dict:
        """Get total cost of all data"""
        return {
            'coingecko': self.coingecko.cost,
            'yahoo': self.yahoo.cost,
            'forex': self.forex.cost,
            'fred': self.fred.cost,
            'news': self.news.cost,
            'reddit': self.reddit.cost,
            'total': 0
        }


# Example usage
if __name__ == '__main__':
    aggregator = FreeDataAggregator()
    
    print("="*60)
    print("FREE DATA PROVIDERS DEMO")
    print("="*60)
    
    # Get crypto price
    print("\n1. Crypto Data (CoinGecko):")
    btc = aggregator.coingecko.get_crypto_price('bitcoin')
    if btc:
        print(f"   Bitcoin: ${btc['price']:,.2f}")
        print(f"   24h Change: {btc['change_24h']:.2f}%")
    
    # Get stock price
    print("\n2. Stock Data (Yahoo Finance):")
    aapl = aggregator.yahoo.get_stock_price('AAPL')
    if aapl:
        print(f"   Apple: ${aapl['price']:.2f}")
        print(f"   Volume: {aapl['volume']:,.0f}")
    
    # Get forex rate
    print("\n3. Forex Data (exchangerate-api):")
    eurusd = aggregator.forex.get_exchange_rate('EUR', 'USD')
    if eurusd:
        print(f"   EUR/USD: {eurusd['rate']:.4f}")
    
    # Get news
    print("\n4. News Data (NewsAPI):")
    news = aggregator.news.search_news('bitcoin', limit=3)
    for article in news:
        print(f"   - {article['title'][:60]}...")
    
    # Get Reddit sentiment
    print("\n5. Sentiment Data (Reddit):")
    sentiment = aggregator.reddit.get_subreddit_sentiment('cryptocurrency')
    if sentiment:
        print(f"   r/cryptocurrency sentiment: {sentiment['sentiment']:.2f}")
        print(f"   Positive: {sentiment['positive']}, Negative: {sentiment['negative']}")
    
    # Cost summary
    print("\n" + "="*60)
    print("COST SUMMARY")
    print("="*60)
    costs = aggregator.get_total_cost()
    print(f"Total Cost: ${costs['total']}/month")
    print("Status: 100% FREE ✅")
