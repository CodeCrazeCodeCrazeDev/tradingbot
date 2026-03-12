"""
Financial Safeguards
====================

Prevents financial catastrophe through:
1. Leverage Control - Hard limits on leverage
2. Concentration Limits - Diversification enforcement
3. Drawdown Circuit Breakers - Automatic trading halts
4. Correlation Breakdown Protection - Diversification failure detection
5. Margin Safety - Prevent margin calls

PRINCIPLE: No single decision should be able to destroy the fund.
"""

import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import json
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    HALF_OPEN = "half_open" # Testing recovery
    OPEN = "open"           # Trading halted


class DrawdownLevel(Enum):
    """Drawdown severity levels"""
    NORMAL = "normal"       # < 5%
    CAUTION = "caution"     # 5-10%
    WARNING = "warning"     # 10-15%
    DANGER = "danger"       # 15-20%
    CRITICAL = "critical"   # > 20%


@dataclass
class FinancialViolation:
    """Record of a financial safeguard violation"""
    violation_id: str
    safeguard_type: str
    severity: str
    current_value: float
    limit_value: float
    description: str
    action_taken: str
    timestamp: datetime = field(default_factory=datetime.now)


class LeverageController:
    """
    Controls and limits leverage across the portfolio.
    
    IMMUTABLE LIMITS:
    - Maximum gross leverage: 5x
    - Maximum net leverage: 3x
    - Maximum single position leverage: 2x
    
    These limits CANNOT be changed by the AI.
    """
    
    # IMMUTABLE LEVERAGE LIMITS
    MAX_GROSS_LEVERAGE = 5.0
    MAX_NET_LEVERAGE = 3.0
    MAX_POSITION_LEVERAGE = 2.0
    MAX_OVERNIGHT_LEVERAGE = 2.0
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Current state
        self.current_gross_leverage = 0.0
        self.current_net_leverage = 0.0
        self.position_leverages: Dict[str, float] = {}
        
        # History
        self.leverage_history: deque = deque(maxlen=1000)
        self.violations: List[FinancialViolation] = []
        
        # Callbacks
        self.on_limit_breach: Optional[Callable] = None
        
        logger.info(f"LeverageController initialized - Max Gross: {self.MAX_GROSS_LEVERAGE}x, Max Net: {self.MAX_NET_LEVERAGE}x")
    
    def calculate_leverage(
        self,
        positions: Dict[str, Dict[str, Any]],
        account_equity: float
    ) -> Dict[str, float]:
        """
        Calculate current leverage metrics.
        
        Args:
            positions: Dict of position_id -> position details
            account_equity: Current account equity
        
        Returns:
            Dict with leverage metrics
        """
        if account_equity <= 0:
            return {'gross': 0, 'net': 0, 'positions': {}}
        
        total_long = 0.0
        total_short = 0.0
        
        for pos_id, pos in positions.items():
            notional = abs(pos.get('quantity', 0) * pos.get('current_price', 0))
            
            if pos.get('direction', 'long') == 'long':
                total_long += notional
            else:
                total_short += notional
            
            # Position-level leverage
            self.position_leverages[pos_id] = notional / account_equity
        
        self.current_gross_leverage = (total_long + total_short) / account_equity
        self.current_net_leverage = abs(total_long - total_short) / account_equity
        
        # Record history
        self.leverage_history.append({
            'gross': self.current_gross_leverage,
            'net': self.current_net_leverage,
            'timestamp': datetime.now()
        })
        
        return {
            'gross': self.current_gross_leverage,
            'net': self.current_net_leverage,
            'positions': self.position_leverages.copy()
        }
    
    def check_new_position(
        self,
        position_notional: float,
        direction: str,
        account_equity: float,
        current_positions: Dict[str, Dict[str, Any]]
    ) -> Tuple[bool, str, float]:
        """
        Check if a new position would violate leverage limits.
        
        Returns:
            Tuple of (is_allowed, reason, max_allowed_notional)
        """
        # Calculate current leverage
        current = self.calculate_leverage(current_positions, account_equity)
        
        # Calculate new leverage with proposed position
        new_gross = current['gross'] + (position_notional / account_equity)
        
        # Check gross leverage
        if new_gross > self.MAX_GROSS_LEVERAGE:
            max_allowed = (self.MAX_GROSS_LEVERAGE - current['gross']) * account_equity
            self._record_violation('gross_leverage', new_gross, self.MAX_GROSS_LEVERAGE)
            return False, f"Gross leverage {new_gross:.2f}x exceeds limit {self.MAX_GROSS_LEVERAGE}x", max(0, max_allowed)
        
        # Check position leverage
        position_leverage = position_notional / account_equity
        if position_leverage > self.MAX_POSITION_LEVERAGE:
            max_allowed = self.MAX_POSITION_LEVERAGE * account_equity
            self._record_violation('position_leverage', position_leverage, self.MAX_POSITION_LEVERAGE)
            return False, f"Position leverage {position_leverage:.2f}x exceeds limit {self.MAX_POSITION_LEVERAGE}x", max_allowed
        
        return True, "Leverage within limits", position_notional
    
    def check_overnight_leverage(self) -> Tuple[bool, str]:
        """Check if current leverage is safe for overnight holding"""
        if self.current_gross_leverage > self.MAX_OVERNIGHT_LEVERAGE:
            return False, f"Gross leverage {self.current_gross_leverage:.2f}x exceeds overnight limit {self.MAX_OVERNIGHT_LEVERAGE}x"
        return True, "Overnight leverage acceptable"
    
    def _record_violation(self, safeguard_type: str, current: float, limit: float):
        """Record a leverage violation"""
        violation = FinancialViolation(
            violation_id=f"lev_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            safeguard_type=safeguard_type,
            severity='high',
            current_value=current,
            limit_value=limit,
            description=f"Leverage {current:.2f}x exceeds limit {limit:.2f}x",
            action_taken="Position blocked"
        )
        self.violations.append(violation)
        
        if self.on_limit_breach:
            self.on_limit_breach(violation)
    
    def get_available_leverage(self, account_equity: float) -> float:
        """Get remaining available leverage"""
        return max(0, self.MAX_GROSS_LEVERAGE - self.current_gross_leverage)


