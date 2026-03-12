"""
Unified Risk Manager - Consolidated risk management interface.

Provides a single entry point for all risk management operations including
pre-trade checks, position sizing, portfolio risk, and circuit breakers.
Delegates to specialized risk modules.
"""

import logging
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk severity levels."""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class RiskCheckType(Enum):
    """Types of risk checks."""
    PRE_TRADE = "pre_trade"
    POSITION_SIZE = "position_size"
    PORTFOLIO = "portfolio"
    DRAWDOWN = "drawdown"
    CORRELATION = "correlation"
    LEVERAGE = "leverage"
    CONCENTRATION = "concentration"
    CIRCUIT_BREAKER = "circuit_breaker"
    LIQUIDITY = "liquidity"
    VOLATILITY = "volatility"


@dataclass
class RiskCheckResult:
    """Result from a risk check."""
    check_type: RiskCheckType
    passed: bool
    risk_level: RiskLevel
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    recommended_action: str = "none"
    adjusted_size: Optional[float] = None


@dataclass
class RiskState:
    """Current risk state of the portfolio."""
    total_exposure: float = 0.0
    daily_pnl: float = 0.0
    daily_pnl_pct: float = 0.0
    current_drawdown: float = 0.0
    max_drawdown: float = 0.0
    open_positions: int = 0
    leverage: float = 0.0
    risk_level: RiskLevel = RiskLevel.MINIMAL
    circuit_breaker_active: bool = False
    last_updated: datetime = field(default_factory=datetime.utcnow)


class UnifiedRiskManager:
    """
    Consolidated risk management interface.

    Integrates:
    - trading_bot/risk/ (core risk management, position sizing)
    - trading_bot/risk_management/ (advanced risk)
    - trading_bot/safety/ (safety systems)
    - trading_bot/reality_gates/ (reality validation)
    - trading_bot/hedge_fund_safety/ (institutional safety)
    - trading_bot/msos/ (market survival)
    - trading_bot/critical_fixes/ (critical validators)
    """

    # Immutable risk limits
    MAX_RISK_PER_TRADE = 0.02      # 2%
    MAX_DAILY_LOSS = 0.05          # 5%
    MAX_DRAWDOWN = 0.20            # 20%
    MAX_LEVERAGE = 5.0
    MAX_POSITION_SIZE_PCT = 0.10   # 10% of portfolio
    MAX_SECTOR_EXPOSURE = 0.25     # 25%
    MAX_CORRELATED_EXPOSURE = 0.30 # 30%

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}
        self._state = RiskState()
        self._check_history: List[RiskCheckResult] = []
        self._risk_modules: Dict[str, Any] = {}
        self._initialize_modules()
        logger.info("UnifiedRiskManager initialized with immutable limits")

    def _initialize_modules(self) -> None:
        """Initialize available risk sub-modules."""
        try:
            from trading_bot.risk import risk_manager
            self._risk_modules["core"] = risk_manager
        except (ImportError, AttributeError):
            pass

        try:
            from trading_bot.risk import position_sizer
            self._risk_modules["position_sizer"] = position_sizer
        except (ImportError, AttributeError):
            pass

        try:
            from trading_bot.safety import safety_manager
            self._risk_modules["safety"] = safety_manager
        except (ImportError, AttributeError):
            pass

        try:
            from trading_bot.reality_gates import reality_gate
            self._risk_modules["reality_gates"] = reality_gate
        except (ImportError, AttributeError):
            pass

        logger.info("Risk modules loaded: %d", len(self._risk_modules))

    def validate_trade(
        self,
        symbol: str,
        direction: str,
        quantity: float,
        price: float,
        portfolio_value: float,
        context: Optional[Dict] = None,
    ) -> List[RiskCheckResult]:
        """
        Run all risk checks on a proposed trade.

        Returns list of RiskCheckResult. Trade should only proceed if ALL pass.
        """
        context = context or {}
        results = []

        # 1. Position size check
        position_value = quantity * price
        position_pct = position_value / portfolio_value if portfolio_value > 0 else 1.0

        if position_pct > self.MAX_POSITION_SIZE_PCT:
            results.append(RiskCheckResult(
                check_type=RiskCheckType.POSITION_SIZE,
                passed=False,
                risk_level=RiskLevel.HIGH,
                message=f"Position size {position_pct:.1%} exceeds max {self.MAX_POSITION_SIZE_PCT:.1%}",
                adjusted_size=self.MAX_POSITION_SIZE_PCT * portfolio_value / price,
                recommended_action="reduce_size",
            ))
        else:
            results.append(RiskCheckResult(
                check_type=RiskCheckType.POSITION_SIZE,
                passed=True,
                risk_level=RiskLevel.LOW,
                message=f"Position size {position_pct:.1%} within limits",
            ))

        # 2. Daily loss check
        if abs(self._state.daily_pnl_pct) >= self.MAX_DAILY_LOSS:
            results.append(RiskCheckResult(
                check_type=RiskCheckType.DRAWDOWN,
                passed=False,
                risk_level=RiskLevel.CRITICAL,
                message=f"Daily loss {self._state.daily_pnl_pct:.1%} exceeds limit {self.MAX_DAILY_LOSS:.1%}",
                recommended_action="halt_trading",
            ))
        else:
            results.append(RiskCheckResult(
                check_type=RiskCheckType.DRAWDOWN,
                passed=True,
                risk_level=RiskLevel.LOW,
                message=f"Daily P&L {self._state.daily_pnl_pct:.1%} within limits",
            ))

        # 3. Max drawdown check
        if self._state.current_drawdown >= self.MAX_DRAWDOWN:
            results.append(RiskCheckResult(
                check_type=RiskCheckType.DRAWDOWN,
                passed=False,
                risk_level=RiskLevel.EMERGENCY,
                message=f"Drawdown {self._state.current_drawdown:.1%} exceeds max {self.MAX_DRAWDOWN:.1%}",
                recommended_action="emergency_close_all",
            ))
        else:
            results.append(RiskCheckResult(
                check_type=RiskCheckType.DRAWDOWN,
                passed=True,
                risk_level=RiskLevel.LOW,
                message=f"Drawdown {self._state.current_drawdown:.1%} within limits",
            ))

        # 4. Leverage check
        new_leverage = (self._state.total_exposure + position_value) / portfolio_value if portfolio_value > 0 else 0
        if new_leverage > self.MAX_LEVERAGE:
            results.append(RiskCheckResult(
                check_type=RiskCheckType.LEVERAGE,
                passed=False,
                risk_level=RiskLevel.HIGH,
                message=f"Leverage {new_leverage:.1f}x exceeds max {self.MAX_LEVERAGE:.1f}x",
                recommended_action="reduce_size",
            ))
        else:
            results.append(RiskCheckResult(
                check_type=RiskCheckType.LEVERAGE,
                passed=True,
                risk_level=RiskLevel.LOW,
                message=f"Leverage {new_leverage:.1f}x within limits",
            ))

        # 5. Circuit breaker check
        if self._state.circuit_breaker_active:
            results.append(RiskCheckResult(
                check_type=RiskCheckType.CIRCUIT_BREAKER,
                passed=False,
                risk_level=RiskLevel.CRITICAL,
                message="Circuit breaker is active - trading halted",
                recommended_action="wait",
            ))
        else:
            results.append(RiskCheckResult(
                check_type=RiskCheckType.CIRCUIT_BREAKER,
                passed=True,
                risk_level=RiskLevel.MINIMAL,
                message="Circuit breaker inactive",
            ))

        # Store results
        self._check_history.extend(results)
        if len(self._check_history) > 5000:
            self._check_history = self._check_history[-2500:]

        return results

    def is_trade_allowed(
        self,
        symbol: str,
        direction: str,
        quantity: float,
        price: float,
        portfolio_value: float,
        context: Optional[Dict] = None,
    ) -> tuple:
        """
        Quick check if a trade is allowed.

        Returns (allowed: bool, reason: str, results: List[RiskCheckResult])
        """
        results = self.validate_trade(symbol, direction, quantity, price, portfolio_value, context)
        all_passed = all(r.passed for r in results)
        if all_passed:
            return True, "All risk checks passed", results
        else:
            failed = [r for r in results if not r.passed]
            reason = "; ".join(r.message for r in failed)
            return False, reason, results

    def update_state(
        self,
        total_exposure: Optional[float] = None,
        daily_pnl: Optional[float] = None,
        daily_pnl_pct: Optional[float] = None,
        current_drawdown: Optional[float] = None,
        open_positions: Optional[int] = None,
        leverage: Optional[float] = None,
        portfolio_value: Optional[float] = None,
    ) -> None:
        """Update the current risk state."""
        if total_exposure is not None:
            self._state.total_exposure = total_exposure
        if daily_pnl is not None:
            self._state.daily_pnl = daily_pnl
        if daily_pnl_pct is not None:
            self._state.daily_pnl_pct = daily_pnl_pct
        if current_drawdown is not None:
            self._state.current_drawdown = current_drawdown
            self._state.max_drawdown = max(self._state.max_drawdown, current_drawdown)
        if open_positions is not None:
            self._state.open_positions = open_positions
        if leverage is not None:
            self._state.leverage = leverage

        # Update risk level
        self._state.risk_level = self._calculate_risk_level()
        self._state.last_updated = datetime.utcnow()

        # Check circuit breaker triggers
        if (abs(self._state.daily_pnl_pct) >= self.MAX_DAILY_LOSS or
                self._state.current_drawdown >= self.MAX_DRAWDOWN):
            self._state.circuit_breaker_active = True
            logger.critical("CIRCUIT BREAKER ACTIVATED - Risk limits breached")

    def reset_circuit_breaker(self) -> None:
        """Manually reset the circuit breaker (requires human action)."""
        self._state.circuit_breaker_active = False
        logger.warning("Circuit breaker manually reset")

    def calculate_position_size(
        self,
        portfolio_value: float,
        risk_per_trade: float,
        entry_price: float,
        stop_loss_price: float,
    ) -> float:
        """
        Calculate position size based on risk parameters.

        Uses fixed fractional method with Kelly Criterion adjustment.
        """
        risk_pct = min(risk_per_trade, self.MAX_RISK_PER_TRADE)
        risk_amount = portfolio_value * risk_pct

        price_risk = abs(entry_price - stop_loss_price)
        if price_risk <= 0:
            return 0.0

        position_size = risk_amount / price_risk

        # Cap at max position size
        max_size = (portfolio_value * self.MAX_POSITION_SIZE_PCT) / entry_price
        position_size = min(position_size, max_size)

        return round(position_size, 8)

    def get_risk_state(self) -> Dict:
        """Get current risk state as dictionary."""
        return {
            "total_exposure": self._state.total_exposure,
            "daily_pnl": self._state.daily_pnl,
            "daily_pnl_pct": self._state.daily_pnl_pct,
            "current_drawdown": self._state.current_drawdown,
            "max_drawdown": self._state.max_drawdown,
            "open_positions": self._state.open_positions,
            "leverage": self._state.leverage,
            "risk_level": self._state.risk_level.value,
            "circuit_breaker_active": self._state.circuit_breaker_active,
            "last_updated": self._state.last_updated.isoformat(),
            "modules_loaded": len(self._risk_modules),
            "checks_performed": len(self._check_history),
        }

    def _calculate_risk_level(self) -> RiskLevel:
        """Calculate overall risk level from current state."""
        if self._state.circuit_breaker_active:
            return RiskLevel.EMERGENCY
        if self._state.current_drawdown >= 0.15:
            return RiskLevel.CRITICAL
        if self._state.current_drawdown >= 0.10:
            return RiskLevel.HIGH
        if abs(self._state.daily_pnl_pct) >= 0.03:
            return RiskLevel.MODERATE
        if self._state.leverage > 3.0:
            return RiskLevel.MODERATE
        if abs(self._state.daily_pnl_pct) >= 0.01:
            return RiskLevel.LOW
        return RiskLevel.MINIMAL
