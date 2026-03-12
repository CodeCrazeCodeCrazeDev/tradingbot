"""
Trade Surveillance System - Complete Implementation

Comprehensive trade monitoring and surveillance for:
- Market manipulation detection (spoofing, layering, wash trading)
- Unusual trading pattern detection
- Regulatory compliance monitoring
- Real-time alert generation
- Audit trail maintenance
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import json
import hashlib
import statistics

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ManipulationType(Enum):
    """Types of market manipulation."""
    SPOOFING = "spoofing"
    LAYERING = "layering"
    WASH_TRADING = "wash_trading"
    PUMP_AND_DUMP = "pump_and_dump"
    FRONT_RUNNING = "front_running"
    QUOTE_STUFFING = "quote_stuffing"
    MOMENTUM_IGNITION = "momentum_ignition"
    MARKING_THE_CLOSE = "marking_the_close"


class ComplianceRule(Enum):
    """Compliance rules to monitor."""
    MAX_POSITION_SIZE = "max_position_size"
    MAX_ORDER_SIZE = "max_order_size"
    MAX_DAILY_VOLUME = "max_daily_volume"
    CANCEL_RATIO = "cancel_ratio"
    ORDER_TO_TRADE_RATIO = "order_to_trade_ratio"
    PRICE_DEVIATION = "price_deviation"
    CONCENTRATION_LIMIT = "concentration_limit"
    WASH_TRADE_PREVENTION = "wash_trade_prevention"


@dataclass
class Trade:
    """Trade record for surveillance."""
    trade_id: str
    timestamp: datetime
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    order_id: str
    account_id: str
    venue: str
    is_maker: bool = False
    counterparty_id: Optional[str] = None
    
    @property
    def value(self) -> float:
        return self.quantity * self.price


@dataclass
class Order:
    """Order record for surveillance."""
    order_id: str
    timestamp: datetime
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float]
    status: str  # 'new', 'partial', 'filled', 'cancelled'
    account_id: str
    venue: str
    filled_quantity: float = 0
    cancelled_at: Optional[datetime] = None
    
    @property
    def is_cancelled(self) -> bool:
        return self.status == 'cancelled'
    
    @property
    def cancel_time_ms(self) -> Optional[float]:
        if self.cancelled_at:
            return (self.cancelled_at - self.timestamp).total_seconds() * 1000
        return None


@dataclass
class SurveillanceAlert:
    """Surveillance alert."""
    alert_id: str
    timestamp: datetime
    alert_type: str
    severity: AlertSeverity
    symbol: str
    description: str
    evidence: Dict[str, Any]
    account_id: Optional[str] = None
    recommended_action: Optional[str] = None
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'timestamp': self.timestamp.isoformat(),
            'alert_type': self.alert_type,
            'severity': self.severity.value,
            'symbol': self.symbol,
            'description': self.description,
            'evidence': self.evidence,
            'account_id': self.account_id,
            'recommended_action': self.recommended_action,
            'is_acknowledged': self.is_acknowledged
        }


class SpoofingDetector:
    """
    Detects spoofing behavior - placing orders with intent to cancel.
    
    Indicators:
    - High cancel rate (>80%)
    - Quick cancellations (<500ms)
    - Large orders cancelled before execution
    - Pattern of orders on one side cancelled when price moves
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.cancel_threshold = self.config.get('cancel_threshold', 0.8)
        self.quick_cancel_ms = self.config.get('quick_cancel_ms', 500)
        self.min_orders = self.config.get('min_orders', 10)
        self.window_minutes = self.config.get('window_minutes', 5)
        
        # Track orders by account
        self.orders_by_account: Dict[str, deque] = {}
    
    def add_order(self, order: Order):
        """Add order for tracking."""
        if order.account_id not in self.orders_by_account:
            self.orders_by_account[order.account_id] = deque(maxlen=1000)
        self.orders_by_account[order.account_id].append(order)
    
    def detect(self, account_id: str, symbol: Optional[str] = None) -> Optional[SurveillanceAlert]:
        """
        Detect spoofing behavior for an account.
        
        Returns:
            SurveillanceAlert if spoofing detected, None otherwise
        """
        if account_id not in self.orders_by_account:
            return None
        
        orders = list(self.orders_by_account[account_id])
        
        # Filter by symbol if specified
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        
        # Filter by time window
        cutoff = datetime.now() - timedelta(minutes=self.window_minutes)
        orders = [o for o in orders if o.timestamp >= cutoff]
        
        if len(orders) < self.min_orders:
            return None
        
        # Calculate metrics
        cancelled = [o for o in orders if o.is_cancelled]
        cancel_rate = len(cancelled) / len(orders)
        
        # Check quick cancellations
        quick_cancels = [o for o in cancelled if o.cancel_time_ms and o.cancel_time_ms < self.quick_cancel_ms]
        quick_cancel_rate = len(quick_cancels) / len(orders) if orders else 0
        
        # Calculate average cancelled order size vs filled
        avg_cancelled_size = statistics.mean([o.quantity for o in cancelled]) if cancelled else 0
        filled = [o for o in orders if o.status == 'filled']
        avg_filled_size = statistics.mean([o.quantity for o in filled]) if filled else 0
        
        # Detect spoofing
        is_spoofing = False
        evidence = {
            'cancel_rate': cancel_rate,
            'quick_cancel_rate': quick_cancel_rate,
            'avg_cancelled_size': avg_cancelled_size,
            'avg_filled_size': avg_filled_size,
            'total_orders': len(orders),
            'cancelled_orders': len(cancelled),
            'quick_cancels': len(quick_cancels)
        }
        
        if cancel_rate > self.cancel_threshold:
            is_spoofing = True
            evidence['trigger'] = 'high_cancel_rate'
        
        if quick_cancel_rate > 0.5:
            is_spoofing = True
            evidence['trigger'] = 'quick_cancellations'
        
        if avg_cancelled_size > avg_filled_size * 3 and cancelled:
            is_spoofing = True
            evidence['trigger'] = 'large_cancelled_orders'
        
        if is_spoofing:
            return SurveillanceAlert(
                alert_id=f"SPOOF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{account_id[:8]}",
                timestamp=datetime.now(),
                alert_type=ManipulationType.SPOOFING.value,
                severity=AlertSeverity.HIGH,
                symbol=symbol or 'MULTIPLE',
                description=f"Potential spoofing detected: {cancel_rate:.1%} cancel rate, {len(quick_cancels)} quick cancels",
                evidence=evidence,
                account_id=account_id,
                recommended_action="Review trading activity and consider temporary suspension"
            )
        
        return None


