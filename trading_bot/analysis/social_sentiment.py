"""
Social Sentiment Aggregator

Aggregates sentiment from multiple social media sources:
- Twitter/X sentiment analysis
- Reddit (wallstreetbets, stocks, investing)
- StockTwits
- Discord trading servers
- Telegram channels
- News sentiment
- Fear & Greed indicators
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import statistics
import re
import json

logger = logging.getLogger(__name__)


class SentimentSource(Enum):
    """Social sentiment sources."""
    TWITTER = "twitter"
    REDDIT = "reddit"
    STOCKTWITS = "stocktwits"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    NEWS = "news"
    FINTWIT = "fintwit"


class SentimentLevel(Enum):
    """Sentiment levels."""
    EXTREME_FEAR = -2
    FEAR = -1
    NEUTRAL = 0
    GREED = 1
    EXTREME_GREED = 2


class MentionType(Enum):
    """Types of social mentions."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    QUESTION = "question"
    NEWS = "news"


@dataclass
class SocialMention:
    """Single social media mention."""
    timestamp: datetime
    source: SentimentSource
    platform_id: str
    author: str
    content: str
    symbol: str
    sentiment_score: float  # -1.0 to 1.0
    mention_type: MentionType
    engagement: int  # likes, retweets, upvotes
    reach: int  # followers, subscribers
    url: Optional[str] = None
    
    @property
    def weighted_sentiment(self) -> float:
        """Sentiment weighted by engagement and reach."""
        weight = 1.0 + (self.engagement / 1000) + (self.reach / 10000)
        return self.sentiment_score * min(weight, 5.0)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'source': self.source.value,
            'author': self.author,
            'content': self.content[:200],
            'symbol': self.symbol,
            'sentiment_score': self.sentiment_score,
            'mention_type': self.mention_type.value,
            'engagement': self.engagement,
            'reach': self.reach
        }


@dataclass
class SentimentMetrics:
    """Aggregated sentiment metrics for a symbol."""
    symbol: str
    timestamp: datetime
    overall_sentiment: float  # -1.0 to 1.0
    sentiment_level: SentimentLevel
    mention_count: int
    bullish_count: int
    bearish_count: int
    neutral_count: int
    total_engagement: int
    total_reach: int
    sentiment_by_source: Dict[str, float]
    trending_score: float  # 0 to 100
    sentiment_change_1h: float
    sentiment_change_24h: float
    key_influencers: List[str]
    top_mentions: List[SocialMention]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'overall_sentiment': self.overall_sentiment,
            'sentiment_level': self.sentiment_level.name,
            'mention_count': self.mention_count,
            'bullish_count': self.bullish_count,
            'bearish_count': self.bearish_count,
            'neutral_count': self.neutral_count,
            'total_engagement': self.total_engagement,
            'trending_score': self.trending_score,
            'sentiment_change_1h': self.sentiment_change_1h,
            'sentiment_change_24h': self.sentiment_change_24h,
            'sentiment_by_source': self.sentiment_by_source
        }


@dataclass
class FearGreedIndex:
    """Fear & Greed Index reading."""
    timestamp: datetime
    value: int  # 0-100
    level: SentimentLevel
    components: Dict[str, float]
    previous_close: int
    week_ago: int
    month_ago: int
    year_ago: int
    
    @property
    def change_1d(self) -> int:
        return self.value - self.previous_close
    
    @property
    def change_1w(self) -> int:
        return self.value - self.week_ago
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'level': self.level.name,
            'components': self.components,
            'change_1d': self.change_1d,
            'change_1w': self.change_1w
        }


@dataclass
class SocialSignal:
    """Social sentiment trading signal."""
    symbol: str
    signal_type: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    confidence: float
    sentiment_score: float
    mention_velocity: float  # mentions per hour
    engagement_velocity: float
    contrarian_signal: bool  # Extreme sentiment often reverses
    smart_money_alignment: bool  # Influencers agree with retail
    analysis: str
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'signal_type': self.signal_type,
            'confidence': self.confidence,
            'sentiment_score': self.sentiment_score,
            'mention_velocity': self.mention_velocity,
            'engagement_velocity': self.engagement_velocity,
            'contrarian_signal': self.contrarian_signal,
            'smart_money_alignment': self.smart_money_alignment,
            'analysis': self.analysis,
            'generated_at': self.generated_at.isoformat()
        }


