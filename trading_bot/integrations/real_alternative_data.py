"""
Real Alternative Data Integration
Replaces mock satellite/alternative data with actual free data sources
"""

import asyncio
import re
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import os

try:
    import aiohttp
except ImportError:
    aiohttp = None

logger = logging.getLogger(__name__)


@dataclass
class SentimentData:
    """Sentiment analysis result"""
    source: str
    symbol: str
    sentiment_score: float  # -1 to 1
    volume: int  # Number of mentions
    change_24h: float
    timestamp: datetime


@dataclass
class EconomicIndicator:
    """Economic indicator data"""
    indicator: str
    value: float
    previous: float
    change: float
    date: datetime
    source: str


@dataclass
class NewsItem:
    """News article data"""
    title: str
    source: str
    url: str
    published: datetime
    sentiment: float
    relevance: float
    symbols: List[str]


class RealAlternativeDataProvider:
    """
    Real alternative data integration using FREE APIs
    
    Data Sources:
    - Reddit API (sentiment from r/wallstreetbets, r/stocks, r/cryptocurrency)
    - NewsAPI (news sentiment)
    - FRED (economic indicators)
    - Fear & Greed Index
    - Google Trends (via pytrends)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # API Keys from environment
        self.newsapi_key = os.getenv('NEWSAPI_KEY', '')
        self.fred_key = os.getenv('FRED_API_KEY', '')
        self.reddit_client_id = os.getenv('REDDIT_CLIENT_ID', '')
        self.reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET', '')
        
        # HTTP session
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Cache
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self.cache_ttl = 300  # 5 minutes
        
        logger.info("Real alternative data provider initialized")
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
        
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self._cache:
            timestamp = self._cache_timestamps.get(key)
            if timestamp and (datetime.now() - timestamp).seconds < self.cache_ttl:
                return self._cache[key]
        return None
        
    def _set_cached(self, key: str, value: Any):
        """Set cached value"""
        self._cache[key] = value
        self._cache_timestamps[key] = datetime.now()
        
    # ==================== FEAR & GREED INDEX (FREE) ====================
    
    async def get_fear_greed_index(self) -> Dict[str, Any]:
        """
        Get Crypto Fear & Greed Index
        FREE - No API key required
        """
        cache_key = "fear_greed_index"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        try:
            
            session = await self._get_session()
            
            url = "https://api.alternative.me/fng/?limit=30"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    current = data.get('data', [{}])[0]
                    historical = data.get('data', [])
                    
                    result = {
                        'value': int(current.get('value', 50)),
                        'classification': current.get('value_classification', 'Neutral'),
                        'timestamp': datetime.fromtimestamp(int(current.get('timestamp', 0))).isoformat(),
                        'historical': [
                            {
                                'value': int(h.get('value', 50)),
                                'classification': h.get('value_classification', ''),
                                'date': datetime.fromtimestamp(int(h.get('timestamp', 0))).strftime('%Y-%m-%d')
                            }
                            for h in historical[:7]
                        ],
                        'source': 'alternative.me'
                    }
                    
                    # Calculate trend
                    if len(historical) >= 7:
                        week_ago = int(historical[6].get('value', 50))
                        current_val = int(current.get('value', 50))
                        result['trend'] = 'increasing' if current_val > week_ago else 'decreasing' if current_val < week_ago else 'stable'
                        result['change_7d'] = current_val - week_ago
                        
                    self._set_cached(cache_key, result)
                    logger.info(f"Fear & Greed Index: {result['value']} ({result['classification']})")
                    return result
                    
        except Exception as err:
            logger.error(f"Fear & Greed Index request failed: {err}")
            return {'value': 50, 'classification': 'Neutral', 'error': str(err)}
        
    # ==================== REDDIT SENTIMENT (FREE) ====================
    
    async def get_reddit_sentiment(self, subreddit: str = 'wallstreetbets', 
                                   limit: int = 100) -> Dict[str, Any]:
        """
        Get sentiment from Reddit using public JSON API
        FREE - No API key required (rate limited)
        """
        cache_key = f"reddit_sentiment_{subreddit}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        try:
            
            session = await self._get_session()
            
            # Use Reddit's public JSON API
            url = f"https://www.reddit.com/r/{subreddit}/hot.json"
            headers = {'User-Agent': 'TradingBot/1.0'}
            params = {'limit': limit}
            
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    posts = data.get('data', {}).get('children', [])
                    
                    # Analyze posts
                    total_score = 0
                    total_comments = 0
                    ticker_mentions: Dict[str, int] = {}
                    sentiment_words = {
                        'bullish': ['moon', 'rocket', 'buy', 'calls', 'long', 'bull', 'pump', 'green', 'gain'],
                        'bearish': ['crash', 'puts', 'short', 'bear', 'dump', 'red', 'loss', 'sell', 'tank']
                    }
                    
                    bullish_count = 0
                    bearish_count = 0
                    
                    for post in posts:
                        post_data = post.get('data', {})
                        title = post_data.get('title', '').lower()
                        score = post_data.get('score', 0)
                        comments = post_data.get('num_comments', 0)
                        
                        total_score += score
                        total_comments += comments
                        
                        # Count sentiment words
                        for word in sentiment_words['bullish']:
                            if word in title:
                                bullish_count += 1
                        for word in sentiment_words['bearish']:
                            if word in title:
                                bearish_count += 1
                                
                        # Extract ticker mentions ($XXX or just XXX for known tickers)
                        tickers = re.findall(r'\$([A-Z]{2,5})', post_data.get('title', ''))
                        for ticker in tickers:
                            ticker_mentions[ticker] = ticker_mentions.get(ticker, 0) + 1
                            
                    # Calculate sentiment score
                    total_sentiment_words = bullish_count + bearish_count
                    if total_sentiment_words > 0:
                        sentiment_score = (bullish_count - bearish_count) / total_sentiment_words
                    else:
                        sentiment_score = 0
                        
                    result = {
                        'subreddit': subreddit,
                        'posts_analyzed': len(posts),
                        'total_score': total_score,
                        'total_comments': total_comments,
                        'sentiment_score': sentiment_score,  # -1 to 1
                        'bullish_signals': bullish_count,
                        'bearish_signals': bearish_count,
                        'top_tickers': dict(sorted(ticker_mentions.items(), key=lambda x: x[1], reverse=True)[:10]),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'reddit'
                    }
                    
                    self._set_cached(cache_key, result)
                    logger.info(f"Reddit r/{subreddit}: sentiment={sentiment_score:.2f}, posts={len(posts)}")
                    return result
                    
        except Exception as err:
            logger.error(f"Reddit sentiment request failed: {err}")
            return {'error': str(err)}
        
    async def get_wsb_sentiment(self) -> Dict[str, Any]:
        """Get WallStreetBets sentiment"""
        return await self.get_reddit_sentiment('wallstreetbets')
        
    async def get_crypto_reddit_sentiment(self) -> Dict[str, Any]:
        """Get cryptocurrency subreddit sentiment"""
        return await self.get_reddit_sentiment('cryptocurrency')
        
    # ==================== NEWS SENTIMENT (FREE WITH API KEY) ====================
    
    async def get_news_sentiment(self, query: str, days: int = 7) -> Dict[str, Any]:
        """
        Get news sentiment using NewsAPI
        FREE tier: 100 requests/day
        """
        if not self.newsapi_key:
            logger.warning("NewsAPI key not configured")
            return await self._get_news_fallback(query)
            
        cache_key = f"news_sentiment_{query}_{days}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        try:
            
            session = await self._get_session()
            
            from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'from': from_date,
                'sortBy': 'relevancy',
                'language': 'en',
                'apiKey': self.newsapi_key
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    articles = data.get('articles', [])
                    
                    # Simple sentiment analysis
                    positive_words = ['surge', 'gain', 'rise', 'bull', 'growth', 'profit', 'success', 'up', 'high', 'record']
                    negative_words = ['crash', 'fall', 'drop', 'bear', 'loss', 'fail', 'down', 'low', 'crisis', 'fear']
                    
                    positive_count = 0
                    negative_count = 0
                    
                    news_items = []
                    for article in articles[:50]:
                        title = article.get('title', '').lower()
                        description = article.get('description', '').lower() or ''
                        text = title + ' ' + description
                        
                        article_positive = sum(1 for w in positive_words if w in text)
                        article_negative = sum(1 for w in negative_words if w in text)
                        
                        positive_count += article_positive
                        negative_count += article_negative
                        
                        # Calculate article sentiment
                        total = article_positive + article_negative
                        article_sentiment = (article_positive - article_negative) / total if total > 0 else 0
                        
                        news_items.append({
                            'title': article.get('title', ''),
                            'source': article.get('source', {}).get('name', ''),
                            'url': article.get('url', ''),
                            'published': article.get('publishedAt', ''),
                            'sentiment': article_sentiment
                        })
                        
                    # Overall sentiment
                    total_words = positive_count + negative_count
                    overall_sentiment = (positive_count - negative_count) / total_words if total_words > 0 else 0
                    
                    result = {
                        'query': query,
                        'articles_analyzed': len(articles),
                        'sentiment_score': overall_sentiment,
                        'positive_signals': positive_count,
                        'negative_signals': negative_count,
                        'top_articles': news_items[:10],
                        'timestamp': datetime.now().isoformat(),
                        'source': 'newsapi'
                    }
                    
                    self._set_cached(cache_key, result)
                    logger.info(f"NewsAPI {query}: sentiment={overall_sentiment:.2f}, articles={len(articles)}")
                    return result
                    
        except Exception as e:
            logger.error(f"NewsAPI request failed: {e}")
            
        return await self._get_news_fallback(query)
        
    async def _get_news_fallback(self, query: str) -> Dict[str, Any]:
        """Fallback news source using free RSS feeds"""
        try:
            session = await self._get_session()
            
            # Use Google News RSS
            url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            
            async with session.get(url) as response:
                if response.status == 200:
                    # Parse RSS (simplified)
                    text = await response.text()
                    
                    # Count items (very basic)
                    items = re.findall(r'<item>(.*?)</item>', text, re.DOTALL)
                    
                    return {
                        'query': query,
                        'articles_found': len(items),
                        'sentiment_score': 0,  # Cannot analyze without full text
                        'source': 'google_news_rss',
                        'timestamp': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"News fallback failed: {e}")
            
        return {'error': 'No news data available'}
        
    # ==================== ECONOMIC DATA (FRED - FREE) ====================
    
    async def get_economic_indicator(self, series_id: str) -> Dict[str, Any]:
        """
        Get economic indicator from FRED
        FREE - Requires API key
        
        Popular series:
        - GDP: Gross Domestic Product
        - UNRATE: Unemployment Rate
        - CPIAUCSL: Consumer Price Index
        - FEDFUNDS: Federal Funds Rate
        - T10Y2Y: 10Y-2Y Treasury Spread (recession indicator)
        - VIXCLS: VIX Index
        - DGS10: 10-Year Treasury Rate
        - MORTGAGE30US: 30-Year Mortgage Rate
        """
        if not self.fred_key:
            logger.warning("FRED API key not configured")
            return {'error': 'FRED API key not configured'}
            
        cache_key = f"fred_{series_id}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        try:
            
            session = await self._get_session()
            
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.fred_key,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': 30
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    observations = data.get('observations', [])
                    
                    if observations:
                        current = observations[0]
                        previous = observations[1] if len(observations) > 1 else current
                        
                        current_value = float(current.get('value', 0)) if current.get('value') != '.' else None
                        previous_value = float(previous.get('value', 0)) if previous.get('value') != '.' else None
                        
                        result = {
                            'series_id': series_id,
                            'current_value': current_value,
                            'previous_value': previous_value,
                            'change': (current_value - previous_value) if current_value and previous_value else None,
                            'change_pct': ((current_value - previous_value) / previous_value * 100) if current_value and previous_value else None,
                            'date': current.get('date', ''),
                            'historical': [
                                {
                                    'date': obs.get('date', ''),
                                    'value': float(obs.get('value', 0)) if obs.get('value') != '.' else None
                                }
                                for obs in observations[:10]
                            ],
                            'source': 'fred',
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        self._set_cached(cache_key, result)
                        logger.info(f"FRED {series_id}: {current_value}")
                        return result
                        
        except Exception as err:
            logger.error(f"FRED request failed: {err}")
            return {'error': str(err)}
        
    async def get_recession_indicators(self) -> Dict[str, Any]:
        """Get key recession indicators"""
        indicators = {}
        
        # 10Y-2Y Spread (inverted = recession signal)
        spread = await self.get_economic_indicator('T10Y2Y')
        if 'current_value' in spread:
            indicators['yield_curve'] = {
                'value': spread['current_value'],
                'signal': 'recession_warning' if spread['current_value'] < 0 else 'normal',
                'date': spread['date']
            }
            
        # Unemployment Rate
        unemployment = await self.get_economic_indicator('UNRATE')
        if 'current_value' in unemployment:
            indicators['unemployment'] = {
                'value': unemployment['current_value'],
                'change': unemployment.get('change', 0),
                'date': unemployment['date']
            }
            
        # VIX
        vix = await self.get_economic_indicator('VIXCLS')
        if 'current_value' in vix:
            indicators['vix'] = {
                'value': vix['current_value'],
                'signal': 'high_fear' if vix['current_value'] > 30 else 'elevated' if vix['current_value'] > 20 else 'normal',
                'date': vix['date']
            }
            
        return {
            'indicators': indicators,
            'timestamp': datetime.now().isoformat()
        }
        
    # ==================== SOCIAL SENTIMENT AGGREGATOR ====================
    
    async def get_aggregated_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Get aggregated sentiment from multiple sources
        """
        results = {}
        
        # Reddit sentiment
        wsb = await self.get_wsb_sentiment()
        if 'sentiment_score' in wsb:
            results['reddit_wsb'] = {
                'score': wsb['sentiment_score'],
                'mentions': wsb.get('top_tickers', {}).get(symbol.upper(), 0)
            }
            
        # News sentiment
        news = await self.get_news_sentiment(symbol)
        if 'sentiment_score' in news:
            results['news'] = {
                'score': news['sentiment_score'],
                'articles': news.get('articles_analyzed', 0)
            }
            
        # Fear & Greed (for crypto)
        if symbol.upper() in ['BTC', 'ETH', 'BITCOIN', 'ETHEREUM']:
            fng = await self.get_fear_greed_index()
            if 'value' in fng:
                # Convert 0-100 to -1 to 1
                results['fear_greed'] = {
                    'score': (fng['value'] - 50) / 50,
                    'classification': fng['classification']
                }
                
        # Calculate weighted average
        weights = {'reddit_wsb': 0.3, 'news': 0.4, 'fear_greed': 0.3}
        total_weight = 0
        weighted_sum = 0
        
        for source, data in results.items():
            if source in weights and 'score' in data:
                weighted_sum += data['score'] * weights[source]
                total_weight += weights[source]
                
        aggregate_score = weighted_sum / total_weight if total_weight > 0 else 0
        
        return {
            'symbol': symbol,
            'aggregate_sentiment': aggregate_score,
            'sources': results,
            'signal': 'bullish' if aggregate_score > 0.2 else 'bearish' if aggregate_score < -0.2 else 'neutral',
            'confidence': min(total_weight / sum(weights.values()), 1.0),
            'timestamp': datetime.now().isoformat()
        }
        
    # ==================== GOOGLE TRENDS (FREE) ====================
    
    async def get_search_trends(self, keyword: str) -> Dict[str, Any]:
        """
        Get Google Trends data
        Note: Requires pytrends library
        """
        try:
            from pytrends.request import TrendReq
            
            pytrends = TrendReq(hl='en-US', tz=360)
            pytrends.build_payload([keyword], timeframe='today 3-m')
            
            interest = pytrends.interest_over_time()
            
            if not interest.empty:
                current = interest[keyword].iloc[-1]
                week_ago = interest[keyword].iloc[-7] if len(interest) >= 7 else current
                
                return {
                    'keyword': keyword,
                    'current_interest': int(current),
                    'week_ago_interest': int(week_ago),
                    'change_7d': int(current - week_ago),
                    'trend': 'increasing' if current > week_ago else 'decreasing' if current < week_ago else 'stable',
                    'source': 'google_trends',
                    'timestamp': datetime.now().isoformat()
                }
                
        except ImportError:
            logger.warning("pytrends not installed. Install with: pip install pytrends")
        except Exception as e:
            logger.error(f"Google Trends request failed: {e}")
            
        return {'error': 'Google Trends data not available'}
        
    async def close(self):
        """Close the session"""
        if self._session and not self._session.closed:
            await self._session.close()


# Convenience function
async def get_real_alternative_data():
    """Get a configured real alternative data provider"""
    return RealAlternativeDataProvider()
