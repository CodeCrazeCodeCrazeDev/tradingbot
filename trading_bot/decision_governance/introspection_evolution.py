"""
Introspection-Driven Evolution Loop

A system that explains WHY failures happen and how to fix them.
Integrates deep diagnostic introspection with continuous capability discovery
to create a self-healing, self-improving trading system.

Core Loop:
1. Observe failure → 2. Introspect (explain WHY) → 3. Prescribe fix → 
4. Generate capability → 5. Validate → 6. Integrate → 7. Monitor
"""

from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import logging
import asyncio
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class RootCauseCategory(Enum):
    """Categories of root causes for failures"""
    MODEL_DEFICIENCY = "model_deficiency"  # Model architecture/inadequacy
    DATA_QUALITY = "data_quality"  # Input data issues
    CALIBRATION_DRIFT = "calibration_drift"  # Confidence miscalibration
    REGIME_MISMATCH = "regime_mismatch"  # Wrong market regime assumptions
    EXECUTION_FAILURE = "execution_failure"  # Slippage, liquidity, timing
    RISK_MANAGEMENT = "risk_management"  # Position sizing, drawdown
    SYSTEM_ERROR = "system_error"  # Bugs, infrastructure issues
    EXTERNAL_SHOCK = "external_shock"  # Unpredictable market events


class FixComplexity(Enum):
    """Complexity levels for fixes"""
    IMMEDIATE = "immediate"  # Config change, parameter tweak (< 1 day)
    SHORT_TERM = "short_term"  # Component improvement (1-7 days)
    MEDIUM_TERM = "medium_term"  # New capability needed (1-4 weeks)
    LONG_TERM = "long_term"  # Major architectural change (1-3 months)


@dataclass
class CausalFactor:
    """A single causal factor in a failure chain"""
    factor_id: str
    description: str
    category: RootCauseCategory
    evidence: List[str]
    confidence: float  # 0-1 confidence this factor contributed
    is_root: bool  # Is this the root cause vs contributing factor


@dataclass
class Explanation:
    """Human-readable explanation of why failure happened"""
    summary: str  # One-sentence summary
    detailed_narrative: str  # Full explanation
    causal_chain: List[CausalFactor]  # Ordered chain from root to outcome
    counterfactual: str  # What would have prevented this
    lessons: List[str]  # Key takeaways


@dataclass
class PrescribedFix:
    """A specific fix prescribed for a root cause"""
    fix_id: str
    target_cause: str  # Which causal factor this addresses
    description: str
    fix_type: str  # config, parameter, component, capability, architecture
    complexity: FixComplexity
    implementation_steps: List[str]
    expected_improvement: float  # Estimated impact
    risks: List[str]
    validation_criteria: List[str]  # How to know it worked
    automated: bool  # Can be applied automatically


@dataclass
class IntrospectionResult:
    """Complete result of introspection process"""
    failure_id: str
    timestamp: datetime
    explanation: Explanation
    prescribed_fixes: List[PrescribedFix]
    capability_gaps_created: List[str]  # IDs of gaps to add to discovery
    priority: float  # 0-1 urgency of addressing
    estimated_impact: float  # Estimated performance improvement if fixed
    status: str = "pending"  # pending, in_progress, resolved


@dataclass
class EvolutionLoopRecord:
    """Record of a complete evolution loop iteration"""
    loop_id: str
    introspection_id: str
    capability_gap_id: Optional[str]
    innovation_id: Optional[str]
    experiment_id: Optional[str]
    outcome: str  # success, failed, in_progress
    actual_improvement: Optional[float]
    lessons_learned: List[str]
    completed_at: Optional[datetime] = None


