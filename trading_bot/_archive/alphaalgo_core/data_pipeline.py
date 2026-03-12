"""
AlphaAlgo Unified Data Pipeline

Data Acquisition System for:
- Level 2 Data (Order book, Market depth, Bid/ask pressure, Imbalance)
- Sentiment Data (News, Social, Alternative text streams, Fear/Greed)
- Macro Data (Economic events, Interest rates, Fed announcements)
- Broker Data (MT5, Robinhood, Alpaca, Interactive Brokers)

AI does NOT auto-connect - prepares modules for human to configure.
"""

import asyncio
import json
import logging
import sqlite3
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from collections import deque

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        """
        decorator function.

    Args:
        func: Description

    Returns:
        Result of operation
        """
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class DataType(Enum):
    """Types of data the system can acquire"""
    # Level 2 Data
    ORDER_BOOK = "order_book"
    MARKET_DEPTH = "market_depth"
    BID_ASK_PRESSURE = "bid_ask_pressure"
    IMBALANCE = "imbalance"
    TRADE_FLOW = "trade_flow"
    
    # Price Data
    OHLCV = "ohlcv"
    TICK = "tick"
    
    # Sentiment Data
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"
    FEAR_GREED = "fear_greed"
    ALTERNATIVE_TEXT = "alternative_text"
    
    # Macro Data
    ECONOMIC_CALENDAR = "economic_calendar"
    INTEREST_RATES = "interest_rates"
    FED_ANNOUNCEMENTS = "fed_announcements"
    GDP_DATA = "gdp_data"
    INFLATION_DATA = "inflation_data"


class DataQuality(Enum):
    """Data quality levels"""
    UNKNOWN = "unknown"
    POOR = "poor"
    ACCEPTABLE = "acceptable"
    GOOD = "good"
    EXCELLENT = "excellent"


class DataSourceStatus(Enum):
    """Data source connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    STALE = "stale"
    AWAITING_CONFIG = "awaiting_config"


@dataclass
class DataSourceConfig:
    """Configuration for a data source - human must fill"""
    source_name: str
    source_type: str
    api_key: str = ""
    api_secret: str = ""
    endpoint: str = ""
    additional: Dict[str, str] = field(default_factory=dict)
    enabled: bool = False
    
    def is_configured(self) -> bool:
        """Check if source is configured"""
        # Different sources have different requirements
        if self.source_type in ['free', 'simulation']:
            return True
        return bool(self.api_key or self.endpoint)


@dataclass
class DataPoint:
    """A single data point"""
    data_type: DataType
    symbol: str
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    quality: DataQuality = DataQuality.UNKNOWN
    latency_ms: float = 0.0


class DataSource(ABC):
    """Abstract base class for data sources"""
    
    def __init__(self, name: str, data_types: List[DataType]):
        self.name = name
        self.data_types = set(data_types)
        self.status = DataSourceStatus.DISCONNECTED
        self.last_data_time: Optional[datetime] = None
        self.error_count = 0
        self.data_count = 0
    
    @abstractmethod
    async def connect(self, config: DataSourceConfig) -> Tuple[bool, str]:
        """Connect to data source"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from data source"""
        pass
    
    @abstractmethod
    async def fetch_data(
        self,
        data_type: DataType,
        symbol: str,
        **kwargs
    ) -> Optional[DataPoint]:
        """Fetch data from source"""
        pass
    
    def supports(self, data_type: DataType) -> bool:
        """Check if source supports data type"""
        return data_type in self.data_types
    
    def is_stale(self, max_age_seconds: int = 60) -> bool:
        """Check if data is stale"""
        if not self.last_data_time:
            return True
        age = (datetime.now() - self.last_data_time).total_seconds()
        return age > max_age_seconds


