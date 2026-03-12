"""
Real-time Market Sentiment Engine

Captures alpha from news, social media, and alternative data sources.
Provides sentiment signals for trading decisions.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque
import logging
import asyncio
import re

logger = logging.getLogger(__name__)


@dataclass
class SentimentSignal:
    """Sentiment signal data"""
    source: str
    symbol: str
    sentiment_score: float  # -1 to 1
    magnitude: float  # 0 to 1
    confidence: float  # 0 to 1
    timestamp: datetime
    raw_text: str
    entities: List[str]
    topics: List[str]


@dataclass
class NewsEvent:
    """News event data"""
    headline: str
    summary: str
    source: str
    timestamp: datetime
    symbols: List[str]
    sentiment: float
    impact_score: float
    category: str


class SentimentAnalyzer:
    """
    Advanced Sentiment Analysis Engine
    
    Uses NLP and ML to extract sentiment from text data.
    """
    
    def __init__(self):
        # Sentiment lexicons
        self.positive_words = {
            'bullish', 'surge', 'rally', 'breakout', 'upgrade', 'beat', 'exceed',
            'strong', 'growth', 'profit', 'gain', 'rise', 'soar', 'jump', 'boom',
            'outperform', 'momentum', 'breakthrough', 'innovation', 'expansion'
        }
        
        self.negative_words = {
            'bearish', 'crash', 'plunge', 'downgrade', 'miss', 'decline', 'fall',
            'weak', 'loss', 'drop', 'tumble', 'slump', 'collapse', 'concern',
            'underperform', 'risk', 'warning', 'crisis', 'recession', 'bankruptcy'
        }
        
        # Intensity modifiers
        self.intensifiers = {
            'very': 1.5, 'extremely': 2.0, 'highly': 1.5, 'significantly': 1.8,
            'massively': 2.0, 'substantially': 1.7, 'dramatically': 1.9
        }
        
        self.diminishers = {
            'slightly': 0.5, 'somewhat': 0.6, 'moderately': 0.7, 'barely': 0.3
        }
        
        # Try to load transformer model for advanced analysis
        self.use_transformer = False
        try:
            from transformers import pipeline
            self.sentiment_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
            self.use_transformer = True
            logger.info("FinBERT transformer model loaded for sentiment analysis")
        except ImportError:
            logger.info("Transformers not available, using lexicon-based sentiment analysis")
    
    def analyze_text(self, text: str) -> Tuple[float, float]:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            
        Returns:
            (sentiment_score, confidence)
        """
        if self.use_transformer:
            return self._transformer_sentiment(text)
        else:
            return self._lexicon_sentiment(text)
    
    def _transformer_sentiment(self, text: str) -> Tuple[float, float]:
        """Transformer-based sentiment analysis"""
        try:
            result = self.sentiment_pipeline(text[:512])[0]  # Limit to 512 tokens
            
            # Convert to -1 to 1 scale
            if result['label'] == 'positive':
                sentiment = result['score']
            elif result['label'] == 'negative':
                sentiment = -result['score']
            else:
                sentiment = 0.0
            
            confidence = result['score']
            
            return sentiment, confidence
            
        except Exception as e:
            logger.error(f"Transformer sentiment analysis failed: {e}")
            return self._lexicon_sentiment(text)
    
    def _lexicon_sentiment(self, text: str) -> Tuple[float, float]:
        """Lexicon-based sentiment analysis"""
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        sentiment_score = 0.0
        word_count = 0
        
        for i, word in enumerate(words):
            # Check for intensity modifiers
            modifier = 1.0
            if i > 0:
                prev_word = words[i-1]
                if prev_word in self.intensifiers:
                    modifier = self.intensifiers[prev_word]
                elif prev_word in self.diminishers:
                    modifier = self.diminishers[prev_word]
            
            # Check sentiment
            if word in self.positive_words:
                sentiment_score += 1.0 * modifier
                word_count += 1
            elif word in self.negative_words:
                sentiment_score -= 1.0 * modifier
                word_count += 1
        
        # Normalize
        if word_count > 0:
            sentiment = np.clip(sentiment_score / word_count, -1, 1)
            confidence = min(1.0, word_count / 10)  # More words = higher confidence
        else:
            sentiment = 0.0
            confidence = 0.0
        
        return sentiment, confidence
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract named entities (companies, tickers)"""
        # Simple regex-based extraction
        # In production, would use NER model
        
        # Extract ticker symbols (uppercase 1-5 letters)
        tickers = re.findall(r'\b[A-Z]{1,5}\b', text)
        
        # Extract company names (capitalized words)
        companies = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        entities = list(set(tickers + companies))
        
        return entities[:10]  # Limit to top 10


class NewsAggregator:
    """
    News Aggregation and Processing
    
    Collects news from multiple sources and processes for trading signals.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # News sources (in production, would use actual APIs)
        self.sources = [
            'Bloomberg', 'Reuters', 'CNBC', 'WSJ', 'FT',
            'MarketWatch', 'Seeking Alpha', 'Benzinga'
        ]
        
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # News cache
        self.news_cache = deque(maxlen=1000)
        
        # Impact scoring weights
        self.source_weights = {
            'Bloomberg': 1.0,
            'Reuters': 1.0,
            'WSJ': 0.9,
            'FT': 0.9,
            'CNBC': 0.7,
            'MarketWatch': 0.6,
            'Seeking Alpha': 0.5,
            'Benzinga': 0.5
        }
    
    async def fetch_news(self, symbol: Optional[str] = None) -> List[NewsEvent]:
        """
        Fetch latest news from multiple sources.
        
        Args:
            symbol: Optional symbol to filter news
            
        Returns:
            List of news events
        """
        news_events = []
        
        try:
            # Try NewsAPI (free tier: 100 requests/day)
            newsapi_events = await self._fetch_newsapi(symbol)
            news_events.extend(newsapi_events)
        except Exception as e:
            logger.warning(f"NewsAPI fetch failed: {e}")
        # Try Yahoo Finance RSS
            yahoo_events = await self._fetch_yahoo_rss(symbol)
            news_events.extend(yahoo_events)
        except Exception as e:
            logger.warning(f"Yahoo RSS fetch failed: {e}")
        # Try Reddit (free)
            reddit_events = await self._fetch_reddit_news(symbol)
            news_events.extend(reddit_events)
        except Exception as e:
            logger.warning(f"Reddit fetch failed: {e}")
        
        return news_events
    
    async def _fetch_newsapi(self, symbol: Optional[str] = None) -> List[NewsEvent]:
        """Fetch news from NewsAPI"""
        import aiohttp
        
        api_key = self.config.get('newsapi_key', '')
        if not api_key:
            return []
        
        query = symbol or 'stock market'
        url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={api_key}"
        
        events = []
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    for article in data.get('articles', [])[:10]:
                        event = self.process_news(
                            headline=article.get('title', ''),
                            summary=article.get('description', ''),
                            source=article.get('source', {}).get('name', 'NewsAPI')
                        )
                        events.append(event)
        return events
    
    async def _fetch_yahoo_rss(self, symbol: Optional[str] = None) -> List[NewsEvent]:
        """Fetch news from Yahoo Finance RSS"""
        import xml.etree.ElementTree as ET
        
        if symbol:
            url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
        else:
            url = "https://feeds.finance.yahoo.com/rss/2.0/headline?region=US&lang=en-US"
        
        events = []
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                    try:
                        root = ET.fromstring(content)
                        for item in root.findall('.//item')[:10]:
                            title = item.find('title')
                            desc = item.find('description')
                            if title is not None:
                                event = self.process_news(
                                    headline=title.text or '',
                                    summary=desc.text if desc is not None else '',
                                    source='Yahoo Finance'
                                )
                                events.append(event)
                    except ET.ParseError:
                        pass
        return events
    
    async def _fetch_reddit_news(self, symbol: Optional[str] = None) -> List[NewsEvent]:
        """Fetch news from Reddit"""
        
        subreddits = ['wallstreetbets', 'stocks', 'investing']
        if symbol:
            query = f"{symbol} stock"
        else:
            query = "stock market"
        
        events = []
        headers = {'User-Agent': 'TradingBot/1.0'}
        
        for subreddit in subreddits:
            url = f"https://www.reddit.com/r/{subreddit}/search.json?q={query}&sort=new&limit=5"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        for post in data.get('data', {}).get('children', []):
                            post_data = post.get('data', {})
                            event = self.process_news(
                                headline=post_data.get('title', ''),
                                summary=post_data.get('selftext', '')[:500],
                                source=f'Reddit r/{subreddit}'
                            )
                            events.append(event)
        return events
    
    def process_news(self, headline: str, summary: str, source: str) -> NewsEvent:
        """Process a news article"""
        # Analyze sentiment
        combined_text = f"{headline}. {summary}"
        sentiment, confidence = self.sentiment_analyzer.analyze_text(combined_text)
        
        # Extract entities
        entities = self.sentiment_analyzer.extract_entities(combined_text)
        
        # Calculate impact score
        source_weight = self.source_weights.get(source, 0.5)
        impact_score = abs(sentiment) * confidence * source_weight
        
        # Categorize
        category = self._categorize_news(combined_text)
        
        event = NewsEvent(
            headline=headline,
            summary=summary,
            source=source,
            timestamp=datetime.now(),
            symbols=entities,
            sentiment=sentiment,
            impact_score=impact_score,
            category=category
        )
        
        self.news_cache.append(event)
        
        return event
    
    def _categorize_news(self, text: str) -> str:
        """Categorize news by topic"""
        text_lower = text.lower()
        
        categories = {
            'earnings': ['earnings', 'revenue', 'profit', 'eps', 'guidance'],
            'merger': ['merger', 'acquisition', 'buyout', 'takeover'],
            'regulatory': ['sec', 'fda', 'regulation', 'approval', 'investigation'],
            'product': ['launch', 'product', 'release', 'innovation'],
            'management': ['ceo', 'executive', 'resign', 'appoint', 'hire'],
            'macro': ['fed', 'interest rate', 'inflation', 'gdp', 'unemployment']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'general'


class SocialMediaMonitor:
    """
    Social Media Sentiment Monitor
    
    Tracks sentiment from Twitter, Reddit, StockTwits, etc.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # Social media sources
        self.platforms = ['Twitter', 'Reddit', 'StockTwits', 'Discord']
        
        # Sentiment history
        self.sentiment_history = {}
    
    async def monitor_symbol(self, symbol: str) -> Dict:
        """
        Monitor social media sentiment for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Aggregated sentiment data
        """
        platform_sentiments = {}
        
        try:
            # Fetch from Reddit (free, no API key required)
            reddit_sentiment = await self._fetch_reddit_sentiment(symbol)
            platform_sentiments['Reddit'] = reddit_sentiment
        except Exception as e:
            logger.warning(f"Reddit sentiment fetch failed: {e}")
            platform_sentiments['Reddit'] = {'sentiment': 0, 'volume': 0, 'trending': False}
        # Fetch from StockTwits (free, limited)
            stocktwits_sentiment = await self._fetch_stocktwits_sentiment(symbol)
            platform_sentiments['StockTwits'] = stocktwits_sentiment
        except Exception as e:
            logger.warning(f"StockTwits sentiment fetch failed: {e}")
            platform_sentiments['StockTwits'] = {'sentiment': 0, 'volume': 0, 'trending': False}
        
        # Twitter placeholder (requires API key)
        platform_sentiments['Twitter'] = {'sentiment': 0, 'volume': 0, 'trending': False}
        platform_sentiments['Discord'] = {'sentiment': 0, 'volume': 0, 'trending': False}
    
    async def _fetch_reddit_sentiment(self, symbol: str) -> Dict:
        """Fetch sentiment from Reddit"""
        
        subreddits = ['wallstreetbets', 'stocks', 'investing', 'stockmarket']
        headers = {'User-Agent': 'TradingBot/1.0'}
        
        all_sentiments = []
        total_posts = 0
        
        for subreddit in subreddits:
            url = f"https://www.reddit.com/r/{subreddit}/search.json?q={symbol}&sort=new&limit=25&t=day"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = data.get('data', {}).get('children', [])
                        
                        for post in posts:
                            post_data = post.get('data', {})
                            title = post_data.get('title', '')
                            text = post_data.get('selftext', '')
                            score = post_data.get('score', 0)
                            
                            # Analyze sentiment
                            combined = f"{title}. {text}"
                            sentiment, confidence = self.sentiment_analyzer.analyze_text(combined)
                            
                            # Weight by upvotes
                            weighted_sentiment = sentiment * (1 + np.log1p(max(score, 1)))
                            all_sentiments.append(weighted_sentiment)
                            total_posts += 1
        
        avg_sentiment = np.mean(all_sentiments) if all_sentiments else 0
        return {
            'sentiment': float(avg_sentiment),
            'volume': total_posts,
            'trending': total_posts > 50
        }
    
    async def _fetch_stocktwits_sentiment(self, symbol: str) -> Dict:
        """Fetch sentiment from StockTwits"""
        
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    messages = data.get('messages', [])
                    
                    bullish = 0
                    bearish = 0
                    
                    for msg in messages:
                        sentiment = msg.get('entities', {}).get('sentiment', {})
                        if sentiment.get('basic') == 'Bullish':
                            bullish += 1
                        elif sentiment.get('basic') == 'Bearish':
                            bearish += 1
                    
                    total = bullish + bearish
                    if total > 0:
                        sentiment_score = (bullish - bearish) / total
                    else:
                        sentiment_score = 0
                    
                    return {
                        'sentiment': sentiment_score,
                        'volume': len(messages),
                        'trending': data.get('symbol', {}).get('is_following', False)
                    }
        
        return {'sentiment': 0, 'volume': 0, 'trending': False}
    
    def detect_sentiment_surge(self, symbol: str) -> bool:
        """Detect sudden sentiment surge"""
        if symbol not in self.sentiment_history or len(self.sentiment_history[symbol]) < 10:
            return False
        
        recent = list(self.sentiment_history[symbol])[-5:]
        historical = list(self.sentiment_history[symbol])[-20:-5]
        
        recent_volume = np.mean([h['volume'] for h in recent])
        historical_volume = np.mean([h['volume'] for h in historical])
        
        # Surge if volume increased by 3x
        return recent_volume > historical_volume * 3


class RealtimeSentimentEngine:
    """
    Integrated Real-time Sentiment Engine
    
    Combines news, social media, and alternative data for trading signals.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.news_aggregator = NewsAggregator(config)
        self.social_monitor = SocialMediaMonitor(config)
        
        # Signal generation
        self.min_signal_strength = self.config.get('min_signal_strength', 0.3)
        
        # Active signals
        self.active_signals = {}
        
        logger.info("Real-time Sentiment Engine initialized")
    
    async def generate_signals(self, symbols: List[str]) -> List[SentimentSignal]:
        """
        Generate sentiment signals for symbols
        
        Args:
            symbols: List of symbols to analyze
            
        Returns:
            List of sentiment signals
        """
        signals = []
        
        for symbol in symbols:
            # Get social media sentiment
            social_data = await self.social_monitor.monitor_symbol(symbol)
            
            # Get news sentiment
            news_events = await self.news_aggregator.fetch_news(symbol)
            
            # Combine signals
            if news_events:
                news_sentiment = np.mean([n.sentiment for n in news_events])
                news_impact = np.mean([n.impact_score for n in news_events])
            else:
                news_sentiment = 0.0
                news_impact = 0.0
            
            social_sentiment = social_data['sentiment']
            social_volume = social_data['volume']
            
            # Weighted combination
            combined_sentiment = (
                news_sentiment * 0.6 +
                social_sentiment * 0.4
            )
            
            # Calculate magnitude and confidence
            magnitude = abs(combined_sentiment)
            confidence = min(1.0, (news_impact + social_volume / 1000) / 2)
            
            # Generate signal if strong enough
            if magnitude > self.min_signal_strength and confidence > 0.5:
                signal = SentimentSignal(
                    source='COMBINED',
                    symbol=symbol,
                    sentiment_score=combined_sentiment,
                    magnitude=magnitude,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    raw_text=f"News: {news_sentiment:.2f}, Social: {social_sentiment:.2f}",
                    entities=[symbol],
                    topics=['sentiment']
                )
                
                signals.append(signal)
                self.active_signals[symbol] = signal
                
                logger.info(f"Sentiment signal for {symbol}: {combined_sentiment:.2f} "
                          f"(magnitude: {magnitude:.2f}, confidence: {confidence:.2f})")
        
        return signals
    
    def get_trading_recommendation(self, signal: SentimentSignal) -> Dict:
        """
        Convert sentiment signal to trading recommendation
        
        Args:
            signal: Sentiment signal
            
        Returns:
            Trading recommendation
        """
        # Calculate position size based on confidence
        base_size = 1.0
        position_size = base_size * signal.confidence * signal.magnitude
        
        # Determine action
        if signal.sentiment_score > 0.3:
            action = 'BUY'
        elif signal.sentiment_score < -0.3:
            action = 'SELL'
        else:
            action = 'HOLD'
        
        # Calculate urgency
        if signal.magnitude > 0.7:
            urgency = 'HIGH'
        elif signal.magnitude > 0.5:
            urgency = 'MEDIUM'
        else:
            urgency = 'LOW'
        
        return {
            'symbol': signal.symbol,
            'action': action,
            'position_size': position_size,
            'urgency': urgency,
            'confidence': signal.confidence,
            'reason': f"Sentiment: {signal.sentiment_score:.2f}, Source: {signal.source}"
        }


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        engine = RealtimeSentimentEngine()
        
        # Generate signals for symbols
        symbols = ['AAPL', 'GOOGL', 'TSLA', 'MSFT']
        
        logger.info("\nGenerating sentiment signals...\n")
        
        signals = await engine.generate_signals(symbols)
        
        logger.info(f"Generated {len(signals)} signals:\n")
        
        for signal in signals:
            logger.info(f"{signal.symbol}:")
            logger.info(f"  Sentiment: {signal.sentiment_score:.2f}")
            logger.info(f"  Magnitude: {signal.magnitude:.2f}")
            logger.info(f"  Confidence: {signal.confidence:.2f}")
            
            # Get trading recommendation
            rec = engine.get_trading_recommendation(signal)
            logger.info(f"  Recommendation: {rec['action']} (urgency: {rec['urgency']})")
            logger.info(f"  Position Size: {rec['position_size']:.2f}")
            print()
    
    asyncio.run(main())
