"""
Research Paper Ingestion Engine

Ingests academic papers from arXiv, SSRN, and other sources.
Extracts text, identifies trading-relevant content, and feeds
into the relevance filtering pipeline.
"""

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class PaperSource(Enum):
    """Sources for research papers."""
    ARXIV = "arxiv"
    SSRN = "ssrn"
    NBER = "nber"
    REPEC = "repec"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    GOOGLE_SCHOLAR = "google_scholar"
    CUSTOM_URL = "custom_url"


class PaperCategory(Enum):
    """Categories of trading-relevant research."""
    ALPHA_GENERATION = auto()
    RISK_MANAGEMENT = auto()
    PORTFOLIO_OPTIMIZATION = auto()
    MARKET_MICROSTRUCTURE = auto()
    MACHINE_LEARNING = auto()
    DEEP_LEARNING = auto()
    REINFORCEMENT_LEARNING = auto()
    TIME_SERIES = auto()
    VOLATILITY_MODELING = auto()
    SENTIMENT_ANALYSIS = auto()
    ALTERNATIVE_DATA = auto()
    EXECUTION_OPTIMIZATION = auto()
    REGIME_DETECTION = auto()
    FACTOR_INVESTING = auto()
    HIGH_FREQUENCY = auto()
    CRYPTO_DEFI = auto()
    OPTIONS_DERIVATIVES = auto()
    STATISTICAL_ARBITRAGE = auto()


@dataclass
class ResearchPaper:
    """A research paper with extracted metadata."""
    id: str
    title: str
    authors: List[str]
    abstract: str
    source: PaperSource
    url: str
    published_date: Optional[datetime] = None
    categories: List[PaperCategory] = field(default_factory=list)
    full_text: str = ""
    key_findings: List[str] = field(default_factory=list)
    methodology: str = ""
    datasets_used: List[str] = field(default_factory=list)
    performance_claims: List[Dict[str, Any]] = field(default_factory=list)
    code_available: bool = False
    code_url: str = ""
    citation_count: int = 0
    relevance_score: float = 0.0
    ingested_at: datetime = field(default_factory=datetime.utcnow)
    content_hash: str = ""


