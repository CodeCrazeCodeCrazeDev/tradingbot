"""
Exchange Health Monitor, Fee Calculator & Latency Monitor
==========================================================

Comprehensive exchange monitoring:
- Health status tracking
- Fee calculation and optimization
- Latency measurement
- Connection quality metrics
- Automatic failover triggers

Author: Elite Trading Bot
Version: 1.0.0
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum, auto
from collections import deque
import threading
import statistics
import json

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
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


class ExchangeStatus(Enum):
    """Exchange health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class LatencyLevel(Enum):
    """Latency classification"""
    EXCELLENT = "excellent"  # < 10ms
    GOOD = "good"           # 10-50ms
    ACCEPTABLE = "acceptable"  # 50-100ms
    POOR = "poor"           # 100-500ms
    CRITICAL = "critical"   # > 500ms
    UNKNOWN = "unknown"     # Not measured


@dataclass
class LatencyMetrics:
    """Latency measurement metrics"""
    exchange: str
    timestamp: datetime
    
    # Current measurements
    current_latency_ms: float = 0.0
    
    # Statistics
    avg_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0.0
    std_dev_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    
    # Classification
    level: LatencyLevel = LatencyLevel.UNKNOWN
    
    # Sample info
    sample_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'exchange': self.exchange,
            'timestamp': self.timestamp.isoformat(),
            'current_ms': self.current_latency_ms,
            'avg_ms': self.avg_latency_ms,
            'min_ms': self.min_latency_ms,
            'max_ms': self.max_latency_ms,
            'std_dev_ms': self.std_dev_ms,
            'p50_ms': self.p50_ms,
            'p95_ms': self.p95_ms,
            'p99_ms': self.p99_ms,
            'level': self.level.value,
            'samples': self.sample_count
        }


@dataclass
class ExchangeHealth:
    """Exchange health status"""
    exchange: str
    status: ExchangeStatus
    timestamp: datetime
    
    # Connection info
    connected: bool = False
    last_heartbeat: Optional[datetime] = None
    connection_uptime_seconds: float = 0.0
    
    # API status
    rest_api_healthy: bool = True
    websocket_healthy: bool = True
    trading_enabled: bool = True
    
    # Error tracking
    error_count_1h: int = 0
    error_count_24h: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    
    # Rate limits
    rate_limit_remaining: int = 0
    rate_limit_reset: Optional[datetime] = None
    
    # Latency
    latency: Optional[LatencyMetrics] = None
    
    def to_dict(self) -> Dict:
        return {
            'exchange': self.exchange,
            'status': self.status.value,
            'timestamp': self.timestamp.isoformat(),
            'connected': self.connected,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'uptime_seconds': self.connection_uptime_seconds,
            'rest_api_healthy': self.rest_api_healthy,
            'websocket_healthy': self.websocket_healthy,
            'trading_enabled': self.trading_enabled,
            'error_count_1h': self.error_count_1h,
            'error_count_24h': self.error_count_24h,
            'last_error': self.last_error,
            'rate_limit_remaining': self.rate_limit_remaining,
            'latency': self.latency.to_dict() if self.latency else None
        }


@dataclass
class FeeStructure:
    """Exchange fee structure"""
    exchange: str
    
    # Trading fees
    maker_fee_pct: float = 0.1
    taker_fee_pct: float = 0.1
    
    # Volume-based discounts
    volume_tier: str = "standard"
    volume_30d: float = 0.0
    
    # Token discounts (e.g., BNB for Binance)
    token_discount_pct: float = 0.0
    token_discount_enabled: bool = False
    
    # Withdrawal fees
    withdrawal_fees: Dict[str, float] = field(default_factory=dict)
    
    # Funding rates (for futures)
    funding_rate_pct: float = 0.0
    next_funding_time: Optional[datetime] = None
    
    def calculate_fee(
        self,
        order_value: float,
        is_maker: bool = False,
        use_token_discount: bool = False
    ) -> float:
        """Calculate trading fee for an order"""
        base_fee_pct = self.maker_fee_pct if is_maker else self.taker_fee_pct
        
        if use_token_discount and self.token_discount_enabled:
            base_fee_pct *= (1 - self.token_discount_pct / 100)
        
        return order_value * (base_fee_pct / 100)
    
    def to_dict(self) -> Dict:
        return {
            'exchange': self.exchange,
            'maker_fee_pct': self.maker_fee_pct,
            'taker_fee_pct': self.taker_fee_pct,
            'volume_tier': self.volume_tier,
            'volume_30d': self.volume_30d,
            'token_discount_pct': self.token_discount_pct,
            'token_discount_enabled': self.token_discount_enabled,
            'withdrawal_fees': self.withdrawal_fees,
            'funding_rate_pct': self.funding_rate_pct
        }


