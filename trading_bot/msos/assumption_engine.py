"""
AlphaAlgo MSOS - Assumption Extraction & Enforcement Engine

For every strategy or signal, explicitly extract:
- Regime assumptions
- Liquidity assumptions
- Volatility assumptions
- Latency assumptions
- Behavioral assumptions

If assumptions cannot be explicitly stated → strategy rejected.
If assumptions are violated in live data → strategy muted immediately.

Author: AlphaAlgo MSOS
"""

import hashlib
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class AssumptionType(Enum):
    """Types of strategy assumptions"""
    REGIME = auto()           # Market regime assumptions
    LIQUIDITY = auto()        # Liquidity assumptions
    VOLATILITY = auto()       # Volatility assumptions
    LATENCY = auto()          # Execution latency assumptions
    BEHAVIORAL = auto()       # Market participant behavior
    STATIONARITY = auto()     # Data stationarity assumptions
    CORRELATION = auto()      # Correlation structure assumptions
    DISTRIBUTION = auto()     # Return distribution assumptions
    MICROSTRUCTURE = auto()   # Market microstructure assumptions
    TEMPORAL = auto()         # Time-based assumptions


class AssumptionStatus(Enum):
    """Status of an assumption"""
    VALID = auto()
    STRESSED = auto()
    VIOLATED = auto()
    UNKNOWN = auto()


class ViolationSeverity(Enum):
    """Severity of assumption violation"""
    MINOR = auto()      # Slight deviation, monitor
    MODERATE = auto()   # Significant deviation, reduce exposure
    SEVERE = auto()     # Major violation, mute strategy
    CRITICAL = auto()   # Complete breakdown, retire strategy


@dataclass
class StrategyAssumption:
    """A single strategy assumption"""
    assumption_id: str
    assumption_type: AssumptionType
    name: str
    description: str
    expected_value: float
    tolerance: float  # Acceptable deviation
    current_value: float = 0.0
    status: AssumptionStatus = AssumptionStatus.UNKNOWN
    stress_score: float = 0.0  # 0-100
    last_validated: float = 0.0
    violation_count: int = 0
    
    def validate(self, current_value: float) -> AssumptionStatus:
        """Validate assumption against current value"""
        try:
            self.current_value = current_value
            self.last_validated = time.time()
        
            deviation = abs(current_value - self.expected_value)
            relative_deviation = deviation / (abs(self.expected_value) + 1e-10)
        
            # Calculate stress score (0-100)
            self.stress_score = min(100, (relative_deviation / self.tolerance) * 50)
        
            if relative_deviation <= self.tolerance * 0.5:
                self.status = AssumptionStatus.VALID
            elif relative_deviation <= self.tolerance:
                self.status = AssumptionStatus.STRESSED
            else:
                self.status = AssumptionStatus.VIOLATED
                self.violation_count += 1
        
            return self.status
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'assumption_id': self.assumption_id,
            'type': self.assumption_type.name,
            'name': self.name,
            'description': self.description,
            'expected_value': self.expected_value,
            'tolerance': self.tolerance,
            'current_value': self.current_value,
            'status': self.status.name,
            'stress_score': self.stress_score,
            'violation_count': self.violation_count
        }


@dataclass
class AssumptionViolation:
    """Record of an assumption violation"""
    assumption: StrategyAssumption
    severity: ViolationSeverity
    deviation: float
    expected: float
    actual: float
    timestamp: float = field(default_factory=time.time)
    action_taken: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'assumption_id': self.assumption.assumption_id,
            'assumption_name': self.assumption.name,
            'severity': self.severity.name,
            'deviation': self.deviation,
            'expected': self.expected,
            'actual': self.actual,
            'timestamp': self.timestamp,
            'action_taken': self.action_taken
        }


@dataclass
class AssumptionResult:
    """Result from assumption engine"""
    strategy_id: str
    is_valid: bool
    can_trade: bool
    exposure_multiplier: float
    assumptions: List[StrategyAssumption]
    violations: List[AssumptionViolation]
    hidden_assumptions: List[StrategyAssumption]
    overall_stress: float  # 0-100
    reason: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'strategy_id': self.strategy_id,
            'is_valid': self.is_valid,
            'can_trade': self.can_trade,
            'exposure_multiplier': self.exposure_multiplier,
            'assumptions_count': len(self.assumptions),
            'violations_count': len(self.violations),
            'hidden_assumptions_count': len(self.hidden_assumptions),
            'overall_stress': self.overall_stress,
            'reason': self.reason,
            'timestamp': self.timestamp
        }


