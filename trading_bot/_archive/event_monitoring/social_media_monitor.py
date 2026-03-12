"""
Elite Trading Bot - Social Media Monitor

This module provides social media monitoring capabilities for the Elite Trading Bot,
enabling tracking of market sentiment, trending topics, and influential posts.
"""

import enum
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
import json

try:
    import aiohttp
except ImportError:
    aiohttp = None
import pandas as pd
import numpy as np
from nltk.sentiment import SentimentIntensityAnalyzer

from .event_monitor import EventMonitor, SocialMediaEvent, EventType, EventPriority, EventSource
from enum import Enum
from enum import auto
import numpy
import pandas

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



# Configure logging
logger = logging.getLogger(__name__)


class SocialMediaSource(enum.Enum):
    """Supported social media sources."""
    TWITTER = "twitter"
    REDDIT = "reddit"
    STOCKTWITS = "stocktwits"
    TRADINGVIEW = "tradingview"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    CUSTOM = "custom"


@dataclass
class SocialMediaTrend:
    """Represents a trending topic on social media."""
    topic: str
    source: SocialMediaSource
    volume: int
    sentiment_score: float
    momentum: float  # Rate of change in volume
    start_time: datetime
    peak_time: Optional[datetime] = None
    is_growing: bool = True
    related_symbols: List[str] = field(default_factory=list)
    related_topics: List[str] = field(default_factory=list)
    sample_posts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SocialMediaAnalysisResult:
    """Results of social media analysis."""
    trends: List[SocialMediaTrend]
    sentiment_by_symbol: Dict[str, float]
    volume_by_symbol: Dict[str, int]
    influential_posts: List[Dict[str, Any]]
    timestamp: datetime = field(default_factory=datetime.now)


