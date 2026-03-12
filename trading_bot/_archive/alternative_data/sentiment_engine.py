"""
Real-Time Market Sentiment Engine ($0 Budget)
Free Reddit/Twitter API integration
NLP-powered sentiment scoring
"""

import re
import json
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import Counter
import numpy as np
import numpy

import logging
logger = logging.getLogger(__name__)



@dataclass
class SentimentScore:
    """Sentiment score result"""
    text: str
    score: float  # -1 to 1
    magnitude: float  # 0 to 1
    label: str  # 'positive', 'negative', 'neutral'
    keywords: List[str]
    timestamp: datetime


class FreeSentimentAnalyzer:
    """Free sentiment analyzer using lexicon-based approach"""
    
    def __init__(self):
        # Free sentiment lexicon (simplified VADER-style)
        self.positive_words = {
            'bullish', 'moon', 'rocket', 'gain', 'profit', 'buy', 'long', 'up',
            'surge', 'rally', 'breakout', 'strong', 'growth', 'winning', 'success',
            'excellent', 'great', 'amazing', 'awesome', 'fantastic', 'good', 'best',
            'high', 'rise', 'pump', 'boom', 'soar', 'jump', 'climb', 'bull'
        }
        
        self.negative_words = {
            'bearish', 'crash', 'dump', 'loss', 'sell', 'short', 'down', 'drop',
            'fall', 'decline', 'weak', 'bad', 'terrible', 'awful', 'worst', 'poor',
            'low', 'plunge', 'tank', 'collapse', 'fail', 'bear', 'risk', 'danger',
            'warning', 'concern', 'worry', 'fear', 'panic', 'disaster'
        }
        
        # Intensifiers
        self.intensifiers = {
            'very': 1.5, 'extremely': 2.0, 'super': 1.8, 'really': 1.3,
            'absolutely': 2.0, 'completely': 1.8, 'totally': 1.7
        }
        
        # Negations
        self.negations = {'not', 'no', 'never', 'none', 'nobody', 'nothing', 'neither', 'nowhere', 'hardly'}
        
    def analyze(self, text: str) -> SentimentScore:
        """Analyze sentiment of text"""
        
        # Preprocess
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        # Calculate sentiment
        score = 0
        magnitude = 0
        keywords = []
        
        for i, word in enumerate(words):
            # Check for negation
            is_negated = i > 0 and words[i-1] in self.negations
            
            # Check for intensifier
            intensifier = 1.0
            if i > 0 and words[i-1] in self.intensifiers:
                intensifier = self.intensifiers[words[i-1]]
            
            # Calculate word sentiment
            if word in self.positive_words:
                word_score = 1.0 * intensifier
                if is_negated:
                    word_score *= -0.5
                score += word_score
                magnitude += abs(word_score)
                keywords.append(word)
            
            elif word in self.negative_words:
                word_score = -1.0 * intensifier
                if is_negated:
                    word_score *= -0.5
                score += word_score
                magnitude += abs(word_score)
                keywords.append(word)
        
        # Normalize
        if len(words) > 0:
            score = score / len(words)
            magnitude = magnitude / len(words)
        
        # Clip to [-1, 1]
        score = np.clip(score, -1, 1)
        magnitude = np.clip(magnitude, 0, 1)
        
        # Label
        if score > 0.05:
            label = 'positive'
        elif score < -0.05:
            label = 'negative'
        else:
            label = 'neutral'
        
        return SentimentScore(
            text=text,
            score=score,
            magnitude=magnitude,
            label=label,
            keywords=keywords,
            timestamp=datetime.now()
        )


class FreeRedditScraper:
    """Free Reddit scraper (no API key needed for public data)"""
    
    def __init__(self):
        self.base_url = "https://www.reddit.com"
        
    def get_posts(self, subreddit: str, limit: int = 25) -> List[Dict]:
        """Get recent posts from subreddit (simulated)"""
        
        # In production, use requests library to scrape public JSON
        # Example: requests.get(f"{self.base_url}/r/{subreddit}.json")
        
        # Simulated data for demo
        mock_posts = [
            {
                'title': 'Bitcoin looking bullish! Strong breakout above resistance',
                'text': 'The chart is showing a clear bullish pattern. Great time to buy!',
                'score': 150,
                'comments': 45,
                'created': datetime.now() - timedelta(hours=2)
            },
            {
                'title': 'Market crash incoming? Warning signs everywhere',
                'text': 'Seeing bearish signals across the board. Time to sell?',
                'score': 89,
                'comments': 67,
                'created': datetime.now() - timedelta(hours=5)
            },
            {
                'title': 'ETH to the moon! 🚀',
                'text': 'Ethereum is pumping hard. This rally is just getting started!',
                'score': 234,
                'comments': 102,
                'created': datetime.now() - timedelta(hours=1)
            }
        ]
        
        return mock_posts[:limit]


