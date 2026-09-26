"""
AlphaAlgo Ingestion Orchestrator
================================
Master coordinator for the entire ingestion pipeline.
Manages collectors, normalizers, routers, storage, and monitoring.
"""

from __future__ import annotations

import asyncio
import logging
import time
import signal
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json

from .schema import MarketEvent, MarketEventType, EventEnvelope
from .collector import (
    CollectorConfig, CollectorManager, WebSocketCollector,
    create_collector_config
)
from .normalizer import EventNormalizer, NormalizerConfig
from .event_router import EventRouter, RouterConfig, TOPIC_CONFIGS
from .orderbook_builder import OrderBookManager, OrderBookConfig
from .storage import StorageManager, StorageConfig

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorConfig:
    """Configuration for ingestion orchestrator"""
    # Component configs
    normalizer_config: NormalizerConfig = field(default_factory=NormalizerConfig)
    router_config: RouterConfig = field(default_factory=RouterConfig)
    orderbook_config: OrderBookConfig = field(default_factory=OrderBookConfig)
    storage_config: StorageConfig = field(default_factory=StorageConfig)
    
    # Pipeline settings
    enable_storage: bool = True
    enable_orderbook: bool = True
    enable_routing: bool = True
    
    # Monitoring
    metrics_interval_seconds: float = 10.0
    health_check_interval_seconds: float = 30.0
    
    # Error handling
    max_consecutive_errors: int = 100
    error_cooldown_seconds: float = 5.0
    
    # Shutdown
    graceful_shutdown_timeout: float = 30.0


