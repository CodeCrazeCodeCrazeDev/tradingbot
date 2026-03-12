"""
AlphaAlgo Institutional - Layer 5: Risk Governance
===================================================

The Risk Governance Layer is responsible for:
- Tail risk management
- Drawdown controls
- Position limits
- Correlation risk
- Stress testing
- Kill switch authority

This layer operates as the VALIDATION & KILL COMMITTEE.

Key principles:
- Risk has veto power over opportunity
- Capital preservation is non-negotiable
- Drawdown limits are absolute
- No single position can threaten survival
- Correlation risk is systemic risk
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import numpy as np
from collections import defaultdict
import uuid

from .core_types import (
    RiskMetrics, RiskLevel, MarketRegime, CommitteeType, CommitteeVote,
    CommitteeDecision, SystemConstants
)

logger = logging.getLogger(__name__)


# =============================================================================
# RISK TYPES
# =============================================================================

class RiskType(Enum):
    """Types of risk."""
    MARKET = "market"
    CREDIT = "credit"
    LIQUIDITY = "liquidity"
    OPERATIONAL = "operational"
    MODEL = "model"
    CONCENTRATION = "concentration"
    CORRELATION = "correlation"
    TAIL = "tail"
    LEVERAGE = "leverage"
    COUNTERPARTY = "counterparty"


class RiskAction(Enum):
    """Risk management actions."""
    NONE = "none"
    REDUCE_POSITION = "reduce_position"
    HEDGE = "hedge"
    CLOSE_POSITION = "close_position"
    HALT_TRADING = "halt_trading"
    EMERGENCY_LIQUIDATION = "emergency_liquidation"


class DrawdownLevel(Enum):
    """Drawdown severity levels."""
    NORMAL = "normal"  # < 5%
    ELEVATED = "elevated"  # 5-10%
    WARNING = "warning"  # 10-15%
    CRITICAL = "critical"  # 15-20%
    EMERGENCY = "emergency"  # > 20%


@dataclass
class RiskLimit:
    """A risk limit definition."""
    name: str
    limit_type: RiskType
    soft_limit: float
    hard_limit: float
    current_value: float = 0.0
    breached: bool = False
    breach_time: Optional[datetime] = None
    action_on_breach: RiskAction = RiskAction.REDUCE_POSITION


@dataclass
class RiskAlert:
    """A risk alert."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: datetime = field(default_factory=datetime.utcnow)
    risk_type: RiskType = RiskType.MARKET
    level: RiskLevel = RiskLevel.LOW
    message: str = ""
    current_value: float = 0.0
    limit_value: float = 0.0
    recommended_action: RiskAction = RiskAction.NONE
    acknowledged: bool = False


@dataclass
class StressScenario:
    """A stress test scenario."""
    name: str
    description: str
    market_shock: float  # % change in market
    volatility_multiplier: float
    correlation_shock: float  # Change in correlations
    liquidity_shock: float  # % reduction in liquidity
    probability: float  # Estimated probability


@dataclass
class StressTestResult:
    """Result of a stress test."""
    scenario: StressScenario
    portfolio_loss: float
    max_drawdown: float
    var_breach: bool
    liquidity_shortfall: float
    margin_call_risk: float
    survival_probability: float


# =============================================================================
# VAR ENGINE
# =============================================================================

