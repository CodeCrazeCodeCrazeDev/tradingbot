"""
AlphaAlgo MSOS - Core Architecture

The foundational layer of the Market Survival Operating System.
Defines immutable constraints, system hierarchy, and core decision structures.

ABSOLUTE AXIOMS (CANNOT BE MODIFIED):
1. Capital is non-renewable
2. Markets are partially observable and adversarial
3. Intelligence does not imply correctness
4. Confidence without calibration is dangerous
5. Any assumption can fail
6. Survival dominates performance
7. Being flat is a valid position
8. Learning under stress is forbidden
9. No decision is justified without constraint compliance
10. No override exists for these axioms

Author: AlphaAlgo MSOS
"""

import hashlib
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# ABSOLUTE AXIOMS - IMMUTABLE, CANNOT BE OVERRIDDEN
# =============================================================================

ABSOLUTE_AXIOMS = frozenset([
    "Capital is non-renewable",
    "Markets are partially observable and adversarial",
    "Intelligence does not imply correctness",
    "Confidence without calibration is dangerous",
    "Any assumption can fail",
    "Survival dominates performance",
    "Being flat is a valid position",
    "Learning under stress is forbidden",
    "No decision is justified without constraint compliance",
    "No override exists for these axioms"
])

# Cryptographic hash of axioms - used to verify integrity
AXIOM_HASH = hashlib.sha256(str(sorted(ABSOLUTE_AXIOMS)).encode()).hexdigest()


class HierarchyLevel(Enum):
    """
    System hierarchy levels - STRICT ordering.
    No lower layer may override a higher layer.
    """
    CONSTRAINTS = 1      # Absolute authority - cannot be overridden
    CONTROL = 2          # Risk and exposure control
    EXPOSURE = 3         # Position sizing and allocation
    STRATEGY = 4         # Strategy selection and execution
    INTELLIGENCE = 5     # ML/AI predictions and signals
    PREDICTION = 6       # Lowest authority - predictions only


class DecisionType(Enum):
    """Types of decisions the system can make"""
    TRADE_ALLOWED = auto()
    TRADE_FORBIDDEN = auto()
    EXPOSURE_REDUCED = auto()
    EXPOSURE_ZERO = auto()
    STRATEGY_MUTED = auto()
    STRATEGY_RETIRED = auto()
    LEARNING_FROZEN = auto()
    MARKET_INVALID = auto()
    ASSUMPTION_VIOLATED = auto()
    SEMANTIC_DRIFT = auto()
    REGIME_HOSTILE = auto()
    UNCERTAINTY_EXCEEDED = auto()


class ConstraintType(Enum):
    """Types of immutable constraints"""
    MAX_RISK_PER_TRADE = auto()
    MAX_DAILY_LOSS = auto()
    MAX_DRAWDOWN = auto()
    MAX_LEVERAGE = auto()
    MAX_POSITION_SIZE = auto()
    MAX_CORRELATION = auto()
    MIN_LIQUIDITY = auto()
    MAX_SPREAD = auto()
    MAX_VOLATILITY = auto()
    MIN_MARKET_VALIDITY = auto()
    MAX_UNCERTAINTY = auto()
    MIN_CONFIDENCE_CALIBRATION = auto()


@dataclass(frozen=True)
class ImmutableConstraint:
    """A single immutable constraint that cannot be modified at runtime"""
    constraint_type: ConstraintType
    value: float
    description: str
    violation_action: DecisionType
    
    def is_violated(self, current_value: float) -> bool:
        """Check if constraint is violated"""
        try:
            if self.constraint_type in [
                ConstraintType.MAX_RISK_PER_TRADE,
                ConstraintType.MAX_DAILY_LOSS,
                ConstraintType.MAX_DRAWDOWN,
                ConstraintType.MAX_LEVERAGE,
                ConstraintType.MAX_POSITION_SIZE,
                ConstraintType.MAX_CORRELATION,
                ConstraintType.MAX_SPREAD,
                ConstraintType.MAX_VOLATILITY,
                ConstraintType.MAX_UNCERTAINTY
            ]:
                return current_value > self.value
            else:  # MIN constraints
                return current_value < self.value
        except Exception as e:
            logger.error(f"Error in is_violated: {e}")
            raise


