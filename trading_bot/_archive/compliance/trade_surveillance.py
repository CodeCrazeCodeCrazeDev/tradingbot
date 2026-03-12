import logging
logger = logging.getLogger(__name__)
"""Compliance Automation - Real-Time Trade Surveillance Module

This module implements automated compliance monitoring and trade surveillance
to detect market manipulation, insider trading, and regulatory violations.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
import uuid
from collections import deque, defaultdict
from loguru import logger
import numpy
import pandas


class ViolationType(Enum):
    """Types of compliance violations."""
    WASH_TRADING = auto()
    LAYERING = auto()
    SPOOFING = auto()
    FRONT_RUNNING = auto()
    INSIDER_TRADING = auto()
    MARKET_MANIPULATION = auto()
    POSITION_LIMIT_BREACH = auto()
    CONCENTRATION_RISK = auto()
    SUSPICIOUS_TIMING = auto()
    EXCESSIVE_CANCELLATION = auto()


class SeverityLevel(Enum):
    """Severity levels for violations."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


@dataclass
class ComplianceViolation:
    """Represents a compliance violation."""
    id: str
    violation_type: ViolationType
    severity: SeverityLevel
    timestamp: datetime
    symbol: str
    description: str
    details: Dict[str, Any]
    risk_score: float  # 0.0 to 1.0
    user_id: Optional[str] = None
    strategy_id: Optional[str] = None
    trades_involved: List[str] = field(default_factory=list)
    status: str = "open"  # open, investigating, resolved, false_positive


@dataclass
class TradeRecord:
    """Trade record for surveillance."""
    id: str
    timestamp: datetime
    symbol: str
    side: str  # buy/sell
    quantity: float
    price: float
    user_id: str
    strategy_id: Optional[str] = None
    order_type: str = "market"
    execution_venue: str = "default"


@dataclass
class SurveillanceMetrics:
    """Surveillance system metrics."""
    total_trades_monitored: int = 0
    violations_detected: int = 0
    false_positives: int = 0
    alerts_generated: int = 0
    last_update: datetime = field(default_factory=datetime.now)


