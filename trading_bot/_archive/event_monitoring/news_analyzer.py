"""
Elite Trading Bot - News Analyzer

This module provides advanced news analysis capabilities for the Elite Trading Bot,
enabling real-time processing of financial news, sentiment analysis, and event detection.
"""

import enum
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
import itertools

try:
    import aiohttp
except ImportError:
    aiohttp = None
import pandas as pd
import numpy as np
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import spacy

from .event_monitor import EventMonitor, NewsEvent, EventType, EventPriority, EventSource
from enum import Enum
import json
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

# Try to load spaCy model for entity extraction
try:
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except (ImportError, OSError):
    logger.warning("spaCy model not available. Entity extraction will be limited.")
    SPACY_AVAILABLE = False


class NewsSource(enum.Enum):
    """Supported news sources."""
    ALPHA_VANTAGE = "alpha_vantage"
    BLOOMBERG = "bloomberg"
    REUTERS = "reuters"
    FINANCIAL_TIMES = "financial_times"
    WALL_STREET_JOURNAL = "wall_street_journal"
    CNBC = "cnbc"
    YAHOO_FINANCE = "yahoo_finance"
    SEEKING_ALPHA = "seeking_alpha"
    BENZINGA = "benzinga"
    CUSTOM = "custom"


@dataclass
class SentimentAnalysisResult:
    """Results of sentiment analysis on news text."""
    compound_score: float
    positive_score: float
    negative_score: float
    neutral_score: float
    is_positive: bool
    is_negative: bool
    is_neutral: bool
    confidence: float
    
    @classmethod
    def from_vader(cls, scores: Dict[str, float]):
        """Create from VADER sentiment analyzer scores."""
        return cls(
            compound_score=scores['compound'],
            positive_score=scores['pos'],
            negative_score=scores['neg'],
            neutral_score=scores['neu'],
            is_positive=scores['compound'] >= 0.05,
            is_negative=scores['compound'] <= -0.05,
            is_neutral=-0.05 < scores['compound'] < 0.05,
            confidence=abs(scores['compound'])
        )


class KeywordDetector:
    """Detects important keywords in financial news."""
    
    def __init__(self, custom_keywords: Optional[Dict[str, List[str]]] = None):
        """
        Initialize keyword detector.
        
        Args:
            custom_keywords: Optional dictionary of category -> keywords
        """
        self.custom_keywords = custom_keywords or {}
        self._initialize_default_keywords()
        
    def _initialize_default_keywords(self):
        """Initialize default financial keywords by category."""
        self.keywords = {
            "bullish": [
                "rally", "surge", "jump", "gain", "rise", "soar", "outperform",
                "beat", "exceed", "upgrade", "growth", "profit", "positive",
                "strong", "upside", "opportunity", "recovery", "bullish"
            ],
            "bearish": [
                "drop", "fall", "decline", "plunge", "tumble", "slump", "crash",
                "underperform", "miss", "downgrade", "loss", "negative", "weak",
                "downside", "risk", "recession", "bearish", "correction"
            ],
            "economic_indicators": [
                "gdp", "inflation", "cpi", "ppi", "unemployment", "jobs", "nonfarm",
                "payroll", "fomc", "fed", "interest rate", "rate hike", "rate cut",
                "monetary policy", "fiscal policy", "treasury", "yield"
            ],
            "market_events": [
                "ipo", "merger", "acquisition", "buyout", "takeover", "spinoff",
                "split", "dividend", "buyback", "earnings", "guidance", "forecast",
                "outlook", "estimate", "conference call", "sec filing"
            ],
            "risk_events": [
                "default", "bankruptcy", "lawsuit", "litigation", "investigation",
                "probe", "fine", "penalty", "recall", "breach", "hack", "cyberattack",
                "scandal", "fraud", "crisis", "emergency", "disaster"
            ],
            "central_banks": [
                "federal reserve", "fed", "ecb", "boj", "pboc", "bank of england",
                "rba", "rbnz", "snb", "riksbank", "powell", "lagarde", "kuroda",
                "bailey", "rate decision", "monetary policy", "qe", "quantitative easing"
            ]
        }
        
        # Add custom keywords
        for category, words in self.custom_keywords.items():
            if category in self.keywords:
                self.keywords[category].extend(words)
            else:
                self.keywords[category] = words
    
    def detect_keywords(self, text: str) -> Dict[str, List[str]]:
        """
        Detect keywords in text by category.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of category -> found keywords
        """
        text = text.lower()
        results = {}
        
        for category, keywords in self.keywords.items():
            found = []
            for keyword in keywords:
                if keyword.lower() in text:
                    found.append(keyword)
            
            if found:
                results[category] = found
                
        return results