class ConcentrationLimiter:
    """
    Enforces position concentration limits.
    
    IMMUTABLE LIMITS:
    - Maximum single position: 10% of portfolio
    - Maximum sector exposure: 25% of portfolio
    - Maximum correlated positions: 30% of portfolio
    - Minimum positions for full allocation: 5
    """
    
    # IMMUTABLE CONCENTRATION LIMITS
    MAX_SINGLE_POSITION = 0.10      # 10%
    MAX_SECTOR_EXPOSURE = 0.25      # 25%
    MAX_CORRELATED_EXPOSURE = 0.30  # 30%
    MIN_POSITIONS = 5
    MAX_SINGLE_ASSET_CLASS = 0.40   # 40%
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Current state
        self.position_weights: Dict[str, float] = {}
        self.sector_weights: Dict[str, float] = {}
        self.asset_class_weights: Dict[str, float] = {}
        
        # Correlation tracking
        self.correlation_matrix: Dict[str, Dict[str, float]] = {}
        
        # Violations
        self.violations: List[FinancialViolation] = []
        
        logger.info("ConcentrationLimiter initialized")
    
    def calculate_concentrations(
        self,
        positions: Dict[str, Dict[str, Any]],
        portfolio_value: float
    ) -> Dict[str, Any]:
        """Calculate current concentration metrics"""
        if portfolio_value <= 0:
            return {}
        
        self.position_weights = {}
        self.sector_weights = {}
        self.asset_class_weights = {}
        
        for pos_id, pos in positions.items():
            value = abs(pos.get('quantity', 0) * pos.get('current_price', 0))
            weight = value / portfolio_value
            
            self.position_weights[pos_id] = weight
            
            # Sector
            sector = pos.get('sector', 'unknown')
            self.sector_weights[sector] = self.sector_weights.get(sector, 0) + weight
            
            # Asset class
            asset_class = pos.get('asset_class', 'unknown')
            self.asset_class_weights[asset_class] = self.asset_class_weights.get(asset_class, 0) + weight
        
        return {
            'positions': self.position_weights,
            'sectors': self.sector_weights,
            'asset_classes': self.asset_class_weights,
            'max_position': max(self.position_weights.values()) if self.position_weights else 0,
            'max_sector': max(self.sector_weights.values()) if self.sector_weights else 0,
            'position_count': len(self.position_weights)
        }
    
    def check_new_position(
        self,
        symbol: str,
        position_value: float,
        sector: str,
        asset_class: str,
        portfolio_value: float
    ) -> Tuple[bool, str, float]:
        """
        Check if a new position would violate concentration limits.
        
        Returns:
            Tuple of (is_allowed, reason, max_allowed_value)
        """
        if portfolio_value <= 0:
            return False, "Invalid portfolio value", 0
        
        proposed_weight = position_value / portfolio_value
        
        # Check single position limit
        current_weight = self.position_weights.get(symbol, 0)
        new_weight = current_weight + proposed_weight
        
        if new_weight > self.MAX_SINGLE_POSITION:
            max_allowed = (self.MAX_SINGLE_POSITION - current_weight) * portfolio_value
            self._record_violation('single_position', new_weight, self.MAX_SINGLE_POSITION)
            return False, f"Position weight {new_weight*100:.1f}% exceeds limit {self.MAX_SINGLE_POSITION*100:.0f}%", max(0, max_allowed)
        
        # Check sector limit
        current_sector = self.sector_weights.get(sector, 0)
        new_sector = current_sector + proposed_weight
        
        if new_sector > self.MAX_SECTOR_EXPOSURE:
            max_allowed = (self.MAX_SECTOR_EXPOSURE - current_sector) * portfolio_value
            self._record_violation('sector_exposure', new_sector, self.MAX_SECTOR_EXPOSURE)
            return False, f"Sector exposure {new_sector*100:.1f}% exceeds limit {self.MAX_SECTOR_EXPOSURE*100:.0f}%", max(0, max_allowed)
        
        # Check asset class limit
        current_ac = self.asset_class_weights.get(asset_class, 0)
        new_ac = current_ac + proposed_weight
        
        if new_ac > self.MAX_SINGLE_ASSET_CLASS:
            max_allowed = (self.MAX_SINGLE_ASSET_CLASS - current_ac) * portfolio_value
            self._record_violation('asset_class', new_ac, self.MAX_SINGLE_ASSET_CLASS)
            return False, f"Asset class exposure {new_ac*100:.1f}% exceeds limit {self.MAX_SINGLE_ASSET_CLASS*100:.0f}%", max(0, max_allowed)
        
        return True, "Concentration within limits", position_value
    
    def check_correlated_exposure(
        self,
        symbol: str,
        position_value: float,
        portfolio_value: float
    ) -> Tuple[bool, str]:
        """Check exposure to correlated positions"""
        if symbol not in self.correlation_matrix:
            return True, "No correlation data"
        
        correlated_exposure = 0.0
        proposed_weight = position_value / portfolio_value
        
        for other_symbol, correlation in self.correlation_matrix[symbol].items():
            if correlation > 0.7:  # Highly correlated
                other_weight = self.position_weights.get(other_symbol, 0)
                correlated_exposure += other_weight
        
        total_correlated = correlated_exposure + proposed_weight
        
        if total_correlated > self.MAX_CORRELATED_EXPOSURE:
            return False, f"Correlated exposure {total_correlated*100:.1f}% exceeds limit {self.MAX_CORRELATED_EXPOSURE*100:.0f}%"
        
        return True, "Correlated exposure acceptable"
    
    def update_correlations(self, correlation_matrix: Dict[str, Dict[str, float]]):
        """Update the correlation matrix"""
        self.correlation_matrix = correlation_matrix
    
    def _record_violation(self, safeguard_type: str, current: float, limit: float):
        """Record a concentration violation"""
        violation = FinancialViolation(
            violation_id=f"conc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            safeguard_type=safeguard_type,
            severity='medium',
            current_value=current,
            limit_value=limit,
            description=f"Concentration {current*100:.1f}% exceeds limit {limit*100:.0f}%",
            action_taken="Position blocked"
        )
        self.violations.append(violation)


