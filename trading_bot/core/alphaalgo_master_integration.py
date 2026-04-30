"""
AlphaAlgo Core - Master Integration Script

Integrates ALL violation fixes into a unified system:
- Stage 0: Unified Market Hostility Gate
- Stage 1: Explicit Claim Decomposition
- Stage 2: Adversarial Failure Analysis
- Stage 3: Adversarial Committee (already in core engine)
- Stage 4: Multi-Dimensional Confidence Vectors
- Stage 5: Unified Decision Gate
- Stage 6: Confidence-Weighted Position Sizing
- Stage 7: Post-Trade Self-Fixing

This is the COMPLETE AlphaAlgo Core system with NO BYPASSES.

Author: AlphaAlgo Core
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Any
import asyncio

logger = logging.getLogger(__name__)

# Import all fixed components
from trading_bot.core.unified_market_hostility_gate import (
    get_global_hostility_gate,
    UnifiedMarketHostilityGate,
    HostilityAssessment
)
from trading_bot.core.explicit_claim_decomposition import (
    get_global_decomposer,
    ExplicitClaimDecomposer,
    DecomposedSignal
)
from trading_bot.core.adversarial_failure_analysis import (
    get_global_analyzer,
    AdversarialFailureAnalyzer,
    AdversarialAnalysis
)
from trading_bot.core.multi_dimensional_confidence_system import (
    get_global_builder,
    MultiDimensionalConfidenceBuilder,
    ConfidenceVector
)
from trading_bot.core.unified_decision_gate import (
    get_global_gate,
    UnifiedDecisionGate,
    UnifiedDecision,
)
from trading_bot.core.signal_counterintelligence import (
    AlphaAlgoIntelligenceDirectorate,
    CounterintelligenceMode,
    DirectorateRunReport,
    IntelligenceCompartment,
    IntelligenceDecision,
    IntelligenceRole,
)
from trading_bot.core.confidence_weighted_position_sizer import (
    get_global_sizer,
    ConfidenceWeightedPositionSizer,
    PositionSizingResult
)
from trading_bot.core.post_trade_self_fixing import (
    get_global_self_fixer,
    PostTradeSelfFixingSystem,
    TradeOutcome
)


@dataclass
class CompleteEvaluationResult:
    """Complete evaluation result from master integration"""
    signal_id: str
    symbol: str
    
    # Stage results
    market_hostility: HostilityAssessment
    decomposed_signal: DecomposedSignal
    adversarial_analysis: AdversarialAnalysis
    confidence_vector: ConfidenceVector
    unified_decision: UnifiedDecision
    position_sizing: Optional[PositionSizingResult]
    
    # Final verdict
    approved: bool
    final_quantity: float
    rejection_reason: str
    
    # Metadata
    timestamp: datetime
    total_evaluation_time_ms: float
    counterintelligence: Optional[DirectorateRunReport] = None


class AlphaAlgoMasterIntegration:
    """
    Master integration that coordinates ALL AlphaAlgo Core components.
    
    This is the SINGLE entry point for all trading decisions.
    NO BYPASSES POSSIBLE.
    
    Flow:
    1. Check if strategy is allowed (post-trade self-fixing)
    2. Market hostility gate
    3. Claim decomposition
    4. Adversarial failure analysis
    5. Confidence vector building
    6. Unified decision gate
    7. Position sizing (if approved)
    8. Record outcome (post-trade)
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.6,
        enable_strict_mode: bool = True,
        counterintelligence_mode: CounterintelligenceMode = CounterintelligenceMode.HARD_GATE,
        intelligence_directorate: Optional[AlphaAlgoIntelligenceDirectorate] = None,
    ):
        try:
            self.confidence_threshold = confidence_threshold
            self.enable_strict_mode = enable_strict_mode
            self.counterintelligence_mode = self._coerce_counterintelligence_mode(counterintelligence_mode)
        
            # Initialize all components
            self.hostility_gate = get_global_hostility_gate()
            self.claim_decomposer = get_global_decomposer()
            self.adversarial_analyzer = get_global_analyzer()
            self.confidence_builder = get_global_builder()
            self.decision_gate = get_global_gate()
            self.position_sizer = get_global_sizer()
            self.self_fixer = get_global_self_fixer()
            self.intelligence_directorate = intelligence_directorate or AlphaAlgoIntelligenceDirectorate(
                mode=self.counterintelligence_mode
            )
        
            # Statistics
            self.total_evaluations = 0
            self.approved_count = 0
            self.rejected_count = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def evaluate_signal(
        self,
        signal: Dict[str, Any],
        market_context: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        historical_data: Optional[Dict[str, Any]] = None
    ) -> CompleteEvaluationResult:
        """
        Complete signal evaluation through ALL stages.
        
        This is the ONLY way signals should be evaluated.
        """
        try:
            start_time = datetime.utcnow()
            self.total_evaluations += 1
        
            signal_id = signal.get('signal_id', f"sig_{datetime.utcnow().timestamp()}")
            symbol = signal['symbol']
            strategy_id = signal.get('strategy_id', 'unknown')
        
            logger.info(f"Evaluating signal {signal_id} for {symbol} (strategy: {strategy_id})")

            # STAGE -1: Signal Counterintelligence and Intelligence Directorate
            logger.debug("Stage -1: signal counterintelligence")
            kill_switch_active = bool(
                signal.get("kill_switch_active")
                or market_context.get("kill_switch_active")
                or portfolio_state.get("kill_switch_active")
            )
            directorate_report = self.intelligence_directorate.evaluate_raw_signal(
                signal,
                role=IntelligenceRole.RESEARCH_ANALYST,
                compartment=IntelligenceCompartment.RESEARCH,
                production_model_artifact=signal.get("production_model_artifact"),
                feedback_metrics=signal.get("feedback_metrics"),
                mode=self.counterintelligence_mode,
                kill_switch_active=kill_switch_active,
            )
            signal.setdefault("metadata", {})
            signal["metadata"]["intelligence"] = directorate_report.to_execution_metadata()
            signal["intelligence"] = directorate_report.to_execution_metadata()

            if (
                directorate_report.governance_decision != IntelligenceDecision.ACCEPT
                or not directorate_report.counterintelligence.execution_allowed
            ):
                decision = self.decision_gate.evaluate(
                    signal=signal,
                    market_context=market_context,
                    portfolio_state=portfolio_state,
                    counterintelligence_report=directorate_report.counterintelligence,
                )
                result = CompleteEvaluationResult(
                    signal_id=signal_id,
                    symbol=symbol,
                    market_hostility=None,
                    decomposed_signal=None,
                    adversarial_analysis=None,
                    confidence_vector=None,
                    unified_decision=decision,
                    position_sizing=None,
                    approved=False,
                    final_quantity=0.0,
                    rejection_reason=decision.rejection_reason,
                    timestamp=datetime.utcnow(),
                    total_evaluation_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                    counterintelligence=directorate_report,
                )
                self.rejected_count += 1
                return result
        
            # STAGE 0: Check if strategy is allowed (post-trade self-fixing)
            if not self.self_fixer.is_strategy_allowed(strategy_id):
                logger.warning(f"Strategy {strategy_id} is not allowed to trade (quarantined/disabled)")
            
                result = CompleteEvaluationResult(
                    signal_id=signal_id,
                    symbol=symbol,
                    market_hostility=None,
                    decomposed_signal=None,
                    adversarial_analysis=None,
                    confidence_vector=None,
                    unified_decision=None,
                    position_sizing=None,
                    approved=False,
                    final_quantity=0.0,
                    rejection_reason=f"Strategy {strategy_id} is quarantined or disabled",
                    timestamp=datetime.utcnow(),
                    total_evaluation_time_ms=0.0,
                    counterintelligence=directorate_report,
                )
            
                self.rejected_count += 1
                return result
        
            # STAGE 1: Market Hostility Gate
            logger.debug(f"Stage 1: Market hostility check")
            hostility_assessment = self.hostility_gate.assess_hostility()
        
            if not hostility_assessment.can_trade:
                logger.warning(f"Market hostile: {hostility_assessment.dominant_reason}")
            
                result = CompleteEvaluationResult(
                    signal_id=signal_id,
                    symbol=symbol,
                    market_hostility=hostility_assessment,
                    decomposed_signal=None,
                    adversarial_analysis=None,
                    confidence_vector=None,
                    unified_decision=None,
                    position_sizing=None,
                    approved=False,
                    final_quantity=0.0,
                    rejection_reason=hostility_assessment.dominant_reason,
                    timestamp=datetime.utcnow(),
                    total_evaluation_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
                )
            
                self.rejected_count += 1
                return result
        
            # STAGE 2: Claim Decomposition
            logger.debug(f"Stage 2: Claim decomposition")
            decomposed = self.claim_decomposer.decompose_signal(signal, market_context)
        
            if not decomposed.all_claims_pass:
                logger.warning(f"Failed claims: {decomposed.failed_claims}")
            
                result = CompleteEvaluationResult(
                    signal_id=signal_id,
                    symbol=symbol,
                    market_hostility=hostility_assessment,
                    decomposed_signal=decomposed,
                    adversarial_analysis=None,
                    confidence_vector=None,
                    unified_decision=None,
                    position_sizing=None,
                    approved=False,
                    final_quantity=0.0,
                    rejection_reason=f"Failed claims: {', '.join(decomposed.failed_claims)}",
                    timestamp=datetime.utcnow(),
                    total_evaluation_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
                )
            
                self.rejected_count += 1
                return result
        
            # STAGE 3: Adversarial Failure Analysis
            logger.debug(f"Stage 3: Adversarial analysis")
            adversarial = self.adversarial_analyzer.analyze(signal, market_context)
        
            if not adversarial.survives_adversarial_analysis:
                logger.warning(f"Fails adversarial analysis: {len(adversarial.catastrophic_scenarios)} catastrophic scenarios")
            
                result = CompleteEvaluationResult(
                    signal_id=signal_id,
                    symbol=symbol,
                    market_hostility=hostility_assessment,
                    decomposed_signal=decomposed,
                    adversarial_analysis=adversarial,
                    confidence_vector=None,
                    unified_decision=None,
                    position_sizing=None,
                    approved=False,
                    final_quantity=0.0,
                    rejection_reason=f"Adversarial analysis failed: {adversarial.dominant_failure_risk.value if adversarial.dominant_failure_risk else 'unknown'}",
                    timestamp=datetime.utcnow(),
                    total_evaluation_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
                )
            
                self.rejected_count += 1
                return result
        
            # STAGE 4: Confidence Vector Building
            logger.debug(f"Stage 4: Confidence vector")
            confidence_vector = self.confidence_builder.build_confidence_vector(
                signal,
                market_context,
                historical_data
            )
        
            if confidence_vector.penalized_minimum_confidence < self.confidence_threshold:
                logger.warning(f"Confidence too low: {confidence_vector.penalized_minimum_confidence:.2%} < {self.confidence_threshold:.2%}")
            
                result = CompleteEvaluationResult(
                    signal_id=signal_id,
                    symbol=symbol,
                    market_hostility=hostility_assessment,
                    decomposed_signal=decomposed,
                    adversarial_analysis=adversarial,
                    confidence_vector=confidence_vector,
                    unified_decision=None,
                    position_sizing=None,
                    approved=False,
                    final_quantity=0.0,
                    rejection_reason=f"Minimum confidence {confidence_vector.penalized_minimum_confidence:.2%} < threshold {self.confidence_threshold:.2%}",
                    timestamp=datetime.utcnow(),
                    total_evaluation_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
                )
            
                self.rejected_count += 1
                return result
        
            # STAGE 5: Unified Decision Gate
            logger.debug(f"Stage 5: Unified decision gate")
            decision = self.decision_gate.evaluate(
                signal=signal,
                market_context=market_context,
                portfolio_state=portfolio_state,
                market_hostility_result=hostility_assessment,
                counterintelligence_report=directorate_report.counterintelligence,
                decomposed_signal=decomposed,
                adversarial_analysis=adversarial,
                confidence_vector=confidence_vector
            )
        
            if not decision.approved:
                logger.warning(f"Decision gate rejected: {decision.rejection_reason}")
            
                result = CompleteEvaluationResult(
                    signal_id=signal_id,
                    symbol=symbol,
                    market_hostility=hostility_assessment,
                    decomposed_signal=decomposed,
                    adversarial_analysis=adversarial,
                    confidence_vector=confidence_vector,
                    unified_decision=decision,
                    position_sizing=None,
                    approved=False,
                    final_quantity=0.0,
                    rejection_reason=decision.rejection_reason,
                    timestamp=datetime.utcnow(),
                    total_evaluation_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
                )
            
                self.rejected_count += 1
                return result
        
            # STAGE 6: Position Sizing
            logger.debug(f"Stage 6: Position sizing")
            position_sizing = self.position_sizer.calculate_position_size(
                signal=signal,
                confidence_vector=confidence_vector,
                market_context=market_context,
                portfolio_state=portfolio_state
            )
        
            # Validate position size
            if not self.position_sizer.validate_position_size(position_sizing, portfolio_state):
                logger.warning(f"Position size validation failed")
            
                result = CompleteEvaluationResult(
                    signal_id=signal_id,
                    symbol=symbol,
                    market_hostility=hostility_assessment,
                    decomposed_signal=decomposed,
                    adversarial_analysis=adversarial,
                    confidence_vector=confidence_vector,
                    unified_decision=decision,
                    position_sizing=position_sizing,
                    approved=False,
                    final_quantity=0.0,
                    rejection_reason="Position size validation failed",
                    timestamp=datetime.utcnow(),
                    total_evaluation_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
                )
            
                self.rejected_count += 1
                return result
        
            # ALL STAGES PASSED - APPROVED
            self.approved_count += 1
        
            total_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
            result = CompleteEvaluationResult(
                signal_id=signal_id,
                symbol=symbol,
                market_hostility=hostility_assessment,
                decomposed_signal=decomposed,
                adversarial_analysis=adversarial,
                confidence_vector=confidence_vector,
                unified_decision=decision,
                position_sizing=position_sizing,
                approved=True,
                final_quantity=position_sizing.final_quantity,
                rejection_reason="",
                timestamp=datetime.utcnow(),
                total_evaluation_time_ms=total_time,
                counterintelligence=directorate_report,
            )
        
            logger.info(
                f"✅ Signal {signal_id} APPROVED:\n"
                f"  Symbol: {symbol}\n"
                f"  Final Quantity: {position_sizing.final_quantity:.4f}\n"
                f"  Min Confidence: {confidence_vector.penalized_minimum_confidence:.2%}\n"
                f"  Risk: {position_sizing.final_risk_pct:.2%}\n"
                f"  Total Evaluation Time: {total_time:.1f}ms"
            )
        
            return result
        except Exception as e:
            logger.error(f"Error in evaluate_signal: {e}")
            raise
    
    def record_trade_outcome(
        self,
        signal_id: str,
        strategy_id: str,
        symbol: str,
        direction: str,
        predicted_regime: str,
        predicted_confidence: float,
        predicted_pnl: float,
        actual_regime: str,
        actual_pnl: float,
        won: bool,
        claim_failures: list
    ):
        """Record trade outcome for post-trade self-fixing"""
        try:
            outcome = TradeOutcome(
                trade_id=f"trade_{datetime.utcnow().timestamp()}",
                signal_id=signal_id,
                strategy_id=strategy_id,
                symbol=symbol,
                direction=direction,
                predicted_regime=predicted_regime,
                predicted_confidence=predicted_confidence,
                predicted_pnl=predicted_pnl,
                actual_regime=actual_regime,
                actual_pnl=actual_pnl,
                won=won,
                claim_failures=claim_failures,
                timestamp=datetime.utcnow()
            )
        
            self.self_fixer.record_trade_outcome(outcome)
        except Exception as e:
            logger.error(f"Error in record_trade_outcome: {e}")
            raise
    
    def get_complete_statistics(self) -> Dict[str, Any]:
        """Get complete statistics from all components"""
        return {
            'master_integration': {
                'total_evaluations': self.total_evaluations,
                'approved': self.approved_count,
                'rejected': self.rejected_count,
                'approval_rate': self.approved_count / self.total_evaluations if self.total_evaluations > 0 else 0.0
            },
            'market_hostility_gate': self.hostility_gate.get_statistics(),
            'decision_gate': self.decision_gate.get_statistics(),
            'strategy_health': self.self_fixer.get_all_strategy_health()
        }

    def _coerce_counterintelligence_mode(self, value: Any) -> CounterintelligenceMode:
        if isinstance(value, CounterintelligenceMode):
            return value
        try:
            return CounterintelligenceMode(str(value))
        except ValueError:
            return CounterintelligenceMode.HARD_GATE


# Global singleton
_global_master: Optional[AlphaAlgoMasterIntegration] = None


def get_global_master() -> AlphaAlgoMasterIntegration:
    """Get global master integration singleton"""
    try:
        global _global_master
        if _global_master is None:
            _global_master = AlphaAlgoMasterIntegration()
        return _global_master
    except Exception as e:
        logger.error(f"Error in get_global_master: {e}")
        raise


def create_master_integration(**kwargs) -> AlphaAlgoMasterIntegration:
    """Create new master integration instance"""
    return AlphaAlgoMasterIntegration(**kwargs)


async def evaluate_signal_complete(
    signal: Dict[str, Any],
    market_context: Dict[str, Any],
    portfolio_state: Dict[str, Any],
    historical_data: Optional[Dict[str, Any]] = None
) -> CompleteEvaluationResult:
    """Evaluate signal using global master integration"""
    return await get_global_master().evaluate_signal(
        signal,
        market_context,
        portfolio_state,
        historical_data
    )
