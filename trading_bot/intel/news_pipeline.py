"""
Elite Trading Bot - News Pipeline

This module provides a comprehensive pipeline for fetching, processing, and analyzing
financial news articles to enhance trading decisions with real-time internet data.

Features:
- Fetches financial news articles from multiple sources (NewsAPI, RSS feeds)
- Cleans and normalizes text while preserving metadata
- Embeds text using sentence-transformers for semantic understanding
- Indexes embeddings in FAISS for efficient similarity search
- Provides structured trading signals based on news sentiment and relevance
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
import re
import hashlib
import pickle

# Third-party imports
import numpy as np
import pandas as pd
import faiss
import feedparser
try:
    import requests
except ImportError:
    requests = None
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
import numpy
import pandas

# Ensure NLTK resources are available
try:
    nltk.data.find('vader_lexicon')
    nltk.data.find('punkt')
    nltk.data.find('stopwords')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Represents a news article with metadata and content."""
    id: str
    title: str
    content: str
    summary: str
    url: str
    source: str
    published_at: datetime
    keywords: List[str] = field(default_factory=list)
    embedding: Optional[np.ndarray] = None
    sentiment_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert article to dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'url': self.url,
            'source': self.source,
            'published_at': self.published_at.isoformat(),
            'keywords': self.keywords,
            'sentiment_score': self.sentiment_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NewsArticle':
        """Create article from dictionary."""
        return cls(
            id=data['id'],
            title=data['title'],
            content=data['content'],
            summary=data['summary'],
            url=data['url'],
            source=data['source'],
            published_at=datetime.fromisoformat(data['published_at']),
            keywords=data['keywords'],
            sentiment_score=data['sentiment_score']
        )