class TrendDetector:
    """Detects trending topics in social media data."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize trend detector.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Historical data
        self.topic_history: Dict[str, List[Tuple[datetime, int, float]]] = {}
        self.active_trends: Dict[str, SocialMediaTrend] = {}
        
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        defaults = {
            "min_volume_threshold": 10,
            "trend_detection_window_hours": 24,
            "trend_momentum_threshold": 0.2,
            "max_sample_posts": 5,
            "min_trend_duration_minutes": 30
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def update_topic_data(self, 
                         topic: str, 
                         source: SocialMediaSource,
                         volume: int,
                         sentiment_score: float,
                         timestamp: datetime,
                         related_symbols: List[str] = None,
                         sample_posts: List[Dict[str, Any]] = None):
        """
        Update data for a topic.
        
        Args:
            topic: Topic name
            source: Social media source
            volume: Current volume
            sentiment_score: Current sentiment score
            timestamp: Current timestamp
            related_symbols: Optional list of related symbols
            sample_posts: Optional list of sample posts
        """
        # Create topic key
        topic_key = f"{source.value}:{topic}"
        
        # Initialize history if needed
        if topic_key not in self.topic_history:
            self.topic_history[topic_key] = []
        
        # Add data point
        self.topic_history[topic_key].append((timestamp, volume, sentiment_score))
        
        # Keep only recent history
        cutoff = timestamp - timedelta(hours=self.config["trend_detection_window_hours"])
        self.topic_history[topic_key] = [
            (ts, vol, sent) for ts, vol, sent in self.topic_history[topic_key]
            if ts >= cutoff
        ]
        
        # Check if this is a trend
        is_trend = self._check_if_trend(topic_key, timestamp)
        
        if is_trend:
            # Create or update trend
            if topic_key in self.active_trends:
                trend = self.active_trends[topic_key]
                trend.volume = volume
                trend.sentiment_score = sentiment_score
                
                # Update momentum
                history = self.topic_history[topic_key]
                if len(history) >= 2:
                    oldest_ts, oldest_vol, _ = history[0]
                    time_diff = (timestamp - oldest_ts).total_seconds() / 3600  # hours
                    if time_diff > 0:
                        vol_diff = volume - oldest_vol
                        trend.momentum = vol_diff / time_diff
                
                # Update peak time if this is a new peak
                if volume > trend.volume:
                    trend.peak_time = timestamp
                
                # Update growing status
                trend.is_growing = trend.momentum > 0
                
                # Update related symbols
                if related_symbols:
                    for symbol in related_symbols:
                        if symbol not in trend.related_symbols:
                            trend.related_symbols.append(symbol)
                
                # Update sample posts
                if sample_posts:
                    for post in sample_posts:
                        if len(trend.sample_posts) < self.config["max_sample_posts"]:
                            trend.sample_posts.append(post)
            else:
                # Create new trend
                self.active_trends[topic_key] = SocialMediaTrend(
                    topic=topic,
                    source=source,
                    volume=volume,
                    sentiment_score=sentiment_score,
                    momentum=0.0,  # Will be calculated on next update
                    start_time=timestamp,
                    related_symbols=related_symbols or [],
                    sample_posts=sample_posts[:self.config["max_sample_posts"]] if sample_posts else []
                )
        elif topic_key in self.active_trends:
            # No longer a trend, remove it
            del self.active_trends[topic_key]
    
    def _check_if_trend(self, topic_key: str, current_time: datetime) -> bool:
        """
        Check if a topic is trending.
        
        Args:
            topic_key: Topic key
            current_time: Current timestamp
            
        Returns:
            True if topic is trending, False otherwise
        """
        history = self.topic_history[topic_key]
        
        # Need at least 2 data points
        if len(history) < 2:
            return False
        
        # Get latest volume
        _, latest_volume, _ = history[-1]
        
        # Check if volume is above threshold
        if latest_volume < self.config["min_volume_threshold"]:
            return False
        
        # Check if trend has been active for minimum duration
        oldest_ts, _, _ = history[0]
        duration_minutes = (current_time - oldest_ts).total_seconds() / 60
        
        if duration_minutes < self.config["min_trend_duration_minutes"]:
            return False
        
        # Check momentum
        if len(history) >= 3:
            # Calculate momentum over last 3 data points
            recent_history = history[-3:]
            timestamps = [ts for ts, _, _ in recent_history]
            volumes = [vol for _, vol, _ in recent_history]
            
            # Simple linear regression for momentum
            x = [(ts - timestamps[0]).total_seconds() / 3600 for ts in timestamps]  # hours
            y = volumes
            
            if max(x) > 0:  # Avoid division by zero
                # Calculate slope
                n = len(x)
                sum_x = sum(x)
                sum_y = sum(y)
                sum_xy = sum(x[i] * y[i] for i in range(n))
                sum_xx = sum(x[i] * x[i] for i in range(n))
                
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
                
                # Normalize by latest volume
                normalized_slope = slope / latest_volume if latest_volume > 0 else 0
                
                # Check if momentum is above threshold
                return normalized_slope >= self.config["trend_momentum_threshold"]
        
        # Default to True if we can't calculate momentum yet
        return True
    
    def get_active_trends(self) -> List[SocialMediaTrend]:
        """
        Get list of active trends.
        
        Returns:
            List of active trends
        """
        return list(self.active_trends.values())
    
    def get_trend(self, topic: str, source: SocialMediaSource) -> Optional[SocialMediaTrend]:
        """
        Get a specific trend.
        
        Args:
            topic: Topic name
            source: Social media source
            
        Returns:
            Trend or None if not found
        """
        topic_key = f"{source.value}:{topic}"
        return self.active_trends.get(topic_key)


class SentimentAnalyzer:
    """Analyzes sentiment in social media posts."""
    
    def __init__(self):
        """Initialize sentiment analyzer."""
        self.vader = SentimentIntensityAnalyzer()
        
        # Historical sentiment data
        self.sentiment_history: Dict[str, List[Tuple[datetime, float]]] = {}
        
    def analyze_text(self, text: str) -> float:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment score (-1 to 1)
        """
        scores = self.vader.polarity_scores(text)
        return scores["compound"]
    
    def analyze_posts(self, posts: List[Dict[str, Any]], text_key: str = "text") -> List[float]:
        """
        Analyze sentiment of multiple posts.
        
        Args:
            posts: List of post dictionaries
            text_key: Key for text content in post dictionaries
            
        Returns:
            List of sentiment scores
        """
        return [self.analyze_text(post[text_key]) for post in posts if text_key in post]
    
    def update_symbol_sentiment(self, symbol: str, sentiment_score: float, timestamp: datetime):
        """
        Update sentiment history for a symbol.
        
        Args:
            symbol: Symbol
            sentiment_score: Current sentiment score
            timestamp: Current timestamp
        """
        if symbol not in self.sentiment_history:
            self.sentiment_history[symbol] = []
            
        self.sentiment_history[symbol].append((timestamp, sentiment_score))
        
        # Keep only recent history (last 100 data points)
        if len(self.sentiment_history[symbol]) > 100:
            self.sentiment_history[symbol] = self.sentiment_history[symbol][-100:]
    
    def get_symbol_sentiment(self, symbol: str) -> Optional[float]:
        """
        Get current sentiment for a symbol.
        
        Args:
            symbol: Symbol
            
        Returns:
            Current sentiment score or None if not available
        """
        if symbol not in self.sentiment_history or not self.sentiment_history[symbol]:
            return None
            
        # Average of recent sentiment
        recent = self.sentiment_history[symbol][-10:]  # Last 10 data points
        return sum(score for _, score in recent) / len(recent)
    
    def get_sentiment_trend(self, symbol: str) -> Optional[str]:
        """
        Get sentiment trend for a symbol.
        
        Args:
            symbol: Symbol
            
        Returns:
            'bullish', 'bearish', 'neutral', or None if not available
        """
        if symbol not in self.sentiment_history or len(self.sentiment_history[symbol]) < 5:
            return None
            
        # Get recent sentiment
        recent = self.sentiment_history[symbol][-5:]
        scores = [score for _, score in recent]
        
        # Calculate trend
        if all(score > 0.2 for score in scores):
            return "bullish"
        elif all(score < -0.2 for score in scores):
            return "bearish"
        else:
            return "neutral"


