"""
Data Staleness Detection & Auto-Pause System
Implements HI-DAT-002: Staleness Detection + Pause

Monitors data freshness and automatically pauses trading when data becomes stale.
Critical for preventing trading on outdated information.
"""

import time
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import threading
from collections import deque
from enum import auto

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Types of data sources to monitor"""
    MARKET_DATA = "market_data"
    ORDER_BOOK = "order_book"
    TRADES = "trades"
    NEWS = "news"
    ECONOMIC_DATA = "economic_data"
    BROKER_CONNECTION = "broker_connection"


class FreshnessStatus(Enum):
    """Data freshness status"""
    FRESH = "fresh"
    DEGRADED = "degraded"
    STALE = "stale"
    CRITICAL = "critical"


@dataclass
class DataFreshness:
    """Tracks freshness of a data source"""
    source: DataSource
    last_update: datetime
    update_count: int = 0
    expected_update_interval: float = 1.0  # seconds
    staleness_threshold: float = 5.0  # seconds
    critical_threshold: float = 30.0  # seconds
    
    def get_age_seconds(self) -> float:
        """Get age of last update in seconds"""
        return (datetime.now() - self.last_update).total_seconds()
    
    def get_status(self) -> FreshnessStatus:
        """Get current freshness status"""
        age = self.get_age_seconds()
        
        if age > self.critical_threshold:
            return FreshnessStatus.CRITICAL
        elif age > self.staleness_threshold:
            return FreshnessStatus.STALE
        elif age > self.expected_update_interval * 2:
            return FreshnessStatus.DEGRADED
        else:
            return FreshnessStatus.FRESH
    
    def is_stale(self) -> bool:
        """Check if data is stale"""
        return self.get_status() in [FreshnessStatus.STALE, FreshnessStatus.CRITICAL]
    
    def update(self):
        """Mark data as updated"""
        self.last_update = datetime.now()
        self.update_count += 1


@dataclass
class StalenessEvent:
    """Event triggered when data becomes stale"""
    source: DataSource
    status: FreshnessStatus
    age_seconds: float
    threshold_seconds: float
    timestamp: datetime = field(default_factory=datetime.now)
    action_taken: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source.value,
            'status': self.status.value,
            'age_seconds': self.age_seconds,
            'threshold_seconds': self.threshold_seconds,
            'timestamp': self.timestamp.isoformat(),
            'action_taken': self.action_taken,
            'metadata': self.metadata
        }


class StalenessDetector:
    """
    Monitors data freshness and triggers alerts/actions when data becomes stale
    
    Features:
    - Multi-source monitoring
    - Configurable thresholds per source
    - Automatic trading pause on stale data
    - Event callbacks for custom actions
    - Freshness statistics and reporting
    """
    
    def __init__(self,
                 auto_pause_trading: bool = True,
                 check_interval_seconds: float = 1.0,
                 enable_monitoring: bool = True):
        """
        Initialize staleness detector
        
        Args:
            auto_pause_trading: Automatically pause trading on stale data
            check_interval_seconds: How often to check freshness
            enable_monitoring: Enable background monitoring thread
        """
        self.auto_pause_trading = auto_pause_trading
        self.check_interval = check_interval_seconds
        self.enable_monitoring = enable_monitoring
        
        # Data source tracking
        self.data_sources: Dict[DataSource, DataFreshness] = {}
        self.staleness_events: deque = deque(maxlen=1000)
        
        # Trading state
        self.trading_paused = False
        self.pause_reason: Optional[str] = None
        self.pause_timestamp: Optional[datetime] = None
        
        # Callbacks
        self.on_stale_callbacks: List[Callable] = []
        self.on_fresh_callbacks: List[Callable] = []
        self.on_pause_callbacks: List[Callable] = []
        self.on_resume_callbacks: List[Callable] = []
        
        # Statistics
        self.stats = {
            'total_checks': 0,
            'stale_detections': 0,
            'critical_detections': 0,
            'auto_pauses': 0,
            'auto_resumes': 0
        }
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Monitoring thread
        self.monitoring_thread = None
        if self.enable_monitoring:
            self._start_monitoring()
        
        logger.info(f"Staleness Detector initialized (auto_pause: {auto_pause_trading})")
    
    def register_data_source(self,
                            source: DataSource,
                            expected_update_interval: float = 1.0,
                            staleness_threshold: float = 5.0,
                            critical_threshold: float = 30.0):
        """
        Register a data source for monitoring
        
        Args:
            source: Data source type
            expected_update_interval: Expected time between updates (seconds)
            staleness_threshold: When to consider data stale (seconds)
            critical_threshold: When to consider data critically stale (seconds)
        """
        with self.lock:
            self.data_sources[source] = DataFreshness(
                source=source,
                last_update=datetime.now(),
                expected_update_interval=expected_update_interval,
                staleness_threshold=staleness_threshold,
                critical_threshold=critical_threshold
            )
            logger.info(f"Registered data source: {source.value} "
                       f"(interval: {expected_update_interval}s, threshold: {staleness_threshold}s)")
    
    def update_data_source(self, source: DataSource):
        """
        Mark data source as updated (call this when new data arrives)
        
        Args:
            source: Data source that was updated
        """
        with self.lock:
            if source not in self.data_sources:
                logger.warning(f"Data source {source.value} not registered, auto-registering")
                self.register_data_source(source)
            
            freshness = self.data_sources[source]
            was_stale = freshness.is_stale()
            
            freshness.update()
            
            # If was stale and now fresh, trigger callbacks
            if was_stale and not freshness.is_stale():
                self._trigger_fresh_callbacks(source)
                
                # Auto-resume if all sources fresh
                if self.trading_paused and self._all_sources_fresh():
                    self._resume_trading(f"All data sources fresh")
    
    def check_freshness(self) -> Dict[DataSource, FreshnessStatus]:
        """
        Check freshness of all data sources
        
        Returns:
            Dictionary mapping sources to their freshness status
        """
        with self.lock:
            self.stats['total_checks'] += 1
            
            freshness_map = {}
            stale_sources = []
            critical_sources = []
            
            for source, freshness in self.data_sources.items():
                status = freshness.get_status()
                freshness_map[source] = status
                
                if status == FreshnessStatus.STALE:
                    stale_sources.append(source)
                    self.stats['stale_detections'] += 1
                elif status == FreshnessStatus.CRITICAL:
                    critical_sources.append(source)
                    self.stats['critical_detections'] += 1
            
            # Handle stale data
            if stale_sources or critical_sources:
                self._handle_stale_data(stale_sources, critical_sources)
            
            return freshness_map
    
    def _handle_stale_data(self, 
                          stale_sources: List[DataSource],
                          critical_sources: List[DataSource]):
        """Handle detection of stale data"""
        # Create events
        for source in stale_sources:
            freshness = self.data_sources[source]
            event = StalenessEvent(
                source=source,
                status=FreshnessStatus.STALE,
                age_seconds=freshness.get_age_seconds(),
                threshold_seconds=freshness.staleness_threshold
            )
            self.staleness_events.append(event)
            self._trigger_stale_callbacks(source, event)
        
        for source in critical_sources:
            freshness = self.data_sources[source]
            event = StalenessEvent(
                source=source,
                status=FreshnessStatus.CRITICAL,
                age_seconds=freshness.get_age_seconds(),
                threshold_seconds=freshness.critical_threshold
            )
            self.staleness_events.append(event)
            self._trigger_stale_callbacks(source, event)
        
        # Auto-pause if enabled and not already paused
        if self.auto_pause_trading and not self.trading_paused:
            if critical_sources:
                reason = f"Critical stale data: {[s.value for s in critical_sources]}"
                self._pause_trading(reason)
            elif len(stale_sources) >= 2:  # Multiple stale sources
                reason = f"Multiple stale sources: {[s.value for s in stale_sources]}"
                self._pause_trading(reason)
    
    def _pause_trading(self, reason: str):
        """Pause trading due to stale data"""
        with self.lock:
            if self.trading_paused:
                return
            
            self.trading_paused = True
            self.pause_reason = reason
            self.pause_timestamp = datetime.now()
            self.stats['auto_pauses'] += 1
            
            logger.critical(f"TRADING PAUSED: {reason}")
            
            # Trigger callbacks
            for callback in self.on_pause_callbacks:
                try:
                    callback(reason)
                except Exception as e:
                    logger.error(f"Error in pause callback: {e}")
    
    def _resume_trading(self, reason: str):
        """Resume trading after data becomes fresh"""
        with self.lock:
            if not self.trading_paused:
                return
            
            pause_duration = (datetime.now() - self.pause_timestamp).total_seconds()
            
            self.trading_paused = False
            self.pause_reason = None
            self.pause_timestamp = None
            self.stats['auto_resumes'] += 1
            
            logger.info(f"TRADING RESUMED: {reason} (paused for {pause_duration:.1f}s)")
            
            # Trigger callbacks
            for callback in self.on_resume_callbacks:
                try:
                    callback(reason, pause_duration)
                except Exception as e:
                    logger.error(f"Error in resume callback: {e}")
    
    def _all_sources_fresh(self) -> bool:
        """Check if all data sources are fresh"""
        with self.lock:
            for freshness in self.data_sources.values():
                if freshness.is_stale():
                    return False
            return True
    
    def _trigger_stale_callbacks(self, source: DataSource, event: StalenessEvent):
        """Trigger callbacks for stale data"""
        for callback in self.on_stale_callbacks:
            try:
                callback(source, event)
            except Exception as e:
                logger.error(f"Error in stale callback: {e}")
    
    def _trigger_fresh_callbacks(self, source: DataSource):
        """Trigger callbacks for fresh data"""
        for callback in self.on_fresh_callbacks:
            try:
                callback(source)
            except Exception as e:
                logger.error(f"Error in fresh callback: {e}")
    
    def register_callback(self,
                         event_type: str,
                         callback: Callable):
        """
        Register callback for events
        
        Args:
            event_type: 'stale', 'fresh', 'pause', or 'resume'
            callback: Function to call
        """
        if event_type == 'stale':
            self.on_stale_callbacks.append(callback)
        elif event_type == 'fresh':
            self.on_fresh_callbacks.append(callback)
        elif event_type == 'pause':
            self.on_pause_callbacks.append(callback)
        elif event_type == 'resume':
            self.on_resume_callbacks.append(callback)
        else:
            raise ValueError(f"Unknown event type: {event_type}")
        
        logger.info(f"Registered {event_type} callback")
    
    def _start_monitoring(self):
        """Start background monitoring thread"""
        def monitor_loop():
            while self.enable_monitoring:
                try:
                    self.check_freshness()
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                
                time.sleep(self.check_interval)
        
        self.monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Staleness monitoring thread started")
    
    def stop_monitoring(self):
        """Stop monitoring thread"""
        self.enable_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Staleness monitoring stopped")
    
    def is_trading_paused(self) -> bool:
        """Check if trading is currently paused"""
        with self.lock:
            return self.trading_paused
    
    def get_pause_info(self) -> Optional[Dict[str, Any]]:
        """Get information about current pause"""
        with self.lock:
            if not self.trading_paused:
                return None
            
            return {
                'paused': True,
                'reason': self.pause_reason,
                'paused_at': self.pause_timestamp.isoformat(),
                'duration_seconds': (datetime.now() - self.pause_timestamp).total_seconds()
            }
    
    def get_freshness_report(self) -> Dict[str, Any]:
        """Get comprehensive freshness report"""
        with self.lock:
            report = {
                'timestamp': datetime.now().isoformat(),
                'trading_paused': self.trading_paused,
                'sources': {}
            }
            
            for source, freshness in self.data_sources.items():
                report['sources'][source.value] = {
                    'status': freshness.get_status().value,
                    'age_seconds': freshness.get_age_seconds(),
                    'update_count': freshness.update_count,
                    'last_update': freshness.last_update.isoformat(),
                    'staleness_threshold': freshness.staleness_threshold
                }
            
            return report
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detector statistics"""
        with self.lock:
            return {
                **self.stats,
                'registered_sources': len(self.data_sources),
                'currently_paused': self.trading_paused,
                'recent_events': len(self.staleness_events)
            }
    
    def force_pause(self, reason: str):
        """Manually pause trading"""
        self._pause_trading(f"Manual pause: {reason}")
    
    def force_resume(self, reason: str):
        """Manually resume trading"""
        self._resume_trading(f"Manual resume: {reason}")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create detector
    detector = StalenessDetector(
        auto_pause_trading=True,
        check_interval_seconds=1.0
    )
    
    # Register callbacks
    def on_stale(source, event):
        logger.info(f"⚠️  STALE: {source.value} - {event.age_seconds:.1f}s old")
    
    def on_pause(reason):
        logger.info(f"🛑 TRADING PAUSED: {reason}")
    
    def on_resume(reason, duration):
        logger.info(f"✅ TRADING RESUMED: {reason} (was paused {duration:.1f}s)")
    
    detector.register_callback('stale', on_stale)
    detector.register_callback('pause', on_pause)
    detector.register_callback('resume', on_resume)
    
    # Register data sources
    detector.register_data_source(
        DataSource.MARKET_DATA,
        expected_update_interval=1.0,
        staleness_threshold=3.0,
        critical_threshold=10.0
    )
    
    detector.register_data_source(
        DataSource.ORDER_BOOK,
        expected_update_interval=0.5,
        staleness_threshold=2.0,
        critical_threshold=5.0
    )
    
    # Simulate data updates
    logger.info("Simulating normal operation...")
    for i in range(5):
        time.sleep(1)
        detector.update_data_source(DataSource.MARKET_DATA)
        detector.update_data_source(DataSource.ORDER_BOOK)
        logger.info(f"Tick {i+1}: Data updated")
    
    # Simulate stale data
    logger.info("\nSimulating stale data (no updates for 5 seconds)...")
    time.sleep(5)
    
    # Resume updates
    logger.info("\nResuming data updates...")
    for i in range(3):
        time.sleep(1)
        detector.update_data_source(DataSource.MARKET_DATA)
        detector.update_data_source(DataSource.ORDER_BOOK)
        logger.info(f"Tick {i+1}: Data updated")
    
    # Print report
    print("\n" + "="*60)
    logger.info("FRESHNESS REPORT")
    print("="*60)
    report = detector.get_freshness_report()
    for source, info in report['sources'].items():
        logger.info(f"{source}: {info['status']} ({info['age_seconds']:.1f}s old)")
    
    stats = detector.get_statistics()
    logger.info(f"\nStatistics: {stats}")
    
    # Stop monitoring
    detector.stop_monitoring()
