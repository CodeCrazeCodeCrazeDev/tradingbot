"""
Retrieval Pipeline for Perplexity Trading Architecture
============================================================

Multi-source data retrieval with citation tracking.
Like Perplexity's retrieval-augmented generation, this:
- Retrieves data from multiple sources
- Tracks provenance for citations
- Ranks and filters results
- Provides freshness guarantees
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

from .core_types import (
    Citation,
    RetrievalSource,
)

logger = logging.getLogger(__name__)


class RetrievalPriority(Enum):
    """Priority for retrieval sources"""
    CRITICAL = 1    # Must have (e.g., current price)
    HIGH = 2        # Important (e.g., recent news)
    MEDIUM = 3      # Useful (e.g., sentiment)
    LOW = 4         # Nice to have (e.g., alternative data)


@dataclass
class RetrievalResult:
    """Result from a retrieval operation"""
    source: RetrievalSource
    source_name: str
    data: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    freshness_seconds: float = 0.0
    confidence: float = 0.8
    url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_citation(self, data_point: str) -> Citation:
        """Convert to citation"""
        return Citation(
            source_type=self.source,
            source_name=self.source_name,
            timestamp=self.timestamp,
            data_point=data_point,
            confidence=self.confidence,
            url=self.url,
            raw_data=self.data,
        )


class BaseRetriever(ABC):
    """Base class for data retrievers"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.source_type: RetrievalSource = RetrievalSource.MARKET_DATA
        self.name: str = "Base Retriever"
        self.priority: RetrievalPriority = RetrievalPriority.MEDIUM
        self.cache: Dict[str, RetrievalResult] = {}
        self.cache_ttl_seconds: float = 60.0
    
    @abstractmethod
    async def retrieve(self, query: Dict[str, Any]) -> RetrievalResult:
        """Retrieve data based on query"""
        pass
    
    def get_cached(self, cache_key: str) -> Optional[RetrievalResult]:
        """Get cached result if still fresh"""
        if cache_key in self.cache:
            result = self.cache[cache_key]
            age = (datetime.utcnow() - result.timestamp).total_seconds()
            if age < self.cache_ttl_seconds:
                result.freshness_seconds = age
                return result
        return None
    
    def set_cached(self, cache_key: str, result: RetrievalResult) -> None:
        """Cache a result"""
        self.cache[cache_key] = result
        
        # Cleanup old entries
        if len(self.cache) > 100:
            oldest_key = min(self.cache, key=lambda k: self.cache[k].timestamp)
            del self.cache[oldest_key]