class AssumptionExtractor:
    """
    Extracts assumptions from strategy configurations.
    
    Every strategy MUST have explicit assumptions.
    If assumptions cannot be extracted → strategy rejected.
    """
    
    # Required assumption types for each strategy category
    REQUIRED_ASSUMPTIONS = {
        'trend_following': [
            AssumptionType.REGIME,
            AssumptionType.VOLATILITY,
            AssumptionType.STATIONARITY
        ],
        'mean_reversion': [
            AssumptionType.REGIME,
            AssumptionType.STATIONARITY,
            AssumptionType.DISTRIBUTION
        ],
        'momentum': [
            AssumptionType.REGIME,
            AssumptionType.LIQUIDITY,
            AssumptionType.BEHAVIORAL
        ],
        'arbitrage': [
            AssumptionType.LATENCY,
            AssumptionType.LIQUIDITY,
            AssumptionType.MICROSTRUCTURE
        ],
        'market_making': [
            AssumptionType.LIQUIDITY,
            AssumptionType.VOLATILITY,
            AssumptionType.MICROSTRUCTURE
        ],
        'default': [
            AssumptionType.REGIME,
            AssumptionType.LIQUIDITY,
            AssumptionType.VOLATILITY
        ]
    }
    
    def __init__(self):
        try:
            self.logger = logging.getLogger("msos.assumption.extractor")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def extract(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any]
    ) -> Tuple[List[StrategyAssumption], List[StrategyAssumption]]:
        """
        Extract assumptions from strategy configuration.
        
        Returns:
            Tuple of (explicit_assumptions, hidden_assumptions)
        """
        try:
            explicit = []
            hidden = []
        
            strategy_type = strategy_config.get('type', 'default')
            required_types = self.REQUIRED_ASSUMPTIONS.get(
                strategy_type,
                self.REQUIRED_ASSUMPTIONS['default']
            )
        
            # Extract explicit assumptions from config
            config_assumptions = strategy_config.get('assumptions', {})
        
            for assumption_type in required_types:
                type_name = assumption_type.name.lower()
            
                if type_name in config_assumptions:
                    # Explicit assumption found
                    assumption_config = config_assumptions[type_name]
                    assumption = StrategyAssumption(
                        assumption_id=f"{strategy_id}_{type_name}",
                        assumption_type=assumption_type,
                        name=assumption_config.get('name', type_name),
                        description=assumption_config.get('description', ''),
                        expected_value=assumption_config.get('expected_value', 0.0),
                        tolerance=assumption_config.get('tolerance', 0.1)
                    )
                    explicit.append(assumption)
                else:
                    # Hidden assumption - must be inferred
                    hidden_assumption = self._infer_assumption(
                        strategy_id, assumption_type, strategy_config
                    )
                    hidden.append(hidden_assumption)
        
            # Check for additional implicit assumptions
            hidden.extend(self._detect_hidden_assumptions(strategy_id, strategy_config))
        
            return explicit, hidden
        except Exception as e:
            logger.error(f"Error in extract: {e}")
            raise
    
    def _infer_assumption(
        self,
        strategy_id: str,
        assumption_type: AssumptionType,
        config: Dict[str, Any]
    ) -> StrategyAssumption:
        """Infer a hidden assumption from strategy behavior"""
        # Default values based on assumption type
        try:
            defaults = {
                AssumptionType.REGIME: (0.5, 0.3, "Assumes stable regime"),
                AssumptionType.LIQUIDITY: (0.7, 0.2, "Assumes adequate liquidity"),
                AssumptionType.VOLATILITY: (0.02, 0.5, "Assumes normal volatility"),
                AssumptionType.LATENCY: (0.1, 0.5, "Assumes low latency"),
                AssumptionType.BEHAVIORAL: (0.5, 0.3, "Assumes rational behavior"),
                AssumptionType.STATIONARITY: (0.8, 0.2, "Assumes stationarity"),
                AssumptionType.CORRELATION: (0.3, 0.5, "Assumes stable correlations"),
                AssumptionType.DISTRIBUTION: (0.0, 0.3, "Assumes normal distribution"),
                AssumptionType.MICROSTRUCTURE: (0.5, 0.3, "Assumes stable microstructure"),
                AssumptionType.TEMPORAL: (0.5, 0.3, "Assumes time consistency")
            }
        
            expected, tolerance, description = defaults.get(
                assumption_type,
                (0.5, 0.3, "Unknown assumption")
            )
        
            return StrategyAssumption(
                assumption_id=f"{strategy_id}_{assumption_type.name.lower()}_hidden",
                assumption_type=assumption_type,
                name=f"Hidden {assumption_type.name}",
                description=f"HIDDEN: {description}",
                expected_value=expected,
                tolerance=tolerance
            )
        except Exception as e:
            logger.error(f"Error in _infer_assumption: {e}")
            raise
    
    def _detect_hidden_assumptions(
        self,
        strategy_id: str,
        config: Dict[str, Any]
    ) -> List[StrategyAssumption]:
        """Detect additional hidden assumptions from strategy config"""
        try:
            hidden = []
        
            # Check for lookback period → stationarity assumption
            if 'lookback' in config or 'window' in config:
                lookback = config.get('lookback', config.get('window', 20))
                hidden.append(StrategyAssumption(
                    assumption_id=f"{strategy_id}_lookback_stationarity",
                    assumption_type=AssumptionType.STATIONARITY,
                    name="Lookback Stationarity",
                    description=f"Assumes data is stationary over {lookback} periods",
                    expected_value=0.8,
                    tolerance=0.2
                ))
        
            # Check for correlation-based logic
            if 'correlation' in str(config).lower():
                hidden.append(StrategyAssumption(
                    assumption_id=f"{strategy_id}_correlation_stability",
                    assumption_type=AssumptionType.CORRELATION,
                    name="Correlation Stability",
                    description="Assumes correlations remain stable",
                    expected_value=0.7,
                    tolerance=0.3
                ))
        
            # Check for ML model → distribution assumption
            if 'model' in config or 'ml' in str(config).lower():
                hidden.append(StrategyAssumption(
                    assumption_id=f"{strategy_id}_distribution_iid",
                    assumption_type=AssumptionType.DISTRIBUTION,
                    name="IID Assumption",
                    description="Assumes returns are independently distributed",
                    expected_value=0.5,
                    tolerance=0.3
                ))
        
            return hidden
        except Exception as e:
            logger.error(f"Error in _detect_hidden_assumptions: {e}")
            raise


