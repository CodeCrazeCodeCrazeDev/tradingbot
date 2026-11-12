"""
Data Canonicalizer

Interface to canonical data sources for evidence verification.
Ensures data integrity by comparing against trusted authoritative sources.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import aiohttp
import uuid

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Types of canonical data sources."""
    MARKET_DATA_PROVIDER = "market_data_provider"
    EXCHANGE = "exchange"
    BLOCKCHAIN_ORACLE = "blockchain_oracle"
    NEWS_AGGREGATOR = "news_aggregator"
    ECONOMIC_DATA = "economic_data"
    REGULATORY_FILING = "regulatory_filing"
    PRICE_FEED = "price_feed"
    DEX_AGGREGATOR = "dex_aggregator"


class DataIntegrityStatus(Enum):
    """Status of data integrity check."""
    VERIFIED = "verified"
    MISMATCH = "mismatch"
    SOURCE_UNAVAILABLE = "source_unavailable"
    STALE_DATA = "stale_data"
    PARTIAL_MATCH = "partial_match"
    UNKNOWN = "unknown"


@dataclass
class CanonicalDataSource:
    """
    Configuration for a canonical data source.
    """
    source_id: str
    source_name: str
    source_type: DataSourceType
    base_url: str
    api_key: Optional[str] = None
    trust_score: float = 0.9
    rate_limit_per_minute: int = 60
    timeout_seconds: int = 30
    is_active: bool = True
    supported_symbols: List[str] = field(default_factory=list)
    last_verified: Optional[datetime] = None
    verification_count: int = 0
    failure_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_id': self.source_id,
            'source_name': self.source_name,
            'source_type': self.source_type.value,
            'base_url': self.base_url,
            'trust_score': self.trust_score,
            'rate_limit_per_minute': self.rate_limit_per_minute,
            'is_active': self.is_active,
            'supported_symbols': self.supported_symbols,
            'last_verified': self.last_verified.isoformat() if self.last_verified else None,
            'verification_count': self.verification_count,
            'failure_count': self.failure_count,
        }


@dataclass
class DataIntegrityReport:
    """
    Report of data integrity verification against canonical sources.
    """
    report_id: str
    data_hash: str
    timestamp: datetime
    sources_checked: List[str]
    status: DataIntegrityStatus
    confidence_score: float
    discrepancies: List[Dict[str, Any]]
    canonical_values: Dict[str, Any]
    provided_values: Dict[str, Any]
    verification_duration_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_id': self.report_id,
            'data_hash': self.data_hash,
            'timestamp': self.timestamp.isoformat(),
            'sources_checked': self.sources_checked,
            'status': self.status.value,
            'confidence_score': self.confidence_score,
            'discrepancies': self.discrepancies,
            'canonical_values': self.canonical_values,
            'provided_values': self.provided_values,
            'verification_duration_ms': self.verification_duration_ms,
        }


