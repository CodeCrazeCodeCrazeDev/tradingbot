"""
Knowledge Harvester - Autonomous Internet Browsing for Trading Knowledge

Automatically browses the internet to gather:
- Market sentiment from news and social media
- Trading strategies and techniques
- Economic data and indicators
- AI/ML research and innovations
- Competitor analysis
"""

import asyncio
try:
    import aiohttp
except ImportError:
    aiohttp = None
import json
import re
import hashlib
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import deque
from pathlib import Path
import logging
import random
import time

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """Types of knowledge to harvest"""
    SENTIMENT = auto()
    STRATEGY = auto()
    INDICATOR = auto()
    PATTERN = auto()
    NEWS = auto()
    ECONOMIC = auto()
    AI_RESEARCH = auto()
    CODE_SNIPPET = auto()
    RISK_MANAGEMENT = auto()
    MARKET_ANALYSIS = auto()


@dataclass
class KnowledgeItem:
    """A piece of harvested knowledge"""
    id: str
    type: KnowledgeType
    source: str
    url: str
    title: str
    content: str
    summary: str
    relevance_score: float
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    applied: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type.name,
            'source': self.source,
            'url': self.url,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'relevance_score': self.relevance_score,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'tags': self.tags,
            'applied': self.applied,
        }


@dataclass
class SentimentData:
    """Aggregated sentiment data"""
    symbol: str
    overall_sentiment: float  # -1 to 1
    bullish_count: int
    bearish_count: int
    neutral_count: int
    sources: List[str]
    confidence: float
    timestamp: datetime


