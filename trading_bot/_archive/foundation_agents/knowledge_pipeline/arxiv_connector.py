"""
ArXiv Connector - External Research Knowledge Acquisition
==========================================================

Implements connection to arXiv for research paper discovery:
1. Paper search by topic, author, date
2. Abstract parsing and summarization
3. Citation network analysis
4. Trend detection in research topics
5. Relevance scoring for trading applications

Based on the Foundation Agents paper (arXiv:2504.01990) knowledge systems.
"""

import logging
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class PaperCategory(Enum):
    """ArXiv paper categories relevant to trading"""
    QUANTITATIVE_FINANCE = "q-fin"
    MACHINE_LEARNING = "cs.LG"
    ARTIFICIAL_INTELLIGENCE = "cs.AI"
    STATISTICS = "stat"
    ECONOMICS = "econ"
    COMPUTATIONAL_FINANCE = "q-fin.CP"
    PORTFOLIO_MANAGEMENT = "q-fin.PM"
    RISK_MANAGEMENT = "q-fin.RM"
    STATISTICAL_FINANCE = "q-fin.ST"
    TRADING = "q-fin.TR"
    MATHEMATICAL_FINANCE = "q-fin.MF"


class RelevanceLevel(Enum):
    """Relevance level for papers"""
    HIGHLY_RELEVANT = 5
    RELEVANT = 4
    SOMEWHAT_RELEVANT = 3
    MARGINALLY_RELEVANT = 2
    NOT_RELEVANT = 1


@dataclass
class Author:
    """Paper author"""
    name: str
    affiliation: Optional[str] = None
    arxiv_id: Optional[str] = None


@dataclass
class Paper:
    """Research paper from arXiv"""
    arxiv_id: str
    title: str
    abstract: str
    authors: List[Author]
    categories: List[str]
    
    # Dates
    published: datetime
    updated: Optional[datetime] = None
    
    # Links
    pdf_url: Optional[str] = None
    abs_url: Optional[str] = None
    
    # Analysis
    relevance_score: float = 0.0
    relevance_level: RelevanceLevel = RelevanceLevel.NOT_RELEVANT
    key_concepts: List[str] = field(default_factory=list)
    methodology: Optional[str] = None
    
    # Citations
    citations: List[str] = field(default_factory=list)
    cited_by: List[str] = field(default_factory=list)
    
    # Trading relevance
    trading_applications: List[str] = field(default_factory=list)
    potential_alpha: bool = False
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'arxiv_id': self.arxiv_id,
            'title': self.title,
            'abstract': self.abstract[:500] + '...' if len(self.abstract) > 500 else self.abstract,
            'authors': [a.name for a in self.authors],
            'categories': self.categories,
            'published': self.published.isoformat(),
            'relevance_score': self.relevance_score,
            'relevance_level': self.relevance_level.value,
            'key_concepts': self.key_concepts,
            'trading_applications': self.trading_applications,
            'potential_alpha': self.potential_alpha
        }


@dataclass
class SearchQuery:
    """Search query for arXiv"""
    keywords: List[str]
    categories: List[PaperCategory] = field(default_factory=list)
    authors: List[str] = field(default_factory=list)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    max_results: int = 50
    sort_by: str = "relevance"  # relevance, lastUpdatedDate, submittedDate


