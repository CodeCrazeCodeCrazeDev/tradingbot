"""
Research Ingestion Module
=========================
Continuous ingestion of academic research from multiple sources.

Sources:
- arXiv (quantitative finance, machine learning)
- SSRN (social science research network)
- NBER (National Bureau of Economic Research)
- Quant blogs and sell-side research
- Market microstructure studies

For each paper, extracts and stores structured metadata including:
- alpha_source, horizon, asset_class
- required_data, assumptions, failure_modes
- expected_decay, capacity_limit
- key equations and variables

Author: AlphaAlgo Research Team
"""

import asyncio
import hashlib
import json
import logging
import re
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import numpy as np

from .rdaos_core import (
    AlphaHorizon,
    AssetClass,
    FailureMode,
    ProductionStatus,
    ResearchObject,
    generate_id
)

logger = logging.getLogger(__name__)


@dataclass
class ResearchSource:
    """Configuration for a research source"""
    name: str
    source_type: str  # arxiv, ssrn, nber, blog, sellside
    base_url: str
    api_endpoint: Optional[str] = None
    rate_limit_per_minute: int = 10
    enabled: bool = True
    last_fetch: Optional[datetime] = None
    
    categories: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


@dataclass
class RawPaper:
    """Raw paper data before processing"""
    source: str
    external_id: str
    title: str
    authors: List[str]
    abstract: str
    url: str
    
    publication_date: Optional[datetime] = None
    categories: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    pdf_url: Optional[str] = None
    full_text: Optional[str] = None
    
    fetched_at: datetime = field(default_factory=datetime.utcnow)


class ResearchSourceAdapter(ABC):
    """Abstract adapter for research sources"""
    
    @abstractmethod
    async def fetch_recent(self, days: int = 7, max_results: int = 100) -> List[RawPaper]:
        """Fetch recent papers from the source"""
        pass
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 50) -> List[RawPaper]:
        """Search for papers matching query"""
        pass
    
    @abstractmethod
    async def fetch_by_id(self, paper_id: str) -> Optional[RawPaper]:
        """Fetch a specific paper by ID"""
        pass