# Bullish/Bearish keywords for simple sentiment analysis
BULLISH_KEYWORDS = {
    'buy', 'long', 'calls', 'moon', 'rocket', 'bullish', 'breakout',
    'squeeze', 'undervalued', 'accumulate', 'strong', 'growth',
    'upgrade', 'beat', 'outperform', 'rally', 'surge', 'soar',
    '🚀', '📈', '💎', '🙌', '💪', '🔥'
}

BEARISH_KEYWORDS = {
    'sell', 'short', 'puts', 'crash', 'dump', 'bearish', 'breakdown',
    'overvalued', 'distribute', 'weak', 'decline', 'downgrade',
    'miss', 'underperform', 'drop', 'plunge', 'tank', 'fade',
    '📉', '🐻', '💀', '⚠️', '🔻'
}

# Known influencers (simplified - would be more comprehensive in production)
KNOWN_INFLUENCERS = {
    'twitter': ['elonmusk', 'jimcramer', 'chaikinadvisor', 'unusual_whales'],
    'reddit': ['deepfuckingvalue', 'wallstreetbets_mod'],
    'stocktwits': ['traderstewie', 'stockdweebs']
}


class SimpleSentimentAnalyzer:
    """
    Simple keyword-based sentiment analyzer.
    In production, would use NLP models like FinBERT.
    """
    
    def __init__(self):
        self.bullish = BULLISH_KEYWORDS
        self.bearish = BEARISH_KEYWORDS
    
    def analyze(self, text: str) -> Tuple[float, MentionType]:
        """
        Analyze text sentiment.
        
        Returns:
            Tuple of (sentiment_score, mention_type)
        """
        text_lower = text.lower()
        
        bullish_count = sum(1 for word in self.bullish if word in text_lower)
        bearish_count = sum(1 for word in self.bearish if word in text_lower)
        
        total = bullish_count + bearish_count
        
        if total == 0:
            # Check for question marks
            if '?' in text:
                return 0.0, MentionType.QUESTION
            return 0.0, MentionType.NEUTRAL
        
        sentiment = (bullish_count - bearish_count) / total
        
        if sentiment > 0.3:
            return sentiment, MentionType.BULLISH
        elif sentiment < -0.3:
            return sentiment, MentionType.BEARISH
        else:
            return sentiment, MentionType.NEUTRAL
    
    def extract_tickers(self, text: str) -> List[str]:
        """Extract stock tickers from text."""
        # Match $TICKER or standalone uppercase 1-5 letter words
        cashtags = re.findall(r'\$([A-Z]{1,5})\b', text)
        
        # Common false positives to filter
        false_positives = {'I', 'A', 'THE', 'AND', 'FOR', 'TO', 'IN', 'IS', 'IT', 'ON'}
        
        return [t for t in cashtags if t not in false_positives]


class RedditSentimentFetcher:
    """
    Fetches sentiment from Reddit.
    Uses Reddit API or scraping.
    """
    
    SUBREDDITS = ['wallstreetbets', 'stocks', 'investing', 'options', 'stockmarket']
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.analyzer = SimpleSentimentAnalyzer()
    
    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={'User-Agent': 'TradingBot/1.0'}
            )
    
    async def fetch_mentions(self, symbol: str, hours: int = 24) -> List[SocialMention]:
        """
        Fetch Reddit mentions for a symbol.
        
        Note: In production, would use Reddit API with proper auth.
        This is a simplified implementation.
        """
        mentions = []
        
        # Simulated data - in production would fetch from Reddit API
        # This demonstrates the structure
        
        return mentions
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()


