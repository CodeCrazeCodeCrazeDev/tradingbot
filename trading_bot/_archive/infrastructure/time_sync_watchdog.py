"""
Time Sync Watchdog - NTP Drift Monitoring
Implements HI-DAT-003: Time sync/NTP drift watchdog

Monitors system clock drift against NTP servers and alerts on synchronization issues.
Critical for accurate timestamping in trading operations.
"""

import time
import socket
import struct
from datetime import datetime
from typing import Callable, List, Optional
import logging
import threading
from typing import Tuple

logger = logging.getLogger(__name__)


class TimeSyncWatchdog:
    """
    Monitors system time synchronization with NTP servers
    
    Features:
    - NTP time checking
    - Clock drift detection
    - Alert on sync issues
    - Multiple NTP server support
    """
    
    def __init__(self,
                 max_drift_ms: float = 100.0,
                 check_interval_seconds: int = 300,
                 ntp_servers: Optional[List[str]] = None):
        """
        Initialize time sync watchdog
        
        Args:
            max_drift_ms: Maximum acceptable drift in milliseconds
            check_interval_seconds: How often to check sync
            ntp_servers: List of NTP servers to query
        """
        self.max_drift_ms = max_drift_ms
        self.check_interval = check_interval_seconds
        self.ntp_servers = ntp_servers or [
            'pool.ntp.org',
            'time.google.com',
            'time.cloudflare.com'
        ]
        
        self.running = True
        self.drift_detected = False
        self.last_drift_ms = 0.0
        self.last_check = None
        self.on_drift_callbacks: List[Callable] = []
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"Time Sync Watchdog started (max drift: {max_drift_ms}ms)")
    
    def check_time_sync(self) -> tuple[bool, float]:
        """
        Check time synchronization with NTP
        
        Returns:
            Tuple of (is_synced, drift_ms)
        """
        for server in self.ntp_servers:
            try:
                ntp_time = self._get_ntp_time(server)
                if ntp_time:
                    local_time = time.time()
                    drift_ms = abs((ntp_time - local_time) * 1000)
                    self.last_drift_ms = drift_ms
                    self.last_check = datetime.now()
                    
                    if drift_ms > self.max_drift_ms:
                        self.drift_detected = True
                        logger.error(f"Clock drift detected: {drift_ms:.1f}ms (max: {self.max_drift_ms}ms)")
                        self._trigger_drift_callbacks(drift_ms)
                        return False, drift_ms
                    else:
                        self.drift_detected = False
                        logger.debug(f"Time sync OK: drift {drift_ms:.1f}ms")
                        return True, drift_ms
                        
            except Exception as e:
                logger.warning(f"NTP check failed for {server}: {e}")
                continue
        
        logger.error("All NTP servers failed")
        return False, 0.0
    
    def _get_ntp_time(self, server: str, port: int = 123, timeout: int = 5) -> Optional[float]:
        """
        Get time from NTP server
        
        Args:
            server: NTP server hostname
            port: NTP port (default 123)
            timeout: Query timeout in seconds
        
        Returns:
            Unix timestamp or None if failed
        """
        try:
            # NTP packet format
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client.settimeout(timeout)
            
            # NTP request packet (mode 3 = client)
            data = b'\x1b' + 47 * b'\0'
            client.sendto(data, (server, port))
            
            # Receive response
            data, address = client.recvfrom(1024)
            if data:
                # Extract transmit timestamp (bytes 40-43 for seconds, 44-47 for fraction)
                t = struct.unpack('!12I', data)[10]
                # Convert from NTP epoch (1900) to Unix epoch (1970)
                return t - 2208988800
            
        except socket.timeout:
            logger.warning(f"NTP query timeout for {server}")
        except Exception as e:
            logger.error(f"NTP query error for {server}: {e}")
        finally:
            client.close()
        
        return None
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                self.check_time_sync()
            except Exception as e:
                logger.error(f"Error in time sync monitor: {e}")
            
            time.sleep(self.check_interval)
    
    def _trigger_drift_callbacks(self, drift_ms: float):
        """Trigger drift detection callbacks"""
        for callback in self.on_drift_callbacks:
            try:
                callback(drift_ms)
            except Exception as e:
                logger.error(f"Error in drift callback: {e}")
    
    def register_callback(self, callback: Callable):
        """Register callback for drift detection"""
        self.on_drift_callbacks.append(callback)
    
    def get_status(self) -> dict:
        """Get current watchdog status"""
        return {
            'drift_detected': self.drift_detected,
            'last_drift_ms': self.last_drift_ms,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'max_drift_ms': self.max_drift_ms
        }
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Time Sync Watchdog stopped")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    watchdog = TimeSyncWatchdog(max_drift_ms=50.0, check_interval_seconds=10)
    
    def on_drift(drift_ms):
        logger.info(f"⚠️  Clock drift: {drift_ms:.1f}ms")
    
    watchdog.register_callback(on_drift)
    
    # Manual check
    is_synced, drift = watchdog.check_time_sync()
    logger.info(f"Time sync: {is_synced}, drift: {drift:.1f}ms")
    
    time.sleep(15)
    watchdog.stop()