@dataclass
class NewsSignal:
    """Structured trading signal derived from news analysis."""
    asset: str
    sentiment: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    impact: float  # 0.0 to 1.0
    source: str
    title: str
    url: str
    published_at: datetime
    summary: str
    relevance_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary."""
        return {
            'asset': self.asset,
            'sentiment': self.sentiment,
            'confidence': self.confidence,
            'impact': self.impact,
            'source': self.source,
            'title': self.title,
            'url': self.url,
            'published_at': self.published_at.isoformat(),
            'summary': self.summary,
            'relevance_score': self.relevance_score
        }


class NewsPipeline:
    """
    Pipeline for fetching, processing, and analyzing financial news.
    
    This class handles the entire workflow from fetching articles to
    generating structured trading signals based on news content.
    """
    
    def __init__(self, 
                 newsapi_key: Optional[str] = None,
                 model_name: str = "all-MiniLM-L6-v2",
                 data_dir: str = "./data/news",
                 max_articles: int = 1000,
                 refresh_interval: int = 3600):
        """
        Initialize the news pipeline.
        
        Args:
            newsapi_key: API key for NewsAPI (optional)
            model_name: Name of the sentence-transformer model to use
            data_dir: Directory to store news data and indices
            max_articles: Maximum number of articles to keep in memory
            refresh_interval: Time between news refreshes in seconds
        """
        self.newsapi_key = newsapi_key or os.environ.get("NEWSAPI_KEY")
        self.model_name = model_name
        self.data_dir = data_dir
        self.max_articles = max_articles
        self.refresh_interval = refresh_interval
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize components
        self.articles: Dict[str, NewsArticle] = {}
        self.last_refresh = datetime.now() - timedelta(hours=24)  # Force initial refresh
        self.index_path = os.path.join(data_dir, "faiss_index.bin")
        self.articles_path = os.path.join(data_dir, "articles.json")
        
        # Load existing data if available
        self._load_data()
        
        # Initialize NLP components
        logger.info(f"Loading sentence transformer model: {model_name}")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # Initialize FAISS index
        self._init_index()
        
        logger.info("News pipeline initialized")
    
    def _init_index(self):
        """Initialize or load FAISS index."""
        if os.path.exists(self.index_path):
            logger.info("Loading existing FAISS index")
            self.index = faiss.read_index(self.index_path)
        else:
            logger.info("Creating new FAISS index")
            self.index = faiss.IndexFlatL2(self.embedding_dim)
        
        # Create ID mapping
        self.id_to_idx = {article_id: i for i, article_id in enumerate(self.articles.keys())}
        self.idx_to_id = {i: article_id for article_id, i in self.id_to_idx.items()}
    
    def _load_data(self):
        """Load existing articles from disk."""
        if os.path.exists(self.articles_path):
            try:
                with open(self.articles_path, 'r') as f:
                    articles_data = json.load(f)
                
                for article_data in articles_data:
                    article = NewsArticle.from_dict(article_data)
                    self.articles[article.id] = article
                
                logger.info(f"Loaded {len(self.articles)} articles from disk")
            except Exception as e:
                logger.error(f"Error loading articles: {e}")
    
    def _save_data(self):
        """Save articles to disk."""
        try:
            articles_data = [article.to_dict() for article in self.articles.values()]
            
            with open(self.articles_path, 'w') as f:
                json.dump(articles_data, f)
            
            # Save FAISS index
            faiss.write_index(self.index, self.index_path)
            
            logger.info(f"Saved {len(self.articles)} articles to disk")
        except Exception as e:
            logger.error(f"Error saving articles: {e}")
    
    async def refresh(self, assets: List[str] = None):
        """
        Refresh news articles for specified assets.
        
        Args:
            assets: List of asset symbols to fetch news for
        """
        # Check if refresh is needed
        now = datetime.now()
        if (now - self.last_refresh).total_seconds() < self.refresh_interval:
            logger.info("Skipping refresh, not enough time elapsed since last refresh")
            return
        
        self.last_refresh = now
        assets = assets or []
        
        # Fetch articles from different sources
        new_articles = []
        
        # Fetch from NewsAPI if key is available
        if self.newsapi_key:
            newsapi_articles = await self._fetch_from_newsapi(assets)
            new_articles.extend(newsapi_articles)
        
        # Fetch from RSS feeds
        rss_articles = await self._fetch_from_rss(assets)
        new_articles.extend(rss_articles)
        
        # Process new articles
        if new_articles:
            await self._process_articles(new_articles)
            
            # Update index
            self._update_index()
            
            # Save data
            self._save_data()
            
            logger.info(f"Refreshed {len(new_articles)} articles")
        else:
            logger.info("No new articles found")
    
    async def _fetch_from_newsapi(self, assets: List[str]) -> List[NewsArticle]:
        """
        Fetch articles from NewsAPI.
        
        Args:
            assets: List of asset symbols to fetch news for
            
        Returns:
            List of news articles
        """
        if not self.newsapi_key:
            return []
        
        articles = []
        
        try:
            # Prepare query
            if assets:
                # Create query for specific assets
                query = " OR ".join([f'"{asset}"' for asset in assets])
                query += " AND (finance OR market OR stock OR trading OR economy OR economic)"
            else:
                # General financial news
                query = "finance OR market OR stock OR trading OR economy OR economic"
            
            # Make API request
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "apiKey": self.newsapi_key,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 100
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if response.status_code != 200:
                logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                return []
            
            # Process articles
            for item in data.get("articles", []):
                # Generate ID
                article_id = hashlib.md5(item["url"].encode()).hexdigest()
                
                # Skip if already exists
                if article_id in self.articles:
                    continue
                try:
                
                # Parse date
                    published_at = datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    published_at = datetime.now()
                
                # Create article
                article = NewsArticle(
                    id=article_id,
                    title=item["title"],
                    content=item.get("content", ""),
                    summary=item.get("description", ""),
                    url=item["url"],
                    source=item.get("source", {}).get("name", "NewsAPI"),
                    published_at=published_at,
                    keywords=[]
                )
                
                articles.append(article)
            
            logger.info(f"Fetched {len(articles)} articles from NewsAPI")
            
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
        
        return articles
    
    async def _fetch_from_rss(self, assets: List[str]) -> List[NewsArticle]:
        """
        Fetch articles from RSS feeds.
        
        Args:
            assets: List of asset symbols to fetch news for
            
        Returns:
            List of news articles
        """
        articles = []
        
        # List of financial news RSS feeds
        feeds = [
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",  # CNBC Markets
            "https://www.reuters.com/business/finance/rssfeeds",      # Reuters Finance
            "https://feeds.finance.yahoo.com/rss/2.0/headline",       # Yahoo Finance
            "https://www.ft.com/markets?format=rss"                  # Financial Times Markets
        ]
        
        for feed_url in feeds:
            try:
                # Parse feed
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Generate ID
                    article_id = hashlib.md5(entry.get("link", "").encode()).hexdigest()
                    
                    # Skip if already exists
                    if article_id in self.articles:
                        continue
                    try:
                    
                    # Parse date
                        if "published_parsed" in entry:
                            published_at = datetime(*entry.published_parsed[:6])
                        else:
                            published_at = datetime.now()
                    except (ValueError, TypeError):
                        published_at = datetime.now()
                    
                    # Extract content
                    content = entry.get("content", [{}])[0].get("value", "") if "content" in entry else ""
                    if not content and "summary" in entry:
                        content = entry.summary
                    
                    # Create article
                    article = NewsArticle(
                        id=article_id,
                        title=entry.get("title", ""),
                        content=content,
                        summary=entry.get("summary", ""),
                        url=entry.get("link", ""),
                        source=feed.feed.get("title", "RSS Feed"),
                        published_at=published_at,
                        keywords=[]
                    )
                    
                    articles.append(article)
                
                logger.info(f"Fetched {len(articles)} articles from RSS feed: {feed.feed.get('title', feed_url)}")
                
            except Exception as e:
                logger.error(f"Error fetching from RSS feed {feed_url}: {e}")
        
        return articles
    
    async def _process_articles(self, articles: List[NewsArticle]):
        """
        Process new articles (clean, embed, analyze sentiment).
        
        Args:
            articles: List of news articles to process
        """
        for article in articles:
            # Clean text
            article.title = self._clean_text(article.title)
            article.content = self._clean_text(article.content)
            article.summary = self._clean_text(article.summary)
            
            # Extract keywords
            article.keywords = self._extract_keywords(article.title + " " + article.content)
            
            # Analyze sentiment
            article.sentiment_score = self._analyze_sentiment(article.title + " " + article.content)
            
            # Generate embedding
            text_to_embed = article.title + " " + article.summary
            article.embedding = self.model.encode(text_to_embed)
            
            # Add to articles dictionary
            self.articles[article.id] = article
        
        # Limit number of articles
        if len(self.articles) > self.max_articles:
            # Remove oldest articles
            sorted_articles = sorted(
                self.articles.items(),
                key=lambda x: x[1].published_at
            )
            
            # Keep only the newest max_articles
            self.articles = dict(sorted_articles[-self.max_articles:])
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove special characters
        text = re.sub(r'[^\w\s.,!?;:()\-\'"]', '', text)
        
        return text.strip()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction based on frequency
        stop_words = set(stopwords.words('english'))
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter out stop words
        words = [word for word in words if word not in stop_words]
        
        # Count word frequency
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, _ in keywords[:10]]
    
    def _analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment score (-1.0 to 1.0)
        """
        scores = self.sentiment_analyzer.polarity_scores(text)
        return scores['compound']
    
    def _update_index(self):
        """Update FAISS index with current articles."""
        # Reset index
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        
        # Add all embeddings
        embeddings = []
        for article_id, article in self.articles.items():
            if article.embedding is not None:
                embeddings.append(article.embedding)
        
        if embeddings:
            embeddings_array = np.array(embeddings).astype('float32')
            self.index.add(embeddings_array)
        
        # Update ID mappings
        self.id_to_idx = {article_id: i for i, article_id in enumerate(self.articles.keys())}
        self.idx_to_id = {i: article_id for article_id, i in self.id_to_idx.items()}
    
    async def query(self, text: str, assets: List[str] = None, top_k: int = 5) -> List[NewsArticle]:
        """
        Query for relevant news articles.
        
        Args:
            text: Query text
            assets: Optional list of assets to filter by
            top_k: Number of results to return
            
        Returns:
            List of relevant news articles
        """
        # Refresh news if needed
        await self.refresh(assets)
        
        # Encode query
        query_embedding = self.model.encode(text).reshape(1, -1).astype('float32')
        
        # Search index
        if self.index.ntotal == 0:
            logger.warning("No articles in index")
            return []
        
        distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        
        # Get articles
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0:
                continue
                
            article_id = self.idx_to_id.get(idx)
            if article_id and article_id in self.articles:
                article = self.articles[article_id]
                
                # Filter by assets if provided
                if assets and not any(asset.lower() in article.title.lower() or 
                                     asset.lower() in article.content.lower() 
                                     for asset in assets):
                    continue
                
                results.append(article)
        
        return results
    
    async def generate_signals(self, assets: List[str]) -> List[NewsSignal]:
        """
        Generate trading signals for specified assets.
        
        Args:
            assets: List of asset symbols to generate signals for
            
        Returns:
            List of trading signals
        """
        signals = []
        
        for asset in assets:
            # Query for relevant articles
            query = f"{asset} market trading finance news"
            articles = await self.query(query, [asset], top_k=5)
            
            for article in articles:
                # Calculate impact based on recency and sentiment strength
                days_old = (datetime.now() - article.published_at).days
                recency_factor = max(0, 1 - (days_old / 7))  # 0 after 7 days
                
                sentiment_strength = abs(article.sentiment_score)
                
                # Calculate impact (0.0 to 1.0)
                impact = recency_factor * sentiment_strength
                
                # Calculate confidence based on source reliability
                # This is a simplified approach - in a real system, you'd have a database of source reliability
                major_sources = ["Reuters", "Bloomberg", "CNBC", "Financial Times", "Wall Street Journal"]
                source_reliability = 0.8 if any(source in article.source for source in major_sources) else 0.5
                
                confidence = source_reliability * (0.5 + sentiment_strength / 2)
                
                # Create signal
                signal = NewsSignal(
                    asset=asset,
                    sentiment=article.sentiment_score,
                    confidence=confidence,
                    impact=impact,
                    source=article.source,
                    title=article.title,
                    url=article.url,
                    published_at=article.published_at,
                    summary=article.summary,
                    relevance_score=1.0 - (days_old / 30)  # Relevance decreases with age
                )
                
                signals.append(signal)
        
        # Sort by impact * confidence
        signals.sort(key=lambda x: x.impact * x.confidence, reverse=True)
        
        return signals
