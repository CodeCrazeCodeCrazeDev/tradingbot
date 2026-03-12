"""
Regulatory Compliance Monitor - Answers Q931-Q970
=================================================

Critical Question Q931: What regulations apply to your trading, and are you compliant?
Critical Question Q941: What constraints does your broker impose?
Critical Question Q961: What reporting is required, and are you meeting requirements?

This module provides:
1. Regulatory rule enforcement
2. Broker constraint monitoring
3. Trade reporting
4. Compliance audit trail
5. Violation detection and alerting
"""

import logging
import threading
import json
from datetime import datetime, timedelta, time
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)


class RegulatoryRegime(Enum):
    """Regulatory regimes"""
    SEC = "sec"           # US Securities
    CFTC = "cftc"         # US Commodities/Futures
    FINRA = "finra"       # US Broker-Dealer
    MiFID_II = "mifid2"   # EU Markets
    FCA = "fca"           # UK Financial Conduct
    ASIC = "asic"         # Australia
    CRYPTO = "crypto"     # Cryptocurrency (varies)
    NONE = "none"         # No specific regulation


class ViolationType(Enum):
    """Types of compliance violations"""
    PATTERN_DAY_TRADER = "pattern_day_trader"
    WASH_SALE = "wash_sale"
    POSITION_LIMIT = "position_limit"
    MARGIN_VIOLATION = "margin_violation"
    TRADING_HOURS = "trading_hours"
    SYMBOL_RESTRICTION = "symbol_restriction"
    ORDER_SIZE_LIMIT = "order_size_limit"
    RATE_LIMIT = "rate_limit"
    REPORTING_FAILURE = "reporting_failure"
    BEST_EXECUTION = "best_execution"


class ViolationSeverity(Enum):
    """Violation severity levels"""
    INFO = "info"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL = "critical"


@dataclass
class ComplianceRule:
    """A compliance rule to enforce"""
    rule_id: str
    name: str
    description: str
    regime: RegulatoryRegime
    violation_type: ViolationType
    check_function: Optional[Callable] = None
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceViolation:
    """A detected compliance violation"""
    violation_id: str
    timestamp: datetime
    rule_id: str
    violation_type: ViolationType
    severity: ViolationSeverity
    description: str
    details: Dict[str, Any]
    trade_id: Optional[str] = None
    symbol: Optional[str] = None
    remediation: Optional[str] = None
    acknowledged: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'violation_id': self.violation_id,
            'timestamp': self.timestamp.isoformat(),
            'rule_id': self.rule_id,
            'violation_type': self.violation_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'details': self.details,
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'remediation': self.remediation,
            'acknowledged': self.acknowledged
        }


@dataclass
class BrokerConstraint:
    """Broker-imposed constraint"""
    constraint_id: str
    name: str
    description: str
    constraint_type: str
    value: Any
    enforced: bool = True


@dataclass
class TradeReport:
    """Trade report for regulatory reporting"""
    report_id: str
    trade_id: str
    timestamp: datetime
    symbol: str
    direction: str
    quantity: float
    price: float
    venue: str
    order_type: str
    execution_time_ms: float
    reported: bool = False
    reported_at: Optional[datetime] = None
    report_destination: Optional[str] = None