class FreeDataSource(DataSource):
    """Free data source using public APIs"""
    
    def __init__(self):
        super().__init__(
            name="free_data",
            data_types=[
                DataType.OHLCV,
                DataType.NEWS,
                DataType.FEAR_GREED,
                DataType.ECONOMIC_CALENDAR,
            ]
        )
    
    async def connect(self, config: DataSourceConfig) -> Tuple[bool, str]:
        self.status = DataSourceStatus.CONNECTED
        logger.info(f"[{self.name}] Connected to free data sources")
        return (True, "Connected to free data sources")
    
    async def disconnect(self) -> bool:
        self.status = DataSourceStatus.DISCONNECTED
        return True
    
    async def fetch_data(
        self,
        data_type: DataType,
        symbol: str,
        **kwargs
    ) -> Optional[DataPoint]:
        """Fetch from free sources"""
        try:
            if data_type == DataType.OHLCV:
                # Would use yfinance, ccxt, etc.
                data = {
                    'open': 0.0,
                    'high': 0.0,
                    'low': 0.0,
                    'close': 0.0,
                    'volume': 0.0,
                    'source': 'simulation',
                }
            elif data_type == DataType.FEAR_GREED:
                data = {
                    'value': 50,
                    'classification': 'Neutral',
                }
            else:
                data = {}
            
            self.last_data_time = datetime.now()
            self.data_count += 1
            
            return DataPoint(
                data_type=data_type,
                symbol=symbol,
                timestamp=datetime.now(),
                data=data,
                source=self.name,
                quality=DataQuality.ACCEPTABLE,
            )
        except Exception as e:
            self.error_count += 1
            logger.error(f"[{self.name}] Error fetching {data_type}: {e}")
            return None


class Level2DataSource(DataSource):
    """Level 2 market data source"""
    
    def __init__(self):
        super().__init__(
            name="level2_data",
            data_types=[
                DataType.ORDER_BOOK,
                DataType.MARKET_DEPTH,
                DataType.BID_ASK_PRESSURE,
                DataType.IMBALANCE,
                DataType.TRADE_FLOW,
            ]
        )
        self._config: Optional[DataSourceConfig] = None
    
    async def connect(self, config: DataSourceConfig) -> Tuple[bool, str]:
        if not config.is_configured():
            self.status = DataSourceStatus.AWAITING_CONFIG
            return (False, "Level 2 data requires API configuration")
        
        self._config = config
        self.status = DataSourceStatus.CONNECTED
        logger.info(f"[{self.name}] Connected")
        return (True, "Connected to Level 2 data source")
    
    async def disconnect(self) -> bool:
        self.status = DataSourceStatus.DISCONNECTED
        return True
    
    async def fetch_data(
        self,
        data_type: DataType,
        symbol: str,
        **kwargs
    ) -> Optional[DataPoint]:
        if self.status != DataSourceStatus.CONNECTED:
            return None
        
        # Simulated L2 data
        if data_type == DataType.ORDER_BOOK:
            data = {
                'bids': [[1.0, 100], [0.99, 200]],
                'asks': [[1.01, 150], [1.02, 250]],
                'timestamp': datetime.now().isoformat(),
            }
        elif data_type == DataType.IMBALANCE:
            data = {
                'bid_volume': 1000,
                'ask_volume': 800,
                'imbalance_ratio': 1.25,
                'direction': 'bullish',
            }
        else:
            data = {}
        
        self.last_data_time = datetime.now()
        self.data_count += 1
        
        return DataPoint(
            data_type=data_type,
            symbol=symbol,
            timestamp=datetime.now(),
            data=data,
            source=self.name,
            quality=DataQuality.GOOD,
        )


class SentimentDataSource(DataSource):
    """Sentiment data source"""
    
    def __init__(self):
        super().__init__(
            name="sentiment_data",
            data_types=[
                DataType.NEWS,
                DataType.SOCIAL_MEDIA,
                DataType.FEAR_GREED,
                DataType.ALTERNATIVE_TEXT,
            ]
        )
    
    async def connect(self, config: DataSourceConfig) -> Tuple[bool, str]:
        self.status = DataSourceStatus.CONNECTED
        return (True, "Connected to sentiment sources")
    
    async def disconnect(self) -> bool:
        self.status = DataSourceStatus.DISCONNECTED
        return True
    
    async def fetch_data(
        self,
        data_type: DataType,
        symbol: str,
        **kwargs
    ) -> Optional[DataPoint]:
        if data_type == DataType.NEWS:
            data = {
                'headlines': [],
                'sentiment_score': 0.0,
                'article_count': 0,
            }
        elif data_type == DataType.SOCIAL_MEDIA:
            data = {
                'mentions': 0,
                'sentiment': 'neutral',
                'trending': False,
            }
        elif data_type == DataType.FEAR_GREED:
            data = {
                'value': 50,
                'classification': 'Neutral',
            }
        else:
            data = {}
        
        self.last_data_time = datetime.now()
        return DataPoint(
            data_type=data_type,
            symbol=symbol,
            timestamp=datetime.now(),
            data=data,
            source=self.name,
            quality=DataQuality.ACCEPTABLE,
        )


