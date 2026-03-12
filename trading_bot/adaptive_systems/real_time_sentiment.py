import logging
logger = logging.getLogger(__name__)
"""Real-time Market Sentiment Integration System.

This module provides real-time sentiment analysis integration with multiple data sources:
- News sentiment from financial news APIs
- Social media sentiment from Twitter/Reddit
- Economic calendar events and their impact
- Market sentiment indicators
- Adaptive sentiment weighting based on market conditions
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np
from loguru import logger
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except Exception:
    AIOHTTP_AVAILABLE = False
    aiohttp = None
    logger.warning("aiohttp not available - using offline sentiment fetchers")
import sqlite3
import threading
from collections import deque
import numpy


class SentimentSource(Enum):
    """Sentiment data sources."""
    NEWS_API = "news_api"
    TWITTER = "twitter"
    REDDIT = "reddit"
    ECONOMIC_CALENDAR = "economic_calendar"
    MARKET_INDICATORS = "market_indicators"
    ANALYST_RATINGS = "analyst_ratings"


@dataclass
class SentimentData:
    """Real-time sentiment data point."""
    source: SentimentSource
    symbol: str
    sentiment_score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    impact_weight: float  # 0.0 to 1.0
    timestamp: datetime
    raw_data: Dict[str, Any]
    keywords: List[str]
    relevance_score: float


class RealTimeSentimentEngine:
    """Real-time sentiment analysis and integration engine."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the real-time sentiment engine."""
        self.config = config or {}
        
        # API configurations
        self.news_api_key = self.config.get('news_api_key', 'demo_key')
        self.twitter_bearer_token = self.config.get('twitter_bearer_token', 'demo_token')
        self.reddit_client_id = self.config.get('reddit_client_id', 'demo_id')
        
        # Sentiment buffers
        self.sentiment_buffer = deque(maxlen=1000)
        self.symbol_sentiment = {}
        
        # Real-time processing
        self.is_running = False
        self.update_interval = self.config.get('update_interval', 60)  # seconds
        
        # Database for sentiment history
        self.db_path = self.config.get('db_path', 'sentiment_history.db')
        self._init_database()
        
        # Sentiment weights (adaptive)
        self.source_weights = {
            SentimentSource.NEWS_API: 0.3,
            SentimentSource.TWITTER: 0.2,
            SentimentSource.REDDIT: 0.15,
            SentimentSource.ECONOMIC_CALENDAR: 0.25,
            SentimentSource.MARKET_INDICATORS: 0.1
        }
        
        logger.info("Real-time Sentiment Engine initialized")
    
    def _init_database(self):
        """Initialize SQLite database for sentiment history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sentiment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                symbol TEXT NOT NULL,
                sentiment_score REAL NOT NULL,
                confidence REAL NOT NULL,
                impact_weight REAL NOT NULL,
                timestamp TEXT NOT NULL,
                raw_data TEXT,
                keywords TEXT,
                relevance_score REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def start_real_time_monitoring(self, symbols: List[str]):
        """Start real-time sentiment monitoring for given symbols."""
        self.is_running = True
        self.monitored_symbols = symbols
        
        logger.info(f"Starting real-time sentiment monitoring for {symbols}")
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._monitor_news_sentiment()),
            asyncio.create_task(self._monitor_social_sentiment()),
            asyncio.create_task(self._monitor_economic_events()),
            asyncio.create_task(self._monitor_market_indicators()),
            asyncio.create_task(self._process_sentiment_updates())
        ]
        
        await asyncio.gather(*tasks)
    
    def stop_monitoring(self):
        """Stop real-time sentiment monitoring."""
        self.is_running = False
        logger.info("Real-time sentiment monitoring stopped")
    
    async def _monitor_news_sentiment(self):
        """Monitor news sentiment from financial news APIs."""
        while self.is_running:
            try:
                for symbol in self.monitored_symbols:
                    news_data = await self._fetch_news_sentiment(symbol)
                    
                    for item in news_data:
                        sentiment_data = SentimentData(
                            source=SentimentSource.NEWS_API,
                            symbol=symbol,
                            sentiment_score=item['sentiment_score'],
                            confidence=item['confidence'],
                            impact_weight=item['impact_weight'],
                            timestamp=datetime.now(),
                            raw_data=item,
                            keywords=item.get('keywords', []),
                            relevance_score=item.get('relevance', 0.5)
                        )
                        
                        self.sentiment_buffer.append(sentiment_data)
                        self._store_sentiment_data(sentiment_data)
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error monitoring news sentiment: {e}")
                await asyncio.sleep(30)
    
    async def _fetch_news_sentiment(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch news sentiment from financial news APIs."""
        # Mock implementation - replace with real API calls
        mock_news = [
            {
                'title': f'{symbol} shows strong quarterly results',
                'sentiment_score': np.random.uniform(0.2, 0.8),
                'confidence': np.random.uniform(0.6, 0.9),
                'impact_weight': np.random.uniform(0.3, 0.7),
                'keywords': ['earnings', 'growth', 'revenue'],
                'relevance': np.random.uniform(0.7, 1.0),
                'source': 'Financial Times'
            },
            {
                'title': f'Market volatility affects {symbol} trading',
                'sentiment_score': np.random.uniform(-0.3, 0.3),
                'confidence': np.random.uniform(0.5, 0.8),
                'impact_weight': np.random.uniform(0.2, 0.5),
                'keywords': ['volatility', 'trading', 'market'],
                'relevance': np.random.uniform(0.6, 0.9),
                'source': 'Reuters'
            }
        ]
        
        return mock_news
    
    async def _monitor_social_sentiment(self):
        """Monitor social media sentiment from Twitter and Reddit."""
        while self.is_running:
            try:
                for symbol in self.monitored_symbols:
                    # Twitter sentiment
                    twitter_data = await self._fetch_twitter_sentiment(symbol)
                    for item in twitter_data:
                        sentiment_data = SentimentData(
                            source=SentimentSource.TWITTER,
                            symbol=symbol,
                            sentiment_score=item['sentiment_score'],
                            confidence=item['confidence'],
                            impact_weight=0.3,  # Lower weight for social media
                            timestamp=datetime.now(),
                            raw_data=item,
                            keywords=item.get('keywords', []),
                            relevance_score=item.get('relevance', 0.4)
                        )
                        self.sentiment_buffer.append(sentiment_data)
                        self._store_sentiment_data(sentiment_data)
                    
                    # Reddit sentiment
                    reddit_data = await self._fetch_reddit_sentiment(symbol)
                    for item in reddit_data:
                        sentiment_data = SentimentData(
                            source=SentimentSource.REDDIT,
                            symbol=symbol,
                            sentiment_score=item['sentiment_score'],
                            confidence=item['confidence'],
                            impact_weight=0.25,
                            timestamp=datetime.now(),
                            raw_data=item,
                            keywords=item.get('keywords', []),
                            relevance_score=item.get('relevance', 0.4)
                        )
                        self.sentiment_buffer.append(sentiment_data)
                        self._store_sentiment_data(sentiment_data)
                
                await asyncio.sleep(self.update_interval * 2)  # Less frequent for social media
                
            except Exception as e:
                logger.error(f"Error monitoring social sentiment: {e}")
                await asyncio.sleep(60)
    
    async def _fetch_twitter_sentiment(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch Twitter sentiment data."""
        # Mock implementation
        mock_tweets = [
            {
                'text': f'Bullish on {symbol} after latest news',
                'sentiment_score': np.random.uniform(0.1, 0.6),
                'confidence': np.random.uniform(0.4, 0.7),
                'keywords': ['bullish', 'news'],
                'relevance': np.random.uniform(0.3, 0.7),
                'followers': np.random.randint(100, 10000)
            }
        ]
        return mock_tweets
    
    async def _fetch_reddit_sentiment(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch Reddit sentiment data."""
        # Mock implementation
        mock_posts = [
            {
                'title': f'Discussion: {symbol} technical analysis',
                'sentiment_score': np.random.uniform(-0.2, 0.4),
                'confidence': np.random.uniform(0.3, 0.6),
                'keywords': ['technical', 'analysis'],
                'relevance': np.random.uniform(0.4, 0.8),
                'upvotes': np.random.randint(10, 500)
            }
        ]
        return mock_posts
    
    async def _monitor_economic_events(self):
        """Monitor economic calendar events and their sentiment impact."""
        while self.is_running:
            try:
                economic_events = await self._fetch_economic_events()
                
                for event in economic_events:
                    # Calculate sentiment impact based on event outcome vs expectations
                    sentiment_score = self._calculate_economic_sentiment(event)
                    
                    sentiment_data = SentimentData(
                        source=SentimentSource.ECONOMIC_CALENDAR,
                        symbol='MARKET',  # Economic events affect overall market
                        sentiment_score=sentiment_score,
                        confidence=0.8,  # High confidence for economic data
                        impact_weight=0.6,  # High impact weight
                        timestamp=datetime.now(),
                        raw_data=event,
                        keywords=event.get('keywords', []),
                        relevance_score=0.8
                    )
                    
                    self.sentiment_buffer.append(sentiment_data)
                    self._store_sentiment_data(sentiment_data)
                
                await asyncio.sleep(self.update_interval * 5)  # Less frequent for economic events
                
            except Exception as e:
                logger.error(f"Error monitoring economic events: {e}")
                await asyncio.sleep(300)
    
    async def _fetch_economic_events(self) -> List[Dict[str, Any]]:
        """Fetch economic calendar events."""
        # Mock implementation
        mock_events = [
            {
                'event': 'Non-Farm Payrolls',
                'actual': 250000,
                'forecast': 200000,
                'previous': 180000,
                'impact': 'high',
                'keywords': ['employment', 'jobs', 'economy']
            },
            {
                'event': 'CPI Inflation',
                'actual': 3.2,
                'forecast': 3.0,
                'previous': 2.8,
                'impact': 'high',
                'keywords': ['inflation', 'prices', 'fed']
            }
        ]
        return mock_events
    
    def _calculate_economic_sentiment(self, event: Dict[str, Any]) -> float:
        """Calculate sentiment score based on economic event outcome."""
        actual = event.get('actual', 0)
        forecast = event.get('forecast', 0)
        
        if forecast == 0:
            return 0.0
        
        # Calculate surprise factor
        surprise = (actual - forecast) / abs(forecast)
        
        # Convert to sentiment score (-1 to 1)
        sentiment = np.tanh(surprise * 2)  # Tanh to bound between -1 and 1
        
        return float(sentiment)
    
    async def _monitor_market_indicators(self):
        """Monitor market-based sentiment indicators."""
        while self.is_running:
            try:
                for symbol in self.monitored_symbols:
                    indicators = await self._fetch_market_indicators(symbol)
                    
                    sentiment_data = SentimentData(
                        source=SentimentSource.MARKET_INDICATORS,
                        symbol=symbol,
                        sentiment_score=indicators['composite_sentiment'],
                        confidence=0.7,
                        impact_weight=0.4,
                        timestamp=datetime.now(),
                        raw_data=indicators,
                        keywords=['vix', 'put_call', 'momentum'],
                        relevance_score=0.6
                    )
                    
                    self.sentiment_buffer.append(sentiment_data)
                    self._store_sentiment_data(sentiment_data)
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error monitoring market indicators: {e}")
                await asyncio.sleep(60)
    
    async def _fetch_market_indicators(self, symbol: str) -> Dict[str, Any]:
        """Fetch market-based sentiment indicators."""
        # Mock implementation - in reality, fetch VIX, put/call ratios, etc.
        vix_level = np.random.uniform(15, 35)
        put_call_ratio = np.random.uniform(0.8, 1.5)
        momentum = np.random.uniform(-0.5, 0.5)
        
        # Calculate composite sentiment
        vix_sentiment = -((vix_level - 20) / 20)  # Lower VIX = more positive
        pc_sentiment = -(put_call_ratio - 1.0)  # Lower P/C ratio = more positive
        
        composite = (vix_sentiment + pc_sentiment + momentum) / 3
        
        return {
            'vix_level': vix_level,
            'put_call_ratio': put_call_ratio,
            'momentum': momentum,
            'composite_sentiment': composite
        }
    
    async def _process_sentiment_updates(self):
        """Process and aggregate sentiment updates."""
        while self.is_running:
            try:
                if len(self.sentiment_buffer) > 0:
                    # Process recent sentiment data
                    recent_data = list(self.sentiment_buffer)[-50:]  # Last 50 items
                    
                    # Aggregate by symbol
                    symbol_aggregates = {}
                    for data in recent_data:
                        if data.symbol not in symbol_aggregates:
                            symbol_aggregates[data.symbol] = []
                        symbol_aggregates[data.symbol].append(data)
                    
                    # Calculate weighted sentiment for each symbol
                    for symbol, data_list in symbol_aggregates.items():
                        weighted_sentiment = self._calculate_weighted_sentiment(data_list)
                        self.symbol_sentiment[symbol] = weighted_sentiment
                    
                    # Adapt source weights based on recent performance
                    self._adapt_source_weights()
                
                await asyncio.sleep(10)  # Process every 10 seconds
                
            except Exception as e:
                logger.error(f"Error processing sentiment updates: {e}")
                await asyncio.sleep(30)
    
    def _calculate_weighted_sentiment(self, data_list: List[SentimentData]) -> Dict[str, float]:
        """Calculate weighted sentiment score from multiple sources."""
        if not data_list:
            return {'score': 0.0, 'confidence': 0.0}
        
        total_weight = 0
        weighted_sum = 0
        confidence_sum = 0
        
        for data in data_list:
            source_weight = self.source_weights.get(data.source, 0.1)
            weight = source_weight * data.confidence * data.impact_weight * data.relevance_score
            
            weighted_sum += data.sentiment_score * weight
            confidence_sum += data.confidence * weight
            total_weight += weight
        
        if total_weight == 0:
            return {'score': 0.0, 'confidence': 0.0}
        
        return {
            'score': weighted_sum / total_weight,
            'confidence': confidence_sum / total_weight,
            'data_points': len(data_list),
            'timestamp': datetime.now()
        }
    
    def _adapt_source_weights(self):
        """Adapt source weights based on recent performance and market conditions."""
        # Simple adaptation - increase weight of sources with higher confidence
        recent_data = list(self.sentiment_buffer)[-100:]
        
        source_performance = {}
        for data in recent_data:
            if data.source not in source_performance:
                source_performance[data.source] = []
            source_performance[data.source].append(data.confidence)
        
        # Adjust weights based on average confidence
        for source, confidences in source_performance.items():
            avg_confidence = np.mean(confidences)
            current_weight = self.source_weights.get(source, 0.1)
            
            # Gradually adjust weight based on performance
            adjustment = (avg_confidence - 0.5) * 0.1  # Max 10% adjustment
            new_weight = max(0.05, min(0.5, current_weight + adjustment))
            self.source_weights[source] = new_weight
    
    def _store_sentiment_data(self, data: SentimentData):
        """Store sentiment data in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sentiment_history 
                (source, symbol, sentiment_score, confidence, impact_weight, 
                 timestamp, raw_data, keywords, relevance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.source.value,
                data.symbol,
                data.sentiment_score,
                data.confidence,
                data.impact_weight,
                data.timestamp.isoformat(),
                json.dumps(data.raw_data),
                json.dumps(data.keywords),
                data.relevance_score
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing sentiment data: {e}")
    
    def get_current_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get current sentiment for a symbol."""
        if symbol in self.symbol_sentiment:
            return self.symbol_sentiment[symbol]
        
        return {'score': 0.0, 'confidence': 0.0, 'data_points': 0}
    
    def get_sentiment_history(self, symbol: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get sentiment history for a symbol."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT * FROM sentiment_history 
                WHERE symbol = ? AND timestamp > ?
                ORDER BY timestamp DESC
            ''', (symbol, cutoff_time.isoformat()))
            
            rows = cursor.fetchall()
            conn.close()
            
            history = []
            for row in rows:
                history.append({
                    'source': row[1],
                    'sentiment_score': row[3],
                    'confidence': row[4],
                    'timestamp': row[6],
                    'keywords': json.loads(row[8]) if row[8] else []
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error fetching sentiment history: {e}")
            return []
    
    def get_sentiment_summary(self) -> Dict[str, Any]:
        """Get overall sentiment monitoring summary."""
        return {
            'is_running': self.is_running,
            'monitored_symbols': getattr(self, 'monitored_symbols', []),
            'buffer_size': len(self.sentiment_buffer),
            'tracked_symbols': len(self.symbol_sentiment),
            'source_weights': self.source_weights,
            'last_update': datetime.now().isoformat()
        }
