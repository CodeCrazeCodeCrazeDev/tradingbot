"""
Compliance, Fraud Detection, and Trade Surveillance System

Production-ready compliance infrastructure:
- Regulatory compliance checks (MiFID II, SEC)
- Real-time fraud/anomaly detection
- Trade surveillance
- Market manipulation detection
- Wash trading detection
- Spoofing detection
- Best execution monitoring
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics

logger = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class ComplianceViolationType(Enum):
    """Types of compliance violations"""
    # Trading violations
    WASH_TRADING = "wash_trading"
    SPOOFING = "spoofing"
    LAYERING = "layering"
    FRONT_RUNNING = "front_running"
    MARKET_MANIPULATION = "market_manipulation"
    
    # Regulatory violations
    POSITION_LIMIT_BREACH = "position_limit_breach"
    CONCENTRATION_LIMIT = "concentration_limit"
    BEST_EXECUTION_FAILURE = "best_execution_failure"
    
    # Risk violations
    EXCESSIVE_TRADING = "excessive_trading"
    UNUSUAL_VOLUME = "unusual_volume"
    PRICE_ANOMALY = "price_anomaly"
    
    # Operational
    UNAUTHORIZED_TRADING = "unauthorized_trading"
    SYSTEM_ABUSE = "system_abuse"


class ComplianceSeverity(Enum):
    """Severity levels for compliance issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RegulatoryFramework(Enum):
    """Regulatory frameworks"""
    MIFID_II = "mifid_ii"
    SEC = "sec"
    CFTC = "cftc"
    FCA = "fca"
    ESMA = "esma"


@dataclass
class ComplianceAlert:
    """Compliance alert"""
    alert_id: str
    violation_type: ComplianceViolationType
    severity: ComplianceSeverity
    timestamp: datetime
    symbol: Optional[str]
    user_id: Optional[str]
    description: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    regulatory_framework: Optional[RegulatoryFramework] = None
    acknowledged: bool = False
    resolved: bool = False
    resolution_notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'alert_id': self.alert_id,
            'violation_type': self.violation_type.value,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'user_id': self.user_id,
            'description': self.description,
            'evidence': self.evidence,
            'regulatory_framework': self.regulatory_framework.value if self.regulatory_framework else None,
            'acknowledged': self.acknowledged,
            'resolved': self.resolved
        }