class FreeTwitterScraper:
    """Free Twitter scraper (using public search)"""
    
    def __init__(self):
        self.base_url = "https://twitter.com"
        
    def search_tweets(self, query: str, limit: int = 25) -> List[Dict]:
        """Search tweets (simulated)"""
        
        # In production, use free Twitter API basic tier or web scraping
        # Or use libraries like snscrape (free)
        
        # Simulated data
        mock_tweets = [
            {
                'text': '$BTC breaking out! Bullish momentum building 📈',
                'likes': 45,
                'retweets': 12,
                'created': datetime.now() - timedelta(minutes=30)
            },
            {
                'text': 'Market looking weak. Bearish divergence on the daily chart',
                'likes': 23,
                'retweets': 5,
                'created': datetime.now() - timedelta(hours=1)
            },
            {
                'text': 'Amazing gains today! Portfolio up 15% 🚀',
                'likes': 67,
                'retweets': 18,
                'created': datetime.now() - timedelta(minutes=15)
            }
        ]
        
        return mock_tweets[:limit]


class FreeNewsScraper:
    """Free news scraper using RSS feeds"""
    
    def __init__(self):
        # Free RSS feeds
        self.feeds = {
            'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
            'cointelegraph': 'https://cointelegraph.com/rss',
            'yahoo_finance': 'https://finance.yahoo.com/news/rssindex'
        }
        
    def get_news(self, source: str = 'all', limit: int = 10) -> List[Dict]:
        """Get news articles (simulated)"""
        
        # In production, use feedparser library (free)
        # import feedparser
        # feed = feedparser.parse(self.feeds[source])
        
        # Simulated data
        mock_news = [
            {
                'title': 'Bitcoin Surges Past $50K as Institutional Demand Grows',
                'description': 'Major institutions continue buying Bitcoin, driving prices higher.',
                'source': 'CoinDesk',
                'published': datetime.now() - timedelta(hours=3)
            },
            {
                'title': 'Fed Signals Potential Rate Cuts, Markets Rally',
                'description': 'Federal Reserve hints at easing monetary policy.',
                'source': 'Yahoo Finance',
                'published': datetime.now() - timedelta(hours=6)
            }
        ]
        
        return mock_news[:limit]