class VaREngine:
    """Value at Risk calculation engine."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.confidence_level = self.config.get('confidence_level', 0.99)
        self.lookback_days = self.config.get('lookback_days', 252)
    
    def compute_parametric_var(
        self,
        portfolio_value: float,
        portfolio_volatility: float,
        confidence: float = None
    ) -> float:
        """
        Compute parametric VaR.
        
        Args:
            portfolio_value: Current portfolio value
            portfolio_volatility: Portfolio volatility (annualized)
            confidence: Confidence level (default from config)
            
        Returns:
            VaR value (positive number representing potential loss)
        """
        conf = confidence or self.confidence_level
        
        # Z-score for confidence level
        from scipy import stats
        z_score = stats.norm.ppf(conf)
        
        # Daily volatility
        daily_vol = portfolio_volatility / np.sqrt(252)
        
        # VaR
        var = portfolio_value * z_score * daily_vol
        
        return abs(var)
    
    def compute_historical_var(
        self,
        returns: np.ndarray,
        portfolio_value: float,
        confidence: float = None
    ) -> float:
        """
        Compute historical VaR.
        
        Args:
            returns: Historical returns array
            portfolio_value: Current portfolio value
            confidence: Confidence level
            
        Returns:
            VaR value
        """
        conf = confidence or self.confidence_level
        
        if len(returns) < 10:
            return 0.0
        
        # Percentile of losses
        percentile = (1 - conf) * 100
        var_return = np.percentile(returns, percentile)
        
        return abs(portfolio_value * var_return)
    
    def compute_cvar(
        self,
        returns: np.ndarray,
        portfolio_value: float,
        confidence: float = None
    ) -> float:
        """
        Compute Conditional VaR (Expected Shortfall).
        
        Args:
            returns: Historical returns array
            portfolio_value: Current portfolio value
            confidence: Confidence level
            
        Returns:
            CVaR value
        """
        conf = confidence or self.confidence_level
        
        if len(returns) < 10:
            return 0.0
        
        # VaR threshold
        percentile = (1 - conf) * 100
        var_threshold = np.percentile(returns, percentile)
        
        # Average of returns below VaR
        tail_returns = returns[returns <= var_threshold]
        if len(tail_returns) == 0:
            return abs(portfolio_value * var_threshold)
        
        cvar_return = np.mean(tail_returns)
        
        return abs(portfolio_value * cvar_return)


# =============================================================================
# DRAWDOWN CONTROLLER
# =============================================================================

class DrawdownController:
    """Controls drawdown and implements circuit breakers."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Drawdown thresholds
        self.thresholds = {
            DrawdownLevel.NORMAL: 0.05,
            DrawdownLevel.ELEVATED: 0.10,
            DrawdownLevel.WARNING: 0.15,
            DrawdownLevel.CRITICAL: 0.20,
            DrawdownLevel.EMERGENCY: 0.25
        }
        
        # Position reduction by level
        self.position_reduction = {
            DrawdownLevel.NORMAL: 0.0,
            DrawdownLevel.ELEVATED: 0.25,
            DrawdownLevel.WARNING: 0.50,
            DrawdownLevel.CRITICAL: 0.75,
            DrawdownLevel.EMERGENCY: 1.0
        }
        
        # State
        self.high_water_mark: float = 0.0
        self.current_drawdown: float = 0.0
        self.max_drawdown: float = 0.0
        self.drawdown_start: Optional[datetime] = None
        self.drawdown_duration: int = 0
    
    def update(self, portfolio_value: float) -> DrawdownLevel:
        """
        Update drawdown state.
        
        Args:
            portfolio_value: Current portfolio value
            
        Returns:
            Current drawdown level
        """
        # Update high water mark
        if portfolio_value > self.high_water_mark:
            self.high_water_mark = portfolio_value
            self.drawdown_start = None
            self.drawdown_duration = 0
        
        # Compute drawdown
        if self.high_water_mark > 0:
            self.current_drawdown = (self.high_water_mark - portfolio_value) / self.high_water_mark
        else:
            self.current_drawdown = 0.0
        
        # Track max drawdown
        self.max_drawdown = max(self.max_drawdown, self.current_drawdown)
        
        # Track duration
        if self.current_drawdown > self.thresholds[DrawdownLevel.NORMAL]:
            if self.drawdown_start is None:
                self.drawdown_start = datetime.utcnow()
            self.drawdown_duration = (datetime.utcnow() - self.drawdown_start).days
        
        return self.get_level()
    
    def get_level(self) -> DrawdownLevel:
        """Get current drawdown level."""
        for level in reversed(list(DrawdownLevel)):
            if self.current_drawdown >= self.thresholds[level]:
                return level
        return DrawdownLevel.NORMAL
    
    def get_position_limit_multiplier(self) -> float:
        """Get position limit multiplier based on drawdown."""
        level = self.get_level()
        reduction = self.position_reduction[level]
        return 1.0 - reduction
    
    def get_required_action(self) -> RiskAction:
        """Get required action based on drawdown level."""
        level = self.get_level()
        
        if level == DrawdownLevel.EMERGENCY:
            return RiskAction.EMERGENCY_LIQUIDATION
        elif level == DrawdownLevel.CRITICAL:
            return RiskAction.HALT_TRADING
        elif level == DrawdownLevel.WARNING:
            return RiskAction.CLOSE_POSITION
        elif level == DrawdownLevel.ELEVATED:
            return RiskAction.REDUCE_POSITION
        else:
            return RiskAction.NONE