class WashTradingDetector:
    """
    Detects wash trading - trading with oneself to create artificial volume.
    
    Indicators:
    - Same account on both sides of trade
    - Trades between related accounts
    - Trades that result in no change in beneficial ownership
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.related_accounts: Dict[str, Set[str]] = {}  # account -> related accounts
        self.trades: deque = deque(maxlen=10000)
        self.window_minutes = self.config.get('window_minutes', 60)
    
    def add_related_accounts(self, account_id: str, related: List[str]):
        """Register related accounts."""
        if account_id not in self.related_accounts:
            self.related_accounts[account_id] = set()
        self.related_accounts[account_id].update(related)
    
    def add_trade(self, trade: Trade):
        """Add trade for analysis."""
        self.trades.append(trade)
    
    def detect(self, symbol: Optional[str] = None) -> List[SurveillanceAlert]:
        """
        Detect wash trading patterns.
        
        Returns:
            List of SurveillanceAlerts for detected wash trades
        """
        alerts = []
        cutoff = datetime.now() - timedelta(minutes=self.window_minutes)
        
        trades = [t for t in self.trades if t.timestamp >= cutoff]
        if symbol:
            trades = [t for t in trades if t.symbol == symbol]
        
        # Group trades by symbol and time window
        trade_pairs: Dict[str, List[Trade]] = {}
        for trade in trades:
            key = f"{trade.symbol}_{trade.timestamp.strftime('%Y%m%d%H%M')}"
            if key not in trade_pairs:
                trade_pairs[key] = []
            trade_pairs[key].append(trade)
        
        # Check for wash trading patterns
        for key, group in trade_pairs.items():
            buys = [t for t in group if t.side == 'buy']
            sells = [t for t in group if t.side == 'sell']
            
            for buy in buys:
                for sell in sells:
                    # Check if same account
                    if buy.account_id == sell.account_id:
                        alerts.append(self._create_wash_alert(buy, sell, "same_account"))
                        continue
                    
                    # Check if related accounts
                    if buy.account_id in self.related_accounts:
                        if sell.account_id in self.related_accounts[buy.account_id]:
                            alerts.append(self._create_wash_alert(buy, sell, "related_accounts"))
                            continue
                    
                    # Check if counterparty matches
                    if buy.counterparty_id == sell.account_id or sell.counterparty_id == buy.account_id:
                        # Same quantity and price is suspicious
                        if abs(buy.quantity - sell.quantity) < 0.01 and abs(buy.price - sell.price) < 0.01:
                            alerts.append(self._create_wash_alert(buy, sell, "matching_counterparty"))
        
        return alerts
    
    def _create_wash_alert(self, buy: Trade, sell: Trade, trigger: str) -> SurveillanceAlert:
        """Create wash trading alert."""
        return SurveillanceAlert(
            alert_id=f"WASH-{datetime.now().strftime('%Y%m%d%H%M%S')}-{buy.trade_id[:8]}",
            timestamp=datetime.now(),
            alert_type=ManipulationType.WASH_TRADING.value,
            severity=AlertSeverity.CRITICAL,
            symbol=buy.symbol,
            description=f"Potential wash trade detected: {trigger}",
            evidence={
                'trigger': trigger,
                'buy_trade_id': buy.trade_id,
                'sell_trade_id': sell.trade_id,
                'buy_account': buy.account_id,
                'sell_account': sell.account_id,
                'quantity': buy.quantity,
                'price': buy.price,
                'value': buy.value
            },
            account_id=buy.account_id,
            recommended_action="Immediate investigation required - potential regulatory violation"
        )


class LayeringDetector:
    """
    Detects layering - placing multiple orders at different price levels to create false impression.
    
    Indicators:
    - Multiple orders at successive price levels
    - Orders cancelled in sequence as price moves
    - Asymmetric order book manipulation
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_layers = self.config.get('min_layers', 3)
        self.price_step_pct = self.config.get('price_step_pct', 0.1)
        self.orders: deque = deque(maxlen=5000)
    
    def add_order(self, order: Order):
        """Add order for analysis."""
        self.orders.append(order)
    
    def detect(self, account_id: str, symbol: str) -> Optional[SurveillanceAlert]:
        """
        Detect layering behavior.
        
        Returns:
            SurveillanceAlert if layering detected
        """
        cutoff = datetime.now() - timedelta(minutes=5)
        
        # Get recent orders for this account and symbol
        orders = [o for o in self.orders 
                  if o.account_id == account_id 
                  and o.symbol == symbol 
                  and o.timestamp >= cutoff
                  and o.price is not None]
        
        if len(orders) < self.min_layers:
            return None
        
        # Group by side
        buy_orders = sorted([o for o in orders if o.side == 'buy'], key=lambda x: x.price, reverse=True)
        sell_orders = sorted([o for o in orders if o.side == 'sell'], key=lambda x: x.price)
        
        # Check for layering pattern
        for side_orders, side in [(buy_orders, 'buy'), (sell_orders, 'sell')]:
            if len(side_orders) >= self.min_layers:
                # Check if orders form layers
                prices = [o.price for o in side_orders]
                
                # Calculate price steps
                steps = []
                for i in range(1, len(prices)):
                    step_pct = abs(prices[i] - prices[i-1]) / prices[i-1] * 100
                    steps.append(step_pct)
                
                # Check if steps are consistent (layering pattern)
                if steps and all(abs(s - steps[0]) < 0.05 for s in steps):
                    # Check cancel rate for these orders
                    cancelled = [o for o in side_orders if o.is_cancelled]
                    cancel_rate = len(cancelled) / len(side_orders)
                    
                    if cancel_rate > 0.7:
                        return SurveillanceAlert(
                            alert_id=f"LAYER-{datetime.now().strftime('%Y%m%d%H%M%S')}-{account_id[:8]}",
                            timestamp=datetime.now(),
                            alert_type=ManipulationType.LAYERING.value,
                            severity=AlertSeverity.HIGH,
                            symbol=symbol,
                            description=f"Potential layering detected: {len(side_orders)} {side} orders at consistent price steps",
                            evidence={
                                'side': side,
                                'num_layers': len(side_orders),
                                'price_step_pct': statistics.mean(steps) if steps else 0,
                                'cancel_rate': cancel_rate,
                                'prices': prices[:5]  # First 5 prices
                            },
                            account_id=account_id,
                            recommended_action="Review order placement pattern"
                        )
        
        return None