class StockTwitsFetcher:
    """
    Fetches sentiment from StockTwits.
    """
    
    BASE_URL = "https://api.stocktwits.com/api/2"
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.analyzer = SimpleSentimentAnalyzer()
    
    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def fetch_mentions(self, symbol: str) -> List[SocialMention]:
        """
        Fetch StockTwits mentions for a symbol.
        """
        await self._ensure_session()
        
        mentions = []
        
        try:
            url = f"{self.BASE_URL}/streams/symbol/{symbol}.json"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for message in data.get('messages', []):
                        # Parse StockTwits sentiment
                        st_sentiment = message.get('entities', {}).get('sentiment', {})
                        
                        if st_sentiment.get('basic') == 'Bullish':
                            sentiment_score = 0.7
                            mention_type = MentionType.BULLISH
                        elif st_sentiment.get('basic') == 'Bearish':
                            sentiment_score = -0.7
                            mention_type = MentionType.BEARISH
                        else:
                            # Use our analyzer
                            sentiment_score, mention_type = self.analyzer.analyze(message.get('body', ''))
                        
                        mention = SocialMention(
                            timestamp=datetime.fromisoformat(message.get('created_at', '').replace('Z', '+00:00')),
                            source=SentimentSource.STOCKTWITS,
                            platform_id=str(message.get('id', '')),
                            author=message.get('user', {}).get('username', ''),
                            content=message.get('body', ''),
                            symbol=symbol,
                            sentiment_score=sentiment_score,
                            mention_type=mention_type,
                            engagement=message.get('likes', {}).get('total', 0),
                            reach=message.get('user', {}).get('followers', 0)
                        )
                        mentions.append(mention)
        except Exception as e:
            logger.warning(f"StockTwits fetch failed: {e}")
        
        return mentions
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()