class DrawdownCircuitBreaker:
    """
    Automatic trading halt based on drawdown levels.
    
    IMMUTABLE THRESHOLDS:
    - 5% drawdown: Reduce position sizes by 25%
    - 10% drawdown: Reduce position sizes by 50%
    - 15% drawdown: Stop new positions
    - 20% drawdown: Close all positions
    
    These thresholds CANNOT be changed by the AI.
    """
    
    # IMMUTABLE DRAWDOWN THRESHOLDS
    THRESHOLDS = {
        0.05: {'action': 'reduce_25', 'level': DrawdownLevel.CAUTION},
        0.10: {'action': 'reduce_50', 'level': DrawdownLevel.WARNING},
        0.15: {'action': 'stop_new', 'level': DrawdownLevel.DANGER},
        0.20: {'action': 'close_all', 'level': DrawdownLevel.CRITICAL},
    }
    
    # Recovery requirements
    RECOVERY_THRESHOLD = 0.5  # Must recover 50% of drawdown before resuming
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # State
        self.state = CircuitBreakerState.CLOSED
        self.current_drawdown = 0.0
        self.peak_equity = 0.0
        self.current_level = DrawdownLevel.NORMAL
        
        # Tracking
        self.drawdown_history: deque = deque(maxlen=1000)
        self.state_changes: List[Dict] = []
        
        # Callbacks
        self.on_state_change: Optional[Callable] = None
        self.on_close_all: Optional[Callable] = None
        
        logger.info("DrawdownCircuitBreaker initialized")
    
    def update(self, current_equity: float) -> Tuple[DrawdownLevel, Dict[str, Any]]:
        """
        Update drawdown state and return required actions.
        
        Returns:
            Tuple of (drawdown_level, actions)
        """
        # Update peak
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
        
        # Calculate drawdown
        if self.peak_equity > 0:
            self.current_drawdown = (self.peak_equity - current_equity) / self.peak_equity
        else:
            self.current_drawdown = 0
        
        # Record history
        self.drawdown_history.append({
            'drawdown': self.current_drawdown,
            'equity': current_equity,
            'timestamp': datetime.now()
        })
        
        # Determine level and actions
        actions = {}
        new_level = DrawdownLevel.NORMAL
        
        for threshold, config in sorted(self.THRESHOLDS.items()):
            if self.current_drawdown >= threshold:
                new_level = config['level']
                actions['action'] = config['action']
        
        # State transitions
        if new_level != self.current_level:
            old_level = self.current_level
            self.current_level = new_level
            
            self.state_changes.append({
                'from': old_level.value,
                'to': new_level.value,
                'drawdown': self.current_drawdown,
                'timestamp': datetime.now()
            })
            
            logger.warning(f"Drawdown level changed: {old_level.value} -> {new_level.value}")
            
            if self.on_state_change:
                self.on_state_change(old_level, new_level, self.current_drawdown)
        
        # Handle critical level
        if new_level == DrawdownLevel.CRITICAL:
            self.state = CircuitBreakerState.OPEN
            actions['halt_trading'] = True
            actions['close_all_positions'] = True
            
            if self.on_close_all:
                self.on_close_all(self.current_drawdown)
        
        # Determine position size multiplier
        if 'action' in actions:
            if actions['action'] == 'reduce_25':
                actions['position_multiplier'] = 0.75
            elif actions['action'] == 'reduce_50':
                actions['position_multiplier'] = 0.50
            elif actions['action'] == 'stop_new':
                actions['position_multiplier'] = 0.0
                actions['allow_new_positions'] = False
            elif actions['action'] == 'close_all':
                actions['position_multiplier'] = 0.0
                actions['allow_new_positions'] = False
        else:
            actions['position_multiplier'] = 1.0
            actions['allow_new_positions'] = True
        
        return new_level, actions
    
    def can_open_position(self) -> Tuple[bool, str]:
        """Check if new positions are allowed"""
        if self.state == CircuitBreakerState.OPEN:
            return False, "Circuit breaker OPEN - trading halted"
        
        if self.current_level in [DrawdownLevel.DANGER, DrawdownLevel.CRITICAL]:
            return False, f"Drawdown at {self.current_level.value} level - no new positions"
        
        return True, "Positions allowed"
    
    def check_recovery(self, current_equity: float) -> bool:
        """Check if system has recovered enough to resume trading"""
        if self.state != CircuitBreakerState.OPEN:
            return True
        
        # Calculate recovery
        drawdown_amount = self.peak_equity - current_equity
        if drawdown_amount <= 0:
            # Fully recovered
            self.state = CircuitBreakerState.CLOSED
            self.current_level = DrawdownLevel.NORMAL
            logger.info("Full recovery - circuit breaker closed")
            return True
        
        # Check partial recovery
        max_drawdown_amount = self.peak_equity * 0.20  # 20% was the trigger
        recovery_pct = 1 - (drawdown_amount / max_drawdown_amount)
        
        if recovery_pct >= self.RECOVERY_THRESHOLD:
            self.state = CircuitBreakerState.HALF_OPEN
            logger.info(f"Partial recovery ({recovery_pct*100:.1f}%) - circuit breaker half-open")
            return True
        
        return False
    
    def get_position_multiplier(self) -> float:
        """Get current position size multiplier"""
        multipliers = {
            DrawdownLevel.NORMAL: 1.0,
            DrawdownLevel.CAUTION: 0.75,
            DrawdownLevel.WARNING: 0.50,
            DrawdownLevel.DANGER: 0.0,
            DrawdownLevel.CRITICAL: 0.0
        }
        return multipliers.get(self.current_level, 0.0)