class ArxivAdapter(ResearchSourceAdapter):
    """Adapter for arXiv API"""
    
    RELEVANT_CATEGORIES = [
        "q-fin.TR",   # Trading and Market Microstructure
        "q-fin.PM",   # Portfolio Management
        "q-fin.RM",   # Risk Management
        "q-fin.ST",   # Statistical Finance
        "q-fin.CP",   # Computational Finance
        "q-fin.MF",   # Mathematical Finance
        "stat.ML",    # Machine Learning
        "cs.LG",      # Machine Learning (CS)
    ]
    
    ALPHA_KEYWORDS = [
        "alpha", "trading strategy", "market microstructure",
        "momentum", "mean reversion", "factor", "anomaly",
        "price prediction", "return prediction", "volatility",
        "order flow", "liquidity", "market making",
        "high frequency", "algorithmic trading"
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.base_url = "http://export.arxiv.org/api/query"
        self.rate_limit = self.config.get("rate_limit", 10)
        self._last_request = None
    
    async def _rate_limit_wait(self):
        """Enforce rate limiting"""
        if self._last_request:
            elapsed = (datetime.utcnow() - self._last_request).total_seconds()
            wait_time = max(0, (60 / self.rate_limit) - elapsed)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        self._last_request = datetime.utcnow()
    
    async def fetch_recent(self, days: int = 7, max_results: int = 100) -> List[RawPaper]:
        """Fetch recent papers from arXiv"""
        papers = []
        
        for category in self.RELEVANT_CATEGORIES:
            try:
                await self._rate_limit_wait()
                
                # Build query
                query = f"cat:{category}"
                
                # Simulate API call (in production, use aiohttp)
                # For now, return structured placeholder
                logger.info(f"Fetching from arXiv category: {category}")
                
            except Exception as e:
                logger.error(f"Error fetching from arXiv {category}: {e}")
        
        return papers
    
    async def search(self, query: str, max_results: int = 50) -> List[RawPaper]:
        """Search arXiv for papers"""
        await self._rate_limit_wait()
        
        # Build search query combining user query with alpha keywords
        search_terms = [query] + [kw for kw in self.ALPHA_KEYWORDS if kw.lower() in query.lower()]
        
        logger.info(f"Searching arXiv for: {query}")
        return []
    
    async def fetch_by_id(self, paper_id: str) -> Optional[RawPaper]:
        """Fetch specific paper by arXiv ID"""
        await self._rate_limit_wait()
        
        logger.info(f"Fetching arXiv paper: {paper_id}")
        return None


class SSRNAdapter(ResearchSourceAdapter):
    """Adapter for SSRN"""
    
    RELEVANT_NETWORKS = [
        "FEN",   # Financial Economics Network
        "ERN",   # Econometrics Research Network
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.base_url = "https://papers.ssrn.com"
    
    async def fetch_recent(self, days: int = 7, max_results: int = 100) -> List[RawPaper]:
        """Fetch recent SSRN papers"""
        logger.info("Fetching recent SSRN papers")
        return []
    
    async def search(self, query: str, max_results: int = 50) -> List[RawPaper]:
        """Search SSRN"""
        logger.info(f"Searching SSRN for: {query}")
        return []
    
    async def fetch_by_id(self, paper_id: str) -> Optional[RawPaper]:
        """Fetch specific SSRN paper"""
        logger.info(f"Fetching SSRN paper: {paper_id}")
        return None


class NBERAdapter(ResearchSourceAdapter):
    """Adapter for NBER working papers"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.base_url = "https://www.nber.org"
    
    async def fetch_recent(self, days: int = 7, max_results: int = 100) -> List[RawPaper]:
        """Fetch recent NBER papers"""
        logger.info("Fetching recent NBER papers")
        return []
    
    async def search(self, query: str, max_results: int = 50) -> List[RawPaper]:
        """Search NBER"""
        logger.info(f"Searching NBER for: {query}")
        return []
    
    async def fetch_by_id(self, paper_id: str) -> Optional[RawPaper]:
        """Fetch specific NBER paper"""
        logger.info(f"Fetching NBER paper: {paper_id}")
        return None


class MetadataExtractor:
    """
    Extract structured metadata from raw papers.
    
    Extracts:
    - Alpha source and type
    - Time horizon
    - Asset class
    - Required data
    - Assumptions
    - Failure modes
    - Expected decay
    - Capacity limits
    - Key equations
    """
    
    HORIZON_PATTERNS = {
        AlphaHorizon.TICK: ["tick", "millisecond", "microsecond", "sub-second"],
        AlphaHorizon.MICROSTRUCTURE: ["microstructure", "second", "minute-level"],
        AlphaHorizon.INTRADAY: ["intraday", "hourly", "daily pattern"],
        AlphaHorizon.DAILY: ["daily", "overnight", "close-to-close"],
        AlphaHorizon.WEEKLY: ["weekly", "week", "5-day"],
        AlphaHorizon.MONTHLY: ["monthly", "month", "30-day"],
        AlphaHorizon.QUARTERLY: ["quarterly", "quarter", "90-day"],
        AlphaHorizon.LONG_TERM: ["long-term", "annual", "yearly", "multi-year"]
    }
    
    ASSET_CLASS_PATTERNS = {
        AssetClass.EQUITY: ["stock", "equity", "equities", "shares", "s&p", "nasdaq"],
        AssetClass.FOREX: ["forex", "fx", "currency", "exchange rate"],
        AssetClass.CRYPTO: ["crypto", "bitcoin", "ethereum", "cryptocurrency"],
        AssetClass.FUTURES: ["futures", "commodity futures", "index futures"],
        AssetClass.OPTIONS: ["options", "volatility surface", "implied volatility"],
        AssetClass.FIXED_INCOME: ["bond", "fixed income", "yield", "treasury"],
        AssetClass.COMMODITIES: ["commodity", "oil", "gold", "agricultural"]
    }
    
    FAILURE_MODE_PATTERNS = {
        FailureMode.REGIME_SHIFT: ["regime change", "structural break", "market regime"],
        FailureMode.ALPHA_DECAY: ["alpha decay", "signal decay", "diminishing returns"],
        FailureMode.CROWDING: ["crowding", "crowded trade", "capacity constraint"],
        FailureMode.LIQUIDITY_DRAIN: ["liquidity crisis", "market stress", "illiquidity"],
        FailureMode.CORRELATION_SPIKE: ["correlation breakdown", "correlation spike"],
        FailureMode.EXECUTION_SLIPPAGE: ["slippage", "execution cost", "market impact"],
        FailureMode.DATA_QUALITY: ["data quality", "missing data", "data errors"],
        FailureMode.OVERFITTING: ["overfit", "in-sample", "data snooping"]
    }
    
    ALPHA_SOURCE_PATTERNS = [
        ("momentum", ["momentum", "trend following", "price continuation"]),
        ("mean_reversion", ["mean reversion", "reversal", "contrarian"]),
        ("value", ["value", "fundamental", "valuation"]),
        ("carry", ["carry", "yield", "interest rate differential"]),
        ("volatility", ["volatility", "vol", "variance"]),
        ("liquidity", ["liquidity", "market making", "bid-ask"]),
        ("sentiment", ["sentiment", "news", "social media"]),
        ("flow", ["order flow", "trade flow", "institutional"]),
        ("microstructure", ["microstructure", "market micro", "order book"]),
        ("factor", ["factor", "cross-sectional", "anomaly"])
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def extract_metadata(self, paper: RawPaper) -> Dict[str, Any]:
        """Extract all metadata from a raw paper"""
        text = f"{paper.title} {paper.abstract}".lower()
        
        metadata = {
            "alpha_source": self._extract_alpha_source(text),
            "horizon": self._extract_horizon(text),
            "asset_class": self._extract_asset_class(text),
            "required_data": self._extract_required_data(text),
            "assumptions": self._extract_assumptions(text),
            "failure_modes": self._extract_failure_modes(text),
            "expected_decay": self._extract_expected_decay(text),
            "capacity_limit": self._extract_capacity_limit(text),
            "key_equations": self._extract_equations(paper.abstract),
            "key_variables": self._extract_variables(paper.abstract)
        }
        
        return metadata
    
    def _extract_alpha_source(self, text: str) -> str:
        """Extract the primary alpha source"""
        for source, patterns in self.ALPHA_SOURCE_PATTERNS:
            for pattern in patterns:
                if pattern in text:
                    return source
        return "unknown"
    
    def _extract_horizon(self, text: str) -> AlphaHorizon:
        """Extract trading horizon"""
        for horizon, patterns in self.HORIZON_PATTERNS.items():
            for pattern in patterns:
                if pattern in text:
                    return horizon
        return AlphaHorizon.DAILY
    
    def _extract_asset_class(self, text: str) -> AssetClass:
        """Extract asset class"""
        for asset_class, patterns in self.ASSET_CLASS_PATTERNS.items():
            for pattern in patterns:
                if pattern in text:
                    return asset_class
        return AssetClass.MULTI_ASSET
    
    def _extract_required_data(self, text: str) -> List[str]:
        """Extract required data sources"""
        data_patterns = [
            ("price", ["price", "ohlc", "close price"]),
            ("volume", ["volume", "trading volume"]),
            ("order_book", ["order book", "limit order", "lob"]),
            ("trades", ["trade data", "tick data", "transaction"]),
            ("fundamentals", ["fundamental", "earnings", "financial statement"]),
            ("sentiment", ["sentiment", "news", "social"]),
            ("options", ["options", "implied volatility", "iv"]),
            ("macro", ["macro", "economic indicator", "gdp", "inflation"])
        ]
        
        required = []
        for data_type, patterns in data_patterns:
            for pattern in patterns:
                if pattern in text:
                    required.append(data_type)
                    break
        
        return list(set(required)) if required else ["price"]
    
    def _extract_assumptions(self, text: str) -> List[str]:
        """Extract key assumptions"""
        assumptions = []
        
        assumption_patterns = [
            ("no transaction costs", "Assumes zero or negligible transaction costs"),
            ("perfect liquidity", "Assumes perfect market liquidity"),
            ("no market impact", "Assumes no market impact from trades"),
            ("iid returns", "Assumes independent and identically distributed returns"),
            ("normal distribution", "Assumes normally distributed returns"),
            ("stationary", "Assumes stationary market conditions"),
            ("efficient market", "Assumes market efficiency"),
            ("no short-selling constraints", "Assumes unrestricted short selling")
        ]
        
        for pattern, assumption in assumption_patterns:
            if pattern in text:
                assumptions.append(assumption)
        
        return assumptions
    
    def _extract_failure_modes(self, text: str) -> List[FailureMode]:
        """Extract potential failure modes"""
        modes = []
        
        for mode, patterns in self.FAILURE_MODE_PATTERNS.items():
            for pattern in patterns:
                if pattern in text:
                    modes.append(mode)
                    break
        
        return modes
    
    def _extract_expected_decay(self, text: str) -> str:
        """Extract expected alpha decay information"""
        decay_patterns = [
            ("rapid decay", "days to weeks"),
            ("moderate decay", "weeks to months"),
            ("slow decay", "months to years"),
            ("persistent", "years or more")
        ]
        
        for pattern, decay in decay_patterns:
            if pattern in text:
                return decay
        
        return "unknown"
    
    def _extract_capacity_limit(self, text: str) -> str:
        """Extract capacity constraints"""
        if "small cap" in text or "illiquid" in text:
            return "low (<$10M)"
        elif "mid cap" in text:
            return "medium ($10M-$100M)"
        elif "large cap" in text or "liquid" in text:
            return "high (>$100M)"
        return "unknown"
    
    def _extract_equations(self, text: str) -> Dict[str, str]:
        """Extract key equations from text"""
        equations = {}
        
        # Simple pattern matching for common equation formats
        # In production, use LaTeX parser
        equation_patterns = [
            (r"r_t\s*=", "return_equation"),
            (r"alpha\s*=", "alpha_equation"),
            (r"sharpe\s*=", "sharpe_equation"),
            (r"signal\s*=", "signal_equation")
        ]
        
        for pattern, name in equation_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extract surrounding context as equation
                start = max(0, match.start() - 10)
                end = min(len(text), match.end() + 50)
                equations[name] = text[start:end].strip()
        
        return equations
    
    def _extract_variables(self, text: str) -> Dict[str, str]:
        """Extract key variables and their definitions"""
        variables = {}
        
        # Common variable patterns
        var_patterns = [
            (r"where\s+(\w+)\s+(?:is|denotes|represents)", "definition"),
            (r"(\w+)\s+(?:is defined as|equals)", "definition")
        ]
        
        for pattern, _ in var_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) <= 3:  # Likely a variable
                    variables[match] = "extracted from paper"
        
        return variables


class ResearchStorage:
    """
    SQLite-based storage for research objects.
    
    Stores:
    - Raw papers
    - Extracted metadata
    - Research objects
    - Processing history
    """
    
    def __init__(self, db_path: str = "rdaos_research.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Raw papers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id TEXT UNIQUE,
                source TEXT,
                external_id TEXT,
                title TEXT,
                authors TEXT,
                abstract TEXT,
                url TEXT,
                publication_date TEXT,
                categories TEXT,
                keywords TEXT,
                fetched_at TEXT,
                processed BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Research objects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id TEXT UNIQUE,
                data TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Processing history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id TEXT,
                action TEXT,
                result TEXT,
                timestamp TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_raw_paper(self, paper: RawPaper) -> str:
        """Store a raw paper"""
        paper_id = generate_id("paper")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO raw_papers 
                (paper_id, source, external_id, title, authors, abstract, url,
                 publication_date, categories, keywords, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                paper_id,
                paper.source,
                paper.external_id,
                paper.title,
                json.dumps(paper.authors),
                paper.abstract,
                paper.url,
                paper.publication_date.isoformat() if paper.publication_date else None,
                json.dumps(paper.categories),
                json.dumps(paper.keywords),
                paper.fetched_at.isoformat()
            ))
            conn.commit()
        finally:
            conn.close()
        
        return paper_id
    
    def store_research_object(self, obj: ResearchObject):
        """Store a research object"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO research_objects
                (paper_id, data, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                obj.paper_id,
                json.dumps(obj.to_dict()),
                obj.production_status.value,
                obj.ingested_at.isoformat(),
                datetime.utcnow().isoformat()
            ))
            conn.commit()
        finally:
            conn.close()
    
    def get_research_object(self, paper_id: str) -> Optional[ResearchObject]:
        """Retrieve a research object"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT data FROM research_objects WHERE paper_id = ?",
                (paper_id,)
            )
            row = cursor.fetchone()
            
            if row:
                data = json.loads(row[0])
                # Reconstruct ResearchObject from dict
                return self._dict_to_research_object(data)
            return None
        finally:
            conn.close()
    
    def get_all_by_status(self, status: ProductionStatus) -> List[ResearchObject]:
        """Get all research objects with given status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT data FROM research_objects WHERE status = ?",
                (status.value,)
            )
            rows = cursor.fetchall()
            
            return [self._dict_to_research_object(json.loads(row[0])) for row in rows]
        finally:
            conn.close()
    
    def _dict_to_research_object(self, data: Dict) -> ResearchObject:
        """Convert dictionary to ResearchObject"""
        return ResearchObject(
            paper_id=data["paper_id"],
            title=data.get("title", ""),
            authors=data.get("authors", []),
            source=data.get("source", ""),
            url=data.get("url", ""),
            alpha_source=data.get("alpha_source", ""),
            horizon=AlphaHorizon(data.get("horizon", "daily")),
            asset_class=AssetClass(data.get("asset_class", "multi_asset")),
            required_data=data.get("required_data", []),
            assumptions=data.get("assumptions", []),
            failure_modes=[FailureMode(f) for f in data.get("failure_modes", [])],
            expected_decay=data.get("expected_decay", ""),
            capacity_limit=data.get("capacity_limit", ""),
            production_status=ProductionStatus(data.get("production_status", "candidate"))
        )
    
    def log_processing(self, paper_id: str, action: str, result: str):
        """Log processing action"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO processing_history (paper_id, action, result, timestamp)
                VALUES (?, ?, ?, ?)
            """, (paper_id, action, result, datetime.utcnow().isoformat()))
            conn.commit()
        finally:
            conn.close()