class TradeSurveillanceSystem:
    """Real-time trade surveillance and compliance monitoring system."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the trade surveillance system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Data storage
        self.trade_history: deque = deque(maxlen=self.config["max_trade_history"])
        self.violations: List[ComplianceViolation] = []
        self.user_positions: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.user_trade_patterns: Dict[str, List[TradeRecord]] = defaultdict(list)
        
        # Surveillance metrics
        self.metrics = SurveillanceMetrics()
        
        # Pattern detection windows
        self.wash_trading_window = timedelta(minutes=self.config["wash_trading_window_minutes"])
        self.layering_window = timedelta(minutes=self.config["layering_window_minutes"])
        self.front_running_window = timedelta(seconds=self.config["front_running_window_seconds"])
        
        logger.info("TradeSurveillanceSystem initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "max_trade_history": 100000,
            "wash_trading_threshold": 0.95,  # Price similarity threshold
            "wash_trading_window_minutes": 30,
            "layering_min_levels": 3,
            "layering_window_minutes": 10,
            "front_running_window_seconds": 30,
            "position_limit_threshold": 0.1,  # 10% of total volume
            "concentration_risk_threshold": 0.2,  # 20% of portfolio
            "excessive_cancellation_ratio": 0.8,  # 80% cancellation rate
            "suspicious_timing_threshold": 5,  # seconds before news
            "min_violation_score": 0.3,
            "alert_cooldown_minutes": 60
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def monitor_trade(self, trade: TradeRecord) -> List[ComplianceViolation]:
        """Monitor a single trade for compliance violations.
        
        Args:
            trade: Trade record to monitor
            
        Returns:
            List of detected violations
        """
        violations = []
        
        # Add trade to history
        self.trade_history.append(trade)
        self.user_trade_patterns[trade.user_id].append(trade)
        
        # Update position tracking
        if trade.side == "buy":
            self.user_positions[trade.user_id][trade.symbol] = \
                self.user_positions[trade.user_id].get(trade.symbol, 0) + trade.quantity
        else:
            self.user_positions[trade.user_id][trade.symbol] = \
                self.user_positions[trade.user_id].get(trade.symbol, 0) - trade.quantity
        
        # Run surveillance checks
        violations.extend(self._check_wash_trading(trade))
        violations.extend(self._check_layering_spoofing(trade))
        violations.extend(self._check_front_running(trade))
        violations.extend(self._check_position_limits(trade))
        violations.extend(self._check_concentration_risk(trade))
        violations.extend(self._check_suspicious_timing(trade))
        
        # Store violations
        for violation in violations:
            self.violations.append(violation)
            logger.warning(f"Compliance violation detected: {violation.violation_type.name} "
                         f"for user {trade.user_id} in {trade.symbol}")
        
        # Update metrics
        self.metrics.total_trades_monitored += 1
        self.metrics.violations_detected += len(violations)
        self.metrics.alerts_generated += len([v for v in violations if v.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]])
        self.metrics.last_update = datetime.now()
        
        return violations
    
    def _check_wash_trading(self, trade: TradeRecord) -> List[ComplianceViolation]:
        """Check for wash trading patterns."""
        violations = []
        
        # Get recent trades from same user in same symbol
        cutoff_time = trade.timestamp - self.wash_trading_window
        recent_trades = [
            t for t in self.user_trade_patterns[trade.user_id]
            if t.symbol == trade.symbol and t.timestamp >= cutoff_time and t.id != trade.id
        ]
        
        if not recent_trades:
            return violations
        
        # Look for offsetting trades at similar prices
        for recent_trade in recent_trades:
            # Check if trades are offsetting (opposite sides)
            if recent_trade.side != trade.side:
                # Check price similarity
                price_diff = abs(trade.price - recent_trade.price) / recent_trade.price
                
                if price_diff <= (1 - self.config["wash_trading_threshold"]):
                    # Check quantity similarity
                    qty_ratio = min(trade.quantity, recent_trade.quantity) / max(trade.quantity, recent_trade.quantity)
                    
                    if qty_ratio > 0.8:  # Similar quantities
                        risk_score = (1 - price_diff) * qty_ratio
                        
                        if risk_score >= self.config["min_violation_score"]:
                            violation = ComplianceViolation(
                                id=str(uuid.uuid4()),
                                violation_type=ViolationType.WASH_TRADING,
                                severity=SeverityLevel.HIGH if risk_score > 0.8 else SeverityLevel.MEDIUM,
                                timestamp=trade.timestamp,
                                symbol=trade.symbol,
                                description=f"Potential wash trading detected: offsetting trades at similar prices",
                                details={
                                    "trade1_id": trade.id,
                                    "trade2_id": recent_trade.id,
                                    "price_similarity": 1 - price_diff,
                                    "quantity_ratio": qty_ratio,
                                    "time_difference_minutes": (trade.timestamp - recent_trade.timestamp).total_seconds() / 60
                                },
                                risk_score=risk_score,
                                user_id=trade.user_id,
                                trades_involved=[trade.id, recent_trade.id]
                            )
                            violations.append(violation)
        
        return violations
    
    def _check_layering_spoofing(self, trade: TradeRecord) -> List[ComplianceViolation]:
        """Check for layering and spoofing patterns."""
        violations = []
        
        # Get recent trades from same user in same symbol
        cutoff_time = trade.timestamp - self.layering_window
        recent_trades = [
            t for t in self.user_trade_patterns[trade.user_id]
            if t.symbol == trade.symbol and t.timestamp >= cutoff_time
        ]
        
        if len(recent_trades) < self.config["layering_min_levels"]:
            return violations
        
        # Analyze order patterns for layering
        buy_orders = [t for t in recent_trades if t.side == "buy"]
        sell_orders = [t for t in recent_trades if t.side == "sell"]
        
        # Check for imbalanced order placement (many orders on one side)
        if len(buy_orders) > 0 and len(sell_orders) > 0:
            imbalance_ratio = max(len(buy_orders), len(sell_orders)) / min(len(buy_orders), len(sell_orders))
            
            if imbalance_ratio >= 3.0:  # Significant imbalance
                # Check for price levels (layering typically involves multiple price levels)
                if len(buy_orders) > len(sell_orders):
                    dominant_side = "buy"
                    dominant_orders = buy_orders
                else:
                    dominant_side = "sell"
                    dominant_orders = sell_orders
                
                # Check price distribution
                prices = [t.price for t in dominant_orders]
                price_levels = len(set(prices))
                
                if price_levels >= self.config["layering_min_levels"]:
                    risk_score = min(1.0, (imbalance_ratio - 2.0) / 5.0 + (price_levels / 10.0))
                    
                    if risk_score >= self.config["min_violation_score"]:
                        violation = ComplianceViolation(
                            id=str(uuid.uuid4()),
                            violation_type=ViolationType.LAYERING,
                            severity=SeverityLevel.HIGH if risk_score > 0.7 else SeverityLevel.MEDIUM,
                            timestamp=trade.timestamp,
                            symbol=trade.symbol,
                            description=f"Potential layering detected: {imbalance_ratio:.1f}x order imbalance on {dominant_side} side",
                            details={
                                "imbalance_ratio": imbalance_ratio,
                                "dominant_side": dominant_side,
                                "price_levels": price_levels,
                                "total_orders": len(recent_trades)
                            },
                            risk_score=risk_score,
                            user_id=trade.user_id,
                            trades_involved=[t.id for t in recent_trades]
                        )
                        violations.append(violation)
        
        return violations
    
    def _check_front_running(self, trade: TradeRecord) -> List[ComplianceViolation]:
        """Check for front-running patterns."""
        violations = []
        
        # Get trades from other users in same symbol shortly after this trade
        cutoff_time = trade.timestamp + self.front_running_window
        
        # Look for large trades from other users that might have been front-run
        recent_other_trades = [
            t for t in self.trade_history
            if (t.symbol == trade.symbol and 
                t.user_id != trade.user_id and
                t.timestamp > trade.timestamp and 
                t.timestamp <= cutoff_time and
                t.quantity > trade.quantity * 2)  # Significantly larger trade
        ]
        
        for other_trade in recent_other_trades:
            # Check if trades are in same direction (potential front-running)
            if trade.side == other_trade.side:
                # Check if the front-runner got a better price
                if ((trade.side == "buy" and trade.price < other_trade.price) or
                    (trade.side == "sell" and trade.price > other_trade.price)):
                    
                    time_diff = (other_trade.timestamp - trade.timestamp).total_seconds()
                    size_ratio = other_trade.quantity / trade.quantity
                    
                    risk_score = min(1.0, (1 / (time_diff + 1)) * (size_ratio / 10))
                    
                    if risk_score >= self.config["min_violation_score"]:
                        violation = ComplianceViolation(
                            id=str(uuid.uuid4()),
                            violation_type=ViolationType.FRONT_RUNNING,
                            severity=SeverityLevel.HIGH if risk_score > 0.6 else SeverityLevel.MEDIUM,
                            timestamp=trade.timestamp,
                            symbol=trade.symbol,
                            description=f"Potential front-running: small trade followed by large trade in same direction",
                            details={
                                "front_runner_trade_id": trade.id,
                                "victim_trade_id": other_trade.id,
                                "time_difference_seconds": time_diff,
                                "size_ratio": size_ratio,
                                "price_advantage": abs(trade.price - other_trade.price) / other_trade.price
                            },
                            risk_score=risk_score,
                            user_id=trade.user_id,
                            trades_involved=[trade.id, other_trade.id]
                        )
                        violations.append(violation)
        
        return violations
    
    def _check_position_limits(self, trade: TradeRecord) -> List[ComplianceViolation]:
        """Check for position limit breaches."""
        violations = []
        
        # Get current position for user in this symbol
        current_position = abs(self.user_positions[trade.user_id].get(trade.symbol, 0))
        
        # Calculate recent volume in this symbol (simplified - would use actual market data)
        recent_volume = sum(t.quantity for t in self.trade_history 
                          if t.symbol == trade.symbol and 
                          t.timestamp >= trade.timestamp - timedelta(hours=24))
        
        if recent_volume > 0:
            position_ratio = current_position / recent_volume
            
            if position_ratio > self.config["position_limit_threshold"]:
                risk_score = min(1.0, position_ratio / (self.config["position_limit_threshold"] * 2))
                
                violation = ComplianceViolation(
                    id=str(uuid.uuid4()),
                    violation_type=ViolationType.POSITION_LIMIT_BREACH,
                    severity=SeverityLevel.CRITICAL if position_ratio > 0.2 else SeverityLevel.HIGH,
                    timestamp=trade.timestamp,
                    symbol=trade.symbol,
                    description=f"Position limit breach: {position_ratio:.2%} of daily volume",
                    details={
                        "current_position": current_position,
                        "daily_volume": recent_volume,
                        "position_ratio": position_ratio,
                        "limit_threshold": self.config["position_limit_threshold"]
                    },
                    risk_score=risk_score,
                    user_id=trade.user_id
                )
                violations.append(violation)
        
        return violations
    
    def _check_concentration_risk(self, trade: TradeRecord) -> List[ComplianceViolation]:
        """Check for concentration risk violations."""
        violations = []
        
        # Calculate total portfolio value for user (simplified)
        total_position_value = sum(
            abs(qty * 100)  # Assuming price of 100 for simplification
            for positions in self.user_positions[trade.user_id].values()
            for qty in [positions] if qty != 0
        )
        
        if total_position_value > 0:
            symbol_position_value = abs(self.user_positions[trade.user_id].get(trade.symbol, 0) * 100)
            concentration_ratio = symbol_position_value / total_position_value
            
            if concentration_ratio > self.config["concentration_risk_threshold"]:
                risk_score = min(1.0, concentration_ratio / (self.config["concentration_risk_threshold"] * 2))
                
                violation = ComplianceViolation(
                    id=str(uuid.uuid4()),
                    violation_type=ViolationType.CONCENTRATION_RISK,
                    severity=SeverityLevel.MEDIUM if concentration_ratio < 0.4 else SeverityLevel.HIGH,
                    timestamp=trade.timestamp,
                    symbol=trade.symbol,
                    description=f"High concentration risk: {concentration_ratio:.2%} of portfolio in single symbol",
                    details={
                        "concentration_ratio": concentration_ratio,
                        "symbol_position_value": symbol_position_value,
                        "total_portfolio_value": total_position_value,
                        "risk_threshold": self.config["concentration_risk_threshold"]
                    },
                    risk_score=risk_score,
                    user_id=trade.user_id
                )
                violations.append(violation)
        
        return violations
    
    def _check_suspicious_timing(self, trade: TradeRecord) -> List[ComplianceViolation]:
        """Check for suspicious timing patterns (e.g., trading before news)."""
        violations = []
        
        # This would integrate with news feed APIs in a real implementation
        # For now, we'll simulate by checking for unusual trading patterns
        
        # Get recent trades from same user
        recent_trades = [
            t for t in self.user_trade_patterns[trade.user_id]
            if t.symbol == trade.symbol and 
            t.timestamp >= trade.timestamp - timedelta(hours=1)
        ]
        
        if len(recent_trades) >= 5:  # Burst of trading activity
            # Check if trades are clustered in time
            timestamps = [t.timestamp for t in recent_trades]
            time_diffs = [(timestamps[i] - timestamps[i-1]).total_seconds() 
                         for i in range(1, len(timestamps))]
            
            avg_time_diff = np.mean(time_diffs) if time_diffs else 0
            
            if avg_time_diff < 60:  # Less than 1 minute between trades on average
                risk_score = min(1.0, 5 / len(recent_trades) + (60 - avg_time_diff) / 60)
                
                if risk_score >= self.config["min_violation_score"]:
                    violation = ComplianceViolation(
                        id=str(uuid.uuid4()),
                        violation_type=ViolationType.SUSPICIOUS_TIMING,
                        severity=SeverityLevel.MEDIUM,
                        timestamp=trade.timestamp,
                        symbol=trade.symbol,
                        description=f"Suspicious trading burst: {len(recent_trades)} trades in 1 hour",
                        details={
                            "trades_in_hour": len(recent_trades),
                            "avg_time_between_trades": avg_time_diff,
                            "total_quantity": sum(t.quantity for t in recent_trades)
                        },
                        risk_score=risk_score,
                        user_id=trade.user_id,
                        trades_involved=[t.id for t in recent_trades]
                    )
                    violations.append(violation)
        
        return violations
    
    def get_compliance_report(self, 
                            start_date: datetime = None,
                            end_date: datetime = None,
                            user_id: str = None,
                            violation_types: List[ViolationType] = None) -> Dict[str, Any]:
        """Generate compliance report.
        
        Args:
            start_date: Start date for report
            end_date: End date for report
            user_id: Filter by specific user
            violation_types: Filter by violation types
            
        Returns:
            Compliance report dictionary
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()
        
        # Filter violations
        filtered_violations = []
        for violation in self.violations:
            if violation.timestamp < start_date or violation.timestamp > end_date:
                continue
            if user_id and violation.user_id != user_id:
                continue
            if violation_types and violation.violation_type not in violation_types:
                continue
            filtered_violations.append(violation)
        
        # Generate statistics
        total_violations = len(filtered_violations)
        violations_by_type = defaultdict(int)
        violations_by_severity = defaultdict(int)
        violations_by_user = defaultdict(int)
        
        for violation in filtered_violations:
            violations_by_type[violation.violation_type.name] += 1
            violations_by_severity[violation.severity.name] += 1
            if violation.user_id:
                violations_by_user[violation.user_id] += 1
        
        # Calculate risk metrics
        avg_risk_score = np.mean([v.risk_score for v in filtered_violations]) if filtered_violations else 0.0
        high_risk_violations = len([v for v in filtered_violations if v.risk_score > 0.7])
        
        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_violations": total_violations,
                "high_risk_violations": high_risk_violations,
                "average_risk_score": avg_risk_score,
                "unique_users_involved": len(violations_by_user)
            },
            "breakdown": {
                "by_type": dict(violations_by_type),
                "by_severity": dict(violations_by_severity),
                "by_user": dict(violations_by_user)
            },
            "surveillance_metrics": {
                "total_trades_monitored": self.metrics.total_trades_monitored,
                "detection_rate": (total_violations / self.metrics.total_trades_monitored * 100) 
                                if self.metrics.total_trades_monitored > 0 else 0.0,
                "false_positive_rate": (self.metrics.false_positives / total_violations * 100)
                                     if total_violations > 0 else 0.0
            },
            "recent_violations": [
                {
                    "id": v.id,
                    "type": v.violation_type.name,
                    "severity": v.severity.name,
                    "timestamp": v.timestamp.isoformat(),
                    "symbol": v.symbol,
                    "description": v.description,
                    "risk_score": v.risk_score,
                    "user_id": v.user_id,
                    "status": v.status
                }
                for v in sorted(filtered_violations, key=lambda x: x.timestamp, reverse=True)[:20]
            ]
        }
    
    def update_violation_status(self, violation_id: str, status: str, notes: str = "") -> bool:
        """Update the status of a compliance violation.
        
        Args:
            violation_id: Violation ID
            status: New status
            notes: Additional notes
            
        Returns:
            True if successful, False otherwise
        """
        for violation in self.violations:
            if violation.id == violation_id:
                violation.status = status
                if notes:
                    violation.details["investigation_notes"] = notes
                    violation.details["status_updated"] = datetime.now().isoformat()
                
                # Update metrics for false positives
                if status == "false_positive":
                    self.metrics.false_positives += 1
                
                logger.info(f"Updated violation {violation_id} status to {status}")
                return True
        
        return False
    
    def get_user_risk_profile(self, user_id: str) -> Dict[str, Any]:
        """Get risk profile for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            User risk profile
        """
        user_violations = [v for v in self.violations if v.user_id == user_id]
        user_trades = self.user_trade_patterns.get(user_id, [])
        
        if not user_trades:
            return {
                "user_id": user_id,
                "risk_level": "unknown",
                "message": "No trading activity found"
            }
        
        # Calculate risk metrics
        total_violations = len(user_violations)
        high_risk_violations = len([v for v in user_violations if v.risk_score > 0.7])
        avg_risk_score = np.mean([v.risk_score for v in user_violations]) if user_violations else 0.0
        
        # Risk level classification
        violation_rate = total_violations / len(user_trades) if user_trades else 0.0
        
        if violation_rate > 0.1 or high_risk_violations > 5:
            risk_level = "high"
        elif violation_rate > 0.05 or high_risk_violations > 2:
            risk_level = "medium"
        elif violation_rate > 0.01 or total_violations > 0:
            risk_level = "low"
        else:
            risk_level = "minimal"
        
        # Recent activity
        recent_trades = len([t for t in user_trades 
                           if t.timestamp >= datetime.now() - timedelta(days=7)])
        recent_violations = len([v for v in user_violations 
                               if v.timestamp >= datetime.now() - timedelta(days=7)])
        
        return {
            "user_id": user_id,
            "risk_level": risk_level,
            "total_trades": len(user_trades),
            "total_violations": total_violations,
            "high_risk_violations": high_risk_violations,
            "violation_rate": violation_rate,
            "average_risk_score": avg_risk_score,
            "recent_activity": {
                "trades_last_7_days": recent_trades,
                "violations_last_7_days": recent_violations
            },
            "violation_types": list(set(v.violation_type.name for v in user_violations)),
            "current_positions": dict(self.user_positions.get(user_id, {}))
        }