class SocialSentimentAggregator:
    """
    Aggregates sentiment from multiple social sources.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Fetchers
        self.reddit_fetcher = RedditSentimentFetcher(config)
        self.stocktwits_fetcher = StockTwitsFetcher(config)
        self.analyzer = SimpleSentimentAnalyzer()
        
        # Storage
        self.mentions: Dict[str, List[SocialMention]] = defaultdict(list)
        self.sentiment_history: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        
        # Fear & Greed
        self.fear_greed: Optional[FearGreedIndex] = None
        
        logger.info("SocialSentimentAggregator initialized")
    
    def add_mention(self, mention: SocialMention):
        """Add a social mention."""
        self.mentions[mention.symbol].append(mention)
        
        # Update sentiment history
        self.sentiment_history[mention.symbol].append(
            (mention.timestamp, mention.sentiment_score)
        )
        
        # Cleanup old data
        self._cleanup_old_data(mention.symbol)
    
    def _cleanup_old_data(self, symbol: str, max_age_hours: int = 48):
        """Remove old mentions."""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        self.mentions[symbol] = [
            m for m in self.mentions[symbol] if m.timestamp >= cutoff
        ]
        self.sentiment_history[symbol] = [
            (t, s) for t, s in self.sentiment_history[symbol] if t >= cutoff
        ]
    
    async def fetch_all_sources(self, symbol: str) -> List[SocialMention]:
        """
        Fetch mentions from all sources.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            List of SocialMention objects
        """
        all_mentions = []
        
        # Fetch from each source
        tasks = [
            self.reddit_fetcher.fetch_mentions(symbol),
            self.stocktwits_fetcher.fetch_mentions(symbol),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_mentions.extend(result)
            elif isinstance(result, Exception):
                logger.warning(f"Fetch failed: {result}")
        
        # Add to storage
        for mention in all_mentions:
            self.add_mention(mention)
        
        return all_mentions
    
    def calculate_metrics(self, symbol: str) -> SentimentMetrics:
        """
        Calculate sentiment metrics for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            SentimentMetrics with aggregated data
        """
        mentions = self.mentions.get(symbol, [])
        
        if not mentions:
            return SentimentMetrics(
                symbol=symbol,
                timestamp=datetime.now(),
                overall_sentiment=0.0,
                sentiment_level=SentimentLevel.NEUTRAL,
                mention_count=0,
                bullish_count=0,
                bearish_count=0,
                neutral_count=0,
                total_engagement=0,
                total_reach=0,
                sentiment_by_source={},
                trending_score=0.0,
                sentiment_change_1h=0.0,
                sentiment_change_24h=0.0,
                key_influencers=[],
                top_mentions=[]
            )
        
        # Count by type
        bullish = [m for m in mentions if m.mention_type == MentionType.BULLISH]
        bearish = [m for m in mentions if m.mention_type == MentionType.BEARISH]
        neutral = [m for m in mentions if m.mention_type == MentionType.NEUTRAL]
        
        # Calculate weighted sentiment
        total_weight = sum(m.engagement + 1 for m in mentions)
        weighted_sentiment = sum(m.sentiment_score * (m.engagement + 1) for m in mentions) / total_weight
        
        # Sentiment by source
        sentiment_by_source = {}
        for source in SentimentSource:
            source_mentions = [m for m in mentions if m.source == source]
            if source_mentions:
                sentiment_by_source[source.value] = statistics.mean(
                    m.sentiment_score for m in source_mentions
                )
        
        # Calculate sentiment changes
        sentiment_change_1h = self._calculate_sentiment_change(symbol, hours=1)
        sentiment_change_24h = self._calculate_sentiment_change(symbol, hours=24)
        
        # Trending score (based on mention velocity)
        recent_mentions = [m for m in mentions if m.timestamp >= datetime.now() - timedelta(hours=1)]
        trending_score = min(100, len(recent_mentions) * 10)
        
        # Key influencers
        key_influencers = self._identify_influencers(mentions)
        
        # Top mentions by engagement
        top_mentions = sorted(mentions, key=lambda x: x.engagement, reverse=True)[:5]
        
        # Determine sentiment level
        sentiment_level = self._score_to_level(weighted_sentiment)
        
        return SentimentMetrics(
            symbol=symbol,
            timestamp=datetime.now(),
            overall_sentiment=weighted_sentiment,
            sentiment_level=sentiment_level,
            mention_count=len(mentions),
            bullish_count=len(bullish),
            bearish_count=len(bearish),
            neutral_count=len(neutral),
            total_engagement=sum(m.engagement for m in mentions),
            total_reach=sum(m.reach for m in mentions),
            sentiment_by_source=sentiment_by_source,
            trending_score=trending_score,
            sentiment_change_1h=sentiment_change_1h,
            sentiment_change_24h=sentiment_change_24h,
            key_influencers=key_influencers,
            top_mentions=top_mentions
        )
    
    def _calculate_sentiment_change(self, symbol: str, hours: int) -> float:
        """Calculate sentiment change over time period."""
        history = self.sentiment_history.get(symbol, [])
        
        if len(history) < 2:
            return 0.0
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent = [s for t, s in history if t >= cutoff]
        older = [s for t, s in history if t < cutoff]
        
        if not recent or not older:
            return 0.0
        
        return statistics.mean(recent) - statistics.mean(older)
    
    def _identify_influencers(self, mentions: List[SocialMention]) -> List[str]:
        """Identify key influencers from mentions."""
        influencers = []
        
        for mention in mentions:
            source_key = mention.source.value
            if source_key in KNOWN_INFLUENCERS:
                if mention.author.lower() in [i.lower() for i in KNOWN_INFLUENCERS[source_key]]:
                    influencers.append(mention.author)
            
            # High reach authors
            if mention.reach > 100000:
                influencers.append(mention.author)
        
        return list(set(influencers))[:5]
    
    def _score_to_level(self, score: float) -> SentimentLevel:
        """Convert sentiment score to level."""
        if score > 0.5:
            return SentimentLevel.EXTREME_GREED
        elif score > 0.2:
            return SentimentLevel.GREED
        elif score > -0.2:
            return SentimentLevel.NEUTRAL
        elif score > -0.5:
            return SentimentLevel.FEAR
        else:
            return SentimentLevel.EXTREME_FEAR
    
    def generate_signal(self, symbol: str) -> SocialSignal:
        """
        Generate trading signal from social sentiment.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            SocialSignal with analysis
        """
        metrics = self.calculate_metrics(symbol)
        
        # Calculate velocities
        recent_mentions = [
            m for m in self.mentions.get(symbol, [])
            if m.timestamp >= datetime.now() - timedelta(hours=1)
        ]
        mention_velocity = len(recent_mentions)
        engagement_velocity = sum(m.engagement for m in recent_mentions)
        
        # Check for contrarian signal (extreme sentiment often reverses)
        contrarian_signal = metrics.sentiment_level in [
            SentimentLevel.EXTREME_FEAR, SentimentLevel.EXTREME_GREED
        ]
        
        # Check smart money alignment
        influencer_mentions = [
            m for m in self.mentions.get(symbol, [])
            if m.author in metrics.key_influencers
        ]
        if influencer_mentions:
            influencer_sentiment = statistics.mean(m.sentiment_score for m in influencer_mentions)
            smart_money_alignment = (
                (influencer_sentiment > 0 and metrics.overall_sentiment > 0) or
                (influencer_sentiment < 0 and metrics.overall_sentiment < 0)
            )
        else:
            smart_money_alignment = True  # No conflict
        
        # Determine signal
        signal_type, confidence = self._determine_signal(
            metrics, mention_velocity, contrarian_signal, smart_money_alignment
        )
        
        # Generate analysis
        analysis = self._generate_analysis(
            metrics, mention_velocity, contrarian_signal, smart_money_alignment
        )
        
        return SocialSignal(
            symbol=symbol,
            signal_type=signal_type,
            confidence=confidence,
            sentiment_score=metrics.overall_sentiment,
            mention_velocity=mention_velocity,
            engagement_velocity=engagement_velocity,
            contrarian_signal=contrarian_signal,
            smart_money_alignment=smart_money_alignment,
            analysis=analysis
        )
    
    def _determine_signal(
        self,
        metrics: SentimentMetrics,
        velocity: float,
        contrarian: bool,
        smart_money: bool
    ) -> Tuple[str, float]:
        """Determine signal type and confidence."""
        confidence = 0.5
        
        # Base signal from sentiment
        if metrics.overall_sentiment > 0.3:
            signal_type = 'BULLISH'
            confidence = 0.5 + metrics.overall_sentiment * 0.3
        elif metrics.overall_sentiment < -0.3:
            signal_type = 'BEARISH'
            confidence = 0.5 + abs(metrics.overall_sentiment) * 0.3
        else:
            signal_type = 'NEUTRAL'
            confidence = 0.5
        
        # Contrarian adjustment
        if contrarian:
            # Extreme sentiment often reverses
            if signal_type == 'BULLISH':
                signal_type = 'BEARISH'  # Contrarian
            elif signal_type == 'BEARISH':
                signal_type = 'BULLISH'  # Contrarian
            confidence *= 0.8  # Lower confidence for contrarian
        
        # Smart money adjustment
        if not smart_money:
            confidence *= 0.7  # Lower confidence if influencers disagree
        
        # Velocity adjustment
        if velocity > 50:
            confidence = min(1.0, confidence + 0.1)
        
        return signal_type, min(1.0, confidence)
    
    def _generate_analysis(
        self,
        metrics: SentimentMetrics,
        velocity: float,
        contrarian: bool,
        smart_money: bool
    ) -> str:
        """Generate analysis text."""
        parts = []
        
        # Sentiment
        parts.append(f"Sentiment: {metrics.overall_sentiment:+.2f} ({metrics.sentiment_level.name})")
        
        # Mentions
        parts.append(f"Mentions: {metrics.mention_count} (B:{metrics.bullish_count}/Be:{metrics.bearish_count})")
        
        # Velocity
        if velocity > 50:
            parts.append("HIGH velocity")
        elif velocity > 20:
            parts.append("Moderate velocity")
        
        # Contrarian
        if contrarian:
            parts.append("⚠️ CONTRARIAN signal (extreme sentiment)")
        
        # Smart money
        if not smart_money:
            parts.append("⚠️ Influencers diverge from retail")
        
        # Trending
        if metrics.trending_score > 50:
            parts.append(f"TRENDING ({metrics.trending_score:.0f})")
        
        return " | ".join(parts)
    
    def update_fear_greed(self, value: int, components: Dict[str, float]):
        """Update Fear & Greed Index."""
        level = self._score_to_level((value - 50) / 50)  # Convert 0-100 to -1 to 1
        
        self.fear_greed = FearGreedIndex(
            timestamp=datetime.now(),
            value=value,
            level=level,
            components=components,
            previous_close=self.fear_greed.value if self.fear_greed else value,
            week_ago=value,  # Would track historically
            month_ago=value,
            year_ago=value
        )
    
    def get_fear_greed(self) -> Optional[FearGreedIndex]:
        """Get current Fear & Greed Index."""
        return self.fear_greed
    
    def get_status(self) -> Dict[str, Any]:
        """Get aggregator status."""
        return {
            'symbols_tracked': len(self.mentions),
            'total_mentions': sum(len(m) for m in self.mentions.values()),
            'fear_greed': self.fear_greed.to_dict() if self.fear_greed else None,
            'timestamp': datetime.now().isoformat()
        }
    
    async def close(self):
        """Close all fetchers."""
        await self.reddit_fetcher.close()
        await self.stocktwits_fetcher.close()


# Factory function
def create_sentiment_aggregator(config: Optional[Dict] = None) -> SocialSentimentAggregator:
    """Create SocialSentimentAggregator instance."""
    return SocialSentimentAggregator(config)


# Example usage
if __name__ == "__main__":
    import random
    
    aggregator = create_sentiment_aggregator()
    
    # Simulate some mentions
    symbol = "AAPL"
    
    for i in range(30):
        # Random sentiment
        if random.random() > 0.6:
            sentiment = random.uniform(0.3, 0.9)
            mention_type = MentionType.BULLISH
            content = f"$AAPL looking strong! 🚀 Buy the dip! #{i}"
        elif random.random() > 0.3:
            sentiment = random.uniform(-0.9, -0.3)
            mention_type = MentionType.BEARISH
            content = f"$AAPL overvalued, time to sell 📉 #{i}"
        else:
            sentiment = random.uniform(-0.2, 0.2)
            mention_type = MentionType.NEUTRAL
            content = f"Watching $AAPL today #{i}"
        
        mention = SocialMention(
            timestamp=datetime.now() - timedelta(minutes=random.randint(0, 120)),
            source=random.choice(list(SentimentSource)),
            platform_id=f"id_{i}",
            author=f"user_{i}",
            content=content,
            symbol=symbol,
            sentiment_score=sentiment,
            mention_type=mention_type,
            engagement=random.randint(0, 1000),
            reach=random.randint(100, 50000)
        )
        
        aggregator.add_mention(mention)
    
    # Update Fear & Greed
    aggregator.update_fear_greed(65, {
        'market_momentum': 0.7,
        'stock_price_strength': 0.6,
        'stock_price_breadth': 0.65,
        'put_call_ratio': 0.55,
        'market_volatility': 0.7,
        'safe_haven_demand': 0.6,
        'junk_bond_demand': 0.65
    })
    
    # Calculate metrics
    metrics = aggregator.calculate_metrics(symbol)
    
    print("=" * 60)
    print("SOCIAL SENTIMENT ANALYSIS")
    print("=" * 60)
    print(f"\nSymbol: {metrics.symbol}")
    print(f"Overall Sentiment: {metrics.overall_sentiment:+.2f}")
    print(f"Sentiment Level: {metrics.sentiment_level.name}")
    print(f"\nMention Count: {metrics.mention_count}")
    print(f"  Bullish: {metrics.bullish_count}")
    print(f"  Bearish: {metrics.bearish_count}")
    print(f"  Neutral: {metrics.neutral_count}")
    print(f"\nTotal Engagement: {metrics.total_engagement:,}")
    print(f"Trending Score: {metrics.trending_score:.0f}")
    print(f"Sentiment Change (1h): {metrics.sentiment_change_1h:+.2f}")
    print(f"Sentiment Change (24h): {metrics.sentiment_change_24h:+.2f}")
    
    print(f"\nSentiment by Source:")
    for source, sent in metrics.sentiment_by_source.items():
        print(f"  {source}: {sent:+.2f}")
    
    # Generate signal
    signal = aggregator.generate_signal(symbol)
    
    print("\n" + "=" * 60)
    print("TRADING SIGNAL")
    print("=" * 60)
    print(f"\nSignal: {signal.signal_type}")
    print(f"Confidence: {signal.confidence:.1%}")
    print(f"Contrarian: {signal.contrarian_signal}")
    print(f"Smart Money Aligned: {signal.smart_money_alignment}")
    print(f"\nAnalysis: {signal.analysis}")
    
    # Fear & Greed
    fg = aggregator.get_fear_greed()
    if fg:
        print("\n" + "=" * 60)
        print("FEAR & GREED INDEX")
        print("=" * 60)
        print(f"\nValue: {fg.value}")
        print(f"Level: {fg.level.name}")
        print(f"Change (1d): {fg.change_1d:+d}")