class PaperIngestionEngine:
    """
    Ingests research papers from multiple academic sources.
    
    Monitors new literature, downloads papers, extracts text,
    and prepares them for the relevance filtering stage.
    """

    # Trading-relevant search terms for each source
    SEARCH_QUERIES = [
        "algorithmic trading machine learning",
        "deep reinforcement learning portfolio optimization",
        "market microstructure order flow",
        "statistical arbitrage pairs trading",
        "volatility forecasting neural network",
        "sentiment analysis financial markets",
        "alternative data alpha generation",
        "regime detection hidden markov",
        "execution optimization slippage",
        "factor investing momentum value",
        "cryptocurrency trading strategy",
        "risk management tail risk",
        "high frequency trading latency",
        "options pricing deep learning",
        "time series forecasting transformer",
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.papers: Dict[str, ResearchPaper] = {}
        self.ingestion_history: List[Dict[str, Any]] = []
        self.storage_dir = Path(self.config.get(
            'storage_dir', 'data/research_papers'
        ))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.max_papers_per_query = self.config.get('max_papers_per_query', 20)
        self.lookback_days = self.config.get('lookback_days', 30)
        logger.info("PaperIngestionEngine initialized")

    async def ingest_new_papers(self) -> List[ResearchPaper]:
        """
        Scan all sources for new trading-relevant papers.
        Returns list of newly ingested papers.
        """
        new_papers = []
        
        for source in [PaperSource.ARXIV, PaperSource.SSRN, PaperSource.SEMANTIC_SCHOLAR]:
            try:
                papers = await self._ingest_from_source(source)
                new_papers.extend(papers)
                logger.info(f"Ingested {len(papers)} papers from {source.value}")
            except Exception as e:
                logger.error(f"Error ingesting from {source.value}: {e}")

        # Deduplicate by content hash
        seen = set()
        unique = []
        for p in new_papers:
            if p.content_hash not in seen:
                seen.add(p.content_hash)
                unique.append(p)
                self.papers[p.id] = p

        self.ingestion_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'total_found': len(new_papers),
            'unique': len(unique),
            'sources': [s.value for s in [PaperSource.ARXIV, PaperSource.SSRN]],
        })

        logger.info(f"Total new unique papers: {len(unique)}")
        return unique

    async def _ingest_from_source(self, source: PaperSource) -> List[ResearchPaper]:
        """Ingest papers from a specific source."""
        papers = []

        if source == PaperSource.ARXIV:
            papers = await self._ingest_arxiv()
        elif source == PaperSource.SSRN:
            papers = await self._ingest_ssrn()
        elif source == PaperSource.SEMANTIC_SCHOLAR:
            papers = await self._ingest_semantic_scholar()

        return papers

    async def _ingest_arxiv(self) -> List[ResearchPaper]:
        """Ingest papers from arXiv API."""
        papers = []
        try:
            import urllib.request
            import xml.etree.ElementTree as ET

            for query in self.SEARCH_QUERIES[:5]:
                encoded_query = query.replace(' ', '+')
                url = (
                    f"http://export.arxiv.org/api/query?"
                    f"search_query=all:{encoded_query}"
                    f"&start=0&max_results={self.max_papers_per_query}"
                    f"&sortBy=submittedDate&sortOrder=descending"
                )

                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'AlphaAlgo/1.0'})
                    with urllib.request.urlopen(req, timeout=30) as response:
                        xml_data = response.read().decode('utf-8')

                    root = ET.fromstring(xml_data)
                    ns = {'atom': 'http://www.w3.org/2005/Atom'}

                    for entry in root.findall('atom:entry', ns):
                        title = entry.find('atom:title', ns)
                        summary = entry.find('atom:summary', ns)
                        paper_id = entry.find('atom:id', ns)
                        published = entry.find('atom:published', ns)

                        authors = []
                        for author in entry.findall('atom:author', ns):
                            name = author.find('atom:name', ns)
                            if name is not None and name.text:
                                authors.append(name.text)

                        if title is not None and summary is not None:
                            title_text = title.text.strip().replace('\n', ' ')
                            abstract_text = summary.text.strip().replace('\n', ' ')
                            paper_url = paper_id.text.strip() if paper_id is not None else ""

                            content_hash = hashlib.sha256(
                                (title_text + abstract_text).encode()
                            ).hexdigest()[:16]

                            pub_date = None
                            if published is not None and published.text:
                                try:
                                    pub_date = datetime.fromisoformat(
                                        published.text.replace('Z', '+00:00')
                                    )
                                except ValueError:
                                    pass

                            paper = ResearchPaper(
                                id=f"arxiv-{content_hash}",
                                title=title_text,
                                authors=authors,
                                abstract=abstract_text,
                                source=PaperSource.ARXIV,
                                url=paper_url,
                                published_date=pub_date,
                                categories=self._categorize_paper(title_text, abstract_text),
                                content_hash=content_hash,
                            )
                            papers.append(paper)

                    # Rate limit between queries
                    await asyncio.sleep(3)

                except Exception as e:
                    logger.warning(f"arXiv query failed for '{query}': {e}")
                    continue

        except ImportError as e:
            logger.error(f"Missing dependency for arXiv ingestion: {e}")

        return papers

    async def _ingest_ssrn(self) -> List[ResearchPaper]:
        """Ingest papers from SSRN (via web scraping or API)."""
        papers = []
        # SSRN doesn't have a public API; use Semantic Scholar as proxy
        logger.info("SSRN ingestion via Semantic Scholar proxy")
        return papers

    async def _ingest_semantic_scholar(self) -> List[ResearchPaper]:
        """Ingest papers from Semantic Scholar API."""
        papers = []
        try:
            import urllib.request

            for query in self.SEARCH_QUERIES[:5]:
                encoded_query = query.replace(' ', '%20')
                url = (
                    f"https://api.semanticscholar.org/graph/v1/paper/search"
                    f"?query={encoded_query}&limit=10"
                    f"&fields=title,abstract,authors,year,citationCount,url,externalIds"
                )

                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'AlphaAlgo/1.0'})
                    with urllib.request.urlopen(req, timeout=30) as response:
                        data = json.loads(response.read().decode('utf-8'))

                    for item in data.get('data', []):
                        title = item.get('title', '')
                        abstract = item.get('abstract', '') or ''
                        authors = [a.get('name', '') for a in item.get('authors', [])]
                        paper_url = item.get('url', '')
                        citations = item.get('citationCount', 0)

                        if not title:
                            continue

                        content_hash = hashlib.sha256(
                            (title + abstract).encode()
                        ).hexdigest()[:16]

                        paper = ResearchPaper(
                            id=f"s2-{content_hash}",
                            title=title,
                            authors=authors,
                            abstract=abstract,
                            source=PaperSource.SEMANTIC_SCHOLAR,
                            url=paper_url,
                            categories=self._categorize_paper(title, abstract),
                            citation_count=citations or 0,
                            content_hash=content_hash,
                        )
                        papers.append(paper)

                    await asyncio.sleep(1)

                except Exception as e:
                    logger.warning(f"Semantic Scholar query failed for '{query}': {e}")
                    continue

        except ImportError as e:
            logger.error(f"Missing dependency for Semantic Scholar: {e}")

        return papers

    def _categorize_paper(self, title: str, abstract: str) -> List[PaperCategory]:
        """Auto-categorize paper based on title and abstract keywords."""
        text = (title + " " + abstract).lower()
        categories = []

        keyword_map = {
            PaperCategory.ALPHA_GENERATION: ['alpha', 'anomaly', 'return prediction', 'stock selection'],
            PaperCategory.RISK_MANAGEMENT: ['risk management', 'var ', 'value at risk', 'tail risk', 'drawdown'],
            PaperCategory.PORTFOLIO_OPTIMIZATION: ['portfolio optimization', 'asset allocation', 'markowitz', 'mean-variance'],
            PaperCategory.MARKET_MICROSTRUCTURE: ['microstructure', 'order book', 'bid-ask', 'market making'],
            PaperCategory.MACHINE_LEARNING: ['machine learning', 'random forest', 'gradient boosting', 'xgboost'],
            PaperCategory.DEEP_LEARNING: ['deep learning', 'neural network', 'lstm', 'transformer', 'attention'],
            PaperCategory.REINFORCEMENT_LEARNING: ['reinforcement learning', 'q-learning', 'policy gradient', 'dqn'],
            PaperCategory.TIME_SERIES: ['time series', 'forecasting', 'arima', 'garch'],
            PaperCategory.VOLATILITY_MODELING: ['volatility', 'stochastic volatility', 'implied volatility'],
            PaperCategory.SENTIMENT_ANALYSIS: ['sentiment', 'nlp', 'text mining', 'news'],
            PaperCategory.ALTERNATIVE_DATA: ['alternative data', 'satellite', 'social media', 'web scraping'],
            PaperCategory.EXECUTION_OPTIMIZATION: ['execution', 'slippage', 'market impact', 'optimal execution'],
            PaperCategory.REGIME_DETECTION: ['regime', 'hidden markov', 'change point', 'structural break'],
            PaperCategory.FACTOR_INVESTING: ['factor', 'momentum', 'value', 'quality', 'size'],
            PaperCategory.HIGH_FREQUENCY: ['high frequency', 'hft', 'latency', 'tick data'],
            PaperCategory.CRYPTO_DEFI: ['cryptocurrency', 'bitcoin', 'defi', 'blockchain'],
            PaperCategory.STATISTICAL_ARBITRAGE: ['arbitrage', 'pairs trading', 'cointegration', 'mean reversion'],
        }

        for category, keywords in keyword_map.items():
            if any(kw in text for kw in keywords):
                categories.append(category)

        return categories or [PaperCategory.MACHINE_LEARNING]

    async def ingest_from_url(self, url: str) -> Optional[ResearchPaper]:
        """Ingest a specific paper from a URL."""
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={'User-Agent': 'AlphaAlgo/1.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode('utf-8', errors='replace')

            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            # Extract title from HTML if possible
            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
            title = title_match.group(1) if title_match else f"Paper from {url}"

            paper = ResearchPaper(
                id=f"url-{content_hash}",
                title=title,
                authors=[],
                abstract=content[:2000],
                source=PaperSource.CUSTOM_URL,
                url=url,
                full_text=content,
                content_hash=content_hash,
            )
            self.papers[paper.id] = paper
            return paper

        except Exception as e:
            logger.error(f"Failed to ingest paper from {url}: {e}")
            return None

    def get_recent_papers(self, days: int = 7) -> List[ResearchPaper]:
        """Get papers ingested in the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [
            p for p in self.papers.values()
            if p.ingested_at >= cutoff
        ]

    def save_papers(self):
        """Save ingested papers to disk."""
        data = {}
        for pid, paper in self.papers.items():
            data[pid] = {
                'id': paper.id,
                'title': paper.title,
                'authors': paper.authors,
                'abstract': paper.abstract[:500],
                'source': paper.source.value,
                'url': paper.url,
                'categories': [c.name for c in paper.categories],
                'citation_count': paper.citation_count,
                'relevance_score': paper.relevance_score,
                'ingested_at': paper.ingested_at.isoformat(),
                'content_hash': paper.content_hash,
            }

        path = self.storage_dir / 'papers_index.json'
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(data)} papers to {path}")
