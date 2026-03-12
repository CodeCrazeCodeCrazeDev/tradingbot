"""
Internet Research Engine - Autonomous Knowledge Acquisition
============================================================

Connects to the internet to:
1. Search for trading books, papers, strategies
2. Find and evaluate AI models
3. Discover new trading techniques
4. Learn from financial news and analysis
5. Access academic research (arXiv, SSRN, etc.)
6. Monitor competitor strategies
7. Track market sentiment globally
"""

import asyncio
try:
    import aiohttp
except ImportError:
    aiohttp = None
import logging
import json
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import re
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class ResearchType(Enum):
    """Types of research the engine can perform"""
    TRADING_STRATEGY = "trading_strategy"
    ACADEMIC_PAPER = "academic_paper"
    AI_MODEL = "ai_model"
    MARKET_NEWS = "market_news"
    BOOK = "book"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    SENTIMENT = "sentiment"
    ECONOMIC_DATA = "economic_data"
    TECHNICAL_ANALYSIS = "technical_analysis"
    QUANTITATIVE_RESEARCH = "quantitative_research"


class SourceQuality(Enum):
    """Quality rating of sources"""
    ACADEMIC = "academic"  # Peer-reviewed
    PROFESSIONAL = "professional"  # Industry experts
    COMMUNITY = "community"  # Forums, blogs
    NEWS = "news"  # News outlets
    SOCIAL = "social"  # Social media
    UNKNOWN = "unknown"


@dataclass
class ResearchResult:
    """A single research result"""
    result_id: str
    research_type: ResearchType
    title: str
    summary: str
    source_url: str
    source_quality: SourceQuality
    relevance_score: float  # 0-1
    confidence: float  # 0-1
    
    # Content
    key_insights: List[str]
    actionable_items: List[str]
    trading_implications: List[str]
    
    # Metadata
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    citations: int = 0
    
    # Processing
    processed_at: datetime = field(default_factory=datetime.now)
    applied: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'result_id': self.result_id,
            'type': self.research_type.value,
            'title': self.title,
            'summary': self.summary,
            'source_url': self.source_url,
            'quality': self.source_quality.value,
            'relevance': self.relevance_score,
            'confidence': self.confidence,
            'insights': self.key_insights,
            'actions': self.actionable_items,
            'implications': self.trading_implications
        }


@dataclass
class ResearchQuery:
    """A research query"""
    query: str
    research_type: ResearchType
    priority: int = 1
    max_results: int = 10
    min_quality: SourceQuality = SourceQuality.COMMUNITY
    created_at: datetime = field(default_factory=datetime.now)