class AbstractAnalyzer:
    """Analyze paper abstracts for relevance and concepts"""
    
    # Keywords indicating trading relevance
    TRADING_KEYWORDS = {
        'high_relevance': [
            'trading', 'portfolio', 'alpha', 'return prediction', 'stock',
            'market', 'price prediction', 'financial', 'asset allocation',
            'risk management', 'hedge', 'arbitrage', 'momentum', 'mean reversion',
            'volatility', 'options', 'derivatives', 'order book', 'execution'
        ],
        'medium_relevance': [
            'time series', 'forecasting', 'prediction', 'regression',
            'classification', 'neural network', 'deep learning', 'reinforcement learning',
            'optimization', 'bayesian', 'causal', 'anomaly detection'
        ],
        'methodology': [
            'transformer', 'lstm', 'gru', 'attention', 'graph neural',
            'reinforcement learning', 'meta-learning', 'ensemble',
            'gradient boosting', 'random forest', 'svm'
        ]
    }
    
    def analyze(self, paper: Paper) -> Paper:
        """Analyze paper abstract and update relevance"""
        text = (paper.title + ' ' + paper.abstract).lower()
        
        # Count keyword matches
        high_matches = sum(1 for kw in self.TRADING_KEYWORDS['high_relevance'] if kw in text)
        medium_matches = sum(1 for kw in self.TRADING_KEYWORDS['medium_relevance'] if kw in text)
        
        # Calculate relevance score
        score = (high_matches * 2 + medium_matches) / 20
        paper.relevance_score = min(1.0, score)
        
        # Determine relevance level
        if paper.relevance_score >= 0.7:
            paper.relevance_level = RelevanceLevel.HIGHLY_RELEVANT
        elif paper.relevance_score >= 0.5:
            paper.relevance_level = RelevanceLevel.RELEVANT
        elif paper.relevance_score >= 0.3:
            paper.relevance_level = RelevanceLevel.SOMEWHAT_RELEVANT
        elif paper.relevance_score >= 0.1:
            paper.relevance_level = RelevanceLevel.MARGINALLY_RELEVANT
        else:
            paper.relevance_level = RelevanceLevel.NOT_RELEVANT
        
        # Extract key concepts
        paper.key_concepts = self._extract_concepts(text)
        
        # Identify methodology
        paper.methodology = self._identify_methodology(text)
        
        # Identify trading applications
        paper.trading_applications = self._identify_applications(text)
        
        # Check for potential alpha
        alpha_indicators = ['novel', 'outperform', 'superior', 'significant', 'profitable']
        paper.potential_alpha = any(ind in text for ind in alpha_indicators)
        
        return paper
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        concepts = []
        
        # Check for methodology keywords
        for kw in self.TRADING_KEYWORDS['methodology']:
            if kw in text:
                concepts.append(kw)
        
        # Check for trading concepts
        for kw in self.TRADING_KEYWORDS['high_relevance']:
            if kw in text:
                concepts.append(kw)
        
        return list(set(concepts))[:10]
    
    def _identify_methodology(self, text: str) -> Optional[str]:
        """Identify the main methodology"""
        for method in self.TRADING_KEYWORDS['methodology']:
            if method in text:
                return method
        return None
    
    def _identify_applications(self, text: str) -> List[str]:
        """Identify potential trading applications"""
        applications = []
        
        app_patterns = {
            'price_prediction': ['price prediction', 'return prediction', 'forecast'],
            'portfolio_optimization': ['portfolio', 'asset allocation', 'optimization'],
            'risk_management': ['risk', 'var', 'drawdown', 'volatility'],
            'alpha_generation': ['alpha', 'signal', 'factor'],
            'execution': ['execution', 'order', 'market making'],
            'sentiment': ['sentiment', 'news', 'social media']
        }
        
        for app, patterns in app_patterns.items():
            if any(p in text for p in patterns):
                applications.append(app)
        
        return applications