# =============================================================================
# TAIL RISK MANAGER
# =============================================================================

class TailRiskManager:
    """Manages tail risk and extreme events."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.tail_threshold = self.config.get('tail_threshold', 0.05)
        self.extreme_threshold = self.config.get('extreme_threshold', 0.01)
    
    def estimate_tail_risk(self, returns: np.ndarray) -> Dict[str, float]:
        """
        Estimate tail risk metrics.
        
        Args:
            returns: Historical returns
            
        Returns:
            Dict of tail risk metrics
        """
        if len(returns) < 30:
            return {
                'left_tail_prob': 0.0,
                'right_tail_prob': 0.0,
                'tail_index': 0.0,
                'expected_shortfall': 0.0
            }
        
        # Left tail (losses)
        left_threshold = np.percentile(returns, self.tail_threshold * 100)
        left_tail_returns = returns[returns <= left_threshold]
        
        # Right tail (gains)
        right_threshold = np.percentile(returns, (1 - self.tail_threshold) * 100)
        right_tail_returns = returns[returns >= right_threshold]
        
        # Tail index (simplified)
        if len(left_tail_returns) > 0:
            tail_index = 1.0 / np.std(left_tail_returns) if np.std(left_tail_returns) > 0 else 0
        else:
            tail_index = 0.0
        
        # Expected shortfall
        if len(left_tail_returns) > 0:
            expected_shortfall = abs(np.mean(left_tail_returns))
        else:
            expected_shortfall = 0.0
        
        return {
            'left_tail_prob': len(left_tail_returns) / len(returns),
            'right_tail_prob': len(right_tail_returns) / len(returns),
            'tail_index': tail_index,
            'expected_shortfall': expected_shortfall
        }
    
    def detect_tail_event(self, current_return: float, returns: np.ndarray) -> bool:
        """Check if current return is a tail event."""
        if len(returns) < 30:
            return False
        
        threshold = np.percentile(returns, self.extreme_threshold * 100)
        return current_return <= threshold


# =============================================================================
# STRESS TESTER
# =============================================================================

class StressTester:
    """Performs stress testing on portfolio."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Predefined scenarios
        self.scenarios = [
            StressScenario(
                name="Market Crash",
                description="2008-style market crash",
                market_shock=-0.40,
                volatility_multiplier=3.0,
                correlation_shock=0.3,
                liquidity_shock=0.5,
                probability=0.02
            ),
            StressScenario(
                name="Flash Crash",
                description="Sudden intraday crash",
                market_shock=-0.10,
                volatility_multiplier=5.0,
                correlation_shock=0.5,
                liquidity_shock=0.8,
                probability=0.05
            ),
            StressScenario(
                name="Volatility Spike",
                description="VIX-style volatility explosion",
                market_shock=-0.05,
                volatility_multiplier=4.0,
                correlation_shock=0.2,
                liquidity_shock=0.3,
                probability=0.10
            ),
            StressScenario(
                name="Liquidity Crisis",
                description="Market-wide liquidity freeze",
                market_shock=-0.15,
                volatility_multiplier=2.0,
                correlation_shock=0.4,
                liquidity_shock=0.9,
                probability=0.03
            ),
            StressScenario(
                name="Correlation Breakdown",
                description="Historical correlations fail",
                market_shock=-0.10,
                volatility_multiplier=2.0,
                correlation_shock=0.6,
                liquidity_shock=0.2,
                probability=0.05
            ),
            StressScenario(
                name="Moderate Correction",
                description="Normal market correction",
                market_shock=-0.15,
                volatility_multiplier=1.5,
                correlation_shock=0.1,
                liquidity_shock=0.1,
                probability=0.20
            )
        ]
    
    def run_stress_test(
        self,
        portfolio_value: float,
        portfolio_beta: float,
        leverage: float,
        liquidity_buffer: float
    ) -> List[StressTestResult]:
        """
        Run stress tests on portfolio.
        
        Args:
            portfolio_value: Current portfolio value
            portfolio_beta: Portfolio beta to market
            leverage: Current leverage
            liquidity_buffer: Available liquidity
            
        Returns:
            List of stress test results
        """
        results = []
        
        for scenario in self.scenarios:
            # Compute portfolio loss
            market_impact = scenario.market_shock * portfolio_beta
            vol_impact = (scenario.volatility_multiplier - 1) * 0.02  # Assume 2% base vol
            leverage_impact = leverage * market_impact
            
            total_loss = (market_impact + vol_impact) * (1 + leverage)
            portfolio_loss = portfolio_value * total_loss
            
            # Max drawdown under scenario
            max_dd = abs(total_loss)
            
            # VaR breach check
            var_threshold = portfolio_value * 0.05  # 5% VaR
            var_breach = abs(portfolio_loss) > var_threshold
            
            # Liquidity shortfall
            required_liquidity = abs(portfolio_loss) * scenario.liquidity_shock
            liquidity_shortfall = max(0, required_liquidity - liquidity_buffer)
            
            # Margin call risk
            margin_call_risk = min(1.0, leverage * abs(market_impact) / 0.25)
            
            # Survival probability
            survival_prob = 1.0 - min(1.0, max_dd / SystemConstants.MAX_DRAWDOWN_LIMIT)
            
            results.append(StressTestResult(
                scenario=scenario,
                portfolio_loss=portfolio_loss,
                max_drawdown=max_dd,
                var_breach=var_breach,
                liquidity_shortfall=liquidity_shortfall,
                margin_call_risk=margin_call_risk,
                survival_probability=survival_prob
            ))
        
        return results