@dataclass
class TradeRecord:
    """Trade record for surveillance"""
    trade_id: str
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    timestamp: datetime
    user_id: Optional[str] = None
    account_id: Optional[str] = None
    venue: Optional[str] = None
    order_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class WashTradingDetector:
    """
    Detect wash trading patterns.
    
    Wash trading: Buying and selling the same security to create
    misleading market activity.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Detection parameters
        self.time_window_seconds = self.config.get('time_window_seconds', 300)  # 5 minutes
        self.min_round_trips = self.config.get('min_round_trips', 3)
        self.price_tolerance_pct = self.config.get('price_tolerance_pct', 0.1)  # 0.1%
        
        # Trade history by account
        self.trade_history: Dict[str, deque] = {}
        self.max_history = 1000
    
    def analyze_trade(self, trade: TradeRecord) -> Optional[ComplianceAlert]:
        """Analyze trade for wash trading patterns"""
        account_key = trade.account_id or trade.user_id or 'default'
        
        if account_key not in self.trade_history:
            self.trade_history[account_key] = deque(maxlen=self.max_history)
        
        history = self.trade_history[account_key]
        history.append(trade)
        
        # Look for round-trip patterns
        cutoff_time = trade.timestamp - timedelta(seconds=self.time_window_seconds)
        recent_trades = [t for t in history if t.timestamp >= cutoff_time and t.symbol == trade.symbol]
        
        if len(recent_trades) < 2:
            return None
        
        # Count buy/sell pairs at similar prices
        buys = [t for t in recent_trades if t.side.lower() == 'buy']
        sells = [t for t in recent_trades if t.side.lower() == 'sell']
        
        round_trips = 0
        for buy in buys:
            for sell in sells:
                price_diff_pct = abs(buy.price - sell.price) / buy.price * 100
                if price_diff_pct <= self.price_tolerance_pct:
                    round_trips += 1
        
        if round_trips >= self.min_round_trips:
            return ComplianceAlert(
                alert_id=f"wash_{trade.trade_id}",
                violation_type=ComplianceViolationType.WASH_TRADING,
                severity=ComplianceSeverity.HIGH,
                timestamp=datetime.now(),
                symbol=trade.symbol,
                user_id=trade.user_id,
                description=f"Potential wash trading detected: {round_trips} round-trip trades in {self.time_window_seconds}s",
                evidence={
                    'round_trips': round_trips,
                    'time_window': self.time_window_seconds,
                    'trades': [t.trade_id for t in recent_trades]
                }
            )
        
        return None


class SpoofingDetector:
    """
    Detect spoofing patterns.
    
    Spoofing: Placing orders with intent to cancel before execution
    to manipulate prices.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Detection parameters
        self.time_window_seconds = self.config.get('time_window_seconds', 60)
        self.cancel_ratio_threshold = self.config.get('cancel_ratio_threshold', 0.9)  # 90%
        self.min_orders = self.config.get('min_orders', 10)
        
        # Order history
        self.order_history: Dict[str, deque] = {}
        self.max_history = 500
    
    def record_order(self, order_id: str, symbol: str, user_id: str, 
                     action: str, timestamp: datetime):
        """Record order action (placed, cancelled, filled)"""
        key = f"{user_id}:{symbol}"
        
        if key not in self.order_history:
            self.order_history[key] = deque(maxlen=self.max_history)
        
        self.order_history[key].append({
            'order_id': order_id,
            'action': action,
            'timestamp': timestamp
        })
    
    def analyze(self, user_id: str, symbol: str) -> Optional[ComplianceAlert]:
        """Analyze for spoofing patterns"""
        key = f"{user_id}:{symbol}"
        
        if key not in self.order_history:
            return None
        
        history = self.order_history[key]
        cutoff = datetime.now() - timedelta(seconds=self.time_window_seconds)
        recent = [o for o in history if o['timestamp'] >= cutoff]
        
        if len(recent) < self.min_orders:
            return None
        
        placed = sum(1 for o in recent if o['action'] == 'placed')
        cancelled = sum(1 for o in recent if o['action'] == 'cancelled')
        
        if placed == 0:
            return None
        
        cancel_ratio = cancelled / placed
        
        if cancel_ratio >= self.cancel_ratio_threshold:
            return ComplianceAlert(
                alert_id=f"spoof_{user_id}_{symbol}_{int(datetime.now().timestamp())}",
                violation_type=ComplianceViolationType.SPOOFING,
                severity=ComplianceSeverity.CRITICAL,
                timestamp=datetime.now(),
                symbol=symbol,
                user_id=user_id,
                description=f"Potential spoofing: {cancel_ratio*100:.1f}% cancel rate ({cancelled}/{placed} orders)",
                evidence={
                    'cancel_ratio': cancel_ratio,
                    'orders_placed': placed,
                    'orders_cancelled': cancelled,
                    'time_window': self.time_window_seconds
                }
            )
        
        return None