class InternetResearchEngine:
    """
    Autonomous Internet Research Engine
    
    Capabilities:
    - Search academic databases (arXiv, SSRN, Google Scholar)
    - Find trading strategies and backtests
    - Discover AI/ML models for trading
    - Monitor financial news globally
    - Track market sentiment
    - Learn from books and courses
    - Analyze competitor strategies
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # API endpoints (free/public APIs)
        self.endpoints = {
            'arxiv': 'http://export.arxiv.org/api/query',
            'news_api': 'https://newsapi.org/v2/everything',
            'reddit': 'https://www.reddit.com/r/{subreddit}/search.json',
            'github': 'https://api.github.com/search/repositories',
            'duckduckgo': 'https://api.duckduckgo.com/',
            'wikipedia': 'https://en.wikipedia.org/api/rest_v1/page/summary/',
            'fred': 'https://api.stlouisfed.org/fred/series/observations',
            'coingecko': 'https://api.coingecko.com/api/v3',
            'alpha_vantage': 'https://www.alphavantage.co/query',
            'yahoo_finance': 'https://query1.finance.yahoo.com/v8/finance/chart/',
        }
        
        # API keys (from config or environment)
        self.api_keys = self.config.get('api_keys', {})
        
        # Research cache
        self.cache_path = Path(self.config.get('cache_path', 'research_cache'))
        self.cache_path.mkdir(parents=True, exist_ok=True)
        
        # Knowledge base
        self.knowledge_base: List[ResearchResult] = []
        self.max_knowledge = 10000
        
        # Research queue
        self.research_queue: List[ResearchQuery] = []
        
        # Statistics
        self.stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'results_found': 0,
            'insights_extracted': 0,
            'strategies_discovered': 0,
            'models_found': 0
        }
        
        # Session for async requests
        self._session: Optional[aiohttp.ClientSession] = None
        
        logger.info("Internet Research Engine initialized")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self):
        """Close the session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def research(
        self,
        query: str,
        research_type: ResearchType = ResearchType.TRADING_STRATEGY,
        max_results: int = 10
    ) -> List[ResearchResult]:
        """
        Perform comprehensive research on a topic
        
        Args:
            query: Search query
            research_type: Type of research
            max_results: Maximum results to return
            
        Returns:
            List of research results
        """
        logger.info(f"Researching: {query} (type: {research_type.value})")
        self.stats['total_searches'] += 1
        
        results = []
        
        try:
            # Search multiple sources based on research type
            if research_type == ResearchType.ACADEMIC_PAPER:
                results.extend(await self._search_arxiv(query, max_results))
                
            elif research_type == ResearchType.TRADING_STRATEGY:
                results.extend(await self._search_trading_strategies(query, max_results))
                
            elif research_type == ResearchType.AI_MODEL:
                results.extend(await self._search_ai_models(query, max_results))
                
            elif research_type == ResearchType.MARKET_NEWS:
                results.extend(await self._search_news(query, max_results))
                
            elif research_type == ResearchType.BOOK:
                results.extend(await self._search_books(query, max_results))
                
            elif research_type == ResearchType.SENTIMENT:
                results.extend(await self._search_sentiment(query, max_results))
                
            elif research_type == ResearchType.ECONOMIC_DATA:
                results.extend(await self._search_economic_data(query, max_results))
                
            else:
                # General search
                results.extend(await self._general_search(query, max_results))
            
            # Process and rank results
            results = self._rank_results(results)[:max_results]
            
            # Store in knowledge base
            for result in results:
                self._add_to_knowledge_base(result)
            
            self.stats['successful_searches'] += 1
            self.stats['results_found'] += len(results)
            
            logger.info(f"Found {len(results)} results for: {query}")
            
        except Exception as e:
            logger.error(f"Research failed: {e}")
        
        return results
    
    async def _search_arxiv(self, query: str, max_results: int) -> List[ResearchResult]:
        """Search arXiv for academic papers"""
        results = []
        
        try:
            session = await self._get_session()
            
            # Build arXiv query
            search_query = f"all:{query} AND (cat:q-fin.* OR cat:cs.LG OR cat:stat.ML)"
            params = {
                'search_query': search_query,
                'start': 0,
                'max_results': max_results,
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }
            
            async with session.get(self.endpoints['arxiv'], params=params) as response:
                if response.status == 200:
                    content = await response.text()
                    results = self._parse_arxiv_response(content, query)
                    
        except Exception as e:
            logger.error(f"arXiv search failed: {e}")
        
        return results
    
    def _parse_arxiv_response(self, xml_content: str, query: str) -> List[ResearchResult]:
        """Parse arXiv XML response"""
        results = []
        
        try:
            # Simple XML parsing (avoid heavy dependencies)
            entries = re.findall(r'<entry>(.*?)</entry>', xml_content, re.DOTALL)
            
            for entry in entries:
                title_match = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
                summary_match = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
                id_match = re.search(r'<id>(.*?)</id>', entry)
                author_match = re.search(r'<name>(.*?)</name>', entry)
                
                if title_match and summary_match:
                    title = title_match.group(1).strip().replace('\n', ' ')
                    summary = summary_match.group(1).strip().replace('\n', ' ')
                    url = id_match.group(1) if id_match else ""
                    author = author_match.group(1) if author_match else "Unknown"
                    
                    # Extract insights
                    insights = self._extract_insights(summary)
                    implications = self._extract_trading_implications(summary)
                    
                    result = ResearchResult(
                        result_id=hashlib.md5(url.encode()).hexdigest()[:12],
                        research_type=ResearchType.ACADEMIC_PAPER,
                        title=title,
                        summary=summary[:500],
                        source_url=url,
                        source_quality=SourceQuality.ACADEMIC,
                        relevance_score=self._calculate_relevance(query, title + summary),
                        confidence=0.85,
                        key_insights=insights,
                        actionable_items=self._extract_actions(summary),
                        trading_implications=implications,
                        author=author
                    )
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"arXiv parsing failed: {e}")
        
        return results
    
    async def _search_trading_strategies(self, query: str, max_results: int) -> List[ResearchResult]:
        """Search for trading strategies"""
        results = []
        
        try:
            # Search GitHub for trading strategies
            github_results = await self._search_github(
                f"{query} trading strategy backtest",
                max_results
            )
            results.extend(github_results)
            
            # Search Reddit for strategies
            reddit_results = await self._search_reddit(
                query,
                ['algotrading', 'quantfinance', 'wallstreetbets'],
                max_results
            )
            results.extend(reddit_results)
            
        except Exception as e:
            logger.error(f"Trading strategy search failed: {e}")
        
        return results
    
    async def _search_github(self, query: str, max_results: int) -> List[ResearchResult]:
        """Search GitHub for trading-related repositories"""
        results = []
        
        try:
            session = await self._get_session()
            
            params = {
                'q': query,
                'sort': 'stars',
                'order': 'desc',
                'per_page': max_results
            }
            
            headers = {'Accept': 'application/vnd.github.v3+json'}
            if 'github' in self.api_keys:
                headers['Authorization'] = f"token {self.api_keys['github']}"
            
            async with session.get(
                self.endpoints['github'],
                params=params,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for item in data.get('items', [])[:max_results]:
                        result = ResearchResult(
                            result_id=f"gh_{item['id']}",
                            research_type=ResearchType.TRADING_STRATEGY,
                            title=item['name'],
                            summary=item.get('description', 'No description')[:500],
                            source_url=item['html_url'],
                            source_quality=SourceQuality.COMMUNITY,
                            relevance_score=min(1.0, item['stargazers_count'] / 1000),
                            confidence=0.7,
                            key_insights=[
                                f"Stars: {item['stargazers_count']}",
                                f"Language: {item.get('language', 'Unknown')}",
                                f"Forks: {item['forks_count']}"
                            ],
                            actionable_items=["Review code", "Test strategy", "Adapt to our system"],
                            trading_implications=["Potential new strategy source"],
                            author=item['owner']['login']
                        )
                        results.append(result)
                        
        except Exception as e:
            logger.error(f"GitHub search failed: {e}")
        
        return results
    
    async def _search_reddit(
        self,
        query: str,
        subreddits: List[str],
        max_results: int
    ) -> List[ResearchResult]:
        """Search Reddit for trading discussions"""
        results = []
        
        try:
            session = await self._get_session()
            
            for subreddit in subreddits:
                url = self.endpoints['reddit'].format(subreddit=subreddit)
                params = {
                    'q': query,
                    'sort': 'relevance',
                    't': 'year',
                    'limit': max_results // len(subreddits)
                }
                
                headers = {'User-Agent': 'TradingBot/1.0'}
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for post in data.get('data', {}).get('children', []):
                            post_data = post['data']
                            
                            result = ResearchResult(
                                result_id=f"reddit_{post_data['id']}",
                                research_type=ResearchType.TRADING_STRATEGY,
                                title=post_data['title'],
                                summary=post_data.get('selftext', '')[:500],
                                source_url=f"https://reddit.com{post_data['permalink']}",
                                source_quality=SourceQuality.COMMUNITY,
                                relevance_score=min(1.0, post_data['score'] / 500),
                                confidence=0.5,
                                key_insights=self._extract_insights(post_data.get('selftext', '')),
                                actionable_items=[],
                                trading_implications=[],
                                author=post_data['author']
                            )
                            results.append(result)
                            
        except Exception as e:
            logger.error(f"Reddit search failed: {e}")
        
        return results
    
    async def _search_ai_models(self, query: str, max_results: int) -> List[ResearchResult]:
        """Search for AI/ML models for trading"""
        results = []
        
        try:
            # Search GitHub for ML trading models
            github_results = await self._search_github(
                f"{query} machine learning trading neural network",
                max_results
            )
            
            for result in github_results:
                result.research_type = ResearchType.AI_MODEL
                results.append(result)
            
            # Search arXiv for ML papers
            arxiv_results = await self._search_arxiv(
                f"{query} deep learning trading",
                max_results
            )
            
            for result in arxiv_results:
                result.research_type = ResearchType.AI_MODEL
                results.append(result)
                
        except Exception as e:
            logger.error(f"AI model search failed: {e}")
        
        return results
    
    async def _search_news(self, query: str, max_results: int) -> List[ResearchResult]:
        """Search financial news"""
        results = []
        
        try:
            session = await self._get_session()
            
            # Use free news sources
            # DuckDuckGo instant answers
            params = {
                'q': f"{query} finance trading",
                'format': 'json',
                'no_html': 1
            }
            
            async with session.get(self.endpoints['duckduckgo'], params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process related topics
                    for topic in data.get('RelatedTopics', [])[:max_results]:
                        if isinstance(topic, dict) and 'Text' in topic:
                            result = ResearchResult(
                                result_id=hashlib.md5(topic.get('FirstURL', '').encode()).hexdigest()[:12],
                                research_type=ResearchType.MARKET_NEWS,
                                title=topic.get('Text', '')[:100],
                                summary=topic.get('Text', ''),
                                source_url=topic.get('FirstURL', ''),
                                source_quality=SourceQuality.NEWS,
                                relevance_score=0.6,
                                confidence=0.6,
                                key_insights=[topic.get('Text', '')[:200]],
                                actionable_items=[],
                                trading_implications=[]
                            )
                            results.append(result)
                            
        except Exception as e:
            logger.error(f"News search failed: {e}")
        
        return results
    
    async def _search_books(self, query: str, max_results: int) -> List[ResearchResult]:
        """Search for trading books"""
        results = []
        
        # Curated list of essential trading books
        essential_books = [
            {
                'title': 'Advances in Financial Machine Learning',
                'author': 'Marcos Lopez de Prado',
                'insights': ['Meta-labeling', 'Triple barrier method', 'Feature importance'],
                'implications': ['ML-based trading strategies', 'Proper backtesting']
            },
            {
                'title': 'Quantitative Trading',
                'author': 'Ernest Chan',
                'insights': ['Mean reversion', 'Momentum strategies', 'Risk management'],
                'implications': ['Systematic trading approach', 'Position sizing']
            },
            {
                'title': 'Algorithmic Trading',
                'author': 'Ernest Chan',
                'insights': ['Market microstructure', 'Execution algorithms', 'HFT'],
                'implications': ['Optimal execution', 'Slippage reduction']
            },
            {
                'title': 'Trading and Exchanges',
                'author': 'Larry Harris',
                'insights': ['Market structure', 'Order types', 'Liquidity'],
                'implications': ['Understanding market dynamics', 'Better execution']
            },
            {
                'title': 'Machine Learning for Asset Managers',
                'author': 'Marcos Lopez de Prado',
                'insights': ['Clustering algorithms', 'Portfolio optimization', 'Overfitting'],
                'implications': ['ML in portfolio management', 'Robust strategies']
            }
        ]
        
        for book in essential_books:
            if query.lower() in book['title'].lower() or any(
                query.lower() in insight.lower() for insight in book['insights']
            ):
                result = ResearchResult(
                    result_id=hashlib.md5(book['title'].encode()).hexdigest()[:12],
                    research_type=ResearchType.BOOK,
                    title=book['title'],
                    summary=f"By {book['author']}. Key concepts: {', '.join(book['insights'])}",
                    source_url=f"https://www.amazon.com/s?k={quote_plus(book['title'])}",
                    source_quality=SourceQuality.PROFESSIONAL,
                    relevance_score=0.9,
                    confidence=0.95,
                    key_insights=book['insights'],
                    actionable_items=['Study concepts', 'Implement strategies', 'Backtest ideas'],
                    trading_implications=book['implications'],
                    author=book['author']
                )
                results.append(result)
        
        return results[:max_results]
    
    async def _search_sentiment(self, query: str, max_results: int) -> List[ResearchResult]:
        """Search for market sentiment"""
        results = []
        
        try:
            # Search Reddit for sentiment
            reddit_results = await self._search_reddit(
                query,
                ['stocks', 'investing', 'cryptocurrency'],
                max_results
            )
            
            for result in reddit_results:
                result.research_type = ResearchType.SENTIMENT
                # Analyze sentiment from title/summary
                sentiment = self._analyze_sentiment(result.title + " " + result.summary)
                result.key_insights.append(f"Sentiment: {sentiment}")
                results.append(result)
                
        except Exception as e:
            logger.error(f"Sentiment search failed: {e}")
        
        return results
    
    async def _search_economic_data(self, query: str, max_results: int) -> List[ResearchResult]:
        """Search for economic data and indicators"""
        results = []
        
        # Key economic indicators
        indicators = {
            'GDP': 'Gross Domestic Product',
            'CPI': 'Consumer Price Index (Inflation)',
            'UNRATE': 'Unemployment Rate',
            'FEDFUNDS': 'Federal Funds Rate',
            'DGS10': '10-Year Treasury Rate',
            'VIXCLS': 'VIX Volatility Index'
        }
        
        for code, name in indicators.items():
            if query.lower() in name.lower() or query.lower() in code.lower():
                result = ResearchResult(
                    result_id=f"econ_{code}",
                    research_type=ResearchType.ECONOMIC_DATA,
                    title=f"{name} ({code})",
                    summary=f"Key economic indicator: {name}. Use FRED API for data.",
                    source_url=f"https://fred.stlouisfed.org/series/{code}",
                    source_quality=SourceQuality.ACADEMIC,
                    relevance_score=0.9,
                    confidence=0.95,
                    key_insights=[f"Track {name} for macro analysis"],
                    actionable_items=['Fetch latest data', 'Analyze trends', 'Incorporate in models'],
                    trading_implications=['Macro-aware trading', 'Risk adjustment']
                )
                results.append(result)
        
        return results[:max_results]
    
    async def _general_search(self, query: str, max_results: int) -> List[ResearchResult]:
        """General web search"""
        results = []
        
        # Combine multiple sources
        arxiv_results = await self._search_arxiv(query, max_results // 3)
        github_results = await self._search_github(query, max_results // 3)
        reddit_results = await self._search_reddit(query, ['algotrading'], max_results // 3)
        
        results.extend(arxiv_results)
        results.extend(github_results)
        results.extend(reddit_results)
        
        return results
    
    def _extract_insights(self, text: str) -> List[str]:
        """Extract key insights from text"""
        insights = []
        
        # Look for key patterns
        patterns = [
            r'(?:we find|we show|results show|we demonstrate)\s+(.{20,100})',
            r'(?:key finding|main result|importantly)\s*:?\s*(.{20,100})',
            r'(?:outperform|improve|achieve)\s+(.{20,80})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            insights.extend(matches[:2])
        
        # If no patterns found, extract first sentences
        if not insights:
            sentences = text.split('.')[:3]
            insights = [s.strip()[:100] for s in sentences if len(s.strip()) > 20]
        
        return insights[:5]
    
    def _extract_trading_implications(self, text: str) -> List[str]:
        """Extract trading implications from text"""
        implications = []
        
        trading_keywords = [
            'trading', 'portfolio', 'returns', 'risk', 'alpha', 'strategy',
            'market', 'price', 'prediction', 'forecast', 'profit', 'loss'
        ]
        
        sentences = text.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in trading_keywords):
                implications.append(sentence.strip()[:100])
        
        return implications[:3]
    
    def _extract_actions(self, text: str) -> List[str]:
        """Extract actionable items from text"""
        actions = []
        
        action_patterns = [
            r'(?:should|could|can)\s+(.{20,80})',
            r'(?:recommend|suggest)\s+(.{20,80})',
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, text.lower())
            actions.extend(matches[:2])
        
        if not actions:
            actions = ['Review and analyze', 'Test hypothesis', 'Implement if validated']
        
        return actions[:3]
    
    def _calculate_relevance(self, query: str, text: str) -> float:
        """Calculate relevance score"""
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        if not query_words:
            return 0.0
        
        overlap = len(query_words & text_words)
        return min(1.0, overlap / len(query_words))
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis"""
        positive_words = ['bullish', 'buy', 'long', 'up', 'gain', 'profit', 'growth', 'positive']
        negative_words = ['bearish', 'sell', 'short', 'down', 'loss', 'crash', 'negative', 'fear']
        
        text_lower = text.lower()
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return "BULLISH"
        elif neg_count > pos_count:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def _rank_results(self, results: List[ResearchResult]) -> List[ResearchResult]:
        """Rank results by relevance and quality"""
        # Score based on quality and relevance
        quality_weights = {
            SourceQuality.ACADEMIC: 1.0,
            SourceQuality.PROFESSIONAL: 0.9,
            SourceQuality.NEWS: 0.7,
            SourceQuality.COMMUNITY: 0.6,
            SourceQuality.SOCIAL: 0.4,
            SourceQuality.UNKNOWN: 0.3
        }
        
        for result in results:
            quality_score = quality_weights.get(result.source_quality, 0.5)
            result.relevance_score = (result.relevance_score + quality_score) / 2
        
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)
    
    def _add_to_knowledge_base(self, result: ResearchResult):
        """Add result to knowledge base"""
        # Check for duplicates
        existing_ids = {r.result_id for r in self.knowledge_base}
        if result.result_id not in existing_ids:
            self.knowledge_base.append(result)
            
            # Trim if too large
            if len(self.knowledge_base) > self.max_knowledge:
                self.knowledge_base = self.knowledge_base[-self.max_knowledge:]
    
    def get_knowledge(self, research_type: Optional[ResearchType] = None) -> List[ResearchResult]:
        """Get knowledge from the base"""
        if research_type:
            return [r for r in self.knowledge_base if r.research_type == research_type]
        return self.knowledge_base
    
    async def continuous_research(self, topics: List[str], interval_minutes: int = 60):
        """Continuously research topics"""
        logger.info(f"Starting continuous research on {len(topics)} topics")
        
        while True:
            for topic in topics:
                try:
                    # Rotate through research types
                    for research_type in ResearchType:
                        await self.research(topic, research_type, max_results=5)
                        await asyncio.sleep(5)  # Rate limiting
                        
                except Exception as e:
                    logger.error(f"Continuous research error: {e}")
            
            logger.info(f"Research cycle complete. Sleeping for {interval_minutes} minutes")
            await asyncio.sleep(interval_minutes * 60)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get research statistics"""
        return {
            **self.stats,
            'knowledge_base_size': len(self.knowledge_base),
            'research_types': {
                rt.value: len([r for r in self.knowledge_base if r.research_type == rt])
                for rt in ResearchType
            }
        }
