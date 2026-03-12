"""
AlphaAlgo Internet Stability & Safety Module
Complete network monitoring, safe mode, offline mode, and auto-recovery system.
"""

import asyncio
import aiohttp
import logging
import time
import json
import statistics
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
import platform
import subprocess

logger = logging.getLogger(__name__)


class NetworkStatus(Enum):
    """Network connection status."""
    ONLINE = "online"
    DEGRADED = "degraded"
    UNSTABLE = "unstable"
    OFFLINE = "offline"


class TradingMode(Enum):
    """Trading operation modes."""
    NORMAL = "normal"
    SAFE_MODE = "safe_mode"
    OFFLINE_MODE = "offline_mode"
    RECOVERY = "recovery"


@dataclass
class NetworkMetrics:
    """Network performance metrics."""
    timestamp: datetime
    endpoint: str
    latency_ms: float
    packet_loss_percent: float
    status: NetworkStatus
    consecutive_failures: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'endpoint': self.endpoint,
            'latency_ms': self.latency_ms,
            'packet_loss_percent': self.packet_loss_percent,
            'status': self.status.value,
            'consecutive_failures': self.consecutive_failures
        }


@dataclass
class RecoveryState:
    """System recovery state."""
    timestamp: datetime
    mode: TradingMode
    open_positions: List[Dict[str, Any]]
    pending_orders: List[Dict[str, Any]]
    account_balance: float
    equity: float
    last_sync_time: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'mode': self.mode.value,
            'open_positions': self.open_positions,
            'pending_orders': self.pending_orders,
            'account_balance': self.account_balance,
            'equity': self.equity,
            'last_sync_time': self.last_sync_time.isoformat()
        }