class BestExecutionMonitor:
    """
    Monitor best execution compliance.
    
    Ensures trades are executed at the best available prices.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Thresholds
        self.slippage_threshold_bps = self.config.get('slippage_threshold_bps', 10)  # 10 bps
        self.latency_threshold_ms = self.config.get('latency_threshold_ms', 100)
        
        # Price history for comparison
        self.price_history: Dict[str, deque] = {}
        self.max_history = 100
    
    def record_market_price(self, symbol: str, bid: float, ask: float, timestamp: datetime):
        """Record market price"""
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.max_history)
        
        self.price_history[symbol].append({
            'bid': bid,
            'ask': ask,
            'mid': (bid + ask) / 2,
            'timestamp': timestamp
        })
    
    def analyze_execution(
        self,
        trade: TradeRecord,
        expected_price: float,
        market_bid: Optional[float] = None,
        market_ask: Optional[float] = None
    ) -> Optional[ComplianceAlert]:
        """Analyze trade execution quality"""
        # Calculate slippage
        if trade.side.lower() == 'buy':
            reference_price = market_ask or expected_price
            slippage = (trade.price - reference_price) / reference_price * 10000  # bps
        else:
            reference_price = market_bid or expected_price
            slippage = (reference_price - trade.price) / reference_price * 10000  # bps
        
        if slippage > self.slippage_threshold_bps:
            return ComplianceAlert(
                alert_id=f"exec_{trade.trade_id}",
                violation_type=ComplianceViolationType.BEST_EXECUTION_FAILURE,
                severity=ComplianceSeverity.MEDIUM if slippage < 50 else ComplianceSeverity.HIGH,
                timestamp=datetime.now(),
                symbol=trade.symbol,
                user_id=trade.user_id,
                description=f"Best execution concern: {slippage:.1f} bps slippage",
                evidence={
                    'executed_price': trade.price,
                    'reference_price': reference_price,
                    'slippage_bps': slippage
                },
                regulatory_framework=RegulatoryFramework.MIFID_II
            )
        
        return None


class PositionLimitMonitor:
    """
    Monitor position limits and concentration.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Limits
        self.position_limits: Dict[str, float] = self.config.get('position_limits', {})
        self.default_limit = self.config.get('default_limit', 1000000)  # $1M
        self.concentration_limit_pct = self.config.get('concentration_limit_pct', 25)  # 25%
        
        # Current positions
        self.positions: Dict[str, Dict[str, float]] = {}  # account -> symbol -> value
    
    def update_position(self, account_id: str, symbol: str, value: float):
        """Update position value"""
        if account_id not in self.positions:
            self.positions[account_id] = {}
        self.positions[account_id][symbol] = value
    
    def check_limits(self, account_id: str, symbol: str, 
                     proposed_value: float) -> Optional[ComplianceAlert]:
        """Check if proposed position would breach limits"""
        limit = self.position_limits.get(symbol, self.default_limit)
        
        current_value = self.positions.get(account_id, {}).get(symbol, 0)
        new_value = current_value + proposed_value
        
        if abs(new_value) > limit:
            return ComplianceAlert(
                alert_id=f"limit_{account_id}_{symbol}_{int(datetime.now().timestamp())}",
                violation_type=ComplianceViolationType.POSITION_LIMIT_BREACH,
                severity=ComplianceSeverity.HIGH,
                timestamp=datetime.now(),
                symbol=symbol,
                user_id=account_id,
                description=f"Position limit breach: ${abs(new_value):,.0f} exceeds limit ${limit:,.0f}",
                evidence={
                    'current_value': current_value,
                    'proposed_value': proposed_value,
                    'new_value': new_value,
                    'limit': limit
                }
            )
        
        # Check concentration
        total_portfolio = sum(abs(v) for v in self.positions.get(account_id, {}).values())
        if total_portfolio > 0:
            concentration = abs(new_value) / total_portfolio * 100
            if concentration > self.concentration_limit_pct:
                return ComplianceAlert(
                    alert_id=f"conc_{account_id}_{symbol}_{int(datetime.now().timestamp())}",
                    violation_type=ComplianceViolationType.CONCENTRATION_LIMIT,
                    severity=ComplianceSeverity.MEDIUM,
                    timestamp=datetime.now(),
                    symbol=symbol,
                    user_id=account_id,
                    description=f"Concentration limit: {concentration:.1f}% exceeds {self.concentration_limit_pct}%",
                    evidence={
                        'concentration_pct': concentration,
                        'limit_pct': self.concentration_limit_pct
                    }
                )
        
        return None