class RegulatoryComplianceMonitor:
    """
    Monitors and enforces regulatory compliance.
    
    Addresses critical questions:
    - Q931: Regulatory compliance
    - Q941: Broker constraints
    - Q961: Reporting requirements
    
    Features:
    - Pattern Day Trader (PDT) rule enforcement
    - Wash sale detection
    - Position limit monitoring
    - Trading hours enforcement
    - Trade reporting
    - Audit trail
    """
    
    def __init__(
        self,
        regime: RegulatoryRegime = RegulatoryRegime.SEC,
        broker_constraints: Optional[List[BrokerConstraint]] = None,
        db_path: str = "compliance.db",
        on_violation: Optional[Callable] = None,
        on_warning: Optional[Callable] = None
    ):
        """
        Initialize compliance monitor.
        
        Args:
            regime: Primary regulatory regime
            broker_constraints: List of broker constraints
            db_path: Path to compliance database
            on_violation: Callback when violation detected
            on_warning: Callback for warnings
        """
        self.regime = regime
        self.broker_constraints = broker_constraints or []
        self.db_path = Path(db_path)
        self.on_violation = on_violation
        self.on_warning = on_warning
        
        # State
        self._lock = threading.RLock()
        self._rules: Dict[str, ComplianceRule] = {}
        self._violations: List[ComplianceViolation] = []
        self._trade_reports: List[TradeReport] = []
        
        # Day trading tracking
        self._day_trades: Dict[str, List[datetime]] = {}  # symbol -> trade times
        self._day_trade_count = 0
        self._last_day_trade_reset = datetime.now().date()
        
        # Wash sale tracking
        self._recent_sales: Dict[str, List[Dict]] = {}  # symbol -> sales
        
        # Initialize database
        self._init_database()
        
        # Load default rules
        self._load_default_rules()
        
        # Add broker constraints as rules
        for constraint in self.broker_constraints:
            self._add_broker_constraint_rule(constraint)
        
        logger.info(f"RegulatoryComplianceMonitor initialized for {regime.value}")
    
    def _init_database(self):
        """Initialize compliance database"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    violation_id TEXT UNIQUE,
                    timestamp TEXT,
                    rule_id TEXT,
                    violation_type TEXT,
                    severity TEXT,
                    description TEXT,
                    details TEXT,
                    trade_id TEXT,
                    symbol TEXT,
                    remediation TEXT,
                    acknowledged INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trade_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT UNIQUE,
                    trade_id TEXT,
                    timestamp TEXT,
                    symbol TEXT,
                    direction TEXT,
                    quantity REAL,
                    price REAL,
                    venue TEXT,
                    order_type TEXT,
                    execution_time_ms REAL,
                    reported INTEGER DEFAULT 0,
                    reported_at TEXT,
                    report_destination TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS day_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    symbol TEXT,
                    trade_time TEXT,
                    buy_order_id TEXT,
                    sell_order_id TEXT
                )
            """)
            
            conn.commit()
    
    def _load_default_rules(self):
        """Load default compliance rules based on regime"""
        
        # Pattern Day Trader Rule (SEC/FINRA)
        if self.regime in (RegulatoryRegime.SEC, RegulatoryRegime.FINRA):
            self._rules['pdt_rule'] = ComplianceRule(
                rule_id='pdt_rule',
                name='Pattern Day Trader Rule',
                description='No more than 3 day trades in 5 business days for accounts under $25,000',
                regime=RegulatoryRegime.FINRA,
                violation_type=ViolationType.PATTERN_DAY_TRADER,
                parameters={'max_day_trades': 3, 'period_days': 5, 'min_equity': 25000}
            )
        
        # Wash Sale Rule (SEC)
        if self.regime == RegulatoryRegime.SEC:
            self._rules['wash_sale'] = ComplianceRule(
                rule_id='wash_sale',
                name='Wash Sale Rule',
                description='Cannot claim loss if substantially identical security bought within 30 days',
                regime=RegulatoryRegime.SEC,
                violation_type=ViolationType.WASH_SALE,
                parameters={'wash_period_days': 30}
            )
        
        # Trading Hours
        self._rules['trading_hours'] = ComplianceRule(
            rule_id='trading_hours',
            name='Trading Hours',
            description='Trading only during market hours',
            regime=self.regime,
            violation_type=ViolationType.TRADING_HOURS,
            parameters={
                'market_open': '09:30',
                'market_close': '16:00',
                'timezone': 'US/Eastern',
                'allow_premarket': False,
                'allow_afterhours': False
            }
        )
        
        # Position Limits
        self._rules['position_limit'] = ComplianceRule(
            rule_id='position_limit',
            name='Position Limit',
            description='Maximum position size per symbol',
            regime=self.regime,
            violation_type=ViolationType.POSITION_LIMIT,
            parameters={'max_position_pct': 0.25}  # 25% of portfolio
        )
        
        # Order Rate Limit
        self._rules['rate_limit'] = ComplianceRule(
            rule_id='rate_limit',
            name='Order Rate Limit',
            description='Maximum orders per minute',
            regime=self.regime,
            violation_type=ViolationType.RATE_LIMIT,
            parameters={'max_orders_per_minute': 60}
        )
    
    def _add_broker_constraint_rule(self, constraint: BrokerConstraint):
        """Add a broker constraint as a compliance rule"""
        rule_id = f"broker_{constraint.constraint_id}"
        
        self._rules[rule_id] = ComplianceRule(
            rule_id=rule_id,
            name=f"Broker: {constraint.name}",
            description=constraint.description,
            regime=RegulatoryRegime.NONE,
            violation_type=ViolationType.SYMBOL_RESTRICTION,
            parameters={'constraint': constraint}
        )
    
    def check_pre_trade(
        self,
        symbol: str,
        direction: str,
        quantity: float,
        price: float,
        equity: float,
        existing_position: float = 0
    ) -> tuple:
        """
        Check compliance before executing a trade.
        
        This is the answer to Q931: What regulations apply and are you compliant?
        
        Args:
            symbol: Trading symbol
            direction: 'buy' or 'sell'
            quantity: Order quantity
            price: Order price
            equity: Current account equity
            existing_position: Current position in symbol
            
        Returns:
            Tuple of (can_trade, violations)
        """
        violations = []
        
        # Check PDT rule
        if 'pdt_rule' in self._rules and self._rules['pdt_rule'].enabled:
            pdt_violation = self._check_pdt_rule(symbol, direction, equity)
            if pdt_violation:
                violations.append(pdt_violation)
        
        # Check position limits
        if 'position_limit' in self._rules and self._rules['position_limit'].enabled:
            position_violation = self._check_position_limit(
                symbol, quantity, price, equity, existing_position
            )
            if position_violation:
                violations.append(position_violation)
        
        # Check trading hours
        if 'trading_hours' in self._rules and self._rules['trading_hours'].enabled:
            hours_violation = self._check_trading_hours()
            if hours_violation:
                violations.append(hours_violation)
        
        # Check wash sale (for sells at a loss)
        if direction == 'sell' and 'wash_sale' in self._rules:
            wash_violation = self._check_wash_sale(symbol)
            if wash_violation:
                violations.append(wash_violation)
        
        # Check broker constraints
        for rule_id, rule in self._rules.items():
            if rule_id.startswith('broker_') and rule.enabled:
                constraint = rule.parameters.get('constraint')
                if constraint:
                    broker_violation = self._check_broker_constraint(
                        constraint, symbol, quantity, price
                    )
                    if broker_violation:
                        violations.append(broker_violation)
        
        # Store violations
        for violation in violations:
            self._record_violation(violation)
        
        # Determine if can trade
        critical_violations = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
        can_trade = len(critical_violations) == 0
        
        return can_trade, violations
    
    def _check_pdt_rule(
        self,
        symbol: str,
        direction: str,
        equity: float
    ) -> Optional[ComplianceViolation]:
        """Check Pattern Day Trader rule"""
        rule = self._rules['pdt_rule']
        params = rule.parameters
        
        # PDT only applies to accounts under $25,000
        if equity >= params['min_equity']:
            return None
        
        # Reset day trade count if new day
        today = datetime.now().date()
        if today != self._last_day_trade_reset:
            self._day_trade_count = self._count_recent_day_trades(params['period_days'])
            self._last_day_trade_reset = today
        
        # Check if this would be a day trade
        if direction == 'sell' and symbol in self._day_trades:
            # Check if bought today
            today_trades = [
                t for t in self._day_trades[symbol]
                if t.date() == today
            ]
            if today_trades:
                # This would be a day trade
                if self._day_trade_count >= params['max_day_trades']:
                    return ComplianceViolation(
                        violation_id=f"pdt_{datetime.now().timestamp()}",
                        timestamp=datetime.now(),
                        rule_id='pdt_rule',
                        violation_type=ViolationType.PATTERN_DAY_TRADER,
                        severity=ViolationSeverity.CRITICAL,
                        description=f"Would exceed {params['max_day_trades']} day trades in {params['period_days']} days",
                        details={
                            'current_day_trades': self._day_trade_count,
                            'max_allowed': params['max_day_trades'],
                            'equity': equity,
                            'min_equity_required': params['min_equity']
                        },
                        symbol=symbol,
                        remediation="Wait for day trade count to reset or increase account equity above $25,000"
                    )
        
        return None
    
    def _check_position_limit(
        self,
        symbol: str,
        quantity: float,
        price: float,
        equity: float,
        existing_position: float
    ) -> Optional[ComplianceViolation]:
        """Check position size limits"""
        rule = self._rules['position_limit']
        max_pct = rule.parameters['max_position_pct']
        
        # Calculate new position value
        new_position_value = (existing_position + quantity) * price
        position_pct = new_position_value / equity if equity > 0 else 1.0
        
        if position_pct > max_pct:
            return ComplianceViolation(
                violation_id=f"position_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                rule_id='position_limit',
                violation_type=ViolationType.POSITION_LIMIT,
                severity=ViolationSeverity.WARNING,
                description=f"Position would be {position_pct:.1%} of portfolio (max: {max_pct:.1%})",
                details={
                    'position_value': new_position_value,
                    'position_pct': position_pct,
                    'max_pct': max_pct,
                    'equity': equity
                },
                symbol=symbol,
                remediation="Reduce position size"
            )
        
        return None
    
    def _check_trading_hours(self) -> Optional[ComplianceViolation]:
        """Check if within trading hours"""
        rule = self._rules['trading_hours']
        params = rule.parameters
        
        now = datetime.now()
        current_time = now.time()
        
        market_open = datetime.strptime(params['market_open'], '%H:%M').time()
        market_close = datetime.strptime(params['market_close'], '%H:%M').time()
        
        # Check if weekend
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return ComplianceViolation(
                violation_id=f"hours_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                rule_id='trading_hours',
                violation_type=ViolationType.TRADING_HOURS,
                severity=ViolationSeverity.CRITICAL,
                description="Market is closed on weekends",
                details={'day': now.strftime('%A')},
                remediation="Wait for market to open"
            )
        
        # Check time
        if current_time < market_open:
            if not params.get('allow_premarket', False):
                return ComplianceViolation(
                    violation_id=f"hours_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    rule_id='trading_hours',
                    violation_type=ViolationType.TRADING_HOURS,
                    severity=ViolationSeverity.WARNING,
                    description=f"Pre-market trading not allowed (opens at {params['market_open']})",
                    details={'current_time': current_time.strftime('%H:%M'), 'market_open': params['market_open']},
                    remediation="Wait for market to open"
                )
        
        if current_time > market_close:
            if not params.get('allow_afterhours', False):
                return ComplianceViolation(
                    violation_id=f"hours_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    rule_id='trading_hours',
                    violation_type=ViolationType.TRADING_HOURS,
                    severity=ViolationSeverity.WARNING,
                    description=f"After-hours trading not allowed (closed at {params['market_close']})",
                    details={'current_time': current_time.strftime('%H:%M'), 'market_close': params['market_close']},
                    remediation="Wait for next trading day"
                )
        
        return None
    
    def _check_wash_sale(self, symbol: str) -> Optional[ComplianceViolation]:
        """Check for potential wash sale"""
        rule = self._rules.get('wash_sale')
        if not rule:
            return None
        
        wash_period = rule.parameters['wash_period_days']
        cutoff = datetime.now() - timedelta(days=wash_period)
        
        # Check recent sales
        if symbol in self._recent_sales:
            recent = [
                s for s in self._recent_sales[symbol]
                if s['timestamp'] > cutoff and s.get('loss', False)
            ]
            if recent:
                return ComplianceViolation(
                    violation_id=f"wash_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    rule_id='wash_sale',
                    violation_type=ViolationType.WASH_SALE,
                    severity=ViolationSeverity.INFO,
                    description=f"Potential wash sale - sold {symbol} at loss within {wash_period} days",
                    details={'recent_loss_sales': len(recent), 'wash_period_days': wash_period},
                    symbol=symbol,
                    remediation="Consult tax advisor - loss may not be deductible"
                )
        
        return None
    
    def _check_broker_constraint(
        self,
        constraint: BrokerConstraint,
        symbol: str,
        quantity: float,
        price: float
    ) -> Optional[ComplianceViolation]:
        """Check broker-specific constraint"""
        
        if constraint.constraint_type == 'restricted_symbol':
            if symbol in constraint.value:
                return ComplianceViolation(
                    violation_id=f"broker_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    rule_id=f"broker_{constraint.constraint_id}",
                    violation_type=ViolationType.SYMBOL_RESTRICTION,
                    severity=ViolationSeverity.CRITICAL,
                    description=f"Symbol {symbol} is restricted by broker",
                    details={'constraint': constraint.name},
                    symbol=symbol,
                    remediation="Choose a different symbol"
                )
        
        elif constraint.constraint_type == 'max_order_value':
            order_value = quantity * price
            if order_value > constraint.value:
                return ComplianceViolation(
                    violation_id=f"broker_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    rule_id=f"broker_{constraint.constraint_id}",
                    violation_type=ViolationType.ORDER_SIZE_LIMIT,
                    severity=ViolationSeverity.CRITICAL,
                    description=f"Order value ${order_value:.2f} exceeds broker limit ${constraint.value:.2f}",
                    details={'order_value': order_value, 'limit': constraint.value},
                    remediation="Reduce order size"
                )
        
        return None
    
    def _count_recent_day_trades(self, days: int) -> int:
        """Count day trades in recent period"""
        cutoff = datetime.now() - timedelta(days=days)
        count = 0
        
        for symbol, trades in self._day_trades.items():
            # Group by date
            by_date = {}
            for t in trades:
                if t > cutoff:
                    date_key = t.date()
                    if date_key not in by_date:
                        by_date[date_key] = []
                    by_date[date_key].append(t)
            
            # Count days with round trips
            for date_key, day_trades in by_date.items():
                if len(day_trades) >= 2:  # Buy and sell same day
                    count += 1
        
        return count
    
    def record_trade(
        self,
        trade_id: str,
        symbol: str,
        direction: str,
        quantity: float,
        price: float,
        venue: str,
        order_type: str,
        execution_time_ms: float
    ) -> TradeReport:
        """
        Record a trade for compliance tracking and reporting.
        
        This is the answer to Q961: What reporting is required?
        """
        report = TradeReport(
            report_id=f"rpt_{trade_id}",
            trade_id=trade_id,
            timestamp=datetime.now(),
            symbol=symbol,
            direction=direction,
            quantity=quantity,
            price=price,
            venue=venue,
            order_type=order_type,
            execution_time_ms=execution_time_ms
        )
        
        with self._lock:
            self._trade_reports.append(report)
            
            # Track for day trading
            if symbol not in self._day_trades:
                self._day_trades[symbol] = []
            self._day_trades[symbol].append(datetime.now())
            
            # Track for wash sales
            if direction == 'sell':
                if symbol not in self._recent_sales:
                    self._recent_sales[symbol] = []
                self._recent_sales[symbol].append({
                    'timestamp': datetime.now(),
                    'quantity': quantity,
                    'price': price,
                    'loss': False  # Would need P&L info to determine
                })
        
        # Persist
        self._persist_trade_report(report)
        
        return report
    
    def _record_violation(self, violation: ComplianceViolation):
        """Record a violation"""
        with self._lock:
            pass
        try:
            self._violations.append(violation)
        
        # Persist
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO violations
                    (violation_id, timestamp, rule_id, violation_type, severity,
                     description, details, trade_id, symbol, remediation, acknowledged)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    violation.violation_id,
                    violation.timestamp.isoformat(),
                    violation.rule_id,
                    violation.violation_type.value,
                    violation.severity.value,
                    violation.description,
                    json.dumps(violation.details),
                    violation.trade_id,
                    violation.symbol,
                    violation.remediation,
                    1 if violation.acknowledged else 0
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error persisting violation: {e}")
        
        # Callbacks
        if violation.severity in (ViolationSeverity.CRITICAL, ViolationSeverity.VIOLATION):
            if self.on_violation:
                try:
                    self.on_violation(violation)
                except Exception as e:
                    logger.error(f"Violation callback error: {e}")
        else:
            if self.on_warning:
                try:
                    self.on_warning(violation)
                except Exception as e:
                    logger.error(f"Warning callback error: {e}")
    
    def _persist_trade_report(self, report: TradeReport):
        """Persist trade report to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO trade_reports
                    (report_id, trade_id, timestamp, symbol, direction, quantity,
                     price, venue, order_type, execution_time_ms, reported, reported_at, report_destination)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report.report_id,
                    report.trade_id,
                    report.timestamp.isoformat(),
                    report.symbol,
                    report.direction,
                    report.quantity,
                    report.price,
                    report.venue,
                    report.order_type,
                    report.execution_time_ms,
                    1 if report.reported else 0,
                    report.reported_at.isoformat() if report.reported_at else None,
                    report.report_destination
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error persisting trade report: {e}")
    
    def get_violations(
        self,
        severity: Optional[ViolationSeverity] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100
    ) -> List[ComplianceViolation]:
        """Get recorded violations"""
        with self._lock:
            violations = self._violations[-limit:]
            
            if severity:
                violations = [v for v in violations if v.severity == severity]
            
            if acknowledged is not None:
                violations = [v for v in violations if v.acknowledged == acknowledged]
            
            return violations
    
    def acknowledge_violation(self, violation_id: str) -> bool:
        """Acknowledge a violation"""
        with self._lock:
            for violation in self._violations:
                if violation.violation_id == violation_id:
                    violation.acknowledged = True
                    
                    try:
                        # Update database
                        with sqlite3.connect(self.db_path) as conn:
                            conn.execute(
                                "UPDATE violations SET acknowledged = 1 WHERE violation_id = ?",
                                (violation_id,)
                            )
                            conn.commit()
                    except Exception as e:
                        logger.error(f"Error acknowledging violation: {e}")
                    
                    return True
        
        return False
    
    def get_compliance_status(self) -> Dict:
        """Get current compliance status"""
        with self._lock:
            unacknowledged = [v for v in self._violations if not v.acknowledged]
            critical = [v for v in unacknowledged if v.severity == ViolationSeverity.CRITICAL]
            
            return {
                'regime': self.regime.value,
                'rules_count': len(self._rules),
                'enabled_rules': len([r for r in self._rules.values() if r.enabled]),
                'total_violations': len(self._violations),
                'unacknowledged_violations': len(unacknowledged),
                'critical_violations': len(critical),
                'day_trade_count': self._day_trade_count,
                'trade_reports_pending': len([r for r in self._trade_reports if not r.reported]),
                'is_compliant': len(critical) == 0
            }
    
    def get_rules(self) -> List[Dict]:
        """Get all compliance rules"""
        return [
            {
                'rule_id': r.rule_id,
                'name': r.name,
                'description': r.description,
                'regime': r.regime.value,
                'enabled': r.enabled
            }
            for r in self._rules.values()
        ]
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a compliance rule"""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a compliance rule (use with caution)"""
        if rule_id in self._rules:
            logger.warning(f"Disabling compliance rule: {rule_id}")
            self._rules[rule_id].enabled = False
            return True
        return False