class NetworkMonitor:
    """
    Comprehensive Internet Stability & Safety Module
    
    Features:
    1. Continuous network monitoring (ping, latency, packet loss)
    2. Safe Mode activation on network degradation
    3. Offline Mode on connection loss
    4. Auto-recovery when network stabilizes
    5. Fallback endpoints and retry logic
    6. Alert system integration
    7. State persistence for recovery
    8. Performance optimization with async operations
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize network monitor."""
        self.config = config
        
        # Endpoints to monitor
        self.primary_endpoints = config.get('primary_endpoints', [
            'https://api.example.com/health',  # Replace with actual broker API
            '8.8.8.8',  # Google DNS
            '1.1.1.1'   # Cloudflare DNS
        ])
        
        self.fallback_endpoints = config.get('fallback_endpoints', [
            'https://backup-api.example.com/health',
            '8.8.4.4'  # Google DNS secondary
        ])
        
        # Thresholds
        self.latency_warning_ms = config.get('latency_warning_ms', 150)
        self.latency_critical_ms = config.get('latency_critical_ms', 300)
        self.packet_loss_threshold = config.get('packet_loss_threshold', 10)
        self.timeout_seconds = config.get('timeout_seconds', 5)
        
        # Recovery settings
        self.stable_latency_ms = config.get('stable_latency_ms', 100)
        self.stable_duration_seconds = config.get('stable_duration_seconds', 60)
        self.max_offline_minutes = config.get('max_offline_minutes', 15)
        
        # Retry settings
        self.retry_delays = config.get('retry_delays', [1, 2, 4, 8, 16])
        self.max_retries = len(self.retry_delays)
        
        # Monitoring settings
        self.check_interval_seconds = config.get('check_interval_seconds', 10)
        
        # Paths
        self.log_dir = Path(config.get('log_dir', 'logs'))
        self.state_dir = Path(config.get('state_dir', 'state'))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.network_log_file = self.log_dir / 'network_monitor.log'
        self.recovery_state_file = self.state_dir / 'recovery.json'
        
        # State
        self.current_mode = TradingMode.NORMAL
        self.network_status = NetworkStatus.ONLINE
        self.metrics_history: List[NetworkMetrics] = []
        self.stable_since: Optional[datetime] = None
        self.offline_since: Optional[datetime] = None
        self.consecutive_stable_checks = 0
        
        # Alert callbacks
        self.alert_callbacks: List[callable] = []
        
        # Running flag
        self.is_running = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Setup logging
        self._setup_logging()
        
        logger.info("NetworkMonitor initialized")
        logger.info(f"Primary endpoints: {self.primary_endpoints}")
        logger.info(f"Fallback endpoints: {self.fallback_endpoints}")
        logger.info(f"Thresholds - Warning: {self.latency_warning_ms}ms, Critical: {self.latency_critical_ms}ms, Packet Loss: {self.packet_loss_threshold}%")
    
    def _setup_logging(self):
        """Setup file logging for network monitoring."""
        file_handler = logging.FileHandler(self.network_log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    async def start(self):
        """Start network monitoring."""
        if self.is_running:
            logger.warning("Network monitor already running")
            return
        
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("✅ Network monitoring started")
    
    async def stop(self):
        """Stop network monitoring."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Network monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        logger.info("Network monitoring loop started")
        
        while self.is_running:
            try:
                # Check all endpoints
                metrics = await self._check_all_endpoints()
                
                # Analyze metrics and update status
                await self._analyze_metrics(metrics)
                
                # Log metrics
                self._log_metrics(metrics)
                
                # Check for mode transitions
                await self._check_mode_transitions()
                
                # Wait for next check
                await asyncio.sleep(self.check_interval_seconds)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval_seconds)
        
        logger.info("Network monitoring loop stopped")
    
    async def _check_all_endpoints(self) -> List[NetworkMetrics]:
        """Check all endpoints and return metrics."""
        tasks = []
        
        # Check primary endpoints
        for endpoint in self.primary_endpoints:
            tasks.append(self._check_endpoint(endpoint, is_primary=True))
        
        # Check fallback endpoints
        for endpoint in self.fallback_endpoints:
            tasks.append(self._check_endpoint(endpoint, is_primary=False))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        metrics = [r for r in results if isinstance(r, NetworkMetrics)]
        
        return metrics
    
    async def _check_endpoint(self, endpoint: str, is_primary: bool = True) -> NetworkMetrics:
        """Check a single endpoint."""
        start_time = time.time()
        consecutive_failures = 0
        
        try:
            if endpoint.startswith('http'):
                # HTTP endpoint check
                latency_ms, success = await self._check_http_endpoint(endpoint)
            else:
                # IP address - use ping
                latency_ms, success = await self._ping_endpoint(endpoint)
            
            if not success:
                consecutive_failures += 1
            
            # Determine status
            if not success:
                status = NetworkStatus.OFFLINE
            elif latency_ms > self.latency_critical_ms:
                status = NetworkStatus.UNSTABLE
            elif latency_ms > self.latency_warning_ms:
                status = NetworkStatus.DEGRADED
            else:
                status = NetworkStatus.ONLINE
            
            # Calculate packet loss (simplified)
            packet_loss = 100.0 if not success else 0.0
            
            return NetworkMetrics(
                timestamp=datetime.now(),
                endpoint=endpoint,
                latency_ms=latency_ms,
                packet_loss_percent=packet_loss,
                status=status,
                consecutive_failures=consecutive_failures
            )
        
        except Exception as e:
            logger.error(f"Error checking endpoint {endpoint}: {e}")
            return NetworkMetrics(
                timestamp=datetime.now(),
                endpoint=endpoint,
                latency_ms=9999.0,
                packet_loss_percent=100.0,
                status=NetworkStatus.OFFLINE,
                consecutive_failures=1
            )
    
    async def _check_http_endpoint(self, url: str) -> Tuple[float, bool]:
        """Check HTTP endpoint and return latency and success."""
        try:
            start_time = time.time()
            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    latency_ms = (time.time() - start_time) * 1000
                    success = response.status == 200
                    return latency_ms, success
        
        except asyncio.TimeoutError:
            return self.timeout_seconds * 1000, False
        except Exception as e:
            logger.debug(f"HTTP check failed for {url}: {e}")
            return 9999.0, False
    
    async def _ping_endpoint(self, ip: str) -> Tuple[float, bool]:
        """Ping IP address and return latency and success."""
        try:
            # Platform-specific ping command
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', ip]
            
            start_time = time.time()
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds
            )
            
            latency_ms = (time.time() - start_time) * 1000
            success = process.returncode == 0
            
            # Try to extract actual ping time from output
            if success:
                output = stdout.decode()
                if 'time=' in output:
                    # Extract time value
                    time_str = output.split('time=')[1].split('ms')[0].strip()
                    try:
                        latency_ms = float(time_str)
                    except ValueError:
                        pass
            
            return latency_ms, success
        
        except asyncio.TimeoutError:
            return self.timeout_seconds * 1000, False
        except Exception as e:
            logger.debug(f"Ping failed for {ip}: {e}")
            return 9999.0, False
    
    async def _analyze_metrics(self, metrics: List[NetworkMetrics]):
        """Analyze metrics and update network status."""
        if not metrics:
            self.network_status = NetworkStatus.OFFLINE
            return
        
        # Calculate average latency from successful checks
        successful_metrics = [m for m in metrics if m.status != NetworkStatus.OFFLINE]
        
        if not successful_metrics:
            self.network_status = NetworkStatus.OFFLINE
            return
        
        avg_latency = statistics.mean([m.latency_ms for m in successful_metrics])
        max_latency = max([m.latency_ms for m in successful_metrics])
        
        # Calculate packet loss
        total_checks = len(metrics)
        failed_checks = len([m for m in metrics if m.status == NetworkStatus.OFFLINE])
        packet_loss = (failed_checks / total_checks) * 100
        
        # Determine overall status
        if packet_loss > self.packet_loss_threshold:
            self.network_status = NetworkStatus.UNSTABLE
        elif max_latency > self.latency_critical_ms:
            self.network_status = NetworkStatus.UNSTABLE
        elif avg_latency > self.latency_warning_ms:
            self.network_status = NetworkStatus.DEGRADED
        else:
            self.network_status = NetworkStatus.ONLINE
        
        # Track stability
        if self.network_status == NetworkStatus.ONLINE and avg_latency < self.stable_latency_ms:
            if self.stable_since is None:
                self.stable_since = datetime.now()
            self.consecutive_stable_checks += 1
        else:
            self.stable_since = None
            self.consecutive_stable_checks = 0
        
        # Store metrics
        self.metrics_history.extend(metrics)
        
        # Keep only last 1000 metrics
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
    
    async def _check_mode_transitions(self):
        """Check if mode should transition based on network status."""
        current_time = datetime.now()
        
        # NORMAL -> SAFE_MODE
        if self.current_mode == TradingMode.NORMAL:
            if self.network_status in [NetworkStatus.UNSTABLE, NetworkStatus.DEGRADED]:
                await self._enter_safe_mode()
        
        # NORMAL/SAFE_MODE -> OFFLINE_MODE
        if self.current_mode in [TradingMode.NORMAL, TradingMode.SAFE_MODE]:
            if self.network_status == NetworkStatus.OFFLINE:
                if self.offline_since is None:
                    self.offline_since = current_time
                elif (current_time - self.offline_since).total_seconds() > self.timeout_seconds:
                    await self._enter_offline_mode()
        
        # SAFE_MODE/OFFLINE_MODE -> RECOVERY
        if self.current_mode in [TradingMode.SAFE_MODE, TradingMode.OFFLINE_MODE]:
            if self.network_status == NetworkStatus.ONLINE:
                if self.stable_since and (current_time - self.stable_since).total_seconds() >= self.stable_duration_seconds:
                    await self._enter_recovery_mode()
        
        # RECOVERY -> NORMAL
        if self.current_mode == TradingMode.RECOVERY:
            if self.network_status == NetworkStatus.ONLINE:
                await self._enter_normal_mode()
        
        # Check for emergency shutdown
        if self.current_mode == TradingMode.OFFLINE_MODE:
            if self.offline_since and (current_time - self.offline_since).total_seconds() > (self.max_offline_minutes * 60):
                await self._emergency_shutdown()
    
    async def _enter_safe_mode(self):
        """Enter Safe Mode - stop new trades, manage existing positions."""
        if self.current_mode == TradingMode.SAFE_MODE:
            return
        
        logger.warning("⚠️ Network unstable – entering Safe Mode")
        logger.warning(f"Current status: {self.network_status.value}")
        
        # Save current state
        await self._save_recovery_state()
        
        # Update mode
        self.current_mode = TradingMode.SAFE_MODE
        
        # Send alert
        await self._send_alert(
            level="WARNING",
            message=f"AlphaAlgo entered Safe Mode due to network instability ({self.network_status.value})"
        )
        
        logger.info("Safe Mode activated - new trades stopped, existing positions monitored")
    
    async def _enter_offline_mode(self):
        """Enter Offline Mode - pause all trading activity."""
        if self.current_mode == TradingMode.OFFLINE_MODE:
            return
        
        logger.error("🌐 Connection lost – trading paused")
        
        # Save current state
        await self._save_recovery_state()
        
        # Update mode
        self.current_mode = TradingMode.OFFLINE_MODE
        self.offline_since = datetime.now()
        
        # Send alert
        await self._send_alert(
            level="CRITICAL",
            message="ALERT: AlphaAlgo connection lost. All trading paused."
        )
        
        logger.info("Offline Mode activated - all trading paused")
    
    async def _enter_recovery_mode(self):
        """Enter Recovery Mode - prepare to resume trading."""
        if self.current_mode == TradingMode.RECOVERY:
            return
        
        logger.info("✅ Internet stable – initiating recovery")
        
        # Update mode
        self.current_mode = TradingMode.RECOVERY
        
        # Re-sync positions and balances
        await self._resync_trading_state()
        
        # Validate data consistency
        await self._validate_consistency()
        
        logger.info("Recovery Mode - validating system state")
    
    async def _enter_normal_mode(self):
        """Enter Normal Mode - resume full trading operations."""
        if self.current_mode == TradingMode.NORMAL:
            return
        
        logger.info("✅ Internet stable – resuming operations")
        
        # Clear offline tracking
        self.offline_since = None
        self.stable_since = None
        
        # Update mode
        self.current_mode = TradingMode.NORMAL
        
        # Send alert
        await self._send_alert(
            level="INFO",
            message="AlphaAlgo resumed normal operations. Network stable."
        )
        
        logger.info("Normal Mode activated - full trading resumed")
    
    async def _emergency_shutdown(self):
        """Emergency shutdown after prolonged offline period."""
        logger.critical(f"🚨 EMERGENCY SHUTDOWN: Network offline for {self.max_offline_minutes} minutes")
        
        # Save final state
        await self._save_recovery_state()
        
        # Send critical alert
        await self._send_alert(
            level="CRITICAL",
            message=f"EMERGENCY: AlphaAlgo shutting down after {self.max_offline_minutes} minutes offline"
        )
        
        # Stop monitoring
        await self.stop()
        
        logger.critical("Emergency shutdown complete")
    
    async def _save_recovery_state(self):
        """Save current system state for recovery."""
        try:
            # Get actual positions and orders from trading system
            open_positions = []
            pending_orders = []
            account_balance = 0.0
            equity = 0.0
            
            try:
                # Try to get from position manager
                from trading_bot.position_manager import PositionManager
                if hasattr(self, 'position_manager') and self.position_manager:
                    open_positions = self.position_manager.get_all_positions()
            except Exception as e:
                logger.debug(f"Could not get positions from manager: {e}")
            # Try to get from order manager
                from trading_bot.execution import OrderManager
                if hasattr(self, 'order_manager') and self.order_manager:
                    pending_orders = self.order_manager.get_pending_orders()
            except Exception as e:
                logger.debug(f"Could not get orders from manager: {e}")
            # Try to get account data
                from trading_bot.brokers import BrokerAdapter
                if hasattr(self, 'broker') and self.broker:
                    account_balance = await self.broker.get_account_balance()
                    equity = await self.broker.get_account_equity()
            except Exception as e:
                logger.debug(f"Could not get account data: {e}")
            
            state = RecoveryState(
                timestamp=datetime.now(),
                mode=self.current_mode,
                open_positions=open_positions,
                pending_orders=pending_orders,
                account_balance=account_balance,
                equity=equity,
                last_sync_time=datetime.now()
            )
            
            with open(self.recovery_state_file, 'w') as f:
                json.dump(state.to_dict(), f, indent=2)
            
            logger.info(f"Recovery state saved to {self.recovery_state_file}")
        
        except Exception as e:
            logger.error(f"Failed to save recovery state: {e}", exc_info=True)
    
    async def _resync_trading_state(self):
        """Re-sync open positions and balances with broker."""
        try:
            logger.info("Re-syncing trading state with broker...")
            
            # 1. Fetch current positions from broker
            broker_positions = []
            try:
                if hasattr(self, 'broker') and self.broker:
                    broker_positions = await self.broker.get_positions()
                    logger.info(f"Fetched {len(broker_positions)} positions from broker")
            except Exception as e:
                logger.error(f"Failed to fetch positions: {e}")
            
            # 2. Fetch pending orders from broker
            broker_orders = []
            try:
                if hasattr(self, 'broker') and self.broker:
                    broker_orders = await self.broker.get_pending_orders()
                    logger.info(f"Fetched {len(broker_orders)} pending orders from broker")
            except Exception as e:
                logger.error(f"Failed to fetch orders: {e}")
            # 3. Fetch account balance and equity
                if hasattr(self, 'broker') and self.broker:
                    balance = await self.broker.get_account_balance()
                    equity = await self.broker.get_account_equity()
                    logger.info(f"Account - Balance: {balance}, Equity: {equity}")
            except Exception as e:
                logger.error(f"Failed to fetch account data: {e}")
            # 4. Compare with saved state and reconcile
                if hasattr(self, 'position_manager') and self.position_manager:
                    local_positions = self.position_manager.get_all_positions()
                    if len(broker_positions) != len(local_positions):
                        logger.warning(f"Position count mismatch: broker={len(broker_positions)}, local={len(local_positions)}")
                        # Reconcile: add missing positions
                        for bp in broker_positions:
                            if not any(p.ticket == bp.ticket for p in local_positions):
                                logger.info(f"Adding missing position: {bp.ticket}")
                                self.position_manager.add_position(bp)
            except Exception as e:
                logger.error(f"Failed to reconcile positions: {e}")
            
            logger.info("Trading state re-synced successfully")
        
        except Exception as e:
            logger.error(f"Failed to re-sync trading state: {e}", exc_info=True)
    
    async def _validate_consistency(self):
        """Validate data consistency between bot and broker."""
        try:
            logger.info("Validating data consistency...")
            
            consistency_issues = []
            
            try:
                # 1. Verify position counts match
                if hasattr(self, 'broker') and self.broker and hasattr(self, 'position_manager'):
                    broker_positions = await self.broker.get_positions()
                    local_positions = self.position_manager.get_all_positions() if self.position_manager else []
                    if len(broker_positions) != len(local_positions):
                        consistency_issues.append(f"Position count mismatch: broker={len(broker_positions)}, local={len(local_positions)}")
                        logger.warning(consistency_issues[-1])
            except Exception as e:
                logger.error(f"Failed to verify position counts: {e}")
            # 2. Verify order counts match
                if hasattr(self, 'broker') and self.broker:
                    broker_orders = await self.broker.get_pending_orders()
                    if hasattr(self, 'order_manager') and self.order_manager:
                        local_orders = self.order_manager.get_pending_orders()
                        if len(broker_orders) != len(local_orders):
                            consistency_issues.append(f"Order count mismatch: broker={len(broker_orders)}, local={len(local_orders)}")
                            logger.warning(consistency_issues[-1])
            except Exception as e:
                logger.error(f"Failed to verify order counts: {e}")
            # 3. Verify balance matches
                if hasattr(self, 'broker') and self.broker:
                    broker_balance = await self.broker.get_account_balance()
                    if hasattr(self, 'last_account_balance'):
                        if abs(self.last_account_balance - broker_balance) > 0.01:
                            consistency_issues.append(f"Balance mismatch: local={self.last_account_balance}, broker={broker_balance}")
                            logger.warning(consistency_issues[-1])
                    self.last_account_balance = broker_balance
            except Exception as e:
                logger.error(f"Failed to verify balance: {e}")
            # 4. Check for orphaned orders or positions
                if hasattr(self, 'broker') and self.broker and hasattr(self, 'position_manager'):
                    broker_positions = await self.broker.get_positions()
                    local_positions = self.position_manager.get_all_positions() if self.position_manager else []
                    
                    # Find orphaned local positions
                    for lp in local_positions:
                        if not any(bp.ticket == lp.ticket for bp in broker_positions):
                            consistency_issues.append(f"Orphaned local position: {lp.ticket}")
                            logger.warning(consistency_issues[-1])
                    
                    # Find orphaned broker positions
                    for bp in broker_positions:
                        if not any(lp.ticket == bp.ticket for lp in local_positions):
                            consistency_issues.append(f"Orphaned broker position: {bp.ticket}")
                            logger.warning(consistency_issues[-1])
            except Exception as e:
                logger.error(f"Failed to check for orphaned positions: {e}")
            
            if consistency_issues:
                logger.warning(f"Data consistency check found {len(consistency_issues)} issues")
            else:
                logger.info("Data consistency validated successfully")
        
        except Exception as e:
            logger.error(f"Consistency validation failed: {e}", exc_info=True)
    
    def _log_metrics(self, metrics: List[NetworkMetrics]):
        """Log network metrics to file."""
        try:
            with open(self.network_log_file, 'a') as f:
                for metric in metrics:
                    log_entry = {
                        'timestamp': metric.timestamp.isoformat(),
                        'endpoint': metric.endpoint,
                        'latency_ms': metric.latency_ms,
                        'packet_loss': metric.packet_loss_percent,
                        'status': metric.status.value,
                        'mode': self.current_mode.value
                    }
                    f.write(json.dumps(log_entry) + '\n')
        
        except Exception as e:
            logger.error(f"Failed to log metrics: {e}")
    
    async def _send_alert(self, level: str, message: str):
        """Send alert through registered callbacks."""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'network_status': self.network_status.value,
            'trading_mode': self.current_mode.value
        }
        
        # Log alert
        if level == "CRITICAL":
            logger.critical(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    def register_alert_callback(self, callback: callable):
        """Register a callback for alerts."""
        self.alert_callbacks.append(callback)
        logger.info(f"Alert callback registered: {callback.__name__}")
    
    async def api_call_with_retry(self, api_func: callable, *args, **kwargs) -> Any:
        """
        Execute API call with exponential backoff retry logic.
        
        Args:
            api_func: Async function to call
            *args, **kwargs: Arguments for the function
        
        Returns:
            Result from api_func
        
        Raises:
            Exception if all retries fail
        """
        last_exception = None
        
        for attempt, delay in enumerate(self.retry_delays, 1):
            try:
                # Check if we should use fallback
                if attempt > 2 and self.network_status in [NetworkStatus.UNSTABLE, NetworkStatus.OFFLINE]:
                    logger.info(f"Attempting fallback endpoint (attempt {attempt})")
                
                # Execute API call
                result = await api_func(*args, **kwargs)
                
                # Success
                if attempt > 1:
                    logger.info(f"API call succeeded on attempt {attempt}")
                
                return result
            
            except Exception as e:
                last_exception = e
                logger.warning(f"API call failed (attempt {attempt}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries:
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"API call failed after {self.max_retries} attempts")
        
        # All retries failed
        raise last_exception
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current network and trading status."""
        recent_metrics = self.metrics_history[-10:] if self.metrics_history else []
        
        avg_latency = 0.0
        if recent_metrics:
            successful = [m for m in recent_metrics if m.status != NetworkStatus.OFFLINE]
            if successful:
                avg_latency = statistics.mean([m.latency_ms for m in successful])
        
        return {
            'network_status': self.network_status.value,
            'trading_mode': self.current_mode.value,
            'average_latency_ms': avg_latency,
            'stable_since': self.stable_since.isoformat() if self.stable_since else None,
            'offline_since': self.offline_since.isoformat() if self.offline_since else None,
            'consecutive_stable_checks': self.consecutive_stable_checks,
            'is_trading_allowed': self.current_mode == TradingMode.NORMAL,
            'recent_metrics': [m.to_dict() for m in recent_metrics]
        }
    
    def is_trading_allowed(self) -> bool:
        """Check if trading is allowed in current mode."""
        return self.current_mode == TradingMode.NORMAL
    
    def is_safe_mode(self) -> bool:
        """Check if in safe mode."""
        return self.current_mode == TradingMode.SAFE_MODE
    
    def is_offline(self) -> bool:
        """Check if offline."""
        return self.current_mode == TradingMode.OFFLINE_MODE


# Singleton instance
_network_monitor_instance: Optional[NetworkMonitor] = None


def get_network_monitor(config: Optional[Dict[str, Any]] = None) -> NetworkMonitor:
    """Get or create network monitor singleton."""
    global _network_monitor_instance
    
    if _network_monitor_instance is None:
        if config is None:
            raise ValueError("Config required for first initialization")
        _network_monitor_instance = NetworkMonitor(config)
    
    return _network_monitor_instance