class ImmutableConstraints:
    """
    Container for all immutable constraints.
    These constraints CANNOT be modified at runtime.
    They represent absolute boundaries that protect capital.
    """
    
    # These values are FROZEN and cannot be changed
    _CONSTRAINTS: FrozenSet[ImmutableConstraint] = frozenset([
        ImmutableConstraint(
            ConstraintType.MAX_RISK_PER_TRADE,
            0.02,  # 2% max risk per trade
            "Maximum risk per single trade",
            DecisionType.TRADE_FORBIDDEN
        ),
        ImmutableConstraint(
            ConstraintType.MAX_DAILY_LOSS,
            0.05,  # 5% max daily loss
            "Maximum daily loss before trading halt",
            DecisionType.EXPOSURE_ZERO
        ),
        ImmutableConstraint(
            ConstraintType.MAX_DRAWDOWN,
            0.20,  # 20% max drawdown
            "Maximum drawdown before system shutdown",
            DecisionType.EXPOSURE_ZERO
        ),
        ImmutableConstraint(
            ConstraintType.MAX_LEVERAGE,
            5.0,  # 5x max leverage
            "Maximum leverage allowed",
            DecisionType.EXPOSURE_REDUCED
        ),
        ImmutableConstraint(
            ConstraintType.MAX_POSITION_SIZE,
            0.10,  # 10% max position size
            "Maximum position size as fraction of capital",
            DecisionType.TRADE_FORBIDDEN
        ),
        ImmutableConstraint(
            ConstraintType.MAX_CORRELATION,
            0.70,  # 70% max correlation
            "Maximum correlation between positions",
            DecisionType.TRADE_FORBIDDEN
        ),
        ImmutableConstraint(
            ConstraintType.MIN_LIQUIDITY,
            0.30,  # 30% minimum liquidity score
            "Minimum liquidity required to trade",
            DecisionType.MARKET_INVALID
        ),
        ImmutableConstraint(
            ConstraintType.MAX_SPREAD,
            0.005,  # 0.5% max spread
            "Maximum spread allowed",
            DecisionType.MARKET_INVALID
        ),
        ImmutableConstraint(
            ConstraintType.MAX_VOLATILITY,
            0.10,  # 10% max volatility (annualized daily)
            "Maximum volatility before exposure reduction",
            DecisionType.EXPOSURE_REDUCED
        ),
        ImmutableConstraint(
            ConstraintType.MIN_MARKET_VALIDITY,
            0.50,  # 50% minimum market validity score
            "Minimum market validity required",
            DecisionType.MARKET_INVALID
        ),
        ImmutableConstraint(
            ConstraintType.MAX_UNCERTAINTY,
            0.80,  # 80% max uncertainty
            "Maximum uncertainty before exposure reduction",
            DecisionType.EXPOSURE_REDUCED
        ),
        ImmutableConstraint(
            ConstraintType.MIN_CONFIDENCE_CALIBRATION,
            0.60,  # 60% minimum confidence calibration
            "Minimum confidence calibration required",
            DecisionType.STRATEGY_MUTED
        )
    ])
    
    # Hash to verify integrity
    _CONSTRAINT_HASH = hashlib.sha256(
        str(sorted([(c.constraint_type.name, c.value) for c in _CONSTRAINTS])).encode()
    ).hexdigest()
    
    def __init__(self):
        try:
            self._verify_integrity()
            self.logger = logging.getLogger("msos.constraints")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _verify_integrity(self) -> bool:
        """Verify constraints have not been tampered with"""
        try:
            current_hash = hashlib.sha256(
                str(sorted([(c.constraint_type.name, c.value) for c in self._CONSTRAINTS])).encode()
            ).hexdigest()
            if current_hash != self._CONSTRAINT_HASH:
                raise RuntimeError("CRITICAL: Constraint integrity violation detected!")
            return True
        except Exception as e:
            logger.error(f"Error in _verify_integrity: {e}")
            raise
    
    def get_constraint(self, constraint_type: ConstraintType) -> Optional[ImmutableConstraint]:
        """Get a specific constraint"""
        try:
            for c in self._CONSTRAINTS:
                if c.constraint_type == constraint_type:
                    return c
            return None
        except Exception as e:
            logger.error(f"Error in get_constraint: {e}")
            raise
    
    def check_all(self, current_values: Dict[ConstraintType, float]) -> List[Tuple[ImmutableConstraint, bool]]:
        """Check all constraints against current values"""
        try:
            results = []
            for constraint in self._CONSTRAINTS:
                if constraint.constraint_type in current_values:
                    violated = constraint.is_violated(current_values[constraint.constraint_type])
                    results.append((constraint, violated))
            return results
        except Exception as e:
            logger.error(f"Error in check_all: {e}")
            raise
    
    def get_violations(self, current_values: Dict[ConstraintType, float]) -> List[ImmutableConstraint]:
        """Get list of violated constraints"""
        try:
            violations = []
            for constraint, violated in self.check_all(current_values):
                if violated:
                    violations.append(constraint)
            return violations
        except Exception as e:
            logger.error(f"Error in get_violations: {e}")
            raise
    
    @property
    def all_constraints(self) -> FrozenSet[ImmutableConstraint]:
        """Get all constraints (read-only)"""
        return self._CONSTRAINTS


