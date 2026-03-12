"""
Compliance monitoring for AlphaAlgo 2.0
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

Set up logger
logger = logging.getLogger(__name__)


class ViolationType(Enum):
    """Types of compliance violations."""
    POSITION_LIMIT = "position_limit"
    TRADE_FREQUENCY = "trade_frequency"
    WASH_SALE = "wash_sale"
    MARKET_HOURS = "market_hours"
    RESTRICTED_SYMBOL = "restricted_symbol"
    LEVERAGE_LIMIT = "leverage_limit"
    CONCENTRATION = "concentration"


@dataclass
class ComplianceViolation:
    """Compliance violation record."""
    type: ViolationType
    symbol: str
    timestamp: datetime
    description: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    action_taken: str


class ComplianceMonitor:
    """
    Monitors trading activity for compliance violations.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Position limits
        self.max_position_size = self.config.get('max_position_size', 1000000)
        self.max_positions = self.config.get('max_positions', 10)
        
        # Trade frequency limits
        self.max_trades_per_hour = self.config.get('max_trades_per_hour', 100)
        self.max_trades_per_day = self.config.get('max_trades_per_day', 500)
        
        # Wash sale period
        self.wash_sale_period = self.config.get('wash_sale_period', 30)  # days
        
        # Restricted symbols
        self.restricted_symbols = set(self.config.get('restricted_symbols', []))
        
        # Leverage limits
        self.max_leverage = self.config.get('max_leverage', 10.0)
        
        # Concentration limits
        self.max_concentration = self.config.get('max_concentration', 0.25)  # 25%
        
        # Trading hours
        self.market_open = self.config.get('market_open', 9)  # 9 AM
        self.market_close = self.config.get('market_close', 17)  # 5 PM
        
        # Violation tracking
        self.violations = []
        self.trade_history = []
        
        logger.info("✅ Compliance Monitor initialized")
    
    def check_position_limit(self, symbol: str, position_size: float) -> tuple:
        """
        Check if position size exceeds limits.
        
        Returns:
            (is_compliant, violation)
        """
        if position_size > self.max_position_size:
            violation = ComplianceViolation(
                type=ViolationType.POSITION_LIMIT,
                symbol=symbol,
                timestamp=datetime.now(),
                description=f"Position size {position_size} exceeds limit {self.max_position_size}",
                severity="HIGH",
                action_taken="Order rejected"
            )
            self.violations.append(violation)
            logger.warning(f"⚠️ Position limit violation: {symbol}")
            return False, violation
        
        return True, None
    
    def check_trade_frequency(self, symbol: str) -> tuple:
        """
        Check if trade frequency exceeds limits.
        
        Returns:
            (is_compliant, violation)
        """
        now = datetime.now()
        
        # Count trades in last hour
        hour_ago = now - timedelta(hours=1)
        trades_last_hour = len([
            t for t in self.trade_history
            if t['timestamp'] > hour_ago and t['symbol'] == symbol
        ])
        
        if trades_last_hour >= self.max_trades_per_hour:
            violation = ComplianceViolation(
                type=ViolationType.TRADE_FREQUENCY,
                symbol=symbol,
                timestamp=now,
                description=f"Trade frequency {trades_last_hour} exceeds hourly limit {self.max_trades_per_hour}",
                severity="MEDIUM",
                action_taken="Order rejected"
            )
            self.violations.append(violation)
            logger.warning(f"⚠️ Trade frequency violation: {symbol}")
            return False, violation
        
        # Count trades today
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        trades_today = len([
            t for t in self.trade_history
            if t['timestamp'] > today and t['symbol'] == symbol
        ])
        
        if trades_today >= self.max_trades_per_day:
            violation = ComplianceViolation(
                type=ViolationType.TRADE_FREQUENCY,
                symbol=symbol,
                timestamp=now,
                description=f"Trade frequency {trades_today} exceeds daily limit {self.max_trades_per_day}",
                severity="HIGH",
                action_taken="Order rejected"
            )
            self.violations.append(violation)
            logger.warning(f"⚠️ Daily trade limit violation: {symbol}")
            return False, violation
        
        return True, None
    
    def check_wash_sale(self, symbol: str, side: str) -> tuple:
        """
        Check for potential wash sale.
        
        Returns:
            (is_compliant, violation)
        """
        now = datetime.now()
        wash_sale_start = now - timedelta(days=self.wash_sale_period)
        
        # Find recent opposite trades
        recent_trades = [
            t for t in self.trade_history
            if t['symbol'] == symbol
            and t['timestamp'] > wash_sale_start
            and t['side'] != side
        ]
        
        if recent_trades:
            violation = ComplianceViolation(
                type=ViolationType.WASH_SALE,
                symbol=symbol,
                timestamp=now,
                description=f"Potential wash sale detected within {self.wash_sale_period} days",
                severity="MEDIUM",
                action_taken="Warning issued"
            )
            self.violations.append(violation)
            logger.warning(f"⚠️ Potential wash sale: {symbol}")
            return False, violation
        
        return True, None
    
    def check_market_hours(self) -> tuple:
        """
        Check if trading is within market hours.
        
        Returns:
            (is_compliant, violation)
        """
        now = datetime.now()
        current_hour = now.hour
        
        if not (self.market_open <= current_hour < self.market_close):
            violation = ComplianceViolation(
                type=ViolationType.MARKET_HOURS,
                symbol="ALL",
                timestamp=now,
                description=f"Trading outside market hours ({self.market_open}-{self.market_close})",
                severity="LOW",
                action_taken="Order rejected"
            )
            self.violations.append(violation)
            logger.warning("⚠️ Trading outside market hours")
            return False, violation
        
        return True, None
    
    def check_restricted_symbol(self, symbol: str) -> tuple:
        """
        Check if symbol is restricted.
        
        Returns:
            (is_compliant, violation)
        """
        if symbol in self.restricted_symbols:
            violation = ComplianceViolation(
                type=ViolationType.RESTRICTED_SYMBOL,
                symbol=symbol,
                timestamp=datetime.now(),
                description=f"Symbol {symbol} is restricted",
                severity="CRITICAL",
                action_taken="Order rejected"
            )
            self.violations.append(violation)
            logger.warning(f"⚠️ Restricted symbol: {symbol}")
            return False, violation
        
        return True, None
    
    def check_leverage(self, equity: float, exposure: float) -> tuple:
        """
        Check if leverage exceeds limits.
        
        Returns:
            (is_compliant, violation)
        """
        if equity == 0:
            return True, None
        
        leverage = exposure / equity
        
        if leverage > self.max_leverage:
            violation = ComplianceViolation(
                type=ViolationType.LEVERAGE_LIMIT,
                symbol="PORTFOLIO",
                timestamp=datetime.now(),
                description=f"Leverage {leverage:.2f}x exceeds limit {self.max_leverage}x",
                severity="HIGH",
                action_taken="Order rejected"
            )
            self.violations.append(violation)
            logger.warning(f"⚠️ Leverage limit violation: {leverage:.2f}x")
            return False, violation
        
        return True, None
    
    def check_concentration(
        self,
        symbol: str,
        position_value: float,
        portfolio_value: float
    ) -> tuple:
        """
        Check if position concentration exceeds limits.
        
        Returns:
            (is_compliant, violation)
        """
        if portfolio_value == 0:
            return True, None
        
        concentration = position_value / portfolio_value
        
        if concentration > self.max_concentration:
            violation = ComplianceViolation(
                type=ViolationType.CONCENTRATION,
                symbol=symbol,
                timestamp=datetime.now(),
                description=f"Concentration {concentration:.1%} exceeds limit {self.max_concentration:.1%}",
                severity="MEDIUM",
                action_taken="Order rejected"
            )
            self.violations.append(violation)
            logger.warning(f"⚠️ Concentration violation: {symbol}")
            return False, violation
        
        return True, None
    
    def check_all(
        self,
        symbol: str,
        side: str,
        position_size: float,
        equity: float = None,
        exposure: float = None,
        portfolio_value: float = None
    ) -> tuple:
        """
        Run all compliance checks.
        
        Returns:
            (is_compliant, violations)
        """
        violations = []
        
        # Check restricted symbol
        is_compliant, violation = self.check_restricted_symbol(symbol)
        if not is_compliant:
            violations.append(violation)
            return False, violations  # Critical - stop immediately
        
        # Check market hours
        is_compliant, violation = self.check_market_hours()
        if not is_compliant:
            violations.append(violation)
        
        # Check position limit
        is_compliant, violation = self.check_position_limit(symbol, position_size)
        if not is_compliant:
            violations.append(violation)
        
        # Check trade frequency
        is_compliant, violation = self.check_trade_frequency(symbol)
        if not is_compliant:
            violations.append(violation)
        
        # Check wash sale
        is_compliant, violation = self.check_wash_sale(symbol, side)
        if not is_compliant:
            violations.append(violation)
        
        # Check leverage if provided
        if equity is not None and exposure is not None:
            is_compliant, violation = self.check_leverage(equity, exposure)
            if not is_compliant:
                violations.append(violation)
        
        # Check concentration if provided
        if portfolio_value is not None:
            position_value = position_size  # Simplified
            is_compliant, violation = self.check_concentration(
                symbol, position_value, portfolio_value
            )
            if not is_compliant:
                violations.append(violation)
        
        # Return overall compliance status
        is_compliant = len(violations) == 0
        return is_compliant, violations
    
    def record_trade(self, symbol: str, side: str, quantity: float, price: float):
        """Record trade for compliance tracking."""
        self.trade_history.append({
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'timestamp': datetime.now()
        })
        
        # Keep only recent history
        cutoff = datetime.now() - timedelta(days=self.wash_sale_period)
        self.trade_history = [
            t for t in self.trade_history
            if t['timestamp'] > cutoff
        ]
    
    def get_violations(
        self,
        severity: Optional[str] = None,
        type: Optional[ViolationType] = None,
        days: int = 7
    ) -> List[ComplianceViolation]:
        """Get compliance violations."""
        cutoff = datetime.now() - timedelta(days=days)
        
        violations = [
            v for v in self.violations
            if v.timestamp > cutoff
        ]
        
        if severity:
            violations = [v for v in violations if v.severity == severity]
        
        if type:
            violations = [v for v in violations if v.type == type]
        
        return violations
    
    def get_summary(self) -> Dict:
        """Get compliance summary."""
        recent_violations = self.get_violations(days=7)
        
        return {
            'total_violations': len(recent_violations),
            'by_severity': {
                'CRITICAL': len([v for v in recent_violations if v.severity == 'CRITICAL']),
                'HIGH': len([v for v in recent_violations if v.severity == 'HIGH']),
                'MEDIUM': len([v for v in recent_violations if v.severity == 'MEDIUM']),
                'LOW': len([v for v in recent_violations if v.severity == 'LOW'])
            },
            'by_type': {
                vtype.value: len([v for v in recent_violations if v.type == vtype])
                for vtype in ViolationType
            },
            'recent_trades': len(self.trade_history)
        }