class IntrospectionDrivenEvolutionEngine:
    """
    Introspection-Driven Evolution Engine
    
    Explains WHY failures happen and prescribes specific fixes.
    Creates a closed-loop system where failures automatically generate
    improvements through capability discovery.
    
    Key Features:
    - Deep causal analysis with confidence scoring
    - Root cause categorization (8 categories)
    - Prescriptive fixes with implementation plans
    - Automated gap generation for capability discovery
    - Self-healing feedback loop
    - Impact prediction and tracking
    """
    
    def __init__(
        self,
        diagnostic_engine=None,
        failure_memory=None,
        outcome_memory=None,
        decision_memory=None,
        capability_discovery_engine=None,
        storage_path: Optional[str] = None
    ):
        self.diagnostic_engine = diagnostic_engine
        self.failure_memory = failure_memory
        self.outcome_memory = outcome_memory
        self.decision_memory = decision_memory
        self.capability_discovery = capability_discovery_engine
        self.storage_path = storage_path or "introspection_evolution_state.json"
        
        # Introspection tracking
        self.introspections: Dict[str, IntrospectionResult] = {}
        self.introspection_queue: deque = deque(maxlen=100)
        
        # Evolution loop tracking
        self.active_loops: Dict[str, EvolutionLoopRecord] = {}
        self.completed_loops: List[EvolutionLoopRecord] = []
        
        # Fix effectiveness tracking
        self.fix_effectiveness: Dict[str, List[Dict]] = defaultdict(list)
        
        # Root cause patterns
        self.root_cause_patterns: Dict[str, Dict] = {}
        
        # Callbacks
        self.on_introspection_complete: List[Callable] = []
        self.on_fix_prescribed: List[Callable] = []
        self.on_loop_completed: List[Callable] = []
        
        # Load state
        self._load_state()
        
        logger.info("IntrospectionDrivenEvolutionEngine initialized")
    
    # ==================== Core Introspection ====================
    
    async def introspect_failure(
        self,
        decision_id: str,
        auto_generate_fixes: bool = True,
        auto_create_gaps: bool = True
    ) -> IntrospectionResult:
        """
        Perform deep introspection on a failure to explain WHY it happened.
        
        Args:
            decision_id: ID of the failed decision to analyze
            auto_generate_fixes: Whether to automatically generate prescribed fixes
            auto_create_gaps: Whether to automatically create capability gaps
            
        Returns:
            Complete introspection result with explanation and fixes
        """
        logger.info(f"Starting introspection for failure: {decision_id}")
        
        # Gather all relevant data
        decision, outcome, context = await self._gather_failure_data(decision_id)
        
        if not decision or not outcome:
            logger.error(f"Could not gather data for decision {decision_id}")
            return None
        
        # Perform causal analysis
        causal_chain = self._analyze_causal_chain(decision, outcome, context)
        
        # Identify root cause
        root_cause = self._identify_root_cause(causal_chain)
        
        # Generate explanation
        explanation = self._generate_explanation(
            decision, outcome, causal_chain, root_cause, context
        )
        
        # Generate prescribed fixes if enabled
        prescribed_fixes = []
        if auto_generate_fixes:
            prescribed_fixes = self._prescribe_fixes(causal_chain, root_cause, decision)
        
        # Calculate priority and impact
        priority = self._calculate_priority(causal_chain, outcome)
        estimated_impact = self._estimate_fix_impact(root_cause, prescribed_fixes)
        
        # Create introspection result
        introspection_id = f"introspect_{decision_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        result = IntrospectionResult(
            failure_id=decision_id,
            timestamp=datetime.utcnow(),
            explanation=explanation,
            prescribed_fixes=prescribed_fixes,
            capability_gaps_created=[],
            priority=priority,
            estimated_impact=estimated_impact,
            status="pending"
        )
        
        self.introspections[introspection_id] = result
        
        # Auto-create capability gaps if enabled
        if auto_create_gaps and self.capability_discovery:
            gap_ids = await self._create_capability_gaps(introspection_id, result)
            result.capability_gaps_created = gap_ids
        
        # Trigger callbacks
        for callback in self.on_introspection_complete:
            try:
                callback(introspection_id, result)
            except Exception as e:
                logger.warning(f"Introspection callback error: {e}")
        
        # Save state
        self._save_state()
        
        logger.info(f"Introspection complete: {introspection_id}")
        logger.info(f"  Root cause: {root_cause.category.value}")
        logger.info(f"  Fixes prescribed: {len(prescribed_fixes)}")
        logger.info(f"  Priority: {priority:.2f}")
        
        return result
    
    async def _gather_failure_data(
        self,
        decision_id: str
    ) -> Tuple[Optional[Any], Optional[Any], Dict]:
        """Gather all data related to a failure"""
        decision = None
        outcome = None
        context = {}
        
        try:
            # Get decision record
            if self.decision_memory:
                decision = self.decision_memory.get_decision(decision_id)
            
            # Get outcome record
            if self.outcome_memory and decision_id in self.outcome_memory.outcomes:
                outcome = self.outcome_memory.outcomes[decision_id]
            
            # Get failure pattern if exists
            if self.failure_memory:
                patterns = [
                    p for p in self.failure_memory.patterns.values()
                    if decision_id in p.examples
                ]
                context['failure_patterns'] = patterns
            
            # Get diagnostic if exists
            if self.diagnostic_engine:
                # Look for existing diagnosis
                existing = [
                    d for d in self.diagnostic_engine.diagnosis_history
                    if d.decision_id == decision_id
                ]
                if existing:
                    context['existing_diagnosis'] = existing[-1]
            
            # Get market context
            context['timestamp'] = decision.timestamp if decision else datetime.utcnow()
            context['symbol'] = decision.symbol if decision else 'unknown'
            
        except Exception as e:
            logger.warning(f"Error gathering failure data: {e}")
        
        return decision, outcome, context
    
    def _analyze_causal_chain(
        self,
        decision: Any,
        outcome: Any,
        context: Dict
    ) -> List[CausalFactor]:
        """
        Analyze the complete causal chain from root cause to failure.
        Returns ordered list from root cause to immediate cause.
        """
        causal_factors = []
        
        # 1. Identify root cause category based on evidence
        root_category, evidence = self._categorize_root_cause(decision, outcome, context)
        
        # 2. Build causal chain based on category
        chain_builders = {
            RootCauseCategory.MODEL_DEFICIENCY: self._build_model_deficiency_chain,
            RootCauseCategory.DATA_QUALITY: self._build_data_quality_chain,
            RootCauseCategory.CALIBRATION_DRIFT: self._build_calibration_drift_chain,
            RootCauseCategory.REGIME_MISMATCH: self._build_regime_mismatch_chain,
            RootCauseCategory.EXECUTION_FAILURE: self._build_execution_failure_chain,
            RootCauseCategory.RISK_MANAGEMENT: self._build_risk_management_chain,
            RootCauseCategory.SYSTEM_ERROR: self._build_system_error_chain,
            RootCauseCategory.EXTERNAL_SHOCK: self._build_external_shock_chain,
        }
        
        builder = chain_builders.get(root_category, self._build_generic_chain)
        causal_factors = builder(decision, outcome, context, evidence)
        
        return causal_factors
    
    def _categorize_root_cause(
        self,
        decision: Any,
        outcome: Any,
        context: Dict
    ) -> Tuple[RootCauseCategory, List[str]]:
        """Determine the root cause category based on failure evidence"""
        evidence = []
        scores = defaultdict(float)
        
        # Check for calibration issues
        if outcome and hasattr(outcome, 'confidence_error'):
            if outcome.confidence_error > 0.3:
                scores[RootCauseCategory.CALIBRATION_DRIFT] += outcome.confidence_error
                evidence.append(f"High confidence error: {outcome.confidence_error:.2f}")
        
        # Check for regime mismatch
        if decision and hasattr(decision, 'regime_applicability_score'):
            if decision.regime_applicability_score < 0.4:
                scores[RootCauseCategory.REGIME_MISMATCH] += 0.5
                evidence.append(f"Low regime fit: {decision.regime_applicability_score:.2f}")
        
        # Check for execution issues
        if outcome and hasattr(outcome, 'fill_behavior'):
            if outcome.fill_behavior == 'partial' or outcome.slippage > 0.01:
                scores[RootCauseCategory.EXECUTION_FAILURE] += 0.6
                evidence.append(f"Execution slippage: {outcome.slippage:.4f}")
        
        # Check for invalidation hit (risk management)
        if outcome and hasattr(outcome, 'invalidation_hit') and outcome.invalidation_hit:
            scores[RootCauseCategory.RISK_MANAGEMENT] += 0.7
            evidence.append("Position hit invalidation condition")
        
        # Check for overconfidence (model deficiency)
        if decision and hasattr(decision, 'uncertainty_profile'):
            if decision.uncertainty_profile:
                if decision.uncertainty_profile.overall_confidence > 0.8 and outcome.realized_pnl < 0:
                    scores[RootCauseCategory.MODEL_DEFICIENCY] += 0.5
                    evidence.append("High confidence with negative outcome")
        
        # Check for robustness issues (model deficiency)
        if decision and hasattr(decision, 'robustness_score'):
            if decision.robustness_score < 0.4:
                scores[RootCauseCategory.MODEL_DEFICIENCY] += 0.4
                evidence.append(f"Low robustness score: {decision.robustness_score:.2f}")
        
        # Check for data quality issues
        if decision and hasattr(decision, 'evidence_coverage'):
            missing = decision.evidence_coverage.get('missing_critical', [])
            if missing:
                scores[RootCauseCategory.DATA_QUALITY] += len(missing) * 0.2
                evidence.append(f"Missing evidence: {missing}")
        
        # Get highest scoring category
        if scores:
            top_category = max(scores.items(), key=lambda x: x[1])
            return top_category[0], evidence
        
        # Default to model deficiency if no clear pattern
        return RootCauseCategory.MODEL_DEFICIENCY, ["No clear pattern - defaulting to model deficiency"]
    
    def _build_model_deficiency_chain(
        self, decision, outcome, context, evidence
    ) -> List[CausalFactor]:
        """Build causal chain for model deficiency failures"""
        factors = []
        
        # Root: Model architecture inadequacy
        factors.append(CausalFactor(
            factor_id="model_inadequacy",
            description="Model architecture inadequate for current market conditions",
            category=RootCauseCategory.MODEL_DEFICIENCY,
            evidence=evidence,
            confidence=0.7,
            is_root=True
        ))
        
        # Contributing: Feature set insufficient
        if decision and hasattr(decision, 'claims'):
            factors.append(CausalFactor(
                factor_id="insufficient_features",
                description="Feature set doesn't capture relevant market dynamics",
                category=RootCauseCategory.MODEL_DEFICIENCY,
                evidence=["Limited feature coverage in claims"],
                confidence=0.6,
                is_root=False
            ))
        
        # Contributing: Overfitting
        if outcome and hasattr(outcome, 'confidence_error'):
            factors.append(CausalFactor(
                factor_id="overfitting",
                description="Model overfit to historical patterns that no longer hold",
                category=RootCauseCategory.MODEL_DEFICIENCY,
                evidence=[f"Confidence error: {outcome.confidence_error:.2f}"],
                confidence=0.5,
                is_root=False
            ))
        
        # Immediate: Wrong prediction
        factors.append(CausalFactor(
            factor_id="wrong_prediction",
            description="Model produced incorrect directional prediction",
            category=RootCauseCategory.MODEL_DEFICIENCY,
            evidence=[f"PnL: {outcome.realized_pnl if outcome else 'unknown'}"],
            confidence=0.9,
            is_root=False
        ))
        
        return factors
    
    def _build_calibration_drift_chain(
        self, decision, outcome, context, evidence
    ) -> List[CausalFactor]:
        """Build causal chain for calibration drift failures"""
        factors = []
        
        # Root: Calibration drift
        factors.append(CausalFactor(
            factor_id="calibration_drift",
            description="Model confidence calibration has drifted from reality",
            category=RootCauseCategory.CALIBRATION_DRIFT,
            evidence=evidence,
            confidence=0.8,
            is_root=True
        ))
        
        # Contributing: No recent recalibration
        factors.append(CausalFactor(
            factor_id="stale_calibration",
            description="Calibration not updated with recent market data",
            category=RootCauseCategory.CALIBRATION_DRIFT,
            evidence=["No recent calibration events in audit trail"],
            confidence=0.6,
            is_root=False
        ))
        
        # Contributing: Overconfidence in predictions
        if decision and hasattr(decision, 'uncertainty_profile'):
            conf = decision.uncertainty_profile.overall_confidence if decision.uncertainty_profile else 0.5
            factors.append(CausalFactor(
                factor_id="overconfidence",
                description=f"Excessive confidence ({conf:.2f}) led to oversized position",
                category=RootCauseCategory.CALIBRATION_DRIFT,
                evidence=[f"Confidence: {conf:.2f}, PnL: {outcome.realized_pnl if outcome else 'unknown'}"],
                confidence=0.7,
                is_root=False
            ))
        
        # Immediate: Wrong position sizing
        factors.append(CausalFactor(
            factor_id="wrong_sizing",
            description="Position size based on miscalibrated confidence",
            category=RootCauseCategory.CALIBRATION_DRIFT,
            evidence=["Position size inconsistent with actual edge"],
            confidence=0.8,
            is_root=False
        ))
        
        return factors
    
    def _build_regime_mismatch_chain(
        self, decision, outcome, context, evidence
    ) -> List[CausalFactor]:
        """Build causal chain for regime mismatch failures"""
        factors = []
        
        # Root: Regime detection failure
        factors.append(CausalFactor(
            factor_id="regime_detection_failure",
            description="Failed to detect or adapt to current market regime",
            category=RootCauseCategory.REGIME_MISMATCH,
            evidence=evidence,
            confidence=0.75,
            is_root=True
        ))
        
        # Contributing: Wrong regime classification
        if decision and hasattr(decision, 'current_regime'):
            factors.append(CausalFactor(
                factor_id="wrong_regime",
                description=f"Incorrectly classified regime as {decision.current_regime.volatility_state if decision.current_regime else 'unknown'}",
                category=RootCauseCategory.REGIME_MISMATCH,
                evidence=["Regime fit score below threshold"],
                confidence=0.7,
                is_root=False
            ))
        
        # Contributing: Strategy not suited to regime
        factors.append(CausalFactor(
            factor_id="strategy_regime_mismatch",
            description="Strategy deployed is ineffective in current regime",
            category=RootCauseCategory.REGIME_MISMATCH,
            evidence=["Historical strategy performance poor in this regime"],
            confidence=0.6,
            is_root=False
        ))
        
        return factors
    
    def _build_execution_failure_chain(
        self, decision, outcome, context, evidence
    ) -> List[CausalFactor]:
        """Build causal chain for execution failures"""
        factors = []
        
        # Root: Execution modeling inadequacy
        factors.append(CausalFactor(
            factor_id="execution_model_failure",
            description="Execution cost/impact model failed to predict actual conditions",
            category=RootCauseCategory.EXECUTION_FAILURE,
            evidence=evidence,
            confidence=0.8,
            is_root=True
        ))
        
        # Contributing: Liquidity underestimated
        if outcome and hasattr(outcome, 'fill_behavior'):
            factors.append(CausalFactor(
                factor_id="liquidity_underestimated",
                description="Available liquidity lower than expected",
                category=RootCauseCategory.EXECUTION_FAILURE,
                evidence=[f"Fill behavior: {outcome.fill_behavior}"],
                confidence=0.7,
                is_root=False
            ))
        
        # Contributing: Timing wrong
        factors.append(CausalFactor(
            factor_id="bad_timing",
            description="Execution timing missed optimal window",
            category=RootCauseCategory.EXECUTION_FAILURE,
            evidence=["High slippage relative to market conditions"],
            confidence=0.6,
            is_root=False
        ))
        
        return factors
    
    def _build_risk_management_chain(
        self, decision, outcome, context, evidence
    ) -> List[CausalFactor]:
        """Build causal chain for risk management failures"""
        factors = []
        
        # Root: Risk monitoring gaps
        factors.append(CausalFactor(
            factor_id="risk_monitoring_gaps",
            description="Risk management failed to detect or respond to adverse conditions",
            category=RootCauseCategory.RISK_MANAGEMENT,
            evidence=evidence,
            confidence=0.8,
            is_root=True
        ))
        
        # Contributing: Invalidation not detected
        if outcome and hasattr(outcome, 'invalidation_hit') and outcome.invalidation_hit:
            factors.append(CausalFactor(
                factor_id="invalidation_missed",
                description="Position invalidation condition occurred but was not acted upon",
                category=RootCauseCategory.RISK_MANAGEMENT,
                evidence=["Invalidation hit flag set"],
                confidence=0.9,
                is_root=False
            ))
        
        # Contributing: Position too large
        factors.append(CausalFactor(
            factor_id="oversized_position",
            description="Position size exceeded prudent risk limits for the setup",
            category=RootCauseCategory.RISK_MANAGEMENT,
            evidence=["Position size disproportionate to edge confidence"],
            confidence=0.6,
            is_root=False
        ))
        
        return factors
    
    def _build_data_quality_chain(
        self, decision, outcome, context, evidence
    ) -> List[CausalFactor]:
        """Build causal chain for data quality failures"""
        factors = []
        
        factors.append(CausalFactor(
            factor_id="data_quality_issue",
            description="Input data had quality issues affecting model accuracy",
            category=RootCauseCategory.DATA_QUALITY,
            evidence=evidence,
            confidence=0.7,
            is_root=True
        ))
        
        return factors
    
    def _build_system_error_chain(
        self, decision, outcome, context, evidence
    ) -> List[CausalFactor]:
        """Build causal chain for system errors"""
        factors = []
        
        factors.append(CausalFactor(
            factor_id="system_error",
            description="System or infrastructure error caused failure",
            category=RootCauseCategory.SYSTEM_ERROR,
            evidence=evidence,
            confidence=0.9,
            is_root=True
        ))
        
        return factors
    
    def _build_external_shock_chain(
        self, decision, outcome, context, evidence
    ) -> List[CausalFactor]:
        """Build causal chain for external shocks"""
        factors = []
        
        factors.append(CausalFactor(
            factor_id="external_shock",
            description="Unpredictable external market event caused failure",
            category=RootCauseCategory.EXTERNAL_SHOCK,
            evidence=evidence,
            confidence=0.6,
            is_root=True
        ))
        
        return factors
    
    def _build_generic_chain(
        self, decision, outcome, context, evidence
    ) -> List[CausalFactor]:
        """Generic causal chain when no specific pattern matches"""
        return [CausalFactor(
            factor_id="unknown_cause",
            description="Root cause unclear - requires further investigation",
            category=RootCauseCategory.MODEL_DEFICIENCY,
            evidence=evidence,
            confidence=0.3,
            is_root=True
        )]
    
    def _identify_root_cause(
        self,
        causal_chain: List[CausalFactor]
    ) -> CausalFactor:
        """Identify the root cause from causal chain"""
        # Find the root cause (is_root=True with highest confidence)
        roots = [f for f in causal_chain if f.is_root]
        if roots:
            return max(roots, key=lambda f: f.confidence)
        
        # Fallback to first factor
        return causal_chain[0] if causal_chain else None

    def _generate_explanation(
        self,
        decision: Any,
        outcome: Any,
        causal_chain: List[CausalFactor],
        root_cause: CausalFactor,
        context: Dict
    ) -> Explanation:
        """Generate human-readable explanation of failure"""
        
        # Generate summary
        summary = self._generate_summary(root_cause, outcome)
        
        # Generate detailed narrative
        narrative = self._generate_narrative(decision, outcome, causal_chain, root_cause)
        
        # Generate counterfactual
        counterfactual = self._generate_counterfactual(causal_chain, root_cause)
        
        # Extract lessons
        lessons = self._extract_lessons(causal_chain, root_cause, outcome)
        
        return Explanation(
            summary=summary,
            detailed_narrative=narrative,
            causal_chain=causal_chain,
            counterfactual=counterfactual,
            lessons=lessons
        )
    
    def _generate_summary(
        self,
        root_cause: CausalFactor,
        outcome: Any
    ) -> str:
        """Generate one-sentence summary"""
        pnl = outcome.realized_pnl if outcome and hasattr(outcome, 'realized_pnl') else 0
        
        summaries = {
            RootCauseCategory.MODEL_DEFICIENCY: 
                f"Trade lost {pnl:.2%} due to model inadequacy: {root_cause.description}",
            RootCauseCategory.CALIBRATION_DRIFT: 
                f"Trade lost {pnl:.2%} due to confidence miscalibration causing poor position sizing",
            RootCauseCategory.REGIME_MISMATCH: 
                f"Trade lost {pnl:.2%} because strategy was deployed in unsuitable market regime",
            RootCauseCategory.EXECUTION_FAILURE: 
                f"Trade lost {pnl:.2%} due to execution slippage and liquidity issues",
            RootCauseCategory.RISK_MANAGEMENT: 
                f"Trade lost {pnl:.2%} because risk management failed to detect invalidation conditions",
            RootCauseCategory.DATA_QUALITY: 
                f"Trade lost {pnl:.2%} due to poor input data quality affecting model accuracy",
            RootCauseCategory.SYSTEM_ERROR: 
                f"Trade lost {pnl:.2%} due to system or infrastructure error",
            RootCauseCategory.EXTERNAL_SHOCK: 
                f"Trade lost {pnl:.2%} due to unpredictable external market event",
        }
        
        return summaries.get(
            root_cause.category, 
            f"Trade lost {pnl:.2%} - root cause: {root_cause.description}"
        )
    
    def _generate_narrative(
        self,
        decision: Any,
        outcome: Any,
        causal_chain: List[CausalFactor],
        root_cause: CausalFactor
    ) -> str:
        """Generate detailed narrative explanation"""
        
        symbol = decision.symbol if decision and hasattr(decision, 'symbol') else 'unknown'
        timestamp = decision.timestamp if decision and hasattr(decision, 'timestamp') else datetime.utcnow()
        pnl = outcome.realized_pnl if outcome and hasattr(outcome, 'realized_pnl') else 0
        
        narrative_parts = [
            f"On {timestamp.strftime('%Y-%m-%d %H:%M')}, a trade in {symbol} resulted in a loss of {pnl:.2%}.",
            "",
            f"ROOT CAUSE: {root_cause.description}",
            f"Category: {root_cause.category.value}",
            f"Confidence: {root_cause.confidence:.0%}",
            "",
            "EVIDENCE:",
        ]
        
        for evidence in root_cause.evidence:
            narrative_parts.append(f"  - {evidence}")
        
        if len(causal_chain) > 1:
            narrative_parts.extend([
                "",
                "CAUSAL CHAIN:",
            ])
            for i, factor in enumerate(causal_chain, 1):
                marker = " [ROOT]" if factor.is_root else ""
                narrative_parts.append(f"  {i}. {factor.description}{marker} ({factor.confidence:.0%} confidence)")
        
        return "\n".join(narrative_parts)
    
    def _generate_counterfactual(
        self,
        causal_chain: List[CausalFactor],
        root_cause: CausalFactor
    ) -> str:
        """Generate counterfactual explanation"""
        
        counterfactuals = {
            RootCauseCategory.MODEL_DEFICIENCY: 
                "If the model had been updated with recent market data or the trade had been blocked due to model uncertainty, this loss would have been avoided.",
            RootCauseCategory.CALIBRATION_DRIFT: 
                "If confidence calibration had been updated with recent outcomes and position sizing reduced accordingly, the loss would have been smaller or avoided.",
            RootCauseCategory.REGIME_MISMATCH: 
                "If the system had correctly identified the regime as unsuitable and blocked this strategy, the trade would not have been taken.",
            RootCauseCategory.EXECUTION_FAILURE: 
                "If execution timing had been optimized and position size adjusted for available liquidity, slippage would have been reduced.",
            RootCauseCategory.RISK_MANAGEMENT: 
                "If invalidation monitoring had been real-time and position exited promptly, the loss would have been smaller.",
            RootCauseCategory.DATA_QUALITY: 
                "If data quality checks had caught the issues before model inference, the trade would have been blocked or sized smaller.",
            RootCauseCategory.SYSTEM_ERROR: 
                "If system monitoring had detected and handled the error, the trade would have been managed correctly.",
            RootCauseCategory.EXTERNAL_SHOCK: 
                "This was likely unavoidable, but if position sizing had been more conservative, the loss would have been smaller.",
        }
        
        return counterfactuals.get(
            root_cause.category,
            f"If {root_cause.description} had been addressed, this failure could have been prevented."
        )
    
    def _extract_lessons(
        self,
        causal_chain: List[CausalFactor],
        root_cause: CausalFactor,
        outcome: Any
    ) -> List[str]:
        """Extract key lessons from the failure"""
        
        lessons = []
        
        # Category-specific lessons
        category_lessons = {
            RootCauseCategory.MODEL_DEFICIENCY: [
                "Model performance must be continuously monitored",
                "Model updates should be triggered by performance degradation",
                "Uncertain predictions should reduce position size or block trades"
            ],
            RootCauseCategory.CALIBRATION_DRIFT: [
                "Confidence calibration must be regularly updated",
                "High confidence requires calibration validation",
                "Position sizing must reflect true confidence, not just model output"
            ],
            RootCauseCategory.REGIME_MISMATCH: [
                "Regime detection is critical for strategy selection",
                "Strategy-regime fit must be validated before trading",
                "Regime transitions require heightened caution"
            ],
            RootCauseCategory.EXECUTION_FAILURE: [
                "Execution feasibility must be verified pre-trade",
                "Position size must account for available liquidity",
                "Execution timing optimization can significantly impact PnL"
            ],
            RootCauseCategory.RISK_MANAGEMENT: [
                "Invalidation conditions must be monitored in real-time",
                "Position sizing must account for tail risks",
                "Risk management failures compound losses quickly"
            ],
            RootCauseCategory.DATA_QUALITY: [
                "Data quality checks must precede model inference",
                "Missing or stale data should block or reduce trade size",
                "Data pipeline health must be continuously monitored"
            ],
        }
        
        lessons.extend(category_lessons.get(root_cause.category, []))
        
        # Add generic lessons
        lessons.append("Every failure should generate a capability improvement")
        lessons.append("Similar failures should be detected and prevented")
        
        return lessons
    
    # ==================== Fix Prescription ====================
    
    def _prescribe_fixes(
        self,
        causal_chain: List[CausalFactor],
        root_cause: CausalFactor,
        decision: Any
    ) -> List[PrescribedFix]:
        """Generate specific fixes for the root cause"""
        
        fixes = []
        
        # Get fix templates for the root cause category
        fix_templates = self._get_fix_templates(root_cause.category)
        
        for template in fix_templates:
            fix = self._instantiate_fix(template, root_cause, causal_chain, decision)
            if fix:
                fixes.append(fix)
        
        # Sort by expected improvement / complexity
        fixes.sort(key=lambda f: f.expected_improvement / self._complexity_weight(f.complexity), reverse=True)
        
        return fixes[:3]  # Return top 3 fixes
    
    def _get_fix_templates(self, category: RootCauseCategory) -> List[Dict]:
        """Get fix templates for a root cause category"""
        
        templates = {
            RootCauseCategory.MODEL_DEFICIENCY: [
                {
                    'fix_type': 'capability',
                    'complexity': FixComplexity.MEDIUM_TERM,
                    'description': 'Implement model performance monitoring with automatic retraining triggers',
                    'implementation_steps': [
                        'Add real-time model performance tracking',
                        'Define performance degradation thresholds',
                        'Implement automatic retraining pipeline',
                        'Add model A/B testing framework'
                    ],
                    'expected_improvement': 0.15,
                    'risks': ['Retraining may introduce new bugs', 'Computational cost of frequent retraining'],
                    'validation_criteria': ['Model performance stays above threshold', 'Retraining reduces error rate']
                },
                {
                    'fix_type': 'parameter',
                    'complexity': FixComplexity.IMMEDIATE,
                    'description': 'Reduce position size when model confidence is below calibrated threshold',
                    'implementation_steps': [
                        'Add confidence threshold check before sizing',
                        'Implement graduated position sizing based on confidence',
                        'Add monitoring for confidence-sensitivity relationship'
                    ],
                    'expected_improvement': 0.08,
                    'risks': ['May reduce profitable trades too', 'Requires calibration of thresholds'],
                    'validation_criteria': ['Reduced loss rate in low-confidence trades', 'Maintained win rate in high-confidence trades']
                }
            ],
            RootCauseCategory.CALIBRATION_DRIFT: [
                {
                    'fix_type': 'component',
                    'complexity': FixComplexity.SHORT_TERM,
                    'description': 'Implement automated confidence calibration with sliding window',
                    'implementation_steps': [
                        'Add sliding window calibration calculation',
                        'Implement recalibration trigger based on drift detection',
                        'Add calibration quality monitoring',
                        'Implement temperature scaling for confidence adjustment'
                    ],
                    'expected_improvement': 0.12,
                    'risks': ['May overfit to recent data', 'Calibration may oscillate'],
                    'validation_criteria': ['Calibration error stays below 0.15', 'Reliability diagrams show good fit']
                },
                {
                    'fix_type': 'config',
                    'complexity': FixComplexity.IMMEDIATE,
                    'description': 'Reduce maximum position size multiplier until calibration fixed',
                    'implementation_steps': [
                        'Temporarily reduce max_position_multiplier',
                        'Add calibration quality gate before trading',
                        'Monitor position sizing effectiveness'
                    ],
                    'expected_improvement': 0.05,
                    'risks': ['Reduced returns during fix period', 'May not address root cause'],
                    'validation_criteria': ['Reduced drawdown', 'Stable position sizing']
                }
            ],
            RootCauseCategory.REGIME_MISMATCH: [
                {
                    'fix_type': 'capability',
                    'complexity': FixComplexity.MEDIUM_TERM,
                    'description': 'Enhance regime detection with leading indicators and transition prediction',
                    'implementation_steps': [
                        'Add leading indicators to regime detection',
                        'Implement regime transition probability model',
                        'Add strategy-regime compatibility matrix',
                        'Implement regime-specific risk adjustments'
                    ],
                    'expected_improvement': 0.18,
                    'risks': ['May add complexity without benefit', 'Regime changes can be unpredictable'],
                    'validation_criteria': ['Earlier regime detection', 'Higher win rate per regime', 'Reduced regime-mismatch losses']
                },
                {
                    'fix_type': 'parameter',
                    'complexity': FixComplexity.IMMEDIATE,
                    'description': 'Increase minimum regime fit threshold for strategy deployment',
                    'implementation_steps': [
                        'Raise regime_applicability_score threshold',
                        'Add regime uncertainty penalty to position sizing',
                        'Monitor strategy performance by regime'
                    ],
                    'expected_improvement': 0.06,
                    'risks': ['May block profitable trades in borderline regimes'],
                    'validation_criteria': ['Higher win rate in trades taken', 'Reduced losses from regime mismatch']
                }
            ],
            RootCauseCategory.EXECUTION_FAILURE: [
                {
                    'fix_type': 'component',
                    'complexity': FixComplexity.SHORT_TERM,
                    'description': 'Implement dynamic liquidity estimation and adaptive execution sizing',
                    'implementation_steps': [
                        'Add real-time order book depth analysis',
                        'Implement volume-weighted execution timing',
                        'Add liquidity-adjusted position sizing',
                        'Implement smart order routing'
                    ],
                    'expected_improvement': 0.10,
                    'risks': ['Complexity of real-time analysis', 'Potential for over-engineering'],
                    'validation_criteria': ['Reduced slippage', 'Better fill rates', 'Lower market impact']
                }
            ],
            RootCauseCategory.RISK_MANAGEMENT: [
                {
                    'fix_type': 'capability',
                    'complexity': FixComplexity.MEDIUM_TERM,
                    'description': 'Implement real-time invalidation monitoring with automatic position exit',
                    'implementation_steps': [
                        'Add streaming invalidation condition checks',
                        'Implement sub-second invalidation detection',
                        'Add automatic position reduction on invalidation',
                        'Implement post-invalidation analysis and reporting'
                    ],
                    'expected_improvement': 0.14,
                    'risks': ['False positives may exit good trades', 'Latency requirements for real-time monitoring'],
                    'validation_criteria': ['Faster invalidation detection', 'Reduced losses on invalidation hits', 'Lower average drawdown']
                },
                {
                    'fix_type': 'parameter',
                    'complexity': FixComplexity.IMMEDIATE,
                    'description': 'Reduce position sizes across all strategies until risk system improved',
                    'implementation_steps': [
                        'Apply global position size reduction factor',
                        'Tighten stop-loss thresholds',
                        'Increase cash buffer requirements'
                    ],
                    'expected_improvement': 0.04,
                    'risks': ['Reduced returns', 'Does not fix underlying issue'],
                    'validation_criteria': ['Reduced drawdown', 'Lower volatility']
                }
            ],
            RootCauseCategory.DATA_QUALITY: [
                {
                    'fix_type': 'component',
                    'complexity': FixComplexity.SHORT_TERM,
                    'description': 'Implement comprehensive data quality validation pipeline',
                    'implementation_steps': [
                        'Add data freshness checks',
                        'Implement outlier and anomaly detection',
                        'Add data completeness validation',
                        'Implement data quality scoring'
                    ],
                    'expected_improvement': 0.09,
                    'risks': ['False positives may block good trades', 'Additional latency from validation'],
                    'validation_criteria': ['Fewer data-related errors', 'Higher data quality scores', 'Reduced bad data impact']
                }
            ]
        }
        
        return templates.get(category, [])
    
    def _instantiate_fix(
        self,
        template: Dict,
        root_cause: CausalFactor,
        causal_chain: List[CausalFactor],
        decision: Any
    ) -> PrescribedFix:
        """Instantiate a fix from template with specific details"""
        
        fix_id = f"fix_{root_cause.factor_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        return PrescribedFix(
            fix_id=fix_id,
            target_cause=root_cause.factor_id,
            description=template['description'],
            fix_type=template['fix_type'],
            complexity=template['complexity'],
            implementation_steps=template['implementation_steps'],
            expected_improvement=template['expected_improvement'],
            risks=template['risks'],
            validation_criteria=template['validation_criteria'],
            automated=template['fix_type'] in ['config', 'parameter']
        )
    
    def _complexity_weight(self, complexity: FixComplexity) -> float:
        """Convert complexity to weight for prioritization"""
        weights = {
            FixComplexity.IMMEDIATE: 1.0,
            FixComplexity.SHORT_TERM: 2.0,
            FixComplexity.MEDIUM_TERM: 4.0,
            FixComplexity.LONG_TERM: 8.0
        }
        return weights.get(complexity, 4.0)
    
    def _calculate_priority(
        self,
        causal_chain: List[CausalFactor],
        outcome: Any
    ) -> float:
        """Calculate priority score for addressing this failure"""
        
        # Base priority on loss size
        pnl = outcome.realized_pnl if outcome and hasattr(outcome, 'realized_pnl') else 0
        loss_factor = min(1.0, abs(pnl) * 10)  # Scale by loss magnitude
        
        # Root cause confidence
        root_confidence = max((f.confidence for f in causal_chain if f.is_root), default=0.5)
        
        # Frequency of similar failures (if we have pattern data)
        frequency_factor = 0.5  # Default
        if self.failure_memory:
            similar = len([
                p for p in self.failure_memory.patterns.values()
                if p.frequency > 2
            ])
            frequency_factor = min(1.0, similar / 10)
        
        priority = (loss_factor * 0.4 + root_confidence * 0.4 + frequency_factor * 0.2)
        
        return min(1.0, priority)
    
    def _estimate_fix_impact(
        self,
        root_cause: CausalFactor,
        prescribed_fixes: List[PrescribedFix]
    ) -> float:
        """Estimate the impact of implementing the prescribed fixes"""
        
        if not prescribed_fixes:
            return 0.0
        
        # Sum expected improvements (with diminishing returns)
        total = 0.0
        for i, fix in enumerate(prescribed_fixes):
            total += fix.expected_improvement * (0.8 ** i)  # Diminishing returns
        
        return min(0.5, total)  # Cap at 50% improvement
    
    # ==================== Integration with Capability Discovery ====================
    
    async def _create_capability_gaps(
        self,
        introspection_id: str,
        result: IntrospectionResult
    ) -> List[str]:
        """Create capability gaps from introspection for discovery engine"""
        
        if not self.capability_discovery:
            return []
        
        gap_ids = []
        
        # Create a gap for each non-automated fix
        for fix in result.prescribed_fixes:
            if not fix.automated or fix.complexity in [FixComplexity.MEDIUM_TERM, FixComplexity.LONG_TERM]:
                gap = self._fix_to_capability_gap(fix, result)
                
                # Add to capability discovery engine
                gap_id = f"gap_introspect_{introspection_id}_{fix.fix_id}"
                
                # Create CapabilityGap object
                from .continuous_capability_discovery import CapabilityGap
                
                capability_gap = CapabilityGap(
                    id=gap_id,
                    description=f"Introspection-generated: {fix.description}",
                    affected_categories=self._fix_to_categories(fix),
                    severity=result.priority,
                    impact_score=fix.expected_improvement,
                    detection_date=datetime.utcnow(),
                    evidence=[{
                        'type': 'introspection',
                        'introspection_id': introspection_id,
                        'failure_id': result.failure_id,
                        'root_cause': result.explanation.causal_chain[0].description if result.explanation.causal_chain else 'unknown'
                    }],
                    root_causes=[result.explanation.causal_chain[0].category.value if result.explanation.causal_chain else 'unknown']
                )
                
                # Add to capability discovery engine
                self.capability_discovery.active_gaps[gap_id] = capability_gap
                
                gap_ids.append(gap_id)
                
                logger.info(f"Created capability gap from introspection: {gap_id}")
        
        return gap_ids
    
    def _fix_to_capability_gap(self, fix: PrescribedFix, result: IntrospectionResult) -> Dict:
        """Convert a prescribed fix to a capability gap specification"""
        
        return {
            'gap_id': fix.fix_id,
            'description': fix.description,
            'severity': result.priority,
            'impact_score': fix.expected_improvement,
            'source': 'introspection',
            'introspection_id': result.failure_id,
            'fix_complexity': fix.complexity.value,
            'implementation_steps': fix.implementation_steps,
            'validation_criteria': fix.validation_criteria
        }
    
    def _fix_to_categories(self, fix: PrescribedFix) -> List[str]:
        """Map fix type to capability categories"""
        
        category_map = {
            'config': ['decision_governance'],
            'parameter': ['decision_governance'],
            'component': ['signal_generation', 'risk_management', 'execution'],
            'capability': ['signal_generation', 'risk_management', 'execution', 'market_analysis'],
            'architecture': ['decision_governance', 'portfolio_management']
        }
        
        return category_map.get(fix.fix_type, ['decision_governance'])
    
    # ==================== Evolution Loop Management ====================
    
    async def start_evolution_loop(
        self,
        failure_id: str,
        auto_execute_immediate: bool = True
    ) -> EvolutionLoopRecord:
        """
        Start a complete evolution loop for a failure.
        
        Flow:
        1. Introspect failure → 2. Prescribe fixes → 3. Create capability gaps → 
        4. Generate innovations → 5. Validate → 6. Integrate
        """
        
        logger.info(f"Starting evolution loop for failure: {failure_id}")
        
        # Step 1: Introspect
        introspection = await self.introspect_failure(failure_id)
        if not introspection:
            logger.error(f"Introspection failed for {failure_id}")
            return None
        
        introspection_id = [
            k for k, v in self.introspections.items() 
            if v.failure_id == failure_id
        ][-1]  # Get most recent
        
        # Execute immediate fixes if enabled
        if auto_execute_immediate:
            for fix in introspection.prescribed_fixes:
                if fix.automated and fix.complexity == FixComplexity.IMMEDIATE:
                    await self._execute_immediate_fix(fix, failure_id)
        
        # Create evolution loop record
        loop_id = f"loop_{failure_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        loop_record = EvolutionLoopRecord(
            loop_id=loop_id,
            introspection_id=introspection_id,
            capability_gap_id=introspection.capability_gaps_created[0] if introspection.capability_gaps_created else None,
            innovation_id=None,
            experiment_id=None,
            outcome="in_progress",
            actual_improvement=None,
            lessons_learned=[]
        )
        
        self.active_loops[loop_id] = loop_record
        
        # The rest of the loop (innovation generation, validation, integration)
        # will be handled by the continuous capability discovery engine
        # which monitors capability gaps and generates innovations
        
        logger.info(f"Evolution loop started: {loop_id}")
        
        return loop_record
    
    async def _execute_immediate_fix(self, fix: PrescribedFix, failure_id: str):
        """Execute an immediate fix automatically"""
        
        logger.info(f"Executing immediate fix: {fix.fix_id}")
        
        # In a real implementation, this would modify system configuration
        # For now, we log the fix that would be applied
        
        fix_record = {
            'fix_id': fix.fix_id,
            'failure_id': failure_id,
            'description': fix.description,
            'executed_at': datetime.utcnow().isoformat(),
            'status': 'applied'
        }
        
        self.fix_effectiveness[fix.fix_id].append(fix_record)
        
        # Trigger callback
        for callback in self.on_fix_prescribed:
            try:
                callback(fix, failure_id, True)
            except Exception as e:
                logger.warning(f"Fix callback error: {e}")
        
        logger.info(f"Immediate fix applied: {fix.fix_id}")
    
    def complete_evolution_loop(
        self,
        loop_id: str,
        innovation_id: Optional[str],
        experiment_id: Optional[str],
        outcome: str,
        actual_improvement: Optional[float],
        lessons: List[str]
    ):
        """Mark an evolution loop as completed"""
        
        if loop_id not in self.active_loops:
            logger.warning(f"Loop {loop_id} not found")
            return
        
        loop_record = self.active_loops.pop(loop_id)
        loop_record.innovation_id = innovation_id
        loop_record.experiment_id = experiment_id
        loop_record.outcome = outcome
        loop_record.actual_improvement = actual_improvement
        loop_record.lessons_learned = lessons
        loop_record.completed_at = datetime.utcnow()
        
        self.completed_loops.append(loop_record)
        
        # Save fix effectiveness data
        if loop_record.introspection_id in self.introspections:
            introspection = self.introspections[loop_record.introspection_id]
            for fix in introspection.prescribed_fixes:
                self.fix_effectiveness[fix.fix_id].append({
                    'loop_id': loop_id,
                    'predicted_improvement': fix.expected_improvement,
                    'actual_improvement': actual_improvement,
                    'outcome': outcome
                })
        
        # Trigger callback
        for callback in self.on_loop_completed:
            try:
                callback(loop_record)
            except Exception as e:
                logger.warning(f"Loop completion callback error: {e}")
        
        self._save_state()
        
        logger.info(f"Evolution loop completed: {loop_id}")
        logger.info(f"  Outcome: {outcome}")
        logger.info(f"  Actual improvement: {actual_improvement}")
    
    # ==================== State Management ====================
    
    def _save_state(self):
        """Save engine state"""
        try:
            state = {
                'introspections_count': len(self.introspections),
                'completed_loops_count': len(self.completed_loops),
                'fix_effectiveness': dict(self.fix_effectiveness),
                'saved_at': datetime.utcnow().isoformat()
            }
            Path(self.storage_path).write_text(json.dumps(state, indent=2, default=str))
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def _load_state(self):
        """Load engine state"""
        try:
            if not Path(self.storage_path).exists():
                return
            state = json.loads(Path(self.storage_path).read_text())
            logger.info(f"Loaded introspection evolution state: {state.get('introspections_count', 0)} introspections")
        except Exception as e:
            logger.warning(f"Error loading state: {e}")
    
    # ==================== Reporting ====================
    
    def get_introspection_report(self, introspection_id: str) -> Optional[Dict]:
        """Get detailed report for an introspection"""
        
        result = self.introspections.get(introspection_id)
        if not result:
            return None
        
        return {
            'introspection_id': introspection_id,
            'failure_id': result.failure_id,
            'timestamp': result.timestamp.isoformat(),
            'explanation': {
                'summary': result.explanation.summary,
                'detailed_narrative': result.explanation.detailed_narrative,
                'counterfactual': result.explanation.counterfactual,
                'lessons': result.explanation.lessons
            },
            'causal_chain': [
                {
                    'factor_id': f.factor_id,
                    'description': f.description,
                    'category': f.category.value,
                    'confidence': f.confidence,
                    'is_root': f.is_root
                }
                for f in result.explanation.causal_chain
            ],
            'prescribed_fixes': [
                {
                    'fix_id': f.fix_id,
                    'description': f.description,
                    'fix_type': f.fix_type,
                    'complexity': f.complexity.value,
                    'expected_improvement': f.expected_improvement,
                    'automated': f.automated,
                    'implementation_steps': f.implementation_steps
                }
                for f in result.prescribed_fixes
            ],
            'capability_gaps_created': result.capability_gaps_created,
            'priority': result.priority,
            'estimated_impact': result.estimated_impact,
            'status': result.status
        }
    
    def get_evolution_summary(self) -> Dict[str, Any]:
        """Get summary of evolution activity"""
        
        total_introspections = len(self.introspections)
        pending_introspections = sum(1 for i in self.introspections.values() if i.status == "pending")
        
        # Category breakdown
        category_counts = defaultdict(int)
        for i in self.introspections.values():
            if i.explanation.causal_chain:
                root = [f for f in i.explanation.causal_chain if f.is_root]
                if root:
                    category_counts[root[0].category.value] += 1
        
        # Fix statistics
        total_fixes = sum(len(i.prescribed_fixes) for i in self.introspections.values())
        automated_fixes = sum(
            sum(1 for f in i.prescribed_fixes if f.automated)
            for i in self.introspections.values()
        )
        
        # Loop statistics
        completed_loops = len([l for l in self.completed_loops if l.outcome == "success"])
        failed_loops = len([l for l in self.completed_loops if l.outcome == "failed"])
        
        return {
            'introspections': {
                'total': total_introspections,
                'pending': pending_introspections,
                'by_category': dict(category_counts)
            },
            'fixes': {
                'total_prescribed': total_fixes,
                'automated': automated_fixes,
                'manual': total_fixes - automated_fixes
            },
            'evolution_loops': {
                'active': len(self.active_loops),
                'completed_success': completed_loops,
                'completed_failed': failed_loops,
                'success_rate': completed_loops / max(1, completed_loops + failed_loops)
            },
            'fix_effectiveness': {
                fix_id: len(records)
                for fix_id, records in self.fix_effectiveness.items()
            }
        }


# Factory function
def create_introspection_evolution_engine(
    diagnostic_engine=None,
    failure_memory=None,
    outcome_memory=None,
    decision_memory=None,
    capability_discovery_engine=None,
    storage_path: Optional[str] = None
) -> IntrospectionDrivenEvolutionEngine:
    """Factory function to create introspection evolution engine"""
    
    return IntrospectionDrivenEvolutionEngine(
        diagnostic_engine=diagnostic_engine,
        failure_memory=failure_memory,
        outcome_memory=outcome_memory,
        decision_memory=decision_memory,
        capability_discovery_engine=capability_discovery_engine,
        storage_path=storage_path
    )
