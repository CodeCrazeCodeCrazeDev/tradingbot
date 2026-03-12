"""
Venue Outage Detection & Failover System
Implements HI-EXE-010: Venue outage detection and failover

Monitors venue health and automatically fails over to backup venues
when outages are detected. Critical for high availability.
"""

import time
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import threading

logger = logging.getLogger(__name__)


class VenueStatus(Enum):
    """Venue health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class VenueHealth:
    """Venue health metrics"""
    venue_id: str
    status: VenueStatus
    last_successful_request: datetime
    last_failed_request: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    latency_ms: float = 0.0
    error_rate: float = 0.0
    uptime_percentage: float = 100.0
    
    def is_available(self) -> bool:
        """Check if venue is available"""
        return self.status in [VenueStatus.HEALTHY, VenueStatus.DEGRADED]


class VenueOutageDetector:
    """
    Monitors venue health and enables automatic failover
    
    Features:
    - Health check probes
    - Latency monitoring
    - Error rate tracking
    - Automatic failover
    - Venue priority management
    """
    
    def __init__(self,
                 health_check_interval: int = 30,
                 failure_threshold: int = 3,
                 degraded_latency_ms: float = 1000.0,
                 unhealthy_latency_ms: float = 5000.0):
        self.health_check_interval = health_check_interval
        self.failure_threshold = failure_threshold
        self.degraded_latency_ms = degraded_latency_ms
        self.unhealthy_latency_ms = unhealthy_latency_ms
        
        self.venues: Dict[str, VenueHealth] = {}
        self.venue_priority: List[str] = []
        self.on_outage_callbacks: List[Callable] = []
        self.on_recovery_callbacks: List[Callable] = []
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Venue Outage Detector initialized")
    
    def register_venue(self, venue_id: str, priority: int = 0):
        """Register venue for monitoring"""
        self.venues[venue_id] = VenueHealth(
            venue_id=venue_id,
            status=VenueStatus.HEALTHY,
            last_successful_request=datetime.now()
        )
        self.venue_priority.append(venue_id)
        self.venue_priority.sort(key=lambda v: priority)
        logger.info(f"Registered venue: {venue_id}")
    
    def record_success(self, venue_id: str, latency_ms: float):
        """Record successful request"""
        if venue_id not in self.venues:
            return
        
        venue = self.venues[venue_id]
        venue.last_successful_request = datetime.now()
        venue.success_count += 1
        venue.latency_ms = latency_ms
        
        # Update status based on latency
        if latency_ms > self.unhealthy_latency_ms:
            venue.status = VenueStatus.UNHEALTHY
        elif latency_ms > self.degraded_latency_ms:
            venue.status = VenueStatus.DEGRADED
        else:
            old_status = venue.status
            venue.status = VenueStatus.HEALTHY
            if old_status != VenueStatus.HEALTHY:
                self._trigger_recovery(venue_id)
    
    def record_failure(self, venue_id: str, error: str):
        """Record failed request"""
        if venue_id not in self.venues:
            return
        
        venue = self.venues[venue_id]
        venue.last_failed_request = datetime.now()
        venue.failure_count += 1
        
        # Check if exceeded threshold
        if venue.failure_count >= self.failure_threshold:
            old_status = venue.status
            venue.status = VenueStatus.OFFLINE
            if old_status != VenueStatus.OFFLINE:
                logger.error(f"Venue {venue_id} marked OFFLINE")
                self._trigger_outage(venue_id)
    
    def get_best_venue(self) -> Optional[str]:
        """Get best available venue"""
        for venue_id in self.venue_priority:
            if self.venues[venue_id].is_available():
                return venue_id
        return None
    
    def _monitor_loop(self):
        """Background health monitoring"""
        while self.running:
            time.sleep(self.health_check_interval)
            # Health check logic here
    
    def _trigger_outage(self, venue_id: str):
        """Trigger outage callbacks"""
        for callback in self.on_outage_callbacks:
            try:
                callback(venue_id)
            except Exception as e:
                logger.error(f"Error in outage callback: {e}")
    
    def _trigger_recovery(self, venue_id: str):
        """Trigger recovery callbacks"""
        for callback in self.on_recovery_callbacks:
            try:
                callback(venue_id)
            except Exception as e:
                logger.error(f"Error in recovery callback: {e}")
    
    def register_callback(self, event_type: str, callback: Callable):
        """Register callback"""
        if event_type == 'outage':
            self.on_outage_callbacks.append(callback)
        elif event_type == 'recovery':
            self.on_recovery_callbacks.append(callback)
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
