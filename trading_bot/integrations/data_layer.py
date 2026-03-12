"""
Data Layer Integration - Unified data access and management
Integrates all data-related components into a cohesive layer
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from trading_bot.system_interfaces import (
    IDataProvider,
    MarketData,
    ComponentStatus,
    ComponentHealth,
)

logger = logging.getLogger(__name__)


@dataclass
class DataQualityMetrics:
    """Data quality metrics"""
    staleness_score: float  # 0-1, 1 = fresh
    completeness_score: float  # 0-1, 1 = complete
    accuracy_score: float  # 0-1, 1 = accurate
    consistency_score: float  # 0-1, 1 = consistent
    overall_score: float  # 0-1, weighted average


class UnifiedDataLayer(IDataProvider):
    """
    Unified Data Layer - Integrates all data sources and quality systems
    
    Integrates:
    - Market data streams (real-time and historical)
    - Data validation and quarantine
    - Staleness detection
    - Time synchronization
    - Multiple data providers with failover
    - Caching and optimization
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.status = ComponentStatus.UNINITIALIZED
        
        # Data providers
        self.primary_provider = None
        self.backup_providers = []
        self.active_provider = None
        
        # Quality systems
        self.validator = None
        self.staleness_detector = None
        self.time_sync = None
        
        # Cache
        self.cache = {}
        self.cache_ttl = config.get('cache_ttl_seconds', 300)
        
        # Subscriptions
        self.subscriptions = {}
        
        # Metrics
        self.metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'provider_failures': 0,
            'failovers': 0,
            'data_quality_issues': 0,
        }
        
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize data layer"""
        logger.info("Initializing Unified Data Layer...")
        
        try:
            # Initialize data providers
            await self._initialize_providers()
            
            # Initialize quality systems
            await self._initialize_quality_systems()
            
            # Set active provider
            self.active_provider = self.primary_provider
            
            self.status = ComponentStatus.READY
            logger.info("Unified Data Layer initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing data layer: {e}", exc_info=True)
            self.status = ComponentStatus.ERROR
            return False
    
    async def _initialize_providers(self):
        """Initialize data providers"""
        # In real implementation, would initialize actual providers
        # For now, create mock providers
        
        primary_source = self.config.get('primary_data_source', 'yahoo')
        backup_sources = self.config.get('backup_data_sources', [])
        
        logger.info(f"Primary data source: {primary_source}")
        logger.info(f"Backup data sources: {backup_sources}")
        
        # Placeholder - actual implementation would import and initialize real providers
        self.primary_provider = MockDataProvider(primary_source)
        self.backup_providers = [MockDataProvider(source) for source in backup_sources]
    
    async def _initialize_quality_systems(self):
        """Initialize data quality systems"""
        # Placeholder - actual implementation would initialize real quality systems
        logger.info("Initializing data quality systems...")
        
        if self.config.get('enable_data_validation', True):
            self.validator = MockValidator()
        
        if self.config.get('enable_staleness_detection', True):
            self.staleness_detector = MockStalenessDetector()
        
        self.time_sync = MockTimeSync()
    
    async def start(self) -> bool:
        """Start data layer"""
        if self.status != ComponentStatus.READY:
            logger.error("Data layer not ready")
            return False
        
        logger.info("Starting Unified Data Layer...")
        self.status = ComponentStatus.RUNNING
        return True
    
    async def stop(self) -> bool:
        """Stop data layer"""
        logger.info("Stopping Unified Data Layer...")
        
        # Unsubscribe from all
        for symbol in list(self.subscriptions.keys()):
            await self.unsubscribe(symbol)
        
        self.status = ComponentStatus.STOPPED
        return True
    
    async def get_market_data(
        self,
        symbol: str,
        timeframe: str = '1m',
        limit: int = 100
    ) -> List[MarketData]:
        """
        Get market data with automatic failover and quality checks
        """
        self.metrics['total_requests'] += 1
        
        # Check cache first
        cache_key = f"{symbol}_{timeframe}_{limit}"
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if datetime.utcnow() - cache_entry['timestamp'] < timedelta(seconds=self.cache_ttl):
                self.metrics['cache_hits'] += 1
                return cache_entry['data']
        
        self.metrics['cache_misses'] += 1
        
        # Try primary provider
        data = await self._fetch_with_failover(symbol, timeframe, limit)
        
        if not data:
            logger.error(f"Failed to fetch data for {symbol}")
            return []
        
        # Validate data quality
        if self.validator:
            quality = await self._validate_data_quality(data)
            if quality.overall_score < 0.7:
                logger.warning(f"Low data quality for {symbol}: {quality.overall_score:.2f}")
                self.metrics['data_quality_issues'] += 1
        
        # Cache the data
        self.cache[cache_key] = {
            'data': data,
            'timestamp': datetime.utcnow()
        }
        
        return data
    
    async def _fetch_with_failover(
        self,
        symbol: str,
        timeframe: str,
        limit: int
    ) -> List[MarketData]:
        """Fetch data with automatic failover to backup providers"""
        
        # Try active provider
        try:
            data = await self.active_provider.fetch(symbol, timeframe, limit)
            if data:
                return data
        except Exception as e:
            logger.error(f"Error fetching from {self.active_provider.name}: {e}")
            self.metrics['provider_failures'] += 1
        
        # Try backup providers
        for backup in self.backup_providers:
            try:
                logger.info(f"Failing over to backup provider: {backup.name}")
                data = await backup.fetch(symbol, timeframe, limit)
                if data:
                    self.active_provider = backup
                    self.metrics['failovers'] += 1
                    return data
            except Exception as e:
                logger.error(f"Error fetching from backup {backup.name}: {e}")
                self.metrics['provider_failures'] += 1
        
        return []
    
    async def _validate_data_quality(self, data: List[MarketData]) -> DataQualityMetrics:
        """Validate data quality"""
        if not data:
            return DataQualityMetrics(0, 0, 0, 0, 0)
        
        # Check staleness
        staleness_score = 1.0
        if self.staleness_detector:
            latest = data[-1].timestamp
            age_seconds = (datetime.utcnow() - latest).total_seconds()
            staleness_score = max(0, 1 - (age_seconds / 300))  # 5 min threshold
        
        # Check completeness (no gaps)
        completeness_score = 1.0
        for i in range(1, len(data)):
            if data[i].timestamp <= data[i-1].timestamp:
                completeness_score -= 0.1
        completeness_score = max(0, completeness_score)
        
        # Check accuracy (no outliers)
        accuracy_score = 1.0
        prices = [d.close for d in data]
        if len(prices) > 1:
            mean = sum(prices) / len(prices)
            std = (sum((p - mean) ** 2 for p in prices) / len(prices)) ** 0.5
            outliers = sum(1 for p in prices if abs(p - mean) > 3 * std)
            accuracy_score = max(0, 1 - (outliers / len(prices)))
        
        # Check consistency
        consistency_score = 1.0
        for d in data:
            if d.high < d.low or d.close > d.high or d.close < d.low:
                consistency_score -= 0.1
        consistency_score = max(0, consistency_score)
        
        # Overall score (weighted average)
        overall = (
            staleness_score * 0.3 +
            completeness_score * 0.25 +
            accuracy_score * 0.25 +
            consistency_score * 0.2
        )
        
        return DataQualityMetrics(
            staleness_score=staleness_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            overall_score=overall
        )
    
    async def subscribe(self, symbol: str, callback) -> bool:
        """Subscribe to real-time data"""
        if symbol in self.subscriptions:
            logger.warning(f"Already subscribed to {symbol}")
            return True
        
        self.subscriptions[symbol] = {
            'callback': callback,
            'started_at': datetime.utcnow()
        }
        
        logger.info(f"Subscribed to {symbol}")
        return True
    
    async def unsubscribe(self, symbol: str) -> bool:
        """Unsubscribe from real-time data"""
        if symbol in self.subscriptions:
            del self.subscriptions[symbol]
            logger.info(f"Unsubscribed from {symbol}")
            return True
        return False
    
    async def health_check(self) -> ComponentHealth:
        """Check data layer health"""
        errors = []
        warnings = []
        
        # Check provider health
        if not self.active_provider:
            errors.append("No active data provider")
        
        # Check cache hit rate
        total = self.metrics['cache_hits'] + self.metrics['cache_misses']
        if total > 0:
            hit_rate = self.metrics['cache_hits'] / total
            if hit_rate < 0.5:
                warnings.append(f"Low cache hit rate: {hit_rate:.2%}")
        
        # Check failure rate
        if self.metrics['provider_failures'] > 10:
            warnings.append(f"High provider failure count: {self.metrics['provider_failures']}")
        
        return ComponentHealth(
            status=ComponentStatus.ERROR if errors else self.status,
            message="OK" if not errors else f"{len(errors)} errors",
            metrics={
                'total_requests': self.metrics['total_requests'],
                'cache_hit_rate': self.metrics['cache_hits'] / max(1, total),
                'provider_failures': self.metrics['provider_failures'],
                'failovers': self.metrics['failovers'],
                'data_quality_issues': self.metrics['data_quality_issues'],
            },
            last_check=datetime.utcnow(),
            errors=errors,
            warnings=warnings
        )
    
    def get_status(self) -> ComponentStatus:
        """Get current status"""
        return self.status


# Mock implementations (to be replaced with real implementations)

class MockDataProvider:
    """Mock data provider"""
    def __init__(self, name: str):
        self.name = name
    
    async def fetch(self, symbol: str, timeframe: str, limit: int) -> List[MarketData]:
        """Mock fetch"""
        # Return mock data
        now = datetime.utcnow()
        return [
            MarketData(
                symbol=symbol,
                timestamp=now - timedelta(minutes=i),
                open=100.0 + i,
                high=101.0 + i,
                low=99.0 + i,
                close=100.5 + i,
                volume=1000000.0
            )
            for i in range(limit)
        ]


class MockValidator:
    """Mock validator"""
    pass


class MockStalenessDetector:
    """Mock staleness detector"""
    pass


class MockTimeSync:
    """Mock time sync"""
    pass


__all__ = [
    'UnifiedDataLayer',
    'DataQualityMetrics',
]