class LatencyMonitor:
    """
    Monitors and tracks exchange latency
    """
    
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.latency_samples: Dict[str, deque] = {}
        self._lock = threading.RLock()
    
    def record_latency(self, exchange: str, latency_ms: float):
        """Record a latency measurement"""
        with self._lock:
            if exchange not in self.latency_samples:
                self.latency_samples[exchange] = deque(maxlen=self.max_samples)
            
            self.latency_samples[exchange].append({
                'timestamp': datetime.now(),
                'latency_ms': latency_ms
            })
    
    def get_metrics(self, exchange: str) -> LatencyMetrics:
        """Get latency metrics for an exchange"""
        with self._lock:
            samples = self.latency_samples.get(exchange, deque())
            
            if not samples:
                return LatencyMetrics(
                    exchange=exchange,
                    timestamp=datetime.now(),
                    level=LatencyLevel.UNKNOWN
                )
            
            latencies = [s['latency_ms'] for s in samples]
            current = latencies[-1] if latencies else 0
            
            # Calculate statistics
            avg = statistics.mean(latencies)
            std_dev = statistics.stdev(latencies) if len(latencies) > 1 else 0
            
            sorted_latencies = sorted(latencies)
            p50 = sorted_latencies[len(sorted_latencies) // 2]
            p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
            p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
            
            # Classify latency level
            if avg < 10:
                level = LatencyLevel.EXCELLENT
            elif avg < 50:
                level = LatencyLevel.GOOD
            elif avg < 100:
                level = LatencyLevel.ACCEPTABLE
            elif avg < 500:
                level = LatencyLevel.POOR
            else:
                level = LatencyLevel.CRITICAL
            
            return LatencyMetrics(
                exchange=exchange,
                timestamp=datetime.now(),
                current_latency_ms=current,
                avg_latency_ms=avg,
                min_latency_ms=min(latencies),
                max_latency_ms=max(latencies),
                std_dev_ms=std_dev,
                p50_ms=p50,
                p95_ms=p95,
                p99_ms=p99,
                level=level,
                sample_count=len(latencies)
            )
    
    async def measure_latency(self, exchange: str, ping_func: Callable) -> float:
        """Measure latency using a ping function"""
        start = time.perf_counter()
        
        try:
            if asyncio.iscoroutinefunction(ping_func):
                await ping_func()
            else:
                ping_func()
            
            latency_ms = (time.perf_counter() - start) * 1000
            self.record_latency(exchange, latency_ms)
            return latency_ms
            
        except Exception as e:
            logger.error(f"Latency measurement failed for {exchange}: {e}")
            return -1


class ExchangeFeeCalculator:
    """
    Calculates and optimizes exchange fees
    """
    
    # Default fee structures for major exchanges
    DEFAULT_FEES = {
        'binance': FeeStructure(
            exchange='binance',
            maker_fee_pct=0.1,
            taker_fee_pct=0.1,
            token_discount_pct=25,
            token_discount_enabled=True
        ),
        'binance_futures': FeeStructure(
            exchange='binance_futures',
            maker_fee_pct=0.02,
            taker_fee_pct=0.04
        ),
        'mt5': FeeStructure(
            exchange='mt5',
            maker_fee_pct=0.0,  # Spread-based
            taker_fee_pct=0.0
        ),
        'interactive_brokers': FeeStructure(
            exchange='interactive_brokers',
            maker_fee_pct=0.0,
            taker_fee_pct=0.0  # Commission-based
        ),
        'coinbase': FeeStructure(
            exchange='coinbase',
            maker_fee_pct=0.4,
            taker_fee_pct=0.6
        ),
        'kraken': FeeStructure(
            exchange='kraken',
            maker_fee_pct=0.16,
            taker_fee_pct=0.26
        )
    }
    
    # IB commission structure
    IB_COMMISSIONS = {
        'stocks_us': {'per_share': 0.005, 'min': 1.0, 'max_pct': 1.0},
        'stocks_eu': {'per_share': 0.05, 'min': 3.0, 'max_pct': 0.5},
        'forex': {'per_million': 20.0, 'min': 2.0},
        'futures': {'per_contract': 0.85},
        'options': {'per_contract': 0.65, 'min': 1.0}
    }
    
    def __init__(self):
        self.fee_structures: Dict[str, FeeStructure] = dict(self.DEFAULT_FEES)
        self.volume_history: Dict[str, List[Dict]] = {}
    
    def get_fee_structure(self, exchange: str) -> FeeStructure:
        """Get fee structure for an exchange"""
        return self.fee_structures.get(
            exchange.lower(),
            FeeStructure(exchange=exchange)
        )
    
    def update_fee_structure(self, exchange: str, fee_structure: FeeStructure):
        """Update fee structure for an exchange"""
        self.fee_structures[exchange.lower()] = fee_structure
    
    def calculate_trading_fee(
        self,
        exchange: str,
        order_value: float,
        is_maker: bool = False,
        use_token_discount: bool = False
    ) -> float:
        """Calculate trading fee"""
        fee_structure = self.get_fee_structure(exchange)
        return fee_structure.calculate_fee(order_value, is_maker, use_token_discount)
    
    def calculate_ib_commission(
        self,
        asset_type: str,
        quantity: float,
        price: float,
        region: str = "us"
    ) -> float:
        """Calculate IB commission"""
        if asset_type == "stocks":
            key = f"stocks_{region}"
            if key in self.IB_COMMISSIONS:
                comm = self.IB_COMMISSIONS[key]
                raw_commission = quantity * comm['per_share']
                min_comm = comm['min']
                max_comm = quantity * price * (comm['max_pct'] / 100)
                return max(min_comm, min(raw_commission, max_comm))
        
        elif asset_type == "forex":
            comm = self.IB_COMMISSIONS['forex']
            order_value = quantity * price
            raw_commission = (order_value / 1_000_000) * comm['per_million']
            return max(comm['min'], raw_commission)
        
        elif asset_type == "futures":
            comm = self.IB_COMMISSIONS['futures']
            return quantity * comm['per_contract']
        
        elif asset_type == "options":
            comm = self.IB_COMMISSIONS['options']
            raw_commission = quantity * comm['per_contract']
            return max(comm['min'], raw_commission)
        
        return 0.0
    
    def calculate_spread_cost(
        self,
        bid: float,
        ask: float,
        quantity: float,
        is_buy: bool = True
    ) -> float:
        """Calculate spread cost (for forex/CFD)"""
        spread = ask - bid
        mid = (bid + ask) / 2
        
        if is_buy:
            # Buying at ask, fair value is mid
            cost = (ask - mid) * quantity
        else:
            # Selling at bid, fair value is mid
            cost = (mid - bid) * quantity
        
        return cost
    
    def compare_exchange_costs(
        self,
        order_value: float,
        exchanges: List[str],
        is_maker: bool = False
    ) -> List[Dict]:
        """Compare costs across exchanges"""
        results = []
        
        for exchange in exchanges:
            fee = self.calculate_trading_fee(exchange, order_value, is_maker)
            fee_structure = self.get_fee_structure(exchange)
            
            results.append({
                'exchange': exchange,
                'fee': fee,
                'fee_pct': (fee / order_value) * 100 if order_value > 0 else 0,
                'maker_fee_pct': fee_structure.maker_fee_pct,
                'taker_fee_pct': fee_structure.taker_fee_pct
            })
        
        # Sort by fee
        results.sort(key=lambda x: x['fee'])
        
        return results
    
    def get_optimal_exchange(
        self,
        order_value: float,
        exchanges: List[str],
        is_maker: bool = False
    ) -> str:
        """Get the exchange with lowest fees"""
        comparison = self.compare_exchange_costs(order_value, exchanges, is_maker)
        return comparison[0]['exchange'] if comparison else ""


class ExchangeHealthMonitor:
    """
    Monitors health of all connected exchanges
    """
    
    def __init__(
        self,
        check_interval_seconds: int = 30,
        error_threshold_1h: int = 10,
        error_threshold_24h: int = 50
    ):
        self.check_interval = check_interval_seconds
        self.error_threshold_1h = error_threshold_1h
        self.error_threshold_24h = error_threshold_24h
        
        # Health tracking
        self.health_status: Dict[str, ExchangeHealth] = {}
        self.error_history: Dict[str, deque] = {}
        self.connection_times: Dict[str, datetime] = {}
        
        # Latency monitor
        self.latency_monitor = LatencyMonitor()
        
        # Fee calculator
        self.fee_calculator = ExchangeFeeCalculator()
        
        # Callbacks
        self.on_status_change: List[Callable] = []
        self.on_unhealthy: List[Callable] = []
        
        # Background task
        self._running = False
        self._monitor_task = None
        
        logger.info("ExchangeHealthMonitor initialized")
    
    def register_exchange(self, exchange: str):
        """Register an exchange for monitoring"""
        self.health_status[exchange] = ExchangeHealth(
            exchange=exchange,
            status=ExchangeStatus.UNKNOWN,
            timestamp=datetime.now()
        )
        self.error_history[exchange] = deque(maxlen=1000)
        logger.info(f"Exchange registered for monitoring: {exchange}")
    
    def record_connection(self, exchange: str, connected: bool):
        """Record connection status"""
        if exchange not in self.health_status:
            self.register_exchange(exchange)
        
        health = self.health_status[exchange]
        health.connected = connected
        health.timestamp = datetime.now()
        
        if connected:
            if exchange not in self.connection_times:
                self.connection_times[exchange] = datetime.now()
            health.last_heartbeat = datetime.now()
        else:
            if exchange in self.connection_times:
                del self.connection_times[exchange]
        
        self._update_status(exchange)
    
    def record_heartbeat(self, exchange: str):
        """Record heartbeat from exchange"""
        if exchange in self.health_status:
            self.health_status[exchange].last_heartbeat = datetime.now()
    
    def record_error(self, exchange: str, error: str):
        """Record an error"""
        if exchange not in self.health_status:
            self.register_exchange(exchange)
        
        self.error_history[exchange].append({
            'timestamp': datetime.now(),
            'error': error
        })
        
        health = self.health_status[exchange]
        health.last_error = error
        health.last_error_time = datetime.now()
        
        self._update_error_counts(exchange)
        self._update_status(exchange)
    
    def record_latency(self, exchange: str, latency_ms: float):
        """Record latency measurement"""
        self.latency_monitor.record_latency(exchange, latency_ms)
        
        if exchange in self.health_status:
            self.health_status[exchange].latency = self.latency_monitor.get_metrics(exchange)
    
    def update_rate_limit(self, exchange: str, remaining: int, reset_time: Optional[datetime] = None):
        """Update rate limit info"""
        if exchange in self.health_status:
            self.health_status[exchange].rate_limit_remaining = remaining
            self.health_status[exchange].rate_limit_reset = reset_time
    
    def _update_error_counts(self, exchange: str):
        """Update error counts"""
        now = datetime.now()
        errors = self.error_history.get(exchange, deque())
        
        # Count errors in last hour
        hour_ago = now - timedelta(hours=1)
        errors_1h = sum(1 for e in errors if e['timestamp'] > hour_ago)
        
        # Count errors in last 24 hours
        day_ago = now - timedelta(hours=24)
        errors_24h = sum(1 for e in errors if e['timestamp'] > day_ago)
        
        health = self.health_status[exchange]
        health.error_count_1h = errors_1h
        health.error_count_24h = errors_24h
    
    def _update_status(self, exchange: str):
        """Update exchange status based on health metrics"""
        if exchange not in self.health_status:
            return
        
        health = self.health_status[exchange]
        old_status = health.status
        
        # Calculate uptime
        if exchange in self.connection_times:
            health.connection_uptime_seconds = (
                datetime.now() - self.connection_times[exchange]
            ).total_seconds()
        
        # Determine status
        if not health.connected:
            health.status = ExchangeStatus.OFFLINE
        elif health.error_count_1h >= self.error_threshold_1h:
            health.status = ExchangeStatus.UNHEALTHY
        elif health.error_count_1h >= self.error_threshold_1h // 2:
            health.status = ExchangeStatus.DEGRADED
        elif not health.rest_api_healthy or not health.websocket_healthy:
            health.status = ExchangeStatus.DEGRADED
        else:
            health.status = ExchangeStatus.HEALTHY
        
        health.timestamp = datetime.now()
        
        # Fire callbacks if status changed
        if old_status != health.status:
            for callback in self.on_status_change:
                try:
                    callback(exchange, old_status, health.status)
                except Exception as e:
                    logger.error(f"Status change callback error: {e}")
            
            if health.status == ExchangeStatus.UNHEALTHY:
                for callback in self.on_unhealthy:
                    try:
                        callback(exchange, health)
                    except Exception as e:
                        logger.error(f"Unhealthy callback error: {e}")
    
    def get_health(self, exchange: str) -> Optional[ExchangeHealth]:
        """Get health status for an exchange"""
        return self.health_status.get(exchange)
    
    def get_all_health(self) -> Dict[str, ExchangeHealth]:
        """Get health status for all exchanges"""
        return dict(self.health_status)
    
    def get_healthy_exchanges(self) -> List[str]:
        """Get list of healthy exchanges"""
        return [
            exchange for exchange, health in self.health_status.items()
            if health.status == ExchangeStatus.HEALTHY
        ]
    
    def is_healthy(self, exchange: str) -> bool:
        """Check if an exchange is healthy"""
        health = self.health_status.get(exchange)
        return health is not None and health.status == ExchangeStatus.HEALTHY
    
    async def start_monitoring(self):
        """Start background health monitoring"""
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Exchange health monitoring started")
    
    async def stop_monitoring(self):
        """Stop background health monitoring"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Exchange health monitoring stopped")
    
    async def _monitor_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                for exchange in list(self.health_status.keys()):
                    self._update_error_counts(exchange)
                    self._update_status(exchange)
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(5)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get health summary for all exchanges"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_exchanges': len(self.health_status),
            'healthy': 0,
            'degraded': 0,
            'unhealthy': 0,
            'offline': 0,
            'exchanges': {}
        }
        
        for exchange, health in self.health_status.items():
            if health.status == ExchangeStatus.HEALTHY:
                summary['healthy'] += 1
            elif health.status == ExchangeStatus.DEGRADED:
                summary['degraded'] += 1
            elif health.status == ExchangeStatus.UNHEALTHY:
                summary['unhealthy'] += 1
            elif health.status == ExchangeStatus.OFFLINE:
                summary['offline'] += 1
            
            summary['exchanges'][exchange] = health.to_dict()
        
        return summary


# Singleton instances
_health_monitor: Optional[ExchangeHealthMonitor] = None
_fee_calculator: Optional[ExchangeFeeCalculator] = None
_latency_monitor: Optional[LatencyMonitor] = None


def get_health_monitor() -> ExchangeHealthMonitor:
    """Get or create health monitor singleton"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = ExchangeHealthMonitor()
    return _health_monitor


def get_fee_calculator() -> ExchangeFeeCalculator:
    """Get or create fee calculator singleton"""
    global _fee_calculator
    if _fee_calculator is None:
        _fee_calculator = ExchangeFeeCalculator()
    return _fee_calculator


def get_latency_monitor() -> LatencyMonitor:
    """Get or create latency monitor singleton"""
    global _latency_monitor
    if _latency_monitor is None:
        _latency_monitor = LatencyMonitor()
    return _latency_monitor


# Export
__all__ = [
    'ExchangeHealthMonitor',
    'ExchangeFeeCalculator',
    'LatencyMonitor',
    'ExchangeHealth',
    'ExchangeStatus',
    'FeeStructure',
    'LatencyMetrics',
    'LatencyLevel',
    'get_health_monitor',
    'get_fee_calculator',
    'get_latency_monitor'
]
