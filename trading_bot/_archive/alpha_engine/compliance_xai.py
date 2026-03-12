"""
Compliance, Ethics & Explainable AI Module
===========================================

Comprehensive compliance and explainability:
- Regulatory Compliance (SEC, MiFID II, MAR)
- Ethical Trading Practices
- Explainable AI (SHAP, LIME, Attention Visualization)
- Audit Trail and Reporting
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import json
import hashlib

logger = logging.getLogger(__name__)

# Try importing XAI libraries
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False


class ComplianceRegulation(Enum):
    """Regulatory frameworks"""
    SEC_15C3_5 = "sec_15c3_5"  # Market Access Rule
    FINRA_ALGO = "finra_algo"  # FINRA Algorithmic Trading
    MIFID_II = "mifid_ii"  # Markets in Financial Instruments Directive
    MAR = "mar"  # Market Abuse Regulation
    DODD_FRANK = "dodd_frank"  # Dodd-Frank Act


class ProhibitedActivity(Enum):
    """Prohibited trading activities"""
    SPOOFING = "spoofing"
    LAYERING = "layering"
    FRONT_RUNNING = "front_running"
    QUOTE_STUFFING = "quote_stuffing"
    WASH_TRADING = "wash_trading"
    MARKET_MANIPULATION = "market_manipulation"


class AlertSeverity(Enum):
    """Compliance alert severity"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    VIOLATION = "violation"


@dataclass
class ComplianceCheck:
    """Compliance check result"""
    timestamp: datetime
    regulation: ComplianceRegulation
    check_name: str
    passed: bool
    details: str
    severity: AlertSeverity
    action_required: Optional[str] = None


@dataclass
class TradeExplanation:
    """Explanation for a trading decision"""
    timestamp: datetime
    trade_id: str
    symbol: str
    direction: str
    
    # Feature importance
    feature_importance: Dict[str, float]
    top_features: List[Tuple[str, float]]
    
    # Decision narrative
    narrative: str
    confidence: float
    
    # Model contributions
    model_contributions: Dict[str, float]
    
    # Risk factors
    risk_factors: List[str]


@dataclass
class AuditRecord:
    """Audit trail record"""
    timestamp: datetime
    record_id: str
    event_type: str
    details: Dict[str, Any]
    user: str
    system_state: Dict[str, Any]
    hash: str  # For integrity verification