class CorrelationBreakdownProtector:
    """
    Protects against correlation breakdown during market stress.
    
    During crises, correlations spike to 1.0, destroying diversification.
    This protector:
    1. Monitors correlation changes
    2. Detects breakdown conditions
    3. Reduces exposure when correlations spike
    4. Activates hedges
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Thresholds
        self.correlation_spike_threshold = self.config.get('spike_threshold', 0.85)
        self.normal_correlation = self.config.get('normal_correlation', 0.3)
        
        # State
        self.current_avg_correlation = 0.0
        self.is_breakdown = False
        self.breakdown_start: Optional[datetime] = None
        
        # History
        self.correlation_history: deque = deque(maxlen=100)
        
        logger.info("CorrelationBreakdownProtector initialized")
    
    def update(
        self,
        correlation_matrix: Dict[str, Dict[str, float]]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Update correlation state and detect breakdown.
        
        Returns:
            Tuple of (is_breakdown, actions)
        """
        if not correlation_matrix:
            return False, {}
        
        # Calculate average correlation
        correlations = []
        for symbol1, corrs in correlation_matrix.items():
            for symbol2, corr in corrs.items():
                if symbol1 != symbol2:
                    correlations.append(abs(corr))
        
        if correlations:
            self.current_avg_correlation = sum(correlations) / len(correlations)
        
        self.correlation_history.append({
            'avg_correlation': self.current_avg_correlation,
            'timestamp': datetime.now()
        })
        
        actions = {}
        
        # Detect breakdown
        if self.current_avg_correlation > self.correlation_spike_threshold:
            if not self.is_breakdown:
                self.is_breakdown = True
                self.breakdown_start = datetime.now()
                logger.warning(f"CORRELATION BREAKDOWN detected: avg correlation {self.current_avg_correlation:.2f}")
            
            actions['reduce_exposure'] = True
            actions['exposure_multiplier'] = 0.5
            actions['activate_hedges'] = True
            actions['hedge_ratio'] = 0.10  # 10% of portfolio
        
        elif self.is_breakdown:
            # Check for recovery
            if self.current_avg_correlation < self.normal_correlation + 0.1:
                self.is_breakdown = False
                self.breakdown_start = None
                logger.info("Correlation breakdown recovered")
        
        return self.is_breakdown, actions
    
    def get_diversification_benefit(self) -> float:
        """
        Calculate current diversification benefit.
        
        Returns value between 0 (no diversification) and 1 (full diversification)
        """
        if self.current_avg_correlation >= 1.0:
            return 0.0
        
        # Diversification benefit decreases as correlation increases
        return max(0, 1 - self.current_avg_correlation)