# =============================================================================
# POSITION LIMIT MANAGER
# =============================================================================

class PositionLimitManager:
    """Manages position limits and concentration."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Default limits
        self.max_single_position = self.config.get('max_single_position', 0.10)
        self.max_sector_exposure = self.config.get('max_sector_exposure', 0.25)
        self.max_correlated_exposure = self.config.get('max_correlated_exposure', 0.30)
        self.max_leverage = self.config.get('max_leverage', SystemConstants.MAX_LEVERAGE)
        
        # Current positions
        self.positions: Dict[str, float] = {}
        self.sector_exposures: Dict[str, float] = {}
    
    def check_position_limit(
        self,
        symbol: str,
        proposed_size: float,
        portfolio_value: float
    ) -> Tuple[bool, str]:
        """
        Check if proposed position is within limits.
        
        Returns:
            Tuple of (allowed, reason)
        """
        position_weight = proposed_size / portfolio_value if portfolio_value > 0 else 0
        
        if position_weight > self.max_single_position:
            return False, f"Position {position_weight:.2%} exceeds limit {self.max_single_position:.2%}"
        
        return True, "Within limits"
    
    def check_concentration(
        self,
        positions: Dict[str, float],
        portfolio_value: float
    ) -> Tuple[bool, List[str]]:
        """
        Check portfolio concentration.
        
        Returns:
            Tuple of (passes, list of violations)
        """
        violations = []
        
        for symbol, size in positions.items():
            weight = size / portfolio_value if portfolio_value > 0 else 0
            if weight > self.max_single_position:
                violations.append(f"{symbol}: {weight:.2%} exceeds {self.max_single_position:.2%}")
        
        return len(violations) == 0, violations
    
    def compute_concentration_score(self, weights: np.ndarray) -> float:
        """Compute Herfindahl-Hirschman Index for concentration."""
        return np.sum(weights ** 2)


# =============================================================================
# VALIDATION & KILL COMMITTEE
# =============================================================================

class ValidationKillCommittee:
    """
    Internal committee responsible for risk governance.
    
    Has VETO POWER over all trading decisions.
    
    Responsibilities:
    - Validate all trades before execution
    - Monitor risk limits
    - Trigger circuit breakers
    - Kill underperforming strategies
    - Emergency liquidation authority
    
    Key principles:
    - Risk has veto power
    - Capital preservation is non-negotiable
    - Drawdown limits are absolute
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.committee_type = CommitteeType.VALIDATION_KILL
        
        # Initialize components
        self.var_engine = VaREngine(self.config)
        self.drawdown_controller = DrawdownController(self.config)
        self.tail_risk_manager = TailRiskManager(self.config)
        self.stress_tester = StressTester(self.config)
        self.position_limit_manager = PositionLimitManager(self.config)
        
        # Risk limits
        self.risk_limits: Dict[str, RiskLimit] = self._initialize_risk_limits()
        
        # Alerts
        self.active_alerts: List[RiskAlert] = []
        self.alert_history: List[RiskAlert] = []
        
        # Kill list
        self.killed_strategies: List[str] = []
        
        # State
        self.trading_halted = False
        self.halt_reason: Optional[str] = None
        
        logger.info("ValidationKillCommittee initialized")
    
    def _initialize_risk_limits(self) -> Dict[str, RiskLimit]:
        """Initialize default risk limits."""
        return {
            'max_drawdown': RiskLimit(
                name="Maximum Drawdown",
                limit_type=RiskType.MARKET,
                soft_limit=0.15,
                hard_limit=SystemConstants.MAX_DRAWDOWN_LIMIT,
                action_on_breach=RiskAction.HALT_TRADING
            ),
            'daily_var': RiskLimit(
                name="Daily VaR",
                limit_type=RiskType.MARKET,
                soft_limit=0.03,
                hard_limit=0.05,
                action_on_breach=RiskAction.REDUCE_POSITION
            ),
            'position_concentration': RiskLimit(
                name="Position Concentration",
                limit_type=RiskType.CONCENTRATION,
                soft_limit=0.08,
                hard_limit=SystemConstants.MAX_POSITION_SIZE,
                action_on_breach=RiskAction.REDUCE_POSITION
            ),
            'leverage': RiskLimit(
                name="Leverage",
                limit_type=RiskType.LEVERAGE,
                soft_limit=SystemConstants.MAX_LEVERAGE * 0.8,
                hard_limit=SystemConstants.MAX_LEVERAGE,
                action_on_breach=RiskAction.REDUCE_POSITION
            ),
            'correlation_exposure': RiskLimit(
                name="Correlated Exposure",
                limit_type=RiskType.CORRELATION,
                soft_limit=0.25,
                hard_limit=0.35,
                action_on_breach=RiskAction.HEDGE
            )
        }
    
    def validate_trade(
        self,
        symbol: str,
        direction: str,
        size: float,
        portfolio_value: float,
        current_positions: Dict[str, float]
    ) -> Tuple[bool, str, List[str]]:
        """
        Validate a proposed trade.
        
        Args:
            symbol: Trading symbol
            direction: 'buy' or 'sell'
            size: Position size
            portfolio_value: Current portfolio value
            current_positions: Current positions
            
        Returns:
            Tuple of (approved, reason, conditions)
        """
        conditions = []
        
        # Check if trading is halted
        if self.trading_halted:
            return False, f"Trading halted: {self.halt_reason}", []
        
        # Check position limit
        allowed, reason = self.position_limit_manager.check_position_limit(
            symbol, size, portfolio_value
        )
        if not allowed:
            return False, reason, []
        
        # Check drawdown
        dd_level = self.drawdown_controller.get_level()
        if dd_level in [DrawdownLevel.CRITICAL, DrawdownLevel.EMERGENCY]:
            return False, f"Drawdown at {dd_level.value} level", []
        
        if dd_level == DrawdownLevel.WARNING:
            conditions.append("Reduced position size due to drawdown")
        
        # Check concentration
        test_positions = current_positions.copy()
        test_positions[symbol] = test_positions.get(symbol, 0) + size
        passes, violations = self.position_limit_manager.check_concentration(
            test_positions, portfolio_value
        )
        if not passes:
            return False, f"Concentration violation: {violations[0]}", []
        
        return True, "Trade approved", conditions
    
    def update_risk_state(
        self,
        portfolio_value: float,
        returns: np.ndarray,
        positions: Dict[str, float],
        leverage: float
    ) -> List[RiskAlert]:
        """
        Update risk state and check for breaches.
        
        Returns:
            List of new alerts
        """
        new_alerts = []
        
        # Update drawdown
        dd_level = self.drawdown_controller.update(portfolio_value)
        if dd_level != DrawdownLevel.NORMAL:
            alert = RiskAlert(
                risk_type=RiskType.MARKET,
                level=self._dd_level_to_risk_level(dd_level),
                message=f"Drawdown at {dd_level.value}: {self.drawdown_controller.current_drawdown:.2%}",
                current_value=self.drawdown_controller.current_drawdown,
                limit_value=SystemConstants.MAX_DRAWDOWN_LIMIT,
                recommended_action=self.drawdown_controller.get_required_action()
            )
            new_alerts.append(alert)
        
        # Check VaR
        if len(returns) > 0:
            portfolio_vol = np.std(returns) * np.sqrt(252)
            var = self.var_engine.compute_parametric_var(portfolio_value, portfolio_vol)
            var_pct = var / portfolio_value if portfolio_value > 0 else 0
            
            var_limit = self.risk_limits['daily_var']
            if var_pct > var_limit.hard_limit:
                var_limit.breached = True
                var_limit.current_value = var_pct
                alert = RiskAlert(
                    risk_type=RiskType.MARKET,
                    level=RiskLevel.CRITICAL,
                    message=f"VaR breach: {var_pct:.2%} > {var_limit.hard_limit:.2%}",
                    current_value=var_pct,
                    limit_value=var_limit.hard_limit,
                    recommended_action=var_limit.action_on_breach
                )
                new_alerts.append(alert)
        
        # Check leverage
        leverage_limit = self.risk_limits['leverage']
        if leverage > leverage_limit.hard_limit:
            leverage_limit.breached = True
            leverage_limit.current_value = leverage
            alert = RiskAlert(
                risk_type=RiskType.LEVERAGE,
                level=RiskLevel.HIGH,
                message=f"Leverage breach: {leverage:.2f}x > {leverage_limit.hard_limit:.2f}x",
                current_value=leverage,
                limit_value=leverage_limit.hard_limit,
                recommended_action=leverage_limit.action_on_breach
            )
            new_alerts.append(alert)
        
        # Store alerts
        self.active_alerts.extend(new_alerts)
        self.alert_history.extend(new_alerts)
        
        # Check for halt conditions
        self._check_halt_conditions()
        
        return new_alerts
    
    def _dd_level_to_risk_level(self, dd_level: DrawdownLevel) -> RiskLevel:
        """Convert drawdown level to risk level."""
        mapping = {
            DrawdownLevel.NORMAL: RiskLevel.LOW,
            DrawdownLevel.ELEVATED: RiskLevel.MEDIUM,
            DrawdownLevel.WARNING: RiskLevel.HIGH,
            DrawdownLevel.CRITICAL: RiskLevel.CRITICAL,
            DrawdownLevel.EMERGENCY: RiskLevel.CRITICAL
        }
        return mapping.get(dd_level, RiskLevel.LOW)
    
    def _check_halt_conditions(self):
        """Check if trading should be halted."""
        # Check drawdown
        if self.drawdown_controller.get_level() == DrawdownLevel.EMERGENCY:
            self.halt_trading("Emergency drawdown level reached")
            return
        
        # Check for multiple critical alerts
        critical_alerts = [a for a in self.active_alerts if a.level == RiskLevel.CRITICAL]
        if len(critical_alerts) >= 3:
            self.halt_trading("Multiple critical risk alerts")
    
    def halt_trading(self, reason: str):
        """Halt all trading."""
        self.trading_halted = True
        self.halt_reason = reason
        logger.critical(f"TRADING HALTED: {reason}")
    
    def resume_trading(self) -> bool:
        """Resume trading if conditions allow."""
        # Check if conditions have improved
        if self.drawdown_controller.get_level() in [DrawdownLevel.CRITICAL, DrawdownLevel.EMERGENCY]:
            return False
        
        # Clear critical alerts
        self.active_alerts = [a for a in self.active_alerts if a.level != RiskLevel.CRITICAL]
        
        self.trading_halted = False
        self.halt_reason = None
        logger.info("Trading resumed")
        return True
    
    def kill_strategy(self, strategy_id: str, reason: str):
        """Kill a strategy."""
        self.killed_strategies.append(strategy_id)
        logger.warning(f"Strategy killed: {strategy_id} - {reason}")
    
    def run_stress_tests(
        self,
        portfolio_value: float,
        portfolio_beta: float,
        leverage: float,
        liquidity_buffer: float
    ) -> List[StressTestResult]:
        """Run stress tests."""
        return self.stress_tester.run_stress_test(
            portfolio_value, portfolio_beta, leverage, liquidity_buffer
        )
    
    def vote(self, trade_proposal: Dict[str, Any]) -> CommitteeVote:
        """
        Vote on a trade proposal.
        
        Returns:
            CommitteeVote with risk assessment
        """
        symbol = trade_proposal.get('symbol', '')
        direction = trade_proposal.get('direction', '')
        size = trade_proposal.get('size', 0)
        portfolio_value = trade_proposal.get('portfolio_value', 0)
        current_positions = trade_proposal.get('current_positions', {})
        
        approved, reason, conditions = self.validate_trade(
            symbol, direction, size, portfolio_value, current_positions
        )
        
        if approved:
            decision = CommitteeDecision.APPROVE if not conditions else CommitteeDecision.CONDITIONAL
            confidence = 0.9 if not conditions else 0.7
        else:
            decision = CommitteeDecision.REJECT
            confidence = 0.95
        
        return CommitteeVote(
            committee=self.committee_type,
            decision=decision,
            confidence=confidence,
            rationale=reason,
            conditions=conditions
        )
    
    def get_risk_metrics(self) -> RiskMetrics:
        """Get current risk metrics."""
        return RiskMetrics(
            var_95=0.0,  # Would be computed from actual data
            var_99=0.0,
            cvar_95=0.0,
            cvar_99=0.0,
            max_drawdown=self.drawdown_controller.max_drawdown,
            current_drawdown=self.drawdown_controller.current_drawdown,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            calmar_ratio=0.0,
            beta=0.0,
            correlation_to_benchmark=0.0,
            tail_risk_score=0.0,
            liquidity_risk_score=0.0,
            concentration_risk_score=0.0
        )
    
    def get_committee_state(self) -> Dict[str, Any]:
        """Get committee state."""
        return {
            'trading_halted': self.trading_halted,
            'halt_reason': self.halt_reason,
            'current_drawdown': self.drawdown_controller.current_drawdown,
            'max_drawdown': self.drawdown_controller.max_drawdown,
            'drawdown_level': self.drawdown_controller.get_level().value,
            'active_alerts': len(self.active_alerts),
            'killed_strategies': len(self.killed_strategies),
            'risk_limits_breached': sum(1 for l in self.risk_limits.values() if l.breached)
        }