class MentionTracker:
    """Tracks mentions of symbols and topics."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize mention tracker.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Mention data
        self.symbol_mentions: Dict[str, Dict[datetime, int]] = {}
        self.topic_mentions: Dict[str, Dict[datetime, int]] = {}
        
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        defaults = {
            "time_window_hours": 24,
            "time_bucket_minutes": 15
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def add_symbol_mention(self, symbol: str, timestamp: datetime, count: int = 1):
        """
        Add symbol mention.
        
        Args:
            symbol: Symbol
            timestamp: Mention timestamp
            count: Number of mentions
        """
        if symbol not in self.symbol_mentions:
            self.symbol_mentions[symbol] = {}
            
        # Bucket by time
        bucket = self._get_time_bucket(timestamp)
        
        if bucket in self.symbol_mentions[symbol]:
            self.symbol_mentions[symbol][bucket] += count
        else:
            self.symbol_mentions[symbol][bucket] = count
            
        # Clean up old data
        self._clean_old_data(self.symbol_mentions[symbol], timestamp)
    
    def add_topic_mention(self, topic: str, timestamp: datetime, count: int = 1):
        """
        Add topic mention.
        
        Args:
            topic: Topic
            timestamp: Mention timestamp
            count: Number of mentions
        """
        if topic not in self.topic_mentions:
            self.topic_mentions[topic] = {}
            
        # Bucket by time
        bucket = self._get_time_bucket(timestamp)
        
        if bucket in self.topic_mentions[topic]:
            self.topic_mentions[topic][bucket] += count
        else:
            self.topic_mentions[topic][bucket] = count
            
        # Clean up old data
        self._clean_old_data(self.topic_mentions[topic], timestamp)
    
    def _get_time_bucket(self, timestamp: datetime) -> datetime:
        """
        Get time bucket for a timestamp.
        
        Args:
            timestamp: Timestamp
            
        Returns:
            Bucketed timestamp
        """
        minutes = self.config["time_bucket_minutes"]
        return timestamp.replace(
            minute=(timestamp.minute // minutes) * minutes,
            second=0,
            microsecond=0
        )
    
    def _clean_old_data(self, data: Dict[datetime, int], current_time: datetime):
        """
        Clean up old data.
        
        Args:
            data: Data dictionary
            current_time: Current timestamp
        """
        cutoff = current_time - timedelta(hours=self.config["time_window_hours"])
        
        old_keys = [key for key in data if key < cutoff]
        for key in old_keys:
            del data[key]
    
    def get_symbol_mention_count(self, symbol: str, hours: Optional[int] = None) -> int:
        """
        Get total mentions for a symbol.
        
        Args:
            symbol: Symbol
            hours: Optional time window in hours
            
        Returns:
            Total mentions
        """
        if symbol not in self.symbol_mentions:
            return 0
            
        if hours is None:
            return sum(self.symbol_mentions[symbol].values())
            
        cutoff = datetime.now() - timedelta(hours=hours)
        return sum(count for ts, count in self.symbol_mentions[symbol].items() if ts >= cutoff)
    
    def get_topic_mention_count(self, topic: str, hours: Optional[int] = None) -> int:
        """
        Get total mentions for a topic.
        
        Args:
            topic: Topic
            hours: Optional time window in hours
            
        Returns:
            Total mentions
        """
        if topic not in self.topic_mentions:
            return 0
            
        if hours is None:
            return sum(self.topic_mentions[topic].values())
            
        cutoff = datetime.now() - timedelta(hours=hours)
        return sum(count for ts, count in self.topic_mentions[topic].items() if ts >= cutoff)
    
    def get_top_symbols(self, limit: int = 10, hours: Optional[int] = None) -> List[Tuple[str, int]]:
        """
        Get top mentioned symbols.
        
        Args:
            limit: Maximum number of symbols to return
            hours: Optional time window in hours
            
        Returns:
            List of (symbol, count) tuples
        """
        counts = [
            (symbol, self.get_symbol_mention_count(symbol, hours))
            for symbol in self.symbol_mentions
        ]
        
        # Sort by count (descending)
        counts.sort(key=lambda x: x[1], reverse=True)
        
        return counts[:limit]
    
    def get_top_topics(self, limit: int = 10, hours: Optional[int] = None) -> List[Tuple[str, int]]:
        """
        Get top mentioned topics.
        
        Args:
            limit: Maximum number of topics to return
            hours: Optional time window in hours
            
        Returns:
            List of (topic, count) tuples
        """
        counts = [
            (topic, self.get_topic_mention_count(topic, hours))
            for topic in self.topic_mentions
        ]
        
        # Sort by count (descending)
        counts.sort(key=lambda x: x[1], reverse=True)
        
        return counts[:limit]


class SocialMediaMonitor:
    """
    Social media monitoring system that tracks sentiment, trends,
    and mentions across various platforms.
    """
    
    def __init__(self, 
                 event_monitor: EventMonitor,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize social media monitor.
        
        Args:
            event_monitor: Event monitoring system
            config: Optional configuration dictionary
        """
        self.event_monitor = event_monitor
        self.config = config or {}
        self._init_default_config()
        
        # Initialize components
        self.trend_detector = TrendDetector(self.config.get("trend_detector_config"))
        self.sentiment_analyzer = SentimentAnalyzer()
        self.mention_tracker = MentionTracker(self.config.get("mention_tracker_config"))
        
        # API clients
        self.api_clients: Dict[SocialMediaSource, Any] = {}
        
        # Cache for processed posts
        self.processed_posts: Set[str] = set()
        
        # Enable social media source in event monitor
        self.event_monitor.enable_source(EventSource.SOCIAL_MEDIA_API)
        
        logger.info("SocialMediaMonitor initialized")
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        defaults = {
            "cache_size": 10000,
            "min_event_priority": EventPriority.MEDIUM.value,
            "min_trend_volume": 20,
            "min_influential_followers": 1000,
            "refresh_interval_minutes": 15,
            "symbols_to_track": [],
            "topics_to_track": [],
            "api_request_timeout": 30,
            "max_posts_per_request": 100
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    async def configure_api(self, source: SocialMediaSource, api_key: str, **kwargs):
        """
        Configure API client for a social media source.
        
        Args:
            source: Social media source
            api_key: API key
            **kwargs: Additional configuration parameters
        """
        self.api_clients[source] = {
            "api_key": api_key,
            "base_url": kwargs.get("base_url"),
            "session": None,
            "config": kwargs
        }
        logger.info(f"Configured API client for {source.value}")
    
    async def _get_session(self, source: SocialMediaSource) -> aiohttp.ClientSession:
        """Get or create an aiohttp session for a source."""
        if source not in self.api_clients:
            raise ValueError(f"API client for {source.value} not configured")
            
        client = self.api_clients[source]
        
        if client["session"] is None or client["session"].closed:
            client["session"] = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config["api_request_timeout"])
            )
            
        return client["session"]
    
    def _extract_symbols(self, text: str) -> List[str]:
        """
        Extract stock symbols from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of symbols
        """
        # Match $SYMBOL pattern
        matches = re.findall(r'\$([A-Z]{1,5})', text)
        
        # Add symbols from config if mentioned
        for symbol in self.config["symbols_to_track"]:
            if symbol in text and symbol not in matches:
                matches.append(symbol)
                
        return matches
    
    def _extract_topics(self, text: str) -> List[str]:
        """
        Extract topics from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of topics
        """
        # Match #topic pattern
        matches = re.findall(r'#(\w+)', text)
        
        # Add topics from config if mentioned
        for topic in self.config["topics_to_track"]:
            if topic.lower() in text.lower() and topic not in matches:
                matches.append(topic)
                
        return matches
    
    def _is_influential(self, post: Dict[str, Any]) -> bool:
        """
        Check if a post is from an influential user.
        
        Args:
            post: Post data
            
        Returns:
            True if influential, False otherwise
        """
        # Check followers count
        followers = post.get("user", {}).get("followers_count", 0)
        return followers >= self.config["min_influential_followers"]
    
    async def fetch_posts(self, 
                        source: SocialMediaSource, 
                        query: Optional[str] = None,
                        symbol: Optional[str] = None,
                        limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch posts from a social media source.
        
        Args:
            source: Social media source
            query: Optional search query
            symbol: Optional symbol to search for
            limit: Maximum number of posts to return
            
        Returns:
            List of posts
        """
        if source not in self.api_clients:
            raise ValueError(f"API client for {source.value} not configured")
            
        client = self.api_clients[source]
        session = await self._get_session(source)
        
        # Build request URL and parameters based on the source
        if source == SocialMediaSource.TWITTER:
            url = f"{client['base_url']}/tweets/search/recent"
            params = {
                "query": query or f"${symbol}" if symbol else "",
                "max_results": limit or self.config["max_posts_per_request"],
                "tweet.fields": "created_at,public_metrics",
                "user.fields": "public_metrics",
                "expansions": "author_id"
            }
            headers = {
                "Authorization": f"Bearer {client['api_key']}"
            }
        
        elif source == SocialMediaSource.STOCKTWITS:
            url = f"{client['base_url']}/api/2/streams/symbol/{symbol}" if symbol else f"{client['base_url']}/api/2/streams/trending"
            params = {
                "access_token": client["api_key"],
                "limit": limit or self.config["max_posts_per_request"]
            }
            headers = {}
        
        elif source == SocialMediaSource.REDDIT:
            subreddit = client["config"].get("subreddit", "wallstreetbets")
            url = f"{client['base_url']}/r/{subreddit}/search.json" if query or symbol else f"{client['base_url']}/r/{subreddit}/hot.json"
            params = {
                "q": query or symbol or "",
                "limit": limit or self.config["max_posts_per_request"],
                "sort": "new",
                "t": "day"
            }
            headers = {
                "User-Agent": "EliteTradingBot/1.0"
            }
        
        else:
            pass
        try:
            # Generic handling
            url = client["base_url"]
            params = {
                "api_key": client["api_key"],
                "query": query or symbol or "",
                "limit": limit or self.config["max_posts_per_request"]
            }
            headers = {}
        
            async with session.get(url, params=params, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Parse response based on source
                if source == SocialMediaSource.TWITTER:
                    return self._parse_twitter_response(data)
                elif source == SocialMediaSource.STOCKTWITS:
                    return self._parse_stocktwits_response(data)
                elif source == SocialMediaSource.REDDIT:
                    return self._parse_reddit_response(data)
                else:
                    # Generic handling
                    return data.get("posts", [])
                    
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching posts from {source.value}: {e}")
            return []
    
    def _parse_twitter_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Twitter API response."""
        posts = []
        
        tweets = data.get("data", [])
        users = {user["id"]: user for user in data.get("includes", {}).get("users", [])}
        
        for tweet in tweets:
            author_id = tweet.get("author_id")
            user = users.get(author_id, {})
            
            post = {
                "id": tweet.get("id"),
                "text": tweet.get("text", ""),
                "created_at": tweet.get("created_at"),
                "user": {
                    "id": author_id,
                    "username": user.get("username", ""),
                    "name": user.get("name", ""),
                    "followers_count": user.get("public_metrics", {}).get("followers_count", 0)
                },
                "metrics": {
                    "retweet_count": tweet.get("public_metrics", {}).get("retweet_count", 0),
                    "reply_count": tweet.get("public_metrics", {}).get("reply_count", 0),
                    "like_count": tweet.get("public_metrics", {}).get("like_count", 0),
                    "quote_count": tweet.get("public_metrics", {}).get("quote_count", 0)
                },
                "source": "twitter"
            }
            
            posts.append(post)
            
        return posts
    
    def _parse_stocktwits_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse StockTwits API response."""
        posts = []
        
        messages = data.get("messages", [])
        
        for message in messages:
            post = {
                "id": message.get("id"),
                "text": message.get("body", ""),
                "created_at": message.get("created_at"),
                "user": {
                    "id": message.get("user", {}).get("id"),
                    "username": message.get("user", {}).get("username", ""),
                    "name": message.get("user", {}).get("name", ""),
                    "followers_count": message.get("user", {}).get("followers", 0)
                },
                "symbols": [symbol.get("symbol") for symbol in message.get("symbols", [])],
                "sentiment": message.get("entities", {}).get("sentiment", {}).get("basic", ""),
                "source": "stocktwits"
            }
            
            posts.append(post)
            
        return posts
    
    def _parse_reddit_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Reddit API response."""
        posts = []
        
        children = data.get("data", {}).get("children", [])
        
        for child in children:
            post_data = child.get("data", {})
            
            post = {
                "id": post_data.get("id"),
                "text": post_data.get("selftext", post_data.get("title", "")),
                "title": post_data.get("title", ""),
                "created_at": datetime.fromtimestamp(post_data.get("created_utc", 0)).isoformat(),
                "user": {
                    "id": post_data.get("author_fullname"),
                    "username": post_data.get("author", ""),
                    "name": post_data.get("author", ""),
                    "followers_count": 0  # Reddit API doesn't provide this
                },
                "metrics": {
                    "score": post_data.get("score", 0),
                    "num_comments": post_data.get("num_comments", 0),
                    "upvote_ratio": post_data.get("upvote_ratio", 0)
                },
                "source": "reddit"
            }
            
            posts.append(post)
            
        return posts
    
    async def process_posts(self, 
                          posts: List[Dict[str, Any]], 
                          source: SocialMediaSource) -> SocialMediaAnalysisResult:
        """
        Process social media posts.
        
        Args:
            posts: List of posts
            source: Social media source
            
        Returns:
            Analysis results
        """
        # Skip already processed posts
        new_posts = []
        for post in posts:
            post_id = f"{source.value}:{post['id']}"
            if post_id not in self.processed_posts:
                new_posts.append(post)
                self.processed_posts.add(post_id)
                
                # Limit cache size
                if len(self.processed_posts) > self.config["cache_size"]:
                    self.processed_posts.pop()
        
        if not new_posts:
            logger.debug(f"No new posts to process from {source.value}")
            return SocialMediaAnalysisResult(
                trends=[],
                sentiment_by_symbol={},
                volume_by_symbol={},
                influential_posts=[]
            )
        
        # Extract symbols and topics
        symbol_mentions: Dict[str, List[Dict[str, Any]]] = {}
        topic_mentions: Dict[str, List[Dict[str, Any]]] = {}
        
        for post in new_posts:
            # Extract symbols
            symbols = self._extract_symbols(post["text"])
            for symbol in symbols:
                if symbol not in symbol_mentions:
                    symbol_mentions[symbol] = []
                symbol_mentions[symbol].append(post)
            
            # Extract topics
            topics = self._extract_topics(post["text"])
            for topic in topics:
                if topic not in topic_mentions:
                    topic_mentions[topic] = []
                topic_mentions[topic].append(post)
        
        # Analyze sentiment
        sentiment_by_symbol = {}
        for symbol, posts in symbol_mentions.items():
            sentiment_scores = self.sentiment_analyzer.analyze_posts(posts)
            if sentiment_scores:
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                sentiment_by_symbol[symbol] = avg_sentiment
                
                # Update sentiment history
                self.sentiment_analyzer.update_symbol_sentiment(
                    symbol, avg_sentiment, datetime.now()
                )
        
        # Update mention counts
        now = datetime.now()
        volume_by_symbol = {}
        
        for symbol, posts in symbol_mentions.items():
            count = len(posts)
            volume_by_symbol[symbol] = count
            self.mention_tracker.add_symbol_mention(symbol, now, count)
        
        for topic, posts in topic_mentions.items():
            self.mention_tracker.add_topic_mention(topic, now, len(posts))
        
        # Update trends
        for topic, posts in topic_mentions.items():
            if len(posts) >= self.config["min_trend_volume"]:
                # Calculate sentiment
                sentiment_scores = self.sentiment_analyzer.analyze_posts(posts)
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
                
                # Get related symbols
                related_symbols = set()
                for post in posts:
                    symbols = self._extract_symbols(post["text"])
                    related_symbols.update(symbols)
                
                # Update trend
                self.trend_detector.update_topic_data(
                    topic=topic,
                    source=source,
                    volume=len(posts),
                    sentiment_score=avg_sentiment,
                    timestamp=now,
                    related_symbols=list(related_symbols),
                    sample_posts=posts
                )
        
        # Find influential posts
        influential_posts = [post for post in new_posts if self._is_influential(post)]
        
        # Generate events for significant trends
        active_trends = self.trend_detector.get_active_trends()
        for trend in active_trends:
            # Only generate events for significant trends
            if trend.volume >= self.config["min_trend_volume"] * 2:
                await self._generate_trend_event(trend)
        
        # Generate events for significant sentiment changes
        for symbol, sentiment in sentiment_by_symbol.items():
            prev_sentiment = self.sentiment_analyzer.get_symbol_sentiment(symbol)
            if prev_sentiment is not None:
                sentiment_change = sentiment - prev_sentiment
                if abs(sentiment_change) >= 0.5:  # Significant change
                    await self._generate_sentiment_event(symbol, sentiment, sentiment_change)
        
        # Return analysis results
        return SocialMediaAnalysisResult(
            trends=active_trends,
            sentiment_by_symbol=sentiment_by_symbol,
            volume_by_symbol=volume_by_symbol,
            influential_posts=influential_posts
        )
    
    async def _generate_trend_event(self, trend: SocialMediaTrend):
        """Generate event for a significant trend."""
        event_id = f"trend_{trend.source.value}_{trend.topic}_{int(datetime.now().timestamp())}"
        
        # Determine direction
        if trend.is_growing:
            direction = "growing"
        else:
            direction = "fading"
        
        # Determine priority based on volume and momentum
        if trend.volume >= self.config["min_trend_volume"] * 5:
            priority = EventPriority.HIGH
        elif trend.volume >= self.config["min_trend_volume"] * 2:
            priority = EventPriority.MEDIUM
        else:
            priority = EventPriority.LOW
            
        # Skip if below minimum priority
        if priority.value < EventPriority[self.config["min_event_priority"]].value:
            return
        
        # Create event
        event = SocialMediaEvent(
            id=event_id,
            type=EventType.SOCIAL_MEDIA,
            priority=priority,
            source=EventSource.SOCIAL_MEDIA_API,
            timestamp=datetime.now(),
            description=f"Trending topic on {trend.source.value}: {trend.topic} ({direction})",
            platform=trend.source.value,
            topic=trend.topic,
            sentiment_score=trend.sentiment_score,
            volume=trend.volume,
            trend_direction=direction,
            related_symbols=trend.related_symbols,
            sample_posts=trend.sample_posts
        )
        
        await self.event_monitor.add_event(event)
    
    async def _generate_sentiment_event(self, symbol: str, sentiment: float, change: float):
        """Generate event for a significant sentiment change."""
        event_id = f"sentiment_{symbol}_{int(datetime.now().timestamp())}"
        
        # Determine direction
        if change > 0:
            direction = "bullish"
        else:
            direction = "bearish"
        
        # Determine priority based on magnitude of change
        if abs(change) >= 0.8:
            priority = EventPriority.HIGH
        elif abs(change) >= 0.5:
            priority = EventPriority.MEDIUM
        else:
            priority = EventPriority.LOW
            
        # Skip if below minimum priority
        if priority.value < EventPriority[self.config["min_event_priority"]].value:
            return
        
        # Create event
        event = SocialMediaEvent(
            id=event_id,
            type=EventType.SOCIAL_MEDIA,
            priority=priority,
            source=EventSource.SOCIAL_MEDIA_API,
            timestamp=datetime.now(),
            description=f"Significant {direction} sentiment shift for {symbol}",
            platform="multiple",
            topic=symbol,
            sentiment_score=sentiment,
            volume=self.mention_tracker.get_symbol_mention_count(symbol, 1),  # Last hour
            trend_direction=direction,
            related_symbols=[symbol]
        )
        
        await self.event_monitor.add_event(event)
    
    async def fetch_and_process(self, source: SocialMediaSource, query: Optional[str] = None) -> SocialMediaAnalysisResult:
        """
        Fetch and process posts from a social media source.
        
        Args:
            source: Social media source
            query: Optional search query
            
        Returns:
            Analysis results
        """
        posts = await self.fetch_posts(source, query)
        return await self.process_posts(posts, source)
    
    async def monitor_symbols(self, symbols: List[str], sources: List[SocialMediaSource]) -> Dict[str, SocialMediaAnalysisResult]:
        """
        Monitor social media for specific symbols.
        
        Args:
            symbols: List of symbols to monitor
            sources: List of sources to monitor
            
        Returns:
            Dictionary of symbol -> analysis results
        """
        results = {}
        
        for symbol in symbols:
            symbol_results = []
            
            for source in sources:
                if source in self.api_clients:
                    posts = await self.fetch_posts(source, symbol=symbol)
                    result = await self.process_posts(posts, source)
                    symbol_results.append(result)
            
            # Combine results
            if symbol_results:
                combined = SocialMediaAnalysisResult(
                    trends=[],
                    sentiment_by_symbol={},
                    volume_by_symbol={},
                    influential_posts=[]
                )
                
                for result in symbol_results:
                    combined.trends.extend(result.trends)
                    combined.sentiment_by_symbol.update(result.sentiment_by_symbol)
                    combined.volume_by_symbol.update(result.volume_by_symbol)
                    combined.influential_posts.extend(result.influential_posts)
                
                results[symbol] = combined
        
        return results
    
    def get_symbol_sentiment(self, symbol: str) -> Optional[float]:
        """
        Get current sentiment for a symbol.
        
        Args:
            symbol: Symbol
            
        Returns:
            Current sentiment score or None if not available
        """
        return self.sentiment_analyzer.get_symbol_sentiment(symbol)
    
    def get_symbol_sentiment_trend(self, symbol: str) -> Optional[str]:
        """
        Get sentiment trend for a symbol.
        
        Args:
            symbol: Symbol
            
        Returns:
            'bullish', 'bearish', 'neutral', or None if not available
        """
        return self.sentiment_analyzer.get_sentiment_trend(symbol)
    
    def get_top_symbols(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get top mentioned symbols.
        
        Args:
            limit: Maximum number of symbols to return
            
        Returns:
            List of (symbol, count) tuples
        """
        return self.mention_tracker.get_top_symbols(limit)
    
    def get_active_trends(self) -> List[SocialMediaTrend]:
        """
        Get list of active trends.
        
        Returns:
            List of active trends
        """
        return self.trend_detector.get_active_trends()
    
    async def start_auto_refresh(self, interval_minutes: Optional[int] = None):
        """
        Start automatic refresh of social media data.
        
        Args:
            interval_minutes: Optional refresh interval in minutes
        """
        interval = interval_minutes or self.config["refresh_interval_minutes"]
        
        async def refresh_loop():
            logger.info(f"Starting social media auto-refresh every {interval} minutes")
            while True:
                try:
                    # Monitor configured symbols
                    symbols = self.config["symbols_to_track"]
                    sources = list(self.api_clients.keys())
                    
                    if symbols and sources:
                        await self.monitor_symbols(symbols, sources)
                    
                except Exception as e:
                    logger.error(f"Error in social media refresh: {e}")
                
                await asyncio.sleep(interval * 60)
        
        # Start refresh loop
        asyncio.create_task(refresh_loop())
    
    async def close(self):
        """Close all API client sessions."""
        for source, client in self.api_clients.items():
            if client["session"] and not client["session"].closed:
                await client["session"].close()
                
        logger.info("Closed all SocialMediaMonitor API sessions")