class EntityExtractor:
    """Extracts named entities from financial news."""
    
    def __init__(self):
        """Initialize entity extractor."""
        self.spacy_available = SPACY_AVAILABLE
        
        # Simple regex patterns for fallback extraction
        self.patterns = {
            "ticker": r'\$([A-Z]{1,5})',  # $AAPL, $MSFT, etc.
            "company": r'([A-Z][a-z]+ (?:[A-Z][a-z]+ )*(?:Inc\.?|Corp\.?|Co\.?|Ltd\.?|LLC|Group|Holdings|Technologies|Therapeutics|Pharmaceuticals))',
            "person": r'([A-Z][a-z]+ [A-Z][a-z]+)',  # Simple name pattern
            "percentage": r'(\d+(?:\.\d+)?%)',
            "money": r'\$([\d,]+(?:\.\d+)?(?:\s*(?:million|billion|trillion))?)',
            "date": r'((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})'
        }
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of entity type -> entities
        """
        if self.spacy_available:
            return self._extract_with_spacy(text)
        else:
            return self._extract_with_regex(text)
    
    def _extract_with_spacy(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using spaCy."""
        doc = nlp(text)
        entities = {}
        
        # Process spaCy entities
        for ent in doc.ents:
            ent_type = ent.label_
            if ent_type not in entities:
                entities[ent_type] = []
            entities[ent_type].append(ent.text)
        
        # Add ticker symbols (not always caught by spaCy)
        ticker_pattern = self.patterns["ticker"]
        tickers = re.findall(ticker_pattern, text)
        if tickers:
            entities["TICKER"] = tickers
            
        return entities
    
    def _extract_with_regex(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using regex patterns (fallback)."""
        entities = {}
        
        for entity_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                entities[entity_type.upper()] = matches
                
        return entities


class NewsAnalyzer:
    """
    Advanced news analysis system for processing financial news,
    detecting sentiment, extracting entities, and generating events.
    """
    
    def __init__(self, 
                 event_monitor: EventMonitor,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize news analyzer.
        
        Args:
            event_monitor: Event monitoring system
            config: Optional configuration dictionary
        """
        self.event_monitor = event_monitor
        self.config = config or {}
        self._init_default_config()
        
        # Initialize components
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.keyword_detector = KeywordDetector(self.config.get("custom_keywords"))
        self.entity_extractor = EntityExtractor()
        
        # Cache for recently processed news to avoid duplicates
        self.processed_news_cache: Dict[str, datetime] = {}
        
        # API clients
        self.api_clients: Dict[NewsSource, Any] = {}
        
        # Enable news source in event monitor
        self.event_monitor.enable_source(EventSource.NEWS_API)
        
        logger.info("NewsAnalyzer initialized")
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        defaults = {
            "cache_expiration_minutes": 60,
            "relevance_threshold": 0.5,
            "high_priority_threshold": 0.8,
            "max_summary_sentences": 3,
            "api_request_timeout": 30,
            "max_news_per_request": 100,
            "default_language": "en"
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    async def configure_api(self, source: NewsSource, api_key: str, **kwargs):
        """
        Configure API client for a news source.
        
        Args:
            source: News source to configure
            api_key: API key for the source
            **kwargs: Additional configuration parameters
        """
        self.api_clients[source] = {
            "api_key": api_key,
            "base_url": kwargs.get("base_url"),
            "session": None,
            "config": kwargs
        }
        logger.info(f"Configured API client for {source.value}")
    
    async def _get_session(self, source: NewsSource) -> aiohttp.ClientSession:
        """Get or create an aiohttp session for a news source."""
        if source not in self.api_clients:
            raise ValueError(f"API client for {source.value} not configured")
            
        client = self.api_clients[source]
        
        if client["session"] is None or client["session"].closed:
            client["session"] = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config["api_request_timeout"])
            )
            
        return client["session"]
    
    async def fetch_news(self, source: NewsSource, **params) -> List[Dict[str, Any]]:
        """
        Fetch news from a configured source.
        
        Args:
            source: News source to fetch from
            **params: Additional parameters for the API request
            
        Returns:
            List of news articles
        """
        if source not in self.api_clients:
            raise ValueError(f"API client for {source.value} not configured")
            
        client = self.api_clients[source]
        session = await self._get_session(source)
        
        # Build request URL and parameters based on the source
        if source == NewsSource.ALPHA_VANTAGE:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "NEWS_SENTIMENT",
                "apikey": client["api_key"],
                "limit": params.get("limit", self.config["max_news_per_request"]),
                "sort": params.get("sort", "LATEST"),
                "topics": params.get("topics", "")
            }
        elif source == NewsSource.BENZINGA:
            url = f"{client['base_url']}/news"
            params = {
                "token": client["api_key"],
                "pageSize": params.get("limit", self.config["max_news_per_request"]),
                "displayOutput": "full",
                "sortBy": "date",
                "sortDir": "desc"
            }
            if "tickers" in params:
                params["tickers"] = ",".join(params["tickers"])
        else:
            pass
        try:
            # Generic handling for other sources
            url = client["base_url"]
            params["api_key"] = client["api_key"]
        
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Parse response based on source
                if source == NewsSource.ALPHA_VANTAGE:
                    return data.get("feed", [])
                elif source == NewsSource.BENZINGA:
                    return data.get("result", [])
                else:
                    return data.get("articles", [])
                    
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching news from {source.value}: {e}")
            return []
    
    def _is_duplicate(self, news_id: str, url: str) -> bool:
        """
        Check if news has been recently processed.
        
        Args:
            news_id: Unique ID of the news
            url: URL of the news article
            
        Returns:
            True if duplicate, False otherwise
        """
        now = datetime.now()
        expiration_minutes = self.config["cache_expiration_minutes"]
        
        # Check by ID
        if news_id in self.processed_news_cache:
            timestamp = self.processed_news_cache[news_id]
            if (now - timestamp).total_seconds() < expiration_minutes * 60:
                return True
        
        # Check by URL
        url_hash = hash(url)
        if str(url_hash) in self.processed_news_cache:
            timestamp = self.processed_news_cache[str(url_hash)]
            if (now - timestamp).total_seconds() < expiration_minutes * 60:
                return True
                
        return False
    
    def _mark_processed(self, news_id: str, url: str):
        """Mark news as processed."""
        now = datetime.now()
        self.processed_news_cache[news_id] = now
        self.processed_news_cache[str(hash(url))] = now
        
        # Clean up old entries
        self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Remove expired entries from the cache."""
        now = datetime.now()
        expiration_seconds = self.config["cache_expiration_minutes"] * 60
        
        expired_keys = [
            key for key, timestamp in self.processed_news_cache.items()
            if (now - timestamp).total_seconds() > expiration_seconds
        ]
        
        for key in expired_keys:
            del self.processed_news_cache[key]
    
    def analyze_sentiment(self, text: str) -> SentimentAnalysisResult:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            SentimentAnalysisResult
        """
        scores = self.sentiment_analyzer.polarity_scores(text)
        return SentimentAnalysisResult.from_vader(scores)
    
    def calculate_relevance(self, 
                           text: str, 
                           keywords: Dict[str, List[str]],
                           entities: Dict[str, List[str]]) -> float:
        """
        Calculate relevance score for news.
        
        Args:
            text: News text
            keywords: Detected keywords
            entities: Extracted entities
            
        Returns:
            Relevance score (0-1)
        """
        # Base score
        score = 0.0
        
        # Keywords boost
        keyword_count = sum(len(words) for words in keywords.values())
        keyword_categories = len(keywords)
        
        # More weight to certain categories
        if "economic_indicators" in keywords:
            score += 0.2
        if "central_banks" in keywords:
            score += 0.2
        if "market_events" in keywords:
            score += 0.15
        if "risk_events" in keywords:
            score += 0.15
            
        # General keyword score
        score += min(0.3, keyword_count * 0.03)
        score += min(0.2, keyword_categories * 0.05)
        
        # Entities boost
        entity_count = sum(len(ents) for ents in entities.values())
        
        # More weight to certain entity types
        ticker_count = len(entities.get("TICKER", []))
        company_count = len(entities.get("ORG", [])) + len(entities.get("company", []))
        
        score += min(0.2, ticker_count * 0.05)
        score += min(0.1, company_count * 0.02)
        score += min(0.1, entity_count * 0.01)
        
        # Cap at 1.0
        return min(1.0, score)
    
    def generate_summary(self, text: str) -> str:
        """
        Generate a concise summary of news text.
        
        Args:
            text: News text
            
        Returns:
            Summary text
        """
        # Simple extractive summarization
        sentences = sent_tokenize(text)
        
        if len(sentences) <= self.config["max_summary_sentences"]:
            return text
            
        # Use first few sentences as summary
        return " ".join(sentences[:self.config["max_summary_sentences"]])
    
    def determine_priority(self, 
                          relevance_score: float, 
                          sentiment_result: SentimentAnalysisResult,
                          keywords: Dict[str, List[str]]) -> EventPriority:
        """
        Determine priority of news event.
        
        Args:
            relevance_score: Relevance score
            sentiment_result: Sentiment analysis result
            keywords: Detected keywords
            
        Returns:
            EventPriority
        """
        # High priority for highly relevant news
        if relevance_score >= self.config["high_priority_threshold"]:
            return EventPriority.HIGH
            
        # High priority for strong sentiment
        if abs(sentiment_result.compound_score) >= 0.6:
            return EventPriority.HIGH
            
        # High priority for risk events
        if "risk_events" in keywords and len(keywords["risk_events"]) >= 2:
            return EventPriority.HIGH
            
        # Medium priority for moderately relevant news
        if relevance_score >= self.config["relevance_threshold"]:
            return EventPriority.MEDIUM
            
        # Low priority for everything else
        return EventPriority.LOW
    
    async def process_news_item(self, 
                               news_item: Dict[str, Any], 
                               source: NewsSource) -> Optional[NewsEvent]:
        """
        Process a single news item and generate an event if relevant.
        
        Args:
            news_item: News item data
            source: Source of the news
            
        Returns:
            NewsEvent or None if not relevant
        """
        # Extract fields based on source
        if source == NewsSource.ALPHA_VANTAGE:
            news_id = news_item.get("id", str(hash(news_item.get("url", ""))))
            headline = news_item.get("title", "")
            url = news_item.get("url", "")
            source_name = news_item.get("source", "")
            text = news_item.get("summary", "")
            timestamp_str = news_item.get("time_published", "")
            timestamp = datetime.strptime(timestamp_str, "%Y%m%dT%H%M%S") if timestamp_str else datetime.now()
        elif source == NewsSource.BENZINGA:
            news_id = str(news_item.get("id", hash(news_item.get("url", ""))))
            headline = news_item.get("title", "")
            url = news_item.get("url", "")
            source_name = "Benzinga"
            text = news_item.get("body", "")
            timestamp_str = news_item.get("created_at", "")
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00")) if timestamp_str else datetime.now()
        else:
            # Generic handling
            news_id = str(hash(news_item.get("url", "")))
            headline = news_item.get("title", "")
            url = news_item.get("url", "")
            source_name = news_item.get("source", {}).get("name", "")
            text = news_item.get("description", "") or news_item.get("content", "")
            timestamp_str = news_item.get("publishedAt", "")
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00")) if timestamp_str else datetime.now()
        
        # Skip if already processed
        if self._is_duplicate(news_id, url):
            return None
            
        # Combine headline and text for analysis
        full_text = f"{headline}. {text}"
        
        # Analyze sentiment
        sentiment_result = self.analyze_sentiment(full_text)
        
        # Detect keywords
        keywords = self.keyword_detector.detect_keywords(full_text)
        
        # Extract entities
        entities = self.entity_extractor.extract_entities(full_text)
        
        # Calculate relevance
        relevance_score = self.calculate_relevance(full_text, keywords, entities)
        
        # Skip if not relevant enough
        if relevance_score < self.config["relevance_threshold"]:
            return None
            
        # Generate summary
        summary = self.generate_summary(text)
        
        # Determine priority
        priority = self.determine_priority(relevance_score, sentiment_result, keywords)
        
        # Create event
        event = NewsEvent(
            id=f"news_{news_id}",
            type=EventType.NEWS,
            priority=priority,
            source=EventSource.NEWS_API,
            timestamp=timestamp,
            description=headline,
            headline=headline,
            url=url,
            news_source=source_name,  # Changed from 'source' to 'news_source' to avoid duplicate
            sentiment_score=sentiment_result.compound_score,
            relevance_score=relevance_score,
            entities=entities,
            keywords=list(itertools.chain.from_iterable(keywords.values())),
            summary=summary,
            raw_data={
                "source_type": source.value,
                "keywords_by_category": keywords
            }
        )
        
        # Mark as processed
        self._mark_processed(news_id, url)
        
        return event
    
    async def process_news_batch(self, 
                                news_items: List[Dict[str, Any]], 
                                source: NewsSource) -> List[NewsEvent]:
        """
        Process a batch of news items.
        
        Args:
            news_items: List of news items
            source: Source of the news
            
        Returns:
            List of generated NewsEvents
        """
        events = []
        
        for item in news_items:
            event = await self.process_news_item(item, source)
            if event:
                events.append(event)
                # Add to event monitor
                await self.event_monitor.add_event(event)
                
        logger.info(f"Processed {len(news_items)} news items from {source.value}, generated {len(events)} events")
        return events
    
    async def fetch_and_process(self, source: NewsSource, **params) -> List[NewsEvent]:
        """
        Fetch and process news from a source.
        
        Args:
            source: News source
            **params: Additional parameters for the API request
            
        Returns:
            List of generated NewsEvents
        """
        news_items = await self.fetch_news(source, **params)
        return await self.process_news_batch(news_items, source)
    
    async def process_custom_news(self, news_items: List[Dict[str, Any]]) -> List[NewsEvent]:
        """
        Process custom news items.
        
        Args:
            news_items: List of news items with at least 'title' and 'text' fields
            
        Returns:
            List of generated NewsEvents
        """
        # Convert to standard format
        standardized_items = []
        
        for item in news_items:
            standardized = {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "source": item.get("source", "custom"),
                "description": item.get("text", ""),
                "publishedAt": item.get("timestamp", datetime.now().isoformat())
            }
            standardized_items.append(standardized)
            
        return await self.process_news_batch(standardized_items, NewsSource.CUSTOM)
    
    async def close(self):
        """Close all API client sessions."""
        for source, client in self.api_clients.items():
            if client["session"] and not client["session"].closed:
                await client["session"].close()
                
        logger.info("Closed all NewsAnalyzer API sessions")