# =============================================================================
# RISK GOVERNANCE LAYER
# =============================================================================

class RiskGovernanceLayer:
    """
    Layer 5: Risk Governance Layer
    
    Responsible for:
    - Risk monitoring and limits
    - Drawdown controls
    - Position limits
    - Stress testing
    - Kill switch authority
    
    Has VETO POWER over all trading decisions.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.committee = ValidationKillCommittee(self.config)
        
        # Layer state
        self.last_risk_update: Optional[datetime] = None
        self.risk_update_count = 0
        
        logger.info("RiskGovernanceLayer initialized")
    
    def validate_trade(
        self,
        symbol: str,
        direction: str,
        size: float,
        portfolio_value: float,
        current_positions: Dict[str, float]
    ) -> Tuple[bool, str, List[str]]:
        """Validate a trade."""
        return self.committee.validate_trade(
            symbol, direction, size, portfolio_value, current_positions
        )
    
    def update_risk_state(
        self,
        portfolio_value: float,
        returns: np.ndarray,
        positions: Dict[str, float],
        leverage: float
    ) -> List[RiskAlert]:
        """Update risk state."""
        alerts = self.committee.update_risk_state(
            portfolio_value, returns, positions, leverage
        )
        self.last_risk_update = datetime.utcnow()
        self.risk_update_count += 1
        return alerts
    
    def run_stress_tests(
        self,
        portfolio_value: float,
        portfolio_beta: float,
        leverage: float,
        liquidity_buffer: float
    ) -> List[StressTestResult]:
        """Run stress tests."""
        return self.committee.run_stress_tests(
            portfolio_value, portfolio_beta, leverage, liquidity_buffer
        )
    
    def is_trading_allowed(self) -> Tuple[bool, str]:
        """Check if trading is allowed."""
        if self.committee.trading_halted:
            return False, self.committee.halt_reason or "Trading halted"
        return True, "Trading allowed"
    
    def halt_trading(self, reason: str):
        """Halt trading."""
        self.committee.halt_trading(reason)
    
    def resume_trading(self) -> bool:
        """Resume trading."""
        return self.committee.resume_trading()
    
    def kill_strategy(self, strategy_id: str, reason: str):
        """Kill a strategy."""
        self.committee.kill_strategy(strategy_id, reason)
    
    def get_risk_metrics(self) -> RiskMetrics:
        """Get risk metrics."""
        return self.committee.get_risk_metrics()
    
    def get_layer_state(self) -> Dict[str, Any]:
        """Get layer state."""
        return {
            'last_risk_update': self.last_risk_update.isoformat() if self.last_risk_update else None,
            'risk_update_count': self.risk_update_count,
            'committee_state': self.committee.get_committee_state()
        }
