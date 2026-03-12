"""
Trust & Safety Layer
====================
Enterprise-grade audit, logging, and quarantine system.

Features:
- Every trade logged and scored
- Every strategy change explained
- Every evolution audited
- Failed modules quarantined
- Suspicious behavior flagged
- Complete audit trail
- Compliance reporting

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
import json
import hashlib
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from collections import deque
import threading
import traceback
import uuid

import numpy as np
import pandas as pd
import numpy
import pandas

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""
    TRADE_EXECUTED = auto()
    TRADE_REJECTED = auto()
    STRATEGY_CHANGED = auto()
    STRATEGY_ADDED = auto()
    STRATEGY_REMOVED = auto()
    PARAMETER_CHANGED = auto()
    RISK_LIMIT_BREACH = auto()
    ANOMALY_DETECTED = auto()
    MODULE_QUARANTINED = auto()
    MODULE_RESTORED = auto()
    SYSTEM_ERROR = auto()
    EVOLUTION_CYCLE = auto()
    MANUAL_OVERRIDE = auto()
    COMPLIANCE_CHECK = auto()


class SeverityLevel(Enum):
    """Severity levels for events"""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class QuarantineReason(Enum):
    """Reasons for quarantine"""
    EXCESSIVE_LOSSES = auto()
    ANOMALOUS_BEHAVIOR = auto()
    SYSTEM_ERROR = auto()
    COMPLIANCE_VIOLATION = auto()
    MANUAL_QUARANTINE = auto()
    PERFORMANCE_DEGRADATION = auto()


class TrustScore(Enum):
    """Trust score levels"""
    TRUSTED = auto()
    VERIFIED = auto()
    NEUTRAL = auto()
    SUSPICIOUS = auto()
    UNTRUSTED = auto()


@dataclass
class AuditEvent:
    """Single audit event"""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    
    # Event details
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Context
    module_name: str = ""
    strategy_name: str = ""
    symbol: str = ""
    
    # Severity
    severity: SeverityLevel = SeverityLevel.INFO
    
    # Outcome
    outcome: str = ""
    impact: str = ""
    
    # Traceability
    user_id: str = "system"
    session_id: str = ""
    correlation_id: str = ""


@dataclass
class TradeAudit:
    """Detailed trade audit record"""
    trade_id: str
    timestamp: datetime
    
    # Trade details
    symbol: str
    side: str
    quantity: float
    price: float
    
    # Decision context
    signal_source: str = ""
    signal_confidence: float = 0.0
    strategy_name: str = ""
    
    # Risk assessment
    risk_score: float = 0.0
    position_size_pct: float = 0.0
    portfolio_impact: float = 0.0
    
    # Execution quality
    slippage: float = 0.0
    execution_time_ms: float = 0.0
    venue: str = ""
    
    # Outcome
    pnl: float = 0.0
    outcome: str = ""  # win, loss, breakeven
    
    # Compliance
    compliant: bool = True
    compliance_notes: str = ""
    
    # Scoring
    trade_score: float = 0.0
    explanation: str = ""


@dataclass
class QuarantinedModule:
    """Quarantined module record"""
    module_id: str
    module_name: str
    quarantine_time: datetime
    
    # Reason
    reason: QuarantineReason
    reason_details: str = ""
    
    # Impact
    trades_affected: int = 0
    pnl_impact: float = 0.0
    
    # Status
    is_active: bool = True
    restored_time: Optional[datetime] = None
    restore_reason: str = ""
    
    # Review
    reviewed_by: str = ""
    review_notes: str = ""


@dataclass
class StrategyChangeRecord:
    """Record of strategy changes"""
    change_id: str
    timestamp: datetime
    
    # Change details
    strategy_name: str
    change_type: str  # parameter, logic, weight, etc.
    
    # Before/After
    previous_value: Any = None
    new_value: Any = None
    
    # Explanation
    explanation: str = ""
    justification: str = ""
    
    # Impact assessment
    expected_impact: str = ""
    risk_assessment: str = ""
    
    # Approval
    approved_by: str = "system"
    approval_time: Optional[datetime] = None


class AuditLogger:
    """Persistent audit logging"""
    
    def __init__(self, db_path: str = "audit_log.db"):
        try:
            self.db_path = db_path
            self._init_database()
            self._lock = threading.Lock()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def _init_database(self):
        """Initialize audit database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        
            # Audit events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT,
                    timestamp TEXT,
                    description TEXT,
                    details TEXT,
                    module_name TEXT,
                    strategy_name TEXT,
                    symbol TEXT,
                    severity TEXT,
                    outcome TEXT,
                    impact TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    correlation_id TEXT
                )
            ''')
        
            # Trade audits table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_audits (
                    trade_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    symbol TEXT,
                    side TEXT,
                    quantity REAL,
                    price REAL,
                    signal_source TEXT,
                    signal_confidence REAL,
                    strategy_name TEXT,
                    risk_score REAL,
                    position_size_pct REAL,
                    portfolio_impact REAL,
                    slippage REAL,
                    execution_time_ms REAL,
                    venue TEXT,
                    pnl REAL,
                    outcome TEXT,
                    compliant INTEGER,
                    compliance_notes TEXT,
                    trade_score REAL,
                    explanation TEXT
                )
            ''')
        
            # Quarantine table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quarantine (
                    module_id TEXT PRIMARY KEY,
                    module_name TEXT,
                    quarantine_time TEXT,
                    reason TEXT,
                    reason_details TEXT,
                    trades_affected INTEGER,
                    pnl_impact REAL,
                    is_active INTEGER,
                    restored_time TEXT,
                    restore_reason TEXT,
                    reviewed_by TEXT,
                    review_notes TEXT
                )
            ''')
        
            # Strategy changes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_changes (
                    change_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    strategy_name TEXT,
                    change_type TEXT,
                    previous_value TEXT,
                    new_value TEXT,
                    explanation TEXT,
                    justification TEXT,
                    expected_impact TEXT,
                    risk_assessment TEXT,
                    approved_by TEXT,
                    approval_time TEXT
                )
            ''')
        
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error in _init_database: {e}")
            raise
    
    def log_event(self, event: AuditEvent):
        """Log an audit event"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
            
                cursor.execute('''
                    INSERT INTO audit_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.event_id,
                    event.event_type.name,
                    event.timestamp.isoformat(),
                    event.description,
                    json.dumps(event.details),
                    event.module_name,
                    event.strategy_name,
                    event.symbol,
                    event.severity.name,
                    event.outcome,
                    event.impact,
                    event.user_id,
                    event.session_id,
                    event.correlation_id
                ))
            
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"Error in log_event: {e}")
            raise
    
    def log_trade(self, trade: TradeAudit):
        """Log a trade audit"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
            
                cursor.execute('''
                    INSERT OR REPLACE INTO trade_audits VALUES 
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade.trade_id,
                    trade.timestamp.isoformat(),
                    trade.symbol,
                    trade.side,
                    trade.quantity,
                    trade.price,
                    trade.signal_source,
                    trade.signal_confidence,
                    trade.strategy_name,
                    trade.risk_score,
                    trade.position_size_pct,
                    trade.portfolio_impact,
                    trade.slippage,
                    trade.execution_time_ms,
                    trade.venue,
                    trade.pnl,
                    trade.outcome,
                    1 if trade.compliant else 0,
                    trade.compliance_notes,
                    trade.trade_score,
                    trade.explanation
                ))
            
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"Error in log_trade: {e}")
            raise
    
    def log_quarantine(self, module: QuarantinedModule):
        """Log quarantine action"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
            
                cursor.execute('''
                    INSERT OR REPLACE INTO quarantine VALUES 
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    module.module_id,
                    module.module_name,
                    module.quarantine_time.isoformat(),
                    module.reason.name,
                    module.reason_details,
                    module.trades_affected,
                    module.pnl_impact,
                    1 if module.is_active else 0,
                    module.restored_time.isoformat() if module.restored_time else None,
                    module.restore_reason,
                    module.reviewed_by,
                    module.review_notes
                ))
            
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"Error in log_quarantine: {e}")
            raise
    
    def log_strategy_change(self, change: StrategyChangeRecord):
        """Log strategy change"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
            
                cursor.execute('''
                    INSERT INTO strategy_changes VALUES 
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    change.change_id,
                    change.timestamp.isoformat(),
                    change.strategy_name,
                    change.change_type,
                    json.dumps(change.previous_value),
                    json.dumps(change.new_value),
                    change.explanation,
                    change.justification,
                    change.expected_impact,
                    change.risk_assessment,
                    change.approved_by,
                    change.approval_time.isoformat() if change.approval_time else None
                ))
            
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"Error in log_strategy_change: {e}")
            raise
    
    def get_recent_events(
        self,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[SeverityLevel] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get recent audit events"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        
            query = "SELECT * FROM audit_events WHERE 1=1"
            params = []
        
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type.name)
        
            if severity:
                query += " AND severity = ?"
                params.append(severity.name)
        
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
        
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
        
            events = []
            for row in rows:
                events.append(AuditEvent(
                    event_id=row[0],
                    event_type=AuditEventType[row[1]],
                    timestamp=datetime.fromisoformat(row[2]),
                    description=row[3],
                    details=json.loads(row[4]) if row[4] else {},
                    module_name=row[5],
                    strategy_name=row[6],
                    symbol=row[7],
                    severity=SeverityLevel[row[8]],
                    outcome=row[9],
                    impact=row[10],
                    user_id=row[11],
                    session_id=row[12],
                    correlation_id=row[13]
                ))
        
            return events
        except Exception as e:
            logger.error(f"Error in get_recent_events: {e}")
            raise


class TradeScorer:
    """Score trades for quality assessment"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def score_trade(self, trade: TradeAudit) -> Tuple[float, str]:
        """Score a trade and provide explanation"""
        
        try:
            score = 50  # Base score
            explanations = []
        
            # Signal confidence scoring
            if trade.signal_confidence > 0.8:
                score += 15
                explanations.append("High signal confidence (+15)")
            elif trade.signal_confidence > 0.6:
                score += 10
                explanations.append("Good signal confidence (+10)")
            elif trade.signal_confidence < 0.4:
                score -= 10
                explanations.append("Low signal confidence (-10)")
        
            # Risk score assessment
            if trade.risk_score < 0.3:
                score += 10
                explanations.append("Low risk score (+10)")
            elif trade.risk_score > 0.7:
                score -= 15
                explanations.append("High risk score (-15)")
        
            # Position sizing
            if 0.01 <= trade.position_size_pct <= 0.02:
                score += 10
                explanations.append("Optimal position size (+10)")
            elif trade.position_size_pct > 0.05:
                score -= 15
                explanations.append("Oversized position (-15)")
        
            # Execution quality
            if trade.slippage < 0.0001:
                score += 10
                explanations.append("Excellent execution (+10)")
            elif trade.slippage > 0.001:
                score -= 10
                explanations.append("Poor execution (-10)")
        
            # Outcome
            if trade.outcome == 'win':
                score += 10
                explanations.append("Winning trade (+10)")
            elif trade.outcome == 'loss':
                score -= 5
                explanations.append("Losing trade (-5)")
        
            # Compliance
            if not trade.compliant:
                score -= 30
                explanations.append("Compliance violation (-30)")
        
            # Normalize score
            score = max(0, min(100, score))
        
            explanation = "; ".join(explanations)
        
            return score, explanation
        except Exception as e:
            logger.error(f"Error in score_trade: {e}")
            raise