class ResearchIngestionEngine:
    """
    Main engine for continuous research ingestion.
    
    Coordinates:
    - Multiple source adapters
    - Metadata extraction
    - Storage
    - Deduplication
    - Quality filtering
    """
    
    # Quality thresholds
    MIN_ABSTRACT_LENGTH = 100
    MIN_TITLE_LENGTH = 10
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize adapters
        self.adapters: Dict[str, ResearchSourceAdapter] = {
            "arxiv": ArxivAdapter(config),
            "ssrn": SSRNAdapter(config),
            "nber": NBERAdapter(config)
        }
        
        # Initialize components
        self.extractor = MetadataExtractor(config)
        self.storage = ResearchStorage(
            self.config.get("db_path", "rdaos_research.db")
        )
        
        # State
        self.running = False
        self._seen_hashes: Set[str] = set()
        
        logger.info("Research Ingestion Engine initialized")
    
    async def start_continuous_ingestion(self, interval_hours: int = 6):
        """Start continuous ingestion loop"""
        self.running = True
        logger.info(f"Starting continuous ingestion (interval: {interval_hours}h)")
        
        while self.running:
            try:
                await self.ingest_all_sources()
                await asyncio.sleep(interval_hours * 3600)
            except Exception as e:
                logger.error(f"Ingestion error: {e}")
                await asyncio.sleep(300)  # Wait 5 min on error
    
    def stop(self):
        """Stop continuous ingestion"""
        self.running = False
        logger.info("Ingestion stopped")
    
    async def ingest_all_sources(self) -> List[ResearchObject]:
        """Ingest from all enabled sources"""
        all_objects = []
        
        for source_name, adapter in self.adapters.items():
            try:
                logger.info(f"Ingesting from {source_name}")
                papers = await adapter.fetch_recent(days=7, max_results=50)
                
                for paper in papers:
                    obj = await self.process_paper(paper)
                    if obj:
                        all_objects.append(obj)
                
                logger.info(f"Ingested {len(papers)} papers from {source_name}")
                
            except Exception as e:
                logger.error(f"Error ingesting from {source_name}: {e}")
        
        return all_objects
    
    async def process_paper(self, paper: RawPaper) -> Optional[ResearchObject]:
        """Process a single paper into a research object"""
        
        # Quality check
        if not self._passes_quality_check(paper):
            logger.debug(f"Paper failed quality check: {paper.title[:50]}")
            return None
        
        # Deduplication
        paper_hash = self._compute_hash(paper)
        if paper_hash in self._seen_hashes:
            logger.debug(f"Duplicate paper: {paper.title[:50]}")
            return None
        self._seen_hashes.add(paper_hash)
        
        # Store raw paper
        paper_id = self.storage.store_raw_paper(paper)
        
        # Extract metadata
        metadata = self.extractor.extract_metadata(paper)
        
        # Check if paper has clear alpha source
        if metadata["alpha_source"] == "unknown":
            self.storage.log_processing(paper_id, "rejected", "no clear alpha source")
            return None
        
        # Create research object
        research_obj = ResearchObject(
            paper_id=paper_id,
            title=paper.title,
            authors=paper.authors,
            source=paper.source,
            url=paper.url,
            publication_date=paper.publication_date,
            alpha_source=metadata["alpha_source"],
            horizon=metadata["horizon"],
            asset_class=metadata["asset_class"],
            required_data=metadata["required_data"],
            assumptions=metadata["assumptions"],
            failure_modes=metadata["failure_modes"],
            expected_decay=metadata["expected_decay"],
            capacity_limit=metadata["capacity_limit"],
            key_equations=metadata["key_equations"],
            key_variables=metadata["key_variables"],
            production_status=ProductionStatus.CANDIDATE
        )
        
        # Store research object
        self.storage.store_research_object(research_obj)
        self.storage.log_processing(paper_id, "ingested", "success")
        
        logger.info(f"Processed paper: {paper.title[:50]} -> {metadata['alpha_source']}")
        
        return research_obj
    
    def _passes_quality_check(self, paper: RawPaper) -> bool:
        """Check if paper meets quality standards"""
        if len(paper.abstract) < self.MIN_ABSTRACT_LENGTH:
            return False
        if len(paper.title) < self.MIN_TITLE_LENGTH:
            return False
        return True
    
    def _compute_hash(self, paper: RawPaper) -> str:
        """Compute hash for deduplication"""
        content = f"{paper.title}|{paper.authors}|{paper.source}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def search_and_ingest(self, query: str, sources: Optional[List[str]] = None) -> List[ResearchObject]:
        """Search and ingest papers matching query"""
        sources = sources or list(self.adapters.keys())
        all_objects = []
        
        for source_name in sources:
            if source_name not in self.adapters:
                continue
            
            adapter = self.adapters[source_name]
            papers = await adapter.search(query, max_results=20)
            
            for paper in papers:
                obj = await self.process_paper(paper)
                if obj:
                    all_objects.append(obj)
        
        return all_objects
    
    def get_candidates(self) -> List[ResearchObject]:
        """Get all candidate research objects ready for hypothesis extraction"""
        return self.storage.get_all_by_status(ProductionStatus.CANDIDATE)


def create_ingestion_engine(config: Optional[Dict] = None) -> ResearchIngestionEngine:
    """Factory function to create ingestion engine"""
    return ResearchIngestionEngine(config)