class ArxivConnector:
    """
    ArXiv Connector
    
    Connects to arXiv API for research paper discovery and analysis.
    Note: This is a simulated connector - in production, would use actual arXiv API.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Analyzer
        self.analyzer = AbstractAnalyzer()
        
        # Cache
        self.paper_cache: Dict[str, Paper] = {}
        self.search_cache: Dict[str, List[Paper]] = {}
        
        # Tracking
        self.search_history: List[SearchQuery] = []
        self.discovered_papers: List[Paper] = []
        
        # Topic trends
        self.topic_counts: Dict[str, int] = defaultdict(int)
        self.topic_timeline: Dict[str, List[Tuple[datetime, int]]] = defaultdict(list)
        
        # Statistics
        self.stats = {
            'searches_performed': 0,
            'papers_discovered': 0,
            'highly_relevant': 0,
            'potential_alpha': 0
        }
        
        logger.info("ArXiv Connector initialized")
    
    async def search(self, query: SearchQuery) -> List[Paper]:
        """
        Search arXiv for papers
        
        Note: In production, this would call the actual arXiv API.
        This is a simulated implementation.
        """
        self.search_history.append(query)
        self.stats['searches_performed'] += 1
        
        # Generate cache key
        cache_key = self._query_hash(query)
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
        
        # Simulate API call delay
        await asyncio.sleep(0.1)
        
        # In production, would call: https://export.arxiv.org/api/query
        # For now, generate simulated results based on query
        papers = self._simulate_search_results(query)
        
        # Analyze papers
        analyzed_papers = []
        for paper in papers:
            analyzed = self.analyzer.analyze(paper)
            analyzed_papers.append(analyzed)
            
            # Update statistics
            self.stats['papers_discovered'] += 1
            if analyzed.relevance_level == RelevanceLevel.HIGHLY_RELEVANT:
                self.stats['highly_relevant'] += 1
            if analyzed.potential_alpha:
                self.stats['potential_alpha'] += 1
            
            # Update topic tracking
            for concept in analyzed.key_concepts:
                self.topic_counts[concept] += 1
                self.topic_timeline[concept].append((datetime.utcnow(), 1))
        
        # Cache results
        self.search_cache[cache_key] = analyzed_papers
        self.discovered_papers.extend(analyzed_papers)
        
        # Sort by relevance
        analyzed_papers.sort(key=lambda p: p.relevance_score, reverse=True)
        
        return analyzed_papers
    
    def _query_hash(self, query: SearchQuery) -> str:
        """Generate hash for query caching"""
        key = f"{query.keywords}_{query.categories}_{query.date_from}_{query.date_to}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _simulate_search_results(self, query: SearchQuery) -> List[Paper]:
        """Simulate search results (placeholder for actual API)"""
        # This would be replaced with actual arXiv API calls
        simulated_papers = []
        
        # Generate some simulated papers based on keywords
        templates = [
            {
                'title': "Deep Learning for {keyword} Prediction in Financial Markets",
                'abstract': "We propose a novel deep learning approach for {keyword} prediction. "
                           "Our method uses transformer architecture to capture temporal dependencies "
                           "in financial time series. Experiments on stock market data show significant "
                           "improvements over baseline methods.",
                'categories': ['cs.LG', 'q-fin.ST']
            },
            {
                'title': "Reinforcement Learning for {keyword} Optimization",
                'abstract': "This paper presents a reinforcement learning framework for {keyword} "
                           "optimization in trading systems. We demonstrate that our approach achieves "
                           "superior risk-adjusted returns compared to traditional methods.",
                'categories': ['cs.LG', 'q-fin.PM']
            },
            {
                'title': "Causal Discovery in {keyword} Analysis",
                'abstract': "We apply causal discovery methods to understand {keyword} dynamics "
                           "in financial markets. Our analysis reveals novel causal relationships "
                           "that can be exploited for alpha generation.",
                'categories': ['stat.ML', 'q-fin.ST']
            }
        ]
        
        for i, keyword in enumerate(query.keywords[:3]):
            for j, template in enumerate(templates):
                paper = Paper(
                    arxiv_id=f"2024.{i:02d}{j:02d}",
                    title=template['title'].format(keyword=keyword.title()),
                    abstract=template['abstract'].format(keyword=keyword),
                    authors=[Author(name=f"Author {i+1}")],
                    categories=template['categories'],
                    published=datetime.utcnow() - timedelta(days=i*30),
                    pdf_url=f"https://arxiv.org/pdf/2024.{i:02d}{j:02d}.pdf",
                    abs_url=f"https://arxiv.org/abs/2024.{i:02d}{j:02d}"
                )
                simulated_papers.append(paper)
        
        return simulated_papers[:query.max_results]
    
    def search_sync(self, query: SearchQuery) -> List[Paper]:
        """Synchronous search wrapper"""
        return asyncio.get_event_loop().run_until_complete(self.search(query))
    
    def get_paper(self, arxiv_id: str) -> Optional[Paper]:
        """Get a specific paper by ID"""
        if arxiv_id in self.paper_cache:
            return self.paper_cache[arxiv_id]
        
        # In production, would fetch from API
        for paper in self.discovered_papers:
            if paper.arxiv_id == arxiv_id:
                self.paper_cache[arxiv_id] = paper
                return paper
        
        return None
    
    def get_trending_topics(self, days: int = 30, limit: int = 10) -> List[Tuple[str, int]]:
        """Get trending research topics"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        recent_counts = defaultdict(int)
        for topic, timeline in self.topic_timeline.items():
            for timestamp, count in timeline:
                if timestamp > cutoff:
                    recent_counts[topic] += count
        
        sorted_topics = sorted(recent_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_topics[:limit]
    
    def get_relevant_papers(
        self,
        min_relevance: RelevanceLevel = RelevanceLevel.RELEVANT,
        limit: int = 20
    ) -> List[Paper]:
        """Get papers above relevance threshold"""
        relevant = [
            p for p in self.discovered_papers
            if p.relevance_level.value >= min_relevance.value
        ]
        relevant.sort(key=lambda p: p.relevance_score, reverse=True)
        return relevant[:limit]
    
    def get_papers_with_alpha_potential(self, limit: int = 10) -> List[Paper]:
        """Get papers with potential alpha generation applications"""
        alpha_papers = [p for p in self.discovered_papers if p.potential_alpha]
        alpha_papers.sort(key=lambda p: p.relevance_score, reverse=True)
        return alpha_papers[:limit]
    
    def get_papers_by_methodology(self, methodology: str) -> List[Paper]:
        """Get papers using a specific methodology"""
        return [
            p for p in self.discovered_papers
            if p.methodology and methodology.lower() in p.methodology.lower()
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get connector statistics"""
        return {
            **self.stats,
            'cached_papers': len(self.paper_cache),
            'total_discovered': len(self.discovered_papers),
            'trending_topics': self.get_trending_topics(limit=5),
            'relevance_distribution': {
                level.name: len([p for p in self.discovered_papers if p.relevance_level == level])
                for level in RelevanceLevel
            }
        }
    
    def create_search_query(
        self,
        keywords: List[str],
        categories: Optional[List[str]] = None,
        days_back: int = 30,
        max_results: int = 50
    ) -> SearchQuery:
        """Helper to create a search query"""
        cat_enums = []
        if categories:
            for cat in categories:
                try:
                    cat_enums.append(PaperCategory(cat))
                except ValueError:
                    pass
        
        return SearchQuery(
            keywords=keywords,
            categories=cat_enums,
            date_from=datetime.utcnow() - timedelta(days=days_back),
            date_to=datetime.utcnow(),
            max_results=max_results
        )