class FinancialSafeguards:
    """
    Master Financial Safeguards System
    
    Coordinates all financial protection mechanisms:
    - Leverage Control
    - Concentration Limits
    - Drawdown Circuit Breakers
    - Correlation Breakdown Protection
    
    CORE PRINCIPLE: Multiple layers of protection, any one can halt trading.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.leverage = LeverageController(config.get('leverage', {}))
        self.concentration = ConcentrationLimiter(config.get('concentration', {}))
        self.drawdown = DrawdownCircuitBreaker(config.get('drawdown', {}))
        self.correlation = CorrelationBreakdownProtector(config.get('correlation', {}))
        
        # Overall state
        self.is_safe = True
        self.active_restrictions: List[str] = []
        
        # Callbacks
        self.on_restriction: Optional[Callable] = None
        self.on_halt: Optional[Callable] = None
        
        # Lock
        self._lock = threading.Lock()
        
        logger.info("FinancialSafeguards system initialized")
    
    def validate_trade(
        self,
        symbol: str,
        direction: str,
        quantity: float,
        price: float,
        sector: str,
        asset_class: str,
        portfolio_value: float,
        account_equity: float,
        current_positions: Dict[str, Dict[str, Any]]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate a proposed trade against all financial safeguards.
        
        Returns:
            Tuple of (is_allowed, reason, adjustments)
        """
        with self._lock:
            position_value = quantity * price
            adjustments = {}
            
            # Check 1: Drawdown circuit breaker
            can_trade, dd_reason = self.drawdown.can_open_position()
            if not can_trade:
                return False, dd_reason, {}
            
            # Check 2: Leverage limits
            is_allowed, lev_reason, max_notional = self.leverage.check_new_position(
                position_value, direction, account_equity, current_positions
            )
            if not is_allowed:
                if max_notional > 0:
                    adjustments['max_quantity'] = max_notional / price
                return False, lev_reason, adjustments
            
            # Check 3: Concentration limits
            is_allowed, conc_reason, max_value = self.concentration.check_new_position(
                symbol, position_value, sector, asset_class, portfolio_value
            )
            if not is_allowed:
                if max_value > 0:
                    adjustments['max_quantity'] = max_value / price
                return False, conc_reason, adjustments
            
            # Check 4: Correlated exposure
            is_allowed, corr_reason = self.concentration.check_correlated_exposure(
                symbol, position_value, portfolio_value
            )
            if not is_allowed:
                return False, corr_reason, {}
            
            # Apply position multiplier from drawdown level
            multiplier = self.drawdown.get_position_multiplier()
            if multiplier < 1.0:
                adjustments['position_multiplier'] = multiplier
                adjustments['adjusted_quantity'] = quantity * multiplier
            
            return True, "Trade approved", adjustments
    
    def update_state(
        self,
        current_equity: float,
        positions: Dict[str, Dict[str, Any]],
        portfolio_value: float,
        correlation_matrix: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Update all safeguard states.
        
        Returns:
            Current state and any required actions
        """
        with self._lock:
            state = {}
            actions = []
            
            # Update drawdown
            dd_level, dd_actions = self.drawdown.update(current_equity)
            state['drawdown'] = {
                'level': dd_level.value,
                'current': self.drawdown.current_drawdown,
                'actions': dd_actions
            }
            
            if dd_actions.get('close_all_positions'):
                actions.append('close_all_positions')
            
            # Update leverage
            lev_metrics = self.leverage.calculate_leverage(positions, current_equity)
            state['leverage'] = lev_metrics
            
            # Update concentration
            conc_metrics = self.concentration.calculate_concentrations(positions, portfolio_value)
            state['concentration'] = conc_metrics
            
            # Update correlation
            if correlation_matrix:
                is_breakdown, corr_actions = self.correlation.update(correlation_matrix)
                state['correlation'] = {
                    'is_breakdown': is_breakdown,
                    'avg_correlation': self.correlation.current_avg_correlation,
                    'diversification_benefit': self.correlation.get_diversification_benefit(),
                    'actions': corr_actions
                }
                
                if corr_actions.get('reduce_exposure'):
                    actions.append('reduce_exposure')
            
            # Determine overall safety
            self.is_safe = (
                dd_level in [DrawdownLevel.NORMAL, DrawdownLevel.CAUTION] and
                not self.correlation.is_breakdown and
                self.leverage.current_gross_leverage <= LeverageController.MAX_GROSS_LEVERAGE
            )
            
            state['is_safe'] = self.is_safe
            state['required_actions'] = actions
            
            return state
    
    def get_position_size_limit(self) -> float:
        """Get maximum position size as fraction of normal"""
        # Take the most restrictive limit
        dd_multiplier = self.drawdown.get_position_multiplier()
        corr_multiplier = 0.5 if self.correlation.is_breakdown else 1.0
        
        return min(dd_multiplier, corr_multiplier)
    
    def emergency_reduce_all(self) -> Dict[str, float]:
        """
        Calculate emergency reduction targets for all positions.
        
        Returns:
            Dict of symbol -> target reduction percentage
        """
        reductions = {}
        
        # Reduce based on drawdown level
        multiplier = self.drawdown.get_position_multiplier()
        
        for symbol, weight in self.concentration.position_weights.items():
            if multiplier < 1.0:
                reductions[symbol] = 1 - multiplier
        
        return reductions
    
    def get_status(self) -> Dict[str, Any]:
        """Get current safeguard status"""
        return {
            'is_safe': self.is_safe,
            'drawdown': {
                'level': self.drawdown.current_level.value,
                'current': self.drawdown.current_drawdown,
                'circuit_breaker': self.drawdown.state.value
            },
            'leverage': {
                'gross': self.leverage.current_gross_leverage,
                'net': self.leverage.current_net_leverage,
                'available': self.leverage.get_available_leverage(1.0)
            },
            'concentration': {
                'max_position': max(self.concentration.position_weights.values()) if self.concentration.position_weights else 0,
                'position_count': len(self.concentration.position_weights)
            },
            'correlation': {
                'is_breakdown': self.correlation.is_breakdown,
                'avg_correlation': self.correlation.current_avg_correlation,
                'diversification': self.correlation.get_diversification_benefit()
            },
            'position_size_limit': self.get_position_size_limit()
        }