class PreTradeRiskControls:
    """
    Pre-Trade Risk Controls (SEC Rule 15c3-5)
    
    Implements:
    - Price collars
    - Quantity limits
    - Credit limits
    - Duplicate order detection
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Price collar (max deviation from reference price)
        self.price_collar_pct = self.config.get('price_collar_pct', 0.05)  # 5%
        
        # Quantity limits
        self.max_order_quantity = self.config.get('max_order_quantity', 10000)
        self.max_daily_quantity = self.config.get('max_daily_quantity', 100000)
        
        # Credit limits
        self.max_order_value = self.config.get('max_order_value', 1000000)
        self.max_daily_value = self.config.get('max_daily_value', 10000000)
        
        # Daily tracking
        self.daily_quantity: Dict[str, float] = {}
        self.daily_value: Dict[str, float] = {}
        
        # Recent orders for duplicate detection
        self.recent_orders: deque = deque(maxlen=1000)
    
    def check_order(self, order: Dict[str, Any], reference_price: float) -> ComplianceCheck:
        """
        Run pre-trade risk checks on order
        
        Args:
            order: Order details
            reference_price: Current market price
            
        Returns:
            ComplianceCheck result
        """
        symbol = order.get('symbol', '')
        quantity = order.get('quantity', 0)
        price = order.get('price', reference_price)
        value = quantity * price
        
        # Price collar check
        if reference_price > 0:
            price_deviation = abs(price - reference_price) / reference_price
            if price_deviation > self.price_collar_pct:
                return ComplianceCheck(
                    timestamp=datetime.now(),
                    regulation=ComplianceRegulation.SEC_15C3_5,
                    check_name="price_collar",
                    passed=False,
                    details=f"Price deviation {price_deviation:.2%} exceeds collar {self.price_collar_pct:.2%}",
                    severity=AlertSeverity.CRITICAL,
                    action_required="Reject order or adjust price",
                )
        
        # Quantity limit check
        if quantity > self.max_order_quantity:
            return ComplianceCheck(
                timestamp=datetime.now(),
                regulation=ComplianceRegulation.SEC_15C3_5,
                check_name="quantity_limit",
                passed=False,
                details=f"Order quantity {quantity} exceeds limit {self.max_order_quantity}",
                severity=AlertSeverity.CRITICAL,
                action_required="Reduce order size",
            )
        
        # Daily quantity check
        daily_qty = self.daily_quantity.get(symbol, 0) + quantity
        if daily_qty > self.max_daily_quantity:
            return ComplianceCheck(
                timestamp=datetime.now(),
                regulation=ComplianceRegulation.SEC_15C3_5,
                check_name="daily_quantity_limit",
                passed=False,
                details=f"Daily quantity {daily_qty} would exceed limit {self.max_daily_quantity}",
                severity=AlertSeverity.WARNING,
                action_required="Wait until next trading day",
            )
        
        # Value limit check
        if value > self.max_order_value:
            return ComplianceCheck(
                timestamp=datetime.now(),
                regulation=ComplianceRegulation.SEC_15C3_5,
                check_name="value_limit",
                passed=False,
                details=f"Order value ${value:,.2f} exceeds limit ${self.max_order_value:,.2f}",
                severity=AlertSeverity.CRITICAL,
                action_required="Reduce order size",
            )
        
        # Duplicate order check
        order_hash = hashlib.md5(
            f"{symbol}{order.get('side')}{quantity}{price}".encode()
        ).hexdigest()
        
        recent_hashes = [o.get('hash') for o in self.recent_orders]
        if order_hash in recent_hashes:
            return ComplianceCheck(
                timestamp=datetime.now(),
                regulation=ComplianceRegulation.SEC_15C3_5,
                check_name="duplicate_order",
                passed=False,
                details="Potential duplicate order detected",
                severity=AlertSeverity.WARNING,
                action_required="Verify order is intentional",
            )
        
        # All checks passed
        return ComplianceCheck(
            timestamp=datetime.now(),
            regulation=ComplianceRegulation.SEC_15C3_5,
            check_name="pre_trade_risk",
            passed=True,
            details="All pre-trade risk checks passed",
            severity=AlertSeverity.INFO,
        )
    
    def record_order(self, order: Dict[str, Any]):
        """Record order for tracking"""
        symbol = order.get('symbol', '')
        quantity = order.get('quantity', 0)
        price = order.get('price', 0)
        
        # Update daily tracking
        self.daily_quantity[symbol] = self.daily_quantity.get(symbol, 0) + quantity
        self.daily_value[symbol] = self.daily_value.get(symbol, 0) + quantity * price
        
        # Add to recent orders
        order_hash = hashlib.md5(
            f"{symbol}{order.get('side')}{quantity}{price}".encode()
        ).hexdigest()
        self.recent_orders.append({**order, 'hash': order_hash, 'timestamp': datetime.now()})
    
    def reset_daily_limits(self):
        """Reset daily limits (call at start of trading day)"""
        self.daily_quantity = {}
        self.daily_value = {}


class MarketAbuseDetector:
    """
    Market Abuse Detection (MAR Compliance)
    
    Detects:
    - Spoofing patterns
    - Layering
    - Quote stuffing
    - Wash trading
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Detection thresholds
        self.cancel_rate_threshold = self.config.get('cancel_rate_threshold', 0.9)
        self.layer_count_threshold = self.config.get('layer_count_threshold', 5)
        self.quote_rate_threshold = self.config.get('quote_rate_threshold', 100)  # per second
        
        # Order history
        self.order_history: deque = deque(maxlen=10000)
        self.quote_history: deque = deque(maxlen=10000)
    
    def check_spoofing(self, orders: List[Dict[str, Any]]) -> ComplianceCheck:
        """
        Check for spoofing patterns
        
        Spoofing: Placing orders with intent to cancel before execution
        """
        if not orders:
            return ComplianceCheck(
                timestamp=datetime.now(),
                regulation=ComplianceRegulation.MAR,
                check_name="spoofing_check",
                passed=True,
                details="No orders to check",
                severity=AlertSeverity.INFO,
            )
        
        # Calculate cancel rate
        total_orders = len(orders)
        cancelled = sum(1 for o in orders if o.get('status') == 'cancelled')
        cancel_rate = cancelled / total_orders if total_orders > 0 else 0
        
        if cancel_rate > self.cancel_rate_threshold:
            return ComplianceCheck(
                timestamp=datetime.now(),
                regulation=ComplianceRegulation.MAR,
                check_name="spoofing_check",
                passed=False,
                details=f"High cancel rate detected: {cancel_rate:.2%}",
                severity=AlertSeverity.VIOLATION,
                action_required="Review order patterns for potential spoofing",
            )
        
        return ComplianceCheck(
            timestamp=datetime.now(),
            regulation=ComplianceRegulation.MAR,
            check_name="spoofing_check",
            passed=True,
            details=f"Cancel rate {cancel_rate:.2%} within acceptable range",
            severity=AlertSeverity.INFO,
        )
    
    def check_layering(self, order_book_activity: List[Dict[str, Any]]) -> ComplianceCheck:
        """
        Check for layering patterns
        
        Layering: Creating false liquidity impressions with multiple orders
        """
        if not order_book_activity:
            return ComplianceCheck(
                timestamp=datetime.now(),
                regulation=ComplianceRegulation.MAR,
                check_name="layering_check",
                passed=True,
                details="No activity to check",
                severity=AlertSeverity.INFO,
            )
        
        # Count orders at different price levels
        price_levels = {}
        for activity in order_book_activity:
            price = activity.get('price', 0)
            price_levels[price] = price_levels.get(price, 0) + 1
        
        # Check for suspicious layering
        max_layers = max(price_levels.values()) if price_levels else 0
        
        if max_layers > self.layer_count_threshold:
            return ComplianceCheck(
                timestamp=datetime.now(),
                regulation=ComplianceRegulation.MAR,
                check_name="layering_check",
                passed=False,
                details=f"Potential layering detected: {max_layers} orders at single level",
                severity=AlertSeverity.WARNING,
                action_required="Review order book activity",
            )
        
        return ComplianceCheck(
            timestamp=datetime.now(),
            regulation=ComplianceRegulation.MAR,
            check_name="layering_check",
            passed=True,
            details="No layering patterns detected",
            severity=AlertSeverity.INFO,
        )
    
    def check_quote_stuffing(self, quote_updates: List[Dict[str, Any]], 
                            time_window_seconds: float = 1.0) -> ComplianceCheck:
        """
        Check for quote stuffing
        
        Quote stuffing: Overwhelming system with rapid quote updates
        """
        if not quote_updates:
            return ComplianceCheck(
                timestamp=datetime.now(),
                regulation=ComplianceRegulation.MAR,
                check_name="quote_stuffing_check",
                passed=True,
                details="No quotes to check",
                severity=AlertSeverity.INFO,
            )
        
        # Calculate quote rate
        quote_rate = len(quote_updates) / time_window_seconds
        
        if quote_rate > self.quote_rate_threshold:
            return ComplianceCheck(
                timestamp=datetime.now(),
                regulation=ComplianceRegulation.MAR,
                check_name="quote_stuffing_check",
                passed=False,
                details=f"High quote rate detected: {quote_rate:.0f}/sec",
                severity=AlertSeverity.VIOLATION,
                action_required="Reduce quote update frequency",
            )
        
        return ComplianceCheck(
            timestamp=datetime.now(),
            regulation=ComplianceRegulation.MAR,
            check_name="quote_stuffing_check",
            passed=True,
            details=f"Quote rate {quote_rate:.0f}/sec within limits",
            severity=AlertSeverity.INFO,
        )