class AnomalyDetector:
    """Detect suspicious behavior"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.trade_history: deque = deque(maxlen=1000)
            self.baseline_metrics: Dict[str, float] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def add_trade(self, trade: TradeAudit):
        """Add trade to history"""
        try:
            self.trade_history.append(trade)
            self._update_baseline()
        except Exception as e:
            logger.error(f"Error in add_trade: {e}")
            raise
    
    def _update_baseline(self):
        """Update baseline metrics"""
        try:
            if len(self.trade_history) < 50:
                return
        
            trades = list(self.trade_history)
        
            self.baseline_metrics = {
                'avg_trade_size': np.mean([t.quantity for t in trades]),
                'avg_slippage': np.mean([t.slippage for t in trades]),
                'avg_execution_time': np.mean([t.execution_time_ms for t in trades]),
                'win_rate': sum(1 for t in trades if t.outcome == 'win') / len(trades),
                'avg_pnl': np.mean([t.pnl for t in trades])
            }
        except Exception as e:
            logger.error(f"Error in _update_baseline: {e}")
            raise
    
    def detect_anomalies(self, trade: TradeAudit) -> List[Dict[str, Any]]:
        """Detect anomalies in trade"""
        
        try:
            anomalies = []
        
            if not self.baseline_metrics:
                return anomalies
        
            # Size anomaly
            if trade.quantity > self.baseline_metrics['avg_trade_size'] * 5:
                anomalies.append({
                    'type': 'size_anomaly',
                    'severity': 'high',
                    'description': f"Trade size {trade.quantity} is 5x above average"
                })
        
            # Slippage anomaly
            if trade.slippage > self.baseline_metrics['avg_slippage'] * 3:
                anomalies.append({
                    'type': 'slippage_anomaly',
                    'severity': 'medium',
                    'description': f"Slippage {trade.slippage} is 3x above average"
                })
        
            # Execution time anomaly
            if trade.execution_time_ms > self.baseline_metrics['avg_execution_time'] * 10:
                anomalies.append({
                    'type': 'execution_anomaly',
                    'severity': 'low',
                    'description': f"Execution time {trade.execution_time_ms}ms is 10x above average"
                })
        
            # Consecutive losses
            recent_trades = list(self.trade_history)[-10:]
            consecutive_losses = sum(1 for t in recent_trades if t.outcome == 'loss')
            if consecutive_losses >= 8:
                anomalies.append({
                    'type': 'loss_streak',
                    'severity': 'critical',
                    'description': f"{consecutive_losses} consecutive losses detected"
                })
        
            return anomalies
        except Exception as e:
            logger.error(f"Error in detect_anomalies: {e}")
            raise


class QuarantineManager:
    """Manage module quarantine"""
    
    def __init__(self, audit_logger: AuditLogger):
        try:
            self.audit_logger = audit_logger
            self.quarantined: Dict[str, QuarantinedModule] = {}
            self._lock = threading.Lock()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def quarantine_module(
        self,
        module_name: str,
        reason: QuarantineReason,
        reason_details: str = "",
        trades_affected: int = 0,
        pnl_impact: float = 0.0
    ) -> QuarantinedModule:
        """Quarantine a module"""
        
        try:
            with self._lock:
                module = QuarantinedModule(
                    module_id=str(uuid.uuid4())[:8],
                    module_name=module_name,
                    quarantine_time=datetime.now(),
                    reason=reason,
                    reason_details=reason_details,
                    trades_affected=trades_affected,
                    pnl_impact=pnl_impact
                )
            
                self.quarantined[module_name] = module
                self.audit_logger.log_quarantine(module)
            
                # Log event
                event = AuditEvent(
                    event_id=str(uuid.uuid4())[:8],
                    event_type=AuditEventType.MODULE_QUARANTINED,
                    timestamp=datetime.now(),
                    description=f"Module {module_name} quarantined: {reason.name}",
                    details={'reason': reason.name, 'details': reason_details},
                    module_name=module_name,
                    severity=SeverityLevel.WARNING
                )
                self.audit_logger.log_event(event)
            
                logger.warning(f"Module quarantined: {module_name} - {reason.name}")
            
                return module
        except Exception as e:
            logger.error(f"Error in quarantine_module: {e}")
            raise
    
    def restore_module(
        self,
        module_name: str,
        restore_reason: str = "",
        reviewed_by: str = "system"
    ) -> bool:
        """Restore a quarantined module"""
        
        try:
            with self._lock:
                if module_name not in self.quarantined:
                    return False
            
                module = self.quarantined[module_name]
                module.is_active = False
                module.restored_time = datetime.now()
                module.restore_reason = restore_reason
                module.reviewed_by = reviewed_by
            
                self.audit_logger.log_quarantine(module)
            
                # Log event
                event = AuditEvent(
                    event_id=str(uuid.uuid4())[:8],
                    event_type=AuditEventType.MODULE_RESTORED,
                    timestamp=datetime.now(),
                    description=f"Module {module_name} restored: {restore_reason}",
                    details={'restore_reason': restore_reason},
                    module_name=module_name,
                    severity=SeverityLevel.INFO
                )
                self.audit_logger.log_event(event)
            
                del self.quarantined[module_name]
            
                logger.info(f"Module restored: {module_name}")
            
                return True
        except Exception as e:
            logger.error(f"Error in restore_module: {e}")
            raise
    
    def is_quarantined(self, module_name: str) -> bool:
        """Check if module is quarantined"""
        return module_name in self.quarantined
    
    def get_quarantined_modules(self) -> List[QuarantinedModule]:
        """Get all quarantined modules"""
        return list(self.quarantined.values())


class ComplianceChecker:
    """Check compliance rules"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Compliance limits
            self.max_position_size = self.config.get('max_position_size', 0.05)
            self.max_daily_trades = self.config.get('max_daily_trades', 100)
            self.max_daily_loss = self.config.get('max_daily_loss', 0.03)
            self.max_single_loss = self.config.get('max_single_loss', 0.02)
        
            # Daily tracking
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.last_reset = datetime.now().date()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def check_trade(self, trade: TradeAudit) -> Tuple[bool, List[str]]:
        """Check trade compliance"""
        
        try:
            violations = []
        
            # Reset daily counters
            if datetime.now().date() != self.last_reset:
                self.daily_trades = 0
                self.daily_pnl = 0.0
                self.last_reset = datetime.now().date()
        
            # Position size check
            if trade.position_size_pct > self.max_position_size:
                violations.append(f"Position size {trade.position_size_pct:.2%} exceeds limit {self.max_position_size:.2%}")
        
            # Daily trade count
            if self.daily_trades >= self.max_daily_trades:
                violations.append(f"Daily trade limit {self.max_daily_trades} reached")
        
            # Daily loss check
            if self.daily_pnl < -self.max_daily_loss:
                violations.append(f"Daily loss limit {self.max_daily_loss:.2%} breached")
        
            # Single trade loss check
            if trade.pnl < -self.max_single_loss:
                violations.append(f"Single trade loss {abs(trade.pnl):.2%} exceeds limit {self.max_single_loss:.2%}")
        
            # Update counters
            self.daily_trades += 1
            self.daily_pnl += trade.pnl
        
            compliant = len(violations) == 0
        
            return compliant, violations
        except Exception as e:
            logger.error(f"Error in check_trade: {e}")
            raise


