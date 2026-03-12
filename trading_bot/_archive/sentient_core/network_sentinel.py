"""
Network Sentinel - WiFi/Internet Connectivity Monitor with Auto-Activation

Monitors network connectivity and automatically activates/deactivates
trading systems based on connection status. Supports live and paper trading modes.
"""

import asyncio
import socket
import time
import threading
import subprocess
import platform
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set
from collections import deque
import logging
import json
import os

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Network connection states"""
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED_WEAK = auto()
    CONNECTED_STABLE = auto()
    CONNECTED_STRONG = auto()
    RECONNECTING = auto()


class TradingMode(Enum):
    """Trading mode based on connectivity"""
    OFFLINE = auto()
    PAPER = auto()
    LIVE = auto()
    SIMULATION = auto()


@dataclass
class NetworkMetrics:
    """Network performance metrics"""
    latency_ms: float = 0.0
    packet_loss_pct: float = 0.0
    bandwidth_mbps: float = 0.0
    jitter_ms: float = 0.0
    signal_strength_dbm: int = -100
    connection_uptime_seconds: float = 0.0
    last_check: datetime = field(default_factory=datetime.now)
    
    def is_stable(self) -> bool:
        """Check if connection is stable enough for trading"""
        return (
            self.latency_ms < 200 and
            self.packet_loss_pct < 5.0 and
            self.jitter_ms < 50
        )
    
    def is_strong(self) -> bool:
        """Check if connection is strong enough for live trading"""
        return (
            self.latency_ms < 100 and
            self.packet_loss_pct < 1.0 and
            self.jitter_ms < 20 and
            self.signal_strength_dbm > -70
        )


@dataclass
class ConnectionEvent:
    """Connection state change event"""
    timestamp: datetime
    old_state: ConnectionState
    new_state: ConnectionState
    metrics: NetworkMetrics
    reason: str


class NetworkSentinel:
    """
    Monitors network/WiFi connectivity and auto-activates trading systems.
    
    Features:
    - Real-time WiFi/Internet monitoring
    - Auto-activation of trading systems when connected
    - Graceful degradation to paper trading on weak connection
    - Emergency shutdown on disconnection
    - Connection quality scoring
    - Latency and packet loss tracking
    """
    
    # Test endpoints for connectivity checks
    TEST_ENDPOINTS = [
        ("8.8.8.8", 53),           # Google DNS
        ("1.1.1.1", 53),           # Cloudflare DNS
        ("208.67.222.222", 53),    # OpenDNS
        ("api.binance.com", 443),  # Binance API
        ("api.alpaca.markets", 443),  # Alpaca API
    ]
    
    # Trading endpoints to verify
    TRADING_ENDPOINTS = [
        "api.binance.com",
        "api.alpaca.markets",
        "api.coingecko.com",
        "query1.finance.yahoo.com",
    ]
    
    def __init__(
        self,
        check_interval: float = 5.0,
        stability_threshold: int = 3,
        auto_switch_mode: bool = True,
        preferred_mode: TradingMode = TradingMode.PAPER,
    ):
        self.check_interval = check_interval
        self.stability_threshold = stability_threshold
        self.auto_switch_mode = auto_switch_mode
        self.preferred_mode = preferred_mode
        
        # State
        self.current_state = ConnectionState.DISCONNECTED
        self.current_mode = TradingMode.OFFLINE
        self.metrics = NetworkMetrics()
        self.is_running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # History
        self.connection_history: deque = deque(maxlen=1000)
        self.state_changes: deque = deque(maxlen=100)
        self.stability_counter = 0
        self.last_connected_time: Optional[datetime] = None
        self.total_downtime_seconds = 0.0
        
        # Callbacks
        self._on_connect_callbacks: List[Callable] = []
        self._on_disconnect_callbacks: List[Callable] = []
        self._on_mode_change_callbacks: List[Callable] = []
        self._on_quality_change_callbacks: List[Callable] = []
        
        # Systems to activate/deactivate
        self._registered_systems: Dict[str, Any] = {}
        self._active_systems: Set[str] = set()
        
        logger.info("NetworkSentinel initialized")
    
    def register_system(self, name: str, system: Any) -> None:
        """Register a trading system for auto-activation"""
        self._registered_systems[name] = system
        logger.info(f"Registered system: {name}")
    
    def on_connect(self, callback: Callable) -> None:
        """Register callback for connection events"""
        self._on_connect_callbacks.append(callback)
    
    def on_disconnect(self, callback: Callable) -> None:
        """Register callback for disconnection events"""
        self._on_disconnect_callbacks.append(callback)
    
    def on_mode_change(self, callback: Callable) -> None:
        """Register callback for trading mode changes"""
        self._on_mode_change_callbacks.append(callback)
    
    def on_quality_change(self, callback: Callable) -> None:
        """Register callback for connection quality changes"""
        self._on_quality_change_callbacks.append(callback)
    
    def start(self) -> None:
        """Start the network monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="NetworkSentinel"
        )
        self._monitor_thread.start()
        logger.info("NetworkSentinel started monitoring")
    
    def stop(self) -> None:
        """Stop the network monitoring"""
        self.is_running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=10)
        logger.info("NetworkSentinel stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.is_running:
            try:
                self._check_connectivity()
                self._update_state()
                self._manage_systems()
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
            
            time.sleep(self.check_interval)
    
    def _check_connectivity(self) -> None:
        """Check network connectivity and measure quality"""
        # Check basic internet connectivity
        connected = False
        latencies = []
        
        for host, port in self.TEST_ENDPOINTS:
            try:
                start = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((host, port))
                latency = (time.time() - start) * 1000
                sock.close()
                
                if result == 0:
                    connected = True
                    latencies.append(latency)
            except Exception:
                pass
        
        # Update metrics
        with self._lock:
            if latencies:
                self.metrics.latency_ms = sum(latencies) / len(latencies)
                self.metrics.jitter_ms = max(latencies) - min(latencies) if len(latencies) > 1 else 0
            
            # Check WiFi signal strength (Windows)
            self.metrics.signal_strength_dbm = self._get_wifi_signal_strength()
            
            # Calculate packet loss
            success_rate = len(latencies) / len(self.TEST_ENDPOINTS) * 100
            self.metrics.packet_loss_pct = 100 - success_rate
            
            self.metrics.last_check = datetime.now()
            
            # Update connection uptime
            if connected and self.last_connected_time:
                self.metrics.connection_uptime_seconds = (
                    datetime.now() - self.last_connected_time
                ).total_seconds()
            
            # Record history
            self.connection_history.append({
                'timestamp': datetime.now().isoformat(),
                'connected': connected,
                'latency': self.metrics.latency_ms,
                'packet_loss': self.metrics.packet_loss_pct,
            })
    
    def _get_wifi_signal_strength(self) -> int:
        """Get WiFi signal strength in dBm"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["netsh", "wlan", "show", "interfaces"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'Signal' in line:
                        # Parse signal percentage
                        pct = int(line.split(':')[1].strip().replace('%', ''))
                        # Convert to approximate dBm
                        return int(-100 + (pct * 0.7))
            elif platform.system() == "Linux":
                result = subprocess.run(
                    ["iwconfig"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'Signal level' in line:
                        # Parse dBm value
                        import re
                        match = re.search(r'Signal level[=:](-?\d+)', line)
                        if match:
                            return int(match.group(1))
        except Exception as e:
            logger.debug(f"Could not get WiFi signal: {e}")
        
        return -100  # Default weak signal
    
    def _update_state(self) -> None:
        """Update connection state based on metrics"""
        with self._lock:
            old_state = self.current_state
            
            # Determine new state
            if self.metrics.packet_loss_pct >= 100:
                new_state = ConnectionState.DISCONNECTED
                self.stability_counter = 0
            elif self.metrics.packet_loss_pct > 50:
                new_state = ConnectionState.RECONNECTING
                self.stability_counter = 0
            elif self.metrics.is_strong():
                self.stability_counter += 1
                if self.stability_counter >= self.stability_threshold:
                    new_state = ConnectionState.CONNECTED_STRONG
                else:
                    new_state = ConnectionState.CONNECTING
            elif self.metrics.is_stable():
                self.stability_counter += 1
                if self.stability_counter >= self.stability_threshold:
                    new_state = ConnectionState.CONNECTED_STABLE
                else:
                    new_state = ConnectionState.CONNECTING
            else:
                new_state = ConnectionState.CONNECTED_WEAK
                self.stability_counter = max(0, self.stability_counter - 1)
            
            # Handle state change
            if new_state != old_state:
                self.current_state = new_state
                self._handle_state_change(old_state, new_state)
    
    def _handle_state_change(
        self,
        old_state: ConnectionState,
        new_state: ConnectionState
    ) -> None:
        """Handle connection state changes"""
        event = ConnectionEvent(
            timestamp=datetime.now(),
            old_state=old_state,
            new_state=new_state,
            metrics=NetworkMetrics(**self.metrics.__dict__),
            reason=self._get_state_change_reason(old_state, new_state)
        )
        self.state_changes.append(event)
        
        logger.info(f"Connection state: {old_state.name} -> {new_state.name}")
        
        # Handle connection
        if new_state in [
            ConnectionState.CONNECTED_STABLE,
            ConnectionState.CONNECTED_STRONG
        ]:
            if old_state == ConnectionState.DISCONNECTED:
                self.last_connected_time = datetime.now()
            self._trigger_connect_callbacks(event)
            self._update_trading_mode()
        
        # Handle disconnection
        elif new_state == ConnectionState.DISCONNECTED:
            if self.last_connected_time:
                self.total_downtime_seconds += (
                    datetime.now() - self.last_connected_time
                ).total_seconds()
            self._trigger_disconnect_callbacks(event)
            self._update_trading_mode()
        
        # Handle quality change
        self._trigger_quality_callbacks(event)
    
    def _get_state_change_reason(
        self,
        old_state: ConnectionState,
        new_state: ConnectionState
    ) -> str:
        """Get human-readable reason for state change"""
        if new_state == ConnectionState.DISCONNECTED:
            return "Network connection lost"
        elif new_state == ConnectionState.RECONNECTING:
            return f"High packet loss: {self.metrics.packet_loss_pct:.1f}%"
        elif new_state == ConnectionState.CONNECTED_WEAK:
            return f"Weak signal: {self.metrics.signal_strength_dbm} dBm"
        elif new_state == ConnectionState.CONNECTED_STABLE:
            return "Connection stabilized"
        elif new_state == ConnectionState.CONNECTED_STRONG:
            return "Strong connection established"
        return "State transition"
    
    def _update_trading_mode(self) -> None:
        """Update trading mode based on connection quality"""
        if not self.auto_switch_mode:
            return
        
        old_mode = self.current_mode
        
        if self.current_state == ConnectionState.DISCONNECTED:
            new_mode = TradingMode.OFFLINE
        elif self.current_state == ConnectionState.CONNECTED_STRONG:
            new_mode = self.preferred_mode
        elif self.current_state == ConnectionState.CONNECTED_STABLE:
            # Stable connection - allow paper trading, be cautious with live
            if self.preferred_mode == TradingMode.LIVE:
                new_mode = TradingMode.PAPER  # Downgrade to paper
            else:
                new_mode = self.preferred_mode
        elif self.current_state in [
            ConnectionState.CONNECTED_WEAK,
            ConnectionState.RECONNECTING
        ]:
            new_mode = TradingMode.SIMULATION  # Only simulation on weak connection
        else:
            new_mode = TradingMode.OFFLINE
        
        if new_mode != old_mode:
            self.current_mode = new_mode
            logger.info(f"Trading mode: {old_mode.name} -> {new_mode.name}")
            self._trigger_mode_change_callbacks(old_mode, new_mode)
    
    def _manage_systems(self) -> None:
        """Activate/deactivate registered systems based on state"""
        if self.current_state in [
            ConnectionState.CONNECTED_STABLE,
            ConnectionState.CONNECTED_STRONG
        ]:
            # Activate systems
            for name, system in self._registered_systems.items():
                if name not in self._active_systems:
                    try:
                        if hasattr(system, 'activate'):
                            system.activate(self.current_mode)
                        elif hasattr(system, 'start'):
                            system.start()
                        self._active_systems.add(name)
                        logger.info(f"Activated system: {name}")
                    except Exception as e:
                        logger.error(f"Failed to activate {name}: {e}")
        
        elif self.current_state == ConnectionState.DISCONNECTED:
            # Deactivate all systems
            for name in list(self._active_systems):
                system = self._registered_systems.get(name)
                if system:
                    try:
                        if hasattr(system, 'deactivate'):
                            system.deactivate()
                        elif hasattr(system, 'stop'):
                            system.stop()
                        self._active_systems.discard(name)
                        logger.info(f"Deactivated system: {name}")
                    except Exception as e:
                        logger.error(f"Failed to deactivate {name}: {e}")
    
    def _trigger_connect_callbacks(self, event: ConnectionEvent) -> None:
        """Trigger connection callbacks"""
        for callback in self._on_connect_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Connect callback error: {e}")
    
    def _trigger_disconnect_callbacks(self, event: ConnectionEvent) -> None:
        """Trigger disconnection callbacks"""
        for callback in self._on_disconnect_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Disconnect callback error: {e}")
    
    def _trigger_mode_change_callbacks(
        self,
        old_mode: TradingMode,
        new_mode: TradingMode
    ) -> None:
        """Trigger mode change callbacks"""
        for callback in self._on_mode_change_callbacks:
            try:
                callback(old_mode, new_mode)
            except Exception as e:
                logger.error(f"Mode change callback error: {e}")
    
    def _trigger_quality_callbacks(self, event: ConnectionEvent) -> None:
        """Trigger quality change callbacks"""
        for callback in self._on_quality_change_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Quality callback error: {e}")
    
    def check_trading_endpoints(self) -> Dict[str, bool]:
        """Check connectivity to trading endpoints"""
        results = {}
        for endpoint in self.TRADING_ENDPOINTS:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((endpoint, 443))
                sock.close()
                results[endpoint] = (result == 0)
            except Exception:
                results[endpoint] = False
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get current network status"""
        with self._lock:
            return {
                'state': self.current_state.name,
                'trading_mode': self.current_mode.name,
                'metrics': {
                    'latency_ms': self.metrics.latency_ms,
                    'packet_loss_pct': self.metrics.packet_loss_pct,
                    'signal_strength_dbm': self.metrics.signal_strength_dbm,
                    'jitter_ms': self.metrics.jitter_ms,
                    'uptime_seconds': self.metrics.connection_uptime_seconds,
                },
                'active_systems': list(self._active_systems),
                'stability_counter': self.stability_counter,
                'total_downtime_seconds': self.total_downtime_seconds,
                'last_check': self.metrics.last_check.isoformat(),
            }
    
    def is_ready_for_trading(self) -> bool:
        """Check if network is ready for trading"""
        return self.current_state in [
            ConnectionState.CONNECTED_STABLE,
            ConnectionState.CONNECTED_STRONG
        ]
    
    def is_ready_for_live_trading(self) -> bool:
        """Check if network is ready for live trading"""
        return (
            self.current_state == ConnectionState.CONNECTED_STRONG and
            self.current_mode == TradingMode.LIVE
        )
    
    def get_connection_quality_score(self) -> float:
        """Get connection quality score (0-100)"""
        with self._lock:
            score = 100.0
            
            # Latency penalty (up to 30 points)
            if self.metrics.latency_ms > 500:
                score -= 30
            elif self.metrics.latency_ms > 200:
                score -= 20
            elif self.metrics.latency_ms > 100:
                score -= 10
            
            # Packet loss penalty (up to 40 points)
            score -= min(40, self.metrics.packet_loss_pct * 4)
            
            # Jitter penalty (up to 15 points)
            if self.metrics.jitter_ms > 100:
                score -= 15
            elif self.metrics.jitter_ms > 50:
                score -= 10
            elif self.metrics.jitter_ms > 20:
                score -= 5
            
            # Signal strength penalty (up to 15 points)
            if self.metrics.signal_strength_dbm < -80:
                score -= 15
            elif self.metrics.signal_strength_dbm < -70:
                score -= 10
            elif self.metrics.signal_strength_dbm < -60:
                score -= 5
            
            return max(0, min(100, score))
    
    async def wait_for_connection(
        self,
        timeout: float = 60.0,
        min_quality: float = 50.0
    ) -> bool:
        """Wait for a stable connection"""
        start = time.time()
        while time.time() - start < timeout:
            if (
                self.is_ready_for_trading() and
                self.get_connection_quality_score() >= min_quality
            ):
                return True
            await asyncio.sleep(1)
        return False


# Singleton instance
_sentinel_instance: Optional[NetworkSentinel] = None


def get_network_sentinel() -> NetworkSentinel:
    """Get the singleton NetworkSentinel instance"""
    global _sentinel_instance
    if _sentinel_instance is None:
        _sentinel_instance = NetworkSentinel()
    return _sentinel_instance
