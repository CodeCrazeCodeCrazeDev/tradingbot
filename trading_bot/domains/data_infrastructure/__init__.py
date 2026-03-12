"""
Domain 5: Data Infrastructure
==============================

Data collection, storage, processing, and distribution.

Mapped Modules:
- data, database, ingestion, data_feeds, data_sources, persistence
- schemas, event_pipeline, event_monitoring, streaming
- connectivity, connectivity_unified, connectors, bridges, infrastructure
- core, core_api, system, system_supervisor, system_health, config
- log_system, logs, backups, telemetry, monitoring, observability
- metrics, alerts, notifications
"""

from ..base import BaseDomain, DomainPriority, DomainStatus
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class DataInfrastructureDomain(BaseDomain):
    """
    Data Infrastructure Domain - Data engineering and feeds.
    
    This domain is responsible for:
    - Real-time data feeds
    - Data lake architecture
    - ETL pipelines
    - Quality control
    - Historical data management
    """
    
    MODULE_MAPPINGS = {
        # Core Data
        'data': 'trading_bot.data',
        'database': 'trading_bot.database',
        'ingestion': 'trading_bot.ingestion',
        'data_feeds': 'trading_bot.data_feeds',
        'data_sources': 'trading_bot.data_sources',
        'persistence': 'trading_bot.persistence',
        
        # Schemas & Events
        'schemas': 'trading_bot.schemas',
        'event_pipeline': 'trading_bot.event_pipeline',
        'event_monitoring': 'trading_bot.event_monitoring',
        'streaming': 'trading_bot.streaming',
        
        # Connectivity
        'connectivity': 'trading_bot.connectivity',
        'connectivity_unified': 'trading_bot.connectivity_unified',
        'connectors': 'trading_bot.connectors',
        'bridges': 'trading_bot.bridges',
        'infrastructure': 'trading_bot.infrastructure',
        
        # Core Systems
        'core': 'trading_bot.core',
        'core_api': 'trading_bot.core_api',
        'system': 'trading_bot.system',
        'system_supervisor': 'trading_bot.system_supervisor',
        'system_health': 'trading_bot.system_health',
        'config': 'trading_bot.config',
        
        # Monitoring
        'log_system': 'trading_bot.log_system',
        'telemetry': 'trading_bot.telemetry',
        'monitoring': 'trading_bot.monitoring',
        'observability': 'trading_bot.observability',
        'alerts': 'trading_bot.alerts',
        'notifications': 'trading_bot.notifications',
    }
    
    def __init__(self):
        super().__init__(
            domain_id="data_infrastructure",
            domain_name="Data Infrastructure",
            priority=DomainPriority.CRITICAL
        )
        self._data_sources = {}
        self._pipelines = {}
    
    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing Data Infrastructure domain...")
            await self._load_data_systems()
            await self._load_monitoring_systems()
            self.logger.info(f"Data Infrastructure initialized with {len(self._modules)} modules")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Data Infrastructure: {e}")
            return False
    
    async def shutdown(self) -> bool:
        self._modules.clear()
        return True
    
    def get_capabilities(self) -> List[str]:
        return [
            "real_time_feeds",
            "historical_data",
            "data_storage",
            "etl_pipelines",
            "data_quality",
            "event_streaming",
            "data_normalization",
            "data_caching",
            "data_replication",
            "monitoring",
        ]
    
    def get_module_mapping(self) -> Dict[str, str]:
        return self.MODULE_MAPPINGS.copy()
    
    async def _load_data_systems(self):
        try:
            from trading_bot import database
            self.register_module('database', database)
        except ImportError:
            pass
        try:
            from trading_bot import ingestion
            self.register_module('ingestion', ingestion)
        except ImportError:
            pass
    
    async def _load_monitoring_systems(self):
        try:
            from trading_bot import monitoring
            self.register_module('monitoring', monitoring)
        except ImportError:
            pass
    
    async def get_market_data(self, symbol: str, timeframe: str = "1H") -> Dict[str, Any]:
        """Get market data for a symbol."""
        return {'symbol': symbol, 'timeframe': timeframe, 'data': []}
    
    async def subscribe(self, symbol: str, callback: callable) -> str:
        """Subscribe to real-time data."""
        return f"sub_{symbol}"


__all__ = ['DataInfrastructureDomain']
