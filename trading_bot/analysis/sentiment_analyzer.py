"""
from pathlib import Path
Unified Sentiment Analysis System for Trading Bot
Integrates news and social media sentiment analysis for trading signals
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union
import logging
from datetime import datetime, timedelta
import asyncio
import json
import os
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns

from trading_bot.analysis.sentiment_core import SentimentAnalyzer, SentimentResult, AssetSentiment
from trading_bot.analysis.news_collector import NewsCollector
from trading_bot.analysis.social_media_collector import SocialMediaCollector
import pathlib
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



logger = logging.getLogger(__name__)


@dataclass
class SentimentSignal:
    """Trading signal based on sentiment analysis"""
    ticker: str
    signal_type: str  # 'bullish', 'bearish', 'neutral'
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    news_sentiment: float
    social_sentiment: float
    volume: int
    sentiment_change: float
    timestamp: datetime
    sources: Dict[str, float]
    key_topics: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'ticker': self.ticker,
            'signal_type': self.signal_type,
            'strength': self.strength,
            'confidence': self.confidence,
            'news_sentiment': self.news_sentiment,
            'social_sentiment': self.social_sentiment,
            'volume': self.volume,
            'sentiment_change': self.sentiment_change,
            'timestamp': self.timestamp.isoformat(),
            'sources': self.sources,
            'key_topics': self.key_topics
        }


class UnifiedSentimentAnalyzer:
    """
    Unified sentiment analysis system for trading signals
    
    Features:
    - News and social media sentiment integration
    - Weighted sentiment scoring
    - Signal generation
    - Trend detection
    - Visualization
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize components
        self.news_collector = NewsCollector(self.config.get('news_collector', {}))
        self.social_collector = SocialMediaCollector(self.config.get('social_collector', {}))
        self.sentiment_analyzer = SentimentAnalyzer(self.config.get('sentiment_analyzer', {}))
        
        # Sentiment weights
        self.weights = self.config.get('weights', {
            'news': 0.6,
            'social': 0.4,
            'sources': {
                'financial_times': 0.9,
                'bloomberg': 0.9,
                'reuters': 0.9,
                'wsj': 0.9,
                'cnbc': 0.8,
                'yahoo_finance': 0.7,
                'seeking_alpha': 0.7,
                'twitter': 0.5,
                'reddit': 0.4,
                'stocktwits': 0.6,
                'tradingview': 0.7
            }
        })
        
        # Signal thresholds
        self.thresholds = self.config.get('thresholds', {
            'bullish': 0.2,
            'bearish': -0.2,
            'min_confidence': 0.5,
            'min_volume': 5
        })
        
        # Cache directory
        self.cache_dir = self.config.get('cache_dir', 'sentiment_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Sentiment history
        self.sentiment_history = {}
        
        logger.info("Unified Sentiment Analyzer initialized")
    
    async def analyze_sentiment(self, tickers: List[str], 
                              keywords: Optional[List[str]] = None,
                              lookback_hours: int = 24) -> Dict[str, SentimentSignal]:
        """
        Analyze sentiment and generate trading signals
        
        Args:
            tickers: List of ticker symbols
            keywords: Additional keywords to search for
            lookback_hours: Hours to look back for data
            
        Returns:
            Dictionary of ticker to sentiment signal
        """
        # Collect news and social media data
        news_data, social_data = await asyncio.gather(
            self._collect_news(tickers, keywords, lookback_hours),
            self._collect_social(tickers, keywords, lookback_hours)
        )
        
        # Analyze sentiment
        news_results, social_results = await asyncio.gather(
            self._analyze_news(news_data),
            self._analyze_social(social_data)
        )
        
        # Update sentiment history
        self._update_history(news_results, social_results)
        
        # Generate signals
        signals = self._generate_signals(tickers)
        
        # Save cache
        self._save_cache()
        
        return signals
    
    async def _collect_news(self, tickers: List[str], 
                          keywords: Optional[List[str]], 
                          lookback_hours: int) -> List[Dict[str, Any]]:
        """Collect news data"""
        logger.info(f"Collecting news for {len(tickers)} tickers")
        return await self.news_collector.collect_news(
            tickers=tickers,
            keywords=keywords,
            max_age_hours=lookback_hours
        )
    
    async def _collect_social(self, tickers: List[str], 
                            keywords: Optional[List[str]], 
                            lookback_hours: int) -> List[Dict[str, Any]]:
        """Collect social media data"""
        logger.info(f"Collecting social media posts for {len(tickers)} tickers")
        return await self.social_collector.collect_posts(
            tickers=tickers,
            keywords=keywords,
            max_age_hours=lookback_hours
        )
    
    async def _analyze_news(self, news_data: List[Dict[str, Any]]) -> List[SentimentResult]:
        """Analyze news sentiment"""
        if not news_data:
            return []
        
        logger.info(f"Analyzing sentiment for {len(news_data)} news articles")
        
        # Prepare data for analysis
        texts = []
        for article in news_data:
            # Combine title and content
            text = article.get('title', '') + ' ' + article.get('content', '')
            
            texts.append({
                'text': text,
                'source': article.get('source', 'news'),
                'timestamp': article.get('published_at', datetime.now())
            })
        
        # Analyze sentiment
        results = self.sentiment_analyzer.analyze_texts(texts)
        
        return results
    
    async def _analyze_social(self, social_data: List[Dict[str, Any]]) -> List[SentimentResult]:
        """Analyze social media sentiment"""
        if not social_data:
            return []
        
        logger.info(f"Analyzing sentiment for {len(social_data)} social media posts")
        
        # Prepare data for analysis
        texts = []
        for post in social_data:
            texts.append({
                'text': post.get('text', ''),
                'source': post.get('platform', 'social'),
                'timestamp': post.get('created_at', datetime.now())
            })
        
        # Analyze sentiment
        results = self.sentiment_analyzer.analyze_texts(texts)
        
        return results
    
    def _update_history(self, news_results: List[SentimentResult], 
                       social_results: List[SentimentResult]):
        """Update sentiment history"""
        # Update sentiment analyzer history
        self.sentiment_analyzer.update_sentiment_history(news_results + social_results)
        
        # Update local history
        for ticker in self.sentiment_analyzer.sentiment_history:
            if ticker not in self.sentiment_history:
                self.sentiment_history[ticker] = []
            
            # Get latest sentiment
            sentiment = self.sentiment_analyzer.get_asset_sentiment(ticker)
            if sentiment:
                self.sentiment_history[ticker].append({
                    'timestamp': sentiment.timestamp,
                    'score': sentiment.score,
                    'volume': sentiment.volume
                })
                
                # Limit history size
                if len(self.sentiment_history[ticker]) > 100:
                    self.sentiment_history[ticker] = self.sentiment_history[ticker][-100:]
    
    def _generate_signals(self, tickers: List[str]) -> Dict[str, SentimentSignal]:
        """Generate trading signals from sentiment"""
        signals = {}
        
        for ticker in tickers:
            # Get asset sentiment
            sentiment = self.sentiment_analyzer.get_asset_sentiment(ticker)
            if not sentiment:
                continue
            
            # Calculate sentiment change
            sentiment_change = self._calculate_sentiment_change(ticker)
            
            # Calculate source-weighted sentiment
            weighted_sentiment = self._calculate_weighted_sentiment(sentiment)
            
            # Determine signal type
            if weighted_sentiment > self.thresholds['bullish']:
                signal_type = 'bullish'
            elif weighted_sentiment < self.thresholds['bearish']:
                signal_type = 'bearish'
            else:
                signal_type = 'neutral'
            
            # Calculate signal strength
            strength = min(1.0, abs(weighted_sentiment) * 2)
            
            # Calculate confidence
            confidence = self._calculate_confidence(sentiment, sentiment_change)
            
            # Create signal
            if confidence >= self.thresholds['min_confidence'] and sentiment.volume >= self.thresholds['min_volume']:
                signal = SentimentSignal(
                    ticker=ticker,
                    signal_type=signal_type,
                    strength=strength,
                    confidence=confidence,
                    news_sentiment=self._extract_source_sentiment(sentiment, 'news'),
                    social_sentiment=self._extract_source_sentiment(sentiment, 'social'),
                    volume=sentiment.volume,
                    sentiment_change=sentiment_change,
                    timestamp=datetime.now(),
                    sources=sentiment.sources,
                    key_topics=sentiment.trending_topics
                )
                
                signals[ticker] = signal
        
        return signals
    
    def _calculate_weighted_sentiment(self, sentiment: AssetSentiment) -> float:
        """Calculate weighted sentiment score"""
        # Extract source sentiments
        news_sources = ['financial_times', 'bloomberg', 'reuters', 'wsj', 'cnbc', 'yahoo_finance', 'seeking_alpha']
        social_sources = ['twitter', 'reddit', 'stocktwits', 'tradingview']
        
        news_scores = []
        social_scores = []
        
        for source, score in sentiment.sources.items():
            source_weight = self.weights['sources'].get(source, 0.5)
            
            if source in news_sources:
                news_scores.append((score, source_weight))
            elif source in social_sources:
                social_scores.append((score, source_weight))
        
        # Calculate weighted averages
        news_sentiment = 0.0
        news_weight_sum = 0.0
        
        for score, weight in news_scores:
            news_sentiment += score * weight
            news_weight_sum += weight
        
        if news_weight_sum > 0:
            news_sentiment /= news_weight_sum
        
        social_sentiment = 0.0
        social_weight_sum = 0.0
        
        for score, weight in social_scores:
            social_sentiment += score * weight
            social_weight_sum += weight
        
        if social_weight_sum > 0:
            social_sentiment /= social_weight_sum
        
        # Combine news and social sentiment
        if news_scores and social_scores:
            # Both sources available
            weighted_sentiment = (
                news_sentiment * self.weights['news'] + 
                social_sentiment * self.weights['social']
            )
        elif news_scores:
            # Only news available
            weighted_sentiment = news_sentiment
        elif social_scores:
            # Only social available
            weighted_sentiment = social_sentiment
        else:
            # No sources available
            weighted_sentiment = 0.0
        
        return weighted_sentiment
    
    def _extract_source_sentiment(self, sentiment: AssetSentiment, source_type: str) -> float:
        """Extract sentiment for a specific source type"""
        news_sources = ['financial_times', 'bloomberg', 'reuters', 'wsj', 'cnbc', 'yahoo_finance', 'seeking_alpha']
        social_sources = ['twitter', 'reddit', 'stocktwits', 'tradingview']
        
        sources = news_sources if source_type == 'news' else social_sources
        scores = []
        
        for source, score in sentiment.sources.items():
            if source in sources:
                scores.append(score)
        
        if scores:
            return sum(scores) / len(scores)
        else:
            return 0.0
    
    def _calculate_sentiment_change(self, ticker: str) -> float:
        """Calculate sentiment change over time"""
        history = self.sentiment_history.get(ticker, [])
        
        if len(history) < 2:
            return 0.0
        
        # Get latest and previous sentiment
        latest = history[-1]
        previous = history[-2] if len(history) >= 2 else None
        
        if previous:
            return latest['score'] - previous['score']
        else:
            return 0.0
    
    def _calculate_confidence(self, sentiment: AssetSentiment, sentiment_change: float) -> float:
        """Calculate confidence in sentiment signal"""
        # Base confidence on volume
        volume_factor = min(1.0, sentiment.volume / 20)  # Scale volume up to 20 mentions
        
        # Adjust for sentiment magnitude
        magnitude_factor = sentiment.magnitude
        
        # Adjust for sentiment change (trend)
        trend_factor = 0.5
        if abs(sentiment_change) > 0.1:
            # Strong trend in same direction as sentiment
            if (sentiment.score > 0 and sentiment_change > 0) or (sentiment.score < 0 and sentiment_change < 0):
                trend_factor = 0.8
            # Strong trend in opposite direction
            elif (sentiment.score > 0 and sentiment_change < 0) or (sentiment.score < 0 and sentiment_change > 0):
                trend_factor = 0.3
        
        # Calculate overall confidence
        confidence = (volume_factor * 0.4 + magnitude_factor * 0.4 + trend_factor * 0.2)
        
        return confidence
    
    def _save_cache(self):
        """Save sentiment cache"""
        cache_file = os.path.join(self.cache_dir, 'sentiment_history.json')
        
        try:
            # Convert history to serializable format
            serializable_history = {}
            for ticker, history in self.sentiment_history.items():
                serializable_history[ticker] = []
                for item in history:
                    serializable_history[ticker].append({
                        'timestamp': item['timestamp'].isoformat(),
                        'score': item['score'],
                        'volume': item['volume']
                    })
            
            with open(cache_file, 'w') as f:
                json.dump(serializable_history, f)
            
            logger.debug(f"Saved sentiment history to {cache_file}")
        except Exception as e:
            logger.warning(f"Error saving sentiment cache: {e}")
    
    def _load_cache(self):
        """Load sentiment cache"""
        cache_file = os.path.join(self.cache_dir, 'sentiment_history.json')
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    serialized_history = json.load(f)
                
                # Convert to proper format
                for ticker, history in serialized_history.items():
                    self.sentiment_history[ticker] = []
                    for item in history:
                        self.sentiment_history[ticker].append({
                            'timestamp': datetime.fromisoformat(item['timestamp']),
                            'score': item['score'],
                            'volume': item['volume']
                        })
                
                logger.info(f"Loaded sentiment history from {cache_file}")
            except Exception as e:
                logger.warning(f"Error loading sentiment cache: {e}")
    
    def plot_sentiment_history(self, ticker: str, save_path: Optional[str] = None):
        """
        Plot sentiment history for a ticker
        
        Args:
            ticker: Ticker symbol
            save_path: Path to save plot, if None, plot is displayed
        """
        history = self.sentiment_history.get(ticker, [])
        
        if not history:
            logger.warning(f"No sentiment history for {ticker}")
            return
        
        # Extract data
        timestamps = [item['timestamp'] for item in history]
        scores = [item['score'] for item in history]
        volumes = [item['volume'] for item in history]
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # Plot sentiment score
        ax1.plot(timestamps, scores, 'b-', marker='o')
        ax1.axhline(y=0, color='r', linestyle='-', alpha=0.3)
        ax1.set_ylabel('Sentiment Score')
        ax1.set_title(f'Sentiment History for {ticker}')
        ax1.grid(True, alpha=0.3)
        
        # Color positive and negative areas
        ax1.fill_between(timestamps, scores, 0, where=[s > 0 for s in scores], color='green', alpha=0.3)
        ax1.fill_between(timestamps, scores, 0, where=[s < 0 for s in scores], color='red', alpha=0.3)
        
        # Plot volume
        ax2.bar(timestamps, volumes, color='skyblue')
        ax2.set_ylabel('Mention Volume')
        ax2.set_xlabel('Time')
        ax2.grid(True, alpha=0.3)
        
        # Format x-axis
        fig.autofmt_xdate()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Saved sentiment plot to {save_path}")
        else:
            plt.show()
        
        plt.close()


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create analyzer
    analyzer = UnifiedSentimentAnalyzer()
    
    # Run async analysis
    async def main():
        signals = await analyzer.analyze_sentiment(
            tickers=['AAPL', 'MSFT', 'GOOGL', 'TSLA'],
            keywords=['tech stocks', 'earnings'],
            lookback_hours=24
        )
        
        logger.info(f"Generated {len(signals)} sentiment signals")
        
        for ticker, signal in signals.items():
            logger.info(f"Ticker: {ticker}")
            logger.info(f"Signal: {signal.signal_type}")
            logger.info(f"Strength: {signal.strength:.2f}")
            logger.info(f"Confidence: {signal.confidence:.2f}")
            logger.info(f"News sentiment: {signal.news_sentiment:.2f}")
            logger.info(f"Social sentiment: {signal.social_sentiment:.2f}")
            logger.info(f"Volume: {signal.volume}")
            logger.info(f"Key topics: {signal.key_topics}")
            print()
        
        # Plot sentiment history
        for ticker in signals:
            analyzer.plot_sentiment_history(ticker)
    
    asyncio.run(main())