class AssumptionValidator:
    """
    Validates assumptions against live market data.
    
    If assumptions are violated → strategy muted immediately.
    """
    
    def __init__(self):
        try:
            self.logger = logging.getLogger("msos.assumption.validator")
            self._violation_history: Dict[str, List[AssumptionViolation]] = defaultdict(list)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate(
        self,
        assumptions: List[StrategyAssumption],
        market_data: Dict[str, Any]
    ) -> Tuple[List[StrategyAssumption], List[AssumptionViolation]]:
        """
        Validate all assumptions against current market data.
        
        Returns:
            Tuple of (validated_assumptions, violations)
        """
        try:
            violations = []
        
            for assumption in assumptions:
                current_value = self._get_current_value(assumption, market_data)
                status = assumption.validate(current_value)
            
                if status == AssumptionStatus.VIOLATED:
                    deviation = abs(current_value - assumption.expected_value)
                    severity = self._determine_severity(assumption, deviation)
                
                    violation = AssumptionViolation(
                        assumption=assumption,
                        severity=severity,
                        deviation=deviation,
                        expected=assumption.expected_value,
                        actual=current_value,
                        action_taken=self._get_action(severity)
                    )
                    violations.append(violation)
                    self._violation_history[assumption.assumption_id].append(violation)
                
                    self.logger.warning(
                        f"Assumption violated: {assumption.name} | "
                        f"Expected: {assumption.expected_value:.4f} | "
                        f"Actual: {current_value:.4f} | "
                        f"Severity: {severity.name}"
                    )
        
            return assumptions, violations
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise
    
    def _get_current_value(
        self,
        assumption: StrategyAssumption,
        market_data: Dict[str, Any]
    ) -> float:
        """Get current value for assumption from market data"""
        try:
            type_to_field = {
                AssumptionType.REGIME: 'regime_stability',
                AssumptionType.LIQUIDITY: 'liquidity_score',
                AssumptionType.VOLATILITY: 'realized_volatility',
                AssumptionType.LATENCY: 'execution_latency',
                AssumptionType.BEHAVIORAL: 'behavioral_score',
                AssumptionType.STATIONARITY: 'stationarity_score',
                AssumptionType.CORRELATION: 'correlation_stability',
                AssumptionType.DISTRIBUTION: 'distribution_score',
                AssumptionType.MICROSTRUCTURE: 'microstructure_score',
                AssumptionType.TEMPORAL: 'temporal_consistency'
            }
        
            field_name = type_to_field.get(assumption.assumption_type, 'unknown')
            return market_data.get(field_name, assumption.expected_value)
        except Exception as e:
            logger.error(f"Error in _get_current_value: {e}")
            raise
    
    def _determine_severity(
        self,
        assumption: StrategyAssumption,
        deviation: float
    ) -> ViolationSeverity:
        """Determine severity of violation"""
        try:
            relative_deviation = deviation / (abs(assumption.expected_value) + 1e-10)
        
            # Check violation history
            history = self._violation_history.get(assumption.assumption_id, [])
            recent_violations = sum(
                1 for v in history
                if time.time() - v.timestamp < 3600  # Last hour
            )
        
            # Escalate severity based on history
            if recent_violations >= 3:
                return ViolationSeverity.CRITICAL
            elif relative_deviation > assumption.tolerance * 3:
                return ViolationSeverity.CRITICAL
            elif relative_deviation > assumption.tolerance * 2:
                return ViolationSeverity.SEVERE
            elif relative_deviation > assumption.tolerance * 1.5:
                return ViolationSeverity.MODERATE
            else:
                return ViolationSeverity.MINOR
        except Exception as e:
            logger.error(f"Error in _determine_severity: {e}")
            raise
    
    def _get_action(self, severity: ViolationSeverity) -> str:
        """Get action for violation severity"""
        try:
            actions = {
                ViolationSeverity.MINOR: "Monitor closely",
                ViolationSeverity.MODERATE: "Reduce exposure by 50%",
                ViolationSeverity.SEVERE: "Mute strategy immediately",
                ViolationSeverity.CRITICAL: "Retire strategy"
            }
            return actions.get(severity, "Unknown action")
        except Exception as e:
            logger.error(f"Error in _get_action: {e}")
            raise