class SystemHierarchy:
    """
    Enforces the strict system hierarchy.
    No lower layer may override a higher layer.
    """
    
    def __init__(self):
        try:
            self.logger = logging.getLogger("msos.hierarchy")
            self._layer_decisions: Dict[HierarchyLevel, DecisionType] = {}
            self._layer_reasons: Dict[HierarchyLevel, str] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def can_override(self, requesting_layer: HierarchyLevel, target_layer: HierarchyLevel) -> bool:
        """Check if requesting layer can override target layer"""
        # Lower value = higher authority
        return requesting_layer.value < target_layer.value
    
    def set_decision(self, layer: HierarchyLevel, decision: DecisionType, reason: str) -> bool:
        """
        Set a decision at a specific layer.
        Returns False if a higher layer has already made a conflicting decision.
        """
        # Check if any higher layer has made a decision
        try:
            for existing_layer, existing_decision in self._layer_decisions.items():
                if existing_layer.value < layer.value:
                    # Higher layer exists - check for conflict
                    if self._is_conflicting(existing_decision, decision):
                        self.logger.warning(
                            f"Layer {layer.name} cannot override {existing_layer.name}: "
                            f"{existing_decision.name} vs {decision.name}"
                        )
                        return False
        
            self._layer_decisions[layer] = decision
            self._layer_reasons[layer] = reason
            return True
        except Exception as e:
            logger.error(f"Error in set_decision: {e}")
            raise
    
    def _is_conflicting(self, higher_decision: DecisionType, lower_decision: DecisionType) -> bool:
        """Check if two decisions conflict"""
        # If higher layer forbids, lower cannot allow
        try:
            forbidden_decisions = {
                DecisionType.TRADE_FORBIDDEN,
                DecisionType.EXPOSURE_ZERO,
                DecisionType.MARKET_INVALID,
                DecisionType.STRATEGY_RETIRED
            }
        
            allowed_decisions = {
                DecisionType.TRADE_ALLOWED
            }
        
            if higher_decision in forbidden_decisions and lower_decision in allowed_decisions:
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in _is_conflicting: {e}")
            raise
    
    def get_final_decision(self) -> Tuple[DecisionType, str, HierarchyLevel]:
        """Get the final decision based on hierarchy"""
        try:
            if not self._layer_decisions:
                return DecisionType.TRADE_FORBIDDEN, "No decision made", HierarchyLevel.CONSTRAINTS
        
            # Return decision from highest authority layer
            sorted_layers = sorted(self._layer_decisions.keys(), key=lambda x: x.value)
            highest_layer = sorted_layers[0]
        
            return (
                self._layer_decisions[highest_layer],
                self._layer_reasons[highest_layer],
                highest_layer
            )
        except Exception as e:
            logger.error(f"Error in get_final_decision: {e}")
            raise
    
    def reset(self):
        """Reset all layer decisions"""
        try:
            self._layer_decisions.clear()
            self._layer_reasons.clear()
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise


@dataclass
class MSOSState:
    """Current state of the MSOS system"""
    market_validity: float = 0.0
    uncertainty_level: float = 1.0
    regime_stability: float = 0.0
    signal_integrity: float = 0.0
    capital_at_risk: float = 0.0
    current_drawdown: float = 0.0
    daily_loss: float = 0.0
    learning_frozen: bool = False
    exposure_multiplier: float = 1.0
    active_constraints: List[ConstraintType] = field(default_factory=list)
    violated_constraints: List[ConstraintType] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    def is_tradable(self) -> bool:
        """Check if system state allows trading"""
        return (
            self.market_validity >= 0.5 and
            len(self.violated_constraints) == 0 and
            self.exposure_multiplier > 0
        )


@dataclass
class MSOSDecision:
    """A decision made by the MSOS system"""
    decision_type: DecisionType
    reason: str
    authority_layer: HierarchyLevel
    max_exposure: float
    constraints_checked: List[ConstraintType]
    constraints_violated: List[ConstraintType]
    state: MSOSState
    timestamp: float = field(default_factory=time.time)
    
    def is_trade_allowed(self) -> bool:
        """Check if trade is allowed"""
        return self.decision_type == DecisionType.TRADE_ALLOWED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'decision_type': self.decision_type.name,
            'reason': self.reason,
            'authority_layer': self.authority_layer.name,
            'max_exposure': self.max_exposure,
            'constraints_checked': [c.name for c in self.constraints_checked],
            'constraints_violated': [c.name for c in self.constraints_violated],
            'is_trade_allowed': self.is_trade_allowed(),
            'timestamp': self.timestamp
        }


@dataclass
class MSOSConfig:
    """Configuration for MSOS system"""
    # Constraint overrides are NOT allowed - these are informational only
    enable_strict_mode: bool = True
    log_all_decisions: bool = True
    require_explicit_justification: bool = True
    default_to_no_trade: bool = True
    
    # Cooldown periods
    loss_cooldown_seconds: int = 3600  # 1 hour after loss
    change_cooldown_seconds: int = 1800  # 30 min after parameter change
    
    # Evidence thresholds
    min_evidence_for_trade: float = 0.7
    min_evidence_for_change: float = 0.9
    
    # Learning controls
    freeze_learning_on_volatility: float = 0.05  # 5% daily volatility
    freeze_learning_on_drawdown: float = 0.10  # 10% drawdown