class AnomalyDetector:
    """
    Detect trading anomalies using statistical methods.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Detection parameters
        self.volume_zscore_threshold = self.config.get('volume_zscore_threshold', 3.0)
        self.price_zscore_threshold = self.config.get('price_zscore_threshold', 4.0)
        self.min_samples = self.config.get('min_samples', 20)
        
        # Historical data
        self.volume_history: Dict[str, deque] = {}
        self.price_history: Dict[str, deque] = {}
        self.max_history = 100
    
    def record_trade(self, symbol: str, volume: float, price: float):
        """Record trade data"""
        if symbol not in self.volume_history:
            self.volume_history[symbol] = deque(maxlen=self.max_history)
            self.price_history[symbol] = deque(maxlen=self.max_history)
        
        self.volume_history[symbol].append(volume)
        self.price_history[symbol].append(price)
    
    def analyze(self, symbol: str, volume: float, price: float) -> List[ComplianceAlert]:
        """Analyze for anomalies"""
        alerts = []
        
        # Volume anomaly
        if symbol in self.volume_history and len(self.volume_history[symbol]) >= self.min_samples:
            volumes = list(self.volume_history[symbol])
            mean_vol = statistics.mean(volumes)
            std_vol = statistics.stdev(volumes) if len(volumes) > 1 else 1
            
            if std_vol > 0:
                zscore = (volume - mean_vol) / std_vol
                if abs(zscore) > self.volume_zscore_threshold:
                    alerts.append(ComplianceAlert(
                        alert_id=f"vol_anom_{symbol}_{int(datetime.now().timestamp())}",
                        violation_type=ComplianceViolationType.UNUSUAL_VOLUME,
                        severity=ComplianceSeverity.MEDIUM,
                        timestamp=datetime.now(),
                        symbol=symbol,
                        user_id=None,
                        description=f"Unusual volume: {zscore:.1f} standard deviations from mean",
                        evidence={
                            'volume': volume,
                            'mean_volume': mean_vol,
                            'zscore': zscore
                        }
                    ))
        
        # Price anomaly
        if symbol in self.price_history and len(self.price_history[symbol]) >= self.min_samples:
            prices = list(self.price_history[symbol])
            mean_price = statistics.mean(prices)
            std_price = statistics.stdev(prices) if len(prices) > 1 else 1
            
            if std_price > 0:
                zscore = (price - mean_price) / std_price
                if abs(zscore) > self.price_zscore_threshold:
                    alerts.append(ComplianceAlert(
                        alert_id=f"price_anom_{symbol}_{int(datetime.now().timestamp())}",
                        violation_type=ComplianceViolationType.PRICE_ANOMALY,
                        severity=ComplianceSeverity.HIGH,
                        timestamp=datetime.now(),
                        symbol=symbol,
                        user_id=None,
                        description=f"Price anomaly: {zscore:.1f} standard deviations from mean",
                        evidence={
                            'price': price,
                            'mean_price': mean_price,
                            'zscore': zscore
                        }
                    ))
        
        # Record for future analysis
        self.record_trade(symbol, volume, price)
        
        return alerts


class ComplianceEngine:
    """
    Main compliance engine coordinating all detection systems.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize detectors
        self.wash_trading = WashTradingDetector(config.get('wash_trading', {}))
        self.spoofing = SpoofingDetector(config.get('spoofing', {}))
        self.best_execution = BestExecutionMonitor(config.get('best_execution', {}))
        self.position_limits = PositionLimitMonitor(config.get('position_limits', {}))
        self.anomaly = AnomalyDetector(config.get('anomaly', {}))
        
        # Alert storage
        self.alerts: List[ComplianceAlert] = []
        self.max_alerts = self.config.get('max_alerts', 10000)
        
        # Callbacks
        self.on_alert: Optional[callable] = None
        
        # Enabled checks
        self.enabled_checks: Set[str] = set(self.config.get('enabled_checks', [
            'wash_trading', 'spoofing', 'best_execution', 'position_limits', 'anomaly'
        ]))
        
        logger.info("ComplianceEngine initialized")
    
    async def analyze_trade(
        self,
        trade: TradeRecord,
        expected_price: Optional[float] = None,
        market_bid: Optional[float] = None,
        market_ask: Optional[float] = None
    ) -> List[ComplianceAlert]:
        """Analyze trade for compliance issues"""
        alerts = []
        
        # Wash trading check
        if 'wash_trading' in self.enabled_checks:
            alert = self.wash_trading.analyze_trade(trade)
            if alert:
                alerts.append(alert)
        
        # Best execution check
        if 'best_execution' in self.enabled_checks and expected_price:
            alert = self.best_execution.analyze_execution(
                trade, expected_price, market_bid, market_ask
            )
            if alert:
                alerts.append(alert)
        
        # Anomaly detection
        if 'anomaly' in self.enabled_checks:
            anomaly_alerts = self.anomaly.analyze(trade.symbol, trade.quantity, trade.price)
            alerts.extend(anomaly_alerts)
        
        # Store and notify
        for alert in alerts:
            self._store_alert(alert)
        
        return alerts
    
    def analyze_order(
        self,
        order_id: str,
        symbol: str,
        user_id: str,
        action: str,
        timestamp: Optional[datetime] = None
    ) -> Optional[ComplianceAlert]:
        """Analyze order for compliance issues"""
        timestamp = timestamp or datetime.now()
        
        # Record for spoofing detection
        if 'spoofing' in self.enabled_checks:
            self.spoofing.record_order(order_id, symbol, user_id, action, timestamp)
            
            if action == 'cancelled':
                alert = self.spoofing.analyze(user_id, symbol)
                if alert:
                    self._store_alert(alert)
                    return alert
        
        return None
    
    def check_position_limit(
        self,
        account_id: str,
        symbol: str,
        proposed_value: float
    ) -> Optional[ComplianceAlert]:
        """Check position limits before trade"""
        if 'position_limits' not in self.enabled_checks:
            return None
        
        alert = self.position_limits.check_limits(account_id, symbol, proposed_value)
        if alert:
            self._store_alert(alert)
        
        return alert
    
    def _store_alert(self, alert: ComplianceAlert):
        """Store alert and notify"""
        self.alerts.append(alert)
        
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        if self.on_alert:
            try:
                self.on_alert(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
        
        logger.warning(f"Compliance alert: {alert.violation_type.value} - {alert.description}")
    
    def get_alerts(
        self,
        violation_type: Optional[ComplianceViolationType] = None,
        severity: Optional[ComplianceSeverity] = None,
        symbol: Optional[str] = None,
        unresolved_only: bool = False,
        limit: int = 100
    ) -> List[ComplianceAlert]:
        """Get compliance alerts"""
        alerts = self.alerts
        
        if violation_type:
            alerts = [a for a in alerts if a.violation_type == violation_type]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if symbol:
            alerts = [a for a in alerts if a.symbol == symbol]
        
        if unresolved_only:
            alerts = [a for a in alerts if not a.resolved]
        
        return alerts[-limit:]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False
    
    def resolve_alert(self, alert_id: str, notes: str = "") -> bool:
        """Resolve an alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolution_notes = notes
                return True
        return False
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report"""
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        
        recent_alerts = [a for a in self.alerts if a.timestamp >= day_ago]
        week_alerts = [a for a in self.alerts if a.timestamp >= week_ago]
        
        return {
            'generated_at': now.isoformat(),
            'summary': {
                'total_alerts': len(self.alerts),
                'alerts_24h': len(recent_alerts),
                'alerts_7d': len(week_alerts),
                'unresolved': sum(1 for a in self.alerts if not a.resolved),
                'critical': sum(1 for a in self.alerts if a.severity == ComplianceSeverity.CRITICAL)
            },
            'by_type': {
                vt.value: sum(1 for a in self.alerts if a.violation_type == vt)
                for vt in ComplianceViolationType
            },
            'by_severity': {
                s.value: sum(1 for a in self.alerts if a.severity == s)
                for s in ComplianceSeverity
            }
        }


# Export
__all__ = [
    'ComplianceEngine',
    'ComplianceAlert',
    'ComplianceViolationType',
    'ComplianceSeverity',
    'RegulatoryFramework',
    'TradeRecord',
    'WashTradingDetector',
    'SpoofingDetector',
    'BestExecutionMonitor',
    'PositionLimitMonitor',
    'AnomalyDetector'
]