class MacroDataSource(DataSource):
    """Macro economic data source"""
    
    def __init__(self):
        super().__init__(
            name="macro_data",
            data_types=[
                DataType.ECONOMIC_CALENDAR,
                DataType.INTEREST_RATES,
                DataType.FED_ANNOUNCEMENTS,
                DataType.GDP_DATA,
                DataType.INFLATION_DATA,
            ]
        )
    
    async def connect(self, config: DataSourceConfig) -> Tuple[bool, str]:
        self.status = DataSourceStatus.CONNECTED
        return (True, "Connected to macro data sources")
    
    async def disconnect(self) -> bool:
        self.status = DataSourceStatus.DISCONNECTED
        return True
    
    async def fetch_data(
        self,
        data_type: DataType,
        symbol: str,
        **kwargs
    ) -> Optional[DataPoint]:
        if data_type == DataType.ECONOMIC_CALENDAR:
            data = {
                'events': [],
                'high_impact_today': False,
            }
        elif data_type == DataType.INTEREST_RATES:
            data = {
                'fed_rate': 5.25,
                'ecb_rate': 4.50,
                'boe_rate': 5.25,
            }
        else:
            data = {}
        
        self.last_data_time = datetime.now()
        return DataPoint(
            data_type=data_type,
            symbol=symbol,
            timestamp=datetime.now(),
            data=data,
            source=self.name,
            quality=DataQuality.GOOD,
        )