class MSOSCore:
    """
    Core MSOS system - the central decision authority.
    
    This class enforces the system hierarchy and immutable constraints.
    It is the final arbiter of all trading decisions.
    """
    
    def __init__(self, config: Optional[MSOSConfig] = None):
        try:
            self.config = config or MSOSConfig()
            self.constraints = ImmutableConstraints()
            self.hierarchy = SystemHierarchy()
            self.state = MSOSState()
            self.logger = logging.getLogger("msos.core")
        
            # Verify axiom integrity
            self._verify_axioms()
        
            self.logger.info("MSOS Core initialized - Capital preservation mode active")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _verify_axioms(self):
        """Verify absolute axioms have not been tampered with"""
        try:
            current_hash = hashlib.sha256(str(sorted(ABSOLUTE_AXIOMS)).encode()).hexdigest()
            if current_hash != AXIOM_HASH:
                raise RuntimeError("CRITICAL: Axiom integrity violation detected!")
            self.logger.debug("Axiom integrity verified")
        except Exception as e:
            logger.error(f"Error in _verify_axioms: {e}")
            raise
    
    def evaluate(
        self,
        strategy_id: str,
        symbol: str,
        current_values: Dict[ConstraintType, float],
        market_data: Optional[Dict[str, Any]] = None
    ) -> MSOSDecision:
        """
        Evaluate whether a trade should be allowed.
        
        This is the main entry point for all trading decisions.
        The system defaults to NO TRADE unless all constraints pass.
        """
        try:
            self.hierarchy.reset()
        
            # Update state
            self._update_state(current_values)
        
            # Layer 1: Check immutable constraints (HIGHEST AUTHORITY)
            violations = self.constraints.get_violations(current_values)
            if violations:
                violation_names = [v.constraint_type.name for v in violations]
                self.hierarchy.set_decision(
                    HierarchyLevel.CONSTRAINTS,
                    violations[0].violation_action,
                    f"Constraint violations: {violation_names}"
                )
            
                decision_type, reason, layer = self.hierarchy.get_final_decision()
                return MSOSDecision(
                    decision_type=decision_type,
                    reason=reason,
                    authority_layer=layer,
                    max_exposure=0.0,
                    constraints_checked=[c.constraint_type for c in self.constraints.all_constraints],
                    constraints_violated=[v.constraint_type for v in violations],
                    state=self.state
                )
        
            # Layer 2: Check control layer (market validity, regime)
            if not self._check_control_layer(current_values):
                decision_type, reason, layer = self.hierarchy.get_final_decision()
                return MSOSDecision(
                    decision_type=decision_type,
                    reason=reason,
                    authority_layer=layer,
                    max_exposure=0.0,
                    constraints_checked=[c.constraint_type for c in self.constraints.all_constraints],
                    constraints_violated=[],
                    state=self.state
                )
        
            # Layer 3: Calculate allowed exposure
            max_exposure = self._calculate_max_exposure(current_values)
        
            # Layer 4: Final decision
            if max_exposure > 0:
                self.hierarchy.set_decision(
                    HierarchyLevel.EXPOSURE,
                    DecisionType.TRADE_ALLOWED,
                    f"Trade allowed with max exposure: {max_exposure:.2%}"
                )
            else:
                self.hierarchy.set_decision(
                    HierarchyLevel.EXPOSURE,
                    DecisionType.EXPOSURE_ZERO,
                    "Calculated exposure is zero"
                )
        
            decision_type, reason, layer = self.hierarchy.get_final_decision()
        
            return MSOSDecision(
                decision_type=decision_type,
                reason=reason,
                authority_layer=layer,
                max_exposure=max_exposure,
                constraints_checked=[c.constraint_type for c in self.constraints.all_constraints],
                constraints_violated=[],
                state=self.state
            )
        except Exception as e:
            logger.error(f"Error in evaluate: {e}")
            raise
    
    def _update_state(self, current_values: Dict[ConstraintType, float]):
        """Update internal state from current values"""
        try:
            if ConstraintType.MIN_MARKET_VALIDITY in current_values:
                self.state.market_validity = current_values[ConstraintType.MIN_MARKET_VALIDITY]
            if ConstraintType.MAX_UNCERTAINTY in current_values:
                self.state.uncertainty_level = current_values[ConstraintType.MAX_UNCERTAINTY]
            if ConstraintType.MAX_DRAWDOWN in current_values:
                self.state.current_drawdown = current_values[ConstraintType.MAX_DRAWDOWN]
            if ConstraintType.MAX_DAILY_LOSS in current_values:
                self.state.daily_loss = current_values[ConstraintType.MAX_DAILY_LOSS]
        
            self.state.timestamp = time.time()
        except Exception as e:
            logger.error(f"Error in _update_state: {e}")
            raise
    
    def _check_control_layer(self, current_values: Dict[ConstraintType, float]) -> bool:
        """Check control layer conditions"""
        # Check market validity
        try:
            market_validity = current_values.get(ConstraintType.MIN_MARKET_VALIDITY, 0.0)
            if market_validity < 0.5:
                self.hierarchy.set_decision(
                    HierarchyLevel.CONTROL,
                    DecisionType.MARKET_INVALID,
                    f"Market validity too low: {market_validity:.2%}"
                )
                return False
        
            # Check uncertainty
            uncertainty = current_values.get(ConstraintType.MAX_UNCERTAINTY, 1.0)
            if uncertainty > 0.8:
                self.hierarchy.set_decision(
                    HierarchyLevel.CONTROL,
                    DecisionType.UNCERTAINTY_EXCEEDED,
                    f"Uncertainty too high: {uncertainty:.2%}"
                )
                return False
        
            return True
        except Exception as e:
            logger.error(f"Error in _check_control_layer: {e}")
            raise
    
    def _calculate_max_exposure(self, current_values: Dict[ConstraintType, float]) -> float:
        """Calculate maximum allowed exposure based on current conditions"""
        try:
            base_exposure = 1.0
        
            # Reduce for uncertainty
            uncertainty = current_values.get(ConstraintType.MAX_UNCERTAINTY, 0.5)
            uncertainty_factor = max(0, 1 - uncertainty)
        
            # Reduce for volatility
            volatility = current_values.get(ConstraintType.MAX_VOLATILITY, 0.02)
            volatility_factor = max(0, 1 - (volatility / 0.10))  # Normalize to 10%
        
            # Reduce for drawdown
            drawdown = current_values.get(ConstraintType.MAX_DRAWDOWN, 0.0)
            drawdown_factor = max(0, 1 - (drawdown / 0.20))  # Normalize to 20%
        
            # Combine factors
            exposure = base_exposure * uncertainty_factor * volatility_factor * drawdown_factor
        
            # Apply position size limit
            max_position = self.constraints.get_constraint(ConstraintType.MAX_POSITION_SIZE)
            if max_position:
                exposure = min(exposure, max_position.value)
        
            return max(0, exposure)
        except Exception as e:
            logger.error(f"Error in _calculate_max_exposure: {e}")
            raise
    
    def force_flat(self, reason: str):
        """Force system to flat exposure - emergency use only"""
        try:
            self.logger.critical(f"FORCE FLAT: {reason}")
            self.state.exposure_multiplier = 0.0
            self.hierarchy.set_decision(
                HierarchyLevel.CONSTRAINTS,
                DecisionType.EXPOSURE_ZERO,
                f"FORCE FLAT: {reason}"
            )
        except Exception as e:
            logger.error(f"Error in force_flat: {e}")
            raise
    
    def freeze_learning(self, reason: str):
        """Freeze all learning - used during stress"""
        try:
            self.logger.warning(f"LEARNING FROZEN: {reason}")
            self.state.learning_frozen = True
        except Exception as e:
            logger.error(f"Error in freeze_learning: {e}")
            raise
    
    def unfreeze_learning(self):
        """Unfreeze learning - only when conditions stabilize"""
        try:
            if self.state.uncertainty_level < 0.5 and self.state.current_drawdown < 0.05:
                self.state.learning_frozen = False
                self.logger.info("Learning unfrozen - conditions stabilized")
            else:
                self.logger.warning("Cannot unfreeze learning - conditions not stable")
        except Exception as e:
            logger.error(f"Error in unfreeze_learning: {e}")
            raise


def create_msos(config: Optional[MSOSConfig] = None) -> MSOSCore:
    """Factory function to create MSOS core"""
    return MSOSCore(config)


async def quick_start(config: Optional[Dict[str, Any]] = None) -> MSOSCore:
    """Quick start function for MSOS"""
    try:
        msos_config = MSOSConfig(**(config or {}))
        return create_msos(msos_config)
    except Exception as e:
        logger.error(f"Error in quick_start: {e}")
        raise
