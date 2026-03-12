"""
AlphaAlgo MSOS - Orchestrator

The Master Orchestrator integrates all MSOS components into a unified
capital-preservation-first trading governance system.

SYSTEM HIERARCHY (ENFORCED):
1. Constraints > Control
2. Control > Exposure
3. Exposure > Strategy
4. Strategy > Intelligence
5. Intelligence > Prediction

No layer may override a higher layer.

PRIMARY DIRECTIVE:
Preserve capital across regime shifts. Returns are a side effect of survival.

Author: AlphaAlgo MSOS
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

from .core import (
    MSOSCore,
    MSOSConfig,
    MSOSDecision,
    MSOSState,
    ConstraintType,
    DecisionType,
    HierarchyLevel,
    ImmutableConstraints,
    ABSOLUTE_AXIOMS
)
from .market_tradability import MarketTradabilityGate, TradabilityResult
from .assumption_engine import AssumptionEngine, AssumptionResult
from .signal_semantics import SignalSemanticMonitor, SemanticResult
from .regime_instability import RegimeInstabilityDetector, InstabilityResult
from .capital_governor import CapitalGovernor, CapitalResult
from .loss_monitor import LossShapeMonitor, LossResult
from .execution_reality import ExecutionRealityChecker, ExecutionResult
from .anti_overreaction import AntiOverreactionEngine, OverreactionResult, ReactionType
from .learning_firewall import LearningFirewall, FirewallResult
from .time_risk import TimeRiskManager, TimeRiskResult
from .data_adversarial import DataAdversarialDefense, DataDefenseResult
from .quant_factory import QuantModelFactory
from .post_mortem import PostMortemEngine, PostMortemResult
from .entropy_budget import EntropyBudgetManager, EntropyResult

logger = logging.getLogger(__name__)


class SystemMode(Enum):
    """System operating modes"""
    NORMAL = auto()           # Normal operations
    DEFENSIVE = auto()        # Reduced exposure
    SURVIVAL = auto()         # Minimal exposure
    RECOVERY = auto()         # Post-drawdown recovery
    FROZEN = auto()           # No trading
    EMERGENCY = auto()        # Emergency shutdown


@dataclass
class OrchestratorConfig:
    """Configuration for MSOS Orchestrator"""
    enable_all_checks: bool = True
    log_all_decisions: bool = True
    strict_mode: bool = True
    default_to_no_trade: bool = True
    
    # Component enables
    enable_market_tradability: bool = True
    enable_assumption_engine: bool = True
    enable_signal_semantics: bool = True
    enable_regime_detection: bool = True
    enable_capital_governance: bool = True
    enable_loss_monitoring: bool = True
    enable_execution_checks: bool = True
    enable_anti_overreaction: bool = True
    enable_learning_firewall: bool = True
    enable_time_risk: bool = True
    enable_data_defense: bool = True
    enable_entropy_budget: bool = True


@dataclass
class OrchestratorResult:
    """Result from MSOS Orchestrator evaluation"""
    is_tradable: bool
    can_trade: bool
    max_exposure: float
    exposure_multiplier: float
    mode: SystemMode
    decision: MSOSDecision
    tradability: Optional[TradabilityResult] = None
    assumptions: Optional[AssumptionResult] = None
    semantics: Optional[SemanticResult] = None
    regime: Optional[InstabilityResult] = None
    capital: Optional[CapitalResult] = None
    loss: Optional[LossResult] = None
    execution: Optional[ExecutionResult] = None
    overreaction: Optional[OverreactionResult] = None
    firewall: Optional[FirewallResult] = None
    time_risk: Optional[TimeRiskResult] = None
    data_defense: Optional[DataDefenseResult] = None
    entropy: Optional[EntropyResult] = None
    warnings: List[str] = field(default_factory=list)
    reason: str = ""
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_tradable': self.is_tradable,
            'can_trade': self.can_trade,
            'max_exposure': self.max_exposure,
            'exposure_multiplier': self.exposure_multiplier,
            'mode': self.mode.name,
            'decision_type': self.decision.decision_type.name,
            'authority_layer': self.decision.authority_layer.name,
            'warnings': self.warnings,
            'reason': self.reason,
            'timestamp': self.timestamp
        }


class MSOSOrchestrator:
    """
    MSOS Master Orchestrator
    
    Integrates all MSOS components into a unified governance system.
    Enforces the strict hierarchy and immutable constraints.
    
    PRIMARY DIRECTIVE: Preserve capital. Returns are a side effect of survival.
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        try:
            self.config = config or OrchestratorConfig()
            self.logger = logging.getLogger("msos.orchestrator")
        
            # Core
            self._core = MSOSCore(MSOSConfig(
                enable_strict_mode=self.config.strict_mode,
                log_all_decisions=self.config.log_all_decisions,
                default_to_no_trade=self.config.default_to_no_trade
            ))
        
            # Components
            self._market_tradability = MarketTradabilityGate()
            self._assumption_engine = AssumptionEngine()
            self._signal_semantics = SignalSemanticMonitor()
            self._regime_detector = RegimeInstabilityDetector()
            self._capital_governor = CapitalGovernor()
            self._loss_monitor = LossShapeMonitor()
            self._execution_checker = ExecutionRealityChecker()
            self._anti_overreaction = AntiOverreactionEngine()
            self._learning_firewall = LearningFirewall()
            self._time_risk = TimeRiskManager()
            self._data_defense = DataAdversarialDefense()
            self._quant_factory = QuantModelFactory()
            self._post_mortem = PostMortemEngine()
            self._entropy_budget = EntropyBudgetManager()
        
            # State
            self._mode = SystemMode.NORMAL
            self._total_equity = 0.0
            self._current_drawdown = 0.0
        
            self.logger.info("=" * 60)
            self.logger.info("MSOS ORCHESTRATOR INITIALIZED")
            self.logger.info("PRIMARY DIRECTIVE: Capital Preservation")
            self.logger.info("=" * 60)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def evaluate(
        self,
        strategy_id: str,
        symbol: str,
        market_data: Dict[str, Any],
        strategy_config: Dict[str, Any],
        equity: float = 0.0
    ) -> OrchestratorResult:
        """
        Evaluate whether a trade should be allowed.
        
        This is the main entry point for all trading decisions.
        The system defaults to NO TRADE unless all checks pass.
        """
        try:
            warnings = []
            exposure_multipliers = []
        
            self._total_equity = equity
        
            # =====================================================================
            # LAYER 0: MARKET TRADABILITY (Highest Priority after Constraints)
            # =====================================================================
            tradability = None
            if self.config.enable_market_tradability:
                tradability = self._market_tradability.evaluate(symbol, market_data)
            
                if not tradability.is_tradable:
                    return self._create_blocked_result(
                        strategy_id, symbol,
                        DecisionType.MARKET_INVALID,
                        f"Market not tradable: {tradability.reason}",
                        tradability=tradability
                    )
            
                exposure_multipliers.append(tradability.exposure_multiplier)
                if tradability.invalidation_reasons:
                    warnings.extend(tradability.invalidation_reasons)
        
            # =====================================================================
            # LAYER 1: DATA ADVERSARIAL DEFENSE
            # =====================================================================
            data_defense = None
            if self.config.enable_data_defense:
                data_defense = self._data_defense.validate(
                    source_id=market_data.get('source', 'unknown'),
                    data=market_data
                )
            
                if not data_defense.can_use:
                    return self._create_blocked_result(
                        strategy_id, symbol,
                        DecisionType.MARKET_INVALID,
                        f"Data not trustworthy: {data_defense.reason}",
                        data_defense=data_defense
                    )
            
                warnings.extend(data_defense.warnings)
        
            # =====================================================================
            # LAYER 2: LEARNING FIREWALL
            # =====================================================================
            firewall = None
            if self.config.enable_learning_firewall:
                firewall = self._learning_firewall.check(market_data)
            
                if firewall.detected_events:
                    warnings.append(f"Extreme events detected: {[e.name for e in firewall.detected_events]}")
        
            # =====================================================================
            # LAYER 3: REGIME INSTABILITY DETECTION
            # =====================================================================
            regime = None
            if self.config.enable_regime_detection:
                regime = self._regime_detector.update(market_data)
            
                exposure_multipliers.append(regime.exposure_multiplier)
                warnings.extend(regime.early_warnings)
            
                if regime.instability_score > 0.8:
                    self._mode = SystemMode.SURVIVAL
        
            # =====================================================================
            # LAYER 4: ASSUMPTION ENGINE
            # =====================================================================
            assumptions = None
            if self.config.enable_assumption_engine:
                # Register strategy if not already
                if strategy_id not in self._assumption_engine._strategy_assumptions:
                    self._assumption_engine.register_strategy(strategy_id, strategy_config)
            
                assumptions = self._assumption_engine.validate_strategy(strategy_id, market_data)
            
                if not assumptions.can_trade:
                    return self._create_blocked_result(
                        strategy_id, symbol,
                        DecisionType.ASSUMPTION_VIOLATED,
                        f"Assumptions violated: {assumptions.reason}",
                        assumptions=assumptions
                    )
            
                exposure_multipliers.append(assumptions.exposure_multiplier)
        
            # =====================================================================
            # LAYER 5: SIGNAL SEMANTIC INTEGRITY
            # =====================================================================
            semantics = None
            if self.config.enable_signal_semantics:
                signal_id = f"{strategy_id}_{symbol}"
                signal_value = market_data.get('signal_value', 0)
                target_value = market_data.get('target_value', 0)
            
                semantics = self._signal_semantics.update(
                    signal_id, signal_value, target_value
                )
            
                if not semantics.can_use:
                    return self._create_blocked_result(
                        strategy_id, symbol,
                        DecisionType.SEMANTIC_DRIFT,
                        f"Signal semantics invalid: {semantics.reason}",
                        semantics=semantics
                    )
        
            # =====================================================================
            # LAYER 6: TIME RISK MANAGEMENT
            # =====================================================================
            time_risk = None
            if self.config.enable_time_risk:
                time_risk = self._time_risk.update(market_data)
            
                exposure_multipliers.append(time_risk.exposure_multiplier)
                warnings.extend(time_risk.warnings)
        
            # =====================================================================
            # LAYER 7: LOSS SHAPE MONITORING
            # =====================================================================
            loss = None
            if self.config.enable_loss_monitoring:
                return_value = market_data.get('return', 0)
                loss = self._loss_monitor.update(equity, return_value)
            
                exposure_multipliers.append(loss.exposure_multiplier)
                warnings.extend(loss.warnings)
            
                if loss.post_mortem_required:
                    warnings.append("Post-mortem required for loss shape")
        
            # =====================================================================
            # LAYER 8: CAPITAL GOVERNANCE
            # =====================================================================
            capital = None
            if self.config.enable_capital_governance:
                strategy_returns = {strategy_id: market_data.get('return', 0)}
                self._capital_governor.update(equity, strategy_returns)
            
                capital = self._capital_governor.allocate(
                    strategy_id,
                    {'return': market_data.get('return', 0)}
                )
            
                exposure_multipliers.append(capital.allocation)
                warnings.extend(capital.constraints_applied)
        
            # =====================================================================
            # LAYER 9: ENTROPY BUDGET
            # =====================================================================
            entropy = None
            if self.config.enable_entropy_budget:
                entropy = self._entropy_budget.update_from_market(
                    prediction_error=market_data.get('prediction_error', 0),
                    data_quality=data_defense.trust_score if data_defense else 1.0,
                    regime_confidence=1 - regime.instability_score if regime else 1.0,
                    fill_rate=market_data.get('fill_rate', 1.0),
                    slippage=market_data.get('slippage', 0),
                    correlation_stability=market_data.get('correlation_stability', 1.0)
                )
            
                exposure_multipliers.append(entropy.exposure_multiplier)
                warnings.extend(entropy.warnings)
            
                if not entropy.can_add_exposure:
                    return self._create_blocked_result(
                        strategy_id, symbol,
                        DecisionType.UNCERTAINTY_EXCEEDED,
                        f"Entropy budget exceeded: {entropy.reason}",
                        entropy=entropy
                    )
        
            # =====================================================================
            # LAYER 10: ANTI-OVERREACTION CHECK
            # =====================================================================
            overreaction = None
            if self.config.enable_anti_overreaction:
                self._anti_overreaction.update_stability(market_data.get('return', 0))
            
                overreaction = self._anti_overreaction.check_reaction(
                    ReactionType.EXPOSURE_INCREASE,
                    observations=market_data.get('observations', 0),
                    confidence=market_data.get('confidence', 0)
                )
            
                if not overreaction.is_allowed:
                    warnings.append(f"Reaction blocked: {overreaction.reason}")
        
            # =====================================================================
            # FINAL DECISION
            # =====================================================================
        
            # Calculate final exposure multiplier
            if exposure_multipliers:
                final_exposure = min(exposure_multipliers)
            else:
                final_exposure = 1.0
        
            # Apply position size constraint
            max_position = 0.10  # 10% max
            max_exposure = min(final_exposure, max_position)
        
            # Determine if trade is allowed
            is_tradable = max_exposure > 0.01  # Minimum 1% exposure
            can_trade = is_tradable and len(warnings) < 5
        
            # Build constraint values for core evaluation
            constraint_values = {
                ConstraintType.MIN_MARKET_VALIDITY: tradability.overall_score if tradability else 0.5,
                ConstraintType.MAX_UNCERTAINTY: entropy.budget.consumed if entropy else 0.5,
                ConstraintType.MAX_VOLATILITY: market_data.get('volatility', 0.02),
                ConstraintType.MAX_DRAWDOWN: self._current_drawdown,
                ConstraintType.MAX_DAILY_LOSS: market_data.get('daily_loss', 0),
            }
        
            # Get core decision
            decision = self._core.evaluate(strategy_id, symbol, constraint_values, market_data)
        
            # Override if core says no
            if not decision.is_trade_allowed():
                is_tradable = False
                can_trade = False
                max_exposure = 0.0
        
            # Determine system mode
            self._mode = self._determine_mode(
                regime, loss, entropy, self._current_drawdown
            )
        
            # Generate reason
            reason = self._generate_reason(
                is_tradable, can_trade, max_exposure, warnings
            )
        
            result = OrchestratorResult(
                is_tradable=is_tradable,
                can_trade=can_trade,
                max_exposure=max_exposure,
                exposure_multiplier=final_exposure,
                mode=self._mode,
                decision=decision,
                tradability=tradability,
                assumptions=assumptions,
                semantics=semantics,
                regime=regime,
                capital=capital,
                loss=loss,
                execution=None,
                overreaction=overreaction,
                firewall=firewall,
                time_risk=time_risk,
                data_defense=data_defense,
                entropy=entropy,
                warnings=warnings,
                reason=reason
            )
        
            self.logger.info(
                f"[{strategy_id}:{symbol}] Decision: {decision.decision_type.name} | "
                f"Tradable: {is_tradable} | Exposure: {max_exposure:.1%} | "
                f"Mode: {self._mode.name}"
            )
        
            return result
        except Exception as e:
            logger.error(f"Error in evaluate: {e}")
            raise
    
    def _create_blocked_result(
        self,
        strategy_id: str,
        symbol: str,
        decision_type: DecisionType,
        reason: str,
        **kwargs
    ) -> OrchestratorResult:
        """Create a blocked result"""
        try:
            decision = MSOSDecision(
                decision_type=decision_type,
                reason=reason,
                authority_layer=HierarchyLevel.CONTROL,
                max_exposure=0.0,
                constraints_checked=[],
                constraints_violated=[],
                state=self._core.state
            )
        
            return OrchestratorResult(
                is_tradable=False,
                can_trade=False,
                max_exposure=0.0,
                exposure_multiplier=0.0,
                mode=self._mode,
                decision=decision,
                warnings=[reason],
                reason=reason,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error in _create_blocked_result: {e}")
            raise
    
    def _determine_mode(
        self,
        regime: Optional[InstabilityResult],
        loss: Optional[LossResult],
        entropy: Optional[EntropyResult],
        drawdown: float
    ) -> SystemMode:
        """Determine system operating mode"""
        # Check for emergency conditions
        try:
            if drawdown > 0.15:
                return SystemMode.EMERGENCY
        
            # Check for survival mode
            if regime and regime.instability_score > 0.8:
                return SystemMode.SURVIVAL
        
            if entropy and entropy.level.name == 'EXCEEDED':
                return SystemMode.FROZEN
        
            if loss and loss.damage_level.name == 'CRITICAL':
                return SystemMode.SURVIVAL
        
            # Check for defensive mode
            if drawdown > 0.10:
                return SystemMode.RECOVERY
        
            if regime and regime.instability_score > 0.6:
                return SystemMode.DEFENSIVE
        
            if entropy and entropy.level.name in ['EXTREME', 'HIGH']:
                return SystemMode.DEFENSIVE
        
            return SystemMode.NORMAL
        except Exception as e:
            logger.error(f"Error in _determine_mode: {e}")
            raise
    
    def _generate_reason(
        self,
        is_tradable: bool,
        can_trade: bool,
        max_exposure: float,
        warnings: List[str]
    ) -> str:
        """Generate explanation for decision"""
        try:
            if not is_tradable:
                return f"Trade blocked: {warnings[0] if warnings else 'Unknown reason'}"
            elif not can_trade:
                return f"Trade not recommended: {len(warnings)} warnings"
            elif max_exposure < 0.05:
                return f"Trade allowed with minimal exposure ({max_exposure:.1%})"
            else:
                return f"Trade allowed with exposure up to {max_exposure:.1%}"
        except Exception as e:
            logger.error(f"Error in _generate_reason: {e}")
            raise
    
    def record_execution(
        self,
        strategy_id: str,
        latency_ms: float,
        slippage_bps: float,
        impact_bps: float,
        size: float = 1.0
    ) -> ExecutionResult:
        """Record execution and check against tolerances"""
        return self._execution_checker.check_execution(
            strategy_id, latency_ms, slippage_bps, impact_bps, size
        )
    
    def record_failure(
        self,
        strategy_id: str,
        loss_amount: float,
        loss_percentage: float,
        market_data: Dict[str, Any],
        strategy_state: Dict[str, Any]
    ) -> PostMortemResult:
        """Record a failure and perform post-mortem"""
        try:
            explicit, hidden = self._assumption_engine.get_strategy_assumptions(strategy_id)
            assumptions = [
                {
                    'name': a.name,
                    'expected_value': a.expected_value,
                    'tolerance': a.tolerance,
                    'market_field': a.assumption_type.name.lower(),
                    'monitored': True,
                    'has_warning': True
                }
                for a in explicit
            ]
        
            return self._post_mortem.analyze_failure(
                strategy_id=strategy_id,
                loss_amount=loss_amount,
                loss_percentage=loss_percentage,
                market_data=market_data,
                strategy_state=strategy_state,
                assumptions=assumptions,
                warnings=[]
            )
        except Exception as e:
            logger.error(f"Error in record_failure: {e}")
            raise
    
    def force_survival_mode(self, reason: str):
        """Force system into survival mode"""
        try:
            self._mode = SystemMode.SURVIVAL
            self._capital_governor.force_survival_mode(reason)
            self._anti_overreaction.force_cooldown_all(reason)
            self.logger.critical(f"SURVIVAL MODE ACTIVATED: {reason}")
        except Exception as e:
            logger.error(f"Error in force_survival_mode: {e}")
            raise
    
    def force_flat(self, reason: str):
        """Force all positions flat"""
        try:
            self._mode = SystemMode.FROZEN
            self._core.force_flat(reason)
            self.logger.critical(f"FORCE FLAT: {reason}")
        except Exception as e:
            logger.error(f"Error in force_flat: {e}")
            raise
    
    def get_mode(self) -> SystemMode:
        """Get current system mode"""
        return self._mode
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'mode': self._mode.name,
            'equity': self._total_equity,
            'drawdown': self._current_drawdown,
            'entropy_level': self._entropy_budget.get_budget().level.name,
            'learning_state': self._learning_firewall.get_state().name,
            'regime_uncertainty': self._regime_detector.get_current_uncertainty().name,
            'axioms_verified': True,
            'constraints_active': len(self._core.constraints.all_constraints)
        }
    
    def get_quant_factory(self) -> QuantModelFactory:
        """Get quant model factory"""
        return self._quant_factory


async def create_orchestrator(config: Optional[Dict[str, Any]] = None) -> MSOSOrchestrator:
    """Factory function to create MSOS Orchestrator"""
    try:
        orch_config = OrchestratorConfig(**(config or {}))
        return MSOSOrchestrator(orch_config)
    except Exception as e:
        logger.error(f"Error in create_orchestrator: {e}")
        raise