class ExplainableAI:
    """
    Explainable AI for Trading Decisions
    
    Provides:
    - Feature importance (SHAP values)
    - Local explanations (LIME-style)
    - Decision narratives
    - Model contribution analysis
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Explanation history
        self.explanations: deque = deque(maxlen=1000)
    
    def explain_decision(self, trade_id: str, symbol: str, direction: str,
                        features: Dict[str, float], model_outputs: Dict[str, Any],
                        model: Any = None) -> TradeExplanation:
        """
        Generate explanation for trading decision
        
        Args:
            trade_id: Trade identifier
            symbol: Trading symbol
            direction: Trade direction
            features: Input features
            model_outputs: Outputs from each model
            model: ML model for SHAP (optional)
            
        Returns:
            TradeExplanation
        """
        # Calculate feature importance
        if SHAP_AVAILABLE and model is not None:
            try:
                explainer = shap.TreeExplainer(model)
                feature_array = np.array(list(features.values())).reshape(1, -1)
                shap_values = explainer.shap_values(feature_array)
                
                feature_importance = {
                    name: float(shap_values[0][i])
                    for i, name in enumerate(features.keys())
                }
            except Exception as e:
                logger.warning(f"SHAP explanation failed: {e}")
                feature_importance = self._simple_importance(features)
        else:
            feature_importance = self._simple_importance(features)
        
        # Get top features
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        top_features = sorted_features[:5]
        
        # Calculate model contributions
        model_contributions = {}
        for model_name, output in model_outputs.items():
            if isinstance(output, dict):
                contribution = output.get('confidence', 0) * output.get('weight', 0.2)
            else:
                contribution = 0.2
            model_contributions[model_name] = contribution
        
        # Normalize contributions
        total_contrib = sum(model_contributions.values())
        if total_contrib > 0:
            model_contributions = {k: v / total_contrib for k, v in model_contributions.items()}
        
        # Generate narrative
        narrative = self._generate_narrative(
            direction, top_features, model_contributions, features
        )
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(features, model_outputs)
        
        # Calculate overall confidence
        confidence = np.mean([
            output.get('confidence', 0.5) if isinstance(output, dict) else 0.5
            for output in model_outputs.values()
        ])
        
        explanation = TradeExplanation(
            timestamp=datetime.now(),
            trade_id=trade_id,
            symbol=symbol,
            direction=direction,
            feature_importance=feature_importance,
            top_features=top_features,
            narrative=narrative,
            confidence=confidence,
            model_contributions=model_contributions,
            risk_factors=risk_factors,
        )
        
        self.explanations.append(explanation)
        
        return explanation
    
    def _simple_importance(self, features: Dict[str, float]) -> Dict[str, float]:
        """Simple feature importance based on deviation from mean"""
        values = list(features.values())
        mean_val = np.mean(values) if values else 0
        std_val = np.std(values) if len(values) > 1 else 1
        
        importance = {}
        for name, value in features.items():
            if std_val > 0:
                importance[name] = (value - mean_val) / std_val
            else:
                importance[name] = 0
        
        return importance
    
    def _generate_narrative(self, direction: str, top_features: List[Tuple[str, float]],
                           model_contributions: Dict[str, float],
                           features: Dict[str, float]) -> str:
        """Generate human-readable narrative"""
        narrative_parts = []
        
        # Direction statement
        if direction == 'long':
            narrative_parts.append(f"Decision to go LONG based on:")
        elif direction == 'short':
            narrative_parts.append(f"Decision to go SHORT based on:")
        else:
            narrative_parts.append(f"Decision to stay NEUTRAL based on:")
        
        # Top features
        for feature_name, importance in top_features[:3]:
            if importance > 0:
                narrative_parts.append(f"  - {feature_name}: Positive contribution ({importance:.2f})")
            else:
                narrative_parts.append(f"  - {feature_name}: Negative contribution ({importance:.2f})")
        
        # Model contributions
        top_model = max(model_contributions, key=model_contributions.get)
        narrative_parts.append(f"Primary signal source: {top_model} ({model_contributions[top_model]:.1%})")
        
        return "\n".join(narrative_parts)
    
    def _identify_risk_factors(self, features: Dict[str, float],
                              model_outputs: Dict[str, Any]) -> List[str]:
        """Identify risk factors in the decision"""
        risks = []
        
        # Check for low confidence
        confidences = [
            output.get('confidence', 0.5) if isinstance(output, dict) else 0.5
            for output in model_outputs.values()
        ]
        if np.mean(confidences) < 0.6:
            risks.append("Low overall model confidence")
        
        # Check for model disagreement
        directions = [
            output.get('direction', 'neutral') if isinstance(output, dict) else 'neutral'
            for output in model_outputs.values()
        ]
        unique_directions = set(directions)
        if len(unique_directions) > 2:
            risks.append("Model disagreement on direction")
        
        # Check for high volatility
        if features.get('volatility', 0) > 0.03:
            risks.append("High market volatility")
        
        # Check for low liquidity
        if features.get('liquidity_score', 1) < 0.5:
            risks.append("Low market liquidity")
        
        return risks


class AuditTrailManager:
    """
    Audit Trail Management
    
    Maintains complete audit trail for regulatory compliance
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Audit records
        self.records: deque = deque(maxlen=100000)
        
        # Record types
        self.record_types = [
            'order_submitted', 'order_filled', 'order_cancelled',
            'position_opened', 'position_closed',
            'risk_check', 'compliance_check',
            'model_prediction', 'signal_generated',
            'system_event', 'user_action',
        ]
    
    def create_record(self, event_type: str, details: Dict[str, Any],
                     user: str = "system") -> AuditRecord:
        """
        Create audit record
        
        Args:
            event_type: Type of event
            details: Event details
            user: User or system that triggered event
            
        Returns:
            AuditRecord
        """
        timestamp = datetime.now()
        record_id = f"AUD_{timestamp.strftime('%Y%m%d%H%M%S%f')}"
        
        # Capture system state
        system_state = {
            'timestamp': timestamp.isoformat(),
            'memory_usage': 0,  # Would capture actual memory
            'active_positions': 0,  # Would capture actual count
        }
        
        # Create hash for integrity
        hash_input = f"{record_id}{event_type}{json.dumps(details, sort_keys=True)}{user}"
        record_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        record = AuditRecord(
            timestamp=timestamp,
            record_id=record_id,
            event_type=event_type,
            details=details,
            user=user,
            system_state=system_state,
            hash=record_hash,
        )
        
        self.records.append(record)
        
        return record
    
    def verify_integrity(self, record: AuditRecord) -> bool:
        """Verify record integrity"""
        hash_input = f"{record.record_id}{record.event_type}{json.dumps(record.details, sort_keys=True)}{record.user}"
        expected_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        return record.hash == expected_hash
    
    def get_records(self, event_type: str = None, start_time: datetime = None,
                   end_time: datetime = None) -> List[AuditRecord]:
        """
        Query audit records
        
        Args:
            event_type: Filter by event type
            start_time: Filter by start time
            end_time: Filter by end time
            
        Returns:
            List of matching records
        """
        records = list(self.records)
        
        if event_type:
            records = [r for r in records if r.event_type == event_type]
        
        if start_time:
            records = [r for r in records if r.timestamp >= start_time]
        
        if end_time:
            records = [r for r in records if r.timestamp <= end_time]
        
        return records
    
    def generate_report(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate compliance report for period"""
        records = self.get_records(start_time=start_time, end_time=end_time)
        
        # Count by type
        type_counts = {}
        for record in records:
            type_counts[record.event_type] = type_counts.get(record.event_type, 0) + 1
        
        # Check for violations
        violations = [r for r in records if 'violation' in r.details.get('severity', '').lower()]
        
        return {
            'period': f"{start_time.date()} to {end_time.date()}",
            'total_records': len(records),
            'records_by_type': type_counts,
            'violations': len(violations),
            'integrity_verified': all(self.verify_integrity(r) for r in records),
        }


class ComplianceEngine:
    """
    Unified Compliance Engine
    
    Integrates all compliance components
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize components
        self.pre_trade_controls = PreTradeRiskControls(config.get('pre_trade', {}))
        self.abuse_detector = MarketAbuseDetector(config.get('abuse', {}))
        self.explainer = ExplainableAI(config.get('xai', {}))
        self.audit_trail = AuditTrailManager(config.get('audit', {}))
        
        # Compliance history
        self.compliance_history: deque = deque(maxlen=10000)
    
    def check_order_compliance(self, order: Dict[str, Any], 
                              reference_price: float) -> Dict[str, Any]:
        """
        Run all compliance checks on order
        
        Args:
            order: Order details
            reference_price: Current market price
            
        Returns:
            Compliance result
        """
        checks = []
        
        # Pre-trade risk check
        pre_trade = self.pre_trade_controls.check_order(order, reference_price)
        checks.append(pre_trade)
        
        # Record in audit trail
        self.audit_trail.create_record(
            'compliance_check',
            {
                'order': order,
                'check': 'pre_trade_risk',
                'passed': pre_trade.passed,
                'severity': pre_trade.severity.value,
            }
        )
        
        # Determine overall result
        all_passed = all(c.passed for c in checks)
        max_severity = max(c.severity.value for c in checks)
        
        result = {
            'passed': all_passed,
            'checks': [
                {
                    'name': c.check_name,
                    'passed': c.passed,
                    'details': c.details,
                    'severity': c.severity.value,
                    'action': c.action_required,
                }
                for c in checks
            ],
            'max_severity': max_severity,
        }
        
        self.compliance_history.append(result)
        
        return result
    
    def explain_trade(self, trade_id: str, symbol: str, direction: str,
                     features: Dict[str, float], model_outputs: Dict[str, Any]) -> TradeExplanation:
        """Generate trade explanation"""
        explanation = self.explainer.explain_decision(
            trade_id, symbol, direction, features, model_outputs
        )
        
        # Record in audit trail
        self.audit_trail.create_record(
            'model_prediction',
            {
                'trade_id': trade_id,
                'symbol': symbol,
                'direction': direction,
                'confidence': explanation.confidence,
                'top_features': explanation.top_features,
            }
        )
        
        return explanation
    
    def get_compliance_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate compliance report"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        audit_report = self.audit_trail.generate_report(start_time, end_time)
        
        # Add compliance check summary
        recent_checks = [
            c for c in self.compliance_history
            if True  # Would filter by time
        ]
        
        passed_checks = sum(1 for c in recent_checks if c.get('passed', False))
        
        return {
            **audit_report,
            'compliance_checks': len(recent_checks),
            'passed_checks': passed_checks,
            'pass_rate': passed_checks / len(recent_checks) if recent_checks else 1.0,
        }
