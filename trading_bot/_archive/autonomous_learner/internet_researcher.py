"""
Internet Researcher - Autonomous Web Research for Trading Education

Accesses the internet to learn trading from:
- Books and educational resources
- Research papers (arXiv, SSRN, academic journals)
- Trading articles and blogs
- Video transcripts and courses
- Real-time market analysis
"""

import asyncio
import aiohttp
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
import urllib.parse

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of learning resources"""
    BOOK = auto()
    RESEARCH_PAPER = auto()
    ARTICLE = auto()
    TUTORIAL = auto()
    VIDEO_TRANSCRIPT = auto()
    COURSE = auto()
    DOCUMENTATION = auto()
    CODE_EXAMPLE = auto()
    MARKET_ANALYSIS = auto()
    STRATEGY_GUIDE = auto()


class DifficultyLevel(Enum):
    """Learning difficulty levels"""
    BEGINNER = 1
    ELEMENTARY = 2
    INTERMEDIATE = 3
    UPPER_INTERMEDIATE = 4
    ADVANCED = 5
    EXPERT = 6
    MASTER = 7


@dataclass
class LearningResource:
    """A learning resource from the internet"""
    id: str
    type: ResourceType
    title: str
    url: str
    content: str
    summary: str
    difficulty: DifficultyLevel
    topics: List[str]
    key_concepts: List[str]
    code_snippets: List[str]
    relevance_score: float
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type.name,
            'title': self.title,
            'url': self.url,
            'content': self.content[:1000],  # Truncate for storage
            'summary': self.summary,
            'difficulty': self.difficulty.name,
            'topics': self.topics,
            'key_concepts': self.key_concepts,
            'code_snippets': self.code_snippets,
            'relevance_score': self.relevance_score,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'metadata': self.metadata,
        }


@dataclass
class LearnedConcept:
    """A concept learned from research"""
    id: str
    name: str
    category: str  # technical_analysis, fundamental, risk_management, etc.
    description: str
    difficulty: DifficultyLevel
    prerequisites: List[str]
    examples: List[str]
    formulas: List[str]
    code_implementation: Optional[str]
    confidence: float  # How well understood
    mastery_level: float  # 0-1, how well mastered
    times_reviewed: int
    last_reviewed: datetime
    sources: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'difficulty': self.difficulty.name,
            'prerequisites': self.prerequisites,
            'examples': self.examples,
            'formulas': self.formulas,
            'code_implementation': self.code_implementation,
            'confidence': self.confidence,
            'mastery_level': self.mastery_level,
            'times_reviewed': self.times_reviewed,
            'last_reviewed': self.last_reviewed.isoformat(),
            'sources': self.sources,
        }


class InternetResearcher:
    """
    Autonomous internet researcher for trading education.
    
    Capabilities:
    - Search and fetch educational content
    - Parse and extract key concepts
    - Build knowledge graph
    - Track learning progress
    - Adapt to difficulty levels
    """
    
    # Learning curriculum topics from basic to advanced (100+ topics)
    # Bot can dynamically choose what to learn from this comprehensive list
    CURRICULUM = {
        DifficultyLevel.BEGINNER: [
            # Market Fundamentals
            "what is trading",
            "stock market basics",
            "forex trading introduction",
            "cryptocurrency basics",
            "commodities trading basics",
            "bond market fundamentals",
            "ETF investing basics",
            "index funds explained",
            # Chart Basics
            "candlestick charts explained",
            "line charts vs bar charts",
            "reading price charts",
            "timeframes in trading",
            # Order Types
            "bid ask spread",
            "market orders vs limit orders",
            "stop orders explained",
            "trailing stop orders",
            # Basic Concepts
            "trading terminology glossary",
            "bull vs bear markets",
            "long vs short positions",
            "leverage margin trading basics",
            "pip points ticks explained",
            "lot sizes position units",
            "trading sessions market hours",
            "liquidity in markets",
        ],
        DifficultyLevel.ELEMENTARY: [
            # Technical Analysis Basics
            "support and resistance levels",
            "trend lines trading",
            "moving averages explained",
            "simple vs exponential moving average",
            "volume analysis basics",
            "price action trading basics",
            "breakout trading strategy",
            "pullback trading strategy",
            # Risk Management
            "risk management fundamentals",
            "position sizing basics",
            "stop loss take profit",
            "risk reward ratio",
            "portfolio diversification",
            "capital preservation strategies",
            # Psychology
            "trading psychology introduction",
            "emotional discipline trading",
            "fear greed in markets",
            "trading journal importance",
            # Fundamental Analysis
            "earnings reports trading",
            "economic indicators basics",
            "interest rates impact markets",
            "inflation trading strategies",
        ],
        DifficultyLevel.INTERMEDIATE: [
            # Technical Indicators
            "RSI indicator strategy",
            "MACD trading signals",
            "Bollinger Bands strategy",
            "stochastic oscillator trading",
            "ATR average true range",
            "ADX trend strength indicator",
            "CCI commodity channel index",
            "Williams %R indicator",
            "parabolic SAR strategy",
            "ichimoku cloud trading",
            # Chart Patterns
            "Fibonacci retracement trading",
            "chart patterns head shoulders",
            "double top double bottom",
            "triangle patterns trading",
            "wedge patterns trading",
            "flag pennant patterns",
            "cup handle pattern",
            "harmonic patterns trading",
            # Advanced Concepts
            "divergence trading",
            "multiple timeframe analysis",
            "confluence trading strategy",
            "swing trading strategies",
            "day trading techniques",
            "scalping strategies",
            "gap trading strategies",
            "momentum trading",
        ],
        DifficultyLevel.UPPER_INTERMEDIATE: [
            # Advanced Technical Analysis
            "Elliott Wave theory",
            "Wyckoff method trading",
            "order flow analysis",
            "market profile trading",
            "volume profile analysis",
            "footprint charts trading",
            "delta volume analysis",
            "cumulative delta trading",
            # Institutional Trading
            "institutional trading strategies",
            "smart money concepts",
            "liquidity zones trading",
            "order blocks trading",
            "fair value gaps",
            "breaker blocks strategy",
            "mitigation blocks",
            "inducement trading",
            # Options Basics
            "options trading fundamentals",
            "call put options explained",
            "options pricing basics",
            "covered calls strategy",
            "protective puts strategy",
            "options spreads introduction",
            # Sector Analysis
            "sector rotation strategy",
            "intermarket analysis",
            "correlation trading",
            "relative strength analysis",
        ],
        DifficultyLevel.ADVANCED: [
            # Algorithmic Trading
            "algorithmic trading strategies",
            "quantitative trading models",
            "backtesting trading strategies",
            "walk forward optimization",
            "monte carlo simulation trading",
            "strategy optimization techniques",
            # Statistical Methods
            "statistical arbitrage",
            "pairs trading cointegration",
            "mean reversion strategies",
            "momentum factor investing",
            "value factor strategies",
            "quality factor investing",
            # Machine Learning
            "machine learning trading",
            "neural networks price prediction",
            "random forest trading",
            "gradient boosting trading",
            "support vector machines trading",
            "LSTM time series prediction",
            "reinforcement learning trading",
            "genetic algorithms trading",
            # HFT Concepts
            "high frequency trading concepts",
            "latency arbitrage",
            "market making strategies",
            "order book analysis",
        ],
        DifficultyLevel.EXPERT: [
            # Market Microstructure
            "market microstructure theory",
            "optimal execution algorithms",
            "VWAP TWAP implementation",
            "implementation shortfall",
            "transaction cost analysis",
            "slippage minimization",
            # Dark Pools & Alternative Venues
            "dark pool trading strategies",
            "alternative trading systems",
            "smart order routing",
            "iceberg orders strategy",
            # Options Advanced
            "options Greeks hedging",
            "delta neutral strategies",
            "gamma scalping",
            "theta decay strategies",
            "vega trading volatility",
            "volatility surface modeling",
            "implied volatility trading",
            "volatility skew trading",
            # Portfolio Management
            "factor investing models",
            "risk parity portfolio",
            "Black Litterman model",
            "Kelly criterion position sizing",
            "portfolio optimization markowitz",
            "tail risk hedging",
        ],
        DifficultyLevel.MASTER: [
            # Deep Learning
            "deep reinforcement learning trading",
            "transformer models financial",
            "attention mechanisms trading",
            "CNN pattern recognition trading",
            "autoencoder anomaly detection",
            "GAN synthetic data generation",
            # Alternative Data
            "alternative data alpha",
            "satellite imagery trading",
            "web scraping trading signals",
            "social media sentiment trading",
            "news analytics trading",
            "credit card data trading",
            # NLP & Sentiment
            "sentiment analysis NLP trading",
            "earnings call analysis NLP",
            "SEC filings text analysis",
            "financial news classification",
            # Advanced ML
            "graph neural networks markets",
            "temporal fusion transformers",
            "meta learning trading",
            "transfer learning finance",
            "ensemble methods trading",
            "online learning trading",
            # Cutting Edge
            "quantum computing finance",
            "cross-asset correlation modeling",
            "regime detection hidden markov",
            "causal inference trading",
            "Bayesian portfolio optimization",
            "multi-agent market simulation",
            "adversarial machine learning trading",
            "explainable AI trading",
        ],
    }
    
    # Additional specialized topics the bot can explore
    SPECIALIZED_TOPICS = {
        'crypto_defi': [
            "DeFi yield farming strategies",
            "liquidity pool trading",
            "DEX arbitrage strategies",
            "NFT trading strategies",
            "crypto derivatives trading",
            "stablecoin strategies",
            "blockchain analytics trading",
            "MEV maximal extractable value",
        ],
        'forex_specific': [
            "carry trade strategy",
            "central bank trading",
            "currency correlation trading",
            "forex news trading",
            "swap rates trading",
            "exotic currency pairs",
            "forex hedging strategies",
            "currency strength analysis",
        ],
        'commodities': [
            "gold trading strategies",
            "oil trading fundamentals",
            "agricultural commodities trading",
            "precious metals trading",
            "commodity futures spreads",
            "seasonality commodity trading",
            "contango backwardation trading",
            "commodity ETF strategies",
        ],
        'fixed_income': [
            "bond trading strategies",
            "yield curve trading",
            "duration convexity trading",
            "credit spread trading",
            "treasury futures trading",
            "interest rate swaps",
            "municipal bond strategies",
            "corporate bond analysis",
        ],
        'derivatives': [
            "futures trading strategies",
            "options straddle strangle",
            "iron condor strategy",
            "butterfly spread options",
            "calendar spreads trading",
            "ratio spreads options",
            "synthetic positions trading",
            "exotic options trading",
        ],
        'risk_models': [
            "Value at Risk VaR",
            "Expected Shortfall CVaR",
            "stress testing portfolios",
            "scenario analysis trading",
            "correlation risk modeling",
            "liquidity risk management",
            "counterparty risk trading",
            "operational risk trading",
        ],
        'execution': [
            "algorithmic execution strategies",
            "participation rate algorithms",
            "arrival price algorithms",
            "close price algorithms",
            "adaptive execution algorithms",
            "execution quality analysis",
            "best execution practices",
            "order flow toxicity",
        ],
        'research_methods': [
            "alpha research process",
            "factor research methodology",
            "signal decay analysis",
            "overfitting prevention trading",
            "cross validation trading",
            "feature engineering trading",
            "data preprocessing finance",
            "survivorship bias trading",
        ],
    }
    
    # Research sources
    SOURCES = {
        'arxiv': {
            'base_url': 'https://export.arxiv.org/api/query',
            'type': ResourceType.RESEARCH_PAPER,
        },
        'investopedia': {
            'base_url': 'https://www.investopedia.com',
            'type': ResourceType.ARTICLE,
        },
        'tradingview': {
            'base_url': 'https://www.tradingview.com/ideas',
            'type': ResourceType.MARKET_ANALYSIS,
        },
        'babypips': {
            'base_url': 'https://www.babypips.com/learn/forex',
            'type': ResourceType.TUTORIAL,
        },
        'github': {
            'base_url': 'https://api.github.com/search/repositories',
            'type': ResourceType.CODE_EXAMPLE,
        },
        'ssrn': {
            'base_url': 'https://papers.ssrn.com/sol3/papers.cfm',
            'type': ResourceType.RESEARCH_PAPER,
        },
    }
    
    def __init__(self, data_dir: str = "autonomous_learner_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.data_dir / "learning_database.db"
        self._init_database()
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.resources: List[LearningResource] = []
        self.concepts: Dict[str, LearnedConcept] = {}
        self.current_level = DifficultyLevel.BEGINNER
        self.learning_progress: Dict[str, float] = {}
        self.research_history: List[Dict] = []
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds
        
        logger.info("InternetResearcher initialized")
    
    def _init_database(self):
        """Initialize SQLite database for storing learned content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resources (
                id TEXT PRIMARY KEY,
                type TEXT,
                title TEXT,
                url TEXT,
                content TEXT,
                summary TEXT,
                difficulty TEXT,
                topics TEXT,
                key_concepts TEXT,
                relevance_score REAL,
                timestamp TEXT,
                source TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS concepts (
                id TEXT PRIMARY KEY,
                name TEXT,
                category TEXT,
                description TEXT,
                difficulty TEXT,
                prerequisites TEXT,
                examples TEXT,
                formulas TEXT,
                code_implementation TEXT,
                confidence REAL,
                mastery_level REAL,
                times_reviewed INTEGER,
                last_reviewed TEXT,
                sources TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_progress (
                topic TEXT PRIMARY KEY,
                level TEXT,
                progress REAL,
                last_updated TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                source TEXT,
                results_count INTEGER,
                timestamp TEXT,
                success INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            # Create SSL context that doesn't verify certificates (for learning purposes)
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    'User-Agent': 'AlphaAlgo-LearningBot/1.0 (Educational Research)',
                    'Accept': 'text/html,application/json,application/xml',
                }
            )
    
    async def _rate_limit(self):
        """Apply rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    async def search_arxiv(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search arXiv for research papers"""
        await self._ensure_session()
        await self._rate_limit()
        
        try:
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': max_results,
                'sortBy': 'relevance',
                'sortOrder': 'descending',
            }
            
            url = f"{self.SOURCES['arxiv']['base_url']}?{urllib.parse.urlencode(params)}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    papers = self._parse_arxiv_response(content)
                    logger.info(f"Found {len(papers)} papers on arXiv for '{query}'")
                    return papers
                else:
                    logger.warning(f"arXiv search failed: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"arXiv search error: {e}")
            return []
    
    def _parse_arxiv_response(self, xml_content: str) -> List[Dict]:
        """Parse arXiv API XML response"""
        papers = []
        
        # Simple XML parsing without external dependencies
        entries = re.findall(r'<entry>(.*?)</entry>', xml_content, re.DOTALL)
        
        for entry in entries:
            title_match = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
            summary_match = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
            id_match = re.search(r'<id>(.*?)</id>', entry)
            
            if title_match and summary_match:
                papers.append({
                    'title': title_match.group(1).strip().replace('\n', ' '),
                    'summary': summary_match.group(1).strip().replace('\n', ' '),
                    'url': id_match.group(1) if id_match else '',
                    'source': 'arxiv',
                })
        
        return papers
    
    async def search_github(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search GitHub for trading code examples"""
        await self._ensure_session()
        await self._rate_limit()
        
        try:
            params = {
                'q': f'{query} trading bot',
                'sort': 'stars',
                'order': 'desc',
                'per_page': max_results,
            }
            
            url = f"{self.SOURCES['github']['base_url']}?{urllib.parse.urlencode(params)}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    repos = []
                    for item in data.get('items', [])[:max_results]:
                        repos.append({
                            'title': item.get('name', ''),
                            'summary': item.get('description', '') or '',
                            'url': item.get('html_url', ''),
                            'stars': item.get('stargazers_count', 0),
                            'language': item.get('language', ''),
                            'source': 'github',
                        })
                    logger.info(f"Found {len(repos)} repos on GitHub for '{query}'")
                    return repos
                else:
                    logger.warning(f"GitHub search failed: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"GitHub search error: {e}")
            return []
    
    async def fetch_web_content(self, url: str) -> Optional[str]:
        """Fetch content from a web URL"""
        await self._ensure_session()
        await self._rate_limit()
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    # Extract text content (simple HTML stripping)
                    text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
                    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                    text = re.sub(r'<[^>]+>', ' ', text)
                    text = re.sub(r'\s+', ' ', text).strip()
                    return text[:50000]  # Limit content size
                else:
                    return None
        except Exception as e:
            logger.error(f"Fetch error for {url}: {e}")
            return None
    
    async def research_topic(self, topic: str, difficulty: DifficultyLevel) -> List[LearningResource]:
        """Research a specific topic at given difficulty level"""
        logger.info(f"Researching topic: '{topic}' at {difficulty.name} level")
        
        resources = []
        
        # Search multiple sources
        arxiv_results = await self.search_arxiv(topic)
        github_results = await self.search_github(topic)
        
        # Process arXiv papers
        for paper in arxiv_results:
            resource = LearningResource(
                id=hashlib.md5(paper['url'].encode()).hexdigest(),
                type=ResourceType.RESEARCH_PAPER,
                title=paper['title'],
                url=paper['url'],
                content=paper['summary'],
                summary=paper['summary'][:500],
                difficulty=difficulty,
                topics=[topic],
                key_concepts=self._extract_concepts(paper['summary']),
                code_snippets=[],
                relevance_score=0.8,
                timestamp=datetime.now(),
                source='arxiv',
            )
            resources.append(resource)
        
        # Process GitHub repos
        for repo in github_results:
            resource = LearningResource(
                id=hashlib.md5(repo['url'].encode()).hexdigest(),
                type=ResourceType.CODE_EXAMPLE,
                title=repo['title'],
                url=repo['url'],
                content=repo['summary'],
                summary=repo['summary'][:500],
                difficulty=difficulty,
                topics=[topic],
                key_concepts=self._extract_concepts(repo['summary']),
                code_snippets=[],
                relevance_score=min(1.0, repo.get('stars', 0) / 1000),
                timestamp=datetime.now(),
                source='github',
                metadata={'stars': repo.get('stars', 0), 'language': repo.get('language', '')},
            )
            resources.append(resource)
        
        # Store resources
        for resource in resources:
            self._store_resource(resource)
        
        # Log research
        self._log_research(topic, 'multiple', len(resources))
        
        return resources
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        # Trading-related keywords to look for
        keywords = [
            'momentum', 'trend', 'volatility', 'liquidity', 'arbitrage',
            'hedging', 'portfolio', 'risk', 'return', 'alpha', 'beta',
            'sharpe', 'drawdown', 'backtest', 'optimization', 'machine learning',
            'neural network', 'reinforcement', 'prediction', 'forecast',
            'indicator', 'oscillator', 'moving average', 'support', 'resistance',
            'breakout', 'reversal', 'continuation', 'pattern', 'candlestick',
            'order flow', 'market making', 'execution', 'slippage', 'spread',
        ]
        
        text_lower = text.lower()
        found_concepts = [kw for kw in keywords if kw in text_lower]
        return found_concepts[:10]  # Limit to top 10
    
    def _store_resource(self, resource: LearningResource):
        """Store a learning resource in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO resources 
            (id, type, title, url, content, summary, difficulty, topics, key_concepts, relevance_score, timestamp, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            resource.id,
            resource.type.name,
            resource.title,
            resource.url,
            resource.content,
            resource.summary,
            resource.difficulty.name,
            json.dumps(resource.topics),
            json.dumps(resource.key_concepts),
            resource.relevance_score,
            resource.timestamp.isoformat(),
            resource.source,
        ))
        
        conn.commit()
        conn.close()
    
    def _log_research(self, query: str, source: str, results_count: int, success: bool = True):
        """Log research activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO research_log (query, source, results_count, timestamp, success)
            VALUES (?, ?, ?, ?, ?)
        ''', (query, source, results_count, datetime.now().isoformat(), int(success)))
        
        conn.commit()
        conn.close()
        
        self.research_history.append({
            'query': query,
            'source': source,
            'results_count': results_count,
            'timestamp': datetime.now(),
            'success': success,
        })
    
    def get_all_available_topics(self) -> Dict[str, List[str]]:
        """Get all available topics the bot can learn from (100+ topics)"""
        all_topics = {
            'curriculum': {},
            'specialized': self.SPECIALIZED_TOPICS.copy(),
        }
        
        # Add curriculum topics by level
        for level, topics in self.CURRICULUM.items():
            all_topics['curriculum'][level.name] = topics.copy()
        
        return all_topics
    
    def get_total_topic_count(self) -> int:
        """Get total count of all available learning topics"""
        count = sum(len(topics) for topics in self.CURRICULUM.values())
        count += sum(len(topics) for topics in self.SPECIALIZED_TOPICS.values())
        return count
    
    def choose_topics_to_learn(self, level: DifficultyLevel, num_topics: int = 10, 
                                include_specialized: bool = True) -> List[str]:
        """
        Bot dynamically chooses what topics to learn from the available list.
        Combines curriculum topics with specialized topics based on level.
        """
        available_topics = list(self.CURRICULUM.get(level, []))
        
        # Add specialized topics based on level
        if include_specialized:
            if level in [DifficultyLevel.BEGINNER, DifficultyLevel.ELEMENTARY]:
                # Beginners get forex and commodities basics
                available_topics.extend(self.SPECIALIZED_TOPICS.get('forex_specific', [])[:3])
                available_topics.extend(self.SPECIALIZED_TOPICS.get('commodities', [])[:3])
            elif level in [DifficultyLevel.INTERMEDIATE, DifficultyLevel.UPPER_INTERMEDIATE]:
                # Intermediate gets options and derivatives
                available_topics.extend(self.SPECIALIZED_TOPICS.get('derivatives', []))
                available_topics.extend(self.SPECIALIZED_TOPICS.get('fixed_income', [])[:4])
                available_topics.extend(self.SPECIALIZED_TOPICS.get('forex_specific', []))
            elif level in [DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT]:
                # Advanced gets risk models and execution
                available_topics.extend(self.SPECIALIZED_TOPICS.get('risk_models', []))
                available_topics.extend(self.SPECIALIZED_TOPICS.get('execution', []))
                available_topics.extend(self.SPECIALIZED_TOPICS.get('research_methods', []))
            elif level == DifficultyLevel.MASTER:
                # Masters get crypto/DeFi and all specialized
                available_topics.extend(self.SPECIALIZED_TOPICS.get('crypto_defi', []))
                for category in self.SPECIALIZED_TOPICS.values():
                    available_topics.extend(category)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_topics = []
        for topic in available_topics:
            if topic not in seen:
                seen.add(topic)
                unique_topics.append(topic)
        
        # Randomly select topics if we have more than requested
        if len(unique_topics) > num_topics:
            selected = random.sample(unique_topics, num_topics)
        else:
            selected = unique_topics
        
        logger.info(f"Bot chose {len(selected)} topics to learn at {level.name} level")
        return selected
    
    async def learn_curriculum_level(self, level: DifficultyLevel, 
                                      dynamic_selection: bool = True,
                                      num_topics: int = 12) -> Dict[str, Any]:
        """
        Learn topics at a specific curriculum level.
        If dynamic_selection is True, bot chooses what to learn from 100+ available topics.
        """
        if dynamic_selection:
            topics = self.choose_topics_to_learn(level, num_topics, include_specialized=True)
        else:
            topics = self.CURRICULUM.get(level, [])
        
        logger.info(f"Learning {len(topics)} topics at {level.name} level")
        
        all_resources = []
        concepts_learned = []
        
        for topic in topics:
            resources = await self.research_topic(topic, level)
            all_resources.extend(resources)
            
            # Extract and store concepts
            for resource in resources:
                for concept_name in resource.key_concepts:
                    if concept_name not in self.concepts:
                        concept = LearnedConcept(
                            id=hashlib.md5(concept_name.encode()).hexdigest(),
                            name=concept_name,
                            category=self._categorize_concept(concept_name),
                            description=f"Concept learned from {resource.title}",
                            difficulty=level,
                            prerequisites=[],
                            examples=[resource.summary[:200]],
                            formulas=[],
                            code_implementation=None,
                            confidence=0.5,
                            mastery_level=0.0,
                            times_reviewed=1,
                            last_reviewed=datetime.now(),
                            sources=[resource.url],
                        )
                        self.concepts[concept_name] = concept
                        concepts_learned.append(concept_name)
            
            # Small delay between topics
            await asyncio.sleep(0.5)
        
        # Update progress
        self.learning_progress[level.name] = 1.0
        self._save_progress(level)
        
        return {
            'level': level.name,
            'topics_covered': len(topics),
            'resources_found': len(all_resources),
            'concepts_learned': concepts_learned,
            'timestamp': datetime.now().isoformat(),
        }
    
    def _categorize_concept(self, concept: str) -> str:
        """Categorize a concept"""
        categories = {
            'technical_analysis': ['indicator', 'oscillator', 'moving average', 'support', 'resistance', 'pattern', 'candlestick', 'trend', 'breakout'],
            'risk_management': ['risk', 'drawdown', 'hedging', 'portfolio', 'position'],
            'quantitative': ['alpha', 'beta', 'sharpe', 'optimization', 'backtest', 'arbitrage'],
            'machine_learning': ['machine learning', 'neural network', 'reinforcement', 'prediction', 'forecast'],
            'market_microstructure': ['order flow', 'market making', 'execution', 'slippage', 'spread', 'liquidity'],
            'fundamental': ['momentum', 'volatility', 'return'],
        }
        
        concept_lower = concept.lower()
        for category, keywords in categories.items():
            if any(kw in concept_lower for kw in keywords):
                return category
        return 'general'
    
    def _save_progress(self, level: DifficultyLevel):
        """Save learning progress to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO learning_progress (topic, level, progress, last_updated)
            VALUES (?, ?, ?, ?)
        ''', (level.name, level.name, 1.0, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get current learning statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count resources
        cursor.execute('SELECT COUNT(*) FROM resources')
        resource_count = cursor.fetchone()[0]
        
        # Count by type
        cursor.execute('SELECT type, COUNT(*) FROM resources GROUP BY type')
        resources_by_type = dict(cursor.fetchall())
        
        # Count concepts
        cursor.execute('SELECT COUNT(*) FROM concepts')
        concept_count = cursor.fetchone()[0]
        
        # Get progress
        cursor.execute('SELECT level, progress FROM learning_progress')
        progress = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_resources': resource_count,
            'resources_by_type': resources_by_type,
            'total_concepts': len(self.concepts),
            'concepts_in_db': concept_count,
            'progress_by_level': progress,
            'current_level': self.current_level.name,
            'research_sessions': len(self.research_history),
        }
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