class TrustSafetyLayer:
    """
    Complete Trust & Safety Layer.
    
    Features:
    - Every trade logged and scored
    - Every strategy change explained
    - Every evolution audited
    - Failed modules quarantined
    - Suspicious behavior flagged
    - Complete audit trail
    - Compliance reporting
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Components
            db_path = self.config.get('db_path', 'audit_log.db')
            self.audit_logger = AuditLogger(db_path)
            self.trade_scorer = TradeScorer(config)
            self.anomaly_detector = AnomalyDetector(config)
            self.quarantine_manager = QuarantineManager(self.audit_logger)
            self.compliance_checker = ComplianceChecker(config)
        
            # Trust scores
            self.module_trust: Dict[str, TrustScore] = {}
            self.strategy_trust: Dict[str, TrustScore] = {}
        
            # Session tracking
            self.session_id = str(uuid.uuid4())[:8]
        
            logger.info("TrustSafetyLayer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def audit_trade(
        self,
        trade_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        signal_source: str = "",
        signal_confidence: float = 0.0,
        strategy_name: str = "",
        risk_score: float = 0.0,
        position_size_pct: float = 0.0,
        slippage: float = 0.0,
        execution_time_ms: float = 0.0,
        venue: str = "",
        pnl: float = 0.0
    ) -> TradeAudit:
        """Audit a trade"""
        
        # Determine outcome
        try:
            if pnl > 0:
                outcome = 'win'
            elif pnl < 0:
                outcome = 'loss'
            else:
                outcome = 'breakeven'
        
            # Create trade audit
            trade = TradeAudit(
                trade_id=trade_id,
                timestamp=datetime.now(),
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                signal_source=signal_source,
                signal_confidence=signal_confidence,
                strategy_name=strategy_name,
                risk_score=risk_score,
                position_size_pct=position_size_pct,
                portfolio_impact=quantity * price,
                slippage=slippage,
                execution_time_ms=execution_time_ms,
                venue=venue,
                pnl=pnl,
                outcome=outcome
            )
        
            # Check compliance
            compliant, violations = self.compliance_checker.check_trade(trade)
            trade.compliant = compliant
            trade.compliance_notes = "; ".join(violations) if violations else "Compliant"
        
            # Score trade
            score, explanation = self.trade_scorer.score_trade(trade)
            trade.trade_score = score
            trade.explanation = explanation
        
            # Log trade
            self.audit_logger.log_trade(trade)
        
            # Check for anomalies
            anomalies = self.anomaly_detector.detect_anomalies(trade)
            self.anomaly_detector.add_trade(trade)
        
            # Handle anomalies
            for anomaly in anomalies:
                self._handle_anomaly(anomaly, trade)
        
            # Log event
            event = AuditEvent(
                event_id=str(uuid.uuid4())[:8],
                event_type=AuditEventType.TRADE_EXECUTED,
                timestamp=datetime.now(),
                description=f"Trade executed: {side} {quantity} {symbol} @ {price}",
                details={
                    'trade_id': trade_id,
                    'score': score,
                    'compliant': compliant
                },
                strategy_name=strategy_name,
                symbol=symbol,
                severity=SeverityLevel.INFO if compliant else SeverityLevel.WARNING,
                session_id=self.session_id
            )
            self.audit_logger.log_event(event)
        
            return trade
        except Exception as e:
            logger.error(f"Error in audit_trade: {e}")
            raise
    
    def _handle_anomaly(self, anomaly: Dict, trade: TradeAudit):
        """Handle detected anomaly"""
        
        try:
            severity = anomaly.get('severity', 'low')
        
            # Log anomaly event
            event = AuditEvent(
                event_id=str(uuid.uuid4())[:8],
                event_type=AuditEventType.ANOMALY_DETECTED,
                timestamp=datetime.now(),
                description=anomaly.get('description', 'Anomaly detected'),
                details=anomaly,
                strategy_name=trade.strategy_name,
                symbol=trade.symbol,
                severity=SeverityLevel.CRITICAL if severity == 'critical' else SeverityLevel.WARNING,
                session_id=self.session_id
            )
            self.audit_logger.log_event(event)
        
            # Quarantine if critical
            if severity == 'critical':
                self.quarantine_manager.quarantine_module(
                    trade.strategy_name,
                    QuarantineReason.ANOMALOUS_BEHAVIOR,
                    anomaly.get('description', '')
                )
        except Exception as e:
            logger.error(f"Error in _handle_anomaly: {e}")
            raise
    
    def audit_strategy_change(
        self,
        strategy_name: str,
        change_type: str,
        previous_value: Any,
        new_value: Any,
        explanation: str = "",
        justification: str = ""
    ) -> StrategyChangeRecord:
        """Audit a strategy change"""
        
        try:
            change = StrategyChangeRecord(
                change_id=str(uuid.uuid4())[:8],
                timestamp=datetime.now(),
                strategy_name=strategy_name,
                change_type=change_type,
                previous_value=previous_value,
                new_value=new_value,
                explanation=explanation,
                justification=justification,
                expected_impact="To be evaluated",
                risk_assessment="Pending review"
            )
        
            self.audit_logger.log_strategy_change(change)
        
            # Log event
            event = AuditEvent(
                event_id=str(uuid.uuid4())[:8],
                event_type=AuditEventType.STRATEGY_CHANGED,
                timestamp=datetime.now(),
                description=f"Strategy {strategy_name} changed: {change_type}",
                details={
                    'change_type': change_type,
                    'explanation': explanation
                },
                strategy_name=strategy_name,
                severity=SeverityLevel.INFO,
                session_id=self.session_id
            )
            self.audit_logger.log_event(event)
        
            return change
        except Exception as e:
            logger.error(f"Error in audit_strategy_change: {e}")
            raise
    
    def audit_evolution_cycle(
        self,
        cycle_id: str,
        changes_made: List[Dict],
        performance_before: Dict,
        performance_after: Dict
    ):
        """Audit an evolution cycle"""
        
        try:
            event = AuditEvent(
                event_id=str(uuid.uuid4())[:8],
                event_type=AuditEventType.EVOLUTION_CYCLE,
                timestamp=datetime.now(),
                description=f"Evolution cycle {cycle_id} completed",
                details={
                    'cycle_id': cycle_id,
                    'changes_count': len(changes_made),
                    'changes': changes_made,
                    'performance_before': performance_before,
                    'performance_after': performance_after
                },
                severity=SeverityLevel.INFO,
                session_id=self.session_id
            )
            self.audit_logger.log_event(event)
        except Exception as e:
            logger.error(f"Error in audit_evolution_cycle: {e}")
            raise
    
    def quarantine_module(
        self,
        module_name: str,
        reason: QuarantineReason,
        reason_details: str = ""
    ) -> QuarantinedModule:
        """Quarantine a module"""
        return self.quarantine_manager.quarantine_module(
            module_name, reason, reason_details
        )
    
    def restore_module(self, module_name: str, reason: str = "") -> bool:
        """Restore a quarantined module"""
        return self.quarantine_manager.restore_module(module_name, reason)
    
    def is_module_quarantined(self, module_name: str) -> bool:
        """Check if module is quarantined"""
        return self.quarantine_manager.is_quarantined(module_name)
    
    def get_trust_score(self, module_name: str) -> TrustScore:
        """Get trust score for module"""
        return self.module_trust.get(module_name, TrustScore.NEUTRAL)
    
    def update_trust_score(self, module_name: str, score: TrustScore):
        """Update trust score for module"""
        try:
            self.module_trust[module_name] = score
        except Exception as e:
            logger.error(f"Error in update_trust_score: {e}")
            raise
    
    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate compliance report"""
        
        # Get events in date range
        try:
            events = self.audit_logger.get_recent_events(limit=10000)
        
            filtered_events = [
                e for e in events
                if start_date <= e.timestamp <= end_date
            ]
        
            # Analyze events
            trade_events = [e for e in filtered_events if e.event_type == AuditEventType.TRADE_EXECUTED]
            anomaly_events = [e for e in filtered_events if e.event_type == AuditEventType.ANOMALY_DETECTED]
            quarantine_events = [e for e in filtered_events if e.event_type == AuditEventType.MODULE_QUARANTINED]
        
            return {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'summary': {
                    'total_events': len(filtered_events),
                    'total_trades': len(trade_events),
                    'anomalies_detected': len(anomaly_events),
                    'modules_quarantined': len(quarantine_events)
                },
                'compliance_status': 'COMPLIANT' if len(anomaly_events) == 0 else 'REVIEW_REQUIRED',
                'quarantined_modules': self.quarantine_manager.get_quarantined_modules()
            }
        except Exception as e:
            logger.error(f"Error in generate_compliance_report: {e}")
            raise
    
    def get_audit_trail(
        self,
        event_type: Optional[AuditEventType] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get audit trail"""
        return self.audit_logger.get_recent_events(event_type=event_type, limit=limit)


# Factory function
def create_trust_safety(config: Optional[Dict] = None) -> TrustSafetyLayer:
    """Create and return a TrustSafetyLayer instance"""
    return TrustSafetyLayer(config)