class MarketDataRetriever(BaseRetriever):
    """Retrieves real-time and historical market data"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_type = RetrievalSource.MARKET_DATA
        self.name = "Market Data"
        self.priority = RetrievalPriority.CRITICAL
        self.cache_ttl_seconds = 5.0  # Very short cache for market data
    
    async def retrieve(self, query: Dict[str, Any]) -> RetrievalResult:
        """Retrieve market data"""
        symbol = query.get('symbol', 'EURUSD')
        timeframe = query.get('timeframe', 'H1')
        data_type = query.get('data_type', 'ohlcv')
        
        cache_key = f"{symbol}_{timeframe}_{data_type}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        # In production, call actual market data API
        # For now, return simulated data
        import numpy as np
        
        if data_type == 'ohlcv':
            data = {
                'symbol': symbol,
                'timeframe': timeframe,
                'bars': [
                    {
                        'time': datetime.utcnow() - timedelta(hours=i),
                        'open': 1.0850 + np.random.randn() * 0.001,
                        'high': 1.0860 + np.random.randn() * 0.001,
                        'low': 1.0840 + np.random.randn() * 0.001,
                        'close': 1.0855 + np.random.randn() * 0.001,
                        'volume': 1000 + np.random.randint(0, 500),
                    }
                    for i in range(100)
                ],
                'current_price': 1.0855,
                'bid': 1.0854,
                'ask': 1.0856,
                'spread': 0.0002,
            }
        elif data_type == 'orderbook':
            data = {
                'symbol': symbol,
                'bids': [[1.0854 - i*0.0001, 100000 + i*10000] for i in range(10)],
                'asks': [[1.0856 + i*0.0001, 100000 + i*10000] for i in range(10)],
                'timestamp': datetime.utcnow().isoformat(),
            }
        else:
            data = {'symbol': symbol, 'price': 1.0855}
        
        result = RetrievalResult(
            source=self.source_type,
            source_name=self.name,
            data=data,
            confidence=0.99,
            metadata={'symbol': symbol, 'timeframe': timeframe},
        )
        
        self.set_cached(cache_key, result)
        return result


class NewsRetriever(BaseRetriever):
    """Retrieves financial news"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_type = RetrievalSource.NEWS
        self.name = "Financial News"
        self.priority = RetrievalPriority.HIGH
        self.cache_ttl_seconds = 300.0  # 5 minutes
    
    async def retrieve(self, query: Dict[str, Any]) -> RetrievalResult:
        """Retrieve news articles"""
        symbol = query.get('symbol', '')
        keywords = query.get('keywords', [])
        limit = query.get('limit', 10)
        
        cache_key = f"news_{symbol}_{'-'.join(keywords)}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        # In production, call news API
        data = {
            'articles': [
                {
                    'title': 'Fed Signals Potential Rate Pause',
                    'source': 'Reuters',
                    'timestamp': datetime.utcnow() - timedelta(hours=2),
                    'sentiment': 0.15,
                    'relevance': 0.9,
                    'url': 'https://reuters.com/article/123',
                },
                {
                    'title': 'European Markets Rise on Economic Data',
                    'source': 'Bloomberg',
                    'timestamp': datetime.utcnow() - timedelta(hours=4),
                    'sentiment': 0.25,
                    'relevance': 0.85,
                    'url': 'https://bloomberg.com/article/456',
                },
                {
                    'title': 'Dollar Weakens Against Major Currencies',
                    'source': 'FX Street',
                    'timestamp': datetime.utcnow() - timedelta(hours=6),
                    'sentiment': -0.1,
                    'relevance': 0.95,
                    'url': 'https://fxstreet.com/article/789',
                },
            ],
            'overall_sentiment': 0.10,
            'article_count': 3,
            'keywords_matched': keywords,
        }
        
        result = RetrievalResult(
            source=self.source_type,
            source_name=self.name,
            data=data,
            confidence=0.85,
            metadata={'symbol': symbol, 'keywords': keywords},
        )
        
        self.set_cached(cache_key, result)
        return result