class ComplianceMonitor:
    """
    Monitors compliance with trading rules and limits.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Default limits
        self.limits = {
            ComplianceRule.MAX_POSITION_SIZE: self.config.get('max_position_size', 1000000),
            ComplianceRule.MAX_ORDER_SIZE: self.config.get('max_order_size', 100000),
            ComplianceRule.MAX_DAILY_VOLUME: self.config.get('max_daily_volume', 5000000),
            ComplianceRule.CANCEL_RATIO: self.config.get('max_cancel_ratio', 0.9),
            ComplianceRule.ORDER_TO_TRADE_RATIO: self.config.get('max_otr', 10),
            ComplianceRule.PRICE_DEVIATION: self.config.get('max_price_deviation', 0.05),
            ComplianceRule.CONCENTRATION_LIMIT: self.config.get('concentration_limit', 0.25),
        }
        
        # Tracking
        self.daily_volume: Dict[str, float] = {}  # account -> volume
        self.positions: Dict[str, Dict[str, float]] = {}  # account -> symbol -> position
        self.order_counts: Dict[str, int] = {}
        self.trade_counts: Dict[str, int] = {}
        self.cancel_counts: Dict[str, int] = {}
    
    def check_order(self, order: Order, current_price: float) -> List[SurveillanceAlert]:
        """
        Check order against compliance rules.
        
        Returns:
            List of compliance alerts
        """
        alerts = []
        
        # Check order size
        order_value = order.quantity * (order.price or current_price)
        if order_value > self.limits[ComplianceRule.MAX_ORDER_SIZE]:
            alerts.append(SurveillanceAlert(
                alert_id=f"COMP-{datetime.now().strftime('%Y%m%d%H%M%S')}-SIZE",
                timestamp=datetime.now(),
                alert_type=ComplianceRule.MAX_ORDER_SIZE.value,
                severity=AlertSeverity.MEDIUM,
                symbol=order.symbol,
                description=f"Order size ${order_value:,.2f} exceeds limit ${self.limits[ComplianceRule.MAX_ORDER_SIZE]:,.2f}",
                evidence={'order_value': order_value, 'limit': self.limits[ComplianceRule.MAX_ORDER_SIZE]},
                account_id=order.account_id,
                recommended_action="Reduce order size or obtain approval"
            ))
        
        # Check price deviation
        if order.price:
            deviation = abs(order.price - current_price) / current_price
            if deviation > self.limits[ComplianceRule.PRICE_DEVIATION]:
                alerts.append(SurveillanceAlert(
                    alert_id=f"COMP-{datetime.now().strftime('%Y%m%d%H%M%S')}-PRICE",
                    timestamp=datetime.now(),
                    alert_type=ComplianceRule.PRICE_DEVIATION.value,
                    severity=AlertSeverity.LOW,
                    symbol=order.symbol,
                    description=f"Order price ${order.price:.4f} deviates {deviation:.1%} from market ${current_price:.4f}",
                    evidence={'order_price': order.price, 'market_price': current_price, 'deviation': deviation},
                    account_id=order.account_id,
                    recommended_action="Verify intended price"
                ))
        
        # Track order
        self.order_counts[order.account_id] = self.order_counts.get(order.account_id, 0) + 1
        
        return alerts
    
    def check_trade(self, trade: Trade) -> List[SurveillanceAlert]:
        """
        Check trade against compliance rules.
        
        Returns:
            List of compliance alerts
        """
        alerts = []
        
        # Update daily volume
        self.daily_volume[trade.account_id] = self.daily_volume.get(trade.account_id, 0) + trade.value
        
        # Check daily volume limit
        if self.daily_volume[trade.account_id] > self.limits[ComplianceRule.MAX_DAILY_VOLUME]:
            alerts.append(SurveillanceAlert(
                alert_id=f"COMP-{datetime.now().strftime('%Y%m%d%H%M%S')}-VOL",
                timestamp=datetime.now(),
                alert_type=ComplianceRule.MAX_DAILY_VOLUME.value,
                severity=AlertSeverity.HIGH,
                symbol=trade.symbol,
                description=f"Daily volume ${self.daily_volume[trade.account_id]:,.2f} exceeds limit",
                evidence={'daily_volume': self.daily_volume[trade.account_id], 'limit': self.limits[ComplianceRule.MAX_DAILY_VOLUME]},
                account_id=trade.account_id,
                recommended_action="Halt trading for the day"
            ))
        
        # Update position
        if trade.account_id not in self.positions:
            self.positions[trade.account_id] = {}
        
        current_pos = self.positions[trade.account_id].get(trade.symbol, 0)
        if trade.side == 'buy':
            new_pos = current_pos + trade.quantity
        else:
            new_pos = current_pos - trade.quantity
        self.positions[trade.account_id][trade.symbol] = new_pos
        
        # Check position size
        position_value = abs(new_pos * trade.price)
        if position_value > self.limits[ComplianceRule.MAX_POSITION_SIZE]:
            alerts.append(SurveillanceAlert(
                alert_id=f"COMP-{datetime.now().strftime('%Y%m%d%H%M%S')}-POS",
                timestamp=datetime.now(),
                alert_type=ComplianceRule.MAX_POSITION_SIZE.value,
                severity=AlertSeverity.HIGH,
                symbol=trade.symbol,
                description=f"Position value ${position_value:,.2f} exceeds limit",
                evidence={'position_value': position_value, 'position_qty': new_pos, 'limit': self.limits[ComplianceRule.MAX_POSITION_SIZE]},
                account_id=trade.account_id,
                recommended_action="Reduce position size"
            ))
        
        # Track trade
        self.trade_counts[trade.account_id] = self.trade_counts.get(trade.account_id, 0) + 1
        
        return alerts
    
    def check_cancel(self, order: Order) -> List[SurveillanceAlert]:
        """Check cancel against compliance rules."""
        alerts = []
        
        self.cancel_counts[order.account_id] = self.cancel_counts.get(order.account_id, 0) + 1
        
        # Check cancel ratio
        total_orders = self.order_counts.get(order.account_id, 1)
        cancel_ratio = self.cancel_counts[order.account_id] / total_orders
        
        if cancel_ratio > self.limits[ComplianceRule.CANCEL_RATIO]:
            alerts.append(SurveillanceAlert(
                alert_id=f"COMP-{datetime.now().strftime('%Y%m%d%H%M%S')}-CANCEL",
                timestamp=datetime.now(),
                alert_type=ComplianceRule.CANCEL_RATIO.value,
                severity=AlertSeverity.MEDIUM,
                symbol=order.symbol,
                description=f"Cancel ratio {cancel_ratio:.1%} exceeds limit {self.limits[ComplianceRule.CANCEL_RATIO]:.1%}",
                evidence={'cancel_ratio': cancel_ratio, 'cancels': self.cancel_counts[order.account_id], 'orders': total_orders},
                account_id=order.account_id,
                recommended_action="Review order management practices"
            ))
        
        # Check order-to-trade ratio
        trades = self.trade_counts.get(order.account_id, 1)
        otr = total_orders / trades if trades > 0 else total_orders
        
        if otr > self.limits[ComplianceRule.ORDER_TO_TRADE_RATIO]:
            alerts.append(SurveillanceAlert(
                alert_id=f"COMP-{datetime.now().strftime('%Y%m%d%H%M%S')}-OTR",
                timestamp=datetime.now(),
                alert_type=ComplianceRule.ORDER_TO_TRADE_RATIO.value,
                severity=AlertSeverity.MEDIUM,
                symbol=order.symbol,
                description=f"Order-to-trade ratio {otr:.1f} exceeds limit {self.limits[ComplianceRule.ORDER_TO_TRADE_RATIO]}",
                evidence={'otr': otr, 'orders': total_orders, 'trades': trades},
                account_id=order.account_id,
                recommended_action="Review order submission strategy"
            ))
        
        return alerts
    
    def reset_daily(self):
        """Reset daily counters."""
        self.daily_volume.clear()
        self.order_counts.clear()
        self.trade_counts.clear()
        self.cancel_counts.clear()


class TradeSurveillanceSystem:
    """
    Complete trade surveillance system integrating all detectors.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize detectors
        self.spoofing_detector = SpoofingDetector(config)
        self.wash_trading_detector = WashTradingDetector(config)
        self.layering_detector = LayeringDetector(config)
        self.compliance_monitor = ComplianceMonitor(config)
        
        # Alert storage
        self.alerts: List[SurveillanceAlert] = []
        self.alert_callbacks: List[callable] = []
        
        # Audit trail
        self.audit_log: List[Dict[str, Any]] = []
        
        logger.info("TradeSurveillanceSystem initialized")
    
    def register_alert_callback(self, callback: callable):
        """Register callback for new alerts."""
        self.alert_callbacks.append(callback)
    
    def _emit_alert(self, alert: SurveillanceAlert):
        """Emit alert to all registered callbacks."""
        self.alerts.append(alert)
        
        # Log to audit trail
        self.audit_log.append({
            'timestamp': datetime.now().isoformat(),
            'event': 'alert_generated',
            'alert': alert.to_dict()
        })
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
        
        logger.warning(f"SURVEILLANCE ALERT: {alert.alert_type} - {alert.description}")
    
    def process_order(self, order: Order, current_price: float):
        """
        Process new order through surveillance.
        
        Args:
            order: Order to process
            current_price: Current market price
        """
        # Log to audit trail
        self.audit_log.append({
            'timestamp': datetime.now().isoformat(),
            'event': 'order_received',
            'order_id': order.order_id,
            'symbol': order.symbol,
            'side': order.side,
            'quantity': order.quantity,
            'price': order.price
        })
        
        # Add to detectors
        self.spoofing_detector.add_order(order)
        self.layering_detector.add_order(order)
        
        # Check compliance
        alerts = self.compliance_monitor.check_order(order, current_price)
        for alert in alerts:
            self._emit_alert(alert)
    
    def process_trade(self, trade: Trade):
        """
        Process executed trade through surveillance.
        
        Args:
            trade: Trade to process
        """
        # Log to audit trail
        self.audit_log.append({
            'timestamp': datetime.now().isoformat(),
            'event': 'trade_executed',
            'trade_id': trade.trade_id,
            'symbol': trade.symbol,
            'side': trade.side,
            'quantity': trade.quantity,
            'price': trade.price,
            'value': trade.value
        })
        
        # Add to detectors
        self.wash_trading_detector.add_trade(trade)
        
        # Check compliance
        alerts = self.compliance_monitor.check_trade(trade)
        for alert in alerts:
            self._emit_alert(alert)
        
        # Check wash trading
        wash_alerts = self.wash_trading_detector.detect(trade.symbol)
        for alert in wash_alerts:
            self._emit_alert(alert)
    
    def process_cancel(self, order: Order):
        """
        Process order cancellation through surveillance.
        
        Args:
            order: Cancelled order
        """
        order.status = 'cancelled'
        order.cancelled_at = datetime.now()
        
        # Log to audit trail
        self.audit_log.append({
            'timestamp': datetime.now().isoformat(),
            'event': 'order_cancelled',
            'order_id': order.order_id,
            'symbol': order.symbol,
            'cancel_time_ms': order.cancel_time_ms
        })
        
        # Check compliance
        alerts = self.compliance_monitor.check_cancel(order)
        for alert in alerts:
            self._emit_alert(alert)
        
        # Check spoofing
        spoof_alert = self.spoofing_detector.detect(order.account_id, order.symbol)
        if spoof_alert:
            self._emit_alert(spoof_alert)
        
        # Check layering
        layer_alert = self.layering_detector.detect(order.account_id, order.symbol)
        if layer_alert:
            self._emit_alert(layer_alert)
    
    def run_periodic_checks(self):
        """Run periodic surveillance checks."""
        # Check all accounts for spoofing
        for account_id in self.spoofing_detector.orders_by_account.keys():
            alert = self.spoofing_detector.detect(account_id)
            if alert:
                self._emit_alert(alert)
        
        # Check wash trading
        wash_alerts = self.wash_trading_detector.detect()
        for alert in wash_alerts:
            self._emit_alert(alert)
    
    def acknowledge_alert(self, alert_id: str, user: str, notes: Optional[str] = None):
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.is_acknowledged = True
                alert.acknowledged_by = user
                alert.acknowledged_at = datetime.now()
                
                self.audit_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'event': 'alert_acknowledged',
                    'alert_id': alert_id,
                    'user': user,
                    'notes': notes
                })
                
                logger.info(f"Alert {alert_id} acknowledged by {user}")
                return True
        return False
    
    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        alert_type: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        since: Optional[datetime] = None
    ) -> List[SurveillanceAlert]:
        """Get filtered alerts."""
        alerts = self.alerts
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.is_acknowledged == acknowledged]
        if since:
            alerts = [a for a in alerts if a.timestamp >= since]
        
        return alerts
    
    def get_audit_log(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get audit log entries."""
        if since:
            return [e for e in self.audit_log if datetime.fromisoformat(e['timestamp']) >= since]
        return self.audit_log
    
    def get_status(self) -> Dict[str, Any]:
        """Get surveillance system status."""
        return {
            'total_alerts': len(self.alerts),
            'unacknowledged_alerts': len([a for a in self.alerts if not a.is_acknowledged]),
            'critical_alerts': len([a for a in self.alerts if a.severity == AlertSeverity.CRITICAL]),
            'audit_log_entries': len(self.audit_log),
            'accounts_monitored': len(self.spoofing_detector.orders_by_account),
            'timestamp': datetime.now().isoformat()
        }
    
    def reset_daily(self):
        """Reset daily counters."""
        self.compliance_monitor.reset_daily()
        logger.info("Daily surveillance counters reset")


# Factory function
def create_surveillance_system(config: Optional[Dict] = None) -> TradeSurveillanceSystem:
    """Create and return a TradeSurveillanceSystem instance."""
    return TradeSurveillanceSystem(config)


# Example usage
if __name__ == "__main__":
    import uuid
    
    # Create surveillance system
    surveillance = create_surveillance_system({
        'max_position_size': 500000,
        'max_order_size': 50000,
        'cancel_threshold': 0.7
    })
    
    # Register alert callback
    def alert_handler(alert: SurveillanceAlert):
        print(f"🚨 ALERT: {alert.severity.value.upper()} - {alert.description}")
    
    surveillance.register_alert_callback(alert_handler)
    
    # Simulate some trading activity
    account = "ACC-001"
    
    # Create some orders
    for i in range(15):
        order = Order(
            order_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            symbol="AAPL",
            side="buy",
            order_type="limit",
            quantity=100,
            price=150.0 + i * 0.1,
            status="new",
            account_id=account,
            venue="NYSE"
        )
        surveillance.process_order(order, current_price=150.0)
        
        # Cancel most orders (simulate spoofing)
        if i < 12:
            surveillance.process_cancel(order)
    
    # Create a trade
    trade = Trade(
        trade_id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        symbol="AAPL",
        side="buy",
        quantity=100,
        price=150.0,
        order_id=str(uuid.uuid4()),
        account_id=account,
        venue="NYSE"
    )
    surveillance.process_trade(trade)
    
    # Run periodic checks
    surveillance.run_periodic_checks()
    
    # Print status
    print("\n" + "=" * 60)
    print("SURVEILLANCE STATUS")
    print("=" * 60)
    status = surveillance.get_status()
    for key, value in status.items():
        print(f"{key}: {value}")
    
    # Print alerts
    print("\n" + "=" * 60)
    print("ALERTS")
    print("=" * 60)
    for alert in surveillance.get_alerts():
        print(f"\n{alert.alert_type} ({alert.severity.value})")
        print(f"  {alert.description}")
        print(f"  Evidence: {alert.evidence}")