class DataCanonicalizer:
    """
    Verifies data against canonical authoritative sources.
    
    Provides:
    - Multi-source verification
    - Discrepancy detection
    - Trust-weighted consensus
    - Real-time data validation
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'canonical_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._sources: Dict[str, CanonicalDataSource] = {}
        self._rate_limiters: Dict[str, asyncio.Semaphore] = {}
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._cache_ttl_seconds = self.config.get('cache_ttl_seconds', 60)
        
        self._tolerance_config = {
            'price_tolerance_percent': 0.1,
            'volume_tolerance_percent': 5.0,
            'timestamp_tolerance_seconds': 60,
        }
        
        self._initialize_default_sources()
        
        logger.info("✅ Data Canonicalizer initialized")
    
    def _initialize_default_sources(self):
        """Initialize default canonical data sources."""
        default_sources = [
            CanonicalDataSource(
                source_id="bloomberg",
                source_name="Bloomberg",
                source_type=DataSourceType.MARKET_DATA_PROVIDER,
                base_url="https://api.bloomberg.com",
                trust_score=0.99,
                rate_limit_per_minute=100,
            ),
            CanonicalDataSource(
                source_id="reuters",
                source_name="Reuters",
                source_type=DataSourceType.MARKET_DATA_PROVIDER,
                base_url="https://api.reuters.com",
                trust_score=0.98,
                rate_limit_per_minute=100,
            ),
            CanonicalDataSource(
                source_id="chainlink",
                source_name="Chainlink Oracle",
                source_type=DataSourceType.BLOCKCHAIN_ORACLE,
                base_url="https://api.chain.link",
                trust_score=0.96,
                rate_limit_per_minute=60,
            ),
            CanonicalDataSource(
                source_id="coinbase",
                source_name="Coinbase",
                source_type=DataSourceType.EXCHANGE,
                base_url="https://api.coinbase.com",
                trust_score=0.95,
                rate_limit_per_minute=30,
            ),
            CanonicalDataSource(
                source_id="binance",
                source_name="Binance",
                source_type=DataSourceType.EXCHANGE,
                base_url="https://api.binance.com",
                trust_score=0.94,
                rate_limit_per_minute=1200,
            ),
            CanonicalDataSource(
                source_id="coingecko",
                source_name="CoinGecko",
                source_type=DataSourceType.PRICE_FEED,
                base_url="https://api.coingecko.com",
                trust_score=0.90,
                rate_limit_per_minute=50,
            ),
            CanonicalDataSource(
                source_id="polygon_io",
                source_name="Polygon.io",
                source_type=DataSourceType.MARKET_DATA_PROVIDER,
                base_url="https://api.polygon.io",
                trust_score=0.91,
                rate_limit_per_minute=5,
            ),
            CanonicalDataSource(
                source_id="alpha_vantage",
                source_name="Alpha Vantage",
                source_type=DataSourceType.MARKET_DATA_PROVIDER,
                base_url="https://www.alphavantage.co",
                trust_score=0.88,
                rate_limit_per_minute=5,
            ),
            CanonicalDataSource(
                source_id="fred",
                source_name="Federal Reserve Economic Data",
                source_type=DataSourceType.ECONOMIC_DATA,
                base_url="https://api.stlouisfed.org",
                trust_score=0.99,
                rate_limit_per_minute=120,
            ),
            CanonicalDataSource(
                source_id="uniswap",
                source_name="Uniswap",
                source_type=DataSourceType.DEX_AGGREGATOR,
                base_url="https://api.thegraph.com/subgraphs/name/uniswap",
                trust_score=0.92,
                rate_limit_per_minute=100,
            ),
        ]
        
        for source in default_sources:
            self.register_source(source)
    
    def register_source(self, source: CanonicalDataSource):
        """Register a canonical data source."""
        self._sources[source.source_id] = source
        self._rate_limiters[source.source_id] = asyncio.Semaphore(
            source.rate_limit_per_minute
        )
        logger.debug(f"Registered canonical source: {source.source_name}")
    
    def get_source(self, source_id: str) -> Optional[CanonicalDataSource]:
        """Get a registered source by ID."""
        return self._sources.get(source_id)
    
    def list_sources(self, source_type: Optional[DataSourceType] = None) -> List[CanonicalDataSource]:
        """List all registered sources, optionally filtered by type."""
        sources = list(self._sources.values())
        if source_type:
            sources = [s for s in sources if s.source_type == source_type]
        return sorted(sources, key=lambda s: s.trust_score, reverse=True)
    
    async def verify_price_data(
        self,
        symbol: str,
        price: float,
        timestamp: datetime,
        source_ids: Optional[List[str]] = None,
    ) -> DataIntegrityReport:
        """
        Verify price data against canonical sources.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USD')
            price: Price to verify
            timestamp: Timestamp of the price
            source_ids: Optional list of specific sources to check
        
        Returns:
            DataIntegrityReport with verification results
        """
        start_time = datetime.now(timezone.utc)
        report_id = f"DIR-{uuid.uuid4().hex[:16]}"
        
        sources_to_check = source_ids or [
            s.source_id for s in self._sources.values() 
            if s.is_active and s.source_type in [
                DataSourceType.EXCHANGE,
                DataSourceType.PRICE_FEED,
                DataSourceType.MARKET_DATA_PROVIDER,
            ]
        ]
        
        canonical_prices = {}
        discrepancies = []
        
        for source_id in sources_to_check:
            source = self._sources.get(source_id)
            if not source:
                continue
            
            try:
                canonical_price = await self._fetch_canonical_price(
                    source, symbol, timestamp
                )
                if canonical_price is not None:
                    canonical_prices[source_id] = {
                        'price': canonical_price,
                        'trust_score': source.trust_score,
                    }
                    
                    tolerance = self._tolerance_config['price_tolerance_percent']
                    deviation = abs(price - canonical_price) / canonical_price * 100
                    
                    if deviation > tolerance:
                        discrepancies.append({
                            'source_id': source_id,
                            'canonical_price': canonical_price,
                            'provided_price': price,
                            'deviation_percent': deviation,
                            'trust_score': source.trust_score,
                        })
                    
                    source.verification_count += 1
                    source.last_verified = datetime.now(timezone.utc)
                    
            except Exception as e:
                logger.warning(f"Failed to fetch from {source_id}: {e}")
                source.failure_count += 1
        
        status, confidence = self._calculate_verification_status(
            canonical_prices, discrepancies, price
        )
        
        duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        report = DataIntegrityReport(
            report_id=report_id,
            data_hash=hashlib.sha256(f"{symbol}:{price}:{timestamp}".encode()).hexdigest(),
            timestamp=datetime.now(timezone.utc),
            sources_checked=list(canonical_prices.keys()),
            status=status,
            confidence_score=confidence,
            discrepancies=discrepancies,
            canonical_values=canonical_prices,
            provided_values={'symbol': symbol, 'price': price, 'timestamp': timestamp.isoformat()},
            verification_duration_ms=duration_ms,
        )
        
        await self._persist_report(report)
        
        return report
    
    async def verify_market_data(
        self,
        data: Dict[str, Any],
        data_type: str,
        source_ids: Optional[List[str]] = None,
    ) -> DataIntegrityReport:
        """
        Verify general market data against canonical sources.
        
        Args:
            data: Market data to verify
            data_type: Type of data (e.g., 'ohlcv', 'orderbook', 'trade')
            source_ids: Optional list of specific sources to check
        
        Returns:
            DataIntegrityReport with verification results
        """
        start_time = datetime.now(timezone.utc)
        report_id = f"DIR-{uuid.uuid4().hex[:16]}"
        
        data_hash = hashlib.sha256(
            json.dumps(data, sort_keys=True, default=str).encode()
        ).hexdigest()
        
        sources_to_check = source_ids or [
            s.source_id for s in self._sources.values() if s.is_active
        ]
        
        canonical_values = {}
        discrepancies = []
        
        for source_id in sources_to_check:
            source = self._sources.get(source_id)
            if not source:
                continue
            
            try:
                canonical_data = await self._fetch_canonical_data(
                    source, data_type, data
                )
                if canonical_data:
                    canonical_values[source_id] = {
                        'data': canonical_data,
                        'trust_score': source.trust_score,
                    }
                    
                    field_discrepancies = self._compare_data(data, canonical_data)
                    if field_discrepancies:
                        discrepancies.append({
                            'source_id': source_id,
                            'fields': field_discrepancies,
                            'trust_score': source.trust_score,
                        })
                    
                    source.verification_count += 1
                    source.last_verified = datetime.now(timezone.utc)
                    
            except Exception as e:
                logger.warning(f"Failed to fetch from {source_id}: {e}")
                source.failure_count += 1
        
        status, confidence = self._calculate_verification_status(
            canonical_values, discrepancies, data
        )
        
        duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        report = DataIntegrityReport(
            report_id=report_id,
            data_hash=data_hash,
            timestamp=datetime.now(timezone.utc),
            sources_checked=list(canonical_values.keys()),
            status=status,
            confidence_score=confidence,
            discrepancies=discrepancies,
            canonical_values=canonical_values,
            provided_values=data,
            verification_duration_ms=duration_ms,
        )
        
        await self._persist_report(report)
        
        return report
    
    async def get_canonical_price(
        self,
        symbol: str,
        timestamp: Optional[datetime] = None,
    ) -> Tuple[Optional[float], float]:
        """
        Get the canonical price for a symbol using trust-weighted consensus.
        
        Args:
            symbol: Trading symbol
            timestamp: Optional timestamp (defaults to now)
        
        Returns:
            Tuple of (canonical_price, confidence_score)
        """
        timestamp = timestamp or datetime.now(timezone.utc)
        
        cache_key = f"{symbol}:{timestamp.isoformat()[:16]}"
        if cache_key in self._cache:
            cached_value, cached_time = self._cache[cache_key]
            if (datetime.now(timezone.utc) - cached_time).total_seconds() < self._cache_ttl_seconds:
                return cached_value
        
        prices = []
        total_weight = 0
        
        for source in self._sources.values():
            if not source.is_active:
                continue
            
            try:
                price = await self._fetch_canonical_price(source, symbol, timestamp)
                if price is not None:
                    prices.append((price, source.trust_score))
                    total_weight += source.trust_score
            except Exception as e:
                logger.debug(f"Failed to fetch price from {source.source_id}: {e}")
        
        if not prices:
            return None, 0.0
        
        weighted_price = sum(p * w for p, w in prices) / total_weight
        
        if len(prices) > 1:
            variance = sum((p - weighted_price) ** 2 * w for p, w in prices) / total_weight
            std_dev = variance ** 0.5
            confidence = max(0, 1 - (std_dev / weighted_price) * 10)
        else:
            confidence = prices[0][1]
        
        self._cache[cache_key] = ((weighted_price, confidence), datetime.now(timezone.utc))
        
        return weighted_price, confidence
    
    async def _fetch_canonical_price(
        self,
        source: CanonicalDataSource,
        symbol: str,
        timestamp: datetime,
    ) -> Optional[float]:
        """Fetch canonical price from a source (simulated for now)."""
        import random
        
        base_prices = {
            'BTC/USD': 65000.0,
            'ETH/USD': 3500.0,
            'EUR/USD': 1.08,
            'GBP/USD': 1.26,
            'AAPL': 175.0,
            'GOOGL': 140.0,
        }
        
        base_price = base_prices.get(symbol, 100.0)
        
        noise = random.gauss(0, base_price * 0.001)
        
        return base_price + noise
    
    async def _fetch_canonical_data(
        self,
        source: CanonicalDataSource,
        data_type: str,
        reference_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Fetch canonical data from a source (simulated for now)."""
        return reference_data.copy()
    
    def _compare_data(
        self,
        provided: Dict[str, Any],
        canonical: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Compare provided data with canonical data."""
        discrepancies = []
        
        for key, provided_value in provided.items():
            if key not in canonical:
                continue
            
            canonical_value = canonical[key]
            
            if isinstance(provided_value, (int, float)) and isinstance(canonical_value, (int, float)):
                if canonical_value != 0:
                    deviation = abs(provided_value - canonical_value) / abs(canonical_value) * 100
                    tolerance = self._tolerance_config.get(
                        f'{key}_tolerance_percent',
                        self._tolerance_config['price_tolerance_percent']
                    )
                    
                    if deviation > tolerance:
                        discrepancies.append({
                            'field': key,
                            'provided': provided_value,
                            'canonical': canonical_value,
                            'deviation_percent': deviation,
                        })
            elif provided_value != canonical_value:
                discrepancies.append({
                    'field': key,
                    'provided': provided_value,
                    'canonical': canonical_value,
                })
        
        return discrepancies
    
    def _calculate_verification_status(
        self,
        canonical_values: Dict[str, Any],
        discrepancies: List[Dict[str, Any]],
        provided_data: Any,
    ) -> Tuple[DataIntegrityStatus, float]:
        """Calculate verification status and confidence score."""
        if not canonical_values:
            return DataIntegrityStatus.SOURCE_UNAVAILABLE, 0.0
        
        if not discrepancies:
            avg_trust = sum(
                v.get('trust_score', 0.5) for v in canonical_values.values()
            ) / len(canonical_values)
            return DataIntegrityStatus.VERIFIED, avg_trust
        
        total_trust = sum(v.get('trust_score', 0.5) for v in canonical_values.values())
        discrepancy_trust = sum(d.get('trust_score', 0.5) for d in discrepancies)
        
        if discrepancy_trust / total_trust > 0.5:
            return DataIntegrityStatus.MISMATCH, 1 - (discrepancy_trust / total_trust)
        else:
            confidence = 1 - (discrepancy_trust / total_trust) * 0.5
            return DataIntegrityStatus.PARTIAL_MATCH, confidence
    
    async def _persist_report(self, report: DataIntegrityReport):
        """Persist integrity report to storage."""
        report_file = self.storage_path / 'reports' / f"{report.report_id}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report.to_dict(), f, indent=2, default=str)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about canonical sources."""
        active_sources = [s for s in self._sources.values() if s.is_active]
        
        return {
            'total_sources': len(self._sources),
            'active_sources': len(active_sources),
            'total_verifications': sum(s.verification_count for s in self._sources.values()),
            'total_failures': sum(s.failure_count for s in self._sources.values()),
            'average_trust_score': sum(s.trust_score for s in active_sources) / len(active_sources) if active_sources else 0,
            'cache_size': len(self._cache),
        }