class RealTimeSentimentEngine:
    """Real-time market sentiment engine"""
    
    def __init__(self):
        self.sentiment_analyzer = FreeSentimentAnalyzer()
        self.reddit_scraper = FreeRedditScraper()
        self.twitter_scraper = FreeTwitterScraper()
        self.news_scraper = FreeNewsScraper()
        self.sentiment_history: List[Dict] = []
        
    def analyze_reddit_sentiment(self, subreddit: str = 'cryptocurrency') -> Dict:
        """Analyze Reddit sentiment"""
        
        posts = self.reddit_scraper.get_posts(subreddit)
        
        sentiments = []
        for post in posts:
            # Analyze title and text
            combined_text = f"{post['title']} {post['text']}"
            sentiment = self.sentiment_analyzer.analyze(combined_text)
            
            sentiments.append({
                'sentiment': sentiment,
                'weight': post['score'] + post['comments']  # Weight by engagement
            })
        
        # Calculate weighted average
        if sentiments:
            total_weight = sum(s['weight'] for s in sentiments)
            weighted_score = sum(s['sentiment'].score * s['weight'] for s in sentiments) / total_weight
            
            return {
                'source': 'reddit',
                'subreddit': subreddit,
                'score': weighted_score,
                'num_posts': len(posts),
                'label': 'bullish' if weighted_score > 0.1 else 'bearish' if weighted_score < -0.1 else 'neutral',
                'timestamp': datetime.now()
            }
        
        return {'source': 'reddit', 'score': 0, 'label': 'neutral'}
    
    def analyze_twitter_sentiment(self, query: str = 'bitcoin') -> Dict:
        """Analyze Twitter sentiment"""
        
        tweets = self.twitter_scraper.search_tweets(query)
        
        sentiments = []
        for tweet in tweets:
            sentiment = self.sentiment_analyzer.analyze(tweet['text'])
            
            sentiments.append({
                'sentiment': sentiment,
                'weight': tweet['likes'] + tweet['retweets']
            })
        
        # Calculate weighted average
        if sentiments:
            total_weight = sum(s['weight'] for s in sentiments)
            weighted_score = sum(s['sentiment'].score * s['weight'] for s in sentiments) / total_weight if total_weight > 0 else 0
            
            return {
                'source': 'twitter',
                'query': query,
                'score': weighted_score,
                'num_tweets': len(tweets),
                'label': 'bullish' if weighted_score > 0.1 else 'bearish' if weighted_score < -0.1 else 'neutral',
                'timestamp': datetime.now()
            }
        
        return {'source': 'twitter', 'score': 0, 'label': 'neutral'}
    
    def analyze_news_sentiment(self) -> Dict:
        """Analyze news sentiment"""
        
        articles = self.news_scraper.get_news()
        
        sentiments = []
        for article in articles:
            combined_text = f"{article['title']} {article['description']}"
            sentiment = self.sentiment_analyzer.analyze(combined_text)
            sentiments.append(sentiment)
        
        # Calculate average
        if sentiments:
            avg_score = np.mean([s.score for s in sentiments])
            
            return {
                'source': 'news',
                'score': avg_score,
                'num_articles': len(articles),
                'label': 'bullish' if avg_score > 0.1 else 'bearish' if avg_score < -0.1 else 'neutral',
                'timestamp': datetime.now()
            }
        
        return {'source': 'news', 'score': 0, 'label': 'neutral'}
    
    def get_aggregate_sentiment(self, symbol: str = 'BTC') -> Dict:
        """Get aggregate sentiment from all sources"""
        
        # Analyze all sources
        reddit_sentiment = self.analyze_reddit_sentiment('cryptocurrency')
        twitter_sentiment = self.analyze_twitter_sentiment(symbol)
        news_sentiment = self.analyze_news_sentiment()
        
        # Aggregate with weights
        weights = {'reddit': 0.3, 'twitter': 0.4, 'news': 0.3}
        
        aggregate_score = (
            reddit_sentiment['score'] * weights['reddit'] +
            twitter_sentiment['score'] * weights['twitter'] +
            news_sentiment['score'] * weights['news']
        )
        
        # Determine label
        if aggregate_score > 0.15:
            label = 'very_bullish'
        elif aggregate_score > 0.05:
            label = 'bullish'
        elif aggregate_score < -0.15:
            label = 'very_bearish'
        elif aggregate_score < -0.05:
            label = 'bearish'
        else:
            label = 'neutral'
        
        result = {
            'symbol': symbol,
            'aggregate_score': aggregate_score,
            'label': label,
            'sources': {
                'reddit': reddit_sentiment,
                'twitter': twitter_sentiment,
                'news': news_sentiment
            },
            'confidence': abs(aggregate_score),
            'timestamp': datetime.now(),
            'cost': 0  # Free
        }
        
        # Store in history
        self.sentiment_history.append(result)
        
        return result
    
    def get_sentiment_trend(self, symbol: str, hours: int = 24) -> Dict:
        """Get sentiment trend over time"""
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_sentiments = [
            s for s in self.sentiment_history
            if s['symbol'] == symbol and s['timestamp'] > cutoff
        ]
        
        if not recent_sentiments:
            return {'trend': 'unknown', 'direction': 'neutral'}
        
        # Calculate trend
        scores = [s['aggregate_score'] for s in recent_sentiments]
        
        if len(scores) >= 2:
            # Simple linear trend
            x = np.arange(len(scores))
            slope = np.polyfit(x, scores, 1)[0]
            
            if slope > 0.01:
                direction = 'improving'
            elif slope < -0.01:
                direction = 'deteriorating'
            else:
                direction = 'stable'
        else:
            direction = 'insufficient_data'
        
        return {
            'symbol': symbol,
            'trend': direction,
            'current_score': scores[-1] if scores else 0,
            'avg_score': np.mean(scores),
            'num_samples': len(scores)
        }


# Example usage
if __name__ == '__main__':
    # Initialize engine
    engine = RealTimeSentimentEngine()
    
    logger.info("Real-Time Market Sentiment Engine")
    print("="*60)
    
    # Get aggregate sentiment
    sentiment = engine.get_aggregate_sentiment('BTC')
    
    logger.info(f"\nAggregate Sentiment for {sentiment['symbol']}:")
    logger.info(f"Score: {sentiment['aggregate_score']:.3f}")
    logger.info(f"Label: {sentiment['label']}")
    logger.info(f"Confidence: {sentiment['confidence']:.2%}")
    
    logger.info(f"\nSource Breakdown:")
    logger.info(f"  Reddit: {sentiment['sources']['reddit']['score']:.3f} ({sentiment['sources']['reddit']['label']})")
    logger.info(f"  Twitter: {sentiment['sources']['twitter']['score']:.3f} ({sentiment['sources']['twitter']['label']})")
    logger.info(f"  News: {sentiment['sources']['news']['score']:.3f} ({sentiment['sources']['news']['label']})")
    
    logger.info(f"\nCost: ${sentiment['cost']}")