class SentimentRetriever(BaseRetriever):
    """Retrieves market sentiment data"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_type = RetrievalSource.SENTIMENT
        self.name = "Market Sentiment"
        self.priority = RetrievalPriority.MEDIUM
        self.cache_ttl_seconds = 600.0  # 10 minutes
    
    async def retrieve(self, query: Dict[str, Any]) -> RetrievalResult:
        """Retrieve sentiment data"""
        symbol = query.get('symbol', '')
        
        cache_key = f"sentiment_{symbol}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        # In production, aggregate from multiple sources
        data = {
            'symbol': symbol,
            'social_media': {
                'twitter': {'score': 0.12, 'volume': 5000, 'trend': 'increasing'},
                'reddit': {'score': 0.08, 'volume': 1200, 'trend': 'stable'},
                'stocktwits': {'score': 0.15, 'volume': 800, 'trend': 'increasing'},
            },
            'news_sentiment': 0.10,
            'positioning': {
                'retail': {'long_percent': 62, 'short_percent': 38},
                'institutional': {'long_percent': 55, 'short_percent': 45},
            },
            'fear_greed_index': 55,
            'overall_score': 0.12,
            'label': 'slightly_bullish',
        }
        
        result = RetrievalResult(
            source=self.source_type,
            source_name=self.name,
            data=data,
            confidence=0.80,
            metadata={'symbol': symbol},
        )
        
        self.set_cached(cache_key, result)
        return result


class FundamentalsRetriever(BaseRetriever):
    """Retrieves fundamental/economic data"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_type = RetrievalSource.FUNDAMENTALS
        self.name = "Fundamentals"
        self.priority = RetrievalPriority.HIGH
        self.cache_ttl_seconds = 3600.0  # 1 hour (fundamentals change slowly)
    
    async def retrieve(self, query: Dict[str, Any]) -> RetrievalResult:
        """Retrieve fundamental data"""
        symbol = query.get('symbol', '')
        data_type = query.get('data_type', 'economic')
        
        cache_key = f"fundamentals_{symbol}_{data_type}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        # In production, call economic data APIs
        data = {
            'symbol': symbol,
            'economic_indicators': {
                'gdp_growth': {'value': 2.1, 'previous': 1.9, 'trend': 'improving'},
                'inflation': {'value': 3.2, 'previous': 3.4, 'trend': 'declining'},
                'unemployment': {'value': 3.8, 'previous': 3.9, 'trend': 'improving'},
                'interest_rate': {'value': 5.25, 'previous': 5.25, 'trend': 'stable'},
            },
            'central_bank': {
                'stance': 'hawkish',
                'next_meeting': (datetime.utcnow() + timedelta(days=14)).isoformat(),
                'rate_expectation': 'hold',
            },
            'economic_calendar': [
                {'event': 'FOMC Minutes', 'date': (datetime.utcnow() + timedelta(days=3)).isoformat(), 'impact': 'high'},
                {'event': 'NFP', 'date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'impact': 'high'},
                {'event': 'CPI', 'date': (datetime.utcnow() + timedelta(days=10)).isoformat(), 'impact': 'high'},
            ],
        }
        
        result = RetrievalResult(
            source=self.source_type,
            source_name=self.name,
            data=data,
            confidence=0.90,
            metadata={'symbol': symbol, 'data_type': data_type},
        )
        
        self.set_cached(cache_key, result)
        return result


class AlternativeDataRetriever(BaseRetriever):
    """Retrieves alternative data sources"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_type = RetrievalSource.ALTERNATIVE
        self.name = "Alternative Data"
        self.priority = RetrievalPriority.LOW
        self.cache_ttl_seconds = 1800.0  # 30 minutes
    
    async def retrieve(self, query: Dict[str, Any]) -> RetrievalResult:
        """Retrieve alternative data"""
        symbol = query.get('symbol', '')
        
        cache_key = f"altdata_{symbol}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        # In production, call alternative data providers
        data = {
            'symbol': symbol,
            'web_traffic': {'trend': 'increasing', 'change_percent': 5.2},
            'app_downloads': {'trend': 'stable', 'change_percent': 0.5},
            'satellite_data': {'activity_level': 'normal'},
            'credit_card_data': {'spending_trend': 'increasing'},
            'job_postings': {'trend': 'increasing', 'change_percent': 8.0},
        }
        
        result = RetrievalResult(
            source=self.source_type,
            source_name=self.name,
            data=data,
            confidence=0.70,
            metadata={'symbol': symbol},
        )
        
        self.set_cached(cache_key, result)
        return result


class RetrievalPipeline:
    """
    Orchestrates multi-source data retrieval.
    
    Features:
    - Parallel retrieval from multiple sources
    - Priority-based ordering
    - Caching and freshness tracking
    - Citation generation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize retrievers
        self.retrievers: Dict[RetrievalSource, BaseRetriever] = {
            RetrievalSource.MARKET_DATA: MarketDataRetriever(config),
            RetrievalSource.NEWS: NewsRetriever(config),
            RetrievalSource.SENTIMENT: SentimentRetriever(config),
            RetrievalSource.FUNDAMENTALS: FundamentalsRetriever(config),
            RetrievalSource.ALTERNATIVE: AlternativeDataRetriever(config),
        }
        
        # Retrieval history
        self.history: List[Dict[str, Any]] = []
    
    async def retrieve(
        self,
        sources: List[RetrievalSource],
        query: Dict[str, Any],
        timeout_seconds: float = 10.0,
    ) -> Dict[RetrievalSource, RetrievalResult]:
        """
        Retrieve data from multiple sources in parallel.
        
        Args:
            sources: List of sources to retrieve from
            query: Query parameters
            timeout_seconds: Maximum time to wait
            
        Returns:
            Dict mapping source to result
        """
        logger.info(f"Retrieving from {len(sources)} sources: {[s.value for s in sources]}")
        
        # Create tasks for parallel retrieval
        tasks = {}
        for source in sources:
            if source in self.retrievers:
                tasks[source] = asyncio.create_task(
                    self.retrievers[source].retrieve(query)
                )
        
        # Wait for all with timeout
        results: Dict[RetrievalSource, RetrievalResult] = {}
        
        try:
            done, pending = await asyncio.wait(
                tasks.values(),
                timeout=timeout_seconds,
                return_when=asyncio.ALL_COMPLETED,
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            # Collect results
            for source, task in tasks.items():
                if task in done and not task.cancelled():
                    try:
                        results[source] = task.result()
                    except Exception as e:
                        logger.error(f"Error retrieving from {source.value}: {e}")
        
        except asyncio.TimeoutError:
            logger.warning(f"Retrieval timeout after {timeout_seconds}s")
        
        # Record in history
        self.history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'sources_requested': [s.value for s in sources],
            'sources_retrieved': [s.value for s in results.keys()],
            'query': query,
        })
        
        return results
    
    async def retrieve_all(
        self,
        query: Dict[str, Any],
        timeout_seconds: float = 15.0,
    ) -> Dict[RetrievalSource, RetrievalResult]:
        """Retrieve from all available sources"""
        return await self.retrieve(
            list(self.retrievers.keys()),
            query,
            timeout_seconds,
        )
    
    async def retrieve_critical(
        self,
        query: Dict[str, Any],
        timeout_seconds: float = 5.0,
    ) -> Dict[RetrievalSource, RetrievalResult]:
        """Retrieve only critical data (market data)"""
        critical_sources = [
            source for source, retriever in self.retrievers.items()
            if retriever.priority == RetrievalPriority.CRITICAL
        ]
        return await self.retrieve(critical_sources, query, timeout_seconds)
    
    def generate_citations(
        self,
        results: Dict[RetrievalSource, RetrievalResult],
    ) -> List[Citation]:
        """Generate citations from retrieval results"""
        citations = []
        
        for source, result in results.items():
            # Create a summary citation for each source
            if isinstance(result.data, dict):
                data_point = f"Retrieved {len(result.data)} data points"
            else:
                data_point = str(result.data)[:100]
            
            citations.append(result.to_citation(data_point))
        
        return citations
    
    def get_freshness_report(
        self,
        results: Dict[RetrievalSource, RetrievalResult],
    ) -> Dict[str, Any]:
        """Get freshness report for retrieved data"""
        report = {
            'sources': {},
            'oldest_seconds': 0,
            'newest_seconds': float('inf'),
            'all_fresh': True,
        }
        
        for source, result in results.items():
            age = result.freshness_seconds
            report['sources'][source.value] = {
                'age_seconds': age,
                'is_fresh': age < self.retrievers[source].cache_ttl_seconds,
            }
            report['oldest_seconds'] = max(report['oldest_seconds'], age)
            report['newest_seconds'] = min(report['newest_seconds'], age)
            
            if age > self.retrievers[source].cache_ttl_seconds:
                report['all_fresh'] = False
        
        return report
    
    def add_retriever(self, source: RetrievalSource, retriever: BaseRetriever) -> None:
        """Add or replace a retriever"""
        self.retrievers[source] = retriever
    
    def clear_cache(self, source: Optional[RetrievalSource] = None) -> None:
        """Clear cache for one or all retrievers"""
        if source:
            if source in self.retrievers:
                self.retrievers[source].cache.clear()
        else:
            for retriever in self.retrievers.values():
                retriever.cache.clear()