class PipelineMetrics:
    """Metrics for the ingestion pipeline"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.events_received: int = 0
        self.events_normalized: int = 0
        self.events_routed: int = 0
        self.events_stored: int = 0
        self.events_dropped: int = 0
        self.bytes_received: int = 0
        self.errors: int = 0
        self.latency_sum_us: float = 0.0
        self.latency_count: int = 0
        self.start_time: float = time.time()
    
    def record_event(self, latency_us: float):
        self.events_received += 1
        self.latency_sum_us += latency_us
        self.latency_count += 1
    
    @property
    def avg_latency_us(self) -> float:
        if self.latency_count == 0:
            return 0.0
        return self.latency_sum_us / self.latency_count
    
    @property
    def events_per_second(self) -> float:
        elapsed = time.time() - self.start_time
        if elapsed <= 0:
            return 0.0
        return self.events_received / elapsed
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'events_received': self.events_received,
            'events_normalized': self.events_normalized,
            'events_routed': self.events_routed,
            'events_stored': self.events_stored,
            'events_dropped': self.events_dropped,
            'bytes_received': self.bytes_received,
            'errors': self.errors,
            'avg_latency_us': self.avg_latency_us,
            'events_per_second': self.events_per_second,
            'uptime_seconds': time.time() - self.start_time,
        }


class IngestionOrchestrator:
    """
    Master orchestrator for the AlphaAlgo ingestion pipeline.
    
    Pipeline flow:
    1. Collectors receive raw data from exchanges
    2. Normalizer transforms to unified schema
    3. Order book builder maintains book state
    4. Event router sends to Kafka/Redpanda
    5. Storage writes to ClickHouse/S3
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        
        # Components
        self.collector_manager = CollectorManager()
        self.normalizer = EventNormalizer(self.config.normalizer_config)
        self.router: Optional[EventRouter] = None
        self.orderbook_manager: Optional[OrderBookManager] = None
        self.storage_manager: Optional[StorageManager] = None
        
        # State
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._tasks: List[asyncio.Task] = []
        
        # Metrics
        self.metrics = PipelineMetrics()
        
        # Error tracking
        self._consecutive_errors = 0
        
        # Callbacks
        self._on_event_callbacks: List[Callable[[MarketEvent], None]] = []
        
        logger.info("IngestionOrchestrator initialized")
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing ingestion pipeline...")
        
        # Initialize router
        if self.config.enable_routing:
            self.router = EventRouter(self.config.router_config)
            await self.router.initialize()
            logger.info("Event router initialized")
        
        # Initialize order book manager
        if self.config.enable_orderbook:
            self.orderbook_manager = OrderBookManager(self.config.orderbook_config)
            await self.orderbook_manager.start()
            logger.info("Order book manager initialized")
        
        # Initialize storage
        if self.config.enable_storage:
            self.storage_manager = StorageManager(self.config.storage_config)
            await self.storage_manager.initialize()
            logger.info("Storage manager initialized")
        
        # Sync NTP
        await self.normalizer.timestamp_aligner.sync_clock()
        
        logger.info("Ingestion pipeline initialized")
    
    def add_collector(
        self,
        exchange: str,
        symbols: List[str],
        api_key: str = '',
        api_secret: str = '',
    ):
        """Add a collector for an exchange"""
        config = create_collector_config(
            exchange=exchange,
            symbols=symbols,
            api_key=api_key,
            api_secret=api_secret,
        )
        
        self.collector_manager.add_collector(
            config=config,
            message_handler=self._handle_raw_message,
        )
        
        logger.info(f"Added collector for {exchange} with {len(symbols)} symbols")
    
    def add_custom_collector(
        self,
        config: CollectorConfig,
    ):
        """Add a custom collector configuration"""
        self.collector_manager.add_collector(
            config=config,
            message_handler=self._handle_raw_message,
        )
    
    async def start(self):
        """Start the ingestion pipeline"""
        if self._running:
            logger.warning("Pipeline already running")
            return
        
        self._running = True
        self._shutdown_event.clear()
        self.metrics.reset()
        
        logger.info("Starting ingestion pipeline...")
        
        # Start collectors
        await self.collector_manager.start_all()
        
        # Start metrics reporter
        self._tasks.append(
            asyncio.create_task(self._metrics_reporter())
        )
        
        # Start health checker
        self._tasks.append(
            asyncio.create_task(self._health_checker())
        )
        
        logger.info("Ingestion pipeline started")
    
    async def stop(self):
        """Stop the ingestion pipeline gracefully"""
        if not self._running:
            return
        
        logger.info("Stopping ingestion pipeline...")
        self._running = False
        self._shutdown_event.set()
        
        # Stop collectors
        await self.collector_manager.stop_all()
        
        # Cancel tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks with timeout
        if self._tasks:
            await asyncio.wait(
                self._tasks,
                timeout=self.config.graceful_shutdown_timeout
            )
        
        self._tasks.clear()
        
        # Flush router
        if self.router:
            await self.router.close()
        
        # Flush storage
        if self.storage_manager:
            await self.storage_manager.close()
        
        # Stop order book manager
        if self.orderbook_manager:
            await self.orderbook_manager.stop()
        
        logger.info("Ingestion pipeline stopped")
    
    async def _handle_raw_message(self, raw_message: bytes, receive_ts: int):
        """
        Handle raw message from collector.
        This is the main pipeline entry point.
        """
        try:
            self.metrics.bytes_received += len(raw_message)
            
            # Determine exchange from collector (simplified - would need proper routing)
            exchange = 'unknown'
            
            # Normalize
            event = await self.normalizer.normalize(raw_message, receive_ts, exchange)
            
            if event is None:
                self.metrics.events_dropped += 1
                return
            
            self.metrics.events_normalized += 1
            
            # Calculate latency
            latency_us = (event.process_ts - event.exchange_ts) / 1000
            self.metrics.record_event(latency_us)
            
            # Process through pipeline
            await self._process_event(event)
            
            # Reset error counter on success
            self._consecutive_errors = 0
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            self.metrics.errors += 1
            self._consecutive_errors += 1
            
            if self._consecutive_errors >= self.config.max_consecutive_errors:
                logger.critical(f"Too many consecutive errors ({self._consecutive_errors}), cooling down")
                await asyncio.sleep(self.config.error_cooldown_seconds)
                self._consecutive_errors = 0
    
    async def _process_event(self, event: MarketEvent):
        """Process a normalized event through the pipeline"""
        
        # Update order book
        if self.orderbook_manager:
            self.orderbook_manager.process_event(event)
        
        # Route to Kafka
        if self.router:
            await self.router.route(event)
            self.metrics.events_routed += 1
        
        # Store
        if self.storage_manager:
            await self.storage_manager.write([event])
            self.metrics.events_stored += 1
        
        # Call registered callbacks
        for callback in self._on_event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")
    
    def on_event(self, callback: Callable[[MarketEvent], None]):
        """Register callback for processed events"""
        self._on_event_callbacks.append(callback)
    
    async def _metrics_reporter(self):
        """Periodic metrics reporting"""
        while self._running:
            await asyncio.sleep(self.config.metrics_interval_seconds)
            
            metrics = self.get_metrics()
            logger.info(
                f"Pipeline metrics: "
                f"events={metrics['events_received']}, "
                f"eps={metrics['events_per_second']:.1f}, "
                f"latency={metrics['avg_latency_us']:.1f}us, "
                f"errors={metrics['errors']}"
            )
    
    async def _health_checker(self):
        """Periodic health check"""
        while self._running:
            await asyncio.sleep(self.config.health_check_interval_seconds)
            
            health = self.get_health()
            
            if not health['healthy']:
                logger.warning(f"Pipeline unhealthy: {health}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get pipeline metrics"""
        metrics = self.metrics.to_dict()
        
        # Add component metrics
        metrics['collectors'] = self.collector_manager.get_all_stats()
        metrics['normalizer'] = self.normalizer.get_stats()
        
        if self.router:
            metrics['router'] = self.router.get_stats()
        
        if self.orderbook_manager:
            metrics['orderbook'] = self.orderbook_manager.get_stats()
        
        if self.storage_manager:
            metrics['storage'] = asyncio.create_task(
                self.storage_manager.get_stats()
            )
        
        return metrics
    
    def get_health(self) -> Dict[str, Any]:
        """Get pipeline health status"""
        collector_health = self.collector_manager.get_health()
        
        healthy = (
            collector_health['health_ratio'] >= 0.5 and
            self._consecutive_errors < self.config.max_consecutive_errors
        )
        
        return {
            'healthy': healthy,
            'running': self._running,
            'collectors': collector_health,
            'consecutive_errors': self._consecutive_errors,
            'uptime_seconds': time.time() - self.metrics.start_time,
        }
    
    def get_orderbook(self, exchange: str, symbol: str):
        """Get current order book state"""
        if self.orderbook_manager:
            return self.orderbook_manager.get_state(exchange, symbol)
        return None


async def create_pipeline(
    exchanges: Dict[str, List[str]],  # exchange -> symbols
    kafka_servers: List[str] = None,
    clickhouse_host: str = 'localhost',
    s3_bucket: str = '',
) -> IngestionOrchestrator:
    """
    Factory function to create a complete ingestion pipeline.
    
    Args:
        exchanges: Dict mapping exchange names to list of symbols
        kafka_servers: Kafka/Redpanda bootstrap servers
        clickhouse_host: ClickHouse host
        s3_bucket: S3 bucket for archival
    
    Returns:
        Configured IngestionOrchestrator
    """
    # Build config
    config = OrchestratorConfig()
    
    if kafka_servers:
        config.router_config.bootstrap_servers = kafka_servers
    
    config.storage_config.clickhouse_host = clickhouse_host
    
    if s3_bucket:
        config.storage_config.s3_bucket = s3_bucket
    else:
        config.enable_storage = False
    
    # Create orchestrator
    orchestrator = IngestionOrchestrator(config)
    
    # Add collectors
    for exchange, symbols in exchanges.items():
        orchestrator.add_collector(exchange, symbols)
    
    # Initialize
    await orchestrator.initialize()
    
    return orchestrator


# Signal handlers for graceful shutdown
def setup_signal_handlers(orchestrator: IngestionOrchestrator):
    """Setup signal handlers for graceful shutdown"""
    
    def handle_signal(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(orchestrator.stop())
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)


# Main entry point
async def main():
    """Example main entry point"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create pipeline
    pipeline = await create_pipeline(
        exchanges={
            'binance': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
            'coinbase': ['BTC-USD', 'ETH-USD'],
        },
        kafka_servers=['localhost:9092'],
        clickhouse_host='localhost',
    )
    
    # Setup signal handlers
    setup_signal_handlers(pipeline)
    
    # Start pipeline
    await pipeline.start()
    
    try:
        # Run until shutdown
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await pipeline.stop()


if __name__ == '__main__':
    asyncio.run(main())