class KnowledgeHarvester:
    """
    Autonomous internet browsing system for gathering trading knowledge.
    
    Features:
    - Sentiment analysis from multiple sources
    - Strategy discovery from trading forums
    - AI research paper analysis
    - Code snippet extraction
    - Continuous learning and adaptation
    """
    
    # Free data sources
    SENTIMENT_SOURCES = {
        'reddit': {
            'base_url': 'https://www.reddit.com',
            'subreddits': [
                'wallstreetbets', 'stocks', 'investing', 'cryptocurrency',
                'forex', 'algotrading', 'options', 'daytrading'
            ],
        },
        'stocktwits': {
            'base_url': 'https://api.stocktwits.com/api/2',
        },
        'newsapi': {
            'base_url': 'https://newsapi.org/v2',
            'categories': ['business', 'technology'],
        },
    }
    
    KNOWLEDGE_SOURCES = {
        'arxiv': {
            'base_url': 'http://export.arxiv.org/api/query',
            'categories': ['q-fin', 'cs.LG', 'cs.AI', 'stat.ML'],
        },
        'github': {
            'base_url': 'https://api.github.com',
            'topics': [
                'trading-bot', 'algorithmic-trading', 'quantitative-finance',
                'machine-learning-trading', 'crypto-trading'
            ],
        },
        'medium': {
            'base_url': 'https://medium.com',
            'tags': ['trading', 'cryptocurrency', 'machine-learning', 'finance'],
        },
    }
    
    # Keywords for relevance scoring
    TRADING_KEYWORDS = {
        'high_value': [
            'alpha', 'edge', 'profitable', 'strategy', 'backtest',
            'sharpe', 'drawdown', 'risk-adjusted', 'momentum', 'mean reversion',
            'machine learning', 'neural network', 'reinforcement learning',
            'order flow', 'market microstructure', 'execution', 'slippage',
        ],
        'medium_value': [
            'indicator', 'signal', 'entry', 'exit', 'stop loss', 'take profit',
            'position sizing', 'portfolio', 'diversification', 'correlation',
            'volatility', 'trend', 'breakout', 'support', 'resistance',
        ],
        'low_value': [
            'buy', 'sell', 'bullish', 'bearish', 'long', 'short',
            'price', 'volume', 'chart', 'analysis', 'technical',
        ],
    }
    
    def __init__(
        self,
        db_path: str = "knowledge/knowledge_base.db",
        harvest_interval: int = 300,  # 5 minutes
        max_items_per_source: int = 50,
    ):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.harvest_interval = harvest_interval
        self.max_items_per_source = max_items_per_source
        
        # State
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Knowledge storage
        self.knowledge_cache: Dict[str, KnowledgeItem] = {}
        self.sentiment_cache: Dict[str, SentimentData] = {}
        self.harvested_urls: Set[str] = set()
        
        # Statistics
        self.stats = {
            'total_harvested': 0,
            'total_applied': 0,
            'sources_checked': 0,
            'errors': 0,
            'last_harvest': None,
        }
        
        # Initialize database
        self._init_database()
        
        logger.info("KnowledgeHarvester initialized")
    
    def _init_database(self) -> None:
        """Initialize SQLite database for knowledge storage"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge (
                id TEXT PRIMARY KEY,
                type TEXT,
                source TEXT,
                url TEXT,
                title TEXT,
                content TEXT,
                summary TEXT,
                relevance_score REAL,
                confidence REAL,
                timestamp TEXT,
                metadata TEXT,
                tags TEXT,
                applied INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sentiment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                overall_sentiment REAL,
                bullish_count INTEGER,
                bearish_count INTEGER,
                neutral_count INTEGER,
                sources TEXT,
                confidence REAL,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge(type)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_knowledge_timestamp ON knowledge(timestamp)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sentiment_symbol ON sentiment(symbol)
        ''')
        
        conn.commit()
        conn.close()
    
    async def start(self) -> None:
        """Start the knowledge harvesting loop"""
        if self.is_running:
            return
        
        self.is_running = True
        self._session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        self._task = asyncio.create_task(self._harvest_loop())
        logger.info("KnowledgeHarvester started")
    
    async def stop(self) -> None:
        """Stop the knowledge harvesting"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._session:
            await self._session.close()
        logger.info("KnowledgeHarvester stopped")
    
    async def _harvest_loop(self) -> None:
        """Main harvesting loop"""
        while self.is_running:
            try:
                await self._harvest_all()
                self.stats['last_harvest'] = datetime.now().isoformat()
            except Exception as e:
                logger.error(f"Harvest error: {e}")
                self.stats['errors'] += 1
            
            await asyncio.sleep(self.harvest_interval)
    
    async def _harvest_all(self) -> None:
        """Harvest from all sources"""
        tasks = [
            self._harvest_reddit_sentiment(),
            self._harvest_news(),
            self._harvest_arxiv_research(),
            self._harvest_github_strategies(),
            self._harvest_economic_data(),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Harvest task error: {result}")
                self.stats['errors'] += 1
    
    async def _harvest_reddit_sentiment(self) -> List[KnowledgeItem]:
        """Harvest sentiment from Reddit"""
        items = []
        
        for subreddit in self.SENTIMENT_SOURCES['reddit']['subreddits']:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=25"
                
                async with self._session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = data.get('data', {}).get('children', [])
                        
                        for post in posts:
                            post_data = post.get('data', {})
                            item = await self._process_reddit_post(post_data, subreddit)
                            if item:
                                items.append(item)
                                self._save_knowledge(item)
                
                self.stats['sources_checked'] += 1
                await asyncio.sleep(2)  # Rate limiting
                
            except Exception as e:
                logger.debug(f"Reddit harvest error for {subreddit}: {e}")
        
        return items
    
    async def _process_reddit_post(
        self,
        post: Dict[str, Any],
        subreddit: str
    ) -> Optional[KnowledgeItem]:
        """Process a Reddit post into a knowledge item"""
        url = f"https://reddit.com{post.get('permalink', '')}"
        
        if url in self.harvested_urls:
            return None
        
        title = post.get('title', '')
        content = post.get('selftext', '')
        score = post.get('score', 0)
        
        # Calculate relevance
        relevance = self._calculate_relevance(title + ' ' + content)
        
        if relevance < 0.3:
            return None
        
        # Analyze sentiment
        sentiment = self._analyze_sentiment(title + ' ' + content)
        
        item = KnowledgeItem(
            id=hashlib.md5(url.encode()).hexdigest(),
            type=KnowledgeType.SENTIMENT,
            source=f"reddit/{subreddit}",
            url=url,
            title=title,
            content=content[:2000],
            summary=self._generate_summary(content),
            relevance_score=relevance,
            confidence=min(1.0, score / 1000),
            timestamp=datetime.now(),
            metadata={
                'score': score,
                'sentiment': sentiment,
                'subreddit': subreddit,
            },
            tags=self._extract_tags(title + ' ' + content),
        )
        
        self.harvested_urls.add(url)
        self.stats['total_harvested'] += 1
        
        return item
    
    async def _harvest_news(self) -> List[KnowledgeItem]:
        """Harvest news from various sources"""
        items = []
        
        # Try free news sources
        news_sources = [
            'https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US',
            'https://www.investing.com/rss/news.rss',
        ]
        
        for url in news_sources:
            try:
                async with self._session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Parse RSS/XML
                        news_items = self._parse_rss(content)
                        
                        for news in news_items[:10]:
                            item = KnowledgeItem(
                                id=hashlib.md5(news['link'].encode()).hexdigest(),
                                type=KnowledgeType.NEWS,
                                source='news_feed',
                                url=news['link'],
                                title=news['title'],
                                content=news.get('description', ''),
                                summary=news.get('description', '')[:200],
                                relevance_score=self._calculate_relevance(
                                    news['title'] + ' ' + news.get('description', '')
                                ),
                                confidence=0.7,
                                timestamp=datetime.now(),
                                metadata={'source_url': url},
                                tags=self._extract_tags(news['title']),
                            )
                            items.append(item)
                            self._save_knowledge(item)
                
                self.stats['sources_checked'] += 1
                
            except Exception as e:
                logger.debug(f"News harvest error: {e}")
        
        return items
    
    def _parse_rss(self, content: str) -> List[Dict[str, str]]:
        """Parse RSS feed content"""
        items = []
        
        # Simple regex-based parsing
        item_pattern = re.compile(r'<item>(.*?)</item>', re.DOTALL)
        title_pattern = re.compile(r'<title>(.*?)</title>', re.DOTALL)
        link_pattern = re.compile(r'<link>(.*?)</link>', re.DOTALL)
        desc_pattern = re.compile(r'<description>(.*?)</description>', re.DOTALL)
        
        for item_match in item_pattern.finditer(content):
            item_content = item_match.group(1)
            
            title_match = title_pattern.search(item_content)
            link_match = link_pattern.search(item_content)
            desc_match = desc_pattern.search(item_content)
            
            if title_match and link_match:
                items.append({
                    'title': self._clean_html(title_match.group(1)),
                    'link': link_match.group(1).strip(),
                    'description': self._clean_html(desc_match.group(1)) if desc_match else '',
                })
        
        return items
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'&[a-zA-Z]+;', ' ', clean)
        return clean.strip()
    
    async def _harvest_arxiv_research(self) -> List[KnowledgeItem]:
        """Harvest AI/ML research from arXiv"""
        items = []
        
        search_queries = [
            'algorithmic trading machine learning',
            'reinforcement learning finance',
            'deep learning stock prediction',
            'neural network trading',
            'quantitative finance AI',
        ]
        
        for query in search_queries[:2]:  # Limit queries
            try:
                url = f"http://export.arxiv.org/api/query?search_query=all:{query.replace(' ', '+')}&max_results=10"
                
                async with self._session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        papers = self._parse_arxiv(content)
                        
                        for paper in papers:
                            if paper['id'] in self.harvested_urls:
                                continue
                            
                            item = KnowledgeItem(
                                id=hashlib.md5(paper['id'].encode()).hexdigest(),
                                type=KnowledgeType.AI_RESEARCH,
                                source='arxiv',
                                url=paper['id'],
                                title=paper['title'],
                                content=paper['summary'],
                                summary=paper['summary'][:500],
                                relevance_score=self._calculate_relevance(
                                    paper['title'] + ' ' + paper['summary']
                                ),
                                confidence=0.9,  # Academic sources are reliable
                                timestamp=datetime.now(),
                                metadata={
                                    'authors': paper.get('authors', []),
                                    'categories': paper.get('categories', []),
                                },
                                tags=['research', 'ai', 'ml'] + self._extract_tags(paper['title']),
                            )
                            items.append(item)
                            self._save_knowledge(item)
                            self.harvested_urls.add(paper['id'])
                
                self.stats['sources_checked'] += 1
                await asyncio.sleep(3)  # Rate limiting
                
            except Exception as e:
                logger.debug(f"arXiv harvest error: {e}")
        
        return items
    
    def _parse_arxiv(self, content: str) -> List[Dict[str, Any]]:
        """Parse arXiv API response"""
        papers = []
        
        entry_pattern = re.compile(r'<entry>(.*?)</entry>', re.DOTALL)
        id_pattern = re.compile(r'<id>(.*?)</id>')
        title_pattern = re.compile(r'<title>(.*?)</title>', re.DOTALL)
        summary_pattern = re.compile(r'<summary>(.*?)</summary>', re.DOTALL)
        author_pattern = re.compile(r'<name>(.*?)</name>')
        
        for entry_match in entry_pattern.finditer(content):
            entry = entry_match.group(1)
            
            id_match = id_pattern.search(entry)
            title_match = title_pattern.search(entry)
            summary_match = summary_pattern.search(entry)
            authors = author_pattern.findall(entry)
            
            if id_match and title_match:
                papers.append({
                    'id': id_match.group(1),
                    'title': ' '.join(title_match.group(1).split()),
                    'summary': ' '.join(summary_match.group(1).split()) if summary_match else '',
                    'authors': authors,
                })
        
        return papers
    
    async def _harvest_github_strategies(self) -> List[KnowledgeItem]:
        """Harvest trading strategies from GitHub"""
        items = []
        
        topics = ['trading-bot', 'algorithmic-trading', 'quantitative-trading']
        
        for topic in topics:
            try:
                url = f"https://api.github.com/search/repositories?q=topic:{topic}&sort=stars&per_page=10"
                
                async with self._session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        repos = data.get('items', [])
                        
                        for repo in repos:
                            repo_url = repo.get('html_url', '')
                            if repo_url in self.harvested_urls:
                                continue
                            
                            item = KnowledgeItem(
                                id=hashlib.md5(repo_url.encode()).hexdigest(),
                                type=KnowledgeType.STRATEGY,
                                source='github',
                                url=repo_url,
                                title=repo.get('name', ''),
                                content=repo.get('description', '') or '',
                                summary=repo.get('description', '') or '',
                                relevance_score=self._calculate_relevance(
                                    repo.get('name', '') + ' ' + (repo.get('description', '') or '')
                                ),
                                confidence=min(1.0, repo.get('stargazers_count', 0) / 1000),
                                timestamp=datetime.now(),
                                metadata={
                                    'stars': repo.get('stargazers_count', 0),
                                    'language': repo.get('language', ''),
                                    'topics': repo.get('topics', []),
                                },
                                tags=['github', 'code', topic],
                            )
                            items.append(item)
                            self._save_knowledge(item)
                            self.harvested_urls.add(repo_url)
                
                self.stats['sources_checked'] += 1
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.debug(f"GitHub harvest error: {e}")
        
        return items
    
    async def _harvest_economic_data(self) -> List[KnowledgeItem]:
        """Harvest economic indicators from FRED"""
        items = []
        
        # FRED series IDs for key economic indicators
        series = [
            ('GDP', 'Gross Domestic Product'),
            ('UNRATE', 'Unemployment Rate'),
            ('CPIAUCSL', 'Consumer Price Index'),
            ('FEDFUNDS', 'Federal Funds Rate'),
            ('DGS10', '10-Year Treasury Rate'),
        ]
        
        for series_id, name in series:
            try:
                url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key=DEMO_KEY&file_type=json&limit=1&sort_order=desc"
                
                async with self._session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        observations = data.get('observations', [])
                        
                        if observations:
                            obs = observations[0]
                            item = KnowledgeItem(
                                id=f"fred_{series_id}_{obs.get('date', '')}",
                                type=KnowledgeType.ECONOMIC,
                                source='fred',
                                url=f"https://fred.stlouisfed.org/series/{series_id}",
                                title=f"{name} ({series_id})",
                                content=f"Value: {obs.get('value', 'N/A')} as of {obs.get('date', 'N/A')}",
                                summary=f"{name}: {obs.get('value', 'N/A')}",
                                relevance_score=0.8,
                                confidence=1.0,  # Official data
                                timestamp=datetime.now(),
                                metadata={
                                    'series_id': series_id,
                                    'value': obs.get('value', ''),
                                    'date': obs.get('date', ''),
                                },
                                tags=['economic', 'indicator', series_id.lower()],
                            )
                            items.append(item)
                            self._save_knowledge(item)
                
                self.stats['sources_checked'] += 1
                
            except Exception as e:
                logger.debug(f"FRED harvest error: {e}")
        
        return items
    
    def _calculate_relevance(self, text: str) -> float:
        """Calculate relevance score for text"""
        text_lower = text.lower()
        score = 0.0
        
        for keyword in self.TRADING_KEYWORDS['high_value']:
            if keyword in text_lower:
                score += 0.15
        
        for keyword in self.TRADING_KEYWORDS['medium_value']:
            if keyword in text_lower:
                score += 0.08
        
        for keyword in self.TRADING_KEYWORDS['low_value']:
            if keyword in text_lower:
                score += 0.03
        
        return min(1.0, score)
    
    def _analyze_sentiment(self, text: str) -> float:
        """Simple sentiment analysis (-1 to 1)"""
        text_lower = text.lower()
        
        bullish_words = [
            'bullish', 'buy', 'long', 'moon', 'rocket', 'gains', 'profit',
            'up', 'rise', 'growth', 'positive', 'strong', 'breakout',
        ]
        bearish_words = [
            'bearish', 'sell', 'short', 'crash', 'dump', 'loss', 'down',
            'fall', 'decline', 'negative', 'weak', 'breakdown', 'fear',
        ]
        
        bullish_count = sum(1 for word in bullish_words if word in text_lower)
        bearish_count = sum(1 for word in bearish_words if word in text_lower)
        
        total = bullish_count + bearish_count
        if total == 0:
            return 0.0
        
        return (bullish_count - bearish_count) / total
    
    def _generate_summary(self, text: str) -> str:
        """Generate a summary of the text"""
        sentences = text.split('.')
        if len(sentences) <= 2:
            return text[:200]
        return '. '.join(sentences[:2]) + '.'
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text"""
        tags = []
        text_lower = text.lower()
        
        # Asset tags
        assets = ['btc', 'eth', 'bitcoin', 'ethereum', 'spy', 'qqq', 'forex', 'crypto']
        for asset in assets:
            if asset in text_lower:
                tags.append(asset)
        
        # Strategy tags
        strategies = ['momentum', 'mean reversion', 'trend', 'breakout', 'scalping']
        for strategy in strategies:
            if strategy in text_lower:
                tags.append(strategy.replace(' ', '_'))
        
        return tags[:5]
    
    def _save_knowledge(self, item: KnowledgeItem) -> None:
        """Save knowledge item to database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO knowledge
                (id, type, source, url, title, content, summary, relevance_score,
                 confidence, timestamp, metadata, tags, applied)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.id,
                item.type.name,
                item.source,
                item.url,
                item.title,
                item.content,
                item.summary,
                item.relevance_score,
                item.confidence,
                item.timestamp.isoformat(),
                json.dumps(item.metadata),
                json.dumps(item.tags),
                1 if item.applied else 0,
            ))
            
            conn.commit()
            conn.close()
            
            # Update cache
            self.knowledge_cache[item.id] = item
            
        except Exception as e:
            logger.error(f"Failed to save knowledge: {e}")
    
    def get_sentiment(self, symbol: str = None) -> Dict[str, Any]:
        """Get aggregated sentiment data"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Get recent sentiment items
        cursor.execute('''
            SELECT content, metadata, timestamp FROM knowledge
            WHERE type = 'SENTIMENT'
            ORDER BY timestamp DESC
            LIMIT 100
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return {'overall': 0.0, 'confidence': 0.0, 'count': 0}
        
        sentiments = []
        for row in rows:
            try:
                metadata = json.loads(row[1])
                sentiments.append(metadata.get('sentiment', 0))
            except Exception:
                pass
        
        if not sentiments:
            return {'overall': 0.0, 'confidence': 0.0, 'count': 0}
        
        return {
            'overall': sum(sentiments) / len(sentiments),
            'confidence': min(1.0, len(sentiments) / 50),
            'count': len(sentiments),
            'bullish_pct': len([s for s in sentiments if s > 0]) / len(sentiments) * 100,
            'bearish_pct': len([s for s in sentiments if s < 0]) / len(sentiments) * 100,
        }
    
    def get_latest_knowledge(
        self,
        knowledge_type: KnowledgeType = None,
        limit: int = 10
    ) -> List[KnowledgeItem]:
        """Get latest knowledge items"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        if knowledge_type:
            cursor.execute('''
                SELECT * FROM knowledge
                WHERE type = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (knowledge_type.name, limit))
        else:
            cursor.execute('''
                SELECT * FROM knowledge
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        items = []
        for row in rows:
            try:
                items.append(KnowledgeItem(
                    id=row[0],
                    type=KnowledgeType[row[1]],
                    source=row[2],
                    url=row[3],
                    title=row[4],
                    content=row[5],
                    summary=row[6],
                    relevance_score=row[7],
                    confidence=row[8],
                    timestamp=datetime.fromisoformat(row[9]),
                    metadata=json.loads(row[10]) if row[10] else {},
                    tags=json.loads(row[11]) if row[11] else [],
                    applied=bool(row[12]),
                ))
            except Exception as e:
                logger.debug(f"Error parsing knowledge item: {e}")
        
        return items
    
    def get_actionable_insights(self) -> List[Dict[str, Any]]:
        """Get actionable trading insights from harvested knowledge"""
        insights = []
        
        # Get high-relevance items
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM knowledge
            WHERE relevance_score > 0.6 AND applied = 0
            ORDER BY relevance_score DESC, timestamp DESC
            LIMIT 20
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            try:
                insights.append({
                    'id': row[0],
                    'type': row[1],
                    'title': row[4],
                    'summary': row[6],
                    'relevance': row[7],
                    'confidence': row[8],
                    'source': row[2],
                    'url': row[3],
                    'action': self._suggest_action(row[1], row[5]),
                })
            except Exception:
                pass
        
        return insights
    
    def _suggest_action(self, knowledge_type: str, content: str) -> str:
        """Suggest an action based on knowledge type and content"""
        if knowledge_type == 'STRATEGY':
            return "Review and potentially integrate this trading strategy"
        elif knowledge_type == 'AI_RESEARCH':
            return "Analyze research for applicable ML techniques"
        elif knowledge_type == 'SENTIMENT':
            return "Factor into market sentiment analysis"
        elif knowledge_type == 'NEWS':
            return "Monitor for market impact"
        elif knowledge_type == 'ECONOMIC':
            return "Update economic indicators model"
        return "Review for potential application"
    
    def mark_applied(self, item_id: str) -> None:
        """Mark a knowledge item as applied"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE knowledge SET applied = 1 WHERE id = ?
        ''', (item_id,))
        
        conn.commit()
        conn.close()
        
        self.stats['total_applied'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get harvester statistics"""
        return {
            **self.stats,
            'cache_size': len(self.knowledge_cache),
            'urls_harvested': len(self.harvested_urls),
        }