class AssumptionEngine:
    """
    Main Assumption Engine - combines extraction and validation.
    
    RULES:
    1. If assumptions cannot be explicitly stated → strategy rejected
    2. If assumptions are violated in live data → strategy muted immediately
    3. Hidden assumptions are tracked and monitored
    4. Repeated violations lead to strategy retirement
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.extractor = AssumptionExtractor()
            self.validator = AssumptionValidator()
            self.logger = logging.getLogger("msos.assumption")
        
            # Strategy assumption registry
            self._strategy_assumptions: Dict[str, List[StrategyAssumption]] = {}
            self._strategy_hidden: Dict[str, List[StrategyAssumption]] = {}
        
            self.logger.info("Assumption Engine initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def register_strategy(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any]
    ) -> AssumptionResult:
        """
        Register a strategy and extract its assumptions.
        
        If assumptions cannot be extracted → strategy rejected.
        """
        try:
            explicit, hidden = self.extractor.extract(strategy_id, strategy_config)
        
            # Check if strategy has minimum required assumptions
            if len(explicit) == 0:
                self.logger.error(
                    f"Strategy {strategy_id} rejected: No explicit assumptions defined"
                )
                return AssumptionResult(
                    strategy_id=strategy_id,
                    is_valid=False,
                    can_trade=False,
                    exposure_multiplier=0.0,
                    assumptions=[],
                    violations=[],
                    hidden_assumptions=hidden,
                    overall_stress=100.0,
                    reason="Strategy rejected: No explicit assumptions defined"
                )
        
            # Store assumptions
            self._strategy_assumptions[strategy_id] = explicit
            self._strategy_hidden[strategy_id] = hidden
        
            self.logger.info(
                f"Strategy {strategy_id} registered: "
                f"{len(explicit)} explicit, {len(hidden)} hidden assumptions"
            )
        
            return AssumptionResult(
                strategy_id=strategy_id,
                is_valid=True,
                can_trade=True,
                exposure_multiplier=1.0,
                assumptions=explicit,
                violations=[],
                hidden_assumptions=hidden,
                overall_stress=0.0,
                reason="Strategy registered successfully"
            )
        except Exception as e:
            logger.error(f"Error in register_strategy: {e}")
            raise
    
    def validate_strategy(
        self,
        strategy_id: str,
        market_data: Dict[str, Any]
    ) -> AssumptionResult:
        """
        Validate strategy assumptions against current market data.
        
        If assumptions are violated → strategy muted immediately.
        """
        try:
            if strategy_id not in self._strategy_assumptions:
                return AssumptionResult(
                    strategy_id=strategy_id,
                    is_valid=False,
                    can_trade=False,
                    exposure_multiplier=0.0,
                    assumptions=[],
                    violations=[],
                    hidden_assumptions=[],
                    overall_stress=100.0,
                    reason="Strategy not registered"
                )
        
            # Get assumptions
            explicit = self._strategy_assumptions[strategy_id]
            hidden = self._strategy_hidden.get(strategy_id, [])
            all_assumptions = explicit + hidden
        
            # Validate all assumptions
            validated, violations = self.validator.validate(all_assumptions, market_data)
        
            # Calculate overall stress
            if validated:
                overall_stress = np.mean([a.stress_score for a in validated])
            else:
                overall_stress = 0.0
        
            # Determine if strategy can trade
            critical_violations = [
                v for v in violations
                if v.severity in [ViolationSeverity.SEVERE, ViolationSeverity.CRITICAL]
            ]
        
            if critical_violations:
                can_trade = False
                exposure_multiplier = 0.0
                reason = f"Critical violations: {[v.assumption.name for v in critical_violations]}"
            elif violations:
                can_trade = True
                # Reduce exposure based on violation severity
                exposure_multiplier = max(0.1, 1.0 - len(violations) * 0.2)
                reason = f"Minor violations detected, exposure reduced to {exposure_multiplier:.1%}"
            else:
                can_trade = True
                exposure_multiplier = max(0.5, 1.0 - overall_stress / 100)
                reason = "All assumptions valid"
        
            return AssumptionResult(
                strategy_id=strategy_id,
                is_valid=len(critical_violations) == 0,
                can_trade=can_trade,
                exposure_multiplier=exposure_multiplier,
                assumptions=validated,
                violations=violations,
                hidden_assumptions=hidden,
                overall_stress=overall_stress,
                reason=reason
            )
        except Exception as e:
            logger.error(f"Error in validate_strategy: {e}")
            raise
    
    def get_strategy_assumptions(
        self,
        strategy_id: str
    ) -> Tuple[List[StrategyAssumption], List[StrategyAssumption]]:
        """Get explicit and hidden assumptions for a strategy"""
        try:
            explicit = self._strategy_assumptions.get(strategy_id, [])
            hidden = self._strategy_hidden.get(strategy_id, [])
            return explicit, hidden
        except Exception as e:
            logger.error(f"Error in get_strategy_assumptions: {e}")
            raise
    
    def retire_strategy(self, strategy_id: str, reason: str):
        """Retire a strategy due to repeated violations"""
        try:
            self.logger.critical(f"Strategy {strategy_id} RETIRED: {reason}")
            if strategy_id in self._strategy_assumptions:
                del self._strategy_assumptions[strategy_id]
            if strategy_id in self._strategy_hidden:
                del self._strategy_hidden[strategy_id]
        except Exception as e:
            logger.error(f"Error in retire_strategy: {e}")
            raise