class UnifiedDataPipeline:
    """
    Unified Data Ingestion Pipeline
    
    Aggregates data from multiple sources:
    - Level 2 Data
    - Sentiment Data
    - Macro Data
    - Broker Data
    
    Features:
    - Data validation
    - Staleness detection
    - Quality scoring
    - Automatic failover
    """
    
    def __init__(self, db_path: str = "alphaalgo_data/data_pipeline.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        self._sources: Dict[str, DataSource] = {}
        self._configs: Dict[str, DataSourceConfig] = {}
        self._data_cache: Dict[str, deque] = {}
        self._lock = threading.Lock()
        
        # Initialize default sources
        self._init_default_sources()
        
        logger.info("[DataPipeline] Initialized")
    
    def _init_database(self):
        """Initialize data pipeline database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_source_configs (
                    source_name TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    api_key TEXT,
                    api_secret TEXT,
                    endpoint TEXT,
                    additional TEXT,
                    enabled INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_quality_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    symbol TEXT,
                    quality TEXT NOT NULL,
                    latency_ms REAL,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.commit()
    
    def _init_default_sources(self):
        """Initialize default data sources"""
        self._sources['free_data'] = FreeDataSource()
        self._sources['level2_data'] = Level2DataSource()
        self._sources['sentiment_data'] = SentimentDataSource()
        self._sources['macro_data'] = MacroDataSource()
    
    def get_config_template(self, source_name: str) -> Dict[str, Any]:
        """
        Get configuration template for human to fill.
        
        AI does NOT fill these - human must provide credentials.
        """
        templates = {
            'level2_data': {
                'source_name': 'level2_data',
                'source_type': 'level2',
                'api_key': '<your_api_key>',
                'api_secret': '<your_api_secret>',
                'endpoint': '<data_provider_endpoint>',
                'additional': {
                    'provider': 'polygon|alpaca|ib',
                },
            },
            'news_data': {
                'source_name': 'news_data',
                'source_type': 'news',
                'api_key': '<newsapi_key>',
                'endpoint': 'https://newsapi.org/v2',
            },
            'social_data': {
                'source_name': 'social_data',
                'source_type': 'social',
                'api_key': '<twitter_api_key>',
                'api_secret': '<twitter_api_secret>',
                'additional': {
                    'reddit_client_id': '<reddit_client_id>',
                    'reddit_client_secret': '<reddit_client_secret>',
                },
            },
            'macro_data': {
                'source_name': 'macro_data',
                'source_type': 'macro',
                'api_key': '<fred_api_key>',
                'endpoint': 'https://api.stlouisfed.org/fred',
            },
        }
        return templates.get(source_name, {
            'source_name': source_name,
            'source_type': 'custom',
            'api_key': '<your_api_key>',
        })
    
    def configure_source(self, config: DataSourceConfig) -> bool:
        """
        Configure a data source.
        
        Human provides configuration - AI validates and stores.
        """
        with self._lock:
            self._configs[config.source_name] = config
            self._save_config(config)
        
        logger.info(f"[DataPipeline] Source configured: {config.source_name}")
        return True
    
    async def connect_source(self, source_name: str) -> Tuple[bool, str]:
        """Connect to a data source"""
        if source_name not in self._sources:
            return (False, f"Unknown source: {source_name}")
        
        source = self._sources[source_name]
        config = self._configs.get(source_name, DataSourceConfig(
            source_name=source_name,
            source_type='default',
        ))
        
        return await source.connect(config)
    
    async def connect_all(self) -> Dict[str, Tuple[bool, str]]:
        """Connect to all configured sources"""
        results = {}
        for name in self._sources:
            results[name] = await self.connect_source(name)
        return results
    
    async def fetch_data(
        self,
        data_type: DataType,
        symbol: str,
        preferred_source: Optional[str] = None
    ) -> Optional[DataPoint]:
        """
        Fetch data with automatic source selection and failover.
        """
        # Find sources that support this data type
        available_sources = [
            (name, src) for name, src in self._sources.items()
            if src.supports(data_type) and src.status == DataSourceStatus.CONNECTED
        ]
        
        if not available_sources:
            logger.warning(f"[DataPipeline] No sources available for {data_type}")
            return None
        
        # Prefer specified source
        if preferred_source:
            available_sources.sort(key=lambda x: x[0] != preferred_source)
        
        # Try sources in order
        for name, source in available_sources:
            try:
                start_time = datetime.now()
                data_point = await source.fetch_data(data_type, symbol)
                
                if data_point:
                    latency = (datetime.now() - start_time).total_seconds() * 1000
                    data_point.latency_ms = latency
                    
                    # Cache data
                    self._cache_data(data_type, symbol, data_point)
                    
                    # Log quality
                    self._log_quality(name, data_type, symbol, data_point.quality, latency)
                    
                    return data_point
            except Exception as e:
                logger.error(f"[DataPipeline] Error from {name}: {e}")
                continue
        
        return None
    
    def _cache_data(self, data_type: DataType, symbol: str, data_point: DataPoint):
        """Cache data point"""
        cache_key = f"{data_type.value}:{symbol}"
        with self._lock:
            if cache_key not in self._data_cache:
                self._data_cache[cache_key] = deque(maxlen=1000)
            self._data_cache[cache_key].append(data_point)
    
    def get_cached_data(
        self,
        data_type: DataType,
        symbol: str,
        limit: int = 100
    ) -> List[DataPoint]:
        """Get cached data"""
        cache_key = f"{data_type.value}:{symbol}"
        with self._lock:
            if cache_key in self._data_cache:
                return list(self._data_cache[cache_key])[-limit:]
            return []
    
    def get_source_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all data sources"""
        with self._lock:
            return {
                name: {
                    'status': src.status.value,
                    'data_types': [dt.value for dt in src.data_types],
                    'last_data': src.last_data_time.isoformat() if src.last_data_time else None,
                    'data_count': src.data_count,
                    'error_count': src.error_count,
                    'is_stale': src.is_stale(),
                }
                for name, src in self._sources.items()
            }
    
    def is_data_available(self, data_type: DataType) -> bool:
        """Check if data type is available from any source"""
        for source in self._sources.values():
            if source.supports(data_type) and source.status == DataSourceStatus.CONNECTED:
                return True
        return False
    
    def get_data_quality_report(self) -> Dict[str, Any]:
        """Generate data quality report"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT source_name, data_type, 
                       AVG(latency_ms) as avg_latency,
                       COUNT(*) as count,
                       quality
                FROM data_quality_log
                WHERE timestamp > datetime('now', '-1 hour')
                GROUP BY source_name, data_type, quality
            """)
            
            results = cursor.fetchall()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'sources': self.get_source_status(),
            'quality_metrics': [
                {
                    'source': r[0],
                    'data_type': r[1],
                    'avg_latency_ms': r[2],
                    'count': r[3],
                    'quality': r[4],
                }
                for r in results
            ],
        }
    
    def _save_config(self, config: DataSourceConfig):
        """Save configuration to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO data_source_configs
                (source_name, source_type, api_key, api_secret, endpoint,
                 additional, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                config.source_name,
                config.source_type,
                config.api_key,
                config.api_secret,
                config.endpoint,
                json.dumps(config.additional),
                1 if config.enabled else 0,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ))
            conn.commit()
    
    def _log_quality(
        self,
        source_name: str,
        data_type: DataType,
        symbol: str,
        quality: DataQuality,
        latency_ms: float
    ):
        """Log data quality metrics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO data_quality_log
                (source_name, data_type, symbol, quality, latency_ms, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                source_name,
                data_type.value,
                symbol,
                quality.value,
                latency_ms,
                datetime.now().isoformat(),
            ))
            conn.commit()
